"""
Activities ETL Loader
Source: Bullhorn call_notes (50,710 rows)
"""

import sqlite3
from pathlib import Path

from ..utils import (
    generate_id,
    safe_int,
    safe_str,
    standardize_date,
)

BASE_DIR = Path(__file__).parent.parent.parent.parent


def load_activities(conn: sqlite3.Connection, verbose: bool = False) -> int:
    """Load activities/call notes from Bullhorn."""
    cursor = conn.cursor()
    loaded = 0

    bullhorn_db = BASE_DIR / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"
    if not bullhorn_db.exists():
        if verbose:
            print("  Activities: bullhorn_master.db not found, skipping")
        return 0

    bh_conn = sqlite3.connect(str(bullhorn_db))
    bh_conn.row_factory = sqlite3.Row
    bh_cursor = bh_conn.cursor()

    # Load call_notes in batches for memory efficiency
    bh_cursor.execute("SELECT COUNT(*) FROM call_notes")
    total = bh_cursor.fetchone()[0]
    batch_size = 5000
    offset = 0

    while offset < total:
        bh_cursor.execute(f"SELECT * FROM call_notes LIMIT {batch_size} OFFSET {offset}")
        rows = bh_cursor.fetchall()
        if not rows:
            break

        batch_data = []
        for row in rows:
            keys = row.keys()
            bh_id = safe_str(row["id"] if "id" in keys else None) or str(offset + loaded)
            aid = generate_id(bh_id, "call_note")

            batch_data.append((
                aid, bh_id,
                safe_str(row["type"] if "type" in keys else None),
                safe_str(row["action"] if "action" in keys else None),
                safe_str(row["about"] if "about" in keys else None),
                None,  # about_contact_id - linked later
                standardize_date(row["date"] if "date" in keys else
                                row["activity_date"] if "activity_date" in keys else None),
                safe_str(row["author"] if "author" in keys else
                        row["actor"] if "actor" in keys else None),
                safe_str(row["note_text"] if "note_text" in keys else
                        row["comments"] if "comments" in keys else None),
                safe_str(row["comments"] if "comments" in keys else None),
                safe_int(row["hiring_signal"] if "hiring_signal" in keys else None),
                safe_int(row["positive_response"] if "positive_response" in keys else None),
                safe_int(row["traction"] if "traction" in keys else None),
                safe_str(row["programs_mentioned"] if "programs_mentioned" in keys else None),
                safe_str(row["primes_mentioned"] if "primes_mentioned" in keys else None),
                safe_str(row["locations"] if "locations" in keys else None),
                "bullhorn_master.db",
            ))
            loaded += 1

        cursor.executemany("""
            INSERT OR IGNORE INTO activities (
                id, bullhorn_activity_id,
                activity_type, action, about, about_contact_id,
                activity_date, actor,
                note_text, comments,
                hiring_signal, positive_response, traction,
                programs_mentioned, primes_mentioned, locations,
                source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch_data)

        offset += batch_size
        if verbose and offset % 10000 == 0:
            print(f"    Activities progress: {offset}/{total}")

    bh_conn.close()
    conn.commit()
    if verbose:
        print(f"  Activities loaded: {loaded}")
    return loaded
