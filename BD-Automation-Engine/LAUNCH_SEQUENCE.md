# LAUNCH SEQUENCE: Production Platform Transformation

**Prerequisites:**
- OpenClaw running with Claude Max (x20) subscription ✅
- Auto Claude terminals available ✅
- Workspace: `C:\Auto-Claud\Auto-Claude\BD-Automation-Engine` ✅
- Both prompt documents saved ✅

---

## EXECUTION STRATEGY: Parallel + Sequential Hybrid

### Phase Execution Model

```
PARALLEL TRACK A                    PARALLEL TRACK B
┌──────────────────┐                ┌──────────────────┐
│   Phase 0        │──────┬────────>│   Phase 1        │
│ (Consolidation)  │      │         │  (Diagnostic)    │
│ 2 days           │      │         │  3 days          │
└──────────────────┘      │         └────────┬─────────┘
                          │                  │
                    SEQUENTIAL GATE          │
                          │                  │
                          ▼                  ▼
                    ┌──────────────────────────┐
                    │      Phase 2             │
                    │     (Ideation)           │
                    │      3 days              │
                    └──────────┬───────────────┘
                               │
                          SEQUENTIAL GATE
                               │
                               ▼
                    ┌──────────────────────────┐
                    │      Phase 3             │
                    │   (Architecture)         │
                    │      4 days              │
                    └──────────┬───────────────┘
                               │
                          SEQUENTIAL GATE
                               │
                   ┌───────────┴───────────┐
                   │                       │
                   ▼                       ▼
        ┌──────────────────┐    ┌──────────────────┐
        │   Phase 4        │    │   Phase 5        │
        │  (Execution)     │    │  (Market)        │
        │   5 days         │    │   2 days         │
        └──────────────────┘    └──────────────────┘

TOTAL DURATION: ~19 days
```

---

## STEP 1: Terminal Setup (5 minutes)

### Terminal Configuration

Open **3 Auto Claude terminals** in VS Code:

**Terminal 1 — Main WRAITH Commander (OpenClaw)**
```bash
# Directory: C:\Auto-Claud\Auto-Claude\BD-Automation-Engine
# Role: Phase orchestration, reporting, monitoring
# Token allocation: 200k (coordination only)
pwd
# Should output: C:\Auto-Claud\Auto-Claude\BD-Automation-Engine
```

**Terminal 2 — Code Execution (Auto Claude with PTY)**
```bash
# Directory: C:\Auto-Claud\Auto-Claude\BD-Automation-Engine
# Role: Coding agents for actual file changes
# Model: Claude Opus 4.6 (best for code)
pwd
```

**Terminal 3 — Parallel Tasks (Auto Claude)**
```bash
# Directory: C:\Auto-Claud\Auto-Claude\BD-Automation-Engine
# Role: Concurrent audits, analysis, report generation
# Model: Claude Sonnet 4.5 (balanced)
pwd
```

---

## STEP 2: Pre-Flight Checks (10 minutes)

Run from **Terminal 1 (WRAITH Commander)**:

```bash
# 1. Verify OpenClaw status
openclaw status

# 2. Check git status (should be clean)
git status

# 3. Create phase branches
git checkout -b phase-0-consolidation
git checkout -b phase-1-diagnostic
git checkout -b phase-2-ideation
git checkout -b phase-3-architecture
git checkout -b phase-4-execution
git checkout -b phase-5-market-strategy
git checkout phase-0-consolidation

# 4. Create deliverables directories
mkdir -p docs/phase_reports
mkdir -p memory/execution_log
mkdir -p data/deliverables/phase_0
mkdir -p data/deliverables/phase_1
mkdir -p data/deliverables/phase_2
mkdir -p data/deliverables/phase_3
mkdir -p data/deliverables/phase_4
mkdir -p data/deliverables/phase_5

# 5. Initialize execution log
echo "# Execution Log\nStarted: $(date)" > memory/execution_log/$(date +%Y-%m-%d).md

# 6. Backup current state
openclaw checkpoint-backup

# 7. Check available skills
openclaw skills list | grep -E "security|audit|architect|data|research"

# 8. Test sessions_spawn capability
openclaw agents list
```

---

## STEP 3: Launch Phase 0 — Repository Consolidation (Terminal 1)

**Why Phase 0 first:** Blocks all other work. Must consolidate workspace before agents can operate across all 3 repos.

### Option A: Via sessions_spawn (Recommended)

```bash
# From Terminal 1 (WRAITH Commander):

# Create Phase 0 task file
cat > phase_0_task.txt << 'EOF'
PHASE 0: Repository Consolidation & Data Migration

OBJECTIVE: Merge N8N-Builder and data-scraper into BD-Automation-Engine workspace

TASKS:
1. Pre-migration audit (file inventory, git history, hardcoded paths)
2. Copy repos into new structure:
   - N8N-Builder → BD-Automation-Engine/n8n-builder/
   - data-scraper → BD-Automation-Engine/data-scraper/
3. Fix all absolute paths to relative paths
4. Merge data/deliverables/ folders from all 3 projects
5. Update docker-compose.yml volume mounts
6. Test imports and agent routing
7. Update workspace config in .openclaw/

DELIVERABLES:
- PRE_MIGRATION_AUDIT.md
- POST_MIGRATION_REPORT.md
- WORKSPACE_CONFIG.md
- DATA_MIGRATION_MANIFEST.csv

SKILLS TO USE:
- git-expert (history preservation)
- file-structure-analyzer (inventory)
- docker-essentials (compose updates)
- coding-agent (path fixes)

POST-COMPLETION:
- Update EXECUTION_CONTROL_CENTER.md phase status
- Append to docs/AGENT_AUDIT_LOG.md
- Commit consolidated workspace to git

ACCEPTANCE CRITERIA:
- All 3 repos merged without file loss
- Git history preserved in original repos
- All imports work: python -c "from n8n_builder import *; from data_scraper import *"
- OpenClaw workspace path: C:\Auto-Claud\Auto-Claude\BD-Automation-Engine
- Subagent can read files from all 3 subdirectories
EOF

# Launch Phase 0 agent
openclaw sessions spawn \
  --task "$(cat phase_0_task.txt)" \
  --label phase-0-consolidation \
  --model anthropic/claude-sonnet-4-5 \
  --cleanup keep \
  --runTimeoutSeconds 14400
```

### Option B: Via Manual Coordination (If sessions_spawn unavailable)

Use **Terminal 2 (Coding Agent)**:

```bash
# Activate Claude Code
# Then paste Phase 0 task from phase_0_task.txt
# Agent will execute steps 1-7 interactively
```

---

## STEP 4: Monitor Phase 0 Progress (Terminal 1)

```bash
# Check running agents
openclaw subagents list

# View Phase 0 agent output (replace with actual session key from spawn output)
openclaw sessions history phase-0-consolidation --limit 50

# If agent needs guidance:
openclaw subagents steer \
  --target phase-0-consolidation \
  --message "Focus on data migration next. Generate DATA_MIGRATION_MANIFEST.csv"

# Check deliverables as they're created:
ls -lh data/deliverables/phase_0/
```

---

## STEP 5: Launch Parallel Phases 1 & 2 (After Phase 0 Complete)

Once Phase 0 agent reports completion (check `EXECUTION_CONTROL_CENTER.md`):

### Terminal 1 — Launch Phase 1 (Diagnostic)

```bash
# Create Phase 1 task file
cat > phase_1_task.txt << 'EOF'
PHASE 1: System Diagnostic & Competitive Analysis

OBJECTIVE: Comprehensive audit of technical health, security posture, and competitive positioning

SCOPE:
- BD-Automation-Engine (8 engines)
- n8n-builder (workflows)
- data-scraper (infrastructure)

TASKS:
1. Architecture Audit (code quality score, tech debt, dependencies)
2. Security Audit (P0/P1/P2 findings, compliance gaps)
3. Performance Analysis (API latency, query performance, bottlenecks)
4. Competitive Gap Analysis (vs Govini, Attain, SCI, Booz Allen)
5. User Journey Mapping (BD analyst workflows, friction points)
6. Production Readiness Checklist (deployment blockers)
7. Data Architecture Review (schemas, relationships, optimization opportunities)

DELIVERABLES (7 total):
- SYSTEM_HEALTH_REPORT.pdf (50 pages)
- SECURITY_AUDIT_FINDINGS.md
- PERFORMANCE_ANALYSIS.md
- COMPETITIVE_GAP_ANALYSIS.md
- USER_JOURNEY_MAP.pdf
- PRODUCTION_READINESS_CHECKLIST.md
- ARCHITECTURE_DIAGRAMS/ (15 diagrams)

SKILLS TO USE:
- security-guardian, aws-security-scanner, guard-scanner
- perf-profiler, healthcheck
- fundamental-stock-analysis (competitor financials)
- data-lineage-tracker
- figma (user journey diagrams)
- voltagent-qa-sec:security-auditor
- voltagent-qa-sec:architect-reviewer

SUBAGENTS TO SPAWN:
- security-auditor (voltagent) for comprehensive security scan
- performance-engineer for bottleneck analysis
- data-researcher for schema optimization recommendations

ACCEPTANCE CRITERIA:
- All 7 deliverables generated
- Security score calculated (current baseline)
- Performance baseline established (p95, p99 latencies)
- Competitive moats identified (3+ differentiators)
- Production blockers documented with priority levels
EOF

openclaw sessions spawn \
  --task "$(cat phase_1_task.txt)" \
  --label phase-1-diagnostic \
  --model anthropic/claude-sonnet-4-5 \
  --cleanup keep \
  --runTimeoutSeconds 28800
```

### Terminal 3 — Launch Phase 2 (Ideation) in Parallel

```bash
# Create Phase 2 task file
cat > phase_2_task.txt << 'EOF'
PHASE 2: Future State Vision & Feature Ideation

OBJECTIVE: Design the ideal BD intelligence platform that dominates the market

TASKS:
1. AI-Native Feature Ideation (autonomous lead qual, predictive recompete, NL queries)
2. UI/UX Transformation (dashboard design, mobile responsiveness, data viz)
3. Knowledge Management 2.0 (unified search, conversational interface, document intelligence)
4. Competitive Moats (10x value props, speed/coverage/insights advantages)
5. Integration Strategy (CRM, Notion, Bullhorn connectors)
6. ML/AI Roadmap (models to build, data requirements, success metrics)

DELIVERABLES (6 total):
- FUTURE_STATE_VISION_DOCUMENT.pdf (80 pages)
- FEATURE_ROADMAP.md (30 pages with user stories)
- UI_UX_MOCKUPS/ (Figma exports or wireframes)
- COMPETITIVE_DIFFERENTIATION_MATRIX.xlsx
- SUCCESS_METRICS_FRAMEWORK.md (KPIs, OKRs)
- BUILD_VS_BUY_ANALYSIS.md

SKILLS TO USE:
- figma (mockups)
- slides (presentation materials)
- GSD Claw (spec-driven feature planning)
- Dashboard (design patterns)
- cellcog (deep research on competitor features)
- parallel-search (market intelligence)
- adversarial-prompting (critique mode for feature ideas)

SUBAGENTS TO SPAWN:
- feature-dev:code-architect (for technical feasibility analysis)
- voltagent-research:deep-research (competitor feature deep dive)

ACCEPTANCE CRITERIA:
- Feature roadmap with 20+ features (prioritized)
- UI/UX mockups for dashboard, search, and reporting modules
- 5+ competitive moats identified with quantitative backing
- Success metrics framework (10+ KPIs)
- Build vs buy decisions for 10+ components
EOF

openclaw sessions spawn \
  --task "$(cat phase_2_task.txt)" \
  --label phase-2-ideation \
  --model anthropic/claude-sonnet-4-5 \
  --cleanup keep \
  --runTimeoutSeconds 28800
```

---

## STEP 6: Monitor Both Phases (Terminal 1)

```bash
# Check both agents
openclaw subagents list

# View progress
openclaw sessions history phase-1-diagnostic --limit 20
openclaw sessions history phase-2-ideation --limit 20

# Check deliverables
watch -n 60 'ls -lh data/deliverables/phase_1/ data/deliverables/phase_2/'

# Update control center every 2 hours
# (Agent will auto-update EXECUTION_CONTROL_CENTER.md)
```

---

## STEP 7: Sequential Phases 3, 4, 5

After Phases 1 & 2 complete (both agents report done):

### Launch Phase 3 — Architecture (Terminal 1)

```bash
openclaw sessions spawn \
  --task "$(cat 'FINAL RE-ENGINEERED PROMPT (Production-Ready with All Integrations.md' | sed -n '/PHASE 3/,/PHASE 4/p')" \
  --label phase-3-architecture \
  --model anthropic/claude-sonnet-4-5 \
  --cleanup keep \
  --runTimeoutSeconds 36000
```

After Phase 3 complete, launch Phases 4 & 5 in parallel:

### Launch Phase 4 & 5 (Terminal 1 & 3)

```bash
# Terminal 1: Phase 4 (Execution Roadmap)
openclaw sessions spawn \
  --task "$(cat 'FINAL RE-ENGINEERED PROMPT (Master Exec Plan).md' | sed -n '/PHASE 4/,/PHASE 5/p')" \
  --label phase-4-execution \
  --model anthropic/claude-sonnet-4-5 \
  --cleanup keep

# Terminal 3: Phase 5 (Market Strategy)
openclaw sessions spawn \
  --task "$(cat 'FINAL RE-ENGINEERED PROMPT (Production-Ready with All Integrations.md' | sed -n '/PHASE 5/,//p')" \
  --label phase-5-market-strategy \
  --model anthropic/claude-sonnet-4-5 \
  --cleanup keep
```

---

## STEP 8: Final Assembly & Review

After all 5 phases complete:

```bash
# Generate master execution summary
openclaw sessions spawn \
  --task "Review all phase deliverables in data/deliverables/phase_*/. Generate MASTER_EXECUTION_SUMMARY.pdf (20 pages) with: executive summary, key findings from each phase, integrated roadmap, go/no-go recommendation, next immediate actions." \
  --label master-summary \
  --model anthropic/claude-opus-4-6

# Create consolidated documentation
mkdir -p docs/transformation_complete
cp data/deliverables/phase_*/*.pdf docs/transformation_complete/
cp EXECUTION_CONTROL_CENTER.md docs/transformation_complete/
cp docs/AGENT_AUDIT_LOG.md docs/transformation_complete/

# Final checkpoint
openclaw checkpoint-backup
git add .
git commit -m "feat: production platform transformation complete - all 5 phases"
git push origin --all
```

---

## Token Budget Summary

| Session | Model | Est. Tokens | Duration |
|---------|-------|-------------|----------|
| WRAITH Commander (Term 1) | Sonnet 4.5 | 200k | 19 days |
| Phase 0 Agent | Sonnet 4.5 | 100k | 2 days |
| Phase 1 Agent | Sonnet 4.5 | 150k | 3 days |
| Phase 2 Agent | Sonnet 4.5 | 120k | 3 days |
| Phase 3 Agent | Sonnet 4.5 | 180k | 4 days |
| Phase 4 Agent | Sonnet 4.5 | 150k | 5 days |
| Phase 5 Agent | Sonnet 4.5 | 100k | 2 days |
| Task Executors (10-20 concurrent) | Sonnet/Opus mix | 1000k total | 19 days |
| **TOTAL** | | **~2000k** | **19 days** |

**Claude Max (x20) Daily Limit:** ~500k tokens/day  
**Strategy:** Parallel execution spreads load across multiple sessions  
**Safety Margin:** 3-tier architecture prevents single-session burnout

---

## Emergency Fallback Plans

### If Token Limit Hit Mid-Phase:

```bash
# Save progress
openclaw subagents list > agents_snapshot.txt
cat agents_snapshot.txt

# Kill all agents
openclaw subagents kill --all

# Restart from checkpoint
openclaw checkpoint-restore --latest

# Resume specific phase
openclaw sessions spawn --task "Resume Phase X from last checkpoint. Check EXECUTION_CONTROL_CENTER.md for completed tasks." --label phase-X-recovery
```

### If Agent Gets Stuck:

```bash
# Steer with specific instructions
openclaw subagents steer --target phase-X-label --message "You're stuck on task Y. Skip it and move to task Z. Document the blocker in ISSUES.md"

# Or kill and respawn with adjusted scope
openclaw subagents kill --target phase-X-label
# Edit phase_X_task.txt to remove problematic task
openclaw sessions spawn --task "$(cat phase_X_task.txt)" --label phase-X-retry
```

---

## Success Metrics

After 19 days, you should have:

- ✅ **46 deliverables** across 5 phases
- ✅ **Consolidated workspace** (3 repos → 1)
- ✅ **Production roadmap** (12 sprints, 6 months)
- ✅ **Technical blueprint** (150 pages)
- ✅ **Market strategy** (40 pages)
- ✅ **Security hardened** (score >90/100)
- ✅ **Competitive moats** (5+ differentiators)
- ✅ **Go-live checklist** (production-ready criteria)

**Next Step:** Execute Sprint 0 (implement Phase 3 infrastructure plan)

---

## Ready to Launch?

**Command to start Phase 0 NOW:**

```bash
openclaw sessions spawn \
  --task "$(cat phase_0_task.txt)" \
  --label phase-0-consolidation \
  --model anthropic/claude-sonnet-4-5 \
  --cleanup keep \
  --runTimeoutSeconds 14400
```

**Then monitor:**

```bash
openclaw subagents list
openclaw sessions history phase-0-consolidation
```

**I'll wait for your go-ahead to launch Phase 0.**
