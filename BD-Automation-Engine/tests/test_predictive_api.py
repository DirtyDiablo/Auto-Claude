"""Tests for Phase 32A — Predictive Intelligence API (14 endpoints)."""

import pytest

from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.predictive_api import router


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def app():
    """Create test app with predictive router."""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def sample_opportunity():
    return {
        "id": "opp-test-1",
        "title": "Sr Intelligence Analyst",
        "company": "Leidos",
        "program": "AF DCGS",
        "contact_tier": 2,
        "relationship_depth": 8,
        "days_since_last_contact": 5,
        "mutual_connections": 3,
        "contact_response_rate": 0.7,
        "pts_involvement": 3,
        "program_value_log": 8.5,
        "days_to_pop_end": 180,
        "past_placements_on_program": 2,
        "competitor_density": 2,
        "clearance_match": 1,
        "role_match_score": 0.9,
        "location_familiarity": 0.8,
        "days_job_open": 10,
        "salary_competitiveness": 1.1,
        "fiscal_quarter": 3,
        "days_to_fy_end": 90,
        "is_option_year": 0,
        "seasonal_hiring_index": 1.2,
        "outreach_attempts": 3,
        "channels_used": 2,
        "similar_opp_win_rate": 0.4,
        "estimated_value": 500000,
        "location": "Hickam AFB",
        "description": "ISR analyst position",
    }


# =========================================
# WIN PROBABILITY ENDPOINTS
# =========================================


class TestWinProbabilityEndpoints:
    def test_predict_single(self, client, sample_opportunity):
        resp = client.post("/predict/win-probability", json=sample_opportunity)
        assert resp.status_code == 200
        data = resp.json()
        assert "win_probability" in data
        assert "confidence" in data
        assert "top_factors" in data
        assert 0 <= data["win_probability"] <= 1

    def test_predict_defaults(self, client):
        resp = client.post("/predict/win-probability", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert "win_probability" in data

    def test_predict_batch(self, client, sample_opportunity):
        resp = client.post(
            "/predict/win-probability/batch",
            json={"opportunities": [sample_opportunity, sample_opportunity]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "predictions" in data
        assert data["total"] == 2

    def test_predict_batch_empty(self, client):
        resp = client.post(
            "/predict/win-probability/batch",
            json={"opportunities": []},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# =========================================
# PIPELINE ENDPOINTS
# =========================================


class TestPipelineEndpoints:
    def test_pipeline_ranked(self, client):
        resp = client.get("/predict/pipeline/ranked")
        assert resp.status_code == 200
        data = resp.json()
        assert "pipeline" in data
        assert "total" in data
        assert isinstance(data["pipeline"], list)

    def test_pipeline_ranked_with_limit(self, client):
        resp = client.get("/predict/pipeline/ranked?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] <= 2

    def test_pipeline_review(self, client):
        resp = client.get("/predict/pipeline/review")
        assert resp.status_code == 200
        data = resp.json()
        assert "review_date" in data
        assert "top_opportunities" in data
        assert "focus_areas" in data

    def test_what_if(self, client, sample_opportunity):
        resp = client.post(
            "/predict/what-if",
            json={
                "opportunity": sample_opportunity,
                "changes": {"contact_tier": 1, "relationship_depth": 10},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "original_score" in data
        assert "modified_score" in data
        assert "score_delta" in data


# =========================================
# FORECAST ENDPOINTS
# =========================================


class TestForecastEndpoints:
    def test_forecast_program(self, client):
        resp = client.get("/predict/forecast/program/AF%20DCGS")
        assert resp.status_code == 200
        data = resp.json()
        assert "program" in data
        assert "trend" in data
        assert "confidence" in data

    def test_forecast_location(self, client):
        resp = client.get("/predict/forecast/location/San%20Diego")
        assert resp.status_code == 200
        data = resp.json()
        assert "location" in data
        assert "trend" in data

    def test_forecast_roles(self, client):
        resp = client.get("/predict/forecast/roles?role=analyst")
        assert resp.status_code == 200
        data = resp.json()
        assert "role" in data
        assert "current_demand" in data

    def test_ramp_signals(self, client):
        resp = client.get("/predict/ramp-signals")
        assert resp.status_code == 200
        data = resp.json()
        assert "signals" in data
        assert "total" in data

    def test_timing(self, client):
        resp = client.get("/predict/timing/AF%20DCGS")
        assert resp.status_code == 200
        data = resp.json()
        assert "program" in data
        assert "best_window" in data


# =========================================
# BUDGET ENDPOINTS
# =========================================


class TestBudgetEndpoints:
    def test_budget_calendar(self, client):
        resp = client.get("/predict/budget-calendar")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data
        assert "fiscal_year" in data
        assert "total_events" in data

    def test_budget_calendar_months(self, client):
        resp = client.get("/predict/budget-calendar?months=6")
        assert resp.status_code == 200

    def test_recompete(self, client):
        resp = client.get("/predict/recompete/test-contract")
        assert resp.status_code == 200
        data = resp.json()
        assert "contract_id" in data
        assert "recompete_probability" in data
        assert "recommended_actions" in data


# =========================================
# MODEL MANAGEMENT ENDPOINTS
# =========================================


class TestModelManagementEndpoints:
    def test_model_performance(self, client):
        resp = client.get("/predict/model-performance")
        assert resp.status_code == 200
        data = resp.json()
        assert "trained" in data
        assert "feature_count" in data

    def test_retrain(self, client):
        resp = client.post("/predict/retrain", json={"n_synthetic": 50})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("trained", "failed")
        assert "accuracy" in data
        assert "training_samples" in data


# =========================================
# ENDPOINT COUNT
# =========================================


class TestEndpointCount:
    def test_fourteen_endpoints(self, app):
        predict_routes = [
            r
            for r in app.routes
            if hasattr(r, "path") and r.path.startswith("/predict")
        ]
        assert len(predict_routes) == 14
