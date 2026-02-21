# Engine 6 — QA & Alerts

Quality assurance gating, alert rules, and live data quality monitoring across the full pipeline.

## Scripts

| Script | Purpose |
|--------|---------|
| `quality_monitor.py` | Live health checks for Qdrant collections — vector counts, index status, data completeness |
| `alerts.py` | Alert engine with 4 rules + 60-minute cooldown + Slack/n8n delivery |
| `qa_feedback.py` | QA gating with root cause analysis, confidence thresholds, auto-fix detection |

## Alert Rules

| Rule | Trigger | Severity |
|------|---------|----------|
| High-Priority Contacts | Tier 1-2 contacts added | Critical |
| Job Count Anomalies | >20% deviation from baseline | Warning |
| Pipeline Stage Failures | Stage execution errors | Error |
| Search Quality Degradation | Mean relevance below threshold | Warning |

## QA Gating

| Confidence | Action |
|------------|--------|
| ≥0.70 | Auto-approve |
| 0.50–0.70 | Manual review |
| <0.50 | Reject |

Root cause analysis returns: issue type, severity (low/medium/high/critical), affected fields, recommended fix, auto-fixable flag.

## Quality Monitor

Tracks 9 collections: contacts, programs, documents, activities, jobs, bullhorn_notes, federal_contracts, intelligence_reports, opportunities.

Reports vector count, segment count, optimization status, and data completeness percentage.

## Running

```python
# Quality monitoring
from Engine6_QA.quality_monitor import QualityMonitor
monitor = QualityMonitor()
report = monitor.generate_report()

# Alerting
from Engine6_QA.scripts.alerts import AlertEngine
engine = AlertEngine()
alerts = engine.evaluate_all_rules()
engine.deliver_notifications(alerts)

# QA Feedback
from Engine6_QA.scripts.qa_feedback import analyze_root_cause
root_cause = analyze_root_cause(job_data)
```

## Environment Variables

```
QDRANT_URL=http://localhost:6333   # Vector DB
QDRANT_API_KEY=                    # Optional auth
SLACK_WEBHOOK_URL=                 # Optional Slack notifications
N8N_ALERT_WEBHOOK=                 # Optional n8n webhook
```

## Dependencies

- **Input from:** Engines 2-5 (all pipeline stages)
- **Requires:** Qdrant client
- **Feeds:** Dashboard/monitoring, manual review queues
