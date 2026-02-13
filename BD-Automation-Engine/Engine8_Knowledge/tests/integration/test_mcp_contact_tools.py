"""
Phase 26A — MCP Contact Tools Tests

Tests 5 contact tools: search_contacts, get_contact_360, classify_contact,
find_introduction_path, get_org_chart.
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

    # search_contacts
    hub.get = AsyncMock(return_value={
        "contacts": [
            {"name": "Alice Smith", "title": "Program Manager", "tier": 2, "program": "DCGS"},
            {"name": "Bob Jones", "title": "Senior Analyst", "tier": 4, "program": "DCGS"},
        ],
        "total": 2,
    })

    # post responses
    hub.post = AsyncMock(return_value={
        "name": "New Contact",
        "title": "Director",
        "tier": 3,
        "classification": "api",
    })
    return hub


@pytest.fixture
def mock_mcp():
    """Mock FastMCP instance that captures tool registrations."""
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
    from Engine8_Knowledge.mcp.contact_tools import register_contact_tools
    count = register_contact_tools(mock_mcp, mock_hub)
    return mock_mcp._registered, count


# ---------------------------------------------------------------------------
# TestSearchContacts
# ---------------------------------------------------------------------------


class TestSearchContacts:
    @pytest.mark.asyncio
    async def test_search_contacts(self, tools, mock_hub):
        fns, count = tools
        result = await fns["search_contacts"]("DCGS analyst")
        assert len(result) == 2
        assert result[0]["name"] == "Alice Smith"
        mock_hub.get.assert_called()

    @pytest.mark.asyncio
    async def test_search_empty(self, tools, mock_hub):
        mock_hub.get = AsyncMock(return_value={"contacts": [], "total": 0})
        fns, _ = tools
        result = await fns["search_contacts"]("nonexistent person")
        assert result == []


# ---------------------------------------------------------------------------
# TestGetContact360
# ---------------------------------------------------------------------------


class TestGetContact360:
    @pytest.mark.asyncio
    async def test_get_contact_360(self, tools, mock_hub):
        fns, _ = tools
        # get_contact_360 makes 3 hub.get calls
        mock_hub.get = AsyncMock(side_effect=[
            {"contacts": [{"name": "Alice", "title": "PM", "tier": 2}], "total": 1},
            {"interactions": [{"type": "call"}]},
            {"position": "reports_to: VP"},
        ])
        result = await fns["get_contact_360"]("Alice Smith")
        assert "contact" in result
        assert "memory" in result
        assert "graph_position" in result


# ---------------------------------------------------------------------------
# TestClassifyContact
# ---------------------------------------------------------------------------


class TestClassifyContact:
    @pytest.mark.asyncio
    async def test_classify_contact(self, tools, mock_hub):
        fns, _ = tools
        result = await fns["classify_contact"]("John Doe", "Manager", "San Diego")
        assert "tier" in result

    @pytest.mark.asyncio
    async def test_classify_contact_executive(self, tools, mock_hub):
        """Fallback classification for executive titles."""
        mock_hub.post = AsyncMock(return_value={})
        fns, _ = tools
        result = await fns["classify_contact"]("CEO Person", "CEO", "DC")
        assert result["tier"] == 1

    @pytest.mark.asyncio
    async def test_classify_fallback(self, tools, mock_hub):
        """Fallback for non-executive titles."""
        mock_hub.post = AsyncMock(return_value={})
        fns, _ = tools
        result = await fns["classify_contact"]("Jane Doe", "Analyst III", "Tampa")
        assert result["tier"] == 5
        assert result["classification"] == "auto"


# ---------------------------------------------------------------------------
# TestFindIntroductionPath
# ---------------------------------------------------------------------------


class TestFindIntroductionPath:
    @pytest.mark.asyncio
    async def test_find_introduction_path(self, tools, mock_hub):
        mock_hub.get = AsyncMock(return_value={
            "from": "Alice",
            "to": "Bob",
            "path": ["Alice", "Carol", "Bob"],
            "hops": 2,
        })
        fns, _ = tools
        result = await fns["find_introduction_path"]("Alice", "Bob")
        assert result["hops"] == 2
        assert len(result["path"]) == 3


# ---------------------------------------------------------------------------
# TestGetOrgChart
# ---------------------------------------------------------------------------


class TestGetOrgChart:
    @pytest.mark.asyncio
    async def test_get_org_chart_text(self, tools, mock_hub):
        mock_hub.post = AsyncMock(return_value={
            "nodes": [
                {"name": "Alice", "title": "VP", "reports_to": ""},
                {"name": "Bob", "title": "Manager", "reports_to": "Alice"},
            ],
        })
        fns, _ = tools
        result = await fns["get_org_chart"]("DCGS", "text")
        assert "nodes" in result
        assert result["format"] == "text"

    @pytest.mark.asyncio
    async def test_get_org_chart_mermaid(self, tools, mock_hub):
        mock_hub.post = AsyncMock(return_value={
            "nodes": [
                {"name": "Alice", "title": "VP", "reports_to": ""},
                {"name": "Bob", "title": "Manager", "reports_to": "Alice"},
            ],
        })
        fns, _ = tools
        result = await fns["get_org_chart"]("DCGS", "mermaid")
        assert "mermaid" in result
        assert "graph TD" in result["mermaid"]
        assert "Alice" in result["mermaid"]


# ---------------------------------------------------------------------------
# TestRegisterCount
# ---------------------------------------------------------------------------


class TestRegisterCount:
    def test_register_count(self, tools):
        _, count = tools
        assert count == 5
