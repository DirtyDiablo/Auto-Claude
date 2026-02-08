"""
BD Knowledge API - Enhanced FastAPI server for BD Intelligence Hub.
50+ endpoints for comprehensive BD operations.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

try:
    from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("FastAPI not installed. Install with: pip install fastapi uvicorn")
    sys.exit(1)

# Import existing modules
from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore, SearchResult
from qdrant_client.models import Filter, FieldCondition, MatchValue
from Engine8_Knowledge.scripts.rag_engine import BDRAGEngine, RAGResponse
from Engine8_Knowledge.scripts.indexer import BDIndexer

# Import new enhanced modules
from Engine8_Knowledge.scripts.memory_layer import get_memory
from Engine8_Knowledge.scripts.lightrag_engine import get_knowledge_graph
from Engine8_Knowledge.scripts.hybrid_retriever import get_hybrid_retriever
from Engine8_Knowledge.scripts.query_router import QueryRouter, QueryType
from Engine8_Knowledge.scripts.pageindex_engine import get_pageindex
from Engine8_Knowledge.scripts.redis_cache import get_cache

# Import agents
from Engine8_Knowledge.agents.program_intel_agent import ProgramIntelAgent
from Engine8_Knowledge.agents.company_research_agent import CompanyResearchAgent
from Engine8_Knowledge.agents.contact_finder_agent import ContactFinderAgent
from Engine8_Knowledge.agents.bd_strategy_agent import BDStrategyAgent
from Engine8_Knowledge.agents.crewai_orchestrator import get_orchestrator

# Configure structlog early so imports can use logger
try:
    from config.logging_config import setup_logging, get_logger as _get_structlog, generate_request_id, request_id_var
    setup_logging(log_level="INFO")
    logger = _get_structlog("BDKnowledgeAPI")
    STRUCTLOG_AVAILABLE = True
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('BDKnowledgeAPI')
    STRUCTLOG_AVAILABLE = False

# Import new module routers
try:
    from Engine8_Knowledge.processors.routes import router as document_router
    DOCUMENT_PROCESSOR_AVAILABLE = True
except ImportError as e:
    DOCUMENT_PROCESSOR_AVAILABLE = False
    logger.warning(f"Document processor not available: {e}")

try:
    from Engine8_Knowledge.retrieval.routes import router as pageindex_router
    from Engine8_Knowledge.retrieval.ultra_rag_routes import router as ultrarag_router
    RETRIEVAL_ROUTERS_AVAILABLE = True
except ImportError as e:
    RETRIEVAL_ROUTERS_AVAILABLE = False
    logger.warning(f"Retrieval routers not available: {e}")

try:
    from Engine8_Knowledge.bd_lightrag.routes import router as lightrag_router
    LIGHTRAG_AVAILABLE = True
except ImportError as e:
    LIGHTRAG_AVAILABLE = False
    logger.warning(f"LightRAG router not available: {e}")

try:
    from streaming.streaming_api import router as streaming_router, include_streaming_router
    STREAMING_AVAILABLE = True
except ImportError as e:
    STREAMING_AVAILABLE = False
    logger.warning(f"Streaming router not available: {e}")

try:
    from memory.routes import router as memory_router
    MEMORY_AVAILABLE = True
except ImportError as e:
    MEMORY_AVAILABLE = False
    logger.warning(f"Memory router not available: {e}")

try:
    from dify_integration.dify_qdrant_bridge import create_dify_knowledge_router
    from dify_integration.dify_crewai_bridge import create_dify_agents_router
    from dify_integration.dify_n8n_bridge import create_dify_n8n_router
    DIFY_INTEGRATION_AVAILABLE = True
except ImportError as e:
    DIFY_INTEGRATION_AVAILABLE = False
    logger.warning(f"Dify integration not available: {e}")

try:
    from Engine8_Knowledge.ragflow.routes import router as ragflow_router
    RAGFLOW_AVAILABLE = True
except ImportError as e:
    RAGFLOW_AVAILABLE = False
    logger.warning(f"RAGflow integration not available: {e}")

# Import unified API endpoints
try:
    from api.unified_endpoints import router as unified_router
    UNIFIED_API_AVAILABLE = True
except ImportError as e:
    UNIFIED_API_AVAILABLE = False
    logger.warning(f"Unified API endpoints not available: {e}")

# Logger already configured above

# =========================================
# CONFIGURATION
# =========================================

API_HOST = os.getenv('KNOWLEDGE_API_HOST', '127.0.0.1')
API_PORT = int(os.getenv('KNOWLEDGE_API_PORT', '8100'))

# =========================================
# PYDANTIC MODELS
# =========================================

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    collection: Optional[str] = Field(None, description="Collection to search")
    limit: int = Field(10, ge=1, le=50, description="Max results")
    score_threshold: float = Field(0.3, ge=0.0, le=1.0, description="Min relevance score")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter conditions")
    rerank: bool = Field(False, description="Apply cross-encoder reranking")


class AskRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    collection: Optional[str] = Field(None, description="Collection to search")
    limit: int = Field(5, ge=1, le=20, description="Max sources")
    include_sources: bool = Field(True, description="Include source citations")


class SimilarRequest(BaseModel):
    item_id: str = Field(..., description="ID of source item")
    collection: str = Field(..., description="Collection containing the item")
    limit: int = Field(10, ge=1, le=50, description="Max similar items")


class SearchResultModel(BaseModel):
    id: str
    score: float
    payload: Dict[str, Any]
    collection: str


class SearchResponse(BaseModel):
    query: str
    collection: Optional[str]
    results: List[SearchResultModel]
    count: int
    timestamp: str


class AskResponse(BaseModel):
    answer: str
    sources: List[SearchResultModel]
    query: str
    confidence: float
    collection_searched: Optional[str]
    timestamp: str


class StatsResponse(BaseModel):
    collections: Dict[str, Dict[str, Any]]
    total_vectors: int
    timestamp: str


class IndexResponse(BaseModel):
    success: bool
    message: str
    indexed: int
    errors: int
    duration_seconds: float


# New models for enhanced API
class MemoryInput(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None


class InsightInput(BaseModel):
    insight_type: str
    insight: str
    source: str = "user"
    confidence: float = 0.8


class DocumentInput(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None


class ProgramInput(BaseModel):
    name: str
    description: str = ""
    agency: str = ""
    primes: List[str] = []
    value: str = ""
    clearance: str = ""
    technologies: List[str] = []


class CompanyInput(BaseModel):
    name: str
    type: str = ""
    capabilities: List[str] = []
    programs: List[str] = []
    partners: List[str] = []
    locations: List[str] = []


class ContactInput(BaseModel):
    name: str
    company: str = ""
    title: str = ""
    programs: List[str] = []
    clearance: str = ""


class JobInput(BaseModel):
    title: str
    company: str
    location: str = ""
    clearance: str = ""
    description: str = ""


# =========================================
# APPLICATION SETUP
# =========================================

# Global instances
store: Optional[BDKnowledgeStore] = None
rag_engine: Optional[BDRAGEngine] = None
indexer: Optional[BDIndexer] = None
memory = None
graph = None
retriever = None
router = None
pageindex = None
cache = None
program_agent = None
company_agent = None
contact_agent = None
strategy_agent = None
orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global store, rag_engine, indexer, memory, graph, retriever, router
    global pageindex, cache, program_agent, company_agent, contact_agent
    global strategy_agent, orchestrator

    logger.info("Initializing BD Intelligence Hub API...")

    # Initialize existing components
    # Use Qdrant server if URL is set, otherwise use local storage
    qdrant_url = os.getenv('QDRANT_URL')
    store = BDKnowledgeStore(url=qdrant_url)
    store.initialize_collections()
    rag_engine = BDRAGEngine(vector_store=store)
    indexer = BDIndexer(store=store)

    # Initialize new components (catch chromadb/mem0 Rust panic - PanicException is BaseException)
    try:
        memory = get_memory()
    except BaseException as e:
        logger.warning(f"Memory layer init failed (continuing without): {e}")
        memory = None
    graph = get_knowledge_graph()
    retriever = get_hybrid_retriever()
    router = QueryRouter()
    pageindex = get_pageindex()
    cache = get_cache()

    # Initialize agents
    program_agent = ProgramIntelAgent()
    company_agent = CompanyResearchAgent()
    contact_agent = ContactFinderAgent()
    strategy_agent = BDStrategyAgent()
    orchestrator = get_orchestrator()

    logger.info("BD Intelligence Hub API initialized with 50+ endpoints")

    yield

    logger.info("Shutting down BD Intelligence Hub API")


app = FastAPI(
    title="BD Intelligence Hub API",
    description="Comprehensive API for BD Intelligence operations: search, memory, graph, agents, and more",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Structlog request-ID middleware
if STRUCTLOG_AVAILABLE:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class RequestIdMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            rid = generate_request_id()
            request_id_var.set(rid)
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response

    app.add_middleware(RequestIdMiddleware)

# Include module routers
if DOCUMENT_PROCESSOR_AVAILABLE:
    app.include_router(document_router)
    logger.info("Document processor routes enabled: /documents/*")

if RETRIEVAL_ROUTERS_AVAILABLE:
    app.include_router(pageindex_router)
    app.include_router(ultrarag_router)
    logger.info("Retrieval routes enabled: /pageindex/*, /ultrarag/*")

if LIGHTRAG_AVAILABLE:
    app.include_router(lightrag_router)
    logger.info("LightRAG routes enabled: /lightrag/*")

if STREAMING_AVAILABLE:
    app.include_router(streaming_router)
    logger.info("Streaming routes enabled: /streaming/*")

# Supermemory router disabled - using local Mem0-based memory endpoints instead
# The Supermemory API (api.supermemory.ai) returns 404 errors
# if MEMORY_AVAILABLE:
#     app.include_router(memory_router)
#     logger.info("Memory routes enabled: /memory/*")
logger.info("Using local Mem0 memory endpoints (Supermemory disabled)")

if DIFY_INTEGRATION_AVAILABLE:
    app.include_router(create_dify_knowledge_router(), prefix="/dify")
    app.include_router(create_dify_agents_router(), prefix="/dify")
    app.include_router(create_dify_n8n_router(), prefix="/dify")
    logger.info("Dify integration routes enabled: /dify/*")

if RAGFLOW_AVAILABLE:
    app.include_router(ragflow_router)
    logger.info("RAGflow integration routes enabled: /ragflow/*")

if UNIFIED_API_AVAILABLE:
    app.include_router(unified_router)
    logger.info("Unified API v2 routes enabled: /api/v2/*")

try:
    from Engine8_Knowledge.api_routers.hybrid_endpoints import router as hybrid_router
    app.include_router(hybrid_router)
    logger.info("Hybrid search routes enabled: /search/hybrid/v2, /collections/*, /sync/*, /index/bullhorn-notes")
except ImportError as e:
    logger.warning(f"Hybrid endpoints not available: {e}")

try:
    from Engine8_Knowledge.agents.api_routes import router as crewai_router
    app.include_router(crewai_router)
    logger.info("CrewAI agent routes enabled: /agents/*")
except ImportError as e:
    logger.warning(f"CrewAI agent routes not available: {e}")


# =========================================
# HEALTH & STATUS ENDPOINTS
# =========================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/stats")
async def get_stats():
    """Get comprehensive system statistics."""
    stats = {
        "qdrant": store.get_collection_stats() if store else {},
        "memory": memory.get_stats() if memory else {},
        "graph": graph.get_stats() if graph else {},
        "pageindex": pageindex.get_stats() if pageindex else {},
        "cache": cache.get_stats() if cache else {},
        "timestamp": datetime.now().isoformat()
    }
    return stats


# =========================================
# DASHBOARD ENDPOINTS
# =========================================

class FilterRequest(BaseModel):
    query: Optional[str] = Field(None, description="Optional text search query")
    limit: int = Field(20, ge=1, le=200, description="Max results")
    offset: int = Field(0, ge=0, description="Pagination offset")
    program: Optional[str] = Field(None, description="Filter by program name")
    prime: Optional[str] = Field(None, description="Filter by prime contractor")
    agency: Optional[str] = Field(None, description="Filter by agency")
    clearance: Optional[str] = Field(None, description="Filter by clearance level")
    status: Optional[str] = Field(None, description="Filter by status")
    company: Optional[str] = Field(None, description="Filter by company")
    location: Optional[str] = Field(None, description="Filter by location")


def _build_qdrant_filter(request: FilterRequest, field_map: Dict[str, str]) -> Optional[Filter]:
    """Build Qdrant Filter from FilterRequest using a field mapping."""
    conditions = []
    for param_name, payload_field in field_map.items():
        value = getattr(request, param_name, None)
        if value:
            conditions.append(FieldCondition(
                key=payload_field,
                match=MatchValue(value=value)
            ))
    return Filter(must=conditions) if conditions else None


@app.post("/contacts/filter")
async def filter_contacts(request: FilterRequest):
    """Filter contacts by payload fields. Use query for semantic search + filters, or omit for filter-only scroll."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")

    field_map = {
        "program": "Programs",
        "prime": "Primes",
        "clearance": "Clearances",
        "status": "Status",
        "company": "Primes",
    }

    try:
        if request.query:
            filters = {}
            for param, payload_field in field_map.items():
                val = getattr(request, param, None)
                if val:
                    filters[payload_field] = val

            results = store.search(
                query=request.query,
                collection="contacts",
                limit=request.limit,
                filters=filters if filters else None,
            )
            return {
                "contacts": [{"id": r.id, "score": r.score, **r.payload} for r in results],
                "count": len(results),
                "query": request.query,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            qdrant_filter = _build_qdrant_filter(request, field_map)
            results, _next = store.client.scroll(
                collection_name="contacts",
                scroll_filter=qdrant_filter,
                limit=request.limit,
                offset=request.offset if request.offset else None,
                with_payload=True,
                with_vectors=False,
            )
            return {
                "contacts": [{"id": str(p.id), **p.payload} for p in results],
                "count": len(results),
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error(f"Filter contacts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/programs/filter")
async def filter_programs(request: FilterRequest):
    """Filter programs by payload fields. Use query for semantic search + filters, or omit for filter-only scroll."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")

    field_map = {
        "prime": '"Prime Contractor"',
        "agency": "Agency",
        "clearance": "clearance",
        "program": '"Program Name"',
    }

    try:
        if request.query:
            filters = {}
            for param, payload_field in field_map.items():
                val = getattr(request, param, None)
                if val:
                    filters[payload_field] = val

            results = store.search(
                query=request.query,
                collection="programs",
                limit=request.limit,
                filters=filters if filters else None,
            )
            return {
                "programs": [{"id": r.id, "score": r.score, **r.payload} for r in results],
                "count": len(results),
                "query": request.query,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            qdrant_filter = _build_qdrant_filter(request, field_map)
            results, _next = store.client.scroll(
                collection_name="programs",
                scroll_filter=qdrant_filter,
                limit=request.limit,
                offset=request.offset if request.offset else None,
                with_payload=True,
                with_vectors=False,
            )
            return {
                "programs": [{"id": str(p.id), **p.payload} for p in results],
                "count": len(results),
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error(f"Filter programs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/stats")
async def dashboard_stats():
    """Consolidated stats endpoint for the dashboard home page."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")

    try:
        collection_stats = store.get_collection_stats()

        total_vectors = sum(
            s.get("points_count", 0) for s in collection_stats.values() if isinstance(s, dict) and "points_count" in s
        )

        all_green = all(
            s.get("status", "").upper() == "GREEN"
            for s in collection_stats.values()
            if isinstance(s, dict) and "status" in s
        )

        return {
            "collections": collection_stats,
            "total_vectors": total_vectors,
            "total_collections": len(collection_stats),
            "all_healthy": all_green,
            "memory": memory.get_stats() if memory else {},
            "graph": graph.get_stats() if graph else {},
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# SMART QUERY ENDPOINTS
# =========================================

@app.get("/ask/smart")
async def smart_ask(
    q: str = Query(..., description="Your BD question"),
    use_cache: bool = Query(True, description="Use semantic cache")
):
    """Intelligent query that routes to optimal system(s)."""
    if use_cache and cache:
        cached = cache.get(q)
        if cached:
            # Return the cached response in the standard shape
            result_data = cached.get("result", cached)
            return {
                "answer": result_data.get("answer", ""),
                "query_type": result_data.get("query_type", "factual"),
                "systems_used": result_data.get("systems_used", []),
                "sources": result_data.get("sources", [])[:5],
                "cache_hit": True
            }

    result = await router.smart_query(q)

    logger.info("smart_query_result",
                answer_len=len(result.answer),
                sources_count=len(result.sources),
                systems=result.systems_used,
                query_type=result.query_type.value)

    response = {
        "answer": result.answer,
        "query_type": result.query_type.value,
        "systems_used": result.systems_used,
        "sources": result.sources[:5],
        "cache_hit": False
    }

    if cache:
        cache.set(q, response)

    return response


# =========================================
# COLLECTION LIST ENDPOINTS
# =========================================

@app.get("/programs")
async def list_programs(
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    """List programs from Qdrant programs collection (replaces /api/v2/programs)."""
    try:
        results, _next = store.client.scroll(
            collection_name="programs",
            limit=limit,
            offset=offset if offset else None,
            with_payload=True,
            with_vectors=False,
        )
        programs = [{"id": str(p.id), **p.payload} for p in results]
        return {"programs": programs, "total": len(programs), "offset": offset}
    except Exception as e:
        logger.error(f"List programs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/contacts/list")
async def list_contacts(
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    """List contacts from Qdrant contacts collection."""
    try:
        results, _next = store.client.scroll(
            collection_name="contacts",
            limit=limit,
            offset=offset if offset else None,
            with_payload=True,
            with_vectors=False,
        )
        contacts = [{"id": str(p.id), **p.payload} for p in results]
        return {"contacts": contacts, "total": len(contacts), "offset": offset}
    except Exception as e:
        logger.error(f"List contacts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# SEARCH ENDPOINTS
# =========================================

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Semantic search across knowledge base. Set rerank=true for cross-encoder reranking."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")

    try:
        if request.collection:
            results = store.search(
                query=request.query,
                collection=request.collection,
                limit=request.limit,
                score_threshold=request.score_threshold,
                filters=request.filters
            )
        else:
            all_results = store.search_all(
                query=request.query,
                limit_per_collection=request.limit,
                score_threshold=request.score_threshold
            )
            results = []
            for coll, items in all_results.items():
                for item in items:
                    item.collection = coll
                    results.append(item)
            results.sort(key=lambda x: x.score, reverse=True)
            results = results[:request.limit]

        # Optional cross-encoder reranking
        if request.rerank and results and retriever and getattr(retriever, 'reranker', None):
            pairs = [[request.query, r.payload.get("text", "") or str(r.payload)] for r in results]
            scores = retriever.reranker.predict(pairs)
            ranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
            results = [r for r, _ in ranked[:request.limit]]

        return SearchResponse(
            query=request.query,
            collection=request.collection,
            results=[SearchResultModel(id=r.id, score=r.score, payload=r.payload, collection=r.collection) for r in results],
            count=len(results),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
async def search_get(
    q: str = Query(..., description="Search query"),
    collection: Optional[str] = Query(None, description="Collection to search"),
    limit: int = Query(10, ge=1, le=50, description="Max results")
):
    """GET endpoint for search."""
    request = SearchRequest(query=q, collection=collection, limit=limit)
    return await search(request)


@app.get("/search/semantic")
async def semantic_search(
    q: str = Query(..., description="Search query"),
    collection: str = Query("bd_knowledge", description="Collection"),
    limit: int = Query(10, description="Max results")
):
    """Semantic-only search."""
    results = retriever._semantic_search(q, collection, limit)
    return {"results": [{"id": r.id, "text": r.text, "score": r.score} for r in results]}


@app.get("/search/keyword")
async def keyword_search(
    q: str = Query(..., description="Search query"),
    collection: str = Query("bd_knowledge", description="Collection"),
    limit: int = Query(10, description="Max results")
):
    """BM25 keyword search."""
    results = retriever._keyword_search(q, collection, limit)
    return {"results": [{"id": r.id, "text": r.text, "score": r.score} for r in results]}


@app.get("/search/hybrid")
async def hybrid_search(
    q: str = Query(..., description="Search query"),
    collection: str = Query("bd_knowledge", description="Collection"),
    limit: int = Query(10, description="Max results"),
    use_rerank: bool = Query(True, description="Apply reranking")
):
    """Hybrid semantic + keyword search with reranking."""
    results = retriever.search(q, collection, limit, True, use_rerank)
    return {"results": [{"id": r.id, "text": r.text, "score": r.score, "source": r.source} for r in results]}


# =========================================
# RAG ENDPOINTS
# =========================================

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """Ask a natural language question (RAG)."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")

    try:
        response = rag_engine.ask(
            question=request.question,
            collection=request.collection,
            limit=request.limit
        )

        sources = []
        if request.include_sources:
            sources = [SearchResultModel(id=s.id, score=s.score, payload=s.payload, collection=s.collection) for s in response.sources]

        return AskResponse(
            answer=response.answer,
            sources=sources,
            query=response.query,
            confidence=response.confidence,
            collection_searched=response.collection_searched,
            timestamp=response.timestamp
        )
    except Exception as e:
        logger.error(f"RAG error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ask")
async def ask_get(
    q: str = Query(..., description="Question to ask"),
    collection: Optional[str] = Query(None, description="Collection to search"),
    limit: int = Query(5, ge=1, le=20, description="Max sources")
):
    """GET endpoint for ask."""
    request = AskRequest(question=q, collection=collection, limit=limit)
    return await ask_question(request)


# =========================================
# GRAPH ENDPOINTS
# =========================================

@app.get("/graph/query")
async def query_graph(
    q: str = Query(..., description="Query"),
    mode: str = Query("hybrid", description="Query mode: naive, local, global, hybrid")
):
    """Query knowledge graph."""
    result = await graph.query(q, mode)
    return {"query": q, "mode": mode, "result": result}


@app.get("/graph/relationships")
async def get_relationships(entity: str = Query(..., description="Entity name")):
    """Get relationships for entity."""
    result = await graph.find_relationships(entity)
    return result


@app.get("/graph/network")
async def analyze_network(company: str = Query(..., description="Company name")):
    """Analyze company network."""
    result = await graph.analyze_network(company)
    return {"company": company, "analysis": result}


# =========================================
# BD KNOWLEDGE GRAPH ENDPOINTS
# =========================================

# Import BD Knowledge Graph
try:
    from Engine8_Knowledge.graph.bd_knowledge_graph import (
        get_knowledge_graph as get_bd_graph,
        BDKnowledgeGraph,
        ENTITY_TYPES,
        RELATIONSHIP_TYPES
    )
    BD_GRAPH_AVAILABLE = True
except ImportError as e:
    BD_GRAPH_AVAILABLE = False
    logger.warning(f"BD Knowledge Graph not available: {e}")

# Initialize BD Graph (lazy)
_bd_graph = None

def get_bd_knowledge_graph():
    global _bd_graph
    if _bd_graph is None and BD_GRAPH_AVAILABLE:
        _bd_graph = get_bd_graph()
    return _bd_graph


@app.get("/bdgraph/program/{program_name}")
async def bdgraph_program_ecosystem(program_name: str):
    """
    Get full ecosystem for a program.
    Returns primes, subs, contacts, jobs, locations, required skills.
    """
    bg = get_bd_knowledge_graph()
    if not bg:
        raise HTTPException(status_code=503, detail="BD Knowledge Graph not available")

    result = bg.get_program_ecosystem(program_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@app.get("/bdgraph/contact/{contact_name}")
async def bdgraph_contact_network(contact_name: str):
    """
    Get contact's professional network.
    Returns employer, programs, manages, managed_by, connections.
    """
    bg = get_bd_knowledge_graph()
    if not bg:
        raise HTTPException(status_code=503, detail="BD Knowledge Graph not available")

    result = bg.get_contact_network(contact_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@app.get("/bdgraph/teaming/{from_contractor}/{to_program}")
async def bdgraph_teaming_path(from_contractor: str, to_program: str, max_depth: int = 4):
    """
    Find teaming path from a contractor to a program.
    Uses BFS to find shortest relationship path.
    """
    bg = get_bd_knowledge_graph()
    if not bg:
        raise HTTPException(status_code=503, detail="BD Knowledge Graph not available")

    path = bg.find_teaming_path(from_contractor, to_program, max_depth)
    return {"from": from_contractor, "to": to_program, "path": path}


@app.get("/bdgraph/query")
async def bdgraph_query(q: str = Query(..., description="Natural language query")):
    """
    Natural language query against the BD knowledge graph.
    Examples:
    - "Who works on AF DCGS?"
    - "What programs does GDIT prime on?"
    - "Who is the prime on DCGS-A?"
    """
    bg = get_bd_knowledge_graph()
    if not bg:
        raise HTTPException(status_code=503, detail="BD Knowledge Graph not available")

    results = bg.query(q)
    return {"query": q, "results": results}


@app.get("/bdgraph/search")
async def bdgraph_search(
    q: str = Query(..., description="Search query"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(20, description="Max results")
):
    """Search entities in the BD knowledge graph."""
    bg = get_bd_knowledge_graph()
    if not bg:
        raise HTTPException(status_code=503, detail="BD Knowledge Graph not available")

    results = bg.search_entities(q, entity_type, limit)
    return {"query": q, "entity_type": entity_type, "results": [e.to_dict() for e in results]}


@app.post("/bdgraph/entity")
async def bdgraph_add_entity(
    entity_type: str = Query(..., description=f"Entity type: {list(ENTITY_TYPES.keys()) if BD_GRAPH_AVAILABLE else []}"),
    name: str = Query(..., description="Entity name"),
    properties: Optional[str] = Query(None, description="JSON properties")
):
    """Add an entity to the BD knowledge graph."""
    bg = get_bd_knowledge_graph()
    if not bg:
        raise HTTPException(status_code=503, detail="BD Knowledge Graph not available")

    props = json.loads(properties) if properties else {}
    entity = bg.add_entity(entity_type, name, props)
    return {"success": True, "entity": entity.to_dict()}


@app.post("/bdgraph/relationship")
async def bdgraph_add_relationship(
    from_entity: str = Query(..., description="Source entity (ID or name)"),
    rel_type: str = Query(..., description=f"Relationship type"),
    to_entity: str = Query(..., description="Target entity (ID or name)"),
    confidence: float = Query(1.0, description="Confidence score 0-1")
):
    """Add a relationship between entities."""
    bg = get_bd_knowledge_graph()
    if not bg:
        raise HTTPException(status_code=503, detail="BD Knowledge Graph not available")

    try:
        rel = bg.add_relationship(from_entity, rel_type, to_entity, confidence=confidence)
        return {"success": True, "relationship": rel.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/bdgraph/stats")
async def bdgraph_stats():
    """Get BD knowledge graph statistics."""
    bg = get_bd_knowledge_graph()
    if not bg:
        return {"available": False, "error": "BD Knowledge Graph not available"}

    stats = bg.get_stats()
    stats["available"] = True
    return stats


@app.post("/bdgraph/populate")
async def bdgraph_populate_from_store():
    """
    Populate the BD knowledge graph from the vector store.
    Loads programs, contacts, jobs and infers relationships.
    """
    bg = get_bd_knowledge_graph()
    if not bg:
        raise HTTPException(status_code=503, detail="BD Knowledge Graph not available")

    if not store:
        raise HTTPException(status_code=503, detail="Vector store not initialized")

    bg.populate_from_vector_store(store)
    return {"success": True, "stats": bg.get_stats()}


@app.get("/bdgraph/types")
async def bdgraph_list_types():
    """List available entity and relationship types."""
    if not BD_GRAPH_AVAILABLE:
        raise HTTPException(status_code=503, detail="BD Knowledge Graph not available")

    return {
        "entity_types": ENTITY_TYPES,
        "relationship_types": {k: {"from": v[0], "to": v[1]} for k, v in RELATIONSHIP_TYPES.items()}
    }


# =========================================
# MEMORY ENDPOINTS
# =========================================

@app.post("/memory/add")
async def add_memory(data: MemoryInput):
    """Add memory."""
    result = memory.add_interaction(data.content, data.metadata)
    return {"success": True, "result": result}


@app.post("/memory/entity")
async def add_entity_fact(
    entity_name: str = Query(...),
    entity_type: str = Query(...),
    fact: str = Query(...)
):
    """Add entity fact."""
    result = memory.add_entity_fact(entity_name, entity_type, fact)
    return {"success": True, "result": result}


@app.post("/memory/insight")
async def add_insight(data: InsightInput):
    """Add BD insight."""
    result = memory.add_bd_insight(data.insight_type, data.insight, data.source, data.confidence)
    return {"success": True, "result": result}


@app.get("/memory/search")
async def search_memory(q: str = Query(...), limit: int = Query(10)):
    """Search memories."""
    results = memory.get_context(q, limit)
    return {"results": results}


@app.get("/memory/entity/{entity_name}")
async def get_entity_facts(entity_name: str, limit: int = Query(20)):
    """Get facts about entity."""
    results = memory.get_entity_facts(entity_name, limit)
    return {"entity": entity_name, "facts": results}


@app.get("/memory/insights")
async def get_insights(insight_type: Optional[str] = Query(None), limit: int = Query(10)):
    """Get BD insights."""
    results = memory.get_recent_insights(insight_type, limit)
    return {"insights": results}


@app.get("/memory/stats")
async def memory_stats():
    """Get memory statistics."""
    return memory.get_stats()


@app.get("/memory/contact/{contact_name}")
async def get_contact_context(contact_name: str):
    """Get full context for a contact (interactions + memories)."""
    try:
        from Engine8_Knowledge.scripts.memory_system import get_memory_system
        system = get_memory_system()
        return system.get_contact_context(contact_name)
    except Exception as e:
        # Fallback to existing memory layer
        return {
            "interactions": [],
            "memories": memory.get_context(f"contact {contact_name}", 10)
        }


@app.get("/memory/program/{program_name}")
async def get_program_context(program_name: str):
    """Get full context for a program (insights + memories)."""
    try:
        from Engine8_Knowledge.scripts.memory_system import get_memory_system
        system = get_memory_system()
        return system.get_program_context(program_name)
    except Exception as e:
        # Fallback to existing memory layer
        return {
            "insights": [],
            "memories": memory.get_context(f"program {program_name}", 10)
        }


# =========================================
# RAG ROUTER ENDPOINTS
# =========================================

@app.get("/rag/router")
async def rag_router_query(
    q: str = Query(..., description="Query"),
    strategy: str = Query("auto", description="Strategy: auto, lightrag, bm25, hybrid"),
    limit: int = Query(10, description="Max results"),
    collection: str = Query("bd_knowledge", description="Collection")
):
    """RAG query with strategy selection."""
    try:
        from Engine8_Knowledge.scripts.rag_router import get_rag_router, RetrievalStrategy
        rag_router = get_rag_router()
        result = await rag_router.retrieve(q, RetrievalStrategy(strategy), limit, collection)
        return {
            "strategy": result.strategy,
            "query": result.query,
            "results": result.results,
            "count": result.count,
            "strategies_used": result.strategies_used
        }
    except Exception as e:
        logger.error(f"RAG router error: {e}")
        return {"error": str(e), "query": q}


@app.get("/rag/analyze")
async def analyze_query_strategy(q: str = Query(..., description="Query to analyze")):
    """Analyze query to recommend optimal strategy."""
    try:
        from Engine8_Knowledge.scripts.rag_router import get_rag_router
        rag_router = get_rag_router()
        strategy = rag_router.analyze_query(q)
        return {
            "query": q,
            "recommended_strategy": strategy.value,
            "available_strategies": rag_router.get_available_strategies()
        }
    except Exception as e:
        return {"error": str(e), "query": q}


# =========================================
# INGEST ENDPOINTS
# =========================================

@app.post("/ingest/document")
def ingest_document(data: DocumentInput):
    """Ingest document to Qdrant documents collection via OpenAI embeddings."""
    try:
        doc = {
            "content": data.text,
            "indexed_at": datetime.now().isoformat(),
            "_source": "api_ingest",
        }
        if data.metadata:
            doc.update(data.metadata)
        indexed, errors = store.index_documents([doc])
        return {"success": True, "indexed": indexed, "errors": errors}
    except Exception as e:
        logger.error(f"Ingest document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/program")
def ingest_program(data: ProgramInput):
    """Ingest program to Qdrant programs collection via OpenAI embeddings."""
    try:
        program_dict = {
            "Program Name": data.name,
            "description": data.description,
            "Agency": data.agency,
            "Prime Contractor": ", ".join(data.primes) if data.primes else "",
            "Contract Value": data.value,
            "clearance": data.clearance,
            "technologies": ", ".join(data.technologies) if data.technologies else "",
            "indexed_at": datetime.now().isoformat(),
            "_source": "api_ingest",
        }
        indexed, errors = store.index_programs([program_dict])
        return {"success": True, "program": data.name, "indexed": indexed, "errors": errors}
    except Exception as e:
        logger.error(f"Ingest program error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/programs/batch")
def ingest_programs_batch(programs: List[ProgramInput]):
    """Batch ingest programs to Qdrant programs collection."""
    try:
        program_dicts = []
        for p in programs:
            program_dicts.append({
                "Program Name": p.name,
                "description": p.description,
                "Agency": p.agency,
                "Prime Contractor": ", ".join(p.primes) if p.primes else "",
                "Contract Value": p.value,
                "clearance": p.clearance,
                "technologies": ", ".join(p.technologies) if p.technologies else "",
                "indexed_at": datetime.now().isoformat(),
                "_source": "api_ingest_batch",
            })
        indexed, errors = store.index_programs(program_dicts)
        return {"success": True, "inserted": indexed, "updated": 0, "errors": errors, "total_submitted": len(programs)}
    except Exception as e:
        logger.error(f"Batch ingest programs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/company")
def ingest_company(data: CompanyInput):
    """Ingest company to Qdrant documents collection via OpenAI embeddings."""
    try:
        doc = {
            "content": f"COMPANY: {data.name} | Type: {data.type} | Capabilities: {', '.join(data.capabilities)} | Programs: {', '.join(data.programs)}",
            "name": data.name,
            "type": data.type,
            "capabilities": ", ".join(data.capabilities),
            "programs": ", ".join(data.programs),
            "partners": ", ".join(data.partners),
            "locations": ", ".join(data.locations),
            "indexed_at": datetime.now().isoformat(),
            "_source": "api_ingest",
        }
        indexed, errors = store.index_documents([doc])
        return {"success": True, "company": data.name, "indexed": indexed, "errors": errors}
    except Exception as e:
        logger.error(f"Ingest company error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/contact")
def ingest_contact(data: ContactInput):
    """Ingest contact to Qdrant contacts collection via OpenAI embeddings."""
    try:
        contact_dict = {
            "name": data.name,
            "company": data.company,
            "title": data.title,
            "programs": ", ".join(data.programs) if data.programs else "",
            "clearance": data.clearance,
            "indexed_at": datetime.now().isoformat(),
            "_source": "api_ingest",
        }
        indexed, errors = store.index_contacts([contact_dict])
        return {"success": True, "contact": data.name, "indexed": indexed, "errors": errors}
    except Exception as e:
        logger.error(f"Ingest contact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/contacts/batch")
def ingest_contacts_batch(contacts: List[ContactInput]):
    """Batch ingest contacts to Qdrant contacts collection."""
    try:
        contact_dicts = []
        for c in contacts:
            contact_dicts.append({
                "name": c.name,
                "company": c.company,
                "title": c.title,
                "programs": ", ".join(c.programs) if c.programs else "",
                "clearance": c.clearance,
                "indexed_at": datetime.now().isoformat(),
                "_source": "api_ingest_batch",
            })
        indexed, errors = store.index_contacts(contact_dicts)
        return {"success": True, "inserted": indexed, "updated": 0, "errors": errors, "total_submitted": len(contacts)}
    except Exception as e:
        logger.error(f"Batch ingest contacts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/jobs")
def ingest_jobs(jobs: List[JobInput]):
    """Ingest multiple jobs (for Data-Scraper)."""
    try:
        job_dicts = []
        for job in jobs:
            job_dicts.append({
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "clearance": job.clearance,
                "description": job.description[:2000] if job.description else "",
                "indexed_at": datetime.now().isoformat(),
                "_source": "api_ingest",
            })
        indexed, errors = store.index_jobs(job_dicts)
        return {"success": True, "count": indexed, "errors": errors}
    except Exception as e:
        logger.error(f"Ingest jobs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/scraper-batch")
async def ingest_scraper_batch(
    jobs_json: UploadFile = File(None, description="standardized_jobs JSON file"),
    intel_report: UploadFile = File(None, description="BD Intelligence Report .md file"),
    excel_file: UploadFile = File(None, description="BD Job Openings .xlsx file")
):
    """
    Batch ingest from Data-Scraper.
    Accepts any combination of:
    - standardized_jobs_*.json - Full job data
    - BD_Intelligence_Report_*.md - Intel report
    - BD_Job_Openings_*.xlsx - Excel workbook
    """
    results = {"success": True, "ingested": {}}

    # Process JSON jobs file
    if jobs_json:
        try:
            content = await jobs_json.read()
            jobs = json.loads(content.decode('utf-8'))
            # Convert to job dicts with all enriched fields
            job_dicts = []
            for job in jobs:
                job_dicts.append({
                    "job_id": job.get('job_id', ''),
                    "title": job.get('title', ''),
                    "company": job.get('company', ''),
                    "location": job.get('location', ''),
                    "location_normalized": job.get('location_normalized', ''),
                    "clearance": job.get('clearance_required', ''),
                    "clearance_level": job.get('clearance_level', ''),
                    "bd_priority_score": job.get('bd_priority_score', 0),
                    "bd_priority_tier": job.get('bd_priority_tier', ''),
                    "mapped_program": job.get('mapped_program', ''),
                    "program_confidence": job.get('program_confidence', 0),
                    "likely_prime": job.get('likely_prime', ''),
                    "likely_agency": job.get('likely_agency', ''),
                    "source_url": job.get('source_url', ''),
                    "date_posted": job.get('date_posted', ''),
                    "date_scraped": job.get('date_scraped', ''),
                    "description": job.get('description', '')[:2000],
                    "indexed_at": datetime.now().isoformat()
                })
            # Use vector store's index_jobs method
            indexed, errors = store.index_jobs(job_dicts)
            results["ingested"]["jobs"] = indexed
            if errors:
                results["ingested"]["job_errors"] = errors
            logger.info(f"Ingested {indexed} jobs from JSON")
            try:
                memory.add_scrape_result("jobs", f"Batch ingested {indexed} jobs", indexed)
            except Exception as me:
                logger.warning(f"Memory logging failed: {me}")
        except Exception as e:
            results["ingested"]["jobs_error"] = str(e)
            logger.error(f"Jobs JSON error: {e}")

    # Process Intel Report (.md)
    if intel_report:
        try:
            content = await intel_report.read()
            report_text = content.decode('utf-8')
            indexed, errors = store.index_documents([{
                "title": intel_report.filename,
                "type": "intel_report",
                "content": report_text[:10000],
                "indexed_at": datetime.now().isoformat()
            }])
            results["ingested"]["intel_report"] = intel_report.filename
            logger.info(f"Ingested intel report: {intel_report.filename}")
        except Exception as e:
            results["ingested"]["intel_report_error"] = str(e)
            logger.error(f"Intel report error: {e}")

    # Process Excel file (.xlsx)
    if excel_file:
        try:
            import pandas as pd
            import io
            content = await excel_file.read()
            df = pd.read_excel(io.BytesIO(content))
            # Store as document with summary
            summary = f"Excel workbook: {excel_file.filename}\n"
            summary += f"Rows: {len(df)}, Columns: {len(df.columns)}\n"
            summary += f"Columns: {', '.join(df.columns.tolist())}\n"
            indexed, errors = store.index_documents([{
                "title": excel_file.filename,
                "type": "excel_workbook",
                "content": summary,
                "row_count": len(df),
                "column_count": len(df.columns),
                "indexed_at": datetime.now().isoformat()
            }])
            results["ingested"]["excel"] = {"filename": excel_file.filename, "rows": len(df)}
            logger.info(f"Ingested Excel: {excel_file.filename} ({len(df)} rows)")
        except Exception as e:
            results["ingested"]["excel_error"] = str(e)
            logger.error(f"Excel error: {e}")

    return results


# =========================================
# AGENT ENDPOINTS
# =========================================

@app.get("/agent/program")
async def agent_program_intel(q: str = Query(..., description="Query")):
    """Program intelligence agent."""
    result = await program_agent.process(q)
    return {"agent": result.agent_name, "response": result.content, "confidence": result.confidence}


@app.get("/agent/company")
async def agent_company_research(q: str = Query(..., description="Query")):
    """Company research agent."""
    result = await company_agent.process(q)
    return {"agent": result.agent_name, "response": result.content, "confidence": result.confidence}


@app.get("/agent/contact")
async def agent_contact_finder(q: str = Query(..., description="Query")):
    """Contact finder agent."""
    result = await contact_agent.process(q)
    return {"agent": result.agent_name, "response": result.content, "confidence": result.confidence}


@app.get("/agent/strategy")
async def agent_bd_strategy(q: str = Query(..., description="Query")):
    """BD strategy agent."""
    result = await strategy_agent.process(q)
    return {"agent": result.agent_name, "response": result.content, "confidence": result.confidence}


# =========================================
# ORCHESTRATION ENDPOINTS
# =========================================

@app.get("/workflow/capture")
async def workflow_capture_strategy(opportunity: str = Query(..., description="Opportunity name")):
    """Run capture strategy workflow."""
    result = await orchestrator.capture_strategy_workflow(opportunity)
    return {
        "workflow": result.workflow,
        "success": result.success,
        "agents_used": result.agents_used,
        "output": result.final_output
    }


@app.get("/workflow/competitor")
async def workflow_competitor_analysis(company: str = Query(..., description="Company name")):
    """Run competitor analysis workflow."""
    result = await orchestrator.competitor_analysis_workflow(company)
    return {
        "workflow": result.workflow,
        "success": result.success,
        "agents_used": result.agents_used,
        "output": result.final_output
    }


@app.get("/workflow/quick")
async def workflow_quick_intel(q: str = Query(..., description="Query")):
    """Quick intelligence query."""
    result = await orchestrator.quick_intel_workflow(q)
    return {
        "workflow": result.workflow,
        "success": result.success,
        "agents_used": result.agents_used,
        "output": result.final_output
    }


# =========================================
# PAGEINDEX ENDPOINTS
# =========================================

@app.post("/pageindex/index")
async def index_for_audit(doc_id: str = Query(...), content: str = Query(...)):
    """Index document for audit trail."""
    success = pageindex.index_document(doc_id, content)
    return {"success": success, "doc_id": doc_id}


@app.get("/pageindex/query")
async def query_with_audit(q: str = Query(...), doc_ids: Optional[str] = Query(None)):
    """Query with audit trail."""
    docs = doc_ids.split(",") if doc_ids else None
    result = pageindex.query(q, docs)
    trail = pageindex.get_audit_trail(result)
    return {"answer": result.final_answer, "confidence": result.confidence, "audit_trail": trail}


@app.get("/pageindex/stats")
async def pageindex_stats():
    """Get PageIndex statistics."""
    return pageindex.get_stats()


# =========================================
# CACHE ENDPOINTS
# =========================================

@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    return cache.get_stats()


@app.delete("/cache/clear")
async def clear_cache():
    """Clear all cache."""
    count = cache.clear_all()
    return {"cleared": count}


# =========================================
# SPECIALIZED ENDPOINTS (EXISTING)
# =========================================

@app.get("/program/{program_name}")
async def get_program_intel(program_name: str):
    """Get comprehensive intelligence about a program."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    response = rag_engine.ask_about_program(program_name)
    return response.to_dict()


@app.get("/company/{company_name}")
async def get_company_intel(company_name: str):
    """Get intelligence about a company/contractor."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    response = rag_engine.ask_about_company(company_name)
    return response.to_dict()


@app.get("/contacts/at/{company_name}")
async def get_contacts_at_company(company_name: str, limit: int = 20):
    """Find contacts at a specific company."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")
    results = store.find_contacts_at_company(company_name, limit=limit)
    return {"company": company_name, "contacts": [r.to_dict() for r in results], "count": len(results)}


@app.get("/jobs/for/{program_name}")
async def get_jobs_for_program(program_name: str, limit: int = 20):
    """Find jobs associated with a program."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")
    results = store.find_jobs_for_program(program_name, limit=limit)
    return {"program": program_name, "jobs": [r.to_dict() for r in results], "count": len(results)}


# =========================================
# INDEXING ENDPOINTS
# =========================================

@app.post("/index/all", response_model=IndexResponse)
async def index_all():
    """Run full indexing of all data sources."""
    if not indexer:
        raise HTTPException(status_code=503, detail="Indexer not initialized")

    try:
        results = indexer.index_all()
        total_indexed = sum(r.indexed for r in results)
        total_errors = sum(r.errors for r in results)
        total_duration = sum(r.duration_seconds for r in results)

        return IndexResponse(
            success=total_errors == 0,
            message=f"Indexed {total_indexed} items across {len(results)} collections",
            indexed=total_indexed,
            errors=total_errors,
            duration_seconds=total_duration
        )
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index/{collection}", response_model=IndexResponse)
async def index_collection(collection: str):
    """Index a specific collection."""
    if not indexer:
        raise HTTPException(status_code=503, detail="Indexer not initialized")

    try:
        if collection == 'jobs':
            result = indexer.index_jobs()
        elif collection == 'contacts':
            result = indexer.index_contacts()
        elif collection == 'programs':
            result = indexer.index_programs()
        elif collection == 'documents':
            result = indexer.index_documents()
        elif collection == 'activities':
            result = indexer.index_activities()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown collection: {collection}")

        return IndexResponse(
            success=result.errors == 0,
            message=f"Indexed {result.indexed} items to {collection}",
            indexed=result.indexed,
            errors=result.errors,
            duration_seconds=result.duration_seconds
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# CREWAI AGENT ENDPOINTS
# =========================================

# Import CrewAI workflows
try:
    from Engine8_Knowledge.agents.workflows import (
        get_workflows,
        analyze_program as run_analyze_program,
        prepare_outreach as run_prepare_outreach,
        generate_weekly_intel as run_weekly_intel
    )
    from Engine8_Knowledge.agents.bd_agents import get_bd_agent_team, CREWAI_AVAILABLE
    CREWAI_WORKFLOWS_AVAILABLE = True
except ImportError as e:
    CREWAI_WORKFLOWS_AVAILABLE = False
    CREWAI_AVAILABLE = False
    logger.warning(f"CrewAI workflows not available: {e}")


class ProgramAnalysisRequest(BaseModel):
    program_name: str = Field(..., description="Name of the program to analyze")


class OutreachPrepRequest(BaseModel):
    contact_name: str = Field(..., description="Name of the contact")


class AgentStatusResponse(BaseModel):
    crewai_available: bool
    langchain_anthropic_available: bool
    agents_initialized: bool
    agent_count: int


@app.get("/agents/status")
async def get_agent_status():
    """Get status of CrewAI agents."""
    if not CREWAI_WORKFLOWS_AVAILABLE:
        return AgentStatusResponse(
            crewai_available=False,
            langchain_anthropic_available=False,
            agents_initialized=False,
            agent_count=0
        )

    team = get_bd_agent_team()
    return AgentStatusResponse(
        crewai_available=CREWAI_AVAILABLE,
        langchain_anthropic_available=True,  # If we got here, it's available
        agents_initialized=team.available,
        agent_count=4 if team.available else 0
    )


@app.post("/agents/analyze-program")
async def api_analyze_program(
    request: ProgramAnalysisRequest = None,
    program_name: str = Query(None, description="Program name (alternative to body)")
):
    """
    Analyze a federal program and generate a BD playbook.

    Uses 4 agents in sequence:
    1. Research Agent - Gathers program intelligence
    2. Analyst Agent - Scores the opportunity
    3. Strategy Agent - Develops approach
    4. Writer Agent - Generates playbook

    Returns a complete BD playbook with talking points and priority contacts.
    """
    if not CREWAI_WORKFLOWS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="CrewAI workflows not available. Install: pip install crewai langchain-anthropic"
        )

    # Get program name from body or query param
    name = request.program_name if request else program_name
    if not name:
        raise HTTPException(status_code=400, detail="program_name is required")

    try:
        result = await run_analyze_program(name)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

        return {
            "success": True,
            "program": name,
            "playbook": result.get("playbook"),
            "talking_points": result.get("talking_points", []),
            "opportunity_score": result.get("opportunity_score", 0),
            "priority_contacts": result.get("priority_contacts", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Program analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/prepare-outreach")
async def api_prepare_outreach(
    request: OutreachPrepRequest = None,
    contact_name: str = Query(None, description="Contact name (alternative to body)")
):
    """
    Prepare outreach materials for a contact.

    Uses 4 agents in sequence:
    1. Research Agent - Gets contact context
    2. Analyst Agent - Finds relevant opportunities
    3. Strategy Agent - Determines approach
    4. Writer Agent - Generates outreach materials

    Returns call script, email template, and LinkedIn message.
    """
    if not CREWAI_WORKFLOWS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="CrewAI workflows not available. Install: pip install crewai langchain-anthropic"
        )

    # Get contact name from body or query param
    name = request.contact_name if request else contact_name
    if not name:
        raise HTTPException(status_code=400, detail="contact_name is required")

    try:
        result = await run_prepare_outreach(name)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

        return {
            "success": True,
            "contact": name,
            "call_script": result.get("call_script"),
            "email_template": result.get("email_template"),
            "linkedin_message": result.get("linkedin_message")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Outreach prep error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/weekly-intel")
async def api_weekly_intel():
    """
    Generate weekly BD intelligence report.

    Uses 4 agents in sequence:
    1. Research Agent - Scans for new opportunities
    2. Analyst Agent - Identifies hot programs
    3. Strategy Agent - Prioritizes actions
    4. Writer Agent - Generates executive briefing

    Returns hot programs, action items, and executive summary.
    """
    if not CREWAI_WORKFLOWS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="CrewAI workflows not available. Install: pip install crewai langchain-anthropic"
        )

    try:
        result = await run_weekly_intel()

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

        return {
            "success": True,
            "executive_summary": result.get("executive_summary"),
            "hot_programs": result.get("hot_programs", []),
            "new_opportunities": result.get("new_opportunities", []),
            "action_items": result.get("action_items", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Weekly intel error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# QA & PIPELINE STATUS
# =========================================

@app.get("/qa/stats")
async def get_qa_stats():
    """Get QA review queue statistics."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from Engine6_QA.scripts.qa_feedback import ReviewQueue
        queue = ReviewQueue()
        stats = queue.get_stats()
        return {
            "total_items": stats["total"],
            "pending": stats["pending"],
            "reviewed": stats["reviewed"],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"QA stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/qa/review-queue")
async def get_qa_review_queue(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
):
    """Get paginated QA review queue items."""
    try:
        from Engine6_QA.scripts.qa_feedback import ReviewQueue
        queue = ReviewQueue()
        items = queue.get_pending() if status == "pending" else queue.items
        return {
            "items": items[offset:offset + limit],
            "total": len(items),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"QA review-queue error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ResolveRequest(BaseModel):
    action: str = Field(..., description="approve, reject, or fix")
    notes: Optional[str] = None


@app.post("/qa/review-queue/{item_id}/resolve")
async def resolve_qa_item(item_id: str, request: ResolveRequest):
    """Approve, reject, or fix a QA review queue item."""
    try:
        from Engine6_QA.scripts.qa_feedback import ReviewQueue
        queue = ReviewQueue()
        item = next((i for i in queue.items if i.get("job_id") == item_id), None)
        if not item:
            raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
        item["reviewed"] = True
        item["review_action"] = request.action
        item["review_notes"] = request.notes
        item["reviewed_at"] = datetime.now().isoformat()
        queue._save()
        return {"success": True, "item": item}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"QA resolve error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# DOCLING DOCUMENT INGESTION
# =========================================

@app.post("/ingest/document")
def ingest_document(
    file: UploadFile = File(...),
    collection: str = Form("federal_contracts"),
    doc_type: str = Form("unknown"),
    max_tokens: int = Form(512),
):
    """Ingest a PDF/DOCX via Docling: convert, chunk, embed, upsert to Qdrant."""
    import tempfile
    try:
        from Engine8_Knowledge.processors.docling_processor import ingest_document_to_qdrant
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Docling processor not available: {e}")

    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")

    # Save upload to temp file
    suffix = Path(file.filename).suffix if file.filename else ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = file.file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = ingest_document_to_qdrant(
            file_path=tmp_path,
            store=store,
            collection=collection,
            max_tokens=max_tokens,
            doc_type=doc_type,
            metadata={"original_filename": file.filename},
        )
        return result
    except Exception as e:
        logger.error(f"Document ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# =========================================
# GRAPHITI KNOWLEDGE GRAPH ENDPOINTS
# =========================================

@app.post("/graphiti/ingest")
async def graphiti_ingest(
    name: str = Query(..., description="Episode name"),
    source: str = Query("api", description="Source description"),
    body: str = Query(..., description="Episode text body"),
):
    """Add a BD intelligence episode to the Graphiti knowledge graph."""
    try:
        from services.graphiti_service import add_bd_episode
        result = await add_bd_episode(name=name, body=body, source=source)
        return result
    except Exception as e:
        logger.error(f"Graphiti ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graphiti/search")
async def graphiti_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
):
    """Search the Graphiti knowledge graph for facts and relationships."""
    try:
        from services.graphiti_service import search_graph
        results = await search_graph(query=q, limit=limit)
        return {"query": q, "results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Graphiti search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/qa/report")
def get_qa_report():
    """Full quality report: collection health, quality scores, alerts."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from Engine6_QA.quality_monitor import QualityMonitor
        qdrant_client = store.client if store else None
        monitor = QualityMonitor(client=qdrant_client)
        report = monitor.generate_report()
        return {
            "timestamp": report.timestamp,
            "collections": report.collections,
            "quality_scores": report.quality_scores,
            "alerts": report.alerts,
            "summary": report.summary,
        }
    except Exception as e:
        logger.error(f"QA report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alerts/check")
def check_alerts_now():
    """Manually trigger alert rule evaluation."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from Engine6_QA.scripts.alerts import AlertEngine
        engine = AlertEngine()
        alerts = engine.check_all_rules()
        engine.deliver_all(alerts)
        return {
            "triggered": len(alerts),
            "alerts": [
                {"title": a.title, "severity": a.severity.value, "message": a.message}
                for a in alerts
            ],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Alert check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/summary")
def get_dashboard_summary():
    """Aggregated dashboard data in a single call."""
    result = {"timestamp": datetime.now().isoformat()}

    # Collection stats
    try:
        result["collections"] = store.get_collection_stats() if store else {}
    except Exception:
        result["collections"] = {}

    # QA queue stats
    try:
        from Engine6_QA.scripts.qa_feedback import ReviewQueue
        queue = ReviewQueue()
        result["qa"] = queue.get_stats()
    except Exception:
        result["qa"] = {"total": 0, "pending": 0, "reviewed": 0}

    # Pipeline status
    state_file = Path(__file__).parent.parent / "outputs" / "pipeline_state.json"
    try:
        if state_file.exists():
            with open(state_file, "r") as f:
                state = json.load(f)
            result["pipeline"] = {
                "is_running": bool(state.get("current_run")),
                "last_run": state.get("last_completed_run"),
                "total_runs": len(state.get("history", [])),
            }
        else:
            result["pipeline"] = {"is_running": False, "last_run": None, "total_runs": 0}
    except Exception:
        result["pipeline"] = {"is_running": False, "last_run": None, "total_runs": 0}

    # Recent alerts
    try:
        from Engine6_QA.scripts.alerts import AlertEngine
        engine = AlertEngine()
        result["alerts"] = engine.get_recent_alerts(5)
    except Exception:
        result["alerts"] = []

    # System health
    result["health"] = {"status": "healthy", "api": True, "qdrant": store is not None}

    return result


@app.get("/pipeline/status")
async def get_pipeline_status():
    """Get pipeline execution status and history."""
    state_file = Path(__file__).parent.parent / "outputs" / "pipeline_state.json"
    if not state_file.exists():
        return {
            "is_running": False,
            "current_run": None,
            "last_run": None,
            "history": [],
            "stats": {"total_runs": 0, "success_rate": 0.0, "avg_duration": 0.0},
        }
    try:
        with open(state_file, "r") as f:
            state = json.load(f)
        history = state.get("history", [])
        successes = sum(1 for r in history if r.get("success"))
        durations = [r.get("duration_seconds", 0) for r in history if r.get("duration_seconds")]
        return {
            "is_running": bool(state.get("current_run")),
            "current_run": state.get("current_run"),
            "last_run": state.get("last_completed_run"),
            "history": history[-10:],
            "stats": {
                "total_runs": len(history),
                "success_rate": round(successes / len(history), 2) if history else 0.0,
                "avg_duration": round(sum(durations) / len(durations), 1) if durations else 0.0,
            },
        }
    except Exception as e:
        logger.error(f"Pipeline status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class TriggerRequest(BaseModel):
    input_file: Optional[str] = None
    test_mode: bool = False
    hot_leads_only: bool = False


@app.post("/pipeline/trigger")
async def trigger_pipeline(request: TriggerRequest):
    """Trigger a pipeline run as a background subprocess."""
    import subprocess as sp
    import uuid as _uuid

    run_id = str(_uuid.uuid4())[:8]
    python_exe = sys.executable
    orchestrator_path = Path(__file__).parent.parent / "orchestrator.py"

    cmd = [python_exe, str(orchestrator_path)]
    if request.input_file:
        cmd.extend(["--input", request.input_file])
    if request.test_mode:
        cmd.append("--test")
    if request.hot_leads_only:
        cmd.append("--hot-leads-only")

    # Record start in state file
    state_file = Path(__file__).parent.parent / "outputs" / "pipeline_state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state = {}
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                state = json.load(f)
        except (json.JSONDecodeError, OSError):
            state = {}
    state["current_run"] = {"run_id": run_id, "started_at": datetime.now().isoformat(), "config": request.dict()}
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2, default=str)

    sp.Popen(cmd, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    logger.info(f"Pipeline triggered: run_id={run_id}")

    return {"success": True, "run_id": run_id, "status": "started"}


@app.get("/alerts")
async def get_alerts(limit: int = Query(20, ge=1, le=100)):
    """Get recent alert history."""
    try:
        from Engine6_QA.scripts.alerts import AlertEngine
        engine = AlertEngine()
        return {"alerts": engine.get_recent_alerts(limit), "count": len(engine.get_recent_alerts(limit))}
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        return {"alerts": [], "count": 0, "error": str(e)}


# =========================================
# MAIN
# =========================================

def main():
    """Run the API server."""
    import argparse

    parser = argparse.ArgumentParser(description='BD Intelligence Hub API Server')
    parser.add_argument('--host', default=API_HOST, help='Host to bind')
    parser.add_argument('--port', type=int, default=API_PORT, help='Port to bind')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    parser.add_argument('--workers', type=int, default=4, help='Number of uvicorn workers (default: 4)')

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"BD Intelligence Hub API v2.0")
    print(f"{'='*60}")
    print(f"Starting at http://{args.host}:{args.port}")
    print(f"API docs: http://{args.host}:{args.port}/docs")
    print(f"50+ endpoints available")
    print(f"{'='*60}\n")

    if args.reload:
        uvicorn.run(
            "Engine8_Knowledge.api:app",
            host=args.host,
            port=args.port,
            reload=True
        )
    else:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port
        )


if __name__ == '__main__':
    main()
