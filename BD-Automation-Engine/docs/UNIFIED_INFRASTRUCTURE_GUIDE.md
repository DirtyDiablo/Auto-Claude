# Master Unification Guide
## Multi-Project Unified Infrastructure for BD Automation, N8N Builder, and Data Scraper

**Version:** 1.0
**Date:** February 1, 2026
**Status:** Draft - Pending Additional Audit Files
**Author:** Claude AI for DirtyDiablo

---

## EXECUTIVE SUMMARY

### The Vision
Create a **unified intelligent infrastructure** that connects three autonomous coding projects:
1. **BD-Automation-Engine** - Business Development intelligence pipeline
2. **N8N Builder** - Workflow automation and orchestration
3. **Data Scraper** - Web data collection and processing

### Current State Analysis

| Project | Vector DB | Embeddings | API Hub | Knowledge Base | Dashboard |
|---------|-----------|------------|---------|----------------|-----------|
| BD-Automation-Engine | Qdrant (configured) | OpenAI ✅ | Partial | Graphiti + Notion | React (in-progress) |
| N8N Builder | TBD | TBD | TBD | TBD | TBD |
| Data Scraper | TBD | TBD | TBD | TBD | TBD |

### Target State

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     UNIFIED INTELLIGENT INFRASTRUCTURE                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                     CENTRAL API HUB (FastAPI)                            │    │
│  │   • Authentication & Rate Limiting                                       │    │
│  │   • Unified REST/GraphQL Endpoints                                       │    │
│  │   • Cross-Project Query Router                                           │    │
│  │   • Webhook Event Distribution                                           │    │
│  └───────────────────────────────┬─────────────────────────────────────────┘    │
│                                  │                                              │
│  ┌───────────────────────────────┼─────────────────────────────────────────┐    │
│  │               SHARED KNOWLEDGE LAYER (Qdrant + Graphiti)                │    │
│  │                                  │                                       │    │
│  │  ┌──────────────────┐  ┌────────┴───────┐  ┌──────────────────┐        │    │
│  │  │  BD-Automation   │  │    UNIFIED     │  │    Data Scraper  │        │    │
│  │  │    Namespace     │  │  KNOWLEDGE     │  │    Namespace     │        │    │
│  │  │                  │  │     GRAPH      │  │                  │        │    │
│  │  │ • Jobs Index     │  │                │  │ • Raw Data Index │        │    │
│  │  │ • Contacts Index │  │  • Entities    │  │ • Source Index   │        │    │
│  │  │ • Programs Index │  │  • Relations   │  │ • Schema Index   │        │    │
│  │  └──────────────────┘  │  • Insights    │  └──────────────────┘        │    │
│  │                        └────────────────┘                              │    │
│  │  ┌──────────────────┐                                                   │    │
│  │  │   N8N Builder    │                                                   │    │
│  │  │    Namespace     │                                                   │    │
│  │  │                  │                                                   │    │
│  │  │ • Workflow Index │                                                   │    │
│  │  │ • Node Index     │                                                   │    │
│  │  │ • Template Index │                                                   │    │
│  │  └──────────────────┘                                                   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                  │                                              │
│  ┌───────────────────────────────┼─────────────────────────────────────────┐    │
│  │                         UNIFIED DASHBOARD                                │    │
│  │   • Multi-Project Data Visualization                                     │    │
│  │   • Cross-Project Search & Discovery                                     │    │
│  │   • Unified Analytics & Reporting                                        │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## PART 1: SHARED INFRASTRUCTURE COMPONENTS

### 1.1 Qdrant Vector Database (Unified Instance)

**Current BD-Automation-Engine Configuration:**
```bash
# From .env.example
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key
```

**Unified Multi-Project Configuration:**

```yaml
# unified-qdrant-config.yaml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"  # gRPC port
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__API_KEY=${QDRANT_API_KEY}
      - QDRANT__SERVICE__ENABLE_TLS=false
    restart: always
```

**Collection Strategy (Multi-Namespace):**

```python
# unified_vector_config.py
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

COLLECTIONS = {
    # BD-Automation-Engine Collections
    "bd_jobs": {
        "size": 1536,  # OpenAI ada-002
        "distance": Distance.COSINE,
        "metadata": ["program", "location", "clearance", "priority"]
    },
    "bd_contacts": {
        "size": 1536,
        "distance": Distance.COSINE,
        "metadata": ["tier", "program", "company", "priority"]
    },
    "bd_programs": {
        "size": 1536,
        "distance": Distance.COSINE,
        "metadata": ["agency", "prime", "value", "status"]
    },

    # N8N Builder Collections
    "n8n_workflows": {
        "size": 1536,
        "distance": Distance.COSINE,
        "metadata": ["category", "nodes", "triggers", "complexity"]
    },
    "n8n_nodes": {
        "size": 1536,
        "distance": Distance.COSINE,
        "metadata": ["type", "integration", "auth_required"]
    },
    "n8n_templates": {
        "size": 1536,
        "distance": Distance.COSINE,
        "metadata": ["use_case", "industry", "complexity"]
    },

    # Data Scraper Collections
    "scraper_sources": {
        "size": 1536,
        "distance": Distance.COSINE,
        "metadata": ["domain", "type", "frequency", "schema"]
    },
    "scraper_data": {
        "size": 1536,
        "distance": Distance.COSINE,
        "metadata": ["source", "timestamp", "schema_version"]
    },

    # Unified Cross-Project Collection
    "unified_knowledge": {
        "size": 1536,
        "distance": Distance.COSINE,
        "metadata": ["project", "entity_type", "relationships"]
    }
}

def initialize_collections(client: QdrantClient):
    """Initialize all collections with proper configuration."""
    for name, config in COLLECTIONS.items():
        client.recreate_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=config["size"],
                distance=config["distance"]
            )
        )
        # Create payload indexes for metadata filtering
        for field in config["metadata"]:
            client.create_payload_index(
                collection_name=name,
                field_name=field,
                field_schema="keyword"
            )
```

### 1.2 OpenAI Embeddings Service (Shared)

**Unified Embedding Service:**

```python
# services/embedding_service.py
import openai
from typing import List, Dict, Optional
from functools import lru_cache
import hashlib
import json

class UnifiedEmbeddingService:
    """
    Shared embedding service for all three projects.
    Implements caching to reduce API costs.
    """

    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self._cache: Dict[str, List[float]] = {}

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text hash."""
        return hashlib.md5(text.encode()).hexdigest()

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding with caching."""
        cache_key = self._get_cache_key(text)

        if cache_key in self._cache:
            return self._cache[cache_key]

        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )

        embedding = response.data[0].embedding
        self._cache[cache_key] = embedding
        return embedding

    def get_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Get embeddings for multiple texts efficiently."""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Check cache first
            cached = []
            to_embed = []
            for text in batch:
                cache_key = self._get_cache_key(text)
                if cache_key in self._cache:
                    cached.append((batch.index(text), self._cache[cache_key]))
                else:
                    to_embed.append(text)

            # Embed uncached texts
            if to_embed:
                response = self.client.embeddings.create(
                    input=to_embed,
                    model=self.model
                )
                for j, emb in enumerate(response.data):
                    text = to_embed[j]
                    cache_key = self._get_cache_key(text)
                    self._cache[cache_key] = emb.embedding

            # Reconstruct batch in order
            batch_embeddings = []
            for text in batch:
                cache_key = self._get_cache_key(text)
                batch_embeddings.append(self._cache[cache_key])

            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    # Project-specific embedding methods
    def embed_job(self, job: Dict) -> List[float]:
        """Embed a BD job posting."""
        text = f"""
        Job Title: {job.get('title', '')}
        Location: {job.get('location', '')}
        Description: {job.get('description', '')}
        Clearance: {job.get('clearance', '')}
        Technologies: {', '.join(job.get('technologies', []))}
        """
        return self.get_embedding(text)

    def embed_contact(self, contact: Dict) -> List[float]:
        """Embed a contact for similarity search."""
        text = f"""
        Name: {contact.get('name', '')}
        Title: {contact.get('job_title', '')}
        Company: {contact.get('company', '')}
        Program: {contact.get('program', '')}
        Location: {contact.get('location', '')}
        """
        return self.get_embedding(text)

    def embed_workflow(self, workflow: Dict) -> List[float]:
        """Embed an n8n workflow."""
        nodes = ', '.join([n.get('type', '') for n in workflow.get('nodes', [])])
        text = f"""
        Workflow: {workflow.get('name', '')}
        Description: {workflow.get('description', '')}
        Nodes: {nodes}
        Tags: {', '.join(workflow.get('tags', []))}
        """
        return self.get_embedding(text)

    def embed_scraper_source(self, source: Dict) -> List[float]:
        """Embed a data scraper source."""
        text = f"""
        Source: {source.get('name', '')}
        URL: {source.get('url', '')}
        Data Type: {source.get('data_type', '')}
        Schema: {json.dumps(source.get('schema', {}))}
        """
        return self.get_embedding(text)
```

### 1.3 Central API Hub (FastAPI)

```python
# api/main.py
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn

from services.embedding_service import UnifiedEmbeddingService
from services.vector_service import UnifiedVectorService
from services.graphiti_service import UnifiedGraphitiService

app = FastAPI(
    title="Unified Project API Hub",
    description="Central API for BD-Automation-Engine, N8N Builder, and Data Scraper",
    version="1.0.0"
)

# CORS for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key security
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key


# ============================================================================
# UNIFIED SEARCH ENDPOINTS
# ============================================================================

class SearchRequest(BaseModel):
    query: str
    projects: List[str] = ["bd", "n8n", "scraper"]  # Filter by project
    entity_types: Optional[List[str]] = None  # jobs, contacts, workflows, etc.
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    project: str
    entity_type: str
    score: float
    data: Dict[str, Any]
    relationships: Optional[List[Dict]] = None

@app.post("/api/v1/search", response_model=List[SearchResult])
async def unified_search(
    request: SearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Unified semantic search across all projects.
    """
    embedding = embedding_service.get_embedding(request.query)
    results = []

    # Search BD-Automation collections
    if "bd" in request.projects:
        for collection in ["bd_jobs", "bd_contacts", "bd_programs"]:
            if request.entity_types and collection.split("_")[1] not in request.entity_types:
                continue
            hits = vector_service.search(
                collection=collection,
                vector=embedding,
                limit=request.limit,
                filters=request.filters
            )
            results.extend([
                SearchResult(
                    project="bd",
                    entity_type=collection.split("_")[1],
                    score=hit.score,
                    data=hit.payload
                ) for hit in hits
            ])

    # Search N8N Builder collections
    if "n8n" in request.projects:
        for collection in ["n8n_workflows", "n8n_nodes", "n8n_templates"]:
            if request.entity_types and collection.split("_")[1] not in request.entity_types:
                continue
            hits = vector_service.search(
                collection=collection,
                vector=embedding,
                limit=request.limit,
                filters=request.filters
            )
            results.extend([
                SearchResult(
                    project="n8n",
                    entity_type=collection.split("_")[1],
                    score=hit.score,
                    data=hit.payload
                ) for hit in hits
            ])

    # Search Data Scraper collections
    if "scraper" in request.projects:
        for collection in ["scraper_sources", "scraper_data"]:
            if request.entity_types and collection.split("_")[1] not in request.entity_types:
                continue
            hits = vector_service.search(
                collection=collection,
                vector=embedding,
                limit=request.limit,
                filters=request.filters
            )
            results.extend([
                SearchResult(
                    project="scraper",
                    entity_type=collection.split("_")[1],
                    score=hit.score,
                    data=hit.payload
                ) for hit in hits
            ])

    # Sort by score and limit
    results.sort(key=lambda x: x.score, reverse=True)
    return results[:request.limit]


# ============================================================================
# BD-AUTOMATION-ENGINE ENDPOINTS
# ============================================================================

@app.get("/api/v1/bd/jobs")
async def get_bd_jobs(
    program: Optional[str] = None,
    priority: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 100,
    api_key: str = Depends(verify_api_key)
):
    """Get BD jobs with optional filtering."""
    filters = {}
    if program:
        filters["program"] = program
    if priority:
        filters["priority"] = priority
    if location:
        filters["location"] = location

    return await bd_service.get_jobs(filters=filters, limit=limit)

@app.get("/api/v1/bd/contacts")
async def get_bd_contacts(
    tier: Optional[int] = None,
    program: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100,
    api_key: str = Depends(verify_api_key)
):
    """Get BD contacts with optional filtering."""
    filters = {}
    if tier:
        filters["tier"] = tier
    if program:
        filters["program"] = program
    if priority:
        filters["priority"] = priority

    return await bd_service.get_contacts(filters=filters, limit=limit)

@app.get("/api/v1/bd/programs")
async def get_bd_programs(
    agency: Optional[str] = None,
    prime: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Get BD programs with optional filtering."""
    return await bd_service.get_programs(agency=agency, prime=prime)

@app.get("/api/v1/bd/playbook")
async def get_daily_playbook(
    date: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Get daily BD playbook."""
    return await bd_service.get_playbook(date=date)


# ============================================================================
# N8N BUILDER ENDPOINTS
# ============================================================================

@app.get("/api/v1/n8n/workflows")
async def get_n8n_workflows(
    category: Optional[str] = None,
    complexity: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Get N8N workflows."""
    return await n8n_service.get_workflows(category=category, complexity=complexity)

@app.post("/api/v1/n8n/workflows/search")
async def search_n8n_workflows(
    query: str,
    limit: int = 10,
    api_key: str = Depends(verify_api_key)
):
    """Semantic search for N8N workflows."""
    embedding = embedding_service.get_embedding(query)
    return await vector_service.search("n8n_workflows", embedding, limit=limit)


# ============================================================================
# DATA SCRAPER ENDPOINTS
# ============================================================================

@app.get("/api/v1/scraper/sources")
async def get_scraper_sources(
    domain: Optional[str] = None,
    data_type: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Get data scraper sources."""
    return await scraper_service.get_sources(domain=domain, data_type=data_type)

@app.post("/api/v1/scraper/trigger")
async def trigger_scraper(
    source_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Trigger a scraper run."""
    return await scraper_service.trigger_scrape(source_id)


# ============================================================================
# CROSS-PROJECT INTELLIGENCE
# ============================================================================

@app.get("/api/v1/intelligence/relationships")
async def get_entity_relationships(
    entity_id: str,
    project: str,
    depth: int = 2,
    api_key: str = Depends(verify_api_key)
):
    """Get knowledge graph relationships for an entity."""
    return await graphiti_service.get_relationships(
        entity_id=entity_id,
        project=project,
        depth=depth
    )

@app.post("/api/v1/intelligence/insights")
async def add_insight(
    insight: Dict[str, Any],
    project: str,
    api_key: str = Depends(verify_api_key)
):
    """Add an insight to the unified knowledge graph."""
    return await graphiti_service.add_insight(insight, project)


# ============================================================================
# WEBHOOK ENDPOINTS (for N8N integration)
# ============================================================================

@app.post("/api/v1/webhooks/bd/job-import")
async def webhook_job_import(payload: Dict[str, Any]):
    """Webhook for importing jobs from Apify/N8N."""
    return await bd_service.import_jobs(payload)

@app.post("/api/v1/webhooks/scraper/data-ready")
async def webhook_scraper_data_ready(payload: Dict[str, Any]):
    """Webhook when scraper has new data."""
    return await scraper_service.process_new_data(payload)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 1.4 Unified Environment Configuration

```bash
# unified.env - Master environment file

# ============================================================================
# SHARED SERVICES
# ============================================================================

# Qdrant Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-unified-qdrant-api-key

# OpenAI (for embeddings)
OPENAI_API_KEY=your-openai-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Anthropic (for AI operations)
ANTHROPIC_API_KEY=your-anthropic-api-key

# Unified API Hub
UNIFIED_API_URL=http://localhost:8000
UNIFIED_API_KEY=your-unified-api-key

# Graphiti Memory System
GRAPHITI_ENABLED=true
GRAPHITI_DB_PATH=./unified_knowledge_graph

# ============================================================================
# BD-AUTOMATION-ENGINE
# ============================================================================

# Notion Integration
NOTION_TOKEN=secret_your-notion-token
NOTION_DB_DCGS_CONTACTS=2ccdef65-baa5-8087-a53b-000ba596128e
NOTION_DB_GDIT_JOBS=2563119e7914442cbe0fb86904a957a1
NOTION_DB_PROGRAM_MAPPING_HUB=f57792c1-605b-424c-8830-23ab41c47137
NOTION_DB_FEDERAL_PROGRAMS=06cd9b22-5d6b-4d37-b0d3-ba99da4971fa
NOTION_DB_BD_OPPORTUNITIES=2bcdef65-baa5-80ed-bd95-000b2f898e17

# Apify (for job scraping)
APIFY_API_TOKEN=your-apify-token

# N8N Integration
N8N_WEBHOOK_URL=https://your-n8n-instance/webhook/job-data-intake
N8N_API_KEY=your-n8n-api-key
N8N_API_URL=https://your-n8n-instance/api/v1

# BD Scoring
BD_SCORE_BASE=50
BD_TIER_HOT_MIN=80
BD_TIER_WARM_MIN=50

# ============================================================================
# N8N BUILDER
# ============================================================================

N8N_BUILDER_DB_PATH=./n8n_builder_data
N8N_TEMPLATE_DIR=./n8n_templates
N8N_WORKFLOW_EXPORT_DIR=./n8n_exports

# ============================================================================
# DATA SCRAPER
# ============================================================================

SCRAPER_OUTPUT_DIR=./scraper_outputs
SCRAPER_CACHE_DIR=./scraper_cache
SCRAPER_MAX_CONCURRENT=5
SCRAPER_DEFAULT_DELAY=2

# Proxy Configuration (optional)
PROXY_URL=
PROXY_USERNAME=
PROXY_PASSWORD=

# ============================================================================
# UNIFIED DASHBOARD
# ============================================================================

DASHBOARD_PORT=5173
DASHBOARD_API_BASE=http://localhost:8000/api/v1

# ============================================================================
# LOGGING & MONITORING
# ============================================================================

LOG_LEVEL=INFO
LOG_FILE=./logs/unified_system.log
ENABLE_METRICS=true
METRICS_PORT=9090
```

---

## PART 2: PROJECT-SPECIFIC INDEXING

### 2.1 BD-Automation-Engine Indexing (COMPLETED)

Based on your enrichment state, the following has been indexed:
- **7,602 contacts** across 3 databases (DCGS, GDIT Other, GDIT PTS)
- **2 jobs** with full BD context
- **3 BD Opportunities** with priority scoring

**Next Steps for BD:**
```bash
# Index remaining entities
cd BD-Automation-Engine

# 1. Index Federal Programs (388 programs)
python scripts/index_programs.py --collection bd_programs

# 2. Index all jobs from Notion
python scripts/index_jobs.py --collection bd_jobs

# 3. Create cross-reference relationships
python scripts/create_relationships.py
```

### 2.2 N8N Builder Indexing (TODO)

**Data to Index:**
```python
# n8n_indexing.py
N8N_INDEX_TARGETS = {
    "workflows": {
        "source": "n8n/",  # All workflow JSON files
        "fields": ["name", "description", "nodes", "connections"],
        "count_estimate": "17+ workflows"
    },
    "nodes": {
        "source": "workflows.nodes[]",
        "fields": ["type", "parameters", "credentials"],
        "count_estimate": "~200 node configurations"
    },
    "templates": {
        "source": "templates/",
        "fields": ["use_case", "industry", "complexity", "nodes"],
        "count_estimate": "TBD"
    }
}
```

**Indexing Script Template:**
```python
# scripts/index_n8n.py
import json
from pathlib import Path
from services.embedding_service import UnifiedEmbeddingService
from services.vector_service import UnifiedVectorService

def index_n8n_workflows(workflow_dir: str):
    """Index all N8N workflow files."""
    embedding_service = UnifiedEmbeddingService(api_key=os.getenv("OPENAI_API_KEY"))
    vector_service = UnifiedVectorService(url=os.getenv("QDRANT_URL"))

    workflow_files = Path(workflow_dir).glob("*.json")

    for file in workflow_files:
        with open(file) as f:
            workflow = json.load(f)

        # Generate embedding
        embedding = embedding_service.embed_workflow(workflow)

        # Extract metadata
        nodes = [n.get("type", "") for n in workflow.get("nodes", [])]

        # Store in Qdrant
        vector_service.upsert(
            collection="n8n_workflows",
            id=workflow.get("id", file.stem),
            vector=embedding,
            payload={
                "name": workflow.get("name"),
                "description": workflow.get("description", ""),
                "nodes": nodes,
                "node_count": len(nodes),
                "category": classify_workflow(workflow),
                "complexity": calculate_complexity(workflow),
                "file_path": str(file)
            }
        )
```

### 2.3 Data Scraper Indexing (TODO)

**Data to Index:**
```python
# scraper_indexing.py
SCRAPER_INDEX_TARGETS = {
    "sources": {
        "description": "Data source configurations",
        "fields": ["url", "domain", "schema", "frequency"],
        "count_estimate": "TBD"
    },
    "schemas": {
        "description": "Data extraction schemas",
        "fields": ["fields", "validation_rules", "transformations"],
        "count_estimate": "TBD"
    },
    "extracted_data": {
        "description": "Sample extracted data for search",
        "fields": ["content_summary", "source", "timestamp"],
        "count_estimate": "TBD"
    }
}
```

---

## PART 3: UNIFIED DASHBOARD ARCHITECTURE

### 3.1 Dashboard Design

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🔮 UNIFIED INTELLIGENCE DASHBOARD                            [Search] [Settings]│
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  🔍 UNIFIED SEARCH                                                       │    │
│  │  [Search across all projects...                               ] [🔍]     │    │
│  │                                                                          │    │
│  │  Projects: [✓] BD-Automation [✓] N8N Builder [✓] Data Scraper           │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌──────────────────────────┐  ┌──────────────────────────┐                     │
│  │  📊 BD-AUTOMATION         │  │  ⚙️ N8N BUILDER           │                     │
│  │  ─────────────────────   │  │  ─────────────────────   │                     │
│  │  Jobs: 127 active        │  │  Workflows: 17           │                     │
│  │  Contacts: 7,602         │  │  Templates: 25           │                     │
│  │  Programs: 388           │  │  Active: 8               │                     │
│  │  Hot Leads: 23           │  │  Scheduled: 12           │                     │
│  │                          │  │                          │                     │
│  │  [Open Dashboard →]      │  │  [Open Dashboard →]      │                     │
│  └──────────────────────────┘  └──────────────────────────┘                     │
│                                                                                  │
│  ┌──────────────────────────┐  ┌──────────────────────────┐                     │
│  │  🔄 DATA SCRAPER          │  │  🧠 KNOWLEDGE GRAPH       │                     │
│  │  ─────────────────────   │  │  ─────────────────────   │                     │
│  │  Sources: 12             │  │  Entities: 8,234         │                     │
│  │  Last Run: 2h ago        │  │  Relations: 12,456       │                     │
│  │  Records Today: 234      │  │  Insights: 89            │                     │
│  │  Queue: 5 pending        │  │  Cross-Project: 156      │                     │
│  │                          │  │                          │                     │
│  │  [Open Dashboard →]      │  │  [View Graph →]          │                     │
│  └──────────────────────────┘  └──────────────────────────┘                     │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  📈 CROSS-PROJECT INSIGHTS                                               │    │
│  │                                                                          │    │
│  │  Recent Connections:                                                     │    │
│  │  • Job "Network Engineer" → Workflow "Job Import Pipeline" (95% match)  │    │
│  │  • Contact "Kingsley Ero" → Data Source "LinkedIn Scraper" (87% match)  │    │
│  │  • Program "AF DCGS" → Template "BD Automation" (92% match)             │    │
│  │                                                                          │    │
│  │  [View All Insights →]                                                   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Unified Dashboard Routes

```typescript
// dashboard/src/App.tsx
const routes = [
  // Unified views
  { path: "/", component: UnifiedDashboard },
  { path: "/search", component: UnifiedSearch },
  { path: "/knowledge-graph", component: KnowledgeGraph },

  // BD-Automation-Engine
  { path: "/bd", component: BDDashboard },
  { path: "/bd/jobs", component: JobsTab },
  { path: "/bd/contacts", component: ContactsTab },
  { path: "/bd/programs", component: ProgramsTab },
  { path: "/bd/playbook", component: PlaybookTab },

  // N8N Builder
  { path: "/n8n", component: N8NDashboard },
  { path: "/n8n/workflows", component: WorkflowsTab },
  { path: "/n8n/templates", component: TemplatesTab },
  { path: "/n8n/nodes", component: NodesTab },

  // Data Scraper
  { path: "/scraper", component: ScraperDashboard },
  { path: "/scraper/sources", component: SourcesTab },
  { path: "/scraper/data", component: DataTab },
  { path: "/scraper/schedules", component: SchedulesTab },

  // Settings
  { path: "/settings", component: UnifiedSettings },
  { path: "/settings/api", component: APISettings },
  { path: "/settings/integrations", component: IntegrationsSettings },
];
```

---

## PART 4: IMPLEMENTATION PHASES

### Phase 1: Foundation (Week 1-2)

**Objective:** Establish shared infrastructure

| Task | Description | Deliverable |
|------|-------------|-------------|
| 1.1 | Deploy unified Qdrant instance | `docker-compose.yml` |
| 1.2 | Create shared embedding service | `services/embedding_service.py` |
| 1.3 | Set up unified API hub skeleton | `api/main.py` |
| 1.4 | Configure unified environment | `unified.env` |
| 1.5 | Set up Graphiti knowledge graph | `services/graphiti_service.py` |

### Phase 2: BD-Automation Enhancement (Week 3-4)

**Objective:** Complete BD indexing and enhance dashboard

| Task | Description | Deliverable |
|------|-------------|-------------|
| 2.1 | Index all Federal Programs | 388 programs in Qdrant |
| 2.2 | Index all job postings | Jobs in Qdrant |
| 2.3 | Create program-contact relationships | Knowledge graph edges |
| 2.4 | Complete BD Dashboard tabs | Working 8-tab dashboard |
| 2.5 | Implement BD Formula generator | `scripts/bd_formula_generator.py` |

### Phase 3: N8N Builder Integration (Week 5-6)

**Objective:** Index N8N Builder and add to unified system

| Task | Description | Deliverable |
|------|-------------|-------------|
| 3.1 | Audit N8N Builder project | Inventory of indexable data |
| 3.2 | Index all workflows | Workflows in Qdrant |
| 3.3 | Index node configurations | Nodes in Qdrant |
| 3.4 | Create N8N → BD relationships | Cross-project connections |
| 3.5 | Add N8N section to unified dashboard | `/n8n/*` routes |

### Phase 4: Data Scraper Integration (Week 7-8)

**Objective:** Index Data Scraper and complete unification

| Task | Description | Deliverable |
|------|-------------|-------------|
| 4.1 | Audit Data Scraper project | Inventory of indexable data |
| 4.2 | Index scraper sources | Sources in Qdrant |
| 4.3 | Index extracted data samples | Data in Qdrant |
| 4.4 | Create Scraper → BD relationships | Job source tracking |
| 4.5 | Add Scraper section to unified dashboard | `/scraper/*` routes |

### Phase 5: Unified Intelligence (Week 9-10)

**Objective:** Enable cross-project intelligence

| Task | Description | Deliverable |
|------|-------------|-------------|
| 5.1 | Implement unified search | Cross-project semantic search |
| 5.2 | Build knowledge graph visualizations | Interactive graph view |
| 5.3 | Create cross-project insights | Auto-generated insights |
| 5.4 | Deploy unified dashboard | Production deployment |
| 5.5 | Documentation and training | Complete user guide |

---

## PART 5: EXECUTION GUIDE

### Step 1: Set Up Unified Qdrant

```bash
# 1. Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__API_KEY=${QDRANT_API_KEY}
    restart: always
EOF

# 2. Start Qdrant
docker-compose up -d qdrant

# 3. Verify
curl http://localhost:6333/collections
```

### Step 2: Initialize Collections

```bash
# 1. Navigate to project
cd BD-Automation-Engine

# 2. Create initialization script
python scripts/init_unified_collections.py

# 3. Verify collections
curl http://localhost:6333/collections | jq
```

### Step 3: Index BD-Automation Data

```bash
# 1. Index Federal Programs
python scripts/index_programs.py \
  --source Engine2_ProgramMapping/data/Programs_KB.csv \
  --collection bd_programs

# 2. Index Jobs
python scripts/index_jobs.py \
  --source "outputs/*.json" \
  --collection bd_jobs

# 3. Re-index Contacts (already enriched)
python scripts/index_contacts.py \
  --source "outputs/contacts_enriched.json" \
  --collection bd_contacts

# 4. Verify
python scripts/verify_indexes.py
```

### Step 4: Start Unified API Hub

```bash
# 1. Install dependencies
pip install fastapi uvicorn qdrant-client openai python-dotenv

# 2. Create API server
# (Use the main.py template from Part 1.3)

# 3. Start server
uvicorn api.main:app --reload --port 8000

# 4. Test endpoints
curl http://localhost:8000/docs
```

### Step 5: Set Up Unified Dashboard

```bash
# 1. Extend existing BD dashboard
cd BD-Automation-Engine/dashboard

# 2. Add unified routes
# Update src/App.tsx with unified routes

# 3. Add unified search component
# Create src/components/UnifiedSearch.tsx

# 4. Start dashboard
npm run dev
```

### Step 6: Index N8N Builder (After Audit)

```bash
# (Pending N8N Builder audit file)

# 1. Navigate to N8N Builder
cd "C:\N8N Builder"

# 2. Export all workflows to JSON
# (Method depends on N8N Builder structure)

# 3. Index workflows
python scripts/index_n8n.py \
  --source workflows/*.json \
  --collection n8n_workflows
```

### Step 7: Index Data Scraper (After Audit)

```bash
# (Pending Data Scraper audit file)

# 1. Navigate to Data Scraper
cd "C:\data-scraper\data-scraper"

# 2. Export source configurations
# (Method depends on Data Scraper structure)

# 3. Index sources
python scripts/index_scraper.py \
  --source sources/*.json \
  --collection scraper_sources
```

### Step 8: Create Cross-Project Relationships

```bash
# 1. Create relationship builder
python scripts/build_relationships.py \
  --bd-contacts bd_contacts \
  --bd-jobs bd_jobs \
  --n8n-workflows n8n_workflows \
  --scraper-sources scraper_sources

# 2. Verify knowledge graph
python scripts/verify_knowledge_graph.py
```

### Step 9: Deploy Unified System

```bash
# 1. Build dashboard for production
cd dashboard && npm run build

# 2. Deploy API (example with PM2)
pm2 start api/main.py --interpreter python3 --name unified-api

# 3. Deploy dashboard
pm2 start npm --name unified-dashboard -- start

# 4. Verify deployment
curl http://localhost:8000/api/v1/search -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"query": "network engineer DCGS", "projects": ["bd", "n8n"]}'
```

---

## APPENDIX A: REQUIRED AUDIT FILES

To complete this guide, please provide the following audit files:

1. **DEEP_AUDIT_BD-Automation-Engine.md** - Full BD engine analysis
2. **BD_DASHBOARD_FULL_AUDIT.md** - Dashboard-specific analysis
3. **DEEP_AUDIT_N8N_BUILDER.md** - N8N Builder analysis (CRITICAL)
4. **DEEP_AUDIT_DATA-SCRAPER.md** - Data Scraper analysis (CRITICAL)
5. **compass_artifact_*.md** - Unified infrastructure research
6. **repo-tools-capabilities-matrix.md** - Tool capabilities analysis

### How to Share

**Option 1:** Copy files to this repo
```bash
mkdir -p /home/user/Auto-Claude/audits
# Copy files from Windows to audits/
```

**Option 2:** Paste contents directly in chat

**Option 3:** Upload files through your interface

---

## APPENDIX B: TECHNOLOGY STACK SUMMARY

| Component | Technology | Purpose |
|-----------|------------|---------|
| Vector DB | Qdrant | Semantic search across all projects |
| Embeddings | OpenAI ada-002 | Text-to-vector conversion |
| API Hub | FastAPI | Central REST/GraphQL endpoint |
| Knowledge Graph | Graphiti/LadybugDB | Cross-project relationships |
| Dashboard | React + TypeScript + Vite | Unified visualization |
| Orchestration | N8N | Workflow automation |
| Data Storage | Notion | BD operational data |
| AI Operations | Anthropic Claude | LLM processing |

---

## DOCUMENT CONTROL

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-01 | Claude AI | Initial draft based on BD-Automation-Engine analysis |

**NEXT VERSION:** Will include N8N Builder and Data Scraper specifics once audit files are provided.

---

**END OF UNIFIED INFRASTRUCTURE GUIDE v1.0**
