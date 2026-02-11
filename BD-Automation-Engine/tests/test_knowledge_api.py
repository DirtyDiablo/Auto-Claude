"""Tests for Phase 39A — Knowledge API endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.knowledge_api import include_knowledge_router


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def app():
    app = FastAPI()
    include_knowledge_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# INGEST
# =========================================

def test_ingest_episode(client):
    resp = client.post("/knowledge/ingest", json={
        "content": "John Smith works at GDIT as a Senior Analyst on DCGS.",
        "episode_type": "conversation_note",
        "source": "test",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "episode_id" in data
    assert data["entities_discovered"] >= 0


def test_ingest_episode_empty_content(client):
    resp = client.post("/knowledge/ingest", json={
        "content": "",
    })
    assert resp.status_code == 422  # validation error


# =========================================
# TIMELINE
# =========================================

def test_timeline_not_found(client):
    resp = client.get("/knowledge/entity/nonexistent/timeline")
    assert resp.status_code == 404


def test_timeline_after_ingest(client):
    # Ingest first
    resp = client.post("/knowledge/ingest", json={
        "content": "Sarah Johnson works at Leidos on the DCGS program.",
    })
    data = resp.json()
    entities = data.get("entities", [])
    if entities:
        eid = entities[0]["id"]
        resp2 = client.get(f"/knowledge/entity/{eid}/timeline")
        assert resp2.status_code == 200
        assert "entity_id" in resp2.json()


# =========================================
# CHANGES
# =========================================

def test_changes_missing_since(client):
    resp = client.get("/knowledge/entity/test-id/changes")
    assert resp.status_code == 400


def test_changes_with_since(client):
    resp = client.get("/knowledge/entity/test-id/changes?since=2024-01-01T00:00:00Z")
    assert resp.status_code == 200
    data = resp.json()
    assert "changes" in data


# =========================================
# TEMPORAL QUERY
# =========================================

def test_temporal_query(client):
    resp = client.post("/knowledge/query/temporal", json={
        "timestamp": "2025-01-01T00:00:00Z",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "facts" in data
    assert "count" in data


# =========================================
# CONTRADICTIONS
# =========================================

def test_get_contradictions(client):
    resp = client.get("/knowledge/contradictions")
    assert resp.status_code == 200
    data = resp.json()
    assert "contradictions" in data
    assert "count" in data


# =========================================
# ENTITY RESOLUTION
# =========================================

def test_resolve_entity(client):
    resp = client.post("/knowledge/resolve/entity", json={
        "entity_a": {"id": "a", "name": "John Smith", "type": "person"},
        "entity_b": {"id": "b", "name": "Jon Smith", "type": "person"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "confidence" in data
    assert "outcome" in data


def test_resolve_candidates_not_found(client):
    resp = client.get("/knowledge/resolve/candidates/nonexistent")
    assert resp.status_code == 404


def test_merge_entities(client):
    resp = client.post("/knowledge/resolve/merge", json={
        "primary": {"id": "p1", "name": "John Smith", "email": "js@test.com"},
        "duplicate": {"id": "d1", "name": "Jon Smith", "phone": "555-0123"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


def test_global_resolution(client):
    resp = client.post("/knowledge/resolve/global", json={
        "entities": [
            {"id": "1", "name": "John Smith", "type": "person"},
            {"id": "2", "name": "Jane Doe", "type": "person"},
        ],
        "entity_type": "person",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "total_entities_scanned" in data
    assert data["total_entities_scanned"] == 2


# =========================================
# COMPILE
# =========================================

def test_compile_text(client):
    resp = client.post("/knowledge/compile", json={
        "text": "John Smith at GDIT is hiring 5 analysts for the DCGS program.",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "facts" in data
    assert "count" in data
    assert data["count"] >= 1


def test_compile_batch(client):
    resp = client.post("/knowledge/compile/batch", json={
        "texts": [
            "John Smith works at GDIT.",
            "Budget is $1.5M for Q2.",
        ],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "total_facts" in data


def test_compile_notes(client):
    resp = client.post("/knowledge/compile/notes", json={
        "notes": [
            {"contact_name": "John Smith", "company": "GDIT", "notes": "Discussed hiring."},
        ],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "total_texts" in data


# =========================================
# STATS & SEARCH
# =========================================

def test_get_stats(client):
    resp = client.get("/knowledge/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_entities" in data
    assert "total_facts" in data


def test_search_semantic(client):
    # Ingest something first
    client.post("/knowledge/ingest", json={
        "content": "Robert Jones works at Northrop Grumman.",
    })
    resp = client.get("/knowledge/search/semantic?query=Robert")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "count" in data


def test_search_hybrid(client):
    resp = client.get("/knowledge/search/hybrid?query=GDIT")
    assert resp.status_code == 200
    data = resp.json()
    assert "entities" in data
    assert "facts" in data
    assert "entity_count" in data
    assert "fact_count" in data
