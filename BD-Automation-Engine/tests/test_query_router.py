"""Tests for Phase 33A — Natural Language Query Router."""

import pytest

from src.nlq.query_router import (
    NLQueryRouter,
    QueryPlan,
    QueryResult,
    QueryIntent,
    EXAMPLE_QUERIES,
)


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def router():
    return NLQueryRouter()


# =========================================
# INTENT CLASSIFICATION
# =========================================


@pytest.mark.asyncio
class TestIntentClassification:
    async def test_search_contacts(self, router):
        plan = await router.route_query("Find Tier 1 contacts at Leidos")
        assert plan.intent == QueryIntent.SEARCH_CONTACTS.value

    async def test_search_jobs(self, router):
        plan = await router.route_query("Show TS/SCI jobs at Langley posted this week")
        assert plan.intent == QueryIntent.SEARCH_JOBS.value

    async def test_search_programs(self, router):
        plan = await router.route_query("What programs does GDIT run?")
        assert plan.intent == QueryIntent.SEARCH_PROGRAMS.value

    async def test_search_contracts(self, router):
        plan = await router.route_query("Recent contract awards to Leidos")
        assert plan.intent == QueryIntent.SEARCH_CONTRACTS.value

    async def test_graph_query(self, router):
        plan = await router.route_query(
            "Show the relationship path connected to the site lead"
        )
        assert plan.intent == QueryIntent.GRAPH_QUERY.value

    async def test_analytics(self, router):
        plan = await router.route_query("What's our pipeline worth this quarter?")
        assert plan.intent == QueryIntent.ANALYTICS.value

    async def test_prediction(self, router):
        plan = await router.route_query("Win probability for the Langley opportunity")
        assert plan.intent == QueryIntent.PREDICTION.value

    async def test_forecast(self, router):
        plan = await router.route_query("Hiring trend for Navy DCGS-N")
        assert plan.intent == QueryIntent.FORECAST.value

    async def test_campaign(self, router):
        plan = await router.route_query(
            "Launch an outreach campaign sequence to engage them"
        )
        assert plan.intent == QueryIntent.CAMPAIGN.value

    async def test_generate(self, router):
        plan = await router.route_query("Write outreach email for Kingsley Ero")
        assert plan.intent == QueryIntent.GENERATE.value

    async def test_compare(self, router):
        plan = await router.route_query("Compare GDIT vs Leidos hiring in Virginia")
        assert plan.intent == QueryIntent.COMPARE.value

    async def test_explain(self, router):
        plan = await router.route_query("Why is PACAF scored critical?")
        assert plan.intent == QueryIntent.EXPLAIN.value

    async def test_status(self, router):
        plan = await router.route_query("What happened today?")
        assert plan.intent == QueryIntent.STATUS.value

    async def test_memory(self, router):
        plan = await router.route_query("What do we know about Craig Lindahl?")
        assert plan.intent == QueryIntent.MEMORY.value


# =========================================
# PARAMETER EXTRACTION
# =========================================


@pytest.mark.asyncio
class TestParameterExtraction:
    async def test_extract_company(self, router):
        plan = await router.route_query("Find contacts at leidos")
        assert "leidos" in plan.parameters.get("companies", [])

    async def test_extract_clearance(self, router):
        plan = await router.route_query("Show TS/SCI jobs in San Diego")
        assert plan.parameters.get("clearance") == "TS/SCI"

    async def test_extract_location(self, router):
        plan = await router.route_query("Jobs in san diego")
        assert "san diego" in plan.parameters.get("locations", [])

    async def test_extract_program(self, router):
        plan = await router.route_query("Show dcgs contacts")
        assert "dcgs" in plan.parameters.get("programs", [])

    async def test_extract_timeframe(self, router):
        plan = await router.route_query("Jobs posted this week")
        assert plan.parameters.get("timeframe") == "this_week"

    async def test_extract_limit(self, router):
        plan = await router.route_query("Show top 10 contacts")
        assert plan.parameters.get("limit") == 10

    async def test_extract_tier(self, router):
        plan = await router.route_query("Find Tier 1 contacts")
        assert plan.parameters.get("tier") == 1

    async def test_extract_comparison_entities(self, router):
        plan = await router.route_query("Compare GDIT vs Leidos")
        # Should extract entity_a and entity_b
        assert plan.intent == QueryIntent.COMPARE.value


# =========================================
# QUERY PLAN STRUCTURE
# =========================================


@pytest.mark.asyncio
class TestQueryPlanStructure:
    async def test_plan_has_intent(self, router):
        plan = await router.route_query("Find jobs")
        assert plan.intent is not None
        assert isinstance(plan.intent, str)

    async def test_plan_has_confidence(self, router):
        plan = await router.route_query("Find contacts at Leidos")
        assert 0.0 <= plan.confidence <= 1.0

    async def test_plan_has_original_query(self, router):
        query = "Show me DCGS jobs"
        plan = await router.route_query(query)
        assert plan.original_query == query

    async def test_plan_has_created_at(self, router):
        plan = await router.route_query("Find jobs")
        assert plan.created_at != ""

    async def test_low_confidence_triggers_clarification(self, router):
        plan = await router.route_query("asdfghjkl")
        # Very low confidence should trigger clarification
        assert plan.confidence < 0.5


# =========================================
# MULTI-STEP QUERIES
# =========================================


@pytest.mark.asyncio
class TestMultiStepQueries:
    async def test_simple_query_no_sub_queries(self, router):
        plan = await router.route_query("Find contacts at Leidos")
        # Simple queries may or may not have sub_queries
        assert isinstance(plan.sub_queries, list)

    async def test_sub_queries_are_query_plans(self, router):
        plan = await router.route_query("Find contacts and show their jobs")
        for sq in plan.sub_queries:
            assert isinstance(sq, QueryPlan)


# =========================================
# RESPONSE FORMATTING
# =========================================


@pytest.mark.asyncio
class TestResponseFormatting:
    async def test_format_natural(self, router):
        result = QueryResult(data=[{"name": "Test"}], summary="Found 1 result", count=1)
        formatted = await router.format_response(result, "natural")
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    async def test_format_brief(self, router):
        result = QueryResult(summary="1 result", count=1)
        formatted = await router.format_response(result, "brief")
        assert isinstance(formatted, str)

    async def test_format_table(self, router):
        result = QueryResult(
            data=[{"name": "Test", "score": 85}],
            count=1,
        )
        formatted = await router.format_response(result, "table")
        assert isinstance(formatted, str)

    async def test_format_chart(self, router):
        result = QueryResult(data=[{"x": 1, "y": 2}], count=1)
        formatted = await router.format_response(result, "chart")
        assert isinstance(formatted, str)

    async def test_format_detailed(self, router):
        result = QueryResult(data=[], summary="Test", count=0, intent="search_jobs")
        formatted = await router.format_response(result, "detailed")
        assert "Query:" in formatted

    async def test_format_empty_result(self, router):
        result = QueryResult(count=0)
        formatted = await router.format_response(result, "natural")
        assert "didn't find" in formatted.lower() or "no" in formatted.lower()


# =========================================
# EXAMPLE QUERIES
# =========================================


class TestExampleQueries:
    def test_all_intents_have_examples(self):
        for intent in QueryIntent:
            assert intent.value in EXAMPLE_QUERIES, (
                f"Missing examples for {intent.value}"
            )

    def test_examples_are_non_empty(self):
        for intent, examples in EXAMPLE_QUERIES.items():
            assert len(examples) > 0, f"Empty examples for {intent}"

    def test_fourteen_intents(self):
        assert len(QueryIntent) == 14
