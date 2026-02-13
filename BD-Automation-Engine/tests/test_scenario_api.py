"""Tests for Phase 51A — Strategic Scenario API."""

import pytest

from src.simulation.scenario_api import (
    StrategicScenarioAPI,
    ScenarioAnalysis,
    SensitivityResult,
    ScenarioMethod,
    get_scenario_api,
)


@pytest.fixture
def api():
    return StrategicScenarioAPI()


# =========================================
# NL SCENARIO ANALYSIS
# =========================================

def test_analyze_hire_reps(api):
    result = api.analyze_scenario("What if we hire 3 more BD reps?")
    assert isinstance(result, ScenarioAnalysis)
    assert result.method == ScenarioMethod.SIMULATION
    assert "team_size" in result.parsed_variables


def test_analyze_double_outreach(api):
    result = api.analyze_scenario("What if we double our outreach volume?")
    assert result.method == ScenarioMethod.SIMULATION
    assert "avg_calls_per_rep" in result.parsed_variables


def test_analyze_improve_win_rate(api):
    result = api.analyze_scenario("What if we improve win rate by 10 percent?")
    assert result.method == ScenarioMethod.SIMULATION
    assert "proposal_win_rate" in result.parsed_variables


def test_analyze_competitor_exits(api):
    result = api.analyze_scenario("What if a major competitor exits the market?")
    assert result.method == ScenarioMethod.SIMULATION
    assert "competitor_count" in result.parsed_variables


def test_analyze_clearance_delay(api):
    result = api.analyze_scenario("How sensitive is our pipeline to clearance delays?")
    assert result.method == ScenarioMethod.SENSITIVITY


def test_analyze_what_caused(api):
    result = api.analyze_scenario("What caused our Q4 pipeline drop?")
    assert result.method == ScenarioMethod.COUNTERFACTUAL
    assert "attribution" in result.result_details


def test_analyze_should_we_focus(api):
    result = api.analyze_scenario("Should we focus on Army or Navy DCGS?")
    assert result.method == ScenarioMethod.COMPARISON
    assert "scenarios" in result.result_details


def test_analyze_budget_cut(api):
    result = api.analyze_scenario("What if there's a 10 percent budget cut?")
    assert result.method == ScenarioMethod.SIMULATION


def test_analyze_unknown_defaults_simulation(api):
    result = api.analyze_scenario("Something completely random and unrelated")
    assert result.method == ScenarioMethod.SIMULATION


def test_analyze_has_summary(api):
    result = api.analyze_scenario("What if we hire 2 more reps?")
    assert len(result.result_summary) > 10


def test_analyze_has_confidence(api):
    result = api.analyze_scenario("What if we hire 2 more reps?")
    assert result.confidence > 0


def test_analyze_unique_id(api):
    r1 = api.analyze_scenario("Hire 2 reps")
    r2 = api.analyze_scenario("Hire 2 reps")
    assert r1.analysis_id != r2.analysis_id


# =========================================
# SENSITIVITY ANALYSIS
# =========================================

def test_sensitivity_team_size(api):
    result = api.sensitivity_analysis("team_size")
    assert isinstance(result, SensitivityResult)
    assert result.variable == "team_size"
    assert result.baseline_value == 8.0


def test_sensitivity_has_sweep(api):
    result = api.sensitivity_analysis("team_size")
    assert len(result.sweep_points) >= 10


def test_sensitivity_has_elasticity(api):
    result = api.sensitivity_analysis("team_size")
    assert result.elasticity != 0


def test_sensitivity_clearance(api):
    result = api.sensitivity_analysis("clearance_processing_weeks")
    assert result.elasticity < 0  # delays are negative


def test_sensitivity_competitor(api):
    result = api.sensitivity_analysis("competitor_count")
    assert result.elasticity < 0  # more competition is negative


def test_sensitivity_custom_range(api):
    result = api.sensitivity_analysis("team_size", range_pct=50.0)
    assert result.range_pct == 50.0
    # Should have more sweep points with wider range
    assert len(result.sweep_points) >= 15


def test_sensitivity_to_dict(api):
    result = api.sensitivity_analysis("team_size")
    d = result.to_dict()
    assert "sweep_points" in d
    assert "elasticity" in d


# =========================================
# PRESETS
# =========================================

def test_get_presets(api):
    presets = api.get_presets()
    assert len(presets) == 8


def test_presets_have_required_fields(api):
    presets = api.get_presets()
    for p in presets:
        assert p.preset_id != ""
        assert p.name != ""
        assert p.description != ""
        assert p.category != ""


def test_presets_filter_category(api):
    team_presets = api.get_presets(category="team")
    assert len(team_presets) >= 1
    assert all(p.category == "team" for p in team_presets)


def test_presets_filter_strategy(api):
    strategy = api.get_presets(category="strategy")
    assert len(strategy) >= 1


def test_presets_filter_risk(api):
    risk = api.get_presets(category="risk")
    assert len(risk) >= 1


def test_preset_to_dict(api):
    presets = api.get_presets()
    d = presets[0].to_dict()
    assert "preset_id" in d
    assert "variables" in d
    assert "method" in d


# =========================================
# QUERIES
# =========================================

def test_get_analysis(api):
    result = api.analyze_scenario("Hire 2 reps")
    fetched = api.get_analysis(result.analysis_id)
    assert fetched is not None


def test_get_analysis_not_found(api):
    assert api.get_analysis("sa_nonexistent") is None


def test_list_analyses(api):
    api.analyze_scenario("Hire 2 reps")
    api.analyze_scenario("Double outreach")
    analyses = api.list_analyses()
    assert len(analyses) == 2


# =========================================
# TO DICT
# =========================================

def test_analysis_to_dict(api):
    result = api.analyze_scenario("Hire 2 more reps")
    d = result.to_dict()
    assert "analysis_id" in d
    assert "method" in d
    assert "result_summary" in d
    assert "result_details" in d


# =========================================
# STATS
# =========================================

def test_stats(api):
    api.analyze_scenario("Hire 2 reps")
    api.sensitivity_analysis("team_size")
    stats = api.get_stats()
    assert stats["total_analyses"] >= 1
    assert stats["total_sensitivities"] >= 1
    assert stats["total_presets"] == 8


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    import src.simulation.scenario_api as mod
    mod._instance = None
    s1 = get_scenario_api()
    s2 = get_scenario_api()
    assert s1 is s2
    mod._instance = None
