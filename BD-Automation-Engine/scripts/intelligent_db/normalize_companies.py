"""
Normalize company names across all tables in the unified database.
Uses normalize_company_name() from master_db utils.
"""
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.master_db.utils import normalize_company_name, generate_id

DB_PATH = PROJECT_ROOT / "data" / "unified_federal_contracts.db"

# Tables and columns to normalize
NORMALIZE_TARGETS = [
    ("contacts", "company"),
    ("contracts", "recipient_name"),
    ("jobs", "company"),
    ("jobs", "prime"),
    ("task_orders", "prime_name"),
    ("task_orders", "sub_recipient_name"),
    ("programs", "prime_contractor"),
    ("intelligence", "company_name"),
]


def normalize_table_column(conn, table, column):
    """Normalize a single column in a table. Returns count of updates."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT DISTINCT [{column}] FROM {table} WHERE [{column}] IS NOT NULL")
    raw_names = [row[0] for row in cursor.fetchall()]

    updated = 0
    for raw in raw_names:
        normalized = normalize_company_name(raw)
        if normalized and normalized != raw:
            cursor.execute(
                f"UPDATE {table} SET [{column}] = ? WHERE [{column}] = ?",
                (normalized, raw)
            )
            updated += cursor.rowcount

    return updated


def build_company_aliases(conn):
    """Build aliases for each company by collecting all variant names seen."""
    cursor = conn.cursor()

    # Collect all company names from all tables
    all_names = defaultdict(set)

    for table, column in NORMALIZE_TARGETS:
        try:
            cursor.execute(f"SELECT DISTINCT [{column}] FROM {table} WHERE [{column}] IS NOT NULL")
            for (name,) in cursor.fetchall():
                normalized = normalize_company_name(name)
                if normalized:
                    all_names[normalized].add(name)
        except sqlite3.OperationalError:
            continue

    # Update companies table
    updated = 0
    for normalized, variants in all_names.items():
        aliases = json.dumps(sorted(variants - {normalized})) if len(variants) > 1 else None
        cursor.execute("""
            UPDATE companies SET normalized_name = ?, aliases = ?
            WHERE name = ? OR normalized_name = ?
        """, (normalized, aliases, normalized, normalized))
        if cursor.rowcount > 0:
            updated += cursor.rowcount

    return updated, len(all_names)


def run(db_path=None):
    """Run company name normalization."""
    db_path = db_path or DB_PATH
    print("Company Name Normalization")
    print(f"  Database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        total = 0
        for table, column in NORMALIZE_TARGETS:
            count = normalize_table_column(conn, table, column)
            if count > 0:
                print(f"  {table}.{column}: {count} records updated")
            total += count

        alias_updated, unique_companies = build_company_aliases(conn)
        print(f"  companies.normalized_name: {alias_updated} updated")
        print(f"  Unique normalized companies: {unique_companies}")

        conn.commit()
        print(f"  Total records normalized: {total}")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
