"""Tests for Phase 36A — Revenue API (16 endpoints)."""

import pytest

from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.revenue_api import router


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
# REVENUE ENDPOINTS
# =========================================

class TestRevenueEndpoints:
    def test_summary(self, client):
        resp = client.get("/revenue/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_revenue" in data
        assert "avg_margin_pct" in data

    def test_summary_with_period(self, client):
        resp = client.get("/revenue/summary?period=2025-01")
        assert resp.status_code == 200

    def test_by_program(self, client):
        resp = client.get("/revenue/by-program")
        assert resp.status_code == 200
        data = resp.json()
        assert "programs" in data
        assert "total_revenue" in data

    def test_by_rep(self, client):
        resp = client.get("/revenue/by-rep")
        assert resp.status_code == 200
        assert "reps" in resp.json()

    def test_by_contact(self, client):
        resp = client.get("/revenue/by-contact")
        assert resp.status_code == 200
        assert "contacts" in resp.json()

    def test_forecast(self, client):
        resp = client.get("/revenue/forecast?months=6")
        assert resp.status_code == 200
        data = resp.json()
        assert "forecast" in data
        assert data["months"] == 6

    def test_margins(self, client):
        resp = client.get("/revenue/margins")
        assert resp.status_code == 200
        assert "avg_margin_pct" in resp.json()

    def test_concentration(self, client):
        resp = client.get("/revenue/concentration")
        assert resp.status_code == 200
        data = resp.json()
        assert "risk_level" in data
        assert "diversification_score" in data


# =========================================
# DEAL LIFECYCLE ENDPOINTS
# =========================================

class TestDealEndpoints:
    def test_lifecycle(self, client):
        resp = client.get("/revenue/deals/lifecycle")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_deals" in data

    def test_velocity(self, client):
        resp = client.get("/revenue/deals/velocity")
        assert resp.status_code == 200
        data = resp.json()
        assert "stages" in data

    def test_stale(self, client):
        resp = client.get("/revenue/deals/stale")
        assert resp.status_code == 200
        assert "stale_deals" in resp.json()


# =========================================
# ROI ENDPOINTS
# =========================================

class TestROIEndpoints:
    def test_campaign_roi(self, client):
        resp = client.get("/revenue/roi/campaigns")
        assert resp.status_code == 200
        assert "campaigns" in resp.json()

    def test_contact_roi(self, client):
        resp = client.get("/revenue/roi/contacts")
        assert resp.status_code == 200
        assert "contacts" in resp.json()

    def test_program_roi(self, client):
        resp = client.get("/revenue/roi/programs")
        assert resp.status_code == 200
        assert "programs" in resp.json()

    def test_channel_roi(self, client):
        resp = client.get("/revenue/roi/channels")
        assert resp.status_code == 200
        assert "channels" in resp.json()


# =========================================
# EXECUTIVE SUMMARY ENDPOINT
# =========================================

class TestExecutiveSummaryEndpoint:
    def test_executive_summary(self, client):
        resp = client.get("/revenue/executive-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "narrative" in data
        assert "period" in data


# =========================================
# PLACEMENT RECORDING
# =========================================

class TestPlacementEndpoint:
    def test_record_placement(self, client):
        resp = client.post("/revenue/placements", json={
            "id": "p-test-1",
            "contractor_name": "Test Person",
            "client": "Leidos",
            "program": "DCGS",
            "role_title": "Intelligence Analyst",
            "bill_rate": 120,
            "pay_rate": 75,
            "start_date": "2025-03-01",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "recorded"
        assert data["projected_annual_revenue"] > 0


# =========================================
# ENDPOINT COUNT
# =========================================

class TestEndpointCount:
    def test_sixteen_endpoints(self, app):
        revenue_routes = [
            r for r in app.routes
            if hasattr(r, "path") and r.path.startswith("/revenue")
        ]
        assert len(revenue_routes) == 16
