# BD INTELLIGENCE HUB - MASTER UTILIZATION GUIDE

## Complete Cheat Sheet for All Projects, Engines, Tools & Processes

**Created:** January 26, 2026  
**Version:** 1.0  
**Purpose:** Quick reference for all BD Intelligence Hub capabilities

---

## SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BD INTELLIGENCE HUB ECOSYSTEM                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│  BD-AUTOMATION-     │     │    DATA-SCRAPER     │     │    N8N-BUILDER      │
│      ENGINE         │     │                     │     │                     │
│   (CENTRAL HUB)     │     │   (DATA WRITER)     │     │   (ORCHESTRATOR)    │
│                     │     │                     │     │                     │
│ • FastAPI :8100     │◄───►│ • Job Scraping      │     │ • n8n Workflows     │
│ • Qdrant Vectors    │     │ • Standardization   │────►│ • Webhooks          │
│ • Mem0 Memory       │     │ • Program Mapping   │     │ • Scheduling        │
│ • LightRAG Graph    │◄────│ • Hub Sync          │     │ • Alerts            │
│ • RAG + Claude      │     │                     │     │                     │
│ • 5 BD Agents       │     └─────────────────────┘     └─────────────────────┘
│ • MCP Server        │                │                          │
└─────────────────────┘                │                          │
         │                             │                          │
         └─────────────────────────────┼──────────────────────────┘
                                       │
                              ┌────────┴────────┐
                              │  CLAUDE CODE    │
                              │   (59+ MCP      │
                              │    Tools)       │
                              └─────────────────┘
```

---

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: BD-AUTOMATION-ENGINE (THE HUB)
# Location: C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine
# ═══════════════════════════════════════════════════════════════════════════

## 1.1 QUICK START

```cmd
cd "C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine"
claude --dangerously-skip-permissions
```

**Start the Hub:**
```
Start the BD Hub API server on port 8100
```

**Or manually:**
```cmd
cd "C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine"
python Engine8_Knowledge/api.py
```

**Verify Running:**
```cmd
curl http://127.0.0.1:8100/health
curl http://127.0.0.1:8100/stats
```

---

## 1.2 API ENDPOINTS REFERENCE

### Health & Stats
| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/health` | GET | Health check | `curl http://127.0.0.1:8100/health` |
| `/stats` | GET | System statistics | `curl http://127.0.0.1:8100/stats` |
| `/docs` | GET | Swagger UI | Open in browser |

### Search & Query
| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/search` | GET | Semantic search | `curl "http://127.0.0.1:8100/search?q=DCGS&collection=programs"` |
| `/ask` | GET | RAG Q&A with Claude | `curl "http://127.0.0.1:8100/ask?q=What programs does GDIT prime?"` |
| `/ask/smart` | GET | Intelligent query routing | `curl "http://127.0.0.1:8100/ask/smart?q=Find Leidos contacts"` |

### Memory Operations
| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/memory/add` | POST | Add memory | `curl -X POST -d '{"content":"..."}' http://127.0.0.1:8100/memory/add` |
| `/memory/search` | GET | Search memories | `curl "http://127.0.0.1:8100/memory/search?q=DCGS"` |

### Knowledge Graph
| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/graph/query` | GET | Query knowledge graph | `curl "http://127.0.0.1:8100/graph/query?q=GDIT relationships"` |
| `/graph/entities` | GET | List entities | `curl http://127.0.0.1:8100/graph/entities` |

### Ingest (for Data-Scraper)
| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/ingest/jobs` | POST | Ingest jobs | POST JSON array of jobs |
| `/ingest/contacts` | POST | Ingest contacts | POST JSON array of contacts |
| `/ingest/programs` | POST | Ingest programs | POST JSON array of programs |

### BD Agents
| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/agent/program` | GET | Program intel agent | `curl "http://127.0.0.1:8100/agent/program?q=Analyze DCGS"` |
| `/agent/company` | GET | Company research agent | `curl "http://127.0.0.1:8100/agent/company?q=Research Leidos"` |
| `/agent/contact` | GET | Contact finder agent | `curl "http://127.0.0.1:8100/agent/contact?q=Find DCGS PMs"` |
| `/agent/strategy` | GET | BD strategy agent | `curl "http://127.0.0.1:8100/agent/strategy?q=Capture plan"` |
| `/agent/competitive` | GET | Competitive intel agent | `curl "http://127.0.0.1:8100/agent/competitive?q=GDIT vs Leidos"` |

### Workflows
| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/workflow/capture` | GET | Generate capture strategy | `curl "http://127.0.0.1:8100/workflow/capture?opportunity=DCGS"` |

---

## 1.3 COLLECTIONS (Qdrant)

| Collection | Records | Description |
|------------|---------|-------------|
| `contacts` | 7,337 | BD contacts from ZoomInfo/LinkedIn |
| `programs` | 401 | Federal programs database |
| `documents` | 205 | Ingested documents |
| `activities` | 500 | BD activities log |
| `jobs` | 4+ | Job postings (grows with scraping) |

**Search a specific collection:**
```cmd
curl "http://127.0.0.1:8100/search?q=network engineer&collection=contacts&limit=10"
```

---

## 1.4 COMPONENTS & ENGINES

### Memory Layer (Mem0)
- **Purpose:** Cross-session context, remembers BD insights
- **Location:** `Engine8_Knowledge/scripts/memory_layer.py`
- **Usage:** Automatic - stores insights from queries

### Knowledge Graph (LightRAG)
- **Purpose:** Entity relationships (companies, programs, contacts)
- **Location:** `Engine8_Knowledge/scripts/lightrag_engine.py`
- **Usage:** Query with `/graph/query?q=...`

### Hybrid Retriever
- **Purpose:** Semantic + BM25 keyword search with reranking
- **Location:** `Engine8_Knowledge/scripts/hybrid_retriever.py`
- **Components:** Qdrant (semantic) + BM25 + CrossEncoder reranking

### Query Router
- **Purpose:** Routes queries to optimal engine
- **Location:** `Engine8_Knowledge/scripts/query_router.py`
- **Query Types:** FACTUAL, RELATIONAL, COMPREHENSIVE, MEMORY, KEYWORD

### 5 BD Agents
| Agent | Purpose | Endpoint |
|-------|---------|----------|
| Program Intel | Federal program analysis | `/agent/program` |
| Company Research | Competitor/partner analysis | `/agent/company` |
| Contact Finder | Key personnel identification | `/agent/contact` |
| BD Strategy | Capture strategy synthesis | `/agent/strategy` |
| Competitive Intel | Competitive landscape | `/agent/competitive` |

---

## 1.5 COMMON TASKS - BD-AUTOMATION-ENGINE

### Task: Search for contacts on a program
```
Search for all contacts who work on DCGS programs at GDIT
```

### Task: Analyze a competitor
```
Use the company research agent to analyze Leidos' DCGS involvement
```

### Task: Generate capture strategy
```
Generate a capture strategy for the AF DCGS program opportunity
```

### Task: Find related entities
```
Query the knowledge graph for all companies connected to DCGS
```

### Task: Load new data into Qdrant
```
Load the file dod-programs-by-target-firms.csv into the programs collection
```

---

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: DATA-SCRAPER (DATA WRITER)
# Location: C:\data-scraper\data-scraper
# ═══════════════════════════════════════════════════════════════════════════

## 2.1 QUICK START

```cmd
cd "C:\data-scraper\data-scraper"
claude --dangerously-skip-permissions
```

**Verify Hub Connection:**
```
Test the connection to the BD Hub at http://127.0.0.1:8100
```

---

## 2.2 DIRECTORY STRUCTURE

```
data-scraper/
├── hub/                    # Hub integration
│   ├── hub_client.py       # API client
│   ├── models.py           # Pydantic models
│   └── sync_pipeline.py    # ETL pipeline
├── pipelines/              # Processing pipelines
│   ├── standardization.py  # Job standardization
│   ├── program_mapper.py   # Program matching
│   ├── contact_extractor.py # NER extraction
│   ├── competitive_intel.py # Competitor analysis
│   └── deduplication.py    # Deduplication
├── apify/                  # Apify scraper management
│   └── apify_manager.py
├── scheduling/             # Job scheduling
│   ├── scheduler.py
│   └── jobs.py
├── notion/                 # Notion sync
│   └── notion_client.py
├── monitoring/             # Logging & alerts
│   ├── logger.py
│   └── alerts.py
├── config/
│   └── programs.yaml       # Federal programs config
├── data/                   # Data storage
│   ├── raw/                # Raw scrape outputs
│   ├── processed/          # Processed data
│   └── cache/              # Dedup cache
└── outputs/                # Generated outputs
    ├── notion/             # Notion exports
    ├── n8n/                # n8n payloads
    └── BD_Briefings/       # BD playbooks
```

---

## 2.3 THE 7-STAGE BD PIPELINE

```
┌─────────┐   ┌─────────────┐   ┌─────────┐   ┌───────┐   ┌───────┐   ┌────────┐   ┌───────────┐
│ INGEST  │──►│ STANDARDIZE │──►│  MATCH  │──►│ SCORE │──►│EXPORT │──►│PLAYBOOK│──►│ HUB SYNC  │
└─────────┘   └─────────────┘   └─────────┘   └───────┘   └───────┘   └────────┘   └───────────┘
   │               │                │            │            │           │             │
   │               │                │            │            │           │             │
 Raw JSON      Claude LLM      Program       BD Score     CSV/JSON    Markdown      POST to
 from Apify    extraction      fuzzy match   (0-100)      exports     playbooks     Hub API
```

### Stage Details:

| Stage | File | What It Does |
|-------|------|--------------|
| 1. INGEST | `hub/sync_pipeline.py` | Load raw JSON from Apify |
| 2. STANDARDIZE | `pipelines/standardization.py` | Claude LLM extracts 18 fields |
| 3. MATCH | `pipelines/program_mapper.py` | Fuzzy match to federal programs |
| 4. SCORE | `pipelines/competitive_intel.py` | BD priority score (0-100) |
| 5. EXPORT | `hub/sync_pipeline.py` | Generate CSV + JSON |
| 6. PLAYBOOK | `hub/sync_pipeline.py` | Generate BD playbooks |
| 7. HUB SYNC | `hub/hub_client.py` | POST to Hub API |

---

## 2.4 COMMON TASKS - DATA-SCRAPER

### Task: Process new Apify JSON files
```
Process the Apify JSON files in data/raw/ through the full 7-stage pipeline and generate:
1. Standardized jobs with all 18 fields
2. Program mappings with confidence scores
3. BD priority scores (Hot/Warm/Cold)
4. Notion-ready CSV export
5. n8n webhook JSON
6. BD playbooks for hot opportunities
```

### Task: Run the full pipeline
```python
from hub.sync_pipeline import run_full_sync
run_full_sync()
```

### Task: Standardize jobs only
```python
from pipelines.standardization import JobStandardizer
standardizer = JobStandardizer()
jobs = standardizer.standardize_jobs(raw_jobs)
```

### Task: Map jobs to programs
```python
from pipelines.program_mapper import ProgramMapper
mapper = ProgramMapper()
mapped = mapper.map_jobs(standardized_jobs)
```

### Task: Generate competitive intelligence
```python
from pipelines.competitive_intel import CompetitiveIntel
intel = CompetitiveIntel()
insights = intel.analyze_hiring_patterns(jobs, "GDIT")
```

### Task: Sync to Hub
```python
from hub.hub_client import get_hub_client
client = get_hub_client()
client.post_jobs(processed_jobs)
```

---

## 2.5 JOB STANDARDIZATION - 18 FIELDS SCHEMA

When processing Apify JSON, jobs are standardized to these fields:

| Field | Description | Source |
|-------|-------------|--------|
| `job_id` | Unique hash ID | Generated |
| `title` | Job title | Extracted |
| `company` | Company name | Extracted |
| `location` | Normalized location | Extracted + normalized |
| `clearance` | Security clearance | Extracted from description |
| `clearance_level` | Enum (none/secret/ts_sci/etc) | Parsed |
| `salary_min` | Minimum salary | Parsed from text |
| `salary_max` | Maximum salary | Parsed from text |
| `employment_type` | Full-time/Contract/etc | Extracted |
| `remote` | Remote work flag | Detected |
| `skills` | Required skills array | Claude LLM extraction |
| `requirements` | Requirements array | Claude LLM extraction |
| `description` | Full description | Original |
| `source` | Source (apex/insight/etc) | From scrape |
| `source_url` | Original URL | From scrape |
| `posted_date` | When posted | Extracted |
| `scraped_at` | When scraped | Timestamp |
| `program_match` | Matched program | From mapper |

---

## 2.6 FEDERAL PROGRAMS CONFIG

**File:** `config/programs.yaml`

```yaml
programs:
  DCGS-A:
    full_name: "Distributed Common Ground System - Army"
    agency: "Army"
    primes: ["Leidos", "General Dynamics"]
    keywords: ["dcgs", "distributed common ground", "ground system"]
    locations: ["Fort Belvoir", "Aberdeen", "Fort Huachuca"]
    clearance: "ts_sci"
    
  DCGS-AF:
    full_name: "Distributed Common Ground System - Air Force"
    agency: "Air Force"
    primes: ["BAE Systems", "GDIT"]
    keywords: ["dcgs", "air force dcgs", "langley", "pacaf"]
    locations: ["Langley", "San Diego", "Wright-Patterson"]
    clearance: "ts_sci"
    
  # ... 11 more programs
```

---

## 2.7 OUTPUT FILES

After running the pipeline, find outputs in:

| Output | Location | Format |
|--------|----------|--------|
| Notion export | `outputs/notion/jobs_export_YYYYMMDD.csv` | CSV |
| n8n webhook | `outputs/n8n/jobs_webhook_YYYYMMDD.json` | JSON |
| BD Playbooks | `outputs/BD_Briefings/*.md` | Markdown |
| Processing log | `outputs/logs/pipeline_YYYYMMDD.log` | Text |

---

## 2.8 PROCESSING APIFY JSON - STEP BY STEP

### Step 1: Place raw files
```
C:\data-scraper\data-scraper\data\raw\
├── apex_jobs_20260126.json
└── insight_global_jobs_20260126.json
```

### Step 2: Run processing
```
Process all JSON files in data/raw/ through the full BD pipeline:
- Parse and extract all fields including description parsing
- Standardize to 18-field schema
- Match to federal programs
- Score for BD priority
- Generate Excel/CSV with all column headers
- Create BD Intelligence Document
- Sync to Hub
```

### Step 3: Collect outputs
```
outputs/
├── notion/jobs_export_20260126.csv      # Full spreadsheet
├── n8n/jobs_webhook_20260126.json       # Webhook payload
└── BD_Briefings/                         # Individual playbooks
    ├── DCGS_Senior_Engineer_Playbook.md
    └── ...
```

---

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: N8N-BUILDER (ORCHESTRATOR)
# Location: C:\N8N Builder
# ═══════════════════════════════════════════════════════════════════════════

## 3.1 QUICK START

```cmd
cd "C:\N8N Builder"
claude --dangerously-skip-permissions
```

**n8n Cloud:** https://primetech.app.n8n.cloud

---

## 3.2 WORKFLOWS REFERENCE

### Hub Integration Workflows
| Workflow | Webhook | Purpose |
|----------|---------|---------|
| Hub - Smart Query | `/webhook/hub-query` | Query Hub with routing |
| Hub - Search | `/webhook/hub-search` | Search Hub collections |
| Hub - Add Insight | `/webhook/add-insight` | Add BD insights |
| Hub - Ingest Jobs | `/webhook/ingest-jobs` | Bulk ingest jobs |

### Scraper Workflows
| Workflow | Webhook | Purpose |
|----------|---------|---------|
| Trigger Job Scrape | `/webhook/trigger-scrape` | Trigger single scraper |
| Full Pipeline | `/webhook/full-pipeline` | Run complete pipeline |
| Scraper Webhook | `/webhook/scraper-complete` | Callback handler |

### BD Pipeline Workflows
| Workflow | Webhook | Purpose |
|----------|---------|---------|
| BD Intelligence Pipeline | `/webhook/bd-pipeline` | Full BD analysis |
| Competitor Analysis | `/webhook/competitor-analysis` | Multi-competitor analysis |

### Alert Workflows
| Workflow | Webhook | Purpose |
|----------|---------|---------|
| Slack Notification | `/webhook/slack-alert` | Send alerts |
| Error Notification | (Error trigger) | Error logging |

### Scheduled Workflows
| Workflow | Schedule | Purpose |
|----------|----------|---------|
| Daily Scrape | 6 AM daily | Automated scraping |
| Weekly Report | Monday 9 AM | Weekly summary |
| Health Check | Every 15 min | Monitor Hub health |

---

## 3.3 ACTIVATING WEBHOOKS

**⚠️ IMPORTANT:** Webhooks must be manually activated in n8n Cloud UI!

1. Go to https://primetech.app.n8n.cloud
2. Open each workflow
3. Toggle activation switch OFF then ON
4. This registers the webhook URL

---

## 3.4 CALLING WEBHOOKS

### Query the Hub via n8n:
```bash
curl -X POST "https://primetech.app.n8n.cloud/webhook/hub-query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Find DCGS contacts at Leidos"}'
```

### Trigger a scrape:
```bash
curl -X POST "https://primetech.app.n8n.cloud/webhook/trigger-scrape" \
  -H "Content-Type: application/json" \
  -d '{"source": "apex-jobs", "max_items": 100}'
```

### Send a Slack alert:
```bash
curl -X POST "https://primetech.app.n8n.cloud/webhook/slack-alert" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hot opportunity found!", "severity": "critical"}'
```

---

## 3.5 MCP TOOLS (14 Tools)

Available when MCP server is configured:

| Tool | Description |
|------|-------------|
| `hub_smart_query` | Query Hub with intelligent routing |
| `hub_search` | Search Hub collections |
| `hub_ingest_jobs` | Ingest jobs to Hub |
| `hub_add_insight` | Add BD insight |
| `trigger_scraper` | Trigger job scraper |
| `trigger_full_pipeline` | Run full pipeline |
| `run_bd_pipeline` | Run BD analysis pipeline |
| `run_competitor_analysis` | Analyze competitors |
| `send_slack_alert` | Send Slack notification |
| `log_error` | Log error to Hub |
| `sync_jobs_to_notion` | Sync to Notion |
| `get_workflow_status` | Get workflow status |
| `list_workflows` | List all workflows |
| `trigger_workflow` | Trigger specific workflow |

---

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: END-TO-END WORKFLOWS
# ═══════════════════════════════════════════════════════════════════════════

## 4.1 DAILY JOB INTELLIGENCE WORKFLOW

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   SCRAPE     │───►│   PROCESS    │───►│   ANALYZE    │───►│   OUTPUT     │
│              │    │              │    │              │    │              │
│ Apify actors │    │ Data-Scraper │    │ BD Hub       │    │ Documents    │
│ Apex/Insight │    │ 7-stage pipe │    │ Agents       │    │ Playbooks    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### Step-by-Step:

1. **Run Apify scrapers** (manually or via n8n schedule)
2. **Download JSON** to `data-scraper/data/raw/`
3. **Process via pipeline** in Data-Scraper terminal
4. **Review outputs** in `outputs/` folder
5. **Query Hub** for analysis
6. **Generate playbooks** for hot opportunities

---

## 4.2 COMPETITOR INTELLIGENCE WORKFLOW

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  SCRAPE      │───►│  ANALYZE     │───►│  REPORT      │
│  JOBS        │    │  PATTERNS    │    │  FINDINGS    │
│              │    │              │    │              │
│ Target firms │    │ Hiring trend │    │ BD Intel doc │
│ job boards   │    │ Program map  │    │ Slack alert  │
└──────────────┘    └──────────────┘    └──────────────┘
```

### Quick Command:
```
Analyze hiring patterns for GDIT, Leidos, and BAE Systems on DCGS programs
```

---

## 4.3 CAPTURE STRATEGY WORKFLOW

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  IDENTIFY    │───►│  RESEARCH    │───►│  ANALYZE     │───►│  STRATEGY    │
│  OPPORTUNITY │    │  PROGRAM     │    │  COMPETITION │    │  DOCUMENT    │
│              │    │              │    │              │    │              │
│ From jobs or │    │ Hub program  │    │ Company      │    │ Playbook     │
│ SAM.gov      │    │ agent        │    │ agent        │    │ Call script  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### Quick Command:
```
Generate a complete capture strategy for AF DCGS - Langley including:
- Program intelligence
- Key contacts
- Competitive landscape
- Pain points
- Action plan with timeline
- Call script for initial outreach
```

---

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: MCP SERVER CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

## 5.1 CLAUDE DESKTOP CONFIGURATION

Add to your Claude Desktop config file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bd-intelligence-hub": {
      "command": "node",
      "args": ["C:/Users/gtmar/Projects/Auto-Claude/BD-Automation-Engine/mcp/knowledge-mcp-server/build/index.js"]
    },
    "data-scraper": {
      "command": "node", 
      "args": ["C:/data-scraper/data-scraper/mcp/data-scraper-mcp/build/index.js"]
    },
    "n8n-orchestrator": {
      "command": "node",
      "args": ["C:/N8N Builder/mcp/n8n-orchestrator-mcp/build/index.js"],
      "env": {
        "N8N_CLOUD_URL": "https://primetech.app.n8n.cloud",
        "N8N_API_KEY": "your_n8n_api_key"
      }
    }
  }
}
```

---

## 5.2 TOTAL MCP TOOLS AVAILABLE

| Server | Tools | Category |
|--------|-------|----------|
| BD Hub | 30+ | Search, memory, graph, agents, ingest |
| Data-Scraper | 15 | Scraping, pipeline, sync, intel |
| N8N Orchestrator | 14 | Workflows, webhooks, alerts |
| **TOTAL** | **59+** | |

---

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: QUICK REFERENCE COMMANDS
# ═══════════════════════════════════════════════════════════════════════════

## 6.1 STARTING THE SYSTEM

```cmd
# Terminal 1: Start Hub
cd "C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine"
python Engine8_Knowledge/api.py

# Terminal 2: Data-Scraper (when needed)
cd "C:\data-scraper\data-scraper"
claude --dangerously-skip-permissions

# Terminal 3: N8N Builder (when needed)
cd "C:\N8N Builder"
claude --dangerously-skip-permissions
```

## 6.2 HEALTH CHECKS

```cmd
# Hub health
curl http://127.0.0.1:8100/health

# Hub stats
curl http://127.0.0.1:8100/stats

# Hub docs
start http://127.0.0.1:8100/docs
```

## 6.3 COMMON SEARCHES

```cmd
# Search contacts
curl "http://127.0.0.1:8100/search?q=program manager DCGS&collection=contacts&limit=10"

# Search programs
curl "http://127.0.0.1:8100/search?q=GDIT prime&collection=programs&limit=10"

# Smart query
curl "http://127.0.0.1:8100/ask/smart?q=Who are the key contacts at Leidos for DCGS"
```

## 6.4 AGENT QUERIES

```cmd
# Program analysis
curl "http://127.0.0.1:8100/agent/program?q=Analyze AF DCGS opportunity"

# Company research
curl "http://127.0.0.1:8100/agent/company?q=Research GDIT DCGS involvement"

# Competitive intel
curl "http://127.0.0.1:8100/agent/competitive?q=Compare GDIT vs Leidos on DCGS"
```

---

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: ENVIRONMENT VARIABLES
# ═══════════════════════════════════════════════════════════════════════════

## BD-Automation-Engine/.env
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
QDRANT_PATH=./qdrant_data
```

## data-scraper/.env
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
APIFY_API_TOKEN=apify_api_xxxxx
BD_HUB_URL=http://127.0.0.1:8100
NOTION_API_KEY=secret_xxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/xxxxx
```

## N8N Builder/.env
```env
N8N_CLOUD_URL=https://primetech.app.n8n.cloud
N8N_API_KEY=xxxxx
BD_HUB_URL=http://127.0.0.1:8100
```

---

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8: TROUBLESHOOTING
# ═══════════════════════════════════════════════════════════════════════════

## Hub won't start
```cmd
# Check if port 8100 is in use
netstat -ano | findstr :8100

# Kill process
taskkill /PID <pid> /F

# Remove Qdrant lock
del "C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine\Engine8_Knowledge\data\qdrant\.lock"
```

## API key errors
- Check `.env` file has correct key
- Ensure Anthropic account has credits
- Restart the server after changing `.env`

## Hub returns no results
- Check collection name is correct
- Verify data is indexed: `curl http://127.0.0.1:8100/stats`
- Try broader search terms

## n8n webhooks return 404
- Webhooks need manual UI activation
- Go to n8n Cloud → Toggle each workflow OFF then ON

---

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 9: DATA INVENTORY
# ═══════════════════════════════════════════════════════════════════════════

## Current Indexed Data

| Collection | Count | Description |
|------------|-------|-------------|
| contacts | 7,337 | BD contacts (ZoomInfo/LinkedIn) |
| programs | 401 | Federal programs |
| documents | 205 | Ingested documents |
| activities | 500 | BD activity logs |
| jobs | 4+ | Job postings |
| **Total** | **8,447+** | |

## Recent Discoveries

| Dataset | Records | Location |
|---------|---------|----------|
| DoD Programs (Target Firms) | 131 | `dod-programs-by-target-firms.csv` |
| Subawards Scanned | 110,000 | SAM.gov API |

---

# END OF MASTER UTILIZATION GUIDE

**Bookmark this document for quick reference!**

**Last Updated:** January 26, 2026
