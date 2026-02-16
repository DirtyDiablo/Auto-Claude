"""Tests for Phase 52A — Immutable Audit Trail."""

import pytest

from src.security.audit_trail import (
    ImmutableAuditTrail,
    AuditActor,
    AuditAction,
    AuditResource,
    AuditFilters,
    ComplianceReport,
    get_audit_trail,
)


@pytest.fixture
def trail():
    return ImmutableAuditTrail()


def _log_sample(trail, user_id="u1", action=AuditAction.READ, rt="contact", rid="c1"):
    return trail.log_event(
        actor=AuditActor(user_id=user_id, role="analyst"),
        action=action,
        resource=AuditResource(resource_type=rt, resource_id=rid),
    )


# =========================================
# LOGGING EVENTS
# =========================================


def test_log_event(trail):
    eid = _log_sample(trail)
    assert eid.startswith("evt_")


def test_logged_event_has_timestamp(trail):
    eid = _log_sample(trail)
    event = trail.get_event(eid)
    assert event is not None
    assert event.timestamp.endswith("Z")


def test_logged_event_has_chain_hash(trail):
    eid = _log_sample(trail)
    event = trail.get_event(eid)
    assert len(event.chain_hash) == 64  # SHA-256 hex


def test_chain_links_events(trail):
    eid1 = _log_sample(trail)
    eid2 = _log_sample(trail, user_id="u2")
    e1 = trail.get_event(eid1)
    e2 = trail.get_event(eid2)
    assert e2.prev_hash == e1.chain_hash


def test_first_event_prev_hash_is_genesis(trail):
    eid = _log_sample(trail)
    event = trail.get_event(eid)
    assert event.prev_hash == "genesis"


def test_log_with_details(trail):
    eid = trail.log_event(
        actor=AuditActor(user_id="u1", role="analyst"),
        action=AuditAction.UPDATE,
        resource=AuditResource(resource_type="contact", resource_id="c1"),
        details={"field": "email", "old": "a@b.com", "new": "c@d.com"},
    )
    event = trail.get_event(eid)
    assert event.details["field"] == "email"


def test_log_with_policy_decision(trail):
    eid = trail.log_event(
        actor=AuditActor(user_id="u1", role="analyst"),
        action=AuditAction.POLICY_EVAL,
        resource=AuditResource(resource_type="contact"),
        policy_decision="deny",
        policy_id="pol_program_isolation",
    )
    event = trail.get_event(eid)
    assert event.policy_decision == "deny"
    assert event.policy_id == "pol_program_isolation"


def test_unique_event_ids(trail):
    eid1 = _log_sample(trail)
    eid2 = _log_sample(trail)
    assert eid1 != eid2


# =========================================
# QUERYING
# =========================================


def test_get_event(trail):
    eid = _log_sample(trail)
    event = trail.get_event(eid)
    assert event.event_id == eid


def test_get_event_not_found(trail):
    assert trail.get_event("evt_nonexistent") is None


def test_query_all(trail):
    _log_sample(trail)
    _log_sample(trail, user_id="u2")
    events = trail.query_trail()
    assert len(events) == 2


def test_query_by_actor(trail):
    _log_sample(trail, user_id="u1")
    _log_sample(trail, user_id="u2")
    events = trail.query_trail(filters=AuditFilters(actor_id="u1"))
    assert len(events) == 1
    assert events[0].actor.user_id == "u1"


def test_query_by_action(trail):
    _log_sample(trail, action=AuditAction.READ)
    _log_sample(trail, action=AuditAction.UPDATE)
    events = trail.query_trail(filters=AuditFilters(action=AuditAction.READ))
    assert len(events) == 1


def test_query_by_resource_type(trail):
    _log_sample(trail, rt="contact")
    _log_sample(trail, rt="program")
    events = trail.query_trail(filters=AuditFilters(resource_type="contact"))
    assert len(events) == 1


def test_query_with_limit(trail):
    for i in range(10):
        _log_sample(trail, user_id=f"u{i}")
    events = trail.query_trail(limit=5)
    assert len(events) == 5


def test_query_with_offset(trail):
    for i in range(10):
        _log_sample(trail, user_id=f"u{i}")
    events = trail.query_trail(limit=5, offset=5)
    assert len(events) == 5


def test_query_reverse_chronological(trail):
    _log_sample(trail, user_id="first")
    _log_sample(trail, user_id="second")
    events = trail.query_trail()
    assert events[0].actor.user_id == "second"


def test_query_resource_trail(trail):
    _log_sample(trail, rt="contact", rid="c1")
    _log_sample(trail, rt="contact", rid="c1")
    _log_sample(trail, rt="contact", rid="c2")
    events = trail.query_resource_trail("contact", "c1")
    assert len(events) == 2


# =========================================
# CHAIN VERIFICATION
# =========================================


def test_verify_empty_chain(trail):
    result = trail.verify_chain()
    assert result.verified is True
    assert result.records_checked == 0


def test_verify_single_event(trail):
    _log_sample(trail)
    result = trail.verify_chain()
    assert result.verified is True
    assert result.records_checked == 1


def test_verify_valid_chain(trail):
    for i in range(20):
        _log_sample(trail, user_id=f"u{i}")
    result = trail.verify_chain()
    assert result.verified is True
    assert result.records_checked == 20


def test_verify_tampered_chain(trail):
    for i in range(5):
        _log_sample(trail, user_id=f"u{i}")
    # Tamper with middle event
    trail._events[2].chain_hash = "tampered_hash"
    result = trail.verify_chain()
    assert result.verified is False
    assert result.broken_at == trail._events[2].event_id


def test_verify_partial_range(trail):
    for i in range(10):
        _log_sample(trail, user_id=f"u{i}")
    result = trail.verify_chain(start_idx=3, end_idx=7)
    assert result.verified is True
    assert result.records_checked == 4


def test_verify_out_of_range(trail):
    _log_sample(trail)
    result = trail.verify_chain(start_idx=10)
    assert result.verified is True
    assert result.records_checked == 0


# =========================================
# COMPLIANCE REPORTS
# =========================================


def test_generate_soc2_report(trail):
    for i in range(10):
        _log_sample(trail, user_id=f"u{i}")
    report = trail.generate_compliance_report(report_type="soc2")
    assert isinstance(report, ComplianceReport)
    assert report.report_type == "soc2"
    assert report.total_events >= 10
    assert report.score > 0


def test_generate_fedramp_report(trail):
    for i in range(10):
        _log_sample(trail, user_id=f"u{i}")
    report = trail.generate_compliance_report(report_type="fedramp")
    assert report.report_type == "fedramp"


def test_report_has_unique_id(trail):
    _log_sample(trail)
    r1 = trail.generate_compliance_report()
    r2 = trail.generate_compliance_report()
    assert r1.report_id != r2.report_id


def test_report_coverage(trail):
    _log_sample(trail, action=AuditAction.READ)
    _log_sample(trail, action=AuditAction.CREATE)
    _log_sample(trail, action=AuditAction.UPDATE)
    report = trail.generate_compliance_report()
    assert "action_types" in report.coverage


def test_report_to_dict(trail):
    _log_sample(trail)
    report = trail.generate_compliance_report()
    d = report.to_dict()
    assert "report_id" in d
    assert "score" in d
    assert "findings" in d


def test_report_counts_denials(trail):
    trail.log_event(
        actor=AuditActor(user_id="u1"),
        action=AuditAction.POLICY_EVAL,
        resource=AuditResource(resource_type="contact"),
        policy_decision="deny",
    )
    report = trail.generate_compliance_report()
    assert report.total_denials >= 1


# =========================================
# SOC2 / FEDRAMP READINESS
# =========================================


def test_soc2_readiness(trail):
    trail.log_event(
        actor=AuditActor(user_id="u1"),
        action=AuditAction.LOGIN,
        resource=AuditResource(resource_type="session"),
    )
    trail.log_event(
        actor=AuditActor(user_id="u1"),
        action=AuditAction.POLICY_EVAL,
        resource=AuditResource(resource_type="contact"),
    )
    result = trail.soc2_readiness()
    assert result["framework"] == "SOC 2 Type II"
    assert result["passed"] >= 3
    assert result["score"] > 0


def test_fedramp_readiness(trail):
    trail.log_event(
        actor=AuditActor(user_id="u1"),
        action=AuditAction.ENCRYPT,
        resource=AuditResource(resource_type="field"),
    )
    for i in range(5):
        _log_sample(trail, user_id=f"u{i}")
    result = trail.fedramp_readiness()
    assert result["framework"] == "FedRAMP Moderate"
    assert result["passed"] >= 3


def test_soc2_empty_trail(trail):
    result = trail.soc2_readiness()
    assert result["score"] >= 0


# =========================================
# TO_DICT / STATS
# =========================================


def test_event_to_dict(trail):
    eid = _log_sample(trail)
    event = trail.get_event(eid)
    d = event.to_dict()
    assert "event_id" in d
    assert "chain_hash" in d
    assert "actor" in d


def test_chain_verification_to_dict(trail):
    _log_sample(trail)
    result = trail.verify_chain()
    d = result.to_dict()
    assert "verified" in d
    assert "records_checked" in d


def test_stats(trail):
    _log_sample(trail, action=AuditAction.READ)
    _log_sample(trail, action=AuditAction.READ)
    _log_sample(trail, action=AuditAction.UPDATE)
    stats = trail.get_stats()
    assert stats["total_events"] == 3
    assert stats["by_action"]["read"] == 2
    assert stats["chain_verified"] is True


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    import src.security.audit_trail as mod

    mod._instance = None
    t1 = get_audit_trail()
    t2 = get_audit_trail()
    assert t1 is t2
    mod._instance = None
