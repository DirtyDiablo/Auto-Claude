# PTS BD Intelligence Dashboard — Complete Implementation Guide v5.0

> **Document Purpose**: Full implementation specification for building a Palantir-grade BD Intelligence Dashboard across 3 Auto-Claude terminals
> **Date**: February 7, 2026
> **Follows**: V4 Architecture Completion + Dashboard Research Report

---

## SECTION 1: CLAUDE SESSION SETUP

### Chat Configuration

| Setting | Value | Why |
|---------|-------|-----|
| **Model** | Claude Opus 4 (claude-opus-4-5-20250929) | Most capable for architecture + code generation |
| **Extended Thinking** | **ON** — Budget: HIGH | Complex multi-file code generation needs deep reasoning |
| **Web Search** | **ON** | For resolving npm package APIs, latest docs |
| **Code Execution** | **ON** | For generating and testing implementation files |
| **Artifacts** | **ON** | For architecture diagrams and visual outputs |
| **Memory** | **ON** | For continuity across long sessions |
| **Style** | Default (no custom style) | Technical precision over creative flair |

### Project Knowledge to Attach

Upload these files to the Claude Project (in this priority order):

1. **This document** (`PTS_BD_Dashboard_Implementation_v5.md`) — master reference
2. `Building_a_Palantir-Grade_BD_Intelligence_Dashboard_on_Your_Existing_Stack.md` — the research report
3. `PTS_BD_Platform_Implementation_Handoff.docx` — current architecture state
4. `Auto_Claude_Implementation_Prompts_FINAL_v3.md` — terminal prompt patterns
5. `BD_Intelligence_System_Handoff_Document.md` — data schema reference
6. `DCGS_BD_Custom_Instructions_V3.md` — BD methodology reference

### MCP Connections to Enable

- **Notion** — For reading/writing DCGS Contacts, Programs, Jobs databases
- **n8n** — For workflow triggers (if still connected)

---

## SECTION 2: PRE-IMPLEMENTATION CHECKLIST

Complete these BEFORE starting any terminal prompts.

### ✅ Infrastructure Verification

```bash
# Run from any terminal with access to localhost

# 1. Qdrant is running and healthy
curl -s http://localhost:6333/collections | python -c "import sys,json; d=json.load(sys.stdin); print(f'Collections: {len(d[\"result\"][\"collections\"])}')"
# Expected: Collections: 12+

# 2. Hub API is running
curl -s http://localhost:8100/health
# Expected: {"status":"healthy"}

# 3. Neo4j is running
curl -s http://localhost:7474
# Expected: HTML response (Neo4j browser)

# 4. Node.js version
node --version
# Expected: v20+ (v22 preferred)

# 5. npm packages available globally
npm list -g docx
# If missing: npm install -g docx
```

### ✅ Qdrant State (Verified Feb 7, 2026)

| Collection | Vectors | Status | Payload Indexes |
|---|---|---|---|
| documents | 499,750 | GREEN | 7 |
| activities | 445,972 | GREEN | 6 |
| contacts | 211,267 | GREEN | 7 |
| federal_contracts | 107,902 | GREEN | 6 |
| programs | 68,103 | GREEN | 6 |
| bullhorn_notes | 50,710 | GREEN | 6 |
| jobs | 15,997 | GREEN | 6 |
| intelligence_reports | 2,229 | GREEN | varies |
| bd_memories | 2 | GREEN | 4 |
| **TOTAL** | **~1,401,932** | | |

### ✅ API Endpoints Available (Hub :8100)

| Category | Endpoints | Status |
|---|---|---|
| Health/Stats | GET /health, GET /stats, GET /collections | ✅ Verified |
| Search | POST /search, POST /ask/smart | ✅ Verified |
| Agents | POST /agents/research, POST /agents/outreach, POST /agents/weekly-intel, GET /agents/tasks, GET /agents/status/{id} | ✅ Verified |
| Documents | POST /ingest/document, POST /documents/upload | ✅ Verified |
| Graphiti | POST /graphiti/ingest, POST /graphiti/search | ✅ Verified |
| Mem0 | Integrated into agent workflows | ✅ Verified |
| Collections | GET /collections/{name}, POST /collections/{name}/search | ✅ Available |
| Streaming | Various SSE endpoints | ✅ Available |

### ✅ CrewAI Agents Available

| Agent | Model | Tools | Structured Output |
|---|---|---|---|
| program_researcher | GPT-4o | programs, contracts, documents, graphiti | ProgramIntelligence |
| contact_enricher | GPT-4o-mini | contacts, notes, mem0, graphiti | ContactProfile |
| competitive_analyst | GPT-4o | jobs, documents, programs | CompetitiveReport |
| outreach_composer | GPT-4o | contacts, programs, jobs, mem0 | OutreachPlan |
| humint_analyst | GPT-4o | notes, contacts, mem0, graphiti | HUMINTBrief |

### ✅ Terminal Configuration

| Terminal | Project | Port | Directory | Branch |
|---|---|---|---|---|
| **A** (Hub) | BD-Automation-Engine | 8100 | `C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine\` | claude/setup-auto-claude-* |
| **B** (Data) | Data-Scraper | 8200 | `C:\data-scraper\data-scraper\` | main |
| **C** (Workflow) | N8N-Builder | 8300 | `C:\Auto-Claud\N8N-Builder\` | main |

---

## SECTION 3: ARCHITECTURE OVERVIEW

### Dashboard Architecture — The 5-Layer Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 5: UI SHELL                                                  │
│  React 19 + Vite 7 + TanStack Router (file-based routing)          │
│  shadcn/ui components + Tremor dashboard blocks                     │
│  cmdk command palette (⌘K) + Framer Motion transitions              │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 4: VISUALIZATION                                             │
│  Cosmograph (200K+ node overview) → G6 v5 (1K-50K exploration)      │
│  → Reagraph (<500 detail views) + Recharts/Nivo analytics           │
│  @dnd-kit for Kanban pipeline boards                                │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 3: AI INTEGRATION                                            │
│  Vercel AI SDK (useChat, streamText, useObject)                     │
│  assistant-ui chat primitives + shadcn/ai citation cards            │
│  CrewAI agent triggers via SSE streaming                            │
│  Mem0 memory panel + Graphiti relationship timeline                 │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 2: DATA LAYER                                                │
│  TanStack Query (server state) + TanStack Table (data grids)        │
│  React Hook Form + Zod (forms matching Pydantic schemas)            │
│  WebSocket event bus for real-time Qdrant updates                   │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 1: API GATEWAY                                               │
│  FastAPI Hub (:8100) — 157+ endpoints                               │
│  Qdrant (:6333) — 1.4M vectors, 12 collections                     │
│  Neo4j (:7687) — Graphiti temporal KG                               │
│  Vite dev proxy → /api/* → localhost:8100                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Page Structure (12 Routes)

| Route | Purpose | Key Components | Data Source |
|---|---|---|---|
| `/` | Executive dashboard + Weekly Intel Brief | KPI cards, alerts strip, activity feed | GET /stats, GET /agents/tasks |
| `/search` | AI-powered conversational search | Chat interface, faceted results, citations | POST /ask/smart |
| `/copilot` | Full AI copilot sidebar (expandable) | assistant-ui chat, tool call viz | Vercel AI SDK + all agents |
| `/contacts` | Contact database browser | TanStack Table, tier/program filters | Qdrant contacts collection |
| `/contacts/:id` | Contact intelligence profile | Profile card, timeline, HUMINT, outreach | Qdrant + Neo4j + Mem0 |
| `/programs` | Federal programs browser | Program cards, contract values, PTS involvement | Qdrant programs + federal_contracts |
| `/programs/:id` | Program intelligence detail | Pain points, contacts, jobs, competitive landscape | All agents |
| `/jobs` | Job pipeline Kanban board | @dnd-kit columns, enrichment status | Qdrant jobs collection |
| `/org-chart` | Interactive org chart | G6 tree layout, BD priority coloring, expand/collapse | Qdrant contacts + Neo4j |
| `/graph` | Relationship explorer | Cosmograph overview → G6 detail | Neo4j + Graphiti |
| `/outreach` | Outreach sequence manager | Timeline view, sequence steps, response tracking | SQLite outreach engine |
| `/agents` | Agent control center | Trigger forms, task queue, result cards | /agents/* endpoints |

### New npm Packages Required (Terminal A)

```bash
# Dashboard analytics
npm install @tremor/react

# Graph visualization (tiered)
npm install @cosmograph/react @antv/g6 graphin

# AI chat interface
npm install ai @ai-sdk/openai assistant-ui @assistant-ui/react

# Data management
npm install @tanstack/react-table @tanstack/react-router
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities

# Forms
npm install react-hook-form @hookform/resolvers zod

# Utilities
npm install framer-motion cmdk date-fns

# Timeline
npm install react-chrono vis-timeline
```

---

## SECTION 4: IMPLEMENTATION PHASES

### Phase 1: Foundation + AI Search (Week 1) — Terminal A

**This is the highest-impact phase.** Getting conversational AI search working across 1.4M vectors makes everything else easier to build because you can immediately query your data while developing.

### Phase 2: Entity Pages + Org Chart (Week 2) — Terminal A + C

Contact profiles, program intelligence cards, interactive org chart with G6.

### Phase 3: Pipeline + Outreach + Analytics (Week 3) — Terminal A + B + C

Kanban board, outreach sequences, cost tracking, weekly intel brief.

---

## SECTION 5: TERMINAL PROMPTS

### ═══════════════════════════════════════════════════
### TERMINAL A — Phase 1: Foundation + AI-Powered Search
### ═══════════════════════════════════════════════════

```
DASHBOARD V5: PHASE 1 — Foundation + AI-Powered Search

You are building a Palantir-grade BD Intelligence Dashboard for Prime Technical Services.
The backend is ALREADY RUNNING and PROVEN — 1.4M vectors in Qdrant, 5 CrewAI agents, Neo4j graph, Mem0 memory. 
Your job is to build the frontend that maximizes all of this infrastructure.

PROJECT: BD-Automation-Engine
DIRECTORY: C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine\
API: Already running on http://localhost:8100

═══ VERIFIED BACKEND STATE ═══
- Qdrant: 1.4M vectors across 12 collections (contacts 211K, documents 499K, activities 445K, federal_contracts 108K, programs 68K, bullhorn_notes 50K, jobs 16K, intelligence_reports 2.2K)
- API endpoints: GET /health, GET /stats, POST /search, POST /ask/smart, POST /agents/research, POST /agents/outreach, POST /agents/weekly-intel, GET /agents/tasks, GET /agents/status/{id}, POST /graphiti/search, POST /ingest/document
- CrewAI agents: program_researcher, contact_enricher, competitive_analyst, outreach_composer, humint_analyst — all with structured Pydantic outputs
- Neo4j: 7 nodes, 4 relationship types on bolt://localhost:7687
- Mem0: Configured with Qdrant vector store + Neo4j graph store
- Cross-encoder reranking: ms-marco-MiniLM-L-6-v2

═══ CRITICAL CONTEXT ═══
This dashboard serves a federal defense staffing BD team. The core workflow is:
1. Find contracts (scrape competitor job boards → map to federal programs)
2. Build contacts (ZoomInfo/LinkedIn → classify by 6-tier hierarchy → assign BD priority)
3. Gather HUMINT (call lower-tier contacts → document pain points, hiring manager names)
4. Craft outreach (PTS past performance + HUMINT + labor gaps → personalized 6-step BD formula)
5. Approach decision-makers (arrive with solutions, not cold calls)

The dashboard must make 1.4M vectors feel like talking to an AI that has MEMORIZED every detail about every contact, program, contract, and job in the database.

═══ TASK 1: Install new frontend dependencies ═══

Navigate to the frontend/dashboard directory (or wherever the Vite React app lives).
Audit what's already installed. Then install ONLY what's missing:

```bash
# Dashboard analytics (copy-paste compatible with shadcn/ui)
npm install @tremor/react

# AI chat interface  
npm install ai @ai-sdk/openai

# Data grids
npm install @tanstack/react-table

# Drag and drop (for Kanban later)
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities

# Forms matching Pydantic schemas
npm install react-hook-form @hookform/resolvers zod

# Command palette + animations
npm install cmdk framer-motion date-fns
```

Do NOT install Cosmograph, G6, or assistant-ui yet — those are Phase 2/3.

═══ TASK 2: Configure Vite proxy + API client ═══

In vite.config.ts, add proxy for the Hub API:
```typescript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:8100',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
}
```

Create src/lib/api.ts:
```typescript
const API_BASE = '/api';

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function apiPost<T>(path: string, body: any): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

// SSE streaming for agent tasks
export function streamSSE(path: string, onMessage: (data: any) => void): () => void {
  const source = new EventSource(`${API_BASE}${path}`);
  source.onmessage = (e) => onMessage(JSON.parse(e.data));
  source.onerror = () => source.close();
  return () => source.close();
}
```

Create src/lib/hooks.ts with TanStack Query hooks:
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from './api';

// Collection stats for KPI cards
export function useCollectionStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: () => apiGet('/stats'),
    staleTime: 30_000, // 30s cache
  });
}

// Smart search with AI synthesis
export function useSmartSearch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (query: string) => apiPost('/ask/smart', { query, rerank: true }),
  });
}

// Vector search across collections
export function useVectorSearch(collection?: string) {
  return useMutation({
    mutationFn: ({ query, limit = 20, filters }: { query: string; limit?: number; filters?: any }) =>
      apiPost('/search', { query, collection_name: collection, limit, filters }),
  });
}

// Agent tasks
export function useAgentTasks() {
  return useQuery({
    queryKey: ['agent-tasks'],
    queryFn: () => apiGet('/agents/tasks'),
    refetchInterval: 5000, // Poll every 5s
  });
}

export function useTriggerResearch() {
  return useMutation({
    mutationFn: (params: { program_name: string; agency: string }) =>
      apiPost('/agents/research', params),
  });
}

export function useTriggerOutreach() {
  return useMutation({
    mutationFn: (params: { contact_name: string; program: string }) =>
      apiPost('/agents/outreach', params),
  });
}

// Contact search
export function useContactSearch() {
  return useMutation({
    mutationFn: (query: string) =>
      apiPost('/search', { query, collection_name: 'contacts', limit: 50 }),
  });
}

// Program search
export function useProgramSearch() {
  return useMutation({
    mutationFn: (query: string) =>
      apiPost('/search', { query, collection_name: 'programs', limit: 50 }),
  });
}
```

═══ TASK 3: Build the root layout with navigation ═══

Create a responsive shell layout with:
- LEFT SIDEBAR: Collapsible navigation with icons (use lucide-react)
  - Dashboard (Home icon)
  - Search (Search icon) 
  - Contacts (Users icon)
  - Programs (Building2 icon)
  - Jobs (Briefcase icon)
  - Org Chart (Network icon)
  - Outreach (Send icon)
  - Agents (Bot icon)
- TOP BAR: Command palette trigger (⌘K), notification bell, user avatar
- MAIN CONTENT: Router outlet
- Use shadcn/ui sidebar component if available, otherwise build with Tailwind

The sidebar should show the PTS logo area at top, nav links in the middle, and a "Qdrant Status" indicator at the bottom showing total vector count (fetch from GET /stats on mount).

═══ TASK 4: Build the Executive Dashboard (/) ═══

This is the home page. Structure:

ROW 1 — KPI Cards (use Tremor Card + shadcn/ui):
- Total Contacts: 211,267 (from Qdrant stats, contacts collection)
- Federal Programs: 68,103 (programs collection)
- Active Jobs: 15,997 (jobs collection)
- Intelligence Reports: 2,229 (intelligence_reports collection)
- Federal Contracts: 107,902 (federal_contracts collection)
Each card shows the count, a sparkline trend (placeholder for now), and a colored indicator.

ROW 2 — Priority Alerts Strip:
- Fetch latest agent task results from GET /agents/tasks
- Show any tasks completed in the last 24 hours as alert cards
- Color code: research = blue, outreach = green, weekly-intel = purple

ROW 3 — Two-column layout:
LEFT: "Quick Actions" card with buttons:
  - "Research a Program" → opens modal with program name input → triggers POST /agents/research
  - "Build Outreach" → opens modal with contact name + program → triggers POST /agents/outreach
  - "Run Weekly Intel" → triggers POST /agents/weekly-intel with default programs
  - "Search Everything" → focuses the command palette

RIGHT: "Recent Agent Activity" — table of last 10 agent tasks with status, duration, type

ROW 4 — "BD Pipeline Summary" (placeholder for Phase 3 Kanban data)

═══ TASK 5: Build the AI Search Page (/search) ═══

THIS IS THE MOST IMPORTANT PAGE. It should feel like talking to Claude with your entire database attached.

Structure:
- Large search input at top (styled like Claude's input box)
- Below input: collection filter chips (All, Contacts, Programs, Jobs, Documents, Federal Contracts, Intelligence, Bullhorn Notes)
- Toggle: "AI Synthesis" (on/off) — when on, uses POST /ask/smart for LLM-generated answer; when off, returns raw vector results
- Toggle: "Cross-encoder Reranking" (on/off) — adds rerank=true param

Results display:
- When AI Synthesis is ON: Show the AI-generated answer at top in a distinct card with light blue background, then show the source documents below as citation cards with relevance scores
- When AI Synthesis is OFF: Show ranked vector search results as cards, each showing: collection badge, title/name, relevance score, key metadata, snippet of matching text

Each result card should be clickable — contacts navigate to /contacts/:id, programs to /programs/:id, etc.

Add a "conversation mode" toggle that converts the search into a multi-turn chat interface using TanStack Query mutations. Each query appends to a message history displayed above the input.

═══ TASK 6: Build the Agents Page (/agents) ═══

Structure:
TOP: Three trigger cards side by side:
1. "Program Research" — Form: program_name (text), agency (select: USAF, Army, Navy, DIA, NRO, NGA) → POST /agents/research
2. "Contact Outreach" — Form: contact_name (text), program (select from known programs) → POST /agents/outreach
3. "Weekly Intelligence" — Form: programs (multi-select) → POST /agents/weekly-intel

Each form shows a loading spinner after submission, then redirects focus to the task queue below.

BOTTOM: Agent Task Queue — TanStack Table with columns:
- Task ID (truncated)
- Type (research/outreach/weekly-intel) with colored badge
- Input params
- Status (pending/running/completed/failed) with animated indicator
- Duration
- Created timestamp
- Actions: "View Result" button (opens modal with full structured output)

The table auto-refreshes every 5 seconds via useAgentTasks() hook.

When "View Result" is clicked for a completed task, render the structured Pydantic output:
- ProgramIntelligence → Program card with all fields
- OutreachPlan → Outreach card with personalized opener, pain points, CTA, follow-up plan
- CompetitiveReport → Side-by-side competitor comparison
- HUMINTBrief → Intelligence card with findings, action items, confidence level

═══ TASK 7: Verify and test ═══

1. Start the Vite dev server: npm run dev
2. Open http://localhost:5173
3. Verify:
   a. Sidebar navigation renders and routes work
   b. Dashboard KPI cards load real numbers from GET /stats
   c. Search page accepts queries and returns results from POST /search
   d. AI Synthesis toggle works with POST /ask/smart
   e. Agents page can trigger a research task and poll status
   f. Command palette (⌘K) opens and filters routes
4. Fix any CORS issues (ensure Hub API allows localhost:5173)
5. Fix any proxy issues (ensure /api/* routes to :8100)

═══ DELIVERABLES ═══
- [ ] All npm packages installed
- [ ] Vite proxy configured
- [ ] API client + TanStack Query hooks created
- [ ] Root layout with sidebar navigation
- [ ] Executive Dashboard (/) with live KPI cards
- [ ] AI Search page (/search) with synthesis + reranking toggles
- [ ] Agents page (/agents) with trigger forms + task queue
- [ ] Command palette (⌘K) working
- [ ] All pages loading real data from the API

Commit: git add -A && git commit -m "feat: Dashboard V5 Phase 1 - foundation, AI search, agent triggers" && git push
```

### ═══════════════════════════════════════════════════
### TERMINAL A — Phase 2: Entity Pages + Org Chart
### ═══════════════════════════════════════════════════

```
DASHBOARD V5: PHASE 2 — Entity Pages + Org Chart

PREREQUISITE: Phase 1 must be complete — sidebar, API client, search, and agents pages working.

═══ TASK 1: Install graph visualization packages ═══

```bash
npm install @antv/g6@^5 @antv/graphin
# Note: Do NOT install Cosmograph yet — it requires a license for commercial use.
# G6 v5 handles up to 50K nodes which covers our 965 DCGS contacts + programs.
```

═══ TASK 2: Build Contacts List Page (/contacts) ═══

Structure:
TOP: Search bar + filter row
- Search input that queries contacts collection via POST /search
- Filter chips: Program (AF DCGS - Langley, AF DCGS - PACAF, AF DCGS - Wright-Patt, Army DCGS-A, Navy DCGS-N, Corporate HQ)
- Filter chips: Tier (Tier 1-6)
- Filter chips: BD Priority (🔴 Critical, 🟠 High, 🟡 Medium, ⚪ Standard)
- Filter chips: Location Hub (Hampton Roads, San Diego Metro, DC Metro, Dayton/Wright-Patt)

MAIN: TanStack Table with columns:
- BD Priority (colored dot)
- Name (clickable → /contacts/:id)
- Title
- Company
- Program (badge)
- Tier (badge with tier number)
- Location
- Email (mailto link)
- Phone
- LinkedIn (external link icon)

FEATURES:
- Server-side search via Qdrant vector search with payload filters
- Virtual scrolling for large result sets
- Click any row to open right-panel detail view (or navigate to /contacts/:id)
- Bulk select with checkboxes for "Generate Outreach for Selected" action
- Export selected to CSV button

═══ TASK 3: Build Contact Detail Page (/contacts/:id) ═══

This is the full intelligence profile for a single contact. Load by querying Qdrant with the contact's point ID or by name search.

Layout — Full width, tabbed interface:

TAB 1: OVERVIEW
- Header: Name, Title, Company, Program badge, Tier badge, BD Priority badge, Location
- Contact info row: Email, Phone, LinkedIn (all clickable)
- "AI Insight Band" — distinct section with light blue bg:
  - AI-generated summary of this contact's relevance to BD campaign
  - Recommended outreach approach based on tier + program + pain points
  - Button: "Generate Outreach Script" → triggers POST /agents/outreach with this contact

TAB 2: INTELLIGENCE
- HUMINT gathered (search bullhorn_notes + intelligence_reports for this contact's name)
- Pain points documented
- Team dynamics notes
- Hiring manager connections
- Budget cycle information

TAB 3: RELATIONSHIPS
- Related contacts at same program (search contacts by program match)
- Reporting chain (if available from org chart data)
- Interaction history from Bullhorn notes (search activities + bullhorn_notes)

TAB 4: OUTREACH HISTORY
- Outreach sequence status (if enrolled)
- Past agent-generated outreach plans for this contact
- Email/call history from Bullhorn notes

TAB 5: DOCUMENTS
- Any documents mentioning this contact (search documents collection)
- Related intelligence reports

═══ TASK 4: Build Programs List Page (/programs) ═══

Structure:
TOP: Search + filters (Agency Owner, Prime Contractor, PTS Involvement, Priority Level)

MAIN: Card grid layout (not table — programs deserve richer display):
Each Program Card shows:
- Program Name + Acronym (large font)
- Agency Owner badge
- Prime Contractor → Sub Contractor chain
- Contract Value (formatted as $XXM)
- PTS Involvement status: Current (green), Past (blue), Target (orange), None (gray)
- Active Jobs count (from jobs collection filtered by program)
- Key Contacts count (from contacts collection filtered by program)
- Pain Points summary (1-2 lines)
- "Research This Program" button → triggers POST /agents/research

Cards should be filterable and sortable. Click card → navigate to /programs/:id.

═══ TASK 5: Build Program Detail Page (/programs/:id) ═══

Full program intelligence view. Tabbed layout similar to contacts.

TAB 1: OVERVIEW
- Program header: Name, Acronym, Agency, Prime, Value, PoP dates
- AI Insight Band: AI-generated program assessment + recommended BD actions
- Key metrics row: Active Jobs, Known Contacts, Intelligence Reports, HUMINT Items

TAB 2: CONTACTS
- All contacts assigned to this program (table with tier + priority sorting)
- Grouped by tier: Executives first, then Directors, then PMs, etc.
- Quick outreach buttons per contact

TAB 3: COMPETITIVE LANDSCAPE
- Known competitors on this program
- PTS differentiators
- "Run Competitive Analysis" button → triggers competitive_analyst agent

TAB 4: LABOR GAPS
- Active job openings mapped to this program (from jobs collection)
- Unfilled positions by role type
- Time-to-fill estimates

TAB 5: INTELLIGENCE
- All HUMINT and intelligence reports related to this program
- Timeline view of intelligence gathered over time

═══ TASK 6: Build Org Chart Page (/org-chart) ═══

Use G6 v5 (already installed from Task 1) to build an interactive organizational hierarchy.

Data loading:
- Fetch contacts from Qdrant contacts collection (filter by program or load all DCGS contacts)
- Build tree structure: Program → Tier 1 → Tier 2 → Tier 3 → Tier 4 → Tier 5 → Tier 6
- Each node contains: name, title, tier, BD priority, program, location

G6 Configuration:
- Layout: 'dagre' (hierarchical top-down) OR 'compactBox' (tree)
- Node styling: Color border by BD Priority (🔴=red, 🟠=orange, 🟡=yellow, ⚪=gray)
- Node content: Name (bold), Title (small), Program badge
- Click node → show tooltip with full contact info + "View Profile" link
- Double-click node → navigate to /contacts/:id
- Expand/collapse subtrees by clicking +/- icon on nodes with children
- Zoom/pan controls
- Search within org chart (highlight matching nodes)
- Filter controls: Program dropdown, Tier range slider, Location dropdown

Toolbar above chart:
- Program filter (select which program's org chart to show)
- Color by: Priority / Program / Tier (radio buttons)
- Layout: Tree / Radial / Force (radio buttons)
- Export as PNG button
- Fullscreen toggle

═══ TASK 7: Build the Command Palette (⌘K) ═══

Use cmdk (already in shadcn/ui) to build a global command palette:

Groups:
1. "Navigate" — links to all pages (Dashboard, Search, Contacts, Programs, Jobs, etc.)
2. "Search Contacts" — type-ahead search that queries contacts collection in real-time
3. "Search Programs" — type-ahead search for programs
4. "Actions" — trigger agent research, trigger outreach, run weekly intel, export data
5. "Recent" — last 5 entities viewed (stored in localStorage)

The command palette should be accessible from ANY page via ⌘K (Mac) or Ctrl+K (Windows).

═══ DELIVERABLES ═══
- [ ] G6 v5 installed and working
- [ ] Contacts list page with filters + TanStack Table
- [ ] Contact detail page with 5 tabs + AI Insight Band
- [ ] Programs list page with card grid
- [ ] Program detail page with 5 tabs
- [ ] Interactive org chart with G6 dagre layout
- [ ] Command palette (⌘K) with entity search + navigation
- [ ] All pages loading real data from Qdrant

Commit: git add -A && git commit -m "feat: Dashboard V5 Phase 2 - entity pages, org chart, command palette" && git push
```

### ═══════════════════════════════════════════════════
### TERMINAL A — Phase 3: Pipeline + Outreach + Analytics
### ═══════════════════════════════════════════════════

```
DASHBOARD V5: PHASE 3 — Pipeline + Outreach + Analytics

PREREQUISITE: Phase 1 and Phase 2 must be complete.

═══ TASK 1: Build Jobs Pipeline Kanban (/jobs) ═══

Use @dnd-kit for a horizontal Kanban board.

Columns (map to BD workflow stages):
1. "Scraped" — raw job postings from competitor portals
2. "Mapped to Program" — jobs matched to federal programs
3. "Contacts Found" — programs where we've identified contacts
4. "Outreach Active" — contacts being engaged
5. "Meeting Set" — meetings scheduled with decision-makers
6. "Job Req Obtained" — requisitions received to fill

Each card shows:
- Job title
- Company (staffing portal source)
- Location
- Clearance required
- Mapped program (if known)
- Key contact (if identified)
- Days in current stage

Drag cards between columns to update status.
Column headers show: count + aggregate value.
Filter bar: Company, Location, Clearance, Date range.

Load initial data from Qdrant jobs collection. Status transitions should update the job's payload in Qdrant via a new PATCH endpoint (or store pipeline state in a local SQLite).

═══ TASK 2: Build Outreach Sequence Manager (/outreach) ═══

Two views (toggle):

VIEW 1: Sequence Timeline (per contact)
- Vertical timeline of outreach steps for a selected contact
- Steps: Day 1 Intro Email → Day 2 Check Reply → Day 3 Follow-up → Day 5 SMS → Day 7 Case Study → Day 14 Breakup
- Each step shows: type (email/call/SMS), status (sent/pending/skipped), date, content preview
- Click step to expand full content
- "Generate Content" button per step → triggers outreach_composer agent for that specific step

VIEW 2: Portfolio Overview (all contacts)
- Horizontal Gantt-like view: rows = contacts, columns = days
- Color-coded cells: green (completed), blue (scheduled), red (bounced), yellow (pending), gray (not started)
- Sort by: program, tier, last activity
- Bulk actions: pause all, resume all, skip step for selected

Data source: The outreach sequence engine (SQLite DB from Terminal C's sequence_engine.py)
Create a new API endpoint in Hub: GET /outreach/sequences, POST /outreach/sequences, PATCH /outreach/sequences/:id

═══ TASK 3: Build Analytics Dashboard section ═══

Add an "Analytics" section to the home dashboard OR create a dedicated /analytics page.

Charts (use Tremor + Recharts):
1. "Contacts by Program" — horizontal bar chart showing contact counts per DCGS program
2. "Contacts by Tier" — donut chart showing distribution across 6 tiers
3. "BD Priority Distribution" — stacked bar (Critical/High/Medium/Standard per program)
4. "Job Pipeline Funnel" — funnel chart: Scraped → Mapped → Contacts → Outreach → Meeting → Req
5. "Agent Activity Over Time" — area chart showing agent runs per day/week
6. "Intelligence Coverage" — heatmap: programs × intelligence types (HUMINT, competitive, hiring, subaward)
7. "LLM Cost Tracker" — bar chart of daily token usage (if CrewAI returns token_usage)

═══ TASK 4: Enhance the Home Dashboard with Weekly Intel Brief ═══

Add a new section to the home page: "Weekly Intelligence Briefing"

Structure (mirrors military Common Operating Picture):
- "Stale Intelligence" warnings — programs not updated in 7+ days highlighted in red
- AI-generated executive summary (trigger weekly-intel agent or use cached last result)
- Sections: New Opportunities, Program Updates, Contact Activity, Competitive Moves
- Each section has 3-5 bullet points with linked entities

Also add a "Quick Stats" comparison bar: This Week vs Last Week for contacts added, jobs scraped, outreach sent, meetings set.

═══ TASK 5: Final polish ═══

1. Add loading skeletons to all pages (use shadcn/ui Skeleton component)
2. Add error boundaries with retry buttons
3. Add breadcrumb navigation on detail pages
4. Add keyboard shortcuts: / for search, n for new, esc to close modals
5. Add dark mode toggle (Tailwind dark: classes)
6. Add responsive design for tablet viewing (the BD team may use iPads in meetings)
7. Ensure all links between entities work: clicking a program name in a contact card navigates to /programs/:id, etc.

═══ DELIVERABLES ═══
- [ ] Jobs Kanban board with drag-and-drop
- [ ] Outreach sequence manager with timeline + portfolio views
- [ ] Analytics charts (7 charts minimum)
- [ ] Weekly Intelligence Briefing on home page
- [ ] Loading skeletons, error boundaries, keyboard shortcuts
- [ ] Dark mode support
- [ ] All cross-entity navigation working

Commit: git add -A && git commit -m "feat: Dashboard V5 Phase 3 - pipeline, outreach, analytics, weekly intel" && git push
```

### ═══════════════════════════════════════════════════
### TERMINAL B — Support Tasks (Run in parallel with A)
### ═══════════════════════════════════════════════════

```
DASHBOARD SUPPORT: API Endpoints for Dashboard Features

The Hub dashboard (Terminal A) needs additional API endpoints. Create these in the Hub API OR expose them from Data-Scraper on port 8200.

═══ TASK 1: Create a /api/contacts/search endpoint with Qdrant payload filters ═══

The dashboard needs filtered contact searches beyond basic vector search.

Add to the Hub API:

POST /api/contacts/filter
Body: {
  "query": "optional text query",
  "program": "AF DCGS - PACAF",        // optional filter
  "tier": "Tier 3 - Program Leadership", // optional filter
  "priority": "🔴 Critical",            // optional filter
  "location_hub": "San Diego Metro",     // optional filter
  "limit": 50,
  "offset": 0
}

Implementation:
- Use Qdrant scroll() with payload filters when no query text
- Use Qdrant search() with payload filters when query text provided
- Return: { results: [...], total: count, offset: n }

═══ TASK 2: Create /api/programs/filter endpoint ═══

Same pattern as contacts but for programs collection:

POST /api/programs/filter
Body: {
  "query": "optional text query",
  "agency": "USAF",
  "prime": "GDIT",
  "pts_involvement": "Target",
  "limit": 50,
  "offset": 0
}

═══ TASK 3: Create /api/dashboard/stats endpoint ═══

Consolidated stats for the dashboard home page:

GET /api/dashboard/stats

Returns:
{
  "collections": {
    "contacts": { "count": 211267, "status": "green" },
    "programs": { "count": 68103, "status": "green" },
    ...for each collection
  },
  "agents": {
    "total_runs": 47,
    "completed": 42,
    "failed": 5,
    "last_run": "2026-02-07T17:30:00Z"
  },
  "recent_tasks": [...last 10 agent tasks],
  "pipeline": {
    "scraped": 175,
    "mapped": 120,
    "contacts_found": 80,
    "outreach_active": 25,
    "meetings_set": 3
  }
}

═══ TASK 4: Create /api/outreach/sequences endpoints ═══

If Terminal C built the outreach sequence engine (SQLite-based), expose it via HTTP:

GET /api/outreach/sequences — list all sequences
POST /api/outreach/sequences — create new sequence
GET /api/outreach/sequences/:id — get single sequence
PATCH /api/outreach/sequences/:id — advance step / mark replied / pause
GET /api/outreach/sequences/due — get sequences with pending actions

═══ TASK 5: Ensure CORS allows dashboard origin ═══

In the Hub API's CORS middleware, ensure localhost:5173 (Vite dev server) is allowed:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8100"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit: git add -A && git commit -m "feat: Dashboard support API endpoints - contacts, programs, stats, outreach, CORS" && git push
```

### ═══════════════════════════════════════════════════
### TERMINAL C — Support Tasks (Run in parallel)
### ═══════════════════════════════════════════════════

```
DASHBOARD SUPPORT: Outreach Engine + Data Exports

═══ TASK 1: Expose outreach sequence engine via FastAPI ═══

Terminal C already has (or should have) the outreach sequence engine from the previous prompt.
Now wrap it in a FastAPI app on port 8300:

```python
# src/outreach/api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .sequence_engine import SequenceEngine

app = FastAPI(title="PTS Outreach API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

engine = SequenceEngine()

@app.get("/sequences")
def list_sequences():
    return {"sequences": engine.get_all_sequences()}

@app.post("/sequences")
def create_sequence(data: dict):
    sid = engine.create_sequence(
        data["contact_name"], data["contact_email"],
        data["program"], data["tier"],
        data.get("contact_phone")
    )
    return {"id": sid, "status": "created"}

@app.get("/sequences/due")
def get_due():
    return {"due": engine.get_due_sequences()}

@app.patch("/sequences/{seq_id}")
def advance(seq_id: str, data: dict):
    result = engine.advance_step(seq_id, data.get("result", "sent"))
    return {"next_step": result}

@app.get("/health")
def health():
    return {"status": "healthy", "port": 8300}
```

Run: uvicorn src.outreach.api:app --host 0.0.0.0 --port 8300

═══ TASK 2: Create org chart data export script ═══

The dashboard org chart needs structured hierarchical data. Create a script that:

1. Reads contacts from Qdrant (or from the CSV files in project)
2. Builds a tree structure grouped by: Program → Tier → Contacts
3. Outputs JSON in G6-compatible format:

```json
{
  "nodes": [
    {"id": "prog_1", "label": "AF DCGS - PACAF", "type": "program", "style": {"fill": "#3b82f6"}},
    {"id": "contact_1", "label": "Kingsley Ero", "type": "contact", "data": {
      "title": "Acting Site Lead", "tier": 3, "priority": "critical",
      "email": "...", "phone": "...", "linkedin": "..."
    }}
  ],
  "edges": [
    {"source": "prog_1", "target": "contact_1"}
  ]
}
```

4. Save to: data/exports/org_chart_data.json
5. Also create an API endpoint: GET /org-chart/data that serves this JSON

═══ TASK 3: Create Neo4j relationship export for graph visualization ═══

Query Neo4j for all entity relationships and export for the dashboard graph view:

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    # Get all nodes and relationships
    result = session.run("""
        MATCH (a)-[r]->(b) 
        RETURN a, type(r) as rel_type, r, b 
        LIMIT 5000
    """)
    
    nodes = {}
    edges = []
    for record in result:
        # Build G6-compatible graph data
        ...
```

Save to: data/exports/graph_data.json

Commit: git add -A && git commit -m "feat: Outreach API, org chart export, Neo4j graph export for dashboard" && git push
```

---

## SECTION 6: ARCHITECTURE DIAGRAM

```
╔══════════════════════════════════════════════════════════════════════╗
║                    PTS BD INTELLIGENCE DASHBOARD V5                  ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  ┌──────────────────────────────────────────────────────────────┐   ║
║  │                    BROWSER (localhost:5173)                    │   ║
║  │                                                                │   ║
║  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐│   ║
║  │  │ Sidebar  │ │ Dashboard│ │ Search   │ │ Entity Pages      ││   ║
║  │  │ Nav      │ │ + KPIs   │ │ + AI Chat│ │ Contacts/Programs ││   ║
║  │  │ (cmdk)   │ │ + Alerts │ │ + Cite   │ │ + Detail + Tabs   ││   ║
║  │  └─────────┘ └──────────┘ └──────────┘ └───────────────────┘│   ║
║  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐│   ║
║  │  │ Org Chart│ │ Jobs     │ │ Outreach │ │ Agents Control    ││   ║
║  │  │ G6 Tree  │ │ Kanban   │ │ Timeline │ │ Trigger + Queue   ││   ║
║  │  │ +Reagraph│ │ @dnd-kit │ │ Gantt    │ │ + Result Cards    ││   ║
║  │  └──────────┘ └──────────┘ └──────────┘ └───────────────────┘│   ║
║  │                                                                │   ║
║  │  Tech: React 19 + Vite 7 + shadcn/ui + Tremor + TanStack     │   ║
║  │        Query + Table + Router + G6 v5 + Recharts + cmdk       │   ║
║  └────────────────────────┬─────────────────────────────────────┘   ║
║                           │ Vite Proxy /api/* → :8100                ║
║  ┌────────────────────────┴─────────────────────────────────────┐   ║
║  │                    HUB API (localhost:8100)                    │   ║
║  │                    FastAPI + 157+ endpoints                    │   ║
║  │                                                                │   ║
║  │  /stats  /search  /ask/smart  /agents/*  /graphiti/*          │   ║
║  │  /contacts/filter  /programs/filter  /dashboard/stats         │   ║
║  │  /outreach/sequences  /ingest/document  /collections/*        │   ║
║  │                                                                │   ║
║  │  CrewAI Agents:                                                │   ║
║  │  ├─ program_researcher (GPT-4o)                               │   ║
║  │  ├─ contact_enricher (GPT-4o-mini)                            │   ║
║  │  ├─ competitive_analyst (GPT-4o)                              │   ║
║  │  ├─ outreach_composer (GPT-4o)                                │   ║
║  │  └─ humint_analyst (GPT-4o)                                   │   ║
║  └──┬──────────────────┬──────────────────┬─────────────────────┘   ║
║     │                  │                  │                          ║
║  ┌──┴──────────┐ ┌────┴──────────┐ ┌────┴──────────────────────┐   ║
║  │ Qdrant      │ │ Neo4j         │ │ Mem0                      │   ║
║  │ :6333       │ │ :7687         │ │ (Qdrant+Neo4j backend)    │   ║
║  │ 1.4M vectors│ │ Graphiti KG   │ │ Cross-session agent memory│   ║
║  │ 12 colls    │ │ 7 nodes       │ │ bd_memories collection    │   ║
║  │ INT8 quant  │ │ 4 rel types   │ │                           │   ║
║  │ Payload idx │ │ Temporal edges│ │                           │   ║
║  └─────────────┘ └───────────────┘ └───────────────────────────┘   ║
║                                                                      ║
║  ┌─────────────────────────────────────────────────────────────┐    ║
║  │                    SPOKE SERVICES                            │    ║
║  │  ┌─────────────────┐  ┌──────────────────────────────────┐  │    ║
║  │  │ Data-Scraper    │  │ N8N-Builder / Workflow Engine     │  │    ║
║  │  │ :8200           │  │ :8300                             │  │    ║
║  │  │ Apify scrapers  │  │ Outreach sequence engine (SQLite) │  │    ║
║  │  │ Federal APIs    │  │ Tango/MakeGov discovery           │  │    ║
║  │  │ Bullhorn sync   │  │ LangGraph workflows               │  │    ║
║  │  └─────────────────┘  └──────────────────────────────────┘  │    ║
║  └─────────────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## SECTION 7: EXECUTION ORDER

| Week | Terminal A (Hub Dashboard) | Terminal B (API Support) | Terminal C (Data Services) |
|---|---|---|---|
| **Week 1** | Phase 1: Install deps, API client, layout, dashboard home, AI search, agents page | Create filtered search endpoints, dashboard stats, CORS | Expose outreach API on :8300, org chart data export |
| **Week 2** | Phase 2: Contacts list+detail, programs list+detail, org chart (G6), command palette | Fresh job scrape + push to Qdrant, test filtered endpoints | Neo4j graph export, test outreach sequences |
| **Week 3** | Phase 3: Kanban pipeline, outreach timeline, analytics charts, weekly intel brief, dark mode | Pipeline status tracking endpoint | Connect outreach engine to Hub, create sequence templates |

### Parallel Execution Pattern

1. Start Terminal A on Phase 1 immediately — it's the primary workstream
2. Start Terminal B on API support tasks simultaneously — Terminal A will need those endpoints
3. Start Terminal C on outreach API + data exports — Terminal A Phase 3 needs these
4. Terminal A Phase 1 should take 2-4 hours of Auto-Claude time
5. Terminal A Phase 2 should take 3-5 hours
6. Terminal A Phase 3 should take 3-5 hours
7. Terminal B and C tasks are 1-2 hours each

### Between Phases

After each phase completes on Terminal A:
1. Test all pages in browser
2. Screenshot any issues
3. Verify API calls return real data
4. Check console for errors
5. Commit and push
6. Proceed to next phase
