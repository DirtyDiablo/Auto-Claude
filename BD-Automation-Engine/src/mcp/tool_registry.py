"""Phase 45A — MCP Tool Registry.

Dynamic registry that discovers, catalogs, health-monitors, and
intelligently routes to MCP servers across the ecosystem.
"""

from __future__ import annotations

import hashlib
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


# =========================================
# ENUMS & DATA CLASSES
# =========================================

class TransportType(str, Enum):
    SSE = "sse"
    STDIO = "stdio"
    HTTP = "http"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CostTier(str, Enum):
    FREE = "free"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class MCPAuth:
    auth_type: str = "bearer"  # bearer | api_key | oauth
    token: str = ""
    header_name: str = "Authorization"


@dataclass
class MCPTool:
    name: str = ""
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    estimated_latency_ms: int = 500
    cost_per_call: float = 0.0
    rate_limit: int = 0  # calls per minute, 0 = unlimited
    auth_required: bool = False
    server_id: str = ""


@dataclass
class MCPServerConfig:
    server_id: str = ""
    name: str = ""
    url: str = ""
    transport: str = "http"
    auth: Optional[MCPAuth] = None
    capabilities: List[str] = field(default_factory=list)
    priority: int = 5  # 1=highest, 10=lowest
    cost_tier: str = "free"
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.server_id:
            raw = f"{self.name}:{self.url}:{datetime.utcnow().isoformat()}"
            self.server_id = f"mcp_{hashlib.md5(raw.encode()).hexdigest()[:10]}"


@dataclass
class MCPServerEntry:
    config: MCPServerConfig = field(default_factory=MCPServerConfig)
    tools: List[MCPTool] = field(default_factory=list)
    health: str = "unknown"
    last_health_check: str = ""
    last_latency_ms: int = 0
    total_calls: int = 0
    total_errors: int = 0
    error_rate: float = 0.0
    registered_at: str = ""
    last_used: str = ""

    def __post_init__(self):
        if not self.registered_at:
            self.registered_at = datetime.utcnow().isoformat()


@dataclass
class MCPRoutingResult:
    intent: str = ""
    matched_servers: List[Dict[str, Any]] = field(default_factory=list)
    selected_server: str = ""
    selected_tool: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    fallback_servers: List[str] = field(default_factory=list)


@dataclass
class UsageRecord:
    server_id: str = ""
    tool_name: str = ""
    success: bool = True
    latency_ms: int = 0
    timestamp: str = ""
    error: str = ""


# =========================================
# BUILT-IN SERVER CONFIGS
# =========================================

_BUILTIN_SERVERS: List[MCPServerConfig] = [
    MCPServerConfig(
        server_id="mcp_notion",
        name="Notion MCP",
        url="stdio://notion-mcp",
        transport="stdio",
        capabilities=["database_query", "page_read", "page_write", "contacts", "programs", "jobs"],
        priority=2,
        cost_tier="free",
        tags=["crm", "database", "productivity"],
    ),
    MCPServerConfig(
        server_id="mcp_google_maps",
        name="Google Maps MCP",
        url="https://maps-mcp.googleapis.com/v1",
        transport="http",
        capabilities=["geocoding", "distance_matrix", "place_search", "directions", "geographic"],
        priority=3,
        cost_tier="low",
        tags=["maps", "location", "geographic"],
    ),
    MCPServerConfig(
        server_id="mcp_slack",
        name="Slack MCP",
        url="https://slack-mcp.example.com/v1",
        transport="sse",
        capabilities=["send_message", "channel_list", "user_lookup", "thread_reply", "team_coordination"],
        priority=3,
        cost_tier="free",
        tags=["messaging", "team", "notifications"],
    ),
    MCPServerConfig(
        server_id="mcp_github",
        name="GitHub MCP",
        url="stdio://github-mcp",
        transport="stdio",
        capabilities=["repo_management", "issue_tracking", "pr_review", "ci_cd", "code_search"],
        priority=4,
        cost_tier="free",
        tags=["code", "devops", "vcs"],
    ),
    MCPServerConfig(
        server_id="mcp_google_workspace",
        name="Google Workspace MCP",
        url="https://workspace-mcp.googleapis.com/v1",
        transport="http",
        capabilities=["email_send", "email_draft", "calendar_create", "calendar_list", "email_sequence"],
        priority=2,
        cost_tier="low",
        tags=["email", "calendar", "productivity"],
    ),
    MCPServerConfig(
        server_id="mcp_filesystem",
        name="Filesystem MCP",
        url="stdio://filesystem-mcp",
        transport="stdio",
        capabilities=["file_read", "file_write", "file_list", "file_search"],
        priority=5,
        cost_tier="free",
        tags=["filesystem", "local"],
    ),
    MCPServerConfig(
        server_id="mcp_memory",
        name="Memory MCP",
        url="stdio://memory-mcp",
        transport="stdio",
        capabilities=["knowledge_store", "knowledge_recall", "entity_create", "relation_create"],
        priority=4,
        cost_tier="free",
        tags=["memory", "knowledge_graph"],
    ),
    MCPServerConfig(
        server_id="mcp_day_ai",
        name="Day AI MCP",
        url="https://api.day.ai/mcp/v1",
        transport="http",
        capabilities=["contact_enrich", "linkedin_activity", "company_intel", "contact_intelligence"],
        priority=3,
        cost_tier="medium",
        tags=["contacts", "enrichment", "intelligence"],
    ),
    MCPServerConfig(
        server_id="mcp_n8n",
        name="n8n Workflow MCP",
        url="http://localhost:5678/mcp",
        transport="http",
        capabilities=["workflow_trigger", "workflow_list", "workflow_status", "automation"],
        priority=4,
        cost_tier="free",
        tags=["automation", "workflow", "integration"],
    ),
]

# Tool definitions for built-in servers
_BUILTIN_TOOLS: Dict[str, List[MCPTool]] = {
    "mcp_notion": [
        MCPTool(name="query_database", description="Query a Notion database with filters",
                input_schema={"database_id": "string", "filter": "object"}, server_id="mcp_notion"),
        MCPTool(name="read_page", description="Read a Notion page by ID",
                input_schema={"page_id": "string"}, server_id="mcp_notion"),
        MCPTool(name="create_page", description="Create a new Notion page",
                input_schema={"parent_id": "string", "properties": "object"}, server_id="mcp_notion"),
    ],
    "mcp_google_maps": [
        MCPTool(name="geocode", description="Convert address to coordinates",
                input_schema={"address": "string"}, server_id="mcp_google_maps", cost_per_call=0.005),
        MCPTool(name="distance_matrix", description="Calculate distances between locations",
                input_schema={"origins": "array", "destinations": "array"}, server_id="mcp_google_maps", cost_per_call=0.01),
        MCPTool(name="place_search", description="Search for places near a location",
                input_schema={"query": "string", "location": "string"}, server_id="mcp_google_maps", cost_per_call=0.02),
    ],
    "mcp_slack": [
        MCPTool(name="send_message", description="Send a message to a Slack channel",
                input_schema={"channel": "string", "text": "string"}, server_id="mcp_slack"),
        MCPTool(name="list_channels", description="List available Slack channels",
                input_schema={}, server_id="mcp_slack"),
        MCPTool(name="lookup_user", description="Look up a Slack user",
                input_schema={"email": "string"}, server_id="mcp_slack"),
    ],
    "mcp_github": [
        MCPTool(name="search_code", description="Search code across repositories",
                input_schema={"query": "string", "repo": "string"}, server_id="mcp_github"),
        MCPTool(name="create_issue", description="Create a GitHub issue",
                input_schema={"repo": "string", "title": "string", "body": "string"}, server_id="mcp_github"),
    ],
    "mcp_google_workspace": [
        MCPTool(name="draft_email", description="Draft an email in Gmail",
                input_schema={"to": "string", "subject": "string", "body": "string"}, server_id="mcp_google_workspace"),
        MCPTool(name="send_email", description="Send an email via Gmail",
                input_schema={"to": "string", "subject": "string", "body": "string"}, server_id="mcp_google_workspace", cost_per_call=0.001),
        MCPTool(name="create_event", description="Create a Google Calendar event",
                input_schema={"title": "string", "start": "string", "end": "string"}, server_id="mcp_google_workspace"),
        MCPTool(name="list_events", description="List upcoming calendar events",
                input_schema={"days": "integer"}, server_id="mcp_google_workspace"),
    ],
    "mcp_filesystem": [
        MCPTool(name="read_file", description="Read a local file", input_schema={"path": "string"}, server_id="mcp_filesystem"),
        MCPTool(name="write_file", description="Write a local file", input_schema={"path": "string", "content": "string"}, server_id="mcp_filesystem"),
    ],
    "mcp_memory": [
        MCPTool(name="store_memory", description="Store a knowledge entity",
                input_schema={"content": "string", "metadata": "object"}, server_id="mcp_memory"),
        MCPTool(name="recall_memory", description="Recall stored knowledge",
                input_schema={"query": "string"}, server_id="mcp_memory"),
    ],
    "mcp_day_ai": [
        MCPTool(name="enrich_contact", description="Enrich a contact with Day AI intelligence",
                input_schema={"name": "string", "company": "string"}, server_id="mcp_day_ai", cost_per_call=0.05),
        MCPTool(name="company_intel", description="Get company intelligence",
                input_schema={"company": "string"}, server_id="mcp_day_ai", cost_per_call=0.03),
    ],
    "mcp_n8n": [
        MCPTool(name="trigger_workflow", description="Trigger an n8n workflow",
                input_schema={"workflow_id": "string", "data": "object"}, server_id="mcp_n8n"),
        MCPTool(name="list_workflows", description="List available n8n workflows",
                input_schema={}, server_id="mcp_n8n"),
    ],
}

# Intent-to-capability mapping for routing
_INTENT_KEYWORDS: Dict[str, List[str]] = {
    "email": ["email_send", "email_draft", "email_sequence"],
    "send email": ["email_send", "email_draft"],
    "draft email": ["email_draft"],
    "calendar": ["calendar_create", "calendar_list"],
    "schedule": ["calendar_create"],
    "meeting": ["calendar_create"],
    "message": ["send_message"],
    "slack": ["send_message", "channel_list", "thread_reply"],
    "post": ["send_message"],
    "notify": ["send_message"],
    "distance": ["distance_matrix", "geocoding"],
    "map": ["geocoding", "place_search"],
    "location": ["geocoding", "place_search", "geographic"],
    "directions": ["directions"],
    "contact": ["contact_enrich", "contacts", "contact_intelligence"],
    "enrich": ["contact_enrich", "linkedin_activity"],
    "linkedin": ["linkedin_activity", "contact_enrich"],
    "database": ["database_query"],
    "notion": ["database_query", "page_read"],
    "query": ["database_query", "code_search"],
    "workflow": ["workflow_trigger", "workflow_list"],
    "automate": ["workflow_trigger", "automation"],
    "trigger": ["workflow_trigger"],
    "file": ["file_read", "file_write"],
    "code": ["code_search", "repo_management"],
    "github": ["repo_management", "issue_tracking", "pr_review"],
    "issue": ["issue_tracking"],
    "remember": ["knowledge_store", "knowledge_recall"],
    "knowledge": ["knowledge_store", "knowledge_recall"],
    "company": ["company_intel"],
}


# =========================================
# HEALTH MONITOR
# =========================================

class HealthMonitor:
    """Tracks health of MCP servers with periodic checks."""

    def __init__(self, check_interval: int = 60) -> None:
        self.check_interval = check_interval
        self._history: Dict[str, List[Dict[str, Any]]] = {}

    def record_check(self, server_id: str, healthy: bool, latency_ms: int = 0) -> HealthStatus:
        """Record a health check result and compute status."""
        self._history.setdefault(server_id, []).append({
            "healthy": healthy,
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat(),
        })
        # Keep last 10 checks
        self._history[server_id] = self._history[server_id][-10:]

        recent = self._history[server_id]
        healthy_count = sum(1 for c in recent if c["healthy"])
        total = len(recent)

        if healthy_count == total:
            return HealthStatus.HEALTHY
        elif healthy_count >= total * 0.5:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY

    def get_history(self, server_id: str) -> List[Dict[str, Any]]:
        return list(self._history.get(server_id, []))


# =========================================
# USAGE TRACKER
# =========================================

class UsageTracker:
    """Tracks usage patterns across MCP servers."""

    def __init__(self) -> None:
        self._records: List[UsageRecord] = []

    def record(self, record: UsageRecord) -> None:
        self._records.append(record)

    def get_usage(self, server_id: str = "") -> Dict[str, Any]:
        records = self._records
        if server_id:
            records = [r for r in records if r.server_id == server_id]

        total = len(records)
        successes = sum(1 for r in records if r.success)
        latencies = [r.latency_ms for r in records if r.latency_ms > 0]

        return {
            "total_calls": total,
            "success_rate": round(successes / max(total, 1), 2),
            "avg_latency_ms": round(statistics.mean(latencies), 1) if latencies else 0,
            "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0, 1),
        }


# =========================================
# MCP TOOL REGISTRY
# =========================================

class MCPToolRegistry:
    """Central registry for all MCP server connections."""

    def __init__(self, seed_builtins: bool = True) -> None:
        self.servers: Dict[str, MCPServerEntry] = {}
        self.capability_index: Dict[str, List[str]] = {}
        self.health_monitor = HealthMonitor()
        self.usage_tracker = UsageTracker()

        if seed_builtins:
            self._seed_builtins()

    def _seed_builtins(self) -> None:
        """Register built-in MCP server configs."""
        for config in _BUILTIN_SERVERS:
            entry = MCPServerEntry(config=config, health=HealthStatus.HEALTHY.value)
            tools = _BUILTIN_TOOLS.get(config.server_id, [])
            entry.tools = tools
            self.servers[config.server_id] = entry
            # Index capabilities
            for cap in config.capabilities:
                self.capability_index.setdefault(cap, []).append(config.server_id)

    # --------------------------------------------------
    # REGISTRATION
    # --------------------------------------------------

    def register_server(self, config: MCPServerConfig) -> MCPServerEntry:
        """Register an MCP server and index its capabilities."""
        entry = MCPServerEntry(config=config, health=HealthStatus.UNKNOWN.value)
        self.servers[config.server_id] = entry

        # Index capabilities
        for cap in config.capabilities:
            if config.server_id not in self.capability_index.get(cap, []):
                self.capability_index.setdefault(cap, []).append(config.server_id)

        return entry

    def unregister_server(self, server_id: str) -> bool:
        """Remove a server from the registry."""
        if server_id not in self.servers:
            return False
        entry = self.servers.pop(server_id)
        # Clean capability index
        for cap in entry.config.capabilities:
            if cap in self.capability_index:
                self.capability_index[cap] = [
                    sid for sid in self.capability_index[cap] if sid != server_id
                ]
        return True

    # --------------------------------------------------
    # DISCOVERY
    # --------------------------------------------------

    def discover_tools(self, server_id: str) -> List[MCPTool]:
        """Discover tools available on a server (returns known tools)."""
        entry = self.servers.get(server_id)
        if not entry:
            return []
        # In production, this would do an MCP handshake.
        # Here we return the known tools.
        if not entry.tools:
            entry.tools = _BUILTIN_TOOLS.get(server_id, [])
        return entry.tools

    def get_all_tools(self) -> List[MCPTool]:
        """Get all tools across all registered servers."""
        tools: List[MCPTool] = []
        for entry in self.servers.values():
            tools.extend(entry.tools)
        return tools

    # --------------------------------------------------
    # ROUTING
    # --------------------------------------------------

    def route_request(self, intent: str, context: Optional[Dict] = None) -> MCPRoutingResult:
        """Intelligent routing: find the best MCP server for an intent."""
        context = context or {}
        intent_lower = intent.lower()

        # Find matching capabilities from intent keywords
        matched_caps: List[str] = []
        for keyword, caps in _INTENT_KEYWORDS.items():
            if keyword in intent_lower:
                matched_caps.extend(caps)
        matched_caps = list(set(matched_caps))

        if not matched_caps:
            return MCPRoutingResult(
                intent=intent,
                confidence=0.0,
                reasoning="No matching capabilities found for intent",
            )

        # Find servers that provide matched capabilities
        candidates: Dict[str, Dict[str, Any]] = {}
        for cap in matched_caps:
            for server_id in self.capability_index.get(cap, []):
                entry = self.servers.get(server_id)
                if not entry:
                    continue
                if server_id not in candidates:
                    candidates[server_id] = {
                        "server_id": server_id,
                        "name": entry.config.name,
                        "matched_capabilities": [],
                        "priority": entry.config.priority,
                        "health": entry.health,
                        "cost_tier": entry.config.cost_tier,
                        "score": 0.0,
                    }
                candidates[server_id]["matched_capabilities"].append(cap)

        if not candidates:
            return MCPRoutingResult(
                intent=intent,
                confidence=0.0,
                reasoning="No servers provide matching capabilities",
            )

        # Score candidates
        cost_weights = {"free": 0, "low": 1, "medium": 3, "high": 5}
        health_weights = {"healthy": 0, "degraded": 5, "unhealthy": 20, "unknown": 10}

        for c in candidates.values():
            cap_score = len(c["matched_capabilities"]) * 20
            priority_score = (10 - c["priority"]) * 5
            cost_penalty = cost_weights.get(c["cost_tier"], 3)
            health_penalty = health_weights.get(c["health"], 10)
            c["score"] = cap_score + priority_score - cost_penalty - health_penalty

        # Sort by score descending
        ranked = sorted(candidates.values(), key=lambda c: c["score"], reverse=True)
        best = ranked[0]

        # Find best matching tool
        best_entry = self.servers[best["server_id"]]
        selected_tool = ""
        for tool in best_entry.tools:
            for cap in best["matched_capabilities"]:
                if cap in tool.name or any(kw in tool.description.lower() for kw in intent_lower.split()):
                    selected_tool = tool.name
                    break
            if selected_tool:
                break
        if not selected_tool and best_entry.tools:
            selected_tool = best_entry.tools[0].name

        confidence = min(best["score"] / 60, 0.99)

        return MCPRoutingResult(
            intent=intent,
            matched_servers=[{
                "server_id": c["server_id"],
                "name": c["name"],
                "score": round(c["score"], 1),
                "matched_capabilities": c["matched_capabilities"],
            } for c in ranked],
            selected_server=best["server_id"],
            selected_tool=selected_tool,
            confidence=round(confidence, 2),
            reasoning=f"Matched {len(best['matched_capabilities'])} capabilities on {best['name']}",
            fallback_servers=[c["server_id"] for c in ranked[1:3]],
        )

    # --------------------------------------------------
    # HEALTH
    # --------------------------------------------------

    def health_check(self, server_id: str, healthy: bool = True, latency_ms: int = 50) -> str:
        """Record a health check for a specific server."""
        entry = self.servers.get(server_id)
        if not entry:
            return HealthStatus.UNKNOWN.value
        status = self.health_monitor.record_check(server_id, healthy, latency_ms)
        entry.health = status.value
        entry.last_health_check = datetime.utcnow().isoformat()
        entry.last_latency_ms = latency_ms
        return status.value

    def health_check_all(self) -> Dict[str, str]:
        """Check all registered servers. Returns health status dict."""
        results: Dict[str, str] = {}
        for server_id, entry in self.servers.items():
            # Simulate check — in production this pings each server
            status = self.health_monitor.record_check(
                server_id, healthy=True, latency_ms=50,
            )
            entry.health = status.value
            entry.last_health_check = datetime.utcnow().isoformat()
            results[server_id] = status.value
        return results

    # --------------------------------------------------
    # USAGE
    # --------------------------------------------------

    def record_usage(self, server_id: str, tool_name: str,
                     success: bool = True, latency_ms: int = 100) -> None:
        """Record a tool usage event."""
        entry = self.servers.get(server_id)
        if entry:
            entry.total_calls += 1
            if not success:
                entry.total_errors += 1
            entry.error_rate = round(entry.total_errors / max(entry.total_calls, 1), 2)
            entry.last_used = datetime.utcnow().isoformat()

        self.usage_tracker.record(UsageRecord(
            server_id=server_id,
            tool_name=tool_name,
            success=success,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow().isoformat(),
        ))

    # --------------------------------------------------
    # QUERIES
    # --------------------------------------------------

    def get_server(self, server_id: str) -> Optional[MCPServerEntry]:
        return self.servers.get(server_id)

    def list_servers(self, capability: str = "", healthy_only: bool = False) -> List[MCPServerEntry]:
        """List registered servers with optional filters."""
        results = list(self.servers.values())
        if capability:
            server_ids = set(self.capability_index.get(capability, []))
            results = [e for e in results if e.config.server_id in server_ids]
        if healthy_only:
            results = [e for e in results if e.health == HealthStatus.HEALTHY.value]
        return results

    def get_stats(self) -> Dict[str, Any]:
        total_tools = sum(len(e.tools) for e in self.servers.values())
        health_counts: Dict[str, int] = {}
        for e in self.servers.values():
            health_counts[e.health] = health_counts.get(e.health, 0) + 1

        return {
            "total_servers": len(self.servers),
            "total_tools": total_tools,
            "total_capabilities": len(self.capability_index),
            "by_health": health_counts,
            "by_transport": self._count_by(lambda e: e.config.transport),
            "by_cost_tier": self._count_by(lambda e: e.config.cost_tier),
            "usage": self.usage_tracker.get_usage(),
        }

    def _count_by(self, key_fn) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self.servers.values():
            k = key_fn(e)
            counts[k] = counts.get(k, 0) + 1
        return counts


# =========================================
# SINGLETON
# =========================================

_instance: Optional[MCPToolRegistry] = None


def get_tool_registry() -> MCPToolRegistry:
    global _instance
    if _instance is None:
        _instance = MCPToolRegistry()
    return _instance
