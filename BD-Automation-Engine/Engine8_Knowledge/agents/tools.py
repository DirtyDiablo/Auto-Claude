"""
CrewAI Tools for BD Intelligence Agents.

6 Qdrant vector search tools (using text-embedding-3-small 1536-dim)
+ 2 custom tools for Mem0 and Graphiti.
"""

import os
import logging
from openai import OpenAI
from crewai import tool
from crewai_tools import QdrantVectorSearchTool
from crewai_tools.tools.qdrant_search_tool import QdrantConfig

logger = logging.getLogger("BD-AgentTools")

# OpenAI client for embeddings
oai = OpenAI()


def embed_1536(text: str) -> list[float]:
    """Embed text using text-embedding-3-small (1536 dims) to match existing collections."""
    return oai.embeddings.create(
        input=text, model="text-embedding-3-small"
    ).data[0].embedding


def qdrant_cfg(collection: str, limit: int = 10) -> QdrantConfig:
    return QdrantConfig(
        qdrant_url="http://localhost:6333",
        collection_name=collection,
        limit=limit,
        score_threshold=0.35,
    )


# =========================================
# 6 Qdrant Search Tools
# =========================================

qdrant_contacts_tool = QdrantVectorSearchTool(
    qdrant_config=qdrant_cfg("contacts"),
    custom_embedding_fn=embed_1536,
    description="Search BD contacts by name, title, company, program, or location",
)

qdrant_programs_tool = QdrantVectorSearchTool(
    qdrant_config=qdrant_cfg("programs"),
    custom_embedding_fn=embed_1536,
    description="Search federal programs by name, agency, prime contractor, or contract value",
)

qdrant_documents_tool = QdrantVectorSearchTool(
    qdrant_config=qdrant_cfg("documents"),
    custom_embedding_fn=embed_1536,
    description="Search federal contract documents, SOWs, and RFPs",
)

qdrant_jobs_tool = QdrantVectorSearchTool(
    qdrant_config=qdrant_cfg("jobs"),
    custom_embedding_fn=embed_1536,
    description="Search scraped job postings by title, company, location, clearance",
)

qdrant_notes_tool = QdrantVectorSearchTool(
    qdrant_config=qdrant_cfg("bullhorn_notes"),
    custom_embedding_fn=embed_1536,
    description="Search CRM notes and HUMINT intelligence from field contacts",
)

qdrant_contracts_tool = QdrantVectorSearchTool(
    qdrant_config=qdrant_cfg("federal_contracts"),
    custom_embedding_fn=embed_1536,
    description="Search USASpending federal contract awards by agency, contractor, NAICS",
)


# =========================================
# Custom Tools
# =========================================

@tool("Search Contact Memory")
def mem0_search_tool(query: str, contact_name: str = "") -> str:
    """Search Mem0 for contact interaction history, HUMINT notes, and pain points."""
    try:
        from Engine8_Knowledge.scripts.memory_layer import get_memory
        mem = get_memory()
        if mem.backend == "mem0":
            results = mem.memory.search(query, user_id="bd_team", limit=10)
            memories = results.get("results", []) if isinstance(results, dict) else results
            return "\n".join([r.get("memory", str(r)) for r in memories]) or "No memories found."
        else:
            results = mem.get_context(query, limit=10)
            return "\n".join([r.get("memory", str(r)) for r in results]) or "No memories found."
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
                results = pool.submit(asyncio.run, search_graph(query, limit=10)).result()
        else:
            results = asyncio.run(search_graph(query, limit=10))
        return "\n".join([r.get("fact", str(r)) for r in results]) or "No graph results found."
    except Exception as e:
        logger.error("graphiti_search_tool error: %s", e)
        return f"Graph search error: {e}"
