# Auto-Claude Forward Plan — 2026-08-09

**Document type:** Post-migration forward planning (per CHARTER: Finish-line list, integration moves, decision gates, suggested order, explicitly parked work)  
**Baseline:** Dashboard (2026-08-09), workstream emit (2026-08-05), cross-repo census (2026-08-05)  
**Plan horizon:** Phase 9 → shipping readiness (T+4 weeks, iterative refinement)  
**George's failure mode:** "I get most of the way there and then I move onto the next one before it is 100%." → This plan optimizes for **finishing**, not starting.

---

## 1. Finish-Line List (Near-Done Workstreams)

Ordered by payoff / effort ratio. Each task has explicit acceptance criteria ("definition of done").

### 1.1 **WS-SDK-MIGRATION — Verify baseline + document known issues** ✅ (95%)

**Status:** Merge complete; tests pass 4,196/4,205 (99.8%); one known upstream flake.  
**Evidence:** Commit de3c9360 (merge), cfe94e78 (reconcile report). Typecheck: clean. Lint: 822 warnings (baseline).

**Remaining work:**
- [ ] Re-run `npm test` on Precision machine to confirm 4,196/4,205 baseline is stable (not flaky regression)
- [ ] Run `npm run typecheck` to verify type safety (expected: clean)
- [ ] Document the github-error-parser.test.ts flake (time-dependent, upstream baseline, not a merge regression) in KNOWN_ISSUES.md
- [ ] Confirm app can launch in dev mode (`npm run dev`) without errors
- [ ] Verify electron build succeeds (`npm run build`)

**Definition of done:**  
All 5 tasks completed; baseline test results confirmed on Precision; 1 upstream flake documented with link to upstream issue (if any); team unblocked to release.

**Payoff:** Unblock shipping; establish stable test baseline for all downstream work.  
**Effort:** S (1 day, mostly waiting on test runs)  
**Blocker:** None.

---

### 1.2 **WS-DONOR-PIPELINE — PII audit + commit decision** 🟡 (70%)

**Status:** 11 files (10 numbered patches + combined .mine.patch, ~332 KB measured 2026-08-09) secured pre-migration; untracked on Precision; no audit completed.  
**Evidence:** Commit 02428faf; untracked dir `donor-clearancejobs-contact-pipeline/`; MIGRATION-MANUAL Part 6 §7 flags NFR-2 concern.

**Remaining work:**
- [ ] George inspects patch files for PII (email, phone, names, account IDs, credentials, internal URLs)
- [ ] George rules: (a) **COMMIT** if clean, (b) **MOVE TO PRIVATE REPO** if light PII, or (c) **DELETE** if sensitive
- [ ] If COMMIT: `git add donor-clearancejobs-contact-pipeline/` + commit with message `chore: add ClearanceJobs pipeline patches (PII-audited clean)`
- [ ] If MOVE: document hand-off location in MIGRATION-MANUAL Part 6 addendum
- [ ] If DELETE: note decision in continuity ledger

**Definition of done:**  
George's decision made and documented; if (a), patches are committed and `git status` shows them tracked; team understands future ClearanceJobs capability status.

**Payoff:** Unblock candidate contact enrichment; resolve open inventory item.  
**Effort:** S (audit = 20 min; decision = 5 min; commit = 5 min)  
**Blocker:** George PII review (30 min of his time).

---

### 1.3 **WS-SPEC-025-JOB-INGESTION — Characterize status + formalize or archive** ❓ (85%)

**Status:** Full 5-phase pipeline complete (268 jobs parsed, 100% Notion upload); no spec.md or acceptance criteria; never integrated into build orchestration.  
**Evidence:** Commit 52f4505a (2026-01-26); 7 Python modules, 8 output JSON files; README documents 243 jobs, 94.7% prime match.

**Remaining work:**
- [ ] George reviews spec-025/README.md results and determines: is this *complete-ready-to-ship* or *stalled-WIP* or *parked-idea*?
- [ ] **If READY-TO-SHIP:** formalize as `SPEC-025.md` at root with (a) requirements.json, (b) acceptance criteria (tests), (c) assign to build backlog
- [ ] **If STALLED-WIP:** move to separate feature branch (`feature/spec-025-revisit`) and document blocking issues
- [ ] **If PARKED-IDEA:** move to `docs/archived-specs/spec-025/` with decision note
- [ ] Document choice in continuity ledger with reason

**Definition of done:**  
George's disposition decision made and documented; directory either integrated into spec pipeline (with spec.md + acceptance criteria) or moved to archive branch or `docs/` with clear rationale.

**Payoff:** Resolve 85%-complete item; free decision overhead; clarify whether job ingestion is a shipping feature.  
**Effort:** M (30 min review + 1 day integration if shipping, else 30 min archive)  
**Blocker:** George's 30-min review.

---

### 1.4 **WS-KNIP-XSTATE-UPDATE — Verify + commit-or-skip decision** 🟡 (95%)

**Status:** knip.json (dead-code analyzer config) + xstate 5.28 bump secured pre-merge; untracked; xstate bump not re-applied.  
**Evidence:** Commit 260148b3; knip.json untracked; RECONCILE report notes byte-identical to origin/local-2026-08-04.

**Remaining work:**
- [ ] Check if `knip.json` exists on `origin/develop` (run: `git show origin/develop:knip.json 2>/dev/null && echo "EXISTS" || echo "NOT FOUND"`)
- [ ] George rules: (a) **ADD TO REPO** if not already present (repo-wide dev tooling), or (b) **KEEP LOCAL** (personal tooling only)
- [ ] If (a): commit knip.json; integrate `npm run knip` check into pre-commit lint script (`.husky/pre-commit`)
- [ ] If (b): add knip.json to `.gitignore` (if not already there) and document in CONTRIBUTING.md
- [ ] **Re-apply xstate 5.28 bump** if it was intentional (check `package.json` on `origin/develop` for current version)

**Definition of done:**  
knip.json disposition decided; either committed with lint integration or gitignored with documentation; xstate version aligned across branches.

**Payoff:** Enable dead-code detection in CI; reduce linting friction; clarify tooling ownership.  
**Effort:** S (<1 day: 15 min check + 30 min commit + 15 min integration, or 10 min gitignore)  
**Blocker:** None.

---

### 1.5 **WS-TEST-SUITE-FLAKES — Confirm baseline + document upstream issue** 🟡 (99%)

**Status:** 4,196/4,205 pass (99.8%); one upstream-baseline flake (github-error-parser.test.ts, time-dependent).  
**Evidence:** RECONCILE-2026-08-05-develop-510x6.md confirms flake is identical on origin/develop (not a merge regression).

**Remaining work:**
- [ ] Re-run `npm test` twice on Precision to establish whether github-error-parser.test.ts flake is **transient** or **consistent**
- [ ] If consistent: search Vercel AI SDK & github-error-parser upstream issues for root cause
- [ ] Document in KNOWN_ISSUES.md with (a) test name, (b) expected vs actual, (c) upstream status, (d) workaround (if any)
- [ ] Decide: file upstream issue if not already reported

**Definition of done:**  
Test results confirmed stable; flake documented in KNOWN_ISSUES.md with upstream link; team knows this is a known baseline issue, not a regression.

**Payoff:** Establish confidence in test stability; unblock CI sign-off.  
**Effort:** S (2–3 hrs for test runs + 30 min documentation)  
**Blocker:** None.

---

## 2. Integration Moves (Untied Work Worth Connecting Now)

### 2.1 **Implement Auto-Claude MCP Server** 🔴 CRITICAL (0%)

**Gap:** Agent configs reference `mcpServers: ['auto-claude']` in planner, coder, QA agents; no server exists. Session introspection tools (`recordDiscovery`, `recordGotcha`, `updateSubtaskStatus`, `getBuildProgress`) are dead code.

**Evidence:**  
- `apps/desktop/src/main/ai/mcp/registry.ts` line 106–119: spawns `auto-claude-mcp-server.js` (does not exist)
- `apps/desktop/src/main/ai/tools/auto-claude/record-discovery.ts` + `record-gotcha.ts` defined but unreachable
- `apps/desktop/src/main/ai/config/agent-configs.ts`: coder/QA agents list `TOOL_RECORD_DISCOVERY` in tools array (never executes)

**Remaining work:**
- [ ] **Design MCP server interface** (2–3 days TypeScript): define tool schemas (recordDiscovery, recordGotcha, updateSubtaskStatus, getBuildProgress, etc.)
- [ ] **Implement in-memory store** for session discoveries + gotchas (could be backed by file-based JSON or SQLite later)
- [ ] **Route tools to agent session context**: planner, coder, QA agents call tools → server records to session state
- [ ] **Add unit tests** for each tool (Vitest)
- [ ] **Integrate MCP server launch** into agent bootstrap (`apps/desktop/src/main/ai/session/index.ts`)
- [ ] **Verify coder/QA discovery logging** in end-to-end test

**Definition of done:**  
MCP server starts alongside agent sessions; all 4 tools execute without error; coder & QA agents record discoveries to session memory; E2E test confirms discovery logs persist in session output.

**Payoff:** Unblock session memory recording; unlock multi-session learning; enable gotcha capture.  
**Effort:** L (5–10 days: design 2 + impl 5 + tests 2 + integration 1)  
**Blocker:** None (pure implementation).  
**Owner:** Coder agent (recommend spawning as dedicated workstream).

---

### 2.2 **Verify MCP Context Layer Consistency** M (60%)

**Gap:** Agent configs reference MCP tools (recordDiscovery, etc.), but integration layer may have stale references or missing error handling for MCP connection failures.

**Remaining work:**  
- [ ] Audit `apps/desktop/src/main/ai/mcp/` for stale client initialization code
- [ ] Verify MCP client error handling in `apps/desktop/src/main/ai/session/index.ts` (graceful fallback if MCP server unavailable)
- [ ] Add MCP server health check before spawning coder/QA agents
- [ ] Document MCP server lifecycle in ARCHITECTURE.md

**Definition of done:**  
MCP integration is resilient to server startup failures; agent session logs indicate MCP connection status; team knows MCP server is not optional (blocking agents from running session memory code).

**Payoff:** Prevent silent failures of session introspection.  
**Effort:** S (1 day)  
**Blocker:** None (can run after MCP server impl).

---

## 3. Decisions George Owes (Blocked Workstreams Requiring His Ruling)

### D1: ClearanceJobs Patches — Commit vs. Archive vs. Move?

**Question:** After PII audit, do patches get committed to repo (with workflow integration), moved to private repo, or deleted?

**Evidence:** Untracked `donor-clearancejobs-contact-pipeline/` (11 files, ~332 KB).  
**Depends on:** George's PII review (~30 min).  
**Unblocks:** WS-DONOR-PIPELINE (finish-line item 1.2).  
**Suggested timeline:** Next 48 hours (low friction decision).

---

### D2: Spec-025 Disposition — Ship vs. Archive vs. Stall?

**Question:** Is job ingestion pipeline ready to integrate into automated BD workflow, or should it be archived as reference/parked as WIP?

**Evidence:** Commit 52f4505a; README documents full 5-phase pipeline with 243 jobs, 100% Notion success.  
**Depends on:** George's 30-min review of README + results.  
**Unblocks:** WS-SPEC-025-JOB-INGESTION (finish-line item 1.3); potential contribution to BD workflow lane.  
**Suggested timeline:** Next 48 hours (low friction decision).

---

### D3: Knip Tooling — Repo-wide or Local-only?

**Question:** Is knip.json a develop-branch dependency (all team members use it) or a personal dev tool (George only)?

**Evidence:** knip.json untracked; commit 260148b3 pre-merge.  
**Depends on:** ~5 min verification (`git show origin/develop:knip.json`).  
**Unblocks:** WS-KNIP-XSTATE-UPDATE (finish-line item 1.4).  
**Suggested timeline:** Today (2 min decision).

---

### D4: Auto-Claude MCP Server Priority — Now vs. Post-Launch?

**Question:** Build the MCP server now (5–10 days, blocking coder/QA session introspection) or defer to post-launch optimization?

**Evidence:** Dead code in registry.ts + agent configs; no urgent shipping dependency on session memory (nice-to-have for multi-session learning).  
**Risk if deferred:** Coder/QA agents operate without session discovery logging; multi-session insights unavailable.  
**Risk if built now:** 5–10 days delay to shipping; context overhead.  
**Suggested:** Defer to **Wave 1 post-launch** (iterate with real agent telemetry).  
**Unblocks:** Clarity on Phase 9 go-live scope.

---

## 4. Suggested Order of Attack (Top 5 Moves)

**Why this order:** Finish-line items ordered by (payoff × 1/effort) + decision gates resolved first + critical paths unblocked.

### **MOVE #1: Verify SDK baseline (1 day)** ← DO FIRST

**What:** Re-run `npm test` + `npm run typecheck` on Precision to confirm test stability.  
**Why:** Unblocks shipping sign-off. All downstream work depends on stable baseline. Super low friction (waiting on test runs).  
**Done when:** Test results match 4,196/4,205; typecheck clean; documented in KNOWN_ISSUES.md.

---

### **MOVE #2: Batch-decide ClearanceJobs + Spec-025 + Knip (2 hrs)** ← DO SECOND

**What:** George spends 2 hours on three finish-line decisions:
- (a) Inspect ClearanceJobs patches (30 min) → decide commit/archive/delete
- (b) Review Spec-025 README + results (30 min) → decide ship/archive/stall
- (c) Verify knip.json on origin/develop (5 min) → decide add-to-repo/keep-local

**Why:** High leverage. Three stalled 70–95% items unblock simultaneously. Decisions are parallelizable (single George pass = 3 items done).  
**Done when:** All three items have George's documented ruling; git status shows them committed (if yes) or gitignored (if no).

---

### **MOVE #3: Implement WS-DONOR-PIPELINE decision (if COMMIT)** ← DO THIRD

**What:** If George rules COMMIT: `git add donor-clearancejobs-contact-pipeline/` + commit.  
**Why:** Frees inventory item; restores ClearanceJobs capability to codebase.  
**Effort:** S (15 min).  
**Done when:** `git log --oneline | head -1` shows "chore: add ClearanceJobs pipeline patches...".

---

### **MOVE #4: Formalize or archive Spec-025 (if ship) OR archive (if stall/park)** ← DO FOURTH

**What:** If George rules SHIP: copy spec-025/ to `docs/specs/spec-025/` + add SPEC-025.md + requirements.json + acceptance criteria.  
If George rules ARCHIVE: move to `docs/archived-specs/spec-025/` with decision note.

**Why:** Clarifies job-ingestion ownership; unblocks decision overhead; enables downstream integration (if shipping).  
**Effort:** M (1–2 days if shipping, 30 min if archiving).  
**Done when:** Directory moved + spec.md or archive note committed + team knows disposition.

---

### **MOVE #5: Start MCP server design (5 days, parallel effort)** ← DO FIFTH (or parallel to #3–4)

**What:** Spawn **dedicated coder/architect** to design + implement Auto-Claude MCP server.

**Why:** Unblocks session introspection (gotcha capture, discovery logging, progress tracking). Safe to parallelize with #2–4 (no data deps).

**Effort:** L (5–10 days design+impl+tests).  
**Blocker if needed sooner:** Prioritize over new feature work. If shipping deadline is tight (days, not weeks), defer to Wave 1.

**Suggested path:** 
1. Design tool schemas (recordDiscovery, recordGotcha, updateSubtaskStatus, getBuildProgress) — 1 day
2. Implement in TypeScript (Zod schemas, stdio transport) — 3 days
3. Unit tests (Vitest) — 1 day
4. Integration into agent bootstrap — 1 day
5. E2E test (agent session → discovery logged) — 1 day

**Done when:** the definition of done in Integration Move 2.1 is met — MCP server starts alongside agent sessions, all 4 tools execute, coder/QA discoveries persist, E2E test passes.

---

## 5. Explicitly Parked Work (What NOT to Do, and Why)

### 🚫 **WS-BD-AUTOMATION-ENGINE-NESTED** — OUT OF SCOPE

**Why parked:** Own git repo with own emit. Covered separately by BD-Automation-Engine session. Auto-Claude repo treats it as gitignored dependency only.

**Action:** Refer to BD-Automation-Engine emit (own reconcile, own decisions).

---

### 🚫 **WS-SCHEDULER-OPERATIONS** — GATED ON X-1 SIGN-OFF

**Why parked:** Disabled pre-migration (Decision 18: stale-pid crash-loop). Re-enable depends on PTS-BD Phase 8 stack restore (X-1 milestone).

**Action:** After X-1 sign-off (Tier-3 restore + Phase 8 DB reconcile):
1. Verify `pts-reporting` dependencies are committed
2. Check for PII in `outputs/` (never bulk-git-add)
3. Re-enable scheduler with monitoring

**Timeline:** Post-Phase 9 (T+2–3 weeks after enclosure restore).

---

### 🚫 **Python Agent Layer Artifacts** — DELETE (NO DECISION NEEDED)

**Why parked:** Retired by WS-SDK-MIGRATION (Python → TypeScript). Artifacts are gitignored and safe to delete.

**Action:** `rm -r .venv apps/frontend/node_modules apps/backend` (when cleanup happens post-Phase 9).

---

### 🚫 **BD-Engine-v2 Untracked Directory** — CLARIFY THEN DELETE

**Status:** 4.4 GB untracked (measured 2026-08-09); duplicate/superseded by BD-Automation-Engine nested repo.

**Why parked:** Out of scope for Auto-Claude; belongs to BD-Automation-Engine emit.

**Action:** Refer to BD-Automation-Engine reconcile report; verify disposition; coordinate deletion if deemed obsolete.

---

### 🚫 **getshitdone/ Untracked Directory** — INVESTIGATE THEN DECIDE

**Status:** 554 KB untracked; unknown purpose.

**Why parked:** Unclear origin/ownership; risk of deleting active work.

**Action:** George inspects; if artifact/junk → delete; if active → move to docs or separate repo.

---

### 🚫 **Lint Baseline (822 warnings)** — DEFER TO WAVE 1

**Why parked:** Upstream baseline (same as origin/develop). Not a merge regression. Non-blocking for shipping.

**Action:** Keep as-is pre-launch. Post-launch, add linting improvement workstream to Wave 1 roadmap.

---

### 🚫 **TypeScript Strict Mode Hardening** — DEFER

**Status:** Typecheck clean; but some modules may use `any` to suppress strict checks.

**Why parked:** Non-blocking for shipping. Nice-to-have for maintainability.

**Action:** Post-launch: audit for `any` usage; upgrade to explicit types incrementally.

---

## 6. Continuity & Handoff Notes

### Phase 9 Go-Live Scope (What Needs Completion Before Shipping)

✅ **DONE:**
- Vercel AI SDK v6 integration (tests pass 99.8%)
- Merge reconciliation (all 7 conflicts resolved)
- i18n framework (English + French)
- Multi-provider LLM support (9 providers)
- Agent orchestration pipeline (planner→coder→QA)
- GitHub/GitLab integration
- Terminal system (PTY + xterm.js)
- Electron desktop app + CI (Windows/macOS/Linux)

⚠️ **DECISION GATES (George needed):**
1. ClearanceJobs patches: commit or archive? (30 min)
2. Spec-025: ship, stall, or park? (30 min)
3. Knip: repo tooling or local? (5 min)

🟡 **OPTIONAL (Wave 1 post-launch):**
- Auto-Claude MCP server implementation (5–10 days; unlocks session memory)
- Lint baseline hardening (upstream issue, not blocking)
- Test flake fix (file upstream issue if needed)
- Scheduler re-enable (depends on X-1 Phase 8)

### Continuity Ledger Location

**Harvests:** `D:\Auto-Claud\Auto-Claude\.claude\harvest\` (session harvest reports; currently holds 2026-08-05-workstream-emit.harvest.md)  
Note: `.claude\continuity\` does not exist in this repo as of 2026-08-09 — harvest files are the only continuity artifacts here.

### Next Orchestrator Session

**Input:** George's rulings on D1–D3 above.  
**Output:** Formalized specs for shipping items; delegation plan for MCP server.  
**Estimated:** 2–3 hours after George's decisions are documented.

---

## Appendix: Evidence & Verification

| Claim | Evidence | SHA/Ref |
|-------|----------|---------|
| Merge complete, tests 99.8% pass | RECONCILE-2026-08-05-develop-510x6.md | cfe94e78 |
| WS-SDK-MIGRATION DONE | All 7 conflicts resolved, typecheck clean | de3c9360 |
| WS-DONOR-PIPELINE untracked | `git status --porcelain` | HEAD |
| WS-SPEC-025 85% complete | spec-025/README.md + outputs/ | 52f4505a |
| WS-KNIP untracked | knip.json in git status | HEAD |
| Auto-Claude MCP server missing | `grep -n "auto-claude-mcp-server.js" registry.ts` (no file exists) | HEAD |
| Test flake upstream baseline | RECONCILE report + compare origin/develop | cfe94e78 |

---

**Document created:** 2026-08-09  
**Baseline:** Dashboard 2026-08-09, Emit 2026-08-05, Census 2026-08-05  
**Charter:** FINISHING optimization (not starting) + explicit acceptance criteria on every task  
**Next review:** After George's D1–D3 decisions (expect 2–3 hrs orchestrator + 5–10 days execution on #1–5).
