# OpenClaw as a Repo Agent — Deployment Plan

Deploy OpenClaw pointed at the BD-Automation-Engine repo to autonomously audit, clean, improve, and build out the codebase. Every change lands on a review branch as a PR you approve or reject.

---

## How This Works

```
┌──────────────────────────────────────────────────────┐
│                YOUR MACHINE (or VM)                   │
│                                                       │
│   OpenClaw Daemon (:18789)                           │
│      │                                                │
│      ├─ Skill: repo-auditor                          │
│      │    └─ Scans code quality, dead code, deps     │
│      ├─ Skill: code-improver                         │
│      │    └─ Refactors, types, tests, docs           │
│      ├─ Skill: data-organizer                        │
│      │    └─ Dedup DBs, clean data dirs, migrations  │
│      ├─ Skill: pipeline-builder                      │
│      │    └─ Fixes engines, wires orchestrator       │
│      ├─ Skill: infra-upgrader                        │
│      │    └─ CI, Docker, deps, auth, monitoring      │
│      └─ Skill: bd-enrichment                         │
│           └─ Data scraping, mapping, CRM creation    │
│                                                       │
│   MCP Servers:                                        │
│      ├─ filesystem (read/write repo files)           │
│      ├─ github (create branches, PRs, issues)        │
│      └─ knowledge-mcp (query existing BD data)       │
│                                                       │
│   Workflow:                                           │
│      1. OpenClaw runs a skill                        │
│      2. Creates a feature branch                     │
│      3. Makes changes + commits                      │
│      4. Opens a PR against your working branch       │
│      5. You review and merge (or reject)             │
│      6. OpenClaw learns from your feedback            │
└──────────────────────────────────────────────────────┘
```

**Every change is a PR. Nothing lands without your approval.**

---

## Step 1: Install OpenClaw on Your Machine

You're on Windows 11 with Git Bash. OpenClaw runs natively.

### Prompt 1: Install and Onboard

```
Install OpenClaw on this Windows 11 machine.

1. Install globally:
   npm install -g openclaw@latest

2. Run onboarding:
   openclaw onboard --install-daemon

   Configure:
   - AI Provider: Anthropic
   - Model: claude-sonnet-4-6
   - API Key: (use your ANTHROPIC_API_KEY)
   - Workspace: C:\Auto-Claud\Auto-Claude\BD-Automation-Engine
   - Skip messaging channels for now

3. Verify:
   openclaw status
   openclaw chat "Hello, what workspace are you pointed at?"
```

### Prompt 2: Configure MCP Servers

```
Configure OpenClaw MCP servers for repo work.

Add to openclaw.json:

1. Filesystem MCP — read/write project files:
   Server: @anthropic/mcp-server-filesystem
   Allowed paths: ["C:/Auto-Claud/Auto-Claude/BD-Automation-Engine"]

2. GitHub MCP — branches, PRs, issues:
   Server: @anthropic/mcp-server-github
   Env: GITHUB_TOKEN=<your token>

3. Knowledge MCP (when API is running) — query BD data:
   Server: node C:/Auto-Claud/Auto-Claude/BD-Automation-Engine/mcp/knowledge-mcp-server/dist/index.js
   Env: BD_API_URL=http://localhost:8100

Verify:
   openclaw mcp list
   openclaw mcp test filesystem
   openclaw mcp test github
```

---

## Step 2: The Six Skills OpenClaw Needs

Each skill below is a self-contained agent that OpenClaw runs. Each one creates a branch, makes changes, and opens a PR.

---

### Skill 1: repo-auditor

**Purpose:** Full codebase audit. Finds everything wrong and creates a prioritized issue backlog.

#### Prompt 3: Create repo-auditor Skill

```
You are building an OpenClaw skill called "repo-auditor" that performs a comprehensive audit of a Python codebase.

Create: ~/.openclaw/skills/repo-auditor/skill.mjs

The skill runs 8 audit passes and creates GitHub issues for each finding:

PASS 1 — DEAD CODE DETECTION
  - Scan all .py files for unused imports (use AST parsing or grep patterns)
  - Detect unused variables (especially the 12 'authenticated' stubs in api/unified_endpoints.py)
  - Find empty files, 0-byte files (like Engine7_BullhornETL/data/bullhorn.db)
  - Find duplicate directories serving the same purpose (Engine4_Briefing vs Engine4_Playbook)
  - Output: List of files/lines with dead code, severity (low/med/high)

PASS 2 — DEPENDENCY AUDIT
  - Parse requirements.txt for:
    - Duplicate entries (crawl4ai appears twice with different version constraints)
    - Missing version ceilings (everything is >= with no upper bound)
    - Dev dependencies mixed with production (pytest, fakeredis in same file)
    - Commented-out packages still imported somewhere
  - Check for a lock file (requirements.lock or uv.lock) — flag if missing
  - Output: Dependency health report with specific fixes

PASS 3 — DATABASE DUPLICATION
  - Find all SQLite .db files — report path, size, table schemas
  - Find all Qdrant data directories — report paths and sizes
  - Identify overlapping data (bullhorn.db vs bullhorn_master.db, three qdrant/ dirs)
  - Flag 0-byte databases as dead
  - Output: Database inventory with dedup recommendations

PASS 4 — DATA FILE AUDIT
  - Scan all data/ directories for:
    - Multiple versions of the same CSV (Federal Programs has 5+ variants)
    - Backup files that should be gitignored
    - Test artifacts in production data dirs (lightrag_test2/)
    - Large files that shouldn't be in git (anything > 50MB)
  - Output: Data file inventory with archive/delete recommendations

PASS 5 — CI/CD HEALTH
  - Read .github/workflows/*.yml
  - Flag: || true on pytest (test failures silently ignored)
  - Flag: || true on mypy (type errors silently ignored)
  - Flag: Coverage threshold configured but never enforced
  - Flag: Missing CI for Engines 2-7
  - Output: CI health report with specific fixes

PASS 6 — CODE QUALITY METRICS
  - Count files with/without type hints (by directory)
  - Count files with/without docstrings
  - Measure average function length
  - Find functions > 100 lines (refactoring candidates)
  - Find files > 500 lines (splitting candidates)
  - Output: Quality metrics dashboard

PASS 7 — SECURITY SCAN
  - Check for hardcoded secrets, API keys, tokens in source
  - Verify .env is in .gitignore
  - Check api/unified_endpoints.py auth stub (assigned but never enforced)
  - Check for SQL injection vectors in raw SQL queries
  - Check for unvalidated user input in API endpoints
  - Output: Security findings with severity ratings

PASS 8 — ARCHITECTURE GAPS
  - Compare CLAUDE.md engine descriptions against actual code
  - Identify engines with no tests
  - Identify endpoints with no error handling
  - Find stub/placeholder code in src/ that isn't wired to anything
  - Check orchestrator.py for stages that are flags but not implemented
  - Output: Architecture gap analysis

FINAL OUTPUT:
  - Create GitHub issues for each finding (grouped by pass)
  - Label: audit/dead-code, audit/deps, audit/data, audit/ci, audit/quality, audit/security, audit/architecture
  - Priority: P0 (fix now), P1 (fix this week), P2 (fix when convenient)
  - Write full report to outputs/audit/audit_report_{date}.md

skill.md manifest:
  name: repo-auditor
  description: Comprehensive 8-pass codebase audit. Creates GitHub issues for dead code, dependency problems, database duplication, CI gaps, security issues, and architecture gaps.
  triggers: ["audit repo", "scan codebase", "find problems", "code health check"]
```

---

### Skill 2: code-improver

**Purpose:** Takes audit findings and makes the actual code changes. One PR per improvement area.

#### Prompt 4: Create code-improver Skill

```
You are building an OpenClaw skill called "code-improver" that fixes code quality issues found by the repo-auditor.

Create: ~/.openclaw/skills/code-improver/skill.mjs

The skill takes an improvement category and creates a branch + PR with the fixes.

IMPROVEMENT CATEGORIES:

1. DEAD_CODE_CLEANUP
   Branch: openclaw/cleanup-dead-code
   Actions:
   - Remove all unused imports across all .py files
   - Remove the 12 dead 'authenticated' variable assignments in api/unified_endpoints.py
   - Delete Engine7_BullhornETL/data/bullhorn.db (0 bytes)
   - Delete lightrag_test2/ from Engine8 data
   - Create a decision doc: should Engine4_Briefing or Engine4_Playbook be the canonical one?
   PR title: "chore: Remove dead code, unused imports, and empty artifacts"

2. DEPENDENCY_CLEANUP
   Branch: openclaw/fix-dependencies
   Actions:
   - Remove duplicate crawl4ai entry from requirements.txt
   - Split into requirements.txt (production) and requirements-dev.txt (testing/linting)
   - Add version ceilings to critical packages (qdrant-client<1.15, anthropic<1.0)
   - Generate uv.lock file
   - Remove commented-out packages that aren't imported anywhere
   PR title: "chore: Clean up dependencies, split prod/dev, add lock file"

3. TYPE_HINTS
   Branch: openclaw/add-type-hints
   Actions:
   - Add type hints to Engine2 core scripts (job_standardizer.py, program_mapper.py)
   - Add type hints to Engine5 scoring (bd_scoring.py)
   - Add Pydantic models for API request/response schemas that don't have them
   - Enable mypy strict mode for new code only (gradual adoption)
   PR title: "feat: Add type hints to core engine scripts"

4. CI_FIX
   Branch: openclaw/fix-ci
   Actions:
   - Remove || true from pytest step — tests must pass
   - Remove || true from mypy step — type checks must pass
   - Add pytest coverage for Engines 2-7 (not just Engine8)
   - Enforce the 60% coverage threshold that's configured but ignored
   - Add a pre-commit hook for ruff
   PR title: "fix: Make CI actually fail on test/type errors"

5. API_AUTH
   Branch: openclaw/implement-auth
   Actions:
   - Wire up the 'authenticated' stub in api/unified_endpoints.py
   - Add API key validation middleware to FastAPI
   - Create a simple auth scheme: API key in header, validated against .env
   - Add auth to all write endpoints (reads can stay open for now)
   PR title: "feat: Implement API authentication for write endpoints"

6. TEST_COVERAGE
   Branch: openclaw/add-tests
   Actions:
   - Add unit tests for Engine3 contact_classifier.py
   - Add unit tests for Engine4 playbook generator
   - Add integration tests for the orchestrator pipeline
   - Add API endpoint tests for the top 10 most-used endpoints
   - Use pytest fixtures and mocking (no real API calls in tests)
   PR title: "test: Add missing test coverage for Engines 3, 4, and orchestrator"

WORKFLOW:
  1. Read the relevant source files
  2. Create feature branch from claude/setup-auto-claude-IrK21
  3. Make changes, commit with conventional commit messages
  4. Run ruff lint and fix any issues
  5. Run existing tests to verify nothing breaks
  6. Open PR with description of what changed and why
  7. If tests fail, fix and update PR

SAFETY:
  - Never modify .env or any file containing secrets
  - Never delete data files without creating a backup reference
  - Always run tests before opening PR
  - One improvement category per PR (small, reviewable changes)

skill.md manifest:
  name: code-improver
  description: Fixes code quality issues. Removes dead code, cleans dependencies, adds type hints, fixes CI, implements auth, adds tests. One PR per improvement area.
  triggers: ["fix dead code", "clean dependencies", "add types", "fix ci", "add tests", "improve code"]
```

---

### Skill 3: data-organizer

**Purpose:** Cleans up the data mess — deduplicates databases, consolidates CSVs, creates proper migrations.

#### Prompt 5: Create data-organizer Skill

```
You are building an OpenClaw skill called "data-organizer" that cleans up data duplication and creates proper database management.

Create: ~/.openclaw/skills/data-organizer/skill.mjs

TASK 1: QDRANT DEDUPLICATION
   Branch: openclaw/dedup-qdrant
   Problem: Qdrant data exists in 3 directories (~3.3GB total, ~1.1GB actual):
     - BD-Automation-Engine/qdrant/
     - BD-Automation-Engine/data/qdrant/
     - BD-Automation-Engine/Engine8_Knowledge/data/qdrant/
   Actions:
   - Determine which directory the running Qdrant server (localhost:6333) uses
   - Add the other two to .gitignore
   - Update all code references to use QDRANT_URL=http://localhost:6333 (server mode, not file mode)
   - Remove hardcoded file paths to local qdrant directories
   - Document the canonical data path
   PR: "fix: Deduplicate Qdrant data dirs, enforce server mode"

TASK 2: SQLITE CONSOLIDATION
   Branch: openclaw/consolidate-sqlite
   Problem: 7+ SQLite files with overlapping data:
     - unified_federal_contracts.db (134MB) vs master_federal_contracts.db (48MB)
     - bullhorn_master.db (293MB) vs bullhorn.db (0 bytes, dead)
     - bullhorn_past_performance.db (23MB, derived)
     - bd_graph.db (22MB, LightRAG)
     - chroma.sqlite3 (8.6MB, alongside Qdrant — dual vector store?)
   Actions:
   - Delete bullhorn.db (0 bytes)
   - Determine if unified_federal_contracts.db supersedes master_federal_contracts.db
   - Document the purpose of each remaining DB in a DATA_INVENTORY.md
   - If chroma is unused (Qdrant is primary), remove or gitignore it
   - Create a database schema doc showing all tables across all DBs
   PR: "chore: Consolidate SQLite databases, remove dead files, document schema"

TASK 3: CSV CANONICALIZATION
   Branch: openclaw/canonicalize-csvs
   Problem: Federal Programs has 5+ CSV variants with unclear lineage
   Actions:
   - Compare all Federal Programs CSV files (column overlap, row counts)
   - Determine the canonical "latest" version
   - Rename it to Federal_Programs_Master.csv
   - Move old versions to data/archive/ (gitignored)
   - Update all code references to point to the canonical file
   - Do the same for any other duplicated CSVs
   PR: "chore: Canonicalize CSV data files, archive old versions"

TASK 4: DATABASE MIGRATION SYSTEM
   Branch: openclaw/add-migrations
   Problem: No migration system — schema changes are ad-hoc scripts
   Actions:
   - Set up Alembic for SQLAlchemy-based migration tracking
   - Create initial migration from current schema (auto-generate from existing tables)
   - Convert the ad-hoc scripts (fix_remaining_migration.py, full_migration_to_supabase.py) into proper Alembic migrations
   - Add alembic commands to the Makefile/README
   - Create a migration guide doc
   PR: "feat: Add Alembic migration system for database schema management"

TASK 5: DATA DIRECTORY RESTRUCTURE
   Branch: openclaw/restructure-data
   Problem: Data scattered across engine dirs with no clear organization
   Actions:
   - Create canonical structure:
     data/
       databases/          # All SQLite DBs
       vectors/            # Qdrant connection config (not data — that's in Docker volume)
       csv/                # Canonical CSVs
       csv/archive/        # Old versions (gitignored)
       exports/            # Pipeline output (gitignored)
       dashboard/          # Dashboard JSON snapshots
       state/              # Pipeline state files
   - Update all code paths
   - Update .gitignore for the new structure
   - Update CLAUDE.md project structure section
   PR: "refactor: Restructure data directories with clear canonical paths"

WORKFLOW:
  - One task per PR
  - Run in order (1→2→3→4→5) since later tasks depend on earlier ones
  - Always verify existing code still works after path changes
  - Never delete data without confirming it's either dead or backed up

skill.md manifest:
  name: data-organizer
  description: Deduplicates databases, consolidates CSVs, creates migration system, restructures data directories. Fixes the 3.3GB Qdrant duplication and 7-database sprawl.
  triggers: ["organize data", "clean databases", "fix data dirs", "dedup", "consolidate data"]
```

---

### Skill 4: pipeline-builder

**Purpose:** Fix and complete the actual BD pipeline — wire stub engines, fix the orchestrator, close architecture gaps.

#### Prompt 6: Create pipeline-builder Skill

```
You are building an OpenClaw skill called "pipeline-builder" that fixes and completes the BD-Automation-Engine pipeline.

Create: ~/.openclaw/skills/pipeline-builder/skill.mjs

TASK 1: FIX PATTERN ENGINE (Replace Mock Data)
   Branch: openclaw/fix-pattern-engine
   Problem: src/intelligence/pattern_engine.py uses 7 hardcoded arrays instead of real data
   Actions:
   - Replace _HIRING_DATA with Qdrant query against jobs collection
   - Replace _LEADERSHIP_EVENTS with contacts collection query (role changes)
   - Replace _CONTRACT_MILESTONES with programs collection query
   - Replace _COMPETITIVE_SHIFTS with programs competition data
   - Replace _BUDGET_SIGNALS with programs budget/funding fields
   - Replace _GEOGRAPHIC_SHIFTS with jobs location data
   - Replace _SKILL_DEMANDS with jobs skills/requirements data
   - Each query goes through the Hub API (http://localhost:8100)
   - Add tests with mocked API responses
   PR: "feat: Wire pattern engine to real Qdrant data via Hub API"

TASK 2: FIX SWARM WORKERS (Replace Empty Placeholders)
   Branch: openclaw/fix-swarm-workers
   Problem: src/agents/swarm/workers.py _default_execute() returns empty arrays
   Actions:
   - Implement researcher executor: calls /search and /api/v2/programs
   - Implement contact_finder executor: calls /api/v2/contacts
   - Implement scorer executor: calls /api/v2/intelligence/score
   - Implement writer executor: calls /ask/smart with task-specific prompts
   - Implement analyst executor: calls /api/v2/intelligence/patterns
   - Register each via registry.register_executor()
   - Add tests for each executor with mocked responses
   PR: "feat: Implement swarm worker executors with real API calls"

TASK 3: PERSIST MEMORY CORTEX
   Branch: openclaw/persist-memory
   Problem: src/memory/cortex.py stores everything in Python dicts — lost on restart
   Actions:
   - Create 3 new Qdrant collections via Hub API:
     episodic_memories (1536-dim, cosine)
     semantic_facts (1536-dim, cosine)
     procedural_insights (1536-dim, cosine)
   - Add API endpoints for memory CRUD:
     POST/GET /api/v2/memory/episodes
     POST/GET /api/v2/memory/facts
     POST/GET /api/v2/memory/insights
   - Refactor cortex.py to use these endpoints instead of dicts
   - Add startup recovery: load recent memories from Qdrant on init
   - Add tests
   PR: "feat: Persist memory cortex to Qdrant, add memory API endpoints"

TASK 4: FIX ORCHESTRATOR WIRING
   Branch: openclaw/fix-orchestrator
   Problem: orchestrator.py has config flags that may not be wired to actual engines
   Actions:
   - Verify each stage (1-11) actually calls the correct engine
   - Fix any stages that are boolean flags without real execution
   - Replace time.sleep scheduling with proper async handling
   - Add proper error handling per stage (don't fail the whole pipeline if one stage errors)
   - Add structured logging with stage timings
   - Add a --dry-run flag that validates config without executing
   PR: "fix: Wire all orchestrator stages to real engines, add error isolation"

TASK 5: RESOLVE ENGINE4 DUPLICATION
   Branch: openclaw/resolve-engine4
   Problem: Both Engine4_Briefing/ and Engine4_Playbook/ exist
   Actions:
   - Compare the two implementations (briefing_generator.py vs bd_playbook_generator.py)
   - Determine if they serve different purposes or are duplicates
   - If different: document both in CLAUDE.md, rename for clarity
   - If overlapping: merge the best of both into one, archive the other
   - Update orchestrator.py references
   PR: "refactor: Resolve Engine4 duplication (Briefing vs Playbook)"

skill.md manifest:
  name: pipeline-builder
  description: Fixes the BD pipeline. Wires pattern engine to real data, implements swarm workers, persists memory, fixes orchestrator, resolves Engine4 duplication.
  triggers: ["fix pipeline", "wire engines", "fix orchestrator", "implement workers", "fix patterns"]
```

---

### Skill 5: infra-upgrader

**Purpose:** Fix CI, Docker, monitoring, and infrastructure concerns.

#### Prompt 7: Create infra-upgrader Skill

```
You are building an OpenClaw skill called "infra-upgrader" that improves the project's infrastructure.

Create: ~/.openclaw/skills/infra-upgrader/skill.mjs

TASK 1: FIX CI PIPELINE
   Branch: openclaw/fix-ci-pipeline
   Actions:
   - Remove || true from pytest in ci.yml — tests must pass to merge
   - Remove || true from mypy — type errors must be fixed
   - Add separate CI jobs: lint, typecheck, test-engine8, test-engines, test-api
   - Add coverage reporting (upload to codecov or just print in CI)
   - Enforce the 60% coverage threshold from pyproject.toml
   - Add a CI job that runs ruff format --check
   - Add matrix testing for Python 3.11 and 3.12
   PR: "fix: Make CI pipeline actually enforce quality gates"

TASK 2: DOCKER OPTIMIZATION
   Branch: openclaw/optimize-docker
   Actions:
   - Review Dockerfile multi-stage build for unnecessary layers
   - Add .dockerignore to exclude: .git, node_modules, outputs/, __pycache__, *.db, data/qdrant/
   - Optimize layer caching (copy requirements.txt before source code)
   - Add health check to hub_api container
   - Review docker-compose.yml resource limits
   - Add docker-compose.test.yml for CI integration testing
   PR: "chore: Optimize Docker build, add .dockerignore, improve caching"

TASK 3: MONITORING AND OBSERVABILITY
   Branch: openclaw/add-monitoring
   Actions:
   - Add Prometheus metrics endpoint to Hub API (/metrics)
   - Track: request count, latency histogram, error rate, qdrant query duration
   - Add structured logging with correlation IDs across API requests
   - Create a Grafana dashboard JSON for the key metrics
   - Add a /monitoring/live and /monitoring/ready endpoint for k8s probes
   - Add startup health check that verifies all external dependencies
   PR: "feat: Add Prometheus metrics, structured logging, health probes"

TASK 4: SECRETS AND CONFIG MANAGEMENT
   Branch: openclaw/improve-config
   Actions:
   - Audit every place that reads from os.environ or .env
   - Create a central config.py using Pydantic Settings (BaseSettings)
   - Validate all required env vars at startup with clear error messages
   - Add .env.example with every required variable documented
   - Ensure no secrets can leak into logs (mask API keys in log output)
   PR: "feat: Centralize config with Pydantic Settings, validate on startup"

TASK 5: MAKEFILE / TASK RUNNER
   Branch: openclaw/add-makefile
   Actions:
   - Create a Makefile (or justfile) with common commands:
     make install      — set up venv, install deps
     make dev          — start all services locally
     make test         — run full test suite
     make lint         — ruff check + format
     make typecheck    — mypy
     make docker-up    — docker compose up
     make docker-down  — docker compose down
     make index        — reindex all Qdrant collections
     make audit        — run dead code + dep audit
   - Update README with the new commands
   PR: "chore: Add Makefile with standard development commands"

skill.md manifest:
  name: infra-upgrader
  description: Fixes CI pipeline, optimizes Docker, adds monitoring, centralizes config, creates Makefile. Infrastructure hardening.
  triggers: ["fix ci", "improve docker", "add monitoring", "fix config", "add makefile"]
```

---

### Skill 6: bd-enrichment

**Purpose:** The offensive skill — scrapes new data, enriches existing records, builds new database tables, maps relationships.

#### Prompt 8: Create bd-enrichment Skill

```
You are building an OpenClaw skill called "bd-enrichment" that enriches the BD intelligence data.

Create: ~/.openclaw/skills/bd-enrichment/skill.mjs

TASK 1: CONTACT ENRICHMENT
   Branch: openclaw/enrich-contacts
   Actions:
   - Query contacts collection for records with missing fields (no email, no phone, no tier)
   - For each incomplete contact:
     - Search LinkedIn (via Apify actor) for additional data
     - Search company website for org chart / directory
     - Classify tier using Engine3 contact_classifier.py
   - Update contact records in Qdrant via Hub API
   - Log all enrichment actions with source attribution
   - Respect rate limits: max 50 enrichments per run
   PR: "feat: Auto-enrich contacts with missing fields via LinkedIn/company search"

TASK 2: PROGRAM INTELLIGENCE ENRICHMENT
   Branch: openclaw/enrich-programs
   Actions:
   - Query SAM.gov API for latest contract awards in DCGS portfolio
   - Cross-reference with existing 388 programs in Federal_Programs_Master.csv
   - For new programs not in the CSV: add them
   - For existing programs: update contract values, period of performance, incumbent
   - Query USASpending.gov for budget allocation data
   - Enrich program records in Qdrant with latest fiscal data
   PR: "feat: Enrich federal programs with SAM.gov and USASpending data"

TASK 3: JOB SCRAPING AND MAPPING
   Branch: openclaw/scrape-and-map-jobs
   Actions:
   - Trigger Apify scraper (Engine 1) for latest defense job postings
   - Run Engine 2 pipeline on new jobs (standardize → map → score)
   - Auto-generate playbooks for any new hot leads (BD Score >= 80)
   - Index all new data into Qdrant
   - Update pipeline_state.json
   PR: "feat: Full job scrape → map → score → playbook pipeline run"

TASK 4: RELATIONSHIP MAPPING
   Branch: openclaw/map-relationships
   Actions:
   - Analyze contacts collection for co-located contacts (same company + program)
   - Build relationship edges in Neo4j:
     CONTACT -[WORKS_AT]-> COMPANY
     CONTACT -[WORKS_ON]-> PROGRAM
     COMPANY -[PRIMES]-> PROGRAM
     CONTACT -[KNOWS]-> CONTACT (inferred from shared activities)
   - Score each relationship using Engine5's 6-dimension scoring
   - Generate a network analysis report: key connectors, isolated nodes, cluster detection
   PR: "feat: Build Neo4j relationship graph from contacts/programs/activities"

TASK 5: CRM SYNC AND CREATION
   Branch: openclaw/crm-sync
   Actions:
   - Design a CRM schema optimized for BD pipeline data:
     Tables: contacts, companies, programs, opportunities, activities, relationships, scores
   - Create the schema in SQLite (or Supabase if configured)
   - ETL existing Bullhorn data (Engine7) into the new CRM schema
   - ETL Qdrant contacts into CRM contacts table
   - ETL programs collection into CRM programs table
   - Map relationships between tables (foreign keys, junction tables)
   - Create a read API: GET /api/v2/crm/{table}?filter=...
   - Create a write API: POST /api/v2/crm/{table}
   PR: "feat: Create unified CRM database with ETL from Bullhorn + Qdrant"

SAFETY:
   - All data enrichment writes require Tier 2 approval (auto-approved within budget)
   - External API calls (SAM.gov, LinkedIn, USASpending) have rate limiters
   - Never overwrite existing data — only append or update null fields
   - Log all sources for audit trail
   - Max 50 enrichment operations per skill run

skill.md manifest:
  name: bd-enrichment
  description: Enriches BD data. Scrapes jobs, enriches contacts, updates program intelligence, maps relationships in Neo4j, builds unified CRM.
  triggers: ["enrich contacts", "scrape jobs", "update programs", "map relationships", "build crm", "enrich data"]
```

---

## Step 3: The Master Run Sequence

Once all skills are installed, here's the order OpenClaw should execute them:

### Prompt 9: Create the Master Orchestration Skill

```
You are building a master orchestration skill for OpenClaw that runs the full improvement pipeline in the correct order.

Create: ~/.openclaw/skills/repo-master/skill.mjs

PHASE 1 — AUDIT (day 1)
  Run: repo-auditor
  Output: GitHub issues created, audit_report.md generated
  Gate: Wait for human to review audit report before proceeding

PHASE 2 — CLEANUP (day 1-2, after audit approval)
  Run in order:
  1. code-improver DEAD_CODE_CLEANUP
  2. code-improver DEPENDENCY_CLEANUP
  3. data-organizer QDRANT_DEDUPLICATION
  4. data-organizer SQLITE_CONSOLIDATION
  5. data-organizer CSV_CANONICALIZATION
  Gate: All PRs must be merged before Phase 3

PHASE 3 — STRUCTURE (day 2-3, after cleanup merged)
  Run in order:
  1. data-organizer DATA_DIRECTORY_RESTRUCTURE
  2. data-organizer DATABASE_MIGRATION_SYSTEM
  3. infra-upgrader FIX_CI_PIPELINE
  4. infra-upgrader MAKEFILE
  5. infra-upgrader SECRETS_AND_CONFIG
  Gate: All PRs must be merged before Phase 4

PHASE 4 — QUALITY (day 3-4, after structure merged)
  Run in parallel (independent):
  - code-improver TYPE_HINTS
  - code-improver TEST_COVERAGE
  - code-improver API_AUTH
  - infra-upgrader DOCKER_OPTIMIZATION
  - infra-upgrader MONITORING
  Gate: All PRs merged before Phase 5

PHASE 5 — PIPELINE FIX (day 4-5, after quality merged)
  Run in order:
  1. pipeline-builder FIX_PATTERN_ENGINE
  2. pipeline-builder FIX_SWARM_WORKERS
  3. pipeline-builder PERSIST_MEMORY
  4. pipeline-builder FIX_ORCHESTRATOR
  5. pipeline-builder RESOLVE_ENGINE4
  Gate: All PRs merged before Phase 6

PHASE 6 — ENRICHMENT (day 5+, after pipeline working)
  Run in order:
  1. bd-enrichment CONTACT_ENRICHMENT
  2. bd-enrichment PROGRAM_INTELLIGENCE
  3. bd-enrichment JOB_SCRAPING
  4. bd-enrichment RELATIONSHIP_MAPPING
  5. bd-enrichment CRM_SYNC

TRACKING:
  - Maintain a progress file: outputs/openclaw_progress.json
  - After each task: update status (pending/running/pr_open/merged/failed)
  - After each phase: send summary to Telegram (if configured)
  - Track total: PRs opened, PRs merged, issues closed, lines changed

skill.md manifest:
  name: repo-master
  description: Master orchestrator. Runs all 6 skills in the correct order across 6 phases. Tracks progress, enforces gates, waits for PR approvals between phases.
  triggers: ["run full improvement", "start master plan", "improve everything", "full repo upgrade"]
```

---

## Step 4: Launch It

### Prompt 10: Kick Off the Full Run

```
I've installed OpenClaw with 7 skills pointed at the BD-Automation-Engine repo:
  - repo-auditor
  - code-improver
  - data-organizer
  - pipeline-builder
  - infra-upgrader
  - bd-enrichment
  - repo-master

Start Phase 1: Run the repo-auditor skill.

Create a branch: openclaw/full-audit
Scan the entire BD-Automation-Engine codebase.
Create GitHub issues for every finding.
Write the full audit report to outputs/audit/audit_report.md.
Ping me on Telegram when done so I can review before you proceed to Phase 2.
```

---

## What You'll See

After the full 6-phase run, your repo will have:

| Before | After |
|--------|-------|
| 82 dead code issues | Clean imports, no dead variables |
| Duplicate crawl4ai in requirements | Split prod/dev deps with lock file |
| 3 copies of Qdrant data (3.3GB) | Single Docker volume, server mode only |
| 7 SQLite files with overlap | Consolidated DBs with Alembic migrations |
| 5 Federal Programs CSVs | 1 canonical + archived versions |
| CI that never fails (|| true) | CI that actually enforces tests + types |
| No auth on API | API key auth on write endpoints |
| Pattern engine with mock data | Pattern engine querying real Qdrant data |
| Swarm workers returning empty arrays | Working executors calling real API endpoints |
| Memory lost on restart | 3-tier memory persisted in Qdrant |
| Scattered data directories | Clean data/ structure with documentation |
| No monitoring | Prometheus metrics + Grafana dashboard |
| No CRM database | Unified CRM with ETL from Bullhorn + Qdrant |
| No relationship graph | Neo4j with scored relationships |

**~25 PRs total, each reviewable independently, nothing lands without your approval.**
