# PTS BD Dashboard v5 — Complete Implementation Package

## What's In This Package

```
📁 project-knowledge/          ← Upload ALL 4 to Claude Project
│  ├── 01_ARCHITECTURE_STATE.md       Architecture, infra, integrations
│  ├── 02_TERMINAL_PROMPT_PATTERNS.md Prompt format, feedback loop, parallel execution
│  ├── 03_DATA_SCHEMA_REFERENCE.md    Qdrant schemas, Notion schemas, classification logic
│  └── 04_BD_METHODOLOGY_REFERENCE.md 6-phase BD cycle, formula, HUMINT, targets, KPIs
│
📁 automation/                  ← Copy-paste audit prompts (one per terminal)
│  ├── AUDIT_TERMINAL_A.txt           Hub: API, Qdrant, agents, frontend, Neo4j, Mem0
│  ├── AUDIT_TERMINAL_B.txt           Data: scrapers, APIs, Bullhorn, n8n removal
│  └── AUDIT_TERMINAL_C.txt           Workflow: LangGraph, Tango, outreach, n8n removal
│
📁 scripts/                     ← Drop into each project's scripts/ directory
│  ├── health_check.py                Run on Terminal A — condensed state for orchestrator
│  ├── validate_phase.py              Run after each phase — checks deliverables
│  └── install_dashboard_deps.bat     Run on Terminal A — installs all npm packages
│
📄 PTS_BD_Dashboard_Implementation_v5.md  ← Master guide with all phase prompts
└── 📄 PTS_Project_Knowledge_Update_Package.md ← Combined reference (everything above)
```

## Execution Order

### Day 1: Audit + Foundation

```
STEP 1: Run Audits (30 min total — all 3 terminals in parallel)
├── Terminal A: paste contents of automation/AUDIT_TERMINAL_A.txt
├── Terminal B: paste contents of automation/AUDIT_TERMINAL_B.txt
└── Terminal C: paste contents of automation/AUDIT_TERMINAL_C.txt

STEP 2: Collect Results
├── Copy each terminal's "COPY-PASTE FOR ORCHESTRATOR" paragraph
├── Paste all 3 into your Claude orchestrator chat
└── Claude now has verified current state

STEP 3: Update Project Knowledge
├── Update any values in the 4 project-knowledge/ docs that audits revealed changed
├── Remove old project knowledge files from Claude Project
└── Upload all 4 updated docs to Claude Project

STEP 4: Copy scripts to projects
├── Terminal A: copy health_check.py + validate_phase.py to BD-Automation-Engine/scripts/
├── Terminal A: copy install_dashboard_deps.bat to BD-Automation-Engine/
└── Run install_dashboard_deps.bat on Terminal A
```

### Day 1-3: Dashboard Build

```
STEP 5: Dashboard Phase 1 (Terminal A — 2-4 hours)
├── Paste Phase 1 prompt from PTS_BD_Dashboard_Implementation_v5.md
├── Terminal runs autonomously
├── When done: python scripts/validate_phase.py 1
├── Copy "COPY-PASTE FOR ORCHESTRATOR" back to Claude
└── SIMULTANEOUSLY run Terminal B + C support prompts

STEP 6: Dashboard Phase 2 (Terminal A — 3-5 hours)
├── Paste Phase 2 prompt
├── When done: python scripts/validate_phase.py 2
└── Copy results back to Claude

STEP 7: Dashboard Phase 3 (Terminal A — 3-5 hours)
├── Paste Phase 3 prompt
├── When done: python scripts/validate_phase.py 3
└── Copy results back to Claude
```

### Ongoing: Health Check Pattern

```
Anytime you start a new Claude session:
1. Run: python scripts/health_check.py (on Terminal A)
2. Paste output into Claude
3. Claude has full current state
4. Continue from where you left off
```

## Claude Session Configuration

| Setting | Value |
|---------|-------|
| Model | Claude Opus 4 (claude-opus-4-5-20250929) |
| Extended Thinking | ON — HIGH budget |
| Web Search | ON |
| Code Execution | ON |
| Artifacts | ON |
| Memory | ON |
| MCP: Notion | Connected |

## Key Decisions Made

1. **n8n REMOVED** — All automation is Python-native (FastAPI, APScheduler, or cron)
2. **N8N-Builder keeps its name** but drops n8n runtime dependency; retains LangGraph, Tango, outreach engine
3. **Graph visualization tiered**: G6 v5 for org charts + exploration (Phase 2), Cosmograph deferred (requires license)
4. **Feedback loop built in**: Every phase ends with structured summary that feeds context back to Claude
5. **Phase validation automated**: `validate_phase.py` checks actual deliverables before proceeding
6. **Health check standardized**: `health_check.py` gives instant state snapshot for any new Claude session
