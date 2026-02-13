"""
Phase 23A — Workflow API Router

18 FastAPI endpoints for production workflow management:
- Workflow execution: start, resume, cancel
- Monitoring: active, history, status, timeline, state
- Time-travel: inspect, diff, replay
- Scheduling: create, list, toggle
- Human-in-the-loop: approvals, decide, stats
- Streaming: SSE event stream
"""

from dataclasses import asdict
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/workflows", tags=["Workflows v2"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class StartWorkflowRequest(BaseModel):
    workflow_name: str
    input_state: Dict[str, Any] = {}
    thread_id: Optional[str] = None


class ResumeWorkflowRequest(BaseModel):
    updated_state: Optional[Dict[str, Any]] = None


class CancelWorkflowRequest(BaseModel):
    reason: str = ""


class ReplayRequest(BaseModel):
    modified_state: Optional[Dict[str, Any]] = None


class ScheduleRequest(BaseModel):
    workflow_name: str
    cron_expression: str
    default_input: Dict[str, Any] = {}
    enabled: bool = True


class ApprovalDecisionRequest(BaseModel):
    decision: str
    modified_state: Optional[Dict[str, Any]] = None
    notes: str = ""
    decided_by: str = "user"


# ---------------------------------------------------------------------------
# Lazy imports
# ---------------------------------------------------------------------------

def _get_orchestrator():
    from Engine8_Knowledge.workflows.orchestrator_v2 import get_workflow_orchestrator
    return get_workflow_orchestrator()


def _get_debugger():
    from Engine8_Knowledge.workflows.time_travel import get_time_travel_debugger
    return get_time_travel_debugger()


def _get_hitl():
    from Engine8_Knowledge.workflows.human_loop import get_hitl_manager
    return get_hitl_manager()


# ---------------------------------------------------------------------------
# Execution endpoints
# ---------------------------------------------------------------------------

@router.post("/start")
async def start_workflow(req: StartWorkflowRequest):
    """Start a workflow execution."""
    try:
        orch = _get_orchestrator()
        execution = await orch.start_workflow(
            workflow_name=req.workflow_name,
            input_state=req.input_state,
            thread_id=req.thread_id,
        )
        return asdict(execution)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("workflow_api.start_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{thread_id}/resume")
async def resume_workflow(thread_id: str, req: ResumeWorkflowRequest):
    """Resume an interrupted workflow."""
    try:
        orch = _get_orchestrator()
        execution = await orch.resume_workflow(thread_id, req.updated_state)
        return asdict(execution)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{thread_id}/cancel")
async def cancel_workflow(thread_id: str, req: CancelWorkflowRequest):
    """Cancel a running workflow."""
    orch = _get_orchestrator()
    success = await orch.cancel_workflow(thread_id, req.reason)
    if not success:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    return {"cancelled": True, "thread_id": thread_id}


# ---------------------------------------------------------------------------
# Monitoring endpoints
# ---------------------------------------------------------------------------

@router.get("/active")
async def get_active_workflows():
    """List all active workflow executions."""
    orch = _get_orchestrator()
    active = await orch.get_active_workflows()
    return {"workflows": [asdict(e) for e in active], "count": len(active)}


@router.get("/history")
async def get_workflow_history(
    workflow_name: Optional[str] = None,
    limit: int = Query(default=20, le=100),
):
    """Workflow execution history."""
    orch = _get_orchestrator()
    history = await orch.get_workflow_history(workflow_name, limit)
    return {"history": [asdict(e) for e in history], "count": len(history)}


@router.get("/{thread_id}/status")
async def get_execution_status(thread_id: str):
    """Get execution status for a specific thread."""
    orch = _get_orchestrator()
    execution = await orch.get_execution_status(thread_id)
    if not execution:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    return asdict(execution)


# ---------------------------------------------------------------------------
# Time-travel endpoints
# ---------------------------------------------------------------------------

@router.get("/{thread_id}/timeline")
async def get_execution_timeline(thread_id: str):
    """Time-travel: full execution timeline."""
    try:
        debugger = _get_debugger()
        timeline = await debugger.get_execution_timeline(thread_id)
        return asdict(timeline)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{thread_id}/state/{step}")
async def get_state_at_step(thread_id: str, step: int):
    """Time-travel: state at specific step."""
    try:
        debugger = _get_debugger()
        state = await debugger.inspect_state_at(thread_id, step)
        return state
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{thread_id}/diff")
async def diff_states(
    thread_id: str,
    step_a: int = Query(...),
    step_b: int = Query(...),
):
    """Time-travel: diff between two checkpoint states."""
    try:
        debugger = _get_debugger()
        diff = await debugger.diff_states(thread_id, step_a, step_b)
        return asdict(diff)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{thread_id}/replay/{step}")
async def replay_from_step(thread_id: str, step: int, req: ReplayRequest):
    """Time-travel: fork from a checkpoint and optionally modify state."""
    try:
        debugger = _get_debugger()
        new_tid = await debugger.replay_from(thread_id, step, req.modified_state)
        return {"forked_thread_id": new_tid, "original_thread_id": thread_id, "from_step": step}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------------------------------------------------------------------------
# Streaming endpoint
# ---------------------------------------------------------------------------

@router.get("/{thread_id}/stream")
async def stream_workflow_events(thread_id: str):
    """SSE stream of workflow events."""
    import json

    orch = _get_orchestrator()

    async def event_generator():
        async for event in orch.stream_workflow(thread_id):
            data = json.dumps(asdict(event), default=str)
            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# Registry endpoint
# ---------------------------------------------------------------------------

@router.get("/registry")
async def list_registered_workflows():
    """List all registered workflow definitions."""
    orch = _get_orchestrator()
    workflows = orch.list_workflows()
    return {
        "workflows": [asdict(w) for w in workflows],
        "count": len(workflows),
    }


# ---------------------------------------------------------------------------
# Schedule endpoints
# ---------------------------------------------------------------------------

@router.get("/schedules")
async def list_schedules():
    """List all workflow schedules."""
    orch = _get_orchestrator()
    schedules = await orch.list_schedules()
    return {"schedules": [asdict(s) for s in schedules], "count": len(schedules)}


@router.post("/schedules")
async def create_schedule(req: ScheduleRequest):
    """Create a new workflow schedule."""
    try:
        orch = _get_orchestrator()
        schedule = await orch.schedule_workflow(
            workflow_name=req.workflow_name,
            cron_expression=req.cron_expression,
            default_input=req.default_input,
            enabled=req.enabled,
        )
        return asdict(schedule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/schedules/{schedule_id}")
async def toggle_schedule(schedule_id: str, enabled: bool = Query(...)):
    """Toggle a schedule on/off."""
    orch = _get_orchestrator()
    success = await orch.toggle_schedule(schedule_id, enabled)
    if not success:
        raise HTTPException(status_code=404, detail=f"Schedule {schedule_id} not found")
    return {"schedule_id": schedule_id, "enabled": enabled}


# ---------------------------------------------------------------------------
# Human-in-the-loop endpoints
# ---------------------------------------------------------------------------

@router.get("/approvals")
async def list_pending_approvals(
    workflow_name: Optional[str] = None,
    urgency: Optional[str] = None,
    limit: int = Query(default=20, le=100),
):
    """List pending human approvals."""
    hitl = _get_hitl()
    approvals = await hitl.list_pending_approvals(workflow_name, urgency, limit)
    return {"approvals": [asdict(a) for a in approvals], "count": len(approvals)}


@router.post("/approvals/{request_id}/decide")
async def submit_approval_decision(request_id: str, req: ApprovalDecisionRequest):
    """Submit a human decision for an approval request."""
    try:
        hitl = _get_hitl()
        decision = await hitl.submit_decision(
            request_id=request_id,
            decision=req.decision,
            modified_state=req.modified_state,
            notes=req.notes,
            decided_by=req.decided_by,
        )
        return asdict(decision)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/approvals/stats")
async def get_approval_stats():
    """Approval response metrics."""
    hitl = _get_hitl()
    return await hitl.get_approval_stats()


# ---------------------------------------------------------------------------
# Stats endpoint
# ---------------------------------------------------------------------------

@router.get("/stats")
async def get_workflow_stats():
    """Overall workflow execution stats."""
    orch = _get_orchestrator()
    return await orch.get_stats()
