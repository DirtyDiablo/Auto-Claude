"""Tests for Phase 43A — Governance API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.governance_api import include_governance_router


@pytest.fixture
def app():
    app = FastAPI()
    include_governance_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# CATALOG
# =========================================

def test_catalog_list(client):
    resp = client.get("/governance/catalog")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 5


def test_catalog_asset(client):
    resp = client.get("/governance/catalog/contacts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Contacts"


def test_catalog_asset_not_found(client):
    resp = client.get("/governance/catalog/nonexistent")
    assert resp.status_code == 404


def test_catalog_lineage(client):
    resp = client.get("/governance/catalog/contacts/lineage")
    assert resp.status_code == 200
    data = resp.json()
    assert "upstream" in data


def test_catalog_search(client):
    resp = client.get("/governance/catalog/search?q=contacts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1


# =========================================
# SCHEMAS
# =========================================

def test_schemas_list(client):
    resp = client.get("/governance/schemas")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 3


def test_validate_valid(client):
    resp = client.post("/governance/schemas/validate", json={
        "schema_name": "contact",
        "data": {"name": "John Smith", "email": "j@test.com"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True


def test_validate_invalid(client):
    resp = client.post("/governance/schemas/validate", json={
        "schema_name": "contact",
        "data": {"email": "j@test.com"},  # missing required "name"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False


# =========================================
# CONTRACTS
# =========================================

def test_contracts_list(client):
    resp = client.get("/governance/contracts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 3


def test_contract_check_passing(client):
    resp = client.post("/governance/contracts/check", json={
        "contract_id": "contract_jobs_scraper",
        "metrics": {"completeness": 0.95, "accuracy": 0.95},
        "record_count": 10,
        "staleness_hours": 4.0,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "passing"


def test_contract_check_breached(client):
    resp = client.post("/governance/contracts/check", json={
        "contract_id": "contract_jobs_scraper",
        "metrics": {"completeness": 0.5, "accuracy": 0.5},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "breached"
    assert len(data["breaches"]) >= 1


# =========================================
# SLAs
# =========================================

def test_slas_list(client):
    resp = client.get("/governance/slas")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 3


def test_sla_check_meeting(client):
    resp = client.post("/governance/slas/check", json={
        "sla_id": "sla_contacts_freshness",
        "metrics": {"freshness_hours": 48.0, "accuracy": 0.99, "completeness": 0.99},
    })
    assert resp.status_code == 200
    data = resp.json()
    # All targets met, none violated (may be at_risk for near-1.0 thresholds)
    assert data["status"] in ("meeting", "at_risk")
    assert data["targets_violated"] == 0


def test_sla_check_violated(client):
    resp = client.post("/governance/slas/check", json={
        "sla_id": "sla_jobs_freshness",
        "metrics": {"freshness_hours": 10.0, "completeness": 0.5},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "violated"


# =========================================
# CHECK ALL
# =========================================

def test_check_all(client):
    resp = client.post("/governance/check-all", json={
        "metrics_by_asset": {
            "contacts": {"completeness": 0.95, "accuracy": 0.97, "freshness_hours": 48},
            "jobs": {"completeness": 0.9, "accuracy": 0.95, "freshness_hours": 2},
            "programs": {"completeness": 0.85, "accuracy": 0.92, "freshness_hours": 72},
        },
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "contracts" in data
    assert "slas" in data


# =========================================
# STATS
# =========================================

def test_stats(client):
    resp = client.get("/governance/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "catalog" in data
    assert "schemas" in data
    assert "contracts" in data
    assert "slas" in data
