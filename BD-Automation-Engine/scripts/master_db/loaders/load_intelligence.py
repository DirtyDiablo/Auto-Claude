"""
Intelligence ETL Loader
Sources: bd_master_target_list.csv, bd_scored_targets.csv, bd_all_scored_targets.csv,
         bd_competitor_contract_presence.csv, COMBINED_INTELLIGENCE_REPORT.csv,
         PROGRAM_INTELLIGENCE.csv, Bullhorn gap_analysis, bd_graph.db entities,
         PHASE4_RECOMPETE_PIPELINE.csv, bd_hot_hiring_programs.csv,
         competitor_program_matches.csv, db6_bd_targets_priority.csv
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
    normalize_company_name,
    parse_currency,
    safe_float,
    safe_int,
    safe_str,
    standardize_date,
)

BASE_DIR = Path(__file__).parent.parent.parent.parent


def load_intelligence(conn: sqlite3.Connection, verbose: bool = False) -> int:
    """Load intelligence data from all sources."""
    cursor = conn.cursor()
    dedup = Deduplicator()
    program_lookup = build_program_lookup(conn)
    loaded = 0

    sources = [
        ("bd_master_target_list.csv", _load_bd_targets),
        ("bd_all_scored_targets.csv", _load_scored_targets),
        ("bd_scored_targets.csv", _load_scored_targets_v2),
        ("db6_bd_targets_priority.csv", _load_db6_targets),
        ("bd_competitor_contract_presence.csv", _load_competitor_presence),
        ("competitor_program_matches.csv", _load_competitor_matches),
        ("bd_hot_hiring_programs.csv", _load_hot_hiring),
    ]

    for filename, loader_fn in sources:
        csv_path = BASE_DIR / "data" / "enriched" / "targets" / filename
        if csv_path.exists():
            loaded += loader_fn(cursor, csv_path, dedup, program_lookup, verbose)

    # Bullhorn gap_analysis
    bullhorn_db = BASE_DIR / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"
    if bullhorn_db.exists():
        loaded += _load_gap_analysis(cursor, bullhorn_db, dedup, verbose)

    # bd_graph.db entities
    graph_db = BASE_DIR / "Engine8_Knowledge" / "data" / "bd_graph.db"
    if graph_db.exists():
        loaded += _load_graph_entities(cursor, graph_db, dedup, verbose)

    conn.commit()
    if verbose:
        print(f"  Intelligence loaded: {loaded} ({dedup.stats})")
    return loaded


def _load_bd_targets(cursor, csv_path: Path, dedup: Deduplicator,
                     program_lookup: dict, verbose: bool) -> int:
    """Load bd_master_target_list.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            piid = safe_str(row.get("piid"))
            recipient = safe_str(row.get("recipient_name"))
            dedup_key = piid or f"{recipient}|{row.get('description', '')[:50]}"
            if not dedup.is_new(dedup_key, "bd_target"):
                continue

            iid = generate_id(dedup_key, "bd_target")
            cursor.execute("""
                INSERT OR IGNORE INTO intelligence (
                    id, intel_type, company_name, piid,
                    bd_score, bd_reasons,
                    lifecycle_phase, is_base_year, runway_years,
                    award_amount, description,
                    awarding_agency, sub_agency,
                    naics_code, psc_code,
                    pop_city, pop_state,
                    start_date, end_date,
                    matched_jobs, competitors,
                    source, source_file
                ) VALUES (?, 'bd_target', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                iid, recipient, piid,
                safe_float(row.get("bd_score")),
                safe_str(row.get("bd_reasons")),
                safe_str(row.get("lifecycle_phase")),
                safe_int(row.get("is_base_year")),
                safe_float(row.get("runway_years")),
                parse_currency(row.get("award_amount")),
                safe_str(row.get("description")),
                safe_str(row.get("awarding_agency")),
                safe_str(row.get("sub_agency")),
                safe_str(row.get("naics_code")),
                safe_str(row.get("psc_code")),
                safe_str(row.get("pop_city")),
                safe_str(row.get("pop_state")),
                standardize_date(row.get("start_date")),
                standardize_date(row.get("end_date")),
                safe_str(row.get("matched_jobs")),
                safe_str(row.get("competitors_in_agency")),
                "bd_master_target_list",
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    {csv_path.name}: {count}")
    return count


def _load_scored_targets(cursor, csv_path: Path, dedup: Deduplicator,
                         program_lookup: dict, verbose: bool) -> int:
    """Load bd_all_scored_targets.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            piid = safe_str(row.get("piid")) or safe_str(row.get("award_id"))
            recipient = safe_str(row.get("recipient_name"))
            dedup_key = piid or f"{recipient}|scored"
            if not dedup.is_new(dedup_key, "scored"):
                continue

            iid = generate_id(dedup_key, "scored_target")
            cursor.execute("""
                INSERT OR IGNORE INTO intelligence (
                    id, intel_type, company_name, piid,
                    bd_score, bd_reasons,
                    lifecycle_phase, is_base_year, runway_years,
                    award_amount, description,
                    awarding_agency, sub_agency,
                    naics_code, psc_code,
                    pop_city, pop_state,
                    start_date, end_date,
                    competitors, competitor_present,
                    hiring_activity,
                    source, source_file
                ) VALUES (?, 'scored_target', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                iid, recipient, piid,
                safe_float(row.get("bd_score")),
                safe_str(row.get("bd_reasons")),
                safe_str(row.get("lifecycle_phase")),
                safe_int(row.get("is_base_year")),
                safe_float(row.get("runway_years")),
                parse_currency(row.get("award_amount")),
                safe_str(row.get("description")),
                safe_str(row.get("awarding_agency")),
                safe_str(row.get("sub_agency")),
                safe_str(row.get("naics_code")),
                safe_str(row.get("psc_code")),
                safe_str(row.get("pop_city")),
                safe_str(row.get("pop_state")),
                standardize_date(row.get("start_date")),
                standardize_date(row.get("end_date")),
                safe_str(row.get("competitors")),
                safe_int(row.get("competitor_present")),
                safe_str(row.get("job_activity")),
                "bd_all_scored_targets",
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    {csv_path.name}: {count}")
    return count


def _load_scored_targets_v2(cursor, csv_path: Path, dedup: Deduplicator,
                            program_lookup: dict, verbose: bool) -> int:
    """Load bd_scored_targets.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            piid = safe_str(row.get("piid"))
            if not piid:
                continue
            if not dedup.is_new(piid, "scored_v2"):
                continue

            iid = generate_id(piid, "scored_v2")
            cursor.execute("""
                INSERT OR IGNORE INTO intelligence (
                    id, intel_type, company_name, piid,
                    bd_score, bd_reasons,
                    award_amount, description,
                    days_until_end,
                    pop_city, pop_state,
                    start_date, end_date,
                    competitor_present,
                    source, source_file
                ) VALUES (?, 'scored_target', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                iid, safe_str(row.get("recipient_name")), piid,
                safe_float(row.get("bd_score")),
                safe_str(row.get("bd_reasons")),
                parse_currency(row.get("obligated") or row.get("total_contract_value")),
                safe_str(row.get("description")),
                safe_int(row.get("days_until_end")),
                safe_str(row.get("pop_city")),
                safe_str(row.get("pop_state")),
                standardize_date(row.get("pop_start")),
                standardize_date(row.get("pop_end")),
                safe_int(row.get("competitor_present")),
                "bd_scored_targets",
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    {csv_path.name}: {count}")
    return count


def _load_db6_targets(cursor, csv_path: Path, dedup: Deduplicator,
                      program_lookup: dict, verbose: bool) -> int:
    """Load db6_bd_targets_priority.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            piid = safe_str(row.get("contract_id")) or safe_str(row.get("award_id"))
            if not piid:
                continue
            if not dedup.is_new(piid, "db6"):
                continue

            iid = generate_id(piid, "db6_target")
            cursor.execute("""
                INSERT OR IGNORE INTO intelligence (
                    id, intel_type, company_name, piid,
                    bd_score, bd_reasons,
                    award_amount, description,
                    awarding_agency, sub_agency,
                    naics_code, psc_code,
                    pop_city, pop_state,
                    start_date, end_date,
                    source, source_file
                ) VALUES (?, 'priority_target', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                iid, safe_str(row.get("recipient_name")), piid,
                safe_float(row.get("bd_score")),
                safe_str(row.get("bd_reasons")),
                parse_currency(row.get("award_amount")),
                safe_str(row.get("description")),
                safe_str(row.get("awarding_agency")),
                safe_str(row.get("awarding_sub_agency")),
                safe_str(row.get("naics_code")),
                safe_str(row.get("psc_code")),
                safe_str(row.get("pop_city")),
                safe_str(row.get("pop_state")),
                standardize_date(row.get("start_date")),
                standardize_date(row.get("end_date")),
                "db6_bd_targets_priority",
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    {csv_path.name}: {count}")
    return count


def _load_competitor_presence(cursor, csv_path: Path, dedup: Deduplicator,
                              program_lookup: dict, verbose: bool) -> int:
    """Load bd_competitor_contract_presence.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row.get('competitor', '')}|{row.get('award_id', '')}"
            if not dedup.is_new(key, "competitor"):
                continue
            iid = generate_id(key, "competitor_presence")
            cursor.execute("""
                INSERT OR IGNORE INTO intelligence (
                    id, intel_type, company_name, piid,
                    award_amount, description,
                    awarding_agency,
                    source, source_file
                ) VALUES (?, 'competitor_presence', ?, ?, ?, ?, ?, ?, ?)
            """, (
                iid,
                safe_str(row.get("competitor")),
                safe_str(row.get("award_id")),
                parse_currency(row.get("award_amount")),
                safe_str(row.get("award_description")),
                safe_str(row.get("awarding_agency")),
                "competitor_presence",
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    {csv_path.name}: {count}")
    return count


def _load_competitor_matches(cursor, csv_path: Path, dedup: Deduplicator,
                             program_lookup: dict, verbose: bool) -> int:
    """Load competitor_program_matches.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row.get('competitor', '')}|{row.get('award_id', '')}|{row.get('matched_program', '')}"
            if not dedup.is_new(key, "comp_match"):
                continue
            program_id = fuzzy_program_match(safe_str(row.get("matched_program")), program_lookup)
            iid = generate_id(key, "comp_match")
            cursor.execute("""
                INSERT OR IGNORE INTO intelligence (
                    id, intel_type, company_name, piid,
                    program_id, program_name,
                    award_amount, description,
                    awarding_agency, pop_city, pop_state,
                    source, source_file
                ) VALUES (?, 'competitor_match', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                iid,
                safe_str(row.get("competitor")),
                safe_str(row.get("award_id")),
                program_id,
                safe_str(row.get("matched_program")),
                parse_currency(row.get("award_amount")),
                safe_str(row.get("award_description")),
                safe_str(row.get("awarding_agency")),
                safe_str(row.get("pop_city")),
                safe_str(row.get("pop_state")),
                "competitor_program_matches",
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    {csv_path.name}: {count}")
    return count


def _load_hot_hiring(cursor, csv_path: Path, dedup: Deduplicator,
                     program_lookup: dict, verbose: bool) -> int:
    """Load bd_hot_hiring_programs.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            prog = safe_str(row.get("program") or row.get("program_name"))
            if not prog:
                continue
            if not dedup.is_new(prog, "hot_hiring"):
                continue
            program_id = fuzzy_program_match(prog, program_lookup)
            iid = generate_id(prog, "hot_hiring")
            cursor.execute("""
                INSERT OR IGNORE INTO intelligence (
                    id, intel_type, program_id, program_name,
                    hiring_activity,
                    source, source_file
                ) VALUES (?, 'hot_hiring', ?, ?, ?, ?, ?)
            """, (
                iid, program_id, prog,
                safe_str(row.get("job_count") or row.get("hiring_activity")),
                "bd_hot_hiring_programs",
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    {csv_path.name}: {count}")
    return count


def _load_gap_analysis(cursor, db_path: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load gap_analysis from Bullhorn."""
    count = 0
    bh_conn = sqlite3.connect(str(db_path))
    bh_conn.row_factory = sqlite3.Row
    bh_cursor = bh_conn.cursor()

    bh_cursor.execute("SELECT * FROM gap_analysis")
    for row in bh_cursor.fetchall():
        keys = row.keys()
        gap_id = str(row["id"]) if "id" in keys else str(count)
        if not dedup.is_new(gap_id, "gap"):
            continue
        iid = generate_id(gap_id, "gap_analysis")
        cursor.execute("""
            INSERT OR IGNORE INTO intelligence (
                id, intel_type,
                program_name, company_name,
                gap_analysis_notes,
                source, source_file
            ) VALUES (?, 'gap_analysis', ?, ?, ?, ?, 'bullhorn_master.db')
        """, (
            iid,
            safe_str(row["program_name"] if "program_name" in keys else None),
            safe_str(row["prime_name"] if "prime_name" in keys else None),
            safe_str(row["analysis"] if "analysis" in keys else
                    row["gap_description"] if "gap_description" in keys else None),
            "gap_analysis",
        ))
        count += 1

    bh_conn.close()
    if verbose:
        print(f"    Bullhorn gap_analysis: {count}")
    return count


def _load_graph_entities(cursor, db_path: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load entities from bd_graph.db."""
    count = 0
    graph_conn = sqlite3.connect(str(db_path))
    graph_conn.row_factory = sqlite3.Row
    graph_cursor = graph_conn.cursor()

    graph_cursor.execute("SELECT * FROM entities")
    for row in graph_cursor.fetchall():
        entity_id = str(row["id"])
        entity_type = row["type"]
        entity_name = row["name"]
        if not entity_name:
            continue
        if not dedup.is_new(entity_name, entity_type, "graph"):
            continue

        iid = generate_id(entity_id, "graph")
        cursor.execute("""
            INSERT OR IGNORE INTO intelligence (
                id, intel_type, entity_type, entity_properties,
                program_name, company_name,
                source, source_file
            ) VALUES (?, 'graph_entity', ?, ?, ?, ?, ?, 'bd_graph.db')
        """, (
            iid, entity_type, row["properties"],
            entity_name if entity_type == "program" else None,
            entity_name if entity_type in ("company", "prime") else None,
            f"graph_{entity_type}",
        ))
        count += 1

    graph_conn.close()
    if verbose:
        print(f"    bd_graph.db entities: {count}")
    return count
