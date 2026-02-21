"""
Tests for Feature 16 — StableMemoryManager

Covers: add, search, get_all, delete, clear, deduplication,
per-user isolation, TTL cleanup, context generation, stats,
error handling, and fallback mode.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure mem0 import will fail gracefully in tests (we test fallback mode)
import sys


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the module singleton before each test."""
    from Engine8_Knowledge.memory.stable_mem0 import reset_stable_memory_manager

    reset_stable_memory_manager()
    yield
    reset_stable_memory_manager()


@pytest.fixture
def tmp_storage(tmp_path):
    """Provide a temporary storage directory."""
    return str(tmp_path)


@pytest.fixture
def manager(tmp_storage):
    """Create a fresh StableMemoryManager with dict fallback."""
    from Engine8_Knowledge.memory.stable_mem0 import StableMemoryManager

    # Patch _init_mem0 to prevent network connections during tests
    with patch.object(StableMemoryManager, "_init_mem0"):
        mgr = StableMemoryManager(storage_dir=tmp_storage)
    mgr._mem0 = None
    mgr._mem0_available = False
    return mgr


# ---------------------------------------------------------------------------
# Basic add / get / search
# ---------------------------------------------------------------------------


class TestAddMemory:
    def test_add_returns_id(self, manager):
        mid = manager.add("user1", "DCGS is a high-priority program")
        assert mid.startswith("smem_")

    def test_add_stores_in_fallback(self, manager):
        manager.add("user1", "test content")
        assert len(manager._memories["user1"]) == 1
        assert manager._memories["user1"][0]["content"] == "test content"

    def test_add_with_metadata(self, manager):
        manager.add("user1", "note", metadata={"source": "call"})
        entry = manager._memories["user1"][0]
        assert entry["metadata"]["source"] == "call"

    def test_add_requires_user_id(self, manager):
        with pytest.raises(ValueError):
            manager.add("", "content")

    def test_add_requires_content(self, manager):
        with pytest.raises(ValueError):
            manager.add("user1", "")

    def test_add_created_at_timestamp(self, manager):
        manager.add("user1", "timestamped")
        entry = manager._memories["user1"][0]
        assert "created_at" in entry
        # Should be a valid ISO format
        datetime.fromisoformat(entry["created_at"])


class TestGetAll:
    def test_get_all_empty_user(self, manager):
        result = manager.get_all("nonexistent")
        assert result == []

    def test_get_all_returns_entries(self, manager):
        manager.add("user1", "memory one")
        manager.add("user1", "memory two")
        result = manager.get_all("user1")
        assert len(result) == 2
        contents = [r["content"] for r in result]
        assert "memory one" in contents
        assert "memory two" in contents

    def test_get_all_returns_dict_format(self, manager):
        manager.add("user1", "test")
        result = manager.get_all("user1")
        entry = result[0]
        assert "id" in entry
        assert "content" in entry
        assert "metadata" in entry

    def test_get_all_empty_user_id(self, manager):
        result = manager.get_all("")
        assert result == []


class TestSearch:
    def test_search_keyword_match(self, manager):
        manager.add("user1", "DCGS is a billion dollar program")
        manager.add("user1", "Leidos is a prime contractor")
        results = manager.search("user1", "DCGS")
        assert len(results) == 1
        assert "DCGS" in results[0]["content"]

    def test_search_case_insensitive(self, manager):
        manager.add("user1", "DCGS analysis report")
        results = manager.search("user1", "dcgs")
        assert len(results) == 1

    def test_search_respects_limit(self, manager):
        for i in range(10):
            manager.add("user1", f"common keyword entry {i}")
        results = manager.search("user1", "common", limit=3)
        assert len(results) == 3

    def test_search_no_results(self, manager):
        manager.add("user1", "something else")
        results = manager.search("user1", "nonexistent_term_xyz")
        assert results == []

    def test_search_empty_query(self, manager):
        results = manager.search("user1", "")
        assert results == []

    def test_search_returns_score(self, manager):
        manager.add("user1", "keyword match")
        results = manager.search("user1", "keyword")
        assert results[0]["score"] == 0.8  # fallback score


# ---------------------------------------------------------------------------
# Per-user isolation
# ---------------------------------------------------------------------------


class TestUserIsolation:
    def test_users_cannot_see_each_other(self, manager):
        manager.add("alice", "alice secret data")
        manager.add("bob", "bob secret data")

        alice_all = manager.get_all("alice")
        bob_all = manager.get_all("bob")

        assert len(alice_all) == 1
        assert len(bob_all) == 1
        assert alice_all[0]["content"] == "alice secret data"
        assert bob_all[0]["content"] == "bob secret data"

    def test_search_scoped_to_user(self, manager):
        manager.add("alice", "DCGS program intel")
        manager.add("bob", "DCGS budget analysis")

        alice_results = manager.search("alice", "DCGS")
        bob_results = manager.search("bob", "DCGS")

        assert len(alice_results) == 1
        assert "intel" in alice_results[0]["content"]
        assert len(bob_results) == 1
        assert "budget" in bob_results[0]["content"]

    def test_delete_scoped_to_user(self, manager):
        mid_alice = manager.add("alice", "shared topic")
        mid_bob = manager.add("bob", "shared topic")

        # Delete alice's copy
        manager.delete("alice", mid_alice)
        assert len(manager.get_all("alice")) == 0
        assert len(manager.get_all("bob")) == 1

    def test_clear_scoped_to_user(self, manager):
        manager.add("alice", "data 1")
        manager.add("alice", "data 2")
        manager.add("bob", "data 3")

        manager.clear("alice")
        assert len(manager.get_all("alice")) == 0
        assert len(manager.get_all("bob")) == 1


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


class TestDeduplication:
    def test_duplicate_not_stored_twice(self, manager):
        mid1 = manager.add("user1", "exact same content")
        mid2 = manager.add("user1", "exact same content")
        assert mid1 == mid2
        assert len(manager._memories["user1"]) == 1

    def test_case_insensitive_dedup(self, manager):
        mid1 = manager.add("user1", "Hello World")
        mid2 = manager.add("user1", "hello world")
        assert mid1 == mid2
        assert len(manager._memories["user1"]) == 1

    def test_whitespace_dedup(self, manager):
        mid1 = manager.add("user1", "  spaced content  ")
        mid2 = manager.add("user1", "spaced content")
        assert mid1 == mid2

    def test_different_content_not_deduped(self, manager):
        manager.add("user1", "content A")
        manager.add("user1", "content B")
        assert len(manager._memories["user1"]) == 2

    def test_same_content_different_users(self, manager):
        """Same content for different users should both be stored."""
        manager.add("alice", "shared insight")
        manager.add("bob", "shared insight")
        assert len(manager._memories.get("alice", [])) == 1
        assert len(manager._memories.get("bob", [])) == 1


# ---------------------------------------------------------------------------
# Delete / Clear
# ---------------------------------------------------------------------------


class TestDelete:
    def test_delete_existing(self, manager):
        mid = manager.add("user1", "to be deleted")
        assert manager.delete("user1", mid) is True
        assert len(manager.get_all("user1")) == 0

    def test_delete_nonexistent(self, manager):
        assert manager.delete("user1", "fake_id") is False

    def test_delete_wrong_user(self, manager):
        mid = manager.add("alice", "alice memory")
        assert manager.delete("bob", mid) is False
        assert len(manager.get_all("alice")) == 1

    def test_delete_removes_hash(self, manager):
        """After delete, the same content can be added again."""
        mid = manager.add("user1", "recyclable content")
        manager.delete("user1", mid)
        mid2 = manager.add("user1", "recyclable content")
        assert mid2 != mid  # New ID since it was deleted

    def test_delete_empty_params(self, manager):
        assert manager.delete("", "mid") is False
        assert manager.delete("user1", "") is False


class TestClear:
    def test_clear_returns_count(self, manager):
        manager.add("user1", "a")
        manager.add("user1", "b")
        manager.add("user1", "c")
        count = manager.clear("user1")
        assert count == 3

    def test_clear_empty_user(self, manager):
        count = manager.clear("nonexistent")
        assert count == 0

    def test_clear_removes_hashes(self, manager):
        manager.add("user1", "content")
        manager.clear("user1")
        assert "user1" not in manager._hashes

    def test_clear_empty_user_id(self, manager):
        assert manager.clear("") == 0


# ---------------------------------------------------------------------------
# Context generation for RAG
# ---------------------------------------------------------------------------


class TestContext:
    def test_context_returns_string(self, manager):
        manager.add("user1", "DCGS is a key program worth 950M")
        ctx = manager.get_context("user1", "DCGS")
        assert isinstance(ctx, str)
        assert "DCGS" in ctx

    def test_context_empty_when_no_matches(self, manager):
        ctx = manager.get_context("user1", "nonexistent")
        assert ctx == ""

    def test_context_respects_token_budget(self, manager):
        # Add lots of content
        for i in range(50):
            manager.add("user1", f"keyword entry number {i} " + "x" * 200)
        ctx = manager.get_context("user1", "keyword", max_tokens=100)
        # 100 tokens * 4 chars = 400 chars budget
        assert len(ctx) < 600  # some overhead for the header line

    def test_context_empty_query(self, manager):
        assert manager.get_context("user1", "") == ""

    def test_context_empty_user(self, manager):
        assert manager.get_context("", "query") == ""

    def test_context_header(self, manager):
        manager.add("user1", "relevant data")
        ctx = manager.get_context("user1", "relevant")
        assert ctx.startswith("Relevant memories:")


# ---------------------------------------------------------------------------
# TTL Cleanup
# ---------------------------------------------------------------------------


class TestTTLCleanup:
    def test_cleanup_removes_old_entries(self, manager):
        manager.add("user1", "old memory")
        # Manually backdate
        old_date = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        manager._memories["user1"][0]["created_at"] = old_date

        removed = manager.cleanup_expired(ttl_days=90)
        assert removed == 1
        assert len(manager.get_all("user1")) == 0

    def test_cleanup_keeps_recent_entries(self, manager):
        manager.add("user1", "fresh memory")
        removed = manager.cleanup_expired(ttl_days=90)
        assert removed == 0
        assert len(manager.get_all("user1")) == 1

    def test_cleanup_custom_ttl(self, manager):
        manager.add("user1", "semi-old")
        old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        manager._memories["user1"][0]["created_at"] = old_date

        # 30 day TTL: should keep
        assert manager.cleanup_expired(ttl_days=30) == 0
        # 5 day TTL: should remove
        assert manager.cleanup_expired(ttl_days=5) == 1

    def test_cleanup_removes_empty_users(self, manager):
        manager.add("user1", "to expire")
        old_date = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
        manager._memories["user1"][0]["created_at"] = old_date

        manager.cleanup_expired()
        assert "user1" not in manager._memories


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class TestStats:
    def test_stats_empty(self, manager):
        stats = manager.get_stats()
        assert stats["user_count"] == 0
        assert stats["total_memories"] == 0
        assert stats["backend"] == "dict_fallback"
        assert stats["mem0_available"] is False

    def test_stats_with_data(self, manager):
        manager.add("alice", "a1")
        manager.add("alice", "a2")
        manager.add("bob", "b1")
        stats = manager.get_stats()
        assert stats["user_count"] == 2
        assert stats["total_memories"] == 3
        assert stats["per_user"]["alice"] == 2
        assert stats["per_user"]["bob"] == 1

    def test_stats_storage_dir(self, manager, tmp_storage):
        stats = manager.get_stats()
        assert stats["storage_dir"] == tmp_storage


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


class TestPersistence:
    def test_save_and_load(self, tmp_storage):
        from Engine8_Knowledge.memory.stable_mem0 import StableMemoryManager

        with patch.object(StableMemoryManager, "_init_mem0"):
            mgr1 = StableMemoryManager(storage_dir=tmp_storage)
        mgr1._mem0 = None
        mgr1._mem0_available = False
        mgr1.add("user1", "persistent data")

        # New instance loads from disk
        with patch.object(StableMemoryManager, "_init_mem0"):
            mgr2 = StableMemoryManager(storage_dir=tmp_storage)
        mgr2._mem0 = None
        mgr2._mem0_available = False
        all_mems = mgr2.get_all("user1")
        assert len(all_mems) == 1
        assert all_mems[0]["content"] == "persistent data"

    def test_persistence_file_created(self, manager, tmp_storage):
        manager.add("user1", "data")
        path = Path(tmp_storage) / "stable_memories.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert "user1" in data


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_corrupted_persistence_file(self, tmp_storage):
        """Manager should handle corrupted JSON gracefully."""
        from Engine8_Knowledge.memory.stable_mem0 import StableMemoryManager

        path = Path(tmp_storage) / "stable_memories.json"
        path.write_text("NOT VALID JSON {{{")

        with patch.object(StableMemoryManager, "_init_mem0"):
            mgr = StableMemoryManager(storage_dir=tmp_storage)
        mgr._mem0 = None
        mgr._mem0_available = False
        # Should start empty, not crash
        assert mgr.get_stats()["total_memories"] == 0

    def test_mem0_failure_falls_back(self, tmp_storage):
        """If mem0 add raises, fallback store still works."""
        from Engine8_Knowledge.memory.stable_mem0 import StableMemoryManager

        with patch.object(StableMemoryManager, "_init_mem0"):
            mgr = StableMemoryManager(storage_dir=tmp_storage)
        # Simulate mem0 present but broken
        mock_mem0 = MagicMock()
        mock_mem0.add.side_effect = RuntimeError("connection refused")
        mgr._mem0 = mock_mem0
        mgr._mem0_available = True

        mid = mgr.add("user1", "fallback test")
        assert mid.startswith("smem_")
        assert len(mgr.get_all("user1")) == 1

    def test_mem0_search_failure_falls_back(self, tmp_storage):
        """If mem0 search raises, keyword fallback is used."""
        from Engine8_Knowledge.memory.stable_mem0 import StableMemoryManager

        with patch.object(StableMemoryManager, "_init_mem0"):
            mgr = StableMemoryManager(storage_dir=tmp_storage)
        mock_mem0 = MagicMock()
        mock_mem0.search.side_effect = RuntimeError("timeout")
        mgr._mem0 = mock_mem0
        mgr._mem0_available = True

        mgr.add("user1", "keyword findable content")
        results = mgr.search("user1", "keyword")
        assert len(results) == 1

    def test_missing_user_operations(self, manager):
        """Operations on nonexistent users should not raise."""
        assert manager.get_all("ghost") == []
        assert manager.search("ghost", "test") == []
        assert manager.delete("ghost", "fake") is False
        assert manager.clear("ghost") == 0
        assert manager.get_context("ghost", "test") == ""


# ---------------------------------------------------------------------------
# Singleton / module-level helpers
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_get_stable_memory_manager(self, tmp_storage):
        from Engine8_Knowledge.memory.stable_mem0 import (
            StableMemoryManager,
            get_stable_memory_manager,
            reset_stable_memory_manager,
        )

        reset_stable_memory_manager()
        with patch.object(StableMemoryManager, "_init_mem0"):
            mgr1 = get_stable_memory_manager(storage_dir=tmp_storage)
            mgr2 = get_stable_memory_manager()
        assert mgr1 is mgr2

    def test_reset_creates_new_instance(self, tmp_storage):
        from Engine8_Knowledge.memory.stable_mem0 import (
            StableMemoryManager,
            get_stable_memory_manager,
            reset_stable_memory_manager,
        )

        reset_stable_memory_manager()
        with patch.object(StableMemoryManager, "_init_mem0"):
            mgr1 = get_stable_memory_manager(storage_dir=tmp_storage)
        reset_stable_memory_manager()
        with patch.object(StableMemoryManager, "_init_mem0"):
            mgr2 = get_stable_memory_manager(storage_dir=tmp_storage)
        assert mgr1 is not mgr2
