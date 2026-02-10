"""
Phase 31A: Real-Time Event Streaming Infrastructure.

Redis Streams-based event bus connecting all platform services into a
unified real-time intelligence mesh. Every scrape result, contact update,
campaign action, contract alert, and anomaly detection flows through the
bus as structured events.

Components:
- EventBus: Central pub/sub with 15 streams, consumer groups, replay
- EventProcessorRegistry: 6 real-time processors reacting to intelligence signals
- RealtimeServer: WebSocket server for live dashboard updates
- StreamOrchestrator: Multi-step workflow orchestration triggered by events
"""

from src.streaming.event_bus import EventBus, Event, StreamConfig, StreamStats
from src.streaming.processors import EventProcessorRegistry
from src.streaming.websocket_server import RealtimeServer
from src.streaming.stream_orchestrator import StreamOrchestrator

__all__ = [
    "EventBus",
    "Event",
    "StreamConfig",
    "StreamStats",
    "EventProcessorRegistry",
    "RealtimeServer",
    "StreamOrchestrator",
]
