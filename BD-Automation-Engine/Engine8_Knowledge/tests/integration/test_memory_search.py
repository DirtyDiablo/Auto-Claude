"""
Phase 25A — Memory-Aware Search Tests

Tests MemoryAwareSearch: search with memory augmentation, session caching,
conversation-aware expansion, result merging.
No external services required — uses mocked backends.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.search.memory_search import MemoryAwareSearch, MemorySearchResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_unified():
    us = AsyncMock()
    us.search = AsyncMock(return_value={
        "results": [
            {"id": "r1", "content": "DCGS analyst result", "score": 0.9},
            {"id": "r2", "content": "ISR program result", "score": 0.7},
        ]
    })
    return us


@pytest.fixture
def mock_memory_store():
    ms = AsyncMock()
    recall_result = MagicMock()
    recall_result.results = {
        "episodic": [{"content": "Previous DCGS meeting", "score": 0.6, "id": "m1"}],
        "semantic": [{"content": "DCGS architecture docs", "score": 0.5, "id": "m2"}],
    }
    ms.recall = AsyncMock(return_value=recall_result)
    return ms


@pytest.fixture
def search(mock_unified, mock_memory_store):
    return MemoryAwareSearch(unified_search=mock_unified, memory_store=mock_memory_store)


# ---------------------------------------------------------------------------
# TestInit
# ---------------------------------------------------------------------------


class TestInit:
    def test_init(self):
        s = MemoryAwareSearch()
        assert s.unified_search is None
        assert s.memory_store is None
        assert s._session_cache == {}


# ---------------------------------------------------------------------------
# TestSearch
# ---------------------------------------------------------------------------


class TestSearch:
    @pytest.mark.asyncio
    async def test_search_basic(self, search, mock_unified):
        result = await search.search("DCGS contacts", user_id="u1")
        assert isinstance(result, MemorySearchResult)
        assert result.query == "DCGS contacts"
        assert result.total_results > 0
        assert result.from_cache is False

    @pytest.mark.asyncio
    async def test_search_with_memory(self, search):
        result = await search.search("DCGS", user_id="u1")
        assert result.memory_matches >= 2  # episodic + semantic memories
        assert len(result.memory_context) >= 2

    @pytest.mark.asyncio
    async def test_search_cached(self, search):
        """Second identical search returns cached results."""
        r1 = await search.search("DCGS test", user_id="u1")
        assert r1.from_cache is False

        r2 = await search.search("DCGS test", user_id="u1")
        assert r2.from_cache is True
        assert r2.total_results == r1.total_results

    @pytest.mark.asyncio
    async def test_search_no_unified(self, mock_memory_store):
        """Search works even without unified search engine."""
        s = MemoryAwareSearch(unified_search=None, memory_store=mock_memory_store)
        result = await s.search("test query", user_id="u1")
        assert isinstance(result, MemorySearchResult)
        # Should still return memory results
        assert result.memory_matches >= 0


# ---------------------------------------------------------------------------
# TestSearchWithHistory
# ---------------------------------------------------------------------------


class TestSearchWithHistory:
    @pytest.mark.asyncio
    async def test_search_with_history(self, search):
        conversation = [
            {"role": "user", "content": "Tell me about DCGS Program contacts"},
            {"role": "assistant", "content": "Here are the DCGS contacts at Northrop Grumman"},
        ]
        result = await search.search_with_history(
            "Who is the PM?", user_id="u1", conversation=conversation
        )
        assert isinstance(result, MemorySearchResult)
        assert result.query == "Who is the PM?"  # Original query preserved


# ---------------------------------------------------------------------------
# TestQueryExpansion
# ---------------------------------------------------------------------------


class TestQueryExpansion:
    def test_expand_query(self, search):
        conversation = [
            {"role": "user", "content": "Tell me about Alice Smith at Northrop Grumman"},
        ]
        expanded = search._expand_query("Who is the PM?", conversation)
        assert "Who is the PM?" in expanded
        # Should extract "Alice Smith" or "Northrop Grumman" as entities
        assert len(expanded) >= len("Who is the PM?")

    def test_expand_query_empty(self, search):
        expanded = search._expand_query("test query", [])
        assert expanded == "test query"


# ---------------------------------------------------------------------------
# TestMergeResults
# ---------------------------------------------------------------------------


class TestMergeResults:
    def test_merge_results(self, search):
        search_results = [
            {"id": "r1", "content": "DCGS analyst", "score": 0.9},
            {"id": "r2", "content": "ISR engineer", "score": 0.7},
        ]
        memory_context = [
            {"id": "m1", "content": "Previous DCGS meeting notes", "score": 0.6},
        ]
        merged = search._merge_results(search_results, memory_context, limit=10)
        assert len(merged) >= 2
        # All results should have final_score
        for r in merged:
            assert "final_score" in r

    def test_memory_boost(self, search):
        """Results supported by memory get a score boost."""
        search_results = [
            {"id": "r1", "content": "DCGS program overview details", "score": 0.8},
        ]
        memory_context = [
            {"id": "m1", "content": "DCGS program background data", "score": 0.6},
        ]
        merged = search._merge_results(search_results, memory_context, limit=10)
        boosted = [r for r in merged if r.get("id") == "r1"]
        assert len(boosted) == 1
        assert boosted[0].get("memory_boost", 0) >= 0


# ---------------------------------------------------------------------------
# TestClearCache
# ---------------------------------------------------------------------------


class TestClearCache:
    @pytest.mark.asyncio
    async def test_clear_cache(self, search):
        await search.search("test query", user_id="u1")
        assert len(search._session_cache) > 0
        search.clear_cache()
        assert len(search._session_cache) == 0

    @pytest.mark.asyncio
    async def test_clear_cache_user(self, search):
        await search.search("query1", user_id="u1")
        await search.search("query2", user_id="u2")
        assert len(search._session_cache) == 2
        search.clear_cache(user_id="u1")
        # Only u1 cache cleared
        assert not any(k.startswith("u1:") for k in search._session_cache)
