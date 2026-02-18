# Federal Programs Database Scraper Repository Analysis

## Executive Summary

This document provides a comprehensive audit of GitHub repositories that can scrape federal procurement data to fill in your Federal Programs database. Based on analysis of your 36-column Notion export (400+ DoD/IC programs), I've identified **25+ repositories and tools** across 6 categories that can populate missing data fields.

---

## Your Database Fields & Data Source Mapping

| Database Field | Primary Data Sources | Key Repos |
|----------------|---------------------|-----------|
| Program Name/Acronym | DoD Budget Books, SAM.gov | 540co/dod-jbook-pdf-xml, FPDS |
| Agency Owner | FPDS, SAM.gov | dherincx92/fpds, GSA/srt-fbo-scraper |
| Budget | DoD P-1/R-1 Books | 540co/dod-president-budget-procurement-rdte-data |
| Contract Value | FPDS, USAspending | fedspendingtransparency/usaspending-api |
| Contract Vehicle | FPDS, SAM.gov | makegov/procurement-tools |
| Period of Performance | FPDS | dherincx92/fpds |
| Prime Contractor | FPDS, USAspending | fpds, usaspending-scripts |
| Subcontractors | USAspending Subawards | usaspending-api subaward endpoints |
| Clearance Requirements | Job Postings | JobSpy, USAJobs scrapers |
| Key Locations | FPDS, Job Postings | fpds, usajobs-scrape |
| Technical Stack/Roles | Job Postings | JobSpy, py-linkedin-jobs-scraper |
| Recompete Date | SAM.gov Opportunities | GSA/srt-fbo-scraper |

---

## Category 1: FPDS (Federal Procurement Data System) Scrapers

### 1.1 dherincx92/fpds (RECOMMENDED - HIGH PRIORITY)
**GitHub:** https://github.com/dherincx92/fpds

**Capabilities:**
- Parses FPDS ATOM feed (the core federal contract database)
- Converts XML to JSON automatically
- Handles pagination (FPDS limits to 10 records/request)
- Async performance: ~28 seconds for large queries (85% faster than sync)

**Data Fields It Can Fill:**
- Contract Value
- Prime Contractor
- Period of Performance (PoP Start/End)
- Agency Owner
- Contract Vehicle/Type
- Key Locations (Place of Performance)

**Installation:**
```bash
pip install fpds
# OR with uv
uv pip install fpds
```

**Usage Example:**
```python
from fpds import fpdsRequest
import asyncio

# Query by agency and date range
request = fpdsRequest(
    LAST_MOD_DATE="[2024/01/01, 2024/12/31]",
    AGENCY_CODE="9700",  # DoD
    CONTRACTING_AGENCY_NAME="AIR FORCE"
)
records = asyncio.run(request.data())
```

**Adaptation for Your Database:**
- Query by agency codes: Air Force (5700), Navy (1700), Army (2100), DIA (9761)
- Filter by NAICS codes for IT/Cyber (541512, 541513, 541519)
- Extract: Vendor Name, Total Obligated Amount, PoP dates, Contract ID

**Relevance Score:** 9/10 - Essential for contract values and contractor data

---

### 1.2 18F/pyfpds (Official Government Project)
**GitHub:** https://github.com/18F/pyfpds

**Capabilities:**
- Official Python wrapper from 18F (GSA digital services)
- Basic FPDS ATOM feed access
- Less maintained than dherincx92/fpds but officially supported

**Adaptation:** Use as backup if dherincx92/fpds has issues

**Relevance Score:** 6/10 - Less feature-rich but government-backed

---

### 1.3 andrew-banister/FPDS_download
**GitHub:** https://github.com/andrew-banister/FPDS_download

**Capabilities:**
- Bulk download of FPDS records
- MD5 checksums for data integrity
- Good for historical data dumps

**Relevance Score:** 5/10 - Useful for bulk historical analysis

---

## Category 2: SAM.gov Scrapers (Opportunities & Entity Data)

### 2.1 GSA/srt-fbo-scraper (RECOMMENDED - HIGH PRIORITY)
**GitHub:** https://github.com/GSA/srt-fbo-scraper

**Capabilities:**
- Scrapes IT solicitations from SAM.gov
- Uses Opportunity Management API + Federal Hierarchy API
- Extracts document text from solicitation attachments
- Classifies by Section 508 compliance (can be adapted)

**Data Fields It Can Fill:**
- Recompete Date (from opportunity posting dates)
- Agency Owner (via Federal Hierarchy API)
- Contract Vehicle (solicitation type)
- Keywords/Signals (from document text extraction)

**Requirements:**
- SAM.gov API key (free registration)
- PostgreSQL database
- Python 3.6+

**Setup:**
```bash
git clone https://github.com/GSA/srt-fbo-scraper
cd srt-fbo-scraper
./dev_setup.sh
export SAM_API_KEY=your_key_here
```

**Adaptation for Your Database:**
- Modify NAICS filters for defense-specific codes
- Add keyword extraction for program names (DCGS, ABMS, etc.)
- Track opportunity dates for recompete intelligence

**Relevance Score:** 8/10 - Key for recompete dates and new opportunities

---

### 2.2 jankaltenegger/SAM.gov-Webscraper
**GitHub:** https://github.com/jankaltenegger/SAM.gov-Webscraper

**Capabilities:**
- Google Apps Script for SAM.gov API
- Outputs to Google Sheets
- Good for non-technical users

**Relevance Score:** 4/10 - Simple but limited

---

### 2.3 makegov/procurement-tools (RECOMMENDED)
**GitHub:** https://github.com/makegov/procurement-tools

**Capabilities:**
- UEI validation (contractor unique identifiers)
- USASpending URL generation
- FAR section lookup
- SAM API client for entity searches

**Installation:**
```bash
pip install procurement-tools
export SAM_API_KEY=your_key
```

**Usage:**
```python
from procurement_tools import SAMClient

client = SAMClient()
entity = client.get_entity(uei="XXXXXXXXXXX")
```

**Relevance Score:** 7/10 - Great utility library for validation

---

## Category 3: USAspending Data (Contract Awards & Spending)

### 3.1 fedspendingtransparency/usaspending-api (OFFICIAL)
**GitHub:** https://github.com/fedspendingtransparency/usaspending-api

**Capabilities:**
- Official government API server codebase
- Access to ALL federal spending data
- Award details, transactions, subawards
- Recipient (contractor) information

**Key Endpoints:**
- `/api/v2/search/spending_by_award/` - Search awards by filters
- `/api/v2/recipient/` - Contractor details
- `/api/v2/subawards/` - Subcontractor data
- `/api/v2/transactions/` - Individual transactions

**Data Fields It Can Fill:**
- Contract Value (total and obligated amounts)
- Prime Contractor
- Known Subcontractors (via subaward data)
- Period of Performance
- Key Locations

**API Usage (No installation needed - use their API):**
```python
import requests

url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
payload = {
    "filters": {
        "agencies": [{"type": "awarding", "tier": "toptier", "name": "Department of Defense"}],
        "award_type_codes": ["A", "B", "C", "D"],  # Contracts
        "time_period": [{"start_date": "2024-01-01", "end_date": "2024-12-31"}]
    },
    "fields": ["Award ID", "Recipient Name", "Award Amount", "Period of Performance Start Date"],
    "limit": 100
}
response = requests.post(url, json=payload)
awards = response.json()
```

**Relevance Score:** 10/10 - Essential for contract values and prime contractors

---

### 3.2 bsweger/usaspending-scripts
**GitHub:** https://github.com/bsweger/usaspending-scripts

**Capabilities:**
- Scripts to download and summarize USAspending data
- Aggregates by agency, program, geography
- Works with bulk downloads

**Relevance Score:** 7/10 - Good for batch processing

---

### 3.3 justindbk/usa-spending-scraper
**GitHub:** https://github.com/justindbk/usa-spending-scraper

**Capabilities:**
- R-based scraper for county-level data
- Addresses poorly documented API v2

**Relevance Score:** 4/10 - R instead of Python, limited scope

---

## Category 4: DoD Budget Justification Books (CRITICAL FOR PROGRAM DATA)

### 4.1 540co/dod-president-budget-procurement-rdte-data (RECOMMENDED - HIGH PRIORITY)
**GitHub:** https://github.com/540co/dod-president-budget-procurement-rdte-data

**Capabilities:**
- Extracted DoD P-1 (Procurement) and R-1 (RDT&E) justification books
- Years: 2013-2017 (machine-readable data)
- Formats: XML, JSON, CSV, SQL, Tableau

**Data Fields It Can Fill:**
- Program Name / Acronym
- Budget (appropriated amounts)
- Agency Owner (by service)
- Program Type (RDT&E, Procurement)

**Available Data:**
- Procurement line items by military service
- RDT&E program elements
- Budget amounts by fiscal year
- Appropriation codes

**Usage:**
```bash
git clone https://github.com/540co/dod-president-budget-procurement-rdte-data
# Data is in multiple formats:
# 0-jbook-xml/ - Raw XML from PDF attachments
# 1-json-rdte-programelements/ - JSON by program element
# 2-csv/ - Relational tables
```

**Adaptation:**
- Map program element codes to your program names
- Cross-reference with FPDS contracts
- Track budget trends by program

**Relevance Score:** 9/10 - Only source for official DoD budget data

---

### 4.2 540co/dod-jbook-pdf-xml
**GitHub:** https://github.com/540co/dod-jbook-pdf-xml

**Capabilities:**
- Raw PDF and extracted XML from justification books
- Includes Master Justification Books
- Pre-2013 PDFs available (no machine-readable)

**Relevance Score:** 8/10 - Companion to above, more raw data

---

## Category 5: Job Posting Scrapers (Contractor Intelligence)

### 5.1 speedyapply/JobSpy (RECOMMENDED - Already in Your Audits)
**GitHub:** https://github.com/speedyapply/JobSpy

**Capabilities:**
- Multi-board scraping: LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter
- Concurrent scraping with proxy support
- Returns pandas DataFrame

**Data Fields It Can Fill:**
- Prime Contractor (who's hiring)
- Typical Roles (job titles)
- Clearance Requirements (from job descriptions)
- Technical Stack (from requirements)
- Key Locations (job locations)
- Keywords/Signals (skills, technologies)

**Installation:**
```bash
pip install python-jobspy
```

**Usage for Defense Contractors:**
```python
from jobspy import scrape_jobs

jobs = scrape_jobs(
    site_name=["linkedin", "indeed"],
    search_term="DCGS TS/SCI",
    location="Virginia",
    results_wanted=100,
    hours_old=72
)

# Filter for defense keywords
dcgs_jobs = jobs[jobs['description'].str.contains('DCGS|TS/SCI|clearance', case=False)]
```

**Relevance Score:** 9/10 - Critical for contractor hiring intelligence

---

### 5.2 marcdacosta/usajobs-scrape
**GitHub:** https://github.com/marcdacosta/usajobs-scrape

**Capabilities:**
- Scrapes USAJobs.gov (federal civilian jobs)
- Saves to JSON
- Callback for new job alerts
- 12-hour automatic refresh

**Data Fields It Can Fill:**
- Typical Roles (government side)
- Clearance Requirements
- Key Locations
- Agency programs hiring

**Relevance Score:** 7/10 - Federal jobs complement contractor data

---

### 5.3 abigailhaddad/usajobs_historical
**GitHub:** https://github.com/abigailhaddad/usajobs_historical

**Capabilities:**
- Combines Historical API + Current API
- Deduplication and field rationalization
- Historical trend analysis

**Relevance Score:** 7/10 - Good for historical staffing trends

---

### 5.4 spinlud/py-linkedin-jobs-scraper
**GitHub:** https://github.com/spinlud/py-linkedin-jobs-scraper

**Capabilities:**
- Selenium-based LinkedIn scraping
- Extracts job title, company, description
- Handles authentication

**Relevance Score:** 6/10 - LinkedIn-specific, requires auth

---

## Category 6: Defense.gov & DoD-Specific Scrapers

### 6.1 mt-digital/contracts (RECOMMENDED)
**GitHub:** https://github.com/mt-digital/contracts

**Capabilities:**
- Scrapes daily contract announcements from defense.gov
- Parses by agency (Navy, Army, Air Force)
- Outputs JSON with contractor, amounts, locations

**Data Fields It Can Fill:**
- Prime Contractor
- Contract Value
- Key Locations (place of performance)
- Agency Owner

**Usage:**
```python
# Download ~10 years of data
download_announcements(first_id=1, last_id=5442)

# Process to JSON
make_agency_dicts()
```

**Relevance Score:** 8/10 - Direct DoD contract data

---

## Category 7: Curated Resource Lists

### 7.1 makegov/awesome-procurement-data (MASTER LIST)
**GitHub:** https://github.com/makegov/awesome-procurement-data

**What It Contains:**
- SAM.gov APIs (Opportunities, Entity/Extracts)
- CALC API (GSA labor rates)
- FPDS ATOM feed documentation
- USAspending API
- SBIR API
- FAR Repository (regulations in XML)
- PSC Selection Tool
- NAICS/PSC code prediction APIs
- Section 889 compliance tool

**Use This As:** Your reference hub for all procurement data sources

**Relevance Score:** 10/10 - Meta-resource, links to everything

---

## Recommended Implementation Strategy

### Phase 1: Core Contract Data (Weeks 1-2)
1. **Deploy dherincx92/fpds** - Query FPDS for all DoD contracts
   - Fill: Contract Value, Prime Contractor, PoP dates, Locations
2. **Use USAspending API** - Get award details and subaward data
   - Fill: Contract Value, Prime Contractor, Subcontractors

### Phase 2: Budget & Program Data (Weeks 2-3)
3. **Clone 540co/dod-president-budget-procurement-rdte-data**
   - Fill: Budget, Program Name/Acronym, Program Type
4. **Deploy mt-digital/contracts** - Daily DoD contract announcements
   - Fill: Recent awards, Prime Contractor, Agency

### Phase 3: Opportunity Intelligence (Weeks 3-4)
5. **Deploy GSA/srt-fbo-scraper** - Track SAM.gov opportunities
   - Fill: Recompete Date, New opportunities
6. **Use makegov/procurement-tools** - Entity validation and FAR lookup
   - Fill: Contract Vehicle details

### Phase 4: Workforce Intelligence (Ongoing)
7. **Deploy JobSpy** - Scrape defense contractor job postings
   - Fill: Typical Roles, Clearance Requirements, Technical Stack, Hiring signals
8. **Deploy usajobs-scrape** - Federal job postings
   - Fill: Government-side hiring, program staffing needs

---

## Data Field Coverage Matrix

| Repo | Program Name | Budget | Contract Value | Prime | Subs | PoP | Clearance | Locations | Roles |
|------|--------------|--------|----------------|-------|------|-----|-----------|-----------|-------|
| fpds | - | - | YES | YES | - | YES | - | YES | - |
| usaspending-api | - | - | YES | YES | YES | YES | - | YES | - |
| dod-budget-data | YES | YES | - | - | - | - | - | - | - |
| srt-fbo-scraper | - | - | - | - | - | - | - | - | - |
| mt-digital/contracts | - | - | YES | YES | - | - | - | YES | - |
| JobSpy | - | - | - | YES | - | - | YES | YES | YES |
| usajobs-scrape | - | - | - | - | - | - | YES | YES | YES |

---

## API Keys Required

| Source | Registration URL | Key Name |
|--------|-----------------|----------|
| SAM.gov | https://sam.gov/content/entity-registration | SAM_API_KEY |
| USAJobs | https://developer.usajobs.gov/ | USAJOBS_API_KEY |
| USAspending | No key needed | N/A |
| FPDS | No key needed | N/A |

---

## Quick Start Commands

```bash
# Install core Python packages
pip install fpds python-jobspy procurement-tools requests pandas

# Clone key repos
git clone https://github.com/540co/dod-president-budget-procurement-rdte-data
git clone https://github.com/GSA/srt-fbo-scraper
git clone https://github.com/mt-digital/contracts

# Set environment variables
export SAM_API_KEY=your_sam_key
```

---

## Sources

- [makegov/awesome-procurement-data](https://github.com/makegov/awesome-procurement-data)
- [dherincx92/fpds](https://github.com/dherincx92/fpds)
- [540co/dod-president-budget-procurement-rdte-data](https://github.com/540co/dod-president-budget-procurement-rdte-data)
- [fedspendingtransparency/usaspending-api](https://github.com/fedspendingtransparency/usaspending-api)
- [GSA/srt-fbo-scraper](https://github.com/GSA/srt-fbo-scraper)
- [mt-digital/contracts](https://github.com/mt-digital/contracts)
- [speedyapply/JobSpy](https://github.com/speedyapply/JobSpy)
- [marcdacosta/usajobs-scrape](https://github.com/marcdacosta/usajobs-scrape)
- [makegov/procurement-tools](https://github.com/makegov/procurement-tools)
- [18F/pyfpds](https://github.com/18F/pyfpds)
- [bsweger/usaspending-scripts](https://github.com/bsweger/usaspending-scripts)
- [SAM.gov API Documentation](https://open.gsa.gov/api/get-opportunities-public-api/)
- [USAspending API](https://api.usaspending.gov/)
