# BD Intelligence Dashboard - Architecture

## System Architecture

```
+------------------+     +------------------+     +------------------+
|  Dashboard (UI)  |     |  Hub API (:8100)  |     |  Qdrant (:6333)  |
|  Vite + React    |<--->|  FastAPI/Python   |<--->|  Vector Database |
|  :5173 (dev)     |     |  140+ endpoints   |     |  1.4M+ vectors   |
+------------------+     +------------------+     +------------------+
        |                        |                        |
        |  Vite Proxy (24 routes)|                        |
        +------------------------+                        |
                                 |     +-----------------+
                                 +---->|  Neo4j (:7687)  |
                                 |     |  Knowledge Graph|
                                 |     +-----------------+
                                 |
                                 |     +-----------------+
                                 +---->|  SQLite (local)  |
                                 |     |  notifications.db|
                                 |     |  bullhorn.db     |
                                 |     +-----------------+
                                 |
+------------------+             |
| Outreach (:8300) |<------------+
| n8n Workflows    |
+------------------+

External Data Sources:
+--------+  +--------+  +----------+  +---------+
| Apify  |  | Tango  |  | ZoomInfo |  | Notion  |
| Scraper|  | SAM.gov|  | Enricher |  | CRM     |
+--------+  +--------+  +----------+  +---------+
     |           |            |             |
     +-----------+------------+-------------+
                 |
          POST /webhooks/*
                 |
          Hub API (:8100)
```

## Data Flow

```
Qdrant (vectors) --> Hub API (FastAPI) --> Vite Proxy --> React Query --> Components --> User

Webhook Flow:
  Scraper -(POST /webhooks/jobs-scraped)--> Hub API
    --> Creates Notification (SQLite)
    --> Updates Freshness Log (JSON)
    --> Dashboard polls /notifications
    --> Bell icon shows unread count
```

## API Endpoints

### Hub API (http://localhost:8100)

#### Health & Stats
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/stats` | System statistics (Qdrant, memory, graph, cache) |
| GET | `/dashboard/stats` | Consolidated dashboard stats |

#### Search
| Method | Path | Description |
|--------|------|-------------|
| GET | `/search?q=&collection=&limit=` | Semantic vector search |
| GET | `/search/hybrid?q=&alpha=` | Hybrid semantic + keyword search |
| GET | `/ask?q=` | RAG question answering |
| GET | `/ask/smart?q=&strategy=` | Smart query with auto-routing |

#### Collections
| Method | Path | Description |
|--------|------|-------------|
| POST | `/contacts/filter` | Filter contacts (query, program, prime, company, clearance) |
| POST | `/programs/filter` | Filter programs (query, prime, agency) |
| GET | `/collections/{name}/search` | Collection-specific search |
| GET | `/collections/{name}/stats` | Collection statistics |

#### Data Freshness (Phase 7)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/data/freshness` | Collection freshness indicators with staleness alerts |

Response:
```json
{
  "collections": {
    "contacts": { "count": 211000, "last_indexed": "2026-02-05T...", "staleness_days": 3, "status": "green" },
    "programs": { "count": 68000, "last_indexed": "2026-01-28T...", "staleness_days": 11, "status": "green" }
  },
  "scraper_last_run": "2026-02-07T...",
  "tango_last_sync": null,
  "alerts": [
    { "level": "warning", "message": "programs collection is 11 days stale" }
  ]
}
```

#### Notifications (Phase 7)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/notifications` | Create notification |
| GET | `/notifications?unread=true&limit=50` | List notifications |
| PATCH | `/notifications/{id}/read` | Mark as read |

Request (POST):
```json
{
  "type": "new_jobs",
  "title": "45 new jobs scraped",
  "message": "Source: Apify, Run: abc123",
  "entity_type": "job",
  "entity_id": null,
  "priority": "info"
}
```

#### Webhooks (Phase 7)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhooks/jobs-scraped` | New jobs scraped |
| POST | `/webhooks/contracts-updated` | Contract modifications |
| POST | `/webhooks/contacts-enriched` | Contact enrichment |
| POST | `/webhooks/alert` | Generic alert |

Example (jobs-scraped):
```json
{ "source": "apify", "count": 45, "run_id": "abc123" }
```

#### AI Memory (Phase 7)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/ai/memories` | Store entity memory |
| GET | `/ai/memories/{type}/{name}` | Get entity memories |
| DELETE | `/ai/memories/{id}` | Delete memory |

Request (POST):
```json
{
  "entity_type": "contact",
  "entity_name": "Kingsley Ero",
  "summary": "Discussed PACAF staffing needs",
  "confidence": 0.9
}
```

#### LLM Costs (Phase 7)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/ai/costs?days=30` | Aggregated LLM cost data |

Response:
```json
{
  "daily": [{ "date": "2026-02-09", "input_tokens": 5000, "output_tokens": 2000, "cost_usd": 0.12, "queries": 5 }],
  "by_endpoint": [{ "endpoint": "/ask/smart", "cost_usd": 0.08 }],
  "summary": { "total_cost_usd": 1.50, "projected_30d_usd": 15.00 }
}
```

#### Knowledge Graph
| Method | Path | Description |
|--------|------|-------------|
| GET | `/bdgraph/program/{name}` | Program ecosystem |
| GET | `/bdgraph/contact/{name}` | Contact network |
| GET | `/bdgraph/teaming/{from}/{to}` | Teaming path |
| GET | `/bdgraph/query?q=` | Graph query |
| GET | `/bdgraph/stats` | Graph statistics |

#### Memory Context
| Method | Path | Description |
|--------|------|-------------|
| GET | `/memory/search?q=&limit=` | Search memories |
| GET | `/memory/entity/{name}` | Entity facts |
| GET | `/memory/insights?type=&limit=` | BD insights |
| GET | `/memory/contact/{name}` | Contact context |
| GET | `/memory/program/{name}` | Program context |

#### Agents
| Method | Path | Description |
|--------|------|-------------|
| GET | `/agent/program?q=` | Program intelligence agent |
| GET | `/agent/company?q=` | Company research agent |
| GET | `/agent/contact?q=` | Contact finder agent |
| GET | `/agent/strategy?q=` | BD strategy agent |
| POST | `/agents/analyze-program` | Multi-agent program analysis |
| POST | `/agents/prepare-outreach` | Outreach preparation |
| POST | `/agents/weekly-intel` | Weekly intel brief |
| GET | `/agents/tasks` | Agent task queue |
| GET | `/agents/status/{id}` | Task status |

#### Pipeline & QA
| Method | Path | Description |
|--------|------|-------------|
| GET | `/pipeline/status` | Pipeline run status |
| POST | `/pipeline/trigger` | Trigger pipeline |
| GET | `/qa/stats` | QA statistics |
| GET | `/qa/review-queue` | QA review items |
| POST | `/qa/review-queue/{id}/resolve` | Resolve QA item |
| GET | `/alerts?limit=` | System alerts |

#### Cache & Indexing
| Method | Path | Description |
|--------|------|-------------|
| GET | `/cache/stats` | Cache statistics |
| POST | `/ingest/document` | Ingest document |
| POST | `/sync/*` | Data synchronization |
| POST | `/index/*` | Indexing operations |

### Outreach API (http://localhost:8300)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/outreach/sequences` | List outreach sequences |
| POST | `/outreach/sequences` | Create sequence |
| GET | `/outreach/contacts` | Outreach contact list |

## Component Hierarchy

```
App
+-- Sidebar
|   +-- NotificationCenter (bell + dropdown)
|   +-- DensityToggle (compact/comfortable/spacious)
|   +-- DarkModeToggle
+-- ErrorBoundary
|   +-- Suspense (code-splitting)
|       +-- [Active Page Component]
+-- CopilotSidebar
+-- DataFreshness (floating indicator)
+-- CommandPalette (Ctrl+K)
```

### Pages (33 total, all lazy-loaded)

| Category | Pages |
|----------|-------|
| **Dashboard** | ExecutiveSummary (+ DataHealthBanner) |
| **Intelligence** | JobIntelligence, JobsPipeline, Programs, Contacts, Contractors, Locations |
| **BD Ops** | BDEvents, Opportunities, EnrichmentDashboard, DailyPlaybook, PastPerformance |
| **Visualization** | MindMap, PrimeOrgChart, ContactOrgChart, KnowledgeGraph, GraphExplorer |
| **Outreach** | OutreachManager, MeetingCalendar, CallIntelligence, AccountTakeover |
| **Operations** | QADashboard, PipelineStatus, Analytics, DataQuality, Placements |
| **Hub AI** | SmartQuery, AgentPanel, MemoryContext, SystemHealth |
| **Detail** | ContactDetail (+ AIMemoryPanel), ProgramDetail (+ AIMemoryPanel) |
| **System** | Settings (+ LLMCostsTab) |

### Shared Components

| Component | Purpose |
|-----------|---------|
| `DataHealthBanner` | Collection freshness indicators (green/yellow/red) |
| `PageFreshnessBadge` | Per-page "Last Refreshed: Xh ago" badge |
| `NotificationCenter` | Bell icon with unread count + dropdown |
| `AIMemoryPanel` | Entity memory CRUD on detail pages |
| `LLMCostsTab` | Token usage charts + cost breakdown |
| `DensityToggle` | Compact/comfortable/spacious UI density |
| `ErrorBoundary` | Per-page error catching with retry |
| `CopilotSidebar` | AI chat sidebar with streaming |
| `CommandPalette` | Ctrl+K quick navigation |
| `Breadcrumb` | Navigation breadcrumbs |

## Data Storage

| Store | Location | Content |
|-------|----------|---------|
| Qdrant | localhost:6333 | 1.4M+ vectors across 12 collections |
| Neo4j | localhost:7687 | Knowledge graph (entities + relationships) |
| SQLite | `data/notifications.db` | Notification center data |
| SQLite | `data/bullhorn_master.db` | Bullhorn CRM ETL |
| JSON | `data/freshness_log.json` | Collection freshness timestamps |
| JSON | `data/llm_costs.json` | LLM token usage and cost log |

### Qdrant Collections

| Collection | Vectors | Content |
|------------|---------|---------|
| documents | ~500K | Documents and PDFs |
| activities | ~446K | BD activities and notes |
| contacts | ~211K | Personnel and contacts |
| federal_contracts | ~108K | Federal contract data |
| programs | ~68K | Federal programs |
| bullhorn_notes | ~51K | CRM notes |
| jobs | ~16K | Job postings |
| intelligence_reports | ~2K | BD reports |
| memories | dynamic | AI entity memories (Phase 7) |

## Environment Variables

### Dashboard (.env / .env.production)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE` | `''` (empty) | Hub API base URL. Empty = use Vite proxy |
| `VITE_HUB_API_URL` | `http://localhost:8100` | Production Hub API URL |
| `VITE_OUTREACH_API_URL` | `http://localhost:8300` | Production Outreach API URL |

### Hub API (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `OPENAI_API_KEY` | Yes | Embeddings |
| `QDRANT_URL` | No | Qdrant server URL (default: localhost:6333) |
| `KNOWLEDGE_API_HOST` | No | API host (default: 127.0.0.1) |
| `KNOWLEDGE_API_PORT` | No | API port (default: 8100) |

## Deployment

### Start All Services

```bash
# 1. Start Qdrant (if not running)
# Already running on localhost:6333

# 2. Start Hub API
cd BD-Automation-Engine
python Engine8_Knowledge/api.py
# Runs on http://localhost:8100

# 3. Start Dashboard (development)
cd dashboard
npm run dev
# Runs on http://localhost:5173

# 4. (Optional) Start Outreach API
# Runs on http://localhost:8300
```

### Production Build

```bash
cd dashboard
npm run build          # TypeScript check + Vite build
npm run preview        # Preview production build locally

# Build output: dashboard/dist/
# Serve with any static file server
```

### Vite Proxy Routes (Development)

24 routes proxied from :5173 to :8100:
```
/api, /health, /stats, /search, /ask, /agents, /memory, /bdgraph
/cache, /qa, /pipeline, /alerts, /rag, /agent, /dify
/collections, /contacts, /programs, /jobs, /ingest, /sync
/index, /dashboard, /documents, /activities, /analytics, /ai, /graph
/notifications, /webhooks
```

1 route proxied to :8300:
```
/outreach
```

## Technology Stack

### Frontend
- React 19.2 + TypeScript 5.9
- Vite 7.2 (build tool)
- TailwindCSS 4.1 (styling)
- TanStack Query 5.90 (data fetching)
- TanStack Table 8.21 (data tables)
- Recharts 3.6 + Tremor 3.18 (charts)
- Zustand 5.0 (state management)
- Framer Motion 12.33 (animations)
- Lucide React (icons)
- React.lazy + Suspense (code splitting)

### Backend
- FastAPI (REST API)
- Python 3.12+
- Qdrant Client (vector search)
- CrewAI (multi-agent orchestration)
- SQLite (notifications, CRM)
- Pydantic (validation)
