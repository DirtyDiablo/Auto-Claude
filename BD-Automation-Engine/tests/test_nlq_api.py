"""Tests for Phase 33A — NLQ API (9 endpoints)."""

import pytest

from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.nlq_api import router


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def app():
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================================
# ASK ENDPOINT
# =========================================


class TestAskEndpoint:
    def test_ask_returns_200(self, client):
        resp = client.post("/nlq/ask", json={"query": "Find contacts at Leidos"})
        assert resp.status_code == 200

    def test_ask_has_answer(self, client):
        resp = client.post("/nlq/ask", json={"query": "Show jobs in San Diego"})
        data = resp.json()
        assert "answer" in data
        assert "intent" in data
        assert "confidence" in data
        assert "suggestions" in data

    def test_ask_with_format(self, client):
        resp = client.post(
            "/nlq/ask",
            json={
                "query": "Show pipeline analytics",
                "format": "brief",
            },
        )
        assert resp.status_code == 200


# =========================================
# CLARIFY ENDPOINT
# =========================================


class TestClarifyEndpoint:
    def test_clarify_returns_200(self, client):
        resp = client.post(
            "/nlq/clarify",
            json={
                "clarification": "I meant Hickam AFB",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data


# =========================================
# SUGGESTIONS ENDPOINT
# =========================================


class TestSuggestionsEndpoint:
    def test_suggestions_returns_200(self, client):
        resp = client.get("/nlq/suggestions")
        assert resp.status_code == 200
        data = resp.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)


# =========================================
# AUTOCOMPLETE ENDPOINT
# =========================================


class TestAutocompleteEndpoint:
    def test_autocomplete_empty(self, client):
        resp = client.get("/nlq/autocomplete")
        assert resp.status_code == 200
        data = resp.json()
        assert "suggestions" in data

    def test_autocomplete_with_query(self, client):
        resp = client.get("/nlq/autocomplete?q=show+me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "show me"
        assert len(data["suggestions"]) > 0


# =========================================
# HISTORY ENDPOINT
# =========================================


class TestHistoryEndpoint:
    def test_history_returns_200(self, client):
        resp = client.get("/nlq/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "history" in data

    def test_clear_history(self, client):
        # Ask first to create history
        client.post("/nlq/ask", json={"query": "Find jobs"})
        resp = client.delete("/nlq/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "cleared" in data


# =========================================
# INTENTS ENDPOINT
# =========================================


class TestIntentsEndpoint:
    def test_intents_returns_14(self, client):
        resp = client.get("/nlq/intents")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 14
        assert len(data["intents"]) == 14


# =========================================
# EXAMPLES ENDPOINT
# =========================================


class TestExamplesEndpoint:
    def test_examples_all(self, client):
        resp = client.get("/nlq/examples")
        assert resp.status_code == 200
        data = resp.json()
        assert "examples" in data
        assert data["total_intents"] == 14

    def test_examples_filtered(self, client):
        resp = client.get("/nlq/examples?intent=search_jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "search_jobs"
        assert len(data["examples"]) > 0


# =========================================
# FEEDBACK ENDPOINT
# =========================================


class TestFeedbackEndpoint:
    def test_feedback_returns_200(self, client):
        resp = client.post(
            "/nlq/feedback",
            json={
                "query": "Find contacts at Leidos",
                "rating": 5,
                "comment": "Great results!",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "recorded"


# =========================================
# ENDPOINT COUNT
# =========================================


class TestEndpointCount:
    def test_nine_endpoints(self, app):
        nlq_routes = [
            r for r in app.routes if hasattr(r, "path") and r.path.startswith("/nlq")
        ]
        assert len(nlq_routes) == 9
