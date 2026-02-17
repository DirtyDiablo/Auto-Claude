"""
Master Federal Contracts Database - ETL Build Orchestrator

Usage:
    python -m scripts.master_db.build --full
    python -m scripts.master_db.build --tables programs,contracts
    python -m scripts.master_db.build --validate
    python -m scripts.master_db.build --stats
"""

import argparse
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.master_db.schema import DATABASE_PATH, create_database, get_connection, get_table_counts
from scripts.master_db.validate import validate

# Loader imports
from scripts.master_db.loaders.load_programs import load_programs
from scripts.master_db.loaders.load_companies import load_companies
from scripts.master_db.loaders.load_contracts import load_contracts
from scripts.master_db.loaders.load_task_orders import load_task_orders
from scripts.master_db.loaders.load_contacts import load_contacts
from scripts.master_db.loaders.load_jobs import load_jobs
from scripts.master_db.loaders.load_placements import load_placements
from scripts.master_db.loaders.load_activities import load_activities
from scripts.master_db.loaders.load_intelligence import load_intelligence
from scripts.master_db.loaders.load_documents import load_documents
from scripts.master_db.loaders.derive_timelines import derive_timelines
from scripts.master_db.loaders.derive_scoring import derive_scoring
from scripts.master_db.loaders.link_junctions import link_junctions


# Ordered list of loaders (respects foreign key dependencies)
LOADER_ORDER = [
    ("programs", load_programs),
    ("companies", load_companies),
    ("contracts", load_contracts),
    ("task_orders", load_task_orders),
    ("contacts", load_contacts),
    ("jobs", load_jobs),
    ("placements", load_placements),
    ("activities", load_activities),
    ("intelligence", load_intelligence),
    ("documents", load_documents),
    # Derived tables (depend on core tables)
    ("junctions", link_junctions),
    ("timelines", derive_timelines),
    ("scoring", derive_scoring),
]


def build_full(verbose: bool = False, db_path: Path = None) -> dict:
    """Run a full ETL build."""
    db_path = db_path or DATABASE_PATH
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"{'='*60}")
    print(f"Master Federal Contracts DB - Full Build")
    print(f"Run ID: {run_id}")
    print(f"Output: {db_path}")
    print(f"{'='*60}\n")

    start = time.time()

    # Create fresh schema
    create_database(db_path)
    conn = get_connection(db_path)

    results = {}
    total_records = 0
    errors = 0

    for name, loader_fn in LOADER_ORDER:
        step_start = time.time()
        print(f"Loading {name}...")
        try:
            count = loader_fn(conn, verbose=verbose)
            elapsed = time.time() - step_start
            results[name] = {"count": count, "time": elapsed, "status": "ok"}
            total_records += count
            print(f"  -> {count:,} records ({elapsed:.1f}s)\n")
        except Exception as e:
            elapsed = time.time() - step_start
            results[name] = {"count": 0, "time": elapsed, "status": "error", "error": str(e)}
            errors += 1
            print(f"  -> ERROR: {e}\n")

    # Log ETL run
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO etl_runs (run_id, run_type, started_at, completed_at,
                             tables_loaded, total_records, errors, status)
        VALUES (?, 'full', ?, ?, ?, ?, ?, ?)
    """, (
        run_id, datetime.now().isoformat(),
        datetime.now().isoformat(),
        ",".join(results.keys()),
        total_records, errors,
        "completed" if errors == 0 else "completed_with_errors",
    ))
    conn.commit()
    conn.close()

    total_time = time.time() - start

    print(f"\n{'='*60}")
    print(f"Build Complete: {total_records:,} total records in {total_time:.1f}s")
    if errors:
        print(f"  {errors} loader(s) had errors")
    print(f"Database size: {db_path.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"{'='*60}")

    return results


def build_tables(tables: list[str], verbose: bool = False, db_path: Path = None) -> dict:
    """Run ETL for specific tables only."""
    db_path = db_path or DATABASE_PATH
    if not db_path.exists():
        print("Database not found. Run --full first.")
        return {}

    conn = get_connection(db_path)
    results = {}

    loader_map = dict(LOADER_ORDER)
    for name in tables:
        if name not in loader_map:
            print(f"Unknown table: {name}")
            continue
        print(f"Loading {name}...")
        try:
            count = loader_map[name](conn, verbose=verbose)
            results[name] = {"count": count, "status": "ok"}
            print(f"  -> {count:,} records\n")
        except Exception as e:
            results[name] = {"count": 0, "status": "error", "error": str(e)}
            print(f"  -> ERROR: {e}\n")

    conn.commit()
    conn.close()
    return results


def show_stats(db_path: Path = None):
    """Show database statistics."""
    db_path = db_path or DATABASE_PATH
    if not db_path.exists():
        print("Database not found. Run --full first.")
        return

    print(f"\n{'='*50}")
    print(f"Master Federal Contracts Database Stats")
    print(f"{'='*50}")
    print(f"Path: {db_path}")
    print(f"Size: {db_path.stat().st_size / 1024 / 1024:.1f} MB\n")

    counts = get_table_counts(db_path)
    print(f"{'Table':<25} {'Records':>10}")
    print(f"{'-'*25} {'-'*10}")
    total = 0
    for table, count in counts.items():
        if count >= 0:
            print(f"{table:<25} {count:>10,}")
            total += count
    print(f"{'-'*25} {'-'*10}")
    print(f"{'TOTAL':<25} {total:>10,}")

    # Show view samples
    conn = get_connection(db_path)
    cursor = conn.cursor()

    views = ["program_360_view", "bd_pipeline_view", "recompete_calendar",
             "competitive_landscape", "revenue_by_program", "contact_network_view"]
    print(f"\nViews available:")
    for view in views:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {view}")
            vcount = cursor.fetchone()[0]
            print(f"  {view}: {vcount:,} rows")
        except sqlite3.OperationalError:
            print(f"  {view}: (not available)")

    # Last ETL run
    try:
        cursor.execute("SELECT * FROM etl_runs ORDER BY id DESC LIMIT 1")
        run = cursor.fetchone()
        if run:
            print(f"\nLast ETL run: {run['run_id']} ({run['status']})")
            print(f"  Records: {run['total_records']:,}, Errors: {run['errors']}")
    except (sqlite3.OperationalError, TypeError):
        pass

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Master Federal Contracts DB Builder")
    parser.add_argument("--full", action="store_true", help="Full build (recreate everything)")
    parser.add_argument("--tables", type=str, help="Comma-separated tables to rebuild")
    parser.add_argument("--validate", action="store_true", help="Run validation checks")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--db", type=str, help="Custom database path")
    args = parser.parse_args()

    db_path = Path(args.db) if args.db else DATABASE_PATH

    if args.full:
        build_full(verbose=args.verbose, db_path=db_path)
    elif args.tables:
        table_list = [t.strip() for t in args.tables.split(",")]
        build_tables(table_list, verbose=args.verbose, db_path=db_path)
    elif args.validate:
        validate(db_path=db_path, verbose=True)
    elif args.stats:
        show_stats(db_path=db_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
