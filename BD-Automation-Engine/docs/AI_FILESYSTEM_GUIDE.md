# AI Filesystem & Development Guide

## Overview

This guide explains how to use the AI-powered filesystem, knowledge base, and development tools in the BD-Automation-Engine project. It's designed for both human developers and AI agents working on this codebase.

---

## Quick Start

### 1. Start the Knowledge API
```bash
cd BD-Automation-Engine
python Engine8_Knowledge/api.py
```
API runs on http://localhost:8100

### 2. Search the Knowledge Base
```bash
# CLI search
python Engine8_Knowledge/scripts/vector_store.py --search "DCGS analyst" --collection contacts

# Python
from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
store = BDKnowledgeStore()
results = store.search("your query", "contacts", limit=10)
```

### 3. Ask Questions (RAG)
```bash
# Via API
curl -X POST http://localhost:8100/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What contacts do we have at Leidos?"}'
```

---

## Project Structure

```
BD-Automation-Engine/
├── Engine1_Scraper/           # Apify job scraper
├── Engine2_ProgramMapping/    # Job-to-program matching
│   └── data/
│       └── Federal_Programs_Master.csv
├── Engine3_OrgChart/          # Contact classification
│   └── data/
│       └── Prime_Contacts/    # 27 contractor CSVs
├── Engine4_Playbook/          # BD playbook generation
├── Engine5_Scoring/           # BD priority scoring
├── Engine6_QA/                # Quality assurance
├── Engine7_BullhornETL/       # CRM data extraction
│   └── data/
│       └── bullhorn.db        # 293 MB SQLite
├── Engine8_Knowledge/         # AI KNOWLEDGE SYSTEM
│   ├── scripts/
│   │   ├── vector_store.py    # Qdrant wrapper (8,447 records)
│   │   ├── indexer.py         # Data ingestion pipeline
│   │   ├── rag_engine.py      # RAG with Claude
│   │   ├── auto_tagger.py     # Document classification
│   │   ├── document_processor.py  # PDF/DOCX processing
│   │   └── file_watcher.py    # Auto-index new files
│   ├── api.py                 # FastAPI server (:8100)
│   └── data/qdrant/           # Vector database
├── dashboard/
│   └── public/data/           # Aggregated JSON views
├── mcp/
│   └── knowledge-mcp-server/  # Claude Code integration
├── docs/                      # Documentation
│   ├── AI_FILESYSTEM_GUIDE.md     # THIS FILE
│   ├── KNOWLEDGE_SYSTEM_GUIDE.md  # Architecture details
│   ├── RAG_USAGE_GUIDE.md         # RAG patterns
│   ├── KNOWLEDGE_SYSTEM_ROADMAP.md # Future plans
│   └── CROSS_PROJECT_SHARING.md   # Multi-project access
├── outputs/                   # Generated content
├── .mcp.json                  # MCP server config
├── CLAUDE.md                  # AI instructions
└── requirements.txt           # Python dependencies
```

---

## Knowledge Base Collections

| Collection | Records | Description |
|------------|---------|-------------|
| **jobs** | 4 | Job postings with BD scores |
| **contacts** | 7,337 | CRM contacts with tier classification |
| **programs** | 401 | Federal programs and contracts |
| **documents** | 205 | Past performance, briefings |
| **activities** | 500 | Call notes, meeting records |
| **TOTAL** | **8,447** | Searchable records |

---

## Common Operations

### Search by Collection
```python
from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
store = BDKnowledgeStore()

# Search contacts
store.search("program manager TS/SCI", "contacts", limit=10)

# Search programs
store.search("Leidos prime contractor", "programs", limit=5)

# Search all collections
store.search_all("DCGS cybersecurity", limit_per_collection=5)
```

### Find Related Items
```python
# Contacts for a program
store.find_contacts_for_program("DCGS")

# Jobs for a program
store.find_jobs_for_program("GBSD")

# Contacts at a company
store.find_contacts_at_company("Leidos")

# Full intelligence report
store.get_program_intelligence("DCGS")
```

### Add New Data
```python
from Engine8_Knowledge.scripts.indexer import BDIndexer

indexer = BDIndexer()

# Index all data
indexer.index_all()

# Index specific collection
indexer.index_contacts()
indexer.index_programs()
```

---

## MCP Tools (Claude Code)

When the API is running, Claude Code has these tools:

| Tool | Description |
|------|-------------|
| `search_knowledge` | Semantic search |
| `ask_knowledge` | RAG Q&A with sources |
| `find_similar` | Find similar items |
| `get_program_intel` | Program intelligence report |
| `get_company_contacts` | Company contact lookup |
| `get_knowledge_stats` | Index statistics |
| `reindex_knowledge` | Trigger reindexing |

### Example Prompts for Claude
- "Search the knowledge base for DCGS contacts"
- "What do we know about the GBSD program?"
- "Find contacts similar to senior program managers"
- "Get intelligence on Leidos"

---

## File Locations Reference

### Data Sources
| Type | Location | Format |
|------|----------|--------|
| Jobs | `dashboard/public/data/jobs_enriched.json` | JSON |
| Contacts | `dashboard/public/data/contacts_classified.json` | JSON |
| Programs | `dashboard/public/data/programs_enriched.json` | JSON |
| Activities | `dashboard/public/data/call_notes_summary.json` | JSON |
| Past Performance | `dashboard/public/data/past_performance.json` | JSON |
| Prime Contacts | `Engine3_OrgChart/data/Prime_Contacts/*.csv` | CSV |
| Bullhorn DB | `Engine7_BullhornETL/data/bullhorn.db` | SQLite |

### Configuration Files
| File | Purpose |
|------|---------|
| `.env` | API keys (NEVER commit) |
| `.mcp.json` | MCP server definitions |
| `CLAUDE.md` | AI agent instructions |
| `requirements.txt` | Python dependencies |

### Output Locations
| Type | Location |
|------|----------|
| Generated Playbooks | `outputs/playbooks/` |
| Briefings | `outputs/briefings/` |
| Reports | `outputs/reports/` |

---

## API Endpoints

Base URL: `http://localhost:8100`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/search` | Semantic search |
| POST | `/ask` | RAG question answering |
| POST | `/similar` | Find similar items |
| GET | `/program/{name}` | Program intelligence |
| GET | `/company/{name}` | Company contacts |
| GET | `/stats` | Collection statistics |
| POST | `/index/all` | Reindex all data |
| GET | `/health` | Health check |

### Request Examples
```bash
# Search
curl -X POST http://localhost:8100/search \
  -H "Content-Type: application/json" \
  -d '{"query": "DCGS analyst", "collection": "contacts", "limit": 10}'

# Ask
curl -X POST http://localhost:8100/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who are the key contacts at Leidos for DCGS?"}'

# Stats
curl http://localhost:8100/stats
```

---

## Best Practices

### For Searching
1. **Be specific** - "TS/SCI cleared DCGS program managers" > "managers"
2. **Use domain terms** - "Tier 1 contacts" > "important people"
3. **Filter by collection** - Search `contacts` for people, `programs` for contracts

### For RAG Questions
1. **Ask focused questions** - One topic per question
2. **Include context** - "For the DCGS program, who are..."
3. **Request sources** - Answers include citations

### For Indexing
1. **Run after data updates** - `python Engine8_Knowledge/scripts/indexer.py --all`
2. **Check stats** - Verify record counts after indexing
3. **Monitor errors** - Check for failed records

---

## Troubleshooting

### API Not Starting
```bash
# Check if port is in use
netstat -an | findstr 8100

# Kill existing process and restart
python Engine8_Knowledge/api.py
```

### Empty Search Results
```bash
# Check index status
python Engine8_Knowledge/scripts/vector_store.py --stats

# Reindex if needed
python Engine8_Knowledge/scripts/indexer.py --all
```

### MCP Tools Not Working
1. Verify API is running: `curl http://localhost:8100/health`
2. Check `.mcp.json` configuration
3. Restart Claude Code session

---

## Integration Patterns

### With Other Auto-Claude Projects
```python
# Reference this knowledge base from another project
import requests

KNOWLEDGE_API = "http://localhost:8100"

def search_bd_knowledge(query, collection="all"):
    return requests.post(f"{KNOWLEDGE_API}/search", json={
        "query": query,
        "collection": collection
    }).json()
```

### With n8n Workflows
```javascript
// In n8n HTTP Request node
{
  "method": "POST",
  "url": "http://localhost:8100/search",
  "body": {
    "query": "{{$json.searchQuery}}",
    "collection": "contacts"
  }
}
```

### With Notion
- Sync contacts via Notion MCP
- Export program data to Notion databases
- Reference knowledge in Notion pages

---

## Maintenance

### Daily
- API should auto-start or be started manually

### Weekly
- Run full reindex if data changes frequently
- Check collection stats for anomalies

### Monthly
- Review and archive old outputs
- Update dependencies: `pip install -r requirements.txt --upgrade`

---

## Getting Help

- **This Guide**: `docs/AI_FILESYSTEM_GUIDE.md`
- **Architecture**: `docs/KNOWLEDGE_SYSTEM_GUIDE.md`
- **RAG Patterns**: `docs/RAG_USAGE_GUIDE.md`
- **Future Plans**: `docs/KNOWLEDGE_SYSTEM_ROADMAP.md`
- **Cross-Project**: `docs/CROSS_PROJECT_SHARING.md`
