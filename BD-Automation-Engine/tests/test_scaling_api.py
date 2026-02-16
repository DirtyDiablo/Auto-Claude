"""Tests for Phase 57A — Scaling API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.scaling.connection_pool as cp_mod
import src.scaling.read_replicas as rr_mod
import src.scaling.cache_layer as cl_mod
import src.scaling.auto_scaler as as_mod
from src.api.scaling_api import include_scaling_router


@pytest.fixture(autouse=True)
def _reset_singletons():
    cp_mod._instance = None
    rr_mod._instance = None
    cl_mod._instance = None
    as_mod._instance = None
    yield
    cp_mod._instance = None
    rr_mod._instance = None
    cl_mod._instance = None
    as_mod._instance = None


@pytest.fixture
def app():
    app = FastAPI()
    include_scaling_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# CONNECTION POOLS
# =========================================


def test_list_pools(client):
    resp = client.get("/api/scaling/pools")
    assert resp.status_code == 200
    assert resp.json()["total"] == 5


def test_get_pool(client):
    resp = client.get("/api/scaling/pools/qdrant_pool")
    assert resp.status_code == 200
    assert resp.json()["name"] == "qdrant_pool"


def test_get_pool_not_found(client):
    resp = client.get("/api/scaling/pools/fake")
    assert resp.status_code == 404


def test_pool_health(client):
    resp = client.get("/api/scaling/pools/qdrant_pool/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


# =========================================
# READ REPLICAS
# =========================================


def test_list_replicas(client):
    resp = client.get("/api/scaling/replicas")
    assert resp.status_code == 200
    assert resp.json()["total"] == 4


def test_lag_report(client):
    resp = client.get("/api/scaling/replicas/lag")
    assert resp.status_code == 200
    assert "qdrant_primary" in resp.json()


def test_promote_replica(client):
    resp = client.post("/api/scaling/replicas/qdrant_replica_2/promote")
    assert resp.status_code == 200
    assert resp.json()["promoted"] is True


def test_promote_not_found(client):
    resp = client.post("/api/scaling/replicas/fake/promote")
    assert resp.status_code == 404


# =========================================
# CACHE LAYERS
# =========================================


def test_list_cache(client):
    resp = client.get("/api/scaling/cache")
    assert resp.status_code == 200
    assert resp.json()["total"] == 4


def test_hit_rates(client):
    resp = client.get("/api/scaling/cache/hit-rates")
    assert resp.status_code == 200


def test_warm_cache(client):
    resp = client.post("/api/scaling/cache/warm", json={"keys": ["k1", "k2"]})
    assert resp.status_code == 200
    assert resp.json()["warmed"] == 2


# =========================================
# AUTO-SCALING
# =========================================


def test_list_policies(client):
    resp = client.get("/api/scaling/policies")
    assert resp.status_code == 200
    assert resp.json()["total"] == 4


def test_evaluate_policy(client):
    resp = client.post(
        "/api/scaling/policies/api_cpu/evaluate",
        json={
            "current_value": 90.0,
        },
    )
    assert resp.status_code == 200
    assert "direction" in resp.json()


def test_evaluate_not_found(client):
    resp = client.post(
        "/api/scaling/policies/fake/evaluate",
        json={
            "current_value": 50.0,
        },
    )
    assert resp.status_code == 404


def test_recommendations(client):
    resp = client.get("/api/scaling/recommendations")
    assert resp.status_code == 200
    assert "recommendations" in resp.json()


# =========================================
# HEALTH
# =========================================


def test_health(client):
    resp = client.get("/api/scaling/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "connection_pools" in data
    assert "read_replicas" in data
    assert "cache" in data
    assert "auto_scaling" in data
