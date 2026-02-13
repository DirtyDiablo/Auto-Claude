"""Phase 42A — Memory API (12 endpoints)

REST endpoints for the unified memory cortex: store, recall,
consolidate, reflect, forget, and query across all memory tiers.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

from src.memory.cortex import (
    Memory,
    AgentContext,
    get_memory_cortex,
)

logger = logging.getLogger(__name__)


# =========================================
# REQUEST / RESPONSE MODELS
# =========================================

class StoreRequest(BaseModel):
    content: str = Field(..., min_length=3)
    memory_type: str = "episodic"
    importance: float = 0.5
    entities: List[str] = Field(default_factory=list)
    programs: List[str] = Field(default_factory=list)
    contacts: List[str] = Field(default_factory=list)
    source: str = ""
    tags: List[str] = Field(default_factory=list)
    confidence: float = 0.8
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecallRequest(BaseModel):
    query: str = Field(..., min_length=2)
    memory_types: Optional[List[str]] = None
    time_range: Optional[List[str]] = None  # [start_iso, end_iso]
    limit: int = 10
    min_score: float = 0.01


class ContextRecallRequest(BaseModel):
    task_type: str = ""
    task_description: str = Field(..., min_length=3)
    entities: List[str] = Field(default_factory=list)
    programs: List[str] = Field(default_factory=list)
    contacts: List[str] = Field(default_factory=list)
    agent_type: str = ""


class ConsolidateRequest(BaseModel):
    age_threshold_days: int = 7


class ForgetRequest(BaseModel):
    decay_factor: float = 0.95
    removal_threshold: float = 0.05


# =========================================
# ROUTE SETUP
# =========================================

def include_memory_router(app: FastAPI) -> None:
    """Register all memory endpoints on the FastAPI app."""

    cortex = get_memory_cortex()

    # --------------------------------------------------
    # 1. POST /memory/store — Store a new memory
    # --------------------------------------------------
    @app.post("/memory/store")
    async def memory_store(req: StoreRequest):
        """Store a new memory in the appropriate tier."""
        mem = Memory(
            content=req.content,
            memory_type=req.memory_type,
            importance=req.importance,
            entities=req.entities,
            programs=req.programs,
            contacts=req.contacts,
            source=req.source,
            tags=req.tags,
            confidence=req.confidence,
            metadata=req.metadata,
        )
        mem_id = await cortex.store(mem)
        return {"memory_id": mem_id, "memory_type": req.memory_type, "status": "stored"}

    # --------------------------------------------------
    # 2. POST /memory/recall — Recall memories by query
    # --------------------------------------------------
    @app.post("/memory/recall")
    async def memory_recall(req: RecallRequest):
        """Recall memories relevant to a query."""
        time_range = None
        if req.time_range and len(req.time_range) == 2:
            time_range = (req.time_range[0], req.time_range[1])

        results = await cortex.recall(
            query=req.query,
            memory_types=req.memory_types,
            time_range=time_range,
            limit=req.limit,
            min_score=req.min_score,
        )
        return {
            "query": req.query,
            "results": [_serialize_result(r) for r in results],
            "count": len(results),
        }

    # --------------------------------------------------
    # 3. POST /memory/recall/context — Recall for agent context
    # --------------------------------------------------
    @app.post("/memory/recall/context")
    async def memory_recall_context(req: ContextRecallRequest):
        """Recall all relevant memories for an agent's task context."""
        context = AgentContext(
            task_type=req.task_type,
            task_description=req.task_description,
            entities=req.entities,
            programs=req.programs,
            contacts=req.contacts,
            agent_type=req.agent_type,
        )
        ctx_mem = await cortex.recall_for_context(context)
        return {
            "episodic": [_serialize_result(r) for r in ctx_mem.episodic],
            "semantic": [_serialize_result(r) for r in ctx_mem.semantic],
            "procedural": [_serialize_result(r) for r in ctx_mem.procedural],
            "summary": ctx_mem.summary,
            "total_memories": ctx_mem.total_memories,
        }

    # --------------------------------------------------
    # 4. POST /memory/consolidate — Run memory consolidation
    # --------------------------------------------------
    @app.post("/memory/consolidate")
    async def memory_consolidate(req: ConsolidateRequest = ConsolidateRequest()):
        """Run memory consolidation: compress episodes into semantic facts."""
        report = await cortex.consolidate(age_threshold_days=req.age_threshold_days)
        return {
            "episodes_scanned": report.episodes_scanned,
            "facts_extracted": report.facts_extracted,
            "facts_updated": report.facts_updated,
            "facts_new": report.facts_new,
            "episodes_compressed": report.episodes_compressed,
            "insights_generated": report.insights_generated,
            "duration_seconds": report.duration_seconds,
            "timestamp": report.timestamp,
        }

    # --------------------------------------------------
    # 5. POST /memory/reflect — Generate procedural insights
    # --------------------------------------------------
    @app.post("/memory/reflect")
    async def memory_reflect():
        """Generate procedural insights from episodic patterns."""
        insights = await cortex.reflect()
        return {
            "insights": [
                {
                    "id": i.id,
                    "pattern": i.pattern,
                    "insight": i.insight,
                    "confidence": i.confidence,
                    "evidence_count": i.evidence_count,
                    "effectiveness_score": i.effectiveness_score,
                    "category": i.category,
                    "applicable_to": i.applicable_to,
                }
                for i in insights
            ],
            "count": len(insights),
        }

    # --------------------------------------------------
    # 6. POST /memory/forget — Run memory decay
    # --------------------------------------------------
    @app.post("/memory/forget")
    async def memory_forget(req: ForgetRequest = ForgetRequest()):
        """Run intelligent memory decay and cleanup."""
        report = await cortex.forget(
            decay_factor=req.decay_factor,
            removal_threshold=req.removal_threshold,
        )
        return {
            "memories_scanned": report.memories_scanned,
            "memories_decayed": report.memories_decayed,
            "memories_removed": report.memories_removed,
            "memories_preserved": report.memories_preserved,
            "timestamp": report.timestamp,
        }

    # --------------------------------------------------
    # 7. GET /memory/stats — Memory statistics by tier
    # --------------------------------------------------
    @app.get("/memory/stats")
    async def memory_stats():
        """Get memory statistics by tier."""
        return cortex.get_stats()

    # --------------------------------------------------
    # 8. GET /memory/episodic/recent — Recent episodic memories
    # --------------------------------------------------
    @app.get("/memory/episodic/recent")
    async def memory_episodic_recent(
        limit: int = Query(20, ge=1, le=100),
    ):
        """Get most recent episodic memories."""
        episodes = cortex.get_recent_episodic(limit=limit)
        return {
            "episodes": [_serialize_memory(m) for m in episodes],
            "count": len(episodes),
        }

    # --------------------------------------------------
    # 9. GET /memory/semantic/facts — Key semantic facts
    # --------------------------------------------------
    @app.get("/memory/semantic/facts")
    async def memory_semantic_facts(
        limit: int = Query(50, ge=1, le=500),
    ):
        """Get highest-confidence semantic facts."""
        facts = cortex.get_semantic_facts(limit=limit)
        return {
            "facts": [_serialize_memory(m) for m in facts],
            "count": len(facts),
        }

    # --------------------------------------------------
    # 10. GET /memory/procedural/insights — Procedural insights catalog
    # --------------------------------------------------
    @app.get("/memory/procedural/insights")
    async def memory_procedural_insights():
        """Get all procedural insights."""
        insights = cortex.get_procedural_insights()
        return {
            "insights": [
                {
                    "id": i.id,
                    "pattern": i.pattern,
                    "insight": i.insight,
                    "confidence": i.confidence,
                    "evidence_count": i.evidence_count,
                    "effectiveness_score": i.effectiveness_score,
                    "category": i.category,
                    "applicable_to": i.applicable_to,
                    "created_at": i.created_at,
                }
                for i in insights
            ],
            "count": len(insights),
        }

    # --------------------------------------------------
    # 11. GET /memory/search — Full-text memory search
    # --------------------------------------------------
    @app.get("/memory/search")
    async def memory_search(
        q: str = Query(..., min_length=2),
        limit: int = Query(20, ge=1, le=100),
    ):
        """Full-text search across all memory tiers."""
        results = await cortex.search(query=q, limit=limit)
        return {
            "query": q,
            "results": [_serialize_result(r) for r in results],
            "count": len(results),
        }

    # --------------------------------------------------
    # 12. GET /memory/entity/{entity_id}/memories — Entity memories
    # --------------------------------------------------
    @app.get("/memory/entity/{entity_id}/memories")
    async def memory_entity(entity_id: str):
        """Get all memories about a specific entity."""
        results = await cortex.get_entity_memories(entity_id)
        return {
            "entity": entity_id,
            "memories": [_serialize_result(r) for r in results],
            "count": len(results),
        }

    logger.info("Memory API: 12 endpoints registered under /memory/*")


# =========================================
# SERIALIZATION HELPERS
# =========================================

def _serialize_memory(mem: Memory) -> Dict[str, Any]:
    """Serialize a Memory to a JSON-safe dict."""
    return {
        "id": mem.id,
        "content": mem.content,
        "memory_type": mem.memory_type,
        "importance": mem.importance,
        "entities": mem.entities,
        "programs": mem.programs,
        "contacts": mem.contacts,
        "source": mem.source,
        "tags": mem.tags,
        "confidence": mem.confidence,
        "access_count": mem.access_count,
        "created_at": mem.created_at,
        "last_accessed": mem.last_accessed,
    }


def _serialize_result(result) -> Dict[str, Any]:
    """Serialize a MemoryResult to a JSON-safe dict."""
    return {
        "memory": _serialize_memory(result.memory),
        "relevance_score": result.relevance_score,
        "recency_score": result.recency_score,
        "importance_score": result.importance_score,
        "combined_score": result.combined_score,
    }
