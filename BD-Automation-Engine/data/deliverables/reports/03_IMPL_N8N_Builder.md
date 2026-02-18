# 🟠 TERMINAL C: N8N-BUILDER
## Complete Implementation & Execution Guide

**Project Folder:** `C:\N8N Builder`  
**Role:** Contract Intelligence Hub — Discovery Engines, Enrichment, Workflow Orchestration  
**Maturity:** 2.2/5 → Target 4.0/5

---

## ═══════════════════════════════════════════
## PHASE 0: EMERGENCY SECURITY (Day 1)
## ═══════════════════════════════════════════
## 🔀 PARALLEL — Run simultaneously with Terminals A and B
## ⚠️ THIS PROJECT HAS EXPOSED API KEYS IN .mcp.json

---

### Step 0.1: Fix .gitignore and Remove Exposed Secrets

⚡ **PROMPT — Paste into Auto-Claude:**

```
CRITICAL SECURITY ISSUE: This project has API keys exposed in the .mcp.json file that is NOT in .gitignore.

1. Find and show the current .gitignore file

2. Add ALL of these patterns to .gitignore:

.env
.env.*
.env.local
.env.production
*.key
*.pem
.mcp.json
mcp_config.json
*.secret
secrets/
.vault/
__pycache__/
*.pyc
.pytest_cache/
node_modules/
*.log
.DS_Store
Thumbs.db
lancedb_data/
*.lance
*.lance-tmp

3. Remove tracked sensitive files:
```bash
git rm --cached .mcp.json 2>/dev/null
git rm --cached .env 2>/dev/null
```

4. Search for API keys in ALL files:
```bash
grep -r "sk-ant-" . --include="*.py" --include="*.json" --include="*.yaml" --include="*.toml" -l
grep -r "sk-proj-" . --include="*.py" --include="*.json" -l
grep -r "ANTHROPIC_API_KEY" . --include="*.py" --include="*.json" --include="*.mcp.json" -l
grep -r "Bearer " . --include="*.py" --include="*.json" -l
grep -rn "api_key.*=.*['\"]" . --include="*.py" -l
```

5. For each file with hardcoded keys, replace with os.environ.get() references

6. Show me the .mcp.json file (redact key values) — I need to see the structure to recreate it with env var references

7. Commit:
```bash
git add .gitignore
git commit -m "SECURITY: Fix .gitignore, remove exposed .mcp.json and secrets from tracking"
```

Do NOT print actual API key values.
```

✅ **VERIFY:** `.mcp.json` no longer tracked by git. Zero API keys in Python source files.

---

### Step 0.2: Audit Git History and Rotate Keys

⚡ **PROMPT — Paste into Auto-Claude:**

```
Audit git history for exposed secrets and create a key rotation checklist.

1. Install and run truffleHog:
```bash
pip install truffleHog
trufflehog filesystem . --no-update 2>&1 | head -50
```

2. Also manually search:
```bash
git log --all --full-history -p -- .mcp.json | head -100
git log --all --full-history -p -- .env | head -100
```

3. Create .env.example with all required variables:
```
# LLM APIs — ROTATE THESE
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here

# Notion
NOTION_API_KEY=your-key-here

# n8n Cloud
N8N_WEBHOOK_BASE=your-n8n-cloud-url
N8N_API_KEY=your-key-here

# Vector DB (pointing to BD-Engine's Qdrant)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-key-here

# Hub API (BD-Automation-Engine)
HUB_API_URL=http://localhost:8100
HUB_API_KEY=your-key-here

# Federal APIs
TANGO_API_KEY=your-key-here
USASPENDING_API_KEY=your-key-here

# Browser automation
BROWSERUSE_API_KEY=your-key-here

# MCP Server
MCP_API_KEY=your-key-here
```

4. Create .mcp.json.example with the same structure as the current .mcp.json but with placeholder values.

5. Print the full key rotation checklist.

Report all findings.
```

---

### Step 0.3: Setup Centralized Settings

⚡ **PROMPT — Paste into Auto-Claude:**

```
Create a centralized settings module for this project.

1. Install:
```bash
pip install pydantic>=2.6.0 pydantic-settings>=2.1.0
```

2. Create `config/settings.py`:

```python
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    default_llm_model: str = "claude-sonnet-4-20250514"
    default_embedding_model: str = "text-embedding-3-small"
    
    # Notion
    notion_api_key: str = ""
    
    # n8n
    n8n_webhook_base: str = ""
    n8n_api_key: str = ""
    
    # Vector DB (BD-Engine's unified Qdrant)
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    
    # Hub API
    hub_api_url: str = "http://localhost:8100"
    hub_api_key: str = ""
    
    # Federal APIs
    tango_api_key: str = ""
    usaspending_api_key: str = ""
    
    # Browser automation
    browseruse_api_key: str = ""
    
    # MCP
    mcp_api_key: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

3. Create `config/__init__.py`

4. Find ALL os.environ references and hardcoded keys in the project and replace with settings:
```bash
grep -rn "os.environ\|os.getenv" . --include="*.py" | head -50
```

Replace each with `from config.settings import get_settings; settings = get_settings()`

Report all files modified.
```

---

## ═══════════════════════════════════════════
## PHASE 1: STABILIZATION (Week 1-2)
## ═══════════════════════════════════════════
## 🔀 PARALLEL — Run simultaneously with Terminals A and B

---

### Step 1.1: Generate requirements.txt and Install Packages

⚡ **PROMPT — Paste into Auto-Claude:**

```
This project has NO requirements.txt despite having ~150,000 lines of Python code. Fix this.

1. First, discover what's installed:
```bash
pip freeze > requirements_current.txt
```

2. Find all imports used in the project:
```bash
grep -rh "^import \|^from " . --include="*.py" | sort | uniq | head -100
```

3. Cross-reference installed packages with actual imports to create a clean requirements.txt

4. Add these critical packages if not present:
```
tenacity>=8.2.0
structlog>=24.1.0
pydantic>=2.6.0
pydantic-settings>=2.1.0
qdrant-client>=1.7.0
anthropic>=0.18.0
openai>=1.12.0
langgraph>=0.1.0
httpx>=0.27.0
sentence-transformers>=2.2.0
```

5. Install missing packages:
```bash
pip install tenacity>=8.2.0 structlog>=24.1.0 pydantic>=2.6.0 pydantic-settings>=2.1.0 qdrant-client>=1.7.0
```

6. Save the final requirements.txt and verify all imports work:
```bash
python -c "import tenacity, structlog, pydantic, qdrant_client; print('Core packages OK')"
```

Create requirements.txt and commit it.
```

✅ **VERIFY:** `pip install -r requirements.txt` completes without errors.

---

### Step 1.2: Fix 477 Bare Except Blocks

⚡ **PROMPT — Paste into Auto-Claude:**

```
This project has 477 bare `except:` blocks that catch EVERYTHING including KeyboardInterrupt and SystemExit. This is critical to fix.

1. Find all bare except blocks:
```bash
grep -rn "except:" . --include="*.py" | grep -v "except:.*#" | wc -l
grep -rn "except:" . --include="*.py" | grep -v "except:.*#" | head -30
```

2. For each bare except, determine the appropriate exception type and fix it. Common patterns:

BEFORE:
```python
try:
    result = some_api_call()
except:
    print("Error")
```

AFTER:
```python
try:
    result = some_api_call()
except (ConnectionError, TimeoutError, ValueError) as e:
    logger.error("api_call_failed", error=str(e))
except Exception as e:
    logger.error("unexpected_error", error=str(e), exc_info=True)
```

3. Priority order for fixes:
   a. First: LLM and API call handlers (most critical)
   b. Second: Data processing functions
   c. Third: File I/O operations
   d. Fourth: General utility functions

4. Rules:
   - Never use bare `except:` — always specify exception type
   - At minimum, use `except Exception as e:` (catches everything except SystemExit, KeyboardInterrupt)
   - Add structured logging to every except block
   - For critical paths, add retry logic

5. Process the first 50 most critical bare excepts (in core modules, not scripts or examples).
   Show me before/after for each fix.

This is a large task — focus on the most important files first:
- Discovery engine files
- Enrichment pipeline files
- LangGraph workflow files
- MCP server files
- API client files
```

✅ **VERIFY:** `grep -rn "except:" . --include="*.py" | grep -v "except.*Exception\|except.*Error\|except.*Warning\|except.*:" | wc -l` should be much lower than 477.

---

### Step 1.3: Add LLM Retry Logic

⚡ **PROMPT — Paste into Auto-Claude:**

```
Add retry logic to ALL LLM API calls in this project (approximately 10 call sites).

1. Create `utils/llm_retry.py` (same pattern as other projects):

```python
import structlog
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type, before_sleep_log,
)

logger = structlog.get_logger()

try:
    from anthropic import APIError, APIConnectionError, RateLimitError
    anthropic_retry = retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((APIError, APIConnectionError, RateLimitError)),
        before_sleep=before_sleep_log(logger, structlog.stdlib.log_level),
        reraise=True,
    )
except ImportError:
    anthropic_retry = lambda f: f

try:
    from openai import OpenAIError
    openai_retry = retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((OpenAIError,)),
        before_sleep=before_sleep_log(logger, structlog.stdlib.log_level),
        reraise=True,
    )
except ImportError:
    openai_retry = lambda f: f

api_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, IOError)),
    before_sleep=before_sleep_log(logger, structlog.stdlib.log_level),
    reraise=True,
)
```

2. Find ALL LLM call sites:
```bash
grep -rn "client.messages.create\|anthropic.*create\|openai.*create\|client.chat.completions" . --include="*.py" -l
```

3. Wrap each with the appropriate retry decorator.

4. Also add api_retry to:
   - Tango API calls
   - USASpending API calls
   - n8n webhook calls
   - Hub API calls
   - Any external HTTP requests

Report all files modified.
```

---

### Step 1.4: Enable Prompt Caching

⚡ **PROMPT — Paste into Auto-Claude:**

```
Enable Anthropic prompt caching on all LLM calls in this project.

Same pattern as the other projects — find all client.messages.create calls and add cache_control to system prompts and large context blocks.

BEFORE:
```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system="You are a federal contract intelligence analyst...",
    messages=[...]
)
```

AFTER:
```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system=[{
        "type": "text",
        "text": "You are a federal contract intelligence analyst...",
        "cache_control": {"type": "ephemeral"}
    }],
    messages=[...]
)
```

Find and modify ALL Anthropic calls. Report each file changed.
```

---

### Step 1.5: Structured Logging

⚡ **PROMPT — Paste into Auto-Claude:**

```
Replace print() statements with structured logging using structlog.

1. Create utils/logging_config.py (same as other projects)

2. Focus on replacing print() in these critical modules:
   - Discovery engines (federal_programs, dod_staffing, high_sub_spend)
   - 4-phase enrichment pipeline
   - LangGraph workflow definitions
   - browser-use automation scripts
   - n8n webhook handlers
   - MCP server endpoints

3. Pattern:
   BEFORE: print(f"Found {count} programs")
   AFTER: logger.info("programs_found", count=count)

Process the top 30 most important files. Report all modifications.
```

---

### Step 1.6: Add Pydantic Validation

⚡ **PROMPT — Paste into Auto-Claude:**

```
Add Pydantic v2 models for all core data structures in this project.

1. Create `models/discovery.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class DiscoverySource(str, Enum):
    USASPENDING = "usaspending"
    FPDS = "fpds"
    SAM_GOV = "sam_gov"
    TANGO = "tango"
    JOB_BOARDS = "job_boards"

class DiscoveredProgram(BaseModel):
    program_name: str
    agency: Optional[str] = None
    prime_contractor: Optional[str] = None
    subcontractors: List[str] = Field(default_factory=list)
    contract_value: Optional[float] = None
    discovery_source: DiscoverySource
    confidence_score: float = Field(default=0.5, ge=0, le=1)
    discovery_date: datetime = Field(default_factory=datetime.utcnow)
    key_locations: List[str] = Field(default_factory=list)
    typical_roles: List[str] = Field(default_factory=list)
    source_project: str = "n8n_builder"
```

2. Create `models/enrichment.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class EnrichmentPhase(str, Enum):
    TASK_ORDERS = "phase_1_task_orders"
    LOCATION = "phase_2_location"
    ORG_HIERARCHY = "phase_3_org_hierarchy"
    TECHNOLOGY = "phase_4_technology"

class EnrichmentResult(BaseModel):
    program_name: str
    phase: EnrichmentPhase
    fields_extracted: int = 0
    data: Dict = Field(default_factory=dict)
    sources_used: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    enriched_at: datetime = Field(default_factory=datetime.utcnow)
    errors: List[str] = Field(default_factory=list)
```

3. Create `models/workflow.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowExecution(BaseModel):
    workflow_id: str
    workflow_name: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_params: Dict = Field(default_factory=dict)
    output: Optional[Dict] = None
    error: Optional[str] = None
    steps_completed: int = 0
    total_steps: int = 0
```

4. Create `models/__init__.py` exporting all models.

5. Apply validation to discovery engines and enrichment pipeline inputs/outputs.

Create all files and report.
```

---

## ═══════════════════════════════════════════
## PHASE 2: DATABASE MIGRATION (Weeks 2-4)
## ═══════════════════════════════════════════
## 🔗 DEPENDS ON: Terminal A completing Steps 2.1-2.2

---

### Step 2.1: Migrate LanceDB to Qdrant

⚡ **PROMPT — Paste into Auto-Claude:**

```
Migrate all data from LanceDB (384-dimension embeddings) to the unified Qdrant instance (1536-dimension).

1. Find LanceDB data and configuration:
```bash
grep -rn "lancedb\|LanceDB\|lance" . --include="*.py" -l
find . -name "*.lance" -o -name "lancedb_data" | head -20
```

2. Create `scripts/migrate_lancedb_to_qdrant.py`:

```python
"""Migrate LanceDB data to unified Qdrant instance."""
import os
import lancedb
import hashlib
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

logger = structlog.get_logger()

# Connections
lance_db = lancedb.connect("path/to/lancedb/data")  # Adjust path
qdrant = QdrantClient(url=os.environ.get("QDRANT_URL", "http://localhost:6333"))
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=30))
def get_embeddings_batch(texts: list) -> list:
    response = openai_client.embeddings.create(input=texts, model="text-embedding-3-small")
    return [d.embedding for d in response.data]

def migrate_table(table_name: str, target_collection: str):
    """Migrate a LanceDB table to a Qdrant collection."""
    table = lance_db.open_table(table_name)
    df = table.to_pandas()
    
    logger.info("migrating_table", table=table_name, records=len(df), target=target_collection)
    
    batch_texts = []
    batch_records = []
    
    for idx, row in df.iterrows():
        # Build text content from row
        text_parts = []
        for col in df.columns:
            if col != 'vector' and row[col] is not None and str(row[col]).strip():
                text_parts.append(f"{col}: {row[col]}")
        text = ". ".join(text_parts)
        
        if not text.strip() or len(text) < 10:
            continue
        
        batch_texts.append(text)
        batch_records.append(row.to_dict())
        
        if len(batch_texts) >= 50:
            _process_batch(batch_texts, batch_records, target_collection)
            batch_texts, batch_records = [], []
            if idx % 500 == 0:
                logger.info("progress", table=table_name, processed=idx)
    
    if batch_texts:
        _process_batch(batch_texts, batch_records, target_collection)
    
    info = qdrant.get_collection(target_collection)
    logger.info("migration_complete", table=table_name, target=target_collection, vectors=info.points_count)

def _process_batch(texts, records, target_collection):
    """Embed and upsert a batch."""
    embeddings = get_embeddings_batch(texts)
    points = []
    for text, embedding, record in zip(texts, embeddings, records):
        # Remove old vector from payload
        record.pop('vector', None)
        
        point_id = hashlib.md5(text.encode()).hexdigest()
        payload = {
            **{k: str(v) for k, v in record.items() if v is not None},
            "content": text,
            "source_project": "n8n_builder",
            "source_type": "lancedb_migration",
            "embedding_model": "text-embedding-3-small",
            "content_hash": hashlib.md5(text.encode()).hexdigest(),
        }
        points.append(PointStruct(id=point_id, vector=embedding, payload=payload))
    
    qdrant.upsert(collection_name=target_collection, points=points)

if __name__ == "__main__":
    # List all LanceDB tables
    tables = lance_db.table_names()
    logger.info("found_tables", tables=tables)
    
    # Map tables to Qdrant collections
    TABLE_MAPPING = {
        # Adjust these based on actual table names found
        # "contacts": "contacts_unified",
        # "programs": "programs_unified",
        # "knowledge": "knowledge_graph",
        # "documents": "documents_kb",
    }
    
    # Auto-map if no explicit mapping
    for table_name in tables:
        target = TABLE_MAPPING.get(table_name)
        if not target:
            if "contact" in table_name.lower():
                target = "contacts_unified"
            elif "program" in table_name.lower():
                target = "programs_unified"
            elif "job" in table_name.lower():
                target = "jobs_unified"
            elif "knowledge" in table_name.lower() or "document" in table_name.lower():
                target = "documents_kb"
            else:
                target = "documents_kb"  # Default
        
        migrate_table(table_name, target)
    
    # Print final stats
    for name in ["contacts_unified", "programs_unified", "jobs_unified", "documents_kb", "knowledge_graph"]:
        try:
            info = qdrant.get_collection(name)
            logger.info("collection_status", name=name, vectors=info.points_count)
        except:
            pass
```

3. Find the actual LanceDB data path and run the migration.

4. After migration, update ALL code that uses LanceDB to use Qdrant instead:
```bash
grep -rn "import lancedb\|from lancedb" . --include="*.py" -l
```

Replace each with qdrant_client equivalents.

Run the migration and report results.
```

✅ **VERIFY:** Zero LanceDB imports in codebase. Data visible in Qdrant unified collections.

---

### Step 2.2: Export N8N-Builder Contacts to Hub

⚡ **PROMPT — Paste into Auto-Claude:**

```
Export all 7,000+ contacts from the 20 prime contractor databases in N8N-Builder to the unified Qdrant contacts_unified collection.

1. Find all contact databases/files:
```bash
find . -name "*contacts*" -o -name "*person*" -o -name "*PERSON*" | head -30
grep -rn "contacts_db\|contact_database\|prime_db" . --include="*.py" | head -20
```

2. Create `scripts/export_contacts_to_hub.py`:

```python
"""Export all contacts from N8N-Builder databases to Hub."""
import os
import csv
import json
import hashlib
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

logger = structlog.get_logger()

qdrant = QdrantClient(url=os.environ.get("QDRANT_URL", "http://localhost:6333"))
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=30))
def get_embeddings_batch(texts: list) -> list:
    response = openai_client.embeddings.create(input=texts, model="text-embedding-3-small")
    return [d.embedding for d in response.data]

def build_contact_text(record: dict) -> str:
    parts = []
    name = f"{record.get('First Name', record.get('first_name', ''))} {record.get('Last Name', record.get('last_name', ''))}".strip()
    if name: parts.append(f"Name: {name}")
    title = record.get('Job Title', record.get('job_title', ''))
    if title: parts.append(f"Title: {title}")
    company = record.get('Company Name', record.get('company', ''))
    if company: parts.append(f"Company: {company}")
    location = f"{record.get('Person City', record.get('city', ''))}, {record.get('Person State', record.get('state', ''))}".strip(', ')
    if location: parts.append(f"Location: {location}")
    dept = record.get('Department', record.get('department', ''))
    if dept: parts.append(f"Department: {dept}")
    return ". ".join(parts)

def process_csv_file(filepath: str, source_name: str):
    """Process a single CSV contact file."""
    records = []
    with open(filepath, encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        records = list(reader)
    
    logger.info("processing_contacts", source=source_name, count=len(records))
    
    batch_texts = []
    batch_records = []
    total_indexed = 0
    
    for i, record in enumerate(records):
        text = build_contact_text(record)
        if len(text) < 10:
            continue
        
        batch_texts.append(text)
        batch_records.append(record)
        
        if len(batch_texts) >= 50:
            embeddings = get_embeddings_batch(batch_texts)
            points = []
            for text, embedding, rec in zip(batch_texts, embeddings, batch_records):
                point_id = hashlib.md5(text.encode()).hexdigest()
                payload = {
                    **{k: str(v) for k, v in rec.items() if v},
                    "content": text,
                    "source_project": "n8n_builder",
                    "source_type": f"prime_db_{source_name}",
                    "embedding_model": "text-embedding-3-small",
                }
                points.append(PointStruct(id=point_id, vector=embedding, payload=payload))
            
            qdrant.upsert(collection_name="contacts_unified", points=points)
            total_indexed += len(points)
            batch_texts, batch_records = [], []
    
    # Final batch
    if batch_texts:
        embeddings = get_embeddings_batch(batch_texts)
        points = []
        for text, embedding, rec in zip(batch_texts, embeddings, batch_records):
            point_id = hashlib.md5(text.encode()).hexdigest()
            payload = {
                **{k: str(v) for k, v in rec.items() if v},
                "content": text,
                "source_project": "n8n_builder",
                "source_type": f"prime_db_{source_name}",
            }
            points.append(PointStruct(id=point_id, vector=embedding, payload=payload))
        qdrant.upsert(collection_name="contacts_unified", points=points)
        total_indexed += len(points)
    
    logger.info("contacts_indexed", source=source_name, total=total_indexed)
    return total_indexed

if __name__ == "__main__":
    import glob
    
    # Find all contact CSV files
    contact_files = glob.glob("data/**/*contact*", recursive=True)
    contact_files += glob.glob("data/**/*PERSON*", recursive=True)
    contact_files += glob.glob("databases/**/*.csv", recursive=True)
    
    total = 0
    for f in sorted(set(contact_files)):
        if f.endswith('.csv'):
            source = Path(f).stem
            count = process_csv_file(f, source)
            total += count
    
    info = qdrant.get_collection("contacts_unified")
    logger.info("export_complete", total_indexed=total, collection_vectors=info.points_count)
```

3. Run the export and report how many contacts were indexed.
```

---

### Step 2.3: Connect Discovery Engines to Hub

⚡ **PROMPT — Paste into Auto-Claude:**

```
Update the 3 discovery engines to push discovered programs directly to the Hub API and Qdrant.

1. Find the discovery engine source files:
```bash
grep -rn "class.*Discovery\|def discover\|discovery_engine" . --include="*.py" -l
```

2. For each discovery engine (Federal Programs, DoD Staffing, High-Sub-Spend), add a step at the end that:
   a. Validates discovered programs using the DiscoveredProgram Pydantic model
   b. Embeds and upserts to Qdrant programs_unified
   c. Pushes to Hub API via the Hub client

Create `services/hub_client.py`:

```python
"""Hub API client for N8N-Builder."""
import os
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Dict
from config.settings import get_settings

logger = structlog.get_logger()

class HubClient:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.hub_api_url
        self.api_key = settings.hub_api_key
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=30.0,
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=30))
    def push_programs(self, programs: List[Dict]) -> dict:
        response = self.client.post("/api/v2/ingest/programs", json={"programs": programs})
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=30))
    def push_enrichment(self, program_id: str, enrichment_data: Dict) -> dict:
        response = self.client.post(
            f"/api/v2/programs/{program_id}/enrichment",
            json=enrichment_data
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> bool:
        try:
            response = self.client.get("/api/health")
            return response.status_code == 200
        except:
            return False
```

3. Modify each discovery engine to call hub_client.push_programs() after discovering new programs.

4. Test by running a small discovery and verifying the programs appear in Qdrant programs_unified.

Report all modifications.
```

---

### Step 2.4: Build Workflow Status API

⚡ **PROMPT — Paste into Auto-Claude:**

```
Create API endpoints that the BD Dashboard can call to trigger and monitor N8N-Builder workflows.

Create `api/workflow_api.py`:

```python
"""Workflow API for dashboard integration."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
import structlog
import httpx
from datetime import datetime
from config.settings import get_settings

logger = structlog.get_logger()
app = FastAPI(title="N8N-Builder API", version="1.0")

class WorkflowTriggerRequest(BaseModel):
    workflow_name: str
    params: Dict = {}

class EnrichmentTriggerRequest(BaseModel):
    program_name: str
    phases: List[str] = ["phase_1", "phase_2", "phase_3", "phase_4"]

class DiscoveryTriggerRequest(BaseModel):
    engine: str  # federal_programs, dod_staffing, high_sub_spend
    max_results: int = 100

# Workflow execution tracking
active_workflows = {}

@app.post("/api/workflow/trigger")
async def trigger_workflow(request: WorkflowTriggerRequest):
    """Trigger an n8n workflow."""
    settings = get_settings()
    
    # Trigger via n8n webhook
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.n8n_webhook_base}/{request.workflow_name}",
                json=request.params,
                headers={"Authorization": f"Bearer {settings.n8n_api_key}"},
            )
            response.raise_for_status()
            
            execution_id = response.json().get("executionId", "unknown")
            active_workflows[execution_id] = {
                "workflow": request.workflow_name,
                "status": "running",
                "started_at": datetime.utcnow().isoformat(),
            }
            
            return {"status": "triggered", "execution_id": execution_id}
    except Exception as e:
        logger.error("workflow_trigger_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/discovery/trigger")
async def trigger_discovery(request: DiscoveryTriggerRequest):
    """Trigger a discovery engine."""
    logger.info("discovery_triggered", engine=request.engine)
    return {"status": "triggered", "engine": request.engine, "max_results": request.max_results}

@app.post("/api/enrichment/trigger")
async def trigger_enrichment(request: EnrichmentTriggerRequest):
    """Trigger program enrichment pipeline."""
    logger.info("enrichment_triggered", program=request.program_name, phases=request.phases)
    return {"status": "triggered", "program": request.program_name, "phases": request.phases}

@app.get("/api/workflow/status")
async def get_workflow_status():
    """Get status of all active workflows."""
    return {"workflows": active_workflows}

@app.get("/api/workflow/status/{execution_id}")
async def get_specific_workflow_status(execution_id: str):
    """Get status of a specific workflow."""
    if execution_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return active_workflows[execution_id]

@app.get("/api/discovery/engines")
async def list_discovery_engines():
    """List available discovery engines."""
    return {
        "engines": [
            {"name": "federal_programs", "description": "USASpending + FPDS cross-reference", "est_programs": "400-600"},
            {"name": "dod_staffing", "description": "Job board + contractor mapping", "est_programs": "200-400"},
            {"name": "high_sub_spend", "description": "Subcontractor spending analysis", "est_programs": "200-300"},
        ]
    }

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "n8n-builder"}
```

Startup script:
```bash
# run_workflow_api.sh
uvicorn api.workflow_api:app --host 0.0.0.0 --port 8300 --reload
```

Create the API and verify it starts on port 8300.
```

✅ **VERIFY:** `curl http://localhost:8300/api/health` returns OK

---

## ═══════════════════════════════════════════
## PHASE 3-5: INTEGRATION (Weeks 5+)
## ═══════════════════════════════════════════

### Step 3.1: Connect N8N-Builder APIs to Hub

⚡ **PROMPT — Paste into Auto-Claude:**

```
Register the N8N-Builder API endpoints with the BD-Engine Hub so the dashboard can proxy requests.

Create a configuration that the Hub API uses to know about available services:

```python
# services/service_registry.py
SERVICES = {
    "data_scraper": {
        "base_url": "http://localhost:8200",
        "endpoints": {
            "trigger_scrape": "/api/scraper/trigger",
            "scraper_status": "/api/scraper/status",
        }
    },
    "n8n_builder": {
        "base_url": "http://localhost:8300",
        "endpoints": {
            "trigger_workflow": "/api/workflow/trigger",
            "workflow_status": "/api/workflow/status",
            "trigger_discovery": "/api/discovery/trigger",
            "trigger_enrichment": "/api/enrichment/trigger",
            "discovery_engines": "/api/discovery/engines",
        }
    }
}
```

This goes in the BD-Engine project (Terminal A), but N8N-Builder needs to ensure its API is running and accessible.

Test that:
1. Hub can reach N8N-Builder at localhost:8300
2. Dashboard can trigger a discovery engine through Hub
3. Workflow status is visible from the dashboard
```

---

## COMPLETION CHECKLIST

At the end of all phases, verify in Terminal C:

- [ ] ALL API keys rotated (old keys from .mcp.json invalid)
- [ ] .mcp.json and .env in .gitignore, removed from git tracking
- [ ] Git history audited
- [ ] pydantic-settings for all configuration
- [ ] requirements.txt generated and pinned
- [ ] 477 bare except blocks reduced to <50 (ideally zero)
- [ ] Retry logic on all LLM and API calls
- [ ] Prompt caching on all Anthropic calls
- [ ] Structured logging replacing print()
- [ ] Pydantic models for DiscoveredProgram, EnrichmentResult, WorkflowExecution
- [ ] LanceDB fully migrated to Qdrant (zero lancedb imports)
- [ ] 7,000+ contacts exported to Qdrant contacts_unified
- [ ] Discovery engines connected to Hub API
- [ ] Workflow status API running on port 8300
- [ ] n8n workflows callable from Hub/dashboard
- [ ] Enrichment pipeline pushes results to Qdrant
- [ ] End-to-end test: discovery → enrichment → Hub → Qdrant → dashboard
