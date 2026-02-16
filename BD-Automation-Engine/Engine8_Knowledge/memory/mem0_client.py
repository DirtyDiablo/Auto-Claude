"""
BDMemoryClient — Typed Mem0 wrapper for BD Intelligence Hub.

Wraps the existing memory_layer.py singleton with a clean API
supporting typed memory operations and Qdrant-backed persistence.
"""

import os
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

logger = structlog.get_logger(__name__)

# Lazy import to avoid circular deps
_memory_layer = None


def _get_memory_layer():
    global _memory_layer
    if _memory_layer is None:
        from Engine8_Knowledge.scripts.memory_layer import get_memory

        _memory_layer = get_memory()
    return _memory_layer


MEMORY_TYPES = [
    "conversation_summary",
    "entity_fact",
    "action_item",
    "contact_insight",
]

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "bd_memories"
EMBEDDING_DIM = 1536


def _ensure_collection():
    """Create bd_memories collection in Qdrant if it doesn't exist."""
    try:
        client = QdrantClient(url=QDRANT_URL, timeout=10)
        collections = [c.name for c in client.get_collections().collections]
        if COLLECTION_NAME not in collections:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("collection_created", collection=COLLECTION_NAME)
        else:
            logger.info("collection_exists", collection=COLLECTION_NAME)
    except Exception as e:
        logger.warning("collection_check_failed", error=str(e))


class BDMemoryClient:
    """Typed wrapper over BDMemoryLayer for structured memory operations."""

    MEMORY_TYPES = MEMORY_TYPES

    def __init__(self):
        _ensure_collection()
        self._layer = _get_memory_layer()
        logger.info(
            "memory_client_initialized",
            backend=self._layer.backend,
        )

    @property
    def backend(self) -> str:
        return self._layer.backend

    def add_memory(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: str = "entity_fact",
    ) -> Dict[str, Any]:
        """Add a memory entry.

        Args:
            user_id: Who this memory belongs to (e.g. "bd_team").
            content: The memory text.
            metadata: Extra key-value pairs to store.
            memory_type: One of MEMORY_TYPES.
        """
        meta = metadata or {}
        meta["memory_type"] = memory_type
        meta["user_id"] = user_id
        meta["timestamp"] = datetime.now().isoformat()

        if memory_type == "entity_fact":
            entity = meta.get("entity_name", "")
            etype = meta.get("entity_type", "unknown")
            return self._layer.add_entity_fact(entity or content[:50], etype, content)
        elif memory_type == "contact_insight":
            return self._layer.add_bd_insight(
                "contact", content, source=meta.get("source", "user")
            )
        elif memory_type == "action_item":
            return self._layer.add_bd_insight(
                "action", content, source=meta.get("source", "user")
            )
        else:
            # conversation_summary or generic
            return self._layer.add_interaction(content, meta)

    def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Semantic search over memories.

        Returns list of dicts with keys: memory, score, metadata.
        """
        results = self._layer.get_context(query, limit=limit)
        return [
            {
                "memory": r.get("memory", r.get("content", str(r))),
                "score": r.get("score", 0.0),
                "metadata": r.get("metadata", {}),
            }
            for r in results
        ]

    def get_all_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Return all memories for a user."""
        if self._layer.backend == "mem0":
            try:
                all_mem = self._layer.memory.get_all(user_id=self._layer.user_id)
                return all_mem.get("results", [])
            except Exception as e:
                logger.error("get_all_memories_failed", error=str(e))
                return []
        else:
            return self._layer.memory.get_all()


# Singleton
_client_instance: Optional[BDMemoryClient] = None


def get_memory_client() -> Optional[BDMemoryClient]:
    """Get or create the singleton BDMemoryClient. Returns None on failure."""
    global _client_instance
    if _client_instance is None:
        try:
            _client_instance = BDMemoryClient()
        except Exception as e:
            logger.warning("memory_client_init_failed", error=str(e))
            return None
    return _client_instance
