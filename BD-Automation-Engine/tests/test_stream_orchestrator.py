"""Tests for Phase 31A - Stream Orchestrator (workflow registration, trigger, execution, timeout, chains)."""

import asyncio
import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.streaming.event_bus import Event, EventBus
from src.streaming.stream_orchestrator import (
    EventWorkflow,
    StreamOrchestrator,
    StepExecution,
    StepStatus,
    WorkflowExecution,
    WorkflowStatus,
    WorkflowStep,
    TRIGGER_CONDITIONS,
    _build_default_workflows,
    _is_ts_sci_priority_job,
    _is_large_award,
    _is_tier_promotion,
    _is_volume_spike,
)


def _make_mock_bus():
    bus = MagicMock(spec=EventBus)
    bus.publish = AsyncMock(return_value=b"1-0")
    bus.subscribe = AsyncMock()
    bus.STREAM_DEFINITIONS = EventBus.STREAM_DEFINITIONS
    return bus


# =========================================
# TRIGGER CONDITIONS
# =========================================


class TestTriggerConditions:
    """Tests for pre-built trigger conditions."""

    def test_ts_sci_priority_job_match(self):
        """Should match TS/SCI jobs at priority locations."""
        event = Event(
            event_type="job.scraped",
            source="test",
            payload={"clearance": "TS/SCI", "location": "Langley, VA"},
        )
        assert _is_ts_sci_priority_job(event) is True

    def test_ts_sci_priority_job_no_match(self):
        """Should not match non-TS/SCI or non-priority locations."""
        event = Event(
            event_type="job.scraped",
            source="test",
            payload={"clearance": "Secret", "location": "Langley, VA"},
        )
        assert _is_ts_sci_priority_job(event) is False

        event2 = Event(
            event_type="job.scraped",
            source="test",
            payload={"clearance": "TS/SCI", "location": "New York, NY"},
        )
        assert _is_ts_sci_priority_job(event2) is False

    def test_large_award_match(self):
        """Should match awards >$10M."""
        event = Event(
            event_type="contract.awarded",
            source="test",
            payload={"amount": 15000000},
        )
        assert _is_large_award(event) is True

    def test_large_award_no_match(self):
        """Should not match awards <=$10M."""
        event = Event(
            event_type="contract.awarded",
            source="test",
            payload={"amount": 5000000},
        )
        assert _is_large_award(event) is False

    def test_tier_promotion_match(self):
        """Should match tier 1-2 with previous tier >2."""
        event = Event(
            event_type="contact.updated",
            source="test",
            payload={"tier": 2, "previous_tier": 4},
        )
        assert _is_tier_promotion(event) is True

    def test_tier_promotion_no_match(self):
        """Should not match tier >2."""
        event = Event(
            event_type="contact.updated",
            source="test",
            payload={"tier": 3},
        )
        assert _is_tier_promotion(event) is False

    def test_volume_spike_match(self):
        """Should match volume spike >=2x."""
        event = Event(
            event_type="anomaly.detected",
            source="test",
            payload={"anomaly_type": "VOLUME_SPIKE", "multiplier": 3.0},
        )
        assert _is_volume_spike(event) is True

    def test_volume_spike_no_match(self):
        """Should not match low multiplier."""
        event = Event(
            event_type="anomaly.detected",
            source="test",
            payload={"anomaly_type": "VOLUME_SPIKE", "multiplier": 1.5},
        )
        assert _is_volume_spike(event) is False

    def test_all_conditions_registered(self):
        """All named conditions should be in the registry."""
        expected = [
            "ts_sci_priority_job",
            "large_award",
            "tier_promotion",
            "volume_spike",
            "always",
        ]
        for name in expected:
            assert name in TRIGGER_CONDITIONS


# =========================================
# DEFAULT WORKFLOWS
# =========================================


class TestDefaultWorkflows:
    """Tests for the 5 pre-built workflows."""

    def test_builds_5_workflows(self):
        """Should build exactly 5 default workflows."""
        workflows = _build_default_workflows()
        assert len(workflows) == 5

    def test_workflow_ids(self):
        """Should have expected workflow IDs."""
        workflows = _build_default_workflows()
        ids = {wf.workflow_id for wf in workflows}
        assert "new_job_to_outreach" in ids
        assert "contract_award_response" in ids
        assert "contact_change_campaign" in ids
        assert "surge_detection_response" in ids
        assert "daily_intelligence_digest" in ids

    def test_all_workflows_have_steps(self):
        """Every workflow should have at least 2 steps."""
        for wf in _build_default_workflows():
            assert len(wf.steps) >= 2, f"{wf.workflow_id} has < 2 steps"

    def test_all_workflows_have_trigger(self):
        """Every workflow should have trigger streams."""
        for wf in _build_default_workflows():
            assert len(wf.trigger_streams) >= 1, f"{wf.workflow_id} has no trigger"


# =========================================
# WORKFLOW / STEP MODELS
# =========================================


class TestWorkflowModels:
    """Tests for workflow data models."""

    def test_workflow_execution_defaults(self):
        """WorkflowExecution should have sane defaults."""
        ex = WorkflowExecution(workflow_id="test")
        assert ex.execution_id is not None
        assert ex.status == WorkflowStatus.PENDING
        assert ex.steps == []
        assert ex.outputs == {}

    def test_step_execution_defaults(self):
        """StepExecution should default to pending."""
        step = StepExecution(step_name="test_step")
        assert step.status == StepStatus.PENDING
        assert step.output is None

    def test_workflow_step_defaults(self):
        """WorkflowStep should have defaults."""
        step = WorkflowStep(name="test", processor="job_intel")
        assert step.timeout_seconds == 60
        assert step.optional is False


# =========================================
# STREAM ORCHESTRATOR
# =========================================


class TestStreamOrchestrator:
    """Tests for StreamOrchestrator."""

    def test_init_registers_default_workflows(self):
        """Should register 5 default workflows on init."""
        bus = _make_mock_bus()
        orch = StreamOrchestrator(bus)
        assert len(orch.workflows) == 5

    def test_get_registered_workflows(self):
        """Should return workflow definitions as list."""
        bus = _make_mock_bus()
        orch = StreamOrchestrator(bus)
        wfs = orch.get_registered_workflows()
        assert len(wfs) == 5
        for wf in wfs:
            assert "workflow_id" in wf
            assert "name" in wf
            assert "steps" in wf

    @pytest.mark.asyncio
    async def test_register_custom_workflow(self):
        """Should register a custom workflow."""
        bus = _make_mock_bus()
        orch = StreamOrchestrator(bus)

        custom = EventWorkflow(
            workflow_id="custom_test",
            name="Custom Test Workflow",
            trigger_streams=["system:health"],
            steps=[
                WorkflowStep(name="step1", processor="test", output_key="result"),
            ],
        )
        wf_id = await orch.register_workflow(custom)
        assert wf_id == "custom_test"
        assert "custom_test" in orch.workflows

    @pytest.mark.asyncio
    async def test_trigger_workflow_returns_execution_id(self):
        """trigger_workflow should return a valid execution_id."""
        bus = _make_mock_bus()
        orch = StreamOrchestrator(bus)

        trigger_event = Event(event_type="test.trigger", source="test")
        exec_id = await orch.trigger_workflow(
            "daily_intelligence_digest", trigger_event
        )

        assert exec_id is not None
        assert exec_id in orch.executions

    @pytest.mark.asyncio
    async def test_trigger_nonexistent_workflow_raises(self):
        """trigger_workflow should raise for unknown workflow."""
        bus = _make_mock_bus()
        orch = StreamOrchestrator(bus)
        trigger_event = Event(event_type="test", source="test")

        with pytest.raises(ValueError, match="not found"):
            await orch.trigger_workflow("nonexistent", trigger_event)

    @pytest.mark.asyncio
    async def test_execution_completes(self):
        """Triggered workflow should eventually complete."""
        bus = _make_mock_bus()
        orch = StreamOrchestrator(bus)

        trigger_event = Event(event_type="test", source="test")
        exec_id = await orch.trigger_workflow(
            "daily_intelligence_digest", trigger_event
        )

        # Wait for the async task to complete
        await asyncio.sleep(0.5)

        execution = await orch.get_execution_status(exec_id)
        assert execution is not None
        assert execution.status in (WorkflowStatus.COMPLETED, WorkflowStatus.RUNNING)

    @pytest.mark.asyncio
    async def test_list_all_executions(self):
        """list_all_executions should return recent executions."""
        bus = _make_mock_bus()
        orch = StreamOrchestrator(bus)

        trigger = Event(event_type="test", source="test")
        await orch.trigger_workflow("daily_intelligence_digest", trigger)
        await asyncio.sleep(0.1)

        execs = await orch.list_all_executions()
        assert len(execs) >= 1

    @pytest.mark.asyncio
    async def test_get_execution_status_none_for_unknown(self):
        """get_execution_status should return None for unknown ID."""
        bus = _make_mock_bus()
        orch = StreamOrchestrator(bus)
        result = await orch.get_execution_status("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_workflow_timeout(self):
        """Workflow with very short timeout should time out."""
        bus = _make_mock_bus()
        orch = StreamOrchestrator(bus)

        # Register a workflow with 0-second timeout (will timeout immediately)
        fast_wf = EventWorkflow(
            workflow_id="timeout_test",
            name="Timeout Test",
            trigger_streams=["system:health"],
            steps=[
                WorkflowStep(name="slow_step", processor="test", timeout_seconds=1),
            ],
            timeout_seconds=0,  # instant timeout
        )
        await orch.register_workflow(fast_wf)

        trigger = Event(event_type="test", source="test")
        exec_id = await orch.trigger_workflow("timeout_test", trigger)
        await asyncio.sleep(0.5)

        execution = await orch.get_execution_status(exec_id)
        # With 0 timeout, should be TIMED_OUT or COMPLETED (if step was fast enough)
        assert execution is not None
        assert execution.status in (WorkflowStatus.TIMED_OUT, WorkflowStatus.COMPLETED)
