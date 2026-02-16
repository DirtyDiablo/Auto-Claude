"""Tests for Phase 34A — Optimal Path Router."""

import pytest

from src.graph.path_router import (
    OptimalPathRouter,
    PathOption,
    WarmIntroChain,
    MissingLink,
    NetworkGap,
    get_path_router,
)


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def router_with_data():
    r = OptimalPathRouter()
    nodes = [
        {
            "id": "us",
            "name": "Our Contact",
            "tier": 2,
            "programs": ["DCGS"],
            "is_ours": True,
        },
        {
            "id": "mid1",
            "name": "Bridge Person",
            "tier": 3,
            "programs": ["DCGS", "NGEN"],
        },
        {"id": "mid2", "name": "Alt Path", "tier": 4, "programs": ["NGEN"]},
        {"id": "target", "name": "VP Target", "tier": 1, "programs": ["NGEN"]},
        {"id": "isolated", "name": "Lone Wolf", "tier": 5, "programs": ["GBSD"]},
    ]
    edges = [
        {"source": "us", "target": "mid1", "strength": 80},
        {"source": "mid1", "target": "target", "strength": 70},
        {"source": "us", "target": "mid2", "strength": 50},
        {"source": "mid2", "target": "target", "strength": 40},
        {"source": "mid1", "target": "mid2", "strength": 60},
    ]
    r.set_graph_data(nodes, edges)
    return r


@pytest.fixture
def empty_router():
    return OptimalPathRouter()


# =========================================
# OPTIMAL PATH
# =========================================


@pytest.mark.asyncio
class TestOptimalPath:
    async def test_finds_paths(self, router_with_data):
        paths = await router_with_data.find_optimal_path("us", "target")
        assert isinstance(paths, list)
        assert len(paths) > 0

    async def test_path_structure(self, router_with_data):
        paths = await router_with_data.find_optimal_path("us", "target")
        for p in paths:
            assert isinstance(p, PathOption)
            assert p.hops > 0
            assert p.total_strength > 0
            assert p.weakest_link >= 0

    async def test_strongest_path_ranked_first(self, router_with_data):
        paths = await router_with_data.find_optimal_path("us", "target")
        if len(paths) >= 2:
            assert paths[0].total_strength >= paths[1].total_strength

    async def test_path_names_populated(self, router_with_data):
        paths = await router_with_data.find_optimal_path("us", "target")
        assert len(paths[0].path_names) > 0
        assert (
            "Our Contact" in paths[0].path_names or "VP Target" in paths[0].path_names
        )

    async def test_no_path_returns_empty(self, router_with_data):
        paths = await router_with_data.find_optimal_path("us", "isolated")
        assert paths == []

    async def test_empty_graph_returns_empty(self, empty_router):
        paths = await empty_router.find_optimal_path("A", "B")
        assert paths == []

    async def test_multiple_paths_found(self, router_with_data):
        paths = await router_with_data.find_optimal_path("us", "target")
        assert len(paths) >= 2  # Should find both us->mid1->target and us->mid2->target

    async def test_weakest_link_identified(self, router_with_data):
        paths = await router_with_data.find_optimal_path("us", "target")
        for p in paths:
            assert p.weakest_link_segment != ""


# =========================================
# WARM INTRO CHAIN
# =========================================


@pytest.mark.asyncio
class TestWarmIntroChain:
    async def test_finds_chain(self, router_with_data):
        chains = await router_with_data.find_warm_intro_chain("target")
        assert isinstance(chains, list)
        assert len(chains) > 0

    async def test_chain_structure(self, router_with_data):
        chains = await router_with_data.find_warm_intro_chain("target")
        for c in chains:
            assert isinstance(c, WarmIntroChain)
            assert c.hops > 0
            assert c.feasibility in ("strong", "moderate", "weak")
            assert isinstance(c.chain, list)

    async def test_chain_has_approach(self, router_with_data):
        chains = await router_with_data.find_warm_intro_chain("target")
        assert chains[0].suggested_approach != ""

    async def test_empty_graph_returns_empty(self, empty_router):
        chains = await empty_router.find_warm_intro_chain("target")
        assert chains == []


# =========================================
# MISSING LINKS
# =========================================


@pytest.mark.asyncio
class TestMissingLinks:
    async def test_no_contacts_critical(self, router_with_data):
        links = await router_with_data.identify_missing_links("NONEXISTENT")
        assert len(links) > 0
        assert links[0].gap_type == "no_contact"
        assert links[0].priority == "critical"

    async def test_known_program(self, router_with_data):
        links = await router_with_data.identify_missing_links("GBSD")
        assert isinstance(links, list)
        # GBSD has only 1 contact (isolated) → should flag single_thread
        for l in links:
            assert isinstance(l, MissingLink)

    async def test_empty_graph(self, empty_router):
        links = await empty_router.identify_missing_links("DCGS")
        assert links == []


# =========================================
# NETWORK GAPS
# =========================================


@pytest.mark.asyncio
class TestNetworkGaps:
    async def test_returns_gaps(self, router_with_data):
        gaps = await router_with_data.get_network_gaps()
        assert isinstance(gaps, list)

    async def test_gap_structure(self, router_with_data):
        gaps = await router_with_data.get_network_gaps()
        for g in gaps:
            assert isinstance(g, NetworkGap)
            assert g.gap_severity in ("critical", "significant", "minor")
            assert isinstance(g.recommendations, list)

    async def test_specific_programs(self, router_with_data):
        gaps = await router_with_data.get_network_gaps(
            programs=["DCGS", "NGEN", "UNKNOWN"]
        )
        # UNKNOWN should show as critical
        unknown_gaps = [g for g in gaps if g.program == "UNKNOWN"]
        if unknown_gaps:
            assert unknown_gaps[0].gap_severity == "critical"


# =========================================
# SINGLETON
# =========================================


class TestSingleton:
    def test_get_router_returns_instance(self):
        r = get_path_router()
        assert isinstance(r, OptimalPathRouter)

    def test_get_router_is_singleton(self):
        r1 = get_path_router()
        r2 = get_path_router()
        assert r1 is r2
