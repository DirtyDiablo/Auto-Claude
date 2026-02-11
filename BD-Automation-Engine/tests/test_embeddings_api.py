"""Tests for Phase 47A — Embeddings API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.embeddings.synthetic_data_generator as sg_mod
import src.embeddings.fine_tuner as ft_mod
import src.embeddings.benchmark_suite as bs_mod
from src.api.embeddings_api import include_embeddings_router


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset singletons so each test starts fresh."""
    sg_mod._instance = None
    ft_mod._instance = None
    bs_mod._instance = None
    yield
    sg_mod._instance = None
    ft_mod._instance = None
    bs_mod._instance = None


@pytest.fixture
def app():
    app = FastAPI()
    include_embeddings_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# SYNTHETIC DATA GENERATION
# =========================================

def test_generate_synthetic(client):
    resp = client.post("/api/embeddings/synthetic/generate", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_triplets"] > 0
    assert "by_strategy" in data


def test_generate_single_strategy(client):
    resp = client.post("/api/embeddings/synthetic/generate", json={
        "strategies": ["acronym"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "acronym" in data["by_strategy"]


def test_synthetic_stats(client):
    client.post("/api/embeddings/synthetic/generate", json={})
    resp = client.get("/api/embeddings/synthetic/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_triplets"] > 0


# =========================================
# FINE-TUNING
# =========================================

def test_fine_tune(client):
    resp = client.post("/api/embeddings/fine-tune", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["training_triplets"] > 0
    assert "metrics" in data


def test_fine_tune_job_status(client):
    resp = client.post("/api/embeddings/fine-tune", json={})
    job_id = resp.json()["job_id"]

    resp2 = client.get(f"/api/embeddings/fine-tune/{job_id}")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["job_id"] == job_id
    assert data["status"] == "completed"


def test_fine_tune_not_found(client):
    resp = client.get("/api/embeddings/fine-tune/nonexistent")
    assert resp.status_code == 404


# =========================================
# EVALUATE
# =========================================

def test_evaluate(client):
    # Fine-tune first to have data and models
    ft_resp = client.post("/api/embeddings/fine-tune", json={})
    models_resp = client.get("/api/embeddings/models")
    model_id = models_resp.json()["models"][0]["id"]

    resp = client.post("/api/embeddings/evaluate", json={
        "model_id": model_id,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "recall@10" in data


# =========================================
# BENCHMARK
# =========================================

def test_benchmark(client):
    resp = client.post("/api/embeddings/benchmark", json={
        "model_id": "baseline",
        "model_name": "test",
        "is_fine_tuned": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_queries"] >= 25
    assert "overall_metrics" in data
    assert "metrics_by_category" in data


# =========================================
# COMPARE
# =========================================

def test_compare(client):
    # Fine-tune to get two models
    client.post("/api/embeddings/fine-tune", json={})
    models = client.get("/api/embeddings/models").json()["models"]
    assert len(models) >= 2

    resp = client.post("/api/embeddings/compare", json={
        "model_a_id": models[0]["id"],
        "model_b_id": models[1]["id"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "winner" in data


# =========================================
# DEPLOY
# =========================================

def test_deploy(client):
    client.post("/api/embeddings/fine-tune", json={})
    models = client.get("/api/embeddings/models").json()["models"]
    ft_model = [m for m in models if not m["is_baseline"]][0]

    resp = client.post("/api/embeddings/deploy", json={
        "model_id": ft_model["id"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["deployed"] is True


def test_deploy_not_found(client):
    resp = client.post("/api/embeddings/deploy", json={
        "model_id": "nonexistent",
    })
    assert resp.status_code == 404


# =========================================
# MODELS
# =========================================

def test_list_models(client):
    resp = client.get("/api/embeddings/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1  # baseline
    assert any(m["is_baseline"] for m in data["models"])


# =========================================
# QUALITY HISTORY
# =========================================

def test_quality_history(client):
    client.post("/api/embeddings/fine-tune", json={})
    resp = client.get("/api/embeddings/quality/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


# =========================================
# A/B TESTING
# =========================================

def test_ab_test_start(client):
    client.post("/api/embeddings/fine-tune", json={})
    models = client.get("/api/embeddings/models").json()["models"]
    ids = [m["id"] for m in models]

    resp = client.post("/api/embeddings/ab-test/start", json={
        "model_a_id": ids[0],
        "model_b_id": ids[1],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["queries_served"] > 0
    assert "current_leader" in data


def test_ab_test_results(client):
    client.post("/api/embeddings/fine-tune", json={})
    models = client.get("/api/embeddings/models").json()["models"]
    ids = [m["id"] for m in models]

    client.post("/api/embeddings/ab-test/start", json={
        "model_a_id": ids[0],
        "model_b_id": ids[1],
    })

    resp = client.get("/api/embeddings/ab-test/results")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert "winner" in data["tests"][0]
