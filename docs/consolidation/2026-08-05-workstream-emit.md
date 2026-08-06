# Auto-Claude Repository Workstream Emit — 2026-08-05

Single source of truth for all workstreams (finished, in-flight, abandoned) from both MAINGEAR and Precision machines, post-migration reconciliation.

---

## WS-SDK-MIGRATION — Vercel AI SDK v6 migration and Python agent layer retirement

- **Home:** D:\Auto-Claud\Auto-Claude (single repo)
- **Status:** DONE
- **Machine history:** Precision-side work (incoming on origin/develop, commits 75869f7e through bec3fc88). Origin/develop carried the migration; local-develop-2026-08-04 (510-commit line) was secured pre-merge and merged INTO it via commit de3c9360 (2026-08-05). Final reconcile commit cfe94e78 documents decisions.
- **Last activity:** 2026-08-05, commit cfe94e78 "docs: reconcile decisions report — develop 510x6 merge (de3c9360)"
- **Unfinished remainder:** None. Merge complete. Rebuild artifacts (Python .venv, apps/frontend node_modules, apps/backend) are gitignored; deletable.
- **Next milestone:** Verify on Precision via `npm run typecheck` and `npm test` (4,196/4,205 pass; 1 known upstream-baseline flake). App ready to release.
- **Evidence:** 
  - commit 75869f7e: `feat: migrate from Python Claude Agent SDK to Vercel AI SDK v6 (TypeScript) (#1891)`
  - commit de3c9360: merge commit (merge origin/develop into local-develop)
  - commit cfe94e78: RECONCILE-2026-08-05-develop-510x6.md (conflict resolutions, verification results)
  - Merge verification: 7 file conflicts resolved; 49 net files changed in local line; electron.vite.config.ts union merge verified; tests passing

---

## WS-DONOR-PIPELINE — ClearanceJobs candidate contact pipeline (donor patches)

- **Home:** D:\Auto-Claud\Auto-Claude (donor-clearancejobs-contact-pipeline/ untracked subdir)
- **Status:** STALLED
- **Machine history:** Source machine (pre-migration). Commits 02428faf secured as part of pre-migration closeout; patches 0001-0006 applied to local line. Now untracked on Precision; no push to origin.
- **Last activity:** 2026-08-04, pre-migration session (commit 02428faf). Untracked directory created after reconcile merge.
- **Unfinished remainder:** Untracked directory on-disk; not committed. ClearanceJobs data remains locally scoped (PII concerns per MIGRATION-MANUAL Part 6 §7).
- **Next milestone:** Inspect untracked directory; decide (a) commit as subdir after PII audit, (b) move to separate repo, or (c) keep as untracked reference.
- **Evidence:**
  - commit 02428faf: `chore(donor): ClearanceJobs contact-pipeline donor patches 0001-0006 (secured pre-migration)`
  - `git status`: donor-clearancejobs-contact-pipeline/ listed untracked
  - Closed by: PII evaluation (NFR-2 hook concern flagged in MIGRATION-MANUAL Part 6)

---

## WS-KNIP-XSTATE-UPDATE — Dead-code analyzer (knip) + xstate dependency version bump

- **Home:** D:\Auto-Claud\Auto-Claude
- **Status:** STALLED
- **Machine history:** Source machine (pre-migration). Commit 260148b3 secured as part of pre-migration closeout; knip.json added locally. Now untracked on Precision.
- **Last activity:** 2026-08-04, pre-migration session (commit 260148b3). knip.json untracked after reconcile merge.
- **Unfinished remainder:** knip.json (untracked dependency config file) and xstate 5.28 version bump not re-applied post-merge. Decision: whether knip tooling is in the develop branch or local-only.
- **Next milestone:** Check origin/develop for knip.json; if not present, decide (a) commit locally as tooling addition or (b) keep untracked for local builds only.
- **Evidence:**
  - commit 260148b3: `chore(tooling): add knip dead-code analyzer + xstate 5.28 bump (local, pre-migration)`
  - `git status`: knip.json listed untracked
  - RECONCILE-2026-08-05-develop-510x6.md §"Dirty-file triage": knip.json verified byte-identical to origin/local-2026-08-04, left untracked post-merge

---

## WS-SPEC-025-JOB-INGESTION — Spec pipeline for job ingestion (local feature branch)

- **Home:** D:\Auto-Claud\Auto-Claude (spec-025-job-ingestion-pipeline/ subdir + tests/ + outputs/)
- **Status:** UNKNOWN
- **Machine history:** Local feature work; was untouched by the Vercel SDK migration on develop. Survives the reconcile as-is (commit cfe94e78 notes: "The local feature line...was untouched by the migration and survives as-is").
- **Last activity:** Unknown (pre-reconcile). Likely from earlier MAINGEAR session; not referenced in recent commits.
- **Unfinished remainder:** Not fully characterized. Feature directory and tests exist; status unknown (draft, in-review, blocked, ready-to-ship).
- **Next milestone:** Investigate whether spec-025 is (a) a completed feature awaiting merge, (b) a stalled WIP, or (c) a parked idea. Move to separate branch or archive if complete.
- **Evidence:**
  - RECONCILE-2026-08-05-develop-510x6.md: `The local feature line — spec-025-job-ingestion-pipeline/, 4 pipeline tests under tests/, outputs scaffolding, setup guides, libs/SUPERPOWERS_INTEGRATION.md — was untouched by the migration and survives as-is.`
  - Directory structure: D:\Auto-Claud\Auto-Claude/spec-025-job-ingestion-pipeline/ (tracked, survived reconcile)

---

## WS-APP-RENAME — Rebrand Aperant (previously "Auto Claude") in documentation

- **Home:** D:\Auto-Claud\Auto-Claude
- **Status:** DONE
- **Machine history:** Source machine. Commit 96ea7d36 "docs: rebrand Auto Claude to Aperant in README" present on both local line and origin/develop merge. Carried through via rename detection in the reconcile merge (de3c9360).
- **Last activity:** 2026-08-04, pre-migration (commit 96ea7d36). Carried by reconcile on 2026-08-05.
- **Unfinished remainder:** None. README rebranded; no further action needed.
- **Next milestone:** None; closed.
- **Evidence:** commit 96ea7d36: `docs: rebrand Auto Claude to Aperant in README`

---

## WS-PROFILE-PRIMARY-POLICIES — Restoration of policy-limits.json and execution rules

- **Home:** C:\Users\gtmar\.claude-profiles\primary (part of migration, not this repo)
- **Status:** DONE
- **Machine history:** Source machine (separate repo per MIGRATION-MANUAL Part 4 "profile-primary"). Committed as part of laptop migration consolidation. CLAUDE.md rules 7–8 (email-draft format + NEVER-SEND hard gate) added to profile.
- **Last activity:** 2026-08-04, profile closeout session (Decision 13: "policy-limits.json restored, deletion not ratified").
- **Unfinished remainder:** None; restored and pushed.
- **Next milestone:** None; closed.
- **Evidence:** MIGRATION-MANUAL Part 4, profile-primary section; CLAUDE.md (this file references it)

---

## WS-INFRASTRUCTURE-RECONCILE-STAGING — Precision machine staging and git quiesce (Phase A/B/C)

- **Home:** D:\Auto-Claud\Auto-Claude (+ siblings: PTS-BD-Platform, pg-pts, pts-reporting, N8N-Builder, data-scraper)
- **Status:** DONE
- **Machine history:** Precision side (pre-merge). MIGRATION-MANUAL Phase A/B executed; 510-commit backlog on Auto-Claude secured to origin/local-develop-2026-08-04 + origin/local-2026-08-04 on 2026-08-05. Stash exports, side branches, and commits done; 0 dirty pre-reconcile on Auto-Claude.
- **Last activity:** 2026-08-05, pre-reconcile quiesce (commits 260148b3, 02428faf pushed as secured state).
- **Unfinished remainder:** None. Precision machine cleaned to FROZEN state for reconcile.
- **Next milestone:** Verification at reconcile time (verify remote-secured; reconcile = DEBT per PRECISION-MERGE-PLAN §2026-08-05 full-sweep snapshot, line 117).
- **Evidence:**
  - MIGRATION-MANUAL Part 4, "Auto-Claude": "510-commit develop backlog found IDENTICAL on both machines...secured as `local-develop-2026-08-04` + `local-2026-08-04` on origin @ 5ce33a34"
  - PRECISION-MERGE-PLAN line 117: "D:\Auto-Claud\Auto-Claude | develop, 10 dirty, behind 6 / ahead 510 | as planned: verify remote-secured; reconcile = DEBT"

---

## WS-BD-AUTOMATION-ENGINE-NESTED — BD-Automation-Engine (nested repo + gitignored worktrees)

- **Home:** D:\Auto-Claud\Auto-Claude/BD-Automation-Engine (nested git repo, scope of separate session)
- **Status:** UNKNOWN
- **Machine history:** Bundled via BD-Automation-Engine's own session (out of scope for this emit). 5 git bundles secured (data-scraper, n8n-builder, voice-mcp, tango-python, getshitdone); Docker volumes exported; RESTORE-MAP committed. On Auto-Claude reconcile: "out of scope, untouched (own session, own repo, gitignored here)".
- **Last activity:** Source machine (2026-08-04 BD-Engine session). Not touched by Auto-Claude reconcile.
- **Unfinished remainder:** Nested repo work; covered by separate emit.
- **Next milestone:** Refer to BD-Automation-Engine's own workstream emit.
- **Evidence:**
  - MIGRATION-MANUAL Part 4, "BD-Automation-Engine (+ parent Auto-Claude, + nested repos)"
  - RECONCILE-2026-08-05-develop-510x6.md: "BD-Automation-Engine — out of scope, untouched (own session, own repo, gitignored here)"

---

## WS-SCHEDULER-OPERATIONS — Nightly scheduler (outputs generation) and PII data lifecycle

- **Home:** D:\Auto-Claud\Auto-Claude/outputs/ + untracked PII directories
- **Status:** STALLED
- **Machine history:** Scheduler was disabled during migration (Decision 18, pre-existing stale-pid crash-loop). Outputs directory holds untracked PII junk (daily_call_list.* generated by scheduler pre-migration).
- **Last activity:** Unknown (scheduler disabled pre-migration; PII dumps generated at unknown time).
- **Unfinished remainder:** (a) Scheduler re-enable decision pending George (PRECISION-MERGE-PLAN Phase 9); (b) PII outputs untracked (never commit); (c) nightly job dependencies holding groups are themselves uncommitted (pts-reporting; separate emit).
- **Next milestone:** Re-enable scheduler after DB reconcile completes and deps verify (Decision 18).
- **Evidence:**
  - PRECISION-MERGE-PLAN Phase 9: "scheduler stopped deliberately (Decision 18, stale-pid crash-loop was pre-existing) — re-enable after sign-off"
  - `git status`: outputs/daily_call_list.* (untracked, PII)
  - MIGRATION-MANUAL Part 6 §2, 14: PII never through a remote

---

## WS-TEST-SUITE-FLAKES — Intermittent test failures in GitHub error parser (time-dependent)

- **Home:** D:\Auto-Claud\Auto-Claude/apps/desktop/src/main/ai/runners/github/github-error-parser.test.ts
- **Status:** STALLED
- **Machine history:** Upstream baseline (origin/develop). One consistent failure: "should generate fallback message when reset time has passed" (test time-dependent, fails on upstream's own tree). Reconcile report notes it is identical to origin/develop.
- **Last activity:** 2026-08-05 (visible in test output post-reconcile merge, commit cfe94e78).
- **Unfinished remainder:** One flaky test (time-dependent); one other file flaked once, passed on re-run (Vitest 4,196/4,205 pass). Known upstream issue; not a merge regression.
- **Next milestone:** Monitor; if critical, file issue with upstream (Vercel/AI SDK team). Low priority for now (expected baseline).
- **Evidence:**
  - RECONCILE-2026-08-05-develop-510x6.md §"Verification": `npm test` results, "One consistent failure: github-error-parser.test.ts...time-dependent upstream test, fails on upstream's own tree here"`

