"""
RAGflow Router - FastAPI endpoints for RAGflow integration.

Provides endpoints for:
- Health check and status
- Knowledge base management
- Document upload and sync
- Query operations
- Program intelligence
- Call prep generation
- GraphRAG operations
"""

import os
import logging
import traceback
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from .ragflow_client import (
    RAGflowClient,
    RAGflowConfig,
    get_ragflow_client,
)
from .bd_knowledge_manager import (
    BDKnowledgeManager,
    get_bd_knowledge_manager,
    BD_KNOWLEDGE_BASES,
)
from .document_preprocessor import BDDocumentPreprocessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ragflow", tags=["RAGflow Knowledge Intelligence"])

# Global instances
_client: Optional[RAGflowClient] = None
_manager: Optional[BDKnowledgeManager] = None
_preprocessor: Optional[BDDocumentPreprocessor] = None


# =============================================================================
# Request/Response Models
# =============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    ragflow_available: bool
    ragflow_url: str = ""
    knowledge_bases: Dict[str, str] = {}
    timestamp: str


class InitializeRequest(BaseModel):
    """Request to initialize knowledge bases."""

    force_recreate: bool = Field(False, description="Force recreate existing KBs")


class InitializeResponse(BaseModel):
    """Response from KB initialization."""

    success: bool
    knowledge_bases: Dict[str, str]
    message: str


class UploadRequest(BaseModel):
    """Document upload metadata."""

    kb_name: str = Field(..., description="Target knowledge base name")
    chunk_method: Optional[str] = Field(None, description="Override chunk method")
    preprocess: bool = Field(True, description="Preprocess document before upload")


class UploadResponse(BaseModel):
    """Document upload response."""

    success: bool
    doc_id: Optional[str] = None
    kb_name: str
    file_name: str
    message: str


class QueryRequest(BaseModel):
    """Query request."""

    question: str = Field(..., description="Query question")
    context: str = Field(
        "general",
        description="Query context: program, contact, rfp, past_performance, humint, general",
    )
    top_k: int = Field(5, ge=1, le=20, description="Max results")
    with_answer: bool = Field(True, description="Generate LLM answer")


class QueryResponse(BaseModel):
    """Query response."""

    question: str
    answer: Optional[str]
    chunks: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    query_time_ms: float


class ProgramIntelRequest(BaseModel):
    """Program intelligence request."""

    program_name: str = Field(..., description="Program name to research")
    include_related: bool = Field(True, description="Include related programs")


class ContactPrepRequest(BaseModel):
    """Call prep request."""

    contact_name: str = Field(..., description="Contact name")
    program_context: Optional[str] = Field(None, description="Program context for call")


class SyncNotionRequest(BaseModel):
    """Notion sync request."""

    database_id: str = Field(..., description="Notion database ID")
    kb_name: str = Field(..., description="Target KB name")


class GraphBuildResponse(BaseModel):
    """Graph build response."""

    success: bool
    tasks: Dict[str, str]
    message: str


# =============================================================================
# Helper Functions
# =============================================================================


async def get_client() -> RAGflowClient:
    """Get or create RAGflow client."""
    global _client
    if _client is None:
        _client = await get_ragflow_client()
    if not _client._initialized:
        await _client.initialize()
    return _client


async def get_manager() -> BDKnowledgeManager:
    """Get or create BD Knowledge Manager."""
    global _manager
    if _manager is None:
        _manager = await get_bd_knowledge_manager()
    if not _manager._initialized:
        await _manager.initialize()
    return _manager


def get_preprocessor() -> BDDocumentPreprocessor:
    """Get or create document preprocessor."""
    global _preprocessor
    if _preprocessor is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "data", "ragflow_preprocessed")
        _preprocessor = BDDocumentPreprocessor(output_dir=output_dir)
    return _preprocessor


# =============================================================================
# Health & Status Endpoints
# =============================================================================


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check RAGflow server health and availability.

    Returns status of RAGflow connection and initialized KBs.
    """
    try:
        config = RAGflowConfig.from_env()
        client = await get_client()
        health = await client.health_check()

        # Get KB status
        kb_status = {}
        try:
            manager = await get_manager()
            kb_status = {kb: "initialized" for kb in manager.kb_ids.keys()}
        except Exception:
            pass

        return HealthResponse(
            status=health.get("status", "unknown"),
            ragflow_available=health.get("status") == "healthy",
            ragflow_url=config.base_url,
            knowledge_bases=kb_status,
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="error",
            ragflow_available=False,
            ragflow_url=os.getenv("RAGFLOW_BASE_URL", "http://localhost"),
            knowledge_bases={},
            timestamp=datetime.now().isoformat(),
        )


@router.get("/status")
async def get_status():
    """
    Get detailed status of RAGflow integration.

    Returns KB stats, document counts, and system info.
    """
    try:
        manager = await get_manager()
        stats = await manager.get_kb_stats()

        return {
            "status": "operational",
            "knowledge_bases": stats,
            "available_kbs": list(BD_KNOWLEDGE_BASES.keys()),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Knowledge Base Management
# =============================================================================


@router.post("/kb/initialize", response_model=InitializeResponse)
async def initialize_knowledge_bases(request: InitializeRequest):
    """
    Initialize all BD knowledge bases.

    Creates the following KBs if they don't exist:
    - bd_playbooks: BD strategy documents
    - federal_programs: Contract and program data
    - rfp_library: RFPs and solicitations
    - past_performance: Case studies and CPARs
    - humint_notes: Call notes and intel
    - contacts: Contact profiles
    """
    try:
        manager = await get_manager()
        kb_ids = await manager.initialize_knowledge_bases()

        return InitializeResponse(
            success=True,
            knowledge_bases=kb_ids,
            message=f"Initialized {len(kb_ids)} knowledge bases",
        )
    except Exception as e:
        logger.error(f"KB initialization failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb/list")
async def list_knowledge_bases():
    """List all available BD knowledge bases with stats."""
    try:
        manager = await get_manager()
        stats = await manager.get_kb_stats()

        return {
            "knowledge_bases": stats,
            "definitions": {
                kb: {
                    "description": config.description,
                    "chunk_method": config.chunk_method.value,
                }
                for kb, config in BD_KNOWLEDGE_BASES.items()
            },
        }
    except Exception as e:
        logger.error(f"Failed to list KBs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Document Upload
# =============================================================================


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    kb_name: str = Form(...),
    chunk_method: Optional[str] = Form(None),
    preprocess: bool = Form(True),
):
    """
    Upload a document to the appropriate knowledge base.

    Supports: PDF, DOCX, CSV, XLSX, MD, TXT, HTML

    The document will be preprocessed for optimal chunking
    unless preprocess=false is specified.
    """
    try:
        manager = await get_manager()

        if kb_name not in manager.kb_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown KB: {kb_name}. Available: {list(manager.kb_ids.keys())}",
            )

        # Save uploaded file temporarily
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        temp_dir = os.path.join(base_dir, "data", "temp_uploads")
        os.makedirs(temp_dir, exist_ok=True)

        temp_path = os.path.join(temp_dir, file.filename)

        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Preprocess if requested
        upload_path = temp_path
        if preprocess:
            preprocessor = get_preprocessor()

            # Route to appropriate preprocessor
            ext = os.path.splitext(file.filename)[1].lower()
            if ext == ".docx" and kb_name == "bd_playbooks":
                result = await preprocessor.preprocess_playbook(temp_path)
                upload_path = result.processed_path
            elif ext == ".csv" and kb_name == "contacts":
                result = await preprocessor.preprocess_contact_csv(temp_path)
                upload_path = result.processed_path
            elif ext == ".pdf" and kb_name == "rfp_library":
                result = await preprocessor.preprocess_rfp(temp_path)
                upload_path = result.processed_path

        # Upload to RAGflow
        doc_id = await manager.upload_to_kb(kb_name, upload_path)

        # Cleanup temp file
        try:
            os.remove(temp_path)
            if upload_path != temp_path:
                os.remove(upload_path)
        except Exception:
            pass

        return UploadResponse(
            success=True,
            doc_id=doc_id,
            kb_name=kb_name,
            file_name=file.filename,
            message="Document uploaded successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def ingest_project_files(
    project_path: str = Form(...), auto_categorize: bool = Form(True)
):
    """
    Ingest all documents from a project folder.

    Scans the folder, categorizes files by type/name pattern,
    and uploads to appropriate knowledge bases.
    """
    try:
        manager = await get_manager()
        result = await manager.ingest_project_files(project_path, auto_categorize)

        return {
            "success": True,
            "summary": result,
            "message": f"Ingested {result['total_files']} files",
        }
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Query Endpoints
# =============================================================================


@router.post("/query", response_model=QueryResponse)
async def query_knowledge(request: QueryRequest):
    """
    Query BD knowledge bases with smart routing.

    Context options:
    - program: Federal programs and contracts
    - contact: Contact profiles and org charts
    - rfp: RFPs and solicitations
    - past_performance: Case studies and CPARs
    - humint: Call notes and intelligence
    - general: Search all knowledge bases
    """
    try:
        manager = await get_manager()
        result = await manager.query_bd_intelligence(
            question=request.question, context=request.context, top_k=request.top_k
        )

        return QueryResponse(
            question=request.question,
            answer=result.answer,
            chunks=result.chunks,
            citations=result.citations,
            query_time_ms=result.query_time_ms,
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/program/{program_name}")
async def get_program_intelligence(program_name: str, include_related: bool = True):
    """
    Get comprehensive intelligence about a federal program.

    Aggregates:
    - Contract details
    - Related RFPs
    - Past performance
    - Key contacts
    - HUMINT notes
    """
    try:
        manager = await get_manager()
        intel = await manager.get_program_intelligence(
            program_name=program_name, include_related=include_related
        )

        return intel.to_dict()
    except Exception as e:
        logger.error(f"Program intel failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contact/{contact_name}/context")
async def get_contact_context(contact_name: str):
    """
    Get everything we know about a contact.

    Returns profile, program associations, interactions, and related contacts.
    """
    try:
        manager = await get_manager()
        context = await manager.get_contact_context(contact_name)

        return context.to_dict()
    except Exception as e:
        logger.error(f"Contact context failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contact/{contact_name}/prep")
async def generate_call_prep(contact_name: str, request: ContactPrepRequest):
    """
    Generate a call preparation brief for a contact.

    Returns:
    - Contact background
    - Program pain points
    - PTS capability alignment
    - Suggested talking points
    - Questions to ask
    """
    try:
        manager = await get_manager()
        prep = await manager.generate_call_prep(
            contact_name=contact_name, program_context=request.program_context
        )

        return prep.to_dict()
    except Exception as e:
        logger.error(f"Call prep generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Notion Sync
# =============================================================================


@router.post("/sync/notion")
async def sync_notion_to_ragflow(request: SyncNotionRequest):
    """
    Sync a Notion database to RAGflow.

    Exports Notion DB pages and uploads to specified KB.
    """
    # This would integrate with Notion API to export pages
    # For now, return not implemented
    raise HTTPException(
        status_code=501,
        detail="Notion sync not yet implemented. Use /upload endpoint with exported files.",
    )


# =============================================================================
# GraphRAG Operations
# =============================================================================


@router.post("/graph/build", response_model=GraphBuildResponse)
async def build_knowledge_graph():
    """
    Build knowledge graph across BD knowledge bases.

    Enables relationship-aware queries like:
    - "Show programs related to GDIT with DCGS experience"
    - "What companies work with Leidos on ISR?"
    """
    try:
        manager = await get_manager()
        tasks = await manager.build_program_knowledge_graph()

        return GraphBuildResponse(
            success=True, tasks=tasks, message="Knowledge graph build started"
        )
    except Exception as e:
        logger.error(f"Graph build failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/status")
async def get_graph_status():
    """
    Check knowledge graph build status.

    Returns progress and completion status for each KB.
    """
    try:
        manager = await get_manager()
        status = await manager.get_graph_status()

        return {"status": status, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Graph status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Hybrid Search
# =============================================================================


@router.post("/search/hybrid")
async def hybrid_search(
    question: str = Form(...), keyword_weight: float = Form(0.3), top_k: int = Form(5)
):
    """
    Perform hybrid vector + BM25 keyword search.

    Combines semantic understanding with exact keyword matching
    for better results on technical queries.
    """
    try:
        client = await get_client()
        manager = await get_manager()

        # Get all KB IDs
        kb_ids = list(manager.kb_ids.values())

        result = await client.hybrid_search(
            kb_ids=kb_ids, question=question, keyword_weight=keyword_weight, top_k=top_k
        )

        return {
            "question": question,
            "chunks": result.chunks,
            "query_time_ms": result.query_time_ms,
            "search_type": "hybrid",
            "keyword_weight": keyword_weight,
        }
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Dify-Compatible Endpoints
# =============================================================================


@router.post("/dify/knowledge/search")
async def dify_knowledge_search(query: str = Form(...), top_k: int = Form(5)):
    """
    Dify-compatible knowledge search endpoint.

    Returns results in Dify external knowledge format.
    """
    try:
        manager = await get_manager()
        result = await manager.query_bd_intelligence(
            question=query, context="general", top_k=top_k
        )

        # Format for Dify
        return {
            "records": [
                {
                    "content": chunk.get("text", ""),
                    "score": chunk.get("score", 0.0),
                    "title": chunk.get("source_doc", ""),
                    "metadata": {
                        "source": chunk.get("source_doc"),
                        "page": chunk.get("page_num"),
                    },
                }
                for chunk in result.chunks
            ]
        }
    except Exception as e:
        logger.error(f"Dify search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dify/knowledge/rag")
async def dify_rag_query(query: str = Form(...), top_k: int = Form(5)):
    """
    Dify-compatible RAG query endpoint.

    Returns answer with citations in Dify format.
    """
    try:
        manager = await get_manager()
        result = await manager.query_bd_intelligence(
            question=query, context="general", top_k=top_k
        )

        return {
            "answer": result.answer or "",
            "citations": result.citations,
            "context": [
                {
                    "content": chunk.get("text", ""),
                    "source": chunk.get("source_doc", ""),
                }
                for chunk in result.chunks
            ],
        }
    except Exception as e:
        logger.error(f"Dify RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
