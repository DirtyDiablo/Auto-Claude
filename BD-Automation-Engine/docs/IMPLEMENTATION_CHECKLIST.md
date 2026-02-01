# Implementation Checklist
## Multi-Project Unification Step-by-Step Guide

**Status:** Ready for Execution
**Estimated Duration:** 10 weeks
**Prerequisites:** All audit files reviewed

---

## IMMEDIATE ACTIONS (This Week)

### 1. Share Audit Files with Claude
- [ ] **CRITICAL:** Copy audit files to `/home/user/Auto-Claude/audits/`
  ```bash
  # On Windows, copy these files:
  # - DEEP_AUDIT_BD-Automation-Engine.md
  # - BD_DASHBOARD_FULL_AUDIT.md
  # - DEEP_AUDIT_N8N_BUILDER.md
  # - DEEP_AUDIT_DATA-SCRAPER.md
  # - compass_artifact_*.md
  # - repo-tools-capabilities-matrix.md
  ```

### 2. Verify Current BD-Automation-Engine State
- [ ] Confirm OpenAI embeddings working
  ```bash
  cd BD-Automation-Engine
  python -c "from services.ai_enrichment.engine import *; print('OK')"
  ```
- [ ] Verify Qdrant connection
  ```bash
  curl http://localhost:6333/collections
  ```
- [ ] Check enrichment status: 7,602 contacts enriched ✅

---

## PHASE 1: FOUNDATION (Week 1-2)

### Week 1: Infrastructure Setup

#### Day 1-2: Qdrant Unified Instance
- [ ] Create unified docker-compose.yml
  ```bash
  mkdir -p unified-infrastructure
  cd unified-infrastructure
  # Create docker-compose.yml from guide
  ```
- [ ] Start Qdrant container
  ```bash
  docker-compose up -d qdrant
  ```
- [ ] Verify Qdrant is running
  ```bash
  curl http://localhost:6333
  ```

#### Day 3-4: Create Unified Collections
- [ ] Create Python script: `scripts/init_unified_collections.py`
- [ ] Run collection initialization
  ```bash
  python scripts/init_unified_collections.py
  ```
- [ ] Verify all collections created:
  - [ ] `bd_jobs`
  - [ ] `bd_contacts`
  - [ ] `bd_programs`
  - [ ] `n8n_workflows`
  - [ ] `n8n_nodes`
  - [ ] `n8n_templates`
  - [ ] `scraper_sources`
  - [ ] `scraper_data`
  - [ ] `unified_knowledge`

#### Day 5: Unified Environment Configuration
- [ ] Create `unified.env` from template
- [ ] Add all API keys:
  - [ ] `OPENAI_API_KEY`
  - [ ] `ANTHROPIC_API_KEY`
  - [ ] `QDRANT_API_KEY`
  - [ ] `NOTION_TOKEN`
  - [ ] `APIFY_API_TOKEN`
  - [ ] `N8N_API_KEY`
- [ ] Test environment loading
  ```bash
  python -c "from dotenv import load_dotenv; load_dotenv('unified.env'); print('OK')"
  ```

### Week 2: Shared Services

#### Day 6-7: Embedding Service
- [ ] Create `services/embedding_service.py`
- [ ] Implement caching for cost reduction
- [ ] Test embedding generation
  ```bash
  python -c "
  from services.embedding_service import UnifiedEmbeddingService
  import os
  svc = UnifiedEmbeddingService(os.getenv('OPENAI_API_KEY'))
  emb = svc.get_embedding('test')
  print(f'Embedding dims: {len(emb)}')  # Should be 1536
  "
  ```

#### Day 8-9: API Hub Setup
- [ ] Create `api/main.py` with FastAPI
- [ ] Implement core endpoints:
  - [ ] `POST /api/v1/search` - Unified search
  - [ ] `GET /api/v1/bd/jobs` - BD jobs
  - [ ] `GET /api/v1/bd/contacts` - BD contacts
  - [ ] `GET /api/v1/bd/programs` - BD programs
  - [ ] `GET /api/v1/bd/playbook` - Daily playbook
- [ ] Add API key authentication
- [ ] Test API
  ```bash
  uvicorn api.main:app --reload --port 8000
  curl http://localhost:8000/docs
  ```

#### Day 10: Graphiti Integration
- [ ] Verify Graphiti enabled in `.env`
- [ ] Create `services/graphiti_service.py`
- [ ] Test knowledge graph operations
  ```bash
  python -c "
  from services.graphiti_service import UnifiedGraphitiService
  svc = UnifiedGraphitiService()
  print(f'Entities: {svc.count_entities()}')
  "
  ```

---

## PHASE 2: BD-AUTOMATION ENHANCEMENT (Week 3-4)

### Week 3: Complete BD Indexing

#### Day 11-12: Index Federal Programs
- [ ] Export programs from Notion to CSV
  ```bash
  python services/notion_sync.py --export-programs
  ```
- [ ] Create indexing script: `scripts/index_programs.py`
- [ ] Run program indexing
  ```bash
  python scripts/index_programs.py \
    --source Engine2_ProgramMapping/data/Programs_KB.csv \
    --collection bd_programs
  ```
- [ ] Verify: 388+ programs indexed
  ```bash
  curl "http://localhost:6333/collections/bd_programs"
  ```

#### Day 13-14: Index All Jobs
- [ ] Aggregate all job files
  ```bash
  python scripts/aggregate_jobs.py --output outputs/all_jobs.json
  ```
- [ ] Create indexing script: `scripts/index_jobs.py`
- [ ] Run job indexing
  ```bash
  python scripts/index_jobs.py \
    --source outputs/all_jobs.json \
    --collection bd_jobs
  ```
- [ ] Verify: Jobs indexed

#### Day 15: Re-index Contacts with Embeddings
- [ ] Contacts already enriched (7,602 records)
- [ ] Add vector embeddings to contacts
  ```bash
  python scripts/embed_contacts.py \
    --source outputs/contacts_enriched.json \
    --collection bd_contacts
  ```
- [ ] Verify semantic search works
  ```bash
  curl -X POST "http://localhost:8000/api/v1/search" \
    -H "X-API-Key: your-key" \
    -d '{"query": "network engineer San Diego", "projects": ["bd"]}'
  ```

### Week 4: BD Dashboard Completion

#### Day 16-17: Complete Dashboard Tabs
- [ ] Verify existing tabs:
  - [ ] Jobs Tab
  - [ ] Programs Tab
  - [ ] Contacts Tab
- [ ] Complete remaining tabs:
  - [ ] Primes/Clients Tab
  - [ ] Locations Tab
  - [ ] Customers Tab
  - [ ] Contractors Tab
  - [ ] Daily Playbook Tab

#### Day 18-19: BD Formula Generator
- [ ] Create `scripts/bd_formula_generator.py`
- [ ] Implement 6-step BD Formula:
  1. [ ] Personalized opener
  2. [ ] Pain point reference
  3. [ ] Labor gap reference
  4. [ ] PTS-GDIT past performance
  5. [ ] Program alignment
  6. [ ] Role alignment
- [ ] Generate messages for all contacts
  ```bash
  python scripts/bd_formula_generator.py \
    --contacts outputs/contacts_enriched.json \
    --output outputs/contacts_with_messages.json
  ```

#### Day 20: Create Program-Contact Relationships
- [ ] Build knowledge graph edges
  ```bash
  python scripts/create_relationships.py \
    --contacts bd_contacts \
    --jobs bd_jobs \
    --programs bd_programs
  ```
- [ ] Verify in Graphiti
  ```bash
  python scripts/verify_knowledge_graph.py
  ```

---

## PHASE 3: N8N BUILDER INTEGRATION (Week 5-6)

### Week 5: N8N Builder Audit & Indexing

#### Day 21: Audit N8N Builder Project
- [ ] **REQUIRED:** Receive DEEP_AUDIT_N8N_BUILDER.md
- [ ] Review audit findings
- [ ] Document indexable data:
  - [ ] Workflow files (`.json`)
  - [ ] Node configurations
  - [ ] Templates
  - [ ] Credentials (metadata only)

#### Day 22-23: Export N8N Data
- [ ] Export all workflows
  ```bash
  # Method depends on N8N Builder structure
  # Typically: n8n export:workflow --all --output=workflows/
  ```
- [ ] Export node catalog
- [ ] Export templates

#### Day 24-25: Index N8N Workflows
- [ ] Create `scripts/index_n8n.py`
- [ ] Run workflow indexing
  ```bash
  python scripts/index_n8n.py \
    --source "workflows/*.json" \
    --collection n8n_workflows
  ```
- [ ] Verify: 17+ workflows indexed

### Week 6: N8N Dashboard Integration

#### Day 26-27: Add N8N API Endpoints
- [ ] Add to `api/main.py`:
  - [ ] `GET /api/v1/n8n/workflows`
  - [ ] `POST /api/v1/n8n/workflows/search`
  - [ ] `GET /api/v1/n8n/nodes`
  - [ ] `GET /api/v1/n8n/templates`

#### Day 28-29: Create N8N Dashboard Section
- [ ] Create `dashboard/src/pages/N8NDashboard.tsx`
- [ ] Create tabs:
  - [ ] Workflows Tab
  - [ ] Templates Tab
  - [ ] Nodes Tab
- [ ] Add routes to `App.tsx`

#### Day 30: Create BD ↔ N8N Relationships
- [ ] Link job import workflows to jobs
- [ ] Link enrichment workflows to contacts
- [ ] Link export workflows to outputs
  ```bash
  python scripts/link_n8n_to_bd.py
  ```

---

## PHASE 4: DATA SCRAPER INTEGRATION (Week 7-8)

### Week 7: Data Scraper Audit & Indexing

#### Day 31: Audit Data Scraper Project
- [ ] **REQUIRED:** Receive DEEP_AUDIT_DATA-SCRAPER.md
- [ ] Review audit findings
- [ ] Document indexable data:
  - [ ] Source configurations
  - [ ] Extraction schemas
  - [ ] Output data samples

#### Day 32-33: Export Scraper Data
- [ ] Export source configurations
- [ ] Export schemas
- [ ] Sample extracted data

#### Day 34-35: Index Scraper Data
- [ ] Create `scripts/index_scraper.py`
- [ ] Run indexing
  ```bash
  python scripts/index_scraper.py \
    --sources "sources/*.json" \
    --collection scraper_sources
  ```
- [ ] Verify indexing

### Week 8: Scraper Dashboard Integration

#### Day 36-37: Add Scraper API Endpoints
- [ ] Add to `api/main.py`:
  - [ ] `GET /api/v1/scraper/sources`
  - [ ] `POST /api/v1/scraper/trigger`
  - [ ] `GET /api/v1/scraper/data`

#### Day 38-39: Create Scraper Dashboard Section
- [ ] Create `dashboard/src/pages/ScraperDashboard.tsx`
- [ ] Create tabs:
  - [ ] Sources Tab
  - [ ] Data Tab
  - [ ] Schedules Tab
- [ ] Add routes to `App.tsx`

#### Day 40: Create Scraper ↔ BD Relationships
- [ ] Link scraped job data to BD jobs
- [ ] Link scraped contact data to BD contacts
  ```bash
  python scripts/link_scraper_to_bd.py
  ```

---

## PHASE 5: UNIFIED INTELLIGENCE (Week 9-10)

### Week 9: Cross-Project Features

#### Day 41-42: Unified Search Implementation
- [ ] Create `dashboard/src/components/UnifiedSearch.tsx`
- [ ] Implement multi-project search UI
- [ ] Test cross-project queries

#### Day 43-44: Knowledge Graph Visualization
- [ ] Add visualization library (e.g., `react-force-graph`)
- [ ] Create `dashboard/src/pages/KnowledgeGraph.tsx`
- [ ] Implement interactive graph view

#### Day 45: Cross-Project Insights
- [ ] Create insights generator
  ```bash
  python scripts/generate_insights.py
  ```
- [ ] Display insights on unified dashboard

### Week 10: Deployment & Documentation

#### Day 46-47: Production Deployment
- [ ] Build dashboard for production
  ```bash
  cd dashboard && npm run build
  ```
- [ ] Deploy API with process manager
  ```bash
  pm2 start api/main.py --interpreter python3 --name unified-api
  ```
- [ ] Configure reverse proxy (nginx)
- [ ] Set up SSL certificates

#### Day 48-49: Testing & Verification
- [ ] End-to-end testing
- [ ] Load testing
- [ ] Security audit

#### Day 50: Documentation
- [ ] Update README files
- [ ] Create user guide
- [ ] Record demo video

---

## SUCCESS METRICS CHECKLIST

### Infrastructure
- [ ] Qdrant running with 9 collections
- [ ] API hub serving all endpoints
- [ ] Dashboard accessible and responsive
- [ ] Knowledge graph populated

### Data
- [ ] BD: 7,602+ contacts indexed
- [ ] BD: 388+ programs indexed
- [ ] BD: All jobs indexed
- [ ] N8N: All workflows indexed
- [ ] Scraper: All sources indexed

### Features
- [ ] Unified search works across all projects
- [ ] Cross-project relationships visible
- [ ] BD Formula messages generated
- [ ] Daily playbook automated

### Performance
- [ ] Search response < 500ms
- [ ] Dashboard load < 3s
- [ ] API uptime > 99%

---

## ROLLBACK PROCEDURES

### If Qdrant Fails
```bash
# Stop and remove container
docker-compose down

# Remove data (careful!)
rm -rf qdrant_storage/

# Restart fresh
docker-compose up -d qdrant

# Re-run indexing
python scripts/init_unified_collections.py
python scripts/index_all.py
```

### If API Fails
```bash
# Check logs
pm2 logs unified-api

# Restart
pm2 restart unified-api

# If persistent issue, rollback code
git checkout main -- api/
pm2 restart unified-api
```

### If Dashboard Fails
```bash
# Check build
npm run build

# If build fails, check dependencies
rm -rf node_modules package-lock.json
npm install
npm run build

# Restart
pm2 restart unified-dashboard
```

---

## SUPPORT CONTACTS

- **Technical Issues:** Create issue in Auto-Claude repo
- **Feedback:** https://github.com/anthropics/claude-code/issues

---

**END OF IMPLEMENTATION CHECKLIST**
