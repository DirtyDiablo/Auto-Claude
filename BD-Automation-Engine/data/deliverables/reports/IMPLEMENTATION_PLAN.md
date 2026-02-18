# AI-Powered File Management Implementation Plan
## N8N Builder Project Knowledge System

---

## CURRENT STATE ANALYSIS

### File Inventory (833+ files)
| Type | Count | Current State |
|------|-------|---------------|
| Python Scripts | 143 | Scattered across root, data/, scripts/, output/ |
| CSV Files | 398 | Mixed in root, data/, output/, exports/ |
| Excel Files | 120 | Mixed locations, some temp files (~$) |
| Markdown Files | 129 | Reports and docs mixed in root |
| PDF Files | 39 | Reference docs, some duplicates |
| Word Docs | 4 | API documentation |

### Current Folder Structure Issues
1. **Root folder clutter** - 100+ files in root that should be organized
2. **Inconsistent naming** - Mix of snake_case, kebab-case, spaces
3. **Duplicate files** - Same CSVs with different names (enriched V2, V3, V4)
4. **No semantic organization** - Files organized by creation, not by topic
5. **External repos mixed in** - 5+ cloned repos that could be submodules

---

## PROPOSED ARCHITECTURE

```
C:\N8N Builder\
├── .claude/                    # Claude Code configuration
│   └── knowledge/              # Local RAG knowledge base
├── .mcp.json                   # MCP server configuration
│
├── knowledge-base/             # NEW: Unified knowledge layer
│   ├── embeddings/             # Vector embeddings (Qdrant/LanceDB)
│   ├── documents/              # Processed documents
│   ├── code-graph/             # Code-Graph-RAG data
│   └── indexes/                # Search indexes
│
├── src/                        # NEW: All Python source code
│   ├── discovery/              # Federal programs discovery
│   ├── enrichment/             # Data enrichment scripts
│   ├── intelligence/           # BD & Bullhorn intelligence
│   ├── pipeline/               # Data pipeline scripts
│   └── utils/                  # Shared utilities
│
├── data/                       # REORGANIZED: Input data only
│   ├── bullhorn/               # Bullhorn CRM exports
│   ├── federal/                # Federal program data
│   ├── reference/              # Lookup tables, mappings
│   └── raw/                    # Unprocessed imports
│
├── output/                     # REORGANIZED: Generated outputs
│   ├── intelligence/           # BD intelligence outputs
│   ├── targeting/              # ZoomInfo/territory outputs
│   ├── reports/                # Markdown reports
│   └── exports/                # Excel/CSV exports for users
│
├── docs/                       # Documentation
│   ├── research/               # Research documents (like this)
│   ├── guides/                 # How-to guides
│   └── api/                    # API documentation
│
├── external/                   # External repositories
│   ├── capture-mcp-server/     # Submodule
│   ├── n8n-mcp/                # Submodule
│   └── n8n-skills/             # Submodule
│
└── projects/                   # N8N workflow projects
    └── [workflow-name]/        # Per-workflow architectures
```

---

## IMPLEMENTATION PHASES

### PHASE 1: File Organization (No AI Required)
**Duration: 1-2 hours**
**Risk: Low**

#### Step 1.1: Create New Directory Structure
```bash
mkdir -p src/{discovery,enrichment,intelligence,pipeline,utils}
mkdir -p data/{bullhorn,federal,reference,raw}
mkdir -p output/{intelligence,targeting,reports,exports}
mkdir -p docs/{research,guides,api}
mkdir -p external
mkdir -p knowledge-base/{embeddings,documents,code-graph,indexes}
```

#### Step 1.2: Move Files by Category

**Python Scripts → src/**
| From | To | Pattern |
|------|-----|---------|
| `*discovery*.py` | `src/discovery/` | Federal discovery |
| `*enrich*.py` | `src/enrichment/` | Data enrichment |
| `*intelligence*.py`, `*bullhorn*.py` | `src/intelligence/` | BD intel |
| `*pipeline*.py`, `complete-*.py` | `src/pipeline/` | Pipelines |
| `analyze-*.py`, `test-*.py` | `src/utils/` | Utilities |

**Data Files → data/**
| From | To | Pattern |
|------|-----|---------|
| `data/bullhorn_*` | `data/bullhorn/` | Bullhorn exports |
| `Federal Programs*.csv` | `data/federal/` | Federal data |
| `Lookup-Tables/*`, `DIIG-*/*` | `data/reference/` | Lookups |
| `SAM_*.xlsx`, `*.docx` | `data/reference/` | Reference docs |

**Output Files → output/**
| From | To | Pattern |
|------|-----|---------|
| `ZOOMINFO_*.xlsx`, `AM_CALL_LIST.xlsx` | `output/targeting/` | Targeting |
| `*REPORT*.md`, `*SUMMARY*.md` | `output/reports/` | Reports |
| `*_ENRICHED*.csv` | `output/exports/` | Enriched data |

**External Repos → external/**
- Move: `capture-mcp-server/`, `n8n-mcp/`, `n8n-skills/`
- Move: `akshayakula-OpenSAM/`, `ataddesse-govConDiscovery/`, etc.

#### Step 1.3: Update Import Paths
Create `src/__init__.py` files and update relative imports in Python scripts.

#### Step 1.4: Update .gitignore
```gitignore
# Organized structure
data/bullhorn/          # CRM exports (sensitive)
data/raw/               # Raw imports
output/                 # Generated files
knowledge-base/embeddings/  # Vector data
*.xlsx                  # Excel temp files
~$*                     # Office temp files
```

---

### PHASE 2: Local Knowledge Base Setup
**Duration: 2-4 hours**
**Risk: Medium**

Based on the research document, I recommend starting with **mcp-local-rag** for immediate value with zero complexity.

#### Step 2.1: Install mcp-local-rag
```bash
# Uses LanceDB (serverless, file-based)
pip install mcp-local-rag lancedb
```

#### Step 2.2: Configure MCP Server
Update `.mcp.json`:
```json
{
  "mcpServers": {
    "n8n-mcp": { ... existing ... },
    "capture-mcp-server": { ... existing ... },
    "local-rag": {
      "command": "python",
      "args": ["-m", "mcp_local_rag"],
      "env": {
        "KNOWLEDGE_BASE_PATH": "C:\\N8N Builder\\knowledge-base",
        "EMBEDDING_MODEL": "all-MiniLM-L6-v2"
      }
    }
  }
}
```

#### Step 2.3: Initial Document Ingestion
Ingest key documents for immediate searchability:
- All markdown reports
- Python docstrings/comments
- CSV headers and schemas
- PDF reference documents

---

### PHASE 3: Advanced Knowledge Graph (Code-Graph-RAG)
**Duration: 1-2 days**
**Risk: Medium-High**

#### Step 3.1: Install Code-Graph-RAG
```bash
git clone https://github.com/vitali87/code-graph-rag.git
cd code-graph-rag
pip install -r requirements.txt
```

#### Step 3.2: Configure for Multi-Repo
```yaml
# code-graph-config.yaml
repositories:
  - path: C:\N8N Builder\src
    name: n8n-builder-core
  - path: C:\N8N Builder\external\n8n-mcp
    name: n8n-mcp
  - path: C:\N8N Builder\external\capture-mcp-server
    name: capture-mcp

graph:
  database: memgraph
  connection: bolt://localhost:7687

mcp:
  enabled: true
  port: 8080
```

#### Step 3.3: MCP Integration
Add to `.mcp.json`:
```json
{
  "mcpServers": {
    "code-graph": {
      "command": "python",
      "args": ["-m", "code_graph_rag.mcp_server"],
      "env": {
        "CONFIG_PATH": "C:\\N8N Builder\\code-graph-config.yaml"
      }
    }
  }
}
```

---

### PHASE 4: Document Processing Pipeline
**Duration: 2-4 hours**
**Risk: Low**

#### Step 4.1: Install Docling
```bash
pip install docling
```

#### Step 4.2: Create Processing Script
```python
# src/utils/document_processor.py
from docling.document_converter import DocumentConverter
from pathlib import Path

def process_documents(input_dir: str, output_dir: str):
    """Process PDFs, DOCX, XLSX into searchable format"""
    converter = DocumentConverter()

    for file in Path(input_dir).glob("**/*"):
        if file.suffix in ['.pdf', '.docx', '.xlsx']:
            result = converter.convert(file)
            # Export to markdown for RAG ingestion
            output_path = Path(output_dir) / f"{file.stem}.md"
            output_path.write_text(result.document.export_to_markdown())
```

#### Step 4.3: Schedule Processing
Create n8n workflow to watch for new files and auto-process.

---

### PHASE 5: Vector Database (Qdrant)
**Duration: 4-8 hours**
**Risk: Medium**

Only proceed to this phase if Phase 2 (mcp-local-rag) proves insufficient.

#### Step 5.1: Deploy Qdrant
```bash
docker run -p 6333:6333 -v $(pwd)/knowledge-base/qdrant:/qdrant/storage qdrant/qdrant
```

#### Step 5.2: Configure Collections
```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

client = QdrantClient("localhost", port=6333)

# Create collections for different content types
collections = {
    "code": {"size": 768, "distance": Distance.COSINE},
    "documents": {"size": 768, "distance": Distance.COSINE},
    "federal_programs": {"size": 768, "distance": Distance.COSINE},
    "intelligence": {"size": 768, "distance": Distance.COSINE}
}

for name, params in collections.items():
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(**params)
    )
```

---

## RECOMMENDED IMPLEMENTATION ORDER

### Immediate (Today)
1. **Phase 1.1-1.2**: Create directory structure and move files
2. **Phase 1.4**: Update .gitignore

### This Week
3. **Phase 1.3**: Update Python imports
4. **Phase 2**: Install and configure mcp-local-rag

### Next Week
5. **Phase 4**: Set up Docling document processing
6. **Phase 3**: Evaluate Code-Graph-RAG need

### Future (If Needed)
7. **Phase 5**: Migrate to Qdrant for scale

---

## DECISION POINTS FOR YOUR REVIEW

### Question 1: File Organization Approach
**Option A: Full Reorganization (Recommended)**
- Move all files to new structure
- Update all imports and paths
- Clean slate, easier to maintain

**Option B: Gradual Migration**
- Keep existing structure
- Symlink to new structure
- Lower risk, slower progress

### Question 2: Knowledge Base Starting Point
**Option A: mcp-local-rag (Recommended)**
- Zero setup, works immediately
- LanceDB is serverless
- Limited to ~100k documents

**Option B: Qdrant from Start**
- More setup required
- Scales to millions
- Better for long-term

### Question 3: Code Intelligence Priority
**Option A: Skip Code-Graph-RAG**
- Use basic file search
- Faster implementation
- Less capability

**Option B: Full Code-Graph-RAG**
- Cross-repo intelligence
- Requires Memgraph database
- Significant setup

### Question 4: Document Processing
**Option A: Manual Processing**
- Process documents as needed
- No automation overhead

**Option B: Automated Pipeline**
- Watch folders for new files
- n8n workflow triggers Docling
- More complex but hands-off

---

## IMMEDIATE VALUE: What Claude Code Can Do After Phase 2

Once mcp-local-rag is configured, Claude Code can:

1. **Semantic Search**
   - "Find all scripts related to federal program discovery"
   - "Which files mention GSMO program?"
   - "Show me the data enrichment pipeline"

2. **Cross-File Context**
   - Understand relationships between CSVs and Python scripts
   - Find where specific columns are used
   - Track data flow from raw to output

3. **Intelligent Suggestions**
   - Recommend relevant files when working on tasks
   - Surface related documentation
   - Find similar patterns in existing code

---

## SUCCESS METRICS

| Metric | Current | Target |
|--------|---------|--------|
| Files in root directory | 100+ | <20 |
| Time to find relevant file | Minutes | Seconds |
| Cross-file search capability | Manual grep | Semantic search |
| New file categorization | Manual | Auto-suggested |
| Claude context awareness | Current folder only | Full project |

---

## NEXT STEPS (Awaiting Your Decision)

1. Review the 4 decision points above
2. Tell me which options you prefer
3. I'll execute the selected approach

**My Recommendation**:
- Phase 1 Option A (Full reorganization)
- Phase 2 Option A (mcp-local-rag to start)
- Phase 3 Option A (Skip Code-Graph-RAG initially)
- Phase 4 Option A (Manual processing to start)

This gets you immediate value with minimal complexity. We can add advanced features later as needs emerge.
