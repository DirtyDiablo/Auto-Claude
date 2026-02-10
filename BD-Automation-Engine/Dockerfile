# BD Intelligence Hub API - Docker Image
# Phase 20A

FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY Engine8_Knowledge/ ./Engine8_Knowledge/
COPY Engine2_ProgramMapping/ ./Engine2_ProgramMapping/
COPY Engine3_OrgChart/ ./Engine3_OrgChart/
COPY Engine5_Scoring/ ./Engine5_Scoring/
COPY Engine7_BullhornETL/ ./Engine7_BullhornETL/
COPY data/ ./data/

# Create data directories
RUN mkdir -p /app/Engine8_Knowledge/data/automation \
    /app/Engine8_Knowledge/data/embeddings \
    /app/Engine8_Knowledge/data/models

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV API_HOST=0.0.0.0
ENV API_PORT=8100

EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8100/health || exit 1

CMD ["python", "-m", "uvicorn", "Engine8_Knowledge.api:app", "--host", "0.0.0.0", "--port", "8100"]
