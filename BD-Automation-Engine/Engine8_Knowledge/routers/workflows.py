"""Workflow orchestration router -- run, schedule, and monitor LangGraph workflows."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("BDKnowledgeAPI")

router = APIRouter(prefix="/workflows", tags=["Workflow Orchestration"])


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------

class WorkflowRunRequest(BaseModel):
    """Optional configuration for an on-demand workflow run."""
    input_path: Optional[str] = Field(None, description="Path to input JSON file")
    test_mode: bool = Field(False, description="Limit processing for testing")
    batch_size: int = Field(50, ge=1, le=1000)


class ScheduleToggleRequest(BaseModel):
    """Toggle scheduled workflow execution."""
    enabled: bool


# ---------------------------------------------------------------------------
# Workflow registry
# ---------------------------------------------------------------------------

WORKFLOW_REGISTRY = {
    "master_pipeline",
    "morning_briefing",
    "contact_enrichment",
}


def _run_workflow(name: str, config: Optional[WorkflowRunRequest] = None) -> Dict[str, Any]:
    """Dispatch to the correct workflow runner."""
    started = datetime.utcnow()

    if name == "master_pipeline":
        from workflows.master_pipeline import run_master_pipeline
        from workflows.state import WorkflowConfig
        cfg = WorkflowConfig(
            input_path=config.input_path if config else None,
            test_mode=config.test_mode if config else False,
            batch_size=config.batch_size if config else 50,
        )
        result = run_master_pipeline(config=cfg)
    elif name == "morning_briefing":
        from workflows.morning_briefing import run_morning_briefing
        result = run_morning_briefing()
    elif name == "contact_enrichment":
        from workflows.contact_enrichment import run_contact_enrichment
        result = run_contact_enrichment()
    else:
        raise ValueError(f"Unknown workflow: {name}")

    duration = (datetime.utcnow() - started).total_seconds()

    # Record in scheduler history
    from workflows.scheduler import _record_execution
    errors = result.get("errors", [])
    _record_execution(name, success=len(errors) == 0, duration=duration)

    return {
        "workflow": name,
        "duration_seconds": duration,
        "errors": errors,
        "result": _sanitize_result(result),
    }


def _sanitize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Strip large lists from the result for API response."""
    sanitized = {}
    for key, value in result.items():
        if isinstance(value, list) and len(value) > 10:
            sanitized[key] = f"[{len(value)} items]"
        else:
            sanitized[key] = value
    return sanitized


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/run/{workflow_name}")
async def run_workflow(workflow_name: str, body: Optional[WorkflowRunRequest] = None):
    """Run a workflow on-demand by name."""
    if workflow_name not in WORKFLOW_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown workflow '{workflow_name}'. Available: {sorted(WORKFLOW_REGISTRY)}",
        )
    try:
        import asyncio
        result = await asyncio.to_thread(_run_workflow, workflow_name, body)
        return result
    except Exception as exc:
        logger.error(f"Workflow '{workflow_name}' failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/status")
async def workflow_status():
    """Get scheduler status and registered jobs."""
    from workflows.scheduler import get_scheduler
    scheduler = get_scheduler()
    return scheduler.get_status()


@router.get("/history")
async def workflow_history(limit: int = 20):
    """Get recent workflow execution history."""
    from workflows.scheduler import get_execution_history
    history = get_execution_history(limit=limit)
    return {"history": history, "total": len(history)}


@router.post("/schedule/toggle")
async def toggle_schedule(body: ScheduleToggleRequest):
    """Enable or disable the workflow scheduler."""
    from workflows.scheduler import get_scheduler
    scheduler = get_scheduler()
    scheduler.toggle(body.enabled)
    return {
        "enabled": body.enabled,
        "status": scheduler.get_status(),
    }
