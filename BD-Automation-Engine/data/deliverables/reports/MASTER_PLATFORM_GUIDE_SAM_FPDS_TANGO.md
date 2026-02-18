# MASTER PLATFORM GUIDE: SAM.gov, FPDS.gov, and Tango API

## Complete Technical Reference for Federal Program Data Extraction

---

# TABLE OF CONTENTS

1. [Platform Overview](#platform-overview)
2. [SAM.gov Complete Guide](#samgov-complete-guide)
3. [FPDS.gov Complete Guide](#fpdsgov-complete-guide)
4. [Tango API Complete Guide](#tango-api-complete-guide)
5. [Data Field Cross-Reference](#data-field-cross-reference)
6. [PWS/SOW Document Extraction Strategy](#pwssow-document-extraction-strategy)
7. [Program Enrichment Data Mapping](#program-enrichment-data-mapping)
8. [API Integration Strategies](#api-integration-strategies)

---

# PLATFORM OVERVIEW

## What Each Platform Provides

| Platform | Primary Purpose | Key Data Types | API Available |
|----------|-----------------|----------------|---------------|
| **SAM.gov** | Central hub for federal business | Opportunities, Entity Registration, Awards, Exclusions | Yes - Multiple APIs |
| **FPDS.gov** | Federal procurement data system | Contract awards, modifications, IDVs | Yes - ATOM Feed + SOAP |
| **Tango API** | Unified procurement data API | Aggregated data from SAM, FPDS, USAspending | Yes - REST API |

## Legacy Systems Consolidated into SAM.gov

| Legacy System | What It Was | Now In SAM.gov As |
|---------------|-------------|-------------------|
| **FBO.gov** | Federal Business Opportunities | Contract Opportunities |
| **CFDA.gov** | Catalog of Federal Domestic Assistance | Assistance Listings |
| **WDOL.gov** | Wage Determinations OnLine | Wage Determinations |
| **FPDS.gov** (partial) | Contract Data Reports | Contract Data / Data Bank |
| **FAPIIS.gov** | Contractor Responsibility | Responsibility/Qualification |
| **eSRS.gov** | Electronic Subcontracting Reporting | Subaward Reports |
| **FSRS.gov** | Federal Subaward Reporting System | Federal Assistance Subaward Reports |

---

# SAM.gov COMPLETE GUIDE

## All SAM.gov Domains

### 1. Contract Opportunities (formerly FBO.gov)
**URL:** `https://sam.gov/search/?index=opp`

**What It Contains:**
- Pre-solicitation notices
- Solicitation notices (with PWS/SOW attachments)
- Combined Synopsis/Solicitation
- Sources Sought
- Award Notices
- Justification & Authorization (J&A)
- Sale of Surplus Property
- Special Notices
- Intent to Bundle Requirements

**Key Data Fields:**
- Solicitation Number
- Title
- Posted Date / Response Deadline
- Set-Aside Type
- NAICS Code / PSC Code
- Place of Performance (City, State, Zip, Country)
- Awarding Agency / Office
- Point of Contact (Name, Email, Phone)
- Award Information (Awardee, Amount, Date)
- **resourceLinks** - URLs to download attachments (PWS, SOW, RFP, etc.)

### 2. Contract Data / Data Bank (formerly FPDS reports)
**URL:** `https://sam.gov/reports/awards/standard`

**Report Types:**
1. **Standard Reports** - Pre-formatted contract activity reports
2. **Static Reports** - Fiscal year summaries (downloadable)
3. **Ad Hoc Reports** - Custom queries with field selection
4. **Administrative Reports** - Federal users only

**Available Filters:**
- Date Range (Fiscal Year or Custom)
- Awarding Agency
- Funding Agency
- NAICS Code
- PSC Code
- Place of Performance (Country, State, City, Zip, Congressional District)
- Contractor Name / UEI / CAGE Code
- Contract Type
- Set-Aside Status
- Dollar Range

### 3. Entity Information
**URL:** `https://sam.gov/search/?index=ei`

**Sub-Domains:**
- **Entity Registrations** - All registered federal contractors
- **Exclusions** - Debarred/suspended entities
- **Disaster Response Registry** - Emergency response contractors
- **Responsibility/Qualification** - FAPIIS data (past performance issues)

**Key Entity Data Fields:**
- Unique Entity ID (UEI) - 12-character alphanumeric
- CAGE Code - 5-character
- Legal Business Name
- DBA Name
- Physical Address
- Mailing Address
- Congressional District
- Entity Structure (LLC, Corp, etc.)
- Organization Type
- Business Types (Small Business designations)
- NAICS Codes (Primary + Secondary)
- PSC Codes
- SBA Certifications (8(a), HUBZone, WOSB, SDVOSB)
- Points of Contact (Government Business POC, Electronic Business POC, Past Performance POC)
- Banking Information (Sensitive - requires elevated access)
- Hierarchy Information (Parent companies, subsidiaries)

### 4. Federal Hierarchy
**URL:** `https://sam.gov/search/?index=fh`

**Data:**
- All federal departments
- Sub-tier agencies
- Offices
- Organization codes
- Activity Address Codes (AAC)

### 5. Wage Determinations
**URL:** `https://sam.gov/search/?index=wd`

**Types:**
- Service Contract Act (SCA)
- Davis-Bacon Act (DBA)
- By geographic area

### 6. Assistance Listings (formerly CFDA)
**URL:** `https://sam.gov/search/?index=cfda`

**Data:**
- Federal assistance programs
- Grant programs
- CFDA numbers

### 7. Data Services (Bulk Downloads)
**URL:** `https://sam.gov/data-services`

**Available Extracts:**

| Extract Type | Format | Refresh | Access |
|--------------|--------|---------|--------|
| Contract Opportunities | JSON/XML | Daily | Public |
| Entity Registration | CSV/JSON | Daily | Public/FOUO/Sensitive |
| Exclusions | CSV/JSON | Daily | Public |
| Integrity (FAPIIS) | CSV | Daily | Federal Only |

---

## SAM.gov APIs - Complete Reference

### 1. Get Opportunities Public API
**Endpoint:** `https://api.sam.gov/opportunities/v2/search`

**Authentication:** API Key (get from SAM.gov profile)

**Rate Limits:**
- Public: 10 requests/day
- Registered: 1,000 requests/day

**Required Parameters:**
- `api_key` - Your API key
- `postedFrom` - Start date (MM/dd/yyyy)
- `postedTo` - End date (MM/dd/yyyy) - Max 1-year range

**Optional Parameters:**
| Parameter | Description | Values |
|-----------|-------------|--------|
| `ptype` | Notice type | u, p, a, r, s, o, g, k, i |
| `solnum` | Solicitation number | String |
| `noticeid` | Unique notice ID | String |
| `title` | Title keywords | String |
| `state` | State code | 2-letter |
| `zip` | Zip code | String |
| `organizationCode` | Agency code | String |
| `organizationName` | Agency name | String |
| `typeOfSetAside` | Set-aside code | SBA, 8A, HZC, SDVOSBC, WOSB, etc. |
| `ncode` | NAICS code | Up to 6 digits |
| `ccode` | Classification/PSC code | String |
| `rdlfrom` / `rdlto` | Response deadline range | MM/dd/yyyy |
| `limit` | Records per page | 1-1000 |
| `offset` | Page number | Integer |

**Notice Type Codes:**
| Code | Type |
|------|------|
| u | Justification (J&A) |
| p | Pre-solicitation |
| a | Award Notice |
| r | Sources Sought |
| s | Special Notice |
| o | Solicitation |
| g | Sale of Surplus |
| k | Combined Synopsis/Solicitation |
| i | Intent to Bundle |

**Response Fields (Key):**
- `noticeId` - Unique identifier
- `title` - Opportunity title
- `solicitationNumber` - Solicitation number
- `postedDate` - Posted date
- `responseDeadLine` - Response deadline
- `naicsCode` - NAICS code
- `classificationCode` - PSC code
- `typeOfSetAside` - Set-aside type
- `placeOfPerformance` - Location details (city, state, zip, country)
- `pointOfContact` - Array of contacts (name, email, phone, title)
- `award` - Award info (awardee name, UEI, amount, date, address)
- `resourceLinks` - **URLs TO DOWNLOAD PWS/SOW ATTACHMENTS**
- `description` - URL to description document
- `uiLink` - Direct link to SAM.gov page

### 2. Entity Management API
**Endpoints:**
- `https://api.sam.gov/entity-information/v3/entities` (recommended)
- `https://api.sam.gov/entity-information/v4/entities` (latest)

**Access Levels:**
| Level | Data Available | Auth Required |
|-------|----------------|---------------|
| Public | Basic entity info | API Key |
| FOUO | + Hierarchy, security, contacts | Federal System Account |
| Sensitive | + Banking, TIN/EIN | Federal System Account + POST |

**Key Query Parameters:**
- `ueiSAM` - Up to 100 UEIs
- `cageCode` - Up to 100 CAGE codes
- `legalBusinessName` - Company name search
- `registrationStatus` - A (Active) or E (Expired)
- `primaryNaics` - 6-digit NAICS
- `pscCode` - Product/Service code
- `sbaBusinessTypeCode` - SBA certification type
- `physicalAddressStateCode` - State filter
- `physicalAddressCountryCode` - Country filter

**Response Sections (use `includeSections` parameter):**
- `entityRegistration` - Basic registration data
- `coreData` - Addresses, hierarchy, business types
- `assertions` - NAICS, PSC, disaster relief, size metrics
- `repsAndCerts` - FAR/DFARS certifications
- `pointsOfContact` - All POC types
- `integrityInformation` - FAPIIS/responsibility data

**Points of Contact Available:**
- Government Business POC
- Electronic Business POC
- Government Business Alternate POC
- Electronic Business Alternate POC
- Past Performance POC
- Past Performance Alternate POC
- Accounts Receivable POC
- Accounts Payable POC

### 3. Opportunity Management API (Federal Users Only)
**Endpoint:** `https://api.sam.gov/opportunities/v2/`

**Capabilities:**
- Create/publish opportunities
- Update drafts
- Revise published notices
- Cancel/uncancel notices
- Archive/unarchive
- Manage attachments
- Get Interested Vendor List (IVL)
- Download all attachments as ZIP

**Key Endpoints:**
- `POST /create` - Create draft
- `POST /createAndPublish` - Create and publish
- `GET /search` - Search opportunities
- `GET /{opportunityId}` - Get specific opportunity
- `GET /opportunities/{opportunityId}/download/zip` - **DOWNLOAD ALL ATTACHMENTS**
- `GET /ivl/{opportunityId}` - Get interested vendors

### 4. Exclusions API
**Endpoint:** `https://api.sam.gov/entity-information/v2/exclusions`

**Data:** Debarred, suspended, and excluded entities

### 5. Federal Hierarchy API
**Endpoint:** `https://api.sam.gov/fed-hierarchy/v2/`

**Data:** Complete federal agency hierarchy

---

# FPDS.gov COMPLETE GUIDE

## Overview

FPDS (Federal Procurement Data System) contains **180+ data elements** for every federal contract action. It's the authoritative source for contract award data.

**Important:** FPDS ezSearch is being migrated to SAM.gov. ezSearch decommissioning scheduled for Q2 FY2026.

## FPDS Data Access Methods

### 1. ezSearch (Web Interface)
**URL:** `https://www.fpds.gov/ezsearch/search.do`

**Search Capabilities:**
- Keyword search
- Date range filtering
- Agency/department filtering
- Contractor name/UEI/CAGE
- NAICS/PSC codes
- Place of performance
- Contract type
- Dollar ranges
- Set-aside status

### 2. ATOM Feed (Programmatic Access)
**Base URL:** `https://www.fpds.gov/ezsearch/FEEDS/ATOM`

**Feed Types:**
| Feed | URL | Auth Required |
|------|-----|---------------|
| Public/Civilian | `/FPDS-feed/` | No |
| DoD | `/DoD-feed/` | Yes (fsd.gov account) |
| FAADC (Assistance) | `/FAADC-feed/` | Yes |
| Deleted Records | `/DELETED/` | No |

**Rate Limits:**
- 10 records per thread
- 10 threads per search = 100 records max per query
- Updated daily by 9:00 AM ET

### 3. ATOM Feed Query Parameters

**Syntax:** `BASE_URL?PARAM1:value&PARAM2:value`

**Date Parameters:**
| Parameter | Description |
|-----------|-------------|
| `LAST_MOD_DATE:[date1,date2]` | Last modified range |
| `SIGNED_DATE:[date1,date2]` | Date signed range |
| `EFFECTIVE_DATE:[date1,date2]` | Period of performance start |
| `ESTIMATED_COMPLETION_DATE:[date1,date2]` | Estimated completion |
| `AWARD_COMPLETION_DATE:[date1,date2]` | Award completion |
| `CREATED_DATE:[date1,date2]` | Created date range |

**Organization Parameters:**
| Parameter | Description |
|-----------|-------------|
| `AGENCY_CODE:"value"` | Agency code |
| `AGENCY_NAME:"value"` | Agency name |
| `DEPARTMENT_ID:"value"` | Department ID |
| `DEPARTMENT_NAME:"value"` | Department name |
| `CONTRACTING_AGENCY_ID:"value"` | Contracting agency |
| `CONTRACTING_OFFICE_ID:"value"` | Contracting office |
| `FUNDING_AGENCY_ID:"value"` | Funding agency |
| `FUNDING_OFFICE_ID:"value"` | Funding office |

**Contract Identifiers:**
| Parameter | Description |
|-----------|-------------|
| `PIID:"value"` | Contract ID (PIID) |
| `REF_IDV_PIID:"value"` | Reference IDV PIID |
| `REF_IDV_AGENCY_ID:"value"` | Reference IDV agency |
| `CAGE_CODE:"value"` | CAGE code |

**Classification:**
| Parameter | Description |
|-----------|-------------|
| `CONTRACT_TYPE:"AWARD"` or `"IDV"` | Contract type |
| `AWARD_STATUS:"Final"` or `"Deleted"` | Award status |
| `IDV_CONTRACT_TYPE:"BPA"` | IDV type |
| `PRODUCT_OR_SERVICE_CODE:"value"` | PSC code |
| `PRINCIPAL_NAICS_CODE:"value"` | NAICS code |

**Financial:**
| Parameter | Description |
|-----------|-------------|
| `OBLIGATED_AMOUNT:[min,max]` | Obligation range |
| `ULTIMATE_CONTRACT_VALUE:[min,max]` | Total value range |

**Vendor/Entity:**
| Parameter | Description |
|-----------|-------------|
| `VENDOR_UEI:"value"` | Vendor UEI |
| `ULTIMATE_UEI:"value"` | Ultimate parent UEI |
| `UEI_NAME:"value"` | Legal business name |
| `VENDOR_ADDRESS_CITY:"value"` | Vendor city |
| `VENDOR_ADDRESS_STATE_CODE:"value"` | Vendor state |
| `VENDOR_ADDRESS_ZIP_CODE:"value"` | Vendor zip |

**Place of Performance:**
| Parameter | Description |
|-----------|-------------|
| `POP_COUNTRY_NAME:"value"` | PoP country |
| `POP_STATE_NAME:"value"` | PoP state |
| `POP_CONGRESS_DISTRICT_CODE:"value"` | PoP congressional district |

**Socioeconomic:**
| Parameter | Description |
|-----------|-------------|
| `SOCIO_ECONOMIC_INDICATORS:"value"` | Set-aside type |
| `LOCAL_AREA_SET_ASIDE:"Y"` | Local area set-aside |
| `MULTIYEAR_CONTRACT:"Y"` | Multiyear contract |

## FPDS Data Dictionary - Key Fields

**Download Full Data Dictionary:**
- V1.5: https://www.fpds.gov/downloads/Version_1.5_specs/FPDS_DataDictionary_V15_OT.pdf
- User Manual: https://www.fpds.gov/downloads/Manuals/FPDS_User_Manual_V1.5.pdf

### Contract Identification (Category 1)
| Field | Description |
|-------|-------------|
| 1A | Contracting Agency Code |
| 1B | Contracting Agency Name |
| 1C | Contracting Office Code |
| 1D | Contracting Office Name |
| 1E | Funding Agency Code |
| 1F | Funding Agency Name |
| 1G | Funding Office Code |
| 1H | Funding Office Name |
| 1I | PIID (Procurement Instrument ID) |

### Dates (Category 2)
| Field | Description |
|-------|-------------|
| 2A | Date Signed |
| 2B | Effective Date (PoP Start) |
| 2C | Current Completion Date |
| 2D | Ultimate Completion Date |

### Amounts (Category 3)
| Field | Description |
|-------|-------------|
| 3A | Action Obligation |
| 3B | Base and Exercised Options Value |
| 3C | Base and All Options Value |

### Vendor Information (Category 4)
| Field | Description |
|-------|-------------|
| 4A | Unique Entity ID (UEI) |
| 4B | Vendor Name |
| 4C | Vendor Address |
| 4D | Vendor City |
| 4E | Vendor State |
| 4F | Vendor Zip |
| 4G | Vendor Country |
| 4H | Vendor Congressional District |
| 4I | CAGE Code |

### Place of Performance (Category 5)
| Field | Description |
|-------|-------------|
| 5A | PoP City |
| 5B | PoP State |
| 5C | PoP Zip |
| 5D | PoP Country |
| 5E | PoP Congressional District |

### Product/Service (Category 6)
| Field | Description |
|-------|-------------|
| 6A | Product or Service Code (PSC) |
| 6B | Product or Service Description |
| 6C | Principal NAICS Code |
| 6D | NAICS Description |
| 6E | Contract Description (Requirement) |

## FPDS Worksite Portal Resources
**URL:** `https://www.fpds.gov/fpdsng_cms/index.php/en/worksite.html`

**Available Downloads:**
- Data Dictionary (all versions)
- OT (Other Transactions) Data Dictionary
- WSDL Files (SOAP API definitions)
- XSD Files (XML schemas)
- Web Services Specifications
- Validation Rules
- SOAP Examples
- Quick Start Guides

---

# TANGO API COMPLETE GUIDE

## Overview

Tango by MakeGov is a unified REST API that aggregates data from multiple federal sources into a single, normalized interface.

**URL:** `https://tango.makegov.com`
**Documentation:** `https://tango.makegov.com/docs/`
**API Schema:** `https://tango.makegov.com/api/`

## Data Sources Aggregated

| Source | Data Type |
|--------|-----------|
| FPDS | Contract awards, modifications |
| USAspending | Spending data, subawards |
| SAM.gov | Opportunities, entity registrations |
| Grants.gov | Grant opportunities |
| Direct agency feeds | Agency-specific data |

## Core Capabilities

### Authentication
- API Keys (server-to-server)
- OAuth2 (web applications)
- Bearer tokens

### Data Access Features
- Full-text search across titles/descriptions
- Complex AND/OR filter patterns
- Geographic/location filtering
- Date range queries
- Custom field selection
- Nested object expansion
- JSON flattening
- Field aliasing

### SDKs Available
- Python SDK
- Node.js SDK
- Direct HTTP (no SDK required)

## Tango Data Categories

### 1. Contract Awards & Modifications
- All FPDS contract data
- Award modifications
- IDV (Indefinite Delivery Vehicle) data
- Transaction history

### 2. Financial Assistance
- Grants
- Loans
- Other financial assistance
- Transaction details

### 3. Opportunities
- Real-time opportunities (refreshed every 20-60 minutes)
- Full solicitation data
- Historical opportunity lineage

### 4. Entities
- 600,000+ vendor profiles
- Firmographic data
- Business classifications
- Registration status

### 5. Government Agencies
- Agency hierarchy
- Office information
- Unified organization codes

### 6. Webhooks
- Near-real-time notifications
- Event-driven updates

## Tango vs. Direct API Access

| Feature | SAM.gov/FPDS Direct | Tango API |
|---------|---------------------|-----------|
| Single endpoint | No (multiple APIs) | Yes |
| Normalized data | No | Yes |
| Rate limits | Strict | More flexible |
| Historical data | Varies | Comprehensive |
| Real-time updates | Daily | 20-60 min |
| Cross-source queries | Manual | Automatic |

---

# DATA FIELD CROSS-REFERENCE

## Finding Your Data Across Platforms

### Program/Contract Identification
| Data Point | SAM.gov | FPDS | Tango | USAspending |
|------------|---------|------|-------|-------------|
| Contract Number (PIID) | ✓ Award | ✓ 1I | ✓ | ✓ |
| Solicitation Number | ✓ Opp | - | ✓ | - |
| Award ID | ✓ | ✓ | ✓ | ✓ |
| IDV Reference | ✓ | ✓ REF_IDV_PIID | ✓ | ✓ |

### Contractor Information
| Data Point | SAM.gov | FPDS | Tango | USAspending |
|------------|---------|------|-------|-------------|
| Company Name | ✓ Entity | ✓ 4B | ✓ | ✓ |
| UEI | ✓ | ✓ 4A | ✓ | ✓ |
| CAGE Code | ✓ Entity | ✓ 4I | ✓ | ✓ |
| Parent Company | ✓ Entity | ✓ ULTIMATE_UEI | ✓ | ✓ |
| Address | ✓ Entity | ✓ 4C-4G | ✓ | ✓ |
| Business Type | ✓ Entity | ✓ Socio | ✓ | ✓ |
| SBA Certifications | ✓ Entity | - | ✓ | - |
| Points of Contact | ✓ Entity | - | - | - |

### Place of Performance
| Data Point | SAM.gov | FPDS | Tango | USAspending |
|------------|---------|------|-------|-------------|
| City | ✓ Opp/Award | ✓ 5A | ✓ | ✓ |
| State | ✓ | ✓ 5B | ✓ | ✓ |
| Zip | ✓ | ✓ 5C | ✓ | ✓ |
| Country | ✓ | ✓ 5D | ✓ | ✓ |
| Congressional District | ✓ | ✓ 5E | ✓ | ✓ |

### Financial Data
| Data Point | SAM.gov | FPDS | Tango | USAspending |
|------------|---------|------|-------|-------------|
| Award Amount | ✓ Award | ✓ 3A | ✓ | ✓ |
| Total Contract Value | ✓ | ✓ 3C | ✓ | ✓ |
| Funding Amount | - | ✓ | ✓ | ✓ |
| Subaward Data | - | - | ✓ | ✓ |

### Dates
| Data Point | SAM.gov | FPDS | Tango | USAspending |
|------------|---------|------|-------|-------------|
| Award Date | ✓ | ✓ 2A | ✓ | ✓ |
| Period of Performance Start | ✓ | ✓ 2B | ✓ | ✓ |
| Period of Performance End | ✓ | ✓ 2C/2D | ✓ | ✓ |
| Response Deadline | ✓ Opp | - | ✓ | - |
| Posted Date | ✓ Opp | - | ✓ | - |

### Classification
| Data Point | SAM.gov | FPDS | Tango | USAspending |
|------------|---------|------|-------|-------------|
| NAICS Code | ✓ | ✓ 6C | ✓ | ✓ |
| PSC Code | ✓ | ✓ 6A | ✓ | ✓ |
| Set-Aside Type | ✓ | ✓ Socio | ✓ | ✓ |
| Contract Type | ✓ | ✓ | ✓ | ✓ |

### Contact Information
| Data Point | SAM.gov | FPDS | Tango | USAspending |
|------------|---------|------|-------|-------------|
| Contracting Officer | ✓ Opp POC | - | ✓ | - |
| Government POC | ✓ Entity | - | - | - |
| Past Performance POC | ✓ Entity | - | - | - |

---

# PWS/SOW DOCUMENT EXTRACTION STRATEGY

## Method 1: SAM.gov API - resourceLinks Field

The `resourceLinks` field in the Opportunities API response contains URLs to all attachments.

```python
# Example: Extract PWS documents from SAM.gov API
import requests

API_KEY = "your_api_key"
BASE_URL = "https://api.sam.gov/opportunities/v2/search"

params = {
    "api_key": API_KEY,
    "postedFrom": "01/01/2024",
    "postedTo": "12/31/2024",
    "ptype": "o",  # Solicitations only
    "limit": 100
}

response = requests.get(BASE_URL, params=params)
data = response.json()

for opp in data.get("opportunitiesData", []):
    resource_links = opp.get("resourceLinks", [])
    if resource_links:
        for link in resource_links:
            # Download each attachment
            # Look for PWS, SOW, RFP in filename
            print(f"Attachment: {link}")
```

## Method 2: SAM.gov Web Interface Manual Download

1. Go to `https://sam.gov/search/?index=opp`
2. Search for your target contract/program
3. Click on the opportunity
4. Scroll to **"Attachments/Links"** section
5. Download files named:
   - `PWS*.pdf`
   - `SOW*.pdf`
   - `Performance_Work_Statement*.pdf`
   - `Statement_of_Work*.pdf`
   - `Attachment_*.pdf`

## Method 3: Bulk Download via Opportunity Management API (Federal Users)

```
GET /opportunities/{opportunityId}/download/zip
```

This downloads ALL attachments for an opportunity as a ZIP file.

## What PWS/SOW Documents Contain

| Data Point | Found In PWS/SOW |
|------------|------------------|
| Locations/Sites | ✓ Section on Place of Performance |
| Functional Areas | ✓ Task descriptions |
| Labor Categories | ✓ CLIN structure |
| Team Structure | ✓ Organizational requirements |
| Clearance Requirements | ✓ Security section |
| Period of Performance | ✓ Contract period |
| Technical Requirements | ✓ Throughout |
| Deliverables | ✓ CDRL section |

---

# PROGRAM ENRICHMENT DATA MAPPING

## Your Target Data Points → Where to Find Them

### 1. Hiring Contacts (Recruiters, Hiring Managers)
| Source | Method | Data Available |
|--------|--------|----------------|
| LinkedIn Recruiter | Manual/Scraper | Hiring managers, recruiters by company |
| ZoomInfo | Export | Contact names, titles, emails |
| USAJobs | API | Federal hiring managers (gov-side) |
| SAM.gov POC | Entity API | Government Business POC |

### 2. Org Charts (PM, Deputy PM, Site Leads)
| Source | Method | Data Available |
|--------|--------|----------------|
| LinkedIn Recruiter | Search by company + title | Current employees by role |
| ZoomInfo | Export | Org structure, reporting chains |
| PWS Documents | Manual extraction | Required positions/roles |
| Job Postings | Scraper | Positions being filled |
| Press Releases | Web scrape | Leadership announcements |

### 3. Site-Specific Details (PMO Locations, Team Structures)
| Source | Method | Data Available |
|--------|--------|----------------|
| PWS/SOW Documents | SAM.gov attachments | Site locations, team requirements |
| FPDS | Place of Performance fields | Contract locations |
| Job Postings | Location field | Where hiring is happening |
| USAspending | PoP data | Primary/secondary performance locations |

### 4. Personnel Names (Recruiting Targets)
| Source | Method | Data Available |
|--------|--------|----------------|
| LinkedIn Recruiter | Search | Current employees by company/program |
| ZoomInfo | Export | Employee directory |
| Conference Lists | Manual | Speakers, attendees |
| FOIA | Request | Government org charts |

---

# API INTEGRATION STRATEGIES

## Recommended Architecture for This Project

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FEDERAL PROGRAMS DATABASE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │ CAPTURE MCP     │    │ THIS PROJECT    │    │ MANUAL SOURCES  │ │
│  │ (Other Terminal)│    │ (This Terminal) │    │                 │ │
│  ├─────────────────┤    ├─────────────────┤    ├─────────────────┤ │
│  │ • SAM.gov API   │    │ • USAJobs API   │    │ • LinkedIn      │ │
│  │ • USAspending   │    │ • FPDS ATOM     │    │ • ZoomInfo      │ │
│  │   API           │    │ • Tango API     │    │ • PWS parsing   │ │
│  │                 │    │ • PWS Downloader│    │ • Press releases│ │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘ │
│           │                      │                      │          │
│           └──────────────────────┼──────────────────────┘          │
│                                  ▼                                  │
│                    ┌─────────────────────────┐                     │
│                    │   DATA ENRICHMENT       │                     │
│                    │   & MAPPING ENGINE      │                     │
│                    └─────────────────────────┘                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Scrapers/Integrations to Build for This Project

### Priority 1: PWS/SOW Document Pipeline
1. SAM.gov Opportunity scraper → Download all attachments
2. PDF parser → Extract locations, labor categories, requirements
3. Store in database linked to program

### Priority 2: USAJobs Integration
1. Clone `marcdacosta/usajobs-scrape` or `abigailhaddad/usajobs_historical`
2. Pull federal job postings
3. Extract: locations, clearances, program references

### Priority 3: FPDS Deep Pull
1. Use ATOM feed for detailed contract data
2. Pull all modifications to track program changes
3. Extract subcontractor relationships

### Priority 4: Tango API Integration
1. Use as unified query layer
2. Cross-reference data across sources
3. Fill gaps in other APIs

---

# QUICK REFERENCE - KEY URLs

## SAM.gov
| Resource | URL |
|----------|-----|
| Home | https://sam.gov |
| Contract Opportunities | https://sam.gov/search/?index=opp |
| Entity Search | https://sam.gov/search/?index=ei |
| Data Bank | https://sam.gov/reports/awards/standard |
| Data Services | https://sam.gov/data-services |
| API Documentation | https://open.gsa.gov/api/ |

## FPDS.gov
| Resource | URL |
|----------|-----|
| Home | https://www.fpds.gov |
| ezSearch | https://www.fpds.gov/ezsearch/search.do |
| ATOM Feed | https://www.fpds.gov/ezsearch/FEEDS/ATOM |
| Worksite (Docs) | https://www.fpds.gov/fpdsng_cms/index.php/en/worksite.html |
| Data Dictionary | https://www.fpds.gov/downloads/Version_1.5_specs/FPDS_DataDictionary_V15_OT.pdf |

## Tango API
| Resource | URL |
|----------|-----|
| Home | https://tango.makegov.com |
| Documentation | https://tango.makegov.com/docs/ |
| API Schema | https://tango.makegov.com/api/ |

## Other Key Resources
| Resource | URL |
|----------|-----|
| USAspending API | https://api.usaspending.gov/docs/ |
| GSA APIs | https://open.gsa.gov/api/ |
| USAJobs API | https://developer.usajobs.gov/ |
| FOIA.gov | https://www.foia.gov/developer/ |

---

*Document Generated: January 2026*
*For Federal Programs Data Enrichment Project*
