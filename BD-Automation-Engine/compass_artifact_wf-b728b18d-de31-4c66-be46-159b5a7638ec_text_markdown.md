# Next-gen defense BD platform: the 2026 architecture blueprint

A consolidated 2-repo monorepo built on **uv workspaces, LangGraph 1.0.8, Supabase Pro with pgvector, Voyage 4 embeddings, and Neo4j AuraDB** delivers a production-grade defense BD intelligence platform for **$500–$1,200/month** — a fraction of what fragmented architectures cost. The timing is exceptional: Voyage 4 launched January 15, 2026 with industry-first shared embedding spaces; Claude Opus 4.6 dropped February 5 with agent teams and 1M-token context; and FPDS decommissions February 24, making SAM.gov API migration urgent. This report synthesizes current-state research across all 10 architecture domains with specific versions, pricing, and production-proven patterns.

---

## 1. Python monorepo consolidation with uv workspaces

The monorepo tooling question is settled in 2026: **uv v0.10.2** (released February 10, 2026) with native workspaces is the clear winner. Apache Airflow manages 120+ distributions from a single monorepo with uv workspaces — presented at FOSDEM 2026 by their top committer. uv resolves 900+ packages in seconds with a single cross-platform lockfile, and its Cargo-style workspace model maps perfectly to domain-driven design.

The recommended structure organizes code by business domain rather than technical layer. Each domain (Programs, Contacts, Contracts, Jobs, Intelligence, Scraping, Agents, Embeddings) becomes a self-contained module with its own router, schemas, service layer, and repository. Shared code lives in internal packages (`bd-core` for models/config, `bd-agents` for LangGraph agents, `bd-embeddings` for vector operations) referenced via `{ workspace = true }` in `pyproject.toml`.

**Endpoint consolidation from 1,500+ to ~100–150** follows a three-phase audit: classify each endpoint as production/scaffold/duplicate/dead, merge interdependent resources, and replace variant endpoints with query parameters. A BD platform naturally decomposes to roughly **8 endpoints per domain** (5 CRUD + 2–3 specialized), yielding ~80 core endpoints across 10 domains. FastAPI's `APIRouter` with prefix/tags/dependencies keeps each domain's routes modular while a single `create_app()` factory registers everything under `/api/v1`.

Key tooling versions: **uv v0.10.2** (build backend: `uv_build`), **Ruff** for linting/formatting (replaces Black/isort/flake8), **ty** (Astral's type checker, December 2025), and **Python 3.12+** as the runtime target.

---

## 2. PostgreSQL consolidation eliminates 50 databases

Migrating 50+ SQLite databases into a single Supabase PostgreSQL instance eliminates the platform's most fragile architectural layer. **pgloader v3.6.9+** handles batch migration with automatic type conversion, but the critical step is designing the unified schema first, then loading into pre-existing tables with deduplication.

### The hybrid JSONB + typed columns pattern

For wide entity tables like Jobs (97 fields) and Programs (74 fields), the proven pattern uses **15–25 typed columns** for queryable/filterable/joinable fields plus a single **JSONB `details` column** for everything else. Typed columns get B-tree indexes; the JSONB column gets a GIN index with `jsonb_path_ops`. Pydantic models in FastAPI validate JSONB content before insertion, maintaining type safety without the performance penalties of 97-column tables.

### pgvector replaces Qdrant at 1.4M vectors

**pgvector 0.8.0** (October 2024) introduced iterative index scans that deliver **5.7x query improvement** and 100x better filtered search recall — exactly what's needed for vector search combined with relational filters. At 1.4M vectors with 1024 dimensions, pgvector with **halfvec (float16)** quantization reduces storage to ~8.5–11.5 GB total while maintaining near-zero recall loss. Timescale's pgvectorscale benchmarks show **471 QPS at 99% recall** on 50M vectors — 11.4x better than Qdrant at the same recall level. For this scale, pgvector eliminates an entire infrastructure dependency.

**Supabase Pro at $25/month** includes 8 GB database storage, Supavisor connection pooling, Auth, and real-time subscriptions. Connection pooling through Supavisor transaction mode (port 6543) with SQLAlchemy `NullPool` and disabled prepared statement caching is the production pattern for async FastAPI. Partitioning is only warranted for the Activities table if it grows past 1M+ rows — at 400K, standard B-tree indexes suffice.

---

## 3. LangGraph 1.0.8 replaces CrewAI with durable orchestration

**LangGraph 1.0.8** (February 6, 2026) delivers what CrewAI cannot: durable state persistence, production-grade human-in-the-loop, and PostgreSQL-backed checkpointing. The migration from 13 CrewAI agents maps cleanly to LangGraph's supervisor pattern.

### Multi-agent orchestration

The `create_supervisor()` pattern from `langgraph-supervisor-py` replaces CrewAI's hierarchical process model. Each CrewAI agent becomes a `create_react_agent()` node with tools and a system prompt; each Crew becomes a compiled `StateGraph`. The supervisor agent delegates to specialized sub-agents via handoff tools, with full state visibility and checkpoint persistence at every step.

### Human-in-the-loop goes production-grade

LangGraph's first-class `interrupt()` API replaces the current file-based JSON approval system. When a workflow reaches a gate review, `interrupt()` serializes the full state to PostgreSQL and pauses execution — consuming **zero compute resources** while awaiting human approval. Days or weeks later, `Command(resume={"decision": "approved"})` restores execution on any server. The `langgraph-checkpoint-postgres` package (v3.0.4) works directly with Supabase's pooled connection strings.

### Key architecture decisions

- **State design**: Use `TypedDict` with `Annotated[list, operator.add]` for append-only audit trails and plain types for override-on-write fields
- **Durability mode**: `"sync"` for BD capture workflows (every checkpoint persisted before proceeding)
- **MCP integration**: `langchain-mcp-adapters` connects agents to MCP servers for SAM.gov, document analysis, and CRM access via `MultiServerMCPClient`
- **LangGraph Platform pricing**: Plus plan at $39/seat/month, with production uptime costing ~$155/month for 24/7 deployment. For defense contracting, **self-hosted Enterprise** keeps data in your VPC

---

## 4. Voyage 4 embeddings deliver 14% better retrieval at the same cost

**Voyage 4 launched January 15, 2026** and immediately took the #1 position on the RTEB leaderboard. The headline innovation is an **industry-first shared embedding space** across all four models — voyage-4-large, voyage-4, voyage-4-lite, and voyage-4-nano (open-weight, Apache 2.0).

### The asymmetric strategy changes the economics

Embed documents once with **voyage-4-large** ($0.12/M tokens) for maximum quality. Embed queries at runtime with **voyage-4-lite** ($0.02/M tokens — the same price as the current OpenAI text-embedding-3-small). Because all Voyage 4 models share one embedding space, the lite query model benefits from the large model's document representations. This produces **14%+ better retrieval** than OpenAI text-embedding-3-large at the same per-query cost.

The one-time re-embedding cost for 1.4M documents (~700M tokens) is approximately **$40–60 with batch API discounts**. The Voyage 4 models default to **1024 dimensions** with Matryoshka learning supporting 256/512/1024/2048. Combined with pgvector's halfvec quantization, switching from 1536d float32 (OpenAI) to 1024d float16 (Voyage 4) reduces vector storage by **~75%**.

### Specialized models for legal and contextual retrieval

**voyage-law-2** ($0.12/M tokens, 16K context) tops the MTEB legal retrieval leaderboard and outperforms OpenAI v3 large by 6% on legal datasets — relevant for FAR/DFARS regulation embeddings. **voyage-context-3** ($0.18/M tokens, 32K context) embeds chunk content WITH global document context, outperforming standard chunking by 14.24% — ideal for cross-referenced regulatory texts. However, these specialized models are outside the Voyage 4 shared space and should be evaluated against voyage-4-large on your specific corpus.

---

## 5. Neo4j AuraDB Professional at $65/month with full graph analytics

**Neo4j AuraDB Professional** at **$65/GB/month** (minimum 1 GB) provides managed graph infrastructure with all 65+ Graph Data Science algorithms included at no additional cost via the Graph Analytics Plugin. For a graph starting at 3K nodes growing to 50K+, the 1 GB instance is sufficient.

### Graph algorithms that matter for BD intelligence

**PageRank** on AWARDED_TO/PRIMES_ON relationships identifies the most influential prime contractors. **Louvain community detection** on PARTNERS_WITH/SUBS_TO reveals natural teaming ecosystems — clusters of companies that consistently work together. **Betweenness centrality** finds key connector contacts who bridge different contractor communities. **Node similarity (Jaccard)** discovers companies with overlapping contract portfolios — potential teammates or competitors.

### GraphRAG combines structured traversal with semantic search

The `langchain-neo4j` package provides `Neo4jGraph` for Cypher queries, `Neo4jVector` for semantic search on node embeddings, and `LLMGraphTransformer` for auto-populating the graph from unstructured text. A LangGraph workflow routes queries to graph traversal, vector search, or hybrid retrieval based on query type. Multi-hop queries like "find companies that partner with our competitors on programs we're targeting" combine graph traversal's precision with LLM generation's natural language capability.

Neo4j now supports **native vector indexes** (HNSW, up to 4,096 dimensions) with pre-filtering as of the January 2026 release. For the graph's 50K nodes, Neo4j vector indexes can handle semantic search alongside graph traversal, potentially eliminating the need for separate pgvector storage for graph-related embeddings. However, **pgvector remains the better choice for the bulk 1.4M-vector corpus** due to cost efficiency and SQL integration.

### Migration and cost optimization

Migration from Docker to AuraDB is straightforward: `neo4j-admin database dump` creates a dump file, which uploads via the AuraDB Console drag-and-drop (under 4 GB). Start on **AuraDB Free** ($0, 200K node limit) for development, then migrate to Professional. **Pause functionality saves 80%** of running costs — a 1 GB instance paused 16 hours/day costs ~$30–40/month instead of $65.

---

## 6. AI and ML capabilities converge around Claude Opus 4.6

**Claude Opus 4.6** (released February 5, 2026) represents a step change for agentic BD workflows: **1M-token context window** (beta), agent teams that spawn and coordinate sub-agents, automatic context compaction, and an ARC AGI 2 score of 68.8% — nearly double Opus 4.5. Pricing holds steady at **$5/$25 per million tokens** input/output. For cost-sensitive bulk processing, Claude Haiku 4.5 at $1/$5 handles entity extraction and classification, while **Sonnet 4.5** at $3/$15 remains the production workhorse.

### Structured outputs are now GA

Constrained decoding guarantees JSON schema compliance during token generation. For federal document entity extraction, define Pydantic models for ContractEntity, CompanyProfile, or ComplianceRequirement and pass them as `output_format` — Claude produces validated structured data with 2–3% cost overhead but eliminates all retry logic.

### The MCP ecosystem reaches 1,200+ servers

The Model Context Protocol, donated to the Linux Foundation's Agentic AI Foundation in December 2025, now has official servers for PostgreSQL, Filesystem, GitHub, Slack, Google Drive, and Brave Search. Business intelligence servers cover Salesforce/HubSpot CRM (via Apideck), Notion, Google Sheets, and Zapier's 7,000+ app connectors. LangGraph agents connect to MCP servers via `langchain-mcp-adapters`, and LangGraph Platform auto-exposes deployed agents as MCP-accessible tools.

### RAG architecture matures around three stages

The 2026 consensus architecture is: **(1) hybrid BM25 + dense vector retrieval** with Reciprocal Rank Fusion, **(2) cross-encoder reranking** narrowing to 10–50 most relevant chunks (ZeroEntropy zerank-1 delivers +28% NDCG@10 over baseline), and **(3) LLM generation** with assembled context. Hybrid search improves recall 1–9% over vector-only; reranking adds up to 48% improvement in retrieval quality. For defense BD, **contextual retrieval** (prepending document-level context to each chunk before embedding) is particularly valuable for cross-referenced regulatory texts.

### Agentic memory with Mem0

**Mem0** leads the open-source agentic memory space with 26% higher accuracy than OpenAI Memory, 91% lower p95 latency, and 90% token savings versus full-context approaches. The graph variant (**Mem0ᵍ**) stores relational memory in a knowledge graph — ideal for tracking evolving contractor relationships, contact interactions, and opportunity histories across multi-day BD capture workflows. Self-hosting keeps sensitive BD intelligence data under your control.

---

## 7. Next.js 16.1 with shadcn/ui and Tremor for the dashboard

**Next.js 16.1.6 LTS** (patched February 5, 2026) is the right choice for the BD dashboard despite the "SPA for dashboards" conventional wisdom. The 59-page scale benefits from App Router's file-based routing and layouts; RBAC enforcement requires server-side middleware; and Supabase's `@supabase/ssr` package is designed for Next.js. Turbopack is now the stable default for both dev and build, making the developer experience competitive with Vite.

### Component and visualization stack

**shadcn/ui** provides the base component system (forms, navigation, dialogs) while **Tremor** adds purpose-built dashboard components (charts, KPI cards, sparklines, trackers). Both share Tailwind CSS + Radix UI foundations and integrate seamlessly. **TanStack Table v8** (stable; v9 still in alpha) with **TanStack Virtual** handles the 400K+ row data grids — server-side pagination, filtering, and sorting via SQL with virtual scrolling for render performance. **React Flow v12** (`@xyflow/react`) visualizes the contracting entity graph with custom node types per entity, automatic layout via dagre/ElkJS, and built-in interaction (zoom, pan, select).

### Real-time intelligence feeds and RBAC

**Supabase Realtime** via `postgres_changes` pushes new intelligence items to connected clients without additional WebSocket infrastructure. For RBAC, a three-layer pattern works: Supabase Auth Hooks inject `user_role` into JWT custom claims → Next.js middleware enforces route-level access → PostgreSQL RLS policies enforce data-level isolation. The critical performance optimization: always wrap `auth.uid()` in `(SELECT ...)` to cache the result per-statement instead of evaluating per-row.

---

## 8. Infrastructure targets $285–$1,200/month on managed services

**Docker Compose** is the right orchestration for a 1–3 developer team — Kubernetes overhead is unjustifiable at this scale. **Railway** ($10–25/month per service) provides the best developer experience for deploying FastAPI and Next.js with git-push deploys, preview environments per PR, and usage-based pricing.

### Full monthly cost breakdown

| Component | Service | Monthly Cost |
|-----------|---------|-------------|
| Database + pgvector | Supabase Pro | **$25–50** |
| Graph database | Neo4j AuraDB Professional | **$65–100** |
| Workflow automation | N8N Cloud Pro | **$55** |
| Backend + frontend hosting | Railway | **$20–45** |
| AI API usage | Anthropic + OpenAI | **$100–500** |
| Error monitoring | Sentry (free tier) | **$0** |
| Metrics and logs | Grafana Cloud (free tier) | **$0** |
| Secrets management | Doppler (Team) | **$0–12** |
| CI/CD | GitHub Actions | **$4–12** |
| **Total range** | | **$285–800** |

AI API costs are the primary variable — **prompt caching** (90% discount on cached reads with Anthropic), **batch API** (50% off for non-urgent processing), and **model tiering** (Haiku for bulk, Sonnet for production, Opus for complex analysis) keep this manageable. The $500–$1,500/month target is achievable even with moderate AI usage.

**Monitoring**: Sentry (free, 5K errors/month) + Grafana Cloud (free, 10K metric series, 50GB logs) provides comprehensive observability at $0. Scale to ~$45/month if needed. **Secrets management**: Doppler ($4/user/month, SOC 2 Type II) manages SAM.gov, Anthropic, OpenAI, and scraping API keys with automated rotation and CI/CD integration.

---

## 9. FPDS decommissions February 24 — SAM.gov migration is urgent

**FPDS.gov ezSearch decommissions February 24, 2026** — ten days from now. The ATOM Feed follows later in FY2026. All contract award data migrates to SAM.gov, which soft-launched contract awards search in July 2025. Any FPDS ATOM Feed consumers must migrate to the **SAM.gov Contract Awards API** immediately.

### Tango by MakeGov is the developer's shortcut

**Tango API** (docs updated February 13, 2026) unifies FPDS, USASpending, SAM.gov, and Grants.gov into a single REST API with Python and Node.js SDKs, webhooks for near-real-time notifications, response shaping (request only needed fields), and consistent data models. This eliminates the pain of integrating four separate government APIs with different authentication models and data formats.

### Job scraping is simplified by Workday dominance

Virtually every Tier 1 defense contractor (Lockheed Martin, RTX, Northrop Grumman, BAE, L3Harris, Booz Allen, Leidos, SAIC, Boeing) uses **Workday**. The **Fantastic.jobs Career Site Job Listing API** on Apify covers 42 ATS platforms including Workday, indexing 175K+ career sites with AI-enriched data (up to 60 fields per job). New jobs appear within 3 hours of posting. Combined with **Firecrawl Standard** ($83/month) for ad-hoc web intelligence and **Crawl4AI** (free, self-hosted) for sensitive extraction, the data collection pipeline costs approximately **$400–600/month** excluding premium intelligence services.

For contact enrichment, **Apollo.io** ($49–99/month) or **RocketReach** ($75–175/month) provide API-accessible professional data without violating LinkedIn TOS. **Deltek GovWin IQ** ($7K–45K/year) remains the gold standard for pre-RFP intelligence if budget allows.

---

## 10. Security posture: compliant today, architected for CUI tomorrow

**DFARS 252.204-7012 and CMMC 2.0 do not currently apply** to a BD platform handling only publicly-sourced data. The DFARS definition of Covered Defense Information explicitly excludes "information that is lawfully publicly available without restrictions." SAM.gov data, public contract awards, job postings, and USASpending data all qualify as public.

CMMC Phase 1 is active (since November 10, 2025), with Phase 2 C3PAO third-party certification requirements beginning November 10, 2026. Even if not required now, **CMMC Level 1 (17 controls)** is low-effort and provides competitive advantage when selling to defense primes who increasingly require compliance from suppliers.

### Current security stack

**Supabase holds SOC 2 Type 2 certification** with annual audits — adequate for publicly-sourced BD data. RLS with tenant_id-based isolation, indexed policy columns, and security definer functions provides multi-tenant data separation. **Audit logging** combines Supabase's built-in auth audit logs, the `supa_audit` extension for data change tracking, and `pgAudit` for database-level operation logging, meeting NIST SP 800-171's 90-day retention requirement when paired with external SIEM.

**Neither Supabase nor Neo4j AuraDB are FedRAMP authorized.** If the platform ever handles CUI, all cloud services storing or processing CUI must meet FedRAMP Moderate baseline — requiring migration to self-hosted infrastructure on AWS GovCloud or equivalent. Anthropic Claude is not available in GovCloud; Azure OpenAI in GovCloud is the FedRAMP-authorized path for LLM access. **Design clean separation between public and controlled data from day one.**

For AI API data handling, Anthropic's Commercial Terms guarantee no training on API data, with 7-day default retention (Zero Data Retention available for Enterprise). Use `inference_geo: "us"` for US-only inference at 1.1x pricing. Never send CDI/CUI through commercial LLM APIs.

---

## Conclusion: what to build first

The architecture converges on a tight, managed-services stack that a 1–3 person team can operate. Three decisions have outsized impact and should be executed first:

1. **Migrate off FPDS immediately** — the February 24 decommission is days away. Integrate Tango by MakeGov as the unified data pipeline and SAM.gov Contract Awards API as the authoritative backup.

2. **Stand up the Supabase + pgvector foundation** — consolidate 50+ SQLite databases into a single PostgreSQL instance with the hybrid JSONB+typed columns pattern. Deploy pgvector with halfvec quantization. This single change eliminates Qdrant, simplifies the stack, and enables hybrid vector+relational queries.

3. **Begin the LangGraph migration** — start with the most critical CrewAI agent, implement PostgreSQL checkpointing via Supabase, and prove out the `interrupt()`-based human-in-the-loop pattern. The remaining 12 agents migrate incrementally.

The Voyage 4 re-embedding (~$40–60, 1–3 days) and Neo4j AuraDB migration (seconds for a 3K-node graph) are low-risk, high-reward steps that can proceed in parallel. The frontend migration to Next.js 16.1 is the longest pole — the 59 raw TSX files require incremental conversion to App Router pages with proper RBAC middleware.

The total monthly cost of **$500–$800** for the managed-services stack (Supabase $25 + Neo4j $65 + N8N $55 + Railway $40 + AI APIs $200–400 + data collection $100–200) falls well within the $500–$1,500 target while delivering capabilities that would have required a 10-person team and six-figure infrastructure budget two years ago.