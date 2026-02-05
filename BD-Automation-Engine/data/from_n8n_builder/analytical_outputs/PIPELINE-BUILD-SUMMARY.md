# Federal Programs Enrichment Pipeline - Build Summary

## Completed Tasks

### 1. Python Libraries Installed
- **fpds** - Python wrapper for FPDS ATOM Feed (180+ contract data elements)
- DIIG CSIS Lookup Tables cloned (861 files with NAICS/PSC codes)

### 2. MCP Server Integration
The Capture MCP Server is actively connected with 10 tools:
- `search_usaspending_awards_by_recipient` - Contract search by vendor
- `get_usaspending_awards` - Agency award data
- `get_usaspending_budgetary_resources` - Budget data
- `search_sam_entities` - SAM.gov entity search
- `get_sam_opportunities` - Contract opportunities
- `check_sam_exclusions` - Exclusion verification
- And more...

### 3. Contract Data Collected
Successfully queried USASpending.gov for major defense contractors:

| Contractor | Contracts Found | Total Value |
|------------|-----------------|-------------|
| Lockheed Martin | 10 | $241B+ |
| Northrop Grumman | 10 | $54B+ |
| Raytheon/RTX | 10 | $47B+ |
| KBR | 10 | $36B+ |
| General Dynamics | 10 | $30B+ |
| BAE Systems | 10 | $28B+ |
| Leidos | 10 | $19B+ |
| Amentum | 10 | $18B+ |
| Booz Allen Hamilton | 10 | $9.7B+ |
| L3Harris | 10 | $9.5B+ |
| Peraton | 10 | $8.3B+ |
| CACI | 10 | $7.7B+ |
| Jacobs | 10 | $8.2B+ |
| GovCIO | 10 | $1.1B+ |
| Palantir | 10 | $1B+ |
| Dynetics | 10 | $830M+ |
| Anduril | 10 | $531M+ |
| ManTech | 10 | $4.7B+ |
| SAIC | 10 | $120M+ |

### 4. DIIG CSIS Lookup Tables Integrated
- **1,629 NAICS codes** with descriptions and categories
- **3,582 PSC codes** with descriptions, portfolios, and classifications
- Source: https://github.com/CSISdefense/Lookup-Tables

### 5. Complete Pipeline Built
**File:** `complete-pipeline.py`

**Features:**
- Contractor name normalization (handles 36+ variations)
- Keyword-based contract matching with scoring
- NAICS/PSC code enrichment
- Contract caching for incremental updates
- CSV output with 11 new enrichment columns

### 6. Enrichment Results

**Input:** 303 active federal programs
**Output:** `Federal Programs COMPLETE ENRICHED.csv`

| Metric | Value |
|--------|-------|
| Total Programs | 303 |
| Contracts Matched | 33 (10.9%) |
| New Columns Added | 11 |

**Sample High-Confidence Matches:**
| Program | Contractor | Contract | Score |
|---------|------------|----------|-------|
| Ground-Based Strategic Deterrent / Sentinel | Northrop Grumman | FA821920C0006 | 5 |
| GPS Next-Gen Operational Control System | Raytheon | FA880710C0001 | 3 |
| CAMMO (AF Satellite Control Network O&M) | CACI | FA882316C0004 | 3 |
| Ground-Based Midcourse Defense | Boeing/Northrop | HQ085621C0003 | 3 |
| ARCYBER Information Advantage | Peraton | 47QFCA19F0033 | 2 |

## New Columns Added

1. `Contract Number (USASpending)` - PIID from USASpending
2. `Contract Value (USASpending)` - Dollar value
3. `Contract Description (USASpending)` - Award description
4. `Awarding Agency (USASpending)` - Agency name
5. `Match Score` - Keyword match confidence (higher = better)
6. `Match Terms` - Keywords that matched
7. `NAICS Description` - Industry classification description
8. `PSC Description` - Product/Service code description
9. `PSC Category` - Service category
10. `PSC Area` - Product/Service area
11. `DoD Portfolio` - Defense portfolio classification

## Files Created

| File | Purpose |
|------|---------|
| `complete-pipeline.py` | Main enrichment pipeline script |
| `Federal Programs COMPLETE ENRICHED.csv` | Enriched output (303 programs x 56 columns) |
| `contract_cache.json` | Contract match cache for incremental updates |
| `DIIG-CSIS-Lookup-Tables/` | NAICS/PSC lookup tables (861 files) |

## Limitations & Next Steps

### Current Limitations
1. **10.9% contract match rate** - Many programs have:
   - Multiple primes listed ("135 awardees", "Multiple primes")
   - Vague contractor names
   - No direct contractor name

2. **NAICS/PSC enrichment at 0%** - Programs lack FPDS codes in source data

### Potential Improvements
1. **Expand keyword matching** - Add program acronyms to search terms
2. **Query SAM.gov opportunities** - Match by solicitation numbers
3. **Use FPDS library** - Query by NAICS code for industry context
4. **Add competitor job scraping** - Match programs to hiring activity
5. **Integrate with n8n workflows** - Automate periodic enrichment

## How to Run

```bash
cd "C:\N8N Builder"
python complete-pipeline.py
```

The pipeline will:
1. Load NAICS/PSC lookup tables
2. Load cached contract mappings
3. Process all 303 programs
4. Match contracts by vendor name + keywords
5. Enrich with NAICS/PSC descriptions
6. Save to `Federal Programs COMPLETE ENRICHED.csv`
7. Update contract cache

## Architecture

```
┌─────────────────────┐
│   Input CSV (303)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌──────────────────────┐
│ Contract Matching   │◄────│ USASpending Data     │
│ (vendor + keywords) │     │ (17+ contractors)    │
└──────────┬──────────┘     └──────────────────────┘
           │
           ▼
┌─────────────────────┐     ┌──────────────────────┐
│ NAICS/PSC Lookup    │◄────│ DIIG CSIS Tables     │
│ (code descriptions) │     │ (5,211 codes)        │
└──────────┬──────────┘     └──────────────────────┘
           │
           ▼
┌─────────────────────┐
│   Output CSV (56    │
│   columns)          │
└─────────────────────┘
```

---
Generated: 2026-01-19
Pipeline Version: 1.0
