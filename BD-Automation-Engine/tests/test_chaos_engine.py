"""Tests for Phase 54A — Chaos Experiment Engine."""

import pytest

from src.resilience.chaos_engine import (
    ChaosExperimentEngine,
    ChaosExperiment,
    FaultType,
    ExperimentStatus,
    SteadyStateHypothesis,
    get_chaos_engine,
)


@pytest.fixture
def engine():
    return ChaosExperimentEngine()


# =========================================
# CREATE EXPERIMENTS
# =========================================


def test_create_experiment(engine):
    exp = engine.create_experiment(
        name="test_latency",
        fault_type=FaultType.LATENCY,
        target_service="qdrant_search",
    )
    assert isinstance(exp, ChaosExperiment)
    assert exp.experiment_id.startswith("chaos_")
    assert exp.status == ExperimentStatus.PENDING


def test_create_with_intensity(engine):
    exp = engine.create_experiment(
        name="high_error_rate",
        fault_type=FaultType.ERROR,
        target_service="api_gateway",
        intensity=0.8,
    )
    assert exp.intensity == 0.8


def test_create_with_duration(engine):
    exp = engine.create_experiment(
        name="long_test",
        fault_type=FaultType.TIMEOUT,
        target_service="n8n_workflow",
        duration_sec=120.0,
    )
    assert exp.duration_sec == 120.0


# =========================================
# RUN EXPERIMENTS
# =========================================


def test_run_experiment(engine):
    exp = engine.create_experiment(
        name="latency_test",
        fault_type=FaultType.LATENCY,
        target_service="qdrant_search",
    )
    result = engine.run_experiment(exp.experiment_id)
    assert result is not None
    assert result.status == ExperimentStatus.COMPLETED
    assert "latency_added_ms" in result.results


def test_run_error_experiment(engine):
    exp = engine.create_experiment(
        name="error_test",
        fault_type=FaultType.ERROR,
        target_service="api_gateway",
    )
    result = engine.run_experiment(exp.experiment_id)
    assert "errors_injected" in result.results


def test_run_timeout_experiment(engine):
    exp = engine.create_experiment(
        name="timeout_test",
        fault_type=FaultType.TIMEOUT,
        target_service="n8n_workflow",
    )
    result = engine.run_experiment(exp.experiment_id)
    assert "timeouts_injected" in result.results


def test_run_resource_exhaustion(engine):
    exp = engine.create_experiment(
        name="resource_test",
        fault_type=FaultType.RESOURCE_EXHAUSTION,
        target_service="agent_executor",
    )
    result = engine.run_experiment(exp.experiment_id)
    assert "memory_pressure_pct" in result.results


def test_run_network_partition(engine):
    exp = engine.create_experiment(
        name="partition_test",
        fault_type=FaultType.NETWORK_PARTITION,
        target_service="bullhorn_etl",
    )
    result = engine.run_experiment(exp.experiment_id)
    assert "packets_dropped" in result.results


def test_run_not_found(engine):
    assert engine.run_experiment("chaos_nonexistent") is None


# =========================================
# ABORT
# =========================================


def test_abort_experiment(engine):
    exp = engine.create_experiment(
        name="abort_test",
        fault_type=FaultType.LATENCY,
        target_service="qdrant_search",
    )
    result = engine.abort_experiment(exp.experiment_id)
    assert result is True


def test_abort_not_found(engine):
    assert engine.abort_experiment("chaos_nonexistent") is False


# =========================================
# QUERIES
# =========================================


def test_get_experiment(engine):
    exp = engine.create_experiment(
        name="q_test",
        fault_type=FaultType.LATENCY,
        target_service="qdrant_search",
    )
    fetched = engine.get_experiment(exp.experiment_id)
    assert fetched is not None
    assert fetched.name == "q_test"


def test_list_experiments(engine):
    engine.create_experiment("e1", FaultType.LATENCY, "qdrant_search")
    engine.create_experiment("e2", FaultType.ERROR, "api_gateway")
    exps = engine.list_experiments()
    assert len(exps) == 2


def test_list_by_status(engine):
    e1 = engine.create_experiment("e1", FaultType.LATENCY, "qdrant_search")
    engine.run_experiment(e1.experiment_id)
    engine.create_experiment("e2", FaultType.ERROR, "api_gateway")
    completed = engine.list_experiments(status=ExperimentStatus.COMPLETED)
    assert len(completed) == 1


# =========================================
# TEMPLATES
# =========================================


def test_list_templates(engine):
    templates = engine.list_templates()
    assert len(templates) == 5


# =========================================
# STEADY STATE
# =========================================


def test_verify_steady_state(engine):
    hyp = SteadyStateHypothesis(
        metric_name="api_availability_pct",
        operator="gt",
        threshold=99.0,
    )
    result = engine.verify_steady_state(hyp)
    assert "passed" in result
    assert "measured_value" in result


# =========================================
# TO_DICT & STATS
# =========================================


def test_experiment_to_dict(engine):
    exp = engine.create_experiment("t", FaultType.LATENCY, "qdrant_search")
    d = exp.to_dict()
    assert "experiment_id" in d
    assert "fault_type" in d


def test_stats(engine):
    engine.create_experiment("e1", FaultType.LATENCY, "qdrant_search")
    stats = engine.get_stats()
    assert stats["total_experiments"] == 1
    assert stats["templates_available"] == 5


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    import src.resilience.chaos_engine as mod

    mod._instance = None
    e1 = get_chaos_engine()
    e2 = get_chaos_engine()
    assert e1 is e2
    mod._instance = None
