# DATA-SCRAPER - Deep Architecture & Capabilities Audit

**Audit Date:** 2026-02-01
**Project:** Data-Scraper (PTS BD Intelligence System - Data Writer Component)
**Location:** C:\data-scraper\data-scraper
**Git Branch:** master

---

## SECTION 1: KNOWN INFRASTRUCTURE VALIDATION

### 1A. Validate Known Tech Stack Components

#### AI/LLM SDKs

| Component | Status | Version | Location |
|-----------|--------|---------|----------|
| Anthropic SDK (Claude API) | ✅ FOUND | >=0.18.0 | `pipelines/standardization.py:23`, `requirements.txt:25` |
| OpenAI SDK | ❌ NOT FOUND | - | - |
| LlamaIndex | ❌ NOT FOUND | - | - |
| LangChain | ❌ NOT FOUND | - | - |
| LangGraph | ❌ NOT FOUND | - | - |
| CrewAI | ⚠️ PARTIAL | Referenced only | `hub/hub_client.py:140` (reference to BD Hub agents) |
| RAGAS | ❌ NOT FOUND | - | - |
| DSPy | ❌ NOT FOUND | - | - |

#### Vector & Search

| Component | Status | Version | Location |
|-----------|--------|---------|----------|
| Qdrant | ❌ NOT FOUND | - | - |
| Sentence Transformers | ✅ FOUND | Implicit | `scripts/knowledge/vector_search.py:21` |
| BM25 | ❌ NOT FOUND | - | - |
| Redis | ⚠️ PARTIAL | In external only | `data/external/usaspending-api` |
| ChromaDB | ✅ FOUND | Implicit | `scripts/knowledge/vector_search.py:13-14` |
| FAISS | ❌ NOT FOUND | - | - |
| Meilisearch | ❌ NOT FOUND | - | - |

#### Knowledge Graphs & RAG

| Component | Status | Version | Location |
|-----------|--------|---------|----------|
| LightRAG | ❌ NOT FOUND | - | - |
| Microsoft GraphRAG | ❌ NOT FOUND | - | - |
| NetworkX | ❌ NOT FOUND | - | - |
| Neo4j | ❌ NOT FOUND | - | - |

#### Memory Systems

| Component | Status | Notes |
|-----------|--------|-------|
| Mem0 | ❌ NOT FOUND | - |
| Zep | ❌ NOT FOUND | - |
| Custom Memory | ⚠️ PARTIAL | Hub client has memory endpoints, relies on BD Hub |

#### Web Scraping

| Component | Status | Version | Location |
|-----------|--------|---------|----------|
| Apify | ✅ FOUND | >=1.6.0 | `apify/apify_manager.py`, `requirements.txt:7` |
| Firecrawl | ✅ FOUND | >=1.0.0 | `firecrawl_scraper/federal_scraper.py`, `requirements.txt:8` |
| Crawl4AI | ⚠️ PARTIAL | Referenced in diagnostic | `run_diagnostic.py:24` |
| Selenium/Playwright | ✅ FOUND | >=1.40.0 | `requirements.txt:9` |
| BeautifulSoup | ✅ FOUND | >=4.12.0 | `requirements.txt:10` |
| Scrapy | ❌ NOT FOUND | - | - |

#### Web Frameworks

| Component | Status | Version | Location |
|-----------|--------|---------|----------|
| FastAPI | ✅ FOUND | Implicit | `pdf_processing/pdf_api.py:12-13` |
| Flask | ⚠️ EXTERNAL | In SAM.gov-Scripts | `data/external/SAM.gov-Scripts/app.py` |
| Express | ⚠️ EXTERNAL | In capture-mcp-server | `data/external/capture-mcp-server/` |

#### Federal Data APIs

| Component | Status | Location |
|-----------|--------|----------|
| USASpending | ✅ FOUND | `config/config.yaml:20-23`, `external_apis/api_registry.py:55-62` |
| FPDS | ✅ FOUND | `config/config.yaml:15-18`, `fpds_parser/` |
| SAM.gov | ✅ FOUND | `config/config.yaml:25-28`, `external_apis/api_registry.py:45-53` |
| Tango API | ✅ FOUND | `config/config.yaml:30-34`, `.env` |
| GovCon API | ❌ NOT FOUND | - |

#### Workflow & Orchestration

| Component | Status | Notes |
|-----------|--------|-------|
| n8n | ⚠️ PARTIAL | Webhook references in job descriptions |
| Kestra | ❌ NOT FOUND | - |
| Temporal | ❌ NOT FOUND | - |
| Celery | ❌ NOT FOUND | - |
| APScheduler | ✅ FOUND | `requirements.txt:46` |

#### CRM & Contact Tools

| Component | Status | Location |
|-----------|--------|----------|
| Proxycurl | ❌ NOT FOUND | - |
| ZoomInfo | ⚠️ PARTIAL | Export processing only | `scripts/create_l3harris_master_report.py` |
| Reacher | ❌ NOT FOUND | - |
| LinkedIn API | ⚠️ PARTIAL | Via Apify actor | `apify/apify_manager.py:80-82` |

#### MCP (Model Context Protocol)

| Component | Status | Location |
|-----------|--------|----------|
| MCP Server - data-scraper | ✅ FOUND | `mcp/data-scraper-mcp/src/index.ts` |
| MCP Server - capture | 🆕 FOUND EXTERNAL | `data/external/capture-mcp-server/` |
| MCP Client Usage | ❌ NOT FOUND | - |
| Notion MCP | ❌ NOT FOUND | - |
| n8n MCP | ❌ NOT FOUND | - |
| Apify MCP | ❌ NOT FOUND | - |

#### Document Processing

| Component | Status | Location |
|-----------|--------|----------|
| Stirling-PDF | ✅ FOUND | `pdf_processing/stirling_client.py` |
| Docling | ❌ NOT FOUND | - |
| PaddleOCR | ❌ NOT FOUND | - |
| Marker | ❌ NOT FOUND | - |
| python-docx | ⚠️ PARTIAL | Referenced for parsing | `scripts/knowledge/index_files.py:26` |
| openpyxl | ✅ FOUND | Used in scripts | `scripts/create_l3harris_master_report.py` |

#### DevOps & Infrastructure

| Component | Status | Location |
|-----------|--------|----------|
| Docker | ⚠️ EXTERNAL | `data/external/usaspending-api/Dockerfile` |
| Poetry | ⚠️ EXTERNAL | `data/external/usaspending-api/pyproject.toml` |
| pip/requirements.txt | ✅ FOUND | `requirements.txt` |
| npm | ✅ FOUND | `mcp/data-scraper-mcp/package.json` |
| Git | ✅ FOUND | Active repo |
| Environment Management | ⚠️ SECURITY ISSUE | `.env` with exposed keys |
| Logging | ✅ FOUND | Python logging, loguru in requirements |
| Testing | ⚠️ PARTIAL | 327 test files (mostly in external) |

### 1B. Discovery Command Results

#### Directory Structure
```
.
./.auto-claude (ideation, insights, roadmap, specs)
./.claude
./AI-Powered File Management and Knowledge Base
./apify (external_apis)
./config
./data (apify_exports, cache, external, input, output)
./design_intelligence
./docs
./external_apis
./firecrawl_scraper
./fpds_parser
./hub
./knowledge (companies, contacts, programs, research, _index)
./logs
./mcp (data-scraper-mcp)
./monitoring
./New Enhancements
./notion
./pdf_processing
./pipelines
./scheduler
./scheduling
./scrapers
./scripts (knowledge, lib)
./src (core, scrapers, utils)
./TANGO API
./tests
./validation
```

#### File Type Census

| Type | Count |
|------|-------|
| Python (.py) | 1,601 |
| JavaScript (.js) | 22 |
| TypeScript (.ts) | 16 |
| JSX/TSX | 0 |
| JSON | 9,297 |
| YAML/YML | 29 |
| Markdown (.md) | 328 |
| CSV | 492 |
| SQL/DB | 104 |
| HTML | 9 |
| Shell Scripts | 16 |

#### Disk Usage Top Directories

| Directory | Size |
|-----------|------|
| data/ | 11G |
| mcp/ | 33M |
| knowledge/ | 27M |
| TANGO API/ | 2.2M |
| scripts/ | 1.6M |
| apify/ | 718K |
| src/ | 280K |
| fpds_parser/ | 180K |
| pipelines/ | 164K |
| firecrawl_scraper/ | 132K |

#### Large Files (>1MB)

| File | Size |
|------|------|
| data/input/FY(All)_All_Contracts_Delta_20260108_1.csv | 2.3G |
| data/input/FY(All)_All_Contracts_Delta_20260108_2.csv | 2.1G |
| data/input/FY(All)_All_Contracts_Delta_20260108_3.csv | 205M |
| data/external/dod-budget-data/4-tableau/rdte-r3exhibits.tde | 100M |
| data/output/bullhorn_analysis/notes_intelligence/ALL_NOTES_COMBINED.csv | 72M |

#### Environment Files Found

- `./.auto-claude/.env`
- `./.env` (⚠️ Contains exposed API keys)
- `./data/external/capture-mcp-server/.env.example`
- `./data/external/usaspending-api/.env`
- `./data/external/usaspending-api/.env.template`

#### Config Files Found

- `./config/config.yaml` (main project config)
- Various jest/webpack configs in external directories

---

## SECTION 2: AI / ML / LLM DEEP INVENTORY

### 2A. LLM API Calls — Complete Inventory

**Primary LLM Usage Location:** `pipelines/standardization.py`

| Field | Value |
|-------|-------|
| File Path | `pipelines/standardization.py` |
| Function/Class | `JobStandardizer._extract_skills_llm()`, `JobStandardizer._extract_requirements_llm()` |
| Purpose | Extract technical skills and requirements from job descriptions |
| Provider | Anthropic |
| Model | `claude-sonnet-4-20250514` |
| Temperature | Default (not set) |
| Max Tokens | 500 |
| System Prompt | None (user prompt only) |
| Input Format | Text (job description, max 2000 chars) |
| Output Format | JSON array of strings |
| Streaming | No |
| Error Handling | Try/catch with fallback to rules-based extraction |
| Token Estimation | ~500-800 input, ~100-200 output per call |
| Cost Estimation | ~$0.005-0.01 per job (at Sonnet 4 pricing) |

**LLM Call Details:**

```python
# Skills Extraction Call (line 129-141)
response = self.client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=500,
    messages=[{
        "role": "user",
        "content": f"""Extract technical skills from this job description.
Return ONLY a JSON array of skill strings, nothing else.
Job Description: {description[:2000]}
Example output: ["Python", "AWS", "Kubernetes", "CI/CD"]"""
    }]
)

# Requirements Extraction Call (line 189-202)
response = self.client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=500,
    messages=[{
        "role": "user",
        "content": f"""Extract key requirements from this job description.
Return ONLY a JSON array of requirement strings...
Example output: ["5+ years experience", "Bachelor's degree", "CISSP certification"]"""
    }]
)
```

### 2B. Embedding Operations — Complete Inventory

| Field | Value |
|-------|-------|
| File Path | `scripts/knowledge/vector_search.py` |
| Embedding Model | `all-MiniLM-L6-v2` (sentence-transformers) |
| Dimensions | 384 |
| What Gets Embedded | Programs, Companies, Contacts, Files (searchable text descriptions) |
| Batch Size | Full collection per index build |
| Where Stored | ChromaDB at `knowledge/_index/vector_db/` |
| Triggered By | Manual via `--build` flag |
| Last Known Vector Count | Unknown (depends on database content) |

**Embedding Collections:**
- `programs` - Federal program searchable descriptions
- `companies` - Company profiles with relationship tier
- `contacts` - Contact information with title/company/clearance
- `files` - File metadata with document type and path

### 2C. RAG Pipelines — Complete Inventory

| Field | Value |
|-------|-------|
| Pipeline Name | Knowledge Base Semantic Search |
| Retrieval Method | Vector search (cosine similarity via ChromaDB) |
| Embedding Model | all-MiniLM-L6-v2 |
| Chunking Strategy | Document-level (entire records, not chunked) |
| Chunk Size | N/A (whole documents) |
| Chunk Overlap | N/A |
| Reranking | ❌ None |
| Top-K | 10 (configurable) |
| Context Window Management | Returns documents + metadata |
| Citation Tracking | Document IDs tracked |
| Confidence Scoring | Distance score converted to similarity |
| Fallback Strategy | Returns error if embedding model unavailable |

**NOTE:** This is a basic semantic search system, not a full RAG pipeline. The LLM calls in standardization.py are independent of the vector search.

### 2D. Knowledge Graph Operations

**Status:** ❌ NOT IMPLEMENTED in this project

The hub_client.py references knowledge graph endpoints on BD Hub:
- `/graph/program/{program_name}`
- `/graph/contact/{contact_name}`
- `/graph/teaming/{from_contractor}/{to_program}`
- `/graph/query`
- `/graph/stats`

But these are API calls to the BD Hub, not local implementations.

### 2E. AI Agents — Complete Inventory

**Status:** ⚠️ REFERENCED BUT NOT IMPLEMENTED

The `hub_client.py` references agent endpoints on BD Hub:
- `/agents/status`
- `/agents/analyze-program`
- `/agents/prepare-outreach`
- `/agents/weekly-intel`

Reference at line 140: "Full program analysis using CrewAI agents"

The agents are implemented in the BD Hub project, not in data-scraper.

### 2F. Memory Systems — Complete Inventory

**Status:** ⚠️ USES EXTERNAL MEMORY (BD Hub)

Hub client memory endpoints:
- `GET /memory/program/{program_name}`
- `GET /memory/contact/{contact_name}`
- `GET /memory/search`
- `POST /memory/add`

Local knowledge base storage:
- SQLite database at `knowledge/_index/knowledge.db`
- Contains: programs, companies, contacts, files tables
- Not a conversational memory system

---

## SECTION 3: DATA ARCHITECTURE — COMPLETE SCHEMA AUDIT

### 3A. Local Databases

| Database | Location | Size |
|----------|----------|------|
| knowledge.db | `knowledge/_index/knowledge.db` | ~27MB |
| metadata.sqlite | `knowledge/_index/metadata.sqlite` | Small |
| chroma.sqlite3 | `knowledge/_index/vector_db/chroma.sqlite3` | ~10MB |
| bullhorn_past_performance.db | `data/output/bullhorn_analysis/` | ~5MB |

**Knowledge Database Schema:**

```sql
-- files table
CREATE TABLE files (
    file_id TEXT PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT,
    file_size INTEGER,
    document_type TEXT DEFAULT 'unknown',
    data_source TEXT DEFAULT 'unknown',
    row_count INTEGER,
    columns TEXT,
    summary TEXT,
    embedding_id TEXT
);

-- programs table
CREATE TABLE programs (
    program_id TEXT PRIMARY KEY,
    program_name TEXT NOT NULL,
    agency TEXT,
    primes TEXT,
    contract_numbers TEXT,
    locations TEXT,
    clearances TEXT,
    status TEXT DEFAULT 'research',
    total_jobs INTEGER DEFAULT 0,
    contract_value REAL DEFAULT 0
);

-- companies table
CREATE TABLE companies (
    company_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    uei TEXT,
    cage_code TEXT,
    relationship_tier TEXT DEFAULT 'unknown',
    bullhorn_mentions INTEGER DEFAULT 0,
    total_contract_value REAL DEFAULT 0
);

-- contacts table
CREATE TABLE contacts (
    contact_id TEXT PRIMARY KEY,
    full_name TEXT,
    title TEXT,
    company TEXT,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    location TEXT,
    clearance TEXT,
    programs TEXT
);
```

### 3B. Vector Store Collections

| Collection Name | Dimensions | Distance Metric | Source |
|-----------------|------------|-----------------|--------|
| programs | 384 | cosine | ChromaDB |
| companies | 384 | cosine | ChromaDB |
| contacts | 384 | cosine | ChromaDB |
| files | 384 | cosine | ChromaDB |

### 3C. CSV/JSON Data Files

**Large CSV Files (>100KB):**
- `data/input/.../db1_dod_prime_contracts_100m.csv`
- `data/input/.../db2_subawards_tango.csv`
- `data/input/.../db3_dod_opportunities_all.csv`
- `data/input/.../master_bd_targets.csv`
- `data/input/FY(All)_All_Contracts_Delta_*.csv` (4.6GB total)

**Large JSON Files:**
- `data/output/hub_jobs_2026-01-26.json` - Scraped job data
- `data/output/standardized_jobs_2026-01-26.json` - Standardized job data
- `TANGO API/response_*.json` - API response data
- `apify/dataset_*.json` - Apify scraper outputs

### 3D. Notion Database Integration Points

**Status:** ⚠️ CONFIGURED BUT LIMITED USE

Notion client at `notion/notion_client.py` supports:
- Sync jobs to Notion database
- Sync contacts to Notion database
- Query jobs from Notion
- Query contacts from Notion

**Database IDs in config:** Not hardcoded - uses environment variable `NOTION_API_KEY` and configurable database IDs.

---

## SECTION 4: PIPELINE & WORKFLOW ARCHITECTURE

### 4A. Data Processing Pipelines

**Main Pipeline: Hub Sync Pipeline** (`hub/sync_pipeline.py`)

```
[TRIGGER: Manual or Scheduled]
    ↓
[STAGE 1: SCRAPE]
    - ApifyManager.run_actor_sync(source)
    - Sources: apex-jobs, insight-global-jobs, teksystems-jobs
    ↓
[STAGE 2: STANDARDIZE]
    - JobStandardizer.standardize_batch(raw_jobs, source)
    - Extracts clearance, normalizes location
    - LLM extraction of skills/requirements
    ↓
[STAGE 3: ENRICH]
    - ProgramMapper.map_jobs(jobs)
    - Maps jobs to federal programs
    ↓
[STAGE 4: DEDUPLICATE]
    - Deduplicator.deduplicate_jobs(jobs)
    - Hash-based deduplication
    ↓
[STAGE 5: VALIDATE]
    - DataQualityChecker.filter_valid_jobs(jobs)
    ↓
[STAGE 6: SYNC]
    - hub.post_jobs(valid_jobs)
    - POST to BD Hub API
    ↓
[STAGE 7: INSIGHTS]
    - CompetitiveIntel.generate_insights()
    - Add to Hub memory
    ↓
[OUTPUT: Pipeline Results Dict]
```

**Pipeline Components:**

| Step | File | Function | Input | Output |
|------|------|----------|-------|--------|
| Scrape | `apify/apify_manager.py` | `run_actor_sync()` | Actor config | Raw job dicts |
| Standardize | `pipelines/standardization.py` | `standardize_batch()` | Raw jobs | JobPosting objects |
| Map | `pipelines/program_mapper.py` | `map_jobs()` | JobPostings | Mapped JobPostings |
| Deduplicate | `pipelines/deduplication.py` | `deduplicate_jobs()` | JobPostings | Unique JobPostings |
| Validate | `pipelines/deduplication.py` | `filter_valid_jobs()` | JobPostings | Valid JobPostings |
| Sync | `hub/hub_client.py` | `post_jobs()` | JobPostings | Sync result |

### 4B. Scheduling & Automation

**Scheduled Tasks:**
- APScheduler configured in `requirements.txt`
- No active scheduler implementation found in main code
- Relies on external scheduling (n8n workflows, cron)

### 4C. API Endpoints — Complete Map

**MCP Server Endpoints** (data-scraper-mcp):

| Tool Name | Method | Purpose |
|-----------|--------|---------|
| run_job_scraper | POST /scrape/run | Run specific scraper |
| run_all_scrapers | POST /scrape/run-all | Run all scrapers |
| run_full_pipeline | POST /pipeline/full | Full ETL pipeline |
| standardize_jobs | POST /pipeline/standardize | Standardize raw jobs |
| map_to_programs | POST /pipeline/map | Map to federal programs |
| sync_to_hub | POST /hub/sync | Sync to BD Hub |
| hub_health_check | GET /hub/health | Check Hub status |
| analyze_competitor | GET /intel/competitor | Competitor analysis |
| compare_competitors | POST /intel/compare | Compare companies |
| get_schedule | GET /schedule/jobs | Get schedule |
| deduplicate | POST /quality/dedupe | Deduplicate records |
| validate_data | POST /quality/validate | Validate data |
| get_scraper_stats | GET /stats/scraper | Scraper statistics |
| get_pipeline_stats | GET /stats/pipeline | Pipeline statistics |

**PDF Processing API** (FastAPI router at `pdf_processing/pdf_api.py`):
- Various PDF operations via Stirling-PDF integration

### 4D. External API Dependencies

| Service | Base URL | Auth | Rate Limit | Purpose |
|---------|----------|------|------------|---------|
| SAM.gov | api.sam.gov | API Key | 1000/day | Opportunities |
| USASpending | api.usaspending.gov | None | Unlimited | Spending data |
| FPDS | fpds.gov/ezsearch/FEEDS | None | 10/min | Contract data |
| Tango | tango.makegov.com | API Key | 60/min | Unified GovCon data |
| Apify | api.apify.com | Token | By plan | Web scraping |
| Firecrawl | (configured) | API Key | By plan | AI scraping |

---

## SECTION 5: MCP SERVER & TOOL AUDIT

### 5A. MCP Servers Defined

**1. data-scraper-mcp**

| Field | Value |
|-------|-------|
| Server Name | data-scraper |
| File Location | `mcp/data-scraper-mcp/src/index.ts` |
| Transport | stdio |
| Tools Count | 14 |
| Dependencies | Requires data-scraper API running on port 8200 |

**2. capture-mcp-server** (External)

| Field | Value |
|-------|-------|
| Server Name | Capture MCP Server |
| File Location | `data/external/capture-mcp-server/` |
| Transport | stdio / HTTP |
| Tools Count | 15 |
| Dependencies | SAM.gov API, Tango API, USASpending |

### 5B. MCP Tools Detail

**data-scraper-mcp Tools:**

| Tool Name | Input | Output | Purpose |
|-----------|-------|--------|---------|
| run_job_scraper | source, locations, max_items | Job results | Run specific scraper |
| run_all_scrapers | locations | All results | Run all scrapers |
| run_full_pipeline | sources, sync_to_hub | Pipeline results | Full ETL |
| standardize_jobs | jobs, source | Standardized jobs | Normalize data |
| map_to_programs | jobs | Mapped jobs | Program mapping |
| sync_to_hub | jobs | Sync results | Hub sync |
| hub_health_check | - | Boolean | Health check |
| analyze_competitor | company | Analysis | Competitor intel |
| compare_competitors | companies | Comparison | Multi-competitor |
| get_schedule | - | Schedule | View schedule |
| run_scheduled_job | job_name | Result | Trigger job |
| deduplicate | records, type | Unique records | Dedup |
| validate_data | records, type | Validation | Quality check |
| get_scraper_stats | - | Stats | Statistics |

**capture-mcp-server Tools:**

| Tool Name | Purpose |
|-----------|---------|
| sam_entity_search | Search SAM.gov entities |
| sam_opportunities_search | Search SAM.gov opportunities |
| sam_opportunity_details | Get opportunity details |
| sam_exclusions_search | Search exclusions |
| usaspending_award_search | Search awards |
| usaspending_spending_by_award | Get spending details |
| usaspending_budget_authority | Budget data |
| usaspending_recipient_search | Search recipients |
| tango_contracts_search | Search Tango contracts |
| tango_grants_search | Search grants |
| tango_vendor_profile | Get vendor profile |
| tango_opportunities_search | Search opportunities |
| tango_spending_summary | Get spending summary |
| join_entity_awards | Join SAM + USASpending |
| join_opportunity_context | Join opportunity data |

---

## SECTION 6: FRONTEND & DASHBOARD AUDIT

### 6A. Frontend Architecture

**Status:** ❌ NO FRONTEND

This project is a backend data processing service. No React/Vue/Angular frontend exists.

The project provides:
- Python scripts
- MCP servers for AI tool access
- API endpoints for integration

Frontend/Dashboard is expected to be in the BD Hub project.

---

## SECTION 7: SECURITY & RESILIENCE AUDIT

### 7A. Secrets Management

**Status:** ⚠️ CRITICAL SECURITY ISSUE

**Exposed Secrets in `.env`:**
```
TANGO_API_KEY=OG4Tv4Uxr-SgN-oQakNobMESjfipGXF39HWtXXpU52I
# ANTHROPIC_API_KEY=sk-ant-api03-... (commented but visible)
# NOTION_API_KEY=ntn_... (commented but visible)
# APIFY_API_TOKEN=apify_api_... (commented but visible)
FIRECRAWL_API_KEY=fc-2c480ade...
```

**Issues:**
- [ ] `.env` contains actual API keys (not placeholders)
- [ ] Commented-out keys are still visible in file
- [ ] `.env` is NOT in `.gitignore` (CRITICAL)
- [ ] No `.env.example` with placeholder values

**Recommendations:**
1. Immediately rotate all exposed API keys
2. Add `.env` to `.gitignore`
3. Create `.env.example` with placeholder values
4. Use secrets manager for production

### 7B. Error Handling Audit

| Metric | Count |
|--------|-------|
| Try/except blocks | 382 |
| Bare except/Exception | 301 (79%) |
| Specific exceptions | 43 (11%) |

**Error Handling Maturity: Level 2 (Generic catch-all)**

Most error handling uses `except Exception` or bare `except:` without specific exception types.

### 7C. Rate Limiting & Retry Logic

**Configured in `config/config.yaml`:**

| API | Rate Limit |
|-----|------------|
| FPDS | 10 req/min |
| USASpending | 120 req/min |
| SAM.gov | 5 req/min |
| Tango | 60 req/min |

**Retry Config:**
- max_retries: 3
- retry_delay: 5 seconds
- Tenacity library in requirements

### 7D. Input Validation

**Pydantic Usage:** ✅ FOUND

| File | Models |
|------|--------|
| `firecrawl_scraper/extraction_schemas.py` | ContactInfoSchema, SAMOpportunitySchema |
| `requirements.txt` | pydantic>=2.5.0 |

**Coverage:** Partial - Pydantic used for extraction schemas but not all API inputs.

---

## SECTION 8: CROSS-PROJECT INTEGRATION MAPPING

### 8A. Shared Data Paths

| Reference | In This Project | Purpose |
|-----------|-----------------|---------|
| BD_HUB_URL | http://localhost:8100 | API endpoint for BD Hub |
| Hub endpoints | 25+ endpoints referenced | Full Hub API integration |

### 8B. Shared Configurations

| Config Key | This Project's Value | Expected Standard | Match? |
|------------|---------------------|-------------------|--------|
| Qdrant URL | ❌ Not used | http://localhost:6333 | N/A |
| Embedding Model | all-MiniLM-L6-v2 | all-MiniLM-L6-v2 | ✅ |
| Embedding Dimensions | 384 | 384 | ✅ |
| LLM Provider | anthropic | anthropic | ✅ |
| LLM Model | claude-sonnet-4-20250514 | claude-sonnet-4-20250514 | ✅ |
| BD Hub URL | http://localhost:8100 | http://localhost:8100 | ✅ |

---

## SECTION 9: DEPENDENCY HEALTH & VERSION ANALYSIS

### 9A. Python Dependencies

**requirements.txt:**

```
# SCRAPING
apify-client>=1.6.0
firecrawl-py>=1.0.0
playwright>=1.40.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
httpx>=0.25.0
aiohttp>=3.9.0

# DATA PROCESSING
pandas>=2.0.0
numpy>=1.24.0
pyyaml>=6.0.0

# LLM / AI
anthropic>=0.18.0

# FUZZY MATCHING
rapidfuzz>=3.5.0
python-Levenshtein>=0.23.0

# NLP / NER
spacy>=3.7.0

# NOTION
notion-client>=2.2.0

# SCHEDULING
apscheduler>=3.10.0

# HASHING
xxhash>=3.4.0

# API / HTTP
requests>=2.31.0
tenacity>=8.2.0

# UTILITIES
python-dotenv>=1.0.0
pydantic>=2.5.0

# TESTING
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

### 9B. Node Dependencies

**mcp/data-scraper-mcp/package.json:**

```json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.3.0"
  }
}
```

---

## SECTION 10: MATURITY SCORING

| Capability | Score | Evidence | Enhancement Needed |
|-----------|-------|----------|-------------------|
| **LLM Integration** | 3 | Anthropic SDK, basic prompts | Structured output, prompt caching |
| **Embedding Pipeline** | 3 | ChromaDB + sentence-transformers | Add Qdrant for production |
| **Vector Search** | 2 | Basic ChromaDB search | Add hybrid search, reranking |
| **RAG Pipeline** | 1 | Not implemented locally | Build full RAG with chunks |
| **Knowledge Graph** | 1 | Relies on BD Hub | No local implementation |
| **AI Agent Orchestration** | 1 | Relies on BD Hub | No local agents |
| **Memory System** | 2 | SQLite + Hub API | Add local memory |
| **Job Scraping** | 4 | Apify, Firecrawl, multiple sources | Good coverage |
| **Job Standardization** | 4 | LLM + rules-based | Production ready |
| **Program Mapping** | 3 | Fuzzy matching implemented | Improve accuracy |
| **Contact Classification** | 2 | Basic implementation | Needs enhancement |
| **BD Score Calculation** | 1 | Not in this project | In BD Hub |
| **Outreach Generation** | 1 | Not in this project | In BD Hub |
| **HUMINT Tracking** | 2 | Bullhorn analysis scripts | Basic processing |
| **Notion Integration** | 3 | Bidirectional sync | Working but basic |
| **n8n Workflow Integration** | 1 | References only | Not integrated |
| **API Layer** | 3 | MCP server + FastAPI | Needs auth |
| **MCP Server/Tools** | 4 | 14 tools defined | Well structured |
| **Frontend/Dashboard** | 0 | None | N/A for this project |
| **Error Handling** | 2 | 79% generic catch | Need specific exceptions |
| **Logging & Observability** | 2 | Basic Python logging | Add structured logging |
| **Testing** | 1 | 327 files mostly external | Add unit tests |
| **Documentation** | 3 | Docstrings, some docs | Need API docs |
| **Security** | 1 | Exposed API keys | Critical fix needed |
| **Data Validation** | 3 | Pydantic schemas | Expand coverage |
| **Performance/Caching** | 2 | File-based cache | Add Redis |
| **Cross-Project Integration** | 3 | Hub client works | Verify endpoints |

**Average Maturity Score: 2.2 / 5**

---

## SECTION 11: CODE QUALITY & TECHNICAL DEBT

### 11A. TODO/FIXME/HACK Inventory

**Count:** 0 in core project files (good)

### 11B. Dead Code Detection

Based on module structure, potential unused files:
- Various `external_apis/` directories in subfolders
- Some scripts in `scripts/` may be one-off analysis

### 11C. Duplicate Logic Detection

Potential duplicate patterns found:
- Clearance pattern matching in multiple files
- Location normalization logic
- Hash generation for deduplication

### 11D. Hardcoded Values

**Clearance patterns:** In `pipelines/standardization.py` (appropriate)
**Location aliases:** In `pipelines/standardization.py` (could be in config)
**Model names:** Hardcoded (`claude-sonnet-4-20250514`, `all-MiniLM-L6-v2`)

---

## SECTION 12: ENHANCEMENT OPPORTUNITY SCORING

### 12A. Quick Wins (< 1 day, high impact)

| Enhancement | Current State | Target State | Files to Change | Impact |
|-------------|--------------|--------------|-----------------|--------|
| Add .env to .gitignore | Exposed secrets | Secured | .gitignore | Critical security |
| Rotate API keys | Exposed | Fresh | External | Critical security |
| Create .env.example | None | Template | New file | Developer experience |
| Add structured output | Raw JSON | Pydantic validated | standardization.py | Reliability |
| Add prompt caching | No caching | Cached system prompts | standardization.py | 60% cost reduction |

### 12B. Standardization Opportunities

| What to Standardize | Current Variations | Proposed Standard | Affected Files |
|---------------------|-------------------|-------------------|---------------|
| Logging | Python logging, loguru | Structured JSON logging | All Python files |
| Error handling | Bare except | Specific exception types | 300+ except blocks |
| Config loading | Hardcoded + .env | Single config module | config/, all scripts |
| Database connections | Multiple connection patterns | Connection pool | scripts/knowledge/ |

### 12C. Missing Capabilities (Gaps)

| Missing Capability | Why It Matters | Complexity | Priority |
|-------------------|---------------|------------|----------|
| Reranking in vector search | 20-40% precision boost | Low | High |
| Hybrid search (BM25+Vector) | Better recall | Medium | High |
| Production vector DB | ChromaDB not production-ready | Medium | High |
| Local RAG pipeline | Currently relies on Hub | High | Medium |
| Automated testing | No test coverage | High | Critical |
| API authentication | MCP server has no auth | Medium | High |
| Observability (metrics) | Can't monitor production | Medium | High |
| Database migrations | Schema changes break things | Medium | Medium |

### 12D. AI/ML Specific Enhancements

| Enhancement | What It Enables | Current Blocker | Implementation Path |
|-------------|----------------|-----------------|---------------------|
| Structured LLM output | Type-safe responses | Using raw JSON | Add Pydantic mode |
| Prompt caching | 60% cost reduction | Not implemented | Use beta API |
| Streaming responses | Better UX | Not needed currently | Low priority |
| Semantic chunking | Better retrieval | No chunking | Add chunk pipeline |
| Cross-encoder reranking | +30% precision | Not implemented | Add rerank step |
| Confidence scoring | Trust calibration | Not implemented | Add to search |

### 12E. Fortification Recommendations

| Area | Current Risk | Mitigation | Priority |
|------|-------------|------------|----------|
| API keys exposure | CRITICAL - Keys in .env visible | Rotate + gitignore | Critical |
| No retry on LLM failures | Jobs fail silently | Add tenacity retry | High |
| No input validation on MCP | Potential injection | Add schema validation | High |
| No rate limiting on local API | DoS risk | Add rate limiter | Medium |
| No health checks | Silent failures | Add /health endpoints | Medium |
| No backup for ChromaDB | Data loss risk | Add backup script | Medium |

---

## SECTION 13: SUMMARY METRICS TABLE

| Metric | Value |
|--------|-------|
| **Project Name** | data-scraper |
| **Total Files** | ~11,000+ (including data) |
| **Total Lines of Code** | 50,456 (Python) |
| **Python Files** | 1,601 |
| **JS/TS Files** | 38 |
| **Config Files** | ~10 |
| **Data Files (CSV/JSON/DB)** | 9,893+ |
| **Total Disk Usage** | 11GB+ |
| **LLM API Call Points** | 2 (skills, requirements extraction) |
| **LLM Models Used** | claude-sonnet-4-20250514 |
| **Embedding Models Used** | all-MiniLM-L6-v2 |
| **Vector Collections** | 4 (programs, companies, contacts, files) |
| **Total Vectors** | Unknown (depends on data) |
| **RAG Pipelines** | 1 (basic semantic search) |
| **AI Agents** | 0 (uses BD Hub agents) |
| **MCP Servers** | 2 (data-scraper-mcp + capture-mcp-server) |
| **MCP Tools** | 29 (14 + 15) |
| **API Endpoints** | 14+ (via MCP) |
| **External APIs** | 6 (SAM, USASpending, FPDS, Tango, Apify, Firecrawl) |
| **Notion DBs Referenced** | 2 (jobs, contacts) |
| **n8n Workflows Referenced** | 0 (references only) |
| **Scheduled Tasks** | 0 (relies on external) |
| **Data Pipelines** | 1 (Hub Sync Pipeline) |
| **Frontend Components** | 0 (N/A) |
| **Test Files** | 327 (mostly external) |
| **TODO/FIXME Count** | 0 |
| **Average Maturity Score** | 2.2 / 5 |
| **Critical Enhancements** | 6 |
| **Quick Wins** | 5 |

---

## CRITICAL ACTIONS REQUIRED

1. **IMMEDIATE:** Rotate all exposed API keys in `.env`
2. **IMMEDIATE:** Add `.env` to `.gitignore`
3. **HIGH:** Add unit tests for core pipelines
4. **HIGH:** Implement proper error handling with specific exceptions
5. **HIGH:** Add authentication to MCP server endpoints
6. **MEDIUM:** Migrate from ChromaDB to Qdrant for production
7. **MEDIUM:** Add reranking to vector search
8. **LOW:** Add structured logging with JSON format

---

*Report generated by Claude Opus 4.5 - 2026-02-01*
