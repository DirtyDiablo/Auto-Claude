# V4 TANGO Quick Start Guide

**Run Date:** 2026-01-20 (after quota reset)

---

## 1. VERIFY QUOTA RESET

Check current status:
```bash
cd "c:\N8N Builder"
python enrich-federal-programs-v4-TANGO.py 1
```

Expected: Should process 5 programs successfully (no rate limit errors)

---

## 2. RUN FULL ENRICHMENT

Process all 267 programs with contract numbers:
```bash
cd "c:\N8N Builder"
python enrich-federal-programs-v4-TANGO.py 3
```

**Expected Duration:** 5-10 minutes
**Expected Output:**
- Progress updates every 10 programs
- ~200/267 programs enriched (day 1)
- Remaining ~67 programs on day 2

---

## 3. CHECK RESULTS

View statistics:
```bash
cd "c:\N8N Builder"
python -c "import pandas as pd; df = pd.read_csv('Federal Programs ACTIVE ENRICHED V4 TANGO.csv'); print(f'Total: {len(df)} programs'); print(f'Tango Enriched: {df[\"Tango NAICS Code\"].notna().sum()}'); print(f'NAICS Descriptions: {df[\"NAICS Description\"].notna().sum()}'); print(f'Recipient UEIs: {df[\"Recipient UEI (Tango)\"].notna().sum()}')"
```

---

## 4. ERROR CHECK

View any errors:
```bash
cd "c:\N8N Builder"
cat enrichment-errors-v4.log
```

If rate limit errors:
- Note count of errors
- Schedule day 2 run for remaining programs

---

## 5. SAMPLE OUTPUT

View enriched data for one program:
```bash
cd "c:\N8N Builder"
python -c "import pandas as pd; df = pd.read_csv('Federal Programs ACTIVE ENRICHED V4 TANGO.csv'); sample = df[df['Tango NAICS Code'].notna()].iloc[0]; print('Program:', sample['Program Name']); print('Contract:', sample['Contract Number']); print('NAICS:', sample['Tango NAICS Code'], '-', sample['NAICS Description']); print('Contractor:', sample['Recipient Name (Tango)']); print('UEI:', sample['Recipient UEI (Tango)']); print('Value:', sample['Total Obligated (Tango)']); print('Start:', sample['Contract Start Date (Tango)']); print('End:', sample['Current End Date (Tango)'])"
```

---

## TROUBLESHOOTING

### Rate Limit Errors
**Symptom:** "Tango API rate limit exceeded"
**Solution:** Wait 24 hours, run again

### No Data Returned
**Symptom:** Tango API Records: 0
**Check:**
1. Verify contract numbers exist in input
2. Check error log for specific issues
3. Verify API keys are correct

### Low Success Rate
**Symptom:** < 90% enrichment on programs with contracts
**Check:**
1. Error log for patterns
2. Network connectivity
3. Tango API status

---

## OUTPUT FILES

- **Federal Programs ACTIVE ENRICHED V4 TANGO.csv** - Main output (47 columns)
- **enrichment-errors-v4.log** - Error details
- **V4-TANGO-FINAL-SUMMARY.md** - Full documentation

---

## DUAL API KEY STATUS

**Key Rotation:** Automatic (alternates every request)

**Usage Tracking:**
- Shows as: "Tango: 200 (across 2 keys: 100, 100)"
- Day 1 Limit: 200 requests
- Day 2 Limit: 200 requests (after reset)

**Coverage:**
- Day 1: Programs 1-200
- Day 2: Programs 201-267
- Total: 100% of programs with contract numbers

---

## EXPECTED SUCCESS METRICS

```
Total Programs: 303
With Contracts: 267 (85.3%)
Enrichable: 267

After Day 1:
  Tango Enriched: ~200/267 (75%)
  NAICS Codes: ~200
  Contractor UEIs: ~200
  Financial Data: ~200

After Day 2:
  Tango Enriched: 267/267 (100%)
  NAICS Codes: 267
  Contractor UEIs: 267
  Financial Data: 267
```

---

## QUICK COMMAND REFERENCE

| Task | Command |
|------|---------|
| Test (5 programs) | `python enrich-federal-programs-v4-TANGO.py 1` |
| Small batch (25) | `python enrich-federal-programs-v4-TANGO.py 2` |
| **Full run (267)** | `python enrich-federal-programs-v4-TANGO.py 3` |
| All programs (303) | `python enrich-federal-programs-v4-TANGO.py 4` |
| Check errors | `cat enrichment-errors-v4.log` |
| View output | Open `Federal Programs ACTIVE ENRICHED V4 TANGO.csv` in Excel |

---

**Ready to Execute:** 2026-01-20 00:00 UTC (quota reset)
