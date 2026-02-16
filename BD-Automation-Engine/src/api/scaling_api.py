"""Phase 57A — Scaling API.

12 endpoints for connection pools, read replicas, cache layers,
and auto-scaling policies.
"""

from __future__ import annotations

from fastapi import FastAPI, APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Any, List, Optional

router = APIRouter()


# =========================================
# REQUEST MODELS
# =========================================


class ResizePoolRequest(BaseModel):
    new_max: int = 50


class UpdateReplicaStatusRequest(BaseModel):
    status: str = "active"


class CachePutRequest(BaseModel):
    key: str
    value: Any = None
    ttl: int = 300
    layer_name: Optional[str] = None


class CacheWarmRequest(BaseModel):
    keys: List[str] = []


class EvaluateScalingRequest(BaseModel):
    current_value: float = 0.0


class UpdatePolicyRequest(BaseModel):
    scale_up_threshold: Optional[float] = None
    scale_down_threshold: Optional[float] = None
    min_replicas: Optional[int] = None
    max_replicas: Optional[int] = None


# =========================================
# CONNECTION POOL ENDPOINTS
# =========================================


@router.get("/api/scaling/pools")
def list_pools():
    """List all connection pools."""
    from src.scaling.connection_pool import get_pool_manager

    mgr = get_pool_manager()
    pools = mgr.list_pools()
    return {"pools": [p.to_dict() for p in pools], "total": len(pools)}


@router.get("/api/scaling/pools/{name}")
def get_pool(name: str):
    """Get a specific connection pool."""
    from src.scaling.connection_pool import get_pool_manager

    mgr = get_pool_manager()
    pool = mgr.get_pool(name)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    return pool.to_dict()


@router.get("/api/scaling/pools/{name}/health")
def get_pool_health(name: str):
    """Get health status for a connection pool."""
    from src.scaling.connection_pool import get_pool_manager

    mgr = get_pool_manager()
    pool = mgr.get_pool(name)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    return mgr.get_health(name)


# =========================================
# READ REPLICA ENDPOINTS
# =========================================


@router.get("/api/scaling/replicas")
def list_replicas(status: Optional[str] = Query(None)):
    """List read replicas."""
    from src.scaling.read_replicas import get_replica_manager, ReplicaStatus

    mgr = get_replica_manager()
    st = ReplicaStatus(status) if status else None
    replicas = mgr.list_replicas(status_filter=st)
    return {"replicas": [r.to_dict() for r in replicas], "total": len(replicas)}


@router.get("/api/scaling/replicas/lag")
def get_lag_report():
    """Get replication lag report."""
    from src.scaling.read_replicas import get_replica_manager

    mgr = get_replica_manager()
    return mgr.get_lag_report()


@router.post("/api/scaling/replicas/{replica_id}/promote")
def promote_replica(replica_id: str):
    """Promote a replica to active status."""
    from src.scaling.read_replicas import get_replica_manager

    mgr = get_replica_manager()
    replica = mgr.get_replica(replica_id)
    if not replica:
        raise HTTPException(status_code=404, detail="Replica not found")
    mgr.promote_replica(replica_id)
    return {"promoted": True, "replica_id": replica_id}


# =========================================
# CACHE LAYER ENDPOINTS
# =========================================


@router.get("/api/scaling/cache")
def list_cache_layers():
    """List all cache layers."""
    from src.scaling.cache_layer import get_cache_manager

    mgr = get_cache_manager()
    layers = mgr.list_layers()
    return {"layers": [l.to_dict() for l in layers], "total": len(layers)}


@router.get("/api/scaling/cache/hit-rates")
def get_hit_rates():
    """Get hit rates for all cache layers."""
    from src.scaling.cache_layer import get_cache_manager

    mgr = get_cache_manager()
    return mgr.get_hit_rates()


@router.post("/api/scaling/cache/warm")
def warm_cache(req: CacheWarmRequest):
    """Warm cache with specified keys."""
    from src.scaling.cache_layer import get_cache_manager

    mgr = get_cache_manager()
    count = mgr.warm_cache(req.keys)
    return {"warmed": count, "keys_requested": len(req.keys)}


# =========================================
# AUTO-SCALING ENDPOINTS
# =========================================


@router.get("/api/scaling/policies")
def list_policies():
    """List auto-scaling policies."""
    from src.scaling.auto_scaler import get_auto_scaler

    scaler = get_auto_scaler()
    policies = scaler.list_policies()
    return {"policies": [p.to_dict() for p in policies], "total": len(policies)}


@router.post("/api/scaling/policies/{policy_id}/evaluate")
def evaluate_policy(policy_id: str, req: EvaluateScalingRequest):
    """Evaluate a scaling policy against a metric value."""
    from src.scaling.auto_scaler import get_auto_scaler

    scaler = get_auto_scaler()
    policy = scaler.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    event = scaler.evaluate(policy_id, req.current_value)
    return event.to_dict()


@router.get("/api/scaling/recommendations")
def get_recommendations():
    """Get auto-scaling recommendations."""
    from src.scaling.auto_scaler import get_auto_scaler

    scaler = get_auto_scaler()
    return {"recommendations": scaler.get_recommendations()}


# =========================================
# HEALTH
# =========================================


@router.get("/api/scaling/health")
def scaling_health():
    """Scaling subsystem health check."""
    from src.scaling.connection_pool import get_pool_manager
    from src.scaling.read_replicas import get_replica_manager
    from src.scaling.cache_layer import get_cache_manager
    from src.scaling.auto_scaler import get_auto_scaler

    return {
        "status": "healthy",
        "connection_pools": get_pool_manager().get_stats(),
        "read_replicas": get_replica_manager().get_stats(),
        "cache": get_cache_manager().get_stats(),
        "auto_scaling": get_auto_scaler().get_stats(),
    }


# =========================================
# ROUTER REGISTRATION
# =========================================


def include_scaling_router(app: FastAPI) -> None:
    app.include_router(router)
