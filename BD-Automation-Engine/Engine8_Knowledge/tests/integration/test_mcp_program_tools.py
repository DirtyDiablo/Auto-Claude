"""
Phase 26A — MCP Program & Search Tools Tests

Tests 6 program/search tools: search_programs, get_program_intel,
find_hiring_signals, get_competitive_landscape, hybrid_search, graph_query.
Mocks the hub client — no network access required.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_hub():
    hub = AsyncMock()
    hub.get = AsyncMock(return_value={
        "programs": [
            {"name": "DCGS", "prime": "Raytheon", "value": 500_000_000},
            {"name": "GBSD", "prime": "Northrop Grumman", "value": 1_200_000_000},
        ],
        "total": 2,
    })
    hub.post = AsyncMock(return_value={
        "results": [{"id": "r1", "content": "DCGS data", "score": 0.85}],
        "count": 1,
    })
    return hub


@pytest.fixture
def mock_mcp():
    mcp = MagicMock()
    registered_tools = {}

    def tool_decorator():
        def wrapper(fn):
            registered_tools[fn.__name__] = fn
            return fn
        return wrapper

    mcp.tool = tool_decorator
    mcp._registered = registered_tools
    return mcp


@pytest.fixture
def tools(mock_mcp, mock_hub):
    from Engine8_Knowledge.mcp.program_tools import register_program_tools
    count = register_program_tools(mock_mcp, mock_hub)
    return mock_mcp._registered, count


# ---------------------------------------------------------------------------
# TestSearchPrograms
# ---------------------------------------------------------------------------


class TestSearchPrograms:
    @pytest.mark.asyncio
    async def test_search_programs(self, tools, mock_hub):
        fns, _ = tools
        result = await fns["search_programs"]("DCGS")
        assert len(result) == 2
        assert result[0]["name"] == "DCGS"
        mock_hub.get.assert_called()

    @pytest.mark.asyncio
    async def test_search_empty(self, tools, mock_hub):
        mock_hub.get = AsyncMock(return_value={"programs": [], "total": 0})
        fns, _ = tools
        result = await fns["search_programs"]("nonexistent")
        assert result == []


# ---------------------------------------------------------------------------
# TestGetProgramIntel
# ---------------------------------------------------------------------------


class TestGetProgramIntel:
    @pytest.mark.asyncio
    async def test_get_program_intel(self, tools, mock_hub):
        fns, _ = tools
        # get_program_intel makes 3 hub calls
        mock_hub.get = AsyncMock(side_effect=[
            {"name": "DCGS", "prime": "Raytheon", "value": 500_000_000},
            {"jobs": [{"title": "Analyst", "company": "GDIT"}], "total": 1},
            {"contacts": [{"name": "Alice", "program": "DCGS"}], "total": 1},
        ])
        result = await fns["get_program_intel"]("DCGS")
        assert "matching_jobs" in result
        assert "contacts" in result

    @pytest.mark.asyncio
    async def test_program_intel_enriched(self, tools, mock_hub):
        fns, _ = tools
        mock_hub.get = AsyncMock(side_effect=[
            {"name": "GBSD", "prime": "Northrop", "subs": ["L3Harris"]},
            {"jobs": [{"title": "Engineer"}, {"title": "PM"}], "total": 2},
            {"contacts": [], "total": 0},
        ])
        result = await fns["get_program_intel"]("GBSD")
        assert result["name"] == "GBSD"
        assert len(result["matching_jobs"]) == 2
        assert result["contacts"] == []


# ---------------------------------------------------------------------------
# TestFindHiringSignals
# ---------------------------------------------------------------------------


class TestFindHiringSignals:
    @pytest.mark.asyncio
    async def test_find_hiring_signals(self, tools, mock_hub):
        mock_hub.get = AsyncMock(return_value={
            "jobs": [
                {"title": "DCGS Analyst", "company": "GDIT", "program": "DCGS",
                 "location": "San Diego", "clearance": "TS/SCI"},
            ],
            "total": 1,
        })
        fns, _ = tools
        result = await fns["find_hiring_signals"](program="DCGS")
        assert len(result) == 1
        assert result[0]["type"] == "new_job"
        assert result[0]["program"] == "DCGS"

    @pytest.mark.asyncio
    async def test_hiring_no_results(self, tools, mock_hub):
        mock_hub.get = AsyncMock(return_value={"jobs": [], "total": 0})
        fns, _ = tools
        result = await fns["find_hiring_signals"](program="NonexistentProgram")
        assert result == []


# ---------------------------------------------------------------------------
# TestGetCompetitiveLandscape
# ---------------------------------------------------------------------------


class TestGetCompetitiveLandscape:
    @pytest.mark.asyncio
    async def test_get_competitive_landscape(self, tools, mock_hub):
        mock_hub.get = AsyncMock(return_value={
            "program": "DCGS",
            "competitors": ["Raytheon", "Northrop", "GDIT"],
            "contract_count": 5,
        })
        fns, _ = tools
        result = await fns["get_competitive_landscape"]("DCGS")
        assert "competitors" in result

    @pytest.mark.asyncio
    async def test_competitive_fallback(self, tools, mock_hub):
        """Fallback when /competitive/landscape returns empty."""
        mock_hub.get = AsyncMock(side_effect=[
            {},  # /competitive/landscape empty
            {"name": "DCGS"},  # /bdgraph/program/DCGS
            {"jobs": [
                {"title": "Analyst", "company": "GDIT"},
                {"title": "Engineer", "company": "Raytheon"},
            ], "total": 2},  # /api/v2/jobs
        ])
        fns, _ = tools
        result = await fns["get_competitive_landscape"]("DCGS")
        assert "program" in result
        assert "competing_companies" in result
        assert "GDIT" in result["competing_companies"]


# ---------------------------------------------------------------------------
# TestHybridSearch
# ---------------------------------------------------------------------------


class TestHybridSearch:
    @pytest.mark.asyncio
    async def test_hybrid_search(self, tools, mock_hub):
        fns, _ = tools
        result = await fns["hybrid_search"]("DCGS analyst")
        assert "results" in result
        mock_hub.post.assert_called()

    @pytest.mark.asyncio
    async def test_hybrid_search_empty(self, tools, mock_hub):
        mock_hub.post = AsyncMock(return_value={})
        fns, _ = tools
        result = await fns["hybrid_search"]("test")
        assert result == {"results": [], "count": 0}


# ---------------------------------------------------------------------------
# TestGraphQuery
# ---------------------------------------------------------------------------


class TestGraphQuery:
    @pytest.mark.asyncio
    async def test_graph_query(self, tools, mock_hub):
        mock_hub.post = AsyncMock(return_value={
            "results": [
                {"name": "Alice", "title": "PM", "program": "DCGS"},
            ]
        })
        fns, _ = tools
        result = await fns["graph_query"]("MATCH (p:Person) RETURN p LIMIT 1")
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_graph_query_empty(self, tools, mock_hub):
        mock_hub.post = AsyncMock(return_value={})
        fns, _ = tools
        result = await fns["graph_query"]("MATCH (p:Person {name:'Nobody'}) RETURN p")
        assert result == []


# ---------------------------------------------------------------------------
# TestRegisterCount
# ---------------------------------------------------------------------------


class TestRegisterCount:
    def test_register_count(self, tools):
        _, count = tools
        assert count == 6
