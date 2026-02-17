"""
Placements ETL Loader
Source: Bullhorn placements (616) + placement_program_links (1,814)
"""

import sqlite3
from pathlib import Path

from ..utils import (
    generate_id,
    safe_float,
    safe_int,
    safe_str,
    standardize_date,
)

BASE_DIR = Path(__file__).parent.parent.parent.parent


def load_placements(conn: sqlite3.Connection, verbose: bool = False) -> int:
    """Load placements from Bullhorn database."""
    cursor = conn.cursor()
    loaded = 0

    bullhorn_db = BASE_DIR / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"
    if not bullhorn_db.exists():
        if verbose:
            print("  Placements: bullhorn_master.db not found, skipping")
        return 0

    bh_conn = sqlite3.connect(str(bullhorn_db))
    bh_conn.row_factory = sqlite3.Row
    bh_cursor = bh_conn.cursor()

    # Load placements
    bh_cursor.execute("SELECT * FROM placements")
    for row in bh_cursor.fetchall():
        keys = row.keys()
        bh_id = str(row["bullhorn_placement_id"]) if "bullhorn_placement_id" in keys else str(row["id"])
        pid = generate_id(bh_id, "placement")

        cursor.execute("""
            INSERT OR REPLACE INTO placements (
                id, bullhorn_placement_id,
                bullhorn_job_id, bullhorn_candidate_id,
                placement_date, start_date, end_date,
                status, outcome,
                pay_rate, bill_rate, salary, spread,
                flat_fee, estimated_revenue, commission,
                duration_days,
                client_name, job_title, candidate_name,
                owner, source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'bullhorn_master.db')
        """, (
            pid, bh_id,
            safe_str(row["bullhorn_job_id"] if "bullhorn_job_id" in keys else None),
            safe_str(row["bullhorn_candidate_id"] if "bullhorn_candidate_id" in keys else None),
            standardize_date(row["placement_date"] if "placement_date" in keys else None),
            standardize_date(row["start_date"] if "start_date" in keys else None),
            standardize_date(row["end_date"] if "end_date" in keys else None),
            safe_str(row["status"] if "status" in keys else None),
            safe_str(row["outcome"] if "outcome" in keys else None),
            safe_float(row["pay_rate"] if "pay_rate" in keys else None),
            safe_float(row["bill_rate"] if "bill_rate" in keys else None),
            safe_float(row["salary"] if "salary" in keys else None),
            safe_float(row["spread"] if "spread" in keys else None),
            safe_float(row["flat_fee"] if "flat_fee" in keys else None),
            safe_float(row["estimated_revenue"] if "estimated_revenue" in keys else None),
            safe_float(row["commission"] if "commission" in keys else None),
            safe_int(row["duration_days"] if "duration_days" in keys else None),
            safe_str(row["client_name"] if "client_name" in keys else None),
            safe_str(row["job_title"] if "job_title" in keys else None),
            safe_str(row["candidate_name"] if "candidate_name" in keys else None),
            safe_str(row["owner"] if "owner" in keys else None),
        ))
        loaded += 1

    # Load placement_program_links into the helper table
    links_loaded = 0
    try:
        bh_cursor.execute("SELECT * FROM placement_program_links")
        from ..utils import build_program_lookup
        program_lookup = build_program_lookup(conn)

        for row in bh_cursor.fetchall():
            keys = row.keys()
            placement_bh_id = safe_str(row["placement_id"] if "placement_id" in keys else
                                       row["bullhorn_placement_id"] if "bullhorn_placement_id" in keys else None)
            program_name = safe_str(row["program_name"] if "program_name" in keys else None)
            if not placement_bh_id or not program_name:
                continue

            # Look up our placement ID and program ID
            pl_id = generate_id(placement_bh_id, "placement")
            from ..utils import fuzzy_program_match
            prog_id = fuzzy_program_match(program_name, program_lookup)

            if prog_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO placement_program_links
                    (placement_id, program_id, program_name, source)
                    VALUES (?, ?, ?, 'bullhorn')
                """, (pl_id, prog_id, program_name))
                links_loaded += 1
    except sqlite3.OperationalError:
        pass  # Table might not exist

    bh_conn.close()
    conn.commit()
    if verbose:
        print(f"  Placements loaded: {loaded}, program links: {links_loaded}")
    return loaded
