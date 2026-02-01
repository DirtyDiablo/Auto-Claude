# BD-Automation-Engine - Deep Architecture & Capabilities Audit

**Audit Date:** 2026-02-01
**Project:** PTS BD Intelligence System - BD Automation Engine
**Target:** DCGS Portfolio (~$950M)

---

## SECTION 1: KNOWN INFRASTRUCTURE VALIDATION

### 1A. Validate Known Tech Stack Components

#### AI/LLM SDKs

| Component | Status | Version/Location | Notes |
|-----------|--------|------------------|-------|
| Anthropic SDK | ✅ FOUND | `anthropic>=0.18.0` | 88 references, used in Engine2, Engine8, services |
| OpenAI SDK | ✅ FOUND | `openai>=1.12.0` | 57 references, embeddings and LLM calls |
| LlamaIndex | ⚠️ PARTIAL | 6 references | Imported but minimal usage |
| LangChain | ⚠️ PARTIAL | 12 references | `langchain_anthropic.ChatAnthropic` used for CrewAI agents |
| LangGraph | ⚠️ PARTIAL | 1 reference | Minimal, not core architecture |
| CrewAI | ✅ FOUND | 75 references | Full agent orchestration in `Engine8_Knowledge/agents/` |
| RAGAS | ✅ FOUND | 11 references | `Engine8_Knowledge/evaluation/ragas_evaluator.py` |
| DSPy | ❌ NOT FOUND | - | Not implemented |

#### Vector & Search

| Component | Status | Version/Location | Notes |
|-----------|--------|------------------|-------|
| Qdrant | ✅ FOUND | `qdrant-client>=1.7.0` | 199 references, 6 collections (738MB total) |
| Sentence Transformers | ✅ FOUND | `sentence-transformers>=2.2.0` | 11 references, `all-MiniLM-L6-v2` for embeddings |
| BM25 | ✅ FOUND | `rank_bm25` | 57 references, hybrid search implementation |
| Redis | ✅ FOUND | `redis` | 58 references, semantic caching layer |
| ChromaDB | ⚠️ PARTIAL | 1 reference | Not primary, fallback only |
| FAISS | ❌ NOT FOUND | - | Not implemented |
| Meilisearch | ❌ NOT FOUND | - | Not implemented |

#### Knowledge Graphs & RAG

| Component | Status | Version/Location | Notes |
|-----------|--------|------------------|-------|
| LightRAG | ✅ FOUND | 111 references | `Engine8_Knowledge/bd_lightrag/` full implementation |
| GraphRAG | ⚠️ PARTIAL | 26 references | Referenced but LightRAG is primary |
| NetworkX | ❌ NOT FOUND | - | Not used |
| Neo4j | ❌ NOT FOUND | - | Not used (Qdrant + LightRAG instead) |

#### Memory Systems

| Component | Status | Version/Location | Notes |
|-----------|--------|------------------|-------|
| Mem0 | ✅ FOUND | 49 references | `Engine8_Knowledge/scripts/memory_layer.py` |
| Zep | ❌ NOT FOUND | - | Not implemented |
| Custom Memory | ✅ FOUND | 340 references | SQLite + JSON fallback system |

#### Web Scraping

| Component | Status | Version/Location | Notes |
|-----------|--------|------------------|-------|
| Apify | ✅ FOUND | 11 references | MCP integration, `.mcp.json` configured |
| Firecrawl | ✅ FOUND | 16 references | n8n workflow integration |
| Crawl4AI | ✅ FOUND | 13 references | Referenced in integrations |
| BeautifulSoup | ❌ NOT FOUND | 0 in code | Listed in requirements but unused |
| Selenium/Playwright | ❌ NOT FOUND | - | Not implemented |

#### Web Frameworks

| Component | Status | Version/Location | Notes |
|-----------|--------|------------------|-------|
| FastAPI | ✅ FOUND | 35 references | `Engine8_Knowledge/api.py` - 50+ endpoints |
| Flask | ❌ NOT FOUND | - | Not used |
| Express | ❌ NOT FOUND | - | MCP servers use TypeScript SDK |

#### Frontend

| Component | Status | Version/Location | Notes |
|-----------|--------|------------------|-------|
| React | ✅ FOUND | `react@^19.2.0` | Dashboard in `dashboard/` |
| Vite | ✅ FOUND | `vite@^7.2.4` | Build tool |
| TailwindCSS | ✅ FOUND | `tailwindcss@^4.1.18` | Styling |
| Recharts | ✅ FOUND | `recharts@^3.6.0` | Charts |
| D3.js | ✅ FOUND | `d3-force@^3.0.0` | Force graphs |
| Force Graph | ✅ FOUND | `react-force-graph-2d@^1.29.0` | Network visualization |
| Zustand | ✅ FOUND | `zustand@^5.0.10` | State management |

#### Document Processing

| Component | Status | Version/Location | Notes |
|-----------|--------|------------------|-------|
| python-docx | ✅ FOUND | 21 references | Document handling |
| openpyxl | ✅ FOUND | 5 references | Excel processing |
| python-pptx | ⚠️ PARTIAL | 3 references | Minimal usage |
| Docling | ✅ FOUND | In requirements | Document processing |

#### Federal Data APIs

| Component | Status | Notes |
|-----------|--------|-------|
| USASpending | ❌ NOT FOUND | Not implemented |
| FPDS | ✅ FOUND | `Engine2_ProgramMapping/data/enrich-federal-programs-v3.py` |
| SAM.gov | ❌ NOT FOUND | Not implemented |
| GovCon API | ❌ NOT FOUND | Not implemented |

#### Workflow & Orchestration

| Component | Status | Version/Location | Notes |
|-----------|--------|------------------|-------|
| n8n | ✅ FOUND | 1047 references | 18 workflow JSON files in `n8n/` |
| Kestra | ❌ NOT FOUND | - | Not used |
| Temporal | ❌ NOT FOUND | - | Not used |
| Celery | ❌ NOT FOUND | - | Not used |

#### MCP (Model Context Protocol)

| Component | Status | Version/Location | Notes |
|-----------|--------|------------------|-------|
| MCP Server Definitions | ✅ FOUND | `.mcp.json` | 6 servers configured |
| bd-knowledge MCP | ✅ FOUND | `mcp/knowledge-mcp-server/` | 30+ tools |
| n8n MCP | ✅ FOUND | npm package | Workflow integration |
| Notion MCP | ✅ FOUND | Both local and remote | Database operations |
| Apify MCP | ✅ FOUND | npm package | Scraping integration |
| Mapify MCP | ✅ FOUND | `mcp/mapify-mcp-server/` | Mind mapping |

#### DevOps & Infrastructure

| Component | Status | Notes |
|-----------|--------|-------|
| Docker | ❌ NOT FOUND | No Dockerfile in project |
| pip/requirements | ✅ FOUND | `requirements.txt` with 40+ dependencies |
| npm/package.json | ✅ FOUND | Dashboard and MCP servers |
| Git | ✅ FOUND | Tracked repository |
| .env management | ✅ FOUND | `.env`, `.env.example` |
| Logging | ✅ FOUND | Python `logging` module throughout |
| Testing | ⚠️ PARTIAL | 18 test files, limited coverage |

### 1B. Discovery Command Results

#### Directory Structure (Top 3 Levels)
```
./Engine1_Scraper/            # Apify configurations
./Engine2_ProgramMapping/     # Job standardization + program matching
./Engine3_OrgChart/           # Contact classification
./Engine4_Playbook/           # BD playbook generation
./Engine5_Scoring/            # Priority scoring
./Engine6_QA/                 # Quality assurance
./Engine7_BullhornETL/        # CRM data extraction (293MB DB)
./Engine8_Knowledge/          # AI Knowledge System (739MB)
./dashboard/                  # React frontend (290MB)
./dify_integration/           # Visual AI orchestration bridges
./mcp/                        # MCP servers (103MB)
./n8n/                        # Workflow definitions
./services/                   # Integration services
./tests/                      # Test suite
./outputs/                    # Generated files
./docs/                       # Documentation
./streaming/                  # Streaming API
./memory/                     # Memory routes
```

#### File Type Census
| Type | Count |
|------|-------|
| Python | 697 |
| JavaScript | 12 |
| TypeScript | 484 |
| JSX/TSX | 340 |
| JSON | 359 |
| YAML/YML | 31 |
| Markdown | 304 |
| CSV | 180 |
| SQL/DB | 13 |
| HTML | 7 |
| Shell | 35 |

#### Disk Usage (Top Directories)
| Directory | Size |
|-----------|------|
| Engine8_Knowledge/ | 739M |
| Engine7_BullhornETL/ | 370M |
| dashboard/ | 290M |
| mcp/ | 103M |
| outputs/ | 52M |
| docs/ | 52M |
| Engine3_OrgChart/ | 32M |

#### Large Files (>1MB)
| File | Size | Purpose |
|------|------|---------|
| `Engine8_Knowledge/data/qdrant/.../documents/storage.sqlite` | 298M | Documents vector store |
| `Engine7_BullhornETL/data/bullhorn_master.db` | 293M | Bullhorn CRM data |
| `Engine8_Knowledge/data/qdrant/.../contacts/storage.sqlite` | 226M | Contacts vector store |
| `Engine8_Knowledge/data/qdrant/.../activities/storage.sqlite` | 210M | Activities vector store |

#### Environment Variables Referenced
Key environment variables found:
- `ANTHROPIC_API_KEY` - Claude API
- `OPENAI_API_KEY` - Embeddings
- `NOTION_TOKEN` - Notion integration
- `APIFY_API_TOKEN` - Web scraping
- `N8N_API_KEY`, `N8N_API_URL` - Workflow orchestration
- `QDRANT_URL`, `QDRANT_API_KEY` - Vector database
- `REDIS_URL` - Semantic caching
- `KNOWLEDGE_API_URL` - Knowledge API (port 8100)
- 9 Notion Database IDs configured

#### Ports Referenced
| Port | Service |
|------|---------|
| 8100 | Knowledge API (FastAPI) |
| 6333 | Qdrant (default) |
| 6379 | Redis (default) |
| 3000 | Dify UI |

---

## SECTION 2: AI / ML / LLM DEEP INVENTORY

### 2A. LLM API Calls — Complete Inventory

#### Anthropic Claude API Calls

| File Path | Function/Class | Purpose | Model | Streaming |
|-----------|---------------|---------|-------|-----------|
| `Engine2_ProgramMapping/scripts/job_standardizer.py:351` | `standardize_job()` | Job field extraction | claude-3-sonnet (default) | No |
| `Engine8_Knowledge/agents/base_agent.py:85` | `BDAgent.run()` | Base agent execution | claude-3-sonnet | No |
| `Engine8_Knowledge/agents/bd_agents.py:316` | `ChatAnthropic()` | CrewAI agent LLM | claude-3-sonnet | No |
| `Engine8_Knowledge/bd_lightrag/graph_rag.py:186` | LLM function | LightRAG queries | claude-3-haiku | No |
| `Engine8_Knowledge/scripts/auto_tagger.py:285` | `AutoTagger.tag()` | Entity tagging | claude-3-sonnet | No |
| `Engine8_Knowledge/scripts/rag_engine.py:265` | `BDRAGEngine.ask()` | RAG Q&A | claude-3-sonnet | No |
| `scripts/job_ingestion/ai_enrichment.py:113` | Job enrichment | Field extraction | claude-3-sonnet | No |
| `services/ai_enrichment/engine.py:303,514,554,593` | Multiple | Notion enrichment | claude-3-sonnet | No |

**Error Handling:** All calls use try/except with logging. No retry logic implemented.
**Token Estimation:** ~500-2000 input, ~200-1000 output per call
**Cost Estimation:** $0.003 - $0.015 per call (Sonnet pricing)

#### OpenAI API Calls

| File Path | Function | Purpose | Model |
|-----------|----------|---------|-------|
| `Engine8_Knowledge/scripts/vector_store.py:256` | `embeddings.create()` | Vector embeddings | text-embedding-3-small |
| `index_*.py` (multiple) | `embeddings.create()` | Bulk indexing | text-embedding-3-small |

**Embedding Dimensions:** 1536 (OpenAI standard)

### 2B. Embedding Operations — Complete Inventory

| File Path | Model | Dimensions | What Gets Embedded | Batch Size |
|-----------|-------|------------|-------------------|------------|
| `Engine8_Knowledge/scripts/vector_store.py` | text-embedding-3-small | 1536 | All collections | 100 |
| `Engine8_Knowledge/bd_lightrag/graph_rag.py` | all-MiniLM-L6-v2 | 384 | LightRAG entities | Variable |
| `Engine8_Knowledge/scripts/hybrid_retriever.py` | all-MiniLM-L6-v2 | 384 | Query embeddings | 1 |
| `index_contacts_openai.py` | text-embedding-3-small | 1536 | Contacts | 50 |
| `index_activities_openai.py` | text-embedding-3-small | 1536 | Activities | 50 |

**Embedding Model Inconsistency:** Two models in use (OpenAI 1536d and MiniLM 384d)

### 2C. RAG Pipelines — Complete Inventory

#### Primary RAG: `Engine8_Knowledge/scripts/rag_engine.py`
| Field | Value |
|-------|-------|
| Pipeline Name | BDRAGEngine |
| Retrieval Method | Hybrid (Vector + BM25) |
| Embedding Model | text-embedding-3-small / all-MiniLM-L6-v2 |
| Chunking Strategy | Token-based |
| Chunk Size | Not explicitly configured (uses defaults) |
| Reranking | CrossEncoder (ms-marco-MiniLM-L-6-v2) |
| Top-K | 5-10 configurable |
| Citation Tracking | Yes (sources array) |
| Confidence Scoring | Yes (0-1 score) |
| Fallback Strategy | Returns empty with low confidence |

#### LightRAG Pipeline: `Engine8_Knowledge/bd_lightrag/graph_rag.py`
| Field | Value |
|-------|-------|
| Pipeline Name | BDLightRAG |
| Retrieval Method | Knowledge Graph + Vector |
| Embedding Model | all-MiniLM-L6-v2 (384d) |
| Entity Extraction | LLM-based |
| Relationship Types | Program-Contact, Contact-Company, etc. |
| Query Modes | naive, local, global, hybrid |

### 2D. Knowledge Graph Operations

| Field | Value |
|-------|-------|
| Implementation | LightRAG |
| Storage Location | `Engine8_Knowledge/data/lightrag/` |
| Entity Types | Programs, Contacts, Companies, Locations |
| Relationship Types | works_at, manages, contracts_with, located_at |
| Query Patterns | Relationship traversal, entity search |
| Integration | API endpoints at `/graph/*`, `/bdgraph/*` |

### 2E. AI Agents — Complete Inventory

#### CrewAI Agents (4 agents)

| Agent Name | Role | LLM | Tools |
|------------|------|-----|-------|
| ProgramIntelAgent | Program research | ChatAnthropic | hybrid_retriever, graph queries |
| CompanyResearchAgent | Company intelligence | ChatAnthropic | hybrid_retriever |
| ContactFinderAgent | Contact discovery | ChatAnthropic | hybrid_retriever |
| BDStrategyAgent | Strategic analysis | ChatAnthropic | All above |

**CrewAI Orchestration:** `Engine8_Knowledge/agents/crewai_orchestrator.py`
- `get_orchestrator()` factory function
- Multi-agent workflows in `Engine8_Knowledge/agents/workflows.py`

#### BDAgent Base Class
- Location: `Engine8_Knowledge/agents/base_agent.py`
- Memory: Hybrid retriever access
- Error Handling: Try/except with logging

### 2F. Memory Systems — Complete Inventory

| System | Backend | Storage Location | What Stored | Cross-Session |
|--------|---------|-----------------|-------------|---------------|
| Mem0 | Qdrant | `data/qdrant/collection/mem0/` | Conversational memory | Yes |
| Redis Cache | Redis/In-Memory | localhost:6379 | Query cache | Configurable TTL |
| SQLite Memories | SQLite | `data/memories.db` | Persistent insights | Yes |
| JSON Fallback | File | `data/memory/*.json` | Backup storage | Yes |

---

## SECTION 3: DATA ARCHITECTURE — COMPLETE SCHEMA AUDIT

### 3A. Local Databases

| Database | Size | Tables | Purpose |
|----------|------|--------|---------|
| `Engine7_BullhornETL/data/bullhorn_master.db` | 293M | contacts, activities, notes | CRM data |
| `Engine8_Knowledge/data/bd_graph.db` | ~1M | entities, relationships | Knowledge graph |
| `Engine8_Knowledge/data/memories.db` | ~100K | memories, insights | Memory layer |
| `Engine8_Knowledge/data/page_index.db` | ~50K | pages, metadata | Document index |
| `data/page_index.db` | ~50K | pages | Duplicate index |

### 3B. Vector Store Collections

| Collection | Vectors | Dimensions | Distance | Payload Fields |
|------------|---------|------------|----------|----------------|
| documents | ~8,000+ | 1536 | Cosine | doc_id, title, doc_type, source, content |
| contacts | ~7,300+ | 1536 | Cosine | name, title, company, tier, priority |
| activities | ~5,000+ | 1536 | Cosine | type, date, contact_id, notes |
| programs | ~400+ | 1536 | Cosine | name, acronym, agency, prime |
| jobs | ~200+ | 1536 | Cosine | title, company, location, bd_score |
| mem0 | Variable | 1536 | Cosine | memory_id, user_id, content |

**Total Qdrant Storage:** ~738MB

### 3C. CSV/JSON Data Files (Large Files)

| Path | Size | Records | Purpose |
|------|------|---------|---------|
| `Engine7_BullhornETL/outputs/notion_contacts.csv` | 30M | ~7,300 | Contact export |
| `Engine7_BullhornETL/outputs/all_call_notes_records.json` | 26M | ~5,000 | Call notes |
| `Engine3_OrgChart/data/Prime_Contacts/Master_All_Contacts.json` | 11M | ~2,000 | Master contacts |
| `outputs/bd_dashboard/contacts_classified.json` | 9.6M | ~2,000 | Classified contacts |
| `outputs/bd_dashboard/mindmap_nodes.json` | 7.8M | ~10,000 | Mindmap data |

### 3D. Notion Database Integration

**Databases Referenced in .env.example:**
| Database | ID | Usage |
|----------|-----|-------|
| DCGS Contacts | 2ccdef65-baa5-8087-a53b-000ba596128e | Primary contacts |
| GDIT Other Contacts | 70ea1c94-211d-40e6-a994-e8d7c4807434 | Secondary contacts |
| GDIT Jobs | 2563119e7914442cbe0fb86904a957a1 | Job postings |
| Program Mapping Hub | f57792c1-605b-424c-8830-23ab41c47137 | Central hub |
| Federal Programs | 06cd9b22-5d6b-4d37-b0d3-ba99da4971fa | 388 programs |
| BD Opportunities | 2bcdef65-baa5-80ed-bd95-000b2f898e17 | Opportunities |
| Contractors | 3a259041-22bf-4262-a94a-7d33467a1752 | Contractor list |
| Contract Vehicles | 0f09543e-9932-44f2-b0ab-7b4c070afb81 | Vehicles |

**Operations Found:** 435 Notion references - search, create, update, fetch operations

---

## SECTION 4: PIPELINE & WORKFLOW ARCHITECTURE

### 4A. Data Processing Pipelines

#### Pipeline 1: Job Processing Pipeline
```
[Apify Scrape] → [Job Standardizer] → [Program Mapper] → [BD Scorer] → [Notion Export]
```

| Step | File | Input | Output | Error Handling |
|------|------|-------|--------|----------------|
| Scrape | n8n/Apify workflow | URL configs | Raw jobs JSON | n8n retry |
| Standardize | `Engine2_ProgramMapping/scripts/job_standardizer.py` | Raw jobs | 11-field schema | try/except |
| Map | `Engine2_ProgramMapping/scripts/program_mapper.py` | Standardized jobs | Program matches | try/except |
| Score | `Engine5_Scoring/scripts/bd_scoring.py` | Mapped jobs | BD scores 0-100 | try/except |
| Export | `Engine2_ProgramMapping/scripts/exporters.py` | Scored jobs | Notion/CSV | try/except |

#### Pipeline 2: Contact Classification Pipeline
```
[Bullhorn ETL] → [Contact Classifier] → [Tier Assignment] → [Notion Sync]
```

| Step | File | Input | Output |
|------|------|-------|--------|
| ETL | `Engine7_BullhornETL/scripts/` | Bullhorn DB | Contacts JSON |
| Classify | `Engine3_OrgChart/scripts/contact_classifier.py` | Contacts | Tier 1-6 |
| Sync | Notion MCP | Classified | Notion DB |

#### Pipeline 3: Knowledge Indexing Pipeline
```
[Documents/Contacts/Programs] → [Chunker] → [Embedder] → [Qdrant] → [BM25 Index]
```

### 4B. Scheduling & Automation

| Type | Reference | Schedule |
|------|-----------|----------|
| n8n Webhooks | `PTS_BD_WF1-6*.json` | Event-driven |
| Orchestrator | `orchestrator.py:814` | Interval-based loop |
| File Watcher | `Engine8_Knowledge/scripts/file_watcher.py` | Polling (configurable) |

**No cron jobs detected in codebase.**

### 4C. API Endpoints (50+ total)

#### Core Search/RAG Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/search` | Vector search |
| GET | `/search` | Query param search |
| GET | `/search/semantic` | Semantic only |
| GET | `/search/keyword` | BM25 only |
| GET | `/search/hybrid` | Combined search |
| POST | `/ask` | RAG Q&A |
| GET | `/ask/smart` | Auto-routed query |

#### Knowledge Graph Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/graph/query` | Graph queries |
| GET | `/graph/relationships` | Relationship traversal |
| GET | `/bdgraph/program/{name}` | Program intel |
| GET | `/bdgraph/contact/{name}` | Contact intel |
| GET | `/bdgraph/teaming/{from}/{to}` | Teaming analysis |

#### Memory Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/memory/add` | Add memory |
| GET | `/memory/search` | Search memories |
| GET | `/memory/stats` | Memory statistics |

#### Agent Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/agents/list` | List agents |
| GET | `/agents/invoke` | Invoke agent |
| GET | `/agents/program` | Program agent |
| GET | `/agents/company` | Company agent |

### 4D. External API Dependencies

| Service | Base URL | Auth | Purpose |
|---------|----------|------|---------|
| Anthropic | api.anthropic.com | API Key | LLM calls |
| OpenAI | api.openai.com | API Key | Embeddings |
| Notion | api.notion.com | Bearer Token | Database ops |
| n8n | primetech.app.n8n.cloud | API Key | Workflows |
| Apify | api.apify.com | Token | Scraping |
| FPDS | fpds.gov | None | Contract data |
| Bullhorn | cls40.bullhornstaffing.com | OAuth | CRM data |

---

## SECTION 5: MCP SERVER & TOOL AUDIT

### 5A. MCP Servers Defined

| Server | Transport | Location | Tools |
|--------|-----------|----------|-------|
| bd-knowledge | stdio | `mcp/knowledge-mcp-server/` | 30+ |
| n8n | stdio | npm package | Workflow tools |
| notion | stdio | npm package | DB operations |
| notion-remote | SSE/HTTP | mcp.notion.com | Hosted version |
| apify | stdio | npm package | Scraping actors |
| mapify | stdio | `mcp/mapify-mcp-server/` | Mind mapping |

### 5B. BD Knowledge MCP Tools (30+)

| Tool Name | Purpose | API Endpoint |
|-----------|---------|--------------|
| smart_ask | Intelligent query routing | /ask/smart |
| search_knowledge | Collection search | /search |
| semantic_search | Vector search | /search/semantic |
| keyword_search | BM25 search | /search/keyword |
| hybrid_search | Combined + rerank | /search/hybrid |
| ask_knowledge | RAG Q&A | /ask |
| query_knowledge_graph | Graph queries | /graph/query |
| get_program_intel | Program details | /bdgraph/program/{name} |
| get_contact_intel | Contact details | /bdgraph/contact/{name} |
| analyze_teaming | Teaming paths | /bdgraph/teaming/{from}/{to} |
| add_memory | Store memory | /memory/add |
| search_memory | Retrieve memory | /memory/search |
| get_stats | System statistics | /stats |
| ingest_document | Add documents | /ingest/document |

---

## SECTION 6: FRONTEND & DASHBOARD AUDIT

### 6A. Frontend Architecture

| Field | Value |
|-------|-------|
| Framework | React 19.2 |
| Build Tool | Vite 7.2 |
| CSS Framework | TailwindCSS 4.1 |
| Component Library | Custom + Radix UI |
| State Management | Zustand 5.0 |
| Charts | Recharts 3.6 |
| Graph Visualization | react-force-graph-2d 1.29 |
| Data Fetching | Fetch API |
| Routing | Hash-based |
| Total Components | 17 TSX files |

### 6B. Component Inventory

| Component | Purpose | Data Source |
|-----------|---------|-------------|
| Sidebar.tsx | Navigation | Static |
| ThemeSwitcher.tsx | Dark/light mode | Local state |
| DataFreshness.tsx | Data timestamp | File metadata |
| MindMapCanvas.tsx | Knowledge graph viz | JSON files |
| MindMapNode.tsx | Node rendering | Props |
| ControlBar.tsx | Map controls | Local state |
| ContextMenu.tsx | Right-click menu | Event |
| AIMapGenerator.tsx | AI map creation | API call |
| SmartSearchBar.tsx | Search interface | API call |
| AgentCard.tsx | Agent status | API call |
| SystemStatsCard.tsx | System metrics | API call |
| AnimatedCounter.tsx | Animated numbers | Props |

### 6C. Dashboard Data Sources

| View | Data Source | Refresh | Type |
|------|------------|---------|------|
| Contacts | `public/data/contacts_classified.json` | Manual | Static |
| Jobs | `public/data/jobs.json` | Manual | Static |
| Programs | `public/data/programs.json` | Manual | Static |
| Org Chart | `public/data/contact_org_chart.json` | Manual | Static |
| Mindmap | `public/data/mindmap_*.json` | Manual | Static |

**Note:** Dashboard uses pre-generated static JSON files, not live API.

---

## SECTION 7: SECURITY & RESILIENCE AUDIT

### 7A. Secrets Management

| Check | Status |
|-------|--------|
| API keys in .env | ✅ Yes |
| .env in .gitignore | ✅ Yes |
| .env.example exists | ✅ Yes (comprehensive) |
| No hardcoded secrets | ⚠️ Some env vars in .mcp.json (but as ${VAR}) |
| Secrets in git history | ❌ Not checked (would need git log review) |

### 7B. Error Handling Audit

| Metric | Count |
|--------|-------|
| Try/except blocks | 601 |
| Bare except (except:) | 52 (8.6%) |
| Generic except Exception | Part of 52 |
| Specific exceptions | 169 |

**Maturity Level:** 3 - Functional (mix of generic and specific handling)

### 7C. Rate Limiting & Retry Logic

| Operation | Strategy | Adequate? |
|-----------|----------|-----------|
| Notion API | `time.sleep(0.35)` | ⚠️ Basic |
| LLM calls | None | ❌ Missing |
| Qdrant ops | None | ⚠️ Should add |
| n8n webhooks | n8n handles | ✅ Yes |
| Parallel indexing | `time.sleep(10 * attempt)` | ✅ Exponential backoff |

### 7D. Input Validation

| Metric | Count |
|--------|-------|
| Pydantic models | 104 references |
| BaseModel classes | 20+ in api.py |
| Field validation | Yes (FastAPI) |

**Status:** API layer has Pydantic validation; internal functions often use raw dicts.

---

## SECTION 8: CROSS-PROJECT INTEGRATION MAPPING

### 8A. Shared Data Paths

No explicit references to other PTS projects found in codebase. This project appears self-contained.

### 8B. Shared Configurations

| Config Key | This Project | Expected Standard | Match? |
|-----------|--------------|-------------------|--------|
| Qdrant URL | localhost:6333 | localhost:6333 | ✅ |
| Qdrant Collections | 6 collections | bd_documents | ⚠️ Different schema |
| Embedding Model | text-embedding-3-small / all-MiniLM-L6-v2 | all-MiniLM-L6-v2 | ⚠️ Mixed |
| Embedding Dimensions | 1536 (OpenAI) / 384 (MiniLM) | 384 | ⚠️ Inconsistent |
| LLM Provider | Anthropic | Anthropic | ✅ |
| LLM Model | claude-3-sonnet | claude-sonnet-4-20250514 | ⚠️ Different version |
| Priority Score Hot | ≥80 | ≥80 | ✅ |
| Priority Score Warm | 50-79 | 50-79 | ✅ |
| Priority Score Cold | <50 | <50 | ✅ |
| Contact Tier Mapping | Tier 1-6 | Tier 1-6 | ✅ |

---

## SECTION 9: DEPENDENCY HEALTH & VERSION ANALYSIS

### 9A. Python Dependencies (Key Packages)

| Package | Version | Status |
|---------|---------|--------|
| anthropic | >=0.18.0 | ✅ Current |
| openai | >=1.12.0 | ✅ Current |
| qdrant-client | >=1.7.0 | ✅ Current |
| sentence-transformers | >=2.2.0 | ✅ Current |
| fastapi | Not pinned | ⚠️ Should pin |
| uvicorn | Not pinned | ⚠️ Should pin |
| pandas | >=2.0.0 | ✅ Current |
| notion-client | >=2.2.0 | ✅ Current |

### 9B. Node Dependencies (Dashboard)

| Package | Version | Status |
|---------|---------|--------|
| react | ^19.2.0 | ✅ Latest |
| vite | ^7.2.4 | ✅ Latest |
| tailwindcss | ^4.1.18 | ✅ Latest |
| recharts | ^3.6.0 | ✅ Current |
| zustand | ^5.0.10 | ✅ Current |

### 9C. Version Conflicts

- **Embedding dimensions mismatch:** OpenAI (1536) vs MiniLM (384) used in different places
- **No major conflicts detected** between declared dependencies

---

## SECTION 10: MATURITY SCORING

| Capability | Score | Evidence | Enhancement Needed |
|-----------|-------|----------|-------------------|
| **LLM Integration** | 4 | Multiple models, structured prompts, error handling | Add retry logic |
| **Embedding Pipeline** | 3 | Working but inconsistent models | Standardize on one model |
| **Vector Search (Qdrant)** | 4 | 6 collections, production data | Add backup strategy |
| **RAG Pipeline** | 4 | Hybrid search, reranking, citations | Add evaluation metrics |
| **Knowledge Graph** | 3 | LightRAG implemented | Needs more entity types |
| **AI Agent Orchestration** | 3 | CrewAI 4 agents | Add human-in-loop |
| **Memory System** | 3 | Mem0 + Redis + fallback | Consolidate backends |
| **Job Scraping** | 4 | Apify + n8n integration | Add more sources |
| **Job Standardization** | 4 | LLM extraction, 11 fields | Add validation |
| **Program Mapping** | 4 | Multi-signal matching | Add confidence UI |
| **Contact Classification** | 4 | 6-tier system | Add ML classifier |
| **BD Score Calculation** | 4 | Weighted algorithm | Add A/B testing |
| **Outreach Generation** | 2 | Basic templates | Needs personalization |
| **HUMINT Tracking** | 2 | Call notes indexed | Needs structured capture |
| **Notion Integration** | 4 | Full CRUD operations | Add sync monitoring |
| **n8n Workflow Integration** | 4 | 18 workflows | Add error alerting |
| **API Layer** | 4 | 50+ endpoints, Pydantic | Add rate limiting |
| **MCP Server/Tools** | 4 | 30+ tools, well-documented | Add more agents |
| **Frontend/Dashboard** | 3 | Static data, good viz | Add live API |
| **Error Handling** | 3 | Mix of generic/specific | Standardize patterns |
| **Logging & Observability** | 2 | Basic logging module | Add structured logging |
| **Testing** | 2 | 18 test files, low coverage | Add integration tests |
| **Documentation** | 4 | Good README, CLAUDE.md | Add API docs |
| **Security** | 3 | Env vars, .gitignore | Add secrets scanning |
| **Data Validation** | 3 | Pydantic at API | Add internal validation |
| **Performance/Caching** | 3 | Redis cache implemented | Add metrics |
| **Cross-Project Integration** | 2 | Self-contained | Needs shared config |

**Average Maturity Score: 3.2 / 5**

---

## SECTION 11: CODE QUALITY & TECHNICAL DEBT

### 11A. TODO/FIXME Inventory

**Count:** 4 TODO/FIXME markers found (very low - good sign)

### 11B. Dead Code Detection

Limited dead code detected. Most Python files are imported/used.

### 11C. Duplicate Logic Detection

| Pattern | Files | Standardization Opportunity |
|---------|-------|---------------------------|
| LLM client init | 8+ files | Create shared factory |
| Embedding functions | 5+ files | Standardize model choice |
| Qdrant collection access | 10+ files | Create unified client |
| Error handling patterns | Throughout | Create standard decorator |

### 11D. Hardcoded Values

**Location mappings hardcoded in:**
- `Engine2_ProgramMapping/scripts/job_standardizer.py`
- `Engine2_ProgramMapping/scripts/program_mapper.py`
- `Engine3_OrgChart/scripts/contact_classifier.py`

**Recommendation:** Move to configuration files.

---

## SECTION 12: ENHANCEMENT OPPORTUNITY SCORING

### 12A. Quick Wins (< 1 day, high impact)

| Enhancement | Current | Target | Files | Impact |
|-------------|---------|--------|-------|--------|
| Standardize embedding model | Mixed 1536/384 | Single 1536 | 5 files | High |
| Add LLM retry logic | None | 3 retries + backoff | 8 files | High |
| Enable prompt caching | Off | On | 8 files | 60% cost reduction |
| Add structured logging | Basic | JSON structured | All | High |
| Add API rate limiting | None | FastAPI middleware | api.py | Medium |

### 12B. Standardization Opportunities

| What | Current Variations | Proposed Standard | Files |
|------|-------------------|-------------------|-------|
| Embedding model | OpenAI + MiniLM | text-embedding-3-small (1536d) | 5 |
| LLM model string | Various claude-3-* | claude-sonnet-4-20250514 | 8 |
| Error pattern | Bare/generic/specific | Specific with logging | All |
| Config loading | os.getenv scattered | Central config module | All |
| Qdrant client | Per-file init | Singleton pattern | 10 |

### 12C. Missing Capabilities (Gaps)

| Missing | Why It Matters | Complexity | Priority |
|---------|---------------|------------|----------|
| Reranking (API level) | 20-40% precision boost | Low | Critical |
| Structured output (LLM) | Type-safe responses | Medium | High |
| Observability (OpenTelemetry) | Debug production | Medium | High |
| Prompt caching | 60% cost reduction | Low | High |
| Streaming responses | Better UX | Low | Medium |
| Async LLM calls | Parallel processing | Medium | High |
| Circuit breaker | API resilience | Medium | Medium |
| Automated testing | CI/CD coverage | High | Critical |
| Database migrations | Schema versioning | Medium | High |
| Live dashboard data | Replace static JSON | Medium | High |

### 12D. AI/ML Specific Enhancements

| Enhancement | What It Enables | Current Blocker | Path |
|-------------|----------------|-----------------|------|
| Semantic chunking | Better retrieval | Using token-based | Add semantic splitter |
| Confidence calibration | Trust scoring | Ad-hoc thresholds | Add evaluation pipeline |
| Active learning | User feedback loop | No feedback capture | Add UI + storage |
| Cost tracking | Monitor LLM spend | No metrics | Add token counting |
| Evaluation framework | RAG quality metrics | RAGAS stubbed | Implement RAGAS fully |
| Multi-modal support | Image/PDF analysis | Text-only | Add vision models |

### 12E. Fortification Recommendations

| Area | Current Risk | Mitigation | Priority |
|------|-------------|------------|----------|
| No retry on LLM failures | Single point of failure | Add tenacity/backoff | Critical |
| No input validation (internal) | Type errors | Add Pydantic everywhere | High |
| No rate limiting on API | Abuse potential | Add slowapi | High |
| No health checks | Silent failures | Add /health endpoint | Medium |
| No graceful degradation | Full failures | Add fallback logic | Medium |
| No vector store backup | Data loss risk | Add backup script | High |
| No audit logging | Compliance gap | Add audit trail | Medium |

---

## SECTION 13: SUMMARY METRICS TABLE

| Metric | Value |
|--------|-------|
| **Project Name** | BD-Automation-Engine |
| **Total Files** | 2,462+ |
| **Total Lines of Code** | ~95,000 (66,499 Python + 28,478 TypeScript) |
| **Python Files** | 697 |
| **JS/TS Files** | 836 (484 TS + 340 TSX + 12 JS) |
| **Config Files** | 30+ |
| **Data Files (CSV/JSON/DB)** | 552 (180 CSV + 359 JSON + 13 DB) |
| **Total Disk Usage** | ~1.6GB |
| **LLM API Call Points** | 18 unique call sites |
| **LLM Models Used** | claude-3-sonnet, claude-3-haiku, gpt-4o |
| **Embedding Models Used** | text-embedding-3-small (1536d), all-MiniLM-L6-v2 (384d) |
| **Vector Collections** | 6 |
| **Total Vectors** | ~21,000+ |
| **RAG Pipelines** | 2 (BDRAGEngine, LightRAG) |
| **AI Agents** | 4 (Program, Company, Contact, Strategy) |
| **MCP Servers** | 6 |
| **MCP Tools** | 30+ |
| **API Endpoints** | 50+ |
| **External APIs** | 7 (Anthropic, OpenAI, Notion, n8n, Apify, FPDS, Bullhorn) |
| **Notion DBs Referenced** | 8 |
| **n8n Workflows Referenced** | 18 |
| **Scheduled Tasks** | 0 (event-driven only) |
| **Data Pipelines** | 3 (Job, Contact, Knowledge) |
| **Frontend Components** | 17 |
| **Test Files** | 18 |
| **TODO/FIXME Count** | 4 |
| **Average Maturity Score** | 3.2 / 5 |
| **Critical Enhancements** | 5 |
| **Quick Wins** | 5 |

---

## APPENDIX: KEY FILE LOCATIONS

### Core Python Files
- `Engine8_Knowledge/api.py` - Main FastAPI server (50+ endpoints)
- `Engine8_Knowledge/scripts/vector_store.py` - Qdrant operations
- `Engine8_Knowledge/scripts/rag_engine.py` - RAG implementation
- `Engine8_Knowledge/scripts/hybrid_retriever.py` - Hybrid search
- `Engine8_Knowledge/scripts/memory_layer.py` - Mem0 integration
- `Engine8_Knowledge/bd_lightrag/graph_rag.py` - LightRAG
- `Engine8_Knowledge/agents/` - CrewAI agents
- `Engine2_ProgramMapping/scripts/job_standardizer.py` - Job extraction
- `Engine2_ProgramMapping/scripts/program_mapper.py` - Program matching
- `Engine3_OrgChart/scripts/contact_classifier.py` - Contact tiers
- `Engine5_Scoring/scripts/bd_scoring.py` - BD scoring

### Key Configuration Files
- `.env.example` - Complete env var template
- `.mcp.json` - MCP server configuration
- `requirements.txt` - Python dependencies
- `dashboard/package.json` - Frontend dependencies

### Data Locations
- `Engine8_Knowledge/data/qdrant/` - Vector store (738MB)
- `Engine7_BullhornETL/data/bullhorn_master.db` - CRM data (293MB)
- `dashboard/public/data/` - Static dashboard data
- `outputs/` - Generated outputs

---

*Report generated: 2026-02-01*
*Auditor: Claude Opus 4.5*
