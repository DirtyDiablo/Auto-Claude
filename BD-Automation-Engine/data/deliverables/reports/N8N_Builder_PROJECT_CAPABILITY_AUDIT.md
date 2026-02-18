# PROJECT CAPABILITY AUDIT
## N8N Builder - Federal Contract BD Intelligence Platform

**Audit Date:** 2026-01-26
**Auditor:** Claude Code Diagnostic System

---

## EXECUTIVE SUMMARY

**This project is misnamed.** While titled "N8N Builder," it is actually a **comprehensive Federal Contract Business Development Intelligence Platform** that uses N8N for workflow orchestration. The actual capabilities far exceed simple N8N workflow building.

### True Project Identity

| Aspect | Reality |
|--------|---------|
| **Project Name** | "N8N Builder" (misnomer) |
| **Actual Purpose** | Federal Contract BD Intelligence & Automation Platform |
| **Primary Function** | Discover, enrich, and analyze federal contract opportunities |
| **Secondary Function** | CRM intelligence (Bullhorn) and sales enablement |
| **Tertiary Function** | N8N workflow orchestration for automation |

### Scale Metrics

| Metric | Count |
|--------|-------|
| Total Files | 4,898 |
| Python Scripts | 1,619 |
| Data Files (CSV/XLSX) | 713+ |
| Output Files Generated | 447+ |
| N8N Workflows (Cloud) | 37 (10 active) |
| Bullhorn Intelligence Files | 268 |
| Federal Programs Tracked | 1,000-1,400 |

---

## SECTION 1: OUTPUT FOLDER STRUCTURE

### Directory Hierarchy

```
C:\N8N Builder\output/
├── [ROOT] 23 CSV files - BD targets, phase analysis, competitor data
├── bd_databases/ (14 files + categorized/)
│   └── categorized/ (16 files) - Tier/size/agency segmentation
├── exports/ (30 files) - Actionable target lists, call sheets
├── intelligence/ (23 files + bullhorn/)
│   └── bullhorn/ (268 files across 22 subdirectories)
├── program_intelligence/ (17 files) - Program analysis suite
├── reports/ (45 files) - Documentation and status reports
├── targeting/ (8 files) - ZoomInfo and AM call lists
└── task_orders/ (3 files) - Contract task order data
```

### Subdirectory Purposes

| Directory | Files | Purpose |
|-----------|-------|---------|
| `bd_databases/` | 30 | Master BD targeting databases, tiered and categorized |
| `exports/` | 30 | Ready-to-use target sheets, call lists, opportunity lists |
| `intelligence/` | 291 | CRM analysis, competitive intel, hiring signals |
| `program_intelligence/` | 17 | Federal program analysis and enrichment |
| `reports/` | 45 | Documentation, API guides, status reports |
| `targeting/` | 8 | Account manager targeting lists (Excel) |
| `task_orders/` | 3 | Contract task order extraction |

### Bullhorn Intelligence Breakdown (268 files)

| Subdirectory | Files | Content |
|--------------|-------|---------|
| `meeting_prep/` | 51 | Pre-meeting intelligence packets |
| `all_playbooks/` | 32 | Individual company account playbooks |
| `battlecards/` | 21 | Competitive battlecards (SAIC, Leidos, Peraton, etc.) |
| `bd_playbooks/` | 22 | BD strategy playbooks with campaign indexes |
| `advanced_tools/` | 24 | Revenue forecasting, territory optimization |
| `job_opportunities/` | 16 | Program-specific opportunity catalogs |
| `sdvosb_targeting/` | 14 | SDVOSB-specific targeting intelligence |
| `notes_deep_analysis/` | 14 | CRM notes analysis and insights |
| `deep_analysis/` | 11 | Detailed analytical breakdowns |
| `recommendations/` | 9 | Strategic next-best-action recommendations |
| `competitive_intel/` | 6 | Market share, competitor tracking |
| `email_campaigns/` | 6 | Campaign templates and sequences |
| `virgin_territory/` | 6 | Untapped market opportunities |
| `territory_grab/` | 5 | Territory expansion strategies |
| `gap_analysis/` | 5 | Skill/market gap analysis |
| `data_cleanup/` | 5 | Data quality and deduplication |
| `alerts/` | 4 | Hiring alerts and signal summaries |
| `job_analyzer/` | 4 | Job classification tools |
| `program_categories/` | 3 | Program categorization |
| `dashboards/` | 17 | Executive dashboards |

---

## SECTION 2: DATA OUTPUTS DOCUMENTATION

### Master Databases

#### 1. `master_bd_targets.csv` (691 KB)
**Purpose:** Consolidated BD targeting database with scoring

**Source Pipeline:**
- Discovery engines → Enrichment → Merge & Deduplicate → Scoring

**Key Columns:**
```
award_amount, award_id, awarding_agency, bd_reasons, bd_score,
contract_id, description, end_date, is_it_services, naics_code,
pop_city, pop_state, priority_tier, psc_code, recipient_name,
recipient_uei, size_tier, start_date, sub_recipient_count,
subaward_count, subaward_total_value, vendor_prime_count
```

**Creation Method:**
1. Tango API contract discovery (NAICS-grouped queries)
2. USASpending subaward enrichment
3. BD score calculation (value + subs + IT services + hiring)
4. Priority tier assignment (1=High, 2=Medium, 3=Standard)

---

#### 2. `master_program_intelligence.csv` (15 KB)
**Purpose:** Federal program intelligence with hiring velocity

**Source Pipeline:**
- Federal Programs Discovery V2 → Enrichment V4 → Intelligence Synthesis

**Key Columns:**
```
program_name, program_acronym, agency, prime_contractor,
primary_location, clearance_requirements, key_technologies,
functional_areas, total_job_postings, hiring_velocity,
contract_number, location_count, technology_count,
all_locations, all_technologies
```

**Creation Method:**
1. Job posting analysis by program keyword matching
2. Technology signal extraction (Cloud, DevOps, AI/ML, Cyber)
3. Clearance requirement parsing
4. Multi-location aggregation
5. Hiring velocity calculation (jobs/month)

---

#### 3. `bd_hot_hiring_programs.csv` (6 KB)
**Purpose:** Programs with active hiring signals - prioritized for BD outreach

**Key Columns:**
```
rank, program, total_jobs, recent_jobs, agency,
primes, locations, clearances
```

**Creation Method:**
1. Aggregate job postings by program
2. Calculate 30-day hiring velocity
3. Rank by recent job activity
4. Include clearance and location data

---

#### 4. `task_orders_by_program.csv` (10 KB)
**Purpose:** Contract task order extraction for program analysis

**Source:** USASpending IDV (Indefinite Delivery Vehicle) API

**Key Columns:**
```
parent_contract_id, parent_piid, task_order_piid,
task_order_description, award_amount, obligated_amount,
start_date, end_date, pop_city, pop_state, pop_country,
performing_org, performing_org_uei, awarding_agency,
awarding_sub_agency, naics_code, psc_code, extraction_date
```

**Creation Method:**
1. Query USASpending `/idvs/awards/` endpoint
2. Extract child awards and grandchild awards
3. Map to parent contracts
4. Calculate task order metrics

---

#### 5. `technology_skills_intelligence.csv`
**Purpose:** Technology stack and skills analysis from job postings

**Location:** `output/intelligence/bullhorn/deep_analysis/`

**Key Columns:**
```
technology, skill_category, mention_count, programs,
job_titles, demand_trend
```

**Creation Method:**
1. NLP extraction from job descriptions
2. Technology keyword matching
3. Skill categorization (Cloud, Security, Data, DevOps)
4. Trend analysis over time

---

## SECTION 3: ACTUAL TASKS PERFORMED

### 3.1 Data Scraping & Collection

| Source | Method | Output |
|--------|--------|--------|
| **Tango API** | REST API (contracts, entities) | Prime contracts, subawards |
| **USASpending API** | REST API (awards, subawards, IDVs) | Contract details, task orders |
| **SAM.gov API** | REST API (opportunities, entities) | Active solicitations |
| **Bullhorn CRM** | Export processing | Contact/activity intelligence |
| **Job Boards** | Keyword scraping | Hiring signals |

### 3.2 Bullhorn Data Analysis

**Files Processed:** 6,000+ contacts, 200+ programs, 400+ placements

| Analysis Type | Output |
|---------------|--------|
| Contact HUMINT | `contacts_humint.csv` (6,151 contacts) |
| Job-Contact Matrix | `contact_job_matrix.csv` (481 relationships) |
| Hiring Signals | `hiring_signals.csv` (384 KB) |
| Placement History | `placements_all.csv` (675 KB) |
| Dormant Relationships | `dormant_relationships_reactivation.csv` |
| Contact Network Map | `contact_network_map.csv` (1,127 contacts) |

### 3.3 Contract/Award Analysis

| Analysis | Description | Output |
|----------|-------------|--------|
| DoD Prime Contracts | $100M+ contracts with DoD agencies | `db1_dod_prime_contracts_100m.csv` |
| Subaward Analysis | Subcontractor relationships | `db2_subawards_tango.csv` |
| Competitor Awards | Awards to tracked competitors | `db7_competitor_prime_awards.csv` |
| High Sub-Spend | Programs with $100M+ sub activity | `HIGH_SUB_SPEND_QUALIFIED.csv` |

### 3.4 Program Intelligence Generation

**7-Phase Intelligence Pipeline:**

1. **Contract Discovery** - Find qualifying contracts ($10M+, IT services)
2. **Contract Enrichment** - Add recipient details, dates, agency info
3. **Subaward Collection** - Map subcontractor relationships
4. **Task Order Collection** - Extract IDV child awards
5. **Location Enrichment** - Geographic distribution
6. **Technology Extraction** - Tech stack identification
7. **Intelligence Synthesis** - BD scoring and tier assignment

### 3.5 BD Scoring & Prioritization

**BD Score Factors:**
- Award amount (weight: 30%)
- Subcontractor count (weight: 25%)
- IT services flag (weight: 20%)
- Hiring velocity (weight: 15%)
- Recompete proximity (weight: 10%)

**Priority Tiers:**
- **Tier 1 (High):** BD Score > 80, active hiring, recompete within 12 months
- **Tier 2 (Medium):** BD Score 50-80, some hiring activity
- **Tier 3 (Standard):** BD Score < 50, baseline tracking

---

## SECTION 4: DATA PIPELINES

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA SOURCES (INPUT)                        │
├─────────────────────────────────────────────────────────────────┤
│  Tango API    USASpending    SAM.gov    Bullhorn    Job Boards  │
│  (Contracts)  (Awards)       (Opps)     (CRM)       (Hiring)    │
└──────┬──────────────┬────────────┬──────────┬──────────┬────────┘
       │              │            │          │          │
       ▼              ▼            ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DISCOVERY TIER                               │
├─────────────────────────────────────────────────────────────────┤
│  Federal Programs    DoD Staffing    High Sub-Spend             │
│  Discovery V2        Discovery       Discovery                  │
│  (800-1,200 pgms)    (DoD focus)     (Top 10 primes)            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ENRICHMENT TIER                              │
├─────────────────────────────────────────────────────────────────┤
│  Phase 1: Task Orders    Phase 2: Locations                     │
│  Phase 3: Org Hierarchy  Phase 4: Technologies                  │
│  Tango V4 Enrichment     DIIG CSIS Lookups                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SYNTHESIS TIER                               │
├─────────────────────────────────────────────────────────────────┤
│  Merge & Deduplicate  →  BD Scoring  →  Tier Assignment         │
│  (1,000-1,400 programs in master database)                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT TIER                                  │
├─────────────────────────────────────────────────────────────────┤
│  Master DBs      Exports        Reports       Targeting         │
│  (bd_databases)  (call sheets)  (guides)      (Excel lists)     │
└─────────────────────────────────────────────────────────────────┘
```

### Script-to-Output Mapping

| Script | Input | Output |
|--------|-------|--------|
| `federal-programs-discovery-engine-v2.py` | Tango API | `DISCOVERED_PROGRAMS_*.csv` |
| `dod-staffing-discovery-WORKING.py` | Tango + USASpending | `dod-staffing-programs-*.csv` |
| `high-sub-spend-discovery-v2.py` | USASpending | `HIGH_SUB_SPEND_*.csv` |
| `enrich-federal-programs-v4-TANGO.py` | Active programs + APIs | `ENRICHED V4 TANGO.csv` |
| `run_enrichment.py` | db1 contracts | `task_orders_*.csv`, `team_locations.csv` |
| `merge-and-deduplicate.py` | Enriched + Discovered | `Federal Programs MASTER.csv` |
| `program_intelligence_pipeline.py` | USASpending | `master_program_intelligence.csv` |

---

## SECTION 5: N8N WORKFLOW STATUS

### Cloud Deployment Summary

| Status | Count | Usage |
|--------|-------|-------|
| **Active** | 10 | Currently running production workflows |
| **Inactive** | 27 | Development/deprecated workflows |
| **Total** | 37 | All deployed workflows |

### Active Workflows (Production)

| Workflow | Purpose | Trigger |
|----------|---------|---------|
| Scraper - Full Pipeline | End-to-end scraping orchestration | Webhook |
| Monitor - Health Check | System health monitoring | Schedule |
| Alert - Slack Notification | Slack alerting | Webhook |
| Pipeline - Competitor Analysis | Competitor tracking | Webhook |
| Pipeline - BD Intelligence | BD intelligence generation | Webhook |
| Hub - Search | Intelligence hub search | Webhook |
| Hub - Add Insight | Add insights to hub | Webhook |
| Hub - Ingest Jobs | Job data ingestion | Webhook |
| Hub - Smart Query | AI-powered queries | Webhook |
| Scraper - Trigger Job Scrape | Job scraping trigger | Webhook |

### Workflow Relevance Assessment

| Category | Status | Recommendation |
|----------|--------|----------------|
| Hub workflows (4) | **ACTIVE** | Keep - core functionality |
| Scraper workflows (2) | **ACTIVE** | Keep - data collection |
| Pipeline workflows (2) | **ACTIVE** | Keep - intelligence generation |
| Alert workflows (1) | **ACTIVE** | Keep - notifications |
| Monitor workflows (1) | **ACTIVE** | Keep - health checks |
| Legacy "My workflow" (5) | INACTIVE | Delete - test workflows |
| PTS BD workflows (3) | INACTIVE | Review - may have value |
| Other inactive (19) | INACTIVE | Audit individually |

---

## SECTION 6: CAPABILITY SUMMARY

| Actual Capability | Evidence | Status |
|-------------------|----------|--------|
| **Federal Contract Discovery** | 3 discovery engines, 1,400 programs tracked | FULLY OPERATIONAL |
| **Contract Data Enrichment** | 4-phase enrichment pipeline, 60-column master DB | FULLY OPERATIONAL |
| **BD Scoring & Prioritization** | Automated scoring, 3-tier system | FULLY OPERATIONAL |
| **Subcontractor Analysis** | Tango + USASpending subaward APIs | FULLY OPERATIONAL |
| **Task Order Extraction** | USASpending IDV API integration | FULLY OPERATIONAL |
| **Competitor Tracking** | 10+ prime contractors, battlecards | FULLY OPERATIONAL |
| **Program Intelligence** | 17 intelligence outputs, 7-phase pipeline | FULLY OPERATIONAL |
| **Bullhorn CRM Analysis** | 268 files, 6,000+ contacts analyzed | FULLY OPERATIONAL |
| **Hiring Signal Detection** | Job board scraping, velocity tracking | FULLY OPERATIONAL |
| **Geographic Intelligence** | Location enrichment, territory mapping | FULLY OPERATIONAL |
| **Technology Stack Analysis** | NLP extraction, skills categorization | FULLY OPERATIONAL |
| **N8N Workflow Automation** | 10 active workflows, hub integration | OPERATIONAL |
| **Sales Enablement** | Call sheets, playbooks, battlecards | FULLY OPERATIONAL |
| **Territory Management** | Territory grab, virgin territory analysis | FULLY OPERATIONAL |
| **Email Campaign Support** | Templates, sequences, reactivation lists | OPERATIONAL |
| **Meeting Preparation** | 51 meeting prep files | FULLY OPERATIONAL |

---

## SECTION 7: ACTUAL PROJECT SCOPE

### What This Project Actually Is

**Primary:** Federal Contract BD Intelligence Platform
- Discovers and tracks 1,000-1,400 federal programs
- Enriches with contract data, subawards, task orders
- Scores and prioritizes BD opportunities
- Generates actionable intelligence for sales teams

**Secondary:** CRM Intelligence System (Bullhorn)
- Analyzes 6,000+ contacts and relationships
- Identifies hiring signals and warm leads
- Generates playbooks and battlecards
- Supports territory management and expansion

**Tertiary:** N8N Workflow Orchestration
- 10 active workflows for automation
- Hub-based intelligence management
- Scraper integration and alerting
- Health monitoring

### Recommended Project Rename

**Current:** "N8N Builder"
**Proposed:** "PrimeTech BD Intelligence Platform" or "Federal Contract Intelligence Hub"

---

## SECTION 8: GAPS & RECOMMENDATIONS

### Identified Gaps

| Gap | Impact | Priority |
|-----|--------|----------|
| Missing `client/` layer | No programmatic N8N client | HIGH |
| Missing workflow templates | Inconsistent workflow patterns | MEDIUM |
| Inactive workflows (27) | Clutter, maintenance burden | LOW |
| No monitoring dashboard | Limited visibility | MEDIUM |
| Stale data potential | Intelligence freshness | MEDIUM |

### Recommendations

1. **Rename Project** - Reflect actual capabilities
2. **Create Client Layer** - Programmatic N8N management
3. **Audit Inactive Workflows** - Delete or reactivate
4. **Build Refresh Pipeline** - Automated data updates
5. **Add Monitoring Dashboard** - Execution visibility
6. **Document Data Lineage** - Source-to-output tracking

---

## APPENDIX A: FILE COUNTS BY CATEGORY

| Category | File Count |
|----------|------------|
| Python Scripts (src/) | 100+ |
| External Libraries | 85+ |
| Output CSV Files | 447+ |
| Output XLSX Files | 8 |
| Markdown Reports | 60+ |
| JSON Data Files | 50+ |
| N8N Workflow JSONs | 22 (local) |
| Bullhorn Intelligence | 268 |

## APPENDIX B: API INTEGRATIONS

| API | Endpoint | Rate Limit | Usage |
|-----|----------|------------|-------|
| Tango | makegov.com/api | 100/day/key | Contracts, entities |
| USASpending | api.usaspending.gov | 60/min | Awards, subawards, IDVs |
| SAM.gov | api.sam.gov | Varies | Opportunities, entities |
| N8N Cloud | primetech.app.n8n.cloud | Unlimited | Workflow management |

---

**End of Capability Audit**

*Generated by Claude Code Diagnostic System - 2026-01-26*
