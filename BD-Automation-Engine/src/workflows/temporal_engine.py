"""Phase 49A — Temporal Durable Workflow Engine.

Provides deterministic, durable workflow execution with automatic retry,
saga compensation, checkpointing, and time-travel debugging. Four pre-built
BD workflows: FullBDCampaign, ContactEnrichment, WeeklyIntelCycle,
OpportunityResponse.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    COMPENSATED = "compensated"
    RETRYING = "retrying"


@dataclass
class StepCheckpoint:
    """Immutable checkpoint for a single workflow step."""
    step_id: str
    step_name: str
    status: StepStatus
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    attempt: int = 1
    duration_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "attempt": self.attempt,
            "duration_sec": round(self.duration_sec, 3),
        }


@dataclass
class WorkflowRun:
    """A single execution of a workflow."""
    run_id: str
    workflow_id: str
    workflow_name: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    input_params: Dict[str, Any] = field(default_factory=dict)
    checkpoints: List[StepCheckpoint] = field(default_factory=list)
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_sec: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    timeout_sec: float = 3600.0
    output: Any = None
    error: Optional[str] = None
    compensations_run: int = 0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "input_params": self.input_params,
            "checkpoints": [c.to_dict() for c in self.checkpoints],
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_sec": round(self.duration_sec, 3),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "output": self.output,
            "error": self.error,
            "compensations_run": self.compensations_run,
        }


@dataclass
class WorkflowDefinition:
    """Blueprint for a workflow — sequence of step definitions."""
    workflow_id: str
    name: str
    description: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    timeout_sec: float = 3600.0
    max_retries: int = 3
    tags: List[str] = field(default_factory=list)
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "timeout_sec": self.timeout_sec,
            "max_retries": self.max_retries,
            "tags": self.tags,
            "version": self.version,
        }


# =========================================
# BUILT-IN WORKFLOW DEFINITIONS
# =========================================

_FULL_BD_CAMPAIGN = WorkflowDefinition(
    workflow_id="wf_full_bd_campaign",
    name="FullBDCampaign",
    description="End-to-end BD campaign: scrape → map → enrich → score → playbook → outreach.",
    steps=[
        {"name": "scrape_jobs", "task_queue": "scraper_tasks",
         "description": "Scrape target job postings from Apify",
         "timeout_sec": 300, "retries": 2},
        {"name": "map_programs", "task_queue": "hub_tasks",
         "description": "Map jobs to federal programs",
         "timeout_sec": 120, "retries": 1},
        {"name": "enrich_contacts", "task_queue": "hub_tasks",
         "description": "Enrich contacts via Bullhorn + Qdrant",
         "timeout_sec": 180, "retries": 2},
        {"name": "score_opportunities", "task_queue": "hub_tasks",
         "description": "Score BD priority for each opportunity",
         "timeout_sec": 60, "retries": 1},
        {"name": "generate_playbooks", "task_queue": "hub_tasks",
         "description": "Generate BD playbooks for top opportunities",
         "timeout_sec": 120, "retries": 1},
        {"name": "draft_outreach", "task_queue": "n8n_tasks",
         "description": "Draft and queue outreach emails via n8n",
         "timeout_sec": 180, "retries": 2},
    ],
    timeout_sec=1800,
    max_retries=3,
    tags=["campaign", "end-to-end", "bd"],
)

_CONTACT_ENRICHMENT = WorkflowDefinition(
    workflow_id="wf_contact_enrichment",
    name="ContactEnrichment",
    description="Enrich a contact: classify tier, geocode, link programs, generate briefing.",
    steps=[
        {"name": "fetch_crm_data", "task_queue": "hub_tasks",
         "description": "Pull latest data from Bullhorn CRM",
         "timeout_sec": 60, "retries": 2},
        {"name": "classify_tier", "task_queue": "hub_tasks",
         "description": "Classify contact into 6-tier hierarchy",
         "timeout_sec": 30, "retries": 1},
        {"name": "geocode_location", "task_queue": "hub_tasks",
         "description": "Resolve contact location to coordinates",
         "timeout_sec": 30, "retries": 1},
        {"name": "link_programs", "task_queue": "hub_tasks",
         "description": "Link contact to relevant programs",
         "timeout_sec": 60, "retries": 1},
        {"name": "generate_briefing", "task_queue": "hub_tasks",
         "description": "Generate call briefing for the contact",
         "timeout_sec": 90, "retries": 1},
    ],
    timeout_sec=600,
    max_retries=2,
    tags=["contact", "enrichment"],
)

_WEEKLY_INTEL_CYCLE = WorkflowDefinition(
    workflow_id="wf_weekly_intel_cycle",
    name="WeeklyIntelCycle",
    description="Weekly intelligence cycle: fresh scrape, re-score, alerts, report.",
    steps=[
        {"name": "run_scrapers", "task_queue": "scraper_tasks",
         "description": "Execute all configured Apify scrapers",
         "timeout_sec": 600, "retries": 3},
        {"name": "update_program_map", "task_queue": "hub_tasks",
         "description": "Re-run program mapping on new data",
         "timeout_sec": 180, "retries": 1},
        {"name": "rescore_pipeline", "task_queue": "hub_tasks",
         "description": "Re-score all BD opportunities",
         "timeout_sec": 120, "retries": 1},
        {"name": "check_alerts", "task_queue": "hub_tasks",
         "description": "Check for threshold alerts and anomalies",
         "timeout_sec": 60, "retries": 1},
        {"name": "generate_weekly_report", "task_queue": "n8n_tasks",
         "description": "Compile and distribute weekly intel report",
         "timeout_sec": 120, "retries": 2},
    ],
    timeout_sec=1800,
    max_retries=2,
    tags=["weekly", "intelligence", "scheduled"],
)

_OPPORTUNITY_RESPONSE = WorkflowDefinition(
    workflow_id="wf_opportunity_response",
    name="OpportunityResponse",
    description="Rapid response to a new opportunity: analyze, score, assign, prep.",
    steps=[
        {"name": "analyze_opportunity", "task_queue": "hub_tasks",
         "description": "Analyze opportunity details and requirements",
         "timeout_sec": 60, "retries": 1},
        {"name": "competitive_analysis", "task_queue": "hub_tasks",
         "description": "Run competitive density analysis for region",
         "timeout_sec": 60, "retries": 1},
        {"name": "identify_contacts", "task_queue": "hub_tasks",
         "description": "Find relevant contacts for this opportunity",
         "timeout_sec": 60, "retries": 1},
        {"name": "score_and_prioritize", "task_queue": "hub_tasks",
         "description": "Score and set BD priority",
         "timeout_sec": 30, "retries": 1},
        {"name": "assign_bd_rep", "task_queue": "n8n_tasks",
         "description": "Assign BD representative and notify",
         "timeout_sec": 30, "retries": 2},
        {"name": "prep_materials", "task_queue": "hub_tasks",
         "description": "Prepare call prep and playbook materials",
         "timeout_sec": 120, "retries": 1},
    ],
    timeout_sec=900,
    max_retries=2,
    tags=["opportunity", "rapid-response"],
)

BUILTIN_WORKFLOWS: Dict[str, WorkflowDefinition] = {
    "wf_full_bd_campaign": _FULL_BD_CAMPAIGN,
    "wf_contact_enrichment": _CONTACT_ENRICHMENT,
    "wf_weekly_intel_cycle": _WEEKLY_INTEL_CYCLE,
    "wf_opportunity_response": _OPPORTUNITY_RESPONSE,
}


# =========================================
# TEMPORAL WORKFLOW ENGINE
# =========================================

class TemporalWorkflowEngine:
    """Durable workflow execution engine with checkpointing, retry, and saga compensation.

    Simulates Temporal.io semantics in-process for development and testing.
    Production deployment uses actual Temporal server.
    """

    def __init__(self):
        self._workflows: Dict[str, WorkflowDefinition] = dict(BUILTIN_WORKFLOWS)
        self._runs: Dict[str, WorkflowRun] = {}
        self._step_handlers: Dict[str, Callable] = {}
        self._compensation_handlers: Dict[str, Callable] = {}
        self._run_counter = 0
        logger.info("TemporalWorkflowEngine initialized with %d built-in workflows",
                     len(self._workflows))

    # ----- workflow registry -----

    def register_workflow(self, defn: WorkflowDefinition) -> None:
        """Register a new workflow definition."""
        self._workflows[defn.workflow_id] = defn
        logger.info("Registered workflow: %s (%s)", defn.workflow_id, defn.name)

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> List[WorkflowDefinition]:
        return list(self._workflows.values())

    # ----- step handler registration -----

    def register_step_handler(self, step_name: str, handler: Callable) -> None:
        """Register a handler function for a named step."""
        self._step_handlers[step_name] = handler

    def register_compensation(self, step_name: str, handler: Callable) -> None:
        """Register a compensation (rollback) handler for a step."""
        self._compensation_handlers[step_name] = handler

    # ----- execution -----

    def start_workflow(
        self, workflow_id: str, params: Optional[Dict[str, Any]] = None,
    ) -> WorkflowRun:
        """Start a new workflow run.  Returns the WorkflowRun immediately."""
        defn = self._workflows.get(workflow_id)
        if not defn:
            raise ValueError(f"Unknown workflow: {workflow_id}")

        self._run_counter += 1
        run_id = f"run_{hashlib.md5(f'{workflow_id}:{self._run_counter}:{time.time()}'.encode()).hexdigest()[:12]}"

        run = WorkflowRun(
            run_id=run_id,
            workflow_id=workflow_id,
            workflow_name=defn.name,
            input_params=params or {},
            max_retries=defn.max_retries,
            timeout_sec=defn.timeout_sec,
        )
        self._runs[run_id] = run
        logger.info("Workflow run created: %s (%s)", run_id, defn.name)
        return run

    def execute_workflow(self, run_id: str) -> WorkflowRun:
        """Execute a workflow run synchronously, processing each step in order.

        Steps are executed via registered handlers or simulated if no handler exists.
        On failure, saga compensation runs in reverse order.
        """
        run = self._runs.get(run_id)
        if not run:
            raise ValueError(f"Unknown run: {run_id}")

        defn = self._workflows.get(run.workflow_id)
        if not defn:
            raise ValueError(f"Unknown workflow: {run.workflow_id}")

        run.status = WorkflowStatus.RUNNING
        run.started_at = datetime.utcnow().isoformat()

        completed_steps: List[StepCheckpoint] = []

        for idx, step_def in enumerate(defn.steps):
            step_name = step_def["name"]
            step_id = f"step_{idx}_{step_name}"
            retries = step_def.get("retries", 1)

            cp = StepCheckpoint(
                step_id=step_id,
                step_name=step_name,
                status=StepStatus.RUNNING,
                started_at=datetime.utcnow().isoformat(),
            )

            handler = self._step_handlers.get(step_name)
            success = False
            last_error = None

            for attempt in range(1, retries + 2):  # retries + 1 initial attempt
                cp.attempt = attempt
                try:
                    if handler:
                        result = handler(run.input_params, step_def)
                    else:
                        # Simulated execution
                        result = {
                            "step": step_name,
                            "status": "simulated",
                            "task_queue": step_def.get("task_queue", "default"),
                        }
                    cp.result = result
                    cp.status = StepStatus.COMPLETED
                    cp.completed_at = datetime.utcnow().isoformat()
                    cp.duration_sec = 0.001 * (idx + 1)  # simulated duration
                    success = True
                    break
                except Exception as exc:
                    last_error = str(exc)
                    cp.status = StepStatus.RETRYING
                    logger.warning("Step %s attempt %d failed: %s", step_name, attempt, exc)

            if not success:
                cp.status = StepStatus.FAILED
                cp.error = last_error
                cp.completed_at = datetime.utcnow().isoformat()
                run.checkpoints.append(cp)

                # Saga compensation — reverse order
                run.status = WorkflowStatus.COMPENSATING
                for prev_cp in reversed(completed_steps):
                    comp = self._compensation_handlers.get(prev_cp.step_name)
                    if comp:
                        try:
                            comp(run.input_params, prev_cp.result)
                            prev_cp.status = StepStatus.COMPENSATED
                            run.compensations_run += 1
                        except Exception as ce:
                            logger.error("Compensation failed for %s: %s", prev_cp.step_name, ce)

                run.status = WorkflowStatus.FAILED
                run.error = f"Step '{step_name}' failed: {last_error}"
                run.completed_at = datetime.utcnow().isoformat()
                run.duration_sec = 0.01
                return run

            run.checkpoints.append(cp)
            completed_steps.append(cp)

        # All steps completed
        run.status = WorkflowStatus.COMPLETED
        run.completed_at = datetime.utcnow().isoformat()
        run.duration_sec = sum(c.duration_sec for c in run.checkpoints)
        run.output = {
            "total_steps": len(run.checkpoints),
            "completed_steps": sum(1 for c in run.checkpoints if c.status == StepStatus.COMPLETED),
        }
        logger.info("Workflow %s completed in %.3fs", run_id, run.duration_sec)
        return run

    # ----- run management -----

    def get_run(self, run_id: str) -> Optional[WorkflowRun]:
        return self._runs.get(run_id)

    def list_runs(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
    ) -> List[WorkflowRun]:
        runs = list(self._runs.values())
        if workflow_id:
            runs = [r for r in runs if r.workflow_id == workflow_id]
        if status:
            runs = [r for r in runs if r.status == status]
        return sorted(runs, key=lambda r: r.created_at, reverse=True)

    def pause_run(self, run_id: str) -> bool:
        run = self._runs.get(run_id)
        if run and run.status == WorkflowStatus.RUNNING:
            run.status = WorkflowStatus.PAUSED
            return True
        return False

    def resume_run(self, run_id: str) -> bool:
        run = self._runs.get(run_id)
        if run and run.status == WorkflowStatus.PAUSED:
            run.status = WorkflowStatus.RUNNING
            return True
        return False

    def cancel_run(self, run_id: str) -> bool:
        run = self._runs.get(run_id)
        if run and run.status in (WorkflowStatus.PENDING, WorkflowStatus.RUNNING, WorkflowStatus.PAUSED):
            run.status = WorkflowStatus.CANCELLED
            run.completed_at = datetime.utcnow().isoformat()
            return True
        return False

    def replay_run(self, run_id: str) -> Optional[WorkflowRun]:
        """Time-travel: re-execute a completed/failed run with same params."""
        orig = self._runs.get(run_id)
        if not orig:
            return None
        new_run = self.start_workflow(orig.workflow_id, orig.input_params)
        return self.execute_workflow(new_run.run_id)

    # ----- checkpoints / time-travel -----

    def get_checkpoint(self, run_id: str, step_idx: int) -> Optional[StepCheckpoint]:
        run = self._runs.get(run_id)
        if not run or step_idx >= len(run.checkpoints):
            return None
        return run.checkpoints[step_idx]

    def get_timeline(self, run_id: str) -> List[Dict[str, Any]]:
        """Return ordered timeline of step checkpoints for time-travel visualization."""
        run = self._runs.get(run_id)
        if not run:
            return []
        return [cp.to_dict() for cp in run.checkpoints]

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._runs)
        by_status: Dict[str, int] = {}
        for r in self._runs.values():
            by_status[r.status.value] = by_status.get(r.status.value, 0) + 1

        return {
            "total_workflows": len(self._workflows),
            "total_runs": total,
            "runs_by_status": by_status,
            "builtin_workflows": [w.name for w in BUILTIN_WORKFLOWS.values()],
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[TemporalWorkflowEngine] = None


def get_temporal_engine() -> TemporalWorkflowEngine:
    global _instance
    if _instance is None:
        _instance = TemporalWorkflowEngine()
    return _instance
