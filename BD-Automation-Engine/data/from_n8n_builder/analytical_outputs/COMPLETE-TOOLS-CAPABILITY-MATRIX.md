# Complete Federal Programs Data Enrichment - Tools & Capability Matrix

**Date:** 2026-01-19
**Purpose:** Comprehensive audit of all data sources, tools, APIs, and MCP servers for federal programs enrichment

---

## 📊 CURRENT DATABASE STRUCTURE

### **Existing Columns (45 Total)**

#### **Original Columns (18):**
1. Program Name
2. Acronym
3. Agency Owner
4. BD Priority
5. Clearance Requirements
6. Confidence Level
7. Contract Value
8. Contract Vehicle
9. Key Locations
10. Keywords/Signals
11. Known Subcontractors
12. PTS Involvement
13. Period of Performance
14. Prime Contractor Name
15. Program Type
16. Recompete Date
17. Source Evidence
18. Typical Roles

#### **Added Columns - Basic Enrichment (3):**
19. Tech Stack (Basic)
20. Functional Areas (Basic)
21. Job Titles (Basic)

#### **Added Columns - PWS/SOW Pipeline (7):**
22. Tech Stack (PWS)
23. Labor Categories (PWS)
24. Clearances (PWS)
25. Team Locations (PWS)
26. Functional Areas (PWS)
27. PWS Document Name
28. PWS Download Status

#### **Added Columns - FPDS Integration (9):**
29. Signed Date (FPDS)
30. Effective Date (FPDS)
31. Current Completion Date (FPDS)
32. Ultimate Completion Date (FPDS)
33. Base + Options Value (FPDS)
34. Performance Location (FPDS)
35. NAICS Code (FPDS)
36. PSC Code (FPDS)
37. FPDS Enrichment Status

#### **Added Columns - Entity Management API (6):**
38. Contractor UEI
39. Contractor POC Names
40. Contractor POC Titles
41. Contractor POC Emails
42. Contractor POC Phones
43. Entity API Status

#### **Added Columns - Combined Fields (2):**
44. Tech Stack (Combined)
45. Functional Areas (Combined)

---

## 🎯 RECOMMENDED NEW COLUMNS

### **From DIIG CSIS Lookup Tables:**
46. **NAICS Description** - Full industry category description
47. **PSC Description** - Product/Service category explanation
48. **Contracting Office Name** - Who manages the contract
49. **Contracting Office Location** - Where contracting office is located

### **From CALC API:**
50. **Labor Rate Min** - Minimum hourly rate for labor category
51. **Labor Rate Max** - Maximum hourly rate
52. **Labor Rate Average** - Market average rate
53. **Education Requirement** - Degree needed (from CALC)
54. **Experience Requirement** - Years of experience (from CALC)
55. **Annual Salary Range** - Calculated from hourly rates

### **From Contract Number Collection:**
56. **Contract Number / PIID** - Contract identifier for API queries
57. **Solicitation Number** - RFP/solicitation identifier
58. **Award ID** - USAspending award identifier

### **From Enhanced Contractor Intelligence:**
59. **GSA Schedule Numbers** - Contractor's GSA vehicles
60. **Contract Award History Count** - Number of awards by contractor
61. **Market Position Rank** - Rank among competitors in category

### **From USAspending (Capture MCP):**
62. **Award Amount (USAspending)** - Cross-validated contract value
63. **Award Date** - When award was made
64. **Funding Agency** - Which agency funds the contract
65. **Awarding Agency** - Which agency awards the contract

### **From Procurement-Tools:**
66. **UEI Validated** - Whether UEI is valid format (Valid/Invalid)
67. **USAspending Profile URL** - Direct link to contractor profile

### **From Advanced Analysis:**
68. **Acquisition Innovation Type** - OTA, Agile, Challenge-based, etc.
69. **Set-Aside Type** - Small business, 8(a), WOSB, etc.
70. **Competition Type** - Full & Open, Limited, Sole Source
71. **Contract Type** - FFP, CPFF, T&M, etc.
72. **Small Business Participation** - % or $ amount

---

## 📋 COMPLETE CAPABILITY MATRIX

### **Tools & APIs Researched:**

1. **Capture MCP Server** (Already installed ✅)
2. **SAM.gov Opportunities API** (Implemented ✅)
3. **SAM.gov Entity Management API** (Implemented ✅)
4. **FPDS ATOM Feed** (Implemented ✅)
5. **USAspending API via Capture MCP** (Available ✅)
6. **DIIG CSIS Lookup Tables** (GitHub - Not yet integrated)
7. **CALC API** (GSA - Not yet integrated)
8. **Python FPDS Library** (GitHub - Not yet integrated)
9. **pysam** (GitHub - Not yet integrated)
10. **procurement-tools** (GitHub - Not yet integrated)
11. **Tango API** (Commercial - Not evaluated)
12. **The Pulse GovCon Part9 API** (Commercial - Not evaluated)

---

## 🔍 DETAILED CAPABILITY MATRIX

### **Legend:**
- ✅ = Can autonomously scrape this data
- 🔧 = Requires contract number/PIID to scrape
- 📝 = Requires manual research/collection
- ⚠️ = Partial coverage or unreliable
- ❌ = Cannot scrape this data
- 🔄 = Already implemented

---

### **MATRIX: Tools × Data Fields**

| Data Field | Capture MCP | SAM.gov Opps | SAM.gov Entity | FPDS ATOM | DIIG CSIS | CALC API | procurement-tools | USAspending | Current Status |
|------------|-------------|--------------|----------------|-----------|-----------|----------|-------------------|-------------|----------------|
| **BASIC IDENTIFICATION** |
| Program Name | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 📝 Original |
| Acronym | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 📝 Original |
| Agency Owner | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | 📝 Original |
| Prime Contractor Name | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | 📝 Original |
| **CONTRACT IDENTIFIERS** |
| Contract Number/PIID | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | 📝 **MISSING** |
| Solicitation Number | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 📝 **MISSING** |
| Award ID | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | 📝 **MISSING** |
| Contractor UEI | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | 🔄 Implemented |
| UEI Validated | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ **NEW** |
| **FINANCIAL DATA** |
| Contract Value | ✅ | ⚠️ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | 📝 Original |
| Base + Options Value | ❌ | ❌ | ❌ | 🔧 | ❌ | ❌ | ❌ | ✅ | 🔄 Implemented |
| Award Amount (USAspending) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ **NEW** |
| **DATES & PERIODS** |
| Signed Date | ❌ | ✅ | ❌ | 🔧 | ❌ | ❌ | ❌ | ✅ | 🔄 Implemented |
| Effective Date | ❌ | ❌ | ❌ | 🔧 | ❌ | ❌ | ❌ | ❌ | 🔄 Implemented |
| Current Completion Date | ❌ | ✅ | ❌ | 🔧 | ❌ | ❌ | ❌ | ✅ | 🔄 Implemented |
| Ultimate Completion Date | ❌ | ❌ | ❌ | 🔧 | ❌ | ❌ | ❌ | ❌ | 🔄 Implemented |
| Award Date | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ **NEW** |
| Recompete Date | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 📝 Original |
| **CLASSIFICATION CODES** |
| NAICS Code | ❌ | ✅ | ✅ | 🔧 | ❌ | ❌ | ❌ | ✅ | 🔄 Implemented |
| NAICS Description | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ **NEW** |
| PSC Code | ❌ | ✅ | ❌ | 🔧 | ❌ | ❌ | ❌ | ✅ | 🔄 Implemented |
| PSC Description | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ **NEW** |
| Set-Aside Type | ❌ | ✅ | ✅ | 🔧 | ❌ | ❌ | ❌ | ✅ | ❌ **NEW** |
| **LOCATION DATA** |
| Performance Location | ❌ | ✅ | ❌ | 🔧 | ❌ | ❌ | ❌ | ✅ | 🔄 Implemented |
| Team Locations (PWS) | ❌ | 🔧 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🔄 Implemented |
| Contracting Office Name | ❌ | ❌ | ❌ | 🔧 | ✅ | ❌ | ❌ | ❌ | ❌ **NEW** |
| Contracting Office Location | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ **NEW** |
| Key Locations | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 📝 Original |
| **TECHNICAL REQUIREMENTS** |
| Tech Stack (Basic) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🔄 Implemented |
| Tech Stack (PWS) | ❌ | 🔧 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🔄 Implemented |
| Functional Areas (Basic) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🔄 Implemented |
| Functional Areas (PWS) | ❌ | 🔧 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🔄 Implemented |
| Clearance Requirements | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 📝 Original |
| Clearances (PWS) | ❌ | 🔧 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🔄 Implemented |
| **LABOR & HIRING INTELLIGENCE** |
| Job Titles (Basic) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🔄 Implemented |
| Labor Categories (PWS) | ❌ | 🔧 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🔄 Implemented |
| Labor Rate Min | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ **NEW** |
| Labor Rate Max | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ **NEW** |
| Labor Rate Average | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ **NEW** |
| Education Requirement | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ **NEW** |
| Experience Requirement | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ **NEW** |
| Annual Salary Range | ❌ | ❌ | ❌ | ❌ | ❌ | 🔧 | ❌ | ❌ | ❌ **NEW** |
| **CONTRACTOR CONTACT INFO** |
| Contractor POC Names | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | 🔄 Implemented |
| Contractor POC Titles | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | 🔄 Implemented |
| Contractor POC Emails | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | 🔄 Implemented |
| Contractor POC Phones | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | 🔄 Implemented |
| **PWS/SOW DOCUMENTS** |
| PWS Document Name | ❌ | 🔧 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🔄 Implemented |
| PWS Download Status | ❌ | 🔧 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🔄 Implemented |
| PWS Full Text | ❌ | 🔧 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🔄 Implemented |
| **CONTRACT DETAILS** |
| Contract Vehicle | ❌ | ✅ | ❌ | 🔧 | ❌ | ❌ | ❌ | ✅ | 📝 Original |
| Contract Type | ❌ | ✅ | ❌ | 🔧 | ❌ | ❌ | ❌ | ✅ | ❌ **NEW** |
| Competition Type | ❌ | ✅ | ❌ | 🔧 | ❌ | ❌ | ❌ | ✅ | ❌ **NEW** |
| Acquisition Innovation Type | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ❌ **NEW** |
| **ADDITIONAL INTELLIGENCE** |
| GSA Schedule Numbers | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ **NEW** |
| Award History Count | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ✅ | ❌ **NEW** |
| Funding Agency | ❌ | ✅ | ❌ | 🔧 | ❌ | ❌ | ❌ | ✅ | ❌ **NEW** |
| Awarding Agency | ❌ | ✅ | ❌ | 🔧 | ❌ | ❌ | ❌ | ✅ | ❌ **NEW** |
| Small Business % | ❌ | ❌ | ❌ | 🔧 | ❌ | ❌ | ❌ | ✅ | ❌ **NEW** |
| **REFERENCE & LINKS** |
| USAspending Profile URL | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ **NEW** |
| SAM.gov Entity URL | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ **NEW** |
| Source Evidence | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 📝 Original |

---

## 📊 COVERAGE SUMMARY BY TOOL

### **Capture MCP Server** (Currently Installed ✅)
**Can Autonomously Scrape:**
- ✅ Award IDs (USAspending)
- ✅ Prime Contractor Name
- ✅ Contract Value
- ✅ Award Amount (USAspending)
- ✅ Award Date
- ✅ Award History Count

**Coverage:** 6-8 fields autonomously

---

### **SAM.gov Opportunities API** (Currently Implemented ✅)
**Can Autonomously Scrape:**
- ✅ Agency Owner
- ✅ Solicitation Number
- ✅ NAICS Code
- ✅ PSC Code
- ✅ Set-Aside Type
- ✅ Contract Vehicle
- ✅ Contract Type
- ✅ Competition Type
- ✅ Performance Location
- ✅ Current Completion Date
- ✅ Signed Date

**Requires Contract Number:**
- 🔧 PWS Documents (resourceLinks)
- 🔧 All PWS-derived fields

**Coverage:** 11+ fields autonomously, 6+ fields with contract number

---

### **SAM.gov Entity Management API** (Currently Implemented ✅)
**Can Autonomously Scrape:**
- ✅ Contractor UEI
- ✅ Contractor POC Names
- ✅ Contractor POC Titles
- ✅ Contractor POC Emails
- ✅ Contractor POC Phones
- ✅ NAICS Codes (registered)
- ✅ GSA Schedule Numbers
- ✅ Set-Aside Certifications
- ✅ SAM.gov Entity URL

**Coverage:** 9+ fields autonomously (by vendor name)

---

### **FPDS ATOM Feed** (Currently Implemented ✅)
**Requires Contract Number (PIID):**
- 🔧 Signed Date
- 🔧 Effective Date
- 🔧 Current Completion Date
- 🔧 Ultimate Completion Date
- 🔧 Base + Options Value
- 🔧 Performance Location
- 🔧 NAICS Code
- 🔧 PSC Code
- 🔧 Contract Type
- 🔧 Competition Type
- 🔧 Set-Aside Type
- 🔧 Contracting Office Code
- 🔧 Funding Agency
- 🔧 Awarding Agency
- 🔧 Small Business %

**Coverage:** 15+ fields (requires contract number)

---

### **DIIG CSIS Lookup Tables** (GitHub - Not Yet Integrated)
**Can Autonomously Enrich:**
- ✅ NAICS Description (lookup from NAICS code)
- ✅ PSC Description (lookup from PSC code)
- ✅ Contracting Office Name (lookup from office code)
- ✅ Contracting Office Location (lookup from office code)

**Requirements:** Must already have NAICS/PSC/Office codes

**Coverage:** 4 fields (reference data enhancement)

---

### **CALC API** (GSA - Not Yet Integrated)
**Can Autonomously Scrape:**
- ✅ Labor Rate Min (by labor category)
- ✅ Labor Rate Max (by labor category)
- ✅ Labor Rate Average (by labor category)
- ✅ Education Requirement (by labor category)
- ✅ Experience Requirement (by labor category)

**Can Calculate:**
- 🔧 Annual Salary Range (from hourly rates)

**Requirements:** Must have labor category/job title

**Coverage:** 6 fields (requires labor categories from PWS)

---

### **procurement-tools** (GitHub - Not Yet Integrated)
**Can Autonomously Validate:**
- ✅ UEI Validated (format validation)
- ✅ USAspending Profile URL (generation)

**Can Scrape (duplicates existing):**
- 🔄 Contractor POC information (already have)
- 🔄 Recent awards (already have via Capture MCP)

**Coverage:** 2 new fields + validation

---

### **Python FPDS Library** (GitHub - Not Yet Integrated)
**Functionality:**
- 🔄 Replaces manual FPDS ATOM parsing
- ✅ Cleaner code
- ❌ No new data fields

**Coverage:** 0 new fields (code quality improvement)

---

### **pysam** (GitHub - Not Yet Integrated)
**Functionality:**
- 🔄 Replaces manual SAM.gov API calls
- ✅ Cleaner code
- ❌ No new data fields

**Coverage:** 0 new fields (code quality improvement)

---

## 🎯 CRITICAL MISSING DATA: CONTRACT NUMBERS

### **The Blocker:**

**Almost all API enrichment requires contract identifiers:**
- PIID (Procurement Instrument Identifier) - e.g., "FA881918C1001"
- Solicitation Number - e.g., "FA8771-18-R-0001"
- Award ID - USAspending identifier

**Current Status:** ❌ **NOT IN DATABASE**

### **Impact:**

Without contract numbers, we **CANNOT** access:
- ❌ PWS/SOW documents (15 fields blocked)
- ❌ FPDS data (15 fields blocked)
- ❌ CALC API labor rates (6 fields blocked)
- ❌ Validated contract periods
- ❌ Official financial data

**Total Blocked:** ~36 high-value fields

### **Solution Options:**

#### **Option 1: Manual Research (Top 20)**
- Research contract numbers on SAM.gov/USAspending
- Time: ~10 min/program × 20 = 3-4 hours
- Result: Full enrichment for priority programs

#### **Option 2: Capture MCP Contractor Search**
- Search USAspending by contractor name
- Extract all PIIDs for that contractor
- Match to programs by contractor + approximate value
- Time: ~30 min per contractor × 50 contractors = 25 hours
- Result: Partial matching (60-70% accuracy)

#### **Option 3: Hybrid Approach** ⭐ **RECOMMENDED**
- Manual research for top 20 priority programs
- Capture MCP search for top 10 contractors
- Accept partial coverage for lower-priority programs
- Time: 4 hours (top 20) + 5 hours (top 10 contractors) = 9 hours
- Result: 80% coverage on priority programs, 40% on others

---

## 📈 RECOMMENDED DATABASE ENHANCEMENTS

### **Tier 1: Critical - Add Immediately** ⭐⭐⭐

**New Columns:**
1. **Contract Number / PIID** - Unlocks all API enrichment
2. **Solicitation Number** - Alternative identifier for SAM.gov
3. **Award ID** - USAspending identifier

**Why:** These three fields unlock 36+ additional enrichment fields

**How to Obtain:**
- Manual research on SAM.gov for top 20 programs
- Capture MCP search by contractor for others
- Progressive collection over time

---

### **Tier 2: High Value - Add This Month** ⭐⭐

**New Columns:**
4. **NAICS Description** - Industry category explanation
5. **PSC Description** - Product/service category explanation
6. **Contracting Office Name** - Who manages contract
7. **Contracting Office Location** - Where office is located
8. **Labor Rate Min** - Minimum hourly rate
9. **Labor Rate Max** - Maximum hourly rate
10. **Labor Rate Average** - Market average rate
11. **Education Requirement** - Degree needed
12. **Experience Requirement** - Years required
13. **Annual Salary Range** - Calculated from rates

**Why:** Major enhancement to recruiting and market intelligence

**How to Obtain:**
- DIIG CSIS Lookup Tables (1 hour integration)
- CALC API (2-3 hours integration)

---

### **Tier 3: Useful - Add As Needed** ⭐

**New Columns:**
14. **UEI Validated** - Valid/Invalid UEI format
15. **Award Date** - When award was made
16. **Funding Agency** - Who funds the contract
17. **Awarding Agency** - Who awards the contract
18. **Set-Aside Type** - Small business designation
19. **Contract Type** - FFP, CPFF, T&M, etc.
20. **Competition Type** - Full & Open, Limited, Sole Source
21. **USAspending Profile URL** - Direct contractor link
22. **SAM.gov Entity URL** - Direct entity link
23. **GSA Schedule Numbers** - Contractor's GSA vehicles
24. **Award History Count** - Number of awards
25. **Small Business Participation %** - SB subcontracting

**Why:** Additional intelligence for analysis

**How to Obtain:**
- Various APIs (requires contract numbers)
- Entity Management API
- procurement-tools

---

## 🚀 INTEGRATION PRIORITY ROADMAP

### **Week 1: Foundation** (2-3 hours)

#### **Day 1: DIIG CSIS Lookup Tables** (1 hour)
```bash
git clone https://github.com/CSISdefense/Lookup-Tables.git
```

**Add Columns:**
- NAICS Description
- PSC Description
- Contracting Office Name
- Contracting Office Location

**Integration:** Lookup from existing NAICS/PSC codes

---

#### **Day 2: Install procurement-tools** (30 min)
```bash
pip install procurement-tools
```

**Add Columns:**
- UEI Validated

**Add Feature:** CLI tools for team

---

#### **Day 3: Refactor with FPDS Library** (1-2 hours)
```bash
pip install fpds
```

**Benefits:**
- Cleaner code
- Better error handling
- No new columns (code quality)

---

### **Week 2: Contract Number Collection** (4-9 hours)

#### **Top 20 Priority Programs** (4 hours)
**Manual research:**
1. Identify top 20 by BD Priority + Contract Value
2. Search SAM.gov for each program
3. Find contract number (PIID or solicitation)
4. Add to "Contract Number" column
5. Document source in notes

**Result:** Top 20 programs ready for full API enrichment

---

#### **Top 10 Contractors** (5 hours - Optional)
**Capture MCP search:**
1. Identify top 10 contractors by program count
2. Use `search_usaspending_awards_by_recipient` for each
3. Extract all PIIDs
4. Match to programs by value/date
5. Add to database

**Result:** 40-60% coverage on remaining programs

---

### **Week 3: CALC API Integration** (2-3 hours)

**Add Columns:**
- Labor Rate Min
- Labor Rate Max
- Labor Rate Average
- Education Requirement
- Experience Requirement
- Annual Salary Range

**Requirements:** Labor categories from PWS (need contract numbers)

---

### **Week 4: Enhanced API Enrichment** (2-3 hours)

**Re-run enrichment on programs with contract numbers:**
- PWS/SOW download and parsing
- FPDS detailed data extraction
- CALC labor rate queries
- Complete all API-dependent fields

**Result:** Full 72-column dataset for priority programs

---

## 📊 FINAL DATABASE PROJECTION

### **Target: 72 Columns** (from current 45)

**Current:** 45 columns
**Tier 1 Additions:** +3 (contract identifiers)
**Tier 2 Additions:** +10 (NAICS/PSC descriptions, labor rates)
**Tier 3 Additions:** +14 (additional intelligence)

**Total:** 72 comprehensive data fields

### **Expected Coverage:**

| Field Category | Current Coverage | With Contract #s | With All Tools |
|----------------|------------------|------------------|----------------|
| Basic Info | 100% | 100% | 100% |
| Contract IDs | 0% | 80% (top programs) | 80% |
| Financial Data | 60% | 90% | 95% |
| Dates/Periods | 30% | 90% | 95% |
| Classification | 0% | 90% | 100% |
| Locations | 30% | 75% | 85% |
| Tech Stack | 95% | 95% | 95% |
| Labor/Hiring | 60% | 85% | 90% |
| Contractor POCs | 0% | 70% | 75% |
| PWS Documents | 0% | 50% | 60% |

---

## ✅ IMMEDIATE ACTION ITEMS

### **This Week:**

1. **Clone DIIG CSIS Lookup Tables**
```bash
cd "c:\N8N Builder"
git clone https://github.com/CSISdefense/Lookup-Tables.git
```

2. **Install procurement-tools**
```bash
pip install procurement-tools
```

3. **Install FPDS library**
```bash
pip install fpds
```

4. **Integrate NAICS/PSC descriptions** (1 hour)

5. **Add UEI validation** (30 min)

---

### **Next Week:**

6. **Identify Top 20 Priority Programs**
   - Filter by BD Priority + Contract Value + Recompete Date
   - Create prioritized list

7. **Manual Contract Number Research** (4 hours)
   - Search SAM.gov for each top 20 program
   - Document PIIDs in new "Contract Number" column

8. **Re-run Enhanced Enrichment**
   - Run on top 20 with contract numbers
   - Get PWS docs, FPDS data, CALC rates
   - Validate results

---

### **This Month:**

9. **CALC API Integration** (2-3 hours)
10. **Contractor-Based Contract Matching** (5 hours)
11. **Complete Documentation Update**
12. **Final Enriched Dataset** (72 columns)

---

## 🎯 BOTTOM LINE

### **Current Status:**
- ✅ **45 columns** implemented
- ✅ **Basic enrichment** working (100%)
- ⚠️ **API enrichment** blocked (missing contract numbers)

### **With All Recommended Enhancements:**
- 🎯 **72 columns** total (+27 new)
- 🎯 **90%+ coverage** on priority programs
- 🎯 **Full hiring intelligence** (labor rates, salaries)
- 🎯 **Complete market intelligence** (NAICS descriptions, contracting offices)

### **Critical Path:**
1. **Add contract numbers** (unlocks 36+ fields) ⭐⭐⭐
2. **Integrate DIIG CSIS** (adds 4 reference fields) ⭐⭐⭐
3. **Integrate CALC API** (adds 6 labor rate fields) ⭐⭐⭐
4. **Install procurement-tools** (adds validation + CLI) ⭐⭐

### **Total Time Investment:**
- **Quick Wins:** 2-3 hours (DIIG CSIS, FPDS lib, proc-tools)
- **Contract Collection:** 4-9 hours (top 20-30 programs)
- **CALC Integration:** 2-3 hours
- **Total:** 8-15 hours for 60% → 90% coverage upgrade

---

**Ready to proceed? Which integration should we start with?**

1. **DIIG CSIS Lookup Tables** (1 hour - immediate value)
2. **Top 20 Contract Number Collection** (4 hours - unlocks everything)
3. **CALC API Integration** (2-3 hours - labor rates)
4. **All of the above in sequence**
