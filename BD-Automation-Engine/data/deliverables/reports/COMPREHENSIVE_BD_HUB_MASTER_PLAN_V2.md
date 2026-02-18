# COMPREHENSIVE BD INTELLIGENCE HUB - MASTER BUILD PLAN V2

## Unified Implementation Strategy for Prime Technical Services
### Incorporating 60+ Cutting-Edge AI/LLM Repositories

**Created:** January 25, 2026  
**Version:** 2.0 - COMPREHENSIVE EDITION  
**Status:** MASTER PLAN - All Research Incorporated

---

## EXECUTIVE SUMMARY

This comprehensive plan consolidates THREE separate Auto-Claude projects into ONE unified BD Intelligence Hub, incorporating insights from 60+ cutting-edge repositories identified through extensive research.

### The Three Projects Being Unified

| Project | Location | Current Stack | Records |
|---------|----------|---------------|---------|
| **BD-Automation-Engine** | `C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine` | Qdrant + FastAPI + RAG + 8 Engines | 8,447 vectors |
| **Data-Scraper** | `C:\data-scraper\data-scraper` | SQLite + ChromaDB + 40+ scrapers | 388 programs |
| **N8N Builder** | `C:\N8N Builder` | LanceDB + 14 MCP tools + n8n | 3,242 chunks |

### Architecture Decision

**BD-Automation-Engine becomes THE HUB** because:
- Most complete infrastructure (Qdrant, FastAPI, RAG, MCP)
- Largest dataset (8,447 records)
- Production-ready API server
- Already has 5 collections structured for BD intelligence

**Data-Scraper** becomes DATA WRITER (scrapes → POSTs to Hub API)
**N8N Builder** becomes ORCHESTRATOR (builds workflows calling Hub MCP tools)

---

## COMPLETE REPOSITORY INVENTORY (60+ Repos)

### TIER 1: CRITICAL - Must Implement First

| Repository | Stars | Category | BD Application |
|------------|-------|----------|----------------|
| **Mem0** | 45,100+ | Memory | Cross-session BD context across weeks/months |
| **LightRAG** | 25,400+ | GraphRAG | Contractor relationships, teaming networks |
| **PageIndex** | 7,700+ | VectorlessRAG | 98.7% accuracy, federal audit trails |
| **UltraRAG** | 3,700+ | MCP-RAG | YAML pipelines for BD workflows |
| **Docling** | 10,000+ | DocProc | 30x faster federal PDF processing |
| **Firecrawl** | 77,100+ | WebScrape | Official MCP server, AI extraction |
| **Crawl4AI** | 55,800+ | WebScrape | LLM-optimized "Fit Markdown" |
| **RAGAS** | 8,000+ | Evaluation | RAG quality metrics |

### TIER 2: HIGH PRIORITY - Should Implement

| Repository | Stars | Category | BD Application |
|------------|-------|----------|----------------|
| **CrewAI** | 43,100+ | Agents | Multi-agent BD workflows |
| **LangGraph** | 21,000+ | Workflows | Durable BD execution with checkpoints |
| **Dify** | 114,000+ | Platform | Visual workflow builder + MCP |
| **LangFlow** | 140,000+ | Platform | Flow-based agents |
| **Microsoft GraphRAG** | 29,200+ | GraphRAG | Contractor network analysis |
| **Pathway** | 50,000+ | Streaming | Real-time Bullhorn sync |
| **RAGFlow** | 67,700+ | Platform | Enterprise RAG with DeepDoc |
| **MindsDB** | 37,500+ | Data | Federated AI queries, MCP server |

### TIER 3: ENHANCEMENT - Nice to Have

| Repository | Stars | Category | BD Application |
|------------|-------|----------|----------------|
| **Sim.ai** | 21,800+ | Platform | Visual agent workflows for BD team |
| **AgenticSeek** | 16,000+ | Agents | Fully local autonomous agent |
| **Supermemory** | 14,400+ | Memory | High-scale memory API |
| **Graphiti** | 8,000+ | Graph | Temporal knowledge graphs |
| **FalkorDB GraphRAG** | 5,000+ | GraphRAG | 90% hallucination reduction |
| **ExtractThinker** | 3,000+ | DocProc | ORM-style extraction |
| **browser-use** | 77,000+ | Automation | AI browser control |
| **Superpowers** | 35,500+ | Skills | TDD Claude skills |

### TIER 4: REFERENCE RESOURCES

| Repository | Stars | Category | BD Application |
|------------|-------|----------|----------------|
| **awesome-mcp-servers** | 30,000+ | Reference | MCP server catalog |
| **public-apis** | 350,000+ | Reference | Free API discovery |
| **anthropic/skills** | 51,300+ | Reference | Official skill patterns |
| **claude-code** | 60,400+ | Reference | MCP architecture patterns |
| **modelcontextprotocol/servers** | 75,300+ | Reference | Official MCP servers |

---

## IMPLEMENTATION PHASES

### PHASE 1: Core Hub Infrastructure (BD-Automation-Engine)

**Components to Build:**

1. **Memory Layer (Mem0)** - `Engine8_Knowledge/scripts/memory_layer.py`
   - Cross-session memory for BD context
   - Entity facts storage (companies, programs, contacts)
   - BD insights tracking
   - Scrape result summaries

2. **Knowledge Graph (LightRAG)** - `Engine8_Knowledge/scripts/lightrag_engine.py`
   - Entity relationship extraction
   - Dual-level retrieval (local + global)
   - Native Qdrant integration
   - Contractor network analysis

3. **Hybrid Retriever** - `Engine8_Knowledge/scripts/hybrid_retriever.py`
   - Semantic search (Qdrant)
   - BM25 keyword search
   - Reciprocal Rank Fusion (RRF)
   - CrossEncoder reranking (70% accuracy boost)

4. **Query Router** - `Engine8_Knowledge/scripts/query_router.py`
   - Pattern-based query classification
   - Routes to optimal retrieval system(s)
   - Query types: FACTUAL, RELATIONAL, COMPREHENSIVE, MEMORY, KEYWORD

5. **Enhanced FastAPI Endpoints** - `Engine8_Knowledge/api.py`
   - /memory/* endpoints
   - /ask/smart endpoint
   - /lightrag/* endpoints
   - /ingest/* endpoints for external projects

6. **Enhanced MCP Server** - `mcp/knowledge-mcp-server/src/index.ts`
   - memory_add, memory_search, memory_entity
   - smart_ask, query_knowledge_graph
   - hybrid_search

### PHASE 2: Advanced Retrieval Systems

1. **PageIndex Engine** - `Engine8_Knowledge/scripts/pageindex_engine.py`
   - Vectorless RAG (98.7% accuracy)
   - Hierarchical tree-search
   - Audit trail generation for federal compliance

2. **Redis Semantic Cache** - `Engine8_Knowledge/scripts/redis_cache.py`
   - 4x latency reduction
   - Semantic similarity matching
   - TTL-based expiration

### PHASE 3: Document & Web Processing

1. **Docling Processor** - `Engine8_Knowledge/scripts/docling_processor.py`
   - 30x faster PDF processing
   - Table/chart extraction
   - Federal metadata extraction

2. **Unified Web Scraper** - `Engine8_Knowledge/scripts/web_scrapers.py`
   - Firecrawl for JS-rendered sites
   - Crawl4AI for static content
   - BD-specific content categorization

### PHASE 4: Specialized BD Agents

Create 5 specialized agents in `Engine8_Knowledge/agents/`:

1. **Program Intelligence Agent** - Federal program analysis
2. **Company Research Agent** - Competitor/partner analysis
3. **Contact Finder Agent** - Key personnel identification
4. **Document Q&A Agent** - Document-based answers
5. **BD Strategy Agent** - Strategy synthesis

### PHASE 5: Agent Orchestration Platforms

1. **CrewAI Integration** - Multi-agent workflows
2. **Sim.ai Integration** - Visual workflow design
3. **RAGFlow Integration** - Enterprise RAG
4. **MindsDB Integration** - Federated queries

### PHASE 6: Pipelines & Evaluation

1. **UltraRAG YAML Pipelines** - BD capture workflows
2. **RAGAS Evaluation** - Pipeline quality metrics

### PHASE 7: External Integrations

1. **MCP Server Catalog** (awesome-mcp-servers reference)
2. **Public APIs** (free government/business APIs)
3. **AgenticSeek** - Local autonomous agent

### PHASE 8: Project-Specific Integration

**8.1 Data-Scraper Integration:**
- Create `scripts/hub_client.py`
- Update scrapers to POST to Hub
- Add Hub MCP tools

**8.2 N8N Builder Integration:**
- Add Hub MCP config to `.mcp.json`
- Create Hub integration module
- Update knowledge base to use Hub

**8.3 Final Merge:**
- Sync all data to Hub
- Build knowledge graph
- Test cross-project queries
- Run RAGAS evaluation

---

## KEY TECHNOLOGY STACK

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Vector Store** | Qdrant (embedded) | Primary semantic search |
| **Memory** | Mem0 | Cross-session context |
| **Knowledge Graph** | LightRAG | Entity relationships |
| **Vectorless RAG** | PageIndex | Audit-trail reasoning |
| **Document Processing** | Docling | Federal PDF extraction |
| **Web Scraping** | Firecrawl + Crawl4AI | AI-powered extraction |
| **Hybrid Search** | BM25 + RRF | Keyword + semantic fusion |
| **Reranking** | CrossEncoder | 70% accuracy boost |
| **Caching** | Redis | Query result caching |
| **Evaluation** | RAGAS | Pipeline quality metrics |
| **API** | FastAPI | REST endpoints |
| **MCP** | Node.js wrapper | Claude Code integration |

---

## QUICK START COMMANDS

```bash
# 1. Start the Hub
cd "C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine"
python Engine8_Knowledge/api.py

# 2. Start Redis (for caching)
docker run -d -p 6379:6379 redis:latest

# 3. Sync Data-Scraper data
cd "C:\data-scraper\data-scraper"
python scripts/sync_to_hub.py --all

# 4. Build Knowledge Graph
cd "C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine"
python Engine8_Knowledge/scripts/build_knowledge_graph.py

# 5. Test
curl "http://localhost:8100/ask/smart?q=Find%20DCGS%20contacts%20at%20Leidos"
```

---

## REPOSITORY QUICK LINKS

### Core Technologies
- Mem0: https://github.com/mem0ai/mem0
- LightRAG: https://github.com/HKUDS/LightRAG
- PageIndex: https://github.com/VectifyAI/PageIndex
- UltraRAG: https://github.com/OpenBMB/UltraRAG

### Document & Web Processing
- Docling: https://github.com/docling-project/docling
- Firecrawl: https://github.com/firecrawl/firecrawl
- Crawl4AI: https://github.com/unclecode/crawl4ai

### Agent Orchestration
- CrewAI: https://github.com/crewAIInc/crewAI
- LangGraph: https://github.com/langchain-ai/langgraph
- Dify: https://github.com/langgenius/dify
- LangFlow: https://github.com/langflow-ai/langflow

### Platforms
- RAGFlow: https://github.com/infiniflow/ragflow
- MindsDB: https://github.com/mindsdb/mindsdb
- Sim.ai: https://github.com/simstudioai/sim
- AgenticSeek: https://github.com/Fosowl/agenticSeek

### Evaluation
- RAGAS: https://github.com/explodinggradients/ragas

### Reference
- awesome-mcp-servers: https://github.com/punkpeye/awesome-mcp-servers
- public-apis: https://github.com/public-apis/public-apis

---

## HOW TO USE THIS PLAN

**Place this file in ALL THREE project folders, then tell Claude Code:**

1. **BD-Automation-Engine:** "Read COMPREHENSIVE_BD_HUB_MASTER_PLAN_V2.md and implement Phases 1-6"

2. **Data-Scraper:** "Read COMPREHENSIVE_BD_HUB_MASTER_PLAN_V2.md and implement Phase 8.1"

3. **N8N Builder:** "Read COMPREHENSIVE_BD_HUB_MASTER_PLAN_V2.md and implement Phase 8.2"

4. **Final:** Execute Phase 8.3 merge checklist

---

**This plan incorporates ALL 60+ repositories from research and provides a complete roadmap for building a world-class BD Intelligence Hub.**
