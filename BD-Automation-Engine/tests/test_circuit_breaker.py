"""Tests for Phase 54A — Circuit Breaker Registry."""

import pytest

from src.resilience.circuit_breaker import (
    CircuitBreakerRegistry,
    CircuitState,
    get_circuit_registry,
)


@pytest.fixture
def registry():
    return CircuitBreakerRegistry()


# =========================================
# PRE-REGISTERED BREAKERS
# =========================================


def test_default_breakers(registry):
    breakers = registry.list_breakers()
    assert len(breakers) == 6


def test_qdrant_breaker(registry):
    b = registry.get_breaker("qdrant_search")
    assert b is not None
    assert b.state == CircuitState.CLOSED


def test_agent_breaker(registry):
    b = registry.get_breaker("agent_executor")
    assert b is not None


# =========================================
# RECORD SUCCESS / FAILURE
# =========================================


def test_record_success(registry):
    registry.record_success("qdrant_search")
    b = registry.get_breaker("qdrant_search")
    assert b.success_count == 1


def test_record_failure(registry):
    registry.record_failure("qdrant_search")
    b = registry.get_breaker("qdrant_search")
    assert b.failure_count == 1


def test_trip_on_threshold(registry):
    for _ in range(5):
        registry.record_failure("qdrant_search")
    b = registry.get_breaker("qdrant_search")
    assert b.state == CircuitState.OPEN


def test_can_execute_closed(registry):
    assert registry.can_execute("qdrant_search") is True


def test_can_execute_open(registry):
    for _ in range(5):
        registry.record_failure("qdrant_search")
    assert registry.can_execute("qdrant_search") is False


# =========================================
# TRIP / RESET
# =========================================


def test_manual_trip(registry):
    registry.trip("qdrant_search")
    b = registry.get_breaker("qdrant_search")
    assert b.state == CircuitState.OPEN


def test_manual_reset(registry):
    registry.trip("qdrant_search")
    registry.reset("qdrant_search")
    b = registry.get_breaker("qdrant_search")
    assert b.state == CircuitState.CLOSED


def test_trip_unknown(registry):
    assert registry.trip("nonexistent") is False


def test_reset_unknown(registry):
    assert registry.reset("nonexistent") is False


# =========================================
# HALF-OPEN RECOVERY
# =========================================


def test_success_in_half_open_closes(registry):
    registry.trip("qdrant_search")
    b = registry.get_breaker("qdrant_search")
    b.state = CircuitState.HALF_OPEN
    registry.record_success("qdrant_search")
    assert b.state == CircuitState.CLOSED


# =========================================
# REGISTER / LIST
# =========================================


def test_register_new_breaker(registry):
    registry.register("custom_service", failure_threshold=3)
    b = registry.get_breaker("custom_service")
    assert b is not None
    assert b.failure_threshold == 3


def test_get_breaker_not_found(registry):
    assert registry.get_breaker("nonexistent") is None


def test_breaker_to_dict(registry):
    b = registry.get_breaker("qdrant_search")
    d = b.to_dict()
    assert "name" in d
    assert "state" in d
    assert "failure_count" in d


# =========================================
# STATS & SINGLETON
# =========================================


def test_stats(registry):
    stats = registry.get_stats()
    assert stats["total_breakers"] == 6


def test_singleton():
    import src.resilience.circuit_breaker as mod

    mod._instance = None
    r1 = get_circuit_registry()
    r2 = get_circuit_registry()
    assert r1 is r2
    mod._instance = None
