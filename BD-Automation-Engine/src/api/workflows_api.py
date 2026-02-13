"""Phase 49A — Workflow Intelligence API (12 endpoints).

REST endpoints for Temporal durable workflows, cross-project orchestration,
and natural language workflow creation.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from src.workflows.temporal_engine import (
    get_temporal_engine, WorkflowStatus,
)
from src.workflows.cross_project_orchestrator import (
    get_orchestrator, TaskQueueName,
    TaskPriority,
)
from src.workflows.nl_to_workflow import (
    get_nl_engine,
)

logger = logging.getLogger(__name__)


# =========================================
# REQUEST MODELS
# =========================================

class StartWorkflowRequest(BaseModel):
    workflow_id: str
    params: Optional[Dict[str, Any]] = None
    execute: bool = True


class SubmitTaskRequest(BaseModel):
    name: str
    payload: Optional[Dict[str, Any]] = None
    priority: int = 2  # 0=critical, 1=high, 2=normal, 3=low
    depends_on: Optional[List[str]] = None
    queue: Optional[str] = None


class FanOutRequest(BaseModel):
    task_names: List[str]
    payload: Optional[Dict[str, Any]] = None
    priority: int = 2


class NLExecuteRequest(BaseModel):
    text: str


class NLAutocompleteRequest(BaseModel):
    partial: str


# =========================================
# ROUTE SETUP
# =========================================

def include_workflows_router(app: FastAPI) -> None:
    """Register all workflow intelligence endpoints on the FastAPI app."""

    engine = get_temporal_engine()
    orchestrator = get_orchestrator()
    nl_engine = get_nl_engine()

    # --------------------------------------------------
    # 1. GET /api/workflows — List workflow definitions
    # --------------------------------------------------
    @app.get("/api/workflows")
    async def list_workflows():
        """List all available workflow definitions."""
        workflows = engine.list_workflows()
        return {
            "workflows": [w.to_dict() for w in workflows],
            "total": len(workflows),
        }

    # --------------------------------------------------
    # 2. POST /api/workflows/start — Start a workflow run
    # --------------------------------------------------
    @app.post("/api/workflows/start")
    async def start_workflow(req: StartWorkflowRequest):
        """Start (and optionally execute) a workflow run."""
        try:
            run = engine.start_workflow(req.workflow_id, req.params)
        except ValueError as e:
            raise HTTPException(400, str(e))

        if req.execute:
            run = engine.execute_workflow(run.run_id)

        return run.to_dict()

    # --------------------------------------------------
    # 3. GET /api/workflows/runs — List workflow runs
    # --------------------------------------------------
    @app.get("/api/workflows/runs")
    async def list_runs(
        workflow_id: str = Query("", description="Filter by workflow ID"),
        status: str = Query("", description="Filter by status"),
    ):
        """List workflow runs with optional filters."""
        wf_filter = workflow_id or None
        st_filter = None
        if status:
            try:
                st_filter = WorkflowStatus(status)
            except ValueError:
                raise HTTPException(400, f"Invalid status: {status}")

        runs = engine.list_runs(workflow_id=wf_filter, status=st_filter)
        return {
            "runs": [r.to_dict() for r in runs],
            "total": len(runs),
        }

    # --------------------------------------------------
    # 4. GET /api/workflows/runs/{run_id} — Get run details
    # --------------------------------------------------
    @app.get("/api/workflows/runs/{run_id}")
    async def get_run(run_id: str):
        """Get detailed status of a workflow run."""
        run = engine.get_run(run_id)
        if not run:
            raise HTTPException(404, f"Run not found: {run_id}")
        return run.to_dict()

    # --------------------------------------------------
    # 5. GET /api/workflows/runs/{run_id}/timeline — Time-travel timeline
    # --------------------------------------------------
    @app.get("/api/workflows/runs/{run_id}/timeline")
    async def get_timeline(run_id: str):
        """Get step-by-step timeline for time-travel debugging."""
        timeline = engine.get_timeline(run_id)
        if not timeline and not engine.get_run(run_id):
            raise HTTPException(404, f"Run not found: {run_id}")
        return {
            "run_id": run_id,
            "steps": timeline,
            "total_steps": len(timeline),
        }

    # --------------------------------------------------
    # 6. POST /api/workflows/runs/{run_id}/replay — Replay a run
    # --------------------------------------------------
    @app.post("/api/workflows/runs/{run_id}/replay")
    async def replay_run(run_id: str):
        """Time-travel: re-execute a workflow run with same params."""
        new_run = engine.replay_run(run_id)
        if not new_run:
            raise HTTPException(404, f"Run not found: {run_id}")
        return new_run.to_dict()

    # --------------------------------------------------
    # 7. POST /api/workflows/tasks — Submit orchestrator task
    # --------------------------------------------------
    @app.post("/api/workflows/tasks")
    async def submit_task(req: SubmitTaskRequest):
        """Submit a task to the cross-project orchestrator."""
        priority = TaskPriority(min(max(req.priority, 0), 3))
        queue = None
        if req.queue:
            try:
                queue = TaskQueueName(req.queue)
            except ValueError:
                raise HTTPException(400, f"Invalid queue: {req.queue}")

        task = orchestrator.submit_task(
            name=req.name,
            payload=req.payload,
            priority=priority,
            depends_on=req.depends_on,
            queue=queue,
        )
        return task.to_dict()

    # --------------------------------------------------
    # 8. GET /api/workflows/queues — Queue status overview
    # --------------------------------------------------
    @app.get("/api/workflows/queues")
    async def get_queues():
        """Get status of all task queues."""
        return {
            "queues": orchestrator.get_all_queues(),
            "total_queues": 3,
        }

    # --------------------------------------------------
    # 9. POST /api/workflows/fan-out — Fan-out tasks
    # --------------------------------------------------
    @app.post("/api/workflows/fan-out")
    async def fan_out(req: FanOutRequest):
        """Fan-out: dispatch multiple tasks in parallel."""
        priority = TaskPriority(min(max(req.priority, 0), 3))
        result = orchestrator.fan_out(
            task_names=req.task_names,
            shared_payload=req.payload,
            priority=priority,
        )
        return result.to_dict()

    # --------------------------------------------------
    # 10. POST /api/workflows/nl/execute — NL to workflow
    # --------------------------------------------------
    @app.post("/api/workflows/nl/execute")
    async def nl_execute(req: NLExecuteRequest):
        """Execute a workflow from natural language instruction."""
        result = nl_engine.execute(req.text)
        return result.to_dict()

    # --------------------------------------------------
    # 11. POST /api/workflows/nl/autocomplete — NL autocomplete
    # --------------------------------------------------
    @app.post("/api/workflows/nl/autocomplete")
    async def nl_autocomplete(req: NLAutocompleteRequest):
        """Get autocomplete suggestions for partial NL input."""
        suggestions = nl_engine.autocomplete(req.partial)
        return {
            "partial": req.partial,
            "suggestions": suggestions,
            "total": len(suggestions),
        }

    # --------------------------------------------------
    # 12. GET /api/workflows/stats — Workflow system stats
    # --------------------------------------------------
    @app.get("/api/workflows/stats")
    async def workflow_stats():
        """Combined stats from all workflow subsystems."""
        return {
            "temporal": engine.get_stats(),
            "orchestrator": orchestrator.get_stats(),
            "nl_engine": nl_engine.get_stats(),
        }

    logger.info("Workflow Intelligence API: 12 endpoints registered under /api/workflows/*")
