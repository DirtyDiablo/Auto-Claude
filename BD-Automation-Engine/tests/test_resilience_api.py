"""Tests for Phase 54A — Resilience API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.resilience.circuit_breaker as cb_mod
import src.resilience.chaos_engine as chaos_mod
import src.resilience.bulkhead as bh_mod
from src.api.resilience_api import include_resilience_router


@pytest.fixture(autouse=True)
def _reset_singletons():
    cb_mod._instance = None
    chaos_mod._instance = None
    bh_mod._bulkhead_instance = None
    bh_mod._degradation_instance = None
    yield
    cb_mod._instance = None
    chaos_mod._instance = None
    bh_mod._bulkhead_instance = None
    bh_mod._degradation_instance = None


@pytest.fixture
def app():
    app = FastAPI()
    include_resilience_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# CIRCUIT BREAKERS
# =========================================

def test_list_breakers(client):
    resp = client.get("/api/resilience/breakers")
    assert resp.status_code == 200
    assert resp.json()["total"] == 6


def test_get_breaker(client):
    resp = client.get("/api/resilience/breakers/qdrant_search")
    assert resp.status_code == 200
    assert resp.json()["name"] == "qdrant_search"


def test_get_breaker_not_found(client):
    resp = client.get("/api/resilience/breakers/fake")
    assert resp.status_code == 404


def test_trip_breaker(client):
    resp = client.post("/api/resilience/breakers/qdrant_search/trip")
    assert resp.status_code == 200
    assert resp.json()["tripped"] is True


def test_reset_breaker(client):
    client.post("/api/resilience/breakers/qdrant_search/trip")
    resp = client.post("/api/resilience/breakers/qdrant_search/reset")
    assert resp.status_code == 200
    assert resp.json()["reset"] is True


# =========================================
# CHAOS EXPERIMENTS
# =========================================

def test_create_experiment(client):
    resp = client.post("/api/resilience/chaos/experiments", json={
        "name": "test_latency",
        "fault_type": "latency",
        "target_service": "qdrant_search",
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "test_latency"


def test_list_experiments(client):
    client.post("/api/resilience/chaos/experiments", json={
        "name": "e1", "fault_type": "latency", "target_service": "qdrant_search",
    })
    resp = client.get("/api/resilience/chaos/experiments")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_run_experiment(client):
    create = client.post("/api/resilience/chaos/experiments", json={
        "name": "run_test", "fault_type": "latency", "target_service": "qdrant_search",
    })
    exp_id = create.json()["experiment_id"]
    resp = client.post(f"/api/resilience/chaos/experiments/{exp_id}/run")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_run_not_found(client):
    resp = client.post("/api/resilience/chaos/experiments/chaos_fake/run")
    assert resp.status_code == 404


def test_list_templates(client):
    resp = client.get("/api/resilience/chaos/templates")
    assert resp.status_code == 200
    assert resp.json()["total"] == 5


# =========================================
# BULKHEADS & DEGRADATION
# =========================================

def test_list_bulkheads(client):
    resp = client.get("/api/resilience/bulkheads")
    assert resp.status_code == 200
    assert resp.json()["total"] == 5


def test_get_degradation(client):
    resp = client.get("/api/resilience/degradation")
    assert resp.status_code == 200
    assert resp.json()["level"] == "normal"


def test_set_degradation(client):
    resp = client.post("/api/resilience/degradation", json={"level": "degraded"})
    assert resp.status_code == 200
    assert resp.json()["level"] == "degraded"


# =========================================
# HEALTH
# =========================================

def test_health(client):
    resp = client.get("/api/resilience/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "circuit_breakers" in data
    assert "chaos" in data
    assert "bulkheads" in data
