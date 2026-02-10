"""Tests for Phase 29A - Retrain Orchestrator."""
import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from dataclasses import asdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine8_Knowledge.optimization.retrain_orchestrator import (
    RetrainOrchestrator,
    ModelDriftReport,
    RetrainResult,
    REGISTERED_MODELS,
    get_retrain_orchestrator,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def orchestrator(tmp_path):
    """Create RetrainOrchestrator with temp storage."""
    return RetrainOrchestrator(storage_path=str(tmp_path))


# =============================================================================
# Dataclass Tests
# =============================================================================

class TestRetrainDataclasses:
    """Tests for retrain-related dataclasses."""

    def test_model_drift_report_fields(self):
        """Test ModelDriftReport dataclass fields."""
        report = ModelDriftReport(
            model_name="defense_ner",
            current_metric=0.73,
            baseline_metric=0.78,
            drift_pct=0.064,
            needs_retrain=True,
            last_trained="2025-01-01",
            last_checked="2025-06-01",
        )
        assert report.model_name == "defense_ner"
        assert report.needs_retrain is True
        assert report.drift_pct == 0.064

    def test_retrain_result_fields(self):
        """Test RetrainResult dataclass fields."""
        result = RetrainResult(
            model_name="defense_ner",
            success=True,
            old_metric=0.73,
            new_metric=0.80,
            improvement=0.096,
            duration_seconds=120.5,
            status="completed",
        )
        assert result.model_name == "defense_ner"
        assert result.success is True
        assert result.status == "completed"

    def test_retrain_result_defaults(self):
        """Test RetrainResult default values."""
        result = RetrainResult(model_name="test", success=False)
        assert result.old_metric == 0.0
        assert result.new_metric == 0.0
        assert result.improvement == 0.0
        assert result.duration_seconds == 0.0
        assert result.status == "completed"


# =============================================================================
# REGISTERED_MODELS Tests
# =============================================================================

class TestRegisteredModels:
    """Tests for the REGISTERED_MODELS constant."""

    def test_registered_models_count(self):
        """Test that exactly 5 models are registered."""
        assert len(REGISTERED_MODELS) == 5

    def test_registered_model_names(self):
        """Test all expected model names are present."""
        expected = [
            "defense_ner",
            "placement_predictor",
            "topic_modeler",
            "domain_adapter",
            "response_predictor",
        ]
        for name in expected:
            assert name in REGISTERED_MODELS, f"Missing model: {name}"

    def test_registered_models_have_required_keys(self):
        """Test each model config has metric, baseline, and threshold keys."""
        for name, config in REGISTERED_MODELS.items():
            assert "metric" in config, f"{name} missing 'metric'"
            assert "baseline" in config, f"{name} missing 'baseline'"
            assert "threshold" in config, f"{name} missing 'threshold'"
            assert isinstance(config["baseline"], (int, float))
            assert isinstance(config["threshold"], (int, float))


# =============================================================================
# RetrainOrchestrator Core Tests
# =============================================================================

class TestRetrainOrchestrator:
    """Tests for RetrainOrchestrator engine."""

    def test_initialization(self, tmp_path):
        """Test RetrainOrchestrator initializes with registered models."""
        orch = RetrainOrchestrator(storage_path=str(tmp_path))
        assert len(orch._models) == 5
        assert orch._retrain_history == []
        assert orch._storage_path == str(tmp_path)

    def test_get_registered_models(self, orchestrator):
        """Test get_registered_models returns a copy of models dict."""
        models = orchestrator.get_registered_models()
        assert isinstance(models, dict)
        assert len(models) == 5
        assert "defense_ner" in models
        # Ensure it is a copy, not the original
        models["new_model"] = {}
        assert "new_model" not in orchestrator._models

    @pytest.mark.asyncio
    async def test_check_all_models_returns_drift_reports(self, orchestrator):
        """Test check_all_models returns ModelDriftReport for each model."""
        reports = await orchestrator.check_all_models()

        assert isinstance(reports, list)
        assert len(reports) == 5
        for report in reports:
            assert isinstance(report, ModelDriftReport)
            assert report.model_name in REGISTERED_MODELS
            assert report.last_checked != ""

    @pytest.mark.asyncio
    async def test_check_all_models_drift_values(self, orchestrator):
        """Test check_all_models computes drift correctly (simulated 3% degradation)."""
        reports = await orchestrator.check_all_models()

        for report in reports:
            config = REGISTERED_MODELS[report.model_name]
            expected_current = config["baseline"] * 0.97
            assert abs(report.current_metric - expected_current) < 0.001
            assert report.baseline_metric == config["baseline"]
            # 3% drift should be below 5% threshold for most models
            assert abs(report.drift_pct - 0.03) < 0.01

    @pytest.mark.asyncio
    async def test_orchestrate_retrain_known_model(self, orchestrator):
        """Test orchestrate_retrain succeeds for a known model."""
        result = await orchestrator.orchestrate_retrain("defense_ner")

        assert isinstance(result, RetrainResult)
        assert result.success is True
        assert result.model_name == "defense_ner"
        assert result.status == "completed"
        assert result.new_metric > result.old_metric
        assert result.improvement > 0
        assert result.duration_seconds > 0

    @pytest.mark.asyncio
    async def test_orchestrate_retrain_unknown_model(self, orchestrator):
        """Test orchestrate_retrain fails for unknown model."""
        result = await orchestrator.orchestrate_retrain("nonexistent_model")

        assert result.success is False
        assert result.status == "failed"
        assert result.model_name == "nonexistent_model"

    @pytest.mark.asyncio
    async def test_orchestrate_retrain_appends_to_history(self, orchestrator):
        """Test retrain results are added to history."""
        assert len(orchestrator._retrain_history) == 0

        await orchestrator.orchestrate_retrain("defense_ner")
        assert len(orchestrator._retrain_history) == 1

        await orchestrator.orchestrate_retrain("topic_modeler")
        assert len(orchestrator._retrain_history) == 2

    @pytest.mark.asyncio
    async def test_schedule_retrains_returns_model_names(self, orchestrator):
        """Test schedule_retrains returns list of model names needing retrain."""
        scheduled = await orchestrator.schedule_retrains()

        assert isinstance(scheduled, list)
        # With 3% simulated drift, models with threshold=0.05 should NOT need retrain
        # but topic_modeler has threshold=0.10 so also should not
        # All default simulated drift is 3%, all thresholds >= 5%, so none should need retrain
        for name in scheduled:
            assert name in REGISTERED_MODELS

    @pytest.mark.asyncio
    async def test_get_retrain_history_all(self, orchestrator):
        """Test get_retrain_history returns all results."""
        await orchestrator.orchestrate_retrain("defense_ner")
        await orchestrator.orchestrate_retrain("topic_modeler")

        history = await orchestrator.get_retrain_history()
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_get_retrain_history_filtered(self, orchestrator):
        """Test get_retrain_history filtered by model_name."""
        await orchestrator.orchestrate_retrain("defense_ner")
        await orchestrator.orchestrate_retrain("topic_modeler")

        history = await orchestrator.get_retrain_history(model_name="defense_ner")
        assert len(history) == 1
        assert history[0].model_name == "defense_ner"

    @pytest.mark.asyncio
    async def test_persistence_saves_and_loads(self, tmp_path):
        """Test retrain history persists to disk and reloads."""
        orch1 = RetrainOrchestrator(storage_path=str(tmp_path))
        await orch1.orchestrate_retrain("defense_ner")

        # Reload from same path
        orch2 = RetrainOrchestrator(storage_path=str(tmp_path))
        assert len(orch2._retrain_history) == 1
        assert orch2._retrain_history[0].model_name == "defense_ner"


# =============================================================================
# Singleton Tests
# =============================================================================

class TestGetRetrainOrchestrator:
    """Tests for the get_retrain_orchestrator singleton factory."""

    def test_get_retrain_orchestrator_returns_instance(self):
        """Test get_retrain_orchestrator returns a RetrainOrchestrator instance."""
        import Engine8_Knowledge.optimization.retrain_orchestrator as mod
        original = mod._orchestrator
        try:
            mod._orchestrator = None
            instance = get_retrain_orchestrator()
            assert isinstance(instance, RetrainOrchestrator)
        finally:
            mod._orchestrator = original

    def test_get_retrain_orchestrator_returns_same_instance(self):
        """Test get_retrain_orchestrator returns the same singleton."""
        import Engine8_Knowledge.optimization.retrain_orchestrator as mod
        original = mod._orchestrator
        try:
            mod._orchestrator = None
            first = get_retrain_orchestrator()
            second = get_retrain_orchestrator()
            assert first is second
        finally:
            mod._orchestrator = original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
