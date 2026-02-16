"""Tests for Phase 46A — Voice Intelligence API."""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.voice.briefing_generator as bg_mod
import src.voice.transcript_analyzer as ta_mod
from src.api.voice_api import include_voice_router


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset singletons so each test starts fresh."""
    bg_mod._instance = None
    ta_mod._instance = None
    yield
    bg_mod._instance = None
    ta_mod._instance = None


@pytest.fixture
def app():
    app = FastAPI()
    include_voice_router(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


SAMPLE_TRANSCRIPT = """
We're struggling to fill senior positions. The hiring process has been really difficult.
I spoke with Mr. Johnson about this. Leidos is having similar issues.
Our budget for FY26 is approved. The recompete is scheduled for September.
I'll send you the requirements by Friday. Schedule a follow-up meeting by next week.
I appreciate your help. Looking forward to working together.
"""


# =========================================
# BRIEFING
# =========================================


def test_generate_briefing(client):
    resp = client.post("/api/voice/briefing/c001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["contact"]["name"] == "Craig Lindahl"
    assert len(data["pain_points"]) >= 1
    assert len(data["talking_points"]) >= 1
    assert "audio" in data


def test_briefing_not_found(client):
    resp = client.post("/api/voice/briefing/nonexistent")
    assert resp.status_code == 200
    data = resp.json()
    assert "not found" in data["summary"].lower()


def test_briefing_audio(client):
    # Generate briefing first
    client.post("/api/voice/briefing/c001")
    resp = client.get("/api/voice/briefing/c001/audio")
    assert resp.status_code == 200
    data = resp.json()
    assert data["format"] == "mp3"
    assert data["duration_sec"] > 0
    assert "Craig Lindahl" in data["text_script"]


def test_briefing_audio_not_found(client):
    resp = client.get("/api/voice/briefing/nonexistent/audio")
    assert resp.status_code == 404


def test_batch_briefings(client):
    resp = client.post(
        "/api/voice/briefing/batch",
        json={
            "contact_ids": ["c001", "c002", "c003"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3


# =========================================
# TRANSCRIPT ANALYSIS
# =========================================


def test_analyze_transcript(client):
    resp = client.post(
        "/api/voice/transcript/analyze",
        json={
            "transcript": SAMPLE_TRANSCRIPT,
            "contact_id": "c001",
            "duration_sec": 300,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["contact_id"] == "c001"
    assert data["sentiment"] in ("positive", "neutral", "negative")
    assert data["total_intel_items"] >= 1


def test_analyze_empty_transcript(client):
    resp = client.post(
        "/api/voice/transcript/analyze",
        json={
            "transcript": "",
            "contact_id": "c001",
        },
    )
    assert resp.status_code == 400


def test_analyze_extracts_pain_points(client):
    resp = client.post(
        "/api/voice/transcript/analyze",
        json={
            "transcript": SAMPLE_TRANSCRIPT,
            "contact_id": "c001",
        },
    )
    data = resp.json()
    assert len(data["pain_points"]) >= 1


def test_analyze_extracts_competitors(client):
    resp = client.post(
        "/api/voice/transcript/analyze",
        json={
            "transcript": SAMPLE_TRANSCRIPT,
            "contact_id": "c001",
        },
    )
    data = resp.json()
    assert len(data["competitor_mentions"]) >= 1


def test_analyze_extracts_action_items(client):
    resp = client.post(
        "/api/voice/transcript/analyze",
        json={
            "transcript": SAMPLE_TRANSCRIPT,
            "contact_id": "c001",
        },
    )
    data = resp.json()
    assert len(data["action_items"]) >= 1


# =========================================
# VAPI WEBHOOK
# =========================================


def test_vapi_webhook(client):
    resp = client.post(
        "/api/voice/transcript/vapi-webhook",
        json={
            "call_id": "vapi_test_001",
            "transcript": SAMPLE_TRANSCRIPT,
            "contact_id": "c001",
            "duration_seconds": 300,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["call_id"] == "vapi_test_001"


# =========================================
# TRANSCRIPT GET
# =========================================


def test_get_transcript(client):
    # Analyze first
    resp = client.post(
        "/api/voice/transcript/analyze",
        json={
            "transcript": SAMPLE_TRANSCRIPT,
            "contact_id": "c001",
            "call_id": "test_call_001",
        },
    )
    # Get by call_id
    resp = client.get("/api/voice/transcript/test_call_001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["call_id"] == "test_call_001"


def test_get_transcript_not_found(client):
    resp = client.get("/api/voice/transcript/nonexistent")
    assert resp.status_code == 404


# =========================================
# HISTORY
# =========================================


def test_call_history(client):
    client.post(
        "/api/voice/transcript/analyze",
        json={
            "transcript": "First call about hiring.",
            "contact_id": "c001",
        },
    )
    client.post(
        "/api/voice/transcript/analyze",
        json={
            "transcript": "Second call about budget.",
            "contact_id": "c001",
        },
    )
    resp = client.get("/api/voice/history/c001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2


def test_call_history_empty(client):
    resp = client.get("/api/voice/history/c999")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0


# =========================================
# INTEL QUERIES
# =========================================


def test_recent_intel(client):
    client.post(
        "/api/voice/transcript/analyze",
        json={
            "transcript": SAMPLE_TRANSCRIPT,
            "contact_id": "c001",
        },
    )
    resp = client.get("/api/voice/intel/recent")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


def test_pain_points(client):
    client.post(
        "/api/voice/transcript/analyze",
        json={
            "transcript": "We're struggling with staffing issues and latency problems.",
            "contact_id": "c001",
        },
    )
    resp = client.get("/api/voice/intel/pain-points")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


def test_action_items(client):
    client.post(
        "/api/voice/transcript/analyze",
        json={
            "transcript": "I'll send the proposal by Friday. Schedule a meeting by next week.",
            "contact_id": "c001",
        },
    )
    resp = client.get("/api/voice/intel/action-items")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


# =========================================
# COACHING
# =========================================


def test_coaching(client):
    resp = client.post(
        "/api/voice/coaching/suggestions",
        json={
            "transcript": "We're also talking to Leidos about the contract recompete.",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


def test_coaching_no_triggers(client):
    resp = client.post(
        "/api/voice/coaching/suggestions",
        json={
            "transcript": "The weather is nice today.",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0


# =========================================
# ANALYTICS
# =========================================


def test_analytics(client):
    client.post(
        "/api/voice/transcript/analyze",
        json={
            "transcript": SAMPLE_TRANSCRIPT,
            "contact_id": "c001",
            "duration_sec": 300,
        },
    )
    resp = client.get("/api/voice/analytics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_calls"] >= 1
    assert "sentiment_distribution" in data
