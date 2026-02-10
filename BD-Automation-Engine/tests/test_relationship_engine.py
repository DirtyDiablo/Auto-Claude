"""Tests for Phase 34A — Relationship Strength Engine."""

import pytest
from datetime import datetime, timedelta, timezone

from src.graph.relationship_engine import (
    RelationshipStrengthModel,
    RelationshipScore,
    DecayingRelationship,
    RankedPath,
    DIMENSION_WEIGHTS,
    INTERACTION_QUALITY,
    get_relationship_model,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def model():
    return RelationshipStrengthModel()


@pytest.fixture
def recent_interactions():
    now = datetime.now(timezone.utc)
    return [
        {"date": (now - timedelta(days=1)).isoformat(), "type": "meeting", "initiator": "A"},
        {"date": (now - timedelta(days=5)).isoformat(), "type": "call", "initiator": "B"},
        {"date": (now - timedelta(days=10)).isoformat(), "type": "email", "initiator": "A"},
        {"date": (now - timedelta(days=15)).isoformat(), "type": "email", "initiator": "B"},
    ]


@pytest.fixture
def stale_interactions():
    now = datetime.now(timezone.utc)
    return [
        {"date": (now - timedelta(days=60)).isoformat(), "type": "email", "initiator": "A"},
    ]


@pytest.fixture
def shared_data():
    return {
        "shared_programs": 2,
        "shared_contacts": 5,
        "referrals": 1,
        "placements": 1,
        "introductions": 2,
    }


# =========================================
# DIMENSION WEIGHTS
# =========================================

class TestDimensionWeights:
    def test_weights_sum_to_one(self):
        total = sum(DIMENSION_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_six_dimensions(self):
        assert len(DIMENSION_WEIGHTS) == 6

    def test_recency_is_highest(self):
        assert DIMENSION_WEIGHTS["recency"] == 0.25


# =========================================
# SINGLE SCORING
# =========================================

@pytest.mark.asyncio
class TestRelationshipScoring:
    async def test_score_returns_relationship_score(self, model, recent_interactions, shared_data):
        score = await model.score_relationship("A", "B", recent_interactions, shared_data)
        assert isinstance(score, RelationshipScore)

    async def test_score_range(self, model, recent_interactions, shared_data):
        score = await model.score_relationship("A", "B", recent_interactions, shared_data)
        assert 0 <= score.total_score <= 100

    async def test_all_dimensions_scored(self, model, recent_interactions, shared_data):
        score = await model.score_relationship("A", "B", recent_interactions, shared_data)
        assert score.recency_score >= 0
        assert score.frequency_score >= 0
        assert score.quality_score >= 0
        assert score.reciprocity_score >= 0
        assert score.depth_score >= 0
        assert score.outcome_score >= 0

    async def test_recent_scores_higher_than_stale(self, model, recent_interactions, stale_interactions):
        recent = await model.score_relationship("A", "B", recent_interactions)
        stale = await model.score_relationship("C", "D", stale_interactions)
        assert recent.total_score > stale.total_score

    async def test_empty_interactions(self, model):
        score = await model.score_relationship("A", "B", [])
        assert score.total_score == 0

    async def test_shared_data_increases_score(self, model, recent_interactions, shared_data):
        without = await model.score_relationship("A", "B", recent_interactions)
        with_shared = await model.score_relationship("C", "D", recent_interactions, shared_data)
        assert with_shared.total_score > without.total_score

    async def test_factors_tracked(self, model, recent_interactions, shared_data):
        score = await model.score_relationship("A", "B", recent_interactions, shared_data)
        assert score.factors["interaction_count"] == 4
        assert score.factors["shared_programs"] == 2

    async def test_scored_at_timestamp(self, model, recent_interactions):
        score = await model.score_relationship("A", "B", recent_interactions)
        assert score.scored_at != ""


# =========================================
# BATCH SCORING
# =========================================

@pytest.mark.asyncio
class TestBatchScoring:
    async def test_batch_returns_list(self, model):
        rels = [
            {"contact_a": "A", "contact_b": "B", "interactions": [{"type": "call", "date": "2025-01-01"}]},
            {"contact_a": "C", "contact_b": "D", "interactions": []},
        ]
        scores = await model.score_all_relationships(rels)
        assert isinstance(scores, list)
        assert len(scores) == 2

    async def test_batch_sorted_descending(self, model):
        now = datetime.now(timezone.utc)
        rels = [
            {"contact_a": "A", "contact_b": "B", "interactions": []},
            {"contact_a": "C", "contact_b": "D", "interactions": [
                {"type": "meeting", "date": (now - timedelta(days=1)).isoformat()},
            ]},
        ]
        scores = await model.score_all_relationships(rels)
        assert scores[0].total_score >= scores[1].total_score


# =========================================
# DECAYING RELATIONSHIPS
# =========================================

@pytest.mark.asyncio
class TestDecayingRelationships:
    async def test_decaying_returns_list(self, model, recent_interactions):
        # Seed cache with a score
        score = await model.score_relationship("A", "B", recent_interactions)
        score.factors["days_since_contact"] = 20
        model._scores_cache["A:B"] = score
        decaying = await model.get_decaying_relationships(threshold=10, days=14)
        assert isinstance(decaying, list)

    async def test_empty_cache_returns_empty(self, model):
        decaying = await model.get_decaying_relationships()
        assert decaying == []


# =========================================
# STRONGEST PATHS
# =========================================

@pytest.mark.asyncio
class TestStrongestPaths:
    async def test_finds_path(self, model):
        graph_data = {
            "A": [{"to": "B", "strength": 80}],
            "B": [{"to": "C", "strength": 60}],
        }
        paths = await model.get_strongest_paths("A", "C", graph_data=graph_data)
        assert isinstance(paths, list)
        assert len(paths) > 0

    async def test_path_structure(self, model):
        graph_data = {
            "A": [{"to": "B", "strength": 90}],
            "B": [{"to": "C", "strength": 70}],
        }
        paths = await model.get_strongest_paths("A", "C", graph_data=graph_data)
        assert isinstance(paths[0], RankedPath)
        assert paths[0].hops == 2
        assert paths[0].weakest_link == 70

    async def test_no_path_returns_empty(self, model):
        graph_data = {
            "A": [{"to": "B", "strength": 80}],
            "X": [{"to": "Y", "strength": 60}],
        }
        paths = await model.get_strongest_paths("A", "Y", graph_data=graph_data)
        assert paths == []

    async def test_empty_graph_returns_empty(self, model):
        paths = await model.get_strongest_paths("A", "B", graph_data={})
        assert paths == []


# =========================================
# INTERACTION QUALITY
# =========================================

class TestInteractionQuality:
    def test_meeting_highest(self):
        assert INTERACTION_QUALITY["meeting"] == 1.0

    def test_email_lower_than_call(self):
        assert INTERACTION_QUALITY["email"] < INTERACTION_QUALITY["call"]

    def test_linkedin_lowest(self):
        assert INTERACTION_QUALITY["linkedin"] <= min(
            v for k, v in INTERACTION_QUALITY.items() if k != "linkedin"
        )


# =========================================
# SINGLETON
# =========================================

class TestSingleton:
    def test_get_model_returns_instance(self):
        m = get_relationship_model()
        assert isinstance(m, RelationshipStrengthModel)

    def test_get_model_is_singleton(self):
        m1 = get_relationship_model()
        m2 = get_relationship_model()
        assert m1 is m2
