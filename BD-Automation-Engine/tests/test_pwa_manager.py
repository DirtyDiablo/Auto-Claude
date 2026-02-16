"""Tests for Phase 58A — PWA Manager."""

import pytest

from src.pwa.pwa_manager import (
    PWAManager,
    CacheStrategy,
    SyncStatus,
    get_pwa_manager,
)


@pytest.fixture
def mgr():
    return PWAManager()


# =========================================
# DEFAULT RESOURCES
# =========================================


def test_default_resources(mgr):
    resources = mgr.list_resources()
    assert len(resources) == 6


def test_app_shell_resource(mgr):
    r = mgr.get_resource("app_shell")
    assert r is not None
    assert r.cache_strategy == CacheStrategy.CACHE_FIRST


def test_api_contacts_resource(mgr):
    r = mgr.get_resource("api_contacts")
    assert r is not None
    assert r.cache_strategy == CacheStrategy.NETWORK_FIRST


# =========================================
# RESOURCE MANAGEMENT
# =========================================


def test_add_resource(mgr):
    r = mgr.add_resource("/api/v2/jobs", CacheStrategy.STALE_WHILE_REVALIDATE, 5000)
    assert r.resource_id.startswith("res_")
    assert len(mgr.list_resources()) == 7


def test_remove_resource(mgr):
    result = mgr.remove_resource("app_shell")
    assert result is True
    assert mgr.get_resource("app_shell") is None


def test_remove_not_found(mgr):
    result = mgr.remove_resource("nonexistent")
    assert result is False


# =========================================
# SYNC QUEUE
# =========================================


def test_queue_sync(mgr):
    item = mgr.queue_sync("create_contact", {"name": "Test User"})
    assert item.item_id.startswith("sync_")
    assert item.status == SyncStatus.PENDING


def test_pending_count(mgr):
    mgr.queue_sync("action1")
    mgr.queue_sync("action2")
    assert mgr.pending_sync_count() == 2


def test_process_sync(mgr):
    mgr.queue_sync("action1")
    mgr.queue_sync("action2")
    result = mgr.process_sync_queue()
    assert result["synced"] == 2
    assert result["remaining"] == 0


def test_get_sync_queue(mgr):
    mgr.queue_sync("action1")
    queue = mgr.get_sync_queue()
    assert len(queue) == 1


def test_sync_item_to_dict(mgr):
    item = mgr.queue_sync("test_action")
    d = item.to_dict()
    assert "item_id" in d
    assert "action" in d
    assert "status" in d


# =========================================
# MANIFEST
# =========================================


def test_manifest(mgr):
    m = mgr.get_manifest()
    assert m.name == "BD Intelligence Hub"


def test_manifest_to_dict(mgr):
    d = mgr.get_manifest().to_dict()
    assert "name" in d
    assert "icons" in d
    assert len(d["icons"]) == 2


def test_update_manifest(mgr):
    mgr.update_manifest(short_name="BD Test")
    assert mgr.get_manifest().short_name == "BD Test"


# =========================================
# ONLINE STATUS
# =========================================


def test_is_online(mgr):
    assert mgr.is_online() is True


def test_set_offline(mgr):
    mgr.set_online(False)
    assert mgr.is_online() is False


# =========================================
# STATS & SINGLETON
# =========================================


def test_stats(mgr):
    stats = mgr.get_stats()
    assert stats["total_resources"] == 6
    assert stats["is_online"] is True


def test_resource_to_dict(mgr):
    r = mgr.get_resource("app_shell")
    d = r.to_dict()
    assert "resource_id" in d
    assert "cache_strategy" in d


def test_singleton():
    import src.pwa.pwa_manager as mod

    mod._instance = None
    a1 = get_pwa_manager()
    a2 = get_pwa_manager()
    assert a1 is a2
    mod._instance = None
