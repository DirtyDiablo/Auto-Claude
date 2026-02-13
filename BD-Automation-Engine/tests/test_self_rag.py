"""Tests for Phase 40A — Self-Reflective RAG."""

import pytest

from src.rag.self_rag import (
    SelfReflectiveRAG,
    SelfRAGResult,
    RelevanceScore,
    SupportScore,
    UtilityScore,
    reformulate_query,
    get_self_rag,
    _compute_token_overlap,
    _compute_entity_overlap,
    _assess_retrieval_need,
)


# =========================================
# FIXTURES
# =========================================

async def mock_retrieval(query: str, limit: int = 10):
    """Mock retrieval function that returns canned passages."""
    return [
        {"text": "John Smith works at GDIT as a Senior Analyst on the DCGS-A program."},
        {"text": "GDIT is hiring 5 new analysts for the DCGS program in Q2 2025."},
        {"text": "The DCGS-A program manager at Langley is Jeff Bartsch."},
    ]


@pytest.fixture
def self_rag():
    return SelfReflectiveRAG(retrieval_fn=mock_retrieval)


@pytest.fixture
def empty_rag():
    return SelfReflectiveRAG()


# =========================================
# HELPER FUNCTIONS
# =========================================

def test_token_overlap_identical():
    score = _compute_token_overlap("DCGS program status", "DCGS program status update")
    assert score > 0.5


def test_token_overlap_no_match():
    score = _compute_token_overlap("hello world", "completely different text")
    assert score == 0.0


def test_token_overlap_empty():
    assert _compute_token_overlap("", "some text") == 0.0
    assert _compute_token_overlap("some text", "") == 0.0


def test_entity_overlap_found():
    score = _compute_entity_overlap("Find John Smith at GDIT", "John Smith works at GDIT.")
    assert score >= 0.5


def test_entity_overlap_missing():
    score = _compute_entity_overlap("Find John Smith", "No names here.")
    assert score == 0.0


def test_entity_overlap_no_entities():
    score = _compute_entity_overlap("hello world", "some text")
    assert score == 1.0  # No entities to check


def test_assess_retrieval_needed():
    assert _assess_retrieval_need("Who manages DCGS-A?") is True


def test_assess_retrieval_not_needed():
    assert _assess_retrieval_need("Hello!") is False
    assert _assess_retrieval_need("Thanks") is False


# =========================================
# RELEVANCE EVALUATION
# =========================================

@pytest.mark.asyncio
async def test_evaluate_relevance(self_rag):
    scores = await self_rag.evaluate_relevance(
        "DCGS program at GDIT",
        [
            "GDIT works on the DCGS-A program with 50 analysts.",
            "The weather today is sunny with clear skies.",
        ],
    )
    assert len(scores) == 2
    assert isinstance(scores[0], RelevanceScore)
    # First passage should be more relevant
    assert scores[0].score > scores[1].score


@pytest.mark.asyncio
async def test_evaluate_relevance_empty(self_rag):
    scores = await self_rag.evaluate_relevance("test", [])
    assert scores == []


@pytest.mark.asyncio
async def test_evaluate_relevance_marks_relevant(self_rag):
    scores = await self_rag.evaluate_relevance(
        "DCGS GDIT analysts",
        ["GDIT has 50 DCGS analysts working at Langley."],
    )
    assert scores[0].relevant is True


# =========================================
# SUPPORT EVALUATION
# =========================================

@pytest.mark.asyncio
async def test_evaluate_support_supported(self_rag):
    answer = "John Smith works at GDIT on the DCGS program."
    passages = ["John Smith is a Senior Analyst at GDIT working on DCGS-A."]
    result = await self_rag.evaluate_support(answer, passages)
    assert isinstance(result, SupportScore)
    assert result.score > 0.0


@pytest.mark.asyncio
async def test_evaluate_support_unsupported(self_rag):
    answer = "The company was founded in 1850 and has 50000 employees worldwide."
    passages = ["GDIT works on DCGS-A."]
    result = await self_rag.evaluate_support(answer, passages)
    assert result.score < 1.0


@pytest.mark.asyncio
async def test_evaluate_support_empty(self_rag):
    result = await self_rag.evaluate_support("", [])
    assert result.score == 0.0
    assert result.supported is False


# =========================================
# UTILITY EVALUATION
# =========================================

@pytest.mark.asyncio
async def test_evaluate_utility_useful(self_rag):
    result = await self_rag.evaluate_utility(
        "Who works at GDIT on DCGS?",
        "John Smith works at GDIT as a Senior Analyst on the DCGS-A program.",
    )
    assert isinstance(result, UtilityScore)
    assert result.score > 0.3


@pytest.mark.asyncio
async def test_evaluate_utility_negative(self_rag):
    result = await self_rag.evaluate_utility(
        "Who manages DCGS-A?",
        "I cannot find that information.",
    )
    # Negative answers should score lower
    assert result.score < 0.5


@pytest.mark.asyncio
async def test_evaluate_utility_empty(self_rag):
    result = await self_rag.evaluate_utility("", "")
    assert result.score == 0.0


# =========================================
# QUERY REFORMULATION
# =========================================

def test_reformulate_round2():
    result = reformulate_query("Who manages DCGS?", ["low_relevance"], 2)
    assert "DCGS" in result
    assert len(result) > len("Who manages DCGS?")


def test_reformulate_round3():
    result = reformulate_query("Find only the specific DCGS manager", [], 3)
    assert result != ""


# =========================================
# ADAPTIVE RETRIEVAL
# =========================================

@pytest.mark.asyncio
async def test_adaptive_retrieve(self_rag):
    result = await self_rag.adaptive_retrieve("Who works at GDIT on DCGS?")
    assert isinstance(result, SelfRAGResult)
    assert result.query_id != ""
    assert result.answer != ""
    assert result.retrieval_needed is True
    assert len(result.rounds) >= 1


@pytest.mark.asyncio
async def test_adaptive_retrieve_no_retrieval_needed(self_rag):
    result = await self_rag.adaptive_retrieve("Hello!")
    assert result.retrieval_needed is False


@pytest.mark.asyncio
async def test_adaptive_retrieve_empty_retrieval(empty_rag):
    result = await empty_rag.adaptive_retrieve("Who manages DCGS?")
    assert result.retrieval_needed is True
    assert result.total_passages_retrieved == 0


@pytest.mark.asyncio
async def test_adaptive_retrieve_has_scores(self_rag):
    result = await self_rag.adaptive_retrieve("DCGS program at GDIT")
    assert result.support_score is not None
    assert result.utility_score is not None
    assert result.confidence >= 0.0


@pytest.mark.asyncio
async def test_adaptive_retrieve_measures_latency(self_rag):
    result = await self_rag.adaptive_retrieve("test query")
    assert result.latency_ms >= 0


# =========================================
# SINGLETON
# =========================================

def test_get_self_rag_singleton():
    s1 = get_self_rag()
    s2 = get_self_rag()
    assert s1 is s2
