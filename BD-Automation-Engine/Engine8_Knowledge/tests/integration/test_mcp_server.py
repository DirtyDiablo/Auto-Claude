"""
Phase 26A — MCP Server Tests

Tests PTSBDMCPServer: init, hub client, config generation, tool listing, stats.
Mocks FastMCP and HTTP client — no external services required.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.mcp.mcp_server import PTSBDMCPServer, AsyncHubClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def server():
    return PTSBDMCPServer(hub_url="http://localhost:8100")


@pytest.fixture
def mock_httpx_get():
    """Mock httpx.AsyncClient.get to return a JSON response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"contacts": [{"name": "Alice"}], "total": 1}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


@pytest.fixture
def mock_httpx_post():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": [], "count": 0}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ---------------------------------------------------------------------------
# TestInit
# ---------------------------------------------------------------------------


class TestInit:
    def test_init(self):
        s = PTSBDMCPServer(hub_url="http://test:8100")
        assert s.hub_url == "http://test:8100"
        assert s._mcp is None
        assert s._tools_registered == 0
        assert isinstance(s.hub, AsyncHubClient)


# ---------------------------------------------------------------------------
# TestHubClient
# ---------------------------------------------------------------------------


class TestHubClient:
    @pytest.mark.asyncio
    async def test_hub_client_get(self, mock_httpx_get):
        hub = AsyncHubClient(base_url="http://localhost:8100")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_httpx_get)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await hub.get("/api/v2/contacts", params={"q": "Alice"})
        assert result == {"contacts": [{"name": "Alice"}], "total": 1}

    @pytest.mark.asyncio
    async def test_hub_client_post(self, mock_httpx_post):
        hub = AsyncHubClient(base_url="http://localhost:8100")
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_httpx_post)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await hub.post("/search", json={"query": "DCGS"})
        assert result == {"results": [], "count": 0}

    @pytest.mark.asyncio
    async def test_hub_client_error(self):
        hub = AsyncHubClient(base_url="http://localhost:8100")
        with patch("httpx.AsyncClient", side_effect=Exception("Connection refused")):
            result = await hub.get("/api/v2/contacts")
        assert result == {}


# ---------------------------------------------------------------------------
# TestGenerateConfig
# ---------------------------------------------------------------------------


class TestGenerateConfig:
    def test_generate_config(self, server):
        config = server.generate_claude_desktop_config()
        assert "mcpServers" in config
        assert "pts-bd" in config["mcpServers"]
        assert "url" in config["mcpServers"]["pts-bd"]
        assert "8400" in config["mcpServers"]["pts-bd"]["url"]


# ---------------------------------------------------------------------------
# TestGetTools
# ---------------------------------------------------------------------------


class TestGetTools:
    def test_get_tools_empty(self, server):
        """Without FastMCP installed, tools list is empty."""
        with patch.dict("sys.modules", {"fastmcp": None}):
            server._mcp = None
            # _ensure_mcp will try import and fail
            tools = server.get_tools()
            assert isinstance(tools, list)


# ---------------------------------------------------------------------------
# TestStats
# ---------------------------------------------------------------------------


class TestStats:
    def test_get_stats(self, server):
        stats = server.get_stats()
        assert "tools_registered" in stats
        assert "hub_url" in stats
        assert "server_ready" in stats
        assert stats["hub_url"] == "http://localhost:8100"
        assert stats["tools_registered"] == 0


# ---------------------------------------------------------------------------
# TestEnsureMCP
# ---------------------------------------------------------------------------


class TestEnsureMCP:
    def test_ensure_mcp_no_fastmcp(self, server):
        """When FastMCP is not installed, _mcp stays None."""
        with patch.dict("sys.modules", {"fastmcp": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'fastmcp'")):
                result = server._ensure_mcp()
        # Should not crash, just return None
        assert result is None or server._mcp is None


# ---------------------------------------------------------------------------
# TestRegisterTools
# ---------------------------------------------------------------------------


class TestRegisterTools:
    def test_register_tools(self, server):
        """Test _register_tools calls all tool registrars."""
        mock_mcp = MagicMock()
        mock_mcp._tools = {}
        server._mcp = mock_mcp

        with patch("Engine8_Knowledge.mcp.contact_tools.register_contact_tools", return_value=5):
            with patch("Engine8_Knowledge.mcp.program_tools.register_program_tools", return_value=6):
                with patch("Engine8_Knowledge.mcp.memory_tools.register_memory_tools", return_value=5):
                    server._register_tools()

        assert server._tools_registered == 16

    def test_tools_registered_count(self, server):
        """After registration, tools count matches expected."""
        mock_mcp = MagicMock()
        mock_mcp._tools = {}
        server._mcp = mock_mcp

        with patch("Engine8_Knowledge.mcp.contact_tools.register_contact_tools", return_value=5):
            with patch("Engine8_Knowledge.mcp.program_tools.register_program_tools", return_value=6):
                with patch("Engine8_Knowledge.mcp.memory_tools.register_memory_tools", return_value=5):
                    server._register_tools()

        stats = server.get_stats()
        assert stats["tools_registered"] == 16


# ---------------------------------------------------------------------------
# TestSingleton
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_singleton(self):
        import Engine8_Knowledge.mcp.mcp_server as mod
        original = mod._server
        mod._server = None
        s1 = mod.get_mcp_server(hub_url="http://localhost:8100")
        s2 = mod.get_mcp_server()
        assert s1 is s2
        mod._server = original
