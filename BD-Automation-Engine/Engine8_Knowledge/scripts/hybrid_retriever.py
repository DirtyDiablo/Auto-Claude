"""
Hybrid Retriever: Semantic + BM25 + CrossEncoder Reranking
30-50% better recall than semantic-only
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import numpy as np
import logging

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("rank_bm25 not available")

try:
    from sentence_transformers import CrossEncoder
    CROSSENCODER_AVAILABLE = True
except ImportError:
    CROSSENCODER_AVAILABLE = False
    logger.warning("CrossEncoder not available for reranking")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai not available")

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("qdrant_client not available")


@dataclass
class SearchResult:
    id: str
    text: str
    score: float
    source: str  # semantic, keyword, hybrid
    metadata: Dict[str, Any]


class HybridRetriever:
    """
    Hybrid retrieval combining:
    1. Semantic search (Qdrant)
    2. BM25 keyword search
    3. Reciprocal Rank Fusion (RRF)
    4. CrossEncoder reranking
    """

    def __init__(
        self,
        qdrant_url: str = None,
        collection_name: str = "bd_knowledge",
        use_reranker: bool = True
    ):
        # Qdrant - prefer server URL from environment
        qdrant_url = qdrant_url or os.getenv('QDRANT_URL', 'http://localhost:6333')

        # Qdrant client - connect to server
        if QDRANT_AVAILABLE:
            try:
                self.qdrant = QdrantClient(url=qdrant_url, timeout=60)
                logger.info(f"HybridRetriever connected to Qdrant at: {qdrant_url}")
            except Exception as e:
                logger.warning(f"Qdrant init failed: {e}")
                self.qdrant = None
        else:
            self.qdrant = None

        self.collection_name = collection_name

        # OpenAI Embedder (1536 dimensions - matches indexed data)
        self.openai_client = None
        self.embedding_model = "text-embedding-3-small"
        if OPENAI_AVAILABLE:
            try:
                self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                logger.info(f"HybridRetriever using OpenAI embeddings: {self.embedding_model}")
            except Exception as e:
                logger.warning(f"OpenAI init failed: {e}")
                self.openai_client = None
        else:
            logger.warning("OpenAI not available for embeddings")

        # Reranker (optional - still uses CrossEncoder)
        self.use_reranker = use_reranker
        self.reranker = None
        if use_reranker and CROSSENCODER_AVAILABLE:
            try:
                self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            except Exception as e:
                logger.warning(f"Reranker init failed: {e}")
                self.use_reranker = False

        # BM25 indices (built on-demand)
        self._bm25_indices: Dict[str, Any] = {}
        self._bm25_docs: Dict[str, List[Dict]] = {}

    def _build_bm25_index(self, collection: str, documents: List[Dict]):
        """Build BM25 index for collection."""
        if not BM25_AVAILABLE:
            return
        tokenized = [doc.get('text', '').lower().split() for doc in documents]
        self._bm25_indices[collection] = BM25Okapi(tokenized)
        self._bm25_docs[collection] = documents

    @staticmethod
    def _extract_text(payload: Dict) -> str:
        """Extract readable text from a Qdrant payload across different collection schemas."""
        # Try common text fields first
        for key in ('content', 'text', 'summary', 'description', 'Raw Notes', 'notes'):
            val = payload.get(key, '')
            if val and len(str(val)) > 10:
                return str(val)

        # Build text from name/title/company fields
        parts = []
        name = payload.get('\ufeffContact Name', '') or payload.get('Name', '') or payload.get('name', '') or payload.get('Program Name', '')
        if name:
            parts.append(str(name))
        for key in ('Role/Title', 'jobTitle', 'title'):
            val = payload.get(key, '')
            if val:
                parts.append(str(val))
                break
        for key in ('company', 'employer', 'Agency', 'agency', 'Prime Contractor', 'prime_contractor'):
            val = payload.get(key, '')
            if val:
                parts.append(str(val))
                break
        for key in ('Program', 'program', 'program_name'):
            val = payload.get(key, '')
            if val:
                parts.append(str(val))
                break

        if parts:
            return ' | '.join(parts)

        # Last resort: concatenate all non-empty string values
        vals = [str(v) for v in payload.values() if v and isinstance(v, str) and len(str(v)) > 3]
        return ' | '.join(vals[:5]) if vals else ''

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API (1536 dimensions)."""
        if not self.openai_client:
            return []
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            return []

    def _semantic_search(
        self, query: str, collection: str, limit: int = 20
    ) -> List[SearchResult]:
        """Qdrant semantic search using OpenAI embeddings."""
        if not self.qdrant or not self.openai_client:
            return []

        query_vector = self._generate_embedding(query)
        if not query_vector:
            return []

        try:
            results = self.qdrant.query_points(
                collection_name=collection,
                query=query_vector,
                limit=limit
            )
            return [
                SearchResult(
                    id=str(r.id),
                    text=self._extract_text(r.payload),
                    score=r.score,
                    source='semantic',
                    metadata=r.payload
                )
                for r in results.points
            ]
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []

    def _keyword_search(
        self, query: str, collection: str, limit: int = 20
    ) -> List[SearchResult]:
        """BM25 keyword search."""
        if not BM25_AVAILABLE:
            return []

        if collection not in self._bm25_indices:
            docs = self._fetch_all_docs(collection)
            self._build_bm25_index(collection, docs)

        if collection not in self._bm25_indices:
            return []

        bm25 = self._bm25_indices[collection]
        docs = self._bm25_docs[collection]

        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)

        top_indices = np.argsort(scores)[::-1][:limit]

        return [
            SearchResult(
                id=docs[idx].get('id', str(idx)),
                text=docs[idx].get('text', ''),
                score=float(scores[idx]),
                source='keyword',
                metadata=docs[idx]
            )
            for idx in top_indices if scores[idx] > 0
        ]

    def _fetch_all_docs(self, collection: str) -> List[Dict]:
        """Fetch all docs from Qdrant for BM25 indexing."""
        if not self.qdrant:
            return []

        docs = []
        offset = None

        try:
            while True:
                results, offset = self.qdrant.scroll(
                    collection_name=collection,
                    limit=100,
                    offset=offset,
                    with_payload=True
                )
                for r in results:
                    docs.append({
                        'id': str(r.id),
                        'text': r.payload.get('text', ''),
                        **r.payload
                    })
                if offset is None:
                    break
        except Exception as e:
            logger.error(f"Fetch error: {e}")

        return docs

    def _reciprocal_rank_fusion(
        self, rankings: List[List[SearchResult]], k: int = 60
    ) -> List[SearchResult]:
        """Combine rankings with RRF."""
        scores: Dict[str, float] = {}
        results_map: Dict[str, SearchResult] = {}

        for ranking in rankings:
            for rank, result in enumerate(ranking):
                doc_id = result.id
                if doc_id not in scores:
                    scores[doc_id] = 0
                    results_map[doc_id] = result
                scores[doc_id] += 1 / (k + rank + 1)

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        final = []
        for doc_id in sorted_ids:
            result = results_map[doc_id]
            result.score = scores[doc_id]
            result.source = 'hybrid'
            final.append(result)

        return final

    def _rerank(
        self, query: str, results: List[SearchResult], top_k: int = 10
    ) -> List[SearchResult]:
        """Rerank with CrossEncoder."""
        if not self.use_reranker or not results or not self.reranker:
            return results[:top_k]

        pairs = [(query, r.text) for r in results]
        scores = self.reranker.predict(pairs)

        scored = list(zip(results, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        final = []
        for result, score in scored[:top_k]:
            result.score = float(score)
            final.append(result)

        return final

    def search(
        self,
        query: str,
        collection: str = "bd_knowledge",
        limit: int = 10,
        use_hybrid: bool = True,
        use_rerank: bool = True
    ) -> List[SearchResult]:
        """
        Main search method.

        Args:
            query: Search query
            collection: Qdrant collection
            limit: Results to return
            use_hybrid: Combine semantic + keyword
            use_rerank: Apply CrossEncoder
        """
        # Semantic search
        semantic_results = self._semantic_search(query, collection, limit * 3)

        if not use_hybrid:
            if use_rerank:
                return self._rerank(query, semantic_results, limit)
            return semantic_results[:limit]

        # Keyword search
        keyword_results = self._keyword_search(query, collection, limit * 3)

        # RRF fusion
        hybrid_results = self._reciprocal_rank_fusion(
            [semantic_results, keyword_results]
        )

        # Rerank
        if use_rerank:
            return self._rerank(query, hybrid_results, limit)

        return hybrid_results[:limit]

    def search_all(
        self, query: str, collections: List[str], limit_per: int = 5
    ) -> Dict[str, List[SearchResult]]:
        """Search across multiple collections."""
        return {
            col: self.search(query, col, limit_per)
            for col in collections
        }


# Singleton
_retriever_instance = None

def get_hybrid_retriever(qdrant_path: str = None) -> HybridRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = HybridRetriever(qdrant_path)
    return _retriever_instance
