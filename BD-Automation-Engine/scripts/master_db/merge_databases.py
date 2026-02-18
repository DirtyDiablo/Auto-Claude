"""
Merge master databases from BD-Engine, data-scraper, and N8N-Builder
into a single unified database.

Usage:
    python -m scripts.master_db.merge_databases \
        --bd-engine data/master_federal_contracts.db \
        --data-scraper /c/Auto-Claud/data-scraper/data/master_federal_contracts.db \
        --n8n-builder /c/Auto-Claud/N8N-Builder/data/master_federal_contracts.db \
        --output data/unified_federal_contracts.db
"""

import argparse
import shutil
import sqlite3
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TABLES_TO_MERGE = [
    "programs", "companies", "contracts", "task_orders",
    "contacts", "jobs", "placements", "activities",
    "intelligence", "documents",
]

DERIVED_TABLES = ["timelines", "scoring", "program_contacts", "program_companies"]

# Columns where we want to keep the MAX value instead of COALESCE
MAX_COLUMNS = {
    "contacts": {"tier", "engagement_score", "priority_score", "relationship_score"},
    "intelligence": {"priority_score", "composite_score", "bd_score"},
    "scoring": {"composite_score", "job_activity_score", "contact_access_score"},
    "programs": {"match_score", "incumbent_score"},
}


def merge_table(target_conn, source_conn, table: str, source_name: str, verbose: bool):
    """Merge a single table from source into target.

    Strategy:
    - If row doesn't exist in target (by ID): INSERT it
    - If row exists: UPDATE NULL columns with source values (COALESCE)
    - For score columns: keep MAX value
    - Track source_files provenance
    """
    src_cursor = source_conn.cursor()
    tgt_cursor = target_conn.cursor()

    # Get column names
    src_cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in src_cursor.fetchall()]

    if not columns:
        return 0, 0

    # Read all source rows
    src_cursor.execute(f"SELECT * FROM {table}")
    rows = src_cursor.fetchall()

    inserted = 0
    enriched = 0
    max_cols = MAX_COLUMNS.get(table, set())

    for row in rows:
        row_dict = dict(zip(columns, row))
        row_id = row_dict.get("id")
        if not row_id:
            continue

        # Check if exists in target
        tgt_cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,))
        existing = tgt_cursor.fetchone()

        if not existing:
            # INSERT new row
            placeholders = ", ".join(["?" for _ in columns])
            col_names = ", ".join(columns)
            values = list(row)
            # Append source tag to source_files
            if "source_files" in columns:
                sf_idx = columns.index("source_files")
                existing_sf = values[sf_idx] or ""
                values[sf_idx] = f"{existing_sf}|{source_name}" if existing_sf else source_name
            tgt_cursor.execute(
                f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})",
                values,
            )
            if tgt_cursor.rowcount > 0:
                inserted += 1
        else:
            # ENRICH existing row
            existing_dict = dict(zip(columns, existing))
            set_clauses = []
            values = []

            for col in columns:
                if col == "id":
                    continue
                new_val = row_dict.get(col)
                old_val = existing_dict.get(col)

                if new_val is None or (isinstance(new_val, str) and not new_val.strip()):
                    continue

                if col in max_cols:
                    # Keep MAX for score columns
                    try:
                        new_num = float(new_val) if new_val else 0
                        old_num = float(old_val) if old_val else 0
                        if new_num > old_num:
                            set_clauses.append(f"{col} = ?")
                            values.append(new_val)
                    except (ValueError, TypeError):
                        pass
                elif old_val is None or (isinstance(old_val, str) and not old_val.strip()):
                    # Fill NULL/empty columns
                    set_clauses.append(f"{col} = ?")
                    values.append(new_val)

            if set_clauses:
                # Also update source_files provenance
                if "source_files" in columns:
                    old_sf = existing_dict.get("source_files", "") or ""
                    if source_name not in old_sf:
                        set_clauses.append("source_files = ?")
                        values.append(f"{old_sf}|{source_name}" if old_sf else source_name)

                values.append(row_id)
                tgt_cursor.execute(
                    f"UPDATE {table} SET {', '.join(set_clauses)} WHERE id = ?",
                    values,
                )
                if tgt_cursor.rowcount > 0:
                    enriched += 1

    if verbose:
        print(f"  {table}: +{inserted} new, {enriched} enriched from {source_name}")
    return inserted, enriched


def merge_databases(
    bd_engine_path: Path,
    data_scraper_path: Path,
    n8n_builder_path: Path,
    output_path: Path,
    verbose: bool = True,
):
    """Merge 3 project databases into one unified database."""
    start = time.time()

    if verbose:
        print(f"{'='*60}")
        print(f"Master Database Merge")
        print(f"{'='*60}")
        print(f"  Base: {bd_engine_path}")
        print(f"  + N8N-Builder: {n8n_builder_path}")
        print(f"  + data-scraper: {data_scraper_path}")
        print(f"  Output: {output_path}\n")

    if not bd_engine_path.exists():
        print(f"ERROR: BD-Engine database not found: {bd_engine_path}")
        return

    # Start with BD-Engine as base (highest priority)
    shutil.copy2(bd_engine_path, output_path)
    target_conn = sqlite3.connect(str(output_path))
    target_conn.row_factory = sqlite3.Row

    # Merge in priority order: N8N-Builder first (more contacts), then data-scraper
    sources = [
        ("n8n_builder", n8n_builder_path),
        ("data_scraper", data_scraper_path),
    ]

    total_new = 0
    total_enriched = 0

    for source_name, source_path in sources:
        if not source_path.exists():
            if verbose:
                print(f"SKIP {source_name}: {source_path} not found\n")
            continue

        if verbose:
            print(f"Merging {source_name}...")

        source_conn = sqlite3.connect(str(source_path))
        source_conn.row_factory = sqlite3.Row

        for table in TABLES_TO_MERGE:
            try:
                new, enriched = merge_table(
                    target_conn, source_conn, table, source_name, verbose
                )
                total_new += new
                total_enriched += enriched
            except Exception as e:
                if verbose:
                    print(f"  {table}: ERROR - {e}")

        source_conn.close()
        target_conn.commit()

        if verbose:
            print()

    # Re-derive computed tables
    if verbose:
        print("Re-deriving computed tables...")

    from scripts.master_db.loaders.derive_timelines import derive_timelines
    from scripts.master_db.loaders.derive_scoring import derive_scoring
    from scripts.master_db.loaders.link_junctions import link_junctions

    cursor = target_conn.cursor()
    for table in DERIVED_TABLES:
        cursor.execute(f"DELETE FROM {table}")
    target_conn.commit()

    link_junctions(target_conn, verbose=verbose)
    derive_timelines(target_conn, verbose=verbose)
    derive_scoring(target_conn, verbose=verbose)

    target_conn.commit()

    # Final stats
    if verbose:
        print(f"\n{'='*60}")
        print(f"Final table counts:")
        cursor = target_conn.cursor()
        total_records = 0
        for table in TABLES_TO_MERGE + DERIVED_TABLES:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table:<25} {count:>10,}")
                total_records += count
            except sqlite3.OperationalError:
                pass
        print(f"  {'─'*25} {'─'*10}")
        print(f"  {'TOTAL':<25} {total_records:>10,}")

    target_conn.close()

    elapsed = time.time() - start
    if verbose:
        print(f"\n{'='*60}")
        print(f"MERGE COMPLETE in {elapsed:.1f}s")
        print(f"  New records added: {total_new:,}")
        print(f"  Records enriched: {total_enriched:,}")
        print(f"  Output: {output_path}")
        print(f"  Size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Merge master databases from all 3 projects")
    parser.add_argument("--bd-engine", required=True, help="BD-Engine DB path")
    parser.add_argument("--data-scraper", required=True, help="data-scraper DB path")
    parser.add_argument("--n8n-builder", required=True, help="N8N-Builder DB path")
    parser.add_argument("--output", required=True, help="Output unified DB path")
    parser.add_argument("--verbose", "-v", action="store_true", default=True)
    args = parser.parse_args()

    merge_databases(
        Path(args.bd_engine),
        Path(args.data_scraper),
        Path(args.n8n_builder),
        Path(args.output),
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
