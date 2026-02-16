"""Tests for Phase 31A - Event Bus Core (Redis Streams pub/sub, consumer groups, replay, chains)."""

import json
import pytest
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.streaming.event_bus import (
    Event,
    EventBus,
    StreamConfig,
    StreamStats,
    _generate_event_id,
    get_event_bus,
)


# =========================================
# EVENT MODEL TESTS
# =========================================


class TestEventModel:
    """Tests for the Event Pydantic model."""

    def test_event_creation_with_defaults(self):
        """Event should auto-generate id, timestamp, and empty metadata."""
        event = Event(event_type="test.created", source="unit_test")
        assert event.event_id is not None
        assert len(event.event_id) > 0
        assert event.event_type == "test.created"
        assert event.source == "unit_test"
        assert event.timestamp is not None
        assert event.payload == {}
        assert event.metadata == {}
        assert event.priority == "medium"

    def test_event_creation_with_all_fields(self):
        """Event should accept all fields."""
        now = datetime.now(timezone.utc)
        event = Event(
            event_id="custom-id-123",
            event_type="job.scraped",
            source="scraper_engine",
            timestamp=now,
            payload={"title": "Sr Analyst", "company": "Leidos"},
            metadata={"correlation_id": "abc-123"},
            priority="critical",
        )
        assert event.event_id == "custom-id-123"
        assert event.event_type == "job.scraped"
        assert event.payload["title"] == "Sr Analyst"
        assert event.metadata["correlation_id"] == "abc-123"
        assert event.priority == "critical"

    def test_event_to_redis_serialization(self):
        """to_redis should return all-string dict."""
        event = Event(
            event_type="test.serial",
            source="test",
            payload={"key": "value", "nested": {"a": 1}},
        )
        redis_data = event.to_redis()
        assert isinstance(redis_data, dict)
        for key, val in redis_data.items():
            assert isinstance(key, str)
            assert isinstance(val, str)
        assert json.loads(redis_data["payload"]) == {"key": "value", "nested": {"a": 1}}

    def test_event_from_redis_deserialization(self):
        """from_redis should reconstruct Event from bytes dict."""
        original = Event(
            event_type="contract.awarded",
            source="sam_gov",
            payload={"amount": 50000000, "agency": "USAF"},
            metadata={"correlation_id": "corr-1"},
            priority="high",
        )
        redis_data = {}
        for k, v in original.to_redis().items():
            redis_data[k.encode()] = v.encode()

        restored = Event.from_redis(redis_data)
        assert restored.event_type == "contract.awarded"
        assert restored.source == "sam_gov"
        assert restored.payload["amount"] == 50000000
        assert restored.metadata["correlation_id"] == "corr-1"
        assert restored.priority == "high"

    def test_event_from_redis_string_keys(self):
        """from_redis should handle string keys (decoded)."""
        data = {
            "event_id": "id-1",
            "event_type": "test",
            "source": "test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": "{}",
            "metadata": "{}",
            "priority": "low",
        }
        event = Event.from_redis(data)
        assert event.event_type == "test"
        assert event.priority == "low"


class TestEventIdGeneration:
    """Tests for ULID-based event ID generation."""

    def test_event_id_is_generated(self):
        """Each event should get a unique ID."""
        e1 = Event(event_type="a", source="test")
        e2 = Event(event_type="b", source="test")
        assert e1.event_id != e2.event_id

    def test_generate_event_id_returns_string(self):
        """_generate_event_id should return a non-empty string."""
        eid = _generate_event_id()
        assert isinstance(eid, str)
        assert len(eid) > 0


# =========================================
# STREAM CONFIG & STATS TESTS
# =========================================


class TestStreamConfig:
    """Tests for StreamConfig model."""

    def test_defaults(self):
        """StreamConfig should have sensible defaults."""
        cfg = StreamConfig(name="test:stream")
        assert cfg.max_len == 10000
        assert "pts_bd_hub" in cfg.consumer_groups
        assert cfg.retention_hours == 168

    def test_custom_values(self):
        """StreamConfig should accept custom values."""
        cfg = StreamConfig(
            name="custom",
            max_len=5000,
            consumer_groups=["group_a", "group_b"],
            retention_hours=48,
        )
        assert cfg.max_len == 5000
        assert len(cfg.consumer_groups) == 2


class TestStreamStats:
    """Tests for StreamStats model."""

    def test_defaults(self):
        """StreamStats should have zero defaults."""
        stats = StreamStats(name="jobs:scraped")
        assert stats.length == 0
        assert stats.consumer_groups == 0
        assert stats.pending_messages == 0
        assert stats.events_per_minute == 0.0
        assert stats.oldest_event is None


# =========================================
# EVENT BUS TESTS (mocked Redis)
# =========================================


class TestEventBusInit:
    """Tests for EventBus initialization."""

    def test_stream_definitions_count(self):
        """EventBus should define exactly 15 streams."""
        bus = EventBus()
        assert len(bus.STREAM_DEFINITIONS) == 15

    def test_all_streams_present(self):
        """All 15 named streams should be registered."""
        bus = EventBus()
        expected = [
            "jobs:scraped",
            "jobs:enriched",
            "contracts:awards",
            "contracts:opps",
            "documents:processed",
            "contacts:discovered",
            "contacts:updated",
            "intel:anomalies",
            "intel:alerts",
            "intel:predictions",
            "intel:signals",
            "campaigns:events",
            "campaigns:responses",
            "memory:updates",
            "system:health",
        ]
        for stream in expected:
            assert stream in bus.STREAM_DEFINITIONS, f"Missing stream: {stream}"

    def test_default_consumer_group(self):
        """Default consumer group should be pts_bd_hub."""
        bus = EventBus()
        assert bus.consumer_group == "pts_bd_hub"


@pytest.mark.asyncio
class TestEventBusPublish:
    """Tests for EventBus.publish."""

    async def test_publish_returns_message_id(self):
        """publish should return a message ID string."""
        bus = EventBus()
        bus.redis = AsyncMock()
        bus.redis.xadd = AsyncMock(return_value=b"1234567890-0")
        bus._running = True

        event = Event(
            event_type="job.scraped", source="test", payload={"title": "Analyst"}
        )
        msg_id = await bus.publish("jobs:scraped", event)
        assert msg_id == "1234567890-0"
        bus.redis.xadd.assert_called_once()

    async def test_publish_sets_correlation_id(self):
        """publish should auto-set correlation_id in metadata."""
        bus = EventBus()
        bus.redis = AsyncMock()
        bus.redis.xadd = AsyncMock(return_value=b"123-0")
        bus._running = True

        event = Event(event_type="test", source="test")
        assert "correlation_id" not in event.metadata
        await bus.publish("jobs:scraped", event)
        assert "correlation_id" in event.metadata

    async def test_publish_raises_when_disconnected(self):
        """publish should raise RuntimeError when not connected."""
        bus = EventBus()
        event = Event(event_type="test", source="test")
        with pytest.raises(RuntimeError, match="not connected"):
            await bus.publish("jobs:scraped", event)

    async def test_publish_tracks_event_count(self):
        """publish should track event count for throughput."""
        bus = EventBus()
        bus.redis = AsyncMock()
        bus.redis.xadd = AsyncMock(return_value=b"1-0")
        bus._running = True

        event = Event(event_type="test", source="test")
        await bus.publish("jobs:scraped", event)
        assert len(bus._event_counts.get("jobs:scraped", [])) == 1


@pytest.mark.asyncio
class TestEventBusReplay:
    """Tests for EventBus.replay."""

    async def test_replay_returns_events(self):
        """replay should return list of Events."""
        bus = EventBus()
        bus.redis = AsyncMock()

        original = Event(
            event_type="job.scraped", source="test", payload={"title": "Eng"}
        )
        redis_data = {}
        for k, v in original.to_redis().items():
            redis_data[k.encode()] = v.encode()

        bus.redis.xrange = AsyncMock(return_value=[(b"1-0", redis_data)])

        events = await bus.replay("jobs:scraped", count=10)
        assert len(events) == 1
        assert events[0].event_type == "job.scraped"

    async def test_replay_empty_stream(self):
        """replay should return empty list for empty stream."""
        bus = EventBus()
        bus.redis = AsyncMock()
        bus.redis.xrange = AsyncMock(return_value=[])

        events = await bus.replay("jobs:scraped")
        assert events == []

    async def test_replay_returns_empty_when_disconnected(self):
        """replay should return empty list when not connected."""
        bus = EventBus()
        events = await bus.replay("jobs:scraped")
        assert events == []


@pytest.mark.asyncio
class TestEventBusEventChain:
    """Tests for EventBus.get_event_chain."""

    async def test_event_chain_finds_correlated_events(self):
        """get_event_chain should find events sharing a correlation_id."""
        bus = EventBus()
        bus.redis = AsyncMock()

        corr_id = "chain-abc"
        e1 = Event(
            event_type="job.scraped",
            source="test",
            metadata={"correlation_id": corr_id},
        )
        e2 = Event(
            event_type="job.enriched",
            source="processor",
            metadata={"correlation_id": corr_id},
        )
        e_unrelated = Event(
            event_type="contact.updated",
            source="other",
            metadata={"correlation_id": "different"},
        )

        def make_redis(ev):
            return {k.encode(): v.encode() for k, v in ev.to_redis().items()}

        # Mock xrange for all streams
        bus.redis.xrange = AsyncMock(
            return_value=[
                (b"1-0", make_redis(e1)),
                (b"2-0", make_redis(e2)),
                (b"3-0", make_redis(e_unrelated)),
            ]
        )

        chain = await bus.get_event_chain(corr_id)
        assert len(chain) >= 2
        for event in chain:
            assert event.metadata.get("correlation_id") == corr_id

    async def test_event_chain_empty_when_disconnected(self):
        """get_event_chain should return empty when not connected."""
        bus = EventBus()
        chain = await bus.get_event_chain("nonexistent")
        assert chain == []


@pytest.mark.asyncio
class TestEventBusStreamLength:
    """Tests for EventBus.get_stream_length."""

    async def test_get_stream_length(self):
        """get_stream_length should return integer count."""
        bus = EventBus()
        bus.redis = AsyncMock()
        bus.redis.xlen = AsyncMock(return_value=42)

        length = await bus.get_stream_length("jobs:scraped")
        assert length == 42

    async def test_get_stream_length_disconnected(self):
        """get_stream_length should return 0 when disconnected."""
        bus = EventBus()
        length = await bus.get_stream_length("jobs:scraped")
        assert length == 0


class TestGetEventBusSingleton:
    """Tests for the get_event_bus singleton."""

    def test_returns_event_bus(self):
        """get_event_bus should return an EventBus instance."""
        import src.streaming.event_bus as eb

        eb._event_bus = None  # Reset
        bus = get_event_bus()
        assert isinstance(bus, EventBus)

    def test_returns_same_instance(self):
        """get_event_bus should return the same instance on repeated calls."""
        import src.streaming.event_bus as eb

        eb._event_bus = None
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2
        eb._event_bus = None  # Clean up
