"""Tests for Phase 54A — Bulkhead Manager & Graceful Degradation."""

import pytest

from src.resilience.bulkhead import (
    BulkheadManager,
    BulkheadType,
    GracefulDegradation,
    DegradationLevel,
    get_bulkhead_manager,
    get_degradation,
)


@pytest.fixture
def mgr():
    return BulkheadManager()


@pytest.fixture
def deg():
    return GracefulDegradation()


# =========================================
# DEFAULT BULKHEADS
# =========================================

def test_default_bulkheads(mgr):
    bulkheads = mgr.list_bulkheads()
    assert len(bulkheads) == 5


def test_search_pool(mgr):
    b = mgr.get_bulkhead("search_pool")
    assert b is not None
    assert b.bulkhead_type == BulkheadType.THREAD_POOL
    assert b.max_concurrent == 10


def test_export_queue(mgr):
    b = mgr.get_bulkhead("export_queue")
    assert b is not None
    assert b.max_concurrent == 3


# =========================================
# ACQUIRE / RELEASE
# =========================================

def test_acquire(mgr):
    assert mgr.acquire("search_pool") is True
    b = mgr.get_bulkhead("search_pool")
    assert b.active_count == 1


def test_release(mgr):
    mgr.acquire("search_pool")
    mgr.release("search_pool")
    b = mgr.get_bulkhead("search_pool")
    assert b.active_count == 0


def test_acquire_at_capacity_queues(mgr):
    for _ in range(10):
        mgr.acquire("search_pool")
    # 11th should go to queue
    assert mgr.acquire("search_pool") is True
    b = mgr.get_bulkhead("search_pool")
    assert b.queue_size == 1


def test_acquire_full_rejects(mgr):
    b = mgr.get_bulkhead("search_pool")
    # Fill capacity
    for _ in range(b.max_concurrent):
        mgr.acquire("search_pool")
    # Fill queue
    for _ in range(b.max_queue):
        mgr.acquire("search_pool")
    # Should be rejected
    assert mgr.acquire("search_pool") is False
    assert b.rejected_count == 1


def test_acquire_unknown_allows(mgr):
    assert mgr.acquire("unknown_service") is True


# =========================================
# UTILIZATION
# =========================================

def test_utilization_empty(mgr):
    assert mgr.get_utilization("search_pool") == 0.0


def test_utilization_half(mgr):
    for _ in range(5):
        mgr.acquire("search_pool")
    assert mgr.get_utilization("search_pool") == 0.5


def test_utilization_full(mgr):
    for _ in range(10):
        mgr.acquire("search_pool")
    assert mgr.get_utilization("search_pool") == 1.0


# =========================================
# REGISTER
# =========================================

def test_register_new(mgr):
    b = mgr.register("custom", BulkheadType.SEMAPHORE, 20, 5)
    assert b.name == "custom"
    assert b.max_concurrent == 20


def test_register_existing_returns_same(mgr):
    b = mgr.register("search_pool", BulkheadType.THREAD_POOL, 50, 50)
    assert b.max_concurrent == 10  # original, not updated


# =========================================
# BULKHEAD TO_DICT & STATS
# =========================================

def test_bulkhead_to_dict(mgr):
    b = mgr.get_bulkhead("search_pool")
    d = b.to_dict()
    assert "name" in d
    assert "max_concurrent" in d
    assert "active_count" in d


def test_stats(mgr):
    mgr.acquire("search_pool")
    stats = mgr.get_stats()
    assert stats["total_bulkheads"] == 5
    assert stats["total_acquired"] >= 1


# =========================================
# GRACEFUL DEGRADATION
# =========================================

def test_initial_level(deg):
    assert deg.current_level == DegradationLevel.NORMAL


def test_set_level(deg):
    deg.set_level(DegradationLevel.DEGRADED)
    assert deg.current_level == DegradationLevel.DEGRADED


def test_set_emergency(deg):
    deg.set_level(DegradationLevel.EMERGENCY)
    assert deg.current_level == DegradationLevel.EMERGENCY


def test_default_fallbacks(deg):
    assert deg.get_fallback("search") == "cached_results"
    assert deg.get_fallback("agent") == "queued_response"
    assert deg.get_fallback("notification") == "batch_later"
    assert deg.get_fallback("export") == "limited_export"


def test_register_fallback(deg):
    deg.register_fallback("custom", "fallback_fn")
    assert deg.get_fallback("custom") == "fallback_fn"


def test_get_fallback_unknown(deg):
    assert deg.get_fallback("nonexistent") is None


def test_degradation_plan_normal(deg):
    plan = deg.get_degradation_plan()
    assert plan["level"] == "normal"
    assert plan["active_fallbacks"] == []


def test_degradation_plan_degraded(deg):
    deg.set_level(DegradationLevel.DEGRADED)
    plan = deg.get_degradation_plan()
    assert plan["level"] == "degraded"
    assert len(plan["active_fallbacks"]) == 4


# =========================================
# SINGLETONS
# =========================================

def test_bulkhead_singleton():
    import src.resilience.bulkhead as mod
    mod._bulkhead_instance = None
    m1 = get_bulkhead_manager()
    m2 = get_bulkhead_manager()
    assert m1 is m2
    mod._bulkhead_instance = None


def test_degradation_singleton():
    import src.resilience.bulkhead as mod
    mod._degradation_instance = None
    d1 = get_degradation()
    d2 = get_degradation()
    assert d1 is d2
    mod._degradation_instance = None
