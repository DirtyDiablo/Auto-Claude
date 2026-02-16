#!/usr/bin/env python3
"""
Index Contacts from Bullhorn Master DB to Qdrant using OpenAI Embeddings
MUCH FASTER than local CPU embeddings

Source: bullhorn_master.db (candidates table - 426,565 rows)
Target: Qdrant contacts collection (recreated with OpenAI embeddings)

RESUME CAPABILITY:
  python index_contacts_openai.py          # Fresh start (deletes existing)
  python index_contacts_openai.py --resume # Resume from where you left off
"""

import sys
import os
import logging

logger = logging.getLogger(__name__)
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

# Configuration
QDRANT_URL = "http://localhost:6333"
DB_PATH = "Engine7_BullhornETL/data/bullhorn_master.db"
OPENAI_MODEL = "text-embedding-3-small"  # $0.00002 per 1K tokens
EMBEDDING_DIM = 1536
BATCH_SIZE = 500  # Records per Qdrant upsert
EMBED_BATCH_SIZE = 100  # Texts per OpenAI API call (max 2048)
COLLECTION_NAME = "contacts"
PROGRESS_FILE = "index_contacts_progress.json"  # Track progress for resume

# Initialize OpenAI client
client_openai = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# UUID namespace for deterministic ID generation
NAMESPACE_CONTACTS = uuid.UUID("87654321-4321-8765-4321-876543218765")


def id_to_uuid(record_id: int) -> str:
    """Convert integer ID to deterministic UUID."""
    return str(uuid.uuid5(NAMESPACE_CONTACTS, str(record_id)))


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


def create_text_for_embedding(contact: dict) -> str:
    """Create searchable text from contact fields."""
    parts = [
        contact.get("name", ""),
        contact.get("title", ""),
        contact.get("company", ""),
        contact.get("program", ""),
        contact.get("notes", ""),
        contact.get("city", ""),
        contact.get("state", ""),
    ]
    return " ".join(p for p in parts if p)


def classify_tier(row) -> str:
    """Classify contact into tier based on title."""
    title = (row["title"] or "").lower()

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


def save_progress(last_id: int, indexed: int):
    """Save progress to file for resume capability."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(
            {
                "last_id": last_id,
                "indexed": indexed,
                "timestamp": datetime.now().isoformat(),
            },
            f,
        )


def load_progress() -> dict:
    """Load progress from file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"last_id": 0, "indexed": 0}


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Index contacts to Qdrant")
    parser.add_argument(
        "--resume", action="store_true", help="Resume from last checkpoint"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("CONTACTS INDEXER (OpenAI Embeddings)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.resume:
        print("MODE: RESUME (continuing from last checkpoint)")
    else:
        print("MODE: FRESH START (will delete existing data)")
    print("=" * 70)

    # Connect to Qdrant
    print(f"\n[1/5] Connecting to Qdrant at {QDRANT_URL}...")
    qdrant = QdrantClient(
        url=QDRANT_URL, timeout=600
    )  # 10 min timeout for slow operations
    print("  Connected.")

    # Handle collection based on mode
    start_from_id = 0
    already_indexed = 0

    if args.resume:
        # Check if collection exists
        try:
            print(f"\n[2/5] Checking for existing collection...")
            info = qdrant.get_collection(COLLECTION_NAME)
            already_indexed = info.points_count
            progress = load_progress()
            start_from_id = progress.get("last_id", 0)
            print(f"  RESUMING: Collection has {already_indexed:,} points")
            print(f"  Will skip records with id <= {start_from_id}")
        except Exception as e:
            print(
                f"\n[2/5] No existing collection found ({type(e).__name__}), starting fresh..."
            )
            qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM, distance=Distance.COSINE
                ),
            )
    else:
        # Fresh start - delete and recreate
        print(
            f"\n[2/5] Recreating '{COLLECTION_NAME}' collection with OpenAI dimensions..."
        )
        try:
            qdrant.delete_collection(COLLECTION_NAME)
            print(f"  Deleted existing collection.")
        except Exception as e:
            logger.debug("collection_delete_skipped: %s", e)
            print(f"  No existing collection to delete.")

        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        print(f"  Created collection: {COLLECTION_NAME} ({EMBEDDING_DIM} dimensions)")

        # Clear progress file
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)

    # Connect to source database
    print(f"\n[3/5] Connecting to source database...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    total_count = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    remaining_count = conn.execute(
        "SELECT COUNT(*) FROM candidates WHERE id > ?", (start_from_id,)
    ).fetchone()[0]
    print(f"  Source: {total_count:,} candidates total")
    print(f"  Remaining to index: {remaining_count:,}")

    if remaining_count == 0:
        print("\n  *** All records already indexed! Nothing to do. ***")
        conn.close()
        return

    # Fetch candidates starting from resume point
    print(f"\n[4/5] Fetching candidates (id > {start_from_id})...")
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
        WHERE id > ?
        ORDER BY id
    """,
        (start_from_id,),
    )

    # Process in batches
    print(f"\n[5/5] Indexing with OpenAI embeddings (batch size: {BATCH_SIZE})...")
    print("-" * 70)

    session_indexed = 0
    total_errors = 0
    batch_contacts = []
    batch_texts = []
    start_time = time.time()
    last_id = start_from_id

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
            "tier": classify_tier(row),
            "_indexed_at": datetime.now().isoformat(),
            "_embedding_model": OPENAI_MODEL,
        }

        text = create_text_for_embedding(contact)
        batch_contacts.append(contact)
        batch_texts.append(text)
        last_id = row["id"]

        # Process batch
        if len(batch_contacts) >= BATCH_SIZE:
            try:
                # Get embeddings from OpenAI
                embeddings = get_embeddings(batch_texts)

                # Create points
                points = [
                    PointStruct(
                        id=id_to_uuid(int(contact["id"])),
                        vector=embedding,
                        payload=contact,
                    )
                    for contact, embedding in zip(batch_contacts, embeddings)
                ]

                # Upsert to Qdrant
                qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
                session_indexed += len(points)

                # Save progress after each batch
                save_progress(last_id, already_indexed + session_indexed)

            except Exception as e:
                print(f"  [ERROR] Batch failed: {e}")
                total_errors += len(batch_contacts)

            # Reset batch
            batch_contacts = []
            batch_texts = []

            # Progress update
            total_indexed = already_indexed + session_indexed
            elapsed = time.time() - start_time
            rate = session_indexed / elapsed if elapsed > 0 else 0
            remaining = remaining_count - session_indexed
            eta = remaining / rate if rate > 0 else 0

            print(
                f"  Progress: {total_indexed:,}/{total_count:,} ({100 * total_indexed / total_count:.1f}%)"
            )
            print(
                f"  This session: {session_indexed:,} | Rate: {rate:.0f}/sec | ETA: {eta / 60:.1f} min"
            )
            print("-" * 70)

    # Process remaining batch
    if batch_contacts:
        try:
            embeddings = get_embeddings(batch_texts)
            points = [
                PointStruct(id=id_to_uuid(int(c["id"])), vector=e, payload=c)
                for c, e in zip(batch_contacts, embeddings)
            ]
            qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
            session_indexed += len(points)
            save_progress(last_id, already_indexed + session_indexed)
        except Exception as e:
            print(f"  [ERROR] Final batch failed: {e}")
            total_errors += len(batch_contacts)

    conn.close()

    # Final stats
    elapsed = time.time() - start_time
    final_count = qdrant.get_collection(COLLECTION_NAME).points_count

    print("\n" + "=" * 70)
    print("INDEXING COMPLETE")
    print("=" * 70)
    print(f"  This session indexed: {session_indexed:,}")
    print(f"  Previously indexed: {already_indexed:,}")
    print(f"  Total in Qdrant: {final_count:,}")
    print(f"  Total errors: {total_errors:,}")
    print(f"  Time elapsed: {elapsed / 60:.1f} minutes")
    if session_indexed > 0:
        print(f"  Rate: {session_indexed / elapsed:.0f} records/sec")
    print("=" * 70)
    print("\nTo resume later: python index_contacts_openai.py --resume")
    print("=" * 70)

    # Clean up progress file if complete
    if final_count >= total_count:
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
            print("  Progress file cleaned up (indexing complete).")


if __name__ == "__main__":
    main()
