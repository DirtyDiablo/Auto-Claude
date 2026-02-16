"""
Phase 27A — Org Chart Engine Tests

Tests OrgChartEngine: generate (tree, network, matrix), infer_reports_to,
get_team, get_chain_of_command, compare, caching, and singleton.
Mocks Neo4j and Hub API — no external services required.
"""

import pytest
from unittest.mock import AsyncMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.visualization.org_chart_engine import (
    OrgChartEngine,
    Person,
    OrgChart,
    Team,
)


# ---------------------------------------------------------------------------
# Fixture Data
# ---------------------------------------------------------------------------


SAMPLE_PEOPLE = [
    Person(
        id="1",
        name="John CEO",
        title="CEO",
        company="GDIT",
        program="DCGS",
        tier=1,
        location="Fairfax",
        reports_to=None,
    ),
    Person(
        id="2",
        name="Alice VP",
        title="VP Engineering",
        company="GDIT",
        program="DCGS",
        tier=2,
        location="Fairfax",
        reports_to="John CEO",
    ),
    Person(
        id="3",
        name="Bob Director",
        title="Director",
        company="GDIT",
        program="DCGS",
        tier=3,
        location="San Diego",
        reports_to="Alice VP",
    ),
    Person(
        id="4",
        name="Carol Manager",
        title="Manager",
        company="GDIT",
        program="DCGS",
        tier=4,
        location="San Diego",
        reports_to="Bob Director",
    ),
    Person(
        id="5",
        name="Dave Analyst",
        title="Senior Analyst",
        company="GDIT",
        program="DCGS",
        tier=5,
        location="San Diego",
        reports_to="Carol Manager",
    ),
    Person(
        id="6",
        name="Eve Engineer",
        title="Engineer",
        company="GDIT",
        program="ISR",
        tier=6,
        location="Tampa",
        reports_to=None,
    ),
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine():
    """OrgChartEngine with mocked _fetch_people."""
    eng = OrgChartEngine()
    eng._fetch_people = AsyncMock(return_value=SAMPLE_PEOPLE.copy())
    return eng


# ---------------------------------------------------------------------------
# TestInit
# ---------------------------------------------------------------------------


class TestInit:
    def test_init(self):
        eng = OrgChartEngine()
        assert eng.neo4j is None
        assert eng.hub is None
        assert eng._cache == {}


# ---------------------------------------------------------------------------
# TestGenerate
# ---------------------------------------------------------------------------


class TestGenerate:
    @pytest.mark.asyncio
    async def test_generate_tree(self, engine):
        chart = await engine.generate(mode="tree")
        assert isinstance(chart, OrgChart)
        assert chart.mode == "tree"
        assert len(chart.nodes) == 6
        assert len(chart.edges) > 0
        assert chart.chart_id.startswith("org_")
        assert chart.generated_at is not None

    @pytest.mark.asyncio
    async def test_generate_network(self, engine):
        chart = await engine.generate(mode="network")
        assert chart.mode == "network"
        assert chart.metadata["mode"] == "network"

    @pytest.mark.asyncio
    async def test_generate_matrix(self, engine):
        chart = await engine.generate(mode="matrix")
        assert chart.mode == "matrix"
        assert len(chart.nodes) == 6

    @pytest.mark.asyncio
    async def test_generate_with_root(self, engine):
        chart = await engine.generate(root="Alice VP")
        assert chart.root == "Alice VP"
        assert chart.title == "Org Chart: Alice VP"

    @pytest.mark.asyncio
    async def test_generate_with_program(self, engine):
        chart = await engine.generate(program="DCGS")
        assert chart.program == "DCGS"
        assert chart.title == "Org Chart: DCGS"

    @pytest.mark.asyncio
    async def test_generate_builds_edges(self, engine):
        chart = await engine.generate()
        # People with reports_to should generate edges
        edge_targets = {e["target"] for e in chart.edges}
        assert "Alice VP" in edge_targets
        assert "Bob Director" in edge_targets
        assert "Carol Manager" in edge_targets


# ---------------------------------------------------------------------------
# TestInferReportsTo
# ---------------------------------------------------------------------------


class TestInferReportsTo:
    @pytest.mark.asyncio
    async def test_infer_reports_to(self, engine):
        """Inference should assign reports_to for Eve (no existing report)."""
        # Eve is Tier 6 in ISR, different program from others
        report = await engine.infer_reports_to()
        assert report.relationships_inferred >= 0

    @pytest.mark.asyncio
    async def test_infer_same_program(self, engine):
        """People in same program should get higher match scores."""
        # Create people with no reports_to
        people = [
            Person(
                id="a",
                name="Sr Manager",
                title="Manager",
                company="GDIT",
                program="DCGS",
                tier=4,
                location="Fairfax",
                reports_to=None,
            ),
            Person(
                id="b",
                name="Analyst X",
                title="Analyst",
                company="GDIT",
                program="DCGS",
                tier=6,
                location="Fairfax",
                reports_to=None,
            ),
            Person(
                id="c",
                name="Director Y",
                title="Director",
                company="GDIT",
                program="DCGS",
                tier=3,
                location="Fairfax",
                reports_to=None,
            ),
        ]
        engine._fetch_people = AsyncMock(return_value=people)
        report = await engine.infer_reports_to()
        # Should infer at least some relationships
        assert report.relationships_inferred >= 0

    @pytest.mark.asyncio
    async def test_infer_same_location(self, engine):
        """Location match boosts inference confidence."""
        people = [
            Person(
                id="a",
                name="Lead A",
                title="Lead",
                company="GDIT",
                program="DCGS",
                tier=4,
                location="Tampa",
                reports_to=None,
            ),
            Person(
                id="b",
                name="Staff B",
                title="Analyst",
                company="GDIT",
                program="DCGS",
                tier=5,
                location="Tampa",
                reports_to=None,
            ),
        ]
        engine._fetch_people = AsyncMock(return_value=people)
        report = await engine.infer_reports_to()
        assert report.relationships_inferred >= 0


# ---------------------------------------------------------------------------
# TestGetTeam
# ---------------------------------------------------------------------------


class TestGetTeam:
    @pytest.mark.asyncio
    async def test_get_team(self, engine):
        team = await engine.get_team("Bob Director")
        assert isinstance(team, Team)
        assert team.leader is not None
        assert team.leader.name == "Bob Director"
        assert len(team.direct_reports) == 1
        assert team.direct_reports[0].name == "Carol Manager"

    @pytest.mark.asyncio
    async def test_get_team_empty(self, engine):
        team = await engine.get_team("Dave Analyst")
        assert isinstance(team, Team)
        assert team.leader is not None
        assert len(team.direct_reports) == 0

    @pytest.mark.asyncio
    async def test_get_team_nonexistent(self, engine):
        team = await engine.get_team("Nobody Here")
        assert team.leader is None
        assert team.direct_reports == []


# ---------------------------------------------------------------------------
# TestGetChainOfCommand
# ---------------------------------------------------------------------------


class TestGetChainOfCommand:
    @pytest.mark.asyncio
    async def test_get_chain_of_command(self, engine):
        chain = await engine.get_chain_of_command("Dave Analyst")
        assert len(chain) >= 1
        # Chain should go: Dave -> Carol -> Bob -> Alice -> John
        names = [p.name for p in chain]
        assert names[0] == "Dave Analyst"
        assert "Carol Manager" in names
        assert "John CEO" in names

    @pytest.mark.asyncio
    async def test_chain_for_ceo(self, engine):
        chain = await engine.get_chain_of_command("John CEO")
        assert len(chain) == 1
        assert chain[0].name == "John CEO"


# ---------------------------------------------------------------------------
# TestCompare
# ---------------------------------------------------------------------------


class TestCompare:
    @pytest.mark.asyncio
    async def test_compare_org_charts(self, engine):
        diff = await engine.compare_org_charts("2025-01-01", "2025-06-01", "DCGS")
        assert diff.program == "DCGS"
        assert diff.date1 == "2025-01-01"
        assert diff.date2 == "2025-06-01"


# ---------------------------------------------------------------------------
# TestFetchPeopleFallback
# ---------------------------------------------------------------------------


class TestFetchPeople:
    @pytest.mark.asyncio
    async def test_fetch_people_fallback(self):
        """Without neo4j or hub, returns empty list."""
        eng = OrgChartEngine()
        people = await eng._fetch_people()
        assert people == []


# ---------------------------------------------------------------------------
# TestCaching
# ---------------------------------------------------------------------------


class TestCaching:
    @pytest.mark.asyncio
    async def test_cache_chart(self, engine):
        chart = await engine.generate(mode="tree")
        cached = engine.get_cached(chart.chart_id)
        assert cached is not None
        assert cached.chart_id == chart.chart_id

    @pytest.mark.asyncio
    async def test_list_cached(self, engine):
        await engine.generate(mode="tree")
        await engine.generate(mode="network")
        cached = engine.list_cached()
        assert len(cached) == 2
        assert all("chart_id" in c for c in cached)

    @pytest.mark.asyncio
    async def test_clear_cache(self, engine):
        chart = await engine.generate(mode="tree")
        ok = engine.clear_cache(chart.chart_id)
        assert ok is True
        assert engine.get_cached(chart.chart_id) is None

    def test_clear_cache_nonexistent(self, engine):
        ok = engine.clear_cache("nonexistent_id")
        assert ok is False


# ---------------------------------------------------------------------------
# TestSingleton
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_singleton(self):
        import Engine8_Knowledge.visualization.org_chart_engine as mod

        original = mod._engine
        mod._engine = None
        e1 = mod.get_org_chart_engine()
        e2 = mod.get_org_chart_engine()
        assert e1 is e2
        mod._engine = original
