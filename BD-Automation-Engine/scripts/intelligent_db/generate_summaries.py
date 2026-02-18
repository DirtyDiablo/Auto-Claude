"""
Generate per-program intelligence summaries.
Combines data from multiple tables into structured summary records.
"""
import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data" / "unified_federal_contracts.db"


def generate_program_summary(cursor, program_id):
    """Build a structured intelligence summary for a program."""
    # Program basics
    cursor.execute("SELECT * FROM programs WHERE id = ?", (program_id,))
    prog = cursor.fetchone()
    if not prog:
        return None
    prog = dict(prog)

    # Key contacts
    cursor.execute("""
        SELECT c.full_name, c.title, c.company, c.tier, c.bd_priority, c.email
        FROM contacts c
        JOIN program_contacts pc ON pc.contact_id = c.id
        WHERE pc.program_id = ?
        ORDER BY c.tier ASC, c.bd_priority DESC
        LIMIT 10
    """, (program_id,))
    contacts = [dict(r) for r in cursor.fetchall()]

    # Contracts
    cursor.execute("""
        SELECT piid, recipient_name, award_amount, start_date, end_date, description
        FROM contracts WHERE program_id = ?
        ORDER BY award_amount DESC NULLS LAST
        LIMIT 5
    """, (program_id,))
    contracts = [dict(r) for r in cursor.fetchall()]

    # Scoring
    cursor.execute("""
        SELECT composite_score, priority_tier, bd_score,
               recompete_proximity_score, contact_access_score,
               scoring_details
        FROM scoring WHERE entity_id = ? AND entity_type = 'program'
    """, (program_id,))
    score_row = cursor.fetchone()
    scoring = dict(score_row) if score_row else {}

    # Timeline events
    cursor.execute("""
        SELECT event_type, event_date, days_until_event, urgency
        FROM timelines WHERE program_id = ? AND event_date > date('now')
        ORDER BY event_date LIMIT 3
    """, (program_id,))
    upcoming_events = [dict(r) for r in cursor.fetchall()]

    # Intelligence
    cursor.execute("""
        SELECT intel_type, bd_score, bd_reasons, lifecycle_phase, narrative
        FROM intelligence WHERE program_id = ?
        ORDER BY bd_score DESC NULLS LAST LIMIT 3
    """, (program_id,))
    intel = [dict(r) for r in cursor.fetchall()]

    # Recent activity
    cursor.execute("""
        SELECT a.activity_date, a.about, a.note_text, a.sentiment_score
        FROM activities a
        WHERE a.programs_mentioned LIKE ?
        ORDER BY a.activity_date DESC LIMIT 5
    """, (f"%{prog.get('program_name', '')}%",))
    activities = [dict(r) for r in cursor.fetchall()]

    summary = {
        "program_id": program_id,
        "program_name": prog.get("program_name"),
        "acronym": prog.get("acronym"),
        "agency": prog.get("agency_owner"),
        "prime_contractor": prog.get("prime_contractor"),
        "total_value": prog.get("total_contract_value"),
        "priority": prog.get("priority_level"),
        "domain_tags": prog.get("domain_tags"),
        "clearance": prog.get("clearance_requirements"),
        "scoring": scoring,
        "key_contacts": contacts,
        "top_contracts": contracts,
        "upcoming_events": upcoming_events,
        "intelligence": intel,
        "recent_activity": activities,
        "contact_count": len(contacts),
    }

    return summary


def run(db_path=None):
    """Generate summaries for all programs with scoring data."""
    db_path = db_path or DB_PATH
    print("Program Intelligence Summaries")
    print(f"  Database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get programs that have scoring data (most interesting ones)
    cursor.execute("""
        SELECT DISTINCT p.id FROM programs p
        JOIN scoring s ON s.entity_id = p.id AND s.entity_type = 'program'
        ORDER BY s.composite_score DESC
    """)
    program_ids = [row[0] for row in cursor.fetchall()]

    if not program_ids:
        # Fall back to all programs
        cursor.execute("SELECT id FROM programs")
        program_ids = [row[0] for row in cursor.fetchall()]

    summaries = []
    for pid in program_ids:
        summary = generate_program_summary(cursor, pid)
        if summary:
            summaries.append(summary)

    # Store summaries in documents table
    for summary in summaries:
        doc_id = f"summary_{summary['program_id']}"
        cursor.execute("""
            INSERT OR REPLACE INTO documents (id, doc_type, title, content, program_name, program_id, source)
            VALUES (?, 'program_summary', ?, ?, ?, ?, 'auto_generated')
        """, (
            doc_id,
            f"Intelligence Summary: {summary['program_name']}",
            json.dumps(summary, default=str),
            summary["program_name"],
            summary["program_id"],
        ))

    conn.commit()
    conn.close()

    print(f"  Generated: {len(summaries)} program summaries")

    # Show top 5
    for s in summaries[:5]:
        score = s["scoring"].get("composite_score", "N/A")
        print(f"    {s['program_name']}: score={score}, contacts={s['contact_count']}")


if __name__ == "__main__":
    run()
