"""
Companies ETL Loader
Sources: Contractors Database.csv, Bullhorn prime_contractors,
         MASTER_PRIMES_ENRICHED.csv, PRIMES_FINAL.csv, primes_usaspending_enriched.csv,
         COMBINED_INTELLIGENCE_REPORT.csv
"""

import csv
import sqlite3
from pathlib import Path

from ..utils import (
    Deduplicator,
    generate_id,
    normalize_company_name,
    parse_currency,
    safe_float,
    safe_int,
    safe_str,
    standardize_date,
)

BASE_DIR = Path(__file__).parent.parent.parent.parent


def load_companies(conn: sqlite3.Connection, verbose: bool = False) -> int:
    """Load companies from all sources."""
    cursor = conn.cursor()
    dedup = Deduplicator()
    loaded = 0

    # Source 1: Contractors Database.csv (richest per-company data)
    contractors_csv = BASE_DIR / "data" / "raw" / "notion_exports" / "contractors" / "Contractors_Database.csv"
    if contractors_csv.exists():
        loaded += _load_contractors_db(cursor, contractors_csv, dedup, verbose)

    # Source 2: Bullhorn prime_contractors (41 rows)
    bullhorn_db = BASE_DIR / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"
    if bullhorn_db.exists():
        loaded += _load_bullhorn_primes(cursor, bullhorn_db, dedup, verbose)

    # Source 3: MASTER_PRIMES_ENRICHED.csv (6,090 rows - largest source)
    primes_enriched = BASE_DIR / "data" / "enriched" / "primes" / "MASTER_PRIMES_ENRICHED.csv"
    if primes_enriched.exists():
        loaded += _load_primes_enriched(cursor, primes_enriched, dedup, verbose)

    # Source 4: primes_usaspending_enriched.csv (enrichment)
    usaspending = BASE_DIR / "data" / "enriched" / "primes" / "primes_usaspending_enriched.csv"
    if usaspending.exists():
        _enrich_usaspending(cursor, usaspending, verbose)

    # Source 5: COMBINED_INTELLIGENCE_REPORT.csv (relationship tier enrichment)
    intel_report = BASE_DIR / "data" / "enriched" / "intelligence" / "COMBINED_INTELLIGENCE_REPORT.csv"
    if intel_report.exists():
        _enrich_intel_report(cursor, intel_report, verbose)

    conn.commit()
    if verbose:
        print(f"  Companies loaded: {loaded} ({dedup.stats})")
    return loaded


def _load_contractors_db(cursor, csv_path: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load from Contractors Database.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = safe_str(row.get("Company Name") or row.get("\ufeffCompany Name"))
            if not name:
                continue
            normalized = normalize_company_name(name)
            if not dedup.is_new(normalized.lower()):
                continue

            cid = generate_id(normalized)
            cursor.execute("""
                INSERT OR REPLACE INTO companies (
                    id, name, normalized_name, company_type,
                    sam_registration, clearance_facility,
                    employee_count, annual_revenue,
                    linkedin_url, github_org,
                    key_capabilities, recent_wins,
                    contract_vehicles, cage_code, duns_number,
                    federal_programs_prime, federal_programs_sub,
                    past_performance, subcontractor_to,
                    source_files
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cid, name, normalized,
                safe_str(row.get("Company Type")),
                safe_str(row.get("SAM Registration")),
                safe_str(row.get("Clearance Facility")),
                safe_int(row.get("Employee Count")),
                parse_currency(row.get("Annual Revenue")),
                safe_str(row.get("LinkedIn Company URL")),
                safe_str(row.get("GitHub Organization")),
                safe_str(row.get("Key Capabilities")),
                safe_str(row.get("Recent Wins")),
                safe_str(row.get("Contract Vehicles")),
                safe_str(row.get("CAGE Code")),
                safe_str(row.get("DUNS Number")),
                safe_str(row.get("Federal Programs (Prime)")),
                safe_str(row.get("Federal Programs (Sub)")),
                safe_str(row.get("Past Performance")),
                safe_str(row.get("Subcontractor To")),
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    Contractors Database: {count} companies")
    return count


def _load_bullhorn_primes(cursor, db_path: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load from Bullhorn prime_contractors table."""
    count = 0
    bh_conn = sqlite3.connect(str(db_path))
    bh_conn.row_factory = sqlite3.Row
    bh_cursor = bh_conn.cursor()
    bh_cursor.execute("SELECT * FROM prime_contractors")

    for row in bh_cursor.fetchall():
        name = row["name"]
        if not name:
            continue
        normalized = normalize_company_name(name)
        if not dedup.is_new(normalized.lower()):
            # Enrich existing
            cursor.execute("""
                UPDATE companies SET
                    cage_code = COALESCE(cage_code, ?),
                    duns_number = COALESCE(duns_number, ?),
                    website = COALESCE(website, ?),
                    headquarters = COALESCE(headquarters, ?),
                    naics_codes = COALESCE(naics_codes, ?),
                    aliases = COALESCE(aliases, ?)
                WHERE normalized_name = ?
            """, (
                row["cage_code"] if "cage_code" in row.keys() else None,
                row["duns_number"] if "duns_number" in row.keys() else None,
                row["website"] if "website" in row.keys() else None,
                row["headquarters"] if "headquarters" in row.keys() else None,
                row["naics_codes"] if "naics_codes" in row.keys() else None,
                row["aliases"] if "aliases" in row.keys() else None,
                normalized,
            ))
            continue

        cid = generate_id(normalized)
        cursor.execute("""
            INSERT OR IGNORE INTO companies (
                id, name, normalized_name, aliases,
                cage_code, duns_number, website, headquarters,
                employee_count, annual_revenue, naics_codes,
                source_files
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'bullhorn_master.db')
        """, (
            cid, name, normalized,
            row["aliases"] if "aliases" in row.keys() else None,
            row["cage_code"] if "cage_code" in row.keys() else None,
            row["duns_number"] if "duns_number" in row.keys() else None,
            row["website"] if "website" in row.keys() else None,
            row["headquarters"] if "headquarters" in row.keys() else None,
            row["employee_count"] if "employee_count" in row.keys() else None,
            safe_float(row["annual_revenue"] if "annual_revenue" in row.keys() else None),
            row["naics_codes"] if "naics_codes" in row.keys() else None,
        ))
        count += 1

    bh_conn.close()
    if verbose:
        print(f"    Bullhorn primes: {count} new")
    return count


def _load_primes_enriched(cursor, csv_path: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load from MASTER_PRIMES_ENRICHED.csv (6,090 rows)."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = safe_str(row.get("prime_name"))
            if not name:
                continue
            normalized = normalize_company_name(name)
            if not dedup.is_new(normalized.lower()):
                # Enrich
                cursor.execute("""
                    UPDATE companies SET
                        note_count = COALESCE(note_count, ?),
                        programs = COALESCE(programs, ?),
                        tech_stack = COALESCE(tech_stack, ?),
                        contract_count = COALESCE(contract_count, ?),
                        total_award_amount = COALESCE(total_award_amount, ?),
                        recent_contract_count = COALESCE(recent_contract_count, ?),
                        recent_contract_value = COALESCE(recent_contract_value, ?),
                        first_seen = COALESCE(first_seen, ?),
                        last_seen = COALESCE(last_seen, ?)
                    WHERE normalized_name = ?
                """, (
                    safe_int(row.get("note_count")),
                    safe_str(row.get("programs")),
                    safe_str(row.get("tech_stack")),
                    safe_int(row.get("contract_count")),
                    parse_currency(row.get("total_award_amount")),
                    safe_int(row.get("recent_contract_count")),
                    parse_currency(row.get("recent_contract_value")),
                    safe_str(row.get("first_seen")),
                    safe_str(row.get("last_seen")),
                    normalized,
                ))
                continue

            cid = generate_id(normalized)
            cursor.execute("""
                INSERT OR IGNORE INTO companies (
                    id, name, normalized_name, aliases,
                    note_count, programs, tech_stack,
                    contract_count, total_award_amount,
                    recent_contract_count, recent_contract_value,
                    first_seen, last_seen,
                    source_files
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cid, name, normalized,
                safe_str(row.get("aliases")),
                safe_int(row.get("note_count")),
                safe_str(row.get("programs")),
                safe_str(row.get("tech_stack")),
                safe_int(row.get("contract_count")),
                parse_currency(row.get("total_award_amount")),
                safe_int(row.get("recent_contract_count")),
                parse_currency(row.get("recent_contract_value")),
                safe_str(row.get("first_seen")),
                safe_str(row.get("last_seen")),
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    Primes Enriched: {count} new companies")
    return count


def _enrich_usaspending(cursor, csv_path: Path, verbose: bool):
    """Enrich companies with USASpending data."""
    updated = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = safe_str(row.get("prime_name"))
            if not name:
                continue
            normalized = normalize_company_name(name)
            cursor.execute("""
                UPDATE companies SET
                    usaspending_contract_count = ?,
                    usaspending_total_obligated = ?,
                    usaspending_agencies = ?
                WHERE normalized_name = ?
            """, (
                safe_int(row.get("usaspending_contract_count")),
                parse_currency(row.get("usaspending_total_obligated")),
                safe_str(row.get("usaspending_agencies")),
                normalized,
            ))
            if cursor.rowcount > 0:
                updated += 1
    if verbose:
        print(f"    USASpending enrichment: {updated} updated")


def _enrich_intel_report(cursor, csv_path: Path, verbose: bool):
    """Enrich with COMBINED_INTELLIGENCE_REPORT relationship tier."""
    updated = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = safe_str(row.get("prime_name"))
            if not name:
                continue
            normalized = normalize_company_name(name)
            cursor.execute("""
                UPDATE companies SET
                    relationship_tier = ?,
                    bullhorn_mentions = ?,
                    bullhorn_contacts = ?,
                    bullhorn_programs = ?
                WHERE normalized_name = ?
            """, (
                safe_str(row.get("relationship_tier")),
                safe_int(row.get("bullhorn_mentions")),
                safe_int(row.get("bullhorn_contacts")),
                safe_str(row.get("bullhorn_programs")),
                normalized,
            ))
            if cursor.rowcount > 0:
                updated += 1
    if verbose:
        print(f"    Intel Report enrichment: {updated} updated")
