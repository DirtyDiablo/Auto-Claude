"""Phase 45A — MCP Ecosystem API (10 endpoints).

REST endpoints for tool registry, MCP Apps rendering, and orchestration.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from src.mcp.tool_registry import (
    MCPToolRegistry, MCPServerConfig, MCPServerEntry, MCPTool,
    MCPRoutingResult, HealthStatus, get_tool_registry,
)
from src.mcp.apps_renderer import (
    MCPAppsRenderer, MCPAppResponse, MCPAppAction, RenderedApp,
    get_apps_renderer,
)
from src.mcp.orchestrator import (
    MCPOrchestrator, MCPExecutionPlan, MCPExecutionStep,
    MCPExecutionResult, get_orchestrator,
)

logger = logging.getLogger(__name__)


# =========================================
# REQUEST MODELS
# =========================================

class RegisterServerRequest(BaseModel):
    name: str
    url: str
    transport: str = "http"
    capabilities: List[str] = Field(default_factory=list)
    priority: int = 5
    cost_tier: str = "free"
    tags: List[str] = Field(default_factory=list)


class RouteRequest(BaseModel):
    intent: str
    context: Dict[str, Any] = Field(default_factory=dict)


class RenderAppRequest(BaseModel):
    template_id: str
    data: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    title: str = ""
    server_id: str = ""


class RegisterTemplateRequest(BaseModel):
    template_id: str
    name: str
    html: str
    permissions: List[str] = Field(default_factory=lambda: ["display"])
    description: str = ""


class OrchestratePlanRequest(BaseModel):
    intent: str
    context: Dict[str, Any] = Field(default_factory=dict)


class OrchestrateExecuteRequest(BaseModel):
    plan_id: str


# =========================================
# ROUTE SETUP
# =========================================

def include_mcp_router(app: FastAPI) -> None:
    """Register all MCP ecosystem endpoints on the FastAPI app."""

    registry = get_tool_registry()
    renderer = get_apps_renderer()
    orchestrator = get_orchestrator()

    # --------------------------------------------------
    # 1. POST /api/mcp/registry/servers — Register new server
    # --------------------------------------------------
    @app.post("/api/mcp/registry/servers")
    async def mcp_register_server(req: RegisterServerRequest):
        """Register a new MCP server."""
        config = MCPServerConfig(
            name=req.name,
            url=req.url,
            transport=req.transport,
            capabilities=req.capabilities,
            priority=req.priority,
            cost_tier=req.cost_tier,
            tags=req.tags,
        )
        entry = registry.register_server(config)
        return {
            "server_id": entry.config.server_id,
            "name": entry.config.name,
            "health": entry.health,
            "tools": len(entry.tools),
            "registered_at": entry.registered_at,
        }

    # --------------------------------------------------
    # 2. GET /api/mcp/registry/servers — List all servers
    # --------------------------------------------------
    @app.get("/api/mcp/registry/servers")
    async def mcp_list_servers(
        capability: str = "",
        healthy_only: bool = False,
    ):
        """List all registered MCP servers with health."""
        servers = registry.list_servers(capability=capability, healthy_only=healthy_only)
        return {
            "servers": [_serialize_server(e) for e in servers],
            "total": len(servers),
        }

    # --------------------------------------------------
    # 3. GET /api/mcp/registry/tools — List all tools
    # --------------------------------------------------
    @app.get("/api/mcp/registry/tools")
    async def mcp_list_tools():
        """List all available tools across servers."""
        tools = registry.get_all_tools()
        return {
            "tools": [_serialize_tool(t) for t in tools],
            "total": len(tools),
        }

    # --------------------------------------------------
    # 4. POST /api/mcp/registry/discover/{server_id} — Discover tools
    # --------------------------------------------------
    @app.post("/api/mcp/registry/discover/{server_id}")
    async def mcp_discover(server_id: str):
        """Trigger tool discovery for a server."""
        server = registry.get_server(server_id)
        if not server:
            raise HTTPException(404, "Server not found")
        tools = registry.discover_tools(server_id)
        return {
            "server_id": server_id,
            "tools": [_serialize_tool(t) for t in tools],
            "total": len(tools),
        }

    # --------------------------------------------------
    # 5. GET /api/mcp/registry/health — Health status
    # --------------------------------------------------
    @app.get("/api/mcp/registry/health")
    async def mcp_health():
        """Health status of all registered servers."""
        statuses = registry.health_check_all()
        return {
            "servers": statuses,
            "total": len(statuses),
            "healthy": sum(1 for s in statuses.values() if s == "healthy"),
            "degraded": sum(1 for s in statuses.values() if s == "degraded"),
            "unhealthy": sum(1 for s in statuses.values() if s == "unhealthy"),
        }

    # --------------------------------------------------
    # 6. POST /api/mcp/route — Intelligent routing
    # --------------------------------------------------
    @app.post("/api/mcp/route")
    async def mcp_route(req: RouteRequest):
        """Route an intent to the best MCP server."""
        result = registry.route_request(req.intent, req.context)
        return {
            "intent": result.intent,
            "selected_server": result.selected_server,
            "selected_tool": result.selected_tool,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "matched_servers": result.matched_servers,
            "fallback_servers": result.fallback_servers,
        }

    # --------------------------------------------------
    # 7. POST /api/mcp/apps/render — Render MCP App
    # --------------------------------------------------
    @app.post("/api/mcp/apps/render")
    async def mcp_render_app(req: RenderAppRequest):
        """Render an MCP App response."""
        actions = [
            MCPAppAction(
                action_id=a.get("action_id", f"action_{i}"),
                tool_call=a.get("tool_call", ""),
                parameters=a.get("parameters", {}),
                requires_approval=a.get("requires_approval", True),
            )
            for i, a in enumerate(req.actions)
        ]
        app_response = MCPAppResponse(
            template_id=req.template_id,
            data=req.data,
            actions=actions,
            title=req.title,
            server_id=req.server_id,
        )
        rendered = renderer.render_app(app_response)
        return _serialize_rendered(rendered)

    # --------------------------------------------------
    # 8. POST /api/mcp/apps/templates — Register template
    # --------------------------------------------------
    @app.post("/api/mcp/apps/templates")
    async def mcp_register_template(req: RegisterTemplateRequest):
        """Register a new MCP App template."""
        template = renderer.register_template(
            template_id=req.template_id,
            name=req.name,
            html=req.html,
            permissions=req.permissions,
            description=req.description,
        )
        return {
            "template_id": template.template_id,
            "name": template.name,
            "permissions": template.permissions,
            "created_at": template.created_at,
        }

    # --------------------------------------------------
    # 9. POST /api/mcp/orchestrate — Execute multi-tool plan
    # --------------------------------------------------
    @app.post("/api/mcp/orchestrate")
    async def mcp_orchestrate(req: OrchestrateExecuteRequest):
        """Execute a previously generated plan."""
        plan = orchestrator.get_plan(req.plan_id)
        if not plan:
            raise HTTPException(404, "Plan not found")
        result = orchestrator.execute_plan(plan)
        return _serialize_execution(result)

    # --------------------------------------------------
    # 10. POST /api/mcp/orchestrate/plan — Generate plan
    # --------------------------------------------------
    @app.post("/api/mcp/orchestrate/plan")
    async def mcp_generate_plan(req: OrchestratePlanRequest):
        """Generate an execution plan from natural language intent."""
        plan = orchestrator.plan_from_intent(req.intent, req.context)
        return {
            "plan_id": plan.plan_id,
            "intent": plan.intent,
            "status": plan.status,
            "steps": [_serialize_step(s) for s in plan.steps],
            "total_steps": len(plan.steps),
            "estimated_cost": plan.estimated_cost,
            "estimated_time_ms": plan.estimated_time_ms,
            "created_at": plan.created_at,
        }

    logger.info("MCP Ecosystem API: 10 endpoints registered under /api/mcp/*")


# =========================================
# SERIALIZATION HELPERS
# =========================================

def _serialize_server(e: MCPServerEntry) -> Dict[str, Any]:
    return {
        "server_id": e.config.server_id,
        "name": e.config.name,
        "url": e.config.url,
        "transport": e.config.transport,
        "capabilities": e.config.capabilities,
        "priority": e.config.priority,
        "cost_tier": e.config.cost_tier,
        "tags": e.config.tags,
        "health": e.health,
        "tools": len(e.tools),
        "total_calls": e.total_calls,
        "error_rate": e.error_rate,
        "registered_at": e.registered_at,
    }


def _serialize_tool(t: MCPTool) -> Dict[str, Any]:
    return {
        "name": t.name,
        "description": t.description,
        "server_id": t.server_id,
        "input_schema": t.input_schema,
        "estimated_latency_ms": t.estimated_latency_ms,
        "cost_per_call": t.cost_per_call,
        "rate_limit": t.rate_limit,
        "auth_required": t.auth_required,
    }


def _serialize_rendered(r: RenderedApp) -> Dict[str, Any]:
    return {
        "id": r.id,
        "template_id": r.template_id,
        "status": r.status,
        "html": r.html,
        "data": r.data,
        "actions": [
            {"action_id": a.action_id, "tool_call": a.tool_call,
             "status": a.status, "requires_approval": a.requires_approval}
            for a in r.actions
        ],
        "sandbox_config": r.sandbox_config,
        "rendered_at": r.rendered_at,
    }


def _serialize_step(s: MCPExecutionStep) -> Dict[str, Any]:
    return {
        "step_id": s.step_id,
        "server_id": s.server_id,
        "tool_name": s.tool_name,
        "parameters": s.parameters,
        "depends_on": s.depends_on,
        "status": s.status,
        "cost": s.cost,
    }


def _serialize_execution(r: MCPExecutionResult) -> Dict[str, Any]:
    return {
        "plan_id": r.plan_id,
        "status": r.status,
        "steps_completed": r.steps_completed,
        "steps_failed": r.steps_failed,
        "steps_skipped": r.steps_skipped,
        "total_cost": r.total_cost,
        "total_latency_ms": r.total_latency_ms,
        "errors": r.errors,
        "completed_at": r.completed_at,
    }
