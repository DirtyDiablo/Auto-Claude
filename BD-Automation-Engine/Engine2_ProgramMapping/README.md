# Engine 2 — Program Mapping

7-stage pipeline that transforms raw job data into standardized 28-field records and maps them to 388+ federal programs (DCGS focus).

## Scripts

| Script | Purpose |
|--------|---------|
| `pipeline.py` | Full 6-stage orchestration: ingest → parse → standardize → match → score → export |
| `job_standardizer.py` | Claude-powered extraction of 28-field schema from raw job text |
| `program_mapper.py` | Multi-signal matching: location, keywords, clearance alignment |
| `exporters.py` | Export to Notion CSV (24 fields) and n8n JSON formats |
| `generate_bd_playbook.py` | Generates playbooks for Hot-tier opportunities |
| `enrich_insight_global_jobs.py` | Enriches Insight Global data with program intelligence |

## 28-Field Schema

**Required (6):** Job Title, Date Posted, Location, Position Overview, Key Responsibilities, Required Qualifications

**Intelligence (8):** Security Clearance, Program Hints, Client Hints, Contract Vehicle Hints, Prime Contractor, Recruiter Contact, Technologies, Certifications Required

**Enrichment (6):** Matched Program, Match Confidence, Match Type, BD Priority Score, Priority Tier, Match Signals

**Metadata (4):** Source, Source URL, Scraped At, Processed At

## Configuration

`Configurations/ProgramMapping_Config.json`:
- DCGS locations (San Diego, Langley, Wright-Patt, etc.)
- Program keywords by agency (DCGS, NSA, DIA, NGA, NRO, Space Force)
- Prime contractor mappings (BAE, GDIT, Leidos, etc.)
- Confidence thresholds: direct=0.70, fuzzy=0.50

## Data

- `Federal Programs*.csv` — 388 federal programs database
- `Federal Programs MASTER ENRICHED.csv` — enriched with Tango data
- `Insight Global Jobs - Program Mapped*.csv` — mapped outputs

## Running

```bash
# Full pipeline
python Engine2_ProgramMapping/scripts/pipeline.py

# Test mode (first 3 jobs)
python Engine2_ProgramMapping/scripts/pipeline.py --test
```

## Dependencies

- **Requires:** `pandas`, `anthropic`, `openai`
- **Input from:** Engine 1 (raw jobs)
- **Feeds into:** Engine 3 (contacts), Engine 4 (playbooks), Engine 5 (scoring)
