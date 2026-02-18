# Master Federal Contracts Database - Replication & Merge Guide

## What Was Built

The BD-Automation-Engine project now has a **unified master SQLite database** (`data/master_federal_contracts.db`, ~48MB) that aggregates 148,000+ records from 8 engines, 40+ CSV files, 3 SQLite databases, and JSON exports into a single program-centric schema.

**Architecture:**
- 17 tables (programs, companies, contracts, task_orders, contacts, jobs, placements, activities, intelligence, documents, timelines, scoring, program_contacts, program_companies, etl_runs, source_tracking, placement_program_links)
- 6 SQL views (program_360_view, bd_pipeline_view, revenue_by_program, contact_network_view, recompete_calendar, competitive_landscape)
- 40 indexes for query performance
- TEXT primary keys (deterministic SHA256 hashes) for cross-project merge compatibility

---

## How to Replicate This in Your Project

### Step 1: Copy the `scripts/master_db/` directory

Copy the entire `BD-Automation-Engine/scripts/master_db/` directory into your project. The structure is:

```
scripts/master_db/
├── __init__.py
├── schema.py          # 17 tables + 6 views + 40 indexes
├── utils.py           # Dedup, currency parsing, name normalization, ID generation
├── build.py           # CLI orchestrator (--full, --tables, --validate, --stats)
├── validate.py        # Post-build validation checks
└── loaders/
    ├── __init__.py
    ├── load_programs.py
    ├── load_companies.py
    ├── load_contracts.py
    ├── load_task_orders.py
    ├── load_contacts.py
    ├── load_jobs.py
    ├── load_placements.py
    ├── load_activities.py
    ├── load_intelligence.py
    ├── load_documents.py
    ├── derive_timelines.py
    ├── derive_scoring.py
    └── link_junctions.py
```

### Step 2: Update `BASE_DIR` in Each Loader

Every loader uses `BASE_DIR = Path(__file__).parent.parent.parent.parent` to find data files relative to the project root. Verify this resolves correctly for your project structure.

### Step 3: Update Loader File Paths

Each loader references specific CSV/JSON/SQLite paths. You need to update these paths to point to YOUR project's data files. See the **Data Source Mapping** section below for exactly which files exist in each project.

### Step 4: Run the Build

```bash
python -m scripts.master_db.build --full --verbose
python -m scripts.master_db.build --validate
python -m scripts.master_db.build --stats
```

### Step 5: Run Tests

```bash
pytest tests/test_master_db.py -v
```

---

## Shared Schema (All 3 Projects Must Use This)

The schema is defined in `scripts/master_db/schema.py`. **All 3 projects MUST use the identical schema** so the databases can be merged. The key tables:

### Core Tables
| Table | Primary Key | Dedup Key | Description |
|-------|------------|-----------|-------------|
| programs | `sha256(name+agency)` | `normalized(program_name) + acronym` | Central hub, all federal programs |
| companies | `sha256(normalized_name)` | `normalized_name`, secondary: `uei`/`cage_code` | Prime contractors, subs, competitors |
| contracts | `sha256(piid)` | `piid` (priority: tango > fpds > usaspending) | Federal contract awards |
| task_orders | `sha256(subaward_number)` | `subaward_number` or `prime_award_id+sub_name` | Subawards and task orders |
| contacts | `sha256(email)` or `sha256(name+company)` | email-first, then `full_name + employer` | All people |
| jobs | `sha256(job_number)` or `sha256(title+company+date)` | `job_number`, then `title + company` | Job postings |
| placements | `sha256(bullhorn_id)` | `bullhorn_id` | Bullhorn placement records |
| activities | `sha256(bullhorn_id)` | `bullhorn_id` | Call notes, meetings |
| intelligence | `sha256(type+name)` | `intel_type + entity_name` | BD targets, gap analysis, competitor intel |
| documents | `sha256(filename)` | `file_name` | Briefings, reports, past performance |

### Derived Tables
| Table | Derived From | Purpose |
|-------|-------------|---------|
| timelines | programs, contracts, recompete CSVs | PoP windows, recompete dates, option years |
| scoring | jobs, contacts, BD targets | Composite BD scores per program |
| program_contacts | contacts, activities, placements | M:M junction with relationship type |
| program_companies | programs, contracts, task_orders | M:M junction with role (prime/sub/competitor) |

### Key Design Decisions
- **TEXT primary keys** using `sha256(key_fields)[:16]` — deterministic across projects
- **`source_files TEXT`** column on every table — tracks provenance for merge auditing
- **`INSERT OR REPLACE`** for primary sources, **`INSERT OR IGNORE`** for enrichment sources
- **`COALESCE(existing, new)`** pattern for enrichment UPDATEs — never overwrite good data with NULL

---

## Data Source Mapping Per Project

### BD-Automation-Engine (DONE — 148,251 records)

Already built. Key sources used:
- `Engine2_ProgramMapping/data/Federal Programs MASTER ENRICHED.csv` (388 programs, 89 cols)
- `Engine7_BullhornETL/data/bullhorn_master.db` (placements, call_notes, jobs, contacts, gap_analysis)
- `data/from_data_scraper/MASTER_*.csv` (programs, primes, contracts, contacts enrichment)
- `outputs/bd_dashboard/contacts_classified.json` (7,339 contacts)
- `outputs/all_jobs_fully_enriched.json` (243 jobs)
- `outputs/BD_Briefings/*.md` (38 briefings)

---

### data-scraper Project (C:/Auto-Claud/data-scraper/)

**Total data: 392 CSVs, 212 JSON files, 4 SQLite databases, ~4.9GB**

#### Programs Loader Updates
| BD-Engine Source | data-scraper Equivalent | Notes |
|-----------------|------------------------|-------|
| `Engine2_ProgramMapping/data/Federal Programs MASTER ENRICHED.csv` | `scraped_data/programs/MASTER_PROGRAMS_ENRICHED.csv` | May have different/additional columns |
| `data/from_data_scraper/MASTER_PROGRAMS_ENRICHED.csv` | `scraped_data/programs/MASTER_PROGRAMS_ENRICHED.csv` | Same file, different path |
| `data/from_data_scraper/PROGRAM_INTELLIGENCE_DETAILED.csv` | `scraped_data/programs/PROGRAM_INTELLIGENCE_DETAILED.csv` | Direct equivalent |
| — | `scraped_data/programs/program_manifests/*.json` (35 files) | **NEW** - Per-program deep intel |
| — | `scraped_data/programs/PROGRAM_INTELLIGENCE.csv` | **NEW** - Additional program intel |
| — | `scraped_data/programs/PROGRAM_LINKS.csv` | **NEW** - Cross-references |

#### Companies Loader Updates
| BD-Engine Source | data-scraper Equivalent | Notes |
|-----------------|------------------------|-------|
| `data/from_data_scraper/MASTER_PRIMES_ENRICHED.csv` | `scraped_data/companies/MASTER_PRIMES_ENRICHED.csv` | Same file |
| — | `scraped_data/companies/company_manifests/*.json` (61 files) | **NEW** - Per-company deep intel |
| — | `scraped_data/companies/PRIMES_FINAL.csv` | **NEW** - Deduplicated primes |
| — | `scraped_data/companies/primes_usaspending_enriched.csv` | **NEW** - USASpending data |
| — | `scraped_data/companies/primes_all.csv` | **NEW** - All primes combined |

#### Contracts Loader Updates
| BD-Engine Source | data-scraper Equivalent | Notes |
|-----------------|------------------------|-------|
| `data/from_data_scraper/MASTER_CONTRACTS_COMBINED.csv` | `scraped_data/contracts/MASTER_CONTRACTS_COMBINED.csv` | Same file |
| — | `scraped_data/contracts/MASTER_FEDERAL_CONTRACTS.csv` (275 rows, 73 cols) | **NEW** - Rich contract data |
| — | `scraped_data/contracts/FULL_PROGRAM_CONTRACTS.csv` | May be same as BD-Engine version |
| — | `scraped_data/contracts/phase1_tango_contracts.csv` | May be same |
| — | `scraped_data/contracts/db1_dod_prime_contracts_100m.csv` | May be same |
| — | `scraped_data/contracts/PHASE3_ALL_PROGRAM_CONTRACTS.csv` | May be same |
| — | `scraped_data/contracts/PHASE5_RECENT_ACTIVE_CONTRACTS.csv` | **NEW** |

#### Contacts Loader Updates
| BD-Engine Source | data-scraper Equivalent | Notes |
|-----------------|------------------------|-------|
| — | `scraped_data/contacts/CONTACT_INTELLIGENCE_DETAILED.csv` | Same as BD-Engine enrichment source |
| — | `scraped_data/contacts/CONTACTS_ALL_SOURCES.csv` | **NEW** - Combined contacts |
| — | `scraped_data/contacts/contacts_by_source/*.csv` | **NEW** - Per-source contact files |

#### Intelligence Loader Updates
| BD-Engine Source | data-scraper Equivalent | Notes |
|-----------------|------------------------|-------|
| — | `scraped_data/intelligence/COMBINED_INTELLIGENCE_REPORT.csv` | Same as BD-Engine |
| — | `scraped_data/intelligence/WARM_GREENFIELD_ENRICHED.csv` (56 cols) | **NEW** - High-value greenfield targets |
| — | `scraped_data/intelligence/bd_master_target_list.csv` | May be same |
| — | `scraped_data/intelligence/bd_all_scored_targets.csv` | May be same |

#### Jobs Loader Updates
| BD-Engine Source | data-scraper Equivalent | Notes |
|-----------------|------------------------|-------|
| — | `scraped_data/jobs/JOBS_ENRICHED.csv` | Same as BD-Engine |
| — | `scraped_data/jobs/JOBS_INTELLIGENCE_MAPPED.csv` | Same as BD-Engine |

#### SQLite Databases
| Database | Path | Key Tables | Rows |
|----------|------|------------|------|
| bullhorn_past_performance.db | `databases/` | past_performance_programs (6,234), past_performance_contacts (7,157), past_performance_contracts (1,217) | 63K total |
| knowledge.db | `databases/` | contacts (~10K), programs, documents, activities | ~10K+ |
| chroma.sqlite3 | `databases/` | 5,700 embeddings | Vector store |
| data_scraper.db | `databases/` | scrape_results, enrichment_runs | Metadata |

#### Unique data-scraper Assets (NOT in BD-Engine)
1. **`bullhorn_past_performance.db`** — 63K records of past performance data (programs, contacts, contracts) — HUGE value for the unified DB
2. **`knowledge.db`** — Pre-indexed contacts and programs
3. **Program manifests** (35 JSON files) — Deep per-program intelligence reports
4. **Company manifests** (61 JSON files) — Deep per-company profiles
5. **`WARM_GREENFIELD_ENRICHED.csv`** — 56-column greenfield opportunity analysis
6. **`MASTER_FEDERAL_CONTRACTS.csv`** — 275 rows with 73 columns of rich contract data

---

### N8N-Builder Project (C:/Auto-Claud/N8N-Builder/)

**Total data: 783 CSVs, 196 JSON files, 11 SQLite databases, ~2.5GB**

#### Programs Loader Updates
| BD-Engine Source | N8N-Builder Equivalent | Notes |
|-----------------|----------------------|-------|
| `Engine2_ProgramMapping/data/Federal Programs MASTER ENRICHED.csv` | `data/Federal Programs FULLY ENRICHED.csv` | **NEWER VERSION** - likely more columns |
| — | `data/DISCOVERED_PROGRAMS_ALL_V2.csv` | **NEW** - Additional discovered programs |
| — | `outputs/master_program_intelligence.json` (62 programs) | **NEW** - Deep program intelligence |
| — | `data/program_mapping/` directory | **NEW** - Program mapping outputs |

#### Contacts Loader Updates
| BD-Engine Source | N8N-Builder Equivalent | Notes |
|-----------------|----------------------|-------|
| `outputs/bd_dashboard/contacts_classified.json` | `outputs/Master_All_Contacts.json` (35,814 contacts) | **MUCH LARGER** - 35K vs 7K contacts |
| — | `outputs/org_chart_full.json` (2.2MB) | **NEW** - Full organizational hierarchy |
| — | `data/contacts/*.csv` | **NEW** - Various contact lists |
| — | `data/Colton Scurry/` directory | **NEW** - Account takeover data |

#### Intelligence Loader Updates
| BD-Engine Source | N8N-Builder Equivalent | Notes |
|-----------------|----------------------|-------|
| — | `data/bd_master_target_list.csv` (300 targets) | Same as BD-Engine |
| — | `data/IMMEDIATE_ACTION_CALL_LIST.csv` | **NEW** - Priority call list |
| — | `outputs/bd_intelligence/` directory | **NEW** - BD analysis outputs |
| — | `data/Account_Manager_Program_Roster.xlsx` | **NEW** - AM assignments |

#### Jobs Loader Updates
| BD-Engine Source | N8N-Builder Equivalent | Notes |
|-----------------|----------------------|-------|
| `outputs/all_jobs_fully_enriched.json` | `outputs/all_jobs_fully_enriched.json` | May be same or newer version |
| — | `data/jobs/*.csv` | Additional job sources |

#### Documents Loader Updates
| BD-Engine Source | N8N-Builder Equivalent | Notes |
|-----------------|----------------------|-------|
| `outputs/BD_Briefings/*.md` | `outputs/BD_Briefings/*.md` | May be same set or newer |
| — | `outputs/reports/*.md` | **NEW** - Additional reports |

#### SQLite Databases
| Database | Path | Key Tables | Notes |
|----------|------|------------|-------|
| bullhorn_master.db | `data/` | Same structure as BD-Engine | May be newer snapshot |
| bd_graph.db | `data/` | entities, relationships | May be newer |
| knowledge.db | `data/` | contacts, programs | May be newer |
| *.db (8 others) | `data/` | Mostly empty schemas | Ignore |

#### Unique N8N-Builder Assets (NOT in BD-Engine)
1. **`Master_All_Contacts.json`** (35,814 contacts) — 5x more contacts than BD-Engine's 7,339
2. **`org_chart_full.json`** — Complete organizational hierarchy (2.2MB)
3. **`DISCOVERED_PROGRAMS_ALL_V2.csv`** — Programs discovered through analysis
4. **`Federal Programs FULLY ENRICHED.csv`** — Newer enriched version of the programs master
5. **`master_program_intelligence.json`** — 62 programs with deep intelligence
6. **`IMMEDIATE_ACTION_CALL_LIST.csv`** — Priority-ranked call list
7. **Colton Scurry takeover data** — Account manager transition data

---

## Phase 2: Merge All 3 Databases

After each project has built its own `master_federal_contracts.db`, merge them into one.

### Merge Script: `scripts/master_db/merge_databases.py`

Create this script in whichever project will be the "master" (recommend BD-Automation-Engine since it's already built):

```python
"""
Merge master databases from BD-Engine, data-scraper, and N8N-Builder
into a single unified database.

Usage:
    python -m scripts.master_db.merge_databases \
        --bd-engine data/master_federal_contracts.db \
        --data-scraper /c/Auto-Claud/data-scraper/data/master_federal_contracts.db \
        --n8n-builder /c/Auto-Claud/N8N-Builder/data/master_federal_contracts.db \
        --output data/unified_federal_contracts.db
"""

import sqlite3
from pathlib import Path

# Priority order: BD-Engine > N8N-Builder > data-scraper
# (BD-Engine has the most curated data, N8N has the most contacts,
#  data-scraper has the most raw scraped data)
SOURCE_PRIORITY = ["bd_engine", "n8n_builder", "data_scraper"]

TABLES_TO_MERGE = [
    "programs", "companies", "contracts", "task_orders",
    "contacts", "jobs", "placements", "activities",
    "intelligence", "documents",
]

DERIVED_TABLES = ["timelines", "scoring", "program_contacts", "program_companies"]


def merge_table(target_conn, source_conn, table: str, source_name: str, verbose: bool):
    """Merge a single table from source into target.

    Strategy:
    - If row doesn't exist in target (by ID): INSERT it
    - If row exists: UPDATE any NULL columns with source values (COALESCE)
    - Track source_files provenance
    """
    src_cursor = source_conn.cursor()
    tgt_cursor = target_conn.cursor()

    # Get column names
    src_cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in src_cursor.fetchall()]

    # Read all source rows
    src_cursor.execute(f"SELECT * FROM {table}")
    rows = src_cursor.fetchall()

    inserted = 0
    enriched = 0

    for row in rows:
        row_dict = dict(zip(columns, row))
        row_id = row_dict.get("id")
        if not row_id:
            continue

        # Check if exists in target
        tgt_cursor.execute(f"SELECT id FROM {table} WHERE id = ?", (row_id,))
        existing = tgt_cursor.fetchone()

        if not existing:
            # INSERT new row
            placeholders = ", ".join(["?" for _ in columns])
            col_names = ", ".join(columns)
            # Append source tag to source_files
            values = list(row)
            if "source_files" in columns:
                sf_idx = columns.index("source_files")
                existing_sf = values[sf_idx] or ""
                values[sf_idx] = f"{existing_sf}|{source_name}" if existing_sf else source_name
            tgt_cursor.execute(
                f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})",
                values
            )
            if tgt_cursor.rowcount > 0:
                inserted += 1
        else:
            # ENRICH existing row - fill NULL columns only
            set_clauses = []
            values = []
            for col in columns:
                if col == "id":
                    continue
                val = row_dict.get(col)
                if val is not None and str(val).strip():
                    set_clauses.append(f"{col} = COALESCE({col}, ?)")
                    values.append(val)

            if set_clauses:
                values.append(row_id)
                tgt_cursor.execute(
                    f"UPDATE {table} SET {', '.join(set_clauses)} WHERE id = ?",
                    values
                )
                if tgt_cursor.rowcount > 0:
                    enriched += 1

    if verbose:
        print(f"  {table}: +{inserted} new, {enriched} enriched from {source_name}")
    return inserted, enriched


def merge_databases(
    bd_engine_path: Path,
    data_scraper_path: Path,
    n8n_builder_path: Path,
    output_path: Path,
    verbose: bool = True,
):
    """Merge 3 project databases into one unified database."""
    import shutil

    # Start with BD-Engine as base (highest priority)
    if verbose:
        print(f"Starting merge...")
        print(f"  Base: {bd_engine_path}")

    shutil.copy2(bd_engine_path, output_path)
    target_conn = sqlite3.connect(str(output_path))
    target_conn.row_factory = sqlite3.Row

    # Merge N8N-Builder (second priority)
    sources = [
        ("n8n_builder", n8n_builder_path),
        ("data_scraper", data_scraper_path),
    ]

    total_new = 0
    total_enriched = 0

    for source_name, source_path in sources:
        if not source_path.exists():
            if verbose:
                print(f"\n  SKIP {source_name}: {source_path} not found")
            continue

        if verbose:
            print(f"\nMerging {source_name}: {source_path}")

        source_conn = sqlite3.connect(str(source_path))
        source_conn.row_factory = sqlite3.Row

        for table in TABLES_TO_MERGE:
            try:
                new, enriched = merge_table(
                    target_conn, source_conn, table, source_name, verbose
                )
                total_new += new
                total_enriched += enriched
            except Exception as e:
                if verbose:
                    print(f"  {table}: ERROR - {e}")

        source_conn.close()

    target_conn.commit()

    # Re-derive computed tables
    if verbose:
        print(f"\nRe-deriving computed tables...")

    from scripts.master_db.loaders.derive_timelines import derive_timelines
    from scripts.master_db.loaders.derive_scoring import derive_scoring
    from scripts.master_db.loaders.link_junctions import link_junctions

    # Clear and rebuild derived tables
    cursor = target_conn.cursor()
    for table in DERIVED_TABLES:
        cursor.execute(f"DELETE FROM {table}")
    target_conn.commit()

    link_junctions(target_conn, verbose=verbose)
    derive_timelines(target_conn, verbose=verbose)
    derive_scoring(target_conn, verbose=verbose)

    target_conn.commit()
    target_conn.close()

    if verbose:
        print(f"\n{'='*60}")
        print(f"MERGE COMPLETE")
        print(f"  New records: {total_new:,}")
        print(f"  Enriched records: {total_enriched:,}")
        print(f"  Output: {output_path}")
        print(f"  Size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
        print(f"{'='*60}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Merge master databases")
    parser.add_argument("--bd-engine", required=True, help="BD-Engine DB path")
    parser.add_argument("--data-scraper", required=True, help="data-scraper DB path")
    parser.add_argument("--n8n-builder", required=True, help="N8N-Builder DB path")
    parser.add_argument("--output", required=True, help="Output unified DB path")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    merge_databases(
        Path(args.bd_engine),
        Path(args.data_scraper),
        Path(args.n8n_builder),
        Path(args.output),
        verbose=args.verbose,
    )
```

### Merge Strategy

1. **Base database:** BD-Automation-Engine (most curated, 148K records)
2. **Second merge:** N8N-Builder (35K contacts, newer program data)
3. **Third merge:** data-scraper (63K past performance records, company manifests)

### Deduplication Rules (by table)

| Table | Match Strategy | On Match |
|-------|---------------|----------|
| programs | Same ID (sha256 of name+agency) | Fill NULL columns from source |
| companies | Same ID (sha256 of normalized_name) | Fill NULL columns |
| contracts | Same ID (sha256 of piid) | Fill NULL columns |
| contacts | Same ID (sha256 of email or name+company) | Fill NULL columns, keep higher tier |
| jobs | Same ID (sha256 of job_number) | Fill NULL columns |
| intelligence | Same ID (sha256 of type+name) | Fill NULL columns, keep higher score |

### Column Merge Rules

- **NULL + value = value** (always fill gaps)
- **value + value = keep original** (BD-Engine data wins)
- **source_files**: Append `|source_name` to track provenance
- **Numeric scores**: Keep the MAX value across sources
- **Dates**: Keep the most recent non-null date
- **tier/priority**: Keep the highest priority classification

---

## Quick Start Checklist

### For data-scraper:
- [ ] Copy `scripts/master_db/` from BD-Automation-Engine
- [ ] Update loader paths to use `scraped_data/` subdirectories
- [ ] Add new loader for `bullhorn_past_performance.db` (63K records — NEW table or merge into existing)
- [ ] Add manifest JSON ingestion (35 program + 61 company manifests)
- [ ] Add `WARM_GREENFIELD_ENRICHED.csv` to intelligence loader
- [ ] Add `MASTER_FEDERAL_CONTRACTS.csv` to contracts loader
- [ ] Run `python -m scripts.master_db.build --full --verbose`
- [ ] Verify with `python -m scripts.master_db.build --validate`

### For N8N-Builder:
- [ ] Copy `scripts/master_db/` from BD-Automation-Engine
- [ ] Update loader paths to use `data/` and `outputs/` directories
- [ ] Update contacts loader to use `Master_All_Contacts.json` (35,814 contacts)
- [ ] Add `org_chart_full.json` ingestion to contacts enrichment
- [ ] Add `Federal Programs FULLY ENRICHED.csv` as primary programs source
- [ ] Add `DISCOVERED_PROGRAMS_ALL_V2.csv` to programs loader
- [ ] Add `master_program_intelligence.json` to intelligence loader
- [ ] Add `IMMEDIATE_ACTION_CALL_LIST.csv` to intelligence loader
- [ ] Run `python -m scripts.master_db.build --full --verbose`
- [ ] Verify with `python -m scripts.master_db.build --validate`

### Final Merge:
- [ ] All 3 projects have built their `data/master_federal_contracts.db`
- [ ] Copy `merge_databases.py` to BD-Automation-Engine
- [ ] Run merge command (see above)
- [ ] Validate unified database
- [ ] Expected: 200K+ records, 100-200MB

---

## Expected Record Counts After Merge

| Table | BD-Engine | data-scraper | N8N-Builder | Unified (est.) |
|-------|-----------|-------------|-------------|----------------|
| programs | 396 | ~400 | ~500 | 500-700 |
| companies | 5,758 | ~7,000 | ~5,000 | 8,000-10,000 |
| contracts | 3,896 | ~4,000 | ~3,000 | 5,000-6,000 |
| task_orders | 5,531 | ~5,500 | ~5,000 | 6,000-7,000 |
| contacts | 33,090 | ~15,000 | ~35,000 | 40,000-50,000 |
| jobs | 374 | ~300 | ~400 | 500-700 |
| placements | 616 | ~600 | ~600 | 616-700 |
| activities | 50,710 | ~50,000 | ~50,000 | 50,710-55,000 |
| intelligence | 784 | ~1,500 | ~1,000 | 2,000-3,000 |
| documents | 97 | ~200 | ~150 | 200-400 |
| **TOTAL** | **148,251** | **~84,500** | **~100,650** | **200,000+** |

Note: Many records will deduplicate across projects since they share the same Bullhorn source and overlapping CSV files. The `sha256` ID generation ensures identical records get the same ID across all 3 projects.
