FINAL RE-ENGINEERED PROMPT (Master Execution Plan)
MISSION: BD Automation Engine — Production Platform Transformation & Competitive Dominance

═══════════════════════════════════════════════════════════════════════════
SYSTEM CONTEXT
═══════════════════════════════════════════════════════════════════════════

AGENT IDENTITY: WRAITH (War Room AI Intelligence & Tactical Heuristics)
COUNCIL: 8 specialist personas (Strategist, Architect, Operative, Analyst, Commander, Guardian, Engineer, Diplomat)

WORKSPACE SCOPE:
- Primary: C:\Auto-Claud\Auto-Claude\BD-Automation-Engine (8 engines, 50+ endpoints, 250+ files)
- Satellite 1: C:\Auto-Claud\N8N-Builder (workflow automation)
- Satellite 2: C:\Auto-Claud\data-scraper (web scraping infrastructure)
- **Consolidation Target:** Merge N8N-Builder + data-scraper into BD-Automation-Engine as subdirectories

MISSION PARAMETERS:
- Target: Defense/IC subcontracting staffing firms
- Contract Criteria (ALL 4 required):
  1. Subcontracting staffing firms involved
  2. $100M+ contract value OR 100+ subcontractors
  3. Security clearance required
  4. NOT assigned to existing PTS account manager
- Portfolio Scale: ~$950M DCGS targeting
- Current Status: Operational but needs production hardening + competitive moats

EXISTING STRATEGIC ASSETS:
- BD Execution Strategy 2026 (14 deliverables in data/deliverables/reports/)
- Data Architecture V8 Explorer (PTS_DATA_ARCHITECTURE_EXPLORER_V8.html)
- Agent Best Practices Framework (docs/AGENT_BEST_PRACTICES.md, 580 lines)
- Agent Audit Log System (docs/AGENT_AUDIT_LOG.md)
- 7,337+ CRM contacts, 388 federal programs, 8,705+ vectors

═══════════════════════════════════════════════════════════════════════════
PHASE 0 — REPOSITORY CONSOLIDATION (The Architect + The Operative)
Duration: 2 days | Priority: P0 (Blocking)
═══════════════════════════════════════════════════════════════════════════

OBJECTIVE: Consolidate three repos into single workspace with clean git history

TASKS:

0.1 PRE-MIGRATION AUDIT
Skills: git-expert, file-structure-analyzer
Agents: Explore (file inventory), general-purpose (git history analysis)

Steps:
- Inventory all files in N8N-Builder and data-scraper
- Check for .git submodules, uncommitted changes, large binaries
- Verify no hardcoded paths referencing old locations
- Generate pre-migration manifest: files, sizes, last-modified

Deliverable: PRE_MIGRATION_AUDIT.md with:
- File count, total size per repo
- Git history summary (commit count, branches, tags)
- Files to exclude (node_modules, __pycache__, .env)
- Hardcoded path locations to fix

0.2 REPOSITORY MERGE
Skills: git-expert, docker-essentials
Agents: Bash (git commands), general-purpose (path updates)

New Structure:

BD-Automation-Engine/
├── Engine1_Scraper/
├── Engine2_ProgramMapping/
├── ...
├── Engine8_Knowledge/
├── n8n-builder/          ← FROM C:\Auto-Claud\N8N-Builder
├── data-scraper/         ← FROM C:\Auto-Claud\data-scraper
├── orchestrator.py
├── data/
│   ├── deliverables/     ← Merge outputs from all 3 projects
│   └── raw/
└── docs/
Steps:
1. Copy N8N-Builder → BD-Automation-Engine/n8n-builder/ (preserve .git for reference)
2. Copy data-scraper → BD-Automation-Engine/data-scraper/
3. Update all absolute paths to relative paths
4. Update docker-compose.yml if volumes reference old paths
5. Test imports: `python -c "from n8n_builder import *; from data_scraper import *"`
6. Update AGENTS.md, SOUL.md with new workspace path

Deliverable: 
- Consolidated repo with all 3 projects
- POST_MIGRATION_REPORT.md (what moved, what broke, what works)

0.3 WORKSPACE CONFIGURATION
Skills: agent-config, openclaw-checkpoint
Agents: general-purpose (config updates)

Steps:
- Update .openclaw/config.json with single workspace path
- Update all SKILL.md files that reference project paths
- Configure subagent routing: one agent per subdirectory
- Test: Spawn agent in n8n-builder/, verify it can read Engine8 files
- Backup consolidated workspace: `openclaw checkpoint-backup`

Deliverable: WORKSPACE_CONFIG.md documenting agent routing rules

═══════════════════════════════════════════════════════════════════════════
PHASE 1 — COMPREHENSIVE DIAGNOSTIC (The Strategist + The Guardian + The Analyst)
Duration: 5 days | Deliverable: System Health Report (SHR) + Data Intelligence Report (DIR)
═══════════════════════════════════════════════════════════════════════════

OBJECTIVE: Multi-dimensional audit across code, security, data, and competitive landscape

1.1 ARCHITECTURE AUDIT (Code Quality)
Skills: code-review-excellence, production-code-audit, clean-code
Agents: feature-dev:code-explorer, code-simplifier, voltagent-research:code-complexity-analyzer
Subagents: 3 parallel (one per project: BD-Engine, n8n-builder, data-scraper)

Tasks:
- Code quality score (current: 68/100 BD-Engine, unknown for others)
- Cyclomatic complexity analysis
- Dead code detection (functions/files never called)
- Import graph analysis (circular dependencies, unused imports)
- Documentation coverage (docstrings, README completeness)
- API endpoint inventory with response time baselines

Output: CODE_QUALITY_REPORT.md (per-project breakdown + consolidated score)

1.2 SECURITY POSTURE AUDIT
Skills: security-guardian, aws-security-scanner, guard-scanner
Agents: voltagent-qa-sec:security-auditor, voltagent-qa-sec:penetration-tester
Subagents: 2 parallel (security-auditor on all 3 projects, pentest on API endpoints)

Tasks:
- Re-verify Phase 1-4 fixes from previous hardening session
- Scan N8N-Builder and data-scraper for new vulnerabilities
- Check for secrets in git history across all 3 repos: `git log --all --full-history -- .env`
- Dependency vulnerability scan (pip-audit, npm audit, snyk)
- OWASP Top 10 compliance check
- Rate limiting validation (test with 1000 concurrent requests)

Output: SECURITY_AUDIT_CONSOLIDATED.md (P0/P1/P2 by project)

1.3 DATA ARCHITECTURE ANALYSIS (NEW SECTION)
Skills: data-lineage-tracker, database-operations, sql-toolkit
Agents: voltagent-research:data-researcher, feature-dev:code-architect
Subagents: 2 parallel (data inventory, schema analysis)

Tasks:
- **Load Data Architecture V8 Explorer** (PTS_DATA_ARCHITECTURE_EXPLORER_V8.html)
- Inventory all data files across 3 projects:
  - BD-Engine: data/deliverables/, outputs/, Engine*/data/
  - N8N-Builder: workflows/, exports/
  - data-scraper: scraped_data/, raw/
- Identify duplicate/stale/outdated files (same name, different timestamps)
- Map entities to storage locations (Qdrant collections, SQLite tables, CSV files, JSON files)
- Validate referential integrity (e.g., contact IDs in notes match contacts table)
- Calculate data freshness (last_updated timestamps, stale data >90 days)
- Build unified data catalog: Entity → Source → Storage → Update Frequency

Data Categories (from V8 Explorer):
1. Contracts (FPDS, SAM.gov, USASpending)
2. Programs (Tango Alpha, federal program DB)
3. Companies (Contractors, primes, subs)
4. Contacts (CRM, Bullhorn, LinkedIn)
5. Jobs (Clearance, skills, locations)
6. Relationships (Company-Program, Contact-Company, Program-Contract)
7. Intelligence (Notes, call logs, meetings)
8. Scoring (BD priority, quality scores)
Output: DATA_INTELLIGENCE_REPORT.md with:
- Entity-Relationship diagram (Mermaid)
- Storage matrix (Entity × Location × Format × Size × Freshness)
- Data quality scores per entity (completeness, accuracy, consistency)
- Deduplication opportunities
- Files to archive/delete (>90 days old, no recent access)

1.4 FILE ORGANIZATION & MIGRATION STRATEGY
Skills: file-structure-analyzer, data-lineage-tracker
Agents: general-purpose (file operations), Explore (glob patterns)
Subagents: 1 autonomous (file classification + migration)

Current Problem:
- Outputs scattered across 3 projects
- No consistent naming convention
- Duplicate files (e.g., 3 different "contacts.csv" files)
- No version control on data files

Proposed Structure:

BD-Automation-Engine/
├── data/
│   ├── raw/                 ← Immutable source data
│   │   ├── contracts/
│   │   ├── programs/
│   │   ├── contacts/
│   │   └── companies/
│   ├── processed/           ← Transformed data
│   │   ├── matched/
│   │   ├── enriched/
│   │   └── scored/
│   ├── deliverables/        ← User-facing outputs
│   │   ├── reports/         ← Markdown/HTML/PDF reports
│   │   ├── exports/         ← CSV/Excel for analysts
│   │   └── briefings/       ← Executive summaries
│   ├── archive/             ← Data >90 days old
│   └── metadata/            ← Schemas, lineage, catalogs
├── outputs/                 ← Temporary agent outputs (purge weekly)
Tasks:
- Classify all files in outputs/ folders across 3 projects
- Move to appropriate data/ subfolder
- Rename to convention: `YYYY-MM-DD_EntityType_Description.ext`
- Keep only most recent version of each logical file
- Archive old versions with timestamp
- Update all code references to new paths
- Generate data catalog JSON: `data/metadata/data_catalog.json`

Output: 
- Reorganized data/ directory
- FILE_MIGRATION_REPORT.md (what moved, what was deleted, what broke)
- data/metadata/data_catalog.json (AI-friendly file registry)

1.5 BD EXECUTION STRATEGY INTEGRATION
Skills: reporting, dashboard, slides
Agents: general-purpose (report consolidation)

Tasks:
- Review 14 existing strategy files in data/deliverables/reports/
- Extract key insights, metrics, and recommendations
- Integrate findings into Phase 1 System Health Report
- Identify gaps: What's missing from current strategy?
- Map strategy recommendations to Phase 2-5 features

Output: STRATEGY_INTEGRATION_MEMO.md linking existing reports to transformation roadmap

1.6 COMPETITIVE INTELLIGENCE GAP ANALYSIS
Skills: market-research, fundamental-stock-analysis (competitor financials)
Agents: deep-research, parallel-deep-research
Subagents: 4 parallel (one per competitor: Govini, Attain, SCI, Booz Allen)

Tasks:
- What do Govini, Attain, SCI, Booz Allen offer that we don't?
- Feature matrix: Our platform vs. competitors (20+ features)
- Pricing comparison: Usage-based vs. seat-based vs. enterprise
- Unique advantages of our 8-engine architecture
- Market positioning: Where are we Category King vs. also-ran?
- Analyst reviews, G2 ratings, customer testimonials

Output: COMPETITIVE_LANDSCAPE_ANALYSIS.md (50 pages)

1.7 PRODUCTION READINESS CHECKLIST
Skills: healthcheck, aws-ecs-monitor, docker-essentials
Agents: general-purpose (checklist validation)

Checklist Items:
- [ ] All P0 security issues resolved
- [ ] Test coverage >70% (current: ~40%)
- [ ] API latency <200ms p95 (measure with load testing)
- [ ] Database migrations tested (SQLite → Postgres)
- [ ] Observability stack running (logs, metrics, traces)
- [ ] Error tracking configured (Sentry or similar)
- [ ] Rate limiting enforced (100 req/min per key)
- [ ] Backup/restore tested (Qdrant, Neo4j, SQLite)
- [ ] Disaster recovery runbook documented
- [ ] Production environment provisioned (AWS/Azure)
- [ ] CI/CD pipeline functional (GitHub Actions)
- [ ] Documentation complete (API docs, user guides)

Output: PRODUCTION_READINESS_REPORT.md (✅ vs. ❌ for each item)

═══════════════════════════════════════════════════════════════════════════
CONSOLIDATED PHASE 1 DELIVERABLE
═══════════════════════════════════════════════════════════════════════════
Document: SYSTEM_HEALTH_REPORT.md (100 pages)

Structure:
1. Executive Summary (3 pages)
2. Code Quality Analysis (15 pages)
3. Security Audit Findings (20 pages)
4. Data Architecture Intelligence (25 pages) ← NEW SECTION
5. File Organization Results (10 pages) ← NEW SECTION
6. Competitive Landscape (20 pages)
7. Production Readiness Assessment (7 pages)

Appendices:
- Appendix A: Detailed code metrics
- Appendix B: Security vulnerability list
- Appendix C: Data catalog JSON
- Appendix D: Competitive feature matrix
- Appendix E: File migration manifest

Export Formats:
- SYSTEM_HEALTH_REPORT.md (source)
- SYSTEM_HEALTH_REPORT.pdf (via Pandoc)
- SYSTEM_HEALTH_REPORT.html (interactive dashboard)

═══════════════════════════════════════════════════════════════════════════
PHASE 2 — AI-NATIVE FEATURE IDEATION (The Architect + The Analyst + The Diplomat)
Duration: 4 days | Deliverable: Future State Vision Document (FSVD)
═══════════════════════════════════════════════════════════════════════════

OBJECTIVE: Design the features that make us 10x better than competitors
2.1 AUTONOMOUS BD FEATURES
Skills: agent-autonomy-kit, proactive-agent, autonomous-brain
Agents: adversarial-prompting (critique mode), GSD Claw (spec-driven)
Subagents: 2 parallel (feature brainstorm, user story writing)

Features to Design:
1. **Autonomous Lead Qualifier** — Replaces manual scoring with ML model
2. **Predictive Recompete Modeler** — Forecasts contract awards 90 days early
3. **Relationship Graph Intelligence** — "Who knows who" in DCGS ecosystem
4. **Natural Language Pipeline Queries** — "Show me all hot CONUS ISR contracts with Leidos as prime"
5. **Auto-Generated Opportunity Briefs** — GPT-4 + RAG → 2-page exec summary
6. **Real-Time Contract Alerts** — WebSocket push notifications for new contracts
7. **Intelligent Contact Routing** — Auto-assign leads to AMs based on territory + expertise
8. **Competitive Win/Loss Intelligence** — Track who won what, why, and predict next moves
9. **Automated Proposal Support** — Generate past performance narratives from CRM notes
10. **BD Dashboard 2.0** — Real-time pipeline health, forecasting, and analytics

For each feature:
- User story (As a [BD analyst], I want [feature], so that [benefit])
- Acceptance criteria (Given/When/Then)
- Technical feasibility (Easy/Medium/Hard)
- Competitive differentiation (Does anyone else have this?)
- Estimated LOE (story points)

Output: AI_FEATURES_BACKLOG.md (50+ user stories, prioritized)

2.2 UI/UX TRANSFORMATION
Skills: figma, dashboard, slides, apple-hig (design principles)
Agents: general-purpose (mockup generation)
Current State: API-first, no dedicated frontend
Proposed: Next.js dashboard with real-time updates

Design System:
- Style: Vercel-inspired minimalism (clean, fast, dark mode)
- Components: Tailwind UI + shadcn/ui
- Charts: Recharts or D3.js for relationship graphs
- Real-time: WebSocket for live pipeline updates
- Mobile: Responsive design for BD analysts in the field

Key Views:
1. **Pipeline Dashboard** — Active contracts, hot leads, team assignments
2. **Contract Explorer** — Search, filter, sort 10K+ contracts
3. **Contact Directory** — 7,337 contacts with relationship graph
4. **Program Intelligence** — 388 programs with prime/sub mapping
5. **Analytics** — Win rate, conversion funnels, territory performance
6. **Admin Panel** — User management, API keys, audit logs

Output: UI_UX_MOCKUPS/ (Figma designs exported as PNGs, 20+ screens)

2.3 KNOWLEDGE MANAGEMENT 2.0
Skills: muninn, memory-search, rag-construction
Agents: voltagent-research:knowledge-architect
Subagents: 1 (unified search design)

Proposed Features:
- Unified search across all 8 engines (currently siloed)
- Conversational query interface (natural language → SQL + vector search)
- Document intelligence: Auto-extract key personnel from proposal PDFs
- Memory layer: Remember analyst preferences, past searches, saved queries
- Smart summaries: "What happened with SAIC DCGS last quarter?"
- Cross-reference detection: "This contract mentions the same program as..."

Output: KNOWLEDGE_MGMT_SPEC.md (architecture + API design)

2.4 COMPETITIVE MOATS
Skills: market-research, fundamental-stock-analysis
Agents: adversarial-prompting (challenge assumptions)

Questions to Answer:
- What makes us 10x better than spreadsheets + LinkedIn?
- **Speed:** How fast can we go from contract notice → qualified lead? (Target: <30 seconds)
- **Coverage:** Do we have better DoD/IC contact data than anyone else?
- **Insights:** Can we predict contract awards before they happen?
- **Integration:** Do we plug into tools analysts already use (Salesforce, Notion, Slack)?
Output: COMPETITIVE_MOATS_ANALYSIS.md (10 pages)

═══════════════════════════════════════════════════════════════════════════
CONSOLIDATED PHASE 2 DELIVERABLE
═══════════════════════════════════════════════════════════════════════════

Document: FUTURE_STATE_VISION.md (80 pages)

Structure:
1. Executive Summary: The 10x Vision (5 pages)
2. AI-Native Features Roadmap (30 pages, 50+ user stories)
3. UI/UX Transformation (20 pages, Figma mockups)
4. Knowledge Management 2.0 (10 pages)
5. Competitive Differentiation Matrix (10 pages)
6. Success Metrics & KPIs (5 pages)

Export: .md, .pdf, .html (interactive prototype)

═══════════════════════════════════════════════════════════════════════════
PHASE 3 — TECHNICAL IMPLEMENTATION BLUEPRINT (The Architect + The Engineer)
Duration: 6 days | Deliverable: Technical Implementation Blueprint (TIB)
═══════════════════════════════════════════════════════════════════════════

OBJECTIVE: Production-ready architecture that scales to 100 users, 10M records, 1000 req/min

3.1 REBUILD VS. REFACTOR DECISION FRAMEWORK
Skills: senior-architect, architecture, pts-arch-migration
Agents: feature-dev:code-architect, voltagent-qa-sec:architect-reviewer
Decision Matrix:
| Criterion | Rebuild from Scratch | Strangler Fig Migration | Parallel Run |
|-----------|---------------------|------------------------|--------------|
| Tech Debt | >40% of codebase | 20-40% | <20% |
| Timeline | 6+ months acceptable | 3-6 months | 1-3 months |
| Risk Tolerance | High (greenfield) | Medium (gradual) | Low (safe) |
| Team Size | 3+ devs | 2 devs | 1 dev |
| Downtime OK? | Yes (beta users) | No (live users) | No (live users) |

Current Assessment:
- Tech debt: ~32% (estimated from code quality score 68/100)
- Timeline: 6 months target
- Risk: Medium (have beta users, can afford learning curve)
- Team: 1 human + unlimited AI agents
- Downtime: Can use feature flags for gradual rollout
**Recommendation:** Strangler Fig Pattern
- Keep engines 2-5, 7-8 (stable, well-tested)
- Rebuild Engine 1 (scraper) with modern stack
- Rebuild