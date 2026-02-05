# Complete Tango API Schema Reference

**Purpose**: Comprehensive documentation of all available fields across Tango API endpoints
**Date**: 2026-01-20
**API Base URL**: https://tango.makegov.com/api
**Rate Limit**: 25,000 requests/day (Large Plan)

---

## Table of Contents

1. [Contract Fields (/api/contracts/)](#contract-fields-apicontracts)
2. [Subaward Fields (/api/subawards/)](#subaward-fields-apisubawards)
3. [Entity Fields (/api/entities/{uei}/)](#entity-fields-apientitiesuei)
4. [Query Parameters Guide](#query-parameters-guide)
5. [Response Pagination](#response-pagination)
6. [Common Patterns](#common-patterns)

---

## Contract Fields (/api/contracts/)

### Identifiers

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `piid` | string | Procurement Instrument Identifier (unique contract ID) | "FA807519FA029" |
| `key` | string | Alternative unique key | "CONT_AWD_..." |
| `contract_id` | string | Contract ID variant | "FA807519FA029" |

### Financial Fields

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `total_contract_value` | float | Full contract value including all options | 482000000.00 |
| `obligated` | float | **BEST FOR ACTUAL SPEND** - Amount currently obligated | 456789123.00 |
| `base_and_exercised_options_value` | float | Base + exercised options value | 482000000.00 |

**Best Practice**: Use `obligated` as primary financial value with fallback to `total_contract_value`.

### Dates & Period of Performance

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `award_date` | date (YYYY-MM-DD) | Contract award date | "2019-09-27" |
| `fiscal_year` | integer | Fiscal year of award | 2019 |
| `period_of_performance.start_date` | date | Contract start date | "2019-09-27" |
| `period_of_performance.current_end_date` | date | Current end date (before options) | "2024-09-26" |
| `period_of_performance.ultimate_completion_date` | date | Final completion (after all options) | "2029-09-26" |

**Active Contract Logic**:
```python
def is_active(contract):
    today = datetime.now().date()
    period = contract.get('period_of_performance', {})
    current_end = period.get('current_end_date')
    ultimate_end = period.get('ultimate_completion_date')

    try:
        if current_end and datetime.fromisoformat(current_end).date() > today:
            return True
        if ultimate_end and datetime.fromisoformat(ultimate_end).date() > today:
            return True
    except:
        pass
    return False
```

### Description & Classification

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `description` | text | **PRIMARY** - Contract description/title | "Joint training synthetic environment..." |
| `title` | text | Alternative title field | "Mission Partner Environment" |
| `naics_code` | string | Industry classification (6 digits) | "541512" |
| `naics` | string | Alternative NAICS field | "541512" |
| `psc_code` | string | Product/Service Code | "D302" |
| `psc` | string | Alternative PSC field | "D302" |

**NAICS Codes for Staffing Services**:
- 541511 - Custom Computer Programming Services
- 541512 - Computer Systems Design Services
- 541513 - Computer Facilities Management Services
- 541519 - Other Computer Related Services
- 541611 - Administrative Management Consulting
- 541612 - Human Resources Consulting
- 541613 - Marketing Consulting
- 541618 - Other Management Consulting Services
- 541690 - Other Scientific and Technical Consulting
- 541330 - Engineering Services
- 541370 - Surveying and Mapping Services
- 541715 - Research and Development (Physical/Life Sciences)

### Location Fields

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `place_of_performance.city_name` | string | Performance city | "Scott AFB" |
| `place_of_performance.state_name` | string | Performance state | "IL" |
| `place_of_performance.state_code` | string | State abbreviation | "IL" |
| `place_of_performance.zip_code` | string | ZIP code | "62225" |
| `place_of_performance.country_name` | string | Country | "United States" |
| `place_of_performance.congressional_district` | string | Congressional district | "IL-13" |

**Location String Construction**:
```python
perf_loc = contract.get('place_of_performance', {})
location = f"{perf_loc.get('city_name', '')}, {perf_loc.get('state_name', '')}".strip(', ')
```

### Contractor/Recipient Fields

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `recipient.uei` | string | Contractor UEI (unique entity ID) | "L8JX7DYGHBY8" |
| `recipient.display_name` | string | **PRIMARY** - Contractor business name | "Accenture Federal Services" |
| `recipient.legal_business_name` | string | Legal business name | "Accenture Federal Services LLC" |
| `vendor_name` | string | Alternative vendor name | "Accenture Federal Services" |
| `vendor_uei` | string | Alternative vendor UEI | "L8JX7DYGHBY8" |

### Agency Fields

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `awarding_office.agency_name` | string | **PRIMARY** - Awarding agency | "Department of the Air Force" |
| `awarding_office.agency_code` | string | Agency code | "5700" |
| `awarding_office.office_name` | string | Specific office name | "Air Force - Other" |
| `funding_office.agency_name` | string | Funding agency (if different) | "Department of the Air Force" |
| `funding_office.office_name` | string | Funding office name | "Air Force - Other" |

**DoD Agency Keywords**:
```python
dod_keywords = [
    'Department of Defense',
    'Department of the Air Force',
    'Department of the Army',
    'Department of the Navy',
    'Defense Intelligence Agency',
    'National Security Agency',
    'U.S. Marine Corps',
    'Defense Logistics Agency',
    'DARPA',
    'Defense Advanced Research'
]

def is_dod(agency_name):
    if not agency_name:
        return False
    return any(kw in agency_name for kw in dod_keywords)
```

### Subcontractor Summary Fields

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `subawards_summary.count` | integer | **ACTUAL** number of subcontractors | 144 |
| `subawards_summary.total_amount` | float | **ACTUAL** total subaward spending | 82967626.84 |

**CRITICAL**: These are ACTUAL counts from subawards data, not estimates!

**Usage Pattern**:
```python
subawards = contract.get('subawards_summary', {})
actual_contractor_count = subawards.get('count', 0) if subawards else 0
actual_subaward_spend = float(subawards.get('total_amount', 0) or 0) if subawards else 0
```

### Contract Vehicle Fields

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `parent_award.piid` | string | Parent contract PIID (for task orders) | "FA8771-18-D-0001" |
| `award_type.description` | string | Contract vehicle type | "Delivery Order" |
| `contract_type` | string | Contract type | "Firm Fixed Price" |
| `set_aside` | string | Set-aside type | "None", "SBA", "WOSB", "SDVOSB", "8A" |

**Task Order Detection**:
```python
def detect_task_order(contract):
    parent = contract.get('parent_award', {})
    if parent and parent.get('piid'):
        return f"Task Order under {parent.get('piid')}"
    return "Prime Contract"
```

---

## Subaward Fields (/api/subawards/)

### Identifiers

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `fsrs_subaward_id` | string | Federal Subaward Reporting System ID | "abc123def456" |
| `key` | string | Alternative unique key | "SUBAWARD_..." |
| `prime_award_piid` | string | **QUERY PARAMETER** - Parent contract PIID | "FA807519FA029" |

**Query Pattern**:
```python
GET /api/subawards/?prime_award_piid={PIID}&limit=100
```

### Subcontractor Fields

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `subaward_recipient.uei` | string | Subcontractor UEI | "J8XZABCDEF12" |
| `subaward_recipient.display_name` | string | **PRIMARY** - Subcontractor company name | "APEX SYSTEMS LLC" |
| `subaward_recipient.legal_business_name` | string | Legal business name | "Apex Systems LLC" |

**Target Firm Detection**:
```python
target_firms = {
    'APEX': ['APEX', 'APEX SYSTEMS', 'APEX GROUP'],
    'INSIGHT_GLOBAL': ['INSIGHT GLOBAL', 'INSIGHT GLB'],
    'TEKSYSTEMS': ['TEKSYSTEMS', 'TEK SYSTEMS', 'TEKSGLOBAL'],
    'BELCAN': ['BELCAN'],
    'SHINE': ['SHINE', 'SHINE SYSTEMS'],
    'DCI': ['DCI', 'DCI SOLUTIONS'],
    'PATRIOT': ['PATRIOT', 'PATRIOT DEFENSE'],
    'AKINA': ['AKINA']
}

def detect_target_firms(subcontractors_list):
    found_firms = []
    for sub in subcontractors_list:
        sub_upper = sub.get('subaward_recipient', {}).get('display_name', '').upper()

        for firm_key, patterns in target_firms.items():
            if any(pattern in sub_upper for pattern in patterns):
                found_firms.append({
                    'firm': firm_key,
                    'official_name': sub.get('subaward_recipient', {}).get('display_name'),
                    'amount': sub.get('subaward_details', {}).get('amount', 0)
                })
                break

    return found_firms
```

### Financial Fields

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `subaward_details.amount` | float | Subaward dollar amount | 2500000.00 |
| `subaward_details.type` | string | Type (Subaward, Subcontract, etc.) | "Subcontract" |
| `total_funding_amount` | float | Total funding | 2500000.00 |

### Relationship Fields

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `prime_recipient.display_name` | string | Prime contractor name | "Accenture Federal Services" |
| `prime_recipient.uei` | string | Prime contractor UEI | "L8JX7DYGHBY8" |
| `awarding_agency.name` | string | Agency name | "Department of Defense" |
| `awarding_agency.code` | string | Agency code | "9700" |

### Dates

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `fiscal_year` | integer | Fiscal year | 2019 |
| `award_date` | date | Subaward date | "2019-10-15" |

---

## Entity Fields (/api/entities/{uei}/)

### Basic Information

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `uei` | string | Unique Entity Identifier | "L8JX7DYGHBY8" |
| `legal_business_name` | string | Legal business name | "Accenture Federal Services LLC" |
| `dba_name` | string | Doing Business As name | "AFS" |
| `entity_type` | string | Entity type | "Business or Organization" |

### Location

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `physical_address.address_line_1` | string | Street address | "7 Federal Dr" |
| `physical_address.city` | string | City | "Andover" |
| `physical_address.state_code` | string | State | "MA" |
| `physical_address.zip_code` | string | ZIP code | "01810" |

### Business Details

| Field Path | Type | Description | Example |
|------------|------|-------------|---------|
| `naics_codes` | array | All NAICS codes for entity | ["541512", "541519"] |
| `socioeconomic_indicators.small_business` | boolean | Small business status | true/false |
| `socioeconomic_indicators.woman_owned` | boolean | Woman-owned status | true/false |

**Note**: Entity API is useful for Phase 2 enhancements (contact info, certifications).

---

## Query Parameters Guide

### Common Query Parameters

| Parameter | Type | Endpoint | Description | Example |
|-----------|------|----------|-------------|---------|
| `naics` | string | /api/contracts/ | **CORRECT** - Filter by NAICS code | `naics=541512` |
| `psc` | string | /api/contracts/ | Filter by PSC code | `psc=D302` |
| `award_date_gte` | date | /api/contracts/ | Awards on/after date | `award_date_gte=2020-01-01` |
| `award_date_lte` | date | /api/contracts/ | Awards on/before date | `award_date_lte=2023-12-31` |
| `limit` | integer | All | Results per page (max 50 typical) | `limit=50` |
| `cursor` | string | All | Pagination cursor from previous response | `cursor=abc123...` |

### CRITICAL CORRECTIONS

**INCORRECT Parameter Names** (DO NOT USE):
- ❌ `naics_code` - Use `naics` instead
- ❌ `psc_code` - Use `psc` instead
- ❌ `total_contract_value__gte` - Server-side value filtering NOT supported
- ❌ `date_from` / `date_to` - Use `award_date_gte` / `award_date_lte`

**Verified Working Pattern**:
```python
params = {
    'naics': '541512',  # CORRECT
    'award_date_gte': '2020-01-01',  # CORRECT
    'limit': 50
}

response = requests.get(
    'https://tango.makegov.com/api/contracts/',
    headers={'X-API-Key': api_key},
    params=params
)
```

### Client-Side Filtering (Required)

**Server Does NOT Support**:
- Value filtering (`total_contract_value__gte`)
- Complex agency filtering
- Subcontractor count filtering

**Solution - Filter After Retrieval**:
```python
# Get contracts
contracts = api_response['results']

# Client-side filter by value
filtered = [
    c for c in contracts
    if (c.get('obligated') or c.get('total_contract_value') or 0) >= 10_000_000
]

# Client-side filter by agency
dod_contracts = [
    c for c in filtered
    if is_dod(c.get('awarding_office', {}).get('agency_name', ''))
]
```

---

## Response Pagination

### Standard Pagination Pattern

All Tango API endpoints return paginated results:

```json
{
  "count": 1247,
  "next": "cursor_token_here",
  "previous": null,
  "results": [
    { /* contract object */ },
    { /* contract object */ },
    ...
  ]
}
```

### Pagination Code Pattern

```python
def fetch_all_pages(endpoint, params, max_pages=None):
    """Fetch all pages from Tango API endpoint"""
    all_results = []
    cursor = None
    page = 0

    while True:
        page += 1
        if max_pages and page > max_pages:
            break

        if cursor:
            params['cursor'] = cursor

        response = requests.get(endpoint, headers=headers, params=params)
        data = response.json()

        if not data or 'results' not in data:
            break

        results = data['results']
        if not results:
            break

        all_results.extend(results)

        cursor = data.get('next')
        if not cursor:
            break

    return all_results
```

---

## Common Patterns

### Financial Value with Fallback

```python
def get_award_amount(contract):
    """Get award amount with fallbacks"""
    return float(
        contract.get('obligated') or
        contract.get('total_contract_value') or
        contract.get('base_and_exercised_options_value') or
        0
    )
```

### Safe Date Parsing

```python
from datetime import datetime

def safe_parse_date(date_str):
    """Safely parse ISO date string"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str).date()
    except:
        return None
```

### Nested Field Access

```python
def safe_get_nested(obj, *keys, default=''):
    """Safely access nested dictionary keys"""
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key, {})
        else:
            return default
    return obj if obj else default

# Usage
agency = safe_get_nested(contract, 'awarding_office', 'agency_name', default='Unknown')
```

### Rate Limiting

```python
import time

def query_with_rate_limit(url, params, api_key, request_counter):
    """Query API with rate limit management"""
    headers = {'X-API-Key': api_key}

    response = requests.get(url, headers=headers, params=params, timeout=60)
    request_counter['count'] += 1

    # Pause every 50 requests
    if request_counter['count'] % 50 == 0:
        print(f"  [PAUSE] Rate limit management... {request_counter['count']} requests so far")
        time.sleep(1)

    return response.json()
```

### Error Handling with Retries

```python
def query_with_retry(url, params, api_key, retries=3):
    """Query API with exponential backoff retry"""
    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                headers={'X-API-Key': api_key},
                params=params,
                timeout=60
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"  [WARNING] Rate limit hit, pausing 60s...")
                time.sleep(60)
                continue
            elif response.status_code in (502, 503, 504):
                print(f"  [WARNING] Server error {response.status_code}, retry {attempt+1}/{retries}...")
                time.sleep(5 * (attempt + 1))
                continue
            else:
                print(f"  [ERROR] API error {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print(f"  [WARNING] Timeout, retry {attempt+1}/{retries}...")
            time.sleep(5 * (attempt + 1))
            continue
        except Exception as e:
            print(f"  [ERROR] Request exception: {str(e)}")
            return None

    return None
```

---

## Field Inference Techniques

### Acronym Extraction

```python
import re

def extract_acronym(description):
    """Extract acronym from description"""
    # Look for patterns like "Mission Partner Environment (MPE)"
    match = re.search(r'\(([A-Z]{2,})\)', description)
    if match:
        return match.group(1)

    # Look for all-caps words
    words = description.split()
    acronyms = [w for w in words if w.isupper() and len(w) >= 2]
    if acronyms:
        return acronyms[0]

    return ''
```

### Functional Areas from Description

```python
functional_keywords = {
    'Software Development': ['software', 'development', 'coding', 'programming', 'app', 'application'],
    'IT Operations': ['it support', 'help desk', 'operations', 'maintenance', 'service desk'],
    'Systems Engineering': ['systems engineering', 'systems design', 'architecture', 'integration'],
    'Cybersecurity': ['cybersecurity', 'security', 'zero trust', 'siem', 'threat', 'cyber'],
    'Network Administration': ['network', 'networking', 'network admin', 'cisco', 'juniper'],
    'Cloud Services': ['cloud', 'aws', 'azure', 'gcp', 'saas', 'paas'],
    'Data Analytics': ['data analytics', 'big data', 'analytics', 'business intelligence', 'bi'],
    'DevOps': ['devops', 'ci/cd', 'jenkins', 'gitlab', 'kubernetes', 'docker'],
    'AI/ML': ['ai', 'machine learning', 'artificial intelligence', 'ml', 'deep learning']
}

def extract_functional_areas(description):
    """Extract functional areas from contract description"""
    areas = []
    desc_lower = description.lower()
    for area, keywords in functional_keywords.items():
        if any(kw in desc_lower for kw in keywords):
            areas.append(area)
    return '; '.join(areas)
```

### Job Titles from NAICS

```python
naics_to_jobs = {
    '541511': ['Software Developer', 'Systems Analyst', 'QA Engineer', 'DevOps Engineer'],
    '541512': ['Systems Administrator', 'IT Operations Specialist', 'Network Engineer'],
    '541519': ['IT Consultant', 'Solutions Architect', 'Technical Lead'],
    '541330': ['Systems Engineer', 'Hardware Engineer', 'Integration Engineer'],
    '541611': ['Management Consultant', 'Business Analyst', 'Program Manager'],
    '541715': ['Research Scientist', 'Data Scientist', 'AI/ML Engineer']
}

def infer_job_titles(naics_code):
    """Infer typical job titles from NAICS code"""
    return '; '.join(naics_to_jobs.get(naics_code, ['IT Professional']))
```

---

## API Limitations & Workarounds

### Known Limitations

1. **No Server-Side Value Filtering**
   - Limitation: Cannot filter by `total_contract_value__gte`
   - Workaround: Retrieve all results, filter client-side

2. **No Complex Agency Filters**
   - Limitation: DoD filter unreliable via API parameter
   - Workaround: Keyword matching on `awarding_office.agency_name`

3. **Shape Parameters Cause Errors**
   - Limitation: Complex `shape` parameters return 500 errors
   - Workaround: Accept full response, extract needed fields

4. **Subaward Details Require Separate Query**
   - Limitation: Full subcontractor list not in contract response
   - Workaround: Query `/api/subawards/?prime_award_piid={PIID}` for details

5. **No Job Title or Clearance Fields**
   - Limitation: Not structured in API responses
   - Workaround: Infer from NAICS, keyword extraction, or manual research

### Best Practices

1. **Always use `obligated` field first** for financial values
2. **Client-side filtering** for values and complex agency logic
3. **Pattern matching** for target firm detection (handle name variations)
4. **Rate limiting** - pause every 50 requests
5. **Error handling** - retry on 429, 502, 503, 504
6. **Pagination** - use cursor-based pagination for large result sets

---

## API Usage Estimates

For DoD Staffing Programs Discovery:

| Phase | Endpoint | Estimated Requests | Notes |
|-------|----------|-------------------|-------|
| Phase 1: Discovery | /api/contracts/ | 200-400 | 12 NAICS × 5 pages × 50/page |
| Phase 2: Subawards | /api/subawards/ | 500-1,500 | 50-150 contracts × 1-10 queries each |
| **TOTAL** | | **700-1,900** | **~8% of 25,000/day limit** |

---

## Version History

- **2026-01-20**: Initial complete schema documentation
- Created for DoD Staffing Programs Discovery project
- Based on verified API testing results from TANGO-API-TESTING-RESULTS.md
- Incorporates corrections from capture-mcp-server production code analysis

---

**END OF SCHEMA DOCUMENTATION**
