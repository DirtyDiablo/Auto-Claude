"""
Autonomous Agent API Routes — Scheduler, briefings, enrichment.
"""

import logging
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/autonomous", tags=["Autonomous Agents"])


# ─── Scheduler Endpoints ────────────────────────────────────────────────────

@router.get("/schedule")
async def get_schedule():
    """Get current agent schedule with next run times."""
    from Engine8_Knowledge.agents.autonomous.scheduler import get_agent_scheduler

    scheduler = get_agent_scheduler()
    return {
        "running": scheduler.is_running,
        "agents": scheduler.get_schedule(),
    }


@router.post("/start")
async def start_scheduler():
    """Start the autonomous agent scheduler."""
    from Engine8_Knowledge.agents.autonomous.scheduler import get_agent_scheduler

    scheduler = get_agent_scheduler()
    scheduler.start()
    return {"success": True, "running": scheduler.is_running}


@router.post("/stop")
async def stop_scheduler():
    """Stop the autonomous agent scheduler."""
    from Engine8_Knowledge.agents.autonomous.scheduler import get_agent_scheduler

    scheduler = get_agent_scheduler()
    scheduler.stop()
    return {"success": True, "running": scheduler.is_running}


@router.post("/run/{agent_name}")
async def run_agent(agent_name: str):
    """Trigger an agent manually. Available: morning_briefing, contact_enrichment."""
    from Engine8_Knowledge.agents.autonomous.scheduler import get_agent_scheduler

    scheduler = get_agent_scheduler()
    result = scheduler.run_now(agent_name)

    if "error" in result and not result.get("success"):
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/runs")
async def get_runs(limit: int = Query(50, description="Max entries")):
    """Get history of agent executions."""
    from Engine8_Knowledge.agents.autonomous.scheduler import get_runs

    runs = get_runs(limit)
    return {"runs": runs, "count": len(runs)}


# ─── Briefing Endpoints ─────────────────────────────────────────────────────

@router.get("/briefing/latest")
async def get_latest_briefing():
    """Get the most recent morning briefing."""
    from Engine8_Knowledge.agents.autonomous.morning_briefing import MorningBriefingAgent

    agent = MorningBriefingAgent()
    brief = agent.get_latest_brief()

    if not brief:
        return {"available": False, "message": "No briefings generated yet"}

    return {"available": True, "brief": brief.to_dict()}


@router.get("/briefing/{date}")
async def get_briefing_by_date(date: str):
    """Get briefing for a specific date (YYYY-MM-DD)."""
    from Engine8_Knowledge.agents.autonomous.morning_briefing import MorningBriefingAgent

    agent = MorningBriefingAgent()
    brief = agent.get_brief(date)

    if not brief:
        raise HTTPException(status_code=404, detail=f"No briefing found for {date}")

    return {"available": True, "brief": brief.to_dict()}


# ─── Enrichment Endpoints ───────────────────────────────────────────────────

@router.get("/enrichment/report")
async def get_enrichment_report():
    """Get the latest contact enrichment scan results."""
    from Engine8_Knowledge.agents.autonomous.contact_enrichment import ContactEnrichmentAgent

    agent = ContactEnrichmentAgent()
    report = agent.get_latest_report()

    if not report:
        return {"available": False, "message": "No enrichment scans completed yet"}

    return {"available": True, "report": report.to_dict()}
