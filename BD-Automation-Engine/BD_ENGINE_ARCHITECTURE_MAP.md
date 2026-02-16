# BD-Automation-Engine Architecture Map

> Quick-reference navigation guide for AI agents and humans.
> Last updated: 2026-02-16

---

## 1. Forbidden Files (DO NOT READ)

Only secret/credential files are off-limits. Everything else in this repo is fair game.

```
BD-Automation-Engine/
├── .env                               # API keys & secrets (gitignored)
├── *.env                              # All .env variants (gitignored)
├── apps_backend.env
├── auto-claude.env
├── BD-Automation-Engine.env
└── dashboard.env
```

**Everything else is readable** — including data directories, outputs, Qdrant storage, n8n workflows, generated scripts, and all engine data. These are critical to current and future work.

---

## 2. Where Things Live

### Engine 0 — Orchestrator
```
Engine0_Orchestrator/
└── orchestrator.py              # 319 lines — engine-level orchestration

orchestrator.py                  # 976 lines — root-level master orchestrator
```

### Engine 1 — Apify Job Scraper
```
Engine1_Scraper/
├── Configurations/
│   ├── apify_input_primary.json
│   ├── apify_input_variant1.json
│   ├── apify_input_variant2.json
│   └── ScraperEngine_Config.json
└── data/                        # Scraped job data
```
Status: Configured (external Apify actor)

### Engine 2 — Program Mapping (PRODUCTION-CRITICAL)
```
Engine2_ProgramMapping/
├── scripts/
│   ├── pipeline.py              # 1,211 lines — 7-stage pipeline (ENTRY POINT)
│   ├── program_mapper.py        # 1,001 lines — multi-signal matching
│   ├── job_standardizer.py      #   878 lines — LLM field extraction
│   ├── full_pipeline.py         # 6,546 lines — full pipeline runner
│   └── exporters.py             # 21K lines — Notion CSV + n8n export
├── data/
│   ├── Federal Programs *.csv   # 388 federal programs reference
│   ├── BD Opportunities.csv
│   ├── Contractors Database.csv
│   └── Contract_Vehicles.csv
└── Configurations/              # Engine-specific JSON configs
```

### Engine 3 — OrgChart Contact Classification
```
Engine3_OrgChart/
└── scripts/
    ├── contact_classifier.py    #   363 lines — 6-tier hierarchy
    └── contact_lookup.py        # 5,784 lines — contact lookup utils
```

### Engine 4 — Playbook & Briefing Generation
```
Engine4_Playbook/
└── scripts/
    └── bd_playbook_generator.py #   915 lines — playbook generation

Engine4_Briefing/
└── scripts/
    └── briefing_generator.py    #   121 lines — briefing generation
```

### Engine 5 — BD Priority Scoring
```
Engine5_Scoring/
└── scripts/
    └── bd_scoring.py            #   582 lines — 0-100 scoring algorithm
```

### Engine 6 — QA & Alerts (IN PROGRESS)
```
Engine6_QA/
└── scripts/
    ├── qa_feedback.py           # 16K lines — QA feedback system
    └── alerts.py                # 12K lines — alert generation
```
Status: In progress

### Engine 7 — Bullhorn ETL (PRODUCTION-CRITICAL)
```
Engine7_BullhornETL/
├── run_pipeline.py              #   260 lines — main ETL runner (ENTRY POINT)
├── scripts/
│   ├── bullhorn_etl.py          # 33K lines — core ETL logic
│   ├── bullhorn_etl_v2.py       # 45K lines — enhanced ETL
│   ├── intelligent_contact_classifier.py  # 29K lines
│   ├── import_coworker_data.py  # 40K lines
│   ├── ingest_new_notes.py      # 44K lines
│   ├── dashboard_integration.py # 22K lines
│   ├── contact_scoring.py       # 12K lines
│   ├── bd_intelligence_report.py # 11K lines
│   └── ... (15+ more scripts)
├── colton_scurry_analysis/      # Analysis outputs (CSVs + reports)
│   └── ANALYSIS/NOTES_DEEP_DIVE/
└── data/
    └── bullhorn.db              # SQLite database
```

### Engine 8 — AI Knowledge System (PRODUCTION-CRITICAL)
```
Engine8_Knowledge/
├── api.py                       # 3,668 lines — FastAPI server (ENTRY POINT)
├── scripts/
│   ├── vector_store.py          #   845 lines — Qdrant vector operations
│   ├── indexer.py               #   847 lines — data indexing pipeline
│   ├── rag_engine.py            #   418 lines — RAG query engine
│   ├── hybrid_retriever.py      # hybrid search (vector + BM25)
│   ├── query_router.py          # intelligent query routing
│   ├── memory_layer.py          # Mem0 memory integration
│   ├── lightrag_engine.py       # LightRAG knowledge graph
│   ├── index_all_data.py        # batch indexing
│   ├── master_index_all.py      # master indexer
│   └── ... (30+ more scripts)
├── agents/                      # 18 agent files
│   ├── crewai_orchestrator.py   #   448 lines — multi-agent orchestration
│   ├── program_intel_agent.py   # program intelligence
│   ├── company_research_agent.py # company research
│   ├── bd_strategy_agent.py     # BD strategy
│   ├── autonomous/
│   │   ├── morning_briefing.py  # daily briefing
│   │   └── scheduler.py         # autonomous scheduling
│   └── ... (12 more agents)
├── api_routers/                 # 13 router modules
├── retrieval/                   # retrieval engines
├── memory/                      # memory systems (Mem0)
├── graph/                       # knowledge graph (community detection)
├── search/                      # graph-based retrieval
├── ml/                          # ML models (response predictor)
├── realtime/                    # SSE endpoints
├── automation/                  # automation workflows
├── visualization/               # org chart generation
├── scrapers/                    # web scrapers (Crawl4AI, SAM.gov)
└── data/
    └── qdrant/                  # 786 MB — vector database storage
```

---

## 3. Key Files (Read These First)

Priority-ordered list of the most important files to understand the system:

| Priority | File | Lines | Purpose |
|----------|------|-------|---------|
| 1 | `CLAUDE.md` | — | Project rules, structure, commands |
| 2 | `Engine8_Knowledge/api.py` | 3,668 | FastAPI server — 50+ endpoints, all routes |
| 3 | `Engine2_ProgramMapping/scripts/pipeline.py` | 1,211 | 7-stage program mapping pipeline |
| 4 | `orchestrator.py` | 976 | Master pipeline orchestrator |
| 5 | `Engine2_ProgramMapping/scripts/program_mapper.py` | 1,001 | Multi-signal program matching |
| 6 | `Engine4_Playbook/scripts/bd_playbook_generator.py` | 915 | BD playbook generation |
| 7 | `Engine8_Knowledge/scripts/vector_store.py` | 845 | Qdrant vector operations |
| 8 | `Engine5_Scoring/scripts/bd_scoring.py` | 582 | 0-100 BD priority scoring |
| 9 | `Engine3_OrgChart/scripts/contact_classifier.py` | 363 | 6-tier contact hierarchy |
| 10 | `Engine7_BullhornETL/run_pipeline.py` | 260 | ETL entry point |

---

## 4. API & Server Endpoints

### Servers

| Service | Port | Entry Point |
|---------|------|-------------|
| Knowledge API | `:8100` | `Engine8_Knowledge/api.py` |
| Qdrant Vector DB | `:6333` | External service |
| Dashboard (Vite) | `:5173` | `dashboard/` |

### API Response Formats (KNOWN GOTCHA)

```
GET  /api/v2/contacts  → {"contacts": [...], "total": N}
GET  /api/v2/programs  → {"programs": [...], "total": N}
GET  /api/v2/jobs      → {"jobs": [...], "total": N}
POST /search           → {"results": [...], "count": N}
GET  /ask/smart        → {"answer": "...", "query_type": "...", "systems_used": [...]}
```

### Endpoint Summary (50+ routes on :8100)

**Core:**
- `GET /health` `GET /stats`

**Search & RAG:**
- `POST /search` `GET /search/semantic` `GET /search/keyword` `GET /search/hybrid`
- `POST /ask` `GET /ask/smart`

**Entities:**
- `GET /programs` `POST /programs/filter` `GET /program/{name}`
- `GET /contacts/list` `POST /contacts/filter` `GET /contacts/at/{company}`
- `GET /company/{name}` `GET /jobs/for/{program}`

**Knowledge Graph (bdgraph):**
- `GET /bdgraph/program/{name}` `GET /bdgraph/contact/{name}`
- `GET /bdgraph/teaming/{from}/{to}` `GET /bdgraph/search`
- `POST /bdgraph/entity` `POST /bdgraph/relationship`
- `GET /bdgraph/stats` `GET /bdgraph/graph`

**Memory:**
- `POST /memory/add` `POST /memory/entity` `POST /memory/insight`
- `GET /memory/search` `GET /memory/stats`
- `GET /memory/contact/{name}` `GET /memory/program/{name}`

**Ingestion:**
- `POST /ingest/document` `POST /ingest/program` `POST /ingest/contact`
- `POST /ingest/contacts/batch` `POST /ingest/programs/batch`
- `POST /ingest/jobs` `POST /ingest/scraper-batch` `POST /ingest/scraper-bulk`

**BD Operations:**
- `GET /daily-playbook` `GET /call-prep/{contact_id}`
- `GET /claims/status` `GET /claims/unclaimed-priority` `GET /claims/velocity`
- `POST /outreach/log-activity` `GET /outreach/stats`

**Agents:**
- `GET /agent/program` `GET /agent/company` `GET /agent/contact` `GET /agent/strategy`
- `POST /agents/analyze-program` `POST /agents/prepare-outreach` `POST /agents/weekly-intel`

**AI Chat:**
- `POST /ai/chat` `POST /ai/chat/stream`

**Pipeline & Analytics:**
- `GET /pipeline/status` `POST /pipeline/trigger`
- `GET /analytics/summary` `GET /analytics/funnel`

**Predictions:**
- `GET /predictions/recompetes` `GET /predictions/best-channels`

**Dify-compatible:**
- `/dify/knowledge/search` `/dify/knowledge/rag`
- `/dify/agents/invoke` `/dify/n8n/trigger/{workflow}`

---

## 5. Database Locations

### Vector Database (Qdrant @ localhost:6333)

| Collection | Records | Description |
|------------|---------|-------------|
| `contacts` | 7,337 | CRM contacts with tier classification |
| `programs` | 401 | Federal programs and contracts |
| `documents` | 205 | Past performance, briefings |
| `activities` | 500 | Call notes, meeting records |
| `jobs` | 4 | Job postings with BD scores |

Storage: `Engine8_Knowledge/data/qdrant/` (786 MB)

### Relational Database

| File | Size | Description |
|------|------|-------------|
| `Engine7_BullhornETL/data/bullhorn.db` | SQLite | Bullhorn CRM extract |

### CSV Data Sources

| File | Location | Description |
|------|----------|-------------|
| Federal Programs | `Engine2_ProgramMapping/data/Federal Programs *.csv` | 388 programs |
| BD Opportunities | `Engine2_ProgramMapping/data/BD Opportunities.csv` | Opportunities |
| Contractors DB | `Engine2_ProgramMapping/data/Contractors Database.csv` | Contractor data |
| Contract Vehicles | `Engine2_ProgramMapping/data/Contract_Vehicles.csv` | Vehicles |
| Colton/Scurry analysis | `Engine7_BullhornETL/colton_scurry_analysis/` | Analysis CSVs |

---

## 6. Configuration

### Root Config Files

| File | Lines | Purpose |
|------|-------|---------|
| `.env` | — | API keys (NEVER commit, gitignored) |
| `.env.example` | 7,734 | Template with placeholders |
| `.mcp.json` | 54 | MCP server config (6 servers) |
| `requirements.txt` | 184 | Python deps (80+ packages) |
| `Dockerfile` | 1,189 | Container build |
| `docker-compose.yml` | 3,902 | Full stack compose |
| `docker-compose.dev.yml` | 1,190 | Dev compose |
| `.gitignore` | 658 | Git exclusions |

### MCP Servers (from .mcp.json)

`bd-knowledge`, `n8n`, `notion`, `notion-remote`, `apify`, `mapify`

### Engine-Specific Configs

```
Engine1_Scraper/Configurations/     # Apify actor input configs
Engine2_ProgramMapping/Configurations/  # Engine2 mapping configs
config/
├── logging_config.py               # Structured logging (structlog)
├── settings.py                     # Application settings
└── resilience.py                   # Circuit breaker, rate limiting
```

### Required API Keys (.env)

```
ANTHROPIC_API_KEY    # Claude API
OPENAI_API_KEY       # Embeddings
NOTION_TOKEN         # Notion integration
APIFY_API_TOKEN      # Job scraping
N8N_API_KEY          # Workflow orchestration
```

---

## 7. Supporting Infrastructure

### services/ — Integration Services
```
services/
├── database.py                  #   641 lines — DB utilities
├── notion_sync.py               #   584 lines — Notion sync
├── hybrid_search.py             #   386 lines — hybrid search
├── bullhorn_integration.py      # 16K lines — Bullhorn integration
├── notion_qdrant_sync.py        #  9K lines — Notion-Qdrant sync
├── reranker.py                  #  6K lines — result reranking
├── scheduler.py                 # 15K lines — task scheduling
├── graphiti_service.py          #  3K lines — Graphiti knowledge graph
└── ai_enrichment/               # AI enrichment services
```

### dify_integration/ — Visual AI Orchestration
```
dify_integration/
├── dify_apps.py                 #   477 lines — 6 pre-built app templates
├── dify_qdrant_bridge.py        #   401 lines — Qdrant bridge
├── dify_crewai_bridge.py        # 16K lines — CrewAI bridge
├── dify_n8n_bridge.py           # 18K lines — n8n workflow bridge
├── tools_config.py              #   564 lines — 34 external tools
└── README.md                    # 11K lines — complete setup guide
```

### mcp/ — MCP Servers
```
mcp/
├── knowledge-mcp-server/
│   ├── src/index.ts             # TypeScript MCP server
│   └── server.py                # Python MCP server
├── apify/                       # Apify MCP
├── n8n/                         # n8n MCP
├── notion/                      # Notion MCP
├── mapify-mcp-server/           # Mapify MCP
├── auto-claude-builtin/         # Auto-Claude builtin tools
├── claude_desktop_config.json   # Desktop config
└── INSTALLATION_GUIDE.md
```

### n8n/ — Workflow Definitions (19 workflows)
```
n8n/
├── Prime_TS_BD_Intelligence_System_v2.1.json   # 47K lines — master workflow
├── BD_Master_Orchestration_Workflow.json        # 19K lines
├── Error_Logging.json                           # 28K lines
├── Agent_Logger.json                            # 26K lines
├── Clearance_Job_RAG_Agent.json                 # 15K lines
├── PTS_BD_WF1_Apify_Job_Scraper_Intake*.json   # intake workflows
├── PTS_BD_WF2_AI_Enrichment_Processor.json      # enrichment
├── PTS_BD_WF3_Hub_to_BD_Opportunities.json      # opportunity mapping
├── PTS_BD_WF4_Contact_Classification.json       # contact classification
├── PTS_BD_WF5_Hot_Lead_Alerts.json              # hot lead alerts
├── PTS_BD_WF6_Weekly_Summary_Report.json        # weekly summary
└── ... (8 more workflows)
```

### streaming/ — Real-Time Streaming (Pathway.ai)
```
streaming/
├── bd_streaming_pipeline.py     #   772 lines — Pathway streaming pipeline
├── streaming_api.py             # 11K lines — streaming API
└── pathway_config.py            #  4K lines — Pathway configuration
```

### memory/ — Memory Systems
```
memory/
├── supermemory_client.py        #   921 lines — Supermemory integration
└── routes.py                    # 20K lines — memory API routes
```

### models/ — Data Models
```
models/
├── base.py                      # 1,242 lines — base models
├── contacts.py                  # 2,904 lines — contact models
├── programs.py                  # 2,161 lines — program models
├── jobs.py                      # 1,990 lines — job models
└── activities.py                # 1,386 lines — activity models
```

### dashboard/ — React/Vite Dashboard
```
dashboard/
├── src/
│   ├── App.tsx                  # 22K lines — root component
│   ├── main.tsx                 #   719 lines
│   ├── components/              # React components
│   ├── pages/                   # Page components
│   ├── hooks/                   # Custom hooks (useAppData, useHubApi)
│   ├── services/                # API service layer (hubApi.ts)
│   ├── stores/                  # Zustand state
│   └── types/                   # TypeScript types
├── vite.config.ts               # Vite config (proxy to :8100)
├── package.json
└── node_modules/                # 1.1 GB NPM dependencies
```

### Infrastructure
```
k8s/                             # Kubernetes manifests
├── namespace.yaml
├── ingress.yaml
├── dashboard/                   # Dashboard deployment
├── hub-api/                     # Hub API deployment
├── qdrant/                      # Qdrant deployment
├── redis/                       # Redis deployment
└── neo4j/                       # Neo4j deployment

helm/                            # Helm charts
monitoring/                      # Prometheus + Grafana
```

---

## 8. Data Flow Summary

```
                    INGESTION
                    ─────────
  Apify Actor ──► Engine1_Scraper ──► Raw Jobs JSON
                                          │
                    PROCESSING            ▼
                    ──────────
  Raw Jobs ──► Engine2_ProgramMapping ──► Standardized + Mapped
                  (7-stage pipeline)          │
                        │                     ▼
                        ├──► Engine3_OrgChart ──► Classified Contacts
                        │                              │
                        ├──► Engine4_Playbook ──► BD Playbooks
                        │                              │
                        └──► Engine5_Scoring ──► Priority Scores (0-100)
                                                       │
                    QUALITY                            ▼
                    ───────
                  Engine6_QA ──► Validated + Alerts
                                       │
                    CRM                ▼
                    ───
  Bullhorn CRM ──► Engine7_ETL ──► Extracted CRM Data
                                       │
                    INTELLIGENCE        ▼
                    ────────────
                  Engine8_Knowledge ──► Qdrant Vector DB
                  (api.py :8100)           │
                        │                  ├──► Semantic Search
                        │                  ├──► RAG Q&A
                        │                  ├──► Agent Queries
                        │                  └──► Dashboard (:5173)
                        │
                    ORCHESTRATION
                    ─────────────
                  orchestrator.py ──► Full pipeline execution
                  n8n workflows   ──► Visual workflow automation
                  Dify bridges    ──► Visual AI app builder
```

---

## 9. Testing

### Test Location
```
tests/                           # 150+ test files
├── test_orchestrator.py
├── test_knowledge_api.py
├── test_mcp_api.py
├── test_bd_scoring.py
├── test_program_mapper.py
├── test_bullhorn_etl.py
├── test_streaming_api.py
├── test_memory_api.py
└── ... (140+ more)
```

### Running Tests
```bash
# Full suite
pytest tests/ -v

# Specific engine
pytest tests/test_bd_scoring.py -v
pytest tests/test_program_mapper.py -v
pytest tests/test_knowledge_api.py -v
```

Note: Use full Python path on Windows: `/c/Users/gtmar/AppData/Local/Programs/Python/Python312/python.exe -m pytest tests/ -v`

---

## 10. Git Workflow

### CRITICAL: Stay on Feature Branch

```
YOUR FORK (DirtyDiablo/Auto-Claude)
│
├── main ──────────────── DO NOT TOUCH
├── develop ───────────── DO NOT TOUCH
│
└── claude/setup-auto-claude-IrK21  ◄── ALL WORK HERE
```

### Commands
```bash
git checkout claude/setup-auto-claude-IrK21
git push -u origin claude/setup-auto-claude-IrK21
```

### Rules
- **DO:** Commit to `claude/setup-auto-claude-IrK21` only
- **DO:** Use conventional commits (`feat:`, `fix:`, `docs:`, `chore:`)
- **DO NOT:** Push to `develop` or `main`
- **DO NOT:** Create PRs to merge into develop/main

---

## 11. Key Documentation

| File | Description |
|------|-------------|
| `CLAUDE.md` | Project instructions (this is law) |
| `docs/AI_FILESYSTEM_GUIDE.md` | Knowledge system usage guide |
| `docs/RAG_USAGE_GUIDE.md` | RAG patterns and examples |
| `docs/KNOWLEDGE_SYSTEM_GUIDE.md` | Architecture details |
| `docs/OPENCLAW_MASTER_ARCHITECTURE.md` | OpenClaw integration plan (~52K tokens) |
| `docs/PROJECT_STRUCTURE.md` | Project structure reference |
| `docs/FULL_CODESPACE_AUDIT_20260211.md` | Full codebase audit |
| `docs/BD_ENGINE_AUDIT_REPORT.md` | Engine audit report |
| `docs/IMPLEMENTATION_CHECKLIST.md` | Implementation status |
| `docs/MASTER_PROPERTY_SCHEMA.md` | Data property schema |
| `dify_integration/README.md` | Dify setup guide |
| `mcp/INSTALLATION_GUIDE.md` | MCP server installation |
