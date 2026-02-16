"""Tests for Phase 35A — Proposal API (10 endpoints)."""

import pytest

from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.proposal_api import router


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
# CAPABILITY STATEMENT ENDPOINT
# =========================================


class TestCapabilityEndpoint:
    def test_generate_capability(self, client):
        resp = client.post(
            "/proposals/capability-statement",
            json={
                "program": "DCGS",
                "agency": "USAF",
                "variant": "two_page",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "sections" in data
        assert data["program"] == "DCGS"

    def test_one_page_variant(self, client):
        resp = client.post(
            "/proposals/capability-statement",
            json={
                "program": "NGEN",
                "variant": "one_page",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["variant"] == "one_page"


# =========================================
# PAST PERFORMANCE ENDPOINT
# =========================================


class TestPastPerformanceEndpoint:
    def test_build_past_performance(self, client):
        resp = client.post(
            "/proposals/past-performance",
            json={
                "solicitation": "DCGS-2025-RFP",
                "requirements": {"agency": "USAF"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert "avg_relevance" in data


# =========================================
# COMPLIANCE MATRIX ENDPOINT
# =========================================


class TestComplianceEndpoint:
    def test_from_text(self, client):
        resp = client.post(
            "/proposals/compliance-matrix",
            json={
                "rfp_title": "DCGS RFP",
                "document_text": "The contractor shall provide TS/SCI cleared analysts for intelligence operations.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "rows" in data
        assert "compliance_rate" in data

    def test_from_requirements(self, client):
        resp = client.post(
            "/proposals/compliance-matrix",
            json={
                "rfp_title": "Test RFP",
                "requirements": [
                    {
                        "id": "REQ-001",
                        "text": "Shall provide cleared staffing",
                        "type": "staffing",
                    },
                ],
            },
        )
        assert resp.status_code == 200

    def test_missing_input_400(self, client):
        resp = client.post(
            "/proposals/compliance-matrix",
            json={
                "rfp_title": "Empty RFP",
            },
        )
        assert resp.status_code == 400


# =========================================
# PRICING ENDPOINTS
# =========================================


class TestPricingEndpoints:
    def test_labor_categories(self, client):
        resp = client.post(
            "/proposals/pricing/labor-categories",
            json={
                "titles": ["Senior Systems Engineer", "Intelligence Analyst"],
                "clearance": "TS/SCI",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert "categories" in data

    def test_rate_card(self, client):
        resp = client.post(
            "/proposals/pricing/rate-card",
            json={
                "title": "DCGS Rate Card",
                "categories": [
                    {"title": "Systems Engineer", "clearance": "Secret"},
                    {"title": "Intelligence Analyst", "clearance": "TS/SCI"},
                ],
                "pricing_model": "T&M",
                "option_years": 4,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_categories"] == 2

    def test_pricing_analysis(self, client):
        resp = client.post(
            "/proposals/pricing/analysis",
            json={
                "program": "DCGS",
                "categories": [
                    {"title": "Intelligence Analyst", "clearance": "TS/SCI"},
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "competitive_position" in data
        assert "recommendations" in data


# =========================================
# FULL PACKAGE ENDPOINT
# =========================================


class TestFullPackageEndpoint:
    def test_full_package(self, client):
        resp = client.post(
            "/proposals/full-package",
            json={
                "program": "DCGS",
                "agency": "USAF",
                "solicitation": "FA8075-25-R-0001",
                "labor_titles": ["Intelligence Analyst", "Systems Engineer"],
                "clearance": "TS/SCI",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "capability_statement" in data
        assert "past_performance" in data
        assert "rate_card" in data


# =========================================
# TEMPLATES & HISTORY
# =========================================


class TestTemplatesAndHistory:
    def test_templates(self, client):
        resp = client.get("/proposals/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert "templates" in data
        assert "pricing_models" in data

    def test_history(self, client):
        # Generate something first
        client.post(
            "/proposals/capability-statement",
            json={
                "program": "DCGS",
                "agency": "USAF",
            },
        )
        resp = client.get("/proposals/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "capability_statements" in data


# =========================================
# ENDPOINT COUNT
# =========================================


class TestEndpointCount:
    def test_ten_endpoints(self, app):
        proposal_routes = [
            r
            for r in app.routes
            if hasattr(r, "path") and r.path.startswith("/proposals")
        ]
        assert len(proposal_routes) == 10
