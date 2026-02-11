"""Tests for Phase 50A — Shared Intelligence Feed."""

import pytest

from src.collaboration.shared_intel_feed import (
    SharedIntelligenceFeed,
    IntelItem,
    IntelType,
    IntelPriority,
    IntelComment,
    get_intel_feed,
)


@pytest.fixture
def feed():
    return SharedIntelligenceFeed()


# =========================================
# SEED DATA
# =========================================

def test_seed_data_loaded(feed):
    items = feed.get_feed()
    assert len(items) == 5


def test_seed_has_all_types(feed):
    items = feed.get_feed()
    types = {i.intel_type for i in items}
    assert IntelType.WIN_INTEL in types
    assert IntelType.COMPETITOR_MOVE in types
    assert IntelType.OPPORTUNITY_ALERT in types


# =========================================
# POST INTEL
# =========================================

def test_post_intel(feed):
    item = feed.post_intel(
        intel_type=IntelType.WIN_INTEL,
        priority=IntelPriority.HIGH,
        title="Won DCGS-A TO4",
        body="$8M ceiling over 2 years",
        author_id="rep_01",
        author_name="Sarah Mitchell",
        program="DCGS-A",
        tags=["win", "army"],
    )
    assert isinstance(item, IntelItem)
    assert item.intel_type == IntelType.WIN_INTEL
    assert item.title == "Won DCGS-A TO4"


def test_post_with_mentions(feed):
    item = feed.post_intel(
        intel_type=IntelType.CONTACT_UPDATE,
        priority=IntelPriority.NORMAL,
        title="Update",
        body="New POC",
        author_id="rep_01",
        author_name="Sarah Mitchell",
        mentions=["rep_02", "rep_03"],
    )
    assert "rep_02" in item.mentions


def test_post_unique_id(feed):
    i1 = feed.post_intel(IntelType.WIN_INTEL, IntelPriority.NORMAL, "A", "B", "r1", "Alice")
    i2 = feed.post_intel(IntelType.WIN_INTEL, IntelPriority.NORMAL, "C", "D", "r1", "Alice")
    assert i1.item_id != i2.item_id


# =========================================
# GET AND DELETE
# =========================================

def test_get_item(feed):
    items = feed.get_feed()
    item = feed.get_item(items[0].item_id)
    assert item is not None


def test_get_item_not_found(feed):
    assert feed.get_item("intel_9999") is None


def test_delete_item(feed):
    items = feed.get_feed()
    count_before = len(items)
    assert feed.delete_item(items[0].item_id) is True
    assert len(feed.get_feed()) == count_before - 1


# =========================================
# PIN / UNPIN
# =========================================

def test_pin_item(feed):
    items = feed.get_feed()
    assert feed.pin_item(items[-1].item_id) is True
    fetched = feed.get_item(items[-1].item_id)
    assert fetched.pinned is True


def test_pinned_items_first_in_feed(feed):
    items = feed.get_feed()
    last = items[-1]
    feed.pin_item(last.item_id)
    refreshed = feed.get_feed()
    assert refreshed[0].item_id == last.item_id


def test_unpin_item(feed):
    items = feed.get_feed()
    feed.pin_item(items[0].item_id)
    feed.unpin_item(items[0].item_id)
    assert feed.get_item(items[0].item_id).pinned is False


# =========================================
# REACTIONS
# =========================================

def test_add_reaction(feed):
    items = feed.get_feed()
    assert feed.add_reaction(items[0].item_id, "rep_01", "Sarah Mitchell", "thumbsup") is True
    item = feed.get_item(items[0].item_id)
    assert len(item.reactions) == 1


def test_no_duplicate_reaction(feed):
    items = feed.get_feed()
    feed.add_reaction(items[0].item_id, "rep_01", "Sarah Mitchell", "thumbsup")
    assert feed.add_reaction(items[0].item_id, "rep_01", "Sarah Mitchell", "thumbsup") is False


def test_different_emoji_allowed(feed):
    items = feed.get_feed()
    feed.add_reaction(items[0].item_id, "rep_01", "Sarah Mitchell", "thumbsup")
    assert feed.add_reaction(items[0].item_id, "rep_01", "Sarah Mitchell", "fire") is True
    item = feed.get_item(items[0].item_id)
    assert len(item.reactions) == 2


# =========================================
# COMMENTS
# =========================================

def test_add_comment(feed):
    items = feed.get_feed()
    comment = feed.add_comment(items[0].item_id, "rep_02", "James Chen", "Great work!")
    assert isinstance(comment, IntelComment)
    assert comment.text == "Great work!"


def test_comment_on_nonexistent(feed):
    assert feed.add_comment("intel_9999", "rep_01", "Alice", "Test") is None


def test_multiple_comments(feed):
    items = feed.get_feed()
    feed.add_comment(items[0].item_id, "rep_01", "Sarah", "First")
    feed.add_comment(items[0].item_id, "rep_02", "James", "Second")
    item = feed.get_item(items[0].item_id)
    assert len(item.comments) == 2


# =========================================
# FEED QUERIES
# =========================================

def test_feed_filter_type(feed):
    items = feed.get_feed(intel_type=IntelType.COMPETITOR_MOVE)
    assert len(items) >= 1
    assert all(i.intel_type == IntelType.COMPETITOR_MOVE for i in items)


def test_feed_filter_priority(feed):
    items = feed.get_feed(priority=IntelPriority.CRITICAL)
    assert len(items) >= 1
    assert all(i.priority == IntelPriority.CRITICAL for i in items)


def test_feed_filter_program(feed):
    items = feed.get_feed(program="DCGS-A")
    assert len(items) >= 1
    assert all(i.program == "DCGS-A" for i in items)


def test_feed_limit(feed):
    items = feed.get_feed(limit=2)
    assert len(items) == 2


def test_get_mentions(feed):
    feed.post_intel(
        IntelType.TEAM_UPDATE, IntelPriority.NORMAL,
        "Heads up", "Meeting moved", "rep_01", "Sarah",
        mentions=["rep_02"],
    )
    mentioned = feed.get_mentions("rep_02")
    assert len(mentioned) >= 1


def test_search_feed(feed):
    results = feed.search_feed("DCGS")
    assert len(results) >= 1


def test_search_feed_body(feed):
    results = feed.search_feed("Leidos")
    assert len(results) >= 1


# =========================================
# TO DICT
# =========================================

def test_item_to_dict(feed):
    items = feed.get_feed()
    d = items[0].to_dict()
    assert "item_id" in d
    assert "intel_type" in d
    assert "reaction_count" in d
    assert "comment_count" in d


# =========================================
# STATS
# =========================================

def test_stats(feed):
    stats = feed.get_stats()
    assert stats["total_items"] == 5
    assert "by_type" in stats
    assert "by_priority" in stats


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    import src.collaboration.shared_intel_feed as mod
    mod._instance = None
    s1 = get_intel_feed()
    s2 = get_intel_feed()
    assert s1 is s2
    mod._instance = None
