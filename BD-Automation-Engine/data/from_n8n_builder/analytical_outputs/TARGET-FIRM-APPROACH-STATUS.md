# DoD Programs Discovery - Target Firm Approach

**Date**: 2026-01-25 19:30
**Status**: ✅ RUNNING - New approach working

---

## NEW STRATEGY

Instead of searching all DoD contracts then checking for target firms:
1. **Search subawards directly** for each target firm
2. Get parent contract PIIDs
3. Fetch contract details
4. Filter for: **DoD + Active + $100M+ obligated**

**Advantage**: Direct path to exactly what we need

---

## CURRENT PROGRESS

**Script**: `dod-discovery-by-target-firms.py`
**Started**: 2026-01-25 19:27
**Phase**: Step 1 - Searching subawards

### Step 1: Target Firm Subaward Search (In Progress)

**Current**: Searching APEX_SYSTEMS (firm 1 of 8)
- Pages processed: 50+
- Subawards found: 5,000+
- **Unique contracts: 1,060+**

**Remaining firms to search**:
- APEX GROUP (pattern 2 for APEX)
- INSIGHT GLOBAL
- TEKSYSTEMS
- TEK SYSTEMS
- BELCAN
- SHINE SYSTEMS
- DCI SOLUTIONS
- PATRIOT DEFENSE GROUP
- AKINA INC

**Expected**: 5,000-10,000 unique contracts total across all firms

---

## WHAT HAPPENS NEXT

### Step 2: Contract Details & Filtering (Pending)

Once all subawards are searched:
1. Get full details for each unique contract
2. Filter for DoD (dept code 97 in awarding OR funding office)
3. Filter for Active (end date in future)
4. Filter for $100M+ obligated

**Expected output**: 50-200 qualified DoD programs

---

## CRITERIA

Final programs must meet ALL:
- ✅ Has target staffing firm as subcontractor (proven via subawards)
- ✅ DoD contract (department_code = 97)
- ✅ Currently active (end date > today)
- ✅ $100M+ obligated

---

## OUTPUT FIELDS

Each program will include:
- `piid` - Contract ID
- `description` - Program description
- `obligated` - Contract value
- `awarding_agency` / `awarding_department` - Who awarded
- `funding_agency` / `funding_department` - Who funds (DoD)
- `prime_contractor` - Main contractor
- `target_firms` - Which target firms are subs (e.g., "APEX_SYSTEMS; TEKSYSTEMS")
- `period_start` / `period_end` / `ultimate_completion` - Dates
- `performance_city` / `performance_state` - Location
- `naics_code` - Industry

---

## WHY THIS APPROACH WORKS

### Previous Problem
- Fast v4: Found 60 DoD contracts with $10M+
- But all had $0 subawards (too new - FY2026)
- None qualified for final criteria

### New Solution
- Start with contracts that HAVE subawards (proven)
- Filter those for DoD + Active + $100M+
- Guaranteed results with target firms present

---

## ESTIMATED TIMELINE

**Step 1**: Subaward search (current)
- 8 firms × 100 pages avg = 800 API requests
- ~3-4 seconds per page
- **ETA**: 40-60 minutes

**Step 2**: Contract filtering
- ~5,000-10,000 contracts to check
- ~2 seconds per contract
- **ETA**: 3-6 hours

**Total**: 4-7 hours to completion

---

## PROGRESS MONITORING

Check real-time status:
```powershell
Get-Content "c:\N8N Builder\dod-discovery-by-firms.log" -Tail 20
```

Or check task output:
```powershell
Get-Content "C:\Users\gtmar\AppData\Local\Temp\claude\c--N8N-Builder\tasks\bc8967a.output" -Tail 30
```

---

## COMPARISON TO PREVIOUS APPROACHES

| Approach | Strategy | Result |
|----------|----------|--------|
| Attempt 1-3 | Find all DoD → check firms | 0 (bugs) |
| Fast v4 | Find DoD → check firms | 0 (no subawards) |
| **Target Firm** | **Find firms → filter DoD** | **50-200 expected** |

---

**Current Status**: Searching APEX SYSTEMS subawards (1,060+ contracts found)
**Next**: Search remaining 7 firms, then filter contracts
**ETA**: 4-7 hours to final dataset
**Confidence**: 90% (direct approach, proven data)

---

**Report Generated**: 2026-01-25 19:32
**Execution**: Running successfully
**No issues detected**
