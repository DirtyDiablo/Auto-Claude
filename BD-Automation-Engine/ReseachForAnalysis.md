# The definitive toolkit for AI-powered file organization in 2026

**A defense contracting BD team sitting on hundreds of scattered output files — Excel spreadsheets, CSVs, JSONs, markdown reports, Word docs, PDFs — needs a modern stack to crawl, deduplicate, cluster, tag, restructure, and make those files queryable by AI agents.** The good news: the open-source ecosystem has exploded with purpose-built tools since 2024. The recommended architecture combines **Docling** (51.8k ★) for universal document parsing, **LightRAG** (28.4k ★) or **Microsoft GraphRAG** (29.4k ★) for knowledge graph construction, a vector database like **LanceDB** or **ChromaDB** for embedding-based search, and **Claude Code with MCP servers** as the orchestration layer that ties everything together. Below is the full landscape, organized by capability, with GitHub URLs, star counts, and practical fit assessments for every tool worth considering.

---

## Parsing every file type into AI-ready structured data

The foundation of any file organization pipeline is converting diverse formats — XLSX, CSV, JSON, DOCX, PDF, markdown — into structured, machine-readable content. Three tools dominate this space in 2026.

**Docling** ([github.com/docling-project/docling](https://github.com/docling-project/docling), **51.8k ★**, MIT license) is the clear leader. Originally from IBM Research Zurich and now donated to the Linux Foundation, Docling parses PDF, DOCX, PPTX, XLSX, HTML, CSV, Markdown, images, and audio into a unified `DoclingDocument` format exportable as Markdown, HTML, or lossless JSON. Its advanced PDF understanding includes page layout analysis, reading order detection, table structure recognition (97.9% accuracy on benchmarks), and formula extraction. It integrates natively with LangChain, LlamaIndex, CrewAI, and Haystack, and runs entirely locally — critical for defense contracting environments. The ecosystem includes **docling-graph** for converting documents into validated knowledge graphs, **docling-serve** as a FastAPI wrapper, and **docling-mcp** for Model Context Protocol integration.

**MarkItDown** ([github.com/microsoft/markitdown](https://github.com/microsoft/markitdown), **~50k ★**) from Microsoft converts PDF, DOCX, PPTX, XLSX, images, audio, HTML, CSV, and JSON to clean Markdown. It's lighter than Docling — faster for simple conversions but less capable for complex layouts and tables. **Marker** ([github.com/datalab-to/marker](https://github.com/datalab-to/marker), **31.6k ★**) specializes in high-quality PDF-to-Markdown conversion with optional LLM enhancement, supporting 90+ languages. For the BD file collection use case, Docling is the primary tool, with MarkItDown as a fast alternative for simpler files.

Other notable parsers include **Kreuzberg** (Rust-powered core supporting 75+ formats with async Python API and MCP server support), **Unstructured.io** ([github.com/Unstructured-IO/unstructured](https://github.com/Unstructured-IO/unstructured), ~10k ★, Apache 2.0) with 30+ source/destination connectors, **MegaParse** ([github.com/QuivrHQ/MegaParse](https://github.com/QuivrHQ/MegaParse), ~3k ★) with swappable parser backends including multimodal LLMs, and Google's **LangExtract** ([github.com/google/langextract](https://github.com/google/langextract), **32.7k ★**) for LLM-powered structured information extraction with source grounding. For Excel/CSV specifically, **openpyxl** and **pandas** remain the workhorses, integrated into most LangChain and LlamaIndex loaders.

| Tool | Stars | Formats | Strength |
|------|-------|---------|----------|
| **Docling** | 51.8k | PDF, DOCX, XLSX, PPTX, HTML, CSV, MD, images, audio | Best overall: layout, tables, OCR, KG integration |
| **MarkItDown** | ~50k | PDF, DOCX, XLSX, PPTX, CSV, JSON, images, audio | Fastest simple conversion to Markdown |
| **Marker** | 31.6k | PDF → Markdown/JSON/HTML | Highest-quality PDF conversion |
| **LangExtract** | 32.7k | Unstructured text → structured data | LLM-powered field extraction |
| **Unstructured** | ~10k | 20+ formats, 30+ connectors | Production RAG pipelines |
| **Kreuzberg** | Growing | 75+ format families | Rust performance, polyglot bindings |
| **Apache Tika** | Mature | 1,000+ file types | Maximum format coverage (Java) |

---

## Intelligent deduplication and document clustering with ML

Finding near-duplicate files, grouping related documents, and identifying the most mature version of each output requires embedding-based similarity and probabilistic matching. The ecosystem offers tools at every complexity level.

**SemHash** ([github.com/MinishLab/semhash](https://github.com/MinishLab/semhash), MIT) is the most exciting new entrant — a fast multimodal semantic deduplication library using lightweight static embeddings (Model2Vec's `potion-base-8M`) and approximate nearest neighbor search. It supports self-deduplication and cross-dataset deduplication with adjustable similarity thresholds, multi-column matching (e.g., deduplicate on both filename and content), and image dedup via CLIP models. For the BD use case, SemHash can identify semantically similar reports even when filenames and structures differ completely.

**datasketch** ([github.com/ekzhu/datasketch](https://github.com/ekzhu/datasketch), ~2.5k ★, MIT) provides classical MinHash LSH for fast near-duplicate detection at scale. The pipeline — shingling → MinHash signatures → locality-sensitive hashing → candidate pair verification — handles millions of documents efficiently. **text-dedup** ([github.com/ChenghaoMou/text-dedup](https://github.com/ChenghaoMou/text-dedup), ~1.5k ★) bundles MinHash, SimHash, Bloom Filter, and Suffix Array algorithms with TOML configuration and Spark support. For structured record deduplication across CSVs and Excel files specifically, **dedupe** ([github.com/dedupeio/dedupe](https://github.com/dedupeio/dedupe), **~4.1k ★**) uses active learning to train fuzzy matching rules from human feedback.

For embedding-based clustering, **sentence-transformers** ([github.com/huggingface/sentence-transformers](https://github.com/huggingface/sentence-transformers), **~16k ★**) is foundational. The best models for document similarity in 2026 are `all-mpnet-base-v2` (768-dim, highest quality), `all-MiniLM-L6-v2` (384-dim, 5× faster), and NVIDIA's `NV-Embed-v2` for enterprise RAG. Combined with scikit-learn's K-Means, DBSCAN, or agglomerative clustering on TF-IDF or transformer embeddings, you can automatically group related output files. **FAISS** ([github.com/facebookresearch/faiss](https://github.com/facebookresearch/faiss), **~33k ★**) provides GPU-accelerated similarity search handling billions of vectors. Zero-shot document classification via Hugging Face's `facebook/bart-large-mnli` or `MoritzLaurer/deberta-v3-large-zeroshot-v2.0` enables automatic categorization into arbitrary labels (e.g., "proposal," "capability statement," "pricing analysis," "past performance") without training data.

---

## AI-powered file organization and auto-tagging tools

A new class of LLM-powered file organizers has emerged specifically for the "messy output directory" problem. These tools analyze file contents and automatically rename, categorize, and restructure files.

**LlamaFS** ([github.com/iyaja/llama-fs](https://github.com/iyaja/llama-fs), **~10k ★**) is the most popular dedicated tool. Built at a Llama 3 hackathon, it operates in batch mode (scan directory, return organized structure) and watch/daemon mode (continuously monitors and auto-organizes new files). Using Groq for inference, it achieves <500ms per file operation. **Local-File-Organizer** ([github.com/QiuYannnn/Local-File-Organizer](https://github.com/QiuYannnn/Local-File-Organizer), ~2k ★) runs 100% locally with Llama 3.2 and LLaVA, generating descriptions, folder names, and filenames with no data leaving the device — essential for defense contracting. It handles PDFs, DOCX, XLSX, PPTX, TXT, and images.

**Paperless-ngx** ([github.com/paperless-ngx/paperless-ngx](https://github.com/paperless-ngx/paperless-ngx), **36.6k ★**) is the most mature document management system, providing OCR, full-text search, auto-tagging, custom fields, and a REST API. Two AI companion projects supercharge it: **paperless-ai** ([github.com/clusterzx/paperless-ai](https://github.com/clusterzx/paperless-ai), **5.2k ★**) uses OpenAI/Ollama/DeepSeek to automatically assign titles, tags, document types, and correspondents, while **paperless-gpt** ([github.com/icereed/paperless-gpt](https://github.com/icereed/paperless-gpt), 1.9k ★) adds LLM Vision and multiple OCR providers. For the BD workflow, Paperless-ngx + paperless-ai creates a complete document management pipeline with AI-powered metadata generation.

Other notable tools: **AIFiles** ([github.com/jjuliano/aifiles](https://github.com/jjuliano/aifiles)) offers a CLI with watch daemon, XDG folder templates, customizable naming structures with field extraction (e.g., `{file_category}/{file_title}--{file_date}`), and support for ChatGPT, Grok, DeepSeek, or local LLMs. **Offline-AI-File-Organizer** ([github.com/yousefebrahimi0/Offline-AI-File-Organizer](https://github.com/yousefebrahimi0/Offline-AI-File-Organizer)) specifically handles PDF, DOCX, XLSX, CSV, and TXT with predefined categories (Work, Finance, Legal, Projects) and 100% offline operation via LM Studio. **AI File Organizer (Foadsf)** ([github.com/Foadsf/ai-file-organizer](https://github.com/Foadsf/ai-file-organizer)) stands out for **ontology-enforced Key-Value metadata tagging** — it embeds XMP/IPTC tags via exiftool and supports TMSU filesystem-level tags, making metadata universally accessible across tools.

---

## Claude Code skills and MCP servers as the orchestration layer

Claude Code's extensibility through Skills and MCP servers makes it the natural orchestration hub for this entire pipeline. The ecosystem has matured rapidly.

**Claude Code Skills** are folders with `SKILL.md` files that Claude loads dynamically. The official **anthropics/skills** repository (**69.3k ★**) includes source-available document skills for **docx** (create, edit, analyze Word documents with tracked changes), **pdf** (extract text/tables, merge/split, handle forms), **xlsx** (Excel reading, analysis, manipulation), and **pptx** (PowerPoint processing). Community skills include a **CSV Data Summarizer** for auto-analysis with visualizations, **kreuzberg** for text extraction from 62+ formats, and **metadata-extraction** from Trail of Bits for forensic-grade file metadata analysis. Skills can be installed per-project (`.claude/skills/`) or globally (`~/.claude/skills/`).

The **MCP server ecosystem** is where the real power lies for file system intelligence. Over **8,230 MCP servers** exist as of early 2026. The most critical for this use case:

- **@modelcontextprotocol/server-filesystem** (official, Anthropic-maintained) — Core read/write/search/move operations with security sandboxing
- **awslabs/document-loader-mcp-server** — Parses PDF, DOCX, XLSX, PPTX, and images via pdfplumber and markitdown (AWS Labs maintained)
- **bsmi021/mcp-filesystem-server** — Built-in **FindDuplicates** tool, text analysis (line/word/char counts), file hash calculation (MD5/SHA256), and ZIP archive handling
- **kridaydave/File-Organizer-MCP** — Intelligent file organization with metadata extraction (EXIF, ID3), categorization, and organization plan previews
- **qdrant/mcp-server-qdrant** (official Qdrant) — Semantic memory layer using FastEmbed sentence-transformers for meaning-based file retrieval
- **olafgeibig/knowledge-mcp** — LightRAG-powered knowledge base processing PDF, Text, Markdown, and DOCX with graph + vector hybrid retrieval
- **knowledge-graph-rag-mcp** (PyPI) — Auto-ingesting directory watcher that builds a hybrid GraphRAG index from documents, fully local with SQLite + sqlite-vec
- **ttommyth/rag-memory-mcp** — Combines knowledge graph (entities, relationships) with vector search and SQLite backend
- **Dicklesworthstone/ultimate_mcp_server** — Swiss army knife covering document processing, file operations, vector storage, knowledge graph querying, and semantic search in a single server

The recommended MCP stack: official filesystem server + awslabs/document-loader + knowledge-graph-rag-mcp (or olafgeibig/knowledge-mcp) + qdrant/mcp-server-qdrant + SQLite MCP for metadata persistence.

---

## AI coding agents that can analyze and restructure file collections

While dedicated file organizers handle common patterns, AI coding agents offer the flexibility to write custom organization scripts tailored to specific BD file naming conventions and content patterns.

**Claude Code** is the strongest option for this specific use case. It can spawn sub-agents for parallel file analysis, execute bash commands to walk directories and process files, read and understand file contents natively through its tools (Read, Grep, Glob, Bash), and connect to any MCP server for extended capabilities. Background agents enable async task delegation. Combined with CLAUDE.md project configuration, you can define your BD folder taxonomy and have Claude Code reorganize files accordingly.

**Cline** ([github.com/cline/cline](https://github.com/cline/cline), **~48k ★**, 5M+ installations) offers transparent human-in-the-loop file operations — it shows diffs before applying changes and supports workspace snapshots for safe rollback. Its Plan/Act modes generate multi-step reorganization plans that you approve step-by-step. **OpenHands** ([github.com/OpenHands/OpenHands](https://github.com/OpenHands/OpenHands), **~65k ★**) provides a Software Agent SDK for building custom file-organization agents that can scale to thousands of parallel instances in sandboxed Docker environments. **Aider** ([github.com/Aider-AI/aider](https://github.com/Aider-AI/aider), ~27-30k ★) excels at terminal-based multi-file editing with automatic git commits. **Devin** (devin.ai) has demonstrated expertise in large-scale file migrations, completing bank ETL file migrations 10× faster than humans via reusable playbooks — directly applicable to BD output file reorganization. **OpenAI Codex CLI** is now open-source with Skills, MCP integration, and GitHub Actions support for CI/CD-based file organization automation.

No single agent perfectly handles "organize generated output files across all formats" out of the box. **The most practical approach is using Claude Code or Cline to write and execute custom Python scripts** that combine Docling for parsing, sentence-transformers for embeddings, and a vector DB for similarity search — a bespoke pipeline tailored to your specific BD file patterns.

---

## Vector databases and RAG solutions for making files queryable

Creating a queryable metadata layer over a file collection requires a vector database for embedding-based search and a RAG pipeline for natural language Q&A.

For **embedded local-first deployment**, **LanceDB** ([github.com/lancedb/lancedb](https://github.com/lancedb/lancedb), **~12k ★**) is the top choice — truly serverless with zero infrastructure (`pip install lancedb`, data stored in .lance files on disk), claims 100× faster than Parquet, and is used by Midjourney. **ChromaDB** ([github.com/chroma-core/chroma](https://github.com/chroma-core/chroma), ~16k ★) is the simplest API for prototyping — `pip install chromadb` gets you an in-memory or persistent local database. **txtai** ([github.com/neuml/txtai](https://github.com/neuml/txtai), ~10k ★) is the best all-in-one solution, combining embeddings database, NLP pipelines (summarization, translation, transcription), workflow engine, and agents framework in a single package. For production scale with complex metadata filtering, **Qdrant** ([github.com/qdrant/qdrant](https://github.com/qdrant/qdrant), ~22k ★, Rust) and **Milvus** ([github.com/milvus-io/milvus](https://github.com/milvus-io/milvus), ~35k ★) offer distributed deployments handling billions of vectors.

Complete RAG solutions that work out of the box for local document Q&A:

- **AnythingLLM** ([github.com/Mintplex-Labs/anything-llm](https://github.com/Mintplex-Labs/anything-llm), **~35k ★**) — Desktop app + Docker with built-in RAG, AI agents, MCP compatibility, and LanceDB as default vector store. Most accessible option for non-technical users
- **RAGFlow** ([github.com/infiniflow/ragflow](https://github.com/infiniflow/ragflow), **~65k ★**) — Enterprise-grade with deep document understanding, template-based chunking, grounded citations, and multi-modal PDF/DOCX image parsing
- **PrivateGPT** ([github.com/zylon-ai/private-gpt](https://github.com/zylon-ai/private-gpt), **~54k ★**) — 100% offline document Q&A built on LlamaIndex
- **Khoj** ([github.com/khoj-ai/khoj](https://github.com/khoj-ai/khoj), **31.5k ★**) — Personal AI "second brain" with document search, custom agents, scheduled automations, and deep research mode
- **Onyx** (formerly Danswer, [github.com/onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx), ~15k ★) — Enterprise team AI assistant with 13+ SaaS connectors and airgapped deployment support

---

## Knowledge graph builders for understanding document relationships

Knowledge graphs go beyond vector search by capturing **relationships between documents** — which files reference the same contracts, which analyses build on which data, which versions supersede others. This is where the BD file collection use case gets genuinely powerful.

**Microsoft GraphRAG** ([github.com/microsoft/graphrag](https://github.com/microsoft/graphrag), **29.4k ★**) is the gold standard. It extracts entities and relationships from documents using LLMs, builds a knowledge graph, creates hierarchical community summaries via Leiden clustering, and supports both local (entity-focused) and global (thematic) queries. It outperforms naive RAG for questions spanning multiple documents — exactly what you need for querying across hundreds of BD outputs. The trade-off: **indexing is expensive** due to heavy LLM usage.

**LightRAG** ([github.com/HKUDS/LightRAG](https://github.com/HKUDS/LightRAG), **28.4k ★**, EMNLP 2025) achieves comparable accuracy with **10× fewer tokens** and **65-80% cost savings** for 1,500+ documents. It supports multiple storage backends (NetworkX, Neo4j, PostgreSQL+AGE) and vector backends (FAISS, Milvus, Chroma, Qdrant). For the BD use case processing hundreds of files monthly, LightRAG is the pragmatic production choice.

**Graphiti** ([github.com/getzep/Graphiti](https://github.com/getzep/Graphiti), trending on Trendshift) builds real-time, temporally-aware knowledge graphs with continuous incremental updates — critical for BD workflows where new analyses are generated regularly. It supports Neo4j, FalkorDB, and Kuzu backends, and already has an MCP server for Claude/Cursor integration. **Neo4j LLM Knowledge Graph Builder** ([github.com/neo4j-labs/llm-graph-builder](https://github.com/neo4j-labs/llm-graph-builder), ~5k ★) offers the most complete document-to-KG pipeline with a web UI, supporting PDF, DOCX, TXT, images, and YouTube transcripts with multiple RAG modes (Vector, GraphRAG, Text2Cypher). **Docling Graph** ([github.com/docling-project/docling-graph](https://github.com/docling-project/docling-graph)) transforms Docling-parsed documents into validated knowledge graphs exportable to CSV and Cypher — completing the Docling ecosystem for the entire pipeline from parsing to knowledge graph.

---

## Code search and repo analysis tools for scanning GitHub repositories

Since the BD output files are spread across multiple GitHub repos, code search tools help navigate and understand the file landscape before reorganization.

**Repomix** ([github.com/yamadashy/repomix](https://github.com/yamadashy/repomix), **20.8k ★**) packs entire repos into single AI-friendly files with token counting, ~70% code compression, and split output for large codebases. It's the fastest way to prepare a repo's file collection for LLM analysis — run `npx repomix` and feed the output to Claude. **Sourcebot** ([github.com/sourcebot-dev/sourcebot](https://github.com/sourcebot-dev/sourcebot), **3.1k ★**) provides self-hosted code search with natural language "Ask Sourcebot" queries, built on Google's Zoekt engine. Free community edition, single Docker Compose deployment, BYO LLM key. **Sourcegraph** remains the enterprise standard (used by 15+ US government agencies and Leidos) with Deep Search AI reasoning, but **Cody free/pro plans were discontinued** in July 2025 — enterprise-only at $59/user/month. **Greptile** (greptile.com, YC W24, $25M Series A) offers AI-powered code review with 82% bug catch rate, but is code-review-focused rather than file-management-focused.

---

## What's trending on Trendshift right now

Several tools trending on [Trendshift.io](https://trendshift.io) in February 2026 are directly relevant:

**qmd** ([github.com/tobi/qmd](https://github.com/tobi/qmd), **8.9k ★**, position #22 on daily explore) is a mini CLI search engine for docs, knowledge bases, and meeting notes — all local, tracking current SOTA approaches. **PageIndex** ([github.com/VectifyAI/PageIndex](https://github.com/VectifyAI/PageIndex), **7.7k ★**, position #2 on 7-day trending) offers vectorless, reasoning-based RAG for document indexing without embedding overhead. **OpenViking** ([github.com/volcengine/OpenViking](https://github.com/volcengine/OpenViking), 2k ★, position #4 on daily explore) is an open-source context database using a "file system paradigm" for AI agent context management — directly relevant to hierarchical file collection organization. **UltraRAG** ([github.com/OpenBMB/UltraRAG](https://github.com/OpenBMB/UltraRAG), 2.7k ★, position #5 on 7-day trending) provides a low-code MCP framework for building complex RAG pipelines. **Dify** ([github.com/langgenius/dify](https://github.com/langgenius/dify), **129.5k ★**) remains one of the most-trended repos ever (63 times on GitHub Trending) as a full AI workflow platform capable of orchestrating document processing pipelines.

---

## Recommended architecture for the BD file collection

For a defense contracting team needing to organize, deduplicate, tag, and query a large collection of generated output files, the recommended stack integrates five layers:

**Layer 1 — Parse:** Docling (all formats → structured JSON/Markdown) + pandas/openpyxl (Excel/CSV specifics)

**Layer 2 — Embed & Deduplicate:** sentence-transformers (`all-mpnet-base-v2`) for document embeddings → SemHash for semantic deduplication → datasketch MinHash LSH for near-duplicate detection at scale

**Layer 3 — Index & Search:** LanceDB (embedded, serverless) or ChromaDB (simple prototyping) for vector storage, with Qdrant for production deployments needing complex metadata filtering

**Layer 4 — Knowledge Graph:** LightRAG (cost-effective, production-ready) or Microsoft GraphRAG (maximum quality) for relationship extraction and thematic querying across the full document collection

**Layer 5 — Orchestrate:** Claude Code with MCP servers (filesystem + awslabs/document-loader + knowledge-graph-rag-mcp + qdrant/mcp-server-qdrant) as the interactive interface. Paperless-ngx + paperless-ai for ongoing document management with AI auto-tagging. AnythingLLM as a ready-made desktop RAG interface for non-technical team members.

**For immediate, low-effort wins:** Install Repomix (`npx repomix`) to pack each repo for LLM analysis, deploy AnythingLLM desktop app with Ollama for instant local document Q&A, and use Claude Code with the official filesystem MCP server to begin analyzing and restructuring files interactively. Then progressively add Docling for deep parsing, LightRAG for knowledge graphs, and paperless-ai for automated tagging as the pipeline matures.

## Conclusion

The 2024-2026 explosion of AI tooling has created **a complete, open-source stack for every layer of the file intelligence problem** — from parsing (Docling, 51.8k ★) through deduplication (SemHash, sentence-transformers) to knowledge graphs (LightRAG, 28.4k ★) and interactive querying (Claude Code + MCP). The key insight is that **no single tool solves the full pipeline**, but the MCP protocol has emerged as the integration standard that lets Claude Code orchestrate specialized tools together. The most significant gap remains purpose-built tools for "organize generated analysis outputs" specifically — most file organizers target personal files (photos, downloads) rather than BD pipeline artifacts. The practical solution is using an AI coding agent (Claude Code or Cline) to write custom organization scripts that leverage this toolkit stack, guided by project-specific CLAUDE.md rules encoding your BD taxonomy and naming conventions. The knowledge graph layer (LightRAG or GraphRAG) is where the highest ROI lies — it transforms a flat file collection into a queryable web of relationships between contracts, analyses, proposals, and capabilities that AI agents can traverse intelligently.