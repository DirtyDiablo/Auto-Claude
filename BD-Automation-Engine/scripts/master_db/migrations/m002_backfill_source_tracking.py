"""
Migration 002: Backfill source_tracking table from source_files/source_file columns.
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "unified_federal_contracts.db"

# Tables and their source file column names
TABLE_SOURCE_COLUMNS = {
    "programs": "source_files",
    "companies": "source_files",
    "contracts": "source_file",
    "task_orders": "source_file",
    "contacts": "source_files",
    "jobs": "source_file",
    "placements": "source_file",
    "activities": "source_file",
    "intelligence": "source_file",
    "documents": "source",
}


def parse_source_files(value):
    """Parse source file value - could be JSON array, comma-separated, or single value."""
    if not value:
        return []
    value = str(value).strip()
    if not value or value.lower() in ("none", "nan", "null"):
        return []

    # Try JSON array
    if value.startswith("["):
        try:
            parsed = json.loads(value)
            return [str(s).strip() for s in parsed if s]
        except json.JSONDecodeError:
            pass

    # Comma-separated
    if "," in value:
        return [s.strip() for s in value.split(",") if s.strip()]

    return [value]


def backfill_table(conn, table, source_col):
    """Backfill source_tracking for one table."""
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    if source_col not in cols:
        print(f"  {table}: column '{source_col}' not found, skipping")
        return 0

    cursor.execute(f"SELECT id, [{source_col}] FROM {table} WHERE [{source_col}] IS NOT NULL")
    rows = cursor.fetchall()

    count = 0
    for record_id, source_val in rows:
        sources = parse_source_files(source_val)
        for source_file in sources:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO source_tracking
                    (table_name, record_id, source_file, source_type)
                    VALUES (?, ?, ?, ?)
                """, (table, record_id, source_file, _infer_source_type(source_file)))
                count += cursor.rowcount
            except sqlite3.IntegrityError:
                pass

    return count


def _infer_source_type(source_file):
    """Infer source type from file path/name."""
    s = source_file.lower()
    if "bullhorn" in s:
        return "bullhorn_etl"
    if "tango" in s:
        return "tango_scraper"
    if "fpds" in s:
        return "fpds_api"
    if "usaspending" in s:
        return "usaspending_api"
    if "sam" in s:
        return "sam_gov"
    if "scraper" in s or "scraped" in s:
        return "web_scraper"
    if "manual" in s or "spreadsheet" in s:
        return "manual_entry"
    return "unknown"


def run(db_path=None):
    """Run migration 002."""
    db_path = db_path or DB_PATH
    print(f"Migration 002: Backfill source_tracking")
    print(f"  Database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    total = 0
    try:
        for table, source_col in TABLE_SOURCE_COLUMNS.items():
            count = backfill_table(conn, table, source_col)
            if count > 0:
                print(f"  {table}: {count} entries added")
            total += count
        conn.commit()
    finally:
        conn.close()

    print(f"  Migration 002 complete: {total} total source_tracking entries")


if __name__ == "__main__":
    run()
