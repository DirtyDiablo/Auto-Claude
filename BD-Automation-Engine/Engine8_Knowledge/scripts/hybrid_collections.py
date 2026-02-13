"""
Hybrid Collection Management for Qdrant.

Creates and manages collections with both dense (OpenAI 1536-dim) and
sparse (BM25) vector support. Uses Qdrant's native Modifier.IDF for BM25.

Usage:
    from qdrant_client import QdrantClient
    client = QdrantClient(url="http://localhost:6333")
    create_all_new_collections(client)
"""

import logging
from typing import Dict

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
    Modifier,
)

from Engine8_Knowledge.scripts.sparse_encoder import BM25SparseEncoder, DEFAULT_VOCAB_DIR

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSION = 1536

# 4 new collections that get hybrid (dense + sparse) from day one
HYBRID_COLLECTIONS = {
    "bullhorn_notes": {
        "description": "Bullhorn CRM call notes and activities (50K+ records)",
    },
    "federal_contracts": {
        "description": "Federal contract awards, vehicles, and modifications",
    },
    "intelligence_reports": {
        "description": "BD intelligence reports, HUMINT briefings, analysis docs",
    },
    "opportunities": {
        "description": "BD pipeline opportunities and capture tracking",
    },
}


def create_hybrid_collection(client: QdrantClient, name: str) -> bool:
    """Create a collection with dense + sparse vector config.

    Returns False if the collection already exists (never overwrites).
    """
    existing = [c.name for c in client.get_collections().collections]
    if name in existing:
        logger.info(f"Collection '{name}' already exists, skipping")
        return False

    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(
            size=EMBEDDING_DIMENSION,
            distance=Distance.COSINE,
        ),
        sparse_vectors_config={
            "bm25": SparseVectorParams(
                index=SparseIndexParams(on_disk=False),
                modifier=Modifier.IDF,
            )
        },
    )
    logger.info(f"Created hybrid collection: {name}")
    return True


def create_all_new_collections(client: QdrantClient) -> Dict[str, bool]:
    """Create all 4 new hybrid collections. Returns {name: created} map."""
    results = {}
    for name in HYBRID_COLLECTIONS:
        results[name] = create_hybrid_collection(client, name)
    return results


def collection_has_sparse(client: QdrantClient, name: str) -> bool:
    """Check if a collection has sparse vector support."""
    try:
        info = client.get_collection(name)
        sparse_config = getattr(info.config.params, "sparse_vectors", None)
        return bool(sparse_config)
    except Exception:
        return False


def get_sparse_encoder(collection: str) -> BM25SparseEncoder:
    """Get a BM25SparseEncoder with vocabulary for the given collection."""
    vocab_path = DEFAULT_VOCAB_DIR / f"{collection}_vocab.json"
    return BM25SparseEncoder(vocab_path=vocab_path)
