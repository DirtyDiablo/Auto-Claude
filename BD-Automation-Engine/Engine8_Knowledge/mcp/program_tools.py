"""
Phase 26A — MCP Program & Search Tools

6 program/search tools for Claude Desktop integration.
"""

from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


def register_program_tools(mcp, hub) -> int:
    """Register 6 program/search tools with the MCP server."""
    count = 0

    @mcp.tool()
    async def search_programs(
        query: str,
        prime: str = None,
        min_value: float = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search federal programs by keyword, prime contractor, or minimum value."""
        params = {"q": query, "limit": limit}
        if prime:
            params["prime"] = prime
        if min_value:
            params["min_value"] = min_value
        data = await hub.get("/api/v2/programs", params=params)
        return data.get("programs", [])[:limit]

    count += 1

    @mcp.tool()
    async def get_program_intel(program_name: str) -> Dict[str, Any]:
        """Full program intelligence: value, prime/subs, contacts, jobs, pain points, HUMINT."""
        data = await hub.get(f"/bdgraph/program/{program_name}")
        enriched = data or {}

        # Add job matches
        jobs = await hub.get("/api/v2/jobs", params={"q": program_name, "limit": 10})
        enriched["matching_jobs"] = jobs.get("jobs", [])[:5]

        # Add contacts
        contacts = await hub.get("/api/v2/contacts", params={"q": program_name, "limit": 10})
        enriched["contacts"] = contacts.get("contacts", [])[:5]

        return enriched

    count += 1

    @mcp.tool()
    async def find_hiring_signals(
        program: str = None, location: str = None, days: int = 7
    ) -> List[Dict[str, Any]]:
        """Find recent hiring signals: new jobs, surges, clearance shifts."""
        params = {"limit": 20}
        if program:
            params["q"] = program
        if location:
            params["location"] = location

        data = await hub.get("/api/v2/jobs", params=params)
        jobs = data.get("jobs", [])

        signals = []
        for job in jobs:
            signals.append({
                "type": "new_job",
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "program": job.get("program", ""),
                "location": job.get("location", ""),
                "clearance": job.get("clearance", ""),
            })

        return signals[:20]

    count += 1

    @mcp.tool()
    async def get_competitive_landscape(program: str) -> Dict[str, Any]:
        """Who's competing: prime, subs, staffing vendors, recent contract activity."""
        data = await hub.get(f"/competitive/landscape", params={"program": program})
        if not data:
            # Fallback: search for program in multiple sources
            program_data = await hub.get(f"/bdgraph/program/{program}")
            jobs = await hub.get("/api/v2/jobs", params={"q": program, "limit": 20})

            companies = set()
            for job in jobs.get("jobs", []):
                if job.get("company"):
                    companies.add(job["company"])

            return {
                "program": program,
                "program_data": program_data,
                "competing_companies": list(companies),
                "job_activity": len(jobs.get("jobs", [])),
            }
        return data

    count += 1

    @mcp.tool()
    async def hybrid_search(
        query: str, search_type: str = "auto", limit: int = 10
    ) -> Dict[str, Any]:
        """Full hybrid search across all data. Types: auto, dense, bm25, graph, combined."""
        data = await hub.post("/search", json={
            "query": query,
            "mode": search_type,
            "limit": limit,
        })
        return data or {"results": [], "count": 0}

    count += 1

    @mcp.tool()
    async def graph_query(cypher: str) -> List[Dict[str, Any]]:
        """Execute a Cypher query against the Neo4j knowledge graph."""
        data = await hub.post("/neo4j/query", json={"cypher": cypher})
        return data.get("results", []) if data else []

    count += 1

    logger.info("program_tools_registered", count=count)
    return count
