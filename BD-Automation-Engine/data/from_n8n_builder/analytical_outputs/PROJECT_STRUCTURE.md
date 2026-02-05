# N8N Builder Project Structure
## Organized File System Documentation

---

## Directory Overview

```
C:\N8N Builder\
│
├── .claude/                    # Claude Code configuration
├── .mcp.json                   # MCP server configuration (gitignored)
├── .mcp.json.example           # MCP config template
├── .env.example                # Environment variables template
│
├── src/                        # SOURCE CODE
│   ├── api_clients/            # API client implementations
│   │   ├── base.py             # Base API client
│   │   ├── sam.py              # SAM.gov API client
│   │   ├── tango.py            # Tango API client
│   │   └── usaspending.py      # USASpending API client
│   │
│   ├── config/                 # Configuration modules
│   │   └── settings.py         # Application settings
│   │
│   ├── database/               # Database models and migrations
│   │   ├── connection.py       # DB connection handling
│   │   ├── migrate_csv.py      # CSV to DB migration
│   │   └── models.py           # SQLAlchemy models
│   │
│   ├── discovery/              # Federal program discovery scripts
│   │   ├── federal-programs-discovery-engine.py
│   │   ├── dod-staffing-discovery.py
│   │   └── high-sub-spend-discovery.py
│   │
│   ├── enrichment/             # Data enrichment scripts
│   │   ├── enrich-federal-programs.py
│   │   ├── location_enricher.py
│   │   ├── org_hierarchy_builder.py
│   │   └── tango-enrichment.py
│   │
│   ├── intelligence/           # BD & CRM intelligence tools
│   │   ├── advanced_bd_tools.py
│   │   ├── bullhorn_data_processor.py
│   │   ├── categorize_programs.py
│   │   ├── competitive_intelligence_tracker.py
│   │   ├── find_virgin_territory.py
│   │   ├── kpi_dashboard_generator.py
│   │   ├── recommendation_engine.py
│   │   ├── sdvosb_targeting_engine.py
│   │   └── territory_grab_analysis.py
│   │
│   ├── pipeline/               # Data pipeline scripts
│   │   ├── complete-pipeline.py
│   │   ├── filter-active-programs.py
│   │   └── merge-and-deduplicate.py
│   │
│   └── utils/                  # Utility scripts
│       ├── analyze-department-codes.py
│       ├── job-program-mapper.py
│       └── test-*.py
│
├── data/                       # DATA FILES
│   ├── bullhorn/               # Bullhorn CRM exports (gitignored)
│   │   └── exports/            # Raw XLS exports from Bullhorn
│   │
│   ├── federal/                # Federal program data
│   │   ├── contracts/          # Contract-specific data
│   │   ├── Federal Programs MASTER.csv
│   │   └── DISCOVERED_PROGRAMS_*.csv
│   │
│   ├── reference/              # Reference data & lookup tables
│   │   ├── DIIG-CSIS-Lookup-Tables/
│   │   ├── Lookup-Tables/
│   │   ├── pws_documents/
│   │   └── *.docx, *.pdf       # API documentation
│   │
│   ├── cache/                  # API response caches (gitignored)
│   │   ├── contract_cache.json
│   │   └── tango_cache.json
│   │
│   └── raw/                    # Unprocessed imports (gitignored)
│
├── output/                     # GENERATED OUTPUTS
│   ├── intelligence/           # BD intelligence outputs
│   │   ├── bullhorn/           # Bullhorn analysis outputs (gitignored)
│   │   ├── bd_targets.csv
│   │   └── hiring_intelligence.csv
│   │
│   ├── targeting/              # Contact targeting outputs
│   │   ├── AM_CALL_LIST.xlsx
│   │   ├── AVAILABLE_PROGRAMS_1000.xlsx
│   │   ├── ZOOMINFO_SNIPER_STRATEGY.md
│   │   └── ZOOMINFO_*.xlsx
│   │
│   ├── reports/                # Markdown reports
│   │   ├── COMPREHENSIVE-AUDIT-REPORT.md
│   │   ├── TANGO-API-TESTING-RESULTS.md
│   │   └── V4-*.md
│   │
│   ├── exports/                # General CSV/Excel exports
│   │   ├── jobs_mapped_to_programs.csv
│   │   └── vendor_uei_lookup.csv
│   │
│   └── program_intelligence/   # Program-specific intel
│       ├── 01_program_directory.csv
│       └── 06_hot_programs_hiring_now.csv
│
├── docs/                       # DOCUMENTATION
│   ├── research/               # Research documents
│   │   ├── IMPLEMENTATION_PLAN.md
│   │   └── compass_artifact_*.md
│   │
│   ├── guides/                 # How-to guides
│   │
│   └── api/                    # API documentation
│
├── external/                   # EXTERNAL REPOSITORIES
│   ├── n8n-mcp/                # N8N MCP server
│   ├── n8n-skills/             # N8N Claude skills
│   ├── capture-mcp-server/     # Federal data MCP server
│   ├── tango-python/           # Tango SDK
│   ├── usaspending-api/        # USASpending reference
│   └── [other repos]/          # Cloned reference repos
│
├── knowledge-base/             # AI KNOWLEDGE SYSTEM
│   ├── embeddings/             # Vector embeddings (gitignored)
│   ├── documents/              # Processed documents
│   └── indexes/                # Search indexes (gitignored)
│
├── projects/                   # N8N WORKFLOW PROJECTS
│   └── [workflow-name]/        # Per-workflow architectures
│
├── logs/                       # LOG FILES (gitignored)
│   ├── discovery-*.log
│   ├── enrichment-*.log
│   └── dod-discovery-*.log
│
├── CLAUDE.MD                   # Claude orchestrator instructions
├── README.md                   # Project overview
├── QUICK-START.md              # Quick start guide
├── PROJECT_STRUCTURE.md        # This file
└── requirements.txt            # Python dependencies
```

---

## Key Directories Explained

### `/src` - Source Code
All Python source code organized by function:
- **discovery/** - Scripts that discover federal programs and contracts
- **enrichment/** - Scripts that add data to existing records
- **intelligence/** - BD and CRM analysis tools
- **pipeline/** - Data processing pipelines
- **utils/** - Helper scripts and utilities

### `/data` - Data Files
Input data organized by source:
- **bullhorn/** - CRM exports (sensitive, gitignored)
- **federal/** - Federal program data (can be committed)
- **reference/** - Lookup tables and documentation
- **cache/** - API caches (gitignored)
- **raw/** - Unprocessed imports (gitignored)

### `/output` - Generated Outputs
All generated files:
- **intelligence/** - Analysis results
- **targeting/** - Contact lists and strategies
- **reports/** - Markdown reports
- **exports/** - CSV/Excel exports

### `/external` - External Repositories
Cloned or linked repositories:
- MCP servers (n8n-mcp, capture-mcp-server)
- SDKs (tango-python)
- Reference implementations

### `/knowledge-base` - AI Knowledge System
Intelligent file management and semantic search:
- **embeddings/** - LanceDB vector database (gitignored)
- **file_categories.json** - Cached file categorizations
- **processed_docs.json** - Cached processed documents

### `/src/knowledge_base` - Knowledge Base Module
Python module providing:
- **indexer.py** - Document indexing into LanceDB
- **search.py** - Semantic search over indexed documents
- **categorizer.py** - Intelligent file classification
- **document_processor.py** - PDF/DOCX/Excel text extraction
- **mcp_server.py** - MCP server with 14 tools for Claude Code

---

## File Naming Conventions

### Python Scripts
- Use kebab-case: `federal-programs-discovery-engine.py`
- Version suffixes: `script-v2.py`, `script-FINAL.py`

### Data Files
- Use spaces for readability: `Federal Programs MASTER.csv`
- Version indicators: `V2`, `V3`, `ENRICHED`

### Reports
- Use CAPS kebab-case: `COMPREHENSIVE-AUDIT-REPORT.md`
- Include version/status: `V4-FINAL-SUMMARY.md`

---

## Sensitive Data Locations

The following directories contain sensitive data and are gitignored:

| Directory | Contains | Sensitivity |
|-----------|----------|-------------|
| `data/bullhorn/` | CRM exports with employee data | HIGH |
| `data/raw/` | Unprocessed imports | MEDIUM |
| `data/cache/` | API response caches | LOW |
| `output/intelligence/bullhorn/` | Analyzed CRM data | HIGH |
| `output/targeting/*.xlsx` | Contact strategies | MEDIUM |
| `logs/` | Execution logs | LOW |
| `.mcp.json` | API keys | CRITICAL |

---

## Quick Reference Commands

### Find a script by name
```bash
find src -name "*keyword*"
```

### Find all files mentioning a program
```bash
grep -r "GSMO" data/ output/
```

### List all Python scripts
```bash
find src -name "*.py" | wc -l
```

### Check project structure
```bash
tree -L 2 -d
```

---

## Migration Notes

This structure was created on 2026-01-23. Key changes:
- 196+ files reorganized from root to proper directories
- External repos moved to `/external`
- Intelligence scripts consolidated in `src/intelligence/`
- Bullhorn outputs moved to `output/intelligence/bullhorn/`
- Reference docs consolidated in `data/reference/`
