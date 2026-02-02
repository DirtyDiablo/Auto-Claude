# Week 3 Batch 2: Auto-Claude Enhancement Prompts

## Quick Reference

| Prompt # | Repository | Target Project | Terminal | Est. Time |
|----------|------------|----------------|----------|-----------|
| 1 | Stirling-PDF | data-scraper | 2-1 | 2-3 hours |
| 2 | Pathway | bd-automation-engine | 1-1 | 4-6 hours |
| 3 | Public-APIs | All Projects | Any | 1-2 hours |
| 4 | UI-UX-Pro-Max | n8n-builder | 3-1 | 2-3 hours |
| 5 | Supermemory | bd-automation-engine | 1-1 | 2-3 hours |

---

## EXECUTION CHECKLIST

### Terminal Assignment

| Terminal | Project | Prompts to Execute |
|----------|---------|-------------------|
| **1-1** | bd-automation-engine | #2 (Pathway), #3 (Public-APIs), #5 (Supermemory) |
| **2-1** | data-scraper | #1 (Stirling-PDF), #3 (Public-APIs) |
| **3-1** | n8n-builder | #4 (UI-UX-Pro-Max), #3 (Public-APIs) |

### Execution Order

1. **First:** Start Stirling-PDF Docker (Terminal 2-1)
2. **Parallel:** Run Prompts 1, 2, 4 in their respective terminals
3. **Shared:** Run Prompt 3 (Public-APIs) in any terminal, copy to all projects
4. **Last:** Run Prompt 5 (Supermemory) after Pathway is complete

---

# PROMPT 1: STIRLING-PDF INTEGRATION
## Target: data-scraper (Terminal 2-1)

### Copy This Prompt:

\`\`\`
## ENHANCEMENT: Stirling-PDF Integration for BD Document Processing

### OBJECTIVE
Integrate Stirling-PDF (https://github.com/Stirling-Tools/Stirling-PDF) to provide comprehensive PDF processing capabilities for RFP extraction, contract analysis, and proposal generation.

### CONTEXT
- Stirling-PDF is the #1 PDF tool on GitHub (71k+ stars) with 60+ operations
- It runs as a Docker container with REST API at port 8080
- We need it for: OCR scanned RFPs, extract tables from contracts, convert PDFs to Markdown for RAG, merge capability statements, compare contract versions

### DOCKER SETUP (Run First)
docker pull docker.stirlingpdf.com/stirlingtools/stirling-pdf
docker run -d -p 8080:8080 --name stirling-pdf docker.stirlingpdf.com/stirlingtools/stirling-pdf

### IMPLEMENTATION REQUIREMENTS

Create folder: pdf_processing/

#### File 1: pdf_processing/stirling_client.py

Create a StirlingPDFClient class with these methods:
- health_check() -> bool
- extract_text_ocr(pdf_path, languages=['eng'], ocr_type='normal') -> str
- extract_tables_to_csv(pdf_path, pages=None) -> List[Dict]
- extract_images(pdf_path, image_format='png') -> List[bytes]
- get_metadata(pdf_path) -> Dict
- pdf_to_markdown(pdf_path) -> str
- pdf_to_word(pdf_path) -> bytes
- pdf_to_excel(pdf_path) -> bytes
- html_to_pdf(html_content) -> bytes
- markdown_to_pdf(markdown_content) -> bytes
- merge_pdfs(pdf_paths: List[str]) -> bytes
- split_pdf(pdf_path, pages: str) -> bytes
- extract_pages(pdf_path, start_page, end_page) -> bytes
- compress_pdf(pdf_path, compression_level='recommended') -> bytes
- compare_pdfs(pdf1_path, pdf2_path) -> bytes
- add_watermark(pdf_path, watermark_text, opacity=0.3) -> bytes
- redact_text(pdf_path, text_to_redact: List[str]) -> bytes

Base URL: http://localhost:8080
Use httpx.AsyncClient with 300s timeout for large PDFs

#### File 2: pdf_processing/bd_pdf_pipeline.py

Create BDPDFPipeline class with workflows:
- process_rfp(rfp_path, output_dir) -> Dict with metadata, text, markdown, tables, requirements
- analyze_contract(contract_path, previous_version_path=None) -> Dict with text, tables, excel, diff_pdf, key_terms
- assemble_proposal(components: List[str], output_path, add_watermark=False, compress=True) -> str
- batch_process_rfps(rfp_folder, output_dir) -> List[Dict]

Include _extract_requirements() helper that finds lines with 'shall', 'must', 'required', 'mandatory'
Include _extract_contract_terms() helper that extracts dollar amounts and dates via regex

#### File 3: pdf_processing/__init__.py

Export StirlingPDFClient and BDPDFPipeline

### HUB INTEGRATION

Add FastAPI router with endpoints:
- GET /pdf/health - Check Stirling-PDF status
- POST /pdf/extract/text - OCR text extraction (file upload)
- POST /pdf/convert/markdown - PDF to Markdown
- POST /pdf/extract/tables - Tables to JSON
- POST /pdf/process/rfp - Full RFP pipeline
- POST /pdf/compress - Compress for email

### SUCCESS CRITERIA
1. Docker container running on port 8080
2. StirlingPDFClient can OCR scanned documents
3. Can extract tables from contract PDFs
4. Can convert PDFs to Markdown for RAG
5. Can merge multiple capability statements
6. Can compare contract versions
7. Hub API endpoints functional
8. BDPDFPipeline processes RFPs end-to-end
\`\`\`

---

# PROMPT 2: PATHWAY STREAMING INTEGRATION
## Target: bd-automation-engine (Terminal 1-1)

### Copy This Prompt:

\`\`\`
## ENHANCEMENT: Pathway Real-Time Streaming Pipeline

### OBJECTIVE
Integrate Pathway (https://github.com/pathwaycom/pathway) to provide real-time streaming capabilities for BD intelligence: live opportunity monitoring, contract alerts, and streaming RAG.

### CONTEXT
- Pathway is a Python ETL framework (62k+ stars) for stream processing and real-time RAG
- Powered by Rust engine with incremental computation
- Same code works for batch AND streaming
- Native LLM/RAG integration with vector indexing
- 300+ data source connectors (Kafka, PostgreSQL, GDrive, SharePoint)

### INSTALLATION
pip install pathway
pip install pathway[llm]

### IMPLEMENTATION REQUIREMENTS

Create folder: streaming/

#### File 1: streaming/pathway_config.py

Create PathwayConfig dataclass with:
- kafka_bootstrap_servers: str = "localhost:9092"
- kafka_security_protocol: str = "PLAINTEXT"
- postgres_connection: str
- s3_bucket: str
- openai_api_key: Optional[str]
- embedding_model: str = "text-embedding-3-small"
- batch_size: int = 100
- checkpoint_interval_ms: int = 30000

Include get_kafka_settings() helper function

#### File 2: streaming/bd_streaming_pipeline.py

Create BDStreamingPipeline class with methods:

DATA INGESTION:
- create_sam_opportunity_stream() -> pw.Table (schema: notice_id, title, agency, posted_date, response_deadline, set_aside, naics_code, description, estimated_value, place_of_performance)
- create_fpds_contract_stream() -> pw.Table (schema: contract_id, vendor_name, agency, award_date, award_amount, pop_start_date, pop_end_date, naics_code, description, contract_type)
- create_bullhorn_activity_stream() -> pw.Table (schema: activity_id, contact_id, activity_type, timestamp, notes, outcome)

REAL-TIME ANALYTICS:
- detect_relevant_opportunities(opportunities, target_naics, target_agencies, keywords) -> pw.Table
- detect_recompete_signals(contracts, days_threshold=365) -> pw.Table
- track_competitor_activity(contracts, competitors: List[str]) -> pw.Table
- calculate_pipeline_metrics(opportunities, activities) -> pw.Table

RAG INTEGRATION:
- create_streaming_rag(documents, embedding_model) -> VectorStoreServer

ALERTING:
- create_alert_stream(relevant_opps, recompete_signals, competitor_wins) -> pw.Table (unified alert stream)

OUTPUT SINKS:
- output_to_postgres(table, table_name)
- output_to_kafka(table, topic)
- output_alerts_to_webhook(alerts, webhook_url)

ORCHESTRATION:
- run_bd_intelligence_pipeline() - complete pipeline with hardcoded targets for DCGS

Use pw.io.csv.read() with mode="streaming" for demo data sources
Use pw.reducers for aggregations
Use pw.apply() for custom transformations

#### File 3: streaming/streaming_api.py

Create FastAPI router with endpoints:
- GET /streaming/status - Pipeline status
- POST /streaming/start - Start pipeline (PipelineConfig body)
- POST /streaming/stop - Stop pipeline
- GET /streaming/metrics - Current metrics

Use threading for background pipeline execution

#### File 4: streaming/__init__.py

Export BDStreamingPipeline, run_pipeline, PathwayConfig

### SUCCESS CRITERIA
1. Pathway installed and importable
2. Can create streaming data sources
3. Opportunity filtering works
4. Recompete detection works
5. Competitor tracking works
6. Alert stream combines all sources
7. Can output to PostgreSQL/Kafka
8. API endpoints control pipeline
\`\`\`

---

# PROMPT 3: PUBLIC-APIS REGISTRY
## Target: All Projects (Shared Utility)

### Copy This Prompt:

\`\`\`
## ENHANCEMENT: Public APIs Registry for BD Intelligence

### OBJECTIVE
Create a centralized registry of free public APIs relevant to BD intelligence, with clients for government data, business lookup, email validation, and geocoding.

### CONTEXT
- public-apis/public-apis is the largest API collection (379k+ stars)
- Contains 1,400+ free APIs across 45 categories
- We need APIs for: Government contracts, Company research, Contact validation, Location services

### IMPLEMENTATION REQUIREMENTS

Create folder: external_apis/

#### File 1: external_apis/api_registry.py

Create AuthType enum: NONE, API_KEY, OAUTH, BASIC

Create APIConfig dataclass:
- name: str
- base_url: str
- auth_type: AuthType
- auth_header: Optional[str]
- rate_limit: Optional[str]
- docs_url: Optional[str]
- description: str
- free_tier: str

Create PublicAPIRegistry class with APIS dict containing:

GOVERNMENT category:
- sam_gov: SAM.gov API (apiKey, x-api-key header)
- usaspending: USASpending (no auth)
- sec_edgar: SEC EDGAR (no auth)
- fpds: FPDS Atom feeds (no auth)
- data_gov: Data.gov catalog (no auth)
- beta_sam: SAM Entity API (apiKey)

BUSINESS category:
- clearbit_logo: Company logos (no auth)
- hunter: Email finder (apiKey query param)
- pdl: People Data Labs (apiKey)
- open_corporates: Company registry (apiKey)

EMAIL category:
- eva: Free validation (no auth)
- disify: Disposable detection (no auth)
- mailcheck_ai: Temp email detection (no auth)
- email_validator: Abstract API (apiKey)

PHONE category:
- numverify: Phone validation (apiKey)

GEOCODING category:
- nominatim: OpenStreetMap (no auth, 1/sec rate limit)
- positionstack: Geocoding (apiKey)
- ip_geolocation: IP lookup (apiKey)

FINANCE category:
- alpha_vantage: Stock data (apiKey)
- finnhub: Market data (apiKey)

Class methods:
- get_api(category, api_name) -> Optional[APIConfig]
- get_category(category) -> Dict[str, APIConfig]
- get_free_apis() -> List[APIConfig] (auth_type == NONE only)
- list_all() -> Dict[str, List[str]]

#### File 2: external_apis/government_client.py

Create SAMGovClient class:
- __init__(api_key)
- search_opportunities(keywords, naics_codes, set_aside, posted_from, posted_to, limit) -> Dict
- get_entity(uei) -> Dict
- close()

Create USASpendingClient class (no auth):
- __init__()
- search_awards(keywords, agencies, award_type, fiscal_year, limit) -> Dict
- get_agency_spending(agency_code) -> Dict
- get_contract_details(award_id) -> Dict
- close()

Use httpx.AsyncClient

#### File 3: external_apis/validation_client.py

Create EmailValidator class:
- __init__()
- validate_email(email) -> Dict (combines EVA and Disify results)
- _validate_eva(email) -> Dict
- _validate_disify(email) -> Dict
- _determine_validity(eva, disify) -> bool
- close()

Create GeocodingClient class (Nominatim):
- __init__(user_agent)
- geocode(address) -> Dict with lat, lon, display_name
- reverse_geocode(lat, lon) -> Dict
- close()

Use asyncio.gather for parallel API calls

#### File 4: external_apis/__init__.py

Export all classes and enums

### SUCCESS CRITERIA
1. API registry contains all BD-relevant APIs
2. SAM.gov client can search opportunities
3. USASpending client can search awards
4. Email validator combines multiple sources
5. Geocoding works without API key
6. All clients have proper error handling
\`\`\`

---

# PROMPT 4: UI-UX-PRO-MAX DESIGN INTELLIGENCE
## Target: n8n-builder (Terminal 3-1)

### Copy This Prompt:

\`\`\`
## ENHANCEMENT: UI-UX-Pro-Max Design Intelligence

### OBJECTIVE
Integrate UI-UX-Pro-Max design system generator for creating professional BD dashboards, proposals, and marketing materials with industry-appropriate styling.

### CONTEXT
- UI-UX-Pro-Max has 21k+ stars with 100 industry-specific reasoning rules
- 67 UI styles, 96 color palettes, 56 font pairings
- Provides complete design systems: colors, typography, patterns, anti-patterns
- We need it for: BD dashboards, proposal presentations, client-facing materials

### IMPLEMENTATION REQUIREMENTS

Create folder: design_intelligence/

#### File 1: design_intelligence/design_system.py

Create Industry enum: GOVERNMENT, DEFENSE, ENTERPRISE_SAAS, CONSULTING, FINANCIAL

Create ColorPalette dataclass:
- primary, secondary, accent, background, surface, text_primary, text_secondary: str
- success, warning, error, info: str (with defaults)
- to_css_vars() -> str (CSS custom properties)
- to_tailwind_config() -> Dict

Create Typography dataclass:
- heading_font, body_font, mono_font: str
- heading_weights, body_weights: List[int]
- get_google_fonts_url() -> str
- to_css() -> str

Create DesignSystem dataclass:
- name, industry, style: str
- colors: ColorPalette
- typography: Typography
- spacing_unit, border_radius, shadow, transition: str
- anti_patterns: List[str]
- notes: str
- to_css() -> str (complete CSS output)

Create DesignSystemGenerator class with INDUSTRY_RULES dict containing:

GOVERNMENT:
- style: "Accessible & Ethical + Swiss Modernism"
- colors: Navy blue primary (#003366), red accent (#CC0000)
- typography: Source Sans Pro / Open Sans
- anti_patterns: Dark mode only, Low contrast, Complex animations, AI gradients

DEFENSE:
- style: "Swiss Modernism 2.0 + Data-Dense Dashboard"
- colors: Dark blue primary (#1A365D), dark background (#1A202C)
- typography: Inter / IBM Plex Sans
- anti_patterns: Consumer aesthetics, Playful animations, Bright colors

ENTERPRISE_SAAS:
- style: "Minimalism + Glassmorphism"
- colors: Indigo primary (#4F46E5), emerald secondary (#10B981)
- typography: Poppins / Inter
- anti_patterns: Dated gradients, Excessive shadows, Busy layouts

CONSULTING:
- style: "Trust & Authority + Editorial Grid"
- colors: Slate primary (#0F172A), blue secondary (#1E40AF)
- typography: Merriweather / Source Sans Pro (serif heading for authority)
- anti_patterns: Tech startup vibes, Playful illustrations, Casual tone

FINANCIAL:
- style: "Financial Dashboard + Trust & Authority"
- colors: Teal primary (#0D9488), deep blue secondary (#1E3A8A)
- typography: DM Sans / Inter
- anti_patterns: Playful colors, Casual fonts, AI purple gradients

Class methods:
- generate(industry, project_name) -> DesignSystem
- generate_for_bd(project_name) -> DesignSystem (DEFENSE style optimized for BD dashboards)
- validate_design(design) -> List[str] (warnings for anti-patterns)

#### File 2: design_intelligence/component_library.py

Create BDComponentStyles class with static methods:
- get_priority_badge_styles() -> str (Critical=red, High=orange, Medium=yellow, Standard=gray)
- get_contact_card_styles() -> str (avatar, info, actions layout)
- get_pipeline_chart_styles() -> str (stage indicators, value display)
- get_all_styles(design_system) -> str (combines design system + components)

#### File 3: design_intelligence/__init__.py

Export all classes and enums

### SUCCESS CRITERIA
1. Can generate design systems for all industries
2. BD-specific design system works
3. CSS output is valid
4. Google Fonts URLs generated correctly
5. Component styles integrate with design system
6. Anti-pattern validation works
\`\`\`

---

# PROMPT 5: SUPERMEMORY INTEGRATION
## Target: bd-automation-engine (Terminal 1-1)

### Copy This Prompt:

\`\`\`
## ENHANCEMENT: Supermemory AI Memory Integration

### OBJECTIVE
Integrate Supermemory as a complementary memory system to Mem0, providing fast document storage and retrieval with MCP integration for Claude.

### CONTEXT
- Supermemory (13.7k+ stars) is a memory engine for saving/organizing information
- Supports URLs, PDFs, plain text, Notion, Google Drive, OneDrive
- Has MCP integration for Claude, Cursor, and other AI tools
- Complements Mem0 by providing document-level memory vs conversation memory

### IMPLEMENTATION REQUIREMENTS

Create file: memory/supermemory_client.py

Create SupermemoryClient class:
- __init__(api_key, base_url="https://api.supermemory.ai")
- Uses httpx.AsyncClient with Bearer token auth

MEMORY MANAGEMENT:
- add_memory(content, source_type='text', metadata=None, tags=None) -> Dict
- add_url(url, tags=None) -> Dict
- add_document(file_path, title=None, tags=None) -> Dict (with file upload)
- get_memory(memory_id) -> Dict
- delete_memory(memory_id) -> bool
- list_memories(limit=50, offset=0, tags=None) -> List[Dict]

SEARCH:
- search(query, top_k=10, tags=None, min_score=0.0) -> List[Dict]
- search_by_document_type(query, doc_type, top_k=10) -> List[Dict]

CHAT:
- chat(message, conversation_id=None) -> Dict (AI response with citations)

INTEGRATIONS:
- sync_notion(workspace_id, database_id=None) -> Dict
- sync_google_drive(folder_id) -> Dict
- get_sync_status() -> Dict

COLLECTIONS:
- create_collection(name, description=None) -> Dict
- add_to_collection(collection_id, memory_ids) -> Dict

HELPER:
- _get_mime_type(extension) -> str
- close(), __aenter__, __aexit__

Create BDMemoryManager class:
- __init__(supermemory_key, mem0_client=None)
- DOC_TAGS dict: rfp, contract, proposal, capability, past_performance, contact_research, competitor

BD-SPECIFIC METHODS:
- store_rfp(file_path, title, agency=None, deadline=None) -> Dict
- store_contract(file_path, contract_number, contractor=None) -> Dict
- search_rfps(query, top_k=5) -> List[Dict]
- search_contracts(query, contractor=None, top_k=5) -> List[Dict]
- ask_about_documents(question) -> Dict (uses chat with RAG)
- close()

### HUB INTEGRATION

Add FastAPI router:
- POST /memory/add - Add memory
- POST /memory/search - Search memories
- POST /memory/chat - Chat with memories

### SUCCESS CRITERIA
1. Can add text memories
2. Can add URL memories
3. Can upload documents
4. Semantic search works
5. Chat with memories works
6. BD-specific tagging works
7. Hub API endpoints functional
\`\`\`

---

## POST-ENHANCEMENT VERIFICATION

### Test Commands

# Verify Stirling-PDF
curl http://localhost:8080/api/v1/info/status

# Verify Hub endpoints
curl http://localhost:8000/pdf/health
curl http://localhost:8000/streaming/status
curl http://localhost:8000/memory/search -X POST -d '{"query":"test"}'

# Verify imports
python -c "from pdf_processing import StirlingPDFClient; print('OK')"
python -c "from streaming import BDStreamingPipeline; print('OK')"
python -c "from external_apis import PublicAPIRegistry; print('OK')"
python -c "from design_intelligence import DesignSystemGenerator; print('OK')"
