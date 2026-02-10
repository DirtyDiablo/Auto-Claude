"""
Phase 22A — Search API Router

REST endpoints for unified search, hybrid search, graph search,
benchmark v2, and search statistics.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search/v2", tags=["search-v2"])


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query text")
    mode: str = Field("auto", description="Search mode: auto|hybrid|graph|graphrag|vector|keyword")
    collections: list[str] | str = Field("all", description="Collections to search")
    top_k: int = Field(10, ge=1, le=100, description="Number of results")
    use_rerank: bool = Field(True, description="Apply cross-encoder reranking")
    filters: Optional[dict] = Field(None, description="Metadata filters")
    expand_query: bool = Field(True, description="Apply query expansion")


class MultiSearchRequest(BaseModel):
    queries: list[str] = Field(..., min_items=1, max_items=20)
    mode: str = Field("auto")
    collections: list[str] | str = Field("all")
    top_k: int = Field(10, ge=1, le=100)


class BenchmarkRequest(BaseModel):
    modes: list[str] = Field(["vector", "hybrid", "graphrag"])
    categories: Optional[list[str]] = Field(None)


# ---------------------------------------------------------------------------
# Search endpoints
# ---------------------------------------------------------------------------

@router.post("")
async def unified_search(req: SearchRequest):
    """Unified search with auto-mode routing."""
    from Engine8_Knowledge.search.unified_search import get_unified_search
    us = get_unified_search()
    resp = us.search(
        query=req.query,
        mode=req.mode,
        collections=req.collections,
        top_k=req.top_k,
        use_rerank=req.use_rerank,
        filters=req.filters,
        expand_query=req.expand_query,
    )
    return _format_response(resp)


@router.post("/hybrid")
async def hybrid_search(req: SearchRequest):
    """Force hybrid mode (dense + sparse)."""
    from Engine8_Knowledge.search.unified_search import get_unified_search
    us = get_unified_search()
    resp = us.search(
        query=req.query, mode="hybrid",
        collections=req.collections, top_k=req.top_k,
        use_rerank=req.use_rerank, filters=req.filters,
        expand_query=req.expand_query,
    )
    return _format_response(resp)


@router.post("/graph")
async def graph_search(req: SearchRequest):
    """Force graph mode (Neo4j-first)."""
    from Engine8_Knowledge.search.unified_search import get_unified_search
    us = get_unified_search()
    resp = us.search(
        query=req.query, mode="graph",
        collections=req.collections, top_k=req.top_k,
        filters=req.filters, expand_query=req.expand_query,
    )
    return _format_response(resp)


@router.post("/graphrag")
async def graphrag_search(req: SearchRequest):
    """Force triple-channel mode (dense + sparse + graph)."""
    from Engine8_Knowledge.search.unified_search import get_unified_search
    us = get_unified_search()
    resp = us.search(
        query=req.query, mode="graphrag",
        collections=req.collections, top_k=req.top_k,
        use_rerank=req.use_rerank, filters=req.filters,
        expand_query=req.expand_query,
    )
    return _format_response(resp)


@router.post("/multi")
async def multi_search(req: MultiSearchRequest):
    """Batch search multiple queries."""
    from Engine8_Knowledge.search.unified_search import get_unified_search
    us = get_unified_search()
    responses = us.multi_search(
        queries=req.queries, mode=req.mode,
        collections=req.collections, top_k=req.top_k,
    )
    return {
        "queries": len(req.queries),
        "results": [_format_response(r) for r in responses],
    }


# ---------------------------------------------------------------------------
# Info endpoints
# ---------------------------------------------------------------------------

@router.get("/modes")
async def search_modes():
    """Available search modes and descriptions."""
    from Engine8_Knowledge.search.unified_search import get_unified_search
    us = get_unified_search()
    return {"modes": us.get_modes()}


@router.get("/stats")
async def search_stats():
    """Search statistics."""
    from Engine8_Knowledge.search.benchmark_v2 import RESULTS_DIR
    report = None
    latest = RESULTS_DIR / "benchmark_v2_latest.json"
    if latest.exists():
        import json
        report = json.loads(latest.read_text())

    return {
        "timestamp": datetime.now().isoformat(),
        "latest_benchmark": report,
        "available_modes": ["auto", "hybrid", "graph", "graphrag", "vector", "keyword"],
        "collections": ["bd_contacts", "bd_documents", "bd_activities", "bd_programs", "bd_jobs"],
    }


# ---------------------------------------------------------------------------
# Benchmark endpoints
# ---------------------------------------------------------------------------

@router.post("/benchmark")
async def run_benchmark(req: BenchmarkRequest):
    """Run benchmark v2 (returns comparison table)."""
    from Engine8_Knowledge.search.benchmark_v2 import SearchBenchmarkV2
    bench = SearchBenchmarkV2()
    results = bench.run_benchmark(modes=req.modes, categories=req.categories)
    report = bench.export_report(results)
    comparison = bench.compare_modes(results)
    return {
        "comparison": comparison,
        "report": report,
    }


@router.get("/benchmark/latest")
async def latest_benchmark():
    """Get most recent benchmark results."""
    from Engine8_Knowledge.search.benchmark_v2 import SearchBenchmarkV2
    bench = SearchBenchmarkV2()
    report = bench.get_latest_report()
    if not report:
        return {"status": "no_benchmark_results", "hint": "POST /search/v2/benchmark to run"}
    return report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_response(resp) -> dict:
    """Format SearchResponse to JSON-serializable dict."""
    return {
        "results": [
            {
                "id": r.id,
                "content": r.content,
                "score": round(r.score, 4),
                "source": r.source,
                "channel_scores": {k: round(v, 4) for k, v in r.channel_scores.items()},
                "metadata": r.metadata,
            }
            for r in resp.results
        ],
        "mode_used": resp.mode_used,
        "search_latency_ms": resp.search_latency_ms,
        "total_candidates": resp.total_candidates,
        "channels_used": resp.channels_used,
        "query_expanded": getattr(resp, "query_expanded", ""),
    }
