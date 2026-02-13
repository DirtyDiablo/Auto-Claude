"""Tests for Phase 41A — Worker Registry."""

import pytest

from src.agents.swarm.workers import (
    WorkerRegistry,
    WorkerAgent,
    WorkerType,
    SubTask,
    DEFAULT_CAPABILITIES,
    get_worker_registry,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def registry():
    return WorkerRegistry()


# =========================================
# WORKER TYPES
# =========================================

def test_worker_types_enum():
    assert WorkerType.RESEARCH.value == "research"
    assert WorkerType.CONTACT_DISCOVERY.value == "contact_discovery"
    assert WorkerType.JOB_INTEL.value == "job_intel"
    assert WorkerType.OUTREACH_CRAFTER.value == "outreach_crafter"
    assert WorkerType.DOCUMENT_GENERATOR.value == "document_generator"
    assert WorkerType.ANALYTICS.value == "analytics"
    assert WorkerType.PAST_PERFORMANCE.value == "past_performance"
    assert WorkerType.KNOWLEDGE.value == "knowledge"


def test_default_capabilities_count():
    assert len(DEFAULT_CAPABILITIES) == 8


def test_each_capability_has_fields():
    for wtype, cap in DEFAULT_CAPABILITIES.items():
        assert cap.worker_type == wtype
        assert len(cap.description) > 0
        assert len(cap.tools) > 0
        assert len(cap.output_fields) > 0
        assert cap.avg_tokens > 0
        assert cap.avg_time_seconds > 0


# =========================================
# REGISTRY
# =========================================

def test_list_worker_types(registry):
    types = registry.list_worker_types()
    assert len(types) == 8
    assert "research" in types
    assert "contact_discovery" in types


def test_get_capability(registry):
    cap = registry.get_capability("research")
    assert cap is not None
    assert cap.worker_type == "research"


def test_get_capability_nonexistent(registry):
    assert registry.get_capability("nonexistent") is None


def test_get_all_capabilities(registry):
    caps = registry.get_all_capabilities()
    assert len(caps) == 8


def test_get_worker(registry):
    worker = registry.get_worker("research")
    assert worker is not None
    assert isinstance(worker, WorkerAgent)
    assert worker.worker_type == "research"


def test_get_worker_nonexistent(registry):
    assert registry.get_worker("nonexistent") is None


# =========================================
# BEST WORKER SELECTION
# =========================================

def test_get_best_worker_explicit(registry):
    task = SubTask(worker_type="analytics")
    assert registry.get_best_worker(task) == "analytics"


def test_get_best_worker_by_keywords(registry):
    task = SubTask(description="Find contacts at Leidos")
    best = registry.get_best_worker(task)
    assert best == "contact_discovery"


def test_get_best_worker_job(registry):
    task = SubTask(description="Analyze open job positions for hiring")
    best = registry.get_best_worker(task)
    assert best == "job_intel"


def test_get_best_worker_default(registry):
    task = SubTask(description="something unknown")
    best = registry.get_best_worker(task)
    assert best == "research"  # fallback


# =========================================
# WORKER EXECUTION
# =========================================

@pytest.mark.asyncio
async def test_default_execute_research(registry):
    worker = registry.get_worker("research")
    task = SubTask(id="t1", description="Research DCGS", worker_type="research")
    result = await worker.execute(task)
    assert result["worker_type"] == "research"
    assert result["status"] == "completed"
    assert "findings" in result


@pytest.mark.asyncio
async def test_default_execute_contact_discovery(registry):
    worker = registry.get_worker("contact_discovery")
    task = SubTask(id="t2", description="Find contacts", worker_type="contact_discovery")
    result = await worker.execute(task)
    assert result["contacts_found"] == 0
    assert "contacts" in result


@pytest.mark.asyncio
async def test_default_execute_document_generator(registry):
    worker = registry.get_worker("document_generator")
    task = SubTask(id="t3", description="Generate report", worker_type="document_generator")
    result = await worker.execute(task)
    assert "documents" in result


@pytest.mark.asyncio
async def test_custom_executor(registry):
    async def custom_fn(task):
        return {"custom": True, "task_id": task.id}

    registry.register_executor("research", custom_fn)
    worker = registry.get_worker("research")
    task = SubTask(id="t4", description="Custom research")
    result = await worker.execute(task)
    assert result["custom"] is True
    assert result["task_id"] == "t4"


# =========================================
# STATS RECORDING
# =========================================

def test_record_execution(registry):
    registry.record_execution("research", True, 5.0, 1500, 0.9)
    stats = registry.get_stats("research")
    assert stats.total_executions == 1
    assert stats.successful == 1
    assert stats.avg_latency_seconds == 5.0


def test_record_multiple_executions(registry):
    registry.record_execution("research", True, 4.0, 1000, 0.8)
    registry.record_execution("research", True, 6.0, 2000, 0.9)
    stats = registry.get_stats("research")
    assert stats.total_executions == 2
    assert stats.avg_latency_seconds == 5.0
    assert stats.avg_tokens_used == 1500


def test_record_failure(registry):
    registry.record_execution("research", False, 10.0, 500, 0.0)
    stats = registry.get_stats("research")
    assert stats.failed == 1
    assert stats.successful == 0


def test_get_all_stats(registry):
    all_stats = registry.get_all_stats()
    assert len(all_stats) == 8


def test_get_stats_nonexistent(registry):
    assert registry.get_stats("nonexistent") is None


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    r1 = get_worker_registry()
    r2 = get_worker_registry()
    assert r1 is r2
