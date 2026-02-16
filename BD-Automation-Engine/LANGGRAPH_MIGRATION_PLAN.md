# LANGGRAPH WORKFLOW MIGRATION PLAN

> Generated from PROMPT 7 of PTS_NEXTGEN_CONSOLIDATION_BLUEPRINT.md
> Date: 2026-02-16
> Scope: N8N → LangGraph migration, workflow consolidation, unified orchestrator

---

## CURRENT WORKFLOWS

### Summary: 15 Orchestrated Processes

| # | Name | Trigger | Implementation | Frequency |
|---|------|---------|---------------|-----------|
| 1 | Master Pipeline | CLI/scheduled | `orchestrator.py` (Python) | 6h interval |
| 2 | Morning Briefing | Cron 06:30 | LangGraph + APScheduler | Daily |
| 3 | Contact Enrichment | Cron Mon 02:00 | LangGraph + APScheduler | Weekly |
| 4 | Pipeline Manager | API/manual | LangGraph | On-demand |
| 5 | Competitive Intel | API/manual | LangGraph | On-demand |
| 6 | BD Proposal | API + human gate | LangGraph | On-demand |
| 7 | Weekly Pipeline | Cron Fri 04:00 | LangGraph | Weekly |
| 8 | Contact Outreach | API + human gate | LangGraph | On-demand |
| 9 | Recompete Monitor | API + human gate | LangGraph | On-demand |
| 10 | BD Research Crew | API | CrewAI | On-demand |
| 11 | Daily Scrape | Cron 05:00 | task_scheduler.py | Daily |
| 12 | Pipeline Health | Cron */2h | task_scheduler.py | Every 2h |
| 13 | Weekly Report | Cron Fri 16:00 | task_scheduler.py | Weekly |
| 14 | Monthly Retrain | Cron 1st 03:00 | task_scheduler.py | Monthly |
| 15 | N8N Workflows (18) | Webhook/API | N8N JSON | Real-time |

---

### 1. Master Pipeline Orchestrator

| Attribute | Value |
|-----------|-------|
| **File** | `orchestrator.py` (1,086 lines) |
| **Trigger** | CLI: `python orchestrator.py --input data/jobs.json` or `--schedule --interval 6h` |
| **Implementation** | Pure Python, APScheduler for scheduling |
| **Error handling** | Try-catch per stage, error accumulation, alert at end |

**Steps:**
```
1. Ingest jobs from JSON/CSV
   ↓
2. Program Mapping (Engine 2) — standardize fields, match to federal programs
   ↓
3. BD Scoring (Engine 5) — calculate 0-100 BD priority score
   ↓
4. QA Evaluation (Engine 6) — validate data quality
   ↓
5. Briefing Generation (Engine 4) — create daily playbook
   ↓
6. Export to Notion/n8n — push to external systems
   ↓
7. Webhook delivery — POST to n8n triggers
   ↓
8. Email notifications — SMTP hot lead alerts + daily summary
   ↓
9. Bullhorn ETL (Engine 7) — sync CRM data
   ↓
10. Dashboard export — update dashboard data
    ↓
11. Knowledge base indexing — embed and store in Qdrant
```

**Data flow:** JSON input → program_mapper → bd_scorer → qa_evaluator → playbook_generator → notion_exporter → webhook_sender → email_sender → bullhorn_etl → dashboard_exporter → vector_indexer

**DBs touched:** Qdrant (write), SQLite/Bullhorn (read/write), Notion (write), filesystem (JSON state)

---

### 2. Morning Briefing Workflow

| Attribute | Value |
|-----------|-------|
| **File** | `Engine8_Knowledge/workflows/production/morning_briefing.py` (526 lines) |
| **Trigger** | APScheduler CronTrigger(hour=6, minute=30) |
| **Implementation** | LangGraph StateGraph with checkpoint |
| **Error handling** | Per-node try-catch, quality scoring, fallback to cached briefing |

**Steps (parallel gather → merge → generate):**
```
        ┌─ gather_pipeline_updates ──┐
        ├─ gather_new_jobs ──────────┤
START → ├─ gather_competitive_intel ──├→ merge_briefing → quality_check → generate_summary → END
        ├─ gather_contact_changes ───┤
        └─ fetch_graph_insights ─────┘
```

**Data flow:** Qdrant (jobs, contacts) + Neo4j (relationships) → parallel nodes → merge → LLM summary → JSON briefing saved to `data/briefings/`

---

### 3. Contact Enrichment Workflow

| Attribute | Value |
|-----------|-------|
| **File** | `Engine8_Knowledge/workflows/production/contact_enrichment.py` (538 lines) |
| **Trigger** | APScheduler CronTrigger(day_of_week="mon", hour=2, minute=0) |
| **Implementation** | LangGraph StateGraph with human gate |
| **Error handling** | Node retry with backoff, human approval for Tier 1-3 |

**Steps:**
```
validate_input → ┌─ gather_from_qdrant ──┐
                 ├─ gather_from_neo4j ───├→ merge_data → classify_contacts
                 └─ gather_from_notion ──┘       ↓
                                          [HUMAN GATE: Tier 1-3 approval]
                                                 ↓
                                          execute_updates → generate_report → END
```

**Data flow:** Contact IDs → Qdrant + Neo4j + Notion (parallel) → merge → classifier (6-tier) → human approval → update Qdrant + Neo4j → report

---

### 4. Pipeline Manager Workflow

| Attribute | Value |
|-----------|-------|
| **File** | `Engine8_Knowledge/workflows/production/pipeline_manager.py` (487 lines) |
| **Trigger** | API call or scheduled |
| **Implementation** | LangGraph StateGraph with human gate for critical actions |

**Steps:**
```
scan_pipeline → check_stale_items → identify_deadlines → analyze_budget_cycles
     ↓
risk_analysis → [HUMAN GATE: Critical (red) actions] → execute_actions → generate_report → END
```

**Data flow:** Qdrant jobs → stale detection (>14 days) → deadline scan → DoD FY budget analysis → ML risk scoring → human gate → actions → report

---

### 5. Competitive Intel Workflow

| Attribute | Value |
|-----------|-------|
| **File** | `Engine8_Knowledge/workflows/production/competitive_intel.py` (567 lines) |
| **Trigger** | API call |
| **Implementation** | LangGraph StateGraph |

**Steps:**
```
        ┌─ gather_sam_data ──────────┐
START → ├─ gather_hiring_signals ────├→ analyze_competitive_landscape → score_risks → generate_report → END
        └─ gather_contract_awards ───┘
```

**Data flow:** SAM.gov + job boards + contract databases → parallel gather → analysis → win probability → report

---

### 6. BD Proposal Workflow (from N8N-Builder)

| Attribute | Value |
|-----------|-------|
| **File** | `data/from_n8n_builder/langgraph/bd_langgraph/bd_workflows.py` |
| **Trigger** | API call |
| **Implementation** | LangGraph StateGraph with human-in-the-loop interrupt |

**Steps:**
```
research → gather_contacts → analyze_competition → generate_strategy
     ↓
request_review → [INTERRUPT: human feedback]
     ↓
process_feedback → ┌─ finalize_playbook (approved)
                   ├─ revise_strategy (revise) → loop back to generate_strategy
                   └─ abort (rejected) → END
```

---

### 7. Weekly Pipeline Workflow (from N8N-Builder)

| Attribute | Value |
|-----------|-------|
| **File** | `data/from_n8n_builder/langgraph/bd_langgraph/pipeline_workflows.py` |
| **Trigger** | Scheduled (Friday) or API |
| **Implementation** | LangGraph StateGraph with conditional edges |

**Steps:**
```
scrape_opportunities → [CONDITIONAL: has results?]
     ↓ yes                    ↓ no
enrich_opportunities     score → END
     ↓
score_opportunities → [CONDITIONAL: has scored?]
     ↓ yes                    ↓ no
generate_report          END
     ↓
END
```

---

### 8-9. Contact Outreach & Recompete Monitor

Both defined in `data/from_n8n_builder/langgraph/bd_langgraph/states.py` with human approval gates. Follow same LangGraph StateGraph pattern.

---

### 10. BD Research Crew (CrewAI)

| Attribute | Value |
|-----------|-------|
| **File** | `Engine8_Knowledge/agents/crews.py` |
| **Trigger** | API: POST `/agents/research` |
| **Implementation** | CrewAI sequential crew (5 agents, 5 tasks) |

**Agents:** program_researcher → contact_enricher → competitive_analyst → outreach_composer → synthesis

**Data flow:** Program name → research tasks (sequential) → BDResearchBundle output

---

### 11-14. Task Scheduler Automations

| Attribute | Value |
|-----------|-------|
| **File** | `Engine8_Knowledge/automation/task_scheduler.py` (580 lines) |
| **Trigger** | Custom cron parser, 60-second polling loop |
| **Implementation** | Background thread with handler registry |

**10 scheduled tasks:** daily_scrape (05:00), morning_brief (06:30), contact_enrichment (Sun 02:00), competitive_scan (07:00), pipeline_health (*/2h), model_drift_check (03:00), weekly_report (Fri 16:00), monthly_retrain (1st 03:00), event_cleanup (01:00), backup (00:00)

---

### 15. N8N Workflows (18 JSON definitions)

| File | Purpose | N8N Nodes |
|------|---------|-----------|
| WF1_Apify_Job_Scraper_Intake | Ingest scraped jobs | webhook → code → httpRequest |
| WF2_AI_Enrichment_Processor | LLM enrichment | webhook → code → openai → httpRequest |
| WF3_Hub_to_BD_Opportunities | Export to Notion | schedule → httpRequest → notion |
| WF4_Contact_Classification | Classify contacts | webhook → code → openai → httpRequest |
| WF5_Hot_Lead_Alerts | Alert on hot leads | webhook → if → slack → email |
| WF6_Weekly_Summary_Report | Weekly digest | cron → httpRequest → openai → slack |
| BD_Master_Orchestration | Central orchestrator | webhook → switch → multiple branches |
| Plus 11 more | Various integrations | Mixed node types |

---

## LANGGRAPH STATE DEFINITIONS

### Shared Base State

```python
class BaseWorkflowState(TypedDict):
    """Shared fields across all BD workflows."""
    workflow_id: str
    workflow_type: str
    thread_id: str
    status: str                        # pending, running, completed, failed, aborted
    current_node: str
    completed_nodes: list[str]
    started_at: str
    updated_at: str
    error_message: Optional[str]
    error_node: Optional[str]
    retry_count: int
    awaiting_human_review: bool
    human_review_type: Optional[str]   # strategy_approval, contact_approval, action_approval
    human_review_request_id: Optional[str]
    human_feedback: Optional[dict]     # {decision: str, notes: str, reviewer: str}
```

### 1. MasterPipelineState (replaces orchestrator.py)

```python
class MasterPipelineState(TypedDict):
    # Base fields (inherited conceptually)
    workflow_id: str
    status: str
    current_node: str
    completed_nodes: list[str]
    error_message: Optional[str]
    retry_count: int

    # Input
    input_file: str                    # Path to scraped jobs JSON
    input_jobs: list[dict]             # Raw job data

    # Stage outputs
    standardized_jobs: list[dict]      # After field extraction
    mapped_jobs: list[dict]            # After program mapping
    scored_jobs: list[dict]            # After BD scoring (0-100)
    qa_results: dict                   # QA evaluation results
    hot_leads: list[dict]              # Score >= 80

    # Enrichment
    briefing: dict                     # Daily playbook content
    export_results: dict               # Notion/webhook delivery status

    # Notifications
    email_sent: bool
    webhook_delivered: bool
    slack_notified: bool

    # Indexing
    indexed_count: int                 # Records pushed to Qdrant
    indexing_errors: list[str]

    # Pipeline metadata
    stage_timings: dict[str, float]    # Stage name → seconds
    total_processed: int
    total_errors: int
```

### 2. MorningBriefingState (existing, refined)

```python
class MorningBriefingState(TypedDict):
    workflow_id: str
    status: str
    current_node: str
    completed_nodes: list[str]

    # Parallel gather outputs
    briefing_date: str
    pipeline_updates: list[dict]       # Recent pipeline changes
    new_jobs: list[dict]               # Jobs added since last briefing
    competitive_intel: list[dict]      # Competitive signals
    contact_changes: list[dict]        # Contact updates/movements
    graph_insights: list[dict]         # Neo4j relationship discoveries

    # Merge & quality
    merged_items: list[dict]           # Deduplicated, ranked items
    quality_score: float               # 0-1 briefing quality
    executive_summary: str             # LLM-generated summary

    # Delivery
    briefing_path: str                 # Saved JSON path
    slack_delivered: bool
    email_delivered: bool
```

### 3. ContactEnrichmentState (existing, refined)

```python
class ContactEnrichmentState(TypedDict):
    workflow_id: str
    status: str
    current_node: str
    completed_nodes: list[str]
    awaiting_human_review: bool
    human_feedback: Optional[dict]

    # Input
    contact_ids: list[str]             # Target contacts (or empty for full scan)

    # Parallel gather outputs
    contacts_qdrant: list[dict]        # Vector store data
    contacts_neo4j: list[dict]         # Graph relationships
    contacts_notion: list[dict]        # Notion DB records

    # Processing
    contacts_merged: list[dict]        # Deduplicated merge
    classifications: list[dict]        # Tier 1-6 classification results
    tier_1_3_contacts: list[dict]      # High-tier requiring approval

    # Human gate
    human_approved: bool
    approved_contacts: list[str]       # IDs approved for update

    # Output
    enrichment_results: list[dict]     # What was updated
    report: dict                       # EnrichmentReport summary
```

### 4. PipelineManagerState (existing, refined)

```python
class PipelineManagerState(TypedDict):
    workflow_id: str
    status: str
    current_node: str
    completed_nodes: list[str]
    awaiting_human_review: bool
    human_feedback: Optional[dict]

    # Pipeline scan
    active_opportunities: list[dict]
    stale_items: list[dict]            # >14 days no activity
    upcoming_deadlines: list[dict]     # Next 30 days

    # Analysis
    budget_cycles: dict                # FY timing, Q4 surge windows
    risks: list[dict]                  # Risk items with severity
    recommendations: list[dict]        # Recommended actions

    # Human gate (critical actions only)
    critical_actions: list[dict]       # Red-severity items
    human_approved_actions: list[str]  # Approved action IDs

    # Execution
    executed_actions: list[dict]
    report: dict
```

### 5. CompetitiveIntelState (existing, refined)

```python
class CompetitiveIntelState(TypedDict):
    workflow_id: str
    status: str
    current_node: str
    completed_nodes: list[str]

    # Input
    target_programs: list[str]         # Programs to analyze

    # Parallel gather
    primes: list[dict]                 # Prime contractor data
    contracts: list[dict]              # Contract awards from FPDS/SAM
    hiring_signals: list[dict]         # Job posting analysis

    # Analysis
    competitive_landscape: dict        # Market positioning
    win_probabilities: dict            # Per-program win %
    analysis: dict                     # Full competitive analysis

    # Output
    report: dict                       # CompetitiveIntelReport
```

### 6. BDProposalState (existing in N8N-Builder)

```python
class BDProposalState(TypedDict):
    workflow_id: str
    status: str
    current_node: str
    completed_nodes: list[str]
    awaiting_human_review: bool
    human_feedback: Optional[dict]

    # Input
    opportunity_id: str
    agency: str
    naics_codes: list[str]
    target_value: float

    # Research
    similar_contracts: list[dict]
    market_intelligence: dict
    incumbent_info: dict

    # Contacts
    contacts_crm: list[dict]
    contacts_sam: list[dict]
    contacts_jobs: list[dict]

    # Analysis
    competitor_analysis: dict
    win_probability: float

    # Strategy (human approval gate)
    bd_strategy: dict
    strategy_approved: bool
    revision_notes: Optional[str]

    # Output
    final_playbook: dict
```

### 7. DailyScrapeState (replaces task_scheduler daily_scrape)

```python
class DailyScrapeState(TypedDict):
    workflow_id: str
    status: str
    current_node: str
    completed_nodes: list[str]

    # Input
    scraper_configs: list[dict]        # 9 prime scrapers

    # Scraping
    scrape_results: dict[str, list]    # Prime name → scraped jobs
    scrape_errors: dict[str, str]      # Prime name → error message
    total_scraped: int

    # Processing
    standardized_jobs: list[dict]
    mapped_jobs: list[dict]
    scored_jobs: list[dict]

    # Indexing
    indexed_count: int
    new_jobs_count: int                # Jobs not previously seen

    # Alerts
    hot_leads: list[dict]              # Score >= 80
    alerts_sent: bool
```

### 8. WeeklyReportState (replaces task_scheduler weekly_report)

```python
class WeeklyReportState(TypedDict):
    workflow_id: str
    status: str
    current_node: str
    completed_nodes: list[str]

    # Gather
    week_start: str
    week_end: str
    new_jobs_count: int
    new_contacts_count: int
    pipeline_changes: list[dict]
    outreach_stats: dict
    scraper_stats: dict

    # Analysis
    top_programs: list[dict]           # Most active programs
    hiring_trends: list[dict]          # Week-over-week changes
    performance_metrics: dict          # Fill rate, response rate

    # Output
    report_markdown: str
    report_delivered: bool             # Slack/email
```

---

## LANGGRAPH NODE DEFINITIONS

### Master Pipeline Nodes

```python
def ingest_jobs(state: MasterPipelineState) -> dict:
    """Load and validate raw job data from input file."""
    jobs = json.loads(Path(state["input_file"]).read_text())
    return {"input_jobs": jobs, "total_processed": len(jobs)}

def standardize_jobs(state: MasterPipelineState) -> dict:
    """Extract and normalize job fields using LLM."""
    from Engine2_ProgramMapping.scripts.job_standardizer import JobStandardizer
    standardizer = JobStandardizer()
    results = [standardizer.standardize(j) for j in state["input_jobs"]]
    return {"standardized_jobs": results}

def map_to_programs(state: MasterPipelineState) -> dict:
    """Match jobs to federal programs using multi-signal matching."""
    from Engine2_ProgramMapping.scripts.program_mapper import map_jobs_to_programs
    mapped = map_jobs_to_programs(state["standardized_jobs"])
    return {"mapped_jobs": mapped}

def score_bd_priority(state: MasterPipelineState) -> dict:
    """Calculate BD priority score (0-100) for each job."""
    from Engine5_Scoring.scripts.bd_scoring import BDScorer
    scorer = BDScorer()
    scored = [scorer.score(j) for j in state["mapped_jobs"]]
    hot = [j for j in scored if j.get("bd_score", 0) >= 80]
    return {"scored_jobs": scored, "hot_leads": hot}

def run_qa_evaluation(state: MasterPipelineState) -> dict:
    """Validate data quality and flag issues."""
    from Engine6_QA.scripts.alerts import evaluate_batch
    results = evaluate_batch(state["scored_jobs"])
    return {"qa_results": results}

def generate_briefing(state: MasterPipelineState) -> dict:
    """Create daily BD playbook from scored jobs."""
    from Engine4_Playbook.scripts.bd_playbook_generator import generate_playbook
    briefing = generate_playbook(state["scored_jobs"], state["hot_leads"])
    return {"briefing": briefing}

def export_to_external(state: MasterPipelineState) -> dict:
    """Push results to Notion, n8n webhooks, and email."""
    results = {}
    # Notion export
    results["notion"] = export_to_notion(state["scored_jobs"])
    # Webhook delivery
    results["webhook"] = deliver_webhook(state["hot_leads"])
    # Email notifications
    results["email"] = send_email_alerts(state["hot_leads"])
    return {"export_results": results, "email_sent": True, "webhook_delivered": True}

def index_to_knowledge_base(state: MasterPipelineState) -> dict:
    """Embed and store scored jobs in Qdrant."""
    from Engine8_Knowledge.scripts.vector_store import VectorStore
    store = VectorStore()
    count = store.index_jobs(state["scored_jobs"])
    return {"indexed_count": count}
```

### Morning Briefing Nodes

```python
def gather_pipeline_updates(state: MorningBriefingState) -> dict:
    """Fetch recent pipeline activity from Qdrant jobs collection."""
    qdrant = get_qdrant_client()
    results, _ = qdrant.scroll("jobs", limit=50, with_payload=True)
    updates = [{"id": str(r.id), **r.payload} for r in results
               if is_recent(r.payload.get("date_added"), hours=24)]
    return {"pipeline_updates": updates}

def gather_new_jobs(state: MorningBriefingState) -> dict:
    """Find jobs added since last briefing."""
    qdrant = get_qdrant_client()
    # Filter for jobs added in last 24h
    results = search_recent_jobs(qdrant, hours=24)
    return {"new_jobs": results}

def gather_competitive_intel(state: MorningBriefingState) -> dict:
    """Scan for competitive signals from job postings and contracts."""
    signals = detect_hiring_signals()
    return {"competitive_intel": signals}

def gather_contact_changes(state: MorningBriefingState) -> dict:
    """Check Neo4j for contact movements and relationship changes."""
    manager = get_neo4j_manager()
    changes = manager.run_query(
        "MATCH (p:Person) WHERE p.updated_at > $since RETURN p",
        {"since": yesterday_iso()}
    )
    return {"contact_changes": changes}

def fetch_graph_insights(state: MorningBriefingState) -> dict:
    """Extract notable patterns from knowledge graph."""
    manager = get_neo4j_manager()
    insights = manager.run_query("""
        MATCH (p:Person)-[:WORKS_AT]->(c:Company)-[:PRIMES_ON]->(pr:Program)
        WHERE pr.pop_end < date() + duration('P90D')
        RETURN pr.name, c.name, count(p) AS headcount
        ORDER BY headcount DESC LIMIT 10
    """)
    return {"graph_insights": insights}

def merge_briefing(state: MorningBriefingState) -> dict:
    """Merge and deduplicate all gathered intelligence."""
    all_items = (
        state["pipeline_updates"] + state["new_jobs"] +
        state["competitive_intel"] + state["contact_changes"] +
        state["graph_insights"]
    )
    merged = deduplicate_and_rank(all_items)
    return {"merged_items": merged}

def quality_check(state: MorningBriefingState) -> dict:
    """Score briefing quality (completeness, freshness, actionability)."""
    score = calculate_briefing_quality(state["merged_items"])
    return {"quality_score": score}

def generate_summary(state: MorningBriefingState) -> dict:
    """Generate executive summary using LLM."""
    summary = llm_generate_briefing(state["merged_items"], state["quality_score"])
    path = save_briefing(state["briefing_date"], summary)
    return {"executive_summary": summary, "briefing_path": path}
```

### Contact Enrichment Nodes

```python
def validate_enrichment_input(state: ContactEnrichmentState) -> dict:
    """Validate contact IDs or prepare full scan."""
    if not state.get("contact_ids"):
        # Full scan: find stale contacts (>30 days since update)
        ids = find_stale_contacts(days=30)
        return {"contact_ids": ids}
    return {}

def gather_from_qdrant(state: ContactEnrichmentState) -> dict:
    """Fetch contact data from vector store."""
    qdrant = get_qdrant_client()
    contacts = [get_contact_by_id(qdrant, cid) for cid in state["contact_ids"]]
    return {"contacts_qdrant": [c for c in contacts if c]}

def gather_from_neo4j(state: ContactEnrichmentState) -> dict:
    """Fetch relationship data from graph."""
    manager = get_neo4j_manager()
    contacts = [get_contact_graph(manager, cid) for cid in state["contact_ids"]]
    return {"contacts_neo4j": [c for c in contacts if c]}

def gather_from_notion(state: ContactEnrichmentState) -> dict:
    """Fetch latest data from Notion CRM database."""
    contacts = [query_notion_contact(cid) for cid in state["contact_ids"]]
    return {"contacts_notion": [c for c in contacts if c]}

def merge_contact_data(state: ContactEnrichmentState) -> dict:
    """Merge data from all three sources, resolve conflicts."""
    merged = merge_contacts(
        state["contacts_qdrant"],
        state["contacts_neo4j"],
        state["contacts_notion"]
    )
    return {"contacts_merged": merged}

def classify_contacts(state: ContactEnrichmentState) -> dict:
    """Apply 6-tier hierarchy classification."""
    from Engine3_OrgChart.scripts.contact_classifier import classify
    results = [classify(c) for c in state["contacts_merged"]]
    tier_1_3 = [c for c in results if c["tier"] in ["C-Suite", "VP/Director", "Program Manager"]]
    return {"classifications": results, "tier_1_3_contacts": tier_1_3}

def request_human_approval(state: ContactEnrichmentState) -> dict:
    """Pause for human review of Tier 1-3 classifications."""
    return {
        "awaiting_human_review": True,
        "human_review_type": "contact_approval",
    }

def execute_enrichment_updates(state: ContactEnrichmentState) -> dict:
    """Apply approved enrichment updates to all data stores."""
    approved_ids = state.get("approved_contacts", [])
    results = update_contacts_in_all_stores(approved_ids, state["classifications"])
    return {"enrichment_results": results}

def generate_enrichment_report(state: ContactEnrichmentState) -> dict:
    """Generate summary of enrichment run."""
    report = build_enrichment_report(state["enrichment_results"], state["classifications"])
    return {"report": report}
```

### Daily Scrape Nodes

```python
def configure_scrapers(state: DailyScrapeState) -> dict:
    """Load scraper configurations for 9 prime contractors."""
    configs = [
        {"name": "GDIT", "source": "careers.gdit.com"},
        {"name": "Leidos", "source": "careers.leidos.com"},
        {"name": "Northrop Grumman", "source": "jobs.northropgrumman.com"},
        {"name": "Raytheon", "source": "jobs.rtx.com"},
        {"name": "Booz Allen", "source": "careers.boozallen.com"},
        {"name": "SAIC", "source": "jobs.saic.com"},
        {"name": "ManTech", "source": "careers.mantech.com"},
        {"name": "Peraton", "source": "careers.peraton.com"},
        {"name": "L3Harris", "source": "careers.l3harris.com"},
    ]
    return {"scraper_configs": configs}

def execute_scrapers(state: DailyScrapeState) -> dict:
    """Run scrapers in parallel, collect results."""
    results = {}
    errors = {}
    total = 0
    for config in state["scraper_configs"]:
        try:
            jobs = run_apify_scraper(config)
            results[config["name"]] = jobs
            total += len(jobs)
        except Exception as e:
            errors[config["name"]] = str(e)
    return {"scrape_results": results, "scrape_errors": errors, "total_scraped": total}

def process_scraped_jobs(state: DailyScrapeState) -> dict:
    """Standardize, map, and score all scraped jobs."""
    all_jobs = []
    for jobs in state["scrape_results"].values():
        all_jobs.extend(jobs)

    standardized = standardize_batch(all_jobs)
    mapped = map_to_programs_batch(standardized)
    scored = score_batch(mapped)
    return {"standardized_jobs": standardized, "mapped_jobs": mapped, "scored_jobs": scored}

def index_and_alert(state: DailyScrapeState) -> dict:
    """Index new jobs and send hot lead alerts."""
    new_count = index_new_jobs(state["scored_jobs"])
    hot = [j for j in state["scored_jobs"] if j.get("bd_score", 0) >= 80]
    if hot:
        send_hot_lead_alerts(hot)
    return {"indexed_count": new_count, "new_jobs_count": new_count,
            "hot_leads": hot, "alerts_sent": bool(hot)}
```

---

## LANGGRAPH GRAPH DEFINITIONS

### 1. Master Pipeline Graph

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(MasterPipelineState)

# Nodes
graph.add_node("ingest", ingest_jobs)
graph.add_node("standardize", standardize_jobs)
graph.add_node("map_programs", map_to_programs)
graph.add_node("score", score_bd_priority)
graph.add_node("qa", run_qa_evaluation)
graph.add_node("briefing", generate_briefing)
graph.add_node("export", export_to_external)
graph.add_node("index", index_to_knowledge_base)

# Linear pipeline
graph.set_entry_point("ingest")
graph.add_edge("ingest", "standardize")
graph.add_edge("standardize", "map_programs")
graph.add_edge("map_programs", "score")
graph.add_edge("score", "qa")
graph.add_edge("qa", "briefing")
graph.add_edge("briefing", "export")
graph.add_edge("export", "index")
graph.add_edge("index", END)

master_pipeline = graph.compile(checkpointer=get_checkpointer())
```

### 2. Morning Briefing Graph

```python
graph = StateGraph(MorningBriefingState)

# Parallel gather nodes
graph.add_node("gather_pipeline", gather_pipeline_updates)
graph.add_node("gather_jobs", gather_new_jobs)
graph.add_node("gather_competitive", gather_competitive_intel)
graph.add_node("gather_contacts", gather_contact_changes)
graph.add_node("gather_graph", fetch_graph_insights)
graph.add_node("merge", merge_briefing)
graph.add_node("quality", quality_check)
graph.add_node("summary", generate_summary)

# Fan-out: entry → all 5 gather nodes in parallel
graph.set_entry_point("gather_pipeline")
for node in ["gather_pipeline", "gather_jobs", "gather_competitive",
             "gather_contacts", "gather_graph"]:
    graph.add_edge(node, "merge")

# Linear: merge → quality → summary
graph.add_edge("merge", "quality")
graph.add_edge("quality", "summary")
graph.add_edge("summary", END)

morning_briefing = graph.compile(checkpointer=get_checkpointer())
```

### 3. Contact Enrichment Graph (with human gate)

```python
graph = StateGraph(ContactEnrichmentState)

graph.add_node("validate", validate_enrichment_input)
graph.add_node("gather_qdrant", gather_from_qdrant)
graph.add_node("gather_neo4j", gather_from_neo4j)
graph.add_node("gather_notion", gather_from_notion)
graph.add_node("merge", merge_contact_data)
graph.add_node("classify", classify_contacts)
graph.add_node("request_approval", request_human_approval)
graph.add_node("execute", execute_enrichment_updates)
graph.add_node("report", generate_enrichment_report)

# Validate → parallel gather
graph.set_entry_point("validate")
for node in ["gather_qdrant", "gather_neo4j", "gather_notion"]:
    graph.add_edge("validate", node)
    graph.add_edge(node, "merge")

graph.add_edge("merge", "classify")

# Conditional: high-tier contacts need approval
def needs_approval(state: ContactEnrichmentState) -> str:
    if state.get("tier_1_3_contacts"):
        return "request_approval"
    return "execute"

graph.add_conditional_edges("classify", needs_approval, {
    "request_approval": "request_approval",
    "execute": "execute",
})

graph.add_edge("request_approval", "execute")  # Resumes after human feedback
graph.add_edge("execute", "report")
graph.add_edge("report", END)

contact_enrichment = graph.compile(
    checkpointer=get_checkpointer(),
    interrupt_before=["request_approval"],  # Human gate
)
```

### 4. Daily Scrape Graph

```python
graph = StateGraph(DailyScrapeState)

graph.add_node("configure", configure_scrapers)
graph.add_node("scrape", execute_scrapers)
graph.add_node("process", process_scraped_jobs)
graph.add_node("index_alert", index_and_alert)

graph.set_entry_point("configure")
graph.add_edge("configure", "scrape")
graph.add_edge("scrape", "process")
graph.add_edge("process", "index_alert")
graph.add_edge("index_alert", END)

daily_scrape = graph.compile(checkpointer=get_checkpointer())
```

### 5. Pipeline Manager Graph (with human gate)

```python
graph = StateGraph(PipelineManagerState)

graph.add_node("scan", scan_pipeline)
graph.add_node("stale", check_stale_items)
graph.add_node("deadlines", identify_deadlines)
graph.add_node("budget", analyze_budget_cycles)
graph.add_node("risk", risk_analysis)
graph.add_node("human_gate", request_action_approval)
graph.add_node("execute", execute_approved_actions)
graph.add_node("report", generate_pipeline_report)

graph.set_entry_point("scan")
graph.add_edge("scan", "stale")
graph.add_edge("stale", "deadlines")
graph.add_edge("deadlines", "budget")
graph.add_edge("budget", "risk")

# Conditional: critical risks need human approval
def has_critical_risks(state: PipelineManagerState) -> str:
    critical = [r for r in state.get("risks", []) if r.get("severity") == "critical"]
    return "human_gate" if critical else "execute"

graph.add_conditional_edges("risk", has_critical_risks, {
    "human_gate": "human_gate",
    "execute": "execute",
})

graph.add_edge("human_gate", "execute")
graph.add_edge("execute", "report")
graph.add_edge("report", END)

pipeline_manager = graph.compile(
    checkpointer=get_checkpointer(),
    interrupt_before=["human_gate"],
)
```

### 6. BD Proposal Graph (existing, from N8N-Builder)

```python
graph = StateGraph(BDProposalState)

graph.add_node("research", research_opportunity)
graph.add_node("contacts", gather_contacts)
graph.add_node("competition", analyze_competition)
graph.add_node("strategy", generate_strategy)
graph.add_node("request_review", request_human_review)
graph.add_node("process_feedback", process_human_feedback)
graph.add_node("finalize", finalize_playbook)
graph.add_node("revise", revise_strategy)

graph.set_entry_point("research")
graph.add_edge("research", "contacts")
graph.add_edge("contacts", "competition")
graph.add_edge("competition", "strategy")
graph.add_edge("strategy", "request_review")
graph.add_edge("request_review", "process_feedback")

def after_feedback(state: BDProposalState) -> str:
    decision = state.get("human_feedback", {}).get("decision", "abort")
    if decision == "approved":
        return "finalize"
    elif decision == "revise":
        return "revise"
    return END

graph.add_conditional_edges("process_feedback", after_feedback, {
    "finalize": "finalize",
    "revise": "revise",
    END: END,
})

graph.add_edge("revise", "strategy")  # Loop back
graph.add_edge("finalize", END)

bd_proposal = graph.compile(
    checkpointer=get_checkpointer(),
    interrupt_before=["process_feedback"],
)
```

---

## APSCHEDULER INTEGRATION

```python
"""Engine8_Knowledge/automation/unified_scheduler.py"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import uuid


def create_unified_scheduler() -> AsyncIOScheduler:
    """Create the master scheduler with all LangGraph workflows."""
    scheduler = AsyncIOScheduler(
        job_defaults={"coalesce": True, "max_instances": 1}
    )

    # ── Daily Workflows ──────────────────────────────────

    scheduler.add_job(
        invoke_workflow,
        trigger=CronTrigger(hour=5, minute=0),
        args=["daily_scrape", daily_scrape, {
            "workflow_id": f"scrape-{datetime.now():%Y%m%d}",
        }],
        id="daily_scrape",
        name="Daily Job Scraping (9 primes)",
    )

    scheduler.add_job(
        invoke_workflow,
        trigger=CronTrigger(hour=6, minute=30),
        args=["morning_briefing", morning_briefing, {
            "workflow_id": f"brief-{datetime.now():%Y%m%d}",
            "briefing_date": datetime.now().strftime("%Y-%m-%d"),
        }],
        id="morning_briefing",
        name="Morning BD Briefing",
    )

    scheduler.add_job(
        invoke_workflow,
        trigger=CronTrigger(hour=7, minute=0),
        args=["competitive_intel", competitive_intel, {
            "workflow_id": f"ci-{datetime.now():%Y%m%d}",
        }],
        id="competitive_scan",
        name="Daily Competitive Intelligence",
    )

    # ── Periodic Workflows ───────────────────────────────

    scheduler.add_job(
        invoke_workflow,
        trigger=IntervalTrigger(hours=2),
        args=["pipeline_health", pipeline_manager, {
            "workflow_id": f"ph-{uuid.uuid4().hex[:8]}",
        }],
        id="pipeline_health",
        name="Pipeline Health Check (every 2h)",
    )

    # ── Weekly Workflows ─────────────────────────────────

    scheduler.add_job(
        invoke_workflow,
        trigger=CronTrigger(day_of_week="mon", hour=2, minute=0),
        args=["contact_enrichment", contact_enrichment, {
            "workflow_id": f"enrich-{datetime.now():%Y%m%d}",
        }],
        id="contact_enrichment",
        name="Weekly Contact Enrichment (Mon 2 AM)",
    )

    scheduler.add_job(
        invoke_workflow,
        trigger=CronTrigger(day_of_week="fri", hour=16, minute=0),
        args=["weekly_report", weekly_report, {
            "workflow_id": f"wr-{datetime.now():%Y%m%d}",
        }],
        id="weekly_report",
        name="Weekly Performance Report (Fri 4 PM)",
    )

    # ── Monthly Workflows ────────────────────────────────

    scheduler.add_job(
        invoke_workflow,
        trigger=CronTrigger(day=1, hour=3, minute=0),
        args=["monthly_retrain", monthly_retrain, {
            "workflow_id": f"retrain-{datetime.now():%Y%m}",
        }],
        id="monthly_retrain",
        name="Monthly ML Model Retraining (1st 3 AM)",
    )

    # ── Master Pipeline (on-demand with polling) ─────────

    scheduler.add_job(
        invoke_workflow,
        trigger=IntervalTrigger(hours=6),
        args=["master_pipeline", master_pipeline, {
            "workflow_id": f"pipe-{uuid.uuid4().hex[:8]}",
            "input_file": find_latest_input_file(),
        }],
        id="master_pipeline",
        name="Master BD Pipeline (6h interval)",
    )

    return scheduler


async def invoke_workflow(name: str, compiled_graph, initial_state: dict):
    """Execute a LangGraph workflow with error handling and logging."""
    thread_id = initial_state.get("workflow_id", str(uuid.uuid4()))
    config = {"configurable": {"thread_id": thread_id}}

    try:
        logger.info(f"Starting workflow: {name} (thread: {thread_id})")
        result = await compiled_graph.ainvoke(initial_state, config=config)
        logger.info(f"Completed workflow: {name} — status: {result.get('status', 'done')}")
        log_workflow_run(name, thread_id, "success", result)
    except Exception as e:
        logger.error(f"Workflow {name} failed: {e}")
        log_workflow_run(name, thread_id, "failed", {"error": str(e)})
        # Send alert for critical failures
        if name in ["master_pipeline", "daily_scrape", "morning_briefing"]:
            send_failure_alert(name, str(e))
```

---

## CREWAI AGENT MIGRATION

### Current CrewAI Agents (5)

| Agent | Role | LangGraph Mapping |
|-------|------|------------------|
| `program_researcher` | Research federal program details | → `research_opportunity` node |
| `contact_enricher` | Build contact profiles (Tier 1-6) | → `gather_contacts` + `classify_contacts` nodes |
| `competitive_analyst` | Competitive landscape analysis | → `analyze_competition` node |
| `outreach_composer` | Personalized outreach drafting | → `generate_outreach` node |
| `synthesis_agent` | Compile all results | → `finalize_playbook` node |

### Migration Decision

| Agent | Recommendation | Rationale |
|-------|---------------|-----------|
| program_researcher | **Convert to LangGraph node** | Deterministic workflow, no multi-turn reasoning needed |
| contact_enricher | **Convert to LangGraph node** | Structured data merging, better as pipeline step |
| competitive_analyst | **Keep as CrewAI, call from LangGraph** | Benefits from multi-agent debate, complex reasoning |
| outreach_composer | **Keep as CrewAI, call from LangGraph** | Creative writing benefits from agent iteration |
| synthesis_agent | **Convert to LangGraph node** | Simple aggregation, no agent reasoning needed |

### Hybrid Pattern: CrewAI Inside LangGraph

```python
def analyze_competition_node(state: BDProposalState) -> dict:
    """LangGraph node that invokes CrewAI for complex analysis."""
    try:
        from Engine8_Knowledge.agents.crews import get_competitive_crew
        crew = get_competitive_crew()
        result = crew.kickoff(inputs={
            "incumbent": state["incumbent_info"],
            "market": state["market_intelligence"],
            "contacts": state["contacts_crm"],
        })
        return {
            "competitor_analysis": result.raw,
            "win_probability": extract_win_probability(result.raw),
        }
    except ImportError:
        # Fallback: single LLM call if CrewAI unavailable
        return fallback_competitive_analysis(state)
```

---

## UNIFIED ORCHESTRATOR

### Master Scheduler Configuration

```python
"""All workflows registered in one place."""

WORKFLOW_REGISTRY = {
    # Critical (alerts on failure)
    "master_pipeline": {
        "graph": master_pipeline,
        "schedule": "0 */6 * * *",      # Every 6 hours
        "priority": "critical",
        "timeout_minutes": 60,
        "retry_policy": {"max_attempts": 3, "backoff_seconds": 300},
    },
    "daily_scrape": {
        "graph": daily_scrape,
        "schedule": "0 5 * * *",         # 5 AM daily
        "priority": "critical",
        "timeout_minutes": 45,
        "retry_policy": {"max_attempts": 3, "backoff_seconds": 120},
    },
    "morning_briefing": {
        "graph": morning_briefing,
        "schedule": "30 6 * * *",        # 6:30 AM daily
        "priority": "critical",
        "timeout_minutes": 15,
        "retry_policy": {"max_attempts": 2, "backoff_seconds": 60},
    },

    # High (logged, retried)
    "contact_enrichment": {
        "graph": contact_enrichment,
        "schedule": "0 2 * * 1",         # Monday 2 AM
        "priority": "high",
        "timeout_minutes": 120,
        "retry_policy": {"max_attempts": 2, "backoff_seconds": 600},
        "has_human_gate": True,
    },
    "competitive_intel": {
        "graph": competitive_intel,
        "schedule": "0 7 * * *",         # 7 AM daily
        "priority": "high",
        "timeout_minutes": 30,
        "retry_policy": {"max_attempts": 2, "backoff_seconds": 120},
    },
    "pipeline_manager": {
        "graph": pipeline_manager,
        "schedule": "0 */2 * * *",       # Every 2 hours
        "priority": "high",
        "timeout_minutes": 10,
        "retry_policy": {"max_attempts": 1, "backoff_seconds": 0},
        "has_human_gate": True,
    },

    # Normal (logged)
    "weekly_report": {
        "graph": weekly_report,
        "schedule": "0 16 * * 5",        # Friday 4 PM
        "priority": "normal",
        "timeout_minutes": 20,
    },
    "monthly_retrain": {
        "graph": monthly_retrain,
        "schedule": "0 3 1 * *",         # 1st of month 3 AM
        "priority": "normal",
        "timeout_minutes": 180,
    },

    # On-demand only (no schedule)
    "bd_proposal": {
        "graph": bd_proposal,
        "schedule": None,
        "priority": "high",
        "timeout_minutes": 30,
        "has_human_gate": True,
    },
    "contact_outreach": {
        "graph": contact_outreach,
        "schedule": None,
        "priority": "normal",
        "timeout_minutes": 15,
        "has_human_gate": True,
    },
}
```

### Workflow Dependency Graph

```
daily_scrape (05:00)
  ↓ (produces new jobs)
morning_briefing (06:30)
  ↓ (uses latest data)
competitive_intel (07:00)
  │
  ├── pipeline_manager (every 2h, independent)
  │
  └── master_pipeline (every 6h, re-processes all)

contact_enrichment (Mon 02:00) ─── independent cycle
weekly_report (Fri 16:00) ──────── summarizes week
monthly_retrain (1st 03:00) ────── independent cycle

On-demand:
  bd_proposal ← API trigger
  contact_outreach ← API trigger
  recompete_monitor ← API trigger
```

### Error Recovery and Retry Policies

```python
class RetryPolicy:
    max_attempts: int = 3
    backoff_seconds: float = 60
    backoff_multiplier: float = 2.0    # Exponential backoff
    max_backoff_seconds: float = 3600  # Cap at 1 hour
    retry_on: tuple = (ConnectionError, TimeoutError, IOError)
    alert_after_failures: int = 2      # Send alert after N consecutive failures

class WorkflowExecutor:
    async def execute_with_retry(self, workflow_name: str):
        config = WORKFLOW_REGISTRY[workflow_name]
        policy = config.get("retry_policy", RetryPolicy())

        for attempt in range(policy.max_attempts):
            try:
                result = await asyncio.wait_for(
                    config["graph"].ainvoke(initial_state, graph_config),
                    timeout=config["timeout_minutes"] * 60,
                )
                self.record_success(workflow_name, result)
                return result
            except policy.retry_on as e:
                wait = min(
                    policy.backoff_seconds * (policy.backoff_multiplier ** attempt),
                    policy.max_backoff_seconds,
                )
                logger.warning(f"{workflow_name} attempt {attempt+1} failed: {e}. Retry in {wait}s")
                await asyncio.sleep(wait)
            except Exception as e:
                self.record_failure(workflow_name, str(e))
                if attempt >= policy.alert_after_failures:
                    await self.send_failure_alert(workflow_name, str(e))
                raise
```

### Monitoring and Alerting Integration

```python
class WorkflowMonitor:
    """Tracks workflow health and sends alerts."""

    def get_dashboard_data(self) -> dict:
        """Data for the monitoring dashboard."""
        return {
            "workflows": {
                name: {
                    "last_run": self.get_last_run(name),
                    "status": self.get_status(name),
                    "avg_duration": self.get_avg_duration(name),
                    "failure_rate": self.get_failure_rate(name),
                    "next_scheduled": self.get_next_run(name),
                    "pending_reviews": self.get_pending_reviews(name),
                }
                for name in WORKFLOW_REGISTRY
            },
            "alerts": self.get_active_alerts(),
            "system_health": {
                "qdrant": check_qdrant_health(),
                "neo4j": check_neo4j_health(),
                "scheduler": scheduler.running,
            },
        }

    async def send_failure_alert(self, workflow: str, error: str):
        """Send alert via Slack and email."""
        from Engine8_Knowledge.integrations.slack_integration import get_slack_bot
        bot = get_slack_bot()
        bot.send_notification(
            channel="#bd-alerts",
            message=f"Workflow FAILED: {workflow}\nError: {error}",
        )

    async def send_human_gate_notification(self, workflow: str, review_type: str):
        """Notify team when a workflow is waiting for human approval."""
        bot = get_slack_bot()
        bot.send_notification(
            channel="#bd-approvals",
            message=f"Approval needed: {workflow} ({review_type})",
            blocks=[{
                "type": "actions",
                "elements": [{
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Review Now"},
                    "url": f"http://localhost:5173/workflows/{workflow}/review",
                }],
            }],
        )
```

---

## N8N DECOMMISSION PLAN

### N8N Workflows → LangGraph Mapping

| N8N Workflow | LangGraph Replacement | Status |
|---|---|---|
| WF1_Apify_Job_Scraper_Intake | `daily_scrape` graph | Ready |
| WF2_AI_Enrichment_Processor | `contact_enrichment` graph | Ready |
| WF3_Hub_to_BD_Opportunities | `master_pipeline.export` node | Ready |
| WF4_Contact_Classification | `contact_enrichment.classify` node | Ready |
| WF5_Hot_Lead_Alerts | `daily_scrape.index_alert` node | Ready |
| WF6_Weekly_Summary_Report | `weekly_report` graph | Ready |
| BD_Master_Orchestration | `master_pipeline` graph | Ready |
| Agent workflows | CrewAI inside LangGraph nodes | Ready |

### Decommission Steps

1. **Week 1:** Run LangGraph and N8N in parallel (dual webhook delivery)
2. **Week 2:** Compare outputs, fix any discrepancies
3. **Week 3:** Route 100% traffic to LangGraph, N8N on standby
4. **Week 4:** Archive N8N workflow JSONs, shut down N8N instance
5. Delete `n8n/` directory and N8N webhook references

---

*15 workflows consolidated into 10 LangGraph graphs + 1 APScheduler master + CrewAI hybrid nodes. N8N fully replaced. Human-in-the-loop gates on 4 workflows.*
