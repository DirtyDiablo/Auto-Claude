# N8N Workflow Inventory
**Generated:** 2026-01-26
**Instance:** https://primetech.app.n8n.cloud/

---

## Summary

| Status | Count |
|--------|-------|
| **Active** | 11 |
| **Inactive** | 26 |
| **Total** | 37 |

---

## Active Workflows (11)

| ID | Name | Nodes | Last Updated | Purpose |
|----|------|-------|--------------|---------|
| `07YOGFu68qlF7QJ7` | Scraper - Full Pipeline | 5 | 2026-01-26 | End-to-end scraping orchestration |
| `4ntAR1gLLgvheMpE` | Monitor - Health Check | 5 | 2026-01-26 | System health monitoring |
| `8LcLkXWJVMuDgjxV` | Alert - Slack Notification | 4 | 2026-01-26 | Slack alert delivery |
| `AA9MFxaq6HK2NkyN` | Pipeline - Competitor Analysis | 6 | 2026-01-26 | Competitor tracking |
| `Cn5mWTIdIOr3pLmZ` | Hub - Search | 4 | 2026-01-26 | Intelligence search |
| `JKLNJ3BB2iAB5BF0` | Hub - Add Insight | 5 | 2026-01-26 | Add insights to hub |
| `KxKAZ2T4x46V6NrI` | Pipeline - BD Intelligence | 6 | 2026-01-26 | BD intelligence generation |
| `PEkVSg9Iy3D8WtWO` | Scraper - Trigger Job Scrape | 5 | 2026-01-26 | Trigger scraping jobs |
| `PSol8u2uFoZlgnuz` | Hub - Ingest Jobs | 5 | 2026-01-26 | Job ingestion pipeline |
| `q8AK6JgJTFn2UMME` | Hub - Smart Query | 4 | 2026-01-26 | AI-powered queries |

---

## Inactive Workflows (26)

### Test Workflows (RECOMMENDED FOR DELETION)

| ID | Name | Nodes | Created | Last Updated |
|----|------|-------|---------|--------------|
| `02rnlscWVCG6CEIz` | My workflow | 29 | 2025-08-25 | 2026-01-02 |
| `2V4AApTzJgAKhIwe` | My workflow 6 | 17 | 2025-08-25 | 2026-01-02 |
| `4ttaVMx86S551ORs` | My workflow 7 | 6 | 2025-08-25 | 2026-01-02 |
| `KASzneSB46eBTC3u` | My workflow 8 | 6 | 2025-09-04 | 2026-01-02 |
| `XSIIH2SB0lNDsFDj` | My workflow 9 | 6 | 2025-09-04 | 2026-01-02 |
| `bJ5j6BENlAtN8exh` | My workflow 4 | 5 | 2025-08-25 | 2026-01-02 |
| `cXx8j4svFYmgJAvb` | My workflow 2 | 29 | 2025-08-25 | 2026-01-02 |
| `piN6rB6PyfwjG19M` | My workflow 5 | 13 | 2025-08-25 | 2026-01-02 |
| `sHMKNV41jzvqEDh1` | My workflow 4 (duplicate) | 5 | 2025-08-25 | 2026-01-02 |
| `yIhUqWqT3O51cM5H` | My workflow 3 | 5 | 2025-08-25 | 2026-01-02 |

### PTS BD Workflows (REVIEW NEEDED)

| ID | Name | Nodes | Created | Status |
|----|------|-------|---------|--------|
| `Ae2ZaSTMwyHK2hUm` | PTS BD - WF3 Hub to BD Opportunities | 7 | 2026-01-02 | May have value |
| `F39P6WBUSYPRmxsu` | PTS BD - WF6 Weekly Summary Report | 7 | 2026-01-02 | May have value |
| `GVkcFmllJFxScJYW` | PTS BD - WF1 Apify Job Scraper Intake | 7 | 2026-01-02 | Duplicate |
| `gbVtJiUif29JaIHs` | PTS BD - WF5 Hot Lead Alerts | 7 | 2026-01-02 | May have value |
| `oBm1uAznir4nRkVx` | PTS BD - WF4 Contact Classification | 9 | 2026-01-02 | May have value |
| `oFAM7yH4gpJchKjI` | PTS BD - WF1 Apify Job Scraper Intake (dup) | 7 | 2026-01-02 | Duplicate |
| `pdzM84gixhnOXEOp` | PTS BD - WF2 AI Enrichment Processor | 11 | 2026-01-02 | May have value |

### Other Inactive Workflows (AUDIT INDIVIDUALLY)

| ID | Name | Nodes | Created | Notes |
|----|------|-------|---------|-------|
| `6tMYMXtk9d2YWxXo` | Apify | 9 | 2025-08-25 | Old Apify integration |
| `CStCIRR1MAkI6ROe` | Error Logging | 45 | 2025-08-25 | Complex error handler |
| `Mets62LUrkNSuquG` | Agent Logger | 21 | 2025-08-25 | Agent logging system |
| `NrrRAihA4vChAlmk` | Clearance Job RAG Agent | 14 | 2025-10-24 | Intelligence/RAG system |
| `KtkyEI5ycnCuh591` | Hub to BD opportunities pipeline | 0 | 2026-01-02 | Empty workflow |
| `S5ZNab8nkGoDRVHG` | Federal Programs Data Fix | 6 | 2025-12-11 | One-time fix |
| `iANkV5H6t9SCfLna` | AI Agent workflow | 12 | 2025-12-11 | Template workflow |
| `ijtOBhIqHGvZ4MOn` | Firecrawl Search Agent | 16 | 2025-08-25 | Search agent |
| `jYihwcJ5BG04QKVC` | Prime TS BD Intelligence v2.1 | 30 | 2025-12-01 | Complex BD system |
| `zWJqb0Vgfql2wEFY` | cleared_jobs_apify_openai_airtable.json | 11 | 2025-08-25 | Old Airtable integration |

---

## Cleanup Recommendations

### Priority 1: DELETE (10 workflows)
- All "My workflow" test files (IDs listed above)
- Empty workflows (`KtkyEI5ycnCuh591`)

### Priority 2: CONSOLIDATE (2 workflows)
- Duplicate PTS BD WF1 workflows (keep one)

### Priority 3: REVIEW (15 workflows)
- PTS BD workflows for potential reactivation
- Complex systems like "Clearance Job RAG Agent" and "Prime TS BD Intelligence v2.1"

---

## Local Workflow Files

The following workflow JSON files exist in `workflows/`:

### Hub Integration
- `hub/hub-smart-query.json`
- `hub/hub-ingest-jobs.json`
- `hub/hub-add-insight.json`
- `hub/hub-search.json`

### Scrapers
- `scraper/trigger-job-scrape.json`
- `scraper/trigger-full-pipeline.json`
- `scraper/scraper-webhook.json`

### Notion
- `notion/sync-jobs-to-notion.json`
- `notion/notion-to-hub.json`

### Scheduled
- `scheduled/daily-scrape.json`
- `scheduled/weekly-report.json`

### Alerts
- `alerts/slack-alert.json`
- `alerts/error-notification.json`

### Pipelines
- `pipelines/full-bd-pipeline.json`
- `pipelines/competitor-analysis.json`

### Other
- `templates/http-with-retry.json`
- `monitoring/health-check.json`
- `core/daily-scrape-sync.json`
- `utilities/hub-integration-base.json`
- `utilities/scraper-integration-base.json`

---

*Last updated: 2026-01-26*
