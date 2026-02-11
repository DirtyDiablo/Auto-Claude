"""Tests for Phase 49A — Cross-Project Orchestrator."""

import pytest

from src.workflows.cross_project_orchestrator import (
    CrossProjectOrchestrator,
    TaskQueueName,
    TaskPriority,
    OrchestratorTask,
    OrchestratorTaskStatus,
    FanOutResult,
    get_orchestrator,
)


@pytest.fixture
def orch():
    return CrossProjectOrchestrator()


# =========================================
# QUEUE ROUTING
# =========================================

def test_route_hub_task(orch):
    assert orch.route_task("map_programs") == TaskQueueName.HUB


def test_route_scraper_task(orch):
    assert orch.route_task("scrape_jobs") == TaskQueueName.SCRAPER


def test_route_n8n_task(orch):
    assert orch.route_task("draft_outreach") == TaskQueueName.N8N


def test_route_unknown_defaults_hub(orch):
    assert orch.route_task("unknown_task") == TaskQueueName.HUB


# =========================================
# TASK SUBMISSION
# =========================================

def test_submit_task(orch):
    task = orch.submit_task("map_programs", payload={"job_id": "j001"})
    assert isinstance(task, OrchestratorTask)
    assert task.queue == TaskQueueName.HUB
    assert task.status == OrchestratorTaskStatus.QUEUED


def test_submit_task_explicit_queue(orch):
    task = orch.submit_task("custom_task", queue=TaskQueueName.N8N)
    assert task.queue == TaskQueueName.N8N


def test_submit_task_with_priority(orch):
    task = orch.submit_task("scrape_jobs", priority=TaskPriority.CRITICAL)
    assert task.priority == TaskPriority.CRITICAL


def test_submit_task_with_dependencies(orch):
    t1 = orch.submit_task("scrape_jobs")
    orch.execute_task(t1.task_id)  # complete dependency first
    t2 = orch.submit_task("map_programs", depends_on=[t1.task_id])
    # dependency is already complete, so task should be QUEUED
    fetched = orch.get_task(t2.task_id)
    assert fetched.status == OrchestratorTaskStatus.QUEUED


def test_submit_task_waiting_on_dependency(orch):
    t1 = orch.submit_task("scrape_jobs")
    t2 = orch.submit_task("map_programs", depends_on=[t1.task_id])
    assert t2.status == OrchestratorTaskStatus.WAITING


def test_task_id_unique(orch):
    t1 = orch.submit_task("map_programs")
    t2 = orch.submit_task("map_programs")
    assert t1.task_id != t2.task_id


# =========================================
# DISPATCH AND EXECUTE
# =========================================

def test_dispatch_next(orch):
    orch.submit_task("map_programs")
    task = orch.dispatch_next(TaskQueueName.HUB)
    assert task is not None
    assert task.status == OrchestratorTaskStatus.DISPATCHED


def test_dispatch_priority_order(orch):
    orch.submit_task("map_programs", priority=TaskPriority.LOW)
    orch.submit_task("score_opportunities", priority=TaskPriority.CRITICAL)
    task = orch.dispatch_next(TaskQueueName.HUB)
    assert task.name == "score_opportunities"


def test_dispatch_empty_queue(orch):
    assert orch.dispatch_next(TaskQueueName.SCRAPER) is None


def test_execute_task(orch):
    t = orch.submit_task("scrape_jobs")
    result = orch.execute_task(t.task_id)
    assert result.status == OrchestratorTaskStatus.COMPLETED
    assert result.result is not None


def test_execute_unknown_task(orch):
    with pytest.raises(ValueError, match="Unknown task"):
        orch.execute_task("otask_nonexistent")


def test_fail_task(orch):
    t = orch.submit_task("scrape_jobs")
    result = orch.fail_task(t.task_id, "Connection timeout")
    assert result.status == OrchestratorTaskStatus.FAILED
    assert result.error == "Connection timeout"


# =========================================
# DEPENDENCY RESOLUTION
# =========================================

def test_dependency_unblocks_waiting(orch):
    t1 = orch.submit_task("scrape_jobs")
    t2 = orch.submit_task("map_programs", depends_on=[t1.task_id])
    assert t2.status == OrchestratorTaskStatus.WAITING

    # Execute t1 — should unblock t2
    orch.execute_task(t1.task_id)
    fetched = orch.get_task(t2.task_id)
    assert fetched.status == OrchestratorTaskStatus.QUEUED


# =========================================
# FAN-OUT / FAN-IN
# =========================================

def test_fan_out(orch):
    result = orch.fan_out(["scrape_jobs", "map_programs", "score_opportunities"])
    assert isinstance(result, FanOutResult)
    assert result.total == 3
    assert len(result.task_ids) == 3


def test_fan_in_incomplete(orch):
    result = orch.fan_out(["scrape_jobs", "map_programs"])
    collected = orch.fan_in(result.group_id)
    assert collected.completed == 0
    assert collected.all_complete is False


def test_fan_in_after_execution(orch):
    result = orch.fan_out(["scrape_jobs", "map_programs"])
    for tid in result.task_ids:
        orch.execute_task(tid)
    collected = orch.fan_in(result.group_id)
    assert collected.completed == 2
    assert collected.all_complete is True
    assert len(collected.results) == 2


def test_fan_in_unknown_group(orch):
    with pytest.raises(ValueError, match="Unknown fan-out group"):
        orch.fan_in("fanout_nonexistent")


# =========================================
# TASK MANAGEMENT
# =========================================

def test_list_tasks(orch):
    orch.submit_task("scrape_jobs")
    orch.submit_task("map_programs")
    tasks = orch.list_tasks()
    assert len(tasks) == 2


def test_list_tasks_filter_queue(orch):
    orch.submit_task("scrape_jobs")
    orch.submit_task("map_programs")
    tasks = orch.list_tasks(queue=TaskQueueName.SCRAPER)
    assert len(tasks) == 1
    assert tasks[0].name == "scrape_jobs"


def test_list_tasks_filter_status(orch):
    t = orch.submit_task("scrape_jobs")
    orch.execute_task(t.task_id)
    orch.submit_task("map_programs")
    tasks = orch.list_tasks(status=OrchestratorTaskStatus.COMPLETED)
    assert len(tasks) == 1


def test_cancel_task(orch):
    t = orch.submit_task("scrape_jobs")
    assert orch.cancel_task(t.task_id) is True
    assert orch.get_task(t.task_id).status == OrchestratorTaskStatus.CANCELLED


def test_cancel_completed_task_fails(orch):
    t = orch.submit_task("scrape_jobs")
    orch.execute_task(t.task_id)
    assert orch.cancel_task(t.task_id) is False


# =========================================
# QUEUE HEALTH
# =========================================

def test_queue_status(orch):
    orch.submit_task("scrape_jobs")
    status = orch.get_queue_status(TaskQueueName.SCRAPER)
    assert status["pending"] == 1
    assert status["is_healthy"] is True


def test_set_queue_health(orch):
    orch.set_queue_health(TaskQueueName.N8N, False)
    status = orch.get_queue_status(TaskQueueName.N8N)
    assert status["is_healthy"] is False


def test_get_all_queues(orch):
    queues = orch.get_all_queues()
    assert len(queues) == 3
    names = {q["name"] for q in queues}
    assert "hub_tasks" in names
    assert "scraper_tasks" in names
    assert "n8n_tasks" in names


# =========================================
# TO DICT
# =========================================

def test_task_to_dict(orch):
    t = orch.submit_task("scrape_jobs", payload={"key": "val"})
    d = t.to_dict()
    assert d["name"] == "scrape_jobs"
    assert d["queue"] == "scraper_tasks"
    assert d["payload"] == {"key": "val"}


# =========================================
# STATS
# =========================================

def test_stats(orch):
    t = orch.submit_task("scrape_jobs")
    orch.execute_task(t.task_id)
    stats = orch.get_stats()
    assert stats["total_tasks"] >= 1
    assert len(stats["queues"]) == 3


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    import src.workflows.cross_project_orchestrator as mod
    mod._instance = None
    s1 = get_orchestrator()
    s2 = get_orchestrator()
    assert s1 is s2
    mod._instance = None
