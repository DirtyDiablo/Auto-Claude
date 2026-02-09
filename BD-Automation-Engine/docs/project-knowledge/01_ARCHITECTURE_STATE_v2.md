# PTS BD Platform — Architecture State
## Last Updated: February 8, 2026 (Post-Terminal Audit Verification)

---

## Platform Overview

Prime Technical Services (PTS) BD Intelligence Platform is a hub-and-spoke architecture across 3 projects, powered by a unified Qdrant vector database (1.4M+ vectors), 13 CrewAI agents in 6 crews with structured outputs, dual-memory architecture (Mem0 vector + Graphiti temporal graph on Neo4j), and a React 19 dashboard frontend with 27 existing pages.

**Primary Objective**: Transform manual BD analysis (8-15 hours) into AI-powered sub-10-minute workflows for identifying federal defense staffing opportunities, building contact intelligence, and generating personalized outreach.

**Target Market**: $950M DCGS portfolio (AF DCGS ~$500M BAE/GDIT, Army DCGS-A ~$300M GDIT, Navy DCGS-N ~$150M GDIT)

---

## Hub-and-Spoke Architecture

```
                    ┌─────────────────────────────────┐
                    │   BD-Automation-Engine (HUB)    │
                    │   Port: 8100 (API), 5173 (Vite) │
                    │   FastAPI + React Dashboard      │
                    │   13 CrewAI Agents (6 crews)     │
                    │   Qdrant (1.4M vectors, 12 coll) │
                    │   Neo4j (12 nodes, 9 rels)       │
                    │   Mem0 (Qdrant+Neo4j backend)    │
                    └──────────┬──────────┬───────────┘
                               │          │
              ┌────────────────┘          └────────────────┐
              ▼                                            ▼
┌──────────────────────────┐          ┌──────────────────────────────┐
│   Data-Scraper           │          │   N8N-Builder                │
│   Port: 8200             │          │   (Workflow & Intel Engine)  │
│   Apify job scrapers     │          │   Port: 8300                 │
│   Federal API clients    │          │   LangGraph workflows (12)   │
│   Bullhorn CRM sync      │          │   Tango/MakeGov discovery    │
│   Job enrichment pipeline│          │   Outreach sequence engine   │
│   Competitor intelligence│          │   Contact processing         │
└──────────────────────────┘          └──────────────────────────────┘
```

### Terminal A — BD-Automation-Engine (Hub)
- **Path**: `C:\Auto-Claud\Auto-Claude\BD-Automation-Engine\`
- **Role**: Central API server, dashboard frontend, AI agents, vector search, memory systems
- **Port**: 8100 (FastAPI API), 5173 (Vite dev server)
- **Branch**: `claude/setup-auto-claude-IrK21`
- **Last Commit**: 6695fe30 "fix: Smart Query searches real collections with rich text extraction"
- **Disk**: 3.5 GB
- **Key Technologies**: FastAPI, React 19, Vite 7, shadcn/ui, TanStack Query, CrewAI 1.9.3, Qdrant, Neo4j, Mem0, Graphiti, cross-encoder reranking (ms-marco-MiniLM-L-6-v2)
- **Engines**: 8 engines (Engine1 through Engine8_Knowledge) covering scraping → standardization → mapping → scoring → outreach → QA → knowledge

### Terminal B — Data-Scraper
- **Path**: `C:\Auto-Claud\data-scraper\`
- **Role**: Job scraping from competitor portals, federal contract API integration, Bullhorn data processing
- **Port**: 8200 (FastAPI, if running)
- **Branch**: `master`
- **Last Commit**: e6769e9 "feat: Phase 4C - USASpending federal contracts populator for Qdrant" (Feb 7)
- **Disk**: 4.9 GB
- **Files**: 1,085 total (178 Python), 91 scraping files
- **Key Technologies**: Apify Puppeteer scrapers, httpx, pandas, Qdrant client, 234 pip packages
- **Scrapers**: Insight Global (reliable, 207 jobs Jan 26), Apex Systems (55 jobs Jan 26, may be blocked), TEKsystems (configured, no data), CACI (configured, no data)
- **Federal APIs**: SAM.gov (key set), USASpending (no key needed), Tango/MakeGov (unlimited key), FPDS (built), Firecrawl (key set)
- **n8n dependency**: ZERO — 100% pure Python, no removal needed

### Terminal C — N8N-Builder (Workflow & Intelligence Engine)
- **Path**: `C:\Auto-Claud\N8N-Builder\` ⚠️ Note: "Claud" not "Claude"
- **Role**: LangGraph workflows, Tango federal contract discovery, outreach sequence engine, contact processing
- **Port**: 8300 (FastAPI, if running)
- **Branch**: `master`
- **Last Commit**: 3a322dd "feat: Add outreach sequence engine and intelligence reports ingestion" (Feb 7)
- **Disk**: 1.2 GB
- **Files**: 2,770 total (195 Python), 41 scraping files
- **Key Technologies**: LangGraph (12 modules), Tango/MakeGov API (unlimited key), SQLite outreach DB
- **n8n dependency**: 3 Python files need replacement (client/n8n_client.py, api/workflow_api.py, cleanup_workflows.py), 29 workflow JSONs to archive
- **Missing Keys**: ANTHROPIC_API_KEY empty, NOTION_API_KEY empty
- **Virtual env**: NONE (all packages global on Python 3.12)

---

## Data Infrastructure

### Qdrant Vector Database (localhost:6333)

| Collection | Vectors | Dimension | Key Payload Indexes | Quantization | Purpose |
|---|---|---|---|---|---|
| documents | 499,750 | 1536 | 7 (source_project, intel_category, search_tags, priority, doc_type, program_name, date_indexed) | INT8 Scalar | BD documents, playbooks, reports |
| activities | 445,972 | 1536 | 6 (source_project, activity_type, contact_name, company, date, program) | INT8 Scalar | Bullhorn activity records |
| contacts | 211,267 | 1536 | 7 (name, company, title, program, tier, priority, location) | INT8 Scalar | Contact profiles |
| federal_contracts | 107,902 | 1536 | 6 (agency, contractor, naics, value, status, award_date) | none | USASpending/FPDS/SAM data |
| programs | 68,103 | 1536 | 6 (program_name, agency, prime, pts_involvement, priority, contract_value) | none | Federal program intelligence |
| bullhorn_notes | 50,710 | 1536 | 6 (contact, company, author, date, type, programs_mentioned) | — | Extracted CRM notes (2,687 source) |
| jobs | 15,997 | 1536 | 6 (company, title, location, clearance, program_match, source_portal) | none | Scraped + GDIT internal jobs |
| intelligence_reports | 2,229 | 1536 | 0 | none | BD intel, HUMINT, competitive |
| star_charts | 5 | 1536 | — | — | Star chart visualizations |
| bd_memories | 2 | 1536 | 4 | — | Mem0 agent memory |
| mem0migrations | 1 | 1536 | 4 | — | Mem0 migration tracking |
| mem0 | 0 | 1536 | 4 | — | Mem0 (initialized, empty) |
| opportunities | 0 | — | 0 | — | Future opportunity tracking |

**Total**: ~1,401,933 vectors
**Embedding Model**: OpenAI text-embedding-3-small (1536 dimensions) — consistent across ALL collections
**Quantization**: INT8 scalar on top 3 collections (75% RAM reduction, <1% accuracy loss)
**HNSW**: m=16, ef_construct=100

### Neo4j Graph Database (bolt://localhost:7687)

- **Nodes**: 12 (growing as Graphiti ingests more episodes)
- **Relationships**: 9
- **Labels**: 10
- **Relationship Types**: 14
- **Purpose**: Graphiti temporal knowledge graph — tracks entity relationships over time with bi-temporal edges (t_valid, t_invalid)
- **Auth**: neo4j / password

### Mem0 Memory System

- **Vector Backend**: Qdrant `bd_memories` collection (2 memories)
- **Graph Backend**: Neo4j (same instance as Graphiti)
- **Additional**: mem0 collection (initialized, empty), mem0migrations (1 record)
- **Growth**: Automatically stores when CrewAI agents complete tasks
- **Use Case**: Cross-session agent memory

---

## AI Agent System — CrewAI 1.9.3

### 13 Agents in 6 Crews

**8 BDAgent Subclasses** (specialized BD workflow agents):
- ResearchAgent, IntelligenceAgent, OutreachAgent, AnalysisAgent
- TargetingAgent, EnrichmentAgent, ValidationAgent, CoordinatorAgent

**5 Raw CrewAI Agents** (with structured Pydantic outputs):

| Agent | LLM | Tools | Structured Output | Purpose |
|---|---|---|---|---|
| program_researcher | GPT-4o | programs, contracts, documents, graphiti | ProgramIntelligence | Deep program research |
| contact_enricher | GPT-4o-mini | contacts, bullhorn_notes, mem0, graphiti | ContactProfile | Contact intelligence |
| competitive_analyst | GPT-4o | jobs, documents, programs | CompetitiveReport | Competitive landscape |
| outreach_composer | GPT-4o | contacts, programs, jobs, mem0 | OutreachPlan | Personalized outreach |
| humint_analyst | GPT-4o | bullhorn_notes, contacts, mem0, graphiti | HUMINTBrief | Intelligence synthesis |

**6 Crews**: research_crew, intelligence_crew, outreach_crew, enrichment_crew, validation_crew, coordination_crew

### Agent API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| /agents/research | POST | Trigger BD Research Crew |
| /agents/outreach | POST | Generate outreach for contact |
| /agents/weekly-intel | POST | Weekly intelligence briefing |
| /agents/tasks | GET | List all agent task history |
| /agents/status/{task_id} | GET | Get task status |

### Hub API Router Categories (~140+ endpoints)

| Router | Prefix | Key Endpoints |
|---|---|---|
| search | /search | POST /search, POST /ask/smart, POST /collections/{name}/search |
| rag | /rag | RAG pipeline endpoints |
| graph | /bdgraph, /graphiti | POST /graphiti/ingest, POST /graphiti/search |
| memory | /memory | Mem0 operations |
| ingest | /ingest | POST /ingest/document, POST /documents/upload |
| agents | /agents | Agent triggers + task management |
| qa | /qa | Quality assurance endpoints |
| pipeline | /pipeline | Pipeline triggers |
| alerts | /alerts | Alert management |
| dashboard | /dashboard | GET /dashboard/stats, collection filters |
| dify | /dify | Dify integration |
| health | / | GET /health, GET /stats |

### Search Architecture (4-Layer Pipeline)

1. **Query Router**: Classifies intent → selects target Qdrant collections
2. **Hybrid Retrieval**: Dense vectors (cosine) + Sparse BM25 (keywords) in parallel
3. **Cross-Encoder Reranking**: ms-marco-MiniLM-L-6-v2 — 20-35% accuracy improvement
4. **LLM Synthesis**: Natural language answer with inline citations

---

## Dashboard Frontend State

### 27 Existing Pages (React 19 + Vite 7)

| Category | Pages |
|---|---|
| Core BD | ExecutiveSummary, JobIntelligence, JobsPipeline, Programs, Contacts, Contractors, Locations |
| Intelligence | BDEvents, Opportunities, EnrichmentDashboard, DailyPlaybook, PastPerformance, CallIntelligence, AccountTakeover |
| Visualization | MindMap, PrimeOrgChart, ContactOrgChartPage, KnowledgeGraph |
| Operations | QADashboard, PipelineStatus, DataQualityDashboard, PlacementsPage |
| Hub AI | SmartQuery, AgentPanel, MemoryContext, SystemHealth |
| Settings | Settings |

### Routing: State-based (NOT TanStack Router)
```typescript
// App.tsx uses useState<TabId> + switch statement
const [activeTab, setActiveTab] = useState<TabId>('executive');
```

### Vite Proxy: Per-route (NOT /api prefix)
```typescript
// vite.config.ts maps 17+ individual routes to :8100
'/health': { target: 'http://127.0.0.1:8100', changeOrigin: true },
'/stats': { target: 'http://127.0.0.1:8100', changeOrigin: true },
'/search': { target: 'http://127.0.0.1:8100', changeOrigin: true },
// ... etc (NO /api prefix rewriting)
```

### 63 npm Packages Installed (key ones)
React 19, Vite 7, TanStack Query/Router/Table, @tremor/react, @antv/g6, @cosmograph/react, reagraph, recharts, ai, @ai-sdk/openai, assistant-ui, @dnd-kit/core+sortable+utilities, cmdk, framer-motion, react-hook-form, zod, zustand, react-chrono, vis-timeline, lucide-react, 16 Radix packages, shadcn/ui components

### Key Source Files
- `src/services/hubApi.ts` — HubApiClient singleton (full API coverage)
- `src/hooks/useHubApi.ts` — 15+ React hooks for Hub API
- `src/hooks/useAppData.ts` — TanStack Query with Hub → local JSON fallback
- `src/components/Sidebar.tsx` — Collapsible nav, 27+ routes
- `src/components/CommandPalette.tsx` — Cmd+K global search
- `src/components/ThemeSwitcher.tsx` — Dark mode toggle

---

## External Integrations

| Service | Status | Purpose | Terminal |
|---|---|---|---|
| Qdrant | ✅ Running (localhost:6333) | Vector database (1.4M vectors) | A (primary), B+C (clients) |
| Neo4j | ✅ Running (localhost:7687) | Graphiti temporal KG | A |
| OpenAI API | ✅ Configured | Embeddings + Agent LLMs | A, B |
| Anthropic API | ✅ Configured (Terminal A) | RAG synthesis (Claude Sonnet) | A |
| Apify | ✅ Configured | Job scraping actors | B |
| Tango/MakeGov | ✅ Configured (unlimited) | Federal contract discovery | C |
| Notion (MCP) | ✅ Connected | DCGS Contacts, Jobs, Programs | A |
| Apollo.io | ⏳ Not configured | Contact discovery API | Future |
| Azure AD / O365 | ⏳ Not configured | Email automation | Future |
| Twilio | ⏳ Not configured | SMS outreach | Future |

---

## Notion Databases (MCP Access)

| Database | Collection ID | ~Records | Purpose |
|---|---|---|---|
| DCGS Contacts Full | 2ccdef65-baa5-8087-a53b-000ba596128e | 965 | Primary BD contacts |
| GDIT Other Contacts | 70ea1c94-211d-40e6-a994-e8d7c4807434 | 1,052 | Non-DCGS GDIT |
| GDIT Jobs | 2ccdef65-baa5-80b0-9a80-000bd2745f63 | 700 | Bullhorn openings |
| Program Mapping Hub | f57792c1-605b-424c-8830-23ab41c47137 | varies | Scraped jobs + BD scoring |
| Federal Programs | 06cd9b22-5d6b-4d37-b0d3-ba99da4971fa | 388 | Contract intelligence |
| Contractors | 3a259041-22bf-4262-a94a-7d33467a1752 | varies | Contractor profiles |
| Contract Vehicles | 0f09543e-9932-44f2-b0ab-7b4c070afb81 | varies | Vehicle/IDIQ tracking |
| Enrichment Runs Log | 20dca021-f026-42a5-aaf7-2b1c87c4a13d | varies | Processing audit trail |
