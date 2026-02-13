"""
Unified API endpoints for the BD Intelligence Hub.

These endpoints provide unified access to all Qdrant collections
and are the primary interface for the dashboard and external tools.
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.security import APIKeyHeader
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from openai import OpenAI
import structlog
import os

# Import settings if available
try:
    from config.settings import get_settings
    settings = get_settings()
except ImportError:
    settings = None

# Import retry utilities
try:
    from utils.llm_retry import openai_retry
except ImportError:
    def openai_retry(func):
        return func

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v2", tags=["unified"])

# API Key security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify API key if configured."""
    hub_api_key = os.environ.get("HUB_API_KEY", "")
    if not hub_api_key:
        return True  # No key configured = open access (dev mode)
    if api_key != hub_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


def get_qdrant() -> QdrantClient:
    """Get Qdrant client instance."""
    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    return QdrantClient(url=qdrant_url)


@openai_retry
def get_embedding(text: str) -> list:
    """Get embedding for search query."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


# ====== UNIFIED SEARCH ======

@router.get("/search")
async def unified_search(
    query: str = Query(..., min_length=2),
    collections: Optional[str] = Query(None, description="Comma-separated collection names"),
    limit: int = Query(10, ge=1, le=100),
    _authenticated: bool = Depends(verify_api_key),
):
    """
    Search across all or specific unified collections.

    Returns results from multiple collections sorted by relevance score.
    """
    qdrant = get_qdrant()
    embedding = get_embedding(query)

    target_collections = collections.split(",") if collections else [
        "contacts", "programs", "jobs",
        "activities", "documents"
    ]

    results = []
    for coll in target_collections:
        coll = coll.strip()
        try:
            response = qdrant.query_points(
                collection_name=coll,
                query=embedding,
                limit=limit,
            )
            for hit in response.points:
                results.append({
                    "collection": coll,
                    "score": hit.score,
                    "id": str(hit.id),
                    "payload": hit.payload,
                })
        except Exception as e:
            logger.warning("search_collection_failed", collection=coll, error=str(e))

    # Sort by score across all collections
    results.sort(key=lambda x: x["score"], reverse=True)

    logger.info("unified_search", query=query, results_count=len(results))
    return {"results": results[:limit], "total": len(results), "query": query}


# ====== CONTACTS ======

@router.get("/contacts")
async def list_contacts(
    program: Optional[str] = None,
    tier: Optional[str] = None,
    priority: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _authenticated: bool = Depends(verify_api_key),
):
    """List contacts with filtering."""
    qdrant = get_qdrant()

    must_conditions = []
    if program:
        must_conditions.append(FieldCondition(key="program", match=MatchValue(value=program)))
    if tier:
        must_conditions.append(FieldCondition(key="hierarchy_tier", match=MatchValue(value=tier)))
    if priority:
        must_conditions.append(FieldCondition(key="bd_priority", match=MatchValue(value=priority)))
    if location:
        must_conditions.append(FieldCondition(key="location_hub", match=MatchValue(value=location)))

    filter_obj = Filter(must=must_conditions) if must_conditions else None

    try:
        results, next_offset = qdrant.scroll(
            collection_name="contacts",
            scroll_filter=filter_obj,
            limit=limit,
            offset=offset,
            with_payload=True,
        )

        return {
            "contacts": [{"id": str(p.id), **p.payload} for p in results],
            "total": len(results),
            "next_offset": next_offset,
        }
    except Exception as e:
        logger.error("list_contacts_failed", error=str(e))
        return {"contacts": [], "total": 0, "error": str(e)}


@router.get("/contacts/search")
async def search_contacts(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
    _authenticated: bool = Depends(verify_api_key),
):
    """Semantic search across contacts."""
    qdrant = get_qdrant()
    embedding = get_embedding(query)

    try:
        response = qdrant.query_points(
            collection_name="contacts",
            query=embedding,
            limit=limit,
        )

        return {
            "results": [{"id": str(h.id), "score": h.score, **h.payload} for h in response.points],
            "query": query,
        }
    except Exception as e:
        logger.error("search_contacts_failed", error=str(e))
        return {"results": [], "query": query, "error": str(e)}


# ====== PROGRAMS ======

@router.get("/programs")
async def list_programs(
    prime: Optional[str] = None,
    pts_involvement: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    _authenticated: bool = Depends(verify_api_key),
):
    """List federal programs with filtering."""
    qdrant = get_qdrant()

    must_conditions = []
    if prime:
        must_conditions.append(FieldCondition(key="prime_contractor", match=MatchValue(value=prime)))
    if pts_involvement:
        must_conditions.append(FieldCondition(key="pts_involvement", match=MatchValue(value=pts_involvement)))
    if priority:
        must_conditions.append(FieldCondition(key="priority_level", match=MatchValue(value=priority)))

    filter_obj = Filter(must=must_conditions) if must_conditions else None

    try:
        results, _ = qdrant.scroll(
            collection_name="programs",
            scroll_filter=filter_obj,
            limit=limit,
            with_payload=True,
        )

        return {"programs": [{"id": str(p.id), **p.payload} for p in results], "total": len(results)}
    except Exception as e:
        logger.error("list_programs_failed", error=str(e))
        return {"programs": [], "total": 0, "error": str(e)}


# ====== JOBS ======

@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    program: Optional[str] = None,
    clearance: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    _authenticated: bool = Depends(verify_api_key),
):
    """List jobs with filtering."""
    qdrant = get_qdrant()

    must_conditions = []
    if status:
        must_conditions.append(FieldCondition(key="status", match=MatchValue(value=status)))
    if program:
        must_conditions.append(FieldCondition(key="mapped_program", match=MatchValue(value=program)))
    if clearance:
        must_conditions.append(FieldCondition(key="detected_clearance", match=MatchValue(value=clearance)))

    filter_obj = Filter(must=must_conditions) if must_conditions else None

    try:
        results, _ = qdrant.scroll(
            collection_name="jobs",
            scroll_filter=filter_obj,
            limit=limit,
            with_payload=True,
        )

        return {"jobs": [{"id": str(p.id), **p.payload} for p in results], "total": len(results)}
    except Exception as e:
        logger.error("list_jobs_failed", error=str(e))
        return {"jobs": [], "total": 0, "error": str(e)}


# ====== PIPELINE ======

@router.get("/pipeline")
async def get_pipeline(_authenticated: bool = Depends(verify_api_key)):
    """Get BD pipeline overview by stage."""
    qdrant = get_qdrant()

    try:
        results, _ = qdrant.scroll(
            collection_name="pipeline_tracking",
            limit=500,
            with_payload=True,
        )

        stages = {}
        for p in results:
            stage = p.payload.get("stage", "unknown")
            if stage not in stages:
                stages[stage] = []
            stages[stage].append({"id": str(p.id), **p.payload})

        return {"pipeline": stages, "total": len(results)}
    except Exception as e:
        logger.error("get_pipeline_failed", error=str(e))
        return {"pipeline": {}, "total": 0, "error": str(e)}


# ====== ANALYTICS ======

@router.get("/analytics/overview")
async def analytics_overview(_authenticated: bool = Depends(verify_api_key)):
    """Get cross-collection analytics overview."""
    qdrant = get_qdrant()

    collections_data = {}
    for name in ["contacts", "programs", "jobs",
                 "activities", "documents"]:
        try:
            info = qdrant.get_collection(name)
            collections_data[name] = {"count": info.points_count}
        except Exception:
            collections_data[name] = {"count": 0}

    return {
        "total_contacts": collections_data.get("contacts", {}).get("count", 0),
        "total_programs": collections_data.get("programs", {}).get("count", 0),
        "total_jobs": collections_data.get("jobs", {}).get("count", 0),
        "total_activities": collections_data.get("activities", {}).get("count", 0),
        "total_documents": collections_data.get("documents", {}).get("count", 0),
    }


# ====== COLLECTIONS MANAGEMENT ======

@router.get("/collections/stats")
async def collection_stats(_authenticated: bool = Depends(verify_api_key)):
    """Get stats for all unified collections."""
    qdrant = get_qdrant()
    stats = {}
    try:
        for c in qdrant.get_collections().collections:
            info = qdrant.get_collection(c.name)
            stats[c.name] = {
                "vectors": info.points_count,
                "status": str(info.status),
            }
    except Exception as e:
        logger.error("collection_stats_failed", error=str(e))
        return {"error": str(e)}
    return stats


# ====== TOOLS / OPERATIONS ======

@router.post("/tools/trigger-scrape")
async def trigger_scrape(
    scraper_name: str = "insight_global",
    _authenticated: bool = Depends(verify_api_key),
):
    """Trigger a job scraper run (proxied to Data-Scraper)."""
    logger.info("scrape_triggered", scraper=scraper_name)
    return {"status": "triggered", "scraper": scraper_name, "message": "Connect to Data-Scraper API"}


@router.post("/tools/trigger-enrichment")
async def trigger_enrichment(
    program_id: str,
    _authenticated: bool = Depends(verify_api_key),
):
    """Trigger program enrichment (proxied to N8N-Builder)."""
    logger.info("enrichment_triggered", program=program_id)
    return {"status": "triggered", "program": program_id, "message": "Connect to N8N-Builder API"}


# ====== SYNC OPERATIONS ======

@router.get("/sync/status")
async def sync_status(_authenticated: bool = Depends(verify_api_key)):
    """Get sync status for all collections."""
    qdrant = get_qdrant()
    status = {}

    collection_names = [
        "contacts", "programs", "jobs",
        "activities", "documents"
    ]

    for name in collection_names:
        try:
            info = qdrant.get_collection(name)
            status[name] = {"vectors": info.points_count, "status": "ok"}
        except Exception as e:
            status[name] = {"vectors": 0, "error": str(e)}

    return status


@router.post("/sync/notion-to-qdrant")
async def trigger_notion_sync(
    source_db: str = "dcgs_contacts",
    _authenticated: bool = Depends(verify_api_key),
):
    """Trigger Notion -> Qdrant sync for a specific database."""
    logger.info("notion_sync_triggered", source=source_db)
    return {"status": "sync_triggered", "source": source_db}


# ====== HEALTH CHECK ======

@router.get("/health")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {"status": "ok", "service": "bd-hub-api"}
