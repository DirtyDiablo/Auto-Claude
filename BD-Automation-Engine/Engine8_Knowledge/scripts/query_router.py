"""
Query Router - Routes queries to optimal retrieval system(s)
"""

import re
import asyncio
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .memory_layer import get_memory
from .lightrag_engine import get_knowledge_graph
from .hybrid_retriever import get_hybrid_retriever


class QueryType(Enum):
    FACTUAL = "factual"           # -> Qdrant semantic
    RELATIONAL = "relational"     # -> LightRAG graph
    COMPREHENSIVE = "comprehensive"  # -> All systems
    MEMORY = "memory"             # -> Mem0
    KEYWORD = "keyword"           # -> BM25


@dataclass
class RouteDecision:
    query_type: QueryType
    systems: List[str]
    confidence: float
    reasoning: str


@dataclass
class QueryResult:
    answer: str
    sources: List[Dict]
    query_type: QueryType
    systems_used: List[str]


class QueryRouter:
    """
    Routes queries to optimal retrieval system(s).

    Query Classification:
    - FACTUAL: Simple facts -> Qdrant
    - RELATIONAL: Entity connections -> LightRAG
    - COMPREHENSIVE: Complex analysis -> All systems
    - MEMORY: Past context -> Mem0
    - KEYWORD: Exact match -> BM25
    """

    def __init__(self):
        self.memory = get_memory()
        self.graph = get_knowledge_graph()
        self.retriever = get_hybrid_retriever()

        self.patterns = {
            QueryType.RELATIONAL: [
                r"relationship|connected|related|partner|teaming",
                r"who works with|network|associates",
                r"prime|sub|contractor relationship"
            ],
            QueryType.MEMORY: [
                r"remember|recall|last time|previously",
                r"we discussed|you mentioned|history"
            ],
            QueryType.COMPREHENSIVE: [
                r"comprehensive|complete|detailed|everything",
                r"analysis|analyze|evaluate|compare|strategy"
            ],
            QueryType.KEYWORD: [
                r"exact|specifically|contract number",
                r"cage code|duns|naics|solicitation"
            ]
        }

    def _classify_query(self, query: str) -> RouteDecision:
        """Classify query and determine routing."""
        query_lower = query.lower()

        matches = {}
        for qt, patterns in self.patterns.items():
            count = sum(1 for p in patterns if re.search(p, query_lower))
            if count > 0:
                matches[qt] = count

        if not matches:
            return RouteDecision(
                query_type=QueryType.FACTUAL,
                systems=["qdrant"],
                confidence=0.6,
                reasoning="Default to semantic search"
            )

        best_type = max(matches, key=matches.get)
        confidence = min(0.9, 0.5 + matches[best_type] * 0.15)

        system_map = {
            QueryType.FACTUAL: ["qdrant"],
            QueryType.RELATIONAL: ["lightrag"],
            QueryType.COMPREHENSIVE: ["qdrant", "lightrag", "mem0"],
            QueryType.MEMORY: ["mem0"],
            QueryType.KEYWORD: ["bm25"]
        }

        return RouteDecision(
            query_type=best_type,
            systems=system_map[best_type],
            confidence=confidence,
            reasoning=f"Matched patterns for {best_type.value}"
        )

    async def _query_qdrant(self, query: str, limit: int = 10) -> List[Dict]:
        try:
            results = self.retriever.search(query, "bd_knowledge", limit, True, True)
            return [{"text": getattr(r, 'text', None) or "", "score": getattr(r, 'score', 0), "source": "qdrant"} for r in results if results]
        except Exception as e:
            logger.error(f"Error querying qdrant: {e}")
            return []

    async def _query_lightrag(self, query: str) -> List[Dict]:
        try:
            response = await self.graph.query(query, mode="hybrid")
            if response:
                return [{"text": response, "score": 1.0, "source": "lightrag"}]
            return []
        except Exception as e:
            logger.error(f"Error querying lightrag: {e}")
            return []

    async def _query_mem0(self, query: str, limit: int = 10) -> List[Dict]:
        try:
            results = self.memory.get_context(query, limit)
            return [{"text": r.get("memory", "") or "", "score": r.get("score", 0), "source": "mem0"} for r in results if results]
        except Exception as e:
            logger.error(f"Error querying mem0: {e}")
            return []

    async def _query_bm25(self, query: str, limit: int = 10) -> List[Dict]:
        try:
            results = self.retriever._keyword_search(query, "bd_knowledge", limit)
            return [{"text": getattr(r, 'text', None) or "", "score": getattr(r, 'score', 0), "source": "bm25"} for r in results if results]
        except Exception as e:
            logger.error(f"Error querying bm25: {e}")
            return []

    async def smart_query(
        self, query: str, override_type: Optional[QueryType] = None
    ) -> QueryResult:
        """
        Intelligently route and execute query.

        Args:
            query: Natural language query
            override_type: Force specific query type
        """
        if override_type:
            decision = RouteDecision(
                query_type=override_type,
                systems=self._get_systems(override_type),
                confidence=1.0,
                reasoning="User override"
            )
        else:
            decision = self._classify_query(query)

        all_results = []
        systems_used = []

        for system in decision.systems:
            try:
                if system == "qdrant":
                    results = await self._query_qdrant(query)
                elif system == "lightrag":
                    results = await self._query_lightrag(query)
                elif system == "mem0":
                    results = await self._query_mem0(query)
                elif system == "bm25":
                    results = await self._query_bm25(query)
                else:
                    continue
                all_results.extend(results)
                systems_used.append(system)
            except Exception as e:
                logger.error(f"Error querying {system}: {e}")

        answer = self._synthesize(query, all_results)

        return QueryResult(
            answer=answer,
            sources=all_results,
            query_type=decision.query_type,
            systems_used=systems_used
        )

    def _get_systems(self, qt: QueryType) -> List[str]:
        return {
            QueryType.FACTUAL: ["qdrant"],
            QueryType.RELATIONAL: ["lightrag"],
            QueryType.COMPREHENSIVE: ["qdrant", "lightrag", "mem0"],
            QueryType.MEMORY: ["mem0"],
            QueryType.KEYWORD: ["bm25"]
        }.get(qt, ["qdrant"])

    def _synthesize(self, query: str, results: List[Dict]) -> str:
        if not results:
            return "No relevant information found."

        # Filter out results with None or empty text
        valid_results = [r for r in results if r.get('text')]
        if not valid_results:
            return "No relevant information found."

        top = sorted(valid_results, key=lambda x: x.get('score', 0), reverse=True)[:5]
        parts = [f"[{r.get('source', 'unknown')}] {(r.get('text') or '')[:500]}" for r in top]
        return "\n\n".join(parts)


async def smart_query(query: str) -> QueryResult:
    """Convenience function for smart querying."""
    router = QueryRouter()
    return await router.smart_query(query)
