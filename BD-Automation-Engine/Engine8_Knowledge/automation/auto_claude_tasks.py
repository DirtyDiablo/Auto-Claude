"""
Phase 19A — Auto Claude Task Manager

Framework for delegating complex research tasks to Claude.
Packages prompt + context documents, manages queue, stores results.

Task types: deep_research, contact_analysis, competitive_brief,
proposal_section, data_reconciliation.
"""

import json
import uuid
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "automation"
DATA_DIR.mkdir(parents=True, exist_ok=True)
QUEUE_FILE = DATA_DIR / "claude_task_queue.jsonl"
RESULTS_DIR = DATA_DIR / "claude_task_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Task types and templates
# ---------------------------------------------------------------------------


class TaskType(str, Enum):
    DEEP_RESEARCH = "deep_research"
    CONTACT_ANALYSIS = "contact_analysis"
    COMPETITIVE_BRIEF = "competitive_brief"
    PROPOSAL_SECTION = "proposal_section"
    DATA_RECONCILIATION = "data_reconciliation"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


TASK_TEMPLATES: dict[str, dict[str, str]] = {
    "deep_research": {
        "system_prompt": (
            "You are a senior BD analyst at a defense staffing company. "
            "Provide detailed, actionable research with specific data points, "
            "contract numbers, and strategic recommendations."
        ),
        "output_format": "structured_report",
        "expected_sections": "executive_summary, findings, data_points, recommendations, sources",
    },
    "contact_analysis": {
        "system_prompt": (
            "You are a relationship intelligence analyst. Analyze the contact's "
            "career trajectory, influence network, and identify optimal approach "
            "angles for business development engagement."
        ),
        "output_format": "strategy_brief",
        "expected_sections": "profile_summary, career_trajectory, influence_map, approach_strategy, talking_points",
    },
    "competitive_brief": {
        "system_prompt": (
            "You are a competitive intelligence analyst for defense contracting. "
            "Compare companies' positioning, strengths, weaknesses, and provide "
            "actionable competitive strategies."
        ),
        "output_format": "competitive_analysis",
        "expected_sections": "market_position, strengths_comparison, weaknesses, win_strategy, risk_factors",
    },
    "proposal_section": {
        "system_prompt": (
            "You are a proposal writer for a defense staffing company (PTS). "
            "Draft professional, compliant proposal sections that highlight "
            "relevant past performance and technical capabilities."
        ),
        "output_format": "proposal_text",
        "expected_sections": "technical_approach, management_plan, staffing_strategy, risk_mitigation",
    },
    "data_reconciliation": {
        "system_prompt": (
            "You are a data analyst. Cross-reference data sources, identify "
            "discrepancies, new entries, and produce a clean delta report."
        ),
        "output_format": "delta_report",
        "expected_sections": "new_records, updated_records, conflicts, recommended_actions",
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ClaudeTask:
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    task_type: str = TaskType.DEEP_RESEARCH.value
    prompt: str = ""
    context_documents: list[str] = field(default_factory=list)
    context_data: dict = field(default_factory=dict)
    expected_output_format: str = "structured_report"
    priority: str = "normal"  # low, normal, high, urgent
    status: str = TaskStatus.PENDING.value
    submitted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result_file: Optional[str] = None
    error: Optional[str] = None
    estimated_tokens: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TaskResult:
    task_id: str
    task_type: str
    prompt: str
    result: str
    sections: dict = field(default_factory=dict)
    token_usage: dict = field(default_factory=dict)
    completed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    quality_score: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# AutoClaudeTaskManager
# ---------------------------------------------------------------------------


class AutoClaudeTaskManager:
    """Manages complex research tasks delegated to Claude."""

    def __init__(self) -> None:
        self._queue: list[ClaudeTask] = []
        self._in_progress: dict[str, ClaudeTask] = {}
        self._completed: dict[str, ClaudeTask] = {}

        # Load persisted queue
        if QUEUE_FILE.exists():
            for line in QUEUE_FILE.read_text().strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    task = ClaudeTask(**data)
                    if task.status == TaskStatus.PENDING.value:
                        self._queue.append(task)
                    elif task.status == TaskStatus.IN_PROGRESS.value:
                        self._in_progress[task.task_id] = task
                    elif task.status in (
                        TaskStatus.COMPLETED.value,
                        TaskStatus.FAILED.value,
                    ):
                        self._completed[task.task_id] = task
                except Exception:
                    pass

    def _persist_queue(self) -> None:
        """Write full queue state to disk."""
        all_tasks = (
            list(self._queue)
            + list(self._in_progress.values())
            + list(self._completed.values())
        )
        QUEUE_FILE.write_text(
            "\n".join(json.dumps(t.to_dict()) for t in all_tasks) + "\n"
        )

    # -- Submit --

    def submit_task(
        self,
        task_type: str,
        prompt: str,
        context_documents: Optional[list[str]] = None,
        context_data: Optional[dict] = None,
        priority: str = "normal",
    ) -> dict:
        """Submit a new task to the queue."""
        template = TASK_TEMPLATES.get(task_type)
        if not template:
            return {
                "error": f"Unknown task type: {task_type}. Valid: {list(TASK_TEMPLATES.keys())}"
            }

        task = ClaudeTask(
            task_type=task_type,
            prompt=prompt,
            context_documents=context_documents or [],
            context_data=context_data or {},
            expected_output_format=template["output_format"],
            priority=priority,
            estimated_tokens=self._estimate_tokens(prompt, context_data or {}),
        )

        self._queue.append(task)
        self._persist_queue()
        logger.info("claude_task_submitted", task_id=task.task_id, task_type=task_type)

        return {
            "task_id": task.task_id,
            "status": task.status,
            "estimated_tokens": task.estimated_tokens,
            "queue_position": len(self._queue),
        }

    def _estimate_tokens(self, prompt: str, context: dict) -> int:
        """Rough token estimation."""
        text = prompt + json.dumps(context)
        return len(text) // 4  # ~4 chars per token

    # -- Task lifecycle --

    def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get current status of a task."""
        for task in self._queue:
            if task.task_id == task_id:
                return task.to_dict()
        if task_id in self._in_progress:
            return self._in_progress[task_id].to_dict()
        if task_id in self._completed:
            return self._completed[task_id].to_dict()
        return None

    def get_results(self, task_id: str) -> Optional[dict]:
        """Get results for a completed task."""
        result_file = RESULTS_DIR / f"{task_id}.json"
        if result_file.exists():
            return json.loads(result_file.read_text())
        return None

    def list_pending_tasks(self) -> list[dict]:
        """List all pending tasks in queue order."""
        return [t.to_dict() for t in self._queue]

    def list_all_tasks(self) -> list[dict]:
        """List all tasks across all statuses."""
        result = []
        for t in self._queue:
            result.append(t.to_dict())
        for t in self._in_progress.values():
            result.append(t.to_dict())
        for t in self._completed.values():
            result.append(t.to_dict())
        return sorted(result, key=lambda x: x.get("submitted_at", ""), reverse=True)

    # -- Processing (stub — packages prompt + context for Claude) --

    def build_claude_prompt(self, task_id: str) -> Optional[dict]:
        """Build the full prompt package for Claude API call.

        This packages the system prompt, user prompt, and context into
        a format ready for the Claude API. Actual API calls are intentionally
        not implemented here — they should be triggered by the orchestrator.
        """
        task = None
        for t in self._queue:
            if t.task_id == task_id:
                task = t
                break
        if not task:
            task = self._in_progress.get(task_id)
        if not task:
            return None

        template = TASK_TEMPLATES.get(task.task_type, {})

        # Build context block
        context_parts = []
        for doc_path in task.context_documents:
            try:
                content = Path(doc_path).read_text(errors="replace")[:10000]
                context_parts.append(f"=== Document: {doc_path} ===\n{content}")
            except Exception:
                context_parts.append(f"=== Document: {doc_path} (not found) ===")

        if task.context_data:
            context_parts.append(
                f"=== Structured Data ===\n{json.dumps(task.context_data, indent=2)}"
            )

        context_block = (
            "\n\n".join(context_parts)
            if context_parts
            else "No additional context provided."
        )

        return {
            "task_id": task.task_id,
            "system": template.get("system_prompt", "You are a helpful assistant."),
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"{task.prompt}\n\n"
                        f"--- Context ---\n{context_block}\n\n"
                        f"--- Output Format ---\n"
                        f"Provide output as a {template.get('output_format', 'report')} "
                        f"with sections: {template.get('expected_sections', 'summary')}"
                    ),
                }
            ],
            "max_tokens": 4096,
            "model": "claude-sonnet-4-5-20250929",
        }

    def mark_in_progress(self, task_id: str) -> bool:
        """Move a task from pending to in_progress."""
        for i, task in enumerate(self._queue):
            if task.task_id == task_id:
                task.status = TaskStatus.IN_PROGRESS.value
                task.started_at = datetime.now().isoformat()
                self._in_progress[task_id] = task
                self._queue.pop(i)
                self._persist_queue()
                return True
        return False

    def complete_task(
        self, task_id: str, result_text: str, sections: Optional[dict] = None
    ) -> bool:
        """Mark a task as completed with results."""
        task = self._in_progress.pop(task_id, None)
        if not task:
            return False

        task.status = TaskStatus.COMPLETED.value
        task.completed_at = datetime.now().isoformat()

        # Save result
        result = TaskResult(
            task_id=task_id,
            task_type=task.task_type,
            prompt=task.prompt,
            result=result_text,
            sections=sections or {},
        )
        result_file = RESULTS_DIR / f"{task_id}.json"
        result_file.write_text(json.dumps(result.to_dict(), indent=2))
        task.result_file = str(result_file)

        self._completed[task_id] = task
        self._persist_queue()
        logger.info("claude_task_completed", task_id=task_id)
        return True

    def fail_task(self, task_id: str, error: str) -> bool:
        """Mark a task as failed."""
        task = self._in_progress.pop(task_id, None)
        if not task:
            return False

        task.status = TaskStatus.FAILED.value
        task.completed_at = datetime.now().isoformat()
        task.error = error
        self._completed[task_id] = task
        self._persist_queue()
        return True

    # -- Stats --

    def get_stats(self) -> dict:
        return {
            "pending": len(self._queue),
            "in_progress": len(self._in_progress),
            "completed": sum(
                1
                for t in self._completed.values()
                if t.status == TaskStatus.COMPLETED.value
            ),
            "failed": sum(
                1
                for t in self._completed.values()
                if t.status == TaskStatus.FAILED.value
            ),
            "total": len(self._queue) + len(self._in_progress) + len(self._completed),
            "task_types": list(TASK_TEMPLATES.keys()),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: Optional[AutoClaudeTaskManager] = None


def get_claude_task_manager() -> AutoClaudeTaskManager:
    global _instance
    if _instance is None:
        _instance = AutoClaudeTaskManager()
    return _instance
