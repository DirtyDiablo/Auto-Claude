"""Phase 49A — Cross-Project Orchestrator.

Routes tasks across BD-Automation-Engine sub-projects via typed task queues.
Manages dependencies, fan-out/fan-in, priority routing, and health monitoring
for the three task queue channels: hub_tasks, scraper_tasks, n8n_tasks.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================

class TaskQueueName(str, Enum):
    HUB = "hub_tasks"
    SCRAPER = "scraper_tasks"
    N8N = "n8n_tasks"


class OrchestratorTaskStatus(str, Enum):
    QUEUED = "queued"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"  # waiting on dependencies


class TaskPriority(int, Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class OrchestratorTask:
    """A single routable task in the orchestrator."""
    task_id: str
    name: str
    queue: TaskQueueName
    status: OrchestratorTaskStatus = OrchestratorTaskStatus.QUEUED
    priority: TaskPriority = TaskPriority.NORMAL
    payload: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    created_at: str = ""
    dispatched_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2
    workflow_run_id: Optional[str] = None  # optional link to a workflow run

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "queue": self.queue.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "payload": self.payload,
            "depends_on": self.depends_on,
            "created_at": self.created_at,
            "dispatched_at": self.dispatched_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "workflow_run_id": self.workflow_run_id,
        }


@dataclass
class TaskQueue:
    """Named task queue with health tracking."""
    name: TaskQueueName
    tasks: List[OrchestratorTask] = field(default_factory=list)
    total_dispatched: int = 0
    total_completed: int = 0
    total_failed: int = 0
    is_healthy: bool = True
    last_heartbeat: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name.value,
            "pending": sum(1 for t in self.tasks if t.status == OrchestratorTaskStatus.QUEUED),
            "running": sum(1 for t in self.tasks if t.status == OrchestratorTaskStatus.RUNNING),
            "completed": self.total_completed,
            "failed": self.total_failed,
            "total_dispatched": self.total_dispatched,
            "is_healthy": self.is_healthy,
            "last_heartbeat": self.last_heartbeat,
        }


@dataclass
class FanOutResult:
    """Result of a fan-out / fan-in operation."""
    group_id: str
    task_ids: List[str]
    total: int
    completed: int = 0
    failed: int = 0
    results: List[Any] = field(default_factory=list)
    all_complete: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_id": self.group_id,
            "task_ids": self.task_ids,
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "results": self.results,
            "all_complete": self.all_complete,
        }


# =========================================
# QUEUE ROUTING RULES
# =========================================

_QUEUE_ROUTING: Dict[str, TaskQueueName] = {
    # Scraper tasks
    "scrape_jobs": TaskQueueName.SCRAPER,
    "run_scrapers": TaskQueueName.SCRAPER,
    "scrape_postings": TaskQueueName.SCRAPER,
    "apify_run": TaskQueueName.SCRAPER,
    # n8n tasks
    "draft_outreach": TaskQueueName.N8N,
    "send_notification": TaskQueueName.N8N,
    "assign_bd_rep": TaskQueueName.N8N,
    "generate_weekly_report": TaskQueueName.N8N,
    "trigger_webhook": TaskQueueName.N8N,
    # Hub tasks (default)
    "map_programs": TaskQueueName.HUB,
    "enrich_contacts": TaskQueueName.HUB,
    "score_opportunities": TaskQueueName.HUB,
    "classify_tier": TaskQueueName.HUB,
    "geocode_location": TaskQueueName.HUB,
    "generate_playbooks": TaskQueueName.HUB,
    "generate_briefing": TaskQueueName.HUB,
    "analyze_opportunity": TaskQueueName.HUB,
    "competitive_analysis": TaskQueueName.HUB,
    "identify_contacts": TaskQueueName.HUB,
    "fetch_crm_data": TaskQueueName.HUB,
    "link_programs": TaskQueueName.HUB,
    "score_and_prioritize": TaskQueueName.HUB,
    "prep_materials": TaskQueueName.HUB,
    "update_program_map": TaskQueueName.HUB,
    "rescore_pipeline": TaskQueueName.HUB,
    "check_alerts": TaskQueueName.HUB,
}


# =========================================
# CROSS-PROJECT ORCHESTRATOR
# =========================================

class CrossProjectOrchestrator:
    """Routes tasks across BD-Automation-Engine sub-projects via typed queues.

    Three task queues:
    - hub_tasks: Engine 2-8 processing (program mapping, enrichment, scoring)
    - scraper_tasks: Engine 1 Apify job scraping
    - n8n_tasks: Workflow automation (email, notifications, reports)
    """

    def __init__(self):
        self._queues: Dict[TaskQueueName, TaskQueue] = {
            TaskQueueName.HUB: TaskQueue(name=TaskQueueName.HUB),
            TaskQueueName.SCRAPER: TaskQueue(name=TaskQueueName.SCRAPER),
            TaskQueueName.N8N: TaskQueue(name=TaskQueueName.N8N),
        }
        self._tasks: Dict[str, OrchestratorTask] = {}
        self._fan_outs: Dict[str, FanOutResult] = {}
        self._task_counter = 0
        logger.info("CrossProjectOrchestrator initialized with 3 task queues")

    # ----- routing -----

    def route_task(self, task_name: str) -> TaskQueueName:
        """Determine which queue a task belongs to."""
        return _QUEUE_ROUTING.get(task_name, TaskQueueName.HUB)

    # ----- task submission -----

    def submit_task(
        self,
        name: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        depends_on: Optional[List[str]] = None,
        queue: Optional[TaskQueueName] = None,
        workflow_run_id: Optional[str] = None,
    ) -> OrchestratorTask:
        """Submit a task to the appropriate queue."""
        self._task_counter += 1
        task_id = f"otask_{hashlib.md5(f'{name}:{self._task_counter}:{time.time()}'.encode()).hexdigest()[:10]}"
        target_queue = queue or self.route_task(name)

        task = OrchestratorTask(
            task_id=task_id,
            name=name,
            queue=target_queue,
            priority=priority,
            payload=payload or {},
            depends_on=depends_on or [],
            workflow_run_id=workflow_run_id,
        )

        # Check dependencies
        if task.depends_on:
            all_done = all(
                self._tasks.get(dep_id) and self._tasks[dep_id].status == OrchestratorTaskStatus.COMPLETED
                for dep_id in task.depends_on
            )
            if not all_done:
                task.status = OrchestratorTaskStatus.WAITING

        self._tasks[task_id] = task
        self._queues[target_queue].tasks.append(task)
        logger.info("Task %s submitted to %s (priority=%s)", task_id, target_queue.value, priority.name)
        return task

    # ----- dispatch / execute -----

    def dispatch_next(self, queue_name: TaskQueueName) -> Optional[OrchestratorTask]:
        """Dispatch the highest-priority queued task from a queue."""
        q = self._queues.get(queue_name)
        if not q:
            return None

        candidates = [
            t for t in q.tasks
            if t.status == OrchestratorTaskStatus.QUEUED
        ]
        if not candidates:
            return None

        # Sort by priority (lower = higher priority)
        candidates.sort(key=lambda t: t.priority.value)
        task = candidates[0]
        task.status = OrchestratorTaskStatus.DISPATCHED
        task.dispatched_at = datetime.utcnow().isoformat()
        q.total_dispatched += 1
        return task

    def execute_task(self, task_id: str) -> OrchestratorTask:
        """Simulate executing a dispatched task."""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Unknown task: {task_id}")

        task.status = OrchestratorTaskStatus.RUNNING

        # Simulated execution — always succeeds
        task.result = {
            "task": task.name,
            "queue": task.queue.value,
            "status": "simulated_complete",
        }
        task.status = OrchestratorTaskStatus.COMPLETED
        task.completed_at = datetime.utcnow().isoformat()

        q = self._queues[task.queue]
        q.total_completed += 1
        q.last_heartbeat = datetime.utcnow().isoformat()

        # Unblock waiting tasks
        self._check_waiting_tasks()

        return task

    def fail_task(self, task_id: str, error: str) -> OrchestratorTask:
        """Mark a task as failed."""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Unknown task: {task_id}")

        task.status = OrchestratorTaskStatus.FAILED
        task.error = error
        task.completed_at = datetime.utcnow().isoformat()
        self._queues[task.queue].total_failed += 1
        return task

    # ----- fan-out / fan-in -----

    def fan_out(
        self,
        task_names: List[str],
        shared_payload: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> FanOutResult:
        """Dispatch multiple tasks in parallel (fan-out)."""
        group_id = f"fanout_{hashlib.md5(f'{len(task_names)}:{time.time()}'.encode()).hexdigest()[:8]}"
        task_ids = []

        for name in task_names:
            task = self.submit_task(name, payload=shared_payload, priority=priority)
            task_ids.append(task.task_id)

        result = FanOutResult(
            group_id=group_id,
            task_ids=task_ids,
            total=len(task_ids),
        )
        self._fan_outs[group_id] = result
        return result

    def fan_in(self, group_id: str) -> FanOutResult:
        """Collect results from a fan-out group (fan-in)."""
        result = self._fan_outs.get(group_id)
        if not result:
            raise ValueError(f"Unknown fan-out group: {group_id}")

        completed = 0
        failed = 0
        results = []

        for tid in result.task_ids:
            task = self._tasks.get(tid)
            if not task:
                continue
            if task.status == OrchestratorTaskStatus.COMPLETED:
                completed += 1
                results.append(task.result)
            elif task.status == OrchestratorTaskStatus.FAILED:
                failed += 1

        result.completed = completed
        result.failed = failed
        result.results = results
        result.all_complete = (completed + failed) == result.total
        return result

    # ----- queue management -----

    def get_queue_status(self, queue_name: TaskQueueName) -> Dict[str, Any]:
        q = self._queues.get(queue_name)
        if not q:
            return {}
        return q.to_dict()

    def get_all_queues(self) -> List[Dict[str, Any]]:
        return [q.to_dict() for q in self._queues.values()]

    def get_task(self, task_id: str) -> Optional[OrchestratorTask]:
        return self._tasks.get(task_id)

    def list_tasks(
        self,
        queue: Optional[TaskQueueName] = None,
        status: Optional[OrchestratorTaskStatus] = None,
    ) -> List[OrchestratorTask]:
        tasks = list(self._tasks.values())
        if queue:
            tasks = [t for t in tasks if t.queue == queue]
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def cancel_task(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task and task.status in (
            OrchestratorTaskStatus.QUEUED,
            OrchestratorTaskStatus.WAITING,
            OrchestratorTaskStatus.DISPATCHED,
        ):
            task.status = OrchestratorTaskStatus.CANCELLED
            task.completed_at = datetime.utcnow().isoformat()
            return True
        return False

    def set_queue_health(self, queue_name: TaskQueueName, healthy: bool) -> None:
        q = self._queues.get(queue_name)
        if q:
            q.is_healthy = healthy
            q.last_heartbeat = datetime.utcnow().isoformat()

    # ----- internal helpers -----

    def _check_waiting_tasks(self):
        """Promote WAITING tasks whose dependencies are all completed."""
        for task in self._tasks.values():
            if task.status != OrchestratorTaskStatus.WAITING:
                continue
            all_done = all(
                self._tasks.get(dep_id) and self._tasks[dep_id].status == OrchestratorTaskStatus.COMPLETED
                for dep_id in task.depends_on
            )
            if all_done:
                task.status = OrchestratorTaskStatus.QUEUED

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_tasks": len(self._tasks),
            "queues": self.get_all_queues(),
            "fan_out_groups": len(self._fan_outs),
            "tasks_by_status": {
                s.value: sum(1 for t in self._tasks.values() if t.status == s)
                for s in OrchestratorTaskStatus
            },
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[CrossProjectOrchestrator] = None


def get_orchestrator() -> CrossProjectOrchestrator:
    global _instance
    if _instance is None:
        _instance = CrossProjectOrchestrator()
    return _instance
