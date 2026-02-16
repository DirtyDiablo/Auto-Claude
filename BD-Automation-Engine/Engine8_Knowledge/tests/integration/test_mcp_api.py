"""
Phase 26A — MCP API Tests

Tests 5 FastAPI endpoints: health, tools, config, test-tool, stats.
Uses TestClient with mocked MCP server backend.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from Engine8_Knowledge.api_routers.mcp_api import router


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
def mock_mcp_server():
    server = MagicMock()
    server.get_stats.return_value = {
        "tools_registered": 16,
        "hub_url": "http://localhost:8100",
        "server_ready": True,
    }
    server.get_tools.return_value = [
        {"name": "search_contacts", "description": "Search contacts"},
        {"name": "get_program_intel", "description": "Program intelligence"},
    ]
    server.generate_claude_desktop_config.return_value = {
        "mcpServers": {
            "pts-bd": {
                "url": "http://localhost:8400/sse",
                "description": "PTS BD Intelligence Platform",
            }
        }
    }
    server._mcp = MagicMock()
    server._mcp._tools = {
        "search_contacts": AsyncMock(return_value=[{"name": "Alice"}]),
    }
    return server


# ---------------------------------------------------------------------------
# TestHealth
# ---------------------------------------------------------------------------


class TestHealth:
    def test_mcp_health(self, client, mock_mcp_server):
        with patch(
            "Engine8_Knowledge.api_routers.mcp_api._get_mcp_server",
            return_value=mock_mcp_server,
        ):
            resp = client.get("/mcp/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["tools_registered"] == 16

    def test_mcp_health_unavailable(self, client):
        with patch(
            "Engine8_Knowledge.api_routers.mcp_api._get_mcp_server", return_value=None
        ):
            resp = client.get("/mcp/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "unavailable"


# ---------------------------------------------------------------------------
# TestListTools
# ---------------------------------------------------------------------------


class TestListTools:
    def test_list_tools(self, client, mock_mcp_server):
        with patch(
            "Engine8_Knowledge.api_routers.mcp_api._get_mcp_server",
            return_value=mock_mcp_server,
        ):
            resp = client.get("/mcp/tools")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["tools"]) == 2
        assert data["tools"][0]["name"] == "search_contacts"

    def test_list_tools_no_server(self, client):
        with patch(
            "Engine8_Knowledge.api_routers.mcp_api._get_mcp_server", return_value=None
        ):
            resp = client.get("/mcp/tools")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["tools"] == []


# ---------------------------------------------------------------------------
# TestGetConfig
# ---------------------------------------------------------------------------


class TestGetConfig:
    def test_get_config(self, client, mock_mcp_server):
        with patch(
            "Engine8_Knowledge.api_routers.mcp_api._get_mcp_server",
            return_value=mock_mcp_server,
        ):
            resp = client.get("/mcp/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "mcpServers" in data
        assert "pts-bd" in data["mcpServers"]

    def test_get_config_no_server(self, client):
        """Fallback config when server is unavailable."""
        with patch(
            "Engine8_Knowledge.api_routers.mcp_api._get_mcp_server", return_value=None
        ):
            resp = client.get("/mcp/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "mcpServers" in data
        assert "pts-bd" in data["mcpServers"]


# ---------------------------------------------------------------------------
# TestTestTool
# ---------------------------------------------------------------------------


class TestTestTool:
    def test_test_tool_not_found(self, client, mock_mcp_server):
        mock_mcp_server.get_tools.return_value = [
            {"name": "search_contacts", "description": "Search"},
        ]
        with patch(
            "Engine8_Knowledge.api_routers.mcp_api._get_mcp_server",
            return_value=mock_mcp_server,
        ):
            resp = client.post(
                "/mcp/test-tool",
                json={
                    "tool_name": "nonexistent_tool",
                    "parameters": {},
                },
            )
        assert resp.status_code == 404

    def test_test_tool_no_server(self, client):
        with patch(
            "Engine8_Knowledge.api_routers.mcp_api._get_mcp_server", return_value=None
        ):
            resp = client.post(
                "/mcp/test-tool",
                json={
                    "tool_name": "search_contacts",
                    "parameters": {"query": "test"},
                },
            )
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# TestStats
# ---------------------------------------------------------------------------


class TestStats:
    def test_mcp_stats(self, client, mock_mcp_server):
        with patch(
            "Engine8_Knowledge.api_routers.mcp_api._get_mcp_server",
            return_value=mock_mcp_server,
        ):
            resp = client.get("/mcp/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tools_registered"] == 16
        assert data["server_ready"] is True

    def test_mcp_stats_no_server(self, client):
        with patch(
            "Engine8_Knowledge.api_routers.mcp_api._get_mcp_server", return_value=None
        ):
            resp = client.get("/mcp/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tools_registered"] == 0
        assert data["server_ready"] is False
