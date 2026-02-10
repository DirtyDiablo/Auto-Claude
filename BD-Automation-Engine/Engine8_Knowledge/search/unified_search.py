"""
Phase 22A — Unified Search Interface

Single search interface that orchestrates all channels:
dense vector, BM25 sparse, and Neo4j graph retrieval.
Routes queries to optimal channel based on query classification.
"""

import re
import time
import logging
import asyncio
from typing import Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

from Engine8_Knowledge.search.hybrid_engine import (
    HybridSearchEngine, SearchResponse, SearchResult,
    get_hybrid_search_engine,
)
from Engine8_Knowledge.search.graph_retriever import (
    GraphRetriever, GraphResult, get_graph_retriever,
)


# ---------------------------------------------------------------------------
# Query classification
# ---------------------------------------------------------------------------

GRAPH_KEYWORDS = {
    "connected", "connection", "path", "relationship", "introduction",
    "introduce", "knows", "works with", "reports to", "team",
    "org chart", "network", "link", "between",
}

ENTITY_KEYWORDS = {
    "who is", "who are", "what company", "where does", "what programs",
    "tell me about", "profile", "contact",
}

KEYWORD_SIGNALS = {
    "ts/sci", "ci poly", "secret", "top secret", "clearance",
    "engineer", "analyst", "manager", "director", "developer",
    "san diego", "fort meade", "herndon", "reston", "mclean",
}

PROGRAM_NAMES = {
    "dcgs", "af dcgs", "dcgs-a", "dcgs-n", "jstars", "gbsd",
    "sentinel", "sbirs", "opir", "jadc2", "abms", "cjadc2",
}


@dataclass
class SearchMode:
    """Search mode with description."""
    name: str
    description: str


SEARCH_MODES = {
    "auto": SearchMode("auto", "Automatically classify query and route to optimal channel"),
    "hybrid": SearchMode("hybrid", "Dense + Sparse BM25 with RRF fusion"),
    "graph": SearchMode("graph", "Neo4j graph-first with vector fallback"),
    "graphrag": SearchMode("graphrag", "Triple-channel: dense + sparse + graph"),
    "vector": SearchMode("vector", "Dense vector-only (legacy behavior)"),
    "keyword": SearchMode("keyword", "BM25 keyword-only search"),
}


class UnifiedSearch:
    """Unified search interface orchestrating all retrieval channels."""

    def __init__(
        self,
        hybrid_engine: Optional[HybridSearchEngine] = None,
        graph_retriever: Optional[GraphRetriever] = None,
        query_expander: Optional[Any] = None,
    ) -> None:
        self._hybrid = hybrid_engine
        self._graph = graph_retriever
        self._expander = query_expander

    @property
    def hybrid(self) -> HybridSearchEngine:
        if self._hybrid is None:
            self._hybrid = get_hybrid_search_engine()
        return self._hybrid

    @property
    def graph(self) -> GraphRetriever:
        if self._graph is None:
            self._graph = get_graph_retriever()
        return self._graph

    @property
    def expander(self) -> Any:
        if self._expander is None:
            try:
                from Engine8_Knowledge.embeddings.query_expander import get_query_expander
                self._expander = get_query_expander()
            except Exception:
                pass
        return self._expander

    def search(
        self,
        query: str,
        mode: str = "auto",
        collections: list[str] | str = "all",
        top_k: int = 10,
        use_rerank: bool = True,
        filters: Optional[dict] = None,
        expand_query: bool = True,
    ) -> SearchResponse:
        """
        Intelligent search routing.

        mode="auto": Classify query → route appropriately
        mode="hybrid": Dense + Sparse + optional rerank
        mode="graph": Neo4j-first with vector fallback
        mode="vector": Dense-only (legacy behavior)
        mode="keyword": BM25-only
        mode="graphrag": Full triple-channel (dense + sparse + graph)
        """
        start = time.time()

        # Expand query if requested
        expanded = query
        if expand_query and self.expander:
            try:
                eq = self.expander.expand_query(query)
                expanded = eq.expanded if hasattr(eq, "expanded") else query
            except Exception:
                expanded = query

        # Auto-classify if needed
        if mode == "auto":
            mode = self._classify_query(query)
            logger.info("query_classified", query=query[:50], mode=mode)

        # Route to appropriate channel
        if mode == "graph":
            response = self._graph_search(expanded, top_k, filters)
        elif mode == "graphrag":
            response = self._graphrag_search(expanded, collections, top_k, use_rerank, filters)
        elif mode == "keyword":
            response = self._keyword_search(expanded, collections, top_k, filters)
        elif mode == "vector":
            response = self._vector_search(expanded, collections, top_k, filters)
        else:  # hybrid (default)
            response = self.hybrid.search(
                expanded, collections, top_k,
                use_rerank=use_rerank, filters=filters,
            )

        response.mode_used = mode
        response.query_expanded = expanded
        response.search_latency_ms = round((time.time() - start) * 1000, 1)

        logger.info(
            "unified_search_complete",
            query=query[:50], mode=mode,
            results=len(response.results),
            latency_ms=response.search_latency_ms,
        )

        return response

    def multi_search(
        self,
        queries: list[str],
        mode: str = "auto",
        collections: list[str] | str = "all",
        top_k: int = 10,
    ) -> list[SearchResponse]:
        """Batch search multiple queries."""
        return [
            self.search(q, mode=mode, collections=collections, top_k=top_k)
            for q in queries
        ]

    def get_modes(self) -> dict[str, dict]:
        """Return available search modes."""
        return {k: {"name": v.name, "description": v.description} for k, v in SEARCH_MODES.items()}

    # -- Query classification --

    def _classify_query(self, query: str) -> str:
        """Determine optimal search mode from query text."""
        lower = query.lower().strip()

        # Check for relationship/path queries → graph
        for kw in GRAPH_KEYWORDS:
            if kw in lower:
                return "graph"

        # Check for entity queries (who is, what company) → graph
        for kw in ENTITY_KEYWORDS:
            if lower.startswith(kw):
                return "graph"

        # Check for program names → graphrag
        for prog in PROGRAM_NAMES:
            if prog in lower:
                return "graphrag"

        # Check for clearance/keyword-heavy queries → hybrid with keyword weight
        keyword_count = sum(1 for kw in KEYWORD_SIGNALS if kw in lower)
        if keyword_count >= 2:
            return "hybrid"

        # Check for capitalized names → graph
        names = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", query)
        if names:
            return "graphrag"

        # Default: hybrid
        return "hybrid"

    # -- Channel implementations --

    def _graph_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[dict],
    ) -> SearchResponse:
        """Neo4j graph-first search."""
        start = time.time()
        try:
            graph_results = self.graph.retrieve(query, limit=top_k)
            results = [
                SearchResult(
                    id=gr.id,
                    content=gr.context_text,
                    score=gr.score,
                    source="graph",
                    channel_scores={"graph": gr.score},
                    metadata=gr.properties,
                )
                for gr in graph_results
            ]
        except Exception as e:
            logger.warning("graph_search_failed", error=str(e)[:100])
            # Fallback to hybrid
            return self.hybrid.search(query, "all", top_k, filters=filters)

        return SearchResponse(
            results=results,
            mode_used="graph",
            search_latency_ms=round((time.time() - start) * 1000, 1),
            total_candidates=len(results),
            channels_used=["graph"],
        )

    def _graphrag_search(
        self,
        query: str,
        collections: list[str] | str,
        top_k: int,
        use_rerank: bool,
        filters: Optional[dict],
    ) -> SearchResponse:
        """Triple-channel: dense + sparse + graph."""
        try:
            graph_results = self.graph.retrieve(query, limit=20)
            graph_dicts = [
                {"id": gr.id, "name": gr.name, "context_text": gr.context_text, **gr.properties}
                for gr in graph_results
            ]
        except Exception:
            graph_dicts = []

        return self.hybrid.search_with_graph(
            query, collections,
            graph_results=graph_dicts,
            top_k=top_k,
            filters=filters,
        )

    def _keyword_search(
        self,
        query: str,
        collections: list[str] | str,
        top_k: int,
        filters: Optional[dict],
    ) -> SearchResponse:
        """BM25 keyword-heavy search (sparse weight = 0.8)."""
        return self.hybrid.search(
            query, collections, top_k,
            use_rerank=False,
            dense_weight=0.2,
            sparse_weight=0.8,
            filters=filters,
        )

    def _vector_search(
        self,
        query: str,
        collections: list[str] | str,
        top_k: int,
        filters: Optional[dict],
    ) -> SearchResponse:
        """Dense vector-only search (legacy behavior)."""
        return self.hybrid.search(
            query, collections, top_k,
            use_rerank=False,
            dense_weight=1.0,
            sparse_weight=0.0,
            filters=filters,
        )


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: Optional[UnifiedSearch] = None


def get_unified_search() -> UnifiedSearch:
    global _instance
    if _instance is None:
        _instance = UnifiedSearch()
    return _instance
