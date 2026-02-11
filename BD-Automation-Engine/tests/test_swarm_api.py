"""Tests for Phase 41A — Swarm API."""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.swarm_api import include_swarm_router


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def app():
    app = FastAPI()
    include_swarm_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# ENDPOINT TESTS
# =========================================

def test_execute_swarm(client):
    resp = client.post("/swarm/execute", json={
        "description": "Build a BD campaign for DCGS at Langley",
        "task_type": "campaign_build",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["swarm_id"] != ""
    assert data["status"] == "completed"
    assert data["workers_used"] > 0


def test_execute_with_mode(client):
    resp = client.post("/swarm/execute", json={
        "description": "Weekly briefing for DCGS programs",
        "task_type": "weekly_briefing",
        "coordination_mode": "sequential",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["provenance"]["coordination_mode"] == "sequential"


def test_decompose(client):
    resp = client.post("/swarm/decompose", json={
        "description": "Build campaign for DCGS",
        "task_type": "campaign_build",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) == 10
    assert len(data["execution_layers"]) >= 1


def test_estimate(client):
    resp = client.post("/swarm/estimate", json={
        "description": "Contact enrichment for Leidos",
        "task_type": "contact_enrichment",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tokens"] > 0
    assert data["num_workers"] == 5


def test_workers_list(client):
    resp = client.get("/swarm/workers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 8
    assert len(data["workers"]) == 8


def test_worker_stats(client):
    resp = client.get("/swarm/workers/research/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["worker_type"] == "research"


def test_worker_stats_not_found(client):
    resp = client.get("/swarm/workers/nonexistent/stats")
    assert resp.status_code == 404


def test_history(client):
    # Execute one swarm first
    client.post("/swarm/execute", json={
        "description": "Build campaign for DCGS at Langley",
        "task_type": "campaign_build",
    })
    resp = client.get("/swarm/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


def test_status_not_found(client):
    resp = client.get("/swarm/status/nonexistent")
    assert resp.status_code == 404


def test_cancel_not_found(client):
    resp = client.post("/swarm/cancel/nonexistent")
    assert resp.status_code == 404


def test_dag_not_found(client):
    resp = client.get("/swarm/dag/nonexistent")
    assert resp.status_code == 404


def test_result_not_found(client):
    resp = client.get("/swarm/result/nonexistent")
    assert resp.status_code == 404
