# 🎯 MASTER ORCHESTRATION GUIDE
## PTS Unified Platform — Parallel Execution Map

**Date:** February 2026  
**Scope:** BD-Automation-Engine | Data-Scraper | N8N-Builder  
**Execution Mode:** 3 Auto-Claude terminals running in parallel

---

## HOW TO USE THIS GUIDE

You have **3 Auto-Claude terminal windows**, one open in each project folder:

| Terminal | Project Folder | Guide File |
|----------|---------------|------------|
| **Terminal A** | `C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine` | `01_IMPL_BD_Automation_Engine.md` |
| **Terminal B** | `C:\data-scraper\data-scraper` | `02_IMPL_Data_Scraper.md` |
| **Terminal C** | `C:\N8N Builder` | `03_IMPL_N8N_Builder.md` |

Each guide contains numbered steps with:
- ⚡ **PROMPT** blocks = Copy-paste into Auto-Claude terminal
- 💻 **COMMAND** blocks = Run directly in terminal/shell
- ✅ **VERIFY** blocks = How to confirm the step worked
- 🔗 **DEPENDS ON** = What must complete before this step starts
- 🔀 **PARALLEL** = Can run simultaneously with other marked steps

---

## PHASE 0: EMERGENCY SECURITY (Day 1 — All 3 terminals simultaneously)

```
TIMING: 2-3 hours total
ALL THREE TERMINALS RUN SIMULTANEOUSLY
```

| Step | Terminal A (BD-Engine) | Terminal B (Data-Scraper) | Terminal C (N8N-Builder) |
|------|----------------------|--------------------------|--------------------------|
| 0.1 | Fix .gitignore | Fix .gitignore + rotate keys | Fix .gitignore + rotate keys |
| 0.2 | Audit git history | Audit git history | Audit git history |
| 0.3 | Setup secrets management | Setup secrets management | Setup secrets management |

**All steps in Phase 0 run in parallel. No dependencies between terminals.**

---

## PHASE 1: STABILIZATION (Week 1 — All 3 terminals simultaneously)

```
TIMING: 5-7 days total
MOSTLY PARALLEL — see dependency notes
```

| Step | Terminal A (BD-Engine) | Terminal B (Data-Scraper) | Terminal C (N8N-Builder) |
|------|----------------------|--------------------------|--------------------------|
| 1.1 | Install shared packages | Install shared packages | Install shared packages |
| 1.2 | Add LLM retry logic (18 sites) | Add LLM retry logic (2 sites) | Add LLM retry logic (~10 sites) |
| 1.3 | Enable prompt caching | Enable prompt caching | Enable prompt caching |
| 1.4 | Structured logging | Structured logging | Structured logging |
| 1.5 | Add Pydantic models | Add Pydantic models | Generate requirements.txt + Pydantic |
| 1.6 | API auth + rate limiting | MCP auth | MCP auth |
| 1.7 | Clean dashboard temp files | — | — |
| 1.8 | Add error boundaries | — | — |

**Steps 1.1-1.6 run in parallel across all terminals. 1.7-1.8 are Terminal A only.**

---

## PHASE 2: DATABASE UNIFICATION (Weeks 2-4)

```
TIMING: 2-3 weeks
SEQUENTIAL START → THEN PARALLEL
Terminal A must complete 2.1-2.2 before B and C can start migrations
```

| Step | Terminal A (BD-Engine) | Terminal B (Data-Scraper) | Terminal C (N8N-Builder) |
|------|----------------------|--------------------------|--------------------------|
| 2.1 | Create unified Qdrant collections | ⏳ WAIT for 2.1 | ⏳ WAIT for 2.1 |
| 2.2 | Re-embed bd_knowledge (384→1536) | ⏳ WAIT for 2.2 | ⏳ WAIT for 2.2 |
| 2.3 | Build BaseDocument schema | Migrate ChromaDB → Qdrant | Migrate LanceDB → Qdrant |
| 2.4 | Build Notion↔Qdrant sync | Index Bullhorn 38K records | Export N8N contacts to Hub |
| 2.5 | Build Hub API extensions | Index USASpending data | Build Hub sync client |
| 2.6 | Build knowledge graph | Index FPDS data | Connect discovery engines to Hub |
| 2.7 | Test unified search | Test data pipeline to Qdrant | Test data pipeline to Qdrant |

**Terminal A leads. After 2.1-2.2, terminals B and C work in parallel.**

---

## PHASE 3: DASHBOARD REBUILD (Weeks 5-8)

```
TIMING: 3-4 weeks
TERMINAL A PRIMARY — B and C build integration endpoints
```

| Step | Terminal A (BD-Engine) | Terminal B (Data-Scraper) | Terminal C (N8N-Builder) |
|------|----------------------|--------------------------|--------------------------|
| 3.1 | Install TanStack Router + Query | Build scraper status API endpoint | Build workflow status API endpoint |
| 3.2 | Build typed API client | Build scraper trigger endpoint | Build discovery trigger endpoint |
| 3.3 | Build core routes (14 pages) | Build job export endpoint | Build enrichment trigger endpoint |
| 3.4 | Build Tool Control Panel | Test all Data-Scraper APIs | Test all N8N-Builder APIs |
| 3.5 | Add WebSocket layer | Connect WebSocket events | Connect WebSocket events |
| 3.6 | Build analytics module | — | — |
| 3.7 | Integration testing | Integration testing | Integration testing |

**Terminal A does dashboard. B and C build API endpoints the dashboard will call.**

---

## PHASE 4: AI ENHANCEMENT (Weeks 9-12)

```
TIMING: 3-4 weeks
ALL TERMINALS PARALLEL
```

| Step | Terminal A (BD-Engine) | Terminal B (Data-Scraper) | Terminal C (N8N-Builder) |
|------|----------------------|--------------------------|--------------------------|
| 4.1 | Expand CrewAI to 8 agents | Integrate Docling for docs | Enhance discovery with hybrid search |
| 4.2 | Implement hybrid search | Add reranking to scraper | Add reranking to enrichment |
| 4.3 | Add cross-encoder reranking | Build automated scrape scheduling | Build automated enrichment scheduling |
| 4.4 | RAGAS evaluation on all pipelines | Connect scraper to agent triggers | Connect enrichment to agent triggers |
| 4.5 | Enhanced playbook generation | — | — |
| 4.6 | Automated HUMINT reporting | — | — |

**All terminals work in parallel. Dependencies are within each terminal only.**

---

## PHASE 5: INTEGRATION & TESTING (Weeks 13-16)

```
TIMING: 3-4 weeks  
SEQUENTIAL INTEGRATION → PARALLEL TESTING
```

| Step | Terminal A (BD-Engine) | Terminal B (Data-Scraper) | Terminal C (N8N-Builder) |
|------|----------------------|--------------------------|--------------------------|
| 5.1 | End-to-end pipeline test | End-to-end scraper→Hub test | End-to-end discovery→Hub test |
| 5.2 | Cross-project orchestration | Performance optimization | Performance optimization |
| 5.3 | Dashboard integration test | Load testing | Load testing |
| 5.4 | Full system validation | Full system validation | Full system validation |

---

## QUICK START CHECKLIST

Before starting, confirm:
- [ ] All 3 project folders accessible
- [ ] Auto-Claude terminals open in each folder
- [ ] Python 3.10+ available in all terminals
- [ ] Node.js 18+ available (for dashboard)
- [ ] Git configured in all projects
- [ ] Internet access for pip/npm installs
- [ ] Qdrant running (Docker or local) — BD-Engine terminal
- [ ] Redis running — BD-Engine terminal
- [ ] Current API keys ready for rotation (Anthropic, OpenAI, Apify, Notion)

---

## ESTIMATED TOTAL TIMELINE

| Phase | Duration | Parallelization | Critical Path |
|-------|----------|-----------------|---------------|
| Phase 0 | Day 1 | Full parallel | None |
| Phase 1 | Week 1-2 | Full parallel | None |
| Phase 2 | Week 2-4 | A leads, then parallel | Qdrant setup (Terminal A) |
| Phase 3 | Week 5-8 | A primary, B/C support | Dashboard build (Terminal A) |
| Phase 4 | Week 9-12 | Full parallel | None |
| Phase 5 | Week 13-16 | Sequential then parallel | Integration testing |

**Total: ~16 weeks to full unified platform**  
**With aggressive parallelization: ~12 weeks possible**
