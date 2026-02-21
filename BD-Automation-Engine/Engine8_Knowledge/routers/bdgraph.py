"""BD Knowledge Graph router — program ecosystems, contact networks, teaming paths."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger("BDKnowledgeAPI")

# Import BD Knowledge Graph
try:
    from Engine8_Knowledge.graph.bd_knowledge_graph import (
        get_knowledge_graph as _get_bd_graph,
        ENTITY_TYPES,
        RELATIONSHIP_TYPES,
    )

    BD_GRAPH_AVAILABLE = True
except ImportError as e:
    BD_GRAPH_AVAILABLE = False
    ENTITY_TYPES = {}
    RELATIONSHIP_TYPES = {}
    logger.warning(f"BD Knowledge Graph not available: {e}")

router = APIRouter(prefix="/bdgraph", tags=["BD Knowledge Graph"])

# Lazy singleton
_bd_graph = None


def get_bd_knowledge_graph():
    global _bd_graph
    if _bd_graph is None and BD_GRAPH_AVAILABLE:
        _bd_graph = _get_bd_graph()
    return _bd_graph


def _require_graph():
    bg = get_bd_knowledge_graph()
    if not bg:
        raise HTTPException(status_code=503, detail="BD Knowledge Graph not available")
    return bg


@router.get("/program/{program_name}")
async def bdgraph_program_ecosystem(program_name: str):
    """Get full ecosystem for a program — primes, subs, contacts, jobs, locations."""
    bg = _require_graph()
    result = bg.get_program_ecosystem(program_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/contact/{contact_name}")
async def bdgraph_contact_network(contact_name: str):
    """Get contact's professional network — employer, programs, manages, connections."""
    bg = _require_graph()
    result = bg.get_contact_network(contact_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/teaming/{from_contractor}/{to_program}")
async def bdgraph_teaming_path(
    from_contractor: str, to_program: str, max_depth: int = 4
):
    """Find teaming path from a contractor to a program via BFS."""
    bg = _require_graph()
    path = bg.find_teaming_path(from_contractor, to_program, max_depth)
    return {"from": from_contractor, "to": to_program, "path": path}


@router.get("/query")
async def bdgraph_query(q: str = Query(..., description="Natural language query")):
    """Natural language query against the BD knowledge graph."""
    bg = _require_graph()
    results = bg.query(q)
    return {"query": q, "results": results}


@router.get("/search")
async def bdgraph_search(
    q: str = Query(..., description="Search query"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(20, description="Max results"),
):
    """Search entities in the BD knowledge graph."""
    bg = _require_graph()
    results = bg.search_entities(q, entity_type, limit)
    return {
        "query": q,
        "entity_type": entity_type,
        "results": [e.to_dict() for e in results],
    }


@router.post("/entity")
async def bdgraph_add_entity(
    entity_type: str = Query(
        ...,
        description=f"Entity type: {list(ENTITY_TYPES.keys())}",
    ),
    name: str = Query(..., description="Entity name"),
    properties: Optional[str] = Query(None, description="JSON properties"),
):
    """Add an entity to the BD knowledge graph."""
    bg = _require_graph()
    props = json.loads(properties) if properties else {}
    entity = bg.add_entity(entity_type, name, props)
    return {"success": True, "entity": entity.to_dict()}


@router.post("/relationship")
async def bdgraph_add_relationship(
    from_entity: str = Query(..., description="Source entity (ID or name)"),
    rel_type: str = Query(..., description="Relationship type"),
    to_entity: str = Query(..., description="Target entity (ID or name)"),
    confidence: float = Query(1.0, description="Confidence score 0-1"),
):
    """Add a relationship between entities."""
    bg = _require_graph()
    try:
        rel = bg.add_relationship(
            from_entity, rel_type, to_entity, confidence=confidence
        )
        return {"success": True, "relationship": rel.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
async def bdgraph_stats():
    """Get BD knowledge graph statistics."""
    bg = get_bd_knowledge_graph()
    if not bg:
        return {"available": False, "error": "BD Knowledge Graph not available"}
    stats = bg.get_stats()
    stats["available"] = True
    return stats


@router.post("/populate")
async def bdgraph_populate_from_store():
    """Populate the BD knowledge graph from the vector store."""
    from Engine8_Knowledge.deps import get_store

    bg = _require_graph()
    store = get_store()
    if not store:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    bg.populate_from_vector_store(store)
    return {"success": True, "stats": bg.get_stats()}


@router.get("/graph")
async def bdgraph_full_graph(
    limit: int = Query(500, description="Max entities to return"),
):
    """Return full graph as nodes + edges for visualization."""
    bg = _require_graph()
    all_entities = list(bg._entity_cache.values())[:limit]
    nodes = []
    entity_ids = set()
    for e in all_entities:
        nodes.append(
            {
                "id": e.id,
                "type": e.type.lower(),
                "name": e.name,
                **e.properties,
            }
        )
        entity_ids.add(e.id)

    edges = []
    cursor = bg.conn.execute(
        "SELECT from_entity_id, to_entity_id, type FROM relationships"
    )
    for row in cursor:
        if row[0] in entity_ids and row[1] in entity_ids:
            edges.append({"source": row[0], "target": row[1], "type": row[2]})

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(bg._entity_cache),
        "total_edges": sum(
            1
            for _ in bg.conn.execute(
                "SELECT COUNT(*) FROM relationships"
            ).fetchone()
        ),
    }


@router.get("/introduction-path/{from_contact}/{to_contact}")
async def bdgraph_introduction_path(
    from_contact: str,
    to_contact: str,
    max_depth: int = Query(5, description="Max hops to search"),
):
    """Find shortest warm introduction path between two contacts."""
    bg = _require_graph()
    path = bg.find_teaming_path(from_contact, to_contact, max_depth)
    if path and isinstance(path[0], dict) and "error" in path[0]:
        return {
            "from": from_contact,
            "to": to_contact,
            "path": [],
            "hops": 0,
            "error": path[0]["error"],
        }
    return {
        "from": from_contact,
        "to": to_contact,
        "path": path,
        "hops": max(0, len(path) - 1),
    }


@router.get("/types")
async def bdgraph_list_types():
    """List available entity and relationship types."""
    if not BD_GRAPH_AVAILABLE:
        raise HTTPException(status_code=503, detail="BD Knowledge Graph not available")
    return {
        "entity_types": ENTITY_TYPES,
        "relationship_types": {
            k: {"from": v[0], "to": v[1]} for k, v in RELATIONSHIP_TYPES.items()
        },
    }
