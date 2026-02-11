"""Tests for Phase 55A — Experimentation API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.experimentation.feature_flags as ff_mod
import src.experimentation.ab_testing as ab_mod
import src.experimentation.experiment_analytics as ea_mod
from src.api.experimentation_api import include_experimentation_router


@pytest.fixture(autouse=True)
def _reset_singletons():
    ff_mod._instance = None
    ab_mod._instance = None
    ea_mod._instance = None
    yield
    ff_mod._instance = None
    ab_mod._instance = None
    ea_mod._instance = None


@pytest.fixture
def app():
    app = FastAPI()
    include_experimentation_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# FEATURE FLAGS
# =========================================

def test_list_flags(client):
    resp = client.get("/api/experimentation/flags")
    assert resp.status_code == 200
    assert resp.json()["total"] == 8


def test_get_flag(client):
    resp = client.get("/api/experimentation/flags")
    flag_id = resp.json()["flags"][0]["flag_id"]
    resp = client.get(f"/api/experimentation/flags/{flag_id}")
    assert resp.status_code == 200


def test_get_flag_not_found(client):
    resp = client.get("/api/experimentation/flags/flag_fake")
    assert resp.status_code == 404


def test_evaluate_flag(client):
    resp = client.get("/api/experimentation/flags")
    flag_id = resp.json()["flags"][0]["flag_id"]
    resp = client.get(f"/api/experimentation/flags/{flag_id}/evaluate?user_id=user1")
    assert resp.status_code == 200
    assert "enabled" in resp.json()


def test_update_flag(client):
    resp = client.get("/api/experimentation/flags")
    flag_id = resp.json()["flags"][0]["flag_id"]
    resp = client.patch(f"/api/experimentation/flags/{flag_id}", json={
        "description": "Updated via API",
    })
    assert resp.status_code == 200
    assert resp.json()["description"] == "Updated via API"


# =========================================
# A/B TESTING
# =========================================

def test_create_experiment(client):
    resp = client.post("/api/experimentation/experiments", json={
        "name": "api_test",
        "hypothesis": "Test hypothesis",
        "metric_name": "ctr",
        "variants": [
            {"name": "control", "weight": 50},
            {"name": "treatment", "weight": 50},
        ],
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "api_test"


def test_list_experiments(client):
    client.post("/api/experimentation/experiments", json={
        "name": "e1", "variants": [
            {"name": "A", "weight": 50}, {"name": "B", "weight": 50},
        ],
    })
    resp = client.get("/api/experimentation/experiments")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_get_results_not_found(client):
    resp = client.get("/api/experimentation/experiments/exp_fake/results")
    assert resp.status_code == 404


# =========================================
# ANALYTICS
# =========================================

def test_track_event(client):
    resp = client.post("/api/experimentation/analytics/track", json={
        "experiment_id": "exp1",
        "variant_id": "var_a",
        "user_id": "user1",
        "event_type": "view",
    })
    assert resp.status_code == 200
    assert resp.json()["event_type"] == "view"


def test_get_funnel(client):
    for i in range(10):
        client.post("/api/experimentation/analytics/track", json={
            "experiment_id": "exp1", "variant_id": "var_a",
            "user_id": f"user_{i}", "event_type": "view",
        })
    resp = client.get("/api/experimentation/analytics/exp1/funnel")
    assert resp.status_code == 200
    assert "funnel" in resp.json()


def test_sample_size(client):
    resp = client.post("/api/experimentation/analytics/sample-size", json={
        "baseline_rate": 0.10,
        "min_detectable_effect": 0.02,
    })
    assert resp.status_code == 200
    assert resp.json()["sample_size_per_variant"] > 0


# =========================================
# HEALTH
# =========================================

def test_health(client):
    resp = client.get("/api/experimentation/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "flags" in data
    assert "ab_testing" in data
    assert "analytics" in data
