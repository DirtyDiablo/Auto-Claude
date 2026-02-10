"""
Phase 25A — Memory-Aware Search

Upgrades unified search to incorporate memory context.
Wraps existing search with memory augmentation, session continuity,
and conversation-aware query expansion.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class MemorySearchResult:
    """Search result enhanced with memory context."""
    query: str = ""
    search_results: List[Dict[str, Any]] = field(default_factory=list)
    memory_context: List[Dict[str, Any]] = field(default_factory=list)
    merged_results: List[Dict[str, Any]] = field(default_factory=list)
    total_results: int = 0
    memory_matches: int = 0
    search_time_ms: float = 0.0
    memory_time_ms: float = 0.0
    from_cache: bool = False


# ---------------------------------------------------------------------------
# Memory-Aware Search
# ---------------------------------------------------------------------------


class MemoryAwareSearch:
    """Upgrade unified search to incorporate memory context."""

    def __init__(self, unified_search=None, memory_store=None):
        self.unified_search = unified_search
        self.memory_store = memory_store
        self._session_cache: Dict[str, List[Dict[str, Any]]] = {}
        logger.info(
            "memory_aware_search_init",
            has_search=bool(unified_search),
            has_memory=bool(memory_store),
        )

    async def search(
        self,
        query: str,
        user_id: str,
        collection: str = "all",
        limit: int = 10,
        **kwargs,
    ) -> MemorySearchResult:
        """
        Memory-enhanced search:
        1. Check short-term memory for recent related queries
        2. Recall episodic memories related to query entities
        3. Run standard unified search
        4. Merge search + memory results
        5. Re-rank with memory relevance boost
        6. Store in short-term memory for session continuity
        """
        start = time.time()
        result = MemorySearchResult(query=query)

        # Step 1: Check session cache for recent queries
        cache_key = f"{user_id}:{query[:50]}"
        if cache_key in self._session_cache:
            cached = self._session_cache[cache_key]
            result.search_results = cached
            result.merged_results = cached
            result.total_results = len(cached)
            result.from_cache = True
            result.search_time_ms = round((time.time() - start) * 1000, 2)
            return result

        # Step 2: Recall memories
        mem_start = time.time()
        if self.memory_store:
            from Engine8_Knowledge.memory.memory_store import MemoryContext
            ctx = MemoryContext(user_id=user_id)
            recall = await self.memory_store.recall(
                query, ctx, layers=["episodic", "semantic"]
            )
            for layer_results in recall.results.values():
                result.memory_context.extend(layer_results)
            result.memory_matches = len(result.memory_context)
        result.memory_time_ms = round((time.time() - mem_start) * 1000, 2)

        # Step 3: Run standard unified search
        search_start = time.time()
        if self.unified_search:
            try:
                if hasattr(self.unified_search, "search"):
                    raw = await self.unified_search.search(
                        query=query,
                        collection=collection,
                        limit=limit,
                        **kwargs,
                    )
                    if isinstance(raw, dict):
                        result.search_results = raw.get("results", [])
                    elif isinstance(raw, list):
                        result.search_results = raw
                else:
                    result.search_results = []
            except Exception as exc:
                logger.warning("unified_search_error", error=str(exc))

        # Step 4: Merge
        result.merged_results = self._merge_results(
            result.search_results, result.memory_context, limit
        )
        result.total_results = len(result.merged_results)
        result.search_time_ms = round((time.time() - start) * 1000, 2)

        # Step 5: Cache for session continuity
        self._session_cache[cache_key] = result.merged_results

        logger.info(
            "memory_search_complete",
            query=query[:50],
            search_hits=len(result.search_results),
            memory_hits=result.memory_matches,
            total=result.total_results,
            ms=result.search_time_ms,
        )
        return result

    async def search_with_history(
        self,
        query: str,
        user_id: str,
        conversation: List[Dict[str, str]],
        **kwargs,
    ) -> MemorySearchResult:
        """
        Context-aware search using conversation history.
        Expands query based on conversation context + memories.
        """
        expanded_query = self._expand_query(query, conversation)
        result = await self.search(expanded_query, user_id, **kwargs)
        result.query = query  # Keep original query in result
        return result

    def _expand_query(self, query: str, conversation: List[Dict[str, str]]) -> str:
        """Expand query with recent conversation context."""
        if not conversation:
            return query

        # Extract entity mentions from last 3 messages
        recent = conversation[-3:]
        entities = set()
        for msg in recent:
            text = msg.get("content", "")
            # Simple entity extraction: capitalized multi-word phrases
            words = text.split()
            for i in range(len(words) - 1):
                if words[i][0:1].isupper() and words[i + 1][0:1].isupper():
                    entities.add(f"{words[i]} {words[i + 1]}")

        if entities:
            expansion = " ".join(list(entities)[:3])
            return f"{query} {expansion}"
        return query

    def _merge_results(
        self,
        search_results: List[Dict[str, Any]],
        memory_context: List[Dict[str, Any]],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Merge search results with memory context, boosting memory-supported results."""
        seen = set()
        merged = []

        # Add search results with memory boost
        for r in search_results:
            key = r.get("id", r.get("content", str(r)))[:100]
            if key in seen:
                continue
            seen.add(key)

            # Check if memory supports this result
            content = str(r.get("content", r.get("text", "")))
            memory_boost = 0.0
            for mem in memory_context:
                mem_content = mem.get("content", "")
                if any(
                    word in content.lower()
                    for word in mem_content.lower().split()[:5]
                    if len(word) > 3
                ):
                    memory_boost = 0.1
                    break

            r["memory_boost"] = memory_boost
            r["final_score"] = r.get("score", 0.5) + memory_boost
            merged.append(r)

        # Add memory-only results
        for mem in memory_context[:3]:
            key = mem.get("id", mem.get("content", str(mem)))[:100]
            if key in seen:
                continue
            seen.add(key)
            mem["source"] = "memory"
            mem["final_score"] = mem.get("score", 0.4)
            merged.append(mem)

        merged.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        return merged[:limit]

    def clear_cache(self, user_id: Optional[str] = None):
        """Clear session cache."""
        if user_id:
            keys = [k for k in self._session_cache if k.startswith(f"{user_id}:")]
            for k in keys:
                del self._session_cache[k]
        else:
            self._session_cache.clear()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_search: Optional[MemoryAwareSearch] = None


def get_memory_aware_search(**kwargs) -> MemoryAwareSearch:
    global _search
    if _search is None:
        _search = MemoryAwareSearch(**kwargs)
    return _search
