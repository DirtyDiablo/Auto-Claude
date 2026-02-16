#!/usr/bin/env python3
"""
Re-index existing Qdrant collections with OpenAI embeddings.
Reads existing payloads, re-embeds with OpenAI, writes to new collection.

Usage:
  python reindex_with_openai.py --collection programs
  python reindex_with_openai.py --collection documents
  python reindex_with_openai.py --collection jobs
"""

import sys
import os
import time
import uuid
import logging

logger = logging.getLogger(__name__)
import argparse
from datetime import datetime
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir(r"C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine")
load_dotenv()

import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Configuration
QDRANT_URL = "http://localhost:6333"
OPENAI_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
BATCH_SIZE = 500
EMBED_BATCH_SIZE = 2000

client_openai = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# UUID namespace
NAMESPACE = uuid.UUID("abcdef12-3456-7890-abcd-ef1234567890")


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings from OpenAI API."""
    all_embeddings = []

    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        batch = [t if t.strip() else "empty" for t in batch]

        try:
            response = client_openai.embeddings.create(model=OPENAI_MODEL, input=batch)
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)
        except Exception as e:
            print(f"  [ERROR] OpenAI API error: {e}")
            all_embeddings.extend([[0.0] * EMBEDDING_DIM] * len(batch))

    return all_embeddings


def create_text_for_embedding(payload: dict, collection: str) -> str:
    """Create searchable text from payload based on collection type."""
    if collection == "programs":
        parts = [
            payload.get("name", ""),
            payload.get("description", ""),
            payload.get("agency", ""),
            payload.get("prime_contractor", ""),
            payload.get("content", ""),
            payload.get("text", ""),
        ]
    elif collection == "documents":
        parts = [
            payload.get("title", ""),
            payload.get("content", ""),
            payload.get("text", ""),
            payload.get("summary", ""),
            payload.get("description", ""),
        ]
    elif collection == "jobs":
        parts = [
            payload.get("title", ""),
            payload.get("company", ""),
            payload.get("description", ""),
            payload.get("requirements", ""),
            payload.get("location", ""),
            payload.get("content", ""),
            payload.get("text", ""),
        ]
    else:
        # Generic - try common fields
        parts = [
            payload.get("name", ""),
            payload.get("title", ""),
            payload.get("content", ""),
            payload.get("text", ""),
            payload.get("description", ""),
        ]

    return " ".join(str(p) for p in parts if p)


def reindex_collection(collection: str):
    """Re-index a collection with OpenAI embeddings."""
    print("=" * 70)
    print(f"RE-INDEXING: {collection.upper()}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    qdrant = QdrantClient(url=QDRANT_URL, timeout=300)

    # Get current collection info
    try:
        info = qdrant.get_collection(collection)
        total_points = info.points_count
        current_dim = info.config.params.vectors.size
        print(f"\nSource collection: {collection}")
        print(f"  Points: {total_points:,}")
        print(f"  Current dimensions: {current_dim}")
    except Exception as e:
        print(f"Error: Collection '{collection}' not found: {e}")
        return

    if current_dim == EMBEDDING_DIM:
        print(f"\n  Collection already has {EMBEDDING_DIM} dimensions. Skipping.")
        return

    # Create temp collection name
    temp_collection = f"{collection}_openai_temp"

    print(f"\nCreating temp collection: {temp_collection} ({EMBEDDING_DIM} dims)")
    try:
        qdrant.delete_collection(temp_collection)
    except Exception as e:
        logger.debug("temp_collection_delete_skipped: %s", e)

    qdrant.create_collection(
        collection_name=temp_collection,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )

    # Scroll through all points
    print(f"\nReading and re-embedding {total_points:,} points...")
    print("-" * 70)

    start_time = time.time()
    indexed = 0
    errors = 0
    offset = None
    batch_payloads = []
    batch_ids = []
    batch_texts = []

    while True:
        # Scroll batch from source
        result = qdrant.scroll(
            collection_name=collection,
            limit=BATCH_SIZE,
            offset=offset,
            with_payload=True,
            with_vectors=False,  # Don't need old vectors
        )

        points, next_offset = result

        if not points:
            break

        for point in points:
            payload = point.payload or {}
            text = create_text_for_embedding(payload, collection)

            # Add OpenAI metadata
            payload["_indexed_at"] = datetime.now().isoformat()
            payload["_embedding_model"] = OPENAI_MODEL
            payload["_reindexed"] = True

            batch_payloads.append(payload)
            batch_ids.append(point.id)
            batch_texts.append(text)

        # Process batch when full
        if len(batch_payloads) >= BATCH_SIZE:
            try:
                embeddings = get_embeddings(batch_texts)
                points_to_upsert = [
                    PointStruct(id=str(pid), vector=emb, payload=pay)
                    for pid, emb, pay in zip(batch_ids, embeddings, batch_payloads)
                ]
                qdrant.upsert(collection_name=temp_collection, points=points_to_upsert)
                indexed += len(points_to_upsert)
            except Exception as e:
                print(f"  [ERROR] Batch failed: {e}")
                errors += len(batch_payloads)

            batch_payloads = []
            batch_ids = []
            batch_texts = []

            # Progress
            elapsed = time.time() - start_time
            rate = indexed / elapsed if elapsed > 0 else 0
            pct = 100 * indexed / total_points if total_points > 0 else 0
            print(f"  {indexed:,}/{total_points:,} ({pct:.1f}%) | Rate: {rate:.0f}/sec")

        offset = next_offset
        if offset is None:
            break

    # Process remaining
    if batch_payloads:
        try:
            embeddings = get_embeddings(batch_texts)
            points_to_upsert = [
                PointStruct(id=str(pid), vector=emb, payload=pay)
                for pid, emb, pay in zip(batch_ids, embeddings, batch_payloads)
            ]
            qdrant.upsert(collection_name=temp_collection, points=points_to_upsert)
            indexed += len(points_to_upsert)
        except Exception as e:
            print(f"  [ERROR] Final batch failed: {e}")
            errors += len(batch_payloads)

    # Swap collections
    print(f"\nSwapping collections...")
    print(f"  Deleting old: {collection}")
    qdrant.delete_collection(collection)

    # Rename temp to original (Qdrant doesn't have rename, so we need to copy)
    # Actually Qdrant has no rename. We'll just use the temp name approach differently.
    # Let's delete old, create new with same name, and copy from temp

    print(f"  Creating new: {collection} ({EMBEDDING_DIM} dims)")
    qdrant.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )

    # Copy from temp to new collection
    print(f"  Copying {indexed:,} points from temp...")
    offset = None
    copied = 0

    while True:
        result = qdrant.scroll(
            collection_name=temp_collection,
            limit=BATCH_SIZE,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )

        points, next_offset = result
        if not points:
            break

        points_to_upsert = [
            PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in points
        ]
        qdrant.upsert(collection_name=collection, points=points_to_upsert)
        copied += len(points_to_upsert)

        offset = next_offset
        if offset is None:
            break

    # Delete temp
    print(f"  Deleting temp collection...")
    qdrant.delete_collection(temp_collection)

    # Final stats
    elapsed = time.time() - start_time
    final_count = qdrant.get_collection(collection).points_count

    print("\n" + "=" * 70)
    print(f"RE-INDEXING COMPLETE: {collection.upper()}")
    print("=" * 70)
    print(f"  Total indexed: {final_count:,}")
    print(f"  Errors: {errors:,}")
    print(f"  Time: {elapsed / 60:.1f} minutes")
    print(f"  New dimensions: {EMBEDDING_DIM}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Re-index collection with OpenAI")
    parser.add_argument(
        "--collection",
        required=True,
        choices=["programs", "documents", "jobs", "all"],
        help="Collection to re-index",
    )
    args = parser.parse_args()

    if args.collection == "all":
        for coll in ["programs", "documents", "jobs"]:
            reindex_collection(coll)
            print("\n")
    else:
        reindex_collection(args.collection)


if __name__ == "__main__":
    main()
