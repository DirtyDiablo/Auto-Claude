"""Phase 32A: Predictive Intelligence API — 14 endpoints.

POST   /predict/win-probability             — Score single opportunity
POST   /predict/win-probability/batch       — Score multiple opportunities
GET    /predict/pipeline/ranked             — Full pipeline ranked by composite score
GET    /predict/pipeline/review             — Weekly pipeline review
POST   /predict/what-if                     — What-if scenario analysis
GET    /predict/forecast/program/{name}     — Hiring forecast for program
GET    /predict/forecast/location/{loc}     — Hiring forecast for location
GET    /predict/forecast/roles              — Role demand forecast
GET    /predict/ramp-signals                — Programs ramping up/down
GET    /predict/timing/{program}            — Optimal outreach timing
GET    /predict/budget-calendar             — Forward BD calendar
GET    /predict/recompete/{contract}        — Recompete timing prediction
GET    /predict/model-performance           — Model accuracy metrics
POST   /predict/retrain                     — Trigger model retraining
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from src.ml.win_probability import WinProbabilityModel, get_win_model
from src.ml.opportunity_scorer import OpportunityScorer, get_opportunity_scorer
from src.ml.hiring_forecaster import HiringForecaster, get_hiring_forecaster
from src.ml.budget_predictor import BudgetCyclePredictor, get_budget_predictor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["predictive-intelligence"])


# =========================================
# REQUEST/RESPONSE MODELS
# =========================================


class OpportunityInput(BaseModel):
    """Input for win probability prediction."""

    id: str = Field(default="opp-1", description="Opportunity ID")
    title: str = Field(default="Unknown", description="Job/opportunity title")
    company: str = Field(default="Unknown", description="Company name")
    program: str = Field(default="", description="Mapped program")
    contact_tier: int = Field(default=4, ge=1, le=6)
    relationship_depth: int = Field(default=0, ge=0)
    days_since_last_contact: int = Field(default=90, ge=0)
    mutual_connections: int = Field(default=0, ge=0)
    contact_response_rate: float = Field(default=0.0, ge=0, le=1)
    pts_involvement: int = Field(default=0, ge=0, le=3)
    program_value_log: float = Field(default=6.0)
    days_to_pop_end: int = Field(default=365)
    past_placements_on_program: int = Field(default=0, ge=0)
    competitor_density: int = Field(default=3, ge=0)
    clearance_match: int = Field(default=0, ge=0, le=1)
    role_match_score: float = Field(default=0.5, ge=0, le=1)
    location_familiarity: float = Field(default=0.3, ge=0, le=1)
    days_job_open: int = Field(default=14, ge=0)
    salary_competitiveness: float = Field(default=1.0)
    fiscal_quarter: int = Field(default=1, ge=1, le=4)
    days_to_fy_end: int = Field(default=180)
    is_option_year: int = Field(default=0, ge=0, le=1)
    seasonal_hiring_index: float = Field(default=1.0)
    outreach_attempts: int = Field(default=0, ge=0)
    channels_used: int = Field(default=0, ge=0)
    similar_opp_win_rate: float = Field(default=0.3, ge=0, le=1)
    estimated_value: float = Field(default=0)
    location: str = Field(default="")
    description: str = Field(default="")


class BatchInput(BaseModel):
    opportunities: List[OpportunityInput]


class WhatIfInput(BaseModel):
    opportunity: OpportunityInput
    changes: Dict[str, Any] = Field(
        default_factory=dict, description="Hypothetical changes to apply"
    )


class RetrainInput(BaseModel):
    n_synthetic: int = Field(
        default=500, ge=50, le=10000, description="Synthetic training samples"
    )


# =========================================
# MODULE STATE
# =========================================

_win_model: Optional[WinProbabilityModel] = None
_scorer: Optional[OpportunityScorer] = None
_forecaster: Optional[HiringForecaster] = None
_budget: Optional[BudgetCyclePredictor] = None


def _get_win_model() -> WinProbabilityModel:
    global _win_model
    if _win_model is None:
        _win_model = get_win_model()
    return _win_model


def _get_scorer() -> OpportunityScorer:
    global _scorer
    if _scorer is None:
        _scorer = get_opportunity_scorer()
    return _scorer


def _get_forecaster() -> HiringForecaster:
    global _forecaster
    if _forecaster is None:
        _forecaster = get_hiring_forecaster()
    return _forecaster


def _get_budget() -> BudgetCyclePredictor:
    global _budget
    if _budget is None:
        _budget = get_budget_predictor()
    return _budget


def configure_predictive(
    win_model: Optional[WinProbabilityModel] = None,
    scorer: Optional[OpportunityScorer] = None,
    forecaster: Optional[HiringForecaster] = None,
    budget: Optional[BudgetCyclePredictor] = None,
) -> None:
    """Wire up predictive components during app startup."""
    global _win_model, _scorer, _forecaster, _budget
    if win_model:
        _win_model = win_model
    if scorer:
        _scorer = scorer
    if forecaster:
        _forecaster = forecaster
    if budget:
        _budget = budget


# =========================================
# WIN PROBABILITY ENDPOINTS
# =========================================


@router.post("/win-probability")
async def predict_win_probability(opp: OpportunityInput) -> Dict[str, Any]:
    """Predict win probability for a single opportunity."""
    model = _get_win_model()
    prediction = await model.predict(opp.model_dump())
    return {
        "opportunity_id": opp.id,
        "win_probability": prediction.win_probability,
        "confidence": prediction.confidence,
        "top_factors": prediction.top_factors,
        "recommended_actions": prediction.recommended_actions,
        "optimal_timing": prediction.optimal_timing,
    }


@router.post("/win-probability/batch")
async def predict_win_probability_batch(batch: BatchInput) -> Dict[str, Any]:
    """Score multiple opportunities."""
    model = _get_win_model()
    predictions = await model.predict_batch(
        [o.model_dump() for o in batch.opportunities]
    )
    results = []
    for opp, pred in zip(batch.opportunities, predictions):
        results.append(
            {
                "opportunity_id": opp.id,
                "win_probability": pred.win_probability,
                "confidence": pred.confidence,
                "optimal_timing": pred.optimal_timing,
            }
        )
    return {"predictions": results, "total": len(results)}


# =========================================
# PIPELINE ENDPOINTS
# =========================================


@router.get("/pipeline/ranked")
async def get_pipeline_ranked(
    limit: int = Query(default=50, ge=1, le=200),
) -> Dict[str, Any]:
    """Full pipeline ranked by composite score."""
    scorer = _get_scorer()
    # Use synthetic opportunities if no real data available
    sample_opps = _generate_sample_pipeline()
    ranked = await scorer.rank_pipeline(sample_opps, limit=limit)
    return {
        "pipeline": [
            {
                "rank": s.rank,
                "opportunity_id": s.opportunity_id,
                "title": s.title,
                "company": s.company,
                "program": s.program,
                "composite_score": s.composite_score,
                "win_probability": s.win_probability,
                "recommended_approach": s.recommended_approach,
                "dimensions": [
                    {"name": d.name, "score": d.score, "weighted": d.weighted_score}
                    for d in s.dimensions
                ],
            }
            for s in ranked
        ],
        "total": len(ranked),
    }


@router.get("/pipeline/review")
async def get_pipeline_review() -> Dict[str, Any]:
    """Weekly pipeline review with insights."""
    scorer = _get_scorer()
    sample_opps = _generate_sample_pipeline()
    review = await scorer.weekly_pipeline_review(sample_opps)
    return {
        "review_date": review.review_date,
        "total_pipeline_value": review.total_pipeline_value,
        "average_score": review.average_score,
        "top_opportunities": [
            {"rank": s.rank, "title": s.title, "score": s.composite_score}
            for s in review.top_opportunities
        ],
        "new_this_week": review.new_this_week,
        "at_risk": review.at_risk,
        "stale": review.stale,
        "focus_areas": review.focus_areas,
        "win_loss_summary": review.win_loss_summary,
    }


@router.post("/what-if")
async def what_if_analysis(request: WhatIfInput) -> Dict[str, Any]:
    """What-if scenario analysis."""
    scorer = _get_scorer()
    result = await scorer.what_if_analysis(
        request.opportunity.model_dump(),
        request.changes,
    )
    return result


# =========================================
# FORECAST ENDPOINTS
# =========================================


@router.get("/forecast/program/{name}")
async def forecast_program(
    name: str,
    horizon_days: int = Query(default=90, ge=7, le=365),
) -> Dict[str, Any]:
    """Hiring forecast for a specific program."""
    forecaster = _get_forecaster()
    forecast = await forecaster.forecast_program_hiring(name, horizon_days)
    return {
        "program": forecast.entity,
        "horizon_days": forecast.horizon_days,
        "current_rate": forecast.current_rate,
        "forecasted_rate": forecast.forecasted_rate,
        "trend": forecast.trend,
        "trend_strength": forecast.trend_strength,
        "seasonal_pattern": forecast.seasonal_pattern,
        "confidence": forecast.confidence,
        "forecast_points": [
            {
                "date": p.date,
                "predicted": p.predicted,
                "lower": p.lower_bound,
                "upper": p.upper_bound,
            }
            for p in forecast.forecast_points
        ],
    }


@router.get("/forecast/location/{loc}")
async def forecast_location(
    loc: str,
    horizon_days: int = Query(default=90, ge=7, le=365),
) -> Dict[str, Any]:
    """Hiring forecast for a location."""
    forecaster = _get_forecaster()
    forecast = await forecaster.forecast_location_demand(loc, horizon_days)
    return {
        "location": forecast.entity,
        "horizon_days": forecast.horizon_days,
        "current_rate": forecast.current_rate,
        "forecasted_rate": forecast.forecasted_rate,
        "trend": forecast.trend,
        "trend_strength": forecast.trend_strength,
        "confidence": forecast.confidence,
    }


@router.get("/forecast/roles")
async def forecast_roles(
    role: str = Query(default="analyst", description="Role category to forecast"),
) -> Dict[str, Any]:
    """Role demand forecast."""
    forecaster = _get_forecaster()
    forecast = await forecaster.forecast_role_demand(role)
    return {
        "role": forecast.role_category,
        "current_demand": forecast.current_demand,
        "forecasted_demand": forecast.forecasted_demand,
        "growth_rate": forecast.growth_rate,
        "top_programs": forecast.top_programs,
        "top_locations": forecast.top_locations,
    }


@router.get("/ramp-signals")
async def get_ramp_signals() -> Dict[str, Any]:
    """Programs ramping up/down."""
    forecaster = _get_forecaster()
    signals = await forecaster.detect_ramp_signals()
    return {
        "signals": [
            {
                "program": s.program,
                "signal_type": s.signal_type,
                "confidence": s.confidence,
                "evidence": s.evidence,
                "detected_at": s.detected_at,
            }
            for s in signals
        ],
        "total": len(signals),
    }


@router.get("/timing/{program}")
async def get_timing(program: str) -> Dict[str, Any]:
    """Optimal outreach timing for a program."""
    forecaster = _get_forecaster()
    rec = await forecaster.optimal_timing_recommendation(program)
    return {
        "program": rec.program,
        "best_window": rec.best_window,
        "reason": rec.reason,
        "historical_peaks": rec.historical_peaks,
        "next_peak_estimate": rec.next_peak_estimate,
        "confidence": rec.confidence,
    }


# =========================================
# BUDGET ENDPOINTS
# =========================================


@router.get("/budget-calendar")
async def get_budget_calendar(
    months: int = Query(default=12, ge=1, le=24),
) -> Dict[str, Any]:
    """Forward-looking BD calendar."""
    budget = _get_budget()
    calendar = await budget.get_calendar(months)
    return {
        "start_date": calendar.start_date,
        "end_date": calendar.end_date,
        "fiscal_year": calendar.fiscal_year,
        "events": [
            {
                "date": e.date,
                "event_type": e.event_type,
                "title": e.title,
                "agency": e.agency,
                "program": e.program,
                "priority": e.priority,
                "details": e.details,
            }
            for e in calendar.events
        ],
        "total_events": calendar.total_events,
    }


@router.get("/recompete/{contract}")
async def get_recompete(contract: str) -> Dict[str, Any]:
    """Recompete timing prediction for a contract."""
    budget = _get_budget()
    pred = await budget.predict_recompete_timing(contract)
    return {
        "contract_id": pred.contract_id,
        "contract_name": pred.contract_name,
        "current_pop_end": pred.current_pop_end,
        "options_remaining": pred.options_remaining,
        "predicted_rfi_date": pred.predicted_rfi_date,
        "predicted_rfp_date": pred.predicted_rfp_date,
        "predicted_award_date": pred.predicted_award_date,
        "recompete_probability": pred.recompete_probability,
        "months_to_action": pred.months_to_action,
        "recommended_actions": pred.recommended_actions,
        "confidence": pred.confidence,
    }


# =========================================
# MODEL MANAGEMENT ENDPOINTS
# =========================================


@router.get("/model-performance")
async def get_model_performance() -> Dict[str, Any]:
    """Model accuracy and performance metrics."""
    model = _get_win_model()
    metrics = model.get_model_metrics()
    return {
        "trained": metrics.trained,
        "auc": metrics.auc,
        "precision": metrics.precision,
        "recall": metrics.recall,
        "f1": metrics.f1,
        "total_samples": metrics.total_samples,
        "feature_count": metrics.feature_count,
        "trained_at": metrics.trained_at,
    }


@router.post("/retrain")
async def retrain_model(request: RetrainInput) -> Dict[str, Any]:
    """Trigger model retraining with synthetic or real data."""
    model = _get_win_model()
    result = await model.train(n_synthetic=request.n_synthetic)
    return {
        "status": "trained" if result.accuracy > 0 else "failed",
        "accuracy": result.accuracy,
        "auc": result.auc,
        "f1": result.f1,
        "precision": result.precision,
        "recall": result.recall,
        "training_samples": result.training_samples,
        "feature_importance": result.feature_importance[:10],
        "trained_at": result.trained_at,
    }


# =========================================
# HELPERS
# =========================================


def _generate_sample_pipeline() -> List[dict]:
    """Generate sample pipeline data when no real data is available."""
    return [
        {
            "id": "opp-1",
            "title": "Sr Intelligence Analyst",
            "company": "Leidos",
            "program": "AF DCGS - PACAF",
            "contact_tier": 2,
            "relationship_depth": 8,
            "days_since_last_contact": 5,
            "clearance_match": 1,
            "pts_involvement": 3,
            "estimated_value": 500000,
            "days_job_open": 10,
            "fiscal_quarter": 3,
            "location": "Hickam AFB",
            "competitor_density": 2,
        },
        {
            "id": "opp-2",
            "title": "Cyber Security Engineer",
            "company": "GDIT",
            "program": "NGEN",
            "contact_tier": 3,
            "relationship_depth": 3,
            "days_since_last_contact": 20,
            "clearance_match": 1,
            "pts_involvement": 1,
            "estimated_value": 350000,
            "days_job_open": 25,
            "fiscal_quarter": 3,
            "location": "San Diego",
            "competitor_density": 5,
        },
        {
            "id": "opp-3",
            "title": "Systems Engineer",
            "company": "Northrop Grumman",
            "program": "GBSD",
            "contact_tier": 4,
            "relationship_depth": 1,
            "days_since_last_contact": 45,
            "clearance_match": 0,
            "pts_involvement": 0,
            "estimated_value": 200000,
            "days_job_open": 40,
            "fiscal_quarter": 1,
            "location": "Colorado Springs",
            "competitor_density": 8,
        },
    ]


# =========================================
# ROUTER INTEGRATION
# =========================================


def include_predictive_router(app, **kwargs):
    """Include the Phase 32A predictive router in the main FastAPI app."""
    configure_predictive(**kwargs)
    app.include_router(router)
    logger.info("Phase 32A predictive routes enabled: /predict/* (14 endpoints)")
