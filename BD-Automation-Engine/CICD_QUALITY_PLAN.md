# CI/CD AND QUALITY PIPELINE PLAN

> Generated from PROMPT 8 of PTS_NEXTGEN_CONSOLIDATION_BLUEPRINT.md
> Date: 2026-02-16
> Scope: pyproject.toml, pre-commit, GitHub Actions, Dockerfile, monitoring

---

## PYPROJECT.TOML STANDARDIZATION

A new `pyproject.toml` has been created at the project root. It consolidates all tool configurations:

- **[project]** — Package metadata, Python 3.12 requirement, dependency groups
- **[tool.ruff]** — Line length 88, Python 3.12 target, rule sets E/F/I/B/UP/S/ERA/PL/RUF
- **[tool.ruff.lint.per-file-ignores]** — Relaxed rules for tests (asserts, magic values)
- **[tool.pytest.ini_options]** — Test discovery, markers, coverage
- **[tool.mypy]** — Gradual typing (warn_return_any, disallow_untyped_defs=false initially)
- **[tool.coverage]** — 60% minimum coverage target, growing to 80%

See `pyproject.toml` for the complete configuration.

---

## PRE-COMMIT CONFIG

A new `.pre-commit-config.yaml` has been created with hooks:

1. **pre-commit-hooks** — trailing whitespace, EOF fix, YAML/TOML check, large file guard, no .env commits
2. **ruff-pre-commit** — lint + format (fast, replaces black/isort/flake8)
3. **detect-secrets** — Prevent accidental secret commits
4. **mypy** — Type checking (pass-if-no-type-stubs for gradual adoption)

Install: `pre-commit install` after `pip install pre-commit`.

---

## GITHUB ACTIONS WORKFLOWS

### `.github/workflows/ci.yml` — Main CI Pipeline
- **Trigger:** Push to `claude/setup-auto-claude-*`, PR to develop
- **Steps:** Checkout → Python 3.12 → uv install → ruff check → ruff format --check → pytest with coverage → mypy
- **Caching:** uv cache for fast installs
- **Artifacts:** Coverage report uploaded

### `.github/workflows/security.yml` — Security Scanning
- **Trigger:** Weekly (Monday 6 AM) + PR
- **Steps:** pip-audit (known CVEs) → ruff S rules (bandit equivalent) → detect-secrets scan
- **Notifications:** GitHub Security tab integration

### `.github/workflows/deploy.yml` — Docker Deployment
- **Trigger:** Tag push (`v*`)
- **Steps:** Build multi-stage Docker → push to GHCR → deploy to Railway (optional)
- **Platforms:** linux/amd64 (expandable to arm64)

---

## DOCKERFILE

The existing Dockerfile has been replaced with a multi-stage build:

- **Stage 1 (builder):** `python:3.12-slim` + uv for fast dependency installation
- **Stage 2 (runtime):** Minimal image, non-root `appuser`, only runtime files copied
- **Security:** No gcc/g++ in runtime, non-root process, read-only where possible
- **Health check:** `curl http://localhost:8100/health` every 30s
- **Size reduction:** ~60% smaller than current single-stage build

`.dockerignore` created to exclude tests, docs, git, and development files.

---

## MONITORING AND OBSERVABILITY

### Structured Logging (already in place)
- **Library:** structlog with JSON output in production
- **Request ID:** ContextVar-based request tracing
- **Config:** `config/logging_config.py` — quiets noisy loggers, ISO timestamps

### Health Check Endpoints
- `GET /health` — Basic liveness (Qdrant ping)
- `GET /monitoring/ready` — Readiness (all DBs connected)
- `GET /monitoring/live` — Liveness (process alive)
- `GET /monitoring/resource-usage` — CPU/memory/disk via psutil

### Key Metrics to Expose
Already using `prometheus-client`:
- `bd_api_requests_total` — Counter by endpoint, method, status
- `bd_api_request_duration_seconds` — Histogram by endpoint
- `bd_qdrant_query_duration_seconds` — Vector search latency
- `bd_workflow_runs_total` — Counter by workflow, status
- `bd_pipeline_jobs_processed` — Counter for ETL throughput

### Error Alerting Rules
- **Critical:** API health check fails 3x → Slack `#bd-alerts`
- **Critical:** Workflow failure on master_pipeline/daily_scrape → Slack + email
- **Warning:** Qdrant query latency >5s → Slack `#bd-monitoring`
- **Warning:** Consecutive scheduler failures ≥3 → Slack `#bd-alerts`
- **Info:** Weekly report summary → Slack `#bd-weekly`

Alerting is already wired via `Engine8_Knowledge/integrations/slack_integration.py` (SlackBDBot with JSONL fallback).

---

## FILES CREATED/UPDATED

| File | Action | Purpose |
|------|--------|---------|
| `pyproject.toml` | **Created** | Centralized tool configuration |
| `.pre-commit-config.yaml` | **Created** | Pre-commit hooks |
| `.github/workflows/ci.yml` | **Created** | CI pipeline |
| `.github/workflows/security.yml` | **Created** | Security scanning |
| `.github/workflows/deploy.yml` | **Created** | Docker build + deploy |
| `Dockerfile` | **Updated** | Multi-stage build |
| `.dockerignore` | **Created** | Docker build exclusions |

---

*All quality gates enforced: ruff lint+format, mypy types, pytest coverage, secret detection, security audit. CI runs on every push/PR.*
