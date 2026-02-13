"""Phase 29A — Optimizer API Router (10 endpoints)"""
import structlog
from fastapi import APIRouter, HTTPException, Query
logger = structlog.get_logger(__name__)

router = APIRouter(tags=["optimizer"])

# Lazy getters
def _get_assessment():
    try:
        from Engine8_Knowledge.optimization.self_assessment import get_self_assessment
        return get_self_assessment()
    except Exception:
        return None

def _get_optimizer():
    try:
        from Engine8_Knowledge.optimization.auto_optimizer import get_auto_optimizer
        return get_auto_optimizer()
    except Exception:
        return None

def _get_detector():
    try:
        from Engine8_Knowledge.optimization.regression_detector import get_regression_detector
        return get_regression_detector()
    except Exception:
        return None

def _get_retrain():
    try:
        from Engine8_Knowledge.optimization.retrain_orchestrator import get_retrain_orchestrator
        return get_retrain_orchestrator()
    except Exception:
        return None

@router.post("/optimizer/assess")
async def run_assessment():
    sa = _get_assessment()
    if not sa:
        raise HTTPException(503, "Assessment engine not available")
    from dataclasses import asdict
    report = await sa.run_full_assessment()
    return asdict(report)

@router.get("/optimizer/assessments")
async def assessment_history(weeks: int = Query(12)):
    sa = _get_assessment()
    if not sa:
        return {"assessments": [], "total": 0}
    from dataclasses import asdict
    reports = await sa.get_assessment_history(weeks)
    return {"assessments": [asdict(r) for r in reports], "total": len(reports)}

@router.get("/optimizer/trends/{metric}")
async def metric_trend(metric: str, weeks: int = Query(12)):
    sa = _get_assessment()
    if not sa:
        raise HTTPException(503, "Assessment engine not available")
    from dataclasses import asdict
    trend = await sa.get_trend(metric, weeks)
    return asdict(trend)

@router.get("/optimizer/recommendations")
async def get_recommendations():
    optimizer = _get_optimizer()
    if not optimizer:
        return {"recommendations": []}
    from dataclasses import asdict
    pending = [o for o in optimizer._optimizations if o.status == "pending"]
    return {"recommendations": [asdict(o) for o in pending], "total": len(pending)}

@router.post("/optimizer/apply/{opt_id}")
async def apply_optimization(opt_id: str):
    optimizer = _get_optimizer()
    if not optimizer:
        raise HTTPException(503, "Optimizer not available")
    opt = optimizer.get_optimization(opt_id)
    if not opt:
        raise HTTPException(404, f"Optimization not found: {opt_id}")
    from dataclasses import asdict
    result = await optimizer.auto_apply(opt)
    return asdict(result)

@router.post("/optimizer/approve/{opt_id}")
async def approve_optimization(opt_id: str):
    optimizer = _get_optimizer()
    if not optimizer:
        raise HTTPException(503, "Optimizer not available")
    from dataclasses import asdict
    result = await optimizer.approve(opt_id)
    return asdict(result)

@router.post("/optimizer/rollback/{opt_id}")
async def rollback_optimization(opt_id: str):
    optimizer = _get_optimizer()
    if not optimizer:
        raise HTTPException(503, "Optimizer not available")
    success = await optimizer.rollback(opt_id)
    if not success:
        raise HTTPException(404, f"Optimization not found or cannot rollback: {opt_id}")
    return {"rolled_back": True, "opt_id": opt_id}

@router.get("/optimizer/regressions")
async def get_regressions():
    detector = _get_detector()
    if not detector:
        return {"regressions": []}
    from dataclasses import asdict
    active = await detector.get_active_regressions()
    return {"regressions": [asdict(r) for r in active], "total": len(active)}

@router.post("/optimizer/retrain/{model}")
async def retrain_model(model: str):
    retrain = _get_retrain()
    if not retrain:
        raise HTTPException(503, "Retrain orchestrator not available")
    from dataclasses import asdict
    result = await retrain.orchestrate_retrain(model)
    return asdict(result)

@router.get("/optimizer/retrain/status")
async def retrain_status():
    retrain = _get_retrain()
    if not retrain:
        return {"models": []}
    from dataclasses import asdict
    drift_reports = await retrain.check_all_models()
    return {"models": [asdict(r) for r in drift_reports], "total": len(drift_reports)}
