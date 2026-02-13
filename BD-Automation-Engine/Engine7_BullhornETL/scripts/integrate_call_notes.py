#!/usr/bin/env python3
"""
Integrate Call Notes Intelligence into Database

Takes the analyzed call notes data and integrates it into the Bullhorn master database:
1. Adds call activities to activities table
2. Updates prime contractor mentions and relationships
3. Adds program mentions
4. Updates contact scores based on activity
5. Creates new intelligence tables for analytics
"""

import sqlite3
import json
from pathlib import Path
from collections import defaultdict

# Paths
OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"
DB_PATH = Path(__file__).parent.parent / "data" / "bullhorn_master.db"


def load_json(filename: str) -> dict:
    """Load JSON file from outputs directory."""
    filepath = OUTPUTS_DIR / filename
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}


def create_intelligence_tables(conn: sqlite3.Connection):
    """Create new tables for call notes intelligence."""
    cursor = conn.cursor()

    # Call notes activity table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS call_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department VARCHAR(100),
            note_author VARCHAR(200),
            date_added DATE,
            note_type VARCHAR(50),
            action VARCHAR(100),
            about VARCHAR(200),
            status VARCHAR(50),
            note_body TEXT,
            has_traction BOOLEAN DEFAULT FALSE,
            no_answer BOOLEAN DEFAULT FALSE,
            not_interested BOOLEAN DEFAULT FALSE,
            no_openings BOOLEAN DEFAULT FALSE,
            positive_response BOOLEAN DEFAULT FALSE,
            hiring_signal BOOLEAN DEFAULT FALSE,
            programs_mentioned TEXT,
            primes_mentioned TEXT,
            locations_mentioned TEXT,
            clearances_mentioned TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Prime mentions from call notes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prime_call_mentions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prime_name VARCHAR(200),
            mention_count INTEGER DEFAULT 0,
            positive_mentions INTEGER DEFAULT 0,
            negative_mentions INTEGER DEFAULT 0,
            sample_contacts TEXT,
            sample_notes TEXT,
            last_mention_date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Program mentions from call notes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS program_call_mentions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_name VARCHAR(200),
            mention_count INTEGER DEFAULT 0,
            positive_mentions INTEGER DEFAULT 0,
            negative_mentions INTEGER DEFAULT 0,
            is_gap_program BOOLEAN DEFAULT FALSE,
            sample_contacts TEXT,
            sample_notes TEXT,
            last_mention_date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Location intelligence
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS location_intelligence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name VARCHAR(200),
            mention_count INTEGER DEFAULT 0,
            top_primes TEXT,
            top_programs TEXT,
            clearance_distribution TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Contact activity summary
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contact_activity_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_name VARCHAR(200),
            total_interactions INTEGER DEFAULT 0,
            positive_interactions INTEGER DEFAULT 0,
            negative_interactions INTEGER DEFAULT 0,
            no_answer_count INTEGER DEFAULT 0,
            last_interaction_date DATE,
            last_status VARCHAR(50),
            primes_associated TEXT,
            programs_associated TEXT,
            is_gap_contact BOOLEAN DEFAULT FALSE,
            engagement_score INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Gap analysis results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gap_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type VARCHAR(50),  -- 'program', 'contact', 'prime', 'location'
            entity_name VARCHAR(200),
            gap_reason TEXT,
            negative_count INTEGER DEFAULT 0,
            positive_count INTEGER DEFAULT 0,
            recommendation TEXT,
            priority VARCHAR(20),  -- 'high', 'medium', 'low'
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    print("Intelligence tables created successfully")


def insert_call_notes(conn: sqlite3.Connection, records: list):
    """Insert call notes records into database."""
    cursor = conn.cursor()

    # Clear existing call notes
    cursor.execute("DELETE FROM call_notes")

    insert_count = 0
    for record in records:
        try:
            cursor.execute("""
                INSERT INTO call_notes (
                    department, note_author, date_added, note_type, action,
                    about, status, note_body
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.get('Department', ''),
                record.get('Note Author', ''),
                record.get('Date Note Added', ''),
                record.get('Type', ''),
                record.get('Note Action', ''),
                record.get('About', ''),
                record.get('Status', ''),
                str(record.get('Note Body', ''))[:2000]  # Truncate long notes
            ))
            insert_count += 1
        except Exception as e:
            print(f"Error inserting record: {e}")

    conn.commit()
    print(f"Inserted {insert_count} call notes records")


def insert_prime_mentions(conn: sqlite3.Connection, primes_analysis: dict):
    """Insert prime contractor mentions into database."""
    cursor = conn.cursor()

    # Clear existing
    cursor.execute("DELETE FROM prime_call_mentions")

    for prime_name, data in primes_analysis.items():
        sample_notes = json.dumps(data.get('sample_notes', [])[:5])

        cursor.execute("""
            INSERT INTO prime_call_mentions (
                prime_name, mention_count, sample_notes
            ) VALUES (?, ?, ?)
        """, (prime_name, data.get('mention_count', 0), sample_notes))

    conn.commit()
    print(f"Inserted {len(primes_analysis)} prime contractor mentions")


def insert_program_mentions(conn: sqlite3.Connection, programs_analysis: dict, gap_programs: list):
    """Insert program mentions into database."""
    cursor = conn.cursor()

    # Clear existing
    cursor.execute("DELETE FROM program_call_mentions")

    for program_name, data in programs_analysis.items():
        is_gap = program_name in gap_programs
        sample_notes = json.dumps(data.get('sample_notes', [])[:5])

        cursor.execute("""
            INSERT INTO program_call_mentions (
                program_name, mention_count, is_gap_program, sample_notes
            ) VALUES (?, ?, ?, ?)
        """, (program_name, data.get('mention_count', 0), is_gap, sample_notes))

    conn.commit()
    print(f"Inserted {len(programs_analysis)} program mentions")


def insert_contact_activity(conn: sqlite3.Connection, contacts: list, gap_contacts: list):
    """Insert contact activity summary into database."""
    cursor = conn.cursor()

    # Clear existing
    cursor.execute("DELETE FROM contact_activity_summary")

    # Aggregate contacts by name
    contact_summary = defaultdict(lambda: {
        'total': 0,
        'positive': 0,
        'negative': 0,
        'no_answer': 0,
        'last_date': None,
        'last_status': None,
        'primes': set(),
        'programs': set()
    })

    gap_contact_names = {c.get('name', '') for c in gap_contacts}

    for contact in contacts:
        name = contact.get('name', '').strip()
        if not name:
            continue

        summary = contact_summary[name]
        summary['total'] += 1

        traction = contact.get('traction', {})
        if traction.get('positive_response'):
            summary['positive'] += 1
        if traction.get('no_answer'):
            summary['no_answer'] += 1
        if traction.get('not_interested') or traction.get('no_openings'):
            summary['negative'] += 1

        summary['last_date'] = contact.get('date')
        summary['last_status'] = contact.get('status')

        for prime in contact.get('primes_mentioned', []):
            summary['primes'].add(prime)
        for prog in contact.get('programs_mentioned', []):
            summary['programs'].add(prog)

    # Insert aggregated data
    for name, data in contact_summary.items():
        is_gap = name in gap_contact_names

        # Calculate engagement score (0-100)
        total = data['total']
        positive = data['positive']
        data['negative'] + data['no_answer']

        if total > 0:
            engagement = int((positive / total) * 100)
        else:
            engagement = 0

        cursor.execute("""
            INSERT INTO contact_activity_summary (
                contact_name, total_interactions, positive_interactions,
                negative_interactions, no_answer_count, last_interaction_date,
                last_status, primes_associated, programs_associated,
                is_gap_contact, engagement_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, total, data['positive'], data['negative'], data['no_answer'],
            data['last_date'], data['last_status'],
            json.dumps(list(data['primes'])),
            json.dumps(list(data['programs'])),
            is_gap, engagement
        ))

    conn.commit()
    print(f"Inserted {len(contact_summary)} contact activity summaries")


def insert_location_intelligence(conn: sqlite3.Connection, locations: dict):
    """Insert location intelligence into database."""
    cursor = conn.cursor()

    # Clear existing
    cursor.execute("DELETE FROM location_intelligence")

    for location, count in locations.items():
        cursor.execute("""
            INSERT INTO location_intelligence (location_name, mention_count)
            VALUES (?, ?)
        """, (location, count))

    conn.commit()
    print(f"Inserted {len(locations)} location records")


def insert_gap_analysis(conn: sqlite3.Connection, gap_data: dict):
    """Insert gap analysis results into database."""
    cursor = conn.cursor()

    # Clear existing
    cursor.execute("DELETE FROM gap_analysis")

    # Gap programs
    for program in gap_data.get('gap_programs', []):
        cursor.execute("""
            INSERT INTO gap_analysis (
                entity_type, entity_name, gap_reason, priority, recommendation
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            'program', program,
            'High negative traction, low positive response ratio',
            'high',
            'Review targeting strategy, consider different contact approach'
        ))

    # Gap contacts (first 100)
    for contact in gap_data.get('gap_contacts', [])[:100]:
        name = contact.get('name', '')
        cursor.execute("""
            INSERT INTO gap_analysis (
                entity_type, entity_name, gap_reason, priority, recommendation
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            'contact', name,
            f"Multiple no-answer or negative responses. Last status: {contact.get('status', 'Unknown')}",
            'medium',
            'Consider re-engagement strategy or mark as inactive'
        ))

    conn.commit()
    print(f"Inserted gap analysis records")


def update_contact_scores(conn: sqlite3.Connection):
    """Update contact scores based on call activity."""
    cursor = conn.cursor()

    # Get contact activity data
    cursor.execute("""
        SELECT contact_name, total_interactions, positive_interactions,
               negative_interactions, no_answer_count, engagement_score,
               primes_associated, is_gap_contact
        FROM contact_activity_summary
    """)

    activity_data = {row[0]: {
        'total': row[1],
        'positive': row[2],
        'negative': row[3],
        'no_answer': row[4],
        'engagement': row[5],
        'primes': row[6],
        'is_gap': row[7]
    } for row in cursor.fetchall()}

    # Update existing contact scores
    update_count = 0
    for contact_name, data in activity_data.items():
        # Check if contact exists in contact_scores
        cursor.execute("SELECT id, score FROM contact_scores WHERE contact_name = ?", (contact_name,))
        existing = cursor.fetchone()

        if existing:
            # Update score with activity bonus/penalty
            old_score = existing[1]
            activity_modifier = data['engagement'] // 10  # 0-10 points based on engagement

            # Penalize if gap contact
            if data['is_gap']:
                activity_modifier -= 5

            new_score = max(0, min(100, old_score + activity_modifier))

            cursor.execute("""
                UPDATE contact_scores
                SET score = ?,
                    activity_count = ?,
                    scoring_factors = scoring_factors || ' | Call activity: ' || ?
                WHERE id = ?
            """, (new_score, data['total'], data['engagement'], existing[0]))
            update_count += 1

    conn.commit()
    print(f"Updated {update_count} contact scores with call activity data")


def generate_summary_stats(conn: sqlite3.Connection):
    """Generate and print summary statistics."""
    cursor = conn.cursor()

    print("\n" + "="*80)
    print("DATABASE INTEGRATION SUMMARY")
    print("="*80)

    # Count records in each table
    tables = [
        'call_notes',
        'prime_call_mentions',
        'program_call_mentions',
        'contact_activity_summary',
        'location_intelligence',
        'gap_analysis'
    ]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} records")

    # Top primes by mentions
    print("\n--- Top Primes by Call Mentions ---")
    cursor.execute("""
        SELECT prime_name, mention_count
        FROM prime_call_mentions
        ORDER BY mention_count DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # Gap programs
    print("\n--- Gap Programs ---")
    cursor.execute("""
        SELECT program_name, mention_count
        FROM program_call_mentions
        WHERE is_gap_program = 1
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} mentions (LOW TRACTION)")

    # Top engaged contacts
    print("\n--- Top Engaged Contacts (by score) ---")
    cursor.execute("""
        SELECT contact_name, engagement_score, total_interactions
        FROM contact_activity_summary
        WHERE engagement_score > 0
        ORDER BY engagement_score DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}% engagement ({row[2]} interactions)")

    # Gap contacts count
    cursor.execute("SELECT COUNT(*) FROM contact_activity_summary WHERE is_gap_contact = 1")
    gap_count = cursor.fetchone()[0]
    print(f"\n  Gap Contacts (need attention): {gap_count}")


def main():
    print("="*80)
    print("INTEGRATING CALL NOTES INTELLIGENCE INTO DATABASE")
    print("="*80)

    # Load analysis data
    print("\nLoading analysis data...")
    analysis = load_json('call_notes_analysis.json')
    contacts = load_json('extracted_contacts.json')
    gap_data = load_json('gap_analysis.json')
    all_records = load_json('all_call_notes_records.json')

    if not analysis:
        print("No analysis data found. Run analyze_call_notes.py first.")
        return

    # Connect to database
    print(f"\nConnecting to database: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))

    try:
        # Create intelligence tables
        print("\nCreating intelligence tables...")
        create_intelligence_tables(conn)

        # Insert data
        print("\nInserting call notes records...")
        insert_call_notes(conn, all_records)

        print("\nInserting prime mentions...")
        insert_prime_mentions(conn, analysis.get('primes_analysis', {}))

        print("\nInserting program mentions...")
        insert_program_mentions(
            conn,
            analysis.get('programs_analysis', {}),
            gap_data.get('gap_programs', [])
        )

        print("\nInserting contact activity...")
        insert_contact_activity(
            conn,
            contacts if isinstance(contacts, list) else [],
            gap_data.get('gap_contacts', [])
        )

        print("\nInserting location intelligence...")
        insert_location_intelligence(conn, analysis.get('locations', {}))

        print("\nInserting gap analysis...")
        insert_gap_analysis(conn, gap_data)

        print("\nUpdating contact scores...")
        update_contact_scores(conn)

        # Generate summary
        generate_summary_stats(conn)

        print("\n" + "="*80)
        print("INTEGRATION COMPLETE")
        print("="*80)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
