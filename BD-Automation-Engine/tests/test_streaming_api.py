"""Tests for Phase 31A - Streaming API (14 REST + 4 WebSocket endpoints)."""

import pytest
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.streaming.event_bus import Event, EventBus, StreamStats
from src.streaming.processors import EventProcessorRegistry
from src.streaming.stream_orchestrator import StreamOrchestrator
from src.streaming.websocket_server import RealtimeServer
from src.api.streaming_api import (
    router,
    configure_streaming,
)


def _make_mock_bus():
    bus = MagicMock(spec=EventBus)
    bus.publish = AsyncMock(return_value=b"1-0")
    bus.subscribe = AsyncMock()
    bus.STREAM_DEFINITIONS = EventBus.STREAM_DEFINITIONS
    bus.redis = AsyncMock()
    bus.redis.ping = AsyncMock()
    bus.get_stream_length = AsyncMock(return_value=100)
    bus.get_stream_stats = AsyncMock(
        return_value={
            "jobs:scraped": StreamStats(
                name="jobs:scraped", length=42, consumer_groups=1
            ),
        }
    )
    bus.replay = AsyncMock(
        return_value=[
            Event(event_type="test.event", source="test", payload={"key": "value"}),
        ]
    )
    bus.get_event_chain = AsyncMock(
        return_value=[
            Event(
                event_type="test.1",
                source="test",
                metadata={"correlation_id": "corr-1"},
            ),
            Event(
                event_type="test.2",
                source="test",
                metadata={"correlation_id": "corr-1"},
            ),
        ]
    )
    return bus


@pytest.fixture
def client():
    """Create a FastAPI TestClient with the streaming router mounted."""
    app = FastAPI()
    app.include_router(router)

    bus = _make_mock_bus()
    registry = EventProcessorRegistry(bus)
    orchestrator = StreamOrchestrator(bus)
    ws_server = RealtimeServer(bus)
    ws_server._started_at = datetime.now(timezone.utc)

    configure_streaming(bus, registry, orchestrator, ws_server)

    return TestClient(app)


# =========================================
# ROUTER SETUP TESTS
# =========================================


class TestRouterSetup:
    """Tests for router configuration."""

    def test_router_has_streaming_v2_tag(self):
        """Router should be tagged with streaming-v2."""
        assert "streaming-v2" in router.tags

    def test_router_has_expected_rest_routes(self):
        """Router should register 14 REST endpoints."""
        paths = [route.path for route in router.routes if hasattr(route, "methods")]
        expected = [
            "/streaming/stats",
            "/streaming/streams",
            "/streaming/streams/{name}/peek",
            "/streaming/streams/{name}/replay",
            "/streaming/processors",
            "/streaming/processors/{processor_id}/restart",
            "/streaming/workflows",
            "/streaming/workflows/{workflow_id}/trigger",
            "/streaming/workflows/executions",
            "/streaming/executions/{execution_id}",
            "/streaming/event-chain/{correlation_id}",
            "/streaming/websocket/connections",
            "/streaming/publish",
            "/streaming/health",
        ]
        for ep in expected:
            assert ep in paths, f"Missing route: {ep}"

    def test_router_has_websocket_routes(self):
        """Router should register 4 WebSocket endpoints."""
        ws_paths = [
            route.path for route in router.routes if not hasattr(route, "methods")
        ]
        expected_ws = [
            "/streaming/ws/dashboard",
            "/streaming/ws/campaigns",
            "/streaming/ws/alerts",
            "/streaming/ws/system",
        ]
        for ep in expected_ws:
            assert ep in ws_paths, f"Missing WebSocket route: {ep}"


# =========================================
# STREAM STATS & LIST ENDPOINTS
# =========================================


class TestStreamStatsEndpoint:
    """Tests for GET /streaming/stats."""

    def test_stats_returns_200(self, client):
        """Stats endpoint should return 200."""
        response = client.get("/streaming/stats")
        assert response.status_code == 200

    def test_stats_contains_streams(self, client):
        """Stats should include streams dict."""
        response = client.get("/streaming/stats")
        data = response.json()
        assert "streams" in data
        assert "total_streams" in data


class TestStreamListEndpoint:
    """Tests for GET /streaming/streams."""

    def test_list_returns_200(self, client):
        """Streams list should return 200."""
        response = client.get("/streaming/streams")
        assert response.status_code == 200

    def test_list_returns_15_streams(self, client):
        """Should list all 15 configured streams."""
        response = client.get("/streaming/streams")
        data = response.json()
        assert data["total"] == 15


# =========================================
# PEEK & REPLAY ENDPOINTS
# =========================================


class TestPeekEndpoint:
    """Tests for GET /streaming/streams/{name}/peek."""

    def test_peek_returns_200(self, client):
        """Peek should return 200 for valid stream."""
        response = client.get("/streaming/streams/jobs:scraped/peek?count=5")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data

    def test_peek_returns_404_for_unknown_stream(self, client):
        """Peek should return 404 for unknown stream."""
        response = client.get("/streaming/streams/nonexistent:stream/peek")
        assert response.status_code == 404


class TestReplayEndpoint:
    """Tests for POST /streaming/streams/{name}/replay."""

    def test_replay_returns_200(self, client):
        """Replay should return 200 for valid stream."""
        response = client.post(
            "/streaming/streams/jobs:scraped/replay",
            json={"start_id": "0", "end_id": "+", "count": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert "events" in data

    def test_replay_returns_404_for_unknown(self, client):
        """Replay should return 404 for unknown stream."""
        response = client.post(
            "/streaming/streams/fake:stream/replay",
            json={"count": 10},
        )
        assert response.status_code == 404


# =========================================
# PROCESSOR ENDPOINTS
# =========================================


class TestProcessorEndpoints:
    """Tests for processor endpoints."""

    def test_list_processors(self, client):
        """GET /streaming/processors should return all 6 processors."""
        response = client.get("/streaming/processors")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 6

    def test_restart_processor(self, client):
        """POST restart should return 200 for known processor."""
        response = client.post("/streaming/processors/job_intel/restart")
        assert response.status_code == 200

    def test_restart_unknown_processor_404(self, client):
        """POST restart should return 404 for unknown processor."""
        response = client.post("/streaming/processors/nonexistent/restart")
        assert response.status_code == 404


# =========================================
# WORKFLOW ENDPOINTS
# =========================================


class TestWorkflowEndpoints:
    """Tests for workflow endpoints."""

    def test_list_workflows(self, client):
        """GET /streaming/workflows should return 5 default workflows."""
        response = client.get("/streaming/workflows")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5

    def test_trigger_workflow(self, client):
        """POST trigger should return 200 for known workflow."""
        response = client.post(
            "/streaming/workflows/daily_intelligence_digest/trigger",
            json={"event_type": "manual.test", "payload": {"test": True}},
        )
        assert response.status_code == 200
        data = response.json()
        assert "execution_id" in data

    def test_trigger_unknown_workflow_404(self, client):
        """POST trigger should return 404 for unknown workflow."""
        response = client.post(
            "/streaming/workflows/nonexistent/trigger",
            json={"event_type": "test"},
        )
        assert response.status_code == 404

    def test_list_executions(self, client):
        """GET executions should return 200."""
        response = client.get("/streaming/workflows/executions")
        assert response.status_code == 200
        data = response.json()
        assert "executions" in data


# =========================================
# EXECUTION DETAIL ENDPOINT
# =========================================


class TestExecutionEndpoint:
    """Tests for execution detail."""

    def test_get_unknown_execution_404(self, client):
        """GET unknown execution should return 404."""
        response = client.get("/streaming/executions/nonexistent-id")
        assert response.status_code == 404


# =========================================
# EVENT CHAIN ENDPOINT
# =========================================


class TestEventChainEndpoint:
    """Tests for GET /streaming/event-chain/{correlation_id}."""

    def test_event_chain_returns_200(self, client):
        """Event chain should return 200."""
        response = client.get("/streaming/event-chain/corr-1")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert data["chain_length"] >= 1


# =========================================
# WEBSOCKET CONNECTIONS ENDPOINT
# =========================================


class TestWebSocketConnectionsEndpoint:
    """Tests for GET /streaming/websocket/connections."""

    def test_ws_connections_returns_200(self, client):
        """WebSocket stats should return 200."""
        response = client.get("/streaming/websocket/connections")
        assert response.status_code == 200
        data = response.json()
        assert "channels" in data
        assert "total_connections" in data


# =========================================
# PUBLISH ENDPOINT
# =========================================


class TestPublishEndpoint:
    """Tests for POST /streaming/publish."""

    def test_publish_returns_200(self, client):
        """Publish should return 200 for valid stream."""
        response = client.post(
            "/streaming/publish",
            json={
                "stream": "jobs:scraped",
                "event_type": "job.scraped",
                "source": "admin",
                "payload": {"title": "Test Job"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"

    def test_publish_unknown_stream_400(self, client):
        """Publish should return 400 for unknown stream."""
        response = client.post(
            "/streaming/publish",
            json={
                "stream": "fake:stream",
                "event_type": "test",
            },
        )
        assert response.status_code == 400


# =========================================
# HEALTH ENDPOINT
# =========================================


class TestHealthEndpoint:
    """Tests for GET /streaming/health."""

    def test_health_returns_200(self, client):
        """Health should return 200."""
        response = client.get("/streaming/health")
        assert response.status_code == 200

    def test_health_contains_status(self, client):
        """Health response should contain all status fields."""
        response = client.get("/streaming/health")
        data = response.json()
        assert "status" in data
        assert "redis_connected" in data
        assert "streams_active" in data
        assert "processors_running" in data
        assert "websocket_connections" in data
        assert "workflows_registered" in data
