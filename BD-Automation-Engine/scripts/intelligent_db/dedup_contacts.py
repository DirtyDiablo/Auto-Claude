"""
Fuzzy contact deduplication.
Blocks by normalized company, then fuzzy-matches full_name (threshold 85).
"""
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.master_db.utils import normalize_company_name

DB_PATH = PROJECT_ROOT / "data" / "unified_federal_contracts.db"

try:
    from rapidfuzz import fuzz
    def fuzzy_ratio(a, b):
        return fuzz.ratio(a.lower(), b.lower())
except ImportError:
    from difflib import SequenceMatcher
    def fuzzy_ratio(a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100

THRESHOLD = 85
# Columns to count for "completeness" when choosing winner
QUALITY_COLUMNS = [
    "full_name", "first_name", "last_name", "title", "company",
    "email", "phone", "linkedin", "program", "tier", "contact_type",
    "bd_priority", "relationship_status", "clearances", "notes",
    "recent_note", "last_activity",
]


def count_non_null(cursor, record_id):
    """Count non-null quality columns for a contact."""
    cursor.execute(f"SELECT {', '.join(QUALITY_COLUMNS)} FROM contacts WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    if not row:
        return 0
    return sum(1 for v in row if v is not None and str(v).strip())


def merge_contacts(cursor, keep_id, remove_id):
    """Merge remove_id into keep_id: fill NULLs, update FKs, delete duplicate."""
    # Fill NULL fields in keeper from duplicate
    cursor.execute("PRAGMA table_info(contacts)")
    columns = [row[1] for row in cursor.fetchall() if row[1] != "id"]

    for col in columns:
        cursor.execute(f"""
            UPDATE contacts SET [{col}] = (
                SELECT [{col}] FROM contacts WHERE id = ?
            ) WHERE id = ? AND [{col}] IS NULL
        """, (remove_id, keep_id))

    # Delete program_contacts for remove_id where keep_id already has that program
    cursor.execute("""
        DELETE FROM program_contacts
        WHERE contact_id = ? AND program_id IN (
            SELECT program_id FROM program_contacts WHERE contact_id = ?
        )
    """, (remove_id, keep_id))

    # Now safe to update remaining FK references
    cursor.execute(
        "UPDATE OR IGNORE program_contacts SET contact_id = ? WHERE contact_id = ?",
        (keep_id, remove_id)
    )
    # Delete any that still couldn't be updated
    cursor.execute("DELETE FROM program_contacts WHERE contact_id = ?", (remove_id,))

    cursor.execute(
        "UPDATE activities SET about_contact_id = ? WHERE about_contact_id = ?",
        (keep_id, remove_id)
    )

    # Delete the duplicate
    cursor.execute("DELETE FROM contacts WHERE id = ?", (remove_id,))


def run(db_path=None):
    """Run contact deduplication."""
    db_path = db_path or DB_PATH
    print("Contact Deduplication")
    print(f"  Database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Group contacts by normalized company
    cursor.execute("SELECT id, full_name, company FROM contacts WHERE full_name IS NOT NULL")
    contacts = cursor.fetchall()

    by_company = defaultdict(list)
    for cid, name, company in contacts:
        norm_co = normalize_company_name(company) if company else "__no_company__"
        by_company[norm_co].append((cid, name))

    merged = 0
    pairs_found = 0

    for company, group in by_company.items():
        if len(group) < 2:
            continue

        # Find duplicate pairs
        seen = set()
        for i in range(len(group)):
            if group[i][0] in seen:
                continue
            for j in range(i + 1, len(group)):
                if group[j][0] in seen:
                    continue

                score = fuzzy_ratio(group[i][1], group[j][1])
                if score >= THRESHOLD:
                    pairs_found += 1
                    # Keep the one with more data
                    score_i = count_non_null(cursor, group[i][0])
                    score_j = count_non_null(cursor, group[j][0])

                    if score_i >= score_j:
                        keep, remove = group[i][0], group[j][0]
                    else:
                        keep, remove = group[j][0], group[i][0]

                    merge_contacts(cursor, keep, remove)
                    seen.add(remove)
                    merged += 1

    conn.commit()
    conn.close()

    print(f"  Duplicate pairs found: {pairs_found}")
    print(f"  Contacts merged: {merged}")
    print(f"  Contacts remaining: {len(contacts) - merged}")


if __name__ == "__main__":
    run()
