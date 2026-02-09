"""
Server-Sent Events (SSE) Endpoints - Fallback for environments where WebSocket isn't available.

Provides streaming event feeds as text/event-stream with auto-reconnect.
"""

import asyncio
import json
import logging
import time
from typing import AsyncGenerator, Optional
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sse", tags=["Server-Sent Events"])

# Retry interval hint for clients (milliseconds)
SSE_RETRY_MS = 5000
# How often to check for new events (seconds)
POLL_INTERVAL = 1.0


def _format_sse(data: str, event: Optional[str] = None, event_id: Optional[str] = None) -> str:
    """Format a message as an SSE frame."""
    lines = []
    if event_id:
        lines.append(f"id: {event_id}")
    if event:
        lines.append(f"event: {event}")
    for line in data.split("\n"):
        lines.append(f"data: {line}")
    lines.append("")
    lines.append("")
    return "\n".join(lines)


async def _event_generator(
    request: Request,
    event_filter: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Generate SSE events from the realtime server's event history.
    Yields new events as they appear, filtered by event type if specified.
    """
    from Engine8_Knowledge.realtime.ws_server import get_realtime_server

    server = get_realtime_server()

    # Send retry interval hint
    yield f"retry: {SSE_RETRY_MS}\n\n"

    # Send initial connection event
    yield _format_sse(
        json.dumps({
            "type": "connected",
            "filter": event_filter,
            "timestamp": datetime.now().isoformat(),
        }),
        event="connected",
    )

    last_seen = len(server._event_history)
    event_id = 0

    while True:
        # Check if client disconnected
        if await request.is_disconnected():
            break

        # Check for new events
        current_len = len(server._event_history)
        if current_len > last_seen:
            # Get new events since last check
            new_events = list(server._event_history)[last_seen:current_len]
            for evt in new_events:
                evt_type = evt.get("type", "event")

                # Apply filter
                if event_filter:
                    if event_filter == "pipeline" and evt_type != "pipeline_move":
                        continue
                    elif event_filter == "agents" and evt_type != "agent_status":
                        continue
                    elif event_filter == "alerts" and evt_type != "notification":
                        continue

                event_id += 1
                yield _format_sse(
                    json.dumps(evt),
                    event=evt_type,
                    event_id=str(event_id),
                )

            last_seen = current_len

        # Send keepalive comment every 15 seconds worth of polls
        await asyncio.sleep(POLL_INTERVAL)

        # Periodic keepalive (SSE comment)
        if event_id == 0 or int(time.time()) % 15 == 0:
            yield ": keepalive\n\n"


@router.get("/events")
async def sse_all_events(request: Request):
    """
    Stream all real-time events via SSE.
    Includes: events, notifications, metric updates, pipeline moves, agent status.
    """
    return StreamingResponse(
        _event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/pipeline")
async def sse_pipeline_events(request: Request):
    """Stream live pipeline stage changes via SSE."""
    return StreamingResponse(
        _event_generator(request, event_filter="pipeline"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/agents")
async def sse_agent_events(request: Request):
    """Stream agent execution status updates via SSE."""
    return StreamingResponse(
        _event_generator(request, event_filter="agents"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/alerts")
async def sse_alert_events(request: Request):
    """Stream hot lead alerts and compliance warnings via SSE."""
    return StreamingResponse(
        _event_generator(request, event_filter="alerts"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
