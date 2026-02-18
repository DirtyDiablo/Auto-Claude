# LangGraph Workflows Documentation

## Overview

The `bd_langgraph/` module implements production-ready state machine workflows using LangGraph for Business Development automation. These workflows support:

- **Human-in-the-loop approvals** - Pause execution for human review
- **Durable checkpointing** - SQLite persistence survives restarts
- **Incremental execution** - Resume from any checkpoint
- **N8N integration** - Trigger and monitor via webhooks

---

## Architecture

```
bd_langgraph/
├── states.py           # State dataclasses for each workflow
├── nodes.py            # Node functions (workflow steps)
├── edges.py            # Conditional routing logic
├── checkpointer.py     # SQLite persistence layer
├── human_in_loop.py    # File-based review system
├── integrations.py     # API wrappers (Tango, SAM.gov, CRM)
├── bd_workflows.py     # BD Proposal Pipeline
├── contact_workflows.py # Contact Outreach Workflow
├── pipeline_workflows.py# Weekly Pipeline Workflow
└── recompete_workflows.py# Recompete Intelligence Workflow
```

### Data Flow

```
User Request
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Workflow Graph (StateGraph)                    │
│  ┌─────────┐   ┌─────────┐   ┌─────────────┐   │
│  │  Node   │──▶│  Node   │──▶│ Human Review│   │
│  │(function)│   │(function)│   │  (interrupt)│   │
│  └─────────┘   └─────────┘   └──────┬──────┘   │
│                                      │          │
│                              ┌───────▼───────┐  │
│                              │ Review File   │  │
│                              │ (data/human_  │  │
│                              │  reviews/*.json)│ │
│                              └───────┬───────┘  │
│                                      │          │
│  ┌─────────┐   ┌─────────┐   ┌──────▼──────┐   │
│  │  Node   │◀──│  Edge   │◀──│  Feedback   │   │
│  │(finalize)│   │(routing)│   │ (resume)    │   │
│  └─────────┘   └─────────┘   └─────────────┘   │
└─────────────────────────────────────────────────┘
    │
    ▼
Checkpointer (SQLite)
```

---

## Module Reference

### 1. states.py - Workflow State Definitions

**Purpose**: Define typed state dataclasses for each workflow.

#### Classes

| Class | Purpose | Key Fields |
|-------|---------|------------|
| `WorkflowStatus` | Enum of statuses | `PENDING`, `IN_PROGRESS`, `AWAITING_HUMAN_REVIEW`, `COMPLETED`, `FAILED`, `ABORTED` |
| `HumanReviewType` | Review gate types | `STRATEGY_APPROVAL`, `CONTACT_APPROVAL`, `PLAYBOOK_APPROVAL`, `CAPTURE_DECISION` |
| `BaseWorkflowState` | Base class | `workflow_id`, `thread_id`, `status`, `completed_nodes`, `human_feedback` |
| `BDProposalState` | BD Pipeline | `opportunity_title`, `contacts_gathered`, `bd_strategy`, `final_playbook` |
| `ContactOutreachState` | Contact workflow | `target_company`, `discovered_contacts`, `outreach_materials` |
| `RecompeteState` | Recompete monitoring | `monitored_contracts`, `recompete_signals`, `capture_plans` |
| `WeeklyPipelineState` | Weekly reports | `raw_opportunities`, `scored_opportunities`, `weekly_report` |

#### Usage

```python
from bd_langgraph.states import BDProposalState, WorkflowStatus

state = BDProposalState(
    workflow_id="bd_abc123",
    opportunity_title="DoD Cyber Contract",
    agency="Department of Defense"
)
state.set_status(WorkflowStatus.IN_PROGRESS)
```

---

### 2. nodes.py - Workflow Node Functions

**Purpose**: Implement individual workflow steps. Each node receives state dict, performs work, returns updated fields.

#### BD Proposal Pipeline Nodes

| Node | Purpose | Input | Output |
|------|---------|-------|--------|
| `research_opportunity` | Find similar contracts, market intel | `naics_codes`, `agency` | `similar_contracts`, `market_intelligence` |
| `gather_contacts` | Search CRM, SAM, job postings | `agency`, `incumbent_info` | `contacts_gathered`, `prioritized_contacts` |
| `analyze_competition` | Competitive landscape analysis | `naics_codes`, `similar_contracts` | `competitor_analysis`, `win_probability` |
| `generate_strategy` | Build BD strategy | All gathered intel | `bd_strategy`, `win_themes`, `differentiators` |
| `request_human_review` | Create review request | `bd_strategy` | `awaiting_human_review=True` |
| `process_human_feedback` | Process approval decision | `human_feedback` | `strategy_approved`, route decision |
| `finalize_playbook` | Generate final playbook | Approved strategy | `final_playbook`, `playbook_path` |

#### Contact Outreach Nodes

| Node | Purpose |
|------|---------|
| `discover_contacts` | Find contacts from multiple sources |
| `score_and_prioritize_contacts` | Rank contacts by relevance |
| `request_contact_approval` | Request human approval of contact list |
| `generate_outreach_materials` | Create emails, LinkedIn messages |

#### Recompete Intelligence Nodes

| Node | Purpose |
|------|---------|
| `monitor_contracts` | Check contract status via FPDS |
| `detect_recompete_signals_node` | Identify expiring/recompete signals |
| `generate_alert` | Create priority alerts |
| `prepare_capture` | Generate capture plans |

#### Weekly Pipeline Nodes

| Node | Purpose |
|------|---------|
| `scrape_opportunities_node` | Gather from SAM.gov |
| `enrich_opportunities` | Add market/incumbent data |
| `score_and_rank` | Score and prioritize |
| `generate_report` | Create weekly report |

---

### 3. edges.py - Conditional Routing

**Purpose**: Determine next node based on state. Used with `add_conditional_edges()`.

#### Key Edge Functions

```python
def should_continue_after_review(state) -> Literal["finalize", "revise", "abort"]:
    """Route based on human feedback decision."""
    decision = state.get('human_feedback', {}).get('decision', 'abort')
    if decision == 'approve': return "finalize"
    elif decision == 'revise': return "revise"
    else: return "abort"

def has_contacts_for_review(state) -> Literal["request_approval", "generate"]:
    """Check if contacts need human approval."""
    if state.get('auto_approve_contacts', False): return "generate"
    if not state.get('scored_contacts'): return "generate"
    return "request_approval"

def should_generate_alert(state) -> Literal["generate_alert", "complete"]:
    """Check if alerts should be created."""
    return "generate_alert" if state.get('recompete_signals') else "complete"
```

---

### 4. checkpointer.py - State Persistence

**Purpose**: SQLite-based durable checkpointing for workflow state.

#### Functions

| Function | Purpose |
|----------|---------|
| `get_checkpointer(db_path)` | Get SQLite checkpointer (production) |
| `get_memory_checkpointer()` | Get in-memory checkpointer (testing) |

#### CheckpointManager Class

```python
from bd_langgraph.checkpointer import CheckpointManager

manager = CheckpointManager()

# Register workflow
manager.register_workflow(thread_id, 'bd_proposal', workflow_id)

# Update status
manager.update_workflow_status(thread_id, 'completed')

# List workflows
workflows = manager.list_workflows(workflow_type='bd_proposal', status='in_progress')

# Get pending reviews
pending = manager.get_pending_reviews()

# Get statistics
stats = manager.get_stats()
# Returns: {'total': 15, 'by_status': {...}, 'by_type': {...}}

# Cleanup old data
deleted = manager.cleanup_old_workflows(days_old=30)
```

#### Database Location

Default: `data/langgraph_checkpoints.db`

---

### 5. human_in_loop.py - Human Review System

**Purpose**: File-based human review gates for async approval.

#### Creating a Review Request

```python
from bd_langgraph.human_in_loop import create_review_request
from bd_langgraph.states import HumanReviewType

request = create_review_request(
    workflow_id="bd_abc123",
    review_type=HumanReviewType.STRATEGY_APPROVAL,
    review_data={
        'opportunity_title': 'DoD Cyber Contract',
        'win_probability': 0.65,
        'win_themes': ['Innovation', 'Cost Savings']
    },
    instructions="Review the BD strategy and approve or request revisions."
)
# Creates: data/human_reviews/review_abc123.json
# Creates: data/human_reviews/review_abc123_PENDING.md (human-readable)
```

#### Submitting a Review

```python
from bd_langgraph.human_in_loop import submit_review

# Option 1: Via Python API
updated = submit_review(
    request_id="abc123",
    decision="approve",  # or "reject", "revise", "abort"
    notes="Looks good, proceed with capture.",
    reviewer="John Smith"
)

# Option 2: Edit JSON file directly
# Set "decision": "approve" and "status": "approved"
```

#### Checking Review Status

```python
from bd_langgraph.human_in_loop import (
    get_pending_reviews,
    check_review_status,
    get_feedback_for_resume
)

# Get all pending reviews
pending = get_pending_reviews()

# Check specific review
status = check_review_status("abc123")
# Returns: {'found': True, 'status': 'pending', 'is_pending': True, ...}

# Get feedback for workflow resume
feedback = get_feedback_for_resume("abc123")
# Returns: {'decision': 'approve', 'notes': '...', ...}
```

---

### 6. integrations.py - External API Wrappers

**Purpose**: Abstract external APIs for use by nodes.

#### Available Functions

| Function | Purpose | Data Sources |
|----------|---------|--------------|
| `search_similar_contracts()` | Find related contracts | USASpending, Tango |
| `search_opportunities()` | Find SAM.gov opportunities | SAM.gov |
| `get_market_intelligence()` | Market size, competition | FPDS, Tango |
| `search_crm_contacts()` | CRM contact search | Bullhorn/CRM |
| `get_sam_entity_contacts()` | SAM.gov entity contacts | SAM.gov |
| `search_job_posting_contacts()` | Contacts from job posts | Apify/job boards |
| `score_contacts()` | Prioritize contacts | Internal scoring |
| `analyze_incumbent()` | Incumbent analysis | SAM.gov, USASpending |
| `get_competitive_landscape()` | Find competitors | FPDS, USASpending |
| `calculate_win_probability()` | P(win) calculation | All sources |
| `build_bd_strategy()` | Generate strategy | All intel |
| `generate_bd_playbook()` | Create playbook doc | Strategy data |
| `score_opportunity()` | Score single opp | Internal algorithm |
| `check_contract_status()` | Contract status check | FPDS |
| `detect_recompete_signals()` | Find recompete signals | Contract data |

---

## Workflow Reference

### 1. BD Proposal Pipeline

**File**: `bd_workflows.py`

**Pipeline**: Research → Contacts → Competition → Strategy → Human Review → Playbook

```python
from bd_langgraph.bd_workflows import run_bd_proposal_workflow, resume_bd_proposal_workflow

# Start workflow
result = run_bd_proposal_workflow(
    opportunity_id="OPP_123",
    opportunity_title="DoD Cybersecurity Support",
    agency="Department of Defense",
    naics_codes=["541512", "541519"],
    target_value=10_000_000,
    incumbent_name="Acme Corp"
)

# If awaiting review
if result['status'] == 'awaiting_human_review':
    print(f"Review needed: {result['review_request_id']}")

    # After human approves...
    final = resume_bd_proposal_workflow(
        thread_id=result['thread_id'],
        human_feedback={'decision': 'approve', 'notes': 'Proceed'}
    )
```

### 2. Contact Outreach Workflow

**File**: `contact_workflows.py`

**Pipeline**: Discover → Score → Approve → Generate Materials

```python
from bd_langgraph.contact_workflows import run_contact_outreach_workflow

result = run_contact_outreach_workflow(
    target_company="Lockheed Martin",
    target_program="F-35 Sustainment",
    outreach_goal="meeting",
    max_contacts=20,
    auto_approve=False  # Require human approval
)
```

### 3. Weekly Pipeline Workflow

**File**: `pipeline_workflows.py`

**Pipeline**: Scrape → Enrich → Score → Report

```python
from bd_langgraph.pipeline_workflows import (
    run_weekly_pipeline_workflow,
    configure_weekly_pipeline
)

# Configure for scheduled runs
configure_weekly_pipeline(
    target_naics=["541512", "541519"],
    min_value=1_000_000,
    date_range_days=7
)

# Run manually
result = run_weekly_pipeline_workflow(
    target_naics=["541512"],
    date_range_days=7,
    skip_enrichment=False
)

print(f"Found {result['opportunities_found']} opportunities")
print(f"Report: {result['report_path']}")
```

### 4. Recompete Intelligence Workflow

**File**: `recompete_workflows.py`

**Pipeline**: Monitor → Detect → Alert → Capture

```python
from bd_langgraph.recompete_workflows import (
    run_recompete_workflow,
    add_contract_to_monitoring
)

# Add contracts to monitor
add_contract_to_monitoring("CONT_ABC123", alert_threshold_days=365)
add_contract_to_monitoring("CONT_DEF456", alert_threshold_days=180)

# Run check
result = run_recompete_workflow(
    contract_ids=["CONT_ABC123", "CONT_DEF456"],
    alert_threshold_days=365,
    auto_prepare=True  # Auto-create capture plans
)

print(f"Signals detected: {result['signals_detected']}")
print(f"Alerts: {result['alerts_generated']}")
```

---

## Human-in-the-Loop Usage

### Review Flow

```
1. Workflow reaches human review gate
   └── Creates review file: data/human_reviews/review_<id>.json
   └── Creates readable file: data/human_reviews/review_<id>_PENDING.md
   └── Workflow state persisted to SQLite
   └── Returns status: 'awaiting_human_review'

2. Human reviews and decides
   └── Option A: Edit JSON file directly
   └── Option B: Use submit_review() API
   └── Option C: External system (N8N, email)

3. Resume workflow with feedback
   └── Call resume_*_workflow(thread_id, human_feedback)
   └── Workflow continues from checkpoint
```

### Review Request JSON Format

```json
{
  "request_id": "abc123def456",
  "workflow_id": "bd_xyz789",
  "review_type": "strategy_approval",
  "status": "pending",
  "created_at": "2026-02-04T10:00:00",
  "review_data": {
    "opportunity_title": "DoD Cyber Contract",
    "win_probability": 0.65,
    "win_themes": ["Innovation", "Cost Savings"]
  },
  "instructions": "Review the BD strategy...",
  "decision": null,
  "feedback_notes": null
}
```

### Submitting Review (Decision Options)

| Decision | Effect |
|----------|--------|
| `approve` | Continue workflow to finalization |
| `revise` | Loop back to strategy generation |
| `reject` | Abort workflow |
| `abort` | Abort workflow |

---

## Checkpointer Usage

### Persistence Behavior

- **SQLite storage**: All state persisted to `data/langgraph_checkpoints.db`
- **Automatic checkpoints**: After each node execution
- **Thread isolation**: Each workflow run has unique `thread_id`
- **Resume capability**: Can resume from any checkpoint

### Listing Workflows

```python
from bd_langgraph.checkpointer import CheckpointManager

manager = CheckpointManager()

# All workflows
all_workflows = manager.list_workflows(limit=50)

# Filter by type
bd_workflows = manager.list_workflows(workflow_type='bd_proposal')

# Filter by status
pending_review = manager.list_workflows(status='awaiting_human_review')

# Get specific workflow
workflow = manager.get_workflow(thread_id="thread_bd_abc123")
```

### Cleanup

```python
# Delete workflows older than 30 days
deleted_count = manager.cleanup_old_workflows(days_old=30)

# Delete specific workflow
manager.delete_workflow(thread_id="thread_bd_abc123")
```

---

## N8N Integration

### Triggering Workflows

Create N8N workflow with HTTP Request node:

```javascript
// POST to local API (if running bd_langgraph API)
{
  "url": "http://localhost:8000/workflows/bd_proposal",
  "method": "POST",
  "body": {
    "opportunity_id": "{{ $json.opportunity_id }}",
    "opportunity_title": "{{ $json.title }}",
    "agency": "{{ $json.agency }}",
    "naics_codes": ["541512"]
  }
}
```

### Checking Status

```javascript
// GET workflow status
{
  "url": "http://localhost:8000/workflows/status/{{ $json.thread_id }}",
  "method": "GET"
}
```

### Processing Human Reviews

N8N can monitor the `data/human_reviews/` directory for pending reviews and send notifications:

1. Watch folder for new `*_PENDING.md` files
2. Send Slack/email notification
3. Wait for approval via form/button
4. Call `submit_review()` endpoint
5. Trigger workflow resume

---

## Testing

### Run Import Test

```bash
cd C:\Auto-Claud\N8N-Builder
python -c "
from bd_langgraph.states import BDProposalState, WorkflowStatus
from bd_langgraph.nodes import research_opportunity
from bd_langgraph.edges import should_continue_after_review
from bd_langgraph.checkpointer import get_memory_checkpointer
from bd_langgraph.human_in_loop import create_review_request
from bd_langgraph.bd_workflows import run_bd_proposal_workflow

print('All imports successful!')
"
```

### Run Unit Tests

```bash
cd C:\Auto-Claud\N8N-Builder
python -m pytest bd_langgraph/test_langgraph.py -v
```

---

## Configuration

### Environment Variables

```bash
# Optional - if using external APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
TANGO_API_KEY=...
```

### Default Paths

| Path | Purpose |
|------|---------|
| `data/langgraph_checkpoints.db` | SQLite checkpoint database |
| `data/human_reviews/` | Human review files |
| `data/playbooks/` | Generated BD playbooks |
| `data/reports/` | Weekly pipeline reports |
| `data/pipeline_config.json` | Weekly pipeline configuration |
| `data/recompete_monitoring.json` | Monitored contracts list |

---

## Summary

| Module | Lines | Key Exports |
|--------|-------|-------------|
| states.py | 315 | `BDProposalState`, `WorkflowStatus`, `HumanReviewType` |
| nodes.py | 975 | 19 node functions for all workflows |
| edges.py | 306 | 11 conditional edge functions |
| checkpointer.py | 348 | `get_checkpointer`, `CheckpointManager` |
| human_in_loop.py | 565 | `create_review_request`, `submit_review`, `get_pending_reviews` |
| integrations.py | 600+ | 16 API wrapper functions |
| bd_workflows.py | 370 | `run_bd_proposal_workflow`, `resume_bd_proposal_workflow` |
| contact_workflows.py | 288 | `run_contact_outreach_workflow` |
| pipeline_workflows.py | 338 | `run_weekly_pipeline_workflow`, `configure_weekly_pipeline` |
| recompete_workflows.py | 321 | `run_recompete_workflow`, `add_contract_to_monitoring` |

**Total**: ~4,400 lines of production-ready workflow code.
