"""
Bridge Dify to your existing Qdrant vector store.
Avoids duplicating your 8,447+ indexed records.

Your Qdrant Collections:
- contacts (7,337 records) - CRM contacts with tier classification
- programs (401 records) - Federal programs and contracts
- documents (205 records) - Past performance, briefings
- activities (500 records) - Call notes, meeting records
- jobs (4+ records) - Job postings with BD scores
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

logger = logging.getLogger(__name__)


@dataclass
class DifySearchResult:
    """Result format expected by Dify's external knowledge API."""
    content: str
    score: float
    metadata: Dict[str, Any]


class DifyQdrantBridge:
    """
    Connects Dify's external knowledge feature to your existing Qdrant.

    This bridge allows Dify to:
    1. Query your existing vectors (no duplication)
    2. Use your existing embeddings
    3. Leverage your hybrid retrieval (semantic + BM25)

    Usage in Dify:
    - Create an "External Knowledge" source
    - Point it to this bridge's API endpoint
    - Your 8,447+ records become searchable in Dify apps
    """

    # Map friendly names to your actual Qdrant collection names
    COLLECTION_MAP = {
        'contacts': 'contacts',
        'programs': 'programs',
        'documents': 'documents',
        'activities': 'activities',
        'jobs': 'jobs',
        'humint': 'activities',  # HUMINT is stored in activities
        'bd_knowledge': 'bd_knowledge',  # Combined collection
    }

    def __init__(
        self,
        knowledge_api_url: str = None,
        qdrant_url: str = None,
    ):
        """
        Initialize the Dify-Qdrant bridge.

        Args:
            knowledge_api_url: URL of your BD Knowledge API (default: http://127.0.0.1:8100)
            qdrant_url: Direct Qdrant URL for advanced operations (default: http://localhost:6333)
        """
        self.knowledge_api_url = knowledge_api_url or os.getenv(
            'KNOWLEDGE_API_URL', 'http://127.0.0.1:8100'
        )
        self.qdrant_url = qdrant_url or os.getenv(
            'QDRANT_URL', 'http://localhost:6333'
        )
        self.client = httpx.AsyncClient(timeout=60.0)

        logger.info(f"DifyQdrantBridge initialized: API={self.knowledge_api_url}")

    async def search(
        self,
        query: str,
        collection: str = None,
        top_k: int = 5,
        score_threshold: float = 0.3,
        use_hybrid: bool = True
    ) -> List[DifySearchResult]:
        """
        Search your Qdrant vectors for Dify retrieval.

        This is the main endpoint Dify will call for RAG.

        Args:
            query: Search query from Dify
            collection: Collection to search (or None for all)
            top_k: Number of results to return
            score_threshold: Minimum relevance score
            use_hybrid: Whether to use hybrid retrieval (semantic + BM25)

        Returns:
            List of DifySearchResult in Dify's expected format
        """
        try:
            # Use hybrid search for best results
            if use_hybrid:
                endpoint = f"{self.knowledge_api_url}/search/hybrid"
                params = {
                    "q": query,
                    "collection": self._resolve_collection(collection),
                    "limit": top_k,
                    "use_rerank": True
                }
            else:
                endpoint = f"{self.knowledge_api_url}/search"
                params = {
                    "q": query,
                    "collection": self._resolve_collection(collection),
                    "limit": top_k
                }

            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            # Convert to Dify format
            results = []
            for item in data.get('results', []):
                # Handle both formats from your API
                if isinstance(item, dict):
                    content = item.get('text') or item.get('payload', {}).get('text', '')
                    score = item.get('score', 0.0)
                    metadata = {
                        'id': item.get('id', ''),
                        'source': item.get('source') or item.get('payload', {}).get('source', ''),
                        'collection': collection or 'bd_knowledge',
                        **item.get('payload', {})
                    }
                else:
                    continue

                if score >= score_threshold:
                    results.append(DifySearchResult(
                        content=content,
                        score=score,
                        metadata=metadata
                    ))

            logger.info(f"Dify search: '{query[:50]}...' -> {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    async def search_contacts(
        self,
        query: str,
        company: str = None,
        tier: str = None,
        top_k: int = 10
    ) -> List[DifySearchResult]:
        """
        Search contacts with optional filters.

        Args:
            query: Search query
            company: Filter by company name
            tier: Filter by tier (Tier 1, Tier 2, etc.)
            top_k: Number of results
        """
        # Build filter query
        filter_parts = []
        if company:
            filter_parts.append(f"company:{company}")
        if tier:
            filter_parts.append(f"tier:{tier}")

        full_query = query
        if filter_parts:
            full_query = f"{query} {' '.join(filter_parts)}"

        return await self.search(full_query, collection='contacts', top_k=top_k)

    async def search_programs(
        self,
        query: str,
        agency: str = None,
        prime: str = None,
        top_k: int = 10
    ) -> List[DifySearchResult]:
        """
        Search federal programs with optional filters.

        Args:
            query: Search query
            agency: Filter by agency (USAF, Army, etc.)
            prime: Filter by prime contractor
            top_k: Number of results
        """
        filter_parts = []
        if agency:
            filter_parts.append(f"agency:{agency}")
        if prime:
            filter_parts.append(f"prime:{prime}")

        full_query = query
        if filter_parts:
            full_query = f"{query} {' '.join(filter_parts)}"

        return await self.search(full_query, collection='programs', top_k=top_k)

    async def search_jobs(
        self,
        query: str,
        clearance: str = None,
        min_bd_score: int = None,
        top_k: int = 10
    ) -> List[DifySearchResult]:
        """
        Search jobs with BD scoring filters.

        Args:
            query: Search query
            clearance: Filter by clearance (TS/SCI, Secret, etc.)
            min_bd_score: Minimum BD priority score (0-100)
            top_k: Number of results
        """
        filter_parts = []
        if clearance:
            filter_parts.append(f"clearance:{clearance}")
        if min_bd_score:
            filter_parts.append(f"bd_score>={min_bd_score}")

        full_query = query
        if filter_parts:
            full_query = f"{query} {' '.join(filter_parts)}"

        return await self.search(full_query, collection='jobs', top_k=top_k)

    async def ask_rag(
        self,
        question: str,
        collection: str = None,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        RAG query using your existing RAG engine.

        This provides full RAG responses (not just retrieval) for Dify.

        Args:
            question: Natural language question
            collection: Collection to search
            include_sources: Whether to include source citations

        Returns:
            Dict with 'answer', 'sources', 'confidence'
        """
        try:
            response = await self.client.get(
                f"{self.knowledge_api_url}/ask",
                params={
                    "q": question,
                    "collection": self._resolve_collection(collection),
                    "limit": 5
                }
            )
            response.raise_for_status()
            data = response.json()

            result = {
                'answer': data.get('answer', ''),
                'confidence': data.get('confidence', 0.0),
                'query': question
            }

            if include_sources:
                result['sources'] = [
                    {
                        'content': s.get('payload', {}).get('text', ''),
                        'score': s.get('score', 0.0),
                        'id': s.get('id', '')
                    }
                    for s in data.get('sources', [])
                ]

            return result

        except Exception as e:
            logger.error(f"RAG error: {e}")
            return {'answer': f"Error: {e}", 'confidence': 0.0, 'query': question}

    async def get_smart_answer(
        self,
        question: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Use your intelligent query router for optimal system selection.

        This routes to the best combination of:
        - Vector search
        - Knowledge graph
        - Memory system
        - BM25 keyword search

        Args:
            question: Natural language question
            use_cache: Whether to use semantic cache

        Returns:
            Dict with 'answer', 'query_type', 'systems_used', 'sources'
        """
        try:
            response = await self.client.get(
                f"{self.knowledge_api_url}/ask/smart",
                params={"q": question, "use_cache": use_cache}
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Smart query error: {e}")
            return {'answer': f"Error: {e}", 'query_type': 'error'}

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about your Qdrant collections."""
        try:
            response = await self.client.get(f"{self.knowledge_api_url}/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {'error': str(e)}

    def _resolve_collection(self, collection: str = None) -> str:
        """Resolve friendly collection name to actual Qdrant collection."""
        if not collection:
            return 'bd_knowledge'
        return self.COLLECTION_MAP.get(collection, collection)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    # Dify External Knowledge API format
    def to_dify_format(self, results: List[DifySearchResult]) -> Dict[str, Any]:
        """
        Convert results to Dify's External Knowledge API response format.

        Use this when exposing this bridge as a Dify external knowledge endpoint.
        """
        return {
            "records": [
                {
                    "content": r.content,
                    "score": r.score,
                    "title": r.metadata.get('source', ''),
                    "metadata": r.metadata
                }
                for r in results
            ]
        }


# FastAPI router for exposing this as a Dify-compatible endpoint
def create_dify_knowledge_router():
    """
    Create a FastAPI router for Dify External Knowledge integration.

    Add this to your api.py:
        from dify_integration.dify_qdrant_bridge import create_dify_knowledge_router
        app.include_router(create_dify_knowledge_router(), prefix="/dify")
    """
    from fastapi import APIRouter, Query

    router = APIRouter(tags=["Dify Integration"])
    bridge = DifyQdrantBridge()

    @router.get("/knowledge/search")
    async def dify_knowledge_search(
        query: str = Query(..., description="Search query"),
        collection: str = Query(None, description="Collection to search"),
        top_k: int = Query(5, description="Number of results")
    ):
        """Dify External Knowledge search endpoint."""
        results = await bridge.search(query, collection, top_k)
        return bridge.to_dify_format(results)

    @router.get("/knowledge/rag")
    async def dify_knowledge_rag(
        question: str = Query(..., description="Question to answer")
    ):
        """Dify RAG endpoint."""
        return await bridge.ask_rag(question)

    return router
