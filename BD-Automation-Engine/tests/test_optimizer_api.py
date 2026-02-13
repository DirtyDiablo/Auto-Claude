"""Tests for Phase 29A - Optimizer API Router."""
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from Engine8_Knowledge.api_routers.optimizer_api import router
from Engine8_Knowledge.optimization.self_assessment import (
    SelfAssessment,
    AssessmentReport,
    SubsystemStatus,
    MetricTrend,
)
from Engine8_Knowledge.optimization.auto_optimizer import (
    AutoOptimizer,
    Optimization,
    ApplyResult,
)
from Engine8_Knowledge.optimization.regression_detector import (
    RegressionDetector,
    Regression,
)
from Engine8_Knowledge.optimization.retrain_orchestrator import (
    RetrainOrchestrator,
    RetrainResult,
    ModelDriftReport,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def app():
    """Create a FastAPI test app with the optimizer router."""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    """Create a TestClient for the optimizer API."""
    return TestClient(app)


@pytest.fixture
def mock_assessment():
    """Create a mock SelfAssessment instance."""
    sa = MagicMock(spec=SelfAssessment)
    report = AssessmentReport(
        report_id="assess_test_001",
        timestamp="2025-01-01T00:00:00",
        overall_status="green",
        overall_score=87.0,
        subsystems=[
            SubsystemStatus(name="api_latency", status="green", score=95.0),
            SubsystemStatus(name="search_quality", status="green", score=85.0),
        ],
        recommendations=[],
    )
    sa.run_full_assessment = AsyncMock(return_value=report)
    sa.get_assessment_history = AsyncMock(return_value=[report])
    sa.get_trend = AsyncMock(return_value=MetricTrend(
        metric="api_latency", data_points=[{"date": "2025-01-01", "value": 95.0}],
        trend="stable", current_value=95.0,
    ))
    return sa


@pytest.fixture
def mock_optimizer():
    """Create a mock AutoOptimizer instance."""
    opt = MagicMock(spec=AutoOptimizer)
    opt._optimizations = [
        Optimization(
            opt_id="opt_0001", category="create_index",
            description="Test", expected_impact="Test",
            risk_level="safe", status="pending",
        ),
    ]
    opt.get_optimization = MagicMock(return_value=Optimization(
        opt_id="opt_0001", category="create_index",
        description="Test", expected_impact="Test",
        risk_level="safe", status="pending",
    ))
    opt.auto_apply = AsyncMock(return_value=ApplyResult(
        opt_id="opt_0001", success=True, message="Applied create_index",
        applied_at="2025-01-01T00:00:00",
    ))
    opt.approve = AsyncMock(return_value=ApplyResult(
        opt_id="opt_0001", success=True, message="Approved and applied",
    ))
    opt.rollback = AsyncMock(return_value=True)
    return opt


@pytest.fixture
def mock_detector():
    """Create a mock RegressionDetector instance."""
    det = MagicMock(spec=RegressionDetector)
    det.get_active_regressions = AsyncMock(return_value=[
        Regression(
            regression_id="reg_0001", metric="search_relevance",
            severity="warning", current_value=0.72, baseline_value=0.85,
            change_pct=-0.15,
        ),
    ])
    return det


@pytest.fixture
def mock_retrain():
    """Create a mock RetrainOrchestrator instance."""
    retrain = MagicMock(spec=RetrainOrchestrator)
    retrain.orchestrate_retrain = AsyncMock(return_value=RetrainResult(
        model_name="defense_ner", success=True,
        old_metric=0.73, new_metric=0.80,
        improvement=0.096, duration_seconds=5.0,
    ))
    retrain.check_all_models = AsyncMock(return_value=[
        ModelDriftReport(
            model_name="defense_ner",
            current_metric=0.76, baseline_metric=0.78,
            drift_pct=0.026, needs_retrain=False,
        ),
    ])
    return retrain


# =============================================================================
# Router Structure Tests
# =============================================================================

class TestRouterStructure:
    """Tests for the optimizer API router structure."""

    def test_router_has_expected_routes(self):
        """Test that the router has all expected route paths."""
        route_paths = [r.path for r in router.routes]
        expected_paths = [
            "/optimizer/assess",
            "/optimizer/assessments",
            "/optimizer/trends/{metric}",
            "/optimizer/recommendations",
            "/optimizer/apply/{opt_id}",
            "/optimizer/approve/{opt_id}",
            "/optimizer/rollback/{opt_id}",
            "/optimizer/regressions",
            "/optimizer/retrain/{model}",
            "/optimizer/retrain/status",
        ]
        for path in expected_paths:
            assert path in route_paths, f"Missing route: {path}"

    def test_router_tag(self):
        """Test that the router uses the optimizer tag."""
        assert "optimizer" in router.tags


# =============================================================================
# Assessment Endpoint Tests
# =============================================================================

class TestAssessEndpoint:
    """Tests for the /optimizer/assess endpoint."""

    def test_assess_endpoint_success(self, client, mock_assessment):
        """Test POST /optimizer/assess returns assessment report."""
        with patch(
            "Engine8_Knowledge.api_routers.optimizer_api._get_assessment",
            return_value=mock_assessment,
        ):
            response = client.post("/optimizer/assess")

        assert response.status_code == 200
        data = response.json()
        assert data["report_id"] == "assess_test_001"
        assert data["overall_status"] == "green"
        assert len(data["subsystems"]) == 2

    def test_assess_endpoint_unavailable(self, client):
        """Test POST /optimizer/assess returns 503 when engine not available."""
        with patch(
            "Engine8_Knowledge.api_routers.optimizer_api._get_assessment",
            return_value=None,
        ):
            response = client.post("/optimizer/assess")

        assert response.status_code == 503


# =============================================================================
# Recommendations Endpoint Tests
# =============================================================================

class TestRecommendationsEndpoint:
    """Tests for the /optimizer/recommendations endpoint."""

    def test_recommendations_endpoint_success(self, client, mock_optimizer):
        """Test GET /optimizer/recommendations returns pending optimizations."""
        with patch(
            "Engine8_Knowledge.api_routers.optimizer_api._get_optimizer",
            return_value=mock_optimizer,
        ):
            response = client.get("/optimizer/recommendations")

        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert data["total"] == 1

    def test_recommendations_endpoint_unavailable(self, client):
        """Test GET /optimizer/recommendations returns empty when not available."""
        with patch(
            "Engine8_Knowledge.api_routers.optimizer_api._get_optimizer",
            return_value=None,
        ):
            response = client.get("/optimizer/recommendations")

        assert response.status_code == 200
        assert response.json() == {"recommendations": []}


# =============================================================================
# Apply Endpoint Tests
# =============================================================================

class TestApplyEndpoint:
    """Tests for the /optimizer/apply/{opt_id} endpoint."""

    def test_apply_endpoint_success(self, client, mock_optimizer):
        """Test POST /optimizer/apply/{opt_id} applies optimization."""
        with patch(
            "Engine8_Knowledge.api_routers.optimizer_api._get_optimizer",
            return_value=mock_optimizer,
        ):
            response = client.post("/optimizer/apply/opt_0001")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["opt_id"] == "opt_0001"

    def test_apply_endpoint_not_found(self, client, mock_optimizer):
        """Test POST /optimizer/apply/{opt_id} returns 404 for unknown ID."""
        mock_optimizer.get_optimization = MagicMock(return_value=None)
        with patch(
            "Engine8_Knowledge.api_routers.optimizer_api._get_optimizer",
            return_value=mock_optimizer,
        ):
            response = client.post("/optimizer/apply/opt_9999")

        assert response.status_code == 404


# =============================================================================
# Approve Endpoint Tests
# =============================================================================

class TestApproveEndpoint:
    """Tests for the /optimizer/approve/{opt_id} endpoint."""

    def test_approve_endpoint_success(self, client, mock_optimizer):
        """Test POST /optimizer/approve/{opt_id} approves and applies."""
        with patch(
            "Engine8_Knowledge.api_routers.optimizer_api._get_optimizer",
            return_value=mock_optimizer,
        ):
            response = client.post("/optimizer/approve/opt_0001")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


# =============================================================================
# Rollback Endpoint Tests
# =============================================================================

class TestRollbackEndpoint:
    """Tests for the /optimizer/rollback/{opt_id} endpoint."""

    def test_rollback_endpoint_success(self, client, mock_optimizer):
        """Test POST /optimizer/rollback/{opt_id} rolls back optimization."""
        with patch(
            "Engine8_Knowledge.api_routers.optimizer_api._get_optimizer",
            return_value=mock_optimizer,
        ):
            response = client.post("/optimizer/rollback/opt_0001")

        assert response.status_code == 200
        data = response.json()
        assert data["rolled_back"] is True
        assert data["opt_id"] == "opt_0001"

    def test_rollback_endpoint_not_found(self, client, mock_optimizer):
        """Test POST /optimizer/rollback/{opt_id} returns 404 on failure."""
        mock_optimizer.rollback = AsyncMock(return_value=False)
        with patch(
            "Engine8_Knowledge.api_routers.optimizer_api._get_optimizer",
            return_value=mock_optimizer,
        ):
            response = client.post("/optimizer/rollback/opt_9999")

        assert response.status_code == 404


# =============================================================================
# Regressions Endpoint Tests
# =============================================================================

class TestRegressionsEndpoint:
    """Tests for the /optimizer/regressions endpoint."""

    def test_regressions_endpoint_success(self, client, mock_detector):
        """Test GET /optimizer/regressions returns active regressions."""
        with patch(
            "Engine8_Knowledge.api_routers.optimizer_api._get_detector",
            return_value=mock_detector,
        ):
            response = client.get("/optimizer/regressions")

        assert response.status_code == 200
        data = response.json()
        assert len(data["regressions"]) == 1
        assert data["regressions"][0]["severity"] == "warning"
        assert data["total"] == 1

    def test_regressions_endpoint_unavailable(self, client):
        """Test GET /optimizer/regressions returns empty when not available."""
        with patch(
            "Engine8_Knowledge.api_routers.optimizer_api._get_detector",
            return_value=None,
        ):
            response = client.get("/optimizer/regressions")

        assert response.status_code == 200
        assert response.json() == {"regressions": []}


# =============================================================================
# Retrain Endpoint Tests
# =============================================================================

class TestRetrainEndpoint:
    """Tests for the /optimizer/retrain/{model} endpoint."""

    def test_retrain_endpoint_success(self, client, mock_retrain):
        """Test POST /optimizer/retrain/{model} triggers model retrain."""
        with patch(
            "Engine8_Knowledge.api_routers.optimizer_api._get_retrain",
            return_value=mock_retrain,
        ):
            response = client.post("/optimizer/retrain/defense_ner")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["model_name"] == "defense_ner"
        assert data["new_metric"] > data["old_metric"]

    def test_retrain_endpoint_unavailable(self, client):
        """Test POST /optimizer/retrain/{model} returns 503 when not available."""
        with patch(
            "Engine8_Knowledge.api_routers.optimizer_api._get_retrain",
            return_value=None,
        ):
            response = client.post("/optimizer/retrain/defense_ner")

        assert response.status_code == 503

    def test_retrain_status_endpoint(self, client, mock_retrain):
        """Test GET /optimizer/retrain/status returns model drift reports."""
        with patch(
            "Engine8_Knowledge.api_routers.optimizer_api._get_retrain",
            return_value=mock_retrain,
        ):
            response = client.get("/optimizer/retrain/status")

        assert response.status_code == 200
        data = response.json()
        assert len(data["models"]) == 1
        assert data["models"][0]["model_name"] == "defense_ner"
        assert data["total"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
