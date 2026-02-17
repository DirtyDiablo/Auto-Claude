"""
Scoring Derivation
Aggregates BD scores from jobs, contacts, intelligence sources.
"""

import csv
import sqlite3
from pathlib import Path

from ..utils import (
    Deduplicator,
    generate_id,
    safe_float,
    safe_str,
)

BASE_DIR = Path(__file__).parent.parent.parent.parent


def derive_scoring(conn: sqlite3.Connection, verbose: bool = False) -> int:
    """Derive scoring for programs and companies."""
    cursor = conn.cursor()
    loaded = 0

    # Program-level scoring
    loaded += _score_programs(cursor, verbose)

    # Import BD target scores from CSVs
    loaded += _import_target_scores(cursor, verbose)

    conn.commit()
    if verbose:
        print(f"  Scoring derived: {loaded}")
    return loaded


def _score_programs(cursor, verbose: bool) -> int:
    """Compute composite program scores from available signals."""
    count = 0
    cursor.execute("SELECT id, program_name FROM programs")
    programs = cursor.fetchall()

    for pid, pname in programs:
        # Job activity score
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE matched_program_id = ?", (pid,))
        job_count = cursor.fetchone()[0]
        job_score = min(job_count * 10, 100)

        # Contact access score
        cursor.execute("SELECT COUNT(*) FROM program_contacts WHERE program_id = ?", (pid,))
        contact_count = cursor.fetchone()[0]
        contact_score = min(contact_count * 5, 100)

        # Contract/revenue score
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(award_amount), 0)
            FROM contracts WHERE program_id = ?
        """, (pid,))
        contract_row = cursor.fetchone()
        contract_count = contract_row[0]
        contract_score = min(contract_count * 15, 100)

        # Intelligence score (bd_score average)
        cursor.execute("""
            SELECT AVG(bd_score) FROM intelligence
            WHERE program_id = ? AND bd_score IS NOT NULL
        """, (pid,))
        avg_bd = cursor.fetchone()[0] or 0

        # Recompete proximity score
        cursor.execute("""
            SELECT MIN(days_until_event) FROM timelines
            WHERE program_id = ? AND event_date > date('now')
            AND event_type IN ('recompete', 'pop_end')
        """, (pid,))
        days_result = cursor.fetchone()
        days_until = days_result[0] if days_result and days_result[0] else 9999
        if days_until < 90:
            recompete_score = 100
        elif days_until < 180:
            recompete_score = 75
        elif days_until < 365:
            recompete_score = 50
        elif days_until < 730:
            recompete_score = 25
        else:
            recompete_score = 0

        # Engagement score from contact activity
        cursor.execute("""
            SELECT AVG(c.relationship_score) FROM contacts c
            JOIN program_contacts pc ON pc.contact_id = c.id
            WHERE pc.program_id = ? AND c.relationship_score IS NOT NULL
        """, (pid,))
        engagement = cursor.fetchone()[0] or 0

        # Composite score (weighted average)
        composite = (
            job_score * 0.15 +
            contact_score * 0.15 +
            contract_score * 0.15 +
            avg_bd * 0.25 +
            recompete_score * 0.20 +
            min(engagement, 100) * 0.10
        )

        # Determine tier
        if composite >= 70:
            tier = "Hot"
        elif composite >= 40:
            tier = "Warm"
        else:
            tier = "Cold"

        sid = generate_id(pid, "program_score")
        cursor.execute("""
            INSERT OR REPLACE INTO scoring (
                id, entity_type, entity_id, entity_name,
                bd_score, priority_tier,
                job_activity_score, contact_access_score,
                contract_score, recompete_proximity_score,
                engagement_score, composite_score,
                scoring_details, source
            ) VALUES (?, 'program', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'derived')
        """, (
            sid, pid, pname,
            avg_bd, tier,
            job_score, contact_score,
            contract_score, recompete_score,
            engagement, composite,
            f"jobs={job_count},contacts={contact_count},contracts={contract_count},"
            f"days_to_recompete={days_until},avg_bd={avg_bd:.1f}",
        ))
        count += 1

    if verbose:
        print(f"    Program scores: {count}")
    return count


def _import_target_scores(cursor, verbose: bool) -> int:
    """Import individual BD target scores from intelligence table."""
    count = 0
    cursor.execute("""
        SELECT id, intel_type, company_name, piid, bd_score, bd_reasons
        FROM intelligence
        WHERE bd_score IS NOT NULL AND bd_score > 0
    """)
    dedup = Deduplicator()
    for row in cursor.fetchall():
        iid, itype, company, piid, score, reasons = row
        key = f"{company}|{piid}"
        if not dedup.is_new(key):
            continue

        tier = "Hot" if score >= 70 else "Warm" if score >= 40 else "Cold"
        sid = generate_id(iid, "intel_score")
        cursor.execute("""
            INSERT OR IGNORE INTO scoring (
                id, entity_type, entity_id, entity_name,
                bd_score, priority_tier,
                composite_score, scoring_details,
                source
            ) VALUES (?, 'target', ?, ?, ?, ?, ?, ?, 'intelligence')
        """, (
            sid, iid, f"{company} - {piid}",
            score, tier, score, reasons,
        ))
        count += 1

    if verbose:
        print(f"    Target scores: {count}")
    return count
