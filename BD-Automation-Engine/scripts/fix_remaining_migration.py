"""Fix remaining migration items: jobs, program_contacts, program_companies."""
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


def safe_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_array(val):
    if val is None:
        return None
    if isinstance(val, list):
        return val
    val = str(val).strip()
    if not val:
        return None
    try:
        parsed = json.loads(val)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    items = [x.strip() for x in val.split(",") if x.strip()]
    return items if items else None


def main():
    start = time.time()
    pg = psycopg2.connect(SUPABASE_DSN)
    pg.autocommit = False
    cur = pg.cursor()

    sl = sqlite3.connect(str(UNIFIED_DB))
    sl.row_factory = dict_factory
    sl_cur = sl.cursor()

    # === 1. Fix Jobs ===
    print("=" * 60)
    print("FIXING: Jobs (enum mapped -> enriched)")
    print("=" * 60)

    cur.execute("TRUNCATE TABLE jobs CASCADE")
    pg.commit()

    sl_cur.execute("SELECT COUNT(*) as cnt FROM jobs")
    total = sl_cur.fetchone()["cnt"]
    print(f"  Source: {total} jobs")

    sl_cur.execute("PRAGMA table_info(jobs)")
    cols = [r["name"] for r in sl_cur.fetchall()]

    offset = 0
    migrated = 0
    while offset < total:
        sl_cur.execute(f"SELECT * FROM jobs ORDER BY rowid LIMIT {BATCH_SIZE} OFFSET {offset}")
        rows = sl_cur.fetchall()
        if not rows:
            break

        batch = []
        for row in rows:
            title = safe_str(row.get("title")) or ""
            company = safe_str(row.get("company")) or safe_str(row.get("prime")) or ""
            ch = content_hash(f"job_{title}_{company}_{safe_str(row.get('location', ''))}")

            clearance = "none"
            cl_raw = safe_str(row.get("clearance")) or ""
            if cl_raw:
                cl = cl_raw.lower()
                if "ts/sci" in cl:
                    clearance = "ts_sci"
                elif "top secret" in cl:
                    clearance = "top_secret"
                elif "secret" in cl:
                    clearance = "secret"

            batch.append((
                "bd_engine", ch, title, company,
                safe_str(row.get("location")) or "",
                safe_str(row.get("description")),
                clearance,
                None, None,  # salary_min, salary_max
                safe_float(row.get("pay_rate")),
                safe_float(row.get("bill_rate")),
                safe_array(row.get("skills")) if "skills" in cols else None,
                safe_float(row.get("bd_score")) or 0,
                "enriched",  # FIXED: was "mapped"
                "bullhorn",
                None,  # source_url
                safe_str(row.get("bullhorn_job_id")) if "bullhorn_job_id" in cols else None,
                None,  # program_id
                safe_str(row.get("matched_program")) if "matched_program" in cols else None,
                None,  # naics_codes
                safe_float(row.get("confidence_score")) if "confidence_score" in cols else None,
                safe_str(row.get("category")) if "category" in cols else None,
                safe_str(row.get("employment_type")) if "employment_type" in cols else None,
            ))

        columns = [
            "source_project", "content_hash", "title", "company", "location",
            "description", "clearance", "salary_min", "salary_max", "pay_rate",
            "bill_rate", "skills", "bd_score", "status", "source", "source_url",
            "bullhorn_job_id", "program_id", "program_name", "naics_codes",
            "confidence_score", "category", "employment_type",
        ]

        cols_str = ", ".join(columns)
        template = "(" + ", ".join(["%s"] * len(columns)) + ")"
        try:
            execute_values(cur, f"INSERT INTO jobs ({cols_str}) VALUES %s", batch, template=template)
            pg.commit()
            migrated += len(batch)
        except Exception as e:
            pg.rollback()
            print(f"  ERROR: {str(e)[:200]}")

        offset += BATCH_SIZE

    cur.execute("SELECT COUNT(*) FROM jobs")
    print(f"  DONE: {migrated} jobs inserted. Total: {cur.fetchone()[0]}")

    # === 2. Fix program_contacts ===
    print("\n" + "=" * 60)
    print("FIXING: program_contacts (name-based resolution)")
    print("=" * 60)

    # Build name->UUID maps from Supabase
    cur.execute("SELECT id, name FROM programs")
    prog_map = {}
    for row in cur.fetchall():
        if row[1]:
            prog_map[row[1].strip().lower()] = row[0]
    print(f"  Program map: {len(prog_map)} entries")

    cur.execute("SELECT id, first_name, last_name FROM contacts")
    contact_map = {}
    for row in cur.fetchall():
        name = f"{row[1] or ''} {row[2] or ''}".strip().lower()
        if name:
            contact_map[name] = row[0]
    print(f"  Contact map: {len(contact_map)} entries")

    # Get unified DB program_contacts with actual names
    sl_cur.execute("SELECT COUNT(*) as cnt FROM program_contacts")
    total = sl_cur.fetchone()["cnt"]
    print(f"  Source: {total} program-contact links")

    # Get name lookups from unified DB
    sl_cur.execute("SELECT id, program_name FROM programs")
    sl_prog_names = {}
    for row in sl_cur.fetchall():
        sl_prog_names[str(row["id"])] = row["program_name"]

    sl_cur.execute("SELECT id, full_name FROM contacts")
    sl_contact_names = {}
    for row in sl_cur.fetchall():
        sl_contact_names[str(row["id"])] = row["full_name"]

    print(f"  SQLite lookups: {len(sl_prog_names)} programs, {len(sl_contact_names)} contacts")

    sl_cur.execute("SELECT * FROM program_contacts")
    pc_rows = sl_cur.fetchall()

    batch = []
    resolved = 0
    skipped = 0
    for row in pc_rows:
        pid = str(row.get("program_id", ""))
        cid = str(row.get("contact_id", ""))
        rel = safe_str(row.get("relationship_type")) or "works_on"

        pname = sl_prog_names.get(pid)
        cname = sl_contact_names.get(cid)

        if not pname or not cname:
            skipped += 1
            continue

        pg_prog_id = prog_map.get(pname.strip().lower())
        pg_contact_id = contact_map.get(cname.strip().lower())

        if pg_prog_id and pg_contact_id:
            batch.append((pg_prog_id, pg_contact_id, rel, "unified_db"))
            resolved += 1
        else:
            skipped += 1

    if batch:
        cols_str = "program_id, contact_id, relationship_type, source"
        template = "(%s, %s, %s, %s)"
        for i in range(0, len(batch), BATCH_SIZE):
            sub = batch[i:i+BATCH_SIZE]
            try:
                execute_values(cur, f"INSERT INTO program_contacts ({cols_str}) VALUES %s", sub, template=template)
                pg.commit()
            except Exception as e:
                pg.rollback()
                print(f"  ERROR: {str(e)[:200]}")

    cur.execute("SELECT COUNT(*) FROM program_contacts")
    print(f"  DONE: {resolved} resolved, {skipped} skipped. Total: {cur.fetchone()[0]}")

    # === 3. Fix program_companies ===
    print("\n" + "=" * 60)
    print("FIXING: program_companies (name-based resolution)")
    print("=" * 60)

    cur.execute("SELECT id, name FROM companies")
    company_map = {}
    for row in cur.fetchall():
        if row[1]:
            company_map[row[1].strip().lower()] = row[0]
    print(f"  Company map: {len(company_map)} entries")

    sl_cur.execute("SELECT id, name FROM companies")
    sl_company_names = {}
    for row in sl_cur.fetchall():
        sl_company_names[str(row["id"])] = row["name"]

    sl_cur.execute("SELECT COUNT(*) as cnt FROM program_companies")
    total = sl_cur.fetchone()["cnt"]
    print(f"  Source: {total} program-company links")

    sl_cur.execute("SELECT * FROM program_companies")
    pc_rows = sl_cur.fetchall()

    batch = []
    resolved = 0
    skipped = 0
    for row in pc_rows:
        pid = str(row.get("program_id", ""))
        coid = str(row.get("company_id", ""))
        role = safe_str(row.get("role")) or "prime"
        source = safe_str(row.get("source")) or "unified_db"

        pname = sl_prog_names.get(pid)
        coname = sl_company_names.get(coid)

        if not pname or not coname:
            skipped += 1
            continue

        pg_prog_id = prog_map.get(pname.strip().lower())
        pg_co_id = company_map.get(coname.strip().lower())

        if pg_prog_id and pg_co_id:
            batch.append((pg_prog_id, pg_co_id, role, source))
            resolved += 1
        else:
            skipped += 1

    if batch:
        cols_str = "program_id, company_id, role, source"
        template = "(%s, %s, %s, %s)"
        for i in range(0, len(batch), BATCH_SIZE):
            sub = batch[i:i+BATCH_SIZE]
            try:
                execute_values(cur, f"INSERT INTO program_companies ({cols_str}) VALUES %s", sub, template=template)
                pg.commit()
            except Exception as e:
                pg.rollback()
                print(f"  ERROR: {str(e)[:200]}")

    cur.execute("SELECT COUNT(*) FROM program_companies")
    print(f"  DONE: {resolved} resolved, {skipped} skipped. Total: {cur.fetchone()[0]}")

    # Final summary
    print("\n" + "=" * 60)
    print("ALL FINAL COUNTS")
    print("=" * 60)
    for table in ["contacts", "activities", "programs", "companies", "jobs", "placements",
                   "contracts", "documents", "past_performance", "bd_scoring", "task_orders",
                   "timelines", "program_contacts", "program_companies"]:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"  {table}: {cur.fetchone()[0]:,}")

    elapsed = time.time() - start
    print(f"\nFix completed in {elapsed:.1f}s")

    pg.close()
    sl.close()


if __name__ == "__main__":
    main()
