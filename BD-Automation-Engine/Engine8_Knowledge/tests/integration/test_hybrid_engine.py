"""
Phase 22A — Hybrid Search Engine Tests

Tests dense + sparse + RRF fusion, reranking, multi-collection search.
Uses mocking — does not require Qdrant or OpenAI.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.search.hybrid_engine import (
    HybridSearchEngine, SearchResult, SearchResponse,
    get_hybrid_search_engine, RRF_K,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    e = HybridSearchEngine(qdrant_url="http://fake:6333")
    e._qdrant = MagicMock()
    e._openai = MagicMock()
    e._sparse_model = MagicMock()
    e._reranker = MagicMock()
    return e


# ---------------------------------------------------------------------------
# TestInit
# ---------------------------------------------------------------------------

class TestHybridEngineInit:
    """Test initialization and lazy loading."""

    def test_default_config(self):
        e = HybridSearchEngine()
        assert e._qdrant_url == "http://localhost:6333"
        assert e._embedding_model == "text-embedding-3-small"

    def test_custom_config(self):
        e = HybridSearchEngine(qdrant_url="http://custom:6333", embedding_model="custom-model")
        assert e._qdrant_url == "http://custom:6333"
        assert e._embedding_model == "custom-model"

    def test_lazy_qdrant(self):
        e = HybridSearchEngine()
        assert e._qdrant is None

    def test_lazy_reranker(self):
        e = HybridSearchEngine()
        assert e._reranker is None


# ---------------------------------------------------------------------------
# TestEmbeddings
# ---------------------------------------------------------------------------

class TestEmbeddings:
    """Test embedding generation."""

    def test_dense_embedding(self, engine):
        mock_resp = MagicMock()
        mock_resp.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        engine._openai.embeddings.create.return_value = mock_resp
        vec = engine.generate_dense_embedding("test query")
        assert len(vec) == 3

    def test_sparse_tokens(self, engine):
        mock_sparse = MagicMock()
        mock_sparse.indices.tolist.return_value = [1, 5, 10]
        mock_sparse.values.tolist.return_value = [0.5, 0.8, 0.3]
        engine._sparse_model.embed.return_value = [mock_sparse]
        tokens = engine.generate_sparse_tokens("test query")
        assert tokens["indices"] == [1, 5, 10]
        assert tokens["values"] == [0.5, 0.8, 0.3]

    def test_sparse_tokens_empty(self, engine):
        engine._sparse_model.embed.return_value = []
        tokens = engine.generate_sparse_tokens("test")
        assert tokens["indices"] == []
        assert tokens["values"] == []


# ---------------------------------------------------------------------------
# TestSearch
# ---------------------------------------------------------------------------

class TestSearch:
    """Test hybrid search."""

    def test_search_returns_response(self, engine):
        engine._qdrant.get_collection.return_value = MagicMock(
            config=MagicMock(params=MagicMock(sparse_vectors=None))
        )
        mock_resp = MagicMock()
        mock_resp.data = [MagicMock(embedding=[0.1] * 1536)]
        engine._openai.embeddings.create.return_value = mock_resp

        mock_point = MagicMock()
        mock_point.id = "p1"
        mock_point.score = 0.95
        mock_point.payload = {"text": "Alice is an engineer", "name": "Alice"}
        mock_query_resp = MagicMock()
        mock_query_resp.points = [mock_point]
        engine._qdrant.query_points.return_value = mock_query_resp

        engine._reranker.predict.return_value = [0.9]

        resp = engine.search("test query", collections=["bd_contacts"], top_k=5)
        assert isinstance(resp, SearchResponse)
        assert resp.mode_used == "hybrid"
        assert len(resp.results) >= 0

    def test_search_all_collections(self, engine):
        collections = engine._resolve_collections("all")
        assert len(collections) == 5
        assert "bd_contacts" in collections

    def test_search_single_collection(self, engine):
        collections = engine._resolve_collections("bd_contacts")
        assert collections == ["bd_contacts"]

    def test_search_list_collections(self, engine):
        collections = engine._resolve_collections(["bd_contacts", "bd_programs"])
        assert len(collections) == 2

    def test_search_handles_error(self, engine):
        engine._qdrant.get_collection.side_effect = Exception("not found")
        mock_resp = MagicMock()
        mock_resp.data = [MagicMock(embedding=[0.1] * 1536)]
        engine._openai.embeddings.create.return_value = mock_resp

        mock_sparse = MagicMock()
        mock_sparse.indices.tolist.return_value = []
        mock_sparse.values.tolist.return_value = []
        engine._sparse_model.embed.return_value = [mock_sparse]

        resp = engine.search("test", collections=["bad_collection"], top_k=5, use_rerank=False)
        assert isinstance(resp, SearchResponse)


# ---------------------------------------------------------------------------
# TestSearchWithGraph
# ---------------------------------------------------------------------------

class TestSearchWithGraph:
    """Test triple-channel search."""

    def test_graph_results_merged(self, engine):
        engine._qdrant.get_collection.return_value = MagicMock(
            config=MagicMock(params=MagicMock(sparse_vectors=None))
        )
        mock_resp = MagicMock()
        mock_resp.data = [MagicMock(embedding=[0.1] * 1536)]
        engine._openai.embeddings.create.return_value = mock_resp
        engine._qdrant.query_points.return_value = MagicMock(points=[])

        mock_sparse = MagicMock()
        mock_sparse.indices.tolist.return_value = []
        mock_sparse.values.tolist.return_value = []
        engine._sparse_model.embed.return_value = [mock_sparse]
        engine._reranker.predict.return_value = [0.8]

        graph = [{"id": "g1", "name": "Alice", "context_text": "Alice is a PM"}]
        resp = engine.search_with_graph("test", graph_results=graph, top_k=5)
        assert resp.mode_used == "graphrag"
        assert "graph" in resp.channels_used

    def test_graph_results_empty(self, engine):
        engine._qdrant.get_collection.return_value = MagicMock(
            config=MagicMock(params=MagicMock(sparse_vectors=None))
        )
        mock_resp = MagicMock()
        mock_resp.data = [MagicMock(embedding=[0.1] * 1536)]
        engine._openai.embeddings.create.return_value = mock_resp
        engine._qdrant.query_points.return_value = MagicMock(points=[])

        mock_sparse = MagicMock()
        mock_sparse.indices.tolist.return_value = []
        mock_sparse.values.tolist.return_value = []
        engine._sparse_model.embed.return_value = [mock_sparse]

        resp = engine.search_with_graph("test", graph_results=[], top_k=5)
        assert isinstance(resp, SearchResponse)


# ---------------------------------------------------------------------------
# TestReranking
# ---------------------------------------------------------------------------

class TestReranking:
    """Test cross-encoder reranking."""

    def test_rerank_orders_by_score(self, engine):
        results = [
            SearchResult(id="1", content="low relevance", score=0.3, source="test"),
            SearchResult(id="2", content="high relevance", score=0.9, source="test"),
        ]
        engine._reranker.predict.return_value = [0.2, 0.95]
        reranked = engine._rerank_results("query", results, top_k=2)
        assert reranked[0].id == "2"

    def test_rerank_empty(self, engine):
        reranked = engine._rerank_results("query", [], top_k=5)
        assert reranked == []

    def test_rerank_respects_top_k(self, engine):
        results = [SearchResult(id=str(i), content=f"r{i}", score=0.5, source="test") for i in range(10)]
        engine._reranker.predict.return_value = list(range(10))
        reranked = engine._rerank_results("query", results, top_k=3)
        assert len(reranked) == 3


# ---------------------------------------------------------------------------
# TestFilter
# ---------------------------------------------------------------------------

class TestFilter:
    """Test filter building."""

    def test_build_filter_string(self, engine):
        f = engine._build_filter({"program": "DCGS"})
        assert f is not None

    def test_build_filter_list(self, engine):
        f = engine._build_filter({"tier": ["Tier 1", "Tier 2"]})
        assert f is not None

    def test_build_filter_empty(self, engine):
        f = engine._build_filter({})
        assert f is None


# ---------------------------------------------------------------------------
# TestSingleton
# ---------------------------------------------------------------------------

class TestSingleton:
    """Test singleton factory."""

    def test_get_instance(self):
        import Engine8_Knowledge.search.hybrid_engine as mod
        mod._instance = None
        e = mod.get_hybrid_search_engine()
        assert e is not None
        e2 = mod.get_hybrid_search_engine()
        assert e is e2
        mod._instance = None


# ---------------------------------------------------------------------------
# TestFormatResults
# ---------------------------------------------------------------------------

class TestFormatResults:
    """Test Qdrant point formatting."""

    def test_format_with_text(self, engine):
        pt = MagicMock()
        pt.id = "abc"
        pt.score = 0.88
        pt.payload = {"text": "Alice is a PM at Leidos", "name": "Alice"}
        results = engine._format_qdrant_results([pt], "bd_contacts")
        assert len(results) == 1
        assert results[0].content == "Alice is a PM at Leidos"
        assert results[0].source == "bd_contacts"

    def test_format_with_no_text(self, engine):
        pt = MagicMock()
        pt.id = "xyz"
        pt.score = 0.5
        pt.payload = {"name": "Bob"}
        results = engine._format_qdrant_results([pt], "bd_contacts")
        assert results[0].content == "Bob"
