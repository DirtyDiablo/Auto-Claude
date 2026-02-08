# FULL CAPABILITIES & STATE AUDIT — BD-Automation-Engine (Hub)

**Generated:** 2026-02-07T23:50 EST
**Terminal:** A
**Auditor:** Claude Opus 4.6

---

## ═══ SECTION 1: PROJECT METADATA ═══

| Property | Value |
|----------|-------|
| **Git Remote (origin)** | `https://github.com/DirtyDiablo/Auto-Claude.git` |
| **Git Remote (upstream)** | `https://github.com/AndyMik90/Auto-Claude.git` |
| **Current Branch** | `claude/setup-auto-claude-IrK21` |
| **Last Commit** | `6695fe30 fix: Smart Query searches real collections with rich text extraction (10 hours ago)` |
| **Total Files** | 2,076 (excl. .git, node_modules, __pycache__, .auto-claude) |
| **Python Files** | 239 |
| **JS/TS Files** | 101 |
| **Disk Size** | 3.5 GB (excl. node_modules, .git) |
| **.env** | Exists, gitignored |
| **requirements.txt** | Yes |

### package.json Locations (non-node_modules)

| Path | Package Count |
|------|---------------|
| `dashboard/package.json` | 63 |
| `mcp/knowledge-mcp-server/package.json` | 3 |
| `mcp/mapify-mcp-server/package.json` | 9 |

---

## ═══ SECTION 2: QDRANT STATE ═══

| Collection | Vectors | Dimensions | Payload Indexes |
|------------|---------|------------|-----------------|
| jobs | 15,997 | 1536 | title, prime, company, status, location, clearance |
| activities | 445,972 | 1536 | follow_up_required, activity_type, status, related_job_id, action, actor |
| intelligence_reports | 2,229 | 1536 | _(none)_ |
| opportunities | 0 | 1536 | _(none)_ |
| documents | 499,750 | 1536 | intel_category, Fiscal_Year, ContractingOfficeID, MajorCommandID, Contracting_Agency_ID, _source, _source_type |
| programs | 68,103 | 1536 | _source, "Prime Contractor", "Program Name", clearance, "Contract Value", Agency |
| federal_contracts | 107,902 | 1536 | contractor, fiscal_year, _source, agency, sub_agency, naics_code |
| mem0 | 0 | 1536 | run_id, actor_id, user_id, agent_id |
| mem0migrations | 1 | 1536 | actor_id, agent_id, user_id, run_id |
| bd_memories | 2 | 1536 | actor_id, run_id, user_id, agent_id |
| bullhorn_notes | 50,710 | 1536 | note_type, note_author, has_traction, status, action, department |
| contacts | 211,267 | 1536 | Clearances, Primes, Status, intel_category, Programs, Name, priority |

**TOTAL: 1,401,933 vectors across 12 collections**

---

## ═══ SECTION 3: API ENDPOINTS ═══

### Core API (Engine8_Knowledge/api.py) — 81 direct endpoints

```
GET     /health
GET     /stats
GET     /ask/smart
GET     /programs
GET     /contacts/list
POST    /search
GET     /search
GET     /search/semantic
GET     /search/keyword
GET     /search/hybrid
POST    /ask
GET     /ask
GET     /graph/query
GET     /graph/relationships
GET     /graph/network
GET     /bdgraph/program/{program_name}
GET     /bdgraph/contact/{contact_name}
GET     /bdgraph/teaming/{from_contractor}/{to_program}
GET     /bdgraph/query
GET     /bdgraph/search
POST    /bdgraph/entity
POST    /bdgraph/relationship
GET     /bdgraph/stats
POST    /bdgraph/populate
GET     /bdgraph/types
POST    /memory/add
POST    /memory/entity
POST    /memory/insight
GET     /memory/search
GET     /memory/entity/{entity_name}
GET     /memory/insights
GET     /memory/stats
GET     /memory/contact/{contact_name}
GET     /memory/program/{program_name}
GET     /rag/router
GET     /rag/analyze
POST    /ingest/document
POST    /ingest/program
POST    /ingest/programs/batch
POST    /ingest/company
POST    /ingest/contact
POST    /ingest/contacts/batch
POST    /ingest/jobs
POST    /ingest/scraper-batch
GET     /agent/program
GET     /agent/company
GET     /agent/contact
GET     /agent/strategy
GET     /workflow/capture
GET     /workflow/competitor
GET     /workflow/quick
POST    /pageindex/index
GET     /pageindex/query
GET     /pageindex/stats
GET     /cache/stats
DELETE  /cache/clear
GET     /program/{program_name}
GET     /company/{company_name}
GET     /contacts/at/{company_name}
GET     /jobs/for/{program_name}
POST    /index/all
POST    /index/{collection}
GET     /agents/status
POST    /agents/analyze-program
POST    /agents/prepare-outreach
POST    /agents/weekly-intel
GET     /qa/stats
GET     /qa/review-queue
POST    /qa/review-queue/{item_id}/resolve
POST    /ingest/document (duplicate - document processor)
POST    /graphiti/ingest
GET     /graphiti/search
GET     /qa/report
POST    /alerts/check
GET     /dashboard/summary
GET     /pipeline/status
POST    /pipeline/trigger
GET     /alerts
```

### Included Routers (13 routers)

| Router | Prefix | Routes |
|--------|--------|--------|
| document_router | /documents | 4 (process, upload, batch, status) |
| pageindex_router | /pageindex | 3 (search, citation, index-document, delete, stats, answer) |
| ultrarag_router | /ultrarag | 7 (query, analyze-program, research-contact, compare-programs, verify, pipelines, status) |
| lightrag_router | /lightrag | 12 (test-write, insert, query GET/POST, entity, relationships, program contractors, teaming-path, extract-entities, known-entities, stats, status) |
| streaming_router | /streaming | _(streaming endpoints)_ |
| dify knowledge | /dify | knowledge/search, knowledge/rag |
| dify agents | /dify | agents endpoints |
| dify n8n | /dify | n8n trigger endpoints |
| ragflow_router | /ragflow | 14 (health, status, kb/initialize, kb/list, upload, ingest, query, program, contact context/prep, sync/notion, graph/build, graph/status, search/hybrid, dify knowledge) |
| unified_router | /api/v2 | _(unified v2 endpoints)_ |
| hybrid_router | /api/v2 | 6 (search/hybrid/v2, collections/stats, sync/notion/contacts/programs/jobs, index/bullhorn-notes, collections/create-hybrid) |
| crewai_router | /crewai | 5 (research, outreach, weekly-intel, status, tasks) |

**Estimated Total: ~140+ API endpoints**

---

## ═══ SECTION 4: CREWAI AGENTS ═══

### Agent Definitions (BDAgent subclasses)

| # | Agent Class | File |
|---|------------|------|
| 1 | `ProgramIntelAgent` | agents/program_intel_agent.py |
| 2 | `CompanyResearchAgent` | agents/company_research_agent.py |
| 3 | `ContactFinderAgent` | agents/contact_finder_agent.py |
| 4 | `BDStrategyAgent` | agents/bd_strategy_agent.py |
| 5 | `ContactClassifierAgent` | agents/contact_classifier_agent.py |
| 6 | `ScraperMonitorAgent` | agents/scraper_monitor_agent.py |
| 7 | `QualityAssuranceAgent` | agents/quality_assurance_agent.py |
| 8 | `AnalyticsAgent` | agents/analytics_agent.py |

### CrewAI Raw Agents (bd_agents.py)

| # | Agent | Role |
|---|-------|------|
| 1 | `program_researcher` | Program research |
| 2 | `contact_enricher` | Contact enrichment |
| 3 | `competitive_analyst` | Competitive analysis |
| 4 | `outreach_composer` | Outreach composition |
| 5 | `humint_analyst` | HUMINT analysis |

**Total: 13 agents (8 BDAgent + 5 CrewAI raw)**

### Crew Definitions — 6 Crews

| Location | Count |
|----------|-------|
| agents/crews.py | 3 crews |
| agents/workflows.py | 3 crews |

### Pydantic Output Models — 40 models

Key models: `ProgramIntelligence`, `ContactProfile`, `CompetitiveReport`, `OutreachPlan`, `HUMINTBrief`, `BDResearchBundle`, `WeeklyIntelBundle`, `SearchRequest`, `AskRequest`, `SearchResponse`, `AskResponse`, `StatsResponse`, `IndexResponse`, `MemoryInput`, `InsightInput`, `DocumentInput`, `ProgramInput`, `CompanyInput`, `ContactInput`, `JobInput`, `ProgramAnalysisRequest`, `OutreachPrepRequest`, `AgentStatusResponse`, `HybridSearchRequest`, `HybridSearchResponse`, `CollectionStatsResponse`, `SyncResponse`, `IndexBullhornResponse`, `CreateCollectionsResponse`, `ResearchRequest`, `OutreachRequest`, `WeeklyIntelRequest`, `TaskResponse`, `TaskStatus`, and more.

---

## ═══ SECTION 5: INSTALLED PYTHON PACKAGES ═══

| Package | Version |
|---------|---------|
| anthropic | 0.78.0 |
| crewai | 1.9.3 |
| crewai-tools | 1.9.3 |
| docling | 2.72.0 |
| docling-core | 2.63.0 |
| docling-ibm-models | 3.11.0 |
| docling-parse | 4.7.3 |
| fastapi | 0.128.0 |
| graphiti-core | 0.26.3 |
| httpx | 0.28.1 |
| httpx-sse | 0.4.3 |
| langchain-anthropic | 1.3.2 |
| langchain-classic | 1.0.1 |
| langchain-core | 1.2.9 |
| langchain-neo4j | 0.8.0 |
| langchain-text-splitters | 1.1.0 |
| langgraph | 1.0.7 |
| langgraph-checkpoint | 4.0.0 |
| langgraph-checkpoint-sqlite | 3.0.3 |
| langgraph-prebuilt | 1.0.7 |
| langgraph-sdk | 0.3.3 |
| mem0ai | 0.1.116 |
| neo4j | 6.1.0 |
| neo4j-graphrag | 1.13.0 |
| openai | 2.17.0 |
| pydantic | 2.12.5 |
| pydantic_core | 2.41.5 |
| pydantic-settings | 2.10.1 |
| qdrant-client | 1.16.2 |
| sentence-transformers | 5.2.2 |
| structlog | 25.5.0 |
| tenacity | 9.1.2 |
| uvicorn | 0.40.0 |

**Total key packages: 33**

---

## ═══ SECTION 6: FRONTEND STATE ═══

### dashboard/package.json — 63 packages

**Dependencies:**
- `@ai-sdk/openai: ^3.0.26`
- `@antv/g6: ^5.0.51`
- `@assistant-ui/react: ^0.12.9`
- `@cosmograph/react: ^2.1.0`
- `@dnd-kit/core: ^6.3.1`
- `@dnd-kit/sortable: ^10.0.0`
- `@dnd-kit/utilities: ^3.2.2`
- `@hookform/resolvers: ^5.2.2`
- `@radix-ui/react-context-menu: ^2.2.16`
- `@radix-ui/react-dialog: ^1.1.15`
- `@radix-ui/react-scroll-area: ^1.2.10`
- `@radix-ui/react-separator: ^1.1.8`
- `@radix-ui/react-slot: ^1.2.4`
- `@radix-ui/react-tabs: ^1.1.13`
- `@tailwindcss/forms: ^0.5.11`
- `@tailwindcss/postcss: ^4.1.18`
- `@tailwindcss/vite: ^4.1.18`
- `@tanstack/react-query: ^5.90.20`
- `@tanstack/react-query-devtools: ^5.91.3`
- `@tanstack/react-router: ^1.158.4`
- `@tanstack/react-table: ^8.21.3`
- `@tremor/react: ^3.18.7`
- `ai: ^6.0.77`
- `assistant-ui: ^0.0.78`
- `class-variance-authority: ^0.7.1`
- `clsx: ^2.1.1`
- `cmdk: ^1.1.1`
- `d3-force: ^3.0.0`
- `date-fns: ^4.1.0`
- `framer-motion: ^12.33.0`
- `graphin: ^0.0.14`
- `html-to-image: ^1.11.13`
- `jszip: ^3.10.1`
- `lucide-react: ^0.562.0`
- `react: ^19.2.0`
- `react-chrono: ^3.3.3`
- `react-dom: ^19.2.0`
- `react-force-graph-2d: ^1.29.0`
- `react-hook-form: ^7.71.1`
- `reagraph: ^4.30.8`
- `recharts: ^3.6.0`
- `sonner: ^2.0.7`
- `tailwind-merge: ^3.4.0`
- `tailwindcss: ^4.1.18`
- `tailwindcss-animate: ^1.0.7`
- `vis-timeline: ^8.5.0`
- `zod: ^4.3.6`
- `zustand: ^5.0.10`

**DevDependencies:**
- `@eslint/js: ^9.39.1`
- `@types/d3-force: ^3.0.10`
- `@types/node: ^24.10.1`
- `@types/react: ^19.2.5`
- `@types/react-dom: ^19.2.3`
- `@vitejs/plugin-react: ^5.1.1`
- `autoprefixer: ^10.4.23`
- `eslint: ^9.39.1`
- `eslint-plugin-react-hooks: ^7.0.1`
- `eslint-plugin-react-refresh: ^0.4.24`
- `globals: ^16.5.0`
- `postcss: ^8.5.6`
- `typescript: ~5.9.3`
- `typescript-eslint: ^8.46.4`
- `vite: ^7.2.4`

### mcp/knowledge-mcp-server/package.json — 3 packages

- `@modelcontextprotocol/sdk: ^0.5.0`
- `@types/node: ^20.10.0`
- `typescript: ^5.3.0`

### mcp/mapify-mcp-server/package.json — 9 packages

- `@modelcontextprotocol/sdk: ^1.11.2`
- `@types/node: ^22.15.17`
- `body-parser: ^1.20.2`
- `dotenv: ^16.0.3`
- `esbuild: ^0.25.5`
- `express: ^4.18.2`
- `node-fetch: ^3.3.2`
- `typescript: ^5.8.3`
- `zod: ^3.24.4`

---

## ═══ SECTION 7: NEO4J STATE ═══

| Metric | Value |
|--------|-------|
| **Status** | Healthy (bolt://localhost:7687) |
| **Nodes** | 12 |
| **Relationships** | 9 |
| **Labels** | person, organization, location, __User__, Saga, Episodic, Entity, Community, concept, program |
| **Relationship Types** | acting_site_lead_for, located_in, has_role, has_no_backup_support, RELATES_TO, HAS_MEMBER, NEXT_EPISODE, HAS_EPISODE, MENTIONS, is_for, is_a, is_part_of, includes, is_used_by |

> Note: Neo4j is lightly populated (12 nodes, 9 relationships). The Graphiti memory system has seeded initial entities. Bulk population from Qdrant data has not been run yet.

---

## ═══ SECTION 8: MEM0 STATE ═══

| Collection | Count | Details |
|------------|-------|---------|
| **bd_memories** | 2 | HUMINT memories about AF DCGS PACAF |
| **mem0** | 0 | Empty (initialized, not used) |
| **mem0migrations** | 1 | Migration tracking entry |

**Sample Memories (bd_memories):**
1. `"Kingsley Ero is wearing multiple hats with no backup support"` (category: humint, program: AF DCGS PACAF)
2. `"Kingsley Ero is the acting site lead for AF DCGS PACAF in San Diego"` (category: humint, program: AF DCGS PACAF)

---

## ═══ SECTION 9: DIRECTORY STRUCTURE (2 levels) ═══

```
.
├── .auto-claude/
│   ├── .auto-claude/
│   ├── file-timelines/
│   ├── github/
│   ├── ideation/
│   ├── insights/
│   ├── roadmap/
│   ├── specs/
│   ├── terminal/
│   └── worktrees/
├── .claude/
├── AI-Powered File Management and Knowledge Base/
├── Engine1_Scraper/
│   ├── Configurations/
│   └── data/
├── Engine2_ProgramMapping/
│   ├── Configurations/
│   ├── data/
│   └── scripts/
├── Engine3_OrgChart/
│   ├── Configurations/
│   ├── data/
│   └── scripts/
├── Engine4_Briefing/
│   └── scripts/
├── Engine4_Playbook/
│   ├── Configurations/
│   ├── Templates/
│   └── scripts/
├── Engine5_Scoring/
│   ├── Configurations/
│   └── scripts/
├── Engine6_QA/
│   ├── data/
│   └── scripts/
├── Engine7_BullhornETL/
│   ├── colton_scurry_analysis/
│   ├── data/
│   └── scripts/
├── Engine8_Knowledge/
│   ├── agents/
│   ├── api_routers/
│   ├── bd_lightrag/
│   ├── data/
│   ├── evaluation/
│   ├── graph/
│   ├── pipelines/
│   ├── processors/
│   ├── ragflow/
│   ├── retrieval/
│   ├── schemas/
│   ├── scripts/
│   └── tests/
├── New Enhancements/
├── api/
├── apps/
│   └── backend/
├── config/
├── dashboard/
│   ├── dist/
│   ├── public/
│   └── src/
├── data/
│   ├── from_data_scraper/
│   ├── from_n8n_builder/
│   └── qdrant/
├── design_intelligence/
├── dify_integration/
├── docs/
│   ├── Bullhorn Exports/
│   ├── Claude Exports/
│   ├── Claude Skills/
│   ├── N8N-Builder.Capture-MCP-server/
│   ├── bd-dashboard/
│   └── project-knowledge/
├── engine_data/
│   ├── Engine1_Scraper/
│   ├── Engine2_ProgramMapping/
│   ├── Engine3_OrgChart/
│   ├── Engine7_BullhornETL/
│   ├── Engine8_Knowledge/
│   └── dashboard_public/
├── mcp/
│   ├── apify/
│   ├── auto-claude-builtin/
│   ├── knowledge-mcp-server/
│   ├── mapify-mcp-server/
│   ├── n8n/
│   └── notion/
├── memory/
├── models/
├── n8n/
├── outputs/
│   ├── BD_Briefings/
│   ├── Logs/
│   ├── bd_dashboard/
│   ├── coworker_takeover/
│   ├── enriched_spreadsheet/
│   ├── insight_global_full/
│   ├── insight_global_run/
│   ├── insight_global_run2/
│   ├── n8n/
│   ├── notion/
│   └── real_data_run/
├── prompts/
├── qdrant/
│   └── collection/
├── scripts/
│   ├── data_correlation/
│   ├── job_ingestion/
│   └── notion_schema/
├── services/
│   └── ai_enrichment/
├── streaming/
├── tests/
└── utils/
```

---

## ═══ SECTION 10: DOCKER / SERVICES ═══

**Docker:** Not available (command not found in Git Bash)

Services are running natively on Windows (not containerized):
- Qdrant: Native Windows binary
- Neo4j: Native Windows install
- Hub API: Python uvicorn
- Dashboard: Vite dev server

---

## ═══ SECTION 11: PORT CHECK ═══

| Port | Service | Status |
|------|---------|--------|
| 8100 | Hub API (FastAPI/uvicorn) | **UP** (HTTP 200) |
| 6333 | Qdrant Vector DB | **UP** (HTTP 200) |
| 7474 | Neo4j Browser (HTTP) | **UP** (HTTP 200) |
| 7687 | Neo4j Bolt (inferred) | **UP** (auth successful) |
| 5173 | Dashboard (Vite dev) | **UP** (HTTP 200) |

---

## ═══ PHASE COMPLETION SUMMARY ═══

```
Terminal: A
Phase: Capabilities Audit
Status: COMPLETE
```

**COPY-PASTE FOR ORCHESTRATOR:**

BD-Automation-Engine Hub audit complete. Qdrant: 1,401,933 vectors across 12 collections (contacts 211K, documents 500K, activities 446K, federal_contracts 108K, programs 68K, bullhorn_notes 51K, jobs 16K, intelligence_reports 2.2K). API: ~140+ endpoints on FastAPI :8100 covering search, RAG, graph, memory, ingest, agents, QA, pipeline, alerts, dashboard, and Dify integration. CrewAI: 13 agents (8 BDAgent subclasses + 5 raw CrewAI agents) organized into 6 crews. Neo4j: 12 nodes, 9 relationships, 10 labels, 14 relationship types (lightly seeded via Graphiti). Mem0: 2 HUMINT memories in bd_memories, mem0 collection initialized but empty. Frontend: 63 npm packages in dashboard (React 19, TanStack Query/Router/Table, Tremor, Recharts, Framer Motion, assistant-ui, dnd-kit, react-hook-form, zod). Branch: `claude/setup-auto-claude-IrK21`, last commit `6695fe30 fix: Smart Query searches real collections with rich text extraction`.

```
═══ END SUMMARY ═══
```
