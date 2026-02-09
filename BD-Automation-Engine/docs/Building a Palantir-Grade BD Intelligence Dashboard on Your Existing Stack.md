# Building a Palantir-grade BD intelligence dashboard on your existing stack

**Your existing infrastructure — 1.4M vectors, 5 CrewAI agents, Neo4j knowledge graph, 12 Qdrant collections, and 157 API endpoints — already constitutes 70% of a world-class intelligence platform.** The missing piece is a frontend architecture that surfaces all this power through an intuitive, data-dense interface that makes every contact, program, and contract feel instantly accessible. The recommended approach extends your current React 19 + shadcn/ui + TanStack Query stack rather than replacing it, adding targeted libraries for dashboard analytics (Tremor), large-scale graph visualization (Cosmograph + G6), AI-native chat (Vercel AI SDK + assistant-ui), and real-time agent integration (SSE streaming + CopilotKit). This architecture can deliver the "AI that has memorized your entire database" experience within your existing hub-and-spoke infrastructure.

---

## The foundation: extend your stack, don't replace it

After evaluating Tremor, Refine, AdminJS, Retool, Tooljet, Appsmith, and custom builds, the verdict is unambiguous: **your current React 19 + Vite 7 + shadcn/ui + TanStack Query stack is the correct foundation**. Refine and AdminJS would add abstraction layers over your 157 endpoints without meaningful benefit. Low-code platforms like Retool cannot integrate into an existing React app and create security concerns for defense data. AdminJS is fundamentally incompatible — it requires a Node.js backend, not FastAPI.

The optimal strategy is a **targeted library augmentation** approach:

| Dashboard need | Recommended addition | Why it wins |
|---|---|---|
| KPI cards, charts, analytics | **Tremor** | Same Tailwind + Radix foundation as shadcn/ui, copy-paste philosophy, 250+ dashboard blocks |
| Enterprise data grids | **TanStack Table v8** | Headless, virtual scrolling, server-side pagination, native shadcn integration |
| Primary charting | **Recharts 3.0** | Major 2025 update with accessibility improvements, used by Tremor under the hood |
| Specialized viz (heatmaps, Sankey) | **Nivo** | Canvas + SVG rendering for network graphs, chord diagrams, relationship mapping |
| Drag-and-drop (Kanban) | **@dnd-kit** | 10KB, hook-based, React 19 compatible, keyboard accessible |
| Command palette | **cmdk** (via shadcn) | Already available through shadcn/ui Command component |
| Forms | **React Hook Form + Zod** | Integrates with shadcn/ui form components and matches Pydantic schemas |
| Animations | **Framer Motion** | Timeline sequences, transitions, progressive disclosure |

**Tremor deserves special emphasis.** It shares shadcn/ui's DNA — Tailwind CSS, Radix UI primitives, Apache-2.0 license, copy-paste philosophy — and fills the exact gap between shadcn/ui's general components and the dashboard-specific widgets you need: tracker components, bar lists, sparklines, KPI cards, and micro-visualizations. These two libraries compose seamlessly because they share the same design system foundation.

---

## Making search feel like talking to an AI with perfect memory

The single most impactful feature is an **AI-powered search experience where users type a natural language question and get instant, cited answers from all 1.4M vectors**. Achieving this requires an agentic RAG architecture with intelligent query routing — not a naive search across all 12 collections simultaneously.

**The recommended architecture has four layers:**

**Layer 1: Intent classification and query routing.** An LLM-based router analyzes each query and selects which of the 12 Qdrant collections to search. "Find CACI contacts at Fort Belvoir" routes only to the contacts collection. "What intelligence do we have about the ABRAMS program?" fans out to intelligence_reports, bullhorn_notes, programs, and federal_contracts. This routing step eliminates **75%+ of unnecessary search latency** and improves result relevance by avoiding noise from irrelevant collections.

**Layer 2: Hybrid retrieval with parallel execution.** For each selected collection, run three retrieval strategies concurrently: dense vector search (semantic similarity via your existing OpenAI embeddings), sparse BM25 search (exact keyword matching for names, contract numbers, clearance levels — Qdrant natively supports this), and Neo4j graph traversal (relationship-aware context enrichment using the `HybridCypherRetriever` from the neo4j-graphrag package). Merge results using **Reciprocal Rank Fusion (RRF)**.

**Layer 3: Cross-encoder reranking.** Pool the top 20 results from each selected collection (typically 40-80 documents total) and rerank with your existing ms-marco-MiniLM cross-encoder. This consistently delivers a **20-35% accuracy improvement** with only 200-500ms additional latency — negligible against the 2-3 second LLM generation time.

**Layer 4: LLM synthesis with citations.** The reranked top 5-10 results feed into the LLM prompt with metadata (collection name, entity type, entity ID, timestamp). The LLM generates a natural language answer with inline citations that render as clickable links navigating to entity detail pages.

**For the frontend chat interface**, three libraries compose into a production-grade experience. **Vercel AI SDK** (20M+ monthly downloads) provides the `useChat` hook for streaming conversation state, the `streamText` server function, and the `ToolLoopAgent` class for multi-step reasoning. **assistant-ui** (Y Combinator-backed) provides Radix-style composable chat primitives that integrate with shadcn/ui's design system. **shadcn/ui's new AI components** (shadcn.io/ai) provide 25+ purpose-built components including inline citations, source cards, reasoning blocks, and tool call visualization — all following the copy-paste philosophy.

The user experience should combine a **command palette (⌘K) for quick entity search** with a **persistent AI copilot sidebar for conversational exploration**. Initial queries go through cmdk for instant entity cards; complex follow-ups open the sidebar chat. This mirrors the Raycast/Linear pattern that power users find most efficient.

**Performance targets for "instant recall"** are achievable with your current Qdrant deployment. Qdrant benchmarks show **3ms response time for 1M OpenAI embeddings** with scalar quantization (INT8), which reduces memory by 75% and doubles search speed with under 1% accuracy loss. With payload indexing on frequently filtered fields (company, clearance_level, location, date) and HNSW parameter tuning (ef=64-128), sub-100ms per collection is realistic. The three-phase progressive rendering strategy — cached entity cards at 0-200ms, vector search results at 200-500ms, streaming AI synthesis at 500ms-3s — makes the experience feel instant even before the LLM finishes generating.

---

## Graph visualization requires a tiered architecture, not one library

No single graph library handles both 200K+ entity overviews and detailed 500-node subgraph exploration. **Reagraph, already installed in your project, has a critical performance limitation**: users report 12-28 FPS at 400 nodes, browser hangs at 2,600 nodes, and crashes at 40K+ nodes. It remains valuable for small detail views but cannot serve as your primary graph engine.

The recommended tiered architecture:

**Tier 1 — Full dataset overview (200K+ nodes): Cosmograph.** This is the only library proven to handle **1 million nodes and several million edges** in real-time in-browser. It achieves this through GPU-accelerated force layout computation — all physics simulation runs on WebGL shaders rather than the CPU. The `@cosmograph/react` component provides a simple declarative API. Use this for the "big picture" view where all programs, contractors, contacts, and jobs appear as a colored point cloud revealing natural clustering. Note: Cosmograph requires a commercial license (CC BY-NC 4.0 for non-commercial).

**Tier 2 — Focused exploration (1K-50K nodes): G6 v5 with Graphin.** AntV's G6 has the **richest layout algorithm set** among open-source options — force-directed, hierarchical (dagre), radial, concentric, tree, mindmap, and compactBox. The v5.0 release introduces Rust+WASM layout computation and WebGPU acceleration. Its "combo" feature (grouped nodes) is ideal for clustering entity types. Graphin provides the official React wrapper. Use G6 for mid-level exploration when users filter to a program ecosystem, geographic region, or competitive landscape.

**Tier 3 — Detail views (<500 nodes): Reagraph.** Keep what you have. At this scale, Reagraph's WebGL rendering is beautiful, its React API is native, and its 3D mode provides immersive exploration. Use for individual program subgraphs, contact relationship maps, and path-finding between specific entities.

**For org charts specifically**, G6's tree layout handles your 965 contacts with expand/collapse, color-coding by BD priority (Critical=red, High=orange, Medium=yellow, Standard=gray), and level-of-detail rendering. If budget permits, **yFiles for React** ($17K/developer one-time) provides the industry's best org chart component with purpose-built LOD rendering, assistant positioning, and deep customization — it's what Palantir's own Blueprint.js was inspired by.

**For temporal relationship visualization**, integrate **vis-timeline** for analytical timeline exploration (zoomable, interactive, handles dense temporal data) and **react-chrono** for narrative contact history timelines. Your Graphiti temporal knowledge graph stores bi-temporal data (`t_valid` and `t_invalid` for every relationship edge), enabling point-in-time graph reconstruction — "show me the org chart as of 6 months ago" — which should drive a timeline slider that reactively updates the graph visualization.

---

## Adopt Palantir's ontology pattern for entity-centric navigation

The single most important design principle from intelligence platforms is **entity-centric navigation over table-centric browsing**. Palantir's effectiveness stems from its Ontology — a semantic layer where real-world entities (people, organizations, contracts, events) are modeled as typed objects with explicit relationships. Users explore entities and their connections, not database tables and columns.

For your BD dashboard, this means defining canonical entity types — **Program, Contact, Agency, Competitor, Opportunity, Contract, Job, MeetingNote** — and making every UI interaction navigate between related entities. When a user views a Program card, they see key contacts (clickable), competitive landscape (clickable to competitor profiles), active jobs (clickable), and related contracts (clickable). The entire dashboard becomes a navigable knowledge graph.

**The recommended three-tier layout:**

The **left rail** provides entity-type navigation (collapsible sidebar with Programs, Contacts, Jobs, Contracts, Intelligence icons), saved views/filters, and quick search. The **main content area** uses a master-detail split pane — entity list on the left with faceted filtering, entity detail on the right with tabbed sub-views (Overview, Intelligence, Relationships, Timeline, Documents). The **right panel** (collapsible) houses the AI copilot sidebar and background task queue.

**The home dashboard should default to the Weekly Intelligence Briefing** — this mirrors the military Common Operating Picture pattern. Structure it as: priority alerts strip at top (new RFPs, competitor moves, leadership changes), AI-generated executive summary of the week's key intelligence, then sectioned cards for New Opportunities, Program Updates, Contact Activity, and Competitive Intelligence. A "Stale Intelligence" indicator highlights entities that haven't been updated, driving the OODA loop (observe → orient → decide → act).

**Intelligence Cards and Contact Profiles need an AI Insight Band** — a visually distinct section (different background color, AI attribution badge) that shows AI-generated analysis separate from human-entered data. Every Program Intelligence Card should display: contract value, prime/sub relationships, PTS involvement status, known pain points, active jobs, key contacts with relationship strength indicators (green/yellow/red dots), competitive landscape, and AI-recommended BD actions. Every Contact Intelligence Profile should show: hierarchy tier badge, BD priority, program assignments, Bullhorn interaction history, HUMINT gathered, outreach sequence status, and an "AI-generated outreach script" button that triggers the outreach_composer agent.

**Data density without overwhelm** follows the Bloomberg Terminal principle: **hide complexity behind consistent navigation patterns, and prioritize temporal density (speed of navigation) over visual density (cramming more on screen)**. Practical implementation means 14px body font with 4/8px grid spacing, progressive disclosure everywhere (summary → detail → full exploration), keyboard shortcuts for power users, and a user-configurable density toggle (compact/comfortable/spacious).

---

## Integrating CrewAI agents as first-class dashboard citizens

Your 5 CrewAI agents (program_researcher, contact_enricher, competitive_analyst, outreach_composer, humint_analyst) should be triggerable from contextual UI elements and stream their progress in real-time. The recommended integration stack is **CopilotKit with the AG-UI protocol** for full agent-to-UI communication, plus **SSE streaming from FastAPI** for simpler status updates.

**Agent trigger patterns** should follow three levels of integration. **Inline action buttons** on entity cards ("Research this program," "Enrich this contact," "Generate competitive analysis") trigger background tasks and show loading states. The **command palette** (⌘K) accepts natural language requests to trigger workflows ("run weekly intelligence briefing," "analyze CACI competitive landscape at Fort Belvoir"). An **AI Agent widget** (Palantir's AIP pattern) provides a dedicated panel where users interact with agents that have full access to the data ontology.

**For streaming agent progress to the frontend**, SSE is the recommended protocol over WebSockets. SSE provides built-in auto-reconnection, works with standard HTTP infrastructure, and is easier to debug in browser DevTools. The Vercel AI SDK has standardized on SSE for all streaming. Implementation follows a straightforward pattern:

The FastAPI backend exposes a `/api/tasks/{task_id}/stream` SSE endpoint that emits `progress`, `intermediate_result`, and `complete` events as the CrewAI crew executes. The React frontend uses a custom `useAgentTask` hook that creates an `EventSource` connection, updates progress state incrementally, and renders intermediate results as they arrive. For tasks under 10 seconds, show an inline spinner with status text. For 10-60 second tasks, show a determinate progress bar with step descriptions. For tasks over 1 minute, execute in background with a push notification on completion — never block users for extended periods.

**Structured Pydantic outputs map directly to typed React components.** CrewAI's `output_pydantic` parameter on tasks produces validated models like `ProgramAnalysis`, `ContactEnrichment`, or `CompetitiveReport`. These map 1:1 to TypeScript interfaces on the frontend (use Zod schemas for client-side validation via Vercel AI SDK's `useObject` hook). Each Pydantic model type gets a dedicated card renderer — a `ProgramAnalysis` renders as a Program Intelligence Card, a `CompetitiveReport` renders as a competitive landscape view.

**For real-time data synchronization**, TanStack Query's event-based invalidation pattern is optimal: a WebSocket connection to your FastAPI backend receives entity-change events, which trigger `queryClient.invalidateQueries()` for the affected query keys. Only active queries refetch, avoiding over-pushing. Since Qdrant doesn't support native change subscriptions, build a middleware event bus: when your backend writes to Qdrant (via upsert), simultaneously publish an event to the WebSocket channel. Neo4j provides native GraphQL Subscriptions via Change Data Capture for graph updates.

**Mem0 memory integration** should power three dashboard features: cross-session personalization (the AI remembers user preferences, frequently queried entities, and past analysis patterns), a "Memory Panel" on entity detail pages showing what the AI "remembers" about that entity, and memory correction controls letting users edit or delete incorrect AI memories. Mem0 benchmarks show **91% faster responses** and **90% lower token usage** compared to full-context approaches, making it essential for keeping the copilot responsive.

---

## The Kanban pipeline and outreach sequencing views

The **Job Pipeline Tracker** should implement a horizontal Kanban board using **@dnd-kit** — a 10KB, hook-based library with zero dependencies that provides smooth drag-and-drop with `DragOverlay` for polished animations. Pipeline stages map to your BD workflow: Scraped → Mapped to Program → Contacts Identified → Outreach in Progress → Meeting Set → Job Requisition Obtained. Each card shows the opportunity with company name, contract value, key contact, and next action. Column headers display aggregate value ($) and count. Use TanStack Query mutations for optimistic updates on column transitions.

**Outreach sequencing** should follow the Apollo.io vertical timeline pattern — each step is a card showing step type (email, call, LinkedIn, custom task) connected by vertical lines with configurable delay indicators ("Wait 2 days"). Implement with shadcn/ui Cards arranged vertically with CSS connector lines, dnd-kit for step reordering, and Framer Motion for transitions. A secondary **Gantt-like view** (rows = contacts, columns = time periods) shows the entire outreach portfolio at a glance, with color coding: green for completed, blue for scheduled, red for bounced, yellow for pending. Tremor's Tracker component provides at-a-glance sequence health metrics alongside each timeline.

**Cost tracking for LLM usage** should use **Langfuse** (open-source, self-hosted) for token/cost tracking and prompt management, integrated with **LiteLLM** as a proxy that provides per-user and per-team spend tracking with built-in usage quotas. Display daily token consumption as a stacked bar chart (input vs. output), agent-type cost breakdown as a pie chart, per-user quota meters, and a sortable agent run history table with duration, tokens, cost, and status columns.

---

## Conclusion: from infrastructure to intelligence advantage

The architectural recommendation distills to five key principles that should guide implementation. First, **extend rather than replace** — your React 19 + shadcn/ui + TanStack Query stack is the correct foundation; add Tremor, Cosmograph, G6, Vercel AI SDK, and dnd-kit as targeted augmentations. Second, **build entity-centric, not table-centric** — adopt Palantir's ontology pattern where every interaction navigates between typed entities and their relationships. Third, **tier your graph visualization** — Cosmograph for 200K+ overviews, G6 for mid-scale exploration, Reagraph for detail views. Fourth, **make AI a first-class citizen** — the copilot sidebar, agent triggers, and intelligence cards with AI insight bands should make the system feel like a brilliant BD analyst who has memorized every contact, program, and contract. Fifth, **prioritize temporal density** — fast navigation, streaming responses, progressive rendering, and keyboard shortcuts create more analyst productivity than visual density alone.

The implementation should proceed in three phases: Phase 1 deploys the agentic RAG search + AI copilot sidebar + entity navigation framework (highest impact). Phase 2 adds the tiered graph visualization, Kanban pipeline, and outreach sequencing views. Phase 3 adds the weekly intelligence briefing, analytics dashboard, and cost tracking. This sequence delivers the most transformative capability — conversational access to all 1.4M vectors — first, while building toward the full Palantir-grade intelligence platform.