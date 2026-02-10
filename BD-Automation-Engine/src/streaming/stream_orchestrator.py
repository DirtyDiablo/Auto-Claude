"""
Event-driven workflow orchestrator.

Chains events into intelligent multi-step workflows:
1. NEW_JOB_TO_OUTREACH — scrape → enrich → map → match contacts → outreach
2. CONTRACT_AWARD_RESPONSE — award → match → graph → re-score → brief → alert
3. CONTACT_CHANGE_CAMPAIGN — update → re-classify → adjust strategy
4. SURGE_DETECTION_RESPONSE — anomaly → identify → brief → blitz campaign
5. DAILY_INTELLIGENCE_DIGEST — aggregate → compile → score → summarize → deliver
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from src.streaming.event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStep(BaseModel):
    """A single step in an event workflow."""

    name: str
    processor: str  # processor name to invoke
    input_mapping: dict = Field(default_factory=dict)
    output_key: str = ""
    timeout_seconds: int = 60
    optional: bool = False  # If True, failure doesn't stop the workflow


class EventWorkflow(BaseModel):
    """Definition of an event-driven workflow."""

    workflow_id: str
    name: str
    description: str = ""
    trigger_streams: List[str]
    trigger_condition: Optional[str] = None  # serialized condition description
    steps: List[WorkflowStep]
    timeout_seconds: int = 300
    error_handler: str = "retry_3x_then_alert"


class StepExecution(BaseModel):
    """Execution state of a single workflow step."""

    step_name: str
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Optional[dict] = None
    error: Optional[str] = None


class WorkflowExecution(BaseModel):
    """Runtime state of a workflow execution."""

    execution_id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    workflow_name: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    trigger_event: Optional[dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    steps: List[StepExecution] = Field(default_factory=list)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    current_step: int = 0


# Trigger condition functions for pre-built workflows
def _is_ts_sci_priority_job(event: Event) -> bool:
    """Trigger for TS/SCI jobs at priority locations."""
    payload = event.payload
    clearance = str(payload.get("clearance", "")).upper()
    location = str(payload.get("location", "")).lower()
    priority_locations = {"langley", "hickam", "pearl harbor", "san diego", "beale", "ramstein"}
    return "TS/SCI" in clearance and any(loc in location for loc in priority_locations)


def _is_large_award(event: Event) -> bool:
    """Trigger for awards >$10M matching tracked companies."""
    payload = event.payload
    amount = payload.get("amount", 0)
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return False
    return amount > 10_000_000


def _is_tier_promotion(event: Event) -> bool:
    """Trigger for contacts promoted to Tier 1-2."""
    payload = event.payload
    tier = payload.get("tier", 99)
    previous_tier = payload.get("previous_tier")
    try:
        tier = int(tier)
    except (ValueError, TypeError):
        return False
    return tier <= 2 and (previous_tier is None or int(previous_tier) > 2)


def _is_volume_spike(event: Event) -> bool:
    """Trigger for volume spike >2x baseline."""
    payload = event.payload
    anomaly_type = payload.get("anomaly_type", "")
    multiplier = payload.get("multiplier", 1)
    try:
        multiplier = float(multiplier)
    except (ValueError, TypeError):
        return False
    return anomaly_type == "VOLUME_SPIKE" and multiplier >= 2.0


TRIGGER_CONDITIONS: Dict[str, Callable[[Event], bool]] = {
    "ts_sci_priority_job": _is_ts_sci_priority_job,
    "large_award": _is_large_award,
    "tier_promotion": _is_tier_promotion,
    "volume_spike": _is_volume_spike,
    "always": lambda e: True,
}


def _build_default_workflows() -> List[EventWorkflow]:
    """Build the 5 pre-built intelligence workflows."""
    return [
        EventWorkflow(
            workflow_id="new_job_to_outreach",
            name="New Job to Outreach",
            description="End-to-end: scrape → enrich → map → match contacts → outreach (<30s)",
            trigger_streams=["jobs:scraped"],
            trigger_condition="ts_sci_priority_job",
            steps=[
                WorkflowStep(name="enrich_job", processor="job_intel", output_key="enriched_job"),
                WorkflowStep(name="map_program", processor="job_intel", output_key="program_match"),
                WorkflowStep(name="match_contacts", processor="contact_change", output_key="matched_contacts"),
                WorkflowStep(name="score_priority", processor="job_intel", output_key="priority_score"),
                WorkflowStep(name="generate_outreach", processor="campaign_event", output_key="outreach_draft"),
                WorkflowStep(name="queue_campaign", processor="campaign_event", output_key="campaign_queued"),
            ],
            timeout_seconds=120,
        ),
        EventWorkflow(
            workflow_id="contract_award_response",
            name="Contract Award Response",
            description="Award >$10M → match → graph → re-score → brief → alert",
            trigger_streams=["contracts:awards"],
            trigger_condition="large_award",
            steps=[
                WorkflowStep(name="match_program", processor="contract_intel", output_key="program_match"),
                WorkflowStep(name="update_graph", processor="contract_intel", output_key="graph_updated"),
                WorkflowStep(name="rescore_contacts", processor="contact_change", output_key="rescored"),
                WorkflowStep(name="generate_briefing", processor="contract_intel", output_key="briefing"),
                WorkflowStep(name="alert_bd_team", processor="anomaly", output_key="alert_sent"),
            ],
            timeout_seconds=180,
        ),
        EventWorkflow(
            workflow_id="contact_change_campaign",
            name="Contact Change Campaign",
            description="Contact promoted to Tier 1-2 → re-classify → adjust strategy",
            trigger_streams=["contacts:updated"],
            trigger_condition="tier_promotion",
            steps=[
                WorkflowStep(name="reclassify_tier", processor="contact_change", output_key="new_tier"),
                WorkflowStep(name="update_strategy", processor="campaign_event", output_key="strategy_update"),
                WorkflowStep(name="adjust_cadence", processor="campaign_event", output_key="cadence_adjusted"),
            ],
            timeout_seconds=90,
        ),
        EventWorkflow(
            workflow_id="surge_detection_response",
            name="Surge Detection Response",
            description="Volume spike >2x → identify program → brief → blitz campaign",
            trigger_streams=["intel:anomalies"],
            trigger_condition="volume_spike",
            steps=[
                WorkflowStep(name="identify_program", processor="anomaly", output_key="program_identified"),
                WorkflowStep(name="find_contacts", processor="contact_change", output_key="contacts_found"),
                WorkflowStep(name="generate_surge_brief", processor="anomaly", output_key="surge_brief"),
                WorkflowStep(name="create_blitz_campaign", processor="campaign_event", output_key="blitz_created"),
            ],
            timeout_seconds=180,
        ),
        EventWorkflow(
            workflow_id="daily_intelligence_digest",
            name="Daily Intelligence Digest",
            description="Scheduled 6am → aggregate → compile → score → summarize → deliver",
            trigger_streams=["system:health"],
            trigger_condition="always",
            steps=[
                WorkflowStep(name="aggregate_events", processor="system_health", output_key="aggregated"),
                WorkflowStep(name="compile_digest", processor="system_health", output_key="digest"),
                WorkflowStep(name="score_opportunities", processor="job_intel", output_key="scored"),
                WorkflowStep(name="generate_summary", processor="system_health", output_key="summary"),
                WorkflowStep(name="deliver_digest", processor="campaign_event", output_key="delivered"),
            ],
            timeout_seconds=300,
        ),
    ]


class StreamOrchestrator:
    """Chains events into intelligent workflows."""

    def __init__(self, event_bus: EventBus, processors: Optional[Dict[str, Any]] = None):
        self.event_bus = event_bus
        self.processors = processors or {}
        self.workflows: Dict[str, EventWorkflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self._running = False
        self._listener_tasks: List[asyncio.Task] = []

        # Register default workflows
        for wf in _build_default_workflows():
            self.workflows[wf.workflow_id] = wf

    async def start(self) -> None:
        """Start listening for workflow triggers."""
        self._running = True

        # Group workflows by trigger stream
        stream_workflows: Dict[str, List[EventWorkflow]] = {}
        for wf in self.workflows.values():
            for stream in wf.trigger_streams:
                stream_workflows.setdefault(stream, []).append(wf)

        # Create a listener for each unique trigger stream
        all_streams = list(stream_workflows.keys())
        if all_streams:
            task = asyncio.create_task(
                self.event_bus.subscribe(
                    streams=all_streams,
                    handler=self._on_event,
                    group="orchestrator",
                    consumer="orchestrator-main",
                )
            )
            self._listener_tasks.append(task)

        logger.info(
            "StreamOrchestrator started",
            extra={"workflows": len(self.workflows), "streams": len(all_streams)},
        )

    async def stop(self) -> None:
        """Stop the orchestrator."""
        self._running = False
        for task in self._listener_tasks:
            task.cancel()
        self._listener_tasks.clear()
        logger.info("StreamOrchestrator stopped")

    async def _on_event(self, event: Event) -> None:
        """Handle incoming events, check if any workflow should trigger."""
        for wf in self.workflows.values():
            # Check if the event's stream matches
            event_stream_match = False
            for stream in wf.trigger_streams:
                prefix = stream.split(":")[0]
                if prefix in event.event_type or prefix in event.source:
                    event_stream_match = True
                    break

            if not event_stream_match:
                continue

            # Check trigger condition
            if wf.trigger_condition:
                condition_fn = TRIGGER_CONDITIONS.get(wf.trigger_condition)
                if condition_fn and not condition_fn(event):
                    continue

            # Trigger the workflow
            await self.trigger_workflow(wf.workflow_id, event)

    async def register_workflow(self, workflow: EventWorkflow) -> str:
        """Register a new workflow. Returns workflow_id."""
        self.workflows[workflow.workflow_id] = workflow
        logger.info("Workflow registered", extra={"id": workflow.workflow_id, "name": workflow.name})
        return workflow.workflow_id

    async def trigger_workflow(
        self, workflow_id: str, trigger_event: Event
    ) -> str:
        """Start a workflow execution. Returns execution_id."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        execution = WorkflowExecution(
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            status=WorkflowStatus.RUNNING,
            trigger_event=trigger_event.model_dump(),
            started_at=datetime.now(timezone.utc),
            steps=[
                StepExecution(step_name=step.name) for step in workflow.steps
            ],
        )
        self.executions[execution.execution_id] = execution

        logger.info(
            "Workflow triggered",
            extra={
                "workflow": workflow_id,
                "execution_id": execution.execution_id,
                "trigger": trigger_event.event_type,
            },
        )

        # Execute steps sequentially
        asyncio.create_task(self._execute_workflow(workflow, execution))
        return execution.execution_id

    async def _execute_workflow(
        self, workflow: EventWorkflow, execution: WorkflowExecution
    ) -> None:
        """Execute workflow steps sequentially with timeout."""
        try:
            async with asyncio.timeout(workflow.timeout_seconds):
                for i, step in enumerate(workflow.steps):
                    if not self._running:
                        break

                    execution.current_step = i
                    step_exec = execution.steps[i]
                    step_exec.status = StepStatus.RUNNING
                    step_exec.started_at = datetime.now(timezone.utc)

                    try:
                        # Execute the step
                        result = await self._execute_step(step, execution)
                        step_exec.status = StepStatus.COMPLETED
                        step_exec.completed_at = datetime.now(timezone.utc)
                        step_exec.output = result

                        if step.output_key:
                            execution.outputs[step.output_key] = result

                    except Exception as e:
                        step_exec.status = StepStatus.FAILED
                        step_exec.completed_at = datetime.now(timezone.utc)
                        step_exec.error = str(e)

                        if not step.optional:
                            execution.status = WorkflowStatus.FAILED
                            execution.error = f"Step '{step.name}' failed: {e}"
                            execution.completed_at = datetime.now(timezone.utc)

                            # Publish failure event
                            await self._publish_workflow_event(
                                execution, "workflow.failed"
                            )
                            return

                execution.status = WorkflowStatus.COMPLETED
                execution.completed_at = datetime.now(timezone.utc)
                await self._publish_workflow_event(execution, "workflow.completed")

        except asyncio.TimeoutError:
            execution.status = WorkflowStatus.TIMED_OUT
            execution.error = f"Workflow timed out after {workflow.timeout_seconds}s"
            execution.completed_at = datetime.now(timezone.utc)
            await self._publish_workflow_event(execution, "workflow.timed_out")

    async def _execute_step(
        self, step: WorkflowStep, execution: WorkflowExecution
    ) -> dict:
        """Execute a single workflow step."""
        # Build step input from previous outputs and trigger event
        step_input = {}
        if execution.trigger_event:
            step_input["trigger"] = execution.trigger_event

        for key, source_key in step.input_mapping.items():
            if source_key in execution.outputs:
                step_input[key] = execution.outputs[source_key]

        # Publish step event
        step_event = Event(
            event_type=f"workflow.step.{step.name}",
            source="orchestrator",
            payload={
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id,
                "step": step.name,
                "processor": step.processor,
                "input": step_input,
            },
            metadata={
                "correlation_id": execution.execution_id,
            },
        )
        await self.event_bus.publish("system:health", step_event)

        return {
            "step": step.name,
            "processor": step.processor,
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _publish_workflow_event(
        self, execution: WorkflowExecution, event_type: str
    ) -> None:
        """Publish a workflow lifecycle event."""
        event = Event(
            event_type=event_type,
            source="orchestrator",
            payload={
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id,
                "workflow_name": execution.workflow_name,
                "status": execution.status,
                "steps_completed": sum(
                    1 for s in execution.steps if s.status == StepStatus.COMPLETED
                ),
                "total_steps": len(execution.steps),
                "error": execution.error,
            },
            metadata={"correlation_id": execution.execution_id},
            priority="high" if execution.status == WorkflowStatus.FAILED else "medium",
        )
        await self.event_bus.publish("system:health", event)

    async def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get current status of a workflow execution."""
        return self.executions.get(execution_id)

    async def list_active_workflows(self) -> List[WorkflowExecution]:
        """List all active (running) workflow executions."""
        return [
            ex
            for ex in self.executions.values()
            if ex.status == WorkflowStatus.RUNNING
        ]

    async def list_all_executions(
        self, limit: int = 50
    ) -> List[WorkflowExecution]:
        """List recent workflow executions."""
        execs = sorted(
            self.executions.values(),
            key=lambda e: e.started_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return execs[:limit]

    def get_registered_workflows(self) -> List[dict]:
        """List all registered workflow definitions."""
        return [
            {
                "workflow_id": wf.workflow_id,
                "name": wf.name,
                "description": wf.description,
                "trigger_streams": wf.trigger_streams,
                "trigger_condition": wf.trigger_condition,
                "steps": len(wf.steps),
                "timeout_seconds": wf.timeout_seconds,
            }
            for wf in self.workflows.values()
        ]
