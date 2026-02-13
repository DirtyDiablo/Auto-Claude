"""Tests for Phase 45A — MCP Orchestrator."""

import pytest

from src.mcp.tool_registry import MCPToolRegistry
from src.mcp.orchestrator import (
    MCPOrchestrator,
    MCPExecutionPlan,
    MCPExecutionStep,
    PlanStatus,
    get_orchestrator,
)


@pytest.fixture
def registry():
    return MCPToolRegistry(seed_builtins=True)


@pytest.fixture
def orchestrator(registry):
    return MCPOrchestrator(registry=registry)


# =========================================
# PLAN GENERATION
# =========================================

def test_plan_outreach(orchestrator):
    plan = orchestrator.plan_from_intent("Prepare outreach for Navy DCGS-N contacts")
    assert plan.status == PlanStatus.READY.value
    assert len(plan.steps) >= 3
    assert plan.intent != ""


def test_plan_competitor_scan(orchestrator):
    plan = orchestrator.plan_from_intent("Run competitor market scan for GBSD")
    assert len(plan.steps) >= 2


def test_plan_meeting_prep(orchestrator):
    plan = orchestrator.plan_from_intent("Prepare for call with John Smith")
    assert len(plan.steps) >= 2


def test_plan_single_step_fallback(orchestrator):
    plan = orchestrator.plan_from_intent("Send email to Craig Lindahl")
    assert len(plan.steps) >= 1
    assert plan.steps[0].server_id != ""


def test_plan_unknown_intent(orchestrator):
    plan = orchestrator.plan_from_intent("xyz123 completely unknown")
    # Should produce a plan (possibly empty or single-step)
    assert plan.plan_id != ""


def test_plan_has_dependencies(orchestrator):
    plan = orchestrator.plan_from_intent("Prepare outreach for contacts")
    deps_exist = any(len(s.depends_on) > 0 for s in plan.steps)
    assert deps_exist is True


def test_plan_estimated_cost(orchestrator):
    plan = orchestrator.plan_from_intent("Prepare outreach for contacts")
    assert plan.estimated_cost >= 0


def test_plan_estimated_time(orchestrator):
    plan = orchestrator.plan_from_intent("Prepare outreach for contacts")
    assert plan.estimated_time_ms > 0


def test_plan_stored(orchestrator):
    plan = orchestrator.plan_from_intent("Test plan")
    assert orchestrator.get_plan(plan.plan_id) is not None


def test_list_plans(orchestrator):
    orchestrator.plan_from_intent("Plan A")
    orchestrator.plan_from_intent("Plan B")
    assert len(orchestrator.list_plans()) == 2


# =========================================
# EXECUTION
# =========================================

def test_execute_outreach(orchestrator):
    plan = orchestrator.plan_from_intent("Prepare outreach for contacts")
    result = orchestrator.execute_plan(plan)
    assert result.status == "completed"
    assert result.steps_completed == len(plan.steps)
    assert result.steps_failed == 0


def test_execute_competitor_scan(orchestrator):
    plan = orchestrator.plan_from_intent("Run competitor scan")
    result = orchestrator.execute_plan(plan)
    assert result.status == "completed"


def test_execute_records_usage(orchestrator):
    plan = orchestrator.plan_from_intent("Prepare outreach for contacts")
    orchestrator.execute_plan(plan)
    # Check that usage was recorded on at least one server
    notion = orchestrator._registry.get_server("mcp_notion")
    assert notion.total_calls >= 1


def test_execute_tracks_cost(orchestrator):
    plan = orchestrator.plan_from_intent("Prepare outreach for contacts")
    result = orchestrator.execute_plan(plan)
    assert result.total_cost >= 0


def test_execute_tracks_latency(orchestrator):
    plan = orchestrator.plan_from_intent("Prepare outreach for contacts")
    result = orchestrator.execute_plan(plan)
    assert result.total_latency_ms > 0


def test_execute_updates_plan_status(orchestrator):
    plan = orchestrator.plan_from_intent("Test exec")
    orchestrator.execute_plan(plan)
    assert plan.status == PlanStatus.COMPLETED.value


def test_execute_with_unhealthy_server(orchestrator):
    plan = orchestrator.plan_from_intent("Send email to team")
    # Mark the target server unhealthy
    if plan.steps:
        server_id = plan.steps[0].server_id
        for _ in range(10):
            orchestrator._registry.health_check(server_id, healthy=False)
        server = orchestrator._registry.get_server(server_id)
        server.health = "unhealthy"
    result = orchestrator.execute_plan(plan)
    # Should fail or be partial since server is unhealthy
    assert result.status in ("failed", "partial")
    assert result.steps_failed >= 1


# =========================================
# STEP EXECUTION
# =========================================

def test_step_auto_id():
    step = MCPExecutionStep(server_id="s1", tool_name="t1")
    assert step.step_id.startswith("step_")


def test_step_missing_server(orchestrator):
    plan = MCPExecutionPlan(
        intent="test",
        steps=[MCPExecutionStep(step_id="s0", server_id="nonexistent", tool_name="test")],
        status="ready",
    )
    result = orchestrator.execute_plan(plan)
    assert result.steps_failed == 1


# =========================================
# EXECUTION HISTORY
# =========================================

def test_execution_history(orchestrator):
    plan = orchestrator.plan_from_intent("Test history")
    orchestrator.execute_plan(plan)
    execs = orchestrator.get_executions()
    assert len(execs) >= 1


# =========================================
# STATS
# =========================================

def test_stats(orchestrator):
    plan = orchestrator.plan_from_intent("Test stats")
    orchestrator.execute_plan(plan)
    stats = orchestrator.get_stats()
    assert stats["total_plans"] >= 1
    assert stats["total_executions"] >= 1
    assert stats["completed"] >= 1


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    o1 = get_orchestrator()
    o2 = get_orchestrator()
    assert o1 is o2
