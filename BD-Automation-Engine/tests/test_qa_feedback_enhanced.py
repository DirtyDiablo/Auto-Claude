"""
Enhanced Test Suite for Engine 6: QA Feedback
Tests QA evaluation, review queues, and root cause analysis.

Following TDD pattern and Systematic Debugging from Superpowers:
- Tests verify root cause analysis identifies issue types correctly
- Tests verify severity classification
- Tests verify auto-fixable detection
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRootCauseAnalysis:
    """Tests for root cause analysis functionality."""

    @pytest.fixture
    def low_confidence_job(self):
        """Job with low mapping confidence."""
        return {
            'Job Title/Position': 'Software Developer',
            'Prime Contractor': 'Unknown Corp',
            '_mapping': {
                'program_name': 'Generic Program',
                'match_confidence': 0.35
            }
        }

    @pytest.fixture
    def missing_data_job(self):
        """Job with missing required fields."""
        return {
            'Job Title/Position': 'Intelligence Analyst',
            'Security Clearance': '',  # Missing
            'Location': '',  # Missing
            '_mapping': {
                'program_name': 'DCGS',
                'match_confidence': 0.80
            }
        }

    @pytest.fixture
    def invalid_mapping_job(self):
        """Job with invalid program mapping."""
        return {
            'Job Title/Position': 'Systems Engineer',
            'Security Clearance': 'Secret',
            'Location': 'Washington, DC',
            '_mapping': {
                'program_name': 'Unmatched',
                'match_confidence': 0.0
            }
        }

    @pytest.fixture
    def good_job(self):
        """Job that should pass QA."""
        return {
            'Job Title/Position': 'Senior Analyst - DCGS',
            'Security Clearance': 'TS/SCI',
            'Location': 'San Diego, CA',
            'Prime Contractor': 'Leidos',
            '_mapping': {
                'program_name': 'AF DCGS - PACAF',
                'match_confidence': 0.92
            }
        }

    def test_analyze_root_cause_exists(self):
        """Test analyze_root_cause function exists."""
        try:
            from Engine6_QA.scripts.qa_feedback import analyze_root_cause
            assert analyze_root_cause is not None
        except ImportError:
            pytest.skip("analyze_root_cause not available")

    def test_low_confidence_root_cause(self, low_confidence_job):
        """Test root cause identifies low confidence issue."""
        try:
            from Engine6_QA.scripts.qa_feedback import analyze_root_cause

            result = analyze_root_cause(low_confidence_job)

            assert result is not None
            assert result.issue_type == 'low_confidence'
            assert result.severity == 'high'
            assert not result.auto_fixable
        except ImportError:
            pytest.skip("analyze_root_cause not available")

    def test_missing_data_root_cause(self, missing_data_job):
        """Test root cause identifies missing data issue."""
        try:
            from Engine6_QA.scripts.qa_feedback import analyze_root_cause

            result = analyze_root_cause(missing_data_job)

            assert result is not None
            assert result.issue_type == 'missing_data'
            assert result.severity == 'medium'
            assert result.auto_fixable  # Can be re-scraped
        except ImportError:
            pytest.skip("analyze_root_cause not available")

    def test_invalid_mapping_root_cause(self, invalid_mapping_job):
        """Test root cause identifies invalid mapping issue."""
        try:
            from Engine6_QA.scripts.qa_feedback import analyze_root_cause

            result = analyze_root_cause(invalid_mapping_job)

            assert result is not None
            assert result.issue_type == 'invalid_mapping'
            assert result.severity == 'critical'
            assert result.auto_fixable  # Can re-run mapper
        except ImportError:
            pytest.skip("analyze_root_cause not available")

    def test_good_job_no_root_cause(self, good_job):
        """Test good job has no root cause (should auto-approve)."""
        try:
            from Engine6_QA.scripts.qa_feedback import analyze_root_cause

            result = analyze_root_cause(good_job)

            assert result is None  # No issues found
        except ImportError:
            pytest.skip("analyze_root_cause not available")


class TestRootCauseDataclass:
    """Tests for RootCause dataclass structure."""

    def test_root_cause_class_exists(self):
        """Test RootCause dataclass exists."""
        try:
            from Engine6_QA.scripts.qa_feedback import RootCause
            assert RootCause is not None
        except ImportError:
            pytest.skip("RootCause not available")

    def test_root_cause_has_required_fields(self):
        """Test RootCause has all required fields."""
        try:
            from Engine6_QA.scripts.qa_feedback import RootCause

            rc = RootCause(
                issue_type='test_type',
                severity='medium',
                description='Test description',
                affected_fields=['field1'],
                recommended_fix='Test fix',
                auto_fixable=True
            )

            assert rc.issue_type == 'test_type'
            assert rc.severity == 'medium'
            assert rc.description == 'Test description'
            assert rc.affected_fields == ['field1']
            assert rc.recommended_fix == 'Test fix'
            assert rc.auto_fixable is True
        except ImportError:
            pytest.skip("RootCause not available")


class TestDebugQAFailure:
    """Tests for systematic debugging function."""

    @pytest.fixture
    def failing_job(self):
        """Job that fails QA."""
        return {
            'Job Title/Position': 'Test Job',
            'Source URL': 'https://example.com/job/123',
            '_mapping': {
                'program_name': 'Unknown',
                'match_confidence': 0.30
            }
        }

    def test_debug_qa_failure_exists(self):
        """Test debug_qa_failure function exists."""
        try:
            from Engine6_QA.scripts.qa_feedback import debug_qa_failure
            assert debug_qa_failure is not None
        except ImportError:
            pytest.skip("debug_qa_failure not available")

    def test_debug_report_structure(self, failing_job):
        """Test debug report has required structure."""
        try:
            from Engine6_QA.scripts.qa_feedback import debug_qa_failure

            report = debug_qa_failure(failing_job)

            assert 'job_id' in report
            assert 'failure_reason' in report
            assert 'data_quality_check' in report
            assert 'suggested_actions' in report
            assert 'root_cause' in report
        except ImportError:
            pytest.skip("debug_qa_failure not available")

    def test_debug_report_has_data_quality_check(self, failing_job):
        """Test debug report includes data quality checks."""
        try:
            from Engine6_QA.scripts.qa_feedback import debug_qa_failure

            report = debug_qa_failure(failing_job)

            dq = report['data_quality_check']
            assert 'has_mapping' in dq
            assert 'confidence' in dq
            assert 'required_fields_present' in dq
        except ImportError:
            pytest.skip("debug_qa_failure not available")


class TestQAEvaluationWithRootCause:
    """Tests for QA evaluation with root cause integration."""

    @pytest.fixture
    def sample_jobs_with_issues(self):
        """Sample jobs with various quality issues."""
        return [
            # Low confidence
            {
                'Job Title/Position': 'Developer',
                '_mapping': {'program_name': 'Unknown', 'match_confidence': 0.40}
            },
            # Missing clearance
            {
                'Job Title/Position': 'Analyst',
                'Security Clearance': '',
                '_mapping': {'program_name': 'DCGS', 'match_confidence': 0.75}
            },
            # Good job
            {
                'Job Title/Position': 'Engineer',
                'Security Clearance': 'Secret',
                'Location': 'DC',
                'Prime Contractor': 'Leidos',
                '_mapping': {'program_name': 'AF DCGS', 'match_confidence': 0.90}
            }
        ]

    def test_evaluate_item_includes_root_cause(self, sample_jobs_with_issues):
        """Test evaluate_item includes root cause for review items."""
        try:
            from Engine6_QA.scripts.qa_feedback import evaluate_item, QAStatus

            # Low confidence job should have root cause
            result = evaluate_item(sample_jobs_with_issues[0])

            if result.status == QAStatus.NEEDS_REVIEW:
                assert result.root_cause is not None
        except ImportError:
            pytest.skip("evaluate_item not available")

    def test_evaluate_batch_with_root_cause(self, sample_jobs_with_issues):
        """Test batch evaluation includes root cause analysis."""
        try:
            from Engine6_QA.scripts.qa_feedback import evaluate_batch

            report = evaluate_batch(sample_jobs_with_issues)

            assert report.total_items == 3
            assert report.auto_approved >= 1  # Good job should pass

            # Check that review items have root cause
            review_items = [i for i in report.items if i.status.value == 'needs_review']
            for item in review_items:
                # Root cause should be populated for review items
                assert item.root_cause is not None or len(item.review_reasons) > 0
        except ImportError:
            pytest.skip("evaluate_batch not available")


class TestQASummaryReport:
    """Tests for QA summary report generation."""

    def test_generate_qa_summary_report_exists(self):
        """Test generate_qa_summary_report function exists."""
        try:
            from Engine6_QA.scripts.qa_feedback import generate_qa_summary_report
            assert generate_qa_summary_report is not None
        except ImportError:
            pytest.skip("generate_qa_summary_report not available")

    def test_summary_report_creates_file(self, tmp_path):
        """Test summary report creates markdown file."""
        try:
            from Engine6_QA.scripts.qa_feedback import (
                evaluate_batch, generate_qa_summary_report
            )

            jobs = [
                {'_mapping': {'match_confidence': 0.40}},
                {'_mapping': {'match_confidence': 0.90}}
            ]

            report = evaluate_batch(jobs)
            report_path = generate_qa_summary_report(report, output_dir=str(tmp_path))

            assert Path(report_path).exists()
            assert report_path.endswith('.md')
        except ImportError:
            pytest.skip("QA report generation not available")


class TestReviewQueueWithRootCause:
    """Tests for review queue with root cause data."""

    def test_review_queue_includes_root_cause(self, tmp_path):
        """Test review queue items include root cause."""
        try:
            from Engine6_QA.scripts.qa_feedback import (
                ReviewQueue, evaluate_item, QAStatus
            )

            # Create queue in temp directory
            queue_file = tmp_path / "test_review_queue.json"
            queue = ReviewQueue(queue_file=queue_file)

            # Add a job that needs review
            job = {
                'Job Title/Position': 'Test',
                '_mapping': {'match_confidence': 0.30}
            }
            result = evaluate_item(job)

            if result.status == QAStatus.NEEDS_REVIEW:
                queue.add(job, result)

                # Check queue item has root cause
                pending = queue.get_pending()
                if pending:
                    item = pending[0]
                    assert 'root_cause' in item
        except ImportError:
            pytest.skip("ReviewQueue not available")


class TestQAIntegration:
    """Integration tests for enhanced QA workflow."""

    def test_full_qa_workflow_with_root_cause(self):
        """Test complete QA workflow with root cause analysis."""
        try:
            from Engine6_QA.scripts.qa_feedback import run_qa_workflow

            jobs = [
                # Should fail - low confidence
                {
                    'Job Title/Position': 'Dev',
                    '_mapping': {'match_confidence': 0.25}
                },
                # Should fail - unmatched
                {
                    'Job Title/Position': 'Analyst',
                    '_mapping': {'program_name': 'Unmatched', 'match_confidence': 0.5}
                },
                # Should pass
                {
                    'Job Title/Position': 'Engineer',
                    'Security Clearance': 'Secret',
                    '_mapping': {'program_name': 'DCGS', 'match_confidence': 0.85}
                }
            ]

            report, approved, review = run_qa_workflow(jobs, auto_queue=False)

            assert report.total_items == 3
            assert len(approved) >= 1  # At least the good job
            assert len(review) >= 1  # At least the failing jobs

            # Verify root cause on review items
            for item in report.items:
                if item.status.value == 'needs_review':
                    assert item.root_cause is not None
        except ImportError:
            pytest.skip("run_qa_workflow not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
