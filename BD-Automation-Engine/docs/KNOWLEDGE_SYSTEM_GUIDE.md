# BD-Automation-Engine Knowledge System Guide

## Overview

This document describes the AI-powered knowledge management system (Engine 8) that provides semantic search, RAG (Retrieval Augmented Generation), and intelligent file organization across all BD intelligence data.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA LAYER (Source Files)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  dashboard/public/data/          Engine Outputs           External    │
│  ├── jobs_enriched.json         ├── outputs/*.md         ├── Bullhorn│
│  ├── contacts_classified.json   ├── briefings/           ├── Notion  │
│  ├── programs_enriched.json     └── playbooks/           └── Apify   │
│  ├── call_notes_summary.json                                          │
│  └── past_performance.json                                            │
│                                                                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER (Engine 8)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  Document        │  │  Auto-Tagger     │  │  Indexer         │   │
│  │  Processor       │  │  (Rules + LLM)   │  │  Pipeline        │   │
│  │  (Docling)       │  │                  │  │                  │   │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘   │
│           │                     │                     │              │
│           └─────────────────────┼─────────────────────┘              │
│                                 ▼                                     │
│                    ┌────────────────────────┐                        │
│                    │  Sentence Transformers │                        │
│                    │  (all-MiniLM-L6-v2)    │                        │
│                    │  384-dim embeddings    │                        │
│                    └────────────┬───────────┘                        │
│                                 │                                     │
└─────────────────────────────────┼───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER (Qdrant)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Engine8_Knowledge/data/qdrant/                                       │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐│
│  │   jobs    │ │ contacts  │ │ programs  │ │ documents │ │activities││
│  │   4 pts   │ │ 7,337 pts │ │  401 pts  │ │  205 pts  │ │ 500 pts ││
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └─────────┘│
│                                                                       │
│  Total: 8,447 indexed records with semantic embeddings                │
│                                                                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ACCESS LAYER (APIs)                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────┐  ┌──────────────────────┐                  │
│  │  FastAPI Server      │  │  MCP Server          │                  │
│  │  localhost:8100      │  │  bd-knowledge        │                  │
│  │                      │  │                      │                  │
│  │  /search             │  │  search_knowledge    │                  │
│  │  /ask                │  │  ask_knowledge       │                  │
│  │  /similar            │  │  get_program_intel   │                  │
│  │  /program/{name}     │  │  get_company_contacts│                  │
│  │  /company/{name}     │  │  reindex_knowledge   │                  │
│  └──────────────────────┘  └──────────────────────┘                  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Collections Schema

### 1. Jobs Collection (4 records)
Job postings with BD scoring and program mappings.

| Field | Type | Description |
|-------|------|-------------|
| title | string | Job title |
| company | string | Hiring company |
| location | string | Job location |
| program_name | string | Mapped federal program |
| clearance | string | Security clearance required |
| bd_priority | string | hot/warm/cold |
| bd_score | float | 0-100 BD priority score |
| source | string | Job board source |

### 2. Contacts Collection (7,337 records)
Contacts with tier classification from Bullhorn CRM.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Full name |
| first_name | string | First name |
| last_name | string | Last name |
| title | string | Job title |
| company | string | Company affiliation |
| email | string | Email address |
| phone | string | Phone number |
| tier | int | 1-6 tier classification |
| program | string | Associated program |
| source_db | string | Source database |

### 3. Programs Collection (401 records)
Federal programs and contracts.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Program name |
| prime_contractor | string | Prime contractor |
| location | string | Primary location |
| mission_area | string | Mission/domain area |
| contract_vehicle | string | Contract type |
| status | string | Active/completed |
| bd_priority | string | BD priority level |

### 4. Documents Collection (205 records)
Processed documents, briefings, and past performance.

| Field | Type | Description |
|-------|------|-------------|
| content | string | Document text content |
| title | string | Document title |
| summary | string | AI-generated summary |
| doc_type | string | Document category |
| source_file | string | Original file path |
| tags | list | Auto-generated tags |
| created_date | string | Creation date |

### 5. Activities Collection (500 records)
Bullhorn call notes and interactions.

| Field | Type | Description |
|-------|------|-------------|
| content | string | Activity notes |
| subject | string | Activity subject |
| contact_name | string | Related contact |
| company_name | string | Related company |
| activity_type | string | Call/email/meeting |
| date | string | Activity date |

---

## File Organization

### Project Structure
```
BD-Automation-Engine/
├── Engine1_Scraper/           # Apify job scraper configs
├── Engine2_ProgramMapping/    # Job-to-program matching
│   └── data/
│       └── Federal_Programs_Master.csv  # 401 programs
├── Engine3_OrgChart/          # Contact classification
│   └── data/
│       └── Prime_Contacts/    # 27 contractor databases
├── Engine4_Playbook/          # BD playbook generation
├── Engine5_Scoring/           # BD priority scoring
├── Engine6_QA/                # Quality assurance
├── Engine7_BullhornETL/       # Bullhorn data extraction
│   └── data/
│       └── bullhorn.db        # 293 MB SQLite database
├── Engine8_Knowledge/         # THIS SYSTEM
│   ├── scripts/
│   │   ├── vector_store.py    # Qdrant wrapper
│   │   ├── indexer.py         # Data ingestion
│   │   ├── rag_engine.py      # RAG with Claude
│   │   ├── auto_tagger.py     # Document classification
│   │   ├── document_processor.py  # File processing
│   │   └── file_watcher.py    # Auto-index new files
│   ├── api.py                 # FastAPI server
│   ├── data/
│   │   └── qdrant/            # Vector database files
│   └── README.md
├── dashboard/
│   └── public/data/           # Aggregated JSON views
│       ├── jobs_enriched.json
│       ├── contacts_classified.json
│       ├── programs_enriched.json
│       ├── call_notes_summary.json
│       └── past_performance.json
├── mcp/
│   └── knowledge-mcp-server/  # Claude Code integration
├── docs/                      # Documentation
└── outputs/                   # Generated briefings/playbooks
```

### Data Flow
```
Raw Sources → Engine Processing → Dashboard JSON → Knowledge Index → Search/RAG
```

---

## Usage

### CLI Commands

```bash
# Check collection statistics
python Engine8_Knowledge/scripts/vector_store.py --stats

# Search a specific collection
python Engine8_Knowledge/scripts/vector_store.py --search "DCGS analyst" --collection contacts

# Search all collections
python Engine8_Knowledge/scripts/vector_store.py --search "Leidos cybersecurity" --collection all

# Reindex all data
python Engine8_Knowledge/scripts/indexer.py --all

# Index specific collection
python Engine8_Knowledge/scripts/indexer.py --collection contacts
```

### Python API

```python
from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore

# Initialize store
store = BDKnowledgeStore()

# Search contacts
results = store.search("DCGS program manager", "contacts", limit=10)
for r in results:
    print(f"[{r.score:.3f}] {r.payload['name']} at {r.payload['company']}")

# Search across all collections
all_results = store.search_all("Leidos cybersecurity", limit_per_collection=5)

# Find similar items
similar = store.find_similar(item_id="uuid-here", collection="contacts")

# Cross-reference queries
contacts = store.find_contacts_for_program("DCGS")
jobs = store.find_jobs_for_program("DCGS")
intel = store.get_program_intelligence("DCGS")
```

### REST API

```bash
# Start server
python Engine8_Knowledge/api.py

# Search endpoint
curl -X POST http://localhost:8100/search \
  -H "Content-Type: application/json" \
  -d '{"query": "DCGS analyst", "collection": "contacts", "limit": 10}'

# Ask endpoint (RAG)
curl -X POST http://localhost:8100/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What contacts do we have at Leidos working on DCGS?"}'

# Stats endpoint
curl http://localhost:8100/stats
```

---

## Auto-Tagging Taxonomy

The system automatically classifies documents using these categories:

| Category | Examples |
|----------|----------|
| program | DCGS, GBSD, NGI, DES, JADC2, Navy, Army, Air Force |
| contractor | Leidos, GDIT, CACI, Peraton, Northrop, Lockheed, Raytheon |
| clearance | TS/SCI, Top Secret, Secret, Public Trust, None |
| priority | hot, warm, cold |
| location | DC Metro, Arlington, San Diego, Remote, Colorado Springs |
| skill | Cloud, DevOps, Cybersecurity, AI/ML, Systems Engineering |

---

## Maintenance

### Reindexing
Run after data updates:
```bash
python Engine8_Knowledge/scripts/indexer.py --all
```

### Adding New Data Sources
1. Add loader method to `indexer.py`
2. Define collection config in `vector_store.py`
3. Run indexer for new collection

### Monitoring
```bash
# Check index health
python Engine8_Knowledge/scripts/vector_store.py --stats

# View recent indexing logs
# Logs are written to stdout with INFO level
```

---

## Integration Points

### With Other Engines
- **Engine 2**: Provides program mappings for job enrichment
- **Engine 3**: Provides contact classification tiers
- **Engine 5**: Provides BD scores for prioritization
- **Engine 7**: Provides Bullhorn CRM data

### With External Systems
- **Notion**: Sync contacts and programs
- **n8n**: Workflow automation triggers
- **Claude Code**: MCP server for AI assistance

---

## Next Steps

See `docs/KNOWLEDGE_SYSTEM_ROADMAP.md` for planned enhancements.
