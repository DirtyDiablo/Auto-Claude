# DoD Staffing Programs Discovery - Execution Guide

**Project**: DoD Competitive Intelligence Extraction
**Date**: 2026-01-20
**Status**: ✅ READY TO EXECUTE
**Expected Output**: 30-80 DoD programs with target staffing firm intelligence

---

## Pre-Execution Checklist

### Environment Verification

- [ ] **Tango API Key Verified**: `n9pSjPG43Q1BzWZlh_d_1-0dVT3XT6c0lQRkjSkcRLk`
- [ ] **API Requests Remaining**: 24,970 / 25,000 (99.9%)
- [ ] **Output Directory Exists**: `c:\N8N Builder`
- [ ] **Python Dependencies Installed**:
  ```bash
  pip install requests pandas
  ```

### File Verification

- [ ] **Main Script Created**: `dod-staffing-discovery.py`
- [ ] **API Schema Documentation**: `TANGO_API_SCHEMA.md`
- [ ] **This Execution Guide**: `dod-staffing-prompt.md`

### Requirements Understanding

**Criteria**:
- ✅ DoD agency only (not all federal agencies)
- ✅ Currently active contracts (end date in future)
- ✅ $100M+ staffing spend OR 100+ subcontractors
- ✅ At least one target staffing firm present

**Target Firms** (8 total):
1. Apex Systems
2. Insight Global
3. TEKsystems
4. Belcan
5. SHINE Systems
6. DCI Solutions
7. Patriot Defense Group
8. Akina Inc

---

## Execution Command

### Single Command Execution

```bash
cd "c:\N8N Builder"
python dod-staffing-discovery.py
```

### Expected Console Output

The script will display progress through 4 phases:

```
================================================================================
DoD STAFFING PROGRAMS DISCOVERY ENGINE
================================================================================

Configuration:
  Target Firms: 8
  NAICS Codes: 12
  Output Directory: c:\N8N Builder
  API Rate Limit: 25,000 requests/day

Qualification Criteria:
  - DoD agency only
  - Currently active contracts
  - $100M+ staffing spend OR 100+ subcontractors
  - At least one target staffing firm present
================================================================================

[START] DoD Staffing Programs Discovery Pipeline
[ESTIMATE] Runtime: 3-5 hours
[ESTIMATE] API Usage: 700-1,900 requests (~8% of limit)

================================================================================
PHASE 1: DoD CONTRACT DISCOVERY
================================================================================

[SEARCH] Querying NAICS 541511...
  Retrieved 247 contracts
[SEARCH] Querying NAICS 541512...
  Retrieved 198 contracts
...

[OK] Total unique contracts: 1,247

[FILTER] Filtering for DoD agencies...
  DoD contracts: 823

[FILTER] Filtering for active contracts...
  Active contracts: 654

[FILTER] Basic qualification ($1M+ value OR 10+ subs)...
  Qualified contracts: 487

[OK] Phase 1 results exported: dod-staffing-programs-RAW.csv

================================================================================
PHASE 2: SUBAWARDS DEEP DIVE & TARGET FIRM DETECTION
================================================================================

  Processing contract 25/487...
    Target firms found so far: 12
  Processing contract 50/487...
    Target firms found so far: 23
...

[OK] Contracts with target firms: 87
[OK] Final qualified contracts: 52

[OK] Phase 2 results exported: dod-staffing-programs-WITH-TARGETS.csv

================================================================================
PHASE 3: PROGRAM CONSOLIDATION
================================================================================

[PROCESS] Consolidating 52 unique programs...
[OK] Consolidated into 38 unique programs

[OK] Phase 3 results exported: dod-staffing-programs-CONSOLIDATED.csv

================================================================================
PHASE 4: FIELD ENRICHMENT
================================================================================

[OK] Enrichment complete

[OK] Final results exported: dod-staffing-programs-FINAL.csv

================================================================================
DISCOVERY COMPLETE!
================================================================================

Execution Time: 3h 24m

Final Statistics:
  Total Contracts Found: 1247
  DoD Contracts: 823
  Active Contracts: 654
  With Target Firms: 87
  Consolidated Programs: 38
  API Requests Used: 1243

  Target Firms Breakdown:
    APEX                     23 programs
    INSIGHT_GLOBAL           19 programs
    TEKSYSTEMS               31 programs
    BELCAN                    8 programs
    SHINE                     4 programs
    DCI                       6 programs
    PATRIOT                   2 programs
    AKINA                     1 programs

Output Files:
  - dod-staffing-programs-RAW.csv
  - dod-staffing-programs-WITH-TARGETS.csv
  - dod-staffing-programs-CONSOLIDATED.csv
  - dod-staffing-programs-FINAL.csv
  - dod-staffing-stats.json

================================================================================

[DONE] Discovered 38 DoD programs with competitive intelligence!
```

---

## Expected Runtime & API Usage

| Phase | Description | Runtime | API Requests | Output |
|-------|-------------|---------|--------------|--------|
| **Phase 1** | DoD Contract Discovery | 30-60 min | 200-400 | 400-600 qualified contracts |
| **Phase 2** | Subawards Deep Dive | 2-4 hours | 400-1,400 | 50-150 with target firms |
| **Phase 3** | Program Consolidation | 5-10 min | 0 | 30-80 consolidated programs |
| **Phase 4** | Field Enrichment | 5 min | 0 | 30-80 fully enriched |
| **TOTAL** | **Complete Pipeline** | **3-5 hours** | **600-1,800** | **Final dataset** |

**API Usage**: ~6-8% of 25,000/day limit (very safe margin)

---

## Output Files Specification

### 1. dod-staffing-programs-RAW.csv

**Purpose**: All DoD contracts passing basic qualification (Phase 1 output)

**Expected Rows**: 400-600

**Columns** (~15):
- piid
- program_name
- customer_agency
- prime_contractor
- total_contract_value
- subawards_total
- subcontractor_count
- period_start
- period_end
- ultimate_completion
- performance_location
- naics_code
- is_active

### 2. dod-staffing-programs-WITH-TARGETS.csv

**Purpose**: Only programs with target staffing firms present (Phase 2 output)

**Expected Rows**: 50-150

**Columns** (~18):
- All columns from RAW.csv
- target_firms_present (semicolon-separated list)
- target_firms_total_spend
- qualifies_final (TRUE/FALSE)

### 3. dod-staffing-programs-CONSOLIDATED.csv

**Purpose**: Programs consolidated by name (Phase 3 output)

**Expected Rows**: 30-80

**Columns** (~20):
- program_name
- acronym
- customer_agency
- piids (semicolon-separated - multiple contracts)
- prime_contractors (semicolon-separated - multiple primes)
- target_firms_present
- total_contract_value (summed across all contracts)
- subawards_total (summed)
- subcontractor_count (summed)
- target_firms_total_spend
- period_start (earliest)
- period_end (latest)
- ultimate_completion (latest)
- performance_locations (semicolon-separated - all locations)
- contract_description
- functional_areas
- task_orders
- job_titles
- naics_code
- contract_count (how many PIIDs consolidated)
- is_active

### 4. dod-staffing-programs-FINAL.csv (PRIMARY OUTPUT)

**Purpose**: Final enriched dataset with all fields (Phase 4 output)

**Expected Rows**: 30-80

**Columns** (22 total):
- All columns from CONSOLIDATED.csv
- teams_in_locations (marked as [Manual Research Required])

**Example Row**:
```csv
program_name,acronym,customer_agency,piids,prime_contractors,target_firms_present,total_contract_value,subawards_total,subcontractor_count,target_firms_total_spend,period_start,period_end,ultimate_completion,performance_locations,contract_description,functional_areas,task_orders,job_titles,teams_in_locations,naics_code,contract_count,is_active
"Mission Partner Environment","MPE","Department of the Air Force","FA8771-19-C-0001; FA8771-20-C-0002","Accenture Federal Services; Leidos Inc","APEX; INSIGHT_GLOBAL; TEKSYSTEMS",482000000.00,82967626.84,144,12500000.00,2019-09-27,2024-09-26,2029-09-26,"Scott AFB, IL; Fort Meade, MD","Joint training synthetic environment...","Software Development; Cybersecurity; Cloud Services","Prime Contract","Software Developer; Systems Engineer; DevOps Engineer","[Manual Research Required]","541512",2,TRUE
```

### 5. dod-staffing-stats.json

**Purpose**: Detailed execution statistics and metadata

**Content**:
```json
{
  "timestamp": "2026-01-20T15:30:00",
  "execution_time_hours": 3.4,
  "total_contracts_found": 1247,
  "dod_contracts": 823,
  "active_contracts": 654,
  "with_target_firms": 87,
  "programs_consolidated": 38,
  "api_requests": 1243,
  "target_firms_breakdown": {
    "APEX": 23,
    "INSIGHT_GLOBAL": 19,
    "TEKSYSTEMS": 31,
    "BELCAN": 8,
    "SHINE": 4,
    "DCI": 6,
    "PATRIOT": 2,
    "AKINA": 1
  },
  "total_programs": 38,
  "errors": []
}
```

---

## Post-Execution Validation

### Validate Output Files Exist

```powershell
# Check all 5 output files
$outputDir = "c:\N8N Builder"
$files = @(
    "dod-staffing-programs-RAW.csv",
    "dod-staffing-programs-WITH-TARGETS.csv",
    "dod-staffing-programs-CONSOLIDATED.csv",
    "dod-staffing-programs-FINAL.csv",
    "dod-staffing-stats.json"
)

foreach ($file in $files) {
    $path = Join-Path $outputDir $file
    if (Test-Path $path) {
        Write-Host "[OK] $file exists" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] $file missing" -ForegroundColor Red
    }
}
```

### Validate Final Output Structure

```powershell
# Load final CSV
$final = Import-Csv "c:\N8N Builder\dod-staffing-programs-FINAL.csv"

Write-Host "`nFinal Output Validation:" -ForegroundColor Cyan
Write-Host "  Total programs: $($final.Count)"
Write-Host "  Columns: $(($final | Get-Member -MemberType NoteProperty).Count)"

# Check expected columns
$expectedColumns = @(
    'program_name', 'acronym', 'customer_agency', 'piids',
    'prime_contractors', 'target_firms_present', 'total_contract_value',
    'subawards_total', 'subcontractor_count', 'target_firms_total_spend',
    'period_start', 'period_end', 'ultimate_completion',
    'performance_locations', 'contract_description', 'functional_areas',
    'task_orders', 'job_titles', 'teams_in_locations', 'naics_code',
    'contract_count', 'is_active'
)

$actualColumns = ($final | Get-Member -MemberType NoteProperty).Name
$missingColumns = $expectedColumns | Where-Object { $_ -notin $actualColumns }

if ($missingColumns.Count -eq 0) {
    Write-Host "  [OK] All 22 expected columns present" -ForegroundColor Green
} else {
    Write-Host "  [WARNING] Missing columns: $($missingColumns -join ', ')" -ForegroundColor Yellow
}
```

### Validate Data Quality

```powershell
# Load final data
$final = Import-Csv "c:\N8N Builder\dod-staffing-programs-FINAL.csv"

Write-Host "`nData Quality Checks:" -ForegroundColor Cyan

# Check all 8 target firms detected
$allFirms = $final.target_firms_present -join ';'
$targetFirms = @('APEX', 'INSIGHT_GLOBAL', 'TEKSYSTEMS', 'BELCAN', 'SHINE', 'DCI', 'PATRIOT', 'AKINA')

Write-Host "`n  Target Firms Detection:"
foreach ($firm in $targetFirms) {
    if ($allFirms -like "*$firm*") {
        Write-Host "    [OK] $firm detected" -ForegroundColor Green
    } else {
        Write-Host "    [WARNING] $firm NOT detected" -ForegroundColor Yellow
    }
}

# Check value ranges
Write-Host "`n  Value Ranges:"
$minValue = ($final.total_contract_value | Measure-Object -Minimum).Minimum
$maxValue = ($final.total_contract_value | Measure-Object -Maximum).Maximum
$avgValue = ($final.total_contract_value | Measure-Object -Average).Average

Write-Host "    Contract Value Range: $([math]::Round($minValue/1e6, 1))M - $([math]::Round($maxValue/1e6, 1))M"
Write-Host "    Average Contract Value: $([math]::Round($avgValue/1e6, 1))M"

# Check DoD agencies
$agencies = $final.customer_agency | Select-Object -Unique
Write-Host "`n  DoD Agencies Found: $($agencies.Count)"
foreach ($agency in $agencies) {
    Write-Host "    - $agency"
}

# Check active status
$activeCount = ($final | Where-Object { $_.is_active -eq 'True' }).Count
Write-Host "`n  Active Programs: $activeCount / $($final.Count)"

# Check field population
Write-Host "`n  Field Population:"
$fields = @('acronym', 'functional_areas', 'job_titles', 'task_orders')
foreach ($field in $fields) {
    $populated = ($final | Where-Object { $_.$field -ne '' }).Count
    $percentage = [math]::Round(($populated / $final.Count) * 100, 1)
    Write-Host "    $field: $populated / $($final.Count) ($percentage%)"
}
```

### Validate Statistics File

```powershell
# Load stats JSON
$stats = Get-Content "c:\N8N Builder\dod-staffing-stats.json" | ConvertFrom-Json

Write-Host "`nExecution Statistics:" -ForegroundColor Cyan
Write-Host "  Timestamp: $($stats.timestamp)"
Write-Host "  Execution Time: $($stats.execution_time_hours) hours"
Write-Host "  API Requests Used: $($stats.api_requests) / 25,000 ($([math]::Round(($stats.api_requests/25000)*100, 1))%)"
Write-Host "  Total Contracts Found: $($stats.total_contracts_found)"
Write-Host "  DoD Contracts: $($stats.dod_contracts)"
Write-Host "  Active Contracts: $($stats.active_contracts)"
Write-Host "  With Target Firms: $($stats.with_target_firms)"
Write-Host "  Final Programs: $($stats.programs_consolidated)"

if ($stats.errors.Count -gt 0) {
    Write-Host "  [WARNING] Errors encountered: $($stats.errors.Count)" -ForegroundColor Yellow
} else {
    Write-Host "  [OK] No errors" -ForegroundColor Green
}
```

---

## Success Criteria

### Minimum Success (MVP)

- ✅ 20+ consolidated programs found
- ✅ 5+ of 8 target staffing firms detected
- ✅ 18/22 output fields populated (82%)
- ✅ API usage < 2,500 requests (10% of limit)
- ✅ Runtime < 6 hours
- ✅ No fatal errors

### Target Success (Expected)

- ✅ 40+ consolidated programs
- ✅ All 8 target staffing firms detected
- ✅ 21/22 output fields populated (95%)
- ✅ API usage 600-1,800 requests (~6-8% of limit)
- ✅ Runtime 3-5 hours
- ✅ Zero errors

### Exceptional Success

- ✅ 60+ consolidated programs
- ✅ All 8 firms with $10M+ total identified spend each
- ✅ 22/22 fields populated (100%)
- ✅ API usage < 1,500 requests
- ✅ Runtime < 4 hours
- ✅ Comprehensive competitive intelligence

---

## Troubleshooting

### If Script Fails During Phase 1

**Symptom**: Error during NAICS querying

**Possible Causes**:
- API key invalid
- Network connection issues
- Tango API downtime

**Solution**:
```bash
# Verify API key
curl -H "X-API-Key: n9pSjPG43Q1BzWZlh_d_1-0dVT3XT6c0lQRkjSkcRLk" \
  "https://tango.makegov.com/api/contracts/?limit=1"

# If 401: API key issue
# If 200: API is working, check network
# If timeout: Network or API downtime
```

### If Script Fails During Phase 2

**Symptom**: Error during subawards queries

**Possible Causes**:
- Rate limit hit (429 error)
- Server timeout
- Invalid PIID format

**Solution**:
- Script auto-retries on 429 (pauses 60s)
- Check error log in stats JSON
- Partial results still saved to Phase 1 output

### If No Target Firms Found

**Symptom**: Zero programs with target firms

**Possible Causes**:
- Firms not working on DoD contracts currently
- Name variations not covered
- Qualification criteria too strict

**Solution**:
1. Review `dod-staffing-programs-RAW.csv` to see what was found
2. Check if subcontractor_count > 0 for any contracts
3. Adjust target firm patterns in script if needed
4. Lower qualification thresholds temporarily

### If Runtime Exceeds 6 Hours

**Symptom**: Script still running after 6 hours

**Possible Causes**:
- API response times slow
- More contracts than expected
- Network latency

**Solution**:
- Script saves progress incrementally
- Partial results available in intermediate CSVs
- Check API request count in console output
- Can Ctrl+C and resume from Phase 2 CSV if needed

### If API Rate Limit Exceeded

**Symptom**: 429 errors not recovering

**Possible Causes**:
- Other processes using same API key
- Daily limit already consumed

**Solution**:
- Check Tango dashboard for usage
- Wait until next day (limit resets)
- Script auto-pauses and retries on 429

---

## Next Steps After Execution

### Immediate Review

1. **Open Final CSV**:
   ```powershell
   Invoke-Item "c:\N8N Builder\dod-staffing-programs-FINAL.csv"
   ```

2. **Sort by Contract Value**:
   - Identify highest-value programs
   - Focus on top 20 for initial BD efforts

3. **Filter by Target Firm**:
   - See which competitors are most active
   - Identify overlapping programs

4. **Review Performance Locations**:
   - Identify geographic concentration
   - Plan regional BD strategy

### CRM Import Preparation

1. **Select Top Programs**:
   - Top 50 by contract value
   - Programs with 3+ target firms
   - Programs in key locations

2. **Map to CRM Fields**:
   - Program Name → Opportunity Name
   - Prime Contractors → Account Name
   - Total Contract Value → Deal Size
   - Target Firms Present → Competitors
   - Recompete Date (if calculated) → Close Date

3. **Export for Import**:
   ```powershell
   # Create CRM-ready subset
   $final = Import-Csv "c:\N8N Builder\dod-staffing-programs-FINAL.csv"
   $top50 = $final | Sort-Object {[double]$_.total_contract_value} -Descending | Select-Object -First 50
   $top50 | Export-Csv "c:\N8N Builder\CRM-IMPORT-TOP50.csv" -NoTypeInformation
   ```

### Competitive Analysis

1. **Create Firm-Specific Views**:
   ```powershell
   $final = Import-Csv "c:\N8N Builder\dod-staffing-programs-FINAL.csv"

   # Programs with Apex
   $apex = $final | Where-Object { $_.target_firms_present -like '*APEX*' }
   $apex | Export-Csv "c:\N8N Builder\APEX-Programs.csv" -NoTypeInformation

   # Repeat for each target firm
   ```

2. **Identify Net-New Opportunities**:
   - Compare against existing known programs
   - Focus on programs you weren't tracking
   - Prioritize by value + contractor count

3. **Build Win Strategy**:
   - Analyze prime contractor relationships
   - Review performance locations for presence
   - Assess functional areas for capability alignment

---

## Status

**Execution Status**: ✅ READY TO EXECUTE

**All Prerequisites Complete**:
- ✅ API key verified
- ✅ Scripts created
- ✅ Documentation complete
- ✅ Execution guide ready

**Confidence Level**: HIGH
- All corrections from API testing applied
- Production patterns from capture-mcp-server integrated
- Verified Tango API behavior
- Comprehensive error handling
- Incremental progress saving

---

**To execute, run**:
```bash
cd "c:\N8N Builder"
python dod-staffing-discovery.py
```

**Expected completion**: 3-5 hours from start

**Expected output**: 30-80 DoD programs with competitive intelligence across 22 data fields
