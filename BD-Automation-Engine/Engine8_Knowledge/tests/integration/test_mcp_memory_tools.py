"""
Phase 26A — MCP Memory & Intelligence Tools Tests

Tests 5 memory tools: recall_memory, add_memory, search_knowledge_base,
get_interaction_history, generate_outreach.
Mocks the hub client — no network access required.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_hub():
    hub = AsyncMock()

    # Default GET response
    hub.get = AsyncMock(return_value={
        "contacts": [
            {"name": "Alice Smith", "title": "Program Manager", "company": "GDIT",
             "program": "DCGS", "tier": 2},
        ],
        "total": 1,
    })

    # Default POST response
    hub.post = AsyncMock(return_value={
        "results": {
            "episodic": [{"content": "DCGS meeting notes", "score": 0.8, "id": "m1"}],
            "procedural": [{"content": "Cold email pattern", "score": 0.7, "id": "m2"}],
        },
        "total_results": 2,
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
    from Engine8_Knowledge.mcp.memory_tools import register_memory_tools
    count = register_memory_tools(mock_mcp, mock_hub)
    return mock_mcp._registered, count


# ---------------------------------------------------------------------------
# TestRecallMemory
# ---------------------------------------------------------------------------


class TestRecallMemory:
    @pytest.mark.asyncio
    async def test_recall_memory(self, tools, mock_hub):
        fns, _ = tools
        result = await fns["recall_memory"]("DCGS contacts")
        assert isinstance(result, list)
        assert len(result) >= 1
        mock_hub.post.assert_called()

    @pytest.mark.asyncio
    async def test_recall_with_contact(self, tools, mock_hub):
        fns, _ = tools
        result = await fns["recall_memory"]("meeting notes", contact_id="alice_id")
        # Should include user_id in the request body
        call_args = mock_hub.post.call_args
        body = call_args.kwargs.get("json", call_args.args[1] if len(call_args.args) > 1 else {})
        assert body.get("user_id") == "alice_id"


# ---------------------------------------------------------------------------
# TestAddMemory
# ---------------------------------------------------------------------------


class TestAddMemory:
    @pytest.mark.asyncio
    async def test_add_memory(self, tools, mock_hub):
        mock_hub.post = AsyncMock(return_value={"memory_id": "mem_new_123", "layer": "auto"})
        fns, _ = tools
        result = await fns["add_memory"]("Important DCGS insight", "insight")
        assert "memory_id" in result

    @pytest.mark.asyncio
    async def test_add_with_contact(self, tools, mock_hub):
        mock_hub.post = AsyncMock(return_value={"memory_id": "mem_c_456", "layer": "auto"})
        fns, _ = tools
        result = await fns["add_memory"](
            "Alice prefers email",
            memory_type="preference",
            contact_id="alice_id",
        )
        call_args = mock_hub.post.call_args
        body = call_args.kwargs.get("json", call_args.args[1] if len(call_args.args) > 1 else {})
        assert body.get("contact_id") == "alice_id"
        assert body.get("user_id") == "alice_id"


# ---------------------------------------------------------------------------
# TestSearchKnowledgeBase
# ---------------------------------------------------------------------------


class TestSearchKnowledgeBase:
    @pytest.mark.asyncio
    async def test_search_knowledge_base(self, tools, mock_hub):
        mock_hub.post = AsyncMock(return_value={
            "results": [
                {"id": "d1", "content": "DCGS architecture doc", "metadata": {"tag": "architecture"}},
                {"id": "d2", "content": "ISR brief", "metadata": {"tag": "brief"}},
            ],
        })
        fns, _ = tools
        result = await fns["search_knowledge_base"]("DCGS architecture")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_knowledge_with_tags(self, tools, mock_hub):
        mock_hub.post = AsyncMock(return_value={
            "results": [
                {"id": "d1", "content": "DCGS doc", "metadata": {"tag": "architecture"}},
                {"id": "d2", "content": "ISR brief", "metadata": {"tag": "brief"}},
            ],
        })
        fns, _ = tools
        result = await fns["search_knowledge_base"](
            "defense docs",
            tags=["architecture"],
        )
        # Should filter to only matching tags
        assert len(result) >= 1
        assert any("architecture" in str(r.get("metadata", {})) for r in result)


# ---------------------------------------------------------------------------
# TestGetInteractionHistory
# ---------------------------------------------------------------------------


class TestGetInteractionHistory:
    @pytest.mark.asyncio
    async def test_get_interaction_history(self, tools, mock_hub):
        mock_hub.get = AsyncMock(return_value={
            "interactions": [
                {"type": "call", "summary": "Discussed DCGS", "date": "2025-01-15"},
                {"type": "email", "summary": "Follow up", "date": "2025-01-20"},
            ],
        })
        fns, _ = tools
        result = await fns["get_interaction_history"]("Alice Smith")
        assert len(result) == 2
        assert result[0]["type"] == "call"


# ---------------------------------------------------------------------------
# TestGenerateOutreach
# ---------------------------------------------------------------------------


class TestGenerateOutreach:
    @pytest.mark.asyncio
    async def test_generate_outreach_email(self, tools, mock_hub):
        mock_hub.get = AsyncMock(side_effect=[
            {"contacts": [{"name": "Alice Smith", "title": "PM", "company": "GDIT",
                           "program": "DCGS"}], "total": 1},
            {"interactions": [{"type": "call"}]},
        ])
        fns, _ = tools
        result = await fns["generate_outreach"]("Alice Smith", "email")
        assert result["channel"] == "email"
        assert "subject" in result
        assert "body" in result
        assert "Alice" in result["body"]

    @pytest.mark.asyncio
    async def test_generate_outreach_linkedin(self, tools, mock_hub):
        mock_hub.get = AsyncMock(side_effect=[
            {"contacts": [{"name": "Bob Jones", "title": "Director", "company": "Raytheon",
                           "program": "GBSD"}], "total": 1},
            {"interactions": []},
        ])
        fns, _ = tools
        result = await fns["generate_outreach"]("Bob Jones", "linkedin")
        assert result["channel"] == "linkedin"
        assert "body" in result
        assert "Bob" in result["body"]


# ---------------------------------------------------------------------------
# TestRegisterCount
# ---------------------------------------------------------------------------


class TestRegisterCount:
    def test_register_count(self, tools):
        _, count = tools
        assert count == 5
