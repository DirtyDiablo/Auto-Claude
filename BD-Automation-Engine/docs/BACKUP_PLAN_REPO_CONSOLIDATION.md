# Backup Plan: Repo Consolidation into BD-Automation-Engine

## Status: Backup / Alternative Plan
OpenClaw has a separate primary plan for this. This documents the fallback approach.

## Problem
OpenClaw's workspace is set to `C:/Auto-Claud/Auto-Claude/BD-Automation-Engine`. The two sibling repos (`N8N-Builder` and `data-scraper`) sit outside this workspace at `C:/Auto-Claud/`, meaning the OpenClaw agent cannot access them.

Setting workspace to `C:/Auto-Claud` would include the entire Auto-Claude Electron app (thousands of frontend files, node_modules) which wastes tokens and context.

## Backup Approach: Move Into BD-Automation-Engine

Copy `N8N-Builder` and `data-scraper` into BD-Automation-Engine as subdirectories:

```
BD-Automation-Engine/
├── Engine1_Scraper/
├── Engine2_ProgramMapping/
├── Engine3_OrgChart/
├── Engine4_Playbook/
├── Engine5_Scoring/
├── Engine6_QA/
├── Engine7_BullhornETL/
├── Engine8_Knowledge/
├── n8n-builder/          <- from C:/Auto-Claud/N8N-Builder
├── data-scraper/         <- from C:/Auto-Claud/data-scraper
├── orchestrator.py
└── ...
```

### Benefits
- Single workspace covers all BD pipeline code
- Main agent sees everything, subagents focus on subdirectories
- No Auto-Claude frontend noise in context
- Natural fit — all three repos serve the same BD pipeline

### Risks
- Nested git repos if .git dirs are preserved (use copy, not move)
- Independent push/pull for N8N-Builder and data-scraper becomes manual
- Large move could cause merge conflicts if upstream repos diverge

### Migration Steps
1. Copy (not move) `C:/Auto-Claud/N8N-Builder` -> `BD-Automation-Engine/n8n-builder/`
2. Copy `C:/Auto-Claud/data-scraper` -> `BD-Automation-Engine/data-scraper/`
3. Remove nested `.git` directories from copied folders
4. Update any cross-repo import paths
5. Add to BD-Automation-Engine git tracking
6. Update orchestrator.py if it references external paths
7. OpenClaw workspace stays as-is — no config change needed

### Alternative: OpenClaw Multi-Workspace (Primary Plan)
See OpenClaw's own plan for the preferred approach (may use agent routing, workspace overrides, or MCP filesystem access).

---
Created: 2026-02-21
