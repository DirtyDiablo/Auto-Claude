# N8N Builder - Deep Architecture & Capabilities Audit

**Audit Date:** 2026-02-01
**Project Path:** C:\N8N Builder
**Git Branch:** master (clean)

---

## SECTION 1: KNOWN INFRASTRUCTURE VALIDATION

### 1A. Validate Known Tech Stack Components

#### AI/LLM SDKs

| Component | Status | Details |
|-----------|--------|---------|
| Anthropic SDK (Claude API) | ✅ FOUND | `browser_automation/browser_agent.py`, `external/akshayakula-OpenSAM/src/app/api/chat/route.ts` - Uses ChatAnthropic, claude-sonnet-4-20250514 |
| OpenAI SDK | ✅ FOUND | `browser_automation/browser_agent.py`, `external/akshayakula-OpenSAM/*` - Uses ChatOpenAI, gpt-4o |
| LlamaIndex | ❌ NOT FOUND | No llama_index imports detected |
| LangChain | ⚠️ PARTIAL | Only referenced in text patterns in `src/enrichment/technology_extractor.py` |
| LangGraph | ✅ FOUND | **Primary workflow engine** - `bd_langgraph/` module with StateGraph, checkpointing, nodes |
| CrewAI | ❌ NOT FOUND | No crewai imports |
| RAGAS | ❌ NOT FOUND | No RAGAS evaluation framework |
| DSPy | ❌ NOT FOUND | No DSPy optimization |

#### Vector & Search

| Component | Status | Details |
|-----------|--------|---------|
| Qdrant | ❌ NOT FOUND | No Qdrant references |
| Sentence Transformers | ✅ FOUND | `src/knowledge_base/indexer.py`, `src/knowledge_base/search.py` - all-MiniLM-L6-v2 (384 dims) |
| BM25 | ❌ NOT FOUND | No BM25 implementation |
| Redis | ❌ NOT FOUND | No Redis references |
| ChromaDB | ⚠️ PARTIAL | In `external/akshayakula-OpenSAM/` only, migration script to Pinecone |
| LanceDB | ✅ FOUND | **Primary vector store** - `src/knowledge_base/` uses LanceDB for embeddings |
| FAISS | ❌ NOT FOUND | No FAISS references |
| Meilisearch | ❌ NOT FOUND | No Meilisearch references |

#### Knowledge Graphs & RAG

| Component | Status | Details |
|-----------|--------|---------|
| LightRAG | ❌ NOT FOUND | No LightRAG implementation |
| Microsoft GraphRAG | ❌ NOT FOUND | No GraphRAG implementation |
| NetworkX | ❌ NOT FOUND | No NetworkX graphs |
| Neo4j | ❌ NOT FOUND | No Neo4j references |

#### Memory Systems

| Component | Status | Details |
|-----------|--------|---------|
| Mem0 | ❌ NOT FOUND | No Mem0 integration |
| Zep | ❌ NOT FOUND | No Zep integration |
| LangGraph Memory | ✅ FOUND | `bd_langgraph/checkpointer.py` - SqliteSaver and MemorySaver for workflow state |
| Custom Memory | ⚠️ PARTIAL | SQLite checkpoints for workflow state persistence |

#### Web Scraping

| Component | Status | Details |
|-----------|--------|---------|
| Apify | ✅ FOUND | `external/IncrediblyHungie-sam-gov-scraper/`, `src/intelligence/apify_job_intelligence_pipeline.py` |
| Firecrawl | ❌ NOT FOUND | No Firecrawl references |
| Crawl4AI | ❌ NOT FOUND | No Crawl4AI references |
| Selenium/Playwright | ✅ FOUND | Playwright in `external/akshayakula-OpenSAM/`, `external/govbizops/` |
| browser-use | ✅ FOUND | **Primary browser automation** - `browser_automation/browser_agent.py` - AI-driven browser control |
| BeautifulSoup | ❌ NOT FOUND | No BeautifulSoup references |
| Scrapy | ❌ NOT FOUND | No Scrapy references |

#### Web Frameworks

| Component | Status | Details |
|-----------|--------|---------|
| FastAPI | ❌ NOT FOUND | No FastAPI endpoints in main project |
| Flask | ⚠️ PARTIAL | Only in `external/` subdirectories - `external/govbizops/`, `external/ataddesse-govConDiscovery/` |
| Express | ⚠️ PARTIAL | In `external/capture-mcp-server/` MCP server |

#### Frontend

| Component | Status | Details |
|-----------|--------|---------|
| React | ⚠️ PARTIAL | Only in `external/akshayakula-OpenSAM/` (Next.js app) |
| Vite | ❌ NOT FOUND | No Vite in main project |
| TailwindCSS | ⚠️ PARTIAL | In `external/akshayakula-OpenSAM/` only |
| Recharts | ❌ NOT FOUND | No Recharts |
| D3.js | ❌ NOT FOUND | No D3.js |
| Force Graph | ❌ NOT FOUND | No force-graph |
| Reagraph | ❌ NOT FOUND | No Reagraph |

#### Document Processing

| Component | Status | Details |
|-----------|--------|---------|
| Stirling-PDF | ❌ NOT FOUND | No Stirling-PDF |
| Docling | ❌ NOT FOUND | No Docling |
| PaddleOCR | ❌ NOT FOUND | No PaddleOCR |
| Marker | ❌ NOT FOUND | No Marker |
| python-docx | ❌ NOT FOUND | No python-docx |
| openpyxl | ❌ NOT FOUND | No openpyxl |

#### Federal Data APIs

| Component | Status | Details |
|-----------|--------|---------|
| USASpending | ✅ FOUND | `external/usaspending-api/`, `external/capture-mcp-server/`, `bd_langgraph/integrations.py` |
| FPDS | ✅ FOUND | `src/config/settings.py` - FPDS_BASE_URL configured |
| SAM.gov | ✅ FOUND | `browser_automation/bd_tasks.py`, `external/capture-mcp-server/`, `.mcp.json` |
| GovCon API (Tango) | ✅ FOUND | **Primary API** - `src/api_clients/tango.py`, `external/tango-node/`, `external/tango-python/` |

#### Workflow & Orchestration

| Component | Status | Details |
|-----------|--------|---------|
| n8n | ✅ FOUND | **Core orchestration** - `client/n8n_client.py`, `workflows/`, `.mcp.json` points to primetech.app.n8n.cloud |
| Kestra | ❌ NOT FOUND | No Kestra references |
| Temporal | ❌ NOT FOUND | No Temporal references |
| Celery | ❌ NOT FOUND | No Celery references |

#### CRM & Contact Tools

| Component | Status | Details |
|-----------|--------|---------|
| Proxycurl | ❌ NOT FOUND | No Proxycurl references |
| ZoomInfo | ⚠️ PARTIAL | Target generation scripts in `src/intelligence/create_zoominfo_targets.py` |
| Reacher | ❌ NOT FOUND | No Reacher references |
| LinkedIn API | ✅ FOUND | Browser automation in `browser_automation/bd_tasks.py` for LinkedIn |

#### MCP (Model Context Protocol)

| Component | Status | Details |
|-----------|--------|---------|
| MCP server definitions | ✅ FOUND | 3 MCP servers configured in `.mcp.json` |
| n8n MCP | ✅ FOUND | `npx n8n-mcp` - connects to primetech.app.n8n.cloud |
| capture-mcp-server | ✅ FOUND | `external/capture-mcp-server/` - 15 tools for USASpending, SAM, Tango |
| knowledge-base MCP | ✅ FOUND | `src/knowledge_base/mcp_server.py` - semantic search |
| n8n-orchestrator-mcp | ✅ FOUND | `mcp/n8n-orchestrator-mcp/` - 20+ workflow tools |
| Notion MCP | ❌ NOT FOUND | No Notion MCP configured |
| Apify MCP | ❌ NOT FOUND | No Apify MCP configured |

#### DevOps & Infrastructure

| Component | Status | Details |
|-----------|--------|---------|
| Docker | ❌ NOT FOUND | No Dockerfile in main project |
| Poetry/pip | ⚠️ PARTIAL | Only `pyproject.toml` in external projects |
| npm/pnpm/yarn | ✅ FOUND | Multiple `package.json` in external/ and mcp/ |
| Git | ✅ FOUND | Active repo, 7 recent commits |
| Environment management | ✅ FOUND | `.env.example`, dotenv loading in config files |
| Logging | ✅ FOUND | Python logging throughout, `src/utils/logging.py` |
| Testing | ⚠️ PARTIAL | `bd_langgraph/test_langgraph.py` with pytest, minimal coverage |

### 1B. Discovery Command Results

#### Directory Structure
```
./bd_langgraph/          - LangGraph workflow pipelines
./browser_automation/    - AI browser automation (browser-use)
./client/               - n8n Python client
./config/               - Configuration files
./data/                 - Data files (1.7GB)
./design_intelligence/  - UI/Design system intelligence
./docs/                 - Documentation
./exports/              - Export outputs
./external/             - Third-party integrations (355MB)
./hub/                  - Hub integration
./knowledge-base/       - LanceDB vector store (37MB)
./logs/                 - Log files
./mcp/                  - MCP server implementations (33MB)
./output/               - Pipeline outputs (77MB)
./projects/             - Project architecture docs
./scripts/              - Utility scripts
./src/                  - Core Python source (2.1MB)
./tasks/                - Task definitions
./workflows/            - n8n workflow JSON files
```

#### File Type Census
| Type | Count |
|------|-------|
| Python | 1,672 |
| JavaScript | 40 |
| TypeScript | 101 |
| JSX/TSX | 16 |
| JSON | 172 |
| YAML/YML | 31 |
| Markdown | 610 |
| CSV | 720 |
| SQL/DB | 972 |
| HTML | 26 |
| Shell | 31 |

#### Disk Usage (Top Directories)
| Directory | Size |
|-----------|------|
| data/ | 1.7G |
| external/ | 355M |
| output/ | 77M |
| knowledge-base/ | 37M |
| mcp/ | 33M |
| src/ | 2.1M |
| docs/ | 792K |
| bd_langgraph/ | 452K |

---

## SECTION 2: AI / ML / LLM DEEP INVENTORY

### 2A. LLM API Calls — Complete Inventory

#### Browser Automation LLM Usage

| Field | Value |
|-------|-------|
| File Path | `browser_automation/browser_agent.py` |
| Function/Class | `BrowserAgent._create_llm()` |
| Purpose | AI-driven browser control for BD tasks |
| Provider | OpenAI or Anthropic (configurable) |
| Model | gpt-4o (OpenAI) or claude-sonnet-4-20250514 (Anthropic) |
| Temperature | Not specified (defaults) |
| Max Tokens | Not specified |
| System Prompt | Task-specific (e.g., "Search for entity in SAM.gov") |
| Input Format | Natural language task instructions |
| Output Format | Browser actions executed |
| Streaming | No |
| Error Handling | Try/except with logging |
| Token Estimation | ~500-2000 tokens per task |
| Cost Estimation | ~$0.01-0.05 per browser task |

#### External OpenSAM Chat API

| Field | Value |
|-------|-------|
| File Path | `external/akshayakula-OpenSAM/src/app/api/chat/route.ts` |
| Function/Class | `callOpenAI()`, `callAnthropic()` |
| Purpose | SAM.gov contract data chat assistant |
| Provider | OpenAI and Anthropic |
| Model | Configurable via API request |
| Streaming | Yes (supported) |
| Error Handling | Try/catch with error messages |

### 2B. Embedding Operations — Complete Inventory

| Field | Value |
|-------|-------|
| File Path | `src/knowledge_base/indexer.py`, `src/knowledge_base/search.py` |
| Embedding Model | all-MiniLM-L6-v2 (HuggingFace/SentenceTransformers) |
| Dimensions | 384 |
| What Gets Embedded | Python code, Markdown docs, CSV headers, JSON configs |
| Batch Size | Not specified (single document processing) |
| Where Stored | LanceDB at `knowledge-base/embeddings/knowledge.lance` |
| Triggered By | Manual indexing runs |
| Last Known Vector Count | 6 manifest versions (multiple indexing runs) |

#### External Embedding Usage

| Field | Value |
|-------|-------|
| File Path | `external/ataddesse-govConDiscovery/gov-con-search-flask/govConSearch.py` |
| Embedding Model | all-mpnet-base-v2 |
| Dimensions | 768 |
| Purpose | Contract search similarity |

### 2C. RAG Pipelines — Complete Inventory

| Field | Value |
|-------|-------|
| Pipeline Name | Knowledge Base Search |
| File Path | `src/knowledge_base/search.py` |
| Retrieval Method | Vector search (cosine similarity via LanceDB) |
| Embedding Model | all-MiniLM-L6-v2 |
| Chunking Strategy | Word-based with overlap |
| Chunk Size | 500 words |
| Chunk Overlap | 50 words |
| Reranking | ❌ No reranking implemented |
| Top-K | Configurable (default 10) |
| Context Window Management | Simple concatenation |
| Citation Tracking | File path and line tracking |
| Confidence Scoring | Distance score from LanceDB |
| Fallback Strategy | Empty result list |

### 2D. Knowledge Graph Operations

**Status:** ❌ NOT FOUND

No knowledge graph implementation detected. The project uses flat vector search without entity/relationship modeling.

### 2E. AI Agents — Complete Inventory

#### Browser Agent

| Field | Value |
|-------|-------|
| Agent Name | BrowserAgent / BDBrowserAgent |
| Framework | browser-use library (custom wrapper) |
| Role/Purpose | AI-driven web automation for BD tasks |
| LLM Model | gpt-4o or claude-sonnet-4-20250514 |
| Tools Available | Browser navigation, form filling, screenshot |
| Memory Access | No persistent memory |
| Human-in-Loop | Rate limiting and safety prompts |
| Error Handling | Try/except with logging |
| Currently Working | Yes (requires API keys) |

**BD Tasks Available:**
- SAM.gov verification
- SAM.gov opportunity lookup
- LinkedIn company search
- LinkedIn contact discovery
- Bullhorn authentication

#### LangGraph Workflow Agents

| Field | Value |
|-------|-------|
| Agent Name | BD Proposal Pipeline |
| Framework | LangGraph (StateGraph) |
| Role/Purpose | Multi-step BD proposal generation |
| LLM Model | No direct LLM calls (uses integrations) |
| State Schema | BDProposalState dataclass |
| Graph Structure | research → contacts → competition → strategy → review → playbook |
| Human-in-Loop | ✅ Interrupt before process_feedback |
| Error Handling | Try/except with status tracking |
| Currently Working | Partially (placeholder integrations) |

**LangGraph Workflow Nodes:**
1. `research_opportunity` - Find similar contracts
2. `gather_contacts` - CRM and SAM.gov contacts
3. `analyze_competition` - Competitive landscape
4. `generate_strategy` - BD strategy creation
5. `request_human_review` - Human approval checkpoint
6. `process_human_feedback` - Handle feedback
7. `finalize_playbook` - Generate final playbook

### 2F. Memory Systems — Complete Inventory

| Field | Value |
|-------|-------|
| System | LangGraph Checkpointing |
| Config Location | `bd_langgraph/checkpointer.py` |
| Storage Backend | SQLite (SqliteSaver) or Memory (MemorySaver) |
| Storage Location | `data/langgraph_checkpoints.db` |
| What Gets Stored | Workflow state snapshots |
| Retention Policy | No automatic cleanup |
| Retrieval Method | Thread ID lookup |
| Cross-Session | ✅ Yes with SqliteSaver |
| Integration Points | BD Proposal, Contact Outreach, Recompete workflows |

---

## SECTION 3: DATA ARCHITECTURE — COMPLETE SCHEMA AUDIT

### 3A. Local Databases

| Database | Path | Purpose |
|----------|------|---------|
| langgraph_checkpoints.db | `data/langgraph_checkpoints.db` | LangGraph workflow state persistence |

### 3B. Vector Store Collections

| Field | Value |
|-------|-------|
| Collection Name | documents |
| Vector Dimensions | 384 |
| Distance Metric | Cosine (LanceDB default) |
| Approximate Vector Count | 6 indexed versions |
| Payload Fields | file, content, type, directory, chunk_id, hash |
| Embedding Model Used | all-MiniLM-L6-v2 |
| Index Type | LanceDB native |
| Quantization | None |

### 3C. CSV/JSON Data Files

**Data Directory (1.7GB):**
- `data/bullhorn/` - CRM exports
- `data/contacts_databases/` - Contact databases
- `data/federal/contracts/` - Federal contract data
- `data/program_notion_export_databases/` - Notion exports
- `data/reference/` - Lookup tables

**Output Directory (77MB):**
- `output/bd_databases/` - BD categorized data
- `output/intelligence/` - Intelligence reports
- `output/program_intelligence/` - Program analysis

### 3D. Notion Database Integration Points

**Status:** ⚠️ LIMITED

Notion references found:
- `workflows/notion/notion-to-hub.json` - Sync workflow (disabled)
- `workflows/notion/sync-jobs-to-notion.json` - Job sync workflow
- `mcp/n8n-orchestrator-mcp/src/index.ts` - `sync_jobs_to_notion` tool

**No direct Notion API client implementation found in main project.**

---

## SECTION 4: PIPELINE & WORKFLOW ARCHITECTURE

### 4A. Data Processing Pipelines

#### BD Proposal Pipeline (LangGraph)
```
[Trigger: Manual]
  → research_opportunity (search contracts)
  → gather_contacts (CRM + SAM.gov)
  → analyze_competition (competitive landscape)
  → generate_strategy (BD strategy)
  → request_human_review (⏸ INTERRUPT)
  → process_human_feedback
  → finalize_playbook
  → [Output: BD Playbook]
```

#### Knowledge Base Pipeline
```
[Trigger: Manual indexing]
  → Document discovery (glob patterns)
  → File processing (Python/MD/CSV/JSON handlers)
  → Text chunking (500 words, 50 overlap)
  → Embedding generation (all-MiniLM-L6-v2)
  → LanceDB storage
  → [Output: Searchable vector store]
```

#### Apify Job Intelligence Pipeline
```
[Trigger: Manual/Scheduled]
  → Load Apify jobs
  → Standardize job data
  → Program mapping
  → Intelligence extraction
  → [Output: Job intelligence reports]
```

### 4B. Scheduling & Automation

**n8n Workflows (20+ defined):**

| Workflow | Type | Purpose |
|----------|------|---------|
| daily-scrape-sync.json | Scheduled | Daily job scraping |
| weekly-report.json | Scheduled | Weekly BD report |
| hub-smart-query.json | Webhook | Intelligent Hub queries |
| scraper-webhook.json | Webhook | Scraping triggers |
| full-bd-pipeline.json | Pipeline | Complete BD pipeline |

### 4C. API Endpoints — Complete Map

**N8N Client (`client/n8n_client.py`):**
- Workflow CRUD operations
- Execution management
- Webhook triggering

**No standalone REST API in main project.**

### 4D. External API Dependencies

| Service | Base URL | Auth Method | Rate Limit | Purpose |
|---------|----------|-------------|------------|---------|
| n8n Cloud | primetech.app.n8n.cloud | API Key | N/A | Workflow orchestration |
| Tango/MakeGov | api.makegov.com | API Key | 100/min, 25K/day | Federal contracts |
| USASpending | api.usaspending.gov | None | 1000/hour | Spending data |
| SAM.gov | api.sam.gov | API Key | 10/min | Entity/opportunity data |
| FPDS | fpds.gov/ezsearch | None | N/A | Contract data |

---

## SECTION 5: MCP SERVER & TOOL AUDIT

### 5A. MCP Servers Defined

| Server Name | File Location | Transport | Tools Count |
|-------------|---------------|-----------|-------------|
| n8n-mcp | npx n8n-mcp | stdio | 80+ (external package) |
| capture-mcp-server | external/capture-mcp-server/dist/server.js | stdio/HTTP | 15 |
| knowledge-base | src/knowledge_base/mcp_server.py | stdio | 4 |
| n8n-orchestrator-mcp | mcp/n8n-orchestrator-mcp/build/index.js | stdio | 20+ |

### 5B. MCP Tools Detail

#### capture-mcp-server Tools (15 total)

| Tool Name | Purpose |
|-----------|---------|
| get_usaspending_awards | Federal awards by agency |
| get_usaspending_spending_by_category | Spending breakdown |
| get_usaspending_budgetary_resources | Budget data |
| search_usaspending_awards_by_recipient | Recipient award search |
| search_sam_entities | SAM.gov entity search |
| get_sam_opportunities | Contract opportunities |
| get_sam_entity_details | Entity details by UEI |
| check_sam_exclusions | Exclusion verification |
| search_tango_contracts | Tango contract search |
| search_tango_grants | Grant search |
| get_tango_vendor_profile | Vendor profiles |
| search_tango_opportunities | Opportunity search |
| get_tango_spending_summary | Spending analytics |
| get_entity_and_awards | Combined entity+awards |
| get_opportunity_spending_context | Opportunity context |

#### knowledge-base MCP Tools (4 total)

| Tool Name | Purpose |
|-----------|---------|
| kb_search | Semantic search over project files |
| kb_find_similar | Find similar files |
| kb_program_search | Program-specific search |
| kb_reindex | Re-index knowledge base |

#### n8n-orchestrator-mcp Tools (20+ total)

| Tool Name | Purpose |
|-----------|---------|
| hub_smart_query | Intelligent Hub queries |
| hub_search | Hybrid search |
| hub_ingest_jobs | Job ingestion |
| hub_add_insight | Add BD insights |
| sync_jobs_to_notion | Notion sync |
| trigger_scrape | Start scraping |
| get_bd_report | BD report generation |
| list_workflows | List n8n workflows |
| execute_workflow | Execute workflow |
| ... | (20+ total tools) |

---

## SECTION 6: FRONTEND & DASHBOARD AUDIT

### 6A. Frontend Architecture

**Main Project:** ❌ No frontend implementation

**External Projects (reference only):**
- `external/akshayakula-OpenSAM/` - Next.js React app with TailwindCSS
- `external/govbizops/simple_viewer.py` - Flask simple viewer

### 6B. Component Inventory

**No frontend components in main project.**

### 6C. Dashboard Data Sources

**No dashboard implementation in main project.**

---

## SECTION 7: SECURITY & RESILIENCE AUDIT

### 7A. Secrets Management

**Finding:** ⚠️ **API KEYS IN .mcp.json**

The `.mcp.json` file contains API keys (this file is gitignored):
- N8N_API_KEY (JWT token)
- SAM_GOV_API_KEY
- TANGO_API_KEY

**Status:**
- ✅ `.mcp.json` is already in `.gitignore` (line 6)
- ✅ `.mcp.json` is NOT tracked in git
- ✅ `.mcp.json.example` template exists with placeholders

**Recommendations:**
1. ✅ Already gitignored - keys are not exposed in repo
2. Consider rotating keys if they were ever committed previously
3. Use environment variables via `.env` file where possible

**Positive Findings:**
- `.env.example` exists with documented variables
- Environment variables used in config files
- dotenv loading implemented

### 7B. Error Handling Audit

| Metric | Count |
|--------|-------|
| Try/except blocks | 689 |
| Bare except (Exception) | 477 |
| Specific exceptions | 233 |

**Error Handling Maturity: Level 2 (Basic)**

Most error handling uses generic `except Exception` which:
- Catches all errors indiscriminately
- May hide specific failure modes
- Limited retry/recovery logic

### 7C. Rate Limiting & Retry Logic

**Implemented:**
- `browser_automation/safety.py` - Domain-based rate limiting
- `browser_automation/config.py` - Rate limit configs per domain
- `bd_langgraph/edges.py` - Workflow retry logic
- `src/config/settings.py` - API rate limits defined

**Rate Limit Configuration:**
| Service | Rate Limit |
|---------|------------|
| Tango API | 100/min, 25K/day |
| USASpending | 60/min |
| SAM.gov | 10/min |
| sam.gov (browser) | 10/min |

### 7D. Input Validation

**Status:** ⚠️ LIMITED

- No Pydantic models for input validation
- Basic type checking in functions
- Dataclasses used for state (not validation)

---

## SECTION 8: CROSS-PROJECT INTEGRATION MAPPING

### 8A. Shared Data Paths

No direct cross-project file references found. Projects are intended to be independent but share:
- n8n Cloud instance (primetech.app.n8n.cloud)
- Notion databases (via n8n webhooks)
- Federal data APIs (Tango, SAM, USASpending)

### 8B. Shared Configurations

| Config Key | This Project's Value | Expected Standard |
|-----------|---------------------|-------------------|
| Qdrant URL | ❌ Not used | http://localhost:6333 |
| Qdrant Collection | ❌ Not used | bd_documents |
| Embedding Model | all-MiniLM-L6-v2 ✅ | all-MiniLM-L6-v2 |
| Embedding Dimensions | 384 ✅ | 384 |
| LLM Provider | openai/anthropic ✅ | anthropic |
| LLM Model | gpt-4o/claude-sonnet-4-20250514 ✅ | claude-sonnet-4-20250514 |
| n8n MCP URL | primetech.app.n8n.cloud ✅ | primetech.app.n8n.cloud |
| Tango Base URL | https://api.makegov.com ✅ | https://api.makegov.com |

---

## SECTION 9: DEPENDENCY HEALTH & VERSION ANALYSIS

### 9A. Python Dependencies

**No requirements.txt or pyproject.toml in main project root.**

Key dependencies inferred from imports:
- langgraph / langgraph-checkpoint-sqlite
- sentence-transformers
- lancedb
- browser-use
- requests
- python-dotenv
- dataclasses (stdlib)

### 9B. Node Dependencies

**External package.json files:**
- `external/capture-mcp-server/package.json`
- `external/n8n-mcp/package.json`
- `mcp/n8n-orchestrator-mcp/package.json`

Key dependencies:
- @modelcontextprotocol/sdk
- express
- typescript

---

## SECTION 10: MATURITY SCORING

| Capability | Score (1-5) | Evidence | Enhancement Needed |
|-----------|-------------|----------|-------------------|
| **LLM Integration** | 3 | browser-use + external APIs | Add structured outputs, caching |
| **Embedding Pipeline** | 3 | LanceDB + SentenceTransformers | Add hybrid search, reranking |
| **Vector Search (LanceDB)** | 3 | Working implementation | Add metadata filtering |
| **RAG Pipeline** | 2 | Basic vector search only | Add reranking, hybrid search, evaluation |
| **Knowledge Graph** | 1 | Not implemented | Build relationship extraction |
| **AI Agent Orchestration** | 3 | LangGraph workflows | Complete integration implementations |
| **Memory System** | 3 | SQLite checkpointing | Add semantic memory (Mem0/Zep) |
| **Job Scraping** | 3 | Apify integration | Add more sources |
| **Job Standardization** | 2 | Basic processing | Add schema validation |
| **Program Mapping** | 2 | Placeholder implementations | Complete mapping logic |
| **Contact Classification** | 2 | CRM search only | Add tier classification |
| **BD Score Calculation** | 2 | Basic scoring in integrations | Add comprehensive scoring |
| **Outreach Generation** | 1 | Not implemented | Build outreach templates |
| **HUMINT Tracking** | 1 | Not implemented | Add HUMINT system |
| **Notion Integration** | 2 | n8n webhooks only | Add direct API client |
| **n8n Workflow Integration** | 4 | Python client + MCP tools | Add workflow validation |
| **API Layer** | 2 | No REST API | Build FastAPI layer |
| **MCP Server/Tools** | 4 | 3 servers, 50+ tools | Add more domain tools |
| **Frontend/Dashboard** | 1 | Not implemented | Build React dashboard |
| **Error Handling** | 2 | Generic exceptions | Add specific handlers |
| **Logging & Observability** | 2 | Basic Python logging | Add OpenTelemetry |
| **Testing** | 2 | Minimal pytest tests | Add comprehensive tests |
| **Documentation** | 3 | CLAUDE.md exists | Add API docs |
| **Security** | 3 | Keys gitignored, .env.example exists | Add secret scanning |
| **Data Validation** | 2 | No Pydantic | Add input validation |
| **Performance/Caching** | 1 | No caching | Add Redis/caching layer |
| **Cross-Project Integration** | 2 | Shared n8n only | Define data contracts |

**Average Maturity Score: 2.2 / 5**

---

## SECTION 11: CODE QUALITY & TECHNICAL DEBT

### 11A. TODO/FIXME/HACK Inventory

**Total Count:** 70 TODOs found

Most are in `external/` subdirectories (usaspending-api).

### 11B. Dead Code Detection

Several standalone scripts that may not be integrated:
- `cleanup_workflows.py`
- `debug-api-response.py`
- `dod-discovery-by-target-firms.py`
- `dod-discovery-v4-FAST.py`
- `analyze_notes_report_v2.py`

### 11C. Duplicate Logic Detection

**Potential duplicates found:**
- Multiple enrichment versions: `enrich-federal-programs.py`, `enrich-federal-programs-v2.py`, `enrich-federal-programs-v3.py`, `enrich-federal-programs-v4-TANGO.py`
- Multiple discovery engines: `federal-programs-discovery-engine.py`, `federal-programs-discovery-engine-v2.py`
- Multiple DOD discovery scripts with version suffixes

### 11D. Hardcoded Values

Location and program mappings appear in:
- `src/config/settings.py` (NAICS codes, keywords) ✅ Centralized
- Scattered hardcoded values in discovery scripts ⚠️

---

## SECTION 12: ENHANCEMENT OPPORTUNITY SCORING

### 12A. Quick Wins (< 1 day, high impact)

| Enhancement | Current State | Target State | Files to Change | Impact |
|-------------|--------------|--------------|-----------------|--------|
| ~~Fix API key exposure~~ | ✅ Already gitignored | N/A | N/A | Done |
| Add requirements.txt | No dependency file | Documented deps | requirements.txt | High |
| Add Pydantic validation | Raw dicts | Validated models | bd_langgraph/states.py | High |
| Enable prompt caching | No caching | Anthropic cache | browser_automation/ | High |

### 12B. Standardization Opportunities

| What to Standardize | Current Variations Found | Proposed Standard | Affected Files |
|---------------------|------------------------|-------------------|---------------|
| Embedding models | all-MiniLM-L6-v2, all-mpnet-base-v2 | all-MiniLM-L6-v2 | external/, src/ |
| Error handling | 477 bare excepts | Specific exceptions + logging | All Python files |
| Config loading | Mixed env + hardcoded | Centralized Settings class | All scripts |
| Logging | Basic logging module | Structured logging + levels | src/utils/logging.py |

### 12C. Missing Capabilities (Gaps)

| Missing Capability | Why It Matters | Complexity | Priority |
|-------------------|---------------|------------|----------|
| Reranking in RAG | 20-40% precision boost | Low | Critical |
| Hybrid search (BM25+Vector) | Better retrieval recall | Medium | High |
| Structured output (Pydantic) | Type-safe LLM responses | Low | High |
| Observability (OpenTelemetry) | Can't debug production issues | Medium | High |
| Prompt caching | 60% cost reduction | Low | High |
| API keys rotation | Security | Low | Critical |
| Test coverage | Currently minimal | High | High |
| Frontend dashboard | No visualization | High | Medium |
| HUMINT system | No competitive tracking | High | Medium |

### 12D. AI/ML Specific Enhancements

| Enhancement | What It Enables | Current Blocker | Implementation Path |
|-------------|----------------|-----------------|---------------------|
| Hybrid search (BM25+Vector) | Better retrieval (85-95%) | Not implemented | Add rank_bm25 |
| Reranking (cross-encoder) | Better precision | Not implemented | Add sentence-transformers rerank |
| Semantic chunking | Better chunk quality | Word-based chunking | Add semantic_text_splitter |
| Multi-agent coordination | Complex BD research | Placeholder integrations | Complete LangGraph nodes |
| Confidence calibration | Trust scoring | Not implemented | Add score normalization |
| Evaluation framework (RAGAS) | Measure RAG quality | Not implemented | Add RAGAS |

### 12E. Fortification Recommendations

| Area | Current Risk | Mitigation | Priority |
|------|-------------|------------|----------|
| API keys exposure | LOW - Keys gitignored | Already protected, consider rotation | Low |
| No retry on LLM failures | Medium - Single attempts | Add tenacity retry | High |
| No input validation | Medium - Raw inputs | Add Pydantic | High |
| Limited rate limiting | Low - Config exists | Enforce in all APIs | Medium |
| No health checks | Medium - No monitoring | Add /health endpoints | Medium |
| No backup for vector store | Medium - Data loss risk | Add backup scripts | Medium |

---

## SECTION 13: SUMMARY METRICS TABLE

| Metric | Value |
|--------|-------|
| **Project Name** | N8N Builder |
| **Total Files** | ~3,500+ |
| **Total Lines of Code** | ~150,000+ (estimated) |
| **Python Files** | 1,672 |
| **JS/TS Files** | 141 (40 JS + 101 TS) |
| **Config Files** | 20+ |
| **Data Files (CSV/JSON/DB)** | 1,864 (720 CSV + 172 JSON + 972 SQL/DB) |
| **Total Disk Usage** | ~2.4GB |
| **LLM API Call Points** | 2 (browser-use, external OpenSAM) |
| **LLM Models Used** | gpt-4o, claude-sonnet-4-20250514 |
| **Embedding Models Used** | all-MiniLM-L6-v2, all-mpnet-base-v2 |
| **Vector Collections** | 1 (LanceDB documents) |
| **Total Vectors** | ~6 indexed versions |
| **RAG Pipelines** | 1 (basic) |
| **AI Agents** | 2 (BrowserAgent, LangGraph workflows) |
| **MCP Servers** | 4 |
| **MCP Tools** | 50+ total |
| **API Endpoints** | 0 (client-side only) |
| **External APIs** | 5 (n8n, Tango, SAM, USASpending, FPDS) |
| **Notion DBs Referenced** | 1 (via n8n webhooks) |
| **n8n Workflows Referenced** | 20+ JSON definitions |
| **Scheduled Tasks** | 2 (daily-scrape, weekly-report) |
| **Data Pipelines** | 3 (BD Proposal, Knowledge Base, Job Intelligence) |
| **Frontend Components** | 0 (N/A - external only) |
| **Test Files** | 1 (bd_langgraph/test_langgraph.py) |
| **TODO/FIXME Count** | 70 |
| **Average Maturity Score** | 2.2 / 5 |
| **Critical Enhancements** | 3 |
| **Quick Wins** | 4 |

---

## CRITICAL FINDINGS SUMMARY

### 1. Security Status (Good)
**API keys are properly protected** - `.mcp.json` is already in `.gitignore` and not tracked in git. Template file `.mcp.json.example` exists with placeholder values.

### 2. Architecture Strengths
- Well-structured LangGraph workflow system
- Multiple MCP servers providing rich tool ecosystem
- Centralized configuration in `src/config/settings.py`
- LanceDB vector store with semantic search

### 3. Key Gaps
- No reranking or hybrid search in RAG
- Placeholder implementations in LangGraph integrations
- No frontend/dashboard
- No Pydantic input validation
- Minimal test coverage

### 4. Recommended Priority Actions
1. **Week 1:** Add requirements.txt, Pydantic models
2. **Week 2:** Complete LangGraph integration implementations
3. **Week 3:** Add reranking and hybrid search to RAG
4. **Week 4:** Build test suite

---

*Report generated by Deep Architecture Audit v1.0*
