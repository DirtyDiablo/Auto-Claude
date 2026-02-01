# Project Capability Report
## Project: BD-Automation-Engine
Generated: Thu, Jan 29, 2026  5:25:43 PM

---
## 1. Project Overview

### README Summary
```
# PTS Intelligence Hub
## (Formerly: BD-Automation-Engine)

**Central API Gateway + Vector Search + RAG Engine for PTS Business Development**

---

## What This Project Actually Does

This is the **central intelligence hub** for PTS's BD operations. It provides:

- 🔌 **FastAPI Server** (50+ endpoints on localhost:8100)
- 🔍 **Vector Search** (Qdrant with 8,447 embeddings)
- 🤖 **RAG Queries** (LightRAG + BM25 hybrid search)
- 🧠 **Memory Layer** (Mem0 for context retention)
- ⚙️ **AI Pipeline** (Claude-powered job enrichment)
- 📊 **Output Generation** (BD Playbooks, Call Scripts)
- 🔗 **Integration Hub** (Notion, n8n, MCP)

---

## Current Status

| Component | Status | Details |
|-----------|--------|---------|
| FastAPI Server | ✅ Running | localhost:8100 |
| Qdrant Vectors | ✅ Active | 8,447 indexed |
| AI Enrichment | ✅ Active | Claude + Pydantic |
| Playbook Gen | ✅ Active | 40+ generated |
| Notion Sync | ✅ Active | 8 databases |
| n8n Webhooks | ✅ Active | 13+ payloads |
| Mem0 Memory | ⚠️ Partial | Occasional errors |
| LightRAG | ⚠️ Partial | Not exposed via API |
| spaCy NER | ❌ Unused | Installed but not integrated |

---

## Quick Start

### 1. Start the Hub
```bash
cd Engine8_Knowledge
python api.py
# Server runs on http://localhost:8100
```

### 2. Test Health
```bash
curl http://localhost:8100/health
# {"status": "healthy"}
```

### 3. Search Jobs
```bash
curl "http://localhost:8100/search?q=DCGS+network+engineer&collection=jobs"
```

### 4. RAG Query
```bash
curl "http://localhost:8100/ask/smart?q=Who+are+the+key+contacts+at+Langley"
```

---

## Key API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/search` | GET | Semantic vector search |
| `/ask/smart` | GET | RAG query with hybrid retrieval |
| `/ingest/jobs` | POST | Ingest job data from scrapers |
| `/memory/add` | POST | Add to memory layer |
| `/memory/search` | GET | Search memories |
| `/contacts` | GET | Query contact database |
| `/programs` | GET | Query federal programs |

---

## Vector Collections (Qdrant)

| Collection | Vectors | Contents |
|------------|---------|----------|
| jobs | 262 | Scraped job postings |
| contacts | 7,337 | DCGS + GDIT contacts |
| programs | 401 | Federal programs |
| documents | 205 | Processed documents |
| activities | 500 | BD activities log |

---

## Output Files

| Directory | Contents | Count |
|-----------|----------|-------|
| `outputs/BD_Briefings/` | Playbooks, call scripts, emails | 40+ |
| `outputs/notion/` | Notion export CSVs | 13 |
| `outputs/n8n/` | Webhook payloads | 13 |
| `outputs/` (root) | Processed jobs, reports | 95+ |

```

### Directory Structure
```
.
./AI-Powered File Management and Knowledge Base
./dashboard
./dashboard/public
./dashboard/src
./data
./design_intelligence
./dify_integration
./docs
./docs/bd-dashboard
./docs/Bullhorn Exports
./docs/Claude Exports
./docs/Claude Skills
./docs/N8N-Builder.Capture-MCP-server
./Engine1_Scraper
./Engine1_Scraper/Configurations
./Engine1_Scraper/data
./Engine2_ProgramMapping
./Engine2_ProgramMapping/Configurations
./Engine2_ProgramMapping/data
./Engine2_ProgramMapping/scripts
./Engine3_OrgChart
./Engine3_OrgChart/Configurations
./Engine3_OrgChart/data
./Engine3_OrgChart/scripts
./Engine4_Briefing
./Engine4_Briefing/scripts
./Engine4_Playbook
./Engine4_Playbook/Configurations
./Engine4_Playbook/scripts
./Engine4_Playbook/Templates
./Engine5_Scoring
./Engine5_Scoring/Configurations
./Engine5_Scoring/scripts
./Engine6_QA
./Engine6_QA/data
./Engine6_QA/scripts
./Engine7_BullhornETL
./Engine7_BullhornETL/data
./Engine7_BullhornETL/outputs
./Engine7_BullhornETL/scripts
./Engine8_Knowledge
./Engine8_Knowledge/agents
./Engine8_Knowledge/bd_lightrag
./Engine8_Knowledge/data
./Engine8_Knowledge/evaluation
./Engine8_Knowledge/graph
./Engine8_Knowledge/integrations
./Engine8_Knowledge/pipelines
./Engine8_Knowledge/processors
./Engine8_Knowledge/ragflow
./Engine8_Knowledge/retrieval
./Engine8_Knowledge/schemas
./Engine8_Knowledge/scripts
./Engine8_Knowledge/tests
./external_apis
./logs
./mcp
./mcp/apify
./mcp/auto-claude-builtin
./mcp/knowledge-mcp-server
./mcp/mapify-mcp-server
./mcp/n8n
./mcp/notion
./memory
./n8n
./New Enhancements
./outputs
./outputs/BD_Briefings
./outputs/bd_dashboard
./outputs/enriched_spreadsheet
./outputs/insight_global_full
./outputs/insight_global_run
./outputs/insight_global_run2
./outputs/Logs
./outputs/n8n
./outputs/notion
./outputs/real_data_run
./prompts
./scripts
./scripts/data_correlation
./scripts/job_ingestion
./scripts/notion_schema
./services
./services/ai_enrichment
./streaming
./tests
```

---
## 2. File Inventory by Type

| Type | Count |
|------|-------|
| Python (.py) | 686 |
| JS/TS | 837 |
| JSON | 353 |
| Markdown | 869 |
| CSV | 165 |
| YAML | 87 |

---
## 3. BD Engine Pipeline Scripts

### Engine 2: Program Mapping
| Script | Purpose |
|--------|---------|
| `job_standardizer.py` | LLM-powered field extraction from job postings |
| `program_mapper.py` | Multi-signal matching to federal programs |
| `pipeline.py` | Full 7-stage enrichment pipeline |
| `exporters.py` | Notion CSV + n8n JSON export |

### Engine 3: OrgChart Classification
| Script | Purpose |
|--------|---------|
| `contact_classifier.py` | 6-tier hierarchy classification (Exec→Support) |
| `contact_lookup.py` | Contact discovery by company/program |

### Engine 4: BD Playbook
| Script | Purpose |
|--------|---------|
| `bd_playbook_generator.py` | Generate BD playbooks with talking points |
| `briefing_generator.py` | Create call/meeting briefings |

### Engine 5: BD Scoring
| Script | Purpose |
|--------|---------|
| `bd_scoring.py` | 0-100 priority scoring algorithm |

### Engine 6: QA & Alerts
| Script | Purpose |
|--------|---------|
| `qa_feedback.py` | Quality assurance feedback loop |

### Engine 7: Bullhorn ETL
| Script | Purpose |
|--------|---------|
| `bullhorn_etl.py` | CRM data extraction (293MB database) |
| `contact_scoring.py` | AI-powered contact scoring |
| `intelligent_contact_classifier.py` | ML contact classification |
| `bd_intelligence_report.py` | Generate BD intelligence reports |
| `export_to_notion.py` | Sync to Notion databases |
| `past_performance_report.py` | Past performance analysis |

### Engine 8: AI Knowledge System
| Script | Purpose |
|--------|---------|
| `vector_store.py` | Qdrant vector operations (8,447 vectors) |
| `rag_engine.py` | RAG query engine |
| `hybrid_retriever.py` | BM25 + semantic hybrid search |
| `lightrag_engine.py` | Knowledge graph operations |
| `memory_layer.py` | Mem0 memory system |
| `query_router.py` | Intelligent query routing |
| `redis_cache.py` | Semantic caching layer |
| `indexer.py` | Document indexing pipeline |
| `docling_processor.py` | PDF/document processing |
| `web_scrapers.py` | Firecrawl/Crawl4AI integration |

### Engine 8: AI Agents (CrewAI)
| Agent | Purpose |
|-------|---------|
| `program_intel_agent.py` | Program intelligence research |
| `company_research_agent.py` | Company analysis agent |
| `contact_finder_agent.py` | Contact discovery agent |
| `bd_strategy_agent.py` | BD strategy recommendations |
| `crewai_orchestrator.py` | Multi-agent orchestration |

---
## 4. Database Files

### SQLite Databases
- `./data/page_index.db` (24K)
- `./Engine7_BullhornETL/data/bullhorn_master.db` (293M)
- `./Engine8_Knowledge/data/bd_graph.db` (804K)
- `./Engine8_Knowledge/data/memories.db` (40K)
- `./Engine8_Knowledge/data/memory/chroma.sqlite3` (176K)
- `./Engine8_Knowledge/data/page_index.db` (24K)
- `./Engine8_Knowledge/data/qdrant/collection/activities/storage.sqlite` (4.5M)
- `./Engine8_Knowledge/data/qdrant/collection/contacts/storage.sqlite` (34M)
- `./Engine8_Knowledge/data/qdrant/collection/documents/storage.sqlite` (19M)
- `./Engine8_Knowledge/data/qdrant/collection/jobs/storage.sqlite` (960K)
- `./Engine8_Knowledge/data/qdrant/collection/mem0/storage.sqlite` (12K)
- `./Engine8_Knowledge/data/qdrant/collection/programs/storage.sqlite` (3.1M)
- `./Engine8_Knowledge/data/test.db` (24K)

### Vector Databases
- `./.auto-claude/specs/001-program-mapping-engine-v2-0/memory` (56K)
- `./.auto-claude/worktrees/terminal/datamapping/apps/backend/memory` (52K)
- `./Engine8_Knowledge/data/memory` (972K)
- `./Engine8_Knowledge/data/qdrant` (62M)
- `./memory` (124K)

---
## 5. Data Files

### CSV Files
- `./dashboard/node_modules/force-graph/example/datasets/d3-dependencies.csv` (463 rows)
- `./docs/N8N-Builder.Capture-MCP-server/bd_targets.csv` (261 rows)
- `./docs/N8N-Builder.Capture-MCP-server/contact_search_list.csv` (219 rows)
- `./docs/N8N-Builder.Capture-MCP-server/contract_timeline.csv` (255 rows)
- `./docs/N8N-Builder.Capture-MCP-server/hiring_intelligence.csv` (304 rows)
- `./docs/N8N-Builder.Capture-MCP-server/jobs_mapped_to_programs.csv` (219 rows)
- `./docs/N8N-Builder.Capture-MCP-server/location_intelligence.csv` (249 rows)
- `./docs/N8N-Builder.Capture-MCP-server/naics_summary.csv` (20 rows)
- `./docs/N8N-Builder.Capture-MCP-server/programs_with_contracts.csv` (258 rows)
- `./docs/N8N-Builder.Capture-MCP-server/psc_summary.csv` (38 rows)
- `./docs/N8N-Builder.Capture-MCP-server/subaward_intelligence.csv` (184 rows)
- `./docs/N8N-Builder.Capture-MCP-server/tech_stack_summary.csv` (19 rows)
- `./docs/N8N-Builder.Capture-MCP-server/vendor_uei_lookup.csv` (43 rows)
- `./Engine1_Scraper/data/dataset_puppeteer-scraper_2025-12-17_15-35-33-797.csv` (176 rows)
- `./Engine1_Scraper/data/Jobs_Mapped_to_Programs_2026-01-19.csv` (219 rows)
- `./Engine1_Scraper/data/Jobs_Mapped_to_Programs_MASTER.csv` (219 rows)
- `./Engine2_ProgramMapping/data/BD IntelliRepo File Management.csv` (13 rows)
- `./Engine2_ProgramMapping/data/BD IntelliRepo File ManagementAll.csv` (13 rows)
- `./Engine2_ProgramMapping/data/BD Opportunities.csv` (3 rows)
- `./Engine2_ProgramMapping/data/BD OpportunitiesAll.csv` (3 rows)

---
## 6. Configuration

### Environment Variables (.env.example)
| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Claude API for AI operations |
| `OPENAI_API_KEY` | Embeddings (text-embedding-ada-002) |
| `APIFY_API_TOKEN` | Web scraping (ClearanceJobs, LinkedIn) |
| `MAPIFY_API_KEY` | AI-powered mind map generation |
| `NOTION_TOKEN` | Notion API integration |
| `NOTION_DB_*` | 8 Notion database IDs |
| `N8N_WEBHOOK_URL` | n8n orchestration webhooks |
| `QDRANT_URL` | Vector database (localhost:6333) |
| `DIFY_API_URL` | Visual AI orchestration (localhost:3000) |
| `RAGFLOW_BASE_URL` | Deep document RAG (localhost:80) |

### BD Scoring Configuration
| Setting | Value | Purpose |
|---------|-------|---------|
| `BD_SCORE_TS_SCI_POLY` | +35 | TS/SCI with Poly boost |
| `BD_SCORE_TS_SCI` | +25 | TS/SCI clearance boost |
| `BD_SCORE_DCGS_KEYWORD` | +20 | DCGS relevance boost |
| `BD_TIER_HOT_MIN` | 80 | Hot lead threshold |
| `BD_TIER_WARM_MIN` | 50 | Warm lead threshold |

---
## 7. API Endpoints (Engine8_Knowledge/api.py)

### Core Search & RAG
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/search` | GET/POST | Semantic vector search |
| `/ask/smart` | GET | RAG query with hybrid retrieval |
| `/similar` | POST | Find similar items |
| `/stats` | GET | Collection statistics |

### Data Ingestion
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ingest/jobs` | POST | Ingest scraped jobs |
| `/ingest/contacts` | POST | Ingest contacts |
| `/ingest/documents` | POST | Ingest documents |
| `/index/rebuild` | POST | Rebuild vector index |

### Memory & Knowledge Graph
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/memory/add` | POST | Add to memory layer (Mem0) |
| `/memory/search` | GET | Search memories |
| `/lightrag/*` | * | LightRAG knowledge graph |

### Agent Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/agents/program-intel` | POST | Program intelligence report |
| `/agents/company-research` | POST | Company research agent |
| `/agents/contact-finder` | POST | Contact discovery agent |
| `/agents/bd-strategy` | POST | BD strategy recommendations |

### Dify Integration
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/dify/knowledge/search` | POST | Dify-compatible search |
| `/dify/knowledge/rag` | POST | Dify RAG queries |
| `/dify/agents/invoke` | POST | Invoke BD agents from Dify |
| `/dify/n8n/trigger/*` | POST | Trigger n8n workflows |

---
## 8. Key Dependencies

### Core AI/LLM Stack
```
anthropic>=0.18.0          # Claude API
openai>=1.12.0             # Embeddings
crewai>=0.30.0             # Multi-agent orchestration
```

### Vector & RAG
```
qdrant-client>=1.7.0       # Vector database
sentence-transformers>=2.2.0
llama-index>=0.10.0        # RAG framework
lightrag-hku>=0.1.0        # Knowledge graph
rank-bm25>=0.2.2           # Hybrid retrieval
```

### Data Processing
```
pandas>=2.0.0
numpy>=1.24.0
docling>=0.1.0             # Document processing
```

### API & Infrastructure
```
fastapi>=0.109.0           # API server
uvicorn>=0.27.0
redis>=5.0.0               # Semantic caching
notion-client>=2.2.0       # Notion integration
```

### Evaluation
```
ragas>=0.1.0               # RAG evaluation
datasets>=2.16.0           # Hugging Face datasets
```

---
## 9. External Integrations

| Integration | Port/URL | Purpose |
|-------------|----------|---------|
| **Qdrant** | localhost:6333 | Vector database (8,447 vectors) |
| **Notion** | notion.so API | 8 BD databases |
| **n8n** | Webhooks | Workflow orchestration |
| **Dify** | localhost:3000 | Visual AI builder |
| **RAGflow** | localhost:80 | Deep document RAG |
| **Apify** | Cloud API | Job scraping |
| **Bullhorn** | REST API | CRM integration |
| **Redis** | localhost:6379 | Semantic caching |

---
## Summary Statistics

| Metric | Count |
|--------|-------|
| Python Files | 686 |
| JS/TS Files | 837 |
| JSON Files | 353 |
| CSV Files | 165 |
| Markdown Files | 869 |
| Total Files | 1111 |
