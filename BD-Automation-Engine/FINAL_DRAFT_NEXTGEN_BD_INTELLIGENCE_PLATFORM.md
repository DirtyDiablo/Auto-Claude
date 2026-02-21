# FINAL DRAFT: Next-Gen BD Intelligence Platform

**Document**: Authoritative Next-Gen Rebuild Architecture
**Created**: 2026-02-15
**Sources**: BD-Automation-Engine Codebase Audit (10-section deep dive) + 2026 Architecture Blueprint Research (Compass Artifact)
**Purpose**: Single definitive document for final architecture decisions — merges current-state facts with 2026 target tech stack

---

## 1. Executive Summary

The BD-Automation-Engine is an 8-engine pipeline for federal defense contract staffing BD automation, targeting thousands of cleared defense contracts ($100M+, subcontracting staffing firms, clearance-required). The current system spans **~60,000-70,000 unique lines of Python**, **2.5+ GB of data**, **9 SQLite databases**, **10+ Qdrant vector collections**, **858 API route definitions**, and **48 distinct entity types**.

The next-gen rebuild consolidates this into a **2-repo monorepo** built on:
- **uv v0.10.2 workspaces** (Python monorepo)
- **Supabase Pro PostgreSQL + pgvector 0.8.0** (replaces 9 SQLite + Qdrant)
- **LangGraph 1.0.8** (replaces CrewAI)
- **Voyage 4 embeddings** (replaces text-embedding-3-small)
- **Neo4j AuraDB Professional** (replaces Docker Neo4j)
- **Next.js 16.1 + shadcn/ui + Tremor** (replaces React 19 + Vite dashboard)
- **Claude Opus 4.6 / Sonnet 4.5 / Haiku 4.5** (model tiering)

**Target monthly cost**: $500–$1,200/month
**Critical deadline**: FPDS decommissions February 24, 2026 — SAM.gov migration is urgent

### Key Consolidation Numbers

| Metric | Current | Target |
|--------|---------|--------|
| Databases | 9 SQLite + Qdrant + Neo4j Docker | 1 Supabase PostgreSQL + Neo4j AuraDB |
| API endpoints | 858 route definitions | ~100–150 endpoints |
| Entity types | 48 | 12–14 |
| Embedding model | text-embedding-3-small (1536d) | Voyage 4 asymmetric (1024d) |
| Vector storage | Qdrant (8,447+ vectors, 811 MB) | pgvector halfvec (~200 MB) |
| Agent framework | CrewAI 0.30 + 13 agents | LangGraph 1.0.8 supervisor pattern |
| Python tooling | pip + venv | uv v0.10.2 workspaces |
| Dashboard | React 19 + Vite (141 TSX files) | Next.js 16.1 + App Router |
| Auth | None | Supabase Auth + RLS + RBAC |
| Hosting | Docker Compose local | Railway + managed services |

---

## 2. Current State (From 10-Section Codebase Audit)

### 2.1 Repository Stats

| Metric | Value |
|--------|-------|
| Total Python files | ~200+ |
| Estimated unique LoC | ~60,000–70,000 |
| Total data size | **2.5+ GB** (data/ 1.4G, Engine8 811M, Engine7 293M, Engine3 32M) |
| SQLite databases | 9 databases, largest 292 MB |
| Qdrant collections | 10+ collections, 8,447+ vectors |
| Dashboard source files | 141 TypeScript/TSX files, 34 pages |
| API endpoints | 858 route definitions, ~300+ unique |
| Phase routers | 30+ (Phase 7 through Phase 45A) |

### 2.2 Engine Inventory

| Engine | Purpose | Status | Key Files |
|--------|---------|--------|-----------|
| **0: Orchestrator** | Pipeline orchestration | Partial | orchestrator.py (976 lines) |
| **1: Apify Scraper** | Job scraping from defense boards | Complete | Config JSONs only |
| **2: Program Mapping** | 6-stage job→program matching | Complete | pipeline.py (1211 lines), program_mapper.py (1001 lines) |
| **3: OrgChart** | 6-tier contact classification | Complete | contact_classifier.py |
| **4: Playbook** | 5-section BD playbook generation | Complete | bd_playbook_generator.py (915 lines) |
| **5: Scoring** | 0-100 BD priority scoring | Complete | bd_scoring.py |
| **6: QA & Alerts** | Quality monitoring across collections | In Progress | quality_monitor.py, alerts.py |
| **7: Bullhorn ETL** | CRM data extraction | Complete | 40+ files, bullhorn_etl.py (913 lines) |
| **8: Knowledge** | Semantic search, RAG, agents, KG, MCP | Complete | 45+ files, api.py (3668 lines) |

### 2.3 Database Inventory

#### SQLite Databases (9 total)

**bullhorn_master.db** — 292.1 MB (duplicated at 2 locations = 584 MB wasted)

| Table | Rows | Cols | Key Columns |
|-------|------|------|-------------|
| candidates | 426,565 | 29 | bullhorn_candidate_id, name, email, job_title, company, clearance |
| activities | 404,715 | 17 | activity_type, action, related_job_id, related_candidate_id |
| call_notes | 50,710 | 20 | department, note_author, note_type, action, about |
| contact_scores | 9,837 | 11 | contact_name, score, tier, placement_count |
| contact_activity_summary | 2,585 | 14 | total_interactions, positive/negative |
| placement_program_links | 1,814 | 8 | placement_id, program_name, match_score |
| placements | 616 | 22 | job_id, candidate_id, pay_rate, bill_rate |
| past_performance | 492 | 28 | prime_contractor, program, fill_rate, performance_score |
| jobs | 135 | 29 | title, client_corporation, prime, clearance |
| prime_contractors | 41 | 22 | name, cage_code, total_jobs, total_revenue |
| programs | 4 | 21 | name, acronym, agency, contract_value |
| location_intelligence | 30 | 8 | location, mention_count, top_primes |
| gap_analysis | 103 | 9 | entity_type, gap_reason, recommendation |
| 5 empty tables | 0 | — | candidate_prime_history, job_prime_mapping, job_program_mapping, data_quality_log, processing_stats |

**bullhorn_past_performance.db** — 22.2 MB (from Data-Scraper)

| Table | Rows | Key Purpose |
|-------|------|-------------|
| notes_activity | 28,326 | CRM notes |
| contacts | 9,318 | Scraper contacts |
| programs | 8,414 | Program references |
| primes | 6,090 | Prime mentions |
| contact_intelligence | 6,157 | Enriched intel |
| jobs / jobs_enhanced | 1,558 each | Scraped + enriched jobs |

**Other databases**: bd_graph.db (2,166 entities, 938 relationships), memories.db (<1 MB), page_index.db, checkpoints_meta.db (empty), notifications.db

#### Qdrant Vector Collections (10+)

| Collection | Records | Dimensions | Key Payload Fields |
|------------|---------|------------|-------------------|
| contacts | 7,337 | 1536 | name, company, title, tier, program, bd_priority |
| programs | 401 | 1536 | name, prime_contractor, status, contract_vehicle |
| documents | 205 | 1536 | title, content, doc_type, tags |
| activities | 500 | 1536 | content, activity_type, contact_name |
| jobs | ~968 | 1536 | title, company, program_name, clearance |
| bullhorn_notes | ~50,000+ | 1536 | note_body, action, about (+ BM25 sparse) |
| federal_contracts | unknown | 1536 | title, agency, contractor, value (+ BM25 sparse) |
| intelligence_reports | unknown | 1536 | title, content, report_type (+ BM25 sparse) |
| opportunities | unknown | 1536 | title, agency, type, value |
| memories | unknown | **384** | Agent memory (different embedding model) |
| primes | unknown | 1536 | Prime contractor profiles |
| pipeline_tracking | unknown | 1536 | Pipeline stage tracking |

**Hybrid collections** (bullhorn_notes, federal_contracts, intelligence_reports) use additional SparseVectorParams with BM25 (`Modifier.IDF`) — this capability MUST be preserved in pgvector migration.

### 2.4 API Surface (858 Routes)

**Core API** (Engine8_Knowledge/api.py — 107 endpoints on port 8100):
- Search: `/search`, `/search/semantic`, `/search/keyword`, `/search/hybrid`
- RAG: `/ask`, `/ask/smart`
- Data: `/contacts/*`, `/programs/*`, `/jobs/*`, `/company/*`
- Graph: `/bdgraph/*` (12+ endpoints)
- Memory: `/memory/*` (add, search, entity, stats)
- Agents: `/agents/*` (status, analyze-program, prepare-outreach, weekly-intel, tasks)
- Pipeline: `/pipeline/*`, `/analytics/*`, `/predictions/*`
- AI Chat: `/ai/chat`, `/ai/chat/stream`
- Dashboard: `/dashboard/summary`, `/dashboard/stats`

**Unified API** (13 endpoints): `/api/v2/search`, contacts, programs, jobs, pipeline, analytics, stats

**30+ Phase Routers**: Phases 7 through 45A covering data freshness, pipeline, competitive intel, reports, ML, integrations, autonomous agents, graph analytics, realtime (WebSocket/SSE), embeddings, automation, platform, neo4j, search v2, workflows, scraping, memory, MCP, org chart, ML v2, optimizer, monitoring, streaming, predictive, NLQ, relationships, proposals, revenue, multi-tenant, data quality

**Dify Integration**: 12+ endpoints at `/dify/*` (knowledge search, RAG, agent invocation, n8n triggers)

### 2.5 AI/ML Inventory

**CrewAI Agents** (5 — all using GPT-4o/GPT-4o-mini):

| Agent | Role | LLM |
|-------|------|-----|
| program_researcher | Program Research Analyst | gpt-4o |
| contact_enricher | Contact Intelligence Specialist | gpt-4o |
| competitive_analyst | Competitive Intelligence Analyst | gpt-4o |
| outreach_composer | BD Outreach Strategist | gpt-4o-mini |
| humint_analyst | HUMINT Analyst | gpt-4o |

**Native BDAgent Subclasses** (10): ProgramIntelAgent, CompanyResearchAgent, ContactFinderAgent, BDStrategyAgent, ContactClassifierAgent, ScraperMonitorAgent, QualityAssuranceAgent, AnalyticsAgent, MorningBriefingAgent, ContactEnrichmentAgent

**CrewAI Crews** (3): bd_research_crew, contact_outreach_crew, weekly_intel_crew

**LLM Models**: claude-sonnet-4-20250514 (primary), claude-3-haiku-20240307 (LightRAG), gpt-4o (CrewAI), gpt-4o-mini (cost-efficient), text-embedding-3-small (embeddings)

**MCP Servers** (6): bd-knowledge, n8n, notion, notion-remote, apify, mapify

### 2.6 Entity Types (48 Total)

**Core Domain** (5): Contact, FederalProgram, ScrapedJob, Activity, Document
**Business** (5): PrimeContractor, PastPerformance, Placement, FederalContract, ContractOpportunity
**Knowledge Graph** (4): Entity (graph node), Relationship (edge), TemporalEntity, TemporalFact
**Agent Outputs** (12): ProgramIntelligence, ContactProfile, CompetitiveReport, OutreachPlan, HUMINTBrief, BDResearchBundle, WeeklyIntelBundle, ResearchRequest, OutreachRequest, WeeklyIntelRequest, TaskResponse, TaskStatus
**Revenue/Deal** (9): ScoredOpportunity, DimensionScore, PipelineReview, Deal, Placement, RevenueRecord, RevenueSummary, MarginAnalysis, ConcentrationRisk
**Governance** (8): DataContract, QualityTerm, ContractBreach, ContractCheckResult, PastPerformanceEntry, RelevanceScore, CPARSMetrics, PerformanceMatrix
**Operational** (5+): BullhornNote, Memory, Interaction, Episode, CollectionHealth, QualityReport, PlaybookData, ScoringResult, PipelineConfig

### 2.7 Known Issues

1. **Data duplication**: bullhorn_master.db at 2 locations (584 MB wasted), bd_graph.db duplicated
2. **Qdrant version mismatch**: Client 1.14.3 vs Server 1.16.3 (pydantic errors with local stores)
3. **5 empty database tables**: Never populated (candidate_prime_history, job_prime_mapping, etc.)
4. **API sprawl**: 858 routes across 40+ files, no centralized versioning
5. **Missing features**: Engine 6 QA incomplete, full pipeline not wired, Neo4j sparsely populated, multi-tenant auth not enforced
6. **No authentication**: Dev mode only, no rate limiting enforced

---

## 3. Target Tech Stack (From 2026 Architecture Research)

### 3.1 Component Migration Table

| Component | Current | Target | Version | Monthly Cost |
|-----------|---------|--------|---------|-------------|
| **Python tooling** | pip + venv | uv workspaces | v0.10.2 | $0 |
| **Database** | 9 SQLite files (314 MB) | Supabase Pro PostgreSQL | — | $25–50 |
| **Vector DB** | Qdrant (10+ collections, 811 MB) | pgvector + halfvec | v0.8.0 | Included |
| **Graph DB** | Docker Neo4j 5.26 | Neo4j AuraDB Professional | — | $65–100 |
| **Agent framework** | CrewAI 0.30 (5 agents + 10 native) | LangGraph supervisor pattern | v1.0.8 | $0–155 |
| **Primary LLM** | Claude Sonnet 4 + GPT-4o | Claude Opus 4.6 / Sonnet 4.5 / Haiku 4.5 | — | $100–500 |
| **Embeddings** | text-embedding-3-small (1536d) | Voyage 4 asymmetric (1024d) | — | ~$40–60 one-time |
| **RAG** | LlamaIndex + custom | Hybrid BM25 + dense + cross-encoder rerank | — | $0 |
| **Memory** | mem0ai + SQLite | Mem0g (graph memory) + PostgreSQL | — | $0 |
| **Dashboard** | React 19 + Vite (141 files) | Next.js 16.1 + shadcn/ui + Tremor | v16.1.6 LTS | $0 |
| **Caching** | Redis 7 | Redis 7 (keep) | v7-alpine | $0 |
| **Scraping** | Apify + Firecrawl + Crawl4AI | Same + Tango API (SAM.gov) | — | $400–600 |
| **MCP** | 6 servers (mixed) | Consolidated via langchain-mcp-adapters | — | $0 |
| **API** | FastAPI (858 routes, 40+ files) | FastAPI domain-driven (~100–150 routes) | — | $0 |
| **Auth** | None | Supabase Auth + RLS + RBAC | — | Included |
| **Hosting** | Docker Compose local | Railway | — | $20–45 |
| **Monitoring** | None | Sentry + Grafana Cloud (free tiers) | — | $0 |
| **Secrets** | .env files | Doppler | — | $0–12 |
| **CI/CD** | None | GitHub Actions | — | $4–12 |

### 3.2 Why Each Change

**uv v0.10.2**: Resolves 900+ packages in seconds, single cross-platform lockfile, Cargo-style workspaces. Apache Airflow manages 120+ distributions with uv workspaces.

**Supabase Pro + pgvector 0.8.0**: Eliminates Qdrant entirely. pgvector 0.8.0 iterative index scans deliver 5.7x query improvement. Timescale benchmarks: 471 QPS at 99% recall on 50M vectors (11.4x better than Qdrant). $25/month includes 8 GB storage, connection pooling, Auth, and real-time subscriptions.

**LangGraph 1.0.8**: Durable state persistence, PostgreSQL-backed checkpointing, first-class `interrupt()` API for human-in-the-loop. CrewAI cannot provide these. Each CrewAI agent maps to a `create_react_agent()` node; each Crew becomes a compiled `StateGraph`.

**Voyage 4**: #1 on RTEB leaderboard. Industry-first shared embedding space across all 4 models. Asymmetric strategy: embed documents with voyage-4-large ($0.12/M), query with voyage-4-lite ($0.02/M) — 14%+ better retrieval than OpenAI at same per-query cost. 1024d default with Matryoshka learning.

**Neo4j AuraDB Professional**: $65/GB/month, all 65+ Graph Data Science algorithms included. PageRank, Louvain community detection, betweenness centrality, Jaccard similarity. Managed, with pause functionality saving 80% costs.

**Claude Opus 4.6**: 1M-token context (beta), agent teams, automatic context compaction, ARC AGI 2 score of 68.8%. Structured outputs now GA with constrained decoding.

**Next.js 16.1**: App Router file-based routing, RBAC via server middleware, Supabase SSR package, Turbopack stable for dev+build. shadcn/ui + Tremor + TanStack Table v8 + React Flow v12.

---

## 4. Database Consolidation Plan

### 4.1 SQLite → PostgreSQL Migration

**Strategy**: Hybrid JSONB + typed columns pattern. 15–25 typed columns for queryable/filterable/joinable fields + single JSONB `details` column for everything else.

**Migration tool**: pgloader v3.6.9+ with automatic type conversion. Design unified schema first, then load into pre-existing tables with deduplication.

**Tables to migrate** (by priority):

| Source Table | Rows | Target PostgreSQL Table | Strategy |
|-------------|------|------------------------|----------|
| candidates | 426,565 | `persons` | 25 typed cols + JSONB details |
| activities | 404,715 | `interactions` | Merge with call_notes |
| call_notes | 50,710 | `interactions` | Merge with activities |
| contact_scores | 9,837 | `person_scores` | All typed cols |
| contact_activity_summary | 2,585 | Computed view | Materialized view from interactions |
| placement_program_links | 1,814 | `placement_programs` (junction) | All typed cols |
| placements | 616 | `placements` | 15 typed + JSONB |
| past_performance | 492 | `performance_records` | 15 typed + JSONB |
| jobs | 135 | `job_postings` | 20 typed + JSONB |
| prime_contractors | 41 | `organizations` | 15 typed + JSONB |
| programs | 4 | `programs` | All typed cols |
| Scraper contacts | 9,318 | Dedupe → `persons` | Merge with candidates |
| Scraper jobs | 1,558 | Dedupe → `job_postings` | Merge with jobs |
| Scraper notes_activity | 28,326 | → `interactions` | Merge |
| Graph entities | 2,166 | → Neo4j AuraDB | Not PostgreSQL |
| Graph relationships | 938 | → Neo4j AuraDB | Not PostgreSQL |

**Total rows to migrate**: ~900,000+ (after deduplication, likely ~600,000 unique)

### 4.2 Qdrant → pgvector Migration

**Vector storage calculation**:
- 1.4M vectors × 1024 dimensions × 2 bytes (halfvec) = ~2.7 GB raw
- With HNSW index overhead: ~8.5–11.5 GB total
- Supabase Pro 8 GB included; may need $25 add-on for storage

**Migration order** (smallest first to validate pipeline):
1. programs (401 vectors) — validate
2. documents (205 vectors) — validate
3. activities (500 vectors) — validate
4. jobs (~968 vectors) — validate
5. contacts (7,337 vectors) — production test
6. bullhorn_notes (~50,000+ vectors) — bulk migration
7. federal_contracts, intelligence_reports, opportunities — bulk
8. memories (384d → re-embed at 1024d) — special handling

**Hybrid search preservation**: BM25 sparse vectors on bullhorn_notes, federal_contracts, intelligence_reports must be replicated. pgvector supports hybrid search via `tsvector` + GIN indexes for BM25-equivalent keyword search combined with dense vector similarity.

### 4.3 Entity Type Consolidation (48 → 12–14)

| # | Target Entity | Current Sources | Records |
|---|--------------|----------------|---------|
| 1 | **Person** | Contact + Candidate + contact_scores + contact_activity_summary | ~435,000 |
| 2 | **Organization** | PrimeContractor + Company (Neo4j) | ~50 |
| 3 | **Program** | FederalProgram + programs (SQLite) + programs (CSV 388) | ~400 |
| 4 | **JobPosting** | ScrapedJob + jobs (SQLite) + jobs (scraper) | ~2,600 |
| 5 | **Interaction** | Activity + call_notes + activities + bullhorn_notes | ~500,000 |
| 6 | **Placement** | Placement + placement_program_links | ~2,400 |
| 7 | **Contract** | FederalContract + ContractOpportunity | TBD |
| 8 | **Document** | Document (Qdrant) | ~205 |
| 9 | **PerformanceRecord** | PastPerformance | ~492 |
| 10 | **Opportunity** | ScoredOpportunity + Deal + pipeline_tracking | TBD |
| 11 | **Location** | location_intelligence + key_locations | ~30 |
| 12 | **Capability** | Skill + technologies + certifications | Extracted |
| 13 | **AgentMemory** | Memory + Interaction (memories.db) | ~5 |
| 14 | **IntelligenceReport** | intelligence_reports (Qdrant) | TBD |

**Agent output models** (ProgramIntelligence, ContactProfile, CompetitiveReport, OutreachPlan, HUMINTBrief, etc.) become **ephemeral response types**, not persisted entities.

**Governance models** (DataContract, QualityTerm, ContractBreach, etc.) become **operational tables** in PostgreSQL, not core domain entities.

---

## 5. API Consolidation Plan

### 5.1 From 858 to ~100–150 Endpoints

**Three-phase approach**:
1. **Classify**: Each of 858 routes → production / scaffold / duplicate / dead
2. **Merge**: Interdependent resources consolidated
3. **Parameterize**: Variant endpoints replaced with query parameters

### 5.2 Target Domain Structure

| Domain | Core Endpoints | Specialized | Total |
|--------|---------------|-------------|-------|
| Programs | 5 CRUD | +3 (intel, map, search) | ~8 |
| Contacts/Persons | 5 CRUD | +3 (classify, enrich, search) | ~8 |
| Contracts | 5 CRUD | +3 (awards, expiring, opportunities) | ~8 |
| Jobs | 5 CRUD | +3 (scrape, score, match) | ~8 |
| Intelligence | 3 (search, ask, analyze) | +5 (graph, competitive, HUMINT) | ~8 |
| Agents | 5 (create, status, list, stream, cancel) | +3 (research, outreach, briefing) | ~8 |
| Pipeline | 5 (status, trigger, history, schedule, cancel) | +3 (analytics, funnel, predictions) | ~8 |
| Embeddings | 3 (embed, search, hybrid) | +2 (reindex, benchmark) | ~5 |
| System | 5 (health, stats, config, metrics, logs) | +3 (cache, notifications, webhooks) | ~8 |
| Auth | 5 (login, logout, refresh, profile, roles) | +3 (RBAC, tenants, audit) | ~8 |
| **Total** | | | **~80** |

Plus ~20–30 webhook/callback/streaming endpoints = **~100–110 total**

### 5.3 API Versioning

Single version prefix: `/api/v1/*`
All domain routers registered via `create_app()` factory with `APIRouter(prefix="/api/v1/{domain}", tags=[domain])`.

---

## 6. Agent Migration Plan (CrewAI → LangGraph)

### 6.1 Agent Mapping

| Current Agent | Framework | Target LangGraph Node | Priority |
|--------------|-----------|----------------------|----------|
| program_researcher | CrewAI (gpt-4o) | `create_react_agent("program_researcher", tools=[...])` | HIGH |
| contact_enricher | CrewAI (gpt-4o) | `create_react_agent("contact_enricher", tools=[...])` | HIGH |
| competitive_analyst | CrewAI (gpt-4o) | `create_react_agent("competitive_analyst", tools=[...])` | MEDIUM |
| outreach_composer | CrewAI (gpt-4o-mini) | `create_react_agent("outreach_composer", tools=[...])` | MEDIUM |
| humint_analyst | CrewAI (gpt-4o) | `create_react_agent("humint_analyst", tools=[...])` | LOW |
| ProgramIntelAgent | Native BDAgent | LangGraph node with Claude tools | HIGH |
| ContactClassifierAgent | Native BDAgent | LangGraph node with Claude tools | HIGH |
| BDStrategyAgent | Native BDAgent | LangGraph supervisor | MEDIUM |
| MorningBriefingAgent | Native BDAgent | Scheduled LangGraph workflow | MEDIUM |
| ContactEnrichmentAgent | Native BDAgent | LangGraph node | MEDIUM |
| QualityAssuranceAgent | Native BDAgent | LangGraph QA workflow | LOW |
| ScraperMonitorAgent | Native BDAgent | LangGraph monitoring workflow | LOW |
| AnalyticsAgent | Native BDAgent | LangGraph analytics workflow | LOW |

### 6.2 Crew → StateGraph Mapping

| Current Crew | Target StateGraph |
|-------------|-------------------|
| bd_research_crew | `bd_research_graph` (supervisor → program_researcher → competitive_analyst → contact_enricher) |
| contact_outreach_crew | `outreach_graph` (contact_enricher → outreach_composer) |
| weekly_intel_crew | `weekly_intel_graph` (program_researcher → humint_analyst → competitive_analyst) |

### 6.3 Key Architecture Decisions

- **Supervisor pattern**: `create_supervisor()` from `langgraph-supervisor-py` replaces CrewAI hierarchical process
- **State design**: `TypedDict` with `Annotated[list, operator.add]` for append-only audit trails
- **Checkpointing**: `langgraph-checkpoint-postgres` v3.0.4 with Supabase pooled connections
- **Human-in-the-loop**: `interrupt()` API — serializes state to PostgreSQL, pauses (zero compute), resumes with `Command(resume={"decision": "approved"})`
- **MCP integration**: `langchain-mcp-adapters` connects agents to MCP servers via `MultiServerMCPClient`
- **LLM model tiering**: Opus 4.6 for complex analysis, Sonnet 4.5 for production workflows, Haiku 4.5 for bulk processing

---

## 7. Embedding Migration Plan

### 7.1 Current → Target

| Aspect | Current | Target |
|--------|---------|--------|
| Model | text-embedding-3-small (OpenAI) | Voyage 4 (asymmetric) |
| Dimensions | 1536 | 1024 |
| Document embedding | text-embedding-3-small ($0.02/M) | voyage-4-large ($0.12/M) |
| Query embedding | text-embedding-3-small ($0.02/M) | voyage-4-lite ($0.02/M) |
| Storage format | float32 | halfvec (float16) |
| Storage per vector | 6,144 bytes | 2,048 bytes |
| **Storage reduction** | — | **~67%** |

### 7.2 Shared Embedding Space

Voyage 4's industry-first shared embedding space means all 4 models (large, standard, lite, nano) produce compatible embeddings. Embed documents once with the highest-quality model, query with the cheapest model — 14%+ better retrieval than OpenAI at same per-query cost.

### 7.3 Re-embedding Cost

- Total documents: ~1.4M (across all collections)
- Estimated tokens: ~700M
- Cost with batch API discount: **~$40–60 one-time**
- Timeline: 1–3 days

### 7.4 Migration Order

1. **programs** (401 vectors) — smallest, validates pipeline
2. **documents** (205 vectors) — small, validates quality
3. **activities** (500 vectors) — validates at scale
4. **jobs** (~968 vectors) — validates with enriched metadata
5. **contacts** (7,337 vectors) — production-scale test
6. **bullhorn_notes** (~50,000+ vectors) — bulk, preserving hybrid search
7. **federal_contracts, intelligence_reports** — bulk with hybrid
8. **memories** (384d → 1024d) — dimension change, special handling
9. **opportunities, primes, pipeline_tracking** — remaining

### 7.5 Hybrid Search Preservation

Current hybrid collections use BM25 sparse vectors. In pgvector:
- Dense vectors: `halfvec(1024)` column with HNSW index
- Keyword search: `tsvector` column with GIN index
- Hybrid: Reciprocal Rank Fusion of dense + keyword results
- Cross-encoder reranking (ZeroEntropy zerank-1): +28% NDCG@10 improvement

### 7.6 Specialized Models (Evaluate)

- **voyage-law-2** ($0.12/M, 16K context): Legal retrieval for FAR/DFARS — 6% better than OpenAI v3 large
- **voyage-context-3** ($0.18/M, 32K context): Chunk-with-context for cross-referenced regulations — 14.24% improvement
- Note: These are OUTSIDE the Voyage 4 shared space, evaluate on your specific corpus

---

## 8. Knowledge Graph Migration

### 8.1 Current State

- **Storage**: SQLite bd_graph.db (0.8 MB)
- **Entities**: 2,166 nodes (types: Contractor, Program, Contact, Job, Skill, Location, Meeting, Placement)
- **Relationships**: 938 edges (38 relationship types)
- **Temporal KG**: Separate system with Episodes, TemporalEntities, TemporalFacts (18 edge types)

### 8.2 Target: Neo4j AuraDB Professional

- **Cost**: $65/GB/month (1 GB sufficient for 3K→50K nodes)
- **Included**: All 65+ Graph Data Science algorithms at no extra cost
- **Native vector indexes**: HNSW up to 4,096 dimensions (January 2026 release)

### 8.3 Key Algorithms for BD Intelligence

| Algorithm | Use Case |
|-----------|----------|
| **PageRank** | Identify most influential prime contractors via AWARDED_TO/PRIMES_ON |
| **Louvain community detection** | Reveal natural teaming ecosystems (PARTNERS_WITH/SUBS_TO clusters) |
| **Betweenness centrality** | Find key connector contacts bridging contractor communities |
| **Node similarity (Jaccard)** | Discover companies with overlapping contract portfolios |

### 8.4 GraphRAG Integration

- `langchain-neo4j` provides: `Neo4jGraph` (Cypher), `Neo4jVector` (semantic on node embeddings), `LLMGraphTransformer` (auto-populate from text)
- LangGraph workflow routes queries to graph traversal, vector search, or hybrid based on query type
- Multi-hop queries: "find companies that partner with our competitors on programs we're targeting"

### 8.5 Migration Path

1. `neo4j-admin database dump` from Docker instance
2. Upload via AuraDB Console (drag-and-drop, under 4 GB)
3. Start on AuraDB Free ($0, 200K node limit) for validation
4. Migrate to Professional when ready
5. Pause functionality saves 80% costs (16 hrs/day paused → ~$30–40/month)

---

## 9. Dashboard Migration

### 9.1 Current State

- **Framework**: React 19 + Vite + TanStack Query/Router/Table
- **Files**: 141 TypeScript/TSX source files, 34 pages
- **State**: Zustand stores
- **Styling**: Tailwind CSS v4 + Tremor
- **Data**: Static JSON files in `dashboard/dist/data/` + API calls to :8100

### 9.2 Target: Next.js 16.1 LTS

| Aspect | Current | Target |
|--------|---------|--------|
| Framework | React 19 + Vite | Next.js 16.1.6 LTS |
| Routing | TanStack Router | App Router (file-based) |
| Data fetching | TanStack Query + hubApi.ts | Server Components + Supabase SSR |
| State | Zustand (24+ stores) | Zustand (keep) + Server State |
| Components | Radix UI + Tremor | shadcn/ui + Tremor |
| Tables | TanStack Table | TanStack Table v8 + Virtual |
| Charts | Recharts + Tremor | Tremor (keep) |
| Graph viz | reagraph | React Flow v12 (@xyflow/react) |
| Build | Vite 7 | Turbopack (stable in Next.js 16) |
| Auth | None | Supabase Auth + middleware RBAC |
| Real-time | Manual polling | Supabase Realtime (postgres_changes) |

### 9.3 RBAC Architecture

Three-layer pattern:
1. **Supabase Auth Hooks** inject `user_role` into JWT custom claims
2. **Next.js middleware** enforces route-level access
3. **PostgreSQL RLS policies** enforce data-level isolation

Performance: Wrap `auth.uid()` in `(SELECT ...)` to cache per-statement.

### 9.4 Migration Strategy

The 141 TSX files / 34 pages require incremental conversion:
1. Set up Next.js 16.1 with App Router scaffold
2. Port shared components (Tremor charts, tables) first
3. Convert pages incrementally (start with dashboard summary, contacts, programs)
4. Add RBAC middleware after core pages work
5. Wire Supabase Realtime for live intelligence feeds

---

## 10. Data Collection & External APIs

### 10.1 URGENT: FPDS Decommission (February 24, 2026)

**FPDS.gov ezSearch decommissions February 24, 2026.** All contract award data migrates to SAM.gov.

**Action**: Integrate **Tango by MakeGov** — unified API covering FPDS, USASpending, SAM.gov, Grants.gov with:
- Python and Node.js SDKs
- Webhooks for near-real-time notifications
- Response shaping (request only needed fields)
- Consistent data models across all 4 government sources

**Backup**: Direct SAM.gov Contract Awards API integration.

### 10.2 Job Scraping

**Current**: Apify actor configs for defense contractor job boards
**Target**: **Fantastic.jobs Career Site Job Listing API** on Apify — covers 42 ATS platforms including Workday (used by virtually every Tier 1 defense contractor). 175K+ career sites, AI-enriched (60 fields/job), new jobs within 3 hours.

**Supplemental**:
- **Firecrawl Standard** ($83/month) for ad-hoc web intelligence
- **Crawl4AI** (free, self-hosted) for sensitive extraction

### 10.3 Contact Enrichment

- **Apollo.io** ($49–99/month) or **RocketReach** ($75–175/month) for API-accessible professional data
- **Deltek GovWin IQ** ($7K–45K/year) for pre-RFP intelligence (if budget allows)

### 10.4 Preserved Integrations

| Integration | Current Config | Keep/Migrate |
|-------------|---------------|-------------|
| Notion (5 databases) | Database IDs in config/settings.py | Keep, update sync logic |
| N8N webhooks | Dify bridge triggers 5+ workflows | Keep, update endpoints |
| Slack alerts | Engine 6 webhook delivery | Keep |
| Bullhorn CRM API | Engine 7 ETL | Keep for ongoing sync |

---

## 11. Security & Compliance

### 11.1 Current State

- No authentication on any endpoint
- API keys in .env files (properly gitignored)
- No rate limiting enforced
- No audit logging
- Development-only configuration

### 11.2 Target Security Stack

| Layer | Technology | Details |
|-------|-----------|---------|
| Auth | Supabase Auth | JWT-based, social/email login |
| Authorization | RLS + RBAC | Row-level security with tenant isolation |
| Audit | supa_audit + pgAudit | Data change + operation logging |
| Secrets | Doppler ($4/user/mo) | SOC 2 Type II, automated rotation |
| Compliance | Supabase SOC 2 Type 2 | Annual audits, adequate for public data |
| AI data handling | Anthropic commercial terms | No training on API data, 7-day retention |

### 11.3 CMMC Posture

- **Current requirement**: None — BD platform handles only publicly-sourced data (exempt from DFARS 252.204-7012)
- **Recommended**: CMMC Level 1 (17 controls) for competitive advantage
- **Phase 1 active** since November 10, 2025; Phase 2 (C3PAO certification) begins November 10, 2026
- **Design principle**: Clean separation between public and controlled data from day one

### 11.4 FedRAMP Considerations

- **Neither Supabase nor Neo4j AuraDB are FedRAMP authorized**
- If platform ever handles CUI: migrate to self-hosted on AWS GovCloud
- Azure OpenAI in GovCloud is the FedRAMP-authorized LLM path
- Anthropic Claude not available in GovCloud
- **Current decision**: Not needed for public data, but architect for future migration

---

## 12. Infrastructure & Monthly Cost

### 12.1 Full Cost Breakdown

| Component | Service | Monthly Cost |
|-----------|---------|-------------|
| Database + pgvector | Supabase Pro | **$25–50** |
| Graph database | Neo4j AuraDB Professional | **$65–100** |
| Workflow automation | N8N Cloud Pro | **$55** |
| Backend + frontend hosting | Railway | **$20–45** |
| AI API usage | Anthropic + Voyage 4 | **$100–500** |
| Data collection | Apify + Firecrawl | **$100–200** |
| Error monitoring | Sentry (free tier) | **$0** |
| Metrics and logs | Grafana Cloud (free tier) | **$0** |
| Secrets management | Doppler (Team) | **$0–12** |
| CI/CD | GitHub Actions | **$4–12** |
| **Total range** | | **$370–975** |

### 12.2 AI Cost Optimization

- **Prompt caching**: 90% discount on cached reads (Anthropic)
- **Batch API**: 50% off for non-urgent processing
- **Model tiering**: Haiku 4.5 ($1/$5) for bulk, Sonnet 4.5 ($3/$15) for production, Opus 4.6 ($5/$25) for complex analysis
- **Structured outputs**: 2–3% cost overhead but eliminates all retry logic

### 12.3 Infrastructure Decisions

- **Docker Compose** for local development (keep)
- **Railway** ($10–25/service) for production deployment with git-push deploys
- **Kubernetes**: Not justified for 1–3 person team
- Start on free tiers (Neo4j AuraDB Free, Sentry Free, Grafana Free) for validation

---

## 13. Implementation Phases

### Phase 0: URGENT — FPDS Migration (Before February 24)
- Integrate Tango by MakeGov API
- Set up SAM.gov Contract Awards API as backup
- Update all FPDS data consumers
- **Dependencies**: None
- **Risk**: Data gap if missed

### Phase 1: Supabase + pgvector Foundation
- Design unified PostgreSQL schema (hybrid JSONB + typed columns)
- Migrate 9 SQLite databases via pgloader
- Set up pgvector with halfvec quantization
- Deduplicate records across sources
- Set up Supabase Auth + basic RLS
- **Dependencies**: Schema design complete
- **Risk**: Data loss during migration (mitigate: keep SQLite backups)

### Phase 2: Voyage 4 Re-embedding
- Set up Voyage 4 API integration
- Re-embed all collections (~1.4M documents, ~$40–60)
- Validate retrieval quality vs current embeddings
- Set up asymmetric embedding pipeline (large for docs, lite for queries)
- Migrate hybrid search (BM25 → tsvector + GIN)
- **Dependencies**: Phase 1 (pgvector ready)
- **Risk**: Low (one-time cost, reversible)

### Phase 3: LangGraph Migration
- Start with most critical agent (program_researcher)
- Implement PostgreSQL checkpointing via Supabase
- Prove out `interrupt()` human-in-the-loop pattern
- Migrate remaining 12 agents incrementally
- Wire supervisor pattern for crew workflows
- **Dependencies**: Phase 1 (PostgreSQL checkpointing)
- **Risk**: Medium (agent behavior parity validation)

### Phase 4: API Consolidation
- Audit all 858 routes: classify as production/scaffold/duplicate/dead
- Design domain-driven router structure (~10 domains × ~8 endpoints)
- Implement with FastAPI APIRouter + prefix/tags/dependencies
- Backward-compatible response formats during transition
- **Dependencies**: Phase 1 (new data layer)
- **Risk**: Low (can be incremental)

### Phase 5: Neo4j AuraDB Migration
- Dump Docker Neo4j graph (3K nodes)
- Upload to AuraDB Free for validation
- Test GDS algorithms (PageRank, Louvain, betweenness centrality)
- Wire GraphRAG via langchain-neo4j
- Migrate to Professional when validated
- **Dependencies**: None (can run in parallel with Phases 2–4)
- **Risk**: Low (small graph, managed service)

### Phase 6: Dashboard Migration to Next.js 16.1
- Set up Next.js 16.1 with App Router
- Port shared components (Tremor, tables)
- Convert 34 pages incrementally
- Wire Supabase Realtime for live feeds
- Add React Flow v12 for entity graph visualization
- **Dependencies**: Phases 1 + 4 (API endpoints stable)
- **Risk**: High (longest pole, 141 files to convert)

### Phase 7: Auth & RBAC
- Configure Supabase Auth Hooks for role injection
- Implement Next.js middleware for route-level access
- Write PostgreSQL RLS policies for data isolation
- Audit logging via supa_audit + pgAudit
- **Dependencies**: Phase 6 (dashboard ready)
- **Risk**: Medium (security-critical, needs thorough testing)

### Phase 8: Production Hardening
- Set up Doppler for secrets management
- Configure Sentry error monitoring
- Set up Grafana Cloud dashboards
- Deploy to Railway with git-push workflow
- GitHub Actions CI/CD pipeline
- Performance testing and optimization
- **Dependencies**: All previous phases
- **Risk**: Low (operational, not architectural)

---

## 14. Target Monorepo Structure

```
bd-intelligence-platform/          # uv v0.10.2 workspace root
├── pyproject.toml                 # Workspace declaration
├── uv.lock                        # Single cross-platform lockfile
├── packages/
│   ├── bd-core/                   # Shared models, config, utils
│   │   ├── pyproject.toml
│   │   └── src/bd_core/
│   │       ├── models/            # 12-14 unified entity models
│   │       ├── config/            # Centralized settings (Pydantic)
│   │       └── utils/             # Shared utilities
│   ├── bd-agents/                 # LangGraph agent definitions
│   │   ├── pyproject.toml
│   │   └── src/bd_agents/
│   │       ├── graphs/            # StateGraph definitions
│   │       ├── nodes/             # Agent nodes (react agents)
│   │       ├── tools/             # Agent tools
│   │       └── supervisors/       # Supervisor patterns
│   └── bd-embeddings/             # Voyage 4 embedding operations
│       ├── pyproject.toml
│       └── src/bd_embeddings/
│           ├── voyage/            # Voyage 4 client
│           ├── indexer/           # Document indexing
│           └── search/            # Hybrid search (dense + BM25)
├── domains/
│   ├── programs/                  # Program domain
│   │   ├── router.py              # FastAPI router
│   │   ├── schemas.py             # Pydantic request/response
│   │   ├── service.py             # Business logic
│   │   └── repository.py          # Database queries
│   ├── contacts/                  # Contact/Person domain
│   ├── contracts/                 # Federal contracts domain
│   ├── jobs/                      # Job postings domain
│   ├── intelligence/              # Intel reports, HUMINT, analysis
│   ├── scraping/                  # Data collection domain
│   ├── agents/                    # Agent management domain
│   ├── pipeline/                  # BD pipeline tracking
│   ├── analytics/                 # Analytics & predictions
│   └── system/                    # Health, config, admin
├── app/
│   ├── main.py                    # create_app() factory
│   └── dependencies.py            # FastAPI dependency injection
├── migrations/                    # Alembic database migrations
├── tests/                         # Test suite
├── frontend/                      # Next.js 16.1 dashboard (separate)
│   ├── app/                       # App Router pages
│   ├── components/                # shadcn/ui + Tremor
│   └── lib/                       # Supabase client, utils
├── docker-compose.yml             # Local development stack
└── .github/workflows/             # CI/CD
```

---

## 15. Data Preservation Checklist

| Data | Records | Size | Priority | Migration Path |
|------|---------|------|----------|---------------|
| Bullhorn candidates | 426,565 | ~200 MB | CRITICAL | → persons (PostgreSQL) |
| Bullhorn activities | 404,715 | ~50 MB | CRITICAL | → interactions (PostgreSQL) |
| Call notes | 50,710 | ~30 MB | HIGH | → interactions (PostgreSQL) |
| Contact scores | 9,837 | <1 MB | HIGH | → person_scores (PostgreSQL) |
| Past performance | 492 | <1 MB | CRITICAL | → performance_records (PostgreSQL) |
| Placements | 616 | <1 MB | CRITICAL | → placements (PostgreSQL) |
| Prime contractors | 41 | <1 MB | CRITICAL | → organizations (PostgreSQL) |
| Programs (CSV) | 388 | 2 MB | CRITICAL | → programs (PostgreSQL) |
| Knowledge graph | 3,104 | <1 MB | HIGH | → Neo4j AuraDB |
| Qdrant contacts | 7,337 | ~50 MB | CRITICAL | Re-embed → pgvector |
| Qdrant programs | 401 | <5 MB | HIGH | Re-embed → pgvector |
| Qdrant documents | 205 | <5 MB | MEDIUM | Re-embed → pgvector |
| Qdrant bullhorn_notes | ~50,000+ | ~300 MB | HIGH | Re-embed → pgvector |
| Federal Programs CSV | 388 | 2 MB | CRITICAL | → programs (PostgreSQL) |
| Scraper databases | 62K+ rows | 22 MB | HIGH | Dedupe → PostgreSQL |

---

*This document supersedes all previous architecture/rebuild plans (OPENCLAW_MASTER_ARCHITECTURE, UNIFIED_BD_INTELLIGENCE_HUB_BUILD, BD_AUTOMATION_ENGINE_IMPLEMENTATION_PLAN, COMPREHENSIVE_BD_HUB_MASTER_PLAN_V2). It is the single authoritative reference for the next-gen platform rebuild.*
