# PTS DATA ARCHITECTURE EXTRACTION SYSTEM
## Complete Package Summary

**Generated:** 2026-02-12  
**Version:** Final v3 Preparation  
**Target Output:** Interactive Cytoscape.js Architecture Explorer  

---

## 🎯 MISSION

Extract complete data architecture from three PTS projects (BD-Automation-Engine, Data-Scraper, N8N-Builder) into standardized JSON schema files, then merge into a unified interactive visualization showing:

- **50+ Entities** (Contacts, Programs, Jobs, Contractors, API Responses, etc.)
- **700+ Properties** (Fields with types, sources, examples)
- **100+ Relationships** (WORKS_FOR, HAS_CLEARANCE, MATCHES_TO, etc.)
- **400+ Aliases** (Field name variations across systems)
- **20+ Data Flows** (Complete pipeline traces)

---

## 📦 DELIVERABLES

### Six Documents Created

#### 1. **MASTER_ARCHITECTURE_EXTRACTION_GUIDE.md** (START HERE)
The orchestration document. Explains:
- What's been extracted in prior session (20 known node types, 35+ relationships)
- What's missing (critical gaps in each project)
- How to run three terminals in parallel
- How to merge outputs into V3 explorer
- Quality checks and success criteria

**Key sections:**
- Executive summary (what we have/need)
- Critical vs. High vs. Medium priority items
- Timeline and workflow
- Merge process for final output

---

#### 2. **EXTRACT_BD_ENGINE.md** (For Terminal 1)
Detailed extraction script for the BD-Automation-Engine project.

**Focus areas:**
- Qdrant vector collections (12, 1.42M vectors) → Payload schemas
- Bullhorn SQLite database (306MB) → Complete table schemas  
- Dashboard JSON feeds (25 files) → Field lists
- FastAPI endpoints (152+) → Request/response models
- Dashboard TypeScript (14-page React) → Interface definitions
- Engine pipeline stages (Engines 1-8) → I/O schemas
- AI agents (15+) → Input/output definitions
- LangGraph workflows → State definitions

**Scope:** 4,221 files, 8 engines, 1.42M vectors  
**Time estimate:** 30-45 minutes  
**Output:** `data_architecture_bd_engine.json`

---

#### 3. **EXTRACT_DATA_SCRAPER.md** (For Terminal 2)
Detailed extraction script for the Data-Scraper project.

**Focus areas:**
- Tango API SQL schemas (11 files) → Federal procurement data model
- Pydantic models (models/ — 3 files) → Core data definitions
- Scraper output schema → 64-column enriched job structure
- Federal API responses → USASpending, FPDS, SAM.gov shapes
- src/ domain models (33 domains × ~10 files) → Complete model inventory
- Hub client sync → BD-Engine integration schema
- BD target databases (7 databases) → Column lists
- Knowledge base → Manifest and folder structure

**Scope:** 2,018 files, 14 web scrapers, 33 capability domains  
**Time estimate:** 30-45 minutes  
**Output:** `data_architecture_data_scraper.json`

---

#### 4. **EXTRACT_N8N_BUILDER.md** (For Terminal 3)
Detailed extraction script for the N8N-Builder project.

**Focus areas:**
- N8N workflow JSON files (50+ workflows) → Node definitions
- API integration nodes → Bullhorn, Notion, ZoomInfo, Apify calls
- Contact enrichment workflow → Final output schema
- Code node transformations → Data transformation logic
- Notion database operations → CRUD patterns, field mappings
- Webhook triggers → Event payload schemas
- API integration patterns → Auth, request/response mapping
- Data flow diagrams → Node connections

**Scope:** ~800 files, 50+ workflows, contact enrichment pipelines  
**Time estimate:** 20-30 minutes  
**Output:** `data_architecture_n8n_builder.json`

---

#### 5. **TERMINAL_QUICK_REFERENCE.md**
Quick reference cards for each terminal.

**Contains:**
- Quick commands to extract key data
- Critical vs. High vs. Medium checklist for each project
- Common troubleshooting
- Success criteria
- General extraction workflow (4 phases)

**Use this:** During extraction when you need to remember what to get

---

#### 6. **EXTRACTION_PROGRESS_TRACKER.md**
Templates to track extraction progress for all three terminals.

**Contains:**
- Checkbox templates for each terminal
- Statistics tracking
- New discoveries section
- Final consolidation checklist
- Submission quality checks

**Use this:** To mark progress as you extract from each project

---

## 🚀 HOW TO USE THIS PACKAGE

### Step 1: Read the Master Guide (5 minutes)
Start with `MASTER_ARCHITECTURE_EXTRACTION_GUIDE.md` to understand:
- What's already known (20 entities, 35+ relationships from prior session)
- What gaps exist (10 critical items per project)
- Overall workflow and timeline
- Expected output format

### Step 2: Set Up Three Terminals
Open three separate Claude Desktop windows:
1. Terminal 1 → Navigate to `bd-automation-engine/`
2. Terminal 2 → Navigate to `data-scraper/`
3. Terminal 3 → Navigate to `n8n-builder/`

### Step 3: Run Terminal 1 (BD-Automation-Engine)
1. Load `EXTRACT_BD_ENGINE.md` into Terminal 1
2. Follow the extraction steps in order
3. Use `TERMINAL_QUICK_REFERENCE.md` for quick commands
4. Track progress with `EXTRACTION_PROGRESS_TRACKER.md`
5. Save output: `data_architecture_bd_engine.json`

### Step 4: Run Terminal 2 (Data-Scraper)
1. Load `EXTRACT_DATA_SCRAPER.md` into Terminal 2
2. Follow the extraction steps
3. Complete progress tracker
4. Save output: `data_architecture_data_scraper.json`

### Step 5: Run Terminal 3 (N8N-Builder)
1. Load `EXTRACT_N8N_BUILDER.md` into Terminal 3
2. Follow the extraction steps
3. Complete progress tracker
4. Save output: `data_architecture_n8n_builder.json`

### Step 6: Merge All Three
Once all three JSON files are created:
1. Use merge script from Master Guide
2. Output: `data_architecture_merged_v3.json`
3. Update Cytoscape.js explorer with merged JSON
4. Verify visualization renders correctly

---

## 📊 EXPECTED OUTPUT

### Three JSON Files (one per terminal)

#### BD-Automation-Engine Output
```json
{
  "project_id": "BD_ENGINE",
  "scan_date": "2026-02-12",
  "scan_stats": {
    "files_scanned": "4,221",
    "entities_found": "15-20",
    "properties_found": "250-300",
    "relationships_found": "30-40",
    "aliases_found": "100+"
  },
  "entities": [...],
  "relationships": [...],
  "databases": {
    "qdrant_collections": [12 collections with payload schemas],
    "sqlite_tables": [all Bullhorn tables with columns],
    "dashboard_feeds": [25 JSON feeds with field lists],
    "api_endpoints": [152+ FastAPI endpoints]
  }
}
```

#### Data-Scraper Output
```json
{
  "project_id": "DATA_SCRAPER",
  "scan_date": "2026-02-12",
  "scan_stats": {
    "files_scanned": "2,018",
    "entities_found": "15-20",
    "properties_found": "250-300",
    "relationships_found": "20-30"
  },
  "entities": [...],
  "tango_sql_schemas": [11 CREATE TABLE statements],
  "scraper_outputs": [64-column enriched job schema],
  "federal_api_shapes": {
    "tango": {...},
    "usaspending": {...},
    "fpds": {...},
    "sam_gov": {...}
  }
}
```

#### N8N-Builder Output
```json
{
  "project_id": "N8N_BUILDER",
  "scan_date": "2026-02-12",
  "scan_stats": {
    "workflows_found": "50+",
    "nodes_found": "200+",
    "api_integrations": "20+"
  },
  "workflows": [
    {
      "name": "workflow_name",
      "nodes": [...],
      "data_flow": "description",
      "output_schema": {...}
    }
  ],
  "contact_enrichment_output": [enriched contact field list],
  "notion_database_operations": [...],
  "webhooks": [...]
}
```

### Final Merged Explorer
- **Entities:** 50+ total
- **Properties:** 700+
- **Relationships:** 100+
- **Aliases:** 400+
- **Data flows:** 20+
- **Visualization:** Interactive Cytoscape.js graph

---

## 🎓 KEY LEARNINGS FROM PRIOR WORK

From the prior session (`__prompt_response_before_stoppingMASTER_PROPERTY_ARCHITECTURE_SCHE.txt`), we already have:

### 20 Known Node Types
1. CONTACT (36 properties)
2. PROGRAM (90+ properties)
3. JOB (60+ properties)
4. CONTRACTOR (30+ properties)
5. LOCATION (15+ properties)
6. CALL_NOTE (20+ properties)
7. PLACEMENT (18+ properties)
8. TECHNOLOGY (8 properties)
9. CLEARANCE_LEVEL (10 properties)
10. OPPORTUNITY (15+ properties)
11. CONTRACT_VEHICLE (12 properties)
12. AGENCY (10 properties)
13. TEAM (8 properties)
14. SKILL (7 properties)
15. ENTITY (8 properties)
16. PAST_PERFORMANCE (15+ properties)
17. BRIEFING (10 properties)
18. GAP_ANALYSIS (12 properties)
19. NOTIFICATION (8 properties)
20. MEMORY (7 properties)

### 35+ Known Relationship Types
WORKS_FOR, WORKS_AT, MEMBER_OF, WORKS_ON, REPORTS_TO, KNOWS, MANAGES, HIRED_FOR, PLACED_IN, HAS_CLEARANCE, HAS_SKILL, FAMILIAR_WITH, DECISION_MAKER_FOR, INTERVIEWER_FOR, MENTIONED_IN, PRIMED_BY, SUBCONTRACTED_TO, OWNED_BY, LOCATED_AT, USES_VEHICLE, HAS_JOB, HAS_CONTACT, REQUIRES_SKILL, REQUIRES_TECHNOLOGY, REQUIRES_CLEARANCE, RELATED_TO, HAS_PAST_PERFORMANCE, MATCHED_TO, POSTED_BY, ASSIGNED_TO, HAS_BRIEFING, FILLED_BY, APPLIED_BY, PRIMES, EMPLOYS, OFFICES_AT, ABOUT, DISCUSSES, MENTIONS, REFERENCES, CREATED_BY

**DO NOT RE-EXTRACT THESE** — Just verify they exist in code and add any missing properties.

---

## ⏱️ TIMELINE

| Phase | Activity | Duration | Deliverable |
|-------|----------|----------|------------|
| **Phase 1** | Read MASTER guide | 5 min | Understanding |
| **Phase 2** | Run Terminal 1 (BD-Engine) | 30-45 min | `data_architecture_bd_engine.json` |
| **Phase 3** | Run Terminal 2 (Data-Scraper) | 30-45 min | `data_architecture_data_scraper.json` |
| **Phase 4** | Run Terminal 3 (N8N-Builder) | 20-30 min | `data_architecture_n8n_builder.json` |
| **Phase 5** | Merge all 3 | 10 min | `data_architecture_merged_v3.json` |
| **Phase 6** | Update explorer | 5-10 min | V3 visualization live |

**Total time estimate:** 2-3 hours for complete extraction + merge

---

## ✅ SUCCESS CRITERIA

When all 3 terminals complete successfully:

- ✅ Three separate JSON files created with no errors
- ✅ All required fields populated in each JSON
- ✅ Statistics make sense (entities, properties, relationships counts)
- ✅ New discoveries documented
- ✅ Merge produces single consolidated V3 JSON
- ✅ Cytoscape.js explorer renders with all entities
- ✅ Relationships display correctly on graph
- ✅ Filters and search working
- ✅ Color coding applied by category
- ✅ Zoom/pan functionality working

---

## 📋 QUICK CHECKLIST BEFORE STARTING

- [ ] All 6 documents downloaded/saved locally
- [ ] Three project directories accessible
- [ ] Understand the 20 known node types (listed above)
- [ ] Understand the workflow: extract → merge → visualize
- [ ] Have Python available (for merge script)
- [ ] Have JSON validator ready (for format checking)
- [ ] Time blocked for 2-3 hour extraction session

---

## 🚨 CRITICAL REMINDERS

1. **Don't re-extract 20 known node types** — Just verify + add missing properties
2. **Extract REAL data** — Not guesses. If it's not in code, don't guess.
3. **Document sources** — Every property needs a source (which file/API/table)
4. **Be complete** — One thorough pass beats multiple partial attempts
5. **Follow imports** — If a model imports from another file, trace that import
6. **Capture enums** — If a field is categorical, list all possible values
7. **Count records** — Where possible, get actual row counts, record counts
8. **Use quick reference** — Terminal_QUICK_REFERENCE has one-line commands

---

## 📞 SUPPORT DOCUMENTS

If you get stuck, reference:

| Issue | Document |
|-------|----------|
| "What should Terminal 1 extract?" | EXTRACT_BD_ENGINE.md |
| "What should Terminal 2 extract?" | EXTRACT_DATA_SCRAPER.md |
| "What should Terminal 3 extract?" | EXTRACT_N8N_BUILDER.md |
| "How do I run 3 in parallel?" | MASTER_ARCHITECTURE_EXTRACTION_GUIDE.md |
| "Quick command to find X?" | TERMINAL_QUICK_REFERENCE.md |
| "Did I complete Terminal 1?" | EXTRACTION_PROGRESS_TRACKER.md |
| "How do I merge the outputs?" | MASTER_ARCHITECTURE_EXTRACTION_GUIDE.md |

---

## 🎯 FINAL GOAL

**The PTS Data Architecture Explorer V3** — An interactive, zoomable, filterable graph visualization showing:

- Every entity across all 3 projects
- Every property with source attribution
- Every relationship (including cross-project)
- Every data flow pipeline
- Complete Qdrant/Notion/SQL schema coverage
- 50+ entities, 700+ properties, 100+ relationships, 400+ aliases, 20+ data flows

This becomes your **single source of truth** for the entire PTS platform's data architecture.

---

*Complete extraction package generated 2026-02-12 | Start with MASTER_ARCHITECTURE_EXTRACTION_GUIDE.md*
