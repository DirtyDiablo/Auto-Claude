"""Phase 51A — BD Digital Twin.

A complete simulated copy of the BD pipeline for forward simulation,
scenario comparison, and calibration. Uses Monte Carlo methods for
probabilistic outcome estimation.
"""

from __future__ import annotations

import hashlib
import logging
import math
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

random.seed(42)


# =========================================
# DATA MODELS
# =========================================

@dataclass
class Intervention:
    """A change to apply to the twin before simulation."""
    variable: str
    action: str  # set | increase | decrease | multiply
    value: float
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable": self.variable,
            "action": self.action,
            "value": self.value,
            "description": self.description,
        }


@dataclass
class DigitalTwinState:
    """Snapshot of the BD pipeline state for simulation."""
    twin_id: str
    snapshot_date: str
    # Pipeline state
    total_contacts: int = 150
    active_contacts: int = 80
    tier1_contacts: int = 10
    tier2_contacts: int = 25
    # Program state
    total_programs: int = 8
    active_pursuits: int = 5
    # Team state
    team_size: int = 8
    avg_calls_per_rep: float = 15.0
    meeting_conversion_rate: float = 0.25
    proposal_win_rate: float = 0.20
    # Pipeline value
    pipeline_value_m: float = 45.0  # $M
    weighted_pipeline_m: float = 18.0
    # Market state
    competitor_count: int = 6
    avg_competitor_activity: float = 12.0
    contract_cycle_phase: float = 0.5  # 0=start, 1=end
    # Rates (per quarter)
    clearance_processing_weeks: float = 12.0
    placement_rate: float = 0.15
    churn_rate: float = 0.08

    def to_dict(self) -> Dict[str, Any]:
        return {
            "twin_id": self.twin_id,
            "snapshot_date": self.snapshot_date,
            "total_contacts": self.total_contacts,
            "active_contacts": self.active_contacts,
            "tier1_contacts": self.tier1_contacts,
            "tier2_contacts": self.tier2_contacts,
            "total_programs": self.total_programs,
            "active_pursuits": self.active_pursuits,
            "team_size": self.team_size,
            "avg_calls_per_rep": self.avg_calls_per_rep,
            "meeting_conversion_rate": self.meeting_conversion_rate,
            "proposal_win_rate": self.proposal_win_rate,
            "pipeline_value_m": round(self.pipeline_value_m, 2),
            "weighted_pipeline_m": round(self.weighted_pipeline_m, 2),
            "competitor_count": self.competitor_count,
            "avg_competitor_activity": self.avg_competitor_activity,
            "contract_cycle_phase": self.contract_cycle_phase,
            "clearance_processing_weeks": self.clearance_processing_weeks,
            "placement_rate": round(self.placement_rate, 4),
            "churn_rate": round(self.churn_rate, 4),
        }


@dataclass
class SimulationResult:
    """Result of a digital twin simulation."""
    sim_id: str
    twin_id: str
    days_simulated: int
    monte_carlo_runs: int
    interventions: List[Intervention] = field(default_factory=list)
    # Outcomes
    expected_pipeline_value_m: float = 0.0
    pipeline_ci_lower: float = 0.0
    pipeline_ci_upper: float = 0.0
    expected_placements: float = 0.0
    placements_ci_lower: float = 0.0
    placements_ci_upper: float = 0.0
    expected_revenue_m: float = 0.0
    revenue_ci_lower: float = 0.0
    revenue_ci_upper: float = 0.0
    # Simulation metadata
    convergence_score: float = 0.0  # 0-1, how well MC converged
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sim_id": self.sim_id,
            "twin_id": self.twin_id,
            "days_simulated": self.days_simulated,
            "monte_carlo_runs": self.monte_carlo_runs,
            "interventions": [i.to_dict() for i in self.interventions],
            "expected_pipeline_value_m": round(self.expected_pipeline_value_m, 2),
            "pipeline_ci": [round(self.pipeline_ci_lower, 2), round(self.pipeline_ci_upper, 2)],
            "expected_placements": round(self.expected_placements, 1),
            "placements_ci": [round(self.placements_ci_lower, 1), round(self.placements_ci_upper, 1)],
            "expected_revenue_m": round(self.expected_revenue_m, 2),
            "revenue_ci": [round(self.revenue_ci_lower, 2), round(self.revenue_ci_upper, 2)],
            "convergence_score": round(self.convergence_score, 3),
            "created_at": self.created_at,
        }


@dataclass
class ScenarioComparison:
    """Side-by-side comparison of multiple simulation scenarios."""
    comparison_id: str
    scenarios: List[Dict[str, Any]] = field(default_factory=list)
    winner: Optional[str] = None
    winner_reason: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "scenarios": self.scenarios,
            "total_scenarios": len(self.scenarios),
            "winner": self.winner,
            "winner_reason": self.winner_reason,
            "created_at": self.created_at,
        }


@dataclass
class CalibrationReport:
    """Report comparing twin predictions against actuals."""
    report_id: str
    twin_id: str
    metric_errors: Dict[str, float] = field(default_factory=dict)
    overall_accuracy: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "twin_id": self.twin_id,
            "metric_errors": {k: round(v, 4) for k, v in self.metric_errors.items()},
            "overall_accuracy": round(self.overall_accuracy, 3),
            "recommendations": self.recommendations,
            "created_at": self.created_at,
        }


# =========================================
# BD DIGITAL TWIN
# =========================================

class BDDigitalTwin:
    """A complete simulated copy of the BD pipeline.

    Creates snapshots from current data, runs Monte Carlo forward simulations
    with optional interventions, and compares scenarios side-by-side.
    """

    def __init__(self):
        self._twins: Dict[str, DigitalTwinState] = {}
        self._simulations: Dict[str, SimulationResult] = {}
        self._comparisons: Dict[str, ScenarioComparison] = {}
        self._calibrations: Dict[str, CalibrationReport] = {}
        self._twin_counter = 0
        self._sim_counter = 0
        logger.info("BDDigitalTwin initialized")

    # ----- twin creation -----

    def create_twin(self, snapshot_date: Optional[str] = None) -> DigitalTwinState:
        """Create a digital twin from current state."""
        self._twin_counter += 1
        twin_id = f"twin_{hashlib.md5(f'twin:{self._twin_counter}:{time.time()}'.encode()).hexdigest()[:10]}"

        twin = DigitalTwinState(
            twin_id=twin_id,
            snapshot_date=snapshot_date or datetime.utcnow().isoformat(),
        )
        self._twins[twin_id] = twin
        logger.info("Created digital twin %s", twin_id)
        return twin

    def get_twin(self, twin_id: str) -> Optional[DigitalTwinState]:
        return self._twins.get(twin_id)

    def list_twins(self) -> List[DigitalTwinState]:
        return list(self._twins.values())

    # ----- simulation -----

    def simulate(
        self,
        twin_id: str,
        days: int = 90,
        interventions: Optional[List[Intervention]] = None,
        monte_carlo_runs: int = 1000,
    ) -> SimulationResult:
        """Run Monte Carlo simulation forward from twin state."""
        twin = self._twins.get(twin_id)
        if not twin:
            raise ValueError(f"Twin not found: {twin_id}")

        self._sim_counter += 1
        sim_id = f"sim_{hashlib.md5(f'sim:{self._sim_counter}:{time.time()}'.encode()).hexdigest()[:10]}"

        # Apply interventions to copy of state
        state = self._apply_interventions(twin, interventions or [])

        # Monte Carlo simulation
        pipeline_samples = []
        placement_samples = []
        revenue_samples = []

        for _ in range(monte_carlo_runs):
            p_val, placements, revenue = self._simulate_one_run(state, days)
            pipeline_samples.append(p_val)
            placement_samples.append(placements)
            revenue_samples.append(revenue)

        result = SimulationResult(
            sim_id=sim_id,
            twin_id=twin_id,
            days_simulated=days,
            monte_carlo_runs=monte_carlo_runs,
            interventions=interventions or [],
            expected_pipeline_value_m=self._mean(pipeline_samples),
            pipeline_ci_lower=self._percentile(pipeline_samples, 2.5),
            pipeline_ci_upper=self._percentile(pipeline_samples, 97.5),
            expected_placements=self._mean(placement_samples),
            placements_ci_lower=self._percentile(placement_samples, 2.5),
            placements_ci_upper=self._percentile(placement_samples, 97.5),
            expected_revenue_m=self._mean(revenue_samples),
            revenue_ci_lower=self._percentile(revenue_samples, 2.5),
            revenue_ci_upper=self._percentile(revenue_samples, 97.5),
            convergence_score=self._convergence(pipeline_samples),
        )
        self._simulations[sim_id] = result
        return result

    def _apply_interventions(
        self, twin: DigitalTwinState, interventions: List[Intervention],
    ) -> Dict[str, float]:
        """Apply interventions to a copy of the twin state."""
        state = {
            "team_size": float(twin.team_size),
            "avg_calls_per_rep": twin.avg_calls_per_rep,
            "meeting_conversion_rate": twin.meeting_conversion_rate,
            "proposal_win_rate": twin.proposal_win_rate,
            "pipeline_value_m": twin.pipeline_value_m,
            "active_contacts": float(twin.active_contacts),
            "competitor_count": float(twin.competitor_count),
            "clearance_processing_weeks": twin.clearance_processing_weeks,
            "placement_rate": twin.placement_rate,
            "churn_rate": twin.churn_rate,
        }

        for intv in interventions:
            if intv.variable not in state:
                continue
            if intv.action == "set":
                state[intv.variable] = intv.value
            elif intv.action == "increase":
                state[intv.variable] += intv.value
            elif intv.action == "decrease":
                state[intv.variable] -= intv.value
            elif intv.action == "multiply":
                state[intv.variable] *= intv.value

        return state

    def _simulate_one_run(self, state: Dict[str, float], days: int) -> Tuple[float, float, float]:
        """Simulate one Monte Carlo run of the pipeline."""
        team = state["team_size"]
        calls_per_rep = state["avg_calls_per_rep"]
        meeting_conv = state["meeting_conversion_rate"]
        win_rate = state["proposal_win_rate"]
        pipeline = state["pipeline_value_m"]
        placement = state["placement_rate"]
        churn = state["churn_rate"]

        weeks = days / 7.0
        # Weekly outreach
        total_calls = team * calls_per_rep * weeks * random.gauss(1.0, 0.15)
        # Contacts engaged (~40% of calls)
        contacts = total_calls * 0.4 * random.gauss(1.0, 0.10)
        # Meetings from contacts
        meetings = contacts * meeting_conv * random.gauss(1.0, 0.20)
        # Proposals from meetings (~60%)
        proposals = meetings * 0.6 * random.gauss(1.0, 0.15)
        # Wins
        wins = proposals * win_rate * random.gauss(1.0, 0.25)

        # Pipeline change
        new_pipeline = pipeline * (1 + random.gauss(0.05, 0.10))
        new_pipeline += wins * 2.5  # avg $2.5M per win

        # Placements
        placements = wins * placement * random.gauss(1.0, 0.20)
        placements -= pipeline * churn * random.gauss(1.0, 0.15) * (days / 365)

        # Revenue
        revenue = max(0, wins * random.gauss(2.5, 0.8))

        return (
            max(0, new_pipeline),
            max(0, placements),
            max(0, revenue),
        )

    # ----- scenario comparison -----

    def compare_scenarios(
        self,
        twin_id: str,
        scenarios: List[Dict[str, Any]],
        days: int = 90,
        monte_carlo_runs: int = 500,
    ) -> ScenarioComparison:
        """Run multiple scenarios side-by-side and compare."""
        comp_id = f"comp_{hashlib.md5(f'comp:{len(scenarios)}:{time.time()}'.encode()).hexdigest()[:10]}"

        results = []
        for scenario in scenarios:
            name = scenario.get("name", "unnamed")
            raw_interventions = scenario.get("interventions", [])
            interventions = [
                Intervention(
                    variable=i["variable"],
                    action=i.get("action", "set"),
                    value=i.get("value", 0),
                    description=i.get("description", ""),
                )
                for i in raw_interventions
            ]
            sim = self.simulate(twin_id, days, interventions, monte_carlo_runs)
            results.append({
                "name": name,
                "sim_id": sim.sim_id,
                "expected_pipeline_m": round(sim.expected_pipeline_value_m, 2),
                "expected_placements": round(sim.expected_placements, 1),
                "expected_revenue_m": round(sim.expected_revenue_m, 2),
                "pipeline_ci": [round(sim.pipeline_ci_lower, 2), round(sim.pipeline_ci_upper, 2)],
                "interventions": [i.to_dict() for i in interventions],
            })

        # Determine winner by expected revenue
        if results:
            best = max(results, key=lambda r: r["expected_revenue_m"])
            winner = best["name"]
            reason = f"Highest expected revenue: ${best['expected_revenue_m']}M"
        else:
            winner = None
            reason = ""

        comparison = ScenarioComparison(
            comparison_id=comp_id,
            scenarios=results,
            winner=winner,
            winner_reason=reason,
        )
        self._comparisons[comp_id] = comparison
        return comparison

    # ----- calibration -----

    def calibrate(self, twin_id: str) -> CalibrationReport:
        """Calibrate twin against simulated 'actuals'."""
        twin = self._twins.get(twin_id)
        if not twin:
            raise ValueError(f"Twin not found: {twin_id}")

        report_id = f"cal_{hashlib.md5(f'cal:{twin_id}:{time.time()}'.encode()).hexdigest()[:10]}"

        # Simulated actuals vs twin predictions
        errors = {
            "pipeline_value": random.gauss(0.05, 0.03),
            "placement_rate": random.gauss(0.02, 0.01),
            "meeting_conversion": random.gauss(-0.03, 0.02),
            "proposal_win_rate": random.gauss(0.01, 0.02),
        }

        overall_accuracy = 1.0 - sum(abs(v) for v in errors.values()) / len(errors)

        recommendations = []
        if abs(errors["pipeline_value"]) > 0.05:
            recommendations.append("Adjust pipeline growth rate parameter")
        if abs(errors["placement_rate"]) > 0.03:
            recommendations.append("Recalibrate placement probability model")
        if abs(errors["meeting_conversion"]) > 0.04:
            recommendations.append("Update meeting conversion assumptions")
        if not recommendations:
            recommendations.append("Model calibration within acceptable bounds")

        report = CalibrationReport(
            report_id=report_id,
            twin_id=twin_id,
            metric_errors=errors,
            overall_accuracy=max(0, min(1, overall_accuracy)),
            recommendations=recommendations,
        )
        self._calibrations[report_id] = report
        return report

    def get_latest_calibration(self, twin_id: str) -> Optional[CalibrationReport]:
        for cal in reversed(list(self._calibrations.values())):
            if cal.twin_id == twin_id:
                return cal
        return None

    # ----- helpers -----

    @staticmethod
    def _mean(samples: List[float]) -> float:
        return sum(samples) / max(len(samples), 1)

    @staticmethod
    def _percentile(samples: List[float], pct: float) -> float:
        if not samples:
            return 0.0
        sorted_s = sorted(samples)
        idx = int(len(sorted_s) * pct / 100.0)
        idx = min(idx, len(sorted_s) - 1)
        return sorted_s[idx]

    @staticmethod
    def _convergence(samples: List[float]) -> float:
        """Estimate MC convergence via coefficient of variation."""
        if len(samples) < 10:
            return 0.0
        mean = sum(samples) / len(samples)
        if mean == 0:
            return 1.0
        var = sum((x - mean) ** 2 for x in samples) / len(samples)
        cv = math.sqrt(var) / abs(mean)
        return max(0, min(1, 1.0 - cv))

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_twins": len(self._twins),
            "total_simulations": len(self._simulations),
            "total_comparisons": len(self._comparisons),
            "total_calibrations": len(self._calibrations),
        }

    def get_simulation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        sims = sorted(self._simulations.values(), key=lambda s: s.created_at, reverse=True)
        return [s.to_dict() for s in sims[:limit]]


# =========================================
# SINGLETON
# =========================================

_instance: Optional[BDDigitalTwin] = None


def get_digital_twin() -> BDDigitalTwin:
    global _instance
    if _instance is None:
        _instance = BDDigitalTwin()
    return _instance
