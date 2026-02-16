"""Infrastructure metadata merger.

Consolidates database, API, workflow, and tooling metadata across
3 repository architecture JSONs.
"""


def _merge_list_by_key(items: list[dict], key: str) -> list[dict]:
    """Deduplicate a list of dicts by a key field, merging 'projects' lists."""
    by_key = {}
    for item in items:
        k = item.get(key, "")
        if k in by_key:
            for p in item.get("projects", []):
                if p not in by_key[k].get("projects", []):
                    by_key[k].setdefault("projects", []).append(p)
        else:
            by_key[k] = dict(item)
    return list(by_key.values())


def _get(data: dict, key: str, default=None):
    """Get a key from data, checking both top-level and nested 'databases' dict."""
    val = data.get(key)
    if val is not None:
        return val
    dbs = data.get("databases", {})
    if isinstance(dbs, dict):
        val = dbs.get(key)
        if val is not None:
            return val
    return default if default is not None else []


def _tag_items(items: list, project_id: str) -> list[dict]:
    """Tag each item (dict or string) with its source project."""
    tagged = []
    for item in items:
        if isinstance(item, dict):
            item = dict(item)
            item.setdefault("projects", [])
            if project_id not in item["projects"]:
                item["projects"].append(project_id)
            tagged.append(item)
        elif isinstance(item, str):
            tagged.append({"name": item, "projects": [project_id]})
        else:
            tagged.append(item)
    return tagged


def merge_qdrant_collections(*project_datasets: tuple[str, dict]) -> list[dict]:
    """Merge Qdrant collection metadata. BD: 9, DS: 2, N8N: 3."""
    all_collections = []
    for project_id, data in project_datasets:
        collections = _get(data, "qdrant_collections", [])
        all_collections.extend(_tag_items(collections, project_id))
    return _merge_list_by_key(all_collections, "name")


def merge_sqlite_databases(*project_datasets: tuple[str, dict]) -> list[dict]:
    """Merge SQLite database metadata. BD: 6, DS: 1, N8N: 12."""
    all_dbs = []
    for project_id, data in project_datasets:
        dbs = _get(data, "sqlite_databases", [])
        # Also check sqlite_tables (data-scraper uses this key)
        if not dbs:
            dbs = _get(data, "sqlite_tables", [])
        all_dbs.extend(_tag_items(dbs, project_id))
    return _merge_list_by_key(all_dbs, "name")


def merge_neo4j_graph(*project_datasets: tuple[str, dict]) -> dict:
    """Merge Neo4j graph schemas. BD: 9 nodes + 26 rels, N8N: 6 + 10."""
    node_types = {}
    rel_types = {}

    for project_id, data in project_datasets:
        neo4j_data = _get(data, "neo4j_graph", {})
        if not isinstance(neo4j_data, dict):
            neo4j_data = {}

        for nt in neo4j_data.get("node_types", _get(data, "neo4j_node_types", [])):
            name = (
                nt
                if isinstance(nt, str)
                else (nt.get("name", "") or nt.get("type", ""))
            )
            if name:
                node_types.setdefault(name, {"name": name, "projects": []})
                if project_id not in node_types[name]["projects"]:
                    node_types[name]["projects"].append(project_id)

        for rt in neo4j_data.get(
            "relationship_types", _get(data, "neo4j_relationship_types", [])
        ):
            name = rt if isinstance(rt, str) else rt.get("name", "")
            if name:
                rel_types.setdefault(name, {"name": name, "projects": []})
                if project_id not in rel_types[name]["projects"]:
                    rel_types[name]["projects"].append(project_id)

    return {
        "node_types": list(node_types.values()),
        "relationship_types": list(rel_types.values()),
        "total_node_types": len(node_types),
        "total_relationship_types": len(rel_types),
    }


def merge_api_endpoints(*project_datasets: tuple[str, dict]) -> dict:
    """Aggregate API endpoint counts. BD: 340, DS: 250, N8N: 267."""
    per_project = {}
    total = 0

    for project_id, data in project_datasets:
        stats = data.get("scan_stats", {})
        count = stats.get("api_endpoints_documented", 0)
        routers = stats.get("src_api_routers", 0) or stats.get(
            "api_routers_documented", 0
        )
        per_project[project_id] = {
            "endpoints": count,
            "routers": routers,
        }
        total += count

        # Preserve detailed router list if available
        api_routers = data.get("api_routers", [])
        if api_routers:
            per_project[project_id]["router_details"] = api_routers

    return {
        "total_endpoints": total,
        "per_project": per_project,
    }


def merge_data_flows(*project_datasets: tuple[str, dict]) -> list[dict]:
    """Merge data flow definitions. BD: 18, DS: 7, N8N: 14."""
    all_flows = []
    for project_id, data in project_datasets:
        flows = data.get("data_flows", [])
        all_flows.extend(_tag_items(flows, project_id))
    return all_flows


def merge_notion_databases(*project_datasets: tuple[str, dict]) -> list[dict]:
    """Merge Notion database references."""
    all_dbs = []
    for project_id, data in project_datasets:
        dbs = _get(data, "notion_databases", [])
        all_dbs.extend(_tag_items(dbs, project_id))
    return _merge_list_by_key(all_dbs, "name")


def build_infrastructure_section(
    *project_datasets: tuple[str, dict],
) -> dict:
    """Combine all infrastructure metadata into a unified section."""
    result = {
        "qdrant_collections": merge_qdrant_collections(*project_datasets),
        "sqlite_databases": merge_sqlite_databases(*project_datasets),
        "neo4j_graph": merge_neo4j_graph(*project_datasets),
        "notion_databases": merge_notion_databases(*project_datasets),
        "api_endpoints": merge_api_endpoints(*project_datasets),
        "data_flows": merge_data_flows(*project_datasets),
    }

    # Collect project-specific metadata that doesn't need merging
    for project_id, data in project_datasets:
        # Engines (BD-Engine only)
        engines = _get(data, "engines")
        if engines:
            result["engines"] = engines

        # Modules (N8N-Builder)
        modules = _get(data, "modules")
        if modules:
            result["modules"] = modules

        # Capability domains (data-scraper)
        cap_domains = _get(data, "capability_domains")
        if cap_domains:
            result["capability_domains"] = cap_domains

        # MCP servers/agents (N8N-Builder)
        mcp_servers = _get(data, "mcp_servers")
        if mcp_servers:
            result["mcp_servers"] = mcp_servers
        mcp_agents = _get(data, "mcp_agents")
        if mcp_agents:
            result["mcp_agents"] = mcp_agents

        # MCP tools (BD-Engine)
        mcp_tools = _get(data, "mcp_tools")
        if mcp_tools:
            result["mcp_tools"] = mcp_tools

        # Dify tools (BD-Engine)
        dify_tools = _get(data, "dify_tools")
        if dify_tools:
            result["dify_tools"] = dify_tools

        # AI agents/crews (BD-Engine)
        ai_agents = _get(data, "ai_agents")
        if ai_agents:
            result["ai_agents"] = ai_agents
        ai_crews = _get(data, "ai_crews")
        if ai_crews:
            result["ai_crews"] = ai_crews

        # N8N workflows
        n8n_wf = _get(data, "n8n_workflows")
        if n8n_wf:
            result["n8n_workflows"] = n8n_wf

        # Streaming schemas
        streaming = _get(data, "streaming_schemas")
        if streaming:
            result["streaming_schemas"] = streaming

        # CSV sources
        csv = _get(data, "csv_sources") or _get(data, "csv_files")
        if csv:
            result.setdefault("csv_sources", [])
            result["csv_sources"].extend(_tag_items(csv, project_id))

        # Tango SQL tables (data-scraper)
        tango = _get(data, "tango_sql_tables")
        if tango:
            result["tango_sql_tables"] = tango

        # External APIs
        ext_apis = _get(data, "external_apis")
        if ext_apis:
            result.setdefault("external_apis", [])
            result["external_apis"].extend(_tag_items(ext_apis, project_id))

        # External repos (N8N-Builder)
        ext_repos = _get(data, "external_repos")
        if ext_repos:
            result["external_repos"] = ext_repos

    return result
