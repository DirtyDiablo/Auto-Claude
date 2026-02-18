"""
Programs ETL Loader
Primary: Federal Programs MASTER ENRICHED.csv (388 rows, 89+ cols)
Enrichment: MASTER_PROGRAMS_ENRICHED.csv, PROGRAM_INTELLIGENCE_DETAILED.csv, Bullhorn programs
"""

import csv
import sqlite3
from pathlib import Path

from ..utils import (
    Deduplicator,
    generate_id,
    json_encode_array,
    normalize_name,
    parse_currency,
    safe_float,
    safe_int,
    safe_str,
    standardize_date,
)

BASE_DIR = Path(__file__).parent.parent.parent.parent


def load_programs(conn: sqlite3.Connection, verbose: bool = False) -> int:
    """Load programs from all sources into the programs table."""
    cursor = conn.cursor()
    dedup = Deduplicator()
    loaded = 0

    # Source 1: Federal Programs MASTER ENRICHED (primary, richest data)
    master_csv = BASE_DIR / "Engine2_ProgramMapping" / "data" / "Federal Programs MASTER ENRICHED.csv"
    if master_csv.exists():
        loaded += _load_master_enriched(cursor, master_csv, dedup, verbose)

    # Source 2: MASTER_PROGRAMS_ENRICHED (enrichment - more programs, lighter data)
    programs_enriched = BASE_DIR / "data" / "enriched" / "programs" / "MASTER_PROGRAMS_ENRICHED.csv"
    if programs_enriched.exists():
        loaded += _load_programs_enriched(cursor, programs_enriched, dedup, verbose)

    # Source 3: PROGRAM_INTELLIGENCE_DETAILED (enrichment)
    intel_csv = BASE_DIR / "data" / "enriched" / "intelligence" / "PROGRAM_INTELLIGENCE_DETAILED.csv"
    if intel_csv.exists():
        _enrich_from_intel(cursor, intel_csv, verbose)

    # Source 4: Bullhorn programs table (4 rows)
    bullhorn_db = BASE_DIR / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"
    if bullhorn_db.exists():
        loaded += _load_bullhorn_programs(cursor, bullhorn_db, dedup, verbose)

    conn.commit()
    if verbose:
        print(f"  Programs loaded: {loaded} ({dedup.stats})")
    return loaded


def _load_master_enriched(cursor, csv_path: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load from Federal Programs MASTER ENRICHED.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = safe_str(row.get("Program Name"))
            if not name:
                continue
            acronym = safe_str(row.get("Acronym"))
            if not dedup.is_new(normalize_name(name), acronym):
                continue

            pid = generate_id(name, row.get("Agency Owner", ""))
            cursor.execute("""
                INSERT OR REPLACE INTO programs (
                    id, program_name, acronym, agency_owner, program_type,
                    priority_level, confidence_level, pts_involvement,
                    contract_number, tango_piid, parent_piid,
                    contract_value, contract_value_consolidated, total_contract_value,
                    base_contract_value_fpds, base_options_value_fpds,
                    obligated, subawards_total, subawards_count,
                    prime_contractor, prime_contractor_1, prime_contractor_consolidated,
                    recipient_name, recipient_uei,
                    key_subcontractors, known_subcontractors,
                    period_of_performance,
                    pop_start, pop_end,
                    pop_start_consolidated, pop_end_consolidated,
                    ultimate_completion, ultimate_completion_consolidated,
                    recompete_date,
                    contract_signed_date_fpds, contract_effective_date_fpds,
                    current_completion_date_fpds, ultimate_completion_date_fpds,
                    key_locations, performance_location_tango, performance_location_fpds,
                    pop_city, pop_state, pop_zip, pop_country,
                    naics_code_consolidated, naics_code, fpds_naics_code, naics_description,
                    psc_code_consolidated, psc_code, fpds_psc_code, psc_description,
                    set_aside,
                    technical_stack, tech_stack_basic,
                    keywords_signals, functional_areas, typical_roles, job_titles,
                    labor_rate_min, labor_rate_max, labor_rate_average,
                    education_requirement, experience_requirement, annual_salary_range,
                    calc_api_status,
                    contract_vehicle_used, contract_vehicle_type,
                    awarding_office, awarding_agency, funding_office,
                    cor_cotr, program_manager,
                    clearance_requirements, security_requirements,
                    match_confidence, match_score, incumbent_score,
                    source_evidence, notes, pain_points,
                    related_jobs, tango_description, parent_description, budget,
                    source_files
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                pid, name, acronym,
                safe_str(row.get("Agency Owner")),
                safe_str(row.get("Program Type")),
                safe_str(row.get("Priority Level")),
                safe_str(row.get("Confidence Level")),
                safe_str(row.get("PTS Involvement")),
                safe_str(row.get("Contract Number")),
                safe_str(row.get("tango_piid")),
                safe_str(row.get("parent_piid")),
                safe_str(row.get("Contract Value")),
                parse_currency(row.get("Contract Value (Consolidated)")),
                parse_currency(row.get("total_contract_value")),
                parse_currency(row.get("Base Contract Value (FPDS)")),
                parse_currency(row.get("Base + Options Value (FPDS)")),
                parse_currency(row.get("obligated")),
                parse_currency(row.get("subawards_total")),
                safe_int(row.get("subawards_count")),
                safe_str(row.get("Prime Contractor")),
                safe_str(row.get("Prime Contractor 1")),
                safe_str(row.get("Prime Contractor (Consolidated)")),
                safe_str(row.get("recipient_name")),
                safe_str(row.get("recipient_uei")),
                safe_str(row.get("Key Subcontractors")),
                safe_str(row.get("Known Subcontractors")),
                safe_str(row.get("Period of Performance")),
                standardize_date(row.get("PoP Start")),
                standardize_date(row.get("PoP End")),
                standardize_date(row.get("PoP Start (Consolidated)")),
                standardize_date(row.get("PoP End (Consolidated)")),
                standardize_date(row.get("ultimate_completion")),
                standardize_date(row.get("Ultimate Completion (Consolidated)")),
                standardize_date(row.get("Recompete Date")),
                standardize_date(row.get("Contract Signed Date (FPDS)")),
                standardize_date(row.get("Contract Effective Date (FPDS)")),
                standardize_date(row.get("Current Completion Date (FPDS)")),
                standardize_date(row.get("Ultimate Completion Date (FPDS)")),
                safe_str(row.get("Key Locations")),
                safe_str(row.get("Performance Location (TANGO)")),
                safe_str(row.get("Performance Location (FPDS)")),
                safe_str(row.get("pop_city")),
                safe_str(row.get("pop_state")),
                safe_str(row.get("pop_zip")),
                safe_str(row.get("pop_country")),
                safe_str(row.get("NAICS Code (Consolidated)")),
                safe_str(row.get("naics_code")),
                safe_str(row.get("FPDS NAICS Code")),
                safe_str(row.get("NAICS Description")),
                safe_str(row.get("PSC Code (Consolidated)")),
                safe_str(row.get("psc_code")),
                safe_str(row.get("FPDS PSC Code")),
                safe_str(row.get("PSC Description")),
                safe_str(row.get("set_aside")),
                safe_str(row.get("Technical Stack")),
                safe_str(row.get("Tech Stack (Basic)")),
                safe_str(row.get("Keywords/Signals")),
                safe_str(row.get("Functional Areas")),
                safe_str(row.get("Typical Roles")),
                safe_str(row.get("Job Titles")),
                safe_float(row.get("Labor Rate Min")),
                safe_float(row.get("Labor Rate Max")),
                safe_float(row.get("Labor Rate Average")),
                safe_str(row.get("Education Requirement")),
                safe_str(row.get("Experience Requirement")),
                safe_str(row.get("Annual Salary Range")),
                safe_str(row.get("CALC API Status")),
                safe_str(row.get("Contract Vehicle Used")),
                safe_str(row.get("Contract Vehicle/Type")),
                safe_str(row.get("awarding_office")),
                safe_str(row.get("awarding_agency")),
                safe_str(row.get("funding_office")),
                safe_str(row.get("COR/COTR")),
                safe_str(row.get("Program Manager")),
                safe_str(row.get("Clearance Requirements")),
                safe_str(row.get("Security Requirements")),
                safe_str(row.get("Match Confidence")),
                safe_float(row.get("Match Score")),
                safe_float(row.get("Incumbent Score")),
                safe_str(row.get("Source Evidence")),
                safe_str(row.get("Notes")),
                safe_str(row.get("Pain Points")),
                safe_str(row.get("Related Jobs")),
                safe_str(row.get("tango_description")),
                safe_str(row.get("parent_description")),
                safe_str(row.get("Budget")),
                str(csv_path.name),
            ))
            count += 1

    if verbose:
        print(f"    Master Enriched CSV: {count} programs")
    return count


def _load_programs_enriched(cursor, csv_path: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load from MASTER_PROGRAMS_ENRICHED.csv (enrichment source)."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = safe_str(row.get("program_name"))
            if not name:
                continue
            if not dedup.is_new(normalize_name(name)):
                continue

            pid = generate_id(name, "")
            cursor.execute("""
                INSERT OR IGNORE INTO programs (
                    id, program_name, prime_contractor,
                    description, technical_stack,
                    mention_count, piid_count, total_award_amount,
                    top_recipients, source_files
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pid, name,
                safe_str(row.get("prime_name")),
                safe_str(row.get("description")),
                safe_str(row.get("tech_stack")),
                safe_int(row.get("mention_count")),
                safe_int(row.get("piid_count")),
                parse_currency(row.get("total_award_amount")),
                safe_str(row.get("top_recipients")),
                str(csv_path.name),
            ))
            count += 1

    if verbose:
        print(f"    Programs Enriched CSV: {count} new programs")
    return count


def _enrich_from_intel(cursor, csv_path: Path, verbose: bool):
    """Enrich existing programs with PROGRAM_INTELLIGENCE_DETAILED data."""
    updated = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = safe_str(row.get("program_name"))
            if not name:
                continue
            cursor.execute("""
                UPDATE programs SET
                    description = COALESCE(description, ?),
                    technology_areas = ?,
                    roles_needed = ?,
                    parent_organization = COALESCE(parent_organization, ?)
                WHERE program_name = ? OR acronym = ?
            """, (
                safe_str(row.get("aggregated_summary")),
                safe_str(row.get("technology_areas")),
                safe_str(row.get("roles_needed")),
                safe_str(row.get("parent_organization")),
                name,
                safe_str(row.get("program_name")),
            ))
            if cursor.rowcount > 0:
                updated += 1
    if verbose:
        print(f"    Program Intel enrichment: {updated} updated")


def _load_bullhorn_programs(cursor, db_path: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load programs from Bullhorn database."""
    count = 0
    bh_conn = sqlite3.connect(str(db_path))
    bh_conn.row_factory = sqlite3.Row
    bh_cursor = bh_conn.cursor()

    bh_cursor.execute("SELECT * FROM programs")
    for row in bh_cursor.fetchall():
        name = row["name"] if "name" in row.keys() else None
        if not name:
            continue
        if not dedup.is_new(normalize_name(name)):
            # Enrich existing record
            cursor.execute("""
                UPDATE programs SET
                    prime_contractor = COALESCE(prime_contractor, ?),
                    contract_number = COALESCE(contract_number, ?)
                WHERE program_name = ? OR acronym = ?
            """, (
                row["prime_contractor_name"] if "prime_contractor_name" in row.keys() else None,
                row["contract_number"] if "contract_number" in row.keys() else None,
                name, row["acronym"] if "acronym" in row.keys() else None,
            ))
            continue

        pid = generate_id(name, "bullhorn")
        cursor.execute("""
            INSERT OR IGNORE INTO programs (
                id, program_name, acronym, prime_contractor,
                contract_number, pop_start, pop_end,
                key_locations, description, source_files
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'bullhorn_master.db')
        """, (
            pid, name,
            row["acronym"] if "acronym" in row.keys() else None,
            row["prime_contractor_name"] if "prime_contractor_name" in row.keys() else None,
            row["contract_number"] if "contract_number" in row.keys() else None,
            standardize_date(row["start_date"] if "start_date" in row.keys() else None),
            standardize_date(row["end_date"] if "end_date" in row.keys() else None),
            row["location"] if "location" in row.keys() else None,
            row["description"] if "description" in row.keys() else None,
        ))
        count += 1

    bh_conn.close()
    if verbose:
        print(f"    Bullhorn programs: {count} new")
    return count
