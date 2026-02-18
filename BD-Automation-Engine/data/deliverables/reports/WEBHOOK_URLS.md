# N8N Builder - Webhook URL Reference

## Base URL
**Production**: `https://primetech.app.n8n.cloud/webhook`
**Test Mode**: `https://primetech.app.n8n.cloud/webhook-test`

---

## Hub Integration Workflows

| Workflow | Webhook Path | Method | Description |
|----------|--------------|--------|-------------|
| Hub Smart Query | `/webhook/hub-query` | POST | Query BD Hub with intelligent routing |
| Hub Search | `/webhook/hub-search` | GET | Search Hub knowledge base |
| Hub Ingest Jobs | `/webhook/ingest-jobs` | POST | Ingest job postings to Hub |
| Hub Add Insight | `/webhook/add-insight` | POST | Add BD insight to Hub memory |

### Hub Smart Query
```bash
curl -X POST https://primetech.app.n8n.cloud/webhook/hub-query \
  -H "Content-Type: application/json" \
  -d '{"query": "DCGS programs clearance requirements", "use_cache": true}'
```

### Hub Search
```bash
curl "https://primetech.app.n8n.cloud/webhook/hub-search?q=engineer&collection=bd_knowledge&limit=10"
```

### Hub Ingest Jobs
```bash
curl -X POST https://primetech.app.n8n.cloud/webhook/ingest-jobs \
  -H "Content-Type: application/json" \
  -d '{"jobs": [{"title": "Systems Engineer", "company": "SAIC", "location": "Washington DC", "clearance": "TS/SCI"}]}'
```

### Hub Add Insight
```bash
curl -X POST https://primetech.app.n8n.cloud/webhook/add-insight \
  -H "Content-Type: application/json" \
  -d '{"insight_type": "opportunity", "insight": "New RFP expected Q2", "confidence": 0.8}'
```

---

## Scraper Workflows

| Workflow | Webhook Path | Method | Description |
|----------|--------------|--------|-------------|
| Trigger Scrape | `/webhook/trigger-scrape` | POST | Trigger single source scraper |
| Full Pipeline | `/webhook/full-pipeline` | POST | Run full scrape-sync pipeline |
| Scraper Complete | `/webhook/scraper-complete` | POST | Callback from scraper completion |

### Trigger Scrape
```bash
curl -X POST https://primetech.app.n8n.cloud/webhook/trigger-scrape \
  -H "Content-Type: application/json" \
  -d '{"source": "apex-jobs", "locations": ["Washington DC", "Virginia"], "max_items": 100}'
```

### Full Pipeline
```bash
curl -X POST https://primetech.app.n8n.cloud/webhook/full-pipeline \
  -H "Content-Type: application/json" \
  -d '{"include_insights": true}'
```

---

## Notion Workflows

| Workflow | Webhook Path | Method | Description |
|----------|--------------|--------|-------------|
| Sync Jobs to Notion | `/webhook/sync-jobs-notion` | POST | Export jobs from Hub to Notion |
| Notion to Hub | `/webhook/notion-to-hub` | POST | Import from Notion to Hub |

### Sync Jobs to Notion
```bash
curl -X POST https://primetech.app.n8n.cloud/webhook/sync-jobs-notion \
  -H "Content-Type: application/json" \
  -d '{"query": "clearance:TS/SCI", "limit": 50}'
```

---

## Alert Workflows

| Workflow | Webhook Path | Method | Description |
|----------|--------------|--------|-------------|
| Slack Alert | `/webhook/slack-alert` | POST | Send Slack notification |
| Error Notification | `/webhook/error-notification` | POST | Log and notify errors |

### Slack Alert
```bash
curl -X POST https://primetech.app.n8n.cloud/webhook/slack-alert \
  -H "Content-Type: application/json" \
  -d '{"message": "New high-value opportunity detected", "severity": "info", "channel": "#bd-updates"}'
```

**Severity Levels**: `info`, `success`, `warning`, `error`, `critical`

### Error Notification
```bash
curl -X POST https://primetech.app.n8n.cloud/webhook/error-notification \
  -H "Content-Type: application/json" \
  -d '{"workflow_name": "Daily Scrape", "error_message": "Connection timeout", "node_name": "HTTP Request"}'
```

---

## Pipeline Workflows

| Workflow | Webhook Path | Method | Description |
|----------|--------------|--------|-------------|
| BD Pipeline | `/webhook/bd-pipeline` | POST | Full BD intelligence pipeline |
| Competitor Analysis | `/webhook/competitor-analysis` | POST | Multi-competitor analysis |

### BD Pipeline
```bash
curl -X POST https://primetech.app.n8n.cloud/webhook/bd-pipeline \
  -H "Content-Type: application/json" \
  -d '{"program": "DCGS-A", "company": "Raytheon", "include_scrape": false, "generate_strategy": true}'
```

### Competitor Analysis
```bash
curl -X POST https://primetech.app.n8n.cloud/webhook/competitor-analysis \
  -H "Content-Type: application/json" \
  -d '{"companies": ["Booz Allen Hamilton", "SAIC", "Leidos"]}'
```

---

## MCP Server Tools → Webhook Mapping

| MCP Tool | Webhook Called | Method |
|----------|----------------|--------|
| `hub_smart_query` | `/webhook/hub-query` | POST |
| `hub_search` | `/webhook/hub-search` | GET |
| `hub_ingest_jobs` | `/webhook/ingest-jobs` | POST |
| `hub_add_insight` | `/webhook/add-insight` | POST |
| `trigger_scraper` | `/webhook/trigger-scrape` | POST |
| `trigger_full_pipeline` | `/webhook/full-pipeline` | POST |
| `run_bd_pipeline` | `/webhook/bd-pipeline` | POST |
| `run_competitor_analysis` | `/webhook/competitor-analysis` | POST |
| `send_slack_alert` | `/webhook/slack-alert` | POST |
| `sync_jobs_to_notion` | `/webhook/sync-jobs-notion` | POST |

---

## Testing Webhooks

Use the test webhook URL prefix for development:
```
https://primetech.app.n8n.cloud/webhook-test/[path]
```

Test mode workflows must be triggered manually in the n8n UI first.

---

## Authentication

Currently, webhooks are open. For production:
1. Add Header Auth to webhook nodes
2. Use API key validation in Code nodes
3. Implement IP whitelisting if needed
