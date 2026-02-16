"""
WebSocket Real-Time Server - Live dashboard updates via WebSocket.

Manages WebSocket connections, broadcasts events to all connected clients,
and provides a heartbeat mechanism to detect stale connections.

JSON protocol message types:
  - event:         { type, data: { event_type, payload, timestamp } }
  - notification:  { type, data: { level, title, message } }
  - metric_update: { type, data: { metric_name, value, delta } }
  - pipeline_move: { type, data: { deal_id, from_stage, to_stage } }
  - agent_status:  { type, data: { agent_name, status, last_output } }
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass, field
from collections import deque

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Metadata for a connected WebSocket client."""

    client_id: str
    websocket: WebSocket
    connected_at: float
    last_ping: float
    messages_sent: int = 0
    subscriptions: Set[str] = field(default_factory=lambda: {"all"})


class RealtimeServer:
    """
    WebSocket connection manager for real-time dashboard updates.

    Features:
      - Track connected clients with unique IDs
      - Broadcast messages to all clients
      - Send targeted messages to specific clients
      - Heartbeat ping/pong every 30s
      - Event history buffer (last 200 events)
      - Connection statistics
    """

    HEARTBEAT_INTERVAL = 30  # seconds
    MAX_EVENT_HISTORY = 200

    def __init__(self):
        self._connections: Dict[str, ConnectionInfo] = {}
        self._event_history: deque = deque(maxlen=self.MAX_EVENT_HISTORY)
        self._total_messages_sent: int = 0
        self._start_time: float = time.time()
        self._heartbeat_task: Optional[asyncio.Task] = None

    # ─── Connection lifecycle ─────────────────────────────

    async def connect(self, websocket: WebSocket) -> str:
        """Accept a WebSocket connection and return client ID."""
        await websocket.accept()
        client_id = str(uuid.uuid4())[:8]
        now = time.time()

        self._connections[client_id] = ConnectionInfo(
            client_id=client_id,
            websocket=websocket,
            connected_at=now,
            last_ping=now,
        )

        logger.info(
            f"WebSocket client connected: {client_id} (total: {len(self._connections)})"
        )

        # Send welcome message with client ID and recent events
        await self._send_json(
            websocket,
            {
                "type": "welcome",
                "data": {
                    "client_id": client_id,
                    "server_uptime": int(time.time() - self._start_time),
                    "active_connections": len(self._connections),
                    "recent_events": len(self._event_history),
                },
            },
        )

        # Start heartbeat if not running
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        return client_id

    def disconnect(self, client_id: str):
        """Remove a client connection."""
        if client_id in self._connections:
            del self._connections[client_id]
            logger.info(
                f"WebSocket client disconnected: {client_id} (total: {len(self._connections)})"
            )

        # Stop heartbeat if no connections
        if (
            not self._connections
            and self._heartbeat_task
            and not self._heartbeat_task.done()
        ):
            self._heartbeat_task.cancel()

    # ─── Message sending ──────────────────────────────────

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        if not self._connections:
            return

        # Add to event history
        message.setdefault("timestamp", datetime.now().isoformat())
        self._event_history.append(message)

        dead_clients: List[str] = []
        for client_id, conn in self._connections.items():
            try:
                await self._send_json(conn.websocket, message)
                conn.messages_sent += 1
                self._total_messages_sent += 1
            except Exception:
                dead_clients.append(client_id)

        # Clean up dead connections
        for cid in dead_clients:
            self.disconnect(cid)

    async def send_to(self, client_id: str, message: Dict[str, Any]):
        """Send a message to a specific client."""
        conn = self._connections.get(client_id)
        if not conn:
            return

        message.setdefault("timestamp", datetime.now().isoformat())
        try:
            await self._send_json(conn.websocket, message)
            conn.messages_sent += 1
            self._total_messages_sent += 1
        except Exception:
            self.disconnect(client_id)

    async def _send_json(self, websocket: WebSocket, data: Dict):
        """Send JSON data over a WebSocket."""
        await websocket.send_text(json.dumps(data))

    # ─── Convenience broadcast methods ────────────────────

    async def broadcast_event(self, event_type: str, payload: Dict):
        """Broadcast a typed event."""
        await self.broadcast(
            {
                "type": "event",
                "data": {
                    "event_type": event_type,
                    "payload": payload,
                    "timestamp": datetime.now().isoformat(),
                },
            }
        )

    async def broadcast_notification(self, level: str, title: str, message: str):
        """Broadcast a notification (info, warning, error, success)."""
        await self.broadcast(
            {
                "type": "notification",
                "data": {
                    "level": level,
                    "title": title,
                    "message": message,
                },
            }
        )

    async def broadcast_metric(self, metric_name: str, value: float, delta: float = 0):
        """Broadcast a metric update."""
        await self.broadcast(
            {
                "type": "metric_update",
                "data": {
                    "metric_name": metric_name,
                    "value": value,
                    "delta": delta,
                },
            }
        )

    async def broadcast_pipeline_move(
        self, deal_id: str, from_stage: str, to_stage: str
    ):
        """Broadcast a pipeline stage change."""
        await self.broadcast(
            {
                "type": "pipeline_move",
                "data": {
                    "deal_id": deal_id,
                    "from_stage": from_stage,
                    "to_stage": to_stage,
                },
            }
        )

    async def broadcast_agent_status(
        self, agent_name: str, status: str, last_output: str = ""
    ):
        """Broadcast an agent status update."""
        await self.broadcast(
            {
                "type": "agent_status",
                "data": {
                    "agent_name": agent_name,
                    "status": status,
                    "last_output": last_output,
                },
            }
        )

    # ─── Heartbeat ────────────────────────────────────────

    async def _heartbeat_loop(self):
        """Send periodic pings to detect stale connections."""
        while self._connections:
            try:
                await asyncio.sleep(self.HEARTBEAT_INTERVAL)
                dead_clients: List[str] = []

                for client_id, conn in list(self._connections.items()):
                    try:
                        await self._send_json(
                            conn.websocket,
                            {
                                "type": "ping",
                                "timestamp": datetime.now().isoformat(),
                            },
                        )
                        conn.last_ping = time.time()
                    except Exception:
                        dead_clients.append(client_id)

                for cid in dead_clients:
                    self.disconnect(cid)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Heartbeat error: {e}")

    # ─── Handle incoming client messages ──────────────────

    async def handle_client_message(self, client_id: str, data: str):
        """Process an incoming message from a client."""
        try:
            msg = json.loads(data)
        except json.JSONDecodeError:
            return

        msg_type = msg.get("type", "")

        if msg_type == "pong":
            conn = self._connections.get(client_id)
            if conn:
                conn.last_ping = time.time()

        elif msg_type == "subscribe":
            # Client subscribes to specific event types
            conn = self._connections.get(client_id)
            if conn:
                channels = msg.get("channels", [])
                conn.subscriptions.update(channels)

        elif msg_type == "unsubscribe":
            conn = self._connections.get(client_id)
            if conn:
                channels = msg.get("channels", [])
                conn.subscriptions -= set(channels)

    # ─── Stats ────────────────────────────────────────────

    def get_connection_stats(self) -> Dict:
        """Get real-time connection statistics."""
        uptime = time.time() - self._start_time
        return {
            "active_connections": len(self._connections),
            "total_messages_sent": self._total_messages_sent,
            "uptime_seconds": int(uptime),
            "event_history_size": len(self._event_history),
            "clients": [
                {
                    "client_id": c.client_id,
                    "connected_seconds": int(time.time() - c.connected_at),
                    "messages_sent": c.messages_sent,
                    "subscriptions": list(c.subscriptions),
                }
                for c in self._connections.values()
            ],
        }

    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        """Get recent events from history buffer."""
        events = list(self._event_history)
        events.reverse()
        return events[:limit]


# ─── Singleton ────────────────────────────────────────────

_server_instance: Optional[RealtimeServer] = None


def get_realtime_server() -> RealtimeServer:
    """Get realtime server singleton."""
    global _server_instance
    if _server_instance is None:
        _server_instance = RealtimeServer()
    return _server_instance
