# Engine 1 — Apify Job Scraper

Daily job scraper for BD intelligence from multiple sources: ClearanceJobs, LinkedIn, competitor job boards, and SAM.gov.

## How It Works

Engine 1 is configuration-driven — no custom scripts. It uses [Apify](https://apify.com/) actors with the settings in `Configurations/ScraperEngine_Config.json`.

**Sources:** ClearanceJobs, LinkedIn, CompetitorSites, SAM.gov

**Output fields:** jobId, title, company, location, clearanceLevel, description, postedDate, url, source, technologies

## Configuration

| Setting | Value |
|---------|-------|
| Rate limit | 10 requests/minute |
| Request delay | 2000ms |
| Dedup window | 7 days (company + title + location) |

Config file: `Configurations/ScraperEngine_Config.json`

## Data

Raw scraper outputs land in `data/` as JSON files:
- `dataset_puppeteer-scraper_*.json` — raw crawl batches
- `Sample_Jobs.json`, `Insight Global Scrape.json`, `Apex Job Scrape.json` — source-specific outputs
- `Jobs_Mapped_to_Programs_MASTER.csv` — post-processing output (from Engine 2)

## Running

```bash
# Set APIFY_API_TOKEN in .env
# Trigger via Apify UI or API with ScraperEngine_Config.json settings
```

## Dependencies

- **External:** Apify actor infrastructure
- **Env vars:** `APIFY_API_TOKEN`
- **Feeds into:** Engine 2 (Program Mapping)
