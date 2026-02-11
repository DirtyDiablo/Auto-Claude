"""Tests for Phase 58A — PWA API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.pwa.pwa_manager as pwa_mod
import src.pwa.push_notifications as push_mod
import src.pwa.responsive_api as resp_mod
from src.api.pwa_api import include_pwa_router


@pytest.fixture(autouse=True)
def _reset_singletons():
    pwa_mod._instance = None
    push_mod._instance = None
    resp_mod._instance = None
    yield
    pwa_mod._instance = None
    push_mod._instance = None
    resp_mod._instance = None


@pytest.fixture
def app():
    app = FastAPI()
    include_pwa_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# PWA ENDPOINTS
# =========================================

def test_manifest(client):
    resp = client.get("/api/pwa/manifest")
    assert resp.status_code == 200
    assert resp.json()["name"] == "BD Intelligence Hub"


def test_list_resources(client):
    resp = client.get("/api/pwa/resources")
    assert resp.status_code == 200
    assert resp.json()["total"] == 6


def test_queue_sync(client):
    resp = client.post("/api/pwa/sync", json={
        "action": "create_contact",
        "payload": {"name": "Test"},
    })
    assert resp.status_code == 200
    assert resp.json()["action"] == "create_contact"


def test_process_sync(client):
    client.post("/api/pwa/sync", json={"action": "a1"})
    client.post("/api/pwa/sync", json={"action": "a2"})
    resp = client.post("/api/pwa/sync/process")
    assert resp.status_code == 200
    assert resp.json()["synced"] == 2


# =========================================
# NOTIFICATION ENDPOINTS
# =========================================

def test_subscribe(client):
    resp = client.post("/api/pwa/notifications/subscribe", json={
        "user_id": "user1",
    })
    assert resp.status_code == 200
    assert resp.json()["user_id"] == "user1"


def test_send_notification(client):
    # Subscribe first
    client.post("/api/pwa/notifications/subscribe", json={"user_id": "user1"})
    resp = client.post("/api/pwa/notifications/send", json={
        "title": "Test Notification",
        "body": "Test body",
        "target_user_id": "user1",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "delivered"


def test_list_templates(client):
    resp = client.get("/api/pwa/notifications/templates")
    assert resp.status_code == 200
    assert resp.json()["total"] == 5


# =========================================
# RESPONSIVE API ENDPOINTS
# =========================================

def test_detect_client(client):
    resp = client.post("/api/pwa/detect-client", json={
        "user_agent": "Mobile Safari",
        "screen_width": 375,
    })
    assert resp.status_code == 200
    assert resp.json()["device_type"] == "mobile"


# =========================================
# HEALTH
# =========================================

def test_health(client):
    resp = client.get("/api/pwa/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "pwa" in data
    assert "notifications" in data
    assert "responsive_api" in data
