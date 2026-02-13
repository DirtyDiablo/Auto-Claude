"""Tests for Phase 32A — Win Probability Model."""

import pytest

from src.ml.win_probability import (
    WinProbabilityModel,
    WinPrediction,
    TrainResult,
    ModelMetrics,
    ALL_FEATURES,
    get_win_model,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def model():
    return WinProbabilityModel()


@pytest.fixture
def sample_opportunity():
    return {
        "id": "opp-test-1",
        "title": "Sr Intelligence Analyst",
        "company": "Leidos",
        "program": "AF DCGS - PACAF",
        "contact_tier": 2,
        "relationship_depth": 8,
        "days_since_last_contact": 5,
        "mutual_connections": 3,
        "contact_response_rate": 0.7,
        "pts_involvement": 3,
        "program_value_log": 8.5,
        "days_to_pop_end": 180,
        "past_placements_on_program": 2,
        "competitor_density": 2,
        "clearance_match": 1,
        "role_match_score": 0.9,
        "location_familiarity": 0.8,
        "days_job_open": 10,
        "salary_competitiveness": 1.1,
        "fiscal_quarter": 3,
        "days_to_fy_end": 90,
        "is_option_year": 0,
        "seasonal_hiring_index": 1.2,
        "outreach_attempts": 3,
        "channels_used": 2,
        "similar_opp_win_rate": 0.4,
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
        "contact_response_rate": 0.0,
        "pts_involvement": 0,
        "program_value_log": 4.0,
        "days_to_pop_end": 500,
        "past_placements_on_program": 0,
        "competitor_density": 10,
        "clearance_match": 0,
        "role_match_score": 0.2,
        "location_familiarity": 0.1,
        "days_job_open": 60,
        "salary_competitiveness": 0.8,
        "fiscal_quarter": 1,
        "days_to_fy_end": 365,
        "is_option_year": 0,
        "seasonal_hiring_index": 0.7,
        "outreach_attempts": 0,
        "channels_used": 0,
        "similar_opp_win_rate": 0.1,
    }


# =========================================
# FEATURE DEFINITIONS
# =========================================

class TestFeatureDefinitions:
    def test_all_features_count(self):
        assert len(ALL_FEATURES) == 22

    def test_feature_names_are_strings(self):
        for f in ALL_FEATURES:
            assert isinstance(f, str)

    def test_key_features_present(self):
        assert "contact_tier" in ALL_FEATURES
        assert "clearance_match" in ALL_FEATURES
        assert "fiscal_quarter" in ALL_FEATURES
        assert "competitor_density" in ALL_FEATURES
        assert "outreach_attempts" in ALL_FEATURES


# =========================================
# HEURISTIC PREDICTION (no model trained)
# =========================================

@pytest.mark.asyncio
class TestHeuristicPrediction:
    async def test_predict_returns_win_prediction(self, model, sample_opportunity):
        pred = await model.predict(sample_opportunity)
        assert isinstance(pred, WinPrediction)

    async def test_win_probability_range(self, model, sample_opportunity):
        pred = await model.predict(sample_opportunity)
        assert 0.0 <= pred.win_probability <= 1.0

    async def test_confidence_range(self, model, sample_opportunity):
        pred = await model.predict(sample_opportunity)
        assert pred.confidence in ("low", "medium", "high")

    async def test_strong_opp_higher_than_weak(self, model, sample_opportunity, weak_opportunity):
        strong = await model.predict(sample_opportunity)
        weak = await model.predict(weak_opportunity)
        assert strong.win_probability > weak.win_probability

    async def test_top_factors_populated(self, model, sample_opportunity):
        pred = await model.predict(sample_opportunity)
        assert isinstance(pred.top_factors, list)
        assert len(pred.top_factors) > 0

    async def test_recommended_actions_populated(self, model, sample_opportunity):
        pred = await model.predict(sample_opportunity)
        assert isinstance(pred.recommended_actions, list)
        assert len(pred.recommended_actions) > 0

    async def test_optimal_timing_present(self, model, sample_opportunity):
        pred = await model.predict(sample_opportunity)
        assert isinstance(pred.optimal_timing, str)
        assert len(pred.optimal_timing) > 0

    async def test_empty_opportunity_defaults(self, model):
        pred = await model.predict({})
        assert isinstance(pred, WinPrediction)
        assert 0.0 <= pred.win_probability <= 1.0


# =========================================
# BATCH PREDICTION
# =========================================

@pytest.mark.asyncio
class TestBatchPrediction:
    async def test_batch_returns_list(self, model, sample_opportunity, weak_opportunity):
        preds = await model.predict_batch([sample_opportunity, weak_opportunity])
        assert isinstance(preds, list)
        assert len(preds) == 2

    async def test_batch_each_is_win_prediction(self, model, sample_opportunity):
        preds = await model.predict_batch([sample_opportunity])
        assert all(isinstance(p, WinPrediction) for p in preds)

    async def test_batch_empty_input(self, model):
        preds = await model.predict_batch([])
        assert preds == []


# =========================================
# TRAINING
# =========================================

@pytest.mark.asyncio
class TestTraining:
    async def test_train_returns_result(self, model):
        result = await model.train(n_synthetic=50)
        assert isinstance(result, TrainResult)

    async def test_train_result_fields(self, model):
        result = await model.train(n_synthetic=50)
        assert 0.0 <= result.accuracy <= 1.0
        assert result.training_samples >= 50
        assert isinstance(result.feature_importance, list)
        assert isinstance(result.trained_at, str)


# =========================================
# MODEL METRICS
# =========================================

class TestModelMetrics:
    def test_untrained_model_metrics(self, model):
        metrics = model.get_model_metrics()
        assert isinstance(metrics, ModelMetrics)
        assert metrics.trained is False

    @pytest.mark.asyncio
    async def test_trained_model_metrics(self, model):
        await model.train(n_synthetic=50)
        metrics = model.get_model_metrics()
        assert metrics.trained is True
        assert metrics.total_samples > 0
        assert metrics.feature_count == 22


# =========================================
# SINGLETON
# =========================================

class TestSingleton:
    def test_get_win_model_returns_instance(self):
        m = get_win_model()
        assert isinstance(m, WinProbabilityModel)

    def test_get_win_model_is_singleton(self):
        m1 = get_win_model()
        m2 = get_win_model()
        assert m1 is m2
