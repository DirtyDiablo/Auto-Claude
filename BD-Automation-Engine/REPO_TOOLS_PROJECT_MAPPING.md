# REPO TOOLS → PROJECT MAPPING
## Strategic Tool Selection Based on Capability Audits

**Generated:** January 26, 2026  
**Purpose:** Map 52 repo tools to specific project enhancement opportunities

---

## TOOL SELECTION METHODOLOGY

Based on the capability audits, each tool is evaluated for:
1. **Gap Closure** - Does it fix a known gap?
2. **Enhancement** - Does it improve existing capability?
3. **New Capability** - Does it add something new?
4. **Integration Effort** - How hard to add?

### Priority Legend
- 🔴 **CRITICAL** - Deploy immediately, high ROI
- 🟠 **HIGH** - Deploy within 2 weeks
- 🟡 **MEDIUM** - Deploy within 1 month
- ⚪ **LOW** - Optional/Future consideration

---

## TERMINAL 1: BD-AUTOMATION-ENGINE (Hub)
**Current Strengths:** FastAPI, Qdrant (8,447 vectors), Job Pipeline  
**Current Gaps:** LightRAG not exposed, BM25 not exposed, Mem0 sporadic, No graph queries

### Memory & Context Enhancement

| Tool | Priority | Why | Integration |
|------|----------|-----|-------------|
| **Mem0** | 🔴 CRITICAL | Already installed but sporadic. Fix config to use Qdrant backend | 2 hours |
| **Redis-VL** | 🔴 CRITICAL | Semantic caching for API responses, 10x speedup | 4 hours |
| **Supermemory** | 🟡 MEDIUM | 50M token capacity, MCP integration | 1 day |

**Implementation:**
```python
# Already created in ENHANCEMENT_IMPLEMENTATION_GUIDE_V2.md
# Key: Use Qdrant as Mem0 backend (not ChromaDB) for unified storage
```

### RAG & Retrieval Enhancement

| Tool | Priority | Why | Integration |
|------|----------|-----|-------------|
| **LightRAG** | 🔴 CRITICAL | Already have data! Just expose via API endpoints | 2 hours |
| **BM25** | 🔴 CRITICAL | Code exists, just add endpoint. Hybrid search critical | 2 hours |
| **PageIndex** | 🟠 HIGH | Vectorless RAG, 98.7% accuracy, explainable retrieval | 4 hours |
| **UltraRAG** | 🟠 HIGH | Multi-step reasoning, YAML pipelines | 1 day |
| **RAGAS** | 🟡 MEDIUM | Measure RAG quality, continuous improvement | 4 hours |

**Implementation Priority:**
```
Week 1: LightRAG API + BM25 Hybrid → Immediate search improvement
Week 2: PageIndex + UltraRAG → Advanced retrieval strategies
Week 3: RAGAS → Quality measurement and optimization
```

### Knowledge Graph Enhancement

| Tool | Priority | Why | Integration |
|------|----------|-----|-------------|
| **LightRAG Graph** | 🔴 CRITICAL | Already have! Extract entities/relationships | Included above |
| **GraphRAG** | 🟠 HIGH | Microsoft's 70-80% RAG improvement | 1 day |
| **Graphiti** | 🟡 MEDIUM | Temporal graphs - track relationships over time | 2 days |

**Key Entities to Model:**
```
Contractors ←→ Programs (subcontracts_to)
Contacts ←→ Companies (works_for)
Contacts ←→ Programs (works_on)
Jobs ←→ Programs (belongs_to)
Jobs ←→ Skills (requires)
Programs ←→ Locations (has_site)
```

### Agent Orchestration

| Tool | Priority | Why | Integration |
|------|----------|-----|-------------|
| **CrewAI** | 🟠 HIGH | Already have framework. Build BD-specific agents | 1 day |
| **LangGraph** | 🟠 HIGH | Durable workflows, checkpointing, human-in-loop | 1 day |
| **Claude Agent SDK** | 🟡 MEDIUM | Official SDK, type-safe operations | 4 hours |

**Agent Roles:**
```python
# Research Agent: Gather program/contract intelligence
# Analyst Agent: Score opportunities, identify patterns  
# Strategy Agent: Develop BD approach, prioritize contacts
# Writer Agent: Generate playbooks, scripts, reports
```

### Document Processing

| Tool | Priority | Why | Integration |
|------|----------|-----|-------------|
| **Docling** | 🟠 HIGH | Already have script! Connect to pipeline | 4 hours |
| **ExtractThinker** | 🟠 HIGH | LLM-powered extraction to Pydantic models | 4 hours |
| **Anthropic Skills** | 🟡 MEDIUM | PDF/DOCX/XLSX processing workflows | Already using |

---

## TERMINAL 2: DATA-SCRAPER (Data Platform)
**Current Strengths:** 4.6GB contracts, 36 program folders, Federal APIs, MCP servers  
**Current Gaps:** apify-client missing, No scheduling, Scrapers not implemented

### Web Scraping Enhancement

| Tool | Priority | Why | Integration |
|------|----------|-----|-------------|
| **Apify Client** | 🔴 CRITICAL | Already using Apify! Just need client installed | 30 min |
| **Crawlee Python** | 🟠 HIGH | Self-hosted alternative, same patterns | 1 day |
| **Scrapling** | 🟠 HIGH | Survives site redesigns, learns selectors | 4 hours |
| **Firecrawl** | 🟡 MEDIUM | LLM-ready markdown output | 4 hours |
| **Crawl4AI** | 🟡 MEDIUM | BFS/DFS strategies, incremental crawling | 4 hours |

**Priority Actions:**
```bash
# IMMEDIATE
pip install apify-client apscheduler

# THEN
# 1. Create scrapers/insight_global.py
# 2. Create scrapers/apex_systems.py  
# 3. Create scrapers/teksystems.py
```

### Federal Data Enhancement

| Tool | Priority | Why | Integration |
|------|----------|-----|-------------|
| **FPDS Parser** | 🟠 HIGH | Already caching queries. Add structured parser | 2 hours |
| **USASpending Client** | 🟠 HIGH | Batch downloads, organized output | Already have |
| **GSA Scraper** | 🟡 MEDIUM | SAM.gov patterns, document extraction | Reference |
| **PyrateLimiter** | 🟠 HIGH | Federal API compliance, rate limiting | 2 hours |

### Knowledge Base Enhancement

| Tool | Priority | Why | Integration |
|------|----------|-----|-------------|
| **SQLite** | ✅ HAVE | knowledge.db, metadata.sqlite exist | Enhance schema |
| **ChromaDB** | ✅ HAVE | vector_db/ exists | Connect to Hub |
| **Pydantic** | 🔴 CRITICAL | Unified schemas across all data | 1 day |

**Unified Schema Implementation:**
```python
# Create unified Pydantic models that ALL projects use
# Already started with 28-field job schema
# Extend to: Contact, Program, Contract, Opportunity
```

### MCP Server Enhancement

| Tool | Priority | Why | Integration |
|------|----------|-----|-------------|
| **capture-mcp** | ✅ READY | 15 federal tools, just configure in Claude | 30 min |
| **scraper-mcp** | ✅ READY | build/index.js exists | 30 min |
| **MCP Servers (Official)** | 🟡 MEDIUM | Filesystem, Git, Notion servers | As needed |

---

## TERMINAL 3: N8N-BUILDER (Contract Intelligence)
**Current Strengths:** 1,400 programs, 268 Bullhorn files, 10 active N8N workflows  
**Current Gaps:** No Python N8N client, 27 inactive workflows

### Workflow Automation Enhancement

| Tool | Priority | Why | Integration |
|------|----------|-----|-------------|
| **n8n-MCP Server** | 🔴 CRITICAL | Claude can build n8n workflows via MCP | 2 hours |
| **Awesome-n8n** | 🟠 HIGH | Community nodes (Qdrant, Apify integration) | Reference |
| **Prefect** | 🟡 MEDIUM | Python alternative if n8n insufficient | 1 day |

**N8N Cleanup:**
```
Current: 37 workflows (10 active, 27 inactive)
Action: Audit inactive, delete test workflows, consolidate
Target: 15-20 well-documented workflows
```

### Task Queue Enhancement

| Tool | Priority | Why | Integration |
|------|----------|-----|-------------|
| **Celery** | 🟠 HIGH | Distributed task queue, beat scheduler | 1 day |
| **Redis Queue (RQ)** | 🟡 MEDIUM | Simpler alternative for basic queuing | 4 hours |
| **Aiocache** | 🟡 MEDIUM | Async caching for API responses | 2 hours |

### Agent Deployment

| Tool | Priority | Why | Integration |
|------|----------|-----|-------------|
| **Sim.ai** | 🟡 MEDIUM | Visual agent workflow builder | Evaluate |
| **Eigent** | 🟡 MEDIUM | Multi-agent desktop, 100% local | Evaluate |
| **browser-use** | 🟡 MEDIUM | AI browser automation for portal access | Evaluate |

---

## CROSS-PROJECT TOOLS (All Terminals)

### Data Validation (ALL)

| Tool | Priority | Why | Integration |
|------|----------|-----|-------------|
| **Pydantic** | 🔴 CRITICAL | Unified schemas, validation, JSON Schema | 1 day |

**Unified Models Needed:**
```python
class StandardizedJob(BaseModel):
    """28-field job schema - use EVERYWHERE"""
    
class Contact(BaseModel):
    """Contact with tier, program, location"""
    
class FederalProgram(BaseModel):
    """Program with prime, sub, contract value"""
    
class Contract(BaseModel):
    """Contract with PIID, dates, value"""
```

### Skill Generation (ALL)

| Tool | Priority | Why | Integration |
|------|----------|-----|-------------|
| **Skill_Seekers** | 🟠 HIGH | Auto-generate Claude skills from docs | 4 hours |
| **Superpowers** | 🟡 MEDIUM | 20+ battle-tested skills for dev | Reference |

---

## IMPLEMENTATION ROADMAP

### Week 1: Critical Gap Closure

| Day | Terminal | Action |
|-----|----------|--------|
| Mon | T2 | Install apify-client, apscheduler |
| Mon | T2 | Set BD_HUB_URL, ANTHROPIC_API_KEY, NOTION_API_KEY |
| Tue | T1 | Fix Mem0 with Qdrant backend |
| Tue | T1 | Expose LightRAG via /rag/lightrag endpoint |
| Wed | T1 | Expose BM25 via /rag/bm25 endpoint |
| Wed | T1 | Create RAG Router (strategy selector) |
| Thu | T1 | Add Redis-VL semantic caching |
| Thu | T2 | Configure MCP servers in Claude |
| Fri | ALL | Test cross-terminal connectivity |

### Week 2: Enhancement Layer

| Day | Terminal | Action |
|-----|----------|--------|
| Mon | T1 | Add PageIndex (vectorless retrieval) |
| Mon | T1 | Add UltraRAG (multi-step reasoning) |
| Tue | T1 | Implement Knowledge Graph layer |
| Tue | T1 | Add GraphRAG entity extraction |
| Wed | T1 | Build CrewAI BD agents |
| Wed | T1 | Add LangGraph workflows |
| Thu | T2 | Create scraper implementations |
| Thu | T2 | Add PyrateLimiter for federal APIs |
| Fri | T3 | Audit and clean up N8N workflows |
| Fri | T3 | Add n8n-MCP server integration |

### Week 3: Advanced Features

| Day | Terminal | Action |
|-----|----------|--------|
| Mon | T1 | Connect Docling document pipeline |
| Mon | T1 | Add ExtractThinker extraction |
| Tue | T1 | Implement RAGAS evaluation |
| Tue | T3 | Add Celery task queue |
| Wed | ALL | Create unified Pydantic schemas |
| Wed | ALL | Test full pipeline end-to-end |
| Thu | ALL | Performance optimization |
| Fri | ALL | Documentation and handoff |

---

## TOOL INSTALLATION COMMANDS

### Terminal 1 (BD-Automation-Engine)

```bash
# Memory & Caching
pip install mem0ai redisvl redis

# RAG Enhancement
pip install pageindex 
pip install ultrarag

# Knowledge Graph
pip install graphrag

# Agents
pip install crewai langgraph langchain-anthropic

# Document Processing
pip install docling extract-thinker

# Evaluation
pip install ragas

# Optional: Task Queue
pip install celery
```

### Terminal 2 (Data-Scraper)

```bash
# CRITICAL - Missing packages
pip install apify-client apscheduler

# Scraping Enhancement
pip install crawlee scrapling
pip install firecrawl-py crawl4ai

# Rate Limiting
pip install pyrate-limiter

# Data Validation
pip install pydantic
```

### Terminal 3 (N8N-Builder)

```bash
# Task Queue
pip install celery rq

# Caching
pip install aiocache

# Data Validation
pip install pydantic
```

---

## EXPECTED OUTCOMES

### After Week 1
- ✅ All terminals can communicate
- ✅ Memory layer working reliably
- ✅ Hybrid RAG search (vector + keyword)
- ✅ Job scraping automated

### After Week 2
- ✅ Knowledge graph capturing relationships
- ✅ AI agents generating BD intelligence
- ✅ Multi-strategy RAG routing
- ✅ N8N workflows cleaned up

### After Week 3
- ✅ Document processing automated
- ✅ RAG quality measured and optimized
- ✅ Unified schemas across all projects
- ✅ Full pipeline operational

---

## ROI ESTIMATES

| Enhancement | Expected Benefit |
|-------------|------------------|
| Mem0 + Redis-VL | 10x faster repeated queries |
| LightRAG + BM25 Hybrid | 40% better retrieval accuracy |
| Knowledge Graph | Relationship-based intelligence |
| CrewAI Agents | 5x faster playbook generation |
| Docling Pipeline | Process any document automatically |
| Unified Schemas | Eliminate data quality issues |
| N8N Cleanup | Maintainable automation |

**Total Implementation Effort:** ~3 weeks  
**Expected Productivity Gain:** 50-70% faster BD operations

---

*Document generated: January 26, 2026*
