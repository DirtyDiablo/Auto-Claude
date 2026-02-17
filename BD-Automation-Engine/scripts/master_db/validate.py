"""
Post-build validation for the master database.
Checks row counts, referential integrity, required fields, duplicates.
"""

import sqlite3
from pathlib import Path

from .schema import DATABASE_PATH, get_connection


def validate(db_path: Path = None, verbose: bool = True) -> dict:
    """Run all validation checks. Returns dict of results."""
    conn = get_connection(db_path)
    results = {
        "row_counts": _check_row_counts(conn, verbose),
        "required_fields": _check_required_fields(conn, verbose),
        "duplicates": _check_duplicates(conn, verbose),
        "referential_integrity": _check_referential_integrity(conn, verbose),
    }
    conn.close()

    # Summary
    total_issues = sum(
        len(v.get("issues", [])) if isinstance(v, dict) else 0
        for v in results.values()
    )
    if verbose:
        print(f"\n{'='*50}")
        if total_issues == 0:
            print("VALIDATION PASSED - No issues found")
        else:
            print(f"VALIDATION: {total_issues} issue(s) found")
        print(f"{'='*50}")

    results["total_issues"] = total_issues
    return results


def _check_row_counts(conn, verbose: bool) -> dict:
    """Check row counts are within expected ranges."""
    expected_ranges = {
        "programs": (50, 10000),
        "companies": (10, 10000),
        "contracts": (100, 10000),
        "task_orders": (100, 10000),
        "contacts": (100, 10000),
        "jobs": (50, 1000),
        "placements": (100, 1000),
        "activities": (1000, 60000),
        "intelligence": (50, 5000),
        "documents": (10, 500),
    }

    counts = {}
    issues = []
    cursor = conn.cursor()

    for table, (min_rows, max_rows) in expected_ranges.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            counts[table] = count

            if count < min_rows:
                issues.append(f"{table}: {count} rows (expected >= {min_rows})")
            elif count > max_rows:
                issues.append(f"{table}: {count} rows (expected <= {max_rows})")

            if verbose:
                status = "OK" if min_rows <= count <= max_rows else "WARN"
                print(f"  [{status}] {table}: {count:,} rows")
        except sqlite3.OperationalError as e:
            issues.append(f"{table}: table error - {e}")
            counts[table] = -1

    return {"counts": counts, "issues": issues}


def _check_required_fields(conn, verbose: bool) -> dict:
    """Check that required fields are not NULL."""
    checks = [
        ("programs", "program_name", "program_name IS NULL OR program_name = ''"),
        ("companies", "name", "name IS NULL OR name = ''"),
        ("contacts", "full_name", "full_name IS NULL OR full_name = ''"),
        ("jobs", "title", "title IS NULL OR title = ''"),
        ("contracts", "piid", "piid IS NULL OR piid = ''"),
    ]

    issues = []
    cursor = conn.cursor()

    for table, field, condition in checks:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {condition}")
            null_count = cursor.fetchone()[0]
            if null_count > 0:
                issues.append(f"{table}.{field}: {null_count} NULL/empty values")
            if verbose:
                status = "OK" if null_count == 0 else "WARN"
                print(f"  [{status}] {table}.{field}: {null_count} nulls")
        except sqlite3.OperationalError:
            pass

    return {"issues": issues}


def _check_duplicates(conn, verbose: bool) -> dict:
    """Check for duplicate records on key fields."""
    checks = [
        ("contacts", "email", "email IS NOT NULL AND email != ''"),
        ("contracts", "piid", "piid IS NOT NULL AND piid != ''"),
        ("programs", "program_name", "1=1"),
    ]

    issues = []
    cursor = conn.cursor()

    for table, field, where_clause in checks:
        try:
            cursor.execute(f"""
                SELECT {field}, COUNT(*) as cnt FROM {table}
                WHERE {where_clause}
                GROUP BY {field} HAVING cnt > 1
                LIMIT 10
            """)
            dupes = cursor.fetchall()
            if dupes:
                issues.append(f"{table}.{field}: {len(dupes)} duplicate values")
                if verbose:
                    for val, cnt in dupes[:3]:
                        print(f"    Duplicate: {val} ({cnt}x)")
            if verbose:
                status = "OK" if not dupes else "WARN"
                print(f"  [{status}] {table}.{field}: {len(dupes)} duplicates")
        except sqlite3.OperationalError:
            pass

    return {"issues": issues}


def _check_referential_integrity(conn, verbose: bool) -> dict:
    """Check foreign key relationships."""
    checks = [
        ("contracts", "program_id", "programs", "id",
         "program_id IS NOT NULL"),
        ("program_contacts", "program_id", "programs", "id", "1=1"),
        ("program_contacts", "contact_id", "contacts", "id", "1=1"),
        ("program_companies", "program_id", "programs", "id", "1=1"),
        ("program_companies", "company_id", "companies", "id", "1=1"),
    ]

    issues = []
    cursor = conn.cursor()

    for child_table, child_col, parent_table, parent_col, where in checks:
        try:
            cursor.execute(f"""
                SELECT COUNT(*) FROM {child_table} c
                WHERE {where}
                AND NOT EXISTS (
                    SELECT 1 FROM {parent_table} p WHERE p.{parent_col} = c.{child_col}
                )
            """)
            orphan_count = cursor.fetchone()[0]
            if orphan_count > 0:
                issues.append(
                    f"{child_table}.{child_col} -> {parent_table}.{parent_col}: "
                    f"{orphan_count} orphan records"
                )
            if verbose:
                status = "OK" if orphan_count == 0 else "WARN"
                print(f"  [{status}] {child_table}.{child_col} -> {parent_table}: {orphan_count} orphans")
        except sqlite3.OperationalError:
            pass

    return {"issues": issues}


if __name__ == "__main__":
    print("Running validation on master database...\n")
    results = validate(verbose=True)
