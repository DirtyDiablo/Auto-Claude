"""
Jobs ETL Loader
Primary: all_jobs_fully_enriched.json (243 jobs)
Secondary: Bullhorn jobs table (135), JOBS_ENRICHED.csv, JOBS_INTELLIGENCE_MAPPED.csv
"""

import csv
import json
import sqlite3
from pathlib import Path

from ..utils import (
    Deduplicator,
    build_program_lookup,
    fuzzy_program_match,
    generate_id,
    json_encode_array,
    parse_currency,
    safe_float,
    safe_str,
    standardize_date,
)

BASE_DIR = Path(__file__).parent.parent.parent.parent


def load_jobs(conn: sqlite3.Connection, verbose: bool = False) -> int:
    """Load jobs from all sources."""
    cursor = conn.cursor()
    dedup = Deduplicator()
    program_lookup = build_program_lookup(conn)
    loaded = 0

    # Source 1: all_jobs_fully_enriched.json (primary)
    enriched = BASE_DIR / "outputs" / "all_jobs_fully_enriched.json"
    if enriched.exists():
        loaded += _load_enriched_json(cursor, enriched, dedup, program_lookup, verbose)

    # Source 2: Bullhorn jobs table
    bullhorn_db = BASE_DIR / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"
    if bullhorn_db.exists():
        loaded += _load_bullhorn_jobs(cursor, bullhorn_db, dedup, program_lookup, verbose)

    # Source 3: JOBS_ENRICHED.csv
    jobs_csv = BASE_DIR / "data" / "enriched" / "jobs" / "JOBS_ENRICHED.csv"
    if jobs_csv.exists():
        _enrich_jobs_csv(cursor, jobs_csv, verbose)

    conn.commit()
    if verbose:
        print(f"  Jobs loaded: {loaded} ({dedup.stats})")
    return loaded


def _load_enriched_json(cursor, json_path: Path, dedup: Deduplicator,
                        program_lookup: dict, verbose: bool) -> int:
    """Load from all_jobs_fully_enriched.json."""
    count = 0
    with open(json_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    for job in jobs:
        job_num = safe_str(job.get("job_number"))
        title = safe_str(job.get("title"))
        company = safe_str(job.get("company"))
        if not title:
            continue

        dedup_key = job_num or f"{title}|{company}|{job.get('date_posted', '')}"
        if not dedup.is_new(dedup_key):
            continue

        # Try to match to a program
        matched_program = safe_str(job.get("prime")) or company
        program_id = fuzzy_program_match(matched_program, program_lookup)

        jid = generate_id(dedup_key)
        cursor.execute("""
            INSERT OR REPLACE INTO jobs (
                id, job_number, title, company, prime, location,
                date_posted, duration, employment_type, status,
                clearance, description,
                experience_years, skills, technologies,
                certifications_required, certifications_extra,
                subcontractors, task_order,
                hiring_leader, program_manager,
                pts_past_programs, pts_past_jobs,
                pts_past_contractors, pts_past_contacts,
                url, scraped_at,
                matched_program, matched_program_id,
                source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            jid, job_num, title, company,
            safe_str(job.get("prime")),
            safe_str(job.get("location")),
            standardize_date(job.get("date_posted")),
            safe_str(job.get("duration")),
            safe_str(job.get("employment_type")),
            safe_str(job.get("status")),
            safe_str(job.get("clearance")),
            safe_str(job.get("description")),
            safe_str(job.get("experience_years")),
            json_encode_array(job.get("skills")),
            json_encode_array(job.get("technologies")),
            json_encode_array(job.get("certifications_required")),
            json_encode_array(job.get("certifications_extra")),
            json_encode_array(job.get("subcontractors")),
            safe_str(job.get("task_order")),
            safe_str(job.get("hiring_leader")),
            safe_str(job.get("program_manager")),
            json_encode_array(job.get("pts_past_programs")),
            json_encode_array(job.get("pts_past_jobs")),
            json_encode_array(job.get("pts_past_contractors")),
            json_encode_array(job.get("pts_past_contacts")),
            safe_str(job.get("url")),
            safe_str(job.get("scraped_at")),
            matched_program,
            program_id,
            safe_str(job.get("source_file")) or "all_jobs_fully_enriched.json",
        ))
        count += 1

    if verbose:
        print(f"    all_jobs_fully_enriched.json: {count} jobs")
    return count


def _load_bullhorn_jobs(cursor, db_path: Path, dedup: Deduplicator,
                        program_lookup: dict, verbose: bool) -> int:
    """Load from Bullhorn jobs table."""
    count = 0
    bh_conn = sqlite3.connect(str(db_path))
    bh_conn.row_factory = sqlite3.Row
    bh_cursor = bh_conn.cursor()
    bh_cursor.execute("SELECT * FROM jobs")

    for row in bh_cursor.fetchall():
        keys = row.keys()
        job_num = row["job_number"] if "job_number" in keys else None
        title = row["title"] if "title" in keys else None
        if not title:
            continue

        company = row["client_corporation"] if "client_corporation" in keys else None
        dedup_key = job_num or f"{title}|{company}"
        if not dedup.is_new(dedup_key):
            continue

        jid = generate_id(dedup_key, "bullhorn")
        cursor.execute("""
            INSERT OR IGNORE INTO jobs (
                id, job_number, title, company, prime,
                location, employment_type, status,
                clearance, description,
                pay_rate, bill_rate, salary,
                owner, contact,
                date_posted,
                source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'bullhorn_master.db')
        """, (
            jid, job_num, title, company,
            row["prime_contractor"] if "prime_contractor" in keys else None,
            row["location"] if "location" in keys else None,
            row["employment_type"] if "employment_type" in keys else None,
            row["status"] if "status" in keys else None,
            row["clearance_required"] if "clearance_required" in keys else None,
            row["description"] if "description" in keys else None,
            safe_float(row["pay_rate"] if "pay_rate" in keys else None),
            safe_float(row["bill_rate"] if "bill_rate" in keys else None),
            safe_float(row["salary"] if "salary" in keys else None),
            row["owner"] if "owner" in keys else None,
            row["contact"] if "contact" in keys else None,
            standardize_date(row["date_added"] if "date_added" in keys else None),
        ))
        count += 1

    bh_conn.close()
    if verbose:
        print(f"    Bullhorn jobs: {count} new")
    return count


def _enrich_jobs_csv(cursor, csv_path: Path, verbose: bool):
    """Enrich from JOBS_ENRICHED.csv."""
    updated = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            job_num = safe_str(row.get("job_number"))
            if not job_num:
                continue
            cursor.execute("""
                UPDATE jobs SET
                    linked_prime = COALESCE(linked_prime, ?),
                    pay_rate = COALESCE(pay_rate, ?),
                    bill_rate = COALESCE(bill_rate, ?),
                    owner = COALESCE(owner, ?),
                    contact = COALESCE(contact, ?)
                WHERE job_number = ?
            """, (
                safe_str(row.get("linked_prime")),
                parse_currency(row.get("pay_rate")),
                parse_currency(row.get("client_bill_rate")),
                safe_str(row.get("owner")),
                safe_str(row.get("contact")),
                job_num,
            ))
            if cursor.rowcount > 0:
                updated += 1
    if verbose:
        print(f"    Jobs Enriched CSV: {updated} updated")
