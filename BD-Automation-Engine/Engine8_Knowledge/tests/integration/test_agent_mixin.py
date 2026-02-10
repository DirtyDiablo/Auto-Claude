"""
Phase 25A — Agent Memory Mixin Tests

Tests AgentMemoryMixin: remember, recall, recall_contact, learn_from_outcome,
forget, get_briefing — both with and without a MemoryStore backend.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.memory.agent_mixin import AgentMemoryMixin, ContactMemoryBrief


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mixin():
    """AgentMemoryMixin with no backend (uses local memories)."""
    return AgentMemoryMixin(agent_id="agent_bd")


@pytest.fixture
def mock_store():
    store = AsyncMock()
    recall_result = MagicMock()
    recall_result.results = {
        "episodic": [
            {"content": "DCGS analyst meeting", "score": 0.9, "id": "e1"},
            {"content": "ISR program review", "score": 0.7, "id": "e2"},
        ],
        "procedural": [
            {"content": "Cold email worked for DCGS", "score": 0.8, "id": "p1"},
        ],
    }
    store.recall = AsyncMock(return_value=recall_result)
    store.add_memory = AsyncMock(return_value="mem_stored_123")

    contact_memory = MagicMock()
    contact_memory.interactions = [
        {"content": "Called Alice about DCGS"},
    ]
    contact_memory.insights = [
        {"content": "Alice prefers email"},
    ]
    contact_memory.preferences = [
        {"content": "Morning meetings work best"},
    ]
    contact_memory.total_memories = 3
    store.get_contact_memory = AsyncMock(return_value=contact_memory)
    store.mem0 = MagicMock()
    store.mem0.delete = AsyncMock(return_value=True)

    return store


@pytest.fixture
def mixin_with_store(mock_store):
    return AgentMemoryMixin(agent_id="agent_bd", memory_store=mock_store)


# ---------------------------------------------------------------------------
# TestInit
# ---------------------------------------------------------------------------


class TestInit:
    def test_init(self):
        m = AgentMemoryMixin(agent_id="test_agent")
        assert m.agent_id == "test_agent"
        assert m._memory_store is None
        assert m._local_memories == []


# ---------------------------------------------------------------------------
# TestRemember
# ---------------------------------------------------------------------------


class TestRemember:
    @pytest.mark.asyncio
    async def test_remember(self, mixin):
        mid = await mixin.remember("Important DCGS insight")
        assert mid == "local_0"
        assert len(mixin._local_memories) == 1
        assert mixin._local_memories[0]["content"] == "Important DCGS insight"
        assert mixin._local_memories[0]["agent_id"] == "agent_bd"

    @pytest.mark.asyncio
    async def test_remember_with_store(self, mixin_with_store, mock_store):
        mid = await mixin_with_store.remember("Stored memory")
        assert mid == "mem_stored_123"
        mock_store.add_memory.assert_called_once()


# ---------------------------------------------------------------------------
# TestRecall
# ---------------------------------------------------------------------------


class TestRecall:
    @pytest.mark.asyncio
    async def test_recall(self, mixin):
        await mixin.remember("DCGS analyst data")
        await mixin.remember("ISR program info")
        results = await mixin.recall("DCGS")
        assert len(results) == 1
        assert "DCGS" in results[0]["content"]

    @pytest.mark.asyncio
    async def test_recall_empty(self, mixin):
        results = await mixin.recall("nonexistent query")
        assert results == []


# ---------------------------------------------------------------------------
# TestRecallContact
# ---------------------------------------------------------------------------


class TestRecallContact:
    @pytest.mark.asyncio
    async def test_recall_contact(self, mixin_with_store):
        brief = await mixin_with_store.recall_contact("alice_id")
        assert isinstance(brief, ContactMemoryBrief)
        assert brief.contact_id == "alice_id"
        assert brief.interaction_count == 1

    @pytest.mark.asyncio
    async def test_recall_contact_local(self, mixin):
        """Contact recall with local-only memories."""
        await mixin.remember("Met with Bob about DCGS", {"contact_id": "bob_id"})
        brief = await mixin.recall_contact("bob_id")
        assert isinstance(brief, ContactMemoryBrief)
        assert brief.contact_id == "bob_id"
        assert brief.interaction_count == 1


# ---------------------------------------------------------------------------
# TestLearnFromOutcome
# ---------------------------------------------------------------------------


class TestLearnFromOutcome:
    @pytest.mark.asyncio
    async def test_learn_from_outcome(self, mixin):
        await mixin.learn_from_outcome(
            action="Cold email to DCGS lead",
            outcome="Meeting booked",
            score=0.9,
        )
        assert len(mixin._local_memories) == 1
        mem = mixin._local_memories[0]
        assert "Cold email" in mem["content"]
        assert mem["type"] == "pattern"
        assert mem["score"] == 0.9


# ---------------------------------------------------------------------------
# TestForget
# ---------------------------------------------------------------------------


class TestForget:
    @pytest.mark.asyncio
    async def test_forget(self, mixin):
        mid = await mixin.remember("To be forgotten")
        ok = await mixin.forget(mid)
        assert ok is True
        assert len(mixin._local_memories) == 0

    @pytest.mark.asyncio
    async def test_forget_nonexistent(self, mixin):
        ok = await mixin.forget("nonexistent_id")
        assert ok is False


# ---------------------------------------------------------------------------
# TestBriefing
# ---------------------------------------------------------------------------


class TestBriefing:
    @pytest.mark.asyncio
    async def test_get_briefing(self, mixin):
        await mixin.remember("DCGS program had issues last quarter")
        await mixin.remember("DCGS team prefers detailed proposals")
        briefing = await mixin.get_briefing("Prepare for DCGS meeting")
        assert "agent_bd" in briefing
        assert "DCGS" in briefing
        assert "Relevant context from memory" in briefing

    @pytest.mark.asyncio
    async def test_briefing_no_memories(self, mixin):
        briefing = await mixin.get_briefing("Unknown topic with no history")
        assert "No prior context found" in briefing
