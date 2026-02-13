"""Phase 55A — Experimentation API.

12 endpoints for feature flags, A/B testing, experiment analytics,
and gradual rollouts.
"""

from __future__ import annotations

from fastapi import FastAPI, APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter()


# =========================================
# REQUEST MODELS
# =========================================

class CreateFlagRequest(BaseModel):
    name: str
    flag_type: str = "boolean"
    description: str = ""
    tags: List[str] = []


class UpdateFlagRequest(BaseModel):
    enabled: Optional[bool] = None
    percentage: Optional[float] = None
    description: Optional[str] = None


class CreateExperimentRequest(BaseModel):
    name: str
    hypothesis: str = ""
    metric_name: str = "conversion_rate"
    variants: List[Dict[str, Any]] = [
        {"name": "control", "weight": 50},
        {"name": "treatment", "weight": 50},
    ]


class AssignUserRequest(BaseModel):
    experiment_id: str
    user_id: str


class RecordConversionRequest(BaseModel):
    experiment_id: str
    variant_id: str
    value: float = 1.0


class TrackEventRequest(BaseModel):
    experiment_id: str
    variant_id: str
    user_id: str
    event_type: str = "view"
    value: float = 0.0


class SampleSizeRequest(BaseModel):
    baseline_rate: float = 0.10
    min_detectable_effect: float = 0.02
    significance: float = 0.05
    power: float = 0.8


# =========================================
# FEATURE FLAG ENDPOINTS
# =========================================

@router.get("/api/experimentation/flags")
def list_flags(status: Optional[str] = Query(None), tag: Optional[str] = Query(None)):
    """List all feature flags."""
    from src.experimentation.feature_flags import get_flag_engine, FlagStatus
    engine = get_flag_engine()
    st = FlagStatus(status) if status else None
    flags = engine.list_flags(status=st, tag=tag)
    return {"flags": [f.to_dict() for f in flags], "total": len(flags)}


@router.get("/api/experimentation/flags/{flag_id}")
def get_flag(flag_id: str):
    """Get a specific feature flag."""
    from src.experimentation.feature_flags import get_flag_engine
    engine = get_flag_engine()
    flag = engine.get_flag(flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    return flag.to_dict()


@router.get("/api/experimentation/flags/{flag_id}/evaluate")
def evaluate_flag(flag_id: str, user_id: Optional[str] = Query(None)):
    """Evaluate if a flag is enabled for a user."""
    from src.experimentation.feature_flags import get_flag_engine
    engine = get_flag_engine()
    flag = engine.get_flag(flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    enabled = engine.is_enabled(flag_id, user_id=user_id)
    return {"flag_id": flag_id, "enabled": enabled, "user_id": user_id}


@router.patch("/api/experimentation/flags/{flag_id}")
def update_flag(flag_id: str, req: UpdateFlagRequest):
    """Update a feature flag."""
    from src.experimentation.feature_flags import get_flag_engine
    engine = get_flag_engine()
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    flag = engine.update_flag(flag_id, **updates)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    return flag.to_dict()


# =========================================
# A/B TESTING ENDPOINTS
# =========================================

@router.post("/api/experimentation/experiments")
def create_experiment(req: CreateExperimentRequest):
    """Create a new A/B test experiment."""
    from src.experimentation.ab_testing import get_ab_framework
    ab = get_ab_framework()
    exp = ab.create_experiment(
        name=req.name,
        hypothesis=req.hypothesis,
        metric_name=req.metric_name,
        variants=req.variants,
    )
    return exp.to_dict()


@router.get("/api/experimentation/experiments")
def list_experiments(status: Optional[str] = Query(None)):
    """List experiments."""
    from src.experimentation.ab_testing import get_ab_framework, ExperimentStatus
    ab = get_ab_framework()
    st = ExperimentStatus(status) if status else None
    experiments = ab.list_experiments(status=st)
    return {"experiments": [e.to_dict() for e in experiments], "total": len(experiments)}


@router.get("/api/experimentation/experiments/{experiment_id}/results")
def get_results(experiment_id: str):
    """Get experiment results with statistical analysis."""
    from src.experimentation.ab_testing import get_ab_framework
    ab = get_ab_framework()
    exp = ab.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return ab.get_results(experiment_id)


@router.post("/api/experimentation/experiments/{experiment_id}/assign")
def assign_user(experiment_id: str, req: AssignUserRequest):
    """Assign a user to an experiment variant."""
    from src.experimentation.ab_testing import get_ab_framework
    ab = get_ab_framework()
    exp = ab.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    variant_id = ab.assign_user(experiment_id, req.user_id)
    return {"experiment_id": experiment_id, "user_id": req.user_id, "variant_id": variant_id}


# =========================================
# ANALYTICS ENDPOINTS
# =========================================

@router.post("/api/experimentation/analytics/track")
def track_event(req: TrackEventRequest):
    """Track an analytics event."""
    from src.experimentation.experiment_analytics import get_experiment_analytics
    analytics = get_experiment_analytics()
    event = analytics.track_event(
        experiment_id=req.experiment_id,
        variant_id=req.variant_id,
        user_id=req.user_id,
        event_type=req.event_type,
        value=req.value,
    )
    return event.to_dict()


@router.get("/api/experimentation/analytics/{experiment_id}/funnel")
def get_funnel(experiment_id: str):
    """Get conversion funnel for an experiment."""
    from src.experimentation.experiment_analytics import get_experiment_analytics
    analytics = get_experiment_analytics()
    funnel = analytics.get_funnel(experiment_id)
    return {"experiment_id": experiment_id, "funnel": [s.to_dict() for s in funnel]}


@router.post("/api/experimentation/analytics/sample-size")
def compute_sample_size(req: SampleSizeRequest):
    """Compute required sample size for an experiment."""
    from src.experimentation.experiment_analytics import get_experiment_analytics
    analytics = get_experiment_analytics()
    n = analytics.compute_sample_size_needed(
        baseline_rate=req.baseline_rate,
        min_detectable_effect=req.min_detectable_effect,
        significance=req.significance,
        power=req.power,
    )
    return {"sample_size_per_variant": n, **req.model_dump()}


# =========================================
# HEALTH
# =========================================

@router.get("/api/experimentation/health")
def experimentation_health():
    """Experimentation subsystem health check."""
    from src.experimentation.feature_flags import get_flag_engine
    from src.experimentation.ab_testing import get_ab_framework
    from src.experimentation.experiment_analytics import get_experiment_analytics

    return {
        "status": "healthy",
        "flags": get_flag_engine().get_stats(),
        "ab_testing": get_ab_framework().get_stats(),
        "analytics": get_experiment_analytics().get_stats(),
    }


# =========================================
# ROUTER REGISTRATION
# =========================================

def include_experimentation_router(app: FastAPI) -> None:
    app.include_router(router)
