"""
Phase 22A — Hybrid Search Engine (Dense + BM25 Sparse + RRF + Cross-Encoder)

Qdrant-native hybrid search using dense vectors (text-embedding-3-small 1536d)
and BM25 sparse vectors (Qdrant native with IDF modifier). Reciprocal Rank Fusion
merges both channels, optional cross-encoder reranks top results.

Architecture:
  1. Dense channel: text-embedding-3-small (1536d) semantic similarity
  2. Sparse channel: Qdrant-native BM25 with Modifier.IDF for keyword matching
  3. Fusion: Reciprocal Rank Fusion (RRF) merges ranked lists
  4. Reranking: Cross-encoder BAAI/bge-reranker-v2-m3 for final scoring
"""

import os
import time
import logging
from typing import Optional, Any
from dataclasses import dataclass, field
from functools import lru_cache

logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Filter,
        FieldCondition,
        MatchValue,
        MatchText,
        Prefetch,
        FusionQuery,
        Fusion,
        SparseVector,
    )

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from fastembed import SparseTextEmbedding

    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False

try:
    from sentence_transformers import CrossEncoder

    CROSSENCODER_AVAILABLE = True
except ImportError:
    CROSSENCODER_AVAILABLE = False


QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL = "text-embedding-3-small"
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
RRF_K = 60  # RRF constant


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class SearchResult:
    """A single search result from hybrid search."""

    id: str
    content: str
    score: float
    source: str
    channel_scores: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResponse:
    """Complete search response with metadata."""

    results: list[SearchResult]
    mode_used: str
    search_latency_ms: float
    total_candidates: int
    channels_used: list[str]
    query_expanded: str = ""


# ---------------------------------------------------------------------------
# HybridSearchEngine
# ---------------------------------------------------------------------------


class HybridSearchEngine:
    """Qdrant-native hybrid search with dense + BM25 sparse + RRF + reranking."""

    def __init__(
        self,
        qdrant_url: str = QDRANT_URL,
        embedding_model: str = EMBEDDING_MODEL,
        reranker_model: str = RERANKER_MODEL,
    ) -> None:
        self._qdrant_url = qdrant_url
        self._embedding_model = embedding_model
        self._reranker_model = reranker_model
        self._qdrant: Optional[Any] = None
        self._openai: Optional[Any] = None
        self._sparse_model: Optional[Any] = None
        self._reranker: Optional[Any] = None

    # -- Lazy initialization --

    @property
    def qdrant(self) -> Any:
        if self._qdrant is None:
            if not QDRANT_AVAILABLE:
                raise RuntimeError("qdrant_client not installed")
            self._qdrant = QdrantClient(url=self._qdrant_url, timeout=30)
        return self._qdrant

    @property
    def openai_client(self) -> Any:
        if self._openai is None:
            if not OPENAI_AVAILABLE:
                raise RuntimeError("openai not installed")
            self._openai = openai.OpenAI()
        return self._openai

    @property
    def sparse_model(self) -> Any:
        if self._sparse_model is None:
            if not FASTEMBED_AVAILABLE:
                raise RuntimeError("fastembed not installed — pip install fastembed")
            self._sparse_model = SparseTextEmbedding("Qdrant/bm25")
            logger.info("bm25_sparse_model_loaded")
        return self._sparse_model

    @property
    def reranker(self) -> Any:
        if self._reranker is None:
            if not CROSSENCODER_AVAILABLE:
                raise RuntimeError("sentence-transformers not installed")
            self._reranker = CrossEncoder(self._reranker_model)
            logger.info("cross_encoder_loaded", model=self._reranker_model)
        return self._reranker

    # -- Core search --

    def search(
        self,
        query: str,
        collections: list[str] | str = "all",
        top_k: int = 10,
        use_rerank: bool = True,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
        filters: Optional[dict] = None,
    ) -> SearchResponse:
        """
        Hybrid search across one or more collections.

        Steps:
        1. Generate dense embedding (text-embedding-3-small, 1536d)
        2. Generate BM25 sparse tokens (FastEmbed Qdrant/bm25)
        3. Prefetch from both channels (dense limit=50, sparse limit=50)
        4. Fuse with RRF (Reciprocal Rank Fusion)
        5. Optional: Rerank top-30 with cross-encoder
        6. Return top_k results with source attribution
        """
        start = time.time()
        target_collections = self._resolve_collections(collections)
        qdrant_filter = self._build_filter(filters) if filters else None

        all_results: list[SearchResult] = []
        channels_used = []

        for coll in target_collections:
            try:
                coll_results = self._hybrid_search_collection(
                    query,
                    coll,
                    top_k=top_k * 3,
                    dense_weight=dense_weight,
                    sparse_weight=sparse_weight,
                    qdrant_filter=qdrant_filter,
                )
                all_results.extend(coll_results)
                if coll_results:
                    channels_used.append(coll)
            except Exception as e:
                logger.warning(
                    "collection_search_error", collection=coll, error=str(e)[:100]
                )

        if not channels_used:
            channels_used = ["dense"]

        # Deduplicate by ID
        seen = set()
        deduped = []
        for r in all_results:
            if r.id not in seen:
                seen.add(r.id)
                deduped.append(r)
        all_results = deduped

        # Sort by fused score
        all_results.sort(key=lambda r: r.score, reverse=True)
        total_candidates = len(all_results)

        # Rerank top-30
        if use_rerank and len(all_results) > 1:
            try:
                all_results = self._rerank_results(query, all_results[:30], top_k)
            except Exception as e:
                logger.warning("rerank_failed", error=str(e)[:100])
                all_results = all_results[:top_k]
        else:
            all_results = all_results[:top_k]

        elapsed = (time.time() - start) * 1000
        logger.info(
            "hybrid_search_complete",
            query=query[:50],
            results=len(all_results),
            latency_ms=round(elapsed),
            candidates=total_candidates,
        )

        return SearchResponse(
            results=all_results,
            mode_used="hybrid",
            search_latency_ms=round(elapsed, 1),
            total_candidates=total_candidates,
            channels_used=["dense", "sparse"],
        )

    def search_with_graph(
        self,
        query: str,
        collections: list[str] | str = "all",
        graph_results: Optional[list[dict]] = None,
        graph_weight: float = 0.3,
        top_k: int = 10,
        filters: Optional[dict] = None,
    ) -> SearchResponse:
        """
        Triple-channel: dense + sparse + graph.

        Steps:
        1-4. Same as hybrid search
        5. Merge graph results into RRF ranking (weighted)
        6. Deduplicate by entity ID
        7. Rerank merged set
        """
        start = time.time()

        # Get hybrid results first
        hybrid_resp = self.search(
            query,
            collections,
            top_k=top_k * 2,
            use_rerank=False,
            filters=filters,
        )
        merged = list(hybrid_resp.results)

        # Merge graph results with RRF
        if graph_results:
            for rank, gr in enumerate(graph_results):
                graph_rrf_score = graph_weight * (1.0 / (RRF_K + rank + 1))
                merged.append(
                    SearchResult(
                        id=gr.get("id", f"graph_{rank}"),
                        content=gr.get("context_text", gr.get("name", "")),
                        score=graph_rrf_score,
                        source="graph",
                        channel_scores={"graph": graph_rrf_score},
                        metadata=gr,
                    )
                )

        # Deduplicate — prefer higher score
        seen: dict[str, SearchResult] = {}
        for r in merged:
            key = r.id
            if key not in seen or r.score > seen[key].score:
                seen[key] = r
        merged = sorted(seen.values(), key=lambda r: r.score, reverse=True)

        # Rerank
        try:
            merged = self._rerank_results(query, merged[:30], top_k)
        except Exception:
            merged = merged[:top_k]

        elapsed = (time.time() - start) * 1000
        return SearchResponse(
            results=merged,
            mode_used="graphrag",
            search_latency_ms=round(elapsed, 1),
            total_candidates=hybrid_resp.total_candidates + len(graph_results or []),
            channels_used=["dense", "sparse", "graph"],
        )

    # -- Embedding generation --

    def generate_dense_embedding(self, text: str) -> list[float]:
        """Generate dense embedding with text-embedding-3-small."""
        return self._cached_dense_embedding(text)

    @lru_cache(maxsize=1000)
    def _cached_dense_embedding(self, text: str) -> tuple:
        resp = self.openai_client.embeddings.create(
            model=self._embedding_model,
            input=text,
        )
        vec = resp.data[0].embedding
        return tuple(vec)

    def generate_sparse_tokens(self, text: str) -> dict:
        """Generate BM25 sparse tokens with FastEmbed."""
        embeddings = list(self.sparse_model.embed([text]))
        if not embeddings:
            return {"indices": [], "values": []}
        sparse = embeddings[0]
        return {
            "indices": sparse.indices.tolist(),
            "values": sparse.values.tolist(),
        }

    # -- Internal search --

    def _hybrid_search_collection(
        self,
        query: str,
        collection: str,
        top_k: int = 30,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
        qdrant_filter: Optional[Any] = None,
    ) -> list[SearchResult]:
        """Search a single collection with dense + sparse prefetch + RRF."""
        dense_vec = list(self.generate_dense_embedding(query))
        sparse_tokens = self.generate_sparse_tokens(query)

        # Check if collection supports sparse vectors
        has_sparse = self._collection_has_sparse(collection)

        if has_sparse and sparse_tokens["indices"]:
            # Native Qdrant RRF with prefetch
            try:
                results = self.qdrant.query_points(
                    collection_name=collection,
                    prefetch=[
                        Prefetch(
                            query=dense_vec,
                            using="dense",
                            limit=50,
                            filter=qdrant_filter,
                        ),
                        Prefetch(
                            query=SparseVector(
                                indices=sparse_tokens["indices"],
                                values=sparse_tokens["values"],
                            ),
                            using="bm25",
                            limit=50,
                            filter=qdrant_filter,
                        ),
                    ],
                    query=FusionQuery(fusion=Fusion.RRF),
                    limit=top_k,
                ).points
            except Exception as e:
                logger.warning(
                    "prefetch_search_failed", collection=collection, error=str(e)[:100]
                )
                results = self._dense_only_search(
                    collection, dense_vec, top_k, qdrant_filter
                )
        else:
            results = self._dense_only_search(
                collection, dense_vec, top_k, qdrant_filter
            )

        return self._format_qdrant_results(results, collection)

    def _dense_only_search(
        self, collection: str, dense_vec: list, top_k: int, qdrant_filter: Any
    ) -> list:
        """Fallback dense-only search for non-upgraded collections."""
        try:
            return self.qdrant.query_points(
                collection_name=collection,
                query=dense_vec,
                limit=top_k,
                query_filter=qdrant_filter,
            ).points
        except Exception:
            # Try legacy search method
            try:
                results = self.qdrant.search(
                    collection_name=collection,
                    query_vector=dense_vec,
                    limit=top_k,
                    query_filter=qdrant_filter,
                )
                return results
            except Exception as e2:
                logger.warning(
                    "dense_search_failed", collection=collection, error=str(e2)[:100]
                )
                return []

    def _collection_has_sparse(self, collection: str) -> bool:
        """Check if collection has BM25 sparse vector config."""
        try:
            info = self.qdrant.get_collection(collection)
            sparse_config = getattr(info.config.params, "sparse_vectors", None)
            return sparse_config is not None and "bm25" in (sparse_config or {})
        except Exception:
            return False

    def _format_qdrant_results(self, points: list, source: str) -> list[SearchResult]:
        """Convert Qdrant points to SearchResult."""
        results = []
        for pt in points:
            payload = getattr(pt, "payload", {}) or {}
            content = (
                payload.get("text", "")
                or payload.get("content", "")
                or payload.get("name", "")
                or payload.get("title", "")
                or str(payload)[:200]
            )
            results.append(
                SearchResult(
                    id=str(getattr(pt, "id", "")),
                    content=content[:500],
                    score=getattr(pt, "score", 0.0) or 0.0,
                    source=source,
                    channel_scores={"dense": getattr(pt, "score", 0.0) or 0.0},
                    metadata={
                        k: v for k, v in payload.items() if k not in ("text", "content")
                    },
                )
            )
        return results

    # -- Reranking --

    def _rerank_results(
        self, query: str, results: list[SearchResult], top_k: int = 10
    ) -> list[SearchResult]:
        """Cross-encoder reranking with BAAI/bge-reranker-v2-m3."""
        if not results:
            return []
        pairs = [(query, r.content) for r in results]
        scores = self.reranker.predict(pairs)
        for i, s in enumerate(scores):
            results[i].score = float(s)
            results[i].channel_scores["rerank"] = float(s)
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    # -- Helpers --

    def _resolve_collections(self, collections: list[str] | str) -> list[str]:
        """Resolve 'all' to the list of known collections."""
        if collections == "all":
            return [
                "bd_contacts",
                "bd_documents",
                "bd_activities",
                "bd_programs",
                "bd_jobs",
            ]
        if isinstance(collections, str):
            return [collections]
        return collections

    def _build_filter(self, filters: dict) -> Any:
        """Build Qdrant filter from dict."""
        if not QDRANT_AVAILABLE:
            return None
        conditions = []
        for key, val in filters.items():
            if isinstance(val, list):
                for v in val:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=v))
                    )
            elif isinstance(val, str):
                conditions.append(FieldCondition(key=key, match=MatchText(text=val)))
            else:
                conditions.append(FieldCondition(key=key, match=MatchValue(value=val)))
        if not conditions:
            return None
        return Filter(should=conditions)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: Optional[HybridSearchEngine] = None


def get_hybrid_search_engine() -> HybridSearchEngine:
    global _instance
    if _instance is None:
        _instance = HybridSearchEngine()
    return _instance
