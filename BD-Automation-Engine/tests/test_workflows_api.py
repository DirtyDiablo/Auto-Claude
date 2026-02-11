"""Tests for Phase 49A — Workflow Intelligence API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.workflows.temporal_engine as te_mod
import src.workflows.cross_project_orchestrator as co_mod
import src.workflows.nl_to_workflow as nl_mod
from src.api.workflows_api import include_workflows_router


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset singletons so each test starts fresh."""
    te_mod._instance = None
    co_mod._instance = None
    nl_mod._instance = None
    yield
    te_mod._instance = None
    co_mod._instance = None
    nl_mod._instance = None


@pytest.fixture
def app():
    app = FastAPI()
    include_workflows_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# LIST WORKFLOWS
# =========================================

def test_list_workflows(client):
    resp = client.get("/api/workflows")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 4
    names = {w["name"] for w in data["workflows"]}
    assert "FullBDCampaign" in names


# =========================================
# START / EXECUTE WORKFLOW
# =========================================

def test_start_and_execute(client):
    resp = client.post("/api/workflows/start", json={
        "workflow_id": "wf_contact_enrichment",
        "params": {"contact_id": "c001"},
        "execute": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["workflow_name"] == "ContactEnrichment"
    assert len(data["checkpoints"]) == 5


def test_start_without_execute(client):
    resp = client.post("/api/workflows/start", json={
        "workflow_id": "wf_full_bd_campaign",
        "execute": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"


def test_start_unknown_workflow(client):
    resp = client.post("/api/workflows/start", json={
        "workflow_id": "wf_nonexistent",
    })
    assert resp.status_code == 400


# =========================================
# LIST RUNS
# =========================================

def test_list_runs(client):
    client.post("/api/workflows/start", json={"workflow_id": "wf_contact_enrichment"})
    resp = client.get("/api/workflows/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


def test_list_runs_filter_status(client):
    client.post("/api/workflows/start", json={"workflow_id": "wf_contact_enrichment", "execute": True})
    resp = client.get("/api/workflows/runs?status=completed")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


# =========================================
# GET RUN DETAILS
# =========================================

def test_get_run(client):
    start = client.post("/api/workflows/start", json={"workflow_id": "wf_contact_enrichment"})
    run_id = start.json()["run_id"]
    resp = client.get(f"/api/workflows/runs/{run_id}")
    assert resp.status_code == 200
    assert resp.json()["run_id"] == run_id


def test_get_run_not_found(client):
    resp = client.get("/api/workflows/runs/run_nonexistent")
    assert resp.status_code == 404


# =========================================
# TIMELINE / TIME-TRAVEL
# =========================================

def test_timeline(client):
    start = client.post("/api/workflows/start", json={"workflow_id": "wf_contact_enrichment"})
    run_id = start.json()["run_id"]
    resp = client.get(f"/api/workflows/runs/{run_id}/timeline")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_steps"] == 5


# =========================================
# REPLAY
# =========================================

def test_replay(client):
    start = client.post("/api/workflows/start", json={"workflow_id": "wf_contact_enrichment"})
    run_id = start.json()["run_id"]
    resp = client.post(f"/api/workflows/runs/{run_id}/replay")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] != run_id
    assert data["status"] == "completed"


def test_replay_not_found(client):
    resp = client.post("/api/workflows/runs/run_nonexistent/replay")
    assert resp.status_code == 404


# =========================================
# ORCHESTRATOR TASKS
# =========================================

def test_submit_task(client):
    resp = client.post("/api/workflows/tasks", json={
        "name": "scrape_jobs",
        "payload": {"source": "usajobs"},
        "priority": 1,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "scrape_jobs"
    assert data["queue"] == "scraper_tasks"


def test_submit_task_explicit_queue(client):
    resp = client.post("/api/workflows/tasks", json={
        "name": "custom_task",
        "queue": "n8n_tasks",
    })
    assert resp.status_code == 200
    assert resp.json()["queue"] == "n8n_tasks"


def test_submit_task_invalid_queue(client):
    resp = client.post("/api/workflows/tasks", json={
        "name": "custom_task",
        "queue": "invalid_queue",
    })
    assert resp.status_code == 400


# =========================================
# QUEUES
# =========================================

def test_get_queues(client):
    resp = client.get("/api/workflows/queues")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_queues"] == 3
    assert len(data["queues"]) == 3


# =========================================
# FAN-OUT
# =========================================

def test_fan_out(client):
    resp = client.post("/api/workflows/fan-out", json={
        "task_names": ["scrape_jobs", "map_programs", "score_opportunities"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["task_ids"]) == 3


# =========================================
# NL EXECUTE
# =========================================

def test_nl_execute(client):
    resp = client.post("/api/workflows/nl/execute", json={
        "text": "Run full BD campaign for DCGS-A",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"]["intent"] == "create_campaign"
    assert data["status"] == "ready"


def test_nl_execute_unknown(client):
    resp = client.post("/api/workflows/nl/execute", json={
        "text": "What is the meaning of life?",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("invalid", "ambiguous")


# =========================================
# NL AUTOCOMPLETE
# =========================================

def test_nl_autocomplete(client):
    resp = client.post("/api/workflows/nl/autocomplete", json={
        "partial": "campaign",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


# =========================================
# STATS
# =========================================

def test_stats(client):
    client.post("/api/workflows/start", json={"workflow_id": "wf_contact_enrichment"})
    resp = client.get("/api/workflows/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "temporal" in data
    assert "orchestrator" in data
    assert "nl_engine" in data
    assert data["temporal"]["total_workflows"] == 4
