# BD-Automation-Engine Project Instructions

## Project Overview

PTS BD Intelligence System for federal defense contract staffing. Targets thousands of federal defense contracts matching these criteria: (1) subcontracting staffing firms involved, (2) $100M+ contract value or 100+ subcontractors, (3) requires security clearance, (4) not already assigned to an existing PTS account manager.

This is an 8-engine pipeline for Business Development automation:
- **Engine 1:** Apify Job Scraper (external)
- **Engine 2:** Program Mapping (job-to-program matching)
- **Engine 3:** OrgChart Contact Classification
- **Engine 4:** BD Playbook Generator
- **Engine 5:** BD Priority Scoring
- **Engine 6:** QA & Alerts
- **Engine 7:** Bullhorn ETL (CRM data extraction)
- **Engine 8:** AI Knowledge System (semantic search, RAG)

---

## Git Workflow Strategy

**CRITICAL: This project uses a feature branch strategy. Do NOT merge to develop/main.**

### Branch Structure

```
YOUR FORK (DirtyDiablo/Auto-Claude)
│
├── main ──────────────────── (original Auto Claude - don't touch)
├── develop ───────────────── (original Auto Claude - don't touch)
│
└── claude/setup-auto-claude-IrK21 ◄── YOUR WORKING BRANCH
    └── All BD Engine development happens here
```

### Working Branch
- **Name:** `claude/setup-auto-claude-IrK21`
- **Purpose:** All BD-Automation-Engine development
- **Push to:** `origin/claude/setup-auto-claude-IrK21`

### Git Commands

```bash
# Daily work - always be on your branch
git checkout claude/setup-auto-claude-IrK21

# Push your work
git push -u origin claude/setup-auto-claude-IrK21

# Sync upstream Auto Claude updates (only when you want new features)
git fetch upstream
git merge upstream/develop
# Resolve any conflicts, then push
```

### DO NOT:
- Push to `develop` or `main` branches
- Create PRs to merge into develop/main
- Merge BD Engine work into original Auto Claude branches

### DO:
- Keep all work on `claude/setup-auto-claude-IrK21`
- Sync upstream only when you want new Auto Claude features
- Commit frequently with descriptive messages
- Use conventional commit format: `feat:`, `fix:`, `docs:`, `chore:`

---

## Project Structure

```
BD-Automation-Engine/
├── Engine1_Scraper/          # Apify actor configs
├── Engine2_ProgramMapping/   # Job standardization + program matching
│   ├── scripts/
│   │   ├── job_standardizer.py    # LLM-powered field extraction
│   │   ├── program_mapper.py      # Multi-signal program matching
│   │   ├── pipeline.py            # Full 7-stage pipeline
│   │   └── exporters.py           # Notion CSV + n8n JSON export
│   └── data/
│       └── Federal_Programs_*.csv # 388 federal programs
├── Engine3_OrgChart/         # Contact classification
│   └── scripts/
│       └── contact_classifier.py  # 6-tier hierarchy classification
├── Engine4_Playbook/         # BD playbook generation
│   └── scripts/
│       └── bd_playbook_generator.py
├── Engine5_Scoring/          # BD priority scoring
│   └── scripts/
│       └── bd_scoring.py          # 0-100 scoring algorithm
├── Engine6_QA/               # Quality assurance
├── Engine7_BullhornETL/      # CRM data extraction
│   └── data/bullhorn.db      # 293 MB SQLite database
├── Engine8_Knowledge/        # AI Knowledge System
│   ├── scripts/              # Vector store, indexer, RAG
│   ├── api.py                # FastAPI server (:8100)
│   └── data/qdrant/          # Vector database (8,447 records)
├── mcp/knowledge-mcp-server/ # MCP server for Claude Code
├── dify_integration/         # Dify visual AI orchestration bridges
├── docs/                     # Documentation
├── n8n/                      # Workflow definitions
├── services/                 # Integration services
├── tests/                    # Test suite
└── outputs/                  # Generated files (gitignored)
```

---

## Key Configuration Files

| File | Purpose |
|------|---------|
| `.env` | API keys (NEVER commit) |
| `.env.example` | Template with placeholders |
| `requirements.txt` | Python dependencies |
| `.mcp.json` | MCP server configuration |
| `Configurations/*.json` | Engine-specific configs |

---

## API Keys Required

Set in `.env` (copy from `.env.example`):
- `ANTHROPIC_API_KEY` - Claude API
- `OPENAI_API_KEY` - Embeddings
- `NOTION_TOKEN` - Notion integration
- `APIFY_API_TOKEN` - Job scraping
- `N8N_API_KEY` - Workflow orchestration

---

## Running the Pipeline

```bash
# Single engine
python Engine2_ProgramMapping/scripts/pipeline.py

# Full pipeline (when orchestrator is ready)
python orchestrator.py --input jobs.json

# Tests
pytest tests/ -v
```

---

## Notion Database IDs

```
DCGS Contacts:      2ccdef65-baa5-8087-a53b-000ba596128e
GDIT Jobs:          2563119e7914442cbe0fb86904a957a1
Program Mapping:    f57792c1-605b-424c-8830-23ab41c47137
Federal Programs:   06cd9b22-5d6b-4d37-b0d3-ba99da4971fa
BD Opportunities:   2bcdef65-baa5-80ed-bd95-000b2f898e17
```

---

## Development Guidelines

1. **Each engine is independent** - Modify one engine without affecting others
2. **Use existing patterns** - Follow the code style in existing scripts
3. **Test before commit** - Run `pytest tests/` before pushing
4. **Document changes** - Update relevant README if adding features
5. **Conventional commits** - Use `feat:`, `fix:`, `docs:`, `chore:` prefixes

---

## AI Knowledge Base (Engine 8)

This project has a **semantic knowledge base** with 8,447+ indexed records for AI-powered search and RAG.

### Starting the Knowledge API
```bash
python Engine8_Knowledge/api.py
# Runs on http://localhost:8100
```

### Collections Available
| Collection | Records | Description |
|------------|---------|-------------|
| contacts | 7,337 | CRM contacts with tier classification |
| programs | 401 | Federal programs and contracts |
| documents | 205 | Past performance, briefings |
| activities | 500 | Call notes, meeting records |
| jobs | 4 | Job postings with BD scores |

### MCP Tools (when API is running)
- `search_knowledge` - Semantic search across collections
- `ask_knowledge` - RAG-powered Q&A with sources
- `get_program_intel` - Full program intelligence report
- `get_company_contacts` - Find contacts at a company

### Example Queries
- "Find Tier 1 contacts at Leidos working on cleared programs"
- "What programs does Northrop Grumman prime?"
- "Who are the key decision makers for GBSD?"
- "What past performance does GDIT have on ISR programs?"
- "Show contracts with 100+ subcontractors requiring TS/SCI"

### CLI Search
```bash
python Engine8_Knowledge/scripts/vector_store.py --search "cleared defense analyst" --collection contacts
```

### Documentation
- `docs/AI_FILESYSTEM_GUIDE.md` - Complete usage guide
- `docs/RAG_USAGE_GUIDE.md` - RAG patterns and examples
- `docs/KNOWLEDGE_SYSTEM_GUIDE.md` - Architecture details

---

## Dify Integration (Visual AI Orchestration)

Dify provides a **visual AI workflow builder** that complements your existing stack.

### What Dify Adds
- **Visual AI Workflow Builder** - Drag-drop instead of code
- **Prompt IDE** - A/B test prompts without deployments
- **LLMOps Monitoring** - Token usage, latency, quality metrics
- **200+ LLM Support** - Switch Claude ↔ GPT ↔ Llama visually
- **Team Access** - Non-technical BD team can build simple apps

### Starting Dify
```bash
# Clone and start Dify (requires ~6GB RAM)
git clone https://github.com/langgenius/dify.git
cd dify/docker
cp .env.example .env
# Add ANTHROPIC_API_KEY and OPENAI_API_KEY to .env
docker compose up -d
# Access: http://localhost:3000
```

### Bridge Components (`dify_integration/`)
| Bridge | Purpose |
|--------|---------|
| `DifyQdrantBridge` | Search your 8,447+ Qdrant vectors from Dify |
| `DifyCrewAIBridge` | Invoke BD agents from Dify apps |
| `DifyN8NBridge` | Trigger n8n workflows from Dify |
| `BDDifyApps` | Pre-built app templates |

### Pre-Built App Templates
- **BD Research Chat** - Research assistant using indexed documents
- **Call Prep Generator** - Generate call briefs using CrewAI agents
- **Pipeline Controller** - Natural language control of n8n workflows
- **Outreach Drafter** - Draft personalized BD messages
- **Program Analyzer** - Multi-agent program analysis
- **Competitor Intel** - Research competitors

### API Endpoints (when Knowledge API is running)
Dify-compatible endpoints at `/dify/*`:
- `/dify/knowledge/search` - External knowledge search
- `/dify/knowledge/rag` - RAG queries
- `/dify/agents/invoke` - Invoke BD agents
- `/dify/n8n/trigger/{workflow}` - Trigger n8n workflows

### Documentation
- `dify_integration/README.md` - Complete setup guide
- `dify_integration/tools_config.py` - 34 external tools

---

## Current Task Status

- ✅ Engine 1: Apify Scraper (configured)
- ✅ Engine 2: Program Mapping (complete)
- ✅ Engine 3: OrgChart Classification (complete)
- ✅ Engine 4: BD Playbook Generator (complete)
- ✅ Engine 5: BD Scoring (complete)
- 🔄 Engine 6: QA & Alerts (in progress)
- ✅ Engine 7: Bullhorn ETL (complete)
- ✅ Engine 8: AI Knowledge System (complete)
- ✅ Dify Integration: Visual AI Orchestration (complete)
- 🔜 Full Pipeline Integration (next)
## Antigravity Awesome Skills (850+ installed)

All skills from https://github.com/sickn33/antigravity-awesome-skills are installed in `.claude/skills/`.

### PTS Context Files (auto-loaded)
- `PTS_PLATFORM_CONTEXT.md` — Mission, architecture, priorities, tech stack
- `PTS_BD_ENGINE_CONTEXT.md` — 8-engine pipeline, Bullhorn, Neo4j
- `PTS_N8N_BUILDER_CONTEXT.md` — LangGraph workflows, federal APIs, N8N removal
- `PTS_DATA_SCRAPER_CONTEXT.md` — Scraping, classification, program mapping

### PTS Custom Skills
- `@pts-bd-pipeline` — 8-engine pipeline orchestration and scoring
- `@pts-federal-intel` — SAM.gov/FPDS/USASpending/Tango patterns
- `@pts-contact-ops` — Bullhorn CRM, 6-tier hierarchy, HUMINT methodology
- `@pts-arch-migration` — 3 to 2 repo consolidation, Supabase migration

### Key Skills by Next-Gen Rebuild Task

**Revenue Engine (Call Lists and Briefings)**
@pts-bd-pipeline @crewai @langgraph @autonomous-agents @rag-engineer

**Supabase Migration (SQLite to PostgreSQL + pgvector)**
@pts-arch-migration @database-migration @postgres-best-practices @postgresql
@supabase-automation @nextjs-supabase-auth @vector-database-engineer @vector-index-tuning

**LangGraph Workflows (N8N Replacement)**
@langgraph @langchain-architecture @workflow-automation @workflow-orchestration-patterns
@autonomous-agent-patterns @agent-memory-mcp @agent-memory-systems @parallel-agents

**Dashboard Rewrite (Next.js 16.1)**
@nextjs-best-practices @nextjs-app-router-patterns @react-patterns @react-best-practices
@react-flow-architect @react-flow-node-ts @react-state-management @zustand-store-ts
@tailwind-design-system @tailwind-patterns @frontend-design @ui-ux-pro-max

**API Consolidation (3 to 1 Server)**
@fastapi-pro @fastapi-templates @fastapi-router-py @api-design-principles
@api-documentation-generator @api-patterns @senior-architect @architecture

**Python Backend**
@python-pro @python-patterns @python-performance-optimization @async-python-patterns
@pydantic-models-py @python-packaging @uv-package-manager

**AI/Agent Pipeline**
@ai-engineer @ai-agents-architect @crewai @rag-implementation @embedding-strategies
@similarity-search-patterns @prompt-engineering @prompt-caching @llm-evaluation
@context-manager @context-window-management @conversation-memory @hybrid-search-implementation

**CI/CD and Infrastructure**
@docker-expert @github-automation @github-actions-templates @deployment-engineer
@deployment-procedures @terraform-specialist @observability-engineer @server-management

**Security (Federal-Grade)**
@api-security-best-practices @auth-implementation-patterns @security-auditor
@secrets-management @vulnerability-scanner @cc-skill-security-review @gdpr-data-handling

**Testing**
@test-driven-development @tdd-workflow @python-testing-patterns @testing-patterns
@webapp-testing @e2e-testing-patterns @systematic-debugging

**Planning and Documentation**
@brainstorming @doc-coauthoring @concise-planning @plan-writing @planning-with-files
@executing-plans @writing-plans @docs-architect @wiki-architect

**Code Quality and Review**
@clean-code @code-review-checklist @code-review-excellence @production-code-audit
@codebase-cleanup-tech-debt @legacy-modernizer @lint-and-validate

**Workflow Integrations**
@slack-automation @slack-bot-builder @notion-automation @github-automation
@mcp-builder @n8n-code-python @n8n-mcp-tools-expert
