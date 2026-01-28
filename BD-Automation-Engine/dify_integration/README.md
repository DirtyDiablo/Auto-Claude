# Dify Integration for BD-Automation-Engine

Integrates [Dify](https://github.com/langgenius/dify) as a visual AI orchestration layer for your BD Intelligence system.

## What Dify Adds to Your Stack

You already have:
- ✅ CrewAI for multi-agent orchestration
- ✅ LlamaIndex + Qdrant for RAG (8,447+ indexed records)
- ✅ n8n for workflow automation (18 workflows)
- ✅ 5 AI agents (bd_strategy, company_research, contact_finder, program_intel)

Dify adds:
- 🆕 **Visual AI Workflow Builder** - Drag-drop instead of code
- 🆕 **Prompt IDE** - A/B test prompts without deployments
- 🆕 **LLMOps Monitoring** - Token usage, latency, quality metrics
- 🆕 **200+ LLM Support** - Switch Claude ↔ GPT ↔ Llama visually
- 🆕 **Team Access** - Non-technical BD team can build simple apps

## Quick Start

### 1. Start Dify (Docker)

```bash
# Clone Dify
git clone https://github.com/langgenius/dify.git
cd dify/docker

# Configure
cp .env.example .env
# Edit .env and add:
# ANTHROPIC_API_KEY=your-key
# OPENAI_API_KEY=your-key

# Start (requires ~6GB RAM)
docker compose up -d

# Access: http://localhost:3000
# Default: admin@example.com / password
```

### 2. Ensure Your Knowledge API is Running

```bash
# From BD-Automation-Engine root
python Engine8_Knowledge/api.py
# API runs on http://127.0.0.1:8100
```

### 3. Register External Tools in Dify

In Dify UI:
1. Go to **Tools** → **Custom Tools**
2. Add your Knowledge API endpoints from `tools_config.py`

Example tool registration:
```yaml
name: bd_strategy_agent
description: Get BD strategy recommendations
endpoint: http://127.0.0.1:8100/agent/strategy
method: GET
parameters:
  q:
    type: string
    required: true
    description: Strategy request
```

### 4. Create Your First App

Use one of the pre-built templates:

```python
from dify_integration import BDDifyApps

apps = BDDifyApps()
config = apps.export_app_config('bd_research_chat', format='yaml')
print(config)
```

Import this config into Dify to create your app.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BD Intelligence Architecture                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                   DIFY (Visual AI Layer)                         │    │
│  │   • BD Research Chat (visual RAG config)                        │    │
│  │   • Call Prep Workflow (drag-drop)                              │    │
│  │   • Prompt A/B Testing                                          │    │
│  │   • LLMOps Dashboard (monitor all AI usage)                     │    │
│  └───────────────────────────────┬─────────────────────────────────┘    │
│                                  │ HTTP / Webhooks                       │
│  ┌───────────────────────────────▼─────────────────────────────────┐    │
│  │            YOUR EXISTING STACK (Keep Everything)                │    │
│  │                                                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │    │
│  │  │   CrewAI     │  │   Qdrant     │  │  LlamaIndex  │          │    │
│  │  │   Agents     │  │  (8,447+)    │  │    RAG       │          │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │    │
│  │                                                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │    │
│  │  │    n8n       │  │   Notion     │  │   Apify      │          │    │
│  │  │ (18 flows)   │  │    MCP       │  │   Scrapers   │          │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │    │
│  │                                                                  │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Bridge Components

### DifyQdrantBridge

Connects Dify to your existing Qdrant vector store (no data duplication).

```python
from dify_integration import DifyQdrantBridge

bridge = DifyQdrantBridge()

# Search your existing vectors
results = await bridge.search("DCGS program managers", collection="contacts")

# RAG query
answer = await bridge.ask_rag("What programs does Northrop prime on?")

# Smart query (uses optimal retrieval systems)
response = await bridge.get_smart_answer("Find Tier 1 contacts for AF DCGS")
```

### DifyCrewAIBridge

Invokes your existing AI agents from Dify apps.

```python
from dify_integration import DifyCrewAIBridge

bridge = DifyCrewAIBridge()

# Invoke individual agents
result = await bridge.bd_strategy("Develop capture plan for AF DCGS")
result = await bridge.company_research("Northrop Grumman")
result = await bridge.contact_finder("Tier 1 contacts for DCGS")

# Run multi-agent workflows
playbook = await bridge.run_program_analysis("AF DCGS")
outreach = await bridge.run_outreach_prep("John Smith")
```

### DifyN8NBridge

Triggers your n8n workflows from Dify.

```python
from dify_integration import DifyN8NBridge

bridge = DifyN8NBridge()

# Trigger workflows
await bridge.trigger_job_scraper(keywords=["DCGS", "ISR"])
await bridge.trigger_hot_lead_alert({"contact_name": "John Smith", "score": 95})
await bridge.trigger_weekly_report()
```

## Pre-Built App Templates

| App | Mode | Description |
|-----|------|-------------|
| BD Research Chat | chat | Research assistant with 8,447+ indexed documents |
| Call Prep Generator | workflow | Generate call briefs using CrewAI agents |
| Pipeline Controller | agent-chat | Natural language control of n8n workflows |
| Outreach Drafter | workflow | Draft personalized BD messages |
| Program Analyzer | agent-chat | Deep program analysis with multi-agent workflow |
| Competitor Intel | chat | Research competitors and their positioning |

Export templates:
```python
from dify_integration import BDDifyApps

apps = BDDifyApps()
print(apps.export_app_config('bd_research_chat', format='json'))
```

## External Tools

34 tools available for Dify apps:

| Category | Tools |
|----------|-------|
| Search & RAG | qdrant_search, qdrant_smart_query, qdrant_hybrid_search, qdrant_rag |
| Contacts & Companies | qdrant_contacts, qdrant_programs, qdrant_jobs, graph_contact_network |
| Knowledge Graph | graph_query, graph_program_ecosystem, graph_teaming_path |
| Memory | memory_search, memory_contact_context |
| AI Agents | bd_strategy_agent, company_research_agent, contact_finder_agent, program_intel_agent |
| Multi-Agent Workflows | crewai_analyze_program, crewai_prepare_outreach, crewai_weekly_intel |
| Automation (n8n) | n8n_job_scraper, n8n_hot_lead_alert, n8n_weekly_report, n8n_master_pipeline |
| External (MCP) | notion_query, apify_scrape |

See `tools_config.py` for full configurations.

## Adding Dify Routes to Your API

Add the Dify-compatible endpoints to your existing Knowledge API:

```python
# In Engine8_Knowledge/api.py

from dify_integration.dify_qdrant_bridge import create_dify_knowledge_router
from dify_integration.dify_crewai_bridge import create_dify_agents_router
from dify_integration.dify_n8n_bridge import create_dify_n8n_router

# Add to app
app.include_router(create_dify_knowledge_router(), prefix="/dify")
app.include_router(create_dify_agents_router(), prefix="/dify")
app.include_router(create_dify_n8n_router(), prefix="/dify")
```

## Environment Variables

Add to your `.env`:

```bash
# Dify Configuration
DIFY_API_URL=http://localhost:3000
DIFY_API_KEY=your-dify-api-key

# Your existing vars (already set)
KNOWLEDGE_API_URL=http://127.0.0.1:8100
N8N_API_URL=https://primetech.app.n8n.cloud
```

## LLMOps Monitoring

Dify provides out-of-the-box monitoring:

- **Token Usage** - Track costs across all apps
- **Latency** - Response time percentiles
- **Quality Metrics** - User feedback, completion rates
- **A/B Testing** - Compare prompt variants

Access via Dify Dashboard → Analytics

## Success Criteria

- [ ] Dify running at http://localhost:3000
- [ ] Connected to your existing Qdrant (not duplicating vectors)
- [ ] CrewAI agents accessible as Dify tools
- [ ] n8n workflows triggerable from Dify
- [ ] LLMOps dashboard showing token usage
- [ ] Prompt A/B testing working
- [ ] Non-technical team can use visual builder

## Files in This Module

```
dify_integration/
├── __init__.py           # Module exports
├── dify_qdrant_bridge.py # Qdrant/vector search bridge
├── dify_crewai_bridge.py # CrewAI agents bridge
├── dify_n8n_bridge.py    # n8n workflows bridge
├── dify_apps.py          # Pre-built app templates
├── tools_config.py       # External tool configurations
└── README.md             # This file
```

## Troubleshooting

### Dify can't connect to Knowledge API

1. Ensure API is running: `python Engine8_Knowledge/api.py`
2. Check CORS is enabled (already configured in api.py)
3. Verify endpoint: `curl http://127.0.0.1:8100/health`

### Tools not appearing in Dify

1. Register tools manually in Dify UI (Tools → Custom Tools)
2. Check endpoint URLs match your environment
3. Verify API key permissions

### n8n webhooks not triggering

1. Check webhook URLs in `dify_n8n_bridge.py` match your n8n instance
2. Ensure webhooks are active in n8n
3. Check n8n API key has proper permissions

## Resources

- [Dify Documentation](https://docs.dify.ai/)
- [Dify GitHub](https://github.com/langgenius/dify)
- [Your Knowledge API Docs](http://127.0.0.1:8100/docs)
