# PTS Intelligence Hub
## (Formerly: BD-Automation-Engine)

**Central API Gateway + Vector Search + RAG Engine for PTS Business Development**

---

## What This Project Actually Does

This is the **central intelligence hub** for PTS's BD operations. It provides:

- 🔌 **FastAPI Server** (50+ endpoints on localhost:8100)
- 🔍 **Vector Search** (Qdrant with 8,447 embeddings)
- 🤖 **RAG Queries** (LightRAG + BM25 hybrid search)
- 🧠 **Memory Layer** (Mem0 for context retention)
- ⚙️ **AI Pipeline** (Claude-powered job enrichment)
- 📊 **Output Generation** (BD Playbooks, Call Scripts)
- 🔗 **Integration Hub** (Notion, n8n, MCP)

---

## Current Status

| Component | Status | Details |
|-----------|--------|---------|
| FastAPI Server | ✅ Running | localhost:8100 |
| Qdrant Vectors | ✅ Active | 8,447 indexed |
| AI Enrichment | ✅ Active | Claude + Pydantic |
| Playbook Gen | ✅ Active | 40+ generated |
| Notion Sync | ✅ Active | 8 databases |
| n8n Webhooks | ✅ Active | 13+ payloads |
| Mem0 Memory | ⚠️ Partial | Occasional errors |
| LightRAG | ⚠️ Partial | Not exposed via API |
| spaCy NER | ❌ Unused | Installed but not integrated |

---

## Quick Start

### 1. Start the Hub
```bash
cd Engine8_Knowledge
python api.py
# Server runs on http://localhost:8100
```

### 2. Test Health
```bash
curl http://localhost:8100/health
# {"status": "healthy"}
```

### 3. Search Jobs
```bash
curl "http://localhost:8100/search?q=DCGS+network+engineer&collection=jobs"
```

### 4. RAG Query
```bash
curl "http://localhost:8100/ask/smart?q=Who+are+the+key+contacts+at+Langley"
```

---

## Key API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/search` | GET | Semantic vector search |
| `/ask/smart` | GET | RAG query with hybrid retrieval |
| `/ingest/jobs` | POST | Ingest job data from scrapers |
| `/memory/add` | POST | Add to memory layer |
| `/memory/search` | GET | Search memories |
| `/contacts` | GET | Query contact database |
| `/programs` | GET | Query federal programs |

---

## Vector Collections (Qdrant)

| Collection | Vectors | Contents |
|------------|---------|----------|
| jobs | 262 | Scraped job postings |
| contacts | 7,337 | DCGS + GDIT contacts |
| programs | 401 | Federal programs |
| documents | 205 | Processed documents |
| activities | 500 | BD activities log |

---

## Output Files

| Directory | Contents | Count |
|-----------|----------|-------|
| `outputs/BD_Briefings/` | Playbooks, call scripts, emails | 40+ |
| `outputs/notion/` | Notion export CSVs | 13 |
| `outputs/n8n/` | Webhook payloads | 13 |
| `outputs/` (root) | Processed jobs, reports | 95+ |

---

## Integration with Other Terminals

### From Data-Scraper
```python
# Data-Scraper sends jobs to Hub
POST http://localhost:8100/ingest/jobs
{
  "jobs": [...]
}
```

### From N8N-Builder
```
Webhook: Hub - Ingest Jobs
Webhook: Hub - Smart Query
Webhook: Hub - Search
```

---

## Configuration

### Environment Variables
```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
NOTION_API_KEY=secret_...
```

### MCP Server
Configured in `.mcp.json` for Claude Code integration.

---

## What's NOT Used (Deprecate or Integrate)

| Package | Status | Action |
|---------|--------|--------|
| ChromaDB | Installed | Remove (using Qdrant) |
| Firecrawl | Configured | Remove (using Apify) |
| Crawl4AI | Configured | Remove (using Apify) |
| spaCy | Installed | Integrate or remove |
| Redis | Ready | Optional, not required |

---

## Maintenance

### Reindex Vectors
```python
# From Python REPL
from scripts.vector_store import reindex_all
reindex_all()
```

### Clear Memory
```bash
curl -X DELETE http://localhost:8100/memory/clear
```

### Check Stats
```bash
curl http://localhost:8100/stats
```

---

## Directory Structure

```
BD-Automation-Engine/
├── Engine8_Knowledge/
│   ├── api.py              # FastAPI server
│   ├── scripts/
│   │   ├── vector_store.py
│   │   ├── rag_engine.py
│   │   ├── memory_layer.py
│   │   └── ...
│   ├── data/
│   │   ├── qdrant/         # Vector storage
│   │   └── ...
│   └── schemas/
│       └── unified_models.py
├── outputs/
│   ├── BD_Briefings/
│   ├── notion/
│   └── n8n/
└── docs/
```

---

*Last updated: January 26, 2026*
