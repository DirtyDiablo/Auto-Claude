"""
Migration 001: Drop 100% NULL FPDS columns from programs table.
SQLite doesn't support DROP COLUMN, so we rebuild the table.
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "unified_federal_contracts.db"

# Columns expected to be 100% NULL - verify at runtime
CANDIDATE_COLUMNS = [
    "base_contract_value_fpds",
    "base_options_value_fpds",
    "contract_signed_date_fpds",
    "contract_effective_date_fpds",
    "current_completion_date_fpds",
    "ultimate_completion_date_fpds",
    "performance_location_fpds",
    "fpds_naics_code",
    "fpds_psc_code",
]


def find_null_columns(conn):
    """Verify which candidate columns are actually 100% NULL."""
    cursor = conn.cursor()
    null_cols = []
    for col in CANDIDATE_COLUMNS:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM programs WHERE [{col}] IS NOT NULL")
            non_null = cursor.fetchone()[0]
            if non_null == 0:
                null_cols.append(col)
                print(f"  {col}: 100% NULL -> will drop")
            else:
                print(f"  {col}: {non_null} non-null values -> keeping")
        except sqlite3.OperationalError:
            print(f"  {col}: column doesn't exist -> skipping")
    return null_cols


def rebuild_without_columns(conn, drop_cols):
    """Rebuild programs table without the specified columns."""
    cursor = conn.cursor()

    # Get current columns
    cursor.execute("PRAGMA table_info(programs)")
    all_cols = [row[1] for row in cursor.fetchall()]
    keep_cols = [c for c in all_cols if c not in drop_cols]

    if not drop_cols:
        print("  No columns to drop.")
        return

    cols_str = ", ".join(f"[{c}]" for c in keep_cols)

    print(f"  Dropping {len(drop_cols)} columns, keeping {len(keep_cols)}...")

    # Collect and drop views that reference programs table
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view'")
    views = [(name, sql) for name, sql in cursor.fetchall() if sql and "programs" in sql.lower()]

    for view_name, _ in views:
        cursor.execute(f"DROP VIEW IF EXISTS [{view_name}]")

    try:
        cursor.execute(f"CREATE TABLE programs_new AS SELECT {cols_str} FROM programs")
        cursor.execute("DROP TABLE programs")
        cursor.execute("ALTER TABLE programs_new RENAME TO programs")

        # Recreate indexes
        for col in ["program_name", "acronym", "agency_owner", "prime_contractor"]:
            if col in keep_cols:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_programs_{col} ON programs({col})")

        # Recreate views
        for view_name, view_sql in views:
            try:
                cursor.execute(view_sql)
            except sqlite3.OperationalError as ve:
                print(f"  Warning: could not recreate view {view_name}: {ve}")

        conn.commit()
        print(f"  Rebuilt programs table: {len(all_cols)} -> {len(keep_cols)} columns")
    except Exception as e:
        conn.rollback()
        raise e


def run(db_path=None):
    """Run migration 001."""
    db_path = db_path or DB_PATH
    print(f"Migration 001: Drop NULL FPDS columns")
    print(f"  Database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        null_cols = find_null_columns(conn)
        if null_cols:
            rebuild_without_columns(conn, null_cols)
        else:
            print("  No 100% NULL columns found among candidates.")
    finally:
        conn.close()

    print("  Migration 001 complete.")


if __name__ == "__main__":
    run()
