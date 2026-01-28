"""
FastAPI Routes for Supermemory Integration.

Provides REST API endpoints for memory management:
- Add memories (text, URL, document)
- Search memories
- Chat with memories (RAG)
- BD-specific operations
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field

from .supermemory_client import BDMemoryManager, get_bd_memory_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class AddMemoryRequest(BaseModel):
    """Request to add a text memory."""
    content: str = Field(..., description="Text content to store")
    source_type: str = Field("text", description="Source type (text, note, snippet)")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AddUrlRequest(BaseModel):
    """Request to add a URL memory."""
    url: str = Field(..., description="URL to save and index")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")


class SearchRequest(BaseModel):
    """Request to search memories."""
    query: str = Field(..., description="Search query")
    top_k: int = Field(10, ge=1, le=50, description="Maximum results")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum relevance score")


class ChatRequest(BaseModel):
    """Request to chat with memories."""
    message: str = Field(..., description="User message/question")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for continuity")


class StoreRfpRequest(BaseModel):
    """Request to store an RFP (with file upload handled separately)."""
    title: str = Field(..., description="RFP title")
    agency: Optional[str] = Field(None, description="Issuing agency")
    deadline: Optional[str] = Field(None, description="Response deadline")
    program: Optional[str] = Field(None, description="Associated program")
    solicitation_number: Optional[str] = Field(None, description="Solicitation number")


class StoreContractRequest(BaseModel):
    """Request to store a contract (with file upload handled separately)."""
    contract_number: str = Field(..., description="Contract number")
    contractor: Optional[str] = Field(None, description="Contractor name")
    agency: Optional[str] = Field(None, description="Contracting agency")
    program: Optional[str] = Field(None, description="Associated program")
    value: Optional[str] = Field(None, description="Contract value")
    pop_end: Optional[str] = Field(None, description="Period of performance end")


class StoreIntelRequest(BaseModel):
    """Request to store intelligence."""
    content: str = Field(..., description="Intelligence content")
    entity_name: str = Field(..., description="Program or competitor name")
    intel_type: str = Field("general", description="Type of intel")


class MemoryResponse(BaseModel):
    """Standard memory response."""
    success: bool
    id: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Search response."""
    query: str
    results: List[Dict[str, Any]]
    count: int
    timestamp: str


class ChatResponse(BaseModel):
    """Chat response."""
    message: str
    response: str
    citations: Optional[List[Dict[str, Any]]] = None
    conversation_id: Optional[str] = None
    timestamp: str


# =============================================================================
# BASIC MEMORY ENDPOINTS
# =============================================================================

@router.post("/add", response_model=MemoryResponse)
async def add_memory(request: AddMemoryRequest):
    """
    Add a text memory.

    Store text content with optional tags and metadata.
    """
    try:
        manager = get_bd_memory_manager()
        result = await manager.supermemory.add_memory(
            content=request.content,
            source_type=request.source_type,
            tags=request.tags,
            metadata=request.metadata,
        )
        return MemoryResponse(
            success=True,
            id=result.get("id"),
            message="Memory added successfully",
            data=result,
        )
    except Exception as e:
        logger.error(f"Failed to add memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add/url", response_model=MemoryResponse)
async def add_url_memory(request: AddUrlRequest):
    """
    Add a URL memory.

    The URL content will be extracted and indexed.
    """
    try:
        manager = get_bd_memory_manager()
        result = await manager.supermemory.add_url(
            url=request.url,
            tags=request.tags,
        )
        return MemoryResponse(
            success=True,
            id=result.get("id"),
            message="URL memory added successfully",
            data=result,
        )
    except Exception as e:
        logger.error(f"Failed to add URL memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add/document", response_model=MemoryResponse)
async def add_document_memory(
    file: UploadFile = File(..., description="Document to upload"),
    title: Optional[str] = Form(None, description="Document title"),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
):
    """
    Upload and add a document memory.

    Supports PDF, DOCX, TXT, MD, and other document formats.
    """
    import tempfile
    import os

    try:
        # Save uploaded file temporarily
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            manager = get_bd_memory_manager()
            tag_list = [t.strip() for t in tags.split(",")] if tags else None
            result = await manager.supermemory.add_document(
                file_path=tmp_path,
                title=title or file.filename,
                tags=tag_list,
            )
            return MemoryResponse(
                success=True,
                id=result.get("id"),
                message="Document uploaded successfully",
                data=result,
            )
        finally:
            # Clean up temp file
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SEARCH ENDPOINTS
# =============================================================================

@router.post("/search", response_model=SearchResponse)
async def search_memories(request: SearchRequest):
    """
    Semantic search across memories.

    Returns matching memories ranked by relevance.
    """
    try:
        manager = get_bd_memory_manager()
        results = await manager.supermemory.search(
            query=request.query,
            top_k=request.top_k,
            tags=request.tags,
            min_score=request.min_score,
        )
        return SearchResponse(
            query=request.query,
            results=results,
            count=len(results),
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_memories_get(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(10, ge=1, le=50, description="Maximum results"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
):
    """GET endpoint for search."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    request = SearchRequest(query=q, top_k=top_k, tags=tag_list)
    return await search_memories(request)


# =============================================================================
# CHAT ENDPOINTS
# =============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat_with_memories(request: ChatRequest):
    """
    Chat with AI using memories as context (RAG).

    The AI will use stored memories to answer questions with citations.
    """
    try:
        manager = get_bd_memory_manager()
        result = await manager.supermemory.chat(
            message=request.message,
            conversation_id=request.conversation_id,
        )
        return ChatResponse(
            message=request.message,
            response=result.get("response", result.get("answer", "")),
            citations=result.get("citations", result.get("sources", [])),
            conversation_id=result.get("conversation_id"),
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat")
async def chat_get(
    q: str = Query(..., description="Question to ask"),
    conversation_id: Optional[str] = Query(None, description="Conversation ID"),
):
    """GET endpoint for chat."""
    request = ChatRequest(message=q, conversation_id=conversation_id)
    return await chat_with_memories(request)


# =============================================================================
# BD-SPECIFIC ENDPOINTS
# =============================================================================

@router.post("/bd/rfp", response_model=MemoryResponse)
async def store_rfp(
    file: UploadFile = File(..., description="RFP document"),
    title: str = Form(..., description="RFP title"),
    agency: Optional[str] = Form(None, description="Issuing agency"),
    deadline: Optional[str] = Form(None, description="Response deadline"),
    program: Optional[str] = Form(None, description="Associated program"),
    solicitation_number: Optional[str] = Form(None, description="Solicitation number"),
):
    """
    Store an RFP document with BD metadata.

    Automatically tags as RFP and indexes for search.
    """
    import tempfile
    import os

    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            manager = get_bd_memory_manager()
            result = await manager.store_rfp(
                file_path=tmp_path,
                title=title,
                agency=agency,
                deadline=deadline,
                program=program,
                solicitation_number=solicitation_number,
            )
            return MemoryResponse(
                success=True,
                id=result.get("id"),
                message=f"RFP '{title}' stored successfully",
                data=result,
            )
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Failed to store RFP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bd/rfp/search")
async def search_rfps(
    q: str = Query(..., description="Search query"),
    agency: Optional[str] = Query(None, description="Filter by agency"),
    top_k: int = Query(5, ge=1, le=20, description="Maximum results"),
):
    """Search RFP documents."""
    try:
        manager = get_bd_memory_manager()
        results = await manager.search_rfps(q, agency=agency, top_k=top_k)
        return SearchResponse(
            query=q,
            results=results,
            count=len(results),
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"RFP search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bd/contract", response_model=MemoryResponse)
async def store_contract(
    file: UploadFile = File(..., description="Contract document"),
    contract_number: str = Form(..., description="Contract number"),
    contractor: Optional[str] = Form(None, description="Contractor name"),
    agency: Optional[str] = Form(None, description="Contracting agency"),
    program: Optional[str] = Form(None, description="Associated program"),
    value: Optional[str] = Form(None, description="Contract value"),
    pop_end: Optional[str] = Form(None, description="POP end date"),
):
    """
    Store a contract document with BD metadata.

    Automatically tags as contract and indexes for search.
    """
    import tempfile
    import os

    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            manager = get_bd_memory_manager()
            result = await manager.store_contract(
                file_path=tmp_path,
                contract_number=contract_number,
                contractor=contractor,
                agency=agency,
                program=program,
                value=value,
                pop_end=pop_end,
            )
            return MemoryResponse(
                success=True,
                id=result.get("id"),
                message=f"Contract '{contract_number}' stored successfully",
                data=result,
            )
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Failed to store contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bd/contract/search")
async def search_contracts(
    q: str = Query(..., description="Search query"),
    contractor: Optional[str] = Query(None, description="Filter by contractor"),
    top_k: int = Query(5, ge=1, le=20, description="Maximum results"),
):
    """Search contract documents."""
    try:
        manager = get_bd_memory_manager()
        results = await manager.search_contracts(q, contractor=contractor, top_k=top_k)
        return SearchResponse(
            query=q,
            results=results,
            count=len(results),
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"Contract search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bd/program-intel", response_model=MemoryResponse)
async def store_program_intel(request: StoreIntelRequest):
    """Store program intelligence."""
    try:
        manager = get_bd_memory_manager()
        result = await manager.store_program_intel(
            content=request.content,
            program=request.entity_name,
            intel_type=request.intel_type,
        )
        return MemoryResponse(
            success=True,
            id=result.get("id"),
            message=f"Program intel for '{request.entity_name}' stored",
            data=result,
        )
    except Exception as e:
        logger.error(f"Failed to store program intel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bd/competitor-intel", response_model=MemoryResponse)
async def store_competitor_intel(request: StoreIntelRequest):
    """Store competitor intelligence."""
    try:
        manager = get_bd_memory_manager()
        result = await manager.store_competitor_intel(
            content=request.content,
            competitor=request.entity_name,
            intel_type=request.intel_type,
        )
        return MemoryResponse(
            success=True,
            id=result.get("id"),
            message=f"Competitor intel for '{request.entity_name}' stored",
            data=result,
        )
    except Exception as e:
        logger.error(f"Failed to store competitor intel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/list")
async def list_memories(
    limit: int = Query(50, ge=1, le=100, description="Maximum memories"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
):
    """List memories with pagination."""
    try:
        manager = get_bd_memory_manager()
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        memories = await manager.supermemory.list_memories(
            limit=limit,
            offset=offset,
            tags=tag_list,
        )
        return {
            "memories": memories,
            "count": len(memories),
            "offset": offset,
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"Failed to list memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{memory_id}")
async def get_memory(memory_id: str):
    """Get a specific memory by ID."""
    try:
        manager = get_bd_memory_manager()
        memory = await manager.supermemory.get_memory(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        return memory
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a memory."""
    try:
        manager = get_bd_memory_manager()
        success = await manager.supermemory.delete_memory(memory_id)
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found or delete failed")
        return {"success": True, "message": f"Memory {memory_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview")
async def get_memory_stats():
    """Get memory system statistics."""
    try:
        manager = get_bd_memory_manager()
        stats = await manager.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {"available": False, "error": str(e)}


@router.get("/health")
async def health_check():
    """Health check for memory system."""
    try:
        manager = get_bd_memory_manager()
        stats = await manager.get_stats()
        return {
            "status": "healthy" if stats.get("available") else "degraded",
            "supermemory_available": stats.get("available", False),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
