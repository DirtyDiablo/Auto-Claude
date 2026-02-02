#!/usr/bin/env python3
"""
Index Contacts from Bullhorn Master DB to Qdrant
Run in Terminal 1-3

Source: bullhorn_master.db (candidates table - 426,565 rows)
Target: Qdrant contacts collection
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
    """Get current count of indexed contacts."""
    try:
        import urllib.request
        import json
        response = urllib.request.urlopen(f"{QDRANT_URL}/collections/contacts", timeout=10)
        data = json.loads(response.read())
        return data["result"]["points_count"]
    except:
        return 0

def main():
    print("=" * 70)
    print("CONTACTS INDEXER - Terminal 1-3")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Check source database
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        return

    # Connect to source database
    print(f"\n[1/4] Connecting to source database...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Get total count
    total_candidates = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    print(f"  Source: {total_candidates:,} candidates in bullhorn_master.db")

    # Get current indexed count
    current_indexed = get_indexed_count()
    print(f"  Already indexed: {current_indexed:,} contacts in Qdrant")

    # Initialize vector store (connects to Qdrant server)
    print(f"\n[2/4] Connecting to Qdrant server at {QDRANT_URL}...")
    store = BDKnowledgeStore(url=QDRANT_URL)
    store.initialize_collections()
    print("  Connected successfully")

    # Fetch candidates
    print(f"\n[3/4] Fetching candidates from database...")
    cursor = conn.execute("""
        SELECT
            id,
            firstName as first_name,
            lastName as last_name,
            COALESCE(firstName, '') || ' ' || COALESCE(lastName, '') as name,
            title,
            companyName as company,
            email,
            phone,
            address,
            city,
            state,
            status,
            source,
            dateAdded as date_added,
            dateLastModified as date_modified,
            customText1 as notes,
            customText2 as clearance,
            customText3 as program
        FROM candidates
        ORDER BY id
    """)

    # Process in batches
    print(f"\n[4/4] Indexing contacts (batch size: {BATCH_SIZE})...")
    print("-" * 70)

    total_indexed = 0
    total_errors = 0
    batch = []
    start_time = time.time()
    last_progress_time = start_time

    for row in cursor:
        # Convert row to dict
        contact = {
            'id': str(row['id']),
            'first_name': row['first_name'] or '',
            'last_name': row['last_name'] or '',
            'name': row['name'] or '',
            'title': row['title'] or '',
            'company': row['company'] or '',
            'email': row['email'] or '',
            'phone': row['phone'] or '',
            'address': row['address'] or '',
            'city': row['city'] or '',
            'state': row['state'] or '',
            'status': row['status'] or '',
            'source': row['source'] or '',
            'source_db': 'bullhorn_master',
            'date_added': row['date_added'] or '',
            'date_modified': row['date_modified'] or '',
            'notes': row['notes'] or '',
            'clearance': row['clearance'] or '',
            'program': row['program'] or '',
            'tier': classify_tier(row)
        }

        batch.append(contact)

        # Index when batch is full
        if len(batch) >= BATCH_SIZE:
            try:
                indexed, errors = store.index_contacts(batch, batch_size=BATCH_SIZE)
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
                remaining = total_candidates - total_indexed
                eta_seconds = remaining / rate if rate > 0 else 0
                eta_minutes = eta_seconds / 60

                print(f"  Progress: {total_indexed:,}/{total_candidates:,} ({total_indexed*100/total_candidates:.1f}%)")
                print(f"  Rate: {rate:.0f} records/sec | ETA: {eta_minutes:.1f} minutes")
                print(f"  Errors: {total_errors:,}")
                print("-" * 70)

    # Index remaining batch
    if batch:
        try:
            indexed, errors = store.index_contacts(batch, batch_size=len(batch))
            total_indexed += indexed
            total_errors += errors
        except Exception as e:
            print(f"  [ERROR] Final batch failed: {e}")
            total_errors += len(batch)

    # Close database
    conn.close()

    # Final stats
    elapsed = time.time() - start_time
    final_indexed = get_indexed_count()

    print("\n" + "=" * 70)
    print("INDEXING COMPLETE")
    print("=" * 70)
    print(f"  Total processed: {total_indexed:,}")
    print(f"  Total errors: {total_errors:,}")
    print(f"  Time elapsed: {elapsed/60:.1f} minutes")
    print(f"  Average rate: {total_indexed/elapsed:.0f} records/sec")
    print(f"  Final Qdrant count: {final_indexed:,} contacts")
    print("=" * 70)


def classify_tier(row):
    """Classify contact into tier based on available data."""
    title = (row['title'] or '').lower()

    # Tier 1: Executive/Decision Maker
    tier1_keywords = ['ceo', 'cto', 'cio', 'cfo', 'president', 'vice president', 'vp',
                      'director', 'chief', 'partner', 'owner', 'founder', 'general manager']
    for kw in tier1_keywords:
        if kw in title:
            return 'Tier 1'

    # Tier 2: Senior/Manager
    tier2_keywords = ['senior', 'manager', 'lead', 'head', 'principal', 'supervisor']
    for kw in tier2_keywords:
        if kw in title:
            return 'Tier 2'

    # Tier 3: Mid-level
    tier3_keywords = ['engineer', 'analyst', 'specialist', 'consultant', 'developer', 'architect']
    for kw in tier3_keywords:
        if kw in title:
            return 'Tier 3'

    # Default
    return 'Tier 4'


if __name__ == "__main__":
    main()
