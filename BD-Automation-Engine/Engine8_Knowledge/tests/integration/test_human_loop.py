"""
Phase 23A — Human-in-the-Loop Manager Tests

Tests approval request creation, listing, decisions, resume, auto-approve, and stats.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.workflows.checkpoint_store import CheckpointStore, DictMetaStore
from Engine8_Knowledge.workflows.human_loop import (
    HumanInTheLoopManager, ApprovalRequest, ApprovalDecision,
)


@pytest.fixture
def manager(tmp_path):
    store = CheckpointStore(db_path=str(tmp_path / "test.db"))
    store._db = DictMetaStore()
    return HumanInTheLoopManager(
        checkpoint_store=store,
        storage_path=str(tmp_path / "approvals"),
    )


@pytest.fixture
async def seeded_manager(manager):
    """Manager with a pre-created approval request."""
    await manager.create_approval_request(
        thread_id="t1", workflow_name="contact_enrichment",
        node_name="review_classifications",
        state_snapshot={"classifications": [{"tier": 1}]},
        description="Review Tier 1 contact classifications",
        urgency="high", expires_in_hours=24,
    )
    return manager


def test_init(manager):
    assert manager is not None
    assert manager.checkpoint_store is not None


@pytest.mark.asyncio
async def test_create_approval_request(manager):
    req = await manager.create_approval_request(
        thread_id="t1", workflow_name="test",
        node_name="review", state_snapshot={"data": "test"},
        description="Please approve",
    )
    assert isinstance(req, ApprovalRequest)
    assert req.status == "pending"
    assert req.urgency == "normal"
    assert req.workflow_name == "test"


@pytest.mark.asyncio
async def test_list_pending_approvals_empty(manager):
    approvals = await manager.list_pending_approvals()
    assert approvals == []


@pytest.mark.asyncio
async def test_list_pending_approvals_filtered(seeded_manager):
    approvals = await seeded_manager.list_pending_approvals(workflow_name="contact_enrichment")
    assert len(approvals) >= 1
    assert approvals[0].workflow_name == "contact_enrichment"

    empty = await seeded_manager.list_pending_approvals(workflow_name="nonexistent")
    assert len(empty) == 0


@pytest.mark.asyncio
async def test_submit_decision_approve(seeded_manager):
    approvals = await seeded_manager.list_pending_approvals()
    req_id = approvals[0].request_id

    decision = await seeded_manager.submit_decision(
        request_id=req_id, decision="approve",
        notes="Looks good", decided_by="tester",
    )
    assert isinstance(decision, ApprovalDecision)
    assert decision.decision == "approve"
    assert decision.decided_by == "tester"


@pytest.mark.asyncio
async def test_submit_decision_reject(seeded_manager):
    approvals = await seeded_manager.list_pending_approvals()
    req_id = approvals[0].request_id

    decision = await seeded_manager.submit_decision(
        request_id=req_id, decision="reject",
        notes="Tier assignment incorrect",
    )
    assert decision.decision == "reject"


@pytest.mark.asyncio
async def test_submit_decision_invalid_option(seeded_manager):
    approvals = await seeded_manager.list_pending_approvals()
    req_id = approvals[0].request_id

    with pytest.raises(ValueError, match="Invalid decision"):
        await seeded_manager.submit_decision(req_id, decision="invalid_option")


@pytest.mark.asyncio
async def test_submit_decision_already_decided(seeded_manager):
    approvals = await seeded_manager.list_pending_approvals()
    req_id = approvals[0].request_id

    await seeded_manager.submit_decision(req_id, decision="approve")

    with pytest.raises(ValueError, match="already"):
        await seeded_manager.submit_decision(req_id, decision="reject")


@pytest.mark.asyncio
async def test_resume_workflow(seeded_manager):
    approvals = await seeded_manager.list_pending_approvals()
    req_id = approvals[0].request_id
    await seeded_manager.submit_decision(req_id, decision="approve")

    # Create the thread in checkpoint store so resume works
    await seeded_manager.checkpoint_store.create_thread("contact_enrichment", thread_id="t1")
    tid = await seeded_manager.resume_workflow(req_id)
    assert tid == "t1"


@pytest.mark.asyncio
async def test_auto_approve_expired(manager):
    # Create request that expires immediately
    await manager.create_approval_request(
        thread_id="t_expired", workflow_name="test",
        node_name="review", state_snapshot={},
        description="Expire test", expires_in_hours=0,
    )
    auto_approved = await manager.auto_approve_expired()
    assert len(auto_approved) >= 1


@pytest.mark.asyncio
async def test_get_approval_stats(seeded_manager):
    stats = await seeded_manager.get_approval_stats()
    assert stats["total_requests"] >= 1
    assert stats["pending"] >= 1
    assert "by_workflow" in stats
    assert "by_urgency" in stats
