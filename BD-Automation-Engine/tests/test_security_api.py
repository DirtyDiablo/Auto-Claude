"""Tests for Phase 52A — Zero-Trust Security API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.security.abac_engine as abac_mod
import src.security.audit_trail as audit_mod
import src.security.encryption as enc_mod
from src.api.security_api import include_security_router


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset singletons so each test starts fresh."""
    abac_mod._instance = None
    audit_mod._instance = None
    enc_mod._instance = None
    yield
    abac_mod._instance = None
    audit_mod._instance = None
    enc_mod._instance = None


@pytest.fixture
def app():
    app = FastAPI()
    include_security_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# EVALUATE
# =========================================


def test_evaluate_allow(client):
    resp = client.post(
        "/api/security/evaluate",
        json={
            "user_id": "admin1",
            "role": "admin",
            "action": "delete",
            "resource_type": "contact",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "allow"
    assert "explanation" in data


def test_evaluate_deny(client):
    resp = client.post(
        "/api/security/evaluate",
        json={
            "user_id": "u1",
            "role": "analyst",
            "action": "read",
            "resource_type": "contact",
            "program": "DCGS-A",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["decision"] == "deny"


def test_evaluate_require_approval(client):
    resp = client.post(
        "/api/security/evaluate",
        json={
            "user_id": "u1",
            "role": "analyst",
            "action": "export",
            "resource_type": "export",
            "program": "P1",
            "programs_assigned": ["P1"],
            "record_count": 100,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["decision"] == "require_approval"


def test_evaluate_clearance(client):
    resp = client.post(
        "/api/security/evaluate",
        json={
            "user_id": "u1",
            "role": "analyst",
            "action": "read",
            "resource_type": "contact",
            "classification": "top_secret",
            "clearance_level": "confidential",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["decision"] == "deny"


# =========================================
# POLICIES
# =========================================


def test_list_policies(client):
    resp = client.get("/api/security/policies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 8
    assert len(data["policies"]) == 8


def test_list_enabled_policies(client):
    resp = client.get("/api/security/policies?enabled_only=true")
    assert resp.status_code == 200
    assert (
        resp.json()["total"] >= 6
    )  # may be fewer if prior test modified shared policy objects


def test_get_policy(client):
    resp = client.get("/api/security/policies/pol_admin_bypass")
    assert resp.status_code == 200
    assert resp.json()["name"] == "admin_full_access"


def test_get_policy_not_found(client):
    resp = client.get("/api/security/policies/pol_fake")
    assert resp.status_code == 404


def test_update_policy(client):
    resp = client.patch(
        "/api/security/policies/pol_admin_bypass",
        json={
            "description": "Updated for test",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Updated for test"


def test_update_policy_not_found(client):
    resp = client.patch(
        "/api/security/policies/pol_fake",
        json={
            "description": "test",
        },
    )
    assert resp.status_code == 404


# =========================================
# AUDIT TRAIL
# =========================================


def test_audit_trail_empty(client):
    resp = client.get("/api/security/audit")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_audit_trail_after_evaluate(client):
    client.post(
        "/api/security/evaluate",
        json={
            "user_id": "u1",
            "role": "admin",
            "action": "read",
            "resource_type": "contact",
        },
    )
    resp = client.get("/api/security/audit")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_audit_verify_chain(client):
    client.post(
        "/api/security/evaluate",
        json={
            "user_id": "u1",
            "role": "admin",
            "action": "read",
            "resource_type": "contact",
        },
    )
    resp = client.post("/api/security/audit/verify")
    assert resp.status_code == 200
    assert resp.json()["verified"] is True


def test_audit_stats(client):
    resp = client.get("/api/security/audit/stats")
    assert resp.status_code == 200
    assert "total_events" in resp.json()


# =========================================
# ENCRYPTION
# =========================================


def test_encryption_status(client):
    resp = client.get("/api/security/encryption/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_encrypted_fields" in data
    assert "active_deks" in data


def test_rotate_keys(client):
    resp = client.post("/api/security/encryption/rotate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


def test_list_keys(client):
    resp = client.get("/api/security/encryption/keys")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 2  # 1 KEK + 1 DEK


def test_list_keys_dek_only(client):
    resp = client.get("/api/security/encryption/keys?key_type=dek")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_sensitive_registry(client):
    resp = client.get("/api/security/encryption/registry")
    assert resp.status_code == 200
    data = resp.json()
    assert "contact" in data
    assert "humint_note" in data


# =========================================
# COMPLIANCE
# =========================================


def test_soc2_readiness(client):
    resp = client.get("/api/security/compliance/soc2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["framework"] == "SOC 2 Type II"
    assert "score" in data


def test_fedramp_readiness(client):
    resp = client.get("/api/security/compliance/fedramp")
    assert resp.status_code == 200
    data = resp.json()
    assert data["framework"] == "FedRAMP Moderate"


def test_compliance_report(client):
    # Generate some audit events first
    for i in range(5):
        client.post(
            "/api/security/evaluate",
            json={
                "user_id": f"u{i}",
                "role": "admin",
                "action": "read",
                "resource_type": "contact",
            },
        )
    resp = client.get("/api/security/compliance/report?report_type=soc2&period_days=30")
    assert resp.status_code == 200
    data = resp.json()
    assert data["report_type"] == "soc2"
    assert data["total_events"] >= 5


# =========================================
# HEALTH
# =========================================


def test_security_health(client):
    resp = client.get("/api/security/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "abac" in data
    assert "audit" in data
    assert "encryption" in data
