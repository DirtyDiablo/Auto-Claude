# BD Intelligence Hub API — Multi-stage Docker Build
# Feature 14: Production Deployment
#
# Stage 1: Install dependencies with uv (fast resolver)
# Stage 2: Minimal runtime image with non-root user

# ── Stage 1: Builder ─────────────────────────────────────
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

COPY requirements.txt ./
RUN uv venv /build/.venv \
    && uv pip install --python /build/.venv/bin/python \
       --no-cache -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user
RUN groupadd -r bduser && useradd -r -g bduser -d /app bduser

# Minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY Engine8_Knowledge/ ./Engine8_Knowledge/
COPY Engine2_ProgramMapping/ ./Engine2_ProgramMapping/
COPY Engine3_OrgChart/ ./Engine3_OrgChart/
COPY Engine5_Scoring/ ./Engine5_Scoring/
COPY Engine7_BullhornETL/ ./Engine7_BullhornETL/
COPY api/ ./api/
COPY config/ ./config/
COPY services/ ./services/
COPY utils/ ./utils/
COPY workflows/ ./workflows/
COPY migrations/ ./migrations/
COPY orchestrator.py ./orchestrator.py

# Copy entrypoint script
COPY scripts/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Create data directories
RUN mkdir -p /app/Engine8_Knowledge/data/automation \
    /app/Engine8_Knowledge/data/embeddings \
    /app/Engine8_Knowledge/data/models \
    /app/data \
    /app/logs \
    && chown -R bduser:bduser /app

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV API_HOST=0.0.0.0
ENV API_PORT=8100
ENV WORKERS=2

EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8100/health || exit 1

USER bduser

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["serve"]
