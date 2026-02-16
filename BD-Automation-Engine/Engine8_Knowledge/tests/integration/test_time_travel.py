"""
Phase 23A — Time-Travel Debugger Tests

Tests execution timeline, state inspection, diffs, replay/fork,
and execution comparison.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.workflows.checkpoint_store import (
    CheckpointStore,
    DictMetaStore,
)
from Engine8_Knowledge.workflows.time_travel import (
    TimeTravelDebugger,
    ExecutionTimeline,
    StateDiff,
    get_time_travel_debugger,
)


@pytest.fixture
def store():
    s = CheckpointStore(db_path="data/test_tt.db")
    s._db = DictMetaStore()
    return s


@pytest.fixture
def debugger(store):
    return TimeTravelDebugger(checkpoint_store=store)


async def _seed_thread(store, tid="t1", workflow="test_wf"):
    """Seed a thread with some snapshots."""
    await store.create_thread(workflow, thread_id=tid)
    await store.save_snapshot(tid, 1, "node_a", {"x": 1, "errors": []})
    await store.save_snapshot(tid, 2, "node_b", {"x": 1, "y": 2, "errors": []})
    await store.save_snapshot(tid, 3, "node_c", {"x": 1, "y": 2, "z": 3, "errors": []})
    await store.update_thread_status(tid, "completed", step_count=3)


def test_init(debugger):
    assert debugger is not None
    assert debugger.checkpoint_store is not None


@pytest.mark.asyncio
async def test_get_execution_timeline(store, debugger):
    await _seed_thread(store)
    timeline = await debugger.get_execution_timeline("t1")
    assert isinstance(timeline, ExecutionTimeline)
    assert timeline.workflow_name == "test_wf"
    assert timeline.total_steps == 3
    assert len(timeline.nodes_visited) == 3
    assert timeline.nodes_visited[0].node_name == "node_a"


@pytest.mark.asyncio
async def test_get_execution_timeline_not_found(debugger):
    with pytest.raises(ValueError, match="not found"):
        await debugger.get_execution_timeline("nonexistent")


@pytest.mark.asyncio
async def test_inspect_state_at(store, debugger):
    await _seed_thread(store)
    state = await debugger.inspect_state_at("t1", 2)
    assert state["step"] == 2
    assert state["node_name"] == "node_b"
    assert state["state"]["y"] == 2


@pytest.mark.asyncio
async def test_inspect_state_not_found(store, debugger):
    await _seed_thread(store)
    with pytest.raises(ValueError, match="No checkpoint"):
        await debugger.inspect_state_at("t1", 99)


@pytest.mark.asyncio
async def test_diff_states(store, debugger):
    await _seed_thread(store)
    diff = await debugger.diff_states("t1", 1, 3)
    assert isinstance(diff, StateDiff)
    assert "z" in diff.added_keys or "z" in diff.modified_keys


@pytest.mark.asyncio
async def test_diff_states_modified(store, debugger):
    await store.create_thread("test", thread_id="t2")
    await store.save_snapshot("t2", 1, "a", {"val": 10, "errors": []})
    await store.save_snapshot("t2", 2, "b", {"val": 20, "errors": []})
    diff = await debugger.diff_states("t2", 1, 2)
    assert "val" in diff.modified_keys


@pytest.mark.asyncio
async def test_replay_from(store, debugger):
    await _seed_thread(store)
    new_tid = await debugger.replay_from("t1", 2)
    assert new_tid.startswith("fork_")
    # Verify forked thread exists
    threads = await store.list_threads()
    assert any(t.thread_id == new_tid for t in threads)


@pytest.mark.asyncio
async def test_replay_with_modifications(store, debugger):
    await _seed_thread(store)
    new_tid = await debugger.replay_from("t1", 2, modified_state={"y": 999})
    history = await store.get_thread_history(new_tid)
    assert len(history) >= 1
    assert history[0].state["y"] == 999


@pytest.mark.asyncio
async def test_compare_executions(store, debugger):
    await _seed_thread(store, "t_a", "same_wf")
    await _seed_thread(store, "t_b", "same_wf")
    # Modify t_b state
    await store.save_snapshot(
        "t_b", 4, "extra_node", {"x": 1, "y": 2, "z": 3, "w": 4, "errors": []}
    )

    report = await debugger.compare_executions("t_a", "t_b")
    assert report.thread_id_a == "t_a"
    assert report.thread_id_b == "t_b"
    assert len(report.shared_nodes) >= 3


def test_summarize_state(debugger):
    result = debugger._summarize_state({"a": 1, "b": 2})
    assert "a" in result


def test_summarize_value(debugger):
    assert debugger._summarize_value([1, 2, 3]) == [1, 2, 3]
    assert "items" in debugger._summarize_value(list(range(10)))
    assert "keys" in str(debugger._summarize_value({f"k{i}": i for i in range(10)}))


def test_singleton():
    d1 = get_time_travel_debugger()
    d2 = get_time_travel_debugger()
    assert d1 is d2
