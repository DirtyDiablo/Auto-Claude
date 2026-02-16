"""Tests for Phase 31A - WebSocket Server (connections, subscriptions, broadcast, filtering)."""

import pytest
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.streaming.event_bus import Event, EventBus
from src.streaming.websocket_server import (
    CHANNEL_STREAMS,
    ClientSubscription,
    EventTransformer,
    RealtimeServer,
)


def _make_mock_bus():
    bus = MagicMock(spec=EventBus)
    bus.publish = AsyncMock(return_value=b"1-0")
    bus.subscribe = AsyncMock()
    bus.STREAM_DEFINITIONS = EventBus.STREAM_DEFINITIONS
    return bus


def _make_mock_websocket():
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_text = AsyncMock(side_effect=Exception("disconnect"))
    ws.accept = AsyncMock()
    ws.close = AsyncMock()
    return ws


# =========================================
# EVENT TRANSFORMER TESTS
# =========================================


class TestEventTransformer:
    """Tests for EventTransformer."""

    def test_transform_job_event(self):
        """Should generate job summary."""
        transformer = EventTransformer()
        event = Event(
            event_type="job.scraped",
            source="scraper",
            payload={"title": "Systems Analyst", "company": "Leidos"},
            priority="medium",
        )
        result = transformer.transform_for_dashboard(event)
        assert "event_id" in result
        assert "summary" in result
        assert "Leidos" in result["summary"]
        assert "Systems Analyst" in result["summary"]
        assert result["priority_icon"] == "🟡"

    def test_transform_contract_event_with_amount(self):
        """Should format contract amount in summary."""
        transformer = EventTransformer()
        event = Event(
            event_type="contract.awarded",
            source="sam_gov",
            payload={"title": "DCGS Mod", "amount": 50000000},
            priority="critical",
        )
        result = transformer.transform_for_dashboard(event)
        assert "$50,000,000" in result["summary"]
        assert result["priority_icon"] == "🔴"

    def test_transform_contact_event(self):
        """Should generate contact summary with tier."""
        transformer = EventTransformer()
        event = Event(
            event_type="contact.discovered",
            source="zoominfo",
            payload={"name": "Jane Smith", "company": "L3Harris", "tier": 1},
        )
        result = transformer.transform_for_dashboard(event)
        assert "Jane Smith" in result["summary"]
        assert "L3Harris" in result["summary"]
        assert "Tier 1" in result["summary"]

    def test_transform_campaign_event(self):
        """Should generate campaign summary."""
        transformer = EventTransformer()
        event = Event(
            event_type="campaign.response",
            source="outreach",
            payload={"campaign_id": "c-42", "outcome": "interested"},
        )
        result = transformer.transform_for_dashboard(event)
        assert "c-42" in result["summary"]

    def test_transform_anomaly_event(self):
        """Should generate anomaly summary."""
        transformer = EventTransformer()
        event = Event(
            event_type="anomaly.detected",
            source="detector",
            payload={"anomaly_type": "VOLUME_SPIKE", "program": "PACAF"},
        )
        result = transformer.transform_for_dashboard(event)
        assert "VOLUME_SPIKE" in result["summary"]
        assert "PACAF" in result["summary"]

    def test_transform_system_event(self):
        """Should generate system summary."""
        transformer = EventTransformer()
        event = Event(
            event_type="system.health",
            source="monitor",
            payload={"service": "qdrant", "status": "healthy"},
        )
        result = transformer.transform_for_dashboard(event)
        assert "qdrant" in result["summary"]

    def test_transform_includes_actions(self):
        """Known event types should have action buttons."""
        transformer = EventTransformer()
        event = Event(
            event_type="contact.high_tier_discovered",
            source="processor",
            payload={"name": "Boss Person"},
        )
        result = transformer.transform_for_dashboard(event)
        assert "acknowledge" in result["actions"]
        assert "add_to_campaign" in result["actions"]

    def test_transform_strips_internal_metadata(self):
        """Should only include safe metadata keys."""
        transformer = EventTransformer()
        event = Event(
            event_type="test",
            source="test",
            metadata={
                "correlation_id": "abc",
                "causation_id": "def",
                "internal_key": "secret",
            },
        )
        result = transformer.transform_for_dashboard(event)
        assert "correlation_id" in result["metadata"]
        assert "internal_key" not in result["metadata"]


# =========================================
# CLIENT SUBSCRIPTION TESTS
# =========================================


class TestClientSubscription:
    """Tests for ClientSubscription."""

    def test_matches_without_filters(self):
        """No filters = match all events."""
        ws = _make_mock_websocket()
        sub = ClientSubscription(ws, "dashboard")
        event = Event(event_type="test", source="test", priority="high")
        assert sub.matches_event(event) is True

    def test_priority_filter(self):
        """Should filter by priority."""
        ws = _make_mock_websocket()
        sub = ClientSubscription(ws, "dashboard")
        sub.filters = {"priority": "critical"}

        high_event = Event(event_type="test", source="test", priority="high")
        crit_event = Event(event_type="test", source="test", priority="critical")

        assert sub.matches_event(high_event) is False
        assert sub.matches_event(crit_event) is True

    def test_program_filter(self):
        """Should filter by program (case-insensitive substring)."""
        ws = _make_mock_websocket()
        sub = ClientSubscription(ws, "dashboard")
        sub.filters = {"program": "PACAF"}

        match_event = Event(
            event_type="test", source="test", payload={"program": "AF DCGS - PACAF"}
        )
        no_match = Event(event_type="test", source="test", payload={"program": "F-35"})

        assert sub.matches_event(match_event) is True
        assert sub.matches_event(no_match) is False


# =========================================
# CHANNEL STREAMS MAPPING
# =========================================


class TestChannelStreams:
    """Tests for channel-to-stream mapping."""

    def test_all_channels_defined(self):
        """All 4 channels should be defined."""
        assert "dashboard" in CHANNEL_STREAMS
        assert "campaigns" in CHANNEL_STREAMS
        assert "alerts" in CHANNEL_STREAMS
        assert "system" in CHANNEL_STREAMS

    def test_dashboard_has_most_streams(self):
        """Dashboard channel should subscribe to the most streams."""
        assert len(CHANNEL_STREAMS["dashboard"]) >= 6


# =========================================
# REALTIME SERVER TESTS
# =========================================


class TestRealtimeServer:
    """Tests for RealtimeServer."""

    def test_init_creates_4_channels(self):
        """Server should initialize with 4 channels."""
        bus = _make_mock_bus()
        server = RealtimeServer(bus)
        assert len(server.connections) == 4
        assert "dashboard" in server.connections

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_clients(self):
        """Broadcast should send to all connected clients on channel."""
        bus = _make_mock_bus()
        server = RealtimeServer(bus)

        ws1 = _make_mock_websocket()
        ws2 = _make_mock_websocket()
        sub1 = ClientSubscription(ws1, "dashboard")
        sub2 = ClientSubscription(ws2, "dashboard")
        server.connections["dashboard"] = [sub1, sub2]

        event = Event(event_type="test.broadcast", source="test", priority="high")
        await server.broadcast("dashboard", event)

        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()
        assert server._total_messages_sent == 2

    @pytest.mark.asyncio
    async def test_broadcast_cleans_disconnected_clients(self):
        """Broadcast should remove clients that raise on send."""
        bus = _make_mock_bus()
        server = RealtimeServer(bus)

        ws_ok = _make_mock_websocket()
        ws_bad = _make_mock_websocket()
        ws_bad.send_json = AsyncMock(side_effect=Exception("disconnected"))

        sub_ok = ClientSubscription(ws_ok, "dashboard")
        sub_bad = ClientSubscription(ws_bad, "dashboard")
        server.connections["dashboard"] = [sub_ok, sub_bad]

        event = Event(event_type="test", source="test")
        await server.broadcast("dashboard", event)

        assert len(server.connections["dashboard"]) == 1
        assert sub_ok in server.connections["dashboard"]

    @pytest.mark.asyncio
    async def test_connection_stats(self):
        """get_connection_stats should return channel counts."""
        bus = _make_mock_bus()
        server = RealtimeServer(bus)
        server._started_at = datetime.now(timezone.utc)

        ws = _make_mock_websocket()
        sub = ClientSubscription(ws, "alerts")
        sub.messages_sent = 5
        server.connections["alerts"] = [sub]

        stats = await server.get_connection_stats()
        assert stats["total_connections"] == 1
        assert stats["channels"]["alerts"]["connections"] == 1
        assert stats["channels"]["alerts"]["total_messages_sent"] == 5
