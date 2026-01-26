# Spec 025: Job Ingestion Pipeline

## Overview

This spec contains the complete job ingestion, enrichment, and Notion upload pipeline developed for the BD-Automation-Engine project.

**Date Created:** January 16, 2026

## What Was Built

A 5-phase pipeline that:
1. Parses job scrapes from Apex Systems and Insight Global
2. Enriches jobs with AI-extracted skills, technologies, certifications
3. Matches jobs to Federal Programs and Prime Contractors
4. Finds potential Hiring Leaders from Contacts databases
5. Identifies PTS Past Performance matches
6. Uploads enriched data to Notion databases

## Results Summary

| Metric | Value |
|--------|-------|
| Total Jobs Processed | 268 (243 after dedup) |
| Prime Contractor Match | 94.7% |
| Program Match | 100% |
| Hiring Leader Match | 100% |
| PTS Past Programs | 90.5% |
| PTS Past Contractors | 73.7% |
| Notion Upload Success | 100% |

## Folder Structure

```
spec-025-job-ingestion-pipeline/
├── README.md                    # This file
├── scripts/
│   └── job_ingestion/
│       ├── __init__.py          # Package exports
│       ├── job_parser.py        # Job parsing & normalization
│       ├── ai_enrichment.py     # AI-powered skill extraction (Claude API)
│       ├── relational_enrichment.py  # Program/Prime matching
│       ├── hiring_leader_lookup.py   # Contact matching
│       ├── pts_past_performance.py   # PTS history matching
│       └── ingestion_pipeline.py     # Full pipeline orchestration
├── outputs/
│   ├── engine1_parsed.json           # Raw parsed jobs
│   ├── engine1_fallback_enriched.json # Regex-based enrichment
│   ├── engine1_relational_enriched.json # With program matches
│   ├── engine1_fully_enriched.json   # Complete enrichment
│   ├── engine1_pts_refreshed.json    # Refreshed PTS data
│   ├── all_jobs_fully_enriched.json  # Final enriched dataset
│   ├── all_jobs_with_hiring_leaders.json
│   └── all_jobs_complete.json
└── source_data/
    ├── Apex Job Scrape.json     # 25 jobs
    ├── Apex Job Scrape2.json    # 50 jobs
    └── Insight Global Scrape.json # 193 jobs
```

## Scripts Description

### job_parser.py
- Normalizes job data from Apex Systems and Insight Global scrapers
- Handles different date formats, field naming conventions
- Extracts company information from URLs
- Normalizes clearance levels and employment types

### ai_enrichment.py
- Uses Claude API to extract:
  - Skills
  - Technologies
  - Certifications (required and extra)
  - Experience years
  - Clearance level
- Includes fallback regex-based extraction when API unavailable

### relational_enrichment.py
- Loads Federal Programs database (401 programs)
- Matches jobs to programs using multiple signals:
  - Location matching
  - Keyword matching
  - Prime contractor detection
  - Job title to typical roles matching

### hiring_leader_lookup.py
- Loads contacts from 3 Notion databases:
  - DCGS Contacts (6,286 contacts)
  - GDIT Other Contacts (1,051 contacts)
  - GDIT PTS Contacts (342 contacts)
- Matches jobs to potential hiring leaders based on:
  - Location/state match
  - Program match
  - Title seniority

### pts_past_performance.py
- Identifies 18 PTS programs from Federal Programs database
- Tracks 10 prime contractors PTS has worked with
- Matches jobs to PTS past performance

### ingestion_pipeline.py
- Full pipeline orchestration
- Notion upload functionality
- Statistics and reporting

## Notion Databases Updated

### 1. Job Database (158df828-5be2-46bc-81e2-9bd6be860d31)
- 243 new jobs created
- Properties: Title, Location, Company, Prime, Program, Subcontractors, Certifications, Reporting Manager, PTS PAST Programs, PTS PAST Contacts

### 2. Insight Global Jobs (2563119e7914442cbe0fb86904a957a1)
- 243 existing jobs updated
- Added: PTS Past Programs, PTS Past Contractors, Hiring Leader

## Environment Variables Required

```
ANTHROPIC_API_KEY=<your-key>
NOTION_TOKEN=<your-token>
NOTION_DB_GDIT_JOBS=2563119e7914442cbe0fb86904a957a1
NOTION_DB_DCGS_CONTACTS=<id>
NOTION_DB_GDIT_OTHER_CONTACTS=<id>
NOTION_DB_GDIT_PTS_CONTACTS=<id>
NOTION_DB_FEDERAL_PROGRAMS=<id>
```

## Usage

```bash
# Parse and enrich jobs
cd BD-Automation-Engine
python scripts/job_ingestion/ingestion_pipeline.py \
  --files Engine1_Scraper/data/*.json \
  --enrich --relational \
  --output outputs/enriched.json

# Upload to Notion
python scripts/job_ingestion/ingestion_pipeline.py \
  --files Engine1_Scraper/data/*.json \
  --enrich --relational --upload
```

## PTS Past Performance Analysis

### Top PTS Programs by Job Count
1. STRATCOM Mission Readiness Support: 111 jobs
2. Integrated Situational Awareness Tool Environment: 110 jobs
3. Basic Ordering Agreement - Surge Staffing: 107 jobs
4. Basic Ordering Agreement (NG Staff Augmentation): 92 jobs
5. DIA SITE III IDIQ: 59 jobs

### Top PTS Contractors by Job Count
1. Northrop Grumman: 99 jobs
2. Leidos: 37 jobs
3. GDIT: 19 jobs
4. SAIC: 9 jobs
5. CACI: 8 jobs

## Notes

- AI enrichment requires Anthropic API credits
- Fallback regex extraction available when API unavailable
- All Notion updates are live and not reversible
- Source files are copies from Engine1_Scraper/data/
