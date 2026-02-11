"""Tests for Phase 45A — MCP Ecosystem API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.mcp_api import include_mcp_router


@pytest.fixture
def app():
    app = FastAPI()
    include_mcp_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# REGISTRY — SERVERS
# =========================================

def test_list_servers(client):
    resp = client.get("/api/mcp/registry/servers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 9


def test_list_servers_by_capability(client):
    resp = client.get("/api/mcp/registry/servers?capability=geocoding")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


def test_register_server(client):
    resp = client.post("/api/mcp/registry/servers", json={
        "name": "Test MCP",
        "url": "http://test.example.com",
        "transport": "http",
        "capabilities": ["test_capability"],
        "priority": 5,
        "cost_tier": "free",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["server_id"] != ""
    assert data["name"] == "Test MCP"


# =========================================
# REGISTRY — TOOLS
# =========================================

def test_list_tools(client):
    resp = client.get("/api/mcp/registry/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 20


def test_discover_tools(client):
    resp = client.post("/api/mcp/registry/discover/mcp_notion")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 3


def test_discover_nonexistent(client):
    resp = client.post("/api/mcp/registry/discover/nonexistent")
    assert resp.status_code == 404


# =========================================
# HEALTH
# =========================================

def test_health_all(client):
    resp = client.get("/api/mcp/registry/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 9
    assert data["healthy"] >= 1


# =========================================
# ROUTING
# =========================================

def test_route_email(client):
    resp = client.post("/api/mcp/route", json={
        "intent": "send email to Craig Lindahl",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["selected_server"] == "mcp_google_workspace"
    assert data["confidence"] > 0


def test_route_slack(client):
    resp = client.post("/api/mcp/route", json={
        "intent": "post update in slack channel",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["selected_server"] == "mcp_slack"


def test_route_maps(client):
    resp = client.post("/api/mcp/route", json={
        "intent": "find distance from Norfolk to Langley",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["selected_server"] == "mcp_google_maps"


# =========================================
# APPS — RENDER
# =========================================

def test_render_app(client):
    resp = client.post("/api/mcp/apps/render", json={
        "template_id": "contact_card",
        "data": {"name": "Craig Lindahl", "title": "VP", "company": "GDIT", "tier": "1"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rendered"
    assert "Craig Lindahl" in data["html"]


def test_render_not_found(client):
    resp = client.post("/api/mcp/apps/render", json={
        "template_id": "nonexistent",
        "data": {},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "template_not_found"


def test_render_with_actions(client):
    resp = client.post("/api/mcp/apps/render", json={
        "template_id": "contact_card",
        "data": {"name": "Test"},
        "actions": [
            {"action_id": "a1", "tool_call": "send_email", "requires_approval": True},
        ],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["actions"]) == 1
    assert data["actions"][0]["status"] == "pending"


# =========================================
# APPS — TEMPLATES
# =========================================

def test_register_template(client):
    resp = client.post("/api/mcp/apps/templates", json={
        "template_id": "custom_test",
        "name": "Custom Test",
        "html": "<div>{{content}}</div>",
        "permissions": ["display"],
        "description": "Test template",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["template_id"] == "custom_test"


# =========================================
# ORCHESTRATE
# =========================================

def test_generate_plan(client):
    resp = client.post("/api/mcp/orchestrate/plan", json={
        "intent": "Prepare outreach for Navy DCGS-N contacts",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_steps"] >= 3
    assert data["plan_id"] != ""
    assert data["status"] == "ready"


def test_execute_plan(client):
    # First generate a plan
    resp = client.post("/api/mcp/orchestrate/plan", json={
        "intent": "Prepare outreach for contacts",
    })
    plan_id = resp.json()["plan_id"]

    # Then execute it
    resp = client.post("/api/mcp/orchestrate", json={"plan_id": plan_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["steps_completed"] >= 1


def test_execute_nonexistent_plan(client):
    resp = client.post("/api/mcp/orchestrate", json={"plan_id": "nonexistent"})
    assert resp.status_code == 404
