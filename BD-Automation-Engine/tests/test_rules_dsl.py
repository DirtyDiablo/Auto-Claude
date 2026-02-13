"""Tests for Phase 38A — Quality Rules DSL."""

import pytest

from src.data_quality.rules_dsl import (
    QualityRulesDSL,
    ValidationResult,
    ReloadResult,
    get_rules_dsl,
)
from src.data_quality.engine import DataQualityRule


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def dsl():
    return QualityRulesDSL()


@pytest.fixture
def sample_rules():
    return {
        "contacts": [
            {"rule": "email_check", "dimension": "validity",
             "severity": "high", "description": "Email must be valid",
             "impact_score": 0.8},
            {"rule": "name_check", "dimension": "completeness",
             "severity": "critical", "description": "Name required",
             "impact_score": 0.9},
        ],
        "programs": [
            {"rule": "contract_active", "dimension": "freshness",
             "severity": "high", "description": "Contract not expired",
             "impact_score": 0.85},
        ],
    }


# =========================================
# LOADING
# =========================================

class TestLoading:
    def test_load_from_dict(self, dsl, sample_rules):
        rules = dsl.load_rules_from_dict(sample_rules)
        assert len(rules) == 3

    def test_load_sets_domain(self, dsl, sample_rules):
        rules = dsl.load_rules_from_dict(sample_rules)
        contact_rules = [r for r in rules if r.domain == "contacts"]
        assert len(contact_rules) == 2

    def test_load_preserves_fields(self, dsl, sample_rules):
        rules = dsl.load_rules_from_dict(sample_rules)
        email = [r for r in rules if r.name == "email_check"][0]
        assert email.dimension == "validity"
        assert email.severity == "high"
        assert email.impact_score == 0.8

    def test_load_skips_unknown_domain(self, dsl):
        rules = dsl.load_rules_from_dict({
            "unknown_domain": [{"rule": "test", "dimension": "validity"}],
        })
        assert len(rules) == 0

    def test_load_skips_empty_name(self, dsl):
        rules = dsl.load_rules_from_dict({
            "contacts": [{"rule": "", "dimension": "validity"}],
        })
        assert len(rules) == 0

    def test_get_rules(self, dsl, sample_rules):
        dsl.load_rules_from_dict(sample_rules)
        assert len(dsl.get_rules()) == 3

    def test_get_rule_by_name(self, dsl, sample_rules):
        dsl.load_rules_from_dict(sample_rules)
        rule = dsl.get_rule("email_check")
        assert rule is not None
        assert rule.name == "email_check"

    def test_load_history(self, dsl, sample_rules):
        dsl.load_rules_from_dict(sample_rules)
        history = dsl.get_load_history()
        assert len(history) == 1
        assert history[0]["rules_loaded"] == 3


# =========================================
# VALIDATION
# =========================================

class TestValidation:
    def test_valid_rules(self, dsl, sample_rules):
        rules = dsl.load_rules_from_dict(sample_rules)
        result = dsl.validate_rules(rules)
        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert result.rule_count == 3

    def test_invalid_dimension(self, dsl):
        rule = DataQualityRule(
            name="bad", dimension="invalid_dim", domain="contacts",
            severity="high",
        )
        result = dsl.validate_rules([rule])
        assert result.valid is False
        assert len(result.errors) > 0

    def test_invalid_domain(self, dsl):
        rule = DataQualityRule(
            name="bad", dimension="validity", domain="bad_domain",
            severity="high",
        )
        result = dsl.validate_rules([rule])
        assert result.valid is False

    def test_invalid_severity(self, dsl):
        rule = DataQualityRule(
            name="bad", dimension="validity", domain="contacts",
            severity="extreme",
        )
        result = dsl.validate_rules([rule])
        assert result.valid is False

    def test_duplicate_names(self, dsl):
        rules = [
            DataQualityRule(name="dup", dimension="validity",
                          domain="contacts", severity="high"),
            DataQualityRule(name="dup", dimension="accuracy",
                          domain="contacts", severity="low"),
        ]
        result = dsl.validate_rules(rules)
        assert result.valid is False
        assert any("Duplicate" in e.message for e in result.errors)

    def test_impact_score_warning(self, dsl):
        rule = DataQualityRule(
            name="ok", dimension="validity", domain="contacts",
            severity="high", impact_score=1.5,
        )
        result = dsl.validate_rules([rule])
        assert len(result.warnings) > 0


# =========================================
# HOT RELOAD
# =========================================

class TestHotReload:
    def test_reload_adds_new(self, dsl, sample_rules):
        dsl.load_rules_from_dict(sample_rules)
        new_rules = {
            "contacts": [
                {"rule": "email_check", "dimension": "validity", "severity": "high"},
                {"rule": "new_rule", "dimension": "accuracy", "severity": "medium"},
            ],
        }
        result = dsl.hot_reload(new_rules)
        assert isinstance(result, ReloadResult)
        assert result.success is True
        assert "new_rule" in result.added

    def test_reload_removes_old(self, dsl, sample_rules):
        dsl.load_rules_from_dict(sample_rules)
        new_rules = {
            "contacts": [
                {"rule": "email_check", "dimension": "validity", "severity": "high"},
            ],
        }
        result = dsl.hot_reload(new_rules)
        assert result.success is True
        assert "name_check" in result.removed
        assert "contract_active" in result.removed

    def test_reload_detects_modified(self, dsl, sample_rules):
        dsl.load_rules_from_dict(sample_rules)
        new_rules = {
            "contacts": [
                {"rule": "email_check", "dimension": "validity",
                 "severity": "critical"},  # Changed from high to critical
                {"rule": "name_check", "dimension": "completeness",
                 "severity": "critical"},
            ],
            "programs": [
                {"rule": "contract_active", "dimension": "freshness",
                 "severity": "high"},
            ],
        }
        result = dsl.hot_reload(new_rules)
        assert result.success is True
        assert "email_check" in result.modified

    def test_reload_counts_unchanged(self, dsl, sample_rules):
        dsl.load_rules_from_dict(sample_rules)
        # Reload with same rules
        result = dsl.hot_reload(sample_rules)
        assert result.success is True
        assert result.unchanged == 3

    def test_reload_fails_on_invalid(self, dsl, sample_rules):
        dsl.load_rules_from_dict(sample_rules)
        new_rules = {
            "contacts": [
                {"rule": "bad", "dimension": "INVALID", "severity": "high"},
            ],
        }
        result = dsl.hot_reload(new_rules)
        assert result.success is False
        assert len(result.errors) > 0


# =========================================
# EXPORT
# =========================================

class TestExport:
    def test_export_rules(self, dsl, sample_rules):
        dsl.load_rules_from_dict(sample_rules)
        exported = dsl.export_rules()
        assert "contacts" in exported
        assert "programs" in exported
        assert len(exported["contacts"]) == 2

    def test_roundtrip(self, dsl, sample_rules):
        dsl.load_rules_from_dict(sample_rules)
        exported = dsl.export_rules()
        # Reload from exported
        dsl2 = QualityRulesDSL()
        rules = dsl2.load_rules_from_dict(exported)
        assert len(rules) == 3


# =========================================
# SINGLETON
# =========================================

class TestSingleton:
    def test_get_dsl(self):
        d = get_rules_dsl()
        assert isinstance(d, QualityRulesDSL)

    def test_singleton(self):
        d1 = get_rules_dsl()
        d2 = get_rules_dsl()
        assert d1 is d2
