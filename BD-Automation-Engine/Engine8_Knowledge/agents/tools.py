"""
CrewAI Tools for BD Intelligence Agents.

6 Qdrant vector search tools (using text-embedding-3-small 1536-dim)
+ 2 custom tools for Mem0 and Graphiti.

Uses @tool decorator for clean schemas compatible with GPT-4o function calling.
"""

import logging
from openai import OpenAI
from qdrant_client import QdrantClient
from crewai.tools import tool

logger = logging.getLogger("BD-AgentTools")

# Shared clients
_oai = OpenAI()
_qdrant = QdrantClient(url="http://localhost:6333")

EMBEDDING_MODEL = "text-embedding-3-small"
SCORE_THRESHOLD = 0.35
DEFAULT_LIMIT = 10


def _search_qdrant(query: str, collection: str, limit: int = DEFAULT_LIMIT) -> str:
    """Embed query and search a Qdrant collection, returning formatted results."""
    try:
        embedding = (
            _oai.embeddings.create(input=query, model=EMBEDDING_MODEL).data[0].embedding
        )

        results = _qdrant.query_points(
            collection_name=collection,
            query=embedding,
            limit=limit,
            score_threshold=SCORE_THRESHOLD,
            with_payload=True,
        ).points

        if not results:
            return f"No results found in '{collection}' for: {query}"

        lines = []
        for i, pt in enumerate(results, 1):
            score = pt.score
            payload = pt.payload or {}
            text = payload.get("text", "")[:300]
            # Build a summary from key payload fields
            meta_parts = []
            for key in [
                "name",
                "title",
                "company",
                "program",
                "agency",
                "location",
                "source_file",
            ]:
                if key in payload and payload[key]:
                    meta_parts.append(f"{key}={payload[key]}")
            meta_str = ", ".join(meta_parts[:5])
            lines.append(f"[{i}] (score={score:.3f}) {meta_str}\n    {text}")

        return "\n\n".join(lines)
    except Exception as e:
        logger.error("Qdrant search error (%s): %s", collection, e)
        return f"Search error in {collection}: {e}"


# =========================================
# 6 Qdrant Search Tools
# =========================================


@tool("Search BD Contacts")
def qdrant_contacts_tool(query: str) -> str:
    """Search BD contacts by name, title, company, program, or location. Returns contact records with tier classification."""
    return _search_qdrant(query, "contacts")


@tool("Search Federal Programs")
def qdrant_programs_tool(query: str) -> str:
    """Search federal programs by name, agency, prime contractor, or contract value. Returns program intelligence."""
    return _search_qdrant(query, "programs")


@tool("Search Federal Documents")
def qdrant_documents_tool(query: str) -> str:
    """Search federal contract documents, SOWs, RFPs, and past performance records."""
    return _search_qdrant(query, "documents")


@tool("Search Job Postings")
def qdrant_jobs_tool(query: str) -> str:
    """Search scraped job postings by title, company, location, or clearance level. Reveals labor gaps."""
    return _search_qdrant(query, "jobs")


@tool("Search CRM Notes")
def qdrant_notes_tool(query: str) -> str:
    """Search CRM notes and HUMINT intelligence from field contacts and account managers."""
    return _search_qdrant(query, "bullhorn_notes")


@tool("Search Federal Contracts")
def qdrant_contracts_tool(query: str) -> str:
    """Search USASpending federal contract awards by agency, contractor, or NAICS code."""
    return _search_qdrant(query, "federal_contracts")


# =========================================
# Custom Tools
# =========================================


@tool("Search Contact Memory")
def mem0_search_tool(query: str) -> str:
    """Search Mem0 for contact interaction history, HUMINT notes, and pain points."""
    try:
        from Engine8_Knowledge.scripts.memory_layer import get_memory

        mem = get_memory()
        if mem.backend == "mem0":
            results = mem.memory.search(query, user_id="bd_team", limit=10)
            memories = (
                results.get("results", []) if isinstance(results, dict) else results
            )
            return (
                "\n".join([r.get("memory", str(r)) for r in memories])
                or "No memories found."
            )
        else:
            results = mem.get_context(query, limit=10)
            return (
                "\n".join([r.get("memory", str(r)) for r in results])
                or "No memories found."
            )
    except Exception as e:
        logger.error("mem0_search_tool error: %s", e)
        return f"Memory search error: {e}"


@tool("Search Temporal Graph")
def graphiti_search_tool(query: str) -> str:
    """Search Graphiti temporal knowledge graph for relationship history, role changes, and contract timelines."""
    try:
        import asyncio
        from services.graphiti_service import search_graph

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                results = pool.submit(
                    asyncio.run, search_graph(query, limit=10)
                ).result()
        else:
            results = asyncio.run(search_graph(query, limit=10))
        return (
            "\n".join([r.get("fact", str(r)) for r in results])
            or "No graph results found."
        )
    except Exception as e:
        logger.error("graphiti_search_tool error: %s", e)
        return f"Graph search error: {e}"
