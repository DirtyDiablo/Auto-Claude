# SAM.gov Contract Data Systems: Complete Master Reference

Federal contract data on SAM.gov represents a consolidated platform integrating Contract Awards (from FPDS), Contract Opportunities, and Entity Management into a single system managed by GSA's Integrated Award Environment. The database contains over **50 million contract records** dating back 30+ years across 60+ federal agencies, with **283 data fields** per contract award and **9 distinct notice types** for opportunities. Access is tiered: public users can search opportunities without an account, while full contract data requires login.gov authentication with data access governed by user role—DoD contract data remains "unrevealed" for 90 days to non-DoD users.

---

## SECTION 1: Database structure and data dictionary

The FPDS Data Dictionary Version 1.5 (October 2025) defines **14 major data element categories** containing all fields stored for federal contract awards.

### Contract identification information

| Element | Field Name | Data Type | Length | Description |
|---------|-----------|-----------|--------|-------------|
| **1A** | PIID | String | Max 50 | Procurement Instrument Identifier - unique contract/order number |
| **1B** | Modification Number | String | Max 25 | Unique identifier for each modification (starts 0 for base) |
| **1C** | Referenced PIID | String | Max 50 | Parent IDV contract number for task/delivery orders |
| **1D** | Transaction Number | Integer | 6 | Tie-breaker for multi-report actions (DoD specific) |
| **1E** | Solicitation Identifier | String | Max 25 | Links to Contract Opportunities notice |
| **1F** | Agency Identifier | String | 4 | FIPS agency code |
| **1G** | Referenced IDV Mod Number | String | Max 25 | Parent IDV modification reference |
| **1H** | Referenced IDV Agency ID | String | 4 | Parent IDV agency code |

### Date fields

| Element | Field Name | Format | Description |
|---------|-----------|--------|-------------|
| **2A** | Date Signed | YYYY-MM-DD | Mutually binding agreement date |
| **2B** | Period of Performance Start Date | YYYY-MM-DD | Contract performance start |
| **2C** | Current Completion Date | YYYY-MM-DD | Base + exercised options completion |
| **2D** | Ultimate Completion Date | YYYY-MM-DD | Including all options if exercised |
| **2E** | Last Date to Order | YYYY-MM-DD | IDV ordering deadline |
| **2F** | Date/Time Stamp Accepted | YYYY-MM-DD HH:MM:SS | System record timestamp |
| **2H** | Solicitation Date | YYYY-MM-DD | RFQ/solicitation issuance |
| **2I** | Prepared By | String (50) | User who created record |
| **2J** | Prepared Date | Date/Time | Record creation timestamp |
| **2L** | Last Modified User | String (50) | Last modification user |

### Dollar values

| Element | Field Name | Format | Description |
|---------|-----------|--------|-------------|
| **3A** | Base and All Options Value | Currency (20) | Total potential contract value including all options |
| **3B** | Base and Exercised Options Value | Currency (20) | Base + exercised options only |
| **3C** | Action Obligation | Currency (20) | Obligated/de-obligated by this transaction |
| **3E** | Total Estimated Order Value | Currency (20) | IDV estimated order value |
| **3AT** | Total Base and All Options | Currency (20) | System-generated running total |
| **3BT** | Total Base and Exercised | Currency (20) | System-generated running total |
| **3CT** | Total Dollars Obligated | Currency (20) | System-generated cumulative obligations |

### Purchaser information

| Element | Field Name | Length | Description |
|---------|-----------|--------|-------------|
| **4A** | Contracting Agency Code | 4 | Executing agency code |
| **4B** | Contracting Office Code | Max 6 | Contracting office ID |
| **4C** | Funding Agency Code | 4 | Agency providing funds |
| **4D** | Funding Office Code | 6 | Funding office/DODAAC |
| **4F** | Foreign Funding | 1 | FMS/non-FMS/Not Applicable (A/B/X) |

### Contract information

| Element | Field Name | Values | Description |
|---------|-----------|--------|-------------|
| **6A** | Type of Contract | J, K, L, M, R, S, T, U, V, Y, Z, 1, 2, 3 | Pricing arrangement (see competition section) |
| **6B** | Undefinitized Action | Y/N | Letter contract indicator |
| **6C** | Multiyear Contract | Y/N | Multiyear appropriation indicator |
| **6D** | Type of IDC | A, B, R, S | Requirements/Indefinite Quantity/Single/Multiple Award |
| **6E** | Multiple or Single Award IDV | M/S | IDV award type |
| **6F** | Performance-Based Service Acquisition | Y, N, X | PBSA indicator |
| **6H** | Emergency Acquisition | A, B, C, D, X | Contingency/humanitarian/peacekeeping |
| **6K** | Contract Financing | A-Z | Financing type code |
| **6L** | Cost Accounting Standards | Y, N, X | CAS clause inclusion |
| **6M** | Description of Requirement | String (250) | Free-text description |

### Product/service information

| Element | Field Name | Format | Description |
|---------|-----------|--------|-------------|
| **8A** | Product or Service Code (PSC) | String (4) | What was purchased |
| **8B** | DoD Acquisition Program | String (8) | Program identifier |
| **8G** | NAICS Code | String (6) | Industry classification |
| **8H** | IT Commercial Category | String (1) | Information technology category |
| **8J** | Government Furnished Property | Y/N | GFP/GFE indicator |
| **8L** | Recovered Materials/Sustainability | A-M | EPA compliance |
| **8N** | Contract Bundling | A-H | Bundling designation |
| **8P** | Consolidated Contract | Y/N | Consolidation indicator |
| **8Q** | Domestic or Foreign Entity | A-D | Entity location classification |

### Entity (contractor) data

| Element | Field Name | Format | Description |
|---------|-----------|--------|-------------|
| **9M** | Unique Entity ID (UEI) | String (12) | Primary entity identifier (replaced DUNS) |
| **9L** | CAGE Code | String (5) | Commercial And Government Entity code |
| **9C** | Place of Performance Code | String (9) | Location code |
| **9D** | Place of Performance Name | String | Location name |
| **9E** | Country of Origin | String (3) | Product/service origin |
| **9F** | Congressional District - Entity | String (4) | Contractor district |
| **9G** | Congressional District - POP | String (4) | Performance district |
| **9H** | Place of Manufacture | A-D | Manufacturing location |
| **9J** | FAR 4.1102 Exception | 1-9 | SAM registration exception |
| **9K** | ZIP Code - Place of Performance | String (9) | Performance ZIP |
| **13GG** | Legal Business Name | String | Official entity name |
| **13HH** | Doing Business As Name | String | DBA name |
| **13JJ-LL** | Entity Address Lines 1-3 | String | Physical address |
| **13MM** | Entity City | String | City |
| **13NN** | Entity State | String (2) | State code |
| **13PP** | Entity ZIP | String (9) | ZIP code |
| **13QQ** | Entity Country Code | String (3) | Country |

### Business type indicators (50+ Boolean fields)

Socio-economic certifications derived from SAM.gov entity registration include: **13M** (Emerging Small Business), **13N** (SBA 8(a) Certified), **13O** (HUBZone), **13P** (SBA-Certified SDB), **13U** (Women-Owned), **13V** (Veteran-Owned), **13W** (SDVOSB), **13Y** (American Indian Owned), **13Z** (Asian-Pacific Owned), **13AA** (Black American Owned), **13BB** (Hispanic American Owned), plus institutional types (educational, nonprofit, government entities).

---

## SECTION 2: Web interface search capabilities

### Keyword search functionality

The SAM.gov keyword search supports three modes under **Simple Search**:

| Mode | Logic | Use Case |
|------|-------|----------|
| **Any Words** | OR between terms | Broadest results |
| **All Words** | AND between terms | All terms required |
| **Exact Phrase** | Phrase matching | Precise term matching |

**Search Editor** enables SQL-like Boolean operations:
- **AND** (or &): Returns records containing ALL terms
- **OR** (or ~): Returns records containing ANY term
- **NOT** (or !): Excludes records containing term
- Operators are NOT case-sensitive

### Contract identification filters

| Filter | Matching Logic | Wildcard Support | Example |
|--------|---------------|------------------|---------|
| **PIID** | Partial match | Yes (*) | `W58*`, `GS*89` |
| **Referenced IDV PIID** | Partial match | Yes (*) | `47QRAA23DTE5T` |
| **Solicitation ID** | Partial match | Yes (*) | `47QCDE25PTEST` |
| **Modification Number** | Exact match | No | `P00001` |

### Document type codes

**Award Types:**
| Code | Type | Description |
|------|------|-------------|
| A | BPA Call | Call against Blanket Purchase Agreement |
| B | Purchase Order | Standard purchase order |
| C | Delivery Order / Task Order | Under an IDV |
| D | Definitive Contract | Standalone contract |

**IDV Types:**
| Code | Type | Description |
|------|------|-------------|
| A | GWAC | Government-Wide Acquisition Contract |
| B | IDC | Indefinite Delivery Contract |
| C | FSS | Federal Supply Schedule (GSA/VA) |
| D | BOA | Basic Ordering Agreement |
| E | BPA | Blanket Purchase Agreement |
| F | Multi-Agency Contract | Derived type |

### Date filters

| Date Field | API Parameter | Format | Range Syntax |
|------------|--------------|--------|--------------|
| Date Signed | `dateSigned` | MM/DD/YYYY | `[01/01/2025,05/29/2025]` |
| IDV Last Date to Order | `idvLastDateToOrder` | MM/DD/YYYY | `[01/01/2025,]` (open-ended) |
| Contract Fiscal Year | `fiscalYear` | YYYY | `2025` |
| Created Date | `createdDate` | MM/DD/YYYY | Single or range |
| Closed Date | `closedDate` | MM/DD/YYYY | Single or range |
| Last Modified Date | `lastModifiedDate` | MM/DD/YYYY | `[01/01/2025,]` |
| Period of Performance Start | `effectiveDate` | MM/DD/YYYY | Range supported |
| Current Completion Date | `currentCompletionDate` | MM/DD/YYYY | Range supported |
| Ultimate Completion Date | `ultimateCompletionDate` | MM/DD/YYYY | Range supported |

### Dollar amount filters

| Parameter | Description | Syntax Examples |
|-----------|-------------|-----------------|
| `dollarsObligated` | Transaction obligation | `1000.99`, `[5000,100000]` |
| `totalDollarsObligated` | Cumulative obligations | `[0.0,100000000.99]` |
| `ultimateContractValue` | Total potential value | `100000.99` |
| `baseAndExercisedOptionsValue` | Base + exercised | `[50000,500000]` |
| `baseAndAllOptionsValue` | Total including options | Range supported |

**Format requirements:** Numeric with decimals (no commas), supports positive/negative values.

### Set-aside type filters (complete list)

| Code | Set-Aside Type | FAR Reference |
|------|----------------|---------------|
| NONE | No Set Aside | — |
| SBA | Small Business Set-Aside (Total) | FAR 19.502-2 |
| SBP | Small Business Set-Aside (Partial) | FAR 19.502-3 |
| 8A | 8(a) Competed | FAR 19.805-2 |
| 8AN | 8(a) Sole Source | FAR 19.8 |
| HZC | HUBZone Set-Aside | FAR 19.1305 |
| HZS | HUBZone Sole Source | FAR 19.1306 |
| SDVOSBC | SDVOSB Set-Aside | FAR 19.1405 |
| SDVOSBS | SDVOSB Sole Source | FAR 19.1406 |
| WOSB | Women Owned Small Business | FAR 19.15 |
| WOSBSS | WOSB Sole Source | FAR 19.15 |
| EDWOSB | Economically Disadvantaged WOSB | FAR 19.15 |
| EDWOSBSS | EDWOSB Sole Source | FAR 19.15 |
| VSA | Veteran Set Aside | VA only |
| VSS | Veteran Sole Source | VA only |
| BI | Buy Indian | DoI and HHS/IHS only |
| HMT | HBCU/MI Set-Aside (Total) | DFARS 226.7003 |
| HMP | HBCU/MI Set-Aside (Partial) | DFARS 235.016 |
| ESB | Emerging Small Business Set-Aside | FAR 19.10 |
| RSB | Reserved for Small Business $2,501-$100K | FAR 13 |
| IEE | Indian Economic Enterprise | DoI/HHS specific |
| ISBEE | Indian Small Business Economic Enterprise | DoI/HHS specific |
| LAS | Local Area Set-Aside | FAR 26.2 |

### Competition status filters

**Extent Competed (10A):**
| Code | Description |
|------|-------------|
| A | Full and Open Competition |
| B | Not Available for Competition |
| C | Not Competed |
| D | Full and Open after exclusion of sources |
| E | Follow On to Competed Action |
| F | Competed under SAP |
| G | Not Competed under SAP |
| H | Competitive Delivery Order (legacy) |

**Solicitation Procedures (10M):**
| Code | Procedure |
|------|-----------|
| NP | Negotiated Proposal (RFP) |
| SP | Sealed Bid (IFB) |
| SSS | Simplified Acquisition |
| MAFO | Subject to Multiple Award Fair Opportunity |
| DDP | DoD Section 803 CSO Procedures |

**Source Selection Process (10Z):**
| Code | Process |
|------|---------|
| LPTA | Lowest Price Technically Acceptable |
| TO | Trade-Off |
| OTHER | Other selection process |

### Contract type/pricing filters (6A)

**Fixed Price Types:**
| Code | Type |
|------|------|
| J | Firm Fixed Price (FFP) |
| K | Fixed Price with Economic Price Adjustment |
| L | Fixed Price Incentive |
| M | Fixed Price Award Fee |
| A | Fixed Price Redetermination |
| B | Fixed Price Level of Effort |

**Cost-Reimbursement Types:**
| Code | Type |
|------|------|
| R | Cost Plus Award Fee |
| S | Cost No Fee |
| T | Cost Sharing |
| U | Cost Plus Fixed Fee |
| V | Cost Plus Incentive Fee |

**Time-Based Types:**
| Code | Type |
|------|------|
| Y | Time and Materials |
| Z | Labor Hours |

**Special Types:**
| Code | Type |
|------|------|
| 1 | Order Dependent (IDV) |
| 2 | Combination |
| 3 | Other |

### Agency/organization filters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `contractingDepartmentCode` | 4-char department | `9700` (DoD) |
| `contractingDepartmentName` | Department name | `GENERAL SERVICES` |
| `contractingSubtierCode` | 4-char subtier | `2100` |
| `contractingSubtierName` | Subtier name | `PUBLIC BUILDINGS SERVICE` |
| `contractingOfficeCode` | 6-char office | `47QCCA` |
| `fundingDepartmentCode` | Funding department | `4700` (GSA) |
| `fundingSubtierCode` | Funding subtier | 4-char code |
| `fundingOfficeCode` | Funding office | 6-char code |

### Entity/contractor filters

| Parameter | Limit | Syntax |
|-----------|-------|--------|
| `awardeeLegalBusinessName` | Partial match | `ENTITY LEGAL NAME` |
| `awardeeUniqueEntityId` | Up to 100 UEIs | `RV56IG5JM6G9~BR5F3G5JM6TR` |
| `awardeeCageCode` | Up to 100 codes | `00000~11111~11321` |
| `ultimateParentUniqueEntityId` | Up to 100 UEIs | `R5PKHW7GWD94` |
| `ultimateParentLegalBusinessName` | Partial match | `ENTITY NAME` |
| `awardeeDoingBusinessAsName` | DBA partial match | `ENTITY NAME` |

**Multiple value syntax:** Use tilde (~) separator for multiple values.

### Place of performance filters

| Parameter | Format | Example |
|-----------|--------|---------|
| `placeOfPerformCountryCode` | 3-char ISO | `USA` |
| `placeOfPerformCountryName` | Partial match | `UNITED STATES` |
| `placeOfPerformStateCode` | 2-char | `VA` |
| `placeOfPerformStateName` | Partial match | `VIRGINIA` |
| `placeOfPerformCityName` | Text | `RESTON` |
| `placeOfPerformZipCode` | 5 or 9 digits | `022012341` |
| `placeOfPerformCongressionalDistrict` | 2-digit | `01` |

### Contract status filter

| Status | API Parameter | Description |
|--------|--------------|-------------|
| Active | `closedStatus=No` | Not closed out CARs |
| Inactive | `closedStatus=Yes` | Closed out CARs |

### Special search parameters

- **PIID Aggregation:** `piidAggregation=yes&piid=47QALD23PTEST` returns award family summary
- **Deleted Contracts:** `deletedStatus=yes` returns contracts deleted within 6 months
- **Free Text:** `q=search terms` for full-text search
- **Include Sections:** `includeSections=contractId,awardeeData` filters response fields

---

## SECTION 3: API specifications

### Authentication and registration

**Obtaining API Keys:**
1. Register at https://sam.gov
2. Navigate to Account Details: https://sam.gov/profile/details
3. Click "Eye" icon for Public API Key, enter OTP from email
4. For System Account keys: Request via Workspace → System Accounts widget

**Rate Limits:**
| User Type | Daily Limit |
|-----------|-------------|
| Non-federal (no role) | 10 requests/day |
| Non-federal (with role) | 1,000 requests/day |
| Federal User | 1,000 requests/day |
| Non-federal System Account | 1,000 requests/day |
| Federal System Account | 10,000 requests/day |

### Contract Awards API

**Endpoint:** `https://api.sam.gov/contract-awards/v1/search`

**Authentication:** 
```
GET: ?api_key={YOUR_API_KEY}&{parameters}
```

**Key Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `api_key` | Required | API key |
| `limit` | Integer | Records per page (max 100) |
| `offset` | Integer | Page index (default 0) |
| `dollarsObligated` | Currency | Dollar amount or range |
| `lastModifiedDate` | Date | Modified date range |
| `dateSigned` | Date | Signing date |
| `piid` | String | Contract PIID |
| `awardOrIDV` | String | `Award` or `IDV` |
| `naicsCode` | String | Up to 100 codes (~ separated) |
| `productOrServiceCode` | String | PSC codes |
| `awardeeUniqueEntityId` | String | UEI (up to 100) |
| `contractingDepartmentCode` | String | 4-char code |
| `placeOfPerformStateCode` | String | 2-char state |
| `fiscalYear` | String | Fiscal year |
| `typeOfSetAsideCode` | String | Set-aside type |
| `format` | String | `csv` or `json` |
| `includeSections` | String | `contractId,awardDetails,awardeeData` |

**Sample Request:**
```
https://api.sam.gov/contract-awards/v1/search?api_key={KEY}&lastModifiedDate=[01/01/2025,]&dollarsObligated=[0.0,100000000.99]&modificationNumber=0&contractingDepartmentCode=9700
```

**Response Schema:**
```json
{
  "totalRecords": 500,
  "limit": 10,
  "offset": 0,
  "awardSummary": [
    {
      "contractId": {
        "subtier": {"code": "9700", "name": "DEPT OF DEFENSE"},
        "piid": "SPE7M520V0512",
        "modificationNumber": "0",
        "referencedIDVPiid": "V797P3148M"
      },
      "coreData": {
        "awardOrIDV": "AWARD",
        "awardOrIDVType": {"code": "B", "name": "PURCHASE ORDER"},
        "federalOrganization": {...},
        "productOrServiceInformation": {...},
        "competitionInformation": {...}
      },
      "awardDetails": {
        "dates": {"dateSigned": "2025-01-15", "fiscalYear": "2025"},
        "dollars": {"actionObligation": "50000.00"},
        "awardeeData": {...}
      }
    }
  ]
}
```

### Get Opportunities API

**Endpoint:** `https://api.sam.gov/opportunities/v2/search`

**Required Parameters:**
| Parameter | Format | Description |
|-----------|--------|-------------|
| `api_key` | String | Public API Key |
| `postedFrom` | MM/dd/yyyy | Posted date from |
| `postedTo` | MM/dd/yyyy | Posted date to |

**Optional Parameters:**
| Parameter | Description |
|-----------|-------------|
| `ptype` | Notice type (u, p, a, r, s, o, g, k, i) |
| `solnum` | Solicitation Number |
| `title` | Title search |
| `state` | Place of Performance State |
| `ncode` | NAICS Code (max 6 digits) |
| `ccode` | Classification Code (PSC) |
| `organizationCode` | Organization code |
| `typeOfSetAside` | Set-Aside code |
| `rdlfrom` / `rdlto` | Response deadline range |
| `limit` | Records per page (max 1000) |
| `offset` | Page index |

**Sample Request:**
```
https://api.sam.gov/opportunities/v2/search?api_key={KEY}&postedFrom=01/01/2025&postedTo=01/31/2025&ptype=o&limit=25&ncode=541511
```

**Response Schema:**
```json
{
  "totalRecords": 34,
  "opportunitiesData": [
    {
      "noticeId": "string",
      "title": "string",
      "solicitationNumber": "string",
      "postedDate": "2025-01-04",
      "type": "Solicitation",
      "setAsideCode": "SBA",
      "responseDeadLine": "2025-02-01T17:00:00",
      "naicsCode": "541511",
      "classificationCode": "D301",
      "active": "Yes",
      "award": {
        "date": "2025-01-15",
        "amount": "125000.00",
        "awardee": {"name": "Company", "ueiSAM": "XXXXXXXXXXXX"}
      },
      "uiLink": "https://sam.gov/opp/XXX/view"
    }
  ]
}
```

### Entity Management API

**Endpoint:** `https://api.sam.gov/entity-information/v4/entities`

**Access Levels:**
- **Public:** Basic entity data
- **FOUO (CUI):** Hierarchy, security, contacts
- **Sensitive (CUI):** Banking, TIN/SSN (POST method required)

**Key Parameters:**
| Parameter | Description |
|-----------|-------------|
| `ueiSAM` | UEI (up to 100) |
| `cageCode` | CAGE code (up to 100) |
| `legalBusinessName` | Legal name search |
| `registrationStatus` | A=Active, E=Expired |
| `naicsCode` | NAICS code |
| `physicalAddressStateCode` | State code |
| `updateDate` | Update date range |
| `includeSections` | `entityRegistration,coreData,assertions` |

### Entity/Exclusions Extracts API

**Endpoint:** `https://api.sam.gov/data-services/v1/extracts`

**Parameters:**
| Parameter | Values |
|-----------|--------|
| `fileType` | `ENTITY`, `EXCLUSION`, `SCR`, `BIO` |
| `sensitivity` | `PUBLIC`, `FOUO`, `SENSITIVE` |
| `frequency` | `DAILY`, `MONTHLY` |
| `charset` | `ASCII`, `UTF8` |
| `date` | `04/07/2022` or `04/2022` |

**Extract Schedule:**
- **Monthly:** 1st Sunday (all active + 6 months expired)
- **Daily FOUO/Sensitive:** Tuesday-Saturday
- **Daily Exclusions:** Every day

### Pagination

| API | Max Limit | Default | Max Records |
|-----|-----------|---------|-------------|
| Opportunities | 1,000 | 1 | No limit stated |
| Contract Awards | 100 | 10 | 400,000 (limit × offset) |
| Entity | 10 | 10 | 10,000 (synchronous) |

### Error responses

| HTTP Code | Description |
|-----------|-------------|
| 200 | Success |
| 400 | Bad request / validation error |
| 401 | Unauthorized |
| 403 | Forbidden (invalid API key) |
| 404 | Not found |
| 500 | Internal server error |

**Restricted Characters:** `& | { } ^ \` not allowed in parameter values.

---

## SECTION 4: Export and download capabilities

### Available export formats

| Source | Formats Available |
|--------|-------------------|
| **SAM.gov Data Bank Reports** | Excel (.xlsx), CSV, HTML, Text, PDF |
| **SAM.gov Entity Extracts** | ZIP containing .dat files (ASCII/UTF-8) |
| **SAM.gov API** | JSON, CSV via `format` parameter |
| **USAspending.gov** | CSV, PostgreSQL Archive, JSON (API) |
| **FPDS Reports** | Excel, CSV, PDF, HTML |

### Export limitations

**SAM.gov Ad Hoc Reports:**
- **Maximum 150,000 rows** per single report
- **Up to 12 years** of data per report
- Custom field selection via "Attributes" and "Metrics" tools
- **36 pre-formatted standard reports** available

**Contract Awards API:**
- Max 100 records per page
- Max 400,000 total records accessible via pagination

**USAspending.gov:**
- Award Data Archive by fiscal year back to **FY2008**
- Custom Award Data back to **FY2001**
- File sizes approximately **~10GB per fiscal year**

### Bulk data downloads

**SAM.gov Entity Extracts:**
| Extract Type | Frequency | Contents |
|-------------|-----------|----------|
| Monthly Public | 1st Sunday | All active + 6 months expired |
| Monthly FOUO/Sensitive | 1st Sunday | Same + opted-out, CUI data |
| Daily FOUO/Sensitive | Tue-Sat | Incremental updates |
| Daily Exclusions | Daily | All active exclusions |

**File Naming:**
```
SAM_PUBLIC_MONTHLY_V2_YYYYMMDD.ZIP
SAM_FOUO_DAILY_V2_YYYYMMDD.ZIP
SAM_SENSITIVE_MONTHLY_V3_YYYYMMDD.ZIP
SAM_Exclusions_Public_Extract_V2_YYDDD.ZIP (Julian date)
```

**USAspending.gov Bulk:**
- Award Data Archive: Pre-packaged by agency, award type, fiscal year
- Full Database: PostgreSQL archive at files.usaspending.gov
- Refresh: Monthly for archives; daily for API

### Scheduled reports

**SAM.gov Ad Hoc Reports:**
- Schedule frequency: Daily, Weekly, Monthly, Quarterly
- Requires "Schedule Role" assignment from Admin
- Results appear in "History List"
- **SEND NOW:** Email report to recipients
- **SHARE:** Send report structure to qualified users

**Saved Searches:**
- Save custom filter combinations
- Set alert frequency: Daily or weekly email notifications
- Access from account dashboard

---

## SECTION 5: Contract Opportunities (active solicitations)

### Notice types (9 total)

**Pre-Award Notices:**
| Code | Type | Purpose | Contractor Action |
|------|------|---------|-------------------|
| **s** | Special Notice | Events, conferences, draft RFIs, draft solicitations | Review; no formal response |
| **r** | Sources Sought | Market research, capability assessments | Submit capabilities statement |
| **p** | Presolicitation | Advise of acquisition scope before formal solicitation | Prepare for solicitation |
| **o** | Solicitation | Formal RFP (FAR 5.704) | **Submit binding proposal** |
| **k** | Combined Synopsis/Solicitation | Combined for commercial items (FAR 5.203) | **Submit binding proposal** |
| **g** | Sale of Surplus Property | Surplus property sales (FAR Part 45) | Review property; submit bids |

**Post-Award and Other:**
| Code | Type | Purpose |
|------|------|---------|
| **a** | Award Notice | Publicize contract awards (FAR 5.303) |
| **u** | Justification and Authorization | Other Than Full & Open Competition disclosure |
| **i** | Consolidate/(Substantially) Bundle | Intent to bundle requirements (FAR 5.205(g)) |

### Opportunity lifecycle

**Status Progression:**
```
DRAFT → PUBLISHED/ACTIVE → ARCHIVED/INACTIVE
              ↓
          CANCELLED → UNCANCELLED
```

**Status Definitions:**
- **Active:** Published, unarchived, uncancelled
- **Inactive:** Published but archived (past deadline)
- **Draft:** Not yet published (office-only view)
- **Cancelled:** Published but cancelled

**Archive Policies:**
- **auto15:** Archives 15 days after response deadline
- **auto30:** Archives 30 days after response deadline
- **autocustom:** Archives on specified date

### Search parameters for opportunities

| Filter | Description |
|--------|-------------|
| Keyword Search | Full-text across titles, descriptions |
| Notice Type | All 9 types selectable |
| Response/Due Date | Filter by deadline; "Next X days/weeks/months" |
| Posted Date | Posted From/To ranges |
| Status | Active, Inactive, Draft, Published, Cancelled |
| Set-Aside Type | All socio-economic categories |
| NAICS Code | 6-digit codes |
| PSC Code | Product service codes |
| Federal Organization | Department → Sub-tier → Office hierarchy |
| Place of Performance | Country, State, City, ZIP, Congressional District |
| Solicitation Number | Partial/wildcard supported |

### Sole source indicators

| Indicator | Description |
|-----------|-------------|
| Set-aside codes ending in "S" | 8AN, HZS, SDVOSBS, WOSBSS, EDWOSBSS, VSS |
| Justification notices (type "u") | Other than full & open competition |
| `stauth` values | Urgency (1), Only One Source (2), Follow-on (3), Minimum Guarantee (4), Statutory (5), Brand name |

### Interested Vendor List (IVL)

- Contracting Officer determines IVL availability
- Vendors must be **logged in** to add themselves
- Optional: Allow vendors to view other interested vendors (teaming)
- Available for Solicitation and Combined Synopsis/Solicitation notices

### Finding recompete opportunities

**Strategy 1: Search expiring contracts**
- Use SAM.gov Contract Awards with date filters:
  - Period of Performance End Date (filter upcoming 6-12 months)
  - Current Completion Date
  - Ultimate Completion Date

**Strategy 2: Review award notices**
- Track incumbent contractor UEI/CAGE
- Note base + options value and duration
- Monitor for Sources Sought/RFI notices

**Strategy 3: Use "Inactive" filter**
- Search archived opportunities
- Review expired solicitations for future recompetes
- Track PIID/Solicitation numbers for follow-on notices

---

## SECTION 6: Practical use cases

### Finding all contracts for a specific prime contractor

**Method A: SAM.gov Contract Data**
1. Navigate to https://sam.gov/contract-data
2. Select "Entity" filter section
3. Enter: **Legal Business Name**, **UEI**, or **CAGE code**
4. Apply date range filters under "Time Period"
5. Select "Include Modifications" for task orders

**Example searches:**
- Company name: "LEIDOS" or "GDIT" or "BOOZ ALLEN HAMILTON"
- UEI: `JDQNCWSNXFK5` (exact 12-character match)
- CAGE: `5A4J7` (exact 5-character match)

**Pro Tip:** Use UEI or CAGE for **precise matching**—company names have variations. First search SAM.gov entity database for exact UEI.

**Method B: USAspending.gov**
1. Navigate to https://www.usaspending.gov/search
2. Select "Contracts" under Award Type
3. Enter company name or UEI in "Recipient" filter
4. Set Time Period (FY2008 to present)
5. Click "Download" for full export

**API approach:**
```
https://api.sam.gov/contract-awards/v1/search?api_key={KEY}&awardeeUniqueEntityId=JDQNCWSNXFK5&lastModifiedDate=[01/01/2020,]
```

### Finding contracts for a specific program/keyword

**SAM.gov Contract Opportunities:**
1. Go to https://sam.gov/opportunities
2. Enter keywords (e.g., "cybersecurity monitoring", "cloud migration")
3. Refine with filters:
   - Notice Type: Solicitation, Pre-solicitation, Combined Synopsis
   - PSC: D301 (IT services), D302 (IT systems development)
   - NAICS: 541512 (computer systems design)
4. Combine keyword + agency filter

**Best practices:**
- Use **shorter queries** (under 5 words)
- Search variations: "IT support" vs "information technology support"
- Review PWS/SOW attachments for different terminology
- Note relevant NAICS/PSC codes from initial results for refined searching

### Finding contracts by agency and location

**Agency Hierarchy:**
1. Department (e.g., Department of Defense)
2. Sub-tier Agency (e.g., Army, Navy, Air Force)
3. Awarding Office (specific contracting office)

**Geographic Filters - Key Distinction:**
| Filter Type | What It Captures |
|------------|------------------|
| **Place of Performance** | Where work is performed (recommended) |
| **Recipient Location** | Contractor's registered address |

**USAspending.gov Steps:**
1. Add "Awarding Agency" filter → Select agency
2. Add "Place of Performance" filter:
   - Country, State, County, City
   - Congressional District (original or current)
   - ZIP Code
3. Submit search

### Tracking recompete opportunities

**Key FPDS date fields:**
- **Period of Performance Start Date:** Contract start
- **Current Completion Date:** Base + exercised options
- **Ultimate Completion Date:** If all options exercised

**Workflow:**
1. Search FPDS by agency + NAICS for active contracts
2. Filter for contracts with PoP ending in 6-18 months
3. Research incumbent via UEI lookup
4. Monitor agency procurement forecasts
5. Watch for Sources Sought/RFI notices on SAM.gov

**API query for expiring contracts:**
```
https://api.sam.gov/contract-awards/v1/search?api_key={KEY}&naicsCode=541512&ultimateCompletionDate=[01/01/2025,12/31/2025]&closedStatus=No
```

### Finding subcontracting opportunities

**Resources:**
- **SUB-Net on SBA.gov:** Lists large primes needing subs
- **FSRS/SAM.gov:** Subaward reporting data (eSRS.gov decommissioned early 2026)
- **USAspending.gov File F:** FSRS subaward data

**Steps to find primes needing subs:**
1. Search USAspending.gov for contracts in your NAICS
2. Filter: Award Amount > $750,000 (subcontracting plan threshold)
3. Check FPDS field: "Subcontracting Plan" = Yes
4. Research prime via SAM.gov entity search
5. Contact prime directly—profile includes contact info

**Small Business Goals:**
- Federal goal: **23%** of contracts to small business
- Primes with contracts over $750K ($1.5M construction) must have subcontracting plans

### Researching past performance

**Finding similar contracts:**
1. USAspending.gov Award Search:
   - Filter by PSC + NAICS + Agency + Award Amount range
   - Download transaction-level data
2. FPDS Standard Reports:
   - "Dollars Obligated by PSC"
   - "Competition Summary"
   - "Top 100 Contractors"

**Identifying incumbents:**
1. Search FPDS by agency + NAICS
2. Note vendor UEI and contract history
3. Review USAspending.gov Recipient Profile:
   - Total awarded amounts over time
   - Breakdown by agency
   - Business types/certifications

---

## Key resources summary

| Resource | URL | Primary Use |
|----------|-----|-------------|
| **SAM.gov Main** | https://sam.gov | Entity registration, opportunities, contract data |
| **SAM.gov Data Services** | https://sam.gov/data-services | Bulk downloads, data dictionary |
| **SAM.gov Contract Data** | https://sam.gov/contract-data | Award search interface |
| **SAM.gov API Portal** | https://api.sam.gov | API access |
| **API Documentation** | https://open.gsa.gov/api/ | Comprehensive API guides |
| **USAspending.gov** | https://www.usaspending.gov | Spending analysis, bulk downloads |
| **FPDS.gov** | https://www.fpds.gov | Authoritative contract data source |
| **FPDS Data Dictionary** | https://www.fpds.gov/downloads/Version_1.5_specs/FPDS_DataDictionary_V1.5.pdf | Complete field definitions |
| **Federal Service Desk** | https://www.fsd.gov | Help and support |
| **Knowledge Base** | https://www.fsd.gov/gsafsd_sp/en?id=kb_view2 | User guides and FAQs |

---

*Document current as of January 2026. SAM.gov is actively modernizing search functionality—GSA's IAE team has indicated ongoing improvements to search modifiers and API capabilities. Always reference official documentation at open.gsa.gov and fsd.gov for the latest specifications.*