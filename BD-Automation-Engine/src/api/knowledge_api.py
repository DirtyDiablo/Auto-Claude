"""Phase 39A — Knowledge API

15 endpoints for temporal knowledge graph, entity resolution, and knowledge compilation.
"""

import logging
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.knowledge.temporal_kg import (
    Episode,
    EpisodeType,
    get_temporal_kg,
)
from src.knowledge.entity_resolution import (
    get_resolution_engine,
)
from src.knowledge.compiler import (
    EpisodeSource,
    get_knowledge_compiler,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# =========================================
# REQUEST MODELS
# =========================================

class IngestEpisodeRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Text content of the episode")
    episode_type: str = Field(
        EpisodeType.CONVERSATION_NOTE.value,
        description="Type of episode",
    )
    source: str = Field("", description="Source identifier")
    actor: str = Field("", description="Who created this episode")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TemporalQueryRequest(BaseModel):
    timestamp: str = Field(..., description="ISO 8601 timestamp to query at")
    entity_id: Optional[str] = Field(None, description="Filter by entity ID")
    predicate: Optional[str] = Field(None, description="Filter by predicate/edge type")


class ResolveEntityRequest(BaseModel):
    entity_a: Dict[str, Any] = Field(..., description="First entity to compare")
    entity_b: Dict[str, Any] = Field(..., description="Second entity to compare")


class MergeEntityRequest(BaseModel):
    primary: Dict[str, Any] = Field(..., description="Primary entity (kept)")
    duplicate: Dict[str, Any] = Field(..., description="Duplicate entity (merged in)")


class GlobalResolutionRequest(BaseModel):
    entities: List[Dict[str, Any]] = Field(..., description="All entities to scan")
    entity_type: str = Field("person", description="Entity type to resolve")


class CompileTextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to compile into facts")
    source_type: str = Field("conversation_note", description="Source type")
    author: str = Field("", description="Author of the text")
    contact_name: str = Field("", description="Contact mentioned")
    company: str = Field("", description="Company mentioned")


class CompileBatchRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1, description="List of texts to compile")


class CompileNotesRequest(BaseModel):
    notes: List[Dict[str, Any]] = Field(
        ..., min_length=1,
        description="Structured notes (contact_name, company, subject, notes/content)",
    )


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    limit: int = Field(20, ge=1, le=100)


class HybridSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    predicate: Optional[str] = Field(None, description="Filter by predicate")
    active_only: bool = Field(False, description="Only return active facts")
    limit: int = Field(20, ge=1, le=100)


# =========================================
# SERIALIZATION HELPERS
# =========================================

def _serialize_dataclass(obj: Any) -> Any:
    """Convert dataclass to dict, handling nested dataclasses."""
    if hasattr(obj, "__dataclass_fields__"):
        d = asdict(obj)
        # Remove embedding fields (too large for JSON response)
        d.pop("embedding", None)
        return d
    return obj


def _serialize_list(items: list) -> list:
    return [_serialize_dataclass(item) for item in items]


# =========================================
# ENDPOINTS — Temporal Knowledge Graph
# =========================================

@router.post("/ingest")
async def ingest_episode(request: IngestEpisodeRequest):
    """Ingest an episode into the temporal knowledge graph."""
    kg = get_temporal_kg()
    episode = Episode(
        episode_type=request.episode_type,
        content=request.content,
        source=request.source,
        actor=request.actor,
        metadata=request.metadata,
    )
    result = kg.ingest_episode(episode)
    return _serialize_dataclass(result)


@router.get("/entity/{entity_id}/timeline")
async def get_entity_timeline(entity_id: str):
    """Get full timeline for an entity."""
    kg = get_temporal_kg()
    timeline = kg.get_entity_timeline(entity_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    return _serialize_dataclass(timeline)


@router.get("/entity/{entity_id}/changes")
async def get_entity_changes(entity_id: str, since: str = ""):
    """Get changes for an entity since a given date."""
    kg = get_temporal_kg()
    if not since:
        raise HTTPException(status_code=400, detail="'since' query parameter required")
    changes = kg.detect_changes(entity_id, since)
    return {"entity_id": entity_id, "since": since, "changes": _serialize_list(changes)}


@router.post("/query/temporal")
async def query_temporal(request: TemporalQueryRequest):
    """Query the knowledge graph at a specific point in time."""
    kg = get_temporal_kg()
    facts = kg.query_facts_at_time(
        timestamp=request.timestamp,
        entity_id=request.entity_id,
        predicate=request.predicate,
    )
    return {"timestamp": request.timestamp, "facts": _serialize_list(facts), "count": len(facts)}


@router.get("/contradictions")
async def get_contradictions():
    """List all detected contradictions in the knowledge graph."""
    kg = get_temporal_kg()
    contradictions = kg.find_contradictions()
    return {"contradictions": _serialize_list(contradictions), "count": len(contradictions)}


# =========================================
# ENDPOINTS — Entity Resolution
# =========================================

@router.post("/resolve/entity")
async def resolve_entity(request: ResolveEntityRequest):
    """Resolve whether two entity mentions refer to the same real-world entity."""
    engine = get_resolution_engine()
    result = engine.resolve(request.entity_a, request.entity_b)
    return _serialize_dataclass(result)


@router.get("/resolve/candidates/{entity_id}")
async def get_resolution_candidates(entity_id: str, limit: int = 10):
    """Find resolution candidates for an entity from the knowledge graph."""
    kg = get_temporal_kg()
    engine = get_resolution_engine()

    # Get the source entity from the KG
    entity_obj = kg._entities.get(entity_id)
    if entity_obj is None:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

    # Build entity dict for resolution
    entity_dict = {
        "id": entity_obj.id,
        "name": entity_obj.name,
        "type": entity_obj.entity_type,
    }
    entity_dict.update(entity_obj.properties)

    # Build candidate pool from all entities of the same type
    all_entities = [
        {"id": e.id, "name": e.name, "type": e.entity_type, **e.properties}
        for e in kg._entities.values()
        if e.id != entity_id and e.entity_type == entity_obj.entity_type
    ]

    candidates = engine.find_candidates(entity_dict, all_entities, limit)
    return {"entity_id": entity_id, "candidates": _serialize_list(candidates)}


@router.post("/resolve/merge")
async def merge_entities(request: MergeEntityRequest):
    """Merge two confirmed duplicate entities."""
    engine = get_resolution_engine()
    result = engine.merge_entities(request.primary, request.duplicate)
    return _serialize_dataclass(result)


@router.post("/resolve/global")
async def run_global_resolution(request: GlobalResolutionRequest):
    """Run global entity resolution to find all duplicates."""
    engine = get_resolution_engine()
    report = engine.run_global_resolution(request.entities, request.entity_type)
    return _serialize_dataclass(report)


# =========================================
# ENDPOINTS — Knowledge Compiler
# =========================================

@router.post("/compile")
async def compile_text(request: CompileTextRequest):
    """Compile unstructured text into structured facts."""
    compiler = get_knowledge_compiler()
    source = EpisodeSource(
        source_type=request.source_type,
        author=request.author,
        contact_name=request.contact_name,
        company=request.company,
    )
    facts = compiler.compile(request.text, source)
    return {"facts": _serialize_list(facts), "count": len(facts)}


@router.post("/compile/batch")
async def compile_batch(request: CompileBatchRequest):
    """Batch compile multiple texts with deduplication."""
    compiler = get_knowledge_compiler()
    report = compiler.compile_batch(request.texts)
    return _serialize_dataclass(report)


@router.post("/compile/notes")
async def compile_notes(request: CompileNotesRequest):
    """Compile structured notes (e.g., from master_notes.csv) into facts."""
    compiler = get_knowledge_compiler()
    report = compiler.compile_from_notes(request.notes)
    return _serialize_dataclass(report)


# =========================================
# ENDPOINTS — Stats & Search
# =========================================

@router.get("/stats")
async def get_knowledge_stats():
    """Get comprehensive knowledge graph statistics."""
    kg = get_temporal_kg()
    return kg.get_stats()


@router.get("/search/semantic")
async def search_semantic(query: str, entity_type: Optional[str] = None, limit: int = 20):
    """Search entities across the knowledge graph by name/alias."""
    kg = get_temporal_kg()
    entities = kg.search_entities(query, entity_type, limit)
    return {"results": _serialize_list(entities), "count": len(entities)}


@router.get("/search/hybrid")
async def search_hybrid(
    query: str,
    entity_type: Optional[str] = None,
    predicate: Optional[str] = None,
    active_only: bool = False,
    limit: int = 20,
):
    """Hybrid search: entities by name + facts by predicate/subject/object."""
    kg = get_temporal_kg()

    # Entity search
    entities = kg.search_entities(query, entity_type, limit)

    # Fact search — use matching entity IDs as subject/object filters
    entity_ids = {e.id for e in entities}
    matching_facts = []

    # Search facts referencing matched entities
    for eid in entity_ids:
        facts = kg.search_facts(
            predicate=predicate,
            subject_id=eid,
            active_only=active_only,
        )
        matching_facts.extend(facts)
        facts_obj = kg.search_facts(
            predicate=predicate,
            object_id=eid,
            active_only=active_only,
        )
        matching_facts.extend(facts_obj)

    # Deduplicate facts by ID
    seen_fact_ids = set()
    unique_facts = []
    for f in matching_facts:
        if f.id not in seen_fact_ids:
            seen_fact_ids.add(f.id)
            unique_facts.append(f)

    return {
        "entities": _serialize_list(entities[:limit]),
        "facts": _serialize_list(unique_facts[:limit]),
        "entity_count": len(entities),
        "fact_count": len(unique_facts),
    }


# =========================================
# INTEGRATION
# =========================================

def include_knowledge_router(app: FastAPI) -> None:
    """Register the knowledge router with the FastAPI app."""
    app.include_router(router)
    logger.info("Knowledge API router registered with 15 endpoints")
