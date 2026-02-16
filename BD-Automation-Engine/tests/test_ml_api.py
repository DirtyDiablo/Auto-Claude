"""Tests for Phase 28A - ML API Router (FastAPI endpoints for NER, topics, prediction, embeddings)."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from dataclasses import dataclass, field

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from Engine8_Knowledge.api_routers.ml_api import router


# =============================================================================
# Test app setup
# =============================================================================


def _create_test_app() -> FastAPI:
    """Create a FastAPI app with the ML router mounted."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client():
    """FastAPI TestClient with the ML router."""
    app = _create_test_app()
    return TestClient(app)


# =============================================================================
# Mock helpers
# =============================================================================


def _make_mock_ner():
    """Create a mock DefenseNER that returns realistic entity data."""
    mock = MagicMock()
    mock._trained = True
    mock.ENTITY_TYPES = [
        "PROGRAM",
        "CONTRACT",
        "COMPANY",
        "INSTALLATION",
        "CLEARANCE",
        "NAICS",
        "ROLE_TITLE",
        "SET_ASIDE",
        "AGENCY",
        "VALUE",
    ]

    @dataclass
    class _Entity:
        text: str
        label: str
        start: int
        end: int
        confidence: float = 0.9

    mock.predict.return_value = [
        _Entity(text="GDIT", label="COMPANY", start=0, end=4, confidence=0.9),
        _Entity(text="TS/SCI", label="CLEARANCE", start=20, end=26, confidence=0.9),
    ]

    @dataclass
    class _NERMetrics:
        precision: float = 0.0
        recall: float = 0.0
        f1: float = 0.0
        per_entity: dict = field(default_factory=dict)
        total_examples: int = 10

    mock.generate_training_data.return_value = []
    mock.train.return_value = _NERMetrics()
    return mock


def _make_mock_modeler():
    """Create a mock TopicModeler that returns realistic topic data."""
    mock = MagicMock()

    @dataclass
    class _TopicInfo:
        topic_id: int
        name: str
        keywords: list
        size: int
        representative_docs: list = field(default_factory=list)

    @dataclass
    class _TopicResult:
        topics: list
        total_documents: int
        total_topics: int
        outlier_count: int = 0
        model_type: str = "keyword_fallback"

    @dataclass
    class _TopicTrend:
        topic_id: int
        topic_name: str
        data_points: list
        trend: str = "stable"

    result = _TopicResult(
        topics=[_TopicInfo(topic_id=0, name="dcgs", keywords=["dcgs"], size=5)],
        total_documents=5,
        total_topics=1,
    )
    mock.cluster_jobs = AsyncMock(return_value=result)
    mock.cluster_notes = AsyncMock(return_value=result)
    mock.get_topic_trends = AsyncMock(
        return_value=_TopicTrend(topic_id=0, topic_name="dcgs", data_points=[])
    )
    return mock


def _make_mock_predictor():
    """Create a mock PlacementPredictor that returns realistic predictions."""
    mock = MagicMock()
    mock._trained = True
    mock.feature_names = [
        "contact_tier",
        "days_since_last_contact",
        "interaction_count",
        "response_rate",
        "sentiment_score",
        "program_pain_score",
        "pts_past_perf_match",
        "clearance_match",
        "location_match",
    ]

    @dataclass
    class _PlacementPrediction:
        probability: float
        confidence: str
        top_features: list
        recommended_actions: list

    @dataclass
    class _TrainResult:
        accuracy: float = 0.85
        auc: float = 0.85
        f1: float = 0.85
        feature_importance: list = field(default_factory=list)
        training_samples: int = 200
        cv_scores: list = field(default_factory=list)

    @dataclass
    class _FeatureImportance:
        feature: str
        importance: float
        rank: int

    mock.predict.return_value = _PlacementPrediction(
        probability=0.75,
        confidence="high",
        top_features=[],
        recommended_actions=["Accelerate engagement"],
    )
    mock.train.return_value = _TrainResult()
    mock.get_feature_importance.return_value = [
        _FeatureImportance(feature="contact_tier", importance=0.3, rank=1),
    ]
    return mock


def _make_mock_adapter():
    """Create a mock DomainAdapterV2 that returns realistic benchmark data."""
    mock = MagicMock()

    @dataclass
    class _BenchmarkResult:
        avg_precision: float = 0.85
        avg_recall: float = 0.80
        avg_mrr: float = 0.82
        queries_tested: int = 5
        improvements_over_v1: float = 0.0

    mock.train_with_hard_negatives.return_value = {
        "status": "trained",
        "pairs": 0,
        "epochs": 10,
        "hard_negatives": 0,
    }
    mock.evaluate_on_benchmark.return_value = _BenchmarkResult()
    return mock


# =============================================================================
# Router structure tests
# =============================================================================


class TestRouterStructure:
    """Tests for the ML API router configuration."""

    def test_router_has_expected_routes(self):
        """Router should have all 12 expected route paths."""
        paths = [route.path for route in router.routes]
        expected_paths = [
            "/ml/ner/predict",
            "/ml/ner/train",
            "/ml/ner/metrics",
            "/ml/topics/cluster-jobs",
            "/ml/topics/cluster-notes",
            "/ml/topics/trends/{topic_id}",
            "/ml/predict/placement",
            "/ml/predict/train",
            "/ml/predict/feature-importance",
            "/ml/predict/metrics",
            "/ml/embeddings/train",
            "/ml/embeddings/benchmark",
        ]
        for ep in expected_paths:
            assert ep in paths, f"Missing route: {ep}"

    def test_router_tag(self):
        """Router should have the 'ml-v2' tag."""
        assert "ml-v2" in router.tags


# =============================================================================
# NER endpoint tests
# =============================================================================


class TestNEREndpoints:
    """Tests for the NER prediction and training endpoints."""

    def test_ner_predict_returns_entities(self, client):
        """POST /ml/ner/predict should return extracted entities."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_ner",
            return_value=_make_mock_ner(),
        ):
            resp = client.post(
                "/ml/ner/predict", json={"text": "GDIT requires TS/SCI clearance"}
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "entities" in data
        assert "count" in data
        assert data["count"] == 2

    def test_ner_predict_unavailable(self, client):
        """POST /ml/ner/predict should return 503 when NER is unavailable."""
        with patch("Engine8_Knowledge.api_routers.ml_api._get_ner", return_value=None):
            resp = client.post("/ml/ner/predict", json={"text": "test"})
        assert resp.status_code == 503

    def test_ner_train_endpoint(self, client):
        """POST /ml/ner/train should train and return metrics."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_ner",
            return_value=_make_mock_ner(),
        ):
            resp = client.post("/ml/ner/train", json={"epochs": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert "precision" in data
        assert "recall" in data
        assert "f1" in data

    def test_ner_metrics_endpoint(self, client):
        """GET /ml/ner/metrics should return model status and entity types."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_ner",
            return_value=_make_mock_ner(),
        ):
            resp = client.get("/ml/ner/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trained"] is True
        assert "entity_types" in data

    def test_ner_metrics_unavailable(self, client):
        """GET /ml/ner/metrics should return trained=False when NER is unavailable."""
        with patch("Engine8_Knowledge.api_routers.ml_api._get_ner", return_value=None):
            resp = client.get("/ml/ner/metrics")
        assert resp.status_code == 200
        assert resp.json()["trained"] is False


# =============================================================================
# Topic endpoints tests
# =============================================================================


class TestTopicEndpoints:
    """Tests for the topic clustering and trend endpoints."""

    def test_cluster_jobs_endpoint(self, client):
        """POST /ml/topics/cluster-jobs should return topic clusters."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_modeler",
            return_value=_make_mock_modeler(),
        ):
            resp = client.post(
                "/ml/topics/cluster-jobs",
                json={
                    "documents": ["DCGS analyst job", "ISR engineer position"],
                    "days": 90,
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "topics" in data
        assert "total_documents" in data
        assert "total_topics" in data

    def test_cluster_notes_endpoint(self, client):
        """POST /ml/topics/cluster-notes should return topic clusters."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_modeler",
            return_value=_make_mock_modeler(),
        ):
            resp = client.post(
                "/ml/topics/cluster-notes",
                json={"documents": ["Call with Leidos PM"], "days": 180},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "topics" in data

    def test_cluster_jobs_unavailable(self, client):
        """POST /ml/topics/cluster-jobs should return 503 when modeler is unavailable."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_modeler", return_value=None
        ):
            resp = client.post("/ml/topics/cluster-jobs", json={"documents": []})
        assert resp.status_code == 503

    def test_topic_trends_endpoint(self, client):
        """GET /ml/topics/trends/{topic_id} should return trend data."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_modeler",
            return_value=_make_mock_modeler(),
        ):
            resp = client.get("/ml/topics/trends/0?days=90")
        assert resp.status_code == 200
        data = resp.json()
        assert "topic_id" in data
        assert "topic_name" in data
        assert "trend" in data


# =============================================================================
# Placement prediction endpoint tests
# =============================================================================


class TestPlacementEndpoints:
    """Tests for the placement prediction and training endpoints."""

    def test_predict_placement_endpoint(self, client):
        """POST /ml/predict/placement should return a prediction."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_predictor",
            return_value=_make_mock_predictor(),
        ):
            resp = client.post(
                "/ml/predict/placement",
                json={
                    "contact_tier": 2,
                    "days_since_last_contact": 10,
                    "interaction_count": 8,
                    "response_rate": 0.7,
                    "sentiment_score": 0.5,
                    "program_pain_score": 6.0,
                    "pts_past_perf_match": 0.8,
                    "clearance_match": 1,
                    "location_match": 1,
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "probability" in data
        assert "confidence" in data
        assert "recommended_actions" in data

    def test_predict_placement_unavailable(self, client):
        """POST /ml/predict/placement should return 503 when predictor is unavailable."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_predictor", return_value=None
        ):
            resp = client.post("/ml/predict/placement", json={})
        assert resp.status_code == 503

    def test_train_predictor_endpoint(self, client):
        """POST /ml/predict/train should train and return results."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_predictor",
            return_value=_make_mock_predictor(),
        ):
            resp = client.post("/ml/predict/train")
        assert resp.status_code == 200
        data = resp.json()
        assert "accuracy" in data
        assert "training_samples" in data

    def test_feature_importance_endpoint(self, client):
        """GET /ml/predict/feature-importance should return feature rankings."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_predictor",
            return_value=_make_mock_predictor(),
        ):
            resp = client.get("/ml/predict/feature-importance")
        assert resp.status_code == 200
        data = resp.json()
        assert "features" in data
        assert len(data["features"]) > 0

    def test_predictor_metrics_endpoint(self, client):
        """GET /ml/predict/metrics should return model status."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_predictor",
            return_value=_make_mock_predictor(),
        ):
            resp = client.get("/ml/predict/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trained"] is True
        assert "features" in data

    def test_predictor_metrics_unavailable(self, client):
        """GET /ml/predict/metrics should return trained=False when unavailable."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_predictor", return_value=None
        ):
            resp = client.get("/ml/predict/metrics")
        assert resp.status_code == 200
        assert resp.json()["trained"] is False


# =============================================================================
# Embeddings endpoint tests
# =============================================================================


class TestEmbeddingsEndpoints:
    """Tests for the embeddings training and benchmark endpoints."""

    def test_train_embeddings_endpoint(self, client):
        """POST /ml/embeddings/train should start training and return status."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_adapter",
            return_value=_make_mock_adapter(),
        ):
            resp = client.post("/ml/embeddings/train", json={"epochs": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "trained"

    def test_train_embeddings_unavailable(self, client):
        """POST /ml/embeddings/train should return 503 when adapter is unavailable."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_adapter", return_value=None
        ):
            resp = client.post("/ml/embeddings/train", json={"epochs": 5})
        assert resp.status_code == 503

    def test_embeddings_benchmark_endpoint(self, client):
        """GET /ml/embeddings/benchmark should return benchmark metrics."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_adapter",
            return_value=_make_mock_adapter(),
        ):
            resp = client.get("/ml/embeddings/benchmark")
        assert resp.status_code == 200
        data = resp.json()
        assert "avg_precision" in data
        assert "avg_recall" in data
        assert "avg_mrr" in data
        assert "queries_tested" in data

    def test_embeddings_benchmark_unavailable(self, client):
        """GET /ml/embeddings/benchmark should return unavailable status when adapter is missing."""
        with patch(
            "Engine8_Knowledge.api_routers.ml_api._get_adapter", return_value=None
        ):
            resp = client.get("/ml/embeddings/benchmark")
        assert resp.status_code == 200
        assert resp.json()["status"] == "unavailable"
