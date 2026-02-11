"""Tests for Phase 52A — ABAC Policy Engine."""

import pytest

from src.security.abac_engine import (
    ABACPolicyEngine,
    Subject,
    Resource,
    Environment,
    Policy,
    PolicyDecision,
    Decision,
    ClearanceLevel,
    get_abac_engine,
)


@pytest.fixture
def engine():
    return ABACPolicyEngine()


# =========================================
# ADMIN BYPASS
# =========================================

def test_admin_full_access(engine):
    subject = Subject(user_id="admin1", role="admin")
    resource = Resource(resource_type="contact", resource_id="c1")
    decision = engine.evaluate(subject, "delete", resource)
    assert decision.decision == Decision.ALLOW


def test_admin_bypass_program_isolation(engine):
    subject = Subject(user_id="admin1", role="admin")
    resource = Resource(resource_type="contact", program="DCGS-A")
    decision = engine.evaluate(subject, "read", resource)
    assert decision.decision == Decision.ALLOW


# =========================================
# PROGRAM ISOLATION
# =========================================

def test_program_isolation_deny(engine):
    subject = Subject(user_id="u1", role="analyst", programs_assigned=["JADC2"])
    resource = Resource(resource_type="contact", program="DCGS-A")
    decision = engine.evaluate(subject, "read", resource)
    assert decision.decision == Decision.DENY
    assert "program" in decision.reason.lower()


def test_program_isolation_allow(engine):
    subject = Subject(user_id="u1", role="analyst", programs_assigned=["DCGS-A"])
    resource = Resource(resource_type="contact", program="DCGS-A")
    decision = engine.evaluate(subject, "read", resource)
    assert decision.decision == Decision.ALLOW


def test_program_isolation_no_program(engine):
    subject = Subject(user_id="u1", role="analyst", programs_assigned=["JADC2"])
    resource = Resource(resource_type="contact")  # no program
    decision = engine.evaluate(subject, "read", resource)
    assert decision.decision == Decision.ALLOW


# =========================================
# HUMINT ACCESS
# =========================================

def test_humint_owner_access(engine):
    subject = Subject(user_id="u1", role="analyst")
    resource = Resource(
        resource_type="humint_note", resource_id="hn1", owner_id="u1",
    )
    decision = engine.evaluate(subject, "read", resource)
    assert decision.decision == Decision.ALLOW


def test_humint_bd_director_access(engine):
    subject = Subject(user_id="director1", role="bd_director")
    resource = Resource(
        resource_type="humint_note", resource_id="hn1", owner_id="u1",
    )
    decision = engine.evaluate(subject, "read", resource)
    assert decision.decision == Decision.ALLOW


def test_humint_manager_access(engine):
    subject = Subject(user_id="mgr1", role="manager")
    resource = Resource(
        resource_type="humint_note", resource_id="hn1",
        owner_id="u1", owner_manager_id="mgr1",
    )
    decision = engine.evaluate(subject, "read", resource)
    assert decision.decision == Decision.ALLOW


def test_humint_deny_other_user(engine):
    subject = Subject(user_id="u2", role="analyst")
    resource = Resource(
        resource_type="humint_note", resource_id="hn1",
        owner_id="u1", owner_manager_id="mgr1",
    )
    decision = engine.evaluate(subject, "read", resource)
    assert decision.decision == Decision.DENY
    assert "HUMINT" in decision.reason


# =========================================
# EXPORT THRESHOLD
# =========================================

def test_export_small_batch_allowed(engine):
    subject = Subject(user_id="u1", role="analyst", programs_assigned=["P1"])
    resource = Resource(
        resource_type="export", program="P1", record_count=30,
    )
    decision = engine.evaluate(subject, "export", resource)
    assert decision.decision == Decision.ALLOW


def test_export_large_batch_requires_approval(engine):
    subject = Subject(user_id="u1", role="analyst", programs_assigned=["P1"])
    resource = Resource(
        resource_type="export", program="P1", record_count=100,
    )
    decision = engine.evaluate(subject, "export", resource)
    assert decision.decision == Decision.REQUIRE_APPROVAL


# =========================================
# GEO RESTRICTION
# =========================================

def test_dcgs_us_access_allowed(engine):
    subject = Subject(user_id="u1", role="analyst", programs_assigned=["DCGS-A"])
    resource = Resource(resource_type="contact", program="DCGS-A")
    env = Environment(geo_country="US")
    decision = engine.evaluate(subject, "read", resource, env)
    assert decision.decision == Decision.ALLOW


def test_dcgs_non_us_denied(engine):
    subject = Subject(user_id="u1", role="analyst", programs_assigned=["DCGS-A"])
    resource = Resource(resource_type="contact", program="DCGS-A")
    env = Environment(geo_country="CN")
    decision = engine.evaluate(subject, "read", resource, env)
    assert decision.decision == Decision.DENY
    assert "DCGS" in decision.reason


# =========================================
# NDA / COMPETITOR DATA
# =========================================

def test_competitor_data_with_nda_allowed(engine):
    subject = Subject(
        user_id="u1", role="analyst",
        programs_assigned=["P1"], nda_signed=True,
    )
    resource = Resource(
        resource_type="simulation", program="P1", has_competitor_data=True,
    )
    decision = engine.evaluate(subject, "read", resource)
    assert decision.decision == Decision.ALLOW


def test_competitor_data_without_nda_denied(engine):
    subject = Subject(
        user_id="u1", role="analyst",
        programs_assigned=["P1"], nda_signed=False,
    )
    resource = Resource(
        resource_type="simulation", program="P1", has_competitor_data=True,
    )
    decision = engine.evaluate(subject, "read", resource)
    assert decision.decision == Decision.DENY
    assert "NDA" in decision.reason


# =========================================
# CLEARANCE LEVEL
# =========================================

def test_clearance_sufficient(engine):
    subject = Subject(
        user_id="u1", role="analyst",
        clearance_level=ClearanceLevel.SECRET,
    )
    resource = Resource(
        resource_type="contact",
        classification=ClearanceLevel.CONFIDENTIAL,
    )
    decision = engine.evaluate(subject, "read", resource)
    assert decision.decision == Decision.ALLOW


def test_clearance_insufficient(engine):
    subject = Subject(
        user_id="u1", role="analyst",
        clearance_level=ClearanceLevel.CONFIDENTIAL,
    )
    resource = Resource(
        resource_type="contact",
        classification=ClearanceLevel.TOP_SECRET,
    )
    decision = engine.evaluate(subject, "read", resource)
    assert decision.decision == Decision.DENY
    assert "Clearance" in decision.reason


def test_clearance_equal(engine):
    subject = Subject(
        user_id="u1", role="analyst",
        clearance_level=ClearanceLevel.SECRET,
    )
    resource = Resource(
        resource_type="contact",
        classification=ClearanceLevel.SECRET,
    )
    decision = engine.evaluate(subject, "read", resource)
    assert decision.decision == Decision.ALLOW


# =========================================
# VIEWER READ-ONLY
# =========================================

def test_viewer_can_read(engine):
    subject = Subject(user_id="v1", role="viewer")
    resource = Resource(resource_type="contact")
    decision = engine.evaluate(subject, "read", resource)
    assert decision.decision == Decision.ALLOW


def test_viewer_can_search(engine):
    subject = Subject(user_id="v1", role="viewer")
    resource = Resource(resource_type="contact")
    decision = engine.evaluate(subject, "search", resource)
    assert decision.decision == Decision.ALLOW


def test_viewer_cannot_write(engine):
    subject = Subject(user_id="v1", role="viewer")
    resource = Resource(resource_type="contact")
    decision = engine.evaluate(subject, "update", resource)
    assert decision.decision == Decision.DENY
    assert "read-only" in decision.reason.lower()


def test_viewer_cannot_delete(engine):
    subject = Subject(user_id="v1", role="viewer")
    resource = Resource(resource_type="contact")
    decision = engine.evaluate(subject, "delete", resource)
    assert decision.decision == Decision.DENY


# =========================================
# POLICY MANAGEMENT
# =========================================

def test_list_policies(engine):
    policies = engine.list_policies()
    assert len(policies) == 8


def test_list_enabled_only(engine):
    engine.disable_policy("pol_geo_restriction")
    enabled = engine.list_policies(enabled_only=True)
    all_p = engine.list_policies()
    assert len(enabled) == len(all_p) - 1


def test_get_policy(engine):
    p = engine.get_policy("pol_admin_bypass")
    assert p is not None
    assert p.name == "admin_full_access"


def test_get_policy_not_found(engine):
    assert engine.get_policy("pol_nonexistent") is None


def test_update_policy(engine):
    result = engine.update_policy("pol_admin_bypass", description="Updated desc")
    assert result is not None
    assert result.description == "Updated desc"


def test_disable_policy(engine):
    assert engine.disable_policy("pol_admin_bypass") is True
    p = engine.get_policy("pol_admin_bypass")
    assert not p.enabled


def test_add_custom_policy(engine):
    custom = Policy(
        policy_id="pol_custom_test",
        name="test_policy",
        description="Test custom policy",
        priority=50,
    )
    engine.add_policy(custom)
    assert engine.get_policy("pol_custom_test") is not None


# =========================================
# EXPLAIN & CLASSIFY
# =========================================

def test_explain_allow(engine):
    subject = Subject(user_id="admin1", role="admin")
    resource = Resource(resource_type="contact")
    decision = engine.evaluate(subject, "read", resource)
    explanation = engine.explain_decision(decision)
    assert "GRANTED" in explanation


def test_explain_deny(engine):
    subject = Subject(user_id="u1", role="analyst", programs_assigned=[])
    resource = Resource(resource_type="contact", program="DCGS-A")
    decision = engine.evaluate(subject, "read", resource)
    explanation = engine.explain_decision(decision)
    assert "DENIED" in explanation


def test_classify_humint(engine):
    result = engine.classify_resource("humint_note", {})
    assert result == "restricted"


def test_classify_contact_dcgs(engine):
    result = engine.classify_resource("contact", {"program": "DCGS-A"})
    assert result == "sensitive"


def test_classify_export(engine):
    result = engine.classify_resource("export", {})
    assert result == "confidential"


def test_classify_generic(engine):
    result = engine.classify_resource("report", {})
    assert result == "internal"


# =========================================
# STATS & SINGLETON
# =========================================

def test_stats(engine):
    engine.evaluate(
        Subject(user_id="u1", role="admin"),
        "read",
        Resource(resource_type="contact"),
    )
    stats = engine.get_stats()
    assert stats["total_evaluations"] >= 1
    assert stats["total_policies"] == 8


def test_singleton():
    import src.security.abac_engine as mod
    mod._instance = None
    e1 = get_abac_engine()
    e2 = get_abac_engine()
    assert e1 is e2
    mod._instance = None
