"""
Agent Scheduler — APScheduler-based autonomous agent orchestration.

Schedules morning briefings and contact enrichment scans, with manual
trigger support and execution logging.

Human-in-the-loop: Agents generate reports but DON'T take external
actions (no emails, no CRM writes) without explicit approval.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "data"
RUNS_LOG = DATA_DIR / "agent_runs.jsonl"


# ─── Agent Run Record ────────────────────────────────────────────────────────


def _log_run(agent: str, status: str, summary: str, start_time: str, end_time: str):
    """Log an agent run to the JSONL file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "agent": agent,
        "start_time": start_time,
        "end_time": end_time,
        "status": status,
        "summary": summary,
    }
    with open(RUNS_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def get_runs(limit: int = 50) -> List[Dict]:
    """Get recent agent run history."""
    if not RUNS_LOG.exists():
        return []

    entries = []
    with open(RUNS_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    return entries[-limit:]


def get_last_run(agent_name: str) -> Optional[Dict]:
    """Get the most recent run for a specific agent."""
    runs = get_runs(200)
    for run in reversed(runs):
        if run.get("agent") == agent_name:
            return run
    return None


# ─── Agent Executor Functions ────────────────────────────────────────────────


def _run_morning_briefing():
    """Execute morning briefing agent."""
    start = datetime.now().isoformat()
    try:
        from Engine8_Knowledge.agents.autonomous.morning_briefing import (
            MorningBriefingAgent,
        )

        agent = MorningBriefingAgent()
        brief = agent.generate_brief()
        summary = (
            f"Generated brief for {brief.date}: "
            f"{len(brief.hiring_signals)} signals, "
            f"{len(brief.new_opportunities)} opportunities, "
            f"{len(brief.priority_contacts)} priority contacts"
        )
        _log_run(
            "morning_briefing", "success", summary, start, datetime.now().isoformat()
        )
        logger.info(f"Morning briefing completed: {summary}")
        return brief.to_dict()
    except Exception as e:
        _log_run("morning_briefing", "error", str(e), start, datetime.now().isoformat())
        logger.error(f"Morning briefing failed: {e}")
        return {"error": str(e)}


def _run_contact_enrichment():
    """Execute contact enrichment agent."""
    start = datetime.now().isoformat()
    try:
        from Engine8_Knowledge.agents.autonomous.contact_enrichment import (
            ContactEnrichmentAgent,
        )

        agent = ContactEnrichmentAgent()
        report = agent.scan_all_contacts(limit=100)
        summary = (
            f"Scanned {report.contacts_scanned} contacts: "
            f"{report.stale_contacts} stale, {report.missing_fields} missing fields, "
            f"{report.changes_detected} total issues"
        )
        _log_run(
            "contact_enrichment", "success", summary, start, datetime.now().isoformat()
        )
        logger.info(f"Contact enrichment completed: {summary}")
        return report.to_dict()
    except Exception as e:
        _log_run(
            "contact_enrichment", "error", str(e), start, datetime.now().isoformat()
        )
        logger.error(f"Contact enrichment failed: {e}")
        return {"error": str(e)}


AGENT_EXECUTORS = {
    "morning_briefing": _run_morning_briefing,
    "contact_enrichment": _run_contact_enrichment,
}


# ─── Agent Scheduler ─────────────────────────────────────────────────────────


class AgentScheduler:
    """
    APScheduler-based scheduler for autonomous BD agents.

    Schedules:
    - morning_briefing: daily at 06:30 local time
    - contact_enrichment: weekly on Monday at 02:00
    """

    def __init__(self):
        self._scheduler = None
        self._running = False

    def start(self):
        """Start the scheduler with configured jobs."""
        if self._running:
            logger.info("Scheduler already running")
            return

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger

            self._scheduler = BackgroundScheduler()

            # Morning briefing: daily at 06:30
            self._scheduler.add_job(
                _run_morning_briefing,
                CronTrigger(hour=6, minute=30),
                id="morning_briefing",
                name="Morning Briefing",
                replace_existing=True,
            )

            # Contact enrichment: Monday at 02:00
            self._scheduler.add_job(
                _run_contact_enrichment,
                CronTrigger(day_of_week="mon", hour=2, minute=0),
                id="contact_enrichment",
                name="Contact Enrichment",
                replace_existing=True,
            )

            self._scheduler.start()
            self._running = True
            logger.info("Agent scheduler started with 2 jobs")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")

    def stop(self):
        """Stop the scheduler."""
        if self._scheduler and self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False
            logger.info("Agent scheduler stopped")

    def run_now(self, agent_name: str) -> Dict[str, Any]:
        """Trigger an agent manually."""
        executor = AGENT_EXECUTORS.get(agent_name)
        if not executor:
            return {
                "error": f"Unknown agent: {agent_name}",
                "available": list(AGENT_EXECUTORS.keys()),
            }

        logger.info(f"Manual trigger: {agent_name}")
        result = executor()
        return {"success": True, "agent": agent_name, "result": result}

    def get_schedule(self) -> List[Dict[str, Any]]:
        """Get current schedule with next run times."""
        schedules = [
            {
                "agent": "morning_briefing",
                "name": "Morning Briefing",
                "schedule": "Daily at 06:30",
                "next_run": None,
                "last_run": get_last_run("morning_briefing"),
            },
            {
                "agent": "contact_enrichment",
                "name": "Contact Enrichment",
                "schedule": "Weekly on Monday at 02:00",
                "next_run": None,
                "last_run": get_last_run("contact_enrichment"),
            },
        ]

        # Fill in next_run from scheduler if running
        if self._scheduler and self._running:
            for job in self._scheduler.get_jobs():
                for s in schedules:
                    if s["agent"] == job.id:
                        next_run = job.next_run_time
                        s["next_run"] = next_run.isoformat() if next_run else None

        return schedules

    @property
    def is_running(self) -> bool:
        return self._running


# ─── Singleton ──────────────────────────────────────────────────────────────

_scheduler: Optional[AgentScheduler] = None


def get_agent_scheduler() -> AgentScheduler:
    """Get or create the singleton AgentScheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AgentScheduler()
    return _scheduler
