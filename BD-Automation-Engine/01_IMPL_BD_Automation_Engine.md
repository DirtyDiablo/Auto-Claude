# 🔵 TERMINAL A: BD-AUTOMATION-ENGINE
## Complete Implementation & Execution Guide

**Project Folder:** `C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine`  
**Role:** Central Hub — API Gateway, Vector DB, Multi-Agent, Dashboard  
**Maturity:** 3.2/5 → Target 4.5/5

---

## ═══════════════════════════════════════════
## PHASE 0: EMERGENCY SECURITY (Day 1)
## ═══════════════════════════════════════════
## 🔀 PARALLEL — Run simultaneously with Terminals B and C

---

### Step 0.1: Fix .gitignore

⚡ **PROMPT — Paste into Auto-Claude:**

```
Audit and fix the .gitignore file in this project. I need you to:

1. Find the current .gitignore file and show me what's in it
2. Add ALL of these patterns if they're missing:

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
dist/
build/
.vite/
*.log
.DS_Store
Thumbs.db

3. Search the entire project for any files that match these patterns and tell me if any are currently tracked by git
4. If any sensitive files ARE tracked, run: git rm --cached <filename> for each one
5. Show me the final .gitignore

Do NOT delete the actual files — only remove them from git tracking.
```

✅ **VERIFY:** Run `git status` — sensitive files should show as untracked or not listed.

---

### Step 0.2: Audit Git History for Exposed Secrets

⚡ **PROMPT — Paste into Auto-Claude:**

```
I need you to audit this project's git history for any exposed secrets or API keys. Do the following:

1. Install truffleHog if not available:
   pip install truffleHog

2. Run a full scan:
   trufflehog filesystem . --no-update

3. Also do a manual search for common patterns:
   grep -r "sk-ant-" . --include="*.py" --include="*.json" --include="*.env" --include="*.md" -l
   grep -r "sk-proj-" . --include="*.py" --include="*.json" --include="*.env" --include="*.md" -l
   grep -r "ANTHROPIC_API_KEY" . --include="*.py" --include="*.json" -l
   grep -r "OPENAI_API_KEY" . --include="*.py" --include="*.json" -l
   grep -r "apify_" . --include="*.py" --include="*.json" --include="*.env" -l

4. Report ALL findings — file path, line number, what was found (redact the actual key values)
5. For any hardcoded keys found in source code (not .env files), replace them with environment variable references like os.environ.get("ANTHROPIC_API_KEY")

Do NOT print actual API key values in your response.
```

✅ **VERIFY:** No API keys in source code files. All keys referenced via `os.environ` or `.env` only.

---

### Step 0.3: Setup Centralized Secrets Management

⚡ **PROMPT — Paste into Auto-Claude:**

```
Set up a proper secrets management system for this project:

1. Create a .env.example file with ALL required environment variables (values set to placeholder text like "your-key-here"):
   - ANTHROPIC_API_KEY=your-key-here
   - OPENAI_API_KEY=your-key-here  
   - NOTION_API_KEY=your-key-here
   - APIFY_API_TOKEN=your-key-here
   - QDRANT_URL=http://localhost:6333
   - QDRANT_API_KEY=your-key-here
   - REDIS_URL=redis://localhost:6379
   - HUB_API_URL=http://localhost:8100
   - HUB_API_KEY=your-key-here
   - N8N_WEBHOOK_URL=your-url-here
   - PROXYCURL_API_KEY=your-key-here
   - REACHER_API_KEY=your-key-here

2. Create a config/settings.py file using pydantic-settings:

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # LLM
    anthropic_api_key: str
    openai_api_key: str
    default_llm_model: str = "claude-sonnet-4-20250514"
    default_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    # Vector DB
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    
    # Cache
    redis_url: str = "redis://localhost:6379"
    
    # Notion
    notion_api_key: str
    
    # Scraping
    apify_api_token: str = ""
    
    # Hub API
    hub_api_url: str = "http://localhost:8100"
    hub_api_key: str = ""
    
    # n8n
    n8n_webhook_url: str = ""
    
    # Contact enrichment
    proxycurl_api_key: str = ""
    reacher_api_key: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

3. Make sure .env.example is committed to git but .env is NOT
4. Verify the .env file exists with real values (don't show me the values)
5. Test that Settings() loads correctly by importing and printing the qdrant_url

The goal is: every module in the project imports `from config.settings import get_settings` instead of hardcoding values.
```

✅ **VERIFY:** `python -c "from config.settings import get_settings; s = get_settings(); print(s.qdrant_url)"` prints `http://localhost:6333`

---

## ═══════════════════════════════════════════
## PHASE 1: STABILIZATION (Week 1-2)
## ═══════════════════════════════════════════
## 🔀 PARALLEL — Run simultaneously with Terminals B and C

---

### Step 1.1: Install Shared Infrastructure Packages

💻 **COMMAND — Run in terminal:**

```bash
pip install tenacity>=8.2.0 structlog>=24.1.0 pydantic>=2.6.0 pydantic-settings>=2.1.0 slowapi>=0.1.9 --break-system-packages
```

✅ **VERIFY:** `python -c "import tenacity, structlog, pydantic; print('OK')"` prints `OK`

---

### Step 1.2: Add LLM Retry Logic to All 18 Call Sites

⚡ **PROMPT — Paste into Auto-Claude:**

```
I need you to add retry logic with exponential backoff to EVERY LLM API call in this project. This is critical — there are approximately 18 LLM call sites and NONE of them have retry logic.

Here's the pattern to apply. Create a shared utility first:

1. Create a file `utils/llm_retry.py`:

```python
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from anthropic import APIError, APIConnectionError, RateLimitError
from openai import OpenAIError

logger = structlog.get_logger()

# Decorator for Anthropic calls
anthropic_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((APIError, APIConnectionError, RateLimitError)),
    before_sleep=before_sleep_log(logger, structlog.stdlib.log_level),
    reraise=True,
)

# Decorator for OpenAI calls  
openai_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((OpenAIError,)),
    before_sleep=before_sleep_log(logger, structlog.stdlib.log_level),
    reraise=True,
)

# Generic retry for any API call
api_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, IOError)),
    before_sleep=before_sleep_log(logger, structlog.stdlib.log_level),
    reraise=True,
)
```

2. Now search the entire project for ALL Anthropic API calls. Look for patterns like:
   - `client.messages.create(`
   - `anthropic.messages.create(`
   - `self.client.messages.create(`
   - `response = client.`
   - Any function that calls the Anthropic SDK

3. For EACH call site found, wrap the function (or the specific call) with the @anthropic_retry decorator. If the call is inside a method, decorate the method. If it's inline, extract to a function and decorate.

4. Do the same for ALL OpenAI API calls:
   - `client.embeddings.create(`
   - `openai.chat.completions.create(`
   - Any function that calls the OpenAI SDK

5. Report every file and function you modified with before/after snippets.

The goal: NO LLM call in this project can fail on the first attempt without retrying.
```

✅ **VERIFY:** `grep -r "@anthropic_retry\|@openai_retry\|@api_retry" . --include="*.py" | wc -l` should return 18+

---

### Step 1.3: Enable Anthropic Prompt Caching

⚡ **PROMPT — Paste into Auto-Claude:**

```
I need you to enable Anthropic prompt caching across this entire project. This will reduce our LLM costs by approximately 60%.

Here's how prompt caching works:
- Add `cache_control={"type": "ephemeral"}` to message content blocks that are repeated across calls
- System prompts, few-shot examples, and large context blocks are prime candidates
- Cached content must be at least 1024 tokens to qualify

Steps:

1. Search all files for Anthropic API calls (client.messages.create)

2. For each call, identify the system prompt and any large repeated context. Then modify the call to use cache_control. Here's the pattern:

BEFORE:
```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system="You are a BD intelligence analyst...",
    messages=[{"role": "user", "content": user_message}]
)
```

AFTER:
```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system=[
        {
            "type": "text",
            "text": "You are a BD intelligence analyst specialized in federal defense programs...",
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[{"role": "user", "content": user_message}]
)
```

3. For calls that include large context in user messages (like RAG retrieved documents), add cache_control to the context block:

```python
messages=[
    {
        "role": "user", 
        "content": [
            {
                "type": "text",
                "text": large_context_string,
                "cache_control": {"type": "ephemeral"}
            },
            {
                "type": "text",
                "text": actual_user_question
            }
        ]
    }
]
```

4. Find and modify ALL Anthropic calls. Report each one with the file path and what you changed.

Important: Don't change the actual prompt content — only add cache_control wrappers around the content structure.
```

✅ **VERIFY:** `grep -r "cache_control" . --include="*.py" | wc -l` should return 15+

---

### Step 1.4: Implement Structured Logging

⚡ **PROMPT — Paste into Auto-Claude:**

```
Replace all print() statements and basic logging with structured JSON logging using structlog across the entire project.

1. Create `utils/logging_config.py`:

```python
import structlog
import logging
import sys

def setup_logging(log_level: str = "INFO"):
    """Configure structured logging for the entire application."""
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if not sys.stderr.isatty() 
            else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Call on import
setup_logging()
```

2. Search the entire project for `print(` statements that are logging/debug output (not user-facing output). Replace them with structured log calls:

BEFORE:
```python
print(f"Processing contact {name}")
print(f"Error: {e}")
```

AFTER:  
```python
import structlog
logger = structlog.get_logger()

logger.info("processing_contact", name=name)
logger.error("processing_failed", error=str(e), contact=name)
```

3. Replace all `logging.info/warning/error` calls with structlog equivalents.

4. Add the import `from utils.logging_config import setup_logging` to the main entry points (main.py, server.py, etc.)

5. Focus on the most critical modules first:
   - FastAPI server (all endpoints)
   - BD engines (ScraperEngine, ProgramMappingEngine, etc.)
   - LLM call sites (already modified in Step 1.2)
   - Vector DB operations

Don't modify test files, scripts meant for one-time use, or example files.
Report all files modified.
```

✅ **VERIFY:** `grep -r "structlog.get_logger" . --include="*.py" | wc -l` should return 20+

---

### Step 1.5: Add Pydantic Data Models

⚡ **PROMPT — Paste into Auto-Claude:**

```
Create Pydantic v2 data models for all core data structures in this project. These models enforce type safety and validation on all data flowing through the system.

1. Create `models/base.py`:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from enum import Enum

class SourceProject(str, Enum):
    BD_ENGINE = "bd_engine"
    DATA_SCRAPER = "data_scraper"
    N8N_BUILDER = "n8n_builder"

class BaseDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_project: SourceProject = SourceProject.BD_ENGINE
    source_type: str = "unknown"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    content_hash: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    tags: List[str] = Field(default_factory=list)
    notion_page_id: Optional[str] = None
```

2. Create `models/contacts.py`:

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum
from .base import BaseDocument

class HierarchyTier(str, Enum):
    TIER_1_EXECUTIVE = "Tier 1 - Executive"
    TIER_2_DIRECTOR = "Tier 2 - Director"
    TIER_3_PROGRAM_LEADERSHIP = "Tier 3 - Program Leadership"
    TIER_4_MANAGEMENT = "Tier 4 - Management"
    TIER_5_SENIOR_IC = "Tier 5 - Senior IC"
    TIER_6_IC = "Tier 6 - Individual Contributor"

class BDPriority(str, Enum):
    CRITICAL = "🔴 Critical"
    HIGH = "🟠 High"
    MEDIUM = "🟡 Medium"
    STANDARD = "⚪ Standard"

class DCGSProgram(str, Enum):
    AF_LANGLEY = "AF DCGS - Langley"
    AF_WRIGHT_PATT = "AF DCGS - Wright-Patt"
    AF_PACAF = "AF DCGS - PACAF"
    AF_OTHER = "AF DCGS - Other"
    ARMY_DCGS_A = "Army DCGS-A"
    NAVY_DCGS_N = "Navy DCGS-N"
    CORPORATE_HQ = "Corporate HQ"
    ENTERPRISE_SECURITY = "Enterprise Security"
    UNASSIGNED = "Unassigned"

class LocationHub(str, Enum):
    HAMPTON_ROADS = "Hampton Roads"
    SAN_DIEGO = "San Diego Metro"
    DC_METRO = "DC Metro"
    DAYTON = "Dayton/Wright-Patt"
    OTHER_CONUS = "Other CONUS"
    OCONUS = "OCONUS"
    UNKNOWN = "Unknown"

class Contact(BaseDocument):
    first_name: str
    last_name: str
    job_title: Optional[str] = None
    company: str = "GDIT"
    email: Optional[str] = None
    phone: Optional[str] = None
    direct_phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    program: DCGSProgram = DCGSProgram.UNASSIGNED
    hierarchy_tier: HierarchyTier = HierarchyTier.TIER_6_IC
    bd_priority: BDPriority = BDPriority.STANDARD
    location_hub: LocationHub = LocationHub.UNKNOWN
    functional_areas: List[str] = Field(default_factory=list)
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

3. Create `models/programs.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from .base import BaseDocument

class PTSInvolvement(str, Enum):
    CURRENT = "Current"
    PAST = "Past"
    TARGET = "Target"
    NONE = "None"

class PriorityLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class FederalProgram(BaseDocument):
    program_name: str
    acronym: Optional[str] = None
    agency_owner: Optional[str] = None
    prime_contractor: Optional[str] = None
    known_subcontractors: List[str] = Field(default_factory=list)
    contract_value: Optional[str] = None
    contract_vehicle: Optional[str] = None
    pop_start: Optional[str] = None
    pop_end: Optional[str] = None
    key_locations: List[str] = Field(default_factory=list)
    clearance_requirements: Optional[str] = None
    typical_roles: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    program_type: Optional[str] = None
    pts_involvement: PTSInvolvement = PTSInvolvement.NONE
    priority_level: PriorityLevel = PriorityLevel.MEDIUM
    pain_points: List[str] = Field(default_factory=list)
    confidence_level: Optional[str] = None
```

4. Create `models/jobs.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from .base import BaseDocument

class JobStatus(str, Enum):
    RAW_IMPORT = "raw_import"
    PENDING_ENRICHMENT = "pending_enrichment"
    ENRICHING = "enriching"
    ENRICHED = "enriched"
    VALIDATED = "validated"
    ERROR = "error"

class ScrapedJob(BaseDocument):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    detected_clearance: Optional[str] = None
    primary_keyword: Optional[str] = None
    scraped_at: Optional[str] = None
    status: JobStatus = JobStatus.RAW_IMPORT
    mapped_program: Optional[str] = None
    bd_score: float = Field(default=0, ge=0, le=100)
    match_confidence: float = Field(default=0, ge=0, le=1)
```

5. Create `models/activities.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .base import BaseDocument

class ActivityType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    LINKEDIN = "linkedin"
    MEETING = "meeting"
    NOTE = "note"
    HUMINT = "humint"
    SCRAPE = "scrape"
    ENRICHMENT = "enrichment"

class Activity(BaseDocument):
    contact_name: Optional[str] = None
    contact_id: Optional[str] = None
    activity_type: ActivityType
    summary: str
    outcome: Optional[str] = None
    author: Optional[str] = None
    program: Optional[str] = None
    follow_up_date: Optional[datetime] = None
```

6. Create `models/__init__.py`:

```python
from .base import BaseDocument, SourceProject
from .contacts import Contact, HierarchyTier, BDPriority, DCGSProgram, LocationHub
from .programs import FederalProgram, PTSInvolvement, PriorityLevel
from .jobs import ScrapedJob, JobStatus
from .activities import Activity, ActivityType

__all__ = [
    "BaseDocument", "SourceProject",
    "Contact", "HierarchyTier", "BDPriority", "DCGSProgram", "LocationHub",
    "FederalProgram", "PTSInvolvement", "PriorityLevel",
    "ScrapedJob", "JobStatus",
    "Activity", "ActivityType",
]
```

Create all these files. These models will be used by all 3 projects (the other projects will import from this package or copy the models).
```

✅ **VERIFY:** `python -c "from models import Contact, FederalProgram, ScrapedJob; print('Models OK')"` prints `Models OK`

---

### Step 1.6: Add API Authentication and Rate Limiting

⚡ **PROMPT — Paste into Auto-Claude:**

```
Add API key authentication and rate limiting to the FastAPI Hub server.

1. Find the main FastAPI app file (likely server.py or main.py or app.py)

2. Add authentication middleware:

```python
from fastapi import Security, HTTPException, Depends
from fastapi.security import APIKeyHeader
from config.settings import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    settings = get_settings()
    if not settings.hub_api_key:
        return True  # No key configured = open access (dev mode)
    if api_key != settings.hub_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True
```

3. Add rate limiting with slowapi:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

4. Apply to all endpoints. For critical endpoints add both:

```python
@app.get("/api/contacts/search")
@limiter.limit("30/minute")
async def search_contacts(
    request: Request,
    query: str,
    authenticated: bool = Depends(verify_api_key)
):
    ...
```

5. For less critical endpoints, just add auth:

```python
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}  # No auth needed for health check
```

Apply authentication to ALL endpoints except /health and /docs.
Apply rate limiting to search and write endpoints (30/min for search, 10/min for writes).
Show me all endpoints you modified.
```

✅ **VERIFY:** `curl -H "X-API-Key: wrong" http://localhost:8100/api/contacts/search?query=test` returns 401

---

### Step 1.7: Clean Dashboard Temporary Files

⚡ **PROMPT — Paste into Auto-Claude:**

```
Clean up the BD Dashboard. There are approximately 50+ temporary, orphaned, and backup files cluttering the frontend code.

1. Find the dashboard directory (likely in src/dashboard or frontend/ or client/)

2. Search for and list ALL files matching these patterns:
   - *.backup.*
   - *.bak
   - *.old
   - *.copy.*
   - *_temp.*
   - *_tmp.*
   - *.orig
   - Files with "test" or "experiment" in the name that aren't actual test files
   - Duplicate files (same content, different names)
   - Files with trailing numbers like Component2.tsx, Page_v2.jsx

3. Show me the complete list with file sizes BEFORE deleting anything.

4. For each file, check if it's imported anywhere. If NOT imported by any other file, it's safe to delete.

5. Delete all confirmed orphaned/temp files.

6. Also find and remove:
   - Empty files (0 bytes)
   - Console.log statements that are clearly debug output
   - Commented-out code blocks longer than 20 lines

7. Report: files deleted, total size recovered, any files you kept and why.

Do NOT delete files that are actively imported or referenced by other files.
```

✅ **VERIFY:** The file count in the dashboard directory should be noticeably smaller.

---

### Step 1.8: Add React Error Boundaries

⚡ **PROMPT — Paste into Auto-Claude:**

```
Add React Error Boundaries to the BD Dashboard to prevent component crashes from taking down the entire app.

1. Find the dashboard source directory

2. Create a reusable ErrorBoundary component:

```tsx
// src/components/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg m-4">
          <h2 className="text-red-800 font-bold text-lg mb-2">Something went wrong</h2>
          <p className="text-red-600 mb-4">{this.state.error?.message}</p>
          <button 
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
```

3. Wrap the main app layout and each major section/page component with ErrorBoundary:

```tsx
// In the main App component or layout:
<ErrorBoundary>
  <Sidebar />
</ErrorBoundary>
<ErrorBoundary>
  <MainContent />
</ErrorBoundary>
```

4. Find the main routing/page-switching logic and wrap each page/route with its own ErrorBoundary so one page crashing doesn't affect others.

5. Show me all files you modified.
```

✅ **VERIFY:** The dashboard loads without crashing. If any component fails, it shows the error fallback instead of a white screen.

---

## ═══════════════════════════════════════════
## PHASE 2: DATABASE UNIFICATION (Weeks 2-4)
## ═══════════════════════════════════════════
## ⚠️ TERMINAL A LEADS — Terminals B and C wait for Steps 2.1-2.2

---

### Step 2.1: Create Unified Qdrant Collections

⚡ **PROMPT — Paste into Auto-Claude:**

```
I need you to create the unified Qdrant collection architecture. We're consolidating 3 vector databases (Qdrant, ChromaDB, LanceDB) into a single Qdrant instance with 12 purpose-built collections.

First, verify Qdrant is running:
```bash
curl http://localhost:6333/collections
```

Then create a script `scripts/create_unified_collections.py`:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, 
    PayloadSchemaType, TextIndexParams, TokenizerType
)

client = QdrantClient(url="http://localhost:6333")

COLLECTIONS = {
    "contacts_unified": {
        "description": "All contacts from BD-Engine, N8N-Builder, ZoomInfo",
        "payload_indexes": ["program", "hierarchy_tier", "bd_priority", "location_hub", "company", "source_project"]
    },
    "programs_unified": {
        "description": "Federal programs from all sources",
        "payload_indexes": ["agency_owner", "prime_contractor", "pts_involvement", "priority_level", "status"]
    },
    "jobs_unified": {
        "description": "All scraped and tracked jobs",
        "payload_indexes": ["company", "detected_clearance", "location", "mapped_program", "status", "source_project"]
    },
    "contracts_federal": {
        "description": "USASpending + FPDS federal contract data",
        "payload_indexes": ["agency", "contractor", "naics", "contract_type", "fiscal_year"]
    },
    "activities_log": {
        "description": "All BD engagement activities",
        "payload_indexes": ["contact_name", "activity_type", "program", "author", "date"]
    },
    "documents_kb": {
        "description": "Playbooks, reports, briefings",
        "payload_indexes": ["doc_type", "program", "author", "date"]
    },
    "bullhorn_history": {
        "description": "38K Bullhorn CRM records",
        "payload_indexes": ["candidate", "client", "role_type", "date", "outcome"]
    },
    "knowledge_graph": {
        "description": "LightRAG entity extractions",
        "payload_indexes": ["entity_type", "source", "relationship_type"]
    },
    "intelligence_briefs": {
        "description": "HUMINT reports and weekly updates",
        "payload_indexes": ["source_tier", "confidence", "program", "date"]
    },
    "email_templates": {
        "description": "Generated outreach content",
        "payload_indexes": ["contact_tier", "program", "template_type"]
    },
    "competitor_intel": {
        "description": "Competitor analysis data",
        "payload_indexes": ["competitor", "program", "location", "role_type"]
    },
    "pipeline_tracking": {
        "description": "Active BD opportunities",
        "payload_indexes": ["stage", "contact", "program", "probability"]
    },
}

def create_all_collections():
    for name, config in COLLECTIONS.items():
        # Check if exists
        existing = [c.name for c in client.get_collections().collections]
        if name in existing:
            print(f"  Collection '{name}' already exists — skipping")
            continue
        
        # Create with 1536-dim vectors (text-embedding-3-small)
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=1536,
                distance=Distance.COSINE,
            ),
        )
        
        # Create payload indexes for fast filtering
        for field in config["payload_indexes"]:
            client.create_payload_index(
                collection_name=name,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD,
            )
        
        # Add full-text index on 'content' field for hybrid search
        client.create_payload_index(
            collection_name=name,
            field_name="content",
            field_schema=TextIndexParams(
                type="text",
                tokenizer=TokenizerType.WORD,
                min_token_len=2,
                max_token_len=20,
                lowercase=True,
            ),
        )
        
        print(f"  Created collection '{name}' with {len(config['payload_indexes'])} indexes + full-text")

    print("\nAll collections created. Verify:")
    for c in client.get_collections().collections:
        info = client.get_collection(c.name)
        print(f"  {c.name}: {info.points_count} vectors")

if __name__ == "__main__":
    create_all_collections()
```

Run this script and show me the output. All 12 collections should be created with proper indexes.
```

✅ **VERIFY:** `curl http://localhost:6333/collections | python -m json.tool` shows 12+ collections

---

### Step 2.2: Re-embed bd_knowledge Collection (384d → 1536d)

⚡ **PROMPT — Paste into Auto-Claude:**

```
The bd_knowledge collection in Qdrant uses 384-dimension embeddings (all-MiniLM-L6-v2) while all other collections use 1536-dimension (text-embedding-3-small). I need you to:

1. Export all vectors and payloads from the bd_knowledge collection
2. Re-embed the text content using text-embedding-3-small (1536d)
3. Load the re-embedded vectors into the knowledge_graph collection (already created in Step 2.1)
4. Verify the migration
5. Optionally delete the old bd_knowledge collection

Create and run a script `scripts/migrate_bd_knowledge.py`:

```python
import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from openai import OpenAI

client = QdrantClient(url="http://localhost:6333")
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_embedding(text: str) -> list:
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

# Step 1: Export from bd_knowledge
print("Exporting from bd_knowledge...")
records = []
offset = None
while True:
    result = client.scroll(
        collection_name="bd_knowledge",
        limit=100,
        offset=offset,
        with_vectors=False,  # Don't need old vectors
        with_payload=True,
    )
    points, offset = result
    records.extend(points)
    if offset is None:
        break

print(f"Exported {len(records)} records")

# Step 2: Re-embed and insert into knowledge_graph
print("Re-embedding with text-embedding-3-small...")
batch = []
for i, record in enumerate(records):
    # Get the text content to embed
    text = record.payload.get("content", "") or record.payload.get("text", "") or str(record.payload)
    
    if not text.strip():
        continue
    
    embedding = get_embedding(text)
    
    # Add source tracking
    payload = dict(record.payload)
    payload["source_project"] = "bd_engine"
    payload["embedding_model"] = "text-embedding-3-small"
    payload["migrated_from"] = "bd_knowledge"
    
    batch.append(PointStruct(
        id=str(record.id),
        vector=embedding,
        payload=payload,
    ))
    
    if len(batch) >= 50:
        client.upsert(collection_name="knowledge_graph", points=batch)
        print(f"  Inserted batch ({i+1}/{len(records)})")
        batch = []

if batch:
    client.upsert(collection_name="knowledge_graph", points=batch)
    print(f"  Inserted final batch")

# Step 3: Verify
kg_info = client.get_collection("knowledge_graph")
print(f"\nMigration complete:")
print(f"  knowledge_graph: {kg_info.points_count} vectors (1536d)")
print(f"  Old bd_knowledge can be deleted when ready")
```

Run this script. It should migrate all records from the 384d collection to the new 1536d collection.
```

✅ **VERIFY:** `curl http://localhost:6333/collections/knowledge_graph | python -m json.tool` shows vectors with 1536 dimensions

---

### Step 2.3: Build Unified Hub API Extensions

⚡ **PROMPT — Paste into Auto-Claude:**

```
Extend the FastAPI Hub API with new endpoints that the dashboard and other projects will use for unified data access. These endpoints query the new unified Qdrant collections.

Create a new file `api/unified_endpoints.py`:

```python
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional, List
from qdrant_client import QdrantClient
from openai import OpenAI
import structlog
from config.settings import get_settings
from models import Contact, FederalProgram, ScrapedJob, Activity

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v2", tags=["unified"])

def get_qdrant():
    settings = get_settings()
    return QdrantClient(url=settings.qdrant_url)

def get_embedding(text: str) -> list:
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(input=text, model=settings.default_embedding_model)
    return response.data[0].embedding

# ====== UNIFIED SEARCH ======

@router.get("/search")
async def unified_search(
    query: str = Query(..., min_length=2),
    collections: Optional[str] = Query(None, description="Comma-separated collection names"),
    limit: int = Query(10, ge=1, le=100),
    filters: Optional[str] = Query(None, description="JSON filter object"),
):
    """Search across all or specific unified collections."""
    qdrant = get_qdrant()
    embedding = get_embedding(query)
    
    target_collections = collections.split(",") if collections else [
        "contacts_unified", "programs_unified", "jobs_unified", 
        "activities_log", "documents_kb"
    ]
    
    results = []
    for coll in target_collections:
        try:
            hits = qdrant.search(
                collection_name=coll.strip(),
                query_vector=embedding,
                limit=limit,
                with_payload=True,
            )
            for hit in hits:
                results.append({
                    "collection": coll.strip(),
                    "score": hit.score,
                    "id": str(hit.id),
                    "payload": hit.payload,
                })
        except Exception as e:
            logger.warning("search_collection_failed", collection=coll, error=str(e))
    
    # Sort by score across all collections
    results.sort(key=lambda x: x["score"], reverse=True)
    return {"results": results[:limit], "total": len(results), "query": query}

# ====== CONTACTS ======

@router.get("/contacts")
async def list_contacts(
    program: Optional[str] = None,
    tier: Optional[str] = None,
    priority: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List contacts with filtering."""
    qdrant = get_qdrant()
    
    must_conditions = []
    if program:
        must_conditions.append({"key": "program", "match": {"value": program}})
    if tier:
        must_conditions.append({"key": "hierarchy_tier", "match": {"value": tier}})
    if priority:
        must_conditions.append({"key": "bd_priority", "match": {"value": priority}})
    if location:
        must_conditions.append({"key": "location_hub", "match": {"value": location}})
    
    filter_obj = {"must": must_conditions} if must_conditions else None
    
    results = qdrant.scroll(
        collection_name="contacts_unified",
        scroll_filter=filter_obj,
        limit=limit,
        offset=offset,
        with_payload=True,
    )
    
    points, next_offset = results
    return {
        "contacts": [{"id": str(p.id), **p.payload} for p in points],
        "total": len(points),
        "next_offset": next_offset,
    }

@router.get("/contacts/search")
async def search_contacts(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
):
    """Semantic search across contacts."""
    qdrant = get_qdrant()
    embedding = get_embedding(query)
    
    hits = qdrant.search(
        collection_name="contacts_unified",
        query_vector=embedding,
        limit=limit,
        with_payload=True,
    )
    
    return {
        "results": [{"id": str(h.id), "score": h.score, **h.payload} for h in hits],
        "query": query,
    }

# ====== PROGRAMS ======

@router.get("/programs")
async def list_programs(
    prime: Optional[str] = None,
    pts_involvement: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    """List federal programs with filtering."""
    qdrant = get_qdrant()
    
    must_conditions = []
    if prime:
        must_conditions.append({"key": "prime_contractor", "match": {"value": prime}})
    if pts_involvement:
        must_conditions.append({"key": "pts_involvement", "match": {"value": pts_involvement}})
    if priority:
        must_conditions.append({"key": "priority_level", "match": {"value": priority}})
    
    filter_obj = {"must": must_conditions} if must_conditions else None
    
    results = qdrant.scroll(
        collection_name="programs_unified",
        scroll_filter=filter_obj,
        limit=limit,
        with_payload=True,
    )
    
    points, _ = results
    return {"programs": [{"id": str(p.id), **p.payload} for p in points], "total": len(points)}

# ====== JOBS ======

@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    program: Optional[str] = None,
    clearance: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    """List jobs with filtering."""
    qdrant = get_qdrant()
    
    must_conditions = []
    if status:
        must_conditions.append({"key": "status", "match": {"value": status}})
    if program:
        must_conditions.append({"key": "mapped_program", "match": {"value": program}})
    if clearance:
        must_conditions.append({"key": "detected_clearance", "match": {"value": clearance}})
    
    filter_obj = {"must": must_conditions} if must_conditions else None
    
    results = qdrant.scroll(
        collection_name="jobs_unified",
        scroll_filter=filter_obj,
        limit=limit,
        with_payload=True,
    )
    
    points, _ = results
    return {"jobs": [{"id": str(p.id), **p.payload} for p in points], "total": len(points)}

# ====== PIPELINE ======

@router.get("/pipeline")
async def get_pipeline():
    """Get BD pipeline overview."""
    qdrant = get_qdrant()
    
    results = qdrant.scroll(
        collection_name="pipeline_tracking",
        limit=500,
        with_payload=True,
    )
    
    points, _ = results
    stages = {}
    for p in points:
        stage = p.payload.get("stage", "unknown")
        if stage not in stages:
            stages[stage] = []
        stages[stage].append({"id": str(p.id), **p.payload})
    
    return {"pipeline": stages, "total": len(points)}

# ====== ANALYTICS ======

@router.get("/analytics/overview")
async def analytics_overview():
    """Get cross-collection analytics."""
    qdrant = get_qdrant()
    
    collections_data = {}
    for name in ["contacts_unified", "programs_unified", "jobs_unified", 
                  "activities_log", "pipeline_tracking"]:
        try:
            info = qdrant.get_collection(name)
            collections_data[name] = {"count": info.points_count}
        except:
            collections_data[name] = {"count": 0}
    
    return {
        "total_contacts": collections_data["contacts_unified"]["count"],
        "total_programs": collections_data["programs_unified"]["count"],
        "total_jobs": collections_data["jobs_unified"]["count"],
        "total_activities": collections_data["activities_log"]["count"],
        "pipeline_items": collections_data["pipeline_tracking"]["count"],
    }

# ====== TOOLS / OPERATIONS ======

@router.post("/tools/trigger-scrape")
async def trigger_scrape(scraper_name: str = "insight_global"):
    """Trigger a job scraper run (proxied to Data-Scraper)."""
    # This will be connected to Data-Scraper's API
    return {"status": "triggered", "scraper": scraper_name, "message": "Connect to Data-Scraper API"}

@router.post("/tools/trigger-enrichment")  
async def trigger_enrichment(program_id: str):
    """Trigger program enrichment (proxied to N8N-Builder)."""
    # This will be connected to N8N-Builder's API
    return {"status": "triggered", "program": program_id, "message": "Connect to N8N-Builder API"}

@router.get("/collections/stats")
async def collection_stats():
    """Get stats for all unified collections."""
    qdrant = get_qdrant()
    stats = {}
    for c in qdrant.get_collections().collections:
        info = qdrant.get_collection(c.name)
        stats[c.name] = {
            "vectors": info.points_count,
            "status": str(info.status),
        }
    return stats
```

Now register this router in the main FastAPI app:

```python
from api.unified_endpoints import router as unified_router
app.include_router(unified_router)
```

Create this file, register the router, and verify the endpoints are accessible.
```

✅ **VERIFY:** `curl http://localhost:8100/api/v2/collections/stats` returns collection counts

---

### Step 2.4: Build Notion ↔ Qdrant Bidirectional Sync

⚡ **PROMPT — Paste into Auto-Claude:**

```
Create a bidirectional sync system between Notion databases and Qdrant collections. When a contact is updated in Notion, it should be reflected in Qdrant, and when new data is imported to Qdrant, it can push updates to Notion.

Create `services/notion_qdrant_sync.py`:

```python
"""
Bidirectional sync between Notion databases and Qdrant unified collections.
Runs on a schedule or triggered via API.
"""
import os
import hashlib
import json
import structlog
from datetime import datetime
from typing import Optional, Dict, List
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()

# Notion Collection IDs
NOTION_COLLECTIONS = {
    "dcgs_contacts": "2ccdef65-baa5-8087-a53b-000ba596128e",
    "gdit_other": "70ea1c94-211d-40e6-a994-e8d7c4807434",
    "gdit_jobs": "2ccdef65-baa5-80b0-9a80-000bd2745f63",
    "program_mapping": "f57792c1-605b-424c-8830-23ab41c47137",
    "federal_programs": "06cd9b22-5d6b-4d37-b0d3-ba99da4971fa",
}

QDRANT_MAPPING = {
    "dcgs_contacts": "contacts_unified",
    "gdit_other": "contacts_unified",
    "gdit_jobs": "jobs_unified",
    "program_mapping": "jobs_unified",
    "federal_programs": "programs_unified",
}

class NotionQdrantSync:
    def __init__(self):
        self.qdrant = QdrantClient(url=os.environ.get("QDRANT_URL", "http://localhost:6333"))
        self.openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.notion_key = os.environ.get("NOTION_API_KEY")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=30))
    def get_embedding(self, text: str) -> list:
        response = self.openai.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    
    def content_hash(self, data: dict) -> str:
        """Generate hash for deduplication."""
        return hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
    
    def build_contact_text(self, props: dict) -> str:
        """Build searchable text from contact properties."""
        parts = []
        name = f"{props.get('first_name', '')} {props.get('last_name', '')}".strip()
        if name: parts.append(f"Name: {name}")
        if props.get('job_title'): parts.append(f"Title: {props['job_title']}")
        if props.get('company'): parts.append(f"Company: {props['company']}")
        if props.get('program'): parts.append(f"Program: {props['program']}")
        if props.get('city'): parts.append(f"Location: {props['city']}, {props.get('state', '')}")
        return ". ".join(parts)
    
    def sync_contacts_to_qdrant(self, notion_records: List[dict], source_db: str = "dcgs_contacts"):
        """Sync Notion contact records to Qdrant contacts_unified."""
        collection = QDRANT_MAPPING[source_db]
        batch = []
        
        for record in notion_records:
            text = self.build_contact_text(record)
            if not text.strip():
                continue
            
            embedding = self.get_embedding(text)
            
            payload = {
                **record,
                "content": text,
                "source_project": "bd_engine",
                "source_type": f"notion_{source_db}",
                "content_hash": self.content_hash(record),
                "embedding_model": "text-embedding-3-small",
                "synced_at": datetime.utcnow().isoformat(),
            }
            
            point_id = record.get("notion_page_id", self.content_hash(record))
            batch.append(PointStruct(id=point_id, vector=embedding, payload=payload))
            
            if len(batch) >= 50:
                self.qdrant.upsert(collection_name=collection, points=batch)
                logger.info("sync_batch", collection=collection, count=len(batch))
                batch = []
        
        if batch:
            self.qdrant.upsert(collection_name=collection, points=batch)
        
        logger.info("sync_complete", source=source_db, collection=collection, total=len(notion_records))
    
    def get_sync_status(self) -> dict:
        """Get current sync status for all collections."""
        status = {}
        for name in QDRANT_MAPPING.values():
            try:
                info = self.qdrant.get_collection(name)
                status[name] = {"vectors": info.points_count, "status": str(info.status)}
            except Exception as e:
                status[name] = {"vectors": 0, "error": str(e)}
        return status

if __name__ == "__main__":
    sync = NotionQdrantSync()
    print(json.dumps(sync.get_sync_status(), indent=2))
```

Create this file. Then add an API endpoint to trigger sync:

In `api/unified_endpoints.py`, add:

```python
@router.post("/sync/notion-to-qdrant")
async def trigger_notion_sync(source_db: str = "dcgs_contacts"):
    """Trigger Notion → Qdrant sync for a specific database."""
    from services.notion_qdrant_sync import NotionQdrantSync
    sync = NotionQdrantSync()
    # The actual Notion query would go here
    return {"status": "sync_triggered", "source": source_db}

@router.get("/sync/status")
async def sync_status():
    """Get sync status for all collections."""
    from services.notion_qdrant_sync import NotionQdrantSync
    sync = NotionQdrantSync()
    return sync.get_sync_status()
```

Create all files and verify.
```

✅ **VERIFY:** `curl http://localhost:8100/api/v2/sync/status` returns collection vector counts

---

### Steps 2.5-2.7 continue the database work. Due to length, here are the prompts in condensed form:

### Step 2.5: Migrate Existing BD-Engine Qdrant Data to Unified Collections

⚡ **PROMPT — Paste into Auto-Claude:**

```
Create a migration script that copies data from the existing BD-Engine Qdrant collections (bd_contacts, bd_programs, bd_jobs, bd_activities, bd_documents) into the new unified collections (contacts_unified, programs_unified, jobs_unified, activities_log, documents_kb).

The script should:
1. Read all vectors + payloads from each old collection
2. Add source_project="bd_engine" and source_type="qdrant_migration" to each payload
3. Upsert into the corresponding new collection
4. Preserve the original vector embeddings (they're already 1536d)
5. Print progress and final counts for each collection

Map:
- bd_contacts → contacts_unified
- bd_programs → programs_unified  
- bd_jobs → jobs_unified
- bd_activities → activities_log
- bd_documents → documents_kb

Create the script at scripts/migrate_existing_qdrant.py and run it.
Do NOT delete old collections — we keep them as backup until verified.
```

### Step 2.6: Build LightRAG Knowledge Graph Feed

⚡ **PROMPT — Paste into Auto-Claude:**

```
Set up the LightRAG knowledge graph to process data from all unified Qdrant collections. Create a script that:

1. Reads the top 1000 records from contacts_unified, programs_unified, and jobs_unified
2. For each record, extracts entities and relationships using LightRAG's entity extraction
3. Stores the extracted graph data in the knowledge_graph collection
4. Creates a function that can be called incrementally as new data arrives

Create scripts/build_knowledge_graph.py with this logic. Use the existing LightRAG installation in the project.

The key relationships to extract:
- Person WORKS_AT Company
- Person MANAGES Program  
- Company IS_PRIME_ON Program
- Company IS_SUB_ON Program
- Job IS_FOR Program
- Job LOCATED_AT Location
- Program REQUIRES Clearance

Run the script on a sample of 100 records first to verify, then process the full dataset.
```

### Step 2.7: Test Unified Search

⚡ **PROMPT — Paste into Auto-Claude:**

```
Create a test script that validates the unified search is working correctly across all collections. Test the following queries and verify results are relevant:

1. "network engineer San Diego TS/SCI" → should return contacts + jobs in San Diego
2. "DCGS PACAF site lead" → should return Kingsley Ero and related contacts
3. "GDIT prime contractor intelligence" → should return programs where GDIT is prime
4. "PTS past performance BICES" → should return relevant past performance documents
5. "cyber analyst Langley opening" → should return jobs and contacts at Langley

Create scripts/test_unified_search.py that runs all 5 queries against the /api/v2/search endpoint and prints results with scores.

Also test individual collection endpoints:
- GET /api/v2/contacts?program=AF DCGS - PACAF
- GET /api/v2/programs?prime=GDIT
- GET /api/v2/jobs?status=enriched
- GET /api/v2/analytics/overview
- GET /api/v2/collections/stats

Report all results. Flag any endpoints that return errors or empty results.
```

---

## ═══════════════════════════════════════════
## PHASE 3: DASHBOARD REBUILD (Weeks 5-8)
## ═══════════════════════════════════════════

---

### Step 3.1: Install TanStack Router and Query

⚡ **PROMPT — Paste into Auto-Claude:**

```
Upgrade the BD Dashboard with TanStack Router and TanStack Query. Find the dashboard directory (the React app within this project).

1. Install packages:
```bash
cd [dashboard_directory]
npm install @tanstack/react-router @tanstack/react-query @tanstack/react-query-devtools
npm install @tanstack/router-devtools
npm install react-hook-form @hookform/resolvers zod
```

2. Create the router configuration at `src/router.tsx`:

```tsx
import { createRouter, createRoute, createRootRoute } from '@tanstack/react-router';
import { lazy } from 'react';
import RootLayout from './layouts/RootLayout';

const rootRoute = createRootRoute({ component: RootLayout });

// Lazy-loaded routes for code splitting
const indexRoute = createRoute({ getParentRoute: () => rootRoute, path: '/', component: lazy(() => import('./pages/Dashboard')) });
const contactsRoute = createRoute({ getParentRoute: () => rootRoute, path: '/contacts', component: lazy(() => import('./pages/Contacts')) });
const contactDetailRoute = createRoute({ getParentRoute: () => rootRoute, path: '/contacts/$contactId', component: lazy(() => import('./pages/ContactDetail')) });
const programsRoute = createRoute({ getParentRoute: () => rootRoute, path: '/programs', component: lazy(() => import('./pages/Programs')) });
const programDetailRoute = createRoute({ getParentRoute: () => rootRoute, path: '/programs/$programId', component: lazy(() => import('./pages/ProgramDetail')) });
const jobsRoute = createRoute({ getParentRoute: () => rootRoute, path: '/jobs', component: lazy(() => import('./pages/Jobs')) });
const pipelineRoute = createRoute({ getParentRoute: () => rootRoute, path: '/pipeline', component: lazy(() => import('./pages/Pipeline')) });
const humintRoute = createRoute({ getParentRoute: () => rootRoute, path: '/humint', component: lazy(() => import('./pages/Humint')) });
const playbooksRoute = createRoute({ getParentRoute: () => rootRoute, path: '/playbooks', component: lazy(() => import('./pages/Playbooks')) });
const toolsRoute = createRoute({ getParentRoute: () => rootRoute, path: '/tools', component: lazy(() => import('./pages/Tools')) });
const scrapersRoute = createRoute({ getParentRoute: () => rootRoute, path: '/scrapers', component: lazy(() => import('./pages/Scrapers')) });
const analyticsRoute = createRoute({ getParentRoute: () => rootRoute, path: '/analytics', component: lazy(() => import('./pages/Analytics')) });
const orgChartRoute = createRoute({ getParentRoute: () => rootRoute, path: '/org-chart', component: lazy(() => import('./pages/OrgChart')) });
const settingsRoute = createRoute({ getParentRoute: () => rootRoute, path: '/settings', component: lazy(() => import('./pages/Settings')) });

const routeTree = rootRoute.addChildren([
  indexRoute, contactsRoute, contactDetailRoute,
  programsRoute, programDetailRoute, jobsRoute,
  pipelineRoute, humintRoute, playbooksRoute,
  toolsRoute, scrapersRoute, analyticsRoute,
  orgChartRoute, settingsRoute,
]);

export const router = createRouter({ routeTree });
```

3. Create `src/lib/api-client.ts` for typed API access:

```typescript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8100';
const API_KEY = import.meta.env.VITE_API_KEY || '';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }
  
  return response.json();
}

export const api = {
  // Unified search
  search: (query: string, collections?: string) => 
    apiFetch<any>(`/api/v2/search?query=${encodeURIComponent(query)}${collections ? `&collections=${collections}` : ''}`),
  
  // Contacts
  contacts: {
    list: (params?: Record<string, string>) => 
      apiFetch<any>(`/api/v2/contacts?${new URLSearchParams(params || {})}`),
    search: (query: string) =>
      apiFetch<any>(`/api/v2/contacts/search?query=${encodeURIComponent(query)}`),
  },
  
  // Programs
  programs: {
    list: (params?: Record<string, string>) =>
      apiFetch<any>(`/api/v2/programs?${new URLSearchParams(params || {})}`),
  },
  
  // Jobs
  jobs: {
    list: (params?: Record<string, string>) =>
      apiFetch<any>(`/api/v2/jobs?${new URLSearchParams(params || {})}`),
  },
  
  // Pipeline
  pipeline: {
    get: () => apiFetch<any>('/api/v2/pipeline'),
  },
  
  // Analytics
  analytics: {
    overview: () => apiFetch<any>('/api/v2/analytics/overview'),
  },
  
  // Tools
  tools: {
    triggerScrape: (scraper: string) =>
      apiFetch<any>('/api/v2/tools/trigger-scrape', { method: 'POST', body: JSON.stringify({ scraper_name: scraper }) }),
    triggerEnrichment: (programId: string) =>
      apiFetch<any>('/api/v2/tools/trigger-enrichment', { method: 'POST', body: JSON.stringify({ program_id: programId }) }),
  },
  
  // Collections
  collections: {
    stats: () => apiFetch<any>('/api/v2/collections/stats'),
  },
  
  // Sync
  sync: {
    status: () => apiFetch<any>('/api/v2/sync/status'),
    trigger: (source: string) =>
      apiFetch<any>('/api/v2/sync/notion-to-qdrant', { method: 'POST', body: JSON.stringify({ source_db: source }) }),
  },
};
```

4. Update the main App entry point to use the new router and query client:

```tsx
// src/App.tsx or src/main.tsx
import { RouterProvider } from '@tanstack/react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { router } from './router';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 2,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

Create skeleton page components for each route (just a basic div with the page name for now — we'll build them out in the next steps).

Install packages, create all files, and verify the dashboard builds and loads with the new routing.
```

✅ **VERIFY:** Dashboard loads at localhost with URL-based routing working (e.g., /contacts, /programs)

---

### Steps 3.2-3.7: Dashboard Feature Build

Due to the massive scope, these steps follow the same pattern — each is a standalone Auto-Claude prompt that builds one dashboard feature. The prompts are in the companion file. Key steps:

- **3.2**: Build Dashboard Home page with KPI cards querying `/api/v2/analytics/overview`
- **3.3**: Build Contacts page with search, filter, and table using TanStack Query
- **3.4**: Build Programs page with program cards and detail views
- **3.5**: Build Tool Control Panel with scraper triggers and workflow monitoring
- **3.6**: Add WebSocket connection for real-time updates
- **3.7**: Full integration testing

---

## ═══════════════════════════════════════════
## PHASE 4: AI ENHANCEMENT (Weeks 9-12) 
## ═══════════════════════════════════════════
## 🔀 PARALLEL — Run simultaneously with Terminals B and C

---

### Step 4.1: Expand CrewAI to 8 Agents

⚡ **PROMPT — Paste into Auto-Claude:**

```
Expand the existing CrewAI multi-agent system from 4 agents to 8. Find the current CrewAI configuration and add 4 new specialized agents.

Current agents (keep these):
1. ProgramIntelAgent
2. CompanyResearchAgent  
3. ContactFinderAgent
4. BDStrategyAgent

New agents to add:

5. ContactClassifierAgent:
   - Role: Automatically classify contacts by tier, program, priority, and location
   - Tools: Qdrant search (contacts_unified), classification logic from models/contacts.py
   - Trigger: New contacts imported, bulk classification needed
   - Goal: Every contact gets correct HierarchyTier, DCGSProgram, BDPriority, LocationHub

6. ScraperMonitorAgent:
   - Role: Monitor and analyze job scrape results
   - Tools: Qdrant search (jobs_unified), Apify status API, program mapping engine
   - Trigger: Scrape complete, new jobs detected, competitor activity
   - Goal: Identify high-value job signals and map to BD opportunities

7. QualityAssuranceAgent:
   - Role: Validate data quality across all collections
   - Tools: Qdrant stats, deduplication, Pydantic validation, RAGAS evaluation
   - Trigger: Post-import validation, weekly data audit
   - Goal: Flag duplicates, missing fields, stale data, low-confidence records

8. AnalyticsAgent:
   - Role: Generate insights, trends, and forecasts from all data
   - Tools: All Qdrant collections, analytics engines, report generators
   - Trigger: Weekly reports, ad-hoc analysis requests
   - Goal: Surface actionable BD intelligence that humans would miss

For each agent, create:
- Agent definition with role, goal, backstory, tools
- At least 2 tasks the agent can execute
- Integration with the existing CrewAI crew

Use the existing CrewAI patterns in the project. Show me the complete agent definitions and how they integrate with existing agents.
```

### Step 4.2: Implement Hybrid Search

⚡ **PROMPT — Paste into Auto-Claude:**

```
Enhance the unified search with hybrid search combining dense vector, sparse keyword (BM25), and knowledge graph traversal.

Create `services/hybrid_search.py`:

The hybrid search should:
1. Run dense vector search on Qdrant (weight: 0.5)
2. Run BM25 keyword search using Qdrant's full-text index (weight: 0.3)  
3. Run knowledge graph entity traversal via LightRAG (weight: 0.2)
4. Combine results using Reciprocal Rank Fusion (RRF)
5. Return top-K reranked results

Implementation:
1. Dense search: Use existing Qdrant search with query embedding
2. Sparse search: Use Qdrant scroll with text_match filter on the "content" field
3. Graph search: Query LightRAG for entities matching the query, then find related vectors
4. RRF formula: score = sum(1 / (k + rank_i)) across all search types, k=60

Update the /api/v2/search endpoint to use hybrid search by default.
Add a query parameter `search_mode` with values: "dense", "sparse", "hybrid", "graph" so users can select.

Create the implementation and test with 5 sample queries showing improved results vs dense-only search.
```

### Step 4.3: Add Cross-Encoder Reranking

⚡ **PROMPT — Paste into Auto-Claude:**

```
Add cross-encoder reranking to all RAG-augmented queries for dramatically improved precision.

1. Install the cross-encoder:
```bash
pip install sentence-transformers
```

2. Create `services/reranker.py`:

```python
from sentence_transformers import CrossEncoder
import structlog

logger = structlog.get_logger()

# Load once, reuse across calls
_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)
        logger.info("reranker_loaded", model="ms-marco-MiniLM-L-6-v2")
    return _reranker

def rerank(query: str, documents: list, top_k: int = 10) -> list:
    """
    Rerank documents using cross-encoder.
    
    Args:
        query: Search query
        documents: List of dicts with 'content' and any other fields
        top_k: Number of results to return
    
    Returns:
        Top-K documents sorted by relevance
    """
    reranker = get_reranker()
    
    pairs = [(query, doc.get("content", str(doc))) for doc in documents]
    scores = reranker.predict(pairs)
    
    scored_docs = list(zip(documents, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    return [
        {**doc, "rerank_score": float(score)} 
        for doc, score in scored_docs[:top_k]
    ]
```

3. Integrate into the hybrid search pipeline: after getting top-50 candidates from hybrid search, pass them through the reranker to get top-10.

4. Integrate into all RAG-augmented LLM calls: before sending context to Claude, rerank the retrieved documents.

5. Add reranking to the /api/v2/search endpoint with a `rerank=true` parameter.

Test with the same 5 queries from Step 4.2 and show the improvement in result ordering.
```

---

## ═══════════════════════════════════════════
## PHASE 5: INTEGRATION & TESTING (Weeks 13-16)
## ═══════════════════════════════════════════

### Step 5.1: End-to-End Pipeline Test

⚡ **PROMPT — Paste into Auto-Claude:**

```
Create a comprehensive end-to-end test that validates the entire unified platform works:

1. Trigger a job scrape via the dashboard API
2. Verify scraped jobs arrive in Qdrant jobs_unified collection
3. Run program mapping on the new jobs
4. Verify mapped programs update in programs_unified
5. Run contact classification on contacts related to mapped programs
6. Generate a BD playbook for the top-scored program
7. Verify the playbook appears in documents_kb collection
8. Check that the dashboard analytics endpoint reflects the new data

Create scripts/test_e2e_pipeline.py that runs all these steps and reports pass/fail for each.
Also create a dashboard page at /test that shows the pipeline status in real-time.
```

---

## COMPLETION CHECKLIST

At the end of all phases, verify in Terminal A:

- [ ] All API keys rotated and secured
- [ ] .gitignore covers all sensitive files
- [ ] 22 LLM call sites have retry logic
- [ ] Prompt caching enabled on all Anthropic calls
- [ ] Structured logging across all modules
- [ ] Pydantic models for all data boundaries
- [ ] API authentication on all Hub endpoints
- [ ] 12 unified Qdrant collections created and populated
- [ ] All old collections migrated to unified collections
- [ ] Notion ↔ Qdrant bidirectional sync operational
- [ ] Knowledge graph built with LightRAG
- [ ] Dashboard rebuilt with TanStack Router + Query
- [ ] 14 dashboard routes functional with live API data
- [ ] Tool Control Panel operational
- [ ] WebSocket real-time updates working
- [ ] 8 CrewAI agents configured
- [ ] Hybrid search (dense + sparse + graph) operational
- [ ] Cross-encoder reranking on all searches
- [ ] End-to-end pipeline test passing
