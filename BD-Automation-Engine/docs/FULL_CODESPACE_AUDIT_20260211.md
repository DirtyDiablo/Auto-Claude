# PTS BD Codespace — Full Audit Report

## Generated: 2026-02-11

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| **Total Files** | 4,221 (excluding .git, node_modules, __pycache__, dist) |
| **Total Python Scripts** | 1,190 |
| **Total TypeScript/TSX** | 888 (491 .ts + 397 .tsx) |
| **Total Data Files (CSV)** | 814 |
| **Total Documentation (MD)** | 523 |
| **Total JSON Configs/Data** | 460 |
| **Total Qdrant Vectors** | 1,420,232 across 12 collections |
| **Total Pip Packages** | 253 installed |
| **MCP Servers Configured** | 6 (bd-knowledge, n8n, notion, notion-remote, apify, mapify) |
| **AI Agents** | 15+ specialized BD agents |
| **Dashboard Pages** | 14 interactive pages |
| **Engine Count** | 8 engines + dashboard + orchestration layer |

### Key Findings

1. **Massive vector knowledge base**: 1.42M vectors across 12 Qdrant collections — contacts (211K), documents (500K), activities (446K), federal_contracts (108K), programs (68K)
2. **Full-stack operational**: Qdrant server running, Knowledge API healthy, 253 Python packages installed, Node.js v24.13.0
3. **Data-rich**: 814 CSV files + 306MB Bullhorn SQLite DB + 312MB document vector store + 75MB combined notes CSV
4. **Significant duplication**: Data files exist in 3+ locations (data/, engine_data/, Engine*/ directories) — consolidation recommended
5. **Dashboard fully built**: 14-page React/TypeScript dashboard with mind maps, knowledge graphs, call intelligence, smart query, and more
6. **OpenClaw integration planned**: Master architecture document ready, 5-phase implementation plan created 2026-02-10

---

## 2. Directory Structure Map

```
BD-Automation-Engine/                    (4,221 files)
├── .auto-claude/                        Auto Claude integration (specs, roadmap, insights)
│   ├── specs/001-program-mapping-engine-v2-0/
│   ├── roadmap/
│   ├── insights/
│   └── worktrees/terminal/datamapping/  Auto Claude worktree copy
├── .claude/                             Claude Code MCP config
├── Engine1_Scraper/        (24 files)   Apify job scraping configs
├── Engine2_ProgramMapping/ (41 files)   Job standardization + program matching
│   ├── scripts/                         pipeline.py, job_standardizer.py, program_mapper.py
│   └── data/                            Federal_Programs CSVs
├── Engine3_OrgChart/       (71 files)   Contact classification (6-tier hierarchy)
│   ├── scripts/                         contact_classifier.py, contact_lookup.py
│   └── data/Prime_Contacts/             30+ prime contractor contact CSVs
├── Engine4_Briefing/       (1 file)     BD briefing generation
├── Engine4_Playbook/       (4 files)    BD playbook generation
├── Engine5_Scoring/        (2 files)    BD priority scoring (0-100)
├── Engine6_QA/             (4 files)    Quality assurance & alerts
├── Engine7_BullhornETL/    (146 files)  CRM data extraction & analysis
│   ├── scripts/                         15+ ETL and analysis scripts
│   ├── data/                            bullhorn_master.db (306MB)
│   ├── colton_scurry_analysis/          Deep contact analysis
│   └── outputs/                         Notion exports, reports
├── Engine8_Knowledge/      (289 files)  AI Knowledge System (semantic search, RAG)
│   ├── agents/                          15+ AI agents (BD strategy, company research, etc.)
│   ├── scripts/                         30+ indexing, retrieval, memory scripts
│   ├── processors/                      Document processing (docling)
│   ├── retrieval/                       Ultra RAG, PageIndex
│   ├── bd_lightrag/                     Knowledge graph (LightRAG)
│   ├── ragflow/                         RAGflow integration
│   ├── data/qdrant/                     Vector DB storage
│   └── data/lightrag/                   Knowledge graph storage
├── dashboard/              (310 files)  React/TypeScript BD Intelligence Dashboard
│   ├── src/pages/                       14 dashboard pages
│   ├── src/components/                  UI components (mind map, hub, charts)
│   ├── src/hooks/                       10+ custom hooks
│   ├── src/services/                    API, enrichment, correlation services
│   ├── src/stores/                      Zustand state management
│   └── public/data/                     50+ JSON data feeds
├── data/                   (855 files)  Consolidated data repository
│   ├── from_data_scraper/               Imported from data-scraper project
│   ├── from_n8n_builder/               Imported from N8N-Builder project
│   ├── qdrant/                          Local Qdrant collection snapshots
│   └── bullhorn_master.db               CRM database copy
├── engine_data/            (146 files)  Engine-specific data exports
│   ├── Engine1_Scraper/                 Job scrape CSVs
│   ├── Engine2_ProgramMapping/          Federal programs, BD opportunities
│   └── Engine3_OrgChart/                Contact databases by prime
├── outputs/                (242 files)  Generated deliverables
│   ├── BD_Briefings/                    Call scripts, emails, playbooks, talking points
│   ├── coworker_takeover/               Contact & program handoff data
│   ├── enriched_spreadsheet/            Enriched job data
│   ├── notion/                          Notion CSV exports (14+ timestamped)
│   └── n8n/                             N8N webhook JSON outputs
├── docs/                   (115 files)  Documentation
│   ├── Claude Exports/                  23 Claude conversation exports
│   ├── Claude Skills/                   10 skill definition documents
│   ├── project-knowledge/               Architecture & reference docs
│   ├── bd-dashboard/                    Dashboard design docs
│   └── N8N-Builder.Capture-MCP-server/  MCP capture data (13 CSVs)
├── tests/                  (142 files)  Test suite
├── src/                    (148 files)  Source modules
│   ├── agents/                          Agent base classes
│   ├── langgraph/                       LangGraph workflow engine
│   ├── monitoring/                      Prometheus metrics, alerting
│   ├── streaming/                       WebSocket streaming API
│   └── memory/                          Memory system routes
├── scripts/                (27 files)   Utility scripts
├── services/               (21 files)   Integration services
├── mcp/                    (32 files)   MCP server implementations
│   ├── knowledge-mcp-server/            BD Knowledge MCP (Node.js)
│   └── mapify-mcp-server/               Mapify MCP integration
├── dify_integration/       (7 files)    Dify visual AI orchestration bridges
├── api/                    (2 files)    Unified API endpoints
├── config/                 (4 files)    Logging, environment configs
├── utils/                  (3 files)    Shared utilities
├── apify/                               Apify actor configs
├── scrapers/                            Web scraping modules
├── pipelines/                           Orchestration pipelines
├── external_apis/                       External API integrations (SAM, FPDS, Tango)
├── monitoring/                          Health check, metrics
├── validation/                          Data validation framework
├── n8n/                                 N8N workflow definitions
├── notion/                              Notion integration scripts
└── [Root-level files]                   PDFs (resumes), .docx reports, master guides
```

---

## 3. File Inventory & Classification

### By Category (adapted taxonomy)

| Category | Count | Key Files |
|----------|-------|-----------|
| **Data Files** (.csv, .xlsx, .json datasets, .db, .sqlite) | ~1,400 | 814 CSVs, 460 JSONs, 65 XLSX, 12 DBs, 22 SQLite |
| **Source Code** (.py) | 1,190 | Engine scripts, agents, API, tests |
| **Dashboard** (.ts, .tsx) | 888 | 491 TS + 397 TSX React components |
| **Documents & Deliverables** (.md) | 523 | Playbooks, briefings, architecture docs |
| **Configuration** (.json configs, .env, .yml) | ~100 | MCP configs, package.json, vite.config |
| **BD Intelligence** (playbooks, call sheets, scoring) | ~80 | outputs/BD_Briefings/*, bd_call_sheet*, bd_playbook* |
| **Contact Intelligence** (contact CSVs, org charts) | ~100 | Engine3_OrgChart/data/Prime_Contacts/, Bullhorn exports |
| **Resumes & Profiles** (.pdf) | ~15 | Root-level PDFs (Brooks_Price, Bryan_M, etc.) |
| **Visualizations** (.html) | 7 | Interactive dashboards |
| **Images** (.png, .svg) | ~31 | Dashboard assets |

---

## 4. File Type Distribution

| Extension | Count | Description |
|-----------|-------|-------------|
| .py | 1,190 | Python source code |
| .csv | 814 | Data files (contacts, programs, jobs, exports) |
| .md | 523 | Documentation, playbooks, architecture |
| .ts | 491 | TypeScript source |
| .json | 460 | Configuration, data feeds, API schemas |
| .tsx | 397 | React TypeScript components |
| .xlsx | 65 | Excel spreadsheets |
| .txt | 32 | Text files, logs |
| .XLS | 31 | Legacy Excel files |
| .png | 28 | Images |
| .yml | 26 | YAML configs |
| .yaml | 23 | YAML configs |
| .sqlite | 22 | SQLite databases (Qdrant storage) |
| .db | 12 | Database files |
| .js | 8 | JavaScript |
| .docx | 6 | Word documents |
| .html | 7 | Interactive HTML |
| .pdf | ~15 | PDFs (resumes, reports) |
| .css | 3 | Stylesheets |
| .svg | 3 | Vector graphics |
| .sh | 3 | Shell scripts |
| .ps1 | 2 | PowerShell scripts |

---

## 5. Skills Catalog

### Engine Skills (Python-based)

| Skill | Location | Trigger | Capabilities | Output |
|-------|----------|---------|-------------|--------|
| **Job Scraping** | Engine1_Scraper/ | Apify actor trigger | Scrape job postings from Insight Global, GDIT | CSV job listings |
| **Job Standardization** | Engine2/scripts/job_standardizer.py | Pipeline stage 1 | LLM-powered field extraction from raw jobs | Standardized job JSON |
| **Program Mapping** | Engine2/scripts/program_mapper.py | Pipeline stage 2 | Multi-signal matching: jobs → federal programs | Mapped jobs CSV |
| **Full Pipeline** | Engine2/scripts/pipeline.py | Manual or orchestrated | 7-stage pipeline: scrape → standardize → map → export | Notion CSV + n8n JSON |
| **Contact Classification** | Engine3/scripts/contact_classifier.py | On new contacts | 6-tier hierarchy classification | Classified contacts |
| **Contact Lookup** | Engine3/scripts/contact_lookup.py | On demand | Search contacts by criteria | Contact matches |
| **BD Briefing Generation** | Engine4_Briefing/scripts/briefing_generator.py | On demand | Generate call scripts, emails, playbooks, talking points | 4 output types per contact |
| **BD Playbook Generation** | Engine4_Playbook/scripts/bd_playbook_generator.py | On demand | Generate BD approach playbooks | Markdown playbook |
| **BD Scoring** | Engine5/scripts/bd_scoring.py | Pipeline stage | 0-100 scoring algorithm for BD opportunities | Scored opportunities |
| **QA Alerts** | Engine6/scripts/alerts.py | Continuous | Quality monitoring and alerting | Alert notifications |
| **QA Feedback** | Engine6/scripts/qa_feedback.py | Post-pipeline | Quality review and feedback collection | Review queue JSON |
| **Bullhorn ETL** | Engine7/scripts/bullhorn_etl.py | Scheduled/manual | Extract CRM data from Bullhorn SQLite | Structured datasets |
| **Prime Contact Builder** | Engine7/scripts/build_prime_contact_databases.py | On demand | Build contact databases per prime contractor | Per-prime CSVs |
| **Intelligence Report** | Engine7/scripts/bd_intelligence_report.py | On demand | Generate BD intelligence reports from CRM data | Intelligence reports |
| **Past Performance** | Engine7/scripts/past_performance_report.py | On demand | Generate past performance documentation | Performance reports |
| **Financial Analysis** | Engine7/scripts/financial_analysis.py | On demand | Analyze financial data from Bullhorn | Financial reports |
| **Semantic Search** | Engine8/scripts/vector_store.py | API endpoint | Semantic similarity search across collections | Search results JSON |
| **RAG Engine** | Engine8/scripts/rag_engine.py | API endpoint | Retrieval-Augmented Generation Q&A | Answer + sources |
| **Hybrid Retrieval** | Engine8/scripts/hybrid_retriever.py | API endpoint | BM25 + semantic + cross-encoder reranking | Ranked results |
| **Auto Tagger** | Engine8/scripts/auto_tagger.py | On indexing | Automatic tagging of indexed documents | Tagged documents |
| **Memory System** | Engine8/scripts/memory_system.py | Persistent | Store and retrieve conversational memories | Memory records |
| **LightRAG** | Engine8/scripts/lightrag_engine.py | API endpoint | Knowledge graph queries | Graph-based answers |
| **Master Indexer** | Engine8/scripts/master_index_all.py | Manual | Reindex all data across all collections | Indexed vectors |

### AI Agent Skills (Engine8/agents/)

| Agent | File | Purpose |
|-------|------|---------|
| **Program Intel Agent** | program_intel_agent.py | Full program intelligence reports |
| **Company Research Agent** | company_research_agent.py | Company deep-dive research |
| **Contact Finder Agent** | contact_finder_agent.py | Find contacts by criteria |
| **BD Strategy Agent** | bd_strategy_agent.py | BD strategy recommendations |
| **Analytics Agent** | analytics_agent.py | Data analytics and insights |
| **Contact Classifier Agent** | contact_classifier_agent.py | AI-powered contact classification |
| **Quality Assurance Agent** | quality_assurance_agent.py | QA validation agent |
| **Scraper Monitor Agent** | scraper_monitor_agent.py | Monitor scraping activities |
| **CrewAI Orchestrator** | crewai_orchestrator.py | Multi-agent CrewAI workflows |
| **BD Agents (unified)** | bd_agents.py | Unified BD agent definitions |

### Claude Desktop Skills (docs/Claude Skills/)

| Skill | File | Description |
|-------|------|-------------|
| Apify Job Scraping | apify-job-scraping-skill.md | Job scraping methodology |
| BD Call Sheet | bd-call-sheet-skill.md | Generate call preparation sheets |
| BD Outreach Messaging | bd-outreach-messaging-skill.md | Draft personalized outreach |
| BD Playbook | bd-playbook-skill.md | Create BD playbooks |
| Contact Classification | contact-classification-skill.md | Classify contacts into tiers |
| Federal Defense Programs | federal-defense-programs-skill.md | Federal program intelligence |
| Human Intelligence (HUMINT) | human-intelligence-skill.md | Process human intelligence notes |
| Job Standardization | job-standardization-skill.md | Standardize raw job postings |
| Notion BD Operations | notion-bd-operations-skill.md | Notion database operations |
| Program Mapping | program-mapping-skill.md | Map jobs to programs |

---

## 6. Skills Interaction Matrix

```
[Apify Job Scraping] → [Job Standardization] → [Program Mapping] → [BD Scoring]
                                                       ↓
                                                 [Notion Export]
                                                 [n8n Webhook]
                                                       ↓
[Bullhorn ETL] → [Contact Classification] → [Prime Contact Builder]
                         ↓                           ↓
                   [Org Chart]              [Contact Finder Agent]
                         ↓
[BD Playbook] ← [BD Strategy Agent] ← [Program Intel Agent]
      ↓
[BD Briefing] → [Call Script + Email + Talking Points]
      ↓
[BD Call Sheet] → [BD Outreach Messaging]

[ALL DATA] → [Master Indexer] → [Qdrant Vector Store]
                                       ↓
                              [Semantic Search API]
                              [RAG Engine]
                              [Hybrid Retrieval]
                              [LightRAG Knowledge Graph]
                                       ↓
                              [Dashboard (14 pages)]
                              [MCP Tools (Claude Code)]
                              [Dify Visual Workflows]
```

---

## 7. Tools & Capabilities Registry

### API Endpoints (http://localhost:8100)

| Endpoint | Method | Purpose | BD Relevance |
|----------|--------|---------|-------------|
| `/search` | POST | Semantic search across all collections | Core search |
| `/ask` | POST | RAG-powered Q&A with sources | BD research |
| `/ask/smart` | POST | Smart query routing | Intelligent Q&A |
| `/similar` | POST | Find similar items | Discovery |
| `/stats` | GET | Collection statistics | Monitoring |
| `/health` | GET | Server health check | Operations |
| `/api/v2/contacts` | GET | List contacts with filters | Contact intel |
| `/api/v2/programs` | GET | List programs with filters | Program intel |
| `/api/v2/jobs` | GET | List jobs with filters | Job intel |
| `/api/v2/contacts/{id}` | GET | Contact detail | Contact research |
| `/api/v2/programs/{id}` | GET | Program detail | Program research |
| `/memory/add` | POST | Store memory | Persistent context |
| `/memory/search` | POST | Search memories | Context retrieval |
| `/index/*` | POST | Index new data | Data ingestion |
| `/agents/program-intel` | POST | Run program intel agent | Deep analysis |
| `/agents/company-research` | POST | Run company research agent | Company analysis |
| `/agents/contact-finder` | POST | Run contact finder agent | Contact discovery |
| `/agents/bd-strategy` | POST | Run BD strategy agent | Strategy |
| `/dify/knowledge/*` | Various | Dify knowledge bridge | Visual AI |
| `/dify/agents/*` | Various | Dify agent bridge | Visual AI |
| `/dify/n8n/*` | Various | Dify n8n bridge | Workflow automation |

### MCP Servers (.mcp.json)

| Server | Type | Purpose | Tools Provided |
|--------|------|---------|---------------|
| **bd-knowledge** | Local (Node.js) | BD Knowledge semantic search & RAG | search_knowledge, ask_knowledge, get_program_intel, get_company_contacts |
| **n8n** | npx | N8N workflow orchestration | Trigger workflows, manage executions |
| **notion** | npx | Notion database operations | CRUD on all 5 Notion databases |
| **notion-remote** | Remote (OAuth) | Hosted Notion MCP | Same as above, OAuth-based |
| **apify** | npx | Apify actor management | Run scrapers, get datasets |
| **mapify** | Local (Node.js) | Mapify mind mapping | Generate mind maps |

---

## 8. MCP Server Connections

### bd-knowledge (Primary)
- **Command**: `node mcp/knowledge-mcp-server/build/index.js`
- **API URL**: `http://127.0.0.1:8100`
- **Operations**: search_knowledge, ask_knowledge, get_program_intel, get_company_contacts
- **Status**: Operational (API healthy)

### n8n
- **Command**: `npx -y n8n-mcp@latest`
- **Environment**: N8N_API_URL, N8N_API_KEY from .env
- **Operations**: Full n8n workflow control

### notion / notion-remote
- **Local**: `npx -y @notionhq/notion-mcp-server`
- **Remote**: `https://mcp.notion.com/mcp` (OAuth)
- **Database IDs**:
  - DCGS Contacts: `2ccdef65-baa5-8087-a53b-000ba596128e`
  - GDIT Jobs: `2563119e7914442cbe0fb86904a957a1`
  - Program Mapping: `f57792c1-605b-424c-8830-23ab41c47137`
  - Federal Programs: `06cd9b22-5d6b-4d37-b0d3-ba99da4971fa`
  - BD Opportunities: `2bcdef65-baa5-80ed-bd95-000b2f898e17`

### apify
- **Command**: `npx -y @apify/actors-mcp-server`
- **Operations**: Actor management, dataset retrieval

### mapify
- **Command**: `node mcp/mapify-mcp-server/build/index.js`
- **Operations**: Mind map generation from data

---

## 9. Data Files Deep Dive

### Qdrant Vector Collections (12 collections, 1,420,232 total vectors)

| Collection | Vectors | Indexed | Status | Purpose |
|------------|---------|---------|--------|---------|
| **documents** | 499,750 | 498,144 | GREEN | Past performance, briefings, reports |
| **activities** | 445,972 | 444,965 | GREEN | Call notes, meeting records |
| **contacts** | 211,267 | 209,701 | GREEN | CRM contacts with tier classification |
| **federal_contracts** | 107,902 | 108,188 | GREEN | FPDS contract data |
| **programs** | 68,103 | 67,454 | GREEN | Federal programs and contracts |
| **bullhorn_notes** | 50,710 | 100,210 | GREEN | CRM call/meeting notes |
| **opportunities** | 17,801 | 16,200 | GREEN | BD opportunities |
| **jobs** | 16,496 | 10,912 | GREEN | Job postings with BD scores |
| **intelligence_reports** | 2,229 | 0 | GREEN | Generated intel reports |
| **bd_memories** | 2 | - | GREEN | Persistent memories |
| **mem0** | 0 | - | - | Mem0 memory layer (unused) |
| **mem0migrations** | 0 | - | - | Migration tracking |

### Key Database Files

| File | Size | Type | Records | Purpose |
|------|------|------|---------|---------|
| bullhorn_master.db | 306 MB | SQLite | ~50K+ contacts | Complete Bullhorn CRM extract |
| documents/storage.sqlite | 312 MB | SQLite | 499,750 vectors | Document embeddings |
| contacts/storage.sqlite | 236 MB | SQLite | 211,267 vectors | Contact embeddings |
| activities/storage.sqlite | 220 MB | SQLite | 445,972 vectors | Activity embeddings |
| bullhorn_past_performance.db | 23 MB | SQLite | Past perf records | Contract history |

### Key CSV Data Files

| File | Location | Size | Purpose |
|------|----------|------|---------|
| ALL_NOTES_COMBINED.csv | data/from_data_scraper/ | 75 MB | All Bullhorn call notes |
| ProdServPlatformNAICS.csv | data/from_n8n_builder/ | 39 MB | NAICS/PSC analysis |
| notion_contacts.csv | Engine7_BullhornETL/outputs/ | 31 MB | Notion contact export |
| Contract_LargeVendorLabeledSmall.csv | data/from_n8n_builder/ | 26 MB | Contract anomalies |
| CONTACTS_INTELLIGENCE.csv | data/from_data_scraper/ | 18 MB | Enriched contact intel |
| Federal Programs MASTER V4.csv | engine_data/Engine2/ | ~130 KB | 388 federal programs |
| Master_All_Contacts.json | Engine3_OrgChart/data/ | 10.5 MB | All classified contacts |
| Contact_Search_List_MASTER.csv | engine_data/Engine3/ | Contact search data | Master search list |
| Jobs_Mapped_to_Programs_MASTER.csv | engine_data/Engine1/ | Mapped jobs | Job→program mapping |

### Dashboard Data Feeds (dashboard/public/data/)

| Feed | Purpose |
|------|---------|
| contacts.json | Classified contacts |
| contacts_classified.json | Tier-classified contacts |
| jobs.json / jobs_enriched.json | Job postings with enrichment |
| programs.json / programs_enriched.json | Federal programs with enrichment |
| contractors_enriched.json | Contractor intelligence |
| past_performance.json | Past performance data |
| correlation_summary.json | Cross-data correlations |
| data_freshness.json | Data recency tracking |
| contact_org_chart.json / prime_org_chart.json | Organizational charts |
| call_notes_*.json | Call intelligence (contacts, gaps, locations, primes, programs, stats, summary) |
| location_intelligence.json | Location analysis |
| placement_tracking.json | Placement tracking |

---

## 10. Data Flow & Pipeline Map

```
STAGE 1: DATA ACQUISITION
========================
[Apify Actors]         [Bullhorn CRM]         [SAM.gov/FPDS]        [ZoomInfo]
      ↓                      ↓                       ↓                   ↓
 Job Scrapes (CSV)    bullhorn_master.db        Contract data      Contact data
      ↓                      ↓                       ↓                   ↓
  Engine1_Scraper/      Engine7_BullhornETL/    external_apis/     Manual imports

STAGE 2: DATA PROCESSING
=========================
[Engine2: Program Mapping Pipeline (7 stages)]
  Raw Jobs → Cleaned → Standardized → Mapped to Programs → Scored → Exported
     ↓                                                          ↓
  engine_data/Engine2/                               outputs/notion/*.csv
                                                     outputs/n8n/*.json

[Engine3: Contact Classification]
  Raw Contacts → 6-Tier Classification → Org Chart → Prime Grouping
     ↓                                                    ↓
  engine_data/Engine3/                     Engine3/data/Prime_Contacts/

[Engine7: Bullhorn ETL]
  bullhorn.db → Contacts + Notes + Activities + Jobs
     ↓
  Engine7/outputs/ → Notion exports, intelligence reports

STAGE 3: KNOWLEDGE INDEXING
============================
[Engine8: Master Indexer]
  All CSVs + JSONs + DBs → Embeddings → Qdrant Collections
     ↓
  12 collections, 1.42M vectors
  + LightRAG knowledge graph
  + BM25 sparse index
  + Redis semantic cache

STAGE 4: INTELLIGENCE DELIVERY
================================
[Knowledge API (:8100)]         [Dashboard (:5173)]        [MCP Tools]
  50+ REST endpoints              14 interactive pages       6 MCP servers
  ↓                               ↓                         ↓
  RAG Q&A                        Mind Maps                  Claude Code
  Semantic Search                Knowledge Graphs           Claude Desktop
  Agent Workflows                Call Intelligence           Dify Visual AI
  Hybrid Retrieval               Smart Query                N8N Workflows

STAGE 5: OUTPUT GENERATION
============================
[Engine4: Playbook + Briefing]
  Program Intel + Contact Data → BD Playbooks
                               → Call Scripts
                               → Email Templates
                               → Talking Points
     ↓
  outputs/BD_Briefings/
```

---

## 11. Cross-Reference Matrix

| Source | Feeds Into | Via |
|--------|-----------|-----|
| Apify Job Scrapes | Engine2 Pipeline, Qdrant (jobs) | CSV → standardizer → mapper |
| Bullhorn CRM (bullhorn_master.db) | Engine3, Engine7, Qdrant (contacts, activities, bullhorn_notes) | SQLite ETL |
| Federal Programs CSV | Engine2 (mapping target), Qdrant (programs) | Direct indexing |
| Engine2 Mapped Jobs | Notion, n8n, Qdrant (jobs), Dashboard | CSV/JSON export |
| Engine3 Classified Contacts | Dashboard, Qdrant (contacts), BD Playbooks | JSON feeds |
| Engine7 Bullhorn ETL | Qdrant (multiple), Dashboard, Engine3 | ETL pipeline |
| Engine8 Qdrant Vectors | API endpoints, MCP tools, Dashboard, Dify | HTTP API |
| Dashboard JSON feeds | User-facing visualizations | Vite proxy → API |
| MCP bd-knowledge | Claude Code sessions | Node.js → API |
| N8N Workflows | Notion sync, webhook triggers | REST API |
| Notion Databases | Central data hub (5 databases) | Notion API |

---

## 12. Generated Artifacts Inventory

### BD Briefings (outputs/BD_Briefings/)

| Artifact | Target | Format | Status |
|----------|--------|--------|--------|
| AF DCGS - Langley CallScript | Intelligence Analyst | .md | Generated |
| AF DCGS - Langley Email | Intelligence Analyst | .txt | Generated |
| AF DCGS - Langley Playbook | Intelligence Analyst | .md | Generated |
| AF DCGS - Langley TalkingPoints | Intelligence Analyst | .md | Generated |
| Corporate HQ Playbook | Software Developer | .md | Generated |
| Distributed Common Ground Playbook | Senior Systems Engineer | .md | Generated |
| Unmatched Data Analyst Playbook | Data Analyst | .md | Generated |
| Unmatched Software Developer Playbook | Software Developer | .md | Generated |
| Unmatched Systems Engineer Playbook | Systems Engineer | .md | Generated |

### Data Exports (outputs/)

| Export | Count | Format | Status |
|--------|-------|--------|--------|
| Notion job exports | 14+ timestamped files | .csv | Current |
| N8N webhook outputs | 7 files | .json | Current |
| BD call sheets | 3 versions | .csv | Generated |
| BD playbooks (Monday format) | 2 versions | .csv | Generated |
| Enriched spreadsheets | 1 file | .csv | Generated |
| Coworker takeover package | 4 files | .csv | Generated |
| ZoomInfo search queries | 1 file | .csv | Generated |
| Program placement gap analysis | 1 file | .csv | Generated |

### Architecture Documents (docs/)

| Document | Size | Purpose | Status |
|----------|------|---------|--------|
| OPENCLAW_MASTER_ARCHITECTURE.md | ~52K tokens | OpenClaw integration plan | Ready for implementation |
| KNOWLEDGE_SYSTEM_GUIDE.md | Architecture guide | Engine8 architecture | Current |
| KNOWLEDGE_SYSTEM_ROADMAP.md | Roadmap | Engine8 roadmap | Current |
| RAG_USAGE_GUIDE.md | Usage guide | RAG patterns | Current |
| AI_FILESYSTEM_GUIDE.md | Usage guide | AI file access patterns | Current |
| TERMINAL_A_AUDIT_20260207.md | Audit | Previous terminal audit | Historical |
| Mind_Map_Architecture_Analysis.md | Design | Mind map system design | Current |

---

## 13. Version Tracking

### Multi-Version Files

| File Pattern | Versions | Canonical |
|-------------|----------|-----------|
| Federal Programs*.csv | V3, V4, MASTER ENRICHED, TANGO ENRICHED, BACKUP | **Federal Programs MASTER V4.csv** |
| bullhorn_etl*.py | v1, v2 | **bullhorn_etl_v2.py** |
| PTS_BD_Dashboard_Implementation*.md | v1, v5, v6_CORRECTED | **v6_CORRECTED** |
| README*.md | README.md, README-OLD.md, README_V6_CORRECTED.md | **README.md** |
| 01_ARCHITECTURE_STATE*.md | v1, v2 | **v2** |
| 02_TERMINAL_PROMPT_PATTERNS*.md | v1, v2 | **v2** |

### Data Duplication (same file in multiple locations)

| File | Locations | Recommendation |
|------|-----------|---------------|
| bullhorn_master.db (306MB) | Engine7/data/, data/ | Consolidate to one location |
| Qdrant SQLite stores | qdrant/, Engine8/data/qdrant/, data/qdrant/ | 3x duplication — fix symlinks |
| Master_All_Contacts.json (10.5MB) | Engine3/data/, engine_data/Engine3/, data/from_n8n_builder/ | 3x duplication |
| Federal Programs CSVs | Engine2/data/, engine_data/Engine2/, root level | 3x duplication |

---

## 14. Environment Capabilities

### System

| Component | Version/Status |
|-----------|---------------|
| **OS** | Windows 11 Pro 10.0.26100 |
| **Python** | 3.12.10 |
| **Node.js** | v24.13.0 |
| **npm** | 11.8.0 |
| **Git** | 2.35.1.windows.2 |
| **Disk** | 953 GB total, 605 GB free (63% available) |

### Key Python Packages (253 total)

| Category | Packages |
|----------|----------|
| **AI/LLM** | anthropic 0.78.0, openai 1.83.0, crewai 1.9.3, langchain-anthropic 1.3.2, langgraph 1.0.7 |
| **Embeddings** | sentence-transformers 5.2.2, tiktoken 0.8.0, torch 2.10.0, transformers 4.57.6 |
| **Vector DB** | qdrant-client 1.16.2, chromadb 1.1.1 |
| **RAG** | llama-index (multiple), lightrag, graphiti-core 0.26.3 |
| **Data** | pandas 2.3.3, numpy 2.4.2, scipy 1.17.0, scikit-learn 1.8.0, xgboost 3.1.3 |
| **Web/API** | fastapi 0.128.0, uvicorn 0.40.0, requests 2.32.5, httpx 0.25.0 |
| **Documents** | docling 2.72.0, python-docx 1.2.0, openpyxl 1.5, python-pptx 1.0.2, pypdf 6.6.2 |
| **Memory** | mem0ai 0.1.116, redis 7.1.1 |
| **Scraping** | beautifulsoup4, crawl4ai, firecrawl |
| **Monitoring** | prometheus-client, psutil 7.2.2, opentelemetry (full stack) |
| **MCP** | mcp 1.23.3, fastmcp |
| **Graph** | neo4j 6.1.0, neo4j-graphrag 1.13.0, networkx 3.6.1 |

### Live Services

| Service | URL | Status |
|---------|-----|--------|
| Qdrant Vector DB | http://localhost:6333 | RUNNING (12 collections) |
| BD Knowledge API | http://localhost:8100 | RUNNING (healthy) |
| Dashboard (Vite) | http://localhost:5173 | Available when started |

### Missing Tools

| Tool | Purpose | Impact |
|------|---------|--------|
| pandoc | Document format conversion | Can use python-docx/pypdf instead |
| docker | Containerization | Not needed for local dev |
| wkhtmltopdf | PDF generation | Can use PyMuPDF instead |

---

## 15. Gap Analysis & Recommendations

### Missing / Incomplete

| Gap | Severity | Description |
|-----|----------|-------------|
| **Engine4_Briefing nearly empty** | Medium | Only 1 file — briefing_generator.py exists but Engine4_Briefing/ has minimal content |
| **Engine5_Scoring minimal** | Medium | Only 2 files — scoring logic exists but no data pipeline integration |
| **Engine6_QA incomplete** | Medium | Only 4 files — alerts and feedback exist but no automated QA loop |
| **Memory system unused** | Low | bd_memories has only 2 vectors, mem0 has 0 — memory not being utilized |
| **PageIndex empty** | Low | 0 documents indexed in PageIndex engine |
| **intelligence_reports not indexed** | Low | 2,229 reports but indexed_vectors_count = 0 |
| **No automated orchestrator** | High | No central orchestrator.py connecting all 8 engines end-to-end |
| **No CI/CD** | Medium | No GitHub Actions, no automated testing pipeline |
| **No .env.example in root** | Low | .env.example exists but may be outdated |

### Stale Data

| Item | Last Modified | Status |
|------|--------------|--------|
| Notion exports (jobs_export_*) | Multiple from Jan 2026 | Some may be outdated |
| BD Briefings | Modified recently | Active |
| Root-level CSVs | Feb 3, 2026 | May need refresh |

### Data Duplication (Action Required)

| Issue | Impact | Recommendation |
|-------|--------|---------------|
| Qdrant storage in 3 locations | ~750 MB wasted | Use symlinks or single canonical path |
| bullhorn_master.db in 2 locations | 306 MB wasted | Single location + reference |
| Master_All_Contacts.json 3x | 31.5 MB wasted | Single source of truth |
| Federal Programs CSVs 3x | ~400 KB wasted | Single canonical version |

### Recommended Next Steps

1. **Build Central Orchestrator** — Wire all 8 engines into a single pipeline (orchestrator.py)
2. **Fix Data Duplication** — Consolidate to canonical locations, use symlinks
3. **Implement OpenClaw** — Phase 1 ready per OPENCLAW_MASTER_ARCHITECTURE.md
4. **Activate Memory System** — Wire Qdrant bd_memories + mem0 into agent workflows
5. **Add CI/CD** — GitHub Actions for testing on push
6. **Complete Engines 4-6** — Flesh out briefing, scoring, and QA engines
7. **Index intelligence_reports** — 2,229 reports have vectors but aren't indexed for search

---

## 16. Appendices

### Appendix A: Top-Level Directories (File Counts)

| Directory | Files |
|-----------|-------|
| data/ | 855 |
| dashboard/ | 310 |
| Engine8_Knowledge/ | 289 |
| outputs/ | 242 |
| src/ | 148 |
| Engine7_BullhornETL/ | 146 |
| engine_data/ | 146 |
| tests/ | 142 |
| docs/ | 115 |
| Engine3_OrgChart/ | 71 |
| Engine2_ProgramMapping/ | 41 |
| mcp/ | 32 |
| scripts/ | 27 |
| Engine1_Scraper/ | 24 |
| services/ | 21 |
| dify_integration/ | 7 |
| Engine4_Playbook/ | 4 |
| Engine6_QA/ | 4 |
| config/ | 4 |
| utils/ | 3 |
| Engine5_Scoring/ | 2 |
| api/ | 2 |
| Engine4_Briefing/ | 1 |

### Appendix B: Qdrant Collection Sizes (Sorted)

| Collection | Vectors | Storage |
|------------|---------|---------|
| documents | 499,750 | 312 MB |
| activities | 445,972 | 220 MB |
| contacts | 211,267 | 236 MB |
| federal_contracts | 107,902 | — |
| programs | 68,103 | — |
| bullhorn_notes | 50,710 | — |
| opportunities | 17,801 | — |
| jobs | 16,496 | — |
| intelligence_reports | 2,229 | 52 MB |
| bd_memories | 2 | — |
| **TOTAL** | **1,420,232** | **~1 GB** |

### Appendix C: All Python Scripts (81 in scripts/ directories)

**Engine2:** job_standardizer.py, program_mapper.py, pipeline.py, full_pipeline.py, exporters.py
**Engine3:** contact_classifier.py, contact_lookup.py
**Engine4:** briefing_generator.py, bd_playbook_generator.py
**Engine5:** bd_scoring.py
**Engine6:** alerts.py, qa_feedback.py
**Engine7:** bullhorn_etl.py, bullhorn_etl_v2.py, analyze_prime_contacts.py, bd_intelligence_report.py, build_prime_contact_databases.py, dashboard_integration.py, database_schema.py, data_cleanup.py, export_coworker_playbook.py, export_intelligence_dashboard.py, export_to_notion.py, integrate_call_notes.py, intelligent_contact_classifier.py, link_to_federal_programs.py, past_performance_report.py, program_mapper.py, import_coworker_data.py, analyze_call_notes.py, contact_scoring.py, financial_analysis.py
**Engine8:** vector_store.py, rag_engine.py, indexer.py, hybrid_retriever.py, memory_layer.py, lightrag_engine.py, query_router.py, pageindex_engine.py, redis_cache.py, auto_tagger.py, sparse_encoder.py, hybrid_collections.py, memory_system.py, web_scrapers.py, file_watcher.py, document_processor.py, docling_processor.py, init_bm25.py, populate_lightrag.py, rag_router.py, master_index_all.py, dedup_programs.py, index_all_data.py, index_bullhorn_contacts.py, index_all_docs.py, index_dashboard_data.py, index_engine1_jobs.py, index_engine2_programs.py, index_engine3_contacts.py, index_from_json.py, index_staged_data.py, reindex_batch.py, enrich_reindex_all.py, priority_index_full.py
**Root scripts/:** analyze_contact_gaps.py, bd_playbook_generator.py, convert_data_to_json.py, create_call_sheet.py, create_enriched_spreadsheet.py, create_unified_collections.py, generate_bd_call_sheet.py, generate_pipeline_report.py, job_opportunities_parser.py, merge_enriched_federal_programs.py, test_phase4_agents.py, verify_pipeline.py, health_check.py, validate_phase.py

### Appendix D: Dashboard Pages

1. **JobIntelligence** — Job postings analysis and mapping
2. **Opportunities** — BD opportunity tracking
3. **Contractors** — Contractor intelligence
4. **PastPerformance** — Past performance data
5. **DailyPlaybook** — Daily BD action plan
6. **CallIntelligence** — Call note analysis
7. **Locations** — Location-based intelligence
8. **KnowledgeGraph** — Visual knowledge graph
9. **MindMap** — Interactive mind mapping
10. **SmartQuery** — AI-powered natural language query
11. **DataQualityDashboard** — Data quality monitoring
12. **EnrichmentDashboard** — Data enrichment status
13. **MemoryContext** — Memory system UI
14. **SystemHealth** — System monitoring
15. **BDEvents** — BD event tracking
16. **PlacementsPage** — Placement tracking

### Appendix E: Requirements.txt Categories

| Category | Key Packages |
|----------|-------------|
| Core | python-dotenv, requests, pydantic, pydantic-settings |
| Reliability | tenacity, structlog, slowapi |
| AI/LLM | anthropic, openai |
| Data | pandas, numpy |
| Notion | notion-client |
| Embeddings | tiktoken, scipy |
| Scraping | beautifulsoup4, lxml |
| CLI | click, tqdm |
| Database | psycopg2-binary |
| Testing | pytest, pytest-cov |
| Vector DB | qdrant-client, sentence-transformers |
| Document Processing | docling, python-magic-bin |
| RAG | llama-index (full stack) |
| API | fastapi, uvicorn |
| File Watching | watchdog |
| Memory | mem0ai |
| Knowledge Graph | lightrag-hku |
| Hybrid Retrieval | rank-bm25 |
| Caching | redis |
| Web Scraping | firecrawl-py, crawl4ai |
| Multi-Agent | crewai |
| LangGraph | langgraph, langgraph-checkpoint-sqlite, aiosqlite |
| MCP | fastmcp |
| Evaluation | ragas, datasets |
| ML | xgboost, shap, transformers |
| Monitoring | prometheus-client, psutil |
| Streaming | python-ulid, websockets, fakeredis |

---

---

## 17. Broader Workspace Ecosystem (C:\Auto-Claud\)

The BD-Automation-Engine exists within a larger workspace containing 8 sibling projects:

| Directory | Type | Files | Purpose |
|-----------|------|-------|---------|
| **Auto-Claude/** | Git Repo (fork) | Large | Original Auto Claude multi-agent framework (Electron + Python) |
| **BD-Automation-Engine/** | Subproject | 4,221 | BD Intelligence System — this audit's primary target |
| **N8N-Builder/** | Full App | 5,535 | N8N workflow orchestration (559 .py, 888 .sql, 742 .csv, 34 workflows, 40 company intel dirs) |
| **data-scraper/** | Python App | 1,523 | Job/data scraping pipelines (600 .py, 385 .csv, 46 API modules, 40+ company knowledge dirs) |
| **capture-mcp-server/** | MCP Server | ~15 | Browser automation via Chrome DevTools Protocol |
| **n8n-mcp/** | MCP Server | 46 | N8N Model Context Protocol server (Docker + Node.js) |
| **project-knowledge/** | Docs | 4 | Architecture & methodology reference docs |
| **qdrant_storage/** | Data Store | 2 | Qdrant vector DB persistence (raft_state.json) |

**Combined workspace total: ~11,300+ files across all projects (BD: 4,221 + N8N: 5,535 + Scraper: 1,523 + others)**

### N8N-Builder Key Stats (5,535 files, 295 directories)

| Directory | Files | Highlights |
|-----------|-------|-----------|
| data/ | 2,203 | API extracts, Bullhorn, federal contracts, proposals, RAG data |
| src/ | 392 | 42 API modules, 44 intelligence tools, 9 campaigns, 9 outreach |
| tests/ | 354 | Test suite |
| external/ | 281 | SAM.gov scrapers, Tango clients, Apify configs, n8n-mcp |
| output/ | 262 | BD databases, intelligence reports, targeting lists |
| outputs/ | 152 | BD intelligence for 40 companies (Leidos, SAIC, Northrop, etc.) |
| dashboard/ | 64 | React/TypeScript dashboard (separate from BD Engine dashboard) |
| workflows/ | 34 | 10 categories: alerts, core, hub, monitoring, pipelines, scheduled |
| bd_langgraph/ | 24 | LangGraph agentic BD workflows |
| knowledge-base/ | 21 | LanceDB vector store, document indexes |

### Cross-Project Data Flows

```
[data-scraper] → scrapes jobs/contacts → data/from_data_scraper/ (in BD Engine)
[N8N-Builder] → orchestrates workflows → data/from_n8n_builder/ (in BD Engine)
[n8n-mcp] → provides MCP tools → .mcp.json n8n server config
[capture-mcp-server] → browser automation → used by Claude Code sessions
[qdrant_storage] → persists vectors → Qdrant server at :6333
[project-knowledge] → 4 reference docs → shared across all projects
[Auto-Claude] → provides agent framework → .auto-claude/ integration in BD Engine
```

### Key Config Files Across Workspace

| File | Location | Purpose |
|------|----------|---------|
| Auto-Claude/CLAUDE.md | Root instructions | Auto Claude framework rules |
| BD-Automation-Engine/CLAUDE.md | BD Engine instructions | BD-specific rules, git workflow |
| BD-Automation-Engine/.mcp.json | MCP config | 6 MCP servers |
| data-scraper/.mcp.json | MCP config | Data scraper MCP |
| N8N-Builder/mcp/n8n-orchestrator-mcp/ | N8N MCP | Workflow orchestration |
| project-knowledge/01-04_*.md | Reference docs | Architecture, schemas, methodology |

---

*Audit completed 2026-02-11. Total vectors: 1,420,232. BD-Automation-Engine: 4,221 files. N8N-Builder: 5,535 files. data-scraper: 1,523 files. Full workspace: ~11,300+ files across 8 interconnected projects. All systems operational.*
