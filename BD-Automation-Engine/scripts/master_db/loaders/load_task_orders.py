"""
Task Orders / Subawards ETL Loader
Sources: db2_subawards_tango.csv (5,531), PHASE1_ALL_SUBCONTRACTORS.csv,
         PHASE2_SUBAWARD_CHAINS.csv, PHASE3_IDV_TASK_ORDERS.csv
"""

import csv
import sqlite3
from pathlib import Path

from ..utils import (
    Deduplicator,
    generate_id,
    parse_currency,
    safe_int,
    safe_str,
    standardize_date,
)

BASE_DIR = Path(__file__).parent.parent.parent.parent


def load_task_orders(conn: sqlite3.Connection, verbose: bool = False) -> int:
    """Load task orders/subawards from all sources."""
    cursor = conn.cursor()
    dedup = Deduplicator()
    loaded = 0

    # Source 1: db2_subawards_tango.csv (5,531 rows - primary)
    subawards = BASE_DIR / "data" / "from_data_scraper" / "db2_subawards_tango.csv"
    if subawards.exists():
        loaded += _load_subawards_tango(cursor, subawards, dedup, verbose)

    # Source 2: PHASE3_IDV_TASK_ORDERS.csv
    phase3 = BASE_DIR / "data" / "from_data_scraper" / "PHASE3_IDV_TASK_ORDERS.csv"
    if phase3.exists():
        loaded += _load_phase3_task_orders(cursor, phase3, dedup, verbose)

    conn.commit()
    if verbose:
        print(f"  Task orders loaded: {loaded} ({dedup.stats})")
    return loaded


def _load_subawards_tango(cursor, csv_path: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load from db2_subawards_tango.csv."""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sub_id = safe_str(row.get("subaward_id"))
            prime_award = safe_str(row.get("prime_award_id"))
            sub_name = safe_str(row.get("sub_recipient_name"))

            dedup_key = sub_id or f"{prime_award}|{sub_name}|{row.get('subaward_date', '')}"
            if not dedup.is_new(dedup_key):
                continue

            tid = generate_id(dedup_key, "tango")
            cursor.execute("""
                INSERT OR IGNORE INTO task_orders (
                    id, subaward_id, prime_award_id,
                    prime_name, prime_uei,
                    sub_recipient_name, sub_recipient_uei,
                    subaward_amount, subaward_date, subaward_description,
                    awarding_agency, fiscal_year,
                    is_competitor, competitor_match,
                    extraction_date, source_file
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tid, sub_id, prime_award,
                safe_str(row.get("prime_name")),
                safe_str(row.get("prime_uei")),
                sub_name,
                safe_str(row.get("sub_recipient_uei")),
                parse_currency(row.get("subaward_amount")),
                standardize_date(row.get("subaward_date")),
                safe_str(row.get("subaward_description")),
                safe_str(row.get("awarding_agency")),
                safe_str(row.get("fiscal_year")),
                safe_int(row.get("is_competitor")),
                safe_str(row.get("competitor_match")),
                safe_str(row.get("extraction_date")),
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    {csv_path.name}: {count} subawards")
    return count


def _load_phase3_task_orders(cursor, csv_path: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load from PHASE3_IDV_TASK_ORDERS.csv."""
    count = 0
    if not csv_path.exists():
        return 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            piid = safe_str(row.get("piid")) or safe_str(row.get("task_order_piid"))
            prime_award = safe_str(row.get("prime_award_id")) or safe_str(row.get("parent_piid"))
            if not piid and not prime_award:
                continue
            dedup_key = piid or f"{prime_award}|{row.get('recipient', '')}"
            if not dedup.is_new(dedup_key):
                continue

            tid = generate_id(dedup_key, "phase3_idv")
            cursor.execute("""
                INSERT OR IGNORE INTO task_orders (
                    id, subaward_id, prime_award_id,
                    sub_recipient_name, sub_recipient_uei,
                    subaward_amount, subaward_description,
                    awarding_agency,
                    source_file
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tid, piid, prime_award,
                safe_str(row.get("recipient") or row.get("sub_recipient_name")),
                safe_str(row.get("recipient_uei")),
                parse_currency(row.get("amount") or row.get("subaward_amount")),
                safe_str(row.get("description")),
                safe_str(row.get("agency") or row.get("awarding_agency")),
                str(csv_path.name),
            ))
            count += 1
    if verbose:
        print(f"    {csv_path.name}: {count} task orders")
    return count
