"""Tests for Phase 38A — Self-Healing Pipeline."""

import pytest

from src.data_quality.self_healer import (
    SelfHealingPipeline,
    AutoFixResult,
    FixStatus,
    fix_email_normalize,
    fix_phone_format,
    fix_name_capitalize,
    fix_title_standardize,
    fix_location_geocode,
    fix_program_from_location,
    fix_tier_from_title,
    fix_clearance_normalize,
    fix_date_format,
    fix_value_normalize,
    fix_linkedin_url,
    get_self_healer,
)
from src.data_quality.engine import DataIssue


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def healer():
    return SelfHealingPipeline(confidence_threshold=0.85)


def _make_issue(
    field="email", value="bad", domain="contacts", auto_fixable=True,
    severity="high", record_id="c1", suggested_fix=None,
):
    return DataIssue(
        id="test_issue", domain=domain, dimension="validity",
        record_id=record_id, record_type="contact",
        field_name=field, current_value=value,
        expected_pattern="valid", severity=severity,
        description=f"Invalid {field}", auto_fixable=auto_fixable,
        suggested_fix=suggested_fix,
    )


# =========================================
# FIX FUNCTIONS
# =========================================

class TestEmailNormalizer:
    def test_lowercase(self):
        fixed, conf = fix_email_normalize("John@ACME.com")
        assert fixed == "john@acme.com"
        assert conf > 0.9

    def test_strip_whitespace(self):
        fixed, conf = fix_email_normalize("  user@example.com  ")
        assert fixed == "user@example.com"

    def test_fix_con_typo(self):
        fixed, conf = fix_email_normalize("user@gmail.con")
        assert fixed == "user@gmail.com"
        assert conf >= 0.95

    def test_fix_cmo_typo(self):
        fixed, conf = fix_email_normalize("user@yahoo.cmo")
        assert fixed == "user@yahoo.com"

    def test_empty_returns_none(self):
        fixed, conf = fix_email_normalize("")
        assert fixed is None


class TestPhoneFormatter:
    def test_10_digit_us(self):
        fixed, conf = fix_phone_format("2025551234")
        assert fixed == "+12025551234"
        assert conf >= 0.9

    def test_11_digit_us(self):
        fixed, conf = fix_phone_format("12025551234")
        assert fixed == "+12025551234"

    def test_formatted_us(self):
        fixed, conf = fix_phone_format("(202) 555-1234")
        assert "+1" in fixed or "202" in fixed
        assert conf > 0.8

    def test_empty_returns_none(self):
        fixed, conf = fix_phone_format("")
        assert fixed is None


class TestNameCapitalizer:
    def test_all_caps(self):
        fixed, conf = fix_name_capitalize("JOHN SMITH")
        assert fixed == "John Smith"
        assert conf > 0.9

    def test_all_lowercase(self):
        fixed, conf = fix_name_capitalize("john smith")
        assert fixed == "John Smith"

    def test_mc_prefix(self):
        fixed, conf = fix_name_capitalize("MCDONALD")
        assert fixed == "Mcdonald" or fixed == "McDonald"

    def test_already_proper(self):
        fixed, conf = fix_name_capitalize("John Smith")
        assert fixed == "John Smith"
        assert conf == 1.0

    def test_empty(self):
        fixed, conf = fix_name_capitalize("")
        assert fixed is None


class TestTitleStandardizer:
    def test_sr_to_senior(self):
        fixed, conf = fix_title_standardize("Sr. Engineer")
        assert "Senior" in fixed
        assert conf > 0.9

    def test_vp_to_vice_president(self):
        fixed, conf = fix_title_standardize("VP of Sales")
        assert "Vice President" in fixed

    def test_mgr_to_manager(self):
        fixed, conf = fix_title_standardize("Project Mgr")
        assert "Manager" in fixed

    def test_no_change_needed(self):
        fixed, conf = fix_title_standardize("Software Engineer")
        assert fixed == "Software Engineer"
        assert conf == 1.0


class TestLocationGeocoder:
    def test_known_location(self):
        fixed, conf = fix_location_geocode("san diego, ca")
        assert fixed == "San Diego, CA"
        assert conf > 0.9

    def test_langley(self):
        fixed, conf = fix_location_geocode("langley, va")
        assert fixed == "Langley, VA"

    def test_all_caps_normalize(self):
        fixed, conf = fix_location_geocode("NEW YORK")
        assert fixed == "New York"

    def test_already_formatted(self):
        fixed, conf = fix_location_geocode("San Diego, CA")
        assert conf >= 0.97  # Known location map returns high confidence


class TestProgramFromLocation:
    def test_san_diego_to_pacaf(self):
        program, conf = fix_program_from_location("San Diego, CA")
        assert program == "AF DCGS - PACAF"
        assert conf > 0.9

    def test_langley_to_langley(self):
        program, conf = fix_program_from_location("Langley, VA")
        assert program == "AF DCGS - Langley"

    def test_unknown_location(self):
        program, conf = fix_program_from_location("Austin, TX")
        assert program is None


class TestTierFromTitle:
    def test_vp_tier_2(self):
        tier, conf = fix_tier_from_title("Vice President")
        assert tier == 2
        assert conf > 0.9

    def test_analyst_tier_5(self):
        tier, conf = fix_tier_from_title("Intelligence Analyst")
        assert tier == 5


class TestClearanceNormalize:
    def test_ts_sci(self):
        fixed, conf = fix_clearance_normalize("TS/SCI")
        assert fixed == "ts_sci"
        assert conf > 0.9

    def test_top_secret(self):
        fixed, conf = fix_clearance_normalize("Top Secret")
        assert fixed == "top_secret"

    def test_unknown(self):
        fixed, conf = fix_clearance_normalize("Special Access")
        assert conf == 0.5


class TestDateFormat:
    def test_us_format(self):
        fixed, conf = fix_date_format("01/15/2025")
        assert "2025" in fixed
        assert conf > 0.9

    def test_empty(self):
        fixed, conf = fix_date_format("")
        assert fixed is None


class TestValueNormalize:
    def test_500m(self):
        value, conf = fix_value_normalize("500M")
        assert value == 500_000_000
        assert conf > 0.8

    def test_dollar_sign(self):
        value, conf = fix_value_normalize("$1,000,000")
        assert value == 1_000_000

    def test_numeric_passthrough(self):
        value, conf = fix_value_normalize(500)
        assert value == 500
        assert conf == 1.0


class TestLinkedinFixer:
    def test_add_https(self):
        fixed, conf = fix_linkedin_url("http://www.linkedin.com/in/jsmith")
        assert fixed.startswith("https://")

    def test_already_valid(self):
        fixed, conf = fix_linkedin_url("https://www.linkedin.com/in/jsmith")
        assert conf == 1.0

    def test_empty(self):
        fixed, conf = fix_linkedin_url("")
        assert fixed is None


# =========================================
# HEALING PIPELINE
# =========================================

class TestHealingPipeline:
    def test_heal_auto_fixable(self, healer):
        issues = [_make_issue(field="email", value="USER@GMAIL.CON")]
        results = healer.heal(issues)
        assert len(results) == 1
        assert results[0].status == FixStatus.FIXED.value

    def test_skip_non_fixable(self, healer):
        issues = [_make_issue(auto_fixable=False)]
        results = healer.heal(issues)
        assert results[0].status == FixStatus.SKIPPED.value

    def test_confidence_threshold(self):
        healer = SelfHealingPipeline(confidence_threshold=0.99)
        issues = [_make_issue(field="email", value="user@gmail.con")]
        results = healer.heal(issues)
        # 0.95 < 0.99 threshold, should skip
        assert results[0].status == FixStatus.SKIPPED.value

    def test_audit_log(self, healer):
        issues = [_make_issue(field="email", value="USER@GMAIL.COM")]
        healer.heal(issues)
        log = healer.get_audit_log()
        assert len(log) >= 1

    def test_heal_with_suggested_fix(self, healer):
        issues = [_make_issue(
            field="hierarchy_tier", value=5,
            suggested_fix=2, domain="contacts",
        )]
        results = healer.heal(issues)
        fixed = [r for r in results if r.status == FixStatus.FIXED.value]
        assert len(fixed) == 1
        assert fixed[0].new_value == 2

    def test_cascading_title_change(self, healer):
        healer.set_records("contacts", [
            {"id": "c1", "job_title": "Sr. Engineer", "hierarchy_tier": 3},
        ])
        issues = [_make_issue(
            field="job_title", value="Sr. Engineer",
            suggested_fix="Senior Engineer", record_id="c1",
        )]
        results = healer.heal(issues)
        # Title fix should cascade to tier recalculation
        fixed_results = [r for r in results if r.status == FixStatus.FIXED.value]
        assert len(fixed_results) >= 1
        # Check cascading
        cascading = fixed_results[0].cascading_fixes
        assert len(cascading) >= 1

    def test_cascading_location_change(self, healer):
        healer.set_records("contacts", [
            {"id": "c1", "location": "hampton, va", "program": "Unknown"},
        ])
        issues = [_make_issue(
            field="location", value="hampton, va",
            suggested_fix="Hampton, VA", record_id="c1",
        )]
        results = healer.heal(issues)
        fixed = [r for r in results if r.status == FixStatus.FIXED.value]
        assert len(fixed) >= 1
        # Should cascade to program reassignment
        cascading = fixed[0].cascading_fixes
        assert len(cascading) >= 1
        assert any(c.issue.field_name == "program" for c in cascading)


class TestBatchValidation:
    def test_validate_contacts(self, healer):
        records = [
            {"email": "USER@GMAIL.COM", "phone": "2025551234"},
            {"email": "valid@test.com", "phone": "+12025559999"},
        ]
        results = healer.validate_batch(records, "contacts")
        assert len(results) == 2
        # First record email should be lowercased
        assert results[0]["record"]["email"] == "user@gmail.com"


# =========================================
# SINGLETON
# =========================================

class TestSingleton:
    def test_get_healer(self):
        h = get_self_healer()
        assert isinstance(h, SelfHealingPipeline)

    def test_singleton(self):
        h1 = get_self_healer()
        h2 = get_self_healer()
        assert h1 is h2
