"""
Re-index a batch of contacts with proper OpenAI embeddings.
"""
import os
import sys
from pathlib import Path

# Add parent path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

import openai
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

def generate_embedding(text: str) -> list:
    """Generate embedding using OpenAI API."""
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding

def reindex_batch(collection: str = "contacts", batch_size: int = 20):
    """Re-index a batch of records with proper embeddings."""
    logger.info(f"Connecting to Qdrant at {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL)

    # Scroll to get points
    logger.info(f"Fetching {batch_size} points from {collection}")
    result = client.scroll(
        collection_name=collection,
        limit=batch_size,
        with_payload=True,
        with_vectors=False
    )

    points = result[0]
    logger.info(f"Got {len(points)} points to re-index")

    updated = 0
    for point in points:
        point_id = point.id
        payload = point.payload

        # Get text content for embedding
        content = payload.get("content", "")
        if not content:
            # Build from other fields
            parts = []
            for field in ["name", "first_name", "last_name", "title", "company", "program"]:
                if payload.get(field):
                    parts.append(str(payload[field]))
            content = " ".join(parts)

        if not content.strip():
            logger.warning(f"Skipping {point_id} - no content")
            continue

        # Generate new embedding
        try:
            logger.info(f"Generating embedding for {point_id[:20]}...")
            embedding = generate_embedding(content[:8000])  # Limit text length

            # Update the point with new vector
            client.upsert(
                collection_name=collection,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            updated += 1
            logger.info(f"  Updated {updated}/{len(points)}")

        except Exception as e:
            logger.error(f"Error updating {point_id}: {e}")

    logger.info(f"Re-indexed {updated} points in {collection}")
    return updated

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", default="contacts")
    parser.add_argument("--batch-size", type=int, default=20)
    args = parser.parse_args()

    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not set")
        sys.exit(1)

    reindex_batch(args.collection, args.batch_size)
