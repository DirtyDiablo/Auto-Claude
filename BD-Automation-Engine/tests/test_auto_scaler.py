"""Tests for Phase 57A — Auto Scaler."""

import pytest

from src.scaling.auto_scaler import (
    AutoScaler,
    ScalingDirection,
    get_auto_scaler,
)


@pytest.fixture
def scaler():
    return AutoScaler()


# =========================================
# PRE-REGISTERED POLICIES
# =========================================

def test_default_policies(scaler):
    policies = scaler.list_policies()
    assert len(policies) == 4


def test_api_cpu_policy(scaler):
    p = scaler.get_policy("api_cpu")
    assert p is not None
    assert p.scale_up_threshold == 80


def test_search_latency_policy(scaler):
    p = scaler.get_policy("search_latency")
    assert p is not None
    assert p.current_replicas == 2


def test_agent_queue_policy(scaler):
    p = scaler.get_policy("agent_queue")
    assert p is not None


# =========================================
# EVALUATE - SCALE UP
# =========================================

def test_evaluate_scale_up(scaler):
    event = scaler.evaluate("api_cpu", 90.0)
    assert event.direction == ScalingDirection.SCALE_UP
    p = scaler.get_policy("api_cpu")
    assert p.current_replicas == 4  # was 3, now 4


def test_evaluate_scale_up_respects_max(scaler):
    p = scaler.get_policy("api_cpu")
    p.current_replicas = p.max_replicas
    event = scaler.evaluate("api_cpu", 90.0)
    assert event.direction == ScalingDirection.NO_CHANGE


# =========================================
# EVALUATE - SCALE DOWN
# =========================================

def test_evaluate_scale_down(scaler):
    event = scaler.evaluate("api_cpu", 20.0)
    assert event.direction == ScalingDirection.SCALE_DOWN
    p = scaler.get_policy("api_cpu")
    assert p.current_replicas == 2  # was 3, now 2


def test_evaluate_scale_down_respects_min(scaler):
    p = scaler.get_policy("api_cpu")
    p.current_replicas = p.min_replicas
    event = scaler.evaluate("api_cpu", 20.0)
    assert event.direction == ScalingDirection.NO_CHANGE


# =========================================
# EVALUATE - NO CHANGE
# =========================================

def test_evaluate_no_change(scaler):
    event = scaler.evaluate("api_cpu", 50.0)
    assert event.direction == ScalingDirection.NO_CHANGE


def test_evaluate_not_found(scaler):
    event = scaler.evaluate("nonexistent", 50.0)
    assert event is None


# =========================================
# COOLDOWN
# =========================================

def test_cooldown_prevents_scaling(scaler):
    # First scale up succeeds
    event1 = scaler.evaluate("api_cpu", 90.0)
    assert event1.direction == ScalingDirection.SCALE_UP
    # Immediate second call should hit cooldown
    event2 = scaler.evaluate("api_cpu", 90.0)
    assert event2.direction == ScalingDirection.NO_CHANGE


# =========================================
# SCALING HISTORY
# =========================================

def test_scaling_history(scaler):
    scaler.evaluate("api_cpu", 90.0)
    history = scaler.get_scaling_history()
    assert len(history) >= 1


def test_scaling_history_filtered(scaler):
    scaler.evaluate("api_cpu", 90.0)
    scaler.evaluate("search_latency", 600.0)
    history = scaler.get_scaling_history(policy_id="api_cpu")
    assert all(e.policy_id == "api_cpu" for e in history)


# =========================================
# UPDATE POLICY
# =========================================

def test_update_policy(scaler):
    result = scaler.update_policy("api_cpu", scale_up_threshold=90)
    assert result is not None
    p = scaler.get_policy("api_cpu")
    assert p.scale_up_threshold == 90


def test_update_not_found(scaler):
    result = scaler.update_policy("nonexistent", scale_up_threshold=90)
    assert result is None


# =========================================
# RECOMMENDATIONS
# =========================================

def test_recommendations(scaler):
    recs = scaler.get_recommendations()
    assert isinstance(recs, list)


# =========================================
# TO_DICT & STATS
# =========================================

def test_policy_to_dict(scaler):
    p = scaler.get_policy("api_cpu")
    d = p.to_dict()
    assert "policy_id" in d
    assert "metric_name" in d
    assert "current_replicas" in d


def test_stats(scaler):
    stats = scaler.get_stats()
    assert stats["total_policies"] == 4


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    import src.scaling.auto_scaler as mod
    mod._instance = None
    a1 = get_auto_scaler()
    a2 = get_auto_scaler()
    assert a1 is a2
    mod._instance = None
