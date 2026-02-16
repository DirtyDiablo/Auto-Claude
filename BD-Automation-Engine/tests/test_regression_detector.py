"""Tests for Phase 29A - Regression Detector."""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine8_Knowledge.optimization.regression_detector import (
    RegressionDetector,
    Regression,
    RollbackResult,
    ThresholdConfig,
    get_regression_detector,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def detector(tmp_path):
    """Create RegressionDetector with temp storage."""
    return RegressionDetector(storage_path=str(tmp_path))


@pytest.fixture
def detector_with_baselines(tmp_path):
    """Create RegressionDetector with pre-set baselines."""
    det = RegressionDetector(storage_path=str(tmp_path))
    det.set_baseline("search_relevance", 0.85)
    det.set_baseline("api_latency_p95", 120.0)
    det.set_baseline("model_f1", 0.78)
    return det


# =============================================================================
# Dataclass Tests
# =============================================================================


class TestRegressionDataclasses:
    """Tests for regression-related dataclasses."""

    def test_regression_fields(self):
        """Test Regression dataclass fields."""
        reg = Regression(
            regression_id="reg_0001",
            metric="search_relevance",
            severity="warning",
            current_value=0.72,
            baseline_value=0.85,
            change_pct=-0.15,
            detected_at="2025-01-01T00:00:00",
            caused_by="opt_0001",
            status="active",
        )
        assert reg.regression_id == "reg_0001"
        assert reg.severity == "warning"
        assert reg.status == "active"
        assert reg.caused_by == "opt_0001"

    def test_rollback_result_fields(self):
        """Test RollbackResult dataclass fields."""
        result = RollbackResult(
            regression_id="reg_0001",
            success=True,
            message="Rolled back successfully",
            rolled_back_optimization="opt_0001",
        )
        assert result.success is True
        assert result.rolled_back_optimization == "opt_0001"

    def test_threshold_config_defaults(self):
        """Test ThresholdConfig default thresholds."""
        config = ThresholdConfig(metric="test_metric")
        assert config.warning_threshold == 0.10
        assert config.critical_threshold == 0.25


# =============================================================================
# RegressionDetector Core Tests
# =============================================================================


class TestRegressionDetector:
    """Tests for RegressionDetector engine."""

    def test_initialization(self, tmp_path):
        """Test RegressionDetector initializes with empty state."""
        det = RegressionDetector(storage_path=str(tmp_path))
        assert det._regressions == []
        assert det._baselines == {}
        assert det._storage_path == str(tmp_path)

    def test_set_baseline(self, detector):
        """Test set_baseline stores a metric baseline value."""
        detector.set_baseline("search_relevance", 0.85)
        assert detector._baselines["search_relevance"] == 0.85

    def test_set_baseline_persists(self, tmp_path):
        """Test baselines are persisted to disk."""
        det1 = RegressionDetector(storage_path=str(tmp_path))
        det1.set_baseline("test_metric", 100.0)

        # Reload
        det2 = RegressionDetector(storage_path=str(tmp_path))
        assert det2._baselines.get("test_metric") == 100.0

    @pytest.mark.asyncio
    async def test_check_regressions_no_degradation(self, detector_with_baselines):
        """Test check_regressions returns empty list when metrics are stable."""
        current = {
            "search_relevance": 0.84,  # only ~1% drop, below warning threshold
            "api_latency_p95": 118.0,  # slight improvement
            "model_f1": 0.77,  # ~1.3% drop, below warning threshold
        }
        regressions = await detector_with_baselines.check_regressions(current)
        assert regressions == []

    @pytest.mark.asyncio
    async def test_check_regressions_warning_threshold(self, detector_with_baselines):
        """Test check_regressions detects warning-level regression."""
        current = {
            "search_relevance": 0.74,  # ~13% drop from 0.85 -> warning
            "api_latency_p95": 120.0,
            "model_f1": 0.78,
        }
        regressions = await detector_with_baselines.check_regressions(current)

        assert len(regressions) == 1
        assert regressions[0].metric == "search_relevance"
        assert regressions[0].severity == "warning"
        assert regressions[0].status == "active"

    @pytest.mark.asyncio
    async def test_check_regressions_critical_threshold(self, detector_with_baselines):
        """Test check_regressions detects critical-level regression."""
        current = {
            "search_relevance": 0.60,  # ~29% drop from 0.85 -> critical
            "api_latency_p95": 120.0,
            "model_f1": 0.78,
        }
        regressions = await detector_with_baselines.check_regressions(current)

        assert len(regressions) == 1
        assert regressions[0].metric == "search_relevance"
        assert regressions[0].severity == "critical"

    @pytest.mark.asyncio
    async def test_check_regressions_skips_unknown_baselines(self, detector):
        """Test check_regressions ignores metrics without baselines."""
        current = {"unknown_metric": 50.0}
        regressions = await detector.check_regressions(current)
        assert regressions == []

    @pytest.mark.asyncio
    async def test_auto_rollback_with_optimizer(self, detector):
        """Test auto_rollback calls optimizer.rollback when caused_by is set."""
        reg = Regression(
            regression_id="reg_0001",
            metric="search_relevance",
            severity="critical",
            current_value=0.60,
            baseline_value=0.85,
            change_pct=-0.29,
            caused_by="opt_0005",
        )

        mock_optimizer = MagicMock()
        mock_optimizer.rollback = AsyncMock(return_value=True)

        result = await detector.auto_rollback(reg, optimizer=mock_optimizer)

        assert result.success is True
        assert result.rolled_back_optimization == "opt_0005"
        assert reg.status == "rolled_back"
        mock_optimizer.rollback.assert_awaited_once_with("opt_0005")

    @pytest.mark.asyncio
    async def test_auto_rollback_without_optimizer(self, detector):
        """Test auto_rollback fails gracefully without an optimizer."""
        reg = Regression(
            regression_id="reg_0001",
            metric="test",
            severity="warning",
            current_value=50.0,
            baseline_value=100.0,
            change_pct=-0.50,
            caused_by="unknown",
        )

        result = await detector.auto_rollback(reg, optimizer=None)

        assert result.success is False
        assert "No associated optimization" in result.message

    @pytest.mark.asyncio
    async def test_resolve_marks_regression_resolved(self, detector):
        """Test resolve sets regression status to resolved."""
        reg = Regression(
            regression_id="reg_0001",
            metric="test",
            severity="warning",
            current_value=70.0,
            baseline_value=85.0,
            change_pct=-0.18,
        )
        detector._regressions.append(reg)

        success = await detector.resolve("reg_0001")

        assert success is True
        assert reg.status == "resolved"

    @pytest.mark.asyncio
    async def test_resolve_not_found(self, detector):
        """Test resolve returns False for nonexistent regression_id."""
        success = await detector.resolve("reg_9999")
        assert success is False


# =============================================================================
# Singleton Tests
# =============================================================================


class TestGetRegressionDetector:
    """Tests for the get_regression_detector singleton factory."""

    def test_get_regression_detector_returns_instance(self):
        """Test get_regression_detector returns a RegressionDetector instance."""
        import Engine8_Knowledge.optimization.regression_detector as mod

        original = mod._detector
        try:
            mod._detector = None
            instance = get_regression_detector()
            assert isinstance(instance, RegressionDetector)
        finally:
            mod._detector = original

    def test_get_regression_detector_returns_same_instance(self):
        """Test get_regression_detector returns the same singleton."""
        import Engine8_Knowledge.optimization.regression_detector as mod

        original = mod._detector
        try:
            mod._detector = None
            first = get_regression_detector()
            second = get_regression_detector()
            assert first is second
        finally:
            mod._detector = original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
