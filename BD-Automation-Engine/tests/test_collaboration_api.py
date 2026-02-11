"""Tests for Phase 50A — Real-Time Collaboration API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.collaboration.yjs_engine as yjs_mod
import src.collaboration.contact_claiming as cc_mod
import src.collaboration.shared_intel_feed as sif_mod
from src.api.collaboration_api import include_collaboration_router


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset singletons so each test starts fresh."""
    yjs_mod._instance = None
    cc_mod._instance = None
    sif_mod._instance = None
    yield
    yjs_mod._instance = None
    cc_mod._instance = None
    sif_mod._instance = None


@pytest.fixture
def app():
    app = FastAPI()
    include_collaboration_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# ROOMS
# =========================================

def test_create_room(client):
    resp = client.post("/api/collab/rooms", json={
        "room_type": "call_sheet",
        "name": "DCGS-A Call Prep",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["room_type"] == "call_sheet"
    assert "state" in data


def test_create_room_invalid_type(client):
    resp = client.post("/api/collab/rooms", json={
        "room_type": "invalid",
        "name": "Bad Room",
    })
    assert resp.status_code == 400


def test_list_rooms(client):
    client.post("/api/collab/rooms", json={"room_type": "pipeline", "name": "A"})
    client.post("/api/collab/rooms", json={"room_type": "war_room", "name": "B"})
    resp = client.get("/api/collab/rooms")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_list_rooms_filter(client):
    client.post("/api/collab/rooms", json={"room_type": "pipeline", "name": "A"})
    client.post("/api/collab/rooms", json={"room_type": "war_room", "name": "B"})
    resp = client.get("/api/collab/rooms?room_type=pipeline")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


# =========================================
# JOIN ROOM
# =========================================

def test_join_room(client):
    room = client.post("/api/collab/rooms", json={
        "room_type": "call_sheet", "name": "Test",
    }).json()
    resp = client.post(f"/api/collab/rooms/{room['room_id']}/join", json={
        "user_id": "u1", "display_name": "Alice",
    })
    assert resp.status_code == 200
    assert resp.json()["user_id"] == "u1"


def test_join_nonexistent_room(client):
    resp = client.post("/api/collab/rooms/room_fake/join", json={
        "user_id": "u1", "display_name": "Alice",
    })
    assert resp.status_code == 404


# =========================================
# CRDT OPERATIONS
# =========================================

def test_apply_operation(client):
    room = client.post("/api/collab/rooms", json={
        "room_type": "call_sheet", "name": "Test",
    }).json()
    resp = client.post(f"/api/collab/rooms/{room['room_id']}/op", json={
        "op_type": "insert", "path": "notes", "value": "Call Craig", "user_id": "u1",
    })
    assert resp.status_code == 200
    assert resp.json()["op_type"] == "insert"


def test_get_room_state(client):
    room = client.post("/api/collab/rooms", json={
        "room_type": "call_sheet", "name": "Test",
    }).json()
    client.post(f"/api/collab/rooms/{room['room_id']}/op", json={
        "op_type": "insert", "path": "notes", "value": "Hello", "user_id": "u1",
    })
    resp = client.get(f"/api/collab/rooms/{room['room_id']}/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"]["notes"] == "Hello"
    assert data["version"] == 1


# =========================================
# CLAIMS
# =========================================

def test_claim_contact(client):
    resp = client.post("/api/collab/claims", json={
        "contact_id": "c001",
        "contact_name": "Craig Lindahl",
        "owner_id": "rep_01",
        "owner_name": "Sarah Mitchell",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


def test_duplicate_claim_409(client):
    client.post("/api/collab/claims", json={
        "contact_id": "c001", "contact_name": "Craig Lindahl",
        "owner_id": "rep_01", "owner_name": "Sarah Mitchell",
    })
    resp = client.post("/api/collab/claims", json={
        "contact_id": "c001", "contact_name": "Craig Lindahl",
        "owner_id": "rep_02", "owner_name": "James Chen",
    })
    assert resp.status_code == 409


def test_list_claims(client):
    client.post("/api/collab/claims", json={
        "contact_id": "c001", "contact_name": "Craig",
        "owner_id": "rep_01", "owner_name": "Sarah",
    })
    resp = client.get("/api/collab/claims")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_release_claim(client):
    claim = client.post("/api/collab/claims", json={
        "contact_id": "c001", "contact_name": "Craig",
        "owner_id": "rep_01", "owner_name": "Sarah",
    }).json()
    resp = client.post(f"/api/collab/claims/{claim['claim_id']}/release")
    assert resp.status_code == 200
    assert resp.json()["status"] == "released"


def test_contest_claim(client):
    claim = client.post("/api/collab/claims", json={
        "contact_id": "c001", "contact_name": "Craig",
        "owner_id": "rep_01", "owner_name": "Sarah",
    }).json()
    resp = client.post(f"/api/collab/claims/{claim['claim_id']}/contest", json={
        "requester_id": "rep_02",
        "requester_name": "James Chen",
        "reason": "Existing relationship",
    })
    assert resp.status_code == 200
    assert resp.json()["requester_id"] == "rep_02"


# =========================================
# INTEL FEED
# =========================================

def test_post_intel(client):
    resp = client.post("/api/collab/intel", json={
        "intel_type": "win_intel",
        "priority": "high",
        "title": "Won DCGS-A TO5",
        "body": "$10M ceiling",
        "author_id": "rep_01",
        "author_name": "Sarah Mitchell",
        "program": "DCGS-A",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intel_type"] == "win_intel"
    assert data["title"] == "Won DCGS-A TO5"


def test_post_intel_invalid_type(client):
    resp = client.post("/api/collab/intel", json={
        "intel_type": "invalid_type",
        "title": "Bad", "body": "Bad",
        "author_id": "r1", "author_name": "A",
    })
    assert resp.status_code == 400


def test_get_intel_feed(client):
    resp = client.get("/api/collab/intel")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 5  # seed data


def test_get_intel_feed_filter(client):
    resp = client.get("/api/collab/intel?intel_type=competitor_move")
    assert resp.status_code == 200
    data = resp.json()
    assert all(i["intel_type"] == "competitor_move" for i in data["items"])


# =========================================
# STATS
# =========================================

def test_stats(client):
    resp = client.get("/api/collab/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "rooms" in data
    assert "claims" in data
    assert "intel_feed" in data
