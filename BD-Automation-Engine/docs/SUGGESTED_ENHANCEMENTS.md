# Suggested Enhancements for BD-Automation-Engine

## Overview

This document outlines recommended enhancements to improve development workflow, AI capabilities, and overall project robustness.

---

## High Priority Enhancements

### 1. Auto-Start API Server Script
**Why**: Currently must manually start the API for MCP tools to work.

```bash
# Create: scripts/start_services.bat (Windows)
@echo off
echo Starting BD Knowledge API...
start /B python Engine8_Knowledge/api.py
echo API starting on http://localhost:8100
timeout /t 3
curl http://localhost:8100/health
```

```bash
# Create: scripts/start_services.sh (Linux/Mac)
#!/bin/bash
echo "Starting BD Knowledge API..."
nohup python Engine8_Knowledge/api.py > logs/api.log 2>&1 &
echo "API started on http://localhost:8100"
```

### 2. Enhanced CLAUDE.md with Knowledge Instructions
**Why**: Tell Claude how to use the knowledge base automatically.

Add to `CLAUDE.md`:
```markdown
## Knowledge Base Access

This project has a semantic knowledge base with 8,447+ indexed records.

### To Search (when API is running on :8100)
- Use MCP tool `search_knowledge` for semantic search
- Use MCP tool `ask_knowledge` for RAG-powered Q&A

### Collections Available
- `contacts` - 7,337 CRM contacts with tier classification
- `programs` - 401 federal programs
- `jobs` - Job postings with BD scores
- `documents` - Past performance records
- `activities` - Call notes and meetings

### Example Queries
- "Find Tier 1 contacts at Leidos working on DCGS"
- "What programs does Northrop Grumman prime?"
- "Who are the key decision makers for GBSD?"
```

### 3. Caching Layer for Frequent Queries
**Why**: Reduce embedding computation for repeated queries.

```python
# Add to vector_store.py
from functools import lru_cache
import hashlib

class BDKnowledgeStore:
    @lru_cache(maxsize=500)
    def _cached_embedding(self, text_hash: str, text: str):
        return self._generate_embedding(text)

    def search_cached(self, query: str, collection: str, limit: int = 10):
        query_hash = hashlib.md5(query.encode()).hexdigest()
        embedding = self._cached_embedding(query_hash, query)
        # ... rest of search logic
```

### 4. Logging Infrastructure
**Why**: Track API usage, errors, and performance.

```python
# Create: Engine8_Knowledge/logging_config.py
import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_DIR / "knowledge_api.log"),
            logging.StreamHandler()
        ]
    )
```

---

## Medium Priority Enhancements

### 5. Health Monitoring Dashboard
**Why**: Quick visibility into system status.

```python
# Add to api.py
@app.get("/dashboard")
async def dashboard():
    return {
        "status": "healthy",
        "collections": store.get_collection_stats(),
        "uptime": get_uptime(),
        "queries_today": get_query_count(),
        "last_index": get_last_index_time()
    }
```

### 6. Incremental Indexing
**Why**: Faster updates when data changes.

```python
# Add to indexer.py
def incremental_index(self, collection: str, since: datetime):
    """Only index records newer than `since`."""
    data = self.load_data(collection)
    new_records = [r for r in data if r.get('updated_at', '') > since.isoformat()]
    return self.store.index_data(collection, new_records)
```

### 7. Query Analytics
**Why**: Understand usage patterns, improve search quality.

```python
# Create: Engine8_Knowledge/analytics.py
import json
from datetime import datetime
from pathlib import Path

ANALYTICS_FILE = Path("data/query_analytics.jsonl")

def log_query(query: str, collection: str, results_count: int, latency_ms: float):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "collection": collection,
        "results": results_count,
        "latency_ms": latency_ms
    }
    with open(ANALYTICS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
```

### 8. Backup Script
**Why**: Protect indexed data.

```bash
# Create: scripts/backup_knowledge.sh
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR
cp -r Engine8_Knowledge/data/qdrant $BACKUP_DIR/
echo "Backup created: $BACKUP_DIR"
```

---

## AI Capability Enhancements

### 9. Conversation Memory
**Why**: Enable follow-up questions with context.

```python
# Add conversation tracking to RAG engine
class ConversationalRAG:
    def __init__(self):
        self.history = []

    def ask(self, question: str):
        # Include history in context
        context = self._build_context(question, self.history)
        answer = self._generate_answer(question, context)
        self.history.append({"q": question, "a": answer})
        return answer
```

### 10. Multi-Modal Document Processing
**Why**: Index images, diagrams, org charts.

```python
# Enhance document_processor.py
def process_image(self, image_path: str) -> Dict:
    """Extract text and descriptions from images."""
    # Use Claude vision or OCR
    pass

def process_org_chart(self, image_path: str) -> List[Dict]:
    """Extract hierarchy from org chart images."""
    pass
```

### 11. Knowledge Graph Layer
**Why**: Track relationships between entities.

```python
# Create: Engine8_Knowledge/scripts/knowledge_graph.py
class BDKnowledgeGraph:
    """Relationship tracking for BD entities."""

    def add_relationship(self, entity1: str, relationship: str, entity2: str):
        # Contact → works_at → Company
        # Program → prime_contractor → Company
        pass

    def get_relationships(self, entity: str) -> List[Dict]:
        pass
```

### 12. Automated Insight Generation
**Why**: Proactively surface important patterns.

```python
# Create: Engine8_Knowledge/scripts/insights.py
def generate_weekly_insights():
    """Generate automated BD insights."""
    return {
        "new_contacts": find_new_contacts_this_week(),
        "hot_programs": find_programs_with_activity(),
        "coverage_gaps": find_programs_without_contacts(),
        "opportunities": find_emerging_opportunities()
    }
```

---

## Development Workflow Enhancements

### 13. Pre-Commit Hooks
**Why**: Catch issues before commit.

```yaml
# Create: .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.12
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
  - repo: local
    hooks:
      - id: check-env
        name: Check .env not committed
        entry: bash -c 'git diff --cached --name-only | grep -q "^\.env$" && exit 1 || exit 0'
        language: system
```

### 14. Testing Framework
**Why**: Ensure reliability.

```python
# Create: tests/test_knowledge_store.py
import pytest
from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore

@pytest.fixture
def store():
    return BDKnowledgeStore(in_memory=True)

def test_search_returns_results(store):
    store.initialize_collections()
    # Add test data
    results = store.search("test query", "contacts")
    assert isinstance(results, list)

def test_uuid_generation(store):
    data = {"name": "Test", "company": "Test Co"}
    point_id = store._generate_point_id(data, "contacts")
    import uuid
    uuid.UUID(point_id)  # Should not raise
```

### 15. CI/CD Pipeline
**Why**: Automated testing and deployment.

```yaml
# Create: .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pip install pytest
      - run: pytest tests/ -v
```

### 16. Development Container
**Why**: Consistent dev environment.

```json
// Create: .devcontainer/devcontainer.json
{
  "name": "BD-Automation-Engine",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",
  "postCreateCommand": "pip install -r requirements.txt",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.black-formatter"
      ]
    }
  },
  "forwardPorts": [8100]
}
```

---

## Additional MCP Servers to Consider

### 17. GitHub MCP
**Why**: Issue/PR management from Claude.

```json
// Add to .mcp.json
"github": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_TOKEN": "${GITHUB_TOKEN}"
  }
}
```

### 18. Memory MCP (Persistent AI Memory)
**Why**: Claude remembers context across sessions.

```json
"memory": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-memory"]
}
```

### 19. Filesystem MCP
**Why**: Enhanced file operations.

```json
"filesystem": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/project"]
}
```

---

## Quick Wins (Can Implement Now)

| Enhancement | Effort | Impact |
|-------------|--------|--------|
| Auto-start script | 10 min | High |
| Update CLAUDE.md | 15 min | High |
| Add logging | 30 min | Medium |
| Backup script | 10 min | Medium |
| Health endpoint | 20 min | Medium |

---

## Implementation Priority

### This Week
1. Auto-start script for API
2. Update CLAUDE.md with knowledge instructions
3. Add basic logging

### This Month
4. Query caching
5. Incremental indexing
6. Testing framework

### This Quarter
7. Knowledge graph layer
8. Conversation memory
9. Automated insights
10. CI/CD pipeline

---

## Next Steps

To implement any enhancement:
1. Review the code snippet
2. Create the file or add to existing file
3. Test the functionality
4. Update documentation

Would you like me to implement any of these enhancements now?
