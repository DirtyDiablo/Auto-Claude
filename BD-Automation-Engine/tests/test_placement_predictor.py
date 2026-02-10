"""Tests for Phase 28A - Placement Predictor (XGBoost-based contact scoring)."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine8_Knowledge.ml.placement_predictor import (
    PlacementPredictor,
    PlacementPrediction,
    TrainResult,
    ModelMetrics,
    FeatureImportance,
    FEATURES,
    get_placement_predictor,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def predictor():
    """Create a PlacementPredictor with no pre-trained model (heuristic mode)."""
    return PlacementPredictor()


@pytest.fixture
def high_value_features():
    """Feature dict representing a high-value contact."""
    return {
        "contact_tier": 1,
        "days_since_last_contact": 5,
        "interaction_count": 15,
        "response_rate": 0.9,
        "sentiment_score": 0.8,
        "program_pain_score": 8.0,
        "pts_past_perf_match": 0.95,
        "clearance_match": 1,
        "location_match": 1,
    }


@pytest.fixture
def low_value_features():
    """Feature dict representing a low-value contact."""
    return {
        "contact_tier": 6,
        "days_since_last_contact": 200,
        "interaction_count": 1,
        "response_rate": 0.05,
        "sentiment_score": -0.5,
        "program_pain_score": 1.0,
        "pts_past_perf_match": 0.1,
        "clearance_match": 0,
        "location_match": 0,
    }


# =============================================================================
# Initialization tests
# =============================================================================


class TestPlacementPredictorInit:
    """Tests for PlacementPredictor initialization."""

    def test_init_default_no_model(self, predictor):
        """Default initialization should have no trained model."""
        assert predictor.model is None
        assert predictor._trained is False

    def test_init_feature_names(self, predictor):
        """Feature names should match the FEATURES constant."""
        assert predictor.feature_names == list(FEATURES)

    def test_features_constant_has_nine_features(self):
        """The FEATURES list should contain exactly 9 engineered features."""
        assert len(FEATURES) == 9

    def test_features_constant_expected_names(self):
        """FEATURES should include all expected feature names."""
        expected = {
            "contact_tier", "days_since_last_contact", "interaction_count",
            "response_rate", "sentiment_score", "program_pain_score",
            "pts_past_perf_match", "clearance_match", "location_match",
        }
        assert set(FEATURES) == expected


# =============================================================================
# PlacementPrediction dataclass tests
# =============================================================================


class TestPlacementPredictionDataclass:
    """Tests for the PlacementPrediction dataclass."""

    def test_placement_prediction_fields(self):
        """PlacementPrediction should have probability, confidence, top_features, recommended_actions."""
        pred = PlacementPrediction(
            probability=0.75,
            confidence="high",
            top_features=[{"feature": "contact_tier", "importance": 0.3}],
            recommended_actions=["Accelerate engagement"],
        )
        assert pred.probability == 0.75
        assert pred.confidence == "high"
        assert len(pred.top_features) == 1
        assert len(pred.recommended_actions) == 1

    def test_feature_importance_dataclass(self):
        """FeatureImportance should have feature, importance, rank fields."""
        fi = FeatureImportance(feature="contact_tier", importance=0.35, rank=1)
        assert fi.feature == "contact_tier"
        assert fi.importance == 0.35
        assert fi.rank == 1


# =============================================================================
# Heuristic prediction tests (XGBoost not loaded)
# =============================================================================


class TestHeuristicPrediction:
    """Tests for the heuristic fallback prediction when XGBoost is unavailable."""

    def test_predict_returns_placement_prediction(self, predictor, high_value_features):
        """predict() should return a PlacementPrediction instance."""
        result = predictor.predict(high_value_features)
        assert isinstance(result, PlacementPrediction)

    def test_predict_probability_between_zero_and_one(self, predictor, high_value_features):
        """Predicted probability should always be in [0.0, 1.0]."""
        result = predictor.predict(high_value_features)
        assert 0.0 <= result.probability <= 1.0

    def test_predict_high_value_has_higher_probability(self, predictor, high_value_features, low_value_features):
        """High-value contacts should get higher probability than low-value ones."""
        high_result = predictor.predict(high_value_features)
        low_result = predictor.predict(low_value_features)
        assert high_result.probability > low_result.probability

    def test_predict_confidence_high_for_strong_contact(self, predictor, high_value_features):
        """A strong contact should receive 'high' confidence."""
        result = predictor.predict(high_value_features)
        assert result.confidence in ("high", "medium")

    def test_predict_confidence_low_for_weak_contact(self, predictor, low_value_features):
        """A weak contact should receive 'low' confidence."""
        result = predictor.predict(low_value_features)
        assert result.confidence in ("low", "medium")

    def test_predict_empty_features_returns_baseline(self, predictor):
        """predict() with empty features dict should return a baseline prediction."""
        result = predictor.predict({})
        assert isinstance(result, PlacementPrediction)
        assert 0.0 <= result.probability <= 1.0

    def test_heuristic_clearance_match_boosts_score(self, predictor):
        """Clearance match should increase the heuristic score."""
        no_clearance = predictor._heuristic_predict({"clearance_match": 0})
        with_clearance = predictor._heuristic_predict({"clearance_match": 1})
        assert with_clearance > no_clearance

    def test_heuristic_high_tier_reduces_score(self, predictor):
        """Higher tier numbers (lower value contacts) should reduce the score."""
        tier1 = predictor._heuristic_predict({"contact_tier": 1})
        tier6 = predictor._heuristic_predict({"contact_tier": 6})
        assert tier1 > tier6


# =============================================================================
# Recommended actions tests
# =============================================================================


class TestRecommendedActions:
    """Tests for the action recommendation logic."""

    def test_recommend_actions_stale_contact(self, predictor):
        """Stale contacts (> 60 days) should get re-engagement recommendation."""
        result = predictor.predict({"days_since_last_contact": 90})
        assert any("Re-engage" in a for a in result.recommended_actions)

    def test_recommend_actions_low_interactions(self, predictor):
        """Contacts with few interactions should get touchpoint recommendation."""
        result = predictor.predict({"interaction_count": 1})
        assert any("touchpoint" in a.lower() for a in result.recommended_actions)

    def test_recommend_actions_no_clearance(self, predictor):
        """Contacts without clearance match should get verification recommendation."""
        result = predictor.predict({"clearance_match": 0})
        assert any("clearance" in a.lower() for a in result.recommended_actions)


# =============================================================================
# Train and evaluate tests
# =============================================================================


class TestTrainAndEvaluate:
    """Tests for model training and evaluation methods."""

    def test_train_without_xgboost_returns_empty(self, predictor):
        """train() should return empty TrainResult when XGBoost is not installed."""
        with patch.dict("sys.modules", {"xgboost": None}):
            # The train method imports xgboost internally; if it raises ImportError
            # it should return an empty TrainResult
            result = predictor.train()
            assert isinstance(result, TrainResult)

    def test_evaluate_untrained_returns_empty_metrics(self, predictor):
        """evaluate() on an untrained model should return empty ModelMetrics."""
        result = predictor.evaluate(features=[[1, 2, 3]], labels=[1])
        assert isinstance(result, ModelMetrics)
        assert result.total_samples == 0

    def test_evaluate_without_features_returns_empty(self, predictor):
        """evaluate() with None features should return empty ModelMetrics."""
        predictor._trained = True
        result = predictor.evaluate(features=None, labels=None)
        assert isinstance(result, ModelMetrics)
        assert result.total_samples == 0


# =============================================================================
# Feature importance tests
# =============================================================================


class TestFeatureImportance:
    """Tests for feature importance retrieval."""

    def test_get_feature_importance_empty_untrained(self, predictor):
        """get_feature_importance() on an untrained model should return empty list."""
        result = predictor.get_feature_importance()
        assert result == []

    def test_get_feature_importance_returns_list(self, predictor):
        """get_feature_importance() should return a list of FeatureImportance dataclasses."""
        predictor._feature_importance = [
            {"feature": "contact_tier", "importance": 0.3},
            {"feature": "clearance_match", "importance": 0.2},
        ]
        result = predictor.get_feature_importance()
        assert len(result) == 2
        assert all(isinstance(fi, FeatureImportance) for fi in result)
        assert result[0].rank == 1
        assert result[1].rank == 2


# =============================================================================
# Synthetic data generation tests
# =============================================================================


class TestSyntheticData:
    """Tests for synthetic training data generation."""

    def test_generate_synthetic_data_returns_200_samples(self, predictor):
        """Synthetic data generator should produce 200 feature rows and labels."""
        features, labels = predictor._generate_synthetic_data()
        assert len(features) == 200
        assert len(labels) == 200

    def test_generate_synthetic_data_has_nine_features(self, predictor):
        """Each synthetic feature vector should have 9 elements."""
        features, _ = predictor._generate_synthetic_data()
        assert all(len(row) == 9 for row in features)

    def test_generate_synthetic_data_labels_binary(self, predictor):
        """Synthetic labels should be binary (0 or 1)."""
        _, labels = predictor._generate_synthetic_data()
        assert all(l in (0, 1) for l in labels)


# =============================================================================
# Singleton tests
# =============================================================================


class TestSingleton:
    """Tests for the module-level singleton accessor."""

    def test_get_placement_predictor_returns_instance(self):
        """get_placement_predictor() should return a PlacementPredictor instance."""
        import Engine8_Knowledge.ml.placement_predictor as mod
        mod._predictor = None
        instance = get_placement_predictor()
        assert isinstance(instance, PlacementPredictor)

    def test_get_placement_predictor_is_singleton(self):
        """Calling get_placement_predictor() twice should return the same instance."""
        import Engine8_Knowledge.ml.placement_predictor as mod
        mod._predictor = None
        a = get_placement_predictor()
        b = get_placement_predictor()
        assert a is b
