"""
Tests for Engine8_Knowledge.graph.knowledge_graph — BDKnowledgeGraph.

Covers: entity CRUD, relationships, shortest path, community detection,
teaming partners, competitive landscape, stats, build from Qdrant mock,
search, persistence, and edge cases.

Run: python -m pytest tests/test_knowledge_graph.py -v --tb=short
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
from Engine8_Knowledge.graph.knowledge_graph import (
    ENTITY_TYPES,
    RELATIONSHIP_TYPES,
    BDKnowledgeGraph,
    _make_id,
    reset_graph,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset the module-level singleton before each test."""
    reset_graph()
    yield
    reset_graph()


@pytest.fixture
def graph():
    """Return a fresh BDKnowledgeGraph with no persistence and no LightRAG."""
    with patch.object(BDKnowledgeGraph, "_init_lightrag"):
        g = BDKnowledgeGraph(persist_path=None)
    return g


@pytest.fixture
def populated_graph(graph):
    """Graph pre-populated with a small defense BD network."""
    g = graph

    # Companies
    gdit = g.add_entity("GDIT", "COMPANY", {"size": "large"})
    leidos = g.add_entity("Leidos", "COMPANY", {"size": "large"})
    pts = g.add_entity("PTS", "COMPANY", {"size": "small"})
    ng = g.add_entity("Northrop Grumman", "COMPANY", {"size": "large"})

    # Programs
    dcgs = g.add_entity("DCGS-A", "PROGRAM", {"agency": "Army", "value": "$500M"})
    bices = g.add_entity("BICES", "PROGRAM", {"agency": "DIA"})

    # Persons
    alice = g.add_entity("Alice Smith", "PERSON", {"title": "VP"})
    bob = g.add_entity("Bob Jones", "PERSON", {"title": "PM"})

    # Agency
    army = g.add_entity("US Army", "AGENCY")

    # Installation
    langley = g.add_entity("Langley AFB", "INSTALLATION")

    # Relationships
    g.add_relationship(gdit, dcgs, "PRIMES", weight=1.0)
    g.add_relationship(pts, gdit, "SUBCONTRACTS", weight=0.8)
    g.add_relationship(leidos, dcgs, "COMPETES_WITH", weight=0.7)
    g.add_relationship(gdit, alice, "EMPLOYS", weight=1.0)
    g.add_relationship(alice, dcgs, "WORKS_ON", weight=0.9)
    g.add_relationship(dcgs, army, "AWARDED_BY", weight=1.0)
    g.add_relationship(dcgs, langley, "LOCATED_AT", weight=1.0)
    g.add_relationship(ng, bices, "PRIMES", weight=1.0)
    g.add_relationship(bob, bices, "WORKS_ON", weight=0.9)
    g.add_relationship(ng, bob, "EMPLOYS", weight=1.0)
    g.add_relationship(gdit, leidos, "COMPETES_WITH", weight=0.6)

    return g


# ===========================================================================
# 1. Entity add / get / search
# ===========================================================================


class TestEntityOperations:
    def test_add_entity_returns_id(self, graph):
        eid = graph.add_entity("GDIT", "COMPANY")
        assert isinstance(eid, str) and len(eid) == 16

    def test_deterministic_id(self, graph):
        id1 = graph.add_entity("GDIT", "COMPANY")
        id2 = graph.add_entity("GDIT", "COMPANY")
        assert id1 == id2

    def test_get_entity_fields(self, graph):
        eid = graph.add_entity("DCGS-A", "PROGRAM", {"agency": "Army"})
        entity = graph.get_entity(eid)
        assert entity is not None
        assert entity["name"] == "DCGS-A"
        assert entity["type"] == "PROGRAM"
        assert entity["metadata"]["agency"] == "Army"
        assert "relations" in entity

    def test_get_entity_not_found(self, graph):
        assert graph.get_entity("nonexistent") is None

    def test_add_entity_invalid_type(self, graph):
        with pytest.raises(ValueError, match="Unknown entity type"):
            graph.add_entity("Foo", "INVALID_TYPE")

    def test_add_entity_merges_metadata(self, graph):
        eid = graph.add_entity("GDIT", "COMPANY", {"size": "large"})
        graph.add_entity("GDIT", "COMPANY", {"revenue": "10B"})
        entity = graph.get_entity(eid)
        assert entity["metadata"]["size"] == "large"
        assert entity["metadata"]["revenue"] == "10B"

    def test_search_entities_by_name(self, populated_graph):
        results = populated_graph.search_entities("gdit")
        assert len(results) >= 1
        assert results[0]["name"] == "GDIT"

    def test_search_entities_partial_match(self, populated_graph):
        results = populated_graph.search_entities("Smith")
        assert len(results) == 1
        assert results[0]["name"] == "Alice Smith"

    def test_search_entities_with_type_filter(self, populated_graph):
        results = populated_graph.search_entities("A", entity_type="PROGRAM")
        names = [r["name"] for r in results]
        # Should only return PROGRAMs, not AGENCY or INSTALLATION
        for r in results:
            assert r["type"] == "PROGRAM"

    def test_search_entities_limit(self, populated_graph):
        results = populated_graph.search_entities("", limit=3)
        assert len(results) <= 3

    def test_search_entities_no_match(self, graph):
        results = graph.search_entities("zzzzz")
        assert results == []


# ===========================================================================
# 2. Relationship add / get / filter
# ===========================================================================


class TestRelationshipOperations:
    def test_add_relationship(self, graph):
        gdit = graph.add_entity("GDIT", "COMPANY")
        dcgs = graph.add_entity("DCGS-A", "PROGRAM")
        graph.add_relationship(gdit, dcgs, "PRIMES", weight=0.95)

        rels = graph.get_relationships(gdit)
        assert len(rels) == 1
        assert rels[0]["target"] == dcgs
        assert rels[0]["relation_type"] == "PRIMES"
        assert rels[0]["weight"] == 0.95

    def test_add_relationship_invalid_type(self, graph):
        a = graph.add_entity("A", "COMPANY")
        b = graph.add_entity("B", "COMPANY")
        with pytest.raises(ValueError, match="Unknown relation type"):
            graph.add_relationship(a, b, "INVALID_REL")

    def test_add_relationship_missing_source(self, graph):
        b = graph.add_entity("B", "COMPANY")
        with pytest.raises(ValueError, match="Source entity not found"):
            graph.add_relationship("missing_id", b, "PRIMES")

    def test_add_relationship_missing_target(self, graph):
        a = graph.add_entity("A", "COMPANY")
        with pytest.raises(ValueError, match="Target entity not found"):
            graph.add_relationship(a, "missing_id", "PRIMES")

    def test_duplicate_relationship_updates_weight(self, graph):
        a = graph.add_entity("A", "COMPANY")
        b = graph.add_entity("B", "PROGRAM")
        graph.add_relationship(a, b, "PRIMES", weight=0.5)
        graph.add_relationship(a, b, "PRIMES", weight=0.9)

        rels = graph.get_relationships(a)
        assert len(rels) == 1
        assert rels[0]["weight"] == 0.9

    def test_get_relationships_with_type_filter(self, populated_graph):
        gdit_id = populated_graph._resolve_name("GDIT")
        all_rels = populated_graph.get_relationships(gdit_id)
        primes_only = populated_graph.get_relationships(gdit_id, relation_type="PRIMES")
        assert len(primes_only) < len(all_rels)
        for r in primes_only:
            assert r["relation_type"] == "PRIMES"

    def test_get_relationships_empty(self, graph):
        assert graph.get_relationships("nonexistent") == []

    def test_self_loop(self, graph):
        a = graph.add_entity("SelfCo", "COMPANY")
        graph.add_relationship(a, a, "COMPETES_WITH")
        rels = graph.get_relationships(a)
        assert len(rels) == 1
        assert rels[0]["target"] == a


# ===========================================================================
# 3. Shortest path (BFS)
# ===========================================================================


class TestShortestPath:
    def test_direct_path(self, populated_graph):
        gdit_id = populated_graph._resolve_name("GDIT")
        dcgs_id = populated_graph._resolve_name("DCGS-A")
        path = populated_graph.shortest_path(gdit_id, dcgs_id)
        assert len(path) == 2
        assert path[0]["name"] == "GDIT"
        assert path[1]["name"] == "DCGS-A"

    def test_multi_hop_path(self, populated_graph):
        pts_id = populated_graph._resolve_name("PTS")
        dcgs_id = populated_graph._resolve_name("DCGS-A")
        path = populated_graph.shortest_path(pts_id, dcgs_id)
        # PTS -> GDIT -> DCGS-A
        assert len(path) == 3
        names = [n["name"] for n in path]
        assert names[0] == "PTS"
        assert names[-1] == "DCGS-A"

    def test_no_path(self, graph):
        a = graph.add_entity("Isolated1", "COMPANY")
        b = graph.add_entity("Isolated2", "COMPANY")
        path = graph.shortest_path(a, b)
        assert path == []

    def test_same_node(self, populated_graph):
        gdit_id = populated_graph._resolve_name("GDIT")
        path = populated_graph.shortest_path(gdit_id, gdit_id)
        assert len(path) == 1
        assert path[0]["name"] == "GDIT"

    def test_path_nonexistent_source(self, graph):
        a = graph.add_entity("A", "COMPANY")
        path = graph.shortest_path("nope", a)
        assert path == []

    def test_path_nonexistent_target(self, graph):
        a = graph.add_entity("A", "COMPANY")
        path = graph.shortest_path(a, "nope")
        assert path == []

    def test_max_depth_limits_search(self, populated_graph):
        # PTS -> GDIT -> DCGS-A requires 2 hops; max_depth=1 should fail
        pts_id = populated_graph._resolve_name("PTS")
        dcgs_id = populated_graph._resolve_name("DCGS-A")
        path = populated_graph.shortest_path(pts_id, dcgs_id, max_depth=1)
        assert path == []


# ===========================================================================
# 4. Community detection
# ===========================================================================


class TestCommunityDetection:
    def test_single_community(self, graph):
        a = graph.add_entity("A", "COMPANY")
        b = graph.add_entity("B", "COMPANY")
        c = graph.add_entity("C", "COMPANY")
        graph.add_relationship(a, b, "COMPETES_WITH")
        graph.add_relationship(b, c, "COMPETES_WITH")

        communities = graph.find_communities(min_size=3)
        assert len(communities) == 1
        assert len(communities[0]) == 3

    def test_multiple_communities(self, graph):
        # Component 1
        a = graph.add_entity("A", "COMPANY")
        b = graph.add_entity("B", "COMPANY")
        c = graph.add_entity("C", "COMPANY")
        graph.add_relationship(a, b, "COMPETES_WITH")
        graph.add_relationship(b, c, "COMPETES_WITH")

        # Component 2
        d = graph.add_entity("D", "PROGRAM")
        e = graph.add_entity("E", "AGENCY")
        f = graph.add_entity("F", "COMPANY")
        graph.add_relationship(d, e, "AWARDED_BY")
        graph.add_relationship(d, f, "PRIMES")

        communities = graph.find_communities(min_size=3)
        assert len(communities) == 2

    def test_min_size_filter(self, graph):
        a = graph.add_entity("A", "COMPANY")
        b = graph.add_entity("B", "COMPANY")
        graph.add_relationship(a, b, "COMPETES_WITH")

        # min_size=3 should exclude this pair
        communities = graph.find_communities(min_size=3)
        assert len(communities) == 0

        # min_size=2 should include it
        communities = graph.find_communities(min_size=2)
        assert len(communities) == 1

    def test_isolated_nodes_excluded(self, graph):
        graph.add_entity("LoneWolf", "COMPANY")
        communities = graph.find_communities(min_size=2)
        assert len(communities) == 0


# ===========================================================================
# 5. Teaming partner recommendations
# ===========================================================================


class TestTeamingPartners:
    def test_direct_partner(self, populated_graph):
        partners = populated_graph.get_teaming_partners("GDIT")
        partner_names = [p["name"] for p in partners]
        # PTS subcontracts to GDIT and Leidos competes — both should appear
        assert "PTS" in partner_names or "Leidos" in partner_names

    def test_shared_program_partner(self, populated_graph):
        # Leidos is connected to DCGS-A via COMPETES_WITH; GDIT primes on DCGS-A
        # So from Leidos perspective, GDIT could show as a shared-program partner
        partners = populated_graph.get_teaming_partners("Leidos")
        assert len(partners) >= 1

    def test_company_not_found(self, populated_graph):
        partners = populated_graph.get_teaming_partners("NonexistentCorp")
        assert partners == []

    def test_with_program_filter(self, graph):
        a = graph.add_entity("AlphaCo", "COMPANY")
        b = graph.add_entity("BetaCo", "COMPANY")
        p1 = graph.add_entity("ProgramX", "PROGRAM")
        p2 = graph.add_entity("ProgramY", "PROGRAM")
        graph.add_relationship(a, p1, "PRIMES")
        graph.add_relationship(b, p1, "PRIMES")
        graph.add_relationship(a, p2, "PRIMES")

        partners = graph.get_teaming_partners("AlphaCo", program="ProgramX")
        partner_names = [p["name"] for p in partners]
        assert "BetaCo" in partner_names


# ===========================================================================
# 6. Competitive landscape
# ===========================================================================


class TestCompetitiveLandscape:
    def test_landscape_structure(self, populated_graph):
        landscape = populated_graph.get_competitive_landscape("DCGS-A")
        assert "program" in landscape
        assert "incumbents" in landscape
        assert "competitors" in landscape
        assert "subcontractors" in landscape
        assert landscape["program"]["name"] == "DCGS-A"

    def test_incumbents_found(self, populated_graph):
        landscape = populated_graph.get_competitive_landscape("DCGS-A")
        incumbent_names = [e["company"]["name"] for e in landscape["incumbents"]]
        # GDIT PRIMES on DCGS-A
        assert "GDIT" in incumbent_names

    def test_program_not_found(self, populated_graph):
        landscape = populated_graph.get_competitive_landscape("NoSuchProgram")
        assert "error" in landscape


# ===========================================================================
# 7. Build from mock Qdrant data
# ===========================================================================


class TestBuildFromQdrant:
    def test_build_from_qdrant_mock(self, graph):
        mock_store = MagicMock()

        # Programs
        prog = MagicMock()
        prog.payload = {
            "name": "DCGS-A",
            "agency": "Army",
            "prime": "GDIT",
            "value": "$500M",
        }
        mock_store.get_all.side_effect = lambda col, limit=100: {
            "programs": [prog],
            "contacts": [],
            "jobs": [],
        }[col]

        with patch(
            "Engine8_Knowledge.scripts.vector_store.BDKnowledgeStore",
            return_value=mock_store,
        ):
            result = graph.build_from_qdrant()

        assert "error" not in result
        assert result["entities_added"] > 0
        stats = graph.get_stats()
        assert stats["total_entities"] > 0

    def test_build_qdrant_unavailable(self, graph):
        with patch(
            "Engine8_Knowledge.scripts.vector_store.BDKnowledgeStore",
            side_effect=ImportError("no qdrant"),
        ):
            result = graph.build_from_qdrant()
        assert "error" in result


# ===========================================================================
# 8. Stats
# ===========================================================================


class TestStats:
    def test_empty_stats(self, graph):
        stats = graph.get_stats()
        assert stats["total_entities"] == 0
        assert stats["total_relationships"] == 0
        assert stats["entities_by_type"] == {}
        assert stats["community_count"] == 0

    def test_populated_stats(self, populated_graph):
        stats = populated_graph.get_stats()
        assert stats["total_entities"] > 5
        assert stats["total_relationships"] > 5
        assert "COMPANY" in stats["entities_by_type"]
        assert "PROGRAM" in stats["entities_by_type"]
        assert "relationships_by_type" in stats


# ===========================================================================
# 9. Persistence (JSON serialization)
# ===========================================================================


class TestPersistence:
    def test_save_and_load(self, graph):
        graph.add_entity("TestCo", "COMPANY", {"size": "small"})
        tc_id = graph._resolve_name("TestCo")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            path = f.name

        try:
            graph.save(path)
            assert os.path.exists(path)

            # Load into a new graph
            with patch.object(BDKnowledgeGraph, "_init_lightrag"):
                g2 = BDKnowledgeGraph(persist_path=path)

            entity = g2.get_entity(tc_id)
            assert entity is not None
            assert entity["name"] == "TestCo"
            assert entity["metadata"]["size"] == "small"
        finally:
            os.unlink(path)

    def test_to_json(self, graph):
        graph.add_entity("X", "COMPANY")
        j = graph.to_json()
        data = json.loads(j)
        assert isinstance(data, dict)
        assert len(data) == 1

    def test_save_without_path_raises(self, graph):
        with pytest.raises(ValueError, match="No persist path"):
            graph.save()


# ===========================================================================
# 10. Edge cases
# ===========================================================================


class TestEdgeCases:
    def test_entity_types_constant(self):
        assert "PROGRAM" in ENTITY_TYPES
        assert "COMPANY" in ENTITY_TYPES
        assert "PERSON" in ENTITY_TYPES
        assert "AGENCY" in ENTITY_TYPES
        assert "INSTALLATION" in ENTITY_TYPES
        assert "CONTRACT" in ENTITY_TYPES

    def test_relationship_types_constant(self):
        assert "PRIMES" in RELATIONSHIP_TYPES
        assert "WORKS_ON" in RELATIONSHIP_TYPES
        assert "COMPETES_WITH" in RELATIONSHIP_TYPES
        assert "SUBCONTRACTS" in RELATIONSHIP_TYPES
        assert "LOCATED_AT" in RELATIONSHIP_TYPES
        assert "AWARDED_BY" in RELATIONSHIP_TYPES
        assert "EMPLOYS" in RELATIONSHIP_TYPES

    def test_make_id_deterministic(self):
        id1 = _make_id("Test", "COMPANY")
        id2 = _make_id("Test", "COMPANY")
        assert id1 == id2

    def test_make_id_case_insensitive(self):
        id1 = _make_id("GDIT", "COMPANY")
        id2 = _make_id("gdit", "COMPANY")
        assert id1 == id2

    def test_resolve_name_by_id(self, graph):
        eid = graph.add_entity("X", "COMPANY")
        assert graph._resolve_name(eid) == eid

    def test_resolve_name_case_insensitive(self, graph):
        eid = graph.add_entity("GDIT", "COMPANY")
        assert graph._resolve_name("gdit") == eid
        assert graph._resolve_name("GDIT") == eid

    def test_resolve_name_none(self, graph):
        assert graph._resolve_name("") is None
        assert graph._resolve_name(None) is None

    def test_empty_graph_communities(self, graph):
        communities = graph.find_communities()
        assert communities == []

    def test_path_through_large_graph(self, graph):
        # Chain: A -> B -> C -> D -> E
        ids = []
        for i in range(5):
            ids.append(graph.add_entity(f"Node{i}", "COMPANY"))
        for i in range(4):
            graph.add_relationship(ids[i], ids[i + 1], "SUBCONTRACTS")

        path = graph.shortest_path(ids[0], ids[4])
        assert len(path) == 5
        assert path[0]["name"] == "Node0"
        assert path[4]["name"] == "Node4"
