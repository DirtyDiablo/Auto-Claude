# N8N-BUILDER: COMPREHENSIVE IMPLEMENTATION PLAN

## THE ORCHESTRATOR - Coordinates BD Intelligence Workflows

**Project Location:** `C:\Users\gtmar\Projects\Auto-Claude\n8n-builder`  
**Role:** ORCHESTRATOR - Coordinates workflows between Hub and Data-Scraper  
**N8N Instance:** `https://primetech.app.n8n.cloud` (Cloud-hosted)  
**Primary Function:** Multi-step BD workflows, event triggers, automation orchestration

**Created:** January 26, 2026  
**Version:** 1.0 - EXTREMELY EXTENSIVE EDITION  
**Total Estimated Implementation Time:** 20-30 hours

---

## TABLE OF CONTENTS

1. [Executive Overview](#1-executive-overview)
2. [Current State Analysis](#2-current-state-analysis)
3. [Target Architecture](#3-target-architecture)
4. [Prerequisites & Environment Setup](#4-prerequisites--environment-setup)
5. [Phase 1: Hub API Integration Node](#5-phase-1-hub-api-integration-node)
6. [Phase 2: Data-Scraper Integration Node](#6-phase-2-data-scraper-integration-node)
7. [Phase 3: Core BD Workflows](#7-phase-3-core-bd-workflows)
8. [Phase 4: Trigger Workflows](#8-phase-4-trigger-workflows)
9. [Phase 5: Intelligence Processing Workflows](#9-phase-5-intelligence-processing-workflows)
10. [Phase 6: Reporting & Export Workflows](#10-phase-6-reporting--export-workflows)
11. [Phase 7: Notion Integration Workflows](#11-phase-7-notion-integration-workflows)
12. [Phase 8: Alert & Notification Workflows](#12-phase-8-alert--notification-workflows)
13. [Phase 9: MCP Server for Claude Code](#13-phase-9-mcp-server-for-claude-code)
14. [Phase 10: Workflow Templates Library](#14-phase-10-workflow-templates-library)
15. [Phase 11: Error Handling & Recovery](#15-phase-11-error-handling--recovery)
16. [Phase 12: Monitoring & Analytics](#16-phase-12-monitoring--analytics)
17. [Phase 13: Testing & Validation](#17-phase-13-testing--validation)
18. [Phase 14: Deployment & Operations](#18-phase-14-deployment--operations)
19. [Workflow Catalog](#19-workflow-catalog)
20. [Appendices](#20-appendices)

---

## 1. EXECUTIVE OVERVIEW

### 1.1 What This Document Covers

This is the **EXTREMELY EXTENSIVE** implementation plan for N8N-Builder, the orchestration layer of the BD Intelligence Hub. This document contains:

- **Complete n8n workflow JSON definitions** ready for import
- **Custom node configurations** for Hub and Data-Scraper integration
- **Event-driven automation patterns** for BD operations
- **MCP server implementation** for Claude Code integration
- **Monitoring and error handling** strategies

### 1.2 Why N8N-Builder as ORCHESTRATOR

| Reason | Evidence |
|--------|----------|
| **Visual Workflow Designer** | Complex multi-step processes visualized |
| **Event-Driven Architecture** | Webhooks, schedules, triggers |
| **Native Integrations** | 400+ pre-built nodes (Notion, Slack, Google, etc.) |
| **Cloud Hosted** | primetech.app.n8n.cloud - no server management |
| **MCP Available** | Claude can trigger workflows directly |
| **Separation of Concerns** | Orchestration isolated from data/intelligence |

### 1.3 What Gets Built

| Component | Technology | Purpose |
|-----------|------------|---------|
| Hub Integration | HTTP Request Node | Call BD Hub API endpoints |
| Scraper Integration | HTTP Request Node | Trigger Data-Scraper pipelines |
| BD Workflows | n8n Workflows | Multi-step BD automation |
| Triggers | Webhook/Cron Nodes | Event-driven activation |
| Processing | Function/Code Nodes | Data transformation |
| Reporting | Template Nodes | Generate BD reports |
| Notifications | Slack/Email Nodes | Alert delivery |
| MCP Server | TypeScript | Claude Code integration |

### 1.4 Orchestration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        N8N-BUILDER ORCHESTRATION                            │
└─────────────────────────────────────────────────────────────────────────────┘

TRIGGERS                      N8N WORKFLOWS                    ACTIONS
────────                      ─────────────                    ───────

┌─────────────┐              ┌─────────────────────┐         ┌─────────────┐
│  Webhook    │──────────────▶│                     │         │   BD HUB    │
│  (External) │              │   DAILY SCRAPE      │────────▶│  POST/GET   │
└─────────────┘              │   WORKFLOW          │         └─────────────┘
                             │                     │               │
┌─────────────┐              │  ┌───────────────┐  │         ┌─────────────┐
│   Cron      │──────────────▶│  │ Trigger       │  │         │DATA-SCRAPER │
│ (Schedule)  │              │  │ Scrape        │  │────────▶│  Run Jobs   │
└─────────────┘              │  │ Process       │  │         └─────────────┘
                             │  │ Sync          │  │               │
┌─────────────┐              │  │ Report        │  │         ┌─────────────┐
│  Manual     │──────────────▶│  └───────────────┘  │         │   NOTION    │
│  (Claude)   │              │                     │────────▶│  Update DBs │
└─────────────┘              └─────────────────────┘         └─────────────┘
                                      │                            │
┌─────────────┐              ┌─────────────────────┐         ┌─────────────┐
│  Notion     │──────────────▶│  COMPETITOR INTEL   │         │   SLACK     │
│  (Change)   │              │  WORKFLOW           │────────▶│  Alerts     │
└─────────────┘              └─────────────────────┘         └─────────────┘
                                      │                            │
┌─────────────┐              ┌─────────────────────┐         ┌─────────────┐
│  Email      │──────────────▶│  CAPTURE PLANNING   │         │   EMAIL     │
│ (Inbound)   │              │  WORKFLOW           │────────▶│  Reports    │
└─────────────┘              └─────────────────────┘         └─────────────┘
```

---

## 2. CURRENT STATE ANALYSIS

### 2.1 Existing N8N Setup

**N8N Instance:** `https://primetech.app.n8n.cloud`  
**Plan:** Cloud (managed)  
**Current Workflows:** Minimal/None  
**MCP Integration:** Available via n8n MCP server

### 2.2 Available N8N Nodes (Relevant)

| Category | Nodes |
|----------|-------|
| **Triggers** | Webhook, Cron, Manual, Notion Trigger |
| **HTTP** | HTTP Request, HTTP Response |
| **Data** | Set, Function, Code, IF, Switch, Merge |
| **External** | Notion, Slack, Gmail, Google Sheets |
| **Utility** | Wait, DateTime, Crypto, JSON |

### 2.3 Current MCP Configuration

```json
// From .claude/settings.local.json
{
  "mcpServers": {
    "n8n": {
      "url": "https://primetech.app.n8n.cloud/mcp-server/http"
    }
  }
}
```

### 2.4 What's Missing (To Be Built)

| Gap | Solution | Priority |
|-----|----------|----------|
| No Hub integration | HTTP Request workflows | CRITICAL |
| No Scraper integration | HTTP Request workflows | CRITICAL |
| No BD workflows | Custom workflow definitions | HIGH |
| No event triggers | Webhook + Cron configs | HIGH |
| No error handling | Error workflow patterns | MEDIUM |
| No reporting | Report generation workflows | MEDIUM |
| Limited Claude integration | Enhanced MCP wrapper | MEDIUM |

---

## 3. TARGET ARCHITECTURE

### 3.1 Workflow Categories

```
n8n Workflows/
├── Core/
│   ├── daily-scrape-sync.json
│   ├── hub-health-monitor.json
│   └── data-quality-check.json
├── BD-Intelligence/
│   ├── competitor-analysis.json
│   ├── program-research.json
│   ├── contact-enrichment.json
│   └── opportunity-scoring.json
├── Triggers/
│   ├── webhook-receiver.json
│   ├── notion-change-trigger.json
│   └── scheduled-jobs.json
├── Reporting/
│   ├── daily-summary-report.json
│   ├── weekly-intel-digest.json
│   └── capture-plan-generator.json
├── Notifications/
│   ├── slack-alerter.json
│   ├── email-sender.json
│   └── high-priority-alert.json
└── Utilities/
    ├── data-transformer.json
    ├── error-handler.json
    └── retry-logic.json
```

### 3.2 Integration Points

```
┌─────────────────────────────────────────────────────────────────┐
│                    N8N INTEGRATION MAP                          │
└─────────────────────────────────────────────────────────────────┘

                         N8N-BUILDER
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   BD HUB      │   │ DATA-SCRAPER  │   │   EXTERNAL    │
│  :8100        │   │    :8200      │   │   SERVICES    │
├───────────────┤   ├───────────────┤   ├───────────────┤
│ /ask/smart    │   │ /scrape/run   │   │ Notion API    │
│ /ingest/*     │   │ /pipeline/*   │   │ Slack API     │
│ /memory/*     │   │ /hub/sync     │   │ Gmail API     │
│ /graph/*      │   │ /intel/*      │   │ Sheets API    │
│ /agent/*      │   │ /schedule/*   │   │ Calendar API  │
└───────────────┘   └───────────────┘   └───────────────┘
```

---

## 4. PREREQUISITES & ENVIRONMENT SETUP

### 4.1 N8N Cloud Setup

1. **Access N8N Instance:** `https://primetech.app.n8n.cloud`
2. **Create API Credentials:**
   - Settings → API → Create API Key
   - Save as `N8N_API_KEY`

### 4.2 Required Credentials in N8N

Create these credentials in N8N (Settings → Credentials):

| Credential Name | Type | Purpose |
|-----------------|------|---------|
| `bd-hub-api` | Header Auth | BD Hub authentication |
| `data-scraper-api` | Header Auth | Data-Scraper auth |
| `notion-api` | Notion API | Notion integration |
| `slack-api` | Slack API | Slack notifications |
| `gmail-api` | Gmail OAuth2 | Email sending |

### 4.3 Environment Variables

```bash
# .env for local development/testing
N8N_CLOUD_URL=https://primetech.app.n8n.cloud
N8N_API_KEY=your_n8n_api_key

BD_HUB_URL=http://127.0.0.1:8100
DATA_SCRAPER_URL=http://127.0.0.1:8200

NOTION_API_KEY=secret_xxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/xxxxx
```

### 4.4 Project Structure

```
n8n-builder/
├── .claude/
│   └── settings.local.json       # MCP configuration
├── workflows/
│   ├── core/                     # Core operation workflows
│   ├── bd-intelligence/          # BD analysis workflows
│   ├── triggers/                 # Event trigger workflows
│   ├── reporting/                # Report generation
│   ├── notifications/            # Alert workflows
│   └── utilities/                # Helper workflows
├── nodes/
│   └── custom/                   # Custom node definitions
├── mcp/
│   └── n8n-orchestrator-mcp/     # MCP server
├── scripts/
│   ├── deploy_workflows.py       # Workflow deployment
│   └── export_workflows.py       # Workflow export
├── templates/
│   └── workflow_templates/       # Reusable templates
├── config/
│   └── credentials.yaml          # Credential configs
├── CLAUDE.md
└── README.md
```

---

## 5. PHASE 1: HUB API INTEGRATION NODE

### 5.1 Overview

**What:** HTTP Request node configuration for BD Hub API  
**Why:** Enable n8n workflows to query and update the Hub  
**Priority:** CRITICAL

### 5.2 Hub API Credential Setup

In n8n, create a new Header Auth credential:

```
Name: bd-hub-api
Header Name: X-API-Key
Header Value: (leave empty for local, or set if needed)
```

### 5.3 Workflow: Hub Integration Base

**File:** `workflows/utilities/hub-integration-base.json`

```json
{
  "name": "Hub Integration Base",
  "nodes": [
    {
      "parameters": {},
      "id": "start",
      "name": "Start",
      "type": "n8n-nodes-base.manualTrigger",
      "position": [240, 300]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "={{ $env.BD_HUB_URL || 'http://127.0.0.1:8100' }}/health",
        "options": {}
      },
      "id": "hub-health",
      "name": "Hub Health Check",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 300]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "={{ $env.BD_HUB_URL || 'http://127.0.0.1:8100' }}/ask/smart",
        "qs": {
          "q": "={{ $json.query }}",
          "use_cache": true
        },
        "options": {}
      },
      "id": "hub-smart-query",
      "name": "Hub Smart Query",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 500]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $env.BD_HUB_URL || 'http://127.0.0.1:8100' }}/ingest/jobs",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "jobs",
              "value": "={{ $json.jobs }}"
            }
          ]
        },
        "options": {}
      },
      "id": "hub-post-jobs",
      "name": "Hub Post Jobs",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 700]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $env.BD_HUB_URL || 'http://127.0.0.1:8100' }}/memory/insight",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ insight_type: $json.insight_type, insight: $json.insight, source: 'n8n_workflow', confidence: $json.confidence || 0.8 }) }}"
      },
      "id": "hub-add-insight",
      "name": "Hub Add Insight",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 900]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "={{ $env.BD_HUB_URL || 'http://127.0.0.1:8100' }}/agent/{{ $json.agent }}",
        "qs": {
          "q": "={{ $json.query }}"
        }
      },
      "id": "hub-agent-query",
      "name": "Hub Agent Query",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 1100]
    }
  ],
  "connections": {
    "Start": {
      "main": [
        [
          { "node": "Hub Health Check", "type": "main", "index": 0 }
        ]
      ]
    }
  }
}
```

### 5.4 Hub API Helper Functions

**File:** `workflows/utilities/hub-api-functions.json`

```json
{
  "name": "Hub API Functions",
  "nodes": [
    {
      "parameters": {
        "jsCode": "// Hub API Helper Functions\n\nconst HUB_URL = $env.BD_HUB_URL || 'http://127.0.0.1:8100';\n\n// Smart Query\nasync function smartQuery(query, useCache = true) {\n  const response = await $http.request({\n    method: 'GET',\n    url: `${HUB_URL}/ask/smart`,\n    qs: { q: query, use_cache: useCache }\n  });\n  return response.data;\n}\n\n// Search\nasync function hybridSearch(query, collection = 'bd_knowledge', limit = 10) {\n  const response = await $http.request({\n    method: 'GET',\n    url: `${HUB_URL}/search/hybrid`,\n    qs: { q: query, collection, limit }\n  });\n  return response.data;\n}\n\n// Post Jobs\nasync function postJobs(jobs) {\n  const response = await $http.request({\n    method: 'POST',\n    url: `${HUB_URL}/ingest/jobs`,\n    body: jobs\n  });\n  return response.data;\n}\n\n// Add Memory\nasync function addMemory(content, memoryType = 'interaction') {\n  const response = await $http.request({\n    method: 'POST',\n    url: `${HUB_URL}/memory/add`,\n    body: { content, memory_type: memoryType }\n  });\n  return response.data;\n}\n\n// Add Insight\nasync function addInsight(insightType, insight, confidence = 0.8) {\n  const response = await $http.request({\n    method: 'POST',\n    url: `${HUB_URL}/memory/insight`,\n    body: { insight_type: insightType, insight, source: 'n8n', confidence }\n  });\n  return response.data;\n}\n\n// Query Agent\nasync function queryAgent(agent, query) {\n  const response = await $http.request({\n    method: 'GET',\n    url: `${HUB_URL}/agent/${agent}`,\n    qs: { q: query }\n  });\n  return response.data;\n}\n\n// Export for use\nreturn {\n  smartQuery,\n  hybridSearch,\n  postJobs,\n  addMemory,\n  addInsight,\n  queryAgent,\n  HUB_URL\n};"
      },
      "id": "hub-functions",
      "name": "Hub API Functions",
      "type": "n8n-nodes-base.code",
      "position": [300, 300]
    }
  ]
}
```

### 5.5 Phase 1 Verification Checklist

- [ ] Hub credential created in n8n
- [ ] Health check workflow works
- [ ] Smart query workflow works
- [ ] Post jobs workflow works
- [ ] Add insight workflow works
- [ ] Agent query workflow works

---

## 6. PHASE 2: DATA-SCRAPER INTEGRATION NODE

### 6.1 Overview

**What:** HTTP Request node configuration for Data-Scraper API  
**Why:** Enable n8n to trigger scraping and sync operations  
**Priority:** CRITICAL

### 6.2 Workflow: Scraper Integration Base

**File:** `workflows/utilities/scraper-integration-base.json`

```json
{
  "name": "Scraper Integration Base",
  "nodes": [
    {
      "parameters": {},
      "id": "start",
      "name": "Start",
      "type": "n8n-nodes-base.manualTrigger",
      "position": [240, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $env.DATA_SCRAPER_URL || 'http://127.0.0.1:8200' }}/scrape/run",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ source: $json.source || 'apex-jobs', locations: $json.locations, max_items: $json.max_items || 100 }) }}"
      },
      "id": "run-scraper",
      "name": "Run Scraper",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $env.DATA_SCRAPER_URL || 'http://127.0.0.1:8200' }}/scrape/run-all",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ locations: $json.locations }) }}"
      },
      "id": "run-all-scrapers",
      "name": "Run All Scrapers",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 500]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $env.DATA_SCRAPER_URL || 'http://127.0.0.1:8200' }}/pipeline/full",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ sources: $json.sources, sync_to_hub: true }) }}"
      },
      "id": "run-full-pipeline",
      "name": "Run Full Pipeline",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 700]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "={{ $env.DATA_SCRAPER_URL || 'http://127.0.0.1:8200' }}/intel/competitor",
        "qs": {
          "company": "={{ $json.company }}"
        }
      },
      "id": "analyze-competitor",
      "name": "Analyze Competitor",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 900]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "={{ $env.DATA_SCRAPER_URL || 'http://127.0.0.1:8200' }}/stats/pipeline"
      },
      "id": "get-stats",
      "name": "Get Pipeline Stats",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 1100]
    }
  ],
  "connections": {
    "Start": {
      "main": [
        [
          { "node": "Run Scraper", "type": "main", "index": 0 }
        ]
      ]
    }
  }
}
```

### 6.3 Phase 2 Verification Checklist

- [ ] Scraper credential created in n8n
- [ ] Run single scraper works
- [ ] Run all scrapers works
- [ ] Full pipeline works
- [ ] Competitor analysis works
- [ ] Stats endpoint works

---

## 7. PHASE 3: CORE BD WORKFLOWS

### 7.1 Workflow: Daily Scrape & Sync

**File:** `workflows/core/daily-scrape-sync.json`

```json
{
  "name": "Daily Scrape & Sync",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "hours",
              "hoursInterval": 24
            }
          ]
        }
      },
      "id": "cron-trigger",
      "name": "Daily 6AM Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [240, 300],
      "typeVersion": 1
    },
    {
      "parameters": {
        "method": "GET",
        "url": "http://127.0.0.1:8100/health"
      },
      "id": "check-hub",
      "name": "Check Hub Health",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 300]
    },
    {
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.status }}",
              "value2": "healthy"
            }
          ]
        }
      },
      "id": "if-healthy",
      "name": "IF Hub Healthy",
      "type": "n8n-nodes-base.if",
      "position": [680, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://127.0.0.1:8200/pipeline/full",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "{\"sources\": [\"apex-jobs\", \"insight-global-jobs\", \"teksystems-jobs\"], \"sync_to_hub\": true}"
      },
      "id": "run-pipeline",
      "name": "Run Full Pipeline",
      "type": "n8n-nodes-base.httpRequest",
      "position": [900, 200]
    },
    {
      "parameters": {
        "channel": "#bd-alerts",
        "text": "=:warning: BD Hub is unavailable! Daily scrape skipped.\nTime: {{ $now.toISO() }}",
        "otherOptions": {}
      },
      "id": "alert-hub-down",
      "name": "Alert Hub Down",
      "type": "n8n-nodes-base.slack",
      "position": [900, 400],
      "credentials": {
        "slackApi": {
          "id": "slack-api",
          "name": "Slack API"
        }
      }
    },
    {
      "parameters": {
        "jsCode": "// Process pipeline results\nconst results = $input.first().json;\n\nconst summary = {\n  status: results.status,\n  total_scraped: results.summary?.total_scraped || 0,\n  unique_jobs: results.summary?.unique || 0,\n  valid_jobs: results.summary?.valid || 0,\n  synced_to_hub: results.summary?.synced || 0,\n  duration_seconds: results.duration_seconds || 0,\n  errors: results.errors || [],\n  timestamp: new Date().toISOString()\n};\n\nreturn { json: summary };"
      },
      "id": "process-results",
      "name": "Process Results",
      "type": "n8n-nodes-base.code",
      "position": [1120, 200]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://127.0.0.1:8100/memory/add",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ content: 'Daily scrape completed: ' + $json.synced_to_hub + ' jobs synced to Hub', memory_type: 'scrape_result' }) }}"
      },
      "id": "record-memory",
      "name": "Record in Hub Memory",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1340, 200]
    },
    {
      "parameters": {
        "channel": "#bd-updates",
        "text": "=:white_check_mark: Daily Scrape Complete!\n\n• Total Scraped: {{ $json.total_scraped }}\n• Unique Jobs: {{ $json.unique_jobs }}\n• Valid Jobs: {{ $json.valid_jobs }}\n• Synced to Hub: {{ $json.synced_to_hub }}\n• Duration: {{ $json.duration_seconds }}s\n• Time: {{ $json.timestamp }}",
        "otherOptions": {}
      },
      "id": "notify-success",
      "name": "Notify Success",
      "type": "n8n-nodes-base.slack",
      "position": [1560, 200],
      "credentials": {
        "slackApi": {
          "id": "slack-api",
          "name": "Slack API"
        }
      }
    }
  ],
  "connections": {
    "Daily 6AM Trigger": {
      "main": [
        [{ "node": "Check Hub Health", "type": "main", "index": 0 }]
      ]
    },
    "Check Hub Health": {
      "main": [
        [{ "node": "IF Hub Healthy", "type": "main", "index": 0 }]
      ]
    },
    "IF Hub Healthy": {
      "main": [
        [{ "node": "Run Full Pipeline", "type": "main", "index": 0 }],
        [{ "node": "Alert Hub Down", "type": "main", "index": 0 }]
      ]
    },
    "Run Full Pipeline": {
      "main": [
        [{ "node": "Process Results", "type": "main", "index": 0 }]
      ]
    },
    "Process Results": {
      "main": [
        [{ "node": "Record in Hub Memory", "type": "main", "index": 0 }]
      ]
    },
    "Record in Hub Memory": {
      "main": [
        [{ "node": "Notify Success", "type": "main", "index": 0 }]
      ]
    }
  },
  "settings": {
    "executionOrder": "v1"
  }
}
```

### 7.2 Workflow: Hub Health Monitor

**File:** `workflows/core/hub-health-monitor.json`

```json
{
  "name": "Hub Health Monitor",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "minutes",
              "minutesInterval": 15
            }
          ]
        }
      },
      "id": "cron-15min",
      "name": "Every 15 Minutes",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [240, 300]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "http://127.0.0.1:8100/health",
        "options": {
          "timeout": 5000
        }
      },
      "id": "check-hub",
      "name": "Check Hub",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 300],
      "continueOnFail": true
    },
    {
      "parameters": {
        "method": "GET",
        "url": "http://127.0.0.1:8100/stats",
        "options": {
          "timeout": 5000
        }
      },
      "id": "get-stats",
      "name": "Get Hub Stats",
      "type": "n8n-nodes-base.httpRequest",
      "position": [680, 300],
      "continueOnFail": true
    },
    {
      "parameters": {
        "jsCode": "// Evaluate health status\nconst healthResult = $('Check Hub').first().json;\nconst statsResult = $('Get Hub Stats').first().json;\n\nconst status = {\n  hub_healthy: healthResult.status === 'healthy',\n  memory_count: statsResult.memory?.total_memories || 0,\n  graph_files: statsResult.graph?.files || 0,\n  cache_queries: statsResult.cache?.cached_queries || 0,\n  timestamp: new Date().toISOString()\n};\n\n// Check for issues\nstatus.issues = [];\nif (!status.hub_healthy) status.issues.push('Hub unhealthy');\nif (status.memory_count === 0) status.issues.push('No memories');\n\nstatus.needs_alert = status.issues.length > 0;\n\nreturn { json: status };"
      },
      "id": "evaluate",
      "name": "Evaluate Health",
      "type": "n8n-nodes-base.code",
      "position": [900, 300]
    },
    {
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{ $json.needs_alert }}",
              "value2": true
            }
          ]
        }
      },
      "id": "if-issues",
      "name": "IF Has Issues",
      "type": "n8n-nodes-base.if",
      "position": [1120, 300]
    },
    {
      "parameters": {
        "channel": "#bd-alerts",
        "text": "=:rotating_light: Hub Health Issues Detected!\n\nIssues:\n{{ $json.issues.join('\\n• ') }}\n\nStats:\n• Memories: {{ $json.memory_count }}\n• Graph Files: {{ $json.graph_files }}\n• Cached Queries: {{ $json.cache_queries }}\n\nTime: {{ $json.timestamp }}",
        "otherOptions": {}
      },
      "id": "alert-issues",
      "name": "Alert Issues",
      "type": "n8n-nodes-base.slack",
      "position": [1340, 200],
      "credentials": {
        "slackApi": {
          "id": "slack-api",
          "name": "Slack API"
        }
      }
    }
  ],
  "connections": {
    "Every 15 Minutes": {
      "main": [[{ "node": "Check Hub", "type": "main", "index": 0 }]]
    },
    "Check Hub": {
      "main": [[{ "node": "Get Hub Stats", "type": "main", "index": 0 }]]
    },
    "Get Hub Stats": {
      "main": [[{ "node": "Evaluate Health", "type": "main", "index": 0 }]]
    },
    "Evaluate Health": {
      "main": [[{ "node": "IF Has Issues", "type": "main", "index": 0 }]]
    },
    "IF Has Issues": {
      "main": [
        [{ "node": "Alert Issues", "type": "main", "index": 0 }],
        []
      ]
    }
  }
}
```

### 7.3 Phase 3 Verification Checklist

- [ ] Daily Scrape & Sync workflow created
- [ ] Cron trigger works
- [ ] Hub health check integrated
- [ ] Pipeline execution works
- [ ] Results processing works
- [ ] Memory recording works
- [ ] Slack notifications work
- [ ] Hub Health Monitor workflow created

---

## 14. PHASE 10: MCP SERVER FOR CLAUDE CODE

### 14.1 File: `mcp/n8n-orchestrator-mcp/src/index.ts`

```typescript
#!/usr/bin/env node

/**
 * N8N Orchestrator MCP Server
 * Provides workflow orchestration tools for Claude Code
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// n8n Cloud Configuration
const N8N_BASE_URL = process.env.N8N_CLOUD_URL || "https://primetech.app.n8n.cloud";
const N8N_API_KEY = process.env.N8N_API_KEY || "";

// Webhook base URL
const WEBHOOK_BASE = `${N8N_BASE_URL}/webhook`;

async function callWebhook(path: string, method: string = "POST", body?: any) {
  const options: RequestInit = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body && method !== "GET") {
    options.body = JSON.stringify(body);
  }
  
  const url = method === "GET" && body 
    ? `${WEBHOOK_BASE}/${path}?${new URLSearchParams(body).toString()}`
    : `${WEBHOOK_BASE}/${path}`;
  
  const response = await fetch(url, options);
  return response.json();
}

async function callN8nAPI(endpoint: string, method: string = "GET", body?: any) {
  const options: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-N8N-API-KEY": N8N_API_KEY,
    },
  };
  if (body) options.body = JSON.stringify(body);
  
  const response = await fetch(`${N8N_BASE_URL}/api/v1${endpoint}`, options);
  return response.json();
}

const server = new Server(
  { name: "n8n-orchestrator", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    // ==================== HUB TOOLS ====================
    {
      name: "hub_smart_query",
      description: "Query BD Hub with intelligent routing via n8n",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", description: "Natural language query" },
          use_cache: { type: "boolean", default: true }
        },
        required: ["query"]
      }
    },
    {
      name: "hub_search",
      description: "Search BD Hub knowledge base",
      inputSchema: {
        type: "object",
        properties: {
          q: { type: "string", description: "Search query" },
          collection: { type: "string", default: "bd_knowledge" },
          limit: { type: "number", default: 10 }
        },
        required: ["q"]
      }
    },
    {
      name: "hub_ingest_jobs",
      description: "Ingest jobs to BD Hub via n8n",
      inputSchema: {
        type: "object",
        properties: {
          jobs: {
            type: "array",
            items: {
              type: "object",
              properties: {
                title: { type: "string" },
                company: { type: "string" },
                location: { type: "string" },
                clearance: { type: "string" }
              }
            }
          }
        },
        required: ["jobs"]
      }
    },
    {
      name: "hub_add_insight",
      description: "Add BD insight to Hub memory",
      inputSchema: {
        type: "object",
        properties: {
          insight_type: { type: "string", enum: ["opportunity", "risk", "relationship", "strategy"] },
          insight: { type: "string" },
          confidence: { type: "number", default: 0.8 }
        },
        required: ["insight_type", "insight"]
      }
    },
    
    // ==================== SCRAPER TOOLS ====================
    {
      name: "trigger_scraper",
      description: "Trigger job scraper via n8n",
      inputSchema: {
        type: "object",
        properties: {
          source: {
            type: "string",
            enum: ["apex-jobs", "insight-global-jobs", "teksystems-jobs"],
            description: "Scraper source"
          },
          locations: {
            type: "array",
            items: { type: "string" },
            default: ["Washington DC", "Virginia", "Maryland"]
          },
          max_items: { type: "number", default: 100 }
        },
        required: ["source"]
      }
    },
    {
      name: "trigger_full_pipeline",
      description: "Run full scrape-standardize-sync pipeline",
      inputSchema: {
        type: "object",
        properties: {
          include_insights: { type: "boolean", default: true }
        }
      }
    },
    
    // ==================== PIPELINE TOOLS ====================
    {
      name: "run_bd_pipeline",
      description: "Run full BD intelligence pipeline for a program",
      inputSchema: {
        type: "object",
        properties: {
          program: { type: "string", description: "Target program (e.g., DCGS-A)" },
          company: { type: "string", description: "Target company (optional)" },
          include_scrape: { type: "boolean", default: false },
          generate_strategy: { type: "boolean", default: true }
        },
        required: ["program"]
      }
    },
    {
      name: "run_competitor_analysis",
      description: "Analyze multiple competitors",
      inputSchema: {
        type: "object",
        properties: {
          companies: {
            type: "array",
            items: { type: "string" },
            description: "Companies to analyze"
          }
        },
        required: ["companies"]
      }
    },
    
    // ==================== NOTIFICATION TOOLS ====================
    {
      name: "send_slack_alert",
      description: "Send Slack alert via n8n",
      inputSchema: {
        type: "object",
        properties: {
          message: { type: "string" },
          severity: { type: "string", enum: ["info", "warning", "error", "critical"], default: "info" },
          channel: { type: "string", default: "#bd-alerts" }
        },
        required: ["message"]
      }
    },
    
    // ==================== NOTION TOOLS ====================
    {
      name: "sync_jobs_to_notion",
      description: "Sync jobs from Hub to Notion",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", default: "recent jobs" },
          limit: { type: "number", default: 50 }
        }
      }
    },
    
    // ==================== WORKFLOW MANAGEMENT ====================
    {
      name: "list_workflows",
      description: "List all n8n workflows",
      inputSchema: { type: "object", properties: {} }
    },
    {
      name: "get_workflow_executions",
      description: "Get recent workflow executions",
      inputSchema: {
        type: "object",
        properties: {
          workflow_id: { type: "string" },
          limit: { type: "number", default: 10 }
        }
      }
    },
    {
      name: "activate_workflow",
      description: "Activate a workflow",
      inputSchema: {
        type: "object",
        properties: {
          workflow_id: { type: "string" }
        },
        required: ["workflow_id"]
      }
    },
    {
      name: "deactivate_workflow",
      description: "Deactivate a workflow",
      inputSchema: {
        type: "object",
        properties: {
          workflow_id: { type: "string" }
        },
        required: ["workflow_id"]
      }
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    let result;
    
    switch (name) {
      // Hub tools
      case "hub_smart_query":
        result = await callWebhook("hub-query", "POST", {
          query: args.query,
          use_cache: args.use_cache
        });
        break;
      
      case "hub_search":
        result = await callWebhook("hub-search", "GET", {
          q: args.q,
          collection: args.collection,
          limit: args.limit
        });
        break;
      
      case "hub_ingest_jobs":
        result = await callWebhook("ingest-jobs", "POST", {
          jobs: args.jobs
        });
        break;
      
      case "hub_add_insight":
        result = await callWebhook("add-insight", "POST", {
          insight_type: args.insight_type,
          insight: args.insight,
          confidence: args.confidence
        });
        break;
      
      // Scraper tools
      case "trigger_scraper":
        result = await callWebhook("trigger-scrape", "POST", {
          source: args.source,
          locations: args.locations,
          max_items: args.max_items
        });
        break;
      
      case "trigger_full_pipeline":
        result = await callWebhook("full-pipeline", "POST", {
          include_insights: args.include_insights
        });
        break;
      
      // Pipeline tools
      case "run_bd_pipeline":
        result = await callWebhook("bd-pipeline", "POST", {
          program: args.program,
          company: args.company,
          include_scrape: args.include_scrape,
          generate_strategy: args.generate_strategy
        });
        break;
      
      case "run_competitor_analysis":
        result = await callWebhook("competitor-analysis", "POST", {
          companies: args.companies
        });
        break;
      
      // Notification tools
      case "send_slack_alert":
        result = await callWebhook("slack-alert", "POST", {
          message: args.message,
          severity: args.severity,
          channel: args.channel
        });
        break;
      
      // Notion tools
      case "sync_jobs_to_notion":
        result = await callWebhook("sync-jobs-notion", "POST", {
          query: args.query,
          limit: args.limit
        });
        break;
      
      // Workflow management
      case "list_workflows":
        result = await callN8nAPI("/workflows");
        break;
      
      case "get_workflow_executions":
        const endpoint = args.workflow_id 
          ? `/executions?workflowId=${args.workflow_id}&limit=${args.limit || 10}`
          : `/executions?limit=${args.limit || 10}`;
        result = await callN8nAPI(endpoint);
        break;
      
      case "activate_workflow":
        result = await callN8nAPI(`/workflows/${args.workflow_id}/activate`, "POST");
        break;
      
      case "deactivate_workflow":
        result = await callN8nAPI(`/workflows/${args.workflow_id}/deactivate`, "POST");
        break;
      
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
    
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    
  } catch (error) {
    return { 
      content: [{ type: "text", text: `Error: ${error.message}` }], 
      isError: true 
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("N8N Orchestrator MCP Server running");
}

main().catch(console.error);
```

### 14.2 File: `mcp/n8n-orchestrator-mcp/package.json`

```json
{
  "name": "n8n-orchestrator-mcp",
  "version": "1.0.0",
  "description": "MCP server for n8n workflow orchestration",
  "main": "build/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node build/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/node": "^20.10.0"
  }
}
```

### 14.3 File: `mcp/n8n-orchestrator-mcp/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./build",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules"]
}
```

### 14.4 Build MCP Server

```bash
cd mcp/n8n-orchestrator-mcp
npm install
npm run build
```

### 14.5 Claude Desktop Configuration

Add to `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "n8n-orchestrator": {
      "command": "node",
      "args": ["C:/Users/gtmar/Projects/Auto-Claude/n8n-mcp-builder/mcp/n8n-orchestrator-mcp/build/index.js"],
      "env": {
        "N8N_CLOUD_URL": "https://primetech.app.n8n.cloud",
        "N8N_API_KEY": "your_n8n_api_key"
      }
    }
  }
}
```

### 14.6 Phase 10 Verification Checklist

- [ ] MCP server TypeScript created
- [ ] package.json created
- [ ] npm install succeeds
- [ ] npm run build succeeds
- [ ] All 15+ tools defined
- [ ] Tools call correct webhooks

---

## 15. PHASE 11: WORKFLOW TEMPLATES LIBRARY

### 15.1 Template: Basic Hub Query

```json
{
  "name": "Template: Basic Hub Query",
  "description": "Basic template for querying BD Hub",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook"
    },
    {
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://127.0.0.1:8100/ask/smart"
      }
    },
    {
      "name": "Respond",
      "type": "n8n-nodes-base.respondToWebhook"
    }
  ]
}
```

### 15.2 Template: Scheduled Task

```json
{
  "name": "Template: Scheduled Task",
  "description": "Template for scheduled tasks",
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [{"field": "hours", "hoursInterval": 1}]
        }
      }
    },
    {
      "name": "Task Logic",
      "type": "n8n-nodes-base.code"
    },
    {
      "name": "Notify",
      "type": "n8n-nodes-base.slack"
    }
  ]
}
```

### 15.3 Phase 11 Verification Checklist

- [ ] Templates created
- [ ] Templates importable
- [ ] Templates customizable

---

## 16. PHASE 12: MONITORING & ANALYTICS

### 16.1 Workflow: Health Check Monitor

**File:** `workflows/monitoring/health-check.json`

```json
{
  "name": "Health Check Monitor",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "minutes",
              "minutesInterval": 15
            }
          ]
        }
      },
      "id": "schedule",
      "name": "Every 15 Minutes",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "http://127.0.0.1:8100/health",
        "options": {
          "timeout": 5000,
          "response": {
            "response": {
              "neverError": true
            }
          }
        }
      },
      "id": "check-hub",
      "name": "Check Hub",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [450, 300]
    },
    {
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.status }}",
              "operation": "equals",
              "value2": "healthy"
            }
          ]
        }
      },
      "id": "is-healthy",
      "name": "Is Healthy?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 1,
      "position": [650, 300]
    },
    {
      "parameters": {
        "channel": "#bd-alerts",
        "text": "🚨 *BD Hub is DOWN!*\n\nHealth check failed at {{ $now.toISO() }}",
        "otherOptions": {}
      },
      "id": "alert-down",
      "name": "Alert Down",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 2,
      "position": [850, 400]
    }
  ],
  "connections": {
    "Every 15 Minutes": {
      "main": [[{"node": "Check Hub", "type": "main", "index": 0}]]
    },
    "Check Hub": {
      "main": [[{"node": "Is Healthy?", "type": "main", "index": 0}]]
    },
    "Is Healthy?": {
      "main": [
        [],
        [{"node": "Alert Down", "type": "main", "index": 0}]
      ]
    }
  },
  "settings": {
    "executionOrder": "v1"
  },
  "tags": ["monitoring", "health"]
}
```

### 16.2 Phase 12 Verification Checklist

- [ ] Health check workflow created
- [ ] Alerts trigger on failures
- [ ] Executions logged

---

## 17. PHASE 13-14: TESTING & DEPLOYMENT

### 17.1 Testing Script

**File:** `scripts/test-workflows.js`

```javascript
/**
 * Test n8n workflows via webhooks
 */

const WEBHOOK_BASE = "https://primetech.app.n8n.cloud/webhook-test";

async function testWebhook(path, method = "POST", body = {}) {
  console.log(`Testing: ${method} ${path}`);
  
  try {
    const options = {
      method,
      headers: { "Content-Type": "application/json" }
    };
    
    if (method !== "GET" && Object.keys(body).length > 0) {
      options.body = JSON.stringify(body);
    }
    
    const url = method === "GET" 
      ? `${WEBHOOK_BASE}/${path}?${new URLSearchParams(body)}`
      : `${WEBHOOK_BASE}/${path}`;
    
    const response = await fetch(url, options);
    const data = await response.json();
    
    console.log(`  Status: ${response.status}`);
    console.log(`  Response: ${JSON.stringify(data).substring(0, 200)}...`);
    
    return { success: response.ok, data };
  } catch (error) {
    console.log(`  Error: ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function runTests() {
  console.log("=".repeat(60));
  console.log("N8N Workflow Tests");
  console.log("=".repeat(60));
  
  const tests = [
    // Hub tests
    { path: "hub-query", method: "POST", body: { query: "DCGS programs" } },
    { path: "hub-search", method: "GET", body: { q: "engineer", limit: 5 } },
    { path: "add-insight", method: "POST", body: { 
      insight_type: "test", 
      insight: "Test insight from n8n" 
    }},
    
    // Scraper tests (may take long)
    // { path: "trigger-scrape", method: "POST", body: { source: "apex-jobs", max_items: 5 } },
    
    // Alert tests
    { path: "slack-alert", method: "POST", body: { 
      message: "Test alert from n8n tests",
      severity: "info"
    }},
    
    // Pipeline tests
    { path: "bd-pipeline", method: "POST", body: {
      program: "DCGS-A",
      include_scrape: false,
      generate_strategy: false
    }}
  ];
  
  const results = [];
  
  for (const test of tests) {
    const result = await testWebhook(test.path, test.method, test.body);
    results.push({ ...test, ...result });
    console.log("");
  }
  
  // Summary
  console.log("=".repeat(60));
  console.log("Test Summary");
  console.log("=".repeat(60));
  
  const passed = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;
  
  console.log(`Passed: ${passed}/${results.length}`);
  console.log(`Failed: ${failed}/${results.length}`);
  
  if (failed > 0) {
    console.log("\nFailed tests:");
    results.filter(r => !r.success).forEach(r => {
      console.log(`  - ${r.path}: ${r.error || 'Unknown error'}`);
    });
  }
}

runTests().catch(console.error);
```

### 17.2 Import/Export Scripts

**File:** `scripts/import-workflows.js`

```javascript
/**
 * Import workflows to n8n Cloud
 */

const fs = require('fs');
const path = require('path');

const N8N_URL = process.env.N8N_CLOUD_URL || "https://primetech.app.n8n.cloud";
const N8N_API_KEY = process.env.N8N_API_KEY;

async function importWorkflow(workflowPath) {
  const workflow = JSON.parse(fs.readFileSync(workflowPath, 'utf8'));
  
  const response = await fetch(`${N8N_URL}/api/v1/workflows`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-N8N-API-KEY': N8N_API_KEY
    },
    body: JSON.stringify(workflow)
  });
  
  const result = await response.json();
  console.log(`Imported: ${workflow.name} -> ID: ${result.id}`);
  return result;
}

async function importAllWorkflows() {
  const workflowsDir = path.join(__dirname, '..', 'workflows');
  const categories = fs.readdirSync(workflowsDir);
  
  for (const category of categories) {
    const categoryPath = path.join(workflowsDir, category);
    if (!fs.statSync(categoryPath).isDirectory()) continue;
    
    const files = fs.readdirSync(categoryPath).filter(f => f.endsWith('.json'));
    
    for (const file of files) {
      const filePath = path.join(categoryPath, file);
      try {
        await importWorkflow(filePath);
      } catch (error) {
        console.error(`Error importing ${file}: ${error.message}`);
      }
    }
  }
}

importAllWorkflows().catch(console.error);
```

### 17.3 Deployment Checklist

1. **n8n Cloud Setup**
   - [ ] n8n Cloud account active
   - [ ] API key generated
   - [ ] All credentials configured

2. **Workflow Import**
   - [ ] All 21 workflows imported
   - [ ] Workflows activated
   - [ ] Webhooks accessible

3. **MCP Server**
   - [ ] MCP server built
   - [ ] Added to Claude settings
   - [ ] Tools accessible

4. **Testing**
   - [ ] All webhook tests pass
   - [ ] Scheduled workflows trigger
   - [ ] Error handling works

5. **Monitoring**
   - [ ] Health check running
   - [ ] Alerts configured
   - [ ] Logs accessible

---

## 18. QUICK START GUIDE

### Complete Setup Commands

```bash
# 1. Navigate to project
cd "C:\Users\gtmar\Projects\Auto-Claude\n8n-mcp-builder"

# 2. Create directory structure
mkdir -p workflows/hub
mkdir -p workflows/scraper
mkdir -p workflows/notion
mkdir -p workflows/scheduled
mkdir -p workflows/alerts
mkdir -p workflows/pipelines
mkdir -p workflows/templates
mkdir -p workflows/monitoring
mkdir -p mcp/n8n-orchestrator-mcp/src
mkdir -p scripts
mkdir -p config

# 3. Create .env file
cat > .env << EOF
N8N_CLOUD_URL=https://primetech.app.n8n.cloud
N8N_API_KEY=your_n8n_api_key
BD_HUB_URL=http://127.0.0.1:8100
DATA_SCRAPER_URL=http://127.0.0.1:8200
EOF

# 4. Create workflow JSON files (from this document)

# 5. Setup MCP server
cd mcp/n8n-orchestrator-mcp
npm init -y
npm install @modelcontextprotocol/sdk typescript @types/node
# Create index.ts from this document
npm run build

# 6. Import workflows to n8n Cloud
cd ../..
node scripts/import-workflows.js

# 7. Test workflows
node scripts/test-workflows.js
```

### File Creation Order

1. `config/endpoints.yaml`
2. `config/schedules.yaml`
3. `workflows/hub/hub-smart-query.json`
4. `workflows/hub/hub-ingest-jobs.json`
5. `workflows/hub/hub-add-insight.json`
6. `workflows/hub/hub-search.json`
7. `workflows/scraper/trigger-job-scrape.json`
8. `workflows/scraper/trigger-full-pipeline.json`
9. `workflows/scraper/scraper-webhook.json`
10. `workflows/notion/sync-jobs-to-notion.json`
11. `workflows/notion/notion-to-hub.json`
12. `workflows/scheduled/daily-scrape.json`
13. `workflows/scheduled/weekly-report.json`
14. `workflows/alerts/slack-alert.json`
15. `workflows/alerts/error-notification.json`
16. `workflows/pipelines/full-bd-pipeline.json`
17. `workflows/pipelines/competitor-analysis.json`
18. `workflows/templates/http-with-retry.json`
19. `workflows/monitoring/health-check.json`
20. `mcp/n8n-orchestrator-mcp/src/index.ts`
21. `scripts/test-workflows.js`

---

## 19. SUMMARY

### What Was Built

| Component | Files | Purpose |
|-----------|-------|---------|
| Hub Workflows | 4 | Query/ingest BD Hub |
| Scraper Workflows | 3 | Trigger Data-Scraper |
| Notion Workflows | 2 | Bidirectional sync |
| Scheduled Workflows | 2 | Automation |
| Alert Workflows | 2 | Notifications |
| Pipeline Workflows | 2 | Multi-step BD processes |
| Template Workflows | 2 | Reusable patterns |
| Monitoring Workflows | 1 | Health checks |
| MCP Server | 3 | Claude Code tools |
| Scripts | 3 | Testing/deployment |
| **Total** | **24** | |

### Orchestration Flow

```
                    ┌─────────────────────────────────────┐
                    │         N8N ORCHESTRATOR            │
                    │   (primetech.app.n8n.cloud)         │
                    └─────────────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
    ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
    │    BD HUB     │       │ DATA-SCRAPER  │       │    NOTION     │
    │  (localhost   │       │  (localhost   │       │   (Cloud)     │
    │    :8100)     │       │    :8200)     │       │               │
    └───────────────┘       └───────────────┘       └───────────────┘
```

### MCP Tools Summary

| Tool | Purpose |
|------|---------|
| hub_smart_query | Query Hub with routing |
| hub_search | Search Hub knowledge |
| hub_ingest_jobs | Ingest jobs |
| hub_add_insight | Add BD insight |
| trigger_scraper | Trigger scraper |
| trigger_full_pipeline | Full scrape pipeline |
| run_bd_pipeline | Full BD pipeline |
| run_competitor_analysis | Competitor analysis |
| send_slack_alert | Send alerts |
| sync_jobs_to_notion | Sync to Notion |
| list_workflows | List workflows |
| get_workflow_executions | Get executions |
| activate_workflow | Activate workflow |
| deactivate_workflow | Deactivate workflow |

---

## 20. APPENDICES

### A. Webhook URL Reference

| Workflow | Webhook Path | Method |
|----------|--------------|--------|
| Hub Smart Query | `/webhook/hub-query` | POST |
| Hub Search | `/webhook/hub-search` | GET |
| Hub Ingest Jobs | `/webhook/ingest-jobs` | POST |
| Hub Add Insight | `/webhook/add-insight` | POST |
| Trigger Scraper | `/webhook/trigger-scrape` | POST |
| Full Pipeline | `/webhook/full-pipeline` | POST |
| Scraper Complete | `/webhook/scraper-complete` | POST |
| Sync Jobs Notion | `/webhook/sync-jobs-notion` | POST |
| Slack Alert | `/webhook/slack-alert` | POST |
| BD Pipeline | `/webhook/bd-pipeline` | POST |
| Competitor Analysis | `/webhook/competitor-analysis` | POST |

### B. Claude Desktop MCP Configuration

Complete configuration for all three projects:

```json
{
  "mcpServers": {
    "bd-intelligence-hub": {
      "command": "node",
      "args": ["C:/Users/gtmar/Projects/Auto-Claude/BD-Automation-Engine/mcp/knowledge-mcp-server/build/index.js"]
    },
    "data-scraper": {
      "command": "node",
      "args": ["C:/data-scraper/data-scraper/mcp/data-scraper-mcp/build/index.js"]
    },
    "n8n-orchestrator": {
      "command": "node",
      "args": ["C:/Users/gtmar/Projects/Auto-Claude/n8n-mcp-builder/mcp/n8n-orchestrator-mcp/build/index.js"],
      "env": {
        "N8N_CLOUD_URL": "https://primetech.app.n8n.cloud",
        "N8N_API_KEY": "your_api_key"
      }
    }
  }
}
```

---

## END OF N8N-BUILDER IMPLEMENTATION PLAN

**Total Workflows:** 21  
**Total MCP Tools:** 14  
**Total Webhooks:** 11  
**Estimated Implementation Time:** 20-30 hours


## 9. PHASE 5: NOTIFICATION WORKFLOWS

### 9.1 File: `workflows/notifications/slack_alert.json`

```json
{
  "name": "Notify - Slack Alert",
  "nodes": [
    {
      "id": "webhook",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "parameters": {
        "httpMethod": "POST",
        "path": "slack-alert"
      }
    },
    {
      "id": "format_message",
      "name": "Format Message",
      "type": "n8n-nodes-base.set",
      "position": [450, 300],
      "parameters": {
        "values": {
          "string": [
            {
              "name": "channel",
              "value": "={{ $json.body.channel || '#bd-updates' }}"
            },
            {
              "name": "message",
              "value": "={{ $json.body.message }}"
            },
            {
              "name": "severity",
              "value": "={{ $json.body.severity || 'info' }}"
            }
          ]
        }
      }
    },
    {
      "id": "select_emoji",
      "name": "Select Emoji",
      "type": "n8n-nodes-base.switch",
      "position": [650, 300],
      "parameters": {
        "dataType": "string",
        "value1": "={{ $json.severity }}",
        "rules": {
          "rules": [
            {"value": "info", "output": 0},
            {"value": "warning", "output": 1},
            {"value": "error", "output": 2},
            {"value": "success", "output": 3}
          ]
        },
        "fallbackOutput": 0
      }
    },
    {
      "id": "info_post",
      "name": "Info Post",
      "type": "n8n-nodes-base.slack",
      "position": [900, 150],
      "parameters": {
        "operation": "post",
        "channel": "={{ $json.channel }}",
        "text": "ℹ️ {{ $json.message }}"
      }
    },
    {
      "id": "warning_post",
      "name": "Warning Post",
      "type": "n8n-nodes-base.slack",
      "position": [900, 300],
      "parameters": {
        "operation": "post",
        "channel": "={{ $json.channel }}",
        "text": "⚠️ {{ $json.message }}"
      }
    },
    {
      "id": "error_post",
      "name": "Error Post",
      "type": "n8n-nodes-base.slack",
      "position": [900, 450],
      "parameters": {
        "operation": "post",
        "channel": "#bd-alerts",
        "text": "🚨 {{ $json.message }}"
      }
    },
    {
      "id": "success_post",
      "name": "Success Post",
      "type": "n8n-nodes-base.slack",
      "position": [900, 600],
      "parameters": {
        "operation": "post",
        "channel": "={{ $json.channel }}",
        "text": "✅ {{ $json.message }}"
      }
    }
  ],
  "connections": {
    "Webhook": {"main": [[{"node": "Format Message", "type": "main", "index": 0}]]},
    "Format Message": {"main": [[{"node": "Select Emoji", "type": "main", "index": 0}]]},
    "Select Emoji": {
      "main": [
        [{"node": "Info Post", "type": "main", "index": 0}],
        [{"node": "Warning Post", "type": "main", "index": 0}],
        [{"node": "Error Post", "type": "main", "index": 0}],
        [{"node": "Success Post", "type": "main", "index": 0}]
      ]
    }
  },
  "tags": ["notification", "slack", "production"]
}
```

### 9.2 File: `workflows/notifications/daily_digest.json`

```json
{
  "name": "Notify - Daily Digest",
  "nodes": [
    {
      "id": "cron",
      "name": "Daily 8 AM",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [250, 300],
      "parameters": {
        "rule": {
          "interval": [{"field": "cronExpression", "expression": "0 8 * * *"}]
        }
      }
    },
    {
      "id": "get_stats",
      "name": "Get Hub Stats",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300],
      "parameters": {
        "url": "http://127.0.0.1:8100/stats",
        "method": "GET"
      }
    },
    {
      "id": "get_insights",
      "name": "Get Recent Insights",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300],
      "parameters": {
        "url": "http://127.0.0.1:8100/memory/insights",
        "method": "GET",
        "queryParameters": {
          "parameters": [{"name": "limit", "value": "5"}]
        }
      }
    },
    {
      "id": "format_digest",
      "name": "Format Digest",
      "type": "n8n-nodes-base.code",
      "position": [850, 300],
      "parameters": {
        "language": "javaScript",
        "jsCode": "const stats = items[0].json;\nconst insights = items[1]?.json?.insights || [];\n\nconst digest = `📊 *Daily BD Intelligence Digest*\n\n*System Status:*\n• Memory: ${stats.memory?.total_memories || 0} memories\n• Graph: ${stats.graph?.files || 0} entities\n• Cache: ${stats.cache?.cached_queries || 0} cached\n\n*Recent Insights:*\n${insights.slice(0,3).map(i => '• ' + i.memory?.substring(0,100)).join('\\n') || 'No recent insights'}\n\n_Generated at ${new Date().toLocaleString()}_`;\n\nreturn [{json: {digest}}];"
      }
    },
    {
      "id": "send_slack",
      "name": "Send to Slack",
      "type": "n8n-nodes-base.slack",
      "position": [1050, 300],
      "parameters": {
        "operation": "post",
        "channel": "#bd-updates",
        "text": "={{ $json.digest }}"
      }
    }
  ],
  "connections": {
    "Daily 8 AM": {"main": [[{"node": "Get Hub Stats", "type": "main", "index": 0}]]},
    "Get Hub Stats": {"main": [[{"node": "Get Recent Insights", "type": "main", "index": 0}]]},
    "Get Recent Insights": {"main": [[{"node": "Format Digest", "type": "main", "index": 0}]]},
    "Format Digest": {"main": [[{"node": "Send to Slack", "type": "main", "index": 0}]]}
  },
  "tags": ["notification", "digest", "scheduled", "production"]
}
```

### 9.3 File: `workflows/notifications/opportunity_alert.json`

```json
{
  "name": "Notify - New Opportunity Alert",
  "nodes": [
    {
      "id": "webhook",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "parameters": {
        "httpMethod": "POST",
        "path": "opportunity-alert"
      }
    },
    {
      "id": "validate",
      "name": "Validate Opportunity",
      "type": "n8n-nodes-base.if",
      "position": [450, 300],
      "parameters": {
        "conditions": {
          "number": [{"value1": "={{ $json.body.confidence || 0 }}", "value2": 0.7, "operation": "larger"}]
        }
      }
    },
    {
      "id": "format_alert",
      "name": "Format Alert",
      "type": "n8n-nodes-base.set",
      "position": [650, 250],
      "parameters": {
        "values": {
          "string": [
            {
              "name": "alert_text",
              "value": "🎯 *New BD Opportunity Detected*\n\n*Program:* {{ $json.body.program }}\n*Company:* {{ $json.body.company }}\n*Confidence:* {{ Math.round($json.body.confidence * 100) }}%\n*Source:* {{ $json.body.source }}\n\n*Details:* {{ $json.body.details }}"
            }
          ]
        }
      }
    },
    {
      "id": "send_slack",
      "name": "Slack Alert",
      "type": "n8n-nodes-base.slack",
      "position": [850, 200],
      "parameters": {
        "operation": "post",
        "channel": "#bd-opportunities",
        "text": "={{ $json.alert_text }}"
      }
    },
    {
      "id": "log_to_hub",
      "name": "Log to Hub",
      "type": "n8n-nodes-base.httpRequest",
      "position": [850, 350],
      "parameters": {
        "url": "http://127.0.0.1:8100/memory/insight",
        "method": "POST",
        "bodyParametersJson": "={{ JSON.stringify({insight_type: 'opportunity', insight: $json.body.details, source: 'n8n_alert', confidence: $json.body.confidence}) }}"
      }
    }
  ],
  "connections": {
    "Webhook": {"main": [[{"node": "Validate Opportunity", "type": "main", "index": 0}]]},
    "Validate Opportunity": {
      "main": [[{"node": "Format Alert", "type": "main", "index": 0}], []]
    },
    "Format Alert": {
      "main": [
        [{"node": "Slack Alert", "type": "main", "index": 0}],
        [{"node": "Log to Hub", "type": "main", "index": 0}]
      ]
    }
  },
  "tags": ["notification", "opportunity", "production"]
}
```

### 9.4 Phase 5 Verification Checklist

- [ ] `workflows/notifications/slack_alert.json` created
- [ ] `workflows/notifications/daily_digest.json` created
- [ ] `workflows/notifications/opportunity_alert.json` created
- [ ] Slack messages send correctly
- [ ] Daily digest generates at 8 AM

---

## 10. PHASE 6: WEBHOOK HANDLERS

### 10.1 File: `workflows/webhooks/generic_webhook.json`

```json
{
  "name": "Webhook - Generic Handler",
  "nodes": [
    {
      "id": "webhook",
      "name": "Generic Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "parameters": {
        "httpMethod": "=POST",
        "path": "generic-handler",
        "responseMode": "responseNode"
      }
    },
    {
      "id": "log_event",
      "name": "Log to Hub Memory",
      "type": "n8n-nodes-base.httpRequest",
      "position": [500, 300],
      "parameters": {
        "url": "http://127.0.0.1:8100/memory/add",
        "method": "POST",
        "bodyParametersJson": "={{ JSON.stringify({content: 'Webhook received: ' + JSON.stringify($json.body).substring(0, 200), memory_type: 'interaction'}) }}"
      }
    },
    {
      "id": "route_action",
      "name": "Route by Action",
      "type": "n8n-nodes-base.switch",
      "position": [750, 300],
      "parameters": {
        "dataType": "string",
        "value1": "={{ $json.body.action }}",
        "rules": {
          "rules": [
            {"value": "query", "output": 0},
            {"value": "ingest", "output": 1},
            {"value": "notify", "output": 2}
          ]
        },
        "fallbackOutput": 3
      }
    },
    {
      "id": "query_hub",
      "name": "Query Hub",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1000, 150],
      "parameters": {
        "url": "http://127.0.0.1:8100/ask/smart",
        "method": "GET",
        "queryParameters": {"parameters": [{"name": "q", "value": "={{ $json.body.query }}"}]}
      }
    },
    {
      "id": "ingest_data",
      "name": "Ingest Data",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1000, 300],
      "parameters": {
        "url": "http://127.0.0.1:8100/ingest/{{ $json.body.type }}",
        "method": "POST",
        "bodyParametersJson": "={{ JSON.stringify($json.body.data) }}"
      }
    },
    {
      "id": "send_notification",
      "name": "Send Notification",
      "type": "n8n-nodes-base.slack",
      "position": [1000, 450],
      "parameters": {
        "operation": "post",
        "channel": "#bd-updates",
        "text": "={{ $json.body.message }}"
      }
    },
    {
      "id": "default_response",
      "name": "Default Response",
      "type": "n8n-nodes-base.set",
      "position": [1000, 600],
      "parameters": {
        "values": {"string": [{"name": "status", "value": "received"}]}
      }
    },
    {
      "id": "respond",
      "name": "Respond",
      "type": "n8n-nodes-base.respondToWebhook",
      "position": [1250, 300],
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ $json }}"
      }
    }
  ],
  "connections": {
    "Generic Webhook": {"main": [[{"node": "Log to Hub Memory", "type": "main", "index": 0}]]},
    "Log to Hub Memory": {"main": [[{"node": "Route by Action", "type": "main", "index": 0}]]},
    "Route by Action": {
      "main": [
        [{"node": "Query Hub", "type": "main", "index": 0}],
        [{"node": "Ingest Data", "type": "main", "index": 0}],
        [{"node": "Send Notification", "type": "main", "index": 0}],
        [{"node": "Default Response", "type": "main", "index": 0}]
      ]
    },
    "Query Hub": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]},
    "Ingest Data": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]},
    "Send Notification": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]},
    "Default Response": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]}
  },
  "tags": ["webhook", "generic", "production"]
}
```

### 10.2 Phase 6 Verification Checklist

- [ ] `workflows/webhooks/generic_webhook.json` created
- [ ] Webhook receives POST requests
- [ ] Routes to correct action
- [ ] Logs events to Hub memory

---

## 11. PHASE 7: SCHEDULED WORKFLOWS

### 11.1 File: `config/schedules.yaml`

```yaml
# N8N Workflow Schedules

schedules:
  daily_scrape:
    workflow: "Scraper - Full ETL Pipeline"
    cron: "0 6 * * *"  # 6 AM daily
    description: "Run full scraper pipeline daily"
    enabled: true

  daily_digest:
    workflow: "Notify - Daily Digest"
    cron: "0 8 * * *"  # 8 AM daily
    description: "Send daily intelligence digest"
    enabled: true

  weekly_intel:
    workflow: "Campaign - Weekly Intelligence"
    cron: "0 9 * * 1"  # Monday 9 AM
    description: "Generate weekly intelligence report"
    enabled: true

  hub_health_check:
    workflow: "Utility - Health Check"
    cron: "*/30 * * * *"  # Every 30 minutes
    description: "Check Hub health"
    enabled: true

  cache_cleanup:
    workflow: "Utility - Cache Clear"
    cron: "0 0 * * 0"  # Sunday midnight
    description: "Weekly cache cleanup"
    enabled: true
```

### 11.2 Phase 7 Verification Checklist

- [ ] `config/schedules.yaml` created
- [ ] Schedule configurations defined
- [ ] Scheduled workflows activate correctly

---

## 12. PHASE 8: MULTI-STEP BD CAMPAIGNS

### 12.1 File: `workflows/campaigns/new_opportunity.json`

```json
{
  "name": "Campaign - New Opportunity Investigation",
  "nodes": [
    {
      "id": "webhook",
      "name": "Opportunity Trigger",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "parameters": {
        "httpMethod": "POST",
        "path": "new-opportunity"
      }
    },
    {
      "id": "step1_program",
      "name": "Step 1: Program Research",
      "type": "n8n-nodes-base.httpRequest",
      "position": [500, 300],
      "parameters": {
        "url": "http://127.0.0.1:8100/agent/program",
        "method": "GET",
        "queryParameters": {"parameters": [{"name": "q", "value": "Analyze program {{ $json.body.program }}"}]}
      }
    },
    {
      "id": "step2_competitors",
      "name": "Step 2: Competitor Analysis",
      "type": "n8n-nodes-base.httpRequest",
      "position": [750, 300],
      "parameters": {
        "url": "http://127.0.0.1:8100/agent/company",
        "method": "GET",
        "queryParameters": {"parameters": [{"name": "q", "value": "Competitors on {{ $json.body.program }}"}]}
      }
    },
    {
      "id": "step3_contacts",
      "name": "Step 3: Find Contacts",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1000, 300],
      "parameters": {
        "url": "http://127.0.0.1:8100/agent/contact",
        "method": "GET",
        "queryParameters": {"parameters": [{"name": "q", "value": "Decision makers for {{ $json.body.program }}"}]}
      }
    },
    {
      "id": "step4_strategy",
      "name": "Step 4: Generate Strategy",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1250, 300],
      "parameters": {
        "url": "http://127.0.0.1:8100/agent/strategy",
        "method": "GET",
        "queryParameters": {"parameters": [{"name": "q", "value": "Capture strategy for {{ $json.body.program }}"}]}
      }
    },
    {
      "id": "compile_report",
      "name": "Compile Report",
      "type": "n8n-nodes-base.code",
      "position": [1500, 300],
      "parameters": {
        "language": "javaScript",
        "jsCode": "const program = items[0].json;\nconst competitors = items[1]?.json;\nconst contacts = items[2]?.json;\nconst strategy = items[3]?.json;\n\nconst report = {\n  program: $input.first().json.body.program,\n  analysis: {\n    program_intel: program.response,\n    competitors: competitors.response,\n    key_contacts: contacts.response,\n    strategy: strategy.response\n  },\n  generated_at: new Date().toISOString()\n};\n\nreturn [{json: report}];"
      }
    },
    {
      "id": "save_insight",
      "name": "Save to Hub",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1750, 300],
      "parameters": {
        "url": "http://127.0.0.1:8100/memory/insight",
        "method": "POST",
        "bodyParametersJson": "={{ JSON.stringify({insight_type: 'opportunity', insight: 'Full analysis completed for ' + $json.program, source: 'campaign_workflow', confidence: 0.9}) }}"
      }
    },
    {
      "id": "notify_team",
      "name": "Notify Team",
      "type": "n8n-nodes-base.slack",
      "position": [2000, 300],
      "parameters": {
        "operation": "post",
        "channel": "#bd-opportunities",
        "text": "📋 *Opportunity Analysis Complete*\n\nProgram: {{ $json.program }}\n\nFull report generated and saved to Hub.\n\n_View in BD Hub for details_"
      }
    }
  ],
  "connections": {
    "Opportunity Trigger": {"main": [[{"node": "Step 1: Program Research", "type": "main", "index": 0}]]},
    "Step 1: Program Research": {"main": [[{"node": "Step 2: Competitor Analysis", "type": "main", "index": 0}]]},
    "Step 2: Competitor Analysis": {"main": [[{"node": "Step 3: Find Contacts", "type": "main", "index": 0}]]},
    "Step 3: Find Contacts": {"main": [[{"node": "Step 4: Generate Strategy", "type": "main", "index": 0}]]},
    "Step 4: Generate Strategy": {"main": [[{"node": "Compile Report", "type": "main", "index": 0}]]},
    "Compile Report": {"main": [[{"node": "Save to Hub", "type": "main", "index": 0}]]},
    "Save to Hub": {"main": [[{"node": "Notify Team", "type": "main", "index": 0}]]}
  },
  "tags": ["campaign", "opportunity", "multi-step", "production"]
}
```

### 12.2 File: `workflows/campaigns/competitor_watch.json`

```json
{
  "name": "Campaign - Competitor Monitoring",
  "nodes": [
    {
      "id": "cron",
      "name": "Daily Check",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [250, 300],
      "parameters": {
        "rule": {"interval": [{"field": "hours", "hoursInterval": 12}]}
      }
    },
    {
      "id": "get_competitors",
      "name": "Get Watched Competitors",
      "type": "n8n-nodes-base.set",
      "position": [450, 300],
      "parameters": {
        "values": {
          "string": [{"name": "competitors", "value": "Leidos,GDIT,Booz Allen,SAIC,Peraton"}]
        }
      }
    },
    {
      "id": "split",
      "name": "Split Competitors",
      "type": "n8n-nodes-base.splitInBatches",
      "position": [650, 300],
      "parameters": {"batchSize": 1}
    },
    {
      "id": "analyze",
      "name": "Analyze Competitor",
      "type": "n8n-nodes-base.httpRequest",
      "position": [850, 300],
      "parameters": {
        "url": "http://127.0.0.1:8100/agent/company",
        "method": "GET",
        "queryParameters": {"parameters": [{"name": "q", "value": "Recent activity for {{ $json.item }}"}]}
      }
    },
    {
      "id": "check_changes",
      "name": "Check for Changes",
      "type": "n8n-nodes-base.if",
      "position": [1050, 300],
      "parameters": {
        "conditions": {
          "string": [{"value1": "={{ $json.response }}", "operation": "contains", "value2": "new"}]
        }
      }
    },
    {
      "id": "alert_change",
      "name": "Alert on Change",
      "type": "n8n-nodes-base.slack",
      "position": [1250, 250],
      "parameters": {
        "operation": "post",
        "channel": "#bd-alerts",
        "text": "🔍 *Competitor Activity Detected*\n\n{{ $json.response }}"
      }
    },
    {
      "id": "log_check",
      "name": "Log Check",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1250, 400],
      "parameters": {
        "url": "http://127.0.0.1:8100/memory/add",
        "method": "POST",
        "bodyParametersJson": "={{ JSON.stringify({content: 'Competitor check completed', memory_type: 'interaction'}) }}"
      }
    }
  ],
  "connections": {
    "Daily Check": {"main": [[{"node": "Get Watched Competitors", "type": "main", "index": 0}]]},
    "Get Watched Competitors": {"main": [[{"node": "Split Competitors", "type": "main", "index": 0}]]},
    "Split Competitors": {"main": [[{"node": "Analyze Competitor", "type": "main", "index": 0}]]},
    "Analyze Competitor": {"main": [[{"node": "Check for Changes", "type": "main", "index": 0}]]},
    "Check for Changes": {
      "main": [
        [{"node": "Alert on Change", "type": "main", "index": 0}],
        [{"node": "Log Check", "type": "main", "index": 0}]
      ]
    }
  },
  "tags": ["campaign", "competitor", "scheduled", "production"]
}
```

### 12.3 Phase 8 Verification Checklist

- [ ] `workflows/campaigns/new_opportunity.json` created
- [ ] `workflows/campaigns/competitor_watch.json` created
- [ ] Multi-step workflows execute in sequence
- [ ] Reports compile correctly
- [ ] Notifications fire at each stage

---

## 13. PHASE 9: ERROR HANDLING & RETRY LOGIC

### 13.1 Error Handling Strategy

All production workflows should include:

1. **Error Trigger Workflow** - Catches all workflow errors
2. **Retry Logic** - HTTP nodes with `retryOnFail: true`
3. **Error Notifications** - Slack alerts for failures
4. **Graceful Degradation** - Default responses on failure

### 13.2 Deploy Error Handler

```bash
# Deploy error handler to N8N
from client.workflow_manager import get_workflow_manager

manager = get_workflow_manager()
manager.deploy_workflow("templates/error_handler.json", activate=True)
```

### 13.3 Phase 9 Verification Checklist

- [ ] Error handler workflow deployed
- [ ] All HTTP nodes have retry configured
- [ ] Error notifications fire correctly
- [ ] Workflows recover from transient failures

---

## 14. PHASE 10: MCP SERVER FOR CLAUDE CODE

### 14.1 File: `mcp/n8n-orchestrator-mcp/src/index.ts`

```typescript
#!/usr/bin/env node

/**
 * N8N Orchestrator MCP Server
 * Provides workflow orchestration tools for Claude Code
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const N8N_API_URL = process.env.N8N_API_URL || "https://primetech.app.n8n.cloud/api/v1";
const N8N_API_KEY = process.env.N8N_API_KEY || "";

async function callN8N(endpoint: string, method: string = "GET", body?: any) {
  const options: RequestInit = {
    method,
    headers: {
      "X-N8N-API-KEY": N8N_API_KEY,
      "Content-Type": "application/json"
    },
  };
  if (body) options.body = JSON.stringify(body);
  
  const response = await fetch(`${N8N_API_URL}${endpoint}`, options);
  return response.json();
}

// Webhook base URL (for triggering workflows)
const WEBHOOK_BASE = "https://primetech.app.n8n.cloud/webhook";

async function triggerWebhook(path: string, data: any) {
  const response = await fetch(`${WEBHOOK_BASE}/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  return response.json();
}

const server = new Server(
  { name: "n8n-orchestrator", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    // ==================== WORKFLOW MANAGEMENT ====================
    {
      name: "list_workflows",
      description: "List all N8N workflows",
      inputSchema: {
        type: "object",
        properties: {
          active_only: { type: "boolean", default: false }
        }
      }
    },
    {
      name: "get_workflow",
      description: "Get workflow details by ID",
      inputSchema: {
        type: "object",
        properties: {
          workflow_id: { type: "string" }
        },
        required: ["workflow_id"]
      }
    },
    {
      name: "activate_workflow",
      description: "Activate a workflow",
      inputSchema: {
        type: "object",
        properties: {
          workflow_id: { type: "string" }
        },
        required: ["workflow_id"]
      }
    },
    {
      name: "deactivate_workflow",
      description: "Deactivate a workflow",
      inputSchema: {
        type: "object",
        properties: {
          workflow_id: { type: "string" }
        },
        required: ["workflow_id"]
      }
    },
    {
      name: "execute_workflow",
      description: "Execute a workflow directly",
      inputSchema: {
        type: "object",
        properties: {
          workflow_id: { type: "string" },
          data: { type: "object" }
        },
        required: ["workflow_id"]
      }
    },
    
    // ==================== HUB INTEGRATION ====================
    {
      name: "trigger_hub_query",
      description: "Trigger Hub query via N8N webhook",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" },
          use_cache: { type: "boolean", default: true }
        },
        required: ["query"]
      }
    },
    {
      name: "trigger_hub_ingest",
      description: "Trigger data ingestion to Hub via N8N",
      inputSchema: {
        type: "object",
        properties: {
          type: { type: "string", enum: ["jobs", "contacts", "programs", "companies"] },
          data: { type: "object" }
        },
        required: ["type", "data"]
      }
    },
    {
      name: "trigger_hub_agent",
      description: "Call a Hub agent via N8N",
      inputSchema: {
        type: "object",
        properties: {
          agent: { type: "string", enum: ["program", "company", "contact", "strategy"] },
          query: { type: "string" }
        },
        required: ["agent", "query"]
      }
    },
    
    // ==================== SCRAPER ORCHESTRATION ====================
    {
      name: "trigger_scrape",
      description: "Trigger job scraper via N8N",
      inputSchema: {
        type: "object",
        properties: {
          source: { type: "string", enum: ["apex-jobs", "insight-global-jobs", "teksystems-jobs"] },
          locations: { type: "array", items: { type: "string" } },
          max_items: { type: "number", default: 100 }
        },
        required: ["source"]
      }
    },
    {
      name: "trigger_full_pipeline",
      description: "Trigger full scrape-to-hub pipeline",
      inputSchema: {
        type: "object",
        properties: {
          sync_to_hub: { type: "boolean", default: true }
        }
      }
    },
    
    // ==================== NOTIFICATIONS ====================
    {
      name: "send_slack_alert",
      description: "Send Slack alert via N8N",
      inputSchema: {
        type: "object",
        properties: {
          message: { type: "string" },
          channel: { type: "string", default: "#bd-updates" },
          severity: { type: "string", enum: ["info", "warning", "error", "success"], default: "info" }
        },
        required: ["message"]
      }
    },
    {
      name: "send_opportunity_alert",
      description: "Send opportunity alert",
      inputSchema: {
        type: "object",
        properties: {
          program: { type: "string" },
          company: { type: "string" },
          details: { type: "string" },
          confidence: { type: "number" }
        },
        required: ["program", "details"]
      }
    },
    
    // ==================== CAMPAIGNS ====================
    {
      name: "run_opportunity_investigation",
      description: "Run full opportunity investigation campaign",
      inputSchema: {
        type: "object",
        properties: {
          program: { type: "string" }
        },
        required: ["program"]
      }
    },
    {
      name: "run_competitor_analysis",
      description: "Run competitor analysis",
      inputSchema: {
        type: "object",
        properties: {
          company: { type: "string" }
        },
        required: ["company"]
      }
    },
    
    // ==================== EXECUTIONS ====================
    {
      name: "list_executions",
      description: "List recent workflow executions",
      inputSchema: {
        type: "object",
        properties: {
          workflow_id: { type: "string" },
          limit: { type: "number", default: 10 }
        }
      }
    },
    {
      name: "get_execution",
      description: "Get execution details",
      inputSchema: {
        type: "object",
        properties: {
          execution_id: { type: "string" }
        },
        required: ["execution_id"]
      }
    },
    
    // ==================== UTILITIES ====================
    {
      name: "test_n8n_connection",
      description: "Test N8N API connection",
      inputSchema: { type: "object", properties: {} }
    },
    {
      name: "get_workflow_stats",
      description: "Get statistics for a workflow",
      inputSchema: {
        type: "object",
        properties: {
          workflow_id: { type: "string" }
        },
        required: ["workflow_id"]
      }
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    let result;
    
    switch (name) {
      // Workflow Management
      case "list_workflows":
        const params = args.active_only ? "?active=true" : "";
        result = await callN8N(`/workflows${params}`);
        break;
      
      case "get_workflow":
        result = await callN8N(`/workflows/${args.workflow_id}`);
        break;
      
      case "activate_workflow":
        result = await callN8N(`/workflows/${args.workflow_id}`, "PATCH", { active: true });
        break;
      
      case "deactivate_workflow":
        result = await callN8N(`/workflows/${args.workflow_id}`, "PATCH", { active: false });
        break;
      
      case "execute_workflow":
        result = await callN8N(`/workflows/${args.workflow_id}/execute`, "POST", { data: args.data });
        break;
      
      // Hub Integration
      case "trigger_hub_query":
        result = await triggerWebhook("hub-query", { query: args.query, use_cache: args.use_cache });
        break;
      
      case "trigger_hub_ingest":
        result = await triggerWebhook("hub-ingest", { type: args.type, data: args.data });
        break;
      
      case "trigger_hub_agent":
        result = await triggerWebhook("hub-agent", { agent: args.agent, query: args.query });
        break;
      
      // Scraper
      case "trigger_scrape":
        result = await triggerWebhook("trigger-scrape", args);
        break;
      
      case "trigger_full_pipeline":
        result = await triggerWebhook("scrape-to-hub", { sync_to_hub: args.sync_to_hub });
        break;
      
      // Notifications
      case "send_slack_alert":
        result = await triggerWebhook("slack-alert", args);
        break;
      
      case "send_opportunity_alert":
        result = await triggerWebhook("opportunity-alert", args);
        break;
      
      // Campaigns
      case "run_opportunity_investigation":
        result = await triggerWebhook("new-opportunity", { program: args.program });
        break;
      
      case "run_competitor_analysis":
        result = await triggerWebhook("hub-agent", { agent: "company", query: `Analyze ${args.company}` });
        break;
      
      // Executions
      case "list_executions":
        const execParams = args.workflow_id ? `?workflowId=${args.workflow_id}&limit=${args.limit || 10}` : `?limit=${args.limit || 10}`;
        result = await callN8N(`/executions${execParams}`);
        break;
      
      case "get_execution":
        result = await callN8N(`/executions/${args.execution_id}`);
        break;
      
      // Utilities
      case "test_n8n_connection":
        result = await callN8N("/workflows");
        result = { connected: true, workflow_count: result.data?.length || 0 };
        break;
      
      case "get_workflow_stats":
        const executions = await callN8N(`/executions?workflowId=${args.workflow_id}&limit=100`);
        const execs = executions.data || [];
        result = {
          workflow_id: args.workflow_id,
          total_executions: execs.length,
          successful: execs.filter((e: any) => e.status === "success").length,
          failed: execs.filter((e: any) => e.status === "error").length
        };
        break;
      
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
    
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    
  } catch (error: any) {
    return { content: [{ type: "text", text: `Error: ${error.message}` }], isError: true };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("N8N Orchestrator MCP Server running");
}

main().catch(console.error);
```

### 14.2 File: `mcp/n8n-orchestrator-mcp/package.json`

```json
{
  "name": "n8n-orchestrator-mcp",
  "version": "1.0.0",
  "description": "MCP server for N8N workflow orchestration",
  "main": "build/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node build/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0"
  }
}
```

### 14.3 Build MCP Server

```bash
cd mcp/n8n-orchestrator-mcp
npm install
npm run build
```

### 14.4 Phase 10 Verification Checklist

- [ ] MCP server TypeScript created
- [ ] package.json created
- [ ] npm install succeeds
- [ ] npm run build succeeds
- [ ] All 20+ tools defined

---

## 15. PHASE 11: WORKFLOW MONITORING DASHBOARD

### 15.1 File: `monitoring/dashboard.py`

```python
"""
N8N Workflow Monitoring Dashboard
=================================

Provides real-time monitoring of workflow health.
"""

import os
from typing import Dict, List
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.live import Live

from client.n8n_client import get_n8n_client
from client.models import ExecutionStatus

console = Console()


class WorkflowDashboard:
    """Real-time workflow monitoring dashboard."""
    
    def __init__(self):
        self.client = get_n8n_client()
    
    def get_system_status(self) -> Dict:
        """Get overall system status."""
        workflows = self.client.list_workflows()
        executions = self.client.list_executions(limit=50)
        
        active = sum(1 for w in workflows if w.active)
        recent_errors = sum(
            1 for e in executions 
            if e.status == ExecutionStatus.ERROR 
            and e.startedAt > datetime.now() - timedelta(hours=24)
        )
        
        return {
            "total_workflows": len(workflows),
            "active_workflows": active,
            "recent_executions": len(executions),
            "recent_errors": recent_errors,
            "health": "healthy" if recent_errors < 5 else "degraded"
        }
    
    def get_workflow_table(self) -> Table:
        """Generate workflow status table."""
        table = Table(title="N8N Workflows")
        
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Last Run", style="yellow")
        table.add_column("Success Rate", style="magenta")
        
        workflows = self.client.list_workflows()
        
        for wf in workflows[:20]:
            stats = self.client.get_workflow_stats(wf.id)
            
            status = "✅ Active" if wf.active else "⏸️ Inactive"
            last_run = stats.last_execution.strftime("%Y-%m-%d %H:%M") if stats.last_execution else "Never"
            
            if stats.total_executions > 0:
                rate = f"{(stats.successful / stats.total_executions) * 100:.0f}%"
            else:
                rate = "N/A"
            
            table.add_row(wf.name[:40], status, last_run, rate)
        
        return table
    
    def get_execution_table(self, limit: int = 10) -> Table:
        """Generate recent executions table."""
        table = Table(title="Recent Executions")
        
        table.add_column("Workflow", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Started", style="yellow")
        table.add_column("Duration", style="magenta")
        
        executions = self.client.list_executions(limit=limit)
        
        for exec in executions:
            workflow = self.client.get_workflow(exec.workflowId)
            
            status_icon = {
                ExecutionStatus.SUCCESS: "✅",
                ExecutionStatus.ERROR: "❌",
                ExecutionStatus.RUNNING: "🔄",
                ExecutionStatus.WAITING: "⏳"
            }.get(exec.status, "❓")
            
            started = exec.startedAt.strftime("%H:%M:%S")
            
            if exec.stoppedAt:
                duration = f"{(exec.stoppedAt - exec.startedAt).total_seconds():.1f}s"
            else:
                duration = "Running..."
            
            table.add_row(workflow.name[:30], f"{status_icon} {exec.status.value}", started, duration)
        
        return table
    
    def print_dashboard(self):
        """Print full dashboard."""
        console.clear()
        
        status = self.get_system_status()
        
        console.print(f"\n[bold]N8N Orchestrator Dashboard[/bold]")
        console.print(f"Health: {'🟢' if status['health'] == 'healthy' else '🟡'} {status['health']}")
        console.print(f"Workflows: {status['active_workflows']}/{status['total_workflows']} active")
        console.print(f"Recent Errors: {status['recent_errors']}\n")
        
        console.print(self.get_workflow_table())
        console.print()
        console.print(self.get_execution_table())


def run_dashboard():
    """Run the monitoring dashboard."""
    dashboard = WorkflowDashboard()
    dashboard.print_dashboard()


if __name__ == "__main__":
    run_dashboard()
```

### 15.2 Phase 11 Verification Checklist

- [ ] `monitoring/dashboard.py` created
- [ ] Dashboard displays workflow status
- [ ] Execution history shows correctly
- [ ] Health status accurate

---

## 16. PHASE 12: TESTING & DEPLOYMENT

### 16.1 Deploy All Workflows

```python
# deploy_all.py
from client.workflow_manager import get_workflow_manager

def deploy_all_workflows():
    manager = get_workflow_manager()
    
    # Deploy in order
    categories = ["templates", "hub", "scraper", "notifications", "webhooks", "campaigns", "utilities"]
    
    for category in categories:
        print(f"\nDeploying {category} workflows...")
        workflows = manager.deploy_all(category, activate=True)
        print(f"  Deployed {len(workflows)} workflows")
    
    print("\n✅ All workflows deployed!")

if __name__ == "__main__":
    deploy_all_workflows()
```

### 16.2 Test Script

```python
# test_workflows.py
import asyncio
from client.n8n_client import get_n8n_client

async def test_workflows():
    client = get_n8n_client()
    
    print("Testing N8N connection...")
    assert client.test_connection(), "Connection failed!"
    print("✅ Connected")
    
    print("\nListing workflows...")
    workflows = client.list_workflows()
    print(f"✅ Found {len(workflows)} workflows")
    
    # Test webhook
    print("\nTesting hub-query webhook...")
    import requests
    resp = requests.post(
        "https://primetech.app.n8n.cloud/webhook/hub-query",
        json={"query": "test query"}
    )
    print(f"✅ Webhook responded: {resp.status_code}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_workflows())
```

### 16.3 Claude Code MCP Configuration

Add to `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "n8n": {
      "url": "https://primetech.app.n8n.cloud/mcp-server/http"
    },
    "n8n-orchestrator": {
      "command": "node",
      "args": ["C:/Users/gtmar/Projects/Auto-Claude/n8n-mcp-builder/mcp/n8n-orchestrator-mcp/build/index.js"],
      "env": {
        "N8N_API_KEY": "your_n8n_api_key",
        "N8N_API_URL": "https://primetech.app.n8n.cloud/api/v1"
      }
    }
  }
}
```

### 16.4 Phase 12 Verification Checklist

- [ ] All workflows deployed to N8N
- [ ] Workflows activate correctly
- [ ] Webhooks respond
- [ ] MCP server configured in Claude Code
- [ ] Dashboard runs without errors

---

## 17. WORKFLOW CATALOG

### Complete List of Workflows

| Category | Workflow | Webhook Path | Schedule |
|----------|----------|--------------|----------|
| **Hub** | Smart Query | /hub-query | - |
| **Hub** | Ingest Data | /hub-ingest | - |
| **Hub** | Memory Operations | /hub-memory | - |
| **Hub** | Agent Call | /hub-agent | - |
| **Scraper** | Trigger Scrape | /trigger-scrape | - |
| **Scraper** | Full Pipeline | - | Every 6 hours |
| **Scraper** | Scrape to Hub | /scrape-to-hub | - |
| **Notifications** | Slack Alert | /slack-alert | - |
| **Notifications** | Daily Digest | - | 8 AM daily |
| **Notifications** | Opportunity Alert | /opportunity-alert | - |
| **Webhooks** | Generic Handler | /generic-handler | - |
| **Campaigns** | New Opportunity | /new-opportunity | - |
| **Campaigns** | Competitor Watch | - | Every 12 hours |
| **Utilities** | Health Check | - | Every 30 min |

---

## 18. QUICK START GUIDE

### Complete Setup Commands

```bash
# 1. Navigate to project
cd "C:\Users\gtmar\Projects\Auto-Claude\n8n-mcp-builder"

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create directories
mkdir -p client
mkdir -p workflows/hub
mkdir -p workflows/scraper
mkdir -p workflows/notifications
mkdir -p workflows/webhooks
mkdir -p workflows/campaigns
mkdir -p workflows/utilities
mkdir -p templates
mkdir -p mcp/n8n-orchestrator-mcp/src
mkdir -p monitoring
mkdir -p config

# 5. Create .env file
cat > .env << EOF
N8N_API_URL=https://primetech.app.n8n.cloud/api/v1
N8N_API_KEY=your_n8n_api_key
BD_HUB_URL=http://127.0.0.1:8100
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxxxx
EOF

# 6. Create all Python files (from this document)

# 7. Build MCP server
cd mcp/n8n-orchestrator-mcp
npm install
npm run build
cd ../..

# 8. Test N8N connection
python -c "from client.n8n_client import get_n8n_client; print(get_n8n_client().test_connection())"

# 9. Deploy all workflows
python deploy_all.py

# 10. Run monitoring dashboard
python monitoring/dashboard.py
```

---

## SUMMARY

### What Was Built

| Component | Files | Purpose |
|-----------|-------|---------|
| N8N Client | 3 | API client and workflow manager |
| Hub Workflows | 4 | Query, ingest, memory, agents |
| Scraper Workflows | 3 | Trigger, pipeline, sync |
| Notification Workflows | 3 | Slack, digest, opportunity |
| Webhook Handlers | 1 | Generic webhook processing |
| Campaign Workflows | 2 | Multi-step BD automation |
| Templates | 3 | Base, error handler, retry |
| MCP Server | 2 | 20+ Claude Code tools |
| Monitoring | 1 | Dashboard and metrics |

### Integration Points

```
N8N-Builder                     Target Systems
───────────                     ──────────────

/hub-query webhook ────────────▶ BD Hub /ask/smart
/hub-ingest webhook ───────────▶ BD Hub /ingest/*
/hub-agent webhook ────────────▶ BD Hub /agent/*
/trigger-scrape webhook ───────▶ Data-Scraper /scrape/run
/slack-alert webhook ──────────▶ Slack API
Scheduled workflows ───────────▶ Automated runs
```

### MCP Tools Summary

| Category | Tools |
|----------|-------|
| Workflow Management | 5 |
| Hub Integration | 3 |
| Scraper Orchestration | 2 |
| Notifications | 2 |
| Campaigns | 2 |
| Executions | 2 |
| Utilities | 2 |
| **TOTAL** | **18** |

---

## END OF N8N-BUILDER IMPLEMENTATION PLAN

**Total Files to Create:** ~25  
**Total Workflows:** 16  
**Total MCP Tools:** 18  
**Estimated Implementation Time:** 20-30 hours

