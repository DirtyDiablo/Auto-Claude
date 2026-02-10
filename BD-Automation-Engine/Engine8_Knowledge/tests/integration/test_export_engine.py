"""
Phase 27A — Export Engine Tests

Tests ExportEngine: SVG, PNG, PDF, DOCX, JSON, Mermaid exports.
Mocks Playwright and python-docx — no browser or Office tools required.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.visualization.export_engine import ExportEngine
from Engine8_Knowledge.visualization.org_chart_engine import OrgChart, Person


# ---------------------------------------------------------------------------
# Fixture Data
# ---------------------------------------------------------------------------


def make_chart() -> OrgChart:
    return OrgChart(
        chart_id="export_test",
        title="Export Test Org",
        mode="tree",
        nodes=[
            Person(name="Alice VP", title="VP", tier=2, company="GDIT", reports_to=None),
            Person(name="Bob Director", title="Director", tier=3, company="GDIT", reports_to="Alice VP"),
            Person(name="Carol Manager", title="Manager", tier=4, company="GDIT", reports_to="Bob Director"),
        ],
        edges=[
            {"source": "Alice VP", "target": "Bob Director", "type": "REPORTS_TO"},
            {"source": "Bob Director", "target": "Carol Manager", "type": "REPORTS_TO"},
        ],
        depth=3,
        generated_at="2025-01-01T00:00:00",
    )


SAMPLE_HTML_WITH_SVG = """<!DOCTYPE html>
<html><head></head><body>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
<rect x="10" y="10" width="100" height="50" fill="#fff"/>
<text x="20" y="35">Alice VP</text>
</svg>
</body></html>"""

SAMPLE_HTML_NO_SVG = """<!DOCTYPE html>
<html><head></head><body>
<div>No SVG here</div>
</body></html>"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def exporter():
    return ExportEngine()


@pytest.fixture
def chart():
    return make_chart()


# ---------------------------------------------------------------------------
# TestToSVG
# ---------------------------------------------------------------------------


class TestToSVG:
    @pytest.mark.asyncio
    async def test_to_svg(self, exporter):
        result = await exporter.to_svg(SAMPLE_HTML_WITH_SVG)
        assert isinstance(result, bytes)
        assert b"<svg" in result
        assert b"Alice VP" in result

    @pytest.mark.asyncio
    async def test_to_svg_no_svg_in_html(self, exporter):
        result = await exporter.to_svg(SAMPLE_HTML_NO_SVG)
        assert isinstance(result, bytes)
        assert b"<svg" in result  # Fallback SVG
        assert b"No SVG content" in result

    @pytest.mark.asyncio
    async def test_to_svg_valid_xml(self, exporter):
        result = await exporter.to_svg(SAMPLE_HTML_WITH_SVG)
        text = result.decode("utf-8")
        assert text.startswith("<?xml version=")


# ---------------------------------------------------------------------------
# TestToPNG
# ---------------------------------------------------------------------------


class TestToPNG:
    @pytest.mark.asyncio
    async def test_to_png_no_playwright(self, exporter):
        """Without Playwright, returns empty bytes."""
        with patch.dict("sys.modules", {"playwright": None, "playwright.async_api": None}):
            result = await exporter.to_png(SAMPLE_HTML_WITH_SVG)
        assert isinstance(result, bytes)
        assert result == b""


# ---------------------------------------------------------------------------
# TestToPDF
# ---------------------------------------------------------------------------


class TestToPDF:
    @pytest.mark.asyncio
    async def test_to_pdf_no_playwright(self, exporter):
        """Without Playwright, returns empty bytes."""
        with patch.dict("sys.modules", {"playwright": None, "playwright.async_api": None}):
            result = await exporter.to_pdf(SAMPLE_HTML_WITH_SVG)
        assert isinstance(result, bytes)
        assert result == b""


# ---------------------------------------------------------------------------
# TestToDOCX
# ---------------------------------------------------------------------------


class TestToDOCX:
    @pytest.mark.asyncio
    async def test_to_docx_no_docx(self, exporter, chart):
        """Without python-docx, returns empty bytes."""
        with patch.dict("sys.modules", {"docx": None}):
            result = await exporter.to_docx(chart)
        assert isinstance(result, bytes)
        assert result == b""


# ---------------------------------------------------------------------------
# TestToJSON
# ---------------------------------------------------------------------------


class TestToJSON:
    @pytest.mark.asyncio
    async def test_to_json(self, exporter, chart):
        result = await exporter.to_json(chart)
        assert isinstance(result, dict)
        assert result["chart_id"] == "export_test"
        assert result["title"] == "Export Test Org"
        assert len(result["nodes"]) == 3
        assert len(result["edges"]) == 2
        assert result["nodes"][0]["name"] == "Alice VP"


# ---------------------------------------------------------------------------
# TestToMermaid
# ---------------------------------------------------------------------------


class TestToMermaid:
    @pytest.mark.asyncio
    async def test_to_mermaid(self, exporter, chart):
        result = await exporter.to_mermaid(chart)
        assert isinstance(result, str)
        assert result.startswith("graph TD")
        assert "Alice_VP" in result
        assert "Bob_Director" in result

    @pytest.mark.asyncio
    async def test_to_mermaid_with_edges(self, exporter, chart):
        result = await exporter.to_mermaid(chart)
        assert "-->" in result
        # Source -> Target edges
        assert "Alice_VP --> Bob_Director" in result
        assert "Bob_Director --> Carol_Manager" in result


# ---------------------------------------------------------------------------
# TestExportChain
# ---------------------------------------------------------------------------


class TestExportChain:
    @pytest.mark.asyncio
    async def test_export_chain(self, exporter, chart):
        """JSON and Mermaid should both work in sequence."""
        json_result = await exporter.to_json(chart)
        assert json_result["chart_id"] == "export_test"

        mermaid_result = await exporter.to_mermaid(chart)
        assert "graph TD" in mermaid_result

        # Both outputs are consistent
        assert len(json_result["nodes"]) == 3
        assert "Alice_VP" in mermaid_result
