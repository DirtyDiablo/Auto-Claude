# PTS BD Strategy, Methodology & Execution Reference
## Last Updated: February 7, 2026

---

## Company Profile

**Prime Technical Services (PTS)** — Service-Disabled Veteran-Owned Small Business (SDVOSB) specializing in cleared IT staffing for federal defense and intelligence contractors. PTS places contract technical staff with prime contractors (GDIT, Leidos, SAIC, BAE Systems, Northrop Grumman) supporting DoD and IC programs.

**Core Differentiator**: Solution-based BD. PTS arrives with insider knowledge of a program's specific pain points, labor gaps, and staffing challenges — offering tailored solutions instead of cold-calling with generic capabilities.

---

## The 6-Phase BD Execution Cycle

### Phase 1: CONTRACT DISCOVERY
**Goal**: Find federal programs with active staffing needs

**Methods**:
1. **Competitor Job Board Scraping** — Insight Global, Apex Systems, TEKsystems, CACI postings often map to specific federal contracts
2. **Federal Contract Mining** — SAM.gov, FPDS, USASpending via Tango/MakeGov API (NAICS 5415xx IT, 5413xx engineering, >$500K, DoD)
3. **Bullhorn CRM Intelligence** — 2,687 historical notes from PTS account managers reveal contract mentions, hiring patterns, relationship data
4. **Industry Events** — Recompete announcements, option year exercises, organizational changes

**Extract**: Program name, prime/sub chain, contract value, PoP, locations, clearance requirements, typical roles, pain points

### Phase 2: PROGRAM MAPPING
**Goal**: Map generic competitor job postings to specific federal programs

**Mapping Signals (by weight)**:
| Signal | Weight | Rationale |
|---|---|---|
| Location proximity to military installation | 40pts | Strongest signal — geography constrains program assignment |
| Clearance level | 20pts | TS/SCI → IC programs, Secret → tactical programs |
| Skills & technologies | 20pts | ISR, SIGINT, GEOINT, program-specific tools |
| Title pattern match | 10pts | "Intel Analyst" + "ISR" + "Hampton" → AF DCGS Langley |
| Company association | 10pts | Staffing portal posting for known prime |

Score ≥60 = High confidence. Score 40-59 = Medium (needs validation). Score <40 = Low (manual review).

### Phase 3: CONTACT BUILDING
**Goal**: Identify team leads and hiring managers at target programs

**Sources** (preference order):
1. Bullhorn CRM — existing PTS relationships (2,687 notes)
2. ZoomInfo — 275M contacts with direct dials and emails
3. LinkedIn Recruiter — profile verification and relationship building
4. Notion DCGS Contacts — 965+ classified contacts

**6-Tier Contact Hierarchy**:
| Tier | Level | Examples | BD Priority | Use |
|---|---|---|---|---|
| 1 | Executive | VP, President, C-Suite | 🔴 Critical | Strategic alignment, exec-to-exec only |
| 2 | Director | Directors | 🔴 Critical | Portfolio-level partnerships |
| 3 | Program Leadership | PM, Site Lead, Task Order Lead | 🟠 High | Solution pitch, get job reqs |
| 4 | Management | Manager, Team Lead, Supervisor | 🟡 Medium | Validate intel, build coalition |
| 5 | Senior IC | Sr. Engineer, Principal, Architect | ⚪ Standard | Relationship building, technical credibility |
| 6 | Individual Contributor | Analyst, Engineer, Admin | ⚪ Standard | HUMINT gathering, ground truth |

### Phase 4: HUMINT GATHERING
**Goal**: Gather insider intelligence BEFORE approaching decision-makers

**This is what transforms cold calls into warm introductions.**

**Process**:
1. Start with Tier 5-6 contacts — friendly, mission-curious approach ("coffee chat to share insights")
2. Build rapport through genuine interest in their mission and challenges
3. Gather intelligence: team dynamics, actual pain points, hiring manager names, budget cycles, vendor preferences
4. Document all intel in structured notes
5. Validate through Tier 4 contacts (managers)
6. Build complete picture before approaching Tier 3+ decision-makers

**Intelligence Categories**:
- **Operational Pain Points**: What's broken? Understaffed? Single points of failure?
- **Hiring Intelligence**: Who decides? What's the approval process? VMS usage?
- **Budget Intelligence**: Budget cycle timing? Surge funding opportunities?
- **Competitive Intelligence**: Other staffing vendors? Who's falling short?
- **Organizational Intelligence**: Reporting chains, team structures, upcoming reorgs

**Known Pain Points by Program (Feb 2026)**:
| Program / Site | Pain Points |
|---|---|
| **AF DCGS - PACAF** 🔥 | Acting site lead stretched thin, SPOFs, no redundancy, remote from Langley PMO |
| **AF DCGS - Langley** | High ISR volume, analyst burnout, PMO pressure on vacancies, open Sr. Cyber Analyst |
| **AF DCGS - Wright-Patt** | Radar engineer vacancy, DevSecOps shortage, tech modernization delays |
| **Army DCGS-A** | Surge staffing needs, multi-site coordination (Belvoir/Detrick/Aberdeen) |
| **Navy DCGS-N** | Ship/shore integration challenges, Norfolk talent competition |

### Phase 5: PERSONALIZED OUTREACH
**Goal**: Craft outreach demonstrating insider knowledge and offering solutions

**The PTS 6-Step BD Formula** — every outreach follows this sequence:

**Step 1 — Personalized Message**: Role-specific icebreaker showing knowledge of their work
- Reference their specific site, team, or recent activity
- Show understanding of their operational context
- NEVER generic "I saw your profile" openings
- *Example*: "Hi Kingsley, managing the PACAF San Diego node remotely from Langley oversight must come with unique challenges — especially maintaining continuity with a lean team."

**Step 2 — Current Pain Points**: Program-specific challenges from HUMINT
- Reference specific staffing gaps identified
- Show awareness of operational tempo
- *Example*: "I understand the site is operating with minimal redundancy, and the network/security function is running single-threaded."

**Step 3 — Labor Gaps & Open Jobs**: Current vacancies at their location
- Cross-reference Program Mapping Hub for active requisitions
- Match job titles to the contact's team/function
- *Example*: "We're tracking 3 open positions for your site — network engineer, system admin, and field service tech."

**Step 4 — PTS Past Performance with GDIT**: Direct partnership history
- BICES/BICES-X: TS/SCI network engineers & intel analysts (Norfolk, Tampa, Europe)
- GSM-O II: Network engineers for 24/7 DISA global operations
- NATO BICES: Coalition intelligence network analysts
- *Example*: "PTS has placed 12+ TS/SCI network engineers on GDIT's BICES program — same clearance level and similar mission."

**Step 5 — Relevant Past Performance to Program**: Similar program experience
- SOCOM JICCENT → ISR relevance for DCGS
- DIA I2OS → DCGS integration challenges
- Army RS3 → C4ISR/Army intel for DCGS-A
- Platform One → USAF DevSecOps for Wright-Patt
- DISA JRSS → Multi-site network security deployment

**Step 6 — Past Performance Relevant to Job Title**: Role-specific capabilities
- Cyber Analysts → PTS cleared cyber portfolio
- Network Engineers → PTS DISA/coalition network experience
- ISR Analysts → PTS intel community placements
- DevSecOps → PTS Platform One experience

### Phase 6: DECISION-MAKER ENGAGEMENT
**Goal**: Set meetings with PMs to discuss capabilities and get job requisitions

**Outreach Sequencing by Tier**:
| Tier | Channel | Approach | CTA | Follow-up |
|---|---|---|---|---|
| 5-6 ICs | LinkedIn | Friendly, mission-curious | "Coffee chat" | Email |
| 4 Managers | LinkedIn → Email | Collaborative, solution-focused | "30 min staffing solutions call" | Phone + case study |
| 3 PMs/Site Leads | Formal Email | Data-backed, value-driven | "Meet with BD lead + past perf brief" | Exec assistant + events |
| 1-2 Executives | Exec-to-Exec | Strategic, high-level | "15-min strategy sync" | Custom proposal or event |

**14-Day Outreach Cadence**:
| Day | Action | Channel |
|---|---|---|
| 1 | Intro (full BD Formula) | Email |
| 2 | Check reply | — |
| 3 | Follow-up (different angle + case study) | Email |
| 5 | Brief touchpoint | SMS (if phone available) |
| 7 | Case study with specific past perf alignment | Email |
| 14 | Breakup (leave door open, offer value) | Email |

---

## Meeting Execution (The "How To: Meeting Outline")

**Preparation**: Fill out BEFORE the meeting — Name, Title, Company, Pre-Meeting Plan Info

**Pre-Meeting Intel**:
- APPROVED contacts: How are we approved? Who do we work with? What placements have we made?
- UNAPPROVED contacts: Who have we met with? Do we staff similar skill sets? Work with competitors?

**Meeting Structure**:
1. **Intro** — Who PTS is, our story, purpose of meeting, agenda
2. **Team** — What team are they on? Which Division / Line of Business?
3. **Roles/Responsibilities** — Treat like a broad req intake. What does their team do day-to-day?
4. **Tools/Technologies** — What systems are they using?
5. **Organization Breakdown** — Build rough org chart. Who reports to them? Who are the leads? Who decides on hiring?
6. **Upcoming Projects** — Current and future initiatives
7. **Contractors / Full Time** — Team size, offshore presence, outsourcing?
8. **How They Bring People On** — VMS? Can we set up interviews directly?
9. **Current/Upcoming Needs** — ASK FOR BUSINESS. Take the req.
10. **Referrals** — Who else can we introduce ourselves to?
11. **Next Steps** — Build or Drop. Set the next meeting.

---

## Priority Targets (February 2026)

### 🔴 CRITICAL
| Contact | Title | Program | Pain Point | Action |
|---|---|---|---|---|
| Kingsley Ero | Acting Site Lead | AF DCGS - PACAF | Multiple hats, no backup | Call this week |
| Tara Stephenson | Network Analyst | AF DCGS - PACAF | Sole network/security | Call this week |
| Maureen Shamaly | PM/Site Lead | AF DCGS - Langley | Open Sr. Cyber Analyst | Email + call |
| Robert Nicholson | Deputy Site Mgr | AF DCGS - Langley | Supports Shamaly | Follow-up |
| Craig Lindahl | Sr. PM | AF DCGS - Wright-Patt | Radar engineer vacancy | Email intro |

### 🟠 HIGH
| Contact | Title | Location | Approach |
|---|---|---|---|
| David Winkelman | VP, Defense Intelligence | Herndon | Exec-to-exec |
| Christine Carpenter | Network Ops Manager | Falls Church | Direct outreach |
| Julie Coleman | AF Portfolio Director | Falls Church | Strategic alignment |

### 🟡 MEDIUM
| Contact | Title | Program | Action |
|---|---|---|---|
| Jeffrey Bartsch | Ops Manager | Army DCGS-A | Email intro |
| Rebecca Gunning | PM | Army DCGS-A | Follow-up |
| Dusty Galbraith | PM (Norfolk) | Navy DCGS-N | Email intro |
| Jeffrey Schaf | Site Lead (Tracy) | Navy DCGS-N | West coast |

---

## DCGS Organizational Structure

```
GDIT Corporate (Herndon/Falls Church)
├── David Winkelman — VP, Defense Intelligence (oversees all DCGS)
├── Julie Coleman — AF DCGS Portfolio Director
│
├── AF DCGS - Langley (Hampton, VA) — DGS-1, 480th ISR Wing
│   ├── Maureen Shamaly — PM/Site Lead
│   ├── Robert Nicholson — Deputy PM
│   ├── Alfred Boateng, Mindy Boomer, Christine Carpenter — Security/Systems
│   └── Teams: Cyber, Analysts, GRC, Comms Ops
│
├── AF DCGS - Wright-Patterson (Dayton, OH) — NASIC
│   ├── Craig Lindahl — Sr. PM
│   ├── David Crawford — Engineering Lead
│   ├── Jeff Menard — ISR Architecture Lead
│   └── Labor Gaps: Radar Engineer, DevOps, ML Engineers
│
├── AF DCGS - PACAF (San Diego, CA) 🔥
│   ├── Kingsley Ero — Acting Site Lead (functional)
│   ├── Tara Stephenson — Network/Security (sole person)
│   ├── Angelica Madrid, Charles Gateley — Team
│   └── Reports remotely to Langley PMO
│
├── Army DCGS-A
│   ├── Jeffrey Bartsch — Ops Manager (Fort Belvoir)
│   ├── Rebecca Gunning — PM (Fort Detrick)
│   └── Sites: Aberdeen, Belvoir, Fort Detrick
│
└── Navy DCGS-N
    ├── Dusty Galbraith — PM (Norfolk)
    ├── Jeffrey Schaf — Site Lead (Tracy, CA)
    └── Sites: Norfolk, Suffolk, Tracy
```

---

## Success Metrics

| Metric | Target | Measurement |
|---|---|---|
| Contacts classified (DCGS) | 965+ | Notion DCGS Contacts with tier + program + priority |
| HUMINT reports | 1/week | Agent-generated weekly intelligence briefings |
| Active outreach sequences | 25+ | Contacts in 14-day cadence |
| Meetings set (Tier 3+) | 3-5/month | Discovery calls with PMs/Site Leads |
| Job requisitions obtained | 2-3/month | Open reqs from program managers |
| Pipeline value | $950M | DCGS portfolio in active BD |
| Job scrape coverage | 4 portals/week | Automated Apify scrapes |
| Program mapping accuracy | >80% | Jobs correctly matched to programs |
| Contact enrichment rate | >90% | Contacts with email + phone + LinkedIn |
