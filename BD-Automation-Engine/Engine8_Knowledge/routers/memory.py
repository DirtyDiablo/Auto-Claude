"""
Feature 16 — Memory Management API Router

Stable conversational memory endpoints with per-user scoping,
deduplication, TTL cleanup, and RAG context generation.
"""

from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/memory/stable", tags=["memory-stable"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class AddMemoryRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User who owns this memory")
    content: str = Field(..., min_length=1, description="Memory content text")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional metadata"
    )


class AddMemoryResponse(BaseModel):
    memory_id: str
    user_id: str
    deduplicated: bool = False


class SearchMemoryRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=50)


class ContextRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    max_tokens: int = Field(default=2000, ge=100, le=10000)


class MemoryListResponse(BaseModel):
    user_id: str
    memories: List[Dict[str, Any]]
    total: int


class StatsResponse(BaseModel):
    backend: str
    mem0_available: bool
    user_count: int
    total_memories: int
    per_user: Dict[str, int]
    storage_dir: str


# ---------------------------------------------------------------------------
# Lazy getter
# ---------------------------------------------------------------------------

_manager = None


def _get_manager():
    global _manager
    if _manager is None:
        try:
            from Engine8_Knowledge.memory.stable_mem0 import (
                get_stable_memory_manager,
            )

            _manager = get_stable_memory_manager()
        except Exception as e:
            logger.error("stable_memory_init_failed", error=str(e))
            raise HTTPException(503, f"Memory system unavailable: {e}")
    return _manager


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/add", response_model=AddMemoryResponse)
async def add_memory(req: AddMemoryRequest):
    """Add a memory entry for a user. Deduplicates identical content."""
    mgr = _get_manager()
    # Check for dedup by looking at count before
    before_count = len(mgr._memories.get(req.user_id, []))
    memory_id = mgr.add(
        user_id=req.user_id, content=req.content, metadata=req.metadata
    )
    after_count = len(mgr._memories.get(req.user_id, []))
    deduplicated = after_count == before_count
    return AddMemoryResponse(
        memory_id=memory_id, user_id=req.user_id, deduplicated=deduplicated
    )


@router.post("/search")
async def search_memories(req: SearchMemoryRequest):
    """Search memories for a user by semantic similarity or keyword."""
    mgr = _get_manager()
    results = mgr.search(
        user_id=req.user_id, query=req.query, limit=req.limit
    )
    return {"user_id": req.user_id, "query": req.query, "results": results}


@router.get("/user/{user_id}", response_model=MemoryListResponse)
async def get_user_memories(user_id: str):
    """List all memories for a user."""
    mgr = _get_manager()
    memories = mgr.get_all(user_id)
    return MemoryListResponse(
        user_id=user_id, memories=memories, total=len(memories)
    )


@router.delete("/user/{user_id}/{memory_id}")
async def delete_memory(user_id: str, memory_id: str):
    """Delete a specific memory for a user."""
    mgr = _get_manager()
    deleted = mgr.delete(user_id, memory_id)
    if not deleted:
        raise HTTPException(404, f"Memory {memory_id} not found for user {user_id}")
    return {"deleted": True, "memory_id": memory_id, "user_id": user_id}


@router.delete("/user/{user_id}")
async def clear_user_memories(user_id: str):
    """Clear all memories for a user."""
    mgr = _get_manager()
    count = mgr.clear(user_id)
    return {"cleared": True, "user_id": user_id, "count": count}


@router.get("/stats", response_model=StatsResponse)
async def memory_stats():
    """Memory system statistics."""
    mgr = _get_manager()
    return mgr.get_stats()


@router.post("/context")
async def get_memory_context(req: ContextRequest):
    """Get relevant context string for RAG augmentation."""
    mgr = _get_manager()
    context = mgr.get_context(
        user_id=req.user_id, query=req.query, max_tokens=req.max_tokens
    )
    return {"user_id": req.user_id, "query": req.query, "context": context}


@router.post("/cleanup")
async def cleanup_expired(ttl_days: Optional[int] = None):
    """Remove memories older than TTL. Defaults to 90 days."""
    mgr = _get_manager()
    removed = mgr.cleanup_expired(ttl_days)
    return {"removed": removed, "ttl_days": ttl_days or mgr._ttl_days}
