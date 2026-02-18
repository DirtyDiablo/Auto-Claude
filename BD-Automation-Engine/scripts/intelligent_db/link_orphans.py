"""
Auto-link orphan contacts to programs via company matching.
Finds contacts not in program_contacts who have a company matching a program_companies entry.
"""
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.master_db.utils import normalize_company_name, generate_id

DB_PATH = PROJECT_ROOT / "data" / "unified_federal_contracts.db"


def run(db_path=None):
    """Run orphan contact linking."""
    db_path = db_path or DB_PATH
    print("Orphan Contact Linking")
    print(f"  Database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Find contacts NOT in program_contacts
    cursor.execute("""
        SELECT c.id, c.full_name, c.company
        FROM contacts c
        WHERE c.company IS NOT NULL AND TRIM(c.company) != ''
        AND c.id NOT IN (SELECT contact_id FROM program_contacts)
    """)
    orphans = cursor.fetchall()
    print(f"  Orphan contacts (not linked to any program): {len(orphans)}")

    # Build company->program mapping from program_companies + companies
    cursor.execute("""
        SELECT pc.program_id, co.name, co.normalized_name
        FROM program_companies pc
        JOIN companies co ON co.id = pc.company_id
    """)
    company_programs = {}
    for prog_id, name, norm_name in cursor.fetchall():
        if name:
            company_programs.setdefault(name.lower().strip(), set()).add(prog_id)
        if norm_name:
            company_programs.setdefault(norm_name.lower().strip(), set()).add(prog_id)

    # Also map from programs.prime_contractor
    cursor.execute("SELECT id, prime_contractor FROM programs WHERE prime_contractor IS NOT NULL")
    for prog_id, prime in cursor.fetchall():
        norm = normalize_company_name(prime)
        if norm:
            company_programs.setdefault(norm.lower().strip(), set()).add(prog_id)

    linked = 0
    for cid, name, company in orphans:
        norm_co = normalize_company_name(company).lower().strip() if company else ""

        # Try normalized name first, then raw
        program_ids = company_programs.get(norm_co, set())
        if not program_ids and company:
            program_ids = company_programs.get(company.lower().strip(), set())

        for prog_id in program_ids:
            link_id = generate_id(prog_id, cid, "orphan_link")
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO program_contacts
                    (id, program_id, contact_id, relationship_type, source)
                    VALUES (?, ?, ?, 'inferred_company', 'orphan_linker')
                """, (link_id, prog_id, cid))
                if cursor.rowcount > 0:
                    linked += 1
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    conn.close()

    print(f"  New program_contacts links created: {linked}")


if __name__ == "__main__":
    run()
