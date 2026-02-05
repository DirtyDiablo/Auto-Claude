# BD-Automation-Engine Project Capabilities Report

**Generated:** 2026-02-03
**Project:** PTS BD Intelligence System
**Target:** DCGS Portfolio (~$950M Federal Defense Programs)

---

## 1. Project Overview

### Purpose
The BD-Automation-Engine is an 8-engine autonomous pipeline for Business Development automation targeting federal defense programs. It provides end-to-end capabilities from job scraping through AI-powered intelligence generation.

### Core Capabilities
- **Job Scraping & Intake** - Automated harvesting from ClearanceJobs, LinkedIn, competitor sites
- **Program Mapping** - 7-stage pipeline matching jobs to 388 federal programs
- **Contact Intelligence** - 6-tier hierarchy classification of 13,000+ prime contractor contacts
- **BD Playbook Generation** - AI-generated outreach materials and call scripts
- **Priority Scoring** - 0-100 BD opportunity scoring algorithm
- **Knowledge System** - 8,447+ indexed records with semantic search and RAG
- **Multi-Agent Orchestration** - CrewAI-powered BD analysis workflows
- **Visual AI Orchestration** - Dify integration for no-code workflow building

### Component Status

| Engine | Name | Status | Description |
|--------|------|--------|-------------|
| Engine 1 | Apify Scraper | ✅ Complete | External Apify actors for job scraping |
| Engine 2 | Program Mapping | ✅ Complete | Job-to-program matching (7-stage pipeline) |
| Engine 3 | OrgChart | ✅ Complete | Contact classification (6-tier hierarchy) |
| Engine 4 | Playbook | ✅ Complete | BD playbook & briefing generation |
| Engine 5 | Scoring | ✅ Complete | BD priority scoring (0-100) |
| Engine 6 | QA & Alerts | 🔄 In Progress | Quality assurance system |
| Engine 7 | Bullhorn ETL | ✅ Complete | CRM data extraction (293 MB) |
| Engine 8 | Knowledge | ✅ Complete | AI Knowledge System (8,447 vectors) |

---

## 2. Directory Structure

```
BD-Automation-Engine/                    # ~1.2 GB Total
├── Engine1_Scraper/                     # 3.2 MB - Apify job scraper configs
│   ├── Configurations/                  # ScraperEngine_Config.json
│   └── data/                            # 20+ scraped job datasets (JSON)
│
├── Engine2_ProgramMapping/              # 2.4 MB - Job standardization + matching
│   ├── Configurations/                  # ProgramMapping_Config.json
│   ├── data/                            # Federal Programs (388 records)
│   └── scripts/                         # job_standardizer.py, program_mapper.py
│
├── Engine3_OrgChart/                    # 32 MB - Contact classification
│   ├── Configurations/                  # OrgChart_Config.json
│   ├── data/Prime_Contacts/             # 25 CSV files (13,089 contacts)
│   └── scripts/                         # contact_classifier.py, contact_lookup.py
│
├── Engine4_Briefing/                    # 8 KB - Briefing generator
│   └── scripts/                         # briefing_generator.py
│
├── Engine4_Playbook/                    # 96 KB - Playbook generator
│   ├── Configurations/                  # Playbook_Config.json
│   ├── scripts/                         # bd_playbook_generator.py
│   └── Templates/                       # Playbook templates
│
├── Engine5_Scoring/                     # 16 KB - BD scoring algorithm
│   ├── Configurations/                  # Scoring_Config.json
│   └── scripts/                         # bd_scoring.py
│
├── Engine6_QA/                          # 28 KB - Quality assurance
│   ├── data/                            # review_queue.json
│   └── scripts/                         # qa_feedback.py
│
├── Engine7_BullhornETL/                 # 12 MB - CRM extraction
│   ├── colton_scurry_analysis/          # Deep analysis reports
│   │   ├── ANALYSIS/                    # 12 detailed markdown files
│   │   └── FINAL_OUTPUTS/               # 8 actionable BD outputs
│   └── scripts/                         # 17 ETL Python scripts
│
├── Engine8_Knowledge/                   # 1.1 MB code + 734 MB vectors
│   ├── agents/                          # 13 CrewAI agents
│   ├── bd_lightrag/                     # Graph RAG implementation
│   ├── data/qdrant/                     # Vector database (8,447 records)
│   ├── evaluation/                      # RAGAS evaluation framework
│   ├── graph/                           # BD knowledge graph
│   ├── processors/                      # Document pipeline
│   ├── ragflow/                         # RAGflow integration
│   ├── retrieval/                       # Ultra RAG, hybrid retrieval
│   ├── schemas/                         # Vector collection schemas
│   ├── scripts/                         # 28 indexing/RAG scripts
│   └── api.py                           # FastAPI server (:8100)
│
├── mcp/                                 # 2.8 MB - MCP servers
│   ├── knowledge-mcp-server/            # TypeScript - Knowledge API bridge
│   ├── mapify-mcp-server/               # TypeScript - Mind map generation
│   └── claude_desktop_config.json       # MCP configuration
│
├── dashboard/                           # 17 MB - React visualization
│   ├── public/data/                     # 24 JSON data files
│   └── src/                             # Components, hooks, services
│
├── dify_integration/                    # 112 KB - Visual AI orchestration
│   ├── dify_qdrant_bridge.py            # Qdrant knowledge bridge
│   ├── dify_crewai_bridge.py            # CrewAI agent invocation
│   └── dify_n8n_bridge.py               # n8n workflow triggers
│
├── n8n/                                 # 18 workflow JSON files
├── data/                                # 1.1 GB - Main data storage
├── outputs/                             # 52 MB - Generated files
├── docs/                                # 52 MB - Documentation
├── services/                            # Integration services
├── tests/                               # 15 test files
└── scripts/                             # Utility scripts
```

---

## 3. File Inventory by Type

| Extension | Count | Description |
|-----------|-------|-------------|
| `.py` | 199 | Python scripts (engines, agents, APIs) |
| `.ts` | 35 | TypeScript (dashboard, MCP servers) |
| `.js` | 3 | JavaScript (build scripts) |
| `.json` | 264+ | Configurations, data, workflows |
| `.md` | 209+ | Documentation, briefings, analysis |
| `.csv` | 247+ | Contacts, programs, job mappings |
| `.yaml/.yml` | 7 | Workflow pipelines, CI/CD |
| `.db/.sqlite` | 10 | SQLite databases |

**Total Project Size:** ~1.2 GB (excluding node_modules)

---

## 4. Python Modules & Scripts

### Engine 2: Program Mapping (7 scripts)
| Script | Purpose |
|--------|---------|
| `job_standardizer.py` | LLM-powered field extraction from job postings |
| `program_mapper.py` | Multi-signal program matching (semantic + keyword) |
| `pipeline.py` | Full 7-stage standardization pipeline |
| `full_pipeline.py` | Extended pipeline with all stages |
| `exporters.py` | Notion CSV + n8n JSON export |
| `create-tango-exports.py` | Tango format data exports |
| `enrich-federal-programs-v3.py` | Federal programs enrichment |

### Engine 3: OrgChart (2 scripts)
| Script | Purpose |
|--------|---------|
| `contact_classifier.py` | 6-tier hierarchy classification (C-Suite → Analyst) |
| `contact_lookup.py` | Contact search and retrieval |

### Engine 4: Briefing/Playbook (2 scripts)
| Script | Purpose |
|--------|---------|
| `briefing_generator.py` | AI-generated BD briefings |
| `bd_playbook_generator.py` | Complete BD playbook generation |

### Engine 5: Scoring (1 script)
| Script | Purpose |
|--------|---------|
| `bd_scoring.py` | 0-100 BD priority scoring algorithm |

### Engine 6: QA (1 script)
| Script | Purpose |
|--------|---------|
| `qa_feedback.py` | Quality assurance and review processing |

### Engine 7: Bullhorn ETL (17+ scripts)
| Script | Purpose |
|--------|---------|
| `bullhorn_etl.py` | Core CRM data extraction |
| `bullhorn_etl_v2.py` | Enhanced ETL with batching |
| `analyze_call_notes.py` | Call notes analysis |
| `analyze_prime_contacts.py` | Prime contractor analysis |
| `bd_intelligence_report.py` | Intelligence report generation |
| `build_prime_contact_databases.py` | Contact database builder |
| `contact_scoring.py` | Contact priority scoring |
| `export_to_notion.py` | Notion sync |
| `intelligent_contact_classifier.py` | AI-powered classification |
| `link_to_federal_programs.py` | Program linkage |
| `past_performance_report.py` | Past performance analysis |

### Engine 8: Knowledge (108+ scripts)

**Agents (13 files):**
| Agent | Purpose |
|-------|---------|
| `bd_agents.py` | Core BD agent team |
| `bd_strategy_agent.py` | Strategy development |
| `company_research_agent.py` | Company intelligence |
| `contact_finder_agent.py` | Contact discovery |
| `contact_classifier_agent.py` | Contact classification |
| `program_intel_agent.py` | Program intelligence |
| `analytics_agent.py` | Analytics and metrics |
| `quality_assurance_agent.py` | QA validation |
| `scraper_monitor_agent.py` | Scraper monitoring |
| `crewai_orchestrator.py` | Multi-agent orchestration |
| `workflows.py` | Workflow definitions |

**Core Scripts:**
| Script | Purpose |
|--------|---------|
| `vector_store.py` | Qdrant vector operations |
| `rag_engine.py` | RAG question answering |
| `indexer.py` | Data indexing pipeline |
| `hybrid_retriever.py` | BM25 + semantic hybrid search |
| `query_router.py` | Intelligent query routing |
| `memory_layer.py` | mem0 memory integration |
| `lightrag_engine.py` | Knowledge graph RAG |
| `pageindex_engine.py` | Page-level indexing |
| `redis_cache.py` | Semantic caching |

**API (1 file):**
| File | Purpose |
|------|---------|
| `api.py` | FastAPI server with 50+ endpoints |

### Root-Level Scripts (61+ files)
| Script | Purpose |
|--------|---------|
| `orchestrator.py` | Master pipeline orchestrator |
| `quickstart.py` | Quick start helper |
| `status_check.py` | System status check |
| `simple_knowledge_api.py` | Simplified API wrapper |
| `reindex_with_openai.py` | OpenAI reindexing |
| `launch_parallel_indexing.py` | Parallel indexing launcher |

---

## 5. Database Files

### SQLite Databases

| Database | Size | Description |
|----------|------|-------------|
| `data/bullhorn_master.db` | 293 MB | Main CRM database (contacts, jobs, placements, notes) |
| `data/bd_graph.db` | 804 KB | BD knowledge graph |
| `data/memories.db` | 40 KB | mem0 memory layer |
| `data/page_index.db` | 24 KB | Page indexing |

### Qdrant Vector Collections

| Collection | Records | Size | Description |
|------------|---------|------|-------------|
| `contacts` | 7,337 | 225 MB | CRM contacts with tier classification |
| `documents` | 205 | 297 MB | Past performance, briefings |
| `activities` | 500 | 209 MB | Call notes, meeting records |
| `programs` | 401 | 3 MB | Federal programs and contracts |
| `jobs` | 4 | <1 MB | Job postings with BD scores |
| `mem0` | - | <1 MB | Memory layer storage |

**Total Database Size:** ~1.03 GB

---

## 6. Data Assets

### Key CSV Files

**Federal Programs:**
| File | Rows | Description |
|------|------|-------------|
| `Federal Programs MASTER V4.csv` | 388 | Complete federal programs database |

**Prime Contractor Contacts (Engine3_OrgChart/data/Prime_Contacts/):**
| File | Rows | Company |
|------|------|---------|
| `CACI_Contacts.csv` | 3,634 | CACI International |
| `GDIT_Contacts.csv` | 2,345 | General Dynamics IT |
| `Leidos_Contacts.csv` | 1,483 | Leidos |
| `Lockheed_Martin_Contacts.csv` | 1,137 | Lockheed Martin |
| `Northrop_Grumman_Contacts.csv` | 853 | Northrop Grumman |
| `Microsoft_Contacts.csv` | 809 | Microsoft |
| `AWS_Contacts.csv` | 802 | Amazon Web Services |
| `Boeing_Contacts.csv` | 680 | Boeing |
| `Palantir_Contacts.csv` | 440 | Palantir |
| `Booz_Allen_Hamilton_Contacts.csv` | 427 | Booz Allen Hamilton |
| `Deloitte_Contacts.csv` | 371 | Deloitte |
| `BAE_Systems_Contacts.csv` | 273 | BAE Systems |
| `L3Harris_Contacts.csv` | 219 | L3Harris |
| `+ 12 more primes` | ~800 | Various |

**Total Contacts:** 13,089 across 25 prime contractors

### JSON Data Files

| Location | Files | Description |
|----------|-------|-------------|
| `Engine1_Scraper/data/` | 20+ | Scraped job datasets |
| `dashboard/public/data/` | 24 | Dashboard visualization data |
| `n8n/` | 18 | Workflow definitions |

### Output Directories

| Directory | Contents |
|-----------|----------|
| `outputs/BD_Briefings/` | 71+ generated markdown briefings |
| `outputs/BD_Playbooks/` | Generated playbooks |
| `outputs/Logs/` | Application logs |

---

## 7. Configuration

### Environment Variables (.env)

**API Keys:**
```
ANTHROPIC_API_KEY=************     # Claude API
OPENAI_API_KEY=************        # Embeddings (text-embedding-ada-002)
APIFY_API_TOKEN=************       # Web scraping
NOTION_TOKEN=************          # Notion integration
MAPIFY_API_KEY=************        # Mind map generation
```

**Notion Database IDs:**
```
NOTION_DB_DCGS_CONTACTS=2ccdef65-baa5-8087-a53b-000ba596128e
NOTION_DB_GDIT_JOBS=2563119e7914442cbe0fb86904a957a1
NOTION_DB_PROGRAM_MAPPING_HUB=f57792c1-605b-424c-8830-23ab41c47137
NOTION_DB_FEDERAL_PROGRAMS=06cd9b22-5d6b-4d37-b0d3-ba99da4971fa
NOTION_DB_BD_OPPORTUNITIES=2bcdef65-baa5-80ed-bd95-000b2f898e17
NOTION_DB_CONTRACTORS=3a259041-22bf-4262-a94a-7d33467a1752
NOTION_DB_CONTRACT_VEHICLES=0f09543e-9932-44f2-b0ab-7b4c070afb81
```

**Processing Settings:**
```
BATCH_SIZE=10
HIGH_CONFIDENCE_THRESHOLD=0.70
MEDIUM_CONFIDENCE_THRESHOLD=0.50
BD_TIER_HOT_MIN=80
BD_TIER_WARM_MIN=50
```

### MCP Configuration (.mcp.json)

| Server | Type | Purpose |
|--------|------|---------|
| `bd-knowledge` | Local Node | Knowledge API bridge (port 8100) |
| `n8n` | NPX | n8n workflow orchestration |
| `notion` | NPX | Notion API integration |
| `notion-remote` | Remote | Hosted Notion MCP (OAuth) |
| `apify` | NPX | Apify web scraping |
| `mapify` | Local Node | Mind map generation |

### Engine Configuration Files

| File | Engine |
|------|--------|
| `Engine1_Scraper/Configurations/ScraperEngine_Config.json` | Scraper |
| `Engine2_ProgramMapping/Configurations/ProgramMapping_Config.json` | Program Mapping |
| `Engine3_OrgChart/Configurations/OrgChart_Config.json` | OrgChart |
| `Engine4_Playbook/Configurations/Playbook_Config.json` | Playbook |
| `Engine5_Scoring/Configurations/Scoring_Config.json` | Scoring |

---

## 8. API Endpoints (50+)

### Health & Status
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| GET | `/stats` | System statistics (Qdrant, memory, graph, cache) |

### Smart Query
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/ask/smart` | Intelligent query routing with caching |

### Search Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/search` | Semantic search (POST body) |
| GET | `/search` | Semantic search (query params) |
| GET | `/search/semantic` | Semantic-only search |
| GET | `/search/keyword` | BM25 keyword search |
| GET | `/search/hybrid` | Hybrid semantic + keyword with reranking |

### RAG Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/ask` | Natural language Q&A (RAG) |
| GET | `/ask` | RAG query (GET) |
| GET | `/rag/router` | RAG with strategy selection |
| GET | `/rag/analyze` | Analyze query for optimal strategy |

### Graph Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/graph/query` | Knowledge graph query |
| GET | `/graph/relationships` | Entity relationships |
| GET | `/graph/network` | Company network analysis |

### BD Knowledge Graph
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/bdgraph/program/{name}` | Program ecosystem |
| GET | `/bdgraph/contact/{name}` | Contact network |
| GET | `/bdgraph/teaming/{from}/{to}` | Teaming path finder |
| GET | `/bdgraph/query` | Natural language graph query |
| GET | `/bdgraph/search` | Entity search |
| POST | `/bdgraph/entity` | Add entity |
| POST | `/bdgraph/relationship` | Add relationship |
| GET | `/bdgraph/stats` | Graph statistics |
| POST | `/bdgraph/populate` | Populate from vector store |
| GET | `/bdgraph/types` | List entity/relationship types |

### Memory Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/memory/add` | Add memory |
| POST | `/memory/entity` | Add entity fact |
| POST | `/memory/insight` | Add BD insight |
| GET | `/memory/search` | Search memories |
| GET | `/memory/entity/{name}` | Get entity facts |
| GET | `/memory/insights` | Get BD insights |
| GET | `/memory/stats` | Memory statistics |
| GET | `/memory/contact/{name}` | Contact context |
| GET | `/memory/program/{name}` | Program context |

### Ingest Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/ingest/document` | Ingest document |
| POST | `/ingest/program` | Ingest program |
| POST | `/ingest/company` | Ingest company |
| POST | `/ingest/contact` | Ingest contact |
| POST | `/ingest/jobs` | Ingest jobs batch |
| POST | `/ingest/scraper-batch` | Batch ingest from Data-Scraper |

### Agent Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/agent/program` | Program intelligence agent |
| GET | `/agent/company` | Company research agent |
| GET | `/agent/contact` | Contact finder agent |
| GET | `/agent/strategy` | BD strategy agent |

### Workflow Orchestration
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/workflow/capture` | Capture strategy workflow |
| GET | `/workflow/competitor` | Competitor analysis workflow |
| GET | `/workflow/quick` | Quick intelligence query |

### CrewAI Agents
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/agents/status` | CrewAI agent status |
| POST | `/agents/analyze-program` | Analyze program (4-agent workflow) |
| POST | `/agents/prepare-outreach` | Prepare outreach materials |
| POST | `/agents/weekly-intel` | Weekly BD intelligence report |

### Specialized Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/program/{name}` | Program intelligence |
| GET | `/company/{name}` | Company intelligence |
| GET | `/contacts/at/{company}` | Contacts at company |
| GET | `/jobs/for/{program}` | Jobs for program |

### Indexing
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/index/all` | Full reindex |
| POST | `/index/{collection}` | Index specific collection |

### PageIndex & Cache
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/pageindex/index` | Index for audit |
| GET | `/pageindex/query` | Query with audit trail |
| GET | `/pageindex/stats` | PageIndex statistics |
| GET | `/cache/stats` | Cache statistics |
| DELETE | `/cache/clear` | Clear cache |

### Module Routers (when available)
| Prefix | Module | Endpoints |
|--------|--------|-----------|
| `/documents/*` | Document Processor | Document processing pipeline |
| `/pageindex/*` | Retrieval | Page-level indexing |
| `/ultrarag/*` | Ultra RAG | Advanced retrieval |
| `/lightrag/*` | LightRAG | Knowledge graph RAG |
| `/streaming/*` | Streaming | Real-time streaming |
| `/memory/*` | Memory | Memory operations |
| `/dify/*` | Dify Integration | Dify bridges |
| `/ragflow/*` | RAGflow | Deep document RAG |
| `/api/v2/*` | Unified API | Unified endpoints |

---

## 9. External Integrations

| Service | Port/URL | Status | Purpose |
|---------|----------|--------|---------|
| **Qdrant** | localhost:6333 | ✅ Active | Vector database |
| **Knowledge API** | localhost:8100 | ✅ Active | FastAPI server |
| **Notion** | api.notion.com | ✅ Configured | Database sync |
| **Apify** | apify.com | ✅ Configured | Web scraping |
| **n8n** | Configurable | ✅ Configured | Workflow orchestration |
| **Mapify/XMind** | mapify.so | ✅ Configured | Mind map generation |
| **Dify** | localhost:3000 | 🔧 Optional | Visual AI orchestration |
| **RAGflow** | localhost:80 | 🔧 Optional | Deep document RAG |
| **Redis** | localhost:6379 | 🔧 Optional | Semantic caching |
| **PostgreSQL** | localhost:5432 | 🔧 Optional | pgvector storage |

---

## 10. Dependencies

### Core
- `python-dotenv>=1.0.0` - Environment management
- `requests>=2.31.0` - HTTP client
- `pydantic>=2.6.0` - Data validation
- `pydantic-settings>=2.1.0` - Settings management

### AI/LLM
- `anthropic>=0.18.0` - Claude API
- `openai>=1.12.0` - OpenAI embeddings
- `crewai>=0.30.0` - Multi-agent orchestration
- `langchain-anthropic` - LangChain integration

### Vector & Embeddings
- `qdrant-client>=1.7.0` - Qdrant vector database
- `sentence-transformers>=2.2.0` - Embeddings
- `tiktoken>=0.5.0` - Tokenization

### RAG Framework
- `llama-index>=0.10.0` - RAG framework
- `llama-index-vector-stores-qdrant>=0.1.0`
- `llama-index-llms-anthropic>=0.1.0`
- `llama-index-embeddings-huggingface>=0.1.0`

### Knowledge Graph
- `lightrag-hku>=0.1.0` - Graph RAG

### Hybrid Retrieval
- `rank-bm25>=0.2.2` - BM25 keyword search
- `transformers>=4.35.0` - CrossEncoder reranking

### Memory & Caching
- `mem0ai>=0.1.0` - Memory layer
- `redis>=5.0.0` - Semantic caching

### Data Processing
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical computing
- `scipy>=1.11.0` - Scientific computing

### Web Scraping
- `beautifulsoup4>=4.12.0` - HTML parsing
- `lxml>=4.9.0` - XML/HTML processing
- `firecrawl-py>=0.0.1` - Web scraping
- `crawl4ai>=0.2.0` - AI web crawling

### Document Processing
- `docling>=0.1.0` - Document parsing
- `python-magic-bin>=0.4.14` - File type detection

### API Server
- `fastapi>=0.109.0` - API framework
- `uvicorn>=0.27.0` - ASGI server

### Database
- `psycopg2-binary>=2.9.0` - PostgreSQL
- `notion-client>=2.2.0` - Notion API

### Evaluation
- `ragas>=0.1.0` - RAG evaluation
- `datasets>=2.16.0` - Dataset handling

### Observability
- `tenacity>=8.2.0` - Retry logic
- `structlog>=24.1.0` - Structured logging
- `slowapi>=0.1.9` - Rate limiting

### Testing
- `pytest>=7.4.0` - Testing framework
- `pytest-cov>=4.1.0` - Coverage reporting

---

## 11. Summary Statistics

| Metric | Value |
|--------|-------|
| **Total Python Scripts** | 199 |
| **Total TypeScript Files** | 35 |
| **Total JSON Configs** | 264+ |
| **Total Documentation** | 209+ markdown files |
| **Total CSV Data Files** | 247+ |
| **Total Project Size** | ~1.2 GB |
| **Database Size** | ~1.03 GB |
| **Vector Records** | 8,447 |
| **Prime Contractor Contacts** | 13,089 |
| **Federal Programs** | 388 |
| **API Endpoints** | 50+ |
| **CrewAI Agents** | 13 |
| **MCP Servers** | 6 |
| **n8n Workflows** | 18 |
| **Test Files** | 15 |

---

## 12. Current Gaps & Issues

### Missing Configurations
- [ ] Redis not running (optional caching disabled)
- [ ] RAGflow not deployed (optional deep document RAG)
- [ ] Dify not deployed (optional visual AI orchestration)
- [ ] PostgreSQL/pgvector not configured (using Qdrant instead)

### Incomplete Features
- [ ] Engine 6 QA & Alerts - Partially implemented
- [ ] Full pipeline integration - Individual engines work, master orchestrator needs completion
- [ ] Streaming pipeline - Pathway config exists but not fully integrated
- [ ] Dashboard backend connection - Frontend exists, needs API wiring

### Items Needing Attention
- [ ] `.env` file needs actual API keys (currently using .env.example template)
- [ ] Some MCP servers need npm build before use
- [ ] Jobs collection only has 4 records - needs scraper runs to populate
- [ ] Dify integration bridges exist but Dify not deployed
- [ ] Some test files may need updating for recent changes

### Recommended Next Steps
1. Run full indexing to populate all vector collections
2. Configure and test n8n workflows
3. Deploy Dify for visual AI workflow building (optional)
4. Complete Engine 6 QA system
5. Wire up dashboard to live API endpoints
6. Set up scheduled scraper runs via Apify

---

## Appendix: Quick Start Commands

```bash
# Start Knowledge API
python Engine8_Knowledge/api.py
# Runs on http://localhost:8100

# Run full indexing
python Engine8_Knowledge/scripts/index_all_data.py

# CLI search
python Engine8_Knowledge/scripts/vector_store.py --search "DCGS analyst" --collection contacts

# Run single engine
python Engine2_ProgramMapping/scripts/pipeline.py

# Run tests
pytest tests/ -v

# Build MCP servers
cd mcp/knowledge-mcp-server && npm install && npm run build
cd mcp/mapify-mcp-server && npm install && npm run build
```

---

*Report generated by Claude Code on 2026-02-03*
