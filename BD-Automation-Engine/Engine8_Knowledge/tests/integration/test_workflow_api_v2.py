"""
Phase 23A — Workflow API v2 Tests

Tests all 18 FastAPI endpoints with mocked orchestrator, debugger, and HITL manager.
"""

from unittest.mock import patch, AsyncMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from Engine8_Knowledge.workflows.workflow_routes import router
from Engine8_Knowledge.workflows.orchestrator_v2 import (
    WorkflowExecution,
    ScheduledWorkflow,
)
from Engine8_Knowledge.workflows.time_travel import (
    ExecutionTimeline,
    StateDiff,
    NodeVisit,
)
from Engine8_Knowledge.workflows.human_loop import ApprovalRequest, ApprovalDecision
from Engine8_Knowledge.workflows.graph_builder import WorkflowInfo

app = FastAPI()
app.include_router(router)
client = TestClient(app)


# ---------------------------------------------------------------------------
# Mock fixtures
# ---------------------------------------------------------------------------

MOCK_EXECUTION = WorkflowExecution(
    thread_id="t1",
    workflow_name="test_wf",
    status="completed",
    started_at="2024-01-01T00:00:00",
    step_count=3,
)

MOCK_INTERRUPTED = WorkflowExecution(
    thread_id="t2",
    workflow_name="test_wf",
    status="interrupted",
    started_at="2024-01-01T00:00:00",
    current_node="review",
    step_count=2,
    pending_approvals=["approval_123"],
)

MOCK_SCHEDULE = ScheduledWorkflow(
    schedule_id="sched_1",
    workflow_name="test_wf",
    cron_expression="0 6 * * *",
    default_input={},
    enabled=True,
    run_count=5,
)

MOCK_APPROVAL = ApprovalRequest(
    request_id="approval_123",
    thread_id="t2",
    workflow_name="test_wf",
    node_name="review",
    description="Please approve",
    state_snapshot={},
    options=["approve", "reject"],
    urgency="high",
    created_at="2024-01-01T00:00:00",
    expires_at="2024-01-02T00:00:00",
    status="pending",
)

MOCK_DECISION = ApprovalDecision(
    request_id="approval_123",
    decision="approve",
    modified_state=None,
    notes="OK",
    decided_by="user",
    decided_at="2024-01-01T01:00:00",
)

MOCK_TIMELINE = ExecutionTimeline(
    thread_id="t1",
    workflow_name="test_wf",
    started_at="2024-01-01T00:00:00",
    completed_at="2024-01-01T00:01:00",
    status="completed",
    total_steps=3,
    total_duration_seconds=60.0,
    nodes_visited=[
        NodeVisit(
            step=1,
            node_name="a",
            started_at="2024-01-01T00:00:00",
            duration_seconds=1.0,
            state_keys_modified=["x"],
            input_summary="{}",
            output_summary="{x}",
        )
    ],
    errors=[],
    interrupts=[],
)

MOCK_DIFF = StateDiff(
    step_a=1, step_b=2, added_keys=["y"], removed_keys=[], modified_keys={}
)

MOCK_WORKFLOW_INFO = WorkflowInfo(
    name="test_wf",
    description="Test",
    node_count=3,
    edge_count=2,
    interrupt_nodes=[],
    parallel_groups=[],
    entry_point="node_a",
)


def _mock_orch():
    m = AsyncMock()
    m.start_workflow.return_value = MOCK_EXECUTION
    m.resume_workflow.return_value = MOCK_EXECUTION
    m.cancel_workflow.return_value = True
    m.get_active_workflows.return_value = [MOCK_INTERRUPTED]
    m.get_workflow_history.return_value = [MOCK_EXECUTION]
    m.get_execution_status.return_value = MOCK_EXECUTION
    m.list_workflows.return_value = [MOCK_WORKFLOW_INFO]
    m.list_schedules = AsyncMock(return_value=[MOCK_SCHEDULE])
    m.schedule_workflow = AsyncMock(return_value=MOCK_SCHEDULE)
    m.toggle_schedule = AsyncMock(return_value=True)
    m.get_stats = AsyncMock(return_value={"total_executions": 1, "by_status": {}})
    return m


def _mock_debugger():
    m = AsyncMock()
    m.get_execution_timeline.return_value = MOCK_TIMELINE
    m.inspect_state_at.return_value = {"step": 1, "state": {"x": 1}}
    m.diff_states.return_value = MOCK_DIFF
    m.replay_from.return_value = "fork_abc123"
    return m


def _mock_hitl():
    m = AsyncMock()
    m.list_pending_approvals.return_value = [MOCK_APPROVAL]
    m.submit_decision.return_value = MOCK_DECISION
    m.get_approval_stats.return_value = {"total_requests": 1, "pending": 0}
    return m


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_start_workflow():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_orchestrator",
        return_value=_mock_orch(),
    ):
        resp = client.post("/workflows/start", json={"workflow_name": "test_wf"})
        assert resp.status_code == 200
        assert resp.json()["thread_id"] == "t1"


def test_start_workflow_bad_name():
    mock = _mock_orch()
    mock.start_workflow.side_effect = ValueError("not registered")
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_orchestrator",
        return_value=mock,
    ):
        resp = client.post("/workflows/start", json={"workflow_name": "bad"})
        assert resp.status_code == 400


def test_resume_workflow():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_orchestrator",
        return_value=_mock_orch(),
    ):
        resp = client.post("/workflows/t1/resume", json={})
        assert resp.status_code == 200


def test_cancel_workflow():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_orchestrator",
        return_value=_mock_orch(),
    ):
        resp = client.post("/workflows/t1/cancel", json={"reason": "test"})
        assert resp.status_code == 200
        assert resp.json()["cancelled"] is True


def test_get_active():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_orchestrator",
        return_value=_mock_orch(),
    ):
        resp = client.get("/workflows/active")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1


def test_get_history():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_orchestrator",
        return_value=_mock_orch(),
    ):
        resp = client.get("/workflows/history")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1


def test_get_execution_status():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_orchestrator",
        return_value=_mock_orch(),
    ):
        resp = client.get("/workflows/t1/status")
        assert resp.status_code == 200
        assert resp.json()["thread_id"] == "t1"


def test_get_execution_not_found():
    mock = _mock_orch()
    mock.get_execution_status.return_value = None
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_orchestrator",
        return_value=mock,
    ):
        resp = client.get("/workflows/nonexistent/status")
        assert resp.status_code == 404


def test_get_timeline():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_debugger",
        return_value=_mock_debugger(),
    ):
        resp = client.get("/workflows/t1/timeline")
        assert resp.status_code == 200
        assert resp.json()["total_steps"] == 3


def test_get_state_at_step():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_debugger",
        return_value=_mock_debugger(),
    ):
        resp = client.get("/workflows/t1/state/1")
        assert resp.status_code == 200


def test_diff_states():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_debugger",
        return_value=_mock_debugger(),
    ):
        resp = client.get("/workflows/t1/diff?step_a=1&step_b=2")
        assert resp.status_code == 200
        assert "added_keys" in resp.json()


def test_replay_from_step():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_debugger",
        return_value=_mock_debugger(),
    ):
        resp = client.post("/workflows/t1/replay/2", json={})
        assert resp.status_code == 200
        assert resp.json()["forked_thread_id"] == "fork_abc123"


def test_list_registry():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_orchestrator",
        return_value=_mock_orch(),
    ):
        resp = client.get("/workflows/registry")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1


def test_list_schedules():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_orchestrator",
        return_value=_mock_orch(),
    ):
        resp = client.get("/workflows/schedules")
        assert resp.status_code == 200


def test_create_schedule():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_orchestrator",
        return_value=_mock_orch(),
    ):
        resp = client.post(
            "/workflows/schedules",
            json={
                "workflow_name": "test_wf",
                "cron_expression": "0 6 * * *",
            },
        )
        assert resp.status_code == 200


def test_list_approvals():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_hitl",
        return_value=_mock_hitl(),
    ):
        resp = client.get("/workflows/approvals")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1


def test_submit_decision():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_hitl",
        return_value=_mock_hitl(),
    ):
        resp = client.post(
            "/workflows/approvals/approval_123/decide",
            json={"decision": "approve", "decided_by": "test"},
        )
        assert resp.status_code == 200
        assert resp.json()["decision"] == "approve"


def test_get_approval_stats():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_hitl",
        return_value=_mock_hitl(),
    ):
        resp = client.get("/workflows/approvals/stats")
        assert resp.status_code == 200


def test_get_workflow_stats():
    with patch(
        "Engine8_Knowledge.workflows.workflow_routes._get_orchestrator",
        return_value=_mock_orch(),
    ):
        resp = client.get("/workflows/stats")
        assert resp.status_code == 200
        assert "total_executions" in resp.json()
