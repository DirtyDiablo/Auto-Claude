"""Tests for Phase 36A — Deal Lifecycle Engine."""

import pytest
from datetime import datetime, timedelta, timezone

from src.revenue.deal_lifecycle import (
    DealLifecycleEngine,
    Deal,
    DealStage,
    StageVelocity,
    DropOffAnalysis,
    WinRateAnalysis,
    StaleDeal,
    STAGE_NAMES,
    STALE_THRESHOLDS,
    get_deal_engine,
)


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def engine():
    return DealLifecycleEngine()


@pytest.fixture
def sample_deals():
    now = datetime.now(timezone.utc)
    return [
        Deal(
            id="d1",
            title="DCGS Analyst",
            program="DCGS",
            channel="referral",
            rep="Rep-A",
            role_type="analyst",
            estimated_value=200000,
            current_stage=DealStage.REVENUE,
            outcome="won",
            created_at=(now - timedelta(days=90)).isoformat(),
            closed_at=(now - timedelta(days=10)).isoformat(),
            stage_history=[
                {
                    "stage": "discovery",
                    "entered_at": (now - timedelta(days=90)).isoformat(),
                },
                {
                    "stage": "qualification",
                    "entered_at": (now - timedelta(days=80)).isoformat(),
                },
                {
                    "stage": "requirements",
                    "entered_at": (now - timedelta(days=70)).isoformat(),
                },
                {
                    "stage": "submission",
                    "entered_at": (now - timedelta(days=55)).isoformat(),
                },
                {
                    "stage": "interview",
                    "entered_at": (now - timedelta(days=45)).isoformat(),
                },
                {
                    "stage": "offer",
                    "entered_at": (now - timedelta(days=25)).isoformat(),
                },
                {
                    "stage": "start",
                    "entered_at": (now - timedelta(days=15)).isoformat(),
                },
                {
                    "stage": "revenue",
                    "entered_at": (now - timedelta(days=10)).isoformat(),
                },
            ],
        ),
        Deal(
            id="d2",
            title="NGEN Engineer",
            program="NGEN",
            channel="cold_outreach",
            rep="Rep-B",
            role_type="engineer",
            estimated_value=180000,
            current_stage=DealStage.INTERVIEW,
            outcome="open",
            created_at=(now - timedelta(days=60)).isoformat(),
            stage_history=[
                {
                    "stage": "discovery",
                    "entered_at": (now - timedelta(days=60)).isoformat(),
                },
                {
                    "stage": "qualification",
                    "entered_at": (now - timedelta(days=50)).isoformat(),
                },
                {
                    "stage": "requirements",
                    "entered_at": (now - timedelta(days=40)).isoformat(),
                },
                {
                    "stage": "submission",
                    "entered_at": (now - timedelta(days=30)).isoformat(),
                },
                {
                    "stage": "interview",
                    "entered_at": (now - timedelta(days=5)).isoformat(),
                },
            ],
        ),
        Deal(
            id="d3",
            title="GBSD Developer",
            program="GBSD",
            channel="referral",
            rep="Rep-A",
            role_type="engineer",
            estimated_value=250000,
            current_stage=DealStage.QUALIFICATION,
            outcome="lost",
            lost_reason="budget_cut",
            created_at=(now - timedelta(days=45)).isoformat(),
            closed_at=(now - timedelta(days=30)).isoformat(),
            stage_history=[
                {
                    "stage": "discovery",
                    "entered_at": (now - timedelta(days=45)).isoformat(),
                },
                {
                    "stage": "qualification",
                    "entered_at": (now - timedelta(days=35)).isoformat(),
                },
            ],
        ),
        Deal(
            id="d4",
            title="DCGS Cyber",
            program="DCGS",
            channel="inbound",
            rep="Rep-A",
            role_type="cyber",
            estimated_value=220000,
            current_stage=DealStage.DISCOVERY,
            outcome="open",
            created_at=(now - timedelta(days=30)).isoformat(),
            stage_history=[
                {
                    "stage": "discovery",
                    "entered_at": (now - timedelta(days=30)).isoformat(),
                },
            ],
        ),
    ]


@pytest.fixture
def loaded_engine(engine, sample_deals):
    for d in sample_deals:
        engine.add_deal(d)
    return engine


# =========================================
# DEAL STAGE ENUM
# =========================================


class TestDealStage:
    def test_stage_order(self):
        assert DealStage.DISCOVERY < DealStage.REVENUE

    def test_from_string(self):
        assert DealStage.from_string("interview") == DealStage.INTERVIEW

    def test_stage_names(self):
        assert len(STAGE_NAMES) == 8

    def test_stale_thresholds(self):
        assert STALE_THRESHOLDS[DealStage.DISCOVERY] == 14


# =========================================
# DEAL MANAGEMENT
# =========================================


class TestDealManagement:
    def test_add_deal(self, engine, sample_deals):
        engine.add_deal(sample_deals[0])
        assert engine.get_deal("d1") is not None

    def test_open_deals(self, loaded_engine):
        open_deals = loaded_engine.get_open_deals()
        assert len(open_deals) == 2  # d2, d4

    def test_won_deals(self, loaded_engine):
        won = loaded_engine.get_won_deals()
        assert len(won) == 1  # d1

    def test_lost_deals(self, loaded_engine):
        lost = loaded_engine.get_lost_deals()
        assert len(lost) == 1  # d3

    def test_advance_stage(self, loaded_engine):
        loaded_engine.advance_stage("d4", DealStage.QUALIFICATION)
        deal = loaded_engine.get_deal("d4")
        assert deal.current_stage == DealStage.QUALIFICATION
        assert len(deal.stage_history) == 2

    def test_mark_lost(self, loaded_engine):
        loaded_engine.mark_lost("d2", "client_chose_competitor")
        deal = loaded_engine.get_deal("d2")
        assert deal.outcome == "lost"
        assert deal.lost_reason == "client_chose_competitor"


# =========================================
# STAGE VELOCITY
# =========================================


class TestStageVelocity:
    def test_velocity_returns_list(self, loaded_engine):
        velocity = loaded_engine.get_stage_velocity()
        assert isinstance(velocity, list)
        assert len(velocity) == 8  # One per stage

    def test_discovery_has_data(self, loaded_engine):
        velocity = loaded_engine.get_stage_velocity()
        discovery = [v for v in velocity if v.stage == "discovery"][0]
        assert discovery.deal_count > 0
        assert discovery.avg_days > 0

    def test_velocity_structure(self, loaded_engine):
        velocity = loaded_engine.get_stage_velocity()
        for v in velocity:
            assert isinstance(v, StageVelocity)
            if v.deal_count > 0:
                assert v.avg_days >= 0
                assert v.min_days <= v.max_days


# =========================================
# DROP-OFF ANALYSIS
# =========================================


class TestDropOffAnalysis:
    def test_drop_off_returns_list(self, loaded_engine):
        analysis = loaded_engine.get_drop_off_analysis()
        assert isinstance(analysis, list)

    def test_qualification_has_drop(self, loaded_engine):
        analysis = loaded_engine.get_drop_off_analysis()
        qual = [a for a in analysis if a.stage == "qualification"][0]
        assert qual.lost_count == 1  # d3 lost at qualification

    def test_drop_rate_calculated(self, loaded_engine):
        analysis = loaded_engine.get_drop_off_analysis()
        for a in analysis:
            assert isinstance(a, DropOffAnalysis)
            if a.total_entered > 0:
                assert 0 <= a.drop_rate <= 100


# =========================================
# WIN RATES
# =========================================


class TestWinRates:
    def test_win_rate_by_program(self, loaded_engine):
        wr = loaded_engine.get_win_rates("program")
        assert isinstance(wr, WinRateAnalysis)
        assert wr.overall_win_rate == 50.0  # 1 won, 1 lost

    def test_win_rate_by_channel(self, loaded_engine):
        wr = loaded_engine.get_win_rates("channel")
        assert len(wr.breakdown) > 0

    def test_empty_returns_zero(self, engine):
        wr = engine.get_win_rates()
        assert wr.overall_win_rate == 0.0


# =========================================
# STALE DEAL DETECTION
# =========================================


class TestStaleDealDetection:
    def test_detects_stale(self, loaded_engine):
        stale = loaded_engine.detect_stale_deals()
        assert isinstance(stale, list)

    def test_stale_deal_structure(self, loaded_engine):
        stale = loaded_engine.detect_stale_deals()
        for s in stale:
            assert isinstance(s, StaleDeal)
            assert s.overdue_by >= 0
            assert s.recommended_action != ""

    def test_d4_is_stale(self, loaded_engine):
        # d4 has been in discovery for 30 days, threshold is 14
        stale = loaded_engine.detect_stale_deals()
        stale_ids = [s.deal_id for s in stale]
        assert "d4" in stale_ids


# =========================================
# DEAL VALUE PREDICTION
# =========================================


class TestDealValuePrediction:
    def test_predicts_value(self, loaded_engine):
        pred = loaded_engine.predict_deal_value("d2")
        assert "weighted_value" in pred
        assert pred["estimated_value"] == 180000

    def test_stage_probability(self, loaded_engine):
        pred = loaded_engine.predict_deal_value("d2")
        assert pred["stage_probability"] == 0.65  # Interview stage

    def test_nonexistent_deal(self, loaded_engine):
        pred = loaded_engine.predict_deal_value("nonexistent")
        assert "error" in pred


# =========================================
# LIFECYCLE SUMMARY
# =========================================


class TestLifecycleSummary:
    def test_summary(self, loaded_engine):
        summary = loaded_engine.get_lifecycle_summary()
        assert summary["total_deals"] == 4
        assert summary["open_deals"] == 2
        assert summary["won_deals"] == 1
        assert summary["lost_deals"] == 1
        assert summary["win_rate"] == 50.0

    def test_pipeline_value(self, loaded_engine):
        summary = loaded_engine.get_lifecycle_summary()
        assert summary["pipeline_value"] > 0
        assert summary["weighted_pipeline"] > 0


# =========================================
# SINGLETON
# =========================================


class TestSingleton:
    def test_get_engine_returns_instance(self):
        e = get_deal_engine()
        assert isinstance(e, DealLifecycleEngine)

    def test_get_engine_is_singleton(self):
        e1 = get_deal_engine()
        e2 = get_deal_engine()
        assert e1 is e2
