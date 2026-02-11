"""Tests for Phase 51A — Simulation & Causal Intelligence API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.simulation.causal_engine as ce_mod
import src.simulation.digital_twin as dt_mod
import src.simulation.scenario_api as sa_mod
from src.api.simulation_api import include_simulation_router


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset singletons so each test starts fresh."""
    ce_mod._instance = None
    dt_mod._instance = None
    sa_mod._instance = None
    yield
    ce_mod._instance = None
    dt_mod._instance = None
    sa_mod._instance = None


@pytest.fixture
def app():
    app = FastAPI()
    include_simulation_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# CAUSAL GRAPH
# =========================================

def test_build_graph(client):
    resp = client.post("/api/causal/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_nodes"] >= 10
    assert data["total_edges"] >= 10


def test_get_graph(client):
    resp = client.get("/api/causal/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_nodes"] >= 10


# =========================================
# CAUSAL EFFECT
# =========================================

def test_estimate_effect(client):
    resp = client.post("/api/causal/effect", json={
        "treatment": "outreach_volume",
        "outcome": "contacts_engaged",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ate"] > 0
    assert data["ci_lower"] < data["ci_upper"]


def test_estimate_negative_effect(client):
    resp = client.post("/api/causal/effect", json={
        "treatment": "competitor_activity",
        "outcome": "contracts_won",
    })
    assert resp.status_code == 200
    assert resp.json()["ate"] < 0


# =========================================
# COUNTERFACTUAL
# =========================================

def test_counterfactual(client):
    resp = client.post("/api/causal/counterfactual", json={
        "scenario": "What if we doubled outreach?",
        "conditions": {"outreach_volume": 2.0},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "predicted_outcome" in data
    assert "key_drivers" in data


# =========================================
# DIGITAL TWIN
# =========================================

def test_create_twin(client):
    resp = client.post("/api/twin/create", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert "twin_id" in data
    assert data["team_size"] == 8


def test_simulate(client):
    twin = client.post("/api/twin/create", json={}).json()
    resp = client.post("/api/twin/simulate", json={
        "twin_id": twin["twin_id"],
        "days": 90,
        "monte_carlo_runs": 100,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["expected_pipeline_value_m"] > 0
    assert data["days_simulated"] == 90


def test_simulate_with_interventions(client):
    twin = client.post("/api/twin/create", json={}).json()
    resp = client.post("/api/twin/simulate", json={
        "twin_id": twin["twin_id"],
        "days": 90,
        "interventions": [
            {"variable": "team_size", "action": "increase", "value": 3},
        ],
        "monte_carlo_runs": 100,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["interventions"]) == 1


def test_simulate_unknown_twin(client):
    resp = client.post("/api/twin/simulate", json={
        "twin_id": "twin_fake",
        "days": 90,
    })
    assert resp.status_code == 404


# =========================================
# SCENARIO COMPARISON
# =========================================

def test_compare(client):
    twin = client.post("/api/twin/create", json={}).json()
    resp = client.post("/api/twin/compare", json={
        "twin_id": twin["twin_id"],
        "scenarios": [
            {"name": "Status Quo", "interventions": []},
            {"name": "Hire 2", "interventions": [
                {"variable": "team_size", "action": "increase", "value": 2}
            ]},
        ],
        "monte_carlo_runs": 50,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_scenarios"] == 2
    assert data["winner"] is not None


# =========================================
# CALIBRATION
# =========================================

def test_calibrate(client):
    twin = client.post("/api/twin/create", json={}).json()
    resp = client.post("/api/twin/calibrate", json={
        "twin_id": twin["twin_id"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_accuracy"] > 0


def test_get_calibration(client):
    twin = client.post("/api/twin/create", json={}).json()
    client.post("/api/twin/calibrate", json={"twin_id": twin["twin_id"]})
    resp = client.get(f"/api/twin/calibration?twin_id={twin['twin_id']}")
    assert resp.status_code == 200


def test_get_calibration_not_found(client):
    resp = client.get("/api/twin/calibration?twin_id=twin_fake")
    assert resp.status_code == 404


# =========================================
# SCENARIO ANALYSIS
# =========================================

def test_analyze_scenario(client):
    resp = client.post("/api/scenario/analyze", json={
        "question": "What if we hire 2 more BD reps?",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["method"] == "simulation"
    assert len(data["result_summary"]) > 10


def test_sensitivity(client):
    resp = client.post("/api/scenario/sensitivity", json={
        "variable": "team_size",
        "range_pct": 30.0,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["variable"] == "team_size"
    assert len(data["sweep_points"]) >= 10


# =========================================
# PRESETS
# =========================================

def test_presets(client):
    resp = client.get("/api/scenario/presets")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 8


def test_presets_filter(client):
    resp = client.get("/api/scenario/presets?category=team")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


# =========================================
# SIMULATION HISTORY
# =========================================

def test_simulation_history(client):
    twin = client.post("/api/twin/create", json={}).json()
    client.post("/api/twin/simulate", json={
        "twin_id": twin["twin_id"], "monte_carlo_runs": 50,
    })
    resp = client.get("/api/simulation/history")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


# =========================================
# HEALTH
# =========================================

def test_health(client):
    resp = client.get("/api/simulation/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "causal" in data
    assert "twin" in data
    assert "scenario" in data
