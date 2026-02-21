#!/usr/bin/env bash
# BD Intelligence Hub — Docker Entrypoint
# Feature 14: Production Deployment
#
# Usage:
#   docker-entrypoint.sh serve    — Start the API server (default)
#   docker-entrypoint.sh worker   — Start the workflow scheduler
#   docker-entrypoint.sh migrate  — Run Alembic migrations only
#   docker-entrypoint.sh shell    — Drop into a Python shell

set -euo pipefail

# ── Validate required environment variables ────────────────
validate_env() {
    local missing=()

    if [ -z "${OPENAI_API_KEY:-}" ]; then
        missing+=("OPENAI_API_KEY")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        echo "ERROR: Required environment variables are not set:"
        for var in "${missing[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Set them in your .env file or pass via docker compose environment."
        exit 1
    fi
}

# ── Run Alembic migrations if DATABASE_URL is set ──────────
run_migrations() {
    if [ -n "${DATABASE_URL:-}" ]; then
        echo "Running Alembic migrations..."
        cd /app
        python -m alembic -c migrations/alembic.ini upgrade head
        echo "Migrations complete."
    else
        echo "DATABASE_URL not set — skipping migrations."
    fi
}

# ── Main entrypoint logic ──────────────────────────────────
COMMAND="${1:-serve}"

case "$COMMAND" in
    serve)
        validate_env
        run_migrations
        echo "Starting BD Intelligence Hub API on port ${API_PORT:-8100}..."
        exec python -m uvicorn Engine8_Knowledge.api:app \
            --host "${API_HOST:-0.0.0.0}" \
            --port "${API_PORT:-8100}" \
            --workers "${WORKERS:-2}" \
            --log-level "${LOG_LEVEL:-info}"
        ;;
    worker)
        validate_env
        echo "Starting workflow scheduler..."
        exec python -m workflows.scheduler
        ;;
    migrate)
        run_migrations
        ;;
    shell)
        exec python
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Usage: docker-entrypoint.sh {serve|worker|migrate|shell}"
        exit 1
        ;;
esac
