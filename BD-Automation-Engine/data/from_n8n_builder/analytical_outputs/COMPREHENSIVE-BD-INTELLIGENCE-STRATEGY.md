# Comprehensive BD Intelligence Strategy
## Federal Contract and Program Data Model

**Generated:** 2026-01-21
**Purpose:** Map all available USASpending.gov data fields to Business Development intelligence requirements

---

## Executive Summary

This document provides a complete analysis of **500+ data fields** available from USASpending.gov and related federal data sources. It maps these fields to specific BD intelligence needs and provides a comprehensive strategy for extracting competitive intelligence faster than competitors.

---

## Part 1: Complete Data Field Inventory

### 1.1 Prime Contract Data (FPDS Transaction Model)
**Source:** USASpending API `/api/v2/transactions/` and `/api/v2/awards/`
**Total Fields:** 350+

#### Contract Identifiers
| Field | Description | BD Value |
|-------|-------------|----------|
| `piid` | Procurement Instrument Identifier | Primary contract ID for tracking |
| `award_id` | Generated unique award ID | USASpending link key |
| `unique_award_key` | Internal unique key | Cross-referencing |
| `parent_award_id` | Parent IDV contract | Task order relationship |
| `solicitation_identifier` | RFP/RFQ number | Track from opportunity to award |
| `program_acronym` | Program short name | Program identification |
| `major_program` | Major acquisition program | MDAP tracking |

#### Financial Data
| Field | Description | BD Value |
|-------|-------------|----------|
| `federal_action_obligation` | Current transaction amount | Transaction tracking |
| `total_obligated_amount` | Total obligated to date | Current spend |
| `base_exercised_options_val` | Base + exercised options | Funded ceiling |
| `base_and_all_options_value` | Total potential value | Contract ceiling |
| `potential_total_value_awar` | Max contract value | Full opportunity size |
| `current_total_value_award` | Current ceiling | Growth tracking |

#### Vendor/Recipient Intelligence
| Field | Description | BD Value |
|-------|-------------|----------|
| `awardee_or_recipient_uei` | Unique Entity ID | Primary vendor ID |
| `awardee_or_recipient_legal` | Legal entity name | Vendor identification |
| `vendor_doing_as_business_n` | DBA name | Trade name |
| `ultimate_parent_uei` | Parent company UEI | Corporate hierarchy |
| `ultimate_parent_legal_enti` | Parent company name | Parent identification |
| `cage_code` | CAGE code | DoD vendor code |
| `vendor_phone_number` | Vendor phone | Direct contact |
| `vendor_fax_number` | Vendor fax | Contact method |

#### Recipient Location (Full Address)
| Field | Description | BD Value |
|-------|-------------|----------|
| `legal_entity_address_line1` | Street address | Office location |
| `legal_entity_city_name` | City | Geographic analysis |
| `legal_entity_state_code` | State | Regional targeting |
| `legal_entity_county_name` | County | Local presence |
| `legal_entity_zip5` | ZIP code | Precise location |
| `legal_entity_congressional` | Congressional district | Political mapping |
| `legal_entity_country_code` | Country | International vs domestic |

#### Place of Performance
| Field | Description | BD Value |
|-------|-------------|----------|
| `place_of_perform_city_name` | Work site city | Where work happens |
| `place_of_performance_state` | Work site state | Regional work |
| `place_of_perform_county_na` | Work site county | Precise location |
| `place_of_performance_zip5` | Work site ZIP | Team location |
| `place_of_performance_congr` | Congressional district | Political mapping |

#### Contract Classification
| Field | Description | BD Value |
|-------|-------------|----------|
| `naics` | NAICS code | Industry classification |
| `naics_description` | NAICS description | Work type |
| `product_or_service_code` | PSC code | Specific service type |
| `product_or_service_co_desc` | PSC description | Service details |
| `dod_claimant_program_code` | DoD program code | Defense program |
| `dod_claimant_prog_cod_desc` | Program description | Program details |

#### Competition & Set-Aside
| Field | Description | BD Value |
|-------|-------------|----------|
| `extent_competed` | Competition level | Competitive vs sole source |
| `extent_compete_description` | Competition description | How it was awarded |
| `type_set_aside` | Set-aside type | Small business designation |
| `type_set_aside_description` | Set-aside description | SB category |
| `number_of_offers_received` | # of offers | Competition level |
| `evaluated_preference` | Evaluation preference | Preference programs |

#### Contract Characteristics
| Field | Description | BD Value |
|-------|-------------|----------|
| `type_of_contract_pricing` | Pricing type | FFP, T&M, CPFF, etc. |
| `type_of_contract_pric_desc` | Pricing description | Contract structure |
| `idv_type` | IDV type | GWAC, IDIQ, BPA, etc. |
| `idv_type_description` | IDV description | Vehicle type |
| `multi_year_contract` | Multi-year flag | Long-term contracts |
| `subcontracting_plan` | Subcontracting plan | Sub opportunities |
| `consolidated_contract` | Consolidation flag | Bundled contracts |
| `performance_based_service` | PBA flag | Performance-based |

#### Dates & Timeline
| Field | Description | BD Value |
|-------|-------------|----------|
| `action_date` | Transaction date | Activity timing |
| `period_of_performance_star` | PoP start | Contract start |
| `period_of_performance_curr` | Current PoP end | Contract end |
| `period_of_perf_potential_e` | Potential PoP end | Max end date |
| `ordering_period_end_date` | Last date to order | IDV ordering window |
| `solicitation_date` | Solicitation date | RFP timing |

#### Agency Information
| Field | Description | BD Value |
|-------|-------------|----------|
| `awarding_agency_code` | Awarding agency code | Agency tracking |
| `awarding_agency_name` | Awarding agency name | Customer ID |
| `awarding_sub_tier_agency_c` | Sub-tier code | Component agency |
| `awarding_sub_tier_agency_n` | Sub-tier name | Component details |
| `awarding_office_code` | Office code | Contracting office |
| `awarding_office_name` | Office name | PCO location |
| `funding_agency_code` | Funding agency code | Who pays |
| `funding_agency_name` | Funding agency name | Funding source |
| `funding_office_code` | Funding office code | Budget office |
| `funding_office_name` | Funding office name | Budget details |

#### Business Type Flags (100+ Boolean Fields)
**Critical for targeting small business opportunities:**

| Category | Fields | BD Value |
|----------|--------|----------|
| **Veteran-Owned** | `veteran_owned_business`, `service_disabled_veteran_o` | SDVOSB targeting |
| **Woman-Owned** | `woman_owned_business`, `women_owned_small_business`, `economically_disadvantaged` | WOSB/EDWOSB targeting |
| **Minority-Owned** | `minority_owned_business`, `black_american_owned_busin`, `hispanic_american_owned_bu`, `asian_pacific_american_own`, `subcontinent_asian_asian_i`, `native_american_owned_busi` | 8(a)/MBE targeting |
| **Small Business** | `small_disadvantaged_busine`, `c8a_program_participant`, `historically_underutilized` | SDB/HUBZone targeting |
| **Educational** | `educational_institution`, `historically_black_college`, `minority_institution` | Academic partners |
| **Non-Profit** | `nonprofit_organization`, `foundation`, `hospital_flag` | Non-profit partners |
| **Government** | `us_federal_government`, `us_state_government`, `us_local_government`, `us_tribal_government` | Government partners |

#### Highly Compensated Officers
**Critical for executive intelligence:**

| Field | Description | BD Value |
|-------|-------------|----------|
| `officer_1_name` | Top executive name | Leadership ID |
| `officer_1_amount` | Top executive compensation | Salary level |
| `officer_2_name` through `officer_5_name` | Executives 2-5 | Leadership team |
| `officer_2_amount` through `officer_5_amount` | Compensation 2-5 | Salary levels |

---

### 1.2 Sub-Award Data
**Source:** USASpending API `/api/v2/subawards/`
**Total Fields:** 248+

#### Prime Award Reference
| Field | Description | BD Value |
|-------|-------------|----------|
| `prime_award_unique_key` | Prime award ID | Link to prime |
| `prime_award_piid` | Prime PIID | Prime contract # |
| `prime_award_amount` | Prime total value | Prime size |
| `prime_awardee_uei` | Prime UEI | Prime vendor |
| `prime_awardee_name` | Prime name | Prime company |

#### Subawardee Information
| Field | Description | BD Value |
|-------|-------------|----------|
| `subawardee_uei` | Subcontractor UEI | Sub vendor ID |
| `subawardee_name` | Subcontractor name | Sub company |
| `subawardee_dba_name` | Sub DBA name | Trade name |
| `subawardee_parent_uei` | Sub parent UEI | Sub parent company |
| `subawardee_parent_name` | Sub parent name | Corporate hierarchy |

#### Subaward Details
| Field | Description | BD Value |
|-------|-------------|----------|
| `subaward_number` | Subaward number | Sub contract # |
| `subaward_amount` | Subaward value | Sub contract size |
| `subaward_action_date` | Subaward date | Timing |
| `subaward_description` | Work description | Sub scope |
| `subaward_type` | Type (sub-contract/sub-grant) | Classification |

#### Subawardee Location
| Field | Description | BD Value |
|-------|-------------|----------|
| `subawardee_city_name` | Sub city | Sub location |
| `subawardee_state_code` | Sub state | Sub region |
| `subawardee_zip_code` | Sub ZIP | Sub address |
| `subaward_recipient_cd_original` | Congressional district | Political mapping |

#### Subaward Place of Performance
| Field | Description | BD Value |
|-------|-------------|----------|
| `subaward_primary_place_of_performance_city_name` | Work city | Where sub works |
| `subaward_primary_place_of_performance_state_code` | Work state | Work region |
| `subaward_primary_place_of_performance_zip` | Work ZIP | Precise location |

#### Subawardee Executives
| Field | Description | BD Value |
|-------|-------------|----------|
| `subawardee_highly_compensated_officer_1_name` | Sub executive 1 | Sub leadership |
| `subawardee_highly_compensated_officer_1_amount` | Sub exec 1 comp | Sub salary |
| (through officer 5) | | |

---

### 1.3 Federal Account Funding Data
**Source:** USASpending Downloads and API
**Total Fields:** 82+

#### Budget Structure
| Field | Description | BD Value |
|-------|-------------|----------|
| `treasury_account_symbol` | TAS code | Budget account |
| `federal_account_symbol` | Federal account | Funding line |
| `budget_function` | Budget function | Defense/Non-defense |
| `budget_subfunction` | Budget subfunction | Program area |
| `program_activity_code` | Program activity | Specific program |
| `program_activity_name` | Activity name | What it funds |
| `object_class_code` | Object class | Spending category |
| `object_class_name` | Object class name | Category description |

#### Funding Amounts
| Field | Description | BD Value |
|-------|-------------|----------|
| `transaction_obligated_amount` | Obligated amount | What's funded |
| `gross_outlay_amount` | Outlayed amount | What's spent |

---

### 1.4 Lookup/Reference Tables (DIIG-CSIS)
**Source:** CSIS Lookup Tables Repository
**Critical for classification:**

| Table | Fields | BD Value |
|-------|--------|----------|
| `ProductOrServiceCodes.csv` | PSC hierarchy, DoD portfolio, platform | Service classification |
| `PrincipalNaicsCode.csv` | NAICS hierarchy, industry categories | Industry targeting |
| `Agency_AgencyID.csv` | Agency codes, customers, defense flag | Customer mapping |
| `ContractActionType.csv` | Action types | Modification tracking |
| `ExtentCompleted.csv` | Competition codes | Competition analysis |
| `CompetitionClassification.csv` | Competition categories | Competitive landscape |

---

## Part 2: BD Intelligence Requirements Mapping

### 2.1 Program Intelligence Requirements

| Intelligence Need | Primary Data Fields | Source |
|-------------------|---------------------|--------|
| **Program Name** | `award_description`, `program_acronym`, `major_program`, `program_activity_name` | FPDS, Funding |
| **Contract Value** | `base_and_all_options_value`, `potential_total_value_awar` | FPDS |
| **Current Spend** | `total_obligated_amount`, `federal_action_obligation` | FPDS |
| **Prime Contractor** | `awardee_or_recipient_legal`, `ultimate_parent_legal_enti` | FPDS |
| **Primary Location** | `place_of_perform_city_name`, `place_of_performance_state` | FPDS |
| **Work Sites** | Sub-award places of performance | Subawards |
| **Contract End Date** | `period_of_performance_curr`, `ordering_period_end_date` | FPDS |
| **NAICS/PSC** | `naics`, `product_or_service_code` | FPDS |

### 2.2 Competitor Intelligence Requirements

| Intelligence Need | Primary Data Fields | Source |
|-------------------|---------------------|--------|
| **Who's on the Contract** | `awardee_or_recipient_legal`, `subawardee_name` | FPDS, Subawards |
| **Contract Value by Vendor** | `subaward_amount`, `total_obligated_amount` | Both |
| **Team Structure** | Prime + all subawardees | Both |
| **Where They Work** | `place_of_perform_city_name`, subaward POPs | Both |
| **Key Personnel** | `officer_1_name` through `officer_5_name` | FPDS |
| **Business Size** | All business type flags | FPDS |
| **Growth Trajectory** | Transaction history by vendor | FPDS Transactions |

### 2.3 Task Order Intelligence

| Intelligence Need | Primary Data Fields | Source |
|-------------------|---------------------|--------|
| **Parent IDV** | `parent_award_id`, `idv_type` | FPDS |
| **Task Orders** | Child awards via IDV endpoint | USASpending IDV API |
| **Task Order Value** | Child award `obligated_amount` | IDV Awards |
| **Task Order Locations** | Child award place of performance | IDV Awards |
| **Task Order Performers** | Child award recipient info | IDV Awards |

### 2.4 Technology/Skills Intelligence

| Intelligence Need | Data Source | Extraction Method |
|-------------------|-------------|-------------------|
| **Technologies Used** | `award_description`, job postings | Keyword extraction |
| **Skills Required** | Job posting descriptions | NLP parsing |
| **Security Clearances** | Job posting requirements | Pattern matching |
| **Certifications** | Job requirements, contract description | Keyword extraction |

### 2.5 Organizational Intelligence

| Intelligence Need | Primary Data Fields | Source |
|-------------------|---------------------|--------|
| **Executive Names** | `officer_1_name` - `officer_5_name` | FPDS |
| **Executive Compensation** | `officer_1_amount` - `officer_5_amount` | FPDS |
| **Prime-Sub Relationships** | Subaward linkages | Subawards |
| **Corporate Hierarchy** | `ultimate_parent_uei`, `ultimate_parent_legal_enti` | FPDS |
| **Sub Executive Names** | `subawardee_highly_compensated_officer_*_name` | Subawards |

---

## Part 3: Comprehensive Data Structure

### 3.1 Master Program Record Schema

```python
@dataclass
class FederalProgramIntelligence:
    """Complete intelligence profile for a federal program/contract."""

    # === IDENTIFIERS ===
    program_id: str                    # Internal unique ID
    award_id: str                      # USASpending award ID
    piid: str                          # PIID
    parent_award_id: Optional[str]     # Parent IDV PIID
    solicitation_id: Optional[str]     # Original solicitation

    # === PROGRAM INFO ===
    program_name: str                  # Derived/extracted name
    program_acronym: Optional[str]     # Official acronym
    description: str                   # Award description
    major_program: Optional[str]       # MDAP designation

    # === FINANCIAL ===
    contract_ceiling: float            # base_and_all_options_value
    obligated_amount: float            # total_obligated_amount
    annual_funding: float              # Calculated annual average
    growth_rate: float                 # YoY growth %

    # === PRIME CONTRACTOR ===
    prime_contractor: str              # awardee_or_recipient_legal
    prime_uei: str                     # awardee_or_recipient_uei
    prime_parent: Optional[str]        # ultimate_parent_legal_enti
    prime_parent_uei: Optional[str]    # ultimate_parent_uei
    prime_cage_code: Optional[str]     # cage_code
    prime_phone: Optional[str]         # vendor_phone_number
    prime_business_types: List[str]    # Extracted from boolean flags

    # === PRIME EXECUTIVES ===
    prime_executives: List[Dict]       # officer_1-5 name/amount

    # === AGENCY ===
    awarding_agency: str               # awarding_agency_name
    awarding_sub_agency: str           # awarding_sub_tier_agency_n
    awarding_office: str               # awarding_office_name
    funding_agency: str                # funding_agency_name
    funding_office: str                # funding_office_name

    # === CLASSIFICATION ===
    naics_code: str                    # naics
    naics_description: str             # naics_description
    psc_code: str                      # product_or_service_code
    psc_description: str               # product_or_service_co_desc
    dod_program_code: Optional[str]    # dod_claimant_program_code

    # === CONTRACT CHARACTERISTICS ===
    contract_type: str                 # D = Definitive, etc.
    pricing_type: str                  # type_of_contract_pricing
    idv_type: Optional[str]            # idv_type (GWAC, BPA, etc.)
    set_aside_type: Optional[str]      # type_set_aside
    competition_type: str              # extent_competed
    number_of_offers: int              # number_of_offers_received

    # === DATES ===
    start_date: date                   # period_of_performance_star
    current_end_date: date             # period_of_performance_curr
    potential_end_date: date           # period_of_perf_potential_e
    ordering_end_date: Optional[date]  # ordering_period_end_date
    last_action_date: date             # Most recent transaction

    # === PRIMARY LOCATION ===
    pop_city: str                      # place_of_perform_city_name
    pop_state: str                     # place_of_performance_state
    pop_county: str                    # place_of_perform_county_na
    pop_zip: str                       # place_of_performance_zip5
    pop_congressional: str             # place_of_performance_congr

    # === TEAM LOCATIONS ===
    team_locations: List[LocationRecord]  # All work sites from subs

    # === SUBCONTRACTORS ===
    subcontractors: List[SubcontractorRecord]
    total_sub_spend: float
    sub_count: int

    # === TASK ORDERS ===
    task_orders: List[TaskOrderRecord]
    total_task_order_value: float
    active_task_orders: int

    # === TECHNOLOGY/SKILLS ===
    technologies: List[str]            # Extracted tech keywords
    skills: List[str]                  # Extracted skill requirements
    clearances: List[str]              # Security clearance levels
    certifications: List[str]          # Required certifications

    # === JOB INTELLIGENCE ===
    open_jobs: List[JobRecord]
    open_job_count: int
    historical_jobs: List[JobRecord]
    hot_hiring: bool                   # Is actively hiring

    # === RECOMPETE INTELLIGENCE ===
    recompete_risk: str               # High/Medium/Low
    recompete_date: Optional[date]    # Estimated recompete
    incumbent_performance: str        # Based on modifications

    # === METADATA ===
    extraction_date: datetime
    data_sources: List[str]
    last_updated: datetime
```

### 3.2 Subcontractor Record Schema

```python
@dataclass
class SubcontractorRecord:
    """Subcontractor intelligence for a prime contract."""

    # === IDENTIFIERS ===
    subaward_id: str
    prime_award_id: str
    subaward_number: str

    # === SUBCONTRACTOR INFO ===
    name: str                          # subawardee_name
    uei: str                           # subawardee_uei
    parent_name: Optional[str]         # subawardee_parent_name
    parent_uei: Optional[str]          # subawardee_parent_uei
    dba_name: Optional[str]            # subawardee_dba_name
    business_types: List[str]          # subawardee_business_types

    # === FINANCIAL ===
    subaward_amount: float             # subaward_amount
    subaward_date: date                # subaward_action_date

    # === LOCATION ===
    city: str
    state: str
    zip_code: str
    congressional_district: str

    # === WORK LOCATION ===
    pop_city: str
    pop_state: str
    pop_zip: str

    # === DESCRIPTION ===
    description: str                   # subaward_description

    # === EXECUTIVES ===
    executives: List[Dict]             # Highly compensated officers
```

### 3.3 Task Order Record Schema

```python
@dataclass
class TaskOrderRecord:
    """Task order under an IDV contract."""

    # === IDENTIFIERS ===
    task_order_id: str
    parent_idv_id: str
    parent_piid: str
    task_order_piid: str

    # === FINANCIAL ===
    obligated_amount: float
    award_amount: float

    # === DATES ===
    start_date: date
    end_date: date

    # === PERFORMER ===
    performer_name: str
    performer_uei: str

    # === LOCATION ===
    pop_city: str
    pop_state: str

    # === DESCRIPTION ===
    description: str

    # === AGENCY ===
    awarding_agency: str
    funding_agency: str
```

---

## Part 4: Data Collection Strategy

### 4.1 Data Sources Priority Matrix

| Source | Data Type | Priority | Update Frequency |
|--------|-----------|----------|------------------|
| USASpending API | Prime contracts, subawards | CRITICAL | Daily |
| USASpending Bulk Downloads | Historical data | HIGH | Weekly |
| SAM.gov API | Entity details, exclusions | HIGH | Weekly |
| Tango API | Enhanced contract data | HIGH | Daily |
| FPDS.gov | Raw contract data | MEDIUM | Real-time |
| Job Boards | Hiring intelligence | MEDIUM | Daily |
| SEC EDGAR | Company filings | LOW | Quarterly |

### 4.2 API Collection Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FEDERAL PROGRAMS DATA PIPELINE                    │
└─────────────────────────────────────────────────────────────────────┘

Phase 1: Contract Discovery
├── USASpending API: /api/v2/search/spending_by_award/
├── Filter: DoD contracts > $100M, IT services NAICS
├── Extract: Award IDs, PIIDs, basic info
└── Output: candidate_contracts.csv

Phase 2: Contract Detail Enrichment
├── For each award_id:
│   ├── USASpending: /api/v2/awards/{id}/
│   ├── Extract: Full contract details
│   └── Extract: Highly compensated officers
├── Tango API: search_tango_contracts
│   └── Enhanced: Additional metadata
└── Output: enriched_contracts.csv

Phase 3: Subaward Collection
├── For each award_id:
│   ├── USASpending: /api/v2/subawards/
│   ├── Extract: All subawardees
│   ├── Extract: Subaward amounts
│   ├── Extract: Subaward locations
│   └── Extract: Sub executive names
└── Output: subawards_by_contract.csv

Phase 4: Task Order Collection
├── For each IDV (CONT_IDV_*):
│   ├── USASpending: /api/v2/idvs/awards/
│   │   ├── type=child_awards
│   │   ├── type=child_idvs
│   │   └── type=grandchild_awards
│   ├── Extract: Task order details
│   └── Extract: Task order performers
└── Output: task_orders_by_idv.csv

Phase 5: Entity Enrichment
├── For each unique UEI:
│   ├── SAM.gov: get_sam_entity_details
│   ├── Extract: Business types
│   ├── Extract: Certifications
│   ├── Extract: Office addresses
│   └── Extract: POC information
└── Output: entity_profiles.csv

Phase 6: Job Intelligence
├── For each program/vendor:
│   ├── Job board scraping
│   ├── Extract: Job titles
│   ├── Extract: Locations
│   ├── Extract: Technologies
│   └── Extract: Clearances
└── Output: job_intelligence.csv

Phase 7: Intelligence Synthesis
├── Merge all data sources
├── Calculate derived metrics
├── Build relationship graphs
├── Score BD targets
└── Output: master_program_intelligence.csv
```

### 4.3 Collection Endpoints Reference

#### USASpending API Endpoints

| Endpoint | Purpose | Key Parameters |
|----------|---------|----------------|
| `/api/v2/search/spending_by_award/` | Search awards | filters, fields, limit |
| `/api/v2/awards/{id}/` | Award details | award_id |
| `/api/v2/transactions/` | Transaction history | award_id |
| `/api/v2/subawards/` | Subaward data | award_id |
| `/api/v2/idvs/awards/` | IDV children | award_id, type |
| `/api/v2/idvs/funding/` | IDV funding | award_id |
| `/api/v2/idvs/amounts/{id}/` | IDV amounts | idv_id |

#### SAM.gov API Endpoints

| Endpoint | Purpose | Key Parameters |
|----------|---------|----------------|
| `/entity-information/v3/entities` | Entity search | ueiSAM, legalBusinessName |
| `/entity-information/v3/exclusions` | Exclusion check | ueiSAM |

#### Tango API Endpoints

| Endpoint | Purpose | Key Parameters |
|----------|---------|----------------|
| `search_tango_contracts` | Contract search | vendor_uei, agency, naics |
| `search_tango_grants` | Grant search | recipient_uei |
| `get_tango_vendor_profile` | Vendor profile | uei |
| `search_tango_opportunities` | Opportunities | agency, naics, status |

---

## Part 5: Implementation Priority

### Phase 1: Foundation (Week 1-2)
1. [ ] Create unified data schema classes
2. [ ] Build USASpending API client wrapper
3. [ ] Implement bulk contract collection
4. [ ] Create data storage infrastructure

### Phase 2: Enrichment (Week 2-3)
1. [ ] Build subaward collection pipeline
2. [ ] Implement task order extraction
3. [ ] Add SAM.gov entity enrichment
4. [ ] Create executive extraction

### Phase 3: Intelligence (Week 3-4)
1. [ ] Build technology keyword extractor
2. [ ] Implement job posting scraper
3. [ ] Create location clustering
4. [ ] Build team composition analysis

### Phase 4: Synthesis (Week 4-5)
1. [ ] Create unified intelligence profiles
2. [ ] Build BD scoring algorithm
3. [ ] Generate recompete alerts
4. [ ] Create dashboard views

---

## Part 6: Output File Structure

```
output/
├── bd_databases/
│   ├── master_programs.csv              # Complete program profiles
│   ├── prime_contracts.csv              # Prime contract data
│   ├── subawards_complete.csv           # All subaward data
│   ├── task_orders_complete.csv         # All task order data
│   ├── entity_profiles.csv              # Vendor/sub profiles
│   └── executive_directory.csv          # Key personnel
│
├── program_intelligence/
│   ├── 01_program_directory.csv         # Program overview
│   ├── 02_team_composition.csv          # Prime + sub teams
│   ├── 03_technology_signals.csv        # Tech keywords
│   ├── 04_clearance_requirements.csv    # Security requirements
│   ├── 05_functional_areas.csv          # Service categories
│   ├── 06_hot_hiring_programs.csv       # Active hiring
│   ├── 07_work_locations.csv            # All team sites
│   ├── 08_executive_intel.csv           # Leadership data
│   ├── 09_org_hierarchy.csv             # Prime-sub relationships
│   └── 10_recompete_tracker.csv         # Upcoming recompetes
│
├── task_orders/
│   ├── task_orders_by_program.csv       # Task orders per program
│   ├── task_order_locations.csv         # Task order work sites
│   └── task_order_performers.csv        # Who's doing the work
│
├── competitor_intel/
│   ├── competitor_contract_presence.csv # Where competitors work
│   ├── competitor_team_analysis.csv     # Competitor teaming
│   ├── competitor_growth_analysis.csv   # Competitor growth
│   └── competitor_executive_moves.csv   # Personnel changes
│
└── reports/
    ├── daily_alerts.csv                 # New awards, mods
    ├── weekly_summary.csv               # Weekly intelligence
    └── monthly_trends.csv               # Trend analysis
```

---

## Part 7: Key Metrics to Track

### Contract Intelligence Metrics
- Total contract value by program
- Annual burn rate
- Contract utilization (obligated vs ceiling)
- Time remaining on contract
- Modification frequency

### Team Intelligence Metrics
- Team size (# of subs)
- Team spend distribution
- Geographic spread
- Business type mix

### Competitive Intelligence Metrics
- Win rate by competitor
- Teaming frequency
- Market share by NAICS
- Growth rate by vendor

### Hiring Intelligence Metrics
- Open positions by program
- Time-to-fill estimates
- Clearance distribution
- Skills demand trends

---

## Conclusion

This strategy document provides a complete mapping of **500+ data fields** from USASpending.gov and related sources to specific BD intelligence requirements. The comprehensive data structure enables:

1. **Faster competitor intelligence** - All prime and sub relationships in one view
2. **Better recompete targeting** - Complete contract timeline tracking
3. **Deeper program understanding** - Technology, skills, and location mapping
4. **Actionable BD insights** - Scored and prioritized target lists

Implementation of this strategy will provide competitive advantage by enabling faster intelligence gathering than competitors who rely on manual research.
