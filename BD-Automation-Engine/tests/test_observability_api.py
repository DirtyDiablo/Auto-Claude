"""Tests for Phase 53A — Observability API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.observability.distributed_tracer as tracer_mod
import src.observability.metrics_pipeline as metrics_mod
import src.observability.slo_engine as slo_mod
from src.api.observability_api import include_observability_router


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset singletons so each test starts fresh."""
    tracer_mod._instance = None
    metrics_mod._instance = None
    slo_mod._instance = None
    yield
    tracer_mod._instance = None
    metrics_mod._instance = None
    slo_mod._instance = None


@pytest.fixture
def app():
    app = FastAPI()
    include_observability_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# TRACING
# =========================================

def test_list_traces_empty(client):
    resp = client.get("/api/observability/traces")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_get_trace_not_found(client):
    resp = client.get("/api/observability/traces/nonexistent")
    assert resp.status_code == 404


def test_search_spans_empty(client):
    resp = client.get("/api/observability/spans")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


# =========================================
# METRICS
# =========================================

def test_list_metrics(client):
    resp = client.get("/api/observability/metrics")
    assert resp.status_code == 200
    # May be 0 since no metrics have been recorded yet
    assert "metrics" in resp.json()


def test_record_metric(client):
    resp = client.post("/api/observability/metrics/record", json={
        "metric_name": "api_requests_total",
        "value": 1.0,
    })
    assert resp.status_code == 200
    assert resp.json()["recorded"] is True


def test_record_and_list_metric(client):
    client.post("/api/observability/metrics/record", json={
        "metric_name": "api_requests_total",
        "value": 1.0,
    })
    resp = client.get("/api/observability/metrics")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_export_json(client):
    client.post("/api/observability/metrics/record", json={
        "metric_name": "api_requests_total", "value": 1.0,
    })
    resp = client.get("/api/observability/metrics/export?fmt=json")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_export_prometheus(client):
    client.post("/api/observability/metrics/record", json={
        "metric_name": "api_requests_total", "value": 1.0,
    })
    resp = client.get("/api/observability/metrics/export?fmt=prometheus")
    assert resp.status_code == 200
    assert "api_requests_total" in resp.text


# =========================================
# ALERTS
# =========================================

def test_create_alert_rule(client):
    resp = client.post("/api/observability/alerts/rules", json={
        "metric_name": "api_request_duration_ms",
        "condition": "gt",
        "threshold": 1000.0,
        "severity": "critical",
    })
    assert resp.status_code == 200
    assert resp.json()["rule_id"].startswith("rule_")


def test_list_alerts_empty(client):
    resp = client.get("/api/observability/alerts")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_alert_triggers_via_api(client):
    client.post("/api/observability/alerts/rules", json={
        "metric_name": "api_request_duration_ms",
        "condition": "gt",
        "threshold": 100.0,
    })
    client.post("/api/observability/metrics/record", json={
        "metric_name": "api_request_duration_ms", "value": 500.0,
    })
    resp = client.get("/api/observability/alerts")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


# =========================================
# SLOS
# =========================================

def test_list_slos(client):
    resp = client.get("/api/observability/slos")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_slos"] >= 5


def test_get_slo(client):
    resp = client.get("/api/observability/slos/slo_api_availability")
    assert resp.status_code == 200
    assert resp.json()["slo_id"] == "slo_api_availability"


def test_get_slo_not_found(client):
    resp = client.get("/api/observability/slos/slo_fake")
    assert resp.status_code == 404


def test_record_slo_event(client):
    resp = client.post("/api/observability/slos/record", json={
        "slo_id": "slo_api_availability",
        "good": True,
    })
    assert resp.status_code == 200
    assert resp.json()["recorded"] is True


def test_record_slo_not_found(client):
    resp = client.post("/api/observability/slos/record", json={
        "slo_id": "slo_fake", "good": True,
    })
    assert resp.status_code == 404


# =========================================
# HEALTH
# =========================================

def test_health(client):
    resp = client.get("/api/observability/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "tracing" in data
    assert "metrics" in data
    assert "slos" in data
