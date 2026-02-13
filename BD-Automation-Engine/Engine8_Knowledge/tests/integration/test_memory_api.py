"""
Phase 25A — Memory API Tests

Tests all 12 FastAPI endpoints for the 5-layer memory system.
Uses TestClient with mocked backends.
"""

import pytest
from unittest.mock import patch, AsyncMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from Engine8_Knowledge.api_routers.memory_api import router
from Engine8_Knowledge.memory.memory_store import (
    MemoryRecall,
    ContactMemory,
    LayerStats,
)
from Engine8_Knowledge.memory.mem0_manager import Memory, MemoryVersion, MemoryStats
from Engine8_Knowledge.memory.lifecycle import LifecycleReport


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app():
    if not FASTAPI_AVAILABLE:
        pytest.skip("FastAPI not installed")
    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_store():
    store = AsyncMock()
    store.add_memory = AsyncMock(return_value="mem_test_123")
    store.recall = AsyncMock(return_value=MemoryRecall(
        query="test",
        results={"episodic": [{"content": "test memory", "score": 0.8}]},
        total_results=1,
        layers_searched=["episodic"],
        recall_time_ms=5.0,
    ))
    store.get_contact_memory = AsyncMock(return_value=ContactMemory(
        contact_id="alice",
        contact_name="Alice Smith",
        interactions=[{"type": "call", "summary": "DCGS discussion"}],
        total_memories=1,
    ))
    store.remember_interaction = AsyncMock(return_value="mem_int_001")
    store.remember_outcome = AsyncMock(return_value="mem_out_001")
    store.get_layer_stats = AsyncMock(return_value={
        "short_term": LayerStats(layer="short_term", total_entries=5),
        "episodic": LayerStats(layer="episodic", total_entries=20),
        "procedural": LayerStats(layer="procedural", total_entries=10),
        "semantic": LayerStats(layer="semantic", total_entries=0),
        "graph": LayerStats(layer="graph", total_entries=0),
    })
    return store


@pytest.fixture
def mock_mem0():
    mem0 = AsyncMock()
    mem0.get_all = AsyncMock(return_value=[
        Memory(memory_id="m1", content="Agent memory 1", user_id="agent1", metadata={}),
        Memory(memory_id="m2", content="Agent memory 2", user_id="agent1", metadata={}),
    ])
    mem0.delete = AsyncMock(return_value=True)
    mem0.get_history = AsyncMock(return_value=[
        MemoryVersion(version=1, content="V1", updated_at="2025-01-01", change_type="created"),
        MemoryVersion(version=2, content="V2", updated_at="2025-01-02", change_type="updated"),
    ])
    mem0.get_stats = AsyncMock(return_value=MemoryStats(total_memories=50))
    return mem0


@pytest.fixture
def mock_lifecycle():
    lc = AsyncMock()
    lc.run_lifecycle = AsyncMock(return_value=LifecycleReport(
        started_at="2025-01-01T00:00:00",
        completed_at="2025-01-01T00:00:05",
        memories_consolidated=3,
        memories_decayed=2,
        memories_compressed=1,
        storage_saved_bytes=200,
        duration_seconds=5.0,
    ))
    return lc


# ---------------------------------------------------------------------------
# TestAddMemory
# ---------------------------------------------------------------------------


class TestAddMemory:
    def test_add_memory(self, client, mock_store):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_store", return_value=mock_store):
            resp = client.post("/memory/add", json={
                "content": "DCGS analyst meeting notes",
                "user_id": "u1",
                "layer": "episodic",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["memory_id"] == "mem_test_123"
        assert data["layer"] == "episodic"

    def test_add_memory_unavailable(self, client):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_store", return_value=None):
            resp = client.post("/memory/add", json={"content": "test"})
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# TestSearchMemory
# ---------------------------------------------------------------------------


class TestSearchMemory:
    def test_search_memory(self, client, mock_store):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_store", return_value=mock_store):
            resp = client.post("/memory/search", json={
                "query": "DCGS",
                "user_id": "u1",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert data["total_results"] == 1


# ---------------------------------------------------------------------------
# TestContactMemory
# ---------------------------------------------------------------------------


class TestContactMemory:
    def test_get_contact_memory(self, client, mock_store):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_store", return_value=mock_store):
            resp = client.get("/memory/contact/alice")
        assert resp.status_code == 200
        data = resp.json()
        assert data["contact_id"] == "alice"
        assert data["total_memories"] == 1


# ---------------------------------------------------------------------------
# TestAgentMemories
# ---------------------------------------------------------------------------


class TestAgentMemories:
    def test_get_agent_memories(self, client, mock_mem0):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_mem0", return_value=mock_mem0):
            resp = client.get("/memory/agent/agent1?limit=50")
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == "agent1"
        assert data["total"] == 2

    def test_get_agent_memories_no_mem0(self, client):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_mem0", return_value=None):
            resp = client.get("/memory/agent/agent1")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# ---------------------------------------------------------------------------
# TestDeleteMemory
# ---------------------------------------------------------------------------


class TestDeleteMemory:
    def test_delete_memory(self, client, mock_mem0):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_mem0", return_value=mock_mem0):
            resp = client.delete("/memory/mem_123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] is True
        assert data["memory_id"] == "mem_123"

    def test_delete_memory_unavailable(self, client):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_mem0", return_value=None):
            resp = client.delete("/memory/mem_123")
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# TestMemoryHistory
# ---------------------------------------------------------------------------


class TestMemoryHistory:
    def test_memory_history(self, client, mock_mem0):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_mem0", return_value=mock_mem0):
            resp = client.get("/memory/mem_123/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["memory_id"] == "mem_123"
        assert len(data["versions"]) == 2


# ---------------------------------------------------------------------------
# TestInteraction
# ---------------------------------------------------------------------------


class TestInteraction:
    def test_record_interaction(self, client, mock_store):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_store", return_value=mock_store):
            resp = client.post("/memory/interaction", json={
                "contact_id": "c123",
                "contact_name": "Alice Smith",
                "interaction_type": "call",
                "summary": "Discussed DCGS timeline",
                "sentiment": "positive",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["memory_id"] == "mem_int_001"
        assert data["contact_id"] == "c123"


# ---------------------------------------------------------------------------
# TestOutcome
# ---------------------------------------------------------------------------


class TestOutcome:
    def test_record_outcome(self, client, mock_store):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_store", return_value=mock_store):
            resp = client.post("/memory/outcome", json={
                "campaign_id": "camp1",
                "action": "Cold email",
                "outcome": "Meeting booked",
                "score": 0.9,
                "channel": "email",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["memory_id"] == "mem_out_001"
        assert data["campaign_id"] == "camp1"


# ---------------------------------------------------------------------------
# TestBriefing
# ---------------------------------------------------------------------------


class TestBriefing:
    def test_generate_briefing(self, client, mock_store):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_store", return_value=mock_store):
            resp = client.post("/memory/briefing", json={
                "agent_id": "agent_bd",
                "task_context": "Prepare for DCGS meeting",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == "agent_bd"
        assert "briefing" in data


# ---------------------------------------------------------------------------
# TestStats
# ---------------------------------------------------------------------------


class TestStats:
    def test_memory_stats(self, client, mock_store):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_store", return_value=mock_store):
            resp = client.get("/memory/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "layers" in data
        assert "short_term" in data["layers"]

    def test_memory_stats_no_store(self, client):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_store", return_value=None):
            resp = client.get("/memory/stats")
        assert resp.status_code == 200
        assert resp.json()["layers"] == {}


# ---------------------------------------------------------------------------
# TestLayerHealth
# ---------------------------------------------------------------------------


class TestLayerHealth:
    def test_layer_health(self, client, mock_store):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_store", return_value=mock_store):
            resp = client.get("/memory/layers")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_layers"] == 5
        for layer_name, layer_info in data["layers"].items():
            assert "status" in layer_info


# ---------------------------------------------------------------------------
# TestLifecycleRun
# ---------------------------------------------------------------------------


class TestLifecycleRun:
    def test_run_lifecycle(self, client, mock_lifecycle):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_lifecycle", return_value=mock_lifecycle):
            resp = client.post("/memory/lifecycle/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["memories_consolidated"] == 3
        assert data["memories_decayed"] == 2
        assert data["memories_compressed"] == 1

    def test_run_lifecycle_unavailable(self, client):
        with patch("Engine8_Knowledge.api_routers.memory_api._get_lifecycle", return_value=None):
            resp = client.post("/memory/lifecycle/run")
        assert resp.status_code == 503
