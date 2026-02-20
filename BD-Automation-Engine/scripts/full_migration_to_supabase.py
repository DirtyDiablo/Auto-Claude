"""
Full Migration to Supabase
===========================
Migrates ALL data from local SQLite databases to Supabase PostgreSQL.

Sources:
  1. bullhorn_master.db — 426K candidates, 404K activities, 50K call notes, placements, scores, past_performance
  2. unified_federal_contracts.db — 33K contacts, 19K programs, 20K scoring, contracts, companies, jobs, etc.
  3. bd_graph.db — 63K entities, 16K relationships (for graph tables / metadata enrichment)
  4. bullhorn_past_performance.db — 6K contact intel, 28K notes, 8K programs, 6K primes

Target: Supabase PostgreSQL (31 tables)
"""

import hashlib
import io
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

# Fix Windows cp1252 encoding for Unicode output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2
from psycopg2.extras import execute_values

# === Configuration ===
BASE_DIR = Path(__file__).parent.parent
BULLHORN_DB = BASE_DIR / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"
UNIFIED_DB = BASE_DIR / "data" / "unified_federal_contracts.db"
GRAPH_DB = BASE_DIR / "Engine8_Knowledge" / "data" / "bd_graph.db"
PAST_PERF_DB = BASE_DIR / "data" / "state" / "bullhorn_past_performance.db"

SUPABASE_DSN = os.environ.get("DATABASE_URL_DIRECT") or os.environ.get("DATABASE_URL")
if not SUPABASE_DSN:
    raise RuntimeError("Set DATABASE_URL_DIRECT or DATABASE_URL in .env for migration")
BATCH_SIZE = 500
SOURCE_PROJECT = "bd_engine"


def content_hash(data: str) -> str:
    """Generate a short content hash for dedup."""
    return hashlib.md5(data.encode("utf-8", errors="replace")).hexdigest()[:16]


def get_pg():
    """Get PostgreSQL connection."""
    conn = psycopg2.connect(SUPABASE_DSN)
    conn.autocommit = False
    return conn


def dict_factory(cursor, row):
    """Convert sqlite3.Row to dict."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_sqlite(db_path):
    """Get SQLite connection with dict row factory."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = dict_factory
    return conn


def sl_count(conn, table):
    """Count rows in a SQLite table (works with dict_factory)."""
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
    return cur.fetchone()["cnt"]


def count_table(pg_cur, table):
    """Count rows in a Supabase table."""
    pg_cur.execute(f"SELECT COUNT(*) FROM {table}")
    return pg_cur.fetchone()[0]


def truncate_table(pg_conn, table):
    """Truncate a Supabase table."""
    cur = pg_conn.cursor()
    try:
        cur.execute(f"TRUNCATE TABLE {table} CASCADE")
        pg_conn.commit()
        print(f"  Truncated {table}")
    except Exception as e:
        pg_conn.rollback()
        try:
            cur.execute(f"DELETE FROM {table}")
            pg_conn.commit()
            print(f"  Deleted all from {table}")
        except Exception:
            pg_conn.rollback()
            print(f"  WARNING: Could not clear {table}: {e}")


def reconnect_if_needed(pg_conn):
    """Reconnect to PostgreSQL if connection is closed."""
    try:
        pg_conn.cursor().execute("SELECT 1")
        return pg_conn
    except Exception:
        try:
            pg_conn.close()
        except Exception:
            pass
        return get_pg()


def batch_insert(pg_conn, table, columns, rows, conflict_col=None):
    """Bulk insert rows into Supabase table (plain inserts, no conflict).
    Returns (count_inserted, pg_conn) - conn may be reconnected."""
    if not rows:
        return 0

    cur = pg_conn.cursor()
    cols_str = ", ".join(columns)
    template = "(" + ", ".join(["%s"] * len(columns)) + ")"

    total = 0
    errors = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        try:
            execute_values(
                cur,
                f"INSERT INTO {table} ({cols_str}) VALUES %s",
                batch,
                template=template,
            )
            pg_conn.commit()
            total += len(batch)
        except Exception as e:
            pg_conn.rollback()
            errors += 1
            if errors <= 3:
                err_str = str(e)[:150]
                print(f"  ERROR batch {i}: {err_str}")
            elif errors == 4:
                print(f"  (suppressing further batch errors...)")
            # Try reconnect + individual rows
            try:
                pg_conn = reconnect_if_needed(pg_conn)
                cur = pg_conn.cursor()
            except Exception:
                pass
            for row in batch:
                try:
                    cur.execute(
                        f"INSERT INTO {table} ({cols_str}) VALUES ({', '.join(['%s']*len(columns))})",
                        row,
                    )
                    pg_conn.commit()
                    total += 1
                except Exception:
                    try:
                        pg_conn.rollback()
                    except Exception:
                        pg_conn = reconnect_if_needed(pg_conn)
                        cur = pg_conn.cursor()

    if errors > 0:
        print(f"  ({errors} batch errors, {total} rows inserted via fallback)")
    return total


def safe_str(val):
    """Convert value to string or None."""
    if val is None:
        return None
    return str(val).strip() if str(val).strip() else None


def safe_float(val):
    """Convert to float or None."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_int(val):
    """Convert to int or None."""
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def safe_bool(val):
    """Convert to bool."""
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val > 0
    return str(val).lower() in ("true", "1", "yes", "t")


def safe_array(val):
    """Convert comma-separated or JSON string to PostgreSQL array."""
    if val is None:
        return None
    if isinstance(val, list):
        return val
    val = str(val).strip()
    if not val:
        return None
    # Try JSON parse
    try:
        parsed = json.loads(val)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    # Comma-separated
    items = [x.strip() for x in val.split(",") if x.strip()]
    return items if items else None


def safe_json(val):
    """Convert to JSON-safe value."""
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return json.dumps(val)
    try:
        parsed = json.loads(str(val))
        return json.dumps(parsed)
    except (json.JSONDecodeError, TypeError):
        return None


# ========================================================================
# Migration Functions
# ========================================================================


def migrate_contacts_from_bullhorn(pg_conn):
    """Migrate 426K candidates from bullhorn_master.db → contacts."""
    print("\n" + "=" * 60)
    print("MIGRATING: Bullhorn candidates → contacts")
    print("=" * 60)

    if not BULLHORN_DB.exists():
        print(f"  SKIP: {BULLHORN_DB} not found")
        return

    sl = get_sqlite(BULLHORN_DB)
    cur = sl.cursor()

    # Get all candidates
    total = sl_count(sl, "candidates")
    print(f"  Source: {total:,} candidates")

    # Check existing
    pg_cur = pg_conn.cursor()
    existing = count_table(pg_cur, "contacts")
    print(f"  Existing in Supabase: {existing:,}")

    # Get contact scores for enrichment
    scores = {}
    try:
        cur.execute("SELECT contact_name, score, tier, primes, scoring_factors FROM contact_scores")
        for row in cur.fetchall():
            scores[row["contact_name"]] = {
                "score": row["score"],
                "tier": row["tier"],
                "primes": row["primes"],
                "factors": row["scoring_factors"],
            }
    except Exception:
        pass
    print(f"  Loaded {len(scores):,} contact scores for enrichment")

    # Get contact activity summaries
    activity_summaries = {}
    try:
        cur.execute("""SELECT contact_name, total_interactions, engagement_score,
                       primes_associated, programs_associated
                       FROM contact_activity_summary""")
        for row in cur.fetchall():
            activity_summaries[row["contact_name"]] = dict(row)
    except Exception:
        pass
    print(f"  Loaded {len(activity_summaries):,} activity summaries")

    # Process in chunks
    offset = 0
    migrated = 0

    while offset < total:
        cur.execute(f"""
            SELECT * FROM candidates
            ORDER BY id
            LIMIT {BATCH_SIZE} OFFSET {offset}
        """)
        rows_data = cur.fetchall()
        if not rows_data:
            break

        batch_rows = []
        for row in rows_data:
            full_name = safe_str(row["full_name"]) or ""
            parts = full_name.split(None, 1)
            first = parts[0] if parts else ""
            last = parts[1] if len(parts) > 1 else ""

            # Enrichment from scores
            score_data = scores.get(full_name, {})
            act_data = activity_summaries.get(full_name, {})

            bd_score = safe_float(score_data.get("score")) or 0
            tier = safe_int(score_data.get("tier"))
            primes = safe_str(score_data.get("primes"))

            interaction_count = safe_int(act_data.get("total_interactions")) or 0
            engagement = safe_float(act_data.get("engagement_score"))
            programs_assoc = safe_str(act_data.get("programs_associated"))
            primes_assoc = safe_str(act_data.get("primes_associated")) or primes

            # Clearance mapping
            clearance_raw = safe_str(row["clearance_level"]) or ""
            clearance = "none"
            cl = clearance_raw.lower()
            if "ts/sci" in cl and "poly" in cl:
                clearance = "ts_sci_poly"
            elif "ts/sci" in cl or "ts sci" in cl:
                clearance = "ts_sci"
            elif "top secret" in cl or cl == "ts":
                clearance = "top_secret"
            elif "secret" in cl:
                clearance = "secret"
            elif "public trust" in cl:
                clearance = "public_trust"

            # Priority from BD score
            priority = "cold"
            if bd_score >= 80:
                priority = "hot"
            elif bd_score >= 50:
                priority = "warm"

            ch = content_hash(f"bh_{row['bullhorn_candidate_id']}_{full_name}")

            batch_rows.append((
                SOURCE_PROJECT,  # source_project
                ch,  # content_hash
                first,  # first_name
                last,  # last_name
                safe_str(row["job_title"]) or safe_str(row["occupation"]) or "",  # title
                safe_str(row["company_name"]) or safe_str(row["current_employer"]) or "",  # company
                safe_str(row["email"]),  # email
                safe_str(row["phone"]),  # phone
                safe_str(row["linkedin_url"]),  # linkedin_url
                tier,  # hierarchy_tier
                bd_score,  # bd_score
                clearance,  # clearance
                priority,  # priority
                safe_str(row["bullhorn_candidate_id"]),  # bullhorn_id
                safe_array(programs_assoc),  # programs
                None,  # skills
                None,  # notes
                safe_str(row["address"]),  # location
                None,  # agency
                interaction_count,  # interaction_count
                None,  # last_interaction_date
                engagement,  # sentiment_score
                primes_assoc,  # associated_primes
                programs_assoc,  # associated_programs
                None,  # data_quality_score
                ch,  # enrichment_hash
            ))

        columns = [
            "source_project", "content_hash", "first_name", "last_name", "title",
            "company", "email", "phone", "linkedin_url", "hierarchy_tier",
            "bd_score", "clearance", "priority", "bullhorn_id", "programs",
            "skills", "notes", "location", "agency", "interaction_count",
            "last_interaction_date", "sentiment_score", "associated_primes",
            "associated_programs", "data_quality_score", "enrichment_hash",
        ]

        inserted = batch_insert(pg_conn, "contacts", columns, batch_rows)
        migrated += inserted
        offset += BATCH_SIZE

        if offset % 10000 == 0 or offset >= total:
            print(f"  Progress: {min(offset, total):,}/{total:,} processed, {migrated:,} inserted")

    sl.close()
    final = count_table(pg_cur, "contacts")
    print(f"  DONE: {migrated:,} inserted. Total contacts now: {final:,}")


def migrate_contacts_from_unified(pg_conn):
    """Merge 33K contacts from unified_federal_contracts.db (richer fields)."""
    print("\n" + "=" * 60)
    print("MIGRATING: Unified DB contacts → contacts (merge/enrich)")
    print("=" * 60)

    if not UNIFIED_DB.exists():
        print(f"  SKIP: {UNIFIED_DB} not found")
        return

    sl = get_sqlite(UNIFIED_DB)
    cur = sl.cursor()

    total = sl_count(sl, "contacts")
    print(f"  Source: {total:,} contacts")

    # Get column names
    cur.execute("PRAGMA table_info(contacts)")
    cols = [row.get("name", row.get(1, "")) if isinstance(row, dict) else row[1] for row in cur.fetchall()]
    print(f"  Columns: {', '.join(cols[:15])}...")

    offset = 0
    migrated = 0

    while offset < total:
        cur.execute(f"SELECT * FROM contacts ORDER BY rowid LIMIT {BATCH_SIZE} OFFSET {offset}")
        rows_data = cur.fetchall()
        if not rows_data:
            break

        batch_rows = []
        for row in rows_data:
            full_name = safe_str(row["full_name"]) or ""
            parts = full_name.split(None, 1)
            first = parts[0] if parts else ""
            last = parts[1] if len(parts) > 1 else ""

            # Map clearance
            clearance_raw = safe_str(row["clearances"]) if "clearances" in cols else ""
            clearance = "none"
            if clearance_raw:
                cl = clearance_raw.lower()
                if "ts/sci" in cl and "poly" in cl:
                    clearance = "ts_sci_poly"
                elif "ts/sci" in cl:
                    clearance = "ts_sci"
                elif "top secret" in cl:
                    clearance = "top_secret"
                elif "secret" in cl:
                    clearance = "secret"

            bd_score = safe_float(row["bd_priority"]) if "bd_priority" in cols else 0

            # Get tier
            tier_raw = safe_str(row["tier"]) if "tier" in cols else None
            tier = None
            if tier_raw:
                try:
                    tier = int(tier_raw.replace("Tier ", "").replace("tier", "").strip())
                except ValueError:
                    pass

            priority = "cold"
            if bd_score and bd_score >= 80:
                priority = "hot"
            elif bd_score and bd_score >= 50:
                priority = "warm"

            ch = content_hash(f"ufc_{full_name}_{safe_str(row['company']) if 'company' in cols else ''}")

            batch_rows.append((
                SOURCE_PROJECT,
                ch,
                first,
                last,
                safe_str(row["title"]) if "title" in cols else "",
                safe_str(row["company"]) if "company" in cols else "",
                safe_str(row["email"]) if "email" in cols else None,
                safe_str(row["phone"]) if "phone" in cols else None,
                safe_str(row["linkedin"]) if "linkedin" in cols else None,
                tier,
                bd_score or 0,
                clearance,
                priority,
                None,  # bullhorn_id
                safe_array(row["program"]) if "program" in cols else None,
                None,  # skills
                None,  # notes
                None,  # location
                None,  # agency
                0,  # interaction_count
                None,  # last_interaction_date
                safe_float(row["relationship_score"]) if "relationship_score" in cols else None,
                safe_str(row["associated_primes"]) if "associated_primes" in cols else None,
                safe_str(row["program"]) if "program" in cols else None,
                safe_float(row["data_quality_score"]) if "data_quality_score" in cols else None,
                ch,
            ))

        columns = [
            "source_project", "content_hash", "first_name", "last_name", "title",
            "company", "email", "phone", "linkedin_url", "hierarchy_tier",
            "bd_score", "clearance", "priority", "bullhorn_id", "programs",
            "skills", "notes", "location", "agency", "interaction_count",
            "last_interaction_date", "sentiment_score", "associated_primes",
            "associated_programs", "data_quality_score", "enrichment_hash",
        ]

        inserted = batch_insert(pg_conn, "contacts", columns, batch_rows)
        migrated += inserted
        offset += BATCH_SIZE

        if offset % 5000 == 0 or offset >= total:
            print(f"  Progress: {min(offset, total):,}/{total:,} processed, {migrated:,} inserted")

    sl.close()
    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "contacts")
    print(f"  DONE: {migrated:,} inserted. Total contacts now: {final:,}")


def migrate_programs(pg_conn):
    """Migrate 19K programs from unified_federal_contracts.db → programs."""
    print("\n" + "=" * 60)
    print("MIGRATING: Unified DB programs → programs")
    print("=" * 60)

    if not UNIFIED_DB.exists():
        print(f"  SKIP: {UNIFIED_DB} not found")
        return

    sl = get_sqlite(UNIFIED_DB)
    cur = sl.cursor()

    total = sl_count(sl, "programs")
    print(f"  Source: {total:,} programs")

    cur.execute("PRAGMA table_info(programs)")
    cols = [row.get("name", row.get(1, "")) if isinstance(row, dict) else row[1] for row in cur.fetchall()]

    offset = 0
    migrated = 0

    while offset < total:
        cur.execute(f"SELECT * FROM programs ORDER BY rowid LIMIT {BATCH_SIZE} OFFSET {offset}")
        rows_data = cur.fetchall()
        if not rows_data:
            break

        batch_rows = []
        for row in rows_data:
            name = safe_str(row["program_name"]) if "program_name" in cols else safe_str(row.get("name"))
            if not name:
                continue

            ch = content_hash(f"prog_{name}_{safe_str(row.get('contract_number', ''))}")

            # Map clearance
            clearance_raw = safe_str(row["clearance_requirements"]) if "clearance_requirements" in cols else ""
            clearance = "none"
            if clearance_raw:
                cl = clearance_raw.lower()
                if "ts/sci" in cl:
                    clearance = "ts_sci"
                elif "top secret" in cl:
                    clearance = "top_secret"
                elif "secret" in cl:
                    clearance = "secret"

            domain_tags = safe_array(row["domain_tags"]) if "domain_tags" in cols else []
            if domain_tags:
                domain_tags = json.dumps(domain_tags)
            else:
                domain_tags = "[]"

            batch_rows.append((
                SOURCE_PROJECT,
                ch,
                name,
                (safe_str(row["agency_owner"]) if "agency_owner" in cols else safe_str(row.get("agency"))) or "",
                None,  # branch
                safe_array(row["prime_contractor"]) if "prime_contractor" in cols else None,
                safe_float(row["total_contract_value"]) if "total_contract_value" in cols else None,
                clearance,
                safe_array(row["naics_code"]) if "naics_code" in cols else None,
                safe_str(row.get("contract_vehicle")),
                safe_str(row.get("contract_number")),
                safe_str(row.get("pop_start")),
                safe_str(row.get("pop_end")),
                safe_str(row.get("location")),
                safe_str(row.get("description")) or name,
                safe_float(row.get("data_quality_score")) or 0,
                safe_str(row.get("recompete_date")),
                safe_str(row.get("incumbent")),
                safe_str(row.get("set_aside")),
                None,  # award_type
                safe_str(row.get("place_of_performance")),
                safe_array(row.get("technical_stack")) if "technical_stack" in cols else None,
                safe_str(row.get("typical_roles")),
                safe_str(row.get("priority_level")) or "Cold",
                safe_float(row.get("total_contract_value")),
                safe_str(row.get("prime_contractor")) if "prime_contractor" in cols else None,
                safe_str(row.get("pop_end")),
                domain_tags,
                safe_float(row.get("data_quality_score")),
                ch,
            ))

        columns = [
            "source_project", "content_hash", "name", "agency", "branch",
            "primes", "value", "clearance", "naics_codes", "contract_vehicle",
            "contract_number", "pop_start", "pop_end", "location", "description",
            "bd_score", "recompete_date", "incumbent", "set_aside", "award_type",
            "place_of_performance", "keywords", "typical_roles", "priority_level",
            "total_contract_value", "prime_contractor_consolidated", "pop_end_consolidated",
            "domain_tags", "data_quality_score", "enrichment_hash",
        ]

        inserted = batch_insert(pg_conn, "programs", columns, batch_rows)
        migrated += inserted
        offset += BATCH_SIZE

        if offset % 5000 == 0 or offset >= total:
            print(f"  Progress: {min(offset, total):,}/{total:,} processed, {migrated:,} inserted")

    sl.close()
    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "programs")
    print(f"  DONE: {migrated:,} inserted. Total programs now: {final:,}")


def migrate_companies(pg_conn):
    """Migrate 6K companies from unified_federal_contracts.db → companies."""
    print("\n" + "=" * 60)
    print("MIGRATING: Unified DB companies → companies")
    print("=" * 60)

    if not UNIFIED_DB.exists():
        return

    sl = get_sqlite(UNIFIED_DB)
    cur = sl.cursor()

    total = sl_count(sl, "companies")
    print(f"  Source: {total:,} companies")

    cur.execute("PRAGMA table_info(companies)")
    cols = [row.get("name", row.get(1, "")) if isinstance(row, dict) else row[1] for row in cur.fetchall()]

    offset = 0
    migrated = 0

    while offset < total:
        cur.execute(f"SELECT * FROM companies ORDER BY rowid LIMIT {BATCH_SIZE} OFFSET {offset}")
        rows_data = cur.fetchall()
        if not rows_data:
            break

        batch_rows = []
        for row in rows_data:
            name = safe_str(row["name"]) if "name" in cols else ""
            if not name:
                continue

            ch = content_hash(f"co_{name}_{safe_str(row.get('uei', ''))}")

            batch_rows.append((
                SOURCE_PROJECT,
                ch,
                name,
                safe_str(row.get("uei")),
                safe_str(row.get("cage_code")),
                safe_str(row.get("duns_number")),
                safe_array(row.get("naics_codes")) if "naics_codes" in cols else None,
                safe_str(row.get("company_type")),
                safe_str(row.get("relationship_tier")),
                safe_float(row.get("usaspending_total_obligated")),
                safe_int(row.get("contract_count")) if "contract_count" in cols else None,
                safe_float(row.get("data_quality_score")) if "data_quality_score" in cols else None,
                ch,
            ))

        columns = [
            "source_project", "content_hash", "name", "uei", "cage_code",
            "duns_number", "naics_codes", "company_type", "relationship_tier",
            "usaspending_total_obligated", "employee_count", "data_quality_score",
            "enrichment_hash",
        ]

        inserted = batch_insert(pg_conn, "companies", columns, batch_rows)
        migrated += inserted
        offset += BATCH_SIZE

    sl.close()
    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "companies")
    print(f"  DONE: {migrated:,} inserted. Total companies now: {final:,}")


def migrate_contracts(pg_conn):
    """Migrate 4.4K contracts from unified_federal_contracts.db → contracts."""
    print("\n" + "=" * 60)
    print("MIGRATING: Unified DB contracts → contracts")
    print("=" * 60)

    if not UNIFIED_DB.exists():
        return

    sl = get_sqlite(UNIFIED_DB)
    cur = sl.cursor()

    total = sl_count(sl, "contracts")
    print(f"  Source: {total:,} contracts")

    cur.execute("PRAGMA table_info(contracts)")
    cols = [row.get("name", row.get(1, "")) if isinstance(row, dict) else row[1] for row in cur.fetchall()]

    offset = 0
    migrated = 0

    while offset < total:
        cur.execute(f"SELECT * FROM contracts ORDER BY rowid LIMIT {BATCH_SIZE} OFFSET {offset}")
        rows_data = cur.fetchall()
        if not rows_data:
            break

        batch_rows = []
        for row in rows_data:
            piid = safe_str(row.get("piid")) or ""
            ch = content_hash(f"ctr_{piid}_{safe_str(row.get('recipient_name', ''))}")

            batch_rows.append((
                SOURCE_PROJECT,
                ch,
                piid,  # award_id (use piid)
                piid,
                safe_str(row.get("awarding_agency")) or safe_str(row.get("agency")) or "",
                safe_str(row.get("recipient_name")) or "",
                safe_str(row.get("recipient_uei")),
                None,  # cage_code
                safe_float(row.get("award_amount")),
                safe_float(row.get("obligated")),
                safe_str(row.get("start_date")),
                safe_str(row.get("end_date")),
                "active",
                "usaspending",
                safe_str(row.get("naics_code")),
                safe_str(row.get("psc_code")),
                safe_str(row.get("description")),
                safe_str(row.get("place_of_performance")),
                safe_str(row.get("set_aside")),
                None,  # competition_type
                None,  # parent_award_id
            ))

        columns = [
            "source_project", "content_hash", "award_id", "piid", "agency",
            "contractor_name", "contractor_uei", "contractor_cage_code",
            "contract_value", "obligated_amount", "period_of_performance_start",
            "period_of_performance_end", "status", "source", "naics_code",
            "psc_code", "description", "place_of_performance", "set_aside",
            "competition_type", "parent_award_id",
        ]

        inserted = batch_insert(pg_conn, "contracts", columns, batch_rows)
        migrated += inserted
        offset += BATCH_SIZE

    sl.close()
    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "contracts")
    print(f"  DONE: {migrated:,} inserted. Total contracts now: {final:,}")


def migrate_jobs(pg_conn):
    """Migrate jobs from unified + bullhorn → jobs."""
    print("\n" + "=" * 60)
    print("MIGRATING: Jobs → jobs")
    print("=" * 60)

    # From unified DB
    if UNIFIED_DB.exists():
        sl = get_sqlite(UNIFIED_DB)
        cur = sl.cursor()
        total = sl_count(sl, "jobs")
        print(f"  Source (unified): {total:,} jobs")

        cur.execute("PRAGMA table_info(jobs)")
        cols = [row.get("name", row.get(1, "")) if isinstance(row, dict) else row[1] for row in cur.fetchall()]

        offset = 0
        migrated = 0

        while offset < total:
            cur.execute(f"SELECT * FROM jobs ORDER BY rowid LIMIT {BATCH_SIZE} OFFSET {offset}")
            rows_data = cur.fetchall()
            if not rows_data:
                break

            batch_rows = []
            for row in rows_data:
                title = safe_str(row.get("title")) or ""
                company = safe_str(row.get("company")) or safe_str(row.get("prime", ""))
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

                batch_rows.append((
                    SOURCE_PROJECT,
                    ch,
                    title,
                    company,
                    safe_str(row.get("location")) or "",
                    safe_str(row.get("description")),
                    clearance,
                    None,  # salary_min
                    None,  # salary_max
                    safe_float(row.get("pay_rate")),
                    safe_float(row.get("bill_rate")),
                    safe_array(row.get("skills")) if "skills" in cols else None,
                    safe_float(row.get("bd_score")) or 0,
                    "enriched",
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

            inserted = batch_insert(pg_conn, "jobs", columns, batch_rows)
            migrated += inserted
            offset += BATCH_SIZE

        sl.close()
        print(f"  Migrated {migrated:,} jobs from unified DB")

    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "jobs")
    print(f"  Total jobs now: {final:,}")


def migrate_activities(pg_conn):
    """Migrate 404K activities from bullhorn_master.db → activities."""
    print("\n" + "=" * 60)
    print("MIGRATING: Bullhorn activities → activities")
    print("=" * 60)

    if not BULLHORN_DB.exists():
        return

    sl = get_sqlite(BULLHORN_DB)
    cur = sl.cursor()

    total = sl_count(sl, "activities")
    print(f"  Source: {total:,} activities")

    offset = 0
    migrated = 0

    while offset < total:
        cur.execute(f"""
            SELECT * FROM activities
            ORDER BY id
            LIMIT {BATCH_SIZE} OFFSET {offset}
        """)
        rows_data = cur.fetchall()
        if not rows_data:
            break

        batch_rows = []
        for row in rows_data:
            ch = content_hash(f"act_{row['bullhorn_activity_id']}_{safe_str(row.get('activity_date', ''))}")

            # Map activity type
            act_type = safe_str(row.get("activity_type")) or "other"
            valid_types = {"call", "email", "meeting", "note", "submission", "interview", "placement", "other"}
            if act_type.lower() not in valid_types:
                act_type = "other"

            batch_rows.append((
                SOURCE_PROJECT,
                ch,
                act_type.lower(),
                safe_str(row.get("subject")) or safe_str(row.get("action")) or "",
                safe_str(row.get("note_text")) or safe_str(row.get("comments")),
                safe_str(row.get("action")),
                safe_str(row.get("activity_date")),
                None,  # contact_id (UUID - will wire later)
                None,  # job_id
                None,  # program_id
                None,  # company_id
                safe_str(row.get("actor")),
                None,  # notes
                None,  # outcome
                None,  # next_action
                None,  # next_action_date
                False,
                safe_str(row.get("bullhorn_activity_id")),
                False,  # hiring_signal
                False,  # positive_response
                False,  # traction
                None,  # sentiment_score
                "neutral",
            ))

        columns = [
            "source_project", "content_hash", "activity_type", "subject",
            "content", "action", "activity_date", "contact_id", "job_id",
            "program_id", "company_id", "owner", "notes", "outcome",
            "next_action", "next_action_date", "follow_up_required",
            "bullhorn_activity_id", "hiring_signal", "positive_response",
            "traction", "sentiment_score", "priority",
        ]

        inserted = batch_insert(pg_conn, "activities", columns, batch_rows)
        migrated += inserted
        offset += BATCH_SIZE

        if offset % 50000 == 0 or offset >= total:
            print(f"  Progress: {min(offset, total):,}/{total:,} processed, {migrated:,} inserted")

    sl.close()
    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "activities")
    print(f"  DONE: {migrated:,} inserted. Total activities now: {final:,}")


def migrate_call_notes_as_activities(pg_conn):
    """Migrate 50K call notes from bullhorn → activities (type=note)."""
    print("\n" + "=" * 60)
    print("MIGRATING: Bullhorn call_notes → activities")
    print("=" * 60)

    if not BULLHORN_DB.exists():
        return

    sl = get_sqlite(BULLHORN_DB)
    cur = sl.cursor()

    total = sl_count(sl, "call_notes")
    print(f"  Source: {total:,} call notes")

    offset = 0
    migrated = 0

    while offset < total:
        cur.execute(f"SELECT * FROM call_notes ORDER BY rowid LIMIT {BATCH_SIZE} OFFSET {offset}")
        rows_data = cur.fetchall()
        if not rows_data:
            break

        batch_rows = []
        for row in rows_data:
            ch = content_hash(f"cn_{safe_str(row.get('note_author', ''))}_{safe_str(row.get('date_added', ''))}_{safe_str(row.get('about', ''))}")

            batch_rows.append((
                SOURCE_PROJECT,
                ch,
                "note",
                safe_str(row.get("about")) or "",
                safe_str(row.get("note_body")),
                safe_str(row.get("note_action")) or safe_str(row.get("action")),
                safe_str(row.get("date_added")),
                None, None, None, None,
                safe_str(row.get("note_author")),
                None, None, None, None,
                False,
                None,  # no bullhorn_activity_id for call notes
                safe_bool(row.get("hiring_signal")),
                safe_bool(row.get("positive_response")),
                safe_bool(row.get("has_traction")),
                None,
                "neutral",
            ))

        columns = [
            "source_project", "content_hash", "activity_type", "subject",
            "content", "action", "activity_date", "contact_id", "job_id",
            "program_id", "company_id", "owner", "notes", "outcome",
            "next_action", "next_action_date", "follow_up_required",
            "bullhorn_activity_id", "hiring_signal", "positive_response",
            "traction", "sentiment_score", "priority",
        ]

        inserted = batch_insert(pg_conn, "activities", columns, batch_rows)
        migrated += inserted
        offset += BATCH_SIZE

        if offset % 10000 == 0 or offset >= total:
            print(f"  Progress: {min(offset, total):,}/{total:,} processed, {migrated:,} inserted")

    sl.close()
    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "activities")
    print(f"  DONE: {migrated:,} inserted. Total activities now: {final:,}")


def migrate_placements(pg_conn):
    """Migrate placements from unified + bullhorn → placements."""
    print("\n" + "=" * 60)
    print("MIGRATING: Placements → placements")
    print("=" * 60)

    # From unified DB (richer data - 1,243 rows)
    if UNIFIED_DB.exists():
        sl = get_sqlite(UNIFIED_DB)
        cur = sl.cursor()
        total = sl_count(sl, "placements")
        print(f"  Source (unified): {total:,} placements")

        cur.execute("PRAGMA table_info(placements)")
        cols = [row.get("name", row.get(1, "")) if isinstance(row, dict) else row[1] for row in cur.fetchall()]

        cur.execute("SELECT * FROM placements")
        rows_data = cur.fetchall()

        batch_rows = []
        for row in rows_data:
            ch = content_hash(f"pl_{safe_str(row.get('bullhorn_placement_id', ''))}_{safe_str(row.get('candidate_name', ''))}")

            batch_rows.append((
                SOURCE_PROJECT,
                ch,
                safe_str(row.get("bullhorn_placement_id")),
                None, None, None, None,  # FK UUIDs
                "active",
                safe_str(row.get("job_title")) or "",
                safe_str(row.get("candidate_name")) or "",
                safe_str(row.get("client_name")) or "",
                None,  # owner
                safe_str(row.get("start_date")),
                safe_str(row.get("end_date")),
                None,  # placement_date
                safe_float(row.get("pay_rate")),
                safe_float(row.get("bill_rate")),
                safe_float(row.get("estimated_revenue")),
                None,  # duration_days
                None,  # commission
            ))

        columns = [
            "source_project", "content_hash", "bullhorn_placement_id",
            "job_id", "contact_id", "company_id", "program_id",
            "status", "job_title", "candidate_name", "client_name",
            "owner", "start_date", "end_date", "placement_date",
            "pay_rate", "bill_rate", "salary", "duration_days", "commission",
        ]

        inserted = batch_insert(pg_conn, "placements", columns, batch_rows)
        sl.close()
        print(f"  Migrated {inserted:,} placements")

    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "placements")
    print(f"  Total placements now: {final:,}")


def migrate_past_performance(pg_conn):
    """Migrate past_performance from bullhorn → past_performance."""
    print("\n" + "=" * 60)
    print("MIGRATING: Past performance → past_performance")
    print("=" * 60)

    if not BULLHORN_DB.exists():
        return

    sl = get_sqlite(BULLHORN_DB)
    cur = sl.cursor()

    total = sl_count(sl, "past_performance")
    print(f"  Source: {total:,} past_performance records")

    cur.execute("SELECT * FROM past_performance")
    rows_data = cur.fetchall()

    batch_rows = []
    for row in rows_data:
        ch = content_hash(f"pp_{safe_str(row.get('prime_contractor_name', ''))}_{safe_str(row.get('program_name', ''))}")

        batch_rows.append((
            SOURCE_PROJECT,
            ch,
            None,  # company_id UUID
            safe_str(row.get("prime_contractor_name")) or "",
            None,  # program_id UUID
            safe_str(row.get("program_name")) or "",
            safe_int(row.get("total_jobs")) or 0,
            safe_int(row.get("open_jobs")) or 0,
            0,  # closed_jobs
            0,  # filled_jobs
            safe_int(row.get("total_placements")) or 0,
            0,  # active_placements
            safe_float(row.get("total_revenue")) or 0,
            safe_float(row.get("avg_bill_rate")) or 0,
            0,  # avg_pay_rate
            0,  # avg_margin
            safe_float(row.get("fill_rate")) or 0,
            safe_float(row.get("performance_score")) or 0,
        ))

    columns = [
        "source_project", "content_hash", "company_id", "company_name",
        "program_id", "program_name", "total_jobs", "open_jobs",
        "closed_jobs", "filled_jobs", "total_placements", "active_placements",
        "total_revenue", "avg_bill_rate", "avg_pay_rate", "avg_margin",
        "fill_rate", "performance_score",
    ]

    inserted = batch_insert(pg_conn, "past_performance", columns, batch_rows)
    sl.close()

    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "past_performance")
    print(f"  DONE: {inserted:,} inserted. Total past_performance now: {final:,}")


def migrate_scoring(pg_conn):
    """Migrate 20K scoring records from unified → bd_scoring."""
    print("\n" + "=" * 60)
    print("MIGRATING: Scoring → bd_scoring")
    print("=" * 60)

    if not UNIFIED_DB.exists():
        return

    sl = get_sqlite(UNIFIED_DB)
    cur = sl.cursor()

    total = sl_count(sl, "scoring")
    print(f"  Source: {total:,} scoring records")

    cur.execute("PRAGMA table_info(scoring)")
    cols = [row.get("name", row.get(1, "")) if isinstance(row, dict) else row[1] for row in cur.fetchall()]

    offset = 0
    migrated = 0

    while offset < total:
        cur.execute(f"SELECT * FROM scoring ORDER BY rowid LIMIT {BATCH_SIZE} OFFSET {offset}")
        rows_data = cur.fetchall()
        if not rows_data:
            break

        batch_rows = []
        for row in rows_data:
            ch = content_hash(f"sc_{safe_str(row.get('entity_type', ''))}_{safe_str(row.get('entity_name', ''))}")

            batch_rows.append((
                safe_str(row.get("entity_type")) or "unknown",
                safe_str(row.get("entity_id")),
                safe_str(row.get("entity_name")),
                safe_float(row.get("bd_score")),
                safe_str(row.get("priority_tier")),
                safe_float(row.get("match_confidence")) if "match_confidence" in cols else None,
                safe_float(row.get("engagement_score")),
                safe_float(row.get("job_activity_score")),
                safe_float(row.get("contract_score")),
                safe_float(row.get("contact_access_score")),
                safe_float(row.get("recompete_proximity_score")),
                safe_float(row.get("composite_score")),
                None,  # scoring_details
                "unified_db",
                ch,
            ))

        columns = [
            "entity_type", "entity_id", "entity_name", "bd_score",
            "priority_tier", "match_confidence", "engagement_score",
            "job_activity_score", "contract_score", "contact_access_score",
            "recompete_proximity_score", "composite_score", "scoring_details",
            "source", "content_hash",
        ]

        inserted = batch_insert(pg_conn, "bd_scoring", columns, batch_rows)
        migrated += inserted
        offset += BATCH_SIZE

    sl.close()
    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "bd_scoring")
    print(f"  DONE: {migrated:,} inserted. Total bd_scoring now: {final:,}")


def migrate_task_orders(pg_conn):
    """Migrate 5.8K task orders/subawards from unified → task_orders."""
    print("\n" + "=" * 60)
    print("MIGRATING: Task orders → task_orders")
    print("=" * 60)

    if not UNIFIED_DB.exists():
        return

    sl = get_sqlite(UNIFIED_DB)
    cur = sl.cursor()

    total = sl_count(sl, "task_orders")
    print(f"  Source: {total:,} task_orders")

    cur.execute("PRAGMA table_info(task_orders)")
    cols = [row.get("name", row.get(1, "")) if isinstance(row, dict) else row[1] for row in cur.fetchall()]

    offset = 0
    migrated = 0

    while offset < total:
        cur.execute(f"SELECT * FROM task_orders ORDER BY rowid LIMIT {BATCH_SIZE} OFFSET {offset}")
        rows_data = cur.fetchall()
        if not rows_data:
            break

        batch_rows = []
        for row in rows_data:
            ch = content_hash(f"to_{safe_str(row.get('prime_name', ''))}_{safe_str(row.get('sub_recipient_name', ''))}_{safe_str(row.get('subaward_date', ''))}")

            batch_rows.append((
                None,  # subaward_id
                None,  # prime_award_id
                None,  # contract_id
                safe_str(row.get("prime_name")),
                safe_str(row.get("prime_uei")),
                safe_str(row.get("sub_recipient_name")),
                safe_str(row.get("sub_recipient_uei")) if "sub_recipient_uei" in cols else None,
                safe_float(row.get("subaward_amount")),
                safe_str(row.get("subaward_date")),
                safe_str(row.get("subaward_description")) if "subaward_description" in cols else None,
                safe_str(row.get("awarding_agency")),
                safe_str(row.get("fiscal_year")) if "fiscal_year" in cols else None,
                False,  # is_competitor
                None,  # competitor_match
                safe_str(row.get("source_file")) if "source_file" in cols else None,
                ch,
            ))

        columns = [
            "subaward_id", "prime_award_id", "contract_id", "prime_name",
            "prime_uei", "sub_recipient_name", "sub_recipient_uei",
            "subaward_amount", "subaward_date", "subaward_description",
            "awarding_agency", "fiscal_year", "is_competitor",
            "competitor_match", "source_file", "content_hash",
        ]

        inserted = batch_insert(pg_conn, "task_orders", columns, batch_rows)
        migrated += inserted
        offset += BATCH_SIZE

    sl.close()
    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "task_orders")
    print(f"  DONE: {migrated:,} inserted. Total task_orders now: {final:,}")


def migrate_timelines(pg_conn):
    """Migrate 9.9K timeline events from unified → timelines."""
    print("\n" + "=" * 60)
    print("MIGRATING: Timelines → timelines")
    print("=" * 60)

    if not UNIFIED_DB.exists():
        return

    sl = get_sqlite(UNIFIED_DB)
    cur = sl.cursor()

    total = sl_count(sl, "timelines")
    print(f"  Source: {total:,} timeline events")

    cur.execute("PRAGMA table_info(timelines)")
    cols = [row.get("name", row.get(1, "")) if isinstance(row, dict) else row[1] for row in cur.fetchall()]

    offset = 0
    migrated = 0

    while offset < total:
        cur.execute(f"SELECT * FROM timelines ORDER BY rowid LIMIT {BATCH_SIZE} OFFSET {offset}")
        rows_data = cur.fetchall()
        if not rows_data:
            break

        batch_rows = []
        for row in rows_data:
            ch = content_hash(f"tl_{safe_str(row.get('event_type', ''))}_{safe_str(row.get('event_date', ''))}_{safe_str(row.get('program_name', ''))}")

            batch_rows.append((
                safe_str(row.get("event_type")) or "unknown",
                safe_str(row.get("event_date")),
                None,  # program_id UUID
                safe_str(row.get("program_name")),
                None,  # contract_id
                safe_str(row.get("piid")) if "piid" in cols else None,
                safe_str(row.get("description")),
                safe_int(row.get("days_until_event")),
                safe_str(row.get("urgency")),
                safe_str(row.get("source")) if "source" in cols else "unified_db",
                ch,
            ))

        columns = [
            "event_type", "event_date", "program_id", "program_name",
            "contract_id", "piid", "description", "days_until_event",
            "urgency", "source", "content_hash",
        ]

        inserted = batch_insert(pg_conn, "timelines", columns, batch_rows)
        migrated += inserted
        offset += BATCH_SIZE

    sl.close()
    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "timelines")
    print(f"  DONE: {migrated:,} inserted. Total timelines now: {final:,}")


def migrate_documents(pg_conn):
    """Migrate 19.8K documents from unified → documents."""
    print("\n" + "=" * 60)
    print("MIGRATING: Documents → documents")
    print("=" * 60)

    if not UNIFIED_DB.exists():
        return

    sl = get_sqlite(UNIFIED_DB)
    cur = sl.cursor()

    total = sl_count(sl, "documents")
    print(f"  Source: {total:,} documents")

    cur.execute("PRAGMA table_info(documents)")
    cols = [row.get("name", row.get(1, "")) if isinstance(row, dict) else row[1] for row in cur.fetchall()]

    offset = 0
    migrated = 0

    while offset < total:
        cur.execute(f"SELECT * FROM documents ORDER BY rowid LIMIT {BATCH_SIZE} OFFSET {offset}")
        rows_data = cur.fetchall()
        if not rows_data:
            break

        batch_rows = []
        for row in rows_data:
            title = safe_str(row.get("title")) or ""
            ch = content_hash(f"doc_{safe_str(row.get('doc_type', ''))}_{title[:50]}")

            doc_type = safe_str(row.get("doc_type")) or "other"
            valid_types = {"past_performance", "capability_statement", "proposal", "briefing", "contract_document", "intelligence", "other"}
            if doc_type.lower() not in valid_types:
                doc_type = "other"

            batch_rows.append((
                SOURCE_PROJECT,
                ch,
                doc_type.lower(),
                title,
                None,  # filename
                None,  # filepath
                None,  # summary
                safe_str(row.get("content")),
                safe_str(row.get("entity_type")) if "entity_type" in cols else None,
                0,  # chunk_index
                1,  # total_chunks
                None,  # program_ids
                None,  # company_ids
                None,  # source_url
            ))

        columns = [
            "source_project", "content_hash", "doc_type", "title",
            "filename", "filepath", "summary", "content", "category",
            "chunk_index", "total_chunks", "program_ids", "company_ids",
            "source_url",
        ]

        inserted = batch_insert(pg_conn, "documents", columns, batch_rows)
        migrated += inserted
        offset += BATCH_SIZE

        if offset % 5000 == 0 or offset >= total:
            print(f"  Progress: {min(offset, total):,}/{total:,} processed, {migrated:,} inserted")

    sl.close()
    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "documents")
    print(f"  DONE: {migrated:,} inserted. Total documents now: {final:,}")


def migrate_program_contacts(pg_conn):
    """Migrate program_contacts join table from unified."""
    print("\n" + "=" * 60)
    print("MIGRATING: Program-Contact relationships → program_contacts")
    print("=" * 60)

    if not UNIFIED_DB.exists():
        return

    sl = get_sqlite(UNIFIED_DB)
    cur = sl.cursor()

    total = sl_count(sl, "program_contacts")
    print(f"  Source: {total:,} program-contact links")

    # We need to look up UUIDs - get maps from Supabase
    pg_cur = pg_conn.cursor()

    # Build content_hash → UUID maps
    pg_cur.execute("SELECT id, content_hash FROM programs WHERE content_hash IS NOT NULL")
    prog_map = {row[1]: row[0] for row in pg_cur.fetchall()}

    pg_cur.execute("SELECT id, content_hash FROM contacts WHERE content_hash IS NOT NULL")
    contact_map = {row[1]: row[0] for row in pg_cur.fetchall()}

    print(f"  Lookup maps: {len(prog_map):,} programs, {len(contact_map):,} contacts")

    # Get program names → UUID mapping
    pg_cur.execute("SELECT id, name FROM programs")
    prog_name_map = {}
    for row in pg_cur.fetchall():
        prog_name_map[row[1].lower().strip()] = row[0]

    # Get contact names → UUID mapping
    pg_cur.execute("SELECT id, first_name, last_name FROM contacts")
    contact_name_map = {}
    for row in pg_cur.fetchall():
        name = f"{row[1]} {row[2]}".strip().lower()
        contact_name_map[name] = row[0]

    # Get unified DB data
    cur.execute("PRAGMA table_info(program_contacts)")
    cols = [row.get("name", row.get(1, "")) if isinstance(row, dict) else row[1] for row in cur.fetchall()]

    cur.execute("SELECT * FROM program_contacts")
    rows_data = cur.fetchall()

    batch_rows = []
    skipped = 0

    for row in rows_data:
        # Try to resolve IDs
        prog_id_raw = safe_str(row.get("program_id"))
        contact_id_raw = safe_str(row.get("contact_id"))
        rel_type = safe_str(row.get("relationship_type")) or "works_on"

        # Look up by name from unified DB
        program_uuid = None
        contact_uuid = None

        # Try direct ID lookup in unified DB to get names
        try:
            cur2 = sl.cursor()
            if prog_id_raw:
                cur2.execute(f"SELECT program_name FROM programs WHERE rowid = ? OR id = ?", (prog_id_raw, prog_id_raw))
                prow = cur2.fetchone()
                if prow:
                    pname = safe_str(prow[0])
                    if pname:
                        program_uuid = prog_name_map.get(pname.lower().strip())

            if contact_id_raw:
                cur2.execute(f"SELECT full_name FROM contacts WHERE rowid = ? OR id = ?", (contact_id_raw, contact_id_raw))
                crow = cur2.fetchone()
                if crow:
                    cname = safe_str(crow[0])
                    if cname:
                        contact_uuid = contact_name_map.get(cname.lower().strip())
        except Exception:
            pass

        if program_uuid and contact_uuid:
            batch_rows.append((
                program_uuid,
                contact_uuid,
                rel_type,
                "unified_db",
            ))
        else:
            skipped += 1

    columns = ["program_id", "contact_id", "relationship_type", "source"]

    inserted = batch_insert(pg_conn, "program_contacts", columns, batch_rows)
    sl.close()

    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "program_contacts")
    print(f"  DONE: {inserted:,} inserted, {skipped:,} skipped (unresolved IDs). Total: {final:,}")


def migrate_program_companies(pg_conn):
    """Migrate program_companies join table from unified."""
    print("\n" + "=" * 60)
    print("MIGRATING: Program-Company relationships → program_companies")
    print("=" * 60)

    if not UNIFIED_DB.exists():
        return

    sl = get_sqlite(UNIFIED_DB)
    cur = sl.cursor()

    total = sl_count(sl, "program_companies")
    print(f"  Source: {total:,} program-company links")

    pg_cur = pg_conn.cursor()

    # Build name → UUID maps
    pg_cur.execute("SELECT id, name FROM programs")
    prog_name_map = {}
    for row in pg_cur.fetchall():
        prog_name_map[row[1].lower().strip()] = row[0]

    pg_cur.execute("SELECT id, name FROM companies")
    company_name_map = {}
    for row in pg_cur.fetchall():
        company_name_map[row[1].lower().strip()] = row[0]

    cur.execute("PRAGMA table_info(program_companies)")
    cols = [row.get("name", row.get(1, "")) if isinstance(row, dict) else row[1] for row in cur.fetchall()]

    cur.execute("SELECT * FROM program_companies")
    rows_data = cur.fetchall()

    batch_rows = []
    skipped = 0

    for row in rows_data:
        prog_id_raw = safe_str(row.get("program_id"))
        company_id_raw = safe_str(row.get("company_id"))
        role = safe_str(row.get("role")) or "prime"
        source = safe_str(row.get("source")) or "unified_db"

        program_uuid = None
        company_uuid = None

        try:
            cur2 = sl.cursor()
            if prog_id_raw:
                cur2.execute(f"SELECT program_name FROM programs WHERE rowid = ? OR id = ?", (prog_id_raw, prog_id_raw))
                prow = cur2.fetchone()
                if prow:
                    pname = safe_str(prow[0])
                    if pname:
                        program_uuid = prog_name_map.get(pname.lower().strip())

            if company_id_raw:
                cur2.execute(f"SELECT name FROM companies WHERE rowid = ? OR id = ?", (company_id_raw, company_id_raw))
                crow = cur2.fetchone()
                if crow:
                    cname = safe_str(crow[0])
                    if cname:
                        company_uuid = company_name_map.get(cname.lower().strip())
        except Exception:
            pass

        if program_uuid and company_uuid:
            batch_rows.append((
                program_uuid,
                company_uuid,
                role,
                source,
            ))
        else:
            skipped += 1

    columns = ["program_id", "company_id", "role", "source"]

    inserted = batch_insert(pg_conn, "program_companies", columns, batch_rows)
    sl.close()

    pg_cur = pg_conn.cursor()
    final = count_table(pg_cur, "program_companies")
    print(f"  DONE: {inserted:,} inserted, {skipped:,} skipped. Total: {final:,}")


def migrate_prime_contractors_as_companies(pg_conn):
    """Migrate 41 prime contractors from bullhorn → companies (merge)."""
    print("\n" + "=" * 60)
    print("MIGRATING: Bullhorn prime_contractors → companies (merge)")
    print("=" * 60)

    if not BULLHORN_DB.exists():
        return

    sl = get_sqlite(BULLHORN_DB)
    cur = sl.cursor()

    cur.execute("SELECT * FROM prime_contractors")
    rows_data = cur.fetchall()
    print(f"  Source: {len(rows_data)} prime contractors")

    batch_rows = []
    for row in rows_data:
        name = safe_str(row.get("name")) or safe_str(row.get("normalized_name")) or ""
        if not name:
            continue
        ch = content_hash(f"prime_{name}")

        batch_rows.append((
            SOURCE_PROJECT,
            ch,
            name,
            safe_str(row.get("cage_code")),
            safe_str(row.get("duns_number")),
            "prime_contractor",
            "Tier 1",
            None,  # data_quality_score
            ch,
        ))

    columns = [
        "source_project", "content_hash", "name", "cage_code", "duns_number",
        "company_type", "relationship_tier", "data_quality_score", "enrichment_hash",
    ]

    inserted = batch_insert(pg_conn, "companies", columns, batch_rows)
    sl.close()
    print(f"  DONE: {inserted:,} prime contractors merged into companies")


# ========================================================================
# Main
# ========================================================================


def main():
    start = time.time()
    print("=" * 60)
    print("FULL MIGRATION TO SUPABASE")
    print("=" * 60)
    print(f"Target: {SUPABASE_DSN[:50]}...")
    print(f"Sources:")
    for db in [BULLHORN_DB, UNIFIED_DB, GRAPH_DB, PAST_PERF_DB]:
        exists = "EXISTS" if db.exists() else "MISSING"
        print(f"  {db.name}: {exists}")

    pg_conn = get_pg()

    # Get baseline counts
    print("\n--- Baseline Counts ---")
    pg_cur = pg_conn.cursor()
    for table in ["contacts", "activities", "programs", "companies", "jobs", "placements",
                   "contracts", "documents", "past_performance", "bd_scoring", "task_orders",
                   "timelines", "program_contacts", "program_companies"]:
        count = count_table(pg_cur, table)
        print(f"  {table}: {count:,}")

    # Truncate all tables (relationship tables first due to FKs)
    print("\n--- Truncating existing data for fresh migration ---")
    for table in ["program_contacts", "program_companies", "document_companies",
                   "document_programs", "campaign_contacts", "report_companies",
                   "bd_scoring", "timelines", "task_orders", "past_performance",
                   "placements", "activities", "documents", "contracts",
                   "jobs", "contacts", "companies", "programs"]:
        truncate_table(pg_conn, table)

    # Run migrations in order (entities first, then relationships)
    print("\n\n>>> PHASE 1: Core Entities <<<")
    migrate_programs(pg_conn)
    migrate_companies(pg_conn)
    migrate_prime_contractors_as_companies(pg_conn)
    migrate_contacts_from_bullhorn(pg_conn)
    migrate_contacts_from_unified(pg_conn)
    migrate_jobs(pg_conn)

    print("\n\n>>> PHASE 2: Activities & Documents <<<")
    migrate_activities(pg_conn)
    migrate_call_notes_as_activities(pg_conn)
    migrate_documents(pg_conn)

    print("\n\n>>> PHASE 3: Intelligence & Scoring <<<")
    migrate_contracts(pg_conn)
    migrate_placements(pg_conn)
    migrate_past_performance(pg_conn)
    migrate_scoring(pg_conn)
    migrate_task_orders(pg_conn)
    migrate_timelines(pg_conn)

    print("\n\n>>> PHASE 4: Relationships <<<")
    migrate_program_contacts(pg_conn)
    migrate_program_companies(pg_conn)

    # Final counts
    print("\n\n" + "=" * 60)
    print("FINAL COUNTS")
    print("=" * 60)
    pg_cur = pg_conn.cursor()
    for table in ["contacts", "activities", "programs", "companies", "jobs", "placements",
                   "contracts", "documents", "past_performance", "bd_scoring", "task_orders",
                   "timelines", "program_contacts", "program_companies"]:
        count = count_table(pg_cur, table)
        print(f"  {table}: {count:,}")

    elapsed = time.time() - start
    print(f"\nTotal time: {elapsed:.1f}s ({elapsed/60:.1f} min)")

    pg_conn.close()
    print("\nMigration complete!")


if __name__ == "__main__":
    main()
