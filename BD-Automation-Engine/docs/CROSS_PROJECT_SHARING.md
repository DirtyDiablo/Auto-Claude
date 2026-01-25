# Cross-Project Knowledge Sharing Guide

## Purpose

This guide explains how to share knowledge and patterns from the BD-Automation-Engine project with other Auto-Claude projects, enabling them to learn from each other and build better solutions together.

---

## What Can Be Shared

### 1. Indexed Knowledge Data
The 8,447 indexed records across 5 collections can be queried or exported.

### 2. Code Patterns
Reusable implementation patterns for:
- Vector database integration
- RAG implementation
- Data pipelines
- API design

### 3. Taxonomy & Classification
Domain-specific categorization:
- Federal programs
- Defense contractors
- Clearance levels
- BD priorities

### 4. Architectural Decisions
Lessons learned about:
- Qdrant embedded mode vs server
- Embedding model selection
- Chunking strategies
- API design patterns

---

## How to Share Knowledge

### Method 1: Direct File Reference

Other Auto-Claude projects can reference files directly:

```python
# In another project, reference this project's knowledge
import sys
sys.path.insert(0, '/path/to/BD-Automation-Engine')

from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
from Engine8_Knowledge.scripts.rag_engine import BDRAGEngine

# Use the knowledge base
store = BDKnowledgeStore(path='/path/to/BD-Automation-Engine/Engine8_Knowledge/data/qdrant')
results = store.search("your query", "contacts")
```

### Method 2: Export/Import JSON

```python
# Export knowledge snapshot
import json
from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore

store = BDKnowledgeStore()

def export_collection(collection, output_file):
    """Export a collection to JSON for sharing."""
    # Note: This requires custom implementation
    # The pattern shows the approach
    results = store.search("*", collection, limit=10000)
    data = [r.to_dict() for r in results]
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

# Export each collection
for coll in ['jobs', 'contacts', 'programs', 'documents', 'activities']:
    export_collection(coll, f'exports/{coll}.json')
```

### Method 3: REST API Access

If the API server is running, other projects can query via HTTP:

```python
import requests

# From another project
KNOWLEDGE_API = "http://localhost:8100"

def search_bd_knowledge(query, collection="all"):
    response = requests.post(f"{KNOWLEDGE_API}/search", json={
        "query": query,
        "collection": collection,
        "limit": 10
    })
    return response.json()

def ask_bd_knowledge(question):
    response = requests.post(f"{KNOWLEDGE_API}/ask", json={
        "question": question
    })
    return response.json()
```

### Method 4: MCP Server Integration

Other Claude Code projects can add the MCP server to their `.mcp.json`:

```json
{
  "mcpServers": {
    "bd-knowledge": {
      "command": "node",
      "args": ["/path/to/BD-Automation-Engine/mcp/knowledge-mcp-server/build/index.js"],
      "env": {
        "KNOWLEDGE_API_URL": "http://127.0.0.1:8100"
      }
    }
  }
}
```

---

## Shareable Code Patterns

### Pattern 1: Vector Store Wrapper
**File**: `Engine8_Knowledge/scripts/vector_store.py`

Key learnings:
- Use embedded Qdrant for zero-setup deployment
- Generate deterministic UUIDs from content hashes
- Handle API version differences gracefully
- Batch processing with progress logging

```python
# Key pattern: UUID generation for Qdrant
def _generate_point_id(self, data: Dict, collection: str) -> str:
    """Generate deterministic UUID from content."""
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
    content = f"{collection}:{json.dumps(data, sort_keys=True)}"
    return str(uuid.uuid5(namespace, content))
```

### Pattern 2: Multi-Source Indexer
**File**: `Engine8_Knowledge/scripts/indexer.py`

Key learnings:
- Load from multiple JSON sources
- Transform data for embedding
- Track progress with counters
- Handle errors gracefully

```python
# Key pattern: Data loading with fallbacks
def load_data(self, collection):
    """Load data from multiple possible sources."""
    sources = [
        f'dashboard/public/data/{collection}_enriched.json',
        f'dashboard/public/data/{collection}.json',
        f'data/{collection}.json'
    ]
    for source in sources:
        if Path(source).exists():
            return json.load(open(source))
    return []
```

### Pattern 3: RAG with Sources
**File**: `Engine8_Knowledge/scripts/rag_engine.py`

Key learnings:
- Retrieve context before generation
- Include source citations
- Handle missing dependencies gracefully

```python
# Key pattern: RAG with source tracking
def ask_with_sources(self, question: str) -> Dict:
    # 1. Retrieve relevant context
    context_docs = self.store.search_all(question, limit_per_collection=3)

    # 2. Format context for prompt
    context_text = self._format_context(context_docs)

    # 3. Generate answer with Claude
    answer = self._generate_answer(question, context_text)

    # 4. Return with sources
    return {
        'answer': answer,
        'sources': self._extract_sources(context_docs)
    }
```

### Pattern 4: Auto-Classification
**File**: `Engine8_Knowledge/scripts/auto_tagger.py`

Key learnings:
- Combine rule-based and LLM classification
- Define domain-specific taxonomy
- Cache classification results

```python
# Key pattern: Hybrid classification
TAXONOMY = {
    'program': ['DCGS', 'GBSD', 'NGI', ...],
    'contractor': ['Leidos', 'GDIT', 'CACI', ...],
    'clearance': ['TS/SCI', 'Top Secret', 'Secret', ...]
}

def classify(self, text: str) -> Dict[str, List[str]]:
    # Rule-based first (fast)
    tags = self._rule_based_classify(text)

    # LLM for ambiguous cases (accurate)
    if self._needs_llm_classification(tags):
        tags = self._llm_classify(text, tags)

    return tags
```

---

## Knowledge Domains

### BD-Specific Knowledge
This project has deep knowledge about:

| Domain | Examples | Collection |
|--------|----------|------------|
| Federal Programs | DCGS, GBSD, NGI, JADC2 | programs |
| Defense Contractors | Leidos, GDIT, Northrop | contacts, programs |
| Security Clearances | TS/SCI, Secret, Public Trust | jobs, contacts |
| BD Processes | Tier classification, scoring | contacts |
| Government Contacts | Program managers, contracting officers | contacts |

### Reusable for Other Projects
- Vector search patterns
- RAG implementation
- Document processing
- API design
- MCP integration

---

## Setting Up Cross-Project Access

### For the BD-Automation-Engine Side

1. **Start the API server**:
```bash
cd BD-Automation-Engine
python Engine8_Knowledge/api.py
```

2. **Verify it's accessible**:
```bash
curl http://localhost:8100/stats
```

### For Other Auto-Claude Projects

1. **Add to project's CLAUDE.md**:
```markdown
## External Knowledge Sources

This project can access BD intelligence data via:
- REST API: http://localhost:8100
- MCP Server: bd-knowledge

### Query Examples
- Search contacts: POST /search {"query": "...", "collection": "contacts"}
- Ask questions: POST /ask {"question": "..."}
```

2. **Install client helper** (optional):
```python
# Create a simple client in your project
class BDKnowledgeClient:
    def __init__(self, base_url="http://localhost:8100"):
        self.base_url = base_url

    def search(self, query, collection="all", limit=10):
        import requests
        return requests.post(f"{self.base_url}/search",
                           json={"query": query, "collection": collection, "limit": limit}).json()

    def ask(self, question):
        import requests
        return requests.post(f"{self.base_url}/ask",
                           json={"question": question}).json()
```

---

## Future: Knowledge Federation

### Vision
Multiple Auto-Claude projects sharing a unified knowledge layer:

```
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE FEDERATION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  BD-Automation-Engine     Project B           Project C          │
│  ┌─────────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │ bd-knowledge    │    │ project-b   │    │ project-c   │      │
│  │ - jobs          │    │ - codebase  │    │ - docs      │      │
│  │ - contacts      │    │ - patterns  │    │ - apis      │      │
│  │ - programs      │    │ - learnings │    │ - configs   │      │
│  └────────┬────────┘    └──────┬──────┘    └──────┬──────┘      │
│           │                    │                   │              │
│           └────────────────────┼───────────────────┘              │
│                                │                                  │
│                    ┌───────────┴───────────┐                     │
│                    │  Federation Router    │                     │
│                    │  - Route queries      │                     │
│                    │  - Merge results      │                     │
│                    │  - Unify schemas      │                     │
│                    └───────────┬───────────┘                     │
│                                │                                  │
│                    ┌───────────┴───────────┐                     │
│                    │  Unified MCP Server   │                     │
│                    │  search_all_projects  │                     │
│                    │  ask_federation       │                     │
│                    └───────────────────────┘                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Benefits
- Learn from each project's patterns
- Cross-reference information
- Build collective intelligence
- Avoid duplicate work

---

## Contact

For questions about this knowledge system or cross-project integration:
- Review the code in `Engine8_Knowledge/`
- Check docs in `docs/`
- Reference `CLAUDE.md` for project context
