#!/usr/bin/env python3
"""
Parallel Worker for Indexing to Qdrant using OpenAI Embeddings
Handles both contacts and activities with ID range splitting

Usage:
  # Contacts - Worker 1 (first half of remaining)
  python index_parallel_worker.py --type contacts --start-id 82001 --end-id 254000 --worker 1

  # Contacts - Worker 2 (second half)
  python index_parallel_worker.py --type contacts --start-id 254001 --end-id 426565 --worker 2

  # Activities - Worker 1
  python index_parallel_worker.py --type activities --start-id 1 --end-id 202000 --worker 1

  # Activities - Worker 2
  python index_parallel_worker.py --type activities --start-id 202001 --end-id 404715 --worker 2
"""

import sys
import os
import sqlite3
import time
import json
import uuid
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Fix Windows encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Change to project directory
os.chdir(r"C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine")
load_dotenv()

import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Configuration - OPTIMIZED FOR SPEED
QDRANT_URL = "http://localhost:6333"
DB_PATH = "Engine7_BullhornETL/data/bullhorn_master.db"
OPENAI_MODEL = "text-embedding-3-small"  # $0.00002 per 1K tokens
EMBEDDING_DIM = 1536
BATCH_SIZE = 1000  # Records per Qdrant upsert (increased from 500)
EMBED_BATCH_SIZE = 2000  # Texts per OpenAI API call (increased from 100, max is 2048)
QDRANT_TIMEOUT = 600  # Increased timeout for slow Qdrant

# Initialize OpenAI client
client_openai = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# UUID namespaces for deterministic ID generation
NAMESPACE_CONTACTS = uuid.UUID("87654321-4321-8765-4321-876543218765")
NAMESPACE_ACTIVITIES = uuid.UUID("12345678-1234-5678-1234-567812345678")


def id_to_uuid(record_id: int, namespace: uuid.UUID) -> str:
    """Convert integer ID to deterministic UUID."""
    return str(uuid.uuid5(namespace, str(record_id)))


def string_to_uuid(s: str, namespace: uuid.UUID) -> str:
    """Convert string ID to deterministic UUID."""
    return str(uuid.uuid5(namespace, s))


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings from OpenAI API in batches."""
    all_embeddings = []

    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        # Clean texts - OpenAI doesn't like empty strings
        batch = [t if t.strip() else "empty" for t in batch]

        try:
            response = client_openai.embeddings.create(model=OPENAI_MODEL, input=batch)
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)
        except Exception as e:
            print(f"  [ERROR] OpenAI API error: {e}")
            # Return zero vectors on error
            all_embeddings.extend([[0.0] * EMBEDDING_DIM] * len(batch))

    return all_embeddings


def classify_tier(title: str) -> str:
    """Classify contact into tier based on title."""
    title = (title or "").lower()

    tier1 = [
        "ceo",
        "cto",
        "cio",
        "cfo",
        "president",
        "vice president",
        "vp",
        "director",
        "chief",
        "partner",
        "owner",
        "founder",
        "general manager",
    ]
    for kw in tier1:
        if kw in title:
            return "Tier 1"

    tier2 = ["senior", "manager", "lead", "head", "principal", "supervisor"]
    for kw in tier2:
        if kw in title:
            return "Tier 2"

    tier3 = [
        "engineer",
        "analyst",
        "specialist",
        "consultant",
        "developer",
        "architect",
    ]
    for kw in tier3:
        if kw in title:
            return "Tier 3"

    return "Tier 4"


def save_progress(progress_file: str, last_id: int, indexed: int, worker: int):
    """Save progress to file."""
    with open(progress_file, "w") as f:
        json.dump(
            {
                "last_id": last_id,
                "indexed": indexed,
                "worker": worker,
                "timestamp": datetime.now().isoformat(),
            },
            f,
        )


def index_contacts(qdrant, conn, start_id: int, end_id: int, worker: int):
    """Index contacts from candidates table."""
    collection_name = "contacts"
    progress_file = f"index_contacts_worker{worker}_progress.json"

    # Ensure collection exists with retry logic
    for attempt in range(3):
        try:
            qdrant.get_collection(collection_name)
            print(f"  Collection '{collection_name}' exists.")
            break
        except Exception as e:
            if "not found" in str(e).lower() or "doesn't exist" in str(e).lower():
                print(f"  Creating collection '{collection_name}'...")
                qdrant.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIM, distance=Distance.COSINE
                    ),
                )
                break
            else:
                print(f"  Attempt {attempt + 1}/3: Qdrant slow, waiting... ({e})")
                time.sleep(10 * (attempt + 1))
                if attempt == 2:
                    raise Exception(f"Qdrant not responding after 3 attempts: {e}")

    # Count records in range
    total_in_range = conn.execute(
        "SELECT COUNT(*) FROM candidates WHERE id >= ? AND id <= ?", (start_id, end_id)
    ).fetchone()[0]

    print(f"\n  Worker {worker}: Indexing contacts {start_id:,} - {end_id:,}")
    print(f"  Total records in range: {total_in_range:,}")
    print("-" * 70)

    # Fetch candidates in range
    cursor = conn.execute(
        """
        SELECT
            id,
            first_name,
            last_name,
            COALESCE(full_name, COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')) as name,
            job_title as title,
            COALESCE(company_name, current_employer) as company,
            email,
            COALESCE(phone, mobile) as phone,
            address,
            city,
            state,
            status,
            source_file as source,
            date_added,
            date_modified,
            custom_text1 as notes,
            clearance_level as clearance,
            custom_text3 as program
        FROM candidates
        WHERE id >= ? AND id <= ?
        ORDER BY id
    """,
        (start_id, end_id),
    )

    # Process in batches
    indexed = 0
    errors = 0
    batch_contacts = []
    batch_texts = []
    start_time = time.time()
    last_id_processed = start_id

    for row in cursor:
        contact = {
            "id": str(row["id"]),
            "first_name": row["first_name"] or "",
            "last_name": row["last_name"] or "",
            "name": row["name"] or "",
            "title": row["title"] or "",
            "company": row["company"] or "",
            "email": row["email"] or "",
            "phone": row["phone"] or "",
            "address": row["address"] or "",
            "city": row["city"] or "",
            "state": row["state"] or "",
            "status": row["status"] or "",
            "source": row["source"] or "",
            "source_db": "bullhorn_master",
            "date_added": row["date_added"] or "",
            "date_modified": row["date_modified"] or "",
            "notes": row["notes"] or "",
            "clearance": row["clearance"] or "",
            "program": row["program"] or "",
            "tier": classify_tier(row["title"]),
            "_indexed_at": datetime.now().isoformat(),
            "_embedding_model": OPENAI_MODEL,
            "_worker": worker,
        }

        # Create text for embedding
        parts = [
            contact["name"],
            contact["title"],
            contact["company"],
            contact["program"],
            contact["notes"],
            contact["city"],
            contact["state"],
        ]
        text = " ".join(p for p in parts if p)

        batch_contacts.append(contact)
        batch_texts.append(text)
        last_id_processed = row["id"]

        # Process batch
        if len(batch_contacts) >= BATCH_SIZE:
            try:
                embeddings = get_embeddings(batch_texts)
                points = [
                    PointStruct(
                        id=id_to_uuid(int(c["id"]), NAMESPACE_CONTACTS),
                        vector=e,
                        payload=c,
                    )
                    for c, e in zip(batch_contacts, embeddings)
                ]
                qdrant.upsert(collection_name=collection_name, points=points)
                indexed += len(points)
                save_progress(progress_file, last_id_processed, indexed, worker)
            except Exception as e:
                print(f"  [ERROR] Batch failed: {e}")
                errors += len(batch_contacts)

            batch_contacts = []
            batch_texts = []

            # Progress update
            elapsed = time.time() - start_time
            rate = indexed / elapsed if elapsed > 0 else 0
            remaining = total_in_range - indexed
            eta = remaining / rate if rate > 0 else 0

            print(
                f"  [W{worker}] {indexed:,}/{total_in_range:,} ({100 * indexed / total_in_range:.1f}%) | "
                f"Rate: {rate:.0f}/sec | ETA: {eta / 60:.1f} min"
            )

    # Process remaining batch
    if batch_contacts:
        try:
            embeddings = get_embeddings(batch_texts)
            points = [
                PointStruct(
                    id=id_to_uuid(int(c["id"]), NAMESPACE_CONTACTS), vector=e, payload=c
                )
                for c, e in zip(batch_contacts, embeddings)
            ]
            qdrant.upsert(collection_name=collection_name, points=points)
            indexed += len(points)
            save_progress(progress_file, last_id_processed, indexed, worker)
        except Exception as e:
            print(f"  [ERROR] Final batch failed: {e}")
            errors += len(batch_contacts)

    return indexed, errors


def index_activities(qdrant, conn, start_id: int, end_id: int, worker: int):
    """Index activities from activities table."""
    collection_name = "activities"
    progress_file = f"index_activities_worker{worker}_progress.json"

    # Ensure collection exists with retry logic
    for attempt in range(3):
        try:
            qdrant.get_collection(collection_name)
            print(f"  Collection '{collection_name}' exists.")
            break
        except Exception as e:
            if "not found" in str(e).lower() or "doesn't exist" in str(e).lower():
                print(f"  Creating collection '{collection_name}'...")
                qdrant.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIM, distance=Distance.COSINE
                    ),
                )
                break
            else:
                print(f"  Attempt {attempt + 1}/3: Qdrant slow, waiting... ({e})")
                time.sleep(10 * (attempt + 1))
                if attempt == 2:
                    raise Exception(f"Qdrant not responding after 3 attempts: {e}")

    # Count records in range
    total_in_range = conn.execute(
        "SELECT COUNT(*) FROM activities WHERE id >= ? AND id <= ?", (start_id, end_id)
    ).fetchone()[0]

    print(f"\n  Worker {worker}: Indexing activities {start_id:,} - {end_id:,}")
    print(f"  Total records in range: {total_in_range:,}")
    print("-" * 70)

    # Fetch activities in range
    cursor = conn.execute(
        """
        SELECT
            id,
            activity_type,
            action,
            activity_date as date,
            related_candidate_id as contact_id,
            related_job_id as job_id,
            COALESCE(comments, '') as content,
            COALESCE(note_text, '') as subject
        FROM activities
        WHERE id >= ? AND id <= ?
        ORDER BY id
    """,
        (start_id, end_id),
    )

    # Process in batches
    indexed = 0
    errors = 0
    batch_activities = []
    batch_texts = []
    start_time = time.time()
    last_id_processed = start_id

    for row in cursor:
        activity = {
            "id": f"activity_{row['id']}",
            "activity_type": row["activity_type"] or "unknown",
            "content": row["content"] or "",
            "subject": row["subject"] or "",
            "date": row["date"] or "",
            "contact_id": str(row["contact_id"]) if row["contact_id"] else "",
            "job_id": str(row["job_id"]) if row["job_id"] else "",
            "source_db": "bullhorn_master",
            "_indexed_at": datetime.now().isoformat(),
            "_embedding_model": OPENAI_MODEL,
            "_worker": worker,
        }

        # Create text for embedding
        parts = [activity["content"], activity["subject"], activity["activity_type"]]
        text = " ".join(p for p in parts if p)

        batch_activities.append(activity)
        batch_texts.append(text)
        last_id_processed = row["id"]

        # Process batch
        if len(batch_activities) >= BATCH_SIZE:
            try:
                embeddings = get_embeddings(batch_texts)
                points = [
                    PointStruct(
                        id=string_to_uuid(a["id"], NAMESPACE_ACTIVITIES),
                        vector=e,
                        payload=a,
                    )
                    for a, e in zip(batch_activities, embeddings)
                ]
                qdrant.upsert(collection_name=collection_name, points=points)
                indexed += len(points)
                save_progress(progress_file, last_id_processed, indexed, worker)
            except Exception as e:
                print(f"  [ERROR] Batch failed: {e}")
                errors += len(batch_activities)

            batch_activities = []
            batch_texts = []

            # Progress update
            elapsed = time.time() - start_time
            rate = indexed / elapsed if elapsed > 0 else 0
            remaining = total_in_range - indexed
            eta = remaining / rate if rate > 0 else 0

            print(
                f"  [W{worker}] {indexed:,}/{total_in_range:,} ({100 * indexed / total_in_range:.1f}%) | "
                f"Rate: {rate:.0f}/sec | ETA: {eta / 60:.1f} min"
            )

    # Process remaining batch
    if batch_activities:
        try:
            embeddings = get_embeddings(batch_texts)
            points = [
                PointStruct(
                    id=string_to_uuid(a["id"], NAMESPACE_ACTIVITIES),
                    vector=e,
                    payload=a,
                )
                for a, e in zip(batch_activities, embeddings)
            ]
            qdrant.upsert(collection_name=collection_name, points=points)
            indexed += len(points)
            save_progress(progress_file, last_id_processed, indexed, worker)
        except Exception as e:
            print(f"  [ERROR] Final batch failed: {e}")
            errors += len(batch_activities)

    return indexed, errors


def main():
    parser = argparse.ArgumentParser(description="Parallel indexing worker")
    parser.add_argument(
        "--type",
        required=True,
        choices=["contacts", "activities"],
        help="Type of data to index",
    )
    parser.add_argument(
        "--start-id", type=int, required=True, help="Start ID (inclusive)"
    )
    parser.add_argument("--end-id", type=int, required=True, help="End ID (inclusive)")
    parser.add_argument(
        "--worker", type=int, required=True, help="Worker number (1 or 2)"
    )
    args = parser.parse_args()

    print("=" * 70)
    print(f"PARALLEL INDEXER - Worker {args.worker}")
    print(f"Type: {args.type.upper()}")
    print(f"ID Range: {args.start_id:,} - {args.end_id:,}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Batch sizes: QDRANT={BATCH_SIZE}, OPENAI={EMBED_BATCH_SIZE}")
    print("=" * 70)

    # Connect to Qdrant
    print(f"\nConnecting to Qdrant at {QDRANT_URL}...")
    qdrant = QdrantClient(url=QDRANT_URL, timeout=QDRANT_TIMEOUT)
    print("  Connected.")

    # Connect to database
    print(f"Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    print("  Connected.")

    start_time = time.time()

    if args.type == "contacts":
        indexed, errors = index_contacts(
            qdrant, conn, args.start_id, args.end_id, args.worker
        )
    else:
        indexed, errors = index_activities(
            qdrant, conn, args.start_id, args.end_id, args.worker
        )

    conn.close()

    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print(f"WORKER {args.worker} COMPLETE")
    print("=" * 70)
    print(f"  Indexed: {indexed:,}")
    print(f"  Errors: {errors:,}")
    print(f"  Time: {elapsed / 60:.1f} minutes")
    if indexed > 0:
        print(f"  Rate: {indexed / elapsed:.0f} records/sec")
    print("=" * 70)


if __name__ == "__main__":
    main()
