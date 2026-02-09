"""
Phase 19A — Automation API Routes

Endpoints for scheduled tasks, multi-agent workflows, and Auto Claude task management.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automation", tags=["automation"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class WorkflowRunRequest(BaseModel):
    workflow: str = Field(..., description="Workflow name to execute")
    params: dict = Field(default_factory=dict, description="Parameters for the workflow")


class ClaudeTaskRequest(BaseModel):
    task_type: str = Field(..., description="Task type: deep_research, contact_analysis, competitive_brief, proposal_section, data_reconciliation")
    prompt: str = Field(..., description="The research prompt/question")
    context_documents: list[str] = Field(default_factory=list, description="Paths to context files")
    context_data: dict = Field(default_factory=dict, description="Structured context data")
    priority: str = Field("normal", description="Priority: low, normal, high, urgent")


# ---------------------------------------------------------------------------
# Scheduled Tasks Endpoints
# ---------------------------------------------------------------------------

@router.get("/schedule")
async def get_schedule():
    """Get all scheduled tasks with next run times."""
    from Engine8_Knowledge.automation.task_scheduler import get_task_scheduler
    scheduler = get_task_scheduler()
    return {
        "tasks": scheduler.get_schedule(),
        "total": len(scheduler.get_schedule()),
    }


@router.post("/tasks/{name}/run")
async def run_task_now(name: str):
    """Trigger a scheduled task immediately."""
    from Engine8_Knowledge.automation.task_scheduler import get_task_scheduler
    scheduler = get_task_scheduler()
    result = await scheduler.run_now(name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/tasks/{name}/enable")
async def toggle_task(name: str, enabled: bool = Query(True)):
    """Enable or disable a scheduled task."""
    from Engine8_Knowledge.automation.task_scheduler import get_task_scheduler
    scheduler = get_task_scheduler()
    if enabled:
        ok = scheduler.enable_task(name)
    else:
        ok = scheduler.disable_task(name)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Task not found: {name}")
    return {"task": name, "enabled": enabled}


@router.get("/tasks/history")
async def get_task_history(
    name: Optional[str] = Query(None, description="Filter by task name"),
    days: int = Query(7, description="Number of days to look back"),
):
    """Get execution history for scheduled tasks."""
    from Engine8_Knowledge.automation.task_scheduler import get_task_scheduler
    scheduler = get_task_scheduler()
    history = scheduler.get_execution_history(name=name, days=days)
    return {"history": history, "total": len(history)}


# ---------------------------------------------------------------------------
# Multi-Agent Workflow Endpoints
# ---------------------------------------------------------------------------

@router.get("/workflows/definitions")
async def get_workflow_definitions():
    """List available workflow definitions."""
    from Engine8_Knowledge.automation.agent_coordinator import get_agent_coordinator
    coordinator = get_agent_coordinator()
    return {
        "workflows": coordinator.get_workflow_definitions(),
        "total": len(coordinator.workflows),
    }


@router.post("/workflows/run")
async def start_workflow(req: WorkflowRunRequest):
    """Start a multi-agent workflow."""
    from Engine8_Knowledge.automation.agent_coordinator import get_agent_coordinator
    coordinator = get_agent_coordinator()
    result = await coordinator.run_workflow(req.workflow, req.params)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/workflows/active")
async def get_active_workflows():
    """Get all currently active workflow runs."""
    from Engine8_Knowledge.automation.agent_coordinator import get_agent_coordinator
    coordinator = get_agent_coordinator()
    active = coordinator.get_active_workflows()
    return {"active": active, "total": len(active)}


@router.get("/workflows/{run_id}")
async def get_workflow_run(run_id: str):
    """Get details of a specific workflow run."""
    from Engine8_Knowledge.automation.agent_coordinator import get_agent_coordinator
    coordinator = get_agent_coordinator()
    run = coordinator.get_workflow_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return run


@router.post("/workflows/{run_id}/approve")
async def approve_workflow_gate(run_id: str):
    """Approve a human gate in a paused workflow."""
    from Engine8_Knowledge.automation.agent_coordinator import get_agent_coordinator
    coordinator = get_agent_coordinator()
    result = await coordinator.approve_human_gate(run_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/workflows/{run_id}/cancel")
async def cancel_workflow(run_id: str):
    """Cancel an active workflow."""
    from Engine8_Knowledge.automation.agent_coordinator import get_agent_coordinator
    coordinator = get_agent_coordinator()
    result = coordinator.cancel_workflow(run_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/workflows/history")
async def get_workflow_history(limit: int = Query(50)):
    """Get completed workflow history."""
    from Engine8_Knowledge.automation.agent_coordinator import get_agent_coordinator
    coordinator = get_agent_coordinator()
    history = coordinator.get_workflow_history(limit=limit)
    return {"history": history, "total": len(history)}


# ---------------------------------------------------------------------------
# Auto Claude Task Endpoints
# ---------------------------------------------------------------------------

@router.post("/claude/submit")
async def submit_claude_task(req: ClaudeTaskRequest):
    """Submit a research task for Claude."""
    from Engine8_Knowledge.automation.auto_claude_tasks import get_claude_task_manager
    mgr = get_claude_task_manager()
    result = mgr.submit_task(
        task_type=req.task_type,
        prompt=req.prompt,
        context_documents=req.context_documents,
        context_data=req.context_data,
        priority=req.priority,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/claude/queue")
async def get_claude_queue():
    """Get pending Claude tasks."""
    from Engine8_Knowledge.automation.auto_claude_tasks import get_claude_task_manager
    mgr = get_claude_task_manager()
    return {
        "pending": mgr.list_pending_tasks(),
        "stats": mgr.get_stats(),
    }


@router.get("/claude/tasks")
async def list_all_claude_tasks():
    """List all Claude tasks across all statuses."""
    from Engine8_Knowledge.automation.auto_claude_tasks import get_claude_task_manager
    mgr = get_claude_task_manager()
    return {
        "tasks": mgr.list_all_tasks(),
        "stats": mgr.get_stats(),
    }


@router.get("/claude/results/{task_id}")
async def get_claude_results(task_id: str):
    """Get results for a completed Claude task."""
    from Engine8_Knowledge.automation.auto_claude_tasks import get_claude_task_manager
    mgr = get_claude_task_manager()
    status = mgr.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    results = mgr.get_results(task_id)
    return {"task": status, "results": results}


@router.get("/claude/prompt/{task_id}")
async def build_claude_prompt(task_id: str):
    """Build the full Claude API prompt for a task (for debugging/preview)."""
    from Engine8_Knowledge.automation.auto_claude_tasks import get_claude_task_manager
    mgr = get_claude_task_manager()
    prompt = mgr.build_claude_prompt(task_id)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return prompt
