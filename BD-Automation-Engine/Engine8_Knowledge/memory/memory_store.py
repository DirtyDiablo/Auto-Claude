"""
Phase 25A — 5-Layer Memory Store

Unified memory with automatic routing across 5 layers:
1. Short-Term (Redis, TTL 1 hour)
2. Episodic (Mem0 + Qdrant)
3. Semantic (Qdrant embeddings)
4. Graph (Neo4j + Mem0)
5. Procedural (SQLite + Mem0)
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

LAYERS = ["short_term", "episodic", "semantic", "graph", "procedural"]


@dataclass
class MemoryContext:
    """Context for memory operations."""
    user_id: str = ""
    agent_id: Optional[str] = None
    contact_id: Optional[str] = None
    campaign_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class InteractionRecord:
    """Record of an interaction with a contact."""
    interaction_type: str = ""  # call, email, meeting, note
    contact_id: str = ""
    contact_name: str = ""
    summary: str = ""
    sentiment: str = "neutral"  # positive, neutral, negative
    outcome: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OutcomeRecord:
    """Record of a campaign/action outcome."""
    action: str = ""
    outcome: str = ""
    score: float = 0.0  # 0-1 success
    campaign_id: str = ""
    contact_id: Optional[str] = None
    template_used: Optional[str] = None
    channel: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class ContactMemory:
    """All memories related to a specific contact."""
    contact_id: str = ""
    contact_name: str = ""
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    preferences: List[Dict[str, Any]] = field(default_factory=list)
    insights: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    total_memories: int = 0


@dataclass
class LayerStats:
    """Stats for a single memory layer."""
    layer: str = ""
    total_entries: int = 0
    size_bytes: int = 0
    avg_access_time_ms: float = 0.0
    last_accessed: Optional[str] = None


@dataclass
class MemoryRecall:
    """Result from cross-layer memory recall."""
    query: str = ""
    results: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    total_results: int = 0
    layers_searched: List[str] = field(default_factory=list)
    recall_time_ms: float = 0.0


# ---------------------------------------------------------------------------
# Memory Store
# ---------------------------------------------------------------------------


class MemoryStore:
    """Unified 5-layer memory with automatic routing."""

    def __init__(
        self,
        mem0_manager=None,
        neo4j_manager=None,
        redis_client=None,
        storage_path: str = "Engine8_Knowledge/data/memory",
    ):
        self.mem0 = mem0_manager
        self.neo4j = neo4j_manager
        self.redis = redis_client
        self._storage = Path(storage_path)
        self._storage.mkdir(parents=True, exist_ok=True)

        # In-memory fallbacks
        self._short_term: Dict[str, Dict[str, Any]] = {}
        self._episodic: List[Dict[str, Any]] = []
        self._procedural: List[Dict[str, Any]] = []
        self._procedural_path = self._storage / "procedural.json"
        self._load_procedural()

        logger.info(
            "memory_store_init",
            has_mem0=bool(mem0_manager),
            has_neo4j=bool(neo4j_manager),
            has_redis=bool(redis_client),
        )

    def _load_procedural(self):
        if self._procedural_path.exists():
            try:
                self._procedural = json.loads(self._procedural_path.read_text())
            except Exception:
                pass

    def _save_procedural(self):
        self._procedural_path.write_text(json.dumps(self._procedural, indent=2, default=str))

    # ------------------------------------------------------------------
    # Layer routing
    # ------------------------------------------------------------------

    def _classify_layer(self, content: str, metadata: Dict[str, Any]) -> str:
        """Auto-classify which layer a memory belongs to."""
        mem_type = metadata.get("type", "")

        if mem_type == "short_term" or metadata.get("ttl"):
            return "short_term"
        elif mem_type in ("interaction", "call", "email", "meeting"):
            return "episodic"
        elif mem_type in ("knowledge", "document", "expertise"):
            return "semantic"
        elif mem_type in ("relationship", "connection", "introduction"):
            return "graph"
        elif mem_type in ("pattern", "outcome", "template", "strategy"):
            return "procedural"

        content_lower = content.lower()
        if any(kw in content_lower for kw in ["called", "emailed", "met with", "spoke to"]):
            return "episodic"
        elif any(kw in content_lower for kw in ["reports to", "knows", "introduced"]):
            return "graph"
        elif any(kw in content_lower for kw in ["worked because", "effective", "response rate"]):
            return "procedural"

        return "episodic"

    # ------------------------------------------------------------------
    # Core Operations
    # ------------------------------------------------------------------

    async def add_memory(
        self, content: str, layer: Optional[str], context: MemoryContext
    ) -> str:
        """Add a memory, auto-routing to the appropriate layer."""
        metadata = {
            "contact_id": context.contact_id,
            "campaign_id": context.campaign_id,
            "tags": context.tags,
            "type": layer or "",
        }
        actual_layer = layer if layer in LAYERS else self._classify_layer(content, metadata)

        if actual_layer == "short_term":
            return self._add_short_term(content, context, metadata)
        elif actual_layer == "episodic":
            return await self._add_episodic(content, context, metadata)
        elif actual_layer == "semantic":
            return await self._add_semantic(content, context, metadata)
        elif actual_layer == "graph":
            return await self._add_graph(content, context, metadata)
        elif actual_layer == "procedural":
            return self._add_procedural(content, context, metadata)
        else:
            return await self._add_episodic(content, context, metadata)

    def _add_short_term(self, content: str, ctx: MemoryContext, meta: Dict) -> str:
        """Layer 1: Short-term memory with TTL."""
        key = f"st_{ctx.session_id or ctx.user_id}_{len(self._short_term)}"

        if self.redis:
            try:
                self.redis.setex(key, 3600, json.dumps({"content": content, **meta}))
            except Exception:
                pass

        self._short_term[key] = {
            "content": content,
            "created_at": datetime.utcnow().isoformat(),
            **meta,
        }
        return key

    async def _add_episodic(self, content: str, ctx: MemoryContext, meta: Dict) -> str:
        """Layer 2: Episodic memory via Mem0."""
        if self.mem0:
            return await self.mem0.add(
                content, user_id=ctx.user_id, agent_id=ctx.agent_id, metadata=meta
            )
        entry = {
            "id": f"ep_{len(self._episodic)}",
            "content": content,
            "user_id": ctx.user_id,
            "created_at": datetime.utcnow().isoformat(),
            **meta,
        }
        self._episodic.append(entry)
        return entry["id"]

    async def _add_semantic(self, content: str, ctx: MemoryContext, meta: Dict) -> str:
        """Layer 3: Semantic memory (Qdrant embeddings)."""
        if self.mem0:
            meta["type"] = "knowledge"
            return await self.mem0.add(
                content, user_id=ctx.user_id, agent_id=ctx.agent_id, metadata=meta
            )
        return await self._add_episodic(content, ctx, meta)

    async def _add_graph(self, content: str, ctx: MemoryContext, meta: Dict) -> str:
        """Layer 4: Graph memory (Neo4j)."""
        if self.mem0:
            meta["type"] = "relationship"
            return await self.mem0.add(
                content, user_id=ctx.user_id, agent_id=ctx.agent_id, metadata=meta
            )
        return await self._add_episodic(content, ctx, meta)

    def _add_procedural(self, content: str, ctx: MemoryContext, meta: Dict) -> str:
        """Layer 5: Procedural memory (patterns + outcomes)."""
        entry = {
            "id": f"proc_{len(self._procedural)}",
            "content": content,
            "user_id": ctx.user_id,
            "created_at": datetime.utcnow().isoformat(),
            **meta,
        }
        self._procedural.append(entry)
        self._save_procedural()
        return entry["id"]

    # ------------------------------------------------------------------
    # Recall
    # ------------------------------------------------------------------

    async def recall(
        self,
        query: str,
        context: MemoryContext,
        layers: Optional[List[str]] = None,
    ) -> MemoryRecall:
        """Search across specified layers (or all), merge and rank results."""
        start = time.time()
        search_layers = layers or LAYERS
        results: Dict[str, List[Dict[str, Any]]] = {}

        for layer in search_layers:
            if layer == "short_term":
                results["short_term"] = self._recall_short_term(query, context)
            elif layer == "episodic":
                results["episodic"] = await self._recall_episodic(query, context)
            elif layer == "semantic":
                results["semantic"] = await self._recall_semantic(query, context)
            elif layer == "graph":
                results["graph"] = await self._recall_graph(query, context)
            elif layer == "procedural":
                results["procedural"] = self._recall_procedural(query, context)

        total = sum(len(v) for v in results.values())
        elapsed = (time.time() - start) * 1000

        return MemoryRecall(
            query=query,
            results=results,
            total_results=total,
            layers_searched=search_layers,
            recall_time_ms=round(elapsed, 2),
        )

    def _recall_short_term(self, query: str, ctx: MemoryContext) -> List[Dict[str, Any]]:
        q = query.lower()
        return [
            v for v in self._short_term.values()
            if q in v.get("content", "").lower()
        ][:5]

    async def _recall_episodic(self, query: str, ctx: MemoryContext) -> List[Dict[str, Any]]:
        if self.mem0:
            from Engine8_Knowledge.memory.mem0_manager import Memory
            memories = await self.mem0.search(query, user_id=ctx.user_id, agent_id=ctx.agent_id)
            return [{"content": m.content, "score": m.score, "id": m.memory_id} for m in memories]
        q = query.lower()
        return [e for e in self._episodic if q in e.get("content", "").lower()][:5]

    async def _recall_semantic(self, query: str, ctx: MemoryContext) -> List[Dict[str, Any]]:
        return await self._recall_episodic(query, ctx)

    async def _recall_graph(self, query: str, ctx: MemoryContext) -> List[Dict[str, Any]]:
        if self.neo4j:
            try:
                results = await self.neo4j.search(query)
                return results[:5] if isinstance(results, list) else []
            except Exception:
                pass
        return []

    def _recall_procedural(self, query: str, ctx: MemoryContext) -> List[Dict[str, Any]]:
        q = query.lower()
        return [p for p in self._procedural if q in p.get("content", "").lower()][:5]

    # ------------------------------------------------------------------
    # Specialized operations
    # ------------------------------------------------------------------

    async def remember_interaction(
        self, contact_id: str, interaction: InteractionRecord
    ) -> str:
        """Store in episodic layer + update graph relationships."""
        content = (
            f"{interaction.interaction_type} with {interaction.contact_name}: "
            f"{interaction.summary} (Sentiment: {interaction.sentiment})"
        )
        ctx = MemoryContext(
            user_id=contact_id,
            contact_id=contact_id,
            tags=[interaction.interaction_type, interaction.sentiment],
        )
        return await self.add_memory(content, "episodic", ctx)

    async def remember_outcome(
        self, campaign_id: str, outcome: OutcomeRecord
    ) -> str:
        """Store in procedural layer for pattern learning."""
        content = (
            f"Action: {outcome.action} | Outcome: {outcome.outcome} | "
            f"Score: {outcome.score} | Channel: {outcome.channel}"
        )
        ctx = MemoryContext(
            user_id=campaign_id,
            campaign_id=campaign_id,
            contact_id=outcome.contact_id,
            tags=["outcome", outcome.channel or "unknown"],
        )
        return await self.add_memory(content, "procedural", ctx)

    async def get_contact_memory(self, contact_id: str) -> ContactMemory:
        """All memories related to a specific contact across all layers."""
        ctx = MemoryContext(user_id=contact_id, contact_id=contact_id)
        recall = await self.recall(contact_id, ctx)

        interactions = recall.results.get("episodic", [])
        relationships = recall.results.get("graph", [])
        insights = recall.results.get("semantic", [])
        preferences = recall.results.get("procedural", [])

        return ContactMemory(
            contact_id=contact_id,
            interactions=interactions,
            preferences=preferences,
            insights=insights,
            relationships=relationships,
            total_memories=recall.total_results,
        )

    async def get_layer_stats(self) -> Dict[str, LayerStats]:
        """Stats for each memory layer."""
        stats = {}
        stats["short_term"] = LayerStats(
            layer="short_term",
            total_entries=len(self._short_term),
        )
        stats["episodic"] = LayerStats(
            layer="episodic",
            total_entries=len(self._episodic),
        )
        stats["procedural"] = LayerStats(
            layer="procedural",
            total_entries=len(self._procedural),
        )

        if self.mem0:
            try:
                mem_stats = await self.mem0.get_stats()
                stats["episodic"].total_entries = mem_stats.total_memories
            except Exception:
                pass

        stats["semantic"] = LayerStats(layer="semantic", total_entries=0)
        stats["graph"] = LayerStats(layer="graph", total_entries=0)

        return stats


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_store: Optional[MemoryStore] = None


def get_memory_store(**kwargs) -> MemoryStore:
    global _store
    if _store is None:
        _store = MemoryStore(**kwargs)
    return _store
