"""
Phase 31A: Streaming API — 14 REST + 4 WebSocket endpoints.

REST:
  GET    /streaming/stats                         — Stream statistics
  GET    /streaming/streams                       — List all configured streams
  GET    /streaming/streams/{name}/peek           — Peek at latest N events
  POST   /streaming/streams/{name}/replay         — Replay events from a time range
  GET    /streaming/processors                    — List event processors
  POST   /streaming/processors/{id}/restart       — Restart a failed processor
  GET    /streaming/workflows                     — List registered workflows
  POST   /streaming/workflows/{id}/trigger        — Manually trigger a workflow
  GET    /streaming/workflows/executions          — Active workflow executions
  GET    /streaming/executions/{id}               — Execution status + step details
  GET    /streaming/event-chain/{correlation_id}  — Trace event chain
  GET    /streaming/websocket/connections         — WebSocket connection stats
  POST   /streaming/publish                       — Publish event to stream (admin)
  GET    /streaming/health                        — Overall streaming health

WebSocket:
  /ws/dashboard   — Live dashboard feed
  /ws/campaigns   — Campaign updates
  /ws/alerts      — Alert-only feed
  /ws/system      — System health
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket
from pydantic import BaseModel, Field

from src.streaming.event_bus import Event, EventBus, get_event_bus
from src.streaming.processors import EventProcessorRegistry
from src.streaming.stream_orchestrator import StreamOrchestrator
from src.streaming.websocket_server import RealtimeServer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/streaming", tags=["streaming-v2"])


# =========================================
# REQUEST/RESPONSE MODELS
# =========================================


class PublishRequest(BaseModel):
    """Request to publish an event to a stream."""

    stream: str = Field(..., description="Target stream name")
    event_type: str = Field(..., description="Event type identifier")
    source: str = Field(default="admin", description="Event source")
    payload: dict = Field(default_factory=dict, description="Event payload data")
    priority: str = Field(default="medium", description="Event priority")
    metadata: dict = Field(default_factory=dict, description="Event metadata")


class ReplayRequest(BaseModel):
    """Request to replay events from a stream."""

    start_id: str = Field(default="0", description="Start message ID or timestamp")
    end_id: str = Field(default="+", description="End message ID or timestamp")
    count: int = Field(default=100, ge=1, le=1000, description="Max events to return")


class TriggerWorkflowRequest(BaseModel):
    """Request to manually trigger a workflow."""

    event_type: str = Field(default="manual.trigger", description="Trigger event type")
    payload: dict = Field(default_factory=dict, description="Trigger event payload")
    priority: str = Field(default="medium", description="Trigger priority")


class StreamInfoResponse(BaseModel):
    """Response for stream list."""

    name: str
    max_len: int
    consumer_groups: List[str]
    retention_hours: int


class EventResponse(BaseModel):
    """Serialized event for API responses."""

    event_id: str
    event_type: str
    source: str
    timestamp: str
    payload: dict
    metadata: dict
    priority: str


class HealthResponse(BaseModel):
    """Streaming system health."""

    status: str
    redis_connected: bool
    streams_active: int
    processors_running: int
    websocket_connections: int
    workflows_registered: int
    active_executions: int
    timestamp: str


# =========================================
# MODULE-LEVEL STATE (set during app startup)
# =========================================

_event_bus: Optional[EventBus] = None
_processor_registry: Optional[EventProcessorRegistry] = None
_orchestrator: Optional[StreamOrchestrator] = None
_realtime_server: Optional[RealtimeServer] = None


def configure_streaming(
    event_bus: EventBus,
    processor_registry: EventProcessorRegistry,
    orchestrator: StreamOrchestrator,
    realtime_server: RealtimeServer,
) -> None:
    """Wire up streaming components. Called during app startup."""
    global _event_bus, _processor_registry, _orchestrator, _realtime_server
    _event_bus = event_bus
    _processor_registry = processor_registry
    _orchestrator = orchestrator
    _realtime_server = realtime_server


def _get_bus() -> EventBus:
    if _event_bus is None:
        raise HTTPException(status_code=503, detail="Streaming not initialized")
    return _event_bus


def _get_registry() -> EventProcessorRegistry:
    if _processor_registry is None:
        raise HTTPException(status_code=503, detail="Processors not initialized")
    return _processor_registry


def _get_orchestrator() -> StreamOrchestrator:
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return _orchestrator


def _get_ws_server() -> RealtimeServer:
    if _realtime_server is None:
        raise HTTPException(status_code=503, detail="WebSocket server not initialized")
    return _realtime_server


def _event_to_response(event: Event) -> dict:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "source": event.source,
        "timestamp": event.timestamp.isoformat(),
        "payload": event.payload,
        "metadata": event.metadata,
        "priority": event.priority,
    }


# =========================================
# REST ENDPOINTS (14)
# =========================================


@router.get("/stats")
async def get_stream_stats() -> Dict[str, Any]:
    """Get statistics for all streams."""
    bus = _get_bus()
    stats = await bus.get_stream_stats()
    return {
        "streams": {name: s.model_dump() for name, s in stats.items()},
        "total_streams": len(stats),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/streams")
async def list_streams() -> Dict[str, Any]:
    """List all configured streams."""
    bus = _get_bus()
    streams = []
    for name, config in bus.STREAM_DEFINITIONS.items():
        streams.append(
            {
                "name": config.name,
                "max_len": config.max_len,
                "consumer_groups": config.consumer_groups,
                "retention_hours": config.retention_hours,
            }
        )
    return {"streams": streams, "total": len(streams)}


@router.get("/streams/{name}/peek")
async def peek_stream(
    name: str,
    count: int = Query(
        default=10, ge=1, le=100, description="Number of events to peek"
    ),
) -> Dict[str, Any]:
    """Peek at the latest N events in a stream."""
    bus = _get_bus()
    if name not in bus.STREAM_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Stream not found: {name}")

    events = await bus.replay(name, start_id="0", end_id="+", count=count)
    return {
        "stream": name,
        "events": [_event_to_response(e) for e in events],
        "count": len(events),
    }


@router.post("/streams/{name}/replay")
async def replay_stream(name: str, request: ReplayRequest) -> Dict[str, Any]:
    """Replay events from a stream within a time range."""
    bus = _get_bus()
    if name not in bus.STREAM_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Stream not found: {name}")

    events = await bus.replay(
        name,
        start_id=request.start_id,
        end_id=request.end_id,
        count=request.count,
    )
    return {
        "stream": name,
        "events": [_event_to_response(e) for e in events],
        "count": len(events),
        "request": request.model_dump(),
    }


@router.get("/processors")
async def list_processors() -> Dict[str, Any]:
    """List all event processors and their status."""
    registry = _get_registry()
    statuses = registry.get_all_status()
    return {"processors": statuses, "total": len(statuses)}


@router.post("/processors/{processor_id}/restart")
async def restart_processor(processor_id: str) -> Dict[str, Any]:
    """Restart a failed processor."""
    registry = _get_registry()
    success = await registry.restart_processor(processor_id)
    if not success:
        raise HTTPException(
            status_code=404, detail=f"Processor not found: {processor_id}"
        )
    return {"status": "restarted", "processor": processor_id}


@router.get("/workflows")
async def list_workflows() -> Dict[str, Any]:
    """List all registered event workflows."""
    orchestrator = _get_orchestrator()
    workflows = orchestrator.get_registered_workflows()
    return {"workflows": workflows, "total": len(workflows)}


@router.post("/workflows/{workflow_id}/trigger")
async def trigger_workflow(
    workflow_id: str, request: TriggerWorkflowRequest
) -> Dict[str, Any]:
    """Manually trigger a workflow."""
    orchestrator = _get_orchestrator()
    if workflow_id not in orchestrator.workflows:
        raise HTTPException(
            status_code=404, detail=f"Workflow not found: {workflow_id}"
        )

    trigger_event = Event(
        event_type=request.event_type,
        source="admin",
        payload=request.payload,
        priority=request.priority,
    )

    execution_id = await orchestrator.trigger_workflow(workflow_id, trigger_event)
    return {
        "status": "triggered",
        "workflow_id": workflow_id,
        "execution_id": execution_id,
    }


@router.get("/workflows/executions")
async def list_executions(
    limit: int = Query(default=50, ge=1, le=200),
) -> Dict[str, Any]:
    """List workflow executions (recent first)."""
    orchestrator = _get_orchestrator()
    executions = await orchestrator.list_all_executions(limit=limit)
    return {
        "executions": [ex.model_dump() for ex in executions],
        "total": len(executions),
    }


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str) -> Dict[str, Any]:
    """Get detailed status of a workflow execution."""
    orchestrator = _get_orchestrator()
    execution = await orchestrator.get_execution_status(execution_id)
    if not execution:
        raise HTTPException(
            status_code=404, detail=f"Execution not found: {execution_id}"
        )
    return execution.model_dump()


@router.get("/event-chain/{correlation_id}")
async def get_event_chain(correlation_id: str) -> Dict[str, Any]:
    """Trace an event through its full processing chain."""
    bus = _get_bus()
    events = await bus.get_event_chain(correlation_id)
    return {
        "correlation_id": correlation_id,
        "events": [_event_to_response(e) for e in events],
        "chain_length": len(events),
    }


@router.get("/websocket/connections")
async def get_websocket_connections() -> Dict[str, Any]:
    """Get WebSocket connection statistics."""
    server = _get_ws_server()
    return await server.get_connection_stats()


@router.post("/publish")
async def publish_event(request: PublishRequest) -> Dict[str, Any]:
    """Publish an event to a stream (admin/testing)."""
    bus = _get_bus()
    if request.stream not in bus.STREAM_DEFINITIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown stream: {request.stream}. Valid streams: {list(bus.STREAM_DEFINITIONS.keys())}",
        )

    event = Event(
        event_type=request.event_type,
        source=request.source,
        payload=request.payload,
        priority=request.priority,
        metadata=request.metadata,
    )
    msg_id = await bus.publish(request.stream, event)
    decoded_id = msg_id.decode() if isinstance(msg_id, bytes) else msg_id
    return {
        "status": "published",
        "stream": request.stream,
        "event_id": event.event_id,
        "message_id": decoded_id,
    }


@router.get("/health")
async def streaming_health() -> Dict[str, Any]:
    """Overall streaming system health."""
    bus = _get_bus()
    redis_ok = False
    streams_active = 0

    try:
        if bus.redis:
            await bus.redis.ping()
            redis_ok = True
            # Count non-empty streams
            for stream_name in bus.STREAM_DEFINITIONS:
                try:
                    length = await bus.get_stream_length(stream_name)
                    if length > 0:
                        streams_active += 1
                except Exception:
                    pass
    except Exception:
        pass

    processors_running = 0
    if _processor_registry:
        processors_running = sum(
            1 for s in _processor_registry.get_all_status() if s.get("running")
        )

    ws_connections = 0
    if _realtime_server:
        stats = await _realtime_server.get_connection_stats()
        ws_connections = stats.get("total_connections", 0)

    workflows_count = len(_orchestrator.workflows) if _orchestrator else 0
    active_execs = 0
    if _orchestrator:
        active = await _orchestrator.list_active_workflows()
        active_execs = len(active)

    status = "healthy" if redis_ok else "degraded"

    return {
        "status": status,
        "redis_connected": redis_ok,
        "streams_active": streams_active,
        "processors_running": processors_running,
        "websocket_connections": ws_connections,
        "workflows_registered": workflows_count,
        "active_executions": active_execs,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =========================================
# WEBSOCKET ENDPOINTS (4)
# =========================================


@router.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket):
    """WebSocket: live dashboard feed."""
    server = _get_ws_server()
    await server.handle_websocket(websocket, "dashboard")


@router.websocket("/ws/campaigns")
async def ws_campaigns(websocket: WebSocket):
    """WebSocket: campaign updates."""
    server = _get_ws_server()
    await server.handle_websocket(websocket, "campaigns")


@router.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    """WebSocket: alert-only feed."""
    server = _get_ws_server()
    await server.handle_websocket(websocket, "alerts")


@router.websocket("/ws/system")
async def ws_system(websocket: WebSocket):
    """WebSocket: system health."""
    server = _get_ws_server()
    await server.handle_websocket(websocket, "system")


# =========================================
# ROUTER INTEGRATION HELPER
# =========================================


def include_streaming_v2_router(
    app, event_bus=None, redis_url="redis://localhost:6379"
):
    """
    Include the Phase 31A streaming router in the main FastAPI app.

    Usage:
        from src.api.streaming_api import include_streaming_v2_router
        include_streaming_v2_router(app)
    """
    if event_bus is None:
        event_bus = get_event_bus(redis_url)

    processor_registry = EventProcessorRegistry(event_bus)
    orchestrator = StreamOrchestrator(event_bus)
    realtime_server = RealtimeServer(event_bus)

    configure_streaming(event_bus, processor_registry, orchestrator, realtime_server)
    app.include_router(router)
    logger.info(
        "Phase 31A streaming routes enabled: /streaming/* (14 REST + 4 WebSocket)"
    )
