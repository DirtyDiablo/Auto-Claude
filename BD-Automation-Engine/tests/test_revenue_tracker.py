"""Tests for Phase 36A — Revenue Tracker."""

import pytest

from src.revenue.revenue_tracker import (
    RevenueTracker,
    Placement,
    RevenueRecord,
    RevenueSummary,
    MarginAnalysis,
    ConcentrationRisk,
    get_revenue_tracker,
)


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def tracker():
    return RevenueTracker()


@pytest.fixture
def sample_placements():
    return [
        Placement(
            id="p1",
            contractor_name="Alice",
            client="Leidos",
            program="DCGS",
            role_title="Intelligence Analyst",
            bill_rate=120,
            pay_rate=75,
            start_date="2025-01-15",
            rep="Rep-A",
            contact_id="c1",
            status="active",
        ),
        Placement(
            id="p2",
            contractor_name="Bob",
            client="Northrop",
            program="DCGS",
            role_title="Systems Engineer",
            bill_rate=150,
            pay_rate=95,
            start_date="2025-02-01",
            rep="Rep-A",
            contact_id="c2",
            status="active",
        ),
        Placement(
            id="p3",
            contractor_name="Carol",
            client="SAIC",
            program="NGEN",
            role_title="Network Engineer",
            bill_rate=130,
            pay_rate=80,
            start_date="2025-03-01",
            rep="Rep-B",
            contact_id="c3",
            status="active",
        ),
        Placement(
            id="p4",
            contractor_name="Dave",
            client="BAH",
            program="GBSD",
            role_title="Software Engineer",
            bill_rate=140,
            pay_rate=90,
            start_date="2025-01-01",
            end_date="2025-06-30",
            rep="Rep-B",
            contact_id="c4",
            status="completed",
        ),
    ]


@pytest.fixture
def sample_records():
    return [
        RevenueRecord(
            placement_id="p1",
            period="2025-01",
            billed_hours=160,
            bill_amount=19200,
            pay_amount=12000,
            margin=7200,
            margin_pct=37.5,
        ),
        RevenueRecord(
            placement_id="p2",
            period="2025-01",
            billed_hours=160,
            bill_amount=24000,
            pay_amount=15200,
            margin=8800,
            margin_pct=36.7,
        ),
        RevenueRecord(
            placement_id="p1",
            period="2025-02",
            billed_hours=160,
            bill_amount=19200,
            pay_amount=12000,
            margin=7200,
            margin_pct=37.5,
        ),
        RevenueRecord(
            placement_id="p3",
            period="2025-02",
            billed_hours=160,
            bill_amount=20800,
            pay_amount=12800,
            margin=8000,
            margin_pct=38.5,
        ),
        RevenueRecord(
            placement_id="p4",
            period="2025-01",
            billed_hours=160,
            bill_amount=22400,
            pay_amount=14400,
            margin=8000,
            margin_pct=35.7,
        ),
    ]


@pytest.fixture
def loaded_tracker(tracker, sample_placements, sample_records):
    tracker.set_placements(sample_placements)
    for r in sample_records:
        tracker.add_revenue_record(r)
    return tracker


# =========================================
# PLACEMENT MANAGEMENT
# =========================================


class TestPlacementManagement:
    def test_add_placement(self, tracker, sample_placements):
        tracker.add_placement(sample_placements[0])
        assert tracker.get_placement("p1") is not None

    def test_active_placements(self, loaded_tracker):
        active = loaded_tracker.get_active_placements()
        assert len(active) == 3  # p1, p2, p3 active; p4 completed


# =========================================
# REVENUE SUMMARY
# =========================================


class TestRevenueSummary:
    def test_overall_summary(self, loaded_tracker):
        summary = loaded_tracker.get_revenue_summary()
        assert isinstance(summary, RevenueSummary)
        assert summary.total_revenue > 0
        assert summary.total_margin > 0

    def test_period_filtered(self, loaded_tracker):
        summary = loaded_tracker.get_revenue_summary("2025-01")
        assert summary.total_revenue == 19200 + 24000 + 22400  # p1 + p2 + p4

    def test_empty_period(self, loaded_tracker):
        summary = loaded_tracker.get_revenue_summary("2030-01")
        assert summary.total_revenue == 0

    def test_margin_pct(self, loaded_tracker):
        summary = loaded_tracker.get_revenue_summary()
        assert 0 < summary.avg_margin_pct < 100


# =========================================
# REVENUE BY DIMENSION
# =========================================


class TestRevenueByDimension:
    def test_by_program(self, loaded_tracker):
        by_prog = loaded_tracker.get_revenue_by_program()
        assert "DCGS" in by_prog
        assert "NGEN" in by_prog
        assert "GBSD" in by_prog

    def test_dcgs_highest(self, loaded_tracker):
        by_prog = loaded_tracker.get_revenue_by_program()
        programs = list(by_prog.keys())
        assert programs[0] == "DCGS"  # Sorted by revenue desc

    def test_by_rep(self, loaded_tracker):
        by_rep = loaded_tracker.get_revenue_by_rep()
        assert "Rep-A" in by_rep
        assert "Rep-B" in by_rep

    def test_by_contact(self, loaded_tracker):
        by_contact = loaded_tracker.get_revenue_by_contact()
        assert len(by_contact) > 0


# =========================================
# FORECAST
# =========================================


class TestForecast:
    def test_forecast_returns_list(self, loaded_tracker):
        forecast = loaded_tracker.forecast_revenue(6)
        assert isinstance(forecast, list)
        assert len(forecast) == 6

    def test_forecast_has_revenue(self, loaded_tracker):
        forecast = loaded_tracker.forecast_revenue(3)
        assert forecast[0]["projected_revenue"] > 0
        assert forecast[0]["active_placements"] > 0


# =========================================
# MARGIN ANALYSIS
# =========================================


class TestMarginAnalysis:
    def test_margin_analysis(self, loaded_tracker):
        analysis = loaded_tracker.get_margin_analysis()
        assert isinstance(analysis, MarginAnalysis)
        assert analysis.avg_margin_pct > 0

    def test_margin_by_program(self, loaded_tracker):
        analysis = loaded_tracker.get_margin_analysis()
        assert len(analysis.margin_by_program) > 0

    def test_margin_trend(self, loaded_tracker):
        analysis = loaded_tracker.get_margin_analysis()
        assert len(analysis.margin_trend) > 0

    def test_highest_lowest(self, loaded_tracker):
        analysis = loaded_tracker.get_margin_analysis()
        assert analysis.highest_margin_program != ""
        assert analysis.lowest_margin_program != ""

    def test_empty_tracker(self, tracker):
        analysis = tracker.get_margin_analysis()
        assert analysis.avg_margin_pct == 0


# =========================================
# CONCENTRATION RISK
# =========================================


class TestConcentrationRisk:
    def test_concentration_risk(self, loaded_tracker):
        risk = loaded_tracker.get_concentration_risk()
        assert isinstance(risk, ConcentrationRisk)
        assert risk.risk_level in ("low", "moderate", "high", "critical")

    def test_top_programs_listed(self, loaded_tracker):
        risk = loaded_tracker.get_concentration_risk()
        assert len(risk.top_programs) > 0

    def test_hhi_range(self, loaded_tracker):
        risk = loaded_tracker.get_concentration_risk()
        assert 0 <= risk.herfindahl_index <= 1

    def test_diversification_score(self, loaded_tracker):
        risk = loaded_tracker.get_concentration_risk()
        assert 0 <= risk.diversification_score <= 100

    def test_empty_tracker(self, tracker):
        risk = tracker.get_concentration_risk()
        assert risk.risk_level == "low"


# =========================================
# SINGLETON
# =========================================


class TestSingleton:
    def test_get_tracker_returns_instance(self):
        t = get_revenue_tracker()
        assert isinstance(t, RevenueTracker)

    def test_get_tracker_is_singleton(self):
        t1 = get_revenue_tracker()
        t2 = get_revenue_tracker()
        assert t1 is t2
