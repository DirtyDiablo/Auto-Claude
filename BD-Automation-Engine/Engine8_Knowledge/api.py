"""
BD Knowledge API - Enhanced FastAPI server for BD Intelligence Hub.
50+ endpoints for comprehensive BD operations.
"""

import os
import sys
import json
import asyncio
import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

# Add parent to path for imports (fallback if not installed via `pip install -e .`)
_project_root = str(Path(__file__).parent.parent)
_script_dir = str(Path(__file__).parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
# Remove script dir from path to prevent Engine8_Knowledge/platform/ shadowing stdlib
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

from dotenv import load_dotenv

load_dotenv()

try:
    from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, Request, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
    import uvicorn
    import asyncio

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logging.error("FastAPI not installed. Install with: pip install fastapi uvicorn")
    sys.exit(1)

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    from slowapi.middleware import SlowAPIMiddleware

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["120/minute"],
        application_limits=["600/minute"],
    )
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    limiter = None
    RATE_LIMITING_AVAILABLE = False
    logging.warning("slowapi not installed. Rate limiting disabled. Install: pip install slowapi")

# Import existing modules
from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchText
from Engine8_Knowledge.scripts.rag_engine import BDRAGEngine
from Engine8_Knowledge.scripts.indexer import BDIndexer

# Import new enhanced modules
from Engine8_Knowledge.scripts.memory_layer import get_memory
from Engine8_Knowledge.scripts.lightrag_engine import get_knowledge_graph
from Engine8_Knowledge.scripts.hybrid_retriever import get_hybrid_retriever
from Engine8_Knowledge.scripts.query_router import QueryRouter
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
    from config.logging_config import (
        setup_logging,
        get_logger as _get_structlog,
        generate_request_id,
        request_id_var,
    )

    setup_logging(log_level="INFO")
    logger = _get_structlog("BDKnowledgeAPI")
    STRUCTLOG_AVAILABLE = True
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("BDKnowledgeAPI")
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
    from streaming.streaming_api import router as streaming_router

    STREAMING_AVAILABLE = True
except ImportError as e:
    STREAMING_AVAILABLE = False
    logger.warning(f"Streaming router not available: {e}")

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

# Import Supabase client
try:
    from Engine8_Knowledge.supabase_client import (
        is_available as supabase_available,
        get_contacts as sb_get_contacts,
        get_programs as sb_get_programs,
        get_jobs as sb_get_jobs,
        get_companies as sb_get_companies,
        get_graph_data as sb_get_graph_data,
        get_stats as sb_get_stats,
        get_domain_tags as sb_get_domain_tags,
        get_quality_stats as sb_get_quality_stats,
        get_competition_graph as sb_get_competition_graph,
    )
    SUPABASE_CLIENT_AVAILABLE = True
except ImportError as e:
    SUPABASE_CLIENT_AVAILABLE = False
    logger.warning(f"Supabase client not available: {e}")

# Logger already configured above

# =========================================
# CONFIGURATION
# =========================================

API_HOST = os.getenv("KNOWLEDGE_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("KNOWLEDGE_API_PORT", "8100"))

# Authentication & Authorization
# See Engine8_Knowledge/auth.py for full auth module (JWT, API keys, RBAC)
from Engine8_Knowledge.auth import get_current_user, require_permission, require_role, AuthUser, Role

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

# =========================================
# PYDANTIC MODELS (canonical source: Engine8_Knowledge/models.py)
# =========================================

from Engine8_Knowledge.models import (  # noqa: E402
    SearchRequest,
    AskRequest,
    SimilarRequest,
    SearchResultModel,
    SearchResponse,
    AskResponse,
    StatsResponse,
    IndexResponse,
    MemoryInput,
    InsightInput,
    DocumentInput,
    ProgramInput,
    CompanyInput,
    ContactInput,
    JobInput,
)


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
    qdrant_url = os.getenv("QDRANT_URL")
    store = BDKnowledgeStore(url=qdrant_url)
    store.initialize_collections()
    rag_engine = BDRAGEngine(vector_store=store)
    indexer = BDIndexer(store=store)

    # Initialize new components (catch mem0 Rust panic - PanicException is BaseException)
    try:
        memory = get_memory()
    except BaseException as e:
        logger.warning(f"Memory layer init failed (continuing without): {e}")
        memory = None
    graph = get_knowledge_graph()
    retriever = get_hybrid_retriever()
    router = QueryRouter()
    pageindex = get_pageindex()
    try:
        cache = get_cache()
    except Exception as e:
        logger.warning(f"Cache init failed (continuing without): {e}")
        cache = None

    # Initialize agents
    program_agent = ProgramIntelAgent()
    company_agent = CompanyResearchAgent()
    contact_agent = ContactFinderAgent()
    strategy_agent = BDStrategyAgent()
    orchestrator = get_orchestrator()

    # Register globals in dependency registry for router modules
    from Engine8_Knowledge import deps as _deps
    _deps.register("store", store)
    _deps.register("rag_engine", rag_engine)
    _deps.register("indexer", indexer)
    _deps.register("memory", memory)
    _deps.register("graph", graph)
    _deps.register("retriever", retriever)
    _deps.register("router", router)
    _deps.register("pageindex", pageindex)
    _deps.register("cache", cache)
    _deps.register("orchestrator", orchestrator)

    logger.info("BD Intelligence Hub API initialized with 50+ endpoints")

    # Start background staleness auto-alerts (Phase 8A)
    staleness_task = None
    try:
        from Engine8_Knowledge.api_routers.phase8a_pipeline import staleness_auto_alerts

        staleness_task = asyncio.create_task(
            staleness_auto_alerts(interval_seconds=3600)
        )
        logger.info("Background staleness auto-alerts started (1h interval)")
    except ImportError:
        logger.warning("Phase 8A staleness checker not available")

    # Optionally start the sync engine background polling loop
    sync_engine_instance = None
    if os.getenv("SYNC_ENGINE_AUTO_START", "").lower() in ("1", "true", "yes"):
        try:
            from services.sync_engine import get_sync_engine

            poll_interval = int(os.getenv("SYNC_POLL_INTERVAL", "120"))
            sync_engine_instance = get_sync_engine(poll_interval_seconds=poll_interval)
            await sync_engine_instance.start()
            logger.info("Sync engine started", poll_interval=poll_interval)
        except Exception as e:
            logger.warning(f"Sync engine start failed (continuing without): {e}")

    yield

    # Stop sync engine
    if sync_engine_instance:
        await sync_engine_instance.stop()

    # Cancel background tasks
    if staleness_task and not staleness_task.done():
        staleness_task.cancel()
        try:
            await staleness_task
        except asyncio.CancelledError:
            pass

    logger.info("Shutting down BD Intelligence Hub API")


app = FastAPI(
    title="BD Intelligence Hub API",
    description="Comprehensive API for BD Intelligence operations: search, memory, graph, agents, and more",
    version="2.0.0",
    lifespan=lifespan,
    dependencies=[Depends(get_current_user)],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-API-Key", "Authorization"],
)

# Rate limiting (optional - requires slowapi)
if RATE_LIMITING_AVAILABLE:
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiting enabled: 120 req/min per IP (default), 600 req/min total")

    def rate_limit(limit_str):
        """Create rate limit decorator."""
        return limiter.limit(limit_str)
else:
    def rate_limit(limit_str):
        """No-op decorator when slowapi not installed."""
        return lambda f: f

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
logger.info("Using local Mem0 memory endpoints")

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
    logger.info(
        "Hybrid search routes enabled: /search/hybrid/v2, /collections/*, /sync/*, /index/bullhorn-notes"
    )
except ImportError as e:
    logger.warning(f"Hybrid endpoints not available: {e}")

try:
    from Engine8_Knowledge.api_routers.auth_api import router as auth_router

    app.include_router(auth_router)
    logger.info("Auth management routes enabled: /auth/*")
except ImportError as e:
    logger.warning(f"Auth API not available: {e}")

try:
    from Engine8_Knowledge.agents.api_routes import router as crewai_router

    app.include_router(crewai_router)
    logger.info("CrewAI agent routes enabled: /agents/*")
except ImportError as e:
    logger.warning(f"CrewAI agent routes not available: {e}")

try:
    from Engine8_Knowledge.api_routers.phase7_endpoints import router as phase7_router

    app.include_router(phase7_router)
    logger.info(
        "Phase 7 routes enabled: /data/freshness, /notifications, /webhooks/*, /ai/memories, /ai/costs"
    )
except ImportError as e:
    logger.warning(f"Phase 7 endpoints not available: {e}")

try:
    from Engine8_Knowledge.api_routers.phase8a_pipeline import router as phase8a_router

    app.include_router(phase8a_router)
    logger.info(
        "Phase 8A routes enabled: /pipeline/run, /pipeline/status, /pipeline/history"
    )
except ImportError as e:
    logger.warning(f"Phase 8A pipeline routes not available: {e}")

try:
    from Engine8_Knowledge.api_routers.phase9a_competitive import (
        router as phase9a_router,
    )

    app.include_router(phase9a_router)
    logger.info(
        "Phase 9A routes enabled: /contracts/awards, /contracts/expiring, /competitive/summary"
    )
except ImportError as e:
    logger.warning(f"Phase 9A competitive routes not available: {e}")

try:
    from Engine8_Knowledge.api_routers.phase10a_reports import router as phase10a_router

    app.include_router(phase10a_router)
    logger.info("Phase 10A routes enabled: /reports/weekly")
except ImportError as e:
    logger.warning(f"Phase 10A report routes not available: {e}")

try:
    from Engine8_Knowledge.ml.routes import router as ml_router

    app.include_router(ml_router)
    logger.info(
        "Phase 13A ML routes enabled: /ml/predict-response, /ml/hiring-signals, /ml/model-status"
    )
except ImportError as e:
    logger.warning(f"Phase 13A ML routes not available: {e}")

try:
    from Engine8_Knowledge.integrations.routes import router as integrations_router

    app.include_router(integrations_router)
    logger.info(
        "Phase 14A integration routes enabled: /integrations/slack/*, /integrations/crm/*"
    )
except ImportError as e:
    logger.warning(f"Phase 14A integration routes not available: {e}")

try:
    from Engine8_Knowledge.agents.autonomous.routes import router as autonomous_router

    app.include_router(autonomous_router)
    logger.info("Phase 15A autonomous agent routes enabled: /agents/autonomous/*")
except ImportError as e:
    logger.warning(f"Phase 15A autonomous agent routes not available: {e}")

try:
    from Engine8_Knowledge.graph.analytics_routes import (
        router as graph_analytics_router,
    )

    app.include_router(graph_analytics_router)
    logger.info(
        "Phase 16A graph analytics routes enabled: /graph/influence/*, /graph/communities/*, /graph/rag-query"
    )
except ImportError as e:
    logger.warning(f"Phase 16A graph analytics routes not available: {e}")

try:
    from Engine8_Knowledge.realtime.routes import router as realtime_router

    app.include_router(realtime_router)
    logger.info("Phase 17A realtime routes enabled: /ws/dashboard, /sse/*, /realtime/*")
except ImportError as e:
    logger.warning(f"Phase 17A realtime routes not available: {e}")

try:
    from Engine8_Knowledge.embeddings.routes import router as embeddings_router

    app.include_router(embeddings_router)
    logger.info(
        "Phase 18A embeddings routes enabled: /embeddings/embed, /embeddings/benchmark, /embeddings/status"
    )
except ImportError as e:
    logger.warning(f"Phase 18A embeddings routes not available: {e}")

try:
    from Engine8_Knowledge.automation.routes import router as automation_router

    app.include_router(automation_router)
    logger.info(
        "Phase 19A automation routes enabled: /automation/schedule, /automation/workflows/*, /automation/claude/*"
    )
except ImportError as e:
    logger.warning(f"Phase 19A automation routes not available: {e}")

try:
    from Engine8_Knowledge.platform.stats_api import router as platform_router

    app.include_router(platform_router)
    logger.info(
        "Phase 20A platform routes enabled: /platform/stats, /platform/services"
    )
except ImportError as e:
    logger.warning(f"Phase 20A platform routes not available: {e}")

try:
    from Engine8_Knowledge.graph.neo4j_routes import router as neo4j_router

    app.include_router(neo4j_router)
    logger.info(
        "Phase 21A Neo4j graph routes enabled: /neo4j/health, /neo4j/stats, /neo4j/ingest/*, /neo4j/contacts/*, /neo4j/path/*"
    )
except ImportError as e:
    logger.warning(f"Phase 21A Neo4j graph routes not available: {e}")

try:
    from Engine8_Knowledge.search.search_routes import router as search_v2_router

    app.include_router(search_v2_router)
    logger.info(
        "Phase 22A search routes enabled: /search/v2, /search/v2/hybrid, /search/v2/graph, /search/v2/graphrag, /search/v2/benchmark"
    )
except ImportError as e:
    logger.warning(f"Phase 22A search routes not available: {e}")

try:
    from Engine8_Knowledge.workflows.workflow_routes import router as workflow_v2_router

    app.include_router(workflow_v2_router)
    logger.info(
        "Phase 23A workflow routes enabled: /workflows/start, /workflows/active, /workflows/approvals, /workflows/stats"
    )
except ImportError as e:
    logger.warning(f"Phase 23A workflow routes not available: {e}")

# Phase 24A: Scrape API v2 (Crawl4AI, SAM.gov, federal docs)
try:
    from Engine8_Knowledge.api_routers.scrape_api_v2 import router as scrape_v2_router

    app.include_router(scrape_v2_router)
    logger.info("Phase 24A scrape routes enabled: /scrape/*, /sam/*, /federal-docs/*")
except ImportError as e:
    logger.warning(f"Phase 24A scrape routes not available: {e}")

# Phase 25A: Memory API (Mem0, 5-layer memory, lifecycle)
try:
    from Engine8_Knowledge.api_routers.memory_api import router as memory_v2_router

    app.include_router(memory_v2_router)
    logger.info(
        "Phase 25A memory routes enabled: /memory/add, /memory/search, /memory/lifecycle/*"
    )
except ImportError as e:
    logger.warning(f"Phase 25A memory routes not available: {e}")

# Phase 26A: MCP Server API (FastMCP tools, config generator)
try:
    from Engine8_Knowledge.api_routers.mcp_api import router as mcp_router

    app.include_router(mcp_router)
    logger.info("Phase 26A MCP routes enabled: /mcp/health, /mcp/tools, /mcp/config")
except ImportError as e:
    logger.warning(f"Phase 26A MCP routes not available: {e}")

# Phase 27A: Org Chart API (generation, inference, export)
try:
    from Engine8_Knowledge.api_routers.org_chart_api import router as org_chart_router

    app.include_router(org_chart_router)
    logger.info(
        "Phase 27A org chart routes enabled: /org-chart/generate, /org-chart/export/*"
    )
except ImportError as e:
    logger.warning(f"Phase 27A org chart routes not available: {e}")

# Phase 28A: ML API v2 (Defense NER, topic modeling, placement prediction, embeddings)
try:
    from Engine8_Knowledge.api_routers.ml_api import router as ml_v2_router

    app.include_router(ml_v2_router)
    logger.info(
        "Phase 28A ML routes enabled: /ml/ner/*, /ml/topics/*, /ml/predict/*, /ml/embeddings/*"
    )
except ImportError as e:
    logger.warning(f"Phase 28A ML routes not available: {e}")

# Phase 29A: Optimizer API (self-assessment, auto-optimizer, regression detector, retrain)
try:
    from Engine8_Knowledge.api_routers.optimizer_api import router as optimizer_router

    app.include_router(optimizer_router)
    logger.info(
        "Phase 29A optimizer routes enabled: /optimizer/assess, /optimizer/recommendations, /optimizer/retrain/*"
    )
except ImportError as e:
    logger.warning(f"Phase 29A optimizer routes not available: {e}")

# Phase 30A: Monitoring API (health probes, resource usage, Prometheus metrics)
try:
    from Engine8_Knowledge.api_routers.monitoring_api import router as monitoring_router

    app.include_router(monitoring_router)
    logger.info(
        "Phase 30A monitoring routes enabled: /monitoring/health, /monitoring/ready, /monitoring/live, /metrics"
    )
except ImportError as e:
    logger.warning(f"Phase 30A monitoring routes not available: {e}")

# Phase 31A: Real-Time Event Streaming (event bus, processors, WebSocket, orchestrator)
try:
    from src.api.streaming_api import include_streaming_v2_router

    include_streaming_v2_router(app)
    logger.info(
        "Phase 31A streaming routes enabled: /streaming/* (14 REST + 4 WebSocket)"
    )
except ImportError as e:
    logger.warning(f"Phase 31A streaming routes not available: {e}")

# Phase 32A: Predictive Intelligence (win probability, opportunity scorer, forecaster, budget)
try:
    from src.api.predictive_api import include_predictive_router

    include_predictive_router(app)
    logger.info("Phase 32A predictive routes enabled: /predict/* (14 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 32A predictive routes not available: {e}")

# Phase 33A: Natural Language Query Engine (conversational BI, autocomplete)
try:
    from src.api.nlq_api import include_nlq_router

    include_nlq_router(app)
    logger.info("Phase 33A NLQ routes enabled: /nlq/* (9 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 33A NLQ routes not available: {e}")

# Phase 34A: Relationship Intelligence (strength scoring, PageRank, path routing, network analysis)
try:
    from src.api.relationship_api import include_relationship_router

    include_relationship_router(app)
    logger.info(
        "Phase 34A relationship routes enabled: /relationships/* (14 endpoints)"
    )
except ImportError as e:
    logger.warning(f"Phase 34A relationship routes not available: {e}")

# Phase 35A: Proposal & Capture Automation (capability statements, past performance, compliance, pricing)
try:
    from src.api.proposal_api import include_proposal_router

    include_proposal_router(app)
    logger.info("Phase 35A proposal routes enabled: /proposals/* (10 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 35A proposal routes not available: {e}")

# Phase 36A: Revenue Intelligence (revenue tracking, deal lifecycle, ROI, executive analytics)
try:
    from src.api.revenue_api import include_revenue_router

    include_revenue_router(app)
    logger.info("Phase 36A revenue routes enabled: /revenue/* (16 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 36A revenue routes not available: {e}")

# Phase 37A: Multi-Tenant SaaS + RBAC (tenant management, auth, RBAC, middleware)
try:
    from src.api.tenant_api import include_tenant_router

    include_tenant_router(app)
    logger.info("Phase 37A tenant routes enabled: /tenants/* + /auth/* (21 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 37A tenant routes not available: {e}")

# Phase 38A: Autonomous Data Quality Engine (quality monitoring, self-healing, lineage, rules DSL)
try:
    from src.api.data_quality_api import include_data_quality_router

    include_data_quality_router(app)
    logger.info("Phase 38A data quality routes enabled: /data-quality/* (17 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 38A data quality routes not available: {e}")

# Phase 39A: Temporal Knowledge Graph + Entity Resolution + Knowledge Compiler
try:
    from src.api.knowledge_api import include_knowledge_router

    include_knowledge_router(app)
    logger.info("Phase 39A knowledge routes enabled: /knowledge/* (15 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 39A knowledge routes not available: {e}")

# Phase 40A: Agentic RAG + Self-RAG + ColBERT Reranker + Query Decomposition
try:
    from src.api.rag_api import include_rag_router

    include_rag_router(app)
    logger.info("Phase 40A RAG routes enabled: /rag/* (10 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 40A RAG routes not available: {e}")

# Phase 41A: Agent Swarm Coordinator + Task Decomposition + Workers
try:
    from src.api.swarm_api import include_swarm_router

    include_swarm_router(app)
    logger.info("Phase 41A swarm routes enabled: /swarm/* (10 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 41A swarm routes not available: {e}")

# Phase 42A: Unified Memory Cortex — episodic/semantic/procedural
try:
    from src.api.memory_api import include_memory_router

    include_memory_router(app)
    logger.info("Phase 42A memory routes enabled: /memory/* (12 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 42A memory routes not available: {e}")

# Phase 43A: Data Governance — catalog, schema registry, contracts, SLAs
try:
    from src.api.governance_api import include_governance_router

    include_governance_router(app)
    logger.info("Phase 43A governance routes enabled: /governance/* (12 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 43A governance routes not available: {e}")

# Phase 44A: Meta-Learning, Strategic Patterns, Insight Compiler
try:
    from src.api.intelligence_api import include_intelligence_router

    include_intelligence_router(app)
    logger.info(
        "Phase 44A intelligence routes enabled: /api/intelligence/* (13 endpoints)"
    )
except ImportError as e:
    logger.warning(f"Phase 44A intelligence routes not available: {e}")

# Phase 45A: MCP Ecosystem — tool registry, apps renderer, orchestrator
try:
    from src.api.mcp_api import include_mcp_router

    include_mcp_router(app)
    logger.info("Phase 45A MCP routes enabled: /api/mcp/* (10 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 45A MCP routes not available: {e}")

# Phase 46A: Voice Intelligence — call briefings, transcript analysis
try:
    from src.api.voice_api import include_voice_router

    include_voice_router(app)
    logger.info("Phase 46A voice routes enabled: /api/voice/* (12 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 46A voice routes not available: {e}")

# Phase 47A: Domain Embedding Fine-Tuner — synthetic data, fine-tuning, benchmarks
try:
    from src.api.embeddings_api import include_embeddings_router

    include_embeddings_router(app)
    logger.info("Phase 47A embeddings routes enabled: /api/embeddings/* (12 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 47A embeddings routes not available: {e}")

# Phase 48A: Geographic Intelligence — geocoding, spatial queries, proximity analytics
try:
    from src.api.geo_api import include_geo_router

    include_geo_router(app)
    logger.info("Phase 48A geo routes enabled: /api/geo/* (10 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 48A geo routes not available: {e}")

# Phase 49A: Workflow Intelligence — Temporal durable workflows, cross-project orchestrator, NL-to-workflow
try:
    from src.api.workflows_api import include_workflows_router

    include_workflows_router(app)
    logger.info("Phase 49A workflow routes enabled: /api/workflows/* (12 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 49A workflow routes not available: {e}")

# Phase 50A: Real-Time Collaboration — Yjs rooms, contact claiming, shared intel feed
try:
    from src.api.collaboration_api import include_collaboration_router

    include_collaboration_router(app)
    logger.info("Phase 50A collaboration routes enabled: /api/collab/* (12 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 50A collaboration routes not available: {e}")

# Phase 51A: Simulation & Causal Intelligence — causal inference, digital twin, scenario analysis
try:
    from src.api.simulation_api import include_simulation_router

    include_simulation_router(app)
    logger.info(
        "Phase 51A simulation routes enabled: /api/causal/*, /api/twin/*, /api/scenario/*, /api/simulation/* (14 endpoints)"
    )
except ImportError as e:
    logger.warning(f"Phase 51A simulation routes not available: {e}")

# Phase 52A: Zero-Trust Security — ABAC policy enforcement, audit trail, encryption at rest
try:
    from src.api.security_api import include_security_router

    include_security_router(app)
    logger.info("Phase 52A security routes enabled: /api/security/* (14 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 52A security routes not available: {e}")

# Phase 53A: Observability — distributed tracing, metrics pipeline, SLO engine
try:
    from src.api.observability_api import include_observability_router

    include_observability_router(app)
    logger.info(
        "Phase 53A observability routes enabled: /api/observability/* (12 endpoints)"
    )
except ImportError as e:
    logger.warning(f"Phase 53A observability routes not available: {e}")

# Phase 54A: Resilience — circuit breakers, chaos engineering, bulkheads, graceful degradation
try:
    from src.api.resilience_api import include_resilience_router

    include_resilience_router(app)
    logger.info("Phase 54A resilience routes enabled: /api/resilience/* (12 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 54A resilience routes not available: {e}")

# Phase 55A: Experimentation — feature flags, A/B testing, experiment analytics
try:
    from src.api.experimentation_api import include_experimentation_router

    include_experimentation_router(app)
    logger.info(
        "Phase 55A experimentation routes enabled: /api/experimentation/* (12 endpoints)"
    )
except ImportError as e:
    logger.warning(f"Phase 55A experimentation routes not available: {e}")

# Phase 57A: Scaling — connection pools, read replicas, cache layers, auto-scaling
try:
    from src.api.scaling_api import include_scaling_router

    include_scaling_router(app)
    logger.info("Phase 57A scaling routes enabled: /api/scaling/* (12 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 57A scaling routes not available: {e}")

# Phase 58A: PWA — progressive web app, push notifications, responsive API
try:
    from src.api.pwa_api import include_pwa_router

    include_pwa_router(app)
    logger.info("Phase 58A PWA routes enabled: /api/pwa/* (10 endpoints)")
except ImportError as e:
    logger.warning(f"Phase 58A PWA routes not available: {e}")


# =========================================
# EXTRACTED ROUTERS (from routers/ directory)
# =========================================

from Engine8_Knowledge.routers.bdgraph import router as bdgraph_extracted_router
app.include_router(bdgraph_extracted_router)
logger.info("BD Knowledge Graph routes enabled: /bdgraph/* (12 endpoints)")

from Engine8_Knowledge.routers.ingest import router as ingest_extracted_router
app.include_router(ingest_extracted_router)
logger.info("Ingest routes enabled: /ingest/* (9 endpoints)")

from Engine8_Knowledge.routers.qa_review import router as qa_review_router
app.include_router(qa_review_router)
logger.info("QA Review Queue routes enabled: /qa/* (9 endpoints)")

from Engine8_Knowledge.routers.sync_status import router as sync_status_router
app.include_router(sync_status_router)
logger.info("Sync Status routes enabled: /sync/* (6 endpoints)")

try:
    from Engine8_Knowledge.routers.workflows import router as workflow_orchestration_router
    app.include_router(workflow_orchestration_router)
    logger.info("Workflow Orchestration routes enabled: /workflows/* (4 endpoints)")
except ImportError as e:
    logger.warning(f"Workflow orchestration router not available: {e}")


# =========================================
# HEALTH & STATUS ENDPOINTS
# =========================================


@app.get("/health")
async def health_check():
    """Health check endpoint with component status."""
    components = {}

    # Check Qdrant
    try:
        if store:
            stats = await asyncio.to_thread(store.get_collection_stats)
            components["qdrant"] = {"status": "healthy", "collections": len(stats) if isinstance(stats, dict) else 0}
        else:
            components["qdrant"] = {"status": "unavailable"}
    except Exception as e:
        components["qdrant"] = {"status": "unhealthy", "error": str(e)}

    # Check memory layer
    components["memory"] = {"status": "healthy" if memory else "unavailable"}

    # Check knowledge graph
    components["graph"] = {"status": "healthy" if graph else "unavailable"}

    # Overall status
    overall = "healthy" if components.get("qdrant", {}).get("status") == "healthy" else "degraded"

    return {
        "status": overall,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": components,
    }


@app.get("/ready")
async def readiness_check():
    """Readiness probe — returns 200 only when core dependencies are available."""
    if store:
        return {"ready": True}
    return {"ready": False, "reason": "vector store not initialized"}


@app.get("/live")
async def liveness_check():
    """Liveness probe — returns 200 if the process is alive."""
    return {"live": True}


@app.get("/stats")
async def get_stats():
    """Get comprehensive system statistics."""
    stats = {
        "qdrant": store.get_collection_stats() if store else {},
        "memory": memory.get_stats() if memory else {},
        "graph": graph.get_stats() if graph else {},
        "pageindex": pageindex.get_stats() if pageindex else {},
        "cache": cache.get_stats() if cache else {},
        "timestamp": datetime.now().isoformat(),
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


def _build_qdrant_filter(
    request: FilterRequest, field_map: Dict[str, str], text_match_fields: set = None
) -> Optional[Filter]:
    """Build Qdrant Filter from FilterRequest using a field mapping.
    Fields listed in text_match_fields use MatchText (substring) instead of MatchValue (exact).
    """
    conditions = []
    text_match_fields = text_match_fields or set()
    for param_name, payload_field in field_map.items():
        value = getattr(request, param_name, None)
        if value:
            if payload_field in text_match_fields:
                conditions.append(
                    FieldCondition(key=payload_field, match=MatchText(text=value))
                )
            else:
                conditions.append(
                    FieldCondition(key=payload_field, match=MatchValue(value=value))
                )
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
            qdrant_filter = _build_qdrant_filter(
                request,
                field_map,
                text_match_fields={"Programs", "Primes", "Clearances"},
            )
            query_embedding = await asyncio.to_thread(store._generate_embedding, request.query)
            search_result = await asyncio.to_thread(
                store.client.query_points,
                collection_name="contacts",
                query=query_embedding,
                query_filter=qdrant_filter,
                limit=request.limit,
                with_payload=True,
            )
            return {
                "contacts": [
                    {"id": str(p.id), "score": p.score, **p.payload}
                    for p in search_result.points
                ],
                "count": len(search_result.points),
                "query": request.query,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            qdrant_filter = _build_qdrant_filter(
                request,
                field_map,
                text_match_fields={"Programs", "Primes", "Clearances"},
            )
            results, _next = await asyncio.to_thread(
                store.client.scroll,
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

            results = await asyncio.to_thread(
                store.search,
                query=request.query,
                collection="programs",
                limit=request.limit,
                filters=filters if filters else None,
            )
            return {
                "programs": [
                    {"id": r.id, "score": r.score, **r.payload} for r in results
                ],
                "count": len(results),
                "query": request.query,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            qdrant_filter = _build_qdrant_filter(request, field_map)
            results, _next = await asyncio.to_thread(
                store.client.scroll,
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

    def _compute_dashboard_stats():
        collection_stats = store.get_collection_stats()

        total_vectors = sum(
            s.get("points_count", 0)
            for s in collection_stats.values()
            if isinstance(s, dict) and "points_count" in s
        )

        all_green = all(
            s.get("status", "").upper() == "GREEN"
            for s in collection_stats.values()
            if isinstance(s, dict) and "status" in s
        )

        # Field distribution sampling for analytics
        field_distributions = {}
        for coll_name in ["contacts", "programs", "jobs"]:
            try:
                sample, _ = store.client.scroll(
                    collection_name=coll_name,
                    limit=500,
                    with_payload=True,
                    with_vectors=False,
                )
                distributions: Dict[str, Dict[str, int]] = {}
                for point in sample:
                    for key, value in (point.payload or {}).items():
                        if isinstance(value, str) and 0 < len(value) < 100:
                            if key not in distributions:
                                distributions[key] = {}
                            distributions[key][value] = (
                                distributions[key].get(value, 0) + 1
                            )
                # Keep only top 20 values per field
                for key in distributions:
                    sorted_vals = sorted(
                        distributions[key].items(), key=lambda x: -x[1]
                    )[:20]
                    distributions[key] = dict(sorted_vals)
                field_distributions[coll_name] = distributions
            except Exception:
                field_distributions[coll_name] = {}

        return {
            "collections": collection_stats,
            "total_vectors": total_vectors,
            "total_collections": len(collection_stats),
            "all_healthy": all_green,
            "memory": memory.get_stats() if memory else {},
            "graph": graph.get_stats() if graph else {},
            "field_distributions": field_distributions,
            "timestamp": datetime.now().isoformat(),
        }

    try:
        return await asyncio.to_thread(_compute_dashboard_stats)
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# SMART QUERY ENDPOINTS
# =========================================


@app.get("/ask/smart")
async def smart_ask(
    q: str = Query(..., description="Your BD question"),
    use_cache: bool = Query(True, description="Use semantic cache"),
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
                "cache_hit": True,
            }

    result = await router.smart_query(q)

    logger.info(
        "smart_query_result",
        answer_len=len(result.answer),
        sources_count=len(result.sources),
        systems=result.systems_used,
        query_type=result.query_type.value,
    )

    response = {
        "answer": result.answer,
        "query_type": result.query_type.value,
        "systems_used": result.systems_used,
        "sources": result.sources[:5],
        "cache_hit": False,
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
        results, _next = await asyncio.to_thread(
            store.client.scroll,
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
        results, _next = await asyncio.to_thread(
            store.client.scroll,
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
            results = await asyncio.to_thread(
                store.search,
                query=request.query,
                collection=request.collection,
                limit=request.limit,
                score_threshold=request.score_threshold,
                filters=request.filters,
            )
        else:
            all_results = await asyncio.to_thread(
                store.search_all,
                query=request.query,
                limit_per_collection=request.limit,
                score_threshold=request.score_threshold,
            )
            results = []
            for coll, items in all_results.items():
                for item in items:
                    item.collection = coll
                    results.append(item)
            results.sort(key=lambda x: x.score, reverse=True)
            results = results[: request.limit]

        # Optional cross-encoder reranking
        if (
            request.rerank
            and results
            and retriever
            and getattr(retriever, "reranker", None)
        ):
            pairs = [
                [request.query, r.payload.get("text", "") or str(r.payload)]
                for r in results
            ]
            scores = await asyncio.to_thread(retriever.reranker.predict, pairs)
            ranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
            results = [r for r, _ in ranked[: request.limit]]

        return SearchResponse(
            query=request.query,
            collection=request.collection,
            results=[
                SearchResultModel(
                    id=r.id, score=r.score, payload=r.payload, collection=r.collection
                )
                for r in results
            ],
            count=len(results),
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
async def search_get(
    q: str = Query(..., description="Search query"),
    collection: Optional[str] = Query(None, description="Collection to search"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
):
    """GET endpoint for search."""
    request = SearchRequest(query=q, collection=collection, limit=limit)
    return await search(request)


@app.get("/search/semantic")
async def semantic_search(
    q: str = Query(..., description="Search query"),
    collection: str = Query("bd_knowledge", description="Collection"),
    limit: int = Query(10, description="Max results"),
):
    """Semantic-only search."""
    results = await asyncio.to_thread(retriever._semantic_search, q, collection, limit)
    return {
        "results": [{"id": r.id, "text": r.text, "score": r.score} for r in results]
    }


@app.get("/search/keyword")
async def keyword_search(
    q: str = Query(..., description="Search query"),
    collection: str = Query("bd_knowledge", description="Collection"),
    limit: int = Query(10, description="Max results"),
):
    """BM25 keyword search."""
    results = await asyncio.to_thread(retriever._keyword_search, q, collection, limit)
    return {
        "results": [{"id": r.id, "text": r.text, "score": r.score} for r in results]
    }


@app.get("/search/hybrid")
async def hybrid_search(
    q: str = Query(..., description="Search query"),
    collection: str = Query("bd_knowledge", description="Collection"),
    limit: int = Query(10, description="Max results"),
    use_rerank: bool = Query(True, description="Apply reranking"),
):
    """Hybrid semantic + keyword search with reranking."""
    results = await asyncio.to_thread(retriever.search, q, collection, limit, True, use_rerank)
    return {
        "results": [
            {"id": r.id, "text": r.text, "score": r.score, "source": r.source}
            for r in results
        ]
    }


# =========================================
# SAM.gov ENDPOINTS
# =========================================


@app.get("/sam/search")
async def sam_search(
    query: str = Query(..., description="Search keywords for federal opportunities"),
    naics: Optional[str] = Query(None, description="NAICS code filter"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
):
    """Search SAM.gov for active federal opportunities."""
    from Engine8_Knowledge.scrapers.sam_gov_sync import SAMGovSync, OpportunityQuery

    client = SAMGovSync()
    opp_query = OpportunityQuery(
        keywords=[query],
        naics_codes=[naics] if naics else [],
        limit=limit,
    )
    opportunities = await client.search_opportunities(opp_query)
    return {
        "query": query,
        "total": len(opportunities),
        "opportunities": [
            {
                "notice_id": opp.notice_id,
                "title": opp.title,
                "type": opp.type,
                "agency": opp.agency,
                "naics": opp.naics,
                "set_aside": opp.set_aside,
                "description": opp.description[:500] if opp.description else "",
            }
            for opp in opportunities
        ],
    }


@app.get("/sam/awards")
async def sam_awards(
    query: str = Query("", description="Search keywords (optional)"),
    company: Optional[str] = Query(None, description="Awardee company name"),
    naics: Optional[str] = Query(None, description="NAICS code filter"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
):
    """Search SAM.gov for recent contract awards."""
    from Engine8_Knowledge.scrapers.sam_gov_sync import SAMGovSync, SearchQuery

    client = SAMGovSync()
    search_query = SearchQuery(
        keywords=[query] if query else [],
        naics_codes=[naics] if naics else [],
        awardee=company,
        limit=limit,
    )
    awards = await client.search_awards(search_query)
    return {
        "query": query,
        "total": len(awards),
        "awards": [
            {
                "award_id": award.award_id,
                "title": award.title,
                "awardee": award.awardee,
                "value": award.value,
                "naics": award.naics,
                "agency": award.agency,
                "set_aside": award.set_aside,
                "description": award.description[:500] if award.description else "",
                "contract_type": award.contract_type,
            }
            for award in awards
        ],
    }


# =========================================
# RAG ENDPOINTS
# =========================================


@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """Ask a natural language question (RAG)."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")

    try:
        response = await asyncio.to_thread(
            rag_engine.ask,
            question=request.question,
            collection=request.collection,
            limit=request.limit,
        )

        sources = []
        if request.include_sources:
            sources = [
                SearchResultModel(
                    id=s.id, score=s.score, payload=s.payload, collection=s.collection
                )
                for s in response.sources
            ]

        return AskResponse(
            answer=response.answer,
            sources=sources,
            query=response.query,
            confidence=response.confidence,
            collection_searched=response.collection_searched,
            timestamp=response.timestamp,
        )
    except Exception as e:
        logger.error(f"RAG error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ask")
async def ask_get(
    q: str = Query(..., description="Question to ask"),
    collection: Optional[str] = Query(None, description="Collection to search"),
    limit: int = Query(5, ge=1, le=20, description="Max sources"),
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
    mode: str = Query("hybrid", description="Query mode: naive, local, global, hybrid"),
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
# BD KNOWLEDGE GRAPH ENDPOINTS — MOVED to routers/bdgraph.py
# =========================================

# NOTE: BD Graph endpoints (/bdgraph/*) are now served by
# Engine8_Knowledge.routers.bdgraph — included above.
# The imports below are kept for any inline code that still references them.
try:
    from Engine8_Knowledge.graph.bd_knowledge_graph import (
        get_knowledge_graph as get_bd_graph,
        ENTITY_TYPES,
        RELATIONSHIP_TYPES,
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


# bdgraph inline routes removed — now in routers/bdgraph.py


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
    entity_name: str = Query(...), entity_type: str = Query(...), fact: str = Query(...)
):
    """Add entity fact."""
    result = memory.add_entity_fact(entity_name, entity_type, fact)
    return {"success": True, "result": result}


@app.post("/memory/insight")
async def add_insight(data: InsightInput):
    """Add BD insight."""
    result = memory.add_bd_insight(
        data.insight_type, data.insight, data.source, data.confidence
    )
    return {"success": True, "result": result}


@app.get("/memory/search")
async def search_memory(q: str = Query(...), limit: int = Query(10)):
    """Search memories."""
    results = await asyncio.to_thread(memory.get_context, q, limit)
    return {"results": results}


@app.get("/memory/entity/{entity_name}")
async def get_entity_facts(entity_name: str, limit: int = Query(20)):
    """Get facts about entity."""
    results = memory.get_entity_facts(entity_name, limit)
    return {"entity": entity_name, "facts": results}


@app.get("/memory/insights")
async def get_insights(
    insight_type: Optional[str] = Query(None), limit: int = Query(10)
):
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
        return await asyncio.to_thread(system.get_contact_context, contact_name)
    except Exception:
        # Fallback to existing memory layer
        return {
            "interactions": [],
            "memories": memory.get_context(f"contact {contact_name}", 10),
        }


@app.get("/memory/program/{program_name}")
async def get_program_context(program_name: str):
    """Get full context for a program (insights + memories)."""
    try:
        from Engine8_Knowledge.scripts.memory_system import get_memory_system

        system = get_memory_system()
        return await asyncio.to_thread(system.get_program_context, program_name)
    except Exception:
        # Fallback to existing memory layer
        return {
            "insights": [],
            "memories": memory.get_context(f"program {program_name}", 10),
        }


# =========================================
# RAG ROUTER ENDPOINTS
# =========================================


@app.get("/rag/router")
async def rag_router_query(
    q: str = Query(..., description="Query"),
    strategy: str = Query("auto", description="Strategy: auto, lightrag, bm25, hybrid"),
    limit: int = Query(10, description="Max results"),
    collection: str = Query("bd_knowledge", description="Collection"),
):
    """RAG query with strategy selection."""
    try:
        from Engine8_Knowledge.scripts.rag_router import (
            get_rag_router,
            RetrievalStrategy,
        )

        rag_router = get_rag_router()
        result = await rag_router.retrieve(
            q, RetrievalStrategy(strategy), limit, collection
        )
        return {
            "strategy": result.strategy,
            "query": result.query,
            "results": result.results,
            "count": result.count,
            "strategies_used": result.strategies_used,
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
            "available_strategies": rag_router.get_available_strategies(),
        }
    except Exception as e:
        return {"error": str(e), "query": q}


# =========================================
# INGEST ENDPOINTS — MOVED to routers/ingest.py
# =========================================
# NOTE: Ingest endpoints (/ingest/*) are now served by
# Engine8_Knowledge.routers.ingest — included above.





# =========================================
# DAILY ACTION ENGINE
# =========================================

_daily_engine = None
_call_prep = None
_claim_tracker = None
_recompete_predictor = None


def _get_recompete_predictor():
    global _recompete_predictor
    if _recompete_predictor is None:
        from scripts.recompete_predictor import RecompetePredictor

        _recompete_predictor = RecompetePredictor(store, memory)
    return _recompete_predictor


def _get_daily_engine():
    global _daily_engine
    if _daily_engine is None:
        from scripts.daily_action_engine import DailyActionEngine

        _daily_engine = DailyActionEngine(store, memory)
    return _daily_engine


def _get_call_prep():
    global _call_prep
    if _call_prep is None:
        from scripts.call_prep_generator import CallPrepGenerator

        _call_prep = CallPrepGenerator(store, memory)
    return _call_prep


def _get_claim_tracker():
    global _claim_tracker
    if _claim_tracker is None:
        from scripts.claim_tracker import ClaimTracker

        _claim_tracker = ClaimTracker(store, memory)
    return _claim_tracker


@app.get("/daily-playbook")
async def get_daily_playbook(
    date: str = Query(None, description="Target date (YYYY-MM-DD)"),
    max_actions: int = Query(30, description="Max actions to generate"),
):
    """Generate prioritized daily playbook with contact context and recompete alerts."""
    try:
        engine = _get_daily_engine()
        playbook = await asyncio.to_thread(
            engine.generate_daily_playbook,
            target_date=date,
            max_actions=max_actions,
        )

        # Inject recompete alerts into the playbook
        try:
            predictor = _get_recompete_predictor()
            recompete_tasks = await asyncio.to_thread(
                predictor.get_recompete_alerts_for_playbook,
                months=12,
                max_alerts=5,
            )
            if recompete_tasks:
                playbook["tasks"].extend(recompete_tasks)
                # Re-sort by priority score
                playbook["tasks"].sort(
                    key=lambda t: t.get("priority_score", 0), reverse=True
                )
                playbook["total"] = len(playbook["tasks"])
                playbook["recompete_alerts"] = len(recompete_tasks)
        except Exception as re_err:
            logger.warning(f"Recompete alert injection failed: {re_err}")
            playbook["recompete_alerts"] = 0

        return playbook
    except Exception as e:
        logger.error(f"Daily playbook generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/call-prep/{contact_id}")
async def get_call_prep(
    contact_id: str,
    program: str = Query(None, description="Program context"),
):
    """Generate call preparation brief for a contact."""
    try:
        gen = _get_call_prep()
        brief = await asyncio.to_thread(
            gen.generate_brief,
            contact_id=contact_id,
            program_name=program,
        )
        return brief
    except Exception as e:
        logger.error(f"Call prep generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/call-prep")
async def get_call_prep_by_name(
    contact: str = Query(..., description="Contact name"),
    program: str = Query(None, description="Program context"),
):
    """Generate call preparation brief by contact name."""
    try:
        gen = _get_call_prep()
        brief = await asyncio.to_thread(
            gen.generate_brief,
            contact_name=contact,
            program_name=program,
        )
        return brief
    except Exception as e:
        logger.error(f"Call prep generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/claims/status")
async def get_claim_status():
    """Get claimed vs unclaimed contract status."""
    try:
        tracker = _get_claim_tracker()
        return await asyncio.to_thread(tracker.get_claim_status)
    except Exception as e:
        logger.error(f"Claim status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/claims/unclaimed-priority")
async def get_unclaimed_priority(
    limit: int = Query(20, description="Max results"),
):
    """Get highest-priority unclaimed contracts."""
    try:
        tracker = _get_claim_tracker()
        return {"unclaimed": await asyncio.to_thread(tracker.get_unclaimed_priority, limit=limit)}
    except Exception as e:
        logger.error(f"Unclaimed priority failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/outreach/log-activity")
async def log_outreach_activity(request: Request):
    """
    Log an outreach activity to local DB and optionally Bullhorn.

    Accepts: {contact_name, activity_type, notes, channel, program, outcome, ...}
    """
    try:
        from Engine7_BullhornETL.scripts.bullhorn_activity_logger import (
            BullhornActivityLogger,
        )

        body = await request.json()
        bh_logger = BullhornActivityLogger()
        result = await asyncio.to_thread(
            bh_logger.log_outreach,
            contact_name=body.get("contact_name", ""),
            activity_type=body.get("activity_type", "note"),
            notes=body.get("notes", ""),
            contact_email=body.get("contact_email", ""),
            company=body.get("company", ""),
            channel=body.get("channel", ""),
            program=body.get("program", ""),
            outcome=body.get("outcome", ""),
            sync_to_bullhorn=body.get("sync_to_bullhorn", True),
        )
        return result
    except Exception as e:
        logger.error(f"Outreach log failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/outreach/activity-log")
async def get_outreach_activity_log(
    contact: str = Query(None, description="Filter by contact name"),
    limit: int = Query(50, description="Max results"),
):
    """Get outreach activity log."""
    try:
        from Engine7_BullhornETL.scripts.bullhorn_activity_logger import (
            BullhornActivityLogger,
        )

        bh_logger = BullhornActivityLogger()
        activities = await asyncio.to_thread(bh_logger.get_activity_log, contact_name=contact, limit=limit)
        return {"activities": activities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/outreach/stats")
async def get_outreach_stats():
    """Get outreach activity statistics."""
    try:
        from Engine7_BullhornETL.scripts.bullhorn_activity_logger import (
            BullhornActivityLogger,
        )

        bh_logger = BullhornActivityLogger()
        return await asyncio.to_thread(bh_logger.get_stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/claims/velocity")
async def get_claim_velocity(
    days: int = Query(30, description="Lookback period in days"),
):
    """Get claim velocity metrics."""
    try:
        tracker = _get_claim_tracker()
        return await asyncio.to_thread(tracker.get_velocity, days=days)
    except Exception as e:
        logger.error(f"Claim velocity failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# AGENT ENDPOINTS
# =========================================


@app.get("/agent/program")
async def agent_program_intel(q: str = Query(..., description="Query")):
    """Program intelligence agent."""
    result = await program_agent.process(q)
    return {
        "agent": result.agent_name,
        "response": result.content,
        "confidence": result.confidence,
    }


@app.get("/agent/company")
async def agent_company_research(q: str = Query(..., description="Query")):
    """Company research agent."""
    result = await company_agent.process(q)
    return {
        "agent": result.agent_name,
        "response": result.content,
        "confidence": result.confidence,
    }


@app.get("/agent/contact")
async def agent_contact_finder(q: str = Query(..., description="Query")):
    """Contact finder agent."""
    result = await contact_agent.process(q)
    return {
        "agent": result.agent_name,
        "response": result.content,
        "confidence": result.confidence,
    }


@app.get("/agent/strategy")
async def agent_bd_strategy(q: str = Query(..., description="Query")):
    """BD strategy agent."""
    result = await strategy_agent.process(q)
    return {
        "agent": result.agent_name,
        "response": result.content,
        "confidence": result.confidence,
    }


# =========================================
# ORCHESTRATION ENDPOINTS
# =========================================


@app.get("/workflow/capture")
async def workflow_capture_strategy(
    opportunity: str = Query(..., description="Opportunity name"),
):
    """Run capture strategy workflow."""
    result = await orchestrator.capture_strategy_workflow(opportunity)
    return {
        "workflow": result.workflow,
        "success": result.success,
        "agents_used": result.agents_used,
        "output": result.final_output,
    }


@app.get("/workflow/competitor")
async def workflow_competitor_analysis(
    company: str = Query(..., description="Company name"),
):
    """Run competitor analysis workflow."""
    result = await orchestrator.competitor_analysis_workflow(company)
    return {
        "workflow": result.workflow,
        "success": result.success,
        "agents_used": result.agents_used,
        "output": result.final_output,
    }


@app.get("/workflow/quick")
async def workflow_quick_intel(q: str = Query(..., description="Query")):
    """Quick intelligence query."""
    result = await orchestrator.quick_intel_workflow(q)
    return {
        "workflow": result.workflow,
        "success": result.success,
        "agents_used": result.agents_used,
        "output": result.final_output,
    }


# =========================================
# PAGEINDEX ENDPOINTS
# =========================================


@app.post("/pageindex/index")
async def index_for_audit(doc_id: str = Query(...), content: str = Query(...)):
    """Index document for audit trail."""
    success = await asyncio.to_thread(pageindex.index_document, doc_id, content)
    return {"success": success, "doc_id": doc_id}


@app.get("/pageindex/query")
async def query_with_audit(q: str = Query(...), doc_ids: Optional[str] = Query(None)):
    """Query with audit trail."""
    docs = doc_ids.split(",") if doc_ids else None
    result = pageindex.query(q, docs)
    trail = pageindex.get_audit_trail(result)
    return {
        "answer": result.final_answer,
        "confidence": result.confidence,
        "audit_trail": trail,
    }


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
    response = await asyncio.to_thread(rag_engine.ask_about_program, program_name)
    return response.to_dict()


@app.get("/company/{company_name}")
async def get_company_intel(company_name: str):
    """Get intelligence about a company/contractor."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    response = await asyncio.to_thread(rag_engine.ask_about_company, company_name)
    return response.to_dict()


@app.get("/contacts/at/{company_name}")
async def get_contacts_at_company(company_name: str, limit: int = 20):
    """Find contacts at a specific company."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")
    results = await asyncio.to_thread(store.find_contacts_at_company, company_name, limit)
    return {
        "company": company_name,
        "contacts": [r.to_dict() for r in results],
        "count": len(results),
    }


@app.get("/jobs/for/{program_name}")
async def get_jobs_for_program(program_name: str, limit: int = 20):
    """Find jobs associated with a program."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")
    results = await asyncio.to_thread(store.find_jobs_for_program, program_name, limit)
    return {
        "program": program_name,
        "jobs": [r.to_dict() for r in results],
        "count": len(results),
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
        results = await asyncio.to_thread(indexer.index_all)
        total_indexed = sum(r.indexed for r in results)
        total_errors = sum(r.errors for r in results)
        total_duration = sum(r.duration_seconds for r in results)

        return IndexResponse(
            success=total_errors == 0,
            message=f"Indexed {total_indexed} items across {len(results)} collections",
            indexed=total_indexed,
            errors=total_errors,
            duration_seconds=total_duration,
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
        index_methods = {
            "jobs": indexer.index_jobs,
            "contacts": indexer.index_contacts,
            "programs": indexer.index_programs,
            "documents": indexer.index_documents,
            "activities": indexer.index_activities,
        }
        index_fn = index_methods.get(collection)
        if not index_fn:
            raise HTTPException(
                status_code=400, detail=f"Unknown collection: {collection}"
            )

        result = await asyncio.to_thread(index_fn)

        return IndexResponse(
            success=result.errors == 0,
            message=f"Indexed {result.indexed} items to {collection}",
            indexed=result.indexed,
            errors=result.errors,
            duration_seconds=result.duration_seconds,
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
        analyze_program as run_analyze_program,
        prepare_outreach as run_prepare_outreach,
        generate_weekly_intel as run_weekly_intel,
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
            agent_count=0,
        )

    team = get_bd_agent_team()
    return AgentStatusResponse(
        crewai_available=CREWAI_AVAILABLE,
        langchain_anthropic_available=True,  # If we got here, it's available
        agents_initialized=team.available,
        agent_count=4 if team.available else 0,
    )


@app.post("/agents/analyze-program")
async def api_analyze_program(
    request: ProgramAnalysisRequest = None,
    program_name: str = Query(None, description="Program name (alternative to body)"),
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
            detail="CrewAI workflows not available. Install: pip install crewai langchain-anthropic",
        )

    # Get program name from body or query param
    name = request.program_name if request else program_name
    if not name:
        raise HTTPException(status_code=400, detail="program_name is required")

    try:
        result = await run_analyze_program(name)

        if not result.get("success"):
            raise HTTPException(
                status_code=500, detail=result.get("error", "Unknown error")
            )

        return {
            "success": True,
            "program": name,
            "playbook": result.get("playbook"),
            "talking_points": result.get("talking_points", []),
            "opportunity_score": result.get("opportunity_score", 0),
            "priority_contacts": result.get("priority_contacts", []),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Program analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/prepare-outreach")
async def api_prepare_outreach(
    request: OutreachPrepRequest = None,
    contact_name: str = Query(None, description="Contact name (alternative to body)"),
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
            detail="CrewAI workflows not available. Install: pip install crewai langchain-anthropic",
        )

    # Get contact name from body or query param
    name = request.contact_name if request else contact_name
    if not name:
        raise HTTPException(status_code=400, detail="contact_name is required")

    try:
        result = await run_prepare_outreach(name)

        if not result.get("success"):
            raise HTTPException(
                status_code=500, detail=result.get("error", "Unknown error")
            )

        return {
            "success": True,
            "contact": name,
            "call_script": result.get("call_script"),
            "email_template": result.get("email_template"),
            "linkedin_message": result.get("linkedin_message"),
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
            detail="CrewAI workflows not available. Install: pip install crewai langchain-anthropic",
        )

    try:
        result = await run_weekly_intel()

        if not result.get("success"):
            raise HTTPException(
                status_code=500, detail=result.get("error", "Unknown error")
            )

        return {
            "success": True,
            "executive_summary": result.get("executive_summary"),
            "hot_programs": result.get("hot_programs", []),
            "new_opportunities": result.get("new_opportunities", []),
            "action_items": result.get("action_items", []),
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
        from Engine6_QA.scripts.qa_feedback import ReviewQueue

        queue = ReviewQueue()
        stats = await asyncio.to_thread(queue.get_stats)
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
            "items": items[offset : offset + limit],
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


@app.post("/ingest/docling")
def ingest_docling_document(
    file: UploadFile = File(...),
    collection: str = Form("federal_contracts"),
    doc_type: str = Form("unknown"),
    max_tokens: int = Form(512),
):
    """Ingest a PDF/DOCX via Docling: convert, chunk, embed, upsert to Qdrant."""
    import tempfile

    try:
        from Engine8_Knowledge.processors.docling_processor import (
            ingest_document_to_qdrant,
        )
    except ImportError as e:
        raise HTTPException(
            status_code=503, detail=f"Docling processor not available: {e}"
        )

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
            result["pipeline"] = {
                "is_running": False,
                "last_run": None,
                "total_runs": 0,
            }
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


def _determine_job_stage(payload: dict) -> str:
    """Determine pipeline stage from job payload fields."""
    stage = payload.get("pipeline_stage")
    if stage:
        return stage
    if payload.get("mapped_program") or payload.get("Mapped Program"):
        if payload.get("contact") or payload.get("key_contact"):
            return "contacts_found"
        return "mapped"
    return "scraped"


@app.get("/pipeline/status")
async def get_pipeline_status():
    """Get job pipeline stage counts from Qdrant jobs collection for the Kanban board."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")

    try:
        stages = {
            "scraped": {"count": 0, "latest": None},
            "mapped": {"count": 0, "latest": None},
            "contacts_found": {"count": 0, "latest": None},
            "outreach_active": {"count": 0, "latest": None},
            "meeting_set": {"count": 0, "latest": None},
            "req_obtained": {"count": 0, "latest": None},
        }
        total_jobs = 0
        last_scrape = None
        offset = None

        while True:
            results, next_offset = store.client.scroll(
                collection_name="jobs",
                limit=1000,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in results:
                total_jobs += 1
                payload = point.payload or {}
                stage = _determine_job_stage(payload)
                if stage in stages:
                    stages[stage]["count"] += 1
                    date_val = (
                        payload.get("indexed_at")
                        or payload.get("date_scraped")
                        or payload.get("date_posted")
                    )
                    if date_val:
                        if (
                            not stages[stage]["latest"]
                            or date_val > stages[stage]["latest"]
                        ):
                            stages[stage]["latest"] = date_val
                        if not last_scrape or date_val > last_scrape:
                            last_scrape = date_val
                else:
                    stages["scraped"]["count"] += 1

            if next_offset is None:
                break
            offset = next_offset

        return {
            "stages": stages,
            "total_jobs": total_jobs,
            "last_scrape": last_scrape,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Pipeline status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class StageUpdateRequest(BaseModel):
    stage: str = Field(..., description="Pipeline stage")


VALID_STAGES = {
    "scraped",
    "mapped",
    "contacts_found",
    "outreach_active",
    "meeting_set",
    "req_obtained",
}


@app.patch("/jobs/{point_id}/stage")
async def update_job_stage(point_id: str, request: StageUpdateRequest):
    """Update a job's pipeline_stage in Qdrant without re-embedding."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")
    if request.stage not in VALID_STAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage. Must be one of: {sorted(VALID_STAGES)}",
        )

    try:
        # Handle both int and UUID point IDs
        pid = int(point_id) if point_id.isdigit() else point_id
        store.client.set_payload(
            collection_name="jobs",
            payload={
                "pipeline_stage": request.stage,
                "stage_updated_at": datetime.now().isoformat(),
            },
            points=[pid],
        )
        return {"success": True, "point_id": point_id, "stage": request.stage}
    except Exception as e:
        logger.error(f"Update job stage error: {e}")
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
    state["current_run"] = {
        "run_id": run_id,
        "started_at": datetime.now().isoformat(),
        "config": request.dict(),
    }
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
        return {
            "alerts": engine.get_recent_alerts(limit),
            "count": len(engine.get_recent_alerts(limit)),
        }
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        return {"alerts": [], "count": 0, "error": str(e)}


# =========================================
# ANALYTICS & AGENT STATS ENDPOINTS
# =========================================

import time as _time

_analytics_cache: Dict[str, Any] = {"data": None, "expires": 0.0}


@app.get("/analytics/summary")
async def analytics_summary():
    """Pre-aggregated analytics data with 5-minute cache."""
    now = _time.time()
    if _analytics_cache["data"] and now < _analytics_cache["expires"]:
        return _analytics_cache["data"]

    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")

    try:
        contacts_by_program: Dict[str, int] = {}
        contacts_by_tier: Dict[str, int] = {}
        priority_distribution: Dict[str, Dict[str, int]] = {}
        offset = None

        while True:
            results, next_offset = store.client.scroll(
                collection_name="contacts",
                limit=500,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in results:
                payload = point.payload or {}
                programs_str = payload.get("Programs", "")
                progs = (
                    [p.strip() for p in programs_str.split(",") if p.strip()]
                    if programs_str
                    else []
                )

                for prog in progs:
                    contacts_by_program[prog] = contacts_by_program.get(prog, 0) + 1

                tier = payload.get("influence_tier") or payload.get("Tier") or "Unknown"
                contacts_by_tier[tier] = contacts_by_tier.get(tier, 0) + 1

                priority = payload.get("priority") or "standard"
                for prog in progs:
                    if prog not in priority_distribution:
                        priority_distribution[prog] = {}
                    priority_distribution[prog][priority] = (
                        priority_distribution[prog].get(priority, 0) + 1
                    )

            if next_offset is None:
                break
            offset = next_offset

        # Jobs by stage
        jobs_by_stage: Dict[str, int] = {}
        offset = None
        while True:
            results, next_offset = store.client.scroll(
                collection_name="jobs",
                limit=1000,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in results:
                stage = _determine_job_stage(point.payload or {})
                jobs_by_stage[stage] = jobs_by_stage.get(stage, 0) + 1
            if next_offset is None:
                break
            offset = next_offset

        # Collection health
        collection_health = []
        try:
            coll_stats = store.get_collection_stats()
            for name, stats in coll_stats.items():
                if isinstance(stats, dict):
                    collection_health.append(
                        {
                            "name": name,
                            "vectors": stats.get("points_count", 0),
                            "status": stats.get("status", "unknown").lower(),
                        }
                    )
        except Exception:
            pass

        # Limit and sort
        contacts_by_program = dict(
            sorted(contacts_by_program.items(), key=lambda x: x[1], reverse=True)[:50]
        )
        priority_distribution = dict(
            sorted(
                priority_distribution.items(),
                key=lambda x: sum(x[1].values()),
                reverse=True,
            )[:20]
        )

        result = {
            "contacts_by_program": contacts_by_program,
            "contacts_by_tier": contacts_by_tier,
            "priority_distribution": priority_distribution,
            "jobs_by_stage": jobs_by_stage,
            "collection_health": collection_health,
            "timestamp": datetime.now().isoformat(),
        }

        _analytics_cache["data"] = result
        _analytics_cache["expires"] = now + 300
        return result
    except Exception as e:
        logger.error(f"Analytics summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/funnel")
async def analytics_funnel():
    """Revenue pipeline funnel: Discovered -> Scored -> Outreach -> Meeting -> Placement."""
    try:
        funnel = {
            "discovered": 0,
            "scored": 0,
            "outreach": 0,
            "meeting": 0,
            "placement": 0,
        }

        # Count total programs/opportunities (discovered)
        try:
            prog_info = store.client.get_collection("programs")
            funnel["discovered"] = prog_info.points_count or 0
        except Exception:
            pass

        # Count scored items (jobs with bd_priority_score)
        try:
            job_info = store.client.get_collection("jobs")
            funnel["scored"] = job_info.points_count or 0
        except Exception:
            pass

        # Count outreach activities
        try:
            act_info = store.client.get_collection("activities")
            funnel["outreach"] = min(act_info.points_count or 0, funnel["scored"])
        except Exception:
            pass

        # Count meetings (from activity log)
        try:
            from Engine7_BullhornETL.scripts.bullhorn_activity_logger import (
                BullhornActivityLogger,
            )

            bh_logger = BullhornActivityLogger()
            stats = bh_logger.get_stats()
            funnel["meeting"] = stats.get("by_type", {}).get("meeting", 0)
            funnel["placement"] = stats.get("by_type", {}).get("placement", 0)
        except Exception:
            pass

        return {
            "funnel": funnel,
            "stages": ["discovered", "scored", "outreach", "meeting", "placement"],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/system/cross-repo-health")
async def cross_repo_health():
    """Check health of all 3 repos: BD-Engine, N8N-Builder, data-scraper."""
    import httpx

    services = {}

    # BD-Engine (self)
    services["bd_engine"] = {
        "name": "BD-Engine",
        "port": 8100,
        "status": "online",
        "url": "http://localhost:8100",
    }

    # N8N-Builder
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://localhost:8300/health")
            services["n8n_builder"] = {
                "name": "N8N-Builder",
                "port": 8300,
                "status": "online" if resp.status_code == 200 else "degraded",
                "url": "http://localhost:8300",
            }
    except Exception:
        services["n8n_builder"] = {
            "name": "N8N-Builder",
            "port": 8300,
            "status": "offline",
            "url": "http://localhost:8300",
        }

    # data-scraper (no API, check if scheduler is running)
    services["data_scraper"] = {
        "name": "data-scraper",
        "port": None,
        "status": "no_api",
        "url": None,
        "note": "Data pipeline — no persistent API",
    }

    # Qdrant
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://localhost:6333/collections")
            data = resp.json()
            collections = {
                c["name"]: True for c in data.get("result", {}).get("collections", [])
            }
            services["qdrant"] = {
                "name": "Qdrant",
                "port": 6333,
                "status": "online",
                "collections": len(collections),
            }
    except Exception:
        services["qdrant"] = {"name": "Qdrant", "port": 6333, "status": "offline"}

    # N8N Cloud (optional)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("https://n8n.cloud/api/v1/health")
            services["n8n_cloud"] = {"name": "N8N Cloud", "status": "online"}
    except Exception:
        services["n8n_cloud"] = {"name": "N8N Cloud", "status": "unknown"}

    # Overall status
    online_count = sum(1 for s in services.values() if s.get("status") == "online")
    total = len(services)

    return {
        "services": services,
        "overall": "healthy"
        if online_count >= 3
        else "degraded"
        if online_count >= 2
        else "critical",
        "online": online_count,
        "total": total,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/predictions/recompetes")
async def get_recompete_predictions(
    months: int = Query(12, description="Months ahead"),
):
    """Predict upcoming contract recompetes using the RecompetePredictor.

    Scans Qdrant programs, N8N-Builder federal_programs.db, and Bullhorn
    for contracts expiring within the horizon.  Cross-references PTS past
    performance and assigns priority (critical/high/medium/low).
    """
    try:
        predictor = _get_recompete_predictor()
        predictions = predictor.get_recompete_predictions(months=months, limit=50)
        return predictions
    except Exception as e:
        logger.error(f"Recompete prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions/best-channels")
async def get_best_channels():
    """Get best outreach channels by analyzing activity outcomes.

    Uses the RecompetePredictor's channel analysis, which queries the
    Qdrant activities collection for outreach records and computes
    per-channel success rates.  Falls back to Bullhorn activity stats.
    """
    try:
        predictor = _get_recompete_predictor()
        result = predictor.get_best_channels()
        return result
    except Exception as e:
        logger.warning(f"Predictor best-channels failed, falling back: {e}")
        # Fallback to Bullhorn activity logger
        try:
            from Engine7_BullhornETL.scripts.bullhorn_activity_logger import (
                BullhornActivityLogger,
            )

            bh_logger = BullhornActivityLogger()
            stats = bh_logger.get_stats()
            by_type = stats.get("by_type", {})

            channels = []
            for channel, count in sorted(
                by_type.items(), key=lambda x: x[1], reverse=True
            ):
                channels.append(
                    {
                        "channel": channel,
                        "total": count,
                        "success_rate": 0.0,
                        "avg_response_days": 0.0,
                    }
                )

            return {
                "channels": channels,
                "recommendation": "Using Bullhorn activity counts as fallback. Build more outreach history for channel effectiveness analysis.",
                "data_points": stats.get("total_logged", 0),
            }
        except Exception as fallback_err:
            raise HTTPException(status_code=500, detail=str(fallback_err))


@app.post("/predictions/scoring-recalibrate")
async def recalibrate_scoring(request: Request):
    """Recalibrate BD scoring weights from conversion outcome data.

    POST body: { "conversion_data": [ { "item": {...}, "outcome": "meeting", "original_score": 75 } ], "learning_rate": 0.1 }
    """
    try:
        from Engine5_Scoring.scripts.bd_scoring import recalibrate

        body = await request.json()
        conversion_data = body.get("conversion_data", [])
        learning_rate = body.get("learning_rate", 0.1)

        result = recalibrate(conversion_data, learning_rate=learning_rate)
        return result
    except Exception as e:
        logger.error(f"Scoring recalibration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/tasks/stats")
async def get_agent_task_stats():
    """Aggregated agent task statistics for the Analytics dashboard."""
    try:
        tasks_file = Path(__file__).parent.parent / "outputs" / "agent_tasks.json"
        if not tasks_file.exists():
            return {
                "total_tasks": 0,
                "by_type": {},
                "by_status": {},
                "by_date": {},
                "avg_duration_seconds": 0,
                "timestamp": datetime.now().isoformat(),
            }

        with open(tasks_file, "r") as f:
            tasks = json.load(f)

        by_type: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        by_date: Dict[str, int] = {}
        durations: list = []

        task_list = tasks if isinstance(tasks, list) else tasks.get("tasks", [])
        for task in task_list:
            task_type = task.get("type", "unknown")
            by_type[task_type] = by_type.get(task_type, 0) + 1

            status = task.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

            started = task.get("started_at", "")
            if started:
                date_key = started[:10]
                by_date[date_key] = by_date.get(date_key, 0) + 1

            duration = task.get("duration_seconds")
            if duration:
                durations.append(duration)

        return {
            "total_tasks": len(task_list),
            "by_type": by_type,
            "by_status": by_status,
            "by_date": dict(sorted(by_date.items(), reverse=True)[:30]),
            "avg_duration_seconds": round(sum(durations) / len(durations), 1)
            if durations
            else 0,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Agent tasks stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# SSE STREAMING ENDPOINTS FOR AGENT TASKS
# =========================================

_task_events: Dict[str, list] = {}  # task_id -> list of events


@app.post("/agents/tasks/create")
async def create_agent_task(request: Request):
    """Create a new agent task and return task_id for SSE streaming."""
    body = await request.json()
    task_type = body.get("type", "research")
    query = body.get("query", "")
    task_id = f"task_{int(_time.time() * 1000)}"

    _task_events[task_id] = [
        {
            "event": "created",
            "data": {
                "task_id": task_id,
                "type": task_type,
                "query": query,
                "status": "pending",
            },
        }
    ]

    return {"task_id": task_id, "status": "created"}


@app.post("/agents/tasks/{task_id}/event")
async def push_task_event(task_id: str, request: Request):
    """Push an event to a task's stream (called by agent workers)."""
    body = await request.json()
    if task_id not in _task_events:
        _task_events[task_id] = []
    _task_events[task_id].append(body)
    return {"ok": True}


@app.get("/agents/tasks/{task_id}/stream")
async def stream_task(task_id: str):
    """SSE endpoint - frontend connects for real-time agent updates."""

    async def event_generator():
        sent = 0
        timeout = 300
        start = _time.time()

        while _time.time() - start < timeout:
            events = _task_events.get(task_id, [])
            while sent < len(events):
                event = events[sent]
                event_type = event.get("event", "update")
                data = json.dumps(event.get("data", event))
                yield f"event: {event_type}\ndata: {data}\n\n"
                sent += 1

                if event_type in ("complete", "error"):
                    return

            await asyncio.sleep(0.5)

        yield f"event: timeout\ndata: {json.dumps({'message': 'Stream timed out'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# =========================================
# AI CHAT COMPLETION PROXY (RAG + OpenAI)
# =========================================

_openai_client = None


def _get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


_BD_SYSTEM_PROMPT = (
    "You are the PTS BD Intelligence Assistant. You have access to data about "
    "federal defense programs, contacts at prime contractors (GDIT, Leidos, SAIC, NGC, etc.), "
    "job postings, and outreach sequences. Answer questions using the context provided. "
    "Always be specific — mention names, programs, locations, and tier levels when available. "
    "If you reference a contact, include their program and tier."
)


def _rag_retrieve(user_msg: str, collection: str = "contacts", limit: int = 5) -> str:
    """Retrieve RAG context using hybrid search (BM25 + dense + RRF) with memory."""
    if not store or not user_msg:
        return ""
    try:
        chunks: list[str] = []

        # 1. Memory context — prepend relevant memories
        if memory:
            try:
                mem_results = memory.get_context(user_msg, limit=3)
                for r in mem_results:
                    mem_text = r.get("memory", r.get("content", str(r)))
                    if mem_text:
                        chunks.append(f"[Memory]: {str(mem_text)[:300]}")
            except Exception as e:
                logger.debug("memory_context_failed", error=str(e))

        # 2. Hybrid search (BM25 + semantic + RRF) with dense-only fallback
        if retriever:
            try:
                results = retriever.search(
                    query=user_msg,
                    collection=collection,
                    limit=limit,
                    use_hybrid=True,
                    use_rerank=False,
                )
                for r in results:
                    name = r.metadata.get(
                        "Name",
                        r.metadata.get(
                            "name",
                            r.metadata.get("Program Name", r.metadata.get("title", "")),
                        ),
                    )
                    text = r.text[:300] if r.text else ""
                    chunks.append(f"[{name}] ({r.source}): {text}")
                return "\n".join(chunks)
            except Exception as e:
                logger.debug("hybrid_search_failed_falling_back", error=str(e))

        # 3. Dense-only fallback
        query_embedding = store._generate_embedding(user_msg)
        search_result = store.client.query_points(
            collection_name=collection,
            query=query_embedding,
            limit=limit,
            with_payload=True,
        )
        for pt in search_result.points:
            p = pt.payload or {}
            name = p.get(
                "Name", p.get("name", p.get("Program Name", p.get("title", "")))
            )
            text = p.get("text", p.get("content", str(p)[:500]))
            chunks.append(f"[{name}]: {text[:300]}")
        return "\n".join(chunks)
    except Exception as e:
        return f"(RAG search failed: {e})"


@app.post("/ai/chat")
async def ai_chat(request: Request):
    """Non-streaming chat with RAG context from Qdrant."""
    body = await request.json()
    messages = body.get("messages", [])
    collection = body.get("collection", "contacts")
    use_rag = body.get("use_rag", True)

    user_msg = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )

    rag_context = _rag_retrieve(user_msg, collection) if use_rag else ""

    system_prompt = _BD_SYSTEM_PROMPT
    if rag_context:
        system_prompt += f"\n\nRelevant context from the BD database:\n{rag_context}"

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    return {"messages": full_messages, "rag_context": rag_context}


@app.post("/ai/chat/stream")
async def ai_chat_stream(request: Request):
    """Streaming chat with RAG — returns SSE with OpenAI completions."""
    body = await request.json()
    messages = body.get("messages", [])
    collection = body.get("collection", "contacts")
    user_msg = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )

    rag_context = _rag_retrieve(user_msg, collection)

    system_prompt = _BD_SYSTEM_PROMPT
    if rag_context:
        system_prompt += f"\n\nRelevant context from the BD database:\n{rag_context}"

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    client = _get_openai()

    async def generate():
        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=full_messages,
                stream=True,
                max_tokens=1500,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    data = json.dumps({"content": chunk.choices[0].delta.content})
                    yield f"data: {data}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# =========================================
# GRAPH DATA ENDPOINT (V6 — enriched)
# =========================================


def _get_unified_db():
    """Get a connection to the unified federal contracts DB."""
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "unified_federal_contracts.db"
    )
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/graph/data")
async def get_graph_data(
    limit: int = 800,
    node_types: Optional[str] = None,
    domain_filter: Optional[str] = None,
    min_quality: Optional[float] = None,
    include_quality: bool = False,
    include_domain_tags: bool = False,
):
    """Return graph-ready nodes and edges for the frontend Graph Explorer (V6).

    Supports 4 node types: contact, program, contractor, job.
    Uses Supabase when USE_SUPABASE=true, falls back to Qdrant.
    """
    # Supabase fast-path
    if USE_SUPABASE and SUPABASE_CLIENT_AVAILABLE:
        try:
            types_list = None
            if node_types:
                types_list = [t.strip() for t in node_types.split(",")]
            return sb_get_graph_data(limit, types_list, domain_filter, min_quality)
        except Exception as e:
            logger.warning(f"Supabase graph fallback to Qdrant: {e}")

    if not store:
        raise HTTPException(status_code=503, detail="Knowledge store not initialized")

    requested_types = set()
    if node_types:
        requested_types = set(t.strip() for t in node_types.split(","))
    else:
        requested_types = {"contact", "program", "contractor", "job"}

    domain_filters = set()
    if domain_filter:
        domain_filters = set(t.strip() for t in domain_filter.split(","))

    nodes = []
    edges = []
    program_ids = set()
    node_id_set = set()

    # Load quality scores and domain tags from unified DB if requested
    quality_map = {}  # name -> score
    domain_map = {}   # program_name -> tags list
    if include_quality or include_domain_tags or min_quality is not None or domain_filters:
        udb = _get_unified_db()
        if udb:
            try:
                if include_quality or min_quality is not None:
                    name_col_map = {"contacts": "full_name", "programs": "program_name", "companies": "name"}
                    for table in ["contacts", "programs", "companies"]:
                        try:
                            name_col = name_col_map[table]
                            cursor = udb.execute(
                                f"SELECT {name_col}, data_quality_score FROM {table} WHERE data_quality_score IS NOT NULL"
                            )
                            for row in cursor:
                                quality_map[row[0]] = row[1]
                        except Exception:
                            pass
                if include_domain_tags or domain_filters:
                    try:
                        cursor = udb.execute(
                            "SELECT program_name, domain_tags FROM programs WHERE domain_tags IS NOT NULL AND domain_tags != ''"
                        )
                        for row in cursor:
                            try:
                                tags = json.loads(row[1]) if isinstance(row[1], str) else row[1]
                                domain_map[row[0]] = tags
                            except (json.JSONDecodeError, TypeError):
                                pass
                    except Exception:
                        pass
            finally:
                udb.close()

    try:
        # ── Contacts ──
        if "contact" in requested_types:
            contacts, _ = store.client.scroll(
                collection_name="contacts", limit=limit, with_payload=True
            )
            for c in contacts:
                p = c.payload or {}
                name = p.get("\ufeffContact Name", p.get("Contact Name", p.get("name", "")))

                # Quality filter
                q_score = quality_map.get(name)
                if min_quality is not None and (q_score is None or q_score < min_quality):
                    continue

                node_id = f"contact_{c.id}"
                node = {
                    "id": node_id,
                    "type": "contact",
                    "name": name,
                    "title": p.get("Job Title", p.get("title", "")),
                    "tier": p.get("Hierarchy Tier", p.get("tier", "")),
                    "priority": p.get("BD Priority", ""),
                    "program": p.get("Programs", p.get("program", "")),
                    "company": p.get("Company", p.get("company", "")),
                    "location": p.get("Location Hub", p.get("location", "")),
                    "email": p.get("email", ""),
                    "phone": p.get("phone", ""),
                    "linkedin": p.get("linkedin", ""),
                }
                if include_quality and q_score is not None:
                    node["data_quality_score"] = round(q_score, 1)
                nodes.append(node)
                node_id_set.add(node_id)

                # Edges to programs
                programs_str = p.get("Programs", p.get("program", ""))
                if programs_str:
                    for prog in str(programs_str).split(","):
                        prog = prog.strip()
                        if prog:
                            prog_id = f"program_{prog}"
                            program_ids.add(prog)
                            edges.append({"source": node_id, "target": prog_id, "type": "WORKS_ON"})

        # ── Programs ──
        if "program" in requested_types:
            programs, _ = store.client.scroll(
                collection_name="programs", limit=200, with_payload=True
            )
            for pr in programs:
                p = pr.payload or {}
                name = p.get("Program Name", p.get("name", ""))
                prime = p.get("Prime Contractor", p.get("prime", ""))
                tags = domain_map.get(name, [])

                # Domain filter
                if domain_filters and not any(t in domain_filters for t in tags):
                    continue

                q_score = quality_map.get(name)
                if min_quality is not None and (q_score is None or q_score < min_quality):
                    continue

                node = {
                    "id": f"program_{name}",
                    "type": "program",
                    "name": name,
                    "prime": prime,
                    "value": p.get("Contract Value", ""),
                    "agency": p.get("Agency Owner", p.get("agency", "")),
                    "acronym": p.get("Acronym", ""),
                }
                if include_quality and q_score is not None:
                    node["data_quality_score"] = round(q_score, 1)
                if include_domain_tags and tags:
                    node["domain_tags"] = tags
                nodes.append(node)
                node_id_set.add(f"program_{name}")
                program_ids.discard(name)

            # Placeholder program nodes for referenced but not in collection
            for prog_name in program_ids:
                tags = domain_map.get(prog_name, [])
                if domain_filters and not any(t in domain_filters for t in tags):
                    continue
                node = {
                    "id": f"program_{prog_name}",
                    "type": "program",
                    "name": prog_name,
                    "prime": "",
                    "value": "",
                    "agency": "",
                    "acronym": "",
                }
                if include_domain_tags and tags:
                    node["domain_tags"] = tags
                nodes.append(node)
                node_id_set.add(f"program_{prog_name}")

        # ── Contractors & Jobs from BD Knowledge Graph ──
        bg = get_bd_knowledge_graph()
        if bg:
            if "contractor" in requested_types:
                contractor_entities = bg.get_entities_by_type("Contractor")
                for e in contractor_entities[:min(limit, 300)]:
                    nid = f"contractor_{e.id}"
                    q_score = quality_map.get(e.name)
                    if min_quality is not None and (q_score is None or q_score < min_quality):
                        continue
                    node = {
                        "id": nid,
                        "type": "contractor",
                        "name": e.name,
                        "headquarters": e.properties.get("headquarters", ""),
                        "company_type": e.properties.get("type", ""),
                    }
                    if include_quality and q_score is not None:
                        node["data_quality_score"] = round(q_score, 1)
                    nodes.append(node)
                    node_id_set.add(nid)

            if "job" in requested_types:
                job_entities = bg.get_entities_by_type("Job")
                for e in job_entities[:min(limit, 200)]:
                    nid = f"job_{e.id}"
                    node = {
                        "id": nid,
                        "type": "job",
                        "name": e.name,
                        "location": e.properties.get("location", ""),
                        "clearance": e.properties.get("clearance", ""),
                        "bd_score": e.properties.get("bd_score"),
                        "company": e.properties.get("company", ""),
                    }
                    nodes.append(node)
                    node_id_set.add(nid)

            # Add graph-based edges (PRIMES_ON, COMPETES_WITH, HAS_OPENING, etc.)
            for rel_type in ["PRIMES_ON", "COMPETES_WITH", "HAS_OPENING", "POSTED_BY", "SUBS_TO"]:
                try:
                    cursor = bg.conn.execute(
                        "SELECT from_entity_id, to_entity_id FROM relationships WHERE type = ?",
                        (rel_type,)
                    )
                    for row in cursor:
                        from_e = bg._entity_cache.get(row[0])
                        to_e = bg._entity_cache.get(row[1])
                        if not from_e or not to_e:
                            continue
                        prefix_from = from_e.type.lower() if from_e.type.lower() in ("contractor", "program", "contact", "job") else "entity"
                        prefix_to = to_e.type.lower() if to_e.type.lower() in ("contractor", "program", "contact", "job") else "entity"
                        src = f"{prefix_from}_{from_e.id}"
                        tgt = f"{prefix_to}_{to_e.id}"
                        if src in node_id_set and tgt in node_id_set:
                            edges.append({"source": src, "target": tgt, "type": rel_type})
                except Exception:
                    pass

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building graph: {str(e)}")

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }


# =========================================
# COMPETITION GRAPH ENDPOINT (V6)
# =========================================


@app.get("/graph/competition")
async def get_competition_graph(
    program_filter: Optional[str] = None,
    limit: int = 200,
):
    """Competition network: contractors competing on shared programs."""
    # Supabase fast-path
    if USE_SUPABASE and SUPABASE_CLIENT_AVAILABLE:
        try:
            return sb_get_competition_graph(program_filter, limit)
        except Exception as e:
            logger.warning(f"Supabase competition fallback: {e}")

    bg = get_bd_knowledge_graph()
    if not bg:
        raise HTTPException(status_code=503, detail="Knowledge graph not available")

    nodes = []
    edges = []
    contractor_nodes = {}  # id -> node dict
    program_nodes = {}     # id -> node dict

    try:
        # Get all PRIMES_ON relationships to build the competition network
        cursor = bg.conn.execute(
            "SELECT from_entity_id, to_entity_id FROM relationships WHERE type = 'PRIMES_ON'"
        )
        # Map: program_id -> [contractor_ids]
        program_contractors = {}
        for row in cursor:
            contractor_id, program_id = row[0], row[1]
            program_contractors.setdefault(program_id, []).append(contractor_id)

        # Get domain tags from unified DB for program filtering
        domain_map = {}
        udb = _get_unified_db()
        if udb:
            try:
                cur = udb.execute(
                    "SELECT program_name, domain_tags FROM programs WHERE domain_tags IS NOT NULL AND domain_tags != ''"
                )
                for r in cur:
                    try:
                        domain_map[r[0]] = json.loads(r[1]) if isinstance(r[1], str) else r[1]
                    except (json.JSONDecodeError, TypeError):
                        pass
            finally:
                udb.close()

        # Build nodes and COMPETES_WITH edges
        competition_pairs = {}  # (c1, c2) -> [shared_program_names]

        for prog_id, c_ids in program_contractors.items():
            prog_entity = bg._entity_cache.get(prog_id)
            if not prog_entity:
                continue

            prog_name = prog_entity.name
            prog_tags = domain_map.get(prog_name, [])

            # Apply program filter
            if program_filter and program_filter.lower() not in prog_name.lower():
                continue

            # Add program node
            if prog_id not in program_nodes:
                program_nodes[prog_id] = {
                    "id": f"program_{prog_id}",
                    "type": "program",
                    "name": prog_name,
                    "domain_tags": prog_tags,
                    "agency": prog_entity.properties.get("agency", ""),
                }

            # Add contractor nodes and PRIMES_ON edges
            for c_id in c_ids:
                c_entity = bg._entity_cache.get(c_id)
                if not c_entity:
                    continue
                if c_id not in contractor_nodes:
                    contractor_nodes[c_id] = {
                        "id": f"contractor_{c_id}",
                        "type": "contractor",
                        "name": c_entity.name,
                        "program_count": 0,
                    }
                contractor_nodes[c_id]["program_count"] += 1

                edges.append({
                    "source": f"contractor_{c_id}",
                    "target": f"program_{prog_id}",
                    "type": "PRIMES_ON",
                })

            # Build competition pairs
            for i, c1 in enumerate(c_ids):
                for c2 in c_ids[i+1:]:
                    pair = tuple(sorted([c1, c2]))
                    competition_pairs.setdefault(pair, []).append(prog_name)

        # Add COMPETES_WITH edges
        for (c1, c2), shared_progs in competition_pairs.items():
            if c1 in contractor_nodes and c2 in contractor_nodes:
                edges.append({
                    "source": f"contractor_{c1}",
                    "target": f"contractor_{c2}",
                    "type": "COMPETES_WITH",
                    "shared_programs": len(shared_progs),
                    "programs": shared_progs[:5],  # cap for payload size
                })

        nodes = list(contractor_nodes.values())[:limit] + list(program_nodes.values())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building competition graph: {str(e)}")

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }


# =========================================
# DOMAIN TAGS ENDPOINT (V6)
# =========================================


@app.get("/graph/domain-tags")
async def get_domain_tag_summary():
    """Return all available domain tags with program counts."""
    # Supabase fast-path
    if USE_SUPABASE and SUPABASE_CLIENT_AVAILABLE:
        try:
            return {"tags": sb_get_domain_tags()}
        except Exception as e:
            logger.warning(f"Supabase domain-tags fallback: {e}")

    udb = _get_unified_db()
    if not udb:
        return {"tags": []}

    tag_counts = {}
    try:
        cursor = udb.execute(
            "SELECT domain_tags FROM programs WHERE domain_tags IS NOT NULL AND domain_tags != ''"
        )
        for row in cursor:
            try:
                tags = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                for tag in (tags or []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            except (json.JSONDecodeError, TypeError):
                pass
    finally:
        udb.close()

    sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])
    return {"tags": [{"tag": t, "count": c} for t, c in sorted_tags]}


# =========================================
# QUALITY STATS ENDPOINT (V6)
# =========================================


@app.get("/graph/quality-stats")
async def get_quality_stats():
    """Data quality score distribution across entity types."""
    # Supabase fast-path
    if USE_SUPABASE and SUPABASE_CLIENT_AVAILABLE:
        try:
            return sb_get_quality_stats()
        except Exception as e:
            logger.warning(f"Supabase quality-stats fallback: {e}")

    udb = _get_unified_db()
    if not udb:
        raise HTTPException(status_code=503, detail="Unified DB not available")

    result = {
        "overall": {"mean": 0, "median": 0, "p25": 0, "p75": 0, "total": 0},
        "by_type": {},
        "buckets": [],
    }

    try:
        all_scores = []
        for table, name_col in [("contacts", "full_name"), ("programs", "name"), ("companies", "name")]:
            entity_type = table.rstrip("s").capitalize()  # contacts -> Contact
            try:
                cursor = udb.execute(
                    f"SELECT data_quality_score FROM {table} WHERE data_quality_score IS NOT NULL"
                )
                scores = [row[0] for row in cursor]
                if scores:
                    scores.sort()
                    n = len(scores)
                    result["by_type"][entity_type] = {
                        "mean": round(sum(scores) / n, 1),
                        "median": round(scores[n // 2], 1),
                        "count": n,
                        "p25": round(scores[n // 4], 1),
                        "p75": round(scores[3 * n // 4], 1),
                    }
                    all_scores.extend(scores)
            except Exception:
                pass

        if all_scores:
            all_scores.sort()
            n = len(all_scores)
            result["overall"] = {
                "mean": round(sum(all_scores) / n, 1),
                "median": round(all_scores[n // 2], 1),
                "p25": round(all_scores[n // 4], 1),
                "p75": round(all_scores[3 * n // 4], 1),
                "total": n,
            }

            # Build histogram buckets
            bucket_ranges = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
            for low, high in bucket_ranges:
                count = sum(1 for s in all_scores if low <= s < (high + 1 if high == 100 else high))
                result["buckets"].append({
                    "range": f"{low}-{high}",
                    "count": count,
                    "pct": round(count / n * 100, 1) if n > 0 else 0,
                })

    finally:
        udb.close()

    return result


# =========================================
# SUPABASE-BACKED V2 API ENDPOINTS
# =========================================

USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"


def _check_supabase():
    if not SUPABASE_CLIENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Supabase client not installed")
    if not USE_SUPABASE:
        raise HTTPException(status_code=503, detail="USE_SUPABASE not enabled in .env")


@app.get("/api/v2/contacts")
async def api_v2_contacts(
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    company: Optional[str] = None,
    priority: Optional[str] = None,
    min_score: Optional[float] = None,
    sort_by: str = "bd_score",
    sort_dir: str = "desc",
):
    """Get contacts from Supabase with filtering/pagination."""
    _check_supabase()
    rows, total = sb_get_contacts(limit, offset, search, company, priority, min_score, sort_by, sort_dir)
    return {"contacts": rows, "total": total}


@app.get("/api/v2/programs")
async def api_v2_programs(
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    agency: Optional[str] = None,
    domain: Optional[str] = None,
    min_quality: Optional[float] = None,
    sort_by: str = "data_quality_score",
    sort_dir: str = "desc",
):
    """Get programs from Supabase with filtering/pagination."""
    _check_supabase()
    rows, total = sb_get_programs(limit, offset, search, agency, domain, min_quality, sort_by, sort_dir)
    return {"programs": rows, "total": total}


@app.get("/api/v2/jobs")
async def api_v2_jobs(
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    company: Optional[str] = None,
    sort_by: str = "bd_score",
    sort_dir: str = "desc",
):
    """Get jobs from Supabase with filtering/pagination."""
    _check_supabase()
    rows, total = sb_get_jobs(limit, offset, search, company, sort_by, sort_dir)
    return {"jobs": rows, "total": total}


@app.get("/api/v2/companies")
async def api_v2_companies(
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
):
    """Get companies from Supabase with filtering/pagination."""
    _check_supabase()
    rows, total = sb_get_companies(limit, offset, search)
    return {"companies": rows, "total": total}


@app.get("/api/v2/stats")
async def api_v2_stats():
    """Get collection statistics from Supabase (row counts per table)."""
    _check_supabase()
    return sb_get_stats()


@app.get("/api/v2/graph/data")
async def api_v2_graph_data(
    limit: int = 800,
    node_types: Optional[str] = None,
    domain_filter: Optional[str] = None,
    min_quality: Optional[float] = None,
):
    """Graph Explorer V6 data from Supabase: 4 node types + edges."""
    _check_supabase()
    types_list = None
    if node_types:
        types_list = [t.strip() for t in node_types.split(",")]
    return sb_get_graph_data(limit, types_list, domain_filter, min_quality)


@app.get("/api/v2/graph/competition")
async def api_v2_competition_graph(
    program_filter: Optional[str] = None,
    limit: int = 200,
):
    """Competition network: contractors sharing programs."""
    _check_supabase()
    return sb_get_competition_graph(program_filter, limit)


@app.get("/api/v2/graph/domain-tags")
async def api_v2_domain_tags():
    """Domain tag summary for filter dropdowns."""
    _check_supabase()
    return {"tags": sb_get_domain_tags()}


@app.get("/api/v2/graph/quality-stats")
async def api_v2_quality_stats():
    """Data quality score distribution."""
    _check_supabase()
    return sb_get_quality_stats()


@app.get("/api/v2/health")
async def api_v2_health():
    """Supabase connection health check."""
    sb_ok = SUPABASE_CLIENT_AVAILABLE and USE_SUPABASE and supabase_available()
    return {
        "supabase": "connected" if sb_ok else "unavailable",
        "use_supabase": USE_SUPABASE,
        "client_available": SUPABASE_CLIENT_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
    }


# =========================================
# SCORING VALIDATION
# =========================================


@app.get("/scoring/validate")
async def validate_scoring():
    """Run BD score validation against Bullhorn placement outcomes.

    Trains an XGBoost model on historical placements and compares
    its predictive accuracy to the rule-based BD scoring engine.
    Returns accuracy metrics, feature importances, and tuning recommendations.
    """
    try:
        from Engine5_Scoring.scripts.score_validator import BDScoreValidator

        validator = BDScoreValidator()
        result = await asyncio.to_thread(validator.validate)
        report_path = await asyncio.to_thread(validator.save_report, result)

        return {
            "timestamp": result.timestamp,
            "sample_size": result.sample_size,
            "manual_scoring": {
                "accuracy": result.manual_accuracy,
                "mean_absolute_error": result.manual_mae,
            },
            "xgboost_scoring": {
                "accuracy": result.ml_accuracy,
                "mean_absolute_error": result.ml_mae,
            },
            "feature_importance": result.feature_importance,
            "recommendations": result.recommendations,
            "report_path": report_path,
        }
    except ImportError as e:
        raise HTTPException(
            status_code=501,
            detail=f"Score validator dependencies not available: {e}",
        )
    except Exception as e:
        logger.error(f"Score validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# MAIN
# =========================================


def main():
    """Run the API server."""
    import argparse

    parser = argparse.ArgumentParser(description="BD Intelligence Hub API Server")
    parser.add_argument("--host", default=API_HOST, help="Host to bind")
    parser.add_argument("--port", type=int, default=API_PORT, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument(
        "--workers", type=int, default=4, help="Number of uvicorn workers (default: 4)"
    )

    args = parser.parse_args()

    logger.info(
        "server_startup",
        version="2.0",
        host=args.host,
        port=args.port,
        docs_url=f"http://{args.host}:{args.port}/docs",
        endpoints="50+",
    )

    if args.reload:
        uvicorn.run(
            "Engine8_Knowledge.api:app", host=args.host, port=args.port, reload=True
        )
    else:
        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
