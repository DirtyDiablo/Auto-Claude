"""
FastAPI routes for LightRAG graph-based reasoning.
Import this into main api.py during integration step.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import structlog

logger = structlog.get_logger(__name__)

try:
    from .graph_rag import BDGraphRAG, QueryMode, QueryResult
    from .entity_extractor import BDEntityExtractor, EntityType
except ImportError:
    from graph_rag import BDGraphRAG, QueryMode, QueryResult
    from entity_extractor import BDEntityExtractor, EntityType

router = APIRouter(prefix="/lightrag", tags=["LightRAG Graph Reasoning"])

# Global instances
_graph_rag: Optional[BDGraphRAG] = None
_entity_extractor: Optional[BDEntityExtractor] = None


# Request/Response models
class InsertRequest(BaseModel):
    documents: List[str]
    metadata: Optional[List[Dict]] = None
    enrich_entities: bool = True


class QueryRequest(BaseModel):
    query: str
    mode: str = "hybrid"  # local, global, hybrid, naive


class EntityRequest(BaseModel):
    text: str


async def get_graph_rag() -> BDGraphRAG:
    """Get or create BDGraphRAG instance (async to ensure storage init)."""
    global _graph_rag
    logger.debug("get_graph_rag_called", graph_rag_is_none=(_graph_rag is None))

    if _graph_rag is None:
        # Get absolute path for working directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        working_dir = os.path.join(base_dir, "data", "lightrag")

        logger.debug("creating_graph_rag", working_dir=working_dir)
        _graph_rag = BDGraphRAG(
            working_dir=working_dir,
            use_qdrant=False,  # Use NanoVectorDB for simplicity
            llm_provider="openai"
        )
        logger.info("lightrag_created", working_dir=working_dir)

    # Ensure storages are initialized
    logger.debug("storage_init_check", storage_initialized=_graph_rag._storage_initialized)
    if not _graph_rag._storage_initialized:
        logger.debug("calling_initialize")
        await _graph_rag.initialize()
        logger.debug("initialize_completed")

    return _graph_rag


def get_entity_extractor() -> BDEntityExtractor:
    """Get or create entity extractor instance."""
    global _entity_extractor
    if _entity_extractor is None:
        _entity_extractor = BDEntityExtractor()
    return _entity_extractor


@router.get("/test-write")
async def test_write():
    """Test endpoint to verify file writing works."""
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    debug_file = os.path.join(base_dir, "data", "test_write.log")
    with open(debug_file, "a") as f:
        f.write(f"[{__import__('datetime').datetime.now()}] test-write called\n")
    return {"status": "wrote to file", "path": debug_file}


@router.post("/insert")
async def insert_documents(request: InsertRequest):
    """
    Insert documents into LightRAG with entity extraction.

    Documents are processed for entity extraction and indexed
    for graph-based reasoning.
    """
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    debug_file = os.path.join(base_dir, "data", "debug_route.log")

    try:
        with open(debug_file, "a") as f:
            f.write(f"[{__import__('datetime').datetime.now()}] /insert called\n")

        rag = await get_graph_rag()

        with open(debug_file, "a") as f:
            f.write(f"[{__import__('datetime').datetime.now()}] Got rag, _storage_initialized: {rag._storage_initialized}\n")

        extractor = get_entity_extractor()

        # Optionally enrich documents with entity metadata
        documents = request.documents
        if request.enrich_entities:
            documents = [extractor.enrich_document(doc) for doc in documents]

        with open(debug_file, "a") as f:
            f.write(f"[{__import__('datetime').datetime.now()}] Calling insert_documents with {len(documents)} docs\n")

        result = await rag.insert_documents(documents, request.metadata)

        with open(debug_file, "a") as f:
            f.write(f"[{__import__('datetime').datetime.now()}] Result: {result}\n")

        return result
    except Exception as e:
        with open(debug_file, "a") as f:
            f.write(f"[{__import__('datetime').datetime.now()}] ERROR: {e}\n")
            import traceback
            f.write(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_graph(request: QueryRequest):
    """
    Query LightRAG with specified mode.

    Modes:
    - local: Focus on specific entities mentioned in query
    - global: High-level summaries across the knowledge base
    - hybrid: Combined local + global reasoning (recommended)
    - naive: Simple vector search without graph reasoning
    """
    try:
        rag = await get_graph_rag()

        # Parse mode
        try:
            mode = QueryMode(request.mode)
        except ValueError:
            mode = QueryMode.HYBRID

        result = await rag.query(request.query, mode)

        return {
            "query": result.query,
            "mode": result.mode.value,
            "answer": result.answer,
            "entities_found": result.entities_found,
            "relationships": result.relationships,
            "sources": result.sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query")
async def query_graph_get(query: str, mode: str = "hybrid"):
    """GET endpoint for querying LightRAG."""
    request = QueryRequest(query=query, mode=mode)
    return await query_graph(request)


@router.get("/entity/{entity_name}")
async def get_entity(entity_name: str):
    """
    Get relationship graph for a specific entity.

    Returns entity information and its relationships
    from the knowledge graph.
    """
    try:
        rag = await get_graph_rag()
        extractor = get_entity_extractor()

        # First check if it's a known entity
        entity_info = extractor.get_entity_info(entity_name)

        # Get graph data
        graph_data = rag.get_entity_graph(entity_name)

        return {
            "entity_name": entity_name,
            "known_entity": entity_info,
            "graph_data": graph_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relationships")
async def get_relationships(contractor: Optional[str] = None):
    """
    Get contractor teaming relationships.

    If contractor is specified, returns relationships for that contractor.
    Otherwise returns major teaming relationships across all contractors.
    """
    try:
        rag = await get_graph_rag()
        relationships = rag.get_contractor_relationships(contractor)

        return {
            "contractor": contractor,
            "relationships": relationships
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/program/{program_name}/contractors")
async def get_program_contractors(program_name: str):
    """
    Get contractors associated with a program.

    Returns prime contractors, subcontractors, and their roles
    on the specified program.
    """
    try:
        rag = await get_graph_rag()
        result = rag.get_program_contractors(program_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teaming-path")
async def find_teaming_path(contractor1: str, contractor2: str):
    """
    Find relationship path between two contractors.

    Discovers how two contractors are connected through
    shared programs, teaming arrangements, or partnerships.
    """
    try:
        rag = await get_graph_rag()
        result = rag.find_teaming_path(contractor1, contractor2)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-entities")
async def extract_entities(request: EntityRequest):
    """
    Extract BD entities from text.

    Identifies contractors, programs, locations, technologies,
    and agencies mentioned in the text.
    """
    try:
        extractor = get_entity_extractor()
        entities = extractor.extract_entities(request.text)
        relationships = extractor.extract_relationships(request.text)
        tags = extractor.suggest_tags(request.text)

        return {
            "entities": [
                {
                    "name": e.name,
                    "type": e.type.value,
                    "confidence": e.confidence,
                    "context": e.context
                }
                for e in entities
            ],
            "relationships": [
                {
                    "source": r.source,
                    "target": r.target,
                    "type": r.relationship_type,
                    "confidence": r.confidence,
                    "evidence": r.evidence
                }
                for r in relationships
            ],
            "suggested_tags": tags
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/known-entities")
async def get_known_entities():
    """
    Get all known BD entities by type.

    Returns the dictionary of known contractors, programs,
    locations, technologies, and agencies.
    """
    return BDEntityExtractor.get_all_known_entities()


@router.get("/stats")
async def lightrag_stats():
    """Get LightRAG statistics."""
    try:
        rag = await get_graph_rag()
        return rag.stats()
    except Exception as e:
        return {"error": str(e), "initialized": False}


@router.get("/status")
async def lightrag_status():
    """Check LightRAG status and configuration."""
    try:
        rag = await get_graph_rag()
        stats = rag.stats()
        return {
            "status": "ready" if stats.get("initialized") else "initializing",
            "working_dir": stats.get("working_dir"),
            "llm_provider": stats.get("llm_provider"),
            "graph_stats": stats.get("graph", {})
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
