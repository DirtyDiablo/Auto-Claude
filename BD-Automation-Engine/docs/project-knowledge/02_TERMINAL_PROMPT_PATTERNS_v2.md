# Terminal Prompt Patterns — Phase Summary Feedback Loop
## Last Updated: February 8, 2026 (Post-Audit Correction)

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
[One paragraph natural language summary]
═══ END SUMMARY ═══
```

---

## Terminal Configuration ✅ CORRECTED Feb 8, 2026

| Terminal | Project | Ports | Directory | Branch |
|---|---|---|---|---|
| **A** | BD-Automation-Engine (Hub) | 8100, 5173 | `C:\Auto-Claud\Auto-Claude\BD-Automation-Engine\` | `claude/setup-auto-claude-IrK21` |
| **B** | Data-Scraper | 8200 | `C:\Auto-Claud\data-scraper\` | `master` |
| **C** | N8N-Builder | 8300 | `C:\Auto-Claud\N8N-Builder\` ⚠️ "Claud" not "Claude" | `master` |

⚠️ **Path corrections from v5**: Terminal A was incorrectly listed as `C:\Users\gtmar\Projects\...` and Terminal B as `C:\data-scraper\data-scraper\`. Branches B and C are `master` not `main`.

---

## Critical Context for Prompts: Dashboard Already Exists

**ALWAYS include this in Terminal A prompts:**

The dashboard has 27 existing pages, 63 npm packages, a full HubApiClient, and state-based routing. Prompts must:
- Reference EXISTING files and components by name
- Add to the existing switch statement in App.tsx
- Use the existing hubApiClient singleton from src/services/hubApi.ts
- Use the existing hooks from src/hooks/useHubApi.ts
- Follow the existing per-route Vite proxy pattern (NOT /api prefix rewriting)
- NOT rebuild pages, routing, API clients, or install already-present packages

---

## Prompt Structure Template

Every terminal prompt follows this structure:

```
[PHASE NAME]: [One-line description]

You are working on [Project Name] in [CORRECT Directory].
[1-2 sentences on what this project does and your role in the architecture.]

⚠️ CRITICAL: This dashboard has [X] existing pages. DO NOT rebuild them.

PREREQUISITE: [What must be true before starting — check with verification commands]

═══ VERIFIED CURRENT STATE ═══
[Key facts about what exists RIGHT NOW — prevents assumptions]
- Qdrant: 1,401,933 vectors across 12 collections
- API: running on :8100 with ~140+ endpoints
- Dashboard: 27 pages, 63 npm packages, state-based routing
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
When ALL deliverables are checked, output the Phase Completion Summary.
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

## Feedback Loop Workflow

```
┌──────────────────────────┐
│  Claude Orchestrator     │  ← YOU (this Claude project chat)
│  (Project Knowledge +    │
│   v6 Implementation)     │
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
│  phase prompt            │
└──────────────────────────┘
```

---

## Commit Convention

```
feat:     New feature or endpoint
fix:      Bug fix or data connection repair
refactor: Code restructuring without behavior change
audit:    Capability audit or state report
docs:     Documentation only
chore:    Dependencies, config, tooling
test:     Adding or fixing tests
```

---

## Key File Locations for Terminal A Dashboard Work

| File | Purpose | Modify? |
|---|---|---|
| `dashboard/src/App.tsx` | Root layout, routing switch, cross-nav handlers | ADD new cases |
| `dashboard/src/types/index.ts` | TabId type, data types | ADD new TabIds |
| `dashboard/src/components/Sidebar.tsx` | Navigation sidebar | ADD new nav items |
| `dashboard/src/services/hubApi.ts` | HubApiClient singleton | ADD new methods if needed |
| `dashboard/src/hooks/useHubApi.ts` | React hooks for API | ADD new hooks if needed |
| `dashboard/src/hooks/useAppData.ts` | TanStack Query data fetching | FIX data flow |
| `dashboard/vite.config.ts` | Dev proxy (17 per-route mappings) | ADD new routes if needed |
| `dashboard/package.json` | Dependencies (63 packages) | DON'T add already-installed |
