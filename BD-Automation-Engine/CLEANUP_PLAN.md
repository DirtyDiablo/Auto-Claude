# BD-Automation-Engine — Dead Code Cleanup Plan

**Phase 1 (Quick Cleanup) | Generated 2026-02-16**
**Based on:** AUDIT_REPORT.md findings + Ruff static analysis

---

## Ruff Analysis Summary

```
Total errors found: 7,887
  - F401 (unused imports):        32
  - F841 (unused variables):      75
  - ERA001 (commented-out code):  41
  - F821 (undefined names):        7
  - E722 (bare except):            6
  - UP006/UP045/UP035 (type hints): 6,820
  - I001 (unsorted imports):      785
  - Other style issues:           121
```

---

## SAFE TO DELETE (High Confidence 90%+)

### Files to Delete

| File | Size | Reason |
|------|------|--------|
| `data/bullhorn_master.db` | 293 MB | DUPLICATE — canonical copy at `Engine7_BullhornETL/data/bullhorn_master.db` |
| `data/bd_graph.db` | 804 KB | DUPLICATE — canonical copy at `Engine8_Knowledge/data/bd_graph.db` |
| `data/memories.db` | 40 KB | DUPLICATE — canonical copy at `Engine8_Knowledge/data/memories.db` |
| `data/page_index.db` | 24 KB | DUPLICATE — canonical copy at `Engine8_Knowledge/data/page_index.db` |
| `Engine7_BullhornETL/data/bullhorn.db` | 0 bytes | EMPTY file — never populated |
| `design_intelligence/component_library.py` | 655 lines | React/Tailwind component generator — no frontend exists in this repo |
| `design_intelligence/design_system.py` | 577 lines | Design system generator — no frontend consumes it |
| `design_intelligence/__init__.py` | — | Directory becomes empty after above removals |
| `Engine8_Knowledge/scripts/lancedb_hybrid.py` | 330 lines | LanceDB not used elsewhere; Qdrant is the primary vector store |
| `Engine7_BullhornETL/scripts/bullhorn_etl.py` | 913 lines | V1 ETL superseded by `bullhorn_etl_v2.py` — V2 is imported by `run_pipeline.py` |

### Unused Imports (F401) — Auto-fixable

| File:Line | Import | Reason |
|-----------|--------|--------|
| `Engine4_Briefing/scripts/briefing_generator.py:4` | `import json` | Never used in file |
| `Engine4_Briefing/scripts/briefing_generator.py:7` | `typing.Optional` | Never used in file |
| `Engine7_BullhornETL/scripts/bullhorn_activity_logger.py:24` | `import json` | Never used in file |
| `Engine8_Knowledge/scripts/claim_tracker.py:23` | `datetime.timedelta` | Never used in file |
| `Engine8_Knowledge/scripts/claim_tracker.py:24` | `typing.Optional` | Never used in file |
| `Engine8_Knowledge/scripts/daily_action_engine.py:16` | `datetime.timedelta` | Never used in file |
| `config/settings.py:18` | `typing.Optional` | Never used (Pydantic v2 uses `X | None`) |
| `design_intelligence/component_library.py:9` | `.design_system.ColorPalette` | Never used |
| `design_intelligence/design_system.py:12` | `typing.Optional` | Never used |
| `mcp/knowledge-mcp-server/server.py:27` | `typing.Optional` | Never used |
| `models/activities.py:2` | `pydantic.BaseModel` | Unused — inherits from `BaseDocument` |
| `models/contacts.py:2` | `pydantic.BaseModel` | Unused — inherits from `BaseDocument` |
| `models/jobs.py:2` | `pydantic.BaseModel` | Unused — inherits from `BaseDocument` |
| `models/programs.py:2` | `pydantic.BaseModel` | Unused — inherits from `BaseDocument` |
| `orchestrator.py:30` | `typing.Any` | Never used |
| `orchestrator.py:30` | `typing.Callable` | Never used |
| `quickstart.py:18` | `datetime.datetime` | Never used |
| `reindex_with_openai.py:29` | `qdrant_client.models.ScrollRequest` | Never used |
| `scripts/architecture/consolidate.py:160` | `.name_map.assign_category` | Never used |
| `scripts/architecture/html_emitter.py:14` | `.name_map.PROJECT_LABELS` | Never used |
| `scripts/architecture/html_emitter.py:14` | `.name_map.assign_category` | Never used |
| `engine_data/Engine2_ProgramMapping/enrich-federal-programs-v3.py:15` | `import json` | Never used |
| `engine_data/Engine2_ProgramMapping/enrich-federal-programs-v3.py:19` | `import time` | Never used |
| `engine_data/Engine2_ProgramMapping/enrich-federal-programs-v3.py:21` | `typing.Any` | Never used |
| `engine_data/Engine2_ProgramMapping/enrich-federal-programs-v3.py:22` | `datetime.datetime` | Never used |
| `engine_data/Engine2_ProgramMapping/enrich-federal-programs-v3.py:30` | `PyPDF2` | Imported but unused |

### Unused Variables (F841) — Safe to Remove

**Exception handler variables (`except Exception as e` where `e` unused) — 22 instances, auto-fixable:**

| File:Line | Variable |
|-----------|----------|
| `Engine2_ProgramMapping/scripts/pipeline.py:289` | `e` |
| `Engine7_BullhornETL/scripts/bullhorn_etl.py:582,626,659,691,727` | `e` (5 instances) |
| `Engine7_BullhornETL/scripts/bullhorn_etl_v2.py:204,818,849,872,889` | `e` (5 instances) |
| `Engine8_Knowledge/agents/bd_strategy_agent.py:26` | `e` |
| `Engine8_Knowledge/agents/company_research_agent.py:25` | `e` |
| `Engine8_Knowledge/agents/program_intel_agent.py:26` | `e` |
| `Engine8_Knowledge/api.py:1592,1607` | `e` (2 instances) |
| `Engine8_Knowledge/bd_lightrag/graph_rag.py:398` | `e` |
| `Engine8_Knowledge/ragflow/document_preprocessor.py:707` | `e` |
| `Engine8_Knowledge/scripts/index_staged_data.py:139` | `e` |
| `Engine8_Knowledge/scripts/lancedb_hybrid.py:195` | `e` |
| `services/ai_enrichment/run_dcgs_enrichment.py:109` | `e` |
| `services/ai_enrichment/run_dcgs_retry.py:118` | `e` |

**Dead assigned variables — require manual review before removal:**

| File:Line | Variable | Context |
|-----------|----------|---------|
| `Engine0_Orchestrator/orchestrator.py:280` | `std_dir` | Path computed but never used |
| `Engine2_ProgramMapping/scripts/enrich_insight_global_jobs.py:436` | `fp_name` | Loop variable extracted but unused |
| `Engine2_ProgramMapping/scripts/enrich_insight_global_jobs.py:438` | `fp_keywords` | Loop variable extracted but unused |
| `Engine2_ProgramMapping/scripts/enrich_insight_global_jobs.py:439` | `fp_roles` | Loop variable extracted but unused |
| `Engine2_ProgramMapping/scripts/enrich_insight_global_jobs.py:441` | `fp_prime` | Loop variable extracted but unused |
| `Engine2_ProgramMapping/scripts/enrich_insight_global_jobs.py:563` | `programs` | List comprehension result unused |
| `Engine2_ProgramMapping/scripts/generate_bd_playbook.py:528` | `total_contacts` | Computed value never printed/returned |
| `Engine7_BullhornETL/scripts/ingest_new_notes.py:280` | `existing_fields` | Schema check result unused |
| `Engine8_Knowledge/ragflow/bd_knowledge_manager.py:627` | `sections` | Parsed sections never used |
| `Engine8_Knowledge/retrieval/page_index.py:344` | `prompt` | Built prompt never sent |
| `Engine8_Knowledge/scripts/claim_tracker.py:233` | `content` | Extracted content unused |
| `Engine8_Knowledge/workflows/production/pipeline_manager.py:112` | `horizon` | Config value unused |
| `orchestrator.py:578` | `pipeline_config` | Config dict built but unused |
| `scripts/data_correlation/correlation_engine.py:1069` | `location_by_id` | Dict built but never queried |
| `scripts/generate_pipeline_report.py:58` | `target_companies` | List built but unused |
| `scripts/generate_pipeline_report.py:439,440` | `header_font`, `border` | Style objects unused |
| `services/bullhorn_integration.py:67` | `auth_params` | Auth dict built but unused |
| `services/bullhorn_integration.py:80` | `token_data` | Token response unused |
| `index_contacts.py:110` | `last_progress_time` | Timing var unused |

### Commented-Out Code (ERA001) — 41 Instances

| File | Lines | Description |
|------|-------|-------------|
| `Engine8_Knowledge/agents/test_agents.py` | 286-287 | Commented test calls |
| `Engine8_Knowledge/api.py` | 389-390, 3131 | Disabled Supermemory router + comment block |
| `Engine8_Knowledge/graph/bd_knowledge_graph.py` | 468, 473, 479, 485 | Commented graph query code |
| `Engine8_Knowledge/retrieval/ultra_rag_integration.py` | 82-93, 105-106, 132-133 | 13 lines of commented imports and code |
| `Engine8_Knowledge/retrieval/page_index.py` | 355 | Commented retrieval logic |
| `Engine8_Knowledge/scripts/enrich_reindex_all.py` | 225 | Commented reindex step |
| `Engine8_Knowledge/scripts/rag_router.py` | 46, 117 | Commented router paths |
| `Engine8_Knowledge/search/unified_search.py` | 217 | Commented search fallback |
| `scripts/architecture/html_emitter.py` | 199 | Commented HTML generation |
| `scripts/architecture/infrastructure_merger.py` | 169 | Commented merge logic |
| `scripts/architecture/property_standardizer.py` | 10 | Commented import |
| `scripts/job_ingestion/hiring_leader_lookup.py` | 334 | Commented lookup logic |
| `scripts/job_ingestion/job_parser.py` | 256 | Commented parser code |
| `services/bullhorn_integration.py` | 89 | Commented API call |
| `src/auth/auth_service.py` | 465 | Commented auth code |
| `src/data_quality/rules_dsl.py` | 175 | Commented rule |
| `src/embeddings/synthetic_data_generator.py` | 266, 297, 359, 426, 461 | 5 commented generation blocks |
| `src/knowledge/temporal_kg.py` | 277 | Commented knowledge graph code |

---

## NEEDS REVIEW (Medium Confidence 70-89%)

### Files That Look Dead But May Be Dynamically Used

| File | Lines | Concern |
|------|-------|---------|
| `Engine8_Knowledge/scripts/populate_lightrag.py` | 364 | LightRAG experimental system — might be referenced by config or manual runs |
| `Engine8_Knowledge/scripts/lightrag_engine.py` | 209 | Companion to populate_lightrag — check if any CLI or config references it |
| `Engine8_Knowledge/scripts/docling_extractor.py` | 231 | Docling document extraction — might be used by file_watcher or manual pipeline |
| `Engine8_Knowledge/scripts/docling_processor.py` | 125 | Docling processing — companion to extractor |
| `Engine8_Knowledge/scripts/treesitter_parser.py` | 409 | Code parsing — possibly used for codebase analysis features |
| `Engine8_Knowledge/scripts/recompete_predictor.py` | 548 | ML model for contract recompete — no trained model found but logic exists |
| `Engine8_Knowledge/scripts/classifier_pipeline.py` | 790 | ML classifier — no trained model but referenced by some scripts |
| `services/graphiti_service.py` | 115 | Graphiti knowledge graph — no active Neo4j config, but Graphiti is in requirements |
| `config/resilience.py` | 62 | Retry/circuit breaker patterns — defined but never imported elsewhere |
| `scripts/test_phase4_agents.py` | 433 | Test file in wrong directory — may still contain useful test patterns |
| `dify_integration/` (entire directory, 5 files) | 2,465 | Dify bridges — no evidence Dify is deployed, but kept as integration option |
| `scripts/verify_pipeline.py:42-56` | — | Imports 8 agent classes + orchestrator for existence check only — legitimate but flagged |

### Undefined Name References (F821)

| File:Line | Name | Concern |
|-----------|------|---------|
| `Engine8_Knowledge/graph/ingestion.py:73` | `Neo4jManager` | Forward reference — class defined elsewhere, may work at runtime |
| `Engine8_Knowledge/graph/queries.py:17` | `Neo4jManager` | Forward reference — same pattern |
| `Engine8_Knowledge/graph/schema.py:171,236` | `Neo4jManager` | Forward reference — same pattern |
| `Engine8_Knowledge/search/benchmark_v2.py:161,166` | `UnifiedSearch` | Forward reference — lazy import on line 168 |
| `src/embeddings/benchmark_suite.py:290` | `random` | Missing `import random` — will crash at runtime |

---

## FRAMEWORK FALSE POSITIVES (Keep)

These are flagged by static analysis but are legitimately used at runtime:

### FastAPI Route Decorators
All `@app.get()`, `@app.post()`, `@router.get()` handler functions in:
- `simple_knowledge_api.py` — 17 endpoint handlers
- `Engine8_Knowledge/api.py` — additional endpoints
- `dify_integration/dify_n8n_bridge.py` — Dify router endpoints

### APScheduler Job Functions
- `services/scheduler.py` — functions registered as jobs by name string

### Dynamic Imports in verify_pipeline.py
- `scripts/verify_pipeline.py:42-56` — imports Engine8 agents purely to test importability; flagged as F401 but this IS the test

### Pydantic Model Fields
- `models/*.py` — Field definitions appear "unused" but are consumed by Pydantic serialization

### BaseDocument Inheritance
- `models/activities.py`, `contacts.py`, `jobs.py`, `programs.py` — import `BaseModel` alongside `BaseDocument`. The `BaseModel` import is technically unused since they inherit from `BaseDocument(BaseModel)`, but removing it won't break anything (safe to clean).

---

## DUPLICATE CODE BLOCKS

### 1. Program Mapper (Keep Engine2, Remove Engine7 copy)
- **Keep:** `Engine2_ProgramMapping/scripts/program_mapper.py` (1,001 lines) — canonical, full-featured, multi-signal matching
- **Remove/Merge:** `Engine7_BullhornETL/scripts/program_mapper.py` (400 lines) — Bullhorn-specific subset
- **Reason:** Engine2 version has 2.5x more code and is the pipeline's canonical mapper. Engine7 version duplicates core logic with Bullhorn-specific data loading. Refactor Engine7 to import from Engine2.

### 2. Contact Classification (Keep Both — Different Purposes)
- **Keep:** `Engine3_OrgChart/scripts/contact_classifier.py` (363 lines) — regex-based, fast, deterministic
- **Keep:** `Engine7_BullhornETL/scripts/intelligent_contact_classifier.py` (754 lines) — AI-powered, richer but slower
- **Action:** Add clear docstring to each explaining when to use which. Long-term: merge into one with a `mode` parameter.

### 3. Contact Scoring (Keep Engine5, Remove Engine7 copy)
- **Keep:** `Engine5_Scoring/scripts/bd_scoring.py` (582 lines) — canonical scoring with 4-tier system
- **Remove/Merge:** `Engine7_BullhornETL/scripts/contact_scoring.py` (382 lines) — Bullhorn-specific scoring
- **Reason:** Engine5 is the designated scoring engine. Engine7 should import from Engine5.

### 4. BD Playbook Generator (Keep Engine4, Remove scripts/ copy)
- **Keep:** `Engine4_Playbook/scripts/bd_playbook_generator.py` (915 lines) — full playbook with email/call/talking points
- **Remove:** `scripts/bd_playbook_generator.py` (493 lines) — appears to be an older/simpler version
- **Reason:** Engine4 version is more complete (915 vs 493 lines) and is in the canonical engine directory.

### 5. Master Indexing (Keep index_all_data.py, Remove master_index_all.py)
- **Keep:** `Engine8_Knowledge/scripts/index_all_data.py` (922 lines) — comprehensive indexing coordinator
- **Remove:** `Engine8_Knowledge/scripts/master_index_all.py` (87 lines) — thin wrapper that calls index_all_data
- **Reason:** master_index_all.py is a 87-line wrapper with no unique logic.

### 6. Reindexing (Keep enrich_reindex_all.py, Review reindex_batch.py)
- **Keep:** `Engine8_Knowledge/scripts/enrich_reindex_all.py` (1,183 lines) — full reindex with enrichment
- **Review:** `Engine8_Knowledge/scripts/reindex_batch.py` (111 lines) — batch-oriented subset
- **Action:** Check if reindex_batch.py adds batch-size control not in enrich_reindex_all. If not, remove.

### 7. Orchestrators (Merge into one)
- **Keep:** `orchestrator.py` (976 lines) — 11-stage master orchestrator
- **Remove/Merge:** `Engine0_Orchestrator/orchestrator.py` (320 lines) — 8-step controller
- **Reason:** Root orchestrator is more complete. Engine0 version appears to be an earlier iteration.

---

## CLEANUP COMMANDS

### Step 1: Auto-fix unused imports and variables (safe)
```bash
ruff check . --fix --select F401,F841 --exclude=".auto-claude,node_modules,.git,.venv,data"
```

### Step 2: Remove commented-out code (review diff after)
```bash
ruff check . --fix --select ERA001 --exclude=".auto-claude,node_modules,.git,.venv,data" --unsafe-fixes
```

### Step 3: Format all Python files
```bash
ruff format . --exclude=".auto-claude,node_modules,.git,.venv,data"
```

### Step 4: Delete duplicate database files
```bash
rm data/bullhorn_master.db
rm data/bd_graph.db
rm data/memories.db
rm data/page_index.db
rm Engine7_BullhornETL/data/bullhorn.db
```

### Step 5: Delete dead code files
```bash
# V1 ETL superseded by V2
rm Engine7_BullhornETL/scripts/bullhorn_etl.py

# LanceDB alternative (Qdrant is primary)
rm Engine8_Knowledge/scripts/lancedb_hybrid.py

# Design intelligence (no frontend)
rm -rf design_intelligence/

# Duplicate playbook generator
rm scripts/bd_playbook_generator.py

# Thin wrapper (index_all_data.py is canonical)
rm Engine8_Knowledge/scripts/master_index_all.py
```

### Step 6: Merge duplicate orchestrators
```bash
# Remove Engine0 (root orchestrator.py is canonical)
rm -rf Engine0_Orchestrator/
```

### Step 7: Verify nothing breaks
```bash
python -c "
import sys; sys.path.insert(0, '.')
from models.base import BaseDocument
from models.contacts import Contact
from models.programs import FederalProgram
from models.jobs import ScrapedJob
from models.activities import Activity
from config.settings import get_settings
print('Core models and config: OK')
"

# Run existing tests
pytest tests/ -v
```

---

## ESTIMATED IMPACT

| Metric | Count |
|--------|-------|
| **Files to delete** | 12 (5 duplicate DBs + 7 Python files + 1 directory) |
| **Duplicate DB storage recovered** | ~294 MB |
| **Python lines eliminated** | ~3,568 (bullhorn_etl.py 913 + design_intelligence 1,232 + lancedb_hybrid 330 + bd_playbook_generator scripts 493 + master_index_all 87 + Engine0 orchestrator 320 + misc unused code ~193) |
| **Unused imports removed** | 32 |
| **Unused variables cleaned** | 75 |
| **Commented-out code removed** | 41 blocks |
| **Ruff errors fixed** | ~148 (F401 + F841 + ERA001) |
| **Estimated codebase reduction** | ~5.7% of Python LOC |
| **Disk space freed** | ~294 MB (duplicate databases) |

### What This Does NOT Touch
- No active engine logic is modified
- No API endpoints are removed
- No data files (CSV/JSON) are deleted
- No N8N workflows are removed (those are Phase 3: LangGraph migration)
- No Dify integration is removed yet (flagged as NEEDS REVIEW)
- No LightRAG/Docling files are removed yet (flagged as NEEDS REVIEW)

---

## EXECUTION LOG

**Executed: 2026-02-16**
**Branch: `cleanup/dead-code-removal`**

### Step 1: Created branch
```
git checkout -b cleanup/dead-code-removal
```

### Step 2: Ruff auto-fix (F401 + F841)
```
ruff check . --fix --select F401,F841 --exclude=".auto-claude,node_modules,.git,.venv,data"
```
**Result:** 49 errors auto-fixed (27 unused imports removed, 22 `except Exception as e` → `except Exception`).
**Remaining:** 59 F841 (assigned-but-unused variables in loops/tests — need `--unsafe-fixes` or manual review).

### Step 3: ERA001 (commented-out code)
**Decision: SKIPPED auto-fix.** Ruff flagged 41 ERA001 instances, but manual review showed most are legitimate section header comments (e.g., `# Pattern: "Who works on <program>?"` above pattern-matching code, `# STRATEGY: ENTITY-CENTRIC` section dividers). Auto-removing would delete useful documentation.

### Step 4: Ruff format
```
ruff format . --exclude=".auto-claude,node_modules,.git,.venv,data"
```
**Result:** 628 files reformatted, 53 unchanged.

### Step 5: Deleted duplicate databases (5 files, ~294 MB)
- `data/bullhorn_master.db` (293 MB) — duplicate of `Engine7_BullhornETL/data/bullhorn_master.db`
- `data/bd_graph.db` (804 KB) — duplicate of `Engine8_Knowledge/data/bd_graph.db`
- `data/memories.db` (40 KB) — duplicate of `Engine8_Knowledge/data/memories.db`
- `data/page_index.db` (24 KB) — duplicate of `Engine8_Knowledge/data/page_index.db`
- `Engine7_BullhornETL/data/bullhorn.db` (0 bytes) — empty file

### Step 6: Deleted dead Python files and directories
- `Engine7_BullhornETL/scripts/bullhorn_etl.py` (913 lines) — V1 superseded by V2
- `Engine8_Knowledge/scripts/lancedb_hybrid.py` (330 lines) — LanceDB not primary
- `scripts/bd_playbook_generator.py` (493 lines) — duplicate of Engine4 version
- `Engine8_Knowledge/scripts/master_index_all.py` (87 lines) — thin wrapper
- `design_intelligence/` directory (2 files, 1,232 lines) — no frontend to consume
- `Engine0_Orchestrator/` directory (1 file, 320 lines) — root orchestrator.py is canonical

### Step 7: Verification
- **Core imports:** models, config, Engine 2/3/5/7/8 all importable ✅
- **Test suite:** 44 passed, 3 skipped, 0 failures ✅

### Post-Cleanup Ruff Stats
```
Before: 148 errors (F401: 32, F841: 75, ERA001: 41)
After:   99 errors (F401: 6, F841: 52, ERA001: 41)
Fixed:   49 errors
```

### Summary of What Was Done
| Action | Count |
|--------|-------|
| Files deleted | 10 (5 DBs + 5 Python files) |
| Directories deleted | 2 (design_intelligence/, Engine0_Orchestrator/) |
| Unused imports auto-removed | 27 |
| Exception variables auto-cleaned | 22 |
| Files reformatted (ruff format) | 628 |
| Disk space freed | ~294 MB |
| Python LOC eliminated | ~3,375 |
| Tests broken | 0 |

### What Was NOT Done (deferred)
- ERA001 commented-out code: Kept (most are section headers, not dead code)
- 52 remaining F841 unused variables: Need manual review (loop vars, test side-effects)
- 6 remaining F401 imports: In `verify_pipeline.py` (import-for-existence-check pattern)
- NEEDS REVIEW items: LightRAG, Docling, Dify, Graphiti — left for human decision
- DUPLICATE CODE merges: program_mapper, scoring, contact_classifier — left for refactor phase
