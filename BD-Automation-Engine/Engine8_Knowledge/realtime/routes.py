"""
Real-Time Routes - Mount WebSocket, SSE, and status endpoints.

Prefix: /realtime (HTTP) + /ws/dashboard (WebSocket)
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from Engine8_Knowledge.realtime.ws_server import get_realtime_server
from Engine8_Knowledge.realtime.sse_endpoints import router as sse_router

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Real-Time"])

# Include SSE sub-router
router.include_router(sse_router)


# ─── WebSocket endpoint ──────────────────────────────────

@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    Main WebSocket endpoint for live dashboard updates.
    Clients connect here for real-time event streaming.
    """
    server = get_realtime_server()
    client_id = await server.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            await server.handle_client_message(client_id, data)
    except WebSocketDisconnect:
        server.disconnect(client_id)
    except Exception as e:
        logger.warning(f"WebSocket error for {client_id}: {e}")
        server.disconnect(client_id)


# ─── Status endpoint ─────────────────────────────────────

@router.get("/realtime/status")
async def realtime_status():
    """Get real-time server connection stats and event throughput."""
    server = get_realtime_server()
    stats = server.get_connection_stats()

    # Compute events/minute from recent history
    events = server.get_recent_events(50)
    events_per_min = 0
    if events:
        import time
        from datetime import datetime
        try:
            newest = datetime.fromisoformat(events[0].get("timestamp", ""))
            oldest = datetime.fromisoformat(events[-1].get("timestamp", ""))
            span_seconds = max(1, (newest - oldest).total_seconds())
            events_per_min = round(len(events) / (span_seconds / 60), 1)
        except (ValueError, TypeError):
            events_per_min = 0

    stats["events_per_minute"] = events_per_min
    return stats


@router.get("/realtime/events")
async def realtime_recent_events(limit: int = 50):
    """Get recent events from the history buffer."""
    server = get_realtime_server()
    return {"events": server.get_recent_events(limit)}


@router.post("/realtime/broadcast")
async def realtime_broadcast_test(
    event_type: str = "test",
    message: str = "Test broadcast",
):
    """Broadcast a test event (for debugging)."""
    server = get_realtime_server()
    await server.broadcast_event(event_type, {"message": message})
    return {"success": True, "active_connections": len(server._connections)}
