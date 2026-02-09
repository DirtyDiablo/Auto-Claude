# PTS BD Dashboard v6 — CORRECTED Implementation Package
## February 8, 2026

## What Changed from v5

The v5 implementation package contained **22 errors** discovered during deep filesystem audits of all 3 terminals. The most critical: v5 assumed the dashboard was a blank slate, when in fact **27 pages, 63 npm packages, a full API client, and complete component library already exist**.

### Error Categories

| Category | Count | Impact |
|---|---|---|
| Wrong directory paths | 2 | Terminals would fail immediately |
| Wrong branch names | 3 | Git operations would fail |
| Wrong infrastructure counts | 4 | Prompts give agents wrong assumptions |
| Dashboard already exists (not blank) | 8 | Entire rebuild of existing work |
| Routing/proxy pattern wrong | 2 | API connections would break |
| n8n references (removed) | 1 | Confusion and dead code |

### Key Corrections

1. **Terminal paths**: `C:\Auto-Claud\Auto-Claude\BD-Automation-Engine\` (not `C:\Users\gtmar\Projects\...`)
2. **Branches**: B=`master`, C=`master` (not `main`)
3. **CrewAI**: 13 agents in 6 crews (not 5 agents)
4. **Neo4j**: 12 nodes, 9 rels, 10 labels, 14 rel types (not 7 nodes, 4 rels)
5. **Dashboard**: 27 pages exist — Phase 1 becomes "verify + fix" not "build from scratch"
6. **Routing**: State-based activeTab (not TanStack Router)
7. **Proxy**: Per-route mapping (not /api prefix rewrite)
8. **Node.js**: v24.13.0 (not v20/v22)

## Files in This Package

```
v6-corrected/
├── PTS_BD_Dashboard_Implementation_v6_CORRECTED.md   ← MASTER GUIDE (replaces v5)
│   • 22 errors documented and fixed
│   • 3 corrected Terminal A phase prompts
│   • Corrected Terminal B + C support prompts
│   • Execution order with realistic time estimates
│
└── project-knowledge/                                 ← Upload ALL 4 to Claude Project
    ├── 01_ARCHITECTURE_STATE_v2.md                    ← CORRECTED (major changes)
    │   • Correct paths, branches, counts
    │   • Full 12-collection Qdrant table
    │   • 13 agents / 6 crews documented
    │   • Dashboard existing state documented
    │
    ├── 02_TERMINAL_PROMPT_PATTERNS_v2.md               ← CORRECTED
    │   • Correct terminal paths and branches
    │   • Added "dashboard already exists" context rules
    │   • Key file locations for dashboard work
    │
    ├── 03_DATA_SCHEMA_REFERENCE.md                     ← UNCHANGED (no errors found)
    │
    └── 04_BD_METHODOLOGY_REFERENCE.md                  ← UNCHANGED (no errors found)
```

## How to Use

### Step 1: Replace Project Knowledge
1. Remove ALL old project knowledge docs from your Claude Project
2. Upload all 4 files from `project-knowledge/` folder
3. Also upload `PTS_BD_Dashboard_Implementation_v6_CORRECTED.md`

### Step 2: Execute Terminal Prompts
1. **Terminal A Phase 1**: Copy the Phase 1 prompt from the v6 guide → paste into Auto-Claude
2. **Terminal B + C**: Copy support prompts → paste into their respective terminals (run in parallel)
3. After Phase 1 completes, copy the "COPY-PASTE FOR ORCHESTRATOR" back to this chat
4. Continue with Phase 2, then Phase 3

### Estimated Timeline
| Phase | Terminal | Hours |
|---|---|---|
| Phase 1: Verify + Fix | A (+ B/C parallel) | 1-2 |
| Phase 2: Entity Pages | A | 3-5 |
| Phase 3: Outreach + Analytics | A | 3-5 |
| **Total** | | **8-12 hours** |
