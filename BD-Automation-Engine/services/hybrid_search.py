"""
Hybrid Search Service - Combines dense, sparse (BM25), and graph search.

Uses Reciprocal Rank Fusion (RRF) to combine results from multiple search methods.

Usage:
    from services.hybrid_search import HybridSearch

    search = HybridSearch()
    results = search.search("network engineer San Diego TS/SCI", limit=10)
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

# Logging
try:
    from utils.logging_config import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# Retry utilities
try:
    from utils.llm_retry import openai_retry
except ImportError:

    def openai_retry(func):
        return func


# Qdrant
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchText

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# OpenAI
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class SearchResult:
    """Unified search result."""

    id: str
    collection: str
    payload: Dict[str, Any]
    score: float
    search_type: str  # "dense", "sparse", "graph"
    rrf_score: float = 0.0


class HybridSearch:
    """
    Hybrid search combining dense vectors, sparse (BM25), and graph traversal.

    Uses Reciprocal Rank Fusion (RRF) to combine results:
    RRF(d) = sum(1 / (k + rank_i)) for each search method
    where k=60 is a constant.
    """

    def __init__(
        self,
        qdrant_url: str = None,
        openai_api_key: str = None,
        dense_weight: float = 0.5,
        sparse_weight: float = 0.3,
        graph_weight: float = 0.2,
        rrf_k: int = 60,
    ):
        self.qdrant_url = qdrant_url or os.environ.get(
            "QDRANT_URL", "http://localhost:6333"
        )
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")

        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.graph_weight = graph_weight
        self.rrf_k = rrf_k

        if QDRANT_AVAILABLE:
            self.qdrant = QdrantClient(url=self.qdrant_url)
        else:
            self.qdrant = None
            logger.warning("Qdrant not available")

        if OPENAI_AVAILABLE and self.openai_api_key:
            self.openai = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai = None
            logger.warning("OpenAI not available for embeddings")

    @openai_retry
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for query."""
        if not self.openai:
            raise ValueError("OpenAI client not configured")

        response = self.openai.embeddings.create(
            input=text, model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def dense_search(
        self,
        query: str,
        collections: List[str],
        limit: int = 50,
    ) -> List[SearchResult]:
        """Dense vector search using embeddings."""
        if not self.qdrant:
            return []

        embedding = self.get_embedding(query)
        results = []

        for collection in collections:
            try:
                hits = self.qdrant.search(
                    collection_name=collection,
                    query_vector=embedding,
                    limit=limit,
                    with_payload=True,
                )
                for hit in hits:
                    results.append(
                        SearchResult(
                            id=str(hit.id),
                            collection=collection,
                            payload=hit.payload,
                            score=hit.score,
                            search_type="dense",
                        )
                    )
            except Exception as e:
                logger.warning(
                    "dense_search_failed", collection=collection, error=str(e)
                )

        return results

    def sparse_search(
        self,
        query: str,
        collections: List[str],
        limit: int = 50,
    ) -> List[SearchResult]:
        """Sparse BM25-like search using Qdrant's full-text index."""
        if not self.qdrant:
            return []

        results = []

        for collection in collections:
            try:
                # Use text match on the 'content' field
                hits, _ = self.qdrant.scroll(
                    collection_name=collection,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="content",
                                match=MatchText(text=query),
                            )
                        ]
                    ),
                    limit=limit,
                    with_payload=True,
                )

                # Score based on position (higher = earlier = better)
                for i, hit in enumerate(hits):
                    # Simulate BM25-like score decay
                    score = 1.0 / (1 + i * 0.1)
                    results.append(
                        SearchResult(
                            id=str(hit.id),
                            collection=collection,
                            payload=hit.payload,
                            score=score,
                            search_type="sparse",
                        )
                    )
            except Exception as e:
                logger.warning(
                    "sparse_search_failed", collection=collection, error=str(e)
                )

        return results

    def graph_search(
        self,
        query: str,
        collections: List[str],
        limit: int = 50,
    ) -> List[SearchResult]:
        """
        Graph traversal search using knowledge_graph collection.

        Finds entities matching the query and returns related documents.
        """
        if not self.qdrant:
            return []

        results = []

        try:
            # First, search the knowledge graph for matching entities
            embedding = self.get_embedding(query)

            graph_hits = self.qdrant.search(
                collection_name="knowledge_graph",
                query_vector=embedding,
                limit=20,
                with_payload=True,
            )

            # Extract related IDs from graph entities
            related_ids = set()
            for hit in graph_hits:
                payload = hit.payload
                if "related_ids" in payload:
                    related_ids.update(payload["related_ids"])
                if "source_id" in payload:
                    related_ids.add(payload["source_id"])

            # Fetch related documents from main collections
            for collection in collections:
                if collection == "knowledge_graph":
                    continue

                for doc_id in list(related_ids)[:limit]:
                    try:
                        points = self.qdrant.retrieve(
                            collection_name=collection,
                            ids=[doc_id],
                            with_payload=True,
                        )
                        for point in points:
                            results.append(
                                SearchResult(
                                    id=str(point.id),
                                    collection=collection,
                                    payload=point.payload,
                                    score=0.5,  # Base score for graph results
                                    search_type="graph",
                                )
                            )
                    except Exception:
                        pass

        except Exception as e:
            logger.warning("graph_search_failed", error=str(e))

        return results

    def reciprocal_rank_fusion(
        self,
        results_by_type: Dict[str, List[SearchResult]],
    ) -> List[SearchResult]:
        """
        Combine results using Reciprocal Rank Fusion.

        RRF(d) = sum(weight_i * 1 / (k + rank_i)) across search types
        """
        # Collect all unique document IDs
        doc_scores: Dict[str, float] = defaultdict(float)
        doc_data: Dict[str, SearchResult] = {}

        weights = {
            "dense": self.dense_weight,
            "sparse": self.sparse_weight,
            "graph": self.graph_weight,
        }

        for search_type, results in results_by_type.items():
            weight = weights.get(search_type, 0.0)

            # Sort by original score (descending)
            sorted_results = sorted(results, key=lambda x: x.score, reverse=True)

            for rank, result in enumerate(sorted_results, start=1):
                doc_key = f"{result.collection}:{result.id}"
                rrf_contribution = weight * (1.0 / (self.rrf_k + rank))
                doc_scores[doc_key] += rrf_contribution

                # Keep the best data for this doc
                if doc_key not in doc_data or result.score > doc_data[doc_key].score:
                    doc_data[doc_key] = result

        # Apply RRF scores and sort
        final_results = []
        for doc_key, rrf_score in doc_scores.items():
            result = doc_data[doc_key]
            result.rrf_score = rrf_score
            final_results.append(result)

        # Sort by RRF score descending
        final_results.sort(key=lambda x: x.rrf_score, reverse=True)

        return final_results

    def search(
        self,
        query: str,
        collections: Optional[List[str]] = None,
        limit: int = 10,
        search_mode: str = "hybrid",  # "dense", "sparse", "graph", "hybrid"
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search across collections.

        Args:
            query: Search query
            collections: List of collections to search (default: main 5)
            limit: Number of results to return
            search_mode: "dense", "sparse", "graph", or "hybrid"

        Returns:
            List of search results with RRF scores
        """
        if collections is None:
            collections = [
                "contacts_unified",
                "programs_unified",
                "jobs_unified",
                "activities_log",
                "documents_kb",
            ]

        results_by_type = {}

        if search_mode in ["dense", "hybrid"]:
            results_by_type["dense"] = self.dense_search(query, collections, limit * 3)

        if search_mode in ["sparse", "hybrid"]:
            results_by_type["sparse"] = self.sparse_search(
                query, collections, limit * 3
            )

        if search_mode in ["graph", "hybrid"]:
            results_by_type["graph"] = self.graph_search(query, collections, limit * 3)

        # Combine with RRF
        if search_mode == "hybrid":
            combined = self.reciprocal_rank_fusion(results_by_type)
        else:
            # Single mode - just use those results
            combined = results_by_type.get(search_mode, [])
            for r in combined:
                r.rrf_score = r.score

        # Return top results
        return [
            {
                "id": r.id,
                "collection": r.collection,
                "score": r.rrf_score,
                "original_score": r.score,
                "search_type": r.search_type,
                "payload": r.payload,
            }
            for r in combined[:limit]
        ]


# CLI usage
if __name__ == "__main__":
    pass

    search = HybridSearch()

    test_queries = [
        "network engineer San Diego TS/SCI",
        "DCGS program manager",
        "GDIT prime contractor intelligence",
    ]

    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"Query: {query}")
        print("=" * 60)

        results = search.search(query, limit=5)
        for r in results:
            print(f"  [{r['search_type']}] {r['collection']} - Score: {r['score']:.4f}")
            print(f"    ID: {r['id']}")
            if r["payload"].get("content"):
                print(f"    Content: {r['payload']['content'][:100]}...")
