"""Tests for Phase 49A — Temporal Durable Workflow Engine."""

import pytest

from src.workflows.temporal_engine import (
    TemporalWorkflowEngine,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStatus,
    StepStatus,
    StepCheckpoint,
    BUILTIN_WORKFLOWS,
    get_temporal_engine,
)


@pytest.fixture
def engine():
    return TemporalWorkflowEngine()


# =========================================
# WORKFLOW REGISTRY
# =========================================

def test_builtin_workflows_loaded(engine):
    assert len(engine.list_workflows()) == 4


def test_builtin_workflow_names(engine):
    names = {w.name for w in engine.list_workflows()}
    assert "FullBDCampaign" in names
    assert "ContactEnrichment" in names
    assert "WeeklyIntelCycle" in names
    assert "OpportunityResponse" in names


def test_get_workflow(engine):
    wf = engine.get_workflow("wf_full_bd_campaign")
    assert wf is not None
    assert wf.name == "FullBDCampaign"
    assert len(wf.steps) == 6


def test_get_workflow_not_found(engine):
    assert engine.get_workflow("wf_nonexistent") is None


def test_register_custom_workflow(engine):
    custom = WorkflowDefinition(
        workflow_id="wf_custom",
        name="CustomWorkflow",
        description="A test workflow",
        steps=[{"name": "step1", "task_queue": "hub_tasks", "description": "Test", "timeout_sec": 30, "retries": 1}],
    )
    engine.register_workflow(custom)
    assert engine.get_workflow("wf_custom") is not None
    assert len(engine.list_workflows()) == 5


# =========================================
# WORKFLOW EXECUTION
# =========================================

def test_start_workflow(engine):
    run = engine.start_workflow("wf_contact_enrichment", {"contact_id": "c001"})
    assert isinstance(run, WorkflowRun)
    assert run.status == WorkflowStatus.PENDING
    assert run.workflow_name == "ContactEnrichment"


def test_execute_workflow_completes(engine):
    run = engine.start_workflow("wf_contact_enrichment")
    result = engine.execute_workflow(run.run_id)
    assert result.status == WorkflowStatus.COMPLETED
    assert len(result.checkpoints) == 5
    assert all(c.status == StepStatus.COMPLETED for c in result.checkpoints)


def test_execute_full_bd_campaign(engine):
    run = engine.start_workflow("wf_full_bd_campaign")
    result = engine.execute_workflow(run.run_id)
    assert result.status == WorkflowStatus.COMPLETED
    assert len(result.checkpoints) == 6


def test_execute_weekly_intel_cycle(engine):
    run = engine.start_workflow("wf_weekly_intel_cycle")
    result = engine.execute_workflow(run.run_id)
    assert result.status == WorkflowStatus.COMPLETED
    assert len(result.checkpoints) == 5


def test_execute_opportunity_response(engine):
    run = engine.start_workflow("wf_opportunity_response")
    result = engine.execute_workflow(run.run_id)
    assert result.status == WorkflowStatus.COMPLETED
    assert len(result.checkpoints) == 6


def test_execute_unknown_workflow(engine):
    with pytest.raises(ValueError, match="Unknown workflow"):
        engine.start_workflow("wf_does_not_exist")


def test_execute_unknown_run(engine):
    with pytest.raises(ValueError, match="Unknown run"):
        engine.execute_workflow("run_nonexistent")


def test_run_has_output(engine):
    run = engine.start_workflow("wf_contact_enrichment")
    result = engine.execute_workflow(run.run_id)
    assert result.output is not None
    assert result.output["total_steps"] == 5
    assert result.output["completed_steps"] == 5


def test_run_has_duration(engine):
    run = engine.start_workflow("wf_contact_enrichment")
    result = engine.execute_workflow(run.run_id)
    assert result.duration_sec > 0


def test_run_id_unique(engine):
    r1 = engine.start_workflow("wf_contact_enrichment")
    r2 = engine.start_workflow("wf_contact_enrichment")
    assert r1.run_id != r2.run_id


# =========================================
# STEP HANDLERS AND COMPENSATION
# =========================================

def test_custom_step_handler(engine):
    called = []

    def handler(params, step_def):
        called.append(step_def["name"])
        return {"custom": True}

    engine.register_step_handler("fetch_crm_data", handler)
    run = engine.start_workflow("wf_contact_enrichment")
    result = engine.execute_workflow(run.run_id)
    assert "fetch_crm_data" in called
    assert result.checkpoints[0].result == {"custom": True}


def test_failing_step_triggers_compensation(engine):
    compensated = []

    def fail_handler(params, step_def):
        raise RuntimeError("Simulated failure")

    def comp_handler(params, result):
        compensated.append("compensated")

    engine.register_step_handler("classify_tier", fail_handler)
    engine.register_compensation("fetch_crm_data", comp_handler)

    run = engine.start_workflow("wf_contact_enrichment")
    result = engine.execute_workflow(run.run_id)
    assert result.status == WorkflowStatus.FAILED
    assert "compensated" in compensated
    assert result.compensations_run >= 1


def test_step_retries(engine):
    call_count = [0]

    def flaky_handler(params, step_def):
        call_count[0] += 1
        if call_count[0] <= 1:
            raise RuntimeError("Transient error")
        return {"recovered": True}

    engine.register_step_handler("fetch_crm_data", flaky_handler)
    run = engine.start_workflow("wf_contact_enrichment")
    result = engine.execute_workflow(run.run_id)
    assert result.status == WorkflowStatus.COMPLETED
    assert result.checkpoints[0].attempt >= 2


# =========================================
# RUN MANAGEMENT
# =========================================

def test_list_runs(engine):
    engine.start_workflow("wf_contact_enrichment")
    engine.start_workflow("wf_full_bd_campaign")
    runs = engine.list_runs()
    assert len(runs) == 2


def test_list_runs_filter_workflow(engine):
    engine.start_workflow("wf_contact_enrichment")
    engine.start_workflow("wf_full_bd_campaign")
    runs = engine.list_runs(workflow_id="wf_contact_enrichment")
    assert len(runs) == 1


def test_list_runs_filter_status(engine):
    r1 = engine.start_workflow("wf_contact_enrichment")
    engine.execute_workflow(r1.run_id)
    engine.start_workflow("wf_full_bd_campaign")  # pending
    runs = engine.list_runs(status=WorkflowStatus.COMPLETED)
    assert len(runs) == 1


def test_get_run(engine):
    run = engine.start_workflow("wf_contact_enrichment")
    fetched = engine.get_run(run.run_id)
    assert fetched is not None
    assert fetched.run_id == run.run_id


def test_get_run_not_found(engine):
    assert engine.get_run("run_nonexistent") is None


def test_cancel_run(engine):
    run = engine.start_workflow("wf_contact_enrichment")
    assert engine.cancel_run(run.run_id) is True
    assert engine.get_run(run.run_id).status == WorkflowStatus.CANCELLED


def test_cancel_completed_run_fails(engine):
    run = engine.start_workflow("wf_contact_enrichment")
    engine.execute_workflow(run.run_id)
    assert engine.cancel_run(run.run_id) is False


# =========================================
# REPLAY / TIME-TRAVEL
# =========================================

def test_replay_run(engine):
    run = engine.start_workflow("wf_contact_enrichment", {"key": "val"})
    engine.execute_workflow(run.run_id)
    replayed = engine.replay_run(run.run_id)
    assert replayed is not None
    assert replayed.run_id != run.run_id
    assert replayed.status == WorkflowStatus.COMPLETED


def test_replay_unknown_run(engine):
    assert engine.replay_run("run_nonexistent") is None


def test_get_timeline(engine):
    run = engine.start_workflow("wf_contact_enrichment")
    engine.execute_workflow(run.run_id)
    timeline = engine.get_timeline(run.run_id)
    assert len(timeline) == 5
    assert all("step_name" in s for s in timeline)


def test_get_timeline_unknown_run(engine):
    timeline = engine.get_timeline("run_nonexistent")
    assert timeline == []


def test_get_checkpoint(engine):
    run = engine.start_workflow("wf_contact_enrichment")
    engine.execute_workflow(run.run_id)
    cp = engine.get_checkpoint(run.run_id, 0)
    assert cp is not None
    assert cp.step_name == "fetch_crm_data"


# =========================================
# TO DICT
# =========================================

def test_workflow_run_to_dict(engine):
    run = engine.start_workflow("wf_contact_enrichment")
    engine.execute_workflow(run.run_id)
    d = run.to_dict()
    assert d["workflow_name"] == "ContactEnrichment"
    assert d["status"] == "completed"
    assert len(d["checkpoints"]) == 5


def test_workflow_definition_to_dict(engine):
    wf = engine.get_workflow("wf_full_bd_campaign")
    d = wf.to_dict()
    assert d["name"] == "FullBDCampaign"
    assert len(d["steps"]) == 6
    assert d["version"] == "1.0"


# =========================================
# STATS
# =========================================

def test_stats(engine):
    run = engine.start_workflow("wf_contact_enrichment")
    engine.execute_workflow(run.run_id)
    stats = engine.get_stats()
    assert stats["total_workflows"] == 4
    assert stats["total_runs"] >= 1
    assert "completed" in stats["runs_by_status"]


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    import src.workflows.temporal_engine as mod
    mod._instance = None
    s1 = get_temporal_engine()
    s2 = get_temporal_engine()
    assert s1 is s2
    mod._instance = None
