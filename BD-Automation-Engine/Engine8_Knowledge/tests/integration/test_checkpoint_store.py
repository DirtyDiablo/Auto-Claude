"""
Phase 23A — CheckpointStore Integration Tests

Tests SQLite-based checkpoint store: thread lifecycle, snapshots,
cleanup, export/import, stats, and health checks.
Uses DictMetaStore fallback — no aiosqlite required.
"""

import pytest
from unittest.mock import patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.workflows.checkpoint_store import (
    CheckpointStore,
    DictMetaStore,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def store(tmp_path):
    """Create a CheckpointStore backed by DictMetaStore (in-memory fallback)."""
    s = CheckpointStore(db_path=str(tmp_path / "test_checkpoints.db"))
    # Force DictMetaStore so tests don't require aiosqlite
    s._db = DictMetaStore()
    return s


# ---------------------------------------------------------------------------
# TestInit
# ---------------------------------------------------------------------------


class TestInit:
    """Test CheckpointStore initialization."""

    def test_init(self, tmp_path):
        s = CheckpointStore(db_path=str(tmp_path / "checkpoints.db"))
        assert s.db_path == str(tmp_path / "checkpoints.db")
        assert s.max_per_thread == 50
        assert s._checkpointer is None
        assert s._db is None

    def test_init_custom_max(self, tmp_path):
        s = CheckpointStore(db_path=str(tmp_path / "cp.db"), max_per_thread=10)
        assert s.max_per_thread == 10

    def test_init_creates_parent_dir(self, tmp_path):
        nested = tmp_path / "sub" / "deep" / "checkpoints.db"
        CheckpointStore(db_path=str(nested))
        assert nested.parent.exists()


# ---------------------------------------------------------------------------
# TestThreadManagement
# ---------------------------------------------------------------------------


class TestThreadManagement:
    """Test thread create, update, list, delete."""

    @pytest.mark.asyncio
    async def test_create_thread(self, store):
        tid = await store.create_thread("contact_enrichment")
        assert tid.startswith("thread_")
        threads = await store.list_threads()
        assert len(threads) == 1
        assert threads[0].workflow_name == "contact_enrichment"
        assert threads[0].status == "running"

    @pytest.mark.asyncio
    async def test_create_thread_custom_id(self, store):
        tid = await store.create_thread("test_workflow", thread_id="custom_123")
        assert tid == "custom_123"
        threads = await store.list_threads()
        assert threads[0].thread_id == "custom_123"

    @pytest.mark.asyncio
    async def test_update_thread_status(self, store):
        tid = await store.create_thread("test_workflow")
        await store.update_thread_status(
            tid, "completed", current_node="end", step_count=5
        )
        threads = await store.list_threads()
        t = threads[0]
        assert t.status == "completed"
        assert t.current_node == "end"
        assert t.step_count == 5

    @pytest.mark.asyncio
    async def test_list_threads(self, store):
        await store.create_thread("wf_a", thread_id="t1")
        await store.create_thread("wf_b", thread_id="t2")
        await store.create_thread("wf_a", thread_id="t3")
        threads = await store.list_threads()
        assert len(threads) == 3

    @pytest.mark.asyncio
    async def test_list_threads_filtered(self, store):
        await store.create_thread("wf_a", thread_id="t1")
        await store.create_thread("wf_b", thread_id="t2")
        await store.create_thread("wf_a", thread_id="t3")
        # Filter by workflow name
        filtered = await store.list_threads(workflow_name="wf_a")
        assert len(filtered) == 2
        assert all(t.workflow_name == "wf_a" for t in filtered)
        # Filter by status
        await store.update_thread_status("t1", "completed")
        completed = await store.list_threads(status="completed")
        assert len(completed) == 1
        assert completed[0].thread_id == "t1"

    @pytest.mark.asyncio
    async def test_delete_thread(self, store):
        tid = await store.create_thread("test_workflow")
        await store.save_snapshot(tid, 1, "node_a", {"key": "value"})
        result = await store.delete_thread(tid)
        assert result is True
        threads = await store.list_threads()
        assert len(threads) == 0
        history = await store.get_thread_history(tid)
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_delete_thread_nonexistent(self, store):
        result = await store.delete_thread("nonexistent_thread")
        assert result is False


# ---------------------------------------------------------------------------
# TestSnapshots
# ---------------------------------------------------------------------------


class TestSnapshots:
    """Test snapshot save, history, checkpoint-at."""

    @pytest.mark.asyncio
    async def test_save_snapshot(self, store):
        tid = await store.create_thread("test_workflow")
        await store.save_snapshot(tid, 1, "node_a", {"data": "hello"})
        history = await store.get_thread_history(tid)
        assert len(history) == 1
        assert history[0].node_name == "node_a"
        assert history[0].state == {"data": "hello"}

    @pytest.mark.asyncio
    async def test_get_thread_history(self, store):
        tid = await store.create_thread("test_workflow")
        await store.save_snapshot(tid, 1, "node_a", {"step": 1})
        await store.save_snapshot(tid, 2, "node_b", {"step": 2})
        await store.save_snapshot(tid, 3, "node_c", {"step": 3})
        history = await store.get_thread_history(tid)
        assert len(history) == 3
        assert history[0].step == 1
        assert history[2].step == 3

    @pytest.mark.asyncio
    async def test_get_checkpoint_at(self, store):
        tid = await store.create_thread("test_workflow")
        await store.save_snapshot(tid, 1, "node_a", {"data": "first"})
        await store.save_snapshot(tid, 2, "node_b", {"data": "second"})
        snap = await store.get_checkpoint_at(tid, 2)
        assert snap is not None
        assert snap.node_name == "node_b"
        assert snap.state == {"data": "second"}

    @pytest.mark.asyncio
    async def test_get_checkpoint_at_missing(self, store):
        tid = await store.create_thread("test_workflow")
        snap = await store.get_checkpoint_at(tid, 99)
        assert snap is None

    @pytest.mark.asyncio
    async def test_save_snapshot_enforces_retention(self, store):
        store.max_per_thread = 3
        tid = await store.create_thread("test_workflow")
        for i in range(5):
            await store.save_snapshot(tid, i, f"node_{i}", {"step": i})
        history = await store.get_thread_history(tid)
        assert len(history) <= 3


# ---------------------------------------------------------------------------
# TestMaintenance
# ---------------------------------------------------------------------------


class TestMaintenance:
    """Test cleanup, export, import."""

    @pytest.mark.asyncio
    async def test_cleanup_old(self, store):
        tid = await store.create_thread("old_workflow")
        # Manually set old timestamp
        store._db.threads[tid].updated_at = "2020-01-01T00:00:00"
        removed = await store.cleanup_old(days=30)
        assert removed == 1
        threads = await store.list_threads()
        assert len(threads) == 0

    @pytest.mark.asyncio
    async def test_cleanup_old_keeps_recent(self, store):
        await store.create_thread("recent_workflow")
        removed = await store.cleanup_old(days=30)
        assert removed == 0
        threads = await store.list_threads()
        assert len(threads) == 1

    @pytest.mark.asyncio
    async def test_export_thread(self, store):
        tid = await store.create_thread("test_workflow", metadata={"key": "val"})
        await store.save_snapshot(tid, 1, "node_a", {"data": "test"})
        exported = await store.export_thread(tid)
        assert "thread" in exported
        assert "snapshots" in exported
        assert "exported_at" in exported
        assert exported["thread"]["thread_id"] == tid
        assert len(exported["snapshots"]) == 1

    @pytest.mark.asyncio
    async def test_export_thread_not_found(self, store):
        exported = await store.export_thread("nonexistent")
        assert "error" in exported

    @pytest.mark.asyncio
    async def test_import_thread(self, store):
        tid = await store.create_thread("original_wf")
        await store.save_snapshot(tid, 1, "node_a", {"data": "original"})
        exported = await store.export_thread(tid)
        new_tid = await store.import_thread(exported)
        assert new_tid.startswith("imported_")
        # Both threads should exist
        threads = await store.list_threads()
        assert len(threads) == 2
        # Imported thread should have the snapshot
        history = await store.get_thread_history(new_tid)
        assert len(history) == 1
        assert history[0].state == {"data": "original"}


# ---------------------------------------------------------------------------
# TestStats
# ---------------------------------------------------------------------------


class TestStats:
    """Test stats and health check."""

    @pytest.mark.asyncio
    async def test_get_stats(self, store):
        await store.create_thread("wf_a", thread_id="t1")
        await store.create_thread("wf_b", thread_id="t2")
        await store.update_thread_status("t1", "completed")
        await store.save_snapshot("t1", 1, "n", {"x": 1})
        stats = await store.get_stats()
        assert stats["total_threads"] == 2
        assert stats["total_checkpoints"] == 1
        assert stats["by_status"]["completed"] == 1
        assert stats["by_status"]["running"] == 1
        assert stats["max_per_thread"] == 50

    @pytest.mark.asyncio
    async def test_health_check(self, store):
        result = await store.health_check()
        assert result["status"] == "healthy"
        assert "stats" in result

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, store):
        with patch.object(store, "get_stats", side_effect=RuntimeError("DB error")):
            result = await store.health_check()
            assert result["status"] == "unhealthy"
            assert "error" in result


# ---------------------------------------------------------------------------
# TestSingleton
# ---------------------------------------------------------------------------


class TestSingleton:
    """Test singleton factory."""

    def test_singleton(self):
        import Engine8_Knowledge.workflows.checkpoint_store as mod

        original = mod._checkpoint_store
        mod._checkpoint_store = None
        try:
            s1 = mod.get_checkpoint_store()
            s2 = mod.get_checkpoint_store()
            assert s1 is s2
        finally:
            mod._checkpoint_store = original
