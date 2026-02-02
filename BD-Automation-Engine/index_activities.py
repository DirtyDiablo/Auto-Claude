#!/usr/bin/env python3
"""
Index Activities from Bullhorn Master DB to Qdrant
Run in Terminal 1-4

Source: bullhorn_master.db (activities + call_notes tables - 455K+ rows)
Target: Qdrant activities collection
"""

import sys
import os
import sqlite3
import time
from datetime import datetime

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Change to project directory
os.chdir(r"C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine")
sys.path.insert(0, os.getcwd())

from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore

# Configuration
QDRANT_URL = "http://localhost:6333"
DB_PATH = "Engine7_BullhornETL/data/bullhorn_master.db"
BATCH_SIZE = 500  # Larger batches for speed
PROGRESS_INTERVAL = 5000  # Show progress every N records

def get_indexed_count():
    """Get current count of indexed activities."""
    try:
        import urllib.request
        import json
        response = urllib.request.urlopen(f"{QDRANT_URL}/collections/activities", timeout=10)
        data = json.loads(response.read())
        return data["result"]["points_count"]
    except:
        return 0

def main():
    print("=" * 70)
    print("ACTIVITIES INDEXER - Terminal 1-4")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Check source database
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        return

    # Connect to source database
    print(f"\n[1/5] Connecting to source database...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Get total counts
    total_activities = conn.execute("SELECT COUNT(*) FROM activities").fetchone()[0]
    total_call_notes = conn.execute("SELECT COUNT(*) FROM call_notes").fetchone()[0]
    total_placements = conn.execute("SELECT COUNT(*) FROM placements").fetchone()[0]
    total_source = total_activities + total_call_notes + total_placements

    print(f"  activities table: {total_activities:,} rows")
    print(f"  call_notes table: {total_call_notes:,} rows")
    print(f"  placements table: {total_placements:,} rows")
    print(f"  Total source: {total_source:,} rows")

    # Get current indexed count
    current_indexed = get_indexed_count()
    print(f"  Already indexed: {current_indexed:,} activities in Qdrant")

    # Initialize vector store (connects to Qdrant server)
    print(f"\n[2/5] Connecting to Qdrant server at {QDRANT_URL}...")
    store = BDKnowledgeStore(url=QDRANT_URL)
    store.initialize_collections()
    print("  Connected successfully")

    start_time = time.time()
    grand_total_indexed = 0
    grand_total_errors = 0

    # =========================================
    # INDEX ACTIVITIES TABLE
    # =========================================
    print(f"\n[3/5] Indexing ACTIVITIES table ({total_activities:,} rows)...")
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
        ORDER BY id
    """)

    indexed, errors = process_cursor(
        cursor, store, 'activities', total_activities, start_time,
        transform_fn=transform_activity
    )
    grand_total_indexed += indexed
    grand_total_errors += errors

    # =========================================
    # INDEX CALL_NOTES TABLE
    # =========================================
    print(f"\n[4/5] Indexing CALL_NOTES table ({total_call_notes:,} rows)...")
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
        ORDER BY id
    """)

    indexed, errors = process_cursor(
        cursor, store, 'call_notes', total_call_notes, time.time(),
        transform_fn=transform_activity
    )
    grand_total_indexed += indexed
    grand_total_errors += errors

    # =========================================
    # INDEX PLACEMENTS TABLE
    # =========================================
    print(f"\n[5/5] Indexing PLACEMENTS table ({total_placements:,} rows)...")
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
        ORDER BY id
    """)

    indexed, errors = process_cursor(
        cursor, store, 'placements', total_placements, time.time(),
        transform_fn=transform_activity
    )
    grand_total_indexed += indexed
    grand_total_errors += errors

    # Close database
    conn.close()

    # Final stats
    elapsed = time.time() - start_time
    final_indexed = get_indexed_count()

    print("\n" + "=" * 70)
    print("INDEXING COMPLETE")
    print("=" * 70)
    print(f"  Total processed: {grand_total_indexed:,}")
    print(f"  Total errors: {grand_total_errors:,}")
    print(f"  Time elapsed: {elapsed/60:.1f} minutes")
    print(f"  Average rate: {grand_total_indexed/elapsed:.0f} records/sec")
    print(f"  Final Qdrant count: {final_indexed:,} activities")
    print("=" * 70)


def transform_activity(row):
    """Transform database row to activity dict."""
    return {
        'id': f"{row['activity_type']}_{row['id']}",
        'activity_type': row['activity_type'] or 'unknown',
        'content': row['content'] or '',
        'subject': row['subject'] or '',
        'date': row['date'] or '',
        'contact_id': str(row['contact_id']) if row['contact_id'] else '',
        'job_id': str(row['job_id']) if row['job_id'] else '',
        'source_db': 'bullhorn_master',
        'contact_name': '',  # Not available in this query
        'company_name': '',  # Not available in this query
        'company': ''
    }


def process_cursor(cursor, store, source_name, total_count, start_time, transform_fn):
    """Process a database cursor and index records."""
    total_indexed = 0
    total_errors = 0
    batch = []

    for row in cursor:
        # Transform row to activity dict
        activity = transform_fn(row)
        batch.append(activity)

        # Index when batch is full
        if len(batch) >= BATCH_SIZE:
            try:
                indexed, errors = store.index_activities(batch, batch_size=BATCH_SIZE)
                total_indexed += indexed
                total_errors += errors
            except Exception as e:
                print(f"  [ERROR] Batch failed: {e}")
                total_errors += len(batch)

            batch = []

            # Show progress
            if total_indexed % PROGRESS_INTERVAL < BATCH_SIZE:
                elapsed = time.time() - start_time
                rate = total_indexed / elapsed if elapsed > 0 else 0
                remaining = total_count - total_indexed
                eta_seconds = remaining / rate if rate > 0 else 0
                eta_minutes = eta_seconds / 60

                print(f"  [{source_name}] Progress: {total_indexed:,}/{total_count:,} ({total_indexed*100/total_count:.1f}%)")
                print(f"  Rate: {rate:.0f} records/sec | ETA: {eta_minutes:.1f} min | Errors: {total_errors:,}")
                print("-" * 70)

    # Index remaining batch
    if batch:
        try:
            indexed, errors = store.index_activities(batch, batch_size=len(batch))
            total_indexed += indexed
            total_errors += errors
        except Exception as e:
            print(f"  [ERROR] Final batch failed: {e}")
            total_errors += len(batch)

    print(f"  [{source_name}] Completed: {total_indexed:,} indexed, {total_errors:,} errors")
    return total_indexed, total_errors


if __name__ == "__main__":
    main()
