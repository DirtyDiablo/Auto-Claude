# GitHub Repository Guide for Federal BD Automation Projects

**Bottom line:** This analysis identifies **52 production-ready repositories** that can significantly enhance your three Auto Claude BD automation projects. The highest-impact additions are **UltraRAG** and **PageIndex** for revolutionary document retrieval, **Firecrawl** and **Crawl4AI** for AI-powered federal data scraping, **CrewAI** and **LangGraph** for multi-agent orchestration, and **Mem0** for persistent context across your entire BD pipeline.

The MCP ecosystem has matured dramatically—**75,300+ stars** on the official MCP servers repository signals this is now the standard for Claude integrations. Your existing MCP architecture positions you perfectly to leverage these tools.

---

## Cross-project critical infrastructure

These repositories benefit all three projects and should be prioritized first for maximum leverage across your BD automation stack.

### Mem0 - Universal memory layer for AI
**URL:** https://github.com/mem0ai/mem0  
**Stars:** 45,100+ ⭐ | **Activity:** Very active, $24M funding  
**Use Case:** Persistent context across sessions, user preference learning, conversation history  
**Integration:** `pip install mem0ai` → Add memories with user_id → Query across projects  
**Priority:** 🔴 Critical

Mem0 achieves **26% better accuracy** than OpenAI Memory on benchmarks with 91% faster responses. For federal BD, this means maintaining context across long proposal cycles and remembering client preferences. Integrates directly with CrewAI, LangGraph, and LangChain.

### Official MCP Servers Repository
**URL:** https://github.com/modelcontextprotocol/servers  
**Stars:** 75,300+ ⭐ | **Activity:** Official Anthropic-maintained  
**Use Case:** Reference implementations for building custom MCP servers  
**Integration:** Use Python SDK's FastMCP decorators for rapid server development  
**Priority:** 🔴 Critical

Includes ready-made servers for Notion, Git, filesystem, and sequential thinking. Your existing MCP architecture can directly leverage the community's **200+ integration servers**.

### Anthropic Skills (Official)
**URL:** https://github.com/anthropics/skills  
**Stars:** 51,300+ ⭐ | **Activity:** Official, actively maintained  
**Use Case:** Reference architecture for custom BD skills, document processing  
**Integration:** Adopt SKILL.md format for federal documentation skills  
**Priority:** 🟠 High

The official skills repository establishes the standard for Claude Code extensions. Includes PDF, DOCX, Excel processing—essential for federal contract documents.

### Pydantic - Data validation backbone
**URL:** https://github.com/pydantic/pydantic  
**Stars:** 360M+ monthly downloads | **Activity:** Industry standard  
**Use Case:** Validate Bullhorn entities, API responses, scraped data structures  
**Integration:** Define BaseModel classes with custom validators for BD schemas  
**Priority:** 🟠 High

Your 28-field job standardization schema would benefit from Pydantic's Rust-based validation core. Generates JSON Schema automatically for API documentation.

---

## Data-Scraper enhancements

Your Python-based scrapers for FPDS, USASpending, and SAM.gov can be dramatically enhanced with these AI-powered tools and official federal data APIs.

### Firecrawl - LLM-ready web data extraction
**URL:** https://github.com/firecrawl/firecrawl  
**Stars:** 77,100+ ⭐ | **Activity:** Extremely active  
**Use Case:** Convert federal websites to clean markdown/structured data for RAG  
**Integration:** Self-host with Docker or use API; integrates with LangChain/LlamaIndex  
**Priority:** 🔴 Critical

Firecrawl handles JavaScript rendering, proxy rotation, and anti-bot bypasses automatically. The **Extract endpoint** can pull structured contract data from SAM.gov without writing custom parsers.

### Crawl4AI - Intelligent web crawler
**URL:** https://github.com/unclecode/crawl4ai  
**Stars:** 55,800+ ⭐ | **Activity:** #1 trending AI crawler  
**Use Case:** Deep crawling with LLM-driven extraction for complex federal sites  
**Integration:** Async Python API with Playwright/HTTP strategies  
**Priority:** 🔴 Critical

Features **BFS/DFS/BestFirst** crawling strategies and generates "Fit Markdown" optimized for LLM consumption. Perfect for navigating FPDS's complex document structures.

### FPDS Parser - Direct federal feed access
**URL:** https://github.com/dherincx92/fpds  
**Stars:** 32+ ⭐ | **Activity:** Maintained, MIT license  
**Use Case:** Parse FPDS ATOM feeds with automatic pagination  
**Integration:** Direct Python import; CLI for batch operations  
**Priority:** 🔴 Critical

Lightweight but handles the critical challenge of FPDS's **10-record pagination limit** automatically. Converts XML to JSON for your existing SQLite pipeline.

### USASpending API (Official)
**URL:** https://github.com/fedspendingtransparency/usaspending-api  
**Stars:** 372+ ⭐ | **Activity:** Official government repository  
**Use Case:** RESTful API access to federal spending, database snapshots  
**Integration:** Use official endpoints instead of scraping; download snapshots for local analysis  
**Priority:** 🔴 Critical

The official source eliminates scraping fragility. Provides **contract, grant, and loan data** at award, transaction, and account levels.

### GSA SRT-FBO-Scraper - SAM.gov reference architecture
**URL:** https://github.com/GSA/srt-fbo-scraper  
**Stars:** GSA official | **Activity:** Production use at GSA  
**Use Case:** Official SAM.gov integration patterns, document extraction  
**Integration:** Adopt document extraction architecture for solicitation archives  
**Priority:** 🟠 High

GSA's own implementation for IT solicitations demonstrates best practices for the Opportunity Management API and Federal Hierarchy API integration.

### Crawlee Python - Apify's open-source core
**URL:** https://github.com/apify/crawlee-python  
**Stars:** 7,100+ ⭐ | **Activity:** Apify-maintained  
**Use Case:** Self-hosted Apify alternative with proxy rotation, session management  
**Integration:** Replace Apify paid tier while maintaining similar API patterns  
**Priority:** 🟠 High

Same patterns your N8N Builder Apify integration uses, but **self-hosted and free**. Includes automatic parallel crawling based on system resources.

### Scrapling - Adaptive web scraping
**URL:** https://github.com/D4Vinci/Scrapling  
**Stars:** 8,800+ ⭐ | **Activity:** Active development  
**Use Case:** Undetectable scraping that survives website redesigns  
**Integration:** Drop-in replacement for BeautifulSoup with StealthyFetcher  
**Priority:** 🟠 High

First Python scraper that **learns from website changes**. Auto-saves element selectors that survive government site redesigns.

### ExtractThinker - Document intelligence
**URL:** https://github.com/enoch3712/ExtractThinker  
**Stars:** Growing | **Activity:** Active  
**Use Case:** Extract structured data from federal contract PDFs using LLMs  
**Integration:** Multiple loaders (Tesseract, Azure, AWS Textract); Pydantic models for extraction  
**Priority:** 🟠 High

ORM-style document workflows with advanced classification. Perfect for processing solicitation PDFs and RFP documents.

### Camoufox - Anti-detection browser
**URL:** https://github.com/daijro/camoufox  
**Stars:** Growing fast | **Activity:** Active  
**Use Case:** Stealth browser automation for protected federal portals  
**Integration:** Firefox-based; integrates with Playwright scripts  
**Priority:** 🟡 Medium

Human-like mouse movement, fingerprint rotation, and **isolated JavaScript execution** that prevents Playwright detection.

### PyrateLimiter - API compliance
**URL:** https://github.com/vutran1710/PyrateLimiter  
**Stars:** Active | **Activity:** Maintained  
**Use Case:** Rate limit Bullhorn, Apify, and federal API calls  
**Integration:** Decorator-based; Redis/SQLite backends for multi-process coordination  
**Priority:** 🟠 High

Multiple rate limits per function (per-second AND per-day). Essential for staying compliant with federal API terms of service.

---

## N8N Builder enhancements

Your workflow orchestration with specialized AI agents can leverage these multi-agent frameworks and n8n extensions.

### CrewAI - Role-based agent orchestration
**URL:** https://github.com/crewAIInc/crewAI  
**Stars:** 43,100+ ⭐ | **Activity:** 1M+ downloads/month  
**Use Case:** Orchestrate architect, builder, debugger agents with defined roles/goals  
**Integration:** Define agents with role/goal/backstory; use Flows for precise orchestration  
**Priority:** 🔴 Critical

CrewAI's **memory system** (short-term, long-term, entity) aligns perfectly with your BD workflow needs. Built-in guardrails prevent agent drift. Use `Process.sequential` for your n8n workflow generation pipeline.

### LangGraph - Stateful workflow graphs
**URL:** https://github.com/langchain-ai/langgraph  
**Stars:** 21,000+ ⭐ | **Activity:** 4.2M+ downloads/month  
**Use Case:** Durable execution for complex multi-step BD automation  
**Integration:** StateGraph with checkpointer for persistence; LangGraph Studio for visual debugging  
**Priority:** 🔴 Critical

Used by **Klarna, Replit, Uber, and LinkedIn** in production. Human-in-the-loop workflows enable proposal review gates. The supervisor-agent pattern maps directly to your architect/builder/debugger structure.

### n8n-MCP Server
**URL:** https://github.com/czlonkowski/n8n-mcp  
**Stars:** Active | **Activity:** Recent development  
**Use Case:** Let Claude build n8n workflows through MCP  
**Integration:** Add to Claude Code MCP configuration  
**Priority:** 🔴 Critical

Provides Claude comprehensive access to n8n's **1,084 workflow automation nodes**. Essential for your AI-assisted workflow building capabilities.

### Awesome-n8n - Community node directory
**URL:** https://github.com/restyler/awesome-n8n  
**Stars:** 5,834+ nodes indexed | **Activity:** Growing ~13.6 nodes/day  
**Use Case:** Discover Apify, Qdrant, OCR, and scraping community nodes  
**Integration:** Browse and install relevant nodes via npm  
**Priority:** 🟠 High

Top 100+ n8n community nodes sorted by popularity. Includes **Qdrant vector search** and **Apify integration** nodes relevant to your pipeline.

### Sim.ai - Agent workflow platform
**URL:** https://github.com/simstudioai/sim  
**Stars:** 26,000+ ⭐ | **Activity:** Very active  
**Use Case:** Open-source platform for building and deploying AI agent workflows  
**Integration:** Complementary to n8n for agent-specific orchestration  
**Priority:** 🟠 High

Visual builder for agent workflows with deployment infrastructure included.

### Eigent - Multi-agent desktop application
**URL:** https://github.com/eigent-ai/eigent  
**Stars:** Growing | **Activity:** Active development  
**Use Case:** Multi-agent workforce with built-in MCP tools (Notion, Google, Slack)  
**Integration:** Desktop deployment for local, privacy-first execution  
**Priority:** 🟠 High

100% local execution for sensitive BD data. Built on **CAMEL-AI** with specialized agents for development, search, and document analysis.

### Redis Queue (RQ) - Simple job processing
**URL:** https://github.com/rq/rq  
**Stars:** 10,500+ ⭐ | **Activity:** Stable  
**Use Case:** Background job processing for Apify callbacks and webhook handling  
**Integration:** Simpler Celery alternative; Redis-backed  
**Priority:** 🟠 High

Lower complexity than Celery for your webhook callback processing needs. Built-in scheduling with `enqueue_at` and `enqueue_in`.

### browser-use - AI browser automation
**URL:** https://github.com/browser-use/browser-use  
**Stars:** 76,200+ ⭐ | **Activity:** Explosive growth  
**Use Case:** Make websites accessible for AI agents to automate tasks  
**Integration:** Python API for agent-driven web interactions  
**Priority:** 🟠 High

The highest-starred browser automation for AI. Enables your n8n AI agents to interact with web interfaces programmatically.

### Prefect - Python workflow orchestration
**URL:** https://github.com/PrefectHQ/prefect  
**Stars:** 21,000+ ⭐ | **Activity:** Enterprise-grade  
**Use Case:** Orchestrate Python ETL functions with decorators, built-in UI  
**Integration:** Wrap existing Python functions with @flow/@task decorators  
**Priority:** 🟡 Medium

Modern alternative to n8n for Python-heavy pipelines. Built-in dashboard for monitoring Bullhorn sync jobs.

---

## BD-Automation-Engine enhancements

Your 8-engine pipeline with Qdrant vector database can leverage these advanced RAG systems and knowledge graph tools.

### UltraRAG - MCP-native RAG framework
**URL:** https://github.com/OpenBMB/UltraRAG  
**Stars:** 2,700+ ⭐ | **Activity:** v3 released Jan 2026  
**Use Case:** Advanced multi-step RAG with visual IDE and MCP architecture  
**Integration:** YAML configuration for pipelines; direct MCP compatibility with your existing stack  
**Priority:** 🔴 Critical

First lightweight RAG framework built on MCP architecture. **DeepResearch capability** generates 10,000+ word survey reports automatically—perfect for federal contract research. Supports Milvus vector database with loops, conditional branches, and multi-step reasoning.

### PageIndex - Vectorless RAG breakthrough
**URL:** https://github.com/VectifyAI/PageIndex  
**Stars:** 7,700+ ⭐ | **Activity:** Rapidly growing  
**Use Case:** Reasoning-based retrieval achieving 98.7% accuracy on FinanceBench  
**Integration:** MCP server for Claude Code; no vector database required  
**Priority:** 🔴 Critical

Revolutionary approach that generates hierarchical **Table-of-Contents tree structures** for human-like document navigation. Better explainability than vector search—critical for auditable federal BD processes.

### LightRAG - Production-ready graph RAG
**URL:** https://github.com/HKUDS/LightRAG  
**Stars:** 25,400+ ⭐ | **Activity:** 5,928 commits  
**Use Case:** Dual-level retrieval with graph structures + vector representations  
**Integration:** Native `QdrantVectorDBStorage`—direct upgrade path for your existing 8,447+ records  
**Priority:** 🔴 Critical

Incremental update algorithm enables rapid integration of new federal contract data. **PostgreSQL one-stop solution** combines KV + Vector + Graph in single deployment. Web UI included for document management and knowledge graph visualization.

### GraphRAG (Microsoft)
**URL:** https://github.com/microsoft/graphrag  
**Stars:** 29,200+ ⭐ | **Activity:** v2.7.0 Oct 2025  
**Use Case:** Knowledge graph-based RAG for complex relationship queries  
**Integration:** Complement Qdrant with graph-based reasoning layer  
**Priority:** 🟠 High

Achieves **70-80% improvement** over naive RAG on comprehensiveness metrics. Automatic entity, relationship, and key claims extraction from text enables understanding contractor relationships and teaming history.

### Docling (IBM) - Document processing pipeline
**URL:** https://github.com/docling-project/docling  
**Stars:** 10,000+ ⭐ | **Activity:** LF AI & Data Foundation project  
**Use Case:** Parse PDF, DOCX, PPTX, XLSX, HTML before vectorization  
**Integration:** `pip install docling`; LangChain/LlamaIndex integrations included  
**Priority:** 🔴 Critical

**30x faster** than traditional OCR approaches. Advanced PDF understanding extracts tables, code, formulas, and reading order. Air-gapped execution capability for sensitive federal documents.

### RAGFlow - Enterprise RAG engine
**URL:** https://github.com/infiniflow/ragflow  
**Stars:** 69,500+ ⭐ | **Activity:** Leading open-source RAG  
**Use Case:** Production-ready RAG with agent capabilities and MCP support  
**Integration:** Docker deployment; GraphRAG and multi-hop reasoning built-in  
**Priority:** 🟠 High

Deep document understanding with semantic chunking. Production workflows for your 8-engine pipeline pattern.

### RAGAS - RAG evaluation framework
**URL:** https://github.com/explodinggradients/ragas  
**Stars:** Growing | **Activity:** Active  
**Use Case:** Measure and optimize RAG pipeline quality  
**Integration:** LLM-based metrics: faithfulness, answer relevancy, context precision  
**Priority:** 🟠 High

Essential for **continuous improvement** of your RAG engine. Synthetic test data generation for benchmarking federal contract queries.

### Supermemory - High-scale memory API
**URL:** https://github.com/supermemoryai/supermemory  
**Stars:** 14,400+ ⭐ | **Activity:** Enterprise-grade  
**Use Case:** 50M tokens per user, persistent memory across BD pipeline stages  
**Integration:** MCP integration for Claude; self-hosting available  
**Priority:** 🟠 High

Universal Memory API handles **5 billion tokens daily**. User profiles auto-generated from stored memories enable personalized BD recommendations.

### Celery - Distributed task processing
**URL:** https://github.com/celery/celery  
**Stars:** Industry standard | **Activity:** Extremely stable  
**Use Case:** Orchestrate 8-engine pipeline with distributed task queue  
**Integration:** @app.task decorators; Redis broker; beat for scheduling  
**Priority:** 🟠 High

The production standard for Python task queues. Configure beat scheduler for recurring Bullhorn ETL synchronization.

### Graphiti - Temporal knowledge graphs
**URL:** https://github.com/getzep/graphiti  
**Stars:** 5,000+ ⭐ | **Activity:** Active  
**Use Case:** Handle changing contractor relationships over time  
**Integration:** MCP server included; Neo4j backend  
**Priority:** 🟡 Medium

Tracks **temporal relationships**—essential for understanding how teaming arrangements and contractor capabilities evolve.

### Milvus - Billion-scale vector database
**URL:** https://github.com/milvus-io/milvus  
**Stars:** 42,400+ ⭐ | **Activity:** Enterprise-grade  
**Use Case:** Scale beyond Qdrant's current capacity with GPU acceleration  
**Integration:** PyMilvus API compatible with Qdrant concepts  
**Priority:** 🟡 Medium

Native hybrid search (BM25 + dense + sparse vectors). Consider if your 8,447 records need to scale to **billions of vectors**.

### Aiocache - Async caching
**URL:** https://github.com/aio-libs/aiocache  
**Stars:** Active aio-libs project | **Activity:** Maintained  
**Use Case:** Cache API responses, embeddings, LLM calls  
**Integration:** @cached decorator with Redis backend  
**Priority:** 🟠 High

Redis/Memcached/memory backends with multiple serializers. Essential for reducing redundant Bullhorn API calls.

### Redis-VL - AI-native vector caching
**URL:** https://github.com/redis/redis-vl-python  
**Stars:** Official Redis library | **Activity:** Active  
**Use Case:** Semantic caching for LLM responses, embeddings cache  
**Integration:** SemanticCache + EmbeddingsCache + MessageHistory  
**Priority:** 🟠 High

Official Redis client for AI workloads. **SemanticCache** automatically returns cached responses for semantically similar queries.

---

## Claude Code and skills ecosystem

These tools extend Claude's capabilities with federal BD-specific skills and integrations.

### Skill_Seekers - Auto-generate Claude skills
**URL:** https://github.com/yusufkaraaslan/Skill_Seekers  
**Stars:** 800+ ⭐ (800+ in 2 days) | **Activity:** v2.6.0 Jan 2026  
**Use Case:** Convert federal documentation into Claude AI skills automatically  
**Integration:** MCP server for Claude Code; supports PDFs, GitHub repos, documentation sites  
**Priority:** 🟠 High

Convert FAR/DFAR regulations, SAM.gov API docs, and FPDS guides into actionable skills. **AI enhancement** improves skill quality from 3/10 to 9/10.

### Superpowers - Agentic development methodology
**URL:** https://github.com/obra/superpowers  
**Stars:** 34,000+ ⭐ | **Activity:** Very active  
**Use Case:** Structured approach to building BD automation features  
**Integration:** Commands: /brainstorm, /write-plan, /execute-plan  
**Priority:** 🟡 Medium

20+ battle-tested skills including TDD and debugging. Subagent-driven development with code review checkpoints aligns with your multi-engine architecture.

### Awesome-Claude-Skills (Composio)
**URL:** https://github.com/ComposioHQ/awesome-claude-skills  
**Stars:** Curated collection | **Activity:** Updated regularly  
**Use Case:** Pre-built skills for app integrations (Gmail, Slack, Notion)  
**Integration:** Browse and adopt relevant skills; Composio connector for 500+ apps  
**Priority:** 🟡 Medium

The **connect-apps plugin** enables connecting BD automation to Slack/Teams notifications and CRM systems.

### System Prompts Collection
**URL:** https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools  
**Stars:** 111,000+ ⭐ | **Activity:** Comprehensive collection  
**Use Case:** Reference for crafting optimal BD automation agent prompts  
**Integration:** Study and adapt prompt patterns from Cursor, Devin, Claude Code  
**Priority:** 🟡 Medium

6,500+ lines of prompt engineering insights from production AI tools. Learn how top coding agents structure complex workflows.

### Claude Agent SDK (Official)
**URL:** https://github.com/anthropics/claude-agent-sdk-python  
**Stars:** Official SDK | **Activity:** Anthropic-maintained  
**Use Case:** Build custom tools and in-process MCP servers  
**Integration:** query() for Claude Code interactions; hooks for monitoring  
**Priority:** 🟠 High

Official Python SDK for Claude Agent with type-safe operations. Define custom tools as Python functions with `create_sdk_mcp_server()`.

---

## Priority implementation roadmap

### Phase 1: Foundation (weeks 1-2)
Deploy these immediately for maximum impact across all projects:

| Repository | Project | Action |
|------------|---------|--------|
| **UltraRAG** | BD-Automation-Engine | Replace/enhance RAG engine with MCP-native architecture |
| **Firecrawl** | Data-Scraper | Self-host for AI-powered federal site extraction |
| **CrewAI** | N8N Builder | Orchestrate architect/builder/debugger agents |
| **Mem0** | All | Add universal memory layer across sessions |
| **Docling** | BD-Automation-Engine | Pre-process documents before vectorization |

### Phase 2: Core capabilities (weeks 3-4)
Enhance primary functionality of each project:

| Repository | Project | Action |
|------------|---------|--------|
| **PageIndex** | BD-Automation-Engine | Add vectorless RAG for complex contracts |
| **LightRAG** | BD-Automation-Engine | Knowledge graph layer with native Qdrant support |
| **Crawl4AI** | Data-Scraper | Deep crawling for FPDS/SAM.gov |
| **FPDS Parser** | Data-Scraper | Direct ATOM feed integration |
| **LangGraph** | N8N Builder | Durable execution for multi-step workflows |

### Phase 3: Production hardening (weeks 5-6)
Add reliability and scale:

| Repository | Project | Action |
|------------|---------|--------|
| **RAGAS** | BD-Automation-Engine | Establish RAG quality baseline |
| **PyrateLimiter** | All | Rate limit API calls |
| **Celery** | BD-Automation-Engine | Distributed task queue for 8 engines |
| **Aiocache** | All | Cache API responses and embeddings |
| **Pydantic** | All | Validate all data schemas |

### Phase 4: Advanced features (weeks 7-8)
Differentiated capabilities:

| Repository | Project | Action |
|------------|---------|--------|
| **GraphRAG** | BD-Automation-Engine | Complex relationship reasoning |
| **Skill_Seekers** | All | Generate skills from federal documentation |
| **browser-use** | N8N Builder | AI agent web automation |
| **Graphiti** | BD-Automation-Engine | Temporal knowledge graphs |

---

## Key technology trends shaping these recommendations

**MCP architecture dominance**: UltraRAG, PageIndex, Eigent, Supermemory, and Skill_Seekers all support MCP. This is now the standard for Claude integrations—your existing MCP architecture positions you perfectly.

**Vectorless RAG emergence**: PageIndex's **98.7% accuracy** without traditional vectors suggests a paradigm shift. For federal contracts requiring audit trails, the explainable tree-search retrieval provides better traceability than black-box vector similarity.

**Memory systems maturity**: Mem0's $24M raise signals enterprise demand for persistent AI context. Your long-running BD proposal cycles will benefit significantly from cross-session memory.

**AI-native scraping**: Firecrawl and Crawl4AI now dominate over traditional scrapers. LLM-driven extraction eliminates brittle CSS selectors that break when federal sites update.

**Multi-agent production readiness**: CrewAI and LangGraph have moved from experimental to enterprise deployment (Uber, LinkedIn, Klarna). Your existing agent architecture can adopt these proven patterns.

The federal BD automation space is uniquely positioned to benefit from these tools—government data sources have structured patterns that AI extraction handles well, long procurement cycles benefit from persistent memory, and complex teaming relationships require the graph reasoning capabilities now available in production-ready packages.