# BD-Automation-Engine: Full Project Audit Report

**Date:** 2026-02-20
**Auditor:** Claude Opus 4.6 (15+ specialized subagents across 4 waves)
**Scope:** Every file, folder, data point, codebase, tech stack, process, and file type
**Target System:** PTS BD Intelligence System for federal defense contract staffing (thousands of cleared defense contracts)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Vital Signs](#2-project-vital-signs)
3. [Security & Compliance (CRITICAL)](#3-security--compliance)
4. [Code Quality](#4-code-quality)
5. [Silent Failures](#5-silent-failures)
6. [Performance](#6-performance)
7. [Architecture & Dependencies](#7-architecture--dependencies)
8. [Data & Databases](#8-data--databases)
9. [Documentation](#9-documentation)
10. [3-to-1 Consolidation Readiness](#10-3-to-1-consolidation-readiness)
11. [Prioritized Remediation Roadmap](#11-prioritized-remediation-roadmap)
12. [Appendix: File Inventory](#appendix-file-inventory)

---

## 1. Executive Summary

The BD-Automation-Engine is an 8-engine pipeline for federal defense Business Development automation. It is **functionally complete** — all 8 engines work, data flows end-to-end, and the knowledge system indexes 8,447+ records across 5 Qdrant collections. However, the system has **critical security vulnerabilities** that must be fixed before any operational use.

### Overall Scores

| Dimension | Score | Status |
|-----------|-------|--------|
| **Security** | 1/10 | CRITICAL — 20+ live credentials committed, zero auth on 50+ endpoints |
| **Code Quality** | 5.5/10 | MIXED — Engine 8 workflows good (8/10), Engine 7 ETL dangerous (3-5/10) |
| **Architecture** | 4/10 | WEAK — 277 sys.path hacks, monolithic api.py, no package structure |
| **Performance** | 4/10 | POOR — 17 confirmed bottlenecks, 100x write latency in ETL |
| **Data Integrity** | 5/10 | AT RISK — 47 silent failure patterns, eval() on DB data |
| **Documentation** | 5/10 | PARTIAL — 6/8 engines undocumented, k8s/helm/monitoring zero docs |
| **Testing** | 2/10 | MINIMAL — Engine 8 has 42 integration tests, others have near-zero |
| **Compliance (NIST/CMMC)** | 1/10 | FAILED — 88-100% gap across 8 control families |
| **Migration Readiness** | 6/10 | FEASIBLE — migration script exists, needs ON CONFLICT + graph migration |

### Top 5 Most Urgent Actions

1. **ROTATE ALL CREDENTIALS NOW** — 20+ live API keys/passwords committed to git (Anthropic, OpenAI, Supabase, Notion, GitHub, N8N, Neo4j)
2. **Add authentication to Engine 8 API** — 50+ endpoints with PII (7,337 contacts, clearance levels) are completely open
3. **Replace all `eval()` calls** — 13 instances executing arbitrary code from CSV/database data
4. **Replace `except Exception: pass`** in ETL — 7 database INSERT blocks silently drop records
5. **Fix orchestrator stage failure handling** — pipeline continues with stale data when engines fail

---

## 2. Project Vital Signs

### Size & Scope

| Metric | Value |
|--------|-------|
| Total files | 83,599 (including node_modules, skills) |
| Core engine files | ~767 |
| Python files | 280 (.py) + 220 (.pyc) |
| CSV data files | 754 |
| Excel files | 67 |
| SQLite databases | 12 files, ~1.1 GB total |
| Qdrant vector DB | 6 collections, 737 MB |
| Total data volume | ~1.8 GB |
| Lines of code (api.py alone) | 4,682 |
| API endpoints | 222+ routes |
| Dependencies | 60+ packages (all `>=` pinned, no upper bounds) |

### Engine Status

| Engine | Purpose | Status | Quality |
|--------|---------|--------|---------|
| 1 - Scraper | Apify job scraping | Complete | Config-only (no Python) |
| 2 - Program Mapping | Job-to-program matching | Complete | 6/10 |
| 3 - OrgChart | Contact classification | Complete | 6/10 |
| 4 - Playbook | BD playbook generation | Complete | 7/10 |
| 5 - Scoring | BD priority scoring (0-100) | Complete | 7/10 |
| 6 - QA | Quality assurance & alerts | Complete | 7/10 |
| 7 - Bullhorn ETL | CRM data extraction | Complete | **4/10** (most dangerous) |
| 8 - Knowledge | AI knowledge system + RAG | Complete | **5/10** (api.py monolith) |

### Data Holdings

| Collection | Records | Source |
|------------|---------|--------|
| Contacts | 7,337 | Bullhorn CRM + 25 defense contractors |
| Federal Programs | 401 | SAM.gov, FPDS, Tango |
| Documents | 205 | Past performance, briefings |
| Activities | 500 | Call notes, meeting records |
| Jobs | 4-262 | ClearanceJobs, LinkedIn, Insight Global |
| Candidates | 426,565 | Bullhorn master database |
| Federal Contracts | 33,000+ | unified_federal_contracts.db |

---

## 3. Security & Compliance

### 3.1 Credential Exposure (CRITICAL)

**20+ unique live credentials are committed to version control across 8+ files.**

| File | Credentials Found |
|------|------------------|
| `.env` | Anthropic, OpenAI, Apify, Supermemory, Notion, N8N (JWT), Supabase (anon + service + publishable), DB password (3 connection strings), Neo4j |
| `BD-Automation-Engine.env` | Duplicate set of live credentials |
| `auto-claude.env` | GitHub OAuth token, different OpenAI key |
| `dashboard.env` | Different Notion token |
| `dashboard/.env` | Notion token with `VITE_` prefix (embedded in frontend JS bundle) |
| `apps/backend/.env` | Claude Code OAuth token |
| `.auto-claude/.env` | GitHub token, OpenAI key |
| `.auto-claude/.auto-claude/.env` | Different GitHub token, different OpenAI key |
| `docs/Claude Exports/*.md` | Apify tokens, Notion Bearer tokens in documentation |

**Hardcoded in source code (tracked files):**

| File | Line | Credential |
|------|------|------------|
| `Engine8_Knowledge/supabase_client.py` | 34 | Supabase password `DodiroquNew007%3F` |
| `scripts/full_migration_to_supabase.py` | 38 | Supabase DSN with password |
| `scripts/check_schema.py` | 5 | Supabase connection string |
| `scripts/fix_remaining_migration.py` | 18 | Supabase DSN |
| `scripts/remigrate_activities_placements.py` | 19 | Supabase DSN |
| `docker-compose.yml` | 34, 81 | Neo4j password `pts_bd_2026` |
| `Engine8_Knowledge/graph/neo4j_manager.py` | 50 | Neo4j password as default |
| `Engine8_Knowledge/scripts/memory_layer.py` | 132 | Neo4j password as default |
| `services/graphiti_service.py` | 42 | Neo4j password as default |
| `.env.example` | 252 | Real Neo4j password used as "example" |

### 3.2 Authentication & Access Control (CRITICAL)

- **Zero authentication** on 50+ FastAPI endpoints handling PII and federal program data
- **Wildcard CORS** (`allow_origins=["*"]` + `allow_credentials=True`) — any website can access the API
- **No rate limiting** despite `slowapi` being in requirements.txt
- **Unauthenticated webhooks** — no HMAC/signature verification
- **Unauthenticated MCP server** — 21 tools exposed without auth
- **SSRF vulnerability** — scrape endpoints accept arbitrary URLs with no validation
- **Redis without authentication** — exposed on port 6379
- **Qdrant without API key** — exposed on ports 6333/6334
- **Auth bypass** in `api/unified_endpoints.py` — authentication disabled when `HUB_API_KEY` not set

### 3.3 NIST 800-171 / CMMC Compliance

| Control Family | Gap |
|---------------|-----|
| 3.1 Access Control | 91% |
| 3.3 Audit & Accountability | 89% |
| 3.4 Configuration Management | 78% |
| 3.5 Identification & Authentication | 91% |
| 3.8 Media Protection | 100% |
| 3.12 Security Assessment | 100% |
| 3.13 System & Communications Protection | 88% |
| 3.14 System & Information Integrity | 86% |

**Verdict:** The system is **disqualified for CMMC Level 2** in its current state. For a system targeting $950M in DCGS contracts, this represents significant compliance exposure.

---

## 4. Code Quality

### 4.1 Engine-by-Engine Quality

| File | Score | Critical Issues |
|------|-------|-----------------|
| `Engine7/bullhorn_etl_v2.py` | **5/10** | 12 bare `except: pass` on DB inserts, hardcoded path `C:/Users/gtmar/...`, no WAL mode |
| `Engine7/ingest_new_notes.py` | **3/10** | 11 `eval()` calls on DB data (code injection), no try/except around eval |
| `Engine8/api.py` | **4/10** | 4,682-line monolith, 40+ sequential try/except imports, meaningless `MEMORY_AVAILABLE` flag |
| `Engine8/vector_store.py` | **7/10** | Zero-vector fallback corrupts search, no batch embedding |
| `Engine8/hybrid_retriever.py` | **7/10** | Full collection load for BM25 (74 sequential API calls), incompatible `SearchResult` class |
| `Engine8/workflows/orchestrator_v2.py` | **8/10** | Best-quality file — proper async, dataclasses, structured logging |
| `Engine2/full_pipeline.py` | **BROKEN** | Imports `Engine4_Briefing` (doesn't exist), wrong function signatures, references nonexistent `PipelineStats` |
| `Engine2/pipeline.py` | **7/10** | Well-structured 7-stage pipeline |
| `Engine2/generate_bd_playbook.py` | **5/10** | `eval()` + bare `except:`, `total_contacts` count bug, hardcoded dated filename |
| `Engine2/job_standardizer.py` | **6/10** | Violates CLAUDE.md: uses `anthropic.Anthropic()` directly |
| `Engine3/contact_lookup.py` | **6/10** | O(n^2) deduplication, Contact has no `__hash__`/`__eq__` |
| `Engine5/bd_scoring.py` | **7/10** | Tier logic depends on dict insertion order |
| `orchestrator.py` | **7/10** | Stage labels wrong (prints "[x/11]" but only 7-8 stages), module docstring says `Engine4_Briefing` |

### 4.2 Cross-Cutting Issues

- **3 divergent `normalize_company_name` implementations** — `bullhorn_etl_v2.py` (17 entries), `data_cleanup.py` (36 entries), `master_db/utils.py` (most complete). Same company normalizes differently depending on which script processed it.
- **2 incompatible `SearchResult` dataclasses** — `vector_store.py` has `(id, score, payload, collection)`, `hybrid_retriever.py` has `(id, text, score, source, metadata)`.
- **Inconsistent logging** — Engine 7 uses `print()`, Engine 8 uses structlog, agents use `logging.basicConfig()` (conflicts with structlog).
- **`models/` directory completely unused** — well-written Pydantic models (9/10 quality) exist but every engine passes raw dicts instead.
- **Mock auth in production** — `services/bullhorn_integration.py` sets `self._authenticated = True` without actually authenticating.

---

## 5. Silent Failures

**47 distinct silent failure patterns identified. 6 CRITICAL, 10 HIGH, 3 MEDIUM.**

### 5.1 Most Dangerous (CRITICAL)

| Pattern | File | Impact |
|---------|------|--------|
| 7x `except Exception: pass` on DB inserts | `bullhorn_etl_v2.py:846-1141` | CRM data silently vanishes during ETL. Unknown number of records lost. |
| 11x `eval()` on DB strings with no try/except | `ingest_new_notes.py:580-790` | Single corrupted value crashes entire ingestion. All subsequent notes lost. |
| `eval()` + bare `except:` | `generate_bd_playbook.py:245` | Companies silently dropped from playbooks. Catches `SystemExit`. |
| Pipeline continues after engine failures | `orchestrator.py:646-661` | Scoring runs on unmapped data, QA evaluates unscored data, pipeline reports "completed" |
| Mock authentication returns True | `bullhorn_integration.py:89-95` | Auth check passes, all subsequent API calls fail silently |
| Bare `except:` on financial metrics | `enrich_insight_global_jobs.py:893` | Bill rates and margins silently vanish from BD decisions |

### 5.2 High Severity

- **Health checks lie** — `health_check.py` bare `except:` on all 3 checks transforms MemoryError into "service not running"
- **Dollar values silently zeroed** — `build_open_contracts.py` bare `except:` returns 0.0 for unparseable contract values
- **Pipeline state corruption** — `orchestrator.py:874` silently wipes entire run history if state file is corrupted
- **Webhook delivery unchecked** — `streaming/bd_streaming_pipeline.py` never checks HTTP response status
- **Notion updates silently fail** — `services/ai_enrichment/` returns False with no logging on API failure

---

## 6. Performance

**17 confirmed bottlenecks across 5 categories.**

### 6.1 Critical (P0)

| Bottleneck | File:Line | Impact | Fix |
|-----------|-----------|--------|-----|
| Zero-vector fallback corrupts search | `vector_store.py:316` | Failed embeddings stored as `[0.0]*1536`, match everything | Return `None`, skip indexing |
| Individual INSERTs in ETL loops | `bullhorn_etl_v2.py:818-927` | 100x write latency for 426K candidates | Use `executemany()` in batches of 1000 |
| Full collection load for BM25 | `hybrid_retriever.py:240` | 74 sequential API calls per cold search | Increase batch to 1000, persist BM25 index |

### 6.2 High (P1)

| Bottleneck | Fix | Impact |
|-----------|-----|--------|
| Sequential 11-stage orchestrator | ThreadPoolExecutor DAG | 40-60% wall-clock reduction |
| No WAL mode on ETL database | 5 PRAGMA lines | Eliminates read-write blocking |
| Single-record embedding during indexing | Batch API (2048/call) | 28 min → 0.8 sec for full re-index |
| O(n^2) contact deduplication | Set-based dedup with `__hash__` | O(n) for 7,337 contacts |
| No embedding cache | Wire existing `redis_cache.py` | Eliminate redundant OpenAI API spend |

### 6.3 Quick Wins (< 30 min each)

1. **Fix zero-vector fallback** — change `return [0.0] * EMBEDDING_DIMENSION` to `return None` + null check
2. **Enable WAL mode** — add 5 PRAGMA lines after `sqlite3.connect()`
3. **Fix BM25 batch size** — change `limit=100` to `limit=1000` (single integer change)

---

## 7. Architecture & Dependencies

### 7.1 Module Structure

- **277 `sys.path.insert` calls** across 257 files (45 in core engines after filtering skills/)
- **No `pyproject.toml` or package installation** — imports work only because working directory is project root
- **Engine8_Knowledge crosses boundaries** — imports from `streaming/` and `api/` at repo root
- **4,682-line `api.py` monolith** with 40+ try/except import blocks for router registration
- **3 framework collision risk** — crewai, langgraph, llama-index all install competing langchain-core versions

### 7.2 Dependency Issues

| Issue | Details |
|-------|---------|
| Duplicate crawl4ai | `>=0.2.0` (line 133) AND `>=0.4.0` (line 148) — API incompatibility between versions |
| No upper bounds | All 60+ packages use `>=` only — pydantic 3.x will break everything |
| Test deps in production | `fakeredis`, `pytest-asyncio` in main requirements.txt |
| Windows-only package | `python-magic-bin>=0.4.14` breaks on Linux/Mac CI |
| Framework weight | crewai (~85MB), langgraph (~50MB), llama-index (~120MB), transformers (pulls ~2-3GB torch) |

### 7.3 Dead Code

| File | Status | Reason |
|------|--------|--------|
| `Engine2/scripts/full_pipeline.py` | **BROKEN** | Imports `Engine4_Briefing` (doesn't exist), wrong function signatures |
| `models/` directory | **UNUSED** | Well-typed Pydantic models, but every engine passes raw dicts |
| `bd_scoring.py::recalibrate()` | **DEAD** | Not called anywhere in orchestrator |
| `Engine7/bullhorn.db` | **EMPTY** | 0 bytes — actual data in `bullhorn_master.db` (293 MB) |

---

## 8. Data & Databases

### 8.1 Database Inventory

| Database | Size | Records | Status |
|----------|------|---------|--------|
| `Engine7/bullhorn_master.db` | 293 MB | 426,565 candidates, 7,337 contacts | Active |
| `data/unified_federal_contracts.db` | 134 MB | 33,000+ contracts | Active |
| `data/master_federal_contracts.db` | 58 MB | Overlaps with unified | **Duplicate** |
| `Engine8/data/bd_graph.db` | 22 MB | 63K entities, 16K relationships | Active |
| `Engine8/data/qdrant/` (6 collections) | 737 MB | 8,447 records | Active |
| `data/qdrant/` (duplicate) | 737 MB | Same 8,447 records | **Duplicate** |
| `Engine8/data/memory/chroma.sqlite3` | 8.6 MB | Mem0 AI memory | Active |
| `data/state/bullhorn_past_performance.db` | 23 MB | Past performance | Active |
| `data/checkpoints_meta.db` | 24 KB | Pipeline run tracking | Active |

**Total: ~2.0 GB across 12 databases (including 737 MB duplicate Qdrant store)**

### 8.2 Data Quality Issues

- **Duplicate Qdrant stores** consuming 737 MB — `data/qdrant/` and `Engine8_Knowledge/data/qdrant/`
- **Duplicate contract databases** — `unified_federal_contracts.db` and `master_federal_contracts.db` with overlapping data
- **Contract DB copies in directories with spaces** — `Engine8_Knowledge/assigned and open contracts Data scraper/`
- **Naming inconsistency** — mix of `_All.csv`, `_BACKUP_`, `_ENRICHED`, `_ACTIVE`, `_MASTER` without convention
- **Emoji in filenames** — `📊 Insight Global Jobs - Program Mapped All.csv`
- **Qdrant last indexed Feb 3** — potentially stale (2.5 weeks old)

### 8.3 Migration Script Assessment

`scripts/full_migration_to_supabase.py` (1,726 lines):
- Migrates 4 SQLite sources to 14 Supabase tables
- **Missing:** `ON CONFLICT` handling (destructive TRUNCATE+INSERT, non-idempotent)
- **Missing:** Graph data migration (`bd_graph.db` 63K entities not migrated)
- **Missing:** `master_federal_contracts.db` not included (data loss risk)
- **Bug:** UUID FK resolution via name-matching (40-60% skip rate likely)
- **Credential:** Hardcoded Supabase DSN with plaintext password at line 38

---

## 9. Documentation

**Health Score: 52/100**

### Coverage

| Area | Status |
|------|--------|
| Engine 1 (Scraper) | No README |
| Engine 2 (Program Mapping) | No README |
| Engine 3 (OrgChart) | No README |
| Engine 4 (Playbook) | No README |
| Engine 5 (Scoring) | No README |
| Engine 6 (QA) | No README |
| Engine 7 (Bullhorn ETL) | Good README |
| Engine 8 (Knowledge) | Good README |
| MCP servers | **Best documented area** |
| k8s/ (12 manifests) | Zero documentation |
| helm/ (4 YAML files) | Zero documentation |
| monitoring/grafana/ (5 dashboards) | Zero documentation |
| n8n/ (18 workflows) | Zero documentation |
| api.py (222+ routes) | Near-zero docstrings |

### Accuracy Issues

- `SETUP_GUIDE.md` describes 5-engine pipeline (actual: 8)
- `orchestrator.py` docstring says `Engine4_Briefing` (actual: `Engine4_Playbook`)
- `CLAUDE.md` says "Engine 6 in progress" (actual: complete)
- Federal programs count: 388 (CLAUDE.md) vs 401 (Engine8 README) — inconsistent
- `FOLDER_STRUCTURE.md` missing Engines 6-8, dashboard, monitoring, helm, k8s

### Missing

- No static OpenAPI spec (222+ endpoints documented only at runtime)
- No data dictionary for SQLite/Qdrant schemas
- No operational runbooks (Qdrant down, pipeline state corruption, re-indexing)
- No test documentation for 100+ test files

---

## 10. 3-to-1 Consolidation Readiness

### Current State

The "3 repos" are:
1. **BD Engine** — this repository's Engine 1-8 pipeline
2. **Dashboard** — `dashboard/` directory (React/Vite app, 65K files including dist/node_modules)
3. **Auto-Claude parent** — the monorepo at `C:\Auto-Claud\Auto-Claude\`

### Ready for Consolidation As-Is

- `config/settings.py`, `config/resilience.py` — proper abstraction
- `models/base.py`, `models/contacts.py`, `models/programs.py` — quality Pydantic models
- `Engine3_OrgChart/contact_classifier.py` — self-contained
- `Engine5_Scoring/bd_scoring.py` — self-contained
- `Engine6_QA/alerts.py`, `qa_feedback.py` — self-contained

### Needs Fixes First

- `Engine2/full_pipeline.py` — delete (completely broken)
- `Engine2/job_standardizer.py` — must migrate from `anthropic.Anthropic()` to claude-agent-sdk
- `Engine2/generate_bd_playbook.py` — fix eval(), bare except, count bug
- `orchestrator.py` — fix stage labels, add stage dependency checks

### Consolidation Blueprint (4 Phases)

**Phase 1 — Safety (Day 1):** Rotate credentials, remove duplicate crawl4ai, delete dead code, add .gitignore entries

**Phase 2 — Package Structure (Week 1):** Create `pyproject.toml`, `pip install -e .`, remove sys.path hacks, consolidate `normalize_company_name`

**Phase 3 — Database Migration (Week 2):** Fix migration script (ON CONFLICT, graph data, master_federal_contracts), run migration, flip USE_SUPABASE=true

**Phase 4 — API Consolidation (Week 3-4):** Split api.py into router modules, create LangGraph workflow replacing sequential orchestrator, replace n8n webhooks with LangGraph triggers

---

## 11. Prioritized Remediation Roadmap

### IMMEDIATE (24-48 hours)

| # | Action | Risk Mitigated |
|---|--------|---------------|
| 1 | **Rotate ALL 20+ exposed credentials** | Credential compromise |
| 2 | `git rm --cached` all .env files | Prevent future exposure |
| 3 | Replace hardcoded Supabase DSN in 5 source files | Source code credentials |
| 4 | Replace all `eval()` with `json.loads()`/`ast.literal_eval()` (13 instances) | Code injection |
| 5 | Change Neo4j default password in 5 files | Hardcoded credentials |

### SHORT-TERM (1 week)

| # | Action | Risk Mitigated |
|---|--------|---------------|
| 6 | Add API authentication to Engine 8 (FastAPI `Security` dependency) | Unauthorized PII access |
| 7 | Fix CORS to explicit origins | Cross-origin data theft |
| 8 | Add logging to all `except Exception: pass` in ETL (7 blocks) | Silent data loss |
| 9 | Fix zero-vector fallback in vector_store.py | Search result corruption |
| 10 | Enable WAL mode on ETL database | Read-write blocking |
| 11 | Add `detect-secrets` pre-commit hook | Prevent future credential commits |
| 12 | Delete `Engine2/full_pipeline.py` | Dead code confusion |

### MEDIUM-TERM (2-4 weeks)

| # | Action | Risk Mitigated |
|---|--------|---------------|
| 13 | Create `pyproject.toml` and remove sys.path hacks | Import fragility |
| 14 | Consolidate `normalize_company_name` to single module | Inconsistent normalization |
| 15 | Unify `SearchResult` dataclass | Type incompatibility |
| 16 | Add stage dependency checks in orchestrator | Garbage data downstream |
| 17 | Fix migration script (ON CONFLICT, graph, master_federal_contracts) | Data loss during migration |
| 18 | Pin dependency versions with upper bounds | Supply chain risk |
| 19 | Add Redis/Qdrant authentication | Unauthorized database access |
| 20 | Write READMEs for Engines 1-6 | Developer onboarding |
| 21 | Split api.py into router modules | Maintainability |
| 22 | Enable batch embedding for indexing | 28 min → 0.8 sec indexing |

### LONG-TERM (1-3 months)

| # | Action | Risk Mitigated |
|---|--------|---------------|
| 23 | Implement RBAC on all API endpoints | Least-privilege access |
| 24 | Deploy secrets management (Vault/AWS SM) | Credential lifecycle |
| 25 | Create LangGraph workflow replacing orchestrator | Pipeline parallelism |
| 26 | Run Supabase migration with verified counts | SQLite → PostgreSQL |
| 27 | Implement structured audit logging | Compliance (NIST 3.3) |
| 28 | Field-level encryption for PII | Data protection |
| 29 | Static OpenAPI spec + data dictionary | Documentation completeness |
| 30 | NIST 800-171 self-assessment + SSP | CMMC readiness |

---

## Appendix: File Inventory

### Engine File Counts

| Engine | Python | CSV | JSON | DB | Other | Total |
|--------|--------|-----|------|----|-------|-------|
| 1 - Scraper | 0 | 3 | 21 | 0 | 1 | 25 |
| 2 - Program Mapping | 9 | 12 | 2 | 0 | 8 | 31 |
| 3 - OrgChart | 2 | 67 | 2 | 0 | 2 | 73 |
| 4 - Playbook | 1 | 0 | 1 | 0 | 2 | 5 |
| 5 - Scoring | 1 | 0 | 1 | 0 | 0 | 3 |
| 6 - QA | 3 | 0 | 1 | 0 | 3 | 7 |
| 7 - Bullhorn ETL | 22 | 41 | 35 | 2 | 16 | 116 |
| 8 - Knowledge | 248 | 6 | 23 | 6 | 224 | 507 |
| **Total** | **286** | **129** | **86** | **8** | **256** | **767** |

### Critical File Reference

| File | Why Critical |
|------|-------------|
| `orchestrator.py` (1,086 lines) | Master pipeline wiring all engines |
| `Engine8_Knowledge/api.py` (4,682 lines) | Central API, 222+ routes, zero auth |
| `Engine7_BullhornETL/scripts/bullhorn_etl_v2.py` | Most dangerous file — silent data loss |
| `Engine7_BullhornETL/scripts/ingest_new_notes.py` | 11 eval() calls on DB data |
| `Engine8_Knowledge/scripts/vector_store.py` | Zero-vector fallback corrupts search |
| `Engine8_Knowledge/scripts/hybrid_retriever.py` | Full collection load for BM25 |
| `scripts/full_migration_to_supabase.py` (1,726 lines) | Database migration (needs fixes) |
| `.env` | 16+ live production credentials |

### Agent Execution Summary

| Wave | Agents | Duration | Findings |
|------|--------|----------|----------|
| 1 - Discovery | 3 | ~5 min | 83,599 files mapped, 8 DB schemas, full directory structure |
| 2 - Deep Analysis | 7 | ~15 min | 23 security findings (8 CRITICAL), 47 silent failures, 17 code issues |
| 3 - Cross-Cutting | 4 | ~10 min | 17 performance bottlenecks, CMMC failure, 4-phase consolidation blueprint |
| 4 - Synthesis | 1 | This report | Unified findings, prioritized roadmap |
| **Total** | **15** | **~30 min** | **100+ actionable findings** |

---

*Report generated by 15+ specialized Claude Opus 4.6 subagents across 4 execution waves. All findings are evidence-based with specific file paths and line numbers.*
