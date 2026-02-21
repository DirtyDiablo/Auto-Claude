"""Tests for ReviewQueue enhancements — approve, reject, reclassify, bulk ops, audit log."""

import json
import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine6_QA.scripts.qa_feedback import ReviewQueue, QAResult, QAStatus, RootCause


@pytest.fixture
def tmp_queue(tmp_path):
    """Create a ReviewQueue backed by a temporary file with sample items."""
    queue_file = tmp_path / "review_queue.json"
    queue = ReviewQueue(queue_file=queue_file)

    # Add two sample items via the public API
    result_a = QAResult(
        job_id="job-001",
        status=QAStatus.NEEDS_REVIEW,
        confidence=0.55,
        review_reasons=["Low confidence"],
        original_program="DCGS-A",
        root_cause=RootCause(
            issue_type="low_confidence",
            severity="high",
            description="Confidence below threshold",
            affected_fields=["_mapping.match_confidence"],
            recommended_fix="Manual review required",
        ),
    )
    result_b = QAResult(
        job_id="job-002",
        status=QAStatus.NEEDS_REVIEW,
        confidence=0.40,
        review_reasons=["No match"],
        original_program="Unmatched",
        root_cause=RootCause(
            issue_type="invalid_mapping",
            severity="critical",
            description="No valid program match",
            affected_fields=["_mapping.program_name"],
            recommended_fix="Re-run mapper",
            auto_fixable=True,
        ),
    )

    queue.add({"Source URL": "job-001"}, result_a)
    queue.add({"Source URL": "job-002"}, result_b)
    return queue


class TestApproveItem:
    def test_approve_item(self, tmp_queue):
        assert tmp_queue.approve("job-001", reviewer="admin") is True

        item = tmp_queue.get_item("job-001")
        assert item["status"] == "approved"
        assert item["reviewed"] is True
        assert "reviewed_at" in item

    def test_approve_nonexistent_returns_false(self, tmp_queue):
        assert tmp_queue.approve("nonexistent-id", reviewer="admin") is False


class TestRejectItem:
    def test_reject_item(self, tmp_queue):
        assert tmp_queue.reject("job-002", reviewer="admin", reason="Bad data") is True

        item = tmp_queue.get_item("job-002")
        assert item["status"] == "rejected"
        assert item["reviewed"] is True
        assert item["rejection_reason"] == "Bad data"

    def test_reject_nonexistent_returns_false(self, tmp_queue):
        assert tmp_queue.reject("nope", reviewer="admin", reason="x") is False


class TestReclassifyItem:
    def test_reclassify_item(self, tmp_queue):
        assert tmp_queue.reclassify("job-002", "GBSD", reviewer="admin") is True

        item = tmp_queue.get_item("job-002")
        assert item["original_program"] == "GBSD"
        assert item["status"] == "approved"
        assert item["reviewed"] is True


class TestBulkApprove:
    def test_bulk_approve(self, tmp_queue):
        result = tmp_queue.bulk_approve(["job-001", "job-002"], reviewer="admin")
        assert result["success"] == 2
        assert result["failed"] == 0

        for jid in ("job-001", "job-002"):
            assert tmp_queue.get_item(jid)["status"] == "approved"

    def test_bulk_approve_partial(self, tmp_queue):
        result = tmp_queue.bulk_approve(["job-001", "missing"], reviewer="admin")
        assert result["success"] == 1
        assert result["failed"] == 1


class TestBulkReject:
    def test_bulk_reject(self, tmp_queue):
        result = tmp_queue.bulk_reject(
            ["job-001", "job-002"], reviewer="admin", reason="Batch cleanup"
        )
        assert result["success"] == 2
        assert result["failed"] == 0

        for jid in ("job-001", "job-002"):
            assert tmp_queue.get_item(jid)["status"] == "rejected"


class TestGetReviewHistory:
    def test_get_review_history(self, tmp_queue):
        # Initially nothing is reviewed
        assert len(tmp_queue.get_review_history()) == 0

        tmp_queue.approve("job-001", reviewer="admin")
        tmp_queue.reject("job-002", reviewer="admin", reason="bad")

        history = tmp_queue.get_review_history()
        assert len(history) == 2

    def test_history_contains_reviewed_at(self, tmp_queue):
        tmp_queue.approve("job-001", reviewer="admin")
        history = tmp_queue.get_review_history()
        assert "reviewed_at" in history[0]


class TestAuditLog:
    def test_audit_log_created(self, tmp_queue):
        tmp_queue.approve("job-001", reviewer="admin")

        item = tmp_queue.get_item("job-001")
        assert "audit_log" in item
        assert len(item["audit_log"]) == 1

        entry = item["audit_log"][0]
        assert entry["action"] == "approved"
        assert entry["reviewer"] == "admin"
        assert "timestamp" in entry

    def test_multiple_audit_entries(self, tmp_queue):
        tmp_queue.reject("job-001", reviewer="alice", reason="check again")
        tmp_queue.approve("job-001", reviewer="bob")

        item = tmp_queue.get_item("job-001")
        assert len(item["audit_log"]) == 2
        assert item["audit_log"][0]["action"] == "rejected"
        assert item["audit_log"][1]["action"] == "approved"

    def test_reclassify_audit_has_details(self, tmp_queue):
        tmp_queue.reclassify("job-002", "GBSD", reviewer="admin")

        item = tmp_queue.get_item("job-002")
        entry = item["audit_log"][0]
        assert entry["action"] == "reclassified"
        assert "GBSD" in entry["details"]
        assert "Unmatched" in entry["details"]


class TestGetItem:
    def test_get_existing_item(self, tmp_queue):
        item = tmp_queue.get_item("job-001")
        assert item is not None
        assert item["job_id"] == "job-001"

    def test_get_nonexistent_returns_none(self, tmp_queue):
        assert tmp_queue.get_item("does-not-exist") is None


class TestGetStats:
    def test_stats_after_review_actions(self, tmp_queue):
        tmp_queue.approve("job-001", reviewer="admin")
        tmp_queue.reject("job-002", reviewer="admin", reason="bad")

        stats = tmp_queue.get_stats()
        assert stats["total"] == 2
        assert stats["pending"] == 0
        assert stats["reviewed"] == 2
        assert stats["approved"] == 1
        assert stats["rejected"] == 1
        assert "by_root_cause" in stats

    def test_stats_by_root_cause(self, tmp_queue):
        stats = tmp_queue.get_stats()
        assert stats["by_root_cause"]["low_confidence"] == 1
        assert stats["by_root_cause"]["invalid_mapping"] == 1


class TestPersistence:
    def test_changes_persist_to_disk(self, tmp_path):
        queue_file = tmp_path / "review_queue.json"
        queue = ReviewQueue(queue_file=queue_file)

        result = QAResult(
            job_id="persist-test",
            status=QAStatus.NEEDS_REVIEW,
            confidence=0.60,
            review_reasons=["test"],
            original_program="TestProg",
        )
        queue.add({"Source URL": "persist-test"}, result)
        queue.approve("persist-test", reviewer="admin")

        # Load a fresh queue from the same file
        queue2 = ReviewQueue(queue_file=queue_file)
        item = queue2.get_item("persist-test")
        assert item is not None
        assert item["status"] == "approved"
        assert item["reviewed"] is True
