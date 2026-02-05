# Auto Claude Handoff - DoD Programs Discovery

**Date**: 2026-01-25 19:40
**Transferring from**: Claude Code session
**Transfer to**: Auto Claude terminal in N8N Builder project

---

## CURRENT STATUS - ALL SCRIPTS PAUSED

✅ All running scripts have been stopped as requested
✅ Ready for continuation in Auto Claude

---

## PROJECT OBJECTIVE

Extract DoD federal staffing programs meeting ALL criteria:
- **DoD contracts** (department_code = 97 in awarding OR funding office)
- **Currently active** (end date in future)
- **$100M+ obligated amount**
- **Has target staffing firms** as subcontractors:
  - Apex Systems
  - Insight Global
  - TEKsystems
  - Belcan
  - SHINE Systems
  - DCI Solutions
  - Patriot Defense Group
  - Akina Inc

---

## CRITICAL BREAKTHROUGH ACHIEVED

### The Funding Office Discovery

**Problem**: All previous attempts (4 total) found 0 DoD contracts

**Root Cause**: Many DoD contracts are:
- **Awarded by**: GSA (General Services Administration)
- **Funded by**: DoD (Department of Defense)

**Previous code** only checked `awarding_office.department_code = 97` → missed all GSA-awarded contracts

**Fix applied**: Now checks BOTH `awarding_office` AND `funding_office` for dept code 97

**Validation**: Testing confirmed this finds DoD contracts successfully

---

## EXECUTION HISTORY

### Attempt 1-3: Failed (0 results)
- Wrong field paths
- NoneType errors
- Only checked awarding_office

### Attempt 4: Fast v4 - Partial Success
**File**: `dod-discovery-v4-FAST.py`
**Status**: Completed
**Results**:
- Scanned: 12,000 contracts (20 pages per NAICS)
- DoD found: 1,620 (13.5%)
- Qualified ($10M+): 60 contracts
- **Final programs**: 0 (all contracts too new, no subawards data)

**Issue**: FY2026 contracts don't have subawards reported yet

### Attempt 5: Target Firm Approach - PAUSED
**File**: `dod-discovery-by-target-firms.py`
**Status**: Stopped at user request (was running successfully)
**Strategy**: Search subawards for target firms first, then filter contracts
**Progress before stop**: Found 1,060+ contracts with APEX SYSTEMS as sub

---

## FILES READY FOR USE

### Working Scripts (Latest Versions)

1. **`dod-discovery-v4-FAST.py`** ✅ TESTED & WORKING
   - Scans DoD contracts by NAICS code (fast version - 20 pages each)
   - Checks both awarding AND funding offices
   - Completed successfully: 1,620 DoD found from 12,000 contracts

2. **`dod-discovery-by-target-firms.py`** ✅ NEW APPROACH
   - Searches subawards for target firms
   - Gets parent contract details
   - Filters for DoD + Active + $100M+ obligated
   - Was running successfully when paused

### Output Files from Fast v4

1. **`dod-programs-PHASE1-v4-fast.csv`** (60 records)
   - Qualified DoD contracts ($10M+ obligated)
   - All have $0 subawards (too new)

2. **`dod-stats-v4-fast.json`**
   - Execution statistics

### Documentation

1. **`CRITICAL-FIX-FUNDING-OFFICE.md`** - Critical breakthrough explanation
2. **`EXECUTION-SUCCESS-SUMMARY.md`** - Detailed progress report
3. **`TARGET-FIRM-APPROACH-STATUS.md`** - New approach status
4. **`V4-BREAKTHROUGH-REPORT.md`** - Failure analysis and fixes
5. **`AUTO-CLAUDE-HANDOFF.md`** - This file

---

## API CONFIGURATION

**API Key**: Already configured in scripts
```python
API_KEY = "n9pSjPG43Q1BzWZlh_d_1-0dVT3XT6c0lQRkjSkcRLk"
```

**Base URL**: `https://tango.makegov.com/api`

**Endpoints Used**:
- `/api/contracts/` - Contract data
- `/api/subawards/` - Subcontractor data

**Rate Limits**:
- 25,000 requests/day
- 100/min burst

---

## RECOMMENDED NEXT STEPS IN AUTO CLAUDE

### Option 1: Complete Target Firm Approach (RECOMMENDED)

The target firm script was working well before being stopped. Continue it:

```bash
cd "c:\N8N Builder"
python dod-discovery-by-target-firms.py
```

**Expected**:
- Runtime: 4-7 hours
- Output: 50-200 DoD programs with target firms
- Approach: Direct search for target firms in subawards

**Advantage**: Guarantees contracts with subawards data and target firms present

### Option 2: Run Full Discovery (All Pages)

Create a full version that scans ALL contracts (not just 20 pages):

1. Copy `dod-discovery-v4-FAST.py` → `dod-discovery-v4-FULL.py`
2. Remove `MAX_PAGES_PER_NAICS` limit
3. Run full scan

**Expected**:
- Runtime: 6-10 hours
- Contracts scanned: ~260,000
- DoD contracts: 25,000-35,000
- Output: More comprehensive but may still have subawards data issue

### Option 3: Hybrid Approach

1. Use target firm approach to get contracts with known subawards
2. Supplement with additional NAICS code scanning
3. Combine results

---

## KEY CODE PATTERNS TO MAINTAIN

### 1. DoD Detection (CRITICAL - Check Both Offices)

```python
def is_dod(self, contract: Dict) -> tuple:
    awarding_office = contract.get('awarding_office') or {}
    funding_office = contract.get('funding_office') or {}

    awarding_dept = awarding_office.get('department_code')
    funding_dept = funding_office.get('department_code')

    if awarding_dept == 97:
        return True, "DoD Awarding"
    if funding_dept == 97:
        return True, "DoD Funding"

    return False, "Not DoD"
```

### 2. Null Handling (Use 'or {}' Pattern)

```python
# CORRECT
period = contract.get('period_of_performance') or {}
performance = contract.get('place_of_performance') or {}
awarding_office = contract.get('awarding_office') or {}
funding_office = contract.get('funding_office') or {}

# WRONG - can fail if value is None
period = contract.get('period_of_performance', {})
```

### 3. Active Contract Check

```python
def is_active(self, contract: Dict) -> bool:
    today = date.today()
    period = contract.get('period_of_performance') or {}

    current_end = period.get('current_end_date')
    if current_end:
        end_date = datetime.fromisoformat(current_end.replace('Z', '+00:00')).date()
        if end_date > today:
            return True

    ultimate = period.get('ultimate_completion_date')
    if ultimate:
        ultimate_date = datetime.fromisoformat(ultimate.replace('Z', '+00:00')).date()
        if ultimate_date > today:
            return True

    return False
```

---

## KNOWN ISSUES & WORKAROUNDS

### Issue 1: Recent Contracts Lack Subawards
**Problem**: FY2026 contracts don't have subawards reported in FSRS yet
**Workaround**: Use target firm approach (searches subawards first)

### Issue 2: API Rate Limiting
**Symptom**: 429 errors
**Solution**: Scripts include 60s wait on 429, works automatically

### Issue 3: Network Instability
**Symptom**: Connection resets, 502/503/504 errors
**Solution**: Scripts retry automatically with 15-30s delays

---

## TECHNICAL CONTEXT

### API Structure (CRITICAL)

Contracts have TWO offices:
```json
{
  "awarding_office": {
    "department_code": 47,
    "department_name": "General Services Administration"
  },
  "funding_office": {
    "department_code": 97,
    "department_name": "Department of Defense"
  }
}
```

**DoD contracts often awarded by GSA, funded by DoD!**

### Target Firms Search Patterns

```python
self.target_firms = {
    'APEX_SYSTEMS': ['APEX SYSTEMS', 'APEX GROUP'],
    'INSIGHT_GLOBAL': ['INSIGHT GLOBAL'],
    'TEKSYSTEMS': ['TEKSYSTEMS', 'TEK SYSTEMS'],
    'BELCAN': ['BELCAN'],
    'SHINE_SYSTEMS': ['SHINE SYSTEMS'],
    'DCI_SOLUTIONS': ['DCI SOLUTIONS'],
    'PATRIOT_DEFENSE': ['PATRIOT DEFENSE GROUP'],
    'AKINA': ['AKINA INC', 'AKINA,']
}
```

### NAICS Codes for Staffing

```python
naics_codes = [
    '541511',  # Computer Programming
    '541512',  # Computer Systems Design
    '541513',  # Computer Facilities Management
    '541519',  # Other Computer Services
    '541611',  # Admin Management Consulting
    '541612',  # HR Consulting
    '541613',  # Marketing Consulting
    '541618',  # Other Management Consulting
    '541690',  # Other Scientific/Technical
    '541330',  # Engineering Services
    '541370',  # Surveying/Mapping
    '541715'   # R&D Physical Sciences
]
```

---

## EXPECTED FINAL OUTPUT

### File: `dod-programs-by-target-firms.csv`

**Columns**:
- `piid` - Contract ID
- `description` - Program description
- `obligated` - Contract value
- `fiscal_year` - FY
- `awarding_agency` - Agency that awarded
- `awarding_department` - Awarding department
- `funding_agency` - Agency that funds
- `funding_department` - Department of Defense
- `dod_match_reason` - How identified as DoD
- `prime_contractor` - Main contractor
- `period_start` - Start date
- `period_end` - Current end date
- `ultimate_completion` - Final completion
- `performance_city` - Location
- `performance_state` - State
- `target_firms` - Which target firms present (e.g., "APEX_SYSTEMS; TEKSYSTEMS")
- `naics_code` - Industry code

**Expected Records**: 50-200 programs

---

## COMMANDS FOR AUTO CLAUDE

### Check Current Status

```bash
cd "c:\N8N Builder"

# Check if any scripts still running
Get-Process python -ErrorAction SilentlyContinue

# View latest logs
Get-Content dod-discovery-by-firms.log -Tail 50

# Check output files
ls *.csv | Select-Object Name,Length,LastWriteTime
```

### Resume Target Firm Approach

```bash
cd "c:\N8N Builder"
python dod-discovery-by-target-firms.py
```

### Check Progress (While Running)

```bash
# View real-time log
Get-Content dod-discovery-by-firms.log -Tail 20 -Wait

# Check stats file (if created)
Get-Content dod-stats-by-firms.json | ConvertFrom-Json
```

---

## VALIDATION CHECKLIST

Before delivering results, verify:
- [ ] All programs are DoD (dept code 97 in awarding OR funding)
- [ ] All programs are active (end date > today)
- [ ] All programs have $100M+ obligated
- [ ] All programs have at least one target firm
- [ ] CSV file loads correctly in Excel/pandas
- [ ] No duplicate PIIDs

---

## TROUBLESHOOTING

### If Script Fails

1. Check log file: `dod-discovery-by-firms.log`
2. Look for error patterns:
   - NoneType errors → null handling issue
   - 429 errors → rate limiting (should auto-retry)
   - 502/503/504 → server issues (should auto-retry)
3. Check API key is valid
4. Verify network connectivity

### If No Results

1. Check DoD detection is working:
   ```python
   # Run test script
   python test-dod-detection-FIXED.py
   ```
2. Verify target firms search finds contracts
3. Check thresholds aren't too strict

---

## CONTEXT FOR AUTO CLAUDE

When starting in Auto Claude terminal, you can reference:

**"I'm continuing the DoD programs discovery project from Claude Code. Please read AUTO-CLAUDE-HANDOFF.md for full context. The target firm discovery script was paused and ready to resume. Recommended action: run dod-discovery-by-target-firms.py to get 50-200 qualified DoD programs."**

---

## PROJECT FOLDER STRUCTURE

```
c:\N8N Builder\
├── dod-discovery-by-target-firms.py          ← Resume this
├── dod-discovery-v4-FAST.py                  ← Completed (1,620 DoD found)
├── dod-programs-PHASE1-v4-fast.csv           ← Output from fast run
├── dod-stats-v4-fast.json                    ← Stats from fast run
├── AUTO-CLAUDE-HANDOFF.md                    ← This file
├── CRITICAL-FIX-FUNDING-OFFICE.md            ← Key breakthrough
├── EXECUTION-SUCCESS-SUMMARY.md              ← Progress report
├── TARGET-FIRM-APPROACH-STATUS.md            ← Approach status
└── logs/
    ├── dod-discovery-by-firms.log            ← Target firm log
    └── dod-discovery-v4-fast.log             ← Fast run log
```

---

## API USAGE TRACKING

**Today's Usage** (approximate):
- Fast v4 run: ~300 requests
- Target firm start: ~50-100 requests
- **Remaining**: ~24,500 of 25,000 daily limit

**Plenty of quota remaining for full execution**

---

## SUCCESS CRITERIA

Delivery is successful when:
- [ ] 50-200 DoD programs identified
- [ ] All meet criteria (DoD + Active + $100M+ + Target firm)
- [ ] CSV file with all required fields
- [ ] Stats JSON with execution metrics
- [ ] No errors in final run
- [ ] Results validated

---

**Handoff Complete**
**Ready for Auto Claude continuation**
**All scripts paused**
**No background tasks running**

---

**Generated**: 2026-01-25 19:45
**Session**: Claude Code → Auto Claude transfer
**Status**: Ready for pickup
