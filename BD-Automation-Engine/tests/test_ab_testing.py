"""Tests for Phase 55A — A/B Testing Framework."""

import pytest

from src.experimentation.ab_testing import (
    ABTestingFramework,
    Experiment,
    ExperimentStatus,
    get_ab_framework,
)


@pytest.fixture
def ab():
    return ABTestingFramework()


# =========================================
# CREATE EXPERIMENTS
# =========================================


def test_create_experiment(ab):
    exp = ab.create_experiment(
        name="test_exp",
        hypothesis="Testing improves conversion",
        metric_name="conversion_rate",
        variants=[
            {"name": "control", "weight": 50},
            {"name": "treatment", "weight": 50},
        ],
    )
    assert isinstance(exp, Experiment)
    assert exp.experiment_id.startswith("exp_")
    assert len(exp.variants) == 2


def test_control_variant_marked(ab):
    exp = ab.create_experiment(
        name="test",
        variants=[
            {"name": "control", "weight": 50},
            {"name": "treatment", "weight": 50},
        ],
    )
    control = [v for v in exp.variants if v.is_control]
    assert len(control) == 1


# =========================================
# LIFECYCLE
# =========================================


def test_start_experiment(ab):
    exp = ab.create_experiment(
        name="start_test",
        variants=[
            {"name": "A", "weight": 50},
            {"name": "B", "weight": 50},
        ],
    )
    ab.start_experiment(exp.experiment_id)
    e = ab.get_experiment(exp.experiment_id)
    assert e.status == ExperimentStatus.RUNNING


def test_pause_experiment(ab):
    exp = ab.create_experiment(
        name="pause_test",
        variants=[
            {"name": "A", "weight": 50},
            {"name": "B", "weight": 50},
        ],
    )
    ab.start_experiment(exp.experiment_id)
    ab.pause_experiment(exp.experiment_id)
    e = ab.get_experiment(exp.experiment_id)
    assert e.status == ExperimentStatus.PAUSED


def test_complete_experiment(ab):
    exp = ab.create_experiment(
        name="complete_test",
        variants=[
            {"name": "A", "weight": 50},
            {"name": "B", "weight": 50},
        ],
    )
    ab.start_experiment(exp.experiment_id)
    ab.complete_experiment(exp.experiment_id)
    e = ab.get_experiment(exp.experiment_id)
    assert e.status == ExperimentStatus.COMPLETED


# =========================================
# ASSIGNMENT
# =========================================


def test_assign_user(ab):
    exp = ab.create_experiment(
        name="assign_test",
        variants=[
            {"name": "A", "weight": 50},
            {"name": "B", "weight": 50},
        ],
    )
    ab.start_experiment(exp.experiment_id)
    vid = ab.assign_user(exp.experiment_id, "user1")
    assert vid in [v.variant_id for v in exp.variants]


def test_assign_increases_count(ab):
    exp = ab.create_experiment(
        name="count_test",
        variants=[
            {"name": "A", "weight": 50},
            {"name": "B", "weight": 50},
        ],
    )
    ab.start_experiment(exp.experiment_id)
    ab.assign_user(exp.experiment_id, "user1")
    total = sum(v.assignments for v in exp.variants)
    assert total == 1


# =========================================
# CONVERSIONS
# =========================================


def test_record_conversion(ab):
    exp = ab.create_experiment(
        name="conv_test",
        variants=[
            {"name": "A", "weight": 50},
            {"name": "B", "weight": 50},
        ],
    )
    ab.start_experiment(exp.experiment_id)
    vid = ab.assign_user(exp.experiment_id, "user1")
    ab.record_conversion(exp.experiment_id, vid, value=10.0)
    variant = [v for v in exp.variants if v.variant_id == vid][0]
    assert variant.conversions == 1
    assert variant.revenue == 10.0


# =========================================
# RESULTS
# =========================================


def test_get_results(ab):
    exp = ab.create_experiment(
        name="results_test",
        variants=[
            {"name": "control", "weight": 50},
            {"name": "treatment", "weight": 50},
        ],
    )
    ab.start_experiment(exp.experiment_id)
    for i in range(100):
        vid = ab.assign_user(exp.experiment_id, f"user_{i}")
        if i % 10 == 0:
            ab.record_conversion(exp.experiment_id, vid)
    results = ab.get_results(exp.experiment_id)
    assert "variants" in results
    assert "comparisons" in results
    assert "recommendation" in results


def test_results_has_conversion_rate(ab):
    exp = ab.create_experiment(
        name="rate_test",
        variants=[
            {"name": "control", "weight": 50},
            {"name": "treatment", "weight": 50},
        ],
    )
    ab.start_experiment(exp.experiment_id)
    for i in range(50):
        vid = ab.assign_user(exp.experiment_id, f"user_{i}")
        if i % 5 == 0:
            ab.record_conversion(exp.experiment_id, vid)
    results = ab.get_results(exp.experiment_id)
    for v in results["variants"]:
        assert "conversion_rate" in v


# =========================================
# QUERIES
# =========================================


def test_list_experiments(ab):
    ab.create_experiment(
        name="e1",
        variants=[
            {"name": "A", "weight": 50},
            {"name": "B", "weight": 50},
        ],
    )
    ab.create_experiment(
        name="e2",
        variants=[
            {"name": "A", "weight": 50},
            {"name": "B", "weight": 50},
        ],
    )
    exps = ab.list_experiments()
    assert len(exps) == 2


def test_list_by_status(ab):
    e1 = ab.create_experiment(
        name="e1",
        variants=[
            {"name": "A", "weight": 50},
            {"name": "B", "weight": 50},
        ],
    )
    ab.start_experiment(e1.experiment_id)
    ab.create_experiment(
        name="e2",
        variants=[
            {"name": "A", "weight": 50},
            {"name": "B", "weight": 50},
        ],
    )
    running = ab.list_experiments(status=ExperimentStatus.RUNNING)
    assert len(running) == 1


def test_get_experiment_not_found(ab):
    assert ab.get_experiment("exp_fake") is None


# =========================================
# TO_DICT & STATS
# =========================================


def test_experiment_to_dict(ab):
    exp = ab.create_experiment(
        name="dict_test",
        variants=[
            {"name": "A", "weight": 50},
            {"name": "B", "weight": 50},
        ],
    )
    d = exp.to_dict()
    assert "experiment_id" in d
    assert "variants" in d
    assert "status" in d


def test_stats(ab):
    ab.create_experiment(
        name="s1",
        variants=[
            {"name": "A", "weight": 50},
            {"name": "B", "weight": 50},
        ],
    )
    stats = ab.get_stats()
    assert stats["total_experiments"] == 1


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    import src.experimentation.ab_testing as mod

    mod._instance = None
    a1 = get_ab_framework()
    a2 = get_ab_framework()
    assert a1 is a2
    mod._instance = None
