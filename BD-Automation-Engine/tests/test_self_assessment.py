"""Tests for Phase 29A - Self-Assessment Engine."""
import os
import sys
import json
import asyncio
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from dataclasses import asdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine8_Knowledge.optimization.self_assessment import (
    SelfAssessment,
    SubsystemStatus,
    AssessmentReport,
    MetricTrend,
    get_self_assessment,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def assessment(tmp_path):
    """Create SelfAssessment with temp storage."""
    return SelfAssessment(storage_path=str(tmp_path))


@pytest.fixture
def assessment_no_storage():
    """Create SelfAssessment without storage."""
    return SelfAssessment(storage_path=None)


# =============================================================================
# SubsystemStatus Dataclass Tests
# =============================================================================

class TestSubsystemStatus:
    """Tests for the SubsystemStatus dataclass."""

    def test_subsystem_status_fields(self):
        """Test SubsystemStatus has all expected fields with correct types."""
        status = SubsystemStatus(
            name="api_latency",
            status="green",
            score=95.0,
            metrics={"p50_ms": 45, "p95_ms": 120},
            issues=["High p99 latency"],
        )
        assert status.name == "api_latency"
        assert status.status == "green"
        assert status.score == 95.0
        assert status.metrics == {"p50_ms": 45, "p95_ms": 120}
        assert status.issues == ["High p99 latency"]

    def test_subsystem_status_defaults(self):
        """Test SubsystemStatus default values for metrics and issues."""
        status = SubsystemStatus(name="test", status="green", score=80.0)
        assert status.metrics == {}
        assert status.issues == []


# =============================================================================
# AssessmentReport Dataclass Tests
# =============================================================================

class TestAssessmentReport:
    """Tests for the AssessmentReport dataclass."""

    def test_assessment_report_defaults(self):
        """Test AssessmentReport default field values."""
        report = AssessmentReport()
        assert report.report_id == ""
        assert report.timestamp == ""
        assert report.overall_status == "green"
        assert report.overall_score == 100.0
        assert report.subsystems == []
        assert report.recommendations == []

    def test_assessment_report_serialization(self):
        """Test AssessmentReport can be converted to dict."""
        sub = SubsystemStatus(name="test_sub", status="green", score=90.0)
        report = AssessmentReport(
            report_id="assess_001",
            timestamp="2025-01-01T00:00:00",
            overall_status="green",
            overall_score=90.0,
            subsystems=[sub],
            recommendations=["Consider upgrading cache"],
        )
        data = asdict(report)
        assert data["report_id"] == "assess_001"
        assert len(data["subsystems"]) == 1
        assert data["subsystems"][0]["name"] == "test_sub"


# =============================================================================
# SelfAssessment Core Tests
# =============================================================================

class TestSelfAssessment:
    """Tests for the SelfAssessment engine."""

    def test_initialization_with_storage(self, tmp_path):
        """Test SelfAssessment initializes with storage path."""
        sa = SelfAssessment(storage_path=str(tmp_path))
        assert sa._storage_path == str(tmp_path)
        assert sa._history == []

    def test_initialization_without_storage(self):
        """Test SelfAssessment initializes without storage path."""
        sa = SelfAssessment(storage_path=None)
        assert sa._storage_path is None
        assert sa._history == []

    @pytest.mark.asyncio
    async def test_run_full_assessment_returns_report(self, assessment):
        """Test run_full_assessment returns an AssessmentReport with 7 subsystems."""
        report = await assessment.run_full_assessment()

        assert isinstance(report, AssessmentReport)
        assert len(report.subsystems) == 7
        assert report.report_id.startswith("assess_")
        assert report.timestamp != ""

    @pytest.mark.asyncio
    async def test_run_full_assessment_subsystem_names(self, assessment):
        """Test that all 7 expected subsystems are checked."""
        report = await assessment.run_full_assessment()
        subsystem_names = [s.name for s in report.subsystems]

        expected_names = [
            "api_latency",
            "search_quality",
            "memory_health",
            "workflow_health",
            "model_accuracy",
            "data_freshness",
            "database_health",
        ]
        assert subsystem_names == expected_names

    @pytest.mark.asyncio
    async def test_overall_status_green_when_all_green(self, assessment):
        """Test overall_status is green when all subsystems are green."""
        report = await assessment.run_full_assessment()
        # Default stubs all return green status
        assert report.overall_status == "green"

    @pytest.mark.asyncio
    async def test_overall_status_red_when_any_red(self, assessment):
        """Test overall_status is red when any subsystem is red."""
        async def fake_check_api_latency():
            return SubsystemStatus(name="api_latency", status="red", score=30.0,
                                   issues=["API latency critical"])

        assessment._check_api_latency = fake_check_api_latency
        report = await assessment.run_full_assessment()
        assert report.overall_status == "red"

    @pytest.mark.asyncio
    async def test_overall_status_yellow_when_multiple_yellow(self, assessment):
        """Test overall_status is yellow when more than one subsystem is yellow."""
        async def fake_check_search():
            return SubsystemStatus(name="search_quality", status="yellow", score=60.0)

        async def fake_check_memory():
            return SubsystemStatus(name="memory_health", status="yellow", score=55.0)

        assessment._check_search_quality = fake_check_search
        assessment._check_memory_health = fake_check_memory
        report = await assessment.run_full_assessment()
        assert report.overall_status == "yellow"

    @pytest.mark.asyncio
    async def test_overall_score_is_average(self, assessment):
        """Test overall_score is the mean of all subsystem scores."""
        report = await assessment.run_full_assessment()
        expected_avg = sum(s.score for s in report.subsystems) / len(report.subsystems)
        assert abs(report.overall_score - expected_avg) < 0.01

    @pytest.mark.asyncio
    async def test_assessment_persists_to_history(self, assessment):
        """Test that assessments are appended to history."""
        assert len(assessment._history) == 0
        await assessment.run_full_assessment()
        assert len(assessment._history) == 1
        await assessment.run_full_assessment()
        assert len(assessment._history) == 2

    @pytest.mark.asyncio
    async def test_assessment_saves_to_disk(self, tmp_path):
        """Test that assessment history is saved to storage_path."""
        sa = SelfAssessment(storage_path=str(tmp_path))
        await sa.run_full_assessment()

        saved_file = tmp_path / "assessments.json"
        assert saved_file.exists()
        data = json.loads(saved_file.read_text())
        assert len(data) == 1
        assert data[0]["report_id"].startswith("assess_")

    @pytest.mark.asyncio
    async def test_get_assessment_history(self, assessment):
        """Test get_assessment_history returns list of recent reports."""
        await assessment.run_full_assessment()
        await assessment.run_full_assessment()

        history = await assessment.get_assessment_history(weeks=12)
        assert isinstance(history, list)
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_get_trend_returns_metric_trend(self, assessment):
        """Test get_trend returns a MetricTrend object."""
        await assessment.run_full_assessment()

        trend = await assessment.get_trend("api_latency", weeks=12)
        assert isinstance(trend, MetricTrend)
        assert trend.metric == "api_latency"
        assert trend.trend in ("stable", "improving", "declining")


# =============================================================================
# Singleton Tests
# =============================================================================

class TestGetSelfAssessment:
    """Tests for the get_self_assessment singleton factory."""

    def test_get_self_assessment_returns_instance(self):
        """Test get_self_assessment returns a SelfAssessment instance."""
        import Engine8_Knowledge.optimization.self_assessment as mod
        original = mod._assessment
        try:
            mod._assessment = None
            instance = get_self_assessment()
            assert isinstance(instance, SelfAssessment)
        finally:
            mod._assessment = original

    def test_get_self_assessment_returns_same_instance(self):
        """Test get_self_assessment returns the same singleton."""
        import Engine8_Knowledge.optimization.self_assessment as mod
        original = mod._assessment
        try:
            mod._assessment = None
            first = get_self_assessment()
            second = get_self_assessment()
            assert first is second
        finally:
            mod._assessment = original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
