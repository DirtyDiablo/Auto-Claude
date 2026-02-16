"""
Phase 26A — MCP Server API

6 endpoints for MCP server health, tool listing, config generation,
tool testing, stats, and SSE transport.
"""

from typing import Any, Dict

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["mcp"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------


class TestToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Lazy getter
# ---------------------------------------------------------------------------


def _get_mcp_server():
    try:
        from Engine8_Knowledge.mcp.mcp_server import get_mcp_server

        return get_mcp_server()
    except Exception as exc:
        logger.warning("mcp_server_unavailable", error=str(exc))
        return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/mcp/health")
async def mcp_health():
    """MCP server health."""
    server = _get_mcp_server()
    if not server:
        return {"status": "unavailable", "message": "MCP server not initialized"}
    stats = server.get_stats()
    return {"status": "healthy", **stats}


@router.get("/mcp/tools")
async def list_tools():
    """List all registered MCP tools."""
    server = _get_mcp_server()
    if not server:
        return {"tools": [], "total": 0}
    tools = server.get_tools()
    return {"tools": tools, "total": len(tools)}


@router.get("/mcp/config")
async def get_config():
    """Generate Claude Desktop config JSON."""
    server = _get_mcp_server()
    if not server:
        return {
            "mcpServers": {
                "pts-bd": {
                    "url": "http://localhost:8400/sse",
                    "description": "PTS BD Intelligence Platform",
                }
            }
        }
    return server.generate_claude_desktop_config()


@router.post("/mcp/test-tool")
async def test_tool(req: TestToolRequest):
    """Test a specific tool with parameters."""
    server = _get_mcp_server()
    if not server:
        raise HTTPException(503, "MCP server not available")

    mcp = server._mcp
    if not mcp:
        raise HTTPException(503, "FastMCP not initialized")

    # Look up tool
    tools = server.get_tools()
    tool_names = [t["name"] for t in tools]
    if req.tool_name not in tool_names:
        raise HTTPException(
            404, f"Tool not found: {req.tool_name}. Available: {tool_names}"
        )

    try:
        if hasattr(mcp, "_tools") and req.tool_name in mcp._tools:
            handler = mcp._tools[req.tool_name]
            if callable(handler):
                result = await handler(**req.parameters)
                return {"tool": req.tool_name, "result": result}
    except Exception as exc:
        return {"tool": req.tool_name, "error": str(exc)}

    return {"tool": req.tool_name, "error": "Could not execute tool"}


@router.get("/mcp/stats")
async def mcp_stats():
    """Tool usage statistics."""
    server = _get_mcp_server()
    if not server:
        return {"tools_registered": 0, "server_ready": False}
    return server.get_stats()
