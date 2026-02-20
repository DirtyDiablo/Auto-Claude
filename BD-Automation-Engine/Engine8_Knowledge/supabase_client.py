"""
Supabase client for BD-Automation-Engine.

Provides PostgreSQL-backed data access to replace SQLite/Qdrant reads.
Uses psycopg2 with connection pooling for the API server.
"""

import json
import os
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

# Connection pool (initialized lazily)
_pool: Optional[pool.ThreadedConnectionPool] = None


def _get_dsn() -> str:
    """Get Supabase connection string from env."""
    # Prefer pooler for app runtime
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        dsn = os.environ.get("DATABASE_URL_SESSION")
    if not dsn:
        dsn = os.environ.get("DATABASE_URL_DIRECT")
    if not dsn:
        raise RuntimeError(
            "No database connection string configured. "
            "Set DATABASE_URL, DATABASE_URL_SESSION, or DATABASE_URL_DIRECT in .env"
        )
    return dsn


def get_pool() -> pool.ThreadedConnectionPool:
    """Get or create connection pool."""
    global _pool
    if _pool is None or _pool.closed:
        dsn = _get_dsn()
        if not dsn:
            raise RuntimeError("No Supabase DATABASE_URL configured")
        _pool = pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=dsn,
        )
    return _pool


@contextmanager
def get_conn():
    """Get a connection from the pool (context manager)."""
    p = get_pool()
    conn = p.getconn()
    try:
        yield conn
    finally:
        p.putconn(conn)


@contextmanager
def get_cursor():
    """Get a dict cursor from the pool."""
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cur
        finally:
            conn.commit()


def is_available() -> bool:
    """Check if Supabase connection works."""
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1")
            return True
    except Exception:
        return False


# ========================================================================
# Query Functions
# ========================================================================


def get_contacts(
    limit: int = 500,
    offset: int = 0,
    search: Optional[str] = None,
    company: Optional[str] = None,
    priority: Optional[str] = None,
    min_score: Optional[float] = None,
    sort_by: str = "bd_score",
    sort_dir: str = "desc",
) -> Tuple[List[Dict], int]:
    """Get contacts with filtering and pagination."""
    conditions = []
    params: List[Any] = []

    if search:
        conditions.append("(first_name ILIKE %s OR last_name ILIKE %s OR company ILIKE %s)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    if company:
        conditions.append("company ILIKE %s")
        params.append(f"%{company}%")

    if priority:
        conditions.append("priority = %s")
        params.append(priority)

    if min_score is not None:
        conditions.append("bd_score >= %s")
        params.append(min_score)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Validate sort
    allowed_sorts = {"bd_score", "first_name", "last_name", "company", "created_at", "interaction_count", "data_quality_score"}
    if sort_by not in allowed_sorts:
        sort_by = "bd_score"
    direction = "DESC" if sort_dir.lower() == "desc" else "ASC"

    with get_cursor() as cur:
        # Count
        cur.execute(f"SELECT COUNT(*) as total FROM contacts {where}", params)
        total = cur.fetchone()["total"]

        # Data
        cur.execute(
            f"""SELECT id, first_name, last_name, title, company, email, phone,
                       linkedin_url, hierarchy_tier, bd_score, clearance, priority,
                       bullhorn_id, programs, skills, location, agency,
                       interaction_count, sentiment_score, associated_primes,
                       associated_programs, data_quality_score, created_at
                FROM contacts {where}
                ORDER BY {sort_by} {direction} NULLS LAST
                LIMIT %s OFFSET %s""",
            params + [limit, offset],
        )
        rows = [dict(r) for r in cur.fetchall()]

    # Convert UUID to string and add tier alias for dashboard compatibility
    for r in rows:
        r["id"] = str(r["id"])
        if r.get("hierarchy_tier") is not None:
            r["tier"] = r["hierarchy_tier"]

    return rows, total


def get_programs(
    limit: int = 500,
    offset: int = 0,
    search: Optional[str] = None,
    agency: Optional[str] = None,
    domain: Optional[str] = None,
    min_quality: Optional[float] = None,
    sort_by: str = "data_quality_score",
    sort_dir: str = "desc",
) -> Tuple[List[Dict], int]:
    """Get programs with filtering and pagination."""
    conditions = []
    params: List[Any] = []

    if search:
        conditions.append("(name ILIKE %s OR description ILIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])

    if agency:
        conditions.append("agency ILIKE %s")
        params.append(f"%{agency}%")

    if domain:
        conditions.append("domain_tags::text ILIKE %s")
        params.append(f"%{domain}%")

    if min_quality is not None:
        conditions.append("data_quality_score >= %s")
        params.append(min_quality)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    allowed_sorts = {"data_quality_score", "name", "agency", "bd_score", "total_contract_value", "created_at"}
    if sort_by not in allowed_sorts:
        sort_by = "data_quality_score"
    direction = "DESC" if sort_dir.lower() == "desc" else "ASC"

    with get_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) as total FROM programs {where}", params)
        total = cur.fetchone()["total"]

        cur.execute(
            f"""SELECT id, name, agency, branch, primes, value, clearance,
                       contract_number, pop_start, pop_end, location, description,
                       bd_score, recompete_date, incumbent, set_aside,
                       typical_roles, priority_level, total_contract_value,
                       prime_contractor_consolidated, domain_tags,
                       data_quality_score, created_at
                FROM programs {where}
                ORDER BY {sort_by} {direction} NULLS LAST
                LIMIT %s OFFSET %s""",
            params + [limit, offset],
        )
        rows = [dict(r) for r in cur.fetchall()]

    for r in rows:
        r["id"] = str(r["id"])
        if r.get("domain_tags") and isinstance(r["domain_tags"], str):
            try:
                r["domain_tags"] = json.loads(r["domain_tags"])
            except (json.JSONDecodeError, TypeError):
                pass

    return rows, total


def get_jobs(
    limit: int = 500,
    offset: int = 0,
    search: Optional[str] = None,
    company: Optional[str] = None,
    sort_by: str = "bd_score",
    sort_dir: str = "desc",
) -> Tuple[List[Dict], int]:
    """Get jobs with filtering and pagination."""
    conditions = []
    params: List[Any] = []

    if search:
        conditions.append("(title ILIKE %s OR company ILIKE %s OR program_name ILIKE %s)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    if company:
        conditions.append("company ILIKE %s")
        params.append(f"%{company}%")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    allowed_sorts = {"bd_score", "title", "company", "created_at"}
    if sort_by not in allowed_sorts:
        sort_by = "bd_score"
    direction = "DESC" if sort_dir.lower() == "desc" else "ASC"

    with get_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) as total FROM jobs {where}", params)
        total = cur.fetchone()["total"]

        cur.execute(
            f"""SELECT id, title, company, location, description, clearance,
                       pay_rate, bill_rate, skills, bd_score, status, source,
                       bullhorn_job_id, program_name, confidence_score,
                       category, employment_type, created_at
                FROM jobs {where}
                ORDER BY {sort_by} {direction} NULLS LAST
                LIMIT %s OFFSET %s""",
            params + [limit, offset],
        )
        rows = [dict(r) for r in cur.fetchall()]

    for r in rows:
        r["id"] = str(r["id"])

    return rows, total


def get_companies(
    limit: int = 500,
    offset: int = 0,
    search: Optional[str] = None,
) -> Tuple[List[Dict], int]:
    """Get companies."""
    conditions = []
    params: List[Any] = []

    if search:
        conditions.append("name ILIKE %s")
        params.append(f"%{search}%")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    with get_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) as total FROM companies {where}", params)
        total = cur.fetchone()["total"]

        cur.execute(
            f"""SELECT id, name, uei, cage_code, company_type, relationship_tier,
                       usaspending_total_obligated, data_quality_score, created_at
                FROM companies {where}
                ORDER BY usaspending_total_obligated DESC NULLS LAST
                LIMIT %s OFFSET %s""",
            params + [limit, offset],
        )
        rows = [dict(r) for r in cur.fetchall()]

    for r in rows:
        r["id"] = str(r["id"])

    return rows, total


def get_graph_data(
    limit: int = 800,
    node_types: Optional[List[str]] = None,
    domain_filter: Optional[str] = None,
    min_quality: Optional[float] = None,
) -> Dict:
    """Get graph nodes and edges for V6 Graph Explorer."""
    if node_types is None:
        node_types = ["contact", "program", "contractor", "job"]

    nodes = []
    edges = []

    with get_cursor() as cur:
        # Contact nodes
        if "contact" in node_types:
            conditions = ["1=1"]
            params: List[Any] = []
            if min_quality:
                conditions.append("data_quality_score >= %s")
                params.append(min_quality)

            cur.execute(
                f"""SELECT id, first_name || ' ' || last_name as name,
                           'contact' as type, company, bd_score, priority,
                           hierarchy_tier as tier, data_quality_score,
                           associated_programs, clearance
                    FROM contacts
                    WHERE {' AND '.join(conditions)}
                    AND (first_name != '' OR last_name != '')
                    ORDER BY bd_score DESC NULLS LAST
                    LIMIT %s""",
                params + [limit // 3],
            )
            for r in cur.fetchall():
                r = dict(r)
                r["id"] = f"contact_{r['id']}"
                nodes.append(r)

        # Program nodes
        if "program" in node_types:
            conditions = ["name != ''"]
            params = []
            if domain_filter:
                conditions.append("domain_tags::text ILIKE %s")
                params.append(f"%{domain_filter}%")
            if min_quality:
                conditions.append("data_quality_score >= %s")
                params.append(min_quality)

            cur.execute(
                f"""SELECT id, name, 'program' as type, agency, bd_score,
                           priority_level as priority, domain_tags,
                           data_quality_score, total_contract_value,
                           prime_contractor_consolidated as prime
                    FROM programs
                    WHERE {' AND '.join(conditions)}
                    ORDER BY data_quality_score DESC NULLS LAST
                    LIMIT %s""",
                params + [limit // 3],
            )
            for r in cur.fetchall():
                r = dict(r)
                r["id"] = f"program_{r['id']}"
                if r.get("domain_tags") and isinstance(r["domain_tags"], str):
                    try:
                        r["domain_tags"] = json.loads(r["domain_tags"])
                    except (json.JSONDecodeError, TypeError):
                        r["domain_tags"] = []
                nodes.append(r)

        # Contractor/Company nodes
        if "contractor" in node_types:
            cur.execute(
                """SELECT id, name, 'contractor' as type, company_type,
                          relationship_tier, usaspending_total_obligated,
                          data_quality_score
                   FROM companies
                   WHERE name != ''
                   ORDER BY usaspending_total_obligated DESC NULLS LAST
                   LIMIT %s""",
                [limit // 6],
            )
            for r in cur.fetchall():
                r = dict(r)
                r["id"] = f"contractor_{r['id']}"
                nodes.append(r)

        # Job nodes
        if "job" in node_types:
            cur.execute(
                """SELECT id, title as name, 'job' as type, company, location,
                          clearance, bd_score, program_name
                   FROM jobs
                   WHERE title != ''
                   ORDER BY bd_score DESC NULLS LAST
                   LIMIT %s""",
                [limit // 6],
            )
            for r in cur.fetchall():
                r = dict(r)
                r["id"] = f"job_{r['id']}"
                nodes.append(r)

        # Build node ID set for edge filtering
        node_ids = {n["id"] for n in nodes}
        raw_contact_ids = {n["id"].replace("contact_", "") for n in nodes if n["id"].startswith("contact_")}
        raw_program_ids = {n["id"].replace("program_", "") for n in nodes if n["id"].startswith("program_")}
        raw_company_ids = {n["id"].replace("contractor_", "") for n in nodes if n["id"].startswith("contractor_")}

        # Edges from program_contacts
        if raw_program_ids and raw_contact_ids:
            cur.execute(
                """SELECT program_id, contact_id, relationship_type
                   FROM program_contacts
                   WHERE program_id = ANY(%s::uuid[]) AND contact_id = ANY(%s::uuid[])""",
                [list(raw_program_ids), list(raw_contact_ids)],
            )
            for r in cur.fetchall():
                edges.append({
                    "source": f"program_{r['program_id']}",
                    "target": f"contact_{r['contact_id']}",
                    "type": r["relationship_type"] or "WORKS_ON",
                })

        # Edges from program_companies
        if raw_program_ids and raw_company_ids:
            cur.execute(
                """SELECT program_id, company_id, role
                   FROM program_companies
                   WHERE program_id = ANY(%s::uuid[]) AND company_id = ANY(%s::uuid[])""",
                [list(raw_program_ids), list(raw_company_ids)],
            )
            for r in cur.fetchall():
                edges.append({
                    "source": f"contractor_{r['company_id']}",
                    "target": f"program_{r['program_id']}",
                    "type": "PRIMES_ON" if r["role"] == "prime" else "SUBS_ON",
                })

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "source": "supabase",
    }


def get_stats() -> Dict:
    """Get collection statistics."""
    with get_cursor() as cur:
        stats = {}
        for table in ["contacts", "programs", "companies", "jobs", "activities",
                       "documents", "contracts", "placements", "past_performance",
                       "bd_scoring", "task_orders", "timelines",
                       "program_contacts", "program_companies"]:
            cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            stats[table] = cur.fetchone()["cnt"]
    return stats


def get_domain_tags() -> List[Dict]:
    """Get domain tag summary for filter dropdowns."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT tag, COUNT(*) as count
            FROM programs, jsonb_array_elements_text(domain_tags) as tag
            WHERE domain_tags IS NOT NULL AND domain_tags != '[]'::jsonb
            GROUP BY tag
            ORDER BY count DESC
        """)
        return [dict(r) for r in cur.fetchall()]


def get_quality_stats() -> Dict:
    """Get data quality score distribution."""
    with get_cursor() as cur:
        result = {"overall": {}, "by_type": {}}

        # Overall
        cur.execute("""
            SELECT AVG(data_quality_score) as mean,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY data_quality_score) as median,
                   COUNT(*) as total,
                   COUNT(CASE WHEN data_quality_score IS NOT NULL THEN 1 END) as scored
            FROM (
                SELECT data_quality_score FROM contacts WHERE data_quality_score IS NOT NULL
                UNION ALL
                SELECT data_quality_score FROM programs WHERE data_quality_score IS NOT NULL
                UNION ALL
                SELECT data_quality_score FROM companies WHERE data_quality_score IS NOT NULL
            ) combined
        """)
        row = dict(cur.fetchone())
        result["overall"] = {
            "mean": round(float(row["mean"] or 0), 1),
            "median": round(float(row["median"] or 0), 1),
            "total_entities": row["total"],
            "scored_entities": row["scored"],
        }

        # Histogram
        cur.execute("""
            SELECT
                COUNT(CASE WHEN data_quality_score < 20 THEN 1 END) as "0-20",
                COUNT(CASE WHEN data_quality_score >= 20 AND data_quality_score < 40 THEN 1 END) as "20-40",
                COUNT(CASE WHEN data_quality_score >= 40 AND data_quality_score < 60 THEN 1 END) as "40-60",
                COUNT(CASE WHEN data_quality_score >= 60 AND data_quality_score < 80 THEN 1 END) as "60-80",
                COUNT(CASE WHEN data_quality_score >= 80 THEN 1 END) as "80-100"
            FROM (
                SELECT data_quality_score FROM contacts WHERE data_quality_score IS NOT NULL
                UNION ALL
                SELECT data_quality_score FROM programs WHERE data_quality_score IS NOT NULL
                UNION ALL
                SELECT data_quality_score FROM companies WHERE data_quality_score IS NOT NULL
            ) combined
        """)
        result["histogram"] = dict(cur.fetchone())

        # Per type
        for table, label in [("contacts", "Contact"), ("programs", "Program"), ("companies", "Contractor")]:
            cur.execute(f"""
                SELECT AVG(data_quality_score) as mean,
                       COUNT(*) as total,
                       COUNT(CASE WHEN data_quality_score IS NOT NULL THEN 1 END) as scored
                FROM {table}
            """)
            row = dict(cur.fetchone())
            result["by_type"][label] = {
                "mean": round(float(row["mean"] or 0), 1),
                "total": row["total"],
                "scored": row["scored"],
            }

        return result


def get_competition_graph(program_filter: Optional[str] = None, limit: int = 200) -> Dict:
    """Get competition network: contractors competing on same programs."""
    with get_cursor() as cur:
        conditions = []
        params: List[Any] = []

        if program_filter:
            conditions.append("p.name ILIKE %s")
            params.append(f"%{program_filter}%")

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        # Get contractors with shared programs
        cur.execute(f"""
            WITH program_contractors AS (
                SELECT pc.program_id, pc.company_id, c.name as company_name,
                       p.name as program_name, pc.role
                FROM program_companies pc
                JOIN companies c ON c.id = pc.company_id
                JOIN programs p ON p.id = pc.program_id
                {where}
            ),
            competition AS (
                SELECT a.company_id as co1, b.company_id as co2,
                       a.company_name as name1, b.company_name as name2,
                       COUNT(DISTINCT a.program_id) as shared_programs
                FROM program_contractors a
                JOIN program_contractors b ON a.program_id = b.program_id
                    AND a.company_id < b.company_id
                GROUP BY a.company_id, b.company_id, a.company_name, b.company_name
                HAVING COUNT(DISTINCT a.program_id) >= 2
            )
            SELECT * FROM competition
            ORDER BY shared_programs DESC
            LIMIT %s
        """, params + [limit])

        edges = []
        contractor_ids = set()
        for r in cur.fetchall():
            r = dict(r)
            edges.append({
                "source": f"contractor_{r['co1']}",
                "target": f"contractor_{r['co2']}",
                "type": "COMPETES_WITH",
                "shared_programs": r["shared_programs"],
            })
            contractor_ids.add(str(r["co1"]))
            contractor_ids.add(str(r["co2"]))

        # Get contractor nodes
        nodes = []
        if contractor_ids:
            cur.execute(
                """SELECT id, name, company_type, relationship_tier,
                          usaspending_total_obligated, data_quality_score
                   FROM companies WHERE id = ANY(%s::uuid[])""",
                [list(contractor_ids)],
            )
            for r in cur.fetchall():
                r = dict(r)
                r["id"] = f"contractor_{r['id']}"
                r["type"] = "contractor"
                nodes.append(r)

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "source": "supabase",
        }
