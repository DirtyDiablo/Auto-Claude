# PTS BD Platform — Project Knowledge Update Package
## February 7, 2026

---

# PART 1: TERMINAL AUDIT PROMPTS

Run these FIRST on each terminal. The outputs from these audits will validate and update the project knowledge documents below.

---

## TERMINAL A AUDIT — Copy/Paste This:

```
FULL CAPABILITIES & STATE AUDIT — BD-Automation-Engine (Hub)

Output a structured report in this EXACT format. Do not skip any section. Be exhaustive.

═══ SECTION 1: PROJECT METADATA ═══
- Git remote URL:
- Current branch:
- Last commit hash + message + date:
- Total files: (find . -type f | wc -l)
- Total Python files: (find . -name "*.py" | wc -l)
- Total JS/TS files: (find . -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" | wc -l)
- Disk size: (du -sh .)
- .env exists: yes/no
- .env in .gitignore: yes/no
- requirements.txt exists: yes/no
- package.json exists: yes/no (and where)

═══ SECTION 2: QDRANT STATE ═══
Run this and paste the FULL output:
```bash
python -c "
from qdrant_client import QdrantClient
c = QdrantClient(host='localhost', port=6333)
for col in c.get_collections().collections:
    info = c.get_collection(col.name)
    print(f'{col.name}: {info.points_count} vectors, dim={info.config.params.vectors.size if hasattr(info.config.params.vectors, \"size\") else \"multi\"}, status={info.status}')
    # List payload indexes
    if hasattr(info, 'payload_schema') and info.payload_schema:
        for key, schema in info.payload_schema.items():
            print(f'  index: {key} ({schema.data_type})')
print(f'TOTAL VECTORS: {sum(c.get_collection(col.name).points_count for col in c.get_collections().collections)}')
"
```

═══ SECTION 3: API ENDPOINTS ═══
List ALL registered FastAPI routes:
```bash
python -c "
import sys; sys.path.insert(0, '.')
from Engine8_Knowledge.api import app
for route in app.routes:
    if hasattr(route, 'methods'):
        for method in route.methods:
            print(f'{method:6} {route.path}')
" 2>/dev/null | sort
```

If that fails, try:
```bash
grep -rn "@app\.\(get\|post\|put\|patch\|delete\)" Engine8_Knowledge/ --include="*.py" | head -80
```

═══ SECTION 4: CREWAI AGENTS ═══
List all CrewAI agent definitions:
```bash
grep -rn "Agent(" Engine8_Knowledge/agents/ --include="*.py" -A 5 | head -100
```

List all Pydantic output models:
```bash
grep -rn "class.*BaseModel" Engine8_Knowledge/agents/ --include="*.py"
```

═══ SECTION 5: INSTALLED PYTHON PACKAGES ═══
```bash
pip list 2>/dev/null | grep -iE "crewai|qdrant|mem0|graphiti|neo4j|openai|anthropic|langchain|langraph|fastapi|uvicorn|docling|tenacity|structlog|pydantic|numpy|pandas|openpyxl|python-docx|httpx|requests|apify|beautifulsoup|selenium|playwright"
```

═══ SECTION 6: FRONTEND STATE ═══
Find the React/Vite frontend and report:
```bash
# Find package.json files
find . -name "package.json" -not -path "*/node_modules/*" | head -5

# For each, list key deps
for pkg in $(find . -name "package.json" -not -path "*/node_modules/*" | head -3); do
  echo "=== $pkg ==="
  cat $pkg | python -c "import sys,json; d=json.load(sys.stdin); [print(f'  {k}: {v}') for k,v in {**d.get('dependencies',{}), **d.get('devDependencies',{})}.items()]" 2>/dev/null
done
```

═══ SECTION 7: NEO4J STATE ═══
```bash
python -c "
from neo4j import GraphDatabase
d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
with d.session() as s:
    nodes = s.run('MATCH (n) RETURN count(n) as c').single()['c']
    rels = s.run('MATCH ()-[r]->() RETURN count(r) as c').single()['c']
    labels = s.run('CALL db.labels() YIELD label RETURN collect(label) as labels').single()['labels']
    rel_types = s.run('CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types').single()['types']
    print(f'Nodes: {nodes}')
    print(f'Relationships: {rels}')
    print(f'Labels: {labels}')
    print(f'Relationship types: {rel_types}')
d.close()
" 2>/dev/null || echo "Neo4j not accessible"
```

═══ SECTION 8: MEM0 STATE ═══
```bash
python -c "
from qdrant_client import QdrantClient
c = QdrantClient(host='localhost', port=6333)
try:
    info = c.get_collection('bd_memories')
    print(f'bd_memories: {info.points_count} vectors')
    # Sample a memory
    results = c.scroll('bd_memories', limit=3)
    for point in results[0]:
        print(f'  Memory: {str(point.payload)[:200]}')
except: print('bd_memories collection not found')
"
```

═══ SECTION 9: DIRECTORY STRUCTURE ═══
```bash
# Top-level structure (2 levels)
find . -maxdepth 2 -type d -not -path "*/node_modules/*" -not -path "*/__pycache__/*" -not -path "*/.git/*" | sort

# Engine directories specifically
ls -la Engine*/  2>/dev/null
```

═══ SECTION 10: DOCKER SERVICES ═══
```bash
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker not running or not accessible"
```

═══ SECTION 11: ACTIVE PORTS ═══
```bash
netstat -tlnp 2>/dev/null | grep -E "8100|6333|7687|7474|5173|3000" || echo "netstat not available"
```

═══ END OF AUDIT ═══
Save this full report as: docs/TERMINAL_A_AUDIT_20260207.md
Then commit: git add docs/ && git commit -m "audit: Terminal A capabilities and state report Feb 7 2026"
```

---

## TERMINAL B AUDIT — Copy/Paste This:

```
FULL CAPABILITIES & STATE AUDIT — Data-Scraper

Output a structured report in this EXACT format. Be exhaustive.

═══ SECTION 1: PROJECT METADATA ═══
- Git remote URL:
- Current branch:
- Last commit hash + message + date:
- Total files: (find . -type f | wc -l)
- Total Python files: (find . -name "*.py" | wc -l)
- Disk size: (du -sh .)
- .env exists: yes/no
- .env in .gitignore: yes/no
- requirements.txt exists: yes/no

═══ SECTION 2: SCRAPER INVENTORY ═══
List ALL scraper scripts and their targets:
```bash
find . -name "*.py" -path "*/scraper*" -o -name "*.py" -path "*/scrape*" | sort
grep -rn "apify\|puppeteer\|selenium\|playwright\|requests.get\|httpx.get" --include="*.py" -l | sort | uniq
```

For each scraper, identify:
- Target website/portal
- Method (Apify actor, Puppeteer, requests, etc.)
- Last successful run date (check logs/ or data/ directories)
- Output format (CSV, JSON, etc.)

═══ SECTION 3: APIFY CONFIGURATION ═══
```bash
# Find Apify configs
grep -rn "APIFY\|apify_client\|ApifyClient" --include="*.py" | head -30

# Check actor IDs
grep -rn "actor_id\|run_actor" --include="*.py" | head -20

# Check for scheduled runs
find . -name "*.json" -path "*apify*" | head -10
```

═══ SECTION 4: DATA FILES INVENTORY ═══
```bash
# All CSV files with row counts
for f in $(find . -name "*.csv" -not -path "*/node_modules/*" | sort); do
  rows=$(wc -l < "$f")
  size=$(du -h "$f" | cut -f1)
  echo "$size  $rows rows  $f"
done

# All JSON data files
find . -name "*.json" -not -path "*/node_modules/*" -not -name "package*.json" -not -name "tsconfig*" | sort

# All Excel files
find . -name "*.xlsx" -o -name "*.xls" | sort
```

═══ SECTION 5: FEDERAL API CLIENTS ═══
```bash
# Find all API client implementations
grep -rn "sam.gov\|fpds\|usaspending\|tango\|makegov\|govwin" --include="*.py" -l | sort
```

For each found:
- API name
- Base URL
- Auth method (API key, OAuth, none)
- Key configured in .env? (yes/no)

═══ SECTION 6: HUB CONNECTIVITY ═══
```bash
# Check if Hub client exists
grep -rn "localhost:8100\|HUB_BASE_URL\|hub_client" --include="*.py" | head -20

# Test Hub connection
python -c "import httpx; r=httpx.get('http://localhost:8100/health'); print(r.json())" 2>/dev/null || echo "Hub not reachable"
```

═══ SECTION 7: QDRANT CONNECTIVITY ═══
```bash
python -c "
from qdrant_client import QdrantClient
c = QdrantClient(host='localhost', port=6333)
for col in c.get_collections().collections:
    info = c.get_collection(col.name)
    print(f'{col.name}: {info.points_count} vectors')
" 2>/dev/null || echo "Qdrant not reachable from this terminal"
```

═══ SECTION 8: INSTALLED PACKAGES ═══
```bash
pip list 2>/dev/null | grep -iE "qdrant|apify|httpx|requests|pandas|openai|anthropic|beautifulsoup|selenium|playwright|scrapy|tenacity|fastapi|chromadb|lancedb"
```

═══ SECTION 9: BULLHORN DATA ═══
```bash
# Find Bullhorn exports/data
find . -name "*bullhorn*" -o -name "*Bullhorn*" | sort
# Check sizes
for f in $(find . -name "*bullhorn*" -o -name "*Bullhorn*" 2>/dev/null); do
  du -h "$f"
done
```

═══ SECTION 10: N8N DEPENDENCIES — REMOVAL AUDIT ═══
```bash
# Find ALL references to n8n in this project
grep -rn "n8n\|N8N\|webhook" --include="*.py" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.env" | grep -iv "n8n-builder\|n8n_builder\|N8N-Builder\|N8N_Builder" | head -30

# Check if n8n is used as a runtime dependency
grep -rn "n8n" requirements.txt setup.py pyproject.toml package.json 2>/dev/null
```

Report: Which features depend on n8n webhooks vs which are pure Python?

═══ SECTION 11: DIRECTORY STRUCTURE ═══
```bash
find . -maxdepth 2 -type d -not -path "*/node_modules/*" -not -path "*/__pycache__/*" -not -path "*/.git/*" | sort
```

═══ END OF AUDIT ═══
Save as: docs/TERMINAL_B_AUDIT_20260207.md
Commit: git add docs/ && git commit -m "audit: Terminal B capabilities and state report Feb 7 2026"
```

---

## TERMINAL C AUDIT — Copy/Paste This:

```
FULL CAPABILITIES & STATE AUDIT — N8N-Builder (Workflow & Intelligence Engine)

NOTE: This project is being renamed from "N8N-Builder" to reflect its broader capabilities. 
The n8n runtime dependency is being REMOVED. Document what depends on n8n vs what is pure Python.

═══ SECTION 1: PROJECT METADATA ═══
- Git remote URL:
- Current branch:
- Last commit hash + message + date:
- Total files: (find . -type f | wc -l)
- Total Python files: (find . -name "*.py" | wc -l)
- Disk size: (du -sh .)
- .env exists: yes/no
- .env in .gitignore: yes/no

═══ SECTION 2: N8N DEPENDENCY AUDIT (CRITICAL) ═══
```bash
# Find ALL n8n references
echo "=== Direct n8n imports/calls ==="
grep -rn "import.*n8n\|from.*n8n\|n8n_client\|n8n_api\|n8n.cloud\|webhook.*n8n" --include="*.py" | head -30

echo "=== Webhook URLs (n8n endpoints) ==="
grep -rn "webhook\|n8n.*url\|N8N.*URL\|n8n.*endpoint" --include="*.py" --include="*.env" --include="*.json" | head -30

echo "=== n8n workflow references ==="
grep -rn "workflow_id\|execution_id\|n8n.*trigger" --include="*.py" | head -20

echo "=== Pure Python alternatives already exist? ==="
find . -name "*.py" -path "*/outreach*" -o -name "*.py" -path "*/sequence*" -o -name "*.py" -path "*/workflow*" | sort
```

Categorize EVERY feature into:
1. PURE PYTHON (no n8n dependency) — keep as-is
2. N8N WEBHOOK DEPENDENT — needs Python replacement
3. N8N UI DEPENDENT — needs dashboard replacement

═══ SECTION 3: LANGGRAPH WORKFLOWS ═══
```bash
# Find all LangGraph workflow definitions
find . -name "*.py" -path "*langgraph*" -o -name "*.py" -path "*graph*" | sort
grep -rn "StateGraph\|CompiledGraph\|add_node\|add_edge" --include="*.py" | head -30

# Document each workflow
for f in $(find . -name "*.py" -path "*langgraph*" -o -name "*.py" -path "*workflow*" 2>/dev/null); do
  echo "=== $f ==="
  grep -n "class\|def \|StateGraph\|add_node" "$f" | head -15
done
```

═══ SECTION 4: DISCOVERY ENGINES ═══
```bash
find . -name "*.py" -path "*discovery*" -o -name "*.py" -path "*discover*" | sort
# For each, show what it discovers and what APIs it calls
for f in $(find . -name "*.py" -path "*discovery*" 2>/dev/null); do
  echo "=== $f ==="
  grep -n "def \|class \|requests\|httpx\|tango\|sam.gov\|fpds" "$f" | head -15
done
```

═══ SECTION 5: TANGO/MAKEGOV CLIENT ═══
```bash
find . -name "*tango*" -o -name "*makegov*" | sort
# Check Tango API key status
grep -n "TANGO\|MAKEGOV" .env 2>/dev/null | head -5
# Show Tango client capabilities
grep -n "def " src/api_clients/tango.py 2>/dev/null | head -20
```

═══ SECTION 6: ENRICHMENT PIPELINES ═══
```bash
find . -name "*.py" -path "*enrich*" | sort
# Show enrichment pipeline stages
for f in $(find . -name "*.py" -path "*enrich*" 2>/dev/null); do
  echo "=== $f ==="
  grep -n "def \|Phase\|Step\|stage" "$f" | head -15
done
```

═══ SECTION 7: OUTREACH ENGINE ═══
```bash
# Check if sequence_engine.py was created from previous prompt
find . -name "*sequence*" -o -name "*outreach*" | sort
# Show its state
python -c "
import sqlite3, os
for db in ['data/outreach_sequences.db', 'outreach_sequences.db']:
    if os.path.exists(db):
        conn = sqlite3.connect(db)
        tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
        print(f'{db}: tables={[t[0] for t in tables]}')
        for t in tables:
            count = conn.execute(f'SELECT count(*) FROM {t[0]}').fetchone()[0]
            print(f'  {t[0]}: {count} rows')
        conn.close()
" 2>/dev/null || echo "No outreach DB found"
```

═══ SECTION 8: CONTACT PROCESSING ═══
```bash
# Find contact processing scripts
grep -rn "zoominfo\|linkedin\|bullhorn\|contact.*process\|contact.*import" --include="*.py" -l | sort

# Check LanceDB state (may be migrated to Qdrant)
python -c "
try:
    import lancedb
    db = lancedb.connect('./lancedb')
    for name in db.table_names():
        t = db.open_table(name)
        print(f'{name}: {t.count_rows()} rows')
except: print('LanceDB not found or empty')
" 2>/dev/null
```

═══ SECTION 9: INSTALLED PACKAGES ═══
```bash
pip list 2>/dev/null | grep -iE "langgraph|langchain|qdrant|neo4j|mem0|graphiti|tango|openai|anthropic|fastapi|lancedb|tenacity|httpx|requests|apify"
```

═══ SECTION 10: HUB CONNECTIVITY ═══
```bash
python -c "import httpx; r=httpx.get('http://localhost:8100/health'); print(r.json())" 2>/dev/null || echo "Hub not reachable"
python -c "import httpx; r=httpx.get('http://localhost:6333/collections'); print(r.json()['result']['collections'][:3])" 2>/dev/null || echo "Qdrant not reachable"
```

═══ SECTION 11: DIRECTORY STRUCTURE ═══
```bash
find . -maxdepth 2 -type d -not -path "*/node_modules/*" -not -path "*/__pycache__/*" -not -path "*/.git/*" | sort
```

═══ END OF AUDIT ═══
Save as: docs/TERMINAL_C_AUDIT_20260207.md
Commit: git add docs/ && git commit -m "audit: Terminal C capabilities and state report Feb 7 2026"
```

---
---

# PART 2: PROJECT KNOWLEDGE DOCUMENTS

These 4 documents replace the existing project knowledge. Upload them to the Claude Project after running the terminal audits and updating any values that changed.

---

## DOCUMENT 1: Architecture State — Current as of Feb 7, 2026

Save as: `01_ARCHITECTURE_STATE.md`

```markdown
# PTS BD Platform — Architecture State
## Last Updated: February 7, 2026 (Post-V4 Phase 4D Completion)

---

## Platform Overview

Prime Technical Services (PTS) BD Intelligence Platform is a hub-and-spoke architecture across 3 projects, powered by a unified Qdrant vector database (1.4M+ vectors), 5 CrewAI agents with structured outputs, dual-memory architecture (Mem0 vector + Graphiti temporal graph on Neo4j), and a React 19 dashboard frontend.

**Primary Objective**: Transform manual BD analysis (8-15 hours) into AI-powered sub-10-minute workflows for identifying federal defense staffing opportunities, building contact intelligence, and generating personalized outreach.

**Target Market**: Thousands of federal defense contracts matching: subcontracting staffing firms, $100M+ value or 100+ subs, clearance required, not assigned to existing PTS account managers

---

## Hub-and-Spoke Architecture

```
                    ┌─────────────────────────────────┐
                    │   BD-Automation-Engine (HUB)    │
                    │   Port: 8100                     │
                    │   FastAPI + React Dashboard      │
                    │   CrewAI Agents + Mem0 + Graphiti│
                    │   Qdrant (1.4M vectors)          │
                    │   Neo4j (Graphiti KG)            │
                    └──────────┬──────────┬───────────┘
                               │          │
              ┌────────────────┘          └────────────────┐
              ▼                                            ▼
┌──────────────────────────┐          ┌──────────────────────────────┐
│   Data-Scraper           │          │   N8N-Builder                │
│   Port: 8200             │          │   (Workflow & Intel Engine)  │
│   Apify job scrapers     │          │   Port: 8300                 │
│   Federal API clients    │          │   LangGraph workflows        │
│   Bullhorn CRM sync      │          │   Tango/MakeGov discovery    │
│   Job enrichment pipeline│          │   Outreach sequence engine   │
│   Competitor intelligence│          │   Contact processing         │
└──────────────────────────┘          └──────────────────────────────┘
```

### Terminal A — BD-Automation-Engine (Hub)
- **Path**: `C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine\`
- **Role**: Central API server, dashboard frontend, AI agents, vector search, memory systems
- **Port**: 8100 (FastAPI API)
- **Key Technologies**: FastAPI, React 19, Vite 7, shadcn/ui, TanStack Query, CrewAI 1.9.3, Qdrant, Neo4j, Mem0, Graphiti, cross-encoder reranking
- **Engines**: 8 engines (Engine1-Engine8_Knowledge) covering scraping → standardization → mapping → scoring → outreach → QA → knowledge

### Terminal B — Data-Scraper
- **Path**: `C:\data-scraper\data-scraper\`
- **Role**: Job scraping from competitor portals, federal contract API integration, Bullhorn data processing
- **Port**: 8200 (FastAPI, if running)
- **Key Technologies**: Apify Puppeteer scrapers, httpx, pandas, Qdrant client
- **Scrapers**: Insight Global (reliable), Apex Systems (403 blocked), TEKsystems (configured, no data), CACI (configured, no data)

### Terminal C — N8N-Builder (Workflow & Intelligence Engine)
- **Path**: `C:\Auto-Claud\N8N-Builder\` ⚠️ Note: "Claud" not "Claude"
- **Role**: LangGraph workflows, Tango federal contract discovery, outreach sequence engine, contact processing
- **Port**: 8300 (FastAPI, if running)
- **Key Technologies**: LangGraph (12 modules), Tango/MakeGov API, LanceDB (partially migrated), SQLite outreach DB
- **NOTE**: n8n runtime dependency is being REMOVED. All automation migrating to Python-native implementations.

---

## Data Infrastructure

### Qdrant Vector Database (localhost:6333)

| Collection | Vectors | Dimension | Key Payload Indexes | Purpose |
|---|---|---|---|---|
| documents | 499,750 | 1536 | source_project, intel_category, search_tags, priority, doc_type, program_name, date_indexed | BD documents, playbooks, reports, analysis |
| activities | 445,972 | 1536 | source_project, activity_type, contact_name, company, date, program | Bullhorn activity records, call notes, emails |
| contacts | 211,267 | 1536 | name, company, title, program, tier, priority, location, email | Contact profiles from ZoomInfo, LinkedIn, Bullhorn |
| federal_contracts | 107,902 | 1536 | agency, contractor, naics, value, status, award_date | USASpending, FPDS, SAM.gov contract data |
| programs | 68,103 | 1536 | program_name, agency, prime, pts_involvement, priority, contract_value | Federal program intelligence |
| bullhorn_notes | 50,710 | 1536 | contact, company, author, date, type, programs_mentioned | Extracted Bullhorn CRM notes (2,687 source notes) |
| jobs | 15,997 | 1536 | company, title, location, clearance, program_match, source_portal, scraped_date | Scraped competitor jobs + GDIT internal |
| intelligence_reports | 2,229 | 1536 | report_type, program, date, confidence | BD intelligence, HUMINT, competitive analysis, gap analysis |
| bd_memories | 2 | 1536 | user_id, agent_id, memory_type, timestamp | Mem0 agent cross-session memory |

**Embedding Model**: OpenAI text-embedding-3-small (1536 dimensions) — consistent across ALL collections
**Quantization**: INT8 scalar (75% RAM reduction, <1% accuracy loss)
**HNSW**: m=16, ef_construct=100

### Neo4j Graph Database (localhost:7687)

- **Nodes**: ~7 (growing as Graphiti ingests more episodes)
- **Relationships**: ~4 types
- **Labels**: [To be confirmed by audit]
- **Relationship Types**: [To be confirmed by audit]
- **Purpose**: Graphiti temporal knowledge graph — tracks how entity relationships change over time
- **Auth**: neo4j / password (confirm via audit)

### Mem0 Memory System

- **Vector Backend**: Qdrant `bd_memories` collection
- **Graph Backend**: Neo4j (same instance as Graphiti)
- **Current Memories**: 2 (from end-to-end agent test)
- **Growth**: Automatically stores memories when CrewAI agents complete tasks
- **Use Case**: Cross-session agent memory — agents remember past research, contact interactions, and program intelligence

---

## AI Agent System

### CrewAI 1.9.3 — 5 Specialized Agents

| Agent | LLM | Tools | Structured Output Model | Purpose |
|---|---|---|---|---|
| program_researcher | GPT-4o | Qdrant search (programs, contracts, documents), Graphiti search | ProgramIntelligence | Deep program research — contract details, pain points, competitive landscape |
| contact_enricher | GPT-4o-mini | Qdrant search (contacts, bullhorn_notes), Mem0 memory, Graphiti | ContactProfile | Contact intelligence enrichment — interaction history, HUMINT, relationship mapping |
| competitive_analyst | GPT-4o | Qdrant search (jobs, documents, programs) | CompetitiveReport | Competitive landscape analysis — competitor staffing patterns, labor gaps |
| outreach_composer | GPT-4o | Qdrant search (contacts, programs, jobs), Mem0 memory | OutreachPlan | Personalized outreach generation following 6-step BD Formula |
| humint_analyst | GPT-4o | Qdrant search (bullhorn_notes, contacts), Mem0, Graphiti | HUMINTBrief | Human intelligence synthesis — aggregate HUMINT across sources |

### Agent Crews (Sequential Pipelines)

| Crew | Agents | Tasks | Output |
|---|---|---|---|
| BD Research Crew | program_researcher → contact_enricher → competitive_analyst → outreach_composer → [synthesis] | 5 sequential tasks | BDResearchBundle (all intermediate results preserved) |
| Weekly Intel Crew | competitive_analyst → humint_analyst → [synthesis] | 3 sequential tasks | WeeklyIntelBundle |

### Agent API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| /agents/research | POST | Trigger BD Research Crew for a program |
| /agents/outreach | POST | Trigger outreach generation for a contact |
| /agents/weekly-intel | POST | Trigger weekly intelligence briefing |
| /agents/tasks | GET | List all agent task history |
| /agents/status/{task_id} | GET | Get status of specific task |

---

## Search Architecture

### Hybrid Search Pipeline

1. **Query Router**: Classifies query intent → selects target collections
2. **Dense Vector Search**: OpenAI embeddings → Qdrant cosine similarity
3. **Sparse BM25 Search**: Keyword matching (Qdrant native)
4. **Cross-Encoder Reranking**: ms-marco-MiniLM-L-6-v2 (22.7M params) — 20-35% accuracy improvement
5. **LLM Synthesis**: Claude/GPT generates natural language answer with citations

### Key Search Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| /search | POST | Vector search with optional collection filter + payload filters |
| /ask/smart | POST | Full AI-synthesized answer with citation |
| /collections/{name}/search | POST | Collection-specific search |

---

## External Integrations

| Service | Status | Purpose | Terminal |
|---|---|---|---|
| Qdrant | ✅ Running | Vector database (1.4M vectors) | A (primary), B+C (clients) |
| Neo4j | ✅ Running | Graphiti temporal knowledge graph | A (primary) |
| OpenAI API | ✅ Configured | Embeddings (text-embedding-3-small) + Agent LLMs (GPT-4o/mini) | A |
| Anthropic API | ✅ Configured | RAG synthesis (Claude Sonnet 4) | A |
| Apify | ✅ Configured | Job scraping actors | B |
| Tango/MakeGov | ✅ Configured | Federal contract discovery API (unlimited) | C |
| Notion | ✅ Configured | DCGS Contacts, Jobs, Programs databases (MCP) | A |
| Apollo.io | ⏳ Not set up | Contact discovery (275M contacts) | A |
| Azure AD / O365 | ⏳ Not set up | Email automation via Graph API | A |
| Twilio | ⏳ Not set up | SMS outreach automation | C |

---

## Notion Databases (MCP Access)

| Database | Collection ID | Records | Purpose |
|---|---|---|---|
| DCGS Contacts Full | 2ccdef65-baa5-8087-a53b-000ba596128e | ~965 | Primary BD contact database |
| GDIT Other Contacts | 70ea1c94-211d-40e6-a994-e8d7c4807434 | ~1,052 | Non-DCGS GDIT personnel |
| GDIT Jobs | 2ccdef65-baa5-80b0-9a80-000bd2745f63 | ~700 | Current Bullhorn job openings |
| Program Mapping Hub | f57792c1-605b-424c-8830-23ab41c47137 | varies | Scraped jobs with BD scoring |
| Federal Programs | 06cd9b22-5d6b-4d37-b0d3-ba99da4971fa | 388 | Contract intelligence |
| Contractors | 3a259041-22bf-4262-a94a-7d33467a1752 | varies | Contractor profiles |
| Contract Vehicles | 0f09543e-9932-44f2-b0ab-7b4c070afb81 | varies | Vehicle/IDIQ tracking |
| Enrichment Runs Log | 20dca021-f026-42a5-aaf7-2b1c87c4a13d | varies | Processing audit trail |
```

---

## DOCUMENT 2: Terminal Prompt Patterns

Save as: `02_TERMINAL_PROMPT_PATTERNS.md`

```markdown
# Terminal Prompt Patterns — Phase Summary Feedback Loop
## Last Updated: February 7, 2026

---

## Pattern: Phase Summary → Next Phase Handoff

Every terminal prompt phase MUST end with a structured summary that feeds into the next phase or back to the orchestrating Claude session. This ensures continuity across chat sessions and prevents knowledge loss.

### Required Phase Completion Output

At the end of EVERY phase, the terminal must output this EXACT structure:

```
═══ PHASE COMPLETION SUMMARY ═══
Terminal: [A/B/C]
Phase: [Phase Name]  
Duration: [X minutes]
Status: [COMPLETE / PARTIAL / BLOCKED]

COMPLETED:
- [Specific deliverable 1 with verification]
- [Specific deliverable 2 with verification]

FAILED/SKIPPED:
- [Item] — Reason: [why]

STATE CHANGES:
- [What changed in the system — new files, new endpoints, new collections, config changes]
- Qdrant vectors: [before] → [after]  
- API endpoints added: [list]
- Files created: [list]
- Files modified: [list]

BLOCKERS FOR NEXT PHASE:
- [Any dependency on other terminals]
- [Any missing config/keys]

NEXT PHASE READY: [YES/NO]

PASTE THIS INTO CLAUDE ORCHESTRATOR:
[One-paragraph natural language summary suitable for pasting into the orchestrating Claude chat to update context]
═══ END SUMMARY ═══
```

### How to Use the Feedback Loop

1. Paste terminal prompt into Auto-Claude terminal
2. Terminal executes the phase
3. Terminal outputs the Phase Completion Summary
4. Copy the "PASTE THIS INTO CLAUDE ORCHESTRATOR" paragraph
5. Paste it into your orchestrating Claude chat (this project)
6. Claude updates its understanding of current state
7. Claude generates the next phase prompt (or you paste the pre-written one)
8. Repeat

### Terminal Assignment Conventions

| Terminal | Project | Specialization | Always Starts With |
|---|---|---|---|
| **A** | BD-Automation-Engine | Hub API, Dashboard, Agents, Search | `cd C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine\` |
| **B** | Data-Scraper | Scraping, Federal APIs, Bullhorn, Job Processing | `cd C:\data-scraper\data-scraper\` |
| **C** | N8N-Builder | LangGraph, Tango Discovery, Outreach Engine, Contact Processing | `cd C:\Auto-Claud\N8N-Builder\` |

### Prompt Structure Template

Every terminal prompt follows this structure:

```
[PHASE NAME]: [One-line description]

PREREQUISITE: [What must be true before starting]

═══ VERIFIED CURRENT STATE ═══
[Key facts about what exists right now — prevents the terminal from making assumptions]

═══ TASK 1: [Task Name] ([estimated time]) ═══
[Specific instructions with code blocks]
[Expected output/verification command]

═══ TASK 2: [Task Name] ([estimated time]) ═══
...

═══ DELIVERABLES ═══
- [ ] [Checklist items]

═══ PHASE COMPLETION ═══
When all tasks are done, output the Phase Completion Summary (format above).

Commit: git add -A && git commit -m "[conventional commit message]" && git push
```

### Parallel Execution Rules

1. Terminal B and C can always run in parallel with each other
2. Terminal A Phase N+1 should wait for Terminal A Phase N completion
3. Terminal B/C support tasks can run simultaneously with Terminal A
4. If Terminal A needs an endpoint from B or C, note it as a BLOCKER in the Phase Completion Summary
5. Cross-terminal dependencies should be documented in the prompt's PREREQUISITE section
```

---

## DOCUMENT 3: Data Schema Reference

Save as: `03_DATA_SCHEMA_REFERENCE.md`

```markdown
# PTS BD Platform — Data Schema Reference
## Last Updated: February 7, 2026

---

## Qdrant Collection Schemas

### contacts (211,267 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "name": "string — Full name",
    "first_name": "string",
    "last_name": "string",
    "title": "string — Job title",
    "company": "string — Employer (e.g., GDIT, Leidos, SAIC)",
    "email": "string",
    "phone": "string",
    "linkedin_url": "string",
    "program": "string — Assigned program (e.g., AF DCGS - Langley)",
    "tier": "string — Hierarchy tier (Tier 1-6)",
    "priority": "string — BD priority (🔴 Critical / 🟠 High / 🟡 Medium / ⚪ Standard)",
    "location": "string — City, State",
    "location_hub": "string — Location grouping (Hampton Roads, San Diego Metro, DC Metro, etc.)",
    "functional_area": "string — Role function (Program Management, Network Engineering, etc.)",
    "source": "string — Data source (zoominfo, linkedin, bullhorn, manual)",
    "source_project": "string — Which project indexed this",
    "date_indexed": "string — ISO date",
    "search_tags": "string[] — Searchable keywords",
    "intel_category": "string — Intelligence classification"
  }
}
```

### programs (68,103 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "program_name": "string",
    "acronym": "string",
    "agency_owner": "string — e.g., USAF, Army, Navy, DIA",
    "prime_contractor": "string",
    "known_subcontractors": "string",
    "contract_value": "string — e.g., $500M",
    "contract_vehicle": "string",
    "pop_start": "string — Period of Performance start",
    "pop_end": "string — Period of Performance end",
    "key_locations": "string",
    "clearance_requirements": "string — e.g., TS/SCI",
    "typical_roles": "string",
    "keywords": "string",
    "program_type": "string",
    "pts_involvement": "string — Current/Past/Target/None",
    "priority_level": "string",
    "pain_points": "string",
    "confidence_level": "string — High/Medium/Low",
    "source_project": "string",
    "date_indexed": "string"
  }
}
```

### jobs (15,997 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "title": "string — Job title",
    "company": "string — Posting company (staffing portal or prime)",
    "location": "string",
    "clearance": "string — Required clearance level",
    "description": "string — Job description text",
    "program_match": "string — Matched federal program (if mapped)",
    "source_portal": "string — Insight Global, Apex, TEKsystems, CACI, GDIT internal",
    "url": "string — Source URL",
    "scraped_date": "string — When scraped",
    "skills": "string — Required skills",
    "experience_level": "string",
    "status": "string — raw_import / enriched / validated / mapped",
    "bd_score": "float — BD opportunity score (0-100)",
    "source_project": "string",
    "date_indexed": "string"
  }
}
```

### federal_contracts (107,902 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "agency": "string — Awarding agency",
    "contractor": "string — Award recipient",
    "naics": "string — NAICS code",
    "value": "string — Contract value",
    "award_date": "string",
    "status": "string — Active/Completed/Option",
    "description": "string — Contract description",
    "pop_start": "string",
    "pop_end": "string",
    "source": "string — USASpending/FPDS/SAM.gov",
    "source_project": "string",
    "date_indexed": "string"
  }
}
```

### bullhorn_notes (50,710 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "contact": "string — About whom",
    "company": "string",
    "author": "string — Note author (salesperson)",
    "date": "string — Note date",
    "type": "string — Note type (call, email, meeting, etc.)",
    "programs_mentioned": "string[]",
    "roles_mentioned": "string[]",
    "locations_mentioned": "string[]",
    "bill_rates": "string[]",
    "headcounts": "string[]",
    "summary": "string — Note text",
    "source_project": "string",
    "date_indexed": "string"
  }
}
```

### intelligence_reports (2,229 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "report_type": "string — bd_intelligence/program_intelligence/analysis_report/gap_analysis/hiring_intelligence/subaward_intelligence/humint_briefing/executive_summary/competitive_intelligence",
    "program": "string — Related program",
    "date": "string",
    "confidence": "string — High/Medium/Low",
    "source_file": "string — Original filename",
    "source_project": "string",
    "date_indexed": "string"
  }
}
```

---

## Notion Database Schemas

### DCGS Contacts Full (Collection ID: 2ccdef65-baa5-8087-a53b-000ba596128e)

| Property | Type | Values |
|---|---|---|
| Name | Title | Contact full name |
| Program | Select | AF DCGS - Langley, AF DCGS - Wright-Patt, AF DCGS - PACAF, AF DCGS - Other, Army DCGS-A, Navy DCGS-N, Corporate HQ, Enterprise Security, Unassigned |
| Hierarchy Tier | Select | Tier 1 - Executive, Tier 2 - Director, Tier 3 - Program Leadership, Tier 4 - Management, Tier 5 - Senior IC, Tier 6 - Individual Contributor |
| BD Priority | Select | 🔴 Critical, 🟠 High, 🟡 Medium, ⚪ Standard |
| Location Hub | Select | Hampton Roads, San Diego Metro, DC Metro, Dayton/Wright-Patt, Other CONUS, OCONUS, Unknown |
| Functional Area | Multi-Select | Program Management, Network Engineering, Cyber Security, ISR/Intelligence, Systems Administration, Software Engineering, Field Service, Security/FSO, Business Development, Training, Administrative |
| Job Title | Rich Text | |
| Email | Email | |
| Phone | Phone | |
| LinkedIn | URL | |
| Company | Select | GDIT, BAE Systems, etc. |

### Classification Logic

```python
# Tier Assignment
TIER_KEYWORDS = {
    'Tier 1 - Executive': ['vice president', 'vp', 'president', 'chief', 'ceo', 'cto', 'cio'],
    'Tier 2 - Director': ['director'],
    'Tier 3 - Program Leadership': ['program manager', 'site lead', 'task order', 'deputy program'],
    'Tier 4 - Management': ['manager', 'team lead', 'supervisor', 'section chief'],
    'Tier 5 - Senior IC': ['senior', 'sr.', 'principal', 'lead engineer', 'architect'],
    'Tier 6 - Individual Contributor': []  # default
}

# Program Assignment by Location
LOCATION_TO_PROGRAM = {
    'Hampton': 'AF DCGS - Langley', 'Newport News': 'AF DCGS - Langley',
    'San Diego': 'AF DCGS - PACAF', 'La Mesa': 'AF DCGS - PACAF',
    'Dayton': 'AF DCGS - Wright-Patt', 'Beavercreek': 'AF DCGS - Wright-Patt',
    'Norfolk': 'Navy DCGS-N', 'Suffolk': 'Navy DCGS-N',
    'Fort Belvoir': 'Army DCGS-A', 'Aberdeen': 'Army DCGS-A',
    'Herndon': 'Corporate HQ', 'Falls Church': 'Corporate HQ', 'Reston': 'Corporate HQ'
}

# BD Priority Assignment
# Tier 1-2 or PACAF → 🔴 Critical
# Tier 3 → 🟠 High
# Tier 4 → 🟡 Medium
# Tier 5-6 → ⚪ Standard
```
```

---

## DOCUMENT 4: BD Methodology & Strategy Reference

Save as: `04_BD_METHODOLOGY_REFERENCE.md`

```markdown
# PTS BD Strategy, Methodology & Execution Reference
## Last Updated: February 7, 2026

---

## Company Overview

**Prime Technical Services (PTS)** is a Service-Disabled Veteran-Owned Small Business (SDVOSB) specializing in cleared IT staffing for federal defense and intelligence contractors. PTS provides contract technical staff to prime contractors (GDIT, Leidos, SAIC, BAE Systems, Northrop Grumman, etc.) supporting Department of Defense and Intelligence Community programs.

**Core Differentiator**: Solution-based BD — PTS arrives at meetings with insider knowledge of a program's specific pain points, labor gaps, and staffing challenges, offering tailored solutions rather than cold-calling with generic capabilities.

---

## The BD Execution Cycle (End-to-End)

### Phase 1: CONTRACT DISCOVERY
**Goal**: Find federal programs with active staffing needs

**Methods**:
1. **Competitor Job Board Scraping** — Scrape Insight Global, Apex Systems, TEKsystems, CACI job postings. These generic postings often map to specific federal contracts.
2. **Federal Contract Database Mining** — Query SAM.gov, FPDS, USASpending via Tango/MakeGov API for active contracts by NAICS codes (5415xx IT services, 5413xx engineering), DoD agencies, >$500K value.
3. **Bullhorn CRM Intelligence** — Analyze 2,687 historical notes from PTS account managers for contract mentions, hiring patterns, and relationship data.
4. **Industry Events & News** — Monitor recompete announcements, option year exercises, and organizational changes.

**Key Data Points to Extract**:
- Program name and acronym
- Prime contractor and subcontractor chain
- Contract value and period of performance
- Key locations (military installations)
- Clearance requirements
- Typical roles needed
- Known pain points

### Phase 2: PROGRAM MAPPING
**Goal**: Map generic job postings to specific federal programs

**Mapping Signals** (in priority order):
1. **Location** — Strongest signal. Jobs near Wright-Patterson AFB → likely NASIC/AF DCGS. Jobs in Hampton → likely Langley/AF DCGS.
2. **Clearance Level** — TS/SCI narrows to IC programs. Secret narrows to tactical programs.
3. **Skills & Technologies** — DCGS-specific: ISR, SIGINT, GEOINT, ELINT. Program-specific tools: Palantir, DCGS-A Block X.
4. **Job Title Patterns** — "Intelligence Analyst" + "ISR" + "Hampton" = very likely AF DCGS Langley.
5. **Company Name** — The staffing portal name (Insight Global posting for GDIT) reveals prime-sub relationships.
6. **Bill Rate / Salary Range** — Government contract bill rates cluster by program and location.

**Scoring Model**:
- Location match: 40 points
- Clearance match: 20 points
- Skills/keywords match: 20 points
- Title pattern match: 10 points
- Company association: 10 points
- Score ≥60 = High confidence mapping

### Phase 3: CONTACT BUILDING
**Goal**: Identify team leads and hiring managers at target programs

**Sources** (in preference order):
1. **Bullhorn CRM** — Existing relationships from PTS account manager history. 2,687 notes contain contact names, roles, interactions.
2. **ZoomInfo** — 275M contact database with direct dials, emails, job titles. Export batches by company + location + title filters.
3. **LinkedIn Recruiter** — Advanced search by company + location + keywords. Profile data for role verification.
4. **Notion DCGS Contacts Database** — 965+ classified DCGS contacts with tier, priority, program assignment.

**Classification System** (6-Tier Hierarchy):
| Tier | Role Level | Examples | BD Priority | Approach |
|---|---|---|---|---|
| **Tier 1** | Executive | VP, President, Chief, C-Suite | 🔴 Critical | Exec-to-exec only |
| **Tier 2** | Director | Director-level | 🔴 Critical | Strategic alignment |
| **Tier 3** | Program Leadership | PM, Site Lead, Task Order Lead | 🟠 High | Data-backed solution pitch |
| **Tier 4** | Management | Manager, Team Lead, Supervisor | 🟡 Medium | Collaborative outreach |
| **Tier 5** | Senior IC | Senior Engineer, Principal, Architect | ⚪ Standard | Relationship building |
| **Tier 6** | Individual Contributor | Analyst, Engineer, Admin | ⚪ Standard | HUMINT gathering |

**Location-to-Program Assignment**:
| Location | Program |
|---|---|
| Hampton, Newport News, Langley | AF DCGS - Langley (DGS-1, 480th ISR Wing) |
| San Diego, La Mesa | AF DCGS - PACAF 🔥 CRITICAL |
| Dayton, Beavercreek, Fairborn | AF DCGS - Wright-Patt (NASIC) |
| Norfolk, Suffolk, Chesapeake, Virginia Beach | Navy DCGS-N |
| Fort Belvoir, Fort Detrick, Aberdeen | Army DCGS-A |
| Herndon, Falls Church, Reston, Fairfax | Corporate HQ |

### Phase 4: HUMINT GATHERING
**Goal**: Gather insider intelligence before approaching decision-makers

**HUMINT is what transforms cold calls into warm introductions.**

**Process**:
1. Start with Tier 5-6 contacts (ICs) — friendly, mission-curious approach
2. Build rapport through genuine interest in their mission and challenges
3. Gather intelligence: team dynamics, actual pain points, hiring manager names, budget cycles, vendor preferences
4. Document all intel in structured format (contact notes, HUMINT briefings)
5. Validate intel through Tier 4 contacts (managers)
6. Build a complete picture before approaching Tier 3+ decision-makers

**Intelligence Categories**:
- **Operational Pain Points**: What's broken? What's understaffed? Where are single points of failure?
- **Hiring Intelligence**: Who's the actual decision-maker? What's the approval process? Are they using a VMS?
- **Budget Intelligence**: When does the budget cycle reset? Are there surge funding opportunities?
- **Competitive Intelligence**: Which other staffing companies are they using? Who's falling short?
- **Organizational Intelligence**: Reporting chains, team structures, upcoming reorgs

**Known Pain Points by Program** (as of Feb 2026):

| Program / Site | Pain Points | Source |
|---|---|---|
| **AF DCGS - PACAF** 🔥 | Acting site lead stretched thin, single points of failure, no redundancy, remote from Langley PMO | HUMINT |
| **AF DCGS - Langley** | High ISR volume, analyst burnout, PMO pressure on vacancies, open Sr. Cyber Analyst | HUMINT + Job postings |
| **AF DCGS - Wright-Patt** | Radar engineer vacancy, DevSecOps shortage, tech modernization delays | HUMINT + Job postings |
| **Army DCGS-A** | Surge staffing needs, multi-site coordination (Belvoir/Detrick/Aberdeen) | HUMINT |
| **Navy DCGS-N** | Ship/shore integration challenges, Norfolk talent competition | HUMINT |

### Phase 5: PERSONALIZED OUTREACH
**Goal**: Craft outreach that demonstrates insider knowledge and offers solutions

**The PTS 6-Step BD Formula** — Every outreach follows this EXACT sequence:

**Step 1: Personalized Message**
Role-specific icebreaker demonstrating knowledge of their work and program.
- Reference their specific site, team, or recent activity
- Show understanding of their operational context
- NEVER generic "I saw your profile" openings
- Example: "Hi Kingsley, managing the PACAF San Diego node remotely from Langley oversight must come with unique challenges — especially maintaining continuity with a lean team."

**Step 2: Current Pain Points**
Program-specific challenges sourced from HUMINT and job posting analysis.
- Reference specific staffing gaps you've identified
- Show awareness of their operational tempo
- Example: "I understand the site is operating with minimal redundancy, and the network/security function is running single-threaded."

**Step 3: Labor Gaps & Open Jobs**
Current vacancies at their location from GDIT Jobs database and scraped competitor postings.
- Cross-reference Program Mapping Intelligence Hub for active requisitions
- Match job titles to the contact's team/function
- Example: "We're tracking 3 open positions for your site — a network engineer, a system admin, and a field service tech."

**Step 4: PTS Past Performance with GDIT**
Direct partnership history establishes credibility with the prime contractor.
- **BICES/BICES-X**: TS/SCI network engineers & intelligence analysts (Norfolk, Tampa, Europe)
- **GSM-O II**: Network engineers for 24/7 DISA global operations
- **NATO BICES**: Coalition intelligence network analysts
- Example: "PTS has placed 12+ TS/SCI network engineers on GDIT's BICES program — same clearance level and similar mission."

**Step 5: Relevant Past Performance to Program**
Map PTS experience to their specific program needs.
- **SOCOM JICCENT**: Joint Intelligence Center analysts (ISR relevance for DCGS)
- **DIA I2OS**: Software integration (DCGS integration challenges)
- **Army RS3**: C4ISR engineers (Army intel experience for DCGS-A)
- **Platform One**: USAF DevSecOps (modernization relevance for Wright-Patt)
- **DISA JRSS**: Multi-site network security deployment

**Step 6: Past Performance Relevant to Job Title**
Match PTS capabilities to the specific roles they need.
- Need Cyber Analysts → PTS cleared cyber portfolio
- Need Network Engineers → PTS DISA/coalition network experience
- Need ISR Analysts → PTS intel community placements
- Need DevSecOps → PTS Platform One experience

### Phase 6: DECISION-MAKER ENGAGEMENT
**Goal**: Set meetings with Program Managers to discuss capabilities and get job requisitions

**Outreach Sequencing by Tier**:

| Contact Tier | Initial Channel | Pitch Approach | CTA | Follow-up |
|---|---|---|---|---|
| Tier 5-6 (ICs) | LinkedIn | Friendly, mission-curious | "Coffee chat" | Email follow-up |
| Tier 4 (Managers) | LinkedIn → Email | Collaborative, solution-focused | "30 min staffing solutions call" | Phone + case study |
| Tier 3 (PMs/Site Leads) | Formal Email | Data-backed, value-driven | "Meet with BD lead + past perf brief" | Exec assistant + events |
| Tier 1-2 (Executives) | Exec-to-Exec | Strategic, high-level | "15-min strategy sync" | Custom proposal or event |

**14-Day Outreach Cadence**:
- Day 1: Intro email (personalized BD Formula)
- Day 2: Check for reply
- Day 3: Follow-up email (different angle, add case study)
- Day 5: SMS brief touchpoint (if phone available)
- Day 7: Case study email with specific past performance alignment
- Day 14: Breakup email (leave door open, offer value)

**Meeting Objectives** (from the How To: Meeting Outline):
1. Give meeting intro — who PTS is, our story, purpose, agenda
2. Learn about their team — roles, responsibilities, tools, technologies
3. Organization breakdown — build rough org chart, find decision-makers
4. Current/upcoming needs — ASK FOR BUSINESS, take the req
5. Identify how PTS can partner to achieve their goals
6. Get referrals to other teams and managers
7. Set next steps — build or drop decision

---

## Priority Targets (As of February 2026)

### 🔴 CRITICAL — Immediate Outreach

**AF DCGS PACAF (San Diego)** — Highest priority site
| Contact | Title | Pain Point | Action |
|---|---|---|---|
| Kingsley Ero | Acting Site Lead | Wearing multiple hats, no backup | Call this week |
| Tara Stephenson | Network Analyst | Sole network/security person | Call this week |

**AF DCGS Langley (DGS-1)**
| Contact | Title | Pain Point | Action |
|---|---|---|---|
| Maureen Shamaly | PM/Site Lead | Open Sr. Cyber Analyst, analyst burnout | Email + call |
| Robert Nicholson | Deputy Site Mgr | Supports Shamaly, knows all gaps | Follow-up |

**AF DCGS Wright-Patterson**
| Contact | Title | Pain Point | Action |
|---|---|---|---|
| Craig Lindahl | Sr. PM | Radar engineer vacancy, DevSecOps shortage | Email intro |

### 🟠 HIGH — Executive Relationship Building

| Contact | Title | Location | Approach |
|---|---|---|---|
| David Winkelman | VP, Defense Intelligence | Herndon | Exec-to-exec |
| Christine Carpenter | Network Ops Manager | Falls Church | Direct outreach |
| Julie Coleman | AF Portfolio Director | Falls Church | Strategic alignment |

### 🟡 MEDIUM — Army & Navy Expansion

| Program | Contact | Title | Action |
|---|---|---|---|
| Army DCGS-A | Jeffrey Bartsch | Ops Manager | Email intro |
| Army DCGS-A | Rebecca Gunning | PM | Follow-up |
| Navy DCGS-N | Dusty Galbraith | PM (Norfolk) | Email intro |
| Navy DCGS-N | Jeffrey Schaf | Site Lead (Tracy) | West coast contact |

---

## Key Metrics & KPIs

| Metric | Description | Target |
|---|---|---|
| Contacts Classified | Total contacts with tier + program + priority | 965+ (DCGS), 2,000+ (all) |
| HUMINT Reports Generated | Weekly intelligence briefings produced | 1/week |
| Outreach Sequences Active | Contacts in active 14-day cadence | 25+ |
| Meetings Set | Discovery calls/meetings with Tier 3+ contacts | 3-5/month |
| Job Requisitions Obtained | Open reqs received from program managers | 2-3/month |
| Pipeline Value | Total contract value of programs in active BD | $950M |
| Scrape Coverage | Job boards monitored weekly | 4 portals |
| Program Mapping Accuracy | Jobs correctly mapped to programs | >80% |
```
```

---

That completes all 4 project knowledge documents. After running the terminal audits, update any values in these documents that the audits reveal have changed, then upload all 4 to the Claude Project.
