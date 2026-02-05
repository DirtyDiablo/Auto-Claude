# GENERATED ANALYSIS & INTELLIGENCE FILES AUDIT

**Generated:** 2026-02-05
**Project:** BD-Automation-Engine (PTS BD Intelligence System)
**Scope:** Complete inventory of every generated analysis file, report, and processed output

---

## EXECUTIVE SUMMARY

| Category | Count | Total Size |
|----------|------:|----------:|
| **Markdown Reports** | 82 significant | ~15 MB |
| **Excel Workbooks** | 4 | 1.4 MB |
| **HTML Visualizations** | 3 unique | 549 KB |
| **Processed JSON** | ~85 files | ~12 MB |
| **Dashboard JSON** | 25 files | 16 MB |
| **SQLite Databases** | 4 unique | 294 MB |
| **Generated CSVs** | 60+ files | ~42 MB |
| **Python Analysis Scripts** | 12 generators | - |
| **Qdrant Vector DB** | 6 collections | 738 MB |
| **outputs/ directory total** | 120+ files | **52 MB** |
| **GRAND TOTAL** | **280+ files** | **~1.1 GB** |

**Vector Database:** 611,654 indexed records across 5 active collections (contacts, programs, jobs, documents, activities)

---

## TIER 1: IRREPLACEABLE ANALYTICAL WORK PRODUCT

These represent unique human-AI analytical work that would be lost if archived.

### A. Colton Scurry Account Takeover Analysis

**Path:** `Engine7_BullhornETL/colton_scurry_analysis/`
**Size:** 12 MB | **Files:** 45
**Created by:** Claude analysis sessions on Bullhorn CRM export data
**Input:** `bullhorn_master.db` (293 MB) - candidates, placements, activities, notes

#### Final Outputs (9 deliverables)

| File | Size | Content |
|------|------|---------|
| `FINAL_OUTPUTS/00_EXECUTIVE_TAKEOVER_SUMMARY.md` | 8 KB | Portfolio overview: $60K weekly spread, 27 contractors, 16 primes |
| `FINAL_OUTPUTS/01_BD_TAKEOVER_PLAYBOOK.md` | 11 KB | Step-by-step acquisition playbook |
| `FINAL_OUTPUTS/02_FAIR_GAME_CONTACTS_LIST.md` | 10 KB | 36 contactable leads for takeover |
| `FINAL_OUTPUTS/03_AGGREGATED_NOTES_BY_CONTACT.md` | 15 KB | Intelligence per contact (1,183 contacts) |
| `FINAL_OUTPUTS/04_PROGRAM_CONTACT_NOTES.md` | 12 KB | Program-specific intel (45+ programs) |
| `FINAL_OUTPUTS/05_PRIORITY_ACTION_CHECKLIST.md` | 8 KB | Prioritized action items |
| `FINAL_OUTPUTS/06_CONTRACT_PROGRAM_INTEL.md` | 12 KB | Contract intelligence |
| `FINAL_OUTPUTS/07_ACTION_ITEMS_DATABASE.md` | 19 KB | Actionable task database |
| `FINAL_OUTPUTS/08_MASTER_REFERRAL_NETWORK.md` | 19 KB | Referral relationship map |

#### Analysis Documents (13 files)

| File | Size | Content |
|------|------|---------|
| `ANALYSIS/00_QUICK_REFERENCE_CARD.md` | 2.7 KB | Quick lookup reference |
| `ANALYSIS/01_EXECUTIVE_SUMMARY.md` | 3.5 KB | Executive overview |
| `ANALYSIS/02_PRIME_CONTRACTOR_BREAKDOWN.md` | 7.2 KB | 16 prime contractors analysis |
| `ANALYSIS/03_ACTIVE_PLACEMENTS.md` | 4.3 KB | 264 active placements |
| `ANALYSIS/04_OPEN_JOBS_PIPELINE.md` | 4.6 KB | 22 open job opportunities |
| `ANALYSIS/05_CONTACTS_DATABASE.md` | 5.7 KB | 1,183 contacts overview |
| `ANALYSIS/06_BD_PLAYBOOK.md` | 6.5 KB | BD strategy document |
| `ANALYSIS/08_TRANSITION_CHECKLIST.md` | 4.9 KB | Transition procedures |
| `ANALYSIS/09_PROGRAM_MASTER_LIST.md` | 7.1 KB | 45+ programs listed |
| `ANALYSIS/10_PROGRAM_MASTER_LIST_COMPLETE.md` | 12 KB | Complete program database |
| `ANALYSIS/COLTON_SCURRY_AUTHORED_NOTES_MASTER.md` | **534 KB** | All authored notes extracted |
| `ANALYSIS/NOTES_EXTRACTED.md` | 18 KB | 2,687 notes analyzed |

#### Notes Deep Dive (7 files)

| File | Size | Content |
|------|------|---------|
| `ANALYSIS/NOTES_DEEP_DIVE/FULL_NOTES_EXPORT.md` | **1.7 MB** | Complete notes export (2,687 notes) |
| `ANALYSIS/NOTES_DEEP_DIVE/CONTACT_PROGRAM_MATRIX.md` | **834 KB** | Contact-to-program mapping |
| `ANALYSIS/NOTES_DEEP_DIVE/RAW_SHEETS_EXPORT.md` | 142 KB | Raw data sheets |
| `ANALYSIS/NOTES_DEEP_DIVE/PROGRAM_COMPLETE_DATABASE.md` | 140 KB | All programs database |
| `ANALYSIS/NOTES_DEEP_DIVE/ORG_STRUCTURE_MAP.md` | 89 KB | Organizational structures |
| `ANALYSIS/NOTES_DEEP_DIVE/PRIME_CONTRACTOR_PROGRAMS.md` | 79 KB | Prime-to-program mapping |
| `ANALYSIS/NOTES_DEEP_DIVE/NOTES_INTELLIGENCE_EXTRACT.md` | 45 KB | Key intelligence from notes |
| `ANALYSIS/NOTES_DEEP_DIVE/ACTIONABLE_INSIGHTS_REPORT.md` | 21 KB | Extracted actionable insights |

#### Excel Deliverable

| File | Size | Content |
|------|------|---------|
| `colton_scurry_analysis_complete.xlsx` | **1.3 MB** | Multi-tab Excel workbook |

### B. Coworker Takeover Analysis

**Path:** `outputs/coworker_takeover/`
**Size:** 8.9 MB | **Files:** 37
**Created by:** Claude analysis sessions

| File | Content |
|------|---------|
| `BD_TAKEOVER_PLAYBOOK.md` | BD takeover strategy |
| `INSTRUCTIONS.md` | Execution instructions |
| `contact_org_chart.csv` | Organizational chart data |
| `master_data.csv` (411 KB) | Master contact data |
| `programs/` (29 .md files) | Per-program analysis |
| `bd_playbook.json` (4.5 MB) | Structured playbook data |
| `parsed_data.json` (3.9 MB) | Parsed analysis data |
| `contacts.csv` | Contacts snapshot |
| `programs_jobs.csv` | Programs & jobs mapping |

### C. BD Briefings / Playbooks

**Path:** `outputs/BD_Briefings/`
**Size:** 176 KB | **Files:** 38
**Created by:** `Engine4_Playbook/scripts/bd_playbook_generator.py`
**Input:** Scored opportunities from Engine 5

Programs covered:
- AF DCGS (Langley, PACAF, Wright-Patt)
- BICES, Corporate HQ, DCGS variants
- Next Generation Interceptor, NSA Programs

Each opportunity generates: Briefing, Call Script, Email, Playbook, Talking Points

| Example Files | Content |
|---------------|---------|
| `AF DCGS - Langley_Intelligence Analyst_Playbook.md` | Full engagement playbook |
| `AF DCGS - Langley_Intelligence Analyst_CallScript.md` | Call talking points |
| `AF DCGS - Langley_Intelligence Analyst_Email.txt` | Email template |
| `AF DCGS - Langley_Intelligence Analyst_TalkingPoints.md` | Key messages |
| `Distributed Common Ground Syst_Senior Network Engineer - DCGS_Playbook.md` | DCGS playbook |

### D. HUMINT Intelligence Briefings

**Path:** `outputs/`
**Created by:** Claude analysis sessions on CRM data

| File | Size | Content |
|------|------|---------|
| `HUMINT_BD_BRIEFINGS_2026-01-24.md` | 17 KB | BD account manager briefings (NGC JTAGS, DCGS programs) |
| `HUMINT_JRSS_MONTGOMERY_2026-02-03.md` | 14 KB | JRSS program briefing |

---

## TIER 2: CLAUDE SESSION EXPORTS (Design Decisions & Architecture)

**Path:** `docs/Claude Exports/`
**Files:** 12 | **Total:** ~500 KB
**Value:** Captures architectural reasoning and design decisions

| File | Size | Topic |
|------|------|-------|
| `Apify_MCP_Server_Audit_Claude_Export_2026-01-10.md` | 78 KB | Apify scraper architecture analysis |
| `Job_Scraper_Engine_Optimization_Claude_Export_20250110.md` | 70 KB | Engine1 optimization design |
| `ProgramMappingEngine_Claude_Export_2026-01-10.md` | 53 KB | Program mapping design session |
| `Program_Mapping_Engine_AutoClaude_Task_Claude_Export_2025-01-10.md` | 51 KB | AutoClaude task design |
| `DCGS_BD_Intelligence_System_Claude_Export_Dec22_2025.md` | 43 KB | Original system design |
| `PTS_BD_Intelligence_System_Claude_Export_Jan2026.md` | 41 KB | System evolution |
| `DCGS_BD_Intelligence_System_Claude_Export_2025-01-10.md` | 39 KB | System iteration |
| `PTS_BD_Skills_Master_Audit_Claude_Export_20260110.md` | 38 KB | Skills audit |
| `Notion_MCP_Integration_Documentation_Claude_Export_2026-01-10.md` | 37 KB | Notion MCP integration |
| `PTS_BD_Intelligence_System_Claude_Export_2026-01-02.md` | 37 KB | System architecture |
| `Federal_Programs_Data_Transformation_Claude_Export_2025-12-27.md` | 33 KB | Data transformation design |
| `GOD_MODE_MCP_AUTO_CLAUDE_Export_20250110.md` | 33 KB | MCP server architecture |
| `PTS_Notion_Project_Handoff_Document.md` | 31 KB | Full Notion handoff |
| `Apex_Systems_Job_Scraper_Claude_Export_2026-01-08.md` | 30 KB | Apex scraper design |
| `DCGS_BD_Email_Campaign_Claude_Export_20260110.md` | 24 KB | Email campaign strategy |
| `NOTION_PROJECT_HANDOFF_COMPLETE.md` | 23 KB | Notion handoff complete |
| `ZoomInfo_Search_Strategy_DCGS_Claude_Export_20250110.md` | 21 KB | ZoomInfo research strategy |

---

## TIER 3: STRATEGIC PLANNING & ARCHITECTURE DOCUMENTS

**Path:** Root directory + `docs/`
**Value:** Institutional knowledge, implementation plans, system audits

| File | Size | Content |
|------|------|---------|
| `docs/Mind_Map_Dashboard_Architecture_v1.md` | 108 KB | Architecture mind map |
| `BD_AUTOMATION_ENGINE_IMPLEMENTATION_PLAN.md` | 105 KB | Full implementation plan |
| `docs/bd-dashboard/BD_Intelligence_Dashboard_Architecture_v1.md` | 93 KB | Dashboard architecture |
| `UNIFIED_BD_INTELLIGENCE_HUB_BUILD.md` | 88 KB | Hub consolidation plan |
| `01_IMPL_BD_Automation_Engine.md` | 68 KB | Implementation details |
| `ENHANCEMENT_IMPLEMENTATION_GUIDE_V2.md` | 63 KB | Enhancement roadmap |
| `docs/UNIFIED_INFRASTRUCTURE_GUIDE.md` | 45 KB | Infrastructure guide |
| `DEEP_AUDIT_BD-Automation-Engine.md` | 36 KB | System audit |
| `CORE_INFRASTRUCTURE_CODE.md` | 36 KB | Core code documentation |
| `repo-tools-capabilities-matrix (1).md` | 36 KB | Tools & capabilities matrix |
| `DEEP_AUDIT_DATA-SCRAPER.md` | 34 KB | Data-Scraper audit |
| `DEEP_AUDIT_N8N_BUILDER.md` | 33 KB | N8N-Builder audit |
| `BD_INTELLIGENCE_HUB_MASTER_UTILIZATION_GUIDE.md` | 32 KB | Usage guide |
| `MASTER_ECOSYSTEM_ARCHITECTURE.md` | 29 KB | Multi-system architecture |
| `BD_DASHBOARD_FULL_AUDIT.md` | 28 KB | Dashboard audit |
| `PROJECT_CAPABILITIES_BD-Automation-Engine.md` | 26 KB | Capabilities catalog |
| `docs/KNOWLEDGE_SYSTEM_ROADMAP.md` | ~15 KB | Knowledge system roadmap |
| `docs/KNOWLEDGE_SYSTEM_GUIDE.md` | ~12 KB | Knowledge system guide |
| `docs/AI_FILESYSTEM_GUIDE.md` | ~10 KB | AI filesystem guide |
| `docs/RAG_USAGE_GUIDE.md` | ~10 KB | RAG patterns guide |
| `docs/PROJECT_STRUCTURE.md` | 20 KB | Project structure |
| `docs/CROSS_PROJECT_SHARING.md` | ~8 KB | Cross-project sharing |
| `docs/UPSTREAM_MERGE_STRATEGY.md` | ~5 KB | Upstream merge strategy |

### Additional Strategic Documents

| File | Size | Content |
|------|------|---------|
| `docs/DoD_Program_Structure_Diagram.html` | 79 KB | Interactive DoD program visualization |
| `docs/bd-dashboard/BD_Intelligence_Dashboard_Architecture_Visualization.html` | 44 KB | Dashboard architecture diagram |
| `docs/notion-automation-workflow.md` | ~10 KB | Notion automation workflows |
| `docs/SUGGESTED_ENHANCEMENTS.md` | ~8 KB | Enhancement suggestions |
| `docs/IMPLEMENTATION_CHECKLIST.md` | ~5 KB | Implementation checklist |

---

## TIER 4: GENERATED DATA OUTPUTS

### A. Job Enrichment Pipeline (`outputs/`)

| File | Size | Content |
|------|------|---------|
| `all_jobs_complete.json` | 1.3 MB | All jobs fully processed |
| `all_jobs_enriched.json` | 1.0 MB | Enriched job data |
| `all_jobs_fully_enriched.json` | 1.1 MB | Fully enriched jobs |
| `all_jobs_with_hiring_leaders.json` | 1.3 MB | Jobs with hiring leaders |
| `enriched_jobs.json` | 8.7 KB | Sample enriched jobs |

### B. Engine1 Pipeline Stages (`outputs/`)

| File | Size | Content |
|------|------|---------|
| `engine1_parsed.json` | 975 KB | Raw parsed data |
| `engine1_ai_enriched.json` | 975 KB | AI enrichment pass |
| `engine1_relational_enriched.json` | 991 KB | Relational enrichment |
| `engine1_fallback_enriched.json` | 976 KB | Fallback enrichment |
| `engine1_fully_enriched.json` | 1.3 MB | Fully enriched output |
| `engine1_pts_refreshed.json` | 1.3 MB | PTS-refreshed data |

### C. Federal Programs Data (`outputs/`)

| File | Size | Content |
|------|------|---------|
| `federal_programs_data.json` | 646 KB | Programs database |
| `federal_programs_current.json` | 446 KB | Current programs |
| `federal_programs_updated.json` | 799 KB | Updated programs |

### D. BD Pipeline & Call Sheets (`outputs/`)

| File | Size | Content |
|------|------|---------|
| `BD_Pipeline_Report_2026-01-19_15-45.xlsx` | 29 KB | Excel pipeline report |
| `bd_playbook_monday_20260119_012059.csv` | 1.4 MB | Monday playbook |
| `bd_playbook_monday_20260119_012144.csv` | 1.4 MB | Monday playbook v2 |
| `bd_call_sheet_20260119_005930.csv` | 31 KB | Call sheet |
| `gdit_call_sheet.csv` | 243 KB | GDIT-specific call sheet |
| `job_opportunities_20260119_083758.csv` | 117 KB | Job opportunities snapshot |
| `BD_Playbook_2026-01-23.md` | 9.5 KB | BD playbook |
| `call_script_template.txt` | 4.4 KB | Call script template |

### E. Notion Database Snapshots (`outputs/`)

| File | Size | Content |
|------|------|---------|
| `notion_dbs.json` | 144 KB | Database schemas |
| `db_data_264def65*.json` | 396 KB | BD Opportunities data |
| `db_data_2ccdef65*.json` | 316 KB | DCGS Contacts data |
| `db_data_2563119e*.json` | 298 KB | GDIT Jobs data |
| `db_data_294def65*.json` | 247 KB | Programs data |
| `db_data_2ccdef65*80e4*.json` | 230 KB | Contacts data |
| `dcgs_contacts_data.json` | 334 KB | DCGS contacts |
| 11 additional `db_*.json` files | ~150 KB | Various database exports |

### F. Contractor & Contact Data (`outputs/`)

| File | Size | Content |
|------|------|---------|
| `contractors_data.json` | 34 KB | Contractor database |
| `contractors_data_full.json` | 31 KB | Full contractor list |
| `contractors_schema.json` | 7.2 KB | Data schema |
| `contractors_final.json` | 2.2 KB | Finalized contractors |
| `cv_data.json` | 15 KB | CV/resume data |
| `gdit_pts_data.json` | 280 KB | GDIT PTS data |
| `gdit_other_data.json` | 328 KB | Other GDIT data |

### G. ZoomInfo Research (`outputs/`)

| File | Size | Content |
|------|------|---------|
| `ZOOMINFO_EXPORT_STRATEGY_COMPREHENSIVE_20260122.md` | 26 KB | Export procedure |
| `ZoomInfo_Master_Search_List_2026-01-23.md` | 22 KB | Comprehensive search strategy |
| `ZoomInfo_Research_List_2026-01-23.md` | 20 KB | Research targets |
| `ZOOMINFO_STRATEGY_V2_CALL_NOTES_INTEGRATED_20260122.md` | 20 KB | Integrated strategy |
| `zoominfo_bullhorn_strategy_20260119.md` | 11 KB | Bullhorn integration strategy |
| `zoominfo_search_queries.csv` | 3.2 KB | Search query list |

### H. Gap Analysis (`outputs/`)

| File | Size | Content |
|------|------|---------|
| `PROGRAM_PLACEMENT_GAP_ANALYSIS_20260122.csv` | 5.6 KB | Program placement gaps |
| `SESSION_SUMMARY_20260119.md` | 3.7 KB | Session summary |
| `QUICK_ACTION_SHEET_20260122.md` | 3.7 KB | Quick reference actions |

---

## TIER 5: DASHBOARD DATA

### Live Dashboard Data (`dashboard/public/data/`, 16 MB)

| File | Size | Content |
|------|------|---------|
| `contacts_classified.json` | 9.6 MB | All contacts with 6-tier classification |
| `contact_org_chart.json` | 2.4 MB | Org chart visualization data |
| `contacts.json` | 1.0 MB | Contact database |
| `jobs.json` | 598 KB | Job postings |
| `programs.json` | 263 KB | Federal programs |
| `programs_enriched.json` | 209 KB | Enriched program data |
| `placements.json` | 238 KB | Placement history |
| `jobs_enriched.json` | 242 KB | Enriched job data |
| `past_performance.json` | 82 KB | Past performance data |
| `call_notes_contacts.json` | 189 KB | Call notes by contact |
| `call_notes_programs.json` | 21 KB | Call notes by program |
| `call_notes_primes.json` | 23 KB | Call notes by prime |
| `call_notes_locations.json` | 2.7 KB | Call notes by location |
| `call_notes_gaps.json` | 778 B | Staffing gaps |
| `call_notes_stats.json` | 2.7 KB | Call notes statistics |
| `call_notes_summary.json` | 540 B | Call notes summary |
| `prime_org_chart.json` | 29 KB | Prime org chart |
| `program_org_chart.json` | 268 KB | Program org chart |
| `referral_network.json` | 15 KB | Referral network map |
| `scurry_takeover.json` | 16 KB | Takeover analysis data |
| `contractors_enriched.json` | 4.9 KB | Enriched contractors |
| `correlation_summary.json` | 1.9 KB | Correlations |
| `correlation_summary_enriched.json` | 1.8 KB | Enriched correlations |
| `data_freshness.json` | 1.3 KB | Data freshness check |
| `summary.json` | 1.8 KB | Dashboard summary |

### BD Dashboard Data (`outputs/bd_dashboard/`, ~20 MB)

| File | Size | Content |
|------|------|---------|
| `contacts_classified.json` | 9.6 MB | Classified contacts |
| `mindmap_nodes.json` | 7.8 MB | Visualization nodes |
| `mindmap_edges.json` | 1.5 MB | Visualization edges |
| `jobs_enriched.json` | 242 KB | Enriched jobs |
| `programs_enriched.json` | 209 KB | Enriched programs |
| `contractors_enriched.json` | 4.9 KB | Contractors |
| `correlation_summary.json` | 1.9 KB | Correlations |

---

## TIER 6: STAGED DATA (Indexed into Qdrant)

### From Data-Scraper (`data/from_data_scraper/`, 57 CSVs + 2 JSONs)

#### Contact Intelligence

| File | Rows | Content |
|------|-----:|---------|
| `CONTACTS_INTELLIGENCE.csv` | 41,925 | Comprehensive contact database with programs, primes, clearances |
| `CONTACT_INTELLIGENCE_DETAILED.csv` | 6,158 | Detailed contact enrichment |
| `bullhorn_contacts_master.csv` | 9,319 | Bullhorn CRM contacts |
| `PHASE1_FAIR_GAME_CONTACTS.csv` | 7,491 | Fair game contacts (no competitor relationships) |
| `PHASE1_CLAIMED_CONTACTS.csv` | 6,757 | Claimed/contacted contacts |
| `ORG_CHART_DATA.csv` | 3,002 | Organizational structure |
| `colton_scurry_contacts.csv` | 1,183 | Colton Scurry contacts |
| `colton_scurry_contact_handoff.csv` | 156 | Handoff contacts |
| `ZOOMINFO_L3HARRIS.csv` | ~300 | L3Harris ZoomInfo export |

#### Program Intelligence

| File | Rows | Content |
|------|-----:|---------|
| `MASTER_PROGRAMS_ENRICHED.csv` | 8,415 | Federal programs with enrichment |
| `PROGRAMS_CLEAN.csv` | 75 | Clean programs list |
| `PROGRAMS_FROM_NOTES.csv` | 62 | Programs extracted from call notes |
| `GAP_PROGRAMS.csv` | ~200 | Program gaps identified |
| `PROGRAM_INTELLIGENCE_DETAILED.csv` | 401 | Detailed program intel |

#### Prime Contractor Intelligence

| File | Rows | Content |
|------|-----:|---------|
| `MASTER_PRIMES_ENRICHED.csv` | 6,091 | Prime contractor enrichment |
| `PRIME_INTELLIGENCE_DETAILED.csv` | 61 | Detailed prime analysis |
| `PRIMES_FROM_NOTES.csv` | 50 | Primes extracted from notes |
| `FULL_PRIME_ENRICHMENT.csv` | 300 | Full prime enrichment |
| `primes_usaspending_enriched.csv` | 25 | USASpending-enriched primes |
| `high_subcontract_activity.csv` | 969 | High subcontract activity |

#### Contracts & Opportunities

| File | Rows | Content |
|------|-----:|---------|
| `FULL_OPPORTUNITIES.csv` | 814 | All opportunities |
| `FULL_PROGRAM_CONTRACTS.csv` | 1,510 | Program contracts |
| `MASTER_CONTRACTS_COMBINED.csv` | 2,282 | All contracts combined |
| `PHASE2_PROGRAM_PIIDS_FULL.csv` | 2,118 | Program PIIDs |
| `PHASE5_RECENT_ACTIVE_CONTRACTS.csv` | 150 | Recent active contracts |
| `db1_dod_prime_contracts_100m.csv` | 1,932 | DoD primes >$100M |
| `db2_subawards_tango.csv` | 5,531 | Subaward data |
| `db3_dod_it_opportunities.csv` | 927 | IT opportunities |
| `db3_dod_opportunities_all.csv` | 3,505 | All DoD opportunities |
| `db3_dod_solicitations.csv` | 1,754 | Solicitations |
| `phase3_opportunities_tango.csv` | 3,399 | Opportunities (Tango) |
| `phase3_solicitations_only.csv` | 2,243 | Active solicitations |
| `L3Harris_GBS_PROGRAM_CONTRACTS.csv` | 59 | L3 GBS contracts |
| `L3Harris_SATCOM_RF_CONTRACTS.csv` | 85 | L3 SATCOM contracts |
| `navy_subaward_N00019.csv` | 590 | Navy subaward data |

#### BD Targets

| File | Rows | Content |
|------|-----:|---------|
| `master_bd_targets.csv` | 1,933 | All BD targets |
| `master_bd_targets_contract_enriched.csv` | 1,933 | Targets with contract data |
| `master_bd_targets_fpds_enriched.csv` | 1,933 | Targets with FPDS data |
| `db6_bd_targets_all.csv` | 1,932 | All BD targets |
| `db6_bd_targets_priority.csv` | 1,132 | Priority targets |
| `tier1_high_priority_targets.csv` | 1,068 | Tier 1 targets |
| `tier2_medium_priority_targets.csv` | 317 | Tier 2 targets |
| `tier3_standard_targets.csv` | 548 | Tier 3 targets |
| `it_services_all_targets.csv` | 56 | IT services targets |

#### Jobs

| File | Rows | Content |
|------|-----:|---------|
| `JOBS_ENRICHED.csv` | ~170 | Enhanced job listings |
| `JOBS_INTELLIGENCE_MAPPED.csv` | ~190 | Job-to-program mapping |
| `bd_top_program_jobs_detail.csv` | ~65 | Top program jobs |
| `colton_scurry_jobs.csv` | ~170 | Colton Scurry jobs |
| `hub_jobs_2026-01-26.json` | ~200 | Hub jobs JSON |
| `standardized_jobs_2026-01-26.json` | ~200 | Standardized jobs JSON |

#### Size/Agency Classification

| File | Rows | Content |
|------|-----:|---------|
| `size_billion_1b_5b.csv` | 538 | $1B-$5B contractors |
| `size_giant_5b_10b.csv` | 62 | $5B-$10B contractors |
| `size_large_500m_1b.csv` | 752 | $500M-$1B contractors |
| `size_mega_10b_plus.csv` | 39 | $10B+ contractors |
| `agency_Department_of_Defense.csv` | 1,932 | DoD agency data |
| `sam_data_elements.csv` | 370 | SAM.gov elements |

### From N8N-Builder (`data/from_n8n_builder/`)

#### Contacts (68 CSVs, ~32 MB)

| Category | Files | Content |
|----------|------:|---------|
| `*_Enriched.csv` (26 files) | 26 | Enriched contacts per prime (Accenture, AWS, BAE, Boeing, CACI, Deloitte, GDIT, Jacobs, KBR, L3Harris, Leidos, Lockheed Martin, ManTech, Microsoft, Northrop Grumman, Palantir, Parsons, Peraton, Raytheon, SAIC, Sierra Nevada, Unclassified) |
| Base contact CSVs | ~40 | Raw contact exports (DCGS contacts, Contact Search List, etc.) |
| `Contacts_TEMPLATE.csv` | 1 | Template (skipped during indexing) |

#### Documents (1 file, 15.7 MB)

| File | Content |
|------|---------|
| `documents/processed_docs.json` | 78 processed documents (briefings, analysis files) |

#### Bullhorn Activities (42 files, ~3 MB)

| Category | Files | Content |
|----------|------:|---------|
| Per-recruiter CSVs | ~30 | Client interviews, submissions, visits by recruiter ID |
| Summary CSVs | ~10 | Sales Activity Report, Master Data Aggregation, Contacts Master |
| JSON summaries | ~2 | Structured summaries |

---

## TIER 7: DATABASES

### Primary Databases

| Database | Size | Location | Content |
|----------|------|----------|---------|
| `bullhorn_master.db` | **293 MB** | `Engine7_BullhornETL/data/` | 897K rows: candidates (426K), activities (404K), call_notes (50K), contact_scores (9.8K), placements (616), past_performance (205) |
| `bd_graph.db` | 804 KB | `Engine8_Knowledge/data/` | Knowledge graph relationships |
| `memories.db` | 40 KB | `Engine8_Knowledge/data/` | AI memory layer |
| `page_index.db` | 24 KB | `Engine8_Knowledge/data/` | Document page index |

### Qdrant Vector Database (Live at localhost:6333)

| Collection | Records | Content |
|------------|--------:|---------|
| **activities** | 373,765 | Call notes, CRM activities, Bullhorn data |
| **contacts** | 193,593 | Contact intelligence across all sources |
| **documents** | 24,880 | Contracts, opportunities, briefings, analysis |
| **jobs** | 10,475 | Job postings and opportunities |
| **programs** | 506 | Federal programs (deduplicated) |
| **TOTAL** | **611,654** | All collections combined |

**Note:** 3 copies of Qdrant storage exist on disk:
- `data/qdrant/` - stale copy
- `Engine8_Knowledge/data/qdrant/` - stale copy
- `qdrant/` - stale copy (oldest)

Only the live Qdrant process at localhost:6333 has current data. The stale copies total ~1.5 GB that could be reclaimed.

### Duplicate Database Files

| Duplicate | Size | Location | Original |
|-----------|------|----------|----------|
| `data/bullhorn_master.db` | 293 MB | `data/` | Copy of `Engine7_BullhornETL/data/bullhorn_master.db` |
| `data/bd_graph.db` | 804 KB | `data/` | Copy of `Engine8_Knowledge/data/bd_graph.db` |
| `data/memories.db` | 40 KB | `data/` | Copy of `Engine8_Knowledge/data/memories.db` |
| `data/page_index.db` | 24 KB | `data/` | Copy of `Engine8_Knowledge/data/page_index.db` |

---

## TIER 8: ANALYSIS ENGINE SCRIPTS (12 Generators)

These are the Python scripts that PRODUCE analysis files.

| Script | Engine | Generates |
|--------|--------|-----------|
| `Engine2_ProgramMapping/scripts/pipeline.py` | E2 | Full 7-stage job enrichment pipeline |
| `Engine2_ProgramMapping/scripts/exporters.py` | E2 | Notion CSV + n8n JSON exports |
| `Engine4_Playbook/scripts/bd_playbook_generator.py` | E4 | BD briefings, call scripts, emails, talking points |
| `Engine5_Scoring/scripts/bd_scoring.py` | E5 | 0-100 BD priority scores + tier classification |
| `Engine7_BullhornETL/scripts/bd_intelligence_report.py` | E7 | Comprehensive BD intelligence JSON |
| `Engine7_BullhornETL/scripts/past_performance_report.py` | E7 | Defense primes past performance |
| `Engine7_BullhornETL/scripts/analyze_prime_contacts.py` | E7 | Prime contact coverage analysis |
| `Engine7_BullhornETL/scripts/contact_scoring.py` | E7 | Contact engagement scores (0-100) |
| `Engine7_BullhornETL/scripts/analyze_call_notes.py` | E7 | Call notes intelligence extraction |
| `Engine7_BullhornETL/scripts/financial_analysis.py` | E7 | Revenue, margins, financial metrics |
| `Engine7_BullhornETL/scripts/export_intelligence_dashboard.py` | E7 | Dashboard JSON exports |
| `Engine8_Knowledge/scripts/index_staged_data.py` | E8 | 9-phase vector indexing (200-batch, TPM-paced) |

### Supporting Processing Scripts

| Script | Engine | Purpose |
|--------|--------|---------|
| `Engine2_ProgramMapping/scripts/job_standardizer.py` | E2 | LLM-powered 28-field job standardization |
| `Engine2_ProgramMapping/scripts/program_mapper.py` | E2 | Multi-signal program matching (388 programs) |
| `Engine3_OrgChart/scripts/contact_classifier.py` | E3 | 6-tier contact hierarchy classification |
| `Engine7_BullhornETL/scripts/bullhorn_etl.py` | E7 | Master ETL processor (CSV -> SQLite) |
| `Engine7_BullhornETL/scripts/import_coworker_data.py` | E7 | Coworker data import |
| `Engine8_Knowledge/scripts/vector_store.py` | E8 | Qdrant vector store management |
| `Engine8_Knowledge/scripts/dedup_programs.py` | E8 | Programs collection deduplication |
| `index_contacts.py` | Root | Batch index contacts to Qdrant |
| `index_activities.py` | Root | Batch index activities to Qdrant |
| `index_contacts_openai.py` | Root | OpenAI-based contact indexing |
| `reindex_with_openai.py` | Root | Batch reindexing with OpenAI |
| `status_check.py` | Root | System status monitoring |

---

## TIER 9: OTHER FILES

### Excel Workbooks

| File | Size | Content |
|------|------|---------|
| `Engine4_Playbook/Templates/Gullette Pipeline 1-12.xlsx` | 41 KB | Pipeline template |
| `Engine7_BullhornETL/colton_scurry_analysis/colton_scurry_analysis_complete.xlsx` | 1.3 MB | Complete analysis workbook |
| `New Enhancements/Week3_Batch2_Execution_Tracker.xlsx` | 9.7 KB | Execution tracker |
| `outputs/BD_Pipeline_Report_2026-01-19_15-45.xlsx` | 29 KB | BD pipeline report |

### Word Documents

| File | Content |
|------|---------|
| `AI-Powered File Management and Knowledge Base/GitHub_Repository_Research_Report.docx` | GitHub research |
| `Engine1_Scraper/Configurations/Apex_Systems_Scraping_Guide.docx` | Scraper configuration |
| `Engine4_Playbook/Templates/PTS_Notion_Project_Handoff_Document.docx` | Project handoff |
| `PTS_Unified_Database_Architecture_Strategy.docx` | Architecture strategy |
| `PTS_Unified_Platform_Architecture_v2.docx` | Platform architecture |
| `PTS_Unified_Platform_Audit_v3.docx` | Platform audit |

### HTML Visualizations

| File | Size | Content |
|------|------|---------|
| `docs/DoD_Program_Structure_Diagram.html` | 79 KB | Interactive DoD program structure |
| `docs/bd-dashboard/BD_Intelligence_Dashboard_Architecture_Visualization.html` | 44 KB | Dashboard architecture diagram |
| `Engine2_ProgramMapping/data/Federal Programs *.html` | 426 KB | Federal programs Notion export |

### Indexing Progress Log

| File | Size | Content |
|------|------|---------|
| `outputs/INDEXING_PROGRESS_LOG.md` | 6.5 KB | Real-time indexing progress (7,389 -> 537,512, 72.7x growth) |

---

## ANALYSIS PIPELINE FLOW

```
Raw Data Sources
    |
    +-- Bullhorn CRM Exports (CSV)
    |       |
    |       v
    |   bullhorn_etl.py --> bullhorn_master.db (293 MB, 897K rows)
    |
    +-- Apify Job Scrapes (JSON)
    |       |
    |       v
    |   job_standardizer.py --> Standardized 28-field schema
    |       |
    |       v
    |   program_mapper.py --> Matched to 388 federal programs
    |       |
    |       v
    |   bd_scoring.py --> 0-100 scores, Hot/Warm/Cold tiers
    |       |
    |       v
    |   exporters.py --> Notion CSV + n8n JSON
    |
    +-- Contact Databases (CSV/JSON)
    |       |
    |       v
    |   contact_classifier.py --> 6-tier hierarchy classification
    |
    +-- All Sources Combined
            |
            v
        index_staged_data.py --> Qdrant (611K vectors)
            |
            +-- contacts (193,593)
            +-- activities (373,765)
            +-- documents (24,880)
            +-- jobs (10,475)
            +-- programs (506)
            |
            v
        Knowledge API (localhost:8100) --> Semantic Search + RAG
            |
            v
        BD Briefings, Playbooks, Intelligence Reports
```

---

## ACTION ITEMS

| Priority | Action | Impact | Rationale |
|----------|--------|-------:|-----------|
| **CLEANUP** | Remove stale Qdrant copies (`data/qdrant/`, `Engine8_Knowledge/data/qdrant/`, `qdrant/`) | -1.5 GB | 3 stale snapshots; only live Qdrant has current data |
| **CLEANUP** | Remove duplicate `data/bullhorn_master.db` | -293 MB | Duplicates `Engine7_BullhornETL/data/bullhorn_master.db` |
| **CLEANUP** | Remove duplicate `data/bd_graph.db`, `data/memories.db`, `data/page_index.db` | -1 MB | Duplicates of `Engine8_Knowledge/data/` files |
| **VERIFY** | Confirm 38 BD Briefing MDs are indexed in Qdrant `documents` collection | - | Should have been covered by doc indexer |
| **VERIFY** | Confirm Colton Scurry deep-dive MDs (3.5 MB) are indexed | - | High-value unique intelligence |
| **NONE** | All work product is already in BD-Automation-Engine | - | This IS the unified hub |

**Total reclaimable space from cleanup: ~1.8 GB**

---

## MIGRATION STATUS

All analytical work product from the 3 former projects has been consolidated:

| Source Project | Status | Data Location |
|---------------|--------|---------------|
| **Data-Scraper** | MIGRATED | `data/from_data_scraper/` (57 CSVs + 2 JSONs) -> indexed to Qdrant |
| **N8N-Builder** | MIGRATED | `data/from_n8n_builder/` (110+ files) -> indexed to Qdrant |
| **BD-Automation-Engine** | NATIVE | All engines, scripts, outputs in place |

**Nothing to migrate. This IS the unified hub. All 611,654 vectors are searchable through the Knowledge API at localhost:8100.**
