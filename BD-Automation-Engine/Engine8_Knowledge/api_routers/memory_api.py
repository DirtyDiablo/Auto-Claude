"""
Phase 25A — Memory API

12 FastAPI endpoints for the 5-layer memory system.
"""

from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["memory-v2"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------


class AddMemoryRequest(BaseModel):
    content: str
    layer: Optional[str] = None
    user_id: str = "default"
    agent_id: Optional[str] = None
    contact_id: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class SearchMemoryRequest(BaseModel):
    query: str
    user_id: str = "default"
    agent_id: Optional[str] = None
    layers: Optional[List[str]] = None
    limit: int = 10


class InteractionRequest(BaseModel):
    contact_id: str
    contact_name: str
    interaction_type: str = "note"
    summary: str
    sentiment: str = "neutral"
    outcome: Optional[str] = None


class OutcomeRequest(BaseModel):
    campaign_id: str
    action: str
    outcome: str
    score: float = 0.5
    contact_id: Optional[str] = None
    channel: Optional[str] = None


class BriefingRequest(BaseModel):
    agent_id: str
    task_context: str


# ---------------------------------------------------------------------------
# Lazy getters
# ---------------------------------------------------------------------------


def _get_mem0():
    try:
        from Engine8_Knowledge.memory.mem0_manager import get_mem0_manager
        return get_mem0_manager()
    except Exception:
        return None


def _get_store():
    try:
        from Engine8_Knowledge.memory.memory_store import get_memory_store
        return get_memory_store()
    except Exception:
        return None


def _get_lifecycle():
    try:
        from Engine8_Knowledge.memory.lifecycle import get_memory_lifecycle
        return get_memory_lifecycle()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/memory/add")
async def add_memory(req: AddMemoryRequest):
    """Add a memory (auto-routes to layer)."""
    store = _get_store()
    if not store:
        raise HTTPException(503, "Memory store not available")
    from Engine8_Knowledge.memory.memory_store import MemoryContext
    ctx = MemoryContext(
        user_id=req.user_id,
        agent_id=req.agent_id,
        contact_id=req.contact_id,
        tags=req.tags,
    )
    memory_id = await store.add_memory(req.content, req.layer, ctx)
    return {"memory_id": memory_id, "layer": req.layer or "auto"}


@router.post("/memory/search")
async def search_memory(req: SearchMemoryRequest):
    """Search memories across layers."""
    store = _get_store()
    if not store:
        raise HTTPException(503, "Memory store not available")
    from Engine8_Knowledge.memory.memory_store import MemoryContext
    from dataclasses import asdict
    ctx = MemoryContext(user_id=req.user_id, agent_id=req.agent_id)
    recall = await store.recall(req.query, ctx, layers=req.layers)
    return asdict(recall)


@router.get("/memory/contact/{contact_id}")
async def get_contact_memory(contact_id: str):
    """All memories for a contact."""
    store = _get_store()
    if not store:
        raise HTTPException(503, "Memory store not available")
    from dataclasses import asdict
    cm = await store.get_contact_memory(contact_id)
    return asdict(cm)


@router.get("/memory/agent/{agent_id}")
async def get_agent_memories(agent_id: str, limit: int = Query(50)):
    """All memories for an agent."""
    mem0 = _get_mem0()
    if mem0:
        memories = await mem0.get_all(user_id=agent_id, agent_id=agent_id)
        return {
            "agent_id": agent_id,
            "memories": [
                {"id": m.memory_id, "content": m.content, "metadata": m.metadata}
                for m in memories
            ],
            "total": len(memories),
        }
    return {"agent_id": agent_id, "memories": [], "total": 0}


@router.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a specific memory."""
    mem0 = _get_mem0()
    if mem0:
        ok = await mem0.delete(memory_id)
        return {"deleted": ok, "memory_id": memory_id}
    raise HTTPException(503, "Memory manager not available")


@router.get("/memory/{memory_id}/history")
async def memory_history(memory_id: str):
    """Memory version history."""
    mem0 = _get_mem0()
    if mem0:
        from dataclasses import asdict
        history = await mem0.get_history(memory_id)
        return {"memory_id": memory_id, "versions": [asdict(v) for v in history]}
    return {"memory_id": memory_id, "versions": []}


@router.post("/memory/interaction")
async def record_interaction(req: InteractionRequest):
    """Record a contact interaction."""
    store = _get_store()
    if not store:
        raise HTTPException(503, "Memory store not available")
    from Engine8_Knowledge.memory.memory_store import InteractionRecord
    record = InteractionRecord(
        interaction_type=req.interaction_type,
        contact_id=req.contact_id,
        contact_name=req.contact_name,
        summary=req.summary,
        sentiment=req.sentiment,
        outcome=req.outcome,
    )
    memory_id = await store.remember_interaction(req.contact_id, record)
    return {"memory_id": memory_id, "contact_id": req.contact_id}


@router.post("/memory/outcome")
async def record_outcome(req: OutcomeRequest):
    """Record an outcome for learning."""
    store = _get_store()
    if not store:
        raise HTTPException(503, "Memory store not available")
    from Engine8_Knowledge.memory.memory_store import OutcomeRecord
    record = OutcomeRecord(
        action=req.action,
        outcome=req.outcome,
        score=req.score,
        campaign_id=req.campaign_id,
        contact_id=req.contact_id,
        channel=req.channel,
    )
    memory_id = await store.remember_outcome(req.campaign_id, record)
    return {"memory_id": memory_id, "campaign_id": req.campaign_id}


@router.post("/memory/briefing")
async def generate_briefing(req: BriefingRequest):
    """Generate pre-task briefing from memories."""
    from Engine8_Knowledge.memory.agent_mixin import AgentMemoryMixin
    store = _get_store()
    mixin = AgentMemoryMixin(agent_id=req.agent_id, memory_store=store)
    briefing = await mixin.get_briefing(req.task_context)
    return {"agent_id": req.agent_id, "briefing": briefing}


@router.get("/memory/stats")
async def memory_stats():
    """Memory statistics by layer."""
    store = _get_store()
    if store:
        from dataclasses import asdict
        stats = await store.get_layer_stats()
        return {"layers": {k: asdict(v) for k, v in stats.items()}}
    return {"layers": {}}


@router.get("/memory/layers")
async def layer_health():
    """Layer health and stats."""
    store = _get_store()
    if store:
        from dataclasses import asdict
        stats = await store.get_layer_stats()
        return {
            "layers": {
                k: {"status": "healthy", **asdict(v)}
                for k, v in stats.items()
            },
            "total_layers": len(stats),
        }
    return {"layers": {}, "total_layers": 0}


@router.post("/memory/lifecycle/run")
async def run_lifecycle():
    """Trigger lifecycle management."""
    lifecycle = _get_lifecycle()
    if not lifecycle:
        raise HTTPException(503, "Memory lifecycle not available")
    from dataclasses import asdict
    report = await lifecycle.run_lifecycle()
    return asdict(report)
