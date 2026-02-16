# API CONSOLIDATION PLAN

> Generated from PROMPT 5 of PTS_NEXTGEN_CONSOLIDATION_BLUEPRINT.md
> Date: 2026-02-16
> Scope: BD-Automation-Engine API surface → Unified server

---

## CURRENT API SURFACE

The BD-Automation-Engine currently exposes **~300+ endpoints** across one main FastAPI app (`Engine8_Knowledge/api.py`) with 35+ mounted routers, plus a standalone lightweight API (`simple_knowledge_api.py`). There is no separate server for N8N-Builder or Data-Scraper in this repo — those are external repos.

### 1. Core App Routes (`Engine8_Knowledge/api.py` — direct `@app.*`)

These are defined directly on the FastAPI app instance (~98 endpoints):

| # | Method | Path | Handler | DB(s) Touched | Auth |
|---|--------|------|---------|---------------|------|
| 1 | GET | `/health` | `health_check()` | Qdrant (ping) | None |
| 2 | GET | `/stats` | `get_stats()` | Qdrant | None |
| 3 | POST | `/contacts/filter` | `filter_contacts()` | Qdrant (contacts) | None |
| 4 | POST | `/programs/filter` | `filter_programs()` | Qdrant (programs) | None |
| 5 | GET | `/dashboard/stats` | `dashboard_stats()` | Qdrant (all) | None |
| 6 | GET | `/ask/smart` | `ask_smart()` | Qdrant + OpenAI | None |
| 7 | GET | `/programs` | `list_programs()` | Qdrant (programs) | None |
| 8 | GET | `/contacts/list` | `list_contacts()` | Qdrant (contacts) | None |
| 9 | POST | `/search` | `search_post()` | Qdrant + OpenAI | None |
| 10 | GET | `/search` | `search_get()` | Qdrant + OpenAI | None |
| 11 | GET | `/search/semantic` | `search_semantic()` | Qdrant + OpenAI | None |
| 12 | GET | `/search/keyword` | `search_keyword()` | Qdrant | None |
| 13 | GET | `/search/hybrid` | `search_hybrid()` | Qdrant + OpenAI | None |
| 14 | POST | `/ask` | `ask_post()` | Qdrant + OpenAI | None |
| 15 | GET | `/ask` | `ask_get()` | Qdrant + OpenAI | None |
| 16 | GET | `/graph/query` | `graph_query()` | Neo4j | None |
| 17 | GET | `/graph/relationships` | `graph_relationships()` | Neo4j | None |
| 18 | GET | `/graph/network` | `graph_network()` | Neo4j | None |
| 19 | GET | `/bdgraph/program/{name}` | `bdgraph_program()` | Neo4j | None |
| 20 | GET | `/bdgraph/contact/{name}` | `bdgraph_contact()` | Neo4j | None |
| 21 | GET | `/bdgraph/teaming/{from}/{to}` | `bdgraph_teaming()` | Neo4j | None |
| 22 | GET | `/bdgraph/query` | `bdgraph_query()` | Neo4j | None |
| 23 | GET | `/bdgraph/search` | `bdgraph_search()` | Neo4j | None |
| 24 | POST | `/bdgraph/entity` | `bdgraph_add_entity()` | Neo4j | None |
| 25 | POST | `/bdgraph/relationship` | `bdgraph_add_rel()` | Neo4j | None |
| 26 | GET | `/bdgraph/stats` | `bdgraph_stats()` | Neo4j | None |
| 27 | POST | `/bdgraph/populate` | `bdgraph_populate()` | Neo4j + Qdrant | None |
| 28 | GET | `/bdgraph/graph` | `bdgraph_graph()` | Neo4j | None |
| 29 | GET | `/bdgraph/introduction-path/{a}/{b}` | `bdgraph_intro_path()` | Neo4j | None |
| 30 | GET | `/bdgraph/types` | `bdgraph_types()` | Neo4j | None |
| 31 | POST | `/memory/add` | `memory_add()` | Qdrant (memories) | None |
| 32 | POST | `/memory/entity` | `memory_entity()` | Qdrant (memories) | None |
| 33 | POST | `/memory/insight` | `memory_insight()` | Qdrant (memories) | None |
| 34 | GET | `/memory/search` | `memory_search()` | Qdrant (memories) | None |
| 35 | GET | `/memory/entity/{name}` | `memory_entity_get()` | Qdrant (memories) | None |
| 36 | GET | `/memory/insights` | `memory_insights()` | Qdrant (memories) | None |
| 37 | GET | `/memory/stats` | `memory_stats()` | Qdrant (memories) | None |
| 38 | GET | `/memory/contact/{name}` | `memory_contact()` | Qdrant (memories) | None |
| 39 | GET | `/memory/program/{name}` | `memory_program()` | Qdrant (memories) | None |
| 40 | GET | `/rag/router` | `rag_router()` | Qdrant + OpenAI | None |
| 41 | GET | `/rag/analyze` | `rag_analyze()` | Qdrant + OpenAI | None |
| 42 | POST | `/ingest/document` | `ingest_document()` | Qdrant + OpenAI | None |
| 43 | POST | `/ingest/program` | `ingest_program()` | Qdrant + OpenAI | None |
| 44 | POST | `/ingest/programs/batch` | `ingest_programs_batch()` | Qdrant + OpenAI | None |
| 45 | POST | `/ingest/company` | `ingest_company()` | Qdrant + OpenAI | None |
| 46 | POST | `/ingest/contact` | `ingest_contact()` | Qdrant + OpenAI | None |
| 47 | POST | `/ingest/contacts/batch` | `ingest_contacts_batch()` | Qdrant + OpenAI | None |
| 48 | POST | `/ingest/jobs` | `ingest_jobs()` | Qdrant + OpenAI | None |
| 49 | POST | `/ingest/scraper-batch` | `ingest_scraper_batch()` | Qdrant + OpenAI | None |
| 50 | POST | `/ingest/scraper-bulk` | `ingest_scraper_bulk()` | Qdrant + OpenAI | None |
| 51 | GET | `/daily-playbook` | `daily_playbook()` | Qdrant + OpenAI | None |
| 52 | GET | `/call-prep/{contact_id}` | `call_prep_by_id()` | Qdrant + OpenAI | None |
| 53 | GET | `/call-prep` | `call_prep()` | Qdrant + OpenAI | None |
| 54 | GET | `/claims/status` | `claims_status()` | Qdrant | None |
| 55 | GET | `/claims/unclaimed-priority` | `unclaimed_priority()` | Qdrant | None |
| 56 | POST | `/outreach/log-activity` | `log_activity()` | Qdrant | None |
| 57 | GET | `/outreach/activity-log` | `activity_log()` | Qdrant | None |
| 58 | GET | `/outreach/stats` | `outreach_stats()` | Qdrant | None |
| 59 | GET | `/claims/velocity` | `claims_velocity()` | Qdrant | None |
| 60 | GET | `/agent/program` | `agent_program()` | Qdrant + OpenAI | None |
| 61 | GET | `/agent/company` | `agent_company()` | Qdrant + OpenAI | None |
| 62 | GET | `/agent/contact` | `agent_contact()` | Qdrant + OpenAI | None |
| 63 | GET | `/agent/strategy` | `agent_strategy()` | Qdrant + OpenAI | None |
| 64 | GET | `/workflow/capture` | `workflow_capture()` | Qdrant + OpenAI | None |
| 65 | GET | `/workflow/competitor` | `workflow_competitor()` | Qdrant + OpenAI | None |
| 66 | GET | `/workflow/quick` | `workflow_quick()` | Qdrant + OpenAI | None |
| 67 | POST | `/pageindex/index` | `pageindex_index()` | SQLite (page_index) | None |
| 68 | GET | `/pageindex/query` | `pageindex_query()` | SQLite (page_index) | None |
| 69 | GET | `/pageindex/stats` | `pageindex_stats()` | SQLite (page_index) | None |
| 70 | GET | `/cache/stats` | `cache_stats()` | In-memory | None |
| 71 | DELETE | `/cache/clear` | `cache_clear()` | In-memory | None |
| 72 | GET | `/program/{name}` | `get_program()` | Qdrant | None |
| 73 | GET | `/company/{name}` | `get_company()` | Qdrant | None |
| 74 | GET | `/contacts/at/{company}` | `contacts_at()` | Qdrant | None |
| 75 | GET | `/jobs/for/{program}` | `jobs_for()` | Qdrant | None |
| 76 | POST | `/index/all` | `index_all()` | Qdrant + OpenAI | None |
| 77 | POST | `/index/{collection}` | `index_collection()` | Qdrant + OpenAI | None |
| 78 | GET | `/agents/status` | `agents_status()` | In-memory | None |
| 79 | POST | `/agents/analyze-program` | `agents_analyze()` | Qdrant + OpenAI | None |
| 80 | POST | `/agents/prepare-outreach` | `agents_outreach()` | Qdrant + OpenAI | None |
| 81 | POST | `/agents/weekly-intel` | `agents_weekly()` | Qdrant + OpenAI | None |
| 82 | GET | `/qa/stats` | `qa_stats()` | SQLite (qa) | None |
| 83 | GET | `/qa/review-queue` | `qa_queue()` | SQLite (qa) | None |
| 84 | POST | `/qa/review-queue/{id}/resolve` | `qa_resolve()` | SQLite (qa) | None |
| 85 | POST | `/graphiti/ingest` | `graphiti_ingest()` | Neo4j (Graphiti) | None |
| 86 | GET | `/graphiti/search` | `graphiti_search()` | Neo4j (Graphiti) | None |
| 87 | GET | `/qa/report` | `qa_report()` | SQLite (qa) | None |
| 88 | POST | `/alerts/check` | `alerts_check()` | Qdrant | None |
| 89 | GET | `/dashboard/summary` | `dashboard_summary()` | Qdrant (all) | None |
| 90 | GET | `/pipeline/status` | `pipeline_status()` | Qdrant | None |
| 91 | PATCH | `/jobs/{id}/stage` | `update_job_stage()` | Qdrant (jobs) | None |
| 92 | POST | `/pipeline/trigger` | `pipeline_trigger()` | Qdrant | None |
| 93 | GET | `/alerts` | `list_alerts()` | Qdrant | None |
| 94 | GET | `/analytics/summary` | `analytics_summary()` | Qdrant (all) | None |
| 95 | GET | `/analytics/funnel` | `analytics_funnel()` | Qdrant | None |
| 96 | GET | `/system/cross-repo-health` | `cross_repo_health()` | HTTP (3 servers) | None |
| 97 | GET | `/predictions/recompetes` | `predictions_recompetes()` | Qdrant + ML | None |
| 98 | GET | `/predictions/best-channels` | `predictions_best_channels()` | Qdrant + ML | None |
| 99 | POST | `/predictions/scoring-recalibrate` | `scoring_recalibrate()` | Qdrant + ML | None |
| 100 | GET | `/agents/tasks/stats` | `agent_tasks_stats()` | In-memory | None |
| 101 | POST | `/agents/tasks/create` | `agent_tasks_create()` | In-memory | None |
| 102 | POST | `/agents/tasks/{id}/event` | `agent_task_event()` | In-memory | None |
| 103 | GET | `/agents/tasks/{id}/stream` | `agent_task_stream()` | In-memory (SSE) | None |
| 104 | POST | `/ai/chat` | `ai_chat()` | Qdrant + OpenAI | None |
| 105 | POST | `/ai/chat/stream` | `ai_chat_stream()` | Qdrant + OpenAI | None |
| 106 | GET | `/graph/data` | `graph_data()` | Neo4j | None |

### 2. Mounted Routers (35+ via `include_router`)

| Prefix | Router File | Endpoints | DB(s) | Auth |
|--------|-------------|-----------|-------|------|
| `/api/v2` | `api/unified_endpoints.py` | 13 | Qdrant + OpenAI | X-API-Key header |
| `/documents` | `Engine8_Knowledge/processors/routes.py` | 5 | Qdrant + OpenAI | None |
| `/retrieval` | `Engine8_Knowledge/retrieval/routes.py` | 6 | SQLite (page_index) + Qdrant | None |
| `/ultrarag` | `Engine8_Knowledge/retrieval/ultra_rag_routes.py` | 7 | Qdrant + OpenAI | None |
| `/lightrag` | `Engine8_Knowledge/bd_lightrag/routes.py` | 10 | Neo4j (LightRAG) | None |
| `/ragflow` | `Engine8_Knowledge/ragflow/routes.py` | 16 | RAGflow + Qdrant | None |
| `/streaming` | `streaming/streaming_api.py` | 5 | Kafka/In-memory | None |
| `/hybrid` | `Engine8_Knowledge/api_routers/hybrid_endpoints.py` | 7 | Qdrant + Notion | None |
| `/phase7` | `Engine8_Knowledge/api_routers/phase7_endpoints.py` | 10 | Qdrant + SQLite | None |
| `/phase8a` | `Engine8_Knowledge/api_routers/phase8a_pipeline.py` | 3 | Qdrant | None |
| `/phase9a` | `Engine8_Knowledge/api_routers/phase9a_competitive.py` | 3 | Qdrant + FPDS | None |
| `/phase10a` | `Engine8_Knowledge/api_routers/phase10a_reports.py` | 1 | Qdrant + OpenAI | None |
| `/ml-core` | `Engine8_Knowledge/ml/routes.py` | 6 | SQLite (ml) + Qdrant | None |
| `/integrations` | `Engine8_Knowledge/integrations/routes.py` | 10 | Slack + Bullhorn + Qdrant | None |
| `/autonomous` | `Engine8_Knowledge/agents/autonomous/routes.py` | 8 | Qdrant + OpenAI | None |
| `/graph/analytics` | `Engine8_Knowledge/graph/analytics_routes.py` | 11 | Neo4j | None |
| `/realtime` | `Engine8_Knowledge/realtime/routes.py` | 4 | WebSocket/In-memory | None |
| `/sse` | `Engine8_Knowledge/realtime/sse_endpoints.py` | 4 | SSE/In-memory | None |
| `/embeddings` | `Engine8_Knowledge/embeddings/routes.py` | 10 | Qdrant + OpenAI | None |
| `/automation` | `Engine8_Knowledge/automation/routes.py` | 10 | Qdrant + Scheduler | None |
| `/platform` | `Engine8_Knowledge/platform/stats_api.py` | 2 | All | None |
| `/graph/neo4j` | `Engine8_Knowledge/graph/neo4j_routes.py` | 10 | Neo4j | None |
| `/search/v2` | `Engine8_Knowledge/search/search_routes.py` | 9 | Qdrant + Neo4j + OpenAI | None |
| `/workflows/v2` | `Engine8_Knowledge/workflows/workflow_routes.py` | 12 | LangGraph + Qdrant | None |
| `/scrape` | `Engine8_Knowledge/api_routers/scrape_api_v2.py` | 10 | SQLite (scrape) + HTTP | None |
| `/memory` | `Engine8_Knowledge/api_routers/memory_api.py` | 10 | Qdrant (memories) | None |
| `/mcp` | `Engine8_Knowledge/api_routers/mcp_api.py` | 5 | Config/In-memory | None |
| `/org-chart` | `Engine8_Knowledge/api_routers/org_chart_api.py` | 10 | Qdrant + Neo4j | None |
| `/ml` | `Engine8_Knowledge/api_routers/ml_api.py` | 10 | Qdrant + ML models | None |
| `/optimizer` | `Engine8_Knowledge/api_routers/optimizer_api.py` | 10 | Qdrant + ML | None |
| `/monitoring` | `Engine8_Knowledge/api_routers/monitoring_api.py` | 7 | All (health probes) | None |
| `/agents` | `Engine8_Knowledge/agents/api_routes.py` | 5 | Qdrant + OpenAI | None |
| `/memories` | `memory/routes.py` | 18 | Qdrant (memories) | None |
| `/dify/knowledge` | `dify_integration/dify_qdrant_bridge.py` | 2 | Qdrant | None |
| `/dify/agents` | `dify_integration/dify_crewai_bridge.py` | 6 | Qdrant + OpenAI | None |
| `/dify/n8n` | `dify_integration/dify_n8n_bridge.py` | 5 | HTTP (n8n) | None |

### 3. Standalone API (`simple_knowledge_api.py`)

Lightweight standalone server (17 endpoints) that duplicates core search/ask functionality. Used when Engine8 full API is too heavy:

| Method | Path | Handler | DB(s) |
|--------|------|---------|-------|
| GET | `/` | `root()` | None |
| GET | `/health` | `health()` | Qdrant |
| GET | `/stats` | `stats()` | Qdrant |
| GET | `/collections` | `list_collections()` | Qdrant |
| GET | `/collections/{collection}` | `collection_info()` | Qdrant |
| POST | `/search` | `semantic_search()` | Qdrant + OpenAI |
| GET | `/search/{collection}` | `search_get()` | Qdrant + OpenAI |
| GET | `/search` | `search_all()` | Qdrant + OpenAI |
| POST | `/search/hybrid` | `search_hybrid()` | Qdrant + OpenAI |
| POST | `/ask/smart` | `ask_smart_post()` | Qdrant + OpenAI |
| GET | `/ask/smart` | `ask_smart_get()` | Qdrant + OpenAI |
| GET | `/ask` | `ask_get()` | Qdrant + OpenAI |
| POST | `/ask` | `ask_question()` | Qdrant + OpenAI |
| GET | `/contacts/search` | `search_contacts()` | Qdrant + OpenAI |
| GET | `/activities/search` | `search_activities()` | Qdrant + OpenAI |
| GET | `/programs/search` | `search_programs()` | Qdrant + OpenAI |
| GET | `/sample/{collection}` | `get_sample()` | Qdrant |

### Summary Totals

| Source | Endpoint Count |
|--------|---------------|
| Core app (`@app.*`) | ~106 |
| Mounted routers (35 routers) | ~254 |
| Standalone API | 17 |
| **TOTAL** | **~377** |

**Auth status:** Only `/api/v2/*` (13 endpoints) use API key auth via `X-API-Key` header. All other 364 endpoints are completely unauthenticated.

**Database breakdown:**
- Qdrant: ~280 endpoints (74%)
- OpenAI embeddings: ~120 endpoints (32%, overlaps with Qdrant)
- Neo4j: ~45 endpoints (12%)
- SQLite: ~20 endpoints (5%)
- External HTTP: ~15 endpoints (4%)
- In-memory/SSE/WebSocket: ~20 endpoints (5%)

---

## ROUTER ORGANIZATION

All routes consolidated under `/api/v1/*` with 12 domain routers. Current paths shown with `→` mapping to new unified paths.

### 1. `/api/v1/contacts/*` — Contact CRUD and Search

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/contacts/filter` | → `/api/v1/contacts/filter` | POST |
| `/contacts/list` | → `/api/v1/contacts` | GET |
| `/contacts/at/{company}` | → `/api/v1/contacts/at/{company}` | GET |
| `/api/v2/contacts` | → `/api/v1/contacts` | GET |
| `/api/v2/contacts/search` | → `/api/v1/contacts/search` | GET |
| `/contacts/search` (simple) | → `/api/v1/contacts/search` | GET |
| `/memory/contact/{name}` | → `/api/v1/contacts/{name}/memory` | GET |
| `/bdgraph/contact/{name}` | → `/api/v1/contacts/{name}/graph` | GET |
| `/graph/neo4j/contact/{name}/360` | → `/api/v1/contacts/{name}/360` | GET |
| `/org-chart/team/{person}` | → `/api/v1/contacts/{person}/team` | GET |
| `/org-chart/chain/{person}` | → `/api/v1/contacts/{person}/chain` | GET |
| `/call-prep/{contact_id}` | → `/api/v1/contacts/{id}/call-prep` | GET |
| `/call-prep` | → `/api/v1/contacts/call-prep` | GET |
| `/ingest/contact` | → `/api/v1/contacts/ingest` | POST |
| `/ingest/contacts/batch` | → `/api/v1/contacts/ingest/batch` | POST |

### 2. `/api/v1/programs/*` — Federal Program Operations

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/programs/filter` | → `/api/v1/programs/filter` | POST |
| `/programs` | → `/api/v1/programs` | GET |
| `/api/v2/programs` | → `/api/v1/programs` | GET |
| `/program/{name}` | → `/api/v1/programs/{name}` | GET |
| `/bdgraph/program/{name}` | → `/api/v1/programs/{name}/graph` | GET |
| `/memory/program/{name}` | → `/api/v1/programs/{name}/memory` | GET |
| `/graph/neo4j/org-chart/{program}` | → `/api/v1/programs/{program}/org-chart` | GET |
| `/graph/neo4j/contacts/{program}` | → `/api/v1/programs/{program}/contacts` | GET |
| `/ultrarag/analyze-program/{name}` | → `/api/v1/programs/{name}/analyze` | GET |
| `/ingest/program` | → `/api/v1/programs/ingest` | POST |
| `/ingest/programs/batch` | → `/api/v1/programs/ingest/batch` | POST |
| `/org-chart/programs` | → `/api/v1/programs/org-data` | GET |

### 3. `/api/v1/jobs/*` — Job Posting Operations

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/api/v2/jobs` | → `/api/v1/jobs` | GET |
| `/jobs/for/{program}` | → `/api/v1/jobs/for/{program}` | GET |
| `/jobs/{id}/stage` | → `/api/v1/jobs/{id}/stage` | PATCH |
| `/ingest/jobs` | → `/api/v1/jobs/ingest` | POST |
| `/ingest/scraper-batch` | → `/api/v1/jobs/ingest/scraper-batch` | POST |
| `/ingest/scraper-bulk` | → `/api/v1/jobs/ingest/scraper-bulk` | POST |

### 4. `/api/v1/contracts/*` — Contract Intelligence

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/phase9a/contracts/awards` | → `/api/v1/contracts/awards` | GET |
| `/phase9a/contracts/expiring` | → `/api/v1/contracts/expiring` | GET |
| `/phase9a/competitive/summary` | → `/api/v1/contracts/competitive-summary` | GET |
| `/predictions/recompetes` | → `/api/v1/contracts/recompete-predictions` | GET |
| `/memories/bd/contract` | → `/api/v1/contracts/store` | POST |
| `/memories/bd/contract/search` | → `/api/v1/contracts/search` | GET |

### 5. `/api/v1/scraping/*` — Scraper Management

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/scrape/crawl` | → `/api/v1/scraping/crawl` | POST |
| `/scrape/crawl-site` | → `/api/v1/scraping/crawl-site` | POST |
| `/scrape/crawl-competitor` | → `/api/v1/scraping/crawl-competitor` | POST |
| `/scrape/cycle` | → `/api/v1/scraping/cycle` | POST |
| `/scrape/sources` | → `/api/v1/scraping/sources` | GET/POST |
| `/scrape/sources/{id}/health` | → `/api/v1/scraping/sources/{id}/health` | GET |
| `/scrape/sources/{id}/trigger` | → `/api/v1/scraping/sources/{id}/trigger` | POST |
| `/scrape/sources/{id}/toggle` | → `/api/v1/scraping/sources/{id}/toggle` | PATCH |
| `/scrape/stats` | → `/api/v1/scraping/stats` | GET |
| `/api/v2/tools/trigger-scrape` | → `/api/v1/scraping/trigger` | POST |

### 6. `/api/v1/enrichment/*` — Data Enrichment Pipeline

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/ingest/document` | → `/api/v1/enrichment/document` | POST |
| `/ingest/company` | → `/api/v1/enrichment/company` | POST |
| `/documents/process` | → `/api/v1/enrichment/document/process` | POST |
| `/documents/upload` | → `/api/v1/enrichment/document/upload` | POST |
| `/documents/ingest` | → `/api/v1/enrichment/document/ingest` | POST |
| `/documents/batch` | → `/api/v1/enrichment/document/batch` | POST |
| `/documents/status` | → `/api/v1/enrichment/status` | GET |
| `/index/all` | → `/api/v1/enrichment/index/all` | POST |
| `/index/{collection}` | → `/api/v1/enrichment/index/{collection}` | POST |
| `/api/v2/tools/trigger-enrichment` | → `/api/v1/enrichment/trigger` | POST |
| `/hybrid/index/bullhorn-notes` | → `/api/v1/enrichment/bullhorn-notes` | POST |
| `/hybrid/collections/create-hybrid` | → `/api/v1/enrichment/create-hybrid-collections` | POST |
| `/hybrid/sync/notion/contacts` | → `/api/v1/enrichment/sync/notion/contacts` | POST |
| `/hybrid/sync/notion/programs` | → `/api/v1/enrichment/sync/notion/programs` | POST |
| `/hybrid/sync/notion/jobs` | → `/api/v1/enrichment/sync/notion/jobs` | POST |
| `/api/v2/sync/notion-to-qdrant` | → `/api/v1/enrichment/sync/notion-to-qdrant` | POST |

### 7. `/api/v1/outreach/*` — Campaign and Outreach

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/outreach/log-activity` | → `/api/v1/outreach/log` | POST |
| `/outreach/activity-log` | → `/api/v1/outreach/log` | GET |
| `/outreach/stats` | → `/api/v1/outreach/stats` | GET |
| `/claims/status` | → `/api/v1/outreach/claims/status` | GET |
| `/claims/unclaimed-priority` | → `/api/v1/outreach/claims/unclaimed` | GET |
| `/claims/velocity` | → `/api/v1/outreach/claims/velocity` | GET |
| `/daily-playbook` | → `/api/v1/outreach/daily-playbook` | GET |
| `/agents/prepare-outreach` | → `/api/v1/outreach/prepare` | POST |
| `/integrations/slack/hot-lead` | → `/api/v1/outreach/hot-lead-alert` | POST |

### 8. `/api/v1/reports/*` — Report Generation

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/phase10a/reports/weekly` | → `/api/v1/reports/weekly` | POST |
| `/agents/weekly-intel` | → `/api/v1/reports/weekly-intel` | POST |
| `/qa/report` | → `/api/v1/reports/qa` | GET |
| `/qa/stats` | → `/api/v1/reports/qa/stats` | GET |
| `/qa/review-queue` | → `/api/v1/reports/qa/review-queue` | GET |
| `/qa/review-queue/{id}/resolve` | → `/api/v1/reports/qa/{id}/resolve` | POST |
| `/analytics/summary` | → `/api/v1/reports/analytics/summary` | GET |
| `/analytics/funnel` | → `/api/v1/reports/analytics/funnel` | GET |
| `/api/v2/analytics/overview` | → `/api/v1/reports/analytics/overview` | GET |
| `/autonomous/briefing/latest` | → `/api/v1/reports/briefing/latest` | GET |
| `/autonomous/briefing/{date}` | → `/api/v1/reports/briefing/{date}` | GET |
| `/autonomous/enrichment/report` | → `/api/v1/reports/enrichment` | GET |

### 9. `/api/v1/workflows/*` — LangGraph Workflow Triggers

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/workflows/v2/start` | → `/api/v1/workflows/start` | POST |
| `/workflows/v2/{id}/resume` | → `/api/v1/workflows/{id}/resume` | POST |
| `/workflows/v2/{id}/cancel` | → `/api/v1/workflows/{id}/cancel` | POST |
| `/workflows/v2/active` | → `/api/v1/workflows/active` | GET |
| `/workflows/v2/history` | → `/api/v1/workflows/history` | GET |
| `/workflows/v2/{id}/status` | → `/api/v1/workflows/{id}/status` | GET |
| `/workflows/v2/{id}/timeline` | → `/api/v1/workflows/{id}/timeline` | GET |
| `/workflows/v2/{id}/state/{step}` | → `/api/v1/workflows/{id}/state/{step}` | GET |
| `/workflows/v2/{id}/diff` | → `/api/v1/workflows/{id}/diff` | GET |
| `/workflows/v2/{id}/replay/{step}` | → `/api/v1/workflows/{id}/replay/{step}` | POST |
| `/workflows/v2/{id}/stream` | → `/api/v1/workflows/{id}/stream` | GET (SSE) |
| `/workflows/v2/registry` | → `/api/v1/workflows/registry` | GET |
| `/automation/workflows/definitions` | → `/api/v1/workflows/definitions` | GET |
| `/automation/workflows/run` | → `/api/v1/workflows/run` | POST |
| `/automation/workflows/active` | → `/api/v1/workflows/automation/active` | GET |
| `/automation/workflows/{id}` | → `/api/v1/workflows/automation/{id}` | GET |
| `/automation/workflows/{id}/approve` | → `/api/v1/workflows/automation/{id}/approve` | POST |
| `/automation/workflows/{id}/cancel` | → `/api/v1/workflows/automation/{id}/cancel` | POST |
| `/workflow/capture` | → `/api/v1/workflows/quick/capture` | GET |
| `/workflow/competitor` | → `/api/v1/workflows/quick/competitor` | GET |
| `/workflow/quick` | → `/api/v1/workflows/quick` | GET |

### 10. `/api/v1/health/*` — Health Checks and System Status

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/health` | → `/api/v1/health` | GET |
| `/api/v2/health` | → `/api/v1/health` | GET |
| `/stats` | → `/api/v1/health/stats` | GET |
| `/monitoring/health` | → `/api/v1/health/monitoring` | GET |
| `/monitoring/ready` | → `/api/v1/health/ready` | GET |
| `/monitoring/live` | → `/api/v1/health/live` | GET |
| `/monitoring/resource-usage` | → `/api/v1/health/resources` | GET |
| `/monitoring/alerts` | → `/api/v1/health/alerts` | GET |
| `/monitoring/status` | → `/api/v1/health/platform-status` | GET |
| `/monitoring/dashboard-urls` | → `/api/v1/health/dashboard-urls` | GET |
| `/system/cross-repo-health` | → `/api/v1/health/cross-repo` | GET |
| `/api/v2/sync/status` | → `/api/v1/health/sync-status` | GET |
| `/api/v2/collections/stats` | → `/api/v1/health/collections` | GET |
| `/mcp/health` | → `/api/v1/health/mcp` | GET |
| `/mcp/stats` | → `/api/v1/health/mcp/stats` | GET |
| `/cache/stats` | → `/api/v1/health/cache` | GET |
| `/cache/clear` | → `/api/v1/health/cache` | DELETE |
| `/platform/stats` | → `/api/v1/health/platform` | GET |
| `/platform/services` | → `/api/v1/health/services` | GET |

### 11. `/api/v1/admin/*` — Admin Operations

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/autonomous/schedule` | → `/api/v1/admin/schedule` | GET |
| `/autonomous/start` | → `/api/v1/admin/scheduler/start` | POST |
| `/autonomous/stop` | → `/api/v1/admin/scheduler/stop` | POST |
| `/autonomous/run/{agent}` | → `/api/v1/admin/agents/run/{agent}` | POST |
| `/autonomous/runs` | → `/api/v1/admin/agents/runs` | GET |
| `/automation/schedule` | → `/api/v1/admin/automation/schedule` | GET |
| `/automation/tasks/{name}/run` | → `/api/v1/admin/automation/tasks/{name}/run` | POST |
| `/automation/tasks/{name}/enable` | → `/api/v1/admin/automation/tasks/{name}/toggle` | POST |
| `/automation/tasks/history` | → `/api/v1/admin/automation/tasks/history` | GET |
| `/optimizer/assess` | → `/api/v1/admin/optimizer/assess` | POST |
| `/optimizer/assessments` | → `/api/v1/admin/optimizer/assessments` | GET |
| `/optimizer/trends/{metric}` | → `/api/v1/admin/optimizer/trends/{metric}` | GET |
| `/optimizer/recommendations` | → `/api/v1/admin/optimizer/recommendations` | GET |
| `/optimizer/apply/{id}` | → `/api/v1/admin/optimizer/apply/{id}` | POST |
| `/optimizer/approve/{id}` | → `/api/v1/admin/optimizer/approve/{id}` | POST |
| `/optimizer/rollback/{id}` | → `/api/v1/admin/optimizer/rollback/{id}` | POST |
| `/optimizer/regressions` | → `/api/v1/admin/optimizer/regressions` | GET |
| `/optimizer/retrain/{model}` | → `/api/v1/admin/optimizer/retrain/{model}` | POST |
| `/optimizer/retrain/status` | → `/api/v1/admin/optimizer/retrain/status` | GET |
| `/mcp/tools` | → `/api/v1/admin/mcp/tools` | GET |
| `/mcp/config` | → `/api/v1/admin/mcp/config` | GET |
| `/mcp/test-tool` | → `/api/v1/admin/mcp/test-tool` | POST |

### 12. `/api/v1/webhooks/*` — Inbound Webhook Handlers

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/phase7/webhooks/jobs-scraped` | → `/api/v1/webhooks/jobs-scraped` | POST |
| `/phase7/webhooks/contracts-updated` | → `/api/v1/webhooks/contracts-updated` | POST |
| `/phase7/webhooks/contacts-enriched` | → `/api/v1/webhooks/contacts-enriched` | POST |
| `/phase7/webhooks/alert` | → `/api/v1/webhooks/alert` | POST |
| `/alerts/check` | → `/api/v1/webhooks/alerts/check` | POST |
| `/alerts` | → `/api/v1/webhooks/alerts` | GET |

### Additional Domain Routers (not in original 12, but needed)

#### `/api/v1/search/*` — Unified Search

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/search` (GET) | → `/api/v1/search` | GET |
| `/search` (POST) | → `/api/v1/search` | POST |
| `/search/semantic` | → `/api/v1/search/semantic` | GET |
| `/search/keyword` | → `/api/v1/search/keyword` | GET |
| `/search/hybrid` | → `/api/v1/search/hybrid` | GET |
| `/api/v2/search` | → `/api/v1/search/unified` | GET |
| `/search/v2` | → `/api/v1/search/advanced` | POST |
| `/search/v2/hybrid` | → `/api/v1/search/advanced/hybrid` | POST |
| `/search/v2/graph` | → `/api/v1/search/advanced/graph` | POST |
| `/search/v2/graphrag` | → `/api/v1/search/advanced/graphrag` | POST |
| `/search/v2/multi` | → `/api/v1/search/advanced/multi` | POST |
| `/search/v2/modes` | → `/api/v1/search/modes` | GET |
| `/search/v2/stats` | → `/api/v1/search/stats` | GET |
| `/search/v2/benchmark` | → `/api/v1/search/benchmark` | POST |
| `/search/v2/benchmark/latest` | → `/api/v1/search/benchmark/latest` | GET |

#### `/api/v1/graph/*` — Knowledge Graph

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/graph/query` | → `/api/v1/graph/query` | GET |
| `/graph/relationships` | → `/api/v1/graph/relationships` | GET |
| `/graph/network` | → `/api/v1/graph/network` | GET |
| `/graph/data` | → `/api/v1/graph/data` | GET |
| `/graph/neo4j/health` | → `/api/v1/graph/neo4j/health` | GET |
| `/graph/neo4j/stats` | → `/api/v1/graph/neo4j/stats` | GET |
| `/graph/neo4j/schema` | → `/api/v1/graph/neo4j/schema` | GET |
| `/graph/neo4j/schema/apply` | → `/api/v1/graph/neo4j/schema/apply` | POST |
| `/graph/neo4j/path/{a}/{b}` | → `/api/v1/graph/path/{a}/{b}` | GET |
| `/graph/neo4j/introduction/{target}` | → `/api/v1/graph/introduction/{target}` | GET |
| `/graph/neo4j/company/{name}` | → `/api/v1/graph/company/{name}` | GET |
| `/graph/analytics/*` | → `/api/v1/graph/analytics/*` | GET/POST |
| `/bdgraph/*` | → `/api/v1/graph/bd/*` | GET/POST |
| `/lightrag/*` | → `/api/v1/graph/lightrag/*` | GET/POST |
| `/graphiti/*` | → `/api/v1/graph/graphiti/*` | GET/POST |

#### `/api/v1/ai/*` — AI Chat and RAG

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/ai/chat` | → `/api/v1/ai/chat` | POST |
| `/ai/chat/stream` | → `/api/v1/ai/chat/stream` | POST |
| `/ask` (GET) | → `/api/v1/ai/ask` | GET |
| `/ask` (POST) | → `/api/v1/ai/ask` | POST |
| `/ask/smart` | → `/api/v1/ai/ask/smart` | GET |
| `/rag/router` | → `/api/v1/ai/rag/route` | GET |
| `/rag/analyze` | → `/api/v1/ai/rag/analyze` | GET |
| `/ultrarag/*` | → `/api/v1/ai/ultrarag/*` | GET/POST |
| `/ragflow/*` | → `/api/v1/ai/ragflow/*` | GET/POST |
| `/agent/*` | → `/api/v1/ai/agent/*` | GET |
| `/agents/*` | → `/api/v1/ai/agents/*` | GET/POST |

#### `/api/v1/ml/*` — Machine Learning

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/ml-core/*` | → `/api/v1/ml/core/*` | GET/POST |
| `/ml/*` | → `/api/v1/ml/*` | GET/POST |
| `/embeddings/*` | → `/api/v1/ml/embeddings/*` | GET/POST |
| `/predictions/*` | → `/api/v1/ml/predictions/*` | GET/POST |

#### `/api/v1/memory/*` — Memory System

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/memory/*` (core app) | → `/api/v1/memory/*` | GET/POST |
| `/memory/*` (router) | → `/api/v1/memory/*` | GET/POST/DELETE |
| `/memories/*` | → `/api/v1/memory/*` | GET/POST/DELETE |
| `/phase7/ai/memories` | → `/api/v1/memory/store` | POST |
| `/phase7/ai/memories/{type}/{name}` | → `/api/v1/memory/entity/{type}/{name}` | GET |

#### `/api/v1/realtime/*` — Real-time Events

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/realtime/ws/dashboard` | → `/api/v1/realtime/ws` | WebSocket |
| `/realtime/status` | → `/api/v1/realtime/status` | GET |
| `/realtime/events` | → `/api/v1/realtime/events` | GET |
| `/realtime/broadcast` | → `/api/v1/realtime/broadcast` | POST |
| `/sse/*` | → `/api/v1/realtime/sse/*` | GET (SSE) |
| `/streaming/*` | → `/api/v1/realtime/streaming/*` | GET/POST |

#### `/api/v1/integrations/*` — External Integrations

| Current Path | → New Unified Path | Method |
|--------------|--------------------|--------|
| `/integrations/slack/*` | → `/api/v1/integrations/slack/*` | GET/POST |
| `/integrations/crm/*` | → `/api/v1/integrations/crm/*` | GET/POST |
| `/dify/*` | → `/api/v1/integrations/dify/*` | GET/POST |
| `/phase7/notifications` | → `/api/v1/integrations/notifications` | GET/POST |
| `/phase7/notifications/{id}/read` | → `/api/v1/integrations/notifications/{id}/read` | PATCH |

---

## BREAKING CHANGES

### Path Changes (High Impact)

These are routes actively used by the dashboard and MCP tools:

| Current Path | New Path | Impact |
|---|---|---|
| `/stats` | `/api/v1/health/stats` | Dashboard `useAppData.ts` |
| `/search` (GET) | `/api/v1/search` | Dashboard search, MCP `search_knowledge` |
| `/ask/smart` | `/api/v1/ai/ask/smart` | Dashboard AI chat, MCP `ask_knowledge` |
| `/contacts/list` | `/api/v1/contacts` | Dashboard contacts page |
| `/programs` | `/api/v1/programs` | Dashboard programs page |
| `/dashboard/stats` | `/api/v1/health/stats` | Dashboard overview |
| `/dashboard/summary` | `/api/v1/reports/analytics/summary` | Dashboard summary |
| `/pipeline/status` | `/api/v1/reports/analytics/summary` | Dashboard pipeline |
| `/api/v2/contacts` | `/api/v1/contacts` | Dashboard v2 hooks |
| `/api/v2/programs` | `/api/v1/programs` | Dashboard v2 hooks |
| `/api/v2/jobs` | `/api/v1/jobs` | Dashboard v2 hooks |

### Response Format Differences

| Endpoint Group | Current Format | Unified Format | Migration |
|---|---|---|---|
| Contacts list | `{"contacts": [...], "total": N}` | `{"data": [...], "total": N, "offset": N}` | Wrapper |
| Programs list | `{"programs": [...], "total": N}` | `{"data": [...], "total": N}` | Wrapper |
| Jobs list | `{"jobs": [...], "total": N}` | `{"data": [...], "total": N}` | Wrapper |
| Search | `{"results": [...], "count": N}` | `{"data": [...], "total": N, "query": "..."}` | Wrapper |
| Ask/Smart | `{"answer": "...", "systems_used": [...]}` | `{"answer": "...", "sources": [...], "model": "..."}` | Breaking |
| Health | `{"status": "ok"}` | `{"status": "ok", "version": "...", "uptime": N}` | Additive |
| Errors | Mixed formats | `{"error": {"code": "...", "message": "...", "details": {}}}` | Wrapper |

### Auth Mechanism Differences

| Current State | Unified State |
|---|---|
| `/api/v2/*` uses `X-API-Key` header | All routes use `Authorization: Bearer <token>` |
| All other routes: no auth | Public routes explicitly marked: `/health`, `/api/v1/health/live`, `/api/v1/health/ready` |
| No rate limiting | Per-key rate limiting on all authenticated routes |

### Deprecation Strategy

**Phase 1 — Dual-serve (4 weeks)**
- Mount both old and new routers simultaneously
- Old routes return `Deprecation: true` and `Sunset: <date>` headers
- Old routes return `Link: </api/v1/...>; rel="successor-version"` header
- Log all requests to deprecated paths for migration tracking

**Phase 2 — Redirect (2 weeks)**
- Old routes return `301 Moved Permanently` to new paths
- Dashboard and MCP tools updated to use new paths

**Phase 3 — Remove (after 6 weeks total)**
- Old route handlers deleted
- Only `/api/v1/*` paths remain

### Dashboard Migration Checklist

Files that need path updates:
- `dashboard/src/lib/hubApi.ts` — Base API client
- `dashboard/src/hooks/useAppData.ts` — TanStack Query hooks
- `dashboard/src/hooks/useHubApi.ts` — Manual fetch hooks
- `dashboard/vite.config.ts` — Proxy configuration
- `mcp/knowledge-mcp-server/` — MCP tool definitions

---

## OPENAPI SPEC DRAFT

Partial OpenAPI 3.1 YAML showing how key routes look in the unified server:

```yaml
openapi: 3.1.0
info:
  title: BD Intelligence Hub API
  version: 1.0.0
  description: |
    Unified API for the PTS BD Intelligence System.
    Consolidates search, contacts, programs, jobs, contracts, AI/RAG,
    graph analytics, ML predictions, and workflow orchestration.
  contact:
    name: PTS Engineering
servers:
  - url: http://localhost:8100
    description: Local development
  - url: https://bd-hub.pts.internal
    description: Production

security:
  - BearerAuth: []

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    PaginatedResponse:
      type: object
      properties:
        data:
          type: array
          items: {}
        total:
          type: integer
        offset:
          type: integer
        limit:
          type: integer

    ErrorResponse:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: object

    Contact:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        title:
          type: string
        company:
          type: string
        email:
          type: string
        phone:
          type: string
        hierarchy_tier:
          type: string
          enum: [C-Suite, VP/Director, Program Manager, Technical Lead, Staff, Unknown]
        bd_priority:
          type: string
          enum: [Critical, High, Medium, Low]
        program:
          type: string
        location_hub:
          type: string

    FederalProgram:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        acronym:
          type: string
        prime_contractor:
          type: string
        agency:
          type: string
        branch:
          type: string
        value_estimate:
          type: string
        pts_involvement:
          type: string
        priority_level:
          type: string

    Job:
      type: object
      properties:
        id:
          type: string
        title:
          type: string
        company:
          type: string
        location:
          type: string
        clearance:
          type: string
        mapped_program:
          type: string
        bd_score:
          type: number
        status:
          type: string
        stage:
          type: string

    SearchResult:
      type: object
      properties:
        id:
          type: string
        collection:
          type: string
        score:
          type: number
        payload:
          type: object

    AskResponse:
      type: object
      properties:
        answer:
          type: string
        sources:
          type: array
          items:
            type: object
            properties:
              collection:
                type: string
              id:
                type: string
              relevance:
                type: number
        model:
          type: string

paths:
  # ─── Health ───────────────────────────────────────────────
  /api/v1/health:
    get:
      tags: [Health]
      summary: Health check
      security: []
      responses:
        '200':
          description: Service healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: ok
                  version:
                    type: string
                  uptime:
                    type: number

  /api/v1/health/stats:
    get:
      tags: [Health]
      summary: Collection statistics
      responses:
        '200':
          description: Stats for all Qdrant collections
          content:
            application/json:
              schema:
                type: object
                additionalProperties:
                  type: object
                  properties:
                    count:
                      type: integer
                    status:
                      type: string

  # ─── Search ──────────────────────────────────────────────
  /api/v1/search:
    get:
      tags: [Search]
      summary: Semantic search across all collections
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
            minLength: 2
        - name: collections
          in: query
          schema:
            type: string
          description: Comma-separated collection names
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
            minimum: 1
            maximum: 100
      responses:
        '200':
          description: Search results
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/SearchResult'
                  total:
                    type: integer
                  query:
                    type: string

  # ─── Contacts ────────────────────────────────────────────
  /api/v1/contacts:
    get:
      tags: [Contacts]
      summary: List contacts with filtering
      parameters:
        - name: program
          in: query
          schema:
            type: string
        - name: tier
          in: query
          schema:
            type: string
        - name: priority
          in: query
          schema:
            type: string
        - name: location
          in: query
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 50
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
      responses:
        '200':
          description: Paginated contacts
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/PaginatedResponse'
                  - properties:
                      data:
                        items:
                          $ref: '#/components/schemas/Contact'

  /api/v1/contacts/search:
    get:
      tags: [Contacts]
      summary: Semantic search for contacts
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: Contact search results

  /api/v1/contacts/{name}/360:
    get:
      tags: [Contacts]
      summary: 360-degree contact view (graph + vector + memory)
      parameters:
        - name: name
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Full contact intelligence

  /api/v1/contacts/{id}/call-prep:
    get:
      tags: [Contacts]
      summary: Generate call preparation brief
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Call prep brief with talking points

  # ─── Programs ────────────────────────────────────────────
  /api/v1/programs:
    get:
      tags: [Programs]
      summary: List federal programs
      parameters:
        - name: prime
          in: query
          schema:
            type: string
        - name: pts_involvement
          in: query
          schema:
            type: string
        - name: priority
          in: query
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 50
      responses:
        '200':
          description: Paginated programs
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/PaginatedResponse'
                  - properties:
                      data:
                        items:
                          $ref: '#/components/schemas/FederalProgram'

  /api/v1/programs/{name}/analyze:
    get:
      tags: [Programs]
      summary: AI-powered program analysis
      parameters:
        - name: name
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Program intelligence report

  # ─── Jobs ────────────────────────────────────────────────
  /api/v1/jobs:
    get:
      tags: [Jobs]
      summary: List job postings
      parameters:
        - name: status
          in: query
          schema:
            type: string
        - name: program
          in: query
          schema:
            type: string
        - name: clearance
          in: query
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 50
      responses:
        '200':
          description: Paginated jobs
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/PaginatedResponse'
                  - properties:
                      data:
                        items:
                          $ref: '#/components/schemas/Job'

  /api/v1/jobs/{id}/stage:
    patch:
      tags: [Jobs]
      summary: Update job pipeline stage
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                stage:
                  type: string
      responses:
        '200':
          description: Stage updated

  # ─── AI / RAG ───────────────────────────────────────────
  /api/v1/ai/ask/smart:
    get:
      tags: [AI]
      summary: RAG-powered Q&A with smart routing
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: AI answer with sources
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AskResponse'

  /api/v1/ai/chat:
    post:
      tags: [AI]
      summary: Multi-turn AI chat
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                history:
                  type: array
                  items:
                    type: object
      responses:
        '200':
          description: Chat response

  /api/v1/ai/chat/stream:
    post:
      tags: [AI]
      summary: Streaming AI chat (SSE)
      responses:
        '200':
          description: Server-sent events stream

  # ─── Contracts ───────────────────────────────────────────
  /api/v1/contracts/awards:
    get:
      tags: [Contracts]
      summary: Recent contract awards
      responses:
        '200':
          description: Contract award data

  /api/v1/contracts/expiring:
    get:
      tags: [Contracts]
      summary: Expiring contracts (recompete opportunities)
      responses:
        '200':
          description: Expiring contract data

  # ─── Outreach ───────────────────────────────────────────
  /api/v1/outreach/daily-playbook:
    get:
      tags: [Outreach]
      summary: Generate daily BD playbook
      responses:
        '200':
          description: Prioritized call list and action items

  /api/v1/outreach/log:
    post:
      tags: [Outreach]
      summary: Log outreach activity
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                contact_id:
                  type: string
                activity_type:
                  type: string
                notes:
                  type: string
      responses:
        '201':
          description: Activity logged

  # ─── Workflows ──────────────────────────────────────────
  /api/v1/workflows/start:
    post:
      tags: [Workflows]
      summary: Start a LangGraph workflow
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                workflow:
                  type: string
                params:
                  type: object
      responses:
        '200':
          description: Workflow started

  /api/v1/workflows/{id}/stream:
    get:
      tags: [Workflows]
      summary: Stream workflow events (SSE)
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Server-sent events stream

  # ─── Webhooks ───────────────────────────────────────────
  /api/v1/webhooks/jobs-scraped:
    post:
      tags: [Webhooks]
      summary: Receive scraped jobs notification
      security: []
      responses:
        '200':
          description: Webhook received

  # ─── Graph ─────────────────────────────────────────────
  /api/v1/graph/path/{from}/{to}:
    get:
      tags: [Graph]
      summary: Shortest path between two people
      parameters:
        - name: from
          in: path
          required: true
          schema:
            type: string
        - name: to
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Path with intermediate connections

  /api/v1/graph/analytics/influence/leaderboard:
    get:
      tags: [Graph]
      summary: Influence leaderboard
      responses:
        '200':
          description: Top influencers by graph centrality

  # ─── Pipeline ──────────────────────────────────────────
  /api/v1/reports/analytics/summary:
    get:
      tags: [Reports]
      summary: Pipeline and analytics summary
      responses:
        '200':
          description: Cross-collection analytics overview
```

---

## DUPLICATE ROUTE ELIMINATION

Routes that currently exist in multiple places and must be merged:

| Functionality | Duplicated In | Canonical |
|---|---|---|
| Health check | `api.py:/health`, `unified:/api/v2/health`, `monitoring:/monitoring/health`, `simple_knowledge_api.py:/health` | `/api/v1/health` |
| Search | `api.py:/search` (GET+POST), `unified:/api/v2/search`, `search_v2:/search/v2`, `simple:/search`, `hybrid:/hybrid/search/hybrid/v2` | `/api/v1/search` + `/api/v1/search/advanced/*` |
| Ask/RAG | `api.py:/ask` (GET+POST), `api.py:/ask/smart`, `simple:/ask`, `simple:/ask/smart` | `/api/v1/ai/ask` + `/api/v1/ai/ask/smart` |
| Contact list | `api.py:/contacts/list`, `unified:/api/v2/contacts`, `simple:/contacts/search` | `/api/v1/contacts` |
| Program list | `api.py:/programs`, `unified:/api/v2/programs`, `simple:/programs/search` | `/api/v1/programs` |
| Collection stats | `api.py:/stats`, `unified:/api/v2/collections/stats`, `simple:/stats`, `simple:/collections`, `hybrid:/hybrid/collections/stats`, `platform:/platform/stats` | `/api/v1/health/stats` |
| Memory add | `api.py:/memory/add`, `memory_router:/memory/add`, `memories_router:/memories/add` | `/api/v1/memory/add` |
| Memory search | `api.py:/memory/search`, `memory_router:/memory/search`, `memories_router:/memories/search` | `/api/v1/memory/search` |
| Weekly intel | `api.py:/agents/weekly-intel`, `crewai:/agents/weekly-intel` | `/api/v1/reports/weekly-intel` |

**Duplicate elimination reduces ~377 endpoints to ~280 unique endpoints.**

---

## IMPLEMENTATION SEQUENCE

1. **Create router files** — One file per domain under `api/routers/`
2. **Write adapter functions** — Thin wrappers that call existing handlers with new response format
3. **Mount dual routers** — Both old and new paths serve simultaneously
4. **Update dashboard** — Point `hubApi.ts` at `/api/v1/*` paths
5. **Update MCP tools** — Point knowledge-mcp-server at new paths
6. **Add auth middleware** — `Authorization: Bearer` on all non-public routes
7. **Add deprecation headers** — Old routes return `Deprecation` + `Sunset` headers
8. **Remove old routes** — After 6-week deprecation period
9. **Delete `simple_knowledge_api.py`** — All functionality absorbed into unified server
10. **Generate full OpenAPI spec** — Auto-generate from FastAPI metadata

---

*Total current endpoints: ~377 | After dedup: ~280 | Organized into 16 domain routers under `/api/v1/*`*
