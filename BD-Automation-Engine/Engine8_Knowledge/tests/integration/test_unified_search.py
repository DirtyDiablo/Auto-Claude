"""
Phase 22A — Unified Search Tests

Tests query classification, mode routing, multi-search, query expansion.
Uses mocking — does not require Qdrant, Neo4j, or OpenAI.
"""

import pytest
from unittest.mock import MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.search.unified_search import (
    UnifiedSearch,
)
from Engine8_Knowledge.search.hybrid_engine import SearchResponse, SearchResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_hybrid():
    h = MagicMock()
    h.search.return_value = SearchResponse(
        results=[SearchResult(id="1", content="test result", score=0.9, source="bd_contacts")],
        mode_used="hybrid",
        search_latency_ms=100,
        total_candidates=50,
        channels_used=["dense", "sparse"],
    )
    h.search_with_graph.return_value = SearchResponse(
        results=[SearchResult(id="g1", content="graph result", score=0.85, source="graph")],
        mode_used="graphrag",
        search_latency_ms=200,
        total_candidates=75,
        channels_used=["dense", "sparse", "graph"],
    )
    return h


@pytest.fixture
def mock_graph():
    g = MagicMock()
    g.retrieve.return_value = []
    return g


@pytest.fixture
def us(mock_hybrid, mock_graph):
    return UnifiedSearch(hybrid_engine=mock_hybrid, graph_retriever=mock_graph)


# ---------------------------------------------------------------------------
# TestQueryClassification
# ---------------------------------------------------------------------------

class TestQueryClassification:
    """Test query classification logic."""

    def test_graph_keyword(self, us):
        assert us._classify_query("How is Alice connected to DCGS?") == "graph"

    def test_relationship_query(self, us):
        assert us._classify_query("Find introduction path to Bob") == "graph"

    def test_entity_query(self, us):
        assert us._classify_query("Who is Kingsley Ero?") == "graph"

    def test_program_query(self, us):
        assert us._classify_query("What about the DCGS program updates?") == "graphrag"

    def test_keyword_heavy(self, us):
        result = us._classify_query("TS/SCI CI Poly engineer San Diego")
        assert result in ("hybrid", "keyword")

    def test_capitalized_names(self, us):
        assert us._classify_query("Tell me about John Smith at Northrop Grumman") == "graphrag"

    def test_default_hybrid(self, us):
        assert us._classify_query("general search about defense industry") == "hybrid"

    def test_semantic_query(self, us):
        assert us._classify_query("modernization challenges for legacy systems") == "hybrid"


# ---------------------------------------------------------------------------
# TestSearch
# ---------------------------------------------------------------------------

class TestSearch:
    """Test search routing."""

    def test_auto_mode(self, us, mock_hybrid):
        resp = us.search("general query", mode="auto")
        assert isinstance(resp, SearchResponse)

    def test_hybrid_mode(self, us, mock_hybrid):
        resp = us.search("test", mode="hybrid")
        mock_hybrid.search.assert_called()

    def test_graph_mode(self, us, mock_graph):
        mock_graph.retrieve.return_value = []
        resp = us.search("Who is Alice?", mode="graph")
        assert isinstance(resp, SearchResponse)

    def test_graphrag_mode(self, us, mock_hybrid, mock_graph):
        mock_graph.retrieve.return_value = []
        resp = us.search("DCGS program details", mode="graphrag")
        assert isinstance(resp, SearchResponse)

    def test_vector_mode(self, us, mock_hybrid):
        resp = us.search("test vector", mode="vector")
        mock_hybrid.search.assert_called()

    def test_keyword_mode(self, us, mock_hybrid):
        resp = us.search("TS/SCI engineer", mode="keyword")
        mock_hybrid.search.assert_called()

    def test_search_with_filters(self, us, mock_hybrid):
        resp = us.search("test", filters={"program": "DCGS"})
        assert isinstance(resp, SearchResponse)

    def test_search_no_expand(self, us, mock_hybrid):
        resp = us.search("test", expand_query=False)
        assert isinstance(resp, SearchResponse)

    def test_search_with_expansion(self, us, mock_hybrid):
        mock_expander = MagicMock()
        expanded = MagicMock()
        expanded.expanded = "test expanded query"
        mock_expander.expand_query.return_value = expanded
        us._expander = mock_expander
        resp = us.search("test", expand_query=True)
        assert isinstance(resp, SearchResponse)


# ---------------------------------------------------------------------------
# TestMultiSearch
# ---------------------------------------------------------------------------

class TestMultiSearch:
    """Test batch search."""

    def test_multi_search(self, us, mock_hybrid):
        responses = us.multi_search(["query1", "query2"])
        assert len(responses) == 2

    def test_multi_search_empty(self, us):
        responses = us.multi_search([])
        assert responses == []


# ---------------------------------------------------------------------------
# TestModes
# ---------------------------------------------------------------------------

class TestModes:
    """Test mode descriptions."""

    def test_get_modes(self, us):
        modes = us.get_modes()
        assert "auto" in modes
        assert "hybrid" in modes
        assert "graphrag" in modes
        assert len(modes) == 6

    def test_mode_has_description(self, us):
        modes = us.get_modes()
        for name, info in modes.items():
            assert "description" in info
            assert "name" in info


# ---------------------------------------------------------------------------
# TestGraphSearch
# ---------------------------------------------------------------------------

class TestGraphSearch:
    """Test graph-first search."""

    def test_graph_search_with_results(self, us, mock_graph):
        from Engine8_Knowledge.search.graph_retriever import GraphResult
        mock_graph.retrieve.return_value = [
            GraphResult(id="g1", name="Alice", entity_type="Person", context_text="Alice is a PM", score=0.9),
        ]
        resp = us._graph_search("Who is Alice?", top_k=5, filters=None)
        assert len(resp.results) == 1
        assert resp.results[0].source == "graph"

    def test_graph_search_fallback(self, us, mock_graph, mock_hybrid):
        mock_graph.retrieve.side_effect = Exception("neo4j unavailable")
        resp = us._graph_search("test", top_k=5, filters=None)
        # Falls back to hybrid
        assert isinstance(resp, SearchResponse)


# ---------------------------------------------------------------------------
# TestSingleton
# ---------------------------------------------------------------------------

class TestSingleton:
    """Test singleton factory."""

    def test_get_instance(self):
        import Engine8_Knowledge.search.unified_search as mod
        mod._instance = None
        us = mod.get_unified_search()
        assert us is not None
        us2 = mod.get_unified_search()
        assert us is us2
        mod._instance = None
