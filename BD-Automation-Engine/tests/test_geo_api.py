"""Tests for Phase 48A — Geographic Intelligence API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.geographic.geocoding_engine as ge_mod
import src.geographic.spatial_queries as sq_mod
from src.api.geo_api import include_geo_router


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset singletons so each test starts fresh."""
    ge_mod._instance = None
    sq_mod._instance = None
    yield
    ge_mod._instance = None
    sq_mod._instance = None


@pytest.fixture
def app():
    app = FastAPI()
    include_geo_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# GEOCODE
# =========================================

def test_geocode(client):
    resp = client.post("/api/geo/geocode", json={"location": "Pentagon"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["resolved"] is True
    assert data["geo"]["name"] == "Pentagon"


def test_geocode_alias(client):
    resp = client.post("/api/geo/geocode", json={"location": "DGS-1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["resolved"] is True


def test_geocode_not_found(client):
    resp = client.post("/api/geo/geocode", json={"location": "Mars Colony"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["resolved"] is False


# =========================================
# BATCH GEOCODE
# =========================================

def test_batch_geocode_all(client):
    resp = client.post("/api/geo/geocode/batch", json={"entity_type": "all"})
    assert resp.status_code == 200
    data = resp.json()
    assert "contacts" in data
    assert "programs" in data
    assert "jobs" in data
    assert data["contacts"]["total"] > 0


def test_batch_geocode_contacts(client):
    resp = client.post("/api/geo/geocode/batch", json={"entity_type": "contact"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 10
    assert data["resolved"] >= 8


def test_batch_geocode_jobs(client):
    resp = client.post("/api/geo/geocode/batch", json={"entity_type": "job"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 10


# =========================================
# RADIUS
# =========================================

def test_radius(client):
    resp = client.post("/api/geo/radius", json={
        "lat": 38.8719, "lng": -77.0563, "radius_miles": 15.0,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 3
    assert data["radius_miles"] == 15.0


def test_radius_with_entity_filter(client):
    resp = client.post("/api/geo/radius", json={
        "lat": 38.8719, "lng": -77.0563, "radius_miles": 30.0,
        "entity_types": ["facility"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert all(e["entity_type"] == "facility" for e in data["entities"])


# =========================================
# CLUSTERS
# =========================================

def test_clusters_contacts(client):
    resp = client.get("/api/geo/clusters/contact")
    assert resp.status_code == 200
    data = resp.json()
    assert data["entity_type"] == "contact"
    assert data["total_clusters"] >= 2


def test_clusters_facilities(client):
    resp = client.get("/api/geo/clusters/facility")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_clusters"] >= 4


def test_clusters_invalid_type(client):
    resp = client.get("/api/geo/clusters/invalid")
    assert resp.status_code == 400


# =========================================
# OVERLAP
# =========================================

def test_overlap(client):
    resp = client.post("/api/geo/overlap", json={
        "program_a": "DCGS-A", "program_b": "JADC2",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["program_a"] == "DCGS-A"
    assert data["program_b"] == "JADC2"
    assert "overlap_score" in data


# =========================================
# COMMUTE
# =========================================

def test_commute(client):
    resp = client.post("/api/geo/commute", json={
        "lat": 37.0833, "lng": -76.3605, "max_commute_miles": 15.0,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


# =========================================
# COMPETITIVE DENSITY
# =========================================

def test_competitive_density(client):
    resp = client.get("/api/geo/competitive-density/NCR")
    assert resp.status_code == 200
    data = resp.json()
    assert data["region"] == "NCR"
    assert len(data["competitors"]) >= 1


# =========================================
# HEATMAP
# =========================================

def test_heatmap_contacts(client):
    resp = client.get("/api/geo/heatmap/contact")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 8
    assert all("lat" in p and "lng" in p for p in data["points"])


def test_heatmap_facilities(client):
    resp = client.get("/api/geo/heatmap/facility")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 50


def test_heatmap_invalid_type(client):
    resp = client.get("/api/geo/heatmap/invalid")
    assert resp.status_code == 400


# =========================================
# FACILITIES
# =========================================

def test_facilities_all(client):
    resp = client.get("/api/geo/facilities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 50


def test_facilities_filter_region(client):
    resp = client.get("/api/geo/facilities?region=NCR")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 10
    assert all(f["region"] == "NCR" for f in data["facilities"])


def test_facilities_filter_type(client):
    resp = client.get("/api/geo/facilities?facility_type=base")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 20


# =========================================
# STATS
# =========================================

def test_stats(client):
    resp = client.get("/api/geo/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_facilities"] >= 50
    assert "by_region" in data
