"""Re-migrate activities and placements that were lost to CASCADE."""
import hashlib
import io
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2
from psycopg2.extras import execute_values

BASE_DIR = Path(__file__).parent.parent
BULLHORN_DB = BASE_DIR / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"
UNIFIED_DB = BASE_DIR / "data" / "unified_federal_contracts.db"
SUPABASE_DSN = os.environ.get("DATABASE_URL_DIRECT") or os.environ.get("DATABASE_URL")
if not SUPABASE_DSN:
    raise RuntimeError("Set DATABASE_URL_DIRECT or DATABASE_URL in .env for migration")
BATCH_SIZE = 500


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def content_hash(data: str) -> str:
    return hashlib.md5(data.encode("utf-8", errors="replace")).hexdigest()[:16]


def safe_str(val):
    if val is None:
        return None
    return str(val).strip() if str(val).strip() else None


def safe_bool(val):
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val > 0
    return str(val).lower() in ("true", "1", "yes")


def safe_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def main():
    start = time.time()
    pg = psycopg2.connect(SUPABASE_DSN)
    pg.autocommit = False
    cur = pg.cursor()

    # === Activities from Bullhorn ===
    print("=" * 60)
    print("RE-MIGRATING: Bullhorn activities")
    print("=" * 60)

    sl = sqlite3.connect(str(BULLHORN_DB))
    sl.row_factory = dict_factory
    sl_cur = sl.cursor()

    sl_cur.execute("SELECT COUNT(*) as cnt FROM activities")
    total = sl_cur.fetchone()["cnt"]
    print(f"  Source: {total:,} activities")

    offset = 0
    migrated = 0
    while offset < total:
        sl_cur.execute(f"SELECT * FROM activities ORDER BY id LIMIT {BATCH_SIZE} OFFSET {offset}")
        rows = sl_cur.fetchall()
        if not rows:
            break

        batch = []
        for row in rows:
            ch = content_hash(f"act_{row.get('bullhorn_activity_id', '')}_{safe_str(row.get('activity_date', ''))}")
            act_type = safe_str(row.get("activity_type")) or "other"
            valid = {"call", "email", "meeting", "note", "submission", "interview", "placement", "other"}
            if act_type.lower() not in valid:
                act_type = "other"

            batch.append((
                "bd_engine", ch, act_type.lower(),
                safe_str(row.get("subject")) or safe_str(row.get("action")) or "",
                safe_str(row.get("note_text")) or safe_str(row.get("comments")),
                safe_str(row.get("action")),
                safe_str(row.get("activity_date")),
                None, None, None, None,
                safe_str(row.get("actor")),
                None, None, None, None, False,
                safe_str(row.get("bullhorn_activity_id")),
                False, False, False, None, "neutral",
            ))

        columns = [
            "source_project", "content_hash", "activity_type", "subject",
            "content", "action", "activity_date", "contact_id", "job_id",
            "program_id", "company_id", "owner", "notes", "outcome",
            "next_action", "next_action_date", "follow_up_required",
            "bullhorn_activity_id", "hiring_signal", "positive_response",
            "traction", "sentiment_score", "priority",
        ]

        cols_str = ", ".join(columns)
        template = "(" + ", ".join(["%s"] * len(columns)) + ")"
        try:
            execute_values(cur, f"INSERT INTO activities ({cols_str}) VALUES %s", batch, template=template)
            pg.commit()
            migrated += len(batch)
        except Exception as e:
            pg.rollback()
            print(f"  ERROR: {str(e)[:150]}")

        offset += BATCH_SIZE
        if offset % 50000 == 0 or offset >= total:
            print(f"  Progress: {min(offset, total):,}/{total:,}, {migrated:,} inserted")

    print(f"  Activities from Bullhorn: {migrated:,}")
    sl.close()

    # === Call notes ===
    print("\n  Re-migrating call notes...")
    sl = sqlite3.connect(str(BULLHORN_DB))
    sl.row_factory = dict_factory
    sl_cur = sl.cursor()

    sl_cur.execute("SELECT COUNT(*) as cnt FROM call_notes")
    total = sl_cur.fetchone()["cnt"]

    offset = 0
    cn_migrated = 0
    while offset < total:
        sl_cur.execute(f"SELECT * FROM call_notes ORDER BY rowid LIMIT {BATCH_SIZE} OFFSET {offset}")
        rows = sl_cur.fetchall()
        if not rows:
            break

        batch = []
        for row in rows:
            ch = content_hash(f"cn_{safe_str(row.get('note_author', ''))}_{safe_str(row.get('date_added', ''))}_{safe_str(row.get('about', ''))}")
            batch.append((
                "bd_engine", ch, "note",
                safe_str(row.get("about")) or "",
                safe_str(row.get("note_body")),
                safe_str(row.get("note_action")) or safe_str(row.get("action")),
                safe_str(row.get("date_added")),
                None, None, None, None,
                safe_str(row.get("note_author")),
                None, None, None, None, False, None,
                safe_bool(row.get("hiring_signal")),
                safe_bool(row.get("positive_response")),
                safe_bool(row.get("has_traction")),
                None, "neutral",
            ))

        columns = [
            "source_project", "content_hash", "activity_type", "subject",
            "content", "action", "activity_date", "contact_id", "job_id",
            "program_id", "company_id", "owner", "notes", "outcome",
            "next_action", "next_action_date", "follow_up_required",
            "bullhorn_activity_id", "hiring_signal", "positive_response",
            "traction", "sentiment_score", "priority",
        ]

        cols_str = ", ".join(columns)
        template = "(" + ", ".join(["%s"] * len(columns)) + ")"
        try:
            execute_values(cur, f"INSERT INTO activities ({cols_str}) VALUES %s", batch, template=template)
            pg.commit()
            cn_migrated += len(batch)
        except Exception as e:
            pg.rollback()
            print(f"  ERROR: {str(e)[:150]}")

        offset += BATCH_SIZE

    print(f"  Call notes: {cn_migrated:,}")
    sl.close()

    # === Placements ===
    print("\n  Re-migrating placements...")
    sl = sqlite3.connect(str(UNIFIED_DB))
    sl.row_factory = dict_factory
    sl_cur = sl.cursor()

    sl_cur.execute("SELECT COUNT(*) as cnt FROM placements")
    total = sl_cur.fetchone()["cnt"]

    sl_cur.execute("SELECT * FROM placements")
    rows = sl_cur.fetchall()

    batch = []
    for row in rows:
        ch = content_hash(f"pl_{safe_str(row.get('bullhorn_placement_id', ''))}_{safe_str(row.get('candidate_name', ''))}")
        batch.append((
            "bd_engine", ch,
            safe_str(row.get("bullhorn_placement_id")),
            None, None, None, None, "active",
            safe_str(row.get("job_title")) or "",
            safe_str(row.get("candidate_name")) or "",
            safe_str(row.get("client_name")) or "",
            None,
            safe_str(row.get("start_date")),
            safe_str(row.get("end_date")),
            None,
            safe_float(row.get("pay_rate")),
            safe_float(row.get("bill_rate")),
            safe_float(row.get("estimated_revenue")),
            None, None,
        ))

    columns = [
        "source_project", "content_hash", "bullhorn_placement_id",
        "job_id", "contact_id", "company_id", "program_id",
        "status", "job_title", "candidate_name", "client_name",
        "owner", "start_date", "end_date", "placement_date",
        "pay_rate", "bill_rate", "salary", "duration_days", "commission",
    ]

    cols_str = ", ".join(columns)
    template = "(" + ", ".join(["%s"] * len(columns)) + ")"
    try:
        execute_values(cur, f"INSERT INTO placements ({cols_str}) VALUES %s", batch, template=template)
        pg.commit()
        print(f"  Placements: {len(batch):,}")
    except Exception as e:
        pg.rollback()
        print(f"  ERROR: {str(e)[:150]}")

    sl.close()

    # Final
    print("\n" + "=" * 60)
    print("COMPLETE FINAL COUNTS")
    print("=" * 60)
    for table in ["contacts", "activities", "programs", "companies", "jobs", "placements",
                   "contracts", "documents", "past_performance", "bd_scoring", "task_orders",
                   "timelines", "program_contacts", "program_companies"]:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"  {table}: {cur.fetchone()[0]:,}")

    elapsed = time.time() - start
    print(f"\nCompleted in {elapsed:.1f}s ({elapsed/60:.1f} min)")
    pg.close()


if __name__ == "__main__":
    main()
