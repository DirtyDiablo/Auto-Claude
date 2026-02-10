"""
Phase 21A — Cypher Query Library Tests

Tests the 12 pre-built Cypher queries in GraphQueries.
Uses mocking — does not require running Neo4j instance.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.graph.queries import GraphQueries, get_graph_queries


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_mgr():
    mgr = MagicMock()
    mgr.run_query.return_value = []
    mgr.run_single.return_value = None
    mgr.get_node_count.return_value = 0
    mgr.get_relationship_count.return_value = 0
    return mgr


@pytest.fixture
def gq(mock_mgr):
    return GraphQueries(mock_mgr)


# ---------------------------------------------------------------------------
# TestContactsByProgram
# ---------------------------------------------------------------------------

class TestContactsByProgram:
    """Test find_contacts_by_program query."""

    def test_returns_list(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = [
            {"name": "Alice", "title": "PM", "tier": 1, "bd_priority": "High", "company": "Leidos", "email": "a@b.com", "phone": ""},
        ]
        results = gq.find_contacts_by_program("DCGS")
        assert len(results) == 1
        assert results[0]["name"] == "Alice"

    def test_passes_pattern_param(self, gq, mock_mgr):
        gq.find_contacts_by_program("DCGS")
        args = mock_mgr.run_query.call_args
        assert "(?i).*DCGS.*" in str(args)

    def test_empty_result(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = []
        results = gq.find_contacts_by_program("nonexistent")
        assert results == []


# ---------------------------------------------------------------------------
# TestShortestPath
# ---------------------------------------------------------------------------

class TestShortestPath:
    """Test find_shortest_path query."""

    def test_path_found(self, gq, mock_mgr):
        mock_mgr.run_single.return_value = {
            "path_nodes": [{"name": "Alice", "type": "Person"}, {"name": "Bob", "type": "Person"}],
            "path_rels": ["WORKS_AT"],
            "hops": 2,
        }
        result = gq.find_shortest_path("Alice", "Bob")
        assert result["found"] is True
        assert result["hops"] == 2
        assert len(result["path"]) == 2

    def test_path_not_found(self, gq, mock_mgr):
        mock_mgr.run_single.return_value = None
        result = gq.find_shortest_path("Alice", "Unknown")
        assert result["found"] is False
        assert result["hops"] == 0
        assert result["path"] == []

    def test_from_to_fields(self, gq, mock_mgr):
        mock_mgr.run_single.return_value = None
        result = gq.find_shortest_path("Alice", "Bob")
        assert result["from"] == "Alice"
        assert result["to"] == "Bob"


# ---------------------------------------------------------------------------
# TestIntroductionPath
# ---------------------------------------------------------------------------

class TestIntroductionPath:
    """Test find_introduction_path query."""

    def test_returns_list(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = [
            {"from_person": "PTS Employee", "to_person": "Target", "hops": 2, "path_names": ["PTS", "Middleman", "Target"]},
        ]
        results = gq.find_introduction_path("Target")
        assert len(results) == 1
        assert results[0]["hops"] == 2

    def test_empty_when_no_path(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = []
        results = gq.find_introduction_path("Isolated")
        assert results == []


# ---------------------------------------------------------------------------
# TestProgramOrgChart
# ---------------------------------------------------------------------------

class TestProgramOrgChart:
    """Test get_program_org_chart query."""

    def test_returns_structure(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = [{
            "program": "DCGS", "acronym": "DCGS", "prime": "NG", "agency": "Army",
            "managers": [{"name": "Jane", "title": "PM", "tier": 1, "role": "manager"}],
            "team": [{"name": "Bob", "title": "Eng", "tier": 3, "company": "Leidos", "role": "team"}],
        }]
        result = gq.get_program_org_chart("DCGS")
        assert result["program"] == "DCGS"
        assert len(result["managers"]) == 1
        assert len(result["team"]) == 1

    def test_empty_program(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = []
        result = gq.get_program_org_chart("nonexistent")
        assert result["program"] == "nonexistent"
        assert result["managers"] == []
        assert result["team"] == []


# ---------------------------------------------------------------------------
# TestCompanyNetwork
# ---------------------------------------------------------------------------

class TestCompanyNetwork:
    """Test get_company_network query."""

    def test_returns_data(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = [{
            "company": "Leidos", "type": "prime", "defense_prime": True,
            "programs": [{"name": "DCGS"}], "people": [{"name": "Alice"}],
            "subs": ["SAIC"], "program_count": 1, "people_count": 1,
        }]
        result = gq.get_company_network("Leidos")
        assert result["company"] == "Leidos"
        assert result["program_count"] == 1

    def test_company_not_found(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = []
        result = gq.get_company_network("fake")
        assert result["company"] == "fake"
        assert result["programs"] == []


# ---------------------------------------------------------------------------
# TestHiringSignals
# ---------------------------------------------------------------------------

class TestHiringSignals:
    """Test find_hiring_signals query."""

    def test_returns_list(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = [
            {"program": "DCGS", "acronym": "DCGS", "job_count": 15, "sample_titles": ["Eng", "PM"], "prime_contractor": "NG"},
        ]
        signals = gq.find_hiring_signals(30)
        assert len(signals) == 1
        assert signals[0]["job_count"] == 15

    def test_no_signals(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = []
        signals = gq.find_hiring_signals(7)
        assert signals == []


# ---------------------------------------------------------------------------
# TestInfluenceLeaders
# ---------------------------------------------------------------------------

class TestInfluenceLeaders:
    """Test find_influence_leaders query."""

    def test_returns_leaders(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = [
            {"name": "Alice", "title": "VP", "tier": 1, "company": "Leidos", "influence_score": 42, "relationships": 30, "interactions": 12},
        ]
        leaders = gq.find_influence_leaders("DCGS")
        assert len(leaders) == 1
        assert leaders[0]["influence_score"] == 42


# ---------------------------------------------------------------------------
# TestContact360
# ---------------------------------------------------------------------------

class TestContact360:
    """Test get_contact_360 query."""

    def test_found(self, gq, mock_mgr):
        mock_mgr.run_single.return_value = {
            "name": "Alice", "title": "PM", "tier": 1, "bd_priority": "High",
            "email": "alice@test.com", "phone": "", "linkedin": "",
            "company": "Leidos", "programs": ["DCGS"],
            "interaction_count": 5, "recent_interactions": [], "connections": [],
        }
        result = gq.get_contact_360("Alice")
        assert result["found"] is True
        assert result["name"] == "Alice"

    def test_not_found(self, gq, mock_mgr):
        mock_mgr.run_single.return_value = None
        result = gq.get_contact_360("Nobody")
        assert result["found"] is False


# ---------------------------------------------------------------------------
# TestCompetitiveOverlap
# ---------------------------------------------------------------------------

class TestCompetitiveOverlap:
    """Test find_competitive_overlap query."""

    def test_overlap_found(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = [
            {"program": "DCGS", "acronym": "DCGS", "value": "$950M", "agency": "Army"},
        ]
        result = gq.find_competitive_overlap("Leidos", "SAIC")
        assert result["company_a"] == "Leidos"
        assert result["company_b"] == "SAIC"
        assert result["overlap_count"] == 1

    def test_no_overlap(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = []
        result = gq.find_competitive_overlap("A", "B")
        assert result["overlap_count"] == 0


# ---------------------------------------------------------------------------
# TestLocationIntel
# ---------------------------------------------------------------------------

class TestLocationIntel:
    """Test get_location_intel query."""

    def test_location_found(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = [{
            "location": "Fort Meade", "city": "Fort Meade", "state": "MD",
            "lat": 39.1, "lon": -76.7,
            "programs": [{"name": "DCGS"}], "people": [], "jobs": [],
            "program_count": 1, "people_count": 0, "job_count": 0,
        }]
        result = gq.get_location_intel("Fort Meade")
        assert result["location"] == "Fort Meade"
        assert result["program_count"] == 1

    def test_location_not_found(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = []
        result = gq.get_location_intel("Unknown")
        assert result["location"] == "Unknown"
        assert result["programs"] == []


# ---------------------------------------------------------------------------
# TestOrphanContacts
# ---------------------------------------------------------------------------

class TestOrphanContacts:
    """Test find_orphan_contacts query."""

    def test_returns_orphans(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = [
            {"name": "Orphan", "title": "Analyst", "company": "Unknown", "tier": 5, "email": "orphan@test.com"},
        ]
        orphans = gq.find_orphan_contacts()
        assert len(orphans) == 1

    def test_no_orphans(self, gq, mock_mgr):
        mock_mgr.run_query.return_value = []
        orphans = gq.find_orphan_contacts()
        assert orphans == []


# ---------------------------------------------------------------------------
# TestGraphStats
# ---------------------------------------------------------------------------

class TestGraphStats:
    """Test get_graph_stats query."""

    def test_returns_structure(self, gq, mock_mgr):
        mock_mgr.get_node_count.return_value = 100
        mock_mgr.get_relationship_count.return_value = 50
        stats = gq.get_graph_stats()
        assert "total_nodes" in stats
        assert "total_relationships" in stats
        assert "node_counts" in stats
        assert "relationship_counts" in stats
        assert "density" in stats

    def test_node_counts_all_labels(self, gq, mock_mgr):
        mock_mgr.get_node_count.return_value = 10
        stats = gq.get_graph_stats()
        assert len(stats["node_counts"]) == 7  # 7 node types
        assert mock_mgr.get_node_count.call_count == 7

    def test_density_calculation(self, gq, mock_mgr):
        mock_mgr.get_node_count.return_value = 100
        mock_mgr.get_relationship_count.return_value = 50
        stats = gq.get_graph_stats()
        # total_nodes = 7 * 100 = 700, density = total_rels / total_nodes
        assert stats["density"] > 0


# ---------------------------------------------------------------------------
# TestSingleton
# ---------------------------------------------------------------------------

class TestGraphQueriesSingleton:
    """Test singleton factory."""

    def test_get_graph_queries_returns_instance(self):
        import Engine8_Knowledge.graph.queries as mod
        mod._instance = None
        with patch("Engine8_Knowledge.graph.queries.get_neo4j_manager") as mock_get:
            mock_get.return_value = MagicMock()
            gq = mod.get_graph_queries()
            assert gq is not None
            gq2 = mod.get_graph_queries()
            assert gq is gq2
        mod._instance = None  # cleanup
