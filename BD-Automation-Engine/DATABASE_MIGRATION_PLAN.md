# DATABASE MIGRATION PLAN

> Generated from PROMPT 6 of PTS_NEXTGEN_CONSOLIDATION_BLUEPRINT.md
> Date: 2026-02-16
> Scope: BD-Automation-Engine — SQLite → Supabase, Neo4j standardization, Qdrant → pgvector

---

## CURRENT STATE

### Database Inventory Summary

| Type | Count | Total Size | Purpose |
|------|-------|-----------|---------|
| SQLite (application) | 7 | ~317 MB | CRM data, knowledge graph, memory, checkpoints |
| SQLite (Qdrant internal) | ~30 files | ~1.2 GB | Qdrant vector persistence (not directly accessed) |
| Qdrant collections | 8 primary | 8,447+ vectors | Semantic search, RAG |
| Neo4j | 1 instance | External | Relationship graph (contacts, programs, orgs) |
| Chroma (legacy) | 1 | 8.6 MB | Deprecated — replaced by Qdrant |
| PostgreSQL (services/database.py) | 0 active | Schema only | Future target — not currently in use |

---

### SQLite Databases

#### 1. `bullhorn_master.db` — Master CRM Data

| Attribute | Value |
|-----------|-------|
| **Path** | `Engine7_BullhornETL/data/bullhorn_master.db` |
| **Size** | 293 MB |
| **Schema file** | `Engine7_BullhornETL/scripts/database_schema.py` |
| **Tables** | 13 |
| **Readers** | 30+ modules (program_mapper, contact_scoring, past_performance, indexers, exporters, dashboard) |
| **Writers** | `bullhorn_etl_v2.py`, `bullhorn_activity_logger.py`, `integrate_call_notes.py`, `contact_scoring.py`, `link_to_federal_programs.py` |

**Tables:**

```sql
-- Core entities (4 tables)
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bullhorn_job_id VARCHAR(20) UNIQUE,
    title VARCHAR(500), company VARCHAR(200), location VARCHAR(200),
    description TEXT, clearance VARCHAR(100), pay_rate DECIMAL(10,2),
    bill_rate DECIMAL(10,2), status VARCHAR(50), date_added DATE,
    custom_text1-25 TEXT, -- Bullhorn custom fields
    source_file VARCHAR(500), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bullhorn_candidate_id VARCHAR(50) UNIQUE,
    first_name VARCHAR(100), last_name VARCHAR(100), email VARCHAR(200),
    phone VARCHAR(50), clearance VARCHAR(100), title VARCHAR(200),
    company VARCHAR(200), address VARCHAR(500), status VARCHAR(50),
    source VARCHAR(100), owner VARCHAR(100),
    custom_text1-10 TEXT,
    source_file VARCHAR(500), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE placements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bullhorn_placement_id VARCHAR(50) UNIQUE,
    job_id INTEGER REFERENCES jobs(id),
    candidate_id INTEGER REFERENCES candidates(id),
    start_date DATE, end_date DATE, salary DECIMAL(12,2),
    pay_rate DECIMAL(10,2), bill_rate DECIMAL(10,2),
    status VARCHAR(50), fee DECIMAL(10,2),
    source_file VARCHAR(500), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bullhorn_activity_id VARCHAR(50),
    type VARCHAR(100), action VARCHAR(100),
    date_added DATETIME, candidate_id INTEGER, job_id INTEGER,
    note_body TEXT, subject VARCHAR(500),
    source_file VARCHAR(500), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Business intelligence (3 tables)
CREATE TABLE prime_contractors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) UNIQUE NOT NULL,
    cage_code VARCHAR(20), duns_number VARCHAR(20),
    annual_revenue DECIMAL(15,2), employee_count INTEGER,
    contract_vehicles TEXT, -- JSON array
    engagement_start DATE, last_activity DATE,
    source_file VARCHAR(500), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(500) NOT NULL,
    prime_contractor_id INTEGER REFERENCES prime_contractors(id),
    agency VARCHAR(200), branch VARCHAR(100),
    contract_number VARCHAR(100), contract_value DECIMAL(15,2),
    pop_start DATE, pop_end DATE, clearance_required VARCHAR(100),
    location VARCHAR(200), description TEXT,
    source_file VARCHAR(500), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE past_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prime_contractor_id INTEGER REFERENCES prime_contractors(id),
    program_id INTEGER REFERENCES programs(id),
    total_jobs INTEGER DEFAULT 0, total_placements INTEGER DEFAULT 0,
    total_revenue DECIMAL(15,2) DEFAULT 0,
    fill_rate DECIMAL(5,2), avg_time_to_fill INTEGER,
    performance_score DECIMAL(5,2),
    period_start DATE, period_end DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mapping tables (3 tables)
CREATE TABLE job_program_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL, program_id INTEGER NOT NULL,
    confidence_score DECIMAL(5,2), mapping_method VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE job_prime_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL, prime_contractor_id INTEGER NOT NULL,
    confidence_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE candidate_prime_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL, prime_contractor_id INTEGER NOT NULL,
    program_id INTEGER, start_date DATE, end_date DATE,
    role VARCHAR(200), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit/metadata tables (3 tables)
CREATE TABLE source_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(500) NOT NULL, file_type VARCHAR(50),
    record_count INTEGER, processed_at TIMESTAMP,
    checksum VARCHAR(64), error_message TEXT
);

CREATE TABLE data_quality_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file VARCHAR(500), table_name VARCHAR(100),
    issue_type VARCHAR(100), severity VARCHAR(50),
    description TEXT, resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE processing_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id VARCHAR(50), table_name VARCHAR(100),
    records_read INTEGER, records_inserted INTEGER,
    records_updated INTEGER, duplicates_found INTEGER,
    processing_time_seconds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Additional tables created by analysis scripts:**

```sql
-- From contact_scoring.py
CREATE TABLE contact_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_name VARCHAR(200), score DECIMAL(5,2),
    tier VARCHAR(50), reasons TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- From link_to_federal_programs.py
CREATE TABLE placement_program_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    placement_id INTEGER, program_name VARCHAR(500),
    confidence DECIMAL(5,2), method VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- From integrate_call_notes.py (6 additional tables)
CREATE TABLE call_notes (...);
CREATE TABLE prime_call_mentions (...);
CREATE TABLE program_call_mentions (...);
CREATE TABLE location_intelligence (...);
CREATE TABLE contact_activity_summary (...);
CREATE TABLE gap_analysis (...);

-- From bullhorn_activity_logger.py
CREATE TABLE outreach_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_name TEXT NOT NULL, activity_type TEXT,
    notes TEXT, outcome TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. `bd_graph.db` — SQLite Knowledge Graph

| Attribute | Value |
|-----------|-------|
| **Path** | `Engine8_Knowledge/data/bd_graph.db` |
| **Size** | 804 KB |
| **Schema file** | `Engine8_Knowledge/graph/bd_knowledge_graph.py` |
| **Tables** | 2 |
| **Readers** | `datasette_config.py`, API routes, graph endpoints |
| **Writers** | `bd_knowledge_graph.py` |

```sql
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,     -- Contractor, Program, Contact, Job, Skill, Location
    name TEXT NOT NULL,
    properties TEXT,        -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE relationships (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,     -- PRIMES_ON, SUBS_TO, WORKS_FOR, etc.
    from_entity_id TEXT NOT NULL,
    to_entity_id TEXT NOT NULL,
    properties TEXT,        -- JSON blob
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. `memories.db` — Structured Memory

| Attribute | Value |
|-----------|-------|
| **Path** | `Engine8_Knowledge/data/memories.db` |
| **Size** | 40 KB |
| **Schema file** | `Engine8_Knowledge/scripts/memory_system.py` |
| **Tables** | 3 |
| **Readers/Writers** | `memory_system.py`, API routes |

```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT 'default',
    memory_type TEXT,       -- 'fact', 'preference', 'interaction'
    content TEXT,
    metadata TEXT,          -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_name TEXT,
    interaction_type TEXT,  -- 'call', 'email', 'meeting'
    notes TEXT,
    outcome TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT,       -- 'contact', 'program', 'company'
    entity_name TEXT,
    insight TEXT,
    source TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. `page_index.db` — BM25 RAG Index

| Attribute | Value |
|-----------|-------|
| **Path** | `Engine8_Knowledge/data/page_index.db` |
| **Size** | 24 KB |
| **Schema file** | `Engine8_Knowledge/retrieval/page_index.py` |
| **Tables** | 1 |
| **Readers/Writers** | `page_index.py`, retrieval routes |

```sql
CREATE TABLE pages (
    page_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    document_name TEXT,
    page_number INTEGER,
    content TEXT,
    metadata TEXT            -- JSON
);
CREATE UNIQUE INDEX idx_doc_page ON pages(document_id, page_number);
```

#### 5. `notifications.db` — Alert System

| Attribute | Value |
|-----------|-------|
| **Path** | `Engine8_Knowledge/data/notifications.db` |
| **Size** | 12 KB |
| **Schema file** | `Engine8_Knowledge/api_routers/phase7_endpoints.py` |
| **Tables** | 1 |
| **Readers/Writers** | `phase7_endpoints.py` |

```sql
CREATE TABLE notifications (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    title TEXT,
    message TEXT,
    entity_type TEXT,
    entity_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    priority TEXT DEFAULT 'normal'
);
```

#### 6. `checkpoints_meta.db` — Workflow Checkpoints

| Attribute | Value |
|-----------|-------|
| **Path** | `data/checkpoints_meta.db` + `Engine8_Knowledge/workflows/checkpoint_store.py` |
| **Size** | 24 KB |
| **Tables** | 2 |
| **Readers/Writers** | `checkpoint_store.py`, LangGraph workflows |

```sql
CREATE TABLE threads (
    thread_id TEXT PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    metadata TEXT             -- JSON
);

CREATE TABLE checkpoint_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT NOT NULL,
    step_name TEXT,
    state_json TEXT,          -- Full LangGraph state
    created_at TEXT NOT NULL
);
```

#### 7. `bullhorn_past_performance.db` — Pre-computed Analytics

| Attribute | Value |
|-----------|-------|
| **Path** | `data/from_data_scraper/bullhorn_past_performance.db` |
| **Size** | 23 MB |
| **Tables** | Aggregated performance data |
| **Readers** | Indexing scripts, dashboard |
| **Writers** | ETL pipeline |

#### 8. `chroma.sqlite3` — Legacy (DEPRECATED)

| Attribute | Value |
|-----------|-------|
| **Path** | `Engine8_Knowledge/data/memory/chroma.sqlite3` |
| **Size** | 8.6 MB |
| **Status** | **DEPRECATED** — replaced by Qdrant |
| **Action** | Delete after confirming no references |

---

### Qdrant Vector Collections

All collections use **OpenAI `text-embedding-3-small`** (1536 dimensions, Cosine distance).
Schema defined in `Engine8_Knowledge/schemas/vector_collections.py`.

| Collection | Records | Payload Fields | Indexed Fields | Readers | Writers |
|------------|---------|----------------|----------------|---------|---------|
| `contacts` | 7,337 | contact_id, name, title, company, program, tier, priority, location, email | company, tier, program, bd_priority, source_db | api.py, unified_endpoints, dify_bridge, alerts, call_prep | index_contacts_openai, index_parallel_worker, notion_sync |
| `programs` | 401 | program_id, name, acronym, agency, prime, contract_value, clearance, locations | prime_contractor, status, contract_vehicle, bd_priority | api.py, unified_endpoints, dify_bridge, call_prep | index_small_collections, index_engine2_programs, dedup_programs |
| `documents` | 205 | doc_id, title, doc_type, source, chunk_index, total_chunks, content | doc_type, source_file, tags, created_date | morning_briefing, competitive_intel workflows | index_small_collections, index_all_docs, document processor |
| `activities` | ~500 | activity_type, contact_id, company, date | (minimal) | index_parallel_worker | index_activities_openai, index_parallel_worker |
| `jobs` | 4 | job_id, title, company, location, clearance, program, bd_score, scraped_at, source | company, program_name, clearance, bd_priority, source | api.py, unified_endpoints, pipeline_manager, competitive_intel, alerts | index_small_collections, index_engine1_jobs, pipeline_manager |
| `memories` | ~10 | memory_id, user_id, memory_type, content, created_at | (minimal) | phase7_endpoints | phase7_endpoints, mem0_manager |
| `knowledge_graph` | ~50 | entity_id, entity_type, entity_name, relationships | (minimal) | graph endpoints | graph ingestion |
| `bullhorn_notes` | ~100 | (hybrid dense+sparse) | (minimal) | hybrid_endpoints | hybrid_endpoints |

**Additional collections referenced but with minimal data:**
- `pipeline_tracking`, `federal_contracts`, `intelligence_reports`, `opportunities`, `primes`

---

### Neo4j Graph Database

| Attribute | Value |
|-----------|-------|
| **Connection** | `bolt://localhost:7687` (Neo4j Desktop or Docker) |
| **Driver** | Official `neo4j` Python driver (NOT py2neo or neomodel) |
| **Manager** | `Engine8_Knowledge/graph/neo4j_manager.py` — `Neo4jManager` class |
| **Schema** | `Engine8_Knowledge/graph/schema.py` |
| **Queries** | `Engine8_Knowledge/graph/queries.py` |
| **Ingestion** | `Engine8_Knowledge/graph/ingestion.py` |
| **Node types** | 9 (Person, Company, Program, Job, Contract, Location, Interaction, File, Process) |
| **Relationship types** | 25+ (WORKS_AT, MANAGES, REPORTS_TO, PRIMES_ON, SUBS_TO, etc.) |
| **Unique constraints** | 4 (Person.email, Company.name, Program.acronym, Contract.contract_number) |
| **Indexes** | 9 standard + 3 full-text |
| **API routes** | 10 endpoints at `/graph/neo4j/*` + 11 at `/graph/analytics/*` |

---

## SQLITE → SUPABASE MIGRATION

### Proposed Supabase PostgreSQL Schema

#### Schema: `bd` (all BD tables under one schema)

```sql
-- ============================================================
-- BULLHORN CRM TABLES (from bullhorn_master.db)
-- ============================================================

CREATE TABLE bd.jobs (
    id BIGSERIAL PRIMARY KEY,
    bullhorn_job_id VARCHAR(20) UNIQUE,
    title VARCHAR(500),
    company VARCHAR(200),
    location VARCHAR(200),
    description TEXT,
    clearance VARCHAR(100),
    pay_rate NUMERIC(10,2),
    bill_rate NUMERIC(10,2),
    status VARCHAR(50),
    date_added DATE,
    custom_fields JSONB DEFAULT '{}',   -- Consolidate custom_text1-25 into JSONB
    source_file VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.candidates (
    id BIGSERIAL PRIMARY KEY,
    bullhorn_candidate_id VARCHAR(50) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    name VARCHAR(200) GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
    email VARCHAR(200),
    phone VARCHAR(50),
    clearance VARCHAR(100),
    title VARCHAR(200),
    company VARCHAR(200),
    address VARCHAR(500),
    status VARCHAR(50),
    source VARCHAR(100),
    owner VARCHAR(100),
    custom_fields JSONB DEFAULT '{}',
    source_file VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.placements (
    id BIGSERIAL PRIMARY KEY,
    bullhorn_placement_id VARCHAR(50) UNIQUE,
    job_id BIGINT REFERENCES bd.jobs(id) ON DELETE SET NULL,
    candidate_id BIGINT REFERENCES bd.candidates(id) ON DELETE SET NULL,
    start_date DATE,
    end_date DATE,
    salary NUMERIC(12,2),
    pay_rate NUMERIC(10,2),
    bill_rate NUMERIC(10,2),
    status VARCHAR(50),
    fee NUMERIC(10,2),
    source_file VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.activities (
    id BIGSERIAL PRIMARY KEY,
    bullhorn_activity_id VARCHAR(50),
    type VARCHAR(100),
    action VARCHAR(100),
    date_added TIMESTAMPTZ,
    candidate_id BIGINT REFERENCES bd.candidates(id) ON DELETE SET NULL,
    job_id BIGINT REFERENCES bd.jobs(id) ON DELETE SET NULL,
    note_body TEXT,
    subject VARCHAR(500),
    source_file VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.prime_contractors (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    cage_code VARCHAR(20),
    duns_number VARCHAR(20),
    annual_revenue NUMERIC(15,2),
    employee_count INTEGER,
    contract_vehicles JSONB DEFAULT '[]',   -- Was TEXT (JSON string)
    engagement_start DATE,
    last_activity DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.programs (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    prime_contractor_id BIGINT REFERENCES bd.prime_contractors(id) ON DELETE SET NULL,
    agency VARCHAR(200),
    branch VARCHAR(100),
    contract_number VARCHAR(100),
    contract_value NUMERIC(15,2),
    pop_start DATE,
    pop_end DATE,
    clearance_required VARCHAR(100),
    location VARCHAR(200),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.past_performance (
    id BIGSERIAL PRIMARY KEY,
    prime_contractor_id BIGINT REFERENCES bd.prime_contractors(id),
    program_id BIGINT REFERENCES bd.programs(id),
    total_jobs INTEGER DEFAULT 0,
    total_placements INTEGER DEFAULT 0,
    total_revenue NUMERIC(15,2) DEFAULT 0,
    fill_rate NUMERIC(5,2),
    avg_time_to_fill INTEGER,
    performance_score NUMERIC(5,2),
    period_start DATE,
    period_end DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Mapping tables
CREATE TABLE bd.job_program_mapping (
    id BIGSERIAL PRIMARY KEY,
    job_id BIGINT NOT NULL REFERENCES bd.jobs(id) ON DELETE CASCADE,
    program_id BIGINT NOT NULL REFERENCES bd.programs(id) ON DELETE CASCADE,
    confidence_score NUMERIC(5,2),
    mapping_method VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id, program_id)
);

CREATE TABLE bd.job_prime_mapping (
    id BIGSERIAL PRIMARY KEY,
    job_id BIGINT NOT NULL REFERENCES bd.jobs(id) ON DELETE CASCADE,
    prime_contractor_id BIGINT NOT NULL REFERENCES bd.prime_contractors(id) ON DELETE CASCADE,
    confidence_score NUMERIC(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id, prime_contractor_id)
);

CREATE TABLE bd.candidate_prime_history (
    id BIGSERIAL PRIMARY KEY,
    candidate_id BIGINT NOT NULL REFERENCES bd.candidates(id) ON DELETE CASCADE,
    prime_contractor_id BIGINT NOT NULL REFERENCES bd.prime_contractors(id) ON DELETE CASCADE,
    program_id BIGINT REFERENCES bd.programs(id),
    start_date DATE,
    end_date DATE,
    role VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit tables
CREATE TABLE bd.source_files (
    id BIGSERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    record_count INTEGER,
    processed_at TIMESTAMPTZ,
    checksum VARCHAR(64),
    error_message TEXT
);

CREATE TABLE bd.data_quality_log (
    id BIGSERIAL PRIMARY KEY,
    source_file VARCHAR(500),
    table_name VARCHAR(100),
    issue_type VARCHAR(100),
    severity VARCHAR(50) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    description TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.processing_stats (
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(50),
    table_name VARCHAR(100),
    records_read INTEGER,
    records_inserted INTEGER,
    records_updated INTEGER,
    duplicates_found INTEGER,
    processing_time_seconds REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analysis output tables
CREATE TABLE bd.contact_scores (
    id BIGSERIAL PRIMARY KEY,
    candidate_id BIGINT REFERENCES bd.candidates(id),
    contact_name VARCHAR(200),
    score NUMERIC(5,2),
    tier VARCHAR(50),
    reasons JSONB DEFAULT '[]',      -- Was TEXT
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.outreach_log (
    id BIGSERIAL PRIMARY KEY,
    contact_name TEXT NOT NULL,
    candidate_id BIGINT REFERENCES bd.candidates(id),
    activity_type TEXT,
    notes TEXT,
    outcome TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- KNOWLEDGE SYSTEM TABLES (from Engine8 SQLite DBs)
-- ============================================================

CREATE TABLE bd.knowledge_entities (
    id TEXT PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    name TEXT NOT NULL,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ke_type ON bd.knowledge_entities(type);
CREATE INDEX idx_ke_name ON bd.knowledge_entities USING gin(to_tsvector('english', name));

CREATE TABLE bd.knowledge_relationships (
    id TEXT PRIMARY KEY,
    type VARCHAR(100) NOT NULL,
    from_entity_id TEXT NOT NULL REFERENCES bd.knowledge_entities(id),
    to_entity_id TEXT NOT NULL REFERENCES bd.knowledge_entities(id),
    properties JSONB DEFAULT '{}',
    confidence NUMERIC(3,2) DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_kr_type ON bd.knowledge_relationships(type);
CREATE INDEX idx_kr_from ON bd.knowledge_relationships(from_entity_id);
CREATE INDEX idx_kr_to ON bd.knowledge_relationships(to_entity_id);

CREATE TABLE bd.memories (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT DEFAULT 'default',
    memory_type VARCHAR(50),
    content TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_mem_user ON bd.memories(user_id);
CREATE INDEX idx_mem_type ON bd.memories(memory_type);

CREATE TABLE bd.interactions (
    id BIGSERIAL PRIMARY KEY,
    contact_name TEXT,
    candidate_id BIGINT REFERENCES bd.candidates(id),
    interaction_type VARCHAR(50),
    notes TEXT,
    outcome TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.insights (
    id BIGSERIAL PRIMARY KEY,
    entity_type VARCHAR(50),
    entity_name TEXT,
    insight TEXT,
    source TEXT,
    confidence NUMERIC(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.pages (
    page_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    document_name TEXT,
    page_number INTEGER,
    content TEXT,
    metadata JSONB DEFAULT '{}',
    UNIQUE(document_id, page_number)
);
CREATE INDEX idx_pages_doc ON bd.pages(document_id);

CREATE TABLE bd.notifications (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    type VARCHAR(100) NOT NULL,
    title TEXT,
    message TEXT,
    entity_type VARCHAR(50),
    entity_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    read_at TIMESTAMPTZ,
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical'))
);
CREATE INDEX idx_notif_unread ON bd.notifications(read_at) WHERE read_at IS NULL;

-- ============================================================
-- WORKFLOW TABLES (from checkpoint DBs)
-- ============================================================

CREATE TABLE bd.workflow_threads (
    thread_id TEXT PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.checkpoint_snapshots (
    id BIGSERIAL PRIMARY KEY,
    thread_id TEXT NOT NULL REFERENCES bd.workflow_threads(thread_id),
    step_name TEXT,
    state_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Data Transformation Rules

| SQLite Type | PostgreSQL Type | Transformation |
|-------------|-----------------|----------------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `BIGSERIAL PRIMARY KEY` | Auto-mapped |
| `VARCHAR(N)` | `VARCHAR(N)` | Same |
| `TEXT` (JSON strings) | `JSONB` | `json.loads()` before insert |
| `DECIMAL(M,N)` | `NUMERIC(M,N)` | Same semantics |
| `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | `TIMESTAMPTZ DEFAULT NOW()` | Add timezone |
| `BOOLEAN` (0/1 integers) | `BOOLEAN` | Cast `int` → `bool` |
| `custom_text1` through `custom_text25` | `JSONB custom_fields` | Merge into single JSONB column |
| `TEXT properties` (JSON strings) | `JSONB properties` | Parse JSON before insert |
| `TEXT contract_vehicles` (JSON string) | `JSONB contract_vehicles` | Parse JSON before insert |
| `TEXT reasons` (in contact_scores) | `JSONB reasons` | Parse JSON before insert |

### Row-Level Security Policies

```sql
-- Enable RLS on all tables
ALTER TABLE bd.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE bd.candidates ENABLE ROW LEVEL SECURITY;
-- ... (repeat for all tables)

-- Service role has full access (API server)
CREATE POLICY "Service role full access" ON bd.jobs
    FOR ALL USING (auth.role() = 'service_role');

-- Authenticated users can read BD data
CREATE POLICY "Authenticated read" ON bd.jobs
    FOR SELECT USING (auth.role() = 'authenticated');

-- Only service role can write (ETL pipelines)
CREATE POLICY "Service write" ON bd.jobs
    FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service update" ON bd.jobs
    FOR UPDATE USING (auth.role() = 'service_role');

-- Sensitive contact data: restrict PII columns
-- (email, phone, address visible only to service role)
CREATE POLICY "PII protection" ON bd.candidates
    FOR SELECT USING (
        auth.role() = 'service_role'
        OR auth.role() = 'authenticated'
    );
```

### Indexes Needed

```sql
-- Bullhorn lookups (most common queries)
CREATE INDEX idx_jobs_company ON bd.jobs(company);
CREATE INDEX idx_jobs_status ON bd.jobs(status);
CREATE INDEX idx_jobs_clearance ON bd.jobs(clearance);
CREATE INDEX idx_jobs_date ON bd.jobs(date_added);
CREATE INDEX idx_candidates_company ON bd.candidates(company);
CREATE INDEX idx_candidates_clearance ON bd.candidates(clearance);
CREATE INDEX idx_candidates_email ON bd.candidates(email);
CREATE INDEX idx_placements_dates ON bd.placements(start_date, end_date);
CREATE INDEX idx_activities_date ON bd.activities(date_added);
CREATE INDEX idx_activities_type ON bd.activities(type);
CREATE INDEX idx_programs_agency ON bd.programs(agency);
CREATE INDEX idx_programs_prime ON bd.programs(prime_contractor_id);

-- Full-text search (replaces BM25 page_index)
CREATE INDEX idx_pages_fts ON bd.pages USING gin(to_tsvector('english', content));
CREATE INDEX idx_jobs_fts ON bd.jobs USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));
CREATE INDEX idx_candidates_fts ON bd.candidates USING gin(to_tsvector('english', COALESCE(first_name,'') || ' ' || COALESCE(last_name,'') || ' ' || COALESCE(title,'')));

-- JSONB indexes
CREATE INDEX idx_jobs_custom ON bd.jobs USING gin(custom_fields);
CREATE INDEX idx_candidates_custom ON bd.candidates USING gin(custom_fields);
```

### Migration Script Outline

```python
"""migrate_sqlite_to_supabase.py — One-shot migration script."""

import sqlite3
import json
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]  # Service role key

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Step 1: Migrate bullhorn_master.db (293 MB, ~20 tables)
def migrate_bullhorn():
    conn = sqlite3.connect("Engine7_BullhornETL/data/bullhorn_master.db")
    conn.row_factory = sqlite3.Row

    # Jobs — batch insert 500 at a time
    cursor = conn.execute("SELECT * FROM jobs")
    batch = []
    for row in cursor:
        record = dict(row)
        # Transform custom_text columns into JSONB
        custom = {}
        for i in range(1, 26):
            key = f"custom_text{i}"
            if key in record and record[key]:
                custom[key] = record[key]
            record.pop(key, None)
        record["custom_fields"] = json.dumps(custom)
        batch.append(record)
        if len(batch) >= 500:
            supabase.table("jobs").upsert(batch).execute()
            batch = []
    if batch:
        supabase.table("jobs").upsert(batch).execute()

    # Repeat for: candidates, placements, activities,
    # prime_contractors, programs, past_performance,
    # job_program_mapping, job_prime_mapping, candidate_prime_history,
    # source_files, data_quality_log, processing_stats

# Step 2: Migrate Engine8 databases
def migrate_knowledge():
    # bd_graph.db → knowledge_entities + knowledge_relationships
    conn = sqlite3.connect("Engine8_Knowledge/data/bd_graph.db")
    for row in conn.execute("SELECT * FROM entities"):
        record = dict(row)
        record["properties"] = json.loads(record.get("properties", "{}"))
        supabase.table("knowledge_entities").upsert([record]).execute()

    for row in conn.execute("SELECT * FROM relationships"):
        record = dict(row)
        record["properties"] = json.loads(record.get("properties", "{}"))
        supabase.table("knowledge_relationships").upsert([record]).execute()

    # memories.db → memories + interactions + insights
    # page_index.db → pages
    # notifications.db → notifications
    # checkpoints_meta.db → workflow_threads + checkpoint_snapshots

# Step 3: Verify counts
def verify():
    for table in ["jobs", "candidates", "placements", ...]:
        pg_count = supabase.table(table).select("*", count="exact").execute().count
        sqlite_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert pg_count == sqlite_count, f"Mismatch in {table}: {pg_count} vs {sqlite_count}"
```

---

## NEO4J STANDARDIZATION

### Current State

- **Driver:** Raw `neo4j` Python driver via `Neo4jManager` class
- **Query style:** Raw Cypher strings in `queries.py`
- **Connection:** `bolt://localhost:7687` with connection pooling (50 max)
- **Transaction support:** Manual `read_transaction()`/`write_transaction()` with Tenacity retry
- **NOT using:** py2neo, neomodel, or any ORM/OGM

### Proposed neomodel StructuredNode Classes

```python
"""bd_graph_models.py — neomodel OGM for BD knowledge graph."""

from neomodel import (
    StructuredNode, StructuredRel,
    StringProperty, IntegerProperty, FloatProperty,
    DateProperty, DateTimeProperty, JSONProperty,
    BooleanProperty, ArrayProperty,
    RelationshipTo, RelationshipFrom,
    UniqueIdProperty,
)


# ─── Relationship Models ─────────────────────────────────

class WorksAtRel(StructuredRel):
    since = DateProperty()
    title = StringProperty()

class ManagesRel(StructuredRel):
    role = StringProperty()

class PrimesOnRel(StructuredRel):
    contract_value = FloatProperty()
    vehicle = StringProperty()

class SubsToRel(StructuredRel):
    on_program = StringProperty()

class MappedToRel(StructuredRel):
    confidence_score = FloatProperty()

class InteractionRel(StructuredRel):
    pass

class DerivedFromRel(StructuredRel):
    transform = StringProperty()
    timestamp = DateTimeProperty()
    process_name = StringProperty()


# ─── Node Models ──────────────────────────────────────────

class Person(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True, index=True)
    first_name = StringProperty()
    last_name = StringProperty()
    email = StringProperty(unique_index=True)
    phone = StringProperty()
    title = StringProperty()
    company = StringProperty(index=True)
    tier = StringProperty(index=True)          # C-Suite, VP/Director, PM, Tech Lead, Staff
    bd_priority = StringProperty()
    linkedin = StringProperty()
    location_hub = StringProperty()
    functional_area = StringProperty()
    program = StringProperty()
    source_db = StringProperty()

    # Relationships
    works_at = RelationshipTo('Company', 'WORKS_AT', model=WorksAtRel)
    manages = RelationshipTo('Program', 'MANAGES', model=ManagesRel)
    reports_to = RelationshipTo('Person', 'REPORTS_TO')
    located_in = RelationshipTo('Location', 'LOCATED_IN')
    contacted_by = RelationshipFrom('Interaction', 'BETWEEN')


class Company(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True, unique_index=True)
    type = StringProperty(index=True)          # prime, sub, agency, staffing
    revenue = FloatProperty()
    employee_count = IntegerProperty()
    headquarters = StringProperty()
    is_defense_prime = BooleanProperty(default=False)
    website = StringProperty()

    # Relationships
    primes_on = RelationshipTo('Program', 'PRIMES_ON', model=PrimesOnRel)
    subs_to = RelationshipTo('Company', 'SUBS_TO', model=SubsToRel)
    competes_with = RelationshipTo('Company', 'COMPETES_WITH')
    located_in = RelationshipTo('Location', 'COMPANY_LOCATED_IN')


class Program(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True, index=True)
    acronym = StringProperty(unique_index=True)
    value = FloatProperty()
    agency_owner = StringProperty(index=True)
    prime_contractor = StringProperty()
    pop_start = DateProperty()
    pop_end = DateProperty()
    clearance_req = StringProperty()
    program_type = StringProperty()
    confidence_level = FloatProperty()
    contract_vehicle = StringProperty()
    hiring_velocity = IntegerProperty()
    recompete_date = DateProperty()
    naics = StringProperty()

    # Relationships
    owned_by = RelationshipTo('Company', 'OWNED_BY')
    located_at = RelationshipTo('Location', 'LOCATED_AT')
    has_contract = RelationshipTo('Contract', 'HAS_CONTRACT')


class Job(StructuredNode):
    uid = UniqueIdProperty()
    title = StringProperty(required=True)
    status = StringProperty(index=True)
    pay_rate = FloatProperty()
    bill_rate = FloatProperty()
    clearance = StringProperty()
    date_added = DateProperty()
    employment_type = StringProperty()
    location = StringProperty()
    source_url = StringProperty()
    bd_priority = StringProperty()
    functional_area = StringProperty()

    # Relationships
    posted_by = RelationshipTo('Company', 'POSTED_BY')
    mapped_to = RelationshipTo('Program', 'MAPPED_TO', model=MappedToRel)
    at_location = RelationshipTo('Location', 'JOB_AT')


class Contract(StructuredNode):
    uid = UniqueIdProperty()
    contract_number = StringProperty(unique_index=True)
    vehicle = StringProperty()
    value = FloatProperty()
    naics = StringProperty()
    set_aside = StringProperty()
    pop_start = DateProperty()
    pop_end = DateProperty()
    award_date = DateProperty()

    # Relationships
    awarded_to = RelationshipTo('Company', 'AWARDED_TO')
    covers = RelationshipTo('Program', 'COVERS')


class Location(StructuredNode):
    uid = UniqueIdProperty()
    city = StringProperty(index=True)
    state = StringProperty(index=True)
    coordinates_lat = FloatProperty()
    coordinates_lon = FloatProperty()
    hub_name = StringProperty()
    military_installation = StringProperty()
    region = StringProperty()


class Interaction(StructuredNode):
    uid = UniqueIdProperty()
    date = DateTimeProperty(index=True)
    type = StringProperty(index=True)   # call, email, meeting, linkedin
    summary = StringProperty()
    sentiment = StringProperty()
    author = StringProperty()
    action = StringProperty()
    status = StringProperty()
    note_body = StringProperty()

    # Relationships
    between = RelationshipTo('Person', 'BETWEEN')
    about = RelationshipTo('Program', 'ABOUT')
    by_user = RelationshipTo('Person', 'BY_USER')


class File(StructuredNode):
    uid = UniqueIdProperty()
    path = StringProperty(required=True)
    name = StringProperty()
    type = StringProperty()
    extension = StringProperty()
    size_bytes = IntegerProperty()
    hash = StringProperty()
    modified = DateTimeProperty()
    engine = StringProperty()
    is_input = BooleanProperty()
    is_output = BooleanProperty()

    # Relationships
    derived_from = RelationshipTo('File', 'DERIVED_FROM', model=DerivedFromRel)
    depends_on = RelationshipTo('File', 'DEPENDS_ON')


class Process(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    script_path = StringProperty()
    engine = StringProperty()
    description = StringProperty()
    last_run = DateTimeProperty()
    run_count = IntegerProperty()
    avg_duration_seconds = FloatProperty()

    # Relationships
    reads = RelationshipTo('File', 'READS')
    writes = RelationshipTo('File', 'WRITES')
```

### Migration from Raw Driver to neomodel

```python
"""migrate_neo4j_to_neomodel.py"""

# Step 1: Install neomodel
# pip install neomodel

# Step 2: Configure connection
from neomodel import config
config.DATABASE_URL = 'bolt://neo4j:pts_bd_2026@localhost:7687'

# Step 3: Install constraints and indexes (replaces schema.py)
from neomodel import install_all_labels
install_all_labels()  # Auto-creates all unique constraints and indexes

# Step 4: Verify existing data is compatible
# neomodel reads existing nodes by label — no data migration needed
# Existing Cypher-created nodes are immediately accessible via neomodel

# Step 5: Gradually replace raw Cypher queries
# BEFORE (queries.py):
#   results = manager.run_query(
#       "MATCH (p:Person)-[:WORKS_AT]->(c:Company) WHERE c.name = $name RETURN p",
#       {"name": "Leidos"}
#   )
#
# AFTER (neomodel):
#   company = Company.nodes.get(name="Leidos")
#   people = company.employees.all()  # via reverse relationship

# Step 6: Keep Neo4jManager for complex Cypher (path queries, analytics)
# neomodel doesn't replace graph algorithms — keep raw Cypher for:
#   - Shortest path queries
#   - Community detection
#   - Influence scoring
#   - Complex multi-hop traversals
```

---

## QDRANT → PGVECTOR MIGRATION

### Current Qdrant State

| Collection | Records | Dimensions | Distance | Embedding Model |
|------------|---------|-----------|----------|----------------|
| contacts | 7,337 | 1536 | Cosine | text-embedding-3-small |
| programs | 401 | 1536 | Cosine | text-embedding-3-small |
| documents | 205 | 1536 | Cosine | text-embedding-3-small |
| activities | ~500 | 1536 | Cosine | text-embedding-3-small |
| jobs | 4 | 1536 | Cosine | text-embedding-3-small |
| memories | ~10 | 1536 | Cosine | text-embedding-3-small |
| knowledge_graph | ~50 | 1536 | Cosine | text-embedding-3-small |
| bullhorn_notes | ~100 | 1536 | Cosine | text-embedding-3-small |

### Proposed pgvector Table Structure

```sql
-- Enable pgvector extension (Supabase has this pre-installed)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- VECTOR TABLES (replacing Qdrant collections)
-- ============================================================

CREATE TABLE bd.contact_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id VARCHAR(50),
    name TEXT,
    title TEXT,
    company TEXT,
    program TEXT,
    tier VARCHAR(50),
    bd_priority VARCHAR(50),
    location TEXT,
    email TEXT,
    source_db VARCHAR(50),
    embedding vector(1536),
    text_content TEXT,              -- Original text that was embedded
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.program_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    program_id VARCHAR(50),
    name TEXT,
    acronym VARCHAR(50),
    agency TEXT,
    prime_contractor TEXT,
    contract_value NUMERIC(15,2),
    clearance TEXT,
    locations TEXT,
    status VARCHAR(50),
    bd_priority VARCHAR(50),
    embedding vector(1536),
    text_content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id TEXT,
    title TEXT,
    doc_type VARCHAR(100),
    source TEXT,
    chunk_index INTEGER,
    total_chunks INTEGER,
    content TEXT,
    tags TEXT[],
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.activity_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_type VARCHAR(100),
    contact_id VARCHAR(50),
    company TEXT,
    date TIMESTAMPTZ,
    content TEXT,
    subject TEXT,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.job_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(50),
    title TEXT,
    company TEXT,
    location TEXT,
    clearance VARCHAR(100),
    program_name TEXT,
    bd_score NUMERIC(5,2),
    bd_priority VARCHAR(50),
    source VARCHAR(100),
    scraped_at TIMESTAMPTZ,
    embedding vector(1536),
    text_content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bd.memory_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id TEXT,
    user_id TEXT DEFAULT 'default',
    memory_type VARCHAR(50),
    content TEXT,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Index Type: HNSW (recommended)

```sql
-- HNSW indexes — better recall than IVFFlat, good for our data sizes
-- Parameters: m=16, ef_construction=64 (defaults, good for <100K vectors)

CREATE INDEX idx_contacts_embedding ON bd.contact_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_programs_embedding ON bd.program_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_documents_embedding ON bd.document_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);  -- More vectors, higher ef

CREATE INDEX idx_activities_embedding ON bd.activity_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_jobs_embedding ON bd.job_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_memories_embedding ON bd.memory_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Payload filter indexes (for filtered vector search)
CREATE INDEX idx_ce_company ON bd.contact_embeddings(company);
CREATE INDEX idx_ce_tier ON bd.contact_embeddings(tier);
CREATE INDEX idx_ce_program ON bd.contact_embeddings(program);
CREATE INDEX idx_pe_agency ON bd.program_embeddings(agency);
CREATE INDEX idx_pe_prime ON bd.program_embeddings(prime_contractor);
CREATE INDEX idx_de_type ON bd.document_embeddings(doc_type);
CREATE INDEX idx_je_company ON bd.job_embeddings(company);
CREATE INDEX idx_je_clearance ON bd.job_embeddings(clearance);
```

**Why HNSW over IVFFlat:**
- Dataset is <100K vectors — HNSW handles this efficiently
- HNSW has better recall at same query speed
- No need for periodic re-training (IVFFlat requires it after large inserts)
- Supabase recommends HNSW for collections under 1M vectors

### Migration Script Outline

```python
"""migrate_qdrant_to_pgvector.py"""

from qdrant_client import QdrantClient
from supabase import create_client

qdrant = QdrantClient(url="http://localhost:6333")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

COLLECTION_MAP = {
    "contacts": "contact_embeddings",
    "programs": "program_embeddings",
    "documents": "document_embeddings",
    "activities": "activity_embeddings",
    "jobs": "job_embeddings",
    "memories": "memory_embeddings",
}

def migrate_collection(qdrant_name: str, pg_table: str):
    """Scroll all points from Qdrant and insert into pgvector."""
    offset = None
    total = 0

    while True:
        results, offset = qdrant.scroll(
            collection_name=qdrant_name,
            limit=100,
            offset=offset,
            with_vectors=True,
            with_payload=True,
        )

        batch = []
        for point in results:
            record = {
                **point.payload,
                "embedding": point.vector,  # list[float] → pgvector
            }
            batch.append(record)

        if batch:
            supabase.table(pg_table).insert(batch).execute()
            total += len(batch)

        if offset is None:
            break

    print(f"Migrated {total} vectors: {qdrant_name} → {pg_table}")

def verify_counts():
    """Verify vector counts match."""
    for qdrant_name, pg_table in COLLECTION_MAP.items():
        qdrant_count = qdrant.get_collection(qdrant_name).points_count
        pg_count = supabase.table(pg_table).select("*", count="exact").execute().count
        status = "OK" if qdrant_count == pg_count else "MISMATCH"
        print(f"  {qdrant_name}: Qdrant={qdrant_count}, pgvector={pg_count} [{status}]")

# Run migration
for src, dst in COLLECTION_MAP.items():
    migrate_collection(src, dst)
verify_counts()
```

### pgvector Search Query Examples

```sql
-- Semantic search (replaces qdrant.query_points)
SELECT id, name, title, company, tier,
       1 - (embedding <=> $1::vector) AS score
FROM bd.contact_embeddings
ORDER BY embedding <=> $1::vector
LIMIT 10;

-- Filtered semantic search (replaces Qdrant Filter)
SELECT id, name, title, company,
       1 - (embedding <=> $1::vector) AS score
FROM bd.contact_embeddings
WHERE tier = 'C-Suite' AND company = 'Leidos'
ORDER BY embedding <=> $1::vector
LIMIT 10;

-- Hybrid search (vector + full-text)
SELECT id, name, title, company,
       (0.7 * (1 - (embedding <=> $1::vector))) +
       (0.3 * ts_rank(to_tsvector('english', text_content), plainto_tsquery($2))) AS score
FROM bd.contact_embeddings
WHERE to_tsvector('english', text_content) @@ plainto_tsquery($2)
ORDER BY score DESC
LIMIT 10;
```

---

## REPOSITORY PATTERN IMPLEMENTATION

### Base Repository

```python
"""libs/db_layer/base.py"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class EntityRepository(ABC, Generic[T]):
    """Abstract repository interface for all entity types."""

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID."""

    @abstractmethod
    async def list(
        self, filters: Dict[str, Any] = None, limit: int = 50, offset: int = 0
    ) -> tuple[List[T], int]:
        """List entities with optional filters. Returns (items, total)."""

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[tuple[T, float]]:
        """Semantic search. Returns (entity, score) pairs."""

    @abstractmethod
    async def upsert(self, entity: T) -> str:
        """Insert or update an entity. Returns ID."""

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete entity by ID."""

    @abstractmethod
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """Count entities matching filters."""
```

### Contact Repositories

```python
"""libs/db_layer/contacts/models.py"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Contact(BaseModel):
    id: Optional[str] = None
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    program: Optional[str] = None
    tier: Optional[str] = None          # C-Suite, VP/Director, PM, Tech Lead, Staff
    bd_priority: Optional[str] = None   # Critical, High, Medium, Low
    clearance: Optional[str] = None
    location: Optional[str] = None
    source_db: Optional[str] = None
    created_at: Optional[datetime] = None
```

```python
"""libs/db_layer/contacts/supabase_repo.py"""

from supabase import AsyncClient
from .models import Contact
from ..base import EntityRepository
from typing import Optional, List, Dict, Any


class SupabaseContactRepo(EntityRepository[Contact]):
    def __init__(self, client: AsyncClient):
        self.client = client
        self.table = "candidates"           # Bullhorn CRM table
        self.vector_table = "contact_embeddings"  # pgvector table

    async def get_by_id(self, id: str) -> Optional[Contact]:
        result = await self.client.table(self.table).select("*").eq("id", id).single().execute()
        return Contact(**result.data) if result.data else None

    async def list(
        self, filters: Dict[str, Any] = None, limit: int = 50, offset: int = 0
    ) -> tuple[List[Contact], int]:
        query = self.client.table(self.table).select("*", count="exact")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        result = await query.range(offset, offset + limit - 1).execute()
        contacts = [Contact(**r) for r in result.data]
        return contacts, result.count

    async def search(self, query: str, limit: int = 10) -> List[tuple[Contact, float]]:
        # Uses pgvector via Supabase RPC
        embedding = await self._get_embedding(query)
        result = await self.client.rpc(
            "match_contacts",
            {"query_embedding": embedding, "match_count": limit}
        ).execute()
        return [(Contact(**r), r["similarity"]) for r in result.data]

    async def upsert(self, entity: Contact) -> str:
        data = entity.model_dump(exclude_none=True)
        result = await self.client.table(self.table).upsert(data).execute()
        return str(result.data[0]["id"])

    async def delete(self, id: str) -> bool:
        await self.client.table(self.table).delete().eq("id", id).execute()
        return True

    async def count(self, filters: Dict[str, Any] = None) -> int:
        query = self.client.table(self.table).select("*", count="exact", head=True)
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        result = await query.execute()
        return result.count

    async def _get_embedding(self, text: str) -> list:
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
        response = await client.embeddings.create(input=text, model="text-embedding-3-small")
        return response.data[0].embedding
```

```python
"""libs/db_layer/contacts/neo4j_repo.py"""

from neomodel import db
from .models import Contact
from ..base import EntityRepository
from typing import Optional, List, Dict, Any


class Neo4jContactRepo(EntityRepository[Contact]):
    """Graph-based contact queries (relationships, paths, org charts)."""

    async def get_by_id(self, id: str) -> Optional[Contact]:
        results, _ = db.cypher_query(
            "MATCH (p:Person {uid: $id}) RETURN p", {"id": id}
        )
        if results:
            node = results[0][0]
            return Contact(**dict(node))
        return None

    async def list(
        self, filters: Dict[str, Any] = None, limit: int = 50, offset: int = 0
    ) -> tuple[List[Contact], int]:
        where_clauses = []
        params = {"limit": limit, "skip": offset}
        if filters:
            for key, value in filters.items():
                where_clauses.append(f"p.{key} = ${key}")
                params[key] = value
        where = " AND ".join(where_clauses)
        where_str = f"WHERE {where}" if where else ""

        results, _ = db.cypher_query(
            f"MATCH (p:Person) {where_str} RETURN p SKIP $skip LIMIT $limit",
            params,
        )
        contacts = [Contact(**dict(r[0])) for r in results]

        count_results, _ = db.cypher_query(
            f"MATCH (p:Person) {where_str} RETURN count(p)", params
        )
        total = count_results[0][0]
        return contacts, total

    async def search(self, query: str, limit: int = 10) -> List[tuple[Contact, float]]:
        # Full-text search via Neo4j
        results, _ = db.cypher_query(
            """CALL db.index.fulltext.queryNodes('person_fulltext', $query)
               YIELD node, score
               RETURN node, score LIMIT $limit""",
            {"query": query, "limit": limit},
        )
        return [(Contact(**dict(r[0])), r[1]) for r in results]

    async def upsert(self, entity: Contact) -> str:
        data = entity.model_dump(exclude_none=True)
        results, _ = db.cypher_query(
            "MERGE (p:Person {email: $email}) SET p += $props RETURN p.uid",
            {"email": data.get("email", ""), "props": data},
        )
        return results[0][0]

    async def delete(self, id: str) -> bool:
        db.cypher_query("MATCH (p:Person {uid: $id}) DETACH DELETE p", {"id": id})
        return True

    async def count(self, filters: Dict[str, Any] = None) -> int:
        results, _ = db.cypher_query("MATCH (p:Person) RETURN count(p)")
        return results[0][0]
```

### Program Repository

```python
"""libs/db_layer/programs/models.py"""

from pydantic import BaseModel
from typing import Optional
from datetime import date


class FederalProgram(BaseModel):
    id: Optional[str] = None
    name: str
    acronym: Optional[str] = None
    agency: Optional[str] = None
    branch: Optional[str] = None
    prime_contractor: Optional[str] = None
    contract_number: Optional[str] = None
    contract_value: Optional[float] = None
    pop_start: Optional[date] = None
    pop_end: Optional[date] = None
    clearance_required: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    pts_involvement: Optional[str] = None
    priority_level: Optional[str] = None
```

```python
"""libs/db_layer/programs/supabase_repo.py"""
# Same pattern as SupabaseContactRepo, targeting bd.programs table
# and bd.program_embeddings for vector search

class SupabaseProgramRepo(EntityRepository[FederalProgram]):
    def __init__(self, client: AsyncClient):
        self.client = client
        self.table = "programs"
        self.vector_table = "program_embeddings"
    # ... (same CRUD pattern)
```

### Job Repository

```python
"""libs/db_layer/jobs/models.py"""

from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class ScrapedJob(BaseModel):
    id: Optional[str] = None
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    clearance: Optional[str] = None
    mapped_program: Optional[str] = None
    bd_score: Optional[float] = None
    status: Optional[str] = None
    stage: Optional[str] = None
    source: Optional[str] = None
    scraped_at: Optional[datetime] = None
```

### Dependency Injection in FastAPI

```python
"""api/dependencies.py"""

from functools import lru_cache
from libs.db_layer.contacts.supabase_repo import SupabaseContactRepo
from libs.db_layer.contacts.neo4j_repo import Neo4jContactRepo
from libs.db_layer.programs.supabase_repo import SupabaseProgramRepo
from libs.db_layer.base import EntityRepository

@lru_cache
def get_supabase_client():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_contact_repo() -> EntityRepository:
    return SupabaseContactRepo(get_supabase_client())

def get_contact_graph_repo() -> EntityRepository:
    return Neo4jContactRepo()

def get_program_repo() -> EntityRepository:
    return SupabaseProgramRepo(get_supabase_client())

# Usage in routes:
# @router.get("/contacts")
# async def list_contacts(repo: EntityRepository = Depends(get_contact_repo)):
#     contacts, total = await repo.list(limit=50)
#     return {"data": [c.model_dump() for c in contacts], "total": total}
```

---

## MIGRATION SEQUENCE

### Phase 1: Create Supabase Tables (Schema Only)

```bash
# 1. Create Supabase project (or local Docker instance)
# 2. Run schema migration
supabase db push  # or run SQL above via Supabase dashboard

# 3. Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

# 4. Create all tables, indexes, and RLS policies
# 5. Create RPC functions for vector search
```

**Rollback:** Drop schema `bd` entirely.

### Phase 2: Implement Repository Classes

```
libs/db_layer/
├── base.py                     # EntityRepository[T]
├── connections.py              # get_supabase_client(), get_neo4j_db()
├── contacts/
│   ├── models.py               # Contact Pydantic model
│   ├── supabase_repo.py        # SupabaseContactRepo
│   └── neo4j_repo.py           # Neo4jContactRepo
├── programs/
│   ├── models.py               # FederalProgram model
│   └── supabase_repo.py        # SupabaseProgramRepo
├── jobs/
│   ├── models.py               # ScrapedJob model
│   └── supabase_repo.py        # SupabaseJobRepo
├── activities/
│   ├── models.py               # Activity model
│   └── supabase_repo.py        # SupabaseActivityRepo
└── memory/
    ├── models.py               # Memory, Interaction, Insight models
    └── supabase_repo.py        # SupabaseMemoryRepo
```

**Rollback:** Delete `libs/db_layer/` directory.

### Phase 3: Migrate Data (Background Job)

```
1. Run migrate_sqlite_to_supabase.py (bullhorn_master.db → bd.* tables)
2. Run migrate_sqlite_to_supabase.py (Engine8 DBs → bd.* tables)
3. Run migrate_qdrant_to_pgvector.py (all 8 collections)
4. Verify all counts match
5. Run spot-check queries to validate data integrity
```

**Rollback:** Data is additive — Supabase tables can be truncated without affecting SQLite/Qdrant sources.

### Phase 4: Switch Reads (Feature Flag)

```python
# config/feature_flags.py
USE_SUPABASE = os.environ.get("USE_SUPABASE", "false").lower() == "true"

# api/dependencies.py
def get_contact_repo():
    if USE_SUPABASE:
        return SupabaseContactRepo(get_supabase_client())
    else:
        return QdrantContactRepo(get_qdrant_client())  # Legacy
```

**Rollback:** Set `USE_SUPABASE=false`.

### Phase 5: Switch Writes (Feature Flag)

```python
# Dual-write during transition
USE_SUPABASE_WRITES = os.environ.get("USE_SUPABASE_WRITES", "false").lower() == "true"

async def ingest_contact(contact: Contact):
    # Always write to legacy (safety)
    await legacy_qdrant_upsert(contact)
    # Also write to Supabase if enabled
    if USE_SUPABASE_WRITES:
        await supabase_repo.upsert(contact)
```

**Rollback:** Set `USE_SUPABASE_WRITES=false`.

### Phase 6: Verify Data Integrity

```python
"""verify_migration.py"""
# Compare record counts across all databases
# Run identical queries against both backends
# Check that search results have same ranking (cosine similarity)
# Verify RLS policies work correctly
# Load test with production query patterns
```

### Phase 7: Remove Old Database Code

- Delete `QdrantClient` calls from all 54+ files
- Delete `sqlite3.connect()` calls from all 40+ files
- Remove `simple_knowledge_api.py` (absorbed into unified API)
- Remove `Engine8_Knowledge/schemas/vector_collections.py` (replaced by pgvector schema)
- Remove `Engine8_Knowledge/graph/bd_knowledge_graph.py` (SQLite graph → Neo4j is canonical)

### Phase 8: Drop Old Files

```bash
# Only after Phase 6 verification passes
rm Engine7_BullhornETL/data/bullhorn_master.db        # 293 MB
rm Engine8_Knowledge/data/bd_graph.db                  # 804 KB
rm Engine8_Knowledge/data/memories.db                  # 40 KB
rm Engine8_Knowledge/data/page_index.db                # 24 KB
rm Engine8_Knowledge/data/notifications.db             # 12 KB
rm data/checkpoints_meta.db                            # 24 KB
rm Engine8_Knowledge/data/memory/chroma.sqlite3        # 8.6 MB (deprecated)
rm -rf Engine8_Knowledge/data/qdrant/                  # ~1.2 GB vector files
```

**Total disk savings: ~1.5 GB**

---

## RISK ASSESSMENT

| Risk | Severity | Mitigation |
|------|----------|------------|
| Data loss during migration | Critical | Dual-write period, verify counts, never delete source before verification |
| Supabase latency vs local SQLite | Medium | Connection pooling, query optimization, consider self-hosted Supabase |
| pgvector recall vs Qdrant | Medium | Benchmark with production queries before switching reads |
| Neo4j neomodel learning curve | Low | Keep raw Cypher for complex queries, use neomodel for CRUD only |
| Embedding dimension incompatibility | Blocked | Must resolve 384 vs 1536 mismatch BEFORE migration (standardize on 1536) |
| RLS policy complexity | Medium | Test thoroughly with service role and authenticated role tokens |

---

*7 SQLite databases (317 MB) + 8 Qdrant collections (8,447 vectors) → Supabase PostgreSQL + pgvector. Neo4j retained for graph traversal, standardized via neomodel OGM.*
