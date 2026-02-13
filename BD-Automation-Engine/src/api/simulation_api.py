"""Phase 51A — Simulation & Causal Intelligence API (14 endpoints).

REST endpoints for causal inference, digital twin simulation,
scenario analysis, and sensitivity testing.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from src.simulation.causal_engine import (
    get_causal_engine,
)
from src.simulation.digital_twin import (
    get_digital_twin, Intervention,
)
from src.simulation.scenario_api import (
    get_scenario_api,
)

logger = logging.getLogger(__name__)


# =========================================
# REQUEST MODELS
# =========================================

class EstimateEffectRequest(BaseModel):
    treatment: str
    outcome: str
    method: str = "backdoor"


class CounterfactualRequest(BaseModel):
    scenario: str
    conditions: Dict[str, Any]


class CreateTwinRequest(BaseModel):
    snapshot_date: Optional[str] = None


class SimulateRequest(BaseModel):
    twin_id: str
    days: int = 90
    interventions: Optional[List[Dict[str, Any]]] = None
    monte_carlo_runs: int = 500


class CompareRequest(BaseModel):
    twin_id: str
    scenarios: List[Dict[str, Any]]
    days: int = 90
    monte_carlo_runs: int = 500


class CalibrateRequest(BaseModel):
    twin_id: str


class AnalyzeScenarioRequest(BaseModel):
    question: str


class SensitivityRequest(BaseModel):
    variable: str
    range_pct: float = 30.0


# =========================================
# ROUTE SETUP
# =========================================

def include_simulation_router(app: FastAPI) -> None:
    """Register all simulation & causal intelligence endpoints."""

    causal = get_causal_engine()
    twin = get_digital_twin()
    scenario = get_scenario_api()

    # --------------------------------------------------
    # 1. POST /api/causal/graph — Build causal graph
    # --------------------------------------------------
    @app.post("/api/causal/graph")
    async def build_graph():
        """Build causal graph from domain knowledge."""
        graph = causal.build_causal_graph()
        return graph.to_dict()

    # --------------------------------------------------
    # 2. GET /api/causal/graph — Visualize current graph
    # --------------------------------------------------
    @app.get("/api/causal/graph")
    async def get_graph():
        """Get the current causal graph."""
        graph = causal.get_graph()
        if not graph:
            # Auto-build
            graph = causal.build_causal_graph()
        return graph.to_dict()

    # --------------------------------------------------
    # 3. POST /api/causal/effect — Estimate causal effect
    # --------------------------------------------------
    @app.post("/api/causal/effect")
    async def estimate_effect(req: EstimateEffectRequest):
        """Estimate causal effect of treatment on outcome."""
        estimate = causal.estimate_effect(
            treatment=req.treatment,
            outcome=req.outcome,
            method=req.method,
        )
        return estimate.to_dict()

    # --------------------------------------------------
    # 4. POST /api/causal/counterfactual — Counterfactual analysis
    # --------------------------------------------------
    @app.post("/api/causal/counterfactual")
    async def counterfactual(req: CounterfactualRequest):
        """Run counterfactual: What would have happened if...?"""
        result = causal.counterfactual(req.scenario, req.conditions)
        return result.to_dict()

    # --------------------------------------------------
    # 5. POST /api/twin/create — Create digital twin
    # --------------------------------------------------
    @app.post("/api/twin/create")
    async def create_twin(req: CreateTwinRequest):
        """Create a digital twin from current pipeline state."""
        t = twin.create_twin(req.snapshot_date)
        return t.to_dict()

    # --------------------------------------------------
    # 6. POST /api/twin/simulate — Run simulation
    # --------------------------------------------------
    @app.post("/api/twin/simulate")
    async def simulate(req: SimulateRequest):
        """Run Monte Carlo simulation with optional interventions."""
        interventions = None
        if req.interventions:
            interventions = [
                Intervention(
                    variable=i.get("variable", ""),
                    action=i.get("action", "set"),
                    value=i.get("value", 0),
                    description=i.get("description", ""),
                )
                for i in req.interventions
            ]
        try:
            result = twin.simulate(
                twin_id=req.twin_id,
                days=req.days,
                interventions=interventions,
                monte_carlo_runs=req.monte_carlo_runs,
            )
            return result.to_dict()
        except ValueError as e:
            raise HTTPException(404, str(e))

    # --------------------------------------------------
    # 7. POST /api/twin/compare — Compare scenarios
    # --------------------------------------------------
    @app.post("/api/twin/compare")
    async def compare(req: CompareRequest):
        """Compare multiple simulation scenarios side-by-side."""
        try:
            result = twin.compare_scenarios(
                twin_id=req.twin_id,
                scenarios=req.scenarios,
                days=req.days,
                monte_carlo_runs=req.monte_carlo_runs,
            )
            return result.to_dict()
        except ValueError as e:
            raise HTTPException(404, str(e))

    # --------------------------------------------------
    # 8. GET /api/twin/calibration — Latest calibration report
    # --------------------------------------------------
    @app.get("/api/twin/calibration")
    async def get_calibration(
        twin_id: str = Query(..., description="Twin ID to get calibration for"),
    ):
        """Get the latest calibration report for a twin."""
        report = twin.get_latest_calibration(twin_id)
        if not report:
            raise HTTPException(404, f"No calibration for twin: {twin_id}")
        return report.to_dict()

    # --------------------------------------------------
    # 9. POST /api/twin/calibrate — Recalibrate twin
    # --------------------------------------------------
    @app.post("/api/twin/calibrate")
    async def calibrate(req: CalibrateRequest):
        """Recalibrate twin against actuals."""
        try:
            report = twin.calibrate(req.twin_id)
            return report.to_dict()
        except ValueError as e:
            raise HTTPException(404, str(e))

    # --------------------------------------------------
    # 10. POST /api/scenario/analyze — NL scenario analysis
    # --------------------------------------------------
    @app.post("/api/scenario/analyze")
    async def analyze(req: AnalyzeScenarioRequest):
        """Analyze a strategic scenario from natural language."""
        result = scenario.analyze_scenario(req.question)
        return result.to_dict()

    # --------------------------------------------------
    # 11. POST /api/scenario/sensitivity — Sensitivity analysis
    # --------------------------------------------------
    @app.post("/api/scenario/sensitivity")
    async def sensitivity(req: SensitivityRequest):
        """Run sensitivity analysis for a variable."""
        result = scenario.sensitivity_analysis(req.variable, req.range_pct)
        return result.to_dict()

    # --------------------------------------------------
    # 12. GET /api/scenario/presets — Pre-built scenario templates
    # --------------------------------------------------
    @app.get("/api/scenario/presets")
    async def presets(
        category: str = Query("", description="Filter by category"),
    ):
        """Get pre-built scenario templates."""
        p = scenario.get_presets(category=category or None)
        return {
            "presets": [pr.to_dict() for pr in p],
            "total": len(p),
        }

    # --------------------------------------------------
    # 13. GET /api/simulation/history — Simulation history
    # --------------------------------------------------
    @app.get("/api/simulation/history")
    async def sim_history(
        limit: int = Query(50, description="Max items"),
    ):
        """Past simulation runs and results."""
        history = twin.get_simulation_history(limit)
        return {
            "simulations": history,
            "total": len(history),
        }

    # --------------------------------------------------
    # 14. GET /api/simulation/health — Engine health
    # --------------------------------------------------
    @app.get("/api/simulation/health")
    async def sim_health():
        """Simulation engine health and stats."""
        return {
            "status": "healthy",
            "causal": causal.get_stats(),
            "twin": twin.get_stats(),
            "scenario": scenario.get_stats(),
        }

    logger.info("Simulation & Causal Intelligence API: 14 endpoints registered")
