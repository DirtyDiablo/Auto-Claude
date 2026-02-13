"""
Phase 25A — 5-Layer Memory Store Tests

Tests MemoryStore: layer classification, add/recall across all layers,
interaction and outcome recording, contact memory, and layer stats.
Uses in-memory fallback — no Redis, Neo4j, or Qdrant required.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.memory.memory_store import (
    MemoryStore,
    MemoryContext,
    InteractionRecord,
    OutcomeRecord,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_storage(tmp_path):
    return str(tmp_path / "memory_test")


@pytest.fixture
def store(tmp_storage):
    """MemoryStore with no external deps, all in-memory."""
    return MemoryStore(storage_path=tmp_storage)


@pytest.fixture
def ctx():
    return MemoryContext(user_id="u1", agent_id="agent_bd")


# ---------------------------------------------------------------------------
# TestInit
# ---------------------------------------------------------------------------


class TestInit:
    def test_init(self, tmp_storage):
        s = MemoryStore(storage_path=tmp_storage)
        assert s.mem0 is None
        assert s.neo4j is None
        assert s.redis is None
        assert isinstance(s._short_term, dict)
        assert isinstance(s._episodic, list)
        assert isinstance(s._procedural, list)


# ---------------------------------------------------------------------------
# TestClassifyLayer
# ---------------------------------------------------------------------------


class TestClassifyLayer:
    def test_classify_layer_episodic(self, store):
        assert store._classify_layer("general content", {"type": "interaction"}) == "episodic"

    def test_classify_layer_procedural(self, store):
        assert store._classify_layer("content", {"type": "pattern"}) == "procedural"

    def test_classify_layer_graph(self, store):
        assert store._classify_layer("content", {"type": "relationship"}) == "graph"

    def test_auto_classify_content(self, store):
        """Content-based classification when no type metadata."""
        assert store._classify_layer("called Alice about DCGS", {}) == "episodic"
        assert store._classify_layer("Alice reports to Bob", {}) == "graph"
        assert store._classify_layer("strategy worked because of timing", {}) == "procedural"

    def test_classify_short_term(self, store):
        assert store._classify_layer("content", {"type": "short_term"}) == "short_term"

    def test_classify_ttl(self, store):
        assert store._classify_layer("content", {"ttl": 3600}) == "short_term"


# ---------------------------------------------------------------------------
# TestAddMemory
# ---------------------------------------------------------------------------


class TestAddMemory:
    @pytest.mark.asyncio
    async def test_add_short_term(self, store, ctx):
        mid = await store.add_memory("quick note", "short_term", ctx)
        assert mid.startswith("st_")
        assert mid in store._short_term

    @pytest.mark.asyncio
    async def test_add_episodic(self, store, ctx):
        mid = await store.add_memory("Met with DCGS team", "episodic", ctx)
        assert mid.startswith("ep_")
        assert len(store._episodic) == 1

    @pytest.mark.asyncio
    async def test_add_procedural(self, store, ctx):
        mid = await store.add_memory("Cold email worked", "procedural", ctx)
        assert mid.startswith("proc_")
        assert len(store._procedural) == 1


# ---------------------------------------------------------------------------
# TestRecall
# ---------------------------------------------------------------------------


class TestRecall:
    @pytest.mark.asyncio
    async def test_recall_all_layers(self, store, ctx):
        await store.add_memory("DCGS short note", "short_term", ctx)
        await store.add_memory("DCGS meeting notes", "episodic", ctx)
        await store.add_memory("DCGS outreach pattern", "procedural", ctx)

        recall = await store.recall("DCGS", ctx)
        assert recall.total_results >= 3
        assert len(recall.layers_searched) == 5  # All 5 layers

    @pytest.mark.asyncio
    async def test_recall_specific_layer(self, store, ctx):
        await store.add_memory("episodic data", "episodic", ctx)
        await store.add_memory("procedural data", "procedural", ctx)

        recall = await store.recall("data", ctx, layers=["episodic"])
        assert "episodic" in recall.layers_searched
        assert len(recall.layers_searched) == 1

    @pytest.mark.asyncio
    async def test_short_term_cache(self, store, ctx):
        """Short-term memory recall uses keyword search."""
        await store.add_memory("cache hit test", "short_term", ctx)
        recall = await store.recall("cache hit", ctx, layers=["short_term"])
        assert recall.results["short_term"]
        assert any("cache hit" in r["content"] for r in recall.results["short_term"])


# ---------------------------------------------------------------------------
# TestInteraction
# ---------------------------------------------------------------------------


class TestInteraction:
    @pytest.mark.asyncio
    async def test_remember_interaction(self, store):
        record = InteractionRecord(
            interaction_type="call",
            contact_id="c123",
            contact_name="Alice Smith",
            summary="Discussed DCGS timeline",
            sentiment="positive",
        )
        mid = await store.remember_interaction("c123", record)
        assert mid is not None
        assert len(store._episodic) == 1
        assert "Alice Smith" in store._episodic[0]["content"]


# ---------------------------------------------------------------------------
# TestOutcome
# ---------------------------------------------------------------------------


class TestOutcome:
    @pytest.mark.asyncio
    async def test_remember_outcome(self, store):
        record = OutcomeRecord(
            action="Cold email",
            outcome="Booked meeting",
            score=0.9,
            campaign_id="camp1",
            contact_id="c123",
            channel="email",
        )
        mid = await store.remember_outcome("camp1", record)
        assert mid.startswith("proc_")
        assert len(store._procedural) == 1
        assert "Cold email" in store._procedural[0]["content"]


# ---------------------------------------------------------------------------
# TestContactMemory
# ---------------------------------------------------------------------------


class TestContactMemory:
    @pytest.mark.asyncio
    async def test_get_contact_memory(self, store):
        record = InteractionRecord(
            interaction_type="meeting",
            contact_id="alice_id",
            contact_name="Alice",
            summary="DCGS briefing",
        )
        await store.remember_interaction("alice_id", record)

        cm = await store.get_contact_memory("alice_id")
        assert cm.contact_id == "alice_id"
        assert cm.total_memories >= 0


# ---------------------------------------------------------------------------
# TestLayerStats
# ---------------------------------------------------------------------------


class TestLayerStats:
    @pytest.mark.asyncio
    async def test_get_layer_stats(self, store, ctx):
        await store.add_memory("short note", "short_term", ctx)
        await store.add_memory("episode", "episodic", ctx)
        await store.add_memory("pattern", "procedural", ctx)

        stats = await store.get_layer_stats()
        assert "short_term" in stats
        assert "episodic" in stats
        assert "procedural" in stats
        assert stats["short_term"].total_entries == 1
        assert stats["episodic"].total_entries == 1
        assert stats["procedural"].total_entries == 1


# ---------------------------------------------------------------------------
# TestProceduralPersistence
# ---------------------------------------------------------------------------


class TestProceduralPersistence:
    @pytest.mark.asyncio
    async def test_procedural_persistence(self, tmp_storage):
        """Procedural memories survive store reload."""
        ctx = MemoryContext(user_id="u1")
        store1 = MemoryStore(storage_path=tmp_storage)
        await store1.add_memory("pattern learned", "procedural", ctx)
        assert len(store1._procedural) == 1

        # Reload store from same path
        store2 = MemoryStore(storage_path=tmp_storage)
        assert len(store2._procedural) == 1
        assert store2._procedural[0]["content"] == "pattern learned"
