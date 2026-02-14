# BD-AUTOMATION-ENGINE COMPREHENSIVE AUDIT REPORT
**Generated**: 2026-02-14 | **Branch**: claude/setup-auto-claude-IrK21 | **Last Commit**: b5df2b45

---

## 1. REPOSITORY STATS

| Metric | Value |
|--------|-------|
| Total Python files | ~200+ (excluding .auto-claude worktrees) |
| Total lines of Python code | ~153,813 (including worktree copies) |
| Estimated unique LoC | ~60,000-70,000 |
| Total data size | **2.5+ GB** (data/ 1.4G, Engine8 811M, Engine7 293M, Engine3 32M) |
| SQLite databases | 9 databases, largest 292 MB |
| Qdrant collections | 10+ collections, 8,447+ vectors |
| Dashboard source files | 141 TypeScript/TSX files |
| API endpoints | 858 route definitions, ~300+ unique endpoints |
| Last commit | b5df2b45 - feat: Add BD action engines, predictive insights, dashboard |
| Git status | Clean working tree |

---

## 2. ENGINE INVENTORY

### Engine 0: Orchestrator
- **Purpose**: Pipeline orchestration across all engines
- **Files**: `orchestrator.py` (976 lines), `Engine0_Orchestrator/orchestrator.py`
- **Key Classes**: `StepResult`, `PipelineRun`
- **Status**: Partial (orchestrator exists, full pipeline integration pending)

### Engine 1: Apify Scraper
- **Purpose**: Job scraping from defense contractor job boards via Apify
- **Files**: Configuration JSONs only, no Python entry point
- **Data**: `Engine1_Scraper/data/` (3.1 MB) - scraped job JSON/CSV files
- **Dependencies**: Apify API (external service)
- **Status**: Complete (configuration-based, runs externally)

### Engine 2: Program Mapping
- **Purpose**: 6-stage pipeline: job standardization, federal program matching, BD scoring
- **Files**: 5 Python files (pipeline.py 1211 lines, program_mapper.py 1001 lines, job_standardizer.py 878 lines, exporters.py, full_pipeline.py)
- **Key Classes**: `PipelineConfig` (dataclass), `FederalProgram` (dataclass)
- **Key Functions**: `load_federal_programs()`, standardize/map/score pipeline stages
- **Data reads**: Federal_Programs_MASTER_V4.csv (388 programs), scraped job JSONs
- **Data writes**: Mapped/scored job outputs, Notion CSV, n8n JSON
- **Dependencies**: anthropic (LLM extraction), pandas
- **Status**: Complete

### Engine 3: OrgChart Contact Classification
- **Purpose**: 6-tier hierarchy classification of contacts (Executive → IC)
- **Files**: `contact_classifier.py`, `contact_lookup.py`
- **Key Data**: `TIER_DEFINITIONS` dict with regex patterns per tier, BD priority mappings
- **Data reads**: Bullhorn contact CSVs, 30+ Prime_Contacts company folders
- **Data writes**: Classified contact records with tier/priority
- **Dependencies**: anthropic, regex
- **Status**: Complete

### Engine 4: BD Playbook Generator
- **Purpose**: Generate 5-section BD playbooks per opportunity
- **Files**: `bd_playbook_generator.py` (915 lines)
- **Key Class**: `PlaybookData` (dataclass, 25+ fields)
- **Sections Generated**: Program Intel, Org Intel, Pain Points, Competitive Landscape, Action Plan
- **Output Formats**: Intro Email, Call Script, Talking Points, Full Playbook (Markdown)
- **Dependencies**: anthropic
- **Status**: Complete

### Engine 5: BD Priority Scoring
- **Purpose**: 0-100 scoring algorithm with Hot/Warm/Cold tiers
- **Files**: `bd_scoring.py`
- **Key Classes**: `ScoringResult` (dataclass), `BD_SCORE_CONFIG` dict
- **Scoring Factors**: Clearance boosts (5-35 pts), program boosts (8-15 pts), location boosts (5-10 pts), tier multipliers (0.9-1.3x), match confidence weight (20 pts), recency boosts (2-10 pts)
- **Tier Thresholds**: Hot ≥80, Warm ≥50, Cold <50
- **Status**: Complete

### Engine 6: QA & Alerts
- **Purpose**: Quality monitoring across Qdrant collections
- **Files**: `quality_monitor.py`, `scripts/alerts.py`, `scripts/qa_feedback.py`
- **Key Classes**: `QualityMonitor`, `CollectionHealth`, `DataQualityScore`, `QualityReport`
- **Monitored Collections**: contacts, programs, documents, activities, jobs, bullhorn_notes, federal_contracts, intelligence_reports, opportunities
- **Required Payload Fields**: Defined per collection (e.g., contacts need name+company)
- **Dependencies**: qdrant_client, openai (embeddings for alerts)
- **Status**: In progress (core monitoring works, feedback loop incomplete)

### Engine 7: Bullhorn ETL
- **Purpose**: Extract/Transform/Load from Bullhorn CRM exports
- **Files**: 40+ Python files including `bullhorn_etl.py` (913 lines), `bullhorn_etl_v2.py` (1205 lines), `database_schema.py`, `import_coworker_data.py` (1038 lines)
- **Key Classes**: `BullhornConnector`, `BullhornETL`
- **File Types Processed**: Leidos Jobs, Notes Activity Reports, Client Visits, Placements, Submissions, Notes Summary
- **Company Normalizations**: 18 prime contractor name mappings (Leidos, Boeing, SAIC, etc.)
- **Database**: `bullhorn_master.db` (292 MB, 22 tables, 896K+ total rows)
- **Dependencies**: pandas, sqlite3
- **Status**: Complete

### Engine 8: AI Knowledge System
- **Purpose**: Semantic search, RAG, AI agents, knowledge graph, MCP server
- **Files**: 45+ Python files, `api.py` (3668 lines - main API server)
- **Key Classes**: `BDKnowledgeStore`, `BDRAGEngine`, `BDIndexer`, `BDDataLoader`, `BDKnowledgeGraph`
- **Qdrant Collections**: 5 primary (jobs, contacts, programs, documents, activities) + 5+ secondary
- **Vector Dimensions**: 1536 (text-embedding-3-small)
- **API Port**: 8100
- **30+ included routers** from Phase 7 through Phase 45A
- **Dependencies**: qdrant_client, fastapi, openai, anthropic, llama-index, crewai, fastmcp, langgraph, mem0ai, lightrag-hku, rank-bm25, redis
- **Status**: Complete (massive, most complete engine)

---

## 3. DATABASE INVENTORY

### SQLite Databases

#### `Engine7_BullhornETL/data/bullhorn_master.db` — 292.1 MB
Also duplicated at `data/bullhorn_master.db` (symlink/copy)

| Table | Rows | Cols | Key Columns |
|-------|------|------|-------------|
| activities | 404,715 | 17 | bullhorn_activity_id, activity_type, action, related_job_id, related_candidate_id |
| call_notes | 50,710 | 20 | department, note_author, date_added, note_type, action, about, status |
| candidates | 426,565 | 29 | bullhorn_candidate_id, first_name, last_name, email, phone, job_title, company_name, clearance_level |
| contact_activity_summary | 2,585 | 14 | contact_name, total_interactions, positive/negative_interactions, last_status |
| contact_scores | 9,837 | 11 | contact_name, score, tier, placement_count, activity_count, prime_count |
| placements | 616 | 22 | bullhorn_placement_id, job_id, candidate_id, placement_date, pay_rate, bill_rate |
| jobs | 135 | 29 | bullhorn_job_id, title, client_corporation, prime_contractor, clearance_required |
| prime_contractors | 41 | 22 | name, normalized_name, aliases, cage_code, total_jobs, total_revenue |
| programs | 4 | 21 | name, acronym, prime_contractor_name, agency, contract_value |
| past_performance | 492 | 28 | prime_contractor_name, program_name, total_jobs, fill_rate, performance_score |
| placement_program_links | 1,814 | 8 | placement_id, program_name, match_score |
| location_intelligence | 30 | 8 | location_name, mention_count, top_primes, clearance_distribution |
| gap_analysis | 103 | 9 | entity_type, entity_name, gap_reason, recommendation |
| prime_call_mentions | 31 | 10 | prime_name, mention_count, positive/negative_mentions |
| program_call_mentions | 30 | 11 | program_name, mention_count, is_gap_program |
| source_files | 20 | 12 | filename, file_type, entity_type, record_count |
| candidate_prime_history | 0 | 8 | (empty) |
| job_prime_mapping | 0 | 5 | (empty) |
| job_program_mapping | 0 | 6 | (empty) |
| data_quality_log | 0 | 11 | (empty) |
| processing_stats | 0 | 12 | (empty) |

#### `data/from_data_scraper/bullhorn_past_performance.db` — 22.2 MB

| Table | Rows | Key Purpose |
|-------|------|-------------|
| contacts | 9,318 | External scraper contacts |
| contact_intelligence | 6,157 | Enriched contact intelligence |
| jobs | 1,558 | Scraped jobs |
| jobs_enhanced | 1,558 | Enriched jobs |
| notes_activity | 28,326 | CRM notes |
| primes | 6,090 | Prime contractor mentions |
| primes_clean | 9 | Deduplicated primes |
| primes_extracted | 61 | Extracted prime intelligence |
| programs | 8,414 | Program references |
| programs_clean | 985 | Deduplicated programs |
| programs_extracted | 51 | Extracted program intelligence |
| prime_intelligence | 61 | Aggregated prime intel |
| program_intelligence | 51 | Aggregated program intel |
| placements | 0 | (empty) |

#### `Engine8_Knowledge/data/bd_graph.db` (also at `data/bd_graph.db`) — 0.8 MB

| Table | Rows | Purpose |
|-------|------|---------|
| entities | 2,166 | Knowledge graph nodes (Contractor, Program, Contact, Job, Skill, Location, Meeting, Placement) |
| relationships | 938 | Knowledge graph edges (38 relationship types) |

#### Other Small Databases

| Database | Size | Purpose |
|----------|------|---------|
| `data/memories.db` | <1 MB | Agent memories (3 memories, 1 insight, 1 interaction) |
| `data/page_index.db` | <1 MB | Document page index (1 page) |
| `data/checkpoints_meta.db` | <1 MB | LangGraph workflow checkpoints (empty) |
| `Engine8_Knowledge/data/notifications.db` | <1 MB | System notifications (1 notification) |
| `Engine7_BullhornETL/data/bullhorn.db` | 0 MB | Empty placeholder |

### Qdrant Vector Database

**Connection**: `http://localhost:6333`

**Collections** (from code references):

| Collection | Est. Records | Vector Dim | Key Payload Fields |
|------------|-------------|------------|-------------------|
| contacts | 7,337 | 1536 | name, company, title, tier, program, bd_priority |
| programs | 401 | 1536 | name, prime_contractor, status, contract_vehicle |
| documents | 205 | 1536 | title, content, doc_type, tags |
| activities | 500 | 1536 | content, activity_type, contact_name, company |
| jobs | ~968 | 1536 | title, company, program_name, clearance, bd_priority |
| bullhorn_notes | ~50,000+ | 1536 | note_body, action, about, personReference |
| federal_contracts | unknown | 1536 | title, agency, contractor, value |
| intelligence_reports | unknown | 1536 | title, content, report_type |
| opportunities | unknown | 1536 | title, agency, type, value |
| pipeline_tracking | unknown | 1536 | Pipeline stage tracking |
| primes | unknown | 1536 | Prime contractor profiles |
| memories | unknown | 1536 | Agent long-term memory |

**Embedding Model**: `text-embedding-3-small` (OpenAI), 1536 dimensions, Cosine distance
**Exception**: `memories` collection uses **384 dimensions** (smaller model for memory embeddings)
**Hybrid Collections**: bullhorn_notes, federal_contracts, intelligence_reports use additional `SparseVectorParams` with BM25 (`Modifier.IDF`)

---

## 4. API SURFACE

### Total Endpoints
- **858 route definitions** across all files
- **~300+ unique endpoints** (many are phase-specific routers)
- **Engine8_Knowledge/api.py**: 107 endpoints (core API)
- **30+ included routers** covering phases 7 through 45A

### Core API (Engine8_Knowledge/api.py — Port 8100)

**Search & RAG:**
- `POST /search` — Semantic search
- `POST /search/semantic` — Pure semantic
- `POST /search/keyword` — BM25 keyword
- `POST /search/hybrid` — Hybrid (semantic + keyword)
- `POST /ask` — RAG Q&A
- `POST /ask/smart` — Smart routing + RAG

**Data Access:**
- `POST /contacts/filter` — Filter contacts
- `POST /programs/filter` — Filter programs
- `GET /jobs/for/{program}` — Jobs by program
- `GET /contacts/at/{company}` — Contacts at company
- `GET /program/{name}` — Program detail
- `GET /company/{name}` — Company detail

**Knowledge Graph:**
- `POST /bdgraph/*` — 12+ graph endpoints (query, search, entity, relationship, populate, types, stats, introduction-path)

**Memory System:**
- `POST /memory/add` — Store memory
- `GET /memory/search` — Search memories
- `GET /memory/entity/{id}` — Entity memories
- `GET /memory/stats` — Memory stats

**Agent Operations:**
- `GET /agents/status` — Agent health
- `POST /agents/analyze-program` — Program analysis
- `POST /agents/prepare-outreach` — Outreach prep
- `POST /agents/weekly-intel` — Weekly intelligence
- `POST /agents/tasks/create` — Create agent task
- `GET /agents/tasks/stats` — Task statistics
- `GET /agents/tasks/{id}/stream` — SSE task stream

**Pipeline & Analytics:**
- `GET /pipeline/status` — Pipeline status
- `POST /pipeline/trigger` — Trigger pipeline
- `GET /analytics/summary` — Analytics summary
- `GET /analytics/funnel` — BD funnel
- `GET /predictions/recompetes` — Recompete predictions
- `GET /predictions/best-channels` — Best outreach channels

**AI Chat:**
- `POST /ai/chat` — AI chat
- `POST /ai/chat/stream` — Streaming AI chat

**System:**
- `GET /health` — Health check
- `GET /stats` — Collection stats
- `GET /system/cross-repo-health` — Cross-repo health
- `GET /dashboard/summary` — Dashboard summary
- `GET /dashboard/stats` — Dashboard stats

### Unified API (api/unified_endpoints.py — 13 endpoints)
- `POST /api/v2/search` — Cross-collection semantic search
- `GET /api/v2/contacts` — Paginated contacts
- `POST /api/v2/contacts/search` — Contact search
- `GET /api/v2/programs` — Programs list
- `GET /api/v2/jobs` — Jobs list
- `GET /api/v2/pipeline` — Pipeline tracking
- `GET /api/v2/analytics` — Analytics data
- `GET /api/v2/stats` — System stats

### Phase Router Endpoints (30+ routers)

| Phase | Router | Key Endpoints |
|-------|--------|--------------|
| 7 | data freshness | /data/freshness, /notifications, /webhooks |
| 8A | pipeline | /pipeline/run, /pipeline/status |
| 9A | competitive | /contracts/awards, /contracts/expiring |
| 10A | reports | /reports/weekly |
| 13A | ML | /ml/predict-response, /ml/hiring-signals |
| 14A | integrations | /integrations/slack, /integrations/crm |
| 15A | autonomous | /agents/autonomous/* |
| 16A | graph analytics | /graph/influence, /graph/communities |
| 17A | realtime | /ws/dashboard, /sse/*, /realtime/* |
| 18A | embeddings | /embeddings/embed, /embeddings/benchmark |
| 19A | automation | /automation/schedule, /automation/workflows |
| 20A | platform | /platform/stats, /platform/services |
| 21A | neo4j | /neo4j/health, /neo4j/ingest, /neo4j/contacts |
| 22A | search v2 | /search/v2, /search/v2/hybrid, /search/v2/graphrag |
| 23A | workflows | /workflows/start, /workflows/active |
| 24A | scraping | /scrape/*, /sam/*, /federal-docs/* |
| 25A | memory | /memory/add, /memory/search, /memory/lifecycle |
| 26A | MCP | /mcp/health, /mcp/tools, /mcp/config |
| 27A | org chart | /org-chart/generate, /org-chart/export |
| 28A | ML v2 | /ml/ner, /ml/topics, /ml/predict |
| 29A | optimizer | /optimizer/assess, /optimizer/recommendations |
| 30A | monitoring | /monitoring/health, /metrics |
| 31A | streaming | /streaming/* (14 REST + 4 WebSocket) |
| 32A | predictive | /predict/* (14 endpoints) |
| 33A | NLQ | /nlq/* (9 endpoints) |
| 34A | relationships | /relationships/* (14 endpoints) |
| 35A | proposals | /proposals/* (10 endpoints) |
| 36A | revenue | /revenue/* (16 endpoints) |
| 37A | multi-tenant | /tenants/*, /auth/* (21 endpoints) |
| 38A | data quality | /data-quality/* (17 endpoints) |
| 45A | MCP v2 | /api/mcp/* (10 endpoints) |

### Authentication
- No auth on most endpoints (local development)
- Phase 37A has RBAC/tenant framework (not enforced)

### Response Formats
- `/api/v2/contacts` → `{"contacts": [...], "total": N}`
- `/api/v2/programs` → `{"programs": [...], "total": N}`
- `/api/v2/jobs` → `{"jobs": [...], "total": N}`
- `/search` → `{"results": [...], "count": N}`
- `/ask/smart` → `{"answer": "...", "query_type": "...", "systems_used": [...]}`

---

## 5. AI/ML INVENTORY

### CrewAI Agents

| Agent | Role | LLM | File |
|-------|------|-----|------|
| program_researcher | Program Research Analyst | gpt-4o | bd_agents.py |
| contact_enricher | Contact Intelligence Specialist | gpt-4o | bd_agents.py |
| competitive_analyst | Competitive Intelligence Analyst | gpt-4o | bd_agents.py |
| outreach_composer | BD Outreach Strategist | gpt-4o-mini | bd_agents.py |
| humint_analyst | HUMINT Analyst | gpt-4o | bd_agents.py |

### Native BD Agents (BDAgent subclasses)

| Agent | Purpose | File |
|-------|---------|------|
| ProgramIntelAgent | Program intelligence gathering | program_intel_agent.py |
| CompanyResearchAgent | Company research and analysis | company_research_agent.py |
| ContactFinderAgent | Contact discovery | contact_finder_agent.py |
| BDStrategyAgent | BD strategy formulation | bd_strategy_agent.py |
| ContactClassifierAgent | 6-tier contact classification | contact_classifier_agent.py |
| ScraperMonitorAgent | Scraper monitoring | scraper_monitor_agent.py |
| QualityAssuranceAgent | QA validation | quality_assurance_agent.py |
| AnalyticsAgent | Analytics generation | analytics_agent.py |
| MorningBriefingAgent | Daily briefing generation | autonomous/ |
| ContactEnrichmentAgent | Contact data enrichment | autonomous/ |

### CrewAI Crews
- `create_bd_research_crew()` — Full BD research pipeline
- `create_contact_outreach_crew()` — Contact outreach planning
- `create_weekly_intel_crew()` — Weekly intelligence generation

### LLM Models Used

| Model | Where Used | Purpose |
|-------|-----------|---------|
| `claude-sonnet-4-20250514` | config/settings.py default, base_agent, pipeline, automation | Primary LLM |
| `claude-3-haiku-20240307` | LightRAG graph_rag.py | Lightweight graph queries |
| `gpt-4o` | CrewAI agents (bd_agents.py) | Agent operations |
| `gpt-4o-mini` | CrewAI outreach agent, LightRAG, mem0, api.py chat | Cost-efficient operations |
| `text-embedding-3-small` | All embedding operations | Primary embedding model |

### Embedding Configuration
- **Model**: `text-embedding-3-small` (OpenAI)
- **Dimensions**: 1536
- **Distance**: Cosine
- **Used in**: vector_store.py, unified_endpoints.py, hybrid_endpoints.py, alerts.py, domain_embedder.py, mem0_manager.py
- **Resilience**: `config/resilience.py` provides `with_embedding_retry` decorator

### MCP Servers (6 configured in `.mcp.json`)

| Server | Type | Purpose |
|--------|------|---------|
| bd-knowledge | Local Node.js | BD knowledge search/query tools |
| n8n | npx | N8N workflow automation |
| notion | npx | Notion database integration |
| notion-remote | Hosted | Remote Notion MCP |
| apify | npx | Job scraping tools |
| mapify | Local Node.js | Mind map generation |

### MCP API (FastMCP)
- `Engine8_Knowledge/mcp/mcp_server.py` — FastMCP Python server
- 5 API endpoints: /mcp/health, /mcp/tools, /mcp/config, /mcp/test-tool, /mcp/stats
- Phase 45A adds 10 more endpoints at /api/mcp/*

---

## 6. ENTITY TYPES (48 Total)

### Core Domain Entities (5)

#### Contact
- **Defined**: `models/contacts.py`
- **Fields**: 20+ (first_name, last_name, job_title, company, email, phone, linkedin_url, city, state, program, hierarchy_tier, bd_priority, location_hub, functional_areas)
- **Enums**: HierarchyTier (6 levels), BDPriority (4 levels), DCGSProgram (9 programs), LocationHub (7 hubs)
- **Storage**: Qdrant contacts (7,337), SQLite candidates (426,565), Neo4j Person
- **Relationships**: → Program, Activity, Job, PrimeContractor

#### FederalProgram
- **Defined**: `models/programs.py`
- **Fields**: 18+ (program_name, acronym, agency_owner, prime_contractor, known_subcontractors, contract_value, contract_vehicle, pop_start/end, key_locations, clearance_requirements, typical_roles, keywords, pain_points)
- **Enums**: PTSInvolvement (4), PriorityLevel (4)
- **Storage**: Qdrant programs (401), SQLite programs (4), CSV (388), Neo4j Program
- **Relationships**: → Contact, Job, PrimeContractor, Location

#### ScrapedJob
- **Defined**: `models/jobs.py`
- **Fields**: 18+ (title, company, location, url, description, detected_clearance, scraped_at, status, mapped_program, bd_score, match_confidence, match_type, match_signals, technologies, certifications_required)
- **Enum**: JobStatus (6 states: raw_import → enriched → validated)
- **Storage**: Qdrant jobs (~968), SQLite jobs (135), Neo4j Job
- **Relationships**: → Program (mapped), Contact (recruiter), Location

#### Activity
- **Defined**: `models/activities.py`
- **Fields**: 9+ (contact_name, contact_id, activity_type, summary, outcome, author, program, follow_up_date)
- **Enum**: ActivityType (8 types: CALL, EMAIL, LINKEDIN, MEETING, NOTE, HUMINT, SCRAPE, ENRICHMENT)
- **Storage**: Qdrant activities (500), SQLite activities (404,715)
- **Relationships**: → Contact, Program

#### Document
- **Defined**: `models/base.py` (BaseDocument) + Qdrant payload
- **Fields**: 12+ (doc_id, filename, filepath, doc_type, title, summary, content, chunk_index, total_chunks, tags)
- **Storage**: Qdrant documents (205)
- **Relationships**: → Program, PrimeContractor

### Business Entities (5)

#### PrimeContractor
- **Defined**: SQLite schema (`database_schema.py`)
- **Fields**: 22 (name, normalized_name, aliases, cage_code, duns_number, website, headquarters, employee_count, annual_revenue, naics_codes, contract_vehicles, total_jobs, total_placements, total_revenue, relationship_status)
- **Storage**: SQLite prime_contractors (41), Qdrant primes, Neo4j Company
- **Relationships**: → Program, Contact, Job, PastPerformance

#### PastPerformance
- **Defined**: SQLite schema
- **Fields**: 28 (prime_contractor_name, program_name, total_jobs, open/closed/filled/lost_jobs, total_placements, total_revenue, avg_bill_rate, avg_pay_rate, avg_margin, fill_rate, performance_score)
- **Storage**: SQLite past_performance (492)
- **Relationships**: → PrimeContractor, Program

#### Placement
- **Defined**: SQLite schema + `src/revenue/revenue_tracker.py`
- **Fields**: 22 (bullhorn_placement_id, job_id, candidate_id, placement_date, start/end_date, pay_rate, bill_rate, salary, commission, duration_days)
- **Storage**: SQLite placements (616)
- **Relationships**: → Job, Candidate, PrimeContractor, Program

#### FederalContract
- **Storage**: Qdrant federal_contracts, Neo4j Contract
- **Fields**: 20+ (award_id, title, agency, contractor, contract_vehicle, value, naics, award_date, pop_start/end, place_of_performance)
- **Relationships**: → Program, PrimeContractor, Agency

#### ContractOpportunity
- **Storage**: Qdrant opportunities
- **Fields**: 12+ (notice_id, title, type, agency, response_deadline, naics, estimated_value)
- **Relationships**: → Program, Agency

### Knowledge Graph Entities (4)

#### Entity (Graph Node)
- **Defined**: `Engine8_Knowledge/graph/bd_knowledge_graph.py`
- **Fields**: 5 (id, type, name, properties, created_at)
- **Node Types**: Contractor, Program, Contact, Job, Skill, Location, Meeting, Placement
- **Storage**: SQLite bd_graph.db entities (2,166)

#### Relationship (Graph Edge)
- **Fields**: 8 (id, type, from_entity_id, to_entity_id, properties, confidence, source, created_at)
- **38 Edge Types**: PRIMES_ON, SUBS_TO, COMPETES_WITH, PARTNERS_WITH, WORKS_ON, WORKS_FOR, MANAGES, KNOWS, DECISION_MAKER_FOR, HAS_OPENING, REQUIRES, PLACED_BY_PTS, etc.
- **Storage**: SQLite bd_graph.db relationships (938)

#### TemporalEntity
- **Defined**: `src/knowledge/temporal_kg.py`
- **Fields**: 10 (id, entity_type, name, aliases, properties, first_seen, last_seen, confidence, source_episodes, embedding)
- **Types**: PERSON, ORGANIZATION, PROGRAM, LOCATION, ROLE, SKILL, CONTRACT

#### TemporalFact
- **Fields**: 10 (subject_id, predicate, object_id, valid_from, valid_to, confidence, source_episode_id)
- **18 Edge Types**: WORKS_AT, MANAGES, PRIME_ON, SUB_ON, REPORTS_TO, HIRING, TEAMING_WITH, etc.

### Agent Output Models (12)
ProgramIntelligence, ContactProfile, CompetitiveReport, OutreachPlan, HUMINTBrief, BDResearchBundle, WeeklyIntelBundle, ResearchRequest, OutreachRequest, WeeklyIntelRequest, TaskResponse, TaskStatus

### Revenue/Deal Models (7)
ScoredOpportunity, DimensionScore, PipelineReview, Deal, Placement, RevenueRecord, RevenueSummary, MarginAnalysis, ConcentrationRisk

### Governance Models (5)
DataContract, QualityTerm, ContractBreach, ContractCheckResult, PastPerformanceEntry, RelevanceScore, CPARSMetrics, PerformanceMatrix

### Operational Models (10+)
BullhornNote, Memory, Interaction, Episode, CollectionHealth, DataQualityScore, QualityReport, PlaybookData, ScoringResult, PipelineConfig

---

## 7. INTEGRATION MAP

### External APIs Called

| Service | URL/Endpoint | Purpose |
|---------|-------------|---------|
| Anthropic Claude | `anthropic` SDK | LLM operations (job extraction, playbooks, chat, agents) |
| OpenAI | `openai` SDK | Embeddings (text-embedding-3-small) |
| Qdrant | `http://localhost:6333` | Vector database |
| Notion | `notion-client` SDK | Database sync (5+ databases) |
| Apify | `apify` API | Job scraping |
| N8N | `N8N_API_URL` | Workflow orchestration |
| Redis | `redis://localhost:6379` | Caching, event bus |
| Neo4j | `bolt://localhost:7687` | Graph database |
| Firecrawl | `firecrawl-py` SDK | Web scraping |
| Crawl4AI | `crawl4ai` | AI-native scraping |
| SAM.gov | Federal contract search | Contract awards lookup |

### Inter-Service Communication

| Service | Port | Protocol |
|---------|------|----------|
| Knowledge API | 8100 | HTTP/REST + WebSocket |
| Dashboard (Vite) | 5173 (dev) / 3000 (prod) | HTTP |
| Qdrant | 6333/6334 | HTTP + gRPC |
| Neo4j | 7474/7687 | HTTP + Bolt |
| Redis | 6379 | TCP |

### Notion Databases Connected

| Database | ID | Purpose |
|----------|-----|---------|
| DCGS Contacts | 2ccdef65-baa5-8087-a53b-000ba596128e | Contact management |
| GDIT Jobs | 2563119e7914442cbe0fb86904a957a1 | Job tracking |
| Program Mapping | f57792c1-605b-424c-8830-23ab41c47137 | Program-job links |
| Federal Programs | 06cd9b22-5d6b-4d37-b0d3-ba99da4971fa | Program database |
| BD Opportunities | 2bcdef65-baa5-80ed-bd95-000b2f898e17 | Opportunity tracking |

### N8N Webhooks
- `n8n_api_url` configured in .env
- Dify bridge triggers N8N workflows: `scrape-jobs`, `hot-lead`, `weekly-report`
- Workflow definitions in `n8n/` directory

### Dify Integration (3 bridges)
- `DifyQdrantBridge` — Search 8,447+ vectors from Dify
- `DifyCrewAIBridge` — Invoke BD agents from Dify apps
- `DifyN8NBridge` — Trigger n8n workflows from Dify
- 6 pre-built app templates (Research Chat, Call Prep, Pipeline Controller, Outreach Drafter, Program Analyzer, Competitor Intel)
- 34 external tools configured

---

## 8. DEPENDENCY LIST (requirements.txt)

### Core
- python-dotenv>=1.0.0, requests>=2.31.0, pydantic>=2.6.0, pydantic-settings>=2.1.0

### AI/LLM
- anthropic>=0.18.0, openai>=1.12.0

### Data Processing
- pandas>=2.0.0, numpy>=1.24.0

### Vector DB & Embeddings
- qdrant-client>=1.7.0, sentence-transformers>=2.2.0, tiktoken>=0.5.0, scipy>=1.11.0

### RAG Framework
- llama-index>=0.10.0, llama-index-vector-stores-qdrant, llama-index-llms-anthropic, llama-index-embeddings-huggingface

### API Server
- fastapi>=0.109.0, uvicorn>=0.27.0, httpx>=0.25.0

### Multi-Agent
- crewai>=0.30.0, langgraph>=0.4.0, langgraph-checkpoint-sqlite>=1.0.0

### Knowledge Graph
- lightrag-hku>=0.1.0

### Memory
- mem0ai>=0.1.0

### Retrieval
- rank-bm25>=0.2.2

### Caching
- redis>=5.0.0

### ML
- xgboost>=2.0.0, shap>=0.45.0, transformers>=4.35.0

### Scraping
- beautifulsoup4>=4.12.0, lxml>=4.9.0, firecrawl-py>=0.0.1, crawl4ai>=0.4.0

### MCP
- fastmcp>=2.0.0

### Monitoring
- prometheus-client>=0.20.0, psutil>=5.9.0, structlog>=24.1.0, tenacity>=8.2.0

### Real-Time
- websockets>=12.0, python-ulid>=3.0.0, fakeredis>=2.21.0, aiosqlite>=0.19.0

### Evaluation
- ragas>=0.1.0, datasets>=2.16.0

### Document Processing
- docling>=0.1.0, python-magic-bin>=0.4.14, watchdog>=3.0.0

### Notion
- notion-client>=2.2.0

### Database
- psycopg2-binary>=2.9.0

### Testing
- pytest>=7.4.0, pytest-cov>=4.1.0, pytest-asyncio>=0.23.0

### CLI
- click>=8.1.0, tqdm>=4.65.0

### Other
- jsonschema>=4.17.0, slowapi>=0.1.9

---

## 9. KNOWN ISSUES

### Data Duplication
- `bullhorn_master.db` exists at BOTH `Engine7_BullhornETL/data/` AND `data/` (292 MB x2 = 584 MB wasted)
- `bd_graph.db` exists at BOTH `Engine8_Knowledge/data/` AND `data/`
- `memories.db` and `page_index.db` also duplicated

### Qdrant Version Mismatch
- Client: qdrant-client>=1.7.0 (installed 1.14.3)
- Server: 1.16.3
- Causes pydantic validation errors with local file stores (must use URL connection)

### Empty Database Tables
- 5 tables in bullhorn_master.db have 0 rows (candidate_prime_history, job_prime_mapping, job_program_mapping, data_quality_log, processing_stats)
- LangGraph checkpoints_meta.db is completely empty

### API Sprawl
- 858 route definitions across 40+ API files
- Many phase routers (7 through 45A) may have dead/unused endpoints
- No centralized API versioning strategy

### Missing Features
- Engine 6 (QA) is incomplete — feedback loop not implemented
- Full pipeline orchestration not wired end-to-end
- Neo4j graph (Phase 21A) appears to be scaffolded but sparsely populated
- Multi-tenant auth (Phase 37A) not enforced

### Configuration Scattered
- Multiple .env files (root, dashboard, auto-claude, apps_backend)
- Settings spread across config/settings.py, per-engine configs, hardcoded values

### Security
- No authentication on API endpoints (development mode)
- API keys stored in .env files (properly gitignored)
- No rate limiting enforced (slowapi imported but not widely applied)

---

## 10. MIGRATION-CRITICAL FINDINGS

### Data That MUST Be Preserved

| Data | Records | Size | Priority |
|------|---------|------|----------|
| Bullhorn candidates | 426,565 | ~200 MB | CRITICAL |
| Bullhorn activities | 404,715 | ~50 MB | CRITICAL |
| Bullhorn call_notes | 50,710 | ~30 MB | HIGH |
| Contact scores | 9,837 | <1 MB | HIGH |
| Past performance | 492 | <1 MB | CRITICAL |
| Placements | 616 | <1 MB | CRITICAL |
| Prime contractors | 41 | <1 MB | CRITICAL |
| Knowledge graph entities | 2,166 | <1 MB | HIGH |
| Knowledge graph relationships | 938 | <1 MB | HIGH |
| Qdrant contacts | 7,337 vectors | ~50 MB | CRITICAL (re-embed with Voyage 4) |
| Qdrant programs | 401 vectors | <5 MB | HIGH (re-embed) |
| Qdrant documents | 205 vectors | <5 MB | MEDIUM (re-embed) |
| Federal Programs CSV | 388 rows | 2 MB | CRITICAL |
| Scraper past_perf DB | 62K+ rows | 22 MB | HIGH |

### Schemas Needing Decomposition

- **candidates table** (29 columns) — Split into Contact + Address + Employment + Metadata
- **jobs table** (29 columns) — Split into Job + Location + Clearance + Metadata
- **past_performance table** (28 columns) — Split into Performance + Metrics + Timeline
- **placements table** (22 columns) — Split into Placement + Financials + Timeline
- **prime_contractors table** (22 columns) — Split into Company + Financials + Engagement
- **call_notes table** (20 columns) — Split into Note + Context + Sentiment

### Embedding Dimension Migration
- **Current**: text-embedding-3-small, 1536 dimensions
- **Target**: Voyage 4, likely 1024 or 2048 dimensions
- **Impact**: ALL 8,447+ vectors must be re-embedded
- **Collections to re-embed**: contacts, programs, documents, activities, jobs, bullhorn_notes, federal_contracts, intelligence_reports, opportunities
- **Migration order**: Programs first (smallest, validates pipeline), then contacts, then jobs, then bulk notes

### Entity Type Mapping (Current → Target 12-14 Types)

| Current Entity | Target Entity | Notes |
|----------------|---------------|-------|
| Contact/Candidate | **Person** | Merge SQLite candidates + Qdrant contacts |
| FederalProgram | **Program** | Merge CSV + SQLite + Qdrant |
| PrimeContractor | **Organization** | Enrich with Neo4j Company data |
| ScrapedJob | **JobPosting** | Merge Bullhorn + scraper jobs |
| Placement | **Placement** | Keep as-is, add relationships |
| Activity/CallNote | **Interaction** | Merge activities + call_notes + bullhorn_notes |
| Document | **Document** | Re-embed with Voyage 4 |
| FederalContract | **Contract** | Merge with ContractOpportunity |
| PastPerformance | **PerformanceRecord** | Denormalize from current flat table |
| Entity (graph) | Decompose into proper types | 2,166 nodes → proper entity types |
| Memory | **AgentMemory** | New entity type for agent state |
| Location | **Location** | Extract from multiple sources |
| Skill | **Capability** | Extract from jobs/contacts |
| Opportunity | **Opportunity** | BD pipeline tracking |

### Integration Dependencies Affecting Migration Order

1. **Qdrant → PostgreSQL/Supabase**: Must migrate vector storage before API endpoints work
2. **SQLite → PostgreSQL**: Schema migration needed before ETL can write
3. **Embedding model swap**: Must happen before re-indexing
4. **API endpoint rewrite**: Current 858 routes need consolidation
5. **Dashboard API calls**: `hubApi.ts` and `useAppData.ts` call specific response formats
6. **N8N webhooks**: External workflow triggers must be updated
7. **Notion sync**: Database IDs are hardcoded, sync logic must be preserved
8. **MCP server**: Tools reference current API structure

### Docker Stack (Current)
- qdrant:latest → Will be replaced by PostgreSQL pgvector or Supabase
- neo4j:5.26.0 → Kept for graph queries or replaced by Neo4j Aura
- redis:7-alpine → Keep for caching/events
- hub_api (FastAPI) → Rewrite with LangGraph 1.0 orchestration
- dashboard (Nginx) → Keep React frontend, update API calls
