"""Tests for Phase 40A — Agentic RAG Orchestrator."""

import pytest

from src.rag.agentic_rag import (
    AgenticRAGOrchestrator,
    AgenticRAGResult,
    RetrievalTool,
    RetrievalToolResult,
    RetrievalStep,
    QueryComplexity,
    AgentState,
    BenchmarkResult,
    classify_intent,
    classify_complexity,
    extract_query_entities,
    run_benchmark,
    get_agentic_rag,
)


# =========================================
# FIXTURES
# =========================================

class MockTool(RetrievalTool):
    """Mock retrieval tool that returns canned results."""

    def __init__(self, name: str, results: list = None):
        super().__init__(name, f"Mock {name}")
        self._results = results or []

    async def search(self, query: str, limit: int = 10, **kwargs) -> RetrievalToolResult:
        return RetrievalToolResult(
            tool=self.name,
            results=self._results[:limit],
            scores=[0.85] * min(len(self._results), limit),
        )


@pytest.fixture
def mock_tools():
    return {
        "vector_search": MockTool("vector_search", [
            {"text": "John Smith works at GDIT as a Senior Analyst on DCGS-A.", "score": 0.9},
            {"text": "GDIT is hiring 5 analysts for the DCGS program in Q2.", "score": 0.85},
        ]),
        "keyword_search": MockTool("keyword_search", [
            {"text": "DCGS-A program manager is Jeff Bartsch at Langley.", "score": 0.8},
        ]),
        "graph_traverse": MockTool("graph_traverse", [
            {"text": "John Smith → WORKS_AT → GDIT → PRIME_ON → DCGS-A", "score": 0.75},
        ]),
    }


@pytest.fixture
def orchestrator(mock_tools):
    return AgenticRAGOrchestrator(tools=mock_tools)


@pytest.fixture
def empty_orchestrator():
    return AgenticRAGOrchestrator()


# =========================================
# INTENT CLASSIFICATION
# =========================================

def test_classify_intent_person():
    assert classify_intent("Who is the manager of DCGS-A?") == "person_lookup"


def test_classify_intent_hiring():
    assert classify_intent("What are the open positions at GDIT?") == "hiring"


def test_classify_intent_program():
    assert classify_intent("What is the status of the DCGS contract?") == "program_intel"


def test_classify_intent_trend():
    # This query matches both hiring and trend — verify trend wins with a pure trend query
    assert classify_intent("What are the growth trends over the last 12 months?") == "trend_analysis"


def test_classify_intent_relationship():
    assert classify_intent("Who reports to the program director?") == "relationship"


def test_classify_intent_general():
    assert classify_intent("hello world") == "general"


# =========================================
# COMPLEXITY CLASSIFICATION
# =========================================

def test_complexity_simple():
    assert classify_complexity("What is Jeff's email?") == "simple"


def test_complexity_moderate():
    result = classify_complexity("Who manages DCGS-A and what are their pain points?")
    assert result in ("moderate", "complex")


def test_complexity_analytical():
    assert classify_complexity("Compare hiring trends across DCGS sites over the last 12 months") == "analytical"


def test_complexity_complex():
    result = classify_complexity("Which contacts at Leidos have connections to Langley that also work on DCGS?")
    assert result in ("complex", "moderate")


# =========================================
# ENTITY EXTRACTION
# =========================================

def test_extract_entities_person():
    entities = extract_query_entities("Who is John Smith?")
    assert "John Smith" in entities


def test_extract_entities_program():
    entities = extract_query_entities("What is the status of DCGS-A?")
    assert any("DCGS" in e for e in entities)


def test_extract_entities_org():
    entities = extract_query_entities("Find contacts at Leidos working on DCGS")
    assert any("Leidos" in e for e in entities)


def test_extract_entities_empty():
    entities = extract_query_entities("hello")
    assert len(entities) == 0


# =========================================
# ORCHESTRATOR QUERY
# =========================================

@pytest.mark.asyncio
async def test_query_returns_result(orchestrator):
    result = await orchestrator.query("Who manages DCGS-A?")
    assert isinstance(result, AgenticRAGResult)
    assert result.query_id != ""
    assert result.answer != ""
    assert result.complexity in [c.value for c in QueryComplexity]


@pytest.mark.asyncio
async def test_query_has_trace(orchestrator):
    result = await orchestrator.query("What are GDIT hiring plans?")
    assert len(result.retrieval_trace) >= 1
    assert all(isinstance(s, RetrievalStep) for s in result.retrieval_trace)


@pytest.mark.asyncio
async def test_query_has_citations(orchestrator):
    result = await orchestrator.query("Tell me about DCGS-A at GDIT")
    assert len(result.citations) >= 1


@pytest.mark.asyncio
async def test_query_has_state_history(orchestrator):
    result = await orchestrator.query("Who is John Smith?")
    assert AgentState.ANALYZE.value in result.state_history
    assert AgentState.PLAN.value in result.state_history


@pytest.mark.asyncio
async def test_query_tracks_tools_used(orchestrator):
    result = await orchestrator.query("DCGS program status")
    assert len(result.tools_used) >= 1


@pytest.mark.asyncio
async def test_query_measures_latency(orchestrator):
    result = await orchestrator.query("test query")
    assert result.latency_ms >= 0


# =========================================
# SIMPLE QUERY
# =========================================

@pytest.mark.asyncio
async def test_query_simple(orchestrator):
    result = await orchestrator.query_simple("Who is Jeff Bartsch?")
    assert isinstance(result, AgenticRAGResult)
    assert result.iterations == 1
    assert result.complexity == QueryComplexity.SIMPLE.value


@pytest.mark.asyncio
async def test_query_simple_no_tools(empty_orchestrator):
    result = await empty_orchestrator.query_simple("test")
    assert result.answer == "No results found."


# =========================================
# TRACE & STATS
# =========================================

@pytest.mark.asyncio
async def test_get_trace(orchestrator):
    result = await orchestrator.query("DCGS hiring")
    trace = orchestrator.get_trace(result.query_id)
    assert trace is not None
    assert trace.query_id == result.query_id


def test_get_trace_missing(orchestrator):
    assert orchestrator.get_trace("nonexistent") is None


@pytest.mark.asyncio
async def test_get_stats(orchestrator):
    await orchestrator.query("test query 1")
    await orchestrator.query("test query 2")
    stats = orchestrator.get_stats()
    assert stats["total_queries"] == 2
    assert stats["avg_latency_ms"] >= 0


# =========================================
# NO-TOOL ORCHESTRATOR
# =========================================

@pytest.mark.asyncio
async def test_query_no_tools(empty_orchestrator):
    result = await empty_orchestrator.query("Who manages DCGS?")
    assert result.answer != ""  # Should still produce an answer (even if "no info")
    assert result.confidence == 0.0


# =========================================
# BENCHMARK
# =========================================

@pytest.mark.asyncio
async def test_run_benchmark(orchestrator):
    result = await run_benchmark(orchestrator)
    assert isinstance(result, BenchmarkResult)
    assert result.total_queries == 8
    assert len(result.results) == 8
    assert result.avg_confidence >= 0.0


# =========================================
# SINGLETON
# =========================================

def test_get_agentic_rag_singleton():
    r1 = get_agentic_rag()
    r2 = get_agentic_rag()
    assert r1 is r2
