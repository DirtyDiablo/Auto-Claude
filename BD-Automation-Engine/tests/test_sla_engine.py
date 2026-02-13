"""Tests for Phase 43A — Quality SLA Engine."""

import pytest

from src.governance.sla_engine import (
    SLAEngine,
    QualitySLA,
    SLATarget,
    SLAStatus,
    AlertLevel,
    SLACheckResult,
    get_sla_engine,
)


@pytest.fixture
def engine():
    return SLAEngine()


# =========================================
# SEEDED SLAs
# =========================================

def test_seeded_slas(engine):
    slas = engine.list_slas()
    assert len(slas) >= 3
    ids = {s.id for s in slas}
    assert "sla_contacts_freshness" in ids
    assert "sla_jobs_freshness" in ids
    assert "sla_programs_quality" in ids


def test_get_seeded(engine):
    sla = engine.get("sla_contacts_freshness")
    assert sla is not None
    assert len(sla.targets) == 3


# =========================================
# CRUD
# =========================================

def test_create(engine):
    sla_id = engine.create(QualitySLA(
        name="Test SLA", asset_id="test",
        targets=[SLATarget(metric="accuracy", target_value=0.9, operator=">=")],
    ))
    assert sla_id != ""
    assert engine.get(sla_id) is not None


def test_list_by_asset(engine):
    results = engine.list_slas(asset_id="contacts")
    assert all(s.asset_id == "contacts" for s in results)


def test_update(engine):
    result = engine.update("sla_contacts_freshness", {"description": "Updated"})
    assert result is not None
    assert result.description == "Updated"


def test_delete(engine):
    engine.create(QualitySLA(id="temp", name="Temp"))
    assert engine.delete("temp") is True
    assert engine.get("temp") is None


# =========================================
# CHECK SLA — MEETING
# =========================================

def test_check_meeting(engine):
    result = engine.check_sla("sla_contacts_freshness", {
        "freshness_hours": 48.0,
        "accuracy": 0.99,
        "completeness": 0.99,
    })
    # All targets met, none violated (may be at_risk for near-1.0 thresholds)
    assert result.status in (SLAStatus.MEETING.value, SLAStatus.AT_RISK.value)
    assert result.targets_met == 3
    assert result.targets_violated == 0


# =========================================
# CHECK SLA — VIOLATED
# =========================================

def test_check_violated(engine):
    result = engine.check_sla("sla_jobs_freshness", {
        "freshness_hours": 10.0,  # exceeds 4h max
        "completeness": 0.50,     # below 85%
    })
    assert result.status == SLAStatus.VIOLATED.value
    assert result.targets_violated >= 1
    assert len(result.alerts) >= 1


def test_check_staleness_violation(engine):
    result = engine.check_sla("sla_contacts_freshness", {
        "freshness_hours": 200.0,  # exceeds 168h
        "accuracy": 0.97,
        "completeness": 0.95,
    })
    assert result.targets_violated >= 1
    critical_alerts = [a for a in result.alerts if a.level == AlertLevel.CRITICAL.value]
    assert len(critical_alerts) >= 1


# =========================================
# CHECK SLA — AT RISK
# =========================================

def test_check_at_risk(engine):
    # Just barely meeting — freshness at 167h (threshold 168h, margin < 10%)
    result = engine.check_sla("sla_contacts_freshness", {
        "freshness_hours": 167.0,
        "accuracy": 0.97,
        "completeness": 0.95,
    })
    # Should be meeting but at risk
    assert result.targets_met == 3
    # At risk because margin < 10%
    assert result.targets_at_risk >= 1


# =========================================
# CHECK ALL
# =========================================

def test_check_all(engine):
    metrics = {
        "contacts": {"freshness_hours": 48.0, "accuracy": 0.97, "completeness": 0.95},
        "jobs": {"freshness_hours": 2.0, "completeness": 0.90},
        "programs": {"accuracy": 0.92, "completeness": 0.85, "freshness_hours": 72.0},
    }
    results = engine.check_all(metrics)
    assert len(results) >= 3
    assert all(isinstance(r, SLACheckResult) for r in results)


# =========================================
# ALERTS
# =========================================

def test_alerts_generated(engine):
    engine.check_sla("sla_jobs_freshness", {
        "freshness_hours": 10.0, "completeness": 0.5,
    })
    alerts = engine.get_alerts()
    assert len(alerts) >= 1


def test_alerts_by_sla(engine):
    engine.check_sla("sla_jobs_freshness", {
        "freshness_hours": 10.0, "completeness": 0.5,
    })
    alerts = engine.get_alerts(sla_id="sla_jobs_freshness")
    assert all(a.sla_id == "sla_jobs_freshness" for a in alerts)


def test_acknowledge_alert(engine):
    engine.check_sla("sla_jobs_freshness", {
        "freshness_hours": 10.0, "completeness": 0.5,
    })
    alerts = engine.get_alerts(unacknowledged_only=True)
    assert len(alerts) >= 1
    assert engine.acknowledge_alert(alerts[0].id) is True


def test_acknowledge_nonexistent(engine):
    assert engine.acknowledge_alert("nonexistent") is False


# =========================================
# HISTORY
# =========================================

def test_history(engine):
    engine.check_sla("sla_contacts_freshness", {
        "freshness_hours": 48.0, "accuracy": 0.97, "completeness": 0.95,
    })
    history = engine.get_history(sla_id="sla_contacts_freshness")
    assert len(history) >= 1
    assert history[-1].compliance_pct == 100.0


# =========================================
# STATS
# =========================================

def test_stats(engine):
    stats = engine.get_stats()
    assert stats["total_slas"] >= 3
    assert "by_status" in stats
    assert "compliance_summary" in stats


# =========================================
# EVALUATE TARGET
# =========================================

def test_evaluate_gte():
    assert SLAEngine._evaluate_target(">=", 0.95, 0.90) is True
    assert SLAEngine._evaluate_target(">=", 0.85, 0.90) is False


def test_evaluate_lte():
    assert SLAEngine._evaluate_target("<=", 4.0, 168.0) is True
    assert SLAEngine._evaluate_target("<=", 200.0, 168.0) is False


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    e1 = get_sla_engine()
    e2 = get_sla_engine()
    assert e1 is e2
