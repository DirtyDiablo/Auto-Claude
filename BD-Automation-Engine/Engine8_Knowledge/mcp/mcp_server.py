"""
Phase 26A — FastMCP 2.0 BD Intelligence Server

Custom MCP server exposing the PTS BD platform as native Claude Desktop tools.
21 tools across contact, program, search, and memory domains.
"""

import os
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class AsyncHubClient:
    """Async HTTP client for the Hub API."""

    def __init__(self, base_url: str = "http://localhost:8100"):
        self.base_url = base_url

    async def get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(f"{self.base_url}{path}", params=params or {})
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("hub_get_error", path=path, error=str(exc))
            return {}

    async def post(self, path: str, json: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{self.base_url}{path}", json=json or {})
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("hub_post_error", path=path, error=str(exc))
            return {}


class PTSBDMCPServer:
    """Custom MCP server exposing PTS BD platform to Claude Desktop."""

    def __init__(self, hub_url: str = "http://localhost:8100"):
        self.hub_url = hub_url
        self.hub = AsyncHubClient(hub_url)
        self._mcp = None
        self._tools_registered = 0

        logger.info("mcp_server_init", hub_url=hub_url)

    def _ensure_mcp(self):
        if self._mcp is not None:
            return self._mcp
        try:
            from fastmcp import FastMCP
            self._mcp = FastMCP("PTS BD Intelligence", version="1.0.0")
            self._register_tools()
            logger.info("fastmcp_initialized", tools=self._tools_registered)
        except ImportError:
            logger.warning("fastmcp_not_installed", hint="pip install fastmcp")
        return self._mcp

    def _register_tools(self):
        """Register all BD tools with the MCP server."""
        from Engine8_Knowledge.mcp.contact_tools import register_contact_tools
        from Engine8_Knowledge.mcp.program_tools import register_program_tools
        from Engine8_Knowledge.mcp.memory_tools import register_memory_tools

        self._tools_registered += register_contact_tools(self._mcp, self.hub)
        self._tools_registered += register_program_tools(self._mcp, self.hub)
        self._tools_registered += register_memory_tools(self._mcp, self.hub)

    async def start(self, transport: str = "sse", port: int = 8400):
        """Start MCP server with SSE transport for Claude Desktop."""
        mcp = self._ensure_mcp()
        if not mcp:
            raise RuntimeError("FastMCP not available")
        logger.info("mcp_server_starting", transport=transport, port=port)
        await mcp.run_async(transport=transport, port=port)

    def get_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        mcp = self._ensure_mcp()
        if not mcp:
            return []
        tools = []
        if hasattr(mcp, "_tools"):
            for name, tool in mcp._tools.items():
                tools.append({
                    "name": name,
                    "description": getattr(tool, "description", ""),
                })
        return tools

    def generate_claude_desktop_config(self) -> Dict[str, Any]:
        """Generate config block for claude_desktop_config.json."""
        return {
            "mcpServers": {
                "pts-bd": {
                    "url": f"http://localhost:8400/sse",
                    "description": "PTS BD Intelligence Platform — contacts, programs, search, memory",
                }
            }
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "tools_registered": self._tools_registered,
            "hub_url": self.hub_url,
            "server_ready": self._mcp is not None,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_server: Optional[PTSBDMCPServer] = None


def get_mcp_server(**kwargs) -> PTSBDMCPServer:
    global _server
    if _server is None:
        _server = PTSBDMCPServer(**kwargs)
    return _server
