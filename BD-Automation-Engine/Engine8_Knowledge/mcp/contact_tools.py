"""
Phase 26A — MCP Contact Tools

5 contact-focused tools for Claude Desktop integration.
"""

from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


def register_contact_tools(mcp, hub) -> int:
    """Register 5 contact tools with the MCP server. Returns count registered."""
    count = 0

    @mcp.tool()
    async def search_contacts(
        query: str,
        program: str = None,
        tier: str = None,
        location: str = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search DCGS contacts by name, program, tier, or location."""
        params = {"q": query, "limit": limit}
        if program:
            params["program"] = program
        if tier:
            params["tier"] = tier
        if location:
            params["location"] = location
        data = await hub.get("/api/v2/contacts", params=params)
        return data.get("contacts", [])[:limit]

    count += 1

    @mcp.tool()
    async def get_contact_360(contact_name: str) -> Dict[str, Any]:
        """Full 360 profile: bio, tier, program, interactions, memories, org position."""
        # Search for the contact
        data = await hub.get("/api/v2/contacts", params={"q": contact_name, "limit": 1})
        contacts = data.get("contacts", [])
        if not contacts:
            return {"error": f"Contact not found: {contact_name}"}

        contact = contacts[0]
        # Enrich with memory
        memory = await hub.get(f"/memory/contact/{contact_name}")
        # Enrich with graph position
        graph = await hub.get(f"/bdgraph/contact/{contact_name}")

        return {
            "contact": contact,
            "memory": memory,
            "graph_position": graph,
        }

    count += 1

    @mcp.tool()
    async def classify_contact(
        name: str, title: str, location: str = ""
    ) -> Dict[str, Any]:
        """Classify a new contact: tier, program, BD priority, location hub, functional area."""
        data = await hub.post("/api/v2/contacts/classify", json={
            "name": name,
            "title": title,
            "location": location,
        })
        if not data:
            # Fallback basic classification
            tier = 5
            title_lower = title.lower()
            if any(kw in title_lower for kw in ["ceo", "cto", "cio", "president", "vp"]):
                tier = 1
            elif any(kw in title_lower for kw in ["director", "svp"]):
                tier = 2
            elif any(kw in title_lower for kw in ["manager", "lead"]):
                tier = 3
            elif any(kw in title_lower for kw in ["senior", "sr."]):
                tier = 4
            return {
                "name": name,
                "title": title,
                "location": location,
                "tier": tier,
                "classification": "auto",
            }
        return data

    count += 1

    @mcp.tool()
    async def find_introduction_path(
        from_contact: str, to_contact: str
    ) -> Dict[str, Any]:
        """Find the shortest warm introduction path between two contacts using Neo4j."""
        data = await hub.get(
            f"/bdgraph/introduction-path/{from_contact}/{to_contact}"
        )
        if not data:
            data = await hub.get(f"/bdgraph/teaming/{from_contact}/{to_contact}")
        return data or {"from": from_contact, "to": to_contact, "path": [], "hops": -1}

    count += 1

    @mcp.tool()
    async def get_org_chart(
        program: str, format: str = "text"
    ) -> Dict[str, Any]:
        """Get org chart for a program. format: text (ASCII tree), json, or mermaid."""
        data = await hub.post("/org-chart/generate", json={
            "program": program,
            "mode": "tree",
        })
        if not data:
            return {"program": program, "format": format, "chart": "No org chart data available"}

        if format == "mermaid":
            # Convert to mermaid
            nodes = data.get("nodes", [])
            lines = ["graph TD"]
            for node in nodes[:20]:
                name = node.get("name", "Unknown")
                title = node.get("title", "")
                parent = node.get("reports_to", "")
                safe_name = name.replace(" ", "_")
                lines.append(f'    {safe_name}["{name}<br/>{title}"]')
                if parent:
                    safe_parent = parent.replace(" ", "_")
                    lines.append(f"    {safe_parent} --> {safe_name}")
            data["mermaid"] = "\n".join(lines)

        data["format"] = format
        return data

    count += 1

    logger.info("contact_tools_registered", count=count)
    return count
