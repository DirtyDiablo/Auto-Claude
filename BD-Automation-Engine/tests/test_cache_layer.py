"""Tests for Phase 57A — Cache Layer Manager."""

import pytest

from src.scaling.cache_layer import (
    CacheLayerManager,
    LayerType,
    get_cache_manager,
)


@pytest.fixture
def mgr():
    return CacheLayerManager()


# =========================================
# PRE-REGISTERED LAYERS
# =========================================


def test_default_layers(mgr):
    layers = mgr.list_layers()
    assert len(layers) == 4


def test_l1_hot(mgr):
    layer = mgr.get_layer("l1_hot")
    assert layer is not None
    assert layer.layer_type == LayerType.L1_MEMORY


def test_l2_warm(mgr):
    layer = mgr.get_layer("l2_warm")
    assert layer is not None
    assert layer.layer_type == LayerType.L2_REDIS


def test_cdn_static(mgr):
    layer = mgr.get_layer("cdn_static")
    assert layer is not None
    assert layer.layer_type == LayerType.CDN


# =========================================
# PUT / GET
# =========================================


def test_put_and_get(mgr):
    mgr.put("key1", "value1", ttl=60)
    entry = mgr.get("key1")
    assert entry is not None
    assert entry.value == "value1"


def test_get_miss(mgr):
    entry = mgr.get("nonexistent_key")
    assert entry is None


def test_put_specific_layer(mgr):
    mgr.put("l2_key", "l2_value", layer_name="l2_warm")
    entry = mgr.get("l2_key", layer_name="l2_warm")
    assert entry is not None
    assert entry.value == "l2_value"


def test_get_cascade(mgr):
    # Put in L2, get without specifying layer should cascade and find it
    mgr.put("cascade_key", "cascade_val", layer_name="l2_warm")
    entry = mgr.get("cascade_key")
    assert entry is not None


def test_hit_tracking(mgr):
    mgr.put("tracked", "val")
    mgr.get("tracked")
    mgr.get("tracked")
    layer = mgr.get_layer("l1_hot")
    assert layer.total_hits >= 2


def test_miss_tracking(mgr):
    mgr.get("never_exists_1")
    mgr.get("never_exists_2")
    # At least some layer should have misses
    stats = mgr.get_stats()
    assert stats["total_misses"] >= 2


# =========================================
# INVALIDATE
# =========================================


def test_invalidate(mgr):
    mgr.put("del_key", "del_val")
    mgr.invalidate("del_key")
    entry = mgr.get("del_key")
    assert entry is None


def test_invalidate_specific_layer(mgr):
    mgr.put("l1_del", "val", layer_name="l1_hot")
    mgr.invalidate("l1_del", layer_name="l1_hot")
    entry = mgr.get("l1_del", layer_name="l1_hot")
    assert entry is None


# =========================================
# HIT RATES
# =========================================


def test_hit_rates(mgr):
    mgr.put("hr_key", "val")
    mgr.get("hr_key")
    rates = mgr.get_hit_rates()
    assert "l1_hot" in rates


# =========================================
# WARM CACHE
# =========================================


def test_warm_cache(mgr):
    count = mgr.warm_cache(["warm1", "warm2", "warm3"])
    assert count == 3


def test_warm_cache_empty(mgr):
    count = mgr.warm_cache([])
    assert count == 0


# =========================================
# TO_DICT & STATS
# =========================================


def test_layer_to_dict(mgr):
    layer = mgr.get_layer("l1_hot")
    d = layer.to_dict()
    assert "name" in d
    assert "layer_type" in d
    assert "max_entries" in d


def test_stats(mgr):
    stats = mgr.get_stats()
    assert stats["total_layers"] == 4
    assert "total_entries" in stats


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    import src.scaling.cache_layer as mod

    mod._instance = None
    a1 = get_cache_manager()
    a2 = get_cache_manager()
    assert a1 is a2
    mod._instance = None
