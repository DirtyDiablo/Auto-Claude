"""
Tests for the Master Federal Contracts Database.
"""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.master_db.schema import create_database, get_connection, get_table_counts
from scripts.master_db.utils import (
    Deduplicator,
    generate_id,
    normalize_company_name,
    normalize_name,
    parse_currency,
    safe_float,
    safe_int,
    safe_str,
    standardize_date,
    json_encode_array,
)


@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary test database."""
    db_path = tmp_path / "test_master.db"
    create_database(db_path)
    return db_path


@pytest.fixture
def conn(tmp_db):
    """Get connection to test database."""
    c = get_connection(tmp_db)
    yield c
    c.close()


# =========================================
# Schema Tests
# =========================================

class TestSchema:
    def test_all_tables_exist(self, tmp_db):
        """All 16 core tables + placement_program_links should exist."""
        conn = get_connection(tmp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        expected = {
            "programs", "companies", "contracts", "task_orders",
            "contacts", "jobs", "placements", "activities",
            "intelligence", "documents", "timelines", "scoring",
            "program_contacts", "program_companies",
            "etl_runs", "source_tracking",
            "placement_program_links",
        }
        assert expected.issubset(tables), f"Missing tables: {expected - tables}"

    def test_all_views_exist(self, tmp_db):
        """All 6 views should exist."""
        conn = get_connection(tmp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
        views = {row[0] for row in cursor.fetchall()}
        conn.close()

        expected = {
            "program_360_view", "bd_pipeline_view", "revenue_by_program",
            "contact_network_view", "recompete_calendar", "competitive_landscape",
        }
        assert expected.issubset(views), f"Missing views: {expected - views}"

    def test_table_counts_initial(self, tmp_db):
        """All tables should start empty."""
        counts = get_table_counts(tmp_db)
        for table, count in counts.items():
            assert count == 0, f"{table} should be empty, got {count}"

    def test_indexes_exist(self, tmp_db):
        """Key indexes should exist."""
        conn = get_connection(tmp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}
        conn.close()

        key_indexes = {"idx_programs_name", "idx_contacts_email", "idx_contracts_piid"}
        assert key_indexes.issubset(indexes)


# =========================================
# Utils Tests
# =========================================

class TestCurrencyParsing:
    def test_plain_number(self):
        assert parse_currency("47500000") == 47500000.0

    def test_dollar_sign(self):
        assert parse_currency("$1,234.56") == 1234.56

    def test_millions(self):
        assert parse_currency("$47.5M") == 47_500_000.0

    def test_billions(self):
        assert parse_currency("$1.2B") == 1_200_000_000.0

    def test_thousands(self):
        assert parse_currency("$500K") == 500_000.0

    def test_none(self):
        assert parse_currency(None) is None

    def test_empty(self):
        assert parse_currency("") is None

    def test_nan(self):
        assert parse_currency(float("nan")) is None

    def test_na(self):
        assert parse_currency("N/A") is None

    def test_float_passthrough(self):
        assert parse_currency(123.45) == 123.45


class TestCompanyNormalization:
    def test_leidos(self):
        assert normalize_company_name("Leidos - ONLY ONE YOU ARE TO USE") == "Leidos"

    def test_boeing(self):
        assert normalize_company_name("BOEING") == "Boeing"

    def test_gdit(self):
        assert normalize_company_name("GDIT") == "General Dynamics IT"

    def test_suffix_removal(self):
        assert normalize_company_name("Acme Corp.") == "Acme"

    def test_empty(self):
        assert normalize_company_name("") == ""

    def test_none(self):
        assert normalize_company_name(None) == ""


class TestDateStandardization:
    def test_iso_format(self):
        assert standardize_date("2024-01-15") == "2024-01-15"

    def test_us_format(self):
        assert standardize_date("01/15/2024") == "2024-01-15"

    def test_datetime_format(self):
        assert standardize_date("2024-01-15T10:30:00") == "2024-01-15"

    def test_none(self):
        assert standardize_date(None) is None

    def test_empty(self):
        assert standardize_date("") is None

    def test_nan(self):
        assert standardize_date("nan") is None


class TestDeduplicator:
    def test_first_is_new(self):
        d = Deduplicator()
        assert d.is_new("test") is True

    def test_second_is_duplicate(self):
        d = Deduplicator()
        d.is_new("test")
        assert d.is_new("test") is False

    def test_different_keys(self):
        d = Deduplicator()
        assert d.is_new("a") is True
        assert d.is_new("b") is True

    def test_case_insensitive(self):
        d = Deduplicator()
        d.is_new("Test")
        assert d.is_new("test") is False

    def test_stats(self):
        d = Deduplicator()
        d.is_new("a")
        d.is_new("b")
        d.is_new("a")
        assert d.stats == {"total": 3, "unique": 2, "duplicates": 1}


class TestGenerateId:
    def test_deterministic(self):
        id1 = generate_id("test", "program")
        id2 = generate_id("test", "program")
        assert id1 == id2

    def test_different_inputs(self):
        id1 = generate_id("a", "b")
        id2 = generate_id("c", "d")
        assert id1 != id2

    def test_length(self):
        assert len(generate_id("test")) == 16


class TestSafeConversions:
    def test_safe_str_none(self):
        assert safe_str(None) is None

    def test_safe_str_nan(self):
        assert safe_str(float("nan")) is None

    def test_safe_str_value(self):
        assert safe_str("hello") == "hello"

    def test_safe_int_value(self):
        assert safe_int("42") == 42

    def test_safe_int_none(self):
        assert safe_int(None) is None

    def test_safe_float_value(self):
        assert safe_float("3.14") == 3.14

    def test_json_encode_list(self):
        result = json_encode_array(["a", "b"])
        assert json.loads(result) == ["a", "b"]

    def test_json_encode_comma_string(self):
        result = json_encode_array("a, b, c")
        assert json.loads(result) == ["a", "b", "c"]


# =========================================
# Loader Integration Tests (with fixture data)
# =========================================

class TestLoadersWithFixtures:
    def test_insert_program(self, conn):
        """Test inserting a program directly."""
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO programs (id, program_name, acronym, agency_owner)
            VALUES ('test1', 'Test Program', 'TP', 'DoD')
        """)
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM programs")
        assert cursor.fetchone()[0] == 1

    def test_insert_company(self, conn):
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO companies (id, name, normalized_name)
            VALUES ('c1', 'Leidos Inc', 'Leidos')
        """)
        conn.commit()
        cursor.execute("SELECT normalized_name FROM companies WHERE id = 'c1'")
        assert cursor.fetchone()[0] == "Leidos"

    def test_insert_contact(self, conn):
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contacts (id, full_name, email, tier)
            VALUES ('ct1', 'John Doe', 'john@example.com', 1)
        """)
        conn.commit()
        cursor.execute("SELECT tier FROM contacts WHERE id = 'ct1'")
        assert cursor.fetchone()[0] == 1

    def test_junction_link(self, conn):
        cursor = conn.cursor()
        cursor.execute("INSERT INTO programs (id, program_name) VALUES ('p1', 'Prog 1')")
        cursor.execute("INSERT INTO contacts (id, full_name) VALUES ('c1', 'Jane')")
        cursor.execute("""
            INSERT INTO program_contacts (id, program_id, contact_id, relationship_type)
            VALUES ('pc1', 'p1', 'c1', 'direct')
        """)
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM program_contacts")
        assert cursor.fetchone()[0] == 1

    def test_program_360_view(self, conn):
        """Test the program_360_view returns data."""
        cursor = conn.cursor()
        cursor.execute("INSERT INTO programs (id, program_name, acronym) VALUES ('p1', 'DCGS', 'DCGS')")
        conn.commit()
        cursor.execute("SELECT * FROM program_360_view WHERE acronym = 'DCGS'")
        row = cursor.fetchone()
        assert row is not None
        assert row["program_name"] == "DCGS"

    def test_bd_pipeline_view(self, conn):
        cursor = conn.cursor()
        cursor.execute("INSERT INTO programs (id, program_name) VALUES ('p1', 'Test')")
        cursor.execute("""
            INSERT INTO scoring (id, entity_type, entity_id, composite_score)
            VALUES ('s1', 'program', 'p1', 85)
        """)
        conn.commit()
        cursor.execute("SELECT pipeline_tier FROM bd_pipeline_view WHERE program_id = 'p1'")
        row = cursor.fetchone()
        assert row is not None
        assert row["pipeline_tier"] == "Hot"

    def test_competitive_landscape_view(self, conn):
        cursor = conn.cursor()
        cursor.execute("INSERT INTO companies (id, name, normalized_name) VALUES ('co1', 'SAIC', 'SAIC')")
        conn.commit()
        cursor.execute("SELECT * FROM competitive_landscape WHERE company_id = 'co1'")
        row = cursor.fetchone()
        assert row is not None

    def test_timeline_urgency(self, conn):
        """Test timeline urgency computation."""
        cursor = conn.cursor()
        cursor.execute("INSERT INTO programs (id, program_name) VALUES ('p1', 'Test')")
        cursor.execute("""
            INSERT INTO timelines (id, event_type, event_date, program_id, days_until_event, urgency)
            VALUES ('t1', 'recompete', date('now', '+30 days'), 'p1', 30, 'Critical')
        """)
        conn.commit()
        cursor.execute("SELECT urgency FROM recompete_calendar WHERE program_id = 'p1'")
        row = cursor.fetchone()
        assert row is not None
        assert row["urgency"] == "Critical"


# =========================================
# Validation Tests
# =========================================

class TestValidation:
    def test_empty_db_validation(self, tmp_db):
        """Validation should run on empty db without crashing."""
        from scripts.master_db.validate import validate
        results = validate(db_path=tmp_db, verbose=False)
        assert "row_counts" in results
        assert "total_issues" in results
