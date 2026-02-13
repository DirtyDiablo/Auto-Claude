"""
Enhanced Qdrant Collection Schemas
All collections unified with consistent metadata fields
"""

import os
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, PointStruct,
        Filter, FieldCondition, MatchValue
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("qdrant_client not available")

# Collection Definitions
COLLECTIONS = {
    "jobs": {
        "size": 1536,  # OpenAI embedding size
        "distance": "Cosine",
        "description": "Job postings with BD scores and program mappings",
        "payload_fields": [
            "job_id", "title", "company", "location", "clearance",
            "program", "bd_score", "scraped_at", "source"
        ]
    },
    "contacts": {
        "size": 1536,
        "distance": "Cosine",
        "description": "BD contacts with tier classification",
        "payload_fields": [
            "contact_id", "name", "title", "company", "program",
            "tier", "priority", "location", "email"
        ]
    },
    "programs": {
        "size": 1536,
        "distance": "Cosine",
        "description": "Federal programs and contracts",
        "payload_fields": [
            "program_id", "name", "acronym", "agency", "prime",
            "contract_value", "clearance", "locations"
        ]
    },
    "documents": {
        "size": 1536,
        "distance": "Cosine",
        "description": "Processed documents and reports",
        "payload_fields": [
            "doc_id", "title", "doc_type", "source",
            "chunk_index", "total_chunks", "content"
        ]
    },
    "memories": {
        "size": 1536,
        "distance": "Cosine",
        "description": "Long-term memory entries from Mem0",
        "payload_fields": [
            "memory_id", "user_id", "memory_type", "content", "created_at"
        ]
    },
    "knowledge_graph": {
        "size": 1536,
        "distance": "Cosine",
        "description": "Knowledge graph entities and relationships",
        "payload_fields": [
            "entity_id", "entity_type", "entity_name", "relationships"
        ]
    }
}


class EnhancedQdrantStore:
    """Enhanced Qdrant storage with unified schema."""

    def __init__(self, path: str = None):
        if path is None:
            path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data", "qdrant"
            )

        self.path = path
        self.client = None

        if QDRANT_AVAILABLE:
            try:
                os.makedirs(path, exist_ok=True)
                self.client = QdrantClient(path=path)
                logger.info(f"Qdrant initialized at {path}")
            except Exception as e:
                logger.error(f"Qdrant initialization failed: {e}")

    def _ensure_collections(self):
        """Ensure all collections exist with correct schema."""
        if not self.client:
            return

        try:
            existing = [c.name for c in self.client.get_collections().collections]
        except Exception as e:
            logger.error(f"Failed to get collections: {e}")
            return

        for name, config in COLLECTIONS.items():
            if name not in existing:
                try:
                    distance = Distance.COSINE if config["distance"] == "Cosine" else Distance.DOT
                    self.client.create_collection(
                        collection_name=name,
                        vectors_config=VectorParams(
                            size=config["size"],
                            distance=distance
                        )
                    )
                    logger.info(f"Created collection: {name}")
                except Exception as e:
                    logger.warning(f"Failed to create {name}: {e}")

    def upsert_vectors(
        self,
        collection: str,
        vectors: List[List[float]],
        payloads: List[Dict],
        ids: Optional[List[str]] = None
    ) -> int:
        """Upsert vectors with payloads."""
        if not self.client:
            return 0

        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in vectors]

        points = [
            PointStruct(id=id_, vector=vec, payload=payload)
            for id_, vec, payload in zip(ids, vectors, payloads)
        ]

        try:
            self.client.upsert(collection_name=collection, points=points)
            return len(points)
        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            return 0

    def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Dict = None
    ) -> List[Dict]:
        """Search with optional filters."""
        if not self.client:
            return []

        query_filter = None
        if filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filters.items()
            ]
            query_filter = Filter(must=conditions)

        try:
            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter
            )

            return [
                {
                    "id": str(r.id),
                    "score": r.score,
                    "payload": r.payload
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def scroll_all(self, collection: str, limit: int = 100) -> List[Dict]:
        """Scroll through all documents in a collection."""
        if not self.client:
            return []

        docs = []
        offset = None

        try:
            while True:
                results, offset = self.client.scroll(
                    collection_name=collection,
                    limit=limit,
                    offset=offset,
                    with_payload=True
                )
                for r in results:
                    docs.append({
                        "id": str(r.id),
                        "payload": r.payload
                    })
                if offset is None:
                    break
        except Exception as e:
            logger.error(f"Scroll failed: {e}")

        return docs

    def get_stats(self) -> Dict:
        """Get collection statistics."""
        stats = {}
        if not self.client:
            return stats

        for name in COLLECTIONS.keys():
            try:
                info = self.client.get_collection(name)
                stats[name] = {
                    "vectors": info.vectors_count,
                    "points": info.points_count
                }
            except Exception as e:
                logger.warning("collection_stats_failed for %s: %s", name, e)
                stats[name] = {"vectors": 0, "points": 0}

        return stats

    def delete_collection(self, collection: str) -> bool:
        """Delete a collection."""
        if not self.client:
            return False

        try:
            self.client.delete_collection(collection)
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False


# Singleton
_store: Optional[EnhancedQdrantStore] = None


def get_vector_store(path: str = None) -> EnhancedQdrantStore:
    """Get vector store singleton."""
    global _store
    if _store is None:
        _store = EnhancedQdrantStore(path)
        _store._ensure_collections()
    return _store
