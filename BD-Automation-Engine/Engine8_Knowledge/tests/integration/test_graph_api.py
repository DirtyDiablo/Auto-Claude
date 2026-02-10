"""
Phase 21A — Graph API Router Tests

Tests the 17 FastAPI endpoints in neo4j_routes.py.
Uses TestClient with mocked dependencies — no Neo4j required.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from Engine8_Knowledge.graph.neo4j_routes import router


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
def mock_neo4j_mgr():
    mgr = MagicMock()
    mgr.health_check.return_value = {"status": "healthy", "uri": "bolt://localhost:7687"}
    mgr.run_query.return_value = []
    mgr.run_single.return_value = None
    mgr.get_node_count.return_value = 0
    mgr.get_relationship_count.return_value = 0
    mgr.write_query.return_value = {
        "nodes_created": 0, "nodes_deleted": 0,
        "relationships_created": 0, "relationships_deleted": 0,
        "properties_set": 0,
    }
    return mgr


@pytest.fixture
def mock_graph_queries():
    gq = MagicMock()
    gq.find_contacts_by_program.return_value = []
    gq.find_shortest_path.return_value = {"from": "A", "to": "B", "path": [], "found": False}
    gq.find_introduction_path.return_value = []
    gq.get_program_org_chart.return_value = {"program": "test", "managers": [], "team": []}
    gq.get_company_network.return_value = {"company": "test", "programs": [], "people": [], "subs": []}
    gq.get_contact_360.return_value = {"name": "test", "found": False}
    gq.find_hiring_signals.return_value = []
    gq.find_competitive_overlap.return_value = {"company_a": "A", "company_b": "B", "overlap_programs": [], "overlap_count": 0}
    gq.get_location_intel.return_value = {"location": "test", "programs": [], "people": [], "jobs": []}
    gq.find_orphan_contacts.return_value = []
    gq.get_graph_stats.return_value = {"total_nodes": 0, "total_relationships": 0}
    return gq


# ---------------------------------------------------------------------------
# TestHealthEndpoints
# ---------------------------------------------------------------------------

class TestHealthEndpoints:
    """Test health and stats endpoints."""

    def test_health(self, client, mock_neo4j_mgr):
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_neo4j_manager", return_value=mock_neo4j_mgr):
            resp = client.get("/neo4j/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_stats(self, client, mock_graph_queries):
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_graph_queries", return_value=mock_graph_queries):
            resp = client.get("/neo4j/stats")
        assert resp.status_code == 200
        assert "total_nodes" in resp.json()

    def test_schema(self, client, mock_neo4j_mgr):
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_neo4j_manager", return_value=mock_neo4j_mgr), \
             patch("Engine8_Knowledge.graph.neo4j_routes.get_schema_info", return_value={"node_types": [], "constraints": []}):
            resp = client.get("/neo4j/schema")
        assert resp.status_code == 200

    def test_apply_schema(self, client, mock_neo4j_mgr):
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_neo4j_manager", return_value=mock_neo4j_mgr), \
             patch("Engine8_Knowledge.graph.neo4j_routes.apply_schema", return_value={"constraints": [], "indexes": [], "errors": []}):
            resp = client.post("/neo4j/schema/apply")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# TestQueryEndpoints
# ---------------------------------------------------------------------------

class TestQueryEndpoints:
    """Test Cypher query endpoints."""

    def test_contacts_by_program(self, client, mock_graph_queries):
        mock_graph_queries.find_contacts_by_program.return_value = [
            {"name": "Alice", "title": "PM"},
        ]
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_graph_queries", return_value=mock_graph_queries):
            resp = client.get("/neo4j/contacts/DCGS")
        assert resp.status_code == 200
        data = resp.json()
        assert data["program"] == "DCGS"
        assert data["count"] == 1

    def test_shortest_path(self, client, mock_graph_queries):
        mock_graph_queries.find_shortest_path.return_value = {
            "from": "Alice", "to": "Bob", "path": [], "found": False, "hops": 0,
        }
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_graph_queries", return_value=mock_graph_queries):
            resp = client.get("/neo4j/path/Alice/Bob")
        assert resp.status_code == 200
        assert resp.json()["from"] == "Alice"

    def test_introduction_path(self, client, mock_graph_queries):
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_graph_queries", return_value=mock_graph_queries):
            resp = client.get("/neo4j/introduction/TargetPerson")
        assert resp.status_code == 200
        assert resp.json()["target"] == "TargetPerson"

    def test_org_chart(self, client, mock_graph_queries):
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_graph_queries", return_value=mock_graph_queries):
            resp = client.get("/neo4j/org-chart/DCGS")
        assert resp.status_code == 200

    def test_company_network(self, client, mock_graph_queries):
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_graph_queries", return_value=mock_graph_queries):
            resp = client.get("/neo4j/company/Leidos")
        assert resp.status_code == 200

    def test_contact_360(self, client, mock_graph_queries):
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_graph_queries", return_value=mock_graph_queries):
            resp = client.get("/neo4j/contact/Alice/360")
        assert resp.status_code == 200

    def test_hiring_signals(self, client, mock_graph_queries):
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_graph_queries", return_value=mock_graph_queries):
            resp = client.get("/neo4j/hiring-signals?days=30")
        assert resp.status_code == 200
        assert "signals" in resp.json()

    def test_competitive_overlap(self, client, mock_graph_queries):
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_graph_queries", return_value=mock_graph_queries):
            resp = client.get("/neo4j/competitive/Leidos/SAIC")
        assert resp.status_code == 200

    def test_location_intel(self, client, mock_graph_queries):
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_graph_queries", return_value=mock_graph_queries):
            resp = client.get("/neo4j/location/FortMeade")
        assert resp.status_code == 200

    def test_orphan_contacts(self, client, mock_graph_queries):
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_graph_queries", return_value=mock_graph_queries):
            resp = client.get("/neo4j/orphans")
        assert resp.status_code == 200
        assert "orphans" in resp.json()


# ---------------------------------------------------------------------------
# TestIngestionEndpoints
# ---------------------------------------------------------------------------

class TestIngestionEndpoints:
    """Test ingestion trigger endpoints."""

    def _mock_engine(self):
        engine = MagicMock()
        engine.ingest_contacts.return_value = {"status": "completed", "ingested": 100}
        engine.ingest_programs.return_value = {"status": "completed", "ingested": 50}
        engine.ingest_jobs.return_value = {"status": "completed", "ingested": 20}
        engine.ingest_interactions.return_value = {"status": "completed", "ingested": 200}
        engine.ingest_locations.return_value = {"status": "completed", "ingested": 30}
        engine.ingest_all.return_value = {"status": "completed", "elapsed_sec": 5.0}
        return engine

    def test_ingest_contacts(self, client, mock_neo4j_mgr):
        engine = self._mock_engine()
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_neo4j_manager", return_value=mock_neo4j_mgr), \
             patch("Engine8_Knowledge.graph.neo4j_routes.GraphIngestionEngine", return_value=engine):
            resp = client.post("/neo4j/ingest/contacts", json={})
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_ingest_programs(self, client, mock_neo4j_mgr):
        engine = self._mock_engine()
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_neo4j_manager", return_value=mock_neo4j_mgr), \
             patch("Engine8_Knowledge.graph.neo4j_routes.GraphIngestionEngine", return_value=engine):
            resp = client.post("/neo4j/ingest/programs", json={})
        assert resp.status_code == 200

    def test_ingest_jobs(self, client, mock_neo4j_mgr):
        engine = self._mock_engine()
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_neo4j_manager", return_value=mock_neo4j_mgr), \
             patch("Engine8_Knowledge.graph.neo4j_routes.GraphIngestionEngine", return_value=engine):
            resp = client.post("/neo4j/ingest/jobs", json={})
        assert resp.status_code == 200

    def test_ingest_interactions(self, client, mock_neo4j_mgr):
        engine = self._mock_engine()
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_neo4j_manager", return_value=mock_neo4j_mgr), \
             patch("Engine8_Knowledge.graph.neo4j_routes.GraphIngestionEngine", return_value=engine):
            resp = client.post("/neo4j/ingest/interactions", json={})
        assert resp.status_code == 200

    def test_ingest_locations(self, client, mock_neo4j_mgr):
        engine = self._mock_engine()
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_neo4j_manager", return_value=mock_neo4j_mgr), \
             patch("Engine8_Knowledge.graph.neo4j_routes.GraphIngestionEngine", return_value=engine):
            resp = client.post("/neo4j/ingest/locations")
        assert resp.status_code == 200

    def test_ingest_all(self, client, mock_neo4j_mgr):
        engine = self._mock_engine()
        with patch("Engine8_Knowledge.graph.neo4j_routes.get_neo4j_manager", return_value=mock_neo4j_mgr), \
             patch("Engine8_Knowledge.graph.neo4j_routes.GraphIngestionEngine", return_value=engine):
            resp = client.post("/neo4j/ingest/all", json={})
        assert resp.status_code == 200
