"""Tests for Phase 44A — Intelligence API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.intelligence_api import include_intelligence_router


@pytest.fixture
def app():
    app = FastAPI()
    include_intelligence_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# LEARN
# =========================================

def test_learn(client):
    resp = client.post("/api/intelligence/learn")
    assert resp.status_code == 200
    data = resp.json()
    assert data["insights_generated"] >= 5
    assert len(data["insights"]) >= 5


# =========================================
# INSIGHTS
# =========================================

def test_get_insights(client):
    client.post("/api/intelligence/learn")
    resp = client.get("/api/intelligence/insights")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 5


def test_get_insights_by_domain(client):
    client.post("/api/intelligence/learn")
    resp = client.get("/api/intelligence/insights?domain=outreach")
    assert resp.status_code == 200
    data = resp.json()
    assert all(i["domain"] == "outreach" for i in data["insights"])


def test_get_insights_by_type(client):
    client.post("/api/intelligence/learn")
    resp = client.get("/api/intelligence/insights/program")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "program"
    assert all(i["domain"] == "program" for i in data["insights"])


def test_get_insights_invalid_type(client):
    resp = client.get("/api/intelligence/insights/invalid_type")
    assert resp.status_code == 400


# =========================================
# PATTERNS
# =========================================

def test_scan_patterns(client):
    resp = client.post("/api/intelligence/patterns/scan")
    assert resp.status_code == 200
    data = resp.json()
    assert data["patterns_detected"] >= 3
    assert data["alerts_generated"] >= 1


def test_active_patterns(client):
    client.post("/api/intelligence/patterns/scan")
    resp = client.get("/api/intelligence/patterns/active")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 3


def test_active_patterns_by_type(client):
    client.post("/api/intelligence/patterns/scan")
    resp = client.get("/api/intelligence/patterns/active?pattern_type=hiring_surge")
    assert resp.status_code == 200
    data = resp.json()
    assert all(p["pattern_type"] == "hiring_surge" for p in data["patterns"])


# =========================================
# OPPORTUNITIES
# =========================================

def test_opportunities(client):
    client.post("/api/intelligence/patterns/scan")
    resp = client.get("/api/intelligence/opportunities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


def test_opportunities_with_min_score(client):
    client.post("/api/intelligence/patterns/scan")
    resp = client.get("/api/intelligence/opportunities?min_score=50")
    assert resp.status_code == 200
    data = resp.json()
    assert all(o["score"] >= 50 for o in data["opportunities"])


# =========================================
# TRANSFER
# =========================================

def test_transfer_learning(client):
    client.post("/api/intelligence/learn")
    resp = client.post("/api/intelligence/transfer/DCGS-A/DCGS-N")
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_program"] == "DCGS-A"
    assert data["target_program"] == "DCGS-N"
    assert "similarity_score" in data


# =========================================
# BRIEFS
# =========================================

def test_weekly_brief(client):
    client.post("/api/intelligence/learn")
    client.post("/api/intelligence/patterns/scan")
    resp = client.post("/api/intelligence/brief/weekly")
    assert resp.status_code == 200
    data = resp.json()
    assert "executive_summary" in data
    assert "sections" in data
    assert "key_metrics" in data


def test_monthly_assessment(client):
    client.post("/api/intelligence/learn")
    client.post("/api/intelligence/patterns/scan")
    resp = client.post("/api/intelligence/brief/monthly")
    assert resp.status_code == 200
    data = resp.json()
    assert "executive_summary" in data
    assert "trend_analysis" in data
    assert "strategic_recommendations" in data


def test_flash_report(client):
    client.post("/api/intelligence/patterns/scan")
    # Get a pattern ID
    resp = client.get("/api/intelligence/patterns/active")
    patterns = resp.json()["patterns"]
    assert len(patterns) >= 1
    pattern_id = patterns[0]["id"]

    resp = client.post("/api/intelligence/brief/flash", json={"pattern_id": pattern_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["pattern_id"] == pattern_id
    assert data["title"].startswith("FLASH:")


def test_flash_report_not_found(client):
    resp = client.post("/api/intelligence/brief/flash", json={"pattern_id": "nonexistent"})
    assert resp.status_code == 404


# =========================================
# EFFECTIVENESS
# =========================================

def test_outreach_effectiveness(client):
    resp = client.get("/api/intelligence/effectiveness/outreach")
    assert resp.status_code == 200
    data = resp.json()
    assert "channels" in data
    assert "overall_rate" in data


def test_campaign_effectiveness(client):
    resp = client.get("/api/intelligence/effectiveness/campaigns")
    assert resp.status_code == 200
    data = resp.json()
    assert "campaigns" in data
    assert data["total_campaigns"] >= 1


# =========================================
# TRENDS
# =========================================

def test_competitive_trends(client):
    resp = client.get("/api/intelligence/trends/competitive")
    assert resp.status_code == 200
    data = resp.json()
    assert "competitors" in data
    assert data["total_competitors"] >= 1
