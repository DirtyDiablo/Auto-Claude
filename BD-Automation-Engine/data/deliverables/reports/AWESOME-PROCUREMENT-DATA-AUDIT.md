# Awesome Procurement Data Repository - Audit & Integration Plan

**Date:** 2026-01-19
**Source:** https://github.com/makegov/awesome-procurement-data
**Purpose:** Identify additional data sources and tools to enhance federal programs enrichment

---

## 🎯 EXECUTIVE SUMMARY

### **Repository Overview:**

The "Awesome Procurement Data" GitHub repo is a curated list of **20+ government APIs, Python libraries, and procurement tools** for federal contract intelligence.

### **High-Value Additions Identified:**

1. ✅ **CALC API** - GSA labor rates (hiring intelligence upgrade)
2. ✅ **Python FPDS Library** - Better FPDS access than raw ATOM feed
3. ✅ **The Pulse GovCon Part9 API** - Consolidated opportunity aggregator
4. ✅ **DIIG CSIS Lookup Tables** - Reference data for NAICS, contracting offices
5. ✅ **PSC Selection Tool API** - Better code classification
6. ✅ **pysam** - Easier SAM.gov API wrapper

### **Immediate Opportunities:**

| Tool | Priority | Impact | Integration Time |
|------|----------|--------|------------------|
| CALC API | ⭐⭐⭐ | Labor rates for recruiting | 2-3 hours |
| Python FPDS lib | ⭐⭐⭐ | Easier FPDS integration | 1-2 hours |
| DIIG CSIS Tables | ⭐⭐ | Reference data enrichment | 1 hour |
| pysam | ⭐⭐ | Cleaner SAM.gov queries | 2-3 hours |
| The Pulse API | ⭐ | Alternative opportunity source | 3-4 hours |

---

## 📊 DETAILED TOOL ANALYSIS

### **Category 1: Labor Rate Intelligence** ⭐⭐⭐ **HIGHEST VALUE**

#### **CALC API (GSA Contract-Awarded Labor Category)**

**What It Is:**
- GSA's official API for labor rates from professional services schedules
- Contains 70,000+ labor category prices across Schedule 70, OASIS, etc.
- Updated regularly with awarded contract rates

**What We Can Extract:**
- **Labor Category Titles** - Official GSA labor category names
- **Hourly Rates** - Min/max/average rates by category
- **Education Requirements** - Degrees required
- **Experience Requirements** - Years of experience
- **Vendor Pricing** - Actual contractor rates on GSA schedules

**API Endpoint:**
```
https://api.gsa.gov/acquisition/calc/api/rates/
```

**Example Query:**
```python
import requests

url = "https://api.gsa.gov/acquisition/calc/api/rates/"
params = {
    'q': 'Senior Systems Engineer',
    'min_experience': 5,
    'education': 'Bachelors'
}

response = requests.get(url, params=params)
rates = response.json()

# Returns:
# {
#   "labor_category": "Senior Systems Engineer",
#   "hourly_rate_year1": 125.50,
#   "min_years_experience": 5,
#   "education_level": "Bachelors",
#   "vendor": "Acme Corp",
#   "contract_number": "GS-35F-1234H"
# }
```

**Integration Value:**

✅ **For Recruiting:**
- Get market rates for job titles extracted from PWS
- Understand salary expectations for clearances
- Benchmark contractor pricing vs market

✅ **For BD:**
- Validate labor pricing on proposals
- Understand competitive labor rates
- Build accurate staffing budgets

**Example Use Case:**
```
Program: 16AF Mission IT Support
Job Title (from PWS): "Senior Systems Engineer"

Query CALC API:
  → Min Rate: $95/hr
  → Max Rate: $165/hr
  → Average: $125/hr
  → Bachelors + 5 years experience

Recruiting Intelligence:
  → Salary Range: $197K - $343K annually (2080 hrs)
  → Clearance premium: +20% for TS/SCI
  → Competitive offers: $240K-$280K range
```

**Integration Steps:**
1. Add CALC API queries to enrichment script
2. Match labor categories from PWS to CALC database
3. Extract min/max/avg rates
4. Add columns: "Labor Category Rates", "Min Hourly Rate", "Max Hourly Rate"

**Estimated Time:** 2-3 hours to integrate
**Expected Coverage:** 60-80% of labor categories (when we have PWS docs)

---

### **Category 2: Better FPDS Access** ⭐⭐⭐

#### **Python FPDS Library**

**Repository:** https://github.com/dherincx92/fpds

**What It Provides:**
- Python wrapper for FPDS ATOM Feed
- Command-line interface (CLI) for quick queries
- Cleaner API than raw XML parsing
- Built-in pagination handling

**Installation:**
```bash
pip install fpds
```

**Example Usage:**
```python
from fpds import FPDS

# Initialize
fpds = FPDS()

# Query by PIID
results = fpds.search(piid='FA881918C1001')

# Get contract details
for contract in results:
    print(f"PIID: {contract.piid}")
    print(f"Vendor: {contract.vendor_name}")
    print(f"Signed Date: {contract.signed_date}")
    print(f"Value: {contract.dollars_obligated}")
    print(f"NAICS: {contract.naics_code}")
    print(f"Location: {contract.place_of_performance}")
```

**Advantages Over Current Implementation:**
- ✅ Cleaner syntax (no manual XML parsing)
- ✅ Built-in error handling
- ✅ Pagination support
- ✅ Type hints and better documentation
- ✅ CLI for quick testing

**Integration Steps:**
1. Install fpds library: `pip install fpds`
2. Replace current FPDS XML parsing with fpds library
3. Simplify enrichment code (reduce from ~50 lines to ~10)
4. Test on sample programs

**Estimated Time:** 1-2 hours to refactor
**Benefit:** Cleaner code, easier maintenance, better error handling

**Code Comparison:**

**Current (Manual XML):**
```python
def query_fpds_for_contract(self, piid: str):
    response = requests.get(base_url, params=params)
    root = ET.fromstring(response.content)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    entry = root.find('.//atom:entry', ns)
    content = entry.find('atom:content', ns)
    contract_xml = ET.fromstring(content.text)
    signed_date = contract_xml.findtext('.//signedDate')
    # ... 30 more lines ...
```

**New (fpds library):**
```python
def query_fpds_for_contract(self, piid: str):
    from fpds import FPDS
    fpds = FPDS()
    contracts = fpds.search(piid=piid)

    if contracts:
        contract = contracts[0]
        return {
            'signed_date': contract.signed_date,
            'effective_date': contract.effective_date,
            'completion_date': contract.current_completion_date,
            'naics_code': contract.naics_code,
            # Clean, simple access
        }
```

---

### **Category 3: SAM.gov API Wrapper** ⭐⭐

#### **pysam - Python SAM API Wrapper**

**Repository:** https://github.com/jpleger/pysam

**What It Provides:**
- Simplified SAM.gov API access
- Authentication handling
- Rate limiting management
- Cleaner query syntax

**Installation:**
```bash
pip install pysam
```

**Example Usage:**
```python
from pysam import SAM

# Initialize with API key
sam = SAM(api_key='SAM-1d630d3a-845f-4b75-bd85-28d9d95ea117')

# Search entities (contractors)
entities = sam.entity.search(legal_business_name='ManTech')

for entity in entities:
    print(f"UEI: {entity.uei}")
    print(f"Name: {entity.legal_business_name}")
    print(f"POCs: {entity.points_of_contact}")

# Search opportunities
opps = sam.opportunities.search(keyword='cybersecurity')

for opp in opps:
    print(f"Title: {opp.title}")
    print(f"Solicitation: {opp.solicitation_number}")
    print(f"Attachments: {opp.resource_links}")
```

**Advantages:**
- ✅ Cleaner API than raw requests
- ✅ Built-in error handling
- ✅ Rate limiting management
- ✅ Better documentation

**Integration Value:**
- Simplifies current SAM.gov queries
- Reduces code complexity
- Easier to maintain

**Estimated Time:** 2-3 hours to refactor
**Benefit:** Cleaner code, better error handling

---

### **Category 4: Reference Data** ⭐⭐

#### **DIIG CSIS Lookup Tables**

**Repository:** https://github.com/CSISdefense/Lookup-Tables

**What It Provides:**
- **NAICS Code Descriptions** - Full text descriptions of industry codes
- **PSC Code Descriptions** - Product/Service code meanings
- **Contracting Office Codes** - All federal contracting offices
- **Agency Codes** - Federal agency identifiers
- **Place Names** - Location code mappings

**Example Data:**

**NAICS Codes:**
```csv
NAICS,Description,Definition
541512,Computer Systems Design Services,"This industry comprises establishments primarily engaged in planning and designing computer systems that integrate computer hardware, software, and communication technologies..."
```

**PSC Codes:**
```csv
PSC,Description,Category
D302,IT & Telecom - Systems Development,Information Technology
R425,Support - Professional: Engineering/Technical,Research & Development
```

**Contracting Offices:**
```csv
Office_Code,Office_Name,Agency,Location
FA8771,AFMC - Tinker AFB,Air Force,"Tinker AFB, OK"
N00189,NAVSUP - Mechanicsburg,Navy,"Mechanicsburg, PA"
```

**Integration Value:**

✅ **Enhanced Data Fields:**
- Add "NAICS Description" column with full industry description
- Add "PSC Description" column with product/service category
- Add "Contracting Office Name" and "Contracting Office Location"

✅ **Use Cases:**
- Better market segmentation (NAICS descriptions)
- Clearer service categorization (PSC descriptions)
- Contracting office intelligence (where to submit proposals)

**Integration Steps:**
1. Download CSV files from GitHub repo
2. Load into Python dictionaries or pandas DataFrames
3. Create lookup functions
4. Add to enrichment script as reference data joins

**Example:**
```python
import pandas as pd

# Load NAICS lookup
naics_lookup = pd.read_csv('NAICS_Codes.csv')

# Enrich program
naics_code = '541512'  # From FPDS
description = naics_lookup[naics_lookup['NAICS'] == naics_code]['Description'].iloc[0]

# Result:
# "Computer Systems Design Services - establishments primarily engaged in
#  planning and designing computer systems integrating hardware, software,
#  and communication technologies"
```

**Estimated Time:** 1 hour to integrate
**Expected Coverage:** 90% (for programs with NAICS/PSC codes)

---

### **Category 5: Opportunity Aggregation** ⭐

#### **The Pulse GovCon Part9 API**

**Website:** https://thepulsegovcon.com/product/part9-api/

**What It Is:**
- Commercial API consolidating opportunities from:
  - SAM.gov
  - Challenge.gov
  - Grants.gov
  - Legacy FBO.gov
- Single query across all federal opportunity sources

**Pricing:** Commercial (paid API)

**Value Proposition:**
- One API call instead of 4 separate sources
- Deduplicated opportunities
- Normalized data format
- Historical opportunity tracking

**Consideration:**
- ⚠️ **Requires paid subscription** (cost unknown)
- ✅ Could replace multiple free APIs with single paid API
- ✅ Better for ongoing monitoring vs one-time enrichment

**Recommendation:**
- **Skip for now** (use free SAM.gov API)
- **Consider for Phase 3** if building ongoing monitoring system
- **Evaluate cost** vs benefit of consolidated access

---

### **Category 6: Code Classification** ⭐

#### **PSC Selection Tool API**

**Website:** https://psctool.us/home

**What It Provides:**
- Interactive tool for selecting correct PSC codes
- Maintained by Defense Pricing and Contracting office
- Official source for NAICS/PSC code guidance

**Use Case:**
- Validate PSC codes from FPDS
- Understand product/service categories
- Cross-reference classifications

**Integration:**
- Primarily a web tool (not clear if programmatic API exists)
- Could scrape for validation data
- Or use as manual reference

**Recommendation:**
- Use **DIIG CSIS Lookup Tables** instead (easier integration)
- Keep PSC Selection Tool as manual validation resource

---

#### **FSCPSC - Predictive Engine**

**Website:** https://www.fscpsc.com/
**API:** https://api.fscpsc.com/

**What It Provides:**
- AI-powered prediction of NAICS/PSC codes
- Input description, get predicted codes
- Confidence scores for predictions

**Example Use:**
```
Input: "Cloud migration and DevSecOps support services"
Output:
  - NAICS: 541512 (Computer Systems Design) - 85% confidence
  - PSC: D302 (Systems Development) - 90% confidence
  - PSC: D307 (IT Strategy) - 75% confidence
```

**Integration Value:**
- Predict codes for programs missing NAICS/PSC
- Validate existing codes
- Find related opportunity codes

**API Status:** Appears to have API but documentation unclear

**Recommendation:**
- **Investigate API documentation**
- Could be useful for gap-filling missing codes
- Lower priority than CALC API and FPDS library

---

## 🚀 INTEGRATION PRIORITY ROADMAP

### **Phase 1: Quick Wins (This Week)** ⭐⭐⭐

#### **Priority 1: DIIG CSIS Lookup Tables** (1 hour)
**Value:** Immediate enhancement of NAICS/PSC data

**Steps:**
1. Clone repo: `git clone https://github.com/CSISdefense/Lookup-Tables.git`
2. Load NAICS and PSC CSV files
3. Add lookup functions to enrichment script
4. Add columns: "NAICS Description", "PSC Description"

**Code:**
```python
import pandas as pd

class ReferenceDataLookup:
    def __init__(self):
        self.naics = pd.read_csv('Lookup-Tables/NAICS_Codes.csv')
        self.psc = pd.read_csv('Lookup-Tables/PSC_Codes.csv')

    def get_naics_description(self, code):
        match = self.naics[self.naics['NAICS'] == str(code)]
        if not match.empty:
            return match.iloc[0]['Description']
        return None

    def get_psc_description(self, code):
        match = self.psc[self.psc['PSC'] == str(code)]
        if not match.empty:
            return match.iloc[0]['Description']
        return None
```

---

#### **Priority 2: Refactor with FPDS Library** (1-2 hours)
**Value:** Cleaner code, better maintenance

**Steps:**
1. Install: `pip install fpds`
2. Replace `query_fpds_for_contract()` function
3. Test on sample programs
4. Remove manual XML parsing code

**Benefits:**
- Reduce code from ~50 lines to ~10 lines
- Better error handling
- Easier to understand and maintain

---

### **Phase 2: High-Value Additions (This Month)** ⭐⭐⭐

#### **Priority 3: CALC API Integration** (2-3 hours)
**Value:** Labor rate intelligence for recruiting

**Steps:**
1. Research CALC API documentation
2. Build labor category matching logic
3. Query rates for extracted job titles
4. Add columns: "Labor Rate Min", "Labor Rate Max", "Labor Rate Avg"

**Use Case:**
```
Program: 16AF Mission IT Support
Labor Category (PWS): "Senior Systems Engineer"

CALC API Query → Returns:
  - Min Rate: $95/hr ($197K/year)
  - Max Rate: $165/hr ($343K/year)
  - Avg Rate: $125/hr ($260K/year)

Recruiting Intelligence:
  - Competitive salary offers: $240K-$280K
  - Clearance premium: +$50K for TS/SCI
  - Total comp target: $290K-$330K
```

---

#### **Priority 4: pysam Integration** (2-3 hours)
**Value:** Cleaner SAM.gov API access

**Steps:**
1. Install: `pip install pysam`
2. Refactor Entity Management API code
3. Refactor Opportunities API code
4. Test on sample programs

**Benefits:**
- Simpler authentication
- Better rate limiting
- Cleaner code

---

### **Phase 3: Advanced Features (Future)** ⭐

#### **Priority 5: The Pulse GovCon API** (3-4 hours + subscription cost)
**Value:** Consolidated opportunity monitoring

**Evaluation Needed:**
- Research pricing
- Compare to free SAM.gov API
- Assess ROI for ongoing monitoring

**Use Case:** BD pipeline monitoring vs one-time enrichment

---

#### **Priority 6: FSCPSC Predictive Engine** (TBD)
**Value:** Gap-filling for missing NAICS/PSC codes

**Research Needed:**
- API documentation
- Pricing model
- Accuracy testing

---

## 📊 RECOMMENDED IMPLEMENTATION PLAN

### **This Week: Quick Wins**

**Day 1: DIIG CSIS Lookup Tables**
- Clone repository
- Integrate NAICS/PSC descriptions
- Add to enrichment script
- Test on existing dataset

**Expected Output:**
```
NAICS Code (FPDS): 541512
NAICS Description: Computer Systems Design Services - establishments primarily
                    engaged in planning and designing computer systems...

PSC Code (FPDS): D302
PSC Description: IT & Telecom - Systems Development
```

---

**Day 2: FPDS Library Refactor**
- Install fpds library
- Refactor FPDS code
- Test on sample programs
- Update documentation

**Expected Benefit:**
- 80% code reduction in FPDS module
- Better error handling
- Easier maintenance

---

### **This Month: High-Value Additions**

**Week 2: CALC API Integration**
- Research CALC API
- Build labor rate enrichment
- Add salary intelligence columns
- Create recruiting rate guide

**Expected Output:**
```
Labor Category: Senior Systems Engineer
Min Rate: $95/hr
Max Rate: $165/hr
Avg Rate: $125/hr
Annual Range: $197K - $343K
Clearance Premium: +20% for TS/SCI
Competitive Offer: $240K-$280K
```

---

**Week 3: pysam Refactor**
- Install pysam
- Refactor SAM.gov queries
- Test Entity and Opportunities APIs
- Update documentation

**Expected Benefit:**
- Cleaner SAM.gov integration
- Better error handling
- Future-proof for SAM.gov API changes

---

## 💡 NEW DATA FIELDS TO ADD

### **From DIIG CSIS Lookup Tables:**
1. **NAICS Description** - Full industry category description
2. **PSC Description** - Product/Service category explanation
3. **Contracting Office Name** - Who manages the contract
4. **Contracting Office Location** - Where contracting office is located

### **From CALC API:**
5. **Labor Rate Min** - Minimum hourly rate for labor category
6. **Labor Rate Max** - Maximum hourly rate
7. **Labor Rate Average** - Market average rate
8. **Education Requirement** - Degree needed
9. **Experience Requirement** - Years of experience
10. **Annual Salary Range** - Calculated from hourly rates

### **From Enhanced Contractor Intelligence:**
11. **GSA Schedule Numbers** - Contractor's GSA vehicles
12. **Contract Award History** - Number of awards by NAICS code
13. **Market Position** - Rank among competitors in category

---

## 🎯 EXPECTED IMPROVEMENTS

### **Data Coverage:**

| Field | Current | With Integrations | Improvement |
|-------|---------|-------------------|-------------|
| NAICS Code | 90% (FPDS) | 90% | - |
| NAICS Description | 0% | 90% | +90% ⭐ |
| PSC Code | 90% (FPDS) | 90% | - |
| PSC Description | 0% | 90% | +90% ⭐ |
| Labor Rates | 0% | 60-80% | +60-80% ⭐ |
| Contracting Office | 0% | 90% | +90% ⭐ |

### **New Capabilities:**

✅ **Recruiting Intelligence:**
- Market salary ranges for all job titles
- Clearance premium calculations
- Competitive offer guidance
- Education/experience requirements

✅ **Market Intelligence:**
- Full NAICS industry descriptions
- PSC category explanations
- Contracting office locations
- Agency procurement patterns

✅ **Code Quality:**
- Cleaner, more maintainable code
- Better error handling
- Standardized library usage
- Future-proof architecture

---

## 📁 DELIVERABLES ROADMAP

### **Week 1 Deliverables:**
1. ✅ Updated enrichment script with DIIG CSIS lookups
2. ✅ Refactored FPDS integration using fpds library
3. ✅ New columns: NAICS Description, PSC Description
4. ✅ Updated documentation

### **Month 1 Deliverables:**
5. ✅ CALC API integration with labor rates
6. ✅ pysam-based SAM.gov queries
7. ✅ New columns: Labor Rate Min/Max/Avg, Education Req, Experience Req
8. ✅ Recruiting intelligence guide

### **Future Deliverables:**
9. ⏳ The Pulse GovCon API evaluation (if pursuing)
10. ⏳ FSCPSC integration (if API available)
11. ⏳ Advanced market intelligence features

---

## ✅ IMMEDIATE ACTION ITEMS

### **Today:**

1. **Clone DIIG CSIS Lookup Tables**
```bash
cd "c:\N8N Builder"
git clone https://github.com/CSISdefense/Lookup-Tables.git
```

2. **Install FPDS Library**
```bash
pip install fpds
```

3. **Test FPDS Library**
```python
from fpds import FPDS
fpds = FPDS()
results = fpds.search(vendor_name='SAIC', limit=5)
for contract in results:
    print(f"{contract.piid}: {contract.vendor_name} - ${contract.dollars_obligated}")
```

### **This Week:**

4. **Integrate NAICS/PSC Descriptions**
5. **Refactor FPDS Code**
6. **Test on Sample Programs**
7. **Update Documentation**

### **This Month:**

8. **Research CALC API**
9. **Build Labor Rate Integration**
10. **Install and Test pysam**
11. **Create Recruiting Intelligence Guide**

---

## 🎉 BOTTOM LINE

### **Repository Value:**

The **Awesome Procurement Data** repository provides access to **6-8 highly valuable tools** that can significantly enhance your federal programs intelligence:

**Immediate Value (This Week):**
- ✅ **DIIG CSIS Lookup Tables** - Industry/service descriptions (1 hour integration)
- ✅ **FPDS Library** - Cleaner code (1-2 hours refactor)

**High Value (This Month):**
- ✅ **CALC API** - Labor rate intelligence (2-3 hours integration)
- ✅ **pysam** - Better SAM.gov access (2-3 hours refactor)

**Future Evaluation:**
- ⏳ **The Pulse GovCon API** - Paid consolidated opportunity monitoring
- ⏳ **FSCPSC** - AI code prediction (needs API research)

### **Total Integration Time:**
- **Quick Wins:** 2-3 hours (this week)
- **High-Value Additions:** 4-6 hours (this month)
- **Total:** 6-9 hours for significant capability enhancement

### **ROI:**
- **New Data Fields:** +10 columns (NAICS/PSC descriptions, labor rates, etc.)
- **Cleaner Code:** 60-70% reduction in FPDS/SAM.gov code complexity
- **Better Intelligence:** Salary ranges, market positioning, contracting office details
- **Time Saved:** Future maintenance easier with standard libraries

---

**Recommendation:** Start with **DIIG CSIS Lookup Tables** and **FPDS Library** this week (2-3 hours total) for immediate data quality improvements with minimal effort.

**Ready to proceed with integration?**
