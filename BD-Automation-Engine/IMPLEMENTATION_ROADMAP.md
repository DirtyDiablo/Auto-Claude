# IMPLEMENTATION ROADMAP

> Synthesized from Prompts 1–8 of PTS_NEXTGEN_CONSOLIDATION_BLUEPRINT.md
> Date: 2026-02-16
> Scope: BD-Automation-Engine consolidation into unified platform

---

## PRIORITY MATRIX

| Change | Revenue Impact | Risk Level | Effort | Dependencies | Score |
|--------|---------------|------------|--------|-------------|-------|
| Ruff formatting + pre-commit hooks | LOW | LOW | 2 hrs | None | Phase 0 |
| Dead code removal | LOW | LOW | 2 hrs | None | Phase 0 |
| pyproject.toml + CI/CD pipeline | LOW | LOW | 2 hrs | None | Phase 0 |
| Embedding model standardization (384→1536) | **CRITICAL** | MEDIUM | 1 day | Qdrant running | Phase 0 |
| Pin dependencies (requirements.txt → uv.lock) | MEDIUM | LOW | 2 hrs | pyproject.toml | Phase 0 |
| Extract libs/shared-core/ | MEDIUM | LOW | 3 days | Cleanup done | Phase 1 |
| Extract libs/db-layer/ (Repository Pattern) | HIGH | MEDIUM | 5 days | shared-core | Phase 1 |
| Extract libs/bullhorn-client/ | HIGH | LOW | 2 days | shared-core | Phase 1 |
| Extract libs/slack-utils/ | LOW | LOW | 1 day | shared-core | Phase 1 |
| Supabase schema + tables | HIGH | MEDIUM | 2 days | db-layer | Phase 2 |
| SQLite → Supabase migration scripts | **CRITICAL** | HIGH | 3 days | Supabase tables | Phase 2 |
| Qdrant → pgvector migration | HIGH | HIGH | 3 days | Embeddings fixed | Phase 2 |
| Neo4j → neomodel OGM | MEDIUM | MEDIUM | 2 days | db-layer | Phase 2 |
| Feature-flag dual-read switchover | **CRITICAL** | MEDIUM | 2 days | All migrations | Phase 2 |
| LangGraph master pipeline | **CRITICAL** | MEDIUM | 3 days | db-layer | Phase 3 |
| LangGraph morning briefing | **CRITICAL** | LOW | 1 day | master pipeline | Phase 3 |
| LangGraph contact enrichment | HIGH | MEDIUM | 2 days | master pipeline | Phase 3 |
| APScheduler unified scheduler | HIGH | MEDIUM | 1 day | LangGraph graphs | Phase 3 |
| N8N workflow decommission (18 flows) | MEDIUM | LOW | 1 day | LangGraph done | Phase 3 |
| Unified FastAPI server (16 routers) | HIGH | HIGH | 5 days | shared-core, db-layer | Phase 4 |
| Route deduplication (377 → 280) | MEDIUM | MEDIUM | 2 days | Unified server | Phase 4 |
| Auth upgrade (API key → JWT) | HIGH | HIGH | 3 days | Unified server | Phase 4 |
| Dashboard client migration | HIGH | MEDIUM | 2 days | New routes live | Phase 4 |
| Monorepo merge (git-filter-repo) | LOW | HIGH | 1 day | All phases done | Phase 5 |
| uv workspace setup | LOW | LOW | 2 hrs | Monorepo merge | Phase 5 |
| Unified Docker Compose | MEDIUM | LOW | 4 hrs | Monorepo merge | Phase 5 |
| Integration testing suite | HIGH | LOW | 3 days | All phases | Phase 5 |

### Revenue Impact Key
- **CRITICAL** = Directly enables daily call lists, briefings, or pipeline scoring
- **HIGH** = Improves data quality, reliability, or speed of revenue workflows
- **MEDIUM** = Developer productivity, maintainability, or operational efficiency
- **LOW** = Housekeeping, standards compliance, future-proofing

---

## PHASE 0: IMMEDIATE (This Week)

Zero-risk changes that improve the codebase without affecting functionality.

### ✅ Already Complete (Prompt 3 + 8)
- Dead code removal: 10 files deleted, 3,375 LOC removed, 294 MB freed
- Ruff formatting: 628 files reformatted
- 27 unused imports removed, 22 exception variables cleaned
- `pyproject.toml` created (ruff, pytest, mypy, coverage)
- `.pre-commit-config.yaml` created
- `.github/workflows/` created (ci.yml, security.yml, deploy.yml)
- Multi-stage `Dockerfile` with non-root user
- `.dockerignore` created
- Committed on branch `cleanup/dead-code-removal`

### Remaining Phase 0 Tasks

#### 0.1 Pin Dependencies
```bash
# Convert unpinned requirements.txt to locked versions
uv pip compile requirements.txt -o requirements.lock
# Add to pyproject.toml [project.dependencies]
```
**Files:** `requirements.txt`, `pyproject.toml`
**Risk:** None (additive, doesn't change installed versions)

#### 0.2 Fix Embedding Dimension Mismatch
The #1 technical debt item. 5 collections store 384-dim embeddings (local model) but the API queries with 1536-dim (OpenAI text-embedding-3-small). This silently degrades all search quality.

```bash
# 1. Update vector_collections.py to use 1536-dim consistently
# 2. Re-index all collections with OpenAI embeddings
python Engine8_Knowledge/scripts/vector_store.py --reindex --model text-embedding-3-small
```
**Files:**
- `Engine8_Knowledge/schemas/vector_collections.py` — change `size=384` → `size=1536`
- `Engine8_Knowledge/scripts/vector_store.py` — ensure OpenAI embeddings for all indexing
- `Engine8_Knowledge/scripts/indexer.py` — same

**Risk:** Medium (requires re-indexing ~8,447 records, ~$2 in OpenAI API costs)
**Validation:** Run search queries before/after, compare relevance scores

#### 0.3 Install Pre-commit Hooks
```bash
cd BD-Automation-Engine
pip install pre-commit
pre-commit install
pre-commit run --all-files  # Verify everything passes
```

#### 0.4 Deferred Cleanup Items
Review and resolve 52 remaining F841 unused variables (from CLEANUP_PLAN):
```bash
ruff check . --select F841 --output-format github
```
Review 41 ERA001 commented-out code blocks — most are section headers, not dead code. The pyproject.toml already ignores ERA001 globally.

---

## PHASE 1: FOUNDATION (Week 2–3)

Extract shared libraries and establish the Repository Pattern.

### 1.1 Extract `libs/shared-core/`
Common configuration, logging, FastAPI factory, and base models.

**Files to create:**
```
libs/shared-core/
├── pyproject.toml
└── src/shared_core/
    ├── __init__.py
    ├── config.py          ← from config/settings.py (Pydantic BaseSettings)
    ├── logging.py         ← from config/logging_config.py (structlog)
    ├── app_factory.py     ← create_app() with CORS, auth, error handlers
    ├── models.py          ← BaseDocument, PaginatedResponse[T], ErrorResponse
    ├── embeddings.py      ← get_embedding() with retry logic
    └── utils.py           ← path helpers, openai_retry decorator
```

**Files to modify (update imports):** ~40 files that import from `config/`
```bash
# Find all files importing from config
ruff check . --select I --fix  # After moving files
```

**Risk:** Low — config is well-isolated, imports are straightforward
**Validation:** All 44 tests pass, API starts successfully

### 1.2 Extract `libs/db-layer/`
Repository Pattern with abstract interfaces and concrete implementations.

**Files to create:**
```
libs/db-layer/
├── pyproject.toml
└── src/db_layer/
    ├── __init__.py
    ├── interfaces.py      ← EntityRepository[T, TCreate, TUpdate] ABC
    ├── qdrant/
    │   ├── __init__.py
    │   ├── client.py      ← get_qdrant_client() singleton
    │   ├── contacts.py    ← QdrantContactRepo
    │   ├── programs.py    ← QdrantProgramRepo
    │   └── documents.py   ← QdrantDocumentRepo
    ├── sqlite/
    │   ├── __init__.py
    │   ├── connection.py  ← get_sqlite_connection(db_name) pool
    │   └── contacts.py    ← SqliteContactRepo
    └── neo4j/
        ├── __init__.py
        ├── driver.py      ← get_neo4j_driver() singleton
        └── contacts.py    ← Neo4jContactRepo (neomodel StructuredNode)
```

**Problem being solved:** 54+ files create their own `QdrantClient`, 40+ create SQLite connections. No connection pooling, no testability.

**Files to modify:** ~94 files with direct database access
```bash
# Find all Qdrant connection points
grep -r "QdrantClient\|qdrant_client" --include="*.py" -l
# Find all SQLite connection points
grep -r "sqlite3.connect\|get_db\|bullhorn.db" --include="*.py" -l
```

**Risk:** Medium — touching 94 files, but each change is mechanical (swap direct client for injected repo)
**Validation:** All tests pass, API responses identical, no connection leaks

### 1.3 Extract `libs/bullhorn-client/`
Unified Bullhorn CRM integration from scattered modules.

**Files to create:**
```
libs/bullhorn-client/
├── pyproject.toml
└── src/bullhorn_client/
    ├── __init__.py
    ├── auth.py            ← OAuth token management
    ├── client.py          ← BullhornClient (CRUD + search)
    ├── etl.py             ← 7-step ETL pipeline
    ├── models.py          ← Pydantic models for Bullhorn entities
    └── exporters.py       ← Notion CSV, n8n JSON exporters
```

**Files to consolidate from:**
- `services/bullhorn_integration.py` (OAuth + API client)
- `Engine7_BullhornETL/scripts/` (ETL pipeline, 22 files)
- `Engine7_BullhornETL/data/bullhorn.db` (stays in place, accessed via db-layer)

**Risk:** Low — Bullhorn code is self-contained
**Validation:** ETL pipeline produces identical output

### 1.4 Extract `libs/slack-utils/`
Shared Slack integration from Engine8.

**Files to create:**
```
libs/slack-utils/
├── pyproject.toml
└── src/slack_utils/
    ├── __init__.py
    ├── bot.py             ← SlackBDBot with Block Kit
    ├── router.py          ← FastAPI router for slash commands
    └── fallback.py        ← JSONL fallback when no Slack token
```

**Files to consolidate from:**
- `Engine8_Knowledge/integrations/slack_integration.py` (470 lines)

**Risk:** Low — single source file, well-isolated
**Validation:** Slack messages still deliver (or JSONL fallback works)

---

## PHASE 2: DATABASE (Week 3–4)

Migrate from SQLite/Qdrant/Neo4j to Supabase PostgreSQL + pgvector.

### 2.1 Create Supabase Schema
```sql
-- All tables under bd.* schema
CREATE SCHEMA IF NOT EXISTS bd;

-- Core tables
CREATE TABLE bd.contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bullhorn_id INTEGER UNIQUE,
    first_name TEXT, last_name TEXT, email TEXT,
    company TEXT, title TEXT, tier INTEGER,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE bd.programs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL, acronym TEXT,
    agency TEXT, branch TEXT,
    value_millions NUMERIC,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE bd.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT, company TEXT, location TEXT,
    program_match TEXT, bd_score NUMERIC,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Plus: activities, documents, contracts, interactions, companies, locations
-- See DATABASE_MIGRATION_PLAN.md for full schema (1,827 lines)
```

**Files to create:**
- `migrations/001_create_schema.sql`
- `migrations/002_create_tables.sql`
- `migrations/003_create_indexes.sql`
- `migrations/004_rls_policies.sql`

**Risk:** Medium — schema design decisions are hard to reverse
**Validation:** Schema matches all existing data shapes

### 2.2 SQLite → Supabase Migration Scripts
```
scripts/migrate/
├── migrate_contacts.py     ← 7,337 contacts from bullhorn.db
├── migrate_programs.py     ← 401 programs from Federal_Programs CSV
├── migrate_activities.py   ← 500 activities from bullhorn.db
├── migrate_documents.py    ← 205 documents from bd_graph.db
├── migrate_jobs.py         ← Job postings
├── verify_migration.py     ← Row counts, spot checks, embedding queries
└── rollback.py             ← Truncate and restore from SQLite
```

**Risk:** High — data loss potential, must verify row counts and data integrity
**Validation:** `verify_migration.py` checks every table's row count, samples 10 random records, compares field values

### 2.3 Qdrant → pgvector Migration
Move 8 collections (8,447 records) from Qdrant to PostgreSQL pgvector.

```bash
# For each collection: scroll all vectors, insert into Supabase with embedding column
python scripts/migrate/migrate_vectors.py --collection contacts --batch-size 100
```

**Index strategy:**
```sql
CREATE INDEX ON bd.contacts USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

**Risk:** High — search quality regression if HNSW params wrong
**Validation:** Run top-10 queries from API logs, compare result sets and scores against Qdrant

### 2.4 Feature-Flag Switchover
```python
# In libs/db-layer/ interfaces
BACKEND = os.getenv("DB_BACKEND", "qdrant")  # "qdrant" | "supabase"

def get_contact_repo() -> ContactRepository:
    if BACKEND == "supabase":
        return SupabaseContactRepo()
    return QdrantContactRepo()
```

**Risk:** Medium — dual-read phase doubles latency temporarily
**Validation:** A/B compare responses from both backends for 1 week

---

## PHASE 3: ORCHESTRATION (Week 4–5)

Replace N8N + task_scheduler + ad-hoc scripts with LangGraph StateGraphs.

### 3.1 LangGraph Master Pipeline
The core daily workflow that drives revenue.

```python
# workflows/master_pipeline.py
class MasterPipelineState(TypedDict):
    jobs_raw: list[dict]
    jobs_standardized: list[dict]
    program_matches: list[dict]
    contacts_enriched: list[dict]
    scores: list[dict]
    briefings: list[dict]
    status: str

graph = StateGraph(MasterPipelineState)
graph.add_node("scrape", scrape_jobs)
graph.add_node("standardize", standardize_jobs)
graph.add_node("match_programs", match_programs)
graph.add_node("enrich_contacts", enrich_contacts)
graph.add_node("score", score_opportunities)
graph.add_node("generate_briefings", generate_briefings)
graph.add_node("export", export_results)
# Linear flow with error routing to retry/alert nodes
```

**Risk:** Medium — must produce identical call lists to current pipeline
**Validation:** Run both old and new pipeline on same input, diff outputs

### 3.2 Additional LangGraph Graphs
| Graph | Nodes | Trigger | Priority |
|-------|-------|---------|----------|
| `morning_briefing` | fetch_metrics → generate_brief → send_slack | Cron 6 AM | CRITICAL |
| `contact_enrichment` | lookup → classify → enrich → save | On-demand | HIGH |
| `weekly_intel` | aggregate → analyze → format → distribute | Cron Monday | HIGH |
| `bd_proposal` | research → draft → review → finalize | Manual | MEDIUM |
| `contact_outreach` | select → personalize → send → track | Manual | MEDIUM |
| `data_quality` | scan → validate → flag → report | Cron daily | MEDIUM |

**Files to create:**
```
workflows/
├── __init__.py
├── master_pipeline.py      ← 7-node daily pipeline
├── morning_briefing.py     ← 4-node daily brief
├── contact_enrichment.py   ← 4-node with human gate
├── weekly_intel.py         ← 4-node weekly report
├── bd_proposal.py          ← 4-node with human gate
├── contact_outreach.py     ← 4-node with human gate
├── data_quality.py         ← 4-node daily scan
├── scheduler.py            ← APScheduler unified scheduler
├── registry.py             ← Workflow metadata and config
└── states.py               ← All TypedDict state definitions
```

### 3.3 Unified Scheduler
```python
# workflows/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

SCHEDULE = {
    "master_pipeline":    CronTrigger(hour=5, minute=0),   # 5 AM daily
    "morning_briefing":   CronTrigger(hour=6, minute=0),   # 6 AM daily
    "data_quality":       CronTrigger(hour=2, minute=0),   # 2 AM daily
    "weekly_intel":       CronTrigger(day_of_week="mon", hour=7),
    "contact_enrichment": None,  # On-demand only
}
```

### 3.4 N8N Decommission
After LangGraph graphs are verified, remove:
- `n8n/` directory (18 workflow JSON files)
- N8N environment variables from `.env.example`
- N8N bridge code from `dify_integration/`
- N8N references from documentation

**Risk:** Low (N8N workflows are already non-functional without N8N server)
**Validation:** All scheduled tasks execute via APScheduler

---

## PHASE 4: API UNIFICATION (Week 5–6)

Consolidate ~377 endpoints into 16 domain routers under `/api/v1/*`.

### 4.1 Create Unified FastAPI Server
```
api/
├── __init__.py
├── main.py                ← create_app() factory
├── middleware/
│   ├── auth.py            ← JWT Bearer auth
│   ├── cors.py            ← CORS configuration
│   ├── logging.py         ← Request/response logging
│   └── rate_limit.py      ← Per-endpoint rate limiting
├── routers/
│   ├── contacts.py        ← /api/v1/contacts/* (15 routes)
│   ├── programs.py        ← /api/v1/programs/* (12 routes)
│   ├── jobs.py            ← /api/v1/jobs/* (6 routes)
│   ├── contracts.py       ← /api/v1/contracts/* (6 routes)
│   ├── scraping.py        ← /api/v1/scraping/* (10 routes)
│   ├── enrichment.py      ← /api/v1/enrichment/* (13 routes)
│   ├── outreach.py        ← /api/v1/outreach/* (9 routes)
│   ├── reports.py         ← /api/v1/reports/* (11 routes)
│   ├── workflows.py       ← /api/v1/workflows/* (19 routes)
│   ├── health.py          ← /api/v1/health/* (15 routes)
│   ├── admin.py           ← /api/v1/admin/* (18 routes)
│   ├── webhooks.py        ← /api/v1/webhooks/* (6 routes)
│   ├── search.py          ← /api/v1/search/* (14 routes)
│   ├── graph.py           ← /api/v1/graph/* (20 routes)
│   ├── ai.py              ← /api/v1/ai/* (8 routes)
│   └── ml.py              ← /api/v1/ml/* (remaining routes)
└── schemas/
    ├── contacts.py        ← Contact, ContactCreate, ContactUpdate
    ├── programs.py        ← FederalProgram, ProgramCreate
    ├── jobs.py            ← Job, JobCreate
    ├── search.py          ← SearchRequest, SearchResult
    └── common.py          ← PaginatedResponse[T], ErrorResponse
```

### 4.2 Deprecation Schedule
| Week | Old Routes | New Routes | Behavior |
|------|-----------|------------|----------|
| 1–4 | Active | Active | Both serve, old returns `Deprecation` header |
| 5–6 | 301 redirect | Active | Old redirects to new |
| 7+ | Removed | Active | Old returns 410 Gone |

### 4.3 Dashboard Client Migration
**Files to update:**
- `dashboard/src/lib/hubApi.ts` — base URL + all fetch paths
- `dashboard/src/hooks/useAppData.ts` — TanStack Query keys + endpoints
- `dashboard/src/hooks/useHubApi.ts` — manual fetch hooks
- `dashboard/vite.config.ts` — proxy paths

### 4.4 MCP Server Migration
**Files to update:**
- `mcp/knowledge-mcp-server/src/index.ts` — all API call paths

**Risk:** High — breaking changes for dashboard and MCP clients
**Validation:** Dashboard loads, all pages render data, MCP tools return results

---

## PHASE 5: MONOREPO MERGE (Week 6–7)

Final unification of BD-Automation-Engine + N8N-Builder + Data-Scraper.

### 5.1 Git History Preservation
```bash
# In each repo, rewrite history to move files into services/ subfolder
cd BD-Automation-Engine
git filter-repo --to-subdirectory-filter services/bd-automation

cd N8N-Builder
git filter-repo --to-subdirectory-filter services/n8n-builder

cd Data-Scraper
git filter-repo --to-subdirectory-filter services/data-scraper

# Create unified repo and merge
mkdir unified-platform && cd unified-platform && git init
git remote add bd-engine ../BD-Automation-Engine
git remote add n8n-builder ../N8N-Builder
git remote add data-scraper ../Data-Scraper

git fetch bd-engine && git merge bd-engine/main --allow-unrelated-histories
git fetch n8n-builder && git merge n8n-builder/main --allow-unrelated-histories
git fetch data-scraper && git merge data-scraper/main --allow-unrelated-histories
```

### 5.2 uv Workspace Setup
```toml
# unified-platform/pyproject.toml
[project]
name = "pts-unified-platform"
version = "1.0.0"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["services/*", "libs/*"]

[tool.uv.sources]
shared-core = { workspace = true }
db-layer = { workspace = true }
bullhorn-client = { workspace = true }
slack-utils = { workspace = true }
```

### 5.3 Unified Docker Compose
```yaml
# docker-compose.yml
services:
  bd-api:
    build: services/bd-automation
    ports: ["8100:8100"]
    depends_on: [postgres, qdrant]

  postgres:
    image: supabase/postgres:15
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  qdrant:
    image: qdrant/qdrant:v1.16.3
    ports: ["6333:6333"]
    volumes: ["qdrant_data:/qdrant/storage"]

  neo4j:
    image: neo4j:5
    ports: ["7474:7474", "7687:7687"]
    volumes: ["neo4j_data:/data"]

volumes:
  pgdata:
  qdrant_data:
  neo4j_data:
```

### 5.4 Integration Testing
```bash
# Full integration test suite
pytest tests/integration/ -v -m integration
# Smoke tests against running Docker stack
pytest tests/smoke/ -v --base-url http://localhost:8100
```

**Risk:** High — git history merge can create conflicts
**Validation:** `git log --all --oneline | wc -l` preserves commit count from all 3 repos

---

## BLOCKERS AND RISKS

### Phase 0 Blockers
| Risk | Impact | Mitigation |
|------|--------|------------|
| Embedding reindex fails mid-way | Search broken | Reindex into new collection, swap atomically |
| OpenAI API rate limits during reindex | Delayed | Use batch API with exponential backoff |

### Phase 1 Blockers
| Risk | Impact | Mitigation |
|------|--------|------------|
| Import path changes break 150+ files | Build fails | Run ruff fix + test suite after each extraction |
| Circular dependencies in shared-core | Import errors | Strict layering: shared-core → db-layer → engines |

### Phase 2 Blockers
| Risk | Impact | Mitigation |
|------|--------|------------|
| Supabase connection from local dev | Can't test | Use Supabase local (Docker) or connection pooler |
| Data loss during migration | Unrecoverable | Keep SQLite as read-only backup for 30 days |
| pgvector search quality lower than Qdrant | Revenue impact | Tune HNSW params, compare top-10 results before cutover |
| Embedding dimension mismatch not fixed | Migration blocked | **Must complete Phase 0.2 first** |

### Phase 3 Blockers
| Risk | Impact | Mitigation |
|------|--------|------------|
| LangGraph output differs from current pipeline | Wrong call lists | Run both pipelines in parallel, diff outputs for 1 week |
| APScheduler timezone issues | Missed runs | Use UTC everywhere, convert at display time |
| CrewAI agents fail inside LangGraph nodes | Workflow broken | Keep CrewAI as subprocess, not inline |

### Phase 4 Blockers
| Risk | Impact | Mitigation |
|------|--------|------------|
| Dashboard breaks during route migration | Users blocked | Feature-flag new routes, keep old routes active during transition |
| JWT auth implementation delays | Can't deploy | Use API key auth as fallback, add JWT later |
| MCP tools break with new paths | Claude Code loses access | Update MCP server first, test before deploying API changes |

### Phase 5 Blockers
| Risk | Impact | Mitigation |
|------|--------|------------|
| git-filter-repo mangles history | Lost commits | Dry-run on copies first, verify commit counts |
| Merge conflicts between 3 repos | Blocked merge | Resolve one repo at a time, verify after each merge |
| uv workspace resolution failures | Can't install | Pin all versions, test workspace resolution before merge |

### Critical Path
```
Phase 0 (Embedding fix)
  ↓
Phase 1 (shared-core → db-layer)
  ↓
Phase 2 (Database migration)  ←── HIGHEST RISK
  ↓
Phase 3 (LangGraph)  ←── HIGHEST REVENUE IMPACT
  ↓
Phase 4 (API unification)
  ↓
Phase 5 (Monorepo merge)
```

**The #1 blocker across all phases:** Embedding dimension mismatch (Phase 0.2). Every downstream migration depends on consistent 1536-dim embeddings.

---

## SUCCESS METRICS

### Phase 0
- [ ] `ruff check .` returns 0 errors
- [ ] `pre-commit run --all-files` passes
- [ ] CI pipeline runs on push (GitHub Actions green)
- [ ] All 8 Qdrant collections use 1536-dim embeddings
- [ ] Search query "DCGS analyst" returns relevant contacts (score > 0.7)
- [ ] `requirements.txt` has pinned versions

### Phase 1
- [ ] `libs/shared-core/` importable: `from shared_core.config import Settings`
- [ ] `libs/db-layer/` importable: `from db_layer.qdrant import QdrantContactRepo`
- [ ] `libs/bullhorn-client/` importable: `from bullhorn_client import BullhornClient`
- [ ] All 44+ tests pass after extraction
- [ ] No direct `QdrantClient()` or `sqlite3.connect()` calls outside db-layer
- [ ] API starts and serves requests using injected repos

### Phase 2
- [ ] Supabase tables created with RLS policies
- [ ] Row counts match: SQLite contacts (7,337) = Supabase contacts
- [ ] pgvector search returns same top-10 as Qdrant for 5 benchmark queries
- [ ] Feature flag `DB_BACKEND=supabase` switches all reads to PostgreSQL
- [ ] SQLite files retained as read-only backup for 30 days
- [ ] Zero data loss verified by `verify_migration.py`

### Phase 3
- [ ] `master_pipeline` LangGraph produces identical call list to current `orchestrator.py`
- [ ] `morning_briefing` delivers Slack message at 6 AM
- [ ] APScheduler runs all 4 cron workflows without manual intervention for 7 days
- [ ] N8N directory removed, no N8N references in codebase
- [ ] Workflow execution logs stored in Supabase `bd.workflow_runs`

### Phase 4
- [ ] Single FastAPI server on port 8100 with 16 routers
- [ ] `/api/v1/contacts?limit=10` returns paginated contacts
- [ ] Old routes return `Deprecation` header during dual-serve period
- [ ] Dashboard loads and displays data from new endpoints
- [ ] MCP tools (`search_knowledge`, `ask_knowledge`) work with new paths
- [ ] OpenAPI spec generated at `/docs`
- [ ] Response format: `{"data": [...], "total": N, "page": 1}`

### Phase 5
- [ ] `unified-platform/` contains all 3 repos' history
- [ ] `git log --all --oneline | wc -l` ≥ sum of all 3 repos' commits
- [ ] `uv sync` installs all workspace packages
- [ ] `docker compose up` starts full stack (API + Postgres + Qdrant + Neo4j)
- [ ] `pytest tests/` runs all tests from all 3 repos
- [ ] Daily call list output identical to pre-merge output

### Ultimate Success Criterion
**The daily call list pipeline runs end-to-end autonomously, producing prioritized call lists and briefings for the BD team, with zero manual intervention.**

---

*Generated 2026-02-16 from synthesis of AUDIT_REPORT.md, CLEANUP_PLAN.md, SHARED_LIBRARY_PLAN.md, API_CONSOLIDATION_PLAN.md, DATABASE_MIGRATION_PLAN.md, LANGGRAPH_MIGRATION_PLAN.md, and CICD_QUALITY_PLAN.md.*
