#!/usr/bin/env python3
"""
Export Call Notes Intelligence for Dashboard

Exports the analyzed call notes data to JSON files for the React dashboard.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Paths
DB_PATH = Path(__file__).parent.parent / "data" / "bullhorn_master.db"
DASHBOARD_DATA_DIR = Path(__file__).parent.parent.parent / "dashboard" / "public" / "data"


def export_prime_mentions(conn: sqlite3.Connection) -> list:
    """Export prime contractor mentions for dashboard."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT prime_name, mention_count, sample_notes
        FROM prime_call_mentions
        ORDER BY mention_count DESC
    """)

    primes = []
    for row in cursor.fetchall():
        samples = json.loads(row[2]) if row[2] else []
        primes.append({
            'name': row[0],
            'mentionCount': row[1],
            'sampleNotes': samples[:3],  # Limit for dashboard
            'activityLevel': 'High' if row[1] > 500 else 'Medium' if row[1] > 100 else 'Low'
        })

    return primes


def export_program_mentions(conn: sqlite3.Connection) -> list:
    """Export program mentions for dashboard."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT program_name, mention_count, is_gap_program, sample_notes
        FROM program_call_mentions
        ORDER BY mention_count DESC
    """)

    programs = []
    for row in cursor.fetchall():
        samples = json.loads(row[3]) if row[3] else []
        programs.append({
            'name': row[0],
            'mentionCount': row[1],
            'isGapProgram': bool(row[2]),
            'sampleNotes': samples[:3],
            'status': 'Needs Attention' if row[2] else 'Active'
        })

    return programs


def export_contact_activity(conn: sqlite3.Connection) -> list:
    """Export contact activity summary for dashboard."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT contact_name, total_interactions, positive_interactions,
               negative_interactions, no_answer_count, engagement_score,
               primes_associated, programs_associated, is_gap_contact,
               last_interaction_date, last_status
        FROM contact_activity_summary
        ORDER BY total_interactions DESC
        LIMIT 500
    """)

    contacts = []
    for row in cursor.fetchall():
        primes = json.loads(row[6]) if row[6] else []
        programs = json.loads(row[7]) if row[7] else []

        # Determine tier based on engagement
        engagement = row[5]
        if engagement >= 80:
            tier = 'A'
        elif engagement >= 60:
            tier = 'B'
        elif engagement >= 40:
            tier = 'C'
        elif engagement >= 20:
            tier = 'D'
        else:
            tier = 'E'

        contacts.append({
            'name': row[0],
            'totalInteractions': row[1],
            'positiveInteractions': row[2],
            'negativeInteractions': row[3],
            'noAnswerCount': row[4],
            'engagementScore': engagement,
            'tier': tier,
            'primesAssociated': primes,
            'programsAssociated': programs,
            'isGapContact': bool(row[8]),
            'lastInteractionDate': row[9],
            'lastStatus': row[10]
        })

    return contacts


def export_location_intelligence(conn: sqlite3.Connection) -> list:
    """Export location intelligence for dashboard."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT location_name, mention_count
        FROM location_intelligence
        ORDER BY mention_count DESC
    """)

    locations = []
    for row in cursor.fetchall():
        locations.append({
            'name': row[0],
            'mentionCount': row[1],
            'category': categorize_location(row[0])
        })

    return locations


def categorize_location(location: str) -> str:
    """Categorize location by type."""
    location_lower = location.lower()

    if any(x in location_lower for x in ['afb', 'base', 'fort', 'camp']):
        return 'Military Installation'
    elif any(x in location_lower for x in ['japan', 'korea', 'germany', 'qatar', 'kuwait', 'hawaii']):
        return 'OCONUS'
    elif any(x in location_lower for x in ['meade', 'langley', 'pentagon', 'belvoir']):
        return 'Intel Community'
    elif any(x in location_lower for x in ['arlington', 'mclean', 'reston', 'herndon', 'chantilly']):
        return 'DC Metro'
    elif any(x in location_lower for x in ['tampa', 'macdill']):
        return 'SOCOM/CENTCOM'
    elif any(x in location_lower for x in ['colorado', 'peterson', 'schriever']):
        return 'Space Command'
    else:
        return 'Other'


def export_gap_analysis(conn: sqlite3.Connection) -> dict:
    """Export gap analysis for dashboard."""
    cursor = conn.cursor()

    # Gap programs
    cursor.execute("""
        SELECT entity_name, gap_reason, recommendation
        FROM gap_analysis
        WHERE entity_type = 'program'
    """)
    gap_programs = [{'name': r[0], 'reason': r[1], 'recommendation': r[2]} for r in cursor.fetchall()]

    # Gap contacts count by status
    cursor.execute("""
        SELECT last_status, COUNT(*)
        FROM contact_activity_summary
        WHERE is_gap_contact = 1
        GROUP BY last_status
    """)
    gap_contacts_by_status = {r[0] or 'Unknown': r[1] for r in cursor.fetchall()}

    return {
        'gapPrograms': gap_programs,
        'gapContactsByStatus': gap_contacts_by_status,
        'totalGapContacts': sum(gap_contacts_by_status.values())
    }


def export_call_activity_stats(conn: sqlite3.Connection) -> dict:
    """Export call activity statistics for dashboard."""
    cursor = conn.cursor()

    # Action type distribution
    cursor.execute("""
        SELECT action, COUNT(*) as cnt
        FROM call_notes
        GROUP BY action
        ORDER BY cnt DESC
    """)
    action_distribution = {r[0] or 'Unknown': r[1] for r in cursor.fetchall()}

    # Status distribution
    cursor.execute("""
        SELECT status, COUNT(*) as cnt
        FROM call_notes
        GROUP BY status
        ORDER BY cnt DESC
    """)
    status_distribution = {r[0] or 'Unknown': r[1] for r in cursor.fetchall()}

    # Daily activity (last 30 days represented)
    cursor.execute("""
        SELECT date_added, COUNT(*) as cnt
        FROM call_notes
        WHERE date_added IS NOT NULL AND date_added != ''
        GROUP BY date_added
        ORDER BY date_added DESC
        LIMIT 30
    """)
    daily_activity = [{'date': r[0], 'count': r[1]} for r in cursor.fetchall()]

    # Total counts
    cursor.execute("SELECT COUNT(*) FROM call_notes")
    total_notes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT about) FROM call_notes WHERE about IS NOT NULL AND about != ''")
    unique_contacts = cursor.fetchone()[0]

    return {
        'totalNotes': total_notes,
        'uniqueContacts': unique_contacts,
        'actionDistribution': action_distribution,
        'statusDistribution': status_distribution,
        'dailyActivity': daily_activity
    }


def main():
    print("="*80)
    print("EXPORTING CALL NOTES INTELLIGENCE FOR DASHBOARD")
    print("="*80)

    # Ensure dashboard data directory exists
    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Connect to database
    print(f"\nConnecting to database: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))

    try:
        # Export prime mentions
        print("\nExporting prime mentions...")
        primes = export_prime_mentions(conn)
        with open(DASHBOARD_DATA_DIR / "call_notes_primes.json", 'w') as f:
            json.dump(primes, f, indent=2)
        print(f"  Exported {len(primes)} prime records")

        # Export program mentions
        print("\nExporting program mentions...")
        programs = export_program_mentions(conn)
        with open(DASHBOARD_DATA_DIR / "call_notes_programs.json", 'w') as f:
            json.dump(programs, f, indent=2)
        print(f"  Exported {len(programs)} program records")

        # Export contact activity
        print("\nExporting contact activity...")
        contacts = export_contact_activity(conn)
        with open(DASHBOARD_DATA_DIR / "call_notes_contacts.json", 'w') as f:
            json.dump(contacts, f, indent=2)
        print(f"  Exported {len(contacts)} contact records")

        # Export location intelligence
        print("\nExporting location intelligence...")
        locations = export_location_intelligence(conn)
        with open(DASHBOARD_DATA_DIR / "call_notes_locations.json", 'w') as f:
            json.dump(locations, f, indent=2)
        print(f"  Exported {len(locations)} location records")

        # Export gap analysis
        print("\nExporting gap analysis...")
        gaps = export_gap_analysis(conn)
        with open(DASHBOARD_DATA_DIR / "call_notes_gaps.json", 'w') as f:
            json.dump(gaps, f, indent=2)
        print(f"  Exported gap analysis data")

        # Export activity stats
        print("\nExporting activity statistics...")
        stats = export_call_activity_stats(conn)
        with open(DASHBOARD_DATA_DIR / "call_notes_stats.json", 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"  Exported activity statistics")

        # Create combined intelligence summary
        print("\nCreating intelligence summary...")
        summary = {
            'exportDate': datetime.now().isoformat(),
            'totalCallNotes': stats['totalNotes'],
            'uniqueContacts': stats['uniqueContacts'],
            'totalPrimes': len(primes),
            'totalPrograms': len(programs),
            'gapPrograms': len(gaps['gapPrograms']),
            'gapContacts': gaps['totalGapContacts'],
            'topPrimes': [p['name'] for p in primes[:5]],
            'topLocations': [l['name'] for l in locations[:5]],
            'actionBreakdown': stats['actionDistribution']
        }
        with open(DASHBOARD_DATA_DIR / "call_notes_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)

        print("\n" + "="*80)
        print("DASHBOARD EXPORT COMPLETE")
        print("="*80)
        print(f"\nFiles exported to: {DASHBOARD_DATA_DIR}")
        print("\nExported files:")
        for f in DASHBOARD_DATA_DIR.glob("call_notes_*.json"):
            size = f.stat().st_size
            print(f"  - {f.name} ({size:,} bytes)")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
