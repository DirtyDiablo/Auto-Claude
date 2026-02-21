"""
Graph API router - Exposes BDKnowledgeGraph as REST endpoints.

Endpoints:
  GET  /graph/entity/{entity_id}               - Entity with relationships
  GET  /graph/relationships/{entity_id}         - Relationships (optional type filter)
  GET  /graph/path/{source_id}/{target_id}      - Shortest path
  GET  /graph/communities                       - Detected communities
  GET  /graph/teaming-partners/{company}        - Teaming partner recommendations
  GET  /graph/competitive-landscape/{program}   - Competitive landscape
  GET  /graph/search                            - Search entities by name/type
  GET  /graph/stats                             - Graph statistics
  POST /graph/build                             - Rebuild graph from Qdrant
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger("BDKnowledgeAPI")

try:
    from Engine8_Knowledge.graph.knowledge_graph import (
        BDKnowledgeGraph,
        get_graph,
        ENTITY_TYPES,
        RELATIONSHIP_TYPES,
    )

    GRAPH_AVAILABLE = True
except ImportError as e:
    GRAPH_AVAILABLE = False
    logger.warning(f"Knowledge graph module not available: {e}")

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])

# Lazy singleton
_graph: Optional[BDKnowledgeGraph] = None


def _get_graph() -> BDKnowledgeGraph:
    """Get or create the knowledge graph instance."""
    global _graph
    if not GRAPH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Knowledge graph module not available")
    if _graph is None:
        _graph = get_graph()
    return _graph


# ------------------------------------------------------------------
# Entity endpoints
# ------------------------------------------------------------------


@router.get("/entity/{entity_id}")
async def get_entity(entity_id: str):
    """Get entity with all relationships."""
    graph = _get_graph()
    entity = graph.get_entity(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity not found: {entity_id}")
    return entity


@router.get("/relationships/{entity_id}")
async def get_relationships(
    entity_id: str,
    relation_type: Optional[str] = Query(
        None, description="Filter by relationship type"
    ),
):
    """Get relationships for an entity, optionally filtered by type."""
    graph = _get_graph()
    entity = graph.get_entity(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity not found: {entity_id}")

    relations = graph.get_relationships(entity_id, relation_type=relation_type)
    return {
        "entity_id": entity_id,
        "entity_name": entity["name"],
        "relation_type_filter": relation_type,
        "relationships": relations,
        "count": len(relations),
    }


# ------------------------------------------------------------------
# Path finding
# ------------------------------------------------------------------


@router.get("/path/{source_id}/{target_id}")
async def shortest_path(
    source_id: str,
    target_id: str,
    max_depth: int = Query(5, ge=1, le=20, description="Maximum hops"),
):
    """Find shortest path between two entities using BFS."""
    graph = _get_graph()

    if graph.get_entity(source_id) is None:
        raise HTTPException(status_code=404, detail=f"Source entity not found: {source_id}")
    if graph.get_entity(target_id) is None:
        raise HTTPException(status_code=404, detail=f"Target entity not found: {target_id}")

    path = graph.shortest_path(source_id, target_id, max_depth=max_depth)
    return {
        "source": source_id,
        "target": target_id,
        "path": path,
        "hops": max(0, len(path) - 1) if path else 0,
        "found": len(path) > 0,
    }


# ------------------------------------------------------------------
# Community detection
# ------------------------------------------------------------------


@router.get("/communities")
async def find_communities(
    min_size: int = Query(3, ge=2, description="Minimum community size"),
):
    """List detected communities (connected components)."""
    graph = _get_graph()
    communities = graph.find_communities(min_size=min_size)
    return {
        "communities": communities,
        "count": len(communities),
        "min_size": min_size,
    }


# ------------------------------------------------------------------
# BD-specific endpoints
# ------------------------------------------------------------------


@router.get("/teaming-partners/{company}")
async def get_teaming_partners(
    company: str,
    program: Optional[str] = Query(None, description="Optional program filter"),
):
    """Recommend teaming partners for a company."""
    graph = _get_graph()
    partners = graph.get_teaming_partners(company, program=program)
    return {
        "company": company,
        "program_filter": program,
        "partners": partners,
        "count": len(partners),
    }


@router.get("/competitive-landscape/{program}")
async def get_competitive_landscape(program: str):
    """Get competitive landscape for a program."""
    graph = _get_graph()
    landscape = graph.get_competitive_landscape(program)
    if "error" in landscape:
        raise HTTPException(status_code=404, detail=landscape["error"])
    return landscape


# ------------------------------------------------------------------
# Search
# ------------------------------------------------------------------


@router.get("/search")
async def search_entities(
    q: str = Query(..., description="Search query"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
):
    """Search entities by name and optional type filter."""
    graph = _get_graph()
    results = graph.search_entities(q, entity_type=entity_type, limit=limit)
    return {
        "query": q,
        "entity_type": entity_type,
        "results": results,
        "count": len(results),
    }


# ------------------------------------------------------------------
# Stats
# ------------------------------------------------------------------


@router.get("/stats")
async def get_stats():
    """Get graph statistics."""
    graph = _get_graph()
    return graph.get_stats()


# ------------------------------------------------------------------
# Build / rebuild
# ------------------------------------------------------------------


@router.post("/build")
async def build_graph():
    """Rebuild graph from Qdrant data."""
    graph = _get_graph()
    import asyncio

    result = await asyncio.to_thread(graph.build_from_qdrant)
    return result
