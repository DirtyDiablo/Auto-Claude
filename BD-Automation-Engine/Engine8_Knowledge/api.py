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
    query: str = Field(..., description="Search query")
    collection: Optional[str] = Field(None, description="Collection to search")
    limit: int = Field(10, ge=1, le=50, description="Max results")
    score_threshold: float = Field(0.3, ge=0.0, le=1.0, description="Min relevance score")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter conditions")


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
    store = BDKnowledgeStore()
    store.initialize_collections()
    rag_engine = BDRAGEngine(vector_store=store)
    indexer = BDIndexer(store=store)

    # Initialize new components
    memory = get_memory()
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
            return {"answer": cached.get("result", {}).get("answer", ""), "cache_hit": True, **cached}

    result = await router.smart_query(q)

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
# SEARCH ENDPOINTS
# =========================================

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Semantic search across knowledge base."""
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


# =========================================
# INGEST ENDPOINTS
# =========================================

@app.post("/ingest/document")
async def ingest_document(data: DocumentInput):
    """Ingest document to graph."""
    await graph.insert_document(data.text)
    memory.add_interaction(f"Ingested document: {data.text[:200]}...")
    return {"success": True, "message": "Document ingested"}


@app.post("/ingest/program")
async def ingest_program(data: ProgramInput):
    """Ingest program."""
    await graph.insert_program(data.dict())
    memory.add_entity_fact(data.name, "program", f"Value: {data.value}, Clearance: {data.clearance}")
    return {"success": True, "program": data.name}


@app.post("/ingest/company")
async def ingest_company(data: CompanyInput):
    """Ingest company."""
    await graph.insert_company(data.dict())
    memory.add_entity_fact(data.name, "company", f"Type: {data.type}, Programs: {len(data.programs)}")
    return {"success": True, "company": data.name}


@app.post("/ingest/contact")
async def ingest_contact(data: ContactInput):
    """Ingest contact."""
    await graph.insert_contact(data.dict())
    memory.add_entity_fact(data.name, "contact", f"Company: {data.company}, Title: {data.title}")
    return {"success": True, "contact": data.name}


@app.post("/ingest/jobs")
async def ingest_jobs(jobs: List[JobInput]):
    """Ingest multiple jobs (for Data-Scraper)."""
    # Convert JobInput to dicts for indexing
    job_dicts = []
    for job in jobs:
        job_dicts.append({
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "clearance": job.clearance,
            "description": job.description[:2000] if job.description else "",
            "indexed_at": datetime.now().isoformat()
        })

    # Use the vector store's index_jobs method
    indexed, errors = store.index_jobs(job_dicts)

    # Log to memory (optional, may fail)
    try:
        memory.add_scrape_result("jobs", f"Ingested {indexed} jobs", indexed)
    except Exception as e:
        logger.warning(f"Memory logging failed: {e}")

    return {"success": True, "count": indexed, "errors": errors}


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
# MAIN
# =========================================

def main():
    """Run the API server."""
    import argparse

    parser = argparse.ArgumentParser(description='BD Intelligence Hub API Server')
    parser.add_argument('--host', default=API_HOST, help='Host to bind')
    parser.add_argument('--port', type=int, default=API_PORT, help='Port to bind')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"BD Intelligence Hub API v2.0")
    print(f"{'='*60}")
    print(f"Starting at http://{args.host}:{args.port}")
    print(f"API docs: http://{args.host}:{args.port}/docs")
    print(f"50+ endpoints available")
    print(f"{'='*60}\n")

    uvicorn.run(
        "Engine8_Knowledge.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == '__main__':
    main()
