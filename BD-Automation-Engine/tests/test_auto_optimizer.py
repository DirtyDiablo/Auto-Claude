"""Tests for Phase 29A - Auto-Optimizer."""

import sys
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine8_Knowledge.optimization.auto_optimizer import (
    AutoOptimizer,
    Optimization,
    ApplyResult,
    SAFE_CATEGORIES,
    APPROVAL_REQUIRED,
    get_auto_optimizer,
)
from Engine8_Knowledge.optimization.self_assessment import (
    AssessmentReport,
    SubsystemStatus,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def optimizer(tmp_path):
    """Create AutoOptimizer with temp storage."""
    return AutoOptimizer(storage_path=str(tmp_path))


@pytest.fixture
def safe_optimization():
    """Create a safe optimization for testing."""
    return Optimization(
        opt_id="opt_0001",
        category="create_index",
        description="Add index to reduce latency",
        expected_impact="Reduce p95 latency by ~30%",
        risk_level="safe",
        parameters={"subsystem": "api_latency"},
    )


@pytest.fixture
def approval_optimization():
    """Create an approval-required optimization for testing."""
    return Optimization(
        opt_id="opt_0002",
        category="retrain_model",
        description="Retrain NER model with fresh data",
        expected_impact="Improve model accuracy by ~5-10%",
        risk_level="approval_required",
        parameters={"subsystem": "model_accuracy"},
    )


@pytest.fixture
def red_assessment():
    """Create an AssessmentReport with a red subsystem."""
    return AssessmentReport(
        report_id="assess_test",
        timestamp="2025-01-01T00:00:00",
        overall_status="red",
        overall_score=50.0,
        subsystems=[
            SubsystemStatus(name="api_latency", status="red", score=30.0),
            SubsystemStatus(name="model_accuracy", status="red", score=40.0),
            SubsystemStatus(name="memory_health", status="yellow", score=60.0),
            SubsystemStatus(name="search_quality", status="yellow", score=65.0),
            SubsystemStatus(name="data_freshness", status="red", score=35.0),
        ],
    )


# =============================================================================
# Optimization Dataclass Tests
# =============================================================================


class TestOptimizationDataclass:
    """Tests for Optimization and ApplyResult dataclasses."""

    def test_optimization_fields(self, safe_optimization):
        """Test Optimization dataclass fields."""
        assert safe_optimization.opt_id == "opt_0001"
        assert safe_optimization.category == "create_index"
        assert safe_optimization.risk_level == "safe"
        assert safe_optimization.status == "pending"

    def test_apply_result_fields(self):
        """Test ApplyResult dataclass fields."""
        result = ApplyResult(
            opt_id="opt_0001",
            success=True,
            message="Applied successfully",
            applied_at="2025-01-01T00:00:00",
            rollback_data={"category": "create_index"},
        )
        assert result.opt_id == "opt_0001"
        assert result.success is True
        assert result.rollback_data["category"] == "create_index"


# =============================================================================
# Category Constants Tests
# =============================================================================


class TestCategories:
    """Tests for safe vs approval-required category lists."""

    def test_safe_categories_list(self):
        """Test SAFE_CATEGORIES contains expected entries."""
        expected = [
            "create_index",
            "adjust_cache_ttl",
            "rewrite_query",
            "adjust_threshold",
            "cleanup_expired",
            "rebalance_vectors",
        ]
        assert SAFE_CATEGORIES == expected

    def test_approval_required_list(self):
        """Test APPROVAL_REQUIRED contains expected entries."""
        expected = [
            "retrain_model",
            "modify_schema",
            "change_workflow",
            "update_scoring",
        ]
        assert APPROVAL_REQUIRED == expected

    def test_no_overlap_between_safe_and_approval(self):
        """Test there is no overlap between safe and approval-required categories."""
        overlap = set(SAFE_CATEGORIES) & set(APPROVAL_REQUIRED)
        assert len(overlap) == 0, f"Overlapping categories: {overlap}"


# =============================================================================
# AutoOptimizer Core Tests
# =============================================================================


class TestAutoOptimizer:
    """Tests for AutoOptimizer engine."""

    def test_initialization(self, tmp_path):
        """Test AutoOptimizer initializes with empty state."""
        opt = AutoOptimizer(storage_path=str(tmp_path))
        assert opt._optimizations == []
        assert opt._applied == []
        assert opt._storage_path == str(tmp_path)

    @pytest.mark.asyncio
    async def test_generate_recommendations_from_assessment(
        self, optimizer, red_assessment
    ):
        """Test generate_recommendations produces optimizations from a red assessment."""
        recommendations = await optimizer.generate_recommendations(red_assessment)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        for rec in recommendations:
            assert isinstance(rec, Optimization)
            assert rec.opt_id.startswith("opt_")

    @pytest.mark.asyncio
    async def test_generate_recommendations_includes_api_latency_fix(
        self, optimizer, red_assessment
    ):
        """Test recommendations include create_index for red api_latency."""
        recs = await optimizer.generate_recommendations(red_assessment)
        api_recs = [r for r in recs if r.parameters.get("subsystem") == "api_latency"]
        assert len(api_recs) >= 1
        assert api_recs[0].category == "create_index"
        assert api_recs[0].risk_level == "safe"

    @pytest.mark.asyncio
    async def test_generate_recommendations_model_accuracy_needs_approval(
        self, optimizer, red_assessment
    ):
        """Test recommendations for red model_accuracy require approval."""
        recs = await optimizer.generate_recommendations(red_assessment)
        model_recs = [
            r for r in recs if r.parameters.get("subsystem") == "model_accuracy"
        ]
        assert len(model_recs) >= 1
        assert model_recs[0].category == "retrain_model"
        assert model_recs[0].risk_level == "approval_required"

    @pytest.mark.asyncio
    async def test_auto_apply_safe_optimization(self, optimizer, safe_optimization):
        """Test auto_apply succeeds for safe optimizations."""
        optimizer._optimizations.append(safe_optimization)

        result = await optimizer.auto_apply(safe_optimization)

        assert isinstance(result, ApplyResult)
        assert result.success is True
        assert result.opt_id == "opt_0001"
        assert safe_optimization.status == "applied"
        assert result.applied_at != ""

    @pytest.mark.asyncio
    async def test_auto_apply_rejects_non_safe(self, optimizer, approval_optimization):
        """Test auto_apply rejects approval-required optimizations."""
        result = await optimizer.auto_apply(approval_optimization)

        assert result.success is False
        assert "Requires approval" in result.message

    @pytest.mark.asyncio
    async def test_request_approval_sets_pending(
        self, optimizer, approval_optimization
    ):
        """Test request_approval sets status to pending_approval."""
        optimizer._optimizations.append(approval_optimization)

        opt_id = await optimizer.request_approval(approval_optimization)

        assert opt_id == "opt_0002"
        assert approval_optimization.status == "pending_approval"

    @pytest.mark.asyncio
    async def test_approve_applies_optimization(self, optimizer):
        """Test approve changes status and applies the optimization."""
        opt = Optimization(
            opt_id="opt_0010",
            category="create_index",
            description="Test",
            expected_impact="Test",
            risk_level="safe",
            status="pending_approval",
        )
        optimizer._optimizations.append(opt)

        result = await optimizer.approve("opt_0010")

        assert result.success is True
        assert opt.status == "applied"

    @pytest.mark.asyncio
    async def test_approve_not_found(self, optimizer):
        """Test approve returns failure for nonexistent opt_id."""
        result = await optimizer.approve("opt_9999")
        assert result.success is False
        assert "not found" in result.message

    @pytest.mark.asyncio
    async def test_rollback_applied_optimization(self, optimizer, safe_optimization):
        """Test rollback reverts an applied optimization."""
        optimizer._optimizations.append(safe_optimization)
        await optimizer.auto_apply(safe_optimization)
        assert safe_optimization.status == "applied"

        success = await optimizer.rollback("opt_0001")

        assert success is True
        assert safe_optimization.status == "rolled_back"

    @pytest.mark.asyncio
    async def test_rollback_not_found(self, optimizer):
        """Test rollback returns False for nonexistent opt_id."""
        success = await optimizer.rollback("opt_9999")
        assert success is False

    @pytest.mark.asyncio
    async def test_persistence_saves_and_loads(self, tmp_path):
        """Test optimizations persist to disk and can be reloaded."""
        opt1 = AutoOptimizer(storage_path=str(tmp_path))
        safe_opt = Optimization(
            opt_id="opt_0001",
            category="create_index",
            description="Test index",
            expected_impact="Faster",
            risk_level="safe",
        )
        opt1._optimizations.append(safe_opt)
        await opt1.auto_apply(safe_opt)

        # Reload from same path
        opt2 = AutoOptimizer(storage_path=str(tmp_path))
        assert len(opt2._optimizations) == 1
        assert opt2._optimizations[0].opt_id == "opt_0001"
        assert len(opt2._applied) == 1


# =============================================================================
# Singleton Tests
# =============================================================================


class TestGetAutoOptimizer:
    """Tests for the get_auto_optimizer singleton factory."""

    def test_get_auto_optimizer_returns_instance(self):
        """Test get_auto_optimizer returns an AutoOptimizer instance."""
        import Engine8_Knowledge.optimization.auto_optimizer as mod

        original = mod._optimizer
        try:
            mod._optimizer = None
            instance = get_auto_optimizer()
            assert isinstance(instance, AutoOptimizer)
        finally:
            mod._optimizer = original

    def test_get_auto_optimizer_returns_same_instance(self):
        """Test get_auto_optimizer returns the same singleton."""
        import Engine8_Knowledge.optimization.auto_optimizer as mod

        original = mod._optimizer
        try:
            mod._optimizer = None
            first = get_auto_optimizer()
            second = get_auto_optimizer()
            assert first is second
        finally:
            mod._optimizer = original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
