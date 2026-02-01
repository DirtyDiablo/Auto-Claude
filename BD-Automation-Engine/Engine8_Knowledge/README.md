# Engine 8: Knowledge Management System

AI-powered file management and knowledge retrieval system for the BD-Automation-Engine.

## Features

- **Semantic Search** - Search across jobs, contacts, programs, documents, and activities using natural language
- **RAG (Retrieval Augmented Generation)** - Ask questions and get AI-generated answers with source citations
- **Auto-Tagging** - Automatically classify documents by program, contractor, clearance, etc.
- **Document Processing** - Process PDFs, Excel, CSV, and other file formats
- **MCP Integration** - Native Claude Code integration via MCP server

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 DATA SOURCES                             │
│  Dashboard JSON | Bullhorn DB | Documents | Exports      │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              DOCUMENT PROCESSOR (Docling)                │
│  PDF, XLSX, CSV, TXT → Chunked text + metadata          │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                AUTO-TAGGER (Rules + LLM)                 │
│  Classify by program, contractor, clearance, etc.       │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 QDRANT VECTOR DB                         │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐   │
│  │  jobs   │ │ contacts │ │ programs │ │ documents │   │
│  └─────────┘ └──────────┘ └──────────┘ └───────────┘   │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 KNOWLEDGE API (FastAPI)                  │
│  /search | /ask | /similar | /program | /company        │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 MCP SERVER (bd-knowledge)                │
│  search_knowledge | ask_knowledge | get_program_intel   │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Index Data

```bash
# Index all dashboard data
python Engine8_Knowledge/scripts/indexer.py --all

# Check stats
python Engine8_Knowledge/scripts/indexer.py --stats
```

### 3. Start the API Server

```bash
python Engine8_Knowledge/api.py
```

API available at: http://localhost:8100
Docs at: http://localhost:8100/docs

### 4. Build MCP Server

```bash
cd mcp/knowledge-mcp-server
npm install
npm run build
```

### 5. Search from CLI

```bash
# Semantic search
python Engine8_Knowledge/scripts/vector_store.py --search "DCGS analyst" --collection jobs

# Ask a question
python Engine8_Knowledge/scripts/rag_engine.py "What contacts do we have at Leidos?"
```

## Collections

| Collection | Description | Key Fields |
|------------|-------------|------------|
| `jobs` | Job postings with BD scores | title, company, program_name, clearance |
| `contacts` | Contacts with tier classification | name, title, company, tier, email |
| `programs` | Federal programs and contracts | name, prime_contractor, contract_value |
| `documents` | Processed docs, briefings, past perf | title, content, doc_type |
| `activities` | Call notes, interactions | content, contact_name, date |

## API Endpoints

### Search
```
POST /search
{
  "query": "DCGS analyst",
  "collection": "jobs",
  "limit": 10
}
```

### Ask (RAG)
```
POST /ask
{
  "question": "What contacts do we have at Leidos working on DCGS?",
  "limit": 5
}
```

### Specialized
- `GET /program/{program_name}` - Program intelligence
- `GET /company/{company_name}` - Company intelligence
- `GET /contacts/at/{company_name}` - Contacts at company
- `GET /jobs/for/{program_name}` - Jobs for program

### Management
- `GET /stats` - Collection statistics
- `POST /index/all` - Reindex all data
- `POST /index/{collection}` - Reindex specific collection

## MCP Tools (via Claude Code)

When the MCP server is running, Claude Code has access to:

- `search_knowledge` - Semantic search across collections
- `ask_knowledge` - RAG-powered question answering
- `find_similar` - Find similar items
- `get_program_intel` - Program intelligence report
- `get_company_contacts` - Find contacts at a company
- `get_knowledge_stats` - Collection statistics
- `reindex_knowledge` - Trigger reindexing

## File Structure

```
Engine8_Knowledge/
├── __init__.py           # Module exports
├── api.py                # FastAPI server
├── data/                 # Qdrant data storage
│   └── qdrant/           # Vector database files
├── scripts/
│   ├── vector_store.py   # Qdrant wrapper
│   ├── indexer.py        # Data indexing pipeline
│   ├── document_processor.py  # Document processing
│   ├── rag_engine.py     # RAG with Claude
│   ├── auto_tagger.py    # Auto-classification
│   └── file_watcher.py   # Watch for new files
└── README.md
```

## Configuration

### Environment Variables

```bash
# Required for RAG
ANTHROPIC_API_KEY=your-key

# API Server
KNOWLEDGE_API_HOST=127.0.0.1
KNOWLEDGE_API_PORT=8100

# MCP Server
KNOWLEDGE_API_URL=http://127.0.0.1:8100
```

### MCP Configuration (.mcp.json)

```json
{
  "mcpServers": {
    "bd-knowledge": {
      "command": "node",
      "args": ["mcp/knowledge-mcp-server/build/index.js"],
      "env": {
        "KNOWLEDGE_API_URL": "http://127.0.0.1:8100"
      }
    }
  }
}
```

## Auto-Tagging Taxonomy

The auto-tagger recognizes these categories:

- **program**: DCGS, GBSD, NGI, DES, JADC2, etc.
- **contractor**: Leidos, GDIT, Northrop, CACI, etc.
- **clearance**: TS/SCI, Top Secret, Secret, Public Trust
- **priority**: hot, warm, cold
- **location**: DC Metro, Arlington, Remote, etc.
- **skill**: Cloud, DevOps, Cybersecurity, etc.

## Integration with Orchestrator

Engine 8 is integrated with the main pipeline. After dashboard export:

```bash
python orchestrator.py --input data/jobs.json
# ... runs all engines including knowledge indexing
```

To skip knowledge indexing:
```bash
python orchestrator.py --input data/jobs.json --no-knowledge
```

## Troubleshooting

### "qdrant-client not installed"
```bash
pip install qdrant-client sentence-transformers
```

### "Knowledge API not available"
Make sure the API server is running:
```bash
python Engine8_Knowledge/api.py
```

### Empty search results
Run indexing first:
```bash
python Engine8_Knowledge/scripts/indexer.py --all
```
