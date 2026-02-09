# PTS BD Intelligence Dashboard — Corrected Implementation Guide v6.0

> **Document Purpose**: Audit-verified, error-free implementation spec for the BD Dashboard
> **Date**: February 8, 2026
> **Supersedes**: PTS_BD_Dashboard_Implementation_v5.md (20+ errors found)
> **Audit Sources**: Terminal A/B/C audits completed Feb 8, 2026 + filesystem verification

---

## ⚠️ CRITICAL FINDINGS FROM v5 AUDIT

The v5 guide contained **22 errors** that would have caused terminal prompts to fail, rebuild existing work, or target wrong directories. All corrected below.

### Errors Fixed

| # | Category | v5 Said | Actual (Verified) |
|---|----------|---------|-------------------|
| 1 | **Terminal A Path** | `C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine\` | `C:\Auto-Claud\Auto-Claude\BD-Automation-Engine\` |
| 2 | **Terminal B Path** | `C:\data-scraper\data-scraper\` | `C:\Auto-Claud\data-scraper\` |
| 3 | **Terminal A Branch** | `claude/setup-auto-claude-*` | `claude/setup-auto-claude-IrK21` |
| 4 | **Terminal B Branch** | `main` | `master` |
| 5 | **Terminal C Branch** | `main` | `master` |
| 6 | **CrewAI Agents** | 5 agents | **13 agents** (8 BDAgent + 5 raw), **6 crews** |
| 7 | **Neo4j State** | 7 nodes, 4 rel types | **12 nodes, 9 rels, 10 labels, 14 rel types** |
| 8 | **API Endpoints** | ~157 | ~140+ (verified categories: search, RAG, graph, memory, ingest, agents, QA, pipeline, alerts, dashboard, Dify) |
| 9 | **Qdrant Collections** | 9 listed | **12** (missing: star_charts, mem0migrations, mem0, opportunities) |
| 10 | **Node.js Version** | v20+ (v22 preferred) | **v24.13.0** |
| 11 | **n8n MCP** | "if still connected" | **ZERO runtime dependency** — remove all n8n references |
| 12 | **Dashboard State** | Assumes blank slate / build from scratch | **27 pages, 63 npm packages, full component library ALREADY BUILT** |
| 13 | **npm Packages** | "Install these packages" | **ALL already installed** — @tremor, @tanstack/*, @dnd-kit/*, cmdk, framer-motion, zod, react-hook-form, recharts, reagraph, @cosmograph, assistant-ui, ai, zustand, etc. |
| 14 | **Vite Proxy** | `/api` prefix rewrite pattern | **Per-route proxying already configured** (17+ routes mapped individually, NO /api prefix) |
| 15 | **Routing** | TanStack Router file-based | **State-based routing** with `activeTab` + switch (TanStack Router installed but NOT wired) |
| 16 | **API Client** | "Create src/lib/api.ts" | **Already exists**: `src/services/hubApi.ts` (full HubApiClient class) + `src/hooks/useHubApi.ts` |
| 17 | **Data Hooks** | "Create TanStack Query hooks" | **Already exists**: `src/hooks/useAppData.ts` (TanStack Query, Hub API + local JSON fallback) |
| 18 | **Sidebar** | "Build root layout" | **Already exists**: `Sidebar.tsx` with 27+ nav items, collapse toggle |
| 19 | **Command Palette** | "Build with cmdk" | **Already exists**: `CommandPalette.tsx` |
| 20 | **Search Page** | "Build AI Search" | **Already exists**: `SmartQuery.tsx` + `SmartSearchBar.tsx` |
| 21 | **Agent Panel** | "Build Agents page" | **Already exists**: `AgentPanel.tsx` + `AgentCard.tsx` |
| 22 | **Dark Mode** | "Add dark mode toggle" | **Already exists**: `ThemeSwitcher.tsx` |

---

## SECTION 1: VERIFIED INFRASTRUCTURE STATE (Feb 8, 2026)

### Terminal Configuration ✅ CORRECTED

| Terminal | Project | Ports | Directory | Branch |
|---|---|---|---|---|
| **A** (Hub) | BD-Automation-Engine | 8100 (API), 5173 (Vite) | `C:\Auto-Claud\Auto-Claude\BD-Automation-Engine\` | `claude/setup-auto-claude-IrK21` |
| **B** (Data) | Data-Scraper | 8200 | `C:\Auto-Claud\data-scraper\` | `master` |
| **C** (Workflow) | N8N-Builder | 8300 | `C:\Auto-Claud\N8N-Builder\` ⚠️ "Claud" not "Claude" | `master` |

### Services Status ✅

| Service | URL | Status | Details |
|---|---|---|---|
| Qdrant | localhost:6333 | HEALTHY | 12 collections, 1,401,933 vectors |
| Hub API | localhost:8100 | HEALTHY | ~140+ endpoints on FastAPI |
| Neo4j | localhost:7687 | HEALTHY | 12 nodes, 9 rels, 10 labels, 14 rel types |
| Node.js | — | HEALTHY | v24.13.0 |
| docx (npm global) | — | HEALTHY | Installed |

### Qdrant Collections ✅ COMPLETE

| Collection | Vectors | Payload Indexes | Quantization |
|---|---|---|---|
| documents | 499,750 | 7 | INT8 Scalar |
| activities | 445,972 | 6 | INT8 Scalar |
| contacts | 211,267 | 7 | INT8 Scalar |
| federal_contracts | 107,902 | 6 | none |
| programs | 68,103 | 6 | none |
| bullhorn_notes | 50,710 | 6 | — |
| jobs | 15,997 | 6 | none |
| intelligence_reports | 2,229 | 0 | none |
| star_charts | 5 | — | — |
| bd_memories | 2 | 4 | — |
| mem0migrations | 1 | 4 | — |
| mem0 | 0 | 4 | — |
| opportunities | 0 | 0 | — |
| **TOTAL** | **1,401,933** | | |

### CrewAI Agent System ✅ CORRECTED

**13 agents total** organized into **6 crews**:
- 8 BDAgent subclasses (specialized BD workflow agents)
- 5 raw CrewAI agents (program_researcher, contact_enricher, competitive_analyst, outreach_composer, humint_analyst)
- All with structured Pydantic outputs
- Agent API: POST /agents/research, POST /agents/outreach, POST /agents/weekly-intel, GET /agents/tasks, GET /agents/status/{id}

### Dashboard Frontend ✅ EXISTING STATE

**27 pages already built:**

| Category | Pages | Status |
|---|---|---|
| **Core BD** | ExecutiveSummary, JobIntelligence, JobsPipeline, Programs, Contacts, Contractors, Locations | Built, functional |
| **Intelligence** | BDEvents, Opportunities, EnrichmentDashboard, DailyPlaybook, PastPerformance, CallIntelligence, AccountTakeover | Built, functional |
| **Visualization** | MindMap, PrimeOrgChart, ContactOrgChartPage, KnowledgeGraph | Built, functional |
| **Operations** | QADashboard, PipelineStatus, DataQualityDashboard, PlacementsPage | Built, functional |
| **Hub AI** | SmartQuery, AgentPanel, MemoryContext, SystemHealth | Built, functional |
| **Settings** | Settings | Built, functional |

**63 npm packages installed** — ALL dependencies from v5 guide already present

**Key components built:**
- Sidebar.tsx (collapsible nav, 27+ routes)
- CommandPalette.tsx (Cmd+K global search)
- ThemeSwitcher.tsx (dark mode)
- ErrorBoundary.tsx
- DataFreshness.tsx
- OrgChartGraph.tsx
- SmartSearchBar.tsx, AgentCard.tsx, SystemStatsCard.tsx
- MindMap canvas (9 component files)
- 12 shadcn/ui components (badge, button, card, command, dialog, skeleton, sonner, table, tabs, toast, etc.)

**API layer built:**
- `services/hubApi.ts` — Full HubApiClient singleton (SmartQuery, agents, graph, memory, pipeline, alerts, cache, health)
- `hooks/useHubApi.ts` — React hooks wrapping every Hub API method
- `hooks/useAppData.ts` — TanStack Query with Hub API → local JSON fallback
- `hooks/useNotionData.ts` — Direct Notion data fetching

**Current routing**: State-based (`useState<TabId>` + switch), NOT TanStack Router

**Vite proxy**: Per-route mapping (17 individual routes proxied to :8100), NOT /api prefix pattern

---

## SECTION 2: WHAT ACTUALLY NEEDS TO BE DONE

Given the existing dashboard, the implementation phases shift from "build from scratch" to "enhance, connect, and polish."

### Gap Analysis: What's Missing vs. What Exists

| Feature | v5 Planned | Current State | Action Needed |
|---|---|---|---|
| Live KPI from Qdrant stats | Phase 1 | useAppData tries Hub API but may fall back to JSON | **Verify Hub API data flow works end-to-end** |
| AI Synthesis toggle on search | Phase 1 | SmartQuery exists with strategy selection | **Verify /ask/smart returns synthesized answers** |
| Agent task queue with polling | Phase 1 | AgentPanel triggers agents | **Add polling + task history table** |
| Contact detail page (tabbed) | Phase 2 | Contacts list exists, no dedicated detail page | **BUILD: /contacts/:id with 5 tabs** |
| Program detail page (tabbed) | Phase 2 | Programs list exists, no dedicated detail page | **BUILD: /programs/:id with 5 tabs** |
| TanStack Table on contacts | Phase 2 | Custom table exists | **UPGRADE to TanStack Table with server-side filters** |
| G6 org chart | Phase 2 | ContactOrgChartPage + OrgChartGraph exist | **Verify G6 rendering, add BD priority coloring** |
| Kanban with drag-drop | Phase 3 | JobsPipeline exists | **UPGRADE with @dnd-kit drag-drop between stages** |
| Outreach sequence manager | Phase 3 | No outreach UI exists | **BUILD: Full outreach page connecting to Terminal C :8300** |
| Analytics charts (7+) | Phase 3 | KPICharts.tsx exists | **ENHANCE with Tremor/Recharts analytics** |
| Weekly Intel Brief | Phase 3 | Not present | **BUILD: Weekly briefing section on dashboard home** |
| Migrate to TanStack Router | Optional | State-based routing works | **SKIP for now — not worth the rewrite risk** |

### Priority Order

1. **Phase 1 (Verify + Fix)**: Ensure Hub API data flows correctly to all existing pages
2. **Phase 2 (Build Missing)**: Contact detail page, Program detail page, TanStack Table upgrade
3. **Phase 3 (Build New)**: Outreach manager, analytics, weekly intel brief, Kanban upgrade

---

## SECTION 3: CORRECTED TERMINAL PROMPTS

### ═══════════════════════════════════════════════════
### TERMINAL A — Phase 1: Verify + Fix Hub API Integration
### ═══════════════════════════════════════════════════

```
DASHBOARD V6: PHASE 1 — Verify + Fix Hub API Integration

You are enhancing an EXISTING dashboard for Prime Technical Services BD Intelligence.
The dashboard has 27 pages, 63 npm packages, and a full component library ALREADY BUILT.
DO NOT rebuild existing pages. Your job is to verify the data pipeline works and fix gaps.

PROJECT: BD-Automation-Engine
DIRECTORY: C:\Auto-Claud\Auto-Claude\BD-Automation-Engine\
DASHBOARD: C:\Auto-Claud\Auto-Claude\BD-Automation-Engine\dashboard\
API: Already running on http://localhost:8100
BRANCH: claude/setup-auto-claude-IrK21

═══ VERIFIED BACKEND STATE ═══
- Qdrant: 1,401,933 vectors across 12 collections (contacts 211K, documents 500K, activities 446K, federal_contracts 108K, programs 68K, bullhorn_notes 51K, jobs 16K, intelligence_reports 2.2K, star_charts 5, bd_memories 2, mem0migrations 1, mem0 0, opportunities 0)
- Hub API: ~140+ endpoints on FastAPI :8100 — /health, /stats, /search, /ask/smart, /agents/research, /agents/outreach, /agents/weekly-intel, /agents/tasks, /agents/status/{id}, /graphiti/search, /ingest/document, /collections/{name}/search, /contacts/filter, /programs/filter, /dashboard/stats, /pipeline/trigger, /alerts, /rag/*, /memory/*, /bdgraph/*, /cache/*
- CrewAI: 13 agents (8 BDAgent subclasses + 5 raw), 6 crews — all with Pydantic structured outputs
- Neo4j: 12 nodes, 9 relationships, 10 labels, 14 relationship types (Graphiti temporal KG)
- Mem0: 2 memories in bd_memories, mem0 collection initialized

═══ EXISTING DASHBOARD STATE ═══
- 27 pages built (see App.tsx switch statement)
- Routing: State-based activeTab + switch (NOT TanStack Router)
- API client: src/services/hubApi.ts (HubApiClient singleton)
- Hooks: src/hooks/useHubApi.ts (15+ custom hooks)
- Data: src/hooks/useAppData.ts (TanStack Query, Hub API → local JSON fallback)
- Vite proxy: Per-route mapping in vite.config.ts (17 routes, NO /api prefix)
- All npm packages installed (63 total including @tremor, @tanstack/*, @dnd-kit/*, cmdk, etc.)
- Components: Sidebar, CommandPalette, ThemeSwitcher, ErrorBoundary, DataFreshness, 12 shadcn/ui

═══ TASK 1: Verify Hub API connectivity from dashboard ═══

1. cd to the dashboard directory
2. Start the dev server: npm run dev
3. Open http://localhost:5173 in the browser (or test with curl)
4. Check the browser console and Network tab for:
   a. Does GET /health return {"status": "healthy"}?
   b. Does GET /stats return collection counts?
   c. Does POST /search with body {"query": "DCGS", "collection_name": "contacts", "limit": 5} return results?
   d. Does POST /ask/smart with body {"query": "Who are the key contacts at AF DCGS PACAF?"} return a synthesized answer?
   e. Does GET /agents/tasks return (even if empty array)?

5. If ANY of these fail, check:
   - vite.config.ts proxy routes — they map directly without /api prefix
   - Hub API CORS — must allow origin http://localhost:5173
   - hubApi.ts baseUrl — should be empty string (uses Vite proxy)

Fix any connectivity issues found.

═══ TASK 2: Verify Executive Summary page loads real data ═══

1. Look at src/pages/ExecutiveSummary.tsx
2. Check what data prop it receives from App.tsx (summary prop from useAppData)
3. Trace through useAppData.ts:
   - Does fetchDashboardData() successfully hit the Hub API?
   - Does it populate the summary object with real Qdrant counts?
4. If the page shows placeholder/zero data:
   - Check the /api/v2/contacts, /api/v2/programs endpoints exist on the Hub
   - Check the /stats endpoint returns parseable data
   - Fix the response parsing in useAppData.ts to match actual API response shape
5. Verify KPI numbers match Qdrant reality (contacts ~211K, programs ~68K, jobs ~16K)

═══ TASK 3: Verify SmartQuery page connects to /ask/smart ═══

1. Open the SmartQuery page (Hub AI > Smart Query in sidebar)
2. Enter a test query: "What are the current pain points at AF DCGS PACAF in San Diego?"
3. Verify:
   - The request hits POST /ask/smart (not just /search)
   - The response includes an AI-synthesized answer with sources
   - Sources display with collection badges and relevance scores
4. If /ask/smart returns errors:
   - Check if the endpoint exists: curl http://localhost:8100/ask/smart
   - Verify the request body format matches what the API expects
   - Fix the hubApiClient.smartQuery() method if needed

═══ TASK 4: Verify AgentPanel triggers agents successfully ═══

1. Open the Agent Panel page (Hub AI > Agents in sidebar)
2. Try triggering the program_researcher agent with program_name="AF DCGS" agency="USAF"
3. Verify:
   - POST /agents/research fires successfully
   - The response includes a task_id
   - GET /agents/status/{task_id} shows progress
   - When complete, the structured ProgramIntelligence output renders
4. If agents fail:
   - Check CrewAI is properly initialized in the Hub API
   - Check OPENAI_API_KEY is set in the Hub's .env
   - Check the agent endpoint actually exists (curl -X POST http://localhost:8100/agents/research)

═══ TASK 5: Add agent task polling to AgentPanel ═══

The current AgentPanel triggers agents but may not have auto-polling. Add:
1. A "Task History" section below the trigger cards
2. Use GET /agents/tasks to fetch task list
3. Auto-refresh every 5 seconds using TanStack Query or setInterval
4. Show: Task ID, Type (badge), Status (animated), Duration, Input params, "View Result" button
5. Make the task list a TanStack Table with sortable columns

═══ TASK 6: Ensure Hub API CORS is correct ═══

Check the Hub API's main.py or app.py for CORS middleware:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8100", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

If CORS is missing or restrictive, add it. This is critical for the Vite proxy to work.

═══ TASK 7: Test and verify all existing pages load ═══

Navigate through every page in the sidebar and verify:
1. Executive Summary — loads real data or gracefully shows "connecting to Hub API"
2. SmartQuery — accepts queries and shows results
3. AgentPanel — shows agent cards and can trigger
4. SystemHealth — shows Qdrant/Neo4j/API status
5. Contacts — loads contact list (from Hub or Notion)
6. Programs — loads program list
7. JobsPipeline — loads job data
8. KnowledgeGraph — renders graph visualization
9. MemoryContext — shows Mem0 state

For any page that shows errors or empty data, note the issue but DO NOT rewrite the page.
Just fix the data connection.

═══ DELIVERABLES ═══
- [ ] Hub API connectivity verified (all 5 test endpoints respond)
- [ ] Executive Summary loads real KPI numbers from Qdrant
- [ ] SmartQuery returns AI-synthesized answers
- [ ] AgentPanel successfully triggers at least one agent
- [ ] Agent task polling added to AgentPanel
- [ ] CORS verified/fixed
- [ ] All existing pages load without console errors

═══ PHASE COMPLETION ═══
When ALL deliverables are checked, output the Phase Completion Summary:

═══ PHASE COMPLETION SUMMARY ═══
Terminal: A
Phase: Dashboard V6 Phase 1 — Verify + Fix Hub API Integration
Duration: [X minutes]
Status: [COMPLETE / PARTIAL / BLOCKED]

COMPLETED:
- [list each deliverable with verification result]

FAILED/SKIPPED:
- [item] — Reason: [why]

STATE CHANGES:
- Files modified: [list]
- API fixes: [list]
- Config changes: [list]

BLOCKERS FOR NEXT PHASE:
- [list any]

NEXT PHASE READY: [YES/NO]

COPY-PASTE FOR ORCHESTRATOR:
[One paragraph summary]
═══ END SUMMARY ═══

Commit: git add -A && git commit -m "fix: Dashboard V6 Phase 1 - verify and fix Hub API integration" && git push
```

### ═══════════════════════════════════════════════════
### TERMINAL A — Phase 2: Entity Detail Pages + Table Upgrade
### ═══════════════════════════════════════════════════

```
DASHBOARD V6: PHASE 2 — Entity Detail Pages + Table Upgrade

PREREQUISITE: Phase 1 must be complete — Hub API connectivity verified, all existing pages loading.

PROJECT: BD-Automation-Engine
DIRECTORY: C:\Auto-Claud\Auto-Claude\BD-Automation-Engine\
DASHBOARD: C:\Auto-Claud\Auto-Claude\BD-Automation-Engine\dashboard\
BRANCH: claude/setup-auto-claude-IrK21

═══ CRITICAL: DO NOT break existing pages ═══
- The dashboard uses state-based routing (activeTab + switch in App.tsx)
- Add new pages to the EXISTING switch statement
- Add new sidebar entries to the EXISTING Sidebar.tsx
- Use the EXISTING hubApiClient and useHubApi hooks
- Follow the EXISTING component patterns (look at any page for style reference)

═══ TASK 1: Build Contact Detail Page ═══

Create src/pages/ContactDetail.tsx — a full intelligence profile for a single contact.

Data loading:
- Accept a contactId/contactName prop from the parent
- Query Qdrant contacts collection: POST /search with collection_name="contacts" and the contact name
- Also query bullhorn_notes and intelligence_reports for this contact's name

Layout — Tabbed interface using the existing shadcn/ui Tabs component:

TAB 1: OVERVIEW
- Header: Name (large), Title, Company, Program badge, Tier badge (color-coded), BD Priority badge, Location
- Contact row: Email (mailto), Phone (tel:), LinkedIn (external link) — all clickable
- "AI Insight" section (blue-tinted card):
  - Trigger POST /ask/smart with query: "Summarize everything known about {name} including their program, pain points, and BD approach"
  - Show AI-generated summary
  - Button: "Generate Outreach" → triggers POST /agents/outreach

TAB 2: INTELLIGENCE
- Search bullhorn_notes collection for this contact name
- Search intelligence_reports for this contact
- Display as timeline cards with dates and summaries

TAB 3: RELATIONSHIPS
- Search contacts collection for same program
- Show as mini-cards: Name, Title, Tier badge
- Click to navigate to that contact's detail page

TAB 4: OUTREACH HISTORY
- If outreach API exists on :8300, fetch sequences for this contact
- Otherwise show placeholder: "Outreach tracking coming soon"

TAB 5: DOCUMENTS
- Search documents collection for this contact name
- Show matching documents as cards with snippets

Integration with existing app:
- Add 'contactdetail' to the TabId type in src/types/index.ts
- Add case to switch in App.tsx
- Add a way to navigate to it (e.g., clicking a contact name in Contacts.tsx sets the activeTab to 'contactdetail' with the contact name stored in state)

═══ TASK 2: Build Program Detail Page ═══

Create src/pages/ProgramDetail.tsx — full program intelligence view.

Data loading:
- Accept a programName prop
- Query programs collection for this program
- Query contacts collection filtered by program
- Query jobs collection filtered by program
- Query intelligence_reports for this program

Layout — Tabbed interface:

TAB 1: OVERVIEW
- Program header: Name, Acronym, Agency, Prime Contractor, Sub Contractors, Contract Value, PoP dates
- Key metrics row: Active Jobs count, Known Contacts count, Intelligence Reports count
- "AI Insight" section: POST /ask/smart for program assessment
- "Research This Program" button → POST /agents/research

TAB 2: CONTACTS
- All contacts at this program, sorted by tier (Tier 1 first)
- TanStack Table with columns: Priority, Name, Title, Tier, Location, Email
- Click name → navigate to ContactDetail

TAB 3: LABOR GAPS
- Jobs mapped to this program from jobs collection
- Group by role type
- Show unfilled count per role

TAB 4: COMPETITIVE LANDSCAPE
- "Run Competitive Analysis" button → POST /agents/research with competitive focus
- Display any existing CompetitiveReport results

TAB 5: INTELLIGENCE
- All intelligence_reports mentioning this program
- Timeline view with dates

Integration: Same pattern as ContactDetail — add to TabId, switch, and navigation.

═══ TASK 3: Upgrade Contacts list to TanStack Table with Qdrant filters ═══

Enhance src/pages/Contacts.tsx:
1. Replace the current table with @tanstack/react-table
2. Add payload filter dropdowns above the table:
   - Program: AF DCGS - Langley, AF DCGS - PACAF, AF DCGS - Wright-Patt, Army DCGS-A, Navy DCGS-N, Corporate HQ
   - Tier: Tier 1 through Tier 6
   - BD Priority: 🔴 Critical, 🟠 High, 🟡 Medium, ⚪ Standard
   - Location Hub: Hampton Roads, San Diego Metro, DC Metro, Dayton/Wright-Patt
3. When filters change, POST /search or POST /contacts/filter with Qdrant payload filters
4. Columns: BD Priority (dot), Name (clickable → ContactDetail), Title, Program (badge), Tier (badge), Location, Email, Phone
5. Enable sorting on all columns
6. Add "Export CSV" button for selected rows

═══ TASK 4: Enhance OrgChart with BD Priority coloring ═══

Review src/pages/ContactOrgChartPage.tsx and src/components/OrgChartGraph.tsx:
1. Ensure the G6 graph renders contacts from Qdrant
2. Add BD Priority color coding: 🔴 = red border, 🟠 = orange, 🟡 = yellow, ⚪ = gray
3. Add filter controls: Program dropdown, Tier slider, "Color by" radio (Priority / Program / Tier)
4. Node click → show tooltip with contact details + "View Profile" link
5. Node double-click → navigate to ContactDetail page

═══ TASK 5: Add cross-entity navigation from detail pages ═══

Ensure clicking a program name in ContactDetail navigates to ProgramDetail, and clicking a contact name in ProgramDetail navigates to ContactDetail. Wire through the existing cross-navigation pattern in App.tsx (see handleNavigateToProgram, handleNavigateToContractor callbacks).

═══ DELIVERABLES ═══
- [ ] ContactDetail page with 5 tabs, loading real data from Qdrant
- [ ] ProgramDetail page with 5 tabs, loading real data from Qdrant
- [ ] Contacts list upgraded to TanStack Table with Qdrant payload filters
- [ ] OrgChart enhanced with BD priority coloring
- [ ] Cross-entity navigation working (contact ↔ program)
- [ ] All new pages added to App.tsx routing and Sidebar.tsx

═══ PHASE COMPLETION ═══
[Same format as Phase 1]

Commit: git add -A && git commit -m "feat: Dashboard V6 Phase 2 - entity detail pages, TanStack Table, org chart enhancement" && git push
```

### ═══════════════════════════════════════════════════
### TERMINAL A — Phase 3: Outreach + Analytics + Weekly Intel
### ═══════════════════════════════════════════════════

```
DASHBOARD V6: PHASE 3 — Outreach Manager + Analytics + Weekly Intel Brief

PREREQUISITE: Phase 2 complete — ContactDetail, ProgramDetail, TanStack Table all working.

PROJECT: BD-Automation-Engine
DIRECTORY: C:\Auto-Claud\Auto-Claude\BD-Automation-Engine\
DASHBOARD: C:\Auto-Claud\Auto-Claude\BD-Automation-Engine\dashboard\

═══ TASK 1: Build Outreach Sequence Manager page ═══

Create src/pages/OutreachManager.tsx

This page connects to the outreach sequence engine on Terminal C (port 8300).
If :8300 is not running, show graceful fallback with mock data.

Layout:
TOP: "Create New Sequence" button → modal form:
- Contact Name (text input)
- Contact Email (text input)
- Program (select from known programs)
- Tier (select 1-6)
- Contact Phone (optional)
→ POST http://localhost:8300/sequences

MAIN: Two-view toggle (Timeline / Portfolio):

TIMELINE VIEW:
- Vertical timeline showing all sequences with their steps
- Each step shows: Day, Channel (LinkedIn/Email/Phone), Status (pending/sent/replied/no_response)
- Color coding: sent=blue, replied=green, no_response=yellow, pending=gray

PORTFOLIO VIEW:
- TanStack Table: Contact Name, Program, Current Step, Days Since Start, Last Action, Status, Next Due
- Sortable by any column
- Filter by status: Active, Paused, Completed, No Response

BOTTOM: "Due Today" section showing sequences with pending actions

Data:
- GET http://localhost:8300/sequences → list all
- GET http://localhost:8300/sequences/due → today's actions
- PATCH http://localhost:8300/sequences/{id} → advance step

If Terminal C is unavailable, use mock data to demonstrate the UI.

═══ TASK 2: Upgrade JobsPipeline to Kanban with drag-drop ═══

Enhance src/pages/JobsPipeline.tsx:
1. Add @dnd-kit/core + @dnd-kit/sortable drag-and-drop
2. Kanban columns mapping to BD workflow stages:
   - Scraped (raw_import)
   - Enriched (enriched)
   - Mapped to Program (mapped)
   - Contact Found (contacted)
   - Outreach Active (outreach)
   - Meeting Set (meeting)
   - Closed/Won (won)
3. Cards show: Job title, company, location, clearance badge, program match, days in stage
4. Drag between columns to advance status
5. On drop, POST to Hub API to update job status in Qdrant

═══ TASK 3: Build Analytics section ═══

Create src/pages/Analytics.tsx OR enhance ExecutiveSummary.tsx with analytics charts.

Use @tremor/react and recharts (both already installed):

1. "Contacts by Program" — Tremor DonutChart (6 programs)
2. "Contacts by Tier" — Tremor BarChart (6 tiers)
3. "BD Priority Distribution" — colored bar chart (Critical/High/Medium/Standard)
4. "Jobs by Stage" — horizontal bar chart showing pipeline stages
5. "Agent Activity Over Time" — Recharts area chart (runs per day, from GET /agents/tasks)
6. "Intelligence Coverage" — heatmap: programs × intelligence types
7. "Top Programs by Contact Count" — Tremor BarList

Data comes from GET /stats and collection-level queries.

═══ TASK 4: Build Weekly Intelligence Brief on dashboard home ═══

Add a new section to ExecutiveSummary.tsx: "Weekly Intelligence Briefing"

Structure:
- "Stale Intelligence" warnings — programs not updated in 7+ days (red highlight)
- AI-generated executive summary:
  - Trigger POST /agents/weekly-intel with top 5 DCGS programs
  - Display the structured result or use cached last result
- Sections: New Opportunities, Program Updates, Contact Activity, Competitive Moves
- Each section: 3-5 bullet points with linked entity names (clickable → detail pages)
- "Quick Stats" comparison: This Week vs Last Week (contacts added, jobs scraped, outreach sent)

═══ TASK 5: Final polish ═══

1. Add loading skeletons to new pages (use existing src/components/ui/Skeleton.tsx)
2. Add error boundaries to new pages (use existing ErrorBoundary.tsx pattern)
3. Add breadcrumb navigation on detail pages: Dashboard > Contacts > {Name}
4. Verify keyboard shortcuts work: Cmd+K opens CommandPalette, / focuses search
5. Test dark mode on all new pages (ThemeSwitcher already exists)
6. Test responsive layout on smaller screens

═══ DELIVERABLES ═══
- [ ] Outreach Manager page with timeline + portfolio views
- [ ] JobsPipeline upgraded with @dnd-kit drag-drop Kanban
- [ ] Analytics with 7+ charts
- [ ] Weekly Intelligence Brief on dashboard home
- [ ] Loading skeletons + error boundaries on new pages
- [ ] All cross-entity navigation verified

═══ PHASE COMPLETION ═══
[Same format as Phase 1]

Commit: git add -A && git commit -m "feat: Dashboard V6 Phase 3 - outreach manager, Kanban pipeline, analytics, weekly intel brief" && git push
```

### ═══════════════════════════════════════════════════
### TERMINAL B — Support Tasks (Parallel with Terminal A)
### ═══════════════════════════════════════════════════

```
DASHBOARD SUPPORT: API Enhancements for Dashboard

PROJECT: Data-Scraper
DIRECTORY: C:\Auto-Claud\data-scraper\
BRANCH: master

You are enhancing the BD Hub API to support the dashboard frontend.
The Hub API runs on port 8100 from the BD-Automation-Engine project.
You can push data TO the Hub from Data-Scraper.

═══ TASK 1: Verify /contacts/filter and /programs/filter endpoints exist ═══

Check if the Hub API already has these filtered search endpoints.

Test:
curl -X POST http://localhost:8100/contacts/filter -H "Content-Type: application/json" -d '{"program": "AF DCGS - PACAF", "limit": 5}'
curl -X POST http://localhost:8100/programs/filter -H "Content-Type: application/json" -d '{"prime": "GDIT", "limit": 5}'

If they DON'T exist, create them in the Hub API (you have access via hub/hub_client.py).
These endpoints should use Qdrant scroll() with payload filters when no query text, and search() with filters when query text is provided.

═══ TASK 2: Verify /dashboard/stats endpoint ═══

The dashboard home page needs a consolidated stats endpoint.

Test:
curl http://localhost:8100/dashboard/stats

If it doesn't exist or returns incomplete data, check what /stats returns and verify it includes:
- Per-collection vector counts
- Agent task counts (total, completed, failed)
- Last agent run timestamp

═══ TASK 3: Run fresh job scrape and push to Qdrant ═══

1. Run the Insight Global scraper (Apex is blocked):
   python scrapers/insight_global.py
   OR trigger via Apify API if the local scraper uses the actor

2. Process results through the enrichment pipeline
3. Push enriched jobs to Qdrant jobs collection via Hub API:
   POST http://localhost:8100/ingest/document

4. Verify jobs collection count increased

═══ TASK 4: Ensure CORS allows :5173 ═══

If the Hub API is defined in THIS project (or shared), ensure CORS middleware includes:
- http://localhost:5173 (Vite dev)
- http://localhost:3000 (alternative dev)

═══ DELIVERABLES ═══
- [ ] /contacts/filter endpoint verified or created
- [ ] /programs/filter endpoint verified or created
- [ ] /dashboard/stats returns comprehensive data
- [ ] Fresh job scrape completed and pushed to Qdrant
- [ ] CORS allows dashboard origin

Commit: git add -A && git commit -m "feat: Dashboard support - filtered endpoints, stats, fresh scrape" && git push
```

### ═══════════════════════════════════════════════════
### TERMINAL C — Support Tasks (Parallel with Terminal A)
### ═══════════════════════════════════════════════════

```
DASHBOARD SUPPORT: Outreach API + Data Exports

PROJECT: N8N-Builder
DIRECTORY: C:\Auto-Claud\N8N-Builder\
BRANCH: master

═══ TASK 1: Expose outreach sequence engine via FastAPI on :8300 ═══

The outreach sequence engine already exists at src/outreach/sequence_engine.py.
Wrap it in a FastAPI app:

Create src/outreach/api.py:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .sequence_engine import SequenceEngine

app = FastAPI(title="PTS Outreach API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = SequenceEngine()

@app.get("/health")
def health():
    return {"status": "healthy", "port": 8300, "engine": "outreach_sequences"}

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

@app.get("/sequences/{seq_id}")
def get_sequence(seq_id: str):
    return engine.get_sequence(seq_id)
```

Run: python -m uvicorn src.outreach.api:app --host 0.0.0.0 --port 8300

Test: curl http://localhost:8300/health

═══ TASK 2: Create org chart data export for dashboard ═══

The dashboard org chart needs hierarchical JSON. Create a script:

scripts/export_org_chart.py:
1. Query Qdrant contacts collection (filter by DCGS programs)
2. Build tree: Program → Tier 1 → Tier 2 → ... → Tier 6
3. Output G6-compatible JSON:
```json
{
  "nodes": [
    {"id": "prog_1", "label": "AF DCGS - PACAF", "type": "program"},
    {"id": "contact_1", "label": "Kingsley Ero", "type": "contact", "data": {
      "title": "Acting Site Lead", "tier": 3, "priority": "critical"
    }}
  ],
  "edges": [
    {"source": "prog_1", "target": "contact_1"}
  ]
}
```
4. Save to a known location and optionally POST to Hub API

═══ TASK 3: Create Neo4j graph data export ═══

Export Neo4j relationships for the dashboard KnowledgeGraph page:

scripts/export_graph_data.py:
1. Query Neo4j for all nodes and relationships
2. Format as graph JSON compatible with the KnowledgeGraph page
3. Save output and optionally serve via the Hub API

═══ DELIVERABLES ═══
- [ ] Outreach API running on :8300 with /sequences CRUD
- [ ] Org chart JSON export created
- [ ] Neo4j graph data export created

Commit: git add -A && git commit -m "feat: Outreach API on :8300, org chart export, graph data export" && git push
```

---

## SECTION 4: EXECUTION ORDER

| Step | Terminal | Action | Duration |
|---|---|---|---|
| 1 | A | Phase 1: Verify + Fix Hub API | 1-2 hours |
| 1 | B | Support: Verify endpoints + fresh scrape | 1-2 hours (parallel) |
| 1 | C | Support: Outreach API + exports | 1-2 hours (parallel) |
| 2 | A | Phase 2: Entity detail pages | 3-5 hours |
| 3 | A | Phase 3: Outreach + analytics + weekly intel | 3-5 hours |

**Total estimated**: 8-12 hours of Auto-Claude time across 3 terminals

### Between Phases (Your 30-second task)

1. Copy the "COPY-PASTE FOR ORCHESTRATOR" paragraph from the completed terminal
2. Paste it into this Claude chat
3. Claude verifies + generates next phase prompt (or uses pre-written prompt above)
4. Paste the next prompt into the terminal

---

## SECTION 5: QUICK REFERENCE — WHAT NOT TO DO

| ❌ Don't | ✅ Do Instead |
|---|---|
| Rebuild existing pages | Enhance/fix data connections |
| Install npm packages (already there) | Audit what's installed, use it |
| Create new routing system | Add to existing activeTab switch |
| Create new API client | Use existing hubApiClient singleton |
| Create new hooks | Use existing useHubApi.ts hooks |
| Change vite.config.ts proxy pattern | Use existing per-route proxy |
| Reference n8n anywhere | It's removed — use Python-native |
| Use wrong directory paths | See corrected paths in Section 1 |
