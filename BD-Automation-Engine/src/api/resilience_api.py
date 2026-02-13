"""Phase 54A — Resilience API.

12 endpoints for circuit breakers, chaos experiments, bulkheads,
and graceful degradation.
"""

from __future__ import annotations

from fastapi import FastAPI, APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


# =========================================
# REQUEST MODELS
# =========================================

class RegisterBreakerRequest(BaseModel):
    name: str
    failure_threshold: int = 5
    recovery_timeout_sec: float = 30.0


class CreateExperimentRequest(BaseModel):
    name: str
    fault_type: str = "latency"
    target_service: str = "qdrant_search"
    duration_sec: float = 60.0
    intensity: float = 0.5


class RegisterBulkheadRequest(BaseModel):
    name: str
    bulkhead_type: str = "semaphore"
    max_concurrent: int = 10
    max_queue: int = 5


class SetDegradationRequest(BaseModel):
    level: str = "normal"


# =========================================
# CIRCUIT BREAKER ENDPOINTS
# =========================================

@router.get("/api/resilience/breakers")
def list_breakers():
    """List all circuit breakers."""
    from src.resilience.circuit_breaker import get_circuit_registry
    registry = get_circuit_registry()
    breakers = registry.list_breakers()
    return {"breakers": [b.to_dict() for b in breakers], "total": len(breakers)}


@router.get("/api/resilience/breakers/{name}")
def get_breaker(name: str):
    """Get a specific circuit breaker."""
    from src.resilience.circuit_breaker import get_circuit_registry
    registry = get_circuit_registry()
    breaker = registry.get_breaker(name)
    if not breaker:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")
    return breaker.to_dict()


@router.post("/api/resilience/breakers/{name}/trip")
def trip_breaker(name: str):
    """Force trip a circuit breaker to OPEN."""
    from src.resilience.circuit_breaker import get_circuit_registry
    registry = get_circuit_registry()
    success = registry.trip(name)
    if not success:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")
    return {"tripped": True, "name": name}


@router.post("/api/resilience/breakers/{name}/reset")
def reset_breaker(name: str):
    """Reset a circuit breaker to CLOSED."""
    from src.resilience.circuit_breaker import get_circuit_registry
    registry = get_circuit_registry()
    success = registry.reset(name)
    if not success:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")
    return {"reset": True, "name": name}


# =========================================
# CHAOS EXPERIMENT ENDPOINTS
# =========================================

@router.post("/api/resilience/chaos/experiments")
def create_experiment(req: CreateExperimentRequest):
    """Create a chaos experiment."""
    from src.resilience.chaos_engine import get_chaos_engine, FaultType
    engine = get_chaos_engine()
    ft_map = {ft.value: ft for ft in FaultType}
    fault_type = ft_map.get(req.fault_type, FaultType.LATENCY)
    exp = engine.create_experiment(
        name=req.name,
        fault_type=fault_type,
        target_service=req.target_service,
        duration_sec=req.duration_sec,
        intensity=req.intensity,
    )
    return exp.to_dict()


@router.get("/api/resilience/chaos/experiments")
def list_experiments(status: Optional[str] = Query(None), limit: int = Query(50)):
    """List chaos experiments."""
    from src.resilience.chaos_engine import get_chaos_engine, ExperimentStatus
    engine = get_chaos_engine()
    st = ExperimentStatus(status) if status else None
    experiments = engine.list_experiments(status=st, limit=limit)
    return {"experiments": [e.to_dict() for e in experiments], "total": len(experiments)}


@router.post("/api/resilience/chaos/experiments/{experiment_id}/run")
def run_experiment(experiment_id: str):
    """Run a chaos experiment."""
    from src.resilience.chaos_engine import get_chaos_engine
    engine = get_chaos_engine()
    exp = engine.run_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp.to_dict()


@router.get("/api/resilience/chaos/templates")
def list_templates():
    """List pre-built experiment templates."""
    from src.resilience.chaos_engine import get_chaos_engine
    engine = get_chaos_engine()
    templates = engine.list_templates()
    return {"templates": templates, "total": len(templates)}


# =========================================
# BULKHEAD ENDPOINTS
# =========================================

@router.get("/api/resilience/bulkheads")
def list_bulkheads():
    """List all bulkheads."""
    from src.resilience.bulkhead import get_bulkhead_manager
    mgr = get_bulkhead_manager()
    bulkheads = mgr.list_bulkheads()
    return {"bulkheads": [b.to_dict() for b in bulkheads], "total": len(bulkheads)}


@router.get("/api/resilience/degradation")
def get_degradation():
    """Get current degradation level and plan."""
    from src.resilience.bulkhead import get_degradation
    deg = get_degradation()
    return deg.get_degradation_plan()


@router.post("/api/resilience/degradation")
def set_degradation(req: SetDegradationRequest):
    """Set degradation level."""
    from src.resilience.bulkhead import get_degradation, DegradationLevel
    deg = get_degradation()
    level_map = {dl.value: dl for dl in DegradationLevel}
    level = level_map.get(req.level, DegradationLevel.NORMAL)
    deg.set_level(level)
    return {"level": level.value}


# =========================================
# HEALTH
# =========================================

@router.get("/api/resilience/health")
def resilience_health():
    """Resilience subsystem health check."""
    from src.resilience.circuit_breaker import get_circuit_registry
    from src.resilience.chaos_engine import get_chaos_engine
    from src.resilience.bulkhead import get_bulkhead_manager, get_degradation

    registry = get_circuit_registry()
    chaos = get_chaos_engine()
    mgr = get_bulkhead_manager()
    deg = get_degradation()

    return {
        "status": "healthy",
        "circuit_breakers": registry.get_stats(),
        "chaos": chaos.get_stats(),
        "bulkheads": mgr.get_stats(),
        "degradation": {"level": deg.current_level.value},
    }


# =========================================
# ROUTER REGISTRATION
# =========================================

def include_resilience_router(app: FastAPI) -> None:
    app.include_router(router)
