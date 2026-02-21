#!/usr/bin/env python3
"""
SQLite-to-PostgreSQL migration script for BD Automation Engine.

Reads from the existing SQLite databases (bullhorn_master.db,
master_federal_contracts.db) and writes to PostgreSQL via the
SQLAlchemy ORM layer.

Usage::

    # Dry run (no writes)
    python scripts/migrate_sqlite_to_pg.py --dry-run

    # Full migration
    python scripts/migrate_sqlite_to_pg.py

    # Migrate specific tables only
    python scripts/migrate_sqlite_to_pg.py --tables jobs candidates placements

Requires ``DATABASE_URL`` to be set in the environment (or ``.env``).
"""

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import structlog
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from Engine8_Knowledge.db.models import (
    Activity,
    Candidate,
    Company,
    Contact,
    Contract,
    Document,
    EtlRun,
    FederalContract,
    Intelligence,
    Job,
    JobPrimeMapping,
    JobProgramMapping,
    PastPerformance,
    Placement,
    PrimeContractor,
    Program,
    ProgramCompany,
    ProgramContact,
    QaReviewQueue,
    Scoring,
    SourceTracking,
    SyncState,
    Timeline,
)
from Engine8_Knowledge.db.session import create_all_tables, get_db, get_engine

logger = structlog.get_logger("migrate_sqlite_to_pg")

BATCH_SIZE = 1000

# ---------------------------------------------------------------------------
# SQLite source paths
# ---------------------------------------------------------------------------

BULLHORN_DB = PROJECT_ROOT / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"
MASTER_DB = PROJECT_ROOT / "data" / "master_federal_contracts.db"


# ---------------------------------------------------------------------------
# Helper: read all rows from a SQLite table
# ---------------------------------------------------------------------------


def _read_sqlite_table(db_path: Path, table_name: str) -> list[dict]:
    """Return all rows from *table_name* in the SQLite database at *db_path*."""
    if not db_path.exists():
        logger.warning("sqlite.missing", path=str(db_path))
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(f"SELECT * FROM {table_name}")
        rows = [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError as exc:
        logger.warning("sqlite.read_error", table=table_name, error=str(exc))
        rows = []
    finally:
        conn.close()

    return rows


# ---------------------------------------------------------------------------
# Table migration definitions
# ---------------------------------------------------------------------------

# Each entry: (label, sqlite_path, sqlite_table, ORM_class, column_mapping | None)
# When column_mapping is None the SQLite column names match the ORM attribute names.

MIGRATION_PLAN: list[tuple] = [
    # Bullhorn core entities
    ("jobs", BULLHORN_DB, "jobs", Job, None),
    ("candidates", BULLHORN_DB, "candidates", Candidate, None),
    ("prime_contractors", BULLHORN_DB, "prime_contractors", PrimeContractor, None),
    ("programs", BULLHORN_DB, "programs", Program, None),
    ("placements", BULLHORN_DB, "placements", Placement, None),
    ("activities", BULLHORN_DB, "activities", Activity, None),
    ("past_performance", BULLHORN_DB, "past_performance", PastPerformance, None),
    ("job_program_mapping", BULLHORN_DB, "job_program_mapping", JobProgramMapping, None),
    ("job_prime_mapping", BULLHORN_DB, "job_prime_mapping", JobPrimeMapping, None),
    # Master federal contracts
    ("contacts", MASTER_DB, "contacts", Contact, None),
    ("companies", MASTER_DB, "companies", Company, None),
    ("contracts", MASTER_DB, "contracts", Contract, None),
    ("intelligence", MASTER_DB, "intelligence", Intelligence, None),
    ("documents", MASTER_DB, "documents", Document, None),
    ("timelines", MASTER_DB, "timelines", Timeline, None),
    ("scoring", MASTER_DB, "scoring", Scoring, None),
    ("program_contacts", MASTER_DB, "program_contacts", ProgramContact, None),
    ("program_companies", MASTER_DB, "program_companies", ProgramCompany, None),
    ("etl_runs", MASTER_DB, "etl_runs", EtlRun, None),
    ("source_tracking", MASTER_DB, "source_tracking", SourceTracking, None),
]


def _row_to_model(model_class, row: dict, column_mapping: dict | None) -> object:
    """Convert a SQLite row dict to an ORM model instance.

    Skips keys that are not valid ORM attributes (e.g. columns added later
    to SQLite but not modelled in the ORM).
    """
    if column_mapping:
        mapped = {column_mapping.get(k, k): v for k, v in row.items()}
    else:
        mapped = dict(row)

    valid_attrs = {c.key for c in model_class.__table__.columns}
    filtered = {k: v for k, v in mapped.items() if k in valid_attrs}
    return model_class(**filtered)


# ---------------------------------------------------------------------------
# Migration runner
# ---------------------------------------------------------------------------


def migrate_table(
    label: str,
    sqlite_path: Path,
    sqlite_table: str,
    model_class,
    column_mapping: dict | None,
    *,
    dry_run: bool = False,
) -> dict:
    """Migrate a single table and return stats."""
    stats = {
        "table": label,
        "source_rows": 0,
        "inserted": 0,
        "skipped": 0,
        "errors": 0,
    }

    rows = _read_sqlite_table(sqlite_path, sqlite_table)
    stats["source_rows"] = len(rows)

    if not rows:
        logger.info("migrate.skip_empty", table=label)
        return stats

    if dry_run:
        logger.info("migrate.dry_run", table=label, rows=len(rows))
        return stats

    with get_db() as session:
        batch = []
        for i, row in enumerate(rows):
            try:
                entity = _row_to_model(model_class, row, column_mapping)
                batch.append(entity)
            except Exception as exc:
                stats["errors"] += 1
                if stats["errors"] <= 5:
                    logger.warning(
                        "migrate.row_error",
                        table=label,
                        row_index=i,
                        error=str(exc),
                    )

            if len(batch) >= BATCH_SIZE:
                session.add_all(batch)
                session.flush()
                stats["inserted"] += len(batch)
                batch = []

        if batch:
            session.add_all(batch)
            session.flush()
            stats["inserted"] += len(batch)

    logger.info(
        "migrate.complete",
        table=label,
        source_rows=stats["source_rows"],
        inserted=stats["inserted"],
        errors=stats["errors"],
    )
    return stats


def verify_counts(results: list[dict]) -> bool:
    """Compare inserted counts with source counts. Return True if all match."""
    all_ok = True
    for r in results:
        if r["inserted"] != r["source_rows"]:
            logger.error(
                "verify.mismatch",
                table=r["table"],
                source=r["source_rows"],
                inserted=r["inserted"],
                errors=r["errors"],
            )
            all_ok = False
        else:
            logger.info(
                "verify.ok",
                table=r["table"],
                count=r["inserted"],
            )
    return all_ok


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate SQLite databases to PostgreSQL"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read from SQLite and report counts without writing to PostgreSQL",
    )
    parser.add_argument(
        "--tables",
        nargs="*",
        help="Only migrate specific tables (by label name)",
    )
    args = parser.parse_args()

    url = os.getenv("DATABASE_URL", "")
    if not url and not args.dry_run:
        logger.error("DATABASE_URL is not set. Set it in .env or environment.")
        sys.exit(1)

    logger.info("migrate.start", dry_run=args.dry_run)
    start_time = time.time()

    if not args.dry_run:
        create_all_tables()

    plan = MIGRATION_PLAN
    if args.tables:
        plan = [entry for entry in plan if entry[0] in args.tables]

    results = []
    for label, sqlite_path, sqlite_table, model_class, col_map in plan:
        stats = migrate_table(
            label,
            sqlite_path,
            sqlite_table,
            model_class,
            col_map,
            dry_run=args.dry_run,
        )
        results.append(stats)

    elapsed = time.time() - start_time

    # Summary
    total_source = sum(r["source_rows"] for r in results)
    total_inserted = sum(r["inserted"] for r in results)
    total_errors = sum(r["errors"] for r in results)

    logger.info(
        "migrate.summary",
        tables=len(results),
        total_source_rows=total_source,
        total_inserted=total_inserted,
        total_errors=total_errors,
        elapsed_seconds=round(elapsed, 1),
        dry_run=args.dry_run,
    )

    if not args.dry_run:
        ok = verify_counts(results)
        if not ok:
            logger.error("migrate.verification_failed")
            sys.exit(1)
        logger.info("migrate.verification_passed")


if __name__ == "__main__":
    main()
