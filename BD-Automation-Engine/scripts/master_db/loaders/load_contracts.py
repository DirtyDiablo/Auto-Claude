"""
Contracts ETL Loader
Sources: MASTER_CONTRACTS_COMBINED.csv, db1_dod_prime_contracts_100m.csv,
         FULL_PROGRAM_CONTRACTS.csv, phase1_tango_contracts.csv,
         PHASE3_ALL_PROGRAM_CONTRACTS.csv, PHASE5_RECENT_ACTIVE_CONTRACTS.csv
"""

import csv
import sqlite3
from pathlib import Path

from ..utils import (
    Deduplicator,
    build_company_lookup,
    build_program_lookup,
    fuzzy_program_match,
    generate_id,
    normalize_company_name,
    parse_currency,
    safe_int,
    safe_str,
    standardize_date,
)

BASE_DIR = Path(__file__).parent.parent.parent.parent


def load_contracts(conn: sqlite3.Connection, verbose: bool = False) -> int:
    """Load contracts from all sources."""
    cursor = conn.cursor()
    dedup = Deduplicator()
    program_lookup = build_program_lookup(conn)
    company_lookup = build_company_lookup(conn)
    loaded = 0

    # Source 1: phase1_tango_contracts.csv (highest quality, priority)
    tango = BASE_DIR / "data" / "from_data_scraper" / "phase1_tango_contracts.csv"
    if tango.exists():
        loaded += _load_csv(cursor, tango, "tango", dedup, program_lookup, company_lookup, verbose)

    # Source 2: MASTER_CONTRACTS_COMBINED.csv (2,282 rows)
    master = BASE_DIR / "data" / "from_data_scraper" / "MASTER_CONTRACTS_COMBINED.csv"
    if master.exists():
        loaded += _load_master_contracts(cursor, master, dedup, program_lookup, company_lookup, verbose)

    # Source 3: db1_dod_prime_contracts_100m.csv (1,932 rows)
    dod = BASE_DIR / "data" / "from_data_scraper" / "db1_dod_prime_contracts_100m.csv"
    if dod.exists():
        loaded += _load_dod_contracts(cursor, dod, dedup, program_lookup, company_lookup, verbose)

    # Source 4: FULL_PROGRAM_CONTRACTS.csv (1,510 rows)
    full = BASE_DIR / "data" / "from_data_scraper" / "FULL_PROGRAM_CONTRACTS.csv"
    if full.exists():
        loaded += _load_program_contracts(cursor, full, dedup, program_lookup, company_lookup, verbose)

    # Source 5: PHASE3_ALL_PROGRAM_CONTRACTS.csv
    phase3 = BASE_DIR / "data" / "from_data_scraper" / "PHASE3_ALL_PROGRAM_CONTRACTS.csv"
    if phase3.exists():
        loaded += _load_phase3_contracts(cursor, phase3, dedup, program_lookup, company_lookup, verbose)

    conn.commit()
    if verbose:
        print(f"  Contracts loaded: {loaded} ({dedup.stats})")
    return loaded


def _get_piid(row: dict) -> str:
    """Extract PIID from various column names."""
    return safe_str(row.get("piid")) or safe_str(row.get("contract_id")) or safe_str(row.get("award_id")) or ""


def _load_csv(cursor, csv_path: Path, source: str, dedup: Deduplicator,
              program_lookup: dict, company_lookup: dict, verbose: bool) -> int:
    """Load Tango contracts (richest data)."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            piid = _get_piid(row)
            if not piid:
                continue
            if not dedup.is_new(piid):
                continue

            recipient = safe_str(row.get("recipient_name")) or ""
            program_id = fuzzy_program_match(
                safe_str(row.get("prime_search")) or safe_str(row.get("program")),
                program_lookup
            )
            company_id = company_lookup.get(normalize_company_name(recipient).lower())

            cid = generate_id(piid, source)
            cursor.execute("""
                INSERT OR IGNORE INTO contracts (
                    id, piid, source, program_id, program_name,
                    recipient_name, recipient_uei, company_id,
                    award_amount, obligated,
                    base_and_exercised_options_value, total_contract_value,
                    description, awarding_agency, funding_agency,
                    naics_code, psc_code,
                    pop_start, pop_end, pop_ultimate,
                    pop_city, pop_state,
                    fiscal_year, idv_type, set_aside, award_type,
                    award_date, prime_search,
                    source_file
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cid, piid, source, program_id,
                safe_str(row.get("prime_search")),
                recipient, safe_str(row.get("recipient_uei")), company_id,
                parse_currency(row.get("obligated")),
                parse_currency(row.get("obligated")),
                parse_currency(row.get("base_and_exercised_options_value")),
                parse_currency(row.get("total_contract_value")),
                safe_str(row.get("description")),
                safe_str(row.get("awarding_agency")),
                safe_str(row.get("funding_agency")),
                safe_str(row.get("naics_code")),
                safe_str(row.get("psc_code")),
                standardize_date(row.get("pop_start")),
                standardize_date(row.get("pop_end")),
                standardize_date(row.get("pop_ultimate")),
                safe_str(row.get("pop_city")),
                safe_str(row.get("pop_state")),
                safe_str(row.get("fiscal_year")),
                safe_str(row.get("idv_type")),
                safe_str(row.get("set_aside")),
                safe_str(row.get("award_type")),
                standardize_date(row.get("award_date")),
                safe_str(row.get("prime_search")),
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    {csv_path.name}: {count} contracts")
    return count


def _load_master_contracts(cursor, csv_path: Path, dedup: Deduplicator,
                           program_lookup: dict, company_lookup: dict, verbose: bool) -> int:
    """Load MASTER_CONTRACTS_COMBINED.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            piid = safe_str(row.get("piid"))
            if not piid:
                continue
            if not dedup.is_new(piid):
                continue

            recipient = safe_str(row.get("recipient")) or ""
            program_id = fuzzy_program_match(safe_str(row.get("program")), program_lookup)
            company_id = company_lookup.get(normalize_company_name(recipient).lower())

            cid = generate_id(piid, row.get("source", "master"))
            cursor.execute("""
                INSERT OR IGNORE INTO contracts (
                    id, piid, source, program_id, program_name,
                    recipient_name, company_id,
                    award_amount, description,
                    awarding_agency,
                    start_date, end_date,
                    source_file
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cid, piid, safe_str(row.get("source")),
                program_id, safe_str(row.get("program")),
                recipient, company_id,
                parse_currency(row.get("amount")),
                safe_str(row.get("description")),
                safe_str(row.get("agency")),
                standardize_date(row.get("start_date")),
                standardize_date(row.get("end_date")),
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    {csv_path.name}: {count} contracts")
    return count


def _load_dod_contracts(cursor, csv_path: Path, dedup: Deduplicator,
                        program_lookup: dict, company_lookup: dict, verbose: bool) -> int:
    """Load db1_dod_prime_contracts_100m.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            piid = safe_str(row.get("contract_id")) or safe_str(row.get("award_id"))
            if not piid:
                continue
            if not dedup.is_new(piid):
                continue

            recipient = safe_str(row.get("recipient_name")) or ""
            company_id = company_lookup.get(normalize_company_name(recipient).lower())

            cid = generate_id(piid, "dod")
            cursor.execute("""
                INSERT OR IGNORE INTO contracts (
                    id, piid, award_id, contract_id, source,
                    recipient_name, recipient_uei, company_id,
                    award_amount, description,
                    awarding_agency, awarding_sub_agency,
                    naics_code, naics_description,
                    psc_code, psc_description,
                    start_date, end_date,
                    pop_city, pop_state,
                    is_dod, is_it_services,
                    source_file
                ) VALUES (?, ?, ?, ?, 'dod_100m', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cid, piid,
                safe_str(row.get("award_id")),
                safe_str(row.get("contract_id")),
                recipient, safe_str(row.get("recipient_uei")), company_id,
                parse_currency(row.get("award_amount")),
                safe_str(row.get("description")),
                safe_str(row.get("awarding_agency")),
                safe_str(row.get("awarding_sub_agency")),
                safe_str(row.get("naics_code")),
                safe_str(row.get("naics_description")),
                safe_str(row.get("psc_code")),
                safe_str(row.get("psc_description")),
                standardize_date(row.get("start_date")),
                standardize_date(row.get("end_date")),
                safe_str(row.get("pop_city")),
                safe_str(row.get("pop_state")),
                safe_int(row.get("is_dod")),
                safe_int(row.get("is_it_services")),
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    {csv_path.name}: {count} contracts")
    return count


def _load_program_contracts(cursor, csv_path: Path, dedup: Deduplicator,
                            program_lookup: dict, company_lookup: dict, verbose: bool) -> int:
    """Load FULL_PROGRAM_CONTRACTS.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            piid = safe_str(row.get("piid"))
            if not piid:
                continue
            if not dedup.is_new(piid):
                continue

            recipient = safe_str(row.get("recipient")) or ""
            program_id = fuzzy_program_match(safe_str(row.get("program_name")), program_lookup)
            company_id = company_lookup.get(normalize_company_name(recipient).lower())

            cid = generate_id(piid, "full_program")
            cursor.execute("""
                INSERT OR IGNORE INTO contracts (
                    id, piid, source, program_id, program_name,
                    recipient_name, recipient_uei, company_id,
                    award_amount, description, awarding_agency,
                    start_date, end_date,
                    source_file
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cid, piid, safe_str(row.get("source")),
                program_id, safe_str(row.get("program_name")),
                recipient, safe_str(row.get("recipient_uei")), company_id,
                parse_currency(row.get("amount")),
                safe_str(row.get("description")),
                safe_str(row.get("agency")),
                standardize_date(row.get("start_date")),
                standardize_date(row.get("end_date")),
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    {csv_path.name}: {count} contracts")
    return count


def _load_phase3_contracts(cursor, csv_path: Path, dedup: Deduplicator,
                           program_lookup: dict, company_lookup: dict, verbose: bool) -> int:
    """Load PHASE3_ALL_PROGRAM_CONTRACTS.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            piid = safe_str(row.get("piid"))
            if not piid:
                continue
            if not dedup.is_new(piid):
                continue

            recipient = safe_str(row.get("recipient")) or ""
            program_id = fuzzy_program_match(safe_str(row.get("program")), program_lookup)
            company_id = company_lookup.get(normalize_company_name(recipient).lower())

            cid = generate_id(piid, "phase3")
            cursor.execute("""
                INSERT OR IGNORE INTO contracts (
                    id, piid, source, program_id, program_name,
                    recipient_name, company_id,
                    award_amount, description, awarding_agency,
                    start_date, end_date,
                    source_file
                ) VALUES (?, ?, 'phase3', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cid, piid,
                program_id, safe_str(row.get("program")),
                recipient, company_id,
                parse_currency(row.get("amount")),
                safe_str(row.get("description")),
                safe_str(row.get("agency")),
                standardize_date(row.get("start_date")),
                standardize_date(row.get("end_date")),
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    {csv_path.name}: {count} contracts")
    return count
