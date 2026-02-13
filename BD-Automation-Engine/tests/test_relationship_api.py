"""Tests for Phase 34A — Relationship Intelligence API (14 endpoints)."""

import pytest

from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.relationship_api import router


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def app():
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# RELATIONSHIP STRENGTH ENDPOINTS
# =========================================

class TestRelationshipStrengthEndpoints:
    def test_score_relationship(self, client):
        resp = client.get("/relationships/score/contact-a/contact-b")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_score" in data
        assert "dimensions" in data
        assert 0 <= data["total_score"] <= 100

    def test_get_contact_relationships(self, client):
        resp = client.get("/relationships/scores/contact-a")
        assert resp.status_code == 200
        data = resp.json()
        assert "relationships" in data
        assert "total" in data

    def test_decaying_relationships(self, client):
        resp = client.get("/relationships/decaying")
        assert resp.status_code == 200
        data = resp.json()
        assert "decaying" in data
        assert "total" in data


# =========================================
# INFLUENCE ENDPOINTS
# =========================================

class TestInfluenceEndpoints:
    def test_global_influence(self, client):
        resp = client.get("/relationships/influence/global")
        assert resp.status_code == 200
        data = resp.json()
        assert "rankings" in data
        assert "total" in data

    def test_program_influence(self, client):
        resp = client.get("/relationships/influence/program/DCGS")
        assert resp.status_code == 200
        data = resp.json()
        assert data["program"] == "DCGS"

    def test_influence_trend(self, client):
        resp = client.get("/relationships/influence/contact-1/trend")
        assert resp.status_code == 200
        data = resp.json()
        assert "trend" in data
        assert data["trend"] in ("increasing", "decreasing", "stable")


# =========================================
# PATH ENDPOINTS
# =========================================

class TestPathEndpoints:
    def test_optimal_path(self, client):
        resp = client.get("/relationships/path/from-id/to-id")
        assert resp.status_code == 200
        data = resp.json()
        assert "paths" in data
        assert "total" in data

    def test_warm_intro(self, client):
        resp = client.get("/relationships/warm-intro/target-contact")
        assert resp.status_code == 200
        data = resp.json()
        assert "chains" in data
        assert "total" in data

    def test_missing_links(self, client):
        resp = client.get("/relationships/missing-links/DCGS")
        assert resp.status_code == 200
        data = resp.json()
        assert "missing_links" in data


# =========================================
# NETWORK ENDPOINTS
# =========================================

class TestNetworkEndpoints:
    def test_communities(self, client):
        resp = client.get("/relationships/communities")
        assert resp.status_code == 200
        data = resp.json()
        assert "communities" in data
        assert "total" in data

    def test_bridges(self, client):
        resp = client.get("/relationships/bridges")
        assert resp.status_code == 200
        data = resp.json()
        assert "bridges" in data

    def test_network_density(self, client):
        resp = client.get("/relationships/network-density")
        assert resp.status_code == 200
        data = resp.json()
        assert "density" in data
        assert "assessment" in data

    def test_network_growth(self, client):
        resp = client.get("/relationships/network-growth")
        assert resp.status_code == 200
        data = resp.json()
        assert "assessment" in data
        assert "net_growth" in data


# =========================================
# RECOMPUTE ENDPOINT
# =========================================

class TestRecomputeEndpoint:
    def test_recompute(self, client):
        resp = client.post("/relationships/recompute", json={"scope": "all"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "recomputed"


# =========================================
# ENDPOINT COUNT
# =========================================

class TestEndpointCount:
    def test_fourteen_endpoints(self, app):
        rel_routes = [
            r for r in app.routes
            if hasattr(r, "path") and r.path.startswith("/relationships")
        ]
        assert len(rel_routes) == 14
