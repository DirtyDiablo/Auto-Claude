"""
Incremental Update Detection
Compares current record hashes against source_tracking.record_hash.
Only re-processes changed records for efficiency.
"""
import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.master_db.utils import compute_hash

DB_PATH = PROJECT_ROOT / "data" / "unified_federal_contracts.db"

TRACKED_TABLES = [
    "contacts", "programs", "companies", "contracts",
    "jobs", "intelligence", "activities",
]


def detect_changes(conn, table):
    """Detect changed records by comparing hashes."""
    cursor = conn.cursor()

    # Get current records
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    cols_str = ", ".join(f"[{c}]" for c in columns)

    cursor.execute(f"SELECT {cols_str} FROM {table}")
    rows = cursor.fetchall()

    changed = []
    new_records = []

    for row in rows:
        record = dict(zip(columns, row))
        record_id = record.get("id", "")
        if not record_id:
            continue

        current_hash = compute_hash(record)

        # Check stored hash
        cursor.execute("""
            SELECT record_hash FROM source_tracking
            WHERE table_name = ? AND record_id = ?
            ORDER BY last_updated DESC LIMIT 1
        """, (table, record_id))
        stored = cursor.fetchone()

        if stored is None:
            new_records.append(record_id)
            # Insert tracking record
            cursor.execute("""
                INSERT OR REPLACE INTO source_tracking
                (table_name, record_id, source_file, source_type, record_hash)
                VALUES (?, ?, 'unified_db', 'incremental', ?)
            """, (table, record_id, current_hash))
        elif stored[0] != current_hash:
            changed.append(record_id)
            cursor.execute("""
                UPDATE source_tracking SET record_hash = ?, last_updated = datetime('now')
                WHERE table_name = ? AND record_id = ?
            """, (current_hash, table, record_id))

    return changed, new_records


def run(db_path=None):
    """Run incremental change detection."""
    db_path = db_path or DB_PATH
    print("Incremental Update Detection")
    print(f"  Database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    total_changed = 0
    total_new = 0

    try:
        for table in TRACKED_TABLES:
            changed, new_records = detect_changes(conn, table)
            if changed or new_records:
                print(f"  {table}: {len(changed)} changed, {len(new_records)} new")
            total_changed += len(changed)
            total_new += len(new_records)

        conn.commit()
    finally:
        conn.close()

    print(f"  Total: {total_changed} changed, {total_new} new records")
    return total_changed, total_new


if __name__ == "__main__":
    run()
