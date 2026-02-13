"""
Phase 22A — Graph Retriever Tests

Tests entity lookup, context expansion, formatting, and retrieval.
Uses mocking — does not require running Neo4j.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.search.graph_retriever import (
    GraphRetriever, GraphResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_mgr():
    mgr = MagicMock()
    mgr.run_query.return_value = []
    mgr.run_single.return_value = None
    return mgr


@pytest.fixture
def retriever(mock_mgr):
    return GraphRetriever(neo4j_manager=mock_mgr)


# ---------------------------------------------------------------------------
# TestEntityLookup
# ---------------------------------------------------------------------------

class TestEntityLookup:
    """Test entity lookup."""

    def test_lookup_by_name(self, retriever, mock_mgr):
        mock_mgr.run_query.return_value = [
            {"name": "Alice Smith", "type": "Person", "props": {"title": "PM", "company": "Leidos"}},
        ]
        results = retriever.entity_lookup("Alice")
        assert len(results) == 1
        assert results[0]["name"] == "Alice Smith"
        assert results[0]["type"] == "Person"

    def test_lookup_with_type(self, retriever, mock_mgr):
        mock_mgr.run_query.return_value = [
            {"name": "Leidos", "type": "Company", "props": {}},
        ]
        results = retriever.entity_lookup("Leidos", "Company")
        assert len(results) == 1

    def test_lookup_no_results(self, retriever, mock_mgr):
        mock_mgr.run_query.return_value = []
        results = retriever.entity_lookup("Nonexistent")
        assert results == []

    def test_lookup_error_handled(self, retriever, mock_mgr):
        mock_mgr.run_query.side_effect = Exception("connection error")
        results = retriever.entity_lookup("Alice")
        assert results == []


# ---------------------------------------------------------------------------
# TestExpandContext
# ---------------------------------------------------------------------------

class TestExpandContext:
    """Test context expansion."""

    def test_expand_returns_relationships(self, retriever, mock_mgr):
        mock_mgr.run_query.return_value = [
            {
                "connected_name": "Leidos",
                "connected_type": "Company",
                "rel_types": ["WORKS_AT"],
                "props": {"name": "Leidos"},
            },
        ]
        ctx = retriever.expand_context("Alice", "Person", depth=2)
        assert len(ctx["relationships"]) == 1
        assert ctx["relationships"][0]["target"] == "Leidos"

    def test_expand_empty(self, retriever, mock_mgr):
        mock_mgr.run_query.return_value = []
        ctx = retriever.expand_context("Unknown", "Person")
        assert ctx["relationships"] == []
        assert ctx["connected"] == []

    def test_expand_error(self, retriever, mock_mgr):
        mock_mgr.run_query.side_effect = Exception("timeout")
        ctx = retriever.expand_context("Alice", "Person")
        assert ctx["relationships"] == []


# ---------------------------------------------------------------------------
# TestProgramContext
# ---------------------------------------------------------------------------

class TestProgramContext:
    """Test program context retrieval."""

    def test_program_found(self, retriever, mock_mgr):
        mock_mgr.run_single.return_value = {
            "name": "DCGS", "acronym": "DCGS", "value": "$950M",
            "agency": "Army", "primes": ["Northrop"], "managers": [],
            "job_count": 15,
        }
        result = retriever.program_context("DCGS")
        assert result["name"] == "DCGS"
        assert result["job_count"] == 15

    def test_program_not_found(self, retriever, mock_mgr):
        mock_mgr.run_single.return_value = None
        result = retriever.program_context("Unknown")
        assert result.get("found") is False


# ---------------------------------------------------------------------------
# TestContactContext
# ---------------------------------------------------------------------------

class TestContactContext:
    """Test contact context retrieval."""

    def test_contact_found(self, retriever, mock_mgr):
        mock_mgr.run_single.return_value = {
            "name": "Alice", "title": "PM", "tier": 1,
            "email": "a@b.com", "company": "Leidos",
            "programs": ["DCGS"], "interaction_count": 5,
            "connections": [],
        }
        result = retriever.contact_context("Alice")
        assert result["name"] == "Alice"

    def test_contact_not_found(self, retriever, mock_mgr):
        mock_mgr.run_single.return_value = None
        result = retriever.contact_context("Nobody")
        assert result.get("found") is False


# ---------------------------------------------------------------------------
# TestRelationshipContext
# ---------------------------------------------------------------------------

class TestRelationshipContext:
    """Test relationship path retrieval."""

    def test_path_found(self, retriever, mock_mgr):
        mock_mgr.run_single.return_value = {
            "path_names": ["Alice", "Leidos", "Bob"],
            "path_rels": ["WORKS_AT", "WORKS_AT"],
            "hops": 2,
        }
        result = retriever.relationship_context("Alice", "Bob")
        assert result["found"] is True
        assert result["hops"] == 2

    def test_path_not_found(self, retriever, mock_mgr):
        mock_mgr.run_single.return_value = None
        result = retriever.relationship_context("Alice", "Unknown")
        assert result["found"] is False


# ---------------------------------------------------------------------------
# TestRetrieve
# ---------------------------------------------------------------------------

class TestRetrieve:
    """Test main retrieve method."""

    def test_retrieve_with_entities(self, retriever, mock_mgr):
        # entity_lookup returns results
        mock_mgr.run_query.side_effect = [
            # entity lookup
            [{"name": "Alice Smith", "type": "Person", "props": {"title": "PM"}}],
            # expand context
            [{"connected_name": "Leidos", "connected_type": "Company", "rel_types": ["WORKS_AT"], "props": {}}],
        ]
        results = retriever.retrieve("Tell me about Alice Smith")
        assert len(results) >= 1
        assert isinstance(results[0], GraphResult)

    def test_retrieve_no_entities(self, retriever, mock_mgr):
        # All lookups return empty → fallback to fulltext
        mock_mgr.run_query.return_value = []
        results = retriever.retrieve("some generic query")
        # May return empty since fulltext also returns empty
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# TestEntityExtraction
# ---------------------------------------------------------------------------

class TestEntityExtraction:
    """Test entity extraction heuristics."""

    def test_extract_capitalized_names(self, retriever):
        entities = retriever._extract_entities("Find John Smith at Northrop Grumman")
        assert "John Smith" in entities
        assert "Northrop Grumman" in entities

    def test_extract_acronyms(self, retriever):
        entities = retriever._extract_entities("What is the DCGS program?")
        assert "DCGS" in entities

    def test_extract_quoted(self, retriever):
        entities = retriever._extract_entities('Search for "Fort Meade" contacts')
        assert "Fort Meade" in entities

    def test_extract_empty(self, retriever):
        entities = retriever._extract_entities("hello world")
        assert isinstance(entities, list)


# ---------------------------------------------------------------------------
# TestFormatting
# ---------------------------------------------------------------------------

class TestFormatting:
    """Test context text formatting."""

    def test_format_person(self, retriever):
        entity = {"name": "Alice", "type": "Person", "title": "PM", "company": "Leidos"}
        context = {"relationships": [
            {"target": "DCGS", "target_type": "Program", "relationship": "MANAGES"},
        ], "connected": []}
        text = retriever._format_context_text(entity, context)
        assert "Alice" in text
        assert "PM" in text
        assert "Leidos" in text
        assert "MANAGES" in text

    def test_format_no_relationships(self, retriever):
        entity = {"name": "Bob", "type": "Person"}
        context = {"relationships": [], "connected": []}
        text = retriever._format_context_text(entity, context)
        assert "Bob" in text


# ---------------------------------------------------------------------------
# TestSingleton
# ---------------------------------------------------------------------------

class TestSingleton:
    """Test singleton factory."""

    def test_get_instance(self):
        import Engine8_Knowledge.search.graph_retriever as mod
        mod._instance = None
        with patch("Engine8_Knowledge.search.graph_retriever.get_neo4j_manager") as mock_get:
            mock_get.return_value = MagicMock()
            r = mod.get_graph_retriever()
            assert r is not None
        mod._instance = None
