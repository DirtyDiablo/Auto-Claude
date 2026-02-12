# MASTER PROPERTY ARCHITECTURE SCHEMA
## BD-Automation-Engine Neo4j Graph Database Design

**Generated:** 2026-02-11
**Source:** Comprehensive column-level audit across all data files
**Total Data Scanned:** 8,447+ indexed vectors, 897K+ database rows, 400+ CSV/JSON files
**Purpose:** Unified schema for Neo4j knowledge graph migration

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Node Type Definitions](#node-type-definitions)
3. [Relationship Definitions](#relationship-definitions)
4. [Property Mappings](#property-mappings)
5. [Standardization Rules](#standardization-rules)
6. [Data Migration Guide](#data-migration-guide)

---

## OVERVIEW

This schema defines 20 primary node types and 35+ relationship types for the BD-Automation-Engine knowledge graph. All properties are derived from actual column headers found across:

- **Engine1-4:** Job scraping, program mapping, contact classification, playbook generation
- **Engine5-8:** BD scoring, QA, Bullhorn CRM (293 MB), AI knowledge system (8,447 vectors)
- **Dashboard:** 25 JSON visualization files
- **Outputs:** 130+ pipeline output files
- **N8N Analytics:** 20+ analytical output files

### Data Volume Summary

| Entity Type | Record Count | Primary Source |
|-------------|--------------|----------------|
| Contacts | 7,339 | Engine3 + Bullhorn candidates (426K historical) |
| Programs | 401 | Engine2 Federal Programs MASTER ENRICHED |
| Jobs | 531 | Engine1 + All Jobs Fully Enriched |
| Contractors | 500+ | Engine2 + Bullhorn prime_contractors |
| Call Notes | 50,710 | Bullhorn call_notes |
| Placements | 616 | Bullhorn placements |
| Contracts | 100,000+ | FPDS/Tango data |
| Activities | 404,715 | Bullhorn activities |

---

## NODE TYPE DEFINITIONS

### 1. CONTACT (Person)

**Description:** Individual contacts in the BD pipeline (employees, decision-makers, hiring managers)

**Primary Keys:**
- `contact_id` (UUID or Bullhorn ID)
- `email` (unique constraint)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| contact_id | String | id, bullhorn_candidate_id | No | Primary |
| first_name | String | first_name, First Name | Yes | Yes |
| last_name | String | last_name, Last Name | Yes | Yes |
| full_name | String | name, full_name, Name | No | Yes |
| email | String | email, Email Address | Yes | Unique |
| phone | String | phone, Direct Phone Number | Yes | No |
| mobile | String | mobile, Mobile phone | Yes | No |
| linkedin_url | String | linkedin_url, LinkedIn Contact Profile URL | Yes | No |
| job_title | String | job_title, Job Title, title, Primary Title | Yes | Yes |
| all_titles | String[] | All Titles (pipe-separated) | Yes | No |
| current_employer | String | company_name, Company Name, current_employer | Yes | Yes |
| city | String | city, Person City | Yes | No |
| state | String | state, Person State | Yes | No |
| address | String | address | Yes | No |
| zip_code | String | zip_code | Yes | No |
| clearance_level | String | clearance_level, Clearances | Yes | Yes |
| tier | Integer | tier, Hierarchy Tier (1-6) | Yes | Yes |
| contact_type | String | Contact Type (client, internal, vendor) | Yes | No |
| relationship_score | Integer | Relationship Score, engagement_score | Yes | No |
| is_hiring_manager | Boolean | Is Hiring Manager | Yes | No |
| has_open_reqs | Boolean | Has Open Reqs | Yes | No |
| is_decision_maker | Boolean | Is Decision Maker | Yes | No |
| note_count | Integer | note_count, Note Count | Yes | No |
| last_activity_date | DateTime | last_activity_date, Last Activity | Yes | Yes |
| first_activity_date | DateTime | first_activity, First Activity | Yes | No |
| status | String | status, Statuses (Active, New Lead, etc.) | Yes | No |
| bd_priority | String | BD Priority | Yes | No |
| occupation | String | occupation | Yes | No |
| owner | String | owner, Authors | Yes | No |
| hiring_signals | String | Hiring Signals (free text) | Yes | No |
| pain_points | String | Pain Points (free text, multi-line) | Yes | No |
| recent_note | String | Recent Note (500+ chars) | Yes | No |
| source_file | String | source_file | Yes | No |
| date_added | DateTime | date_added, Date | Yes | No |
| date_modified | DateTime | date_modified, updated_at | Yes | No |
| created_at | DateTime | created_at | Yes | No |
| updated_at | DateTime | updated_at | Yes | No |

**Source Files:**
- `Engine3_OrgChart/data/Prime_Contacts_Enriched/*.csv` (45 files, 7,339 contacts)
- `Engine7_BullhornETL/data/bullhorn_master.db` → candidates table (426,565 rows)
- `dashboard/public/data/contacts_classified.json` (7,339 contacts)
- `outputs/bd_dashboard/contacts_classified.json`

**Classification Notes:**
- **Tier 1:** Key Decision Makers (executives, VPs, directors)
- **Tier 2:** Managers (program managers, site leads)
- **Tier 3:** Senior ICs (senior engineers, architects)
- **Tier 4:** Mid-level ICs
- **Tier 5:** Junior ICs
- **Tier 6:** Support staff

---

### 2. PROGRAM (Federal Program)

**Description:** Federal defense programs and contracts

**Primary Keys:**
- `program_id` (UUID)
- `piid` (Program Identification Number)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| program_id | String | id, program_id | No | Primary |
| program_name | String | Program Name, name | No | Yes |
| acronym | String | Acronym, Program Acronym | Yes | Yes |
| normalized_name | String | normalized_name | Yes | No |
| agency_owner | String | Agency Owner | Yes | Yes |
| sub_agency | String | sub_agency | Yes | No |
| program_type | String | Program Type | Yes | No |
| mission_area | String | Mission Area, Functional Areas | Yes | No |
| priority_level | String | Priority Level (Strategic, High, Medium, Low) | Yes | No |
| bd_priority | String | BD Priority (🔴 Critical, 🟠 High, 🟡 Medium, ⚪ Low) | Yes | Yes |
| confidence_level | String | Confidence Level (High/Medium/Low) | Yes | No |
| pts_involvement | String | PTS Involvement (Current, Past, Target, None) | Yes | No |
| contract_number | String | Contract Number, piid | Yes | Yes |
| tango_piid | String | tango_piid | Yes | No |
| parent_piid | String | parent_piid | Yes | No |
| contract_value | Decimal | Contract Value, total_contract_value | Yes | No |
| contract_value_consolidated | Decimal | Contract Value (Consolidated) | Yes | No |
| base_contract_value | Decimal | Base Contract Value (FPDS) | Yes | No |
| base_plus_options | Decimal | Base + Options Value (FPDS) | Yes | No |
| obligated | Decimal | obligated | Yes | No |
| subawards_total | Decimal | subawards_total | Yes | No |
| subawards_count | Integer | subawards_count | Yes | No |
| prime_contractor | String | Prime Contractor, prime_contractor_name | Yes | Yes |
| prime_contractor_id | String | prime_contractor_id | Yes | No |
| recipient_name | String | recipient_name | Yes | No |
| recipient_uei | String | recipient_uei | Yes | No |
| key_subcontractors | String[] | Key Subcontractors (comma-separated) | Yes | No |
| known_subcontractors | String[] | Known Subcontractors | Yes | No |
| period_of_performance | String | Period of Performance | Yes | No |
| pop_start | Date | PoP Start, period_start, start_date | Yes | Yes |
| pop_end | Date | PoP End, period_end, end_date | Yes | Yes |
| pop_start_consolidated | Date | PoP Start (Consolidated) | Yes | No |
| pop_end_consolidated | Date | PoP End (Consolidated) | Yes | No |
| ultimate_completion | Date | ultimate_completion, Ultimate Completion Date (FPDS) | Yes | No |
| recompete_date | Date | Recompete Date | Yes | Yes |
| contract_signed_date | Date | Contract Signed Date (FPDS) | Yes | No |
| contract_effective_date | Date | Contract Effective Date (FPDS) | Yes | No |
| current_completion_date | Date | Current Completion Date (FPDS) | Yes | No |
| key_locations | String[] | Key Locations (comma-separated) | Yes | No |
| performance_location_tango | String | Performance Location (TANGO) | Yes | No |
| performance_location_fpds | String | Performance Location (FPDS) | Yes | No |
| pop_city | String | pop_city | Yes | No |
| pop_state | String | pop_state | Yes | No |
| pop_zip | String | pop_zip | Yes | No |
| pop_country | String | pop_country | Yes | No |
| naics_code | String | NAICS Code (Consolidated), naics_code | Yes | Yes |
| fpds_naics_code | String | FPDS NAICS Code | Yes | No |
| naics_description | String | NAICS Description | Yes | No |
| psc_code | String | PSC Code (Consolidated), psc_code | Yes | No |
| fpds_psc_code | String | FPDS PSC Code | Yes | No |
| psc_description | String | PSC Description | Yes | No |
| set_aside | String | set_aside (Partial/Full) | Yes | No |
| technical_stack | String | Technical Stack (free text) | Yes | No |
| tech_stack_basic | String[] | Tech Stack (Basic) | Yes | No |
| keywords_signals | String[] | Keywords/Signals | Yes | No |
| functional_areas | String[] | Functional Areas | Yes | No |
| typical_roles | String[] | Typical Roles | Yes | No |
| job_titles | String[] | Job Titles | Yes | No |
| labor_rate_min | Decimal | Labor Rate Min | Yes | No |
| labor_rate_max | Decimal | Labor Rate Max | Yes | No |
| labor_rate_average | Decimal | Labor Rate Average | Yes | No |
| education_requirement | String | Education Requirement | Yes | No |
| experience_requirement | String | Experience Requirement | Yes | No |
| annual_salary_range | String | Annual Salary Range | Yes | No |
| clearance_requirements | String[] | Clearance Requirements | Yes | No |
| security_requirements | String | Security Requirements | Yes | No |
| contract_vehicle_used | String | Contract Vehicle Used | Yes | No |
| contract_vehicle_type | String | Contract Vehicle/Type | Yes | No |
| awarding_office | String | awarding_office | Yes | No |
| awarding_agency | String | awarding_agency | Yes | No |
| funding_office | String | funding_office | Yes | No |
| cor_cotr | String | COR/COTR | Yes | No |
| program_manager | String | Program Manager | Yes | No |
| match_confidence | String | Match Confidence | Yes | No |
| match_score | Integer | Match Score (0-100) | Yes | No |
| incumbent_score | Integer | Incumbent Score (0-100) | Yes | No |
| source_evidence | String | Source Evidence | Yes | No |
| notes | String | Notes (free text) | Yes | No |
| pain_points | String | Pain Points | Yes | No |
| related_jobs | String[] | Related Jobs | Yes | No |
| tango_description | String | tango_description | Yes | No |
| parent_description | String | parent_description | Yes | No |
| budget | Decimal | Budget | Yes | No |
| calc_api_status | String | CALC API Status | Yes | No |
| job_count | Integer | job_count, total_jobs | Yes | No |
| contact_count | Integer | contact_count | Yes | No |
| placement_count | Integer | total_placements | Yes | No |
| total_revenue | Decimal | total_revenue | Yes | No |
| hiring_velocity | String | hiring_velocity, Hiring Velocity (High/Medium/Low/None) | Yes | No |
| status | String | status (High/Medium/Low, Open/Closed) | Yes | No |
| description | String | description | Yes | No |
| created_at | DateTime | created_at | Yes | No |
| updated_at | DateTime | updated_at | Yes | No |

**Source Files:**
- `Engine2_ProgramMapping/data/Federal Programs MASTER ENRICHED.csv` (89 columns, 388 programs)
- `dashboard/public/data/programs_enriched.json` (401 programs)
- `data/from_data_scraper/MASTER_PROGRAMS_ENRICHED.csv`
- `Engine7_BullhornETL/data/bullhorn_master.db` → programs table (4 rows)

---

### 3. JOB (Job Posting)

**Description:** Job postings from various sources (Apex, Insight Global, ClearedJobs, etc.)

**Primary Keys:**
- `job_id` (UUID)
- `job_number` (vendor job number)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| job_id | String | id, bullhorn_job_id | No | Primary |
| job_number | String | job_number, Job Number | Yes | Unique |
| title | String | title, Job Title, jobTitle | No | Yes |
| description | String | description (500-2000 chars) | Yes | No |
| company | String | company, client_corporation | Yes | Yes |
| location | String | location, Job Location, jobLocation | Yes | Yes |
| city | String | city | Yes | No |
| state | String | state | Yes | No |
| clearance_required | String | clearance, Security Clearance, clearance_required | Yes | Yes |
| employment_type | String | employment_type, Employment Type, jobType | Yes | No |
| status | String | status (Open, Closed, Filled, enriched) | Yes | Yes |
| pay_rate | Decimal | pay_rate, payRate | Yes | No |
| bill_rate | Decimal | bill_rate | Yes | No |
| salary | Decimal | salary | Yes | No |
| perm_fee_percent | Integer | perm_fee_percent | Yes | No |
| duration | String | duration (e.g., "12 months w/ extension") | Yes | No |
| date_posted | Date | date_posted, Date Posted, datePosted | Yes | Yes |
| date_added | DateTime | date_added | Yes | No |
| date_modified | DateTime | date_modified | Yes | No |
| date_closed | DateTime | date_closed | Yes | No |
| scraped_at | DateTime | scraped_at, Scraped At, scrapedAt | Yes | No |
| source | String | source, Job Source (Apex, Insight, clearancejobs, linkedin) | Yes | Yes |
| url | String | url, Job URL, jobUrl | Yes | No |
| matched_program | String | matched_program, Matched Program | Yes | Yes |
| program_acronym | String | program_acronym, Program Acronym | Yes | No |
| program_agency | String | program_agency, Program Agency | Yes | No |
| prime_contractor | String | prime_contractor, Prime Contractor, prime | Yes | Yes |
| program_location | String | program_location, Program Location | Yes | No |
| contract_number | String | contract_number, Contract Number | Yes | No |
| task_order | String | task_order | Yes | No |
| match_score | Integer | match_score, Match Score (0-100) | Yes | No |
| match_confidence | String | match_confidence, Match Confidence (Low/Medium/High) | Yes | No |
| match_type | String | Match Type | Yes | No |
| match_reasons | String | match_reasons, Match Reasons | Yes | No |
| match_signals | String | Match Signals | Yes | No |
| secondary_candidates | String[] | Secondary Candidates | Yes | No |
| bd_priority_score | Integer | BD Priority Score, bd_score (0-100) | Yes | Yes |
| priority_tier | String | priority_tier, Priority Tier (🔥 Hot, 🟡 Warm, ❄️ Cold) | Yes | Yes |
| base_score | Integer | base_score (50) | Yes | No |
| clearance_boost | Integer | clearance_boost (0-25) | Yes | No |
| program_boost | Integer | program_boost | Yes | No |
| location_boost | Integer | location_boost (0-10) | Yes | No |
| confidence_boost | Integer | confidence_boost (0-10) | Yes | No |
| recency_boost | Integer | recency_boost | Yes | No |
| pain_point_boost | Integer | pain_point_boost | Yes | No |
| tier_multiplier | Float | tier_multiplier (1.0) | Yes | No |
| recommendations | String[] | Recommendations | Yes | No |
| primary_contact | String | Primary Contact | Yes | No |
| contact_title | String | Contact Title | Yes | No |
| contact_tier | Integer | Contact Tier (1-6) | Yes | No |
| contact_email | String | Contact Email | Yes | No |
| matched_contacts_count | Integer | Matched Contacts Count | Yes | No |
| skills | String[] | skills (CSV list) | Yes | No |
| technologies | String[] | technologies, required_technologies (array) | Yes | No |
| certifications_required | String[] | certifications_required | Yes | No |
| certifications_extra | String[] | certifications_extra | Yes | No |
| experience_years | Integer | experience_years | Yes | No |
| hiring_leader | String | hiring_leader | Yes | No |
| program_manager | String | program_manager | Yes | No |
| pts_past_programs | String[] | pts_past_programs | Yes | No |
| pts_past_jobs | String[] | pts_past_jobs | Yes | No |
| pts_past_contractors | String[] | pts_past_contractors | Yes | No |
| pts_past_contacts | String[] | pts_past_contacts | Yes | No |
| owner | String | owner, contact | Yes | No |
| custom_text1 | String | custom_text1 | Yes | No |
| custom_text2 | String | custom_text2 | Yes | No |
| custom_text3 | String | custom_text3 | Yes | No |
| source_file | String | source_file | Yes | No |
| created_at | DateTime | created_at | Yes | No |
| updated_at | DateTime | updated_at | Yes | No |

**Source Files:**
- `Engine1_Scraper/data/Jobs_Mapped_to_Programs_MASTER.csv` (17 columns)
- `outputs/all_jobs_fully_enriched.json` (7,048 lines, 531 jobs)
- `dashboard/public/data/jobs_enriched.json`
- `Engine7_BullhornETL/data/bullhorn_master.db` → jobs table (135 rows)

---

### 4. CONTRACTOR (Company/Prime/Sub)

**Description:** Defense contractors (primes and subs)

**Primary Keys:**
- `contractor_id` (UUID)
- `uei` (Unique Entity Identifier)
- `cage_code` (Commercial and Government Entity code)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| contractor_id | String | id, prime_contractor_id | No | Primary |
| name | String | name, Company Name, prime_contractor_name | No | Yes |
| normalized_name | String | normalized_name | Yes | No |
| aliases | String[] | aliases (pipe-separated) | Yes | No |
| uei | String | recipient_uei, uei | Yes | Unique |
| cage_code | String | cage_code, CAGE Code | Yes | Unique |
| duns_number | String | duns_number, DUNS Number | Yes | No |
| sam_registration | Boolean | SAM Registration | Yes | No |
| company_type | String | Company Type (Large Business, Small Business, 8(a), SDVOSB, WOSB, HUBZone) | Yes | Yes |
| size_tier | String | size_tier (Small, Medium, Large, Giant, Mega) | Yes | No |
| clearance_facility | String | Clearance Facility (None, Secret, TS, SCI) | Yes | No |
| employee_count | Integer | Employee Count, employee_count | Yes | No |
| annual_revenue | Decimal | Annual Revenue, annual_revenue | Yes | No |
| website | String | website | Yes | No |
| linkedin_url | String | LinkedIn Company URL, linkedin_url | Yes | No |
| github_org | String | GitHub Organization | Yes | No |
| headquarters | String | headquarters | Yes | No |
| key_capabilities | String[] | Key Capabilities | Yes | No |
| recent_wins | String[] | Recent Wins | Yes | No |
| naics_codes | String[] | naics_codes (pipe-separated) | Yes | No |
| contract_vehicles | String[] | contract_vehicles, Contract Vehicles | Yes | No |
| federal_programs_prime | String[] | Federal Programs (Prime) | Yes | No |
| federal_programs_sub | String[] | Federal Programs (Sub) | Yes | No |
| past_performance | String | Past Performance | Yes | No |
| subcontractor_to | String[] | Subcontractor To | Yes | No |
| relationship_status | String | relationship_status (Active, Prospect, Cold) | Yes | No |
| programs_supported | String[] | programs_supported | Yes | No |
| total_jobs | Integer | total_jobs | Yes | No |
| total_placements | Integer | total_placements, placements_made | Yes | No |
| active_placements | Integer | active_placements | Yes | No |
| total_revenue | Decimal | total_revenue, portfolio_value | Yes | No |
| first_engagement_date | Date | first_engagement_date | Yes | No |
| last_engagement_date | Date | last_engagement_date, last_engagement | Yes | No |
| bd_contacts | Integer | BD Contacts | Yes | No |
| job_count | Integer | job_count | Yes | No |
| contact_count | Integer | contact_count | Yes | No |
| notes | String | notes | Yes | No |
| category | String | category | Yes | No |
| created_at | DateTime | created_at | Yes | No |
| updated_at | DateTime | updated_at | Yes | No |

**Source Files:**
- `Engine2_ProgramMapping/data/Contractors Database.csv` (19 columns)
- `dashboard/public/data/contractors_enriched.json` (15 contractors)
- `Engine7_BullhornETL/data/bullhorn_master.db` → prime_contractors table (41 rows)
- `data/from_data_scraper/MASTER_PRIMES_ENRICHED.csv`

---

### 5. LOCATION (Geographic Location)

**Description:** Cities, states, and geographic locations

**Primary Keys:**
- `location_id` (UUID)
- Composite: `city` + `state`

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| location_id | String | id | No | Primary |
| city | String | city, pop_city, Person City | Yes | Yes |
| state | String | state, pop_state, Person State | Yes | Yes |
| zip_code | String | zip_code, pop_zip | Yes | No |
| country | String | pop_country, country (default: US) | Yes | No |
| latitude | Float | latitude | Yes | No |
| longitude | Float | longitude | Yes | No |
| job_count | Integer | job_count, job_count_at_location | Yes | No |
| contact_count | Integer | contact_count | Yes | No |
| program_count | Integer | program_count | Yes | No |
| clearances_at_location | String[] | clearances_at_location | Yes | No |
| functional_areas | String[] | functional_area | Yes | No |
| sample_titles | String[] | sample_titles | Yes | No |
| created_at | DateTime | created_at | Yes | No |

**Source Files:**
- `data/from_n8n_builder/analytical_outputs/02_location_org_chart.csv`
- `dashboard/public/data/mindmap_nodes.json` (341 LOCATION nodes)

---

### 6. CALL_NOTE (Activity/Interaction)

**Description:** CRM call notes and interactions

**Primary Keys:**
- `note_id` (Integer or UUID)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| note_id | String | id, bullhorn_activity_id | No | Primary |
| department | String | department, Department | Yes | No |
| note_author | String | note_author, Note Author, actor | Yes | Yes |
| date_added | Date | date_added, Date Note Added, activity_date | Yes | Yes |
| note_type | String | note_type, Type, activity_type | Yes | No |
| action | String | action, Note Action | Yes | No |
| about | String | about, About | Yes | No |
| status | String | status, Status | Yes | No |
| note_body | String | note_body, Note Body (long text) | Yes | No |
| note_text | String | note_text | Yes | No |
| comments | String | comments | Yes | No |
| has_traction | Boolean | has_traction | Yes | No |
| no_answer | Boolean | no_answer | Yes | No |
| not_interested | Boolean | not_interested | Yes | No |
| no_openings | Boolean | no_openings | Yes | No |
| positive_response | Boolean | positive_response | Yes | No |
| hiring_signal | Boolean | hiring_signal | Yes | No |
| programs_mentioned | String[] | programs_mentioned (pipe/comma-delimited) | Yes | No |
| primes_mentioned | String[] | primes_mentioned | Yes | No |
| locations_mentioned | String[] | locations_mentioned | Yes | No |
| clearances_mentioned | String[] | clearances_mentioned | Yes | No |
| related_job_id | Integer | related_job_id | Yes | No |
| related_candidate_id | Integer | related_candidate_id | Yes | No |
| bullhorn_job_id | String | bullhorn_job_id | Yes | No |
| bullhorn_candidate_id | String | bullhorn_candidate_id | Yes | No |
| follow_up_required | Boolean | follow_up_required | Yes | No |
| follow_up_date | Date | follow_up_date | Yes | No |
| source_file | String | source_file | Yes | No |
| period | String | period | Yes | No |
| created_at | DateTime | created_at | Yes | No |

**Source Files:**
- `Engine7_BullhornETL/data/bullhorn_master.db` → call_notes table (50,710 rows)
- `Engine7_BullhornETL/data/bullhorn_master.db` → activities table (404,715 rows)
- `data/from_data_scraper/ALL_NOTES_COMBINED.csv`
- `dashboard/public/data/call_notes_*.json`

---

### 7. PLACEMENT (Job Placement)

**Description:** Successful job placements (monetization events)

**Primary Keys:**
- `placement_id` (String or Integer)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| placement_id | String | id, bullhorn_placement_id | No | Primary |
| job_id | Integer | job_id | Yes | Yes |
| candidate_id | Integer | candidate_id | Yes | Yes |
| bullhorn_job_id | String | bullhorn_job_id | Yes | No |
| bullhorn_candidate_id | String | bullhorn_candidate_id | Yes | No |
| placement_date | Date | placement_date | Yes | Yes |
| start_date | Date | start_date | Yes | Yes |
| end_date | Date | end_date | Yes | No |
| status | String | status | Yes | No |
| outcome | String | outcome | Yes | No |
| pay_rate | Decimal | pay_rate | Yes | No |
| bill_rate | Decimal | bill_rate | Yes | No |
| salary | Decimal | salary | Yes | No |
| commission | Decimal | commission | Yes | No |
| duration_days | Integer | duration_days | Yes | No |
| client_name | String | client_name | Yes | No |
| job_title | String | job_title | Yes | No |
| candidate_name | String | candidate_name | Yes | No |
| owner | String | owner | Yes | No |
| source_file | String | source_file | Yes | No |
| created_at | DateTime | created_at | Yes | No |

**Source Files:**
- `Engine7_BullhornETL/data/bullhorn_master.db` → placements table (616 rows)
- `Engine7_BullhornETL/data/bullhorn_master.db` → placement_program_links table (1,814 rows)

---

### 8. TECHNOLOGY (Tech Stack)

**Description:** Technologies and skills

**Primary Keys:**
- `technology_id` (UUID)
- `name` (unique constraint)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| technology_id | String | id | No | Primary |
| name | String | technology_keyword, technologies | No | Unique |
| category | String | category (cloud, database, network, security, language) | Yes | Yes |
| mention_count | Integer | mention_count | Yes | No |
| pct_of_jobs | Float | pct_of_jobs | Yes | No |
| popularity_score | Integer | popularity_score | Yes | No |
| created_at | DateTime | created_at | Yes | No |

**Source Files:**
- `data/from_n8n_builder/analytical_outputs/03_technology_signals.csv`
- Job descriptions (extracted from technologies field)

---

### 9. CLEARANCE_LEVEL (Security Clearance)

**Description:** Security clearance levels

**Primary Keys:**
- `clearance_id` (UUID)
- `level` (unique constraint)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| clearance_id | String | id | No | Primary |
| level | String | clearance_level (None, Public Trust, Secret, Top Secret, TS/SCI, TS/SCI w/ Poly) | No | Unique |
| rank | Integer | rank (0-6, higher = more restrictive) | Yes | No |
| requirements | String | requirements | Yes | No |
| job_count | Integer | job_count | Yes | No |
| pct_of_jobs | Float | pct_of_jobs | Yes | No |
| created_at | DateTime | created_at | Yes | No |

**Source Files:**
- `data/from_n8n_builder/analytical_outputs/04_clearance_requirements.csv`

**Rank Mapping:**
- 0: None
- 1: Public Trust
- 2: Secret
- 3: Top Secret
- 4: TS/SCI
- 5: TS/SCI with CI Poly
- 6: TS/SCI with Full Scope Polygraph

---

### 10. OPPORTUNITY (BD Opportunity)

**Description:** Business development opportunities

**Primary Keys:**
- `opportunity_id` (UUID)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| opportunity_id | String | id, Opportunity ID | No | Primary |
| matched_program | String | matched_program, Matched Program | Yes | Yes |
| priority_score | Integer | priority_score, Priority Score (0-100) | Yes | Yes |
| priority_level | String | priority_level, Priority Level (Hot/Warm/Cold) | Yes | Yes |
| status | String | status, Status (New/Contacted/Proposed/Won/Lost) | Yes | Yes |
| next_action | String | next_action, Next Action | Yes | No |
| created_date | Date | created_date, Created Date | Yes | Yes |
| source_job_title | String | source_job_title, Source Job Title | Yes | No |
| source_company | String | source_company, Source Company | Yes | No |
| company | String | company, Company | Yes | No |
| value | Decimal | value, Value | Yes | No |
| key_contact | String | key_contact, Key Contact | Yes | No |
| contact_email | String | contact_email, Contact Email | Yes | No |
| next_followup | Date | next_followup, Next Follow-up | Yes | No |
| notes | String | notes, Notes | Yes | No |
| related_program | String | related_program, Related Program | Yes | No |
| source_hub_record | String | source_hub_record, Source Hub Record | Yes | No |
| created_at | DateTime | created_at | Yes | No |
| updated_at | DateTime | updated_at | Yes | No |

**Source Files:**
- `Engine2_ProgramMapping/data/BD Opportunities.csv` (17 columns)

---

### 11. CONTRACT_VEHICLE (Contract Vehicle)

**Description:** Contract vehicles (IDIQ, GWAC, BPA, etc.)

**Primary Keys:**
- `vehicle_id` (UUID)
- `vehicle_name` (unique constraint)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| vehicle_id | String | id | No | Primary |
| vehicle_name | String | Vehicle Name | No | Unique |
| vehicle_type | String | Vehicle Type (GWAC, IDIQ, BPA, etc.) | Yes | Yes |
| agencies | String[] | Agencies (comma-separated) | Yes | No |
| ceiling_value | Decimal | Ceiling Value | Yes | No |
| period_of_performance | String | Period of Performance | Yes | No |
| naics_codes | String[] | NAICS Codes | Yes | No |
| small_business_set_aside | String | Small Business Set-Aside (Partial/Full/No) | Yes | No |
| contract_number | String | Contract Number | Yes | No |
| prime_contractors | String[] | Prime Contractors (approved holders) | Yes | No |
| related_jobs | String[] | Related Jobs | Yes | No |
| solicitation_documents | String | Solicitation Documents | Yes | No |
| federal_programs | String[] | Federal Programs | Yes | No |
| key_personnel_requirements | String | Key Personnel Requirements | Yes | No |
| poc_information | String | POC Information | Yes | No |
| created_at | DateTime | created_at | Yes | No |

**Source Files:**
- `Engine2_ProgramMapping/data/Contract_Vehicles.csv` (14 columns)

---

### 12. AGENCY (Government Agency)

**Description:** Government agencies

**Primary Keys:**
- `agency_id` (UUID)
- `name` (unique constraint)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| agency_id | String | id | No | Primary |
| name | String | Agency Owner, awarding_agency, agency | No | Unique |
| department | String | department | Yes | No |
| agency_type | String | agency_type (DoD, Army, Navy, Air Force, Space Force, IC, etc.) | Yes | Yes |
| budget_estimate | Decimal | budget_estimate | Yes | No |
| program_count | Integer | program_count | Yes | No |
| created_at | DateTime | created_at | Yes | No |

**Source Files:**
- Derived from Agency Owner field in Federal Programs data

**Agency Types (26 options):**
DoD, Army, Navy, Air Force, Space Force, SOCOM, MDA, CIA, NSA, DIA, NRO, NGA, ODNI, DHS, TSA, CBP, DOE, NNSA, DOJ, FBI, DOT, FAA, NASA, NOAA, VA, HHS

---

### 13. TEAM (Organizational Team)

**Description:** Teams within the BD organization

**Primary Keys:**
- `team_id` (UUID)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| team_id | String | id | No | Primary |
| name | String | name | No | Yes |
| department | String | department | Yes | No |
| organization | String | organization | Yes | No |
| member_count | Integer | member_count | Yes | No |
| created_at | DateTime | created_at | Yes | No |

**Source Files:**
- `dashboard/public/data/mindmap_nodes.json` (4 TEAM nodes)

---

### 14. SKILL (Functional Skill)

**Description:** Functional skills and capabilities

**Primary Keys:**
- `skill_id` (UUID)
- `name` (unique constraint)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| skill_id | String | id | No | Primary |
| name | String | functional_area, skill name | No | Unique |
| category | String | category (technical, leadership, clearance, language, domain) | Yes | Yes |
| job_count | Integer | job_count | Yes | No |
| pct_of_jobs | Float | pct_of_jobs | Yes | No |
| frequency | Integer | frequency | Yes | No |
| created_at | DateTime | created_at | Yes | No |

**Source Files:**
- `data/from_n8n_builder/analytical_outputs/05_functional_areas.csv`

---

### 15. ENTITY (Knowledge Graph Entity)

**Description:** Generic entities from LightRAG/Graphiti

**Primary Keys:**
- `entity_id` (String)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| entity_id | String | id | No | Primary |
| type | String | type (organization, person, program, location, capability_area) | No | Yes |
| name | String | name | No | Yes |
| properties | JSON | properties (arbitrary metadata) | Yes | No |
| created_at | DateTime | created_at | Yes | No |

**Source Files:**
- `Engine8_Knowledge/data/bd_graph.db` → entities table (2,166 rows)
- `Engine8_Knowledge/data/lightrag_test2/vdb_entities.json`

---

### 16. PAST_PERFORMANCE (Contractor Performance History)

**Description:** Prime contractor performance history on programs

**Primary Keys:**
- `performance_id` (Integer)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| performance_id | String | id | No | Primary |
| prime_contractor_id | Integer | prime_contractor_id | Yes | Yes |
| prime_contractor_name | String | prime_contractor_name | Yes | Yes |
| program_id | Integer | program_id | Yes | Yes |
| program_name | String | program_name | Yes | No |
| total_jobs | Integer | total_jobs | Yes | No |
| open_jobs | Integer | open_jobs | Yes | No |
| closed_jobs | Integer | closed_jobs | Yes | No |
| filled_jobs | Integer | filled_jobs | Yes | No |
| lost_jobs | Integer | lost_jobs | Yes | No |
| total_placements | Integer | total_placements | Yes | No |
| active_placements | Integer | active_placements | Yes | No |
| completed_placements | Integer | completed_placements | Yes | No |
| total_candidates_submitted | Integer | total_candidates_submitted | Yes | No |
| total_revenue | Decimal | total_revenue | Yes | No |
| avg_bill_rate | Decimal | avg_bill_rate | Yes | No |
| avg_pay_rate | Decimal | avg_pay_rate | Yes | No |
| avg_margin | Decimal | avg_margin | Yes | No |
| avg_placement_duration_days | Integer | avg_placement_duration_days | Yes | No |
| fill_rate | Decimal | fill_rate | Yes | No |
| first_job_date | Date | first_job_date | Yes | No |
| last_job_date | Date | last_job_date | Yes | No |
| first_placement_date | Date | first_placement_date | Yes | No |
| last_placement_date | Date | last_placement_date | Yes | No |
| performance_score | Decimal | performance_score | Yes | No |
| notes | String | notes | Yes | No |
| created_at | DateTime | created_at | Yes | No |
| updated_at | DateTime | updated_at | Yes | No |

**Source Files:**
- `Engine7_BullhornETL/data/bullhorn_master.db` → past_performance table (492 rows)

---

### 17. BRIEFING (BD Briefing Document)

**Description:** Generated BD briefing materials

**Primary Keys:**
- `briefing_id` (UUID)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| briefing_id | String | id | No | Primary |
| job_id | String | job_id | Yes | Yes |
| contact_id | String | contact_id | Yes | Yes |
| program_id | String | program_id | Yes | Yes |
| briefing_type | String | briefing_type (CallScript, Email, Playbook, TalkingPoints, Briefing) | No | Yes |
| title | String | title | Yes | No |
| content | String | content (markdown or text) | Yes | No |
| file_path | String | file_path | Yes | No |
| generated_at | DateTime | generated_at | Yes | Yes |
| generated_by | String | generated_by (engine name) | Yes | No |
| created_at | DateTime | created_at | Yes | No |

**Source Files:**
- `outputs/BD_Briefings/*.md` (50+ files)
- `outputs/BD_Briefings/*.txt`

---

### 18. GAP_ANALYSIS (Staffing Gap Analysis)

**Description:** Identified staffing gaps and opportunities

**Primary Keys:**
- `gap_id` (Integer)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| gap_id | String | id | No | Primary |
| entity_type | String | entity_type (prime, program, location) | Yes | Yes |
| entity_name | String | entity_name | Yes | Yes |
| gap_reason | String | gap_reason (free text) | Yes | No |
| negative_count | Integer | negative_count | Yes | No |
| positive_count | Integer | positive_count | Yes | No |
| recommendation | String | recommendation (free text) | Yes | No |
| priority | String | priority (High/Medium/Low) | Yes | Yes |
| gap_status | String | Gap_Status (CRITICAL_GAP, MINIMAL) | Yes | No |
| contract_value | Decimal | Contract_Value | Yes | No |
| placements | Integer | Placements | Yes | No |
| revenue_est | Decimal | Revenue_Est | Yes | No |
| call_mentions | Integer | Call_Mentions | Yes | No |
| zoominfo_priority | Integer | ZoomInfo_Priority (1-5) | Yes | No |
| key_locations | String[] | Key_Locations | Yes | No |
| recommended_titles | String[] | Recommended_Titles | Yes | No |
| notes | String | Notes | Yes | No |
| created_at | DateTime | created_at | Yes | No |

**Source Files:**
- `Engine7_BullhornETL/data/bullhorn_master.db` → gap_analysis table (103 rows)
- `outputs/PROGRAM_PLACEMENT_GAP_ANALYSIS_20260122.csv`

---

### 19. NOTIFICATION (Alert/Notification)

**Description:** System notifications and alerts

**Primary Keys:**
- `notification_id` (Integer)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| notification_id | String | id | No | Primary |
| type | String | type | Yes | Yes |
| title | String | title | Yes | No |
| message | String | message | Yes | No |
| entity_type | String | entity_type | Yes | No |
| entity_id | String | entity_id | Yes | No |
| priority | String | priority | Yes | No |
| created_at | DateTime | created_at | Yes | Yes |
| read_at | DateTime | read_at | Yes | No |

**Source Files:**
- `Engine8_Knowledge/data/notifications.db` → notifications table (1 row)

---

### 20. MEMORY (AI Memory/Insight)

**Description:** AI-generated insights and memories

**Primary Keys:**
- `memory_id` (Integer)

**Properties:**

| Property | Type | Source Column(s) | Nullable | Index |
|----------|------|------------------|----------|-------|
| memory_id | String | id | No | Primary |
| user_id | String | user_id | Yes | No |
| memory_type | String | memory_type | Yes | No |
| content | String | content | Yes | No |
| metadata | JSON | metadata | Yes | No |
| entity_type | String | entity_type | Yes | No |
| entity_name | String | entity_name | Yes | No |
| insight | String | insight | Yes | No |
| source | String | source | Yes | No |
| confidence | Float | confidence | Yes | No |
| timestamp | DateTime | timestamp, created_at | Yes | Yes |
| created_at | DateTime | created_at | Yes | No |
| updated_at | DateTime | updated_at | Yes | No |

**Source Files:**
- `Engine8_Knowledge/data/memories.db` → memories table (3 rows)
- `Engine8_Knowledge/data/memories.db` → insights table (1 row)

---

## RELATIONSHIP DEFINITIONS

### Contact Relationships

| Relationship | From | To | Properties | Cardinality | Description |
|--------------|------|-----|-----------|-------------|-------------|
| WORKS_FOR | CONTACT | CONTRACTOR | role, start_date, end_date | N:1 | Employment relationship |
| WORKS_AT | CONTACT | LOCATION | office, remote | N:M | Work location |
| MEMBER_OF | CONTACT | TEAM | role, join_date | N:M | Team membership (1,137 relationships) |
| WORKS_ON | CONTACT | PROGRAM | role, engagement_level | N:M | Program engagement (1,142 relationships) |
| REPORTS_TO | CONTACT | CONTACT | relationship_type | N:1 | Organizational hierarchy |
| KNOWS | CONTACT | CONTACT | relationship_strength, last_contact | N:M | Professional network |
| MANAGES | CONTACT | PROGRAM | authority_level, start_date | N:M | Program management |
| HIRED_FOR | CONTACT | JOB | application_date, status | N:M | Job application |
| PLACED_IN | CONTACT | PLACEMENT | start_date, end_date | 1:M | Placement history |
| HAS_CLEARANCE | CONTACT | CLEARANCE_LEVEL | issued_date, expiry_date | N:M | Clearance held |
| HAS_SKILL | CONTACT | SKILL | proficiency_level, years_experience | N:M | Skill possession |
| FAMILIAR_WITH | CONTACT | TECHNOLOGY | proficiency_level | N:M | Technology familiarity |
| DECISION_MAKER_FOR | CONTACT | PROGRAM | authority_level | N:M | Decision authority |
| INTERVIEWER_FOR | CONTACT | JOB | interview_date, outcome | N:M | Hiring role |
| MENTIONED_IN | CONTACT | CALL_NOTE | mention_context | N:M | Note references |

### Program Relationships

| Relationship | From | To | Properties | Cardinality | Description |
|--------------|------|-----|-----------|-------------|-------------|
| PRIMED_BY | PROGRAM | CONTRACTOR | contract_value, start_date, end_date | N:1 | Prime contractor |
| SUBCONTRACTED_TO | PROGRAM | CONTRACTOR | sub_tier, contract_value | N:M | Subcontractor relationships |
| OWNED_BY | PROGRAM | AGENCY | funding_amount | N:1 | Agency ownership (90 relationships) |
| LOCATED_AT | PROGRAM | LOCATION | site_type | N:M | Performance locations (684 relationships) |
| USES_VEHICLE | PROGRAM | CONTRACT_VEHICLE | contract_number | N:M | Contract vehicle usage |
| HAS_JOB | PROGRAM | JOB | job_count | 1:M | Open job postings |
| HAS_CONTACT | PROGRAM | CONTACT | engagement_type | 1:M | Program contacts |
| REQUIRES_SKILL | PROGRAM | SKILL | importance_level | N:M | Required skills |
| REQUIRES_TECHNOLOGY | PROGRAM | TECHNOLOGY | criticality | N:M | Required technologies |
| REQUIRES_CLEARANCE | PROGRAM | CLEARANCE_LEVEL | minimum_level | N:M | Clearance requirements |
| RELATED_TO | PROGRAM | PROGRAM | relationship_type (competing, adjacent, parent, child) | N:M | Program relationships |
| MENTIONED_IN | PROGRAM | CALL_NOTE | mention_context | N:M | Note references |
| HAS_PAST_PERFORMANCE | PROGRAM | PAST_PERFORMANCE | performance_score | 1:M | Performance history |

### Job Relationships

| Relationship | From | To | Properties | Cardinality | Description |
|--------------|------|-----|-----------|-------------|-------------|
| MATCHED_TO | JOB | PROGRAM | match_score, confidence, match_type | N:1 | Program matching (531 relationships) |
| POSTED_BY | JOB | CONTRACTOR | posting_date, status | N:1 | Job poster |
| LOCATED_AT | JOB | LOCATION | site_type | N:1 | Job location (4 relationships) |
| REQUIRES_CLEARANCE | JOB | CLEARANCE_LEVEL | minimum_level | N:1 | Clearance requirement |
| REQUIRES_SKILL | JOB | SKILL | level_required, importance | N:M | Skill requirements |
| REQUIRES_TECHNOLOGY | JOB | TECHNOLOGY | experience_level | N:M | Technology requirements |
| ASSIGNED_TO | JOB | CONTACT | role (hiring_leader, program_manager) | N:M | Assigned contacts |
| HAS_BRIEFING | JOB | BRIEFING | generated_at | 1:M | Associated briefings |
| FILLED_BY | JOB | PLACEMENT | placement_date | 1:1 | Placement link |
| APPLIED_BY | JOB | CONTACT | application_date, status | N:M | Applications |

### Contractor Relationships

| Relationship | From | To | Properties | Cardinality | Description |
|--------------|------|-----|-----------|-------------|-------------|
| PRIMES | CONTRACTOR | PROGRAM | contract_value, role | N:M | Prime contracts (336 relationships) |
| SUBCONTRACTED_TO | CONTRACTOR | CONTRACTOR | tier_level, contract_value | N:M | Sub relationships |
| EMPLOYS | CONTRACTOR | CONTACT | role, start_date | 1:M | Employment |
| OFFICES_AT | CONTRACTOR | LOCATION | office_type (HQ, branch, site) | N:M | Office locations |
| HAS_CONTRACT_FOR | CONTRACTOR | PROGRAM | contract_number, value | N:M | Contract holdings |
| SUBMITTED_FOR | CONTRACTOR | JOB | submission_date, status | N:M | Job submissions |
| HAS_PAST_PERFORMANCE | CONTRACTOR | PAST_PERFORMANCE | performance_score | 1:M | Performance records |

### Location Relationships

| Relationship | From | To | Properties | Cardinality | Description |
|--------------|------|-----|-----------|-------------|-------------|
| HOSTS | LOCATION | PROGRAM | site_type | N:M | Program hosting (684 relationships) |
| HOSTS_JOB | LOCATION | JOB | job_type | N:M | Job locations (4 relationships) |
| HOSTS_CONTACT | LOCATION | CONTACT | residence_type | N:M | Contact locations (1,142 relationships) |
| NEAR | LOCATION | LOCATION | distance_miles | N:M | Proximity |
| IN_REGION | LOCATION | LOCATION | region_type | N:1 | Regional hierarchy |

### Call Note Relationships

| Relationship | From | To | Properties | Cardinality | Description |
|--------------|------|-----|-----------|-------------|-------------|
| ABOUT | CALL_NOTE | CONTACT | mention_type | N:1 | Note subject |
| DISCUSSES | CALL_NOTE | PROGRAM | discussion_context | N:M | Program mentions |
| MENTIONS | CALL_NOTE | CONTRACTOR | mention_context | N:M | Contractor mentions |
| REFERENCES | CALL_NOTE | JOB | reference_type | N:M | Job mentions |
| CREATED_BY | CALL_NOTE | CONTACT | author_role | N:1 | Note author |

### Placement Relationships

| Relationship | From | To | Properties | Cardinality | Description |
|--------------|------|-----|-----------|-------------|-------------|
| FILLED | PLACEMENT | JOB | fill_date | 1:1 | Job filled |
| CANDIDATE | PLACEMENT | CONTACT | placement_role | N:1 | Placed candidate |
| FOR_PROGRAM | PLACEMENT | PROGRAM | program_name, match_score | N:1 | Program link (1,814 relationships) |
| BY_CONTRACTOR | PLACEMENT | CONTRACTOR | contractor_role | N:1 | Contractor link |

### Other Relationships

| Relationship | From | To | Properties | Cardinality | Description |
|--------------|------|-----|-----------|-------------|-------------|
| HAS_BRIEFING | OPPORTUNITY | BRIEFING | generated_at | 1:M | Opportunity briefings |
| TARGETS | OPPORTUNITY | PROGRAM | priority_score | N:1 | Target program |
| INVOLVES | OPPORTUNITY | CONTACT | involvement_type | N:M | Involved contacts |
| IDENTIFIED_IN | GAP_ANALYSIS | PROGRAM | gap_severity | N:1 | Gap identified |
| RECOMMENDS | GAP_ANALYSIS | CONTACT | recommendation_priority | N:M | Recommended hires |

---

## PROPERTY MAPPINGS

### Source Column → Schema Property Mapping

This section maps all unique source column headers to their standardized schema properties.

#### Contact Property Mappings

| Source Column(s) | Schema Property | Data Type | Transformation |
|------------------|-----------------|-----------|----------------|
| id, bullhorn_candidate_id | contact_id | String | Use id if exists, else bullhorn_candidate_id |
| first_name, First Name | first_name | String | Trim, title case |
| last_name, Last Name | last_name | String | Trim, title case |
| name, full_name, Name | full_name | String | Trim |
| email, Email Address | email | String | Lowercase, trim |
| phone, Direct Phone Number, Phone Number | phone | String | Normalize to (XXX) XXX-XXXX |
| mobile, Mobile phone | mobile | String | Normalize to (XXX) XXX-XXXX |
| linkedin_url, LinkedIn Contact Profile URL, LinkedIn | linkedin_url | String | Validate URL |
| job_title, Job Title, title, Primary Title | job_title | String | Trim |
| All Titles | all_titles | String[] | Split by pipe, trim |
| company_name, Company Name, current_employer, company | current_employer | String | Trim, standardize |
| city, Person City | city | String | Trim, title case |
| state, Person State | state | String | Uppercase, 2-letter code |
| address | address | String | Trim |
| zip_code | zip_code | String | 5-digit format |
| clearance_level, Clearances | clearance_level | String | Standardize (Secret, TS/SCI, etc.) |
| tier, Hierarchy Tier | tier | Integer | 1-6 |
| Contact Type | contact_type | String | Lowercase |
| Relationship Score, engagement_score | relationship_score | Integer | 0-1000+ |
| Is Hiring Manager | is_hiring_manager | Boolean | Yes → true, No → false |
| Has Open Reqs | has_open_reqs | Boolean | Yes → true, No → false |
| Is Decision Maker | is_decision_maker | Boolean | Yes → true, No → false |
| note_count, Note Count | note_count | Integer | Cast to int |
| last_activity_date, Last Activity, last_activity | last_activity_date | DateTime | Parse ISO 8601 |
| first_activity, First Activity | first_activity_date | DateTime | Parse ISO 8601 |
| status, Statuses | status | String | Trim, title case |
| BD Priority | bd_priority | String | Trim |
| occupation | occupation | String | Trim |
| owner, Authors | owner | String | Trim, comma-separated if multiple |
| Hiring Signals | hiring_signals | String | Trim |
| Pain Points | pain_points | String | Trim |
| Recent Note | recent_note | String | Trim |
| source_file | source_file | String | Trim |
| date_added, Date | date_added | DateTime | Parse ISO 8601 |
| date_modified, updated_at | date_modified | DateTime | Parse ISO 8601 |
| created_at | created_at | DateTime | Parse ISO 8601 |
| updated_at | updated_at | DateTime | Parse ISO 8601 |

#### Program Property Mappings

| Source Column(s) | Schema Property | Data Type | Transformation |
|------------------|-----------------|-----------|----------------|
| id, program_id | program_id | String | UUID if id exists |
| Program Name, name | program_name | String | Trim |
| Acronym, Program Acronym | acronym | String | Uppercase, trim |
| normalized_name | normalized_name | String | Lowercase, remove special chars |
| Agency Owner | agency_owner | String | Trim, standardize |
| sub_agency | sub_agency | String | Trim |
| Program Type | program_type | String | Trim |
| Mission Area, Functional Areas | mission_area | String | Trim |
| Priority Level | priority_level | String | Strategic/High/Medium/Low |
| BD Priority | bd_priority | String | Extract emoji + text |
| Confidence Level | confidence_level | String | High/Medium/Low |
| PTS Involvement | pts_involvement | String | Current/Past/Target/None |
| Contract Number, piid | contract_number | String | Trim, uppercase |
| tango_piid | tango_piid | String | Trim |
| parent_piid | parent_piid | String | Trim |
| Contract Value, total_contract_value | contract_value | Decimal | Parse currency ($XXM → float) |
| Contract Value (Consolidated) | contract_value_consolidated | Decimal | Parse currency |
| Base Contract Value (FPDS) | base_contract_value | Decimal | Parse currency |
| Base + Options Value (FPDS) | base_plus_options | Decimal | Parse currency |
| obligated | obligated | Decimal | Parse currency |
| subawards_total | subawards_total | Decimal | Parse currency |
| subawards_count | subawards_count | Integer | Cast to int |
| Prime Contractor, prime_contractor_name | prime_contractor | String | Trim, standardize name |
| prime_contractor_id | prime_contractor_id | String | UUID or foreign key |
| recipient_name | recipient_name | String | Trim |
| recipient_uei | recipient_uei | String | Uppercase, 12-char |
| Key Subcontractors | key_subcontractors | String[] | Split by comma, trim |
| Known Subcontractors | known_subcontractors | String[] | Split by comma/pipe, trim |
| Period of Performance | period_of_performance | String | Keep as-is |
| PoP Start, period_start, start_date | pop_start | Date | Parse YYYY-MM-DD |
| PoP End, period_end, end_date | pop_end | Date | Parse YYYY-MM-DD |
| PoP Start (Consolidated) | pop_start_consolidated | Date | Parse YYYY-MM-DD |
| PoP End (Consolidated) | pop_end_consolidated | Date | Parse YYYY-MM-DD |
| ultimate_completion, Ultimate Completion Date (FPDS) | ultimate_completion | Date | Parse YYYY-MM-DD |
| Recompete Date | recompete_date | Date | Parse YYYY-MM-DD |
| Key Locations | key_locations | String[] | Split by comma, trim |
| Performance Location (TANGO) | performance_location_tango | String | Trim |
| Performance Location (FPDS) | performance_location_fpds | String | Trim |
| pop_city | pop_city | String | Title case |
| pop_state | pop_state | String | Uppercase, 2-letter |
| pop_zip | pop_zip | String | 5-digit |
| pop_country | pop_country | String | Default: US |
| NAICS Code (Consolidated), naics_code | naics_code | String | 6-digit |
| FPDS NAICS Code | fpds_naics_code | String | 6-digit |
| NAICS Description | naics_description | String | Trim |
| PSC Code (Consolidated), psc_code | psc_code | String | 4-char |
| FPDS PSC Code | fpds_psc_code | String | 4-char |
| PSC Description | psc_description | String | Trim |
| set_aside | set_aside | String | Partial/Full |
| Technical Stack | technical_stack | String | Trim |
| Tech Stack (Basic) | tech_stack_basic | String[] | Split by comma, trim |
| Keywords/Signals | keywords_signals | String[] | Split by comma, trim |
| Functional Areas | functional_areas | String[] | Split by comma, trim |
| Typical Roles | typical_roles | String[] | Split by comma, trim |
| Job Titles | job_titles | String[] | Split by comma, trim |
| Labor Rate Min | labor_rate_min | Decimal | Parse currency |
| Labor Rate Max | labor_rate_max | Decimal | Parse currency |
| Labor Rate Average | labor_rate_average | Decimal | Parse currency |
| Education Requirement | education_requirement | String | Trim |
| Experience Requirement | experience_requirement | String | Trim |
| Annual Salary Range | annual_salary_range | String | Trim |
| Clearance Requirements | clearance_requirements | String[] | Split by comma, trim |
| Security Requirements | security_requirements | String | Trim |
| Contract Vehicle Used | contract_vehicle_used | String | Trim |
| Contract Vehicle/Type | contract_vehicle_type | String | Trim |
| awarding_office | awarding_office | String | Trim |
| awarding_agency | awarding_agency | String | Trim |
| funding_office | funding_office | String | Trim |
| COR/COTR | cor_cotr | String | Trim |
| Program Manager | program_manager | String | Trim |
| Match Confidence | match_confidence | String | High/Medium/Low |
| Match Score | match_score | Integer | 0-100 |
| Incumbent Score | incumbent_score | Integer | 0-100 |
| Source Evidence | source_evidence | String | Trim |
| Notes | notes | String | Trim |
| Pain Points | pain_points | String | Trim |
| Related Jobs | related_jobs | String[] | Split by comma, trim |
| tango_description | tango_description | String | Trim |
| parent_description | parent_description | String | Trim |
| Budget | budget | Decimal | Parse currency |
| CALC API Status | calc_api_status | String | Trim |
| job_count, total_jobs | job_count | Integer | Cast to int |
| contact_count | contact_count | Integer | Cast to int |
| total_placements | placement_count | Integer | Cast to int |
| total_revenue | total_revenue | Decimal | Parse currency |
| hiring_velocity, Hiring Velocity | hiring_velocity | String | High/Medium/Low/None |
| status | status | String | Trim |
| description | description | String | Trim |
| created_at | created_at | DateTime | Parse ISO 8601 |
| updated_at | updated_at | DateTime | Parse ISO 8601 |

#### Job Property Mappings

| Source Column(s) | Schema Property | Data Type | Transformation |
|------------------|-----------------|-----------|----------------|
| id, bullhorn_job_id | job_id | String | UUID or Bullhorn ID |
| job_number, Job Number | job_number | String | Trim |
| title, Job Title, jobTitle | title | String | Trim |
| description | description | String | Trim, preserve formatting |
| company, client_corporation | company | String | Trim, standardize |
| location, Job Location, jobLocation | location | String | Trim |
| city | city | String | Title case |
| state | state | String | Uppercase, 2-letter |
| clearance, Security Clearance, clearance_required | clearance_required | String | Standardize levels |
| employment_type, Employment Type, jobType | employment_type | String | Contract/Full-Time/etc. |
| status | status | String | Open/Closed/Filled/enriched |
| pay_rate, payRate | pay_rate | Decimal | Parse currency |
| bill_rate | bill_rate | Decimal | Parse currency |
| salary | salary | Decimal | Parse currency |
| perm_fee_percent | perm_fee_percent | Integer | Cast to int |
| duration | duration | String | Trim |
| date_posted, Date Posted, datePosted | date_posted | Date | Parse YYYY-MM-DD |
| date_added | date_added | DateTime | Parse ISO 8601 |
| date_modified | date_modified | DateTime | Parse ISO 8601 |
| date_closed | date_closed | DateTime | Parse ISO 8601 |
| scraped_at, Scraped At, scrapedAt | scraped_at | DateTime | Parse ISO 8601 |
| source, Job Source | source | String | Apex/Insight/clearancejobs/etc. |
| url, Job URL, jobUrl | url | String | Validate URL |
| matched_program, Matched Program | matched_program | String | Trim |
| program_acronym, Program Acronym | program_acronym | String | Uppercase |
| program_agency, Program Agency | program_agency | String | Trim |
| prime_contractor, Prime Contractor, prime | prime_contractor | String | Trim, standardize |
| program_location, Program Location | program_location | String | Trim |
| contract_number, Contract Number | contract_number | String | Trim |
| task_order | task_order | String | Trim |
| match_score, Match Score | match_score | Integer | 0-100 |
| match_confidence, Match Confidence | match_confidence | String | Low/Medium/High |
| Match Type | match_type | String | Trim |
| match_reasons, Match Reasons | match_reasons | String | Trim |
| Match Signals | match_signals | String | Trim |
| Secondary Candidates | secondary_candidates | String[] | Split by comma |
| BD Priority Score, bd_score | bd_priority_score | Integer | 0-100 |
| priority_tier, Priority Tier | priority_tier | String | Extract emoji + text |
| base_score | base_score | Integer | Default: 50 |
| clearance_boost | clearance_boost | Integer | 0-25 |
| program_boost | program_boost | Integer | Calculated |
| location_boost | location_boost | Integer | 0-10 |
| confidence_boost | confidence_boost | Integer | 0-10 |
| recency_boost | recency_boost | Integer | Calculated |
| pain_point_boost | pain_point_boost | Integer | Calculated |
| tier_multiplier | tier_multiplier | Float | Default: 1.0 |
| Recommendations | recommendations | String[] | Split by comma |
| Primary Contact | primary_contact | String | Trim |
| Contact Title | contact_title | String | Trim |
| Contact Tier | contact_tier | Integer | 1-6 |
| Contact Email | contact_email | String | Lowercase, trim |
| Matched Contacts Count | matched_contacts_count | Integer | Cast to int |
| skills | skills | String[] | Split by comma, trim |
| technologies, required_technologies | technologies | String[] | Split by comma, trim |
| certifications_required | certifications_required | String[] | Split by comma, trim |
| certifications_extra | certifications_extra | String[] | Split by comma, trim |
| experience_years | experience_years | Integer | Cast to int |
| hiring_leader | hiring_leader | String | Trim |
| program_manager | program_manager | String | Trim |
| pts_past_programs | pts_past_programs | String[] | Array |
| pts_past_jobs | pts_past_jobs | String[] | Array |
| pts_past_contractors | pts_past_contractors | String[] | Array |
| pts_past_contacts | pts_past_contacts | String[] | Array |
| owner, contact | owner | String | Trim |
| custom_text1 | custom_text1 | String | Trim |
| custom_text2 | custom_text2 | String | Trim |
| custom_text3 | custom_text3 | String | Trim |
| source_file | source_file | String | Trim |
| created_at | created_at | DateTime | Parse ISO 8601 |
| updated_at | updated_at | DateTime | Parse ISO 8601 |

---

## STANDARDIZATION RULES

### 1. Naming Conventions

**Node Labels:**
- Use UPPER_SNAKE_CASE for node labels (e.g., `CONTACT`, `FEDERAL_PROGRAM`)
- Singular form (not plural)

**Relationship Types:**
- Use UPPER_SNAKE_CASE for relationship types (e.g., `WORKS_FOR`, `PRIMED_BY`)
- Active verb form

**Properties:**
- Use lower_snake_case for property names (e.g., `first_name`, `contract_value`)
- Descriptive names, avoid abbreviations unless industry-standard

**IDs:**
- Primary keys: `{node_type}_id` (e.g., `contact_id`, `program_id`)
- Use UUIDs for new records
- Preserve existing IDs from source systems (Bullhorn, Notion, etc.)

### 2. Data Type Standards

**Strings:**
- Trim whitespace
- Standardize casing (title case for names, uppercase for codes)
- Maximum length: 500 chars for short text, TEXT for long content

**Numbers:**
- Integers: Cast to int, no decimals
- Decimals: Use Decimal type with 2-4 decimal places
- Currency: Store as Decimal, not float (avoid rounding errors)

**Dates/Times:**
- Dates: ISO 8601 format (YYYY-MM-DD)
- DateTimes: ISO 8601 with timezone (YYYY-MM-DDTHH:MM:SSZ)
- Always store in UTC

**Booleans:**
- True/False only
- Convert: Yes → true, No → false

**Arrays:**
- Store as arrays/lists in Neo4j
- Delimiter in source: comma or pipe → split and trim
- No nested arrays

**JSON:**
- Use sparingly for unstructured metadata
- Prefer typed properties when possible

### 3. Clearance Level Standardization

**Standard Levels (ranked):**
1. None
2. Public Trust
3. Secret
4. Top Secret
5. TS/SCI
6. TS/SCI with CI Poly
7. TS/SCI with Full Scope Polygraph

**Mapping Rules:**
- "Active Secret" → "Secret"
- "TS/SCI w/ Poly" → "TS/SCI with CI Poly" or "TS/SCI with Full Scope Polygraph" (disambiguate)
- "Top Secret/SCI" → "TS/SCI"

### 4. Contractor Name Standardization

**Standard Names:**
- General Dynamics Information Technology → GDIT
- Northrop Grumman Corporation → Northrop Grumman
- Booz Allen Hamilton Inc. → Booz Allen Hamilton
- Science Applications International Corporation → SAIC
- Lockheed Martin Corporation → Lockheed Martin
- Raytheon Technologies Corporation → Raytheon
- L3Harris Technologies, Inc. → L3Harris

**Rules:**
- Remove legal suffixes (Inc., LLC, Corporation, Corp.)
- Use common acronyms where applicable
- Store full legal name in `legal_name` property

### 5. Location Standardization

**Format:**
- City: Title case (e.g., "Fort Meade", not "FORT MEADE")
- State: 2-letter uppercase code (e.g., "MD", not "Maryland")
- Country: ISO 3166-1 alpha-2 code (e.g., "US")

**Special Cases:**
- "Washington DC" → city: "Washington", state: "DC"
- "APO/FPO" → handle as special military postal codes

### 6. Currency Standardization

**Format:**
- Store as Decimal without currency symbol
- Always USD unless otherwise noted
- Parsing: "$1.2B" → 1200000000.00, "$47.5M" → 47500000.00

**Abbreviations:**
- K = 1,000
- M = 1,000,000
- B = 1,000,000,000

### 7. Priority/Tier Standardization

**Contact Tiers:**
- Tier 1: Key Decision Makers (C-level, VPs, Directors)
- Tier 2: Managers (Program Managers, Site Leads)
- Tier 3: Senior ICs (Senior Engineers, Architects, Leads)
- Tier 4: Mid-level ICs
- Tier 5: Junior ICs
- Tier 6: Support Staff

**BD Priority:**
- 🔴 Critical (score 90-100)
- 🟠 High (score 70-89)
- 🟡 Medium (score 50-69)
- ⚪ Low (score 0-49)

**Priority Tier (Jobs/Opportunities):**
- 🔥 Hot (score ≥ 85)
- 🟡 Warm (score 50-84)
- ❄️ Cold (score < 50)

### 8. Missing Data Handling

**Nullability:**
- Use NULL for missing values, not empty strings
- Do not use "N/A", "Unknown", "TBD" as values

**Required Fields:**
- All `_id` primary keys: NOT NULL
- Names (program_name, full_name, etc.): NOT NULL
- Dates can be NULL if unknown

**Default Values:**
- Booleans: Default to false if unknown
- Scores: No default (NULL if not calculated)
- Timestamps: created_at auto-populated, updated_at NULL until updated

---

## DATA MIGRATION GUIDE

### Phase 1: Data Extraction

**Sources:**
1. **Bullhorn SQLite DB** (`bullhorn_master.db` - 293 MB)
   - Extract tables: candidates, call_notes, activities, placements, jobs, prime_contractors, programs
   - Tool: SQLite3 or pandas

2. **CSV Files**
   - Engine2: Federal Programs MASTER ENRICHED.csv (89 columns)
   - Engine3: Prime_Contacts_Enriched/*.csv (45 files)
   - Dashboard: contacts_classified.json, jobs_enriched.json, programs_enriched.json

3. **JSON Files**
   - outputs/all_jobs_fully_enriched.json
   - dashboard/mindmap_nodes.json, mindmap_edges.json

4. **Qdrant Vector Store**
   - Export collections: jobs (531), contacts (7,337), programs (401), documents (205), activities (500)
   - Preserve embeddings for semantic search

### Phase 2: Data Transformation

**Tools:**
- Python pandas for CSV/JSON processing
- Custom ETL scripts per entity type

**Steps:**
1. **Deduplicate records**
   - Contact: Match by email (primary) or name + company
   - Program: Match by piid or program_name + agency
   - Contractor: Match by UEI or CAGE code

2. **Standardize values**
   - Apply clearance level mapping
   - Normalize contractor names
   - Parse currency values
   - Convert dates to ISO 8601

3. **Enrich relationships**
   - Extract contact → program links from call notes
   - Build contractor → program links from prime/sub fields
   - Link jobs → programs via matched_program field

4. **Generate IDs**
   - Create UUIDs for nodes without existing IDs
   - Preserve Bullhorn IDs, Notion IDs where present

### Phase 3: Neo4j Import

**Method 1: LOAD CSV (recommended for initial load)**

```cypher
// Create constraints first
CREATE CONSTRAINT contact_id IF NOT EXISTS FOR (c:CONTACT) REQUIRE c.contact_id IS UNIQUE;
CREATE CONSTRAINT program_id IF NOT EXISTS FOR (p:PROGRAM) REQUIRE p.program_id IS UNIQUE;
CREATE CONSTRAINT job_id IF NOT EXISTS FOR (j:JOB) REQUIRE j.job_id IS UNIQUE;
CREATE CONSTRAINT contractor_id IF NOT EXISTS FOR (c:CONTRACTOR) REQUIRE c.contractor_id IS UNIQUE;

// Create indexes
CREATE INDEX contact_email IF NOT EXISTS FOR (c:CONTACT) ON (c.email);
CREATE INDEX contact_tier IF NOT EXISTS FOR (c:CONTACT) ON (c.tier);
CREATE INDEX program_acronym IF NOT EXISTS FOR (p:PROGRAM) ON (p.acronym);
CREATE INDEX job_clearance IF NOT EXISTS FOR (j:JOB) ON (j.clearance_required);

// Load nodes
LOAD CSV WITH HEADERS FROM 'file:///contacts.csv' AS row
CREATE (c:CONTACT {
  contact_id: row.contact_id,
  first_name: row.first_name,
  last_name: row.last_name,
  full_name: row.full_name,
  email: row.email,
  // ... all properties
});

// Load relationships
LOAD CSV WITH HEADERS FROM 'file:///contact_works_for_contractor.csv' AS row
MATCH (c:CONTACT {contact_id: row.contact_id})
MATCH (co:CONTRACTOR {contractor_id: row.contractor_id})
CREATE (c)-[:WORKS_FOR {
  role: row.role,
  start_date: date(row.start_date)
}]->(co);
```

**Method 2: Neo4j Admin Import (fastest for bulk loads)**

```bash
neo4j-admin database import full \
  --nodes=Contact=contacts-header.csv,contacts-data.csv \
  --nodes=Program=programs-header.csv,programs-data.csv \
  --relationships=WORKS_FOR=works_for-header.csv,works_for-data.csv \
  --delimiter="," \
  --array-delimiter=";" \
  neo4j
```

**Method 3: Python neo4j driver (programmatic)**

```python
from neo4j import GraphDatabase
import pandas as pd

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

def create_contact(tx, row):
    tx.run(
        """
        CREATE (c:CONTACT {
            contact_id: $contact_id,
            first_name: $first_name,
            last_name: $last_name,
            email: $email,
            tier: $tier
        })
        """,
        contact_id=row['contact_id'],
        first_name=row['first_name'],
        last_name=row['last_name'],
        email=row['email'],
        tier=row['tier']
    )

with driver.session() as session:
    df = pd.read_csv('contacts.csv')
    for _, row in df.iterrows():
        session.write_transaction(create_contact, row)
```

### Phase 4: Vector Embedding Migration

**Preserve Qdrant embeddings in Neo4j:**

1. **Export embeddings from Qdrant**
```python
from qdrant_client import QdrantClient
client = QdrantClient(url="http://localhost:6333")

contacts = client.scroll(collection_name="contacts", limit=10000)
# Save: contact_id, vector (384-dim or 1536-dim), payload
```

2. **Store embeddings in Neo4j**
```cypher
// Add vector property to nodes
MATCH (c:CONTACT {contact_id: $contact_id})
SET c.embedding_384 = $embedding_vector;
```

3. **Use Neo4j Vector Index (if available)**
```cypher
CREATE VECTOR INDEX contact_embedding IF NOT EXISTS
FOR (c:CONTACT) ON (c.embedding_384)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine'
  }
};
```

### Phase 5: Validation

**Data Quality Checks:**

1. **Node counts**
```cypher
MATCH (c:CONTACT) RETURN count(c); // Should be ~7,339
MATCH (p:PROGRAM) RETURN count(p); // Should be ~401
MATCH (j:JOB) RETURN count(j); // Should be ~531
```

2. **Relationship counts**
```cypher
MATCH ()-[r:WORKS_ON]->() RETURN count(r); // Should be ~1,142
MATCH ()-[r:MEMBER_OF]->() RETURN count(r); // Should be ~1,137
```

3. **Orphan detection**
```cypher
// Find contacts with no relationships
MATCH (c:CONTACT)
WHERE NOT (c)-[]-()
RETURN count(c);
```

4. **Data integrity**
```cypher
// Find missing required fields
MATCH (c:CONTACT)
WHERE c.full_name IS NULL OR c.contact_id IS NULL
RETURN c;
```

### Phase 6: Optimization

**Performance tuning:**

1. **Create composite indexes for common queries**
```cypher
CREATE INDEX contact_company_tier IF NOT EXISTS
FOR (c:CONTACT) ON (c.current_employer, c.tier);
```

2. **Add full-text search indexes**
```cypher
CREATE FULLTEXT INDEX program_search IF NOT EXISTS
FOR (p:PROGRAM) ON EACH [p.program_name, p.acronym, p.description];
```

3. **Warm up caches**
```cypher
// Pre-load frequent query patterns
MATCH (c:CONTACT)-[r:WORKS_ON]->(p:PROGRAM)
RETURN count(r);
```

---

## APPENDIX: SAMPLE QUERIES

### Find Top BD Opportunities

```cypher
MATCH (j:JOB)-[:MATCHED_TO]->(p:PROGRAM)
WHERE j.bd_priority_score > 85
  AND j.clearance_required IN ['TS/SCI', 'TS/SCI with CI Poly']
RETURN j.title, p.program_name, j.bd_priority_score, j.location
ORDER BY j.bd_priority_score DESC
LIMIT 10;
```

### Contact Network Analysis

```cypher
MATCH (c:CONTACT)-[:WORKS_ON]->(p:PROGRAM)<-[:WORKS_ON]-(c2:CONTACT)
WHERE c.tier = 1
  AND c2.tier <= 2
RETURN c.full_name AS decision_maker,
       p.program_name,
       collect(DISTINCT c2.full_name) AS team_members
ORDER BY size(collect(c2)) DESC;
```

### Program Intelligence Report

```cypher
MATCH (p:PROGRAM {acronym: 'DCGS'})
OPTIONAL MATCH (p)<-[:PRIMED_BY]-(prime:CONTRACTOR)
OPTIONAL MATCH (p)<-[:WORKS_ON]-(c:CONTACT)
OPTIONAL MATCH (p)<-[:MATCHED_TO]-(j:JOB)
RETURN p.program_name AS program,
       p.contract_value AS value,
       prime.name AS prime_contractor,
       count(DISTINCT c) AS contacts,
       count(DISTINCT j) AS open_jobs;
```

### Gap Analysis - Staffing Shortfalls

```cypher
MATCH (p:PROGRAM)
OPTIONAL MATCH (p)<-[:MATCHED_TO]-(j:JOB)
WHERE j.status = 'Open'
WITH p, count(j) AS open_jobs
WHERE open_jobs > 5
RETURN p.program_name,
       p.prime_contractor,
       open_jobs,
       p.hiring_velocity
ORDER BY open_jobs DESC;
```

### Relationship Path Analysis

```cypher
MATCH path = shortestPath(
  (c:CONTACT {tier: 1})-[*..4]-(target:CONTACT {full_name: 'Target Person'})
)
RETURN [node IN nodes(path) | node.full_name] AS connection_path,
       length(path) AS degrees_of_separation;
```

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-11 | Initial schema definition from comprehensive audit |

---

**End of Master Property Architecture Schema**
