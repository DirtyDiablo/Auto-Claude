"""
Phase 26A — MCP Memory & Intelligence Tools

5 memory/intelligence tools for Claude Desktop integration.
"""

from typing import Any, Dict, List

import structlog

logger = structlog.get_logger(__name__)


def register_memory_tools(mcp, hub) -> int:
    """Register 5 memory/intel tools with the MCP server."""
    count = 0

    @mcp.tool()
    async def recall_memory(
        query: str, contact_id: str = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search agent memories. Optionally scope to a specific contact."""
        body = {"query": query, "limit": limit}
        if contact_id:
            body["user_id"] = contact_id
        data = await hub.post("/memory/search", json=body)
        results = data.get("results", {})
        all_memories = []
        if isinstance(results, dict):
            for layer_results in results.values():
                if isinstance(layer_results, list):
                    all_memories.extend(layer_results)
        return all_memories[:limit]

    count += 1

    @mcp.tool()
    async def add_memory(
        content: str,
        memory_type: str = "insight",
        contact_id: str = None,
    ) -> Dict[str, Any]:
        """Add a memory. Types: interaction, insight, preference, outcome."""
        body = {
            "content": content,
            "layer": None,
            "tags": [memory_type],
            "metadata": {"type": memory_type},
        }
        if contact_id:
            body["contact_id"] = contact_id
            body["user_id"] = contact_id
        data = await hub.post("/memory/add", json=body)
        return data or {"memory_id": None, "error": "Failed to add memory"}

    count += 1

    @mcp.tool()
    async def search_knowledge_base(
        query: str, tags: List[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search institutional knowledge base."""
        data = await hub.post(
            "/search",
            json={
                "query": query,
                "collection": "documents",
                "limit": limit,
            },
        )
        results = data.get("results", [])
        if tags and isinstance(results, list):
            results = [
                r
                for r in results
                if any(
                    tag.lower() in str(r.get("metadata", {})).lower() for tag in tags
                )
            ]
        return results[:limit]

    count += 1

    @mcp.tool()
    async def get_interaction_history(
        contact_name: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent interaction history with a contact."""
        data = await hub.get(f"/memory/contact/{contact_name}")
        interactions = data.get("interactions", [])
        return interactions[:limit]

    count += 1

    @mcp.tool()
    async def generate_outreach(
        contact_name: str, channel: str = "email"
    ) -> Dict[str, Any]:
        """Generate personalized outreach following the PTS BD Formula."""
        # Gather contact intel
        contact_data = await hub.get(
            "/api/v2/contacts", params={"q": contact_name, "limit": 1}
        )
        contacts = contact_data.get("contacts", [])
        memory = await hub.get(f"/memory/contact/{contact_name}")

        contact = contacts[0] if contacts else {"name": contact_name}
        name = contact.get("name", contact_name)
        contact.get("title", "")
        company = contact.get("company", "")
        program = contact.get("program", "")

        # Generate template
        if channel == "email":
            message = {
                "channel": "email",
                "subject": f"PTS Support for {program or company} Staffing Needs",
                "body": (
                    f"Hi {name.split()[0] if name else 'there'},\n\n"
                    f"I noticed {company}'s work on {program or 'federal programs'} and "
                    f"wanted to connect regarding cleared staffing support.\n\n"
                    f"PTS has deep expertise in defense/intel staffing and currently "
                    f"supports several programs in this space. Would you have 15 minutes "
                    f"this week to discuss how we might help?\n\n"
                    f"Best regards"
                ),
                "contact": contact,
                "memory_context": memory.get("interactions", [])[:3],
            }
        elif channel == "linkedin":
            message = {
                "channel": "linkedin",
                "body": (
                    f"Hi {name.split()[0] if name else 'there'}, "
                    f"I see you're working on {program or 'defense programs'} at {company}. "
                    f"PTS supports similar programs — would love to connect."
                ),
                "contact": contact,
            }
        else:
            message = {
                "channel": channel,
                "body": f"Outreach to {name} via {channel}",
                "contact": contact,
            }

        return message

    count += 1

    logger.info("memory_tools_registered", count=count)
    return count
