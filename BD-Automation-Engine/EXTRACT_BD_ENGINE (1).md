# DATA ARCHITECTURE EXTRACTION — BD-Automation-Engine
## Terminal Agent Task | Project: BD_ENGINE

**Save output as:** `data_architecture_bd_engine.json`

---

## YOUR CONTEXT

You are inside the **BD-Automation-Engine** repository — the central hub of the PTS BD platform. This project has:

- **4,221 files** (1,190 .py, 888 .ts/.tsx, 814 .csv, 460 .json, 523 .md)
- **8 Engines**: Scraper, ProgramMapping, OrgChart, Briefing/Playbook, Scoring, QA, BullhornETL, Knowledge
- **1,420,232 Qdrant vectors** across 12 collections
- **306MB Bullhorn SQLite DB** (50K+ contacts, 50K notes, 404K activities, 616 placements)
- **14-page React/TypeScript dashboard** with 50+ JSON data feeds
- **15+ AI agents**, LangGraph workflows, MCP servers, Dify integration

A previous audit documented **20 node types and 35+ relationships**. Your job is to VERIFY those exist in actual code and find everything MISSING — especially Qdrant payload schemas, Dashboard JSON feed schemas, Bullhorn SQLite table schemas, and FastAPI endpoint shapes.

---

## STEP 1: Targeted Discovery

Scan these EXACT paths in order:

```bash
# ════════════════════════════════════════════
# 1. QDRANT COLLECTIONS — #1 PRIORITY GAP
# ════════════════════════════════════════════
# These 12 collections exist with 1.42M total vectors.
# We need the PAYLOAD FIELD SCHEMA for each.

python3 -c "
from qdrant_client import QdrantClient
client = QdrantClient(host='localhost', port=6333)
collections = client.get_collections().collections
for c in collections:
    info = client.get_collection(c.name)
    print(f'=== {c.name} ===')
    print(f'  vectors: {info.points_count}')
    print(f'  indexed: {info.indexed_vectors_count}')
    try:
        vsize = info.config.params.vectors.size
    except:
        vsize = 'multi/named'
    print(f'  vector_size: {vsize}')
    results = client.scroll(c.name, limit=1)
    if results[0]:
        payload = results[0][0].payload
        print(f'  payload_fields ({len(payload)} fields):')
        for k, v in sorted(payload.items()):
            val_preview = str(v)[:80].replace(chr(10),' ')
            print(f'    {k}: {type(v).__name__} = {val_preview}')
    print()
" 2>/dev/null

# If Qdrant server not running, check indexing scripts for payload schemas:
grep -n "payload\|PointStruct\|upsert\|models.Record" Engine8_Knowledge/scripts/*.py 2>/dev/null
grep -n "payload\|PointStruct\|upsert" scripts/*.py 2>/dev/null

# ════════════════════════════════════════════
# 2. BULLHORN SQLITE — Complete table schemas
# ════════════════════════════════════════════
# bullhorn_master.db is 306MB. Get ALL tables and columns.

python3 << 'PYEOF'
import sqlite3, json
for db_path in ['Engine7_BullhornETL/data/bullhorn_master.db',
                'data/bullhorn_master.db',
                'Engine7_BullhornETL/data/bullhorn_past_performance.db']:
    try:
        conn = sqlite3.connect(db_path)
        tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print(f"\n=== {db_path} ({len(tables)} tables) ===")
        for t in tables:
            cols = conn.execute(f"PRAGMA table_info({t})").fetchall()
            count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"\n  TABLE: {t} ({count} rows)")
            for c in cols:
                print(f"    {c[1]}: {c[2]} {'PK' if c[5] else ''} {'NOT NULL' if c[3] else 'NULL'}")
        conn.close()
    except Exception as e:
        print(f"  Error: {e}")
PYEOF

# ════════════════════════════════════════════
# 3. DASHBOARD JSON FEEDS — Frontend data contracts
# ════════════════════════════════════════════

python3 << 'PYEOF'
import json, os, glob
feed_dir = 'dashboard/public/data'
for f in sorted(glob.glob(f'{feed_dir}/*.json')):
    try:
        with open(f) as fh:
            data = json.load(fh)
        name = os.path.basename(f)
        if isinstance(data, list) and data:
            sample = data[0]
            print(f"\n=== {name} ({len(data)} records) ===")
            if isinstance(sample, dict):
                for k, v in sorted(sample.items()):
                    vtype = type(v).__name__
                    preview = str(v)[:60].replace('\n',' ')
                    print(f"  {k}: {vtype} = {preview}")
        elif isinstance(data, dict):
            print(f"\n=== {name} (object) ===")
            for k, v in sorted(data.items()):
                vtype = type(v).__name__
                if isinstance(v, (list, dict)):
                    print(f"  {k}: {vtype} ({len(v)} items)")
                else:
                    print(f"  {k}: {vtype} = {str(v)[:60]}")
    except Exception as e:
        print(f"  {os.path.basename(f)}: Error - {e}")
PYEOF

# ════════════════════════════════════════════
# 4. DASHBOARD TYPESCRIPT INTERFACES
# ════════════════════════════════════════════

find dashboard/src -name "*.ts" -o -name "*.tsx" | xargs grep -l "^export interface\|^export type\|^interface " 2>/dev/null | while read f; do
    echo "=== $f ==="
    grep -A 20 "^export interface\|^export type\|^interface " "$f" 2>/dev/null
done

# Dashboard hooks (data fetching patterns)
for f in dashboard/src/hooks/*.ts dashboard/src/hooks/*.tsx; do
    [ -f "$f" ] && echo "=== $(basename $f) ===" && head -40 "$f"
done

# Dashboard services/stores
for f in dashboard/src/services/*.ts dashboard/src/stores/*.ts; do
    [ -f "$f" ] && echo "=== $(basename $f) ===" && head -60 "$f"
done

# ════════════════════════════════════════════
# 5. ENGINE PYDANTIC MODELS & DATA SCHEMAS
# ════════════════════════════════════════════

# Find ALL Pydantic BaseModel subclasses
find . -name "*.py" -not -path "./.git/*" -not -path "./*cache*" -not -path "*/node_modules/*" | \
  xargs grep -l "BaseModel\|dataclass\|TypedDict\|NamedTuple" 2>/dev/null | while read f; do
    echo "=== $f ==="
    grep -B1 -A30 "class.*BaseModel\|@dataclass\|class.*TypedDict\|class.*NamedTuple" "$f" 2>/dev/null
done

# ════════════════════════════════════════════
# 6. FASTAPI ENDPOINTS — Request/Response shapes
# ════════════════════════════════════════════

for f in api/*.py; do
    echo "=== $(basename $f) ==="
    grep -n "@.*\.get\|@.*\.post\|@.*\.put\|@.*\.delete\|response_model\|class.*Response\|class.*Request\|class.*Input\|class.*Output" "$f" 2>/dev/null
done

# Also check src/ for additional API modules
find src/ -name "*api*.py" -o -name "*route*.py" -o -name "*endpoint*.py" 2>/dev/null | while read f; do
    echo "=== $f ==="
    grep -n "@.*\.get\|@.*\.post\|response_model\|class.*Response" "$f" 2>/dev/null
done

# ════════════════════════════════════════════
# 7. AI AGENTS — Input/Output schemas
# ════════════════════════════════════════════

for f in Engine8_Knowledge/agents/*.py; do
    echo "=== $(basename $f) ==="
    head -80 "$f"
done

# ════════════════════════════════════════════
# 8. LANGGRAPH WORKFLOWS — State schemas
# ════════════════════════════════════════════

find src/langgraph/ -name "*.py" 2>/dev/null | while read f; do
    echo "=== $f ==="
    cat "$f" | head -120
done

# ════════════════════════════════════════════
# 9. ENGINE-SPECIFIC SCHEMAS
# ════════════════════════════════════════════

# Engine2 pipeline stages — job standardization schema
cat Engine2_ProgramMapping/scripts/job_standardizer.py 2>/dev/null | grep -A30 "class\|def.*standardize\|schema\|fields\|COLUMNS"

# Engine2 program mapper output schema
cat Engine2_ProgramMapping/scripts/program_mapper.py 2>/dev/null | grep -A30 "class\|def.*map\|COLUMNS\|output_fields"

# Engine3 contact classifier tiers
cat Engine3_OrgChart/scripts/contact_classifier.py 2>/dev/null | grep -A20 "TIER\|tier\|hierarchy\|classify"

# Engine5 BD scoring algorithm
cat Engine5_Scoring/scripts/bd_scoring.py 2>/dev/null | grep -A30 "class\|score\|weight\|boost\|SCORING"

# Engine4 briefing output formats
find Engine4_Briefing Engine4_Playbook -name "*.py" 2>/dev/null | while read f; do
    echo "=== $f ==="
    grep -A20 "class\|def.*generate\|output\|template" "$f"
done

# ════════════════════════════════════════════
# 10. CROSS-PROJECT DATA IMPORTS
# ════════════════════════════════════════════

echo "=== FROM DATA-SCRAPER ==="
ls -la data/from_data_scraper/ 2>/dev/null
for f in data/from_data_scraper/*.csv; do
    [ -f "$f" ] && echo "--- $(basename $f) ---" && head -1 "$f" && wc -l "$f"
done

echo "=== FROM N8N-BUILDER ==="
ls -la data/from_n8n_builder/ 2>/dev/null
for f in data/from_n8n_builder/*.csv; do
    [ -f "$f" ] && echo "--- $(basename $f) ---" && head -1 "$f" && wc -l "$f"
done

# ════════════════════════════════════════════
# 11. MCP SERVERS — Tool definitions
# ════════════════════════════════════════════

find mcp/ -name "*.ts" -o -name "*.js" -o -name "*.py" -o -name "*.json" 2>/dev/null | while read f; do
    echo "=== $f ==="
    head -80 "$f"
done

# ════════════════════════════════════════════
# 12. CONFIG & ENVIRONMENT
# ════════════════════════════════════════════

cat config/*.py config/*.yaml config/*.yml 2>/dev/null
find . -name ".env*" -maxdepth 2 2>/dev/null | while read f; do
    echo "=== $f ==="
    grep -v "KEY=\|SECRET=\|TOKEN=\|PASSWORD=" "$f" 2>/dev/null
done

# ════════════════════════════════════════════
# 13. NOTION EXPORT SCHEMAS
# ════════════════════════════════════════════

ls outputs/notion/ 2>/dev/null | head -10
for f in $(ls outputs/notion/*.csv 2>/dev/null | head -3); do
    echo "=== $(basename $f) ==="
    head -1 "$f"
    wc -l "$f"
done

# ════════════════════════════════════════════
# 14. KEY CSV HEADERS (engine_data/)
# ════════════════════════════════════════════

find engine_data/ -name "*.csv" 2>/dev/null | while read f; do
    echo "=== $f ==="
    head -1 "$f"
    wc -l "$f"
done
```

---

## KNOWN SCHEMA TO VERIFY (20 Node Types)

A previous audit documented these. For each, confirm properties exist in code:

| # | Node Type | Expected Props | Key Source Files |
|---|-----------|---------------|------------------|
| 1 | CONTACT | 36 | Engine3 contact_classifier.py, Engine7 bullhorn_etl.py |
| 2 | PROGRAM | 90+ | Engine2 program_mapper.py, engine_data/Engine2/*.csv |
| 3 | JOB | 60+ | Engine2 job_standardizer.py, Engine1 scraper configs |
| 4 | CONTRACTOR | 30+ | Engine3 Prime_Contacts/, Engine7 past_performance |
| 5 | LOCATION | 15+ | Engine3 location mappings, dashboard location_intelligence.json |
| 6 | CALL_NOTE | 20+ | Engine7 bullhorn_etl.py → bullhorn_master.db call_notes |
| 7 | PLACEMENT | 18+ | Engine7 bullhorn_master.db placements table |
| 8 | TECHNOLOGY | 8 | Engine2 TECHNOLOGIES dict in job_standardizer.py |
| 9 | CLEARANCE_LEVEL | 10 | Engine2/Engine3 clearance normalization |
| 10 | OPPORTUNITY | 15+ | Engine8 opportunities collection, Qdrant |
| 11 | CONTRACT_VEHICLE | 12 | engine_data/Engine2 Federal Programs CSVs |
| 12 | AGENCY | 10 | Derived from program/contract data |
| 13 | TEAM | 8 | Engine3 OrgChart team groupings |
| 14 | SKILL | 7 | Engine2 skills extraction from job descriptions |
| 15 | ENTITY | 8 | Engine8 knowledge graph entities (LightRAG) |
| 16 | PAST_PERFORMANCE | 15+ | Engine7 bullhorn_past_performance.db |
| 17 | BRIEFING | 10 | Engine4 briefing_generator.py output schema |
| 18 | GAP_ANALYSIS | 12 | Engine7 gap analysis scripts |
| 19 | NOTIFICATION | 8 | Engine6 QA alerts |
| 20 | MEMORY | 7 | Engine8 memory_system.py, bd_memories collection |

### Known Relationships (35+):
```
WORKS_FOR, WORKS_AT, MEMBER_OF, WORKS_ON, REPORTS_TO, KNOWS, MANAGES,
HIRED_FOR, PLACED_IN, HAS_CLEARANCE, HAS_SKILL, FAMILIAR_WITH,
DECISION_MAKER_FOR, INTERVIEWER_FOR, MENTIONED_IN, PRIMED_BY,
SUBCONTRACTED_TO, OWNED_BY, LOCATED_AT, USES_VEHICLE, HAS_JOB,
HAS_CONTACT, REQUIRES_SKILL, REQUIRES_TECHNOLOGY, REQUIRES_CLEARANCE,
RELATED_TO, HAS_PAST_PERFORMANCE, MATCHED_TO, POSTED_BY, ASSIGNED_TO,
HAS_BRIEFING, FILLED_BY, APPLIED_BY, PRIMES, EMPLOYS, OFFICES_AT,
ABOUT, DISCUSSES, MENTIONS, REFERENCES, CREATED_BY, FILLED,
CANDIDATE, FOR_PROGRAM, BY_CONTRACTOR, TARGETS, INVOLVES,
IDENTIFIED_IN, RECOMMENDS
```

---

## PRIORITY EXTRACTION TARGETS (What V2 Explorer is Missing)

1. **Qdrant payload schemas** for all 12 collections — field names, types, examples
2. **Bullhorn SQLite complete schema** — all tables, all columns, row counts
3. **Dashboard JSON feed field lists** — every field in every .json data file
4. **Dashboard TypeScript interfaces** — frontend type definitions
5. **FastAPI endpoint request/response shapes** — Pydantic models from api/*.py
6. **AI agent input/output schemas** — what each Engine8 agent produces
7. **LangGraph state definitions** — workflow state schemas
8. **Cross-project data flow schemas** — from_data_scraper/ and from_n8n_builder/ CSV headers
9. **Engine pipeline stage schemas** — what each pipeline stage produces/consumes
10. **MCP tool definitions** — tool names, parameters, return types

---

## OUTPUT FORMAT

Save as `data_architecture_bd_engine.json` with this structure:

```json
{
  "project_id": "BD_ENGINE",
  "scan_date": "2026-02-12",
  "scan_stats": { "files_scanned": 0, "entities_found": 0, "properties_found": 0, "relationships_found": 0, "aliases_found": 0, "data_flows_found": 0 },
  "entities": [],
  "relationships": [],
  "data_flows": [],
  "databases": {
    "qdrant_collections": [],
    "sqlite_tables": [],
    "dashboard_feeds": [],
    "api_endpoints": [],
    "notion_exports": []
  },
  "agents": [],
  "new_discoveries": "List anything found that ISN'T in the 20 known node types"
}
```

---

*Generated 2026-02-12 | PTS BD-Automation-Engine Architecture Extraction*
