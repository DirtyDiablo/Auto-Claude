# Terminal Prompt Patterns — Phase Summary Feedback Loop
## Last Updated: February 7, 2026

---

## Core Pattern: Phase Summary → Next Phase Handoff

Every terminal prompt phase MUST end with a structured summary that feeds into the next phase or back to the orchestrating Claude session. This ensures continuity across chat sessions and prevents knowledge loss.

---

## Phase Completion Output Format

At the end of EVERY phase, the terminal must output this EXACT structure:

```
═══ PHASE COMPLETION SUMMARY ═══
Terminal: [A/B/C]
Phase: [Phase Name]  
Duration: [X minutes]
Status: [COMPLETE / PARTIAL / BLOCKED]

COMPLETED:
- [Specific deliverable 1 with verification command + result]
- [Specific deliverable 2 with verification command + result]

FAILED/SKIPPED:
- [Item] — Reason: [why]
- [Item] — Reason: [why]

STATE CHANGES:
- Qdrant vectors: [before] → [after] (run: curl localhost:6333/collections)
- API endpoints added: [list new routes]
- npm packages added: [list]
- pip packages added: [list]
- Files created: [list with paths]
- Files modified: [list with paths]
- Config changes: [.env, vite.config, etc.]

BLOCKERS FOR NEXT PHASE:
- [Dependency on Terminal X completing Y]
- [Missing API key / config]
- [Bug that needs manual intervention]

NEXT PHASE READY: [YES/NO]

COPY-PASTE FOR ORCHESTRATOR:
[One paragraph natural language summary. Example: "Terminal A Phase 1 complete. Installed 9 npm packages (tremor, tanstack-table, cmdk, framer-motion, zod, react-hook-form, dnd-kit core+sortable, date-fns). Created API client with Vite proxy to :8100. Built sidebar layout with 8 routes. Dashboard home page loads live KPI cards from GET /stats showing 1.4M total vectors. AI Search page works with both raw vector search and AI synthesis via POST /ask/smart. Agents page triggers research crew successfully. No blockers. Ready for Phase 2."]
═══ END SUMMARY ═══
```

---

## Feedback Loop Workflow

```
┌──────────────────────────┐
│  Claude Orchestrator     │  ← YOU (this Claude project chat)
│  (Project Knowledge +    │
│   Dashboard Guide)       │
└─────────┬────────────────┘
          │ Generates phase prompt
          ▼
┌──────────────────────────┐
│  Auto-Claude Terminal    │  ← Runs autonomously
│  (Executes phase tasks)  │
└─────────┬────────────────┘
          │ Outputs Phase Completion Summary
          ▼
┌──────────────────────────┐
│  You copy "COPY-PASTE    │  ← 30 seconds of your time
│  FOR ORCHESTRATOR" text  │
│  back into Claude chat   │
└─────────┬────────────────┘
          │ Claude updates context
          ▼
┌──────────────────────────┐
│  Claude generates next   │  ← Or you paste pre-written prompt
│  phase prompt (or        │
│  troubleshoots issues)   │
└──────────────────────────┘
```

**Key Rule**: If the Phase Completion Summary says `BLOCKED`, paste the full summary (not just the copy-paste paragraph) into the orchestrator so Claude can diagnose and generate a fix prompt.

---

## Terminal Configuration

| Terminal | Project | Port | Directory | Branch |
|---|---|---|---|---|
| **A** | BD-Automation-Engine (Hub) | 8100, 5173 | `C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine\` | auto-claude branches |
| **B** | Data-Scraper | 8200 | `C:\data-scraper\data-scraper\` | main |
| **C** | N8N-Builder | 8300 | `C:\Auto-Claud\N8N-Builder\` ⚠️ "Claud" not "Claude" | main |

---

## Prompt Structure Template

Every terminal prompt follows this structure:

```
[PHASE NAME]: [One-line description]

You are working on [Project Name] in [Directory].
[1-2 sentences on what this project does and your role in the architecture.]

PREREQUISITE: [What must be true before starting — check with verification commands]

═══ VERIFIED CURRENT STATE ═══
[Key facts about what exists RIGHT NOW — prevents assumptions]
- Qdrant: X vectors across Y collections
- API: running on :PORT with N endpoints
- Frontend: [state]
- Last phase completed: [what was done]

═══ TASK 1: [Task Name] ═══
[Specific instructions with code blocks]
[Verification command to confirm task is done]

═══ TASK 2: [Task Name] ═══
[...]

═══ DELIVERABLES ═══
- [ ] [Checklist item 1 — with verification command]
- [ ] [Checklist item 2 — with verification command]

═══ PHASE COMPLETION ═══
When ALL deliverables are checked, output the Phase Completion Summary using the format above.
Then commit: git add -A && git commit -m "[type]: [description]" && git push
```

---

## Parallel Execution Rules

1. Terminal B and C can ALWAYS run in parallel with each other
2. Terminal A Phase N+1 waits for Terminal A Phase N completion
3. Terminal B/C support tasks run simultaneously with Terminal A phases
4. Cross-terminal dependencies go in the PREREQUISITE and BLOCKERS sections
5. If Terminal A needs an API from B/C that doesn't exist yet, A should create a mock/stub and note the blocker

---

## Commit Convention

```
feat:     New feature or endpoint
fix:      Bug fix
refactor: Code restructuring without behavior change
audit:    Capability audit or state report
docs:     Documentation only
chore:    Dependencies, config, tooling
test:     Adding or fixing tests
```

Examples:
- `feat: Dashboard V5 Phase 1 - foundation, AI search, agent triggers`
- `audit: Terminal A capabilities and state report Feb 7 2026`
- `fix: CORS configuration for dashboard proxy`

---

## Quick Reference: Audit Prompt Trigger

Whenever the system state is uncertain (new session, after errors, before major phase), run the health check script:

```bash
python scripts/health_check.py
```

This outputs a condensed state report suitable for pasting into the orchestrator. See `scripts/health_check.py` in each terminal project.
