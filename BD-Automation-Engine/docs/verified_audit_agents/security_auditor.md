# COMPREHENSIVE SECURITY AUDIT REPORT

**Project:** BD-Automation-Engine (PTS BD Intelligence System)
**Audit Date:** 2026-02-20
**Auditor:** Security Audit Agent (voltagent-qa-sec:security-auditor)
**Scope:** Credential exposure, authentication gaps, code injection, auth bypass, SSRF

---

## EXECUTIVE SUMMARY

This audit identified **23 findings**, including **7 CRITICAL**, **8 HIGH**, **5 MEDIUM**, and **3 LOW** severity issues. The most urgent concern is that the production `.env` file contains live API keys, database passwords, and service tokens for at least 8 external services. Additionally, live credentials are embedded in committed documentation files. The API layer has authentication disabled by default and multiple SSRF-capable endpoints with no URL validation.

**Overall Risk Rating: CRITICAL -- Immediate remediation required.**

---

## FINDINGS

### FINDING 1: Production `.env` file contains live credentials for all services

**Severity:** CRITICAL
**File:** `.env`, Lines: 10-206

Live credentials for Anthropic, OpenAI, Apify, Supermemory, Notion, N8N, Supabase (service_role + anon + publishable), Database URLs with password, Neo4j.

**Remediation:** IMMEDIATELY rotate ALL credentials. Verify `.env` not in git history. Use `git rm --cached .env` if tracked. Implement secrets manager.

### FINDING 2: Live Notion token in dashboard `.env` (no gitignore)

**Severity:** CRITICAL
**File:** `dashboard/.env`, Line: 4

`VITE_` prefix exposes token to browser. `dashboard/.gitignore` does NOT exclude `.env` files.

**Remediation:** Add `.env*` to `dashboard/.gitignore`. Remove from tracking. Rotate token. Move Notion calls to backend proxy.

### FINDING 3: Live credentials in committed documentation files

**Severity:** CRITICAL
**Files:** `docs/Claude Exports/*.md`

Notion tokens and Apify tokens in plaintext in 3+ committed markdown files.

**Remediation:** Purge from git history with BFG Repo Cleaner. Replace with placeholders. Rotate tokens. Add pre-commit hook.

### FINDING 4: Supabase service_role key -- full database admin access

**Severity:** CRITICAL
**File:** `.env`, Line: 116

Bypasses ALL RLS policies. Expires 2036. Combined with plaintext DB password = two paths to full compromise.

**Remediation:** Rotate immediately from Supabase dashboard. Rotate DB password. Restrict to server-side only.

### FINDING 5: API authentication disabled by default

**Severity:** CRITICAL
**File:** `Engine8_Knowledge/api.py`, Lines: 178-195 and `api/unified_endpoints.py`, Lines: 60-67

When `BD_API_KEY`/`HUB_API_KEY` is empty (the default), ALL 50+ endpoints are unauthenticated.

**Remediation:** Require keys to be set. Raise startup error if missing. Remove dev-mode skip.

### FINDING 6: SSRF in scrape endpoints

**Severity:** CRITICAL
**File:** `Engine8_Knowledge/api_routers/scrape_api_v2.py`, Lines: 24-27

`/scrape/crawl` accepts arbitrary URLs. Can scan internal network, access cloud metadata.

**Remediation:** URL allowlisting. Block private IPs. Block metadata endpoints. HTTPS only.

### FINDING 7: Path traversal in document processing

**Severity:** CRITICAL
**File:** `Engine8_Knowledge/api_routers/scrape_api_v2.py`, Lines: 86-87

User-supplied `file_path` passed directly with no sanitization.

**Remediation:** Validate within allowed directory. Reject `..` paths. Use document ID system.

### FINDING 8: Wildcard CORS with credentials

**Severity:** HIGH
**File:** `Engine8_Knowledge/api.py`, Lines: 413-418

`allow_methods=["*"]`, `allow_headers=["*"]`, `allow_credentials=True`.

**Remediation:** Explicitly list allowed methods and headers.

### FINDING 9: `ast.literal_eval()` on untrusted CSV data without try/except

**Severity:** HIGH
**File:** `Engine7_BullhornETL/scripts/ingest_new_notes.py`, 10+ call sites

Safe from code execution but crashes entire function on malformed data.

**Remediation:** Replace with `json.loads()`. Add try/except. Add length validation.

### FINDING 10: `DataFrame.eval(expr, engine="python")` on CLI input

**Severity:** HIGH
**File:** `skills/sheetsmith/scripts/sheetsmith.py`, Line: 123

Allows arbitrary Python expression execution.

**Remediation:** Use `engine="numexpr"` (sandboxed). Validate expression allowlist.

### FINDING 11: Real OAuth token in commented-out line

**Severity:** HIGH
**File:** `apps/backend/.env`, Lines: 13-14

**Remediation:** Remove real value. Replace with placeholder. Rotate token.

### FINDING 12: Weak Neo4j password

**Severity:** HIGH
**File:** `.env`, Line: 205 -- `pts_bd_2026`

**Remediation:** Generate strong random password (32+ chars). Remove empty-string default in code.

### FINDING 13: Skill `.env` files with credentials potentially committed

**Severity:** HIGH
**Files:** `skills/mersal-orem/.env`, `skills/nas-master/.env`

**Remediation:** Verify tracking. Remove with `git rm --cached` if tracked.

### FINDING 14: Unauthenticated webhook endpoints

**Severity:** HIGH
**File:** `Engine8_Knowledge/api.py`, Line: 498

**Remediation:** Implement HMAC-SHA256 webhook signature verification.

### FINDING 15: Unauthenticated ingest endpoints (10+)

**Severity:** HIGH
**File:** `Engine8_Knowledge/api.py`, Lines: 1937-2260

Endpoints: `/ingest/document`, `/ingest/program`, `/ingest/programs/batch`, `/ingest/company`, `/ingest/contact`, `/ingest/contacts/batch`, `/ingest/jobs`, `/ingest/scraper-batch`, `/ingest/scraper-bulk`, `/graphiti/ingest`

**Remediation:** Enforce auth on all ingest endpoints. Add input validation. Add audit logging.

### FINDING 16: Notion token in client-side JS via VITE_ prefix

**Severity:** MEDIUM
**File:** `dashboard/src/services/notionApi.ts`, Line: 208

**Remediation:** Backend API proxy for Notion calls.

### FINDING 17: N8N webhook URLs exposed without auth

**Severity:** MEDIUM
**File:** `.env`, Lines: 57-59

**Remediation:** Enable webhook auth in n8n. Rotate URLs.

### FINDING 18: Database password in connection strings

**Severity:** MEDIUM
**File:** `.env`, Lines: 120-124

**Remediation:** Environment variable interpolation. Rotate password.

### FINDING 19: Prior audit report leaks credentials

**Severity:** MEDIUM
**File:** `FULL_PROJECT_AUDIT_2026-02-20.md`, Line: 122

**Remediation:** Redact credential values from audit reports.

### FINDING 20: Neo4j falls back to empty password

**Severity:** MEDIUM
**Files:** `services/graphiti_service.py:42`, `Engine8_Knowledge/graph/neo4j_manager.py:50`

**Remediation:** Raise config error if password empty/unset.

### FINDING 21: No rate limiting

**Severity:** LOW -- 50+ endpoints, no limits.

### FINDING 22: /docs and /redoc auth-exempt

**Severity:** LOW -- Full API schema exposed.

### FINDING 23: Docker dev bind to 0.0.0.0

**Severity:** LOW -- API on all interfaces.

---

## 13 CREDENTIALS REQUIRING IMMEDIATE ROTATION

1. Anthropic API Key
2. OpenAI API Key
3. Apify Token #1
4. Apify Token #2
5. Supermemory API Key
6. Notion Token #1
7. Notion Token #2
8. N8N API Key (JWT)
9. Supabase Service Key
10. Supabase Anon Key
11. Database Password
12. Neo4j Password
13. Claude OAuth Token
