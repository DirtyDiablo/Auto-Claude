"""
Graphiti Knowledge Graph Service for BD Intelligence Hub.

Provides temporal knowledge graph for BD intelligence episodes, contacts,
and program relationships using Neo4j.
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("BD-Graphiti")

try:
    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType

    GRAPHITI_AVAILABLE = True
except ImportError:
    GRAPHITI_AVAILABLE = False
    logger.warning("graphiti-core not installed")


_graphiti_instance: Optional["Graphiti"] = None


async def get_graphiti() -> Optional["Graphiti"]:
    """Get or create the Graphiti singleton (async)."""
    global _graphiti_instance
    if _graphiti_instance is not None:
        return _graphiti_instance

    if not GRAPHITI_AVAILABLE:
        return None

    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "")

    try:
        graphiti = Graphiti(neo4j_uri, "neo4j", neo4j_password)
        await graphiti.build_indices_and_constraints()
        _graphiti_instance = graphiti
        logger.info("Graphiti initialized with Neo4j at %s", neo4j_uri)
        return graphiti
    except Exception as e:
        logger.error("Graphiti init failed: %s", e)
        return None


async def add_bd_episode(
    name: str,
    body: str,
    reference_time: Optional[datetime] = None,
    source: str = "api",
) -> Dict[str, Any]:
    """Add a BD intelligence episode to the knowledge graph."""
    graphiti = await get_graphiti()
    if not graphiti:
        return {"error": "Graphiti not available"}

    ref_time = reference_time or datetime.now()

    try:
        await graphiti.add_episode(
            name=name,
            episode_body=body,
            reference_time=ref_time,
            source_description=source,
            source=EpisodeType.text,
        )
        return {
            "success": True,
            "name": name,
            "source": source,
            "reference_time": ref_time.isoformat(),
        }
    except Exception as e:
        logger.error("add_bd_episode failed: %s", e)
        return {"error": str(e)}


async def search_graph(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search the Graphiti knowledge graph."""
    graphiti = await get_graphiti()
    if not graphiti:
        return []

    try:
        results = await graphiti.search(query, num_results=limit)
        return [
            {
                "fact": edge.fact if hasattr(edge, "fact") else str(edge),
                "name": getattr(edge, "name", ""),
                "created_at": str(getattr(edge, "created_at", "")),
            }
            for edge in results
        ]
    except Exception as e:
        logger.error("search_graph failed: %s", e)
        return []


async def close_graphiti():
    """Close the Graphiti connection."""
    global _graphiti_instance
    if _graphiti_instance:
        try:
            await _graphiti_instance.close()
        except Exception:
            pass
        _graphiti_instance = None
