# PTS BD INTELLIGENCE ECOSYSTEM
## Master Architecture & Integration Guide

**Generated:** January 26, 2026  
**Based on:** Comprehensive capability audits of all 3 project terminals

---

## EXECUTIVE SUMMARY

You have built a **production-grade Federal Business Development Intelligence Platform** spread across three project terminals. Despite their original names, each project has evolved into a specialized component of a larger ecosystem:

| Terminal | Original Name | Actual Role | Status |
|----------|---------------|-------------|--------|
| **Terminal 1** | BD-Automation-Engine | Central Intelligence Hub + API Gateway | ✅ 85% Operational |
| **Terminal 2** | Data-Scraper | Data Collection + Knowledge Base | ✅ 64% Operational |
| **Terminal 3** | N8N-Builder | Contract Intelligence + Sales Enablement | ✅ 75% Operational |

**Combined Scale:**
- 3M+ data records
- 4.6GB federal contract data
- 8,447 vector embeddings
- 1,000-1,400 federal programs tracked
- 40K+ CRM records analyzed
- 50+ API endpoints
- 37 N8N workflows (10 active)

---

## SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PTS BD INTELLIGENCE ECOSYSTEM                        │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
                    │    BD-AUTOMATION-ENGINE (Hub)       │
                    │         Terminal 1                   │
                    │    ════════════════════════         │
                    │                                      │
                    │  ┌─────────────────────────────┐    │
                    │  │     FastAPI Server          │    │
                    │  │     localhost:8100          │    │
                    │  │     50+ endpoints           │    │
                    │  └─────────────────────────────┘    │
                    │                                      │
                    │  ┌──────────┐  ┌──────────┐         │
                    │  │ Qdrant   │  │ LightRAG │         │
                    │  │ 8,447    │  │ Graph    │         │
                    │  │ vectors  │  │ Store    │         │
                    │  └──────────┘  └──────────┘         │
                    │                                      │
                    │  ┌──────────┐  ┌──────────┐         │
                    │  │ Mem0     │  │ BM25     │         │
                    │  │ Memory   │  │ Hybrid   │         │
                    │  └──────────┘  └──────────┘         │
                    │                                      │
                    │  ┌─────────────────────────────┐    │
                    │  │  AI Enrichment Pipeline     │    │
                    │  │  Claude + Pydantic + NER    │    │
                    │  └─────────────────────────────┘    │
                    │                                      │
                    └─────────────────┬───────────────────┘
                                      │
                                      │ REST API / Webhooks
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
         ▼                            ▼                            ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   DATA-SCRAPER      │    │    N8N-BUILDER      │    │   EXTERNAL SYSTEMS  │
│    Terminal 2       │    │     Terminal 3      │    │                     │
│  ════════════════   │    │  ════════════════   │    │  ════════════════   │
│                     │    │                     │    │                     │
│  Data Collection:   │    │  Intelligence Gen:  │    │  • Notion (8 DBs)   │
│  • Apify Scraping   │    │  • Contract Discover│    │  • Bullhorn CRM     │
│  • USASpending API  │    │  • BD Scoring       │    │  • ZoomInfo         │
│  • FPDS API         │    │  • Competitor Intel │    │  • LinkedIn         │
│  • SAM.gov API      │    │  • Playbooks/Cards  │    │  • Apify Cloud      │
│  • Tango API        │    │  • Territory Mgmt   │    │  • OpenAI           │
│                     │    │                     │    │  • Anthropic        │
│  Knowledge Base:    │    │  N8N Automation:    │    │                     │
│  • 36 Programs      │    │  • 10 Active WFs    │    │                     │
│  • SQLite DBs       │    │  • Hub Integration  │    │                     │
│  • Vector Index     │    │  • Webhook Triggers │    │                     │
│                     │    │                     │    │                     │
│  MCP Servers:       │    │  Bullhorn Intel:    │    │                     │
│  • capture-mcp      │    │  • 268 Files        │    │                     │
│  • scraper-mcp      │    │  • Battlecards      │    │                     │
│                     │    │  • Meeting Prep     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

---

## DATA FLOW ARCHITECTURE

### Primary Data Pipeline

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           DATA COLLECTION LAYER                               │
│                          (Data-Scraper Terminal)                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Apify     │  │ USASpending │  │    FPDS     │  │   SAM.gov   │         │
│  │  Scraper    │  │    API      │  │    API      │  │    API      │         │
│  │  ─────────  │  │  ─────────  │  │  ─────────  │  │  ─────────  │         │
│  │ Job Boards: │  │ • Awards    │  │ • Contracts │  │ • Opps      │         │
│  │ • Apex      │  │ • Subawards │  │ • Vendors   │  │ • Entities  │         │
│  │ • Insight   │  │ • Recipients│  │ • History   │  │ • Exclusions│         │
│  │ • TEKsystems│  │ • IDVs      │  │             │  │             │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                │                 │
│         └────────────────┴────────────────┴────────────────┘                 │
│                                    │                                          │
│                                    ▼                                          │
│                    ┌─────────────────────────────┐                            │
│                    │     Knowledge Base          │                            │
│                    │  ────────────────────────   │                            │
│                    │  • 36 Program Folders       │                            │
│                    │  • knowledge.db (SQLite)    │                            │
│                    │  • Vector Embeddings        │                            │
│                    │  • 4.6GB Contract Data      │                            │
│                    └──────────────┬──────────────┘                            │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                                   │ Hub Sync (hub_jobs_*.json)
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         INTELLIGENCE HUB LAYER                                │
│                       (BD-Automation-Engine Terminal)                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                      PROCESSING PIPELINE                             │     │
│  │  ───────────────────────────────────────────────────────────────     │     │
│  │                                                                      │     │
│  │  [INGEST] → [PARSE] → [ENRICH] → [MAP] → [SCORE] → [INDEX] → [OUT]  │     │
│  │     │         │         │         │        │         │         │     │     │
│  │   Raw      LLM       AI +      Program   BD      Qdrant    Notion   │     │
│  │   JSON    Extract   Relat     Mapping  Priority  Vector    + n8n    │     │
│  │                                                                      │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                               │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                     │
│  │   Qdrant      │  │   LightRAG    │  │    Mem0       │                     │
│  │  ──────────   │  │  ──────────   │  │  ──────────   │                     │
│  │  8,447 vecs   │  │  Knowledge    │  │   Memory      │                     │
│  │  • jobs: 262  │  │  Graph        │  │   Layer       │                     │
│  │  • contacts:  │  │               │  │               │                     │
│  │    7,337      │  │               │  │               │                     │
│  │  • programs:  │  │               │  │               │                     │
│  │    401        │  │               │  │               │                     │
│  └───────────────┘  └───────────────┘  └───────────────┘                     │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                      FastAPI ENDPOINTS (50+)                         │     │
│  │  • /search - Semantic search                                         │     │
│  │  • /ask/smart - RAG queries                                          │     │
│  │  • /ingest/jobs - Job ingestion                                      │     │
│  │  • /memory/* - Memory operations                                     │     │
│  │  • /contacts/* - Contact queries                                     │     │
│  │  • /programs/* - Program queries                                     │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                                   │ Webhooks / API Calls
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                       INTELLIGENCE OUTPUT LAYER                               │
│                         (N8N-Builder Terminal)                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                 CONTRACT INTELLIGENCE ENGINE                         │     │
│  │  ───────────────────────────────────────────────────────────────     │     │
│  │                                                                      │     │
│  │  Discovery Engines:           Enrichment Phases:                     │     │
│  │  • Federal Programs V2        • Phase 1: Task Orders                 │     │
│  │  • DoD Staffing               • Phase 2: Locations                   │     │
│  │  • High Sub-Spend             • Phase 3: Org Hierarchy               │     │
│  │                               • Phase 4: Technologies                │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                               │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                     │
│  │  BD Scoring   │  │  Battlecards  │  │  Playbooks    │                     │
│  │  ──────────   │  │  ──────────   │  │  ──────────   │                     │
│  │  3-Tier       │  │  21 Files     │  │  32 Files     │                     │
│  │  Priority     │  │  Per Compet.  │  │  Per Company  │                     │
│  └───────────────┘  └───────────────┘  └───────────────┘                     │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                    N8N WORKFLOW AUTOMATION                           │     │
│  │  • 10 Active Workflows (scraping, monitoring, hub integration)       │     │
│  │  • Webhook triggers for real-time processing                         │     │
│  │  • Slack notifications and alerts                                    │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                    SALES ENABLEMENT OUTPUTS                          │     │
│  │  • 51 Meeting Prep Files                                             │     │
│  │  • 268 Bullhorn Intelligence Files                                   │     │
│  │  • Territory Management & Virgin Territory Analysis                  │     │
│  │  • Email Campaign Templates                                          │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## PROJECT ROLE DEFINITIONS

### Terminal 1: BD-Automation-Engine
**Actual Role:** Central Intelligence Hub + API Gateway

| Function | Description | Status |
|----------|-------------|--------|
| **API Gateway** | FastAPI server on :8100 with 50+ endpoints | ✅ Active |
| **Vector Storage** | Qdrant with 8,447 embeddings across 5 collections | ✅ Active |
| **RAG Engine** | LightRAG + BM25 hybrid search | ⚠️ Partial |
| **Memory Layer** | Mem0 for conversation/context memory | ⚠️ Partial |
| **AI Pipeline** | Job enrichment via Claude + Pydantic | ✅ Active |
| **Output Generator** | BD Playbooks, Call Scripts, Reports | ✅ Active |
| **Integration Hub** | Notion sync, n8n webhooks, MCP server | ✅ Active |

**Key Outputs:**
- 186+ processed output files
- 40+ BD briefings generated
- 8,447 vectors indexed
- 500+ jobs processed

---

### Terminal 2: Data-Scraper
**Actual Role:** Data Collection + Knowledge Base

| Function | Description | Status |
|----------|-------------|--------|
| **Job Scraping** | Apify Puppeteer scraper for staffing sites | ✅ Active |
| **Federal APIs** | USASpending, FPDS, SAM.gov, Tango integration | ✅ Active |
| **Knowledge Base** | 36 program folders with contacts, contracts, intel | ✅ Active |
| **CRM Processing** | Bullhorn analysis, past performance DB | ✅ Complete |
| **Contact Intel** | ZoomInfo exports by clearance, region, company | ✅ Complete |
| **MCP Servers** | capture-mcp (15 tools), scraper-mcp | ✅ Ready |
| **Hub Sync** | Daily hub_jobs_*.json exports to Hub | ✅ Active |

**Key Data Assets:**
- 4.6GB federal contract data
- 38K+ CRM records
- 36 program knowledge folders
- 3M+ total data records

---

### Terminal 3: N8N-Builder
**Actual Role:** Contract Intelligence + Sales Enablement

| Function | Description | Status |
|----------|-------------|--------|
| **Contract Discovery** | 3 discovery engines, 1,000-1,400 programs | ✅ Active |
| **4-Phase Enrichment** | Task orders, locations, hierarchy, tech | ✅ Active |
| **BD Scoring** | Automated 3-tier priority system | ✅ Active |
| **Competitor Intel** | Battlecards for 10+ prime contractors | ✅ Complete |
| **Bullhorn Analysis** | 268 files: playbooks, meeting prep, alerts | ✅ Complete |
| **N8N Automation** | 10 active workflows, webhook triggers | ✅ Active |
| **Sales Enablement** | Territory mgmt, email campaigns, call sheets | ✅ Active |

**Key Outputs:**
- 447+ output files generated
- 1,000-1,400 federal programs tracked
- 268 Bullhorn intelligence files
- 21 competitor battlecards

---

## INTEGRATION POINTS

### Hub ↔ Data-Scraper

| Integration | Method | Data Flow |
|-------------|--------|-----------|
| Job Ingestion | hub_jobs_*.json | Scraper → Hub |
| Knowledge Queries | MCP Server | Hub ↔ Scraper |
| Program Data | API/Export | Scraper → Hub |
| Contact Sync | JSON Export | Scraper → Hub |

**Connection:**
```python
# Data-Scraper → Hub
BD_HUB_URL = "http://localhost:8100"
POST /ingest/jobs  # Send scraped jobs
GET  /search       # Query indexed data
```

### Hub ↔ N8N-Builder

| Integration | Method | Data Flow |
|-------------|--------|-----------|
| Webhook Triggers | HTTP POST | Hub ↔ N8N |
| Job Scrape Trigger | Webhook | N8N → Hub |
| Intelligence Query | API | N8N → Hub |
| Alert Notifications | Slack | N8N → External |

**Active Workflows:**
- Hub - Search
- Hub - Add Insight
- Hub - Ingest Jobs
- Hub - Smart Query
- Scraper - Trigger Job Scrape

### Data-Scraper ↔ N8N-Builder

| Integration | Method | Data Flow |
|-------------|--------|-----------|
| Federal Contract Data | File Export | Scraper → Builder |
| Program Intelligence | CSV | Scraper → Builder |
| Enrichment Results | JSON | Builder → Scraper |

---

## CAPABILITY MATRIX

### What's Working (Keep)

| Capability | Terminal | Evidence |
|------------|----------|----------|
| Job Scraping (Apify) | All | 18+ datasets, 500+ jobs |
| AI Enrichment (Claude) | Hub | engine1_ai_enriched.json |
| Vector Search (Qdrant) | Hub | 8,447 vectors |
| Program Mapping | Hub + Scraper | Jobs_Mapped_to_Programs |
| Contact Classification | Hub | contact_scores_*.csv |
| BD Playbook Generation | Hub | 40+ BD_Briefings |
| Notion Integration | Hub | 20+ exports |
| N8N Webhooks | Hub + Builder | 10 active workflows |
| Federal APIs | Scraper | 66 cached queries |
| Knowledge Base | Scraper | 36 program folders |
| Contract Discovery | Builder | 1,400 programs |
| Competitor Battlecards | Builder | 21 files |
| Bullhorn Intelligence | Builder | 268 files |

### What's Partial (Fix or Skip)

| Capability | Terminal | Issue | Recommendation |
|------------|----------|-------|----------------|
| Mem0 Memory | Hub | Occasional errors | Fix config |
| LightRAG Graph | Hub | Not exposed via API | Add endpoint |
| BM25 Hybrid | Hub | Code exists, not exposed | Add endpoint |
| spaCy NER | Hub | Installed, not used | Integrate or remove |
| RAGAS Evaluation | Hub | Framework ready | Run tests or remove |

### What's Redundant (Remove)

| Capability | Terminal | Reason |
|------------|----------|--------|
| ChromaDB | Hub | Using Qdrant |
| Firecrawl | Hub | Using Apify |
| Crawl4AI | Hub | Using Apify |
| 27 Inactive N8N Workflows | Builder | Clutter |

---

## RECOMMENDED PROJECT NAMES

Based on actual functionality:

| Current Name | Recommended Name | Reason |
|--------------|------------------|--------|
| BD-Automation-Engine | **PTS Intelligence Hub** | It's the central API + vector + RAG hub |
| Data-Scraper | **PTS Data Platform** | Data collection + knowledge base |
| N8N-Builder | **PTS Contract Intelligence** | Federal contract BD + sales enablement |

---

## OPERATIONAL STATUS

### Daily Operations

| Time | Action | Terminal | Automation |
|------|--------|----------|------------|
| Morning | Job scrape trigger | Scraper | Manual/N8N |
| Morning | Hub sync | Hub | Webhook |
| Ongoing | RAG queries | Hub | API |
| Ongoing | Notion sync | Hub | On-demand |
| Daily | Intelligence reports | Builder | Manual |

### Weekly Operations

| Day | Action | Terminal |
|-----|--------|----------|
| Monday | BD call sheet generation | Hub |
| Monday | Program intelligence refresh | Builder |
| Wednesday | Contract discovery run | Builder |
| Friday | Competitor intelligence update | Builder |

---

## QUICK REFERENCE

### API Endpoints (Hub - localhost:8100)

```
GET  /health              - Health check
GET  /search?q=<query>    - Semantic search
GET  /ask/smart?q=<query> - RAG query
POST /ingest/jobs         - Ingest job data
POST /memory/add          - Add memory
GET  /contacts?program=X  - Query contacts
GET  /programs            - List programs
```

### MCP Servers

| Server | Location | Tools |
|--------|----------|-------|
| Hub MCP | BD-Automation-Engine | Knowledge queries |
| Capture MCP | Data-Scraper | 15 federal API tools |
| Scraper MCP | Data-Scraper | Scrape triggers |

### Key File Locations

| Asset | Terminal | Path |
|-------|----------|------|
| Vector DB | Hub | Engine8_Knowledge/data/qdrant/ |
| Knowledge Base | Scraper | knowledge/programs/ |
| Contract Data | Scraper | data/input/FY(All)_*.csv |
| Bullhorn Intel | Builder | output/intelligence/bullhorn/ |
| BD Outputs | Hub | outputs/BD_Briefings/ |
| N8N Workflows | Builder | workflows/ |

---

## NEXT STEPS

### Immediate (This Week)

1. **Set environment variables in Data-Scraper**
   - BD_HUB_URL, ANTHROPIC_API_KEY, NOTION_API_KEY

2. **Install missing packages in Data-Scraper**
   - `pip install apify-client apscheduler`

3. **Test Hub connectivity from all terminals**
   - Verify localhost:8100 is accessible

### Short-Term (This Month)

4. **Expose LightRAG and BM25 via API endpoints**
5. **Clean up 27 inactive N8N workflows**
6. **Create unified Pydantic schemas across projects**

### Optional (Evaluate Need)

7. **Integrate spaCy NER** (if needed for entity extraction)
8. **Run RAGAS evaluation** (if measuring RAG quality)
9. **Connect Docling** (if processing PDFs)

---

*Document generated: January 26, 2026*
*Based on comprehensive capability audits of all 3 project terminals*
