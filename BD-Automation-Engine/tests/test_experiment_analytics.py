"""Tests for Phase 55A — Experiment Analytics."""

import pytest

from src.experimentation.experiment_analytics import (
    ExperimentAnalytics,
    AnalyticsEvent,
    FunnelStep,
    get_experiment_analytics,
)


@pytest.fixture
def analytics():
    return ExperimentAnalytics()


# =========================================
# TRACK EVENTS
# =========================================

def test_track_event(analytics):
    event = analytics.track_event("exp1", "var_a", "user1", "view")
    assert isinstance(event, AnalyticsEvent)
    assert event.event_id.startswith("evt_")


def test_track_with_value(analytics):
    event = analytics.track_event("exp1", "var_a", "user1", "purchase", value=99.50)
    assert event.value == 99.50


def test_track_multiple(analytics):
    analytics.track_event("exp1", "var_a", "user1", "view")
    analytics.track_event("exp1", "var_a", "user2", "view")
    analytics.track_event("exp1", "var_b", "user3", "view")
    stats = analytics.get_stats()
    assert stats["total_events"] == 3


# =========================================
# FUNNEL
# =========================================

def test_funnel(analytics):
    for i in range(100):
        analytics.track_event("exp1", "var_a", f"user_{i}", "view")
    for i in range(60):
        analytics.track_event("exp1", "var_a", f"user_{i}", "click")
    for i in range(20):
        analytics.track_event("exp1", "var_a", f"user_{i}", "convert")

    funnel = analytics.get_funnel("exp1")
    assert isinstance(funnel, list)
    assert funnel[0].step_name == "view"
    assert funnel[0].count == 100
    assert funnel[1].step_name == "click"
    assert funnel[1].count == 60
    assert funnel[1].conversion_rate == pytest.approx(0.6, abs=0.01)


def test_funnel_empty(analytics):
    funnel = analytics.get_funnel("exp_nonexistent")
    assert len(funnel) == 5  # all steps, zero counts
    assert funnel[0].count == 0


def test_funnel_step_to_dict(analytics):
    analytics.track_event("exp1", "var_a", "user1", "view")
    funnel = analytics.get_funnel("exp1")
    d = funnel[0].to_dict()
    assert "step_name" in d
    assert "conversion_rate" in d


# =========================================
# TIME SERIES
# =========================================

def test_time_series(analytics):
    analytics.track_event("exp1", "var_a", "user1", "conversion", value=10.0)
    analytics.track_event("exp1", "var_a", "user2", "conversion", value=20.0)
    ts = analytics.get_time_series("exp1", "conversion")
    assert len(ts) >= 1
    assert ts[0]["count"] >= 2


def test_time_series_empty(analytics):
    ts = analytics.get_time_series("exp_nonexistent", "conversion")
    assert len(ts) == 0


# =========================================
# SEGMENT ANALYSIS
# =========================================

def test_segment_by_variant(analytics):
    for i in range(20):
        analytics.track_event("exp1", "var_a", f"user_{i}", "view")
    for i in range(10):
        analytics.track_event("exp1", "var_a", f"user_{i}", "convert")
    for i in range(20):
        analytics.track_event("exp1", "var_b", f"user_b{i}", "view")
    for i in range(5):
        analytics.track_event("exp1", "var_b", f"user_b{i}", "convert")

    segments = analytics.get_segment_analysis("exp1", "variant_id")
    assert "var_a" in segments
    assert "var_b" in segments
    assert segments["var_a"] > segments["var_b"]


def test_segment_empty(analytics):
    segments = analytics.get_segment_analysis("exp_nonexistent")
    assert len(segments) == 0


# =========================================
# SAMPLE SIZE CALCULATOR
# =========================================

def test_sample_size(analytics):
    n = analytics.compute_sample_size_needed(0.10, 0.02)
    assert n > 0
    assert n > 1000  # should need a decent sample


def test_sample_size_smaller_effect(analytics):
    n1 = analytics.compute_sample_size_needed(0.10, 0.02)
    n2 = analytics.compute_sample_size_needed(0.10, 0.05)
    assert n1 > n2  # smaller effect needs larger sample


def test_sample_size_invalid_rates(analytics):
    n = analytics.compute_sample_size_needed(0.0, 0.02)
    assert n == 0


# =========================================
# EVENT TO_DICT
# =========================================

def test_event_to_dict(analytics):
    event = analytics.track_event("exp1", "var_a", "user1", "view")
    d = event.to_dict()
    assert "event_id" in d
    assert "experiment_id" in d
    assert "event_type" in d


# =========================================
# STATS & SINGLETON
# =========================================

def test_stats(analytics):
    analytics.track_event("exp1", "var_a", "user1", "view")
    stats = analytics.get_stats()
    assert stats["total_events"] == 1
    assert stats["unique_experiments"] == 1


def test_singleton():
    import src.experimentation.experiment_analytics as mod
    mod._instance = None
    a1 = get_experiment_analytics()
    a2 = get_experiment_analytics()
    assert a1 is a2
    mod._instance = None
