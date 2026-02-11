# OpenClaw: Autonomous Self-Evolving Master Orchestrator
# Complete Research & Architecture Document

**Date:** 2026-02-10
**Author:** Deep multi-agent research analysis
**Scope:** BD-Automation-Engine + OpenClaw-PTS full codebase audit, architecture design, and implementation plan

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [BD-Automation-Engine: Complete Codebase Audit](#codebase-audit)
3. [OpenClaw-PTS: Architecture Analysis](#openclaw-analysis)
4. [Real vs Simulated Assessment](#real-vs-simulated)
5. [Complete API Endpoint Inventory](#api-inventory)
6. [Exact Data Contracts & Interfaces](#data-contracts)
7. [The Infinite Loop Architecture (OODA + Learn)](#infinite-loop)
8. [Self-Discovery Mechanisms](#self-discovery)
9. [Execution Architecture](#execution-architecture)
10. [Precise API Wiring Map](#api-wiring)
11. [Event-Driven Architecture](#event-driven)
12. [Failure Recovery & Resilience](#failure-recovery)
13. [Monitoring & Observability](#monitoring)
14. [Self-Improvement Flywheel](#self-improvement)
15. [Safety & Governance](#safety)
16. [6 New Skills: Complete Specifications](#skill-specs)
17. [Implementation Phases](#implementation)
18. [Verification Plan](#verification)
19. [Key Files Reference](#key-files)

---

## 1. Executive Summary <a name="executive-summary"></a>

### Two Systems, One Vision

**BD-Automation-Engine** has the **BRAIN** — meta-learner (5 analysis domains), pattern engine (7 opportunity types), insight compiler (4 briefing types), swarm decomposer (5 task DAG templates, 8 worker types), opportunity scorer (6 dimensions), relationship engine (6 factors), NLQ engine (14 intents), MCP orchestrator (DAG execution), 200+ API endpoints, 8,447+ vectors, 47-page dashboard.

**OpenClaw-PTS** has the **BODY** — 75+ auto-discovered skills, cron scheduling, 3 MCP bridge servers (:3001-3003), WebSocket Gateway (:18789), Ollama local LLM, cognitive memory, autonomous agent prompts, Notion access, git browsing across 6 repos.

**The vision:** Wire the brain to the body. Create a system that operates in an infinite OODA loop — observing the world, orienting on opportunities, deciding what to do, acting autonomously, and learning from every outcome. No prompts needed. Just an endless flow of intelligence, development, and self-improvement.

### Architecture Readiness: 80% Production-Ready

- **Fully Operational:** 8-engine pipeline, 200+ API endpoints, Qdrant vector DB, scheduler, dashboard
- **Algorithms Real, Data Mocked:** Pattern engine, meta-learner, swarm workers (3 gaps to close)
- **All 4 Key API Systems Already Wired:** Swarm (10 endpoints), Memory (12), Intelligence (13), Relationships (14)

---

## 2. BD-Automation-Engine: Complete Codebase Audit <a name="codebase-audit"></a>

### Development History

- **46 phases of development** committed to `claude/setup-auto-claude-IrK21`
- **106,090+ lines inserted** in last 20 commits
- **319 files changed** across the codebase
- **7 pipeline runs** on Feb 10, 2026 (4 succeeded, 3 failed due to Qdrant lock)

### Engine Inventory

| Engine | Status | Files | LOC | Description |
|--------|--------|-------|-----|-------------|
| Engine 1 (Scraper) | Production | Apify config | External | Job board scraping via Apify actors |
| Engine 2 (Program Mapping) | Production | 4 scripts | ~1,200 | 7-stage pipeline: standardize → match → enrich → score → export |
| Engine 3 (OrgChart) | Production | 1 script | ~400 | 6-tier contact hierarchy classification |
| Engine 4 (Playbook) | Production | 1 script | ~800 | BD playbook + call sheet generation |
| Engine 5 (Scoring) | Production | 1 script | ~500 | 0-100 BD priority scoring algorithm |
| Engine 6 (QA) | Partial | Data + scripts | ~300 | Quality assurance alerting (review queue) |
| Engine 7 (Bullhorn ETL) | Production | SQLite + scripts | 293MB DB | CRM data extraction from Bullhorn |
| Engine 8 (Knowledge) | Production | 3,136 LOC api.py | ~8,000+ | Full AI knowledge system, RAG, vector search |

### Advanced System Inventory (Phases 31-50)

| Phase | System | File | LOC | Status |
|-------|--------|------|-----|--------|
| 31A | Streaming API | `src/api/streaming_api.py` | 14 REST + 4 WebSocket | Wired |
| 32A | Predictive Analytics | `src/api/predictive_api.py` | 14 endpoints | Wired |
| 33A | NLQ Engine | `src/api/nlq_api.py` | 9 endpoints | Wired |
| 34A | Relationship Engine | `src/api/relationship_api.py` | 14 endpoints | Wired |
| 35A | Proposal Generator | `src/api/proposal_api.py` | 10 endpoints | Wired |
| 36A | Revenue Analytics | `src/api/revenue_api.py` | 16 endpoints | Wired |
| 37A | Multi-Tenant | `src/api/tenant_api.py` | 21 endpoints | Wired |
| 38A | Data Quality | `src/api/data_quality_api.py` | 17 endpoints | Wired |
| 39A | Knowledge Management | `src/api/knowledge_api.py` | 15 endpoints | Wired |
| 40A | RAG Advanced | `src/api/rag_api.py` | 10 endpoints | Wired |
| 41A | Swarm Coordinator | `src/api/swarm_api.py` | 10 endpoints | Wired |
| 42A | Memory Cortex | `src/api/memory_api.py` | 12 endpoints | Wired |
| 43A | Data Governance | `src/api/governance_api.py` | 12 endpoints | Wired |
| 44A | Intelligence Suite | `src/api/intelligence_api.py` | 13 endpoints | Wired |
| 45A | MCP Ecosystem | `src/api/mcp_api.py` | 10 endpoints | Wired |
| 46A | Voice API | `src/api/voice_api.py` | 12 endpoints | Wired |
| 47A | Embeddings API | `src/api/embeddings_api.py` | 12 endpoints | Wired |
| 48A | Geo API | `src/api/geo_api.py` | 10 endpoints | Wired |
| 49A | Workflows API | `src/api/workflows_api.py` | 12 endpoints | Wired |
| 50A | Collaboration API | `src/api/collaboration_api.py` | 12 endpoints | Wired |

### Core Intelligence Systems

| System | File | LOC | Key Classes |
|--------|------|-----|-------------|
| Pattern Engine | `src/intelligence/pattern_engine.py` | 537 | StrategicPatternEngine, StrategicPattern, OpportunityScore, StrategicAlert |
| Meta-Learner | `src/intelligence/meta_learner.py` | 645 | BDMetaLearner, MetaInsight, InsightDomain (5 domains) |
| Insight Compiler | `src/intelligence/insight_compiler.py` | 488 | BDInsightCompiler, WeeklyBrief, MonthlyAssessment, FlashReport, CampaignReview |
| Swarm Coordinator | `src/agents/swarm/coordinator.py` | 546 | SwarmCoordinator, CoordinationMode (5 modes), WorkerResult |
| Task Decomposer | `src/agents/swarm/decomposer.py` | 348 | TaskDecomposer, SubTask, TaskDAG, TASK_TEMPLATES (5 templates) |
| Worker Registry | `src/agents/swarm/workers.py` | 363 | WorkerRegistry, WorkerAgent, WorkerType (8 types), WorkerStats |
| Memory Cortex | `src/memory/cortex.py` | 855 | UnifiedMemoryCortex, Memory, MemoryResult, MemoryType (3 tiers), ConsolidationReport |
| Opportunity Scorer | `src/ml/opportunity_scorer.py` | 463 | OpportunityScorer, ScoredOpportunity, DimensionScore, DIMENSION_WEIGHTS |
| Relationship Engine | `src/graph/relationship_engine.py` | 458 | RelationshipStrengthEngine, RelationshipScore, DecayingRelationship |
| MCP Orchestrator | `src/mcp/orchestrator.py` | 380 | MCPOrchestrator, MCPExecutionPlan, MCPExecutionStep, MCPExecutionResult |
| MCP Tool Registry | `src/mcp/tool_registry.py` | 657 | MCPToolRegistry, MCPServerConfig, MCPRoutingResult (9 servers) |
| Pipeline Orchestrator | `orchestrator.py` | 976 | BDOrchestrator, PipelineResult (11-stage pipeline) |
| Scheduler | `services/scheduler.py` | ~400 | SchedulerService, ScheduledRun, FileWatcher |

### Qdrant Vector Database

| Collection | Records | Description |
|------------|---------|-------------|
| contacts | 7,337 | CRM contacts with tier classification |
| programs | 401 | Federal programs and contracts |
| documents | 205 | Past performance, briefings |
| activities | 500 | Call notes, meeting records |
| jobs | 4 | Job postings with BD scores |
| **Total** | **8,447** | |

### Dashboard

- **47 pages** in the React + Vite dashboard (`dashboard/`)
- **TanStack Query** + manual hooks for data fetching
- **44 proxy routes** in `vite.config.ts`
- Serves on `http://localhost:5173`

### MCP Server

- **30+ MCP tools** in `mcp/knowledge-mcp-server/src/index.ts` (608 LOC)
- Tools: smart_ask, search_knowledge, semantic_search, hybrid_search, ask_knowledge, query_knowledge_graph, find_relationships, analyze_network, memory_add/search/get, ingest_program/company/contact, agent_program_intel/company_research/contact_finder/bd_strategy, workflow tools, system tools
- Proxied to BD API at :8100

---

## 3. OpenClaw-PTS: Architecture Analysis <a name="openclaw-analysis"></a>

### System Overview

| Component | Detail |
|-----------|--------|
| Gateway | WebSocket on `:18789` |
| LLM | Ollama `mistral:latest` (local, free) |
| Config | `config/openclaw.json` |
| Skills | 75+ auto-discovered in `skills/*/index.mjs` |
| Bridges | 3 MCP bridge servers (:3001-3003) |
| Memory | SQLite cognitive memory + local knowledge graph |
| Scheduling | Cron-based job scheduler |

### Bridge Servers

| Bridge | Port | Purpose | Git Remote |
|--------|------|---------|------------|
| n8n-builder | :3001 | Workflow automation | `n8n-builder` |
| data-scraper | :3002 | Data collection | `data-scraper` |
| auto-claude | :3003 | Orchestration | `auto-claude` |

### Existing Cron Jobs

| Schedule | Job | Description |
|----------|-----|-------------|
| 06:00 daily | Job scraping | Scrape job boards via Apify |
| 07:00 daily | Contact enrichment | Enrich new contacts |
| 08:00 Mon | Weekly HUMINT | Human intelligence gathering |
| 09:00 Mon | Call sheets | Generate call preparation sheets |
| Biweekly | Classification | Re-classify contacts |

### Git Repo Strategy

- 4 git remotes: n8n-builder, data-scraper, auto-claude, upstream
- Pull-only for 3 sub-repos (hub, scraper, builder)
- Push to origin for OpenClaw changes

### Autonomous Prompts (3 Specialized Agents)

1. **Workflow Agent** — n8n workflow creation and management
2. **Data Agent** — Data scraping and pipeline management
3. **Orchestration Agent** — Cross-system coordination

### Autonomous Task Definitions (5 Workflows)

Defined in `OPENCLAW_AUTONOMOUS_TASKS.json`:
1. Job scraping pipeline
2. Contact enrichment pipeline
3. HUMINT collection
4. Call sheet generation
5. Contact classification

### Health Check Protocol (HEARTBEAT.md)

Sequential health checks:
1. Check Ollama availability
2. Check engine status
3. Check pipeline state
4. Check intelligence systems
5. Generate health report

---

## 4. Real vs Simulated Assessment <a name="real-vs-simulated"></a>

### FULLY OPERATIONAL (Connected to Real Data)

| Component | Evidence | Data Source |
|-----------|----------|-------------|
| Engine8 Knowledge API | 100+ endpoints, serves real Qdrant data | Qdrant vector DB (8,447 records) |
| Pipeline Orchestrator | 7 runs on Feb 10, 11-stage pipeline | Jobs JSON → all 8 engines |
| Scheduler | Imports BDOrchestrator, calls `run_full_pipeline()` | File watchers, cron, retry logic |
| Dashboard Export | 6 JSON files written to `dashboard/public/data/` | Pipeline output data |
| Qdrant Collections | contacts (7,337), programs (401), documents (205), activities (500), jobs (4) | Bullhorn ETL + Notion sync |
| MCP Server | 30+ tools proxied to :8100 | BD API endpoints |
| Swarm API | 10 endpoints wired, routing logic works | coordinator.py algorithms |
| Intelligence API | 13 endpoints wired, algorithms work | pattern_engine.py, meta_learner.py |
| Memory API | 12 endpoints wired, algorithms work | cortex.py (in-memory) |
| Relationship API | 14 endpoints wired, algorithms work | relationship_engine.py |

### ALGORITHMS REAL, DATA MOCKED

#### Pattern Engine (src/intelligence/pattern_engine.py)
**Lines 98-156 contain hardcoded mock data:**
```python
_HIRING_DATA = [...]          # Mock hiring trends — 7 entries
_LEADERSHIP_EVENTS = [...]    # Mock leadership changes — 5 entries
_CONTRACT_MILESTONES = [...]  # Mock contract dates — 6 entries
_BUDGET_SIGNALS = [...]       # Mock budget data — 4 entries
_GEO_ACTIVITY = [...]         # Mock location data — 5 entries
_SKILL_DEMANDS = [...]        # Mock skill trends — 6 entries
_COMPETITOR_SHIFTS = [...]    # Mock competitor intelligence — 4 entries
```
**Fix:** Replace each hardcoded list with a Qdrant query:
- `_HIRING_DATA` → `qdrant.scroll("jobs", filter={"scraped_within": "90_days"})`
- `_LEADERSHIP_EVENTS` → `qdrant.scroll("contacts", filter={"role_changed": True})`
- `_CONTRACT_MILESTONES` → `qdrant.scroll("programs", filter={"pop_end_within": "180_days"})`
- `_BUDGET_SIGNALS` → `qdrant.scroll("programs", filter={"fiscal_year_transition": True})`
- `_COMPETITOR_SHIFTS` → `qdrant.scroll("jobs", filter={"is_competitor": True})`

#### Memory Cortex (src/memory/cortex.py)
**Lines 300-306 use in-memory dicts (lost on restart):**
```python
self._episodic: Dict[str, Memory] = {}      # All lost on restart
self._semantic: Dict[str, Memory] = {}      # All lost on restart
self._procedural: Dict[str, Memory] = {}    # All lost on restart
```
**Fix:** Create 3 new Qdrant collections:
- `episodic_memories` (1536-dim) — timestamped events with embedding vectors
- `semantic_facts` (1536-dim) — extracted entities and relationships
- `procedural_insights` (1536-dim) — strategy effectiveness patterns

#### Swarm Workers (src/agents/swarm/workers.py)
**Lines 122-179: `_default_execute()` returns empty placeholders:**
```python
def _default_execute(self, subtask: SubTask) -> Dict[str, Any]:
    if self.worker_type == WorkerType.RESEARCH.value:
        return {"findings": [], "contracts": [], "competitors": []}
    elif self.worker_type == WorkerType.CONTACT_DISCOVERY.value:
        return {"contacts_found": 0, "contacts": []}
    # ... all workers return empty placeholder results
```
**Fix:** Register actual executors via `registry.register_executor()` that call BD API endpoints.

### NOT IMPLEMENTED

None major — all core systems are present and functional. The 3 gaps above are the only barriers to full production operation.

### Known Issues

| Issue | Impact | Fix |
|-------|--------|-----|
| Qdrant concurrent access lock | 3/7 pipeline runs failed | Switch to server mode: `QDRANT_URL=http://localhost:6333` |
| Memory router commented out | `memory_router` on line 386 of api.py | Uncomment (memory_api.py is loaded via include pattern) |
| Pipeline state not persistent | `pipeline_state.json` overwrites each run | Already being addressed by scheduler |

---

## 5. Complete API Endpoint Inventory <a name="api-inventory"></a>

### Core API (Engine8_Knowledge/api.py — Direct Routes)

| Endpoint | Method | Purpose | Response Format |
|----------|--------|---------|----------------|
| `/health` | GET | System health check | `{"status": "healthy", "qdrant": {...}}` |
| `/stats` | GET | Collection statistics | `{"collections": {...}, "total_records": N}` |
| `/search` | GET/POST | Semantic search | `{"results": [...], "count": N}` |
| `/ask/smart` | POST | Smart Q&A with routing | `{"answer": "...", "query_type": "...", "systems_used": [...]}` |
| `/api/v2/contacts` | GET | Contact listing | `{"contacts": [...], "total": N}` |
| `/api/v2/programs` | GET | Program listing | `{"programs": [...], "total": N}` |
| `/api/v2/jobs` | GET | Job listing | `{"jobs": [...], "total": N}` |
| `/data/freshness` | GET | Collection freshness | `{"freshness": [{collection, last_updated, score}]}` |

### Swarm API (src/api/swarm_api.py — 10 Endpoints)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/swarm/execute` | POST | Full swarm execution |
| `/swarm/status/{swarm_id}` | GET | Live execution status |
| `/swarm/result/{swarm_id}` | GET | Completed result |
| `/swarm/decompose` | POST | Decompose task into DAG |
| `/swarm/dag/{dag_id}` | GET | Get DAG details |
| `/swarm/estimate` | POST | Cost/time estimate |
| `/swarm/workers` | GET | List all worker types |
| `/swarm/workers/{worker_type}/stats` | GET | Worker performance stats |
| `/swarm/history` | GET | Execution history |
| `/swarm/cancel/{swarm_id}` | POST | Cancel running swarm |

### Memory API (src/api/memory_api.py — 12 Endpoints)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/memory/store` | POST | Store new memory |
| `/memory/recall` | POST | Recall by query |
| `/memory/recall/context` | POST | Recall for agent context |
| `/memory/consolidate` | POST | Run memory consolidation |
| `/memory/reflect` | POST | Generate procedural insights |
| `/memory/forget` | POST | Run memory decay/forgetting |
| `/memory/stats` | GET | Memory statistics |
| `/memory/episodic/recent` | GET | Recent episodic memories |
| `/memory/semantic/facts` | GET | Key semantic facts |
| `/memory/procedural/insights` | GET | Procedural insights catalog |
| `/memory/search` | GET | Full-text memory search |
| `/memory/entity/{entity_id}/memories` | GET | Entity-specific memories |

### Intelligence API (src/api/intelligence_api.py — 13 Endpoints)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/intelligence/learn` | POST | Run meta-learning cycle |
| `/api/intelligence/insights` | GET | All current insights |
| `/api/intelligence/insights/{insight_type}` | GET | Insights by type |
| `/api/intelligence/patterns/scan` | POST | Run pattern recognition |
| `/api/intelligence/patterns/active` | GET | Active detected patterns |
| `/api/intelligence/opportunities` | GET | Scored BD opportunities |
| `/api/intelligence/transfer/{source}/{target}` | POST | Transfer learning |
| `/api/intelligence/brief/weekly` | POST | Generate weekly brief |
| `/api/intelligence/brief/monthly` | POST | Generate monthly assessment |
| `/api/intelligence/brief/flash` | POST | Generate flash report |
| `/api/intelligence/effectiveness/outreach` | GET | Outreach effectiveness metrics |
| `/api/intelligence/effectiveness/campaigns` | GET | Campaign effectiveness metrics |
| `/api/intelligence/trends/competitive` | GET | Competitive trend analysis |

### Relationship API (src/api/relationship_api.py — 14 Endpoints)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/relationships/score/{contact_a}/{contact_b}` | GET | Pairwise relationship strength |
| `/relationships/scores/{contact_id}` | GET | All relationships for contact |
| `/relationships/decaying` | GET | Relationships at risk of decay |
| `/relationships/influence/global` | GET | Global influence rankings |
| `/relationships/influence/program/{name}` | GET | Program-scoped influence |
| `/relationships/influence/{contact_id}/trend` | GET | Influence trajectory over time |
| `/relationships/path/{from_id}/{to_id}` | GET | Optimal introduction path |
| `/relationships/warm-intro/{target}` | GET | Warm introduction chain |
| `/relationships/missing-links/{program}` | GET | Network gaps for program |
| `/relationships/communities` | GET | Detected communities/clusters |
| `/relationships/bridges` | GET | Bridge contacts between groups |
| `/relationships/network-density` | GET | Network density report |
| `/relationships/network-growth` | GET | Growth trajectory |
| `/relationships/recompute` | POST | Force score recomputation |

### Other Phase APIs (Partial Listing)

| Router | Prefix | Endpoints | Phase |
|--------|--------|-----------|-------|
| Streaming | `/streaming/*` | 14 REST + 4 WebSocket | 31A |
| Predictive | `/predict/*` | 14 | 32A |
| NLQ | `/nlq/*` | 9 | 33A |
| Proposals | `/proposals/*` | 10 | 35A |
| Revenue | `/revenue/*` | 16 | 36A |
| Multi-Tenant | `/tenants/*` + `/auth/*` | 21 | 37A |
| Data Quality | `/data-quality/*` | 17 | 38A |
| Knowledge | `/knowledge/*` | 15 | 39A |
| RAG | `/rag/*` | 10 | 40A |
| Governance | `/governance/*` | 12 | 43A |
| MCP | `/api/mcp/*` | 10 | 45A |
| Voice | `/api/voice/*` | 12 | 46A |
| Embeddings | `/api/embeddings/*` | 12 | 47A |
| Geo | `/api/geo/*` | 10 | 48A |
| Workflows | `/api/workflows/*` | 12 | 49A |
| Collaboration | `/api/collab/*` | 12 | 50A |

**Total: 200+ API endpoints across 21 router modules**

### Dify Integration Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/dify/knowledge/search` | External knowledge search |
| `/dify/knowledge/rag` | RAG queries |
| `/dify/agents/invoke` | Invoke BD agents |
| `/dify/n8n/trigger/{workflow}` | Trigger n8n workflows |

### CrewAI Agent Endpoints

| Endpoint | Agent | Purpose |
|----------|-------|---------|
| `/agent/program` | ProgramIntelAgent | Full program intelligence report |
| `/agent/company` | CompanyResearchAgent | Company research |
| `/agent/contacts` | ContactFinderAgent | Find contacts |
| `/agent/strategy` | BDStrategyAgent | BD strategy analysis |

---

## 6. Exact Data Contracts & Interfaces <a name="data-contracts"></a>

### Pattern Engine Contracts

**PatternType Enum (7 types):**
```python
class PatternType(str, Enum):
    HIRING_SURGE = "hiring_surge"
    LEADERSHIP_CHANGE = "leadership_change"
    CONTRACT_MILESTONE = "contract_milestone"
    COMPETITIVE_SHIFT = "competitive_shift"
    BUDGET_SIGNAL = "budget_signal"
    GEOGRAPHIC_SHIFT = "geographic_shift"
    SKILL_DEMAND = "skill_demand"
```

**StrategicPattern Dataclass:**
```python
@dataclass
class StrategicPattern:
    pattern_id: str          # auto-generated hash
    pattern_type: str        # PatternType value
    title: str
    description: str
    entities: List[str]      # Programs, companies, contacts involved
    evidence: List[Dict]     # Supporting data points
    confidence: float        # 0.0-1.0
    detected_at: str         # ISO timestamp
    metadata: Dict[str, Any]
```

**OpportunityScore Dataclass:**
```python
@dataclass
class OpportunityScore:
    pattern_id: str
    score: int               # 0-100
    urgency: str             # "high" | "medium" | "low"
    win_probability: float   # 0.0-1.0
    recommended_actions: List[str]
    revenue_potential: str   # "$XXM"
```

**Key Method Signatures:**
```python
def scan_patterns() -> List[StrategicPattern]
def score_opportunity(pattern: StrategicPattern) -> OpportunityScore
def generate_alerts(min_score: int = 50) -> List[StrategicAlert]
def get_active_patterns() -> List[StrategicPattern]
def get_opportunities(min_score: int = 0) -> List[Dict[str, Any]]
```

### Swarm Decomposer Contracts

**5 DAG Templates (TASK_TEMPLATES):**

#### campaign_build (10 steps):
```python
[
    {"name": "Research program/contract details", "worker": "research", "depends": []},
    {"name": "Discover and validate contacts", "worker": "contact_discovery", "depends": []},
    {"name": "Analyze current job openings", "worker": "job_intel", "depends": []},
    {"name": "Find relevant past performance", "worker": "past_performance", "depends": []},
    {"name": "Classify contacts by tier and priority", "worker": "analytics", "depends": [1]},
    {"name": "Match jobs to contacts and programs", "worker": "analytics", "depends": [1, 2]},
    {"name": "Identify pain points from HUMINT data", "worker": "knowledge", "depends": [0]},
    {"name": "Craft personalized outreach messages", "worker": "outreach_crafter", "depends": [3, 4, 5, 6]},
    {"name": "Generate call sheet", "worker": "document_generator", "depends": [4, 7]},
    {"name": "Generate BD playbook", "worker": "document_generator", "depends": [0, 1, 2, 3, 4, 5, 6, 7]},
]
```

#### contact_enrichment (5 steps):
```python
[
    {"name": "Discover contacts from multiple sources", "worker": "contact_discovery", "depends": []},
    {"name": "Validate contact information", "worker": "contact_discovery", "depends": [0]},
    {"name": "Classify contacts by tier", "worker": "analytics", "depends": [1]},
    {"name": "Enrich with knowledge graph data", "worker": "knowledge", "depends": [1]},
    {"name": "Update CRM records", "worker": "document_generator", "depends": [2, 3]},
]
```

#### program_analysis (6 steps):
```python
[
    {"name": "Research program details and timeline", "worker": "research", "depends": []},
    {"name": "Analyze contracts and funding", "worker": "research", "depends": []},
    {"name": "Find program contacts", "worker": "contact_discovery", "depends": []},
    {"name": "Analyze related job postings", "worker": "job_intel", "depends": []},
    {"name": "Gather competitor intelligence", "worker": "research", "depends": [0]},
    {"name": "Generate analysis report", "worker": "document_generator", "depends": [0, 1, 2, 3, 4]},
]
```

#### weekly_briefing (5 steps):
```python
[
    {"name": "Scan for new job postings", "worker": "job_intel", "depends": []},
    {"name": "Check for contact changes", "worker": "contact_discovery", "depends": []},
    {"name": "Review contract updates", "worker": "research", "depends": []},
    {"name": "Summarize HUMINT data", "worker": "knowledge", "depends": []},
    {"name": "Generate weekly briefing document", "worker": "document_generator", "depends": [0, 1, 2, 3]},
]
```

#### competitive_analysis (6 steps):
```python
[
    {"name": "Research target competitor", "worker": "research", "depends": []},
    {"name": "Find competitor contracts", "worker": "research", "depends": [0]},
    {"name": "Identify competitor personnel", "worker": "contact_discovery", "depends": [0]},
    {"name": "Analyze competitor job postings", "worker": "job_intel", "depends": [0]},
    {"name": "Compare with our capabilities", "worker": "analytics", "depends": [1, 3]},
    {"name": "Generate competitive intel report", "worker": "document_generator", "depends": [0, 1, 2, 3, 4]},
]
```

### Opportunity Scorer Contracts

**Dimension Weights:**
```python
DIMENSION_WEIGHTS = {
    "win_probability": 0.30,      # 30%
    "revenue_potential": 0.20,    # 20%
    "strategic_fit": 0.15,        # 15%
    "relationship_strength": 0.15, # 15%
    "timing_urgency": 0.10,       # 10%
    "competitive_position": 0.10,  # 10%
}
```

**ScoredOpportunity Dataclass:**
```python
@dataclass
class ScoredOpportunity:
    opportunity_id: str
    title: str
    company: str
    program: str
    composite_score: float  # 0-100
    rank: int = 0
    dimensions: List[DimensionScore] = field(default_factory=list)
    recommended_approach: str = ""
    win_probability: float = 0.0
    scored_at: str = ""
```

**Input Dict Structure for `score_opportunity()`:**
```python
{
    "id": str,
    "title": str,
    "company": str,
    "program": str | "mapped_program": str,
    "description": str,
    "location": str,
    "estimated_value": float,
    "clearance": str,
    "contact_tier": int (1-6),
    "relationship_depth": int,
    "mutual_connections": int,
    "fiscal_quarter": int (1-4),
    "days_job_open": int,
    "days_to_pop_end": int,
    "is_option_year": bool,
    "pts_involvement": int (0-3),
    "competitor_density": int,
    "past_placements_on_program": int,
    "clearance_match": bool,
}
```

### Relationship Engine Contracts

**Dimension Weights:**
```python
DIMENSION_WEIGHTS = {
    "recency": 0.25,       # 25%
    "frequency": 0.20,     # 20%
    "quality": 0.20,       # 20%
    "reciprocity": 0.15,   # 15%
    "depth": 0.10,         # 10%
    "outcome": 0.10,       # 10%
}
```

**Interaction Quality Scores:**
```python
INTERACTION_QUALITY = {
    "meeting": 1.0,
    "in_person": 1.0,
    "video_call": 0.85,
    "call": 0.7,
    "phone": 0.7,
    "email": 0.4,
    "linkedin": 0.25,
    "message": 0.3,
    "referral": 0.9,
    "introduction": 0.85,
}
```

**Recency Half-Life:** `RECENCY_HALF_LIFE = 30` days (exponential decay)

**RelationshipScore Dataclass:**
```python
@dataclass
class RelationshipScore:
    contact_a: str
    contact_b: str
    total_score: float  # 0-100
    recency_score: float
    frequency_score: float
    quality_score: float
    reciprocity_score: float
    depth_score: float
    outcome_score: float
    factors: Dict[str, Any] = field(default_factory=dict)
    scored_at: str = ""
```

**DecayingRelationship Dataclass:**
```python
@dataclass
class DecayingRelationship:
    contact_a: str
    contact_b: str
    current_score: float
    days_since_contact: int
    projected_score_7d: float
    risk_level: str  # "critical" | "warning" | "watch"
    recommended_action: str
```

### Insight Compiler Contracts

**WeeklyBrief:**
```python
@dataclass
class WeeklyBrief:
    id: str                              # auto: "weekly_YYYYMMDD_HHMMSS"
    title: str
    period_start: str                    # "YYYY-MM-DD"
    period_end: str
    executive_summary: str
    sections: List[BriefSection]
    key_metrics: Dict[str, Any]
    top_opportunities: List[Dict[str, Any]]
    action_items: List[str]
    created_at: str
```

**MonthlyAssessment:**
```python
@dataclass
class MonthlyAssessment:
    id: str                              # auto: "monthly_YYYYMMDD_HHMMSS"
    title: str
    period: str                          # "YYYY-MM"
    executive_summary: str
    sections: List[BriefSection]
    trend_analysis: Dict[str, Any]
    strategic_recommendations: List[str]
    risk_factors: List[Dict[str, Any]]
    created_at: str
```

**FlashReport:**
```python
@dataclass
class FlashReport:
    id: str                              # auto: "flash_YYYYMMDD_HHMMSS"
    title: str
    pattern_id: str
    urgency: str                         # "high" | "urgent" | "medium"
    summary: str
    impact_assessment: str
    recommended_response: List[str]
    time_sensitivity: str
    created_at: str
```

**CampaignReview:**
```python
@dataclass
class CampaignReview:
    id: str                              # auto: "review_YYYYMMDD_HHMMSS"
    campaign_id: str
    title: str
    period: str
    summary: str
    effectiveness_score: float           # 0-100
    metrics: Dict[str, Any]
    what_worked: List[str]
    what_didnt: List[str]
    recommendations: List[str]
    created_at: str
```

**Key Methods:**
```python
compile_weekly_brief() -> WeeklyBrief
compile_monthly_assessment() -> MonthlyAssessment
compile_flash_report(pattern: StrategicPattern) -> FlashReport
compile_campaign_review(campaign_id: str = "") -> CampaignReview
```

### Memory Cortex Contracts

**Memory Dataclass:**
```python
@dataclass
class Memory:
    id: str
    memory_type: str        # "episodic" | "semantic" | "procedural"
    content: str
    entities: List[str]     # Auto-extracted via regex
    importance: float       # 0.0-1.0 computed score
    source: str
    timestamp: str
    metadata: Dict[str, Any]
```

**MemoryResult Dataclass:**
```python
@dataclass
class MemoryResult:
    memory: Memory
    relevance_score: float  # Combined: content_similarity × recency × importance
    source_tier: str        # "episodic" | "semantic" | "procedural"
```

**ConsolidationReport:**
```python
@dataclass
class ConsolidationReport:
    episodes_processed: int
    facts_extracted: int
    facts_new: int
    facts_updated: int
    insights_generated: int
    duration_ms: int
```

**Key Methods:**
```python
async def store(memory: Memory) -> str  # Returns memory_id
async def recall(query: str, memory_types: List[str], time_range, limit, min_score) -> List[MemoryResult]
async def consolidate(age_threshold_days: int = 7) -> ConsolidationReport
async def reflect() -> List[ProceduralInsight]
async def forget(max_age_days: int = 90) -> int  # Returns count forgotten
```

**Entity Extraction Patterns (built into cortex):**
- Programs: regex matches against Federal_Programs.csv names
- Organizations: matches against known contractor names (Leidos, GDIT, Northrop, etc.)
- Locations: city/state/base name matching
- People: Name-like patterns from contact data

### Swarm Worker Types

**8 Worker Types with Capabilities:**
```python
class WorkerType(str, Enum):
    RESEARCH = "research"
    CONTACT_DISCOVERY = "contact_discovery"
    JOB_INTEL = "job_intel"
    OUTREACH_CRAFTER = "outreach_crafter"
    DOCUMENT_GENERATOR = "document_generator"
    ANALYTICS = "analytics"
    PAST_PERFORMANCE = "past_performance"
    KNOWLEDGE = "knowledge"
```

**Worker Capabilities (from worker registry):**

| Worker | Tools | Output Fields | Avg Tokens | Keywords |
|--------|-------|---------------|------------|----------|
| research | search, rag, graph_query | findings, contracts, competitors | 2000 | research, analyze, investigate, details |
| contact_discovery | contact_search, notion_query | contacts_found, contacts | 1500 | contacts, people, who, personnel |
| job_intel | job_search, trend_analysis | jobs_found, mappings, trends | 1500 | jobs, postings, openings, hiring |
| outreach_crafter | template_gen, personalization | messages, templates | 3000 | outreach, email, message, engage |
| document_generator | playbook_gen, call_sheet_gen | documents, file_paths | 4000 | generate, create, document, report |
| analytics | analytics_query, predict | metrics, charts, predictions | 2000 | analyze, metrics, trends, predict |
| past_performance | doc_search, performance_query | contracts, evaluations | 1500 | past performance, CPARS, contracts |
| knowledge | rag_query, graph_traverse | answers, sources, graph | 2000 | knowledge, know, explain, understand |

### Coordination Modes

```python
class CoordinationMode(str, Enum):
    PARALLEL = "parallel"       # Independent steps run concurrently
    SEQUENTIAL = "sequential"   # Steps run in dependency order
    PIPELINE = "pipeline"       # Output of one feeds input of next
    CONSENSUS = "consensus"     # Multiple workers validate, majority wins
    MAP_REDUCE = "map_reduce"   # Split across workers, merge results
```

### MCP Orchestrator Contracts

**3 Plan Templates:**
```python
_PLAN_TEMPLATES = {
    "outreach_prep": [
        {"server_id": "mcp_notion", "tool_name": "query_database", "depends_on": []},
        {"server_id": "mcp_day_ai", "tool_name": "enrich_contact", "depends_on": ["step_0"]},
        {"server_id": "mcp_google_maps", "tool_name": "distance_matrix", "depends_on": ["step_0"]},
        {"server_id": "mcp_google_workspace", "tool_name": "draft_email", "depends_on": ["step_1"]},
        {"server_id": "mcp_slack", "tool_name": "send_message", "depends_on": ["step_3"]},
    ],
    "competitor_scan": [
        {"server_id": "mcp_notion", "tool_name": "query_database", "depends_on": []},
        {"server_id": "mcp_day_ai", "tool_name": "company_intel", "depends_on": ["step_0"]},
        {"server_id": "mcp_slack", "tool_name": "send_message", "depends_on": ["step_1"]},
    ],
    "meeting_prep": [
        {"server_id": "mcp_notion", "tool_name": "query_database", "depends_on": []},
        {"server_id": "mcp_day_ai", "tool_name": "enrich_contact", "depends_on": ["step_0"]},
        {"server_id": "mcp_google_workspace", "tool_name": "list_events", "depends_on": []},
        {"server_id": "mcp_memory", "tool_name": "recall_memory", "depends_on": []},
    ],
}
```

---

## 7. The Infinite Loop Architecture (OODA + Learn) <a name="infinite-loop"></a>

### The 5-Phase Autonomous Cycle

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                    THE INFINITE LOOP                              │
    │                                                                  │
    │   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
    │   │ OBSERVE  │───→│  ORIENT  │───→│  DECIDE  │───→│   ACT    │  │
    │   │          │    │          │    │          │    │          │  │
    │   │ Scrape   │    │ Pattern  │    │ Swarm    │    │ Skills   │  │
    │   │ Search   │    │ Engine   │    │ Decompose│    │ Execute  │  │
    │   │ Monitor  │    │ Meta-    │    │ Prioritze│    │ Pipeline │  │
    │   │ Scan     │    │ Learner  │    │ Score    │    │ Generate │  │
    │   └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
    │        ↑                                               │        │
    │        │          ┌──────────┐                          │        │
    │        └──────────│  LEARN   │←─────────────────────────┘        │
    │                   │          │                                    │
    │                   │ Outcomes │                                    │
    │                   │ Memory   │                                    │
    │                   │ Patterns │                                    │
    │                   │ Improve  │                                    │
    │                   └──────────┘                                    │
    └──────────────────────────────────────────────────────────────────┘
```

### What Each Phase Does

**OBSERVE** (Data Gathering — Continuous)
Uses: OpenClaw cron jobs + BD API + Notion MCP + git browsing
- Scrape job boards daily (existing cron: 6 AM)
- Query BD API `/stats` for collection health
- Read `pipeline_state.json` for run outcomes
- Scan Notion for new contacts/updates
- Monitor git repos for new commits
- Check SAM.gov for new contract opportunities
- Track competitor job postings

**ORIENT** (Pattern Recognition — After Each Observe)
Uses: BD Engine's `src/intelligence/pattern_engine.py` (7 patterns) + `meta_learner.py` (5 domains)
- Feed observations into pattern engine: detect HIRING_SURGE, LEADERSHIP_CHANGE, CONTRACT_MILESTONE, COMPETITIVE_SHIFT, BUDGET_SIGNAL, GEOGRAPHIC_SHIFT, SKILL_DEMAND
- Meta-learner analyzes across 5 domains: outreach effectiveness, program intelligence, contact behaviour, data quality, competitive intelligence
- Insight compiler produces weekly briefs, flash reports, campaign reviews
- Relationship engine scores all relationships 0-100 on 6 factors
- Opportunity scorer ranks all opportunities on 6 dimensions

**DECIDE** (Task Decomposition — Prioritized Queue)
Uses: BD Engine's `src/agents/swarm/decomposer.py` (5 templates) + `coordinator.py` (5 modes)
- Swarm decomposer breaks detected opportunities into task DAGs
- Priority queue ranked by opportunity score (0-100)
- Cost estimation per task (tokens, API cost, time)
- Budget gating: only execute if within daily token/cost budget

**ACT** (Execution — Via OpenClaw Skills + BD API)
Uses: OpenClaw 75+ skills + 3 bridge servers + BD API 200+ endpoints
- Swarm coordinator dispatches to 8 worker types
- 5 coordination modes: PARALLEL, SEQUENTIAL, PIPELINE, CONSENSUS, MAP_REDUCE
- Quality gating: only output results above threshold (default 0.7)

**LEARN** (Feedback + Improvement — After Each Act)
Uses: BD Engine's Memory Cortex + OpenClaw cognitive memory
- Every action generates an episodic memory (what happened, when, outcome)
- Pattern engine extracts semantic facts from episodes (what we know now)
- Meta-learner discovers procedural insights (what works)
- Relationship scores update based on new interactions
- Opportunity scores recalculate with new data
- Skill effectiveness tracked: which skills produce high-quality results?
- Strategy evaluation: which approach patterns lead to success?

---

## 8. Self-Discovery Mechanisms <a name="self-discovery"></a>

The system never runs out of things to do because it has **7 self-discovery mechanisms**:

### 1. Gap Detection (Runs: Daily)
```
Compare: What data SHOULD exist vs. what DOES exist
- Programs in Federal_Programs.csv (388) vs. indexed in Qdrant (401) → find unindexed
- Contacts in Notion (965+) vs. Qdrant (7,337) → find unsynchronized
- Jobs scraped today vs. mapped to programs → find unmapped
- Playbooks generated vs. hot opportunities → find uncovered opportunities
```
**Implementation:** New OpenClaw skill `self-discover` calls BD API `/stats`, Notion MCP, compares counts, generates gap report, creates tasks for each gap.

### 2. Staleness Detection (Runs: Daily)
```
For every data collection, track: last_updated, record_count, freshness_score
- Contacts not updated in 30+ days → trigger re-enrichment
- Programs with no recent job postings → investigate (winding down?)
- Playbooks older than 14 days → regenerate with fresh data
- Pipeline state showing errors → investigate and fix
```
**Implementation:** BD API `/data/freshness` endpoint + pattern engine's HIRING_SURGE/GEOGRAPHIC_SHIFT detection.

### 3. Pattern-Driven Discovery (Runs: After Each Observe)
```
Pattern engine detects:
- HIRING_SURGE on a program → auto-trigger campaign_build DAG
- LEADERSHIP_CHANGE detected → auto-trigger contact_enrichment DAG
- CONTRACT_MILESTONE approaching → auto-trigger competitive_analysis DAG
- COMPETITIVE_SHIFT (new entrant) → auto-trigger competitor research
- SKILL_DEMAND spike → alert + job mapping pipeline
```
**Implementation:** Wire `StrategicPatternEngine.scan_for_patterns()` to OpenClaw's task queue.

### 4. Relationship Decay Monitoring (Runs: Weekly)
```
Relationship engine calculates DecayingRelationship for all contacts:
- "critical" (score dropped below 20) → auto-generate outreach
- "warning" (score dropping fast) → schedule follow-up
- "watch" (gradual decline) → add to weekly brief
```
**Implementation:** `RelationshipStrengthEngine.detect_decaying()` → OpenClaw generates outreach drafts.

### 5. Cross-Repo Intelligence (Runs: Weekly)
```
Scan all 6 git repos for:
- New commits → what changed? Any new capabilities?
- Dead code → files not modified in 90+ days
- Dependency drift → shared patterns that diverged
- TODO/FIXME comments → potential improvement tasks
```

### 6. Knowledge Graph Expansion (Runs: Continuous)
```
Every piece of new data enriches the graph:
- New job posting → extract entities → add to graph
- New contact discovered → link to programs/companies → add to graph
- New past performance found → link to programs → add to graph
- Every /ask/smart query → extract new relationships → add to graph
```

### 7. Self-Performance Analysis (Runs: Weekly)
```
The system evaluates its own effectiveness:
- Which skills produce high-quality output? (quality_score tracking)
- Which worker types are fastest/cheapest? (token/latency tracking)
- Which patterns lead to actionable opportunities? (outcome tracking)
- Which outreach templates get responses? (response tracking)
- What data sources are most valuable? (impact scoring)
```

---

## 9. Execution Architecture <a name="execution-architecture"></a>

```
OPENCLAW GATEWAY (:18789)
    │
    ├── BRAIN BRIDGE (NEW) ──────→ BD API (:8100)
    │   │                            │
    │   ├── /ask/smart              │── Pattern Engine
    │   ├── /search                 │── Meta-Learner
    │   ├── /predict/*              │── Insight Compiler
    │   ├── /swarm/execute          │── Swarm Coordinator
    │   ├── /swarm/decompose        │── Task Decomposer
    │   ├── /relationships/*        │── Relationship Engine
    │   ├── /intelligence/*         │── Opportunity Scorer
    │   └── /memory/*               │── Memory Cortex
    │                                │
    ├── N8N Bridge (:3001) ──────── Workflow automation
    ├── Scraper Bridge (:3002) ──── Data collection
    ├── Auto-Claude Bridge (:3003) ─ Orchestration
    │
    ├── SKILL ENGINE (75+ skills)
    │   ├── bd-knowledge-query (NEW) → BD API bridge
    │   ├── autonomous-loop (NEW) ──→ OODA cycle controller
    │   ├── self-discover (NEW) ────→ Gap/staleness/pattern detection
    │   ├── swarm-dispatch (NEW) ──→ Task DAG execution
    │   ├── learn-feedback (NEW) ──→ Outcome → Memory → Improvement
    │   ├── meta-evolve (NEW) ─────→ Weekly self-improvement
    │   ├── bd-job-scraper ─────────── existing
    │   ├── bd-contact-classifier ──── existing
    │   ├── bd-outreach-composer ───── existing
    │   ├── intelligence-suite ─────── existing
    │   └── ... 65+ more
    │
    ├── CRON SCHEDULER
    │   ├── */30 * * * * ── OODA cycle (every 30 minutes)
    │   ├── 06:00 daily ─── Self-discover (gap + staleness + pattern scan)
    │   ├── 12:00 Wed ───── Data sync (Notion ↔ Qdrant)
    │   ├── 16:00 Fri ───── Weekly insights + briefing
    │   ├── 22:00 Sun ───── Cross-repo scan + self-analysis + meta-evolve
    │   └── CONTINUOUS ──── Event-driven triggers (new data → new tasks)
    │
    └── MEMORY SYSTEM
        ├── OpenClaw SQLite (cross-session facts, skill effectiveness)
        ├── BD Memory Cortex (episodic/semantic/procedural)
        ├── BD Qdrant (8,447+ vectors, persistent)
        └── OpenClaw cognitive-memory (local, PACAF data)
```

---

## 10. Precise API Wiring Map <a name="api-wiring"></a>

### OBSERVE Phase — Data Gathering Calls

| OpenClaw Skill | BD API Call | Returns | Purpose |
|----------------|------------|---------|---------|
| `bd-knowledge-query` | `GET /health` | `{"status": "healthy", "qdrant": {...}}` | System liveness |
| `bd-knowledge-query` | `GET /stats` | `{"collections": {...}, "total_records": N}` | Collection health |
| `bd-knowledge-query` | `GET /data/freshness` | `{"freshness": [{collection, last_updated, score}]}` | Staleness detection |
| `bd-knowledge-query` | `GET /search?collection=jobs&q=*&limit=50` | `{"results": [...], "count": N}` | New job postings |
| `bd-knowledge-query` | `GET /api/v2/contacts?limit=50&sort=updated_desc` | `{"contacts": [...], "total": N}` | Recent contact changes |
| `bd-knowledge-query` | `GET /api/v2/programs` | `{"programs": [...], "total": N}` | Program updates |
| `self-discover` | `GET /memory/stats` | Memory utilization | Knowledge graph density |
| Notion MCP | Notion API | Raw database records | External data sync |
| `meta-crawl` | `git log` across 6 repos | Commit diffs | Cross-repo intelligence |

### ORIENT Phase — Pattern Recognition Calls

| OpenClaw Skill | BD API Call | Returns | Purpose |
|----------------|------------|---------|---------|
| `autonomous-loop` | `POST /api/intelligence/patterns/scan` | `List[StrategicPattern]` | Detect 7 pattern types |
| `autonomous-loop` | `POST /api/intelligence/learn` | `List[MetaInsight]` | 5-domain meta-learning |
| `autonomous-loop` | `GET /api/intelligence/opportunities` | `List[ScoredOpportunity]` | Ranked opportunities |
| `autonomous-loop` | `GET /relationships/decaying` | `List[DecayingRelationship]` | At-risk relationships |
| `autonomous-loop` | `GET /relationships/influence/global` | Influence rankings | Key person identification |
| `autonomous-loop` | `GET /api/intelligence/trends/competitive` | Competitive trends | Market positioning |

### DECIDE Phase — Task Decomposition Calls

| OpenClaw Skill | BD API Call | Input | Returns |
|----------------|------------|-------|---------|
| `swarm-dispatch` | `POST /swarm/decompose` | `{"description": "...", "template": "campaign_build"}` | Task DAG with steps |
| `swarm-dispatch` | `POST /swarm/estimate` | `{"dag_id": "..."}` | `{cost, time, tokens}` |
| `autonomous-loop` | Budget check (local) | Current spend vs daily limit | Go/no-go decision |

### ACT Phase — Execution Calls

| Worker Type | BD API Endpoints Called | OpenClaw Skills Used |
|-------------|----------------------|---------------------|
| `research` | `/ask/smart`, `/search`, `/knowledge/query` | — |
| `contact_discovery` | `/api/v2/contacts`, `/relationships/scores/{id}` | Notion MCP for fresh data |
| `job_intel` | `/search?collection=jobs`, `/predict/trends` | `bd-job-scraper` |
| `outreach_crafter` | `/api/intelligence/brief/flash` | `bd-outreach-composer` |
| `document_generator` | — | `bd-call-sheet-gen`, Engine4 playbook |
| `analytics` | `/analytics/summary`, `/predict/*`, `/nlq/query` | — |
| `past_performance` | `/search?collection=documents` | — |
| `knowledge` | `/ask/smart`, `/knowledge/query`, `/rag/query` | — |

### LEARN Phase — Feedback Calls

| OpenClaw Skill | BD API Call | Input | Effect |
|----------------|------------|-------|--------|
| `learn-feedback` | `POST /memory/store` | `{type: "episodic", content, entities, outcome}` | Records what happened |
| `learn-feedback` | `POST /memory/consolidate` | `{age_threshold_days: 7}` | Episodes → semantic facts |
| `learn-feedback` | `POST /memory/reflect` | — | Extracts procedural insights |
| `learn-feedback` | `POST /relationships/recompute` | — | Updates all relationship scores |
| `learn-feedback` | `POST /api/intelligence/learn` | Platform activity data | Meta-learner cycle |
| `learn-feedback` | Local SQLite write | Skill execution stats | Skill effectiveness tracking |

---

## 11. Event-Driven Architecture <a name="event-driven"></a>

### Event Bus

```
┌─────────────────────────────────────────────────────────────┐
│                    EVENT BUS                                 │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ PIPELINE    │  │ API WEBHOOKS │  │ FILE WATCHERS    │   │
│  │ EVENTS      │  │              │  │                  │   │
│  │             │  │ n8n callback │  │ pipeline_state   │   │
│  │ run_complete│  │ Notion hook  │  │ alert_state      │   │
│  │ run_failed  │  │ SAM.gov feed │  │ outputs/*.json   │   │
│  │ new_data    │  │ git webhook  │  │ Engine6 QA       │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                │                    │             │
│         └────────────────┼────────────────────┘             │
│                          ▼                                  │
│              ┌──────────────────────┐                       │
│              │  EVENT DISPATCHER    │                       │
│              │                      │                       │
│              │  Route to:           │                       │
│              │  • self-discover     │                       │
│              │  • autonomous-loop   │                       │
│              │  • learn-feedback    │                       │
│              └──────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Event → Action Mappings

| Event | Source | Triggers | Priority |
|-------|--------|----------|----------|
| `pipeline_complete` | `orchestrator.py` writes `pipeline_state.json` | Learn phase: store outcomes, update scores | HIGH |
| `new_jobs_scraped` | n8n webhook (`outputs/n8n/*.json`) | Observe: feed to pattern engine | HIGH |
| `contact_updated` | Notion webhook | Orient: check relationship decay | MEDIUM |
| `pattern_detected` | Pattern engine scan | Decide: create swarm task | HIGH |
| `relationship_critical` | Relationship engine | Act: auto-generate outreach draft | HIGH |
| `budget_exhausted` | Budget tracker | Switch to free-only mode | IMMEDIATE |
| `qdrant_unhealthy` | Health check failure | Pause all write operations, alert | IMMEDIATE |
| `new_git_commit` | Git webhook/poll | Cross-repo intelligence scan | LOW |

### File Watchers

OpenClaw's `services/scheduler.py` has `FileWatcher` built in. Wire to:
```
Watch: outputs/pipeline_state.json    → on_change → learn-feedback skill
Watch: outputs/alert_state.json       → on_change → flash report generation
Watch: outputs/n8n/*.json             → on_new → observe phase (immediate)
Watch: Engine6_QA/data/review_queue.json → on_change → quality analysis
```

---

## 12. Failure Recovery & Resilience <a name="failure-recovery"></a>

### Failure Matrix

```
FAILURE TYPE              │ DETECTION          │ RECOVERY ACTION
──────────────────────────┼────────────────────┼──────────────────────────
BD API down (:8100)       │ Health check fails │ Queue tasks, retry in 5min
                          │                    │ Switch to free-only mode
                          │                    │ Use cached data in SQLite
──────────────────────────┼────────────────────┼──────────────────────────
Qdrant down (:6333)       │ Connection refused │ Pause ingestion
                          │                    │ Read-only from cache
                          │                    │ Alert to human
──────────────────────────┼────────────────────┼──────────────────────────
Swarm step fails          │ Worker returns err │ Try fallback worker type
                          │                    │ Skip step if non-critical
                          │                    │ Mark DAG as partial
──────────────────────────┼────────────────────┼──────────────────────────
Budget exceeded           │ Token counter      │ Immediate: stop paid calls
                          │                    │ Switch to free-only mode
                          │                    │ Resume at midnight reset
──────────────────────────┼────────────────────┼──────────────────────────
Pattern false positive    │ Low confidence     │ Require 3+ evidence points
                          │                    │ Mark as "unverified"
                          │                    │ Demote in priority queue
──────────────────────────┼────────────────────┼──────────────────────────
OpenClaw gateway crash    │ Process monitor    │ Auto-restart via systemd
                          │                    │ Resume from task queue
                          │                    │ Memory persisted in Qdrant
──────────────────────────┼────────────────────┼──────────────────────────
Concurrent Qdrant lock    │ "Already accessed" │ Switch to server mode
                          │ error              │ (QDRANT_URL=localhost:6333)
```

### Circuit Breaker Pattern

Each external dependency has a circuit breaker:
```
CLOSED (healthy) ──→ failures > 3 in 5min ──→ OPEN (broken)
                                                    │
                                              wait 30 seconds
                                                    │
                                              HALF-OPEN (testing)
                                                    │
                                            success? → CLOSED
                                            failure? → OPEN
```

Applied to: BD API, Qdrant, Notion API, n8n webhooks, Ollama LLM

### Task Queue Persistence

```
File: openclaw/data/task_queue.json
Format: [{task_id, description, priority_score, dag_template, estimated_cost,
          created_at, status, attempts, last_error}]
```
On restart, queue is loaded and execution resumes from where it left off.

---

## 13. Monitoring & Observability <a name="monitoring"></a>

### System Health Dashboard

```
┌────────────────────── AUTONOMOUS HEALTH ──────────────────────┐
│                                                               │
│  OODA Cycles Today: 14        │  Budget Used: 287K / 500K    │
│  Tasks Completed: 8           │  API Calls: 142 / 200        │
│  Tasks Failed: 1              │  Pipeline Runs: 1 / 3        │
│  Tasks Queued: 12             │  Qdrant Ingests: 34 / 100    │
│                               │                               │
│  Pattern Detections: 3        │  Memory Stats:                │
│  • HIRING_SURGE (DCGS) ⬆     │  • Episodic: 847 memories    │
│  • COMPETITIVE_SHIFT ⬆        │  • Semantic: 234 facts       │
│  • BUDGET_SIGNAL (FY26) ⬆     │  • Procedural: 18 insights   │
│                               │                               │
│  Top Opportunity:             │  Learning:                    │
│  DCGS-PACAF: 87/100          │  • Best skill: research (0.9) │
│  Next Action: campaign_build  │  • Worst: outreach (0.4)     │
│                               │  • Improving: +0.05/cycle    │
│                               │                               │
│  System Health:               │  Self-Discovery:              │
│  ✅ BD API     ✅ Qdrant      │  • 3 gaps found today        │
│  ✅ Notion     ✅ n8n         │  • 2 stale datasets          │
│  ✅ Ollama     ✅ OpenClaw    │  • 1 relationship critical   │
└───────────────────────────────┴───────────────────────────────┘
```

### Metrics Tracked

| Metric | Stored In | Updated | Used By |
|--------|-----------|---------|---------|
| `cycles_completed` | OpenClaw SQLite | Every 30min | Health dashboard |
| `tasks_by_status` | Task queue JSON | Real-time | Decide phase |
| `budget_remaining` | OpenClaw SQLite | After each API call | Budget gating |
| `skill_quality_scores` | OpenClaw SQLite | After each execution | Meta-evolve |
| `pattern_accuracy` | BD Memory Cortex | After outcome verification | Pattern engine tuning |
| `opportunity_outcomes` | BD Memory Cortex | After task completion | Scorer weight adjustment |
| `relationship_delta` | BD API | Weekly | Decay monitoring |
| `data_freshness` | BD API `/data/freshness` | Daily | Staleness detection |
| `knowledge_graph_size` | Qdrant `/stats` | Daily | Coverage tracking |
| `error_rate_by_worker` | OpenClaw SQLite | After each execution | Worker selection |

### Alerting (To Human)

| Condition | Channel | Urgency |
|-----------|---------|---------|
| Budget > 80% | Slack #bd-team | Warning |
| Budget exhausted | Slack #bd-team | Alert |
| Qdrant unhealthy | Slack #bd-team | Critical |
| BD API down > 15min | Slack #bd-team | Critical |
| Tier 3 action pending | Slack DM to owner | Approval needed |
| Flash report generated | Email + Slack | Informational |
| Weekly brief ready | Email | Informational |
| Self-improvement PR created | GitHub notification | Review needed |

---

## 14. Self-Improvement Flywheel <a name="self-improvement"></a>

This is what makes it "Claude Code x10000" — every cycle makes the next cycle better:

```
Cycle 1: Scrape 50 jobs → Map to programs → Score opportunities → Generate 3 playbooks
         Learn: "DCGS-PACAF had 80% match rate, GBSD had 20%"
         Improve: Increase DCGS weight in opportunity scorer

Cycle 2: Scrape 50 jobs → Map (better DCGS matching) → Score → Generate 5 playbooks
         Learn: "LinkedIn outreach to Tier 3 contacts had 40% response"
         Improve: Prioritize Tier 3 LinkedIn in outreach strategy

Cycle 3: Scrape 50 jobs → Map → Score → Generate outreach (LinkedIn-first for Tier 3)
         Learn: "Monday morning outreach has 2x open rate vs. Friday"
         Improve: Schedule outreach for Monday morning

Cycle N: System has accumulated N cycles of learning → scoring is precise,
         outreach is optimized, timing is perfect, coverage is complete
```

### What Gets Better Each Cycle:
1. **Pattern detection accuracy** — more data = more signal = fewer false positives
2. **Opportunity scoring** — outcome tracking validates/adjusts scoring weights
3. **Outreach effectiveness** — A/B testing of channels, timing, templates
4. **Relationship mapping** — network grows richer with every interaction
5. **Data quality** — self-healing fills gaps, corrects errors
6. **Knowledge graph density** — every query extracts new entities and relationships
7. **Skill prompts** — meta-evolve rewrites prompts based on quality scores
8. **Task prioritization** — learns which tasks produce highest ROI

---

## 15. Safety & Governance <a name="safety"></a>

### Budget Control (Hard Limits)
```
DAILY_TOKEN_BUDGET = 500,000 tokens (~$5)
DAILY_API_CALLS = 200 calls to BD API
DAILY_PIPELINE_RUNS = 3 (test mode only)
DAILY_INGEST_LIMIT = 100 records to Qdrant
```
When budget is exhausted, system switches to free-only actions (local analysis, report generation, git scanning, memory consolidation).

### Write Safety Tiers
```
TIER 1 - AUTONOMOUS (no approval):
  - Read any API endpoint
  - Read any git repo or Notion database
  - Generate reports and analysis
  - Store in OpenClaw memory
  - Create openclaw/* branches
  - Update local knowledge graph
  - Execute free-tier skills

TIER 2 - AUTO-APPROVED (within budget):
  - Call BD API /ask/smart, /search (costs tokens)
  - Run pipeline in test mode
  - Generate and store briefings
  - Update opportunity/relationship scores

TIER 3 - HUMAN APPROVAL REQUIRED:
  - Write to BD Qdrant (ingest endpoints)
  - Run full pipeline (not test mode)
  - Create PRs
  - Send outreach to real people
  - Modify any source code
  - Delete any data

TIER 4 - NEVER:
  - Push to develop/main branches
  - Send emails/messages to external people without approval
  - Modify production configurations
  - Run destructive operations
```

### Anti-Hallucination Guards
- Every fact stored in memory includes: source, timestamp, confidence (0-1)
- Facts below 0.5 confidence are flagged as "unverified"
- Conflicting facts trigger investigation tasks
- No action taken based solely on a single unverified source
- Pattern engine requires 3+ evidence points before generating an alert

---

## 16. 6 New Skills: Complete Specifications <a name="skill-specs"></a>

### Skill 1: `bd-knowledge-query` (BD API Bridge)

```
Location: OpenClaw-PTS/skills/bd-knowledge-query/index.mjs
Dependencies: node-fetch (or built-in fetch), better-sqlite3
Config: BD_API_URL=http://localhost:8100

Interface:
  Input:  { endpoint: string, method: "GET"|"POST", params?: object, body?: object }
  Output: { success: boolean, data: any, cached: boolean, latency_ms: number }

Caching:
  - SQLite DB at openclaw/data/bd_cache.db
  - Table: cache(key TEXT PK, response TEXT, created_at INT, ttl_seconds INT)
  - GET requests cached for 15 minutes
  - POST requests never cached
  - Cache key: md5(endpoint + JSON.stringify(params))

Circuit Breaker:
  - State file: openclaw/data/circuit_breakers.json
  - Per-endpoint tracking: { failures: 0, state: "closed", last_failure: null }
  - Opens after 3 consecutive failures within 5 minutes
  - Half-open test after 30 seconds
  - Resets on success

Error Handling:
  - API timeout (10s): return cached result if available, else error
  - 5xx response: increment circuit breaker, return cached
  - 4xx response: return error (don't cache errors)
  - Network error: increment circuit breaker, return cached
```

### Skill 2: `autonomous-loop` (Master Controller)

```
Location: OpenClaw-PTS/skills/autonomous-loop/index.mjs
Dependencies: bd-knowledge-query, self-discover, swarm-dispatch, learn-feedback

State Files:
  - openclaw/data/loop_state.json    → { cycle_count, last_run, phase, errors }
  - openclaw/data/budget.json        → { daily_tokens: 500000, used_tokens: 0,
                                          daily_api_calls: 200, used_calls: 0,
                                          reset_at: "2026-02-11T00:00:00Z" }
  - openclaw/data/task_queue.json    → [{task_id, description, priority, template, cost, status}]

Execution Flow:
  1. BUDGET CHECK: Read budget.json. If exhausted → free-only mode
  2. OBSERVE: Call bd-knowledge-query for /health, /stats, /data/freshness
  3. ORIENT: Call bd-knowledge-query for /api/intelligence/patterns/scan,
             /api/intelligence/learn, /relationships/decaying
  4. DECIDE: Read task_queue.json, sort by priority/cost ratio, pick top task
  5. ACT: Call swarm-dispatch with selected task
  6. LEARN: Call learn-feedback with execution result
  7. UPDATE: Write loop_state.json, budget.json

Free-Only Mode Actions:
  - Memory consolidation (POST /memory/consolidate)
  - Memory reflection (POST /memory/reflect)
  - Git repo scanning (local git commands, zero API cost)
  - Report generation from cached data
  - Skill stats analysis (local file reads)
  - Task queue re-prioritization (local computation)
```

### Skill 3: `self-discover` (Self-Discovery Engine)

```
Location: OpenClaw-PTS/skills/self-discover/index.mjs
Dependencies: bd-knowledge-query

Output: Writes scored tasks to openclaw/data/task_queue.json

7 Discovery Functions:

1. gapDetect():
   - Call GET /stats → get collection counts
   - Compare vs expected: programs ≥ 388, contacts ≥ 965
   - For each gap: create task {template: "contact_enrichment", priority: 60}

2. stalenessDetect():
   - Call GET /data/freshness → get per-collection freshness scores
   - Any collection with freshness < 0.5: create task {template: "program_analysis", priority: 50}
   - Playbooks older than 14 days: create task {template: "campaign_build", priority: 40}

3. patternDiscovery():
   - Call POST /api/intelligence/patterns/scan → get StrategicPattern list
   - HIRING_SURGE → create task {template: "campaign_build", priority: 80}
   - LEADERSHIP_CHANGE → create task {template: "contact_enrichment", priority: 75}
   - CONTRACT_MILESTONE → create task {template: "competitive_analysis", priority: 70}
   - COMPETITIVE_SHIFT → create task {template: "competitive_analysis", priority: 65}

4. decayMonitor():
   - Call GET /relationships/decaying → get DecayingRelationship list
   - "critical" → create task {template: "contact_enrichment", priority: 85, auto_outreach: true}
   - "warning" → create task {template: "contact_enrichment", priority: 55}

5. crossRepoScan():
   - For each of 6 git remotes: git log --oneline --since="7 days ago"
   - New capabilities detected → create task {type: "investigate_capability", priority: 30}
   - New TODO/FIXME → create task {type: "code_improvement", priority: 20}

6. graphExpansion():
   - Call GET /memory/semantic/facts → get known entities
   - Call GET /memory/episodic/recent → get recent events
   - Entities in episodes not in semantic facts → create extraction tasks (priority: 25)

7. selfAnalysis():
   - Read openclaw/data/skill_stats.json
   - Skills with quality < 0.5 after 10+ runs → create task {type: "skill_improvement", priority: 35}
   - Skills with error_rate > 0.3 → create task {type: "skill_debug", priority: 45}
```

### Skill 4: `swarm-dispatch` (Task Executor)

```
Location: OpenClaw-PTS/skills/swarm-dispatch/index.mjs
Dependencies: bd-knowledge-query

Input: { task_id: string } (reads from task_queue.json)

Execution Flow:
  1. Read task from queue, mark as "running"
  2. POST /swarm/decompose → get DAG
  3. POST /swarm/estimate → get cost estimate
  4. Budget check: if cost > remaining budget → mark "deferred", pick cheaper task
  5. POST /swarm/execute → start execution
  6. Poll GET /swarm/status/{id} every 5s until complete
  7. GET /swarm/result/{id} → get final results
  8. Update task in queue: status, result_summary, quality_score
  9. Update budget.json: deduct tokens/calls used
  10. Return result to caller (autonomous-loop → learn-feedback)

Quality Gate:
  - Each step result has quality_score (0-1)
  - Steps below 0.7 are flagged but not failed
  - If > 50% of steps below 0.5 → mark task as "low_quality"
  - Low-quality tasks trigger investigation in next self-discover cycle
```

### Skill 5: `learn-feedback` (Learning Engine)

```
Location: OpenClaw-PTS/skills/learn-feedback/index.mjs
Dependencies: bd-knowledge-query

Input: { task_id: string, result: object, quality_score: number }

Learning Pipeline:
  1. EPISODIC: POST /memory/store
     Body: { type: "episodic", content: "<task description + outcome>",
             entities: [extracted from result], importance: quality_score }

  2. CONSOLIDATION: POST /memory/consolidate
     Body: { age_threshold_days: 7 }
     (Runs every 10th invocation to avoid overhead)

  3. REFLECTION: POST /memory/reflect
     (Runs every 20th invocation)
     → Returns procedural insights → stored automatically

  4. RELATIONSHIP UPDATE: POST /relationships/recompute
     (Only if task involved contacts)

  5. SKILL STATS: Update openclaw/data/skill_stats.json
     Per skill: increment invocations, update avg_quality, avg_latency, avg_cost

  6. OUTCOME TRACKING: Append to openclaw/data/outcomes.json
     { task_id, dag_template, target_entity, quality_score, tokens_used, timestamp }
     (Used by meta-evolve for strategy analysis)
```

### Skill 6: `meta-evolve` (Self-Improvement Engine)

```
Location: OpenClaw-PTS/skills/meta-evolve/index.mjs
Dependencies: bd-knowledge-query, learn-feedback

Schedule: Weekly (Sunday 22:00)

Analysis Pipeline:
  1. READ skill_stats.json → compute per-skill trends over 30 days
  2. READ outcomes.json → compute per-template success rates
  3. Call GET /memory/procedural/insights → get strategy patterns
  4. Call GET /api/intelligence/effectiveness/outreach → outreach metrics
  5. Call GET /api/intelligence/effectiveness/campaigns → campaign metrics

Output: openclaw/data/improvement_proposals.json
Format: [{
  id: string,
  type: "prompt_revision" | "dag_optimization" | "new_skill" | "data_source" | "schedule_change",
  target: string (skill name or template name),
  current_performance: { quality, latency, cost },
  proposed_change: string (description),
  estimated_impact: string,
  requires_approval: boolean (true for Tier 3+ actions),
  created_at: string
}]

Auto-Deploying (Tier 1-2 only):
  - Schedule optimizations (shift cron times based on success patterns)
  - Priority weight adjustments (increase weight for high-ROI task types)
  - Cache TTL adjustments (longer cache for stable data, shorter for volatile)

Human Approval Required (Tier 3):
  - New skill proposals
  - Skill prompt rewrites
  - DAG template modifications
  - New data source integrations
```

---

## 17. Implementation Phases <a name="implementation"></a>

### Phase 1: Connect the Brain to the Body

**Goal:** OpenClaw can query BD Engine and BD Engine returns real data.

**Step 1.1: Fix Qdrant Concurrent Access**
- **File:** `.env` (BD-Automation-Engine root)
- **Change:** Set `QDRANT_URL=http://localhost:6333` to use server mode
- **Why:** 3/7 pipeline runs failed with "Storage folder already accessed by another instance"
- **Verify:** Two concurrent `GET /search` calls succeed without lock errors

**Step 1.2: Persist Memory Cortex to Qdrant**
- **File:** `src/memory/cortex.py` (lines 300-306)
- **Change:** Replace `self._episodic: Dict[str, Memory] = {}` with Qdrant operations
- **Create 3 collections:** `episodic_memories` (1536-dim), `semantic_facts` (1536-dim), `procedural_insights` (1536-dim)
- **Migration:** `store()` → `qdrant.upsert()`, `recall()` → `qdrant.search()`, `consolidate()` → batch process + upsert
- **Verify:** `POST /memory/store` → `POST /memory/recall` returns the stored memory; survives API restart

**Step 1.3: Wire Pattern Engine to Real Data**
- **File:** `src/intelligence/pattern_engine.py` (lines 98-156)
- **Change:** Replace 7 hardcoded arrays with Qdrant queries
- **Each scanner method** (`_scan_hiring_surges`, etc.) queries the appropriate collection
- **Verify:** `POST /api/intelligence/patterns/scan` returns patterns based on actual Qdrant data (not mock)

**Step 1.4: Create `bd-knowledge-query` Skill in OpenClaw**
- **Location:** `OpenClaw-PTS/skills/bd-knowledge-query/index.mjs`
- **Implements:** HTTP client wrapper for all BD API endpoints
- **Caching:** Local SQLite cache with 15min TTL for read endpoints
- **Error handling:** Circuit breaker with 3-failure threshold, 30s cooldown
- **Verify:** From OpenClaw gateway, call skill → gets response from BD API `/ask/smart`

**Step 1.5: Register Real Swarm Worker Executors**
- **File:** `src/agents/swarm/workers.py` (lines 122-179)
- **Change:** Replace `_default_execute()` placeholder responses with actual BD API calls
- **Verify:** `POST /swarm/execute` with `campaign_build` template returns real data from Qdrant

### Phase 2: Build the Autonomous Loop

**Goal:** System runs the OODA cycle automatically, discovers its own work.

**Step 2.1:** Create `autonomous-loop` skill (master controller with budget tracking)
**Step 2.2:** Create `self-discover` skill (7 discovery mechanisms)
**Step 2.3:** Implement priority queue (scored tasks sorted by value/cost ratio)
**Step 2.4:** Wire cron schedule (OODA every 30min, self-discover daily, weekly brief Friday, meta-evolve Sunday)
**Verify:** System runs for 2 hours, discovers at least 1 gap, creates a task, shows it in queue

### Phase 3: Wire the Swarm to OpenClaw

**Goal:** Swarm coordinator dispatches real work through OpenClaw skills.

**Step 3.1:** Create `swarm-dispatch` skill
**Step 3.2:** Map worker types to OpenClaw skills + BD API endpoints
**Step 3.3:** Test all 5 DAG templates end-to-end with real programs

### Phase 4: Activate Learning

**Goal:** Every action feeds back. Second cycle outperforms first.

**Step 4.1:** Create `learn-feedback` skill
**Step 4.2:** Wire opportunity scorer to real outcomes
**Step 4.3:** Implement skill effectiveness scoring

### Phase 5: Self-Evolution

**Goal:** System improves its own prompts, strategies, and capabilities.

**Step 5.1:** Create `meta-evolve` skill
**Step 5.2:** Prompt optimization via A/B testing
**Step 5.3:** DAG template evolution based on step success rates
**Step 5.4:** New capability proposals when gaps can't be filled

---

## 18. Verification Plan <a name="verification"></a>

### Phase 1: Brain-Body Connectivity

| Test | Command | Expected Result | Pass Criteria |
|------|---------|----------------|---------------|
| V1.1 | `curl http://localhost:8100/health` | `{"status": "healthy"}` | 200 OK |
| V1.2 | `curl http://localhost:8100/stats` | Collection counts | contacts > 7000 |
| V1.3 | `curl -X POST http://localhost:8100/api/intelligence/patterns/scan` | Pattern array | Returns real patterns (not hardcoded) |
| V1.4 | `curl -X POST http://localhost:8100/memory/store -d '...'` | Memory ID | Returns valid ID |
| V1.5 | Restart API → recall memory | Previous memory | Survives restart |
| V1.6 | OpenClaw `bd-knowledge-query` | Smart answer | Non-empty answer |
| V1.7 | Two concurrent `/search` calls | Both succeed | No lock errors |

### Phase 2: Autonomous Loop

| Test | Command | Expected Result | Pass Criteria |
|------|---------|----------------|---------------|
| V2.1 | Run `self-discover` | Task queue populated | ≥ 3 tasks created |
| V2.2 | Check `task_queue.json` | Scored tasks | All valid |
| V2.3 | Run `autonomous-loop` once | Complete OODA cycle | cycle_count: 1 |
| V2.4 | Budget near limit | Free-only mode | No API calls |
| V2.5 | Let loop run 2 hours | Multiple cycles | ≥ 4 cycles |

### Phase 3: Swarm Execution

| Test | Command | Expected Result | Pass Criteria |
|------|---------|----------------|---------------|
| V3.1 | `POST /swarm/decompose` | 10-step DAG | All steps typed |
| V3.2 | `POST /swarm/execute` | Real results | Qdrant data returned |
| V3.3 | `campaign_build` end-to-end | Playbook generated | Real program data |
| V3.4 | `weekly_briefing` | Brief generated | All 5 sections |
| V3.5 | Fail one step | Partial completion | Other steps complete |

### Phase 4: Learning

| Test | Command | Expected Result | Pass Criteria |
|------|---------|----------------|---------------|
| V4.1 | Complete task → check episodic | New memory | Contains outcome |
| V4.2 | `POST /memory/consolidate` | Facts extracted | facts_extracted > 0 |
| V4.3 | `POST /memory/reflect` | Insights | ≥ 1 insight |
| V4.4 | Check `skill_stats.json` | Metrics | Tracked |
| V4.5 | Cycle 1 → Cycle 2 | Priorities differ | Learning visible |

### End-to-End

| Test | Duration | Expected Outcome |
|------|----------|-----------------|
| E2E-1 | 24 hours | 48+ OODA cycles |
| E2E-2 | 24 hours | ≥ 5 tasks completed |
| E2E-3 | 24 hours | Memory grows (episodic ≥ 50) |
| E2E-4 | 24 hours | Budget respected |
| E2E-5 | 1 week | ≥ 3 improvement proposals |
| E2E-6 | 1 week | Measurable skill quality trends |

---

## 19. Key Files Reference <a name="key-files"></a>

### BD-Automation-Engine (The Brain)

| File | LOC | Role |
|------|-----|------|
| `Engine8_Knowledge/api.py` | 3,136 | Central API — all brain queries go through here |
| `src/intelligence/pattern_engine.py` | 537 | ORIENT: Detects 7 strategic patterns |
| `src/intelligence/meta_learner.py` | 645 | ORIENT: Analyzes 5 intelligence domains |
| `src/intelligence/insight_compiler.py` | 488 | ORIENT: Compiles executive briefings |
| `src/agents/swarm/coordinator.py` | 546 | DECIDE+ACT: Orchestrates 8 worker types |
| `src/agents/swarm/decomposer.py` | 348 | DECIDE: Breaks tasks into DAGs (5 templates) |
| `src/agents/swarm/workers.py` | 363 | ACT: 8 specialized worker definitions |
| `src/memory/cortex.py` | 855 | LEARN: 3-tier memory (episodic/semantic/procedural) |
| `src/ml/opportunity_scorer.py` | 463 | DECIDE: 6-dimension opportunity ranking |
| `src/graph/relationship_engine.py` | 458 | ORIENT: 6-factor relationship scoring |
| `src/mcp/orchestrator.py` | 380 | ACT: Multi-tool DAG execution |
| `src/mcp/tool_registry.py` | 657 | ACT: 9 MCP servers, intelligent routing |
| `orchestrator.py` | 976 | ACT: Pipeline execution (11 stages) |
| `services/scheduler.py` | ~400 | ACT: Cron-based pipeline scheduling |
| `src/api/swarm_api.py` | - | 10 swarm endpoints |
| `src/api/memory_api.py` | - | 12 memory endpoints |
| `src/api/intelligence_api.py` | - | 13 intelligence endpoints |
| `src/api/relationship_api.py` | - | 14 relationship endpoints |

### OpenClaw-PTS (The Body)

| File | Role |
|------|------|
| `config/openclaw.json` | Gateway config (Ollama, ports) |
| `bridges/{n8n-builder,data-scraper,auto-claude}/` | 3 MCP bridge servers |
| `skills/*/index.mjs` | 75+ auto-discovered execution skills |
| `cron/*.json` | Scheduled autonomous jobs |
| `data/cognitive-memory/` | Local persistent memory |
| `data/knowledge-graph/` | Local knowledge graph |
| `OPENCLAW_AUTONOMOUS_TASKS.json` | 5 workflow definitions |
| `OPENCLAW_AUTONOMOUS_PROMPTS.md` | 3 agent system prompts |
| `HEARTBEAT.md` | Health check protocol |
| `GIT_REPO_AND_AUTO_CLAUDE_STRATEGY.md` | Git multi-remote strategy |

### New Skills to Create (in OpenClaw)

| Skill | Purpose | Key Endpoints |
|-------|---------|---------------|
| `bd-knowledge-query` | BD API bridge (all queries) | All 200+ BD API endpoints |
| `autonomous-loop` | OODA cycle master controller | /health, /intelligence/*, /swarm/* |
| `self-discover` | 7 self-discovery mechanisms | /stats, /data/freshness, /relationships/decaying |
| `swarm-dispatch` | Task DAG execution | /swarm/decompose, /swarm/execute, /swarm/status |
| `learn-feedback` | Outcome → memory → improvement | /memory/store, /memory/consolidate, /memory/reflect |
| `meta-evolve` | Weekly self-improvement | /intelligence/effectiveness/*, /memory/procedural/insights |

---

---

## 20. Pipeline Deep Dive: 11-Stage Orchestrator <a name="pipeline-deep-dive"></a>

### Stage-by-Stage Data Transforms

The master orchestrator (`orchestrator.py`, 976 LOC) coordinates 11 distinct stages:

**Stage 1: INGEST**
- Load raw JSON from Engine1_Scraper output
- Validate file structure and JSON schema
- Returns list of job dictionaries

**Stage 2: PROGRAM MAPPING** (Engine2)
- Execute Engine2's 7-stage sub-pipeline (see Section 21)
- Multi-signal scoring for job-to-program matching
- Direct matches (confidence >= 0.70), Fuzzy (0.50-0.70), Inferred (<0.50)

**Stage 3: BD SCORING** (Engine5)
- Base score: 50 points
- Clearance boost: 0-35 points
- Program boost: 0-15 points
- Location boost: 0-10 points
- Confidence boost: 0-20 points
- Total: 0-100 composite score

**Stage 4: QA EVALUATION** (Engine6)
- Quality checks and validation
- Review queue population
- Approval/rejection decisions

**Stage 5: GENERATE BRIEFINGS** (Engine4)
- Only for jobs with BD Score >= 80 (Hot tier)
- Generates 4 documents per job: Playbook, Email, Call Script, Talking Points

**Stage 6: EXPORT RESULTS**
- Notion CSV: 24-column export for database import
- n8n JSON: Full enriched payload with metadata

**Stage 7: WEBHOOK DELIVERY**
- Push results to n8n workflows
- Timestamped JSON payloads

**Stage 8: EMAIL NOTIFICATIONS**
- Alert on hot leads (BD Score >= 80)
- Configurable recipients

**Stage 9: BULLHORN ETL** (Engine7)
- Extract CRM data from 293MB SQLite database
- Enrich dashboard data

**Stage 10: DASHBOARD EXPORT**
- Generate 6 JSON files for dashboard UI:
  - `past_performance.json` — Historical performance metrics
  - `prime_org_chart.json` — Prime contractor organizational structure
  - `contact_org_chart.json` — Contact hierarchy by tier
  - `correlation_summary_enriched.json` — Program-contact correlations
  - `placements.json` — Placement history
  - `data_freshness.json` — Last update timestamps

**Stage 11: KNOWLEDGE INDEXING** (Engine8)
- Index all data into Qdrant vector store
- Update collection counts and freshness

### PipelineResult Dataclass

```python
@dataclass
class PipelineResult:
    success: bool
    jobs_processed: int
    hot_leads: int              # BD Score >= 80
    warm_leads: int             # 50 <= BD Score < 80
    cold_leads: int             # BD Score < 50
    briefings_generated: int
    qa_approved: int
    qa_needs_review: int
    export_files: Dict[str, str]  # {'notion': path, 'n8n': path}
    errors: List[str]
    duration_seconds: float
    timestamp: str              # ISO 8601 format
```

### Files Written Per Run

| Directory | Files | Format |
|-----------|-------|--------|
| `outputs/notion/` | `jobs_export_YYYYMMDD_HHMMSS.csv` | 24-column CSV |
| `outputs/n8n/` | `jobs_webhook_YYYYMMDD_HHMMSS.json` | JSON payload |
| `outputs/BD_Briefings/` | `{Program}_{Role}_Playbook.md` | Markdown |
| `outputs/BD_Briefings/` | `{Program}_{Role}_Email.txt` | Plain text |
| `outputs/BD_Briefings/` | `{Program}_{Role}_CallScript.md` | Markdown |
| `outputs/BD_Briefings/` | `{Program}_{Role}_TalkingPoints.md` | Markdown |
| `dashboard/public/data/` | 6 JSON files | JSON |
| `outputs/` | `pipeline_state.json` | State (last 100 runs) |
| `outputs/` | `alert_state.json` | Alert rules |
| `outputs/Logs/` | `orchestrator.log` | Log file |

---

## 21. Engine2: 7-Stage Program Mapping Pipeline <a name="program-mapping"></a>

### Processing Flow

**Stage 1: INGEST** — Load raw JSON from Engine1_Scraper, validate schema
**Stage 2: PREPROCESS** — HTML cleanup, whitespace normalization
**Stage 3: STANDARDIZE** — LLM extracts 18 structured fields via Claude
**Stage 4: MATCH TO PROGRAMS** — Multi-signal scoring against 388 federal programs
**Stage 5: CALCULATE BD SCORES** — Composite 0-100 scoring
**Stage 6: EXPORT** — Notion CSV (24 cols) + n8n JSON
**Stage 7: GENERATE PLAYBOOKS** — For hot leads (BD >= 80) only

### Federal_Programs.csv Schema (36 Columns)

```
Program Name, Acronym, Agency Owner, Budget, COR/COTR,
Clearance (Original), Clearance Requirements, Confidence Level,
Contract Value, Contract Vehicle, Contract Vehicle Used,
Contract Vehicle/Type, Incumbent Score, Key Locations,
Key Subcontractors, Keywords/Signals, Known Subcontractors,
Notes, PTS Involvement, Pain Points, Period of Performance,
Period of Performance (Original), PoP End, PoP Start,
Prime Contractor, Prime Contractor 1, Priority Level,
Program Manager, Program Type, Program Type 1, Recompete Date,
Related Jobs, Security Requirements, Source Evidence,
Technical Stack, Typical Roles
```

**Total Programs Indexed:** 388 federal programs

### Match Confidence Tiers

| Tier | Confidence | Description |
|------|-----------|-------------|
| Direct | >= 0.70 | High-confidence match via program name, acronym, or contract |
| Fuzzy | 0.50-0.70 | Partial match via keywords, location, or clearance |
| Inferred | < 0.50 | Weak signal match, needs review |

---

## 22. NLQ Engine: 14 Query Intents <a name="nlq-engine"></a>

The Natural Language Query engine (`src/api/nlq_api.py`, 9 endpoints) classifies user queries into 14 distinct intents:

### Intent Taxonomy

| # | Intent | Example Query | Routes To |
|---|--------|--------------|-----------|
| 1 | `SEARCH_CONTACTS` | "Find Tier 1 contacts at Leidos" | `/api/v2/contacts` |
| 2 | `SEARCH_JOBS` | "Show TS/SCI jobs at Langley posted this week" | `/search?collection=jobs` |
| 3 | `SEARCH_PROGRAMS` | "What programs does GDIT run?" | `/api/v2/programs` |
| 4 | `SEARCH_CONTRACTS` | "When does the DCGS contract recompete?" | `/search?collection=programs` |
| 5 | `GRAPH_QUERY` | "Who knows the PACAF site lead?" | `/relationships/path` |
| 6 | `ANALYTICS` | "What's our pipeline worth this quarter?" | `/analytics/summary` |
| 7 | `PREDICTION` | "Win probability for the Langley opportunity" | `/predict/win-probability` |
| 8 | `FORECAST` | "Forecast demand for analysts next quarter" | `/predict/forecast/roles` |
| 9 | `CAMPAIGN` | "Start outreach to Wright-Patt contacts" | `/swarm/execute` |
| 10 | `GENERATE` | "Write outreach email for Kingsley Ero" | Engine4 playbook generator |
| 11 | `COMPARE` | "Compare GDIT vs Leidos hiring in Virginia" | `/analytics/compare` |
| 12 | `EXPLAIN` | "Why is PACAF scored critical?" | `/predict/explain` |
| 13 | `STATUS` | "What happened today?" | `/stats` + `/memory/episodic/recent` |
| 14 | `MEMORY` | "What do we know about Craig Lindahl?" | `/memory/recall` |

### Intent Routing Mechanism

3-tier classification strategy:
1. **Pattern Matching**: Regex keyword patterns (14 sets of trigger words)
2. **Entity Extraction**: Companies, clearances, locations, programs, timeframes
3. **Confidence Scoring**:
   - 1 pattern match → 0.60 confidence
   - 2 pattern matches → 0.75 confidence
   - 3+ pattern matches → 0.85+ confidence
   - Confidence < 0.40 → Request clarification

---

## 23. MCP Tool Registry: 9 Servers <a name="mcp-registry"></a>

The MCP Tool Registry (`src/mcp/tool_registry.py`, 657 LOC) manages 9 registered MCP servers:

### Server Configurations

| # | Server ID | Transport | Cost Tier | Priority | Key Tools |
|---|-----------|-----------|-----------|----------|-----------|
| 1 | `mcp_notion` | STDIO | FREE | 2 | `query_database`, `read_page`, `create_page` |
| 2 | `mcp_google_maps` | HTTP | LOW | 3 | `geocode` ($0.005), `distance_matrix` ($0.01), `place_search` ($0.02) |
| 3 | `mcp_slack` | SSE | FREE | 3 | `send_message`, `list_channels`, `lookup_user` |
| 4 | `mcp_github` | STDIO | FREE | 4 | `search_code`, `create_issue` |
| 5 | `mcp_google_workspace` | HTTP | LOW | 2 | `draft_email`, `send_email` ($0.001), `create_event`, `list_events` |
| 6 | `mcp_filesystem` | STDIO | FREE | 5 | `read_file`, `write_file` |
| 7 | `mcp_memory` | STDIO | FREE | 4 | `store_memory`, `recall_memory` |
| 8 | `mcp_day_ai` | HTTP | MEDIUM | 3 | `enrich_contact` ($0.05), `company_intel` ($0.03) |
| 9 | `mcp_n8n` | HTTP | FREE | 4 | `trigger_workflow`, `list_workflows` |

### Server Capabilities

**mcp_notion:** `database_query`, `page_read`, `page_write`, `contacts`, `programs`, `jobs`
**mcp_google_maps:** `geocoding`, `distance_matrix`, `place_search`, `directions`, `geographic`
**mcp_slack:** `send_message`, `channel_list`, `user_lookup`, `thread_reply`, `team_coordination`
**mcp_github:** `repo_management`, `issue_tracking`, `pr_review`, `ci_cd`, `code_search`
**mcp_google_workspace:** `email_send`, `email_draft`, `calendar_create`, `calendar_list`, `email_sequence`
**mcp_filesystem:** `file_read`, `file_write`, `file_list`, `file_search`
**mcp_memory:** `knowledge_store`, `knowledge_recall`, `entity_create`, `relation_create`
**mcp_day_ai:** `contact_enrich`, `linkedin_activity`, `company_intel`, `contact_intelligence`
**mcp_n8n:** `workflow_trigger`, `workflow_list`, `workflow_status`, `automation`

### Routing Algorithm

```python
@dataclass
class MCPRoutingResult:
    intent: str
    matched_servers: List[Dict[str, Any]]    # Ranked candidates
    selected_server: str                     # Best server ID
    selected_tool: str                       # Best tool name
    confidence: float                        # 0.0-1.0
    reasoning: str                           # Selection explanation
    fallback_servers: List[str]              # Top 2 alternatives
```

**Scoring Formula:**
```
score = (matched_capabilities * 20) + ((10 - priority) * 5) - cost_penalty - health_penalty
```

**Penalties:** FREE=0, LOW=1, MEDIUM=3, HIGH=5 | HEALTHY=0, DEGRADED=5, UNHEALTHY=20

---

## 24. Qdrant Collection Schemas (9 Collections) <a name="qdrant-schemas"></a>

All collections use **1536-dimension OpenAI `text-embedding-3-small`** embeddings with **cosine distance**.

### Collection 1: `jobs` (Job Postings)

| Field | Type | Indexed |
|-------|------|---------|
| `title` | text (embedded) | No |
| `company` | keyword | Yes |
| `location` | text | No |
| `program_name` | keyword | Yes |
| `clearance` | keyword | Yes |
| `bd_priority` | keyword | Yes |
| `source` | keyword | Yes |
| `description` | text (embedded) | No |
| Current count: **4 records** |

### Collection 2: `contacts` (CRM Contacts)

| Field | Type | Indexed |
|-------|------|---------|
| `name` | text (embedded) | No |
| `first_name` | text | No |
| `last_name` | text | No |
| `title` | text (embedded) | No |
| `company` | keyword | Yes |
| `tier` | keyword | Yes |
| `program` | keyword | Yes |
| `bd_priority` | keyword | Yes |
| `source_db` | keyword | Yes |
| `notes` | text (embedded) | No |
| Current count: **7,337 records** |

### Collection 3: `programs` (Federal Programs)

| Field | Type | Indexed |
|-------|------|---------|
| `name` | text (embedded) | No |
| `prime_contractor` | keyword | Yes |
| `location` | text | No |
| `mission_area` | text | No |
| `status` | keyword | Yes |
| `contract_vehicle` | keyword | Yes |
| `bd_priority` | keyword | Yes |
| `notes` | text (embedded) | No |
| Current count: **401 records** |

### Collection 4: `documents` (Documents & Briefings)

| Field | Type | Indexed |
|-------|------|---------|
| `content` | text (embedded) | No |
| `title` | text (embedded) | No |
| `summary` | text | No |
| `doc_type` | keyword | Yes |
| `source_file` | keyword | Yes |
| `tags` | keyword | Yes |
| `created_date` | keyword | Yes |
| Current count: **205 records** |

### Collection 5: `activities` (Call Notes & Interactions)

| Field | Type | Indexed |
|-------|------|---------|
| `content` | text (embedded) | No |
| `subject` | text | No |
| `contact_name` | text | No |
| `company_name` | text | No |
| `activity_type` | keyword | Yes |
| `contact_id` | keyword | Yes |
| `company` | keyword | Yes |
| `date` | keyword | Yes |
| Current count: **500 records** |

### Collection 6: `bullhorn_notes` (CRM Notes)

| Field | Type | Indexed |
|-------|------|---------|
| `note_body` | text (embedded) | No |
| `comments` | text | No |
| `about` | text | No |
| `action` | text | No |
| `note_type` | keyword | Yes |
| `noteType` | keyword | Yes |
| `personReference` | keyword | Yes |
| `_source` | keyword | Yes |
| Supports hybrid dense + sparse vectors |

### Collection 7: `federal_contracts` (Contract Awards)

| Field | Type | Indexed |
|-------|------|---------|
| `title` | text (embedded) | No |
| `description` | text (embedded) | No |
| `agency` | keyword | Yes |
| `contractor` | keyword | Yes |
| `contract_vehicle` | keyword | Yes |
| `status` | keyword | Yes |

### Collection 8: `intelligence_reports` (BD Intelligence)

| Field | Type | Indexed |
|-------|------|---------|
| `content` | text (embedded) | No |
| `title` | text (embedded) | No |
| `summary` | text | No |
| `source` | keyword | Yes |
| `report_type` | keyword | Yes |
| `classification` | keyword | Yes |
| `date` | keyword | Yes |

### Collection 9: `opportunities` (BD Pipeline)

| Field | Type | Indexed |
|-------|------|---------|
| `title` | text (embedded) | No |
| `description` | text (embedded) | No |
| `program` | keyword | Yes |
| `agency` | keyword | Yes |
| `prime` | keyword | Yes |
| `status` | keyword | Yes |
| `priority` | keyword | Yes |

### Specialized Search Methods

```python
search(query, collection, limit, score_threshold, filters) -> List[SearchResult]
search_all(query, limit_per_collection) -> Dict[collection -> results]
find_similar(item_id, collection, limit) -> List[SearchResult]
find_contacts_for_program(program_name) -> List[SearchResult]
find_jobs_for_program(program_name) -> List[SearchResult]
find_contacts_at_company(company_name) -> List[SearchResult]
get_program_intelligence(program_name) -> Dict[programs, jobs, contacts, documents]
```

### Server Modes

| Mode | Storage | Concurrent Writes | Use Case |
|------|---------|-------------------|----------|
| Embedded (File) | `Engine8_Knowledge/data/qdrant/` | No (lock errors) | Development |
| Server (HTTP) | `http://localhost:6333` | Yes | Production |
| In-Memory | None (ephemeral) | Yes | Testing |

---

## 25. Bullhorn ETL: 14-Table Database Schema <a name="bullhorn-schema"></a>

The 293 MB SQLite database (`Engine7_BullhornETL/data/bullhorn.db`) contains 14 tables:

### Core Entity Tables

**jobs** (31 columns):
`id`, `bullhorn_job_id`, `job_number`, `title`, `description`, `client_corporation`, `prime_contractor`, `employment_type`, `status`, `pay_rate`, `bill_rate`, `salary`, `perm_fee_percent`, `location`, `city`, `state`, `clearance_required`, `skills`, `owner`, `contact`, `date_added`, `date_modified`, `date_closed`, `custom_text1-3`, `source_file`, `created_at`, `updated_at`

**candidates** (24 columns):
`id`, `bullhorn_candidate_id`, `first_name`, `last_name`, `full_name`, `email`, `phone`, `mobile`, `occupation`, `job_title`, `company_name`, `current_employer`, `status`, `address`, `city`, `state`, `zip_code`, `clearance_level`, `linkedin_url`, `owner`, `date_added`, `date_modified`, `last_activity_date`, `custom_text1-3`, `source_file`, `created_at`, `updated_at`

**placements** (20 columns):
`id`, `bullhorn_placement_id`, `job_id` (FK→jobs), `candidate_id` (FK→candidates), `bullhorn_job_id`, `bullhorn_candidate_id`, `placement_date`, `start_date`, `end_date`, `status`, `outcome`, `pay_rate`, `bill_rate`, `salary`, `commission`, `duration_days`, `client_name`, `job_title`, `candidate_name`, `owner`, `source_file`, `created_at`

**activities** (16 columns):
`id`, `bullhorn_activity_id`, `activity_type`, `action`, `related_job_id` (FK→jobs), `related_candidate_id` (FK→candidates), `bullhorn_job_id`, `bullhorn_candidate_id`, `activity_date`, `actor`, `note_text`, `comments`, `follow_up_required`, `follow_up_date`, `status`, `source_file`, `created_at`

### Business Development Tables

**prime_contractors** (19 columns):
`id`, `name`, `normalized_name`, `aliases`, `cage_code`, `duns_number`, `website`, `headquarters`, `employee_count`, `annual_revenue`, `naics_codes`, `contract_vehicles`, `total_jobs`, `total_placements`, `total_revenue`, `first_engagement_date`, `last_engagement_date`, `relationship_status`, `notes`, `created_at`, `updated_at`

**programs** (18 columns):
`id`, `name`, `normalized_name`, `acronym`, `prime_contractor_id` (FK), `prime_contractor_name`, `agency`, `sub_agency`, `contract_number`, `contract_value`, `period_of_performance`, `start_date`, `end_date`, `location`, `description`, `total_jobs`, `total_placements`, `total_revenue`, `source_file`, `created_at`, `updated_at`

**past_performance** (25 columns):
`id`, `prime_contractor_id` (FK), `prime_contractor_name`, `program_id` (FK), `program_name`, `total_jobs`, `open_jobs`, `closed_jobs`, `filled_jobs`, `lost_jobs`, `total_placements`, `active_placements`, `completed_placements`, `total_candidates_submitted`, `total_revenue`, `avg_bill_rate`, `avg_pay_rate`, `avg_margin`, `avg_placement_duration_days`, `fill_rate`, `first_job_date`, `last_job_date`, `first_placement_date`, `last_placement_date`, `performance_score`, `notes`, `created_at`, `updated_at`

### Mapping Tables

**job_program_mapping**: `id`, `job_id` (FK), `program_id` (FK), `confidence_score`, `mapping_method`, `created_at`
**job_prime_mapping**: `id`, `job_id` (FK), `prime_contractor_id` (FK), `relationship_type`, `created_at`
**candidate_prime_history**: `id`, `candidate_id` (FK), `prime_contractor_id` (FK), `start_date`, `end_date`, `job_title`, `program_name`, `created_at`

### Audit Tables

**source_files**: `id`, `filename`, `file_path`, `file_size_bytes`, `file_type`, `entity_type`, `record_count`, `processed_date`, `processing_status`, `error_message`, `checksum`, `created_at`
**data_quality_log**: `id`, `source_file`, `table_name`, `record_identifier`, `issue_type`, `issue_description`, `original_value`, `corrected_value`, `severity`, `resolved`, `created_at`
**processing_stats**: `id`, `run_id`, `source_file`, `table_name`, `records_read`, `records_inserted`, `records_updated`, `records_skipped`, `records_error`, `duplicates_found`, `processing_time_seconds`, `created_at`

---

## 26. Scheduler Service <a name="scheduler-service"></a>

### SchedulerConfig

```python
@dataclass
class SchedulerConfig:
    enabled: bool = True
    interval_hours: int = 6
    cron_expression: str = "0 6 * * *"      # 6 AM daily
    input_dir: str = "Engine1_Scraper/data"
    watch_for_new_files: bool = True
    test_mode: bool = False
    send_email: bool = True
    send_webhook: bool = True
    max_retries: int = 3
    retry_delay_minutes: int = 5
    health_check_interval_minutes: int = 30
```

### ScheduledRun State Machine

```python
@dataclass
class ScheduledRun:
    run_id: str                          # RUN_YYYYMMDD_HHMMSS
    scheduled_time: datetime
    input_file: Optional[str] = None
    status: str = 'pending'
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    retry_count: int = 0
```

```
pending → running → completed
    ↓                   ↑
    └─→ failed ─────────┘ (retry if retry_count < max_retries)
```

### Key Methods

```python
schedule_run(input_file: str, run_at: datetime) -> ScheduledRun
run_now(input_file: str) -> ScheduledRun     # Immediate execution
start(blocking: bool = True)                  # Starts scheduler loop
get_status() -> Dict                          # Running status, last run, pending
get_run_history(limit: int = 20) -> List[Dict]
```

---

## 27. LightRAG: Graph-Based Reasoning <a name="lightrag"></a>

### Architecture

The LightRAG system (`Engine8_Knowledge/bd_lightrag/`) provides graph-based reasoning with entity extraction and relationship traversal.

### Core Class: `BDGraphRAG`

```python
class BDGraphRAG:
    def __init__(working_dir, use_qdrant=False, qdrant_url="http://localhost:6333",
                 llm_provider="openai", embedding_model="all-MiniLM-L6-v2")

    # Document Operations
    async insert_documents(documents: List[str], metadata: List[Dict] = None) -> Dict
    insert_documents_sync()  # Synchronous wrapper

    # Query Modes
    async query(query: str, mode: QueryMode) -> QueryResult
    async query_local(query: str) -> str      # Entity-focused queries
    async query_global(query: str) -> str     # High-level summaries
    async query_hybrid(query: str) -> str     # Combined reasoning

    # Graph Operations
    get_entity_graph(entity_name: str) -> Dict
    get_contractor_relationships(contractor_name: str = None) -> List[Dict]
    get_program_contractors(program_name: str) -> Dict
    find_teaming_path(contractor1: str, contractor2: str) -> Dict
    stats() -> Dict
```

### Query Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `LOCAL` | Entity-focused, retrieves specific relationships | "What contracts does Leidos prime?" |
| `GLOBAL` | High-level summaries across the graph | "What's the competitive landscape for DCGS?" |
| `HYBRID` | Combined local + global reasoning | "Who should we partner with for the ABMS recompete?" |
| `NAIVE` | Simple vector similarity (no graph) | Basic semantic search |

### Entity Extraction

**EntityType Enum (7 types):**
`CONTRACTOR`, `PROGRAM`, `CONTACT`, `LOCATION`, `TECHNOLOGY`, `CONTRACT`, `AGENCY`

**Known Entity Database:**
- **18 contractors**: gdit, leidos, saic, northrop, raytheon, lockheed, bae, booz, l3harris, caci, mantech, peraton, parsons, jacobs, kbr, serco, aecom, accenture_federal
- **14 programs**: dcgs, bices, gsm_o, gbsd, abms, jadc2, cms, ngen, disa_encore, ites, alliant, sewp, oasis, stars
- **12 locations**: langley, san_diego, norfolk, fort_meade, pentagon, colorado_springs, huntsville, tampa, omaha, hawaii, ramstein, beale
- **11 technologies**: (various defense/IT technologies)
- **10 agencies**: (DoD agencies and commands)

**13 Relationship Patterns:**
`primes`, `subcontracts`, `teams_with`, `partners_with`, `works_on`, `supports`, `acquired`, `merged_with`, + 5 more

### LightRAG API Endpoints (11)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/lightrag/insert` | POST | Insert documents with entity extraction |
| `/lightrag/query` | POST | Query with mode selection |
| `/lightrag/query` | GET | GET query endpoint |
| `/lightrag/entity/{name}` | GET | Entity relationship graph |
| `/lightrag/relationships` | GET | Contractor relationships |
| `/lightrag/program/{name}/contractors` | GET | Program contractors |
| `/lightrag/teaming-path` | GET | Teaming path between two contractors |
| `/lightrag/extract-entities` | POST | Extract entities from text |
| `/lightrag/known-entities` | GET | All known entity database |
| `/lightrag/stats` | GET | Graph statistics |
| `/lightrag/status` | GET | System status |

---

## 28. Data Governance System (Phase 43A) <a name="data-governance"></a>

### Data Catalog (`src/governance/catalog.py`)

**DataAsset Dataclass:**
```python
@dataclass
class DataAsset:
    id: str
    name: str
    description: str
    asset_type: AssetType   # COLLECTION, TABLE, FILE, API_ENDPOINT, PIPELINE, MODEL, GRAPH
    status: AssetStatus     # ACTIVE, DEPRECATED, ARCHIVED, DRAFT
    owner: str
    domain: str
    schema_id: str
    tags: List[str]
    record_count: int
    size_bytes: int
    lineage: DataLineage    # upstream, downstream, transformations
    usage: UsageStats       # total_reads, total_writes, unique_consumers, popularity_score
    quality: QualityMetrics # completeness, accuracy, freshness_hours, consistency, overall_score
    created_at: str
    updated_at: str
    metadata: Dict
```

**Seeded Assets (5):**
| Asset | Records | Source | Type |
|-------|---------|--------|------|
| contacts | 7,337 | Bullhorn ETL | COLLECTION |
| programs | 401 | Program Mapping | COLLECTION |
| jobs | 4 | Apify Scraper | COLLECTION |
| documents | 205 | Knowledge | COLLECTION |
| activities | 500 | Knowledge | COLLECTION |

### Schema Registry (`src/governance/schema_registry.py`)

**SchemaField Dataclass:**
```python
@dataclass
class SchemaField:
    name: str
    field_type: FieldType   # STRING, INTEGER, FLOAT, BOOLEAN, DATE, DATETIME, LIST, DICT, ANY
    required: bool
    description: str
    default: Any
    constraints: Dict       # min, max, pattern, enum
```

**Seeded Schemas (3):**

| Schema | Fields | Key Constraints |
|--------|--------|-----------------|
| `contact` | name, email, phone, title, company, tier (1-6), location, source | tier: min=1, max=6 |
| `job_posting` | title, company, location, description, clearance, program, bd_score (0-100), date, url | bd_score: min=0, max=100 |
| `program` | name, agency, prime_contractor, value, status, description | status: enum[active, planning, closing, completed] |

**Schema Evolution:**
- `CompatibilityMode`: NONE, BACKWARD, FORWARD, FULL
- `EvolutionType`: FIELD_ADDED, FIELD_REMOVED, FIELD_RENAMED, FIELD_TYPE_CHANGED, FIELD_MADE_REQUIRED, FIELD_MADE_OPTIONAL

### Data Contracts (`src/governance/contracts.py`)

**DataContract Dataclass:**
```python
@dataclass
class DataContract:
    id: str
    name: str
    version: int
    producer: str       # Who generates the data
    consumer: str       # Who consumes it
    asset_id: str
    schema_name: str
    schema_version: int
    quality_terms: List[QualityTerm]  # metric, operator, threshold
    refresh_schedule: str             # "daily", "weekly", etc.
    max_staleness_hours: int
    min_record_count: int
    status: ContractStatus  # DRAFT, ACTIVE, BREACHED, EXPIRED, DEPRECATED
```

**Seeded Contracts (3):**

| Contract | Producer → Consumer | Schedule | Max Staleness |
|----------|-------------------|----------|---------------|
| `contract_jobs_scraper` | Scraper → Program Mapper | daily | 28h |
| `contract_contacts_etl` | Bullhorn → Knowledge | weekly | 168h |
| `contract_programs_mapping` | Program Mapper → BD Scoring | weekly | 168h |

### Quality SLAs (`src/governance/sla_engine.py`)

**QualitySLA Dataclass:**
```python
@dataclass
class QualitySLA:
    id: str
    name: str
    asset_id: str
    owner: str
    targets: List[SLATarget]  # metric, target_value, operator, window (1d/7d/30d)
    status: SLAStatus         # MEETING, AT_RISK, VIOLATED, SUSPENDED
```

**Seeded SLAs (3):**

| SLA | Asset | Targets |
|-----|-------|---------|
| `sla_contacts_freshness` | contacts | 168h max staleness, 95% accuracy, 90% completeness |
| `sla_jobs_freshness` | jobs | 4h max staleness, 85% completeness |
| `sla_programs_quality` | programs | 90% accuracy, 80% completeness, weekly refresh |

---

## 29. Predictive Intelligence API (Phase 32A) <a name="predictive-api"></a>

14 endpoints for win probability, forecasting, and timing optimization:

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/predict/win-probability` | POST | Single opportunity scoring |
| `/predict/win-probability/batch` | POST | Batch scoring |
| `/predict/pipeline/ranked` | GET | Full pipeline ranked by score |
| `/predict/pipeline/review` | GET | Weekly pipeline review |
| `/predict/what-if` | POST | What-if scenario analysis |
| `/predict/forecast/program/{name}` | GET | Program hiring forecast (90-day horizon) |
| `/predict/forecast/location/{loc}` | GET | Location demand forecast |
| `/predict/forecast/roles` | GET | Role demand forecast |
| `/predict/ramp-signals` | GET | Programs ramping up/down |
| `/predict/timing/{program}` | GET | Optimal outreach timing |
| `/predict/budget-calendar` | GET | Forward BD calendar (12 months) |
| `/predict/recompete/{contract}` | GET | Recompete timing prediction |
| `/predict/model-performance` | GET | Model accuracy metrics |
| `/predict/retrain` | POST | Trigger model retraining |

### ML Models Used

| Model | Algorithm | Purpose |
|-------|-----------|---------|
| `WinProbabilityModel` | XGBoost | Win probability (0-1) from 21 input features |
| `OpportunityScorer` | Weighted composite | 6-dimension scoring (0-100) |
| `HiringForecaster` | Time series | Hiring demand by program/location/role |
| `BudgetCyclePredictor` | Seasonal decomposition | FY budget cycle optimization |

### OpportunityInput (21 fields)

```python
class OpportunityInput:
    title: str
    company: str
    program: str
    description: str
    location: str
    estimated_value: float
    clearance: str
    contact_tier: int        # 1-6
    relationship_depth: int
    mutual_connections: int
    fiscal_quarter: int      # 1-4
    days_job_open: int
    days_to_pop_end: int
    is_option_year: bool
    pts_involvement: int     # 0-3
    competitor_density: int
    past_placements_on_program: int
    clearance_match: bool
    # + 3 more context fields
```

---

## 30. Streaming API (Phase 31A) <a name="streaming-api"></a>

14 REST + 4 WebSocket endpoints for real-time event processing:

### REST Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/streaming/stats` | GET | Stream statistics |
| `/streaming/streams` | GET | List configured streams |
| `/streaming/streams/{name}/peek` | GET | Peek latest events |
| `/streaming/streams/{name}/replay` | POST | Replay event range |
| `/streaming/processors` | GET | List event processors |
| `/streaming/processors/{id}/restart` | POST | Restart processor |
| `/streaming/workflows` | GET | List stream workflows |
| `/streaming/workflows/{id}/trigger` | POST | Trigger workflow |
| `/streaming/workflows/executions` | GET | List executions |
| `/streaming/executions/{id}` | GET | Execution details |
| `/streaming/event-chain/{id}` | GET | Trace event chain |
| `/streaming/websocket/connections` | GET | WebSocket stats |
| `/streaming/publish` | POST | Publish event (admin) |
| `/streaming/health` | GET | System health |

### WebSocket Endpoints

| Endpoint | Feed Type | Content |
|----------|-----------|---------|
| `/ws/dashboard` | Live dashboard | Real-time metrics and updates |
| `/ws/campaigns` | Campaign updates | Outreach status changes |
| `/ws/alerts` | Alert-only | Pattern detections, SLA violations |
| `/ws/system` | System health | Component status, errors |

### Event Processing

- Redis Streams backend for message persistence
- Consumer groups for parallel processing
- Configurable retention and max message count
- Priority-based event routing
- Correlation ID tracing across event chains

---

## 31. Knowledge Management API (Phase 39A) <a name="knowledge-management"></a>

15 endpoints for temporal knowledge graphs and entity resolution:

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/knowledge/ingest` | POST | Ingest knowledge episode |
| `/knowledge/entity/{id}/timeline` | GET | Entity timeline |
| `/knowledge/entity/{id}/changes` | GET | Entity changes since date |
| `/knowledge/query/temporal` | POST | Temporal query |
| `/knowledge/contradictions` | GET | List contradictions |
| `/knowledge/resolve/entity` | POST | Resolve entity ambiguity |
| `/knowledge/resolve/candidates/{id}` | GET | Find merge candidates |
| `/knowledge/resolve/merge` | POST | Merge duplicate entities |
| `/knowledge/resolve/global` | POST | Global entity resolution |
| `/knowledge/compile` | POST | Compile text to facts |
| `/knowledge/compile/batch` | POST | Batch fact compilation |
| `/knowledge/compile/notes` | POST | Compile structured notes |
| `/knowledge/stats` | GET | Graph statistics |
| `/knowledge/search/semantic` | GET | Semantic entity search |
| `/knowledge/search/hybrid` | GET | Hybrid search |

### Temporal Knowledge Graph

- **Episodes**: Timestamped knowledge entries
- **Facts**: Extracted claims with `valid_from` / `valid_to` temporal bounds
- **Contradictions**: Auto-detected conflicting facts
- **Entity Resolution**: Merge duplicate entities across data sources (Bullhorn, Notion, Qdrant)

---

## 32. Geographic Intelligence API (Phase 48A) <a name="geo-api"></a>

10 endpoints for location-based analysis:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/geo/geocode` | POST | Geocode location string |
| `/api/geo/geocode/batch` | POST | Batch geocode entities |
| `/api/geo/radius` | POST | Find entities within radius |
| `/api/geo/clusters/{type}` | GET | Geographic clusters by entity type |
| `/api/geo/overlap` | POST | Program geographic overlap analysis |
| `/api/geo/commute` | POST | Commute analysis for candidates |
| `/api/geo/competitive-density/{region}` | GET | Competitor density per region |
| `/api/geo/heatmap/{type}` | GET | Kepler.gl heatmap data |
| `/api/geo/facilities` | GET | Defense facility database |
| `/api/geo/stats` | GET | Geographic statistics |

Uses Nominatim OSM geocoding + defense facility database with lat/lng caching.

---

## 33. Domain Embeddings API (Phase 47A) <a name="embeddings-api"></a>

12 endpoints for fine-tuning and evaluating domain-specific embeddings:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/embeddings/synthetic/generate` | POST | Generate training triplets |
| `/api/embeddings/synthetic/stats` | GET | Training data stats |
| `/api/embeddings/fine-tune` | POST | Start fine-tuning job |
| `/api/embeddings/fine-tune/{id}` | GET | Job status |
| `/api/embeddings/evaluate` | POST | Evaluate model |
| `/api/embeddings/benchmark` | POST | Run golden benchmark |
| `/api/embeddings/compare` | POST | Compare models A vs B |
| `/api/embeddings/deploy` | POST | Deploy model to production |
| `/api/embeddings/models` | GET | List available models |
| `/api/embeddings/quality/history` | GET | Quality scores over time |
| `/api/embeddings/ab-test/start` | POST | Start A/B test |
| `/api/embeddings/ab-test/results` | GET | A/B test results |

### Matryoshka Embeddings

Supports multiple output dimensions for storage/performance trade-offs:
- 768-dim (full quality)
- 512-dim
- 256-dim
- 128-dim
- 64-dim (fastest, lower quality)

Uses sentence-transformers with triplet loss training on domain-specific synthetic data.

---

## 34. Workflow Intelligence API (Phase 49A) <a name="workflows-api"></a>

12 endpoints for temporal durable workflows:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/workflows` | GET | List workflow definitions |
| `/api/workflows/start` | POST | Start workflow run |
| `/api/workflows/runs` | GET | List runs with filters |
| `/api/workflows/runs/{id}` | GET | Run details |
| `/api/workflows/runs/{id}/timeline` | GET | Time-travel timeline |
| `/api/workflows/runs/{id}/replay` | POST | Replay workflow run |
| `/api/workflows/tasks` | POST | Submit orchestrator task |
| `/api/workflows/queues` | GET | Queue status |
| `/api/workflows/fan-out` | POST | Fan-out tasks |
| `/api/workflows/nl/execute` | POST | Natural language → workflow |
| `/api/workflows/nl/autocomplete` | POST | NL autocomplete |
| `/api/workflows/stats` | GET | System stats |

### Key Features

- **Temporal Durable Workflows**: Workflows survive process restarts
- **Time-Travel Debugging**: Inspect any point in workflow execution history
- **Cross-Project Orchestration**: Coordinate work across multiple projects
- **NL-to-Workflow**: Convert natural language descriptions to executable workflows
- **Fan-Out/Fan-In**: Distribute tasks across workers and merge results

---

## 35. RAG Engine Implementation <a name="rag-engine"></a>

### BDRAGEngine Class

```python
class BDRAGEngine:
    def __init__(vector_store: BDKnowledgeStore, model="claude-sonnet-4-20250514", api_key=None)

    ask(question: str, collection: Optional[str], limit=5, score_threshold=0.3) -> RAGResponse
    ask_about_program(program_name: str) -> RAGResponse
    ask_about_company(company_name: str) -> RAGResponse
    find_experts(topic: str) -> RAGResponse
    summarize_jobs(criteria: str) -> RAGResponse
```

### RAGResponse Dataclass

```python
class RAGResponse:
    answer: str
    sources: List[SearchResult]
    query: str
    confidence: float
    collection_searched: str
    metadata: Dict
    timestamp: str

    to_dict() -> Dict
    format_with_sources() -> str  # Formatted with [1], [2] citations
```

### Query Templates (7)

| Template | Collection | Use Case |
|----------|-----------|----------|
| `program_intel` | programs | Program intelligence reports |
| `company_contacts` | contacts | Find contacts at company |
| `clearance_jobs` | jobs | Jobs by clearance level |
| `location_jobs` | jobs | Jobs by location |
| `contractor_past_perf` | documents | Past performance records |
| `hot_leads` | jobs | High-priority opportunities |
| `dcgs_overview` | programs | DCGS portfolio overview |

### Retrieval Configuration

- Max context: 4,000 tokens
- Max response: 1,000 tokens
- Score threshold: 0.3 (minimum relevance)
- Default limit: 5 results
- Source deduplication enabled
- Claude model for generation

---

## 36. BD Playbook Generator (Engine4) <a name="playbook-generator"></a>

### PlaybookData (22 fields)

```python
@dataclass
class PlaybookData:
    # Core
    job_title: str
    company: str
    location: str
    clearance: str
    description: str
    # Program
    program_name: str
    agency: str
    prime_contractor: str
    match_confidence: float
    match_type: str
    match_signals: List[str]
    # Scoring
    bd_score: int
    priority_tier: str
    score_breakdown: Dict
    recommendations: List[str]
    # Intelligence
    contacts: List[Dict]
    key_decision_makers: List[str]
    technologies: List[str]
    certifications: List[str]
    pain_points: List[str]
    # Metadata
    source_url: str
    date_posted: str
    scraped_at: str
```

### 4 Output Templates

**1. Full Playbook** (5 sections):
- Program Intel — Contract details, timeline, incumbents
- Org Intel — Decision makers, influencers, gate keepers
- Pain Points & Opportunities — Known issues, PTS differentiators
- Competitive Landscape — Incumbent strengths/weaknesses
- Action Plan — 30/60/90 day plan with specific next steps

**2. Intro Email** — Personalized outreach with:
- Subject line optimized for open rate
- Personal hook (shared connection, mutual interest)
- Value proposition tied to pain points
- Clear CTA (call, meeting, referral)

**3. Call Script** — Structured conversation guide:
- Opening hook (15 seconds)
- Discovery questions (5 targeted)
- Value proposition delivery
- Objection handling (top 3)
- Close/next steps

**4. Talking Points** — Key messages organized by:
- Technical differentiators
- Past performance highlights
- Team qualifications
- Pricing/value positioning
- Risk mitigation

### Location Market Insights (8 Markets)

| Location | Market Insight |
|----------|---------------|
| Langley/Hampton Roads | ISR/Intel hub, proximity to NGA |
| San Diego | Navy/SPAWAR tech corridor |
| Fort Meade | NSA/Cyber Command epicenter |
| Colorado Springs | Space Command/missile defense |
| Huntsville | Army/MDA tech corridor |
| Tampa | SOCOM/CENTCOM operations |
| DC Metro | HQ/policy/acquisition |
| Hawaii/Pacific | INDOPACOM forward presence |

### Generation Functions

```python
generate_playbook(job: Dict, include_contacts=True,
    output_formats=['full', 'email', 'call', 'talking']) -> PlaybookOutput
generate_playbooks_batch(jobs: List[Dict], output_dir="outputs/BD_Briefings",
    min_score=80) -> List[PlaybookOutput]
```

---

## 37. Complete System Statistics <a name="system-stats"></a>

### Quantified Architecture

| Category | Count |
|----------|-------|
| **Total API Endpoints** | 300+ across 21 router modules |
| **Qdrant Vector Collections** | 9 |
| **Total Vectors Indexed** | 8,447+ |
| **Bullhorn SQL Tables** | 14 |
| **Federal Programs Tracked** | 388 |
| **CRM Contacts** | 7,337 |
| **MCP Servers Registered** | 9 |
| **MCP Tools Available** | 34+ |
| **NLQ Query Intents** | 14 |
| **Pattern Types** | 7 |
| **Intelligence Domains** | 5 |
| **Briefing Types** | 4 |
| **DAG Templates** | 5 |
| **Worker Types** | 8 |
| **Coordination Modes** | 5 |
| **Scoring Dimensions** | 6 (opportunity) + 6 (relationship) |
| **Memory Tiers** | 3 |
| **Entity Types (LightRAG)** | 7 |
| **Relationship Patterns** | 13 |
| **Known Entities** | 65+ (18 contractors, 14 programs, 12 locations, 11 technologies, 10 agencies) |
| **Pipeline Stages** | 11 (master) + 7 (program mapping) |
| **Playbook Templates** | 4 |
| **Location Market Insights** | 8 |
| **Prediction Models** | 4 (XGBoost, composite, time-series, seasonal) |
| **WebSocket Feeds** | 4 |
| **Data Governance Assets** | 5 seeded |
| **Schema Definitions** | 3 seeded |
| **Data Contracts** | 3 seeded |
| **Quality SLAs** | 3 seeded |
| **Embedding Dimensions** | 5 (64 to 768) |
| **OpenClaw Skills** | 75+ existing + 6 new proposed |
| **OpenClaw Bridges** | 3 MCP servers |
| **OpenClaw Cron Jobs** | 5 existing + 4 new proposed |
| **Lines of Code (Key Files)** | 12,000+ across 14 core modules |

### Cross-System Entity Map

Shows how entities flow across the entire architecture:

```
BULLHORN CRM (293MB)                    NOTION DATABASES
├── candidates → contacts (7,337)       ├── DCGS Contacts → contacts
├── jobs → jobs (4)                     ├── GDIT Jobs → jobs
├── placements → past_performance       ├── Program Mapping → programs
├── activities → activities (500)       └── Federal Programs → programs (388)
└── prime_contractors → programs
         │                                      │
         ▼                                      ▼
    ┌─────────────────── QDRANT (8,447 vectors) ──────────────────┐
    │ contacts  programs  documents  activities  jobs              │
    │ bullhorn_notes  federal_contracts  intelligence_reports      │
    │ opportunities                                                │
    └─────────────────────────────┬────────────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────────┐
         ▼                        ▼                            ▼
    PATTERN ENGINE          OPPORTUNITY SCORER          RELATIONSHIP ENGINE
    (7 pattern types)       (6 dimensions)              (6 factors)
         │                        │                            │
         ▼                        ▼                            ▼
    INSIGHT COMPILER        SWARM DECOMPOSER            MEMORY CORTEX
    (4 briefing types)      (5 DAG templates)           (3 memory tiers)
         │                        │                            │
         └────────────────────────┼────────────────────────────┘
                                  ▼
                         OPENCLAW GATEWAY (:18789)
                         ├── autonomous-loop (OODA)
                         ├── self-discover (7 mechanisms)
                         ├── swarm-dispatch (DAG execution)
                         ├── learn-feedback (outcome tracking)
                         └── meta-evolve (self-improvement)
```

---

## 38. CrewAI Agent System: 8 BD Intelligence Agents <a name="crewai-agents"></a>

The BD-Automation-Engine implements an 8-agent CrewAI system located in `Engine8_Knowledge/agents/`. Each agent extends `BDAgent` (base class) and implements async `process(query, context)` → `AgentResponse`.

### Base Agent Architecture

**File:** `Engine8_Knowledge/agents/base_agent.py`

```python
@dataclass
class AgentResponse:
    success: bool
    content: str
    sources: List[str]
    confidence: float          # 0.0-1.0
    agent_name: str
    metadata: Dict[str, Any]

class BDAgent:
    name: str
    description: str
    async def process(query: str, context: Optional[Dict]) -> AgentResponse
```

### Agent 1: ContactClassifierAgent

**File:** `Engine8_Knowledge/agents/contact_classifier_agent.py` (309 LOC)

**Purpose:** Classifies contacts across 4 dimensions: hierarchy tier, DCGS program, BD priority, location hub.

**6-Tier Hierarchy Classification** (regex-based title matching):

| Tier | Label | Pattern Examples | Confidence |
|------|-------|-----------------|------------|
| 1 | Executive | CEO, CTO, CIO, President, VP, SVP, General, Admiral | 0.9 |
| 2 | Director | Director, Colonel, Captain, Program Manager, Division Chief | 0.9 |
| 3 | Program Leadership | Manager, Senior Manager, Major, Team Lead, Branch Chief | 0.9 |
| 4 | Senior IC | Senior Engineer, Principal, Lead Architect, SME | 0.8 |
| 5 | Individual Contributor | Engineer, Analyst, Developer, Consultant, Specialist | 0.8 |
| 6 | Support / Entry Level | Assistant, Associate, Intern, Trainee, Junior, Technician | 0.5 (default) |

**Program Keywords Map (7 programs):**
- `AF DCGS - Langley` → langley, 480th, acc, air combat command
- `AF DCGS - Wright-Patt` → wright-patt, nasic, wright patterson
- `AF DCGS - PACAF` → pacaf, pacific air, hickam, hawaii
- `Army DCGS-A` → dcgs-a, army intelligence, inscom, fort huachuca
- `Navy DCGS-N` → dcgs-n, naval intelligence, fleet, norfolk
- `Corporate HQ` → corporate, headquarters, hq, arlington
- `Enterprise Security` → cyber, security, infosec, ciso

**Location Hub Map (5 geographic hubs):**
- `Hampton Roads` → langley, norfolk, virginia beach, hampton, newport news
- `San Diego Metro` → san diego, coronado, point loma
- `DC Metro` → washington, arlington, bethesda, mclean, reston, tysons
- `Dayton/Wright-Patt` → dayton, wright-patt, fairborn
- `OCONUS` → oconus, overseas, germany, japan, korea, uk

**BD Priority Calculation:**
```
Critical: Tier ≤ 2 AND program ≠ "Unassigned"
High:     Tier ≤ 3 AND program ≠ "Unassigned" OR Tier ≤ 2
Medium:   Tier = 4 AND program ≠ "Unassigned"
Standard: Everything else
```

**Confidence Formula:** `min(0.95, 0.3 + (number_of_signals × 0.1))`

**Output: ClassificationResult dataclass:**
- `hierarchy_tier: int` (1-6)
- `tier_label: str`
- `program: str`
- `bd_priority: str` (Critical/High/Medium/Standard)
- `location_hub: str`
- `confidence: float`
- `signals: List[str]` (explanation of classification reasoning)

### Agent 2: ScraperMonitorAgent

**File:** `Engine8_Knowledge/agents/scraper_monitor_agent.py` (303 LOC)

**Purpose:** Monitors job scraper results, identifies BD opportunities, detects competitor activity.

**Competitor Watch List (10 companies):**
leidos, northrop, booz allen, peraton, caci, saic, mantech, raytheon, l3harris, parsons

**High-Value Clearance Levels:**
ts/sci, ts/sci poly, top secret/sci, polygraph

**DCGS Keywords (12 terms):**
dcgs, distributed ground, dgs, sensor data, isr, sigint, geoint, humint, masint, fusion, exploitation, dissemination

**High-Value Detection:** Job is high-value when ≥ 2 signals present from:
1. High clearance requirement (TS/SCI+)
2. DCGS keyword in title/description
3. BD score ≥ 80

**Alert Types:**
- `new_jobs` — New jobs detected not in previous set
- `competitor_activity` — Competitor mentions in job posting
- `high_value` — High-value job detected (severity: high)
- `anomaly` — Unexpected patterns

**Output: ScrapeAnalysis dataclass:**
- `scraper_name: str`
- `total_jobs: int`
- `new_jobs: int`
- `high_value_jobs: int`
- `ts_sci_jobs: int`
- `competitor_signals: List[str]`
- `alerts: List[ScraperAlert]`
- `recommendations: List[str]`

**Recommendation Rules:**
- high_value_count > 5 → "Review N high-value opportunities immediately"
- ts_sci_count > 10 → "Heavy TS/SCI hiring (N jobs) - program expansion likely"
- competitor_signals present → "Top competitor activity: X, Y, Z"

### Agent 3: ProgramIntelAgent

**Purpose:** Full program intelligence research — combines Qdrant search, past performance, contact mapping.
**Location:** `Engine8_Knowledge/agents/` (referenced in api.py agent routes)
**Endpoint:** `POST /agent/program`

### Agent 4: CompanyResearchAgent

**Purpose:** Company-level research across all collections — jobs, contacts, programs, past performance.
**Endpoint:** `POST /agent/company`

### Agent 5: ContactFinderAgent

**Purpose:** Intelligent contact discovery with tier-aware ranking.
**Endpoint:** `POST /agent/contact`

### Agent 6: BDStrategyAgent

**Purpose:** Strategic BD recommendations combining opportunity scoring, relationship strength, and competitive analysis.
**Endpoint:** `POST /agent/strategy`

### Agent 7: OutreachComposerAgent

**Purpose:** Generates personalized outreach (emails, call scripts, talking points) based on contact intelligence.
**Endpoint:** Referenced in swarm worker type `outreach_crafter`

### Agent 8: KnowledgeQueryAgent

**Purpose:** General knowledge queries using RAG, semantic search, and graph traversal.
**Endpoint:** `POST /ask/smart` (routes through intent classification)

---

## 39. Engine3: OrgChart Contact Classification Deep Dive <a name="engine3-deep-dive"></a>

**File:** `Engine3_OrgChart/scripts/contact_classifier.py`

### Classification System Architecture

The Engine3 contact classifier is a standalone module (separate from the CrewAI agent) that provides the 6-tier classification with Notion integration.

### Classification Result Data Structure

```python
@dataclass
class ClassificationResult:
    tier: int                          # 1-6
    tier_name: str                     # 'Executive', 'Director', etc.
    bd_priority: str                   # 'Critical', 'High', 'Medium', 'Standard'
    bd_emoji: str                      # 'red_circle', 'orange_circle', etc.
    program: Optional[str]             # Inferred or explicit program
    location_hub: str                  # Regional hub assignment
    outreach_sequence: str             # 'A - Discovery Approach', etc.
    confidence: float                  # 0.3-0.9
```

### Tier-to-Action Mapping

| Tier | BD Priority | Emoji | Outreach Sequence |
|------|-------------|-------|-------------------|
| 1 - Executive | Critical | red_circle | D - Strategic Engagement |
| 2 - Director | Critical | red_circle | D - Strategic Engagement |
| 3 - Program Leadership | High | orange_circle | C - Program Engagement |
| 4 - Management | High | orange_circle | B - Validation Approach |
| 5 - Senior IC | Medium | yellow_circle | A - Discovery Approach |
| 6 - Individual Contributor | Standard | white_circle | A - Discovery Approach |

### Location-to-Program Inference (47 Locations)

**San Diego Metro:**
- San Diego, La Mesa, La Jolla → AF DCGS - PACAF

**Hampton Roads:**
- Hampton, Newport News, Langley → AF DCGS - Langley
- Norfolk, Suffolk → Navy DCGS-N

**Dayton/Wright-Patt:**
- Dayton, Beavercreek, Fairborn → AF DCGS - Wright-Patt

**DC Metro:**
- Herndon, Falls Church, Reston → Corporate HQ
- Fort Belvoir → Army DCGS-A
- Fort Meade → NSA/CYBERCOM
- Springfield → NGA Programs
- McLean → IC Corporate
- Chantilly → NRO/IC

**Other CONUS:**
- Fort Detrick, Aberdeen → Army DCGS-A
- Tracy → Navy DCGS-N
- Colorado Springs → Space Force
- Tampa → SOCOM

### Notion Integration

`format_for_notion(classification)` maps emoji names to Unicode:
- red_circle → U+1F534
- orange_circle → U+1F7E0
- yellow_circle → U+1F7E1
- white_circle → U+26AA

**Notion Properties Output:**
- `Hierarchy Tier`: "Tier {N} - {Name}"
- `BD Priority`: "{emoji} {priority}"
- `Program`: program name
- `Location Hub`: location hub
- `Outreach Sequence`: sequence type
- `Classification Confidence`: float

### CLI Interface

```bash
python contact_classifier.py --input contacts.json --output classified.json --format [full|notion]
```

---

## 40. Engine5: BD Scoring Algorithm Deep Dive <a name="engine5-deep-dive"></a>

**File:** `Engine5_Scoring/scripts/bd_scoring.py`

### Scoring Formula

```
score = (base_score + clearance_boost + program_boost + location_boost +
         confidence_boost + pain_point_boost + recency_boost) × tier_multiplier
score = min(score, 100)  # Cap at 100
```

### Component Breakdown

**Base Score:** 50 points (starting minimum)

**1. Clearance Boosts:**

| Clearance Level | Boost |
|----------------|-------|
| TS/SCI w/ Poly | +35 |
| TS/SCI w/ Full Scope Poly | +35 |
| TS/SCI w/ CI Poly | +30 |
| TS/SCI | +25 |
| Top Secret | +15 |
| Secret | +5 |

**2. Program Boosts:**

| Program | Boost | Notes |
|---------|-------|-------|
| AF DCGS - PACAF | +15 | Critical priority |
| AF DCGS - Langley | +10 | |
| AF DCGS - Wright-Patt | +10 | |
| Navy DCGS-N | +8 | |
| Army DCGS-A | +8 | |
| Other | 0 | |

**3. Location Boosts:**

| Location | Boost | Notes |
|----------|-------|-------|
| San Diego | +10 | Critical understaffed |
| Hampton | +5 | |
| Dayton | +5 | |
| Others | 0 | |

**4. Confidence Weight:** `int(confidence × 20)` → max +20 points

**5. Pain Point Boost:** +5 per validated pain point

**6. Recency Boosts:**

| Timeframe | Boost |
|-----------|-------|
| Last 7 days | +10 |
| Last 30 days | +5 |
| Last 90 days | +2 |
| Older | 0 |

**7. Tier Multipliers:**

| Tier | Multiplier |
|------|-----------|
| 1 (Executive) | ×1.3 |
| 2 (Director) | ×1.25 |
| 3 (Program Leadership) | ×1.2 |
| 4 (Management) | ×1.1 |
| 5 (Senior IC) | ×1.0 |
| 6 (IC) | ×0.9 |

### Score Example

```
Base:           50
TS/SCI:        +25 = 75
AF DCGS-PACAF: +15 = 90
San Diego:     +10 = 100
Tier 1 mult:   ×1.3 = 130 → capped at 100
```

### Priority Tiers

| Tier | Score Range | Emoji | Action |
|------|-------------|-------|--------|
| Hot | 80-100 | 🔥 | Immediate outreach |
| Warm | 50-79 | 🟡 | Weekly follow-up |
| Cold | 0-49 | ❄️ | Pipeline monitoring |

### Recommendation Engine

**Score ≥ 80 (Hot):**
- "Immediate outreach recommended - Hot opportunity"
- "Escalate to BD leadership for review"

**Score 50-79 (Warm):**
- "Add to weekly follow-up queue"
- "Gather additional intelligence before outreach"

**Score < 50 (Cold):**
- "Monitor for changes in priority signals"
- "Add to long-term pipeline tracking"

**Component-specific:**
- Clearance ≥ 25: "High-value cleared position - prioritize"
- Program ≥ 10: "DCGS program alignment - leverage existing relationships"
- Location ≥ 10: "San Diego/PACAF - critical understaffed site"

### ScoringResult Dataclass

```python
@dataclass
class ScoringResult:
    bd_score: int                           # 0-100
    tier: str                               # 'Hot', 'Warm', 'Cold'
    tier_emoji: str                         # '🔥', '🟡', '❄️'
    score_breakdown: Dict[str, int]         # Detailed component scores
    recommendations: List[str]              # Actionable recommendations
```

### Batch Processing & Reporting

**`score_batch(items)`** adds `_scoring` field to each item:
- `BD Priority Score`: 0-100
- `Priority Tier`: "{emoji} {tier}"
- `Score Breakdown`: full component dict
- `Recommendations`: list of strings

**`generate_scoring_report(scored_items)`** returns:
```python
{
    "total_items": N,
    "by_tier": {"Hot": X, "Warm": Y, "Cold": Z},
    "average_score": float,
    "top_opportunities": List[Dict],  # Top 10
    "score_distribution": {"80-100": X, "50-79": Y, "0-49": Z}
}
```

---

## 41. Engine6: QA & Alerts System Deep Dive <a name="engine6-deep-dive"></a>

### QA Feedback System

**File:** `Engine6_QA/scripts/qa_feedback.py`

**QA Configuration:**
```python
@dataclass
class QAConfig:
    auto_approve_threshold: float = 0.70    # ≥70% → auto-approve
    review_threshold: float = 0.50          # <50% → needs review
    batch_size: int = 10
```

**QA Status Workflow:**
```
PENDING → evaluate_item() → APPROVED (≥0.70 confidence)
                           → NEEDS_REVIEW (<0.70 confidence)
                           → REJECTED (manual decision)
```

### 5-Step Root Cause Analysis

The system performs systematic issue detection in priority order:

| Priority | Issue Type | Condition | Severity | Auto-Fixable |
|----------|-----------|-----------|----------|-------------|
| 1 | `invalid_mapping` | program in ['Unmatched', 'Unknown', '', None] | CRITICAL | YES |
| 2 | `low_confidence` | confidence < 0.50 | HIGH | NO |
| 3 | `missing_data` | No clearance, location, or prime contractor | MEDIUM | YES |
| 4 | `data_quality` | 0.50 ≤ confidence < 0.70 | LOW | NO |
| 5 | No issues | All checks pass | — | — |

**RootCause Dataclass:**
```python
@dataclass
class RootCause:
    issue_type: str         # Type of issue detected
    severity: str           # 'low', 'medium', 'high', 'critical'
    description: str        # Human-readable explanation
    affected_fields: List[str]  # Which fields caused the issue
    recommended_fix: str    # What to do about it
    auto_fixable: bool      # Can the system fix it automatically?
```

### Review Queue

**File:** `Engine6_QA/data/review_queue.json`

**Current Status:** 740 items total
- All status: `needs_review`
- Confidence 0.2 (20%): 46 items
- Confidence 0.5 (50%): 694 items
- Reviewed: 0 items (all false)

**Queue Item Structure:**
```json
{
  "job_id": "string",
  "added_at": "ISO timestamp",
  "status": "needs_review",
  "confidence": 0.0-1.0,
  "review_reasons": ["string"],
  "original_program": "string",
  "reviewed": false,
  "root_cause": {
    "type": "low_confidence",
    "severity": "high",
    "description": "string",
    "recommended_fix": "string",
    "auto_fixable": false
  }
}
```

### Alert Engine

**File:** `Engine6_QA/scripts/alerts.py`

**Cooldown:** 60 minutes per rule (prevents alert fatigue)

**4 Alert Rules:**

| # | Rule ID | Monitors | Threshold | Severity |
|---|---------|----------|-----------|----------|
| 1 | `high_priority_contacts` | New Tier 1 contacts in Qdrant | New vs. baseline | WARNING |
| 2 | `job_count_anomaly` | Jobs collection count | >20% deviation | WARNING |
| 3 | `pipeline_failures` | `pipeline_state.json` errors | Any errors present | CRITICAL |
| 4 | `search_quality` | Benchmark query score | score < 0.60 | WARNING |

**Search Quality Benchmark:** Query "network engineer TS/SCI Langley" against jobs collection. If top match score < 0.60, suggests embedding refresh.

**Alert Delivery Channels:**
1. **Logging** — Always (CRITICAL or WARNING level)
2. **Slack webhook** — Color-coded by severity (green/yellow/red)
3. **n8n webhook** — Full JSON payload
4. **History file** — Last 200 alerts in `alert_state.json`

**Alert Dataclass:**
```python
@dataclass
class Alert:
    alert_id: str               # UUID truncated to 8 chars
    rule_id: str
    severity: AlertSeverity     # INFO | WARNING | CRITICAL
    title: str
    message: str
    data: Dict[str, Any]
    timestamp: str              # ISO format
```

### Quality Monitor

**File:** `Engine6_QA/quality_monitor.py`

**Monitors 9 Qdrant collections:** contacts, programs, documents, activities, jobs, bullhorn_notes, federal_contracts, intelligence_reports, opportunities

**Required Payload Fields per Collection:**
```python
{
    "contacts": ["name", "company"],
    "programs": ["name"],
    "documents": ["title"],
    "activities": ["type"],
    "jobs": ["title"],
    "bullhorn_notes": ["action", "comments_text"],
    "federal_contracts": ["title"],
    "intelligence_reports": ["title"],
    "opportunities": ["title"],
}
```

**Health Status:** green (all good) | yellow (indexing/optimizing) | red (empty/error)

**Quality Report:**
```python
@dataclass
class QualityReport:
    timestamp: str
    collections: List[Dict]          # CollectionHealth list
    quality_scores: List[Dict]       # DataQualityScore list
    alerts: List[Dict]               # Recent alerts
    summary: Dict[str, Any]          # {total_vectors, green/yellow/red count, avg_completeness}
```

### QA Workflow Integration

**`run_qa_workflow(jobs, config, auto_queue=True)`** returns:
1. `BatchQAReport` — full statistics
2. `approved_jobs` — auto-approved list
3. `review_jobs` — items needing human review

**QA Summary Report** generates markdown with:
- Overall statistics (auto-approved %, needs review %, avg confidence)
- Root cause analysis breakdown (by type and severity)
- Detailed items requiring review (sorted by severity)
- Recommended actions (critical fixes, auto-fixable count, manual reviews)

---

## 42. Dashboard Architecture: 47+ Page React Application <a name="dashboard-architecture"></a>

### Technology Stack

- **Framework:** React 19 + TypeScript (strict)
- **Build:** Vite 7 with HMR
- **Styling:** Tailwind CSS v4 with defense-themed ThemeProvider
- **State:** TanStack React Query (5-min staleTime) + DataProvider Context
- **Components:** Radix UI + shadcn/ui patterns
- **Charts:** Recharts (likely, based on component patterns)
- **Icons:** Lucide React

### Complete Page Inventory (47+ Pages)

| # | Page Component | Category | Description |
|---|---------------|----------|-------------|
| 1 | SmartQuery.tsx | Intelligence | AI-powered semantic search with strategy selection |
| 2 | Analytics.tsx | Metrics | BD analytics and pipeline metrics |
| 3 | Contacts.tsx | CRM | Contact database browser |
| 4 | ContactDetail.tsx | CRM | Individual contact deep dive |
| 5 | ContactOrgChartPage.tsx | CRM | Org chart visualization |
| 6 | Programs.tsx | Programs | Federal program browser |
| 7 | ProgramDetail.tsx | Programs | Individual program deep dive |
| 8 | Contractors.tsx | Programs | Prime/sub contractor browser |
| 9 | Opportunities.tsx | Pipeline | BD opportunity tracker |
| 10 | JobIntelligence.tsx | Jobs | Job posting intelligence |
| 11 | JobsPipeline.tsx | Jobs | Job processing pipeline |
| 12 | PastPerformance.tsx | Research | Past performance records |
| 13 | CompetitiveLandscape.tsx | Research | Competitor analysis |
| 14 | KnowledgeGraph.tsx | Graph | Knowledge graph explorer |
| 15 | GraphExplorer.tsx | Graph | Interactive graph browser |
| 16 | GraphAnalytics.tsx | Graph | Graph metrics and patterns |
| 17 | MindMap.tsx | Graph | AI-powered mind mapping |
| 18 | RelationshipExplorer.tsx | Relationships | Contact relationship mapping |
| 19 | OutreachManager.tsx | BD Actions | Outreach campaign manager |
| 20 | MeetingCalendar.tsx | BD Actions | Meeting prep + calendar |
| 21 | DailyPlaybook.tsx | BD Actions | Daily BD playbook |
| 22 | CallIntelligence.tsx | Voice | Call transcript analysis |
| 23 | BDEvents.tsx | Events | BD event tracking |
| 24 | AccountTakeover.tsx | Strategy | Account takeover planning |
| 25 | RevenuePipeline.tsx | Revenue | Revenue tracking + forecast |
| 26 | PredictiveInsights.tsx | ML | Predictive analytics dashboard |
| 27 | ExecutiveSummary.tsx | Reports | Executive summary page |
| 28 | DataQualityDashboard.tsx | System | Data quality metrics |
| 29 | EnrichmentDashboard.tsx | System | Data enrichment status |
| 30 | QADashboard.tsx | System | QA review queue |
| 31 | PipelineStatus.tsx | System | Pipeline run status |
| 32 | AlertHistory.tsx | System | Alert history browser |
| 33 | SystemHealth.tsx | System | System health monitoring |
| 34 | SystemOverview.tsx | System | Overview dashboard |
| 35 | RealtimeDashboard.tsx | System | Real-time metrics (SSE/WS) |
| 36 | SearchQuality.tsx | System | Search quality metrics |
| 37 | SearchLab.tsx | System | Search experimentation |
| 38 | Locations.tsx | Geographic | Location-based intelligence |
| 39 | GeographicDashboard.tsx | Geographic | Geographic analysis |
| 40 | PrimeOrgChart.tsx | Organization | Prime contractor org chart |
| 41 | PlacementsPage.tsx | CRM | Placement tracking |
| 42 | MemoryContext.tsx | Memory | Memory system browser |
| 43 | AgentPanel.tsx | Agents | Agent execution panel |
| 44 | AutonomousAgents.tsx | Agents | Autonomous agent control |
| 45 | Integrations.tsx | Config | Integration settings |
| 46 | AutomationCenter.tsx | Config | Automation configuration |
| 47 | WorkflowControl.tsx | Config | N8N workflow manager |
| 48 | Settings.tsx | Config | System settings |

### Vite Proxy Routes (51 API Prefixes)

All proxied to `http://127.0.0.1:8100` unless noted:

```
/api, /health, /stats, /search, /ask, /agents, /memory, /bdgraph,
/cache, /qa, /pipeline, /alerts, /rag, /agent, /dify, /collections,
/contacts, /programs, /jobs, /ingest, /sync, /index, /dashboard,
/documents, /activities, /analytics, /ai, /graph, /notifications,
/webhooks, /contracts, /competitive, /reports, /ml, /integrations,
/outreach (→ :8300), /ws (WebSocket), /sse, /realtime, /embeddings,
/automation, /platform, /neo4j, /workflows, /scrape, /sam,
/federal-docs, /org-chart, /mcp, /optimizer, /monitoring
```

### Data Provider Architecture

**File:** `dashboard/src/data/DataProvider.tsx`

**Three Data Adapters:**
1. `hubAdapter` — BD Intelligence Hub API (localhost:8100)
2. `notionAdapter` — Notion database integration
3. `localAdapter` — Fallback local JSON data

**Context Value:**
```typescript
{
  data: {
    jobs: Job[]
    programs: Program[]
    contacts: Contact[]
    contactsByTier: Record<number, Contact[]>
    contractors: Contractor[]
    summary: CorrelationSummary | null
  }
  loading: boolean
  error: string | null
  dataSource: 'local' | 'notion' | 'hub'
  sourceStatus: DataSourceStatus
  lastUpdated: Date | null
  switchDataSource: (source) => void
  refresh: () => Promise<void>
  sync: () => Promise<SyncResult>
}
```

### Hub API Client (45+ Methods)

**File:** `dashboard/src/api/hubApi.ts`

**Health & Stats:** getHealth, getStats, getCacheStats, getGraphStats, testConnection
**Search:** search, searchHybrid
**RAG/Smart:** ask, askSmart, analyzeQuery, getRouterDecision
**Knowledge Graph:** getProgramEcosystem, getContactNetwork, findTeamingPath, queryGraph
**Memory:** searchMemory, getEntityFacts, getInsights, getContactContext, getProgramContext
**Agents:** runProgramAgent, runCompanyAgent, runContactAgent, runStrategyAgent
**Workflows:** analyzeProgram, prepareOutreach, generateWeeklyIntel, generateWeeklyReport
**Collections:** getJobs, getPrograms, getContacts, getDocuments, getActivities
**QA/Pipeline:** getQAStats, getQAReviewQueue, resolveQAItem, getPipelineStatus, triggerPipeline
**Filtering:** filterContacts, filterPrograms
**Competitive:** getContractAwards, getExpiringContracts, getCompetitiveSummary
**Memory CRUD:** storeMemory, getEntityMemories, deleteMemory

### React Query Hooks

**File:** `dashboard/src/hooks/useHubApi.ts`

**Auto-Fetching Hooks (polling support):**
- useHubHealth(pollInterval?) → HubHealth
- useHubStats(pollInterval?) → HubStats
- useHubCacheStats() → CacheStats
- useHubGraphStats() → GraphStats
- useBDInsights(type?, limit?) → BDInsight[]
- useAgentTasks(pollInterval?) → agent tasks
- useHubConnection() → connection status

**Manual Execution Hooks:**
- useSmartQuery() → execute smart search
- useHubAgent(agentType) → run agents
- useProgramEcosystem() → fetch program data
- useContactNetwork() → fetch contact data
- useTeamingPath() → find teaming paths
- useMemorySearch() → search memories
- useEntityFacts() → get entity facts

### SmartQuery Page Deep Dive

The SmartQuery page (`dashboard/src/pages/SmartQuery.tsx`, 368 LOC) is the primary intelligence interface:

**Search Strategies:**
- `auto` — System chooses optimal strategy
- `semantic` — Vector similarity search
- `hybrid` — Dense + sparse vectors
- `graph` — Knowledge graph traversal
- `rag` — Retrieval-augmented generation

**Features:**
- Multi-strategy search with confidence display
- Source attribution with collection-specific icons (contacts=cyan, programs=purple, documents=amber, activities=green, jobs=blue)
- Score visualization (progress bars)
- Query history with replay
- 4 example query suggestions
- Entity extraction display
- Confidence gauge

---

## 43. Voice Intelligence API: 12 Endpoints <a name="voice-api"></a>

**File:** `src/api/voice_api.py`

### Endpoint Inventory

| # | Method | Path | Purpose |
|---|--------|------|---------|
| 1 | POST | `/api/voice/briefing/batch` | Generate briefings for multiple contacts |
| 2 | POST | `/api/voice/briefing/{contact_id}` | Pre-call intelligence briefing |
| 3 | GET | `/api/voice/briefing/{contact_id}/audio` | Audio briefing file |
| 4 | POST | `/api/voice/transcript/analyze` | Analyze call transcript |
| 5 | POST | `/api/voice/transcript/vapi-webhook` | Handle Vapi post-call webhook |
| 6 | GET | `/api/voice/transcript/{call_id}` | Get transcript analysis |
| 7 | GET | `/api/voice/history/{contact_id}` | Contact call history |
| 8 | GET | `/api/voice/intel/recent` | Recent intelligence (default 20, max 100) |
| 9 | GET | `/api/voice/intel/pain-points` | Aggregated pain points |
| 10 | GET | `/api/voice/intel/action-items` | Outstanding action items |
| 11 | POST | `/api/voice/coaching/suggestions` | Real-time coaching from transcript |
| 12 | GET | `/api/voice/analytics` | Call volume, duration, sentiment trends |

### CallBriefing Model

```python
{
  id: str,
  contact_id: str,
  contact: {
    name, title, company, program, tier,
    priority_score, location, clearance
  },
  pain_points: [{description, source, severity}],
  recent_interactions: [{type, date, outcome, follow_up}],
  open_jobs: List[str],
  past_performance: List[str],
  recent_news: List[str],
  talking_points: [{topic, context, suggested_opener, priority}],
  relationship_map: [{contact_name, relationship, program, contacted}],
  priority: str,
  summary: str,
  duration_estimate_sec: int,
  created_at: str
}
```

### TranscriptIntel Model (Intelligence Extraction)

```python
{
  id: str,
  call_id: str,
  contact_id: str,
  transcript_length: int,
  duration_sec: int,
  sentiment: str,            # positive, neutral, negative
  sentiment_score: float,
  pain_points: [{content, confidence}],
  job_openings: [{content, confidence}],
  contact_mentions: [{content, confidence}],
  budget_signals: [{content, confidence}],
  competitor_mentions: [{content, confidence, context}],
  contract_signals: [{content, confidence}],
  action_items: [{description, owner, due_date, priority}],
  key_topics: List[str],
  summary: str,
  total_intel_items: int,
  created_at: str
}
```

### Vapi Integration

The system integrates with Vapi (voice AI platform) via webhook:
- Receives post-call transcript from Vapi
- Extracts 7 intelligence categories: pain points, job openings, contact mentions, budget signals, competitor mentions, contract signals, action items
- Stores results for learn-feedback cycles

---

## 44. Collaboration API: Real-Time Multi-User <a name="collaboration-api"></a>

**File:** `src/api/collaboration_api.py`

### 12 Endpoints

| # | Method | Path | Purpose |
|---|--------|------|---------|
| 1 | POST | `/api/collab/rooms` | Create collaboration room |
| 2 | GET | `/api/collab/rooms` | List active rooms |
| 3 | POST | `/api/collab/rooms/{room_id}/join` | Join a room |
| 4 | POST | `/api/collab/rooms/{room_id}/op` | Apply CRDT operation |
| 5 | GET | `/api/collab/rooms/{room_id}/state` | Get room state |
| 6 | POST | `/api/collab/claims` | Claim contact ownership |
| 7 | GET | `/api/collab/claims` | List active claims |
| 8 | POST | `/api/collab/claims/{claim_id}/release` | Release claim |
| 9 | POST | `/api/collab/claims/{claim_id}/contest` | Contest a claim |
| 10 | POST | `/api/collab/intel` | Post intelligence |
| 11 | GET | `/api/collab/intel` | Get intel feed |
| 12 | GET | `/api/collab/stats` | Collaboration stats |

### CRDT Operations

The collaboration system uses Conflict-free Replicated Data Types (CRDTs) for real-time collaboration:
- Room-based collaboration model
- Operation-based CRDT application
- Contact claim/release mechanism for preventing duplicate outreach
- Intel sharing feed for team coordination

---

## 45. Tenant & Auth API: Multi-Tenant Security <a name="tenant-api"></a>

**File:** `src/api/tenant_api.py`

### 21 Endpoints Across 4 Categories

**Tenant Management (7 endpoints):**
- Create, list, get, update, delete tenants
- Per-tenant health and usage tracking

**Authentication (8 endpoints):**
- Login (credential-based)
- Logout (session invalidation)
- Token refresh (JWT rotation)
- SSO integration (SAML/OAuth)
- User management (CRUD)
- Password management (reset, change)
- MFA setup and verification

**RBAC (4 endpoints):**
- Role assignment
- Permission management
- API key generation and management

**Audit (2 endpoints):**
- Audit log retrieval (who did what, when)
- Audit statistics (access patterns, anomalies)

---

## 46. Revenue Intelligence API: 16 Endpoints <a name="revenue-api"></a>

**File:** `src/api/revenue_api.py`

### Revenue Tracking (7 endpoints)

| Endpoint | Returns |
|----------|---------|
| `/revenue/summary` | Total revenue, growth rate, projections |
| `/revenue/by-program` | Revenue per federal program |
| `/revenue/by-rep` | Revenue per BD representative |
| `/revenue/by-contact` | Revenue attribution per contact |
| `/revenue/forecast` | Forward-looking revenue forecast |
| `/revenue/margins` | Profit margins by program/contract |
| `/revenue/concentration` | Revenue concentration risk analysis |

### Deal Lifecycle (3 endpoints)

| Endpoint | Returns |
|----------|---------|
| `/revenue/deals/analytics` | Deal pipeline analytics |
| `/revenue/deals/velocity` | Deal velocity metrics (avg time per stage) |
| `/revenue/deals/stale` | Stale deals requiring attention |

### ROI Analysis (4 endpoints)

| Endpoint | Returns |
|----------|---------|
| `/revenue/roi/campaigns` | ROI per outreach campaign |
| `/revenue/roi/contacts` | ROI per contact relationship |
| `/revenue/roi/programs` | ROI per program investment |
| `/revenue/roi/channels` | ROI per channel (email, call, meeting) |

### Other (2 endpoints)

| Endpoint | Returns |
|----------|---------|
| `/revenue/executive-summary` | Complete executive revenue summary |
| `/revenue/placements/record` | Record new placement/win |

---

## 47. Proposal & Capture API: 10 Endpoints <a name="proposal-api"></a>

**File:** `src/api/proposal_api.py`

### Document Generation

| # | Endpoint | Output |
|---|----------|--------|
| 1 | `POST /proposals/capability-statement` | Tailored capability statement |
| 2 | `POST /proposals/past-performance` | Past performance volume |
| 3 | `POST /proposals/compliance-matrix` | RFP compliance matrix |
| 4 | `POST /proposals/pricing/labor-categories` | Labor category definitions |
| 5 | `POST /proposals/pricing/rate-card` | Rate card generation |
| 6 | `POST /proposals/pricing/analysis` | Pricing competitive analysis |
| 7 | `POST /proposals/full-package` | Complete proposal package |
| 8 | `GET /proposals/templates` | Available proposal templates |
| 9 | `GET /proposals/history` | Previous proposal submissions |
| 10 | `POST /proposals/export/{proposal_id}` | Export proposal to document |

---

## 48. N8N Workflow Definitions: 17 Files <a name="n8n-workflows"></a>

**Directory:** `n8n/`

### Workflow Inventory

| # | File | Size | Purpose |
|---|------|------|---------|
| 1 | `Prime_TS_BD_Intelligence_System_v2.1.json` | 47KB | Master orchestration (300+ nodes) |
| 2 | `BD_Master_Orchestration_Workflow.json` | 19KB | Pipeline coordinator |
| 3 | `AI_Agent_workflow.json` | 7.3KB | Agent controller |
| 4 | `PTS_BD_WF1_Apify_Job_Scraper_Intake.json` | 8.5KB | Job ingestion trigger |
| 5 | `PTS_BD_WF2_AI_Enrichment_Processor.json` | 13KB | AI processing pipeline |
| 6 | `PTS_BD_WF3_Hub_to_BD_Opportunities.json` | ~10KB | Hub sync |
| 7 | `PTS_BD_WF4_Contact_Classification.json` | ~10KB | Contact classification |
| 8 | `PTS_BD_WF5_Hot_Lead_Alerts.json` | ~8KB | Alert generation |
| 9 | `PTS_BD_WF6_Weekly_Summary_Report.json` | ~12KB | Weekly reporting |
| 10-17 | Additional specialized workflows | 8-28KB each | Domain-specific automation |

### Workflow Trigger Types

- **Schedule Triggers:** Cron-based (daily scraping at 06:00, weekly reports on Fridays)
- **Manual Triggers:** User-initiated via dashboard WorkflowControl page
- **Webhook Triggers:** External events (Apify completion, Notion updates, SAM.gov feeds)
- **File Watcher Triggers:** `pipeline_state.json`, `alert_state.json` changes

### Master Orchestration Workflow (WF v2.1)

The 47KB master workflow contains 300+ nodes orchestrating the full BD intelligence pipeline:
1. Apify scraper trigger → job ingestion
2. AI enrichment → program mapping → BD scoring
3. Contact classification → tier assignment
4. QA validation → auto-approve or review queue
5. Playbook generation → Notion export
6. Alert evaluation → Slack/webhook notifications
7. Weekly summary compilation

---

## 49. MCP Server Configurations <a name="mcp-config"></a>

**File:** `mcp/claude_desktop_config.json`

### 8 MCP Servers (External Claude Desktop Config)

| # | Server | Command | Transport | Key Capability |
|---|--------|---------|-----------|---------------|
| 1 | `notion` | npx @notionhq/notion-mcp-server | STDIO | Notion database R/W |
| 2 | `apify` | npx @apify/actors-mcp-server | STDIO | Web scraping actors |
| 3 | `n8n-mcp` | npx n8n-mcp@latest | STDIO | Workflow trigger/manage |
| 4 | `mapify` | node mcp/mapify-mcp-server/build/index.js | STDIO | Mind map generation |
| 5 | `windows-mcp` | uvx windows-mcp | STDIO | Windows system control |
| 6 | `computer-control` | uvx computer-control-mcp@latest | STDIO | Chrome/Edge/Electron control |
| 7 | `desktop-commander` | npx @wonderwhy-er/desktop-commander | STDIO | Desktop automation |
| 8 | `sequential-thinking` | npx @modelcontextprotocol/server-sequential-thinking | STDIO | Chain-of-thought reasoning |

### Knowledge MCP Server (Internal)

**File:** `mcp/knowledge-mcp-server/src/index.ts` (608 LOC)

**30+ MCP Tools exposed to Claude Code:**
- `search_knowledge` — Semantic search across collections
- `ask_knowledge` — RAG-powered Q&A with sources
- `get_program_intel` — Full program intelligence report
- `get_company_contacts` — Find contacts at a company
- `get_pipeline_status` — Pipeline health
- `get_system_stats` — Collection counts and health
- `ingest_document` — Add document to knowledge base
- Plus 20+ more domain-specific tools

---

## 50. Contact Lookup & Ranking System <a name="contact-lookup"></a>

**File:** `Engine3_OrgChart/scripts/contact_lookup.py`

### Contact Database

Loads contacts from 4 CSV files:
1. `DCGS_Contacts.csv`
2. `GDIT PTS Contacts.csv`
3. `GDIT_Other_Contacts.csv`
4. `Lockheed Contact.csv`

**Builds indices by:** program name, company name (with fuzzy matching)

### Contact Dataclass

```python
@dataclass
class Contact:
    name: str
    first_name: str = ""
    title: str = ""
    company: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    location: str = ""
    state: str = ""
    program: str = ""
```

### Title Priority Ranking

```python
PRIORITY_TITLES = {
    "critical": ["program manager", "director", "vp", "vice president"],
    "high": ["senior manager", "technical lead", "principal"],
    "medium": ["recruiter", "manager", "lead"],
    "standard": ["engineer", "analyst", "specialist"]
}
```

### Ranking Formula

```
score = (title_priority × 10) - (3 if has_email else 0)
```
Lower score = higher priority. Contacts with email addresses get a 3-point bonus.

### Lookup Functions

- `search_by_program(name)` — Fuzzy match against program index
- `search_by_company(name)` — Fuzzy match with GDIT alias expansion
- `rank_contacts(contacts, limit=5)` — Score and return top N
- `lookup_contacts(program?, contractor?, location?, limit?)` → ContactLookupResult
- `format_contacts_for_briefing(result)` → Markdown with names, titles, contact info
- `format_contacts_json(result)` → JSON array for API responses

---

## 51. Configuration Deep Dive <a name="config-deep-dive"></a>

### Centralized Settings

**File:** `config/settings.py`

```python
# LLM Configuration
default_llm_model = "claude-sonnet-4-20250514"
default_embedding_model = "text-embedding-3-small"
embedding_dimensions = 1536

# Vector Database
qdrant_url = "http://localhost:6333"

# Notion Database IDs
notion_db_dcgs_contacts = "2ccdef65-baa5-8087-a53b-000ba596128e"
notion_db_federal_programs = "06cd9b22-5d6b-4d37-b0d3-ba99da4971fa"
notion_db_bd_opportunities = "2bcdef65-baa5-80ed-bd95-000b2f898e17"
notion_db_program_mapping_hub = "f57792c1-605b-424c-8830-23ab41c47137"

# BD Scoring Thresholds
bd_tier_hot_min = 80     # >= 80: immediate outreach
bd_tier_warm_min = 50    # >= 50: weekly follow-up

# Processing
batch_size = 10
process_interval_minutes = 15
```

### Engine-Specific Configurations

**Program Mapping Config:** `Engine2_ProgramMapping/Configurations/ProgramMapping_Config.json` (282 lines)
- Match confidence thresholds (Direct ≥ 0.70, Fuzzy 0.50-0.70, Inferred < 0.50)
- Field extraction prompts for LLM
- Export column definitions (24 columns for Notion, full JSON for n8n)

**OrgChart Config:** `Engine3_OrgChart/Configurations/OrgChart_Config.json` (92 lines)
- Tier definitions and regex patterns
- Location-to-program mapping
- Emoji and outreach sequence mappings

### Required Environment Variables

```
ANTHROPIC_API_KEY     — Claude API (required)
OPENAI_API_KEY        — Embeddings (required)
NOTION_TOKEN          — Notion integration
APIFY_API_TOKEN       — Job scraping
N8N_API_KEY           — Workflow orchestration
SLACK_WEBHOOK_URL     — Alert delivery
QDRANT_URL            — Vector database (default: http://localhost:6333)
```

---

## 52. Token Economics & Cost Modeling <a name="token-economics"></a>

### Daily Budget Allocation

| Resource | Limit | Estimated Cost |
|----------|-------|---------------|
| API tokens (Claude) | 500,000/day | ~$5.00/day |
| BD API calls | 200/day | Free (internal) |
| Pipeline runs | 3/day | ~$0.50/run in embeddings |
| Qdrant ingests | 100 records/day | Free (local) |
| **Total daily budget** | | **~$6.50/day** |

### Per-Action Token Costs

| Action | Estimated Tokens | Cost |
|--------|-----------------|------|
| `/ask/smart` query | ~2,000 | $0.02 |
| `/search` query | ~500 | $0.005 |
| Pattern scan cycle | ~5,000 | $0.05 |
| Meta-learner cycle | ~8,000 | $0.08 |
| Swarm DAG (campaign_build, 10 steps) | ~15,000 | $0.15 |
| Playbook generation | ~10,000 | $0.10 |
| Memory consolidation | ~3,000 | $0.03 |
| Memory reflection | ~5,000 | $0.05 |
| Embedding (text-embedding-3-small) | ~200/record | $0.0001/record |

### OODA Cycle Cost per Run

| Phase | API Calls | Estimated Tokens | Cost |
|-------|-----------|-----------------|------|
| OBSERVE | 5-8 | ~3,000 | $0.03 |
| ORIENT | 3-5 | ~15,000 | $0.15 |
| DECIDE | 1-2 | ~2,000 | $0.02 |
| ACT (1 task) | 5-15 | ~10,000-20,000 | $0.10-$0.20 |
| LEARN | 3-5 | ~8,000 | $0.08 |
| **Total per cycle** | **17-35** | **~38,000-48,000** | **$0.38-$0.48** |

### Daily Capacity at Budget Limit

At ~$6.50/day and ~$0.43/cycle average:
- **~15 OODA cycles per day** (every ~30 minutes for 8 hours)
- **~5-8 swarm tasks executed** per day
- **~3 playbooks generated** per day
- Remaining budget for ad-hoc queries and learning

### Free-Only Mode Capabilities

When budget exhausted, these actions cost $0:
- Local git scanning (6 repos)
- Memory consolidation/reflection (if data already in memory)
- Task queue re-prioritization
- Report generation from cached data
- Skill statistics analysis
- File watcher event processing

---

## 53. Complete API Endpoint Census <a name="api-census"></a>

### Total: 300+ Endpoints Across 21 Router Modules

| Module | Prefix | Count | Phase |
|--------|--------|-------|-------|
| Core V2 (contacts/programs/jobs) | `/api/v2/*` | 15 | Phase 22A |
| Search | `/search` | 3 | Base |
| Ask/Smart | `/ask/*` | 4 | Phase 25A |
| RAG | `/rag/*` | 6 | Phase 26A |
| Agents | `/agent/*` | 8 | Phase 27A |
| Knowledge Graph | `/graph/*`, `/bdgraph/*` | 12 | Phase 28A |
| Memory | `/memory/*` | 12 | Phase 42A |
| NLQ | `/nlq/*` | 9 | Phase 30A |
| Dashboard Data | `/dashboard/*` | 8 | Phase 31A |
| Pipeline | `/pipeline/*` | 6 | Phase 31A |
| QA | `/qa/*` | 5 | Phase 31A |
| Alerts | `/alerts/*` | 4 | Phase 31A |
| Analytics | `/analytics/*` | 10 | Phase 32A |
| Predictive | `/predict/*` | 8 | Phase 33A |
| Relationships | `/relationships/*` | 14 | Phase 34A |
| Intelligence | `/api/intelligence/*` | 13 | Phase 44A |
| Swarm | `/swarm/*` | 10 | Phase 41A |
| Streaming | `/sse/*`, `/realtime/*` | 6 | Phase 36A |
| Knowledge Mgmt | `/knowledge/*` | 15 | Phase 37A |
| Collaboration | `/api/collab/*` | 12 | Phase 38A |
| Tenant/Auth | `/api/tenants/*`, `/api/auth/*` | 21 | Phase 39A |
| Revenue | `/revenue/*` | 16 | Phase 40A |
| Proposals | `/proposals/*` | 10 | Phase 40A |
| Voice | `/api/voice/*` | 12 | Phase 46A |
| Geo | `/geo/*` | 8 | Phase 35A |
| Embeddings | `/embeddings/*` | 5 | Phase 35A |
| Workflows | `/workflows/*` | 7 | Phase 36A |
| Data Governance | `/governance/*` | 12 | Phase 43A |
| MCP | `/mcp/*` | 8 | Phase 45A |
| Dify | `/dify/*` | 6 | Base |
| Ingest/Sync | `/ingest/*`, `/sync/*` | 8 | Base |
| **TOTAL** | | **~310+** | |

---

## 54. Dify Visual AI Integration <a name="dify-integration"></a>

**Directory:** `dify_integration/`

### Bridge Components

**DifyQdrantBridge** — Search 8,447+ Qdrant vectors from Dify visual workflows
**DifyCrewAIBridge** — Invoke BD agents from Dify apps
**DifyN8NBridge** — Trigger n8n workflows from Dify

### 6 Pre-Built App Templates

| # | App | Purpose | Primary Data Source |
|---|-----|---------|-------------------|
| 1 | BD Research Chat | Research assistant | Qdrant documents collection |
| 2 | Call Prep Generator | Generate call briefs | CrewAI agents + contacts |
| 3 | Pipeline Controller | NL control of n8n | n8n workflows |
| 4 | Outreach Drafter | Personalized BD messages | Contacts + programs |
| 5 | Program Analyzer | Multi-agent analysis | All collections |
| 6 | Competitor Intel | Competitor research | Jobs + programs |

### External Tools (34 total)

**File:** `dify_integration/tools_config.py`

Configures 34 external tools across categories:
- Qdrant vector search tools
- Agent invocation tools
- N8n workflow triggers
- Knowledge graph queries
- Memory system access
- Analytics endpoints

### Dify-Compatible Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/dify/knowledge/search` | External knowledge search |
| `/dify/knowledge/rag` | RAG queries |
| `/dify/agents/invoke` | Invoke BD agents |
| `/dify/n8n/trigger/{workflow}` | Trigger n8n workflows |

---

## 55. Auto Claude Task Definitions <a name="task-definitions"></a>

**File:** `TASKS.md`

The project contains structured task definitions designed for Auto Claude's Kanban board. Key tasks:

1. **New Job Ingestion & Deduplication Pipeline** — Parse Apify JSON, deduplicate against Notion, create records, detect federal vs. commercial sources
2. **Program Knowledge Base Prep** — Build keyword dictionary, compute program embeddings, create reverse index
3. **Job→Program Mapping Engine** — Core matching logic: keyword scoring + semantic vector search + combined confidence
4. **Additional tasks** for contact classification, playbook generation, QA validation, scoring, and pipeline integration

Each task includes: Title, Description, Requirements, Key Files, Agent Profile (model + reasoning level).

---

## 56. Updated System Statistics <a name="updated-stats"></a>

### Complete Codebase Metrics

| Category | Count |
|----------|-------|
| **API Router Modules** | 21+ |
| **Total API Endpoints** | 310+ |
| **Qdrant Collections** | 9 |
| **Qdrant Total Vectors** | 8,447+ |
| **SQL Tables (Bullhorn)** | 14 |
| **SQL Database Size** | 293 MB |
| **MCP Servers (Internal Registry)** | 9 |
| **MCP Servers (External Desktop)** | 8 |
| **NLQ Query Intents** | 14 |
| **Strategic Pattern Types** | 7 |
| **Intelligence Domains** | 5 |
| **Opportunity Scoring Dimensions** | 6 |
| **Relationship Scoring Factors** | 6 |
| **Briefing Types** | 4 |
| **DAG Templates** | 5 |
| **Swarm Worker Types** | 8 |
| **Memory Tiers** | 3 |
| **LightRAG Entity Types** | 7 |
| **LightRAG Relationship Patterns** | 13 |
| **Known LightRAG Entities** | 65+ |
| **Prediction Models** | 4 |
| **Embedding Dimensions** | 5 |
| **Playbook Templates** | 4 |
| **Location Markets** | 8 |
| **Contact Hierarchy Tiers** | 6 |
| **Scoring Components** | 7 |
| **QA Rules** | 5 |
| **Alert Rules** | 4 |
| **CrewAI Agents** | 8 |
| **Dashboard Pages** | 47+ |
| **Vite Proxy Routes** | 51 |
| **Hub API Client Methods** | 45+ |
| **React Query Hooks** | 14 |
| **Voice API Endpoints** | 12 |
| **Collaboration API Endpoints** | 12 |
| **Tenant/Auth Endpoints** | 21 |
| **Revenue API Endpoints** | 16 |
| **Proposal API Endpoints** | 10 |
| **N8N Workflow Files** | 17 |
| **Dify App Templates** | 6 |
| **Dify External Tools** | 34 |
| **Federal Programs Indexed** | 388 |
| **Location-to-Program Mappings** | 47 |
| **Competitor Watch List** | 10 |
| **OpenClaw Existing Skills** | 75+ |
| **OpenClaw Proposed New Skills** | 6 |
| **Lines of Code (Key Files)** | 15,000+ across 20+ core modules |

### OpenClaw Autonomous Architecture Totals

| Component | Count |
|-----------|-------|
| OODA Cycle Phases | 5 (Observe, Orient, Decide, Act, Learn) |
| Self-Discovery Mechanisms | 7 |
| Budget Control Limits | 4 (tokens, API calls, pipeline runs, ingests) |
| Write Safety Tiers | 4 (Autonomous, Auto-Approved, Human Approval, Never) |
| Event Sources | 3 (Pipeline, Webhooks, File Watchers) |
| Event→Action Mappings | 8 |
| Circuit Breaker States | 3 (Closed, Open, Half-Open) |
| Monitoring Metrics | 10 |
| Alert Channels | 3 (Slack, n8n webhook, history file) |
| Failure Recovery Patterns | 7 |
| Cron Schedules | 5 proposed new + 5 existing |
| Implementation Phases | 5 |
| Verification Tests | 22+ |
| E2E Test Scenarios | 8 |

---

*End of document. Total systems analyzed: 21 router modules, 310+ API endpoints, 9 Qdrant collections, 14 SQL tables, 9+8 MCP servers, 14 NLQ intents, 7 pattern types, 5 intelligence domains, 6+6 scoring dimensions, 4 briefing types, 5 DAG templates, 8 worker types, 3 memory tiers, 7 entity types, 13 relationship patterns, 65+ known entities, 4 prediction models, 5 embedding dimensions, 4 playbook templates, 8 location markets, 8 CrewAI agents, 47+ dashboard pages, 12 voice endpoints, 12 collaboration endpoints, 21 tenant/auth endpoints, 16 revenue endpoints, 10 proposal endpoints, 17 n8n workflows, 6 Dify apps, 34 Dify tools, 6-tier contact classification, 7-component scoring algorithm, 5-step QA root cause analysis, 4 alert rules, 75+ existing skills, 6 proposed new skills, and a complete autonomous OODA+Learn architecture proposal with token economics, event-driven architecture, failure recovery, and self-improvement flywheel.*
