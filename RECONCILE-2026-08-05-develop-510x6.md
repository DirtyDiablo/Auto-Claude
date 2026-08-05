# Reconcile report — develop 510-ahead / 6-behind (2026-08-05)

The biggest single merge of the 2026-08-04 laptop migration. Merge commit: `de3c9360`.
Method per `D:\MIGRATION-MANUAL.md` Part 7 item 7: origin/develop's 6 incoming commits
merged INTO the 510-commit local line, develop fast-forwarded to the result.

## What the two sides were

- **Local line (ours):** tip `5ce33a34`, 510 commits not on origin/develop, secured
  pre-merge on `origin/local-develop-2026-08-04` (and `origin/local-2026-08-04`, which
  additionally carries triage commits `260148b3` + `02428faf`).
- **Incoming (theirs):** `75869f7e..bec3fc88` — upstream's migration from the Python
  `claude-agent-sdk` backend to a TypeScript agent layer on Vercel AI SDK v6, including
  `apps/frontend` → `apps/desktop` rename and full retirement of `apps/backend`, plus
  CI fixes and 2.8.0-beta version bumps.

## Why the scary headline was benign

The 510 count is inflated by duplicated/rebased history that had already converged at
the `5ce33a34` merge. Net tree delta of the local line vs merge-base `96ea7d36`:
**49 files**. Overlap with the migration's 1,974 changed files: **7 files**.

## Conflict resolutions (9 total)

| Files | Resolution | Why |
|---|---|---|
| 6 Python files (`core/client.py`, `core/simple_client.py`, `runners/github/services/*`) | **Deleted (theirs)** | Whole Python agent layer superseded by `apps/desktop/src/main/ai/`. The local +408 lines (cross-platform Claude CLI detection mirroring `cli-tool-manager.ts`, parallel-reviewer tweaks) are preserved verbatim on `origin/local-develop-2026-08-04`; the CLI-detection concern already exists on the TS side. |
| `electron.vite.config.ts` | **Union** | Kept local `pty-daemon` entry chunk — `pty-daemon-client.ts:128` spawns `out/main/pty-daemon.js`, which only exists because of this entry — plus incoming `ai/agent/worker` entry. Build verified both chunks emit. |
| `prompts/qa_fixer.md` | **Union** | Local "QA FIX IRON LAWS" + incoming "CRITICAL RULES" sections both kept; worktree example path updated to `./apps/desktop` in the local no-emoji style. |
| `src/main/log-service.ts` | **Exact-usage import** | Kept `unlinkSync` (used at line 298, local edit), dropped `statSync` (no longer used by merged body). |

Rename detection (limit raised to 32767) carried the remaining local edits into their
new `apps/desktop/` paths with no conflict: 5 agent prompts (IRON LAWS blocks),
`ipc-handlers/context/utils.ts` (`~/.auto-claude/memories` fallback), and
`ClaudeCodeStatusBadge.tsx`. `.gitignore` auto-merged (local "External Reference
Libraries" block kept). The local feature line — `spec-025-job-ingestion-pipeline/`,
4 pipeline tests under `tests/`, outputs scaffolding, setup guides,
`libs/SUPERPOWERS_INTEGRATION.md` — was untouched by the migration and survives as-is.

## Verification (apps/desktop, post-merge)

- `npm run typecheck` — clean.
- `npm run lint` (Biome) — 0 errors; 822 warnings, all upstream baseline (`any` usage).
- `npm test` (Vitest) — **4,196 / 4,205 pass**. One consistent failure:
  `github-error-parser.test.ts` › "should generate fallback message when reset time has
  passed" — file and implementation are byte-identical to origin/develop (time-dependent
  upstream test, fails on upstream's own tree here). One other file flaked once, passed
  on re-run.
- `npm run build` — succeeds; `out/main/pty-daemon.js` and `out/main/ai/agent/worker.js`
  both emitted.
- `git ls-files -s` gitlink count: **0** (scope-guard verification — the data-scraper /
  n8n-builder / voice-mcp / tango-python pointers live inside BD-Automation-Engine, not
  in this parent; nothing to update here).

## Dirty-file triage (honored, not re-litigated)

Per the source closeout receipt: the 3 modified tracked files (`package.json`,
`package-lock.json`, `apps/frontend/package.json`) and `knip.json` were verified
byte-identical to what's committed on `origin/local-2026-08-04` (`260148b3`,
`02428faf`) and restored locally. Untracked stays untouched: `BD-Engine-v2/` and
`getshitdone/` (nested repos, separately secured), `donor-clearancejobs-contact-pipeline/`
(secured in `02428faf`), `outputs/daily_call_list.*` (scheduler-regenerated PII junk —
never commit). No `git clean` anywhere.

## Standing state

- `origin/local-develop-2026-08-04` and `origin/local-2026-08-04` — **intact, untouched**;
  they stay until George signs off the whole migration.
- BD-Automation-Engine — out of scope, untouched (own session, own repo, gitignored here).
- On-disk leftovers `apps/frontend/` (node_modules, out) and `apps/backend/` (.venv, .env)
  now contain only gitignored files; harmless, deletable whenever George wants.
- Porting debt (optional, low): if the Python-side CLI-detection hardening ever matters
  to the TS layer, the reference implementation is on `origin/local-develop-2026-08-04`
  at `apps/backend/core/client.py`.
