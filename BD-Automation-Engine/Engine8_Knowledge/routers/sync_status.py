"""Sync status router -- exposes sync engine state and manual trigger endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger("BDKnowledgeAPI")

router = APIRouter(prefix="/sync", tags=["Sync Status"])


def _get_engine():
    """Import and return the sync engine singleton.

    Lazy import avoids circular dependencies when the router module
    is loaded before the services package is fully initialized.
    """
    from services.sync_engine import get_sync_engine
    return get_sync_engine()


@router.get("/status")
async def sync_status():
    """Current sync engine status across all sources."""
    engine = _get_engine()
    return engine.get_sync_status()


@router.post("/trigger")
async def trigger_sync():
    """Manually trigger a full sync cycle (Notion + Bullhorn + Qdrant)."""
    engine = _get_engine()
    try:
        result = await engine.sync_once()
        return {"triggered": True, "result": result}
    except Exception as e:
        logger.error(f"Manual sync trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/{source}")
async def trigger_sync_source(source: str):
    """Trigger sync for a specific source (notion or bullhorn).

    This runs only the polling step for the given source, then upserts
    any changed records into Qdrant.
    """
    engine = _get_engine()

    if source == "notion":
        try:
            changes = await engine._poll_notion_changes()
            qdrant_result = {}
            if changes:
                qdrant_result = await engine._upsert_notion_to_qdrant(changes)
            engine._save_state()
            return {
                "triggered": True,
                "source": source,
                "records_found": len(changes),
                "qdrant": qdrant_result,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    if source == "bullhorn":
        try:
            changes = await engine._poll_bullhorn_changes()
            qdrant_result = {}
            if changes:
                qdrant_result = await engine._upsert_bullhorn_to_qdrant(changes)
            engine._save_state()
            return {
                "triggered": True,
                "source": source,
                "records_found": len(changes),
                "qdrant": qdrant_result,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(
        status_code=400,
        detail=f"Unknown source: {source}. Use 'notion' or 'bullhorn'.",
    )


@router.get("/history")
async def sync_history(limit: int = 50):
    """Recent sync history (last 50 cycles by default)."""
    engine = _get_engine()
    return {"history": engine.get_sync_history(limit=limit)}


@router.get("/retry-queue")
async def retry_queue():
    """Items currently in the retry queue."""
    engine = _get_engine()
    queue = engine.get_retry_queue()
    return {"retry_queue": queue, "count": len(queue)}


@router.post("/retry-queue/clear")
async def clear_retry_queue():
    """Clear all items from the retry queue."""
    engine = _get_engine()
    cleared = engine.clear_retry_queue()
    return {"cleared": cleared}
