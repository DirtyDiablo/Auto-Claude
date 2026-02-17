"""
Junction Table Builder
Builds M:M relationships: program_contacts and program_companies.
"""

import sqlite3
from pathlib import Path

from ..utils import (
    Deduplicator,
    build_company_lookup,
    build_program_lookup,
    fuzzy_program_match,
    generate_id,
    normalize_company_name,
    safe_str,
)

BASE_DIR = Path(__file__).parent.parent.parent.parent


def link_junctions(conn: sqlite3.Connection, verbose: bool = False) -> int:
    """Build junction tables for program-contact and program-company relationships."""
    cursor = conn.cursor()
    loaded = 0

    loaded += _link_program_contacts(cursor, conn, verbose)
    loaded += _link_program_companies(cursor, conn, verbose)

    conn.commit()
    if verbose:
        print(f"  Junction links created: {loaded}")
    return loaded


def _link_program_contacts(cursor, conn, verbose: bool) -> int:
    """Build program_contacts junction from multiple sources."""
    count = 0
    program_lookup = build_program_lookup(conn)
    dedup = Deduplicator()

    # Source 1: contacts.program field -> program_contacts
    cursor.execute("SELECT id, program FROM contacts WHERE program IS NOT NULL AND program != ''")
    for contact_id, program in cursor.fetchall():
        program_id = fuzzy_program_match(program, program_lookup)
        if not program_id:
            continue
        key = f"{program_id}|{contact_id}"
        if not dedup.is_new(key):
            continue
        lid = generate_id(key, "pc")
        cursor.execute("""
            INSERT OR IGNORE INTO program_contacts (id, program_id, contact_id, relationship_type, source)
            VALUES (?, ?, ?, 'contact_program_field', 'contacts')
        """, (lid, program_id, contact_id))
        count += 1

    # Source 2: contacts.associated_programs field
    cursor.execute("""
        SELECT id, associated_programs FROM contacts
        WHERE associated_programs IS NOT NULL AND associated_programs != ''
    """)
    for contact_id, progs in cursor.fetchall():
        for prog_name in progs.split(","):
            prog_name = prog_name.strip()
            if not prog_name:
                continue
            program_id = fuzzy_program_match(prog_name, program_lookup)
            if not program_id:
                continue
            key = f"{program_id}|{contact_id}"
            if not dedup.is_new(key):
                continue
            lid = generate_id(key, "pc_assoc")
            cursor.execute("""
                INSERT OR IGNORE INTO program_contacts (id, program_id, contact_id, relationship_type, source)
                VALUES (?, ?, ?, 'associated_program', 'contacts')
            """, (lid, program_id, contact_id))
            count += 1

    # Source 3: activities.programs_mentioned + about -> contact link
    cursor.execute("""
        SELECT a.about, a.programs_mentioned FROM activities a
        WHERE a.programs_mentioned IS NOT NULL AND a.programs_mentioned != ''
        AND a.about IS NOT NULL AND a.about != ''
    """)
    for about, progs_mentioned in cursor.fetchall():
        # Find contact by name match
        cursor.execute(
            "SELECT id FROM contacts WHERE full_name = ? OR full_name LIKE ? LIMIT 1",
            (about, f"%{about}%")
        )
        contact_row = cursor.fetchone()
        if not contact_row:
            continue
        contact_id = contact_row[0]

        for prog_name in progs_mentioned.split(","):
            prog_name = prog_name.strip()
            if not prog_name:
                continue
            program_id = fuzzy_program_match(prog_name, program_lookup)
            if not program_id:
                continue
            key = f"{program_id}|{contact_id}"
            if not dedup.is_new(key):
                continue
            lid = generate_id(key, "pc_activity")
            cursor.execute("""
                INSERT OR IGNORE INTO program_contacts (id, program_id, contact_id, relationship_type, source)
                VALUES (?, ?, ?, 'activity_mention', 'activities')
            """, (lid, program_id, contact_id))
            count += 1

    if verbose:
        print(f"    Program-Contact links: {count}")
    return count


def _link_program_companies(cursor, conn, verbose: bool) -> int:
    """Build program_companies junction from multiple sources."""
    count = 0
    program_lookup = build_program_lookup(conn)
    company_lookup = build_company_lookup(conn)
    dedup = Deduplicator()

    # Source 1: programs.prime_contractor -> company (role=prime)
    cursor.execute("""
        SELECT id, prime_contractor, prime_contractor_consolidated FROM programs
        WHERE prime_contractor IS NOT NULL OR prime_contractor_consolidated IS NOT NULL
    """)
    for pid, prime, prime_consol in cursor.fetchall():
        prime_name = prime_consol or prime
        if not prime_name:
            continue
        normalized = normalize_company_name(prime_name)
        company_id = company_lookup.get(normalized.lower())
        if not company_id:
            continue
        key = f"{pid}|{company_id}|prime"
        if not dedup.is_new(key):
            continue
        lid = generate_id(key, "pco")
        cursor.execute("""
            INSERT OR IGNORE INTO program_companies (id, program_id, company_id, role, source)
            VALUES (?, ?, ?, 'prime', 'programs')
        """, (lid, pid, company_id))
        count += 1

    # Source 2: contracts.recipient_name -> company (role=prime or sub)
    cursor.execute("""
        SELECT program_id, recipient_name, company_id FROM contracts
        WHERE program_id IS NOT NULL AND company_id IS NOT NULL
    """)
    for pid, recipient, cid in cursor.fetchall():
        key = f"{pid}|{cid}|contract_prime"
        if not dedup.is_new(key):
            continue
        lid = generate_id(key, "pco_contract")
        cursor.execute("""
            INSERT OR IGNORE INTO program_companies (id, program_id, company_id, role, source)
            VALUES (?, ?, ?, 'prime', 'contracts')
        """, (lid, pid, cid))
        count += 1

    # Source 3: task_orders sub recipients -> company (role=sub)
    cursor.execute("""
        SELECT t.prime_award_id, t.sub_recipient_name FROM task_orders t
        WHERE t.sub_recipient_name IS NOT NULL
    """)
    for prime_award_id, sub_name in cursor.fetchall():
        if not sub_name:
            continue
        normalized = normalize_company_name(sub_name)
        company_id = company_lookup.get(normalized.lower())
        if not company_id:
            continue
        # Find program via contract
        cursor.execute(
            "SELECT program_id FROM contracts WHERE piid = ? AND program_id IS NOT NULL LIMIT 1",
            (prime_award_id,)
        )
        contract_row = cursor.fetchone()
        if not contract_row or not contract_row[0]:
            continue
        pid = contract_row[0]
        key = f"{pid}|{company_id}|sub"
        if not dedup.is_new(key):
            continue
        lid = generate_id(key, "pco_sub")
        cursor.execute("""
            INSERT OR IGNORE INTO program_companies (id, program_id, company_id, role, source)
            VALUES (?, ?, ?, 'sub', 'task_orders')
        """, (lid, pid, company_id))
        count += 1

    # Source 4: intelligence competitor matches -> company (role=competitor)
    cursor.execute("""
        SELECT program_id, company_name FROM intelligence
        WHERE intel_type = 'competitor_match' AND program_id IS NOT NULL AND company_name IS NOT NULL
    """)
    for pid, company_name in cursor.fetchall():
        normalized = normalize_company_name(company_name)
        company_id = company_lookup.get(normalized.lower())
        if not company_id:
            continue
        key = f"{pid}|{company_id}|competitor"
        if not dedup.is_new(key):
            continue
        lid = generate_id(key, "pco_comp")
        cursor.execute("""
            INSERT OR IGNORE INTO program_companies (id, program_id, company_id, role, source)
            VALUES (?, ?, ?, 'competitor', 'intelligence')
        """, (lid, pid, company_id))
        count += 1

    if verbose:
        print(f"    Program-Company links: {count}")
    return count
