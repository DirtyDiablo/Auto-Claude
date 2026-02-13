"""Tests for Phase 36A — Executive Revenue Analytics."""

import pytest

from src.revenue.executive_analytics import (
    ExecutiveAnalytics,
    ExecutiveSummary,
    DiversificationScore,
    PeriodComparison,
    get_executive_analytics,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def analytics():
    ea = ExecutiveAnalytics()
    ea.set_revenue_data({
        "2025-01": 85000,
        "2025-02": 92000,
        "2025-03": 78000,
        "2024-12": 70000,
    })
    ea.set_targets({
        "2025-01": 100000,
        "2025-02": 100000,
        "2025-03": 100000,
    })
    ea.set_rep_data([
        {"rep": "Rep-A", "revenue": 55000, "quota": 50000, "placements": 5},
        {"rep": "Rep-B", "revenue": 30000, "quota": 50000, "placements": 2},
    ])
    ea.set_program_revenue({
        "DCGS": 120000,
        "NGEN": 40000,
        "GBSD": 30000,
        "PACAF": 10000,
    })
    ea.set_pipeline_data([
        {"value": 200000, "stage": "interview"},
        {"value": 150000, "stage": "offer"},
        {"value": 80000, "stage": "discovery"},
    ])
    ea.set_placement_metrics(active=15, new=3, avg_margin=35.0)
    return ea


@pytest.fixture
def empty_analytics():
    return ExecutiveAnalytics()


# =========================================
# QUOTA ATTAINMENT
# =========================================

class TestQuotaAttainment:
    def test_returns_list(self, analytics):
        attainment = analytics.get_quota_attainment()
        assert isinstance(attainment, list)
        assert len(attainment) == 2

    def test_rep_a_over_quota(self, analytics):
        attainment = analytics.get_quota_attainment()
        rep_a = [a for a in attainment if a.rep == "Rep-A"][0]
        assert rep_a.attainment_pct == 110.0

    def test_ranked(self, analytics):
        attainment = analytics.get_quota_attainment()
        assert attainment[0].rank == 1
        assert attainment[0].attainment_pct >= attainment[1].attainment_pct


# =========================================
# DIVERSIFICATION SCORE
# =========================================

class TestDiversificationScore:
    def test_returns_score(self, analytics):
        score = analytics.get_diversification_score()
        assert isinstance(score, DiversificationScore)
        assert 0 <= score.score <= 100

    def test_program_count(self, analytics):
        score = analytics.get_diversification_score()
        assert score.program_count == 4

    def test_assessment_valid(self, analytics):
        score = analytics.get_diversification_score()
        assert score.assessment in ("concentrated", "moderate", "balanced", "diversified")

    def test_empty_is_balanced(self, empty_analytics):
        score = empty_analytics.get_diversification_score()
        assert score.assessment == "balanced"
        assert score.score == 100.0


# =========================================
# PERIOD COMPARISON
# =========================================

class TestPeriodComparison:
    def test_comparison(self, analytics):
        comp = analytics.get_period_comparison("2025-01", "2024-12")
        assert isinstance(comp, PeriodComparison)
        assert comp.current_revenue == 85000
        assert comp.prior_revenue == 70000

    def test_growing_trend(self, analytics):
        comp = analytics.get_period_comparison("2025-01", "2024-12")
        assert comp.trend == "growing"
        assert comp.change_pct > 0

    def test_declining_trend(self, analytics):
        comp = analytics.get_period_comparison("2025-03", "2025-02")
        assert comp.trend == "declining"
        assert comp.change_pct < 0


# =========================================
# WEIGHTED PIPELINE
# =========================================

class TestWeightedPipeline:
    def test_pipeline_value(self, analytics):
        pipeline = analytics.get_weighted_pipeline()
        assert pipeline["weighted_value"] > 0
        assert pipeline["deal_count"] == 3

    def test_confidence_intervals(self, analytics):
        pipeline = analytics.get_weighted_pipeline()
        assert pipeline["confidence_low"] < pipeline["weighted_value"]
        assert pipeline["confidence_high"] > pipeline["weighted_value"]

    def test_empty_pipeline(self, empty_analytics):
        pipeline = empty_analytics.get_weighted_pipeline()
        assert pipeline["weighted_value"] == 0


# =========================================
# TOP ACCOUNTS
# =========================================

class TestTopAccounts:
    def test_returns_list(self, analytics):
        accounts = analytics.get_top_accounts(5)
        assert isinstance(accounts, list)
        assert len(accounts) <= 5

    def test_sorted_by_revenue(self, analytics):
        accounts = analytics.get_top_accounts()
        revenues = [a.get("revenue", 0) for a in accounts]
        assert revenues == sorted(revenues, reverse=True)


# =========================================
# EXECUTIVE SUMMARY
# =========================================

class TestExecutiveSummary:
    def test_generates_summary(self, analytics):
        summary = analytics.generate_executive_summary("2025-01", "2024-12")
        assert isinstance(summary, ExecutiveSummary)

    def test_revenue_and_target(self, analytics):
        summary = analytics.generate_executive_summary("2025-01")
        assert summary.total_revenue == 85000
        assert summary.target_revenue == 100000
        assert summary.attainment_pct == 85.0

    def test_has_narrative(self, analytics):
        summary = analytics.generate_executive_summary("2025-01")
        assert summary.narrative != ""
        assert "$85,000" in summary.narrative

    def test_has_diversification(self, analytics):
        summary = analytics.generate_executive_summary("2025-01")
        assert summary.diversification is not None

    def test_has_rep_attainment(self, analytics):
        summary = analytics.generate_executive_summary("2025-01")
        assert len(summary.rep_attainment) == 2

    def test_period_comparison_included(self, analytics):
        summary = analytics.generate_executive_summary("2025-01", "2024-12")
        assert summary.period_comparison is not None
        assert summary.period_comparison.trend == "growing"

    def test_generated_at_set(self, analytics):
        summary = analytics.generate_executive_summary("2025-01")
        assert summary.generated_at != ""


# =========================================
# SINGLETON
# =========================================

class TestSingleton:
    def test_get_analytics_returns_instance(self):
        a = get_executive_analytics()
        assert isinstance(a, ExecutiveAnalytics)

    def test_get_analytics_is_singleton(self):
        a1 = get_executive_analytics()
        a2 = get_executive_analytics()
        assert a1 is a2
