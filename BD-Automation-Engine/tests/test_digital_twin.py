"""Tests for Phase 51A — BD Digital Twin."""

import pytest

from src.simulation.digital_twin import (
    BDDigitalTwin,
    DigitalTwinState,
    SimulationResult,
    ScenarioComparison,
    CalibrationReport,
    Intervention,
    get_digital_twin,
)


@pytest.fixture
def dt():
    return BDDigitalTwin()


# =========================================
# TWIN CREATION
# =========================================

def test_create_twin(dt):
    twin = dt.create_twin()
    assert isinstance(twin, DigitalTwinState)
    assert twin.total_contacts == 150
    assert twin.team_size == 8


def test_create_twin_with_date(dt):
    twin = dt.create_twin(snapshot_date="2025-01-01T00:00:00")
    assert twin.snapshot_date == "2025-01-01T00:00:00"


def test_twin_id_unique(dt):
    t1 = dt.create_twin()
    t2 = dt.create_twin()
    assert t1.twin_id != t2.twin_id


def test_get_twin(dt):
    twin = dt.create_twin()
    fetched = dt.get_twin(twin.twin_id)
    assert fetched is not None
    assert fetched.twin_id == twin.twin_id


def test_get_twin_not_found(dt):
    assert dt.get_twin("twin_nonexistent") is None


def test_list_twins(dt):
    dt.create_twin()
    dt.create_twin()
    assert len(dt.list_twins()) == 2


def test_twin_to_dict(dt):
    twin = dt.create_twin()
    d = twin.to_dict()
    assert "twin_id" in d
    assert "pipeline_value_m" in d
    assert "team_size" in d


# =========================================
# SIMULATION
# =========================================

def test_simulate_basic(dt):
    twin = dt.create_twin()
    result = dt.simulate(twin.twin_id, days=90, monte_carlo_runs=100)
    assert isinstance(result, SimulationResult)
    assert result.expected_pipeline_value_m > 0
    assert result.expected_revenue_m >= 0


def test_simulate_has_confidence_intervals(dt):
    twin = dt.create_twin()
    result = dt.simulate(twin.twin_id, days=90, monte_carlo_runs=200)
    assert result.pipeline_ci_lower < result.pipeline_ci_upper
    assert result.pipeline_ci_lower <= result.expected_pipeline_value_m


def test_simulate_has_placements(dt):
    twin = dt.create_twin()
    result = dt.simulate(twin.twin_id, days=90, monte_carlo_runs=100)
    assert result.expected_placements >= 0


def test_simulate_convergence(dt):
    twin = dt.create_twin()
    result = dt.simulate(twin.twin_id, days=90, monte_carlo_runs=500)
    assert result.convergence_score > 0


def test_simulate_unknown_twin(dt):
    with pytest.raises(ValueError, match="Twin not found"):
        dt.simulate("twin_fake")


def test_simulate_with_interventions(dt):
    twin = dt.create_twin()
    interventions = [
        Intervention(variable="team_size", action="increase", value=4,
                     description="Hire 4 more BD reps"),
    ]
    result_with = dt.simulate(twin.twin_id, days=90,
                               interventions=interventions, monte_carlo_runs=200)
    result_without = dt.simulate(twin.twin_id, days=90, monte_carlo_runs=200)
    # More team → more pipeline (on average, with some MC variance)
    # We don't assert strictly since MC is random, just check it ran
    assert result_with.expected_pipeline_value_m > 0
    assert result_without.expected_pipeline_value_m > 0


def test_simulate_multiply_intervention(dt):
    twin = dt.create_twin()
    interventions = [
        Intervention(variable="avg_calls_per_rep", action="multiply", value=2.0),
    ]
    result = dt.simulate(twin.twin_id, days=90, interventions=interventions,
                          monte_carlo_runs=100)
    assert result.days_simulated == 90


def test_simulate_different_days(dt):
    twin = dt.create_twin()
    r30 = dt.simulate(twin.twin_id, days=30, monte_carlo_runs=100)
    r180 = dt.simulate(twin.twin_id, days=180, monte_carlo_runs=100)
    assert r30.days_simulated == 30
    assert r180.days_simulated == 180


def test_simulation_to_dict(dt):
    twin = dt.create_twin()
    result = dt.simulate(twin.twin_id, days=90, monte_carlo_runs=100)
    d = result.to_dict()
    assert "expected_pipeline_value_m" in d
    assert "pipeline_ci" in d
    assert "convergence_score" in d


# =========================================
# SCENARIO COMPARISON
# =========================================

def test_compare_scenarios(dt):
    twin = dt.create_twin()
    scenarios = [
        {"name": "Status Quo", "interventions": []},
        {"name": "Hire 2 Reps", "interventions": [
            {"variable": "team_size", "action": "increase", "value": 2}
        ]},
        {"name": "Double Outreach", "interventions": [
            {"variable": "avg_calls_per_rep", "action": "multiply", "value": 2.0}
        ]},
    ]
    result = dt.compare_scenarios(twin.twin_id, scenarios, monte_carlo_runs=100)
    assert isinstance(result, ScenarioComparison)
    assert len(result.scenarios) == 3
    assert result.winner is not None


def test_compare_has_per_scenario_results(dt):
    twin = dt.create_twin()
    scenarios = [
        {"name": "A", "interventions": []},
        {"name": "B", "interventions": [
            {"variable": "team_size", "action": "increase", "value": 3}
        ]},
    ]
    result = dt.compare_scenarios(twin.twin_id, scenarios, monte_carlo_runs=100)
    for s in result.scenarios:
        assert "expected_pipeline_m" in s
        assert "expected_revenue_m" in s


def test_compare_to_dict(dt):
    twin = dt.create_twin()
    result = dt.compare_scenarios(twin.twin_id, [
        {"name": "A", "interventions": []},
    ], monte_carlo_runs=50)
    d = result.to_dict()
    assert "scenarios" in d
    assert "winner" in d


# =========================================
# CALIBRATION
# =========================================

def test_calibrate(dt):
    twin = dt.create_twin()
    report = dt.calibrate(twin.twin_id)
    assert isinstance(report, CalibrationReport)
    assert report.overall_accuracy > 0


def test_calibrate_has_errors(dt):
    twin = dt.create_twin()
    report = dt.calibrate(twin.twin_id)
    assert "pipeline_value" in report.metric_errors
    assert "placement_rate" in report.metric_errors


def test_calibrate_has_recommendations(dt):
    twin = dt.create_twin()
    report = dt.calibrate(twin.twin_id)
    assert len(report.recommendations) >= 1


def test_calibrate_unknown_twin(dt):
    with pytest.raises(ValueError, match="Twin not found"):
        dt.calibrate("twin_fake")


def test_get_latest_calibration(dt):
    twin = dt.create_twin()
    dt.calibrate(twin.twin_id)
    report = dt.get_latest_calibration(twin.twin_id)
    assert report is not None


def test_get_latest_calibration_none(dt):
    assert dt.get_latest_calibration("twin_fake") is None


def test_calibration_to_dict(dt):
    twin = dt.create_twin()
    report = dt.calibrate(twin.twin_id)
    d = report.to_dict()
    assert "overall_accuracy" in d
    assert "metric_errors" in d


# =========================================
# SIMULATION HISTORY
# =========================================

def test_simulation_history(dt):
    twin = dt.create_twin()
    dt.simulate(twin.twin_id, monte_carlo_runs=50)
    dt.simulate(twin.twin_id, monte_carlo_runs=50)
    history = dt.get_simulation_history()
    assert len(history) >= 2


# =========================================
# STATS
# =========================================

def test_stats(dt):
    twin = dt.create_twin()
    dt.simulate(twin.twin_id, monte_carlo_runs=50)
    stats = dt.get_stats()
    assert stats["total_twins"] >= 1
    assert stats["total_simulations"] >= 1


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    import src.simulation.digital_twin as mod
    mod._instance = None
    s1 = get_digital_twin()
    s2 = get_digital_twin()
    assert s1 is s2
    mod._instance = None
