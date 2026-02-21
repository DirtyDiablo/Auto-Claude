# PTS BD Platform — Architecture State
## Last Updated: February 7, 2026 (Post-V4 Phase 4D Completion)

---

## Platform Overview

Prime Technical Services (PTS) BD Intelligence Platform is a hub-and-spoke architecture across 3 projects, powered by a unified Qdrant vector database (1.4M+ vectors), 5 CrewAI agents with structured outputs, dual-memory architecture (Mem0 vector + Graphiti temporal graph on Neo4j), and a React 19 dashboard frontend.

**Primary Objective**: Transform manual BD analysis (8-15 hours) into AI-powered sub-10-minute workflows for identifying federal defense staffing opportunities, building contact intelligence, and generating personalized outreach.

**Target Market**: Thousands of federal defense contracts matching: subcontracting staffing firms, $100M+ value or 100+ subs, clearance required, not assigned to existing PTS account managers

---

## Hub-and-Spoke Architecture

```
                    ┌─────────────────────────────────┐
                    │   BD-Automation-Engine (HUB)    │
                    │   Port: 8100                     │
                    │   FastAPI + React Dashboard      │
                    │   CrewAI Agents + Mem0 + Graphiti│
                    │   Qdrant (1.4M vectors)          │
                    │   Neo4j (Graphiti KG)            │
                    └──────────┬──────────┬───────────┘
                               │          │
              ┌────────────────┘          └────────────────┐
              ▼                                            ▼
┌──────────────────────────┐          ┌──────────────────────────────┐
│   Data-Scraper           │          │   N8N-Builder                │
│   Port: 8200             │          │   (Workflow & Intel Engine)  │
│   Apify job scrapers     │          │   Port: 8300                 │
│   Federal API clients    │          │   LangGraph workflows        │
│   Bullhorn CRM sync      │          │   Tango/MakeGov discovery    │
│   Job enrichment pipeline│          │   Outreach sequence engine   │
│   Competitor intelligence│          │   Contact processing         │
└──────────────────────────┘          └──────────────────────────────┘
```

### Terminal A — BD-Automation-Engine (Hub)
- **Path**: `C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine\`
- **Role**: Central API server, dashboard frontend, AI agents, vector search, memory systems
- **Port**: 8100 (FastAPI API), 5173 (Vite dev server)
- **Key Technologies**: FastAPI, React 19, Vite 7, shadcn/ui, TanStack Query, CrewAI 1.9.3, Qdrant, Neo4j, Mem0, Graphiti, cross-encoder reranking (ms-marco-MiniLM-L-6-v2)
- **Engines**: 8 engines (Engine1 through Engine8_Knowledge) covering scraping → standardization → mapping → scoring → outreach → QA → knowledge

### Terminal B — Data-Scraper
- **Path**: `C:\data-scraper\data-scraper\`
- **Role**: Job scraping from competitor portals, federal contract API integration, Bullhorn data processing
- **Port**: 8200 (FastAPI, if running)
- **Key Technologies**: Apify Puppeteer scrapers, httpx, pandas, Qdrant client
- **Scrapers**: Insight Global (reliable, last scrape Jan 26), Apex Systems (403 blocked), TEKsystems (configured, no data), CACI (configured, no data)

### Terminal C — N8N-Builder (Workflow & Intelligence Engine)
- **Path**: `C:\Auto-Claud\N8N-Builder\` ⚠️ Note: "Claud" not "Claude"
- **Role**: LangGraph workflows, Tango federal contract discovery, outreach sequence engine, contact processing
- **Port**: 8300 (FastAPI, if running)
- **Key Technologies**: LangGraph (12 modules), Tango/MakeGov API (unlimited key), LanceDB (partially migrated), SQLite outreach DB
- **NOTE**: n8n runtime dependency is REMOVED. All automation is Python-native. The project name "N8N-Builder" is legacy — actual capabilities are LangGraph workflows, Tango discovery, and contact/outreach processing.

---

## Data Infrastructure

### Qdrant Vector Database (localhost:6333)

| Collection | Vectors | Dimension | Key Payload Indexes | Purpose |
|---|---|---|---|---|
| documents | 499,750 | 1536 | source_project, intel_category, search_tags, priority, doc_type, program_name, date_indexed | BD documents, playbooks, reports, analysis |
| activities | 445,972 | 1536 | source_project, activity_type, contact_name, company, date, program | Bullhorn activity records, call notes, emails |
| contacts | 211,267 | 1536 | name, company, title, program, tier, priority, location, email | Contact profiles from ZoomInfo, LinkedIn, Bullhorn |
| federal_contracts | 107,902 | 1536 | agency, contractor, naics, value, status, award_date | USASpending, FPDS, SAM.gov contract data |
| programs | 68,103 | 1536 | program_name, agency, prime, pts_involvement, priority, contract_value | Federal program intelligence |
| bullhorn_notes | 50,710 | 1536 | contact, company, author, date, type, programs_mentioned | Extracted Bullhorn CRM notes (2,687 source notes) |
| jobs | 15,997 | 1536 | company, title, location, clearance, program_match, source_portal, scraped_date | Scraped competitor jobs + GDIT internal |
| intelligence_reports | 2,229 | 1536 | report_type, program, date, confidence | BD intelligence, HUMINT, competitive analysis |
| bd_memories | 2 | 1536 | user_id, agent_id, memory_type, timestamp | Mem0 agent cross-session memory |

**Total**: ~1,401,932 vectors
**Embedding Model**: OpenAI text-embedding-3-small (1536 dimensions) — consistent across ALL collections
**Quantization**: INT8 scalar (75% RAM reduction, <1% accuracy loss)
**HNSW**: m=16, ef_construct=100

### Neo4j Graph Database (bolt://localhost:7687)

- **Nodes**: ~7 (growing as Graphiti ingests more episodes)
- **Relationships**: ~4 types
- **Purpose**: Graphiti temporal knowledge graph — tracks entity relationships over time with bi-temporal edges (t_valid, t_invalid)
- **Auth**: neo4j / password

### Mem0 Memory System

- **Vector Backend**: Qdrant `bd_memories` collection
- **Graph Backend**: Neo4j (same instance as Graphiti)
- **Current Memories**: 2 (from end-to-end agent test)
- **Growth**: Automatically stores when CrewAI agents complete tasks
- **Use Case**: Cross-session agent memory — agents remember past research and interactions

---

## AI Agent System — CrewAI 1.9.3

### 5 Specialized Agents

| Agent | LLM | Tools | Structured Output | Purpose |
|---|---|---|---|---|
| program_researcher | GPT-4o | programs, contracts, documents, graphiti | ProgramIntelligence | Deep program research |
| contact_enricher | GPT-4o-mini | contacts, bullhorn_notes, mem0, graphiti | ContactProfile | Contact intelligence |
| competitive_analyst | GPT-4o | jobs, documents, programs | CompetitiveReport | Competitive landscape |
| outreach_composer | GPT-4o | contacts, programs, jobs, mem0 | OutreachPlan | Personalized outreach |
| humint_analyst | GPT-4o | bullhorn_notes, contacts, mem0, graphiti | HUMINTBrief | Intelligence synthesis |

### Agent API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| /agents/research | POST | Trigger BD Research Crew |
| /agents/outreach | POST | Generate outreach for contact |
| /agents/weekly-intel | POST | Weekly intelligence briefing |
| /agents/tasks | GET | List all agent task history |
| /agents/status/{task_id} | GET | Get task status |

### Search Architecture (4-Layer Pipeline)

1. **Query Router**: Classifies intent → selects target Qdrant collections
2. **Hybrid Retrieval**: Dense vectors (cosine) + Sparse BM25 (keywords) in parallel
3. **Cross-Encoder Reranking**: ms-marco-MiniLM-L-6-v2 — 20-35% accuracy improvement
4. **LLM Synthesis**: Natural language answer with inline citations

| Search Endpoint | Method | Purpose |
|---|---|---|
| /search | POST | Vector search with collection + payload filters |
| /ask/smart | POST | Full AI-synthesized answer with citations |
| /collections/{name}/search | POST | Collection-specific search |

---

## External Integrations

| Service | Status | Purpose | Terminal |
|---|---|---|---|
| Qdrant | ✅ Running (localhost:6333) | Vector database (1.4M vectors) | A (primary), B+C (clients) |
| Neo4j | ✅ Running (localhost:7687) | Graphiti temporal KG | A |
| OpenAI API | ✅ Configured | Embeddings + Agent LLMs | A |
| Anthropic API | ✅ Configured | RAG synthesis (Claude Sonnet) | A |
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
