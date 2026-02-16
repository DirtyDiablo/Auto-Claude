"""Tests for Phase 40A — RAG API endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.rag_api import include_rag_router


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def app():
    app = FastAPI()
    include_rag_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# QUERY ENDPOINTS
# =========================================


def test_rag_query(client):
    resp = client.post("/rag/query", json={"question": "Who manages DCGS-A?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "query_id" in data
    assert "answer" in data
    assert "complexity" in data


def test_rag_query_simple(client):
    resp = client.post("/rag/query/simple", json={"question": "What is DCGS?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["iterations"] == 1


def test_rag_query_empty(client):
    resp = client.post("/rag/query", json={"question": ""})
    assert resp.status_code == 422


# =========================================
# DECOMPOSE
# =========================================


def test_decompose(client):
    resp = client.post(
        "/rag/query/decompose",
        json={
            "query": "Compare hiring at Langley vs PACAF",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "sub_queries" in data
    assert "complexity_score" in data


# =========================================
# EVALUATION
# =========================================


def test_evaluate_relevance(client):
    resp = client.post(
        "/rag/evaluate/relevance",
        json={
            "query": "DCGS program at GDIT",
            "passages": [
                "GDIT manages the DCGS-A program at Langley.",
                "The weather is sunny today.",
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert len(data["scores"]) == 2


def test_evaluate_support(client):
    resp = client.post(
        "/rag/evaluate/support",
        json={
            "answer": "John Smith works at GDIT on DCGS.",
            "passages": ["John Smith is a GDIT analyst working on DCGS-A."],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data
    assert "supported" in data


# =========================================
# RERANK
# =========================================


def test_rerank(client):
    resp = client.post(
        "/rag/rerank",
        json={
            "query": "DCGS program",
            "channel_results": {
                "vector": [
                    {"doc_id": "d1", "text": "DCGS-A at GDIT.", "score": 0.9},
                    {"doc_id": "d2", "text": "Weather report.", "score": 0.5},
                ],
                "bm25": [
                    {"doc_id": "d3", "text": "DCGS program status.", "score": 0.85},
                ],
            },
            "top_k": 5,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "docs" in data
    assert "stages_applied" in data


# =========================================
# STATS & BENCHMARK
# =========================================


def test_get_stats(client):
    resp = client.get("/rag/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_queries" in data


def test_get_benchmark(client):
    resp = client.get("/rag/benchmark")
    assert resp.status_code == 200


def test_run_benchmark(client):
    resp = client.post("/rag/benchmark/run")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_queries"] == 8


# =========================================
# TRACE
# =========================================


def test_trace_not_found(client):
    resp = client.get("/rag/trace/nonexistent")
    assert resp.status_code == 404


def test_trace_after_query(client):
    # Run a query first
    resp = client.post("/rag/query", json={"question": "DCGS test"})
    query_id = resp.json()["query_id"]
    # Get the trace
    resp2 = client.get(f"/rag/trace/{query_id}")
    assert resp2.status_code == 200
    assert resp2.json()["query_id"] == query_id
