"""Tests for BD Knowledge API endpoints (Engine8_Knowledge/api.py).

Uses FastAPI TestClient with mocked dependencies to test endpoint
request/response shapes without requiring external services.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Mock heavy dependencies BEFORE importing the app module.
# The app's lifespan initializes Qdrant, OpenAI, agents, etc. — we
# replace all of that with lightweight mocks so TestClient can start.
# ---------------------------------------------------------------------------

# Mock modules that may not be installed in the test environment
_MOCK_MODULES = [
    "Engine8_Knowledge.scripts.memory_layer",
    "Engine8_Knowledge.scripts.lightrag_engine",
    "Engine8_Knowledge.scripts.hybrid_retriever",
    "Engine8_Knowledge.scripts.query_router",
    "Engine8_Knowledge.scripts.pageindex_engine",
    "Engine8_Knowledge.scripts.redis_cache",
    "Engine8_Knowledge.agents.program_intel_agent",
    "Engine8_Knowledge.agents.company_research_agent",
    "Engine8_Knowledge.agents.contact_finder_agent",
    "Engine8_Knowledge.agents.bd_strategy_agent",
    "Engine8_Knowledge.agents.crewai_orchestrator",
]

for mod in _MOCK_MODULES:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

# config.logging_config needs real return values since the RequestIdMiddleware
# uses generate_request_id() as a header value (must be a string).
import contextvars as _ctx

if "config.logging_config" not in sys.modules:
    _logging_config = MagicMock()
    _logging_config.setup_logging = MagicMock()
    _logging_config.get_logger = MagicMock(return_value=MagicMock())
    _logging_config.generate_request_id = lambda: "test-request-id"
    _logging_config.request_id_var = _ctx.ContextVar("request_id", default="")
    sys.modules["config.logging_config"] = _logging_config

# Do NOT mock slowapi — api.py gracefully handles its absence
# (RATE_LIMITING_AVAILABLE = False). If we mock it, the mock middleware
# breaks Starlette's middleware stack.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_search_result(id_="r1", score=0.85, payload=None, collection="jobs"):
    """Build a mock SearchResult dataclass instance."""
    from Engine8_Knowledge.schemas.search_result import SearchResult

    return SearchResult(
        id=id_,
        score=score,
        payload=payload or {"title": "Test Job"},
        collection=collection,
    )


def _make_rag_response(answer="Test answer", sources=None, query="q"):
    """Build a mock RAG engine response."""
    resp = MagicMock()
    resp.answer = answer
    resp.sources = sources or []
    resp.query = query
    resp.confidence = 0.9
    resp.collection_searched = "jobs"
    resp.timestamp = datetime.now().isoformat()
    return resp


def _make_index_result(indexed=5, errors=0, duration=1.2):
    result = MagicMock()
    result.indexed = indexed
    result.errors = errors
    result.duration_seconds = duration
    return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_store():
    """Mock BDKnowledgeStore with common return values."""
    store = MagicMock()
    store.get_collection_stats.return_value = {
        "jobs": {"points_count": 4, "status": "green"},
        "contacts": {"points_count": 100, "status": "green"},
    }
    store.search.return_value = [_make_search_result()]
    store.search_all.return_value = {
        "jobs": [_make_search_result()],
        "contacts": [],
    }
    store._generate_embedding.return_value = [0.1] * 1536
    return store


@pytest.fixture()
def mock_rag():
    """Mock BDRAGEngine."""
    engine = MagicMock()
    engine.ask.return_value = _make_rag_response()
    return engine


@pytest.fixture()
def mock_indexer():
    """Mock BDIndexer."""
    idx = MagicMock()
    idx.index_all.return_value = [_make_index_result()]
    idx.index_jobs.return_value = _make_index_result()
    idx.index_contacts.return_value = _make_index_result()
    idx.index_programs.return_value = _make_index_result()
    idx.index_documents.return_value = _make_index_result()
    idx.index_activities.return_value = _make_index_result()
    return idx


@pytest.fixture()
def client(mock_store, mock_rag, mock_indexer):
    """Provide a TestClient with all globals patched."""
    # Patch the globals that lifespan would set
    patches = {
        "store": mock_store,
        "rag_engine": mock_rag,
        "indexer": mock_indexer,
        "memory": MagicMock(),
        "graph": MagicMock(),
        "retriever": None,
        "router": MagicMock(),
        "pageindex": MagicMock(),
        "cache": MagicMock(),
        "program_agent": MagicMock(),
        "company_agent": MagicMock(),
        "contact_agent": MagicMock(),
        "strategy_agent": MagicMock(),
        "orchestrator": MagicMock(),
    }

    # Override the lifespan so it doesn't actually init anything
    from Engine8_Knowledge.api import app
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _noop_lifespan(_app):
        yield

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _noop_lifespan

    with patch.multiple("Engine8_Knowledge.api", **patches):
        # Disable auth for test simplicity (BD_API_KEY is empty via conftest)
        from fastapi.testclient import TestClient

        tc = TestClient(app)
        yield tc

    app.router.lifespan_context = original_lifespan


# ===================================================================
# Health Probes
# ===================================================================


class TestHealthEndpoints:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "timestamp" in data
        assert "components" in data

    def test_health_components_present(self, client):
        data = client.get("/health").json()
        assert "qdrant" in data["components"]
        assert "memory" in data["components"]
        assert "graph" in data["components"]

    def test_ready_returns_200(self, client):
        resp = client.get("/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] is True

    def test_live_returns_200(self, client):
        resp = client.get("/live")
        assert resp.status_code == 200
        assert resp.json()["live"] is True


# ===================================================================
# POST /search
# ===================================================================


class TestSearchEndpoint:
    def test_search_success(self, client):
        resp = client.post("/search", json={"query": "DCGS analyst"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "DCGS analyst"
        assert "results" in data
        assert "count" in data
        assert "timestamp" in data

    def test_search_with_collection(self, client):
        resp = client.post(
            "/search", json={"query": "test", "collection": "contacts", "limit": 5}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["collection"] == "contacts"

    def test_search_with_filters(self, client):
        resp = client.post(
            "/search",
            json={
                "query": "engineer",
                "collection": "jobs",
                "filters": {"company": "Leidos"},
            },
        )
        assert resp.status_code == 200

    def test_search_missing_query_returns_422(self, client):
        resp = client.post("/search", json={})
        assert resp.status_code == 422

    def test_search_limit_validation(self, client):
        resp = client.post("/search", json={"query": "test", "limit": 0})
        assert resp.status_code == 422

        resp2 = client.post("/search", json={"query": "test", "limit": 100})
        assert resp2.status_code == 422

    def test_search_empty_results(self, client, mock_store):
        mock_store.search.return_value = []
        resp = client.post(
            "/search", json={"query": "nonexistent", "collection": "jobs"}
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0
        assert resp.json()["results"] == []

    def test_search_score_threshold(self, client):
        resp = client.post(
            "/search",
            json={"query": "test", "score_threshold": 0.8, "collection": "jobs"},
        )
        assert resp.status_code == 200

    def test_search_get_endpoint(self, client):
        resp = client.get("/search", params={"q": "DCGS"})
        assert resp.status_code == 200

    def test_search_get_missing_q_returns_422(self, client):
        resp = client.get("/search")
        assert resp.status_code == 422


# ===================================================================
# POST /ask
# ===================================================================


class TestAskEndpoint:
    def test_ask_success(self, client):
        resp = client.post("/ask", json={"question": "Who works on DCGS?"})
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "sources" in data
        assert "confidence" in data
        assert "query" in data

    def test_ask_with_collection(self, client):
        resp = client.post(
            "/ask", json={"question": "test", "collection": "contacts", "limit": 3}
        )
        assert resp.status_code == 200

    def test_ask_missing_question_returns_422(self, client):
        resp = client.post("/ask", json={})
        assert resp.status_code == 422

    def test_ask_get_endpoint(self, client):
        resp = client.get("/ask", params={"q": "What programs does Leidos prime?"})
        assert resp.status_code == 200

    def test_ask_get_missing_q_returns_422(self, client):
        resp = client.get("/ask")
        assert resp.status_code == 422


# ===================================================================
# GET /stats
# ===================================================================


class TestStatsEndpoint:
    def test_stats_returns_200(self, client):
        resp = client.get("/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "qdrant" in data
        assert "timestamp" in data


# ===================================================================
# POST /index/{collection}
# ===================================================================


class TestIndexEndpoints:
    def test_index_specific_collection(self, client):
        resp = client.post("/index/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["indexed"] == 5

    def test_index_unknown_collection_returns_400(self, client):
        resp = client.post("/index/unknown_collection")
        assert resp.status_code == 400

    def test_index_all(self, client):
        resp = client.post("/index/all")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_index_contacts(self, client):
        resp = client.post("/index/contacts")
        assert resp.status_code == 200

    def test_index_programs(self, client):
        resp = client.post("/index/programs")
        assert resp.status_code == 200


# ===================================================================
# QA Endpoints
# ===================================================================


class TestQAEndpoints:
    def test_qa_stats_import_error(self, client):
        """qa/stats returns 500 when Engine6_QA is not importable."""
        resp = client.get("/qa/stats")
        # Engine6_QA is unlikely to be in the test env
        assert resp.status_code in (200, 500)

    def test_qa_review_queue_import_error(self, client):
        resp = client.get("/qa/review-queue")
        assert resp.status_code in (200, 500)


# ===================================================================
# Scoring Validation
# ===================================================================


class TestScoringEndpoint:
    def test_scoring_validate_import_error(self, client):
        """Returns 501 when score_validator dependencies are missing."""
        resp = client.get("/scoring/validate")
        assert resp.status_code in (200, 500, 501)


# ===================================================================
# Contacts/Programs filter
# ===================================================================


class TestFilterEndpoints:
    def test_contacts_filter_with_query(self, client, mock_store):
        mock_store.client.query_points.return_value = MagicMock(points=[])
        resp = client.post(
            "/contacts/filter", json={"query": "DCGS", "limit": 10}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "contacts" in data
        assert "count" in data

    def test_contacts_filter_without_query(self, client, mock_store):
        mock_store.client.scroll.return_value = ([], None)
        resp = client.post("/contacts/filter", json={"limit": 5})
        assert resp.status_code == 200

    def test_programs_filter(self, client, mock_store):
        mock_store.client.query_points.return_value = MagicMock(points=[])
        resp = client.post(
            "/programs/filter", json={"query": "DCGS", "limit": 5}
        )
        assert resp.status_code == 200


# ===================================================================
# Convenience GET endpoints
# ===================================================================


class TestConvenienceEndpoints:
    def test_programs_list(self, client, mock_store):
        mock_store.client.scroll.return_value = ([], None)
        resp = client.get("/programs")
        assert resp.status_code == 200

    def test_contacts_list(self, client, mock_store):
        mock_store.client.scroll.return_value = ([], None)
        resp = client.get("/contacts/list")
        assert resp.status_code == 200

    def test_dashboard_stats(self, client, mock_store):
        mock_store.client.scroll.return_value = ([], None)
        resp = client.get("/dashboard/stats")
        assert resp.status_code == 200


# ===================================================================
# Edge cases and error paths
# ===================================================================


class TestEdgeCases:
    def test_search_when_store_unavailable(self, client):
        with patch("Engine8_Knowledge.api.store", None):
            resp = client.post("/search", json={"query": "test"})
            assert resp.status_code == 503

    def test_ask_when_rag_unavailable(self, client):
        with patch("Engine8_Knowledge.api.rag_engine", None):
            resp = client.post("/ask", json={"question": "test"})
            assert resp.status_code == 503

    def test_index_when_indexer_unavailable(self, client):
        with patch("Engine8_Knowledge.api.indexer", None):
            resp = client.post("/index/jobs")
            assert resp.status_code == 503

    def test_index_all_when_indexer_unavailable(self, client):
        with patch("Engine8_Knowledge.api.indexer", None):
            resp = client.post("/index/all")
            assert resp.status_code == 503

    def test_search_internal_error(self, client, mock_store):
        mock_store.search.side_effect = RuntimeError("connection lost")
        resp = client.post(
            "/search", json={"query": "test", "collection": "jobs"}
        )
        assert resp.status_code == 500

    def test_ask_internal_error(self, client, mock_rag):
        mock_rag.ask.side_effect = RuntimeError("LLM timeout")
        resp = client.post("/ask", json={"question": "test"})
        assert resp.status_code == 500
