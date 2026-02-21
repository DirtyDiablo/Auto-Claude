"""
Workflow Scheduler — APScheduler integration for cron-style execution.

Schedules:
    - master_pipeline:      daily at 06:00 UTC
    - morning_briefing:     daily at 07:00 UTC
    - contact_enrichment:   weekly on Monday at 08:00 UTC
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import structlog
    _log = structlog.get_logger("workflows.scheduler")
except ImportError:
    _log = logging.getLogger("workflows.scheduler")

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    AsyncIOScheduler = None
    CronTrigger = None


# ---------------------------------------------------------------------------
# Execution history (in-memory for now)
# ---------------------------------------------------------------------------

_execution_history: List[Dict[str, Any]] = []
MAX_HISTORY = 100


def _record_execution(workflow_name: str, success: bool, duration: float,
                      error: Optional[str] = None) -> None:
    """Record a workflow execution in the history."""
    entry = {
        "workflow": workflow_name,
        "started_at": datetime.utcnow().isoformat(),
        "success": success,
        "duration_seconds": duration,
        "error": error,
    }
    _execution_history.append(entry)
    if len(_execution_history) > MAX_HISTORY:
        _execution_history.pop(0)


def get_execution_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Return recent workflow execution history."""
    return list(reversed(_execution_history[-limit:]))


# ---------------------------------------------------------------------------
# Scheduled job wrappers
# ---------------------------------------------------------------------------

def _run_master_pipeline() -> None:
    """Scheduled wrapper for master pipeline."""
    started = datetime.utcnow()
    try:
        from workflows.master_pipeline import run_master_pipeline, WorkflowConfig
        cfg = WorkflowConfig()
        result = run_master_pipeline(config=cfg)
        errors = result.get("errors", [])
        duration = (datetime.utcnow() - started).total_seconds()
        _record_execution("master_pipeline", success=len(errors) == 0, duration=duration)
        _log.info("scheduled.master_pipeline.done", duration=duration, errors=len(errors))
    except Exception as exc:
        duration = (datetime.utcnow() - started).total_seconds()
        _record_execution("master_pipeline", success=False, duration=duration, error=str(exc))
        _log.error("scheduled.master_pipeline.failed", error=str(exc))


def _run_morning_briefing() -> None:
    """Scheduled wrapper for morning briefing."""
    started = datetime.utcnow()
    try:
        from workflows.morning_briefing import run_morning_briefing
        result = run_morning_briefing()
        errors = result.get("errors", [])
        duration = (datetime.utcnow() - started).total_seconds()
        _record_execution("morning_briefing", success=len(errors) == 0, duration=duration)
        _log.info("scheduled.morning_briefing.done", duration=duration)
    except Exception as exc:
        duration = (datetime.utcnow() - started).total_seconds()
        _record_execution("morning_briefing", success=False, duration=duration, error=str(exc))
        _log.error("scheduled.morning_briefing.failed", error=str(exc))


def _run_contact_enrichment() -> None:
    """Scheduled wrapper for contact enrichment."""
    started = datetime.utcnow()
    try:
        from workflows.contact_enrichment import run_contact_enrichment
        result = run_contact_enrichment()
        errors = result.get("errors", [])
        duration = (datetime.utcnow() - started).total_seconds()
        _record_execution("contact_enrichment", success=len(errors) == 0, duration=duration)
        _log.info("scheduled.contact_enrichment.done", duration=duration)
    except Exception as exc:
        duration = (datetime.utcnow() - started).total_seconds()
        _record_execution("contact_enrichment", success=False, duration=duration, error=str(exc))
        _log.error("scheduled.contact_enrichment.failed", error=str(exc))


# ---------------------------------------------------------------------------
# Scheduler class
# ---------------------------------------------------------------------------

class WorkflowScheduler:
    """Manages scheduled execution of LangGraph workflows."""

    def __init__(self) -> None:
        self._scheduler: Optional[Any] = None
        self._running = False
        self._enabled = True

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> bool:
        """Start the scheduler with all configured jobs.

        Returns True if started, False if APScheduler is unavailable.
        """
        if not APSCHEDULER_AVAILABLE:
            _log.warning("scheduler.start.unavailable",
                         msg="APScheduler not installed")
            return False

        if self._running:
            _log.info("scheduler.already_running")
            return True

        self._scheduler = AsyncIOScheduler()

        # Master pipeline: daily at 06:00 UTC
        self._scheduler.add_job(
            _run_master_pipeline,
            CronTrigger(hour=6, minute=0),
            id="master_pipeline",
            name="BD Master Pipeline",
            replace_existing=True,
        )

        # Morning briefing: daily at 07:00 UTC
        self._scheduler.add_job(
            _run_morning_briefing,
            CronTrigger(hour=7, minute=0),
            id="morning_briefing",
            name="Morning Intelligence Briefing",
            replace_existing=True,
        )

        # Contact enrichment: weekly Monday at 08:00 UTC
        self._scheduler.add_job(
            _run_contact_enrichment,
            CronTrigger(day_of_week="mon", hour=8, minute=0),
            id="contact_enrichment",
            name="Contact Enrichment",
            replace_existing=True,
        )

        self._scheduler.start()
        self._running = True
        _log.info("scheduler.started", jobs=3)
        return True

    def stop(self) -> None:
        """Stop the scheduler gracefully."""
        if self._scheduler and self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False
            _log.info("scheduler.stopped")

    def toggle(self, enabled: bool) -> None:
        """Enable or disable scheduled runs."""
        self._enabled = enabled
        if enabled and not self._running:
            self.start()
        elif not enabled and self._running:
            self.stop()
        _log.info("scheduler.toggle", enabled=enabled)

    def get_status(self) -> Dict[str, Any]:
        """Return current scheduler status and job info."""
        jobs = []
        if self._scheduler and self._running:
            for job in self._scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                })

        return {
            "running": self._running,
            "enabled": self._enabled,
            "apscheduler_available": APSCHEDULER_AVAILABLE,
            "jobs": jobs,
            "execution_history_count": len(_execution_history),
        }


# Singleton
_scheduler_instance: Optional[WorkflowScheduler] = None


def get_scheduler() -> WorkflowScheduler:
    """Return the global WorkflowScheduler singleton."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = WorkflowScheduler()
    return _scheduler_instance
