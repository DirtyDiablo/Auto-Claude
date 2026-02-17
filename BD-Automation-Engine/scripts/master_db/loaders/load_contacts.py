"""
Contacts ETL Loader
Primary: contacts_classified.json (7,339)
Enrichment: Prime_Contacts_Enriched/*.csv (26 files), Bullhorn contact_scores,
            CONTACT_INTELLIGENCE_DETAILED.csv
"""

import csv
import json
import sqlite3
from pathlib import Path

from ..utils import (
    Deduplicator,
    generate_id,
    json_encode_array,
    normalize_name,
    safe_float,
    safe_int,
    safe_str,
    standardize_date,
)

BASE_DIR = Path(__file__).parent.parent.parent.parent


def load_contacts(conn: sqlite3.Connection, verbose: bool = False) -> int:
    """Load contacts from all sources."""
    cursor = conn.cursor()
    dedup = Deduplicator()
    loaded = 0

    # Source 1: contacts_classified.json (primary - 7,339 contacts)
    classified = BASE_DIR / "outputs" / "bd_dashboard" / "contacts_classified.json"
    if classified.exists():
        loaded += _load_classified(cursor, classified, dedup, verbose)

    # Source 2: Prime_Contacts_Enriched/*.csv (26 files, enrichment)
    contacts_dir = BASE_DIR / "Engine3_OrgChart" / "data" / "Prime_Contacts_Enriched"
    if contacts_dir.exists():
        loaded += _load_prime_contacts(cursor, contacts_dir, dedup, verbose)

    # Source 3: Bullhorn contact_scores (enrichment)
    bullhorn_db = BASE_DIR / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"
    if bullhorn_db.exists():
        _enrich_contact_scores(cursor, bullhorn_db, verbose)

    # Source 4: CONTACT_INTELLIGENCE_DETAILED.csv (enrichment)
    intel_csv = BASE_DIR / "data" / "from_data_scraper" / "CONTACT_INTELLIGENCE_DETAILED.csv"
    if intel_csv.exists():
        _enrich_contact_intel(cursor, intel_csv, verbose)

    conn.commit()
    if verbose:
        print(f"  Contacts loaded: {loaded} ({dedup.stats})")
    return loaded


def _load_classified(cursor, json_path: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load from contacts_classified.json."""
    count = 0
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    contacts = data.get("contacts", data) if isinstance(data, dict) else data

    for c in contacts:
        email = safe_str(c.get("email"))
        name = safe_str(c.get("name"))
        first = safe_str(c.get("first_name"))
        last = safe_str(c.get("last_name"))
        full_name = name or f"{first or ''} {last or ''}".strip()
        if not full_name:
            continue

        # Dedup: email first, then name+company
        dedup_key = email if email else f"{normalize_name(full_name)}|{safe_str(c.get('company', ''))}"
        if not dedup.is_new(dedup_key):
            continue

        cid = safe_str(c.get("id")) or generate_id(dedup_key)
        cursor.execute("""
            INSERT OR REPLACE INTO contacts (
                id, full_name, first_name, last_name,
                title, company, email, phone, linkedin,
                program, tier, bd_priority,
                relationship_status,
                last_contact_date, next_outreach_date,
                notes, source_db,
                matched_program_id, matched_jobs,
                source_files
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cid, full_name, first, last,
            safe_str(c.get("title")),
            safe_str(c.get("company")),
            email,
            safe_str(c.get("phone")),
            safe_str(c.get("linkedin")),
            safe_str(c.get("program")),
            safe_int(c.get("tier")),
            safe_str(c.get("bd_priority")),
            safe_str(c.get("relationship_status")),
            standardize_date(c.get("last_contact_date")),
            standardize_date(c.get("next_outreach_date")),
            safe_str(c.get("notes")),
            safe_str(c.get("source_db")),
            safe_str(c.get("matched_program_id")),
            json_encode_array(c.get("matched_jobs")),
            "contacts_classified.json",
        ))
        count += 1

    if verbose:
        print(f"    contacts_classified.json: {count} contacts")
    return count


def _load_prime_contacts(cursor, contacts_dir: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load from Prime_Contacts_Enriched CSV files."""
    count = 0
    for csv_file in sorted(contacts_dir.glob("*.csv")):
        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = safe_str(row.get("Name"))
                if not name:
                    continue
                email = safe_str(row.get("Email"))
                dedup_key = email if email else f"{normalize_name(name)}|{safe_str(row.get('Primes', ''))}"
                if not dedup.is_new(dedup_key):
                    # Enrich existing contact
                    if email:
                        cursor.execute("""
                            UPDATE contacts SET
                                tier = COALESCE(tier, ?),
                                contact_type = COALESCE(contact_type, ?),
                                is_hiring_manager = COALESCE(is_hiring_manager, ?),
                                is_decision_maker = COALESCE(is_decision_maker, ?),
                                clearances = COALESCE(clearances, ?),
                                hiring_signals = COALESCE(hiring_signals, ?),
                                pain_points = COALESCE(pain_points, ?),
                                note_count = COALESCE(note_count, ?),
                                last_activity = COALESCE(last_activity, ?)
                            WHERE email = ?
                        """, (
                            safe_int(row.get("Tier")),
                            safe_str(row.get("Contact Type")),
                            1 if safe_str(row.get("Is Hiring Manager")) in ("True", "true", "1") else 0,
                            1 if safe_str(row.get("Is Decision Maker")) in ("True", "true", "1") else 0,
                            safe_str(row.get("Clearances")),
                            safe_str(row.get("Hiring Signals")),
                            safe_str(row.get("Pain Points")),
                            safe_int(row.get("Note Count")),
                            standardize_date(row.get("Last Activity")),
                            email,
                        ))
                    continue

                cid = generate_id(dedup_key)
                # Parse boolean fields
                is_hiring = 1 if safe_str(row.get("Is Hiring Manager")) in ("True", "true", "1") else 0
                is_decision = 1 if safe_str(row.get("Is Decision Maker")) in ("True", "true", "1") else 0
                has_reqs = 1 if safe_str(row.get("Has Open Reqs")) in ("True", "true", "1") else 0

                cursor.execute("""
                    INSERT OR IGNORE INTO contacts (
                        id, full_name, title, email, phone, linkedin,
                        tier, contact_type,
                        associated_primes, associated_programs,
                        locations, clearances,
                        is_hiring_manager, has_open_reqs, is_decision_maker,
                        relationship_score, note_count,
                        last_activity, first_activity,
                        hiring_signals, pain_points, recent_note,
                        source_files
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cid, name,
                    safe_str(row.get("Primary Title")),
                    email,
                    safe_str(row.get("Phone")),
                    safe_str(row.get("LinkedIn")),
                    safe_int(row.get("Tier")),
                    safe_str(row.get("Contact Type")),
                    safe_str(row.get("Primes")),
                    safe_str(row.get("Programs")),
                    safe_str(row.get("Locations")),
                    safe_str(row.get("Clearances")),
                    is_hiring, has_reqs, is_decision,
                    safe_float(row.get("Relationship Score")),
                    safe_int(row.get("Note Count")),
                    standardize_date(row.get("Last Activity")),
                    standardize_date(row.get("First Activity")),
                    safe_str(row.get("Hiring Signals")),
                    safe_str(row.get("Pain Points")),
                    safe_str(row.get("Recent Note")),
                    str(csv_file.name),
                ))
                count += 1
    if verbose:
        print(f"    Prime Contacts Enriched: {count} new contacts")
    return count


def _enrich_contact_scores(cursor, db_path: Path, verbose: bool):
    """Enrich contacts with Bullhorn contact_scores."""
    updated = 0
    bh_conn = sqlite3.connect(str(db_path))
    bh_conn.row_factory = sqlite3.Row
    bh_cursor = bh_conn.cursor()

    bh_cursor.execute("""
        SELECT * FROM contact_scores
        WHERE contact_name IS NOT NULL
    """)
    for row in bh_cursor.fetchall():
        name = row["contact_name"] if "contact_name" in row.keys() else None
        if not name:
            continue
        score = row["total_score"] if "total_score" in row.keys() else None
        cursor.execute("""
            UPDATE contacts SET
                relationship_score = ?
            WHERE full_name = ? OR full_name LIKE ?
        """, (
            safe_float(score),
            name,
            f"%{name}%",
        ))
        if cursor.rowcount > 0:
            updated += 1

    bh_conn.close()
    if verbose:
        print(f"    Contact scores enrichment: {updated} updated")


def _enrich_contact_intel(cursor, csv_path: Path, verbose: bool):
    """Enrich from CONTACT_INTELLIGENCE_DETAILED.csv."""
    updated = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = safe_str(row.get("contact_name"))
            if not name:
                continue
            cursor.execute("""
                UPDATE contacts SET
                    inferred_role_level = COALESCE(inferred_role_level, ?),
                    associated_primes = COALESCE(associated_primes, ?),
                    associated_programs = COALESCE(associated_programs, ?),
                    aggregated_summary = COALESCE(aggregated_summary, ?),
                    note_count = COALESCE(note_count, ?)
                WHERE full_name = ? OR full_name LIKE ?
            """, (
                safe_str(row.get("inferred_role_level")),
                safe_str(row.get("associated_primes")),
                safe_str(row.get("associated_programs")),
                safe_str(row.get("aggregated_summary")),
                safe_int(row.get("note_count")),
                name, f"%{name}%",
            ))
            if cursor.rowcount > 0:
                updated += 1
    if verbose:
        print(f"    Contact Intel enrichment: {updated} updated")
