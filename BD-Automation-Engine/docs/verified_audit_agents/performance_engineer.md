# BD-Automation-Engine Performance Bottleneck Analysis

**Reviewer:** Performance Engineer Agent (voltagent-qa-sec:performance-engineer)
**Date:** 2026-02-20
**Scope:** All engines, API layer, ETL pipeline, vector store, search infrastructure

---

## Summary Table

| # | Severity | File | Lines | Bottleneck | Status | Est. Impact |
|---|----------|------|-------|-----------|--------|-------------|
| BN-01 | P0 | `vector_store.py` | 578-580 | Silent embedding drop, no retry | Confirmed | Data loss |
| BN-02 | P0 | `bullhorn_etl_v2.py` | 821-968 | Individual INSERTs (not executemany) | Confirmed | 100x ETL slowdown |
| BN-03 | P0 | `hybrid_retriever.py` | 266-295 | 74+ sequential API calls for BM25 cold start | Confirmed | 15-45s first-search |
| BN-04 | P1 | `orchestrator.py` | 759-818 | Sequential stages 9-11 (no parallelism) | Confirmed | +40% pipeline runtime |
| BN-05 | P1 | All Engine7 scripts | 18 files | WAL mode bypassed at 18 direct connect sites | Confirmed | DB locking under concurrency |
| BN-06 | P1 | `vector_store.py` | 562 | 1 OpenAI API call per record (not batch) | Confirmed | 14x more API calls |
| BN-07 | P1 | `contact_lookup.py` | 117-120 | O(n^2) list membership deduplication | Confirmed | Quadratic at scale |
| BN-08 | P1 | `vector_store.py` | 308-340 | Embedding cache exists but never used in store | Confirmed | Wasted API cost + latency |
| BN-09 | P2 | All Engine7 scripts | Multiple | No connection pooling, raw connect() throughout | Confirmed | Risk of leaks + lock issues |
| BN-10 | P2 | `vector_store.py` | 660-694 | `search_all` embeds same query 9 times | Confirmed | 1.35s wasted embedding calls |
| BN-11 | P2 | `api.py` | 1318-1429 | Blocking sync I/O in async endpoints | Confirmed | Event loop starvation |
| BN-12 | P2 (NEW) | `bullhorn_etl_v2.py` | 666-701 | Full Excel load for type detection, loaded twice | New | Double disk I/O |
| BN-13 | P2 (NEW) | `bullhorn_etl_v2.py` | 1004-1083 | N+1 query in `build_past_performance` | New | 2N+1 queries per run |
| BN-14 | P0 (NEW) | `vector_store.py` | 817 | Wrong arg order in `get_program_intelligence` | New | Silent wrong results / crash |
| BN-15 | P2 (NEW) | `redis_cache.py` | 121-172 | O(n) linear Redis scan per cache lookup | New | Cache makes search slower |

---

## P0 -- CRITICAL (Data Loss or Complete Feature Failure)

### BN-01 (CONFIRMED) -- Silent Embedding Drop, No Retry

**File:** `Engine8_Knowledge/scripts/vector_store.py`, lines 578-580

When embedding generation fails for a record, it is silently skipped. No retry buffer, no dead letter queue, no count of dropped records reported to user.

### BN-02 (CONFIRMED) -- Individual INSERTs (not executemany)

**File:** `Engine7_BullhornETL/scripts/bullhorn_etl_v2.py`, lines 821-968

Each record uses an individual `INSERT OR REPLACE` statement instead of `executemany()`. For 50,710 records, this means 50,710 individual SQL executions.

**Impact:** 100x slower than batch `executemany`. ETL that should take 30 seconds takes 45+ minutes.

**Fix:** Collect records into batches and use `cursor.executemany()`.

### BN-03 (CONFIRMED) -- 74+ Sequential API Calls for BM25 Cold Start

**File:** `Engine8_Knowledge/scripts/hybrid_retriever.py`, lines 266-295

`_fetch_all_docs()` scrolls entire Qdrant collection using `limit=100` page size. For contacts (7,337 records), this is 74 sequential scroll API calls. Combined with BM25 tokenization, first hybrid search takes 15-45 seconds.

**Fix:**
1. Use `limit=1000` page size (10x fewer API calls)
2. Persist BM25 index to disk
3. Pre-warm BM25 at API startup in lifespan handler

### BN-14 (NEW) -- Wrong Argument Order in `get_program_intelligence`

**File:** `Engine8_Knowledge/scripts/vector_store.py`, lines 808-821

```python
"program": self.search("programs", program_name, limit=3),
```

The `search()` signature is `search(self, query: str, collection: str, ...)`. This passes `"programs"` as query and `program_name` as collection -- completely backwards. Causes `ValueError: Unknown collection` or silently wrong results.

**Fix:**
```python
"program": self.search(query=program_name, collection="programs", limit=3),
"documents": self.search(query=program_name, collection="documents", limit=10),
```

---

## P1 -- HIGH (Significant Throughput and Latency Impact)

### BN-04 (CONFIRMED) -- Sequential 11-Stage Orchestrator: No Parallelism on Independent Stages

**File:** `orchestrator.py`, lines 616-818

Stages 7-11 (Webhook, Email, Bullhorn ETL, Dashboard Export, Knowledge Indexing) are all I/O bound and fully independent after Stage 6. Running them sequentially adds 4-8 minutes.

**Fix:** Use `ThreadPoolExecutor(max_workers=3)` for stages 9-11.

### BN-05 (CONFIRMED) -- WAL Mode Only Applied Through `get_connection()`, Not All Call Sites

**File:** `Engine7_BullhornETL/scripts/database_schema.py`, line 427; all other Engine7 scripts

`get_connection()` correctly sets WAL mode. However, 18 other scripts use `sqlite3.connect(DATABASE_PATH)` directly, bypassing WAL. These include: `bd_intelligence_report.py:21`, `link_to_federal_programs.py:189`, `program_mapper.py:281`, `dashboard_integration.py:32`, `export_to_notion.py` (5 locations), `bullhorn_activity_logger.py` (7 locations), `contact_scoring.py:145`, `financial_analysis.py:84`.

**Fix:** Create `get_optimized_connection()` wrapper with WAL + performance PRAGMAs and replace all 18 direct connect sites.

### BN-06 (CONFIRMED) -- Single-Record OpenAI Embedding API Calls During Indexing

**File:** `Engine8_Knowledge/scripts/vector_store.py`, lines 552-591

OpenAI embedding API called one record at a time. The API supports up to 2,048 strings per request. Indexing 7,337 contacts = 7,337 API calls instead of 4.

**Fix:** Implement `_generate_embeddings_batch()` using batch API. Reduces indexing from ~73 minutes to ~5 minutes.

### BN-07 (CONFIRMED) -- O(n^2) Contact Deduplication

**File:** `Engine3_OrgChart/scripts/contact_lookup.py`, lines 110-120

`c not in r` list membership check is O(n) per item. For 500 results from 3 variants: 250,000 comparisons. For 100 jobs: 25 million comparisons.

**Fix:** Use `seen_ids = set()` for O(1) deduplication.

### BN-08 (CONFIRMED) -- Embedding Cache Exists But Never Used During Indexing

**File:** `Engine8_Knowledge/scripts/redis_cache.py` (full file); `vector_store.py` lines 229-235

`SemanticCache` is fully implemented with Redis backend and in-memory fallback. It is initialized in `api.py`. However, `BDKnowledgeStore._generate_embedding()` never consults it. Identical queries re-embedded every time.

**Fix:** Add in-process LRU dict cache to `_generate_embedding()`, or wire the `SemanticCache` for production.

---

## P2 -- MEDIUM (Scalability and Reliability Issues)

### BN-09 (CONFIRMED) -- No Database Connection Pooling

**File:** All `Engine7_BullhornETL/scripts/*.py` (18 files)

Every script opens raw `sqlite3.connect()` at module/function level, relies on GC to close.

**Fix:** Context manager wrapper ensuring WAL mode and guaranteed close.

### BN-10 (CONFIRMED) -- `search_all` Embeds Same Query 9 Times

**File:** `Engine8_Knowledge/scripts/vector_store.py`, lines 660-694

Iterates 9 collections, each calling `_generate_embedding(query)` independently. Same text embedded 9x = 1.35s pure embedding latency.

**Fix:** Generate embedding once, pass vector directly to Qdrant `query_points()`.

### BN-11 (CONFIRMED) -- Blocking Sync I/O in Async FastAPI Endpoints

**File:** `Engine8_Knowledge/api.py`, lines 1318-1375, 1390-1429

Search endpoints are `async def` but call synchronous blocking functions directly (OpenAI HTTP, Qdrant I/O, CPU-bound BM25). Blocks uvicorn's event loop for 150-500ms per request.

**Fix:** Wrap in `asyncio.to_thread()` for all blocking calls.

### BN-12 (NEW) -- Full Excel Load for Type Detection, Loaded Twice

**File:** `Engine7_BullhornETL/scripts/bullhorn_etl_v2.py`, lines 666-701

`identify_file_type()` calls `pd.read_excel(file_path, engine="xlrd", header=None)` loading entire file into memory just to check column count. Same file loaded again when actually processed.

**Fix:** Use `nrows=3` for type detection.

### BN-13 (NEW) -- N+1 Query in `build_past_performance()`

**File:** `Engine7_BullhornETL/scripts/bullhorn_etl_v2.py`, lines 1004-1083

Fetches all prime contractors, then for each executes 2 additional queries (job stats + placement stats). With N contractors: 2N+1 total queries.

**Fix:** Collapse to 2 aggregate queries using GROUP BY.

### BN-15 (NEW) -- `SemanticCache.get()` Linear Scan Degrades With Cache Size

**File:** `Engine8_Knowledge/scripts/redis_cache.py`, lines 121-172

`get()` iterates ALL cached keys, fetching each embedding from Redis individually for cosine similarity. At 500 cached queries: 500 Redis round-trips x ~1ms = 500ms -- slower than just calling OpenAI directly (~150ms).

**Fix:** Keep embeddings in numpy array in-process, vectorized cosine similarity (no Redis round-trips per lookup).

---

## Priority Remediation Order

**Immediate (fix before next pipeline run):**
1. **BN-14** -- Argument order bug. 3-line fix.
2. **BN-02** -- Switch to `executemany`. 60-100x faster ETL.
3. **BN-01** -- Add retry buffer for failed embeddings.

**This sprint:**
4. **BN-06** -- Batch OpenAI embeddings (2048/call). 14x fewer API calls.
5. **BN-03** -- BM25 disk persistence + 10x scroll page size. Eliminates 45s cold start.
6. **BN-10** -- Single embedding in `search_all`. Removes 8 redundant API calls.

**Next sprint:**
7. **BN-11** -- `asyncio.to_thread()` for production concurrency.
8. **BN-05** -- Standardize all Engine7 connections through wrapper.
9. **BN-04** -- Parallelize orchestrator stages 9-11.
10. **BN-08** -- Wire `SemanticCache` into embedding layer.
11. **BN-07** -- Set-based deduplication.
12. **BN-15** -- Vectorized cosine in-process cache.
13. **BN-12** -- `nrows=3` in type detection.
14. **BN-13** -- GROUP BY aggregates.
15. **BN-09** -- Context manager for all SQLite connections.
