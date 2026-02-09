# PTS BD Platform — Data Schema Reference
## Last Updated: February 7, 2026

---

## Qdrant Collection Schemas

All collections use OpenAI text-embedding-3-small (1536 dimensions), COSINE distance, INT8 scalar quantization.

---

### contacts (211,267 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "name": "string — Full name",
    "first_name": "string",
    "last_name": "string",
    "title": "string — Job title",
    "company": "string — Employer (GDIT, Leidos, SAIC, BAE, etc.)",
    "email": "string",
    "phone": "string",
    "linkedin_url": "string",
    "program": "string — Assigned program (AF DCGS - Langley, etc.)",
    "tier": "string — Hierarchy tier (Tier 1 - Executive through Tier 6 - Individual Contributor)",
    "priority": "string — BD priority (🔴 Critical / 🟠 High / 🟡 Medium / ⚪ Standard)",
    "location": "string — City, State",
    "location_hub": "string — Location grouping",
    "functional_area": "string — Role function",
    "source": "string — zoominfo / linkedin / bullhorn / manual",
    "source_project": "string",
    "date_indexed": "string — ISO date",
    "search_tags": "string[]",
    "intel_category": "string"
  }
}
```

### programs (68,103 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "program_name": "string",
    "acronym": "string",
    "agency_owner": "string — USAF, Army, Navy, DIA, NRO, NGA, etc.",
    "prime_contractor": "string",
    "known_subcontractors": "string",
    "contract_value": "string — e.g., $500M",
    "contract_vehicle": "string",
    "pop_start": "string",
    "pop_end": "string",
    "key_locations": "string",
    "clearance_requirements": "string — TS/SCI, Secret, etc.",
    "typical_roles": "string",
    "keywords": "string",
    "program_type": "string",
    "pts_involvement": "string — Current / Past / Target / None",
    "priority_level": "string",
    "pain_points": "string",
    "confidence_level": "string — High / Medium / Low",
    "source_project": "string",
    "date_indexed": "string"
  }
}
```

### jobs (15,997 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "title": "string — Job title",
    "company": "string — Posting company / staffing portal",
    "location": "string",
    "clearance": "string",
    "description": "string — Full job description",
    "program_match": "string — Matched federal program",
    "source_portal": "string — Insight Global / Apex / TEKsystems / CACI / GDIT internal",
    "url": "string",
    "scraped_date": "string",
    "skills": "string",
    "experience_level": "string",
    "status": "string — raw_import / enriched / validated / mapped",
    "bd_score": "float — 0-100",
    "source_project": "string",
    "date_indexed": "string"
  }
}
```

### federal_contracts (107,902 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "agency": "string",
    "contractor": "string",
    "naics": "string",
    "value": "string",
    "award_date": "string",
    "status": "string — Active / Completed / Option",
    "description": "string",
    "pop_start": "string",
    "pop_end": "string",
    "source": "string — USASpending / FPDS / SAM.gov / Tango",
    "source_project": "string",
    "date_indexed": "string"
  }
}
```

### documents (499,750 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "title": "string",
    "doc_type": "string — playbook / report / briefing / analysis / reference",
    "content": "string — Text chunk",
    "source_file": "string — Original filename",
    "program_name": "string",
    "intel_category": "string — bd_intelligence / program_intelligence / analysis_report / gap_analysis / competitive_intelligence",
    "priority": "string",
    "search_tags": "string[]",
    "source_project": "string",
    "date_indexed": "string"
  }
}
```

### activities (445,972 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "activity_type": "string — call / email / meeting / note / submission",
    "contact_name": "string",
    "company": "string",
    "author": "string — Note author / salesperson",
    "date": "string",
    "program": "string",
    "summary": "string — Activity text",
    "source_project": "string",
    "date_indexed": "string"
  }
}
```

### bullhorn_notes (50,710 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "contact": "string",
    "company": "string",
    "author": "string — Note author",
    "date": "string",
    "type": "string — Note category",
    "programs_mentioned": "string[]",
    "roles_mentioned": "string[]",
    "locations_mentioned": "string[]",
    "bill_rates": "string[]",
    "headcounts": "string[]",
    "summary": "string",
    "source_project": "string",
    "date_indexed": "string"
  }
}
```

### intelligence_reports (2,229 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "report_type": "string — bd_intelligence / program_intelligence / analysis_report / gap_analysis / hiring_intelligence / subaward_intelligence / humint_briefing / executive_summary / competitive_intelligence",
    "program": "string",
    "date": "string",
    "confidence": "string — High / Medium / Low",
    "source_file": "string",
    "source_project": "string",
    "date_indexed": "string"
  }
}
```

### bd_memories (2 vectors)
```json
{
  "vector": [1536-dim float array],
  "payload": {
    "user_id": "string",
    "agent_id": "string",
    "memory_type": "string",
    "content": "string — Memory text",
    "timestamp": "string"
  }
}
```

---

## Notion Database Schemas

### DCGS Contacts Full
**Collection ID**: `2ccdef65-baa5-8087-a53b-000ba596128e`

| Property | Type | Allowed Values |
|---|---|---|
| Name | Title | Contact full name |
| Program | Select | AF DCGS - Langley, AF DCGS - Wright-Patt, AF DCGS - PACAF, AF DCGS - Other, Army DCGS-A, Navy DCGS-N, Corporate HQ, Enterprise Security, Unassigned |
| Hierarchy Tier | Select | Tier 1 - Executive, Tier 2 - Director, Tier 3 - Program Leadership, Tier 4 - Management, Tier 5 - Senior IC, Tier 6 - Individual Contributor |
| BD Priority | Select | 🔴 Critical, 🟠 High, 🟡 Medium, ⚪ Standard |
| Location Hub | Select | Hampton Roads, San Diego Metro, DC Metro, Dayton/Wright-Patt, Other CONUS, OCONUS, Unknown |
| Functional Area | Multi-Select | Program Management, Network Engineering, Cyber Security, ISR/Intelligence, Systems Administration, Software Engineering, Field Service, Security/FSO, Business Development, Training, Administrative |
| Job Title | Rich Text | Free text |
| Email | Email | |
| Phone | Phone | |
| LinkedIn | URL | |
| Company | Select | |

### Federal Programs
**Collection ID**: `06cd9b22-5d6b-4d37-b0d3-ba99da4971fa`

| Property | Type | Key Values |
|---|---|---|
| Program Name | Title | |
| Acronym | Rich Text | |
| Agency Owner | Select | USAF, Army, Navy, DIA, NRO, NGA, SOCOM, DISA, etc. |
| Prime Contractor | Select | GDIT, Leidos, SAIC, BAE Systems, Northrop Grumman, etc. |
| PTS Involvement | Select | Current, Past, Target, None |
| Priority Level | Select | Critical, High, Medium, Low |
| Contract Value | Rich Text | |
| Pain Points | Rich Text | |

---

## Classification Logic

### Tier Assignment (by job title keywords)
```python
TIER_KEYWORDS = {
    'Tier 1 - Executive': ['vice president', 'vp,', 'vp ', 'president', 'chief ', 'ceo', 'cto', 'cio', 'ciso', 'cfo'],
    'Tier 2 - Director': ['director'],
    'Tier 3 - Program Leadership': ['program manager', 'deputy program', 'site lead', 'task order', 'program director', 'project director'],
    'Tier 4 - Management': ['manager', 'team lead', 'supervisor', 'lead,', 'lead ', 'section chief'],
    'Tier 5 - Senior IC': ['senior ', 'sr.', 'sr ', 'principal', 'lead engineer', 'staff engineer', 'architect'],
    'Tier 6 - Individual Contributor': []  # default fallback
}
```

### Program Assignment (by location)
```python
LOCATION_TO_PROGRAM = {
    'Hampton': 'AF DCGS - Langley', 'Newport News': 'AF DCGS - Langley', 'Langley': 'AF DCGS - Langley',
    'San Diego': 'AF DCGS - PACAF', 'La Mesa': 'AF DCGS - PACAF',
    'Dayton': 'AF DCGS - Wright-Patt', 'Beavercreek': 'AF DCGS - Wright-Patt', 'Fairborn': 'AF DCGS - Wright-Patt',
    'Norfolk': 'Navy DCGS-N', 'Suffolk': 'Navy DCGS-N', 'Chesapeake': 'Navy DCGS-N', 'Virginia Beach': 'Navy DCGS-N',
    'Fort Belvoir': 'Army DCGS-A', 'Fort Detrick': 'Army DCGS-A', 'Aberdeen': 'Army DCGS-A',
    'Herndon': 'Corporate HQ', 'Falls Church': 'Corporate HQ', 'Reston': 'Corporate HQ', 'Fairfax': 'Corporate HQ'
}
```

### BD Priority Assignment
```python
# Tier 1-2 OR PACAF program → 🔴 Critical
# Tier 3 → 🟠 High  
# Tier 4 → 🟡 Medium
# Tier 5-6 → ⚪ Standard
```

---

## Job-to-Program Mapping Score

| Signal | Points | Description |
|---|---|---|
| Location match | 40 | Proximity to military installation |
| Clearance match | 20 | TS/SCI → IC programs, Secret → tactical |
| Skills/keywords | 20 | DCGS-specific: ISR, SIGINT, GEOINT |
| Title pattern | 10 | Role + domain match |
| Company association | 10 | Staffing portal → prime contractor |
| **Threshold** | **≥60** | **High confidence mapping** |
