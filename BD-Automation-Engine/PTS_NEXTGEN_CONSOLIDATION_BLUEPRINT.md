# PTS Next-Gen Consolidation Blueprint
## Research-to-Implementation: Skills Mapping + Autonomous Prompt Sequences

**Date:** February 16, 2026  
**Source:** "The definitive toolkit for AI-powered codebase consolidation in 2026"  
**Goal:** Map every research conclusion to installed antigravity skills, then generate copy-paste prompt sequences that run autonomously in each Claude Code terminal to audit, plan, and execute the 3→1 repo unification.

---

## PART 1: RESEARCH SECTION → SKILLS MAPPING

Each research section's conclusions are mapped to the specific skills installed in `.claude/skills/` that Claude Code will invoke during autonomous execution.

---

### Section 1: AI Codebase Analysis (Multi-Repo Understanding)

**Conclusion:** Use Claude Code with CLAUDE.md context mesh across repos. Feed Repomix output for comprehensive file-by-file analysis.

**Applicable Skills (18):**

| Skill | Category | Role in This Section |
|---|---|---|
| `architecture` | architecture | Architectural decision-making framework, ADR documentation |
| `software-architecture` | architecture | Quality-focused architecture analysis |
| `senior-architect` | data-ai | Comprehensive system design across React, Next, Node, FastAPI |
| `architect-review` | architecture | Reviews system designs, identifies flaws |
| `docs-architect` | architecture | Creates technical documentation from existing codebases |
| `wiki-architect` | architecture | Analyzes repos, generates hierarchical documentation |
| `c4-architecture-c4-architecture` | architecture | Bottom-up C4 architecture documentation generation |
| `c4-context` | architecture | High-level system context diagrams |
| `c4-component` | architecture | Component-level architecture mapping |
| `c4-container` | infrastructure | Container-level deployment mapping |
| `c4-code` | architecture | Code-level documentation with function signatures |
| `production-code-audit` | architecture | Deep-scan entire codebase line-by-line |
| `claude-code-guide` | general | Master guide for using Claude Code effectively |
| `brainstorming` | architecture | Pre-work skill for creative/constructive architecture decisions |
| `context-fundamentals` | general | Understanding context in agent systems |
| `context-manager` | data-ai | Dynamic context management, knowledge graphs |
| `mermaid-expert` | workflow | Flowcharts, sequences, ERDs, architecture diagrams |
| `pts-arch-migration` | PTS custom | 3→2 repo consolidation context |

---

### Section 2: Agentic Autonomous Refactoring

**Conclusion:** Claude Code sub-agents for parallel work. Checkpoint/rewind for safe rollback. One change → test → commit discipline.

**Applicable Skills (14):**

| Skill | Category | Role in This Section |
|---|---|---|
| `parallel-agents` | architecture | Multi-agent orchestration for independent tasks |
| `multi-agent-patterns` | architecture | Orchestrator, peer-to-peer, hierarchical patterns |
| `autonomous-agents` | data-ai | Decompose goals, plan actions, self-correct |
| `autonomous-agent-patterns` | data-ai | Tool integration, permission systems, human-in-the-loop |
| `agent-orchestration-multi-agent-optimize` | workflow | Coordinated profiling, workload distribution |
| `dispatching-parallel-agents` | general | 2+ independent tasks without shared state |
| `subagent-driven-development` | general | Executing plans with independent tasks |
| `executing-plans` | general | Written implementation plan execution with checkpoints |
| `planning-with-files` | general | Manus-style file-based planning for complex tasks |
| `concise-planning` | general | Clear, actionable, atomic checklists |
| `plan-writing` | general | Structured task planning with dependencies |
| `writing-plans` | general | Spec/requirements before touching code |
| `verification-before-completion` | general | Running verification commands before claiming done |
| `git-advanced-workflows` | general | Rebasing, cherry-picking, bisect, worktrees, reflog |

---

### Section 3: Dead Code Detection (Static Analysis + AI)

**Conclusion:** Layer Vulture (global unused) + deadcode (orphaned files) + Ruff (local unused) + jscpd (duplicates). Run in sequence.

**Applicable Skills (12):**

| Skill | Category | Role in This Section |
|---|---|---|
| `lint-and-validate` | general | Automatic quality control, linting, static analysis |
| `clean-code` | general | Clean Code principles for review and refactoring |
| `code-review-checklist` | security | Comprehensive review covering functionality, security, perf |
| `code-review-excellence` | general | Constructive feedback, catch bugs early |
| `code-refactoring-refactor-clean` | architecture | Clean code principles, SOLID design patterns |
| `codebase-cleanup-refactor-clean` | architecture | Same as above, codebase-wide scope |
| `codebase-cleanup-tech-debt` | general | Identify, quantify, prioritize technical debt |
| `code-refactoring-tech-debt` | general | Technical debt identification in software projects |
| `legacy-modernizer` | general | Refactor legacy codebases, gradual modernization |
| `production-code-audit` | architecture | Autonomous deep-scan, transform to production-grade |
| `find-bugs` | security | Find bugs, security vulns, code quality issues in changes |
| `error-detective` | architecture | Search logs/codebases for error patterns, root causes |

---

### Section 4: Codebase Indexing & Architecture Mapping

**Conclusion:** Repomix → Claude Code file descriptions → pydeps import graphs → pyreverse Pydantic UML → OpenAPI extraction → Neo4j schema → Mermaid architecture diagrams.

**Applicable Skills (16):**

| Skill | Category | Role in This Section |
|---|---|---|
| `docs-architect` | architecture | Technical documentation from existing codebases |
| `wiki-architect` | architecture | Hierarchical documentation with onboarding guides |
| `wiki-researcher` | security | Deep research on specific codebase topics |
| `wiki-page-writer` | general | Rich technical docs with Mermaid diagrams |
| `api-documentation-generator` | development | Generate API docs from code |
| `api-documenter` | data-ai | OpenAPI 3.1, interactive docs, SDK generation |
| `openapi-spec-generation` | security | Generate/maintain OpenAPI 3.1 specifications |
| `documentation-templates` | data-ai | README, API docs, code comments, AI-friendly docs |
| `documentation-generation-doc-generate` | data-ai | Comprehensive documentation from code |
| `code-documentation-doc-generate` | data-ai | API docs, architecture diagrams, user guides |
| `code-documentation-code-explain` | general | Explain complex code through narratives, diagrams |
| `mermaid-expert` | workflow | All diagram types (flowcharts, ERDs, sequences) |
| `claude-d3js-skill` | infrastructure | Interactive data visualizations |
| `reference-builder` | development | Exhaustive technical references, API documentation |
| `pydantic-models-py` | data-ai | Multi-model pattern (Base, Create, Update, Response) |
| `graphql` | data-ai | Schema-first API design (for comparison with REST) |

---

### Section 5: Folder Reorganization (rope + AI Strategy)

**Conclusion:** AI proposes target structure → human reviews → rope executes mechanical moves → AI handles complex transforms → pydeps validates.

**Applicable Skills (14):**

| Skill | Category | Role in This Section |
|---|---|---|
| `architecture-patterns` | development | Clean Architecture, Hexagonal, DDD |
| `software-architecture` | architecture | Quality-focused architecture guidance |
| `monorepo-architect` | architecture | Nx, Turborepo, Bazel, Lerna (concepts apply to uv) |
| `monorepo-management` | general | Turborepo, Nx, pnpm workspaces patterns |
| `framework-migration-legacy-modernize` | business | Strangler fig pattern, gradual replacement |
| `framework-migration-code-migrate` | general | Transitioning codebases between frameworks |
| `framework-migration-deps-upgrade` | security | Safe, incremental dependency upgrades |
| `python-packaging` | development | Proper project structure, pyproject.toml, publishing |
| `uv-package-manager` | development | Fast Python dependency management, virtual envs |
| `code-refactoring-refactor-clean` | architecture | SOLID design patterns refactoring |
| `python-patterns` | development | Framework selection, async patterns, project structure |
| `python-pro` | development | Python 3.12+, modern features, ecosystem |
| `backend-dev-guidelines` | development | Layered architecture, BaseController pattern |
| `pts-arch-migration` | PTS custom | 3→2 repo migration rules and sequence |

---

### Section 6: Monorepo Unification (uv Workspaces)

**Conclusion:** uv workspaces with single lockfile. git-filter-repo for history preservation. Una for distributable wheels. Target structure: services/ + libs/ + infra/.

**Applicable Skills (10):**

| Skill | Category | Role in This Section |
|---|---|---|
| `monorepo-architect` | architecture | Multi-project architecture at scale |
| `monorepo-management` | general | Workspace management patterns |
| `uv-package-manager` | development | uv dependency management and virtual environments |
| `python-packaging` | development | pyproject.toml, package structure |
| `environment-setup-guide` | general | Development environment setup |
| `docker-expert` | security | Multi-stage builds, image optimization, Compose |
| `deployment-procedures` | infrastructure | Safe deployment workflows, rollback strategies |
| `git-advanced-workflows` | general | History rewriting, filter-repo concepts |
| `using-git-worktrees` | general | Isolated git worktrees for feature work |
| `pts-arch-migration` | PTS custom | Repo consolidation sequence and rules |

---

### Section 7: Database Standardization (Repository Pattern)

**Conclusion:** Repository Pattern with abstract interfaces per entity. neomodel for Neo4j OGM. qdrant-client wrappers. Canonical Pydantic models in libs/db-layer/. dependency-injector for FastAPI wiring.

**Applicable Skills (20):**

| Skill | Category | Role in This Section |
|---|---|---|
| `database-architect` | data-ai | Data layer design, technology selection, schema modeling |
| `database-design` | data-ai | Schema design, indexing, ORM selection |
| `database-migration` | security | Zero-downtime migrations, data transformation, rollback |
| `database-optimizer` | infrastructure | Performance tuning, query optimization |
| `database-admin` | security | Cloud databases, automation, reliability engineering |
| `postgres-best-practices` | data-ai | Supabase-aligned PostgreSQL optimization |
| `postgresql` | data-ai | PostgreSQL-specific schema, indexing, constraints |
| `nosql-expert` | general | Distributed NoSQL (Cassandra, DynamoDB patterns apply) |
| `vector-database-engineer` | data-ai | Pinecone, Weaviate, Qdrant, Milvus, pgvector |
| `vector-index-tuning` | data-ai | HNSW parameters, quantization, scaling |
| `similarity-search-patterns` | data-ai | Efficient similarity search with vector DBs |
| `embedding-strategies` | data-ai | Select/optimize embedding models for RAG |
| `sql-optimization-patterns` | data-ai | Query optimization, indexing, EXPLAIN analysis |
| `sql-pro` | infrastructure | Cloud-native databases, OLTP/OLAP, query techniques |
| `pydantic-models-py` | data-ai | Canonical Pydantic schemas (Base/Create/Update/Response) |
| `fastapi-pro` | development | Async APIs with SQLAlchemy 2.0 and Pydantic V2 |
| `fastapi-templates` | development | Production-ready FastAPI with dependency injection |
| `fastapi-router-py` | development | CRUD routers with auth dependencies |
| `architecture-patterns` | development | Clean Architecture, Hexagonal, DDD |
| `cqrs-implementation` | architecture | Command Query Responsibility Segregation |

---

### Section 8: Ruff & Code Quality Stack

**Conclusion:** Ruff replaces Black+isort+flake8. pyproject.toml config with select rules. pre-commit hooks for enforcement. Pyright or ty for type checking.

**Applicable Skills (10):**

| Skill | Category | Role in This Section |
|---|---|---|
| `lint-and-validate` | general | Automatic linting and static analysis |
| `clean-code` | general | Clean Code principles |
| `code-review-checklist` | security | Comprehensive review checklist |
| `python-pro` | development | Modern Python 3.12+ ecosystem |
| `python-patterns` | development | Type hints, project structure |
| `python-testing-patterns` | development | pytest, fixtures, mocking, TDD |
| `test-driven-development` | testing | TDD before writing implementation |
| `tdd-workflow` | testing | RED-GREEN-REFACTOR cycle |
| `cc-skill-coding-standards` | development | Universal coding standards |
| `systematic-debugging` | testing | Before proposing fixes |

---

### Section 9: Phased Consolidation Methodology (Phases 0-5)

**Conclusion:** Phase 0=Assessment, 1=Cleanup, 2=Monorepo merge, 3=Extract shared libs, 4=Standardize patterns, 5=Ongoing quality. Golden rule: software must work at every point.

**Applicable Skills (22):**

| Skill | Category | Role in This Section |
|---|---|---|
| `concise-planning` | general | Actionable, atomic checklists |
| `plan-writing` | general | Structured planning with dependencies |
| `writing-plans` | general | Spec/requirements before code |
| `executing-plans` | general | Execute plans with review checkpoints |
| `planning-with-files` | general | File-based planning (task_plan.md, findings.md) |
| `brainstorming` | architecture | Pre-work for creative/constructive decisions |
| `multi-agent-brainstorming` | security | Sequential multi-agent review for confidence |
| `doc-coauthoring` | architecture | Structured documentation co-authoring |
| `production-code-audit` | architecture | Autonomous deep-scan codebase |
| `codebase-cleanup-tech-debt` | general | Identify/quantify technical debt |
| `legacy-modernizer` | general | Gradual modernization, technical debt |
| `framework-migration-legacy-modernize` | business | Strangler fig pattern |
| `deployment-procedures` | infrastructure | Safe deployment, rollback, verification |
| `deployment-engineer` | security | CI/CD pipelines, GitOps, automation |
| `github-actions-templates` | infrastructure | Production-ready CI/CD workflows |
| `github-automation` | infrastructure | Repository, issue, PR automation |
| `docker-expert` | security | Containerization for unified deployment |
| `observability-engineer` | security | Monitoring, logging, tracing |
| `test-driven-development` | testing | TDD at every phase |
| `python-testing-patterns` | development | pytest across all services |
| `e2e-testing-patterns` | infrastructure | Playwright/Cypress for dashboard |
| `security-auditor` | security | DevSecOps, compliance frameworks |

---

### Cross-Cutting: PTS-Specific Skills (Always Active)

These provide the federal BD context that makes every other skill PTS-aware:

| Skill | Role |
|---|---|
| `PTS_PLATFORM_CONTEXT.md` | Mission, architecture, priorities, tech stack |
| `PTS_BD_ENGINE_CONTEXT.md` | 8-engine pipeline, Bullhorn, Neo4j |
| `PTS_N8N_BUILDER_CONTEXT.md` | LangGraph workflows, federal APIs |
| `PTS_DATA_SCRAPER_CONTEXT.md` | Scraping, classification, program mapping |
| `pts-bd-pipeline` | 8-engine scoring and quality gates |
| `pts-federal-intel` | SAM.gov/FPDS/USASpending/Tango |
| `pts-contact-ops` | Bullhorn CRM, 6-tier hierarchy, HUMINT |
| `pts-arch-migration` | Migration sequence and rules |

---

### Full Skill Count by Research Section

| Research Section | Skills Mapped | Primary Categories |
|---|---|---|
| 1. AI Codebase Analysis | 18 | architecture, data-ai, general |
| 2. Agentic Refactoring | 14 | architecture, data-ai, general |
| 3. Dead Code Detection | 12 | general, architecture, security |
| 4. Codebase Indexing | 16 | architecture, data-ai, general |
| 5. Folder Reorganization | 14 | architecture, development, general |
| 6. Monorepo Unification | 10 | architecture, development, infrastructure |
| 7. Database Standardization | 20 | data-ai, development, infrastructure |
| 8. Code Quality (Ruff) | 10 | general, development, testing |
| 9. Phased Methodology | 22 | general, architecture, security, infrastructure |
| Cross-Cutting PTS Context | 8 | PTS custom |
| **TOTAL UNIQUE SKILLS** | **~105** | **Across all 9 categories** |

---

## PART 2: AUTONOMOUS PROMPT SEQUENCE

### How This Works

1. Drop the `nextgenresearchanalysis.md` into each project's `.claude/` directory
2. Run each prompt below sequentially in the Claude Code terminal for that project
3. Each prompt produces an artifact (audit report, plan, or code changes)
4. The output of each prompt feeds context to the next
5. After all 3 projects complete their per-repo phases, a final unification prompt merges them

### Pre-Setup (Run Once Per Project)

```bash
# Copy the research doc into the project
cp ~/path/to/nextgenresearchanalysis.md .claude/NEXTGEN_RESEARCH.md
```

---

### PROMPT 1: COMPREHENSIVE PROJECT AUDIT
**Run in: All 3 terminals (BD-Automation-Engine, N8N-Builder, Data-Scraper)**
**Skills triggered:** @production-code-audit @architecture @docs-architect @wiki-architect @c4-architecture-c4-architecture @pts-arch-migration

```
Read .claude/NEXTGEN_RESEARCH.md and .claude/skills/PTS_PLATFORM_CONTEXT.md completely.

You are conducting Phase 0 (Assessment) from the research document for THIS specific repository.

Perform a comprehensive autonomous audit of this entire codebase. Produce a single markdown file called AUDIT_REPORT.md in the project root with these exact sections:

## 1. FILE INVENTORY
- Total files, lines of code, languages
- Every Python file with a 1-line description of its purpose
- Identify orphaned files (imported by nothing)
- Identify duplicate/near-duplicate files

## 2. ARCHITECTURE MAP
- Draw a Mermaid diagram of the module dependency graph
- List every FastAPI router/endpoint with HTTP method and path
- List every database connection (Neo4j, Qdrant, SQLite, PostgreSQL, any)
- List every external API integration (SAM.gov, FPDS, USASpending, Tango, Bullhorn, Slack, etc.)
- List every scheduled task (APScheduler, cron, etc.)

## 3. DATA MODEL INVENTORY
- Every Pydantic model with fields and which files use it
- Every SQLite table with columns
- Every Neo4j node type and relationship type
- Every Qdrant collection with vector dimensions and count
- Identify duplicate/conflicting data models across files

## 4. DEPENDENCY AUDIT
- Parse pyproject.toml / requirements.txt
- List every dependency with version
- Flag deprecated packages (especially py2neo)
- Flag unused dependencies (imported nowhere)
- Flag version conflicts

## 5. DEAD CODE CANDIDATES
- Functions/classes defined but never called from outside their file
- Files that are never imported
- Commented-out code blocks
- Empty or stub files
- Estimate: what percentage of the codebase is dead weight?

## 6. CROSS-REPO INTEGRATION POINTS
- Which modules in THIS repo call APIs from the other 2 repos?
- Which data formats are shared between repos?
- Which databases are accessed by multiple repos?
- Port numbers, URLs, and connection strings used

## 7. TEST COVERAGE
- Existing test files and what they cover
- Estimated coverage percentage
- Critical paths with ZERO test coverage

## 8. TECHNICAL DEBT SCORECARD
Rate each area 1-5 (1=critical debt, 5=clean):
- Code organization and module structure
- Dependency management
- Error handling patterns
- Logging and observability
- Configuration management
- Security (secrets, auth, input validation)
- Documentation
- Type annotations

## 9. CONSOLIDATION READINESS ASSESSMENT
Based on the research document's recommended monorepo structure:
- What from this repo maps to services/bd-automation (or n8n-builder or data-scraper)?
- What should be extracted to libs/shared-core/?
- What should be extracted to libs/db-layer/?
- What should be extracted to libs/bullhorn-client/?
- What should be extracted to libs/slack-utils/?
- What can be deleted outright?
- What blocking issues must be resolved first?

Save as AUDIT_REPORT.md in the project root. Be exhaustive. Use actual file paths and function names from the codebase.
```

---

### PROMPT 2: DEAD CODE CLEANUP PLAN
**Run in: All 3 terminals**
**Skills triggered:** @lint-and-validate @clean-code @codebase-cleanup-tech-debt @codebase-cleanup-refactor-clean @find-bugs

```
Read AUDIT_REPORT.md and .claude/NEXTGEN_RESEARCH.md.

You are executing Phase 1 (Quick Cleanup) from the research document.

Based on the dead code candidates and technical debt identified in the audit:

1. INSTALL AND RUN the following tools on this codebase (install with pip if needed):
   - ruff check . --statistics (report what ruff finds)
   - ruff check . --select F401,F841,ERA001 --statistics (unused imports, vars, commented code)

2. DO NOT auto-fix yet. First, produce CLEANUP_PLAN.md with:

## SAFE TO DELETE (High Confidence 90%+)
List every file, function, class, import that is definitely dead:
- [file:line] description of what it is and why it's dead

## NEEDS REVIEW (Medium Confidence 70-89%)
Things that look dead but might be called dynamically:
- [file:line] description and why it's uncertain

## FRAMEWORK FALSE POSITIVES (Keep)
Things that static tools flag but are actually used:
- FastAPI route decorators
- APScheduler job functions
- CrewAI agent definitions
- Signal/callback handlers

## DUPLICATE CODE BLOCKS
Pairs of files/functions that do the same thing:
- [file1:lines] vs [file2:lines] — which to keep and why

## CLEANUP COMMANDS
The exact sequence of commands to run:
```
ruff check . --fix --select F401,F841,ERA001
ruff format .
# Then manual deletions listed above
```

## ESTIMATED IMPACT
- Files to delete: X
- Functions to remove: X
- Lines of code eliminated: X
- Estimated codebase reduction: X%

Save as CLEANUP_PLAN.md. Do not execute any deletions yet.
```

---

### PROMPT 3: EXECUTE CLEANUP
**Run in: All 3 terminals**
**Skills triggered:** @lint-and-validate @python-pro @git-advanced-workflows @verification-before-completion

```
Read CLEANUP_PLAN.md.

Execute the cleanup in this exact sequence:

1. Create a new git branch: git checkout -b cleanup/dead-code-removal
2. Run: ruff check . --fix --select F401,F841,ERA001
3. Run: ruff format .
4. Delete all files listed under "SAFE TO DELETE" in CLEANUP_PLAN.md
5. Remove all functions/classes listed under "SAFE TO DELETE"
6. After each batch of deletions, run: python -c "import importlib; print('imports OK')" on key modules to verify nothing breaks
7. Run any existing tests: pytest (if tests exist) or python -m pytest
8. Git commit with message: "chore: remove dead code identified by vulture/ruff audit"

Report what was deleted and any issues encountered. Update CLEANUP_PLAN.md with a "## EXECUTION LOG" section at the bottom documenting what was done.
```

---

### PROMPT 4: SHARED LIBRARY EXTRACTION PLAN
**Run in: All 3 terminals**
**Skills triggered:** @architecture-patterns @database-architect @database-design @pydantic-models-py @fastapi-pro @fastapi-templates @monorepo-architect @pts-arch-migration

```
Read AUDIT_REPORT.md and .claude/NEXTGEN_RESEARCH.md (sections on Repository Pattern and monorepo structure).

You are preparing Phase 3 (Extract Shared Libraries) from the research document.

Analyze this codebase and produce SHARED_LIBRARY_PLAN.md identifying everything that should be extracted into shared packages. For each item, show the CURRENT location and the TARGET location in the unified monorepo.

## libs/shared-core/ (Common FastAPI, config, logging)
For each item list:
- Current file path and function/class name
- What it does
- Which other files in THIS repo depend on it
- Target path in libs/shared-core/

Categories to extract:
- FastAPI app factory / middleware / error handlers
- Configuration management (env vars, settings classes)
- Logging setup
- Common utilities (date formatting, string helpers, etc.)
- Base Pydantic models (pagination, error responses, etc.)

## libs/db-layer/ (Repository Pattern: Neo4j, Qdrant, Supabase)
For each item list:
- Current file path
- Database it connects to
- Connection pattern used (direct client, session, pool)
- Target abstract interface name
- Target concrete implementation name

Map to the Repository Pattern from the research:
```python
class EntityRepository(ABC):
    async def get_by_id(self, id: str) -> Entity: ...
    async def search(self, query: str) -> list[Entity]: ...
    async def create(self, entity: EntityCreate) -> Entity: ...
    async def update(self, id: str, entity: EntityUpdate) -> Entity: ...
    async def delete(self, id: str) -> bool: ...
```

## libs/bullhorn-client/ (Bullhorn CRM integration)
- Every file that touches Bullhorn API
- Auth flow implementation
- CRUD operations
- Custom field handling
- What should become the unified BullhornClient class

## libs/slack-utils/ (Shared Slack utilities)
- Every file that uses slack_sdk
- Notification patterns
- Channel management
- What should become shared utilities

## CANONICAL PYDANTIC MODELS
List every Pydantic model in this repo that represents a shared domain entity:
- Contact, Job, Program, Contract, Organization, etc.
- Show field conflicts between different versions of the same model
- Propose the canonical version with all fields

## DEPENDENCY INJECTION PLAN
How FastAPI routes in this repo should be rewired to use injected repositories instead of direct database calls:
- Current: from db import get_neo4j_session; session.run(...)
- Target: def route(repo: ContactRepo = Depends(get_contact_repo)): ...

Save as SHARED_LIBRARY_PLAN.md.
```

---

### PROMPT 5: API SURFACE CONSOLIDATION PLAN
**Run in: All 3 terminals**
**Skills triggered:** @api-design-principles @api-documentation-generator @api-patterns @fastapi-pro @fastapi-router-py @openapi-spec-generation @senior-architect

```
Read AUDIT_REPORT.md and .claude/NEXTGEN_RESEARCH.md.

You are planning the API consolidation from 3 FastAPI servers to 1 unified server.

Produce API_CONSOLIDATION_PLAN.md:

## CURRENT API SURFACE
List every FastAPI route in this project:
- HTTP method + path
- Handler function name and file location
- Request model (if any)
- Response model (if any)
- Auth requirements
- Which database(s) it touches

## ROUTER ORGANIZATION
Group all routes into logical domain routers for the unified server:
- /api/v1/contacts/* — Contact CRUD and search
- /api/v1/programs/* — Federal program operations
- /api/v1/jobs/* — Job posting operations
- /api/v1/contracts/* — Contract intelligence
- /api/v1/scraping/* — Scraper management
- /api/v1/enrichment/* — Data enrichment pipeline
- /api/v1/outreach/* — Campaign and outreach
- /api/v1/reports/* — Report generation
- /api/v1/workflows/* — LangGraph workflow triggers
- /api/v1/health/* — Health checks and system status
- /api/v1/admin/* — Admin operations
- /api/v1/webhooks/* — Inbound webhook handlers

For each route, show: current path → new unified path

## BREAKING CHANGES
- Routes that would change paths
- Response format differences between repos
- Auth mechanism differences
- How to handle with deprecation headers and redirect period

## OPENAPI SPEC DRAFT
Generate a partial OpenAPI 3.1 YAML for the routes from THIS repo, showing how they'd look in the unified server schema.

Save as API_CONSOLIDATION_PLAN.md.
```

---

### PROMPT 6: DATABASE MIGRATION PLAN
**Run in: All 3 terminals**
**Skills triggered:** @database-architect @database-design @database-migration @postgres-best-practices @postgresql @vector-database-engineer @vector-index-tuning @embedding-strategies @nosql-expert @sql-optimization-patterns @pts-arch-migration

```
Read AUDIT_REPORT.md, SHARED_LIBRARY_PLAN.md, and .claude/NEXTGEN_RESEARCH.md (Database Standardization section).

Produce DATABASE_MIGRATION_PLAN.md for this specific repository:

## CURRENT STATE
For every database in this repo:
- Type (SQLite, Neo4j, Qdrant, PostgreSQL, other)
- File path of database or connection config
- Tables/collections/node types with row/record counts (estimate from code)
- Size on disk (if local file)
- Which modules read from it
- Which modules write to it

## SQLITE → SUPABASE MIGRATION
For each SQLite database:
- Current schema (CREATE TABLE statements or equivalent)
- Proposed Supabase PostgreSQL table with column types
- Data transformation rules (any column type changes)
- JSONB columns for flexible fields
- Indexes needed
- Row-level security policies needed
- Migration script outline (Python: read SQLite → insert Supabase)

## NEO4J STANDARDIZATION
- Current Neo4j usage patterns (raw Cypher? py2neo? neomodel?)
- Proposed neomodel StructuredNode classes for each node type
- Relationship definitions
- Index and constraint declarations
- Migration from current driver to neomodel

## QDRANT → PGVECTOR MIGRATION
- Current Qdrant collections with vector dimensions
- Embedding model used (Voyage, OpenAI, other)
- Proposed pgvector table structure
- Index type (IVFFlat vs HNSW) and parameters
- Migration script outline (scroll Qdrant → insert pgvector)

## REPOSITORY PATTERN IMPLEMENTATION
For each database entity in this repo, define:
```python
# Abstract interface
class [Entity]Repository(ABC):
    # list all methods this repo needs

# Concrete implementation
class Supabase[Entity]Repo([Entity]Repository):
    # Supabase/PostgreSQL implementation

class Neo4j[Entity]Repo([Entity]Repository):
    # neomodel implementation (if still needed)
```

## MIGRATION SEQUENCE
Ordered steps with rollback capability:
1. Create Supabase tables (schema only)
2. Implement new Repository classes alongside old code
3. Migrate data (background job)
4. Switch reads to new repos (feature flag)
5. Switch writes to new repos (feature flag)
6. Verify data integrity
7. Remove old database code
8. Drop old SQLite files

Save as DATABASE_MIGRATION_PLAN.md.
```

---

### PROMPT 7: LANGGRAPH WORKFLOW MIGRATION
**Run in: N8N-Builder terminal (primary), reference from others**
**Skills triggered:** @langgraph @langchain-architecture @workflow-automation @workflow-orchestration-patterns @autonomous-agent-patterns @agent-memory-mcp @agent-memory-systems @parallel-agents @crewai @pts-bd-pipeline

```
Read AUDIT_REPORT.md and .claude/NEXTGEN_RESEARCH.md.

This is the N8N-to-LangGraph migration plan. Analyze every workflow, scheduled task, and orchestration pattern in this codebase.

Produce LANGGRAPH_MIGRATION_PLAN.md:

## CURRENT WORKFLOWS
For every orchestrated process in this repo:
- Name and description
- Trigger (scheduled, API call, webhook, manual)
- Steps in sequence
- Data flow between steps
- Error handling pattern
- Current implementation (N8N, APScheduler, manual, other)

## LANGGRAPH STATE DEFINITIONS
For each workflow, define the TypedDict state:
```python
class [Workflow]State(TypedDict):
    # All fields needed across the workflow
```

## LANGGRAPH NODE DEFINITIONS
For each workflow step:
```python
def [step_name](state: [Workflow]State) -> [Workflow]State:
    """What this node does"""
    # Key logic outline
    return {"field": updated_value}
```

## LANGGRAPH GRAPH DEFINITIONS
For each workflow:
```python
graph = StateGraph([Workflow]State)
graph.add_node("[step1]", step1_fn)
graph.add_node("[step2]", step2_fn)
graph.add_edge("[step1]", "[step2]")
# Conditional edges for branching
graph.add_conditional_edges("[step2]", should_continue, {...})
```

## APSCHEDULER INTEGRATION
How each scheduled workflow integrates with APScheduler:
```python
scheduler.add_job(
    workflow_graph.invoke,
    trigger=CronTrigger(hour=6, minute=0),  # Daily 6 AM
    args=[initial_state],
    id="daily_bd_pipeline"
)
```

## CREWAI AGENT MIGRATION
If CrewAI agents exist:
- Current agent definitions
- How they map to LangGraph nodes or sub-graphs
- Which should remain as CrewAI vs become pure LangGraph

## UNIFIED ORCHESTRATOR
The single orchestrator that coordinates all workflows:
- Master scheduler configuration
- Workflow dependency graph (which must run before which)
- Error recovery and retry policies
- Monitoring and alerting integration

Save as LANGGRAPH_MIGRATION_PLAN.md.
```

---

### PROMPT 8: CI/CD AND QUALITY PIPELINE
**Run in: All 3 terminals**
**Skills triggered:** @github-actions-templates @github-automation @docker-expert @deployment-engineer @deployment-procedures @observability-engineer @security-auditor @secrets-management @e2e-testing-patterns @test-driven-development

```
Read AUDIT_REPORT.md and .claude/NEXTGEN_RESEARCH.md (Ruff section and Phase 5).

Produce CICD_QUALITY_PLAN.md:

## PYPROJECT.TOML STANDARDIZATION
Generate the complete pyproject.toml for this project including:
- [project] metadata
- [tool.ruff] config (line-length=88, target-version="py312")
- [tool.ruff.lint] select rules (E, F, I, B, UP, S, ERA, PL, RUF)
- [tool.ruff.lint.per-file-ignores] for test files
- [tool.vulture] config (min_confidence=80, ignore_decorators)
- [tool.pytest.ini_options]
- [tool.mypy] or [tool.pyright] config

## PRE-COMMIT CONFIG
Generate .pre-commit-config.yaml with:
- ruff (lint + format)
- vulture
- mypy or pyright
- detect-secrets
- check-yaml, check-toml, check-json

## GITHUB ACTIONS WORKFLOWS
Generate workflow YAML files for:

### .github/workflows/ci.yml
- Trigger: push to main, PR to main
- Steps: checkout, setup Python 3.12, install uv, install deps, ruff check, ruff format --check, vulture, pytest, mypy

### .github/workflows/security.yml
- Trigger: weekly + PR
- Steps: pip-audit, bandit (via ruff S rules), detect-secrets

### .github/workflows/deploy.yml
- Trigger: tag push (v*)
- Steps: build Docker image, push to registry, deploy to Railway

## DOCKERFILE
Generate a multi-stage Dockerfile:
- Stage 1: builder (uv install)
- Stage 2: runtime (minimal image, non-root user)
- Health check endpoint
- Proper .dockerignore

## MONITORING AND OBSERVABILITY
- Structured logging format (JSON)
- Health check endpoint spec
- Key metrics to expose
- Error alerting rules (Slack notifications)

Save as CICD_QUALITY_PLAN.md and also create the actual config files:
- pyproject.toml (update existing or create)
- .pre-commit-config.yaml
- .github/workflows/ci.yml
- .github/workflows/security.yml
- Dockerfile (update existing or create)
- .dockerignore
```

---

### PROMPT 9: IMPLEMENTATION PRIORITY MATRIX
**Run in: All 3 terminals**
**Skills triggered:** @concise-planning @plan-writing @executing-plans @pts-arch-migration @brainstorming

```
Read ALL plan files created so far:
- AUDIT_REPORT.md
- CLEANUP_PLAN.md
- SHARED_LIBRARY_PLAN.md
- API_CONSOLIDATION_PLAN.md
- DATABASE_MIGRATION_PLAN.md
- LANGGRAPH_MIGRATION_PLAN.md (if exists in this repo)
- CICD_QUALITY_PLAN.md

Synthesize everything into IMPLEMENTATION_ROADMAP.md:

## PRIORITY MATRIX
Rank every planned change by:
- Revenue Impact (does this enable daily call lists faster?)
- Risk Level (what breaks if this goes wrong?)
- Effort (hours/days estimate)
- Dependencies (what must happen first?)

Score each: CRITICAL / HIGH / MEDIUM / LOW

## PHASE 0: IMMEDIATE (This Week)
Changes that can be done RIGHT NOW with zero risk:
- Ruff formatting
- Dead code removal (high confidence only)
- pyproject.toml standardization
- pre-commit hooks
- CI/CD pipeline setup
List exact commands and files to modify.

## PHASE 1: FOUNDATION (Week 2-3)
Shared library extraction and Repository Pattern:
- Extract libs/shared-core/
- Extract libs/db-layer/ with abstract interfaces
- Extract libs/bullhorn-client/
- Wire up dependency injection
List the exact file moves and new files to create.

## PHASE 2: DATABASE (Week 3-4)
Database consolidation:
- Create Supabase tables
- Implement new Repository classes
- Migrate data
- Feature-flag switchover
List the exact migration scripts needed.

## PHASE 3: ORCHESTRATION (Week 4-5)
LangGraph and workflow unification:
- Convert remaining N8N workflows
- Implement unified scheduler
- Set up monitoring
List the exact LangGraph graphs to build.

## PHASE 4: API UNIFICATION (Week 5-6)
Server consolidation:
- Create unified FastAPI server
- Migrate routes with deprecation headers
- Update all clients
List the exact router files to create.

## PHASE 5: MONOREPO MERGE (Week 6-7)
Final unification:
- git-filter-repo history preservation
- uv workspace setup
- Unified Docker build
- Final integration testing

## BLOCKERS AND RISKS
- What could derail each phase
- Mitigation strategies
- Rollback procedures

## SUCCESS METRICS
How to verify each phase succeeded:
- All existing tests pass
- API responses unchanged
- Data integrity verified
- Performance benchmarks met
- Daily call list output identical

Save as IMPLEMENTATION_ROADMAP.md.
```

---

### PROMPT 10: UNIFICATION MERGE (Run AFTER all 3 repos complete Prompts 1-9)
**Run in: A NEW terminal or the BD-Automation-Engine terminal**
**Skills triggered:** @monorepo-architect @monorepo-management @uv-package-manager @docker-expert @git-advanced-workflows @pts-arch-migration

```
You are performing the final unification of 3 repositories into 1 monorepo.

Read the IMPLEMENTATION_ROADMAP.md from each of the 3 repos. The target structure is:

unified-platform/
├── pyproject.toml              # Root workspace config with uv
├── uv.lock                     # Single lockfile
├── services/
│   ├── bd-automation/          # From BD-Automation-Engine
│   ├── n8n-builder/            # From N8N-Builder
│   └── data-scraper/           # From Data-Scraper
├── libs/
│   ├── shared-core/            # Common FastAPI, config, logging
│   ├── db-layer/               # Repository pattern implementations
│   ├── bullhorn-client/        # Bullhorn CRM unified client
│   └── slack-utils/            # Shared Slack utilities
├── infra/
│   ├── docker/                 # Per-service Dockerfiles
│   ├── docker-compose.yml      # Local dev stack
│   └── railway/                # Railway deployment configs
├── .github/workflows/          # Unified CI/CD
├── CLAUDE.md                   # Unified context for Claude Code
└── ARCHITECTURE.md             # Living architecture document

Execute:

1. Create the unified-platform directory structure
2. Generate the root pyproject.toml with uv workspace config:
   [tool.uv.workspace]
   members = ["services/*", "libs/*"]
3. Generate each libs/ package:
   - libs/shared-core/pyproject.toml + src/
   - libs/db-layer/pyproject.toml + src/
   - libs/bullhorn-client/pyproject.toml + src/
   - libs/slack-utils/pyproject.toml + src/
4. Generate the unified CLAUDE.md combining all PTS context
5. Generate ARCHITECTURE.md documenting the unified system
6. Generate docker-compose.yml for local development
7. Generate unified .github/workflows/ CI/CD
8. Create the git commands needed to merge histories:
   git filter-repo commands for each repo
   git merge --allow-unrelated-histories commands

Produce all files and a MERGE_EXECUTION_SCRIPT.sh with the exact git commands to run.
```

---

## PART 3: EXECUTION SEQUENCE SUMMARY

```
┌─────────────────────────────────────────────────────┐
│              EXECUTION FLOW                          │
├─────────────────────────────────────────────────────┤
│                                                      │
│  BD-Engine    N8N-Builder    Data-Scraper            │
│     │              │              │                   │
│     ▼              ▼              ▼                   │
│  Prompt 1      Prompt 1      Prompt 1   (Audit)      │
│     │              │              │                   │
│     ▼              ▼              ▼                   │
│  Prompt 2      Prompt 2      Prompt 2   (Cleanup)    │
│     │              │              │                   │
│     ▼              ▼              ▼                   │
│  Prompt 3      Prompt 3      Prompt 3   (Execute)    │
│     │              │              │                   │
│     ▼              ▼              ▼                   │
│  Prompt 4      Prompt 4      Prompt 4   (Shared Lib) │
│     │              │              │                   │
│     ▼              ▼              ▼                   │
│  Prompt 5      Prompt 5      Prompt 5   (API Plan)   │
│     │              │              │                   │
│     ▼              ▼              ▼                   │
│  Prompt 6      Prompt 6      Prompt 6   (DB Plan)    │
│     │              │              │                   │
│     ▼              ▼              ▼                   │
│  Prompt 7      Prompt 7      Prompt 7   (LangGraph)  │
│     │              │              │                   │
│     ▼              ▼              ▼                   │
│  Prompt 8      Prompt 8      Prompt 8   (CI/CD)      │
│     │              │              │                   │
│     ▼              ▼              ▼                   │
│  Prompt 9      Prompt 9      Prompt 9   (Roadmap)    │
│     │              │              │                   │
│     └──────────────┼──────────────┘                   │
│                    ▼                                  │
│              Prompt 10           (Unify)              │
│                    │                                  │
│                    ▼                                  │
│           unified-platform/                           │
│           (Single Monorepo)                           │
└─────────────────────────────────────────────────────┘
```

### Artifacts Produced Per Repo (Prompts 1-9):
1. `AUDIT_REPORT.md` — Full codebase audit
2. `CLEANUP_PLAN.md` — Dead code removal plan
3. (Executed cleanup with git commit)
4. `SHARED_LIBRARY_PLAN.md` — Extraction targets for libs/
5. `API_CONSOLIDATION_PLAN.md` — Route mapping to unified server
6. `DATABASE_MIGRATION_PLAN.md` — SQLite→Supabase, Neo4j→neomodel, Qdrant→pgvector
7. `LANGGRAPH_MIGRATION_PLAN.md` — Workflow conversion
8. `CICD_QUALITY_PLAN.md` + actual config files
9. `IMPLEMENTATION_ROADMAP.md` — Prioritized execution plan

### Final Unification (Prompt 10):
- `unified-platform/` directory structure
- Root `pyproject.toml` with uv workspaces
- All `libs/` packages scaffolded
- Unified `CLAUDE.md` and `ARCHITECTURE.md`
- `docker-compose.yml` for local dev
- `MERGE_EXECUTION_SCRIPT.sh` for git history preservation

---

*Generated February 16, 2026 for PTS BD Intelligence Platform*  
*105 unique skills mapped across 9 research sections*  
*10 autonomous prompts producing 9 artifacts per repo + unified monorepo scaffold*
