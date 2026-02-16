"""Tests for Phase 38A — Data Quality Engine."""

import pytest
from datetime import datetime, timezone, timedelta

from src.data_quality.engine import (
    DataQualityEngine,
    DataQualityRule,
    DataQualityReport,
    RecordQualityScore,
    QualityTrend,
    validate_email,
    validate_phone,
    classify_title_tier,
    check_location_program,
    compute_freshness_score,
    detect_duplicates,
    get_quality_engine,
)


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def engine():
    return DataQualityEngine()


@pytest.fixture
def loaded_engine(engine):
    """Engine with sample data loaded."""
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=10)).isoformat()
    stale = (now - timedelta(days=120)).isoformat()

    engine.set_data(
        "contacts",
        [
            {
                "id": "c1",
                "first_name": "John",
                "last_name": "Smith",
                "email": "john@acme.com",
                "phone": "+12025551234",
                "job_title": "Vice President",
                "hierarchy_tier": 2,
                "location": "San Diego, CA",
                "program": "AF DCGS - PACAF",
                "last_updated": recent,
            },
            {
                "id": "c2",
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@bad",
                "phone": "555",
                "job_title": "Analyst",
                "hierarchy_tier": 5,
                "location": "Langley, VA",
                "program": "AF DCGS - Langley",
                "last_updated": stale,
            },
            {
                "id": "c3",
                "first_name": "",
                "last_name": "Brown",
                "email": "",
                "phone": "",
                "job_title": "Director",
                "hierarchy_tier": 5,
                "location": "San Diego, CA",
                "program": "WRONG PROGRAM",
                "last_updated": recent,
            },
        ],
    )

    engine.set_data(
        "programs",
        [
            {
                "id": "p1",
                "name": "AF DCGS - PACAF",
                "contract_value": 500_000_000,
                "contract_end": (now + timedelta(days=365)).isoformat(),
            },
            {
                "id": "p2",
                "name": "",
                "contract_value": -100,
                "contract_end": (now - timedelta(days=30)).isoformat(),
            },
        ],
    )

    engine.set_data(
        "jobs",
        [
            {
                "id": "j1",
                "title": "Systems Engineer",
                "location": "San Diego",
                "clearance": "top_secret",
                "program": "DCGS",
                "url": "https://example.com/job1",
            },
            {
                "id": "j2",
                "title": "",
                "location": "",
                "clearance": "INVALID_LEVEL",
                "program": "",
                "url": "",
            },
        ],
    )

    engine.set_data(
        "enrichments",
        [
            {"id": "e1", "embedding": [0.1, 0.2, 0.3], "confidence": 0.95},
            {"id": "e2", "embedding": None, "confidence": 0.4},
        ],
    )

    return engine


# =========================================
# VALIDATION HELPERS
# =========================================


class TestValidateEmail:
    def test_valid_email(self):
        valid, msg = validate_email("user@example.com")
        assert valid is True

    def test_empty_email(self):
        valid, msg = validate_email("")
        assert valid is False

    def test_invalid_format(self):
        valid, msg = validate_email("not_an_email")
        assert valid is False

    def test_disposable_domain(self):
        valid, msg = validate_email("user@mailinator.com")
        assert valid is False

    def test_whitespace_stripped(self):
        valid, msg = validate_email("  user@example.com  ")
        assert valid is True


class TestValidatePhone:
    def test_e164_format(self):
        valid, msg = validate_phone("+12025551234")
        assert valid is True

    def test_loose_format(self):
        valid, msg = validate_phone("(202) 555-1234")
        assert valid is True

    def test_empty_phone(self):
        valid, msg = validate_phone("")
        assert valid is False

    def test_too_short(self):
        valid, msg = validate_phone("123")
        assert valid is False


class TestClassifyTitleTier:
    def test_ceo_tier_1(self):
        assert classify_title_tier("Chief Executive Officer") == 1

    def test_vp_tier_2(self):
        assert classify_title_tier("Vice President of Engineering") == 2

    def test_director_tier_2(self):
        assert classify_title_tier("Senior Director") == 2

    def test_manager_tier_3(self):
        assert classify_title_tier("Program Manager") == 3

    def test_lead_tier_4(self):
        assert classify_title_tier("Technical Lead") == 4

    def test_analyst_tier_5(self):
        assert classify_title_tier("Intelligence Analyst") == 5

    def test_intern_tier_6(self):
        assert classify_title_tier("Summer Intern") == 6

    def test_empty_returns_6(self):
        assert classify_title_tier("") == 6


class TestLocationProgram:
    def test_san_diego_pacaf(self):
        consistent, msg = check_location_program("San Diego, CA", "AF DCGS - PACAF")
        assert consistent is True

    def test_san_diego_wrong_program(self):
        consistent, msg = check_location_program("San Diego, CA", "AF DCGS - Langley")
        assert consistent is False

    def test_langley_correct(self):
        consistent, msg = check_location_program("Langley, VA", "AF DCGS - Langley")
        assert consistent is True

    def test_unmapped_location(self):
        consistent, msg = check_location_program("Austin, TX", "Whatever")
        assert consistent is True

    def test_empty_location(self):
        consistent, msg = check_location_program("", "Something")
        assert consistent is True


class TestFreshnessScore:
    def test_recent_high_score(self):
        recent = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        assert compute_freshness_score(recent) > 90

    def test_old_low_score(self):
        old = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        assert compute_freshness_score(old) == 0.0

    def test_empty_zero_score(self):
        assert compute_freshness_score("") == 0.0

    def test_boundary_90_days(self):
        boundary = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        assert compute_freshness_score(boundary) == 0.0


class TestDuplicateDetection:
    def test_finds_duplicates(self):
        records = [
            {"name": "John Smith", "email": "john@acme.com"},
            {"name": "John Smith", "email": "john@acme.com"},
        ]
        dups = detect_duplicates(records, ["name", "email"])
        assert len(dups) == 1
        assert dups[0][2] >= 0.85

    def test_no_false_positives(self):
        records = [
            {"name": "John Smith", "email": "john@acme.com"},
            {"name": "Jane Doe", "email": "jane@other.com"},
        ]
        dups = detect_duplicates(records, ["name", "email"])
        assert len(dups) == 0


# =========================================
# FULL AUDIT
# =========================================


class TestFullAudit:
    def test_audit_returns_report(self, loaded_engine):
        report = loaded_engine.run_full_audit()
        assert isinstance(report, DataQualityReport)
        assert report.overall_score >= 0
        assert report.overall_score <= 100

    def test_audit_finds_issues(self, loaded_engine):
        report = loaded_engine.run_full_audit()
        assert len(report.all_issues) > 0

    def test_audit_domain_scores(self, loaded_engine):
        report = loaded_engine.run_full_audit()
        assert "contacts" in report.domain_scores
        assert "programs" in report.domain_scores
        assert "jobs" in report.domain_scores
        assert "enrichments" in report.domain_scores

    def test_audit_dimension_scores(self, loaded_engine):
        report = loaded_engine.run_full_audit()
        assert len(report.dimension_scores) > 0

    def test_audit_finds_critical(self, loaded_engine):
        report = loaded_engine.run_full_audit()
        # c3 has missing name, wrong program — critical issues
        assert len(report.critical_issues) > 0

    def test_audit_auto_fixable(self, loaded_engine):
        report = loaded_engine.run_full_audit()
        assert report.auto_fixable_count > 0

    def test_audit_recommendations(self, loaded_engine):
        report = loaded_engine.run_full_audit()
        assert len(report.recommendations) > 0

    def test_audit_records_audited(self, loaded_engine):
        report = loaded_engine.run_full_audit()
        assert (
            report.records_audited == 9
        )  # 3 contacts + 2 programs + 2 jobs + 2 enrichments

    def test_empty_data_perfect_score(self, engine):
        report = engine.run_full_audit()
        assert report.overall_score == 100.0

    def test_trend_stable_first_run(self, loaded_engine):
        report = loaded_engine.run_full_audit()
        assert report.trend == QualityTrend.STABLE


# =========================================
# SINGLE RECORD SCORING
# =========================================


class TestSingleRecordScoring:
    def test_perfect_contact(self, engine):
        record = {
            "id": "c1",
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@acme.com",
            "phone": "+12025551234",
            "job_title": "Vice President",
            "hierarchy_tier": 2,
            "location": "San Diego",
            "program": "AF DCGS - PACAF",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        score = engine.score_single_record("contacts", record)
        assert isinstance(score, RecordQualityScore)
        assert score.overall_score >= 80

    def test_bad_contact_low_score(self, engine):
        record = {
            "id": "c2",
            "first_name": "",
            "last_name": "",
            "email": "bad_email",
            "phone": "x",
            "job_title": "VP",
            "hierarchy_tier": 6,
            "location": "San Diego",
            "program": "WRONG",
        }
        score = engine.score_single_record("contacts", record)
        assert score.overall_score < 60
        assert len(score.issues) > 0

    def test_single_record_dimensions(self, engine):
        record = {
            "id": "j1",
            "title": "",
            "clearance": "INVALID",
            "location": "",
            "program": "",
        }
        score = engine.score_single_record("jobs", record)
        assert len(score.dimension_scores) > 0


# =========================================
# ISSUES & HEALTH
# =========================================


class TestIssuesAndHealth:
    def test_get_issues_filtered(self, loaded_engine):
        loaded_engine.run_full_audit()
        issues = loaded_engine.get_issues(domain="contacts")
        assert all(i.domain == "contacts" for i in issues)

    def test_get_issues_by_severity(self, loaded_engine):
        loaded_engine.run_full_audit()
        issues = loaded_engine.get_issues(severity="critical")
        assert all(i.severity == "critical" for i in issues)

    def test_health_summary(self, loaded_engine):
        loaded_engine.run_full_audit()
        health = loaded_engine.get_health_summary()
        assert "overall_score" in health
        assert "total_issues" in health

    def test_trends(self, loaded_engine):
        loaded_engine.run_full_audit()
        loaded_engine.run_full_audit()
        trends = loaded_engine.get_trends()
        assert len(trends) == 2


# =========================================
# RULES
# =========================================


class TestRules:
    def test_default_rules_registered(self, engine):
        rules = engine.get_rules()
        assert len(rules) >= 19

    def test_add_custom_rule(self, engine):
        rule = DataQualityRule(
            name="custom_check",
            dimension="validity",
            domain="contacts",
            severity="low",
            description="Custom test rule",
        )
        engine.add_rule(rule)
        assert any(r.name == "custom_check" for r in engine.get_rules())


# =========================================
# SINGLETON
# =========================================


class TestSingleton:
    def test_get_engine(self):
        e = get_quality_engine()
        assert isinstance(e, DataQualityEngine)

    def test_singleton(self):
        e1 = get_quality_engine()
        e2 = get_quality_engine()
        assert e1 is e2
