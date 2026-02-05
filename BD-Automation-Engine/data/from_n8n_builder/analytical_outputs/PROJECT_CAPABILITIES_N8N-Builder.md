# N8N-Builder Project Capabilities Report

**Generated:** 2026-02-03
**Project Root:** `C:\Auto-Claud\N8N-Builder`
**Repository Status:** Git-tracked (master branch)

---

## 1. Project Overview

### Purpose
The N8N-Builder is a **Federal Contract Intelligence Platform** that combines:
- Federal contract discovery and enrichment
- BD (Business Development) scoring and prioritization
- Prime contractor contact management
- Competitive intelligence tracking
- N8N workflow automation for pipeline orchestration

### Core Capabilities
1. **Three Discovery Engines** - Federal programs, DoD staffing, high sub-spend contracts
2. **Four-Phase Enrichment Pipeline** - Task orders → Locations → Org hierarchy → Technology signals
3. **BD Scoring System** - 100-point scale with 3-tier classification
4. **Contact Database** - 25 prime contractors with 15,000+ raw contacts
5. **N8N Workflow Orchestration** - 11 active workflows via MCP integration
6. **Knowledge Base** - LanceDB vector embeddings for semantic search
7. **Hub Integration** - Cross-platform data sharing with BD-Automation-Engine

### Component Status
| Component | Status | Notes |
|-----------|--------|-------|
| Discovery Engines | ✅ Operational | 3 engines, multiple versions |
| Enrichment Pipeline | ✅ Operational | 4-phase with Tango integration |
| BD Scoring | ✅ Operational | 5-factor scoring model |
| Contact Databases | ✅ Operational | 25 prime contractors |
| N8N Workflows | ✅ Operational | 11 active, 26 inactive |
| Knowledge Base | ✅ Operational | 21MB LanceDB embeddings |
| Hub Integration | ⚠️ Needs Hub | Requires BD-Engine connection |
| Browser Automation | ⚠️ Experimental | BrowserUse integration |
| LangGraph Workflows | ⚠️ Experimental | BD workflow state machines |

---

## 2. Directory Structure

```
N8N-Builder/
├── .auto-claude/          # Auto-Claude project metadata
├── .claude/               # Claude Code local settings
├── api/                   # Workflow API module
├── bd_langgraph/          # LangGraph BD workflow state machines
├── browser_automation/    # AI-driven browser automation
├── client/                # N8N client module
├── config/                # Configuration files (endpoints, schedules)
├── data/                  # Input data and caches
│   ├── bullhorn/          # CRM exports (gitignored)
│   ├── cache/             # API response caches
│   ├── contacts_databases/
│   │   ├── Prime_Contacts/           # 25 company CSVs
│   │   └── Prime_Contacts_Enriched/  # 26 enriched CSVs
│   ├── federal/           # Federal program data
│   ├── program_notion_export_databases/
│   └── reference/         # DIIG-CSIS lookup tables
├── design_intelligence/   # UI/UX design system
├── docs/                  # Additional documentation
├── external/              # Cloned external repositories (14 tools)
├── external_apis/         # API integration utilities
├── hub/                   # Hub integration client
├── knowledge-base/        # LanceDB vector embeddings
├── mcp/                   # MCP orchestrator server
├── models/                # Data models
├── New Enhancements/      # Enhancement proposals
├── output/                # Generated outputs
│   ├── bd_databases/      # Master BD databases
│   │   └── categorized/   # Tiered and categorized targets
│   ├── exports/           # General CSV exports
│   ├── intelligence/      # BD intelligence outputs
│   ├── program_intelligence/
│   ├── reports/           # Markdown reports
│   ├── targeting/         # Call lists and Excel sheets
│   └── task_orders/       # Task order extractions
├── projects/              # Per-workflow architecture docs
├── scripts/               # Migration and deployment scripts
├── services/              # Service registry
├── src/                   # Main Python source code
│   ├── api_clients/       # API clients (SAM, Tango, USASpending)
│   ├── config/            # Centralized settings
│   ├── database/          # ORM models and migrations
│   ├── discovery/         # Discovery engines
│   ├── enrichment/        # Enrichment pipeline
│   ├── intelligence/      # BD analysis tools (30+ scripts)
│   ├── knowledge_base/    # Vector DB and search
│   ├── models/            # Data models
│   ├── pipeline/          # Data processing pipelines
│   ├── pipelines/         # Complex pipeline workflows
│   └── utils/             # Utility functions
├── tasks/                 # Task tracking
└── workflows/             # N8N workflow JSONs
    ├── alerts/            # Notification workflows
    ├── core/              # Core execution workflows
    ├── hub/               # Hub integration webhooks
    ├── monitoring/        # Health monitoring
    ├── notion/            # Notion integration
    ├── pipelines/         # Complex pipelines
    ├── scheduled/         # Scheduled tasks
    ├── scraper/           # Scraper triggers
    ├── templates/         # Workflow templates
    └── utilities/         # Utility workflows
```

---

## 3. File Inventory by Type

| File Type | Count | Notes |
|-----------|-------|-------|
| Python (.py) | **178** | Excluding external folder |
| CSV (.csv) | **608** | Data and outputs |
| Markdown (.md) | **140** | Documentation |
| JSON (.json) | **55** | Config and cache files |
| TypeScript (.ts) | **1** | MCP orchestrator |
| JavaScript (.js) | **2** | Import/test scripts |
| YAML (.yaml/.yml) | **2** | Config files |

### Storage by Directory
| Directory | Size |
|-----------|------|
| data/ | **1.7 GB** |
| knowledge-base/embeddings/ | **21 MB** |
| output/ | **14 MB** |
| external/ | **984 KB** |

---

## 4. Python Modules & Scripts

### Source Code Organization (`src/`)

#### API Clients (`src/api_clients/`) - 4 modules
| File | Purpose |
|------|---------|
| `base.py` | Base API client class with retry logic |
| `sam.py` | SAM.gov API client |
| `tango.py` | Tango/MakeGov API client |
| `usaspending.py` | USASpending.gov API client |

#### Discovery Engines (`src/discovery/`) - 9 versions
| File | Purpose |
|------|---------|
| `federal-programs-discovery-engine.py` | Original discovery engine |
| `federal-programs-discovery-engine-v2.py` | Enhanced discovery (primary) |
| `dod-staffing-discovery.py` | DoD staffing discovery |
| `dod-staffing-discovery-FINAL-v4.py` | DoD staffing final version |
| `dod-staffing-discovery-SDK-OPTIMIZED.py` | SDK-optimized version |
| `high-sub-spend-discovery.py` | High subcontract spend discovery |
| `high-sub-spend-discovery-v2.py` | Enhanced sub-spend discovery |

#### Enrichment Pipeline (`src/enrichment/`) - 11 modules
| File | Purpose |
|------|---------|
| `run_enrichment.py` | Master enrichment orchestrator |
| `task_order_enricher.py` | Phase 1: Task order extraction |
| `location_enricher.py` | Phase 2: Geographic enrichment |
| `org_hierarchy_builder.py` | Phase 3: Organizational mapping |
| `technology_extractor.py` | Phase 4: Technology signals |
| `tango-enrichment.py` | Tango API enrichment |
| `enrich-federal-programs-v4-TANGO.py` | Full Tango integration |

#### Intelligence Tools (`src/intelligence/`) - 30+ scripts
| Category | Key Scripts |
|----------|-------------|
| BD Strategy | `advanced_bd_tools.py`, `bd_strategy_playbook_generator.py` |
| Competitive Intel | `competitive_intelligence_tracker.py`, `competitor_job_analyzer.py` |
| Contact Management | `contact_deduplication.py`, `find_gap_contacts.py` |
| Territory Analysis | `find_virgin_territory.py`, `territory_grab_analysis.py` |
| Targeting | `sdvosb_targeting_engine.py`, `create_zoominfo_targets.py` |
| CRM Integration | `bullhorn_data_processor.py`, `bullhorn_intelligence/` |
| Reporting | `kpi_dashboard_generator.py`, `hiring_signal_alerts.py` |

#### Knowledge Base (`src/knowledge_base/`) - 8 modules
| File | Purpose |
|------|---------|
| `mcp_server.py` | MCP server for Claude Code integration |
| `indexer.py` | Document indexer |
| `search.py` | Semantic search engine |
| `categorizer.py` | AI file categorization |
| `document_processor.py` | Document processing |
| `cli.py` | Command line interface |
| `watcher.py` | File system watcher |

#### Pipeline Processing (`src/pipeline/`) - 7 scripts
| File | Purpose |
|------|---------|
| `complete-pipeline.py` | Full pipeline orchestration |
| `filter-active-programs.py` | Active program filtering |
| `merge-and-deduplicate.py` | Data merging and deduplication |
| `create-tango-exports.py` | Tango export generation |

### Additional Python Modules

#### BD LangGraph (`bd_langgraph/`) - 12 modules
State machine workflows for BD automation:
- `bd_workflows.py` - Main BD workflows
- `contact_workflows.py` - Contact management workflows
- `pipeline_workflows.py` - Pipeline state machines
- `recompete_workflows.py` - Recompete tracking
- `human_in_loop.py` - Human approval workflows
- `checkpointer.py` - State persistence
- `nodes.py` - Workflow nodes (32KB - largest)
- `edges.py` - State transitions
- `states.py` - State definitions
- `integrations.py` - External integrations

#### Browser Automation (`browser_automation/`) - 5 modules
AI-driven browser automation using BrowserUse:
- `browser_agent.py` - Main browser agent
- `bd_tasks.py` - BD-specific browser tasks
- `config.py` - Browser configuration
- `safety.py` - Safety constraints

---

## 5. Database Files

### LanceDB Embeddings
| Location | Size | Purpose |
|----------|------|---------|
| `knowledge-base/embeddings/knowledge.lance/` | **21 MB** | Vector embeddings |
| `knowledge-base/embeddings/knowledge.lance/documents.lance/` | - | Document chunks |
| `knowledge-base/embeddings/knowledge.lance/documents.lance/data/` | - | 6 chunk files |
| `knowledge-base/embeddings/knowledge.lance/documents.lance/_transactions/` | - | 6 transaction logs |
| `knowledge-base/embeddings/knowledge.lance/documents.lance/_versions/` | - | 6 version manifests |

### Knowledge Base Indexes
| File | Purpose |
|------|---------|
| `knowledge-base/file_categories.json` | Cached file categorizations |
| `knowledge-base/processed_docs.json` | Processed document tracking |
| `knowledge-base/watcher_state.json` | File watcher state |

### Cache Files (`data/cache/`)
| File | Purpose |
|------|---------|
| `contract_cache.json` | Cached contract data |
| `tango_cache.json` | Tango API response cache |
| `discovery-stats-v2.json` | Discovery statistics |
| `dod-discovery-stats-*.json` | DoD discovery stats |
| `high-sub-spend-stats.json` | Sub-spend stats |
| `tango-api-endpoints.json` | API endpoint cache |

---

## 6. Data Assets

### Contact Databases (`data/contacts_databases/`)

#### Prime Contacts (25 companies)
| Company | Contacts |
|---------|----------|
| CACI | 3,633 |
| GDIT | 2,344 |
| Leidos | 1,482 |
| Lockheed Martin | 1,136 |
| SAIC | 897 |
| Northrop Grumman | 852 |
| AWS | 801 |
| Microsoft | 808 |
| Boeing | 679 |
| Raytheon | 689 |
| Peraton | 654 |
| Palantir | 439 |
| Booz Allen Hamilton | 426 |
| Deloitte | 370 |
| BAE Systems | 272 |
| L3Harris | 218 |
| Jacobs | 186 |
| Accenture | 102 |
| ManTech | 96 |
| Amentum | 88 |
| Anduril | 58 |
| Parsons | 50 |
| KBR | 41 |
| General Dynamics | 32 |
| Sierra Nevada | 23 |
| **TOTAL** | **16,376** |

#### Enriched Contacts (26 files)
| Company | Enriched Contacts |
|---------|-------------------|
| CACI | 3,504 |
| GDIT | 2,534 |
| Leidos | 1,431 |
| Lockheed Martin | 1,192 |
| Microsoft | 890 |
| SAIC | 848 |
| Northrop Grumman | 833 |
| AWS | 806 |
| Boeing | 728 |
| Peraton | 686 |
| Raytheon | 669 |
| Booz Allen Hamilton | 439 |
| Palantir | 414 |
| Deloitte | 380 |
| BAE Systems | 291 |
| Jacobs | 210 |
| L3Harris | 182 |
| Accenture | 101 |
| ManTech | 89 |
| Amentum | 79 |
| Parsons | 64 |
| Anduril | 60 |
| KBR | 54 |
| General Dynamics | 37 |
| Sierra Nevada | 17 |
| **Unclassified** | **22,679** |
| **TOTAL** | **38,217** |

### Federal Data (`data/federal/`)
| File | Records | Size |
|------|---------|------|
| `DISCOVERED_PROGRAMS_ALL_V2.csv` | 101 programs | 31 KB |
| `Federal Programs FULLY ENRICHED.csv` | - | 169 KB |
| `Federal Programs ACTIVE ENRICHED V4 TANGO.csv` | - | 160 KB |
| `Federal Programs COMPLETE ENRICHED.csv` | - | 139 KB |
| `Federal Programs ACTIVE ENRICHED V3.csv` | - | 93 KB |
| `Federal Programs MASTER V2 HIGH SUB.csv` | - | 86 KB |
| `Federal Programs MASTER.csv` | - | 86 KB |

### Reference Data (`data/reference/`)
| Repository | Purpose |
|------------|---------|
| `DIIG-CSIS-Lookup-Tables/` | Complete CSIS lookup tables (git repo) |
| `Lookup-Tables/` | Additional lookup data (git repo) |
| `pws_documents/` | PWS reference documents |

### Program Notion Exports (`data/program_notion_export_databases/`)
| File | Purpose |
|------|---------|
| `FINAL-V3-BREAKTHROUGH-REPORT.md` | V3 breakthrough analysis |
| `V3-BREAKTHROUGH-SUMMARY.md` | Summary report |
| `Federal Programs TANGO ENRICHED.csv` | Tango-enriched programs |
| `Program Mapping Intelligence Hub All.csv` | Hub mapping data |

---

## 7. Output Databases

### BD Master Databases (`output/bd_databases/`)
| File | Size | Purpose |
|------|------|---------|
| `db3_dod_opportunities_all.csv` | 1.3 MB | All DoD opportunities |
| `master_bd_targets.csv` | 692 KB | Master BD target list |
| `db6_bd_targets_all.csv` | 704 KB | All BD targets |
| `db1_dod_prime_contracts_100m.csv` | 653 KB | DoD contracts >$100M |
| `db3_dod_solicitations.csv` | 637 KB | DoD solicitations |
| `db2_subawards_tango.csv` | 411 KB | Subawards from Tango |
| `db3_dod_it_opportunities.csv` | 360 KB | DoD IT opportunities |
| `db6_bd_targets_priority.csv` | 314 KB | Priority BD targets |

### Categorized Outputs (`output/bd_databases/categorized/`)
| Category | Files |
|----------|-------|
| **By Tier** | `tier1_high_priority_targets.csv` (389KB), `tier2_medium_priority_targets.csv` (114KB), `tier3_standard_targets.csv` (189KB) |
| **By Size** | `size_billion_1b_5b.csv` (195KB), `size_large_500m_1b.csv` (264KB), `size_medium_100m_500m.csv` (197KB), `size_giant_5b_10b.csv` (23KB), `size_mega_10b_plus.csv` (15KB) |
| **By Activity** | `high_subcontract_activity.csv` (353KB), `medium_subcontract_activity.csv` (19KB), `some_subcontract_activity.csv` (17KB) |
| **By Agency** | `agency_Department_of_Defense.csv` (691KB), `agency_Department_of_the_Navy.csv` |
| **IT Services** | `it_services_all_targets.csv` (24KB), `it_services_high_priority.csv` (19KB) |

### Intelligence Outputs (`output/intelligence/`)
| File | Size | Purpose |
|------|------|---------|
| `LINKEDIN_SEARCH_QUERIES.csv` | 94 KB | LinkedIn search guide |
| `BD_CALL_SHEET_HIGH_PRIORITY.csv` | 87 KB | Priority call list |
| `hiring_intelligence.csv` | 66 KB | Hiring signals |
| `BD_TARGET_SHEET_LEIDOS.csv` | 41 KB | Leidos targets |
| `bd_targets.csv` | 34 KB | BD targets |
| `BD_TARGET_SHEET_SAIC.csv` | 32 KB | SAIC targets |
| `HIGH_SUB_SPEND_ALL_CONTRACTS.csv` | 20 KB | High sub-spend contracts |
| `BD_TARGET_SHEET_PERATON.csv` | 12 KB | Peraton targets |
| Reports: `BD_ENHANCEMENT_REPORT.md`, `WEEKLY_BD_ACTION_PLAN.md` |

### Targeting Outputs (`output/targeting/`)
Excel call sheets and ZoomInfo exports for AM/BD outreach.

---

## 8. Knowledge Base (LanceDB)

### Structure
```
knowledge-base/
├── embeddings/
│   └── knowledge.lance/
│       └── documents.lance/
│           ├── data/           # 6 chunk files with embeddings
│           ├── _transactions/  # 6 transaction logs
│           └── _versions/      # 6 version manifests
├── documents/                  # Processed documents
├── indexes/                    # Search indexes
├── file_categories.json        # AI-categorized files
├── processed_docs.json         # Processing state
└── watcher_state.json          # File watcher state
```

### MCP Server Tools (14 tools)
The knowledge base MCP server provides:
- `kb_search` - Semantic search across project files
- `kb_similar` - Find similar files
- `kb_program_search` - Program-specific searches
- `kb_code_search` - Code search
- `kb_docs_search` - Documentation search
- File categorization and processing tools

### Size: **21 MB** total embeddings

---

## 9. Configuration

### Environment Variables (`.env.example`)
| Category | Variables |
|----------|-----------|
| **N8N Cloud** | `N8N_CLOUD_URL`, `N8N_API_URL`, `N8N_API_KEY` |
| **BD Hub** | `BD_HUB_URL`, `HUB_API_URL`, `HUB_API_KEY` |
| **Vector DB** | `QDRANT_URL`, `QDRANT_API_KEY` |
| **API Keys** | `TANGO_API_KEY`, `SAM_GOV_API_KEY`, `USASPENDING_API_KEY` |
| **LLM** | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` |
| **Browser** | `BROWSER_LLM_PROVIDER`, `BROWSERUSE_API_KEY` |
| **CRM** | `BULLHORN_USERNAME`, `BULLHORN_PASSWORD` |
| **Database** | `DATABASE_PATH`, `DATABASE_URL` |
| **Logging** | `LOG_LEVEL` |
| **Notion** | `NOTION_API_KEY` |

### MCP Configuration (`.mcp.json.example`)
```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "npx",
      "args": ["-y", "n8n-mcp"],
      "env": { "N8N_API_URL": "...", "N8N_API_KEY": "..." }
    },
    "capture-mcp-server": {
      "command": "node",
      "args": ["external/capture-mcp-server/dist/server.js"],
      "env": { "SAM_GOV_API_KEY": "...", "TANGO_API_KEY": "..." }
    },
    "knowledge-base": {
      "command": "python",
      "args": ["-m", "src.knowledge_base.mcp_server"]
    }
  }
}
```

---

## 10. MCP Servers

### 1. n8n-mcp (N8N Workflow Orchestration)
- **Source:** NPM package `n8n-mcp`
- **Purpose:** Orchestrate N8N workflows via Claude Code
- **Capabilities:** Create/update/execute workflows, manage nodes, validation

### 2. capture-mcp-server (Federal Procurement)
- **Source:** `external/capture-mcp-server/`
- **Purpose:** Federal data API integration
- **APIs:** SAM.gov, Tango/MakeGov

### 3. knowledge-base (Custom)
- **Source:** `src/knowledge_base/mcp_server.py`
- **Purpose:** Semantic search across project documentation
- **Tools:** 14 search and categorization tools

---

## 11. External Folder Assets (`external/`)

| Repository | Purpose |
|------------|---------|
| `n8n-mcp/` | N8N MCP server for Claude Code |
| `n8n-skills/` | 7 specialized N8N skills for Claude Code |
| `capture-mcp-server/` | Federal procurement MCP server |
| `tango-python/` | Tango/MakeGov Python SDK |
| `tango-node/` | Tango/MakeGov Node.js SDK |
| `usaspending-api/` | USASpending API reference |
| `SAM.gov-Scripts/` | SAM.gov scraper reference |
| `akshayakula-OpenSAM/` | OpenSAM tool |
| `ataddesse-govConDiscovery/` | Gov contract discovery |
| `govbizops/` | GovBizOps reference |
| `IncrediblyHungie-sam-gov-scraper/` | SAM.gov scraper |
| `ramfrancis0x1-Beacon/` | Beacon tool reference |
| `tommycolitsas-sam/` | SAM.gov reference |
| `Apify Puppeteer Scraper/` | Web scraping datasets |

---

## 12. External Integrations

### N8N Cloud
- **Instance:** https://primetech.app.n8n.cloud/
- **Integration:** MCP server via n8n-mcp
- **Workflows:** 11 active, 26 inactive

### Hub (BD-Automation-Engine)
- **Client:** `hub/hub_integration.py`
- **Capabilities:** Program sync, search, insights, webhook triggers
- **Endpoints:** `/programs`, `/search`, `/insights`, `/webhooks`

### Federal APIs
| API | Purpose | Client |
|-----|---------|--------|
| Tango/MakeGov | Contract discovery | `src/api_clients/tango.py` |
| SAM.gov | Opportunities, entities | `src/api_clients/sam.py` |
| USASpending | Award data | `src/api_clients/usaspending.py` |

### Other Integrations
- **Notion:** Program mapping exports
- **Bullhorn CRM:** Contact and job data
- **ZoomInfo:** Contact targeting

---

## 13. Dependencies

### Python Dependencies (`requirements.txt`)

#### Core
| Package | Purpose |
|---------|---------|
| `python-dotenv>=1.0.0` | Environment variables |
| `pydantic>=2.6.0` | Data validation |
| `pydantic-settings>=2.1.0` | Settings management |

#### HTTP/API
| Package | Purpose |
|---------|---------|
| `requests>=2.31.0` | HTTP client |
| `httpx>=0.27.0` | Async HTTP client |
| `fastapi>=0.109.0` | Web framework |
| `uvicorn>=0.27.0` | ASGI server |

#### Database
| Package | Purpose |
|---------|---------|
| `sqlalchemy>=2.0.0` | ORM |
| `lancedb>=0.3.0` | Vector database |
| `qdrant-client>=1.7.0` | Vector DB (migration target) |

#### Data Processing
| Package | Purpose |
|---------|---------|
| `pandas>=2.0.0` | DataFrames |
| `numpy>=1.24.0` | Numerical computing |

#### AI/LLM
| Package | Purpose |
|---------|---------|
| `anthropic>=0.18.0` | Claude API |
| `openai>=1.12.0` | OpenAI API |
| `langchain-openai>=0.1.0` | LangChain OpenAI |
| `langchain-anthropic>=0.1.0` | LangChain Anthropic |
| `langgraph>=0.1.0` | State machine workflows |
| `sentence-transformers>=2.2.0` | Embeddings |

#### Reliability
| Package | Purpose |
|---------|---------|
| `tenacity>=8.2.0` | Retry logic |
| `structlog>=24.1.0` | Structured logging |

#### Browser Automation
| Package | Purpose |
|---------|---------|
| `browser-use>=0.1.0` | AI browser agent |
| `playwright>=1.40.0` | Browser automation |

---

## 14. Key Workflows

### Contact Enrichment Pipeline
```
Raw Contacts (CSV) → Deduplication → Enrichment →
  Location Mapping → Title Standardization →
  Program Association → Enriched Contacts (CSV)
```

### Federal Program Data Processing
```
Discovery Engines → Raw Programs →
  Phase 1: Task Orders → Phase 2: Locations →
  Phase 3: Org Hierarchy → Phase 4: Technology →
  Master Database (60+ columns)
```

### Knowledge Base Indexing
```
Project Files → Document Processor →
  Chunking → Embedding (sentence-transformers) →
  LanceDB Storage → MCP Server → Claude Code
```

### BD Scoring Pipeline
```
Master Database → 5-Factor Scoring →
  Factor 1: Contract Value (30 pts)
  Factor 2: Subawards (20 pts)
  Factor 3: Hiring (20 pts)
  Factor 4: IT Services (15 pts)
  Factor 5: Recompete (15 pts)
→ Tier Classification → Call Sheet Generation
```

### N8N Automation Workflows
| Workflow | Purpose | Status |
|----------|---------|--------|
| Hub - Search | Intelligence search | Active |
| Hub - Add Insight | Add insights to hub | Active |
| Hub - Ingest Jobs | Job ingestion | Active |
| Hub - Smart Query | AI-powered queries | Active |
| Scraper - Full Pipeline | End-to-end scraping | Active |
| Scraper - Trigger Job Scrape | Trigger scraping | Active |
| Monitor - Health Check | System health | Active |
| Alert - Slack Notification | Slack alerts | Active |
| Pipeline - Competitor Analysis | Competitor tracking | Active |
| Pipeline - BD Intelligence | BD intelligence gen | Active |

---

## 15. Summary Statistics

### Code Volume
| Metric | Count |
|--------|-------|
| Python Scripts | 178 |
| Markdown Docs | 140 |
| CSV Files | 608 |
| JSON Files | 55 |
| N8N Workflows (active) | 11 |
| N8N Workflows (inactive) | 26 |

### Data Volume
| Metric | Count/Size |
|--------|------------|
| Total Data Size | 1.7 GB |
| Knowledge Base Embeddings | 21 MB |
| Output Files | 14 MB |
| Raw Contacts | 16,376 |
| Enriched Contacts | 38,217 |
| Prime Contractors Tracked | 25 |
| Federal Programs (discovered) | 101 |

### Intelligence Modules
| Category | Script Count |
|----------|-------------|
| Discovery Engines | 9 |
| Enrichment Scripts | 11 |
| Intelligence Tools | 30+ |
| Pipeline Scripts | 7 |
| Utility Scripts | 15+ |
| LangGraph Workflows | 12 |
| Browser Automation | 5 |

---

## 16. Current Gaps & Issues

### Configuration Gaps
- [ ] Hub integration requires running BD-Automation-Engine
- [ ] Qdrant migration from LanceDB not completed
- [ ] Some API keys may need refresh

### Incomplete Features
- [ ] Browser automation is experimental (BrowserUse)
- [ ] LangGraph workflows need testing
- [ ] Real-time dashboard not implemented
- [ ] Mobile interface not available

### Cleanup Needed
- [ ] 26 inactive N8N workflows marked for deletion
- [ ] 10 "My workflow" test files should be removed
- [ ] Duplicate PTS BD workflows need consolidation

### Documentation Gaps
- [ ] Some intelligence scripts lack inline documentation
- [ ] Browser automation needs usage guide
- [ ] LangGraph workflow documentation incomplete

### Data Quality
- [ ] Some DoD discovery outputs show empty results (2-byte files)
- [ ] Contact deduplication could be improved
- [ ] Some enriched data may be stale

---

## 17. Quick Reference Commands

### Run Discovery
```bash
cd src/discovery
python federal-programs-discovery-engine-v2.py
# Output: data/federal/DISCOVERED_PROGRAMS_*.csv
```

### Run Enrichment
```bash
cd src/enrichment
python run_enrichment.py  # All 4 phases
# Output: Various enriched CSVs
```

### Generate Master Database
```bash
cd src/pipeline
python merge-and-deduplicate.py
# Output: output/bd_databases/Federal_Programs_MASTER.csv
```

### Generate Intelligence
```bash
cd src/intelligence
python advanced_bd_tools.py
# Output: output/intelligence/*.csv
```

### Index Knowledge Base
```bash
cd src/knowledge_base
python indexer.py
# Output: knowledge-base/embeddings/
```

### Start Knowledge Base MCP Server
```bash
python -m src.knowledge_base.mcp_server
```

---

*Report generated: 2026-02-03*
*N8N-Builder Version: master branch*
