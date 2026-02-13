"""
WebSocket server for pushing real-time updates to dashboards.

Provides 4 WebSocket channels:
  /ws/dashboard  — All dashboard-relevant events (alerts, jobs, contacts)
  /ws/campaigns  — Campaign-specific live updates
  /ws/alerts     — Alert-only feed (for notification widgets)
  /ws/system     — System health monitoring

Clients can subscribe to specific event types and apply filters.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from src.streaming.event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class ClientSubscription:
    """Tracks a single WebSocket client's subscription preferences."""

    def __init__(self, websocket: WebSocket, channel: str):
        self.websocket = websocket
        self.channel = channel
        self.subscribed_streams: Set[str] = set()
        self.filters: Dict[str, Any] = {}
        self.connected_at = datetime.now(timezone.utc)
        self.messages_sent = 0

    def matches_event(self, event: Event) -> bool:
        """Check if this client's filters match the event."""
        if not self.filters:
            return True

        # Priority filter
        priority_filter = self.filters.get("priority")
        if priority_filter and event.priority != priority_filter:
            return False

        # Program filter
        program_filter = self.filters.get("program")
        if program_filter:
            event_program = event.payload.get("program", "")
            if program_filter.lower() not in event_program.lower():
                return False

        # Event type filter
        type_filter = self.filters.get("event_type")
        if type_filter and event.event_type != type_filter:
            return False

        # Source filter
        source_filter = self.filters.get("source")
        if source_filter and event.source != source_filter:
            return False

        return True


class EventTransformer:
    """Transform raw events into dashboard-friendly payloads."""

    PRIORITY_ICONS = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }

    ACTION_MAP = {
        "contact.high_tier_discovered": ["acknowledge", "add_to_campaign", "view_profile"],
        "contract.competitor_win": ["acknowledge", "create_counter_strategy", "view_details"],
        "contract.pts_opportunity": ["acknowledge", "assign_bd_lead", "create_action_plan"],
        "campaign.positive_response": ["acknowledge", "view_contact", "schedule_followup"],
        "anomaly.priority_program": ["acknowledge", "investigate", "escalate"],
        "system.consecutive_failures": ["acknowledge", "restart_service", "view_logs"],
    }

    def transform_for_dashboard(self, event: Event) -> dict:
        """Transform raw event into dashboard-friendly payload."""
        # Human-readable summary
        summary = self._generate_summary(event)

        # Available actions
        actions = self.ACTION_MAP.get(event.event_type, ["acknowledge", "view_details"])

        return {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "source": event.source,
            "timestamp": event.timestamp.isoformat(),
            "priority": event.priority,
            "priority_icon": self.PRIORITY_ICONS.get(event.priority, "⚪"),
            "summary": summary,
            "payload": event.payload,
            "actions": actions,
            "metadata": {
                k: v
                for k, v in event.metadata.items()
                if k in ("correlation_id", "causation_id")
            },
        }

    def _generate_summary(self, event: Event) -> str:
        """Generate a human-readable summary for the event."""
        payload = event.payload
        event_type = event.event_type

        if "job" in event_type:
            title = payload.get("title", payload.get("job_title", "Unknown"))
            company = payload.get("company", "Unknown")
            return f"New job: {title} at {company}"

        if "contract" in event_type:
            title = payload.get("title", "Unknown")
            amount = payload.get("amount", 0)
            if amount:
                return f"Contract: {title} (${amount:,.0f})"
            return f"Contract: {title}"

        if "contact" in event_type:
            name = payload.get("name", "Unknown")
            company = payload.get("company", "")
            tier = payload.get("tier", "")
            parts = [f"Contact: {name}"]
            if company:
                parts.append(f"at {company}")
            if tier:
                parts.append(f"(Tier {tier})")
            return " ".join(parts)

        if "campaign" in event_type:
            outcome = payload.get("outcome", event_type.split(".")[-1])
            campaign = payload.get("campaign_id", "")
            return f"Campaign {campaign}: {outcome}"

        if "anomaly" in event_type:
            atype = payload.get("anomaly_type", "Unknown")
            program = payload.get("program", "")
            return f"Anomaly: {atype}" + (f" for {program}" if program else "")

        if "system" in event_type:
            service = payload.get("service", "Unknown")
            status = payload.get("status", event_type.split(".")[-1])
            return f"System: {service} - {status}"

        return f"{event_type}: {json.dumps(payload)[:100]}"


# Channel-to-stream mapping — which streams feed each WebSocket channel
CHANNEL_STREAMS = {
    "dashboard": [
        "jobs:scraped", "jobs:enriched",
        "contracts:awards", "contracts:opps",
        "contacts:discovered", "contacts:updated",
        "intel:alerts", "intel:signals",
    ],
    "campaigns": [
        "campaigns:events", "campaigns:responses",
        "intel:signals",
    ],
    "alerts": [
        "intel:alerts", "intel:signals", "intel:anomalies",
    ],
    "system": [
        "system:health", "intel:anomalies",
    ],
}


class RealtimeServer:
    """Push live intelligence updates to connected dashboard clients."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.connections: Dict[str, List[ClientSubscription]] = {
            "dashboard": [],
            "campaigns": [],
            "alerts": [],
            "system": [],
        }
        self.transformer = EventTransformer()
        self._bridge_task: Optional[asyncio.Task] = None
        self._total_messages_sent = 0
        self._started_at: Optional[datetime] = None

    async def start(self) -> None:
        """Start the event-to-WebSocket bridge."""
        self._started_at = datetime.now(timezone.utc)
        # Start a subscriber for each channel's streams
        all_streams = set()
        for streams in CHANNEL_STREAMS.values():
            all_streams.update(streams)

        self._bridge_task = asyncio.create_task(
            self._bridge_events(list(all_streams))
        )
        logger.info("RealtimeServer started")

    async def stop(self) -> None:
        """Stop the bridge and close all connections."""
        if self._bridge_task:
            self._bridge_task.cancel()
        for channel_clients in self.connections.values():
            for sub in channel_clients:
                try:
                    await sub.websocket.close()
                except Exception:
                    pass
            channel_clients.clear()
        logger.info("RealtimeServer stopped")

    async def _bridge_events(self, streams: List[str]) -> None:
        """Bridge events from Redis Streams to WebSocket clients."""
        async def forward_event(event: Event):
            await self.send_filtered(event)

        try:
            await self.event_bus.subscribe(
                streams=streams,
                handler=forward_event,
                group="websocket_bridge",
                consumer="ws-bridge",
            )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Bridge error", extra={"error": str(e)})

    async def handle_websocket(self, websocket: WebSocket, channel: str) -> None:
        """Handle a new WebSocket connection for a channel."""
        if channel not in self.connections:
            await websocket.close(code=4000, reason=f"Unknown channel: {channel}")
            return

        await websocket.accept()
        sub = ClientSubscription(websocket, channel)
        self.connections[channel].append(sub)

        logger.info(
            "WebSocket connected",
            extra={"channel": channel, "total": len(self.connections[channel])},
        )

        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    await self._handle_client_message(sub, msg)
                except json.JSONDecodeError:
                    await websocket.send_json({"error": "Invalid JSON"})
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.warning("WebSocket error", extra={"error": str(e)})
        finally:
            if sub in self.connections.get(channel, []):
                self.connections[channel].remove(sub)
            logger.info(
                "WebSocket disconnected",
                extra={"channel": channel, "total": len(self.connections.get(channel, []))},
            )

    async def _handle_client_message(
        self, sub: ClientSubscription, msg: dict
    ) -> None:
        """Process client subscription/filter messages."""
        if "subscribe" in msg:
            streams = msg["subscribe"]
            if isinstance(streams, list):
                sub.subscribed_streams.update(streams)
                await sub.websocket.send_json({
                    "status": "subscribed",
                    "streams": list(sub.subscribed_streams),
                })

        if "unsubscribe" in msg:
            streams = msg["unsubscribe"]
            if isinstance(streams, list):
                sub.subscribed_streams -= set(streams)
                await sub.websocket.send_json({
                    "status": "unsubscribed",
                    "streams": list(sub.subscribed_streams),
                })

        if "filter" in msg:
            sub.filters = msg["filter"]
            await sub.websocket.send_json({
                "status": "filter_applied",
                "filters": sub.filters,
            })

    async def broadcast(self, channel: str, event: Event) -> None:
        """Send event to all connections on a channel."""
        clients = self.connections.get(channel, [])
        if not clients:
            return

        payload = self.transformer.transform_for_dashboard(event)
        disconnected = []

        for sub in clients:
            try:
                await sub.websocket.send_json(payload)
                sub.messages_sent += 1
                self._total_messages_sent += 1
            except Exception:
                disconnected.append(sub)

        # Clean up disconnected clients
        for sub in disconnected:
            if sub in self.connections.get(channel, []):
                self.connections[channel].remove(sub)

    async def send_filtered(self, event: Event) -> None:
        """Route event to connections based on their filter subscriptions."""
        payload = self.transformer.transform_for_dashboard(event)
        disconnected_by_channel: Dict[str, List[ClientSubscription]] = {}

        for channel, channel_streams in CHANNEL_STREAMS.items():
            # Check if event's source stream is relevant to this channel
            # We match on event_type prefix to stream names
            relevant = False
            for stream in channel_streams:
                prefix = stream.split(":")[0]
                if prefix in event.event_type or prefix in event.source:
                    relevant = True
                    break

            # Also check if the event was explicitly published to a channel stream
            if not relevant:
                continue

            clients = self.connections.get(channel, [])
            for sub in clients:
                # Check client-level filters
                if not sub.matches_event(event):
                    continue

                # Check stream subscription
                if sub.subscribed_streams and not any(
                    s in sub.subscribed_streams
                    for s in channel_streams
                ):
                    continue

                try:
                    await sub.websocket.send_json(payload)
                    sub.messages_sent += 1
                    self._total_messages_sent += 1
                except Exception:
                    disconnected_by_channel.setdefault(channel, []).append(sub)

        # Clean up
        for channel, subs in disconnected_by_channel.items():
            for sub in subs:
                if sub in self.connections.get(channel, []):
                    self.connections[channel].remove(sub)

    async def get_connection_stats(self) -> dict:
        """Active connections per channel, message throughput, latency."""
        return {
            "channels": {
                channel: {
                    "connections": len(clients),
                    "total_messages_sent": sum(c.messages_sent for c in clients),
                }
                for channel, clients in self.connections.items()
            },
            "total_connections": sum(
                len(clients) for clients in self.connections.values()
            ),
            "total_messages_sent": self._total_messages_sent,
            "started_at": self._started_at.isoformat() if self._started_at else None,
        }
