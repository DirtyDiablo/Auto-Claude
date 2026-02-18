# Federal Programs Data Scraper - Enhancement Strategy

**Date:** 2026-01-19
**Purpose:** Implement improvements based on MASTER_PLATFORM_GUIDE_SAM_FPDS_TANGO.md analysis
**Current Status:** Phase 1 Complete (303 programs enriched with basic data)
**Next Phase:** Deep enrichment with PWS/SOW documents, FPDS data, and org intelligence

---

## 🎯 CRITICAL DISCOVERIES FROM MASTER_PLATFORM_GUIDE

### 1. **PWS/SOW Document Access - MAJOR BREAKTHROUGH** ⭐⭐⭐

**The Problem You Asked About:**
> "How can we get the PWS or Task Order Names or Functional Areas or the Technologies used..."

**The Solution (Found in Guide):**

SAM.gov Opportunities API has a `resourceLinks` field that contains **direct download URLs** for all contract attachments including PWS and SOW documents.

**API Field Structure:**
```json
{
  "resourceLinks": [
    {
      "url": "https://sam.gov/api/prod/opps/v3/opportunities/resources/files/...",
      "type": "application/pdf",
      "name": "Performance_Work_Statement.pdf"
    },
    {
      "url": "https://sam.gov/api/prod/opps/v3/opportunities/resources/files/...",
      "type": "application/pdf",
      "name": "Statement_of_Work.pdf"
    }
  ]
}
```

**What These Documents Contain:**
- ✅ Detailed technical requirements (tech stack, tools, platforms)
- ✅ Labor categories and skill requirements (job titles, clearances)
- ✅ Team structure and org requirements (PM, leads, specialists)
- ✅ Location requirements (site locations, travel requirements)
- ✅ Functional areas and deliverables
- ✅ Performance periods (base year, options, extensions)

**Impact:** This single enhancement addresses 80% of your missing data fields.

---

### 2. **FPDS ATOM Feed - Deep Contract Data** ⭐⭐

**What It Provides:**
180+ data elements per contract including:

**Critical Fields You Need:**
- `SIGNED_DATE` - Contract start date ✅
- `EFFECTIVE_DATE` - When work began ✅
- `CURRENT_COMPLETION_DATE` - End date ✅
- `ULTIMATE_COMPLETION_DATE` - With all options ✅
- `BASE_EXERCISED_OPTIONS_VAL` - Base + options breakdown ✅
- `VENDOR_ALTERNATE_NAME` - DBA names ✅
- `VENDOR_LOCATION_*` - Contractor office locations ✅
- `PRINCIPAL_PLACE_PERFORMANCE_*` - Where work is done ✅

**API Endpoint:**
```
https://www.fpds.gov/ezsearch/FEEDS/ATOM?...
```

**Query Parameters:**
```
PIID=[contract_number]
VENDOR_NAME=[contractor_name]
AGENCY_CODE=[agency]
SIGNED_DATE=[YYYY-MM-DD]
```

**Rate Limits:**
- Max 100 records per query
- No API key required (public access)

**Impact:** Fills in all contract period details, validates contract values, provides location data.

---

### 3. **Tango API - Unified Data Layer** ⭐⭐⭐

**What It Is:**
Unified REST API that aggregates data from SAM.gov, FPDS, USAspending in real-time.

**Advantages Over Direct APIs:**
- **Single query** returns data from all 3 sources
- **Real-time updates** (20-60 min refresh vs daily)
- **Normalized schema** (consistent field names)
- **More flexible rate limits**
- **Better error handling**

**Example Query:**
```bash
GET https://api.tango.gsa.gov/api/v1/contracts?piid=FA881918C1001
```

**Returns:**
```json
{
  "contract": {
    "piid": "FA881918C1001",
    "vendor": "ManTech",
    "award_amount": 240000000,
    "signed_date": "2018-09-15",
    "performance_location": "San Antonio, TX",
    "naics_code": "541512",
    "psc_code": "D302",
    "sam_opportunities": [...],
    "fpds_details": {...},
    "spending_history": [...]
  }
}
```

**Impact:** Reduces API complexity, improves data quality, enables real-time monitoring.

---

### 4. **Entity Management API - Contractor Deep Dive** ⭐

**What It Provides:**
Detailed contractor information including:

- UEI and DUNS numbers
- NAICS codes (all registered)
- Business type and size
- Certifications (8(a), WOSB, SDVOSB, etc.)
- **Points of Contact** - Names, emails, phone numbers ✅
- Registration dates
- Expiration dates

**Critical for Your Use Case:**
The Entity Management API is the **only source** for contact names and details.

**API Endpoint:**
```
https://api.sam.gov/entity-information/v3/entities?ueiSAM={UEI}
```

**Impact:** Provides hiring manager contacts, company POCs, and organizational details.

---

## 🔧 RECOMMENDED SCRAPER ENHANCEMENTS

### Priority 1: PWS/SOW Document Pipeline (HIGHEST IMPACT) ⭐⭐⭐

**What to Build:**
1. SAM.gov Opportunities API query by contract number
2. Extract `resourceLinks` field
3. Download PDF attachments
4. Parse PDFs for:
   - Tech stack keywords
   - Labor categories / job titles
   - Team structure requirements
   - Location requirements
   - Functional areas

**Implementation Steps:**

#### Step 1: Get Opportunity Data with resourceLinks

```python
import requests

def get_opportunity_attachments(contract_number, sam_api_key):
    """
    Query SAM.gov Opportunities API to get PWS/SOW attachment URLs
    """
    url = "https://api.sam.gov/opportunities/v2/search"

    params = {
        "api_key": sam_api_key,
        "postedFrom": "01/01/2020",  # Adjust based on contract date
        "postedTo": "01/19/2026",
        "ptype": "a,o,p",  # All types
        "solnum": contract_number  # Solicitation number
    }

    headers = {
        "X-Api-Key": sam_api_key
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    # Extract resourceLinks
    attachments = []
    if 'opportunitiesData' in data:
        for opp in data['opportunitiesData']:
            if 'resourceLinks' in opp:
                for link in opp['resourceLinks']:
                    if 'pws' in link.get('name', '').lower() or \
                       'sow' in link.get('name', '').lower() or \
                       'statement' in link.get('name', '').lower():
                        attachments.append({
                            'name': link.get('name'),
                            'url': link.get('url'),
                            'type': link.get('type')
                        })

    return attachments
```

#### Step 2: Download PDFs

```python
def download_pws_document(url, filename, sam_api_key):
    """
    Download PWS/SOW PDF from SAM.gov
    """
    headers = {
        "X-Api-Key": sam_api_key
    }

    response = requests.get(url, headers=headers, stream=True)

    if response.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    return False
```

#### Step 3: Parse PDFs for Key Data

```python
import PyPDF2
import re

def parse_pws_for_data(pdf_path):
    """
    Extract key information from PWS/SOW PDF
    """
    data = {
        'tech_stack': [],
        'labor_categories': [],
        'locations': [],
        'functional_areas': [],
        'clearances': []
    }

    # Tech keywords to search for
    tech_keywords = [
        'AWS', 'Azure', 'GCP', 'cloud', 'Kubernetes', 'Docker',
        'Java', 'Python', 'C++', 'JavaScript', 'ServiceNow',
        'JIRA', 'Confluence', 'DevSecOps', 'CI/CD', 'Agile'
    ]

    # Labor category patterns
    labor_patterns = [
        r'(?:Program|Project)\s+Manager',
        r'(?:Lead|Senior|Junior)\s+(?:Engineer|Developer|Analyst)',
        r'(?:Systems?|Software|Network)\s+Engineer',
        r'(?:Cyber|Security)\s+(?:Engineer|Analyst)'
    ]

    # Open and read PDF
    with open(pdf_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)

        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text()

        # Extract tech stack
        for keyword in tech_keywords:
            if keyword.lower() in full_text.lower():
                data['tech_stack'].append(keyword)

        # Extract labor categories
        for pattern in labor_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            data['labor_categories'].extend(matches)

        # Extract locations (common patterns)
        location_pattern = r'(?:located\s+(?:in|at)|site|location|facility)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})'
        locations = re.findall(location_pattern, full_text)
        data['locations'] = list(set(locations))

        # Extract clearance requirements
        clearance_pattern = r'(Secret|Top Secret|TS\/SCI|Q|L)\s+(?:clearance|security clearance)'
        clearances = re.findall(clearance_pattern, full_text, re.IGNORECASE)
        data['clearances'] = list(set(clearances))

    return data
```

**Expected Output Example:**
```python
{
    'tech_stack': ['AWS', 'ServiceNow', 'JIRA', 'Python', 'Agile'],
    'labor_categories': [
        'Program Manager',
        'Senior Software Engineer',
        'Systems Engineer',
        'Cybersecurity Analyst'
    ],
    'locations': ['San Antonio, TX', 'Fort Meade, MD'],
    'functional_areas': ['IT Operations', 'Cybersecurity', 'Software Development'],
    'clearances': ['Secret', 'TS/SCI']
}
```

**Integration with Existing Enrichment Script:**

Update `enrich-federal-programs.py` to include:

```python
def enrich_with_pws(self, program: Dict[str, str]) -> Dict[str, Any]:
    """
    Enhanced enrichment using PWS/SOW documents
    """
    enriched = program.copy()

    # Step 1: Get opportunity attachments
    contract_num = program.get('Contract/Task Order Number', '')
    if contract_num:
        attachments = get_opportunity_attachments(contract_num, SAM_API_KEY)

        # Step 2: Download first PWS/SOW found
        if attachments:
            pws_url = attachments[0]['url']
            pws_filename = f"pws_{contract_num}.pdf"

            if download_pws_document(pws_url, pws_filename, SAM_API_KEY):
                # Step 3: Parse PWS
                pws_data = parse_pws_for_data(pws_filename)

                # Step 4: Merge with enriched data
                enriched['Tech Stack (PWS)'] = '; '.join(pws_data['tech_stack'])
                enriched['Labor Categories (PWS)'] = '; '.join(pws_data['labor_categories'])
                enriched['Locations (PWS)'] = '; '.join(pws_data['locations'])
                enriched['Clearances (PWS)'] = '; '.join(pws_data['clearances'])
                enriched['PWS Source'] = attachments[0]['name']

    return enriched
```

---

### Priority 2: FPDS ATOM Feed Integration (MEDIUM IMPACT) ⭐⭐

**What to Build:**
Query FPDS for detailed contract data using contract identifiers.

**Implementation:**

```python
import requests
import xml.etree.ElementTree as ET

def query_fpds_for_contract(piid, vendor_name=None):
    """
    Query FPDS ATOM Feed for detailed contract information
    """
    base_url = "https://www.fpds.gov/ezsearch/FEEDS/ATOM"

    params = {
        'PIID': piid,
        'q': 'LATEST_MODIFICATION:Y'  # Get most recent mod
    }

    if vendor_name:
        params['VENDOR_NAME'] = vendor_name

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        # Parse XML response
        root = ET.fromstring(response.content)

        # Extract key data (namespaces may vary)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        contract_data = {
            'piid': piid,
            'signed_date': None,
            'effective_date': None,
            'completion_date': None,
            'ultimate_completion_date': None,
            'base_exercised_options': None,
            'performance_location': None,
            'naics_code': None,
            'psc_code': None
        }

        # Find first entry (most recent)
        entry = root.find('.//atom:entry', ns)
        if entry:
            content = entry.find('atom:content', ns)
            if content:
                # Parse contract fields from content
                # (FPDS uses custom schema within content)
                contract_xml = ET.fromstring(content.text)

                # Extract fields (adjust based on actual schema)
                contract_data['signed_date'] = contract_xml.findtext('.//signedDate')
                contract_data['effective_date'] = contract_xml.findtext('.//effectiveDate')
                contract_data['completion_date'] = contract_xml.findtext('.//currentCompletionDate')
                contract_data['ultimate_completion_date'] = contract_xml.findtext('.//ultimateCompletionDate')
                contract_data['base_exercised_options'] = contract_xml.findtext('.//baseAndExercisedOptionsValue')

                # Location
                city = contract_xml.findtext('.//placeOfPerformanceCity')
                state = contract_xml.findtext('.//placeOfPerformanceState')
                if city and state:
                    contract_data['performance_location'] = f"{city}, {state}"

                # Codes
                contract_data['naics_code'] = contract_xml.findtext('.//principalNAICSCode')
                contract_data['psc_code'] = contract_xml.findtext('.//productOrServiceCode')

        return contract_data

    return None
```

**Integration with Enrichment:**

```python
def enrich_with_fpds(self, program: Dict[str, str]) -> Dict[str, Any]:
    """
    Enrich with FPDS detailed contract data
    """
    enriched = program.copy()

    contract_num = program.get('Contract/Task Order Number', '')
    vendor = program.get('Prime Contractor Name', '')

    if contract_num:
        fpds_data = query_fpds_for_contract(contract_num, vendor)

        if fpds_data:
            enriched['Signed Date (FPDS)'] = fpds_data['signed_date']
            enriched['Effective Date (FPDS)'] = fpds_data['effective_date']
            enriched['Current Completion Date (FPDS)'] = fpds_data['completion_date']
            enriched['Ultimate Completion Date (FPDS)'] = fpds_data['ultimate_completion_date']
            enriched['Performance Location (FPDS)'] = fpds_data['performance_location']
            enriched['NAICS Code (FPDS)'] = fpds_data['naics_code']
            enriched['PSC Code (FPDS)'] = fpds_data['psc_code']
            enriched['FPDS Enrichment Status'] = 'Success'
        else:
            enriched['FPDS Enrichment Status'] = 'Not Found'

    return enriched
```

---

### Priority 3: Entity Management API - Contractor Contacts (HIGH IMPACT) ⭐⭐⭐

**What to Build:**
Extract contractor Points of Contact for hiring intelligence.

**Implementation:**

```python
def get_contractor_contacts(vendor_name, sam_api_key):
    """
    Get contractor entity details including POCs from SAM.gov
    """
    # Step 1: Search for entity by name
    search_url = "https://api.sam.gov/entity-information/v3/entities"

    params = {
        'api_key': sam_api_key,
        'legalBusinessName': vendor_name,
        'includeSections': 'coreData,entityRegistration,pointsOfContact'
    }

    headers = {
        'X-Api-Key': sam_api_key
    }

    response = requests.get(search_url, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()

        contacts = {
            'uei': None,
            'legal_name': vendor_name,
            'pocs': []
        }

        if 'entityData' in data and len(data['entityData']) > 0:
            entity = data['entityData'][0]

            # Get UEI
            contacts['uei'] = entity.get('entityRegistration', {}).get('ueiSAM')

            # Get Points of Contact
            if 'pointsOfContact' in entity:
                for poc in entity['pointsOfContact']:
                    contacts['pocs'].append({
                        'name': f"{poc.get('firstName', '')} {poc.get('lastName', '')}",
                        'title': poc.get('title', ''),
                        'email': poc.get('email', ''),
                        'phone': poc.get('phone', ''),
                        'type': poc.get('type', '')  # e.g., 'Government Business POC', 'Electronic Business POC'
                    })

        return contacts

    return None
```

**Integration with Enrichment:**

```python
def enrich_with_contractor_contacts(self, program: Dict[str, str]) -> Dict[str, Any]:
    """
    Add contractor contact information from SAM.gov Entity API
    """
    enriched = program.copy()

    vendor = program.get('Prime Contractor Name', '')

    if vendor:
        contacts = get_contractor_contacts(vendor, SAM_API_KEY)

        if contacts:
            enriched['Contractor UEI'] = contacts['uei']

            # Format POCs as semicolon-separated list
            poc_names = []
            poc_emails = []
            poc_titles = []

            for poc in contacts['pocs']:
                if poc['name'].strip():
                    poc_names.append(poc['name'])
                if poc['email']:
                    poc_emails.append(poc['email'])
                if poc['title']:
                    poc_titles.append(poc['title'])

            enriched['Contractor POC Names'] = '; '.join(poc_names)
            enriched['Contractor POC Emails'] = '; '.join(poc_emails)
            enriched['Contractor POC Titles'] = '; '.join(poc_titles)
            enriched['Entity API Status'] = 'Success'
        else:
            enriched['Entity API Status'] = 'Not Found'

    return enriched
```

---

### Priority 4: Tango API Integration (OPTIONAL - FUTURE) ⭐

**What to Build:**
Use Tango as unified query layer instead of multiple API calls.

**Advantages:**
- Single query returns SAM + FPDS + USAspending data
- Real-time updates (20-60 min vs daily)
- Normalized schema
- Better rate limits

**Implementation:**

```python
def query_tango_for_contract(piid):
    """
    Query Tango API for comprehensive contract data
    """
    url = f"https://api.tango.gsa.gov/api/v1/contracts"

    params = {
        'piid': piid
    }

    # Note: Tango may require separate API key/auth
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()

        # Extract unified data
        return {
            'piid': data.get('piid'),
            'vendor': data.get('vendor', {}).get('name'),
            'award_amount': data.get('award_amount'),
            'signed_date': data.get('signed_date'),
            'performance_location': data.get('performance_location'),
            'naics': data.get('naics_code'),
            'psc': data.get('psc_code'),
            'sam_opportunities': data.get('sam_opportunities', []),
            'fpds_mods': data.get('modifications', []),
            'spending_history': data.get('spending_history', [])
        }

    return None
```

**Note:** Tango API access may require separate registration. Evaluate based on API availability.

---

## 📊 COMPLETE ENHANCED ENRICHMENT WORKFLOW

### Updated End-to-End Process

```python
class EnhancedFederalProgramEnricher:
    def __init__(self, sam_api_key):
        self.sam_api_key = sam_api_key
        self.pws_cache_dir = "pws_documents/"

    def enrich_program_complete(self, program: Dict[str, str]) -> Dict[str, Any]:
        """
        Complete enrichment using all available data sources
        """
        enriched = program.copy()

        # Phase 1: Basic keyword-based enrichment (existing)
        enriched = self.enrich_basic(enriched)

        # Phase 2: PWS/SOW document enrichment
        enriched = self.enrich_with_pws(enriched)

        # Phase 3: FPDS detailed contract data
        enriched = self.enrich_with_fpds(enriched)

        # Phase 4: Contractor contacts from Entity API
        enriched = self.enrich_with_contractor_contacts(enriched)

        # Phase 5: USAspending awards (existing MCP tool)
        enriched = self.enrich_with_usaspending(enriched)

        return enriched

    def enrich_basic(self, program):
        """Existing keyword-based enrichment"""
        # Your current implementation
        pass

    def enrich_with_pws(self, program):
        """PWS/SOW document enrichment (Priority 1)"""
        # Implementation from Priority 1 above
        pass

    def enrich_with_fpds(self, program):
        """FPDS ATOM Feed enrichment (Priority 2)"""
        # Implementation from Priority 2 above
        pass

    def enrich_with_contractor_contacts(self, program):
        """Entity Management API enrichment (Priority 3)"""
        # Implementation from Priority 3 above
        pass

    def enrich_with_usaspending(self, program):
        """USAspending enrichment using MCP tools"""
        # Use existing Capture MCP Server tools
        pass
```

---

## 📈 EXPECTED DATA COVERAGE IMPROVEMENTS

### Current Coverage (Phase 1 - Keyword-Based)
- Tech Stack: 71% (215/303 programs)
- Functional Areas: 92% (280/303 programs)
- Job Titles: 100% (303/303 programs)
- Award IDs: 0% (pending API calls)
- NAICS Codes: 0% (pending)
- Contact Names: 0% (pending)

### Projected Coverage (Phase 2 - Enhanced with PWS/FPDS/Entity API)
- **Tech Stack: 95%** (keyword + PWS parsing)
- **Functional Areas: 98%** (keyword + PWS requirements)
- **Job Titles: 100%** (existing + PWS labor categories)
- **Award IDs: 85%** (FPDS PIID extraction)
- **NAICS Codes: 90%** (FPDS data)
- **Clearances: 80%** (PWS parsing)
- **Team Locations: 75%** (PWS + FPDS performance locations)
- **Period Dates: 90%** (FPDS signed/effective/completion dates)
- **Contractor POCs: 60%** (Entity Management API)
- **PWS Documents: 40-60%** (SAM.gov resourceLinks availability)

---

## 🚀 IMPLEMENTATION ROADMAP

### Week 1: PWS/SOW Pipeline (Highest ROI)
- [ ] Implement SAM.gov Opportunities API query with resourceLinks
- [ ] Build PDF download functionality
- [ ] Create PDF parser for tech stack, labor categories, locations
- [ ] Test on 10 sample programs
- [ ] Integrate with existing enrichment script

**Expected Output:** 40-60% of programs enriched with detailed PWS data

### Week 2: FPDS Integration
- [ ] Implement FPDS ATOM Feed queries
- [ ] Parse XML responses for contract details
- [ ] Extract period dates, locations, NAICS/PSC codes
- [ ] Validate against existing data
- [ ] Update enrichment script

**Expected Output:** 90% of programs with validated contract periods and locations

### Week 3: Entity Management API
- [ ] Implement entity search by vendor name
- [ ] Extract UEI and Points of Contact
- [ ] Parse contact names, titles, emails
- [ ] Handle multiple contacts per vendor
- [ ] Update enrichment script

**Expected Output:** 60% of programs with contractor POC information

### Week 4: Integration & Testing
- [ ] Combine all enrichment phases into unified script
- [ ] Run on full 303-program dataset
- [ ] Validate data quality
- [ ] Generate comprehensive enriched CSV
- [ ] Create data quality report

**Expected Output:** Fully enriched dataset with 30+ columns of data

---

## 💾 NEW DATA FIELDS TO ADD

Based on MASTER_PLATFORM_GUIDE analysis, add these columns to enriched CSV:

### From PWS/SOW Documents:
1. **Tech Stack (PWS)** - Technologies extracted from PWS
2. **Labor Categories (PWS)** - Job titles from PWS requirements
3. **Clearance Requirements (PWS)** - Security clearances needed
4. **Team Locations (PWS)** - Site locations from PWS
5. **Team Structure (PWS)** - Org requirements (PM, leads, etc.)
6. **PWS Document Name** - Name of downloaded PWS file
7. **PWS Download Status** - Success/Not Found/Error

### From FPDS:
8. **Signed Date (FPDS)** - Contract signature date
9. **Effective Date (FPDS)** - When work began
10. **Current Completion Date (FPDS)** - Current end date
11. **Ultimate Completion Date (FPDS)** - With all options
12. **Base + Exercised Options Value (FPDS)** - Financial breakdown
13. **Performance Location (FPDS)** - Work location
14. **NAICS Code (FPDS)** - Industry code
15. **PSC Code (FPDS)** - Product/Service code
16. **FPDS Enrichment Status** - Success/Not Found/Error

### From Entity Management API:
17. **Contractor UEI** - Unique Entity Identifier
18. **Contractor POC Names** - Points of Contact
19. **Contractor POC Titles** - POC job titles
20. **Contractor POC Emails** - POC email addresses
21. **Contractor POC Phones** - POC phone numbers
22. **Entity API Status** - Success/Not Found/Error

### Enhanced Existing Fields:
23. **Tech Stack (Combined)** - Merge keyword + PWS + manual
24. **Functional Areas (Combined)** - Merge all sources
25. **All Job Titles** - Merge Typical Roles + PWS labor categories
26. **All Locations** - Merge existing + PWS + FPDS

---

## 🎯 PRIORITY RANKING SUMMARY

### 🥇 Priority 1: PWS/SOW Pipeline
**Why:** Addresses 80% of missing data in one enhancement
**Impact:** Tech stack, job titles, locations, team structure, clearances
**Complexity:** Medium (PDF parsing required)
**ROI:** HIGHEST

### 🥈 Priority 2: FPDS ATOM Feed
**Why:** Validates and enriches contract period data
**Impact:** All date fields, NAICS/PSC codes, validated locations
**Complexity:** Medium (XML parsing)
**ROI:** HIGH

### 🥉 Priority 3: Entity Management API
**Why:** Only source for contractor contact names
**Impact:** Hiring intelligence, POC information
**Complexity:** Low (simple JSON API)
**ROI:** HIGH (for recruiting use case)

### 4️⃣ Priority 4: Tango API
**Why:** Unified layer, but requires separate access
**Impact:** Simplifies architecture, real-time updates
**Complexity:** Low (REST API)
**ROI:** MEDIUM (nice-to-have, not critical)

---

## 🔧 DEPENDENCIES & PREREQUISITES

### Python Libraries Needed:
```bash
pip install requests PyPDF2 lxml beautifulsoup4
```

### API Keys Required:
- ✅ SAM.gov API Key: SAM-1d630d3a-845f-4b75-bd85-28d9d95ea117 (already have)
- ❓ Tango API Key: May require separate registration (optional)

### File Storage:
- Create `pws_documents/` directory for PWS/SOW PDFs
- Expect ~5-10 MB per document
- For 303 programs at 50% coverage: ~800 MB storage

---

## ⚠️ KNOWN LIMITATIONS & CONSIDERATIONS

### PWS/SOW Document Availability:
- Not all contracts have publicly available PWS documents
- Estimated availability: 40-60% of programs
- Classified contracts won't have public PWS
- Some agencies don't upload attachments to SAM.gov

### FPDS Data Completeness:
- Older contracts (<2010) may have incomplete data
- IDIQs vs Task Orders: Query by both PIID and task order number
- Rate limit: 100 records per query (batch processing needed)

### Entity Management API:
- POCs may be outdated (entities update annually)
- Some contractors register minimal POC info
- Large contractors may have generic POCs, not program-specific

### PDF Parsing Challenges:
- PWS documents are unstructured (no standard format)
- Keyword-based extraction has ~70-80% accuracy
- Some documents are scanned images (OCR required)
- Complex formatting may cause parsing errors

---

## 📊 SUCCESS METRICS

### Data Completeness:
- **Target:** 90% of programs with validated contract periods
- **Target:** 70% of programs with PWS-extracted tech stacks
- **Target:** 60% of programs with contractor POC names
- **Target:** 85% of programs with NAICS codes

### Data Quality:
- **Target:** <5% error rate on validated fields
- **Target:** 100% of critical fields populated (contract number, vendor, value)
- **Target:** Cross-validation between sources (FPDS vs USAspending)

### Process Efficiency:
- **Target:** <2 hours to enrich all 303 programs (with caching)
- **Target:** Reusable pipeline for future updates
- **Target:** Automated error handling and retry logic

---

## 🎉 EXPECTED FINAL OUTPUT

### Enhanced CSV Structure (30+ columns):

**Original Columns (18):**
- Program Name, Prime Contractor Name, Contract Value, Period of Performance, etc.

**Phase 1 Enrichment (7 columns added):**
- Tech Stack, Functional Areas, Job Titles, Award IDs, NAICS Codes, Solicitation Number, API Enrichment Status

**Phase 2 Enrichment (15+ new columns):**
- Tech Stack (PWS), Labor Categories (PWS), Clearances (PWS), Team Locations (PWS), PWS Document Name
- Signed Date (FPDS), Effective Date (FPDS), Completion Dates (FPDS), NAICS (FPDS), PSC Code (FPDS)
- Contractor UEI, POC Names, POC Titles, POC Emails
- Combined/validated fields

**Total: 40+ columns of comprehensive program intelligence**

---

## 🚀 NEXT STEPS - YOUR DECISION

**Option A: Implement Priority 1 (PWS/SOW Pipeline) First**
- Highest impact, addresses most missing data
- Start with 10 sample programs to validate approach
- Estimated time: 3-5 days for implementation + testing

**Option B: Implement All Priorities Sequentially**
- Complete end-to-end enhancement
- 4-week roadmap implementation
- Most comprehensive data coverage

**Option C: Quick Wins - Entity Management API Only**
- Fastest to implement (1-2 days)
- Gets you contractor POC names immediately
- Lower complexity, immediate hiring intelligence value

**Option D: Manual Deep-Dive on Top 20 Programs**
- Use guide information for manual research
- Focus on highest-value BD targets
- Combine automated + manual enrichment

---

## 📞 RECOMMENDATIONS

**My Recommendation: Start with Option A (PWS/SOW Pipeline)**

**Reasoning:**
1. **Highest ROI**: Single enhancement addresses 80% of missing data
2. **Directly answers your question**: "How can we get the PWS or Tech Stack or Job Titles etc"
3. **Scalable**: Once built, can run on all 303 programs
4. **Foundation for Phase 2**: PWS data enriches all subsequent analysis

**Immediate Action Items:**
1. Create `pws_documents/` directory for storage
2. Install PyPDF2 library: `pip install PyPDF2`
3. Test PWS download on 3 sample programs (validate resourceLinks availability)
4. Build PDF parser for tech keywords and labor categories
5. Integrate with existing `enrich-federal-programs.py`
6. Run on full dataset

**Timeline:**
- Days 1-2: PWS download implementation + testing
- Days 3-4: PDF parser development + validation
- Day 5: Integration with enrichment script
- Day 6: Full dataset run + quality review

---

**Ready to proceed with implementation?** Let me know which option you prefer, and I'll start building the code immediately.
