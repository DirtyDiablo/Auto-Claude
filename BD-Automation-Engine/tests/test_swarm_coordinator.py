"""Tests for Phase 41A — Swarm Coordinator."""

import pytest

from src.agents.swarm.coordinator import (
    SwarmCoordinator,
    SwarmTask,
    SwarmResult,
    SwarmStatus,
    WorkerResult,
    get_swarm_coordinator,
)
from src.agents.swarm.workers import WorkerStatus as WStatus


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def coordinator():
    return SwarmCoordinator()


@pytest.fixture
def simple_task():
    return SwarmTask(
        description="Build a BD campaign for DCGS program at Langley",
        task_type="campaign_build",
        coordination_mode="parallel",
    )


@pytest.fixture
def enrichment_task():
    return SwarmTask(
        description="Enrich and validate contacts at Leidos",
        task_type="contact_enrichment",
    )


# =========================================
# EXECUTE SWARM
# =========================================

@pytest.mark.asyncio
async def test_execute_swarm_returns_result(coordinator, simple_task):
    result = await coordinator.execute_swarm(simple_task)
    assert isinstance(result, SwarmResult)
    assert result.swarm_id != ""
    assert result.status == SwarmStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_execute_swarm_has_workers(coordinator, simple_task):
    result = await coordinator.execute_swarm(simple_task)
    assert result.workers_used > 0
    assert len(result.worker_results) > 0


@pytest.mark.asyncio
async def test_execute_swarm_has_output(coordinator, simple_task):
    result = await coordinator.execute_swarm(simple_task)
    assert "summary" in result.output
    assert "details" in result.output
    assert result.output["summary"]["total_workers"] > 0


@pytest.mark.asyncio
async def test_execute_swarm_has_dag(coordinator, simple_task):
    result = await coordinator.execute_swarm(simple_task)
    assert result.dag is not None
    assert len(result.dag.nodes) > 0
    assert len(result.dag.execution_layers) > 0


@pytest.mark.asyncio
async def test_execute_swarm_has_cost_estimate(coordinator, simple_task):
    result = await coordinator.execute_swarm(simple_task)
    assert result.cost_estimate is not None
    assert result.cost_estimate.total_tokens > 0


@pytest.mark.asyncio
async def test_execute_swarm_has_provenance(coordinator, simple_task):
    result = await coordinator.execute_swarm(simple_task)
    assert "coordination_mode" in result.provenance
    assert "layers_executed" in result.provenance
    assert result.provenance["coordination_mode"] == "parallel"


@pytest.mark.asyncio
async def test_execute_swarm_quality_score(coordinator, simple_task):
    result = await coordinator.execute_swarm(simple_task)
    assert result.quality_score > 0.0
    assert result.quality_score <= 1.0


@pytest.mark.asyncio
async def test_execute_swarm_timing(coordinator, simple_task):
    result = await coordinator.execute_swarm(simple_task)
    assert result.total_time_seconds >= 0.0


# =========================================
# COORDINATION MODES
# =========================================

@pytest.mark.asyncio
async def test_sequential_mode(coordinator):
    task = SwarmTask(
        description="Weekly briefing for DCGS",
        task_type="weekly_briefing",
        coordination_mode="sequential",
    )
    result = await coordinator.execute_swarm(task)
    assert result.status == SwarmStatus.COMPLETED.value
    assert result.provenance["coordination_mode"] == "sequential"


@pytest.mark.asyncio
async def test_pipeline_mode(coordinator):
    task = SwarmTask(
        description="Analyze DCGS program",
        task_type="program_analysis",
        coordination_mode="pipeline",
    )
    result = await coordinator.execute_swarm(task)
    assert result.status == SwarmStatus.COMPLETED.value
    assert result.provenance["coordination_mode"] == "pipeline"


@pytest.mark.asyncio
async def test_consensus_mode(coordinator):
    task = SwarmTask(
        description="Research competitor Leidos on DCGS",
        task_type="competitive_analysis",
        coordination_mode="consensus",
    )
    result = await coordinator.execute_swarm(task)
    assert result.status == SwarmStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_map_reduce_mode(coordinator):
    task = SwarmTask(
        description="Contact enrichment for GDIT",
        task_type="contact_enrichment",
        coordination_mode="map_reduce",
    )
    result = await coordinator.execute_swarm(task)
    assert result.status == SwarmStatus.COMPLETED.value


# =========================================
# MONITORING & CANCELLATION
# =========================================

@pytest.mark.asyncio
async def test_monitor_nonexistent(coordinator):
    state = await coordinator.monitor_swarm("nonexistent")
    assert state is None


@pytest.mark.asyncio
async def test_cancel_nonexistent(coordinator):
    cancelled = await coordinator.cancel_swarm("nonexistent")
    assert cancelled is False


@pytest.mark.asyncio
async def test_swarm_appears_in_history(coordinator, simple_task):
    result = await coordinator.execute_swarm(simple_task)
    history = coordinator.get_history()
    assert len(history) >= 1
    assert history[-1].swarm_id == result.swarm_id


# =========================================
# ENRICHMENT TASK
# =========================================

@pytest.mark.asyncio
async def test_enrichment_task(coordinator, enrichment_task):
    result = await coordinator.execute_swarm(enrichment_task)
    assert result.status == SwarmStatus.COMPLETED.value
    assert result.workers_used > 0


# =========================================
# QUALITY COMPUTATION
# =========================================

def test_compute_quality_all_completed(coordinator):
    results = [
        WorkerResult(status=WStatus.COMPLETED.value, quality_score=0.9),
        WorkerResult(status=WStatus.COMPLETED.value, quality_score=0.8),
    ]
    q = coordinator._compute_quality(results)
    assert q > 0.7


def test_compute_quality_with_failures(coordinator):
    results = [
        WorkerResult(status=WStatus.COMPLETED.value, quality_score=0.9),
        WorkerResult(status=WStatus.FAILED.value, error="fail", quality_score=0.0),
    ]
    q = coordinator._compute_quality(results)
    assert q < 0.9  # Penalized for failure


def test_compute_quality_empty(coordinator):
    assert coordinator._compute_quality([]) == 0.0


def test_compute_quality_all_failed(coordinator):
    results = [
        WorkerResult(status=WStatus.FAILED.value, error="fail"),
    ]
    q = coordinator._compute_quality(results)
    assert q == 0.0


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    c1 = get_swarm_coordinator()
    c2 = get_swarm_coordinator()
    assert c1 is c2
