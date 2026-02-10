"""
Phase 27A — Org Chart API Tests

Tests 10 FastAPI endpoints: generate, programs, infer, team, chain,
compare, export (json, mermaid), cache, stats.
Uses TestClient with mocked backends.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from dataclasses import asdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from Engine8_Knowledge.api_routers.org_chart_api import router
from Engine8_Knowledge.visualization.org_chart_engine import (
    OrgChart,
    Person,
    Team,
    InferenceReport,
    OrgDiff,
)


# ---------------------------------------------------------------------------
# Fixture Data
# ---------------------------------------------------------------------------


SAMPLE_CHART = OrgChart(
    chart_id="test_chart_001",
    title="Test Org",
    mode="tree",
    nodes=[
        Person(name="Alice VP", title="VP", tier=2, company="GDIT", reports_to=None),
        Person(name="Bob Director", title="Director", tier=3, company="GDIT", reports_to="Alice VP"),
    ],
    edges=[
        {"source": "Alice VP", "target": "Bob Director", "type": "REPORTS_TO"},
    ],
    depth=3,
    generated_at="2025-01-01T00:00:00",
    metadata={"total_nodes": 2, "total_edges": 1, "mode": "tree"},
)


SAMPLE_PEOPLE = [
    Person(name="Alice VP", title="VP", tier=2, company="GDIT", program="DCGS"),
    Person(name="Bob Director", title="Director", tier=3, company="GDIT", program="ISR"),
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app():
    if not FASTAPI_AVAILABLE:
        pytest.skip("FastAPI not installed")
    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_engine():
    engine = AsyncMock()
    engine.generate = AsyncMock(return_value=SAMPLE_CHART)
    engine._fetch_people = AsyncMock(return_value=SAMPLE_PEOPLE)
    engine.infer_reports_to = AsyncMock(return_value=InferenceReport(
        relationships_inferred=5,
        by_tier_hierarchy=3,
        by_location_match=2,
        confidence_avg=0.7,
    ))
    engine.get_team = AsyncMock(return_value=Team(
        leader=Person(name="Alice VP", title="VP", tier=2),
        direct_reports=[Person(name="Bob Director", title="Director", tier=3)],
        skip_level=[],
        total=1,
    ))
    engine.get_chain_of_command = AsyncMock(return_value=[
        Person(name="Bob Director", title="Director", tier=3),
        Person(name="Alice VP", title="VP", tier=2),
    ])
    engine.compare_org_charts = AsyncMock(return_value=OrgDiff(
        program="DCGS",
        date1="2025-01-01",
        date2="2025-06-01",
        new_members=["New Person"],
        departed=["Old Person"],
    ))
    engine.get_cached = MagicMock(return_value=None)
    engine.list_cached = MagicMock(return_value=[
        {"chart_id": "test_chart_001", "title": "Test Org", "generated_at": "2025-01-01"},
    ])
    engine.clear_cache = MagicMock(return_value=True)
    return engine


@pytest.fixture
def mock_renderer():
    renderer = AsyncMock()
    renderer.render = AsyncMock(return_value="<html><svg></svg></html>")
    return renderer


@pytest.fixture
def mock_exporter():
    exporter = AsyncMock()
    exporter.to_json = AsyncMock(return_value=asdict(SAMPLE_CHART))
    exporter.to_mermaid = AsyncMock(return_value='graph TD\n    Alice_VP["Alice VP<br/>VP"]\n    Bob_Director["Bob Director<br/>Director"]\n    Alice_VP --> Bob_Director')
    exporter.to_svg = AsyncMock(return_value=b'<svg>test</svg>')
    return exporter


# ---------------------------------------------------------------------------
# TestGenerate
# ---------------------------------------------------------------------------


class TestGenerate:
    def test_generate(self, client, mock_engine):
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=mock_engine):
            resp = client.post("/org-chart/generate", json={
                "mode": "tree",
                "program": "DCGS",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["chart_id"] == "test_chart_001"
        assert data["mode"] == "tree"
        assert len(data["nodes"]) == 2

    def test_generate_unavailable(self, client):
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=None):
            resp = client.post("/org-chart/generate", json={"mode": "tree"})
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# TestListPrograms
# ---------------------------------------------------------------------------


class TestListPrograms:
    def test_list_programs(self, client, mock_engine):
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=mock_engine):
            resp = client.get("/org-chart/programs")
        assert resp.status_code == 200
        data = resp.json()
        assert "programs" in data
        assert "DCGS" in data["programs"]
        assert "ISR" in data["programs"]
        assert data["total"] == 2


# ---------------------------------------------------------------------------
# TestInfer
# ---------------------------------------------------------------------------


class TestInfer:
    def test_infer(self, client, mock_engine):
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=mock_engine):
            resp = client.post("/org-chart/infer-reports-to", json={"program": "DCGS"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["relationships_inferred"] == 5
        assert data["by_tier_hierarchy"] == 3
        assert data["confidence_avg"] == 0.7


# ---------------------------------------------------------------------------
# TestGetTeam
# ---------------------------------------------------------------------------


class TestGetTeam:
    def test_get_team(self, client, mock_engine):
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=mock_engine):
            resp = client.get("/org-chart/team/Alice%20VP")
        assert resp.status_code == 200
        data = resp.json()
        assert data["leader"]["name"] == "Alice VP"
        assert data["total"] == 1


# ---------------------------------------------------------------------------
# TestGetChain
# ---------------------------------------------------------------------------


class TestGetChain:
    def test_get_chain(self, client, mock_engine):
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=mock_engine):
            resp = client.get("/org-chart/chain/Bob%20Director")
        assert resp.status_code == 200
        data = resp.json()
        assert data["person"] == "Bob Director"
        assert data["hops"] == 2
        assert len(data["chain"]) == 2


# ---------------------------------------------------------------------------
# TestCompare
# ---------------------------------------------------------------------------


class TestCompare:
    def test_compare(self, client, mock_engine):
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=mock_engine):
            resp = client.post("/org-chart/compare", json={
                "date1": "2025-01-01",
                "date2": "2025-06-01",
                "program": "DCGS",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["program"] == "DCGS"
        assert "new_members" in data
        assert "departed" in data


# ---------------------------------------------------------------------------
# TestExport
# ---------------------------------------------------------------------------


class TestExport:
    def test_export_json(self, client, mock_engine, mock_exporter):
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=mock_engine):
            with patch("Engine8_Knowledge.api_routers.org_chart_api._get_exporter", return_value=mock_exporter):
                resp = client.post("/org-chart/export/json", json={
                    "program": "DCGS",
                })
        assert resp.status_code == 200
        data = resp.json()
        assert data["chart_id"] == "test_chart_001"

    def test_export_mermaid(self, client, mock_engine, mock_exporter):
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=mock_engine):
            with patch("Engine8_Knowledge.api_routers.org_chart_api._get_exporter", return_value=mock_exporter):
                resp = client.post("/org-chart/export/mermaid", json={
                    "program": "DCGS",
                })
        assert resp.status_code == 200
        data = resp.json()
        assert "mermaid" in data
        assert "graph TD" in data["mermaid"]

    def test_export_unavailable(self, client):
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=None):
            with patch("Engine8_Knowledge.api_routers.org_chart_api._get_exporter", return_value=None):
                resp = client.post("/org-chart/export/json", json={})
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# TestCacheList
# ---------------------------------------------------------------------------


class TestCache:
    def test_cache_list(self, client, mock_engine):
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=mock_engine):
            resp = client.get("/org-chart/cache")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["charts"][0]["chart_id"] == "test_chart_001"

    def test_cache_delete(self, client, mock_engine):
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=mock_engine):
            resp = client.delete("/org-chart/cache/test_chart_001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] is True

    def test_cache_delete_not_found(self, client, mock_engine):
        mock_engine.clear_cache = MagicMock(return_value=False)
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=mock_engine):
            resp = client.delete("/org-chart/cache/nonexistent")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TestStats
# ---------------------------------------------------------------------------


class TestStats:
    def test_stats(self, client, mock_engine):
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=mock_engine):
            resp = client.get("/org-chart/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cached_charts"] == 1
        assert "tree" in data["renderer_modes"]
        assert "svg" in data["export_formats"]
        assert "mermaid" in data["export_formats"]

    def test_stats_no_engine(self, client):
        with patch("Engine8_Knowledge.api_routers.org_chart_api._get_engine", return_value=None):
            resp = client.get("/org-chart/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cached_charts"] == 0
