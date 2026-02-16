"""
Redis Streams-based event bus connecting all 3 projects.

Why Redis Streams over Kafka: Already in our Docker stack, sub-ms latency,
consumer groups for load balancing, no JVM overhead, perfect for our scale.

Stream topology — every intelligence signal has a dedicated stream:

INGESTION STREAMS (data coming in):
  jobs:scraped        — New jobs discovered by any scraper engine
  jobs:enriched       — Jobs after LLM enrichment + program mapping
  contracts:awards    — SAM.gov award discoveries
  contracts:opps      — New solicitations/RFIs/RFPs
  documents:processed — Federal docs after OCR/Docling processing
  contacts:discovered — New contacts from ZoomInfo/LinkedIn
  contacts:updated    — Contact field changes (title, company, location)

INTELLIGENCE STREAMS (analysis results):
  intel:anomalies     — Anomaly detector findings
  intel:alerts        — Alert engine firings
  intel:predictions   — ML model predictions (placement, win prob)
  intel:signals       — Composite BD opportunity signals

ACTION STREAMS (things happening):
  campaigns:events    — Campaign state changes, outreach sent/received
  campaigns:responses — Contact responses, meeting accepts, rejections
  memory:updates      — Memory layer changes across all tiers
  system:health       — Service health, scrape failures, API errors
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

try:
    from ulid import ULID as _ULID

    ULID_AVAILABLE = True
except ImportError:
    ULID_AVAILABLE = False

try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


def _generate_event_id() -> str:
    """Generate a sortable unique event ID using ULID or fallback."""
    if ULID_AVAILABLE:
        return str(_ULID())
    return f"{int(time.time() * 1000)}-{id(object())}"


class Event(BaseModel):
    """Structured event flowing through the bus."""

    event_id: str = Field(default_factory=_generate_event_id)
    event_type: str
    source: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    priority: str = "medium"  # critical, high, medium, low

    def to_redis(self) -> Dict[str, str]:
        """Serialize event for Redis Streams (all values must be strings)."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "payload": json.dumps(self.payload),
            "metadata": json.dumps(self.metadata),
            "priority": self.priority,
        }

    @classmethod
    def from_redis(cls, data: Dict[bytes, bytes]) -> "Event":
        """Deserialize event from Redis Streams."""
        decoded = {}
        for k, v in data.items():
            key = k.decode() if isinstance(k, bytes) else k
            val = v.decode() if isinstance(v, bytes) else v
            decoded[key] = val

        return cls(
            event_id=decoded["event_id"],
            event_type=decoded["event_type"],
            source=decoded["source"],
            timestamp=datetime.fromisoformat(decoded["timestamp"]),
            payload=json.loads(decoded.get("payload", "{}")),
            metadata=json.loads(decoded.get("metadata", "{}")),
            priority=decoded.get("priority", "medium"),
        )


class StreamConfig(BaseModel):
    """Configuration for a single event stream."""

    name: str
    max_len: int = 10000
    consumer_groups: List[str] = Field(default_factory=lambda: ["pts_bd_hub"])
    retention_hours: int = 168  # 7 days


class StreamStats(BaseModel):
    """Runtime statistics for a stream."""

    name: str
    length: int = 0
    consumer_groups: int = 0
    pending_messages: int = 0
    events_per_minute: float = 0.0
    oldest_event: Optional[datetime] = None
    newest_event: Optional[datetime] = None


# Dead letter queue suffix
DLQ_SUFFIX = ":dlq"
MAX_RETRIES = 3


class EventBus:
    """Central nervous system for real-time platform intelligence."""

    # Stream definitions — the 15-stream topology
    STREAM_DEFINITIONS: Dict[str, StreamConfig] = {
        # Ingestion streams
        "jobs:scraped": StreamConfig(name="jobs:scraped"),
        "jobs:enriched": StreamConfig(name="jobs:enriched"),
        "contracts:awards": StreamConfig(name="contracts:awards"),
        "contracts:opps": StreamConfig(name="contracts:opps"),
        "documents:processed": StreamConfig(name="documents:processed"),
        "contacts:discovered": StreamConfig(name="contacts:discovered"),
        "contacts:updated": StreamConfig(name="contacts:updated"),
        # Intelligence streams
        "intel:anomalies": StreamConfig(name="intel:anomalies"),
        "intel:alerts": StreamConfig(name="intel:alerts"),
        "intel:predictions": StreamConfig(name="intel:predictions"),
        "intel:signals": StreamConfig(name="intel:signals"),
        # Action streams
        "campaigns:events": StreamConfig(name="campaigns:events"),
        "campaigns:responses": StreamConfig(name="campaigns:responses"),
        "memory:updates": StreamConfig(name="memory:updates"),
        "system:health": StreamConfig(name="system:health"),
    }

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[Any] = None
        self.consumer_group = "pts_bd_hub"
        self._running = False
        self._subscriber_tasks: List[asyncio.Task] = []
        self._event_counts: Dict[str, List[float]] = {}  # stream -> list of timestamps

    async def connect(self) -> None:
        """Connect to Redis and initialize streams and consumer groups."""
        if not REDIS_AVAILABLE:
            raise RuntimeError(
                "redis package not installed. Install with: pip install redis"
            )
        self.redis = aioredis.from_url(self.redis_url, decode_responses=False)
        await self._initialize_streams()
        self._running = True
        logger.info("EventBus connected to Redis", extra={"url": self.redis_url})

    async def disconnect(self) -> None:
        """Gracefully disconnect from Redis."""
        self._running = False
        for task in self._subscriber_tasks:
            task.cancel()
        self._subscriber_tasks.clear()
        if self.redis:
            await self.redis.aclose()
            self.redis = None
        logger.info("EventBus disconnected")

    async def _initialize_streams(self) -> None:
        """Create streams and consumer groups if they don't exist."""
        for stream_name, config in self.STREAM_DEFINITIONS.items():
            for group in config.consumer_groups:
                try:
                    await self.redis.xgroup_create(
                        stream_name, group, id="0", mkstream=True
                    )
                except Exception:
                    # Group already exists — that's fine
                    pass

    async def publish(self, stream: str, event: Event) -> str:
        """
        Publish an event to a stream.

        Returns: Redis stream message ID.
        """
        if not self.redis:
            raise RuntimeError("EventBus not connected. Call connect() first.")

        config = self.STREAM_DEFINITIONS.get(stream)
        max_len = config.max_len if config else 10000

        # Set correlation_id if not present
        if "correlation_id" not in event.metadata:
            event.metadata["correlation_id"] = event.event_id

        msg_id = await self.redis.xadd(
            stream,
            event.to_redis(),
            maxlen=max_len,
            approximate=True,
        )

        # Track event count for throughput calculation
        now = time.time()
        self._event_counts.setdefault(stream, []).append(now)
        # Trim old counts (keep last 60s)
        self._event_counts[stream] = [
            t for t in self._event_counts[stream] if now - t < 60
        ]

        decoded_id = msg_id.decode() if isinstance(msg_id, bytes) else msg_id
        logger.debug(
            "Event published",
            extra={
                "stream": stream,
                "event_type": event.event_type,
                "msg_id": decoded_id,
            },
        )
        return decoded_id

    async def subscribe(
        self,
        streams: List[str],
        handler: Callable[[Event], Awaitable[None]],
        group: Optional[str] = None,
        consumer: Optional[str] = None,
        batch_size: int = 10,
    ) -> None:
        """
        Subscribe to one or more streams with a handler function.

        Uses consumer groups for load balancing across multiple instances.
        Automatic acknowledgment on successful processing.
        Dead letter queue for failed events (3 retries).
        """
        if not self.redis:
            raise RuntimeError("EventBus not connected. Call connect() first.")

        group = group or self.consumer_group
        consumer = consumer or f"consumer-{id(handler)}"

        # Ensure consumer groups exist
        for stream in streams:
            try:
                await self.redis.xgroup_create(stream, group, id="0", mkstream=True)
            except Exception:
                pass

        stream_ids = {s: ">" for s in streams}

        while self._running:
            try:
                results = await self.redis.xreadgroup(
                    group, consumer, stream_ids, count=batch_size, block=1000
                )
                if not results:
                    continue

                for stream_data in results:
                    stream_name = stream_data[0]
                    if isinstance(stream_name, bytes):
                        stream_name = stream_name.decode()
                    messages = stream_data[1]

                    for msg_id, msg_data in messages:
                        try:
                            event = Event.from_redis(msg_data)
                            await handler(event)
                            await self.redis.xack(stream_name, group, msg_id)
                        except Exception as e:
                            logger.error(
                                "Event processing failed",
                                extra={
                                    "stream": stream_name,
                                    "msg_id": msg_id,
                                    "error": str(e),
                                },
                            )
                            await self._handle_failure(
                                stream_name, group, msg_id, msg_data, e
                            )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Subscriber error", extra={"error": str(e)})
                await asyncio.sleep(1)

    async def _handle_failure(
        self,
        stream: str,
        group: str,
        msg_id: Any,
        msg_data: Dict,
        error: Exception,
    ) -> None:
        """Handle failed event processing with retry and dead letter queue."""
        try:
            # Check retry count from pending
            retry_count = 0
            try:
                pending = await self.redis.xpending_range(
                    stream, group, msg_id, msg_id, 1
                )
                if pending:
                    entry = pending[0]
                    retry_count = (
                        entry.get("times_delivered", 0)
                        if isinstance(entry, dict)
                        else 0
                    )
            except Exception:
                pass

            if retry_count >= MAX_RETRIES:
                # Move to dead letter queue
                dlq_stream = stream + DLQ_SUFFIX
                dlq_data = dict(msg_data)
                dlq_data[
                    b"_error"
                    if isinstance(list(msg_data.keys())[0], bytes)
                    else "_error"
                ] = (
                    str(error).encode()
                    if isinstance(list(msg_data.keys())[0], bytes)
                    else str(error)
                )
                await self.redis.xadd(dlq_stream, dlq_data, maxlen=1000)
                await self.redis.xack(stream, group, msg_id)
                logger.warning(
                    "Event moved to DLQ",
                    extra={"stream": stream, "dlq": dlq_stream, "msg_id": msg_id},
                )
        except Exception as e:
            logger.error("DLQ handling failed", extra={"error": str(e)})

    async def subscribe_pattern(
        self,
        pattern: str,
        handler: Callable[[Event], Awaitable[None]],
    ) -> None:
        """Subscribe to streams matching a pattern (e.g., 'jobs:*')."""
        import fnmatch

        matching = [
            name for name in self.STREAM_DEFINITIONS if fnmatch.fnmatch(name, pattern)
        ]
        if not matching:
            logger.warning("No streams match pattern", extra={"pattern": pattern})
            return
        await self.subscribe(matching, handler)

    async def get_stream_stats(self) -> Dict[str, StreamStats]:
        """Per-stream: length, consumer groups, pending messages, throughput/sec."""
        if not self.redis:
            return {}

        stats = {}
        for stream_name in self.STREAM_DEFINITIONS:
            try:
                info = await self.redis.xinfo_stream(stream_name)

                # Decode info keys
                decoded_info = {}
                for k, v in info.items():
                    key = k.decode() if isinstance(k, bytes) else k
                    decoded_info[key] = v

                length = decoded_info.get("length", 0)

                # Get consumer group count
                try:
                    groups = await self.redis.xinfo_groups(stream_name)
                    group_count = len(groups)
                except Exception:
                    group_count = 0

                # Get pending count
                pending = 0
                try:
                    for group_info in groups if group_count > 0 else []:
                        gi = {}
                        for k, v in group_info.items():
                            key = k.decode() if isinstance(k, bytes) else k
                            gi[key] = v
                        pending += gi.get("pending", 0)
                except Exception:
                    pass

                # Calculate throughput from tracked counts
                now = time.time()
                recent = [
                    t for t in self._event_counts.get(stream_name, []) if now - t < 60
                ]
                events_per_minute = len(recent)

                # Parse first/last entry timestamps
                oldest = None
                newest = None
                first_entry = decoded_info.get("first-entry")
                last_entry = decoded_info.get("last-entry")
                if first_entry:
                    try:
                        data = (
                            first_entry[1]
                            if isinstance(first_entry, (list, tuple))
                            else None
                        )
                        if data:
                            ts_raw = data.get(b"timestamp") or data.get("timestamp")
                            if ts_raw:
                                ts_str = (
                                    ts_raw.decode()
                                    if isinstance(ts_raw, bytes)
                                    else ts_raw
                                )
                                oldest = datetime.fromisoformat(ts_str)
                    except Exception:
                        pass
                if last_entry:
                    try:
                        data = (
                            last_entry[1]
                            if isinstance(last_entry, (list, tuple))
                            else None
                        )
                        if data:
                            ts_raw = data.get(b"timestamp") or data.get("timestamp")
                            if ts_raw:
                                ts_str = (
                                    ts_raw.decode()
                                    if isinstance(ts_raw, bytes)
                                    else ts_raw
                                )
                                newest = datetime.fromisoformat(ts_str)
                    except Exception:
                        pass

                stats[stream_name] = StreamStats(
                    name=stream_name,
                    length=length,
                    consumer_groups=group_count,
                    pending_messages=pending,
                    events_per_minute=events_per_minute,
                    oldest_event=oldest,
                    newest_event=newest,
                )
            except Exception:
                # Stream doesn't exist yet — return empty stats
                stats[stream_name] = StreamStats(name=stream_name)

        return stats

    async def replay(
        self,
        stream: str,
        start_id: str = "0",
        end_id: str = "+",
        count: int = 100,
    ) -> List[Event]:
        """Replay events from a stream for debugging or reprocessing."""
        if not self.redis:
            return []

        results = await self.redis.xrange(stream, start_id, end_id, count=count)
        events = []
        for msg_id, msg_data in results:
            try:
                events.append(Event.from_redis(msg_data))
            except Exception as e:
                logger.warning(
                    "Failed to parse event during replay", extra={"error": str(e)}
                )
        return events

    async def get_event_chain(self, correlation_id: str) -> List[Event]:
        """Trace an event through its full processing chain using correlation IDs."""
        if not self.redis:
            return []

        chain = []
        for stream_name in self.STREAM_DEFINITIONS:
            try:
                results = await self.redis.xrange(stream_name, "-", "+")
                for msg_id, msg_data in results:
                    try:
                        event = Event.from_redis(msg_data)
                        if event.metadata.get("correlation_id") == correlation_id:
                            chain.append(event)
                    except Exception:
                        pass
            except Exception:
                pass

        # Sort by timestamp
        chain.sort(key=lambda e: e.timestamp)
        return chain

    async def get_stream_length(self, stream: str) -> int:
        """Get the current length of a stream."""
        if not self.redis:
            return 0
        try:
            return await self.redis.xlen(stream)
        except Exception:
            return 0


# Singleton instance for module-level access
_event_bus: Optional[EventBus] = None


def get_event_bus(redis_url: str = "redis://localhost:6379") -> EventBus:
    """Get or create the singleton EventBus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus(redis_url=redis_url)
    return _event_bus
