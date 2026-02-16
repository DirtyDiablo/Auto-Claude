"""Tests for Phase 40A — Query Decomposition Engine."""

import pytest

from src.rag.query_decomposer import (
    QueryDecomposer,
    DecompositionPlan,
    DependencyGraph,
    get_query_decomposer,
    _extract_entities,
    _classify_sub_intent,
    _compute_complexity,
)


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def decomposer():
    return QueryDecomposer()


# =========================================
# HELPER FUNCTIONS
# =========================================


def test_extract_entities():
    entities = _extract_entities("Find contacts at Leidos working on DCGS")
    assert any("Leidos" in e for e in entities)
    assert any("DCGS" in e for e in entities)


def test_extract_entities_empty():
    entities = _extract_entities("hello world")
    assert len(entities) == 0


def test_classify_sub_intent_person():
    assert _classify_sub_intent("who is the manager?") == "person"


def test_classify_sub_intent_hiring():
    assert _classify_sub_intent("what open positions exist?") == "hiring"


def test_classify_sub_intent_trend():
    assert _classify_sub_intent("what are the growth trends over time?") == "trend"


def test_classify_sub_intent_general():
    assert _classify_sub_intent("tell me more") == "general"


def test_compute_complexity_simple():
    score = _compute_complexity("What is Jeff's email?")
    assert score < 0.4


def test_compute_complexity_high():
    score = _compute_complexity(
        "Compare the hiring trends at Langley vs PACAF and identify "
        "which site has more urgent staffing needs and what programs are affected"
    )
    assert score > 0.3


# =========================================
# DECOMPOSITION
# =========================================


@pytest.mark.asyncio
async def test_decompose_simple(decomposer):
    plan = await decomposer.decompose("What is Jeff's email?")
    assert isinstance(plan, DecompositionPlan)
    assert plan.is_decomposed is False
    assert len(plan.sub_queries) == 1


@pytest.mark.asyncio
async def test_decompose_comparison(decomposer):
    plan = await decomposer.decompose("Compare hiring at Langley vs PACAF")
    assert isinstance(plan, DecompositionPlan)
    assert plan.is_decomposed is True
    assert len(plan.sub_queries) >= 2
    assert plan.synthesis_strategy == "compare"


@pytest.mark.asyncio
async def test_decompose_multi_entity(decomposer):
    plan = await decomposer.decompose(
        "Find contacts at Leidos and GDIT working on DCGS"
    )
    assert len(plan.sub_queries) >= 1


@pytest.mark.asyncio
async def test_decompose_has_ids(decomposer):
    plan = await decomposer.decompose("Compare GDIT and Leidos on DCGS")
    for sq in plan.sub_queries:
        assert sq.id != ""


@pytest.mark.asyncio
async def test_decompose_assigns_intents(decomposer):
    plan = await decomposer.decompose(
        "Who manages DCGS and what are their pain points?"
    )
    for sq in plan.sub_queries:
        assert sq.intent != ""


# =========================================
# DEPENDENCY GRAPH
# =========================================


@pytest.mark.asyncio
async def test_classify_dependency_single(decomposer):
    graph = await decomposer.classify_dependency(["What is Jeff's email?"])
    assert isinstance(graph, DependencyGraph)
    assert len(graph.execution_order) >= 1


@pytest.mark.asyncio
async def test_classify_dependency_parallel(decomposer):
    graph = await decomposer.classify_dependency(
        [
            "What positions are open at Langley?",
            "What positions are open at PACAF?",
        ]
    )
    assert len(graph.nodes) == 2
    # These should be parallel (no dependencies between them)
    assert len(graph.execution_order) >= 1


@pytest.mark.asyncio
async def test_classify_dependency_empty(decomposer):
    graph = await decomposer.classify_dependency([])
    assert graph.nodes == []
    assert graph.execution_order == []


# =========================================
# SYNTHESIS
# =========================================


@pytest.mark.asyncio
async def test_synthesize(decomposer):
    result = await decomposer.synthesize(
        "Compare Langley and PACAF",
        {
            "Langley hiring": "Langley has 5 open positions.",
            "PACAF hiring": "PACAF has 3 open positions.",
        },
    )
    assert "Langley" in result
    assert "PACAF" in result


@pytest.mark.asyncio
async def test_synthesize_single(decomposer):
    result = await decomposer.synthesize(
        "Simple query",
        {"answer": "The answer is 42."},
    )
    assert "42" in result


@pytest.mark.asyncio
async def test_synthesize_empty(decomposer):
    result = await decomposer.synthesize("query", {})
    assert "No information" in result


# =========================================
# HISTORY
# =========================================


@pytest.mark.asyncio
async def test_decompose_history(decomposer):
    await decomposer.decompose("query 1")
    await decomposer.decompose("query 2")
    history = decomposer.get_history()
    assert len(history) == 2


# =========================================
# SINGLETON
# =========================================


def test_get_query_decomposer_singleton():
    d1 = get_query_decomposer()
    d2 = get_query_decomposer()
    assert d1 is d2
