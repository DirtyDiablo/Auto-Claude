# OpenClaw Virtual Computer Deployment Plan

## Goal

Stand up a virtual machine running OpenClaw with custom BD skills, then have OpenClaw autonomously build and operate the full PTS BD Intelligence System — the same system we've been building manually across 8 engines.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    VIRTUAL MACHINE                       │
│              (E2B Sandbox / Cloud VM)                    │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  OpenClaw    │  │  Qdrant      │  │  Neo4j        │  │
│  │  Gateway     │  │  :6333       │  │  :7687        │  │
│  │  :18789      │  └──────────────┘  └───────────────┘  │
│  └──────┬──────┘                                        │
│         │         ┌──────────────┐  ┌───────────────┐  │
│         │         │  Redis       │  │  Hub API      │  │
│         │         │  :6379       │  │  :8100        │  │
│         │         └──────────────┘  └───────────────┘  │
│         │                                               │
│  ┌──────┴──────────────────────────────────────────┐   │
│  │              OpenClaw Skills                      │   │
│  │  bd-knowledge-query  │  autonomous-loop          │   │
│  │  self-discover       │  swarm-dispatch           │   │
│  │  learn-feedback      │  meta-evolve              │   │
│  │  bd-pipeline-runner  │  bd-briefing-gen          │   │
│  │  bd-contact-enrich   │  bd-pattern-detect        │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              MCP Servers                           │   │
│  │  knowledge-mcp (:3001) │ github-mcp │ notion-mcp │   │
│  │  filesystem-mcp        │ slack-mcp  │ memory-mcp │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Autonomous OODA Loop                    │   │
│  │  Runs every 30 min — zero human prompting         │   │
│  │  OBSERVE → ORIENT → DECIDE → ACT → LEARN         │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
   ┌───────────┐            ┌──────────────┐
   │ Telegram / │            │  Your Local  │
   │ Discord /  │            │  Machine     │
   │ WhatsApp   │            │  (monitor)   │
   └───────────┘            └──────────────┘
```

---

## Phase 0: Choose Your Virtual Computer

### Option A: E2B Sandbox (Recommended for speed)

**Why:** Starts in <200ms, Firecracker microVM, built for AI agents, Python SDK, 24hr sessions, self-hosted option available.

**Cost:** ~$0.05/hr for a basic sandbox, or self-host on your own AWS/GCP/Azure.

**Limitations:** 24hr max session (need cron restart or self-hosted). Good for development and testing.

### Option B: Cloud VM (Recommended for production)

**Why:** Full control, persistent, runs 24/7, can handle all Docker services.

**Specs needed:**
- 4 vCPU, 16 GB RAM, 100 GB SSD (minimum)
- 8 vCPU, 32 GB RAM, 200 GB SSD (recommended — Qdrant + Neo4j + Ollama are memory-hungry)
- Ubuntu 22.04 LTS
- Providers: DigitalOcean ($48-96/mo), Hetzner ($20-40/mo), AWS EC2 t3.xlarge ($120/mo), GCP e2-standard-4 ($97/mo)

### Option C: Local WSL2 / Hyper-V (Free, for testing)

**Why:** You're already on Windows 11 Pro. Hyper-V is built in. Good for proving the concept before paying for cloud.

**Specs:** Your machine needs at least 32 GB RAM to comfortably run everything.

---

## Phase 1: VM Setup and Base Infrastructure

### Prompt 1: Provision the VM

```
You are setting up a production Ubuntu 22.04 VM for running an autonomous AI agent system.

Install the following base infrastructure:
1. Docker Engine + Docker Compose v2
2. Node.js 22 LTS (via nvm)
3. Python 3.12 (via deadsnakes PPA)
4. Git, curl, wget, jq, htop, tmux
5. uv (Python package manager)
6. pnpm (Node package manager)

Security baseline:
- Create a non-root user 'bdagent' with sudo access
- Set up UFW firewall: allow SSH (22), deny all else initially
- Generate SSH key pair for GitHub access
- Install fail2ban for SSH brute-force protection
- Set timezone to America/New_York (eastern US for federal work)

After installing, verify all versions and output a summary.
```

### Prompt 2: Deploy Docker Services

```
You are deploying the BD Intelligence System infrastructure on an Ubuntu 22.04 VM.

Clone the repository:
  git clone git@github.com:DirtyDiablo/Auto-Claude.git /home/bdagent/Auto-Claude
  cd /home/bdagent/Auto-Claude/BD-Automation-Engine

Start the Docker infrastructure using docker-compose.yml:
  - Qdrant (vector DB) on :6333/:6334
  - Neo4j (graph DB) on :7474/:7687
  - Redis (cache) on :6379

DO NOT start the hub_api or dashboard containers yet — we'll run those natively.

Create a .env file from .env.example with these keys (I'll provide values):
  - ANTHROPIC_API_KEY
  - OPENAI_API_KEY
  - NOTION_TOKEN
  - APIFY_API_TOKEN

Verify all three services are healthy:
  - curl http://localhost:6333/dashboard
  - curl http://localhost:7474
  - redis-cli ping

Open firewall ports: 6333, 7474, 7687, 6379, 8100, 18789 (for internal access only, not public)
```

### Prompt 3: Deploy the Hub API

```
You are deploying the BD-Automation-Engine Hub API (Engine 8 Knowledge System).

Working directory: /home/bdagent/Auto-Claude/BD-Automation-Engine

1. Create a Python virtual environment:
   python3.12 -m venv .venv
   source .venv/bin/activate
   uv pip install -r requirements.txt

2. Set environment variables in .env:
   QDRANT_URL=http://localhost:6333
   QDRANT_USE_SERVER=true

3. If the Qdrant collections are empty, run the indexer to populate them:
   python Engine8_Knowledge/scripts/indexer.py --all

4. Start the Hub API:
   python Engine8_Knowledge/api.py
   (Should be available on http://localhost:8100)

5. Verify the API is working:
   curl http://localhost:8100/health
   curl http://localhost:8100/api/v2/contacts?limit=3
   curl http://localhost:8100/api/v2/programs?limit=3
   curl http://localhost:8100/stats

The API should report 8,447+ indexed records across 5 collections.

Run the API under systemd or tmux so it persists after SSH disconnect.
```

---

## Phase 2: Install and Configure OpenClaw

### Prompt 4: Install OpenClaw

```
You are installing OpenClaw on an Ubuntu 22.04 VM where Node.js 22 and pnpm are already installed.

1. Install OpenClaw globally:
   pnpm add -g openclaw@latest

2. Run the onboarding wizard:
   openclaw onboard --install-daemon

   During onboarding, configure:
   - AI Provider: Anthropic (Claude)
   - Model: claude-sonnet-4-6 (for speed) or claude-opus-4-6 (for quality)
   - API Key: [ANTHROPIC_API_KEY from .env]
   - Gateway port: 18789 (default)
   - Workspace: /home/bdagent/Auto-Claude/BD-Automation-Engine
   - Channels: Skip messaging channels for now (we'll add Telegram later)

3. Verify OpenClaw is running:
   openclaw status
   openclaw health

4. Test basic interaction:
   openclaw chat "What is your name and what can you do?"

5. Check the skills directory structure:
   ls -la ~/.openclaw/skills/

OpenClaw should be running as a daemon on port 18789.
```

### Prompt 5: Configure MCP Servers in OpenClaw

```
You are configuring MCP server connections for OpenClaw on a VM where the BD-Automation-Engine Hub API is running on localhost:8100.

Edit the OpenClaw configuration (openclaw.json or via openclaw config):

Add MCP servers:
1. knowledge-mcp-server (our custom BD knowledge MCP):
   - Command: node
   - Args: ["/home/bdagent/Auto-Claude/BD-Automation-Engine/mcp/knowledge-mcp-server/dist/index.js"]
   - Env: { "BD_API_URL": "http://localhost:8100" }

2. filesystem MCP (for reading/writing local files):
   - Package: @anthropic/mcp-server-filesystem
   - Args: ["/home/bdagent/Auto-Claude/BD-Automation-Engine"]

3. GitHub MCP (for repo operations):
   - Package: @anthropic/mcp-server-github
   - Env: { "GITHUB_TOKEN": "[your token]" }

After adding each, verify with:
   openclaw mcp list
   openclaw mcp test knowledge-mcp-server

Test a knowledge query through OpenClaw:
   openclaw chat "Search for Tier 1 contacts at Leidos"

This should route through the knowledge MCP to our Hub API and return real results from Qdrant.
```

---

## Phase 3: Build the BD Skills for OpenClaw

### Prompt 6: Create the bd-knowledge-query Skill

```
You are building a custom OpenClaw skill called "bd-knowledge-query".

This skill is the HTTP bridge between OpenClaw and our BD-Automation-Engine Hub API running at http://localhost:8100.

Create the skill at: ~/.openclaw/skills/bd-knowledge-query/skill.mjs

The skill must:

1. SEARCH — Semantic search across 5 collections (contacts, programs, documents, activities, jobs)
   - Endpoint: POST http://localhost:8100/search
   - Body: { "query": "...", "collection": "...", "limit": 10 }
   - Returns: { "results": [...], "count": N }

2. ASK — RAG-powered Q&A with source citations
   - Endpoint: POST http://localhost:8100/ask/smart
   - Body: { "question": "..." }
   - Returns: { "answer": "...", "query_type": "...", "systems_used": [...] }

3. CONTACTS — Search and filter contacts
   - Endpoint: GET http://localhost:8100/api/v2/contacts?search=...&tier=...&company=...
   - Returns: { "contacts": [...], "total": N }

4. PROGRAMS — Search federal programs
   - Endpoint: GET http://localhost:8100/api/v2/programs?search=...
   - Returns: { "programs": [...], "total": N }

5. STATS — Get system health and collection counts
   - Endpoint: GET http://localhost:8100/stats
   - Returns: collection names, record counts, last updated timestamps

6. PATTERN DETECTION — Check for BD patterns
   - Endpoint: POST http://localhost:8100/api/v2/intelligence/patterns
   - Body: { "pattern_types": ["HIRING_SURGE", "LEADERSHIP_CHANGE", ...] }

Include a 15-minute SQLite cache for repeated queries. Include a circuit breaker that disables calls for 5 minutes after 3 consecutive failures.

Add a skill.md manifest with:
  name: bd-knowledge-query
  description: Bridge to PTS BD Intelligence System — search contacts, programs, documents. RAG-powered Q&A. Pattern detection.
  triggers: ["search knowledge", "find contacts", "program intel", "ask about", "BD intelligence"]

Test the skill:
  openclaw chat "Use bd-knowledge-query to find all Tier 1 contacts at Northrop Grumman"
  openclaw chat "Ask the knowledge base: what programs does Leidos prime on DCGS?"
```

### Prompt 7: Create the autonomous-loop Skill

```
You are building the master autonomous loop skill for OpenClaw. This is the OODA controller that makes the system self-operating.

Create: ~/.openclaw/skills/autonomous-loop/skill.mjs

State machine with 5 phases:

OBSERVE:
  - Call bd-knowledge-query STATS to check collection health
  - Read /home/bdagent/Auto-Claude/BD-Automation-Engine/pipeline_state.json for last run status
  - Check data freshness via GET http://localhost:8100/data/freshness
  - Query for new patterns via bd-knowledge-query PATTERN DETECTION
  - Record all observations in observations.json

ORIENT:
  - Analyze observations for actionable signals
  - Score each signal by urgency (0-100) and expected impact
  - Compare against previous cycle's observations (delta detection)
  - Identify: stale data, new patterns, quality gaps, relationship decay

DECIDE:
  - Build a prioritized task queue from orient signals
  - Each task has: type, priority, estimated_tokens, description
  - Apply budget gate: max 500K tokens/day, max 200 API calls/day
  - Write queue to task_queue.json
  - Skip tasks below priority threshold (configurable, default 30)

ACT:
  - Execute top N tasks from queue (batch size configurable, default 3)
  - For each task, invoke the appropriate skill (bd-knowledge-query, bd-pipeline-runner, etc.)
  - Record results with timestamps and quality scores
  - Write results to cycle_results.json

LEARN:
  - For each completed task, create an episodic memory entry
  - Store in Qdrant collection "episodic_memories" via Hub API
  - Update running statistics: tasks_completed, tokens_used, quality_scores
  - Write cycle summary to cycle_log.json (append)

Scheduling:
  - Run on a 30-minute cron: */30 * * * *
  - Each cycle should complete in < 10 minutes
  - If previous cycle is still running, skip

Budget tracking (persisted in budget.json):
  - daily_token_limit: 500000
  - daily_api_limit: 200
  - tokens_used_today: 0
  - api_calls_today: 0
  - Resets at midnight Eastern

Safety:
  - All Qdrant writes require explicit confirmation on first run, then auto-approve
  - No external communications (email, Slack) without human approval
  - No git push operations without human approval
  - Log everything to /home/bdagent/Auto-Claude/BD-Automation-Engine/outputs/ooda_logs/

Create skill.md manifest with:
  name: autonomous-loop
  description: Master OODA controller. Observes the BD intelligence system, detects opportunities, prioritizes tasks, executes them, and learns from results. Runs every 30 minutes.
  triggers: ["start autonomous", "run ooda", "start loop", "autonomous mode"]
```

### Prompt 8: Create the self-discover Skill

```
You are building the self-discover skill for OpenClaw. This skill finds new work for the autonomous loop.

Create: ~/.openclaw/skills/self-discover/skill.mjs

7 Discovery Mechanisms:

1. GAP DETECTION (daily)
   - Expected minimums: programs >= 388, contacts >= 965, documents >= 200
   - Compare against actual counts from bd-knowledge-query STATS
   - If below threshold, generate "data_gap" tasks

2. STALENESS DETECTION (daily)
   - GET http://localhost:8100/data/freshness
   - Any collection with freshness_score < 0.5 generates "re_enrich" tasks
   - Priority = (1 - freshness_score) * 100

3. PATTERN-DRIVEN DISCOVERY (after each observe)
   - HIRING_SURGE detected → generate "campaign_build" task
   - LEADERSHIP_CHANGE detected → generate "contact_enrichment" task
   - CONTRACT_MILESTONE detected → generate "competitive_analysis" task
   - BUDGET_SIGNAL detected → generate "program_analysis" task

4. RELATIONSHIP DECAY MONITORING (weekly, Mondays)
   - Query contacts with relationship_score < 20
   - For Tier 1-2 contacts below threshold, generate "outreach_draft" tasks

5. CROSS-REPO INTELLIGENCE (weekly, Wednesdays)
   - Scan git log for recent commits in BD-Automation-Engine
   - Detect TODO/FIXME/HACK comments
   - Generate "tech_debt" tasks for critical items

6. KNOWLEDGE GRAPH EXPANSION (continuous)
   - After each RAG query, extract entities and relationships
   - If entity is new (not in Neo4j), generate "entity_add" task
   - Track graph growth metrics

7. SELF-PERFORMANCE ANALYSIS (weekly, Fridays)
   - Read cycle_log.json for the past 7 days
   - Calculate: avg tasks/day, avg quality score, token efficiency
   - Compare to previous week
   - If declining, generate "self_optimize" task

Output: Write scored tasks to task_queue.json (append, don't overwrite)
Each task: { id, type, priority, source_mechanism, description, estimated_tokens, created_at }

Create skill.md manifest with:
  name: self-discover
  description: Finds new work for the autonomous loop. 7 discovery mechanisms detect gaps, staleness, patterns, decay, and self-performance issues.
  triggers: ["discover tasks", "find work", "gap detection", "what needs doing"]
```

### Prompt 9: Create the swarm-dispatch Skill

```
You are building the swarm-dispatch skill for OpenClaw. This skill breaks tasks into sub-tasks and executes them with specialized workers.

Create: ~/.openclaw/skills/swarm-dispatch/skill.mjs

TASK DECOMPOSITION:
Given a high-level task from the task queue, decompose it into a DAG of sub-tasks using these templates:

campaign_build:
  1. research_program (parallel) → 2. find_contacts (parallel) → 3. score_opportunities → 4. generate_playbook → 5. draft_outreach

contact_enrichment:
  1. search_existing → 2. identify_gaps → 3. enrich_from_sources → 4. classify_tier → 5. update_records

program_analysis:
  1. gather_program_data → 2. analyze_competitors → 3. score_opportunity → 4. generate_brief

weekly_briefing:
  1. collect_metrics (parallel) → 2. detect_patterns (parallel) → 3. rank_opportunities → 4. compile_brief → 5. format_output

competitive_analysis:
  1. identify_competitors → 2. research_each (parallel, map) → 3. compare_positions → 4. generate_report

WORKER TYPES (each maps to specific API calls):
  - researcher: GET /search, GET /api/v2/programs
  - contact_finder: GET /api/v2/contacts
  - scorer: POST /api/v2/intelligence/score
  - writer: POST /ask/smart (with specific writing prompts)
  - analyst: POST /api/v2/intelligence/patterns
  - enricher: POST /api/v2/contacts/enrich
  - exporter: POST /api/v2/export
  - validator: POST /api/v2/qa/validate

COORDINATION MODES:
  - PARALLEL: Run independent sub-tasks simultaneously
  - SEQUENTIAL: Run in order, pass output to next
  - PIPELINE: Stream output between stages
  - MAP_REDUCE: Fan out to N workers, collect and merge results

QUALITY GATE:
  - After each sub-task, score output quality (0-100)
  - If quality < 70, retry once with refined prompt
  - If still < 70, flag for human review and move on
  - Track quality scores per worker type for meta-learning

OUTPUT:
  - Write completed task results to outputs/tasks/{task_id}/
  - Include: result.json, quality_report.json, token_usage.json
  - Update task_queue.json with completion status

Create skill.md manifest with:
  name: swarm-dispatch
  description: Task decomposition and multi-worker execution engine. Breaks high-level BD tasks into DAGs and coordinates parallel execution.
  triggers: ["execute task", "run swarm", "dispatch workers", "build campaign"]
```

### Prompt 10: Create the learn-feedback Skill

```
You are building the learn-feedback skill for OpenClaw. This skill converts task outcomes into persistent memory.

Create: ~/.openclaw/skills/learn-feedback/skill.mjs

THREE MEMORY TIERS:

1. EPISODIC MEMORY (per-task)
   - After each task completes, create an episode:
     { id, task_type, timestamp, input_summary, output_summary, quality_score, tokens_used, duration_ms, success: bool }
   - Store in Qdrant collection "episodic_memories" via:
     POST http://localhost:8100/api/v2/memory/episodes
   - Embed the output_summary for semantic retrieval later

2. SEMANTIC FACTS (extracted from episodes)
   - Every 10 episodes, run a consolidation pass:
   - Use Claude to extract factual statements from recent episodes
   - Examples: "Leidos has 47 Tier 1 contacts in DCGS programs"
              "HIRING_SURGE patterns at Northrop correlate with contract renewals"
              "Weekly briefings score highest when generated on Fridays"
   - Store in Qdrant collection "semantic_facts" via:
     POST http://localhost:8100/api/v2/memory/facts
   - Deduplicate against existing facts (cosine similarity > 0.92 = duplicate)

3. PROCEDURAL INSIGHTS (meta-learning)
   - Every 50 episodes, run a reflection pass:
   - Analyze which strategies produce highest quality scores
   - Examples: "contact_enrichment tasks are 40% more effective when preceded by program_analysis"
              "Parallel worker coordination produces 2x throughput vs sequential for research tasks"
   - Store in Qdrant collection "procedural_insights" via:
     POST http://localhost:8100/api/v2/memory/insights

MEMORY RETRIEVAL:
   - Before starting any new task, query relevant memories:
     GET http://localhost:8100/api/v2/memory/recall?query={task_description}&limit=5
   - Inject retrieved memories into the task context
   - This makes each cycle smarter than the last

STATISTICS TRACKING:
   - Maintain running stats in memory_stats.json:
     { total_episodes, total_facts, total_insights, avg_quality_by_task_type, tokens_per_task_type, best_strategies }
   - Update after every cycle

Create skill.md manifest with:
  name: learn-feedback
  description: Converts task outcomes into 3-tier persistent memory (episodic/semantic/procedural). Makes every OODA cycle smarter than the last.
  triggers: ["learn from", "remember this", "what did we learn", "recall memories"]
```

### Prompt 11: Create the meta-evolve Skill

```
You are building the meta-evolve skill for OpenClaw. This is the self-improvement engine that runs weekly.

Create: ~/.openclaw/skills/meta-evolve/skill.mjs

WEEKLY SELF-IMPROVEMENT CYCLE (runs Sundays at midnight):

1. PERFORMANCE ANALYSIS
   - Read cycle_log.json for the past 7 days
   - Calculate per-skill metrics: avg_quality, avg_duration, token_efficiency, failure_rate
   - Compare to previous week and previous month
   - Identify: improving skills, degrading skills, unused skills

2. PROMPT OPTIMIZATION
   - For each skill with quality < 75%:
     - Retrieve the 5 lowest-quality task results
     - Analyze common failure patterns
     - Generate a revised system prompt or strategy
     - Write proposal to outputs/evolution/prompt_revisions/{skill_name}.md
   - DO NOT auto-apply prompt changes — queue for human review

3. SCHEDULE OPTIMIZATION
   - Analyze which times of day produce best results
   - Check if 30-min OODA cycle is too frequent or too slow
   - Propose schedule changes in outputs/evolution/schedule_proposals.md

4. NEW SKILL PROPOSALS
   - Analyze task types that frequently fail or produce low quality
   - Identify gaps where no existing skill handles the need well
   - Write skill proposals to outputs/evolution/new_skills/
   - Each proposal includes: name, purpose, trigger words, API endpoints needed, estimated complexity

5. BUDGET REBALANCING
   - Analyze token spend per task type
   - Identify high-cost/low-value tasks to deprioritize
   - Identify high-value/low-cost tasks to prioritize
   - Write budget proposal to outputs/evolution/budget_proposals.md

6. WEEKLY REPORT
   - Compile all analysis into a human-readable weekly report
   - Include: tasks completed, quality trends, token usage, top discoveries, improvement proposals
   - Write to outputs/weekly_reports/week_{date}.md
   - Send summary to Telegram/Discord if channel is configured

SAFETY GUARDRAILS:
   - NEVER auto-modify its own code or other skills' code
   - All proposals are written to files for human review
   - Score each proposal by expected impact (0-100) and effort (low/med/high)
   - Human approves → skill applies the change next cycle

Create skill.md manifest with:
  name: meta-evolve
  description: Weekly self-improvement engine. Analyzes performance, proposes prompt revisions, schedule optimizations, new skills, and budget rebalancing.
  triggers: ["self improve", "evolve", "weekly review", "optimize system"]
```

---

## Phase 4: Wire Everything Together

### Prompt 12: Build the BD Pipeline Runner Skill

```
You are building a bd-pipeline-runner skill that can trigger the full 8-engine pipeline or individual engines.

Create: ~/.openclaw/skills/bd-pipeline-runner/skill.mjs

CAPABILITIES:

1. FULL PIPELINE RUN
   - Execute: python /home/bdagent/Auto-Claude/BD-Automation-Engine/orchestrator.py --input latest
   - Monitor progress via pipeline_state.json
   - Capture output and quality metrics
   - Only allowed with budget approval (estimated ~50K tokens)

2. INDIVIDUAL ENGINE RUNS
   - Engine 2 (Program Mapping): python Engine2_ProgramMapping/scripts/pipeline.py --input {file}
   - Engine 3 (Contact Classification): python Engine3_OrgChart/scripts/contact_classifier.py
   - Engine 5 (BD Scoring): python Engine5_Scoring/scripts/bd_scoring.py --input {file}
   - Engine 8 (Reindex): python Engine8_Knowledge/scripts/indexer.py --collection {name}

3. PLAYBOOK GENERATION
   - For hot leads (BD Score >= 80), generate:
     - BD Playbook, Email Template, Call Script, Talking Points
   - python Engine4_Playbook/scripts/bd_playbook_generator.py --lead {lead_id}

4. DATA EXPORT
   - Notion CSV export: python Engine2_ProgramMapping/scripts/exporters.py --format notion
   - n8n JSON export: python Engine2_ProgramMapping/scripts/exporters.py --format n8n
   - Dashboard JSON export: GET http://localhost:8100/api/v2/export/dashboard

SAFETY:
   - Full pipeline runs require Tier 2 budget approval
   - Individual engines are Tier 1 (auto-approved within daily budget)
   - All outputs written to outputs/ directory
   - Log all runs to pipeline_runs.json

Create skill.md manifest with:
  name: bd-pipeline-runner
  description: Triggers the BD intelligence pipeline — full runs or individual engines. Generates playbooks, exports data, reindexes knowledge base.
  triggers: ["run pipeline", "run engine", "generate playbook", "export data", "reindex"]
```

### Prompt 13: Create the Startup Script and Systemd Services

```
You are creating the startup and service management configuration for the autonomous BD system.

Create the following:

1. /home/bdagent/start-bd-system.sh — Master startup script
   #!/bin/bash
   # Start Docker services (Qdrant, Neo4j, Redis)
   docker compose -f /home/bdagent/Auto-Claude/BD-Automation-Engine/docker-compose.yml up -d qdrant neo4j redis
   # Wait for services to be healthy
   # Start Hub API
   # Start OpenClaw daemon
   # Verify all connections
   # Output status summary

2. /etc/systemd/system/bd-hub-api.service — Hub API as systemd service
   - ExecStart: /home/bdagent/Auto-Claude/BD-Automation-Engine/.venv/bin/python Engine8_Knowledge/api.py
   - WorkingDirectory: /home/bdagent/Auto-Claude/BD-Automation-Engine
   - Restart: always
   - EnvironmentFile: /home/bdagent/Auto-Claude/BD-Automation-Engine/.env

3. /etc/systemd/system/openclaw.service — OpenClaw daemon as systemd service
   - ExecStart: /usr/local/bin/openclaw daemon
   - Restart: always

4. Cron jobs for the autonomous loop:
   */30 * * * * openclaw run autonomous-loop
   0 6 * * * openclaw run self-discover --mechanism gap_detection
   0 6 * * * openclaw run self-discover --mechanism staleness_detection
   0 0 * * 0 openclaw run meta-evolve
   0 16 * * 5 openclaw run swarm-dispatch --task weekly_briefing

5. /home/bdagent/health-check.sh — Health monitoring script
   - Check all services are running
   - Check Qdrant has data
   - Check API responds
   - Check OpenClaw daemon is active
   - Check last OODA cycle completed successfully
   - Output: healthy/degraded/critical

Enable and start all services. Verify the full system comes up cleanly after a reboot.
```

---

## Phase 5: Connect Messaging Channel

### Prompt 14: Connect Telegram for Human-in-the-Loop

```
You are connecting a Telegram bot to OpenClaw for human-in-the-loop monitoring and control.

1. Create a Telegram bot via @BotFather:
   - Name: PTS BD Intelligence Bot
   - Username: pts_bd_intel_bot

2. Configure in OpenClaw:
   openclaw channel add telegram --token {BOT_TOKEN} --chat-id {YOUR_CHAT_ID}

3. Set up notification routing:
   - CRITICAL alerts (pattern detected, pipeline failure): Immediate Telegram message
   - DAILY digest: Summary of OODA cycles, tasks completed, quality scores at 6 PM Eastern
   - WEEKLY report: Full meta-evolve output on Sunday evening
   - APPROVAL requests: Tier 3 actions that need human OK

4. Command interface via Telegram:
   /status — Current system health and stats
   /tasks — View task queue and priorities
   /run {skill} — Manually trigger a skill
   /approve {task_id} — Approve a Tier 3 action
   /deny {task_id} — Deny a Tier 3 action
   /budget — View daily budget usage
   /pause — Pause autonomous loop
   /resume — Resume autonomous loop
   /report — Generate on-demand intelligence report

5. Test the full loop:
   - Send "/status" → should return system health
   - Wait for next OODA cycle → should get a digest
   - Trigger a pattern manually → should get an alert
```

---

## Phase 6: Validation and Go-Live

### Prompt 15: Full System Validation

```
You are validating the complete autonomous BD Intelligence System before go-live.

Run these verification tests:

1. CONNECTIVITY TEST
   - OpenClaw → Hub API (http://localhost:8100/health)
   - OpenClaw → Qdrant (http://localhost:6333/collections)
   - OpenClaw → Neo4j (bolt://localhost:7687)
   - OpenClaw → Redis (redis://localhost:6379)
   - All MCP servers responding

2. SKILL INTEGRATION TEST
   - bd-knowledge-query: Search for "DCGS analyst" → expect results
   - bd-knowledge-query: Ask "What programs does Leidos prime?" → expect RAG answer
   - bd-pipeline-runner: Run Engine 5 scoring on test data → expect scores
   - self-discover: Run gap detection → expect task queue entries
   - swarm-dispatch: Execute a contact_enrichment task → expect completed sub-tasks

3. AUTONOMOUS LOOP TEST
   - Trigger one full OODA cycle manually: openclaw run autonomous-loop
   - Verify: observations.json created
   - Verify: task_queue.json has entries
   - Verify: At least one task executed
   - Verify: cycle_results.json written
   - Verify: episodic memory created in Qdrant

4. PERSISTENCE TEST
   - Reboot the VM
   - Verify all services auto-start
   - Verify Hub API has data
   - Verify OpenClaw reconnects
   - Verify next scheduled OODA cycle runs

5. BUDGET GATE TEST
   - Set daily_token_limit to 1000 (artificially low)
   - Run autonomous-loop
   - Verify it respects the limit and stops
   - Reset to 500000

6. QUALITY GATE TEST
   - Feed a deliberately bad task into the queue
   - Verify quality score < 70
   - Verify it gets flagged for review
   - Verify it does NOT auto-retry more than once

7. TELEGRAM TEST
   - /status returns healthy
   - /tasks shows queue
   - OODA cycle sends digest
   - Approval flow works end-to-end

OUTPUT: Write full test results to outputs/validation/go_live_report.md
Grade each test: PASS / FAIL / DEGRADED
System is go-live ready when all tests are PASS or DEGRADED with known workarounds.
```

---

## Estimated Timeline

| Phase | What | Effort |
|-------|------|--------|
| Phase 0 | Choose VM, provision | 1-2 hours |
| Phase 1 | Base infra + Docker + API | 2-3 hours |
| Phase 2 | Install/configure OpenClaw | 1-2 hours |
| Phase 3 | Build 6 custom skills | 1-2 days (largest effort) |
| Phase 4 | Wire together, systemd, cron | 2-3 hours |
| Phase 5 | Telegram integration | 1-2 hours |
| Phase 6 | Validation and go-live | 2-3 hours |

**Total: ~2-3 days of focused work to go from zero to autonomous.**

---

## Budget Estimates

### Cloud VM (monthly)
| Provider | Spec | Cost |
|----------|------|------|
| Hetzner CX41 | 8 vCPU, 32 GB, 240 GB | ~$30/mo |
| DigitalOcean | 8 vCPU, 32 GB, 320 GB | ~$96/mo |
| AWS t3.2xlarge | 8 vCPU, 32 GB, 200 GB EBS | ~$200/mo |

### API Costs (daily at 500K token budget)
| Provider | Rate | Daily | Monthly |
|----------|------|-------|---------|
| Anthropic Sonnet | ~$3/M input, $15/M output | ~$5-8 | ~$150-240 |
| Anthropic Opus | ~$15/M input, $75/M output | ~$25-40 | ~$750-1200 |
| Mixed (Sonnet for routine, Opus for analysis) | — | ~$10-15 | ~$300-450 |

**Recommendation:** Start with Sonnet for all skills. Upgrade specific skills to Opus only if quality scores are consistently below 75%.

---

## What This Achieves

When fully operational, the system will autonomously:

1. **Scrape** federal job boards daily and ingest new opportunities
2. **Map** every job to one of 388 federal programs with confidence scores
3. **Score** every opportunity on 6 dimensions (0-100 composite)
4. **Generate** playbooks, call scripts, and email templates for hot leads (score >= 80)
5. **Detect** 7 strategic patterns (hiring surges, leadership changes, budget signals, etc.)
6. **Monitor** 7,337+ contacts for relationship decay and auto-draft outreach
7. **Compile** weekly intelligence briefs every Friday at 4 PM
8. **Learn** from every action, building persistent memory that makes each cycle smarter
9. **Self-improve** weekly by analyzing what works and proposing optimizations
10. **Alert** you via Telegram when high-urgency patterns are detected
11. **Request approval** for sensitive actions (real outreach, git pushes, production writes)

All with zero daily human prompting required.
