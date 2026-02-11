"""Phase 41A — Swarm API (10 endpoints)

REST endpoints for multi-agent swarm coordination, task decomposition,
worker management, and execution monitoring.
"""

import logging
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from src.agents.swarm.coordinator import (
    SwarmCoordinator, SwarmTask, SwarmResult, SwarmStatus,
    CoordinationMode, get_swarm_coordinator,
)
from src.agents.swarm.decomposer import (
    TaskDecomposer, TaskDAG, get_task_decomposer,
)
from src.agents.swarm.workers import (
    WorkerRegistry, get_worker_registry,
)

logger = logging.getLogger(__name__)


# =========================================
# REQUEST / RESPONSE MODELS
# =========================================

class SwarmExecuteRequest(BaseModel):
    description: str = Field(..., min_length=5)
    task_type: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    coordination_mode: str = "parallel"
    quality_threshold: float = 0.7
    timeout_minutes: int = 10
    budget_tokens: int = 50000


class DecomposeRequest(BaseModel):
    description: str = Field(..., min_length=5)
    task_type: str = ""


class EstimateRequest(BaseModel):
    description: str = Field(..., min_length=5)
    task_type: str = ""


# =========================================
# ROUTE SETUP
# =========================================

def include_swarm_router(app: FastAPI) -> None:
    """Register all swarm endpoints on the FastAPI app."""

    coordinator = get_swarm_coordinator()
    decomposer = get_task_decomposer()
    registry = get_worker_registry()

    # --------------------------------------------------
    # 1. POST /swarm/execute — Full swarm execution
    # --------------------------------------------------
    @app.post("/swarm/execute")
    async def swarm_execute(req: SwarmExecuteRequest):
        """Execute a full swarm pipeline for a high-level BD task."""
        task = SwarmTask(
            description=req.description,
            task_type=req.task_type,
            parameters=req.parameters,
            coordination_mode=req.coordination_mode,
            quality_threshold=req.quality_threshold,
            timeout_minutes=req.timeout_minutes,
            budget_tokens=req.budget_tokens,
        )
        result = await coordinator.execute_swarm(task)
        return _serialize_result(result)

    # --------------------------------------------------
    # 2. GET /swarm/status/{swarm_id} — Live swarm status
    # --------------------------------------------------
    @app.get("/swarm/status/{swarm_id}")
    async def swarm_status(swarm_id: str):
        """Get live status of a running swarm."""
        state = await coordinator.monitor_swarm(swarm_id)
        if not state:
            raise HTTPException(status_code=404, detail="Swarm not found")
        return {
            "swarm_id": state.swarm_id,
            "status": state.status,
            "completed_workers": state.completed_workers,
            "failed_workers": state.failed_workers,
            "total_workers": state.total_workers,
            "current_layer": state.current_layer,
            "started_at": state.started_at,
            "updated_at": state.updated_at,
        }

    # --------------------------------------------------
    # 3. GET /swarm/result/{swarm_id} — Completed result
    # --------------------------------------------------
    @app.get("/swarm/result/{swarm_id}")
    async def swarm_result(swarm_id: str):
        """Get result of a completed swarm execution."""
        for r in coordinator.get_history():
            if r.swarm_id == swarm_id:
                return _serialize_result(r)
        raise HTTPException(status_code=404, detail="Swarm result not found")

    # --------------------------------------------------
    # 4. POST /swarm/decompose — Decompose task into DAG
    # --------------------------------------------------
    @app.post("/swarm/decompose")
    async def swarm_decompose(req: DecomposeRequest):
        """Decompose a task into a dependency DAG without executing."""
        dag = await decomposer.decompose(req.description, req.task_type)
        return _serialize_dag(dag)

    # --------------------------------------------------
    # 5. GET /swarm/dag/{dag_id} — Get DAG details
    # --------------------------------------------------
    @app.get("/swarm/dag/{dag_id}")
    async def swarm_dag(dag_id: str):
        """Retrieve a previously decomposed DAG by ID."""
        for dag in decomposer.get_history():
            if dag.dag_id == dag_id:
                return _serialize_dag(dag)
        raise HTTPException(status_code=404, detail="DAG not found")

    # --------------------------------------------------
    # 6. POST /swarm/estimate — Cost/time estimate
    # --------------------------------------------------
    @app.post("/swarm/estimate")
    async def swarm_estimate(req: EstimateRequest):
        """Estimate cost and time for a task without executing."""
        dag = await decomposer.decompose(req.description, req.task_type)
        cost = await decomposer.estimate_cost(dag)
        return {
            "dag_id": dag.dag_id,
            "total_tokens": cost.total_tokens,
            "total_api_cost_usd": cost.total_api_cost_usd,
            "estimated_time_seconds": cost.estimated_time_seconds,
            "critical_path_seconds": cost.critical_path_seconds,
            "num_workers": cost.num_workers,
            "num_parallel_groups": cost.num_parallel_groups,
            "worker_breakdown": cost.worker_breakdown,
        }

    # --------------------------------------------------
    # 7. GET /swarm/workers — List all worker types
    # --------------------------------------------------
    @app.get("/swarm/workers")
    async def swarm_workers():
        """List all registered worker types and their capabilities."""
        caps = registry.get_all_capabilities()
        return {
            "workers": [
                {
                    "worker_type": cap.worker_type,
                    "description": cap.description,
                    "tools": cap.tools,
                    "output_fields": cap.output_fields,
                    "avg_tokens": cap.avg_tokens,
                    "avg_time_seconds": cap.avg_time_seconds,
                }
                for cap in caps.values()
            ],
            "total": len(caps),
        }

    # --------------------------------------------------
    # 8. GET /swarm/workers/{worker_type}/stats — Worker stats
    # --------------------------------------------------
    @app.get("/swarm/workers/{worker_type}/stats")
    async def swarm_worker_stats(worker_type: str):
        """Get performance statistics for a specific worker type."""
        stats = registry.get_stats(worker_type)
        if not stats:
            raise HTTPException(status_code=404, detail="Worker type not found")
        return {
            "worker_type": stats.worker_type,
            "total_executions": stats.total_executions,
            "successful": stats.successful,
            "failed": stats.failed,
            "avg_latency_seconds": round(stats.avg_latency_seconds, 2),
            "avg_tokens_used": stats.avg_tokens_used,
            "avg_quality_score": round(stats.avg_quality_score, 4),
        }

    # --------------------------------------------------
    # 9. GET /swarm/history — Execution history
    # --------------------------------------------------
    @app.get("/swarm/history")
    async def swarm_history(
        limit: int = Query(20, ge=1, le=100),
    ):
        """Get recent swarm execution history."""
        history = coordinator.get_history()
        recent = history[-limit:] if len(history) > limit else history
        return {
            "executions": [
                {
                    "swarm_id": r.swarm_id,
                    "task_description": r.task_description[:100],
                    "status": r.status,
                    "workers_used": r.workers_used,
                    "total_tokens": r.total_tokens,
                    "total_time_seconds": r.total_time_seconds,
                    "quality_score": r.quality_score,
                }
                for r in reversed(recent)
            ],
            "total": len(history),
        }

    # --------------------------------------------------
    # 10. POST /swarm/cancel/{swarm_id} — Cancel swarm
    # --------------------------------------------------
    @app.post("/swarm/cancel/{swarm_id}")
    async def swarm_cancel(swarm_id: str):
        """Cancel a running swarm execution."""
        cancelled = await coordinator.cancel_swarm(swarm_id)
        if not cancelled:
            raise HTTPException(status_code=404, detail="Swarm not found or already completed")
        return {"swarm_id": swarm_id, "status": "cancelled"}

    logger.info("Swarm API: 10 endpoints registered under /swarm/*")


# =========================================
# SERIALIZATION HELPERS
# =========================================

def _serialize_dag(dag: TaskDAG) -> Dict[str, Any]:
    """Serialize a TaskDAG to a JSON-safe dict."""
    return {
        "dag_id": dag.dag_id,
        "root_task": dag.root_task,
        "nodes": [
            {
                "id": n.id,
                "description": n.description,
                "worker_type": n.worker_type,
                "depends_on": n.depends_on,
                "priority": n.priority,
            }
            for n in dag.nodes
        ],
        "edges": [{"from": e[0], "to": e[1]} for e in dag.edges],
        "execution_layers": dag.execution_layers,
        "total_estimated_tokens": dag.total_estimated_tokens,
        "total_estimated_seconds": dag.total_estimated_seconds,
        "critical_path_seconds": dag.critical_path_seconds,
    }


def _serialize_result(result: SwarmResult) -> Dict[str, Any]:
    """Serialize a SwarmResult to a JSON-safe dict."""
    data = {
        "swarm_id": result.swarm_id,
        "task_description": result.task_description,
        "status": result.status,
        "output": result.output,
        "workers_used": result.workers_used,
        "total_tokens": result.total_tokens,
        "total_time_seconds": result.total_time_seconds,
        "quality_score": result.quality_score,
        "provenance": result.provenance,
        "error": result.error,
    }

    if result.dag:
        data["dag"] = _serialize_dag(result.dag)

    if result.cost_estimate:
        data["cost_estimate"] = {
            "total_tokens": result.cost_estimate.total_tokens,
            "total_api_cost_usd": result.cost_estimate.total_api_cost_usd,
            "estimated_time_seconds": result.cost_estimate.estimated_time_seconds,
            "critical_path_seconds": result.cost_estimate.critical_path_seconds,
            "num_workers": result.cost_estimate.num_workers,
            "num_parallel_groups": result.cost_estimate.num_parallel_groups,
        }

    if result.worker_results:
        data["worker_results"] = [
            {
                "worker_id": wr.worker_id,
                "worker_type": wr.worker_type,
                "task_id": wr.task_id,
                "status": wr.status,
                "tokens_used": wr.tokens_used,
                "latency_seconds": wr.latency_seconds,
                "quality_score": wr.quality_score,
                "error": wr.error,
            }
            for wr in result.worker_results
        ]

    return data
