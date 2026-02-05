# Capture MCP Server - Tango API Implementation Analysis

**Repository:** https://github.com/blencorp/capture-mcp-server
**Purpose:** Extract proven Tango API patterns for our federal programs discovery engine

---

## Key Findings

### 1. Tango API Parameter Mapping

The capture-mcp-server uses different parameter names than we discovered. Here's the mapping:

| Our Tests | Capture MCP | Tango API Actual |
|-----------|-------------|------------------|
| `naics_code=X` | `naics=X` | Both work |
| `total_contract_value__gte=X` | Filtered in code | Client-side filtering |
| `piid=X` | N/A | Direct query |
| `recipient.display_name` | `recipient=name` | Search parameter |

**Critical Discovery:** They filter `award_amount_min` and `award_amount_max` CLIENT-SIDE (lines 300-311), not via API parameters!

```typescript
if (award_amount_min !== undefined || award_amount_max !== undefined) {
  rawContracts = rawContracts.filter((contract: any) => {
    const amount = Number(contract.obligated ?? contract.total_contract_value ?? contract.base_and_exercised_options_value ?? 0);
    if (typeof award_amount_min === 'number' && amount < award_amount_min) {
      return false;
    }
    if (typeof award_amount_max === 'number' && amount > award_amount_max) {
      return false;
    }
    return true;
  });
}
```

**Impact:** This means Tango API may NOT support `__gte` and `__lte` suffixes for value filtering. Need to fetch all and filter in Python.

---

### 2. Field Access Patterns

Multiple fallback patterns for accessing nested data:

```typescript
// Award amount (3 fallbacks):
contract.obligated ?? contract.total_contract_value ?? contract.base_and_exercised_options_value

// Vendor name (3 fallbacks):
contract.recipient?.display_name || contract.vendor_name || contract.recipient_name

// Agency (3 fallbacks):
contract.awarding_office?.agency_name || contract.agency_name || contract.office?.agency_name
```

**Lesson:** Always use fallback chains when accessing Tango API fields - data structure varies by contract type.

---

### 3. Search Parameters Discovered

From `searchContracts()` function (lines 255-356):

| Parameter | Maps To | Example |
|-----------|---------|---------|
| `search` | `query` | Text search in description/title |
| `recipient` | `vendor_name` | Contractor name filter |
| `uei` | `vendor_uei` | Contractor UEI |
| `awarding_agency` | `agency` | Agency name/code |
| `naics` | `naics_code` | NAICS industry code |
| `psc` | `psc_code` | Product/Service code |
| `award_date_gte` | `date_from` | Min award date (YYYY-MM-DD) |
| `award_date_lte` | `date_to` | Max award date (YYYY-MM-DD) |
| `set_aside` | `set_aside` | Set-aside type |

**Critical:** They use `award_date_gte` / `award_date_lte` for date filtering, NOT our assumed parameter names.

---

### 4. Pagination Pattern

```typescript
const response = await ApiClient.tangoGet('/contracts/', params, tangoApiKey);

// Access results:
rawContracts = response.data.results || [];

// Totals:
total: response.data.total || response.data.count || 0

// Next page cursor:
next_cursor: response.data.next ?? null
```

**Pattern:** Use `response.data.results` for data, `response.data.next` for cursor-based pagination.

---

### 5. Entity/Vendor Profile Endpoint

Lines 466-555 show how to get vendor profiles:

```typescript
// Get vendor by UEI:
GET /entities/{uei}/

// Get vendor's contracts:
GET /entities/{uei}/contracts/?limit=5&ordering=-award_date

// Get vendor's subawards:
GET /entities/{uei}/subawards/?limit=5&ordering=-fiscal_year
```

**Discovery:** We can get **all contracts for a specific contractor** by UEI! This is useful for identifying staffing firm participation across programs.

---

### 6. Subawards Endpoint Usage

Lines 508-524 show subawards query:

```typescript
const subawardsResponse = await ApiClient.tangoGet(
  `/entities/${uei}/subawards/`,
  { limit: 5, ordering: '-fiscal_year' },
  tangoApiKey
);

// Extract subaward data:
{
  subaward_id: subaward.fsrs_subaward_id || subaward.key,
  description: subaward.description,
  amount: subaward.amount || subaward.total_funding_amount,
  fiscal_year: subaward.fiscal_year,
  prime_recipient: subaward.prime_recipient?.display_name,
  awarding_agency: subaward.awarding_agency?.name
}
```

**Key Field:** `fsrs_subaward_id` - Federal Subaward Reporting System ID

---

### 7. Opportunities Search

Lines 557-643 show opportunities endpoint:

```typescript
GET /opportunities/?search=X&agency=Y&naics=Z&active=true

Parameters:
- posted_date_after / posted_date_before (date ranges)
- first_notice_date_after / first_notice_date_before
- response_deadline_after
- active (boolean for active/inactive)
- notice_type=f (for forecasted opportunities)
```

**Use Case:** Track upcoming contract opportunities by NAICS code to identify potential new programs before awards.

---

### 8. Client-Side Filtering Strategy

They fetch full responses and filter client-side for:
- Award amounts (min/max)
- Vendor name matching (case-insensitive substring)

```typescript
// Vendor name filtering (lines 313-319):
if (vendor_name) {
  const needle = vendor_name.toLowerCase();
  rawContracts = rawContracts.filter((contract: any) => {
    const recipient = contract.recipient?.display_name || contract.recipient_name || contract.vendor_name;
    return typeof recipient === 'string' ? recipient.toLowerCase().includes(needle) : true;
  });
}
```

**Implication:** For value filtering, we should:
1. Query without value filter
2. Get all results (paginate if needed)
3. Filter by value in Python

---

### 9. Data Normalization Pattern

Lines 322-348 show how they normalize responses:

```typescript
const contracts = rawContracts.map((contract: any) => ({
  contract_id: contract.key || contract.piid || contract.contract_id,
  title: contract.description || contract.title,
  vendor: {
    name: contract.recipient?.display_name || contract.vendor_name,
    uei: contract.recipient?.uei || contract.vendor_uei
  },
  agency: {
    name: contract.awarding_office?.agency_name || contract.agency_name,
    code: contract.awarding_office?.agency_code || contract.agency_code
  },
  award_amount: contract.obligated ?? contract.total_contract_value ?? contract.base_and_exercised_options_value,
  // ... more fields
}));
```

**Lesson:** Always provide multiple field paths for the same data point.

---

### 10. Spending Summary Aggregation

Lines 645-792 show how to aggregate spending data:

```typescript
// Group by agency, vendor, NAICS, PSC, or month
GET /contracts/?awarding_agency=X&fiscal_year=Y&limit=100

// Then aggregate client-side by:
group_by: 'agency' | 'vendor' | 'naics' | 'psc' | 'month'
```

**Pattern:** Tango doesn't provide aggregation endpoint - they fetch contracts and aggregate client-side.

---

## Recommendations for Our Discovery Engine V2

### 1. Update Parameter Names

Change from:
```python
params = {
    'total_contract_value__gte': 100000000,  # Doesn't work!
    'naics_code': '541511'
}
```

To:
```python
params = {
    'naics': '541511',  # Correct parameter name
    # No value filter in API - filter client-side after
}
```

### 2. Implement Fallback Field Access

```python
def get_contractor_name(contract: Dict) -> str:
    recipient = contract.get('recipient', {})
    return (
        recipient.get('display_name') or
        contract.get('vendor_name') or
        contract.get('recipient_name') or
        ''
    )

def get_award_amount(contract: Dict) -> float:
    return float(
        contract.get('obligated') or
        contract.get('total_contract_value') or
        contract.get('base_and_exercised_options_value') or
        0
    )
```

### 3. Use Correct Date Parameters

```python
params = {
    'award_date_gte': '2020-01-01',  # NOT date_from!
    'award_date_lte': '2025-12-31'   # NOT date_to!
}
```

### 4. Client-Side Value Filtering

```python
# Step 1: Query without value filter
data = query_tango_api('contracts', {'naics': '541511', 'limit': 100})

# Step 2: Filter by value client-side
qualified = [
    c for c in data['results']
    if get_award_amount(c) >= 10_000_000
]
```

### 5. Add Entity-Based Queries

```python
# Get all contracts for a staffing firm:
def get_vendor_contracts(uei: str) -> List[Dict]:
    return query_tango_api(f'entities/{uei}/contracts/', {
        'limit': 100,
        'ordering': '-award_date'
    })

# Get all subawards for a contractor:
def get_vendor_subawards(uei: str) -> List[Dict]:
    return query_tango_api(f'entities/{uei}/subawards/', {
        'limit': 100,
        'ordering': '-fiscal_year'
    })
```

---

## Updated Discovery Strategy

### Phase 1: Discovery (Corrected)

```python
def discover_contracts_by_naics_group(naics_codes: List[str]) -> List[Dict]:
    """Query Tango with correct parameters"""
    params = {
        'naics': ','.join(naics_codes),  # Correct parameter name
        'limit': 100,
        'sort': '-obligated'  # NOT -total_contract_value
    }

    response = query_tango_api('contracts', params)
    contracts = response.get('results', [])

    # CLIENT-SIDE value filtering (API doesn't support it):
    qualified = [
        c for c in contracts
        if get_award_amount(c) >= 10_000_000
    ]

    return qualified
```

### Phase 2: Subawards Analysis (New)

```python
def get_subcontractor_details(piid: str) -> Dict:
    """Get detailed subcontractor data for a contract"""
    response = query_tango_api('subawards', {
        'prime_award_piid': piid,
        'limit': 100
    })

    subs = response.get('results', [])

    # Identify staffing firms:
    staffing_firms = [
        s for s in subs
        if is_staffing_firm(s.get('subaward_recipient', {}).get('display_name', ''))
    ]

    return {
        'total_subs': len(subs),
        'staffing_firms': len(staffing_firms),
        'staffing_firm_names': [
            s['subaward_recipient']['display_name']
            for s in staffing_firms
        ]
    }
```

### Phase 3: Vendor Profiling (New Capability)

```python
def profile_staffing_firm(uei: str) -> Dict:
    """Get complete profile of a staffing firm"""

    # Get entity details:
    entity = query_tango_api(f'entities/{uei}/', {})

    # Get their contracts:
    contracts = query_tango_api(f'entities/{uei}/contracts/', {
        'limit': 100,
        'ordering': '-award_date'
    })

    # Get their subawards (where they're the sub):
    subawards = query_tango_api(f'entities/{uei}/subawards/', {
        'limit': 100,
        'ordering': '-fiscal_year'
    })

    return {
        'name': entity.get('legal_business_name'),
        'uei': uei,
        'total_prime_contracts': len(contracts.get('results', [])),
        'total_subcontracts': len(subawards.get('results', [])),
        'programs_participated': list(set([
            c['piid'] for c in contracts.get('results', [])
        ])),
        'business_types': entity.get('business_types', [])
    }
```

---

## API Testing Corrections Needed

Based on capture-mcp analysis, our tests had WRONG assumptions:

| What We Tested | What's Correct | Source |
|----------------|----------------|--------|
| `total_contract_value__gte` | No such parameter - filter client-side | Lines 300-311 |
| `date_from` / `date_to` | `award_date_gte` / `award_date_lte` | Lines 288-289 |
| `naics_code` | `naics` (both may work) | Line 286 |
| Shape parameter reduces data | Causes 500 errors, avoid it | Our testing |
| Multiple NAICS in one query | Works with comma separation | Our testing ✓ |

---

## Next Actions

1. **Rebuild Discovery Engine V2** with corrected parameters:
   - Use `naics` not `naics_code`
   - Use `award_date_gte/lte` for dates
   - Remove `total_contract_value__gte` (filter client-side)
   - Implement fallback field access patterns

2. **Add vendor profiling** capability:
   - Query `/entities/{uei}/` for staffing firm profiles
   - Get all contracts per vendor
   - Identify firms active on multiple programs

3. **Test corrected parameters**:
   - Verify `naics` parameter works
   - Verify client-side value filtering
   - Confirm date parameter names

4. **Extract field mappings** from capture-mcp:
   - Document all fallback paths
   - Create helper functions for data extraction

---

## Code Quality Observations

**Strengths:**
- Comprehensive fallback patterns for data access
- Good error handling (checks for success, returns error objects)
- Client-side filtering when API doesn't support it
- Normalized response structures

**Patterns to Adopt:**
- Multiple fallback field paths
- Client-side filtering for unsupported parameters
- Type safety with optional chaining (`?.`)
- Consistent response normalization

---

**Analysis Complete:** 2026-01-20
**Value:** HIGH - Corrects multiple wrong assumptions in our initial approach
**Action Required:** Update Discovery Engine V2 before running
