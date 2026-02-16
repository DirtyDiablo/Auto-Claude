"""
Phase 21A — Graph Schema Tests

Tests schema definitions, constraint application, and index creation.
"""

from unittest.mock import MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.graph.schema import (
    NODE_TYPES,
    RELATIONSHIP_TYPES,
    CONSTRAINTS,
    INDEXES,
    FULLTEXT_INDEXES,
    apply_schema,
    get_schema_info,
)


class TestSchemaDefinitions:
    """Test schema type definitions."""

    def test_seven_node_types(self):
        assert len(NODE_TYPES) == 7
        expected = {
            "Person",
            "Company",
            "Program",
            "Job",
            "Contract",
            "Location",
            "Interaction",
        }
        assert set(NODE_TYPES.keys()) == expected

    def test_person_has_required_properties(self):
        props = NODE_TYPES["Person"]["properties"]
        assert "name" in props
        assert "title" in props
        assert "tier" in props
        assert "email" in props

    def test_program_has_required_properties(self):
        props = NODE_TYPES["Program"]["properties"]
        assert "name" in props
        assert "acronym" in props
        assert "prime_contractor" in props

    def test_twenty_plus_relationship_types(self):
        assert len(RELATIONSHIP_TYPES) >= 20

    def test_relationship_types_have_from_to(self):
        for name, rel in RELATIONSHIP_TYPES.items():
            assert "from" in rel, f"{name} missing 'from'"
            assert "to" in rel, f"{name} missing 'to'"

    def test_key_relationships_exist(self):
        assert "WORKS_AT" in RELATIONSHIP_TYPES
        assert "PRIMES_ON" in RELATIONSHIP_TYPES
        assert "MANAGES" in RELATIONSHIP_TYPES
        assert "POSTED_BY" in RELATIONSHIP_TYPES
        assert "MAPPED_TO" in RELATIONSHIP_TYPES
        assert "BETWEEN" in RELATIONSHIP_TYPES

    def test_constraints_not_empty(self):
        assert len(CONSTRAINTS) >= 3

    def test_indexes_not_empty(self):
        assert len(INDEXES) >= 8

    def test_fulltext_indexes_exist(self):
        assert len(FULLTEXT_INDEXES) >= 2


class TestApplySchema:
    """Test schema application."""

    def test_apply_schema_success(self):
        mock_mgr = MagicMock()
        mock_mgr.write_query.return_value = {}
        result = apply_schema(mock_mgr)
        assert "constraints" in result
        assert "indexes" in result
        assert "fulltext" in result
        assert "errors" in result
        # Should have called write_query for each constraint + index + fulltext
        total_calls = len(CONSTRAINTS) + len(INDEXES) + len(FULLTEXT_INDEXES)
        assert mock_mgr.write_query.call_count == total_calls

    def test_apply_schema_handles_existing(self):
        mock_mgr = MagicMock()
        mock_mgr.write_query.side_effect = Exception("already exists")
        result = apply_schema(mock_mgr)
        # Should not crash, errors are caught
        assert len(result["errors"]) == 0  # "already exists" is not treated as error

    def test_apply_schema_records_real_errors(self):
        mock_mgr = MagicMock()
        mock_mgr.write_query.side_effect = Exception("syntax error in Cypher")
        result = apply_schema(mock_mgr)
        assert len(result["errors"]) > 0


class TestGetSchemaInfo:
    """Test schema info retrieval."""

    def test_get_schema_info_returns_structure(self):
        mock_mgr = MagicMock()
        mock_mgr.run_query.return_value = []
        result = get_schema_info(mock_mgr)
        assert "node_types" in result
        assert "relationship_types" in result
        assert len(result["node_types"]) == 7

    def test_get_schema_info_handles_error(self):
        mock_mgr = MagicMock()
        mock_mgr.run_query.side_effect = Exception("not connected")
        result = get_schema_info(mock_mgr)
        assert "error" in result
