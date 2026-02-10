"""Tests for Phase 38A — Data Quality API (17 endpoints)."""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.data_quality_api import include_data_quality_router


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def app():
    """Create a test app with data quality routes."""
    import src.data_quality.engine as engine_mod
    import src.data_quality.self_healer as healer_mod
    import src.data_quality.lineage as lineage_mod
    import src.data_quality.rules_dsl as dsl_mod
    old_engine = engine_mod._engine
    old_healer = healer_mod._healer
    old_tracker = lineage_mod._tracker
    old_dsl = dsl_mod._dsl
    engine_mod._engine = None
    healer_mod._healer = None
    lineage_mod._tracker = None
    dsl_mod._dsl = None

    test_app = FastAPI()
    include_data_quality_router(test_app)
    yield test_app

    engine_mod._engine = old_engine
    healer_mod._healer = old_healer
    lineage_mod._tracker = old_tracker
    dsl_mod._dsl = old_dsl


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def loaded_client(client):
    """Client with data loaded and audit run."""
    from src.data_quality.engine import get_quality_engine
    engine = get_quality_engine()
    now = datetime.now(timezone.utc)
    engine.set_data("contacts", [
        {"id": "c1", "first_name": "John", "last_name": "Smith",
         "email": "john@acme.com", "phone": "+12025551234",
         "job_title": "VP", "hierarchy_tier": 2,
         "location": "San Diego", "program": "AF DCGS - PACAF",
         "last_updated": now.isoformat()},
        {"id": "c2", "first_name": "", "last_name": "",
         "email": "bad_email", "phone": "x",
         "job_title": "Director", "hierarchy_tier": 6,
         "location": "San Diego", "program": "WRONG",
         "last_updated": (now - timedelta(days=120)).isoformat()},
    ])
    engine.set_data("programs", [
        {"id": "p1", "name": "DCGS", "contract_value": 500000000,
         "contract_end": (now + timedelta(days=365)).isoformat()},
    ])
    engine.set_data("jobs", [
        {"id": "j1", "title": "Engineer", "clearance": "secret",
         "location": "SD", "program": "DCGS", "url": "https://x.com"},
    ])
    engine.set_data("enrichments", [
        {"id": "e1", "embedding": [0.1], "confidence": 0.9},
    ])
    # Run audit
    client.post("/data-quality/audit/run")
    return client


# =========================================
# HEALTH & REPORTS
# =========================================

class TestHealthEndpoints:
    def test_health(self, loaded_client):
        resp = loaded_client.get("/data-quality/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_score" in data

    def test_report(self, loaded_client):
        resp = loaded_client.get("/data-quality/report")
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_score" in data
        assert "domain_scores" in data

    def test_report_no_audit(self, client):
        resp = client.get("/data-quality/report")
        assert resp.status_code == 200
        assert "no_audit_run" in resp.json().get("status", "")

    def test_domain_report(self, loaded_client):
        resp = loaded_client.get("/data-quality/report/contacts")
        assert resp.status_code == 200
        assert resp.json()["domain"] == "contacts"

    def test_domain_report_not_found(self, loaded_client):
        resp = loaded_client.get("/data-quality/report/nonexistent")
        assert resp.status_code == 404


# =========================================
# AUDIT & SCORING
# =========================================

class TestAuditEndpoints:
    def test_run_audit(self, client):
        # Load some data first
        from src.data_quality.engine import get_quality_engine
        engine = get_quality_engine()
        engine.set_data("contacts", [
            {"id": "c1", "first_name": "A", "last_name": "B",
             "email": "a@b.com", "last_updated": datetime.now(timezone.utc).isoformat()},
        ])
        resp = client.post("/data-quality/audit/run")
        assert resp.status_code == 200
        assert "overall_score" in resp.json()

    def test_score_record(self, loaded_client):
        resp = loaded_client.get("/data-quality/score/contacts/c1")
        assert resp.status_code == 200
        assert resp.json()["record_id"] == "c1"
        assert "overall_score" in resp.json()

    def test_score_record_not_found(self, loaded_client):
        resp = loaded_client.get("/data-quality/score/contacts/nonexistent")
        assert resp.status_code == 404


# =========================================
# ISSUES
# =========================================

class TestIssueEndpoints:
    def test_list_issues(self, loaded_client):
        resp = loaded_client.get("/data-quality/issues")
        assert resp.status_code == 200
        assert "issues" in resp.json()
        assert "total" in resp.json()

    def test_list_issues_filtered(self, loaded_client):
        resp = loaded_client.get("/data-quality/issues?domain=contacts")
        assert resp.status_code == 200
        issues = resp.json()["issues"]
        assert all(i["domain"] == "contacts" for i in issues)


# =========================================
# SELF-HEALING
# =========================================

class TestHealEndpoints:
    def test_heal(self, loaded_client):
        resp = loaded_client.post("/data-quality/heal")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_processed" in data or "status" in data

    def test_heal_log(self, loaded_client):
        loaded_client.post("/data-quality/heal")
        resp = loaded_client.get("/data-quality/heal/log")
        assert resp.status_code == 200
        assert "entries" in resp.json()


# =========================================
# LINEAGE
# =========================================

class TestLineageEndpoints:
    def test_lineage_not_found(self, client):
        resp = client.get("/data-quality/lineage/nonexistent")
        assert resp.status_code == 404

    def test_impact_analysis(self, client):
        resp = client.get("/data-quality/lineage/nonexistent/impact")
        assert resp.status_code == 200
        assert resp.json()["total_downstream"] == 0


# =========================================
# FRESHNESS & TRENDS
# =========================================

class TestFreshnessAndTrends:
    def test_freshness(self, client):
        resp = client.get("/data-quality/freshness")
        assert resp.status_code == 200
        assert "overall_freshness_score" in resp.json()

    def test_trends(self, loaded_client):
        resp = loaded_client.get("/data-quality/trends")
        assert resp.status_code == 200
        assert "trends" in resp.json()


# =========================================
# RULES
# =========================================

class TestRulesEndpoints:
    def test_list_rules(self, client):
        resp = client.get("/data-quality/rules")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 19

    def test_reload_rules(self, client):
        resp = client.post("/data-quality/rules/reload", json={
            "rules": {
                "contacts": [
                    {"rule": "test_rule", "dimension": "validity",
                     "severity": "low", "description": "Test"},
                ],
            },
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True


# =========================================
# BATCH VALIDATION
# =========================================

class TestBatchValidation:
    def test_validate_batch(self, client):
        resp = client.post("/data-quality/validate/batch", json={
            "domain": "contacts",
            "records": [
                {"email": "USER@GMAIL.COM", "phone": "2025551234"},
                {"email": "valid@test.com"},
            ],
        })
        assert resp.status_code == 200
        assert resp.json()["records_validated"] == 2
