"""Tests for Phase 32A — Composite Opportunity Scorer."""

import pytest

from src.ml.opportunity_scorer import (
    OpportunityScorer,
    ScoredOpportunity,
    PipelineReview,
    DIMENSION_WEIGHTS,
    get_opportunity_scorer,
)


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def scorer():
    return OpportunityScorer()


@pytest.fixture
def strong_opportunity():
    return {
        "id": "opp-strong",
        "title": "Sr Intelligence Analyst - ISR",
        "company": "Leidos",
        "program": "AF DCGS - PACAF",
        "contact_tier": 1,
        "relationship_depth": 10,
        "days_since_last_contact": 3,
        "mutual_connections": 5,
        "pts_involvement": 3,
        "competitor_density": 1,
        "past_placements_on_program": 3,
        "clearance_match": 1,
        "role_match_score": 0.95,
        "location_familiarity": 0.9,
        "days_job_open": 7,
        "salary_competitiveness": 1.2,
        "fiscal_quarter": 4,
        "days_to_pop_end": 60,
        "is_option_year": 1,
        "estimated_value": 5_000_000,
        "location": "Hickam AFB",
        "description": "ISR SIGINT data fusion analyst position",
    }


@pytest.fixture
def weak_opportunity():
    return {
        "id": "opp-weak",
        "title": "Associate Coordinator",
        "company": "Unknown Corp",
        "contact_tier": 6,
        "relationship_depth": 0,
        "days_since_last_contact": 90,
        "mutual_connections": 0,
        "pts_involvement": 0,
        "competitor_density": 10,
        "past_placements_on_program": 0,
        "clearance_match": 0,
        "fiscal_quarter": 1,
        "estimated_value": 0,
    }


@pytest.fixture
def sample_pipeline():
    return [
        {
            "id": "opp-1",
            "title": "Sr Analyst",
            "company": "Leidos",
            "program": "AF DCGS",
            "contact_tier": 2,
            "relationship_depth": 5,
            "days_since_last_contact": 5,
            "estimated_value": 500000,
            "days_job_open": 10,
            "fiscal_quarter": 3,
            "clearance_match": 1,
            "pts_involvement": 2,
            "competitor_density": 3,
        },
        {
            "id": "opp-2",
            "title": "Cyber Engineer",
            "company": "GDIT",
            "program": "NGEN",
            "contact_tier": 4,
            "relationship_depth": 1,
            "days_since_last_contact": 30,
            "estimated_value": 200000,
            "days_job_open": 25,
            "fiscal_quarter": 2,
            "clearance_match": 0,
            "pts_involvement": 0,
            "competitor_density": 7,
        },
        {
            "id": "opp-3",
            "title": "Systems Engineer",
            "company": "NGC",
            "program": "GBSD",
            "contact_tier": 5,
            "relationship_depth": 0,
            "days_since_last_contact": 50,
            "estimated_value": 100000,
            "days_job_open": 45,
            "fiscal_quarter": 1,
            "clearance_match": 0,
            "pts_involvement": 0,
            "competitor_density": 9,
        },
    ]


# =========================================
# DIMENSION WEIGHTS
# =========================================


class TestDimensionWeights:
    def test_weights_sum_to_one(self):
        total = sum(DIMENSION_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_six_dimensions(self):
        assert len(DIMENSION_WEIGHTS) == 6

    def test_win_probability_highest_weight(self):
        assert DIMENSION_WEIGHTS["win_probability"] == 0.30
        assert all(
            DIMENSION_WEIGHTS["win_probability"] >= v
            for v in DIMENSION_WEIGHTS.values()
        )


# =========================================
# SINGLE SCORING
# =========================================


@pytest.mark.asyncio
class TestSingleScoring:
    async def test_score_returns_scored_opp(self, scorer, strong_opportunity):
        result = await scorer.score_opportunity(strong_opportunity)
        assert isinstance(result, ScoredOpportunity)

    async def test_composite_score_range(self, scorer, strong_opportunity):
        result = await scorer.score_opportunity(strong_opportunity)
        assert 0 <= result.composite_score <= 100

    async def test_six_dimensions_scored(self, scorer, strong_opportunity):
        result = await scorer.score_opportunity(strong_opportunity)
        assert len(result.dimensions) == 6

    async def test_dimension_names(self, scorer, strong_opportunity):
        result = await scorer.score_opportunity(strong_opportunity)
        names = {d.name for d in result.dimensions}
        assert names == set(DIMENSION_WEIGHTS.keys())

    async def test_strong_scores_higher(
        self, scorer, strong_opportunity, weak_opportunity
    ):
        strong = await scorer.score_opportunity(strong_opportunity)
        weak = await scorer.score_opportunity(weak_opportunity)
        assert strong.composite_score > weak.composite_score

    async def test_recommended_approach_present(self, scorer, strong_opportunity):
        result = await scorer.score_opportunity(strong_opportunity)
        assert isinstance(result.recommended_approach, str)
        assert len(result.recommended_approach) > 0

    async def test_win_probability_field(self, scorer, strong_opportunity):
        result = await scorer.score_opportunity(strong_opportunity)
        assert 0.0 <= result.win_probability <= 1.0


# =========================================
# PIPELINE RANKING
# =========================================


@pytest.mark.asyncio
class TestPipelineRanking:
    async def test_rank_returns_list(self, scorer, sample_pipeline):
        ranked = await scorer.rank_pipeline(sample_pipeline)
        assert isinstance(ranked, list)
        assert len(ranked) == 3

    async def test_ranks_assigned(self, scorer, sample_pipeline):
        ranked = await scorer.rank_pipeline(sample_pipeline)
        ranks = [s.rank for s in ranked]
        assert ranks == [1, 2, 3]

    async def test_sorted_descending(self, scorer, sample_pipeline):
        ranked = await scorer.rank_pipeline(sample_pipeline)
        scores = [s.composite_score for s in ranked]
        assert scores == sorted(scores, reverse=True)

    async def test_limit_parameter(self, scorer, sample_pipeline):
        ranked = await scorer.rank_pipeline(sample_pipeline, limit=2)
        assert len(ranked) == 2


# =========================================
# PIPELINE REVIEW
# =========================================


@pytest.mark.asyncio
class TestPipelineReview:
    async def test_review_returns_pipeline_review(self, scorer, sample_pipeline):
        review = await scorer.weekly_pipeline_review(sample_pipeline)
        assert isinstance(review, PipelineReview)

    async def test_review_has_top_opportunities(self, scorer, sample_pipeline):
        review = await scorer.weekly_pipeline_review(sample_pipeline)
        assert isinstance(review.top_opportunities, list)
        assert len(review.top_opportunities) <= 10

    async def test_review_has_focus_areas(self, scorer, sample_pipeline):
        review = await scorer.weekly_pipeline_review(sample_pipeline)
        assert isinstance(review.focus_areas, list)

    async def test_review_total_value(self, scorer, sample_pipeline):
        review = await scorer.weekly_pipeline_review(sample_pipeline)
        assert review.total_pipeline_value == 800000  # 500k + 200k + 100k


# =========================================
# WHAT-IF ANALYSIS
# =========================================


@pytest.mark.asyncio
class TestWhatIfAnalysis:
    async def test_what_if_returns_dict(self, scorer, strong_opportunity):
        result = await scorer.what_if_analysis(strong_opportunity, {"contact_tier": 1})
        assert isinstance(result, dict)

    async def test_what_if_has_delta(self, scorer, strong_opportunity):
        result = await scorer.what_if_analysis(
            strong_opportunity, {"competitor_density": 1}
        )
        assert "score_delta" in result
        assert "original_score" in result
        assert "modified_score" in result

    async def test_what_if_impact_direction(self, scorer, weak_opportunity):
        # Improving relationship should increase score
        result = await scorer.what_if_analysis(
            weak_opportunity, {"contact_tier": 1, "relationship_depth": 10}
        )
        assert result["score_delta"] >= 0


# =========================================
# SINGLETON
# =========================================


class TestSingleton:
    def test_get_scorer_returns_instance(self):
        s = get_opportunity_scorer()
        assert isinstance(s, OpportunityScorer)

    def test_get_scorer_is_singleton(self):
        s1 = get_opportunity_scorer()
        s2 = get_opportunity_scorer()
        assert s1 is s2
