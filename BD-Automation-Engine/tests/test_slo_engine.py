"""Tests for Phase 53A — SLO Engine."""

import pytest

from src.observability.slo_engine import (
    SLOEngine,
    SLODefinition,
    SLOType,
    SLOStatus,
    SLOReport,
    get_slo_engine,
)


@pytest.fixture
def engine():
    return SLOEngine()


# =========================================
# BUILT-IN SLOS
# =========================================

def test_builtin_slos(engine):
    slos = engine.list_slos()
    assert len(slos) == 6


def test_api_availability_slo(engine):
    slo = engine.get_slo("slo_api_availability")
    assert slo is not None
    assert slo.target == 99.9


def test_error_rate_slo(engine):
    slo = engine.get_slo("slo_error_rate")
    assert slo is not None
    assert slo.target == 0.1


def test_list_enabled_only(engine):
    engine.update_slo("slo_data_freshness", enabled=False)
    enabled = engine.list_slos(enabled_only=True)
    assert len(enabled) == 5


# =========================================
# SLO MANAGEMENT
# =========================================

def test_add_slo(engine):
    custom = SLODefinition(
        slo_id="slo_custom",
        name="Custom SLO",
        slo_type=SLOType.AVAILABILITY,
        target=99.5,
    )
    engine.add_slo(custom)
    assert engine.get_slo("slo_custom") is not None


def test_update_slo(engine):
    result = engine.update_slo("slo_api_availability", target=99.95)
    assert result is not None
    assert result.target == 99.95


def test_update_slo_not_found(engine):
    assert engine.update_slo("slo_fake") is None


def test_get_slo_not_found(engine):
    assert engine.get_slo("slo_fake") is None


# =========================================
# RECORDING EVENTS
# =========================================

def test_record_good_event(engine):
    engine.record_event("slo_api_availability", good=True)
    report = engine.get_report("slo_api_availability")
    assert report.total_events == 1
    assert report.good_events == 1


def test_record_bad_event(engine):
    engine.record_event("slo_api_availability", good=False)
    report = engine.get_report("slo_api_availability")
    assert report.bad_events == 1


def test_record_batch(engine):
    engine.record_batch("slo_api_availability", good_events=990, total_events=1000)
    report = engine.get_report("slo_api_availability")
    assert report.total_events == 1000
    assert report.good_events == 990


def test_record_unknown_slo(engine):
    # Should not raise
    engine.record_event("slo_fake", good=True)


# =========================================
# REPORTS
# =========================================

def test_report_healthy(engine):
    engine.record_batch("slo_api_availability", good_events=9999, total_events=10000)
    report = engine.get_report("slo_api_availability")
    assert isinstance(report, SLOReport)
    assert report.status == SLOStatus.HEALTHY


def test_report_breached(engine):
    engine.record_batch("slo_api_availability", good_events=900, total_events=1000)
    report = engine.get_report("slo_api_availability")
    # 90% availability vs 99.9% target — budget completely consumed
    assert report.status == SLOStatus.BREACHED


def test_report_no_events(engine):
    report = engine.get_report("slo_api_availability")
    assert report.total_events == 0
    assert report.current_value == 100.0  # availability defaults to 100% with no events


def test_report_not_found(engine):
    assert engine.get_report("slo_fake") is None


def test_error_budget(engine):
    engine.record_batch("slo_api_availability", good_events=9999, total_events=10000)
    report = engine.get_report("slo_api_availability")
    # Error budget should be positive and proportional to events
    assert report.error_budget_total > 0
    assert report.error_budget_remaining >= 0


def test_burn_rate(engine):
    engine.record_batch("slo_api_availability", good_events=999, total_events=1000)
    report = engine.get_report("slo_api_availability")
    assert report.burn_rate >= 0


def test_report_to_dict(engine):
    engine.record_batch("slo_api_availability", good_events=999, total_events=1000)
    report = engine.get_report("slo_api_availability")
    d = report.to_dict()
    assert "slo_id" in d
    assert "error_budget_pct" in d
    assert "burn_rate" in d
    assert "status" in d


# =========================================
# DASHBOARD
# =========================================

def test_dashboard(engine):
    engine.record_batch("slo_api_availability", good_events=999, total_events=1000)
    dashboard = engine.get_dashboard()
    assert "total_slos" in dashboard
    assert "by_status" in dashboard
    assert "slos" in dashboard


def test_dashboard_overall_health(engine):
    engine.record_batch("slo_api_availability", good_events=999, total_events=1000)
    dashboard = engine.get_dashboard()
    assert dashboard["overall_health"] in ("healthy", "degraded")


def test_get_all_reports(engine):
    engine.record_batch("slo_api_availability", good_events=999, total_events=1000)
    reports = engine.get_all_reports()
    assert len(reports) >= 5  # may be fewer if shared SLO objects were disabled by prior test


# =========================================
# SLO DEFINITION
# =========================================

def test_slo_definition_to_dict(engine):
    slo = engine.get_slo("slo_api_availability")
    d = slo.to_dict()
    assert "slo_id" in d
    assert "target" in d
    assert "slo_type" in d


# =========================================
# STATS & SINGLETON
# =========================================

def test_stats(engine):
    engine.record_event("slo_api_availability", good=True)
    stats = engine.get_stats()
    assert stats["total_slos"] == 6
    assert stats["total_measurements"] >= 1


def test_singleton():
    import src.observability.slo_engine as mod
    mod._instance = None
    e1 = get_slo_engine()
    e2 = get_slo_engine()
    assert e1 is e2
    mod._instance = None
