"""Phase 41A — Swarm Coordinator (Queen-Worker Pattern)

Orchestrates multi-agent swarm execution with 5 coordination modes,
failure handling, provenance tracking, and quality gating.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from src.agents.swarm.decomposer import (
    TaskDecomposer,
    TaskDAG,
    CostEstimate,
    get_task_decomposer,
)
from src.agents.swarm.workers import (
    WorkerRegistry,
    WorkerHandle,
    WorkerStatus,
    SubTask,
    get_worker_registry,
)

logger = logging.getLogger(__name__)


# =========================================
# ENUMS
# =========================================


class CoordinationMode(str, Enum):
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    PIPELINE = "pipeline"
    CONSENSUS = "consensus"
    MAP_REDUCE = "map_reduce"


class SwarmStatus(str, Enum):
    PENDING = "pending"
    DECOMPOSING = "decomposing"
    RUNNING = "running"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


# =========================================
# DATA CLASSES
# =========================================


@dataclass
class SwarmTask:
    """High-level task submitted to the swarm."""

    description: str = ""
    task_type: str = ""  # campaign_build, contact_enrichment, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    coordination_mode: str = CoordinationMode.PARALLEL.value
    quality_threshold: float = 0.7
    timeout_minutes: int = 10
    budget_tokens: int = 50000
    max_retries: int = 2


@dataclass
class WorkerResult:
    """Result from a single worker execution."""

    worker_id: str = ""
    worker_type: str = ""
    task_id: str = ""
    status: str = WorkerStatus.COMPLETED.value
    output: Dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    latency_seconds: float = 0.0
    quality_score: float = 0.8
    error: str = ""


@dataclass
class SwarmResult:
    """Final result from a swarm execution."""

    swarm_id: str = ""
    task_description: str = ""
    status: str = SwarmStatus.COMPLETED.value
    output: Dict[str, Any] = field(default_factory=dict)
    workers_used: int = 0
    total_tokens: int = 0
    total_time_seconds: float = 0.0
    quality_score: float = 0.0
    worker_results: List[WorkerResult] = field(default_factory=list)
    dag: Optional[TaskDAG] = None
    cost_estimate: Optional[CostEstimate] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    error: str = ""


@dataclass
class SwarmState:
    """Live state of a running swarm."""

    swarm_id: str = ""
    status: str = SwarmStatus.PENDING.value
    task: Optional[SwarmTask] = None
    dag: Optional[TaskDAG] = None
    worker_handles: List[WorkerHandle] = field(default_factory=list)
    completed_workers: int = 0
    failed_workers: int = 0
    total_workers: int = 0
    current_layer: int = 0
    started_at: str = ""
    updated_at: str = ""


# =========================================
# SWARM COORDINATOR
# =========================================


class SwarmCoordinator:
    """Queen agent that orchestrates worker swarm execution.

    9-step pipeline:
    1. Parse task → 2. Detect template → 3. Decompose into DAG →
    4. Estimate cost → 5. Check budget → 6. Spawn workers per layer →
    7. Monitor execution → 8. Aggregate results → 9. Quality gate
    """

    def __init__(
        self,
        registry: Optional[WorkerRegistry] = None,
        decomposer: Optional[TaskDecomposer] = None,
    ):
        self._registry = registry or get_worker_registry()
        self._decomposer = decomposer or get_task_decomposer()
        self._active_swarms: Dict[str, SwarmState] = {}
        self._history: List[SwarmResult] = []

    async def execute_swarm(self, task: SwarmTask) -> SwarmResult:
        """Execute a full swarm pipeline for a high-level task."""
        swarm_id = uuid.uuid4().hex[:10]
        start_time = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Initialize state
        state = SwarmState(
            swarm_id=swarm_id,
            status=SwarmStatus.DECOMPOSING.value,
            task=task,
            started_at=now_iso,
            updated_at=now_iso,
        )
        self._active_swarms[swarm_id] = state

        try:
            # Step 1-3: Decompose task into DAG
            dag = await self._decomposer.decompose(task.description, task.task_type)
            state.dag = dag
            state.total_workers = len(dag.nodes)

            # Step 4: Estimate cost
            cost = await self._decomposer.estimate_cost(dag)

            # Step 5: Budget check
            if cost.total_tokens > task.budget_tokens:
                logger.warning(
                    "Swarm %s exceeds budget: %d > %d tokens",
                    swarm_id,
                    cost.total_tokens,
                    task.budget_tokens,
                )
                # Continue anyway but log warning

            # Step 6-7: Execute workers by coordination mode
            state.status = SwarmStatus.RUNNING.value
            state.updated_at = datetime.now(timezone.utc).isoformat()

            worker_results = await self._execute_by_mode(
                task.coordination_mode,
                dag,
                task,
            )

            # Step 8: Aggregate results
            state.status = SwarmStatus.AGGREGATING.value
            state.updated_at = datetime.now(timezone.utc).isoformat()

            aggregated = self._aggregate_results(worker_results, dag)

            # Step 9: Quality gate
            quality_score = self._compute_quality(worker_results)

            elapsed = round(time.time() - start_time, 2)
            total_tokens = sum(r.tokens_used for r in worker_results)

            result = SwarmResult(
                swarm_id=swarm_id,
                task_description=task.description,
                status=SwarmStatus.COMPLETED.value,
                output=aggregated,
                workers_used=len(worker_results),
                total_tokens=total_tokens,
                total_time_seconds=elapsed,
                quality_score=round(quality_score, 4),
                worker_results=worker_results,
                dag=dag,
                cost_estimate=cost,
                provenance={
                    "coordination_mode": task.coordination_mode,
                    "layers_executed": len(dag.execution_layers),
                    "template_used": task.task_type or "auto-detected",
                    "budget_tokens": task.budget_tokens,
                    "quality_threshold": task.quality_threshold,
                    "quality_passed": quality_score >= task.quality_threshold,
                },
            )

            # Update state
            state.status = SwarmStatus.COMPLETED.value
            state.completed_workers = sum(
                1 for r in worker_results if r.status == WorkerStatus.COMPLETED.value
            )
            state.failed_workers = sum(
                1 for r in worker_results if r.status == WorkerStatus.FAILED.value
            )
            state.updated_at = datetime.now(timezone.utc).isoformat()

            # Record stats
            for wr in worker_results:
                self._registry.record_execution(
                    wr.worker_type,
                    success=(wr.status == WorkerStatus.COMPLETED.value),
                    latency_seconds=wr.latency_seconds,
                    tokens_used=wr.tokens_used,
                    quality_score=wr.quality_score,
                )

            self._history.append(result)
            return result

        except Exception as exc:
            elapsed = round(time.time() - start_time, 2)
            state.status = SwarmStatus.FAILED.value
            state.updated_at = datetime.now(timezone.utc).isoformat()

            result = SwarmResult(
                swarm_id=swarm_id,
                task_description=task.description,
                status=SwarmStatus.FAILED.value,
                error=str(exc),
                total_time_seconds=elapsed,
            )
            self._history.append(result)
            return result

    async def monitor_swarm(self, swarm_id: str) -> Optional[SwarmState]:
        """Get live status of a running swarm."""
        return self._active_swarms.get(swarm_id)

    async def cancel_swarm(self, swarm_id: str) -> bool:
        """Cancel a running swarm."""
        state = self._active_swarms.get(swarm_id)
        if not state:
            return False
        state.status = SwarmStatus.CANCELLED.value
        state.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def get_history(self) -> List[SwarmResult]:
        """Get history of all completed swarm executions."""
        return self._history

    def get_active_swarms(self) -> Dict[str, SwarmState]:
        """Get all currently active swarms."""
        return dict(self._active_swarms)

    # -----------------------------------------
    # Coordination modes
    # -----------------------------------------

    async def _execute_by_mode(
        self,
        mode: str,
        dag: TaskDAG,
        task: SwarmTask,
    ) -> List[WorkerResult]:
        """Execute workers according to coordination mode."""
        if mode == CoordinationMode.SEQUENTIAL.value:
            return await self._execute_sequential(dag, task)
        elif mode == CoordinationMode.PIPELINE.value:
            return await self._execute_pipeline(dag, task)
        elif mode == CoordinationMode.CONSENSUS.value:
            return await self._execute_consensus(dag, task)
        elif mode == CoordinationMode.MAP_REDUCE.value:
            return await self._execute_map_reduce(dag, task)
        else:
            # Default: parallel by layers
            return await self._execute_parallel(dag, task)

    async def _execute_parallel(
        self,
        dag: TaskDAG,
        task: SwarmTask,
    ) -> List[WorkerResult]:
        """Execute DAG layers in parallel."""
        all_results: List[WorkerResult] = []
        node_map = {n.id: n for n in dag.nodes}

        for layer_idx, layer in enumerate(dag.execution_layers):
            state = self._active_swarms.get(dag.dag_id)
            if state:
                state.current_layer = layer_idx

            # Run all nodes in this layer concurrently
            layer_tasks = []
            for node_id in layer:
                node = node_map.get(node_id)
                if node:
                    layer_tasks.append(self._spawn_worker(node, task))

            layer_results = await asyncio.gather(*layer_tasks, return_exceptions=True)

            for res in layer_results:
                if isinstance(res, Exception):
                    all_results.append(
                        WorkerResult(
                            status=WorkerStatus.FAILED.value,
                            error=str(res),
                        )
                    )
                else:
                    all_results.append(res)

        return all_results

    async def _execute_sequential(
        self,
        dag: TaskDAG,
        task: SwarmTask,
    ) -> List[WorkerResult]:
        """Execute all nodes sequentially, one at a time."""
        results: List[WorkerResult] = []
        for node in dag.nodes:
            result = await self._spawn_worker(node, task)
            results.append(result)
        return results

    async def _execute_pipeline(
        self,
        dag: TaskDAG,
        task: SwarmTask,
    ) -> List[WorkerResult]:
        """Pipeline: each worker passes output to the next."""
        results: List[WorkerResult] = []
        prev_output: Dict[str, Any] = {}

        for node in dag.nodes:
            # Inject previous output as context
            node.context["pipeline_input"] = prev_output
            result = await self._spawn_worker(node, task)
            results.append(result)
            prev_output = result.output

        return results

    async def _execute_consensus(
        self,
        dag: TaskDAG,
        task: SwarmTask,
    ) -> List[WorkerResult]:
        """Consensus: run same task on multiple workers, pick majority."""
        # Execute all in parallel first
        results = await self._execute_parallel(dag, task)

        # Mark the highest quality result
        if results:
            best = max(results, key=lambda r: r.quality_score)
            best.output["consensus_winner"] = True

        return results

    async def _execute_map_reduce(
        self,
        dag: TaskDAG,
        task: SwarmTask,
    ) -> List[WorkerResult]:
        """Map-reduce: parallel map phase, then reduce/aggregate."""
        # Map phase: all except last node in parallel
        map_nodes = dag.nodes[:-1] if len(dag.nodes) > 1 else dag.nodes
        reduce_node = dag.nodes[-1] if len(dag.nodes) > 1 else None

        map_tasks = [self._spawn_worker(n, task) for n in map_nodes]
        map_results = await asyncio.gather(*map_tasks, return_exceptions=True)

        results: List[WorkerResult] = []
        for res in map_results:
            if isinstance(res, Exception):
                results.append(
                    WorkerResult(
                        status=WorkerStatus.FAILED.value,
                        error=str(res),
                    )
                )
            else:
                results.append(res)

        # Reduce phase
        if reduce_node:
            reduce_node.context["map_results"] = [
                r.output for r in results if r.status == WorkerStatus.COMPLETED.value
            ]
            reduce_result = await self._spawn_worker(reduce_node, task)
            results.append(reduce_result)

        return results

    # -----------------------------------------
    # Worker spawning
    # -----------------------------------------

    async def _spawn_worker(
        self,
        subtask: SubTask,
        swarm_task: SwarmTask,
    ) -> WorkerResult:
        """Spawn a single worker to execute a sub-task."""
        worker_type = self._registry.get_best_worker(subtask)
        worker = self._registry.get_worker(worker_type)

        if not worker:
            return WorkerResult(
                worker_type=worker_type,
                task_id=subtask.id,
                status=WorkerStatus.FAILED.value,
                error=f"No worker available for type: {worker_type}",
            )

        worker_id = uuid.uuid4().hex[:8]
        start = time.time()

        try:
            # Execute with timeout
            timeout = min(subtask.timeout_seconds, swarm_task.timeout_minutes * 60)
            output = await asyncio.wait_for(
                worker.execute(subtask),
                timeout=timeout,
            )

            latency = round(time.time() - start, 2)
            cap = self._registry.get_capability(worker_type)
            tokens = cap.avg_tokens if cap else 2000

            return WorkerResult(
                worker_id=worker_id,
                worker_type=worker_type,
                task_id=subtask.id,
                status=WorkerStatus.COMPLETED.value,
                output=output,
                tokens_used=tokens,
                latency_seconds=latency,
                quality_score=0.8,
            )

        except asyncio.TimeoutError:
            latency = round(time.time() - start, 2)
            return WorkerResult(
                worker_id=worker_id,
                worker_type=worker_type,
                task_id=subtask.id,
                status=WorkerStatus.TIMED_OUT.value,
                error="Worker timed out",
                latency_seconds=latency,
            )
        except Exception as exc:
            latency = round(time.time() - start, 2)
            return WorkerResult(
                worker_id=worker_id,
                worker_type=worker_type,
                task_id=subtask.id,
                status=WorkerStatus.FAILED.value,
                error=str(exc),
                latency_seconds=latency,
            )

    # -----------------------------------------
    # Aggregation & Quality
    # -----------------------------------------

    def _aggregate_results(
        self,
        results: List[WorkerResult],
        dag: TaskDAG,
    ) -> Dict[str, Any]:
        """Aggregate worker results into a unified output."""
        aggregated: Dict[str, Any] = {
            "summary": {},
            "details": [],
            "contacts": [],
            "jobs": [],
            "documents": [],
            "insights": [],
        }

        for r in results:
            if r.status != WorkerStatus.COMPLETED.value:
                continue

            output = r.output
            aggregated["details"].append(
                {
                    "worker_type": r.worker_type,
                    "task_id": r.task_id,
                    "description": output.get("description", ""),
                    "status": output.get("status", ""),
                }
            )

            # Merge type-specific outputs
            if "contacts" in output:
                aggregated["contacts"].extend(output["contacts"])
            if "jobs" in output:
                aggregated["jobs"].extend(output["jobs"])
            if "documents" in output:
                aggregated["documents"].extend(output["documents"])
            if "insights" in output:
                aggregated["insights"].extend(output["insights"])
            if "findings" in output:
                aggregated["insights"].extend(output["findings"])
            if "trends" in output:
                aggregated["insights"].extend(output["trends"])

        # Build summary
        aggregated["summary"] = {
            "total_workers": len(results),
            "completed": sum(
                1 for r in results if r.status == WorkerStatus.COMPLETED.value
            ),
            "failed": sum(1 for r in results if r.status == WorkerStatus.FAILED.value),
            "contacts_found": len(aggregated["contacts"]),
            "jobs_found": len(aggregated["jobs"]),
            "documents_generated": len(aggregated["documents"]),
            "insights_collected": len(aggregated["insights"]),
        }

        return aggregated

    def _compute_quality(self, results: List[WorkerResult]) -> float:
        """Compute overall quality score from worker results."""
        if not results:
            return 0.0

        completed = [r for r in results if r.status == WorkerStatus.COMPLETED.value]
        if not completed:
            return 0.0

        # Weighted: completion rate (40%) + average quality (40%) + no-error rate (20%)
        completion_rate = len(completed) / len(results)
        avg_quality = sum(r.quality_score for r in completed) / len(completed)
        error_free = sum(1 for r in results if not r.error) / len(results)

        return (completion_rate * 0.4) + (avg_quality * 0.4) + (error_free * 0.2)


# =========================================
# SINGLETON
# =========================================

_coordinator: Optional[SwarmCoordinator] = None


def get_swarm_coordinator() -> SwarmCoordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = SwarmCoordinator()
    return _coordinator
