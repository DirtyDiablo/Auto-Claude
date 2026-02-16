# BD-Automation-Engine — Shared Library Extraction Plan

**Phase 3 Preparation | Generated 2026-02-16**
**Based on:** AUDIT_REPORT.md + nextgenresearchanalysis.md (Repository Pattern, monorepo structure)

---

## Target Monorepo Structure

```
unified-platform/
├── pyproject.toml              # Root workspace config (uv workspace)
├── uv.lock                     # Single lockfile
├── services/
│   ├── bd-automation/          # BD-Automation-Engine (this repo)
│   ├── n8n-builder/            # N8N-Builder
│   └── data-scraper/           # Data-Scraper
├── libs/
│   ├── shared-core/            # Common FastAPI, config, logging
│   ├── db-layer/               # Repository pattern: Qdrant, SQLite, Neo4j
│   ├── bullhorn-client/        # Bullhorn CRM integration
│   └── slack-utils/            # Shared Slack utilities
└── infra/                      # Docker, CI/CD configs
```

---

## libs/shared-core/ (Common FastAPI, config, logging)

### Configuration Management

| Current Location | Class/Function | What It Does | Dependents | Target Path |
|-----------------|----------------|-------------|------------|-------------|
| `config/settings.py` | `Settings(BaseSettings)` | Pydantic BaseSettings with all env vars (API keys, DB URLs, Notion IDs, scoring thresholds) | `api/unified_endpoints.py`, `scripts/verify_pipeline.py`, `tests/test_integration.py`, `config/__init__.py` | `libs/shared-core/src/shared_core/config/settings.py` |
| `config/settings.py` | `get_settings()` | `@lru_cache` singleton factory for Settings | Same as above | `libs/shared-core/src/shared_core/config/settings.py` |
| `config/logging_config.py` | `setup_logging()`, `get_logger()` | Structured logging setup with JSON/console formatters | Indirectly by ~80 files via `logging.getLogger(__name__)` | `libs/shared-core/src/shared_core/config/logging.py` |
| `config/resilience.py` | Retry/circuit breaker decorators | Tenacity-based retry patterns | Currently unused (0 imports found) | `libs/shared-core/src/shared_core/utils/resilience.py` |

### FastAPI App Factory / Middleware

| Current Location | Class/Function | What It Does | Dependents | Target Path |
|-----------------|----------------|-------------|------------|-------------|
| `simple_knowledge_api.py:1-30` | `app = FastAPI(...)` | Main app creation with CORS, title, description | Standalone server entry point | `libs/shared-core/src/shared_core/api/factory.py` |
| `Engine8_Knowledge/api.py:359` | `app = FastAPI(...)` | Extended app with 40+ router mounts | Engine8 extended API | `libs/shared-core/src/shared_core/api/factory.py` |
| `api/unified_endpoints.py:37-48` | `api_key_header`, `verify_api_key()` | API key auth via `X-API-Key` header | All `/api/v2/*` routes | `libs/shared-core/src/shared_core/api/auth.py` |
| `simple_knowledge_api.py` | CORS middleware config | `allow_origins=["*"]` (wide open) | All API consumers | `libs/shared-core/src/shared_core/api/middleware.py` |

**Proposed Factory Pattern:**
```python
# libs/shared-core/src/shared_core/api/factory.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app(
    title: str = "BD Intelligence API",
    version: str = "2.0.0",
    allowed_origins: list[str] | None = None,
    enable_auth: bool = False,
) -> FastAPI:
    app = FastAPI(title=title, version=version)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if enable_auth:
        from .auth import api_key_middleware
        app.middleware("http")(api_key_middleware)
    return app
```

### Common Utilities

| Current Location | Function | What It Does | Dependents | Target Path |
|-----------------|----------|-------------|------------|-------------|
| `utils/llm_retry.py` | `openai_retry` decorator | Retry wrapper for OpenAI API calls with exponential backoff | `api/unified_endpoints.py` | `libs/shared-core/src/shared_core/utils/retry.py` |
| `api/unified_endpoints.py:57-60` | `get_embedding()` | OpenAI text-embedding-3-small (1536-dim) | 40+ files across Engine8 indexers, API search | `libs/shared-core/src/shared_core/utils/embeddings.py` |
| 80+ files | `logging.getLogger(__name__)` | Standard Python logging pattern | Nearly every module | `libs/shared-core/src/shared_core/utils/logging.py` |
| Multiple Engine scripts | `Path(__file__).parent.parent` | Project root resolution | 160+ files | `libs/shared-core/src/shared_core/utils/paths.py` |

**Proposed Embedding Utility:**
```python
# libs/shared-core/src/shared_core/utils/embeddings.py
from openai import OpenAI
from functools import lru_cache
from .retry import openai_retry

@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    return OpenAI()

@openai_retry
def get_embedding(
    text: str,
    model: str = "text-embedding-3-small",
    dimensions: int = 1536,
) -> list[float]:
    client = _get_client()
    response = client.embeddings.create(input=[text], model=model, dimensions=dimensions)
    return response.data[0].embedding
```

### Base Pydantic Models

| Current Location | Class | What It Does | Dependents | Target Path |
|-----------------|-------|-------------|------------|-------------|
| `models/base.py` | `BaseDocument(BaseModel)` | Base model with id, source_project, timestamps, content_hash, tags | All 4 domain models | `libs/shared-core/src/shared_core/models/base.py` |
| `models/base.py` | `SourceProject(Enum)` | BD_ENGINE, DATA_SCRAPER, N8N_BUILDER | `BaseDocument` | `libs/shared-core/src/shared_core/models/base.py` |
| *(missing)* | Pagination model | Not yet implemented — needed for API responses | Would be used by all search endpoints | `libs/shared-core/src/shared_core/models/pagination.py` |
| *(missing)* | ErrorResponse model | Not yet implemented — needed for structured errors | Would be used by all API routes | `libs/shared-core/src/shared_core/models/errors.py` |

**Proposed Pagination Model:**
```python
# libs/shared-core/src/shared_core/models/pagination.py
from pydantic import BaseModel

class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False
```

### shared-core Package Structure

```
libs/shared-core/
├── pyproject.toml
└── src/shared_core/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   ├── factory.py          # create_app() FastAPI factory
    │   ├── auth.py             # API key verification, auth middleware
    │   └── middleware.py       # CORS, request logging, error handling
    ├── config/
    │   ├── __init__.py
    │   ├── settings.py         # Pydantic BaseSettings (all env vars)
    │   └── logging.py          # Structured logging setup
    ├── models/
    │   ├── __init__.py
    │   ├── base.py             # BaseDocument, SourceProject enum
    │   ├── pagination.py       # PaginatedResponse[T]
    │   └── errors.py           # ErrorResponse, ValidationErrorDetail
    └── utils/
        ├── __init__.py
        ├── embeddings.py       # get_embedding() with model selection
        ├── retry.py            # openai_retry, generic retry decorators
        ├── paths.py            # Project root resolution helpers
        └── resilience.py       # Circuit breaker, rate limiter
```

---

## libs/db-layer/ (Repository Pattern: Qdrant, SQLite, Neo4j)

### Current Database Access Patterns

#### Qdrant (54+ connection points)

| Current Location | Connection Pattern | Collections Accessed |
|-----------------|-------------------|---------------------|
| `simple_knowledge_api.py` | `QdrantClient(url=QDRANT_URL)` inline | contacts, programs, documents, activities, jobs |
| `Engine8_Knowledge/scripts/vector_store.py` | `BDKnowledgeStore` class wrapping `QdrantClient` | All 6 collections |
| `api/unified_endpoints.py:51-54` | `get_qdrant()` dependency injection function | All collections via `/api/v2/*` |
| `Engine8_Knowledge/scripts/index_*.py` (12+ files) | Direct `QdrantClient(url=...)` inline | Individual collections per indexer |
| `Engine8_Knowledge/scripts/indexer.py` | `QdrantClient` in `IndexEngine` class | contacts, programs, jobs |
| `dify_integration/dify_qdrant_bridge.py` | `DifyQdrantBridge` class wrapping `QdrantClient` | All collections |
| `mcp/knowledge-mcp-server/server.py` | Direct `QdrantClient(url=...)` inline | contacts, programs |

**Problem:** 54+ files create their own `QdrantClient` instances. No connection pooling, no shared configuration, URL hardcoded in many places.

#### SQLite (40+ connection points)

| Current Location | Connection Pattern | Database |
|-----------------|-------------------|----------|
| `Engine7_BullhornETL/scripts/database_schema.py:426` | `get_connection()` factory function | `bullhorn_master.db` |
| `Engine7_BullhornETL/scripts/*.py` (20+ files) | Direct `sqlite3.connect(DB_PATH)` inline | `bullhorn_master.db` |
| `Engine8_Knowledge/scripts/memory_system.py` | Direct `sqlite3.connect()` | `memories.db` |
| `Engine8_Knowledge/retrieval/page_index.py` | Direct `sqlite3.connect()` | `page_index.db` |
| `Engine8_Knowledge/graph/bd_knowledge_graph.py` | Direct `sqlite3.connect()` | Graph metadata |

**Problem:** 40+ files construct their own SQLite connections. Path computation repeated everywhere with `Path(__file__).parent.parent / "data" / "db.db"`.

#### Neo4j (1 connection point, well-structured)

| Current Location | Connection Pattern | Purpose |
|-----------------|-------------------|---------|
| `Engine8_Knowledge/graph/neo4j_manager.py:79-123` | `Neo4jManager` class with driver pooling (50 connections) | Graph queries, schema management |
| `Engine8_Knowledge/graph/ingestion.py` | Uses `Neo4jManager` via constructor injection | Bulk data ingestion |
| `Engine8_Knowledge/graph/queries.py` | Uses `Neo4jManager` via constructor injection | Pre-built Cypher queries |
| `Engine8_Knowledge/graph/schema.py` | Uses `Neo4jManager` via function parameter | Schema/index management |

**Good pattern:** Neo4j already uses a proper manager class. Needs minimal refactoring.

#### Redis (2 connection points)

| Current Location | Connection Pattern | Purpose |
|-----------------|-------------------|---------|
| `Engine8_Knowledge/scripts/redis_cache.py:26` | Direct `redis.Redis(url=...)` | Caching layer |
| `src/streaming/event_bus.py:48` | `redis.asyncio` | Event streaming |

### Target Repository Pattern

```python
# libs/db-layer/src/db_layer/base.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar("T")
TCreate = TypeVar("TCreate")
TUpdate = TypeVar("TUpdate")

class EntityRepository(ABC, Generic[T, TCreate, TUpdate]):
    @abstractmethod
    async def get_by_id(self, id: str) -> T | None: ...

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> list[T]: ...

    @abstractmethod
    async def create(self, entity: TCreate) -> T: ...

    @abstractmethod
    async def update(self, id: str, entity: TUpdate) -> T: ...

    @abstractmethod
    async def delete(self, id: str) -> bool: ...

    @abstractmethod
    async def list(self, offset: int = 0, limit: int = 20) -> tuple[list[T], int]: ...
```

### Concrete Repository Implementations

#### ContactRepository

| Current Location | Method | Target |
|-----------------|--------|--------|
| `simple_knowledge_api.py` `/contacts/search` handler | `search_contacts()` — Qdrant vector search | `QdrantContactRepo.search()` |
| `Engine8_Knowledge/scripts/vector_store.py` | `BDKnowledgeStore.search_contacts()` | `QdrantContactRepo.search()` |
| `Engine7_BullhornETL/scripts/database_schema.py` | `SELECT * FROM candidates` | `SqliteContactRepo.get_by_id()`, `.list()` |
| `Engine3_OrgChart/scripts/contact_classifier.py` | `classify_contact()` — regex classification | `ContactService.classify()` (not repo, domain logic) |
| `Engine8_Knowledge/graph/queries.py` | Cypher: `MATCH (c:Contact)` | `Neo4jContactRepo.search()` |

```python
# libs/db-layer/src/db_layer/contacts/qdrant_repo.py
class QdrantContactRepo(EntityRepository[Contact, ContactCreate, ContactUpdate]):
    def __init__(self, client: QdrantClient, embedder: Callable):
        self._client = client
        self._embed = embedder
        self._collection = "contacts"

    async def search(self, query: str, limit: int = 20) -> list[Contact]:
        vector = self._embed(query)
        results = self._client.search(
            collection_name=self._collection,
            query_vector=vector,
            limit=limit,
        )
        return [Contact(**r.payload) for r in results]
```

#### ProgramRepository

| Current Location | Method | Target |
|-----------------|--------|--------|
| `simple_knowledge_api.py` `/programs/search` handler | `search_programs()` | `QdrantProgramRepo.search()` |
| `Engine2_ProgramMapping/scripts/program_mapper.py` | CSV-based program lookup | `CsvProgramRepo.search()` (legacy) |
| `Engine7_BullhornETL/scripts/link_to_federal_programs.py` | SQLite `placement_program_links` table | `SqliteProgramRepo.get_linked()` |
| `Engine8_Knowledge/graph/queries.py` | Cypher: `MATCH (p:Program)` | `Neo4jProgramRepo.search()` |

```python
# libs/db-layer/src/db_layer/programs/qdrant_repo.py
class QdrantProgramRepo(EntityRepository[FederalProgram, ProgramCreate, ProgramUpdate]):
    ...
```

#### JobRepository

| Current Location | Method | Target |
|-----------------|--------|--------|
| `simple_knowledge_api.py` general search | `search_knowledge()` with collection="jobs" | `QdrantJobRepo.search()` |
| `Engine2_ProgramMapping/scripts/pipeline.py` | JSON file reading/writing | `FileJobRepo.list()` (legacy) |
| `Engine8_Knowledge/scripts/index_engine1_jobs.py` | JSON → Qdrant indexing | `QdrantJobRepo.create()` |

#### ActivityRepository

| Current Location | Method | Target |
|-----------------|--------|--------|
| `simple_knowledge_api.py` `/activities/search` handler | `search_activities()` | `QdrantActivityRepo.search()` |
| `Engine7_BullhornETL/scripts/bullhorn_activity_logger.py` | SQLite insert/query | `SqliteActivityRepo.create()`, `.list()` |
| `Engine8_Knowledge/scripts/memory_system.py` | SQLite memory store | `SqliteActivityRepo` (conversation memory) |

### Database Connection Factories

```python
# libs/db-layer/src/db_layer/connections.py
from functools import lru_cache
from qdrant_client import QdrantClient
import sqlite3
from pathlib import Path

@lru_cache(maxsize=1)
def get_qdrant_client(url: str | None = None) -> QdrantClient:
    """Singleton Qdrant client. Replaces 54+ inline instantiations."""
    from shared_core.config.settings import get_settings
    url = url or get_settings().qdrant_url
    return QdrantClient(url=url)

def get_sqlite_connection(db_name: str) -> sqlite3.Connection:
    """Get SQLite connection by canonical database name."""
    DB_MAP = {
        "bullhorn": Path("Engine7_BullhornETL/data/bullhorn_master.db"),
        "graph": Path("Engine8_Knowledge/data/bd_graph.db"),
        "memories": Path("Engine8_Knowledge/data/memories.db"),
        "page_index": Path("Engine8_Knowledge/data/page_index.db"),
        "notifications": Path("Engine8_Knowledge/data/notifications.db"),
    }
    path = DB_MAP.get(db_name)
    if not path:
        raise ValueError(f"Unknown database: {db_name}")
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn
```

### db-layer Package Structure

```
libs/db-layer/
├── pyproject.toml
└── src/db_layer/
    ├── __init__.py
    ├── base.py                 # EntityRepository ABC
    ├── connections.py          # get_qdrant_client(), get_sqlite_connection()
    ├── contacts/
    │   ├── __init__.py
    │   ├── qdrant_repo.py      # QdrantContactRepo
    │   ├── sqlite_repo.py      # SqliteContactRepo (Bullhorn data)
    │   └── neo4j_repo.py       # Neo4jContactRepo (graph queries)
    ├── programs/
    │   ├── __init__.py
    │   ├── qdrant_repo.py      # QdrantProgramRepo
    │   └── sqlite_repo.py      # SqliteProgramRepo
    ├── jobs/
    │   ├── __init__.py
    │   ├── qdrant_repo.py      # QdrantJobRepo
    │   └── file_repo.py        # FileJobRepo (JSON/CSV legacy)
    ├── activities/
    │   ├── __init__.py
    │   ├── qdrant_repo.py      # QdrantActivityRepo
    │   └── sqlite_repo.py      # SqliteActivityRepo
    └── graph/
        ├── __init__.py
        ├── neo4j_manager.py    # Neo4jManager (from Engine8)
        ├── ingestion.py        # BulkIngestion (from Engine8)
        ├── queries.py          # BDQueries (from Engine8)
        └── schema.py           # Schema management (from Engine8)
```

---

## libs/bullhorn-client/ (Bullhorn CRM Integration)

### Current Bullhorn Touchpoints

| Current Location | Class/Function | What It Does | Target |
|-----------------|----------------|-------------|--------|
| `services/bullhorn_integration.py` (481 lines) | `BullhornClient` class | OAuth auth flow (mock), API wrapper, CRUD operations | `libs/bullhorn-client/src/bullhorn_client/client.py` |
| `services/bullhorn_integration.py:67` | `auth_params` (built but unused) | OAuth token request params | `libs/bullhorn-client/src/bullhorn_client/auth.py` |
| `services/bullhorn_integration.py:80` | `token_data` (built but unused) | Token response handling | `libs/bullhorn-client/src/bullhorn_client/auth.py` |
| `Engine7_BullhornETL/scripts/bullhorn_etl_v2.py` | `BullhornETL` class | ETL pipeline from Bullhorn API → SQLite | `libs/bullhorn-client/src/bullhorn_client/etl.py` |
| `Engine7_BullhornETL/scripts/database_schema.py` | Schema definitions + `get_connection()` | 13 SQLite table schemas for Bullhorn data | `libs/db-layer/src/db_layer/bullhorn_schema.py` |
| `Engine7_BullhornETL/scripts/bullhorn_activity_logger.py` | `BullhornActivityLogger` class | Log BD activities to Bullhorn | `libs/bullhorn-client/src/bullhorn_client/activity_logger.py` |
| `Engine7_BullhornETL/scripts/export_to_notion.py` | Bullhorn → Notion export | Export Bullhorn contacts/placements to Notion | `libs/bullhorn-client/src/bullhorn_client/exporters/notion.py` |
| `Engine7_BullhornETL/scripts/contact_scoring.py` | Score Bullhorn contacts | BD priority scoring from Bullhorn data | Move scoring logic to `services/bd-automation/scoring/` |
| `Engine7_BullhornETL/run_pipeline.py` | 7-step pipeline orchestrator | ETL → Cleanup → Financials → Programs → Contacts → Reports → Export | `libs/bullhorn-client/src/bullhorn_client/pipeline.py` |

### Proposed Unified BullhornClient

```python
# libs/bullhorn-client/src/bullhorn_client/client.py
class BullhornClient:
    """Unified Bullhorn CRM client with OAuth and CRUD operations."""

    def __init__(self, client_id: str, client_secret: str, username: str, password: str):
        self._client_id = client_id
        self._client_secret = client_secret
        self._auth_token: str | None = None
        self._rest_url: str | None = None

    async def authenticate(self) -> None:
        """OAuth login flow → get rest_token and rest_url."""
        ...

    async def get_candidates(self, query: str = "", limit: int = 100) -> list[dict]:
        """Search/list candidates."""
        ...

    async def get_placements(self, candidate_id: int | None = None) -> list[dict]:
        """Get placements, optionally filtered by candidate."""
        ...

    async def get_job_orders(self, status: str = "Open") -> list[dict]:
        """Get job orders by status."""
        ...

    async def log_activity(self, candidate_id: int, activity_type: str, notes: str) -> dict:
        """Log a BD activity against a candidate."""
        ...

    async def add_note(self, entity_type: str, entity_id: int, text: str) -> dict:
        """Add a note to any Bullhorn entity."""
        ...
```

### bullhorn-client Package Structure

```
libs/bullhorn-client/
├── pyproject.toml
└── src/bullhorn_client/
    ├── __init__.py
    ├── client.py               # BullhornClient (OAuth + CRUD)
    ├── auth.py                 # OAuth flow, token refresh
    ├── etl.py                  # ETL pipeline (API → SQLite)
    ├── activity_logger.py      # Log activities to Bullhorn
    ├── pipeline.py             # 7-step pipeline orchestrator
    └── exporters/
        ├── __init__.py
        ├── notion.py           # Export to Notion databases
        └── csv.py              # Export to CSV/Excel
```

---

## libs/slack-utils/ (Shared Slack Utilities)

### Current Slack Touchpoints

| Current Location | Class/Function | What It Does |
|-----------------|----------------|-------------|
| `Engine8_Knowledge/integrations/slack_integration.py` (461 lines) | `SlackBDBot` class | Send notifications, daily digests, hot lead alerts, slash commands. Falls back to JSONL when no token. |
| `Engine8_Knowledge/integrations/routes.py:38-107` | FastAPI router | `/slack/notify`, `/slack/digest`, `/slack/hot-lead`, `/slack/status`, `/slack/command` |
| `Engine6_QA/scripts/alerts.py` | `send_slack_alert()` function | QA alert delivery to Slack channels |
| `Engine8_Knowledge/agents/autonomous/morning_briefing.py` | Morning briefing delivery | Daily briefing sent via Slack |
| `Engine8_Knowledge/api.py` | Slack router mount | Mounts integration routes |

### Proposed Slack Utility

```python
# libs/slack-utils/src/slack_utils/bot.py
class SlackBDBot:
    """BD Intelligence Slack bot with Block Kit formatting."""

    def __init__(self, token: str | None = None, fallback_log: Path | None = None):
        self.token = token or os.environ.get("SLACK_BOT_TOKEN")
        self._fallback_log = fallback_log or Path("data/slack_notifications.jsonl")
        ...

    async def send_notification(self, channel: str, blocks: list[dict]) -> bool: ...
    async def send_hot_lead_alert(self, lead: dict, channel: str = "#bd-alerts") -> bool: ...
    async def send_daily_digest(self, digest: dict, channel: str = "#bd-daily") -> bool: ...
    async def send_pipeline_update(self, status: dict, channel: str = "#bd-pipeline") -> bool: ...
```

### slack-utils Package Structure

```
libs/slack-utils/
├── pyproject.toml
└── src/slack_utils/
    ├── __init__.py
    ├── bot.py                  # SlackBDBot class
    ├── blocks.py               # Block Kit template builders
    ├── routes.py               # FastAPI router for slash commands
    └── fallback.py             # JSONL fallback logger
```

---

## CANONICAL PYDANTIC MODELS

### Contact Model

**Current versions:**

| Location | Fields | Differences |
|----------|--------|-------------|
| `models/contacts.py` | name, title, company, email, phones, linkedin_url, location, program (DCGSProgram), tier (HierarchyTier 1-6), priority (BDPriority), functional_areas, clearance_level, last_contact_date | Full model with all BD enums |
| `Engine3_OrgChart/scripts/contact_classifier.py` | Inline dict: name, title, company, tier, program, location | Subset — no email, phones, linkedin |
| `Engine7_BullhornETL/scripts/database_schema.py` | SQLite schema: id, firstName, lastName, email, title, company + many more | Has candidateID, status, dateAdded not in Pydantic model |
| `Engine8_Knowledge/scripts/vector_store.py` | Qdrant payload: free-form dict | No schema enforcement |

**Canonical version (proposed):**
```python
# libs/shared-core/src/shared_core/models/contact.py
class Contact(BaseDocument):
    # Identity
    name: str
    first_name: str | None = None
    last_name: str | None = None
    title: str | None = None
    company: str | None = None

    # Contact info
    email: str | None = None
    phones: list[str] = []
    linkedin_url: str | None = None
    location: str | None = None

    # BD classification
    program: DCGSProgram = DCGSProgram.OTHER
    tier: HierarchyTier = HierarchyTier.TIER_6
    priority: BDPriority = BDPriority.LOW
    functional_areas: list[str] = []
    clearance_level: str | None = None

    # Bullhorn-specific (added from ETL schema)
    bullhorn_id: int | None = None
    status: str | None = None
    date_added: datetime | None = None
    last_contact_date: datetime | None = None

    # Enrichment
    bd_score: float = 0.0
    match_confidence: float = 0.0
```

### FederalProgram Model

**Current versions:**

| Location | Fields | Differences |
|----------|--------|-------------|
| `models/programs.py` | program_name, acronym, agency_owner, prime_contractor, subcontractors, contract_number, contract_value, period_of_performance, locations, required_roles, keywords, pts_involvement, priority_level | Full model |
| `Engine2_ProgramMapping/data/Federal_Programs_*.csv` | 15+ columns including NAICS, contract vehicles, functional areas | Has fields not in Pydantic model |

**Canonical version:** Keep `models/programs.py` as-is, add:
```python
    naics_codes: list[str] = []
    contract_vehicles: list[str] = []
    functional_areas: list[str] = []
```

### ScrapedJob Model

**Current versions:**

| Location | Fields | Differences |
|----------|--------|-------------|
| `models/jobs.py` | title, company, location, url, description, clearance_required, mapped_program, bd_score, match_confidence, technologies, certifications, status (JobStatus) | Full model |
| `Engine2_ProgramMapping/scripts/job_standardizer.py` | Inline dict with ~20 fields from LLM extraction | Has salary_range, experience_years, education not in model |

**Canonical version:** Add to `models/jobs.py`:
```python
    salary_range: str | None = None
    experience_years: int | None = None
    education_required: str | None = None
    posting_date: datetime | None = None
    source_url: str | None = None
    scraper_id: str | None = None
```

### Activity Model

**Current versions:**

| Location | Fields | Differences |
|----------|--------|-------------|
| `models/activities.py` | contact_id, contact_name, activity_type (8 types), summary, notes, outcome, follow_up_action, follow_up_date | Full model |
| `Engine7_BullhornETL/scripts/bullhorn_activity_logger.py` | Inline dict with dateAdded, action, comments | Simpler Bullhorn-native format |

**Canonical version:** Keep `models/activities.py` as-is, add:
```python
    bullhorn_note_id: int | None = None
    channel: str | None = None  # "phone", "email", "linkedin", "in-person"
    duration_minutes: int | None = None
```

---

## DEPENDENCY INJECTION PLAN

### Current Pattern (Direct Database Calls)

```python
# simple_knowledge_api.py — current pattern
@app.get("/contacts/search")
async def search_contacts(q: str, tier: str = None):
    client = QdrantClient(url=QDRANT_URL)
    openai_client = OpenAI()
    embedding = openai_client.embeddings.create(input=q, model="text-embedding-3-small")
    results = client.search(
        collection_name="contacts",
        query_vector=embedding.data[0].embedding,
        limit=20,
    )
    return {"results": [r.payload for r in results]}
```

**Problems:**
- Creates new QdrantClient per request (no pooling)
- Creates new OpenAI client per request
- Embedding model hardcoded
- No abstraction — can't swap storage backend
- No testability — can't mock database

### Target Pattern (Injected Repositories)

```python
# services/bd-automation/routes/contacts.py — target pattern
from fastapi import APIRouter, Depends, Query
from db_layer.contacts.qdrant_repo import QdrantContactRepo
from shared_core.utils.embeddings import get_embedding
from shared_core.models.pagination import PaginatedResponse
from shared_core.models.contact import Contact

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])

def get_contact_repo() -> QdrantContactRepo:
    from db_layer.connections import get_qdrant_client
    return QdrantContactRepo(client=get_qdrant_client(), embedder=get_embedding)

@router.get("/search", response_model=PaginatedResponse[Contact])
async def search_contacts(
    q: str = Query(..., description="Search query"),
    tier: str | None = Query(None, description="Filter by tier"),
    limit: int = Query(20, le=100),
    repo: QdrantContactRepo = Depends(get_contact_repo),
):
    results = await repo.search(query=q, limit=limit)
    if tier:
        results = [r for r in results if r.tier.value == tier]
    return PaginatedResponse(items=results, total=len(results))
```

### Routes to Rewire

| Current Route | Current File | Current Pattern | Target Injection |
|--------------|-------------|-----------------|-----------------|
| `GET /contacts/search` | `simple_knowledge_api.py` | Direct Qdrant + OpenAI | `Depends(get_contact_repo)` |
| `GET /programs/search` | `simple_knowledge_api.py` | Direct Qdrant + OpenAI | `Depends(get_program_repo)` |
| `GET /activities/search` | `simple_knowledge_api.py` | Direct Qdrant + OpenAI | `Depends(get_activity_repo)` |
| `POST /search` | `simple_knowledge_api.py` | Direct Qdrant + OpenAI | `Depends(get_search_service)` |
| `POST /search/hybrid` | `simple_knowledge_api.py` | Direct Qdrant + OpenAI | `Depends(get_search_service)` |
| `POST /ask/smart` | `simple_knowledge_api.py` | Direct Qdrant + OpenAI + Claude | `Depends(get_rag_service)` |
| `GET /stats` | `simple_knowledge_api.py` | Direct Qdrant collection counts | `Depends(get_stats_service)` |
| `GET /collections` | `simple_knowledge_api.py` | Direct Qdrant client | `Depends(get_qdrant_client)` |
| `GET /sample/{collection}` | `simple_knowledge_api.py` | Direct Qdrant scroll | `Depends(get_qdrant_client)` |
| All `/api/v2/*` routes | `api/unified_endpoints.py` | `get_qdrant()` function | `Depends(get_qdrant_client)` |
| All `/agents/*` routes | `Engine8_Knowledge/agents/api_routes.py` | Direct agent instantiation | `Depends(get_agent_service)` |
| All `/search/v2/*` routes | `Engine8_Knowledge/search/search_routes.py` | Direct search engine | `Depends(get_search_service)` |
| All `/neo4j/*` routes | `Engine8_Knowledge/graph/neo4j_routes.py` | Direct Neo4jManager | `Depends(get_neo4j_manager)` |
| All `/integrations/*` routes | `Engine8_Knowledge/integrations/routes.py` | Direct SlackBDBot | `Depends(get_slack_bot)` |

### Dependency Provider Module

```python
# services/bd-automation/dependencies.py
from functools import lru_cache
from db_layer.connections import get_qdrant_client, get_sqlite_connection
from db_layer.contacts.qdrant_repo import QdrantContactRepo
from db_layer.programs.qdrant_repo import QdrantProgramRepo
from db_layer.activities.qdrant_repo import QdrantActivityRepo
from shared_core.utils.embeddings import get_embedding

@lru_cache(maxsize=1)
def get_contact_repo() -> QdrantContactRepo:
    return QdrantContactRepo(client=get_qdrant_client(), embedder=get_embedding)

@lru_cache(maxsize=1)
def get_program_repo() -> QdrantProgramRepo:
    return QdrantProgramRepo(client=get_qdrant_client(), embedder=get_embedding)

@lru_cache(maxsize=1)
def get_activity_repo() -> QdrantActivityRepo:
    return QdrantActivityRepo(client=get_qdrant_client(), embedder=get_embedding)
```

---

## MIGRATION SEQUENCE

### Phase 3a: Extract shared-core (lowest risk)
1. Create `libs/shared-core/` with `pyproject.toml`
2. Move `config/settings.py` → `libs/shared-core/src/shared_core/config/settings.py`
3. Move `config/logging_config.py` → `libs/shared-core/src/shared_core/config/logging.py`
4. Move `models/*.py` → `libs/shared-core/src/shared_core/models/`
5. Create `utils/embeddings.py`, `utils/retry.py`, `utils/paths.py`
6. Update all import paths (ruff can assist with import rewriting)
7. Verify: `python -c "from shared_core.config.settings import get_settings; print('OK')"`

### Phase 3b: Extract db-layer (medium risk)
1. Create `libs/db-layer/` with abstract `EntityRepository`
2. Implement `QdrantContactRepo`, `QdrantProgramRepo`, `QdrantActivityRepo`
3. Create `connections.py` singleton factories
4. Rewire `simple_knowledge_api.py` routes to use `Depends()`
5. Rewire `api/unified_endpoints.py` routes
6. Verify: all 17 API endpoints return same results

### Phase 3c: Extract bullhorn-client (low risk, self-contained)
1. Create `libs/bullhorn-client/`
2. Move `services/bullhorn_integration.py` → `client.py`
3. Move `Engine7_BullhornETL/scripts/bullhorn_activity_logger.py` → `activity_logger.py`
4. Move `Engine7_BullhornETL/run_pipeline.py` → `pipeline.py`
5. Update Engine7 scripts to import from `bullhorn_client`

### Phase 3d: Extract slack-utils (low risk, self-contained)
1. Create `libs/slack-utils/`
2. Move `Engine8_Knowledge/integrations/slack_integration.py` → `bot.py`
3. Move `Engine8_Knowledge/integrations/routes.py` Slack endpoints → `routes.py`
4. Update `Engine6_QA/scripts/alerts.py` to import from `slack_utils`

---

## ROOT pyproject.toml (uv workspace)

```toml
[project]
name = "pts-bd-platform"
version = "2.0.0"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["services/*", "libs/*"]

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "S", "ERA", "PL", "RUF"]

[tool.pytest.ini_options]
testpaths = ["tests", "services/*/tests", "libs/*/tests"]
```

---

*End of Shared Library Extraction Plan*
*Ready for implementation after cleanup branch is merged.*
