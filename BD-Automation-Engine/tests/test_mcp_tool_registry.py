"""Tests for Phase 45A — MCP Tool Registry."""

import pytest

from src.mcp.tool_registry import (
    MCPToolRegistry,
    MCPServerConfig,
    MCPTool,
    HealthMonitor,
    UsageTracker,
    get_tool_registry,
)


@pytest.fixture
def registry():
    return MCPToolRegistry(seed_builtins=True)


@pytest.fixture
def empty_registry():
    return MCPToolRegistry(seed_builtins=False)


# =========================================
# SEEDED SERVERS
# =========================================


def test_seeded_servers(registry):
    servers = registry.list_servers()
    assert len(servers) >= 9
    ids = {s.config.server_id for s in servers}
    assert "mcp_notion" in ids
    assert "mcp_google_maps" in ids
    assert "mcp_slack" in ids
    assert "mcp_github" in ids
    assert "mcp_google_workspace" in ids


def test_seeded_tools(registry):
    tools = registry.get_all_tools()
    assert len(tools) >= 20


def test_capability_index(registry):
    assert "email_send" in registry.capability_index
    assert "geocoding" in registry.capability_index
    assert "send_message" in registry.capability_index


# =========================================
# REGISTRATION
# =========================================


def test_register_server(empty_registry):
    config = MCPServerConfig(
        name="Test Server",
        url="http://test.com",
        capabilities=["test_cap"],
    )
    entry = empty_registry.register_server(config)
    assert entry.config.name == "Test Server"
    assert entry.health == "unknown"
    assert "test_cap" in empty_registry.capability_index


def test_register_auto_id(empty_registry):
    config = MCPServerConfig(name="Auto ID", url="http://auto.com")
    entry = empty_registry.register_server(config)
    assert entry.config.server_id.startswith("mcp_")


def test_unregister_server(empty_registry):
    config = MCPServerConfig(
        server_id="temp",
        name="Temp",
        url="http://temp.com",
        capabilities=["temp_cap"],
    )
    empty_registry.register_server(config)
    assert empty_registry.unregister_server("temp") is True
    assert empty_registry.get_server("temp") is None
    assert "temp" not in empty_registry.capability_index.get("temp_cap", [])


def test_unregister_nonexistent(empty_registry):
    assert empty_registry.unregister_server("nonexistent") is False


# =========================================
# DISCOVERY
# =========================================


def test_discover_tools(registry):
    tools = registry.discover_tools("mcp_notion")
    assert len(tools) >= 3
    assert all(isinstance(t, MCPTool) for t in tools)


def test_discover_nonexistent(registry):
    tools = registry.discover_tools("nonexistent")
    assert tools == []


def test_get_all_tools(registry):
    tools = registry.get_all_tools()
    server_ids = {t.server_id for t in tools}
    assert "mcp_notion" in server_ids
    assert "mcp_google_maps" in server_ids


# =========================================
# ROUTING
# =========================================


def test_route_email(registry):
    result = registry.route_request("send email to Craig Lindahl")
    assert result.selected_server == "mcp_google_workspace"
    assert result.confidence > 0


def test_route_slack(registry):
    result = registry.route_request("post update in slack channel")
    assert result.selected_server == "mcp_slack"
    assert result.confidence > 0


def test_route_map(registry):
    result = registry.route_request("find distance from Norfolk to Langley AFB")
    assert result.selected_server == "mcp_google_maps"
    assert result.confidence > 0


def test_route_contact_enrich(registry):
    result = registry.route_request("enrich contact data for John Smith")
    assert result.selected_server in ("mcp_day_ai", "mcp_notion")
    assert result.confidence > 0


def test_route_no_match(registry):
    result = registry.route_request("do something completely unknown xyz123")
    assert result.confidence == 0.0


def test_route_has_fallbacks(registry):
    result = registry.route_request("send email to the team")
    assert isinstance(result.fallback_servers, list)


def test_route_matched_servers(registry):
    result = registry.route_request("send email to Craig")
    assert len(result.matched_servers) >= 1
    assert all("server_id" in s for s in result.matched_servers)


# =========================================
# HEALTH
# =========================================


def test_health_check(registry):
    status = registry.health_check("mcp_notion", healthy=True, latency_ms=50)
    assert status == "healthy"
    entry = registry.get_server("mcp_notion")
    assert entry.last_health_check != ""


def test_health_check_degraded(registry):
    # Alternate healthy/unhealthy for degraded status
    registry.health_check("mcp_notion", healthy=True)
    registry.health_check("mcp_notion", healthy=False)
    registry.health_check("mcp_notion", healthy=True)
    registry.health_check("mcp_notion", healthy=False)
    status = registry.health_check("mcp_notion", healthy=True)
    # 3 healthy, 2 unhealthy = degraded or healthy (>50%)
    assert status in ("healthy", "degraded")


def test_health_check_unhealthy(registry):
    for _ in range(5):
        registry.health_check("mcp_notion", healthy=False)
    status = registry.health_check("mcp_notion", healthy=False)
    assert status == "unhealthy"


def test_health_check_all(registry):
    statuses = registry.health_check_all()
    assert len(statuses) >= 9
    assert all(
        v in ("healthy", "degraded", "unhealthy", "unknown") for v in statuses.values()
    )


def test_health_check_nonexistent(registry):
    status = registry.health_check("nonexistent")
    assert status == "unknown"


# =========================================
# USAGE TRACKING
# =========================================


def test_record_usage(registry):
    registry.record_usage("mcp_notion", "query_database", success=True, latency_ms=100)
    entry = registry.get_server("mcp_notion")
    assert entry.total_calls == 1
    assert entry.last_used != ""


def test_record_usage_error(registry):
    registry.record_usage("mcp_notion", "query_database", success=False, latency_ms=500)
    entry = registry.get_server("mcp_notion")
    assert entry.total_errors == 1
    assert entry.error_rate > 0


def test_usage_tracker(registry):
    registry.record_usage("mcp_notion", "query_database", success=True, latency_ms=100)
    registry.record_usage("mcp_notion", "read_page", success=True, latency_ms=200)
    usage = registry.usage_tracker.get_usage(server_id="mcp_notion")
    assert usage["total_calls"] == 2
    assert usage["avg_latency_ms"] == 150.0


# =========================================
# LIST & FILTER
# =========================================


def test_list_by_capability(registry):
    servers = registry.list_servers(capability="geocoding")
    assert len(servers) >= 1
    assert any(s.config.server_id == "mcp_google_maps" for s in servers)


def test_list_healthy_only(registry):
    registry.health_check_all()
    servers = registry.list_servers(healthy_only=True)
    assert all(s.health == "healthy" for s in servers)


# =========================================
# STATS
# =========================================


def test_stats(registry):
    stats = registry.get_stats()
    assert stats["total_servers"] >= 9
    assert stats["total_tools"] >= 20
    assert stats["total_capabilities"] >= 5
    assert "by_health" in stats
    assert "by_transport" in stats
    assert "by_cost_tier" in stats


# =========================================
# HEALTH MONITOR
# =========================================


def test_health_monitor_history():
    monitor = HealthMonitor()
    monitor.record_check("s1", True, 50)
    monitor.record_check("s1", True, 60)
    history = monitor.get_history("s1")
    assert len(history) == 2


def test_health_monitor_limit():
    monitor = HealthMonitor()
    for i in range(15):
        monitor.record_check("s1", True, 50)
    assert len(monitor.get_history("s1")) == 10  # capped at 10


# =========================================
# USAGE TRACKER
# =========================================


def test_usage_tracker_empty():
    tracker = UsageTracker()
    usage = tracker.get_usage()
    assert usage["total_calls"] == 0


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    r1 = get_tool_registry()
    r2 = get_tool_registry()
    assert r1 is r2
