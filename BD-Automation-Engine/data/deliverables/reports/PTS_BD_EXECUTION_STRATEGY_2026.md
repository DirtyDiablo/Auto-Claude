# PTS BD Execution Strategy — Q1/Q2 2026

**Prepared:** February 20, 2026
**Data Sources:** 8-Engine BD Intelligence Pipeline (Bullhorn CRM, Federal Contracts DB, Knowledge Graph, Apify Scraper, Program Mapping, OrgChart Classification, BD Scoring, QA Alerts)
**Data Freshness:** Pipeline last run 2026-01-23 | Bullhorn ingestion 2026-02-20 | 8,447 indexed vectors

---

## EXECUTIVE SUMMARY

PTS operates an 8-engine AI-powered BD intelligence pipeline tracking **401 federal programs**, **7,339 contacts** (across 24 prime contractors), **1,297 open federal contracts**, and **50,710 call notes**. This strategy converts that intelligence into a repeatable, data-driven cadence that maps buying hierarchies, aligns past performance, and generates meetings.

**Current Revenue Baseline:** 27 deployed contractors generating ~$60K/week spread across NGC (56%), SAIC (28.5%), and others. Total tracked placements: 616 across 41 prime contractors.

**Target Portfolio:** DCGS ecosystem (~$950M) plus adjacent programs totaling $20B+ in addressable contract value across missile defense, space, cyber, and enterprise IT.

---

## PHASE 1: FOUNDATION — DATA-DRIVEN BD CADENCE

### 1.1 Management Approach

Manage through **data and cadence**, not intuition. Every decision backed by engine outputs.

**Core Activity Metrics (tracked in Bullhorn):**

| Metric | Current Baseline | Weekly Target | Source |
|--------|-----------------|---------------|--------|
| Total Call Notes | 50,710 cumulative | 700+/week | Engine 7 ETL |
| Attempted Contacts | 26,010 unique touched | 300+/week | Bullhorn |
| Conversations Held | 29,216 active-status notes | 100+/week | Bullhorn |
| Contacts Added | 3,122 new leads (77%) | 50+/week | Engine 3 Classifier |
| Meetings Set | 186 client visits logged | 10+/week | Bullhorn |
| Hiring Signals Captured | 56 (Feb 20 ingestion) | 15+/week | Engine 6 QA |

**Action Type Breakdown (current state from 50,710 notes):**
- Left Message: 26,095 (51%) — high volume, low conversion signal
- Outbound Call: 12,196 (24%) — core activity
- Prescreen: 9,503 (19%) — candidate pipeline
- Email: 1,179 (2%) — underutilized channel
- Client Visit: 186 (<1%) — **critical gap: need 5x increase**

### 1.2 Leadership Rhythm

| Cadence | Activity | Data Source |
|---------|----------|-------------|
| **Daily** | AM reviews personal Bullhorn dashboard; one win tied to effort | Bullhorn live |
| **Mon/Wed** | Bi-weekly Bullhorn reporting drops | Engine 7 ETL auto-run |
| **Weekly** | Deputy 1:1 — review activity metrics + hiring signals | Engine 6 QA Alert digest |
| **Bi-Weekly** | Program-level pipeline review (top 10 programs by BD score) | Engine 5 Scoring |
| **Monthly** | Full portfolio review: contracts, placements, revenue | Engine 8 Knowledge RAG |

**Escalation Triggers (Red Flags):**
- Hiring signal detected with no follow-up within 48 hours
- Tier 1 contact goes 30+ days without engagement
- Program gap identified (DCGS, NSA, CENTCOM currently flagged)
- Competitor wins placement on tracked program

### 1.3 Self-Management Standard

- One daily win tied to **effort** (calls made, contacts mapped, intel gathered)
- Trust the process — results follow **volume + quality**
- Weekly self-score: Activity Score = (Calls × 1) + (Conversations × 3) + (Meetings × 10) + (Hiring Signals × 5)

---

## PHASE 2: MARKET INTELLIGENCE COLLECTION

### 2.1 Recruiter-Style Conversation Framework

Each AM conducts **5+ recruiter-style conversations per target account daily** to gather:

| Intel Category | What to Capture | Engine That Processes It |
|----------------|-----------------|------------------------|
| Competition | Who else is staffing? Subcontractor names | Engine 2 (Program Mapper) |
| Locations | Work sites, SCIF locations, remote/hybrid | Engine 3 (OrgChart) |
| Skillsets | Required certs, tools, clearance levels | Engine 1 (Scraper) + Engine 8 (RAG) |
| Clearance Levels | TS/SCI, CI Poly, Full Scope (see breakdown below) | Engine 5 (Scoring) |
| Hiring Managers | Name, title, direct line, email | Engine 3 (6-Tier Classifier) |
| Team Size | Current headcount, growth projections | Engine 7 (Bullhorn Notes) |
| Onsite vs Remote | Work arrangement by program | Engine 8 (Knowledge) |
| Hiring Schedule | Intake timing, start dates, urgency | Engine 6 (QA Alerts) |
| Compensation | Bill rates, pay ranges, loaded rates | Engine 7 (Bullhorn) |

**Clearance Demand Signal (from 50,710 call notes):**

| Clearance Level | Mentions | % of Notes | Demand Signal |
|-----------------|----------|-----------|---------------|
| TS/SCI | 3,857 | 7.6% | **Very High** |
| Secret | 2,657 | 5.2% | High |
| Polygraph (general) | 975 | 1.9% | High |
| CI Poly | 382 | 0.8% | Medium |
| Top Secret (standalone) | 380 | 0.7% | Medium |
| Full Scope Poly | 46 | 0.1% | Niche/Premium |

**Outcome:** Every conversation feeds structured data into the pipeline. Not just contacts — **actionable hiring intelligence** with manager names, project names, headcount, and timelines.

### 2.2 Geographic Intelligence Priorities

Our call notes reveal clear geographic clusters. Focus intelligence collection by location:

| Location Cluster | Mentions | Key Programs | Priority |
|-----------------|----------|-------------|----------|
| AFB (multiple) | 1,144 | DCGS, Space, Cyber | **Critical** |
| Japan (OCONUS) | 726 | Pacific ISR, Indo-PACOM | High |
| Korea (OCONUS) | 688 | Pacific ISR, USFK | High |
| Fort Meade, MD | 793 (668+125) | NSA, CYBERCOM, DIA | **Critical** |
| Colorado Springs, CO | 342 | Space Force, MDA, SDA, NORAD | **Critical** |
| MacDill/Tampa, FL | 239 (139+100) | SOCOM, CENTCOM | High |
| San Antonio, TX | 135 | 16th AF, AFCYBER, NSA-TX | High |
| Germany (OCONUS) | 112 | EUCOM, AFRICOM | Medium |
| Huntsville, AL | Active | IBCS, NASA, SLS, MDA | **Critical** |
| St. Louis, MO | Active | Boeing (JDAM, SDB, Weapons) | High |

### 2.3 Most In-Demand Roles (from Bullhorn Analysis)

| Role Category | Demand Level | Key Programs | Typical Clearance |
|---------------|-------------|-------------|-------------------|
| Systems Engineer | **Very High** | IBCS, Aegis, DCGS, Sentinel | TS/SCI |
| Software Engineer | **Very High** | All programs | TS/SCI |
| Program Manager | **High** | All programs | TS/SCI w/ Poly |
| Intelligence Analyst | **High** | DCGS, NSA, DIA | TS/SCI w/ CI Poly |
| Cybersecurity Engineer | **High** | ARCYBER, CYBERCOM | TS/SCI |
| Integration Engineer | **Medium-High** | IBCS, Aegis, MDA | TS/SCI |
| MBSE/Model-Based Engineer | **Medium** | Sentinel, GBSD, NGC | Secret+ |
| Field Service Engineer | **Medium** | SAIC programs | Secret |
| Data Scientist | **Growing** | AI/ML programs | TS/SCI |
| DevSecOps Engineer | **Growing** | Modernization programs | TS/SCI |

---

## PHASE 3: BUYING HIERARCHY MAPPING

### 3.1 Contact Tier Classification System

Our Engine 3 OrgChart Classifier assigns all contacts to a 6-tier hierarchy. Current state across **7,339 contacts**:

| Tier | Role | Count | % | BD Action |
|------|------|-------|---|-----------|
| **Tier 1** | Executive Sponsor / Decision Maker | 388 | 5.3% | Executive engagement, strategic meetings |
| **Tier 2** | Senior Decision Maker | 1 | <0.1% | **DATA GAP — need enrichment** |
| **Tier 3** | Influencer / Program Lead | 284 | 3.9% | Relationship building, program intel |
| **Tier 4** | Resource Manager / Hiring Manager | 377 | 5.1% | Direct hiring conversations |
| **Tier 5** | Gatekeeper / Coordinator | 347 | 4.7% | Access path to Tier 1-4 |
| **Tier 6** | Individual Contributor / Candidate | 1,076 | 14.6% | Intel source, referral network |
| **Unclassified** | Not yet tiered | ~4,866 | 66.3% | **Priority: classify remaining contacts** |

**Target:** Build minimum **30-contact map per account** covering all tiers:

```
PER ACCOUNT TARGET MAP:
├── 2-3 Executive Sponsors (Tier 1)
├── 3-5 Decision Makers (Tier 1-2)
├── 5-8 Influencers / Program Leads (Tier 3)
├── 5-8 Hiring Managers (Tier 4)
├── 5-8 Gatekeepers (Tier 5)
└── 5-10 Key ICs / Referral Sources (Tier 6)
```

### 3.2 Prime Contractor Contact Coverage

**Strategic Accounts (sorted by engagement volume from 50,710 call notes):**

| Rank | Prime | Call Notes | Unique Contacts | Placements | Revenue Status | Coverage |
|------|-------|-----------|-----------------|-----------|----------------|----------|
| 1 | **CACI** | 4,846 | 500+ | 3 | Growing | Good intel, low placement |
| 2 | **GDIT** | 2,380 | 121 | 111 | **Strategic** | Strong |
| 3 | **Lockheed Martin** | 1,531 (1,147+280+104) | 108+ | Active | Growing | Moderate |
| 4 | **Leidos** | 931 | 209 | **209** | **#1 Revenue** | **Strongest** |
| 5 | **AWS** | 728 | 50+ | Active | Emerging | Developing |
| 6 | **Palantir** | 441 | 40+ | Active | Niche | Developing |
| 7 | **Raytheon/RTX** | 405 (349+56) | 30+ | Active | Growing | Moderate |
| 8 | **SAIC** | 327 | 49 | 8+ | Revenue (28.5% spread) | Moderate |
| 9 | **Northrop Grumman** | 498 (262+236) | 103 | **15** | **Revenue (56% spread)** | Strong |
| 10 | **BAE Systems** | 254 (188+66) | 35 | Active | Growing | Developing |
| 11 | **Peraton** | 226 (124+102) | 72 | **72** | **#3 Revenue** | Strong |
| 12 | **Boeing** | 71 | 47 | 13 | Established | Moderate |
| 13 | **Booz Allen** | 104 | 30+ | Active | Developing | Low |
| 14 | **Microsoft** | 108 | 60 | 61 | Established | Strong |
| 15 | **Deloitte** | 141 | 61 | Active | Growing | Moderate |

### 3.3 Key Decision Makers by Program (from Referral Network + Bullhorn)

| Contact | Title/Role | Prime | Program | Action Required |
|---------|-----------|-------|---------|-----------------|
| Rob Whitt | Deputy PM | NGC | JTAGS | Follow up — 15 new heads in 2026 |
| John Bagby | Program Director | SAIC | IBCS | **Retiring soon — critical transition** |
| Casey Thompson | Director | Boeing | SLS | SLS exclusive relationship |
| Tonya Barefoot | Manager | GDIT | MAINES | Active hiring manager |
| Brian Feix | Contact | NGC/inSITE | Various | Hiring authority |
| Lauree Swihart | DAF CW | DAF | Various | DAF-wide influence |
| Reggie White | Contact | — | SOFA | 130-200 position expansion |
| Amy Brown | Key Contact | General Dynamics | Multiple | 42 interactions — highest engagement |
| Mark Trudel | Key Contact | General Dynamics | Multiple | 39 interactions |
| Joel Stammen | Key Contact | General Dynamics | Multiple | 35 interactions |

---

## PHASE 4: PRIME PAST PERFORMANCE ALIGNMENT

### 4.1 Current Placement Performance by Prime

Our Bullhorn data shows **616 total placements** with clear performance tiers:

| Prime | Placements | Jobs Posted | Relationship Tier | Past Performance Strength |
|-------|-----------|------------|-------------------|--------------------------|
| **Leidos** | 209 | 135 | Strategic | **Strongest** — 42 active programs |
| **GDIT** | 111 (+ 12 GD-MS) | 0 | Strategic | Strong — 35+ programs |
| **Peraton** | 72 | 0 | Strategic | Growing — ARCYBER, DISA |
| **Microsoft** | 61 | 0 | Established | Strong — niche enterprise |
| **Dell Federal** | 31 | 0 | Established | Historical |
| **Boeing** | 13 | 0 | Established | Moderate — SLS, weapons |
| **NGC** | 15 | Active | Revenue | Strong — IBCS, JTAGS, Sentinel |
| **SAIC** | 8 | Active | Revenue | Growing — IBCS, AESD |
| **CACI** | 3 | Active | Developing | **Gap vs. engagement volume** |

**Critical Insight:** CACI has 4,846 call note mentions but only 3 placements. This is either a massive untapped opportunity or a conversion problem that needs diagnosis.

### 4.2 High-Value Contract Opportunities (from FINAL_OPEN_CONTRACTS_ENRICHED)

**Top contracts by value with active BD scoring:**

| Contract (PIID) | Program | Prime | Value | BD Score | Status |
|----------------|---------|-------|-------|----------|--------|
| SAQMMA11F0233 | Leidos PMO | Leidos | $2.09B | 68 | WARM |
| 75N91020F00003 | NCI Operational TO | Leidos Biomed | $1.78B | 65 | WARM |
| 28321322FDS030130 | ITSSC Task Order | Leidos | $1.06B | 62 | WARM |
| 47QFCA19F0006 | IGF::OT | CACI Federal | $921M | **83** | **HOT** |
| 47QFCA21F0051 | C5ISR Task Order | General Dynamics | $805M | 77 | WARM |
| — | ARCYBER Info Advantage | Peraton | $889M | Active | Target |
| — | Aegis BMD | Lockheed Martin | $45B+ | Active | Target |
| — | Sentinel GBSD | Northrop Grumman | $2.7B | Active | Target |
| — | DES (DoDNet) | Leidos | $11.5B | Active | Target |
| — | ITES-3S | 135 awardees | $12.1B | Active | Target |
| — | Army AESD | SAIC | $757M | Active | Target |
| — | DTRA I3TS | Leidos | $205M | Active | 315 placements |

### 4.3 Growth Programs (Expansion Signals from Bullhorn Notes)

| Program | Prime | Growth Signal | Headcount Target | Action |
|---------|-------|--------------|-----------------|--------|
| **BOA** | NGC | 6x workload increase | TBD | Aggressive staffing push |
| **JTAGS** | NGC | +15 heads confirmed | 15 in 2026 | Rob Whitt engagement |
| **Munitions** | Various | +100 positions | 100 | Scale team |
| **SLS** | Boeing | Exclusive relationship | 20-50 contractors | Casey Thompson |
| **SOFA** | Various | Major expansion | 130-200 positions | Reggie White |
| **IBCS** | SAIC/NGC | Program Director retiring | Transition | John Bagby succession |

---

## PHASE 5: COLD OUTREACH EXECUTION

### 5.1 Call Prioritization Algorithm

Use Engine 5 BD Scoring (0-100 scale) to prioritize outreach:

**Scoring Methodology:**
```
BD Score = Activity Weight (30 max)
         + Placement Success (20 max)
         + Recency (15 max)
         + Prime Diversity (7 max)
         + Status Multiplier (5 max)
         + Program Value (23 max)
```

**Current Score Distribution:**
- Score 70-100: **HOT** — immediate engagement (CACI Federal contract at 83)
- Score 50-69: **WARM** — active pursuit (majority of $500M+ contracts)
- Score 36-49: **PROSPECT** — nurture and develop
- Score 0-35: **COLD** — low priority / monitoring only

### 5.2 Daily Outreach Cadence

**Per AM Daily Minimum:**

| Block | Time | Activity | Target |
|-------|------|----------|--------|
| **Morning** | 8:00-10:00 | Cold calls — Tier 4-5 contacts (hiring managers, gatekeepers) | 15 dials |
| **Mid-Morning** | 10:00-11:30 | Follow-up conversations with active leads | 5 conversations |
| **Lunch Intel** | 11:30-12:30 | Review Engine 6 alerts + hiring signals | Process signals |
| **Afternoon** | 1:00-3:00 | Cold calls — Tier 1-3 contacts (decision makers) | 10 dials |
| **Late PM** | 3:00-4:30 | Email sequences + LinkedIn outreach | 10 touches |
| **EOD** | 4:30-5:00 | Bullhorn notes entry + next-day prep | Log all activity |

**Primary Goal per call:**
1. **Set the meeting** — get a face-to-face or video call scheduled
2. **Confirm follow-up email** — permission to send capability brief
3. **Gather one intel point** — hiring signal, program update, competition info

### 5.3 Gap Program Attack Plan

Engine 6 QA identified **3 critical gap programs** with high negative traction:

| Gap Program | Issue | Current Contacts | Strategy |
|-------------|-------|-----------------|----------|
| **DCGS** | Low positive response ratio | 71 mentions, 3 key contacts (Sean Gage, Linda Nichols, Andrew Torelli @ GDIT) | Pivot approach — enter through GDIT sub relationship; use past DCGS analyst placements as credibility |
| **NSA** | Low positive response ratio | 302 mentions (Fort Meade heavy) | Shift to Tier 6 referral strategy — use IC-cleared ICs to intro to hiring managers |
| **CENTCOM** | Low positive response ratio | 39 mentions (MacDill/Tampa) | SOCOM adjacency play — leverage SOFA expansion (130-200 positions) for CENTCOM crossover |

### 5.4 Warm Account Acceleration

**Accounts with existing placement revenue (protect + grow):**

| Account | Current Spread | Weekly Revenue | Growth Play |
|---------|---------------|---------------|-------------|
| NGC | 15 placements | $33.6K/week (56%) | BOA 6x, JTAGS +15, Sentinel |
| SAIC | 8 placements | $17.1K/week (28.5%) | IBCS transition, AESD |
| Leidos | 209 placements | Major revenue | I3TS (315 heads), DES ($11.5B), NGEN-R |
| GDIT | 111 placements | Major revenue | MAINES, Justified, DCGS sub |
| Peraton | 72 placements | Growing | ARCYBER ($889M), DISA |
| Boeing | 13 placements | Steady | SLS exclusive (20-50), Weapons |

---

## PHASE 6: SCALABLE PROCESS ("COOKIE CUTTER" PLAYBOOK)

### 6.1 Standardized Deputy Workflow

**Week 1-2 (per new account):**
1. Pull Engine 2 program mapping for account → identify all federal programs
2. Pull Engine 3 contact classification → get 30+ contact hierarchy map
3. Pull Engine 5 BD scoring → prioritize contacts by score
4. Generate Engine 4 playbooks → auto-create call scripts, talking points, briefings

**Already Generated Playbook Library:**
- AF DCGS Intelligence Analyst (CallScript + Playbook + TalkingPoints)
- DCGS Senior Systems Engineer (Briefing + CallScript + Playbook + TalkingPoints)
- DCGS Senior Network Engineer (CallScript + Playbook + TalkingPoints)
- NGI DevSecOps Engineer (CallScript + Playbook + TalkingPoints)
- NSA Intelligence Analyst (Briefing)
- Corporate HQ Software Developer (Full suite)
- Plus generic: Systems Engineer, Software Developer, Data Analyst templates

**Week 3-4:**
5. Execute cold outreach cadence (Section 5.2)
6. Log all intel to Bullhorn → auto-ingested by Engine 7 ETL
7. Engine 6 QA flags anomalies and hiring signals
8. Engine 8 Knowledge system updates RAG corpus for team queries

### 6.2 Reporting Cadence (Emotionless, Data-Driven)

**2x per week activity reporting (Monday + Wednesday):**

```
DEPUTY ACTIVITY REPORT
─────────────────────
Calls Made:        ___  (target: 125/week)
Conversations:     ___  (target: 50/week)
Contacts Added:    ___  (target: 25/week)
Meetings Set:      ___  (target: 5/week)
Hiring Signals:    ___  (target: 7/week)
Intel Points:      ___  (any new program/competition/headcount data)
Bullhorn Notes:    ___  (should equal calls + conversations)
─────────────────────
Weekly BD Score:   ___  (auto-calculated by Engine 5)
```

**No subjective commentary.** Numbers speak. Identify account gaps that generate new hiring demand.

---

## PHASE 7: TEAM ASSIGNMENTS & PROGRAM COVERAGE

### 7.1 Current Team-to-Program Matrix (141 assignments across 24+ AMs)

| AM | Programs Assigned | Top Program | Coverage Level |
|----|------------------|-------------|---------------|
| Colin | 5 programs | NGEN-R, DES | Full |
| Justin | 7 programs | I3TS, Cloud One | Full |
| Logan | 7 programs | MCEN, Warhawk | Full |
| Gullette | 6 programs | ARCYBER, Sentinel | Full |
| Steph | 6 programs | BOA, JTAGS | Full |
| Andres | 6 programs | IBCS, MQ-25 | Full |
| Kevin | 3 programs | GBSD, SLS | Moderate |
| Capelluto | 4 programs | Various | Moderate |
| Hoppe | 3 programs | Various | Moderate |
| Trevor | 5 programs | Various | Full |
| + 14 more | Various | — | Varies |

### 7.2 BD Team Performance (43 total authors in Bullhorn)

**Top 10 by Note Volume (proxy for activity):**

| Rank | Author | Notes | Role Focus |
|------|--------|-------|-----------|
| 1 | Colton Scurry | 401 | Account lead — Leidos, GD, NGC |
| 2 | Matt Capelluto | 264 | Multi-account |
| 3 | Jesse Kane | 258 | Multi-account |
| 4 | Logan Hornback | 258 | MCEN, Warhawk focus |
| 5 | Tyler Holmes | 245 | Multi-account |
| 6 | Matt Gullette | 205 | ARCYBER, Sentinel |
| 7 | Kevin Testerman | 183 | GBSD, SLS |
| 8 | Mike Huerkamp | 154 | Multi-account |
| 9 | Trevor Newell | 119 | Multi-account |
| 10 | Justin Howard | 87 | I3TS, Cloud One |

**Recent Ingestion (Feb 20, 2026 — 833 new notes):**
- Trevor Watson: 123 new notes
- Clay Failor: 193 new notes (highest recent activity)
- George Maranville: 101 new notes
- Will Apple: 94 new notes
- Ethan Dial: 59 new notes

---

## PHASE 8: INTELLIGENCE AUTOMATION (AI-POWERED)

### 8.1 Engine Pipeline Summary

| Engine | Function | Status | Automation Level |
|--------|----------|--------|-----------------|
| **Engine 1** | Apify Job Scraper | ✅ Active | Scheduled scrapes (968 jobs, 606 open) |
| **Engine 2** | Program Mapping | ✅ Complete | Auto-maps jobs → 401 programs |
| **Engine 3** | OrgChart Classification | ✅ Complete | 6-tier hierarchy, 24 prime coverage |
| **Engine 4** | BD Playbook Generator | ✅ Complete | Auto-generates scripts, playbooks, briefs |
| **Engine 5** | BD Priority Scoring | ✅ Complete | 0-100 scoring algorithm |
| **Engine 6** | QA & Alerts | 🔄 In Progress | Hiring signal detection, gap alerts |
| **Engine 7** | Bullhorn ETL | ✅ Complete | 293 MB CRM extraction, 50,710 notes |
| **Engine 8** | AI Knowledge System | ✅ Complete | 8,447 vectors, semantic search, RAG |

### 8.2 Automated Intelligence Queries

**Available via Engine 8 MCP Tools (real-time):**

| Query Type | Tool | Example |
|------------|------|---------|
| Contact Search | `search_knowledge` | "Find Tier 1 contacts at Leidos working on DCGS" |
| RAG Q&A | `ask_knowledge` | "What programs does NGC prime with TS/SCI clearance?" |
| Program Intel | `get_program_intel` | Full program report: contract value, primes, locations, clearance |
| Company Contacts | `get_company_contacts` | All contacts at a specific prime with tier info |
| Competitor Analysis | n8n webhook | Parallel competitor analysis with memory recording |
| BD Pipeline | n8n webhook | Full intelligence → scrape → strategy pipeline |

### 8.3 Deliverables Already Generated

| Deliverable Type | Count | Location |
|-----------------|-------|----------|
| Call Scripts | 10+ | `data/deliverables/briefings/*_CallScript.md` |
| Playbooks | 10+ | `data/deliverables/briefings/*_Playbook.md` |
| Talking Points | 10+ | `data/deliverables/briefings/*_TalkingPoints.md` |
| Program Briefings | 5+ | `data/deliverables/briefings/*_Briefing.md` |
| Call Lists | 7 files | `data/deliverables/call_lists/` (AM lists, BD sheet, GDIT sheet) |
| Open Contracts | 1,297 records | `data/deliverables/FINAL_OPEN_CONTRACTS_ENRICHED.csv` |
| Team Assignments | 141 assignments | `data/deliverables/FINAL_TEAM_ASSIGNMENTS.csv` |
| Contact Cheat Sheet | Master file | `data/deliverables/call_lists/MASTER_CONTACTS_CHEAT_SHEET.xlsx` |

---

## PHASE 9: PRIORITY TARGET LIST (TOP 20 OPPORTUNITIES)

Based on cross-referencing BD Scores, contract values, placement history, growth signals, and hiring intelligence:

| Priority | Program | Prime | Contract Value | Growth Signal | Current Coverage | Next Action |
|----------|---------|-------|---------------|--------------|-----------------|-------------|
| 1 | **IBCS** | NGC/SAIC | $2.7B | Program Director retiring; 57 mentions | Strong (Steph/Andres) | Succession relationship building |
| 2 | **SLS** | Boeing | Multi-B | Exclusive; 20-50 contractors, 15 in 2026 | Moderate (Kevin) | Casey Thompson — scale placements |
| 3 | **BOA** | NGC | Large | **6x workload increase** | Moderate (Steph) | Aggressive staffing push |
| 4 | **JTAGS** | NGC | Large | +15 confirmed heads 2026 | Moderate | Rob Whitt — immediate engagement |
| 5 | **SOFA** | Various | Large | **130-200 position expansion** | Low | Reggie White — first meeting |
| 6 | **Sentinel/GBSD** | NGC | $2.7B | 31 mentions, active hiring | Full (Gullette/Kevin) | Maintain + expand |
| 7 | **DCGS** (Gap) | BAE/GDIT | $950M | Target portfolio; 71 mentions | **Gap — needs strategy pivot** | Enter through GDIT sub channel |
| 8 | **ARCYBER** | Peraton | $889M | Growing cyber demand | Full (Gullette) | Scale placements |
| 9 | **Aegis BMD** | Lockheed Martin | $45B+ | 19 mentions, 22 Aegis ingestion notes | Moderate | Deepen LM relationship |
| 10 | **DES (DoDNet)** | Leidos | $11.5B | Enterprise IT modernization | Strong (Colin) | Expand staffing volume |
| 11 | **NGEN-R SMIT** | Leidos | Multi-B | Navy enterprise, active | Full (Colin) | Protect + grow |
| 12 | **I3TS** | Leidos | $205M | 315 placements — proven | Full (Justin) | Maintain dominance |
| 13 | **CACI Federal** | CACI | $921M | BD Score **83** — highest scored | **Critical gap:** 4,846 notes → 3 placements | Conversion strategy needed |
| 14 | **Munitions** | Various | Large | +100 positions signal | TBD | Assign AM |
| 15 | **MCEN** | Various | Large | 9 ingestion mentions | Full (Logan) | Continue coverage |
| 16 | **GSMO** | Various | Large | 16 ingestion mentions | Active | Expand |
| 17 | **ITES-3S** | 135 awardees | $12.1B | Army-wide vehicle | Developing | Multiple entry points |
| 18 | **NASA** | Various | Large | 34 mentions, Huntsville | Active | Focus Huntsville team |
| 19 | **NSA Programs** (Gap) | Various | Large | 302 mentions — negative traction | **Gap** | Referral strategy shift |
| 20 | **Space Force / SDA** | NGC/others | Growing | 29+14 mentions | Active | Colorado Springs focus |

---

## PHASE 10: SUCCESS METRICS & MILESTONES

### 10.1 30-Day Targets (by March 22, 2026)

| Metric | Target | Measurement |
|--------|--------|-------------|
| New contacts mapped | +150 (Tier 1-4) | Engine 3 classifier |
| Hiring signals captured | 60+ | Engine 6 QA |
| Meetings set | 20+ | Bullhorn |
| Gap programs addressed | All 3 (DCGS, NSA, CENTCOM) | Strategy pivot executed |
| New placements | 5+ | Bullhorn |
| Unclassified contacts tiered | 1,000+ (of 4,866) | Engine 3 batch run |

### 10.2 60-Day Targets (by April 22, 2026)

| Metric | Target | Measurement |
|--------|--------|-------------|
| CACI conversion | 5+ placements (from 3) | Revenue tracking |
| Revenue growth | +$15K/week spread | Bullhorn financials |
| Growth program placements | 10+ across BOA/JTAGS/SOFA/SLS | Bullhorn |
| Account maps completed | 15 accounts at 30+ contacts | Engine 3 |
| Playbooks generated | 20+ program-specific | Engine 4 |

### 10.3 90-Day Targets (by May 22, 2026)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Total weekly spread | $90K+/week (50% increase) | Bullhorn |
| Deployed contractors | 40+ (from 27) | Bullhorn |
| DCGS portfolio penetration | 3+ placements | Revenue tracking |
| Knowledge base growth | 12,000+ vectors (from 8,447) | Engine 8 |
| Pipeline value | $5M+ in qualified opportunities | BD scoring |

---

## APPENDIX A: DATA SOURCES REFERENCE

| Data Source | Records | Last Updated | Location |
|-------------|---------|-------------|----------|
| Bullhorn CRM (master) | 50,710 notes | 2026-02-20 | Engine7/bullhorn_master.db |
| Federal Programs | 401 | 2026-01-23 | Engine2/Federal_Programs*.csv |
| Contacts (classified) | 7,339 | 2026-01-23 | data/dashboard/contacts_classified.json |
| Open Contracts | 1,297 | 2026-01-23 | data/deliverables/FINAL_OPEN_CONTRACTS_ENRICHED.csv |
| Knowledge Vectors | 8,447 | 2026-01-28 | Engine8/data/qdrant/ |
| Team Assignments | 141 | 2026-01-23 | data/deliverables/FINAL_TEAM_ASSIGNMENTS.csv |
| Past Performance | 205 | 2026-01-23 | data/dashboard/past_performance.json |
| Placements | 616 | 2026-01-23 | data/dashboard/placements.json |
| BD Call Sheet | Active | 2026-01-19 | data/deliverables/call_lists/ |
| Scurry Analysis | 4,872 notes | 2026-02-16 | data/bullhorn_analysis/ |
| Warm Greenfield | 1,297 contracts | Active | WARM_GREENFIELD_ENRICHED.csv |
| Referral Network | 100 contacts, 150 edges | Active | data/dashboard/referral_network.json |

## APPENDIX B: COMPETITIVE INTELLIGENCE SNAPSHOT

**Top primes by PTS engagement (call notes) vs. placement conversion:**

| Prime | Engagement (Notes) | Placements | Conversion Signal | Strategy |
|-------|-------------------|-----------|-------------------|----------|
| CACI | 4,846 | 3 | **0.06%** — Severely under-converting | Diagnose: wrong contacts? wrong roles? pricing? |
| GDIT | 2,380 | 111 | 4.7% — Strong | Protect and expand |
| Lockheed Martin | 1,531 | Active | Moderate | Deepen through Aegis, F-35, DCGS |
| Leidos | 931 | 209 | **22.4%** — Best conversion | Maximize: this is the model to replicate |
| AWS | 728 | Active | Emerging | Cloud/enterprise play |
| NGC | 498 | 15 | 3.0% — Good | Scale via BOA/JTAGS/Sentinel growth |
| Raytheon | 405 | Active | Moderate | Missile defense adjacency |
| SAIC | 327 | 8 | 2.4% — Growing | IBCS transition opportunity |
| Peraton | 226 | 72 | **31.9%** — Excellent | Second best conversion — invest more here |

**Key Insight:** Leidos (22.4%) and Peraton (31.9%) have the best call-to-placement conversion rates. The CACI account (0.06%) needs immediate diagnostic review — 4,846 touches with 3 placements suggests systemic issues in the approach.

---

*This strategy is auto-generated from PTS BD Intelligence Pipeline data and should be reviewed weekly against live Bullhorn metrics. All data points are queryable via Engine 8 Knowledge System (`search_knowledge`, `ask_knowledge`) and refreshed via Engine 7 ETL pipeline.*

*Next refresh: Run `python Engine7_BullhornETL/scripts/etl_pipeline.py` + `python Engine8_Knowledge/scripts/indexer.py` to update all vectors.*
