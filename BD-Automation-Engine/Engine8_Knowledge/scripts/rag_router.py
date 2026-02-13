"""
Multi-Strategy RAG Router
Routes queries to optimal retrieval strategy:
- LightRAG: Graph + Vector (for relationship queries)
- BM25: Keyword search (for exact matches)
- Hybrid: Combination (default)
- Auto: Auto-select based on query analysis
"""

from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetrievalStrategy(str, Enum):
    LIGHTRAG = "lightrag"        # Graph + vector
    BM25 = "bm25"                # Keyword search
    HYBRID = "hybrid"            # Combination
    AUTO = "auto"                # Auto-select based on query


@dataclass
class RouterResult:
    """Result from RAG router."""
    strategy: str
    query: str
    results: List[Dict]
    count: int
    strategies_used: List[str]


class RAGRouter:
    """Routes queries to optimal retrieval strategy."""

    def __init__(self):
        self.strategies = {}
        self._initialize_strategies()

    def _initialize_strategies(self):
        """Initialize available retrieval strategies."""

        # LightRAG (graph-based)
        try:
            from Engine8_Knowledge.scripts.lightrag_engine import get_knowledge_graph
            self.strategies["lightrag"] = get_knowledge_graph()
            logger.info("LightRAG strategy initialized")
        except Exception as e:
            logger.warning(f"LightRAG not available: {e}")

        # Hybrid Retriever (includes BM25)
        try:
            from Engine8_Knowledge.scripts.hybrid_retriever import get_hybrid_retriever
            self.strategies["hybrid"] = get_hybrid_retriever()
            logger.info("Hybrid retriever strategy initialized")
        except Exception as e:
            logger.warning(f"Hybrid retriever not available: {e}")

    def analyze_query(self, query: str) -> RetrievalStrategy:
        """Analyze query to determine optimal strategy."""
        query_lower = query.lower()

        # Relationship queries -> LightRAG
        relationship_keywords = [
            "who", "connect", "related", "relationship", "between",
            "teaming", "partners", "works with", "subcontracts"
        ]
        if any(kw in query_lower for kw in relationship_keywords):
            return RetrievalStrategy.LIGHTRAG

        # Exact match queries -> BM25
        exact_keywords = [
            "contract number", "piid", "uei", "cage code", "exact",
            "specific", "id:", "number:"
        ]
        if any(kw in query_lower for kw in exact_keywords):
            return RetrievalStrategy.BM25

        # Complex reasoning queries -> Hybrid
        complex_keywords = [
            "why", "how", "explain", "analyze", "compare",
            "strategy", "recommend", "best"
        ]
        if any(kw in query_lower for kw in complex_keywords):
            return RetrievalStrategy.HYBRID

        # Default to hybrid
        return RetrievalStrategy.HYBRID

    async def retrieve(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.AUTO,
        limit: int = 10,
        collection: str = "bd_knowledge",
        **kwargs
    ) -> RouterResult:
        """Retrieve using specified or auto-selected strategy."""

        # Auto-select strategy if needed
        if strategy == RetrievalStrategy.AUTO:
            strategy = self.analyze_query(query)
            logger.info(f"Auto-selected strategy: {strategy.value}")

        strategies_used = []

        # Execute retrieval based on strategy
        if strategy == RetrievalStrategy.LIGHTRAG:
            return await self._lightrag_retrieve(query, limit, strategies_used)

        if strategy == RetrievalStrategy.BM25:
            return self._bm25_retrieve(query, limit, collection, strategies_used)

        # Default: Hybrid
        return self._hybrid_retrieve(query, limit, collection, strategies_used)

    async def _lightrag_retrieve(
        self, query: str, limit: int, strategies_used: List[str]
    ) -> RouterResult:
        """Retrieve using LightRAG."""
        if "lightrag" not in self.strategies:
            logger.warning("LightRAG not available, falling back to hybrid")
            return self._hybrid_retrieve(query, limit, "bd_knowledge", strategies_used)

        try:
            lightrag = self.strategies["lightrag"]
            # Handle async query
            result = await lightrag.query(query, mode="hybrid")
            strategies_used.append("lightrag")

            # Format result
            results = [{"content": str(result), "source": "lightrag", "score": 1.0}]

            return RouterResult(
                strategy="lightrag",
                query=query,
                results=results,
                count=len(results),
                strategies_used=strategies_used
            )
        except Exception as e:
            logger.error(f"LightRAG retrieval failed: {e}")
            return self._hybrid_retrieve(query, limit, "bd_knowledge", strategies_used)

    def _bm25_retrieve(
        self, query: str, limit: int, collection: str, strategies_used: List[str]
    ) -> RouterResult:
        """Retrieve using BM25 keyword search."""
        if "hybrid" not in self.strategies:
            return RouterResult(
                strategy="bm25",
                query=query,
                results=[],
                count=0,
                strategies_used=["none"]
            )

        try:
            retriever = self.strategies["hybrid"]
            results = retriever._keyword_search(query, collection, limit)
            strategies_used.append("bm25")

            formatted = [
                {"id": r.id, "text": r.text, "score": r.score, "source": "bm25"}
                for r in results
            ]

            return RouterResult(
                strategy="bm25",
                query=query,
                results=formatted,
                count=len(formatted),
                strategies_used=strategies_used
            )
        except Exception as e:
            logger.error(f"BM25 retrieval failed: {e}")
            return RouterResult(
                strategy="bm25",
                query=query,
                results=[],
                count=0,
                strategies_used=["error"]
            )

    def _hybrid_retrieve(
        self, query: str, limit: int, collection: str, strategies_used: List[str]
    ) -> RouterResult:
        """Hybrid retrieval combining multiple strategies."""
        if "hybrid" not in self.strategies:
            return RouterResult(
                strategy="hybrid",
                query=query,
                results=[],
                count=0,
                strategies_used=["none"]
            )

        try:
            retriever = self.strategies["hybrid"]
            results = retriever.search(
                query, collection, limit,
                use_hybrid=True, use_rerank=True
            )
            strategies_used.extend(["semantic", "bm25", "rerank"])

            formatted = [
                {
                    "id": r.id,
                    "text": r.text,
                    "score": r.score,
                    "source": r.source,
                    "metadata": r.metadata
                }
                for r in results
            ]

            return RouterResult(
                strategy="hybrid",
                query=query,
                results=formatted,
                count=len(formatted),
                strategies_used=strategies_used
            )
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {e}")
            return RouterResult(
                strategy="hybrid",
                query=query,
                results=[],
                count=0,
                strategies_used=["error"]
            )

    def get_available_strategies(self) -> List[str]:
        """Get list of available strategies."""
        return list(self.strategies.keys())


# Singleton
_router: Optional[RAGRouter] = None


def get_rag_router() -> RAGRouter:
    """Get RAG router singleton."""
    global _router
    if _router is None:
        _router = RAGRouter()
    return _router
