# The definitive stack for a 11K-file AI-powered project indexer

**LanceDB hybrid search, tree-sitter AST parsing, Neo4j lineage graphs, and a tiered LLM classification pipeline represent the optimal upgrade path** for a custom project indexer already running Qdrant, Neo4j, and FastAPI. The critical insight: most of the best-in-class tooling either already exists in your stack or plugs directly into it. You do not need a wholesale replacement of SQLite+FTS5—you need strategic augmentation across six layers, leveraging what's already deployed. This report evaluates 60+ tools across all eight layers, with concrete GitHub repos, version numbers, and integration blueprints for a Windows 11 + Claude Code environment.

---

## Layer 1: Tree-sitter and Docling should replace the custom crawler

The custom Python crawler using `ast`, `csv.reader`, and `openpyxl` works but locks you into per-format parsing code that doesn't scale. Two tools transform this layer entirely.

**Tree-sitter** (via `tree-sitter-language-pack`, **165+ languages**, py-tree-sitter v0.25.2) should replace Python's `ast` module for all code parsing. It produces concrete syntax trees with error recovery, incremental re-parsing, and a powerful query language for extracting functions, classes, imports, and dependencies. Every major AI code tool—Aider, Cursor, Continue.dev, Cline—uses tree-sitter as their parsing backbone. Install via `pip install tree-sitter-language-pack` and write unified extractors for Python, TypeScript, and JSON in a single API. It is strictly superior to `ast` for multi-language projects.

**IBM Docling** (~52.7K GitHub stars, v2.72.0, MIT license) should handle all non-code files: XLSX, CSV, PDF, DOCX, PPTX, and images. Backed by IBM Research Zurich and the LF AI & Data Foundation, it converts documents into structured Markdown/JSON with AI-powered layout analysis, table structure recognition, and OCR. IBM processed **2.1 million PDFs** from Common Crawl with Docling. It has native integrations with LangChain, LlamaIndex, and CrewAI (already in your stack), plus an MCP server for AI agent access. Install via `pip install docling`.

**Aider's repo-map technique** (tree-sitter + PageRank graph ranking) is the third critical addition. Aider builds a dependency graph where files are nodes and symbol references create edges, then applies PageRank to identify the most important code across your three interconnected projects. A standalone reimplementation called **RepoMapper** (github.com/pdavis68/RepoMapper) provides this as both CLI and MCP server. For 11K+ files across 3 projects, the graph-ranking approach is invaluable for prioritizing what matters.

| Tool | Purpose | Stars | Local | Mixed types | Install |
|------|---------|-------|-------|-------------|---------|
| **tree-sitter-language-pack** | Multi-lang AST parsing | Large ecosystem | ✅ | Code only | `pip install tree-sitter-language-pack` |
| **IBM Docling** | Document/data extraction | ~52.7K | ✅ | XLSX/PDF/DOCX/CSV | `pip install docling` |
| **RepoMapper** | Cross-project importance ranking | Growing | ✅ | Code only | `pip install repomapper` |
| **Repomix** | LLM-friendly repo packing | ~20.8K | ✅ | Text files | `npx repomix` |

**Skip Greptile** (SaaS-only, no open-source indexing library). **Repomix** (~20.8K stars, MIT) is useful as a complementary tool for creating LLM context snapshots but is a packing tool, not a metadata extractor.

---

## Layer 2: LanceDB hybrid search is the single biggest upgrade

SQLite FTS5 remains excellent for 11K documents—queries return in sub-milliseconds. The real gap is the absence of **semantic search** and **hybrid ranking**. The answer is already in your stack.

**LanceDB should become the primary hybrid search engine.** It natively combines vector similarity search with BM25 keyword search (powered internally by **Tantivy**, the Rust full-text search library that benchmarks at **~2× faster than Lucene**). LanceDB's hybrid search API is clean and production-ready:

```python
table.search("authentication handler", query_type="hybrid")
     .rerank(reranker=RRFReranker())  # Reciprocal Rank Fusion
     .limit(10)
     .to_pandas()
```

LanceDB supports multiple built-in rerankers: RRF (default), LinearCombination, Cohere, CrossEncoder, and ColBERT. It has demonstrated scale to **41 million Wikipedia documents**. For your 11K files, this is trivially fast. Zero new infrastructure—it's already deployed.

**Keep SQLite + FTS5** for structured metadata queries (file type, date, size, tags, GROUP BY, JOINs). SQLite's full SQL power is irreplaceable for ad-hoc analytical queries. Use **DuckDB** (`pip install duckdb`, MIT license) as a complement for analytical workloads—it runs **3-25× faster** than SQLite on aggregations and scan-heavy queries, with native Parquet support. But do not use DuckDB for FTS (its full-text extension remains experimental as of 2025).

**Do not replace SQLite with Qdrant for metadata storage.** Qdrant excels at vector search + payload filtering but lacks JOINs, GROUP BY, aggregations, and full SQL capabilities. Its `scroll` API for payload-only queries doesn't use the HNSW index and isn't optimized for general-purpose metadata queries. Continue using Qdrant for deep semantic similarity across the 1.4M vector corpus, especially its native **sparse + dense hybrid search** for combining BM25 sparse vectors with dense embeddings.

**Skip Meilisearch and Typesense**—adding a separate search server is unnecessary complexity for 11K files when LanceDB already provides hybrid search. Skip **Turbopuffer** (cloud-only, not suitable for local deployment). Skip **Vespa** (massive overkill for this scale).

The optimal search architecture is a three-tier flow:

- **SQLite FTS5**: Structured metadata queries, faceted filtering, statistics
- **LanceDB Hybrid**: Semantic + keyword search with RRF reranking (primary search path)
- **Qdrant**: Deep semantic similarity across the full 1.4M vector corpus

---

## Layer 3: Neo4j should own all lineage, LightRAG should use it as backend

The simple SQL lineage table tracking source→derived relationships is an impedance mismatch—lineage is inherently a graph problem. Neo4j is already deployed and purpose-built for this.

**Migrate all data lineage to Neo4j immediately.** Model file dependencies as:

```cypher
(:File {path, type, hash, modified})-[:DERIVED_FROM {transform, timestamp}]->(:File)
(:File)-[:DEPENDS_ON]->(:File)  
(:Process {name, script})-[:READS]->(:File)
(:Process)-[:WRITES]->(:File)
```

Neo4j's Graph Data Science (GDS) library unlocks powerful lineage analytics: **PageRank** identifies the most critical files, **community detection** finds clusters of related files, **shortest path** traces lineage chains, and **betweenness centrality** reveals bottleneck files. For 11K nodes, all queries complete in milliseconds.

**Configure LightRAG to use Neo4j as its backend.** LightRAG (~20K+ stars, EMNLP 2025 paper) natively supports `Neo4JStorage` for its knowledge graph and can also use Qdrant for its vector storage layer. This unifies your semantic knowledge graph and file lineage graph in a single Neo4j instance:

```python
rag = LightRAG(
    graph_storage="Neo4JStorage",
    vector_storage="QdrantStorage",  # Use existing Qdrant
)
```

**CodeGraphContext** (github.com/CodeGraphContext/CodeGraphContext) is a compelling new tool that indexes code directly into Neo4j knowledge graphs—building call chains, class hierarchies, and dependency relationships across **12 programming languages** with live file watching for real-time updates. It also provides an MCP server for AI assistant queries. This could run alongside LightRAG, using the same Neo4j instance.

**Skip Microsoft GraphRAG** for this use case. At ~30.8K stars, it's impressive for document Q&A but consumes 5-10× more LLM tokens than LightRAG for comparable results. **Skip Memgraph** (Neo4j is more than adequate for 11K files; Memgraph's performance advantages only emerge at streaming scale with millions of nodes). **Skip Apache Atlas** (requires Kafka + Solr + HBase; Hadoop-focused). **Skip OpenLineage/Marquez** (designed for ETL pipeline lineage, not file dependency tracking). **Skip Amundsen** (dormant since Stemma's 2023 acquisition by Teradata).

---

## Layer 4: A tiered classification pipeline beats pure LLM or pure rules

Rule-based classification covers obvious cases but misses semantic nuance. Pure LLM classification is too expensive for 11K files. The optimal approach is a **three-tier hybrid pipeline**:

**Tier 1 — Rule-based (free, instant):** Keep existing pattern matching for obvious cases—file extensions, directory structure, naming conventions. This handles ~60-70% of files with zero cost.

**Tier 2 — Local zero-shot model:** Run **DeBERTa-v3-large-mnli** (MoritzLaurer variant, 0.4B params, 3.43M downloads) on ambiguous files using filename + first 500 characters of content. Processes ~50-100 texts/second on CPU. Covers another ~20% of files with no API costs.

**Tier 3 — LLM via Instructor:** Use the **Instructor library** (~11K stars, 3M+ monthly downloads) with Claude Haiku for the remaining ~10% of truly ambiguous files. Instructor structures LLM outputs via Pydantic models with automatic validation and retries:

```python
import instructor
client = instructor.from_provider("anthropic/claude-3-5-haiku")
classification = client.chat.completions.create(
    response_model=FileClassification,  # Pydantic model
    messages=[{"role": "user", "content": file_context}]
)
```

With prompt caching, classifying all 11K files costs **under $2** with Claude Haiku.

**BERTopic** is the breakthrough tool for **automatic category discovery**. Feed your existing Qdrant embeddings (1.4M vectors) through UMAP dimensionality reduction → HDBSCAN clustering → c-TF-IDF topic extraction. BERTopic auto-discovers natural groupings without predefined labels, and can use an LLM to generate human-readable cluster names. This replaces manual category definition with data-driven taxonomy.

---

## Layer 5: Keep SQLite for metadata, skip the heavy platforms

Full-scale metadata platforms like DataHub (requires MySQL + Kafka + Elasticsearch), OpenMetadata (requires PostgreSQL + Elasticsearch + Airflow), and Apache Atlas (requires Kafka + Solr + HBase) are enterprise-grade overkill for a file indexer.

**The optimal metadata architecture is SQLite + Neo4j hybrid:**

- **SQLite**: File properties (path, size, hash, modified date, type, processing status, classification results, tags). Fast reads, zero dependencies, battle-tested.
- **Neo4j**: File relationships (dependencies, lineage, derived-from, imports). Graph algorithms for impact analysis.
- **LightRAG → Neo4j**: Semantic entities and relationships extracted from document content.

**DataHub Lite** (`pip install 'acryl-datahub[datahub-lite]'`) is worth noting as a lightweight alternative using DuckDB as its backend with zero external dependencies. However, it's experimental and lacks full-text search and graph traversal—not yet production-ready.

**Nessie** is for Apache Iceberg table versioning, not file metadata. **Skip it.**

---

## Layer 6: Datasette and Cytoscape.js fill the visualization gap

**Datasette** (by Simon Willison, v1.0 alpha series) is the highest-impact, lowest-effort addition. Point it at your existing SQLite database and get an instant web UI + JSON/CSV API with **154+ plugins**:

```bash
pip install datasette
datasette serve project_index.sqlite
```

Built-in FTS integration, charting via `datasette-vega`, GraphQL via `datasette-graphql`, and CORS support for your React frontend. Runs on a different port alongside FastAPI.

**Cytoscape.js** with `react-cytoscapejs` is the best graph visualization library for the React dashboard. It handles 11K nodes comfortably, has mature graph layout algorithms, and integrates with Neo4j data via API calls. For 3D force-directed views, **react-force-graph** (WebGL-accelerated) handles 100K+ nodes.

**Evidence.dev** (~5K stars) is worth considering for polished BI-as-code reports—write Markdown + SQL, generate static dashboards that connect to SQLite/DuckDB. Good for periodic "Project Health" reports.

**Skip Gradio** (the React dashboard covers UI needs). **Streamlit** is useful for rapid prototyping but redundant with an existing React dashboard.

---

## Layer 7: Integration blueprint for the existing stack

Every integration question has a clear answer based on the research:

**Can Qdrant serve as the primary index store?** No. Keep SQLite for metadata, use Qdrant for vector search. Qdrant lacks SQL-level query power for structured operations.

**Can Neo4j handle data lineage natively?** Yes, and it should. Migrate the SQL lineage table to Neo4j immediately. Use GDS algorithms for impact analysis.

**Can LightRAG leverage Neo4j?** Yes, natively via `Neo4JStorage`. Configure it to use your existing Neo4j instance and Qdrant for vectors.

**Can FastAPI expose indexer queries?** Yes, add endpoints directly to the existing server on port 8100. Pattern: `GET /api/search?q=query&category=python` → SQLite FTS5, `GET /api/semantic-search?q=query` → LanceDB hybrid, `GET /api/lineage/{path}` → Neo4j Cypher.

**Can the React dashboard add an indexer page?** Yes. Use **TanStack Table** for sortable/filterable file listings, custom facet sidebar for category/type filtering, and **react-cytoscapejs** for dependency graph visualization. Connect via React Query to FastAPI endpoints.

**Can MCP expose indexer tools to Claude Code?** Yes. Build a custom MCP server using Python's `fastmcp` library exposing tools like `search_files()`, `get_file_info()`, `find_dependencies()`, `semantic_search()`. Reference **Code-Index-MCP** (github.com/ViperJuice/Code-Index-MCP) for architecture patterns—it uses FastAPI gateway + SQLite FTS5 + Voyage AI, nearly identical to your stack.

---

## Layer 8: Five cutting-edge tools that directly apply

The 2024-2025 landscape has produced several tools that map precisely to this project's needs:

**CodeGraphContext** (github.com/CodeGraphContext/CodeGraphContext) indexes code into Neo4j knowledge graphs with 12-language support, call chain analysis, and live file watching. It ships as both CLI and MCP server. This is the single most relevant new tool—it builds exactly the kind of code knowledge graph this project needs, using Neo4j as the native backend.

**Code-Graph-RAG** (github.com/vitali87/code-graph-rag) combines tree-sitter parsing, Neo4j/Memgraph knowledge graphs, and UniXcoder embeddings for semantic code search. It supports natural language Cypher generation via Gemini, Ollama, or OpenAI. MCP server included.

**Sourcebot** (github.com/sourcebot-dev/sourcebot, ~3K stars) wraps Zoekt's trigram search engine in a modern UI with AI-powered Q&A and MCP server support. Single Docker container deployment. Indexes the Linux kernel (55K files) in ~160 seconds.

**CKB/CodeMCP** (github.com/SimplyLiz/CodeMCP) provides **80+ MCP tools** for code intelligence using SCIP, LSP, and Git backends. Semantic symbol search, call graphs, impact analysis, and ownership detection across Go, TypeScript, Python, Rust, Java, and C++.

**Narsil-MCP** (github.com/postrv/narsil-mcp) is a Rust-based MCP server with 90+ tools, 32 languages, call graphs, neural semantic search, and SPARQL/RDF graph support. Notable for its performance characteristics.

The key technique shared by all cutting-edge tools: **tree-sitter AST parsing → embedding generation → knowledge graph storage → hybrid search retrieval → MCP server exposure**. This is the proven architecture.

---

## Recommended implementation roadmap

The changes below are ordered by impact-to-effort ratio. Each builds on the previous.

**Phase 1 — Drop-in upgrades (1-2 days):** Replace `ast` module with tree-sitter-language-pack for Python+TypeScript parsing. Add Docling for XLSX/document processing. Configure LightRAG to use Neo4j backend. Add Datasette on the existing SQLite database.

**Phase 2 — Search upgrade (2-3 days):** Create FTS index in LanceDB on file content. Implement hybrid search endpoint in FastAPI combining LanceDB (semantic+keyword) with SQLite FTS5 (structured filtering). Deploy Qdrant sparse vectors for BM25 keyword matching within the vector corpus.

**Phase 3 — Lineage migration (1-2 days):** Migrate SQL lineage table to Neo4j graph model. Implement Cypher queries for lineage tracing. Add `react-cytoscapejs` to the React dashboard for lineage visualization.

**Phase 4 — Classification pipeline (2-3 days):** Implement tiered classification (rules → DeBERTa → Instructor+Claude). Run BERTopic on Qdrant embeddings for automatic category discovery. Cache all results in SQLite.

**Phase 5 — MCP and intelligence (1-2 days):** Build custom MCP server wrapping FastAPI search endpoints. Deploy CodeGraphContext for Neo4j code knowledge graph. Integrate RepoMapper for PageRank-based file importance scoring.

## Conclusion

The most important finding is that **your existing stack already contains 80% of what's needed**—LanceDB's hybrid search, Neo4j's graph algorithms, and Qdrant's vector capabilities are individually world-class. The gap is not in the tools but in the connections between them. Tree-sitter unifies multi-language parsing. LanceDB's built-in Tantivy engine eliminates the need for a separate search server. Neo4j's native graph model is strictly superior to SQL for lineage tracking. The tiered classification approach (rules → local model → LLM) reduces API costs by 90% while improving accuracy. And the MCP server pattern—used by CodeGraphContext, Sourcebot, Code-Index-MCP, and others—provides the standard interface for exposing all of this to Claude Code. The architecture that emerges is not a replacement of what exists but a strategic wiring of components that are already deployed, augmented by tree-sitter, Docling, BERTopic, and Datasette as the key new additions.