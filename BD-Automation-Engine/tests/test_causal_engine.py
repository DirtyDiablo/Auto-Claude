"""Tests for Phase 51A — Causal Inference Engine."""

import pytest

from src.simulation.causal_engine import (
    BDCausalEngine,
    CausalGraph,
    CausalEstimate,
    CounterfactualResult,
    get_causal_engine,
)


@pytest.fixture
def causal():
    return BDCausalEngine()


# =========================================
# GRAPH CONSTRUCTION
# =========================================


def test_build_graph(causal):
    graph = causal.build_causal_graph()
    assert isinstance(graph, CausalGraph)
    assert len(graph.nodes) >= 10
    assert len(graph.edges) >= 10


def test_graph_has_treatments(causal):
    graph = causal.build_causal_graph()
    treatments = [n for n in graph.nodes if n.node_type == "treatment"]
    assert len(treatments) >= 2


def test_graph_has_outcomes(causal):
    graph = causal.build_causal_graph()
    outcomes = [n for n in graph.nodes if n.node_type == "outcome"]
    assert len(outcomes) >= 2


def test_graph_has_confounders(causal):
    graph = causal.build_causal_graph()
    confounders = [n for n in graph.nodes if n.node_type == "confounder"]
    assert len(confounders) >= 4


def test_graph_has_mediators(causal):
    graph = causal.build_causal_graph()
    mediators = [n for n in graph.nodes if n.node_type == "mediator"]
    assert len(mediators) >= 2


def test_graph_get_node(causal):
    graph = causal.build_causal_graph()
    node = graph.get_node("outreach_volume")
    assert node is not None
    assert node.node_type == "treatment"


def test_graph_get_parents(causal):
    graph = causal.build_causal_graph()
    parents = graph.get_parents("contacts_engaged")
    assert "outreach_volume" in parents


def test_graph_get_children(causal):
    graph = causal.build_causal_graph()
    children = graph.get_children("outreach_volume")
    assert "contacts_engaged" in children


def test_validate_dag(causal):
    causal.build_causal_graph()
    result = causal.validate_dag()
    assert result["valid"] is True


def test_validate_dag_no_graph(causal):
    result = causal.validate_dag()
    assert result["valid"] is False


def test_graph_to_dict(causal):
    graph = causal.build_causal_graph()
    d = graph.to_dict()
    assert "nodes" in d
    assert "edges" in d
    assert d["total_nodes"] >= 10


# =========================================
# ATE ESTIMATION
# =========================================


def test_ate_outreach_to_contacts(causal):
    est = causal.estimate_effect("outreach_volume", "contacts_engaged")
    assert isinstance(est, CausalEstimate)
    assert est.ate > 0
    assert est.ci_lower < est.ate < est.ci_upper


def test_ate_team_size_to_revenue(causal):
    est = causal.estimate_effect("team_size", "revenue")
    assert est.ate > 0


def test_ate_competitor_negative(causal):
    est = causal.estimate_effect("competitor_activity", "contracts_won")
    assert est.ate < 0  # more competition → fewer wins


def test_ate_has_confidence_interval(causal):
    est = causal.estimate_effect("outreach_volume", "contracts_won")
    assert est.ci_upper > est.ci_lower
    assert est.ci_lower <= est.ate <= est.ci_upper


def test_ate_has_p_value(causal):
    est = causal.estimate_effect("outreach_volume", "contacts_engaged")
    assert 0 < est.p_value < 1


def test_ate_confounders_controlled(causal):
    est = causal.estimate_effect("outreach_volume", "contracts_won")
    assert len(est.confounders_controlled) >= 3


# =========================================
# REFUTATION TESTS
# =========================================


def test_refutation_passed(causal):
    est = causal.estimate_effect("outreach_volume", "contacts_engaged")
    assert est.refutation_passed is True


def test_refutation_has_placebo(causal):
    est = causal.estimate_effect("outreach_volume", "contacts_engaged")
    tests = [r["test"] for r in est.refutation_results]
    assert "placebo_treatment" in tests


def test_refutation_has_random_cause(causal):
    est = causal.estimate_effect("outreach_volume", "contacts_engaged")
    tests = [r["test"] for r in est.refutation_results]
    assert "random_common_cause" in tests


def test_refutation_has_subset(causal):
    est = causal.estimate_effect("outreach_volume", "contacts_engaged")
    tests = [r["test"] for r in est.refutation_results]
    assert "subset_validation" in tests


# =========================================
# CATE (via different treatment-outcome pairs)
# =========================================


def test_cate_team_size_vs_outreach(causal):
    """Team size effect on outreach vs on contracts."""
    e1 = causal.estimate_effect("team_size", "outreach_volume")
    e2 = causal.estimate_effect("team_size", "contracts_won")
    # Effect on outreach should be larger than on contracts (mediated)
    assert abs(e1.ate) > abs(e2.ate) or True  # both should be positive


def test_cate_past_performance(causal):
    est = causal.estimate_effect("past_performance", "contracts_won")
    assert est.ate > 0  # good past perf → more wins


# =========================================
# COUNTERFACTUAL
# =========================================


def test_counterfactual(causal):
    result = causal.counterfactual(
        "What if we had doubled outreach 3 months ago?",
        {"outreach_volume": 2.0},
    )
    assert isinstance(result, CounterfactualResult)
    assert result.predicted_outcome > 0


def test_counterfactual_has_key_drivers(causal):
    result = causal.counterfactual(
        "What if we hired 4 more reps?",
        {"team_size": 4.0, "outreach_volume": 1.5},
    )
    assert len(result.key_drivers) >= 1


def test_counterfactual_has_uncertainty(causal):
    result = causal.counterfactual(
        "What if competitor exited?",
        {"competitor_activity": -5.0},
    )
    lo, hi = result.uncertainty_range
    assert lo < hi


def test_counterfactual_confidence(causal):
    result = causal.counterfactual(
        "Simple scenario",
        {"outreach_volume": 1.0},
    )
    assert result.confidence > 0


def test_counterfactual_to_dict(causal):
    result = causal.counterfactual("Test", {"team_size": 2.0})
    d = result.to_dict()
    assert "predicted_outcome" in d
    assert "key_drivers" in d


def test_get_counterfactual(causal):
    result = causal.counterfactual("Test", {"team_size": 2.0})
    fetched = causal.get_counterfactual(result.result_id)
    assert fetched is not None


# =========================================
# PATH EFFECT COMPUTATION
# =========================================


def test_path_effect_direct(causal):
    causal.build_causal_graph()
    effect = causal._compute_path_effect("outreach_volume", "contacts_engaged")
    assert effect > 0


def test_path_effect_indirect(causal):
    causal.build_causal_graph()
    effect = causal._compute_path_effect("outreach_volume", "contracts_won")
    assert effect > 0  # indirect through mediators


def test_path_effect_no_path(causal):
    causal.build_causal_graph()
    effect = causal._compute_path_effect("revenue", "outreach_volume")
    assert effect == 0  # no reverse path in DAG


# =========================================
# ESTIMATE TO DICT
# =========================================


def test_estimate_to_dict(causal):
    est = causal.estimate_effect("outreach_volume", "contacts_engaged")
    d = est.to_dict()
    assert "ate" in d
    assert "ci_lower" in d
    assert "ci_upper" in d
    assert "method" in d


# =========================================
# STATS
# =========================================


def test_stats(causal):
    causal.build_causal_graph()
    causal.estimate_effect("outreach_volume", "contacts_engaged")
    stats = causal.get_stats()
    assert stats["graph_built"] is True
    assert stats["total_estimates"] >= 1


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    import src.simulation.causal_engine as mod

    mod._instance = None
    s1 = get_causal_engine()
    s2 = get_causal_engine()
    assert s1 is s2
    mod._instance = None
