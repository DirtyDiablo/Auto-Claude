# TERMINAL EXTRACTION QUICK REFERENCE CARDS

---

## TERMINAL 1: BD-AUTOMATION-ENGINE

**Project Path:** `bd-automation-engine/`  
**Output File:** `data_architecture_bd_engine.json`  
**Time:** 30-45 minutes  

### 🔴 CRITICAL (Must Get)
1. **Qdrant Collections** (12 total)
   - Collection names: (run `qdrant_client.scroll()` to sample)
   - Payload field list for each
   - Vector size, record count
   - Example payload values

2. **Bullhorn SQLite** (306MB)
   - All table names
   - All column names with types
   - Row count per table
   - Primary keys
   
3. **Dashboard JSON Feeds** (25 files)
   - Every field in `/dashboard/public/data/*.json`
   - Data types and examples
   - Which entities they represent

4. **FastAPI Endpoints** (152+)
   - Endpoint paths
   - Request Pydantic models
   - Response models
   - Query parameters

### 🟠 HIGH (Should Get)
5. **Engine Pipeline I/O** (Engines 1-8)
   - Input schema for each stage
   - Output schema for each stage
   - Transformation logic

6. **Dashboard TypeScript** (React interfaces)
   - All `export interface` definitions
   - All `export type` definitions
   - Component prop types

7. **AI Agents** (Engine8)
   - Agent names
   - Input/output schemas
   - Tools/capabilities

8. **LangGraph Workflows**
   - State definitions
   - Node types in graphs
   - State transitions

### 🟡 MEDIUM (Nice to Have)
9. MCP Tool definitions
10. Cross-project data flows

### Quick Commands
```bash
# Qdrant: If server running
python3 -c "from qdrant_client import QdrantClient; c = QdrantClient(host='localhost'); print([coll.name for coll in c.get_collections().collections])"

# Bullhorn: SQLite schema
python3 << 'EOF'
import sqlite3
for db in ['Engine7_BullhornETL/data/bullhorn_master.db', 'data/bullhorn_master.db']:
    try:
        conn = sqlite3.connect(db)
        for table in [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
            cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
            print(f"{table}: {[c[1] for c in cols]}")
        conn.close()
    except:
        pass
EOF

# Dashboard feeds
ls dashboard/public/data/*.json 2>/dev/null | while read f; do
    echo "$(basename $f): $(python3 -c "import json; d=json.load(open('$f')); print(list(d[0].keys()) if isinstance(d,list) and d else list(d.keys()))" 2>/dev/null)"
done

# FastAPI routes
grep -r "@.*\.get\|@.*\.post\|response_model" api/*.py 2>/dev/null | grep -o "response_model=.*\|@.*\.\(get\|post\)"
```

---

## TERMINAL 2: DATA-SCRAPER

**Project Path:** `data-scraper/`  
**Output File:** `data_architecture_data_scraper.json`  
**Time:** 30-45 minutes  

### 🔴 CRITICAL (Must Get)
1. **Tango API SQL Schemas** (11 SQL files)
   - Read: `TANGO API/database/*.sql`
   - Extract all CREATE TABLE statements
   - Every column definition
   - Foreign key relationships

2. **Pydantic Models** (models/ — 3 files)
   - All BaseModel classes
   - Every field with type
   - Validators
   - Defaults

3. **Scraper Output 64-Column Schema**
   - `scrapers/ig_job_parser.py` → column list
   - `scrapers/apex_job_parser.py` → column list
   - `scrapers/base_scraper.py` → shared structure

4. **Federal API Response Shapes**
   - Tango client actual responses
   - USASpending response fields
   - FPDS response fields
   - SAM.gov entity profiles

### 🟠 HIGH (Should Get)
5. **src/ Domain Models** (33 domains × ~10 files)
   - agents/ classes
   - enrichment/ classes
   - intelligence/ classes
   - knowledge/ classes
   - memory/ classes
   - ml/ classes
   - proposals/ classes
   - nlq/ classes
   - integrations/ classes
   - streaming/ classes

6. **Hub Client Sync Schema**
   - What gets POSTed to BD-Engine
   - Request body structure
   - Response handling

7. **BD Target Databases** (7 databases)
   - db1.csv column list
   - db2.csv column list
   - ... db7.csv columns
   - Record counts

8. **Knowledge Base Structure**
   - Company _manifest.json schema
   - Program folder schema
   - Index file structure

### 🟡 MEDIUM (Nice to Have)
9. Pipeline stage I/O schemas
10. Enrichment run outputs

### Quick Commands
```bash
# Tango SQL schemas
for f in "TANGO API/database/"*.sql; do
    echo "=== $(basename $f) ===" 
    grep "CREATE TABLE\|CREATE INDEX" "$f" | head -5
done

# Pydantic models
find models/ -name "*.py" -exec grep -H "class.*BaseModel" {} \;

# Scraper columns
grep -A 100 "^COLUMNS\|^columns\|^headers\|^fields" scrapers/ig_job_parser.py | head -80
grep -A 100 "^COLUMNS\|^columns\|^headers\|^fields" scrapers/apex_job_parser.py | head -80

# Hub sync
cat hub/*.py | grep -A 20 "def.*sync\|class.*Request\|class.*Response"

# BD target DB columns
for f in data/output/bd_databases/db*.csv; do
    echo "$(basename $f): $(head -1 $f | tr ',' '\n' | wc -l) columns"
    head -1 "$f"
done
```

---

## TERMINAL 3: N8N-BUILDER

**Project Path:** `n8n-builder/`  
**Output File:** `data_architecture_n8n_builder.json`  
**Time:** 20-30 minutes  

### 🔴 CRITICAL (Must Get)
1. **N8N Workflow Node Definitions** (50+ workflows)
   - Find all `*.n8n.json` files
   - Extract nodes array
   - For each node: name, type, parameters
   - Node connections (data flow)

2. **API Integration Nodes** (HTTP requests)
   - Bullhorn calls (auth, endpoints, fields)
   - Notion calls (databases, operations, fields)
   - ZoomInfo calls (endpoints, response fields)
   - Apify calls (actor, output fields)
   - SAM.gov calls

3. **Contact Enrichment Output Schema**
   - Find contact enrichment workflows
   - Extract final field list
   - Map source of each field (ZoomInfo, Bullhorn, Notion, Calculated)

4. **Code Node Transformations**
   - JavaScript code nodes (data transforms)
   - Python code nodes (data transforms)
   - Output shapes after transformation

### 🟠 HIGH (Should Get)
5. **Notion Database Operations**
   - Which databases (with collection IDs)
   - What CRUD operations per database
   - Which fields are touched
   - Sync patterns

6. **Webhook Trigger Schemas**
   - Webhook paths
   - Event payload structure
   - What workflow it triggers
   - Data fields expected

7. **API Integration Patterns**
   - Auth methods used
   - Request/response mapping patterns
   - Error handling
   - Rate limiting

8. **Data Flow Diagrams**
   - Node→node connections
   - Data transformations at each step
   - Conditional branches

### 🟡 MEDIUM (Nice to Have)
9. Field mapping standards
10. Enrichment process documentation

### Quick Commands
```bash
# Find all n8n workflows
find . -name "*.n8n.json" | wc -l

# Extract workflow structure
python3 << 'EOF'
import json, glob
for f in glob.glob("**/*.n8n.json", recursive=True)[:3]:
    with open(f) as fh:
        wf = json.load(fh)
    print(f"\n{f.split('/')[-1]}")
    print(f"  Nodes: {len(wf.get('nodes', []))}")
    for node in wf.get('nodes', [])[:3]:
        print(f"    - {node.get('name')}: {node.get('type')}")
EOF

# Find Notion operations
grep -r "notion" . --include="*.json" | grep -i "database\|collection\|properties" | head -10

# Find HTTP request nodes
python3 << 'EOF'
import json, glob
for f in glob.glob("**/*.n8n.json", recursive=True):
    with open(f) as fh:
        wf = json.load(fh)
    for node in wf.get('nodes', []):
        if node.get('type') == 'n8n-nodes-base.httpRequest':
            url = node.get('parameters', {}).get('url', '')
            if 'bullhorn' in url.lower() or 'notion' in url.lower():
                print(f"{f}: {node.get('name')} -> {url}")
EOF

# Extract contact enrichment fields
find . -name "*contact*" -name "*.json" -o -name "*enrichment*" -name "*.json" | head -5
```

---

## GENERAL EXTRACTION WORKFLOW (All Terminals)

### Phase 1: Discovery (5-10 min)
1. Identify key directories
2. List major files
3. Count entities to extract
4. Assess scope

### Phase 2: Targeted Extraction (15-30 min)
1. Extract entities (classes, tables, APIs)
2. Extract properties (fields, columns, parameters)
3. Extract relationships (FKs, connections, flows)
4. Extract aliases (field name variations)

### Phase 3: Validation (5-10 min)
1. Spot-check: Do entities have required fields?
2. Spot-check: Do properties have sources?
3. Count totals: entities, properties, relationships
4. Document new discoveries

### Phase 4: JSON Generation (5 min)
1. Populate standard JSON structure
2. Double-check format
3. Save as `data_architecture_<PROJECT>.json`

---

## TROUBLESHOOTING

### "I can't find X in the code"
- Check project structure: `ls -la`
- Search broadly: `find . -name "*x*" -o -name "*X*"`
- Check if it's in a different location than expected
- Document as "not found" vs "missing"

### "The file is too large to read"
- Use `head -N file` to sample
- Use `grep` to extract specific patterns
- Use Python to parse and summarize
- Extract in chunks

### "I found an entity but missing properties"
- Check all source files for that entity
- Look for related classes that inherit from it
- Search for any initialization code
- Document what you found + what's missing

### "Two projects seem to define the same entity differently"
- This is expected! Note both definitions
- Document which project's version is "authoritative"
- These become "aliases" in the merged JSON

---

## SUCCESS CHECKLIST

Before submitting, verify:

**Terminal 1 (BD-Engine):**
- [ ] 12 Qdrant collections documented with payload fields
- [ ] All Bullhorn tables and columns listed
- [ ] Dashboard JSON feeds complete
- [ ] FastAPI endpoints with request/response models
- [ ] 20 known entities verified + any new ones found
- [ ] 35+ relationships documented

**Terminal 2 (Data-Scraper):**
- [ ] Tango API SQL schemas fully extracted
- [ ] 3 Pydantic models in models/ complete
- [ ] Scraper 64-column schema documented
- [ ] Federal API response shapes captured
- [ ] Key src/ domains sampled (agents, enrichment, intelligence, knowledge)
- [ ] Hub client sync schema defined

**Terminal 3 (N8N-Builder):**
- [ ] All n8n workflows identified
- [ ] Workflow node types and parameters documented
- [ ] API integration patterns captured (Bullhorn, Notion, ZoomInfo, etc.)
- [ ] Contact enrichment output schema complete
- [ ] Webhook triggers and payloads documented
- [ ] Notion database operations mapped

---

## FINAL NOTE

Remember:
- **Be precise** — Extract what actually exists, not what you think should exist
- **Be complete** — Don't leave gaps, note when you can't find something
- **Be thorough** — One pass is better than many partial attempts
- **Be clear** — Every property should have a source and purpose

The merged V3 explorer will be the single source of truth for PTS data architecture. Quality input = Quality visualization.

---

*Quick Reference Generated 2026-02-12 | Use with Terminal Extraction Prompts*
