"""
Data Quality Scoring
Adds data_quality_score (0-100) to contacts, programs, companies, intelligence.
Scores based on weighted field completeness per record.
"""
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data" / "unified_federal_contracts.db"

# Field weights per table (field_name: weight, must sum to 100)
QUALITY_WEIGHTS = {
    "contacts": {
        "full_name": 15, "email": 15, "phone": 10, "title": 10,
        "company": 10, "tier": 10, "program": 10, "notes": 5,
        "linkedin": 5, "last_activity": 5, "clearances": 5,
    },
    "programs": {
        "program_name": 15, "agency_owner": 10, "prime_contractor": 10,
        "total_contract_value": 10, "description": 10, "pop_start_consolidated": 5,
        "pop_end_consolidated": 5, "technical_stack": 5, "naics_code_consolidated": 5,
        "clearance_requirements": 5, "keywords_signals": 5, "functional_areas": 5,
        "priority_level": 5, "recompete_date": 5,
    },
    "companies": {
        "name": 15, "normalized_name": 10, "company_type": 10,
        "employee_count": 5, "annual_revenue": 5, "website": 5,
        "headquarters": 5, "key_capabilities": 10, "contract_vehicles": 5,
        "naics_codes": 5, "federal_programs_prime": 10, "past_performance": 10,
        "cage_code": 5,
    },
    "intelligence": {
        "intel_type": 10, "program_name": 10, "company_name": 10,
        "bd_score": 15, "description": 10, "awarding_agency": 5,
        "award_amount": 10, "start_date": 5, "end_date": 5,
        "competitors": 5, "narrative": 10, "lifecycle_phase": 5,
    },
}


def ensure_column(conn, table):
    """Add data_quality_score column if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    if "data_quality_score" not in cols:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN data_quality_score REAL")
        conn.commit()


def score_table(conn, table, weights):
    """Compute quality scores for all records in a table."""
    cursor = conn.cursor()

    # Verify which weight columns actually exist
    cursor.execute(f"PRAGMA table_info({table})")
    existing_cols = {row[1] for row in cursor.fetchall()}
    valid_weights = {k: v for k, v in weights.items() if k in existing_cols}

    if not valid_weights:
        print(f"  {table}: no valid weight columns found")
        return 0

    # Normalize weights to sum to 100
    total_weight = sum(valid_weights.values())
    if total_weight == 0:
        return 0
    scale = 100.0 / total_weight

    # Build SQL CASE expression for scoring
    parts = []
    for col, weight in valid_weights.items():
        scaled = weight * scale
        parts.append(f"CASE WHEN [{col}] IS NOT NULL AND TRIM([{col}]) != '' THEN {scaled:.2f} ELSE 0 END")

    score_expr = " + ".join(parts)

    cursor.execute(f"""
        UPDATE {table} SET data_quality_score = ROUND({score_expr}, 1)
    """)

    updated = cursor.rowcount

    # Get stats
    cursor.execute(f"SELECT AVG(data_quality_score), MIN(data_quality_score), MAX(data_quality_score) FROM {table}")
    avg_score, min_score, max_score = cursor.fetchone()

    print(f"  {table}: {updated} scored (avg={avg_score:.1f}, min={min_score:.1f}, max={max_score:.1f})")
    return updated


def run(db_path=None):
    """Run data quality scoring."""
    db_path = db_path or DB_PATH
    print("Data Quality Scoring")
    print(f"  Database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    total = 0
    try:
        for table, weights in QUALITY_WEIGHTS.items():
            ensure_column(conn, table)
            count = score_table(conn, table, weights)
            total += count
        conn.commit()
    finally:
        conn.close()

    print(f"  Total records scored: {total}")


if __name__ == "__main__":
    run()
