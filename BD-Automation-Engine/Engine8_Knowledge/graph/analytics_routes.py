"""
Graph Analytics API Routes - Influence scoring, community detection, Graph RAG.

Prefix: /graph
"""

import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["Graph Analytics"])


# =========================================
# REQUEST MODELS
# =========================================

class GraphRAGQuery(BaseModel):
    question: str
    max_hops: int = 2
    vector_limit: int = 10


# =========================================
# INFLUENCE SCORING ENDPOINTS
# =========================================

@router.get("/influence/leaderboard")
async def influence_leaderboard(
    entity_type: Optional[str] = Query(None, description="Filter: Contact, Contractor, Program"),
    limit: int = Query(25, description="Max results"),
):
    """Get ranked leaderboard by composite influence score."""
    try:
        from Engine8_Knowledge.graph.influence_scoring import get_influence_scorer
        scorer = get_influence_scorer()
        return {"leaderboard": scorer.get_leaderboard(entity_type, limit)}
    except Exception as e:
        logger.error(f"Influence leaderboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/influence/entity/{entity_name}")
async def influence_entity(entity_name: str):
    """Get influence details for a specific entity."""
    try:
        from Engine8_Knowledge.graph.influence_scoring import get_influence_scorer
        scorer = get_influence_scorer()
        result = scorer.get_entity_influence(entity_name)
        if not result:
            raise HTTPException(status_code=404, detail=f"Entity not found: {entity_name}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity influence error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/influence/hidden-gems")
async def influence_hidden_gems(limit: int = Query(20)):
    """Get high-centrality entities with low official tier/priority."""
    try:
        from Engine8_Knowledge.graph.influence_scoring import get_influence_scorer
        scorer = get_influence_scorer()
        return {"hidden_gems": scorer.get_hidden_gems(limit)}
    except Exception as e:
        logger.error(f"Hidden gems error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bridges")
async def graph_bridges(limit: int = Query(20)):
    """Get bridge nodes with high betweenness centrality."""
    try:
        from Engine8_Knowledge.graph.influence_scoring import get_influence_scorer
        scorer = get_influence_scorer()
        return {"bridges": scorer.get_bridges(limit)}
    except Exception as e:
        logger.error(f"Bridges error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# COMMUNITY DETECTION ENDPOINTS
# =========================================

@router.get("/communities/summary")
async def communities_summary():
    """Get summary of all detected communities."""
    try:
        from Engine8_Knowledge.graph.community_detection import get_community_detector
        detector = get_community_detector()
        return detector.get_community_summary()
    except Exception as e:
        logger.error(f"Community summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/communities/{community_id}")
async def community_detail(community_id: int):
    """Get detailed view of a specific community."""
    try:
        from Engine8_Knowledge.graph.community_detection import get_community_detector
        detector = get_community_detector()
        result = detector.get_community_detail(community_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Community not found: {community_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Community detail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/communities/entity/{entity_name}")
async def entity_community(entity_name: str):
    """Find which community an entity belongs to."""
    try:
        from Engine8_Knowledge.graph.community_detection import get_community_detector
        detector = get_community_detector()
        result = detector.get_entity_community(entity_name)
        if not result:
            raise HTTPException(status_code=404, detail=f"Entity not found or not in any community: {entity_name}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity community error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/communities/bridges")
async def community_bridges(limit: int = Query(20)):
    """Get entities that bridge multiple communities."""
    try:
        from Engine8_Knowledge.graph.community_detection import get_community_detector
        detector = get_community_detector()
        return {"bridges": detector.get_cross_community_bridges(limit)}
    except Exception as e:
        logger.error(f"Community bridges error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/communities/graph")
async def community_meta_graph():
    """Get meta-graph of communities (communities as nodes, cross-edges between them)."""
    try:
        from Engine8_Knowledge.graph.community_detection import get_community_detector
        detector = get_community_detector()
        return detector.get_community_graph()
    except Exception as e:
        logger.error(f"Community graph error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# GRAPH RAG ENDPOINTS
# =========================================

@router.post("/rag-query")
async def graph_rag_query(data: GraphRAGQuery):
    """
    Execute a Graph RAG query combining knowledge graph traversal
    with vector similarity search.
    """
    try:
        from Engine8_Knowledge.graph.graph_rag import get_graph_rag
        engine = get_graph_rag()
        result = engine.query(
            question=data.question,
            max_hops=data.max_hops,
            vector_limit=data.vector_limit,
        )
        return {
            "query": result.query,
            "answer": result.answer,
            "graph_entities": result.graph_entities[:30],
            "graph_relationships": result.graph_relationships[:50],
            "vector_results": result.vector_results[:10],
            "provenance": result.provenance,
            "confidence": result.confidence,
            "elapsed_ms": result.elapsed_ms,
        }
    except Exception as e:
        logger.error(f"Graph RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag-context/{entity_name}")
async def graph_rag_entity_context(entity_name: str):
    """Get rich Graph RAG context for a specific entity."""
    try:
        from Engine8_Knowledge.graph.graph_rag import get_graph_rag
        engine = get_graph_rag()
        return engine.get_entity_context(entity_name)
    except Exception as e:
        logger.error(f"Graph RAG context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
