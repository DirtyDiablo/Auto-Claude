# N8N Workflow Activation Guide

## Summary

All 10 workflows have been successfully created in n8n Cloud via the MCP API. However, **webhook registration requires manual activation through the n8n UI**.

## Issue Identified

When workflows are created and activated via the API, they show `active: true` in the database but the webhooks are not registered with n8n's internal webhook handling system. This is a known limitation of n8n Cloud - webhooks must be activated through the UI for proper registration.

## Created Workflows

| Workflow Name | ID | Webhook Path | Status |
|--------------|-----|--------------|--------|
| Hub - Smart Query | q8AK6JgJTFn2UMME | `/webhook/hub-query` | Needs UI Activation |
| Hub - Search | Cn5mWTIdIOr3pLmZ | `/webhook/hub-search` | Needs UI Activation |
| Hub - Add Insight | JKLNJ3BB2iAB5BF0 | `/webhook/add-insight` | Needs UI Activation |
| Hub - Ingest Jobs | PSol8u2uFoZlgnuz | `/webhook/ingest-jobs` | Needs UI Activation |
| Alert - Slack Notification | 8LcLkXWJVMuDgjxV | `/webhook/slack-alert` | Needs UI Activation |
| Scraper - Trigger Job Scrape | PEkVSg9Iy3D8WtWO | `/webhook/trigger-scrape` | Needs UI Activation |
| Scraper - Full Pipeline | 07YOGFu68qlF7QJ7 | `/webhook/full-pipeline` | Needs UI Activation |
| Pipeline - BD Intelligence | KxKAZ2T4x46V6NrI | `/webhook/bd-pipeline` | Needs UI Activation |
| Pipeline - Competitor Analysis | AA9MFxaq6HK2NkyN | `/webhook/competitor-analysis` | Needs UI Activation |
| Monitor - Health Check | 4ntAR1gLLgvheMpE | Schedule Trigger (15 min) | Needs UI Activation |

## Activation Steps

### Option 1: Toggle Each Workflow (Recommended)

1. Go to https://primetech.app.n8n.cloud
2. For each workflow listed above:
   - Open the workflow
   - Toggle the activation switch **OFF** (if it shows ON)
   - Toggle the activation switch **ON**
   - This properly registers the webhook with n8n's webhook system

### Option 2: Quick Re-activate All

1. Go to https://primetech.app.n8n.cloud
2. Navigate to "Workflows" list view
3. For workflows showing as "Active", click the toggle to deactivate
4. Then click again to reactivate

## Verify Webhooks Are Working

After activating through the UI, test with:

```bash
# Test Hub Smart Query
curl -X POST "https://primetech.app.n8n.cloud/webhook/hub-query" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'

# Test Hub Search
curl "https://primetech.app.n8n.cloud/webhook/hub-search?q=test&limit=5"

# Test Slack Alert
curl -X POST "https://primetech.app.n8n.cloud/webhook/slack-alert" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test alert", "severity": "info"}'
```

## Expected Response

After proper activation, you should receive JSON responses from the workflows instead of:
```json
{
  "code": 404,
  "message": "The requested webhook \"POST hub-query\" is not registered."
}
```

## Production Webhook URLs

Once activated, these are your production webhook URLs:

| Workflow | Production URL |
|----------|----------------|
| Hub Smart Query | `https://primetech.app.n8n.cloud/webhook/hub-query` |
| Hub Search | `https://primetech.app.n8n.cloud/webhook/hub-search` |
| Hub Add Insight | `https://primetech.app.n8n.cloud/webhook/add-insight` |
| Hub Ingest Jobs | `https://primetech.app.n8n.cloud/webhook/ingest-jobs` |
| Slack Alert | `https://primetech.app.n8n.cloud/webhook/slack-alert` |
| Trigger Scrape | `https://primetech.app.n8n.cloud/webhook/trigger-scrape` |
| Full Pipeline | `https://primetech.app.n8n.cloud/webhook/full-pipeline` |
| BD Pipeline | `https://primetech.app.n8n.cloud/webhook/bd-pipeline` |
| Competitor Analysis | `https://primetech.app.n8n.cloud/webhook/competitor-analysis` |

## Notes

- The BD Hub must be running at `http://127.0.0.1:8100` for Hub workflows to function
- The Data Scraper must be running at `http://127.0.0.1:8200` for Scraper workflows to function
- The Monitor - Health Check workflow uses a 15-minute schedule trigger, not a webhook
- Slack notifications require a Slack webhook URL to be configured in the Alert workflow
