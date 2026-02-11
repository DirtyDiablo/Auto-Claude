"""Phase 40A — Agentic RAG + Self-RAG + ColBERT Reranker + Query Decomposition."""

from src.rag.agentic_rag import (
    AgenticRAGOrchestrator,
    AgenticRAGResult,
    RetrievalTool,
    RetrievalStep,
    RetrievalPlan,
    Citation,
    QueryComplexity,
    BenchmarkResult,
    classify_intent,
    classify_complexity,
    extract_query_entities,
    run_benchmark,
    get_agentic_rag,
)
from src.rag.self_rag import (
    SelfReflectiveRAG,
    SelfRAGResult,
    RelevanceScore,
    SupportScore,
    UtilityScore,
    get_self_rag,
)
from src.rag.reranker import (
    AdvancedReranker,
    ScoredDoc,
    RerankResult,
    get_reranker,
)
from src.rag.query_decomposer import (
    QueryDecomposer,
    DecompositionPlan,
    SubQuery,
    DependencyGraph,
    get_query_decomposer,
)

__all__ = [
    "AgenticRAGOrchestrator", "AgenticRAGResult", "RetrievalTool",
    "RetrievalStep", "RetrievalPlan", "Citation", "QueryComplexity",
    "BenchmarkResult", "classify_intent", "classify_complexity",
    "extract_query_entities", "run_benchmark", "get_agentic_rag",
    "SelfReflectiveRAG", "SelfRAGResult", "RelevanceScore",
    "SupportScore", "UtilityScore", "get_self_rag",
    "AdvancedReranker", "ScoredDoc", "RerankResult", "get_reranker",
    "QueryDecomposer", "DecompositionPlan", "SubQuery",
    "DependencyGraph", "get_query_decomposer",
]
