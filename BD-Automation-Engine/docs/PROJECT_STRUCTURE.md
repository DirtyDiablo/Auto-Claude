# BD-Automation-Engine Project Structure

## Overview

BD-Automation-Engine is a comprehensive Business Development intelligence system for federal defense programs. It consists of 8 interconnected engines that form a complete pipeline from job scraping to AI-powered knowledge retrieval.

---

## Directory Structure

```
BD-Automation-Engine/
│
├── .env                          # API keys (NEVER commit)
├── .env.example                  # Template for .env
├── .mcp.json                     # MCP server configuration for Claude Code
├── CLAUDE.md                     # AI agent instructions
├── requirements.txt              # Python dependencies
├── orchestrator.py               # Main pipeline orchestrator
│
├── Engine1_Scraper/              # Job scraping (Apify)
│   └── configs/                  # Apify actor configurations
│
├── Engine2_ProgramMapping/       # Job-to-program matching
│   ├── scripts/
│   │   ├── job_standardizer.py   # LLM field extraction
│   │   ├── program_mapper.py     # Multi-signal matching
│   │   ├── pipeline.py           # 7-stage pipeline
│   │   └── exporters.py          # Notion/n8n export
│   └── data/
│       └── Federal_Programs_Master.csv  # 388 federal programs
│
├── Engine3_OrgChart/             # Contact classification
│   ├── scripts/
│   │   └── contact_classifier.py # 6-tier hierarchy
│   └── data/
│       ├── Prime_Contacts/       # 25 contractor CSVs
│       │   ├── Leidos_Contacts.csv
│       │   ├── GDIT_Contacts.csv
│       │   ├── Northrop_Grumman_Contacts.csv
│       │   └── ... (25 total)
│       └── Prime_Contacts_Enriched/  # Tier-classified contacts
│           ├── Leidos_Contacts_Enriched.csv
│           └── ...
│
├── Engine4_Playbook/             # BD playbook generation
│   └── scripts/
│       └── bd_playbook_generator.py
│
├── Engine5_Scoring/              # BD priority scoring
│   └── scripts/
│       └── bd_scoring.py         # 0-100 scoring algorithm
│
├── Engine6_QA/                   # Quality assurance
│   ├── scripts/
│   └── data/
│       └── review_queue.json     # Items needing review
│
├── Engine7_BullhornETL/          # CRM data extraction
│   ├── scripts/
│   │   ├── analyze_prime_contacts.py
│   │   ├── build_prime_contact_databases.py
│   │   └── intelligent_contact_classifier.py
│   └── data/
│       └── bullhorn.db           # 293 MB SQLite database
│
├── Engine8_Knowledge/            # AI KNOWLEDGE SYSTEM
│   ├── __init__.py
│   ├── api.py                    # FastAPI server (port 8100)
│   ├── README.md
│   ├── scripts/
│   │   ├── __init__.py
│   │   ├── vector_store.py       # Qdrant wrapper (8,447 records)
│   │   ├── indexer.py            # Data ingestion pipeline
│   │   ├── rag_engine.py         # RAG with Claude
│   │   ├── auto_tagger.py        # Document classification
│   │   ├── document_processor.py # PDF/DOCX processing
│   │   └── file_watcher.py       # Auto-index new files
│   └── data/
│       └── qdrant/               # Vector database storage
│           ├── meta.json
│           └── collections/      # Indexed data
│
├── dashboard/                    # React dashboard
│   └── public/data/              # Aggregated JSON views
│       ├── contact_org_chart.json
│       ├── correlation_summary_enriched.json
│       ├── data_freshness.json
│       ├── jobs_enriched.json
│       ├── past_performance.json
│       ├── prime_org_chart.json
│       └── program_org_chart.json
│
├── mcp/                          # MCP servers for Claude Code
│   ├── knowledge-mcp-server/     # Knowledge base integration
│   │   ├── src/
│   │   │   └── index.ts          # TypeScript source
│   │   ├── build/
│   │   │   └── index.js          # Compiled JavaScript
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── mapify-mcp-server/        # Mapify integration
│
├── scripts/                      # Utility scripts
│   ├── start_knowledge_api.bat   # Windows batch startup
│   └── start_knowledge_api.ps1   # PowerShell startup
│
├── docs/                         # Documentation
│   ├── PROJECT_STRUCTURE.md      # THIS FILE
│   ├── AI_FILESYSTEM_GUIDE.md    # AI usage guide
│   ├── KNOWLEDGE_SYSTEM_GUIDE.md # Architecture details
│   ├── RAG_USAGE_GUIDE.md        # RAG patterns
│   ├── KNOWLEDGE_SYSTEM_ROADMAP.md
│   ├── CROSS_PROJECT_SHARING.md
│   ├── SUGGESTED_ENHANCEMENTS.md
│   └── UPSTREAM_MERGE_STRATEGY.md
│
├── outputs/                      # Generated files (gitignored)
│   ├── playbooks/
│   ├── briefings/
│   └── reports/
│
├── logs/                         # API logs (gitignored)
│
└── tests/                        # Test suite
```

---

## Engine Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         BD AUTOMATION PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │   Engine 1   │───▶│   Engine 2   │───▶│   Engine 3   │               │
│  │   Scraper    │    │   Program    │    │   OrgChart   │               │
│  │   (Apify)    │    │   Mapping    │    │   Contacts   │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│         │                   │                   │                        │
│         ▼                   ▼                   ▼                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │   Engine 4   │    │   Engine 5   │    │   Engine 6   │               │
│  │   Playbook   │    │   Scoring    │    │     QA       │               │
│  │   Generator  │    │   (0-100)    │    │   Alerts     │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│         │                   │                   │                        │
│         └───────────────────┼───────────────────┘                        │
│                             ▼                                            │
│                   ┌──────────────────┐                                   │
│                   │    Engine 7      │                                   │
│                   │   Bullhorn ETL   │                                   │
│                   │   (CRM Data)     │                                   │
│                   └────────┬─────────┘                                   │
│                            │                                             │
│                            ▼                                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                       ENGINE 8: KNOWLEDGE                          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │  │
│  │  │   Qdrant    │  │   RAG       │  │   MCP       │                │  │
│  │  │   Vector DB │  │   Engine    │  │   Server    │                │  │
│  │  │  (8,447)    │  │  (Claude)   │  │  (Tools)    │                │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Engine 8: Knowledge System Architecture

### Components

```
Engine8_Knowledge/
│
├── api.py                    # FastAPI REST API
│   ├── GET  /health          # Health check
│   ├── GET  /stats           # Collection statistics
│   ├── POST /search          # Semantic search
│   ├── POST /ask             # RAG question answering
│   ├── POST /similar         # Find similar items
│   ├── GET  /program/{name}  # Program intelligence
│   ├── GET  /company/{name}  # Company contacts
│   └── POST /index/all       # Trigger reindexing
│
├── scripts/
│   ├── vector_store.py       # Core vector database operations
│   │   ├── BDKnowledgeStore  # Main class
│   │   ├── search()          # Semantic search
│   │   ├── find_similar()    # Similarity search
│   │   ├── index_data()      # Add records
│   │   └── get_collection_stats()
│   │
│   ├── indexer.py            # Data ingestion
│   │   ├── BDIndexer         # Main class
│   │   ├── index_all()       # Full reindex
│   │   ├── index_contacts()  # Contact collection
│   │   ├── index_programs()  # Programs collection
│   │   ├── index_jobs()      # Jobs collection
│   │   ├── index_documents() # Documents collection
│   │   └── index_activities()# Activities collection
│   │
│   ├── rag_engine.py         # RAG with Claude
│   │   ├── BDRAGEngine       # Main class
│   │   ├── ask()             # Answer questions
│   │   └── ask_with_sources()# Answer with citations
│   │
│   ├── auto_tagger.py        # Document classification
│   │   ├── AutoTagger        # Main class
│   │   ├── classify()        # Classify document
│   │   └── suggest_tags()    # Tag suggestions
│   │
│   ├── document_processor.py # Document processing
│   │   ├── BDDocumentProcessor
│   │   ├── process_file()    # Process single file
│   │   └── chunk_document()  # Split into chunks
│   │
│   └── file_watcher.py       # Auto-indexing
│       ├── BDFileWatcher     # Main class
│       └── start()           # Start watching
│
└── data/
    └── qdrant/               # Vector database
        ├── meta.json         # Database metadata
        └── collections/      # 5 collections
            ├── jobs/
            ├── contacts/
            ├── programs/
            ├── documents/
            └── activities/
```

### Data Collections

| Collection | Records | Source | Description |
|------------|---------|--------|-------------|
| **contacts** | 7,337 | Bullhorn CRM | Tier-classified contacts |
| **activities** | 500 | Bullhorn | Call notes, meetings |
| **programs** | 401 | Federal Programs CSV | Defense programs |
| **documents** | 205 | Past performance | Capability docs |
| **jobs** | 4 | Apify scraper | Job postings |
| **TOTAL** | **8,447** | | |

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Vector DB | Qdrant (embedded) | Semantic search storage |
| Embeddings | all-MiniLM-L6-v2 | 384-dim sentence vectors |
| LLM | Claude Sonnet | RAG answers |
| API | FastAPI + Uvicorn | REST endpoints |
| MCP | TypeScript server | Claude Code integration |

---

## MCP Configuration

The `.mcp.json` file configures Claude Code tool access:

```json
{
  "mcpServers": {
    "bd-knowledge": {
      "command": "node",
      "args": ["mcp/knowledge-mcp-server/build/index.js"],
      "env": {
        "KNOWLEDGE_API_URL": "http://127.0.0.1:8100"
      }
    },
    "n8n": { ... },
    "notion": { ... },
    "apify": { ... }
  }
}
```

### Available MCP Tools (when API running)

| Tool | Description |
|------|-------------|
| `search_knowledge` | Semantic search across collections |
| `ask_knowledge` | RAG Q&A with source citations |
| `find_similar` | Find similar items by ID |
| `get_program_intel` | Full program intelligence report |
| `get_company_contacts` | Company contact lookup |
| `get_knowledge_stats` | Collection statistics |
| `reindex_knowledge` | Trigger reindexing |

---

## Data Flow

### 1. Data Sources → Dashboard JSON

```
Engine7_BullhornETL/data/bullhorn.db  ─┐
Engine3_OrgChart/data/Prime_Contacts/ ─┼──▶ dashboard/public/data/*.json
Engine2_ProgramMapping/data/*.csv     ─┘
```

### 2. Dashboard JSON → Qdrant Vector DB

```
dashboard/public/data/contacts_classified.json ──▶ contacts collection
dashboard/public/data/programs_enriched.json   ──▶ programs collection
dashboard/public/data/jobs_enriched.json       ──▶ jobs collection
dashboard/public/data/past_performance.json    ──▶ documents collection
dashboard/public/data/call_notes_summary.json  ──▶ activities collection
```

### 3. Qdrant → Claude Code (via MCP)

```
User Query ──▶ MCP Server ──▶ FastAPI ──▶ Qdrant ──▶ Results
                                │
                                ▼
                          RAG Engine ──▶ Claude ──▶ Answer
```

---

## Configuration Files

### .env (API Keys)

```bash
# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI (embeddings fallback)
OPENAI_API_KEY=sk-...

# Notion
NOTION_TOKEN=ntn_...

# Apify
APIFY_API_TOKEN=apify_api_...

# n8n
N8N_API_URL=http://localhost:5678
N8N_API_KEY=...
```

### requirements.txt (Key Dependencies)

```
# Vector Database
qdrant-client>=1.7.0
sentence-transformers>=2.2.0

# API
fastapi>=0.109.0
uvicorn>=0.27.0

# RAG
llama-index>=0.10.0
llama-index-llms-anthropic>=0.1.0

# Document Processing
docling>=0.1.0
python-magic-bin>=0.4.14

# AI
anthropic>=0.18.0
openai>=1.12.0
```

---

## Startup Procedures

### Start Knowledge API

**Windows (CMD):**
```cmd
scripts\start_knowledge_api.bat
```

**PowerShell:**
```powershell
.\scripts\start_knowledge_api.ps1

# Or background mode:
.\scripts\start_knowledge_api.ps1 -Background
```

**Direct Python:**
```bash
python Engine8_Knowledge/api.py
```

### Verify API Running

```bash
curl http://localhost:8100/health
# {"status":"healthy","timestamp":"..."}

curl http://localhost:8100/stats
# {"collections":{...},"total_vectors":8447}
```

### Reindex Data

```bash
# Full reindex
python Engine8_Knowledge/scripts/indexer.py --all

# Single collection
python Engine8_Knowledge/scripts/indexer.py --collection contacts
```

---

## Common Operations

### Search Contacts

```bash
curl -X POST http://localhost:8100/search \
  -H "Content-Type: application/json" \
  -d '{"query": "DCGS program manager TS/SCI", "collection": "contacts", "limit": 10}'
```

### Ask a Question (RAG)

```bash
curl -X POST http://localhost:8100/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who are the key contacts at Leidos for DCGS?"}'
```

### Get Program Intelligence

```bash
curl http://localhost:8100/program/DCGS
```

---

## Git Workflow

**Branch:** `claude/setup-auto-claude-IrK21`

```bash
# All development on this branch
git checkout claude/setup-auto-claude-IrK21

# Commit changes
git add .
git commit -m "feat: description"

# Push to origin
git push origin claude/setup-auto-claude-IrK21
```

**DO NOT** merge to `develop` or `main` - those are upstream Auto-Claude branches.

---

## Troubleshooting

### API Won't Start

```bash
# Check if port in use
netstat -an | findstr 8100

# Kill existing process
taskkill /F /PID <pid>
```

### Empty Search Results

```bash
# Check index status
python -c "from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore; print(BDKnowledgeStore().get_collection_stats())"

# Reindex
python Engine8_Knowledge/scripts/indexer.py --all
```

### MCP Tools Not Working

1. Verify API running: `curl http://localhost:8100/health`
2. Check `.mcp.json` configuration
3. Restart Claude Code session

---

## File Reference Quick Links

| Purpose | File |
|---------|------|
| Start API | `scripts/start_knowledge_api.bat` |
| API server | `Engine8_Knowledge/api.py` |
| Vector store | `Engine8_Knowledge/scripts/vector_store.py` |
| Indexer | `Engine8_Knowledge/scripts/indexer.py` |
| RAG engine | `Engine8_Knowledge/scripts/rag_engine.py` |
| MCP config | `.mcp.json` |
| Dependencies | `requirements.txt` |
| AI instructions | `CLAUDE.md` |

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| `PROJECT_STRUCTURE.md` | This file - complete project overview |
| `AI_FILESYSTEM_GUIDE.md` | How to use the AI filesystem |
| `KNOWLEDGE_SYSTEM_GUIDE.md` | Engine 8 architecture details |
| `RAG_USAGE_GUIDE.md` | RAG patterns and examples |
| `SUGGESTED_ENHANCEMENTS.md` | Future improvement ideas |
| `CROSS_PROJECT_SHARING.md` | Multi-project integration |
| `KNOWLEDGE_SYSTEM_ROADMAP.md` | Development roadmap |

---

*Last updated: January 24, 2026*
