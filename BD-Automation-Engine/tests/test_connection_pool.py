"""Tests for Phase 57A — Connection Pool Manager."""

import pytest

from src.scaling.connection_pool import (
    ConnectionPoolManager,
    PoolType,
    get_pool_manager,
)


@pytest.fixture
def mgr():
    return ConnectionPoolManager()


# =========================================
# PRE-REGISTERED POOLS
# =========================================


def test_default_pools(mgr):
    pools = mgr.list_pools()
    assert len(pools) == 5


def test_qdrant_pool(mgr):
    p = mgr.get_pool("qdrant_pool")
    assert p is not None
    assert p.pool_type == PoolType.DATABASE


def test_api_pool(mgr):
    p = mgr.get_pool("api_pool")
    assert p is not None
    assert p.max_size == 50


def test_redis_cache_pool(mgr):
    p = mgr.get_pool("redis_cache")
    assert p is not None
    assert p.pool_type == PoolType.REDIS


# =========================================
# ACQUIRE / RELEASE
# =========================================


def test_acquire(mgr):
    result = mgr.acquire("qdrant_pool")
    assert result is True
    p = mgr.get_pool("qdrant_pool")
    assert p.active_connections == 1


def test_release(mgr):
    mgr.acquire("qdrant_pool")
    mgr.release("qdrant_pool")
    p = mgr.get_pool("qdrant_pool")
    assert p.active_connections == 0


def test_acquire_at_capacity(mgr):
    p = mgr.get_pool("qdrant_pool")
    for _ in range(p.max_size):
        mgr.acquire("qdrant_pool")
    result = mgr.acquire("qdrant_pool")
    assert result is False


def test_acquire_unknown(mgr):
    result = mgr.acquire("nonexistent")
    assert result is False


def test_release_unknown(mgr):
    # Should not error
    mgr.release("nonexistent")


# =========================================
# RESIZE
# =========================================


def test_resize(mgr):
    mgr.resize("qdrant_pool", 100)
    p = mgr.get_pool("qdrant_pool")
    assert p.max_size == 100


def test_resize_unknown(mgr):
    result = mgr.resize("nonexistent", 50)
    assert result is False


# =========================================
# HEALTH
# =========================================


def test_health_healthy(mgr):
    health = mgr.get_health("qdrant_pool")
    assert health["status"] == "healthy"
    assert health["utilization_pct"] == 0.0


def test_health_warning(mgr):
    p = mgr.get_pool("qdrant_pool")
    # Fill to 75% capacity
    for _ in range(int(p.max_size * 0.75)):
        mgr.acquire("qdrant_pool")
    health = mgr.get_health("qdrant_pool")
    assert health["status"] == "warning"


def test_health_critical(mgr):
    p = mgr.get_pool("qdrant_pool")
    # Fill to 95% capacity
    for _ in range(int(p.max_size * 0.95)):
        mgr.acquire("qdrant_pool")
    health = mgr.get_health("qdrant_pool")
    assert health["status"] == "critical"


def test_health_not_found(mgr):
    health = mgr.get_health("nonexistent")
    assert health is None


# =========================================
# TO_DICT & STATS
# =========================================


def test_pool_to_dict(mgr):
    p = mgr.get_pool("qdrant_pool")
    d = p.to_dict()
    assert "name" in d
    assert "pool_type" in d
    assert "max_size" in d


def test_stats(mgr):
    stats = mgr.get_stats()
    assert stats["total_pools"] == 5


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    import src.scaling.connection_pool as mod

    mod._instance = None
    a1 = get_pool_manager()
    a2 = get_pool_manager()
    assert a1 is a2
    mod._instance = None
