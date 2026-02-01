# Knowledge System Roadmap

## Current State (v1.0) ✅

| Component | Status | Records |
|-----------|--------|---------|
| Qdrant Vector DB | Deployed | 8,447 total |
| Embedding Model | all-MiniLM-L6-v2 | 384 dims |
| Collections | 5 active | jobs, contacts, programs, documents, activities |
| Search API | Working | Python + REST |
| RAG Engine | Basic mode | Claude integration |
| Auto-Tagger | Rules-based | BD taxonomy |
| MCP Server | Configured | Not built |

---

## Immediate Next Steps (v1.1)

### 1. Build & Test MCP Server
**Priority: HIGH** | **Effort: 2-3 hours**

```bash
cd mcp/knowledge-mcp-server
npm install
npm run build
```

Then add to `.mcp.json` and test in Claude Code.

**Verification:**
- [ ] MCP server starts without errors
- [ ] `search_knowledge` tool works in Claude Code
- [ ] `ask_knowledge` returns answers with sources

### 2. Install Optional Dependencies
**Priority: MEDIUM** | **Effort: 30 min**

```bash
# Document processing (for PDFs, Excel)
pip install docling python-magic-bin

# Full RAG framework
pip install llama-index llama-index-vector-stores-qdrant llama-index-llms-anthropic
```

### 3. Index More Data Sources
**Priority: MEDIUM** | **Effort: 1-2 hours**

Currently not indexed:
- [ ] `Engine3_OrgChart/data/Prime_Contacts/*.csv` (27 contractor databases)
- [ ] `docs/Bullhorn Exports/*.xls` (500+ activity exports)
- [ ] `outputs/*.md` (generated briefings and playbooks)
- [ ] `Engine2_ProgramMapping/data/*.html` (Notion exports)

### 4. Start API Server on Boot
**Priority: LOW** | **Effort: 30 min**

Create startup script or Windows service for:
```bash
python Engine8_Knowledge/api.py
```

---

## Short-Term Enhancements (v1.2)

### Hybrid Search
Combine semantic + keyword search for better precision.

```python
def hybrid_search(query, collection, keyword_weight=0.3):
    # Semantic search
    semantic_results = self.search(query, collection)

    # Keyword search (exact matches)
    keyword_results = self.keyword_search(query, collection)

    # Merge with weights
    return merge_results(semantic_results, keyword_results, keyword_weight)
```

### Query Caching
Cache frequent queries to reduce embedding computation.

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_search(query, collection, limit):
    return self.search(query, collection, limit)
```

### Incremental Indexing
Only index new/modified records.

```python
def incremental_index(collection, since_date):
    # Check _indexed_at timestamp
    # Only process newer records
    pass
```

### File Watcher Integration
Auto-index new files when added to watched directories.

```bash
# Start file watcher
python Engine8_Knowledge/scripts/file_watcher.py --watch dashboard/public/data --watch outputs
```

---

## Medium-Term Features (v2.0)

### 1. Knowledge Graph Layer
Add relationship mapping between entities.

```
Contact → works_at → Company
Contact → manages → Program
Program → prime_contractor → Company
Job → requires → Clearance
```

### 2. Conversation Memory
Track conversation history for follow-up questions.

```python
rag.ask("What contacts do we have at Leidos?")
rag.ask("Which of them work on DCGS?")  # Remembers context
```

### 3. Multi-Modal Support
Index and search images, diagrams, org charts.

### 4. Real-Time Sync
Automatic sync with:
- Notion databases
- Bullhorn CRM
- Job board APIs

### 5. Analytics Dashboard
- Search query analytics
- Index health monitoring
- Usage patterns

---

## Cross-Project Integration (v3.0)

### Shared Knowledge Protocol

For sharing across Auto-Claude projects:

```python
# Export knowledge snapshot
def export_knowledge(output_path):
    """Export indexed knowledge for other projects."""
    return {
        'collections': get_all_collection_data(),
        'taxonomy': get_taxonomy(),
        'statistics': get_stats(),
        'schema': get_schema()
    }

# Import external knowledge
def import_knowledge(source_path):
    """Import knowledge from another project."""
    pass
```

### Knowledge Federation
Query across multiple project knowledge bases:

```
Project A (BD-Engine) ←→ Project B (Other) ←→ Project C (Other)
         ↓                     ↓                     ↓
    [bd-knowledge]       [other-knowledge]     [other-knowledge]
         ↓                     ↓                     ↓
         └──────────────→ [Federation Layer] ←──────────────┘
                               ↓
                         [Unified Search]
```

### Pattern Library
Shareable patterns extracted from this project:

| Pattern | File | Description |
|---------|------|-------------|
| Vector Store Wrapper | `vector_store.py` | Qdrant abstraction with UUID handling |
| Data Pipeline | `indexer.py` | Multi-source indexing with progress |
| RAG Engine | `rag_engine.py` | Claude-based Q&A with sources |
| Auto-Classification | `auto_tagger.py` | Rule + LLM hybrid tagging |
| FastAPI Bridge | `api.py` | REST API for MCP integration |

---

## Technical Debt

### Known Issues
1. **QdrantClient shutdown warning** - Harmless but noisy
2. **Missing docling/python-magic** - Optional but shows warnings
3. **No retry logic** - API calls can fail without retry

### Improvements Needed
1. Add comprehensive error handling
2. Add unit tests for core functions
3. Add logging to file (not just stdout)
4. Add configuration file (currently hardcoded)

---

## Resource Requirements

### Current
- **Storage**: ~50 MB for Qdrant data
- **Memory**: ~500 MB (embedding model)
- **CPU**: Moderate (embedding computation)

### Projected (v2.0)
- **Storage**: ~500 MB (more documents)
- **Memory**: ~1 GB (larger models optional)
- **GPU**: Optional (faster embeddings)

---

## Success Metrics

### v1.1 Goals
- [ ] MCP server working in Claude Code
- [ ] Search latency < 500ms
- [ ] RAG answer quality verified

### v2.0 Goals
- [ ] 50,000+ indexed records
- [ ] Knowledge graph relationships
- [ ] Real-time sync active

### v3.0 Goals
- [ ] Cross-project queries working
- [ ] Pattern library published
- [ ] Federation layer deployed

---

## Action Items

### This Week
1. Build MCP server (`npm install && npm run build`)
2. Test in Claude Code session
3. Index remaining data sources

### This Month
1. Implement hybrid search
2. Add query caching
3. Set up file watcher

### This Quarter
1. Knowledge graph layer
2. Real-time sync with Notion
3. Cross-project integration design
