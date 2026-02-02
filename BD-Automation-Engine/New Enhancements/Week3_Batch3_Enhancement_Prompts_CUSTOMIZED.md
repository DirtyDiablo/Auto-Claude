# Week 3 Batch 3: Auto-Claude Enhancement Prompts (CUSTOMIZED)

## 🎯 SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PTS BD INTELLIGENCE STACK                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │   TERMINAL 2-1      │  │   TERMINAL 1-1      │  │   TERMINAL 3-1      │ │
│  │   data-scraper      │  │ bd-automation-engine│  │   n8n-builder       │ │
│  │                     │  │                     │  │                     │ │
│  │ • JobSpy Aggregator │  │ • FastAPI Hub :8000 │  │ • n8n Cloud         │ │
│  │ • FPDS Parser       │  │ • Qdrant :6333      │  │ • Kestra :8081      │ │
│  │ • GovCon API Client │  │ • LangGraph RAG     │  │ • Design System     │ │
│  │ • Stirling-PDF      │  │ • Hybrid Search     │  │ • Dashboard UI      │ │
│  │                     │  │ • Reacher :8080     │  │                     │ │
│  │ scrapers/           │  │ • Twenty CRM :3000  │  │ workflows/          │ │
│  │ external_apis/      │  │ • Proxycurl         │  │ design_intelligence/│ │
│  │ pdf_processing/     │  │ • RFP Agent         │  │                     │ │
│  └─────────┬───────────┘  └─────────┬───────────┘  └─────────┬───────────┘ │
│            │                        │                        │             │
│            └────────────────────────┼────────────────────────┘             │
│                                     │                                       │
│                           ┌─────────▼─────────┐                            │
│                           │  NOTION DATABASES │                            │
│                           │                   │                            │
│                           │ • DCGS Contacts   │                            │
│                           │ • Federal Programs│                            │
│                           │ • Program Mapping │                            │
│                           │ • GDIT Jobs       │                            │
│                           └───────────────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 QUICK REFERENCE

| Prompt # | Tool/Library | Terminal | Project | Est. Time | Dependencies |
|----------|-------------|----------|---------|-----------|--------------|
| 1 | JobSpy | 2-1 | data-scraper | 1-2 hours | None |
| 2 | FPDS Parser | 2-1 | data-scraper | 1-2 hours | None |
| 3 | GovCon API | 2-1 | data-scraper | 1 hour | API Key |
| 4 | Reacher Email | 1-1 | bd-automation-engine | 1-2 hours | Docker |
| 5 | LangGraph RAG | 1-1 | bd-automation-engine | 3-4 hours | Qdrant running |
| 6 | Hybrid Search | 1-1 | bd-automation-engine | 2-3 hours | Prompt #5 |
| 7 | Twenty CRM | 1-1 | bd-automation-engine | 3-4 hours | Docker |
| 8 | Reagraph | 1-1 | bd-automation-engine | 2-3 hours | Node.js |
| 9 | Apache ECharts | 1-1 | bd-automation-engine | 2 hours | Node.js |
| 10 | RFP Response Agent | 1-1 | bd-automation-engine | 2-3 hours | Prompt #5 |
| 11 | Proxycurl | 1-1 | bd-automation-engine | 1-2 hours | API Key |
| 12 | Kestra Workflows | 3-1 | n8n-builder | 2-3 hours | Docker |

---

## 🚀 EXECUTION ORDER & PARALLELIZATION

### Phase 0: Pre-Flight Setup (15 minutes)
```bash
# On your Windows machine before starting terminals

# 1. Start Docker Desktop
# 2. Verify Docker is running
docker --version

# 3. Start required containers (run these BEFORE terminal prompts)
docker run -d --name reacher -p 8080:8080 reacherhq/backend:latest
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest
```

### Phase 1: Data Collection Foundation (Terminal 2-1)
**Run FIRST - These feed data to other systems**

| Order | Prompt | Run Command |
|-------|--------|-------------|
| 1.1 | #1 JobSpy | Copy prompt → Terminal 2-1 |
| 1.2 | #2 FPDS Parser | Copy prompt → Terminal 2-1 |
| 1.3 | #3 GovCon API | Copy prompt → Terminal 2-1 |

### Phase 2: AI & Memory (Terminal 1-1)
**Can run in PARALLEL with Phase 1**

| Order | Prompt | Run Command |
|-------|--------|-------------|
| 2.1 | #4 Reacher | Copy prompt → Terminal 1-1 |
| 2.2 | #5 LangGraph | Copy prompt → Terminal 1-1 (after #4) |
| 2.3 | #6 Hybrid Search | Copy prompt → Terminal 1-1 (after #5) |

### Phase 3: CRM & Visualization (Terminal 1-1)
**After Phase 2 completes**

| Order | Prompt | Run Command |
|-------|--------|-------------|
| 3.1 | #7 Twenty CRM | Copy prompt → Terminal 1-1 |
| 3.2 | #8 Reagraph | Copy prompt → Terminal 1-1 (parallel with #7) |
| 3.3 | #9 ECharts | Copy prompt → Terminal 1-1 (parallel with #7) |

### Phase 4: Advanced Agents (Terminal 1-1)
**After Phase 3 completes**

| Order | Prompt | Run Command |
|-------|--------|-------------|
| 4.1 | #10 RFP Agent | Copy prompt → Terminal 1-1 |
| 4.2 | #11 Proxycurl | Copy prompt → Terminal 1-1 |

### Phase 5: Workflow Orchestration (Terminal 3-1)
**Can run in PARALLEL with Phase 2-4**

| Order | Prompt | Run Command |
|-------|--------|-------------|
| 5.1 | #12 Kestra | Copy prompt → Terminal 3-1 |

---

## ✅ PRE-FLIGHT CHECKLIST

### System Requirements
- [ ] Docker Desktop installed and running
- [ ] Node.js v18+ installed (`node --version`)
- [ ] Python 3.10+ installed (`python --version`)
- [ ] Git installed (`git --version`)
- [ ] At least 16GB RAM available
- [ ] At least 20GB disk space free

### API Keys Required
- [ ] `ANTHROPIC_API_KEY` - For LLM calls
- [ ] `GOVCON_API_KEY` - Sign up at govconapi.com
- [ ] `PROXYCURL_API_KEY` - Sign up at nubela.co/proxycurl
- [ ] `SAM_GOV_API_KEY` - From api.sam.gov

### Docker Containers Pre-Started
```bash
# Verify containers running
docker ps

# Expected output should show:
# - reacher (port 8080)
# - qdrant (ports 6333, 6334)
```

### Existing Infrastructure Verified
- [ ] Notion MCP connected (test: search DCGS contacts)
- [ ] n8n Cloud accessible: https://primetech.app.n8n.cloud
- [ ] Apify MCP connected (test: search-actors "LinkedIn jobs")
- [ ] Qdrant has data: 8,447+ vectors in bd_documents collection

### Project Folders Exist
```bash
# Terminal 2-1: data-scraper
ls -la ~/data-scraper/
# Should have: scrapers/, external_apis/, pdf_processing/

# Terminal 1-1: bd-automation-engine
ls -la ~/bd-automation-engine/
# Should have: agents/, services/, hub/, memory/

# Terminal 3-1: n8n-builder
ls -la ~/n8n-builder/
# Should have: workflows/, design_intelligence/
```

---

## 📦 NOTION DATABASE REFERENCE

| Database | Collection ID | Records |
|----------|---------------|---------|
| DCGS Contacts Full | `2ccdef65-baa5-8087-a53b-000ba596128e` | ~965 |
| GDIT Other Contacts | `70ea1c94-211d-40e6-a994-e8d7c4807434` | ~1,052 |
| GDIT Jobs | `2ccdef65-baa5-80b0-9a80-000bd2745f63` | ~700 |
| Program Mapping Hub | `f57792c1-605b-424c-8830-23ab41c47137` | Variable |
| Federal Programs | `06cd9b22-5d6b-4d37-b0d3-ba99da4971fa` | 388 |

---

# PROMPT 1: JOBSPY MULTI-BOARD AGGREGATION
## Target: data-scraper (Terminal 2-1)

### Copy This Prompt:

```
## ENHANCEMENT: JobSpy Multi-Board Job Aggregation

### OBJECTIVE
Integrate JobSpy (https://github.com/Bunsly/JobSpy) to replace individual Apify Puppeteer scrapers with unified multi-board aggregation including native salary parsing and company metadata enrichment.

### CONTEXT
- JobSpy aggregates LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter in single call
- Returns structured pandas DataFrame with salary normalization
- Replaces our current Apify Puppeteer scrapers (dataset_puppeteerscraper_*.csv files)
- Must integrate with existing Program Mapping Hub (Collection ID: f57792c1-605b-424c-8830-23ab41c47137)

### INSTALLATION
pip install python-jobspy pandas httpx

### IMPLEMENTATION REQUIREMENTS

Create folder structure:
```
scrapers/
├── unified/
│   ├── __init__.py
│   ├── jobspy_aggregator.py
│   └── jobspy_scheduler.py
└── existing files...
```

#### File 1: scrapers/unified/jobspy_aggregator.py

```python
"""JobSpy multi-board job aggregator for BD intelligence."""
from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import re

class JobSpyAggregator:
    """Unified job scraping across multiple boards."""
    
    # BD-relevant keywords for DCGS targeting
    BD_KEYWORDS: List[str] = [
        "DCGS", "ISR analyst", "intelligence analyst", 
        "TS/SCI", "CI Poly", "SIGINT", "GEOINT",
        "network engineer cleared", "systems administrator TS",
        "cyber security clearance", "DevSecOps cleared"
    ]
    
    # Priority DCGS locations
    BD_LOCATIONS: List[str] = [
        "San Diego, CA",      # AF DCGS - PACAF 🔥
        "Hampton, VA",        # AF DCGS - Langley
        "Dayton, OH",         # AF DCGS - Wright-Patt
        "Norfolk, VA",        # Navy DCGS-N
        "Fort Belvoir, VA",   # Army DCGS-A
        "Herndon, VA",        # GDIT Corporate HQ
        "Falls Church, VA"    # GDIT Corporate
    ]
    
    # Competitors to flag
    COMPETITOR_COMPANIES: List[str] = [
        "Insight Global", "TEKsystems", "Apex Systems",
        "GDIT", "Leidos", "SAIC", "CACI", "Peraton", "BAE Systems"
    ]
    
    # Location to program mapping
    LOCATION_TO_PROGRAM: Dict[str, str] = {
        "San Diego": "AF DCGS - PACAF",
        "La Mesa": "AF DCGS - PACAF",
        "Hampton": "AF DCGS - Langley",
        "Newport News": "AF DCGS - Langley",
        "Langley": "AF DCGS - Langley",
        "Dayton": "AF DCGS - Wright-Patt",
        "Beavercreek": "AF DCGS - Wright-Patt",
        "Fairborn": "AF DCGS - Wright-Patt",
        "Norfolk": "Navy DCGS-N",
        "Suffolk": "Navy DCGS-N",
        "Virginia Beach": "Navy DCGS-N",
        "Fort Belvoir": "Army DCGS-A",
        "Fort Detrick": "Army DCGS-A",
        "Aberdeen": "Army DCGS-A",
        "Herndon": "Corporate HQ",
        "Falls Church": "Corporate HQ",
        "Reston": "Corporate HQ",
        "Fairfax": "Corporate HQ"
    }
    
    def __init__(self, proxies: List[str] = None):
        self.proxies = proxies
        
    def scrape_bd_jobs(
        self,
        keywords: List[str] = None,
        locations: List[str] = None,
        sites: List[str] = None,
        results_per_site: int = 50,
        hours_old: int = 72
    ) -> pd.DataFrame:
        """
        Scrape jobs from multiple boards with BD-specific targeting.
        
        Args:
            keywords: Search terms (defaults to BD_KEYWORDS)
            locations: Target locations (defaults to BD_LOCATIONS)
            sites: Job boards to scrape (defaults to major boards)
            results_per_site: Max results per site per search
            hours_old: Only jobs posted within N hours
        """
        keywords = keywords or self.BD_KEYWORDS
        locations = locations or self.BD_LOCATIONS
        sites = sites or ["linkedin", "indeed", "glassdoor", "zip_recruiter"]
        
        all_jobs = []
        
        for keyword in keywords:
            for location in locations:
                try:
                    jobs = scrape_jobs(
                        site_name=sites,
                        search_term=keyword,
                        location=location,
                        results_wanted=results_per_site,
                        hours_old=hours_old,
                        country_indeed="USA"
                    )
                    
                    if not jobs.empty:
                        jobs['search_keyword'] = keyword
                        jobs['search_location'] = location
                        jobs['scraped_at'] = datetime.now().isoformat()
                        all_jobs.append(jobs)
                        
                except Exception as e:
                    print(f"Error scraping {keyword} in {location}: {e}")
                    continue
        
        if not all_jobs:
            return pd.DataFrame()
            
        combined = pd.concat(all_jobs, ignore_index=True)
        return self._deduplicate_and_enrich(combined)
    
    def _deduplicate_and_enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        """Deduplicate by URL and add BD-specific enrichments."""
        # Dedupe by job URL
        df = df.drop_duplicates(subset=['job_url'], keep='first')
        
        # Add BD enrichments
        df['bd_relevance_score'] = df.apply(self._calculate_bd_score, axis=1)
        df['is_competitor'] = df['company'].apply(
            lambda x: any(c.lower() in str(x).lower() for c in self.COMPETITOR_COMPANIES)
        )
        df['detected_clearance'] = df.apply(self._extract_clearance, axis=1)
        df['inferred_program'] = df['location'].apply(self._infer_program)
        
        # Sort by BD score descending
        df = df.sort_values('bd_relevance_score', ascending=False)
        
        return df.reset_index(drop=True)
    
    def _calculate_bd_score(self, row) -> int:
        """Calculate BD relevance score (0-100)."""
        score = 0
        text = f"{row.get('title', '')} {row.get('description', '')}".lower()
        location = str(row.get('location', '')).lower()
        
        # DCGS keywords: +30
        dcgs_keywords = ['dcgs', 'distributed common ground', 'dgs-1', 'dcgs-a', 'dcgs-n']
        if any(kw in text for kw in dcgs_keywords):
            score += 30
        
        # Clearance indicators: +25
        clearance_keywords = ['ts/sci', 'top secret', 'ci poly', 'full scope poly']
        if any(kw in text for kw in clearance_keywords):
            score += 25
        
        # ISR/Intel keywords: +20
        intel_keywords = ['isr', 'intelligence', 'sigint', 'geoint', 'imagery', 'analyst']
        if any(kw in text for kw in intel_keywords):
            score += 20
        
        # Priority location match: +15
        priority_locs = ['san diego', 'hampton', 'langley', 'dayton', 'norfolk']
        if any(loc in location for loc in priority_locs):
            score += 15
        
        # Competitor company: +10 (good for intel)
        if any(c.lower() in str(row.get('company', '')).lower() for c in self.COMPETITOR_COMPANIES):
            score += 10
        
        return min(score, 100)
    
    def _extract_clearance(self, row) -> str:
        """Extract clearance requirement from job."""
        text = f"{row.get('title', '')} {row.get('description', '')}".lower()
        
        patterns = [
            (r'ts/sci.*(?:full.?scope|fs).?poly', 'TS/SCI with FS Poly'),
            (r'ts/sci.*ci.?poly|ci.?poly.*ts/sci', 'TS/SCI with CI Poly'),
            (r'ts/sci|top.?secret/sci', 'TS/SCI'),
            (r'top.?secret(?!/sci)', 'Top Secret'),
            (r'(?<!top.)secret', 'Secret'),
            (r'public.?trust', 'Public Trust'),
        ]
        
        for pattern, clearance in patterns:
            if re.search(pattern, text):
                return clearance
        
        return 'Unknown'
    
    def _infer_program(self, location: str) -> str:
        """Infer DCGS program from location."""
        if not location:
            return 'Unknown'
            
        location_lower = str(location).lower()
        
        for loc_key, program in self.LOCATION_TO_PROGRAM.items():
            if loc_key.lower() in location_lower:
                return program
        
        return 'Unknown'
    
    def export_for_pipeline(self, df: pd.DataFrame, output_path: str) -> str:
        """Export in format compatible with existing standardization pipeline."""
        # Map to existing schema
        export_df = df.rename(columns={
            'job_url': 'url',
            'title': 'job_title',
            'company': 'company_name',
            'min_amount': 'salary_min',
            'max_amount': 'salary_max',
            'date_posted': 'posted_date'
        })
        
        # Select relevant columns
        cols = ['url', 'job_title', 'company_name', 'location', 'description',
                'salary_min', 'salary_max', 'posted_date', 'detected_clearance',
                'inferred_program', 'bd_relevance_score', 'is_competitor', 
                'search_keyword', 'scraped_at']
        
        export_cols = [c for c in cols if c in export_df.columns]
        export_df = export_df[export_cols]
        
        export_df.to_csv(output_path, index=False)
        return output_path
```

#### File 2: scrapers/unified/jobspy_scheduler.py

```python
"""Scheduler for automated JobSpy scraping."""
from .jobspy_aggregator import JobSpyAggregator
import pandas as pd
from datetime import datetime
import os

def run_jobspy_pipeline() -> pd.DataFrame:
    """Run full JobSpy pipeline with BD targeting."""
    print(f"Starting JobSpy pipeline at {datetime.now()}")
    
    aggregator = JobSpyAggregator()
    
    # Scrape with expanded parameters
    df = aggregator.scrape_bd_jobs(
        results_per_site=100,
        hours_old=48
    )
    
    if df.empty:
        print("No jobs found")
        return df
    
    # Print summary stats
    print(f"\n=== JobSpy Pipeline Results ===")
    print(f"Total jobs: {len(df)}")
    print(f"High priority (score >= 70): {len(df[df['bd_relevance_score'] >= 70])}")
    print(f"By program:")
    print(df['inferred_program'].value_counts().head(10))
    print(f"By clearance:")
    print(df['detected_clearance'].value_counts())
    
    # Export for existing pipeline
    output_dir = os.path.join(os.path.dirname(__file__), '../../output')
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(output_dir, f'jobspy_scrape_{timestamp}.csv')
    aggregator.export_for_pipeline(df, output_path)
    print(f"\nExported to: {output_path}")
    
    return df

if __name__ == "__main__":
    run_jobspy_pipeline()
```

#### File 3: scrapers/unified/__init__.py

```python
from .jobspy_aggregator import JobSpyAggregator
from .jobspy_scheduler import run_jobspy_pipeline

__all__ = ['JobSpyAggregator', 'run_jobspy_pipeline']
```

### HUB INTEGRATION (Add to hub/routes/scraper_routes.py)

```python
from fastapi import APIRouter, BackgroundTasks
from scrapers.unified import JobSpyAggregator, run_jobspy_pipeline
import pandas as pd

router = APIRouter(prefix="/scrapers/jobspy", tags=["JobSpy"])

# Store last run results in memory
_last_run_results = {"df": None, "timestamp": None}

@router.post("/run")
async def trigger_jobspy_scrape(background_tasks: BackgroundTasks):
    """Trigger manual JobSpy scrape."""
    background_tasks.add_task(_run_and_store)
    return {"status": "started", "message": "JobSpy scrape initiated in background"}

def _run_and_store():
    global _last_run_results
    from datetime import datetime
    df = run_jobspy_pipeline()
    _last_run_results = {"df": df, "timestamp": datetime.now().isoformat()}

@router.get("/status")
async def get_jobspy_status():
    """Get last run status."""
    if _last_run_results["df"] is None:
        return {"status": "no_runs", "last_run": None}
    
    df = _last_run_results["df"]
    return {
        "status": "completed",
        "last_run": _last_run_results["timestamp"],
        "total_jobs": len(df),
        "high_priority_count": len(df[df['bd_relevance_score'] >= 70]) if not df.empty else 0
    }

@router.get("/results")
async def get_jobspy_results(min_score: int = 0, limit: int = 100):
    """Get high-relevance jobs."""
    if _last_run_results["df"] is None:
        return {"jobs": [], "message": "No scrape results available"}
    
    df = _last_run_results["df"]
    filtered = df[df['bd_relevance_score'] >= min_score].head(limit)
    return {"jobs": filtered.to_dict(orient='records'), "total": len(filtered)}
```

### SUCCESS CRITERIA
1. [ ] JobSpy installed: `pip show python-jobspy`
2. [ ] Can scrape from multiple boards: `python -c "from scrapers.unified import JobSpyAggregator; print('OK')"`
3. [ ] BD relevance scoring working (0-100)
4. [ ] Clearance extraction accurate
5. [ ] Program inference by location working
6. [ ] Output compatible with existing standardization pipeline
7. [ ] Hub API endpoints functional: GET /scrapers/jobspy/status
```

---

# PROMPT 2: FPDS PYTHON PARSER
## Target: data-scraper (Terminal 2-1)

### Copy This Prompt:

```
## ENHANCEMENT: FPDS Python Parser Integration

### OBJECTIVE
Integrate FPDS Python Parser (https://github.com/dherincx92/fpds) to solve the FPDS ATOM feed pagination problem (10 record limit) with auto-pagination and XML→JSON conversion.

### CONTEXT
- Official FPDS ATOM feed limits responses to 10 records per request
- This library auto-paginates to retrieve ALL matching records
- Converts XML responses to Python objects
- Critical for comprehensive DCGS contract award tracking
- Must integrate with Federal Programs database (Collection ID: 06cd9b22-5d6b-4d37-b0d3-ba99da4971fa)

### INSTALLATION
pip install fpds pandas

### IMPLEMENTATION REQUIREMENTS

Create file: external_apis/fpds_enhanced.py

```python
"""Enhanced FPDS client with auto-pagination for BD intelligence."""
from fpds import fpdsRequest
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd

class EnhancedFPDSClient:
    """FPDS client with BD-specific queries and auto-pagination."""
    
    # DCGS-relevant NAICS codes
    DCGS_NAICS: List[str] = [
        '541511',  # Custom Computer Programming
        '541512',  # Computer Systems Design
        '541519',  # Other Computer Services
        '541330',  # Engineering Services
        '541690',  # Other Scientific/Technical Services
    ]
    
    # Target DoD/IC agencies
    TARGET_AGENCIES: List[str] = [
        'DEPARTMENT OF DEFENSE',
        'DEPT OF THE AIR FORCE',
        'DEPT OF THE ARMY', 
        'DEPT OF THE NAVY',
        'DEFENSE INFORMATION SYSTEMS AGENCY',
        'DEFENSE INTELLIGENCE AGENCY',
        'NATIONAL SECURITY AGENCY'
    ]
    
    # Competitors to track
    COMPETITORS: List[str] = [
        'GENERAL DYNAMICS',
        'LEIDOS',
        'SAIC',
        'CACI',
        'PERATON',
        'BAE SYSTEMS',
        'NORTHROP GRUMMAN',
        'RAYTHEON',
        'BOOZ ALLEN',
        'MANTECH'
    ]
    
    def __init__(self):
        pass
        
    def search_contracts(
        self,
        naics_codes: List[str] = None,
        agency: str = None,
        vendor_name: str = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Search FPDS contracts with auto-pagination.
        
        Args:
            naics_codes: List of NAICS codes (defaults to DCGS_NAICS)
            agency: Filter by contracting agency
            vendor_name: Filter by vendor name (partial match)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            keyword: Search keyword in description
            limit: Maximum records to return
        """
        naics_codes = naics_codes or self.DCGS_NAICS
        all_records = []
        
        for naics in naics_codes:
            try:
                # Build FPDS request
                request = fpdsRequest(
                    NAICS_code=naics,
                    agency_name=agency,
                    date_signed_from=date_from,
                    date_signed_to=date_to
                )
                
                # fpds library handles pagination automatically
                records = list(request)
                
                for record in records:
                    parsed = self._parse_record(record)
                    
                    # Apply vendor filter if specified
                    if vendor_name:
                        if vendor_name.upper() not in str(parsed.get('vendor_name', '')).upper():
                            continue
                    
                    # Apply keyword filter if specified
                    if keyword:
                        desc = str(parsed.get('description', '')).upper()
                        if keyword.upper() not in desc:
                            continue
                    
                    all_records.append(parsed)
                    
                    if len(all_records) >= limit:
                        break
                        
            except Exception as e:
                print(f"Error fetching NAICS {naics}: {e}")
                continue
                
            if len(all_records) >= limit:
                break
        
        return all_records[:limit]
    
    def _parse_record(self, record) -> Dict:
        """Parse FPDS record to dict."""
        return {
            'piid': getattr(record, 'piid', None),
            'contract_id': getattr(record, 'idvPIID', None) or getattr(record, 'piid', None),
            'award_id': getattr(record, 'awardID', None),
            'vendor_name': getattr(record, 'vendorName', None),
            'vendor_duns': getattr(record, 'vendorDUNSNumber', None),
            'vendor_uei': getattr(record, 'entityIdentifier', None),
            'contracting_agency': getattr(record, 'contractingOfficeAgencyID', None),
            'funding_agency': getattr(record, 'fundingRequestingAgencyID', None),
            'naics_code': getattr(record, 'principalNAICSCode', None),
            'psc_code': getattr(record, 'productOrServiceCode', None),
            'base_and_all_options_value': getattr(record, 'baseAndAllOptionsValue', None),
            'action_obligation': getattr(record, 'obligatedAmount', None),
            'date_signed': getattr(record, 'signedDate', None),
            'pop_start': getattr(record, 'effectiveDate', None),
            'pop_end': getattr(record, 'ultimateCompletionDate', None),
            'pop_city': getattr(record, 'placeOfPerformanceCity', None),
            'pop_state': getattr(record, 'placeOfPerformanceState', None),
            'description': getattr(record, 'descriptionOfContractRequirement', None),
            'set_aside': getattr(record, 'typeOfSetAside', None),
            'competition_type': getattr(record, 'extentCompeted', None),
        }
    
    def get_competitor_awards(
        self,
        competitor_names: List[str] = None,
        days_back: int = 365
    ) -> Dict[str, List[Dict]]:
        """Get recent awards to competitors."""
        competitors = competitor_names or self.COMPETITORS
        date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        results = {}
        
        for competitor in competitors:
            try:
                awards = self.search_contracts(
                    vendor_name=competitor,
                    date_from=date_from,
                    limit=100
                )
                results[competitor] = awards
                print(f"{competitor}: {len(awards)} awards in last {days_back} days")
            except Exception as e:
                print(f"Error fetching {competitor}: {e}")
                results[competitor] = []
        
        return results
    
    def get_dcgs_related_contracts(self) -> List[Dict]:
        """Get DCGS-related contracts by keyword search."""
        keywords = ['DCGS', 'Distributed Common Ground', 'ISR', 'DGS-1']
        all_contracts = []
        seen_ids = set()
        
        for keyword in keywords:
            contracts = self.search_contracts(keyword=keyword, limit=200)
            for contract in contracts:
                # Deduplicate
                contract_id = contract.get('piid') or contract.get('contract_id')
                if contract_id and contract_id not in seen_ids:
                    seen_ids.add(contract_id)
                    all_contracts.append(contract)
        
        return all_contracts
    
    def export_to_csv(self, contracts: List[Dict], output_path: str) -> str:
        """Export contracts to CSV."""
        df = pd.DataFrame(contracts)
        df.to_csv(output_path, index=False)
        return output_path


async def sync_fpds_to_notion():
    """Sync FPDS data for BD intelligence."""
    client = EnhancedFPDSClient()
    
    # Get DCGS contracts
    dcgs_contracts = client.get_dcgs_related_contracts()
    print(f"Found {len(dcgs_contracts)} DCGS-related contracts")
    
    # Get competitor awards (180 days)
    competitor_awards = client.get_competitor_awards(days_back=180)
    
    # Export
    client.export_to_csv(dcgs_contracts, 'data/fpds_dcgs_contracts.csv')
    
    return {
        'dcgs_contracts': dcgs_contracts,
        'competitor_awards': competitor_awards
    }
```

### HUB INTEGRATION (Add to hub/routes/federal_routes.py)

```python
from fastapi import APIRouter
from external_apis.fpds_enhanced import EnhancedFPDSClient, sync_fpds_to_notion

router = APIRouter(prefix="/fpds", tags=["FPDS"])

@router.get("/search")
async def search_fpds_contracts(
    naics: str = None,
    agency: str = None,
    vendor: str = None,
    keyword: str = None,
    days_back: int = 365,
    limit: int = 100
):
    """Search FPDS contracts."""
    client = EnhancedFPDSClient()
    
    from datetime import datetime, timedelta
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    naics_list = naics.split(',') if naics else None
    
    contracts = client.search_contracts(
        naics_codes=naics_list,
        agency=agency,
        vendor_name=vendor,
        keyword=keyword,
        date_from=date_from,
        limit=limit
    )
    
    return {"contracts": contracts, "total": len(contracts)}

@router.get("/dcgs")
async def get_dcgs_contracts():
    """Get DCGS-related contracts."""
    client = EnhancedFPDSClient()
    contracts = client.get_dcgs_related_contracts()
    return {"contracts": contracts, "total": len(contracts)}

@router.get("/competitors")
async def get_competitor_awards(days: int = 180):
    """Get competitor awards."""
    client = EnhancedFPDSClient()
    awards = client.get_competitor_awards(days_back=days)
    
    summary = {name: len(contracts) for name, contracts in awards.items()}
    return {"summary": summary, "awards": awards}

@router.post("/sync")
async def sync_fpds_data():
    """Sync FPDS data to local storage."""
    result = await sync_fpds_to_notion()
    return {
        "dcgs_contracts_count": len(result['dcgs_contracts']),
        "competitors_synced": list(result['competitor_awards'].keys())
    }
```

### SUCCESS CRITERIA
1. [ ] fpds package installed: `pip show fpds`
2. [ ] Auto-pagination working (returns >10 records)
3. [ ] DCGS keyword search functional
4. [ ] Competitor award tracking working
5. [ ] Exported CSV for analysis
6. [ ] Hub API endpoints functional
```

---

# PROMPT 3: GOVCON API INTEGRATION
## Target: data-scraper (Terminal 2-1)

### Copy This Prompt:

```
## ENHANCEMENT: GovCon API for SAM.gov

### OBJECTIVE
Integrate GovCon API (https://govconapi.com) as a clean JSON layer over SAM.gov with standardized agency name crosswalks and SDVOSB opportunity filtering.

### CONTEXT
- GovCon API provides clean JSON access to 51,000+ SAM.gov opportunities
- Standardized agency names (no inconsistent formatting)
- Free tier: 100 requests/month, Paid: $49/mo unlimited
- Critical for SDVOSB set-aside opportunity discovery (PTS is SDVOSB)

### API SETUP
1. Sign up at https://govconapi.com
2. Get API key from dashboard
3. Add to .env: GOVCON_API_KEY=your_key

### IMPLEMENTATION REQUIREMENTS

Create file: external_apis/govcon_api.py

```python
"""GovCon API client for SAM.gov opportunities."""
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os

class GovConAPIClient:
    """Clean JSON interface to SAM.gov via GovCon API."""
    
    BASE_URL = "https://api.govconapi.com/v1"
    
    # SDVOSB set-aside codes (PTS eligibility)
    SDVOSB_SET_ASIDES: List[str] = [
        'SDVOSBC',  # SDVOSB Sole Source
        'SDVOSBS',  # SDVOSB Set-Aside
        'VSA',      # Veteran Set-Aside
        'VSS',      # Veteran Sole Source
    ]
    
    # Target NAICS for IT services
    TARGET_NAICS: List[str] = [
        '541511',  # Custom Computer Programming
        '541512',  # Computer Systems Design
        '541519',  # Other Computer Services
        '541330',  # Engineering Services
    ]
    
    # Target DoD agencies
    TARGET_AGENCIES: List[str] = [
        'DEPT OF THE AIR FORCE',
        'DEPT OF THE ARMY',
        'DEPT OF THE NAVY',
        'DEFENSE INFORMATION SYSTEMS AGENCY',
        'DEFENSE INTELLIGENCE AGENCY',
    ]
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GOVCON_API_KEY')
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={'Authorization': f'Bearer {self.api_key}'} if self.api_key else {},
            timeout=30.0
        )
    
    async def search_opportunities(
        self,
        keywords: List[str] = None,
        naics_codes: List[str] = None,
        set_asides: List[str] = None,
        agencies: List[str] = None,
        posted_from: str = None,
        posted_to: str = None,
        response_deadline_from: str = None,
        active_only: bool = True,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search SAM.gov opportunities.
        
        Args:
            keywords: Search terms
            naics_codes: Filter by NAICS
            set_asides: Filter by set-aside type
            agencies: Filter by agency name
            posted_from: Posted date start (YYYY-MM-DD)
            posted_to: Posted date end
            response_deadline_from: Response deadline start
            active_only: Only active opportunities
            limit: Max results
        """
        params = {
            'limit': limit,
            'active': active_only
        }
        
        if keywords:
            params['q'] = ' '.join(keywords)
        if naics_codes:
            params['naics'] = ','.join(naics_codes)
        if set_asides:
            params['setAside'] = ','.join(set_asides)
        if agencies:
            params['agency'] = ','.join(agencies)
        if posted_from:
            params['postedFrom'] = posted_from
        if posted_to:
            params['postedTo'] = posted_to
        if response_deadline_from:
            params['responseDeadlineFrom'] = response_deadline_from
        
        response = await self.client.get('/opportunities', params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get('opportunities', [])
    
    async def get_sdvosb_opportunities(
        self,
        keywords: List[str] = None,
        days_ahead: int = 30
    ) -> List[Dict]:
        """Get SDVOSB set-aside opportunities (PTS eligible)."""
        keywords = keywords or ['IT', 'engineering', 'intelligence', 'cyber', 'network']
        
        deadline_from = datetime.now().strftime('%Y-%m-%d')
        
        opportunities = await self.search_opportunities(
            keywords=keywords,
            naics_codes=self.TARGET_NAICS,
            set_asides=self.SDVOSB_SET_ASIDES,
            response_deadline_from=deadline_from,
            limit=200
        )
        
        # Score each opportunity
        scored = []
        for opp in opportunities:
            opp['pts_fit_score'] = self.score_opportunity_for_pts(opp)
            scored.append(opp)
        
        # Sort by PTS fit score
        scored.sort(key=lambda x: x['pts_fit_score'], reverse=True)
        
        return scored
    
    async def get_dcgs_opportunities(self) -> List[Dict]:
        """Get DCGS-related opportunities."""
        keywords = [
            'DCGS', 'Distributed Common Ground', 'ISR',
            'intelligence surveillance reconnaissance', 'DGS-1',
            'DCGS-A', 'DCGS-N'
        ]
        
        opportunities = await self.search_opportunities(
            keywords=keywords,
            agencies=self.TARGET_AGENCIES,
            naics_codes=self.TARGET_NAICS,
            limit=100
        )
        
        # Score each
        for opp in opportunities:
            opp['pts_fit_score'] = self.score_opportunity_for_pts(opp)
        
        return sorted(opportunities, key=lambda x: x['pts_fit_score'], reverse=True)
    
    def score_opportunity_for_pts(self, opp: Dict) -> int:
        """Calculate PTS fit score (0-100)."""
        score = 0
        
        # SDVOSB set-aside: +35
        set_aside = opp.get('setAside', '')
        if any(sa in set_aside for sa in self.SDVOSB_SET_ASIDES):
            score += 35
        
        # Target NAICS: +20
        naics = opp.get('naicsCode', '')
        if naics in self.TARGET_NAICS:
            score += 20
        
        # DoD agency: +15
        agency = opp.get('agency', '')
        if any(a.lower() in agency.lower() for a in self.TARGET_AGENCIES):
            score += 15
        
        # DCGS keywords: +20
        title = opp.get('title', '').lower()
        desc = opp.get('description', '').lower()
        dcgs_keywords = ['dcgs', 'isr', 'intelligence', 'surveillance']
        if any(kw in title or kw in desc for kw in dcgs_keywords):
            score += 20
        
        # Clearance requirement: +10
        if 'clearance' in desc or 'ts/sci' in desc or 'secret' in desc:
            score += 10
        
        return min(score, 100)
    
    async def close(self):
        await self.client.aclose()


async def daily_opportunity_scan():
    """Run daily opportunity scan for BD pipeline."""
    client = GovConAPIClient()
    
    try:
        # Get SDVOSB opportunities
        sdvosb = await client.get_sdvosb_opportunities()
        print(f"SDVOSB opportunities: {len(sdvosb)}")
        
        # Get DCGS opportunities
        dcgs = await client.get_dcgs_opportunities()
        print(f"DCGS opportunities: {len(dcgs)}")
        
        # Combine and dedupe
        seen_ids = set()
        all_opps = []
        
        for opp in sdvosb + dcgs:
            opp_id = opp.get('noticeId') or opp.get('solicitationNumber')
            if opp_id and opp_id not in seen_ids:
                seen_ids.add(opp_id)
                all_opps.append(opp)
        
        # Filter high priority
        high_priority = [o for o in all_opps if o.get('pts_fit_score', 0) >= 70]
        
        print(f"\n=== Daily Opportunity Scan ===")
        print(f"Total unique: {len(all_opps)}")
        print(f"High priority (>=70): {len(high_priority)}")
        
        return {
            'all_opportunities': all_opps,
            'high_priority': high_priority,
            'sdvosb_count': len(sdvosb),
            'dcgs_count': len(dcgs)
        }
        
    finally:
        await client.close()
```

### HUB INTEGRATION (Add to hub/routes/federal_routes.py)

```python
from external_apis.govcon_api import GovConAPIClient, daily_opportunity_scan

@router.get("/govcon/opportunities")
async def search_govcon_opportunities(
    keywords: str = None,
    naics: str = None,
    set_aside: str = None,
    agency: str = None,
    limit: int = 50
):
    """Search GovCon API opportunities."""
    client = GovConAPIClient()
    
    try:
        opps = await client.search_opportunities(
            keywords=keywords.split(',') if keywords else None,
            naics_codes=naics.split(',') if naics else None,
            set_asides=set_aside.split(',') if set_aside else None,
            agencies=agency.split(',') if agency else None,
            limit=limit
        )
        return {"opportunities": opps, "total": len(opps)}
    finally:
        await client.close()

@router.get("/govcon/sdvosb")
async def get_sdvosb_opportunities():
    """Get SDVOSB opportunities (PTS eligible)."""
    client = GovConAPIClient()
    try:
        opps = await client.get_sdvosb_opportunities()
        return {"opportunities": opps, "total": len(opps)}
    finally:
        await client.close()

@router.get("/govcon/dcgs")
async def get_dcgs_opportunities():
    """Get DCGS-related opportunities."""
    client = GovConAPIClient()
    try:
        opps = await client.get_dcgs_opportunities()
        return {"opportunities": opps, "total": len(opps)}
    finally:
        await client.close()

@router.post("/govcon/daily-scan")
async def run_daily_opportunity_scan():
    """Run daily opportunity scan."""
    result = await daily_opportunity_scan()
    return {
        "total": len(result['all_opportunities']),
        "high_priority": len(result['high_priority']),
        "sdvosb_count": result['sdvosb_count'],
        "dcgs_count": result['dcgs_count']
    }
```

### SUCCESS CRITERIA
1. [ ] GovCon API key configured
2. [ ] SDVOSB filtering working
3. [ ] DCGS keyword search working
4. [ ] PTS fit scoring accurate (0-100)
5. [ ] Agency name standardization working
6. [ ] Hub API endpoints functional
```

---

# PROMPT 4: REACHER EMAIL VERIFICATION
## Target: bd-automation-engine (Terminal 1-1)

### Copy This Prompt:

```
## ENHANCEMENT: Reacher Self-Hosted Email Verification

### OBJECTIVE
Deploy Reacher (https://github.com/reacherhq/check-if-email-exists) for self-hosted email verification, eliminating Hunter.io costs for high-volume BD outreach.

### CONTEXT
- Reacher is a Rust-based email verification tool (7,400+ stars)
- Self-hosted via Docker at zero marginal cost per email
- SMTP verification without sending emails
- Detects catch-all domains, disposable emails, role accounts
- Must integrate with DCGS Contacts Full database (Collection ID: 2ccdef65-baa5-8087-a53b-000ba596128e)

### DOCKER SETUP (Run First)
```bash
docker run -d \
  --name reacher \
  -p 8080:8080 \
  -e RCH_BACKEND_NAME=PTS_BD_Verifier \
  -e RCH_SMTP_TIMEOUT=45s \
  reacherhq/backend:latest
```

### IMPLEMENTATION REQUIREMENTS

Create file: services/email_verification/reacher_client.py

```python
"""Reacher email verification client for BD outreach."""
import httpx
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
import pandas as pd

class EmailReachability(Enum):
    """Email verification result status."""
    SAFE = "safe"
    RISKY = "risky"
    INVALID = "invalid"
    UNKNOWN = "unknown"

@dataclass
class VerificationResult:
    """Email verification result."""
    email: str
    is_reachable: EmailReachability
    is_valid_syntax: bool
    is_disposable: bool
    is_role_account: bool
    is_catch_all: bool
    mx_records: List[str]
    smtp_safe: bool
    suggestion: Optional[str] = None
    raw_response: Dict = None

class ReacherClient:
    """Client for Reacher email verification service."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        timeout: float = 60.0
    ):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def verify_email(self, email: str) -> VerificationResult:
        """
        Verify a single email address.
        
        Args:
            email: Email address to verify
            
        Returns:
            VerificationResult with detailed status
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/v0/check_email",
                json={
                    "to_email": email,
                    "from_email": "verify@primetechnical.com",
                    "hello_name": "primetechnical.com"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Parse reachability
            reachability = self._parse_reachability(data.get('is_reachable', 'unknown'))
            
            # Extract MX records
            mx_records = []
            if data.get('mx') and data['mx'].get('records'):
                mx_records = [r.get('exchange', '') for r in data['mx']['records']]
            
            # Check SMTP safety
            smtp_data = data.get('smtp', {})
            smtp_safe = smtp_data.get('can_connect_smtp', False)
            
            # Get suggestion for typos
            suggestion = None
            if data.get('suggestion'):
                suggestion = data['suggestion']
            
            return VerificationResult(
                email=email,
                is_reachable=reachability,
                is_valid_syntax=data.get('syntax', {}).get('is_valid_syntax', False),
                is_disposable=data.get('misc', {}).get('is_disposable', False),
                is_role_account=data.get('misc', {}).get('is_role_account', False),
                is_catch_all=data.get('misc', {}).get('is_catch_all', False),
                mx_records=mx_records,
                smtp_safe=smtp_safe,
                suggestion=suggestion,
                raw_response=data
            )
            
        except Exception as e:
            print(f"Error verifying {email}: {e}")
            return VerificationResult(
                email=email,
                is_reachable=EmailReachability.UNKNOWN,
                is_valid_syntax=False,
                is_disposable=False,
                is_role_account=False,
                is_catch_all=False,
                mx_records=[],
                smtp_safe=False
            )
    
    def _parse_reachability(self, value: str) -> EmailReachability:
        """Parse reachability string to enum."""
        mapping = {
            'safe': EmailReachability.SAFE,
            'risky': EmailReachability.RISKY,
            'invalid': EmailReachability.INVALID,
            'unknown': EmailReachability.UNKNOWN
        }
        return mapping.get(value.lower(), EmailReachability.UNKNOWN)
    
    async def verify_batch(
        self,
        emails: List[str],
        concurrency: int = 5
    ) -> List[VerificationResult]:
        """
        Verify multiple emails with rate limiting.
        
        Args:
            emails: List of email addresses
            concurrency: Max concurrent verifications
            
        Returns:
            List of VerificationResults
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def verify_with_limit(email: str) -> VerificationResult:
            async with semaphore:
                result = await self.verify_email(email)
                await asyncio.sleep(0.5)  # Rate limit
                return result
        
        tasks = [verify_with_limit(email) for email in emails]
        return await asyncio.gather(*tasks)
    
    async def verify_contacts_dataframe(
        self,
        df: pd.DataFrame,
        email_column: str = 'Email Address'
    ) -> pd.DataFrame:
        """
        Verify all emails in a DataFrame.
        
        Args:
            df: DataFrame with email column
            email_column: Name of email column
            
        Returns:
            DataFrame with verification columns added
        """
        # Get unique emails
        emails = df[email_column].dropna().unique().tolist()
        print(f"Verifying {len(emails)} unique emails...")
        
        # Verify in batches
        results = await self.verify_batch(emails)
        
        # Create lookup dict
        verification_map = {r.email: r for r in results}
        
        # Add columns
        df['email_verified'] = df[email_column].apply(
            lambda e: verification_map.get(e, VerificationResult(
                email=e, is_reachable=EmailReachability.UNKNOWN,
                is_valid_syntax=False, is_disposable=False,
                is_role_account=False, is_catch_all=False,
                mx_records=[], smtp_safe=False
            )).is_reachable.value if pd.notna(e) else 'missing'
        )
        
        df['email_safe_to_send'] = df[email_column].apply(
            lambda e: verification_map.get(e, VerificationResult(
                email=e, is_reachable=EmailReachability.UNKNOWN,
                is_valid_syntax=False, is_disposable=False,
                is_role_account=False, is_catch_all=False,
                mx_records=[], smtp_safe=False
            )).is_reachable == EmailReachability.SAFE if pd.notna(e) else False
        )
        
        return df
    
    async def close(self):
        await self.client.aclose()


async def verify_bd_contacts():
    """Verify emails in DCGS contact database."""
    import os
    
    # Load contacts
    csv_path = '/mnt/project/DCGS_Contact_Spreadsheet__391_120925_PERSON.csv'
    if not os.path.exists(csv_path):
        print(f"CSV not found at {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} contacts")
    
    # Verify
    client = ReacherClient()
    try:
        df = await client.verify_contacts_dataframe(df)
        
        # Stats
        safe_count = len(df[df['email_safe_to_send'] == True])
        print(f"\n=== Email Verification Results ===")
        print(f"Total contacts: {len(df)}")
        print(f"Safe to send: {safe_count}")
        print(f"Verification breakdown:")
        print(df['email_verified'].value_counts())
        
        # Export verified
        output_path = 'data/verified_contacts.csv'
        df.to_csv(output_path, index=False)
        print(f"\nExported to: {output_path}")
        
        return df
        
    finally:
        await client.close()
```

### HUB INTEGRATION (Add to hub/routes/email_routes.py)

```python
from fastapi import APIRouter, UploadFile, File
from services.email_verification.reacher_client import ReacherClient, verify_bd_contacts
import pandas as pd
import io

router = APIRouter(prefix="/email", tags=["Email Verification"])

@router.get("/health")
async def check_reacher_health():
    """Check Reacher container status."""
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8080/")
            return {"status": "healthy", "reacher_version": response.text[:100]}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@router.post("/verify")
async def verify_single_email(email: str):
    """Verify single email."""
    client = ReacherClient()
    try:
        result = await client.verify_email(email)
        return {
            "email": result.email,
            "is_reachable": result.is_reachable.value,
            "is_valid_syntax": result.is_valid_syntax,
            "is_disposable": result.is_disposable,
            "is_role_account": result.is_role_account,
            "is_catch_all": result.is_catch_all,
            "smtp_safe": result.smtp_safe,
            "suggestion": result.suggestion
        }
    finally:
        await client.close()

@router.post("/verify-batch")
async def verify_batch_emails(emails: list[str]):
    """Verify list of emails."""
    client = ReacherClient()
    try:
        results = await client.verify_batch(emails)
        return {
            "results": [
                {
                    "email": r.email,
                    "is_reachable": r.is_reachable.value,
                    "safe_to_send": r.is_reachable.value == "safe"
                }
                for r in results
            ],
            "summary": {
                "total": len(results),
                "safe": len([r for r in results if r.is_reachable.value == "safe"]),
                "risky": len([r for r in results if r.is_reachable.value == "risky"]),
                "invalid": len([r for r in results if r.is_reachable.value == "invalid"])
            }
        }
    finally:
        await client.close()

@router.post("/verify-contacts")
async def verify_contact_csv(file: UploadFile = File(...)):
    """Verify emails in uploaded CSV."""
    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))
    
    client = ReacherClient()
    try:
        df = await client.verify_contacts_dataframe(df)
        
        safe_count = len(df[df['email_safe_to_send'] == True])
        
        return {
            "total_contacts": len(df),
            "safe_to_send": safe_count,
            "verification_breakdown": df['email_verified'].value_counts().to_dict()
        }
    finally:
        await client.close()
```

### SUCCESS CRITERIA
1. [ ] Reacher Docker container running: `docker ps | grep reacher`
2. [ ] Health check passing: `curl http://localhost:8080/`
3. [ ] Single email verification working
4. [ ] Batch verification with rate limiting
5. [ ] DataFrame integration working
6. [ ] Distinguishes safe/risky/invalid
7. [ ] Hub API endpoints functional
```

---

Due to length, I'll continue with remaining prompts in Part 2...

---

# PROMPT 5: LANGGRAPH RAG AGENT
## Target: bd-automation-engine (Terminal 1-1)

### Copy This Prompt:

```
## ENHANCEMENT: LangGraph RAG Agent for BD Research

### OBJECTIVE
Build a LangGraph-based RAG agent that combines your Qdrant vector store (8,447+ vectors) with structured reasoning for multi-step BD research queries.

### CONTEXT
- LangGraph enables stateful, multi-step AI workflows with cycles and branching
- Must connect to existing Qdrant collection (bd_documents)
- Enables complex queries: "Find DCGS contacts at PACAF, check for open jobs, generate outreach"
- Must integrate with existing Notion MCP for database operations

### INSTALLATION
pip install langgraph langchain-anthropic langchain-community qdrant-client

### IMPLEMENTATION REQUIREMENTS

Create folder: agents/langgraph_bd/

#### File 1: agents/langgraph_bd/state.py

```python
"""LangGraph state definitions for BD agent."""
from typing import TypedDict, List, Dict, Optional, Annotated
from langgraph.graph.message import add_messages

class BDAgentState(TypedDict):
    """State for BD research agent."""
    # Conversation history
    messages: Annotated[List, add_messages]
    
    # Research context
    query: str
    program: Optional[str]
    location: Optional[str]
    
    # Retrieved data
    contacts: List[Dict]
    jobs: List[Dict]
    programs: List[Dict]
    
    # Analysis results
    pain_points: List[str]
    opportunities: List[str]
    
    # Generated outputs
    outreach_messages: List[Dict]
    call_sheet_data: List[Dict]
    
    # Control flow
    next_action: str
    iteration_count: int
```

#### File 2: agents/langgraph_bd/nodes.py

```python
"""LangGraph nodes for BD research workflow."""
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
import os

# Initialize components
llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))

def retrieve_context(state: dict) -> dict:
    """Retrieve relevant documents from Qdrant."""
    query = state["query"]
    program = state.get("program")
    location = state.get("location")
    
    # Build search query
    search_query = query
    if program:
        search_query += f" {program}"
    if location:
        search_query += f" {location}"
    
    # Search Qdrant
    results = qdrant_client.search(
        collection_name="bd_documents",
        query_vector=get_embedding(search_query),
        limit=10
    )
    
    # Extract contacts, jobs, programs from results
    contacts = []
    jobs = []
    programs = []
    
    for result in results:
        doc_type = result.payload.get("type")
        if doc_type == "contact":
            contacts.append(result.payload)
        elif doc_type == "job":
            jobs.append(result.payload)
        elif doc_type == "program":
            programs.append(result.payload)
    
    return {
        "contacts": contacts,
        "jobs": jobs,
        "programs": programs
    }

def analyze_opportunities(state: dict) -> dict:
    """Analyze retrieved data for BD opportunities."""
    contacts = state.get("contacts", [])
    jobs = state.get("jobs", [])
    programs = state.get("programs", [])
    
    # Build analysis prompt
    prompt = f"""Analyze this BD intelligence data:

CONTACTS ({len(contacts)}):
{contacts[:5]}

JOBS ({len(jobs)}):
{jobs[:5]}

PROGRAMS ({len(programs)}):
{programs[:5]}

Identify:
1. Pain points (staffing gaps, vacancies, challenges)
2. BD opportunities (timing, approach, positioning)
3. Key contacts to prioritize

Respond in JSON format:
{{"pain_points": [...], "opportunities": [...], "priority_contacts": [...]}}
"""
    
    response = llm.invoke(prompt)
    analysis = parse_json_response(response.content)
    
    return {
        "pain_points": analysis.get("pain_points", []),
        "opportunities": analysis.get("opportunities", [])
    }

def generate_outreach(state: dict) -> dict:
    """Generate personalized outreach using BD Formula."""
    contacts = state.get("contacts", [])[:5]  # Top 5
    pain_points = state.get("pain_points", [])
    jobs = state.get("jobs", [])
    
    outreach_messages = []
    
    for contact in contacts:
        prompt = f"""Generate personalized BD outreach using the PTS 6-step formula:

CONTACT:
- Name: {contact.get('name')}
- Title: {contact.get('title')}
- Program: {contact.get('program')}
- Location: {contact.get('location')}

PAIN POINTS: {pain_points}

OPEN JOBS: {[j.get('title') for j in jobs[:3]]}

PTS PAST PERFORMANCE:
- BICES/BICES-X: TS/SCI network engineers (Norfolk, Tampa, Europe)
- GSM-O II: Network engineers for DISA operations
- SOCOM JICCENT: Joint Intelligence Center analysts

Generate a short, personalized LinkedIn message (under 300 characters).
"""
        response = llm.invoke(prompt)
        outreach_messages.append({
            "contact": contact.get("name"),
            "email": contact.get("email"),
            "message": response.content
        })
    
    return {"outreach_messages": outreach_messages}

def decide_next_action(state: dict) -> str:
    """Decide next workflow step based on state."""
    if not state.get("contacts") and not state.get("jobs"):
        return "retrieve"
    elif not state.get("pain_points"):
        return "analyze"
    elif not state.get("outreach_messages"):
        return "generate"
    else:
        return "complete"

def get_embedding(text: str) -> List[float]:
    """Get embedding for text (placeholder - use your embedding model)."""
    # In production, use your embedding model
    from langchain_community.embeddings import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return embeddings.embed_query(text)

def parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response."""
    import json
    import re
    
    # Try to extract JSON from response
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    return {}
```

#### File 3: agents/langgraph_bd/graph.py

```python
"""LangGraph workflow definition for BD agent."""
from langgraph.graph import StateGraph, END
from .state import BDAgentState
from .nodes import retrieve_context, analyze_opportunities, generate_outreach, decide_next_action

def build_bd_agent_graph():
    """Build the BD research agent graph."""
    
    # Create graph with state schema
    workflow = StateGraph(BDAgentState)
    
    # Add nodes
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("analyze", analyze_opportunities)
    workflow.add_node("generate", generate_outreach)
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "retrieve",
        lambda state: "analyze" if state.get("contacts") or state.get("jobs") else END
    )
    
    workflow.add_conditional_edges(
        "analyze",
        lambda state: "generate" if state.get("pain_points") else END
    )
    
    workflow.add_edge("generate", END)
    
    # Set entry point
    workflow.set_entry_point("retrieve")
    
    # Compile
    return workflow.compile()


class BDResearchAgent:
    """High-level interface for BD research."""
    
    def __init__(self):
        self.graph = build_bd_agent_graph()
    
    async def research(
        self,
        query: str,
        program: str = None,
        location: str = None
    ) -> dict:
        """Run BD research workflow."""
        initial_state = {
            "messages": [],
            "query": query,
            "program": program,
            "location": location,
            "contacts": [],
            "jobs": [],
            "programs": [],
            "pain_points": [],
            "opportunities": [],
            "outreach_messages": [],
            "call_sheet_data": [],
            "next_action": "retrieve",
            "iteration_count": 0
        }
        
        # Run graph
        final_state = await self.graph.ainvoke(initial_state)
        
        return {
            "contacts_found": len(final_state.get("contacts", [])),
            "jobs_found": len(final_state.get("jobs", [])),
            "pain_points": final_state.get("pain_points", []),
            "opportunities": final_state.get("opportunities", []),
            "outreach_messages": final_state.get("outreach_messages", [])
        }
```

#### File 4: agents/langgraph_bd/__init__.py

```python
from .graph import BDResearchAgent, build_bd_agent_graph
from .state import BDAgentState

__all__ = ['BDResearchAgent', 'build_bd_agent_graph', 'BDAgentState']
```

### HUB INTEGRATION (Add to hub/routes/agent_routes.py)

```python
from fastapi import APIRouter
from agents.langgraph_bd import BDResearchAgent

router = APIRouter(prefix="/agent", tags=["LangGraph Agent"])

agent = BDResearchAgent()

@router.post("/research")
async def run_bd_research(
    query: str,
    program: str = None,
    location: str = None
):
    """Run BD research workflow."""
    result = await agent.research(query, program, location)
    return result

@router.post("/research/dcgs")
async def research_dcgs_program(program: str):
    """Research specific DCGS program."""
    result = await agent.research(
        query=f"staffing opportunities pain points {program}",
        program=program
    )
    return result
```

### SUCCESS CRITERIA
1. [ ] LangGraph installed: `pip show langgraph`
2. [ ] Connects to Qdrant: `curl http://localhost:6333/collections/bd_documents`
3. [ ] Multi-step workflow executes
4. [ ] Returns contacts, pain points, outreach
5. [ ] Hub API endpoint functional
```

---

# PROMPT 6: HYBRID SEARCH ENGINE
## Target: bd-automation-engine (Terminal 1-1)

### Copy This Prompt:

```
## ENHANCEMENT: Hybrid Search (BM25 + Dense + Rerank)

### OBJECTIVE
Implement hybrid search combining BM25 sparse retrieval with dense embeddings and cross-encoder reranking for improved BD intelligence retrieval.

### CONTEXT
- Dense search alone misses keyword matches (e.g., "DCGS" acronym)
- BM25 alone misses semantic similarity (e.g., "ISR" ≈ "surveillance")
- Hybrid combines strengths of both
- Cross-encoder reranking improves final ranking quality
- Must work with existing Qdrant collection

### INSTALLATION
pip install rank-bm25 sentence-transformers qdrant-client numpy

### IMPLEMENTATION REQUIREMENTS

Create file: services/hybrid_search.py

```python
"""Hybrid search combining BM25, dense vectors, and reranking."""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import os

@dataclass
class SearchResult:
    """Search result with combined score."""
    id: str
    content: str
    metadata: Dict
    bm25_score: float
    dense_score: float
    combined_score: float
    rerank_score: Optional[float] = None

class HybridSearchEngine:
    """
    Hybrid search engine for BD intelligence.
    
    Combines:
    1. BM25 sparse retrieval (keyword matching)
    2. Dense vector search (semantic similarity)
    3. Cross-encoder reranking (final ranking)
    """
    
    def __init__(
        self,
        qdrant_url: str = None,
        collection_name: str = "bd_documents",
        embedding_model: str = "all-MiniLM-L6-v2",
        rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection_name = collection_name
        
        # Initialize clients
        self.qdrant = QdrantClient(url=self.qdrant_url)
        self.embedder = SentenceTransformer(embedding_model)
        self.reranker = CrossEncoder(rerank_model)
        
        # BM25 index (built from documents)
        self.bm25_index = None
        self.documents = []
        self.doc_ids = []
    
    def build_bm25_index(self, documents: List[Dict]):
        """Build BM25 index from documents."""
        self.documents = documents
        self.doc_ids = [doc.get("id") for doc in documents]
        
        # Tokenize for BM25
        tokenized = [doc.get("content", "").lower().split() for doc in documents]
        self.bm25_index = BM25Okapi(tokenized)
        
        print(f"Built BM25 index with {len(documents)} documents")
    
    def _bm25_search(self, query: str, top_k: int = 50) -> List[Tuple[str, float]]:
        """Search using BM25."""
        if not self.bm25_index:
            return []
        
        tokenized_query = query.lower().split()
        scores = self.bm25_index.get_scores(tokenized_query)
        
        # Get top-k
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self.doc_ids[idx], float(scores[idx])))
        
        return results
    
    def _dense_search(
        self,
        query: str,
        top_k: int = 50,
        filter_conditions: Dict = None
    ) -> List[Tuple[str, float, Dict]]:
        """Search using dense vectors in Qdrant."""
        query_vector = self.embedder.encode(query).tolist()
        
        # Build filter if provided
        qdrant_filter = None
        if filter_conditions:
            conditions = []
            for field, value in filter_conditions.items():
                conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))
            qdrant_filter = Filter(must=conditions)
        
        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=qdrant_filter
        )
        
        return [
            (str(r.id), r.score, r.payload)
            for r in results
        ]
    
    def _rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 10
    ) -> List[SearchResult]:
        """Rerank results using cross-encoder."""
        if not results:
            return []
        
        # Prepare pairs for reranking
        pairs = [(query, r.content) for r in results]
        
        # Get rerank scores
        rerank_scores = self.reranker.predict(pairs)
        
        # Update results with rerank scores
        for result, score in zip(results, rerank_scores):
            result.rerank_score = float(score)
        
        # Sort by rerank score
        results.sort(key=lambda x: x.rerank_score or 0, reverse=True)
        
        return results[:top_k]
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        use_rerank: bool = True,
        bm25_weight: float = 0.3,
        dense_weight: float = 0.7,
        filter_conditions: Dict = None
    ) -> List[SearchResult]:
        """
        Hybrid search with optional reranking.
        
        Args:
            query: Search query
            top_k: Number of results to return
            use_rerank: Whether to apply cross-encoder reranking
            bm25_weight: Weight for BM25 scores (0-1)
            dense_weight: Weight for dense scores (0-1)
            filter_conditions: Optional metadata filters
        """
        # Get candidates from both methods
        bm25_results = self._bm25_search(query, top_k=50)
        dense_results = self._dense_search(query, top_k=50, filter_conditions=filter_conditions)
        
        # Create lookup dicts
        bm25_scores = {doc_id: score for doc_id, score in bm25_results}
        dense_lookup = {doc_id: (score, payload) for doc_id, score, payload in dense_results}
        
        # Combine unique IDs
        all_ids = set(bm25_scores.keys()) | set(dense_lookup.keys())
        
        # Calculate combined scores
        combined_results = []
        for doc_id in all_ids:
            bm25_score = bm25_scores.get(doc_id, 0)
            dense_score, payload = dense_lookup.get(doc_id, (0, {}))
            
            # Normalize scores (simple min-max)
            max_bm25 = max(bm25_scores.values()) if bm25_scores else 1
            max_dense = max(s for _, s, _ in dense_results) if dense_results else 1
            
            norm_bm25 = bm25_score / max_bm25 if max_bm25 > 0 else 0
            norm_dense = dense_score / max_dense if max_dense > 0 else 0
            
            combined = (bm25_weight * norm_bm25) + (dense_weight * norm_dense)
            
            combined_results.append(SearchResult(
                id=doc_id,
                content=payload.get("content", ""),
                metadata=payload,
                bm25_score=bm25_score,
                dense_score=dense_score,
                combined_score=combined
            ))
        
        # Sort by combined score
        combined_results.sort(key=lambda x: x.combined_score, reverse=True)
        
        # Take top candidates for reranking
        candidates = combined_results[:min(30, len(combined_results))]
        
        # Rerank if requested
        if use_rerank and candidates:
            return self._rerank(query, candidates, top_k)
        
        return candidates[:top_k]
    
    def search_contacts(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search specifically for contacts."""
        return self.search(
            query=query,
            top_k=top_k,
            filter_conditions={"type": "contact"}
        )
    
    def search_jobs(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search specifically for jobs."""
        return self.search(
            query=query,
            top_k=top_k,
            filter_conditions={"type": "job"}
        )
    
    def search_programs(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search specifically for programs."""
        return self.search(
            query=query,
            top_k=top_k,
            filter_conditions={"type": "program"}
        )


# Singleton instance
_search_engine = None

def get_search_engine() -> HybridSearchEngine:
    """Get or create search engine singleton."""
    global _search_engine
    if _search_engine is None:
        _search_engine = HybridSearchEngine()
    return _search_engine
```

### HUB INTEGRATION (Add to hub/routes/search_routes.py)

```python
from fastapi import APIRouter
from services.hybrid_search import get_search_engine, SearchResult
from typing import List

router = APIRouter(prefix="/search", tags=["Hybrid Search"])

@router.post("/hybrid")
async def hybrid_search(
    query: str,
    top_k: int = 10,
    use_rerank: bool = True,
    bm25_weight: float = 0.3,
    dense_weight: float = 0.7
):
    """Hybrid search across all BD documents."""
    engine = get_search_engine()
    results = engine.search(
        query=query,
        top_k=top_k,
        use_rerank=use_rerank,
        bm25_weight=bm25_weight,
        dense_weight=dense_weight
    )
    return {
        "query": query,
        "results": [
            {
                "id": r.id,
                "content": r.content[:500],
                "metadata": r.metadata,
                "scores": {
                    "bm25": r.bm25_score,
                    "dense": r.dense_score,
                    "combined": r.combined_score,
                    "rerank": r.rerank_score
                }
            }
            for r in results
        ]
    }

@router.post("/contacts")
async def search_contacts(query: str, top_k: int = 10):
    """Search contacts only."""
    engine = get_search_engine()
    results = engine.search_contacts(query, top_k)
    return {"results": [r.metadata for r in results]}

@router.post("/jobs")
async def search_jobs(query: str, top_k: int = 10):
    """Search jobs only."""
    engine = get_search_engine()
    results = engine.search_jobs(query, top_k)
    return {"results": [r.metadata for r in results]}
```

### SUCCESS CRITERIA
1. [ ] BM25 index builds from documents
2. [ ] Dense search works with Qdrant
3. [ ] Combined scoring produces better results
4. [ ] Reranking improves final ranking
5. [ ] Hub API endpoints functional
```

---

# PROMPT 7: TWENTY CRM INTEGRATION
## Target: bd-automation-engine (Terminal 1-1)

### Copy This Prompt:

```
## ENHANCEMENT: Twenty CRM Integration

### OBJECTIVE
Deploy Twenty CRM (https://github.com/twentyhq/twenty) as self-hosted open-source alternative to Salesforce/HubSpot for BD pipeline management.

### CONTEXT
- Twenty is a modern open-source CRM (20k+ stars)
- Self-hosted via Docker at zero marginal cost
- Full REST API for integration with BD workflows
- Replaces spreadsheet-based pipeline tracking
- Must sync with DCGS Contacts database

### DOCKER SETUP (Run First)
```bash
# Create network
docker network create twenty-network

# Start PostgreSQL
docker run -d \
  --name twenty-db \
  --network twenty-network \
  -e POSTGRES_USER=twenty \
  -e POSTGRES_PASSWORD=twenty \
  -e POSTGRES_DB=twenty \
  postgres:15

# Start Twenty
docker run -d \
  --name twenty \
  --network twenty-network \
  -p 3000:3000 \
  -e DATABASE_URL=postgresql://twenty:twenty@twenty-db:5432/twenty \
  -e FRONT_BASE_URL=http://localhost:3000 \
  twentyhq/twenty:latest
```

### IMPLEMENTATION REQUIREMENTS

Create file: services/crm/twenty_client.py

```python
"""Twenty CRM client for BD pipeline management."""
import httpx
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import os

class PipelineStage(Enum):
    """BD pipeline stages."""
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    MEETING_SCHEDULED = "MEETING_SCHEDULED"
    PROPOSAL_SENT = "PROPOSAL_SENT"
    NEGOTIATING = "NEGOTIATING"
    WON = "WON"
    LOST = "LOST"

@dataclass
class Contact:
    """CRM contact record."""
    id: Optional[str]
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    company: str
    title: str
    linkedin_url: Optional[str]
    program: Optional[str]
    tier: Optional[str]
    bd_priority: Optional[str]
    notes: Optional[str]

@dataclass
class Opportunity:
    """CRM opportunity/deal record."""
    id: Optional[str]
    name: str
    company: str
    stage: PipelineStage
    value: float
    contact_id: Optional[str]
    program: str
    expected_close_date: Optional[str]
    notes: Optional[str]

class TwentyCRMClient:
    """Client for Twenty CRM API."""
    
    def __init__(
        self,
        base_url: str = None,
        api_key: str = None
    ):
        self.base_url = base_url or os.getenv("TWENTY_API_URL", "http://localhost:3000")
        self.api_key = api_key or os.getenv("TWENTY_API_KEY")
        
        self.client = httpx.AsyncClient(
            base_url=f"{self.base_url}/rest",
            headers={
                "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    # ==================
    # CONTACTS
    # ==================
    
    async def create_contact(self, contact: Contact) -> Dict:
        """Create a new contact."""
        payload = {
            "name": {
                "firstName": contact.first_name,
                "lastName": contact.last_name
            },
            "emails": {
                "primaryEmail": contact.email
            },
            "phones": {
                "primaryPhoneNumber": contact.phone
            },
            "company": {
                "primaryLinkLabel": contact.company
            },
            "jobTitle": contact.title,
            "linkedinLink": {
                "primaryLinkUrl": contact.linkedin_url
            }
        }
        
        response = await self.client.post("/people", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def get_contacts(self, limit: int = 100) -> List[Dict]:
        """Get all contacts."""
        response = await self.client.get(f"/people?limit={limit}")
        response.raise_for_status()
        return response.json().get("data", {}).get("people", [])
    
    async def search_contacts(self, query: str) -> List[Dict]:
        """Search contacts by name or email."""
        # Twenty uses GraphQL for search, simplified here
        contacts = await self.get_contacts(limit=500)
        
        query_lower = query.lower()
        results = []
        
        for contact in contacts:
            name = contact.get("name", {})
            full_name = f"{name.get('firstName', '')} {name.get('lastName', '')}".lower()
            email = contact.get("emails", {}).get("primaryEmail", "").lower()
            
            if query_lower in full_name or query_lower in email:
                results.append(contact)
        
        return results
    
    async def update_contact(self, contact_id: str, updates: Dict) -> Dict:
        """Update a contact."""
        response = await self.client.patch(f"/people/{contact_id}", json=updates)
        response.raise_for_status()
        return response.json()
    
    # ==================
    # OPPORTUNITIES
    # ==================
    
    async def create_opportunity(self, opp: Opportunity) -> Dict:
        """Create a new opportunity."""
        payload = {
            "name": opp.name,
            "amount": {
                "amountMicros": int(opp.value * 1_000_000)
            },
            "stage": opp.stage.value,
            "closeDate": opp.expected_close_date,
            "companyId": None,  # Link after creation
            "pointOfContactId": opp.contact_id
        }
        
        response = await self.client.post("/opportunities", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def get_opportunities(self, stage: PipelineStage = None) -> List[Dict]:
        """Get opportunities, optionally filtered by stage."""
        params = {"limit": 100}
        if stage:
            params["filter"] = f"stage[eq]={stage.value}"
        
        response = await self.client.get("/opportunities", params=params)
        response.raise_for_status()
        return response.json().get("data", {}).get("opportunities", [])
    
    async def update_opportunity_stage(
        self,
        opp_id: str,
        new_stage: PipelineStage
    ) -> Dict:
        """Move opportunity to new stage."""
        response = await self.client.patch(
            f"/opportunities/{opp_id}",
            json={"stage": new_stage.value}
        )
        response.raise_for_status()
        return response.json()
    
    # ==================
    # ACTIVITIES
    # ==================
    
    async def log_activity(
        self,
        contact_id: str,
        activity_type: str,  # 'call', 'email', 'meeting', 'note'
        title: str,
        body: str
    ) -> Dict:
        """Log an activity for a contact."""
        payload = {
            "type": activity_type.upper(),
            "title": title,
            "body": body,
            "personId": contact_id
        }
        
        response = await self.client.post("/activities", json=payload)
        response.raise_for_status()
        return response.json()
    
    # ==================
    # SYNC WITH NOTION
    # ==================
    
    async def sync_from_notion_contacts(self, notion_contacts: List[Dict]) -> Dict:
        """Sync contacts from Notion DCGS database."""
        created = 0
        updated = 0
        errors = []
        
        for nc in notion_contacts:
            try:
                # Check if exists by email
                email = nc.get("Email Address", "")
                if not email:
                    continue
                
                existing = await self.search_contacts(email)
                
                contact = Contact(
                    id=None,
                    first_name=nc.get("First Name", ""),
                    last_name=nc.get("Last Name", ""),
                    email=email,
                    phone=nc.get("Phone Number"),
                    company="GDIT",
                    title=nc.get("Job Title", ""),
                    linkedin_url=nc.get("LinkedIn Contact Profile URL"),
                    program=nc.get("Program"),
                    tier=nc.get("Hierarchy Tier"),
                    bd_priority=nc.get("BD Priority"),
                    notes=None
                )
                
                if existing:
                    # Update existing
                    await self.update_contact(existing[0]["id"], {
                        "jobTitle": contact.title,
                        "phones": {"primaryPhoneNumber": contact.phone}
                    })
                    updated += 1
                else:
                    # Create new
                    await self.create_contact(contact)
                    created += 1
                    
            except Exception as e:
                errors.append({"contact": nc.get("Email Address"), "error": str(e)})
        
        return {
            "created": created,
            "updated": updated,
            "errors": errors
        }
    
    async def close(self):
        await self.client.aclose()
```

### HUB INTEGRATION (Add to hub/routes/crm_routes.py)

```python
from fastapi import APIRouter
from services.crm.twenty_client import TwentyCRMClient, Contact, Opportunity, PipelineStage

router = APIRouter(prefix="/crm", tags=["Twenty CRM"])

@router.get("/health")
async def check_crm_health():
    """Check Twenty CRM status."""
    client = TwentyCRMClient()
    try:
        contacts = await client.get_contacts(limit=1)
        return {"status": "healthy", "connection": "ok"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
    finally:
        await client.close()

@router.get("/contacts")
async def get_crm_contacts(limit: int = 100):
    """Get CRM contacts."""
    client = TwentyCRMClient()
    try:
        contacts = await client.get_contacts(limit)
        return {"contacts": contacts, "total": len(contacts)}
    finally:
        await client.close()

@router.post("/contacts")
async def create_crm_contact(
    first_name: str,
    last_name: str,
    email: str,
    title: str,
    company: str = "GDIT",
    phone: str = None
):
    """Create CRM contact."""
    client = TwentyCRMClient()
    try:
        contact = Contact(
            id=None,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            company=company,
            title=title,
            linkedin_url=None,
            program=None,
            tier=None,
            bd_priority=None,
            notes=None
        )
        result = await client.create_contact(contact)
        return result
    finally:
        await client.close()

@router.get("/opportunities")
async def get_opportunities(stage: str = None):
    """Get opportunities by stage."""
    client = TwentyCRMClient()
    try:
        stage_enum = PipelineStage[stage.upper()] if stage else None
        opps = await client.get_opportunities(stage_enum)
        return {"opportunities": opps, "total": len(opps)}
    finally:
        await client.close()

@router.post("/sync/notion")
async def sync_notion_to_crm():
    """Sync DCGS contacts from Notion to CRM."""
    # This would read from Notion and sync to Twenty
    # Placeholder - integrate with your Notion MCP
    return {"status": "not_implemented", "message": "Connect Notion MCP to complete"}
```

### SUCCESS CRITERIA
1. [ ] Twenty Docker containers running
2. [ ] API accessible: `curl http://localhost:3000/rest/people`
3. [ ] Can create/read contacts
4. [ ] Can create/track opportunities
5. [ ] Activity logging works
6. [ ] Hub API endpoints functional
```

---

# PROMPT 8: REAGRAPH NETWORK VISUALIZATION
## Target: bd-automation-engine (Terminal 1-1)

### Copy This Prompt:

```
## ENHANCEMENT: Reagraph Network Visualization

### OBJECTIVE
Integrate Reagraph (https://github.com/reaviz/reagraph) for interactive 3D network visualization of GDIT org structure, contact relationships, and program connections.

### CONTEXT
- Reagraph is a React library for large-scale graph visualization
- Supports 3D, clustering, and force-directed layouts
- Critical for visualizing 2,000+ DCGS contacts and relationships
- Must render org chart, program networks, and contact clusters

### INSTALLATION (Node.js project)
npm install reagraph @react-three/fiber three

### IMPLEMENTATION REQUIREMENTS

Create folder: visualization/reagraph/

#### File 1: visualization/reagraph/graph_data_builder.py

```python
"""Build graph data for Reagraph visualization."""
from typing import List, Dict, Set
from dataclasses import dataclass
import json

@dataclass
class GraphNode:
    """Node in the graph."""
    id: str
    label: str
    node_type: str  # 'contact', 'program', 'company', 'location'
    tier: int = 0
    size: float = 1.0
    color: str = "#4A5568"
    metadata: Dict = None

@dataclass
class GraphEdge:
    """Edge connecting nodes."""
    id: str
    source: str
    target: str
    label: str = ""
    weight: float = 1.0

class GraphDataBuilder:
    """Build Reagraph-compatible graph data from BD data."""
    
    # Color mapping for node types
    NODE_COLORS = {
        "contact": {
            "Tier 1 - Executive": "#E53E3E",       # Red
            "Tier 2 - Director": "#DD6B20",        # Orange
            "Tier 3 - Program Leadership": "#D69E2E",  # Yellow
            "Tier 4 - Management": "#38A169",      # Green
            "Tier 5 - Senior IC": "#3182CE",       # Blue
            "Tier 6 - Individual Contributor": "#718096"  # Gray
        },
        "program": "#805AD5",   # Purple
        "company": "#2C5282",   # Dark blue
        "location": "#319795"   # Teal
    }
    
    # Size mapping by tier
    NODE_SIZES = {
        "Tier 1 - Executive": 3.0,
        "Tier 2 - Director": 2.5,
        "Tier 3 - Program Leadership": 2.0,
        "Tier 4 - Management": 1.5,
        "Tier 5 - Senior IC": 1.2,
        "Tier 6 - Individual Contributor": 1.0
    }
    
    def __init__(self):
        self.nodes: List[GraphNode] = []
        self.edges: List[GraphEdge] = []
        self.node_ids: Set[str] = set()
    
    def add_contact(self, contact: Dict) -> str:
        """Add a contact node."""
        node_id = f"contact_{contact.get('email', contact.get('id', ''))}"
        
        if node_id in self.node_ids:
            return node_id
        
        tier = contact.get("Hierarchy Tier", "Tier 6 - Individual Contributor")
        
        node = GraphNode(
            id=node_id,
            label=f"{contact.get('First Name', '')} {contact.get('Last Name', '')}",
            node_type="contact",
            tier=int(tier.split()[1]) if tier else 6,
            size=self.NODE_SIZES.get(tier, 1.0),
            color=self.NODE_COLORS["contact"].get(tier, "#718096"),
            metadata={
                "title": contact.get("Job Title"),
                "email": contact.get("Email Address"),
                "phone": contact.get("Phone Number"),
                "program": contact.get("Program"),
                "location": contact.get("Person City"),
                "linkedin": contact.get("LinkedIn Contact Profile URL"),
                "bd_priority": contact.get("BD Priority")
            }
        )
        
        self.nodes.append(node)
        self.node_ids.add(node_id)
        
        return node_id
    
    def add_program(self, program_name: str) -> str:
        """Add a program node."""
        node_id = f"program_{program_name.replace(' ', '_')}"
        
        if node_id in self.node_ids:
            return node_id
        
        node = GraphNode(
            id=node_id,
            label=program_name,
            node_type="program",
            size=2.5,
            color=self.NODE_COLORS["program"]
        )
        
        self.nodes.append(node)
        self.node_ids.add(node_id)
        
        return node_id
    
    def add_location(self, location: str) -> str:
        """Add a location node."""
        node_id = f"location_{location.replace(' ', '_').replace(',', '')}"
        
        if node_id in self.node_ids:
            return node_id
        
        node = GraphNode(
            id=node_id,
            label=location,
            node_type="location",
            size=2.0,
            color=self.NODE_COLORS["location"]
        )
        
        self.nodes.append(node)
        self.node_ids.add(node_id)
        
        return node_id
    
    def add_edge(self, source: str, target: str, label: str = "", weight: float = 1.0):
        """Add an edge between nodes."""
        edge_id = f"{source}_to_{target}"
        
        edge = GraphEdge(
            id=edge_id,
            source=source,
            target=target,
            label=label,
            weight=weight
        )
        
        self.edges.append(edge)
    
    def build_from_contacts(self, contacts: List[Dict]) -> Dict:
        """Build graph from contact list."""
        for contact in contacts:
            contact_id = self.add_contact(contact)
            
            # Link to program
            program = contact.get("Program")
            if program:
                program_id = self.add_program(program)
                self.add_edge(contact_id, program_id, "works_on")
            
            # Link to location
            location = contact.get("Person City")
            if location:
                location_id = self.add_location(location)
                self.add_edge(contact_id, location_id, "located_in")
        
        return self.to_reagraph_format()
    
    def build_org_chart(self, contacts: List[Dict]) -> Dict:
        """Build hierarchical org chart."""
        # Sort by tier
        sorted_contacts = sorted(contacts, key=lambda x: x.get("Hierarchy Tier", "Tier 6")[:6])
        
        # Build hierarchy
        tier_groups = {}
        for contact in sorted_contacts:
            tier = contact.get("Hierarchy Tier", "Tier 6 - Individual Contributor")
            if tier not in tier_groups:
                tier_groups[tier] = []
            tier_groups[tier].append(contact)
        
        # Add nodes and edges
        previous_tier_ids = []
        
        for tier in ["Tier 1 - Executive", "Tier 2 - Director", "Tier 3 - Program Leadership",
                     "Tier 4 - Management", "Tier 5 - Senior IC", "Tier 6 - Individual Contributor"]:
            
            current_tier_ids = []
            
            for contact in tier_groups.get(tier, []):
                contact_id = self.add_contact(contact)
                current_tier_ids.append(contact_id)
                
                # Link to previous tier (simplified hierarchy)
                if previous_tier_ids:
                    # Find closest match by program/location
                    for prev_id in previous_tier_ids[:3]:  # Limit connections
                        self.add_edge(prev_id, contact_id, "manages", weight=0.5)
            
            previous_tier_ids = current_tier_ids
        
        return self.to_reagraph_format()
    
    def to_reagraph_format(self) -> Dict:
        """Convert to Reagraph-compatible JSON."""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "fill": n.color,
                    "size": n.size,
                    "data": {
                        "type": n.node_type,
                        "tier": n.tier,
                        **(n.metadata or {})
                    }
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "label": e.label,
                    "size": e.weight
                }
                for e in self.edges
            ]
        }
    
    def export_json(self, filepath: str):
        """Export graph to JSON file."""
        data = self.to_reagraph_format()
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return filepath
```

### HUB INTEGRATION (Add to hub/routes/visualization_routes.py)

```python
from fastapi import APIRouter
from visualization.reagraph.graph_data_builder import GraphDataBuilder
import pandas as pd

router = APIRouter(prefix="/viz", tags=["Visualization"])

@router.get("/graph/contacts")
async def get_contacts_graph(program: str = None, limit: int = 200):
    """Get contact network graph."""
    # Load contacts (from CSV or Notion)
    df = pd.read_csv('/mnt/project/DCGS_Contact_Spreadsheet__391_120925_PERSON.csv')
    
    if program:
        df = df[df['Program'] == program] if 'Program' in df.columns else df
    
    contacts = df.head(limit).to_dict(orient='records')
    
    builder = GraphDataBuilder()
    graph = builder.build_from_contacts(contacts)
    
    return {
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
        "graph": graph
    }

@router.get("/graph/org-chart")
async def get_org_chart(program: str = None):
    """Get hierarchical org chart."""
    df = pd.read_csv('/mnt/project/DCGS_Contact_Spreadsheet__391_120925_PERSON.csv')
    
    if program:
        df = df[df['Program'] == program] if 'Program' in df.columns else df
    
    contacts = df.to_dict(orient='records')
    
    builder = GraphDataBuilder()
    graph = builder.build_org_chart(contacts)
    
    return graph

@router.get("/graph/programs")
async def get_programs_graph():
    """Get program relationship graph."""
    # Load program data
    df = pd.read_csv('/mnt/project/Federal_Program_Cleaned_Notion_Import.csv')
    
    builder = GraphDataBuilder()
    
    # Add programs and their relationships
    for _, row in df.iterrows():
        program_id = builder.add_program(row.get("Program Name", "Unknown"))
        
        # Link to prime
        prime = row.get("Prime Contractor")
        if prime:
            company_id = f"company_{prime.replace(' ', '_')}"
            if company_id not in builder.node_ids:
                builder.nodes.append(GraphNode(
                    id=company_id,
                    label=prime,
                    node_type="company",
                    size=3.0,
                    color="#2C5282"
                ))
                builder.node_ids.add(company_id)
            builder.add_edge(company_id, program_id, "prime_on")
    
    return builder.to_reagraph_format()
```

### SUCCESS CRITERIA
1. [ ] GraphDataBuilder creates valid Reagraph JSON
2. [ ] Contact network visualization works
3. [ ] Org chart hierarchy displays correctly
4. [ ] Program relationships visualized
5. [ ] Color coding by tier works
6. [ ] Hub API endpoints return valid graph data
```

---

# PROMPT 9: APACHE ECHARTS DASHBOARDS
## Target: bd-automation-engine (Terminal 1-1)

### Copy This Prompt:

```
## ENHANCEMENT: Apache ECharts Dashboard Components

### OBJECTIVE
Create reusable ECharts dashboard components for BD intelligence visualization: pipeline funnels, geographic maps, timeline charts, and KPI gauges.

### CONTEXT
- Apache ECharts is the most powerful charting library (58k+ stars)
- Zero vendor lock-in, works everywhere
- Need: pipeline tracking, geographic contact distribution, time-series analysis
- Must integrate with existing BD data

### INSTALLATION
npm install echarts echarts-for-react

### IMPLEMENTATION REQUIREMENTS

Create file: visualization/echarts/chart_configs.py

```python
"""ECharts configuration generators for BD dashboards."""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json

class BDChartConfigs:
    """Generate ECharts configurations for BD dashboards."""
    
    # PTS Brand Colors
    PTS_COLORS = {
        "navy": "#1e3a5f",
        "blue": "#3182ce",
        "red": "#e53e3e",
        "orange": "#dd6b20",
        "yellow": "#d69e2e",
        "green": "#38a169",
        "gray": "#718096"
    }
    
    # Tier colors for contacts
    TIER_COLORS = [
        "#E53E3E",  # Tier 1 - Red
        "#DD6B20",  # Tier 2 - Orange
        "#D69E2E",  # Tier 3 - Yellow
        "#38A169",  # Tier 4 - Green
        "#3182CE",  # Tier 5 - Blue
        "#718096"   # Tier 6 - Gray
    ]
    
    @staticmethod
    def pipeline_funnel(stages: List[Dict[str, Any]]) -> Dict:
        """
        Create pipeline funnel chart.
        
        Args:
            stages: [{"name": "New", "value": 100}, ...]
        """
        return {
            "title": {
                "text": "BD Pipeline",
                "left": "center"
            },
            "tooltip": {
                "trigger": "item",
                "formatter": "{a} <br/>{b} : {c}"
            },
            "legend": {
                "data": [s["name"] for s in stages],
                "bottom": 0
            },
            "series": [
                {
                    "name": "Pipeline Stage",
                    "type": "funnel",
                    "left": "10%",
                    "width": "80%",
                    "label": {
                        "show": True,
                        "position": "inside"
                    },
                    "labelLine": {
                        "show": True
                    },
                    "itemStyle": {
                        "borderColor": "#fff",
                        "borderWidth": 1
                    },
                    "data": stages
                }
            ]
        }
    
    @staticmethod
    def contact_tier_breakdown(tier_counts: Dict[str, int]) -> Dict:
        """
        Create pie chart of contacts by tier.
        
        Args:
            tier_counts: {"Tier 1": 10, "Tier 2": 25, ...}
        """
        data = [
            {"value": count, "name": tier}
            for tier, count in tier_counts.items()
        ]
        
        return {
            "title": {
                "text": "Contacts by Tier",
                "left": "center"
            },
            "tooltip": {
                "trigger": "item",
                "formatter": "{b}: {c} ({d}%)"
            },
            "legend": {
                "orient": "vertical",
                "left": "left"
            },
            "series": [
                {
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "avoidLabelOverlap": True,
                    "itemStyle": {
                        "borderRadius": 10,
                        "borderColor": "#fff",
                        "borderWidth": 2
                    },
                    "label": {
                        "show": True,
                        "formatter": "{b}: {c}"
                    },
                    "emphasis": {
                        "label": {
                            "show": True,
                            "fontSize": 14,
                            "fontWeight": "bold"
                        }
                    },
                    "data": data,
                    "color": BDChartConfigs.TIER_COLORS
                }
            ]
        }
    
    @staticmethod
    def program_bar_chart(programs: List[Dict[str, Any]]) -> Dict:
        """
        Create horizontal bar chart of contacts by program.
        
        Args:
            programs: [{"name": "AF DCGS - PACAF", "contacts": 45, "jobs": 12}, ...]
        """
        return {
            "title": {
                "text": "Contacts & Jobs by Program"
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "shadow"}
            },
            "legend": {
                "data": ["Contacts", "Open Jobs"]
            },
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "3%",
                "containLabel": True
            },
            "xAxis": {
                "type": "value"
            },
            "yAxis": {
                "type": "category",
                "data": [p["name"] for p in programs]
            },
            "series": [
                {
                    "name": "Contacts",
                    "type": "bar",
                    "data": [p.get("contacts", 0) for p in programs],
                    "color": BDChartConfigs.PTS_COLORS["navy"]
                },
                {
                    "name": "Open Jobs",
                    "type": "bar",
                    "data": [p.get("jobs", 0) for p in programs],
                    "color": BDChartConfigs.PTS_COLORS["orange"]
                }
            ]
        }
    
    @staticmethod
    def activity_timeline(activities: List[Dict[str, Any]]) -> Dict:
        """
        Create timeline chart of BD activities.
        
        Args:
            activities: [{"date": "2025-01-01", "calls": 5, "emails": 10, "meetings": 2}, ...]
        """
        dates = [a["date"] for a in activities]
        
        return {
            "title": {
                "text": "BD Activity Timeline"
            },
            "tooltip": {
                "trigger": "axis"
            },
            "legend": {
                "data": ["Calls", "Emails", "Meetings"]
            },
            "xAxis": {
                "type": "category",
                "boundaryGap": False,
                "data": dates
            },
            "yAxis": {
                "type": "value"
            },
            "series": [
                {
                    "name": "Calls",
                    "type": "line",
                    "data": [a.get("calls", 0) for a in activities],
                    "smooth": True,
                    "color": BDChartConfigs.PTS_COLORS["blue"]
                },
                {
                    "name": "Emails",
                    "type": "line",
                    "data": [a.get("emails", 0) for a in activities],
                    "smooth": True,
                    "color": BDChartConfigs.PTS_COLORS["green"]
                },
                {
                    "name": "Meetings",
                    "type": "line",
                    "data": [a.get("meetings", 0) for a in activities],
                    "smooth": True,
                    "color": BDChartConfigs.PTS_COLORS["orange"]
                }
            ]
        }
    
    @staticmethod
    def kpi_gauge(value: float, title: str, max_value: float = 100) -> Dict:
        """
        Create KPI gauge chart.
        
        Args:
            value: Current value
            title: Gauge title
            max_value: Maximum value for scale
        """
        return {
            "series": [
                {
                    "type": "gauge",
                    "startAngle": 180,
                    "endAngle": 0,
                    "min": 0,
                    "max": max_value,
                    "splitNumber": 5,
                    "itemStyle": {
                        "color": BDChartConfigs.PTS_COLORS["navy"]
                    },
                    "progress": {
                        "show": True,
                        "width": 18
                    },
                    "pointer": {
                        "show": False
                    },
                    "axisLine": {
                        "lineStyle": {
                            "width": 18
                        }
                    },
                    "axisTick": {
                        "show": False
                    },
                    "splitLine": {
                        "show": False
                    },
                    "axisLabel": {
                        "show": False
                    },
                    "title": {
                        "show": True,
                        "offsetCenter": [0, "30%"],
                        "fontSize": 14
                    },
                    "detail": {
                        "valueAnimation": True,
                        "offsetCenter": [0, "-10%"],
                        "fontSize": 32,
                        "fontWeight": "bold",
                        "formatter": "{value}%",
                        "color": "auto"
                    },
                    "data": [{"value": value, "name": title}]
                }
            ]
        }
    
    @staticmethod
    def location_heatmap(locations: List[Dict[str, Any]]) -> Dict:
        """
        Create US map heatmap of contact locations.
        
        Args:
            locations: [{"name": "Virginia", "value": 150}, ...]
        """
        return {
            "title": {
                "text": "Contact Distribution by State"
            },
            "tooltip": {
                "trigger": "item",
                "formatter": "{b}: {c} contacts"
            },
            "visualMap": {
                "min": 0,
                "max": max(l["value"] for l in locations) if locations else 100,
                "text": ["High", "Low"],
                "realtime": False,
                "calculable": True,
                "inRange": {
                    "color": ["#e0f3f8", "#abd9e9", "#74add1", "#4575b4", "#313695"]
                }
            },
            "series": [
                {
                    "name": "Contacts",
                    "type": "map",
                    "map": "USA",
                    "roam": True,
                    "emphasis": {
                        "label": {"show": True}
                    },
                    "data": locations
                }
            ]
        }


def generate_dashboard_json(contacts: List[Dict], jobs: List[Dict]) -> Dict:
    """Generate complete dashboard configuration."""
    configs = BDChartConfigs()
    
    # Calculate tier breakdown
    tier_counts = {}
    for contact in contacts:
        tier = contact.get("Hierarchy Tier", "Unknown")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    # Calculate program breakdown
    program_data = {}
    for contact in contacts:
        program = contact.get("Program", "Unknown")
        if program not in program_data:
            program_data[program] = {"name": program, "contacts": 0, "jobs": 0}
        program_data[program]["contacts"] += 1
    
    for job in jobs:
        program = job.get("inferred_program", "Unknown")
        if program in program_data:
            program_data[program]["jobs"] += 1
    
    # Pipeline stages (mock data - replace with actual)
    pipeline_stages = [
        {"name": "New Leads", "value": len(contacts)},
        {"name": "Contacted", "value": int(len(contacts) * 0.6)},
        {"name": "Meeting Set", "value": int(len(contacts) * 0.3)},
        {"name": "Proposal", "value": int(len(contacts) * 0.15)},
        {"name": "Won", "value": int(len(contacts) * 0.05)}
    ]
    
    return {
        "pipeline": configs.pipeline_funnel(pipeline_stages),
        "tiers": configs.contact_tier_breakdown(tier_counts),
        "programs": configs.program_bar_chart(list(program_data.values())[:10]),
        "coverage_kpi": configs.kpi_gauge(67, "Pipeline Coverage"),
        "conversion_kpi": configs.kpi_gauge(23, "Conversion Rate")
    }
```

### HUB INTEGRATION (Add to hub/routes/dashboard_routes.py)

```python
from fastapi import APIRouter
from visualization.echarts.chart_configs import BDChartConfigs, generate_dashboard_json
import pandas as pd

router = APIRouter(prefix="/dashboard", tags=["ECharts Dashboard"])

@router.get("/charts/pipeline")
async def get_pipeline_chart():
    """Get pipeline funnel chart config."""
    stages = [
        {"name": "New", "value": 150},
        {"name": "Contacted", "value": 90},
        {"name": "Meeting", "value": 45},
        {"name": "Proposal", "value": 20},
        {"name": "Won", "value": 8}
    ]
    return BDChartConfigs.pipeline_funnel(stages)

@router.get("/charts/tiers")
async def get_tier_chart():
    """Get contact tier breakdown."""
    df = pd.read_csv('/mnt/project/DCGS_Contact_Spreadsheet__391_120925_PERSON.csv')
    
    tier_counts = {}
    if 'Hierarchy Tier' in df.columns:
        tier_counts = df['Hierarchy Tier'].value_counts().to_dict()
    else:
        # Mock data
        tier_counts = {
            "Tier 1 - Executive": 15,
            "Tier 2 - Director": 42,
            "Tier 3 - Program Leadership": 78,
            "Tier 4 - Management": 156,
            "Tier 5 - Senior IC": 312,
            "Tier 6 - Individual Contributor": 595
        }
    
    return BDChartConfigs.contact_tier_breakdown(tier_counts)

@router.get("/charts/programs")
async def get_programs_chart():
    """Get programs bar chart."""
    programs = [
        {"name": "AF DCGS - PACAF", "contacts": 45, "jobs": 12},
        {"name": "AF DCGS - Langley", "contacts": 120, "jobs": 28},
        {"name": "AF DCGS - Wright-Patt", "contacts": 85, "jobs": 15},
        {"name": "Army DCGS-A", "contacts": 95, "jobs": 22},
        {"name": "Navy DCGS-N", "contacts": 65, "jobs": 8},
        {"name": "Corporate HQ", "contacts": 180, "jobs": 35}
    ]
    return BDChartConfigs.program_bar_chart(programs)

@router.get("/full")
async def get_full_dashboard():
    """Get complete dashboard configuration."""
    contacts = pd.read_csv('/mnt/project/DCGS_Contact_Spreadsheet__391_120925_PERSON.csv').to_dict('records')
    jobs = []  # Load from jobs CSV
    
    return generate_dashboard_json(contacts, jobs)
```

### SUCCESS CRITERIA
1. [ ] Chart configs generate valid ECharts JSON
2. [ ] Pipeline funnel displays correctly
3. [ ] Tier breakdown pie chart works
4. [ ] Program bar chart renders
5. [ ] KPI gauges display
6. [ ] Hub API endpoints return valid configs
```

---

# PROMPT 10: RFP RESPONSE AGENT
## Target: bd-automation-engine (Terminal 1-1)

### Copy This Prompt:

```
## ENHANCEMENT: AI-Powered RFP Response Agent

### OBJECTIVE
Build an AI agent that analyzes RFPs, extracts requirements, and generates compliant response outlines with PTS past performance alignment.

### CONTEXT
- Must parse PDF/DOCX RFPs using Stirling-PDF (from data-scraper)
- Extract requirements, evaluation criteria, compliance matrix
- Match requirements to PTS past performance database
- Generate response outlines following BD formula
- Must integrate with Federal Programs database

### INSTALLATION
pip install langchain-anthropic pydantic PyPDF2

### IMPLEMENTATION REQUIREMENTS

Create folder: agents/rfp_agent/

#### File 1: agents/rfp_agent/rfp_parser.py

```python
"""RFP document parser and requirement extractor."""
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import re

class RequirementType(Enum):
    """RFP requirement types."""
    MANDATORY = "mandatory"      # SHALL, MUST, REQUIRED
    DESIRABLE = "desirable"      # SHOULD, PREFERRED
    OPTIONAL = "optional"        # MAY, OPTIONAL
    EVALUATION = "evaluation"    # Evaluation criteria

@dataclass
class Requirement:
    """Extracted RFP requirement."""
    id: str
    text: str
    type: RequirementType
    section: str
    keywords: List[str]
    clearance_required: Optional[str] = None
    location: Optional[str] = None

@dataclass
class RFPAnalysis:
    """Complete RFP analysis result."""
    title: str
    agency: str
    naics: str
    set_aside: str
    due_date: str
    requirements: List[Requirement]
    evaluation_criteria: List[Dict]
    key_personnel: List[str]
    clearance_requirements: List[str]
    locations: List[str]

class RFPParser:
    """Parse and analyze RFP documents."""
    
    # Requirement indicator patterns
    MANDATORY_PATTERNS = [
        r'\bshall\b', r'\bmust\b', r'\brequired\b', 
        r'\bmandatory\b', r'\bwill\b.*\bprovide\b'
    ]
    
    DESIRABLE_PATTERNS = [
        r'\bshould\b', r'\bpreferred\b', r'\bdesirable\b',
        r'\bencouraged\b'
    ]
    
    OPTIONAL_PATTERNS = [
        r'\bmay\b', r'\boptional\b', r'\bcan\b'
    ]
    
    # Clearance patterns
    CLEARANCE_PATTERNS = {
        'TS/SCI with FS Poly': r'ts/sci.*full.?scope|full.?scope.*poly',
        'TS/SCI with CI Poly': r'ts/sci.*ci.?poly|ci.?poly.*ts/sci',
        'TS/SCI': r'ts/sci|top.?secret/sci',
        'Top Secret': r'top.?secret(?!/sci)',
        'Secret': r'(?<!top.)secret',
        'Public Trust': r'public.?trust',
    }
    
    def __init__(self):
        pass
    
    def parse_text(self, text: str) -> RFPAnalysis:
        """Parse RFP text and extract structure."""
        # Extract metadata
        title = self._extract_title(text)
        agency = self._extract_agency(text)
        naics = self._extract_naics(text)
        set_aside = self._extract_set_aside(text)
        due_date = self._extract_due_date(text)
        
        # Extract requirements
        requirements = self._extract_requirements(text)
        
        # Extract evaluation criteria
        evaluation_criteria = self._extract_evaluation_criteria(text)
        
        # Extract key personnel requirements
        key_personnel = self._extract_key_personnel(text)
        
        # Extract clearances
        clearance_requirements = self._extract_clearances(text)
        
        # Extract locations
        locations = self._extract_locations(text)
        
        return RFPAnalysis(
            title=title,
            agency=agency,
            naics=naics,
            set_aside=set_aside,
            due_date=due_date,
            requirements=requirements,
            evaluation_criteria=evaluation_criteria,
            key_personnel=key_personnel,
            clearance_requirements=clearance_requirements,
            locations=locations
        )
    
    def _extract_title(self, text: str) -> str:
        """Extract RFP title."""
        # Look for common title patterns
        patterns = [
            r'(?:SOLICITATION|RFP|RFQ).*?[:]\s*(.+?)(?:\n|$)',
            r'(?:TITLE|SUBJECT).*?[:]\s*(.+?)(?:\n|$)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Unknown"
    
    def _extract_agency(self, text: str) -> str:
        """Extract contracting agency."""
        agencies = [
            'Department of Defense', 'Air Force', 'Army', 'Navy',
            'DISA', 'DIA', 'NSA', 'NGA', 'CIA'
        ]
        for agency in agencies:
            if agency.lower() in text.lower():
                return agency
        return "Unknown"
    
    def _extract_naics(self, text: str) -> str:
        """Extract NAICS code."""
        match = re.search(r'NAICS.*?(\d{6})', text, re.IGNORECASE)
        return match.group(1) if match else "Unknown"
    
    def _extract_set_aside(self, text: str) -> str:
        """Extract set-aside type."""
        set_asides = {
            'SDVOSB': r'service.?disabled.*veteran',
            'WOSB': r'women.?owned',
            '8(a)': r'8\s*\(a\)',
            'HUBZone': r'hubzone',
            'Small Business': r'small.?business',
            'Full and Open': r'full.?and.?open'
        }
        for sa_type, pattern in set_asides.items():
            if re.search(pattern, text, re.IGNORECASE):
                return sa_type
        return "Full and Open"
    
    def _extract_due_date(self, text: str) -> str:
        """Extract response due date."""
        patterns = [
            r'(?:due|deadline|submit.*by).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return "Unknown"
    
    def _extract_requirements(self, text: str) -> List[Requirement]:
        """Extract all requirements from RFP."""
        requirements = []
        req_id = 0
        
        # Split into sentences
        sentences = re.split(r'[.!?]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            # Determine requirement type
            req_type = self._classify_requirement(sentence)
            if req_type:
                req_id += 1
                requirements.append(Requirement(
                    id=f"REQ-{req_id:03d}",
                    text=sentence,
                    type=req_type,
                    section=self._identify_section(sentence),
                    keywords=self._extract_keywords(sentence),
                    clearance_required=self._extract_clearance(sentence),
                    location=self._extract_location(sentence)
                ))
        
        return requirements
    
    def _classify_requirement(self, text: str) -> Optional[RequirementType]:
        """Classify requirement type based on keywords."""
        text_lower = text.lower()
        
        for pattern in self.MANDATORY_PATTERNS:
            if re.search(pattern, text_lower):
                return RequirementType.MANDATORY
        
        for pattern in self.DESIRABLE_PATTERNS:
            if re.search(pattern, text_lower):
                return RequirementType.DESIRABLE
        
        for pattern in self.OPTIONAL_PATTERNS:
            if re.search(pattern, text_lower):
                return RequirementType.OPTIONAL
        
        return None
    
    def _identify_section(self, text: str) -> str:
        """Identify which section the requirement belongs to."""
        sections = {
            'technical': ['technical', 'engineering', 'development', 'system'],
            'management': ['management', 'program', 'project', 'staffing'],
            'past_performance': ['past performance', 'experience', 'similar'],
            'pricing': ['price', 'cost', 'budget', 'financial'],
            'security': ['security', 'clearance', 'classified']
        }
        text_lower = text.lower()
        for section, keywords in sections.items():
            if any(kw in text_lower for kw in keywords):
                return section
        return 'general'
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract technical keywords from requirement."""
        technical_keywords = [
            'DCGS', 'ISR', 'SIGINT', 'GEOINT', 'cyber', 'network',
            'DevSecOps', 'cloud', 'AWS', 'Azure', 'Agile', 'ITIL',
            'TS/SCI', 'CI Poly', 'clearance', 'CONUS', 'OCONUS'
        ]
        found = []
        text_lower = text.lower()
        for kw in technical_keywords:
            if kw.lower() in text_lower:
                found.append(kw)
        return found
    
    def _extract_clearance(self, text: str) -> Optional[str]:
        """Extract clearance requirement."""
        for clearance, pattern in self.CLEARANCE_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return clearance
        return None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location requirement."""
        locations = [
            'San Diego', 'Hampton', 'Langley', 'Dayton', 'Norfolk',
            'Fort Belvoir', 'Herndon', 'Pentagon', 'OCONUS', 'CONUS'
        ]
        for loc in locations:
            if loc.lower() in text.lower():
                return loc
        return None
    
    def _extract_evaluation_criteria(self, text: str) -> List[Dict]:
        """Extract evaluation criteria."""
        criteria = []
        # Look for evaluation section
        eval_match = re.search(r'(?:evaluation|selection)\s*criteria(.*?)(?:\n\n|\Z)', 
                               text, re.IGNORECASE | re.DOTALL)
        if eval_match:
            eval_text = eval_match.group(1)
            # Extract numbered or bulleted items
            items = re.findall(r'(?:\d+\.|[•-])\s*(.+?)(?:\n|$)', eval_text)
            for i, item in enumerate(items, 1):
                criteria.append({
                    "id": i,
                    "criterion": item.strip(),
                    "weight": "TBD"
                })
        return criteria
    
    def _extract_key_personnel(self, text: str) -> List[str]:
        """Extract key personnel requirements."""
        personnel = []
        key_roles = [
            'Program Manager', 'Project Manager', 'Technical Lead',
            'Security Manager', 'Quality Manager', 'Site Lead'
        ]
        for role in key_roles:
            if role.lower() in text.lower():
                personnel.append(role)
        return personnel
    
    def _extract_clearances(self, text: str) -> List[str]:
        """Extract all clearance requirements."""
        found = []
        for clearance, pattern in self.CLEARANCE_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.append(clearance)
        return list(set(found))
    
    def _extract_locations(self, text: str) -> List[str]:
        """Extract all location requirements."""
        locations = []
        location_list = [
            'San Diego', 'Hampton', 'Langley', 'Dayton', 'Norfolk',
            'Fort Belvoir', 'Herndon', 'Wright-Patterson', 'Pentagon'
        ]
        for loc in location_list:
            if loc.lower() in text.lower():
                locations.append(loc)
        return list(set(locations))
```

#### File 2: agents/rfp_agent/response_generator.py (continues with past performance matching and response outline generation)

### HUB INTEGRATION (Add to hub/routes/rfp_routes.py)

```python
from fastapi import APIRouter, UploadFile, File
from agents.rfp_agent.rfp_parser import RFPParser
import io

router = APIRouter(prefix="/rfp", tags=["RFP Agent"])

@router.post("/analyze")
async def analyze_rfp(file: UploadFile = File(...)):
    """Analyze uploaded RFP document."""
    content = await file.read()
    
    # Extract text (simplified - use Stirling-PDF for real PDFs)
    text = content.decode('utf-8', errors='ignore')
    
    parser = RFPParser()
    analysis = parser.parse_text(text)
    
    return {
        "title": analysis.title,
        "agency": analysis.agency,
        "naics": analysis.naics,
        "set_aside": analysis.set_aside,
        "due_date": analysis.due_date,
        "requirements_count": len(analysis.requirements),
        "mandatory_count": len([r for r in analysis.requirements if r.type.value == "mandatory"]),
        "clearances": analysis.clearance_requirements,
        "locations": analysis.locations,
        "key_personnel": analysis.key_personnel,
        "requirements": [
            {"id": r.id, "type": r.type.value, "text": r.text[:200]}
            for r in analysis.requirements[:20]
        ]
    }

@router.post("/compliance-matrix")
async def generate_compliance_matrix(file: UploadFile = File(...)):
    """Generate compliance matrix from RFP."""
    content = await file.read()
    text = content.decode('utf-8', errors='ignore')
    
    parser = RFPParser()
    analysis = parser.parse_text(text)
    
    matrix = []
    for req in analysis.requirements:
        matrix.append({
            "req_id": req.id,
            "requirement": req.text[:150] + "..." if len(req.text) > 150 else req.text,
            "type": req.type.value,
            "section": req.section,
            "compliance": "TBD",
            "response_location": "Section X.X",
            "notes": ""
        })
    
    return {"compliance_matrix": matrix}
```

### SUCCESS CRITERIA
1. [ ] RFP text parsing works
2. [ ] Requirements extraction accurate
3. [ ] Clearance detection working
4. [ ] Location extraction working
5. [ ] Compliance matrix generates
6. [ ] Hub API endpoints functional
```

---

# PROMPT 11: PROXYCURL LINKEDIN ENRICHMENT
## Target: bd-automation-engine (Terminal 1-1)

### Copy This Prompt:

```
## ENHANCEMENT: Proxycurl LinkedIn Enrichment

### OBJECTIVE
Integrate Proxycurl (https://nubela.co/proxycurl) for cost-effective LinkedIn profile enrichment, replacing expensive ZoomInfo queries for contact verification.

### CONTEXT
- Proxycurl provides $0.01/profile LinkedIn data
- Enrich DCGS contacts with current job titles, company, connections
- Verify contact accuracy before outreach
- Must integrate with DCGS Contacts database

### API SETUP
1. Sign up at https://nubela.co/proxycurl
2. Get API key
3. Add to .env: PROXYCURL_API_KEY=your_key

### IMPLEMENTATION REQUIREMENTS

Create file: services/linkedin/proxycurl_client.py

```python
"""Proxycurl LinkedIn profile enrichment client."""
import httpx
from typing import Dict, Optional, List
from dataclasses import dataclass
import os
import asyncio

@dataclass
class LinkedInProfile:
    """Enriched LinkedIn profile data."""
    full_name: str
    headline: str
    current_company: str
    current_title: str
    location: str
    summary: str
    connections: int
    profile_url: str
    profile_picture_url: Optional[str]
    experiences: List[Dict]
    education: List[Dict]
    skills: List[str]
    certifications: List[Dict]

class ProxycurlClient:
    """Client for Proxycurl LinkedIn API."""
    
    BASE_URL = "https://nubela.co/proxycurl/api"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("PROXYCURL_API_KEY")
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0
        )
    
    async def get_profile(self, linkedin_url: str) -> Optional[LinkedInProfile]:
        """
        Get LinkedIn profile by URL.
        
        Cost: ~$0.01 per profile
        """
        if not linkedin_url:
            return None
        
        # Normalize URL
        if not linkedin_url.startswith("http"):
            linkedin_url = f"https://www.linkedin.com/in/{linkedin_url}"
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/v2/linkedin",
                params={
                    "url": linkedin_url,
                    "use_cache": "if-recent",
                    "skills": "include",
                    "inferred_salary": "include"
                }
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Get current position
            experiences = data.get("experiences", [])
            current_exp = next((e for e in experiences if e.get("ends_at") is None), {})
            
            return LinkedInProfile(
                full_name=data.get("full_name", ""),
                headline=data.get("headline", ""),
                current_company=current_exp.get("company", ""),
                current_title=current_exp.get("title", ""),
                location=data.get("city", "") + ", " + data.get("state", ""),
                summary=data.get("summary", ""),
                connections=data.get("connections", 0),
                profile_url=linkedin_url,
                profile_picture_url=data.get("profile_pic_url"),
                experiences=experiences,
                education=data.get("education", []),
                skills=data.get("skills", []),
                certifications=data.get("certifications", [])
            )
            
        except Exception as e:
            print(f"Error enriching {linkedin_url}: {e}")
            return None
    
    async def search_person(
        self,
        first_name: str,
        last_name: str,
        company: str = None,
        location: str = None
    ) -> Optional[str]:
        """
        Search for LinkedIn profile by name.
        
        Cost: ~$0.03 per search
        """
        try:
            params = {
                "first_name": first_name,
                "last_name": last_name
            }
            if company:
                params["company_domain"] = company
            if location:
                params["location"] = location
            
            response = await self.client.get(
                f"{self.BASE_URL}/linkedin/profile/resolve",
                params=params
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            data = response.json()
            
            return data.get("url")
            
        except Exception as e:
            print(f"Error searching for {first_name} {last_name}: {e}")
            return None
    
    async def enrich_batch(
        self,
        contacts: List[Dict],
        linkedin_field: str = "LinkedIn Contact Profile URL"
    ) -> List[Dict]:
        """
        Enrich batch of contacts with LinkedIn data.
        
        Args:
            contacts: List of contact dicts
            linkedin_field: Field containing LinkedIn URL
        """
        enriched = []
        
        for contact in contacts:
            linkedin_url = contact.get(linkedin_field)
            
            if linkedin_url:
                profile = await self.get_profile(linkedin_url)
                
                if profile:
                    contact["linkedin_verified"] = True
                    contact["linkedin_headline"] = profile.headline
                    contact["linkedin_current_company"] = profile.current_company
                    contact["linkedin_current_title"] = profile.current_title
                    contact["linkedin_connections"] = profile.connections
                    contact["linkedin_skills"] = profile.skills[:10]
                    
                    # Check if still at expected company
                    expected_company = contact.get("Company", "GDIT")
                    contact["company_match"] = (
                        expected_company.lower() in profile.current_company.lower()
                        or profile.current_company.lower() in expected_company.lower()
                    )
                else:
                    contact["linkedin_verified"] = False
            else:
                contact["linkedin_verified"] = False
            
            enriched.append(contact)
            
            # Rate limit
            await asyncio.sleep(0.5)
        
        return enriched
    
    async def verify_contact(self, contact: Dict) -> Dict:
        """
        Verify a single contact's LinkedIn data.
        
        Returns contact with verification status.
        """
        linkedin_url = contact.get("LinkedIn Contact Profile URL")
        
        if not linkedin_url:
            contact["verification_status"] = "no_linkedin"
            return contact
        
        profile = await self.get_profile(linkedin_url)
        
        if not profile:
            contact["verification_status"] = "profile_not_found"
            return contact
        
        # Compare data
        expected_name = f"{contact.get('First Name', '')} {contact.get('Last Name', '')}"
        actual_name = profile.full_name
        
        expected_title = contact.get("Job Title", "")
        actual_title = profile.current_title
        
        name_match = expected_name.lower() in actual_name.lower() or actual_name.lower() in expected_name.lower()
        title_match = any(word in actual_title.lower() for word in expected_title.lower().split())
        
        if name_match and title_match:
            contact["verification_status"] = "verified"
        elif name_match:
            contact["verification_status"] = "title_changed"
            contact["new_title"] = actual_title
        else:
            contact["verification_status"] = "mismatch"
        
        contact["linkedin_verified_at"] = str(datetime.now())
        contact["linkedin_data"] = {
            "full_name": profile.full_name,
            "headline": profile.headline,
            "current_company": profile.current_company,
            "current_title": profile.current_title,
            "connections": profile.connections
        }
        
        return contact
    
    async def close(self):
        await self.client.aclose()


from datetime import datetime

async def verify_dcgs_contacts():
    """Verify DCGS contact database."""
    import pandas as pd
    
    df = pd.read_csv('/mnt/project/DCGS_Contact_Spreadsheet__391_120925_PERSON.csv')
    
    # Only verify contacts with LinkedIn URLs
    contacts_with_linkedin = df[df['LinkedIn Contact Profile URL'].notna()].head(50)
    
    client = ProxycurlClient()
    
    try:
        verified = []
        for _, row in contacts_with_linkedin.iterrows():
            contact = row.to_dict()
            verified_contact = await client.verify_contact(contact)
            verified.append(verified_contact)
            print(f"Verified: {contact.get('First Name')} {contact.get('Last Name')} - {verified_contact['verification_status']}")
        
        # Stats
        statuses = [c["verification_status"] for c in verified]
        print(f"\n=== Verification Results ===")
        print(f"Total: {len(verified)}")
        print(f"Verified: {statuses.count('verified')}")
        print(f"Title Changed: {statuses.count('title_changed')}")
        print(f"Not Found: {statuses.count('profile_not_found')}")
        print(f"Mismatch: {statuses.count('mismatch')}")
        
        return verified
        
    finally:
        await client.close()
```

### HUB INTEGRATION (Add to hub/routes/linkedin_routes.py)

```python
from fastapi import APIRouter
from services.linkedin.proxycurl_client import ProxycurlClient, verify_dcgs_contacts

router = APIRouter(prefix="/linkedin", tags=["LinkedIn Enrichment"])

@router.get("/profile")
async def get_linkedin_profile(url: str):
    """Get LinkedIn profile data."""
    client = ProxycurlClient()
    try:
        profile = await client.get_profile(url)
        if not profile:
            return {"error": "Profile not found"}
        return {
            "full_name": profile.full_name,
            "headline": profile.headline,
            "current_company": profile.current_company,
            "current_title": profile.current_title,
            "location": profile.location,
            "connections": profile.connections,
            "skills": profile.skills[:10],
            "experiences": len(profile.experiences)
        }
    finally:
        await client.close()

@router.post("/verify")
async def verify_contact(
    first_name: str,
    last_name: str,
    linkedin_url: str,
    expected_title: str = None
):
    """Verify a contact against LinkedIn."""
    client = ProxycurlClient()
    try:
        contact = {
            "First Name": first_name,
            "Last Name": last_name,
            "LinkedIn Contact Profile URL": linkedin_url,
            "Job Title": expected_title or ""
        }
        result = await client.verify_contact(contact)
        return result
    finally:
        await client.close()

@router.post("/verify-batch")
async def verify_batch_contacts():
    """Verify DCGS contacts (first 50 with LinkedIn)."""
    result = await verify_dcgs_contacts()
    return {"verified_count": len(result), "results": result[:10]}
```

### SUCCESS CRITERIA
1. [ ] Proxycurl API key configured
2. [ ] Profile retrieval working
3. [ ] Batch enrichment working
4. [ ] Contact verification accurate
5. [ ] Company match detection working
6. [ ] Hub API endpoints functional
```

---

# PROMPT 12: KESTRA WORKFLOW ORCHESTRATION
## Target: n8n-builder (Terminal 3-1)

### Copy This Prompt:

```
## ENHANCEMENT: Kestra Workflow Orchestration

### OBJECTIVE
Deploy Kestra (https://github.com/kestra-io/kestra) as workflow orchestration engine alongside n8n, handling complex multi-step pipelines and scheduled jobs.

### CONTEXT
- Kestra is an open-source orchestration platform (16k+ stars)
- Handles complex DAG workflows, retries, scheduling
- Complements n8n for heavier batch processing
- Must integrate with existing n8n webhooks and BD pipeline

### DOCKER SETUP
```bash
docker run -d \
  --name kestra \
  -p 8081:8080 \
  -e KESTRA_CONFIGURATION=kestra.queue.type=memory \
  kestra/kestra:latest server standalone
```

### IMPLEMENTATION REQUIREMENTS

Create folder: workflows/kestra/

#### File 1: workflows/kestra/bd_pipeline.yml

```yaml
# Kestra workflow: BD Intelligence Pipeline
id: bd-intelligence-pipeline
namespace: pts.bd
description: |
  Complete BD intelligence pipeline:
  1. Scrape jobs from multiple sources
  2. Enrich with program mapping
  3. Verify contacts via LinkedIn
  4. Generate daily playbook

inputs:
  - id: scrape_sources
    type: ARRAY
    itemType: STRING
    defaults:
      - insight_global
      - apex_systems
      - teksystems

tasks:
  - id: scrape-jobs
    type: io.kestra.plugin.scripts.python.Script
    description: Run JobSpy aggregator
    runner: DOCKER
    docker:
      image: python:3.11-slim
    beforeCommands:
      - pip install python-jobspy pandas
    script: |
      from jobspy import scrape_jobs
      import pandas as pd
      
      results = []
      for keyword in ['DCGS', 'ISR analyst', 'network engineer TS/SCI']:
          for location in ['San Diego, CA', 'Hampton, VA', 'Dayton, OH']:
              try:
                  jobs = scrape_jobs(
                      site_name=['linkedin', 'indeed'],
                      search_term=keyword,
                      location=location,
                      results_wanted=50,
                      hours_old=72
                  )
                  if not jobs.empty:
                      results.append(jobs)
              except Exception as e:
                  print(f"Error: {e}")
      
      if results:
          combined = pd.concat(results, ignore_index=True)
          combined.to_csv('{{ outputs.jobs_csv }}', index=False)
          print(f"Scraped {len(combined)} jobs")
    outputFiles:
      - jobs_csv: "jobs_scraped.csv"

  - id: enrich-jobs
    type: io.kestra.plugin.scripts.python.Script
    description: Enrich jobs with program mapping
    dependsOn:
      - scrape-jobs
    runner: DOCKER
    docker:
      image: python:3.11-slim
    beforeCommands:
      - pip install pandas anthropic
    inputFiles:
      jobs.csv: "{{ outputs.scrape-jobs.jobs_csv }}"
    script: |
      import pandas as pd
      import os
      from anthropic import Anthropic
      
      df = pd.read_csv('jobs.csv')
      client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
      
      # Program mapping logic
      LOCATION_TO_PROGRAM = {
          'San Diego': 'AF DCGS - PACAF',
          'Hampton': 'AF DCGS - Langley',
          'Dayton': 'AF DCGS - Wright-Patt',
          'Norfolk': 'Navy DCGS-N',
      }
      
      def map_program(location):
          for loc, program in LOCATION_TO_PROGRAM.items():
              if loc.lower() in str(location).lower():
                  return program
          return 'Unknown'
      
      df['inferred_program'] = df['location'].apply(map_program)
      df['bd_score'] = df.apply(lambda r: 80 if 'DCGS' in str(r.get('title', '')) else 50, axis=1)
      
      df.to_csv('{{ outputs.enriched_csv }}', index=False)
      print(f"Enriched {len(df)} jobs")
    env:
      ANTHROPIC_API_KEY: "{{ secret('ANTHROPIC_API_KEY') }}"
    outputFiles:
      - enriched_csv: "jobs_enriched.csv"

  - id: filter-high-priority
    type: io.kestra.plugin.scripts.python.Script
    description: Filter high-priority jobs (BD score >= 70)
    dependsOn:
      - enrich-jobs
    runner: DOCKER
    docker:
      image: python:3.11-slim
    beforeCommands:
      - pip install pandas
    inputFiles:
      enriched.csv: "{{ outputs.enrich-jobs.enriched_csv }}"
    script: |
      import pandas as pd
      
      df = pd.read_csv('enriched.csv')
      high_priority = df[df['bd_score'] >= 70]
      
      high_priority.to_csv('{{ outputs.priority_csv }}', index=False)
      print(f"High priority jobs: {len(high_priority)}")
    outputFiles:
      - priority_csv: "jobs_high_priority.csv"

  - id: notify-slack
    type: io.kestra.plugin.notifications.slack.SlackIncomingWebhook
    description: Send daily summary to Slack
    dependsOn:
      - filter-high-priority
    url: "{{ secret('SLACK_WEBHOOK_URL') }}"
    payload: |
      {
        "text": "🎯 BD Pipeline Complete",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Daily BD Intelligence Summary*\n• Jobs scraped: {{ outputs.scrape-jobs.jobs_csv }}\n• High priority: {{ outputs.filter-high-priority.priority_csv }}"
            }
          }
        ]
      }

triggers:
  - id: daily-schedule
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 6 * * 1-5"  # 6 AM weekdays
    timezone: America/New_York
```

#### File 2: workflows/kestra/contact_verification.yml

```yaml
# Kestra workflow: Contact Verification
id: contact-verification
namespace: pts.bd
description: Verify DCGS contacts via LinkedIn (Proxycurl)

inputs:
  - id: batch_size
    type: INT
    defaults: 50

tasks:
  - id: load-contacts
    type: io.kestra.plugin.scripts.python.Script
    runner: DOCKER
    docker:
      image: python:3.11-slim
    beforeCommands:
      - pip install pandas
    script: |
      import pandas as pd
      
      df = pd.read_csv('/data/contacts.csv')
      to_verify = df[df['LinkedIn Contact Profile URL'].notna()].head({{ inputs.batch_size }})
      to_verify.to_csv('{{ outputs.batch_csv }}', index=False)
    outputFiles:
      - batch_csv: "contacts_batch.csv"

  - id: verify-linkedin
    type: io.kestra.plugin.scripts.python.Script
    dependsOn:
      - load-contacts
    runner: DOCKER
    docker:
      image: python:3.11-slim
    beforeCommands:
      - pip install pandas httpx
    inputFiles:
      batch.csv: "{{ outputs.load-contacts.batch_csv }}"
    env:
      PROXYCURL_API_KEY: "{{ secret('PROXYCURL_API_KEY') }}"
    script: |
      import pandas as pd
      import httpx
      import os
      import time
      
      API_KEY = os.environ['PROXYCURL_API_KEY']
      df = pd.read_csv('batch.csv')
      
      results = []
      for _, row in df.iterrows():
          url = row['LinkedIn Contact Profile URL']
          try:
              resp = httpx.get(
                  'https://nubela.co/proxycurl/api/v2/linkedin',
                  params={'url': url},
                  headers={'Authorization': f'Bearer {API_KEY}'},
                  timeout=30
              )
              if resp.status_code == 200:
                  data = resp.json()
                  row['linkedin_verified'] = True
                  row['current_title'] = data.get('headline', '')
              else:
                  row['linkedin_verified'] = False
          except Exception as e:
              row['linkedin_verified'] = False
          results.append(row)
          time.sleep(0.5)
      
      pd.DataFrame(results).to_csv('{{ outputs.verified_csv }}', index=False)
    outputFiles:
      - verified_csv: "contacts_verified.csv"

triggers:
  - id: weekly-verification
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 2 * * 0"  # 2 AM Sundays
```

#### File 3: workflows/kestra/kestra_client.py

```python
"""Kestra API client for workflow management."""
import httpx
from typing import Dict, List, Optional
import os

class KestraClient:
    """Client for Kestra workflow orchestration."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("KESTRA_URL", "http://localhost:8081")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def list_flows(self, namespace: str = "pts.bd") -> List[Dict]:
        """List all flows in namespace."""
        response = await self.client.get(
            f"{self.base_url}/api/v1/flows/{namespace}"
        )
        response.raise_for_status()
        return response.json()
    
    async def execute_flow(
        self,
        namespace: str,
        flow_id: str,
        inputs: Dict = None
    ) -> Dict:
        """Execute a flow."""
        response = await self.client.post(
            f"{self.base_url}/api/v1/executions/{namespace}/{flow_id}",
            json={"inputs": inputs or {}}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_execution(self, execution_id: str) -> Dict:
        """Get execution status."""
        response = await self.client.get(
            f"{self.base_url}/api/v1/executions/{execution_id}"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_execution_logs(self, execution_id: str) -> List[Dict]:
        """Get execution logs."""
        response = await self.client.get(
            f"{self.base_url}/api/v1/logs/{execution_id}"
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        await self.client.aclose()


async def trigger_bd_pipeline():
    """Trigger the BD intelligence pipeline."""
    client = KestraClient()
    try:
        result = await client.execute_flow(
            namespace="pts.bd",
            flow_id="bd-intelligence-pipeline"
        )
        print(f"Pipeline started: {result.get('id')}")
        return result
    finally:
        await client.close()
```

### INTEGRATION WITH HUB API

Add to hub/routes/workflow_routes.py:

```python
from fastapi import APIRouter
from workflows.kestra.kestra_client import KestraClient, trigger_bd_pipeline

router = APIRouter(prefix="/workflows", tags=["Kestra Workflows"])

@router.get("/kestra/health")
async def check_kestra_health():
    """Check Kestra status."""
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8081/api/v1/configs")
            return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@router.get("/kestra/flows")
async def list_kestra_flows():
    """List all Kestra flows."""
    client = KestraClient()
    try:
        flows = await client.list_flows()
        return {"flows": flows}
    finally:
        await client.close()

@router.post("/kestra/execute/{flow_id}")
async def execute_kestra_flow(flow_id: str):
    """Execute a Kestra flow."""
    client = KestraClient()
    try:
        result = await client.execute_flow("pts.bd", flow_id)
        return result
    finally:
        await client.close()

@router.post("/bd-pipeline/run")
async def run_bd_pipeline():
    """Run the complete BD intelligence pipeline."""
    result = await trigger_bd_pipeline()
    return result
```

### SUCCESS CRITERIA
1. [ ] Kestra Docker container running: `docker ps | grep kestra`
2. [ ] Kestra UI accessible: http://localhost:8081
3. [ ] BD pipeline workflow created
4. [ ] Contact verification workflow created
5. [ ] Scheduled triggers configured
6. [ ] Hub API can trigger workflows
```

---

## ✅ POST-VERIFICATION CHECKLIST

### Docker Container Status
```bash
# Run after all enhancements complete
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Expected output:
# reacher     Up X hours   0.0.0.0:8080->8080/tcp
# qdrant      Up X hours   0.0.0.0:6333-6334->6333-6334/tcp
# twenty      Up X hours   0.0.0.0:3000->3000/tcp  (if CRM installed)
# kestra      Up X hours   0.0.0.0:8081->8080/tcp  (if Kestra installed)
```

### Python Import Tests (Terminal 2-1)
```bash
cd ~/data-scraper
python -c "from scrapers.unified import JobSpyAggregator; print('✅ JobSpy OK')"
python -c "from external_apis.fpds_enhanced import EnhancedFPDSClient; print('✅ FPDS OK')"
python -c "from external_apis.govcon_api import GovConAPIClient; print('✅ GovCon OK')"
```

### Python Import Tests (Terminal 1-1)
```bash
cd ~/bd-automation-engine
python -c "from services.email_verification.reacher_client import ReacherClient; print('✅ Reacher OK')"
python -c "from agents.langgraph_bd_agent import BDResearchAgent; print('✅ LangGraph OK')"
python -c "from services.hybrid_search import HybridSearchEngine; print('✅ Hybrid OK')"
python -c "from agents.rfp_response_agent import RFPResponseAgent; print('✅ RFP OK')"
python -c "from services.linkedin.proxycurl_client import ProxycurlClient; print('✅ Proxycurl OK')"
```

### Hub API Health Checks
```bash
# Start Hub if not running
cd ~/bd-automation-engine && uvicorn hub.main:app --reload --port 8000

# Test endpoints
curl http://localhost:8000/scrapers/jobspy/status
curl http://localhost:8000/fpds/dcgs
curl http://localhost:8000/email/health
curl http://localhost:8000/search/hybrid -X POST -H "Content-Type: application/json" -d '{"query":"DCGS engineer"}'
```

### Integration Verification
```bash
# Test full pipeline: Scrape → Enrich → Search
# 1. Trigger job scrape
curl -X POST http://localhost:8000/scrapers/jobspy/run

# 2. Wait for completion
sleep 60
curl http://localhost:8000/scrapers/jobspy/status

# 3. Search enriched data
curl "http://localhost:8000/scrapers/jobspy/results?min_score=70"
```

---

## 🔧 ENVIRONMENT VARIABLES

### Terminal 2-1 (data-scraper/.env)
```bash
# GovCon API
GOVCON_API_KEY=your_govcon_key

# SAM.gov (optional, FPDS uses public feeds)
SAM_GOV_API_KEY=your_sam_key
```

### Terminal 1-1 (bd-automation-engine/.env)
```bash
# Reacher (self-hosted, no key needed)
REACHER_URL=http://localhost:8080

# Twenty CRM (if installed)
TWENTY_API_URL=http://localhost:3000
TWENTY_API_KEY=your_twenty_key

# Proxycurl
PROXYCURL_API_KEY=your_proxycurl_key

# Qdrant (local)
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=bd_documents

# LLM
ANTHROPIC_API_KEY=your_anthropic_key
```

### Terminal 3-1 (n8n-builder/.env)
```bash
# Kestra
KESTRA_URL=http://localhost:8081

# n8n Cloud
N8N_URL=https://primetech.app.n8n.cloud

# Slack Alerts
SLACK_WEBHOOK_URL=your_slack_webhook
```

---

## 📊 COST TRACKING

### Monthly Estimates

| Service | Cost Model | Estimated Usage | Monthly Cost |
|---------|------------|-----------------|--------------|
| **Free/Self-Hosted** | | | |
| JobSpy | Free | Unlimited | $0 |
| FPDS Parser | Free | Unlimited | $0 |
| Reacher | Self-hosted | Unlimited | $0 |
| Qdrant | Self-hosted | Unlimited | $0 |
| LangGraph | Free (uses your keys) | N/A | $0 |
| **Paid APIs** | | | |
| GovCon API | $49/mo unlimited | Unlimited | $49 |
| Proxycurl | $0.01-0.10/profile | 500 profiles | $5-50 |
| Anthropic Claude | ~$0.003/1K tokens | Variable | $20-50 |
| **Total** | | | **~$74-149/mo** |

---

## 🔄 DATA FLOW DIAGRAM

```
┌──────────────────────────────────────────────────────────────────┐
│                     JOB INTELLIGENCE FLOW                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [JobSpy] → [FPDS] → [GovCon]                                   │
│      ↓         ↓         ↓                                       │
│  Competitor  Contract   SAM.gov                                  │
│  Jobs        Awards     Opportunities                            │
│      └─────────┬─────────┘                                       │
│                ↓                                                 │
│  ┌─────────────────────────────┐                                │
│  │   Program Mapping Hub       │ ← GPT-4o Enrichment            │
│  │   (Notion: f57792c1...)     │                                │
│  │   Status: raw → enriched    │                                │
│  └─────────────┬───────────────┘                                │
│                ↓                                                 │
│  ┌─────────────────────────────┐                                │
│  │   Hybrid Search (Qdrant)    │ ← LangGraph RAG                │
│  │   BM25 + Dense + Rerank     │                                │
│  │   8,447+ vectors            │                                │
│  └─────────────┬───────────────┘                                │
│                ↓                                                 │
│  ┌─────────────────────────────┐                                │
│  │   Contact Intelligence      │                                │
│  │   • Proxycurl LinkedIn      │                                │
│  │   • Reacher Email           │                                │
│  │   • Classification          │                                │
│  └─────────────┬───────────────┘                                │
│                ↓                                                 │
│  ┌─────────────────────────────┐                                │
│  │   BD Outputs                │                                │
│  │   • Call Sheets (Excel)     │                                │
│  │   • Playbooks (DOCX)        │                                │
│  │   • RFP Responses           │                                │
│  │   • Dashboard (Reagraph)    │                                │
│  └─────────────────────────────┘                                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

**Document continues in Part 2 with Prompts 5-12...**
