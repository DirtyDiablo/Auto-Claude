# Agent & Skill Best Practices — Master Reference

> **Purpose:** Standardize how every agent, subagent, skill, workflow, and crew is invoked, what artifacts it must produce, and how to chain them consistently.
>
> **Scope:** 45+ Task-tool subagent types, 8 BD agents, 5 CrewAI agents, 3 crews, 4 LangGraph workflows, 21 MCP tools, 850+ Antigravity skills.

---

## Table of Contents

1. [Universal Post-Completion Framework](#1-universal-post-completion-framework)
2. [Task-Tool Subagent Types (45 types)](#2-task-tool-subagent-types)
3. [BD-Engine Agents](#3-bd-engine-agents)
4. [Workflows & Orchestration](#4-workflows--orchestration)
5. [Key Skills by Category](#5-key-skills-by-category)
6. [Chaining Patterns & Standard Workflows](#6-chaining-patterns--standard-workflows)
7. [Audit Log Format](#7-audit-log-format)

---

## 1. Universal Post-Completion Framework

**Every agent, skill, subagent, or workflow execution MUST produce these artifacts when completing work:**

### 1.1 Memory Updates

Append findings to the project's auto-memory (`MEMORY.md`). Include:

- New patterns or conventions discovered
- Key architectural decisions made
- Important file paths added or changed
- Solutions to problems encountered

**Rule:** Only write stable, verified information. Do not log session-specific or speculative content.

### 1.2 Audit Trail

Append an entry to `docs/AGENT_AUDIT_LOG.md` using the standard format (see [Section 7](#7-audit-log-format)). Every execution — success or failure — gets logged.

### 1.3 Architecture Doc Refresh

If structural changes occurred (new files, renamed modules, changed API endpoints, new collections), update the relevant architecture doc:

| Change Type | Doc to Update |
|-------------|---------------|
| New API endpoints | `docs/KNOWLEDGE_SYSTEM_GUIDE.md` |
| New agents or workflows | This document (`AGENT_BEST_PRACTICES.md`) |
| Pipeline changes | `orchestrator.py` docstring + `CLAUDE.md` status section |
| Infrastructure changes | `docs/UNIFIED_INFRASTRUCTURE_GUIDE.md` |
| Data schema changes | `docs/MASTER_PROPERTY_SCHEMA.md` |
| New engine or subsystem | `CLAUDE.md` project structure section |

### 1.4 File Manifest

Every execution output must include a manifest listing:

```
Files created:  [list]
Files modified: [list]
Files deleted:  [list]
```

### 1.5 Standard Post-Completion Output Block

Use this template at the end of every agent run:

```
## Post-Completion Summary
- **Agent:** [name/type]
- **Status:** [success | partial | failed]
- **Duration:** [if known]
- **Files created:** [list]
- **Files modified:** [list]
- **Memory updated:** [yes/no — summary]
- **Audit logged:** [yes/no]
- **Docs refreshed:** [list or none]
- **Data stores changed:** [Qdrant/Neo4j/Redis details or none]
- **Follow-up needed:** [description or none]
```

---

## 2. Task-Tool Subagent Types

These are the 45+ subagent types available via the `Task` tool. Each entry includes: purpose, when to use, invocation pattern, and expected outputs.

### 2.1 Research & Exploration

#### `Explore`
- **Purpose:** Fast codebase exploration — find files, search code, answer structural questions.
- **When:** Quick file searches, pattern matching across the codebase, understanding how something works.
- **Invocation:** Specify thoroughness: `"quick"` (basic), `"medium"` (moderate), `"very thorough"` (comprehensive).
- **Outputs:** File paths, code snippets, structural summaries.
- **Post-completion:** No file changes expected. Log findings if they reveal new patterns.

```
Task(subagent_type="Explore", prompt="Find all files that define API endpoints in Engine8_Knowledge/")
```

#### `general-purpose`
- **Purpose:** Multi-step research, code search, and complex question answering.
- **When:** Tasks requiring multiple rounds of searching, reading, and web fetching that don't fit other categories.
- **Outputs:** Research summaries, code analysis, multi-step findings.
- **Post-completion:** Log significant discoveries to memory.

#### `voltagent-research:data-researcher`
- **Purpose:** Discover, collect, and validate data from multiple sources.
- **When:** Identifying data sources, gathering datasets, performing quality checks.
- **Outputs:** Data source inventories, quality assessments, prepared datasets.

#### `voltagent-research:market-researcher`
- **Purpose:** Analyze markets, consumer behavior, competitive landscapes, size opportunities.
- **When:** Market analysis, business strategy research, market entry decisions.
- **Outputs:** Market size estimates, competitive positioning, strategic recommendations.

#### `voltagent-research:research-analyst`
- **Purpose:** Comprehensive multi-source research with synthesis into actionable insights.
- **When:** Deep research requiring trend identification and detailed reporting.
- **Outputs:** Synthesized reports, trend analysis, actionable recommendations.

#### `voltagent-research:search-specialist`
- **Purpose:** Find specific information using advanced search strategies.
- **When:** Precision information retrieval where speed matters more than analysis.
- **Outputs:** Targeted search results, source lists.

#### `voltagent-research:trend-analyst`
- **Purpose:** Analyze emerging patterns, predict industry shifts, develop future scenarios.
- **When:** Strategic planning, competitive positioning, industry forecasting.
- **Outputs:** Trend reports, future scenarios, strategic recommendations.

#### `voltagent-research:competitive-analyst`
- **Purpose:** Analyze competitors, benchmark against market leaders.
- **When:** Competitive intelligence, positioning strategy, market advantage analysis.
- **Outputs:** Competitor profiles, benchmarks, strategic recommendations.

---

### 2.2 Code Quality & Review

#### `feature-dev:code-architect`
- **Purpose:** Design feature architectures by analyzing existing patterns and conventions.
- **When:** Before implementing a new feature — get a blueprint first.
- **Outputs:** Implementation blueprints with specific files to create/modify, component designs, data flows, build sequences.
- **Post-completion:** Architecture decisions should be logged to memory.

#### `feature-dev:code-explorer`
- **Purpose:** Deep analysis of existing features — trace execution paths, map layers, understand patterns.
- **When:** Before modifying existing code — understand what's there first.
- **Outputs:** Execution path maps, architecture layer diagrams, dependency documentation.

#### `feature-dev:code-reviewer`
- **Purpose:** Review code for bugs, logic errors, security vulnerabilities, quality issues.
- **When:** After writing or modifying code. Uses confidence-based filtering — only reports high-priority issues.
- **Outputs:** Prioritized issue list with confidence scores and fix suggestions.
- **Post-completion:** Log any recurring patterns found.

#### `code-simplifier:code-simplifier`
- **Purpose:** Simplify and refine code for clarity, consistency, and maintainability.
- **When:** After completing a coding task or writing a logical chunk of code. **Should be triggered proactively.**
- **Outputs:** Simplified code preserving all functionality.

#### `pr-review-toolkit:code-reviewer`
- **Purpose:** Comprehensive code review for PRs.
- **When:** Before merging code — full review pass.
- **Outputs:** Review comments, issue classifications, fix suggestions.

#### `pr-review-toolkit:code-simplifier`
- **Purpose:** Simplify modified code in PR context.
- **When:** After code is written/modified and needs refinement. **Should be triggered proactively.**
- **Outputs:** Simplified code following project best practices.

#### `pr-review-toolkit:comment-analyzer`
- **Purpose:** Analyze PR review comments for patterns and themes.
- **When:** After receiving PR feedback — identify common issues.
- **Outputs:** Comment categorization, recurring issue patterns.

#### `pr-review-toolkit:pr-test-analyzer`
- **Purpose:** Analyze test coverage and quality in PRs.
- **When:** After tests are written — verify coverage completeness.
- **Outputs:** Coverage analysis, missing test cases, quality assessment.

#### `pr-review-toolkit:silent-failure-hunter`
- **Purpose:** Find code that fails silently (swallowed exceptions, missing error handling).
- **When:** During security/quality reviews — find hidden failure modes.
- **Outputs:** Silent failure inventory with severity ratings.

#### `pr-review-toolkit:type-design-analyzer`
- **Purpose:** Analyze type system design for correctness and consistency.
- **When:** After modifying TypeScript types or Python dataclasses.
- **Outputs:** Type design issues, inconsistencies, improvement suggestions.

#### `coderabbit:code-reviewer`
- **Purpose:** Specialized CodeRabbit-style thorough code review.
- **When:** Major code changes requiring deep analysis.
- **Outputs:** Detailed review with categorized findings.

---

### 2.3 Security & QA

#### `voltagent-qa-sec:code-reviewer`
- **Purpose:** Code review focusing on security vulnerabilities and best practices.
- **When:** Security-sensitive code changes (auth, crypto, input handling, API endpoints).
- **Outputs:** Security findings with severity, fix recommendations.

#### `voltagent-qa-sec:security-auditor`
- **Purpose:** Comprehensive security audits, compliance assessments, risk evaluations.
- **When:** Periodic security reviews, pre-deployment audits, compliance checks.
- **Outputs:** Audit findings, compliance gaps, risk ratings.
- **Post-completion:** Update `docs/BD_ENGINE_AUDIT_REPORT.md` with findings.

#### `voltagent-qa-sec:penetration-tester`
- **Purpose:** Authorized security penetration testing.
- **When:** Active security testing, vulnerability exploitation validation. **Requires clear authorization context.**
- **Outputs:** Vulnerability findings, exploitation evidence, remediation steps.

#### `voltagent-qa-sec:compliance-auditor`
- **Purpose:** Regulatory compliance (GDPR, HIPAA, PCI DSS, SOC 2, ISO, NIST 800-53).
- **When:** Compliance gap analysis, audit preparation, control validation.
- **Outputs:** Compliance matrix, gap analysis, remediation roadmap.

#### `voltagent-qa-sec:qa-expert`
- **Purpose:** Quality assurance strategy, test planning, quality metrics.
- **When:** Planning test strategy, improving overall quality, analyzing quality metrics.
- **Outputs:** QA strategy, test plans, quality metric reports.

#### `voltagent-qa-sec:test-automator`
- **Purpose:** Build automated test frameworks, create test scripts, CI/CD test integration.
- **When:** Setting up testing infrastructure, writing test suites, adding tests to CI.
- **Outputs:** Test frameworks, test scripts, CI configuration.
- **Post-completion:** Update test coverage metrics.

#### `voltagent-qa-sec:debugger`
- **Purpose:** Diagnose and fix bugs, analyze error logs and stack traces.
- **When:** Bug investigation, root cause analysis, error diagnosis.
- **Outputs:** Root cause analysis, fix implementation, prevention recommendations.

#### `voltagent-qa-sec:error-detective`
- **Purpose:** Diagnose error patterns, correlate errors across services.
- **When:** Multi-service error investigation, error pattern analysis.
- **Outputs:** Error correlation maps, root causes, prevention strategies.

#### `voltagent-qa-sec:performance-engineer`
- **Purpose:** Identify and eliminate performance bottlenecks.
- **When:** Slow queries, high latency, resource exhaustion, optimization needs.
- **Outputs:** Bottleneck analysis, optimization recommendations, before/after metrics.

#### `voltagent-qa-sec:chaos-engineer`
- **Purpose:** Design failure experiments, validate resilience, test incident response.
- **When:** Pre-production resilience testing, game day exercises.
- **Outputs:** Experiment designs, resilience reports, incident response assessments.

#### `voltagent-qa-sec:architect-reviewer`
- **Purpose:** Evaluate system design decisions, architectural patterns, technology choices.
- **When:** Architecture reviews, major design decisions, technology evaluations.
- **Outputs:** Architecture assessment, trade-off analysis, recommendations.

#### `voltagent-qa-sec:accessibility-tester`
- **Purpose:** WCAG compliance, assistive technology support testing.
- **When:** Frontend accessibility audits, compliance verification.
- **Outputs:** WCAG compliance report, accessibility issues, remediation steps.

#### `voltagent-qa-sec:ad-security-reviewer`
- **Purpose:** Active Directory security posture, privilege escalation risk, auth protocol hardening.
- **When:** AD security audits, identity delegation review.
- **Outputs:** AD security assessment, privilege escalation risks, hardening recommendations.

#### `voltagent-qa-sec:powershell-security-hardening`
- **Purpose:** Harden PowerShell automation, secure remoting, enforce least-privilege.
- **When:** PowerShell security reviews, script hardening.
- **Outputs:** Hardening recommendations, script fixes, compliance alignment.

#### `posthog:error-analyzer`
- **Purpose:** Analyze PostHog errors to identify patterns and prioritize fixes.
- **When:** Error triage, pattern identification, impact-based prioritization.
- **Outputs:** Error patterns, root causes, priority rankings by user impact.

---

### 2.4 Planning & Architecture

#### `Plan`
- **Purpose:** Design implementation plans — step-by-step strategies, critical files, trade-offs.
- **When:** Before implementing non-trivial features. Returns plans for user approval.
- **Outputs:** Implementation plans, file lists, architectural trade-off analysis.
- **Note:** Read-only — does not modify code.

#### `feature-dev:code-architect`
- **Purpose:** (Also listed in Code Quality.) Design feature architectures from existing patterns.
- **When:** New feature planning that needs a concrete blueprint.
- **Outputs:** Implementation blueprints, component designs, build sequences.

#### `voltagent-qa-sec:architect-reviewer`
- **Purpose:** (Also listed in Security.) Evaluate design decisions at the macro level.
- **When:** Reviewing proposed architectures before implementation.
- **Outputs:** Architecture assessment with trade-off analysis.

---

### 2.5 Development & SDK

#### `Bash`
- **Purpose:** Command execution — git operations, builds, tests, terminal tasks.
- **When:** Running commands, installing dependencies, executing scripts.
- **Outputs:** Command output, exit codes.

#### `agent-sdk-dev:agent-sdk-verifier-py`
- **Purpose:** Verify Python Agent SDK applications are properly configured.
- **When:** After creating or modifying a Python Agent SDK app.
- **Outputs:** Configuration validation, best practice compliance, deployment readiness.

#### `agent-sdk-dev:agent-sdk-verifier-ts`
- **Purpose:** Verify TypeScript Agent SDK applications are properly configured.
- **When:** After creating or modifying a TypeScript Agent SDK app.
- **Outputs:** Configuration validation, best practice compliance, deployment readiness.

#### `plugin-dev:agent-creator`
- **Purpose:** Create autonomous agents for plugins.
- **When:** User asks to create, generate, or build a new agent.
- **Outputs:** Agent configuration files.

#### `plugin-dev:plugin-validator`
- **Purpose:** Validate plugin structure, manifest, and files.
- **When:** After creating or modifying plugin components. **Trigger proactively.**
- **Outputs:** Validation results, structural issues, fix suggestions.

#### `plugin-dev:skill-reviewer`
- **Purpose:** Review skill quality, description effectiveness, best practice adherence.
- **When:** After creating or modifying a skill. **Trigger proactively.**
- **Outputs:** Quality assessment, improvement suggestions.

---

### 2.6 Specialized

#### `claude-code-guide`
- **Purpose:** Answer questions about Claude Code CLI, Agent SDK, and Claude API.
- **When:** User asks "Can Claude...", "How do I...", about features, hooks, MCP servers, settings.
- **Outputs:** Feature explanations, usage instructions, code examples.

#### `statusline-setup`
- **Purpose:** Configure Claude Code status line settings.
- **When:** User wants to change status line display.
- **Outputs:** Updated status line configuration.

#### `hookify:conversation-analyzer`
- **Purpose:** Analyze conversation patterns for hook creation opportunities.
- **When:** Identifying automation opportunities from conversation history.
- **Outputs:** Hook suggestions, conversation pattern analysis.

#### `huggingface-skills:AGENTS`
- **Purpose:** HuggingFace-related agent capabilities.
- **When:** Working with HuggingFace models, datasets, or spaces.
- **Outputs:** Model recommendations, usage patterns, integration code.

---

## 3. BD-Engine Agents

### 3.1 Core BD Agents (Claude-backed, inherit from `BDAgent`)

All core agents live in `Engine8_Knowledge/agents/` and inherit from `BDAgent` (defined in `base_agent.py`). They share: MemLayer memory, LightRAG knowledge graph, hybrid BM25+semantic retriever, and Anthropic Claude API client.

#### `ProgramIntelAgent`
- **File:** `Engine8_Knowledge/agents/program_intel_agent.py`
- **Purpose:** Analyze federal programs and contract opportunities.
- **API Endpoint:** `POST /agents/program-intel` (via `agents/api_routes.py`)
- **MCP Tool:** `get_program_intel`
- **Inputs:** Program name, optional agency/contract details.
- **Outputs:** Program overview, contract structure, opportunity assessment, incumbent analysis, recommended actions.
- **Key Methods:** `analyze_program()`, `find_recompetes()`, `get_program_value()`, `find_incumbents()`
- **Data Stores Updated:** Qdrant `programs` collection (interaction stored), MemLayer memory.
- **Chaining:** Often first in chain → feeds `ContactFinderAgent` and `BDStrategyAgent`.

#### `CompanyResearchAgent`
- **File:** `Engine8_Knowledge/agents/company_research_agent.py`
- **Purpose:** Research competitors and teaming partners.
- **API Endpoint:** `POST /agents/company-research`
- **MCP Tool:** `find_relationships` (partial), `get_company_contacts`
- **Inputs:** Company name, optional focus area.
- **Outputs:** Company profile, contract portfolio, competitive position, teaming history, BD implications.
- **Key Methods:** `analyze_competitor()`, `find_teaming_partners()`, `get_contract_history()`, `compare_companies()`
- **Data Stores Updated:** Neo4j network graph queries, MemLayer memory.

#### `ContactFinderAgent`
- **File:** `Engine8_Knowledge/agents/contact_finder_agent.py`
- **Purpose:** Identify key personnel and decision makers.
- **API Endpoint:** `POST /agents/contact-finder`
- **MCP Tool:** `get_company_contacts`
- **Inputs:** Company, program, or role criteria.
- **Outputs:** Contact list with roles, titles, program affiliations, clearance levels, outreach recommendations.
- **Key Methods:** `find_decision_makers()`, `find_by_clearance()`, `find_at_company()`, `find_tier1_contacts()`
- **Data Stores Updated:** Qdrant `contacts` collection queries, MemLayer memory.

#### `BDStrategyAgent`
- **File:** `Engine8_Knowledge/agents/bd_strategy_agent.py`
- **Purpose:** Synthesize intelligence into BD capture strategies.
- **API Endpoint:** `POST /agents/bd-strategy`
- **Inputs:** Opportunity details, competitive landscape, contact intelligence.
- **Outputs:** Opportunity assessment, win themes, teaming strategy, competitive differentiation, 90-day action plan, risk mitigation.
- **Key Methods:** `create_capture_plan()`, `assess_win_probability()`, `develop_teaming_strategy()`, `competitive_analysis()`
- **Data Stores Updated:** LightRAG graph (hybrid mode), MemLayer memory.
- **Chaining:** Usually last in BD research chain — consumes outputs from program_intel, company_research, contact_finder.

### 3.2 Phase 4 Specialized Agents (Rule-based, no LLM dependency)

#### `ContactClassifierAgent`
- **File:** `Engine8_Knowledge/agents/contact_classifier_agent.py`
- **Purpose:** Classify contacts across 4 dimensions using regex pattern matching.
- **API Endpoint:** Used internally by workflows and `BDCrewOrchestrator`.
- **Inputs:** Contact records (name, title, company, location).
- **Outputs per contact:**
  - Hierarchy Tier (1-6): VP+ → Director → Manager → Lead/Senior → Staff → Entry
  - DCGS Program: AF DCGS-Langley, AF DCGS-Wright-Patt, AF DCGS-PACAF, Army DCGS-A, Navy DCGS-N, Corporate HQ, Enterprise Security
  - BD Priority: Critical / High / Medium / Standard
  - Location Hub: Hampton Roads, San Diego, DC Metro, Dayton/Wright-Patt, OCONUS
- **Key Methods:** `classify_tier()`, `classify_program()`, `classify_location_hub()`, `calculate_bd_priority()`, `classify_batch()`
- **Data Stores Updated:** Classification results stored in Qdrant contacts metadata.

#### `AnalyticsAgent`
- **File:** `Engine8_Knowledge/agents/analytics_agent.py`
- **Purpose:** Generate insights, trends, and forecasts from BD data.
- **Inputs:** Job postings, programs, contacts, time period.
- **Outputs:** `AnalyticsReport` with hiring trends (top companies, TS/SCI demand, hot locations), program activity (volume by program, recompete indicators), contact tier distribution.
- **Key Methods:** `analyze_hiring_trends()`, `analyze_program_activity()`, `analyze_contacts_by_tier()`, `generate_report()`

#### `QualityAssuranceAgent`
- **File:** `Engine8_Knowledge/agents/quality_assurance_agent.py`
- **Purpose:** Validate data quality across Qdrant collections.
- **Inputs:** Collection name, records to validate.
- **Outputs:** `QualityReport` with completeness score, freshness score, accuracy score (all 0-1), duplicate count, issue list.
- **Freshness thresholds:** contacts=180d, programs=365d, jobs=30d, activities=90d.
- **Key Methods:** `check_completeness()`, `check_duplicates()`, `check_freshness()`, `check_confidence()`, `assess_quality()`

#### `ScraperMonitorAgent`
- **File:** `Engine8_Knowledge/agents/scraper_monitor_agent.py`
- **Purpose:** Monitor job scraper results and identify BD opportunities.
- **Inputs:** Batch of scraped job postings, scraper name.
- **Outputs:** `ScrapeAnalysis` with high-value jobs (TS/SCI + DCGS keywords + BD score >= 80), competitor alerts, severity ratings.
- **Monitored competitors:** Leidos, Northrop Grumman, Booz Allen, Peraton, CACI, SAIC, ManTech, Raytheon, L3Harris, Parsons.
- **Key Methods:** `detect_competitors()`, `is_high_value()`, `analyze_scrape_batch()`, `get_recent_alerts()`

### 3.3 CrewAI Agents (GPT-4o backed, Qdrant tools)

Defined in `Engine8_Knowledge/agents/bd_agents.py`. These are CrewAI `Agent` instances with Qdrant search tools:

| Agent | Role | LLM | Tools |
|-------|------|-----|-------|
| `program_researcher` | Federal Program Intelligence Analyst | GPT-4o | qdrant_programs, qdrant_contracts, qdrant_documents, graphiti_search |
| `contact_enricher` | BD Contact Intelligence Specialist | GPT-4o-mini | qdrant_contacts, qdrant_notes, mem0_search, graphiti_search |
| `competitive_analyst` | Competitive Intelligence Analyst | GPT-4o | qdrant_jobs, qdrant_documents, qdrant_programs |
| `outreach_composer` | BD Outreach Strategist | GPT-4o | qdrant_contacts, qdrant_programs, qdrant_jobs, mem0_search |
| `humint_analyst` | HUMINT Intelligence Analyst | GPT-4o | qdrant_notes, qdrant_contacts, mem0_search, graphiti_search |

### 3.4 Autonomous Agents (Standalone, HTTP-polling)

#### `MorningBriefingAgent`
- **File:** `Engine8_Knowledge/agents/autonomous/morning_briefing.py`
- **Purpose:** Generate daily BD intelligence reports.
- **Trigger:** Scheduled (6:00 AM) or on-demand.
- **Data Sources:** 6 internal API endpoints.
- **Outputs:** `DailyBrief` dataclass → Slack Block Kit or Markdown.
- **Artifacts:** Saved to `data/briefings/YYYY-MM-DD.json`, sent to `#bd-daily` Slack channel.

#### `ContactEnrichmentAgent`
- **File:** `Engine8_Knowledge/agents/autonomous/contact_enrichment.py`
- **Purpose:** Scan contacts for staleness and change indicators.
- **Triggers:** Stale contacts (90+ days no update), missing required fields (email, phone, title, company, linkedin), low confidence scores, departed keywords in title.
- **Outputs:** `EnrichmentReport` → JSONL log at `data/enrichment/enrichment_log.jsonl`.

### 3.5 Orchestrator (`BDCrewOrchestrator`)

**File:** `Engine8_Knowledge/agents/crewai_orchestrator.py`

Central orchestrator that routes to all 8 agent types. Provides CrewAI mode and fallback (sequential) mode.

| Workflow Method | Agents Used | Purpose |
|-----------------|-------------|---------|
| `capture_strategy_workflow(opportunity)` | program_intel → company_research → contact_finder → bd_strategy | Full BD capture strategy |
| `competitor_analysis_workflow(company)` | company_research + contact_finder | Competitor deep-dive |
| `teaming_partner_workflow(capability_gaps)` | company_research | Find teaming partners |
| `quick_intel_workflow(query)` | Routes to best single agent by keyword | Fast single-agent query |
| `classify_contacts_workflow(contacts)` | contact_classifier | Batch classification |
| `analyze_scrape_workflow(jobs, scraper)` | scraper_monitor | Scraper result analysis |
| `quality_check_workflow(records, type)` | quality_assurance | Data QA validation |
| `generate_analytics_workflow(...)` | analytics | Generate analytics report |
| `full_intelligence_workflow(query, jobs, contacts)` | All 8 agents in sequence | Complete intelligence sweep |

---

## 4. Workflows & Orchestration

### 4.1 LangGraph Production Workflows

All production workflows live in `Engine8_Knowledge/workflows/production/` and use the `WorkflowDefinition`/`NodeSpec`/`EdgeSpec` framework from `workflows/graph_builder.py`.

#### Morning Briefing Workflow
- **File:** `workflows/production/morning_briefing.py`
- **Schedule:** 6:00 AM daily (autonomous, no human interrupt).
- **Nodes (11):** 5-way parallel data gather → merge → prioritize → format → quality check (>= 0.6 threshold) → deliver (or fallback briefing if quality < 0.6).
- **Parallel nodes:** `gather_pipeline_updates`, `gather_new_jobs`, `gather_competitive_intel`, `gather_contact_changes`, `gather_graph_insights`.
- **Output:** Daily briefing pushed to dashboard channel.
- **Timeout:** 120s per gather node, 30-60s for processing nodes.

#### Contact Enrichment Workflow
- **File:** `workflows/production/contact_enrichment.py`
- **Human-in-the-loop:** Yes — pauses at `review_classifications` for Tier 1-3 approval (3600s timeout).
- **Nodes (11):** validate → 3-way parallel gather (Qdrant + Neo4j + Notion) → merge → classify (6-tier) → human review → LinkedIn enrichment (50 max) → ZoomInfo enrichment (graceful degradation) → update databases → generate report.
- **Output:** Tier/priority distribution report, updated Qdrant + Neo4j records.

#### Competitive Intelligence Workflow
- **File:** `workflows/production/competitive_intel.py`
- **Human-in-the-loop:** Yes — pauses at `validate_findings` for high-confidence alert review.
- **Nodes (12):** plan → 4-way parallel scrape (job boards + SAM.gov + LinkedIn + news) → merge/dedup → LLM analysis (hiring surge detection) → human validation → Neo4j cross-reference → update intel DB → generate briefing → distribute.
- **Monitored programs:** DCGS, JSTARS, GBSD, Next-Gen ISR.
- **Monitored competitors:** 9 companies (Leidos, Northrop, Booz Allen, Peraton, CACI, SAIC, ManTech, Raytheon, L3Harris).
- **Retry config:** Job boards 3x, SAM/LinkedIn/News 2x, LLM analysis 2x.

#### Pipeline Manager
- **File:** `workflows/production/pipeline_manager.py`
- **Purpose:** Scheduling and management of the above workflows.

### 4.2 Workflow Infrastructure

| File | Purpose |
|------|---------|
| `workflows/graph_builder.py` | `WorkflowDefinition`, `NodeSpec`, `EdgeSpec`, `RetryConfig` dataclasses |
| `workflows/orchestrator_v2.py` | V2 workflow execution engine |
| `workflows/checkpoint_store.py` | Workflow state persistence (resume after failure) |
| `workflows/time_travel.py` | State rollback/replay for debugging |
| `workflows/human_loop.py` | Human-in-the-loop interrupt handling |
| `workflows/workflow_routes.py` | FastAPI routes for workflow management |

### 4.3 CrewAI Crews

Defined in `Engine8_Knowledge/agents/crews.py`. All use `Process.sequential`.

#### BD Research Crew
- **Factory:** `create_bd_research_crew(program_name, agency, prime)`
- **Agents:** `program_researcher` → `contact_enricher` → `competitive_analyst` → `outreach_composer`
- **Tasks (5):**
  1. Program intel → `ProgramIntelligence` output
  2. Contact profiles with tier classification
  3. Competitive landscape → `CompetitiveReport` output
  4. Outreach plan using PTS BD Formula (6-step) → `OutreachPlan` output
  5. Synthesis → `BDResearchBundle` (combines all above)

#### Weekly Intel Crew
- **Factory:** `create_weekly_intel_crew(focus_programs)`
- **Agents:** `humint_analyst` → `competitive_analyst` → `program_researcher`
- **Tasks (4):**
  1. Weekly HUMINT synthesis from CRM notes → `HUMINTBrief`
  2. Competitor activity scan (new postings, placement changes)
  3. Weekly intelligence summary with prioritized actions
  4. Bundle → `WeeklyIntelBundle`

#### Contact Outreach Crew
- **Factory:** `create_contact_outreach_crew(contact_name, company, program)`
- **Agents:** `contact_enricher` → `program_researcher` → `outreach_composer`
- **Tasks (3):**
  1. Contact profile → `ContactProfile`
  2. Program context (contract status, labor gaps, past performance)
  3. Personalized outreach → `OutreachPlan`

### 4.4 Pipeline Orchestrator (11 Stages)

**File:** `orchestrator.py` (1,476 lines)

| Stage | Name | Description |
|-------|------|-------------|
| 1 | `ingest` | Load job data from Apify/CSV/JSON |
| 2 | `mapping` | Program Mapping — standardize jobs, match to 388 federal programs |
| 2b | `sam_sync` | SAM.gov Opportunity Sync (optional, requires `SAM_GOV_API_KEY`) |
| 2c | `ner_enrichment` | NER Entity Enrichment — extract people, orgs, programs from text |
| 5 | `scoring` | BD Priority Scoring — 0-100 across 5 signals |
| 6 | `qa` | QA Evaluation — validate scores, flag anomalies, generate alerts |
| 7 | `briefings` | BD Playbook briefings per contact/program combo |
| 8 | `export` | Export to Notion CSV + n8n JSON |
| 9 | `bullhorn_etl` | Bullhorn CRM ETL (293MB SQLite, sequential with stage 10) |
| 10 | `dashboard_export` | Dashboard export with verification (depends on stage 9) |
| 11 | `knowledge_indexing` | Qdrant vector store indexing (parallel with stages 9-10) |

**Parallel execution:** Stages 9+10 run sequentially in one thread; Stage 11 runs independently via `ThreadPoolExecutor`.

### 4.5 When to Use Workflow vs. Single Agent

| Scenario | Use |
|----------|-----|
| Quick factual lookup | Single agent via `quick_intel_workflow()` |
| One-off contact search | `ContactFinderAgent` directly |
| Full program capture strategy | `capture_strategy_workflow()` (4-agent chain) |
| Daily automated briefing | Morning Briefing LangGraph workflow |
| Bulk contact enrichment with approval | Contact Enrichment LangGraph workflow |
| Competitive landscape with validation | Competitive Intel LangGraph workflow |
| Full BD research for a program | BD Research CrewAI crew |
| Weekly team intelligence digest | Weekly Intel CrewAI crew |
| Personalized outreach for one contact | Contact Outreach CrewAI crew |
| Full pipeline (all engines) | `orchestrator.py` |

---

## 5. Key Skills by Category

Skills are invoked via `@skill-name` in prompts. The most important ~50 skills are listed below, grouped by use case.

### 5.1 BD Pipeline & Intelligence

| Skill | Purpose | Post-Completion |
|-------|---------|-----------------|
| `@pts-bd-pipeline` | 8-engine pipeline orchestration and scoring | Update pipeline status, scoring results |
| `@pts-federal-intel` | SAM.gov/FPDS/USASpending/Tango patterns | Update program data, contract intel |
| `@pts-contact-ops` | Bullhorn CRM, 6-tier hierarchy, HUMINT methodology | Sync CRM, update contact tiers |
| `@pts-arch-migration` | 3→2 repo consolidation, Supabase migration | Update architecture docs |

### 5.2 AI/ML & Agent Development

| Skill | Purpose | Post-Completion |
|-------|---------|-----------------|
| `@crewai` | CrewAI multi-agent patterns | Update crew definitions |
| `@langgraph` | LangGraph workflow patterns | Update workflow docs |
| `@langchain-architecture` | LangChain/LangGraph architecture | Update architecture docs |
| `@rag-engineer` | RAG implementation patterns | Update retrieval metrics |
| `@rag-implementation` | RAG pipeline implementation | Update RAG config |
| `@embedding-strategies` | Embedding model selection and tuning | Update embedding benchmarks |
| `@similarity-search-patterns` | Vector similarity search optimization | Update search metrics |
| `@ai-engineer` | General AI engineering patterns | Update AI component docs |
| `@ai-agents-architect` | Agent architecture design | Update agent docs |
| `@autonomous-agents` | Autonomous agent patterns | Update agent lifecycle docs |
| `@autonomous-agent-patterns` | Advanced autonomy patterns | Update agent behavior docs |
| `@prompt-engineering` | Prompt design and optimization | Update prompt library |
| `@prompt-caching` | Prompt caching strategies | Update cache config |
| `@context-manager` | Context window management | Update context strategies |
| `@hybrid-search-implementation` | BM25 + semantic hybrid search | Update search pipeline docs |

### 5.3 Data & Database

| Skill | Purpose | Post-Completion |
|-------|---------|-----------------|
| `@database-migration` | Schema migration patterns | Update migration log |
| `@postgres-best-practices` | PostgreSQL optimization | Update DB config docs |
| `@postgresql` | PostgreSQL patterns | Update schema docs |
| `@supabase-automation` | Supabase automation patterns | Update Supabase config |
| `@vector-database-engineer` | Vector DB (Qdrant) management | Update collection docs |
| `@vector-index-tuning` | Vector index optimization | Update index benchmarks |

### 5.4 Backend Development

| Skill | Purpose | Post-Completion |
|-------|---------|-----------------|
| `@fastapi-pro` | FastAPI best practices | Update API docs |
| `@fastapi-templates` | FastAPI project templates | Update endpoint docs |
| `@fastapi-router-py` | FastAPI router patterns | Update router docs |
| `@python-pro` | Python best practices | Update code style docs |
| `@python-patterns` | Python design patterns | Log patterns to memory |
| `@python-performance-optimization` | Python performance tuning | Update performance benchmarks |
| `@async-python-patterns` | Async Python (asyncio) patterns | Update async guidelines |
| `@pydantic-models-py` | Pydantic model patterns | Update model docs |
| `@api-design-principles` | REST API design | Update API style guide |

### 5.5 Frontend Development

| Skill | Purpose | Post-Completion |
|-------|---------|-----------------|
| `@nextjs-best-practices` | Next.js 16+ patterns | Update frontend docs |
| `@nextjs-app-router-patterns` | App Router patterns | Update routing docs |
| `@react-patterns` | React best practices | Update component docs |
| `@react-state-management` | State management patterns | Update store docs |
| `@zustand-store-ts` | Zustand store patterns | Update store definitions |
| `@tailwind-design-system` | Tailwind design system | Update design tokens |
| `@tailwind-patterns` | Tailwind CSS patterns | Update style docs |
| `@ui-ux-pro-max` | UI/UX design principles | Update design system docs |

### 5.6 Security

| Skill | Purpose | Post-Completion |
|-------|---------|-----------------|
| `@security-auditor` | Security audit patterns | Update audit findings |
| `@api-security-best-practices` | API security hardening | Update security docs |
| `@auth-implementation-patterns` | Authentication patterns | Update auth docs |
| `@secrets-management` | Secrets handling patterns | Update secrets policy |
| `@vulnerability-scanner` | Vulnerability scanning | Update vulnerability inventory |

### 5.7 Testing

| Skill | Purpose | Post-Completion |
|-------|---------|-----------------|
| `@test-driven-development` | TDD workflow | Update test strategy |
| `@tdd-workflow` | TDD cycle patterns | Update test coverage |
| `@python-testing-patterns` | pytest patterns | Update test docs |
| `@testing-patterns` | General testing patterns | Update test strategy |
| `@e2e-testing-patterns` | E2E test patterns | Update E2E docs |
| `@systematic-debugging` | Debugging methodology | Log debugging patterns |

### 5.8 DevOps & Infrastructure

| Skill | Purpose | Post-Completion |
|-------|---------|-----------------|
| `@docker-expert` | Docker patterns | Update Docker config docs |
| `@github-actions-templates` | CI/CD pipeline patterns | Update CI config |
| `@github-automation` | GitHub API automation | Update automation docs |
| `@deployment-engineer` | Deployment patterns | Update deployment docs |
| `@terraform-specialist` | Infrastructure as code | Update IaC docs |
| `@observability-engineer` | Monitoring and observability | Update monitoring docs |

### 5.9 Research & Outreach

| Skill | Purpose | Post-Completion |
|-------|---------|-----------------|
| `@deep-research` | Deep multi-source research | Update research findings |
| `@parallel-deep-research` | Parallel research execution | Update research findings |
| `@abm-outbound` | Account-based marketing outbound | Update campaign metrics |
| `@cold-outreach` | Cold outreach patterns | Update outreach templates |

### 5.10 Code Quality

| Skill | Purpose | Post-Completion |
|-------|---------|-----------------|
| `@clean-code` | Clean code principles | Update code standards |
| `@code-review-excellence` | Code review best practices | Update review checklist |
| `@production-code-audit` | Production code audit | Update audit findings |
| `@codebase-cleanup-tech-debt` | Tech debt management | Update tech debt inventory |
| `@legacy-modernizer` | Legacy code modernization | Update modernization roadmap |

### 5.11 Planning & Documentation

| Skill | Purpose | Post-Completion |
|-------|---------|-----------------|
| `@concise-planning` | Concise implementation plans | Update plan docs |
| `@plan-writing` | Detailed plan authoring | Update plan docs |
| `@docs-architect` | Documentation architecture | Update doc structure |
| `@senior-architect` | Senior architecture decisions | Update architecture docs |
| `@architecture` | Architecture patterns | Update architecture docs |

---

## 6. Chaining Patterns & Standard Workflows

### 6.1 New Feature Implementation

```
Plan → feature-dev:code-architect → [User implements] → code-simplifier → feature-dev:code-reviewer → voltagent-qa-sec:test-automator
```

1. **Plan** — Design implementation approach, get user approval.
2. **code-architect** — Blueprint with specific files, components, data flows.
3. **Implementation** — Write the code (user or agent).
4. **code-simplifier** — Refine for clarity and maintainability. *(Proactive)*
5. **code-reviewer** — Review for bugs, security, quality.
6. **test-automator** — Write and run tests.

### 6.2 Security Audit

```
voltagent-qa-sec:security-auditor → voltagent-qa-sec:penetration-tester → voltagent-qa-sec:compliance-auditor → voltagent-qa-sec:code-reviewer
```

1. **security-auditor** — Comprehensive audit, risk evaluation.
2. **penetration-tester** — Validate findings through active testing.
3. **compliance-auditor** — Map findings to compliance frameworks (NIST 800-53, etc.).
4. **code-reviewer** — Review specific code for security fixes.

### 6.3 BD Research (Full Capture Strategy)

```
ProgramIntelAgent → ContactFinderAgent → CompanyResearchAgent → BDStrategyAgent
```

Or use `BDCrewOrchestrator.capture_strategy_workflow(opportunity)` which chains all four.

1. **program_intel** — Program overview, contract structure, recompetes.
2. **contact_finder** — Key personnel, decision makers, clearance levels.
3. **company_research** — Competitor profiles, teaming history.
4. **bd_strategy** — Win themes, teaming strategy, 90-day action plan.

### 6.4 Code Review (Comprehensive)

```
pr-review-toolkit:code-reviewer → pr-review-toolkit:silent-failure-hunter → pr-review-toolkit:type-design-analyzer → pr-review-toolkit:comment-analyzer
```

1. **code-reviewer** — Full code review with issue classification.
2. **silent-failure-hunter** — Find swallowed exceptions, missing error handling.
3. **type-design-analyzer** — Validate type system consistency.
4. **comment-analyzer** — Analyze review comment patterns.

### 6.5 Performance Optimization

```
voltagent-qa-sec:performance-engineer → voltagent-qa-sec:architect-reviewer → voltagent-qa-sec:chaos-engineer
```

1. **performance-engineer** — Identify bottlenecks, measure baselines.
2. **architect-reviewer** — Evaluate optimization approach at architecture level.
3. **chaos-engineer** — Validate resilience under load/failure.

### 6.6 Data Pipeline

```
voltagent-research:data-researcher → database-migration skills → vector-database-engineer skills → voltagent-qa-sec:qa-expert
```

1. **data-researcher** — Discover sources, gather raw data, quality checks.
2. **Database migration** — Schema changes, data transformation.
3. **Vector DB** — Embedding, indexing, collection management.
4. **qa-expert** — Validate pipeline quality end-to-end.

### 6.7 Weekly BD Intelligence

```
Morning Briefing Workflow (daily) → Weekly Intel Crew (weekly) → Competitive Intel Workflow (as-needed)
```

1. **Morning Briefing** — Automated daily: pipeline updates, new jobs, competitive signals, contact changes, graph insights.
2. **Weekly Intel Crew** — Weekly: HUMINT synthesis, competitor activity, prioritized actions.
3. **Competitive Intel** — On-demand: 4-source parallel scrape, LLM analysis, human validation, Neo4j cross-reference.

### 6.8 Contact Enrichment (Full Pipeline)

```
ContactClassifierAgent → Contact Enrichment Workflow → ContactFinderAgent → Contact Outreach Crew
```

1. **ContactClassifier** — 6-tier classification, BD priority, location hub.
2. **Enrichment Workflow** — 3-source gather, merge, LinkedIn/ZoomInfo enrichment, human approval for Tier 1-3.
3. **ContactFinder** — Find additional related contacts.
4. **Outreach Crew** — Generate personalized outreach using PTS BD Formula.

---

## 7. Audit Log Format

All entries go in `docs/AGENT_AUDIT_LOG.md`. Use this exact format:

```markdown
## [YYYY-MM-DD HH:MM] [AGENT_TYPE] [STATUS: success|partial|failed]
- **Triggered by:** [user | automated | chained from <parent>]
- **Task summary:** [1-line description of what was requested]
- **Files modified:** [list or "none"]
- **Files created:** [list or "none"]
- **Files deleted:** [list or "none"]
- **Key findings:** [2-3 bullet summary of outcomes]
- **Memory updated:** [yes/no — if yes, what was added]
- **Docs refreshed:** [list of docs updated, or "none"]
- **Data stores changed:** [Qdrant collections, Neo4j nodes, Redis keys, or "none"]
- **Next recommended action:** [follow-up suggestion or "none"]
```

### Status Definitions

| Status | Meaning |
|--------|---------|
| `success` | All objectives met, all artifacts produced |
| `partial` | Some objectives met, some artifacts missing or incomplete |
| `failed` | Primary objective not met, error occurred |

### Agent Type Values

Use the exact subagent type name (e.g., `Explore`, `voltagent-qa-sec:security-auditor`, `ProgramIntelAgent`, `morning_briefing_workflow`, `bd_research_crew`).

### Example Entry

```markdown
## 2026-02-21 14:30 voltagent-qa-sec:security-auditor success
- **Triggered by:** user
- **Task summary:** Security audit of Engine8_Knowledge API endpoints
- **Files modified:** Engine8_Knowledge/api.py (added rate limiting)
- **Files created:** docs/SECURITY_AUDIT_20260221.md
- **Files deleted:** none
- **Key findings:**
  - 3 endpoints missing authentication middleware
  - SQL injection risk in search parameter (parameterized)
  - CORS wildcard on /dify/* endpoints
- **Memory updated:** yes — added SSRF prevention pattern, auth middleware gaps
- **Docs refreshed:** docs/BD_ENGINE_AUDIT_REPORT.md
- **Data stores changed:** none
- **Next recommended action:** Run penetration-tester to validate auth fixes
```

---

## Appendix: MCP Tools Quick Reference

The BD Intelligence Hub MCP server (`mcp/knowledge-mcp-server/server.py`) exposes 21 tools:

### Search (4)
| Tool | Purpose |
|------|---------|
| `search_knowledge` | Multi-collection search (jobs, contacts, programs, documents, activities) |
| `semantic_search` | Deep semantic similarity search across 1.42M vectors |
| `hybrid_search` | BM25 + semantic + CrossEncoder reranking |
| `smart_ask` | Auto-routes to optimal search system(s) |

### File & Dependency (3)
| Tool | Purpose |
|------|---------|
| `search_files` | Search indexed files by content/metadata |
| `get_file_info` | File metadata and relationships from Neo4j |
| `find_dependencies` | Upstream/downstream file dependencies |

### Graph (2)
| Tool | Purpose |
|------|---------|
| `query_knowledge_graph` | Natural language graph query (local/global/hybrid) |
| `find_relationships` | All relationships for a company/program/contact |

### BD Intelligence (2)
| Tool | Purpose |
|------|---------|
| `get_program_intel` | Full program intelligence report |
| `get_company_contacts` | Contacts at a company, filterable by tier |

### Memory (3)
| Tool | Purpose |
|------|---------|
| `memory_add` | Add to BD memory (interaction, fact, insight, observation) |
| `memory_search` | Search past memories and interactions |
| `memory_add_insight` | Add typed BD insight with confidence score |

### Ingest (2)
| Tool | Purpose |
|------|---------|
| `ingest_document` | Index a document (general, briefing, past_performance, proposal) |
| `ingest_program` | Add a federal program to the knowledge base |

### System (1)
| Tool | Purpose |
|------|---------|
| `get_system_stats` | Collection sizes, vector counts, API health, cache status |

---

## Appendix: API Endpoint Summary

Key API routers mounted on the FastAPI server (`Engine8_Knowledge/api.py`, port 8100):

| Router | Prefix | Key Endpoints |
|--------|--------|---------------|
| `auth_api` | `/auth` | JWT tokens, API key management |
| `hybrid_endpoints` | — | `/search/hybrid/v2`, `/sync/notion/*`, `/collections/*` |
| `ml_api` | `/ml` | NER, topic modeling, placement prediction, embeddings |
| `memory_api` | `/memory` | Memory CRUD, interactions, briefings, lifecycle |
| `monitoring_api` | `/monitoring` | Health, readiness, liveness, resource usage, alerts |
| `mcp_api` | `/mcp` | MCP server health, tools, config, stats |
| `org_chart_api` | `/org-chart` | Generate, export, compare org charts |
| `optimizer_api` | `/optimizer` | ML model assessment, optimization, retraining |
| `phase7_endpoints` | — | Data freshness, notifications, webhooks, AI costs |
| `phase8a_pipeline` | `/pipeline` | Pipeline run, status, history |
| `phase9a_competitive` | `/contracts`, `/competitive` | Contract awards, expiring, competitive summary |
| `phase10a_reports` | `/reports` | Weekly BD intelligence reports |
| Workflow routes | — | Workflow management (start, status, resume) |
| Agent routes | `/agents` | Agent invocation endpoints |
