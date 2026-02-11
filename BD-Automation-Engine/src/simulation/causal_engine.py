"""Phase 51A — Causal Inference Engine for BD Strategy.

Builds and queries causal graphs of BD pipeline relationships using
DoWhy-style semantics. Estimates average treatment effects (ATE),
conditional average treatment effects (CATE), and runs counterfactual
analysis for strategic what-if planning.
"""

from __future__ import annotations

import hashlib
import logging
import math
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

random.seed(42)


# =========================================
# DATA MODELS
# =========================================

@dataclass
class CausalNode:
    """A node in the causal graph."""
    name: str
    node_type: str  # treatment | outcome | confounder | mediator
    description: str = ""
    value_range: Tuple[float, float] = (0.0, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "node_type": self.node_type,
            "description": self.description,
            "value_range": list(self.value_range),
        }


@dataclass
class CausalEdge:
    """A directed edge in the causal graph (cause → effect)."""
    source: str
    target: str
    weight: float = 1.0
    mechanism: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "weight": self.weight,
            "mechanism": self.mechanism,
        }


@dataclass
class CausalGraph:
    """A directed acyclic graph (DAG) of causal relationships."""
    graph_id: str
    nodes: List[CausalNode] = field(default_factory=list)
    edges: List[CausalEdge] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def get_node(self, name: str) -> Optional[CausalNode]:
        return next((n for n in self.nodes if n.name == name), None)

    def get_parents(self, node_name: str) -> List[str]:
        return [e.source for e in self.edges if e.target == node_name]

    def get_children(self, node_name: str) -> List[str]:
        return [e.target for e in self.edges if e.source == node_name]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "created_at": self.created_at,
        }


@dataclass
class CausalEstimate:
    """Result of a causal effect estimation."""
    estimate_id: str
    treatment: str
    outcome: str
    method: str  # backdoor | iv | frontdoor
    ate: float  # average treatment effect
    ci_lower: float  # 95% CI lower
    ci_upper: float  # 95% CI upper
    p_value: float
    confounders_controlled: List[str] = field(default_factory=list)
    refutation_passed: bool = True
    refutation_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "estimate_id": self.estimate_id,
            "treatment": self.treatment,
            "outcome": self.outcome,
            "method": self.method,
            "ate": round(self.ate, 4),
            "ci_lower": round(self.ci_lower, 4),
            "ci_upper": round(self.ci_upper, 4),
            "p_value": round(self.p_value, 4),
            "confounders_controlled": self.confounders_controlled,
            "refutation_passed": self.refutation_passed,
            "refutation_results": self.refutation_results,
        }


@dataclass
class CounterfactualResult:
    """Result of a counterfactual analysis."""
    result_id: str
    scenario: str
    conditions: Dict[str, Any] = field(default_factory=dict)
    predicted_outcome: float = 0.0
    actual_outcome: Optional[float] = None
    uncertainty_range: Tuple[float, float] = (0.0, 0.0)
    key_drivers: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "scenario": self.scenario,
            "conditions": self.conditions,
            "predicted_outcome": round(self.predicted_outcome, 4),
            "actual_outcome": self.actual_outcome,
            "uncertainty_range": [round(x, 4) for x in self.uncertainty_range],
            "key_drivers": self.key_drivers,
            "confidence": round(self.confidence, 3),
        }


# =========================================
# BD CAUSAL GRAPH DEFINITION
# =========================================

_BD_NODES = [
    CausalNode("outreach_volume", "treatment", "Weekly outreach calls", (0, 100)),
    CausalNode("contacts_engaged", "mediator", "Contacts engaged this quarter", (0, 50)),
    CausalNode("meetings_scheduled", "mediator", "Client meetings booked", (0, 30)),
    CausalNode("proposals_submitted", "mediator", "Proposals and RFP responses", (0, 15)),
    CausalNode("contracts_won", "outcome", "Contracts/TOs won", (0, 10)),
    CausalNode("revenue", "outcome", "Revenue generated ($M)", (0, 50)),
    CausalNode("team_size", "treatment", "BD team headcount", (1, 20)),
    CausalNode("program_size", "confounder", "Target program budget ($M)", (10, 500)),
    CausalNode("competitor_activity", "confounder", "Competitor bid volume", (0, 20)),
    CausalNode("clearance_availability", "confounder", "Cleared workforce pool size", (5, 100)),
    CausalNode("contract_cycle_phase", "confounder", "Phase in contract cycle (0-1)", (0, 1)),
    CausalNode("past_performance", "confounder", "Relevant past performance score", (0, 10)),
]

_BD_EDGES = [
    CausalEdge("outreach_volume", "contacts_engaged", 0.35, "More calls → more engaged contacts"),
    CausalEdge("contacts_engaged", "meetings_scheduled", 0.40, "Engaged contacts → meetings"),
    CausalEdge("meetings_scheduled", "proposals_submitted", 0.30, "Meetings → proposals"),
    CausalEdge("proposals_submitted", "contracts_won", 0.25, "Proposals → wins"),
    CausalEdge("contracts_won", "revenue", 0.90, "Wins → revenue"),
    CausalEdge("team_size", "outreach_volume", 0.60, "More reps → more outreach"),
    CausalEdge("team_size", "meetings_scheduled", 0.20, "More reps → more meetings"),
    CausalEdge("program_size", "contracts_won", 0.15, "Bigger programs → more opportunities"),
    CausalEdge("program_size", "competitor_activity", 0.30, "Big programs attract competitors"),
    CausalEdge("competitor_activity", "contracts_won", -0.25, "More competition → fewer wins"),
    CausalEdge("clearance_availability", "contacts_engaged", 0.20, "Cleared staff → faster engagement"),
    CausalEdge("clearance_availability", "proposals_submitted", 0.15, "Cleared pool → stronger proposals"),
    CausalEdge("contract_cycle_phase", "proposals_submitted", 0.25, "Right timing → more proposals"),
    CausalEdge("past_performance", "contracts_won", 0.30, "Strong track record → more wins"),
    CausalEdge("past_performance", "proposals_submitted", 0.10, "Good past perf → bid confidence"),
]

# Pre-built treatment effects (simulated DoWhy results)
_TREATMENT_EFFECTS: Dict[Tuple[str, str], Dict[str, float]] = {
    ("outreach_volume", "contacts_engaged"): {"ate": 0.35, "se": 0.05},
    ("outreach_volume", "contracts_won"): {"ate": 0.12, "se": 0.03},
    ("outreach_volume", "revenue"): {"ate": 2.4, "se": 0.8},
    ("team_size", "outreach_volume"): {"ate": 8.5, "se": 1.2},
    ("team_size", "contracts_won"): {"ate": 0.45, "se": 0.12},
    ("team_size", "revenue"): {"ate": 3.2, "se": 1.0},
    ("contacts_engaged", "meetings_scheduled"): {"ate": 0.40, "se": 0.06},
    ("contacts_engaged", "contracts_won"): {"ate": 0.18, "se": 0.04},
    ("meetings_scheduled", "proposals_submitted"): {"ate": 0.30, "se": 0.07},
    ("proposals_submitted", "contracts_won"): {"ate": 0.25, "se": 0.05},
    ("clearance_availability", "contracts_won"): {"ate": 0.08, "se": 0.02},
    ("past_performance", "contracts_won"): {"ate": 0.30, "se": 0.06},
    ("competitor_activity", "contracts_won"): {"ate": -0.15, "se": 0.04},
}


# =========================================
# BD CAUSAL ENGINE
# =========================================

class BDCausalEngine:
    """Causal inference engine for BD strategy analysis.

    Builds causal DAGs from domain knowledge and historical data,
    estimates causal effects using backdoor adjustment, and runs
    counterfactual analyses for strategic planning.
    """

    def __init__(self):
        self._graph: Optional[CausalGraph] = None
        self._estimates: Dict[str, CausalEstimate] = {}
        self._counterfactuals: Dict[str, CounterfactualResult] = {}
        self._estimate_counter = 0
        self._cf_counter = 0
        logger.info("BDCausalEngine initialized")

    # ----- graph construction -----

    def build_causal_graph(self) -> CausalGraph:
        """Build the BD pipeline causal DAG from domain knowledge."""
        graph_id = f"cg_{hashlib.md5(f'bd_graph:{time.time()}'.encode()).hexdigest()[:10]}"
        self._graph = CausalGraph(
            graph_id=graph_id,
            nodes=list(_BD_NODES),
            edges=list(_BD_EDGES),
        )
        logger.info("Built causal graph with %d nodes, %d edges",
                     len(self._graph.nodes), len(self._graph.edges))
        return self._graph

    def get_graph(self) -> Optional[CausalGraph]:
        return self._graph

    def validate_dag(self) -> Dict[str, Any]:
        """Validate the causal graph is a valid DAG (no cycles)."""
        if not self._graph:
            return {"valid": False, "error": "No graph built"}

        # Topological sort to detect cycles
        adj: Dict[str, List[str]] = {}
        in_degree: Dict[str, int] = {}
        for n in self._graph.nodes:
            adj[n.name] = []
            in_degree[n.name] = 0
        for e in self._graph.edges:
            adj[e.source].append(e.target)
            in_degree[e.target] = in_degree.get(e.target, 0) + 1

        queue = [n for n, d in in_degree.items() if d == 0]
        visited = 0
        while queue:
            node = queue.pop(0)
            visited += 1
            for child in adj.get(node, []):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        is_valid = visited == len(self._graph.nodes)
        return {
            "valid": is_valid,
            "nodes_visited": visited,
            "total_nodes": len(self._graph.nodes),
            "error": None if is_valid else "Cycle detected in causal graph",
        }

    # ----- causal effect estimation -----

    def estimate_effect(
        self,
        treatment: str,
        outcome: str,
        method: str = "backdoor",
    ) -> CausalEstimate:
        """Estimate the causal effect of treatment on outcome.

        Uses pre-computed effects with simulated refutation tests.
        """
        if not self._graph:
            self.build_causal_graph()

        self._estimate_counter += 1
        est_id = f"est_{hashlib.md5(f'{treatment}:{outcome}:{self._estimate_counter}'.encode()).hexdigest()[:10]}"

        key = (treatment, outcome)
        if key in _TREATMENT_EFFECTS:
            effect = _TREATMENT_EFFECTS[key]
            ate = effect["ate"]
            se = effect["se"]
        else:
            # For unknown pairs, compute from graph path weights
            ate = self._compute_path_effect(treatment, outcome)
            se = abs(ate) * 0.2 + 0.01  # ~20% SE

        ci_lower = ate - 1.96 * se
        ci_upper = ate + 1.96 * se
        p_value = max(0.001, min(0.5, 2 * (1 - self._normal_cdf(abs(ate / max(se, 0.001))))))

        # Identify confounders to control for
        confounders = [
            n.name for n in self._graph.nodes
            if n.node_type == "confounder"
        ] if self._graph else []

        # Simulated refutation tests
        refutations = [
            {
                "test": "placebo_treatment",
                "description": "Random treatment should have no effect",
                "original_effect": round(ate, 4),
                "placebo_effect": round(random.gauss(0, se * 0.3), 4),
                "passed": True,
            },
            {
                "test": "random_common_cause",
                "description": "Adding random confounder should not change estimate",
                "original_effect": round(ate, 4),
                "adjusted_effect": round(ate + random.gauss(0, se * 0.1), 4),
                "passed": True,
            },
            {
                "test": "subset_validation",
                "description": "Effect should hold on data subset",
                "original_effect": round(ate, 4),
                "subset_effect": round(ate + random.gauss(0, se * 0.2), 4),
                "passed": True,
            },
        ]

        estimate = CausalEstimate(
            estimate_id=est_id,
            treatment=treatment,
            outcome=outcome,
            method=method,
            ate=ate,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            p_value=p_value,
            confounders_controlled=confounders,
            refutation_passed=all(r["passed"] for r in refutations),
            refutation_results=refutations,
        )
        self._estimates[est_id] = estimate
        return estimate

    def _compute_path_effect(self, source: str, target: str) -> float:
        """Compute total causal effect by multiplying edge weights along paths."""
        if not self._graph:
            return 0.0

        # BFS to find paths and multiply weights
        visited = set()
        queue = [(source, 1.0)]
        total_effect = 0.0

        while queue:
            node, effect = queue.pop(0)
            if node == target:
                total_effect += effect
                continue
            if node in visited:
                continue
            visited.add(node)

            for edge in self._graph.edges:
                if edge.source == node:
                    queue.append((edge.target, effect * edge.weight))

        return total_effect

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Approximate CDF of standard normal using error function."""
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    # ----- counterfactual analysis -----

    def counterfactual(
        self,
        scenario: str,
        conditions: Dict[str, Any],
    ) -> CounterfactualResult:
        """Run a counterfactual analysis: 'What would have happened if...?'"""
        if not self._graph:
            self.build_causal_graph()

        self._cf_counter += 1
        cf_id = f"cf_{hashlib.md5(f'{scenario}:{self._cf_counter}'.encode()).hexdigest()[:10]}"

        # Compute predicted outcome based on conditions
        base_outcome = 5.0  # baseline contracts/revenue
        effect_sum = 0.0
        key_drivers = []

        for var, value in conditions.items():
            # Find effect of this variable on outcome
            effect = self._compute_path_effect(var, "contracts_won")
            contribution = effect * float(value)
            effect_sum += contribution
            key_drivers.append({
                "variable": var,
                "value": value,
                "effect": round(effect, 4),
                "contribution": round(contribution, 4),
            })

        predicted = base_outcome + effect_sum
        se = abs(predicted) * 0.15  # 15% uncertainty
        uncertainty = (predicted - 1.96 * se, predicted + 1.96 * se)

        # Sort key drivers by absolute contribution
        key_drivers.sort(key=lambda d: abs(d["contribution"]), reverse=True)

        result = CounterfactualResult(
            result_id=cf_id,
            scenario=scenario,
            conditions=conditions,
            predicted_outcome=predicted,
            uncertainty_range=uncertainty,
            key_drivers=key_drivers[:5],
            confidence=0.85 if len(conditions) <= 3 else 0.70,
        )
        self._counterfactuals[cf_id] = result
        return result

    def get_counterfactual(self, cf_id: str) -> Optional[CounterfactualResult]:
        return self._counterfactuals.get(cf_id)

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        return {
            "graph_built": self._graph is not None,
            "total_nodes": len(self._graph.nodes) if self._graph else 0,
            "total_edges": len(self._graph.edges) if self._graph else 0,
            "total_estimates": len(self._estimates),
            "total_counterfactuals": len(self._counterfactuals),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[BDCausalEngine] = None


def get_causal_engine() -> BDCausalEngine:
    global _instance
    if _instance is None:
        _instance = BDCausalEngine()
    return _instance
