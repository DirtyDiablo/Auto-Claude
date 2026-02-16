"""Phase 40A — Agentic RAG API

10 endpoints for agentic RAG queries, self-RAG evaluation, reranking,
query decomposition, benchmarks, and retrieval traces.
"""

import logging
from dataclasses import asdict
from typing import Any, Dict, List

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.rag.agentic_rag import (
    get_agentic_rag,
    run_benchmark,
)
from src.rag.self_rag import (
    get_self_rag,
)
from src.rag.reranker import (
    ScoredDoc,
    get_reranker,
)
from src.rag.query_decomposer import (
    get_query_decomposer,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])


# =========================================
# REQUEST MODELS
# =========================================


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural language question")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Optional context"
    )


class SimpleQueryRequest(BaseModel):
    question: str = Field(..., min_length=1)


class DecomposeRequest(BaseModel):
    query: str = Field(..., min_length=1)


class RelevanceRequest(BaseModel):
    query: str = Field(..., min_length=1)
    passages: List[str] = Field(..., min_length=1)


class SupportRequest(BaseModel):
    answer: str = Field(..., min_length=1)
    passages: List[str] = Field(..., min_length=1)


class RerankRequest(BaseModel):
    query: str = Field(..., min_length=1)
    channel_results: Dict[str, List[Dict[str, Any]]] = Field(
        ...,
        description="Channel name → list of docs (each with 'text', optional 'doc_id', 'score')",
    )
    top_k: int = Field(10, ge=1, le=100)


# =========================================
# SERIALIZATION
# =========================================


def _serialize(obj: Any) -> Any:
    """Convert dataclass to dict."""
    if hasattr(obj, "__dataclass_fields__"):
        d = asdict(obj)
        return d
    return obj


def _serialize_list(items: list) -> list:
    return [_serialize(item) for item in items]


# =========================================
# ENDPOINTS
# =========================================


@router.post("/query")
async def rag_query(request: RAGQueryRequest):
    """Full agentic RAG query with adaptive retrieval."""
    rag = get_agentic_rag()
    result = await rag.query(request.question, request.context)
    return _serialize(result)


@router.post("/query/simple")
async def rag_query_simple(request: SimpleQueryRequest):
    """Simple single-round retrieval without adaptive loop."""
    rag = get_agentic_rag()
    result = await rag.query_simple(request.question)
    return _serialize(result)


@router.post("/query/decompose")
async def rag_decompose(request: DecomposeRequest):
    """Decompose a complex query into sub-queries without executing."""
    decomposer = get_query_decomposer()
    plan = await decomposer.decompose(request.query)
    return _serialize(plan)


@router.post("/evaluate/relevance")
async def evaluate_relevance(request: RelevanceRequest):
    """Score passage relevance to a query."""
    self_rag = get_self_rag()
    scores = await self_rag.evaluate_relevance(request.query, request.passages)
    return {"scores": _serialize_list(scores), "count": len(scores)}


@router.post("/evaluate/support")
async def evaluate_support(request: SupportRequest):
    """Check if an answer is supported by passages (hallucination detection)."""
    self_rag = get_self_rag()
    result = await self_rag.evaluate_support(request.answer, request.passages)
    return _serialize(result)


@router.post("/rerank")
async def rerank(request: RerankRequest):
    """Rerank passages using the full reranking pipeline."""
    reranker = get_reranker()

    # Convert input to ScoredDoc objects
    channel_results = {}
    for channel, docs in request.channel_results.items():
        channel_results[channel] = [
            ScoredDoc(
                doc_id=d.get("doc_id", ""),
                text=d.get("text", ""),
                score=d.get("score", 0.0),
                source=d.get("source", channel),
                metadata=d.get("metadata", {}),
            )
            for d in docs
        ]

    result = await reranker.full_rerank(request.query, channel_results, request.top_k)
    return _serialize(result)


@router.get("/stats")
async def rag_stats():
    """Get RAG performance statistics."""
    rag = get_agentic_rag()
    return rag.get_stats()


@router.get("/benchmark")
async def get_benchmark():
    """Get the most recent benchmark results."""
    rag = get_agentic_rag()
    history = rag.get_history()
    if not history:
        return {
            "message": "No benchmark results available. Run POST /rag/benchmark/run first."
        }
    return {
        "total_queries": len(history),
        "latest": _serialize(history[-1]) if history else None,
    }


@router.post("/benchmark/run")
async def run_benchmark_suite():
    """Run the full quality benchmark suite."""
    rag = get_agentic_rag()
    result = await run_benchmark(rag)
    return _serialize(result)


@router.get("/trace/{query_id}")
async def get_trace(query_id: str):
    """Get full retrieval trace for a specific query."""
    rag = get_agentic_rag()
    trace = rag.get_trace(query_id)
    if trace is None:
        raise HTTPException(
            status_code=404, detail=f"No trace found for query_id: {query_id}"
        )
    return _serialize(trace)


# =========================================
# INTEGRATION
# =========================================


def include_rag_router(app: FastAPI) -> None:
    """Register the RAG router with the FastAPI app."""
    app.include_router(router)
    logger.info("RAG API router registered with 10 endpoints")
