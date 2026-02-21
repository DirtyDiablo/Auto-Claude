"""Tests for Feature 9: Real-Time Notion & Bullhorn Sync Engine."""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.sync_engine import SyncEngine, _content_hash, SYNC_STATE_PATH


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def tmp_state_dir(tmp_path):
    """Provide a temporary directory for sync state files."""
    return tmp_path


@pytest.fixture
def engine(tmp_state_dir):
    """Create a SyncEngine with state stored in a temp directory."""
    with patch("services.sync_engine.SYNC_STATE_PATH", tmp_state_dir / "sync_state.json"):
        with patch("services.sync_engine.DATA_DIR", tmp_state_dir):
            eng = SyncEngine(poll_interval_seconds=5)
            yield eng


# =========================================
# STATE PERSISTENCE
# =========================================


def test_sync_state_persistence(tmp_state_dir):
    """Save and load sync state roundtrips correctly."""
    state_path = tmp_state_dir / "sync_state.json"

    with patch("services.sync_engine.SYNC_STATE_PATH", state_path):
        with patch("services.sync_engine.DATA_DIR", tmp_state_dir):
            engine = SyncEngine(poll_interval_seconds=60)

            # Modify state
            engine._sync_state["notion"]["last_sync"] = "2026-02-20T10:00:00+00:00"
            engine._sync_state["notion"]["databases"]["dcgs_contacts"] = {
                "last_edited": "2026-02-20T09:55:00Z",
                "records_synced": 150,
            }
            engine._sync_state["bullhorn"]["last_placement_id"] = 5432
            engine._sync_state["bullhorn"]["last_activity_id"] = 12001

            # Save
            engine._save_state()
            assert state_path.exists()

            # Load into a new engine
            engine2 = SyncEngine(poll_interval_seconds=60)
            assert engine2._sync_state["notion"]["last_sync"] == "2026-02-20T10:00:00+00:00"
            assert engine2._sync_state["bullhorn"]["last_placement_id"] == 5432
            assert engine2._sync_state["bullhorn"]["last_activity_id"] == 12001


def test_load_state_handles_missing_file(tmp_state_dir):
    """Engine initializes with defaults when state file does not exist."""
    state_path = tmp_state_dir / "nonexistent.json"

    with patch("services.sync_engine.SYNC_STATE_PATH", state_path):
        with patch("services.sync_engine.DATA_DIR", tmp_state_dir):
            engine = SyncEngine()
            assert engine._sync_state["notion"]["last_sync"] is None
            assert engine._sync_state["bullhorn"]["last_placement_id"] == 0


def test_load_state_handles_corrupt_json(tmp_state_dir):
    """Engine initializes with defaults when state file contains invalid JSON."""
    state_path = tmp_state_dir / "sync_state.json"
    state_path.write_text("not valid json {{{")

    with patch("services.sync_engine.SYNC_STATE_PATH", state_path):
        with patch("services.sync_engine.DATA_DIR", tmp_state_dir):
            engine = SyncEngine()
            assert engine._sync_state["notion"]["last_sync"] is None


# =========================================
# CONTENT HASH DEDUP
# =========================================


def test_content_hash_deterministic():
    """Same input produces the same hash."""
    data = {"name": "John", "company": "GDIT", "tier": 1}
    assert _content_hash(data) == _content_hash(data)


def test_content_hash_different_content():
    """Different input produces different hashes."""
    data_a = {"name": "John", "company": "GDIT"}
    data_b = {"name": "Jane", "company": "Leidos"}
    assert _content_hash(data_a) != _content_hash(data_b)


def test_content_hash_key_order_irrelevant():
    """Hash is stable regardless of key insertion order."""
    data_a = {"name": "John", "company": "GDIT"}
    data_b = {"company": "GDIT", "name": "John"}
    assert _content_hash(data_a) == _content_hash(data_b)


# =========================================
# RETRY QUEUE
# =========================================


@pytest.mark.asyncio
async def test_retry_queue_exponential_backoff(engine):
    """Failed items are scheduled for retry with increasing backoff."""
    engine._retry_queue = [
        {
            "source": "notion",
            "db_key": "dcgs_contacts",
            "error": "timeout",
            "retry_count": 0,
            "next_retry": "2020-01-01T00:00:00+00:00",  # In the past
        }
    ]

    # Mock Notion service to fail again
    mock_notion = MagicMock()
    mock_notion.query_database.side_effect = Exception("still failing")
    engine._notion_service = mock_notion

    await engine._process_retry_queue()

    assert len(engine._retry_queue) == 1
    assert engine._retry_queue[0]["retry_count"] == 1


@pytest.mark.asyncio
async def test_retry_exhausted_after_max_retries(engine):
    """Items are dropped after MAX_RETRIES failures."""
    engine._retry_queue = [
        {
            "source": "notion",
            "db_key": "dcgs_contacts",
            "error": "permanent failure",
            "retry_count": 3,  # Already at max
            "next_retry": "2020-01-01T00:00:00+00:00",
        }
    ]

    await engine._process_retry_queue()

    assert len(engine._retry_queue) == 0


def test_clear_retry_queue(engine):
    """clear_retry_queue removes all items and returns the count."""
    engine._retry_queue = [{"a": 1}, {"b": 2}, {"c": 3}]
    cleared = engine.clear_retry_queue()
    assert cleared == 3
    assert len(engine._retry_queue) == 0


# =========================================
# SYNC STATUS REPORTING
# =========================================


def test_sync_status_reporting(engine):
    """get_sync_status returns expected structure."""
    status = engine.get_sync_status()

    assert "running" in status
    assert status["running"] is False
    assert "sync_health" in status
    assert status["sync_health"] == "green"
    assert "notion" in status
    assert "bullhorn" in status
    assert "qdrant" in status
    assert "retry_queue_size" in status
    assert "poll_interval_seconds" in status
    assert status["poll_interval_seconds"] == 5


def test_sync_status_health_degrades_on_errors(engine):
    """Health degrades from green to yellow to red based on error count."""
    assert engine.get_sync_status()["sync_health"] == "green"

    engine._error_count = 3
    assert engine.get_sync_status()["sync_health"] == "yellow"

    engine._error_count = 10
    assert engine.get_sync_status()["sync_health"] == "red"


# =========================================
# NOTION POLLING
# =========================================


@pytest.mark.asyncio
async def test_notion_poll_filters_by_last_edited(engine):
    """Notion polling uses last_edited_time filter when a watermark exists."""
    mock_notion = MagicMock()
    mock_notion.query_database.return_value = {
        "results": [
            {
                "id": "page-1",
                "last_edited_time": "2026-02-20T12:00:00Z",
                "properties": {"Name": {"title": [{"text": {"content": "Test"}}]}},
            }
        ]
    }
    engine._notion_service = mock_notion

    # Set a watermark for one database
    engine._sync_state["notion"]["databases"]["dcgs_contacts"] = {
        "last_edited": "2026-02-20T10:00:00Z",
    }

    changes = await engine._poll_notion_changes()

    assert len(changes) >= 1

    # Verify that query_database was called with the last_edited_time filter
    # for the dcgs_contacts database
    calls = mock_notion.query_database.call_args_list
    dcgs_call = None
    for call in calls:
        kwargs = call.kwargs if call.kwargs else {}
        args = call.args if call.args else ()
        db_id = kwargs.get("database_id", args[0] if args else "")
        if "2ccdef65-baa5-8087-a53b-000ba596128e" in str(db_id):
            dcgs_call = call
            break

    assert dcgs_call is not None
    filter_arg = dcgs_call.kwargs.get("filter_obj") or (
        dcgs_call.args[1] if len(dcgs_call.args) > 1 else None
    )
    assert filter_arg is not None
    assert filter_arg["timestamp"] == "last_edited_time"
    assert filter_arg["last_edited_time"]["after"] == "2026-02-20T10:00:00Z"


# =========================================
# GRACEFUL SHUTDOWN
# =========================================


@pytest.mark.asyncio
async def test_graceful_shutdown(engine):
    """Engine stops cleanly without hanging."""
    # Mock services to avoid real calls
    engine._notion_service = MagicMock()
    engine._notion_service.query_database.return_value = {"results": []}
    engine._crm_manager = MagicMock()
    engine._crm_manager.pull_new_placements.return_value = {"placements": [], "count": 0}
    engine._crm_manager.pull_activity_updates.return_value = {"activities": [], "count": 0}
    engine._crm_manager._last_placement_id = 0
    engine._crm_manager._last_activity_id = 0

    await engine.start()
    assert engine._running is True

    await engine.stop()
    assert engine._running is False
    assert engine._task is not None
    assert engine._task.done()


@pytest.mark.asyncio
async def test_stop_when_not_running(engine):
    """Stopping an already-stopped engine is a no-op."""
    await engine.stop()
    assert engine._running is False


# =========================================
# SYNC HISTORY
# =========================================


def test_sync_history_limit(engine):
    """History is capped at 50 entries."""
    engine._sync_history = [{"cycle": i} for i in range(60)]
    history = engine.get_sync_history()
    assert len(history) == 50


def test_sync_history_custom_limit(engine):
    """get_sync_history respects the limit parameter."""
    engine._sync_history = [{"cycle": i} for i in range(20)]
    history = engine.get_sync_history(limit=5)
    assert len(history) == 5
