"""
FastMCP 2.0 Python server for BD Intelligence Hub.

Provides 21 tools for search, graph, memory, ingestion, and file intelligence.
Wraps the existing FastAPI server at http://localhost:8100.

Usage:
    # As MCP server (stdio transport)
    python server.py

    # Or add to .mcp.json:
    {
        "mcpServers": {
            "bd-knowledge-python": {
                "command": "python",
                "args": ["mcp/knowledge-mcp-server/server.py"]
            }
        }
    }

Install:
    pip install fastmcp httpx
"""

import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    logger.error("fastmcp not installed. Install with: pip install fastmcp")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


API_URL = os.environ.get("KNOWLEDGE_API_URL", "http://127.0.0.1:8100")

mcp = FastMCP(
    "bd-intelligence-hub",
    version="3.0.0",
    description="BD Intelligence Hub — search, graph, memory, and file intelligence for federal defense BD",
)

# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

async def _api(method: str, endpoint: str, json_body: dict = None, params: dict = None) -> dict:
    """Call the FastAPI backend."""
    async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
        if method == "GET":
            resp = await client.get(endpoint, params=params)
        elif method == "POST":
            resp = await client.post(endpoint, json=json_body, params=params)
        elif method == "DELETE":
            resp = await client.delete(endpoint, params=params)
        else:
            raise ValueError(f"Unsupported method: {method}")
        resp.raise_for_status()
        return resp.json()


# ===========================================================================
# SEARCH TOOLS
# ===========================================================================

@mcp.tool()
async def search_knowledge(
    query: str,
    collection: str = "all",
    limit: int = 10,
) -> str:
    """Search the BD knowledge base across jobs, contacts, programs, documents, activities.

    Args:
        query: Natural language search query
        collection: Collection to search (jobs, contacts, programs, documents, activities, or all)
        limit: Maximum results (1-50)
    """
    result = await _api("POST", "/search", json_body={
        "query": query,
        "collection": collection if collection != "all" else None,
        "limit": min(limit, 50),
    })
    return _format_search(result)


@mcp.tool()
async def semantic_search(query: str, collection: str = "bd_knowledge", limit: int = 10) -> str:
    """Deep semantic similarity search across 1.42M vectors.

    Args:
        query: Semantic search query
        collection: Vector collection to search
        limit: Maximum results
    """
    result = await _api("GET", "/search/semantic", params={
        "q": query, "collection": collection, "limit": limit,
    })
    return _format_search(result)


@mcp.tool()
async def hybrid_search(query: str, collection: str = "bd_knowledge", limit: int = 10) -> str:
    """Combined BM25 keyword + semantic vector search with reranking.

    Args:
        query: Search query (works with both keywords and natural language)
        collection: Collection to search
        limit: Maximum results
    """
    result = await _api("GET", "/search/hybrid", params={
        "q": query, "collection": collection, "limit": limit, "use_rerank": "true",
    })
    return _format_search(result)


@mcp.tool()
async def smart_ask(query: str) -> str:
    """Intelligent query that auto-routes to the optimal search system(s).
    Use this for any BD question — it picks the best approach automatically.

    Args:
        query: Your BD question in natural language
    """
    result = await _api("GET", "/ask/smart", params={"q": query})
    return _format_dict(result)


# ===========================================================================
# FILE & DEPENDENCY TOOLS
# ===========================================================================

@mcp.tool()
async def search_files(query: str, category: str = None, limit: int = 10) -> str:
    """Search across all indexed files using hybrid search.

    Args:
        query: Search query for file content or metadata
        category: Optional filter (source_code, configuration, documentation, data_file, test_file)
        limit: Maximum results
    """
    params = {"q": query, "limit": limit}
    if category:
        params["category"] = category
    result = await _api("GET", "/search/semantic", params={
        "q": query, "collection": "documents", "limit": limit,
    })
    return _format_search(result)


@mcp.tool()
async def get_file_info(path: str) -> str:
    """Get metadata and relationships for a specific file.

    Args:
        path: File path (relative to project root)
    """
    try:
        result = await _api("GET", f"/neo4j/file/{path}")
        return _format_dict(result)
    except Exception:
        return f"File info not found for: {path}. Neo4j lineage may not be populated yet."


@mcp.tool()
async def find_dependencies(path: str, direction: str = "both") -> str:
    """Find all files that depend on or are depended on by this file.

    Args:
        path: File path to trace dependencies for
        direction: 'upstream' (what this file depends on), 'downstream' (what depends on this), or 'both'
    """
    try:
        result = await _api("GET", f"/neo4j/file/{path}/dependencies", params={"direction": direction})
        return _format_dict(result)
    except Exception:
        return f"No dependency data for: {path}. Run lineage indexing first."


# ===========================================================================
# GRAPH TOOLS
# ===========================================================================

@mcp.tool()
async def query_knowledge_graph(query: str, mode: str = "hybrid") -> str:
    """Query entity relationships and networks in the knowledge graph.

    Args:
        query: Natural language graph query
        mode: Search mode — local (neighborhood), global (full graph), or hybrid
    """
    result = await _api("GET", "/graph/query", params={"q": query, "mode": mode})
    return _format_dict(result)


@mcp.tool()
async def find_relationships(entity: str) -> str:
    """Find all relationships for a company, program, or contact.

    Args:
        entity: Entity name (e.g., "Leidos", "DCGS", "John Smith")
    """
    result = await _api("GET", "/graph/relationships", params={"entity": entity})
    return _format_dict(result)


# ===========================================================================
# SPECIALIZED BD TOOLS
# ===========================================================================

@mcp.tool()
async def get_program_intel(program_name: str) -> str:
    """Get comprehensive intelligence about a federal program.
    Returns prime contractors, key contacts, contract details, job activity, and BD insights.

    Args:
        program_name: Program name or acronym (e.g., "DCGS", "GBSD", "AEGIS")
    """
    result = await _api("GET", f"/program/{program_name}")
    return _format_dict(result)


@mcp.tool()
async def get_company_contacts(company_name: str, tier: int = None, limit: int = 20) -> str:
    """Find contacts at a specific company, optionally filtered by tier.

    Args:
        company_name: Company name (e.g., "Leidos", "Northrop Grumman", "GDIT")
        tier: Optional tier filter (1=Executive, 2=Director, 3=Program Lead, 4=Manager, 5=Senior IC, 6=IC)
        limit: Maximum contacts to return
    """
    params = {"limit": limit}
    if tier:
        params["tier"] = tier
    result = await _api("GET", f"/contacts/at/{company_name}", params=params)
    return _format_dict(result)


# ===========================================================================
# MEMORY TOOLS
# ===========================================================================

@mcp.tool()
async def memory_add(content: str, memory_type: str = "interaction") -> str:
    """Add information to BD memory for future reference.

    Args:
        content: Information to remember
        memory_type: Type of memory (interaction, fact, insight, observation)
    """
    result = await _api("POST", "/memory/add", json_body={
        "content": content,
        "metadata": {"memory_type": memory_type},
    })
    return _format_dict(result)


@mcp.tool()
async def memory_search(query: str, limit: int = 10) -> str:
    """Search past memories and interactions.

    Args:
        query: Search query
        limit: Maximum results
    """
    result = await _api("GET", "/memory/search", params={"q": query, "limit": limit})
    return _format_dict(result)


@mcp.tool()
async def memory_add_insight(
    insight_type: str,
    insight: str,
    source: str = "user",
    confidence: float = 0.8,
) -> str:
    """Add a BD insight (opportunity, risk, relationship, or strategy).

    Args:
        insight_type: Type — opportunity, risk, relationship, or strategy
        insight: The insight content
        source: Source of the insight
        confidence: Confidence level (0-1)
    """
    result = await _api("POST", "/memory/insight", json_body={
        "insight_type": insight_type,
        "insight": insight,
        "source": source,
        "confidence": confidence,
    })
    return _format_dict(result)


# ===========================================================================
# INGEST TOOLS
# ===========================================================================

@mcp.tool()
async def ingest_document(text: str, title: str = None, doc_type: str = "general") -> str:
    """Index a document into the knowledge base.

    Args:
        text: Document text content
        title: Optional document title
        doc_type: Document type (general, briefing, past_performance, proposal)
    """
    result = await _api("POST", "/ingest/document", json_body={
        "text": text,
        "metadata": {"title": title, "doc_type": doc_type},
    })
    return _format_dict(result)


@mcp.tool()
async def ingest_program(
    name: str,
    description: str = None,
    agency: str = None,
    primes: List[str] = None,
    value: str = None,
    clearance: str = None,
) -> str:
    """Add a federal program to the knowledge base.

    Args:
        name: Program name
        description: Program description
        agency: Owning agency
        primes: List of prime contractor names
        value: Contract value
        clearance: Required clearance level
    """
    body = {"name": name}
    if description:
        body["description"] = description
    if agency:
        body["agency"] = agency
    if primes:
        body["primes"] = primes
    if value:
        body["value"] = value
    if clearance:
        body["clearance"] = clearance
    result = await _api("POST", "/ingest/program", json_body=body)
    return _format_dict(result)


# ===========================================================================
# SYSTEM TOOLS
# ===========================================================================

@mcp.tool()
async def get_system_stats() -> str:
    """Get BD Intelligence Hub system statistics.
    Returns collection sizes, vector counts, API health, and cache status.
    """
    result = await _api("GET", "/stats")
    return _format_dict(result)


# ===========================================================================
# Formatting helpers
# ===========================================================================

def _format_search(result: dict) -> str:
    """Format search results for readability."""
    lines = []
    count = result.get("count", result.get("total", 0))
    query = result.get("query", "")
    lines.append(f"Found {count} results for: {query}\n")

    results = result.get("results", [])
    for i, r in enumerate(results, 1):
        score = r.get("score", 0)
        payload = r.get("payload", r)
        title = payload.get("title", payload.get("name", payload.get("full_name", "Untitled")))
        lines.append(f"{i}. [{score:.3f}] {title}")
        # Add key fields
        for key in ("company", "program", "location", "clearance", "tier", "status"):
            if key in payload and payload[key]:
                lines.append(f"   {key}: {payload[key]}")

    return "\n".join(lines)


def _format_dict(result: dict) -> str:
    """Format dict result for readability."""
    import json
    return json.dumps(result, indent=2, default=str)


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    if not FASTMCP_AVAILABLE:
        print("ERROR: fastmcp not installed. Install with: pip install fastmcp")
        exit(1)
    mcp.run()
