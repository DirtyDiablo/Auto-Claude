"""
Phase 27A — D3.js Renderers Tests

Tests TreeRenderer, NetworkRenderer, MatrixRenderer: rendering with
various options, tier colors, empty data, highlight contacts.
No external dependencies — tests HTML output structure.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.visualization.renderers import (
    TreeRenderer,
    NetworkRenderer,
    MatrixRenderer,
    RenderOptions,
    TIER_COLORS,
)
from Engine8_Knowledge.visualization.org_chart_engine import OrgChart, Person


# ---------------------------------------------------------------------------
# Fixture Data
# ---------------------------------------------------------------------------


def make_chart(nodes=None, edges=None) -> OrgChart:
    """Build a test OrgChart."""
    default_nodes = [
        Person(name="John CEO", title="CEO", tier=1, company="GDIT", reports_to=None),
        Person(name="Alice VP", title="VP", tier=2, company="GDIT", reports_to="John CEO"),
        Person(name="Bob Director", title="Director", tier=3, company="GDIT", reports_to="Alice VP"),
    ]
    default_edges = [
        {"source": "John CEO", "target": "Alice VP", "type": "REPORTS_TO"},
        {"source": "Alice VP", "target": "Bob Director", "type": "REPORTS_TO"},
    ]
    return OrgChart(
        chart_id="test_chart",
        title="Test Org",
        mode="tree",
        nodes=nodes or default_nodes,
        edges=edges or default_edges,
        depth=3,
        generated_at="2025-01-01T00:00:00",
    )


def make_empty_chart() -> OrgChart:
    return OrgChart(
        chart_id="empty_chart",
        title="Empty Org",
        mode="tree",
        nodes=[],
        edges=[],
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def chart():
    return make_chart()


@pytest.fixture
def empty_chart():
    return make_empty_chart()


@pytest.fixture
def tree():
    return TreeRenderer()


@pytest.fixture
def network():
    return NetworkRenderer()


@pytest.fixture
def matrix():
    return MatrixRenderer()


# ---------------------------------------------------------------------------
# TestTreeRenderer
# ---------------------------------------------------------------------------


class TestTreeRenderer:
    @pytest.mark.asyncio
    async def test_tree_render(self, tree, chart):
        html = await tree.render(chart)
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
        assert "d3.v7.min.js" in html
        assert "John CEO" in html
        assert "Alice VP" in html

    @pytest.mark.asyncio
    async def test_tree_with_options(self, tree, chart):
        opts = RenderOptions(
            width=1600,
            height=1000,
            title="Custom Title",
            show_emails=False,
        )
        html = await tree.render(chart, options=opts)
        assert "Custom Title" in html
        assert "1600" in html
        assert "1000" in html

    @pytest.mark.asyncio
    async def test_tree_tier_colors(self, tree, chart):
        html = await tree.render(chart)
        # Tier 1 color (red) should be in the data
        assert TIER_COLORS[1] in html  # #dc2626
        assert TIER_COLORS[2] in html  # #ea580c

    @pytest.mark.asyncio
    async def test_tree_empty_chart(self, tree, empty_chart):
        html = await tree.render(empty_chart)
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    @pytest.mark.asyncio
    async def test_tree_highlight(self, tree, chart):
        opts = RenderOptions(highlight_contacts=["Alice VP"])
        html = await tree.render(chart, options=opts)
        assert "Alice VP" in html


# ---------------------------------------------------------------------------
# TestNetworkRenderer
# ---------------------------------------------------------------------------


class TestNetworkRenderer:
    @pytest.mark.asyncio
    async def test_network_render(self, network, chart):
        html = await network.render(chart)
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
        assert "d3.v7.min.js" in html
        assert "forceSimulation" in html
        assert "John CEO" in html

    @pytest.mark.asyncio
    async def test_network_with_options(self, network, chart):
        opts = RenderOptions(width=1000, height=600, title="Network View")
        html = await network.render(chart, options=opts)
        assert "Network View" in html
        assert "1000" in html

    @pytest.mark.asyncio
    async def test_network_empty(self, network, empty_chart):
        html = await network.render(empty_chart)
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html


# ---------------------------------------------------------------------------
# TestMatrixRenderer
# ---------------------------------------------------------------------------


class TestMatrixRenderer:
    @pytest.mark.asyncio
    async def test_matrix_render(self, matrix):
        data = [
            {"person": "Alice", "program": "DCGS"},
            {"person": "Alice", "program": "ISR"},
            {"person": "Bob", "program": "DCGS"},
        ]
        html = await matrix.render(
            dimension1="person",
            dimension2="program",
            data=data,
        )
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
        assert "Alice" in html
        assert "DCGS" in html

    @pytest.mark.asyncio
    async def test_matrix_dimensions(self, matrix):
        data = [
            {"company": "GDIT", "location": "San Diego"},
            {"company": "GDIT", "location": "Fairfax"},
            {"company": "Raytheon", "location": "San Diego"},
        ]
        html = await matrix.render(
            dimension1="company",
            dimension2="location",
            data=data,
        )
        assert "GDIT" in html
        assert "Raytheon" in html
        assert "San Diego" in html

    @pytest.mark.asyncio
    async def test_matrix_empty(self, matrix):
        html = await matrix.render(dimension1="person", dimension2="program", data=[])
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html


# ---------------------------------------------------------------------------
# TestRenderOptions
# ---------------------------------------------------------------------------


class TestRenderOptions:
    def test_render_options_defaults(self):
        opts = RenderOptions()
        assert opts.width == 1200
        assert opts.height == 800
        assert opts.show_photos is False
        assert opts.show_emails is True
        assert opts.color_by == "tier"
        assert opts.highlight_contacts == []
        assert opts.filter_program is None
        assert opts.title == "Org Chart"
