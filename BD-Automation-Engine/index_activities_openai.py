#!/usr/bin/env python3
"""
Index Activities from Bullhorn Master DB to Qdrant using OpenAI Embeddings
MUCH FASTER than local CPU embeddings

Source: bullhorn_master.db (activities + call_notes + placements - 456K rows)
Target: Qdrant activities collection (recreated with OpenAI embeddings)

RESUME CAPABILITY:
  python index_activities_openai.py          # Fresh start (deletes existing)
  python index_activities_openai.py --resume # Resume from where you left off
"""

import sys
import os
import sqlite3
import time
import uuid
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Change to project directory
os.chdir(r"C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine")
load_dotenv()

import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Configuration
QDRANT_URL = "http://localhost:6333"
DB_PATH = "Engine7_BullhornETL/data/bullhorn_master.db"
OPENAI_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
BATCH_SIZE = 500
EMBED_BATCH_SIZE = 100
COLLECTION_NAME = "activities"
PROGRESS_FILE = "index_activities_progress.json"

# Initialize OpenAI client
client_openai = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# UUID namespace for deterministic ID generation
NAMESPACE_ACTIVITIES = uuid.UUID('12345678-1234-5678-1234-567812345678')

def string_to_uuid(s: str) -> str:
    """Convert string ID to deterministic UUID."""
    return str(uuid.uuid5(NAMESPACE_ACTIVITIES, s))


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings from OpenAI API in batches."""
    all_embeddings = []

    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i:i + EMBED_BATCH_SIZE]
        batch = [t if t.strip() else "empty" for t in batch]

        try:
            response = client_openai.embeddings.create(
                model=OPENAI_MODEL,
                input=batch
            )
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)
        except Exception as e:
            print(f"  [ERROR] OpenAI API error: {e}")
            all_embeddings.extend([[0.0] * EMBEDDING_DIM] * len(batch))

    return all_embeddings


def create_text_for_embedding(activity: dict) -> str:
    """Create searchable text from activity fields."""
    parts = [
        activity.get('content', ''),
        activity.get('subject', ''),
        activity.get('activity_type', ''),
        activity.get('contact_name', ''),
        activity.get('company_name', ''),
    ]
    return ' '.join(p for p in parts if p)


def save_progress(table: str, last_id: int, indexed: int):
    """Save progress to file for resume capability."""
    progress = load_progress()
    progress[table] = {'last_id': last_id, 'indexed': indexed}
    progress['timestamp'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)


def load_progress() -> dict:
    """Load progress from file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Index activities to Qdrant')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    args = parser.parse_args()

    print("=" * 70)
    print("ACTIVITIES INDEXER (OpenAI Embeddings)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.resume:
        print("MODE: RESUME (continuing from last checkpoint)")
    else:
        print("MODE: FRESH START (will delete existing data)")
    print("=" * 70)

    # Connect to Qdrant
    print(f"\n[1/6] Connecting to Qdrant at {QDRANT_URL}...")
    qdrant = QdrantClient(url=QDRANT_URL, timeout=300)
    print("  Connected.")

    # Load progress for resume
    progress = load_progress() if args.resume else {}
    already_indexed = 0

    if args.resume:
        try:
            info = qdrant.get_collection(COLLECTION_NAME)
            already_indexed = info.points_count
            print(f"\n[2/6] RESUMING: Collection has {already_indexed:,} points")
            print(f"  Progress: {json.dumps(progress, indent=2)}")
        except:
            print(f"\n[2/6] No existing collection found, starting fresh...")
            qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
            )
            progress = {}
    else:
        # Fresh start - delete and recreate
        print(f"\n[2/6] Recreating '{COLLECTION_NAME}' collection with OpenAI dimensions...")
        try:
            qdrant.delete_collection(COLLECTION_NAME)
            print(f"  Deleted existing collection.")
        except:
            print(f"  No existing collection to delete.")

        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )
        print(f"  Created collection: {COLLECTION_NAME} ({EMBEDDING_DIM} dimensions)")

        # Clear progress file
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)

    # Connect to source database
    print(f"\n[3/6] Connecting to source database...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Get counts
    activities_count = conn.execute("SELECT COUNT(*) FROM activities").fetchone()[0]
    call_notes_count = conn.execute("SELECT COUNT(*) FROM call_notes").fetchone()[0]
    placements_count = conn.execute("SELECT COUNT(*) FROM placements").fetchone()[0]
    total_count = activities_count + call_notes_count + placements_count

    print(f"  activities: {activities_count:,}")
    print(f"  call_notes: {call_notes_count:,}")
    print(f"  placements: {placements_count:,}")
    print(f"  TOTAL: {total_count:,}")

    start_time = time.time()
    grand_total = 0
    grand_errors = 0

    # =========================================
    # INDEX ACTIVITIES TABLE
    # =========================================
    activity_progress = progress.get('activity', {})
    start_id = activity_progress.get('last_id', 0)
    remaining = conn.execute(
        "SELECT COUNT(*) FROM activities WHERE id > ?", (start_id,)
    ).fetchone()[0]

    if remaining > 0:
        print(f"\n[4/6] Indexing ACTIVITIES ({remaining:,} remaining, id > {start_id})...")
        print("-" * 70)

        cursor = conn.execute("""
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
            WHERE id > ?
            ORDER BY id
        """, (start_id,))

        indexed, errors = process_table(
            cursor, qdrant, 'activity', remaining, start_time
        )
        grand_total += indexed
        grand_errors += errors
    else:
        print(f"\n[4/6] ACTIVITIES: Already complete, skipping...")

    # =========================================
    # INDEX CALL_NOTES TABLE
    # =========================================
    call_notes_progress = progress.get('call_note', {})
    start_id = call_notes_progress.get('last_id', 0)
    remaining = conn.execute(
        "SELECT COUNT(*) FROM call_notes WHERE id > ?", (start_id,)
    ).fetchone()[0]

    if remaining > 0:
        print(f"\n[5/6] Indexing CALL_NOTES ({remaining:,} remaining, id > {start_id})...")
        print("-" * 70)

        cursor = conn.execute("""
            SELECT
                id,
                COALESCE(note_type, 'call_note') as activity_type,
                action,
                date_added as date,
                about as contact_id,
                NULL as job_id,
                COALESCE(note_body, '') as content,
                COALESCE(action, 'Call Note') as subject
            FROM call_notes
            WHERE id > ?
            ORDER BY id
        """, (start_id,))

        indexed, errors = process_table(
            cursor, qdrant, 'call_note', remaining, time.time()
        )
        grand_total += indexed
        grand_errors += errors
    else:
        print(f"\n[5/6] CALL_NOTES: Already complete, skipping...")

    # =========================================
    # INDEX PLACEMENTS TABLE
    # =========================================
    placements_progress = progress.get('placement', {})
    start_id = placements_progress.get('last_id', 0)
    remaining = conn.execute(
        "SELECT COUNT(*) FROM placements WHERE id > ?", (start_id,)
    ).fetchone()[0]

    if remaining > 0:
        print(f"\n[6/6] Indexing PLACEMENTS ({remaining:,} remaining, id > {start_id})...")
        print("-" * 70)

        cursor = conn.execute("""
            SELECT
                id,
                'placement' as activity_type,
                status as action,
                placement_date as date,
                candidate_id as contact_id,
                job_id,
                COALESCE(candidate_name, '') || ' at ' || COALESCE(client_name, '') || ' - ' || COALESCE(job_title, '') as content,
                'Placement: ' || COALESCE(status, '') as subject
            FROM placements
            WHERE id > ?
            ORDER BY id
        """, (start_id,))

        indexed, errors = process_table(
            cursor, qdrant, 'placement', remaining, time.time()
        )
        grand_total += indexed
        grand_errors += errors
    else:
        print(f"\n[6/6] PLACEMENTS: Already complete, skipping...")

    conn.close()

    # Final stats
    elapsed = time.time() - start_time
    final_count = qdrant.get_collection(COLLECTION_NAME).points_count

    print("\n" + "=" * 70)
    print("INDEXING COMPLETE")
    print("=" * 70)
    print(f"  This session indexed: {grand_total:,}")
    print(f"  Previously indexed: {already_indexed:,}")
    print(f"  Total in Qdrant: {final_count:,}")
    print(f"  Total errors: {grand_errors:,}")
    print(f"  Time elapsed: {elapsed/60:.1f} minutes")
    if grand_total > 0:
        print(f"  Rate: {grand_total/elapsed:.0f} records/sec")
    print("=" * 70)
    print("\nTo resume later: python index_activities_openai.py --resume")
    print("=" * 70)

    # Clean up progress file if complete
    if final_count >= total_count:
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
            print("  Progress file cleaned up (indexing complete).")


def process_table(cursor, qdrant, prefix: str, total_count: int, start_time: float):
    """Process a database table and index to Qdrant."""
    total_indexed = 0
    total_errors = 0
    batch_activities = []
    batch_texts = []
    last_id = 0

    for row in cursor:
        activity = {
            'id': f"{prefix}_{row['id']}",
            'activity_type': row['activity_type'] or 'unknown',
            'content': row['content'] or '',
            'subject': row['subject'] or '',
            'date': row['date'] or '',
            'contact_id': str(row['contact_id']) if row['contact_id'] else '',
            'job_id': str(row['job_id']) if row['job_id'] else '',
            'source_db': 'bullhorn_master',
            'contact_name': '',
            'company_name': '',
            'company': '',
            '_indexed_at': datetime.now().isoformat(),
            '_embedding_model': OPENAI_MODEL
        }

        text = create_text_for_embedding(activity)
        batch_activities.append(activity)
        batch_texts.append(text)
        last_id = row['id']

        # Process batch
        if len(batch_activities) >= BATCH_SIZE:
            try:
                embeddings = get_embeddings(batch_texts)
                points = [
                    PointStruct(id=string_to_uuid(a['id']), vector=e, payload=a)
                    for a, e in zip(batch_activities, embeddings)
                ]
                qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
                total_indexed += len(points)

                # Save progress after each batch
                save_progress(prefix, last_id, total_indexed)
            except Exception as e:
                print(f"  [ERROR] Batch failed: {e}")
                total_errors += len(batch_activities)

            batch_activities = []
            batch_texts = []

            # Progress
            elapsed = time.time() - start_time
            rate = total_indexed / elapsed if elapsed > 0 else 0
            remaining = total_count - total_indexed
            eta = remaining / rate if rate > 0 else 0

            print(f"  [{prefix}] {total_indexed:,}/{total_count:,} ({100*total_indexed/total_count:.1f}%)")
            print(f"  Rate: {rate:.0f}/sec | ETA: {eta/60:.1f} min | Errors: {total_errors}")
            print("-" * 70)

    # Remaining batch
    if batch_activities:
        try:
            embeddings = get_embeddings(batch_texts)
            points = [
                PointStruct(id=string_to_uuid(a['id']), vector=e, payload=a)
                for a, e in zip(batch_activities, embeddings)
            ]
            qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
            total_indexed += len(points)
            save_progress(prefix, last_id, total_indexed)
        except Exception as e:
            print(f"  [ERROR] Final batch failed: {e}")
            total_errors += len(batch_activities)

    print(f"  [{prefix}] Done: {total_indexed:,} indexed, {total_errors:,} errors")
    return total_indexed, total_errors


if __name__ == "__main__":
    main()
