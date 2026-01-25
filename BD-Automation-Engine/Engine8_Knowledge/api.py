"""
BD Knowledge API - FastAPI server for MCP integration.
Provides REST endpoints for semantic search and RAG queries.
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
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("FastAPI not installed. Install with: pip install fastapi uvicorn")
    sys.exit(1)

from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore, SearchResult
from Engine8_Knowledge.scripts.rag_engine import BDRAGEngine, RAGResponse
from Engine8_Knowledge.scripts.indexer import BDIndexer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('BDKnowledgeAPI')

# =========================================
# CONFIGURATION
# =========================================

API_HOST = os.getenv('KNOWLEDGE_API_HOST', '127.0.0.1')
API_PORT = int(os.getenv('KNOWLEDGE_API_PORT', '8100'))

# =========================================
# PYDANTIC MODELS
# =========================================

class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., description="Search query")
    collection: Optional[str] = Field(None, description="Collection to search (jobs, contacts, programs, documents, activities)")
    limit: int = Field(10, ge=1, le=50, description="Max results")
    score_threshold: float = Field(0.3, ge=0.0, le=1.0, description="Min relevance score")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter conditions")


class AskRequest(BaseModel):
    """RAG query request model."""
    question: str = Field(..., description="Natural language question")
    collection: Optional[str] = Field(None, description="Collection to search")
    limit: int = Field(5, ge=1, le=20, description="Max sources to retrieve")
    include_sources: bool = Field(True, description="Include source citations")


class SimilarRequest(BaseModel):
    """Find similar items request."""
    item_id: str = Field(..., description="ID of source item")
    collection: str = Field(..., description="Collection containing the item")
    limit: int = Field(10, ge=1, le=50, description="Max similar items")


class SearchResultModel(BaseModel):
    """Search result model."""
    id: str
    score: float
    payload: Dict[str, Any]
    collection: str


class SearchResponse(BaseModel):
    """Search response model."""
    query: str
    collection: Optional[str]
    results: List[SearchResultModel]
    count: int
    timestamp: str


class AskResponse(BaseModel):
    """RAG response model."""
    answer: str
    sources: List[SearchResultModel]
    query: str
    confidence: float
    collection_searched: Optional[str]
    timestamp: str


class StatsResponse(BaseModel):
    """Collection statistics response."""
    collections: Dict[str, Dict[str, Any]]
    total_vectors: int
    timestamp: str


class IndexResponse(BaseModel):
    """Indexing response model."""
    success: bool
    message: str
    indexed: int
    errors: int
    duration_seconds: float


# =========================================
# APPLICATION SETUP
# =========================================

# Global instances
store: Optional[BDKnowledgeStore] = None
rag_engine: Optional[BDRAGEngine] = None
indexer: Optional[BDIndexer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global store, rag_engine, indexer

    # Initialize on startup
    logger.info("Initializing BD Knowledge API...")

    store = BDKnowledgeStore()
    store.initialize_collections()

    rag_engine = BDRAGEngine(vector_store=store)
    indexer = BDIndexer(store=store)

    logger.info("BD Knowledge API initialized")

    yield

    # Cleanup on shutdown
    logger.info("Shutting down BD Knowledge API")


app = FastAPI(
    title="BD Knowledge API",
    description="Semantic search and RAG API for BD Intelligence data",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================
# HEALTH & STATUS ENDPOINTS
# =========================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get collection statistics."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")

    stats = store.get_collection_stats()

    total_vectors = sum(
        s.get('vectors_count', 0) for s in stats.values()
        if isinstance(s, dict) and 'vectors_count' in s
    )

    return StatsResponse(
        collections=stats,
        total_vectors=total_vectors,
        timestamp=datetime.now().isoformat()
    )


# =========================================
# SEARCH ENDPOINTS
# =========================================

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Semantic search across knowledge base.

    - **query**: Natural language search query
    - **collection**: Specific collection or None for all
    - **limit**: Maximum results
    - **score_threshold**: Minimum relevance score (0-1)
    - **filters**: Optional field filters
    """
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
            # Search all collections
            all_results = store.search_all(
                query=request.query,
                limit_per_collection=request.limit,
                score_threshold=request.score_threshold
            )
            # Flatten results
            results = []
            for coll, items in all_results.items():
                for item in items:
                    item.collection = coll
                    results.append(item)
            results.sort(key=lambda x: x.score, reverse=True)
            results = results[:request.limit]

        return SearchResponse(
            query=request.query,
            collection=request.collection,
            results=[
                SearchResultModel(
                    id=r.id,
                    score=r.score,
                    payload=r.payload,
                    collection=r.collection
                )
                for r in results
            ],
            count=len(results),
            timestamp=datetime.now().isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
async def search_get(
    q: str = Query(..., description="Search query"),
    collection: Optional[str] = Query(None, description="Collection to search"),
    limit: int = Query(10, ge=1, le=50, description="Max results")
):
    """GET endpoint for search (convenience)."""
    request = SearchRequest(query=q, collection=collection, limit=limit)
    return await search(request)


@app.post("/similar", response_model=SearchResponse)
async def find_similar(request: SimilarRequest):
    """
    Find similar items to a given item.

    - **item_id**: ID of the source item
    - **collection**: Collection containing the item
    - **limit**: Maximum similar items to return
    """
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")

    try:
        results = store.find_similar(
            item_id=request.item_id,
            collection=request.collection,
            limit=request.limit
        )

        return SearchResponse(
            query=f"similar to {request.item_id}",
            collection=request.collection,
            results=[
                SearchResultModel(
                    id=r.id,
                    score=r.score,
                    payload=r.payload,
                    collection=r.collection
                )
                for r in results
            ],
            count=len(results),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Similar search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# RAG ENDPOINTS
# =========================================

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Ask a natural language question (RAG).

    Uses semantic search to find relevant context, then generates
    an answer using Claude.

    - **question**: Natural language question
    - **collection**: Specific collection to search
    - **limit**: Max sources to use for context
    - **include_sources**: Include source citations in response
    """
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
            sources = [
                SearchResultModel(
                    id=s.id,
                    score=s.score,
                    payload=s.payload,
                    collection=s.collection
                )
                for s in response.sources
            ]

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
    """GET endpoint for ask (convenience)."""
    request = AskRequest(question=q, collection=collection, limit=limit)
    return await ask_question(request)


# =========================================
# SPECIALIZED ENDPOINTS
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
    return {
        "company": company_name,
        "contacts": [r.to_dict() for r in results],
        "count": len(results)
    }


@app.get("/jobs/for/{program_name}")
async def get_jobs_for_program(program_name: str, limit: int = 20):
    """Find jobs associated with a program."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")

    results = store.find_jobs_for_program(program_name, limit=limit)
    return {
        "program": program_name,
        "jobs": [r.to_dict() for r in results],
        "count": len(results)
    }


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
# MAIN
# =========================================

def main():
    """Run the API server."""
    import argparse

    parser = argparse.ArgumentParser(description='BD Knowledge API Server')
    parser.add_argument('--host', default=API_HOST, help='Host to bind')
    parser.add_argument('--port', type=int, default=API_PORT, help='Port to bind')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')

    args = parser.parse_args()

    print(f"\nStarting BD Knowledge API at http://{args.host}:{args.port}")
    print(f"API docs available at http://{args.host}:{args.port}/docs\n")

    uvicorn.run(
        "Engine8_Knowledge.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == '__main__':
    main()
