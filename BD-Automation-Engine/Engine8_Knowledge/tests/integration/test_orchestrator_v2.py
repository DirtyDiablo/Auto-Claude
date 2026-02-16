"""
Phase 23A — WorkflowOrchestratorV2 Tests

Tests workflow registration, execution, resume, cancel, scheduling,
monitoring, and stats.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.workflows.checkpoint_store import CheckpointStore, DictMetaStore
from Engine8_Knowledge.workflows.graph_builder import (
    ProductionGraphBuilder,
    WorkflowDefinition,
    NodeSpec,
    EdgeSpec,
)
from Engine8_Knowledge.workflows.human_loop import HumanInTheLoopManager
from Engine8_Knowledge.workflows.orchestrator_v2 import (
    WorkflowOrchestratorV2,
    WorkflowExecution,
    ScheduledWorkflow,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def simple_node_a(state):
    return {**state, "step_a": True}


async def simple_node_b(state):
    return {**state, "step_b": True}


async def interrupt_node(state):
    return {**state, "reviewed": True}


def make_test_definition():
    return WorkflowDefinition(
        name="test_workflow",
        description="Test workflow",
        state_schema={
            "step_a": False,
            "step_b": False,
            "errors": [],
            "step_timings": {},
        },
        nodes={
            "node_a": NodeSpec(
                name="node_a", function=simple_node_a, description="Step A"
            ),
            "node_b": NodeSpec(
                name="node_b", function=simple_node_b, description="Step B"
            ),
        },
        edges=[
            EdgeSpec(source="node_a", target="node_b"),
            EdgeSpec(source="node_b", target="__end__"),
        ],
        entry_point="node_a",
    )


def make_interrupt_definition():
    return WorkflowDefinition(
        name="interrupt_workflow",
        description="Workflow with interrupt",
        state_schema={"reviewed": False, "errors": [], "step_timings": {}},
        nodes={
            "review": NodeSpec(
                name="review", function=interrupt_node, description="Review"
            ),
            "done": NodeSpec(name="done", function=simple_node_b, description="Done"),
        },
        edges=[
            EdgeSpec(source="review", target="done"),
            EdgeSpec(source="done", target="__end__"),
        ],
        entry_point="review",
        interrupt_nodes=["review"],
    )


@pytest.fixture
def orchestrator(tmp_path):
    store = CheckpointStore(db_path=str(tmp_path / "test.db"))
    store._db = DictMetaStore()
    hitl = HumanInTheLoopManager(
        checkpoint_store=store,
        storage_path=str(tmp_path / "approvals"),
    )
    builder = ProductionGraphBuilder(checkpoint_store=store)
    orch = WorkflowOrchestratorV2(
        checkpoint_store=store,
        hitl_manager=hitl,
        graph_builder=builder,
    )
    orch._schedules_path = tmp_path / "schedules.json"
    return orch


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_init(orchestrator):
    assert orchestrator is not None


def test_register_workflow(orchestrator):
    orchestrator.register_workflow(make_test_definition())
    assert orchestrator.get_workflow("test_workflow") is not None


def test_register_multiple_workflows(orchestrator):
    orchestrator.register_workflow(make_test_definition())
    orchestrator.register_workflow(make_interrupt_definition())
    assert len(orchestrator.list_workflows()) == 2


def test_list_workflows(orchestrator):
    orchestrator.register_workflow(make_test_definition())
    workflows = orchestrator.list_workflows()
    assert len(workflows) >= 1
    assert workflows[0].name == "test_workflow"


def test_get_workflow_not_found(orchestrator):
    assert orchestrator.get_workflow("nonexistent") is None


@pytest.mark.asyncio
async def test_start_workflow(orchestrator):
    orchestrator.register_workflow(make_test_definition())
    execution = await orchestrator.start_workflow("test_workflow", {"input": "test"})
    assert isinstance(execution, WorkflowExecution)
    assert execution.workflow_name == "test_workflow"
    assert execution.status in ("completed", "running")


@pytest.mark.asyncio
async def test_start_workflow_not_found(orchestrator):
    with pytest.raises(ValueError, match="not registered"):
        await orchestrator.start_workflow("nonexistent", {})


@pytest.mark.asyncio
async def test_start_interrupted_workflow(orchestrator):
    orchestrator.register_workflow(make_interrupt_definition())
    execution = await orchestrator.start_workflow("interrupt_workflow", {})
    assert execution.status == "interrupted"
    assert len(execution.pending_approvals) >= 1


@pytest.mark.asyncio
async def test_cancel_workflow(orchestrator):
    orchestrator.register_workflow(make_test_definition())
    execution = await orchestrator.start_workflow("test_workflow", {})
    success = await orchestrator.cancel_workflow(execution.thread_id, "test cancel")
    assert success is True


@pytest.mark.asyncio
async def test_cancel_nonexistent(orchestrator):
    success = await orchestrator.cancel_workflow("nonexistent")
    assert success is False


@pytest.mark.asyncio
async def test_get_active_workflows(orchestrator):
    orchestrator.register_workflow(make_interrupt_definition())
    await orchestrator.start_workflow("interrupt_workflow", {})
    active = await orchestrator.get_active_workflows()
    assert len(active) >= 1


@pytest.mark.asyncio
async def test_get_workflow_history(orchestrator):
    orchestrator.register_workflow(make_test_definition())
    await orchestrator.start_workflow("test_workflow", {})
    history = await orchestrator.get_workflow_history("test_workflow")
    assert len(history) >= 1


@pytest.mark.asyncio
async def test_get_execution_status(orchestrator):
    orchestrator.register_workflow(make_test_definition())
    execution = await orchestrator.start_workflow("test_workflow", {})
    status = await orchestrator.get_execution_status(execution.thread_id)
    assert status is not None
    assert status.thread_id == execution.thread_id


@pytest.mark.asyncio
async def test_schedule_workflow(orchestrator):
    orchestrator.register_workflow(make_test_definition())
    schedule = await orchestrator.schedule_workflow(
        "test_workflow",
        "0 6 * * *",
        {"input": "daily"},
        enabled=True,
    )
    assert isinstance(schedule, ScheduledWorkflow)
    assert schedule.cron_expression == "0 6 * * *"


@pytest.mark.asyncio
async def test_list_schedules(orchestrator):
    orchestrator.register_workflow(make_test_definition())
    await orchestrator.schedule_workflow("test_workflow", "0 6 * * *", {})
    schedules = await orchestrator.list_schedules()
    assert len(schedules) >= 1


@pytest.mark.asyncio
async def test_toggle_schedule(orchestrator):
    orchestrator.register_workflow(make_test_definition())
    schedule = await orchestrator.schedule_workflow("test_workflow", "0 6 * * *", {})
    success = await orchestrator.toggle_schedule(schedule.schedule_id, False)
    assert success is True


@pytest.mark.asyncio
async def test_get_stats(orchestrator):
    orchestrator.register_workflow(make_test_definition())
    await orchestrator.start_workflow("test_workflow", {})
    stats = await orchestrator.get_stats()
    assert stats["total_executions"] >= 1
    assert stats["registered_workflows"] >= 1
