"""Tests for Phase 42A — Memory API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.memory_api import include_memory_router


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def app():
    app = FastAPI()
    include_memory_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# STORE
# =========================================

def test_store_memory(client):
    resp = client.post("/memory/store", json={
        "content": "Called John Smith about DCGS program opportunity",
        "memory_type": "episodic",
        "source": "call_log",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["memory_id"] != ""
    assert data["memory_type"] == "episodic"
    assert data["status"] == "stored"


def test_store_semantic(client):
    resp = client.post("/memory/store", json={
        "content": "DCGS-A is a $450M intelligence program",
        "memory_type": "semantic",
        "confidence": 0.9,
        "programs": ["DCGS"],
    })
    assert resp.status_code == 200


# =========================================
# RECALL
# =========================================

def test_recall(client):
    # Store first
    client.post("/memory/store", json={
        "content": "Met with Leidos team about DCGS contract renewal",
        "memory_type": "episodic",
    })
    resp = client.post("/memory/recall", json={
        "query": "DCGS contract",
        "limit": 5,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 0
    assert isinstance(data["results"], list)


def test_recall_by_type(client):
    client.post("/memory/store", json={
        "content": "DCGS program fact",
        "memory_type": "semantic",
    })
    resp = client.post("/memory/recall", json={
        "query": "DCGS",
        "memory_types": ["semantic"],
    })
    assert resp.status_code == 200


# =========================================
# CONTEXT RECALL
# =========================================

def test_recall_context(client):
    resp = client.post("/memory/recall/context", json={
        "task_description": "Build outreach campaign for DCGS",
        "programs": ["DCGS"],
        "agent_type": "outreach",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "episodic" in data
    assert "semantic" in data
    assert "procedural" in data
    assert "summary" in data


# =========================================
# CONSOLIDATE & REFLECT & FORGET
# =========================================

def test_consolidate(client):
    resp = client.post("/memory/consolidate", json={"age_threshold_days": 7})
    assert resp.status_code == 200
    data = resp.json()
    assert "episodes_scanned" in data
    assert "facts_extracted" in data


def test_reflect(client):
    resp = client.post("/memory/reflect")
    assert resp.status_code == 200
    data = resp.json()
    assert "insights" in data
    assert "count" in data


def test_forget(client):
    resp = client.post("/memory/forget", json={"decay_factor": 0.95})
    assert resp.status_code == 200
    data = resp.json()
    assert "memories_scanned" in data


# =========================================
# GET ENDPOINTS
# =========================================

def test_stats(client):
    resp = client.get("/memory/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "episodic" in data
    assert "total_memories" in data


def test_episodic_recent(client):
    resp = client.get("/memory/episodic/recent")
    assert resp.status_code == 200
    data = resp.json()
    assert "episodes" in data


def test_semantic_facts(client):
    resp = client.get("/memory/semantic/facts")
    assert resp.status_code == 200
    data = resp.json()
    assert "facts" in data


def test_procedural_insights(client):
    resp = client.get("/memory/procedural/insights")
    assert resp.status_code == 200
    data = resp.json()
    assert "insights" in data


def test_search(client):
    client.post("/memory/store", json={
        "content": "DCGS program discussion notes",
        "memory_type": "episodic",
    })
    resp = client.get("/memory/search?q=DCGS")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data


def test_entity_memories(client):
    client.post("/memory/store", json={
        "content": "DCGS program details and contacts",
        "memory_type": "semantic",
        "programs": ["DCGS"],
    })
    resp = client.get("/memory/entity/DCGS/memories")
    assert resp.status_code == 200
    data = resp.json()
    assert data["entity"] == "DCGS"
    assert "memories" in data
