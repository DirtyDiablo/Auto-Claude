"""Tests for Phase 34A — Network Analysis Engine."""

import pytest

from src.graph.network_analysis import (
    NetworkAnalyzer,
    Community,
    BridgeContact,
    DensityReport,
    GrowthReport,
    get_network_analyzer,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def analyzer_with_data():
    a = NetworkAnalyzer()
    nodes = [
        {"id": "a1", "name": "Alice", "tier": 1, "programs": ["DCGS"]},
        {"id": "a2", "name": "Bob", "tier": 2, "programs": ["DCGS"]},
        {"id": "a3", "name": "Carol", "tier": 3, "programs": ["DCGS"]},
        {"id": "b1", "name": "Dave", "tier": 2, "programs": ["NGEN"]},
        {"id": "b2", "name": "Eve", "tier": 3, "programs": ["NGEN"]},
        {"id": "bridge", "name": "Frank", "tier": 3, "programs": ["DCGS", "NGEN"]},
    ]
    edges = [
        {"source": "a1", "target": "a2", "strength": 80},
        {"source": "a2", "target": "a3", "strength": 70},
        {"source": "a1", "target": "a3", "strength": 60},
        {"source": "b1", "target": "b2", "strength": 75},
        {"source": "bridge", "target": "a2", "strength": 65},
        {"source": "bridge", "target": "b1", "strength": 55},
    ]
    a.set_graph_data(nodes, edges)
    return a


@pytest.fixture
def empty_analyzer():
    return NetworkAnalyzer()


# =========================================
# COMMUNITY DETECTION
# =========================================

@pytest.mark.asyncio
class TestCommunityDetection:
    async def test_detects_communities(self, analyzer_with_data):
        communities = await analyzer_with_data.detect_communities()
        assert isinstance(communities, list)
        assert len(communities) > 0

    async def test_community_structure(self, analyzer_with_data):
        communities = await analyzer_with_data.detect_communities()
        for c in communities:
            assert isinstance(c, Community)
            assert c.size >= 2
            assert len(c.members) == c.size
            assert isinstance(c.programs, list)
            assert c.key_member != ""

    async def test_community_has_label(self, analyzer_with_data):
        communities = await analyzer_with_data.detect_communities()
        for c in communities:
            assert c.label != ""

    async def test_empty_graph(self, empty_analyzer):
        communities = await empty_analyzer.detect_communities()
        assert communities == []

    async def test_min_community_size(self, analyzer_with_data):
        communities = await analyzer_with_data.detect_communities(min_community_size=3)
        for c in communities:
            assert c.size >= 3


# =========================================
# BRIDGE CONTACTS
# =========================================

@pytest.mark.asyncio
class TestBridgeContacts:
    async def test_finds_bridges(self, analyzer_with_data):
        bridges = await analyzer_with_data.find_bridge_contacts()
        assert isinstance(bridges, list)

    async def test_bridge_structure(self, analyzer_with_data):
        bridges = await analyzer_with_data.find_bridge_contacts()
        for b in bridges:
            assert isinstance(b, BridgeContact)
            assert b.bridge_score >= 0

    async def test_empty_graph(self, empty_analyzer):
        bridges = await empty_analyzer.find_bridge_contacts()
        assert bridges == []


# =========================================
# NETWORK DENSITY
# =========================================

@pytest.mark.asyncio
class TestNetworkDensity:
    async def test_global_density(self, analyzer_with_data):
        report = await analyzer_with_data.get_network_density()
        assert isinstance(report, DensityReport)
        assert report.scope == "global"

    async def test_density_range(self, analyzer_with_data):
        report = await analyzer_with_data.get_network_density()
        assert 0 <= report.density <= 1
        assert report.total_nodes == 6
        assert report.total_edges > 0

    async def test_program_scoped_density(self, analyzer_with_data):
        report = await analyzer_with_data.get_network_density(program="DCGS")
        assert report.scope == "DCGS"
        assert report.total_nodes <= 6

    async def test_assessment_values(self, analyzer_with_data):
        report = await analyzer_with_data.get_network_density()
        assert report.assessment in ("dense", "moderate", "sparse")

    async def test_clustering_coefficient(self, analyzer_with_data):
        report = await analyzer_with_data.get_network_density()
        assert 0 <= report.clustering_coefficient <= 1

    async def test_empty_graph(self, empty_analyzer):
        report = await empty_analyzer.get_network_density()
        assert report.total_nodes == 0
        assert report.density == 0


# =========================================
# NETWORK GROWTH
# =========================================

@pytest.mark.asyncio
class TestNetworkGrowth:
    async def test_returns_report(self, analyzer_with_data):
        report = await analyzer_with_data.get_network_growth(90)
        assert isinstance(report, GrowthReport)
        assert report.period_days == 90

    async def test_growth_assessment(self, analyzer_with_data):
        report = await analyzer_with_data.get_network_growth()
        assert report.assessment in ("expanding", "stable", "contracting")

    async def test_with_history(self, analyzer_with_data):
        history = [
            {"date": "2025-12-01", "type": "new_contact", "name": "New Person"},
            {"date": "2025-12-15", "type": "new_relationship", "contact": "Another"},
        ]
        report = await analyzer_with_data.get_network_growth(90, history)
        assert isinstance(report, GrowthReport)

    async def test_empty_graph(self, empty_analyzer):
        report = await empty_analyzer.get_network_growth()
        assert report.net_growth == 0


# =========================================
# SINGLETON
# =========================================

class TestSingleton:
    def test_get_analyzer_returns_instance(self):
        a = get_network_analyzer()
        assert isinstance(a, NetworkAnalyzer)

    def test_get_analyzer_is_singleton(self):
        a1 = get_network_analyzer()
        a2 = get_network_analyzer()
        assert a1 is a2
