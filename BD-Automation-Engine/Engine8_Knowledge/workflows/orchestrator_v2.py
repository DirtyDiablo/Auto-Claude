"""
Phase 23A — Workflow Orchestrator v2

Production workflow orchestrator managing lifecycle of all production workflows.
Uses ProductionGraphBuilder and CheckpointStore for workflow management,
with scheduling, streaming, and monitoring capabilities.
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

import structlog

from Engine8_Knowledge.workflows.checkpoint_store import CheckpointStore, get_checkpoint_store
from Engine8_Knowledge.workflows.graph_builder import (
    CompiledProductionGraph, ProductionGraphBuilder, WorkflowDefinition,
    WorkflowInfo, get_graph_builder,
)
from Engine8_Knowledge.workflows.human_loop import HumanInTheLoopManager, get_hitl_manager

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class WorkflowExecution:
    thread_id: str
    workflow_name: str
    status: str  # pending, running, interrupted, completed, failed, cancelled
    started_at: str
    completed_at: Optional[str] = None
    current_node: Optional[str] = None
    step_count: int = 0
    input_state: Dict[str, Any] = field(default_factory=dict)
    output_state: Optional[Dict[str, Any]] = None
    errors: List[dict] = field(default_factory=list)
    pending_approvals: List[str] = field(default_factory=list)


@dataclass
class ScheduledWorkflow:
    schedule_id: str
    workflow_name: str
    cron_expression: str
    default_input: Dict[str, Any]
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0


@dataclass
class StreamEvent:
    event_type: str  # node_start, node_end, state_update, interrupt, error, completion
    thread_id: str
    timestamp: str
    data: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# WorkflowOrchestratorV2
# ---------------------------------------------------------------------------

class WorkflowOrchestratorV2:
    """Manages lifecycle of all production workflows."""

    def __init__(self,
                 checkpoint_store: Optional[CheckpointStore] = None,
                 hitl_manager: Optional[HumanInTheLoopManager] = None,
                 graph_builder: Optional[ProductionGraphBuilder] = None):
        self.checkpoint_store = checkpoint_store or get_checkpoint_store()
        self.hitl_manager = hitl_manager or get_hitl_manager()
        self.graph_builder = graph_builder or get_graph_builder()

        self._workflows: Dict[str, CompiledProductionGraph] = {}
        self._definitions: Dict[str, WorkflowDefinition] = {}
        self._executions: Dict[str, WorkflowExecution] = {}
        self._schedules: Dict[str, ScheduledWorkflow] = {}
        self._event_listeners: Dict[str, List[asyncio.Queue]] = {}

        # Load schedules
        self._schedules_path = Path("data/workflow_schedules.json")
        self._load_schedules()

        logger.info("orchestrator_v2.init")

    def _load_schedules(self):
        """Load saved schedules from disk."""
        if self._schedules_path.exists():
            try:
                data = json.loads(self._schedules_path.read_text())
                for sched_data in data.get("schedules", []):
                    sched = ScheduledWorkflow(**sched_data)
                    self._schedules[sched.schedule_id] = sched
            except Exception as e:
                logger.warning("orchestrator_v2.load_schedules_error", error=str(e))

    def _save_schedules(self):
        """Persist schedules to disk."""
        self._schedules_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "schedules": [asdict(s) for s in self._schedules.values()],
            "saved_at": datetime.utcnow().isoformat(),
        }
        self._schedules_path.write_text(json.dumps(data, indent=2, default=str))

    # ------------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------------

    def register_workflow(self, workflow_def: WorkflowDefinition) -> None:
        """Register and compile a workflow definition."""
        compiled = self.graph_builder.build(workflow_def)
        self._workflows[workflow_def.name] = compiled
        self._definitions[workflow_def.name] = workflow_def
        logger.info("orchestrator_v2.registered", workflow=workflow_def.name,
                     nodes=len(workflow_def.nodes))

    def list_workflows(self) -> List[WorkflowInfo]:
        """List all registered workflows."""
        return self.graph_builder.list_workflows()

    def get_workflow(self, name: str) -> Optional[CompiledProductionGraph]:
        """Get a registered compiled graph."""
        return self._workflows.get(name)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def start_workflow(
        self,
        workflow_name: str,
        input_state: dict,
        thread_id: Optional[str] = None,
    ) -> WorkflowExecution:
        """Start a workflow execution."""
        graph = self._workflows.get(workflow_name)
        if not graph:
            raise ValueError(f"Workflow '{workflow_name}' not registered. Available: {list(self._workflows.keys())}")

        tid = thread_id or f"wf_{uuid.uuid4().hex[:10]}"
        now = datetime.utcnow().isoformat()

        execution = WorkflowExecution(
            thread_id=tid,
            workflow_name=workflow_name,
            status="running",
            started_at=now,
            input_state=input_state,
        )
        self._executions[tid] = execution

        # Emit start event
        await self._emit_event(StreamEvent(
            event_type="node_start",
            thread_id=tid,
            timestamp=now,
            data={"workflow": workflow_name, "input_keys": list(input_state.keys())}
        ))

        # Execute the workflow
        try:
            result = await graph.invoke(input_state, thread_id=tid)

            # Check if interrupted
            if result.get("_interrupted_at"):
                execution.status = "interrupted"
                execution.current_node = result["_interrupted_at"]

                # Create approval request
                wf_def = self._definitions.get(workflow_name)
                if wf_def:
                    request = await self.hitl_manager.create_approval_request(
                        thread_id=tid,
                        workflow_name=workflow_name,
                        node_name=result["_interrupted_at"],
                        state_snapshot=result,
                        description=f"Workflow '{workflow_name}' requires approval at node '{result['_interrupted_at']}'",
                        urgency="high" if any(
                            r.get("severity") == "critical" for r in result.get("risks", [])
                        ) else "normal",
                    )
                    execution.pending_approvals.append(request.request_id)

                await self._emit_event(StreamEvent(
                    event_type="interrupt",
                    thread_id=tid,
                    timestamp=datetime.utcnow().isoformat(),
                    data={"node": result["_interrupted_at"], "reason": "human_approval_required"}
                ))
            elif result.get("errors"):
                execution.status = "failed" if not result.get("_completed") else "completed"
                execution.errors = result.get("errors", [])
            else:
                execution.status = "completed"

            execution.output_state = result
            execution.completed_at = datetime.utcnow().isoformat()
            execution.step_count = len(result.get("step_timings", {}))

        except Exception as e:
            execution.status = "failed"
            execution.errors = [{"error": str(e)}]
            execution.completed_at = datetime.utcnow().isoformat()
            logger.error("orchestrator_v2.execution_error",
                         workflow=workflow_name, error=str(e))

        # Emit completion event
        await self._emit_event(StreamEvent(
            event_type="completion",
            thread_id=tid,
            timestamp=datetime.utcnow().isoformat(),
            data={"status": execution.status, "step_count": execution.step_count}
        ))

        return execution

    async def resume_workflow(self, thread_id: str,
                              updated_state: Optional[dict] = None) -> WorkflowExecution:
        """Resume an interrupted workflow."""
        execution = self._executions.get(thread_id)
        if not execution:
            raise ValueError(f"Execution {thread_id} not found")

        graph = self._workflows.get(execution.workflow_name)
        if not graph:
            raise ValueError(f"Workflow '{execution.workflow_name}' not registered")

        execution.status = "running"

        try:
            result = await graph.resume(thread_id, updated_state)
            execution.output_state = result
            execution.status = "completed" if result.get("_completed") else "interrupted"
            execution.completed_at = datetime.utcnow().isoformat()
        except Exception as e:
            execution.status = "failed"
            execution.errors.append({"error": str(e)})
            execution.completed_at = datetime.utcnow().isoformat()

        return execution

    async def cancel_workflow(self, thread_id: str, reason: str = "") -> bool:
        """Cancel a running workflow."""
        execution = self._executions.get(thread_id)
        if not execution:
            return False

        graph = self._workflows.get(execution.workflow_name)
        if graph:
            await graph.cancel(thread_id)

        execution.status = "cancelled"
        execution.completed_at = datetime.utcnow().isoformat()
        if reason:
            execution.errors.append({"cancellation_reason": reason})

        await self._emit_event(StreamEvent(
            event_type="completion",
            thread_id=thread_id,
            timestamp=datetime.utcnow().isoformat(),
            data={"status": "cancelled", "reason": reason}
        ))

        logger.info("orchestrator_v2.cancelled", thread_id=thread_id, reason=reason)
        return True

    # ------------------------------------------------------------------
    # Monitoring
    # ------------------------------------------------------------------

    async def get_active_workflows(self) -> List[WorkflowExecution]:
        """List all active (running/interrupted) workflow executions."""
        return [
            e for e in self._executions.values()
            if e.status in ("running", "interrupted", "pending")
        ]

    async def get_workflow_history(self, workflow_name: Optional[str] = None,
                                   limit: int = 20) -> List[WorkflowExecution]:
        """Get workflow execution history."""
        results = list(self._executions.values())
        if workflow_name:
            results = [e for e in results if e.workflow_name == workflow_name]
        results.sort(key=lambda e: e.started_at, reverse=True)
        return results[:limit]

    async def get_execution_status(self, thread_id: str) -> Optional[WorkflowExecution]:
        """Get execution status for a specific thread."""
        return self._executions.get(thread_id)

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------

    async def schedule_workflow(
        self,
        workflow_name: str,
        cron_expression: str,
        default_input: dict,
        enabled: bool = True,
    ) -> ScheduledWorkflow:
        """Create a workflow schedule."""
        if workflow_name not in self._workflows:
            raise ValueError(f"Workflow '{workflow_name}' not registered")

        schedule_id = f"sched_{uuid.uuid4().hex[:8]}"

        schedule = ScheduledWorkflow(
            schedule_id=schedule_id,
            workflow_name=workflow_name,
            cron_expression=cron_expression,
            default_input=default_input,
            enabled=enabled,
        )

        self._schedules[schedule_id] = schedule
        self._save_schedules()

        logger.info("orchestrator_v2.scheduled",
                     schedule_id=schedule_id, workflow=workflow_name,
                     cron=cron_expression)
        return schedule

    async def list_schedules(self) -> List[ScheduledWorkflow]:
        """List all workflow schedules."""
        return list(self._schedules.values())

    async def toggle_schedule(self, schedule_id: str, enabled: bool) -> bool:
        """Toggle a schedule on/off."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return False

        schedule.enabled = enabled
        self._save_schedules()
        logger.info("orchestrator_v2.schedule_toggled",
                     schedule_id=schedule_id, enabled=enabled)
        return True

    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a workflow schedule."""
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            self._save_schedules()
            return True
        return False

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    async def stream_workflow(self, thread_id: str) -> AsyncGenerator[StreamEvent, None]:
        """Stream real-time events from a running workflow."""
        queue: asyncio.Queue = asyncio.Queue()
        self._event_listeners.setdefault(thread_id, []).append(queue)

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event
                    if event.event_type == "completion":
                        break
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield StreamEvent(
                        event_type="keepalive",
                        thread_id=thread_id,
                        timestamp=datetime.utcnow().isoformat(),
                    )
        finally:
            listeners = self._event_listeners.get(thread_id, [])
            if queue in listeners:
                listeners.remove(queue)

    async def _emit_event(self, event: StreamEvent):
        """Emit an event to all listeners for a thread."""
        listeners = self._event_listeners.get(event.thread_id, [])
        for queue in listeners:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    async def get_stats(self) -> dict:
        """Overall workflow execution stats."""
        executions = list(self._executions.values())

        by_status = {}
        by_workflow = {}
        durations = []

        for ex in executions:
            by_status[ex.status] = by_status.get(ex.status, 0) + 1
            by_workflow[ex.workflow_name] = by_workflow.get(ex.workflow_name, 0) + 1

            if ex.completed_at and ex.started_at:
                try:
                    started = datetime.fromisoformat(ex.started_at)
                    completed = datetime.fromisoformat(ex.completed_at)
                    durations.append((completed - started).total_seconds())
                except (ValueError, TypeError):
                    pass

        checkpoint_stats = await self.checkpoint_store.get_stats()
        approval_stats = await self.hitl_manager.get_approval_stats()

        return {
            "total_executions": len(executions),
            "by_status": by_status,
            "by_workflow": by_workflow,
            "avg_duration_seconds": round(sum(durations) / len(durations), 1) if durations else 0,
            "registered_workflows": len(self._workflows),
            "active_schedules": sum(1 for s in self._schedules.values() if s.enabled),
            "checkpoint_stats": checkpoint_stats,
            "approval_stats": approval_stats,
        }


# ---------------------------------------------------------------------------
# Singleton + auto-registration
# ---------------------------------------------------------------------------

_orchestrator: Optional[WorkflowOrchestratorV2] = None


def get_workflow_orchestrator() -> WorkflowOrchestratorV2:
    """Get or create the singleton WorkflowOrchestratorV2."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = WorkflowOrchestratorV2()
        _register_production_workflows(_orchestrator)
    return _orchestrator


def _register_production_workflows(orch: WorkflowOrchestratorV2):
    """Auto-register all production workflow definitions."""
    try:
        from Engine8_Knowledge.workflows.production.contact_enrichment import get_contact_enrichment_definition
        orch.register_workflow(get_contact_enrichment_definition())
    except ImportError as e:
        logger.warning("orchestrator_v2.skip_contact_enrichment", error=str(e))

    try:
        from Engine8_Knowledge.workflows.production.competitive_intel import get_competitive_intel_definition
        orch.register_workflow(get_competitive_intel_definition())
    except ImportError as e:
        logger.warning("orchestrator_v2.skip_competitive_intel", error=str(e))

    try:
        from Engine8_Knowledge.workflows.production.morning_briefing import get_morning_briefing_definition
        orch.register_workflow(get_morning_briefing_definition())
    except ImportError as e:
        logger.warning("orchestrator_v2.skip_morning_briefing", error=str(e))

    try:
        from Engine8_Knowledge.workflows.production.pipeline_manager import get_pipeline_manager_definition
        orch.register_workflow(get_pipeline_manager_definition())
    except ImportError as e:
        logger.warning("orchestrator_v2.skip_pipeline_manager", error=str(e))

    logger.info("orchestrator_v2.workflows_registered",
                count=len(orch._workflows))
