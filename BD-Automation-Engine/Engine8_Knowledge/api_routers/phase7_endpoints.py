"""
Phase 7 API Router - Production Hardening & Data Foundation

Endpoints:
  - GET  /data/freshness          - Collection freshness indicators
  - POST /notifications           - Create notification
  - GET  /notifications           - List notifications
  - PATCH /notifications/{id}/read - Mark notification read
  - POST /webhooks/jobs-scraped   - Webhook: new jobs
  - POST /webhooks/contracts-updated - Webhook: contract updates
  - POST /webhooks/contacts-enriched - Webhook: contact enrichment
  - POST /webhooks/alert          - Webhook: generic alert
  - POST /ai/memories             - Store entity memory
  - GET  /ai/memories/{entity_type}/{entity_name} - Retrieve memories
  - DELETE /ai/memories/{id}      - Remove memory
  - GET  /ai/costs                - LLM cost aggregation
"""

import os
import json
import sqlite3
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger("BDKnowledgeAPI.phase7")

router = APIRouter()

# =========================================
# FILE PATHS
# =========================================

DATA_DIR = Path(__file__).parent.parent / "data"
FRESHNESS_LOG = DATA_DIR / "freshness_log.json"
NOTIFICATIONS_DB = DATA_DIR / "notifications.db"
LLM_COSTS_LOG = DATA_DIR / "llm_costs.json"


# =========================================
# HELPERS
# =========================================

def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default: Any = None) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return default if default is not None else {}


def _write_json(path: Path, data: Any):
    _ensure_data_dir()
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _get_notifications_db() -> sqlite3.Connection:
    _ensure_data_dir()
    conn = sqlite3.connect(str(NOTIFICATIONS_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            created_at TEXT NOT NULL,
            read_at TEXT,
            priority TEXT DEFAULT 'info'
        )
    """)
    conn.commit()
    return conn


def _create_notification(
    notif_type: str,
    title: str,
    message: str,
    entity_type: str = None,
    entity_id: str = None,
    priority: str = "info",
) -> dict:
    """Insert a notification and return it."""
    conn = _get_notifications_db()
    try:
        notif_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()
        conn.execute(
            """INSERT INTO notifications (id, type, title, message, entity_type, entity_id, created_at, priority)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (notif_id, notif_type, title, message, entity_type, entity_id, now, priority),
        )
        conn.commit()
        return {
            "id": notif_id,
            "type": notif_type,
            "title": title,
            "message": message,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "created_at": now,
            "read_at": None,
            "priority": priority,
        }
    finally:
        conn.close()


def _update_freshness(collection: str, count: int = 0, source: str = "api"):
    """Update the freshness log for a given collection/source."""
    log = _read_json(FRESHNESS_LOG, {"collections": {}, "scraper_last_run": None, "tango_last_sync": None})
    now = datetime.utcnow().isoformat()
    if collection in ("scraper_last_run", "tango_last_sync"):
        log[collection] = now
    else:
        log.setdefault("collections", {})[collection] = {
            "count": count,
            "last_indexed": now,
            "source": source,
        }
    _write_json(FRESHNESS_LOG, log)


# =========================================
# PYDANTIC MODELS
# =========================================

class NotificationCreate(BaseModel):
    type: str = Field(..., description="Notification type: new_jobs, contract_alert, stale_data, meeting_reminder, outreach_response")
    title: str = Field(..., description="Short title")
    message: str = Field(..., description="Notification body")
    entity_type: Optional[str] = Field(None, description="Related entity type (contact, program, job)")
    entity_id: Optional[str] = Field(None, description="Related entity ID")
    priority: str = Field("info", description="Priority: info, warning, critical")


class WebhookJobsScraped(BaseModel):
    source: str = Field("apify", description="Scraper source")
    count: int = Field(..., description="Number of jobs scraped")
    run_id: str = Field("", description="Pipeline run ID")


class WebhookContractsUpdated(BaseModel):
    source: str = Field("tango", description="Source system")
    new_awards: int = Field(0)
    modifications: int = Field(0)


class WebhookContactsEnriched(BaseModel):
    source: str = Field("zoominfo", description="Enrichment source")
    count: int = Field(..., description="Number enriched")
    program: str = Field("", description="Related program")


class WebhookAlert(BaseModel):
    level: str = Field("warning", description="Alert level: info, warning, critical")
    title: str = Field(...)
    message: str = Field(...)
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None


class MemoryCreate(BaseModel):
    entity_type: str = Field(..., description="contact or program")
    entity_name: str = Field(..., description="Entity name")
    summary: str = Field(..., description="Memory content")
    confidence: float = Field(0.8, ge=0.0, le=1.0)


class LLMCostEntry(BaseModel):
    timestamp: str
    endpoint: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


# =========================================
# TASK 1: DATA FRESHNESS
# =========================================

@router.get("/data/freshness")
async def get_data_freshness():
    """Return freshness indicators for each data source and collection."""
    # Try to get live Qdrant stats
    try:
        from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
        qdrant_url = os.getenv("QDRANT_URL")
        store = BDKnowledgeStore(url=qdrant_url)
        collection_stats = store.get_collection_stats()
    except Exception:
        collection_stats = {}

    log = _read_json(FRESHNESS_LOG, {"collections": {}, "scraper_last_run": None, "tango_last_sync": None})
    now = datetime.utcnow()

    collections_out = {}
    for name, stats in collection_stats.items():
        if not isinstance(stats, dict):
            continue
        count = stats.get("points_count", 0)
        # Get last indexed time from log
        log_entry = log.get("collections", {}).get(name, {})
        last_indexed = log_entry.get("last_indexed")
        if last_indexed:
            try:
                indexed_dt = datetime.fromisoformat(last_indexed.replace("Z", "+00:00").replace("+00:00", ""))
            except (ValueError, TypeError):
                indexed_dt = None
        else:
            indexed_dt = None

        staleness_days = (now - indexed_dt).days if indexed_dt else -1
        collections_out[name] = {
            "count": count,
            "last_indexed": last_indexed,
            "staleness_days": staleness_days if staleness_days >= 0 else None,
            "status": stats.get("status", "unknown"),
        }

    # Generate alerts
    alerts = []
    for cname, cinfo in collections_out.items():
        sd = cinfo.get("staleness_days")
        if sd is None or sd < 0:
            alerts.append({"level": "info", "message": f"{cname} has no freshness data recorded"})
        elif sd > 14:
            alerts.append({"level": "critical", "message": f"{cname} collection is {sd} days stale"})
        elif sd > 7:
            alerts.append({"level": "warning", "message": f"{cname} collection is {sd} days stale"})
        elif sd == 0:
            alerts.append({"level": "info", "message": f"{cname} refreshed today"})

    return {
        "collections": collections_out,
        "scraper_last_run": log.get("scraper_last_run"),
        "tango_last_sync": log.get("tango_last_sync"),
        "alerts": alerts,
        "timestamp": now.isoformat(),
    }


# =========================================
# TASK 2: NOTIFICATIONS
# =========================================

@router.post("/notifications")
async def create_notification(body: NotificationCreate):
    """Store a new notification."""
    notif = _create_notification(
        notif_type=body.type,
        title=body.title,
        message=body.message,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        priority=body.priority,
    )
    return notif


@router.get("/notifications")
async def list_notifications(
    unread: bool = Query(False, description="Only unread notifications"),
    limit: int = Query(50, ge=1, le=200),
):
    """List notifications, optionally filtered to unread."""
    conn = _get_notifications_db()
    try:
        if unread:
            rows = conn.execute(
                "SELECT * FROM notifications WHERE read_at IS NULL ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return {
            "notifications": [dict(r) for r in rows],
            "count": len(rows),
        }
    finally:
        conn.close()


@router.patch("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str):
    """Mark a single notification as read."""
    conn = _get_notifications_db()
    try:
        now = datetime.utcnow().isoformat()
        cur = conn.execute(
            "UPDATE notifications SET read_at = ? WHERE id = ?",
            (now, notif_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"success": True, "id": notif_id, "read_at": now}
    finally:
        conn.close()


# =========================================
# TASK 3: WEBHOOK RECEIVERS
# =========================================

@router.post("/webhooks/jobs-scraped")
async def webhook_jobs_scraped(body: WebhookJobsScraped):
    """Receive webhook when new jobs are scraped."""
    _update_freshness("jobs", count=body.count, source=body.source)
    _update_freshness("scraper_last_run")
    notif = _create_notification(
        notif_type="new_jobs",
        title=f"{body.count} new jobs scraped",
        message=f"Source: {body.source}, Run ID: {body.run_id}",
        priority="info",
    )
    return {"success": True, "notification": notif}


@router.post("/webhooks/contracts-updated")
async def webhook_contracts_updated(body: WebhookContractsUpdated):
    """Receive webhook when contracts are updated."""
    total = body.new_awards + body.modifications
    _update_freshness("programs", count=total, source=body.source)
    _update_freshness("tango_last_sync")
    notif = _create_notification(
        notif_type="contract_alert",
        title=f"{total} contract changes detected",
        message=f"New awards: {body.new_awards}, Modifications: {body.modifications} (Source: {body.source})",
        priority="warning" if body.new_awards > 0 else "info",
    )
    return {"success": True, "notification": notif}


@router.post("/webhooks/contacts-enriched")
async def webhook_contacts_enriched(body: WebhookContactsEnriched):
    """Receive webhook when contacts are enriched."""
    _update_freshness("contacts", count=body.count, source=body.source)
    notif = _create_notification(
        notif_type="contact_enriched",
        title=f"{body.count} contacts enriched",
        message=f"Source: {body.source}" + (f", Program: {body.program}" if body.program else ""),
        entity_type="program" if body.program else None,
        entity_id=body.program if body.program else None,
        priority="info",
    )
    return {"success": True, "notification": notif}


@router.post("/webhooks/alert")
async def webhook_alert(body: WebhookAlert):
    """Generic alert webhook from any external source."""
    notif = _create_notification(
        notif_type="external_alert",
        title=body.title,
        message=body.message,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        priority=body.level,
    )
    return {"success": True, "notification": notif}


# =========================================
# TASK 4: CROSS-SESSION MEMORY
# =========================================

@router.post("/ai/memories")
async def store_memory(body: MemoryCreate):
    """Store an AI memory for an entity."""
    try:
        from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
        qdrant_url = os.getenv("QDRANT_URL")
        store = BDKnowledgeStore(url=qdrant_url)

        # Ensure memories collection exists
        try:
            store.client.get_collection("memories")
        except Exception:
            from qdrant_client.models import VectorParams, Distance
            store.client.create_collection(
                collection_name="memories",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

        memory_id = str(uuid.uuid4())[:12]
        embedding = store._generate_embedding(
            f"{body.entity_type}: {body.entity_name} - {body.summary}"
        )

        store.client.upsert(
            collection_name="memories",
            points=[{
                "id": memory_id,
                "vector": embedding,
                "payload": {
                    "entity_type": body.entity_type,
                    "entity_name": body.entity_name,
                    "summary": body.summary,
                    "confidence": body.confidence,
                    "last_updated": datetime.utcnow().isoformat(),
                    "source_interaction": "dashboard",
                },
            }],
        )
        return {
            "success": True,
            "id": memory_id,
            "entity_name": body.entity_name,
        }
    except Exception as e:
        logger.error(f"Store memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/memories/{entity_type}/{entity_name}")
async def get_entity_memories(entity_type: str, entity_name: str, limit: int = Query(20, ge=1, le=100)):
    """Retrieve AI memories for a specific entity."""
    try:
        from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        qdrant_url = os.getenv("QDRANT_URL")
        store = BDKnowledgeStore(url=qdrant_url)

        # Check if collection exists
        try:
            store.client.get_collection("memories")
        except Exception:
            return {"memories": [], "count": 0, "entity_name": entity_name}

        results, _ = store.client.scroll(
            collection_name="memories",
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="entity_type", match=MatchValue(value=entity_type)),
                    FieldCondition(key="entity_name", match=MatchValue(value=entity_name)),
                ]
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        memories = []
        for point in results:
            payload = point.payload or {}
            memories.append({
                "id": str(point.id),
                "entity_type": payload.get("entity_type", ""),
                "entity_name": payload.get("entity_name", ""),
                "summary": payload.get("summary", ""),
                "confidence": payload.get("confidence", 0),
                "last_updated": payload.get("last_updated", ""),
                "source_interaction": payload.get("source_interaction", ""),
            })

        return {
            "memories": memories,
            "count": len(memories),
            "entity_name": entity_name,
        }
    except Exception as e:
        logger.error(f"Get memories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/ai/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a specific AI memory."""
    try:
        from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
        qdrant_url = os.getenv("QDRANT_URL")
        store = BDKnowledgeStore(url=qdrant_url)
        store.client.delete(
            collection_name="memories",
            points_selector=[memory_id],
        )
        return {"success": True, "deleted_id": memory_id}
    except Exception as e:
        logger.error(f"Delete memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# TASK 5: LLM COST TRACKING
# =========================================

@router.get("/ai/costs")
async def get_llm_costs(days: int = Query(30, ge=1, le=365)):
    """Return aggregated LLM cost data."""
    entries: List[dict] = _read_json(LLM_COSTS_LOG, [])
    if not isinstance(entries, list):
        entries = []

    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    filtered = [e for e in entries if e.get("timestamp", "") >= cutoff]

    # Aggregate by day
    daily: Dict[str, Dict[str, Any]] = {}
    by_endpoint: Dict[str, float] = {}
    total_cost = 0.0
    total_input = 0
    total_output = 0

    for e in filtered:
        day = e.get("timestamp", "")[:10]
        cost = e.get("cost_usd", 0)
        inp = e.get("input_tokens", 0)
        out = e.get("output_tokens", 0)
        ep = e.get("endpoint", "unknown")

        daily.setdefault(day, {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "queries": 0})
        daily[day]["input_tokens"] += inp
        daily[day]["output_tokens"] += out
        daily[day]["cost_usd"] += cost
        daily[day]["queries"] += 1

        by_endpoint[ep] = by_endpoint.get(ep, 0) + cost
        total_cost += cost
        total_input += inp
        total_output += out

    daily_list = [{"date": k, **v} for k, v in sorted(daily.items())]

    # Project 30-day spend from recent data
    recent_days = min(days, len(daily_list)) or 1
    avg_daily = total_cost / recent_days if recent_days > 0 else 0
    projected_30d = avg_daily * 30

    return {
        "daily": daily_list,
        "by_endpoint": [{"endpoint": k, "cost_usd": round(v, 4)} for k, v in sorted(by_endpoint.items(), key=lambda x: -x[1])],
        "recent_queries": filtered[-50:] if len(filtered) > 50 else filtered,
        "summary": {
            "total_cost_usd": round(total_cost, 4),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_queries": len(filtered),
            "projected_30d_usd": round(projected_30d, 4),
            "period_days": days,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


def log_llm_cost(endpoint: str, model: str, input_tokens: int, output_tokens: int, cost_usd: float):
    """Utility to log an LLM cost entry (called from middleware)."""
    entries: list = _read_json(LLM_COSTS_LOG, [])
    if not isinstance(entries, list):
        entries = []
    entries.append({
        "timestamp": datetime.utcnow().isoformat(),
        "endpoint": endpoint,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost_usd, 6),
    })
    # Keep last 10000 entries
    if len(entries) > 10000:
        entries = entries[-10000:]
    _write_json(LLM_COSTS_LOG, entries)
