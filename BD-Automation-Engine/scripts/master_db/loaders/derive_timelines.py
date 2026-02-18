"""
Timelines Derivation
Computes timeline events from programs, contracts, and recompete pipeline data.
"""

import csv
import sqlite3
from datetime import datetime
from pathlib import Path

from ..utils import (
    Deduplicator,
    generate_id,
    safe_str,
    standardize_date,
)

BASE_DIR = Path(__file__).parent.parent.parent.parent


def derive_timelines(conn: sqlite3.Connection, verbose: bool = False) -> int:
    """Derive timeline events from programs, contracts, and recompete data."""
    cursor = conn.cursor()
    dedup = Deduplicator()
    loaded = 0

    # From programs table
    loaded += _from_programs(cursor, dedup, verbose)

    # From contracts table
    loaded += _from_contracts(cursor, dedup, verbose)

    # From PHASE4_RECOMPETE_PIPELINE.csv
    recompete = BASE_DIR / "data" / "enriched" / "intelligence" / "PHASE4_RECOMPETE_PIPELINE.csv"
    if recompete.exists():
        loaded += _from_recompete_pipeline(cursor, recompete, dedup, verbose)

    # From PHASE2_RECOMPETE_OPPORTUNITIES.csv
    recompete2 = BASE_DIR / "data" / "enriched" / "intelligence" / "PHASE2_RECOMPETE_OPPORTUNITIES.csv"
    if recompete2.exists():
        loaded += _from_recompete_opportunities(cursor, recompete2, dedup, verbose)

    # Compute days_until_event and urgency for all timelines
    _compute_urgency(cursor)

    conn.commit()
    if verbose:
        print(f"  Timelines derived: {loaded}")
    return loaded


def _compute_urgency(cursor):
    """Compute days_until_event and urgency for all timeline entries."""
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        UPDATE timelines SET
            days_until_event = CAST(julianday(event_date) - julianday(?) AS INTEGER),
            urgency = CASE
                WHEN julianday(event_date) - julianday(?) < 0 THEN 'Passed'
                WHEN julianday(event_date) - julianday(?) < 90 THEN 'Critical'
                WHEN julianday(event_date) - julianday(?) < 180 THEN 'Soon'
                WHEN julianday(event_date) - julianday(?) < 365 THEN 'Planning'
                ELSE 'Future'
            END
        WHERE event_date IS NOT NULL
    """, (today, today, today, today, today))


def _from_programs(cursor, dedup: Deduplicator, verbose: bool) -> int:
    """Extract timeline events from programs table."""
    count = 0
    cursor.execute("""
        SELECT id, program_name,
            pop_start_consolidated, pop_end_consolidated,
            recompete_date, ultimate_completion_consolidated
        FROM programs
    """)
    for row in cursor.fetchall():
        pid, name = row[0], row[1]
        events = [
            ("pop_start", row[2]),
            ("pop_end", row[3]),
            ("recompete", row[4]),
            ("ultimate_completion", row[5]),
        ]
        for event_type, event_date in events:
            if not event_date:
                continue
            key = f"{pid}|{event_type}|{event_date}"
            if not dedup.is_new(key):
                continue
            tid = generate_id(key)
            cursor.execute("""
                INSERT OR IGNORE INTO timelines (
                    id, event_type, event_date,
                    program_id, program_name,
                    description, source
                ) VALUES (?, ?, ?, ?, ?, ?, 'programs')
            """, (
                tid, event_type, event_date,
                pid, name,
                f"{event_type.replace('_', ' ').title()} for {name}",
            ))
            count += 1
    if verbose:
        print(f"    From programs: {count} events")
    return count


def _from_contracts(cursor, dedup: Deduplicator, verbose: bool) -> int:
    """Extract timeline events from contracts table."""
    count = 0
    cursor.execute("""
        SELECT id, piid, program_id, program_name,
            start_date, end_date, pop_end, pop_ultimate
        FROM contracts
    """)
    for row in cursor.fetchall():
        cid, piid = row[0], row[1]
        program_id, program_name = row[2], row[3]
        events = [
            ("contract_start", row[4]),
            ("contract_end", row[5]),
            ("pop_end", row[6]),
            ("ultimate_completion", row[7]),
        ]
        for event_type, event_date in events:
            if not event_date:
                continue
            key = f"{cid}|{event_type}|{event_date}"
            if not dedup.is_new(key):
                continue
            tid = generate_id(key)
            cursor.execute("""
                INSERT OR IGNORE INTO timelines (
                    id, event_type, event_date,
                    program_id, program_name,
                    contract_id, piid,
                    description, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'contracts')
            """, (
                tid, event_type, event_date,
                program_id, program_name,
                cid, piid,
                f"{event_type.replace('_', ' ').title()} for {piid or program_name or 'contract'}",
            ))
            count += 1
    if verbose:
        print(f"    From contracts: {count} events")
    return count


def _from_recompete_pipeline(cursor, csv_path: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load from PHASE4_RECOMPETE_PIPELINE.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            piid = safe_str(row.get("piid"))
            pop_end = standardize_date(row.get("pop_end_date"))
            if not pop_end:
                continue
            key = f"recompete_pipeline|{piid}|{pop_end}"
            if not dedup.is_new(key):
                continue

            tid = generate_id(key)
            cursor.execute("""
                INSERT OR IGNORE INTO timelines (
                    id, event_type, event_date,
                    piid, description, source
                ) VALUES (?, 'recompete', ?, ?, ?, 'recompete_pipeline')
            """, (
                tid, pop_end, piid,
                f"Recompete: {safe_str(row.get('recipient'))} - {safe_str(row.get('description', ''))[:100]}",
            ))
            count += 1
    if verbose:
        print(f"    Recompete pipeline: {count}")
    return count


def _from_recompete_opportunities(cursor, csv_path: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load from PHASE2_RECOMPETE_OPPORTUNITIES.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            end_date = standardize_date(row.get("end_date"))
            if not end_date:
                continue
            program = safe_str(row.get("program_name"))
            piid = safe_str(row.get("piid"))
            key = f"recompete_opp|{program}|{piid}|{end_date}"
            if not dedup.is_new(key):
                continue

            tid = generate_id(key)
            cursor.execute("""
                INSERT OR IGNORE INTO timelines (
                    id, event_type, event_date,
                    program_name, piid,
                    description, source
                ) VALUES (?, 'recompete', ?, ?, ?, ?, 'recompete_opportunities')
            """, (
                tid, end_date, program, piid,
                f"Recompete opportunity: {program or ''} ({safe_str(row.get('urgency', ''))})",
            ))
            count += 1
    if verbose:
        print(f"    Recompete opportunities: {count}")
    return count
