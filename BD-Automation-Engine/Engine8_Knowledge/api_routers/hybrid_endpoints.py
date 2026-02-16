"""
Hybrid Search & Sync Endpoints for BD Intelligence Hub.

Provides:
- Qdrant-native hybrid search (Prefetch + RRF fusion)
- Collection stats with sparse vector detection
- Notion database sync (contacts, programs, jobs)
- Bullhorn notes indexing (50K+ call notes)
- Hybrid collection creation
"""

import os
import json
import uuid
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from qdrant_client.models import (
    PointStruct,
    Prefetch,
    Fusion,
    FusionQuery,
)

try:
    from utils.llm_retry import openai_retry
except ImportError:
    # Fallback: identity decorator if utils not on path
    def openai_retry(fn):
        return fn


logger = logging.getLogger("BDKnowledgeAPI.hybrid")

router = APIRouter(tags=["hybrid"])

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
BULLHORN_DB = PROJECT_ROOT / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"


# =========================================
# Pydantic Models
# =========================================


class HybridSearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    collections: Optional[List[str]] = Field(
        None, description="Collections to search (all if omitted)"
    )
    limit: int = Field(10, ge=1, le=100, description="Max results total")
    score_threshold: float = Field(0.0, ge=0.0, le=1.0)


class HybridSearchResult(BaseModel):
    id: str
    score: float
    payload: Dict[str, Any]
    collection: str


class HybridSearchResponse(BaseModel):
    query: str
    results: List[HybridSearchResult]
    count: int
    collections_searched: List[str]
    hybrid_collections: List[str]
    timestamp: str


class CollectionStatsResponse(BaseModel):
    collections: Dict[str, Dict[str, Any]]
    total_vectors: int
    hybrid_count: int
    dense_only_count: int
    timestamp: str


class SyncResponse(BaseModel):
    success: bool
    source: str
    collection: str
    synced_count: int
    error_count: int
    timestamp: str


class IndexBullhornResponse(BaseModel):
    success: bool
    indexed: int
    errors: int
    total_available: int
    timestamp: str


class CreateCollectionsResponse(BaseModel):
    created: Dict[str, bool]
    timestamp: str


# =========================================
# Helper: get store and client from app state
# =========================================


def _get_store():
    """Get the global BDKnowledgeStore instance."""
    import sys

    # Try direct import now that api_routers/ no longer shadows api.py
    try:
        from Engine8_Knowledge.api import store

        if store is not None:
            return store
    except (ImportError, AttributeError):
        pass
    # Fallback: scan sys.modules
    for mod_name, mod in sys.modules.items():
        if hasattr(mod, "store") and hasattr(mod, "BDKnowledgeStore"):
            s = getattr(mod, "store", None)
            if s is not None:
                return s
    main_mod = sys.modules.get("__main__")
    s = getattr(main_mod, "store", None)
    if s is not None:
        return s
    raise HTTPException(status_code=503, detail="Store not initialized")


def _get_openai_client():
    """Get OpenAI client from the global store."""
    store = _get_store()
    return store.openai_client, store.model_name


@openai_retry
def _generate_query_embedding(openai_client, model_name: str, query: str):
    """Generate embedding for a search query with retry."""
    resp = openai_client.embeddings.create(model=model_name, input=query)
    return resp.data[0].embedding


# =========================================
# 1. Hybrid Search (Qdrant-native Prefetch + RRF)
# =========================================


@router.post("/search/hybrid/v2", response_model=HybridSearchResponse)
async def hybrid_search_v2(request: HybridSearchRequest):
    """Qdrant-native hybrid search using Prefetch + RRF fusion.

    For collections with sparse vectors: uses Prefetch(dense) + Prefetch(sparse) → Fusion.RRF.
    For dense-only collections: falls back to standard dense query.
    """
    store = _get_store()
    client = store.client

    from Engine8_Knowledge.scripts.hybrid_collections import (
        collection_has_sparse,
        get_sparse_encoder,
    )

    # Determine target collections
    all_collections = list(store.configs.keys())
    # Also include hybrid collections that exist
    try:
        existing = [c.name for c in client.get_collections().collections]
    except Exception:
        existing = all_collections

    available = [
        c
        for c in existing
        if c in all_collections
        or c
        in (
            "bullhorn_notes",
            "federal_contracts",
            "intelligence_reports",
            "opportunities",
        )
    ]

    if request.collections:
        target_collections = [c for c in request.collections if c in available]
        if not target_collections:
            raise HTTPException(
                status_code=400,
                detail=f"None of {request.collections} found. Available: {available}",
            )
    else:
        target_collections = available

    # Generate dense embedding for query
    openai_client, model_name = _get_openai_client()
    try:
        query_vector = _generate_query_embedding(
            openai_client, model_name, request.query
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")

    all_results = []
    hybrid_used = []

    for coll in target_collections:
        try:
            has_sparse = collection_has_sparse(client, coll)

            if has_sparse:
                # Qdrant-native hybrid: Prefetch dense + sparse → RRF
                hybrid_used.append(coll)
                encoder = get_sparse_encoder(coll)
                sparse_vector = encoder.encode_query(request.query)

                prefetches = [
                    Prefetch(query=query_vector, limit=50, using=""),
                ]
                # Only add sparse prefetch if we have matching tokens
                if sparse_vector.indices:
                    prefetches.append(
                        Prefetch(
                            query=sparse_vector,
                            limit=50,
                            using="bm25",
                        )
                    )

                results = client.query_points(
                    collection_name=coll,
                    prefetch=prefetches,
                    query=FusionQuery(fusion=Fusion.RRF),
                    limit=request.limit,
                    score_threshold=request.score_threshold or None,
                )
            else:
                # Dense-only fallback
                results = client.query_points(
                    collection_name=coll,
                    query=query_vector,
                    limit=request.limit,
                    score_threshold=request.score_threshold or None,
                )

            for r in results.points:
                all_results.append(
                    HybridSearchResult(
                        id=str(r.id),
                        score=r.score,
                        payload=r.payload or {},
                        collection=coll,
                    )
                )

        except Exception as e:
            logger.warning(f"Hybrid search failed for {coll}: {e}")

    # Sort by score descending, take top N
    all_results.sort(key=lambda x: x.score, reverse=True)
    all_results = all_results[: request.limit]

    return HybridSearchResponse(
        query=request.query,
        results=all_results,
        count=len(all_results),
        collections_searched=target_collections,
        hybrid_collections=hybrid_used,
        timestamp=datetime.now().isoformat(),
    )


# =========================================
# 2. Collection Stats
# =========================================


@router.get("/collections/stats", response_model=CollectionStatsResponse)
async def collection_stats():
    """Get stats for all collections including sparse vector support."""
    store = _get_store()
    client = store.client

    from Engine8_Knowledge.scripts.hybrid_collections import collection_has_sparse

    collections_info = {}
    total_vectors = 0
    hybrid_count = 0
    dense_only_count = 0

    try:
        existing = client.get_collections().collections
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Qdrant error: {e}")

    for coll in existing:
        name = coll.name
        try:
            info = client.get_collection(name)
            points_count = getattr(info, "points_count", 0)
            vectors_count = getattr(info, "vectors_count", points_count)
            status = (
                getattr(info.status, "name", str(info.status))
                if hasattr(info, "status")
                else "unknown"
            )
            has_sparse = collection_has_sparse(client, name)

            collections_info[name] = {
                "points_count": points_count,
                "vectors_count": vectors_count,
                "status": status,
                "has_sparse": has_sparse,
            }
            total_vectors += vectors_count
            if has_sparse:
                hybrid_count += 1
            else:
                dense_only_count += 1
        except Exception as e:
            collections_info[name] = {"error": str(e)}

    return CollectionStatsResponse(
        collections=collections_info,
        total_vectors=total_vectors,
        hybrid_count=hybrid_count,
        dense_only_count=dense_only_count,
        timestamp=datetime.now().isoformat(),
    )


# =========================================
# 3-5. Notion Sync Endpoints
# =========================================


def _get_notion_sync():
    """Get or create NotionQdrantSync instance."""
    notion_token = os.getenv("NOTION_TOKEN")
    if not notion_token:
        raise HTTPException(
            status_code=400, detail="NOTION_TOKEN not set in environment"
        )

    from services.notion_qdrant_sync import NotionQdrantSync

    return NotionQdrantSync()


def _fetch_notion_pages(database_id: str, limit: int = 0) -> List[Dict[str, Any]]:
    """Fetch pages from a Notion database using the Notion API."""
    try:
        from notion_client import Client
    except ImportError:
        raise HTTPException(status_code=503, detail="notion-client not installed")

    notion_token = os.getenv("NOTION_TOKEN")
    if not notion_token:
        raise HTTPException(status_code=400, detail="NOTION_TOKEN not set")

    client = Client(auth=notion_token)
    all_pages = []
    start_cursor = None

    while True:
        kwargs = {"database_id": database_id, "page_size": 100}
        if start_cursor:
            kwargs["start_cursor"] = start_cursor

        response = client.databases.query(**kwargs)
        all_pages.extend(response.get("results", []))

        if not response.get("has_more") or not response.get("next_cursor"):
            break
        start_cursor = response["next_cursor"]

        if limit and len(all_pages) >= limit:
            all_pages = all_pages[:limit]
            break

    return all_pages


def _extract_notion_text(prop: Dict) -> str:
    """Extract text value from a Notion property."""
    prop_type = prop.get("type", "")
    if prop_type == "title":
        return "".join(t.get("plain_text", "") for t in prop.get("title", []))
    elif prop_type == "rich_text":
        return "".join(t.get("plain_text", "") for t in prop.get("rich_text", []))
    elif prop_type == "select":
        sel = prop.get("select")
        return sel.get("name", "") if sel else ""
    elif prop_type == "multi_select":
        return ", ".join(s.get("name", "") for s in prop.get("multi_select", []))
    elif prop_type == "number":
        val = prop.get("number")
        return str(val) if val is not None else ""
    elif prop_type == "email":
        return prop.get("email", "") or ""
    elif prop_type == "phone_number":
        return prop.get("phone_number", "") or ""
    elif prop_type == "url":
        return prop.get("url", "") or ""
    return ""


def _notion_page_to_dict(page: Dict) -> Dict[str, Any]:
    """Convert a Notion page to a flat dictionary of property values."""
    result = {"notion_page_id": page.get("id", "")}
    props = page.get("properties", {})
    for key, prop in props.items():
        result[key.lower().replace(" ", "_")] = _extract_notion_text(prop)
    return result


@router.post("/sync/notion/contacts", response_model=SyncResponse)
async def sync_notion_contacts(
    limit: int = Query(0, ge=0, description="Max records (0=all)"),
):
    """Sync DCGS Contacts from Notion to Qdrant contacts collection."""
    from services.notion_qdrant_sync import NOTION_DATABASES

    db_id = NOTION_DATABASES.get("dcgs_contacts")
    if not db_id:
        raise HTTPException(
            status_code=500, detail="dcgs_contacts database ID not configured"
        )

    pages = _fetch_notion_pages(db_id, limit=limit)
    records = [_notion_page_to_dict(p) for p in pages]

    sync = _get_notion_sync()
    result = sync.sync_records_to_qdrant(records, source_db="dcgs_contacts")

    return SyncResponse(
        success=result["error_count"] == 0,
        source="notion/dcgs_contacts",
        collection=result["collection"],
        synced_count=result["synced_count"],
        error_count=result["error_count"],
        timestamp=datetime.now().isoformat(),
    )


@router.post("/sync/notion/programs", response_model=SyncResponse)
async def sync_notion_programs(
    limit: int = Query(0, ge=0, description="Max records (0=all)"),
):
    """Sync Federal Programs from Notion to Qdrant programs collection."""
    from services.notion_qdrant_sync import NOTION_DATABASES

    db_id = NOTION_DATABASES.get("federal_programs")
    if not db_id:
        raise HTTPException(
            status_code=500, detail="federal_programs database ID not configured"
        )

    pages = _fetch_notion_pages(db_id, limit=limit)
    records = [_notion_page_to_dict(p) for p in pages]

    sync = _get_notion_sync()
    result = sync.sync_records_to_qdrant(records, source_db="federal_programs")

    return SyncResponse(
        success=result["error_count"] == 0,
        source="notion/federal_programs",
        collection=result["collection"],
        synced_count=result["synced_count"],
        error_count=result["error_count"],
        timestamp=datetime.now().isoformat(),
    )


@router.post("/sync/notion/jobs", response_model=SyncResponse)
async def sync_notion_jobs(
    limit: int = Query(0, ge=0, description="Max records (0=all)"),
):
    """Sync GDIT Jobs from Notion to Qdrant jobs collection."""
    from services.notion_qdrant_sync import NOTION_DATABASES

    db_id = NOTION_DATABASES.get("gdit_jobs")
    if not db_id:
        raise HTTPException(
            status_code=500, detail="gdit_jobs database ID not configured"
        )

    pages = _fetch_notion_pages(db_id, limit=limit)
    records = [_notion_page_to_dict(p) for p in pages]

    sync = _get_notion_sync()
    result = sync.sync_records_to_qdrant(records, source_db="gdit_jobs")

    return SyncResponse(
        success=result["error_count"] == 0,
        source="notion/gdit_jobs",
        collection=result["collection"],
        synced_count=result["synced_count"],
        error_count=result["error_count"],
        timestamp=datetime.now().isoformat(),
    )


# =========================================
# 6. Bullhorn Notes Indexing
# =========================================


@router.post("/index/bullhorn-notes", response_model=IndexBullhornResponse)
async def index_bullhorn_notes(
    batch_size: int = Query(
        200, ge=1, le=500, description="Texts per OpenAI embedding call"
    ),
    limit: int = Query(0, ge=0, description="Max notes to index (0=all)"),
):
    """Index Bullhorn call notes into the bullhorn_notes hybrid collection.

    Reads from bullhorn_master.db, generates dense + sparse vectors, upserts to Qdrant.
    """
    store = _get_store()
    client = store.client

    from Engine8_Knowledge.scripts.hybrid_collections import (
        get_sparse_encoder,
        create_hybrid_collection,
    )

    # Ensure collection exists
    create_hybrid_collection(client, "bullhorn_notes")

    if not BULLHORN_DB.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Bullhorn DB not found: {BULLHORN_DB}",
        )

    # Read call notes from SQLite
    conn = sqlite3.connect(str(BULLHORN_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Detect table name (call_notes or notes)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]

    # Try common table names for call notes
    notes_table = None
    for candidate in ["call_notes", "notes", "Note", "activity", "activities"]:
        if candidate in tables:
            notes_table = candidate
            break

    if not notes_table:
        conn.close()
        raise HTTPException(
            status_code=500,
            detail=f"No notes table found. Available tables: {tables}",
        )

    query = f"SELECT * FROM {notes_table}"
    if limit > 0:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    total_available = cursor.execute(f"SELECT COUNT(*) FROM {notes_table}").fetchone()[
        0
    ]
    conn.close()

    if not rows:
        return IndexBullhornResponse(
            success=True,
            indexed=0,
            errors=0,
            total_available=total_available,
            timestamp=datetime.now().isoformat(),
        )

    # Build text and payload for each note
    openai_client, model_name = _get_openai_client()
    encoder = get_sparse_encoder("bullhorn_notes")

    indexed = 0
    errors = 0
    batch_texts = []
    batch_meta = []

    for row in rows:
        record = dict(zip(columns, row))
        # Build composite text for embedding
        parts = []
        for field in [
            "about",
            "personReference",
            "note_type",
            "noteType",
            "action",
            "note_body",
            "comments",
        ]:
            val = record.get(field)
            if val and str(val).strip():
                parts.append(str(val).strip())
        text = " | ".join(parts) if parts else ""
        if not text:
            continue

        batch_texts.append(text)
        batch_meta.append(record)

        if len(batch_texts) >= batch_size:
            count, errs = _upsert_bullhorn_batch(
                client,
                openai_client,
                model_name,
                encoder,
                batch_texts,
                batch_meta,
            )
            indexed += count
            errors += errs
            batch_texts = []
            batch_meta = []

    # Final batch
    if batch_texts:
        count, errs = _upsert_bullhorn_batch(
            client,
            openai_client,
            model_name,
            encoder,
            batch_texts,
            batch_meta,
        )
        indexed += count
        errors += errs

    # Save vocabulary
    encoder.save_vocab()

    logger.info(f"Bullhorn notes indexing complete: {indexed} indexed, {errors} errors")

    return IndexBullhornResponse(
        success=errors == 0,
        indexed=indexed,
        errors=errors,
        total_available=total_available,
        timestamp=datetime.now().isoformat(),
    )


@openai_retry
def _embed_bullhorn_texts(openai_client, model_name: str, texts: List[str]):
    """Generate embeddings for bullhorn texts with retry."""
    response = openai_client.embeddings.create(model=model_name, input=texts)
    return [d.embedding for d in response.data]


def _upsert_bullhorn_batch(
    client,
    openai_client,
    model_name: str,
    encoder,
    texts: List[str],
    records: List[Dict],
) -> tuple:
    """Embed and upsert a batch of bullhorn notes with dense + sparse vectors."""
    try:
        # Batch dense embeddings via OpenAI
        embeddings = _embed_bullhorn_texts(openai_client, model_name, texts)
    except Exception as e:
        logger.error(f"OpenAI batch embedding error: {e}")
        return 0, len(texts)

    points = []
    for i, (text, record, embedding) in enumerate(zip(texts, records, embeddings)):
        sparse_vector = encoder.encode_document(text)

        # Generate deterministic UUID from record
        namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        point_id = str(
            uuid.uuid5(
                namespace,
                f"bullhorn_notes:{json.dumps(record, sort_keys=True, default=str)}",
            )
        )

        payload = {k: (str(v) if v is not None else None) for k, v in record.items()}
        payload["_indexed_at"] = datetime.now().isoformat()
        payload["_embedding_model"] = model_name
        payload["_source"] = "bullhorn_master_db"
        payload["_text"] = text[:2000]  # Store truncated text for reference

        vectors = {"": embedding}
        if sparse_vector.indices:
            vectors["bm25"] = sparse_vector

        points.append(
            PointStruct(
                id=point_id,
                vector=vectors,
                payload=payload,
            )
        )

    try:
        client.upsert(collection_name="bullhorn_notes", points=points)
        return len(points), 0
    except Exception as e:
        logger.error(f"Qdrant upsert error: {e}")
        return 0, len(points)


# =========================================
# 7. Create Hybrid Collections
# =========================================


@router.post("/collections/create-hybrid", response_model=CreateCollectionsResponse)
async def create_hybrid_collections():
    """Create all 4 new hybrid collections (dense + sparse)."""
    store = _get_store()
    client = store.client

    from Engine8_Knowledge.scripts.hybrid_collections import create_all_new_collections

    results = create_all_new_collections(client)

    return CreateCollectionsResponse(
        created=results,
        timestamp=datetime.now().isoformat(),
    )
