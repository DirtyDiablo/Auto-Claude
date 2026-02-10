"""Tests for Phase 33A — Query Execution Engine."""

import pytest

from src.nlq.query_router import QueryIntent, QueryPlan, QueryResult
from src.nlq.query_executor import QueryExecutor


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def executor():
    """Executor without external clients — uses synthetic data."""
    return QueryExecutor()


@pytest.fixture
def sample_plan():
    def _make(intent, **params):
        return QueryPlan(
            intent=intent,
            parameters={"search_query": "test query", **params},
            confidence=0.8,
            original_query="test query",
        )
    return _make


# =========================================
# SEARCH EXECUTION
# =========================================

@pytest.mark.asyncio
class TestSearchExecution:
    async def test_search_contacts(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.SEARCH_CONTACTS.value)
        result = await executor.execute(plan)
        assert isinstance(result, QueryResult)
        assert result.count > 0

    async def test_search_jobs(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.SEARCH_JOBS.value)
        result = await executor.execute(plan)
        assert isinstance(result, QueryResult)
        assert result.count > 0

    async def test_search_programs(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.SEARCH_PROGRAMS.value)
        result = await executor.execute(plan)
        assert isinstance(result, QueryResult)

    async def test_search_contracts(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.SEARCH_CONTRACTS.value)
        result = await executor.execute(plan)
        assert isinstance(result, QueryResult)


# =========================================
# ANALYTICS EXECUTION
# =========================================

@pytest.mark.asyncio
class TestAnalyticsExecution:
    async def test_analytics(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.ANALYTICS.value)
        result = await executor.execute(plan)
        assert isinstance(result, QueryResult)
        assert "pipeline" in str(result.data).lower() or result.count > 0

    async def test_analytics_has_summary(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.ANALYTICS.value)
        result = await executor.execute(plan)
        assert result.summary != ""


# =========================================
# PREDICTION EXECUTION
# =========================================

@pytest.mark.asyncio
class TestPredictionExecution:
    async def test_prediction(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.PREDICTION.value)
        result = await executor.execute(plan)
        assert isinstance(result, QueryResult)
        assert "win_probability" in str(result.data)

    async def test_forecast(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.FORECAST.value, programs=["AF DCGS"])
        result = await executor.execute(plan)
        assert isinstance(result, QueryResult)
        assert "trend" in str(result.data)


# =========================================
# GRAPH EXECUTION
# =========================================

@pytest.mark.asyncio
class TestGraphExecution:
    async def test_graph_query(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.GRAPH_QUERY.value)
        result = await executor.execute(plan)
        assert isinstance(result, QueryResult)
        assert result.count > 0


# =========================================
# GENERATION EXECUTION
# =========================================

@pytest.mark.asyncio
class TestGenerationExecution:
    async def test_generate_email(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.GENERATE.value, search_query="write email")
        result = await executor.execute(plan)
        assert isinstance(result, QueryResult)
        assert isinstance(result.data, dict)
        assert result.data.get("type") == "email"

    async def test_generate_call_script(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.GENERATE.value, search_query="call script for PM")
        result = await executor.execute(plan)
        assert result.data.get("type") == "call_script"


# =========================================
# COMPARISON EXECUTION
# =========================================

@pytest.mark.asyncio
class TestComparisonExecution:
    async def test_compare(self, executor, sample_plan):
        plan = sample_plan(
            QueryIntent.COMPARE.value,
            entity_a="GDIT", entity_b="Leidos",
        )
        result = await executor.execute(plan)
        assert isinstance(result, QueryResult)
        assert "entity_a" in result.data
        assert "entity_b" in result.data


# =========================================
# OTHER EXECUTORS
# =========================================

@pytest.mark.asyncio
class TestOtherExecutors:
    async def test_campaign(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.CAMPAIGN.value, locations=["San Diego"])
        result = await executor.execute(plan)
        assert isinstance(result, QueryResult)

    async def test_explain(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.EXPLAIN.value)
        result = await executor.execute(plan)
        assert "explanation" in str(result.data) or "dimensions" in str(result.data)

    async def test_status(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.STATUS.value)
        result = await executor.execute(plan)
        assert isinstance(result, QueryResult)
        assert "date" in str(result.data)

    async def test_memory(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.MEMORY.value)
        result = await executor.execute(plan)
        assert isinstance(result, QueryResult)


# =========================================
# MULTI-STEP EXECUTION
# =========================================

@pytest.mark.asyncio
class TestMultiStepExecution:
    async def test_multi_step(self, executor):
        main = QueryPlan(
            intent=QueryIntent.SEARCH_CONTACTS.value,
            parameters={"search_query": "contacts"},
            confidence=0.8,
        )
        sub = QueryPlan(
            intent=QueryIntent.SEARCH_JOBS.value,
            parameters={"search_query": "jobs"},
            confidence=0.7,
        )
        main.sub_queries = [sub]
        result = await executor.execute(main)
        assert isinstance(result, QueryResult)
        assert "primary" in result.data
        assert "sub_results" in result.data


# =========================================
# SUGGESTIONS
# =========================================

@pytest.mark.asyncio
class TestSuggestions:
    async def test_result_has_suggestions(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.SEARCH_CONTACTS.value)
        result = await executor.execute(plan)
        assert isinstance(result.suggestions, list)
        assert len(result.suggestions) > 0

    async def test_execution_time_tracked(self, executor, sample_plan):
        plan = sample_plan(QueryIntent.SEARCH_JOBS.value)
        result = await executor.execute(plan)
        assert result.execution_time_ms >= 0
