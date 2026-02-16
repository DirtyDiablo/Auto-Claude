"""
Phase 25A — Memory Lifecycle Manager Tests

Tests MemoryLifecycle: consolidation, decay, compression, importance scoring,
full lifecycle pass. Uses in-memory MemoryStore.
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.memory.lifecycle import MemoryLifecycle, LifecycleReport
from Engine8_Knowledge.memory.memory_store import MemoryStore, MemoryContext


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def store(tmp_path):
    return MemoryStore(storage_path=str(tmp_path / "lifecycle_test"))


@pytest.fixture
def ctx():
    return MemoryContext(user_id="u1")


@pytest.fixture
def lifecycle(store):
    return MemoryLifecycle(memory_store=store)


# ---------------------------------------------------------------------------
# TestInit
# ---------------------------------------------------------------------------


class TestInit:
    def test_init(self):
        lc = MemoryLifecycle()
        assert lc.memory_store is None
        assert lc.mem0 is None
        assert lc._importance_cache == {}


# ---------------------------------------------------------------------------
# TestConsolidate
# ---------------------------------------------------------------------------


class TestConsolidate:
    @pytest.mark.asyncio
    async def test_consolidate_duplicates(self, store, ctx, lifecycle):
        """Duplicate memories should be removed."""
        await store.add_memory("DCGS analyst meeting notes", "episodic", ctx)
        await store.add_memory("DCGS analyst meeting notes", "episodic", ctx)
        await store.add_memory("Unique ISR data", "episodic", ctx)

        consolidated = await lifecycle.consolidate()
        assert consolidated == 1
        assert len(store._episodic) == 2

    @pytest.mark.asyncio
    async def test_consolidate_no_duplicates(self, store, ctx, lifecycle):
        await store.add_memory("Memory A", "episodic", ctx)
        await store.add_memory("Memory B", "episodic", ctx)

        consolidated = await lifecycle.consolidate()
        assert consolidated == 0
        assert len(store._episodic) == 2

    @pytest.mark.asyncio
    async def test_consolidate_empty(self, lifecycle):
        """No error on empty store."""
        consolidated = await lifecycle.consolidate()
        assert consolidated == 0


# ---------------------------------------------------------------------------
# TestDecay
# ---------------------------------------------------------------------------


class TestDecay:
    @pytest.mark.asyncio
    async def test_decay_old(self, store, lifecycle):
        """Memories older than threshold get decayed."""
        old_date = (datetime.utcnow() - timedelta(days=120)).isoformat()
        store._episodic.append(
            {
                "id": "old_1",
                "content": "Old DCGS meeting",
                "created_at": old_date,
                "score": 0.8,
            }
        )

        decayed = await lifecycle.decay(days_threshold=90)
        assert decayed >= 1
        mem = store._episodic[0]
        assert mem.get("decayed") is True
        assert mem["score"] < 0.8  # Score reduced

    @pytest.mark.asyncio
    async def test_decay_recent(self, store, ctx, lifecycle):
        """Recent memories should not be decayed."""
        await store.add_memory("Fresh DCGS data", "episodic", ctx)

        decayed = await lifecycle.decay(days_threshold=90)
        assert decayed == 0
        assert not store._episodic[0].get("decayed")


# ---------------------------------------------------------------------------
# TestCompress
# ---------------------------------------------------------------------------


class TestCompress:
    @pytest.mark.asyncio
    async def test_compress_long(self, store, lifecycle):
        """Long memories get truncated."""
        long_content = "A" * 800
        store._episodic.append(
            {
                "id": "long_1",
                "content": long_content,
            }
        )

        compressed = await lifecycle.compress()
        assert compressed == 1
        mem = store._episodic[0]
        assert len(mem["content"]) <= 504  # 500 + "..."
        assert mem.get("original_content") == long_content

    @pytest.mark.asyncio
    async def test_compress_short(self, store, ctx, lifecycle):
        """Short memories are not compressed."""
        await store.add_memory("Short note", "episodic", ctx)

        compressed = await lifecycle.compress()
        assert compressed == 0


# ---------------------------------------------------------------------------
# TestImportanceScore
# ---------------------------------------------------------------------------


class TestImportanceScore:
    @pytest.mark.asyncio
    async def test_importance_score(self, store, lifecycle):
        """Importance score based on recency and outcome."""
        recent_date = datetime.utcnow().isoformat()
        store._episodic.append(
            {
                "id": "ep_1",
                "content": "Recent interaction",
                "created_at": recent_date,
                "outcome": "positive",
            }
        )

        score = await lifecycle.importance_score("ep_1")
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Recent + has outcome

    @pytest.mark.asyncio
    async def test_importance_score_cached(self, lifecycle):
        """Second call returns cached score."""
        lifecycle._importance_cache["cached_id"] = 0.75
        score = await lifecycle.importance_score("cached_id")
        assert score == 0.75

    @pytest.mark.asyncio
    async def test_importance_score_unknown(self, lifecycle):
        """Unknown memory_id returns default score."""
        score = await lifecycle.importance_score("unknown_id")
        assert score == 0.5


# ---------------------------------------------------------------------------
# TestRunLifecycle
# ---------------------------------------------------------------------------


class TestRunLifecycle:
    @pytest.mark.asyncio
    async def test_run_lifecycle(self, store, ctx, lifecycle):
        """Full lifecycle pass: consolidate -> decay -> compress."""
        # Add some data
        await store.add_memory("DCGS meeting", "episodic", ctx)
        await store.add_memory("DCGS meeting", "episodic", ctx)  # duplicate
        store._episodic.append(
            {
                "id": "old_1",
                "content": "Ancient data " * 100,
                "created_at": (datetime.utcnow() - timedelta(days=200)).isoformat(),
            }
        )

        report = await lifecycle.run_lifecycle()
        assert isinstance(report, LifecycleReport)
        assert report.started_at is not None
        assert report.completed_at is not None
        assert report.duration_seconds >= 0
        assert report.memories_consolidated >= 1

    @pytest.mark.asyncio
    async def test_lifecycle_report(self, lifecycle):
        """Lifecycle on empty store returns valid report with no errors."""
        report = await lifecycle.run_lifecycle()
        assert isinstance(report, LifecycleReport)
        assert report.errors == []
        assert report.memories_consolidated == 0
        assert report.memories_decayed == 0
        assert report.memories_compressed == 0
