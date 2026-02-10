"""Tests for Phase 34A — BD PageRank Influence Scorer."""

import pytest

from src.graph.influence_scorer import (
    BDPageRank,
    InfluenceScore,
    InfluenceTrajectory,
    KeyConnector,
    TIER_WEIGHTS,
    DAMPING_FACTOR,
    get_influence_scorer,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def scorer():
    return BDPageRank()


@pytest.fixture
def sample_nodes():
    return [
        {"id": "c1", "name": "VP Smith", "tier": 1, "programs": ["DCGS", "PACAF"]},
        {"id": "c2", "name": "Dir Jones", "tier": 2, "programs": ["DCGS"]},
        {"id": "c3", "name": "PM Brown", "tier": 3, "programs": ["NGEN"]},
        {"id": "c4", "name": "Analyst Lee", "tier": 5, "programs": ["DCGS", "NGEN"]},
        {"id": "c5", "name": "Coord Patel", "tier": 6, "programs": ["GBSD"]},
    ]


@pytest.fixture
def sample_edges():
    return [
        {"source": "c1", "target": "c2", "strength": 85},
        {"source": "c1", "target": "c3", "strength": 60},
        {"source": "c2", "target": "c4", "strength": 70},
        {"source": "c3", "target": "c4", "strength": 50},
        {"source": "c4", "target": "c5", "strength": 30},
    ]


# =========================================
# TIER WEIGHTS
# =========================================

class TestTierWeights:
    def test_tier_1_highest(self):
        assert TIER_WEIGHTS[1] == 10.0

    def test_tier_6_lowest(self):
        assert TIER_WEIGHTS[6] == 1.0

    def test_monotonic_decrease(self):
        for i in range(1, 6):
            assert TIER_WEIGHTS[i] >= TIER_WEIGHTS[i + 1]

    def test_damping_factor(self):
        assert DAMPING_FACTOR == 0.85


# =========================================
# GLOBAL INFLUENCE
# =========================================

@pytest.mark.asyncio
class TestGlobalInfluence:
    async def test_returns_list(self, scorer, sample_nodes, sample_edges):
        scores = await scorer.compute_influence_scores(sample_nodes, sample_edges)
        assert isinstance(scores, list)
        assert len(scores) == 5

    async def test_scores_are_influence_score(self, scorer, sample_nodes, sample_edges):
        scores = await scorer.compute_influence_scores(sample_nodes, sample_edges)
        for s in scores:
            assert isinstance(s, InfluenceScore)

    async def test_scores_normalized_0_100(self, scorer, sample_nodes, sample_edges):
        scores = await scorer.compute_influence_scores(sample_nodes, sample_edges)
        for s in scores:
            assert 0 <= s.score <= 100

    async def test_top_ranked_is_rank_1(self, scorer, sample_nodes, sample_edges):
        scores = await scorer.compute_influence_scores(sample_nodes, sample_edges)
        assert scores[0].rank == 1
        assert scores[0].score >= scores[-1].score

    async def test_tier_1_generally_higher(self, scorer, sample_nodes, sample_edges):
        scores = await scorer.compute_influence_scores(sample_nodes, sample_edges)
        tier1 = [s for s in scores if s.tier == 1]
        tier6 = [s for s in scores if s.tier == 6]
        if tier1 and tier6:
            assert tier1[0].score >= tier6[0].score

    async def test_empty_nodes(self, scorer):
        scores = await scorer.compute_influence_scores([], [])
        assert scores == []


# =========================================
# PROGRAM INFLUENCE
# =========================================

@pytest.mark.asyncio
class TestProgramInfluence:
    async def test_program_scoped(self, scorer, sample_nodes, sample_edges):
        scores = await scorer.compute_program_influence("DCGS", sample_nodes, sample_edges)
        assert isinstance(scores, list)
        # Should contain nodes on DCGS
        assert len(scores) > 0

    async def test_unknown_program(self, scorer, sample_nodes, sample_edges):
        scores = await scorer.compute_program_influence("NONEXISTENT", sample_nodes, sample_edges)
        assert scores == []


# =========================================
# KEY CONNECTORS
# =========================================

@pytest.mark.asyncio
class TestKeyConnectors:
    async def test_returns_connectors(self, scorer, sample_nodes, sample_edges):
        # Compute influence first
        await scorer.compute_influence_scores(sample_nodes, sample_edges)
        connectors = await scorer.get_key_connectors(sample_nodes, sample_edges)
        assert isinstance(connectors, list)

    async def test_connector_structure(self, scorer, sample_nodes, sample_edges):
        await scorer.compute_influence_scores(sample_nodes, sample_edges)
        connectors = await scorer.get_key_connectors(sample_nodes, sample_edges)
        for c in connectors:
            assert isinstance(c, KeyConnector)
            assert isinstance(c.programs_bridged, list)


# =========================================
# INFLUENCE TRAJECTORY
# =========================================

@pytest.mark.asyncio
class TestInfluenceTrajectory:
    async def test_trajectory_returns_result(self, scorer, sample_nodes, sample_edges):
        await scorer.compute_influence_scores(sample_nodes, sample_edges)
        traj = await scorer.get_influence_trajectory("c1")
        assert isinstance(traj, InfluenceTrajectory)

    async def test_trajectory_trend(self, scorer, sample_nodes, sample_edges):
        await scorer.compute_influence_scores(sample_nodes, sample_edges)
        traj = await scorer.get_influence_trajectory("c1")
        assert traj.trend in ("increasing", "decreasing", "stable")

    async def test_unknown_contact(self, scorer):
        traj = await scorer.get_influence_trajectory("nonexistent")
        assert traj.current_score == 0


# =========================================
# SINGLETON
# =========================================

class TestSingleton:
    def test_get_scorer_returns_instance(self):
        s = get_influence_scorer()
        assert isinstance(s, BDPageRank)

    def test_get_scorer_is_singleton(self):
        s1 = get_influence_scorer()
        s2 = get_influence_scorer()
        assert s1 is s2
