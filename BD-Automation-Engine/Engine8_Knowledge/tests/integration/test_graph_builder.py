"""
Phase 23A — ProductionGraphBuilder Tests

Tests workflow compilation, node execution with retry, parallel groups,
interrupt handling, and singleton.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.workflows.graph_builder import (
    ProductionGraphBuilder,
    CompiledProductionGraph,
    WorkflowDefinition,
    NodeSpec,
    EdgeSpec,
    RetryConfig,
    get_graph_builder,
)
from Engine8_Knowledge.workflows.checkpoint_store import CheckpointStore, DictMetaStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def node_a(state):
    return {**state, "a_done": True}


async def node_b(state):
    return {**state, "b_done": True}


async def node_end(state):
    return {**state, "result": "done"}


async def failing_node(state):
    raise ValueError("Node failed!")


async def interrupt_node(state):
    return {**state, "reviewed": True}


def make_simple_definition():
    return WorkflowDefinition(
        name="test_workflow",
        description="Simple test workflow",
        state_schema={
            "a_done": False,
            "b_done": False,
            "result": "",
            "errors": [],
            "step_timings": {},
        },
        nodes={
            "node_a": NodeSpec(name="node_a", function=node_a, description="Step A"),
            "node_b": NodeSpec(name="node_b", function=node_b, description="Step B"),
            "node_end": NodeSpec(name="node_end", function=node_end, description="End"),
        },
        edges=[
            EdgeSpec(source="node_a", target="node_b"),
            EdgeSpec(source="node_b", target="node_end"),
            EdgeSpec(source="node_end", target="__end__"),
        ],
        entry_point="node_a",
    )


@pytest.fixture
def store():
    s = CheckpointStore(db_path="data/test_builder.db")
    s._db = DictMetaStore()
    return s


@pytest.fixture
def builder(store):
    return ProductionGraphBuilder(checkpoint_store=store)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_init(builder):
    assert builder is not None
    assert builder.checkpoint_store is not None


def test_node_spec():
    spec = NodeSpec(
        name="test", function=node_a, description="Test", timeout_seconds=60
    )
    assert spec.name == "test"
    assert spec.timeout_seconds == 60
    assert spec.retry_on_error is True


def test_edge_spec():
    edge = EdgeSpec(source="a", target="b")
    assert edge.source == "a"
    assert edge.target == "b"
    assert edge.condition is None


def test_workflow_definition():
    defn = make_simple_definition()
    assert defn.name == "test_workflow"
    assert len(defn.nodes) == 3
    assert len(defn.edges) == 3
    assert defn.entry_point == "node_a"
    assert defn.interrupt_nodes == []
    assert defn.parallel_groups == []


def test_build_workflow(builder):
    defn = make_simple_definition()
    compiled = builder.build(defn)
    assert isinstance(compiled, CompiledProductionGraph)
    assert compiled.workflow_def.name == "test_workflow"


def test_build_stores_compiled(builder):
    defn = make_simple_definition()
    builder.build(defn)
    assert builder.get_compiled("test_workflow") is not None
    assert builder.get_compiled("nonexistent") is None


@pytest.mark.asyncio
async def test_invoke_simple(builder):
    defn = make_simple_definition()
    compiled = builder.build(defn)
    result = await compiled.invoke({"input": "test"})
    assert result.get("a_done") is True
    assert result.get("b_done") is True
    assert result.get("result") == "done"


@pytest.mark.asyncio
async def test_invoke_with_errors(builder):
    defn = WorkflowDefinition(
        name="error_workflow",
        description="Workflow with failing node",
        state_schema={"errors": [], "step_timings": {}},
        nodes={
            "fail": NodeSpec(
                name="fail",
                function=failing_node,
                description="Fail",
                max_retries=2,
                timeout_seconds=10,
            ),
        },
        edges=[EdgeSpec(source="fail", target="__end__")],
        entry_point="fail",
        retry_config={"fail": RetryConfig(max_attempts=2, backoff_seconds=0.01)},
    )
    compiled = builder.build(defn)
    result = await compiled.invoke({})
    assert len(result.get("errors", [])) > 0


@pytest.mark.asyncio
async def test_parallel_execution(builder):
    defn = WorkflowDefinition(
        name="parallel_workflow",
        description="Parallel test",
        state_schema={
            "a_done": False,
            "b_done": False,
            "errors": [],
            "step_timings": {},
        },
        nodes={
            "node_a": NodeSpec(name="node_a", function=node_a, description="A"),
            "node_b": NodeSpec(name="node_b", function=node_b, description="B"),
            "node_end": NodeSpec(name="node_end", function=node_end, description="End"),
        },
        edges=[
            EdgeSpec(source="node_a", target="node_end"),
            EdgeSpec(source="node_b", target="node_end"),
            EdgeSpec(source="node_end", target="__end__"),
        ],
        entry_point="node_a",
        parallel_groups=[["node_a", "node_b"]],
    )
    compiled = builder.build(defn)
    result = await compiled.invoke({})
    assert result.get("a_done") is True
    assert result.get("b_done") is True


@pytest.mark.asyncio
async def test_interrupt_handling(builder):
    defn = WorkflowDefinition(
        name="interrupt_workflow",
        description="Interrupt test",
        state_schema={"reviewed": False, "errors": [], "step_timings": {}},
        nodes={
            "review": NodeSpec(
                name="review",
                function=interrupt_node,
                description="Review",
                timeout_seconds=3600,
                retry_on_error=False,
            ),
            "done": NodeSpec(name="done", function=node_end, description="Done"),
        },
        edges=[
            EdgeSpec(source="review", target="done"),
            EdgeSpec(source="done", target="__end__"),
        ],
        entry_point="review",
        interrupt_nodes=["review"],
    )
    compiled = builder.build(defn)
    result = await compiled.invoke({})
    assert result.get("_interrupted_at") == "review"


def test_list_workflows(builder):
    builder.build(make_simple_definition())
    workflows = builder.list_workflows()
    assert len(workflows) >= 1
    assert any(w.name == "test_workflow" for w in workflows)


def test_singleton():
    b1 = get_graph_builder()
    b2 = get_graph_builder()
    assert b1 is b2
