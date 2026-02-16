"""
Phase 22A — Search API Router Tests

Tests all 9 search endpoints with mock backends.
Uses FastAPI TestClient — no external services required.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from fastapi.testclient import TestClient
    from fastapi import FastAPI

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from Engine8_Knowledge.search.search_routes import router
from Engine8_Knowledge.search.hybrid_engine import SearchResponse, SearchResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    if not FASTAPI_AVAILABLE:
        pytest.skip("FastAPI not installed")
    return TestClient(app)


@pytest.fixture
def mock_unified():
    us = MagicMock()
    us.search.return_value = SearchResponse(
        results=[SearchResult(id="1", content="test", score=0.9, source="bd_contacts")],
        mode_used="hybrid",
        search_latency_ms=100,
        total_candidates=50,
        channels_used=["dense", "sparse"],
        query_expanded="test expanded",
    )
    us.multi_search.return_value = [
        SearchResponse(
            results=[
                SearchResult(id="1", content="r1", score=0.8, source="bd_contacts")
            ],
            mode_used="hybrid",
            search_latency_ms=80,
            total_candidates=30,
            channels_used=["dense"],
        ),
    ]
    us.get_modes.return_value = {
        "auto": {"name": "auto", "description": "Auto-route"},
        "hybrid": {"name": "hybrid", "description": "Dense + sparse"},
    }
    return us


# ---------------------------------------------------------------------------
# TestSearchEndpoints
# ---------------------------------------------------------------------------


class TestSearchEndpoints:
    """Test search POST endpoints."""

    def test_unified_search(self, client, mock_unified):
        with patch(
            "Engine8_Knowledge.search.search_routes.get_unified_search",
            return_value=mock_unified,
        ):
            resp = client.post("/search/v2", json={"query": "DCGS contacts"})
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "mode_used" in data
        assert data["search_latency_ms"] >= 0

    def test_hybrid_search(self, client, mock_unified):
        with patch(
            "Engine8_Knowledge.search.search_routes.get_unified_search",
            return_value=mock_unified,
        ):
            resp = client.post("/search/v2/hybrid", json={"query": "test"})
        assert resp.status_code == 200

    def test_graph_search(self, client, mock_unified):
        with patch(
            "Engine8_Knowledge.search.search_routes.get_unified_search",
            return_value=mock_unified,
        ):
            resp = client.post("/search/v2/graph", json={"query": "Who is Alice?"})
        assert resp.status_code == 200

    def test_graphrag_search(self, client, mock_unified):
        with patch(
            "Engine8_Knowledge.search.search_routes.get_unified_search",
            return_value=mock_unified,
        ):
            resp = client.post("/search/v2/graphrag", json={"query": "DCGS details"})
        assert resp.status_code == 200

    def test_multi_search(self, client, mock_unified):
        with patch(
            "Engine8_Knowledge.search.search_routes.get_unified_search",
            return_value=mock_unified,
        ):
            resp = client.post("/search/v2/multi", json={"queries": ["q1", "q2"]})
        assert resp.status_code == 200
        assert resp.json()["queries"] == 2

    def test_search_with_filters(self, client, mock_unified):
        with patch(
            "Engine8_Knowledge.search.search_routes.get_unified_search",
            return_value=mock_unified,
        ):
            resp = client.post(
                "/search/v2",
                json={
                    "query": "DCGS",
                    "filters": {"program": "DCGS", "tier": ["Tier 1"]},
                },
            )
        assert resp.status_code == 200

    def test_search_with_mode(self, client, mock_unified):
        with patch(
            "Engine8_Knowledge.search.search_routes.get_unified_search",
            return_value=mock_unified,
        ):
            resp = client.post("/search/v2", json={"query": "test", "mode": "keyword"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# TestInfoEndpoints
# ---------------------------------------------------------------------------


class TestInfoEndpoints:
    """Test GET info endpoints."""

    def test_search_modes(self, client, mock_unified):
        with patch(
            "Engine8_Knowledge.search.search_routes.get_unified_search",
            return_value=mock_unified,
        ):
            resp = client.get("/search/v2/modes")
        assert resp.status_code == 200
        assert "modes" in resp.json()

    def test_search_stats(self, client):
        with patch(
            "Engine8_Knowledge.search.search_routes.RESULTS_DIR", Path("/nonexistent")
        ):
            resp = client.get("/search/v2/stats")
        assert resp.status_code == 200
        assert "available_modes" in resp.json()


# ---------------------------------------------------------------------------
# TestBenchmarkEndpoints
# ---------------------------------------------------------------------------


class TestBenchmarkEndpoints:
    """Test benchmark endpoints."""

    def test_run_benchmark(self, client):
        mock_bench = MagicMock()
        from Engine8_Knowledge.search.benchmark_v2 import BenchmarkResult

        mock_bench.run_benchmark.return_value = {
            "hybrid": BenchmarkResult(
                mode="hybrid",
                precision_at_5=0.5,
                mrr=0.6,
                ndcg_at_10=0.55,
                total_queries=50,
            ),
        }
        mock_bench.export_report.return_value = {"timestamp": "2026-01-01"}
        mock_bench.compare_modes.return_value = [{"mode": "hybrid", "P@5": 0.5}]
        with patch(
            "Engine8_Knowledge.search.search_routes.SearchBenchmarkV2",
            return_value=mock_bench,
        ):
            resp = client.post("/search/v2/benchmark", json={"modes": ["hybrid"]})
        assert resp.status_code == 200
        assert "comparison" in resp.json()

    def test_latest_benchmark_none(self, client):
        mock_bench = MagicMock()
        mock_bench.get_latest_report.return_value = None
        with patch(
            "Engine8_Knowledge.search.search_routes.SearchBenchmarkV2",
            return_value=mock_bench,
        ):
            resp = client.get("/search/v2/benchmark/latest")
        assert resp.status_code == 200
        assert resp.json()["status"] == "no_benchmark_results"

    def test_latest_benchmark_exists(self, client):
        mock_bench = MagicMock()
        mock_bench.get_latest_report.return_value = {
            "timestamp": "2026-01-01",
            "results": {"hybrid": {}},
        }
        with patch(
            "Engine8_Knowledge.search.search_routes.SearchBenchmarkV2",
            return_value=mock_bench,
        ):
            resp = client.get("/search/v2/benchmark/latest")
        assert resp.status_code == 200
        assert "timestamp" in resp.json()


# ---------------------------------------------------------------------------
# TestResponseFormat
# ---------------------------------------------------------------------------


class TestResponseFormat:
    """Test response formatting."""

    def test_result_has_all_fields(self, client, mock_unified):
        with patch(
            "Engine8_Knowledge.search.search_routes.get_unified_search",
            return_value=mock_unified,
        ):
            resp = client.post("/search/v2", json={"query": "test"})
        data = resp.json()
        result = data["results"][0]
        assert "id" in result
        assert "content" in result
        assert "score" in result
        assert "source" in result
        assert "channel_scores" in result
        assert "metadata" in result

    def test_response_has_metadata(self, client, mock_unified):
        with patch(
            "Engine8_Knowledge.search.search_routes.get_unified_search",
            return_value=mock_unified,
        ):
            resp = client.post("/search/v2", json={"query": "test"})
        data = resp.json()
        assert "mode_used" in data
        assert "search_latency_ms" in data
        assert "total_candidates" in data
        assert "channels_used" in data
