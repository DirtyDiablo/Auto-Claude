"""
Phase 25A — Mem0 Manager Tests

Tests Mem0Manager: add, search, get_all, update, delete, history, stats.
Uses fallback in-memory store (no Mem0/Qdrant required).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.memory.mem0_manager import Mem0Manager, Memory, MemoryStats


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def manager():
    """Fresh Mem0Manager using in-memory fallback."""
    m = Mem0Manager(qdrant_url="localhost:6333", collection="test_memory")
    m._initialized = True  # Skip Mem0 client init, use fallback
    return m


# ---------------------------------------------------------------------------
# TestInit
# ---------------------------------------------------------------------------


class TestInit:
    def test_init(self):
        m = Mem0Manager(qdrant_url="test:6333", collection="test_col")
        assert m.qdrant_url == "test:6333"
        assert m.collection == "test_col"
        assert m._client is None
        assert m._initialized is False

    def test_singleton(self):
        import Engine8_Knowledge.memory.mem0_manager as mod
        original = mod._manager
        mod._manager = None
        m1 = mod.get_mem0_manager(qdrant_url="localhost:6333")
        m2 = mod.get_mem0_manager()
        assert m1 is m2
        mod._manager = original


# ---------------------------------------------------------------------------
# TestAdd
# ---------------------------------------------------------------------------


class TestAdd:
    @pytest.mark.asyncio
    async def test_add_memory(self, manager):
        mid = await manager.add("Met with Alice about DCGS", user_id="u1")
        assert mid.startswith("mem_")
        assert mid in manager._memories
        assert manager._memories[mid].content == "Met with Alice about DCGS"
        assert manager._memories[mid].user_id == "u1"

    @pytest.mark.asyncio
    async def test_add_with_metadata(self, manager):
        meta = {"type": "interaction", "program": "DCGS"}
        mid = await manager.add(
            "Call with Bob",
            user_id="u1",
            agent_id="agent_bd",
            metadata=meta,
        )
        mem = manager._memories[mid]
        assert mem.agent_id == "agent_bd"
        assert mem.metadata["type"] == "interaction"
        assert mem.metadata["program"] == "DCGS"
        assert "created_at" in mem.metadata


# ---------------------------------------------------------------------------
# TestSearch
# ---------------------------------------------------------------------------


class TestSearch:
    @pytest.mark.asyncio
    async def test_search_memory(self, manager):
        await manager.add("DCGS analyst meeting", user_id="u1")
        await manager.add("ISR program review", user_id="u1")
        results = await manager.search("DCGS", user_id="u1")
        assert len(results) >= 1
        assert any("DCGS" in r.content for r in results)

    @pytest.mark.asyncio
    async def test_search_fallback(self, manager):
        """Fallback keyword search when Mem0 client not available."""
        await manager.add("Alpha DCGS contact info", user_id="u1")
        await manager.add("Beta ISR data point", user_id="u1")
        results = await manager.search("alpha", user_id="u1")
        assert len(results) == 1
        assert "Alpha" in results[0].content

    @pytest.mark.asyncio
    async def test_search_scoped_by_agent(self, manager):
        await manager.add("Agent1 memory", user_id="u1", agent_id="a1")
        await manager.add("Agent2 memory", user_id="u1", agent_id="a2")
        results = await manager.search("memory", user_id="u1", agent_id="a1")
        assert len(results) == 1
        assert results[0].agent_id == "a1"


# ---------------------------------------------------------------------------
# TestGetAll
# ---------------------------------------------------------------------------


class TestGetAll:
    @pytest.mark.asyncio
    async def test_get_all(self, manager):
        await manager.add("Memory 1", user_id="u1")
        await manager.add("Memory 2", user_id="u1")
        await manager.add("Memory 3", user_id="u2")
        results = await manager.get_all(user_id="u1")
        assert len(results) == 2
        assert all(r.user_id == "u1" for r in results)


# ---------------------------------------------------------------------------
# TestUpdate
# ---------------------------------------------------------------------------


class TestUpdate:
    @pytest.mark.asyncio
    async def test_update(self, manager):
        mid = await manager.add("Original content", user_id="u1")
        ok = await manager.update(mid, "Updated content")
        assert ok is True
        assert manager._memories[mid].content == "Updated content"
        # Check history
        history = await manager.get_history(mid)
        assert len(history) == 2
        assert history[1].change_type == "updated"

    @pytest.mark.asyncio
    async def test_update_nonexistent(self, manager):
        ok = await manager.update("nonexistent_id", "new content")
        assert ok is False


# ---------------------------------------------------------------------------
# TestDelete
# ---------------------------------------------------------------------------


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete(self, manager):
        mid = await manager.add("To be deleted", user_id="u1")
        ok = await manager.delete(mid)
        assert ok is True
        assert mid not in manager._memories
        # History should record deletion
        history = await manager.get_history(mid)
        assert any(v.change_type == "deleted" for v in history)

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, manager):
        ok = await manager.delete("nonexistent_id")
        assert ok is False


# ---------------------------------------------------------------------------
# TestHistory
# ---------------------------------------------------------------------------


class TestHistory:
    @pytest.mark.asyncio
    async def test_history(self, manager):
        mid = await manager.add("Version 1", user_id="u1")
        await manager.update(mid, "Version 2")
        history = await manager.get_history(mid)
        assert len(history) == 2
        assert history[0].version == 1
        assert history[0].change_type == "created"
        assert history[1].change_type == "updated"


# ---------------------------------------------------------------------------
# TestStats
# ---------------------------------------------------------------------------


class TestStats:
    @pytest.mark.asyncio
    async def test_stats(self, manager):
        await manager.add("Memory A", user_id="u1", agent_id="a1",
                          metadata={"type": "interaction"})
        await manager.add("Memory B", user_id="u2", agent_id="a1",
                          metadata={"type": "outcome"})
        await manager.add("Memory C", user_id="u1",
                          metadata={"type": "interaction"})

        stats = await manager.get_stats()
        assert isinstance(stats, MemoryStats)
        assert stats.total_memories == 3
        assert stats.by_user["u1"] == 2
        assert stats.by_user["u2"] == 1
        assert stats.by_agent["a1"] == 2
        assert stats.by_type["interaction"] == 2
        assert stats.storage_size_bytes > 0
