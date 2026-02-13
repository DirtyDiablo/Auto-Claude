"""Phase 53A — Observability API.

12 endpoints for distributed tracing, metrics, SLOs, and alerts.
"""

from __future__ import annotations

from fastapi import FastAPI, APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Optional

router = APIRouter()


# =========================================
# REQUEST MODELS
# =========================================

class RecordMetricRequest(BaseModel):
    metric_name: str
    value: float
    labels: Dict[str, str] = {}


class AlertRuleRequest(BaseModel):
    metric_name: str
    condition: str = "gt"
    threshold: float = 100.0
    severity: str = "warning"


class RecordSLOEventRequest(BaseModel):
    slo_id: str
    good: bool = True
    value: float = 0.0


class RecordSLOBatchRequest(BaseModel):
    slo_id: str
    good_events: int
    total_events: int
    value: float = 0.0


# =========================================
# TRACING ENDPOINTS
# =========================================

@router.get("/api/observability/traces")
def list_traces(limit: int = Query(50)):
    """List recent traces."""
    from src.observability.distributed_tracer import get_tracer
    tracer = get_tracer()
    traces = tracer.list_traces(limit=limit)
    return {"traces": [t.to_dict() for t in traces], "total": len(traces)}


@router.get("/api/observability/traces/{trace_id}")
def get_trace(trace_id: str):
    """Get a trace with all spans."""
    from src.observability.distributed_tracer import get_tracer
    tracer = get_tracer()
    trace = tracer.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    spans = tracer.get_trace_spans(trace_id)
    return {
        "trace": trace.to_dict(),
        "spans": [s.to_dict() for s in spans],
    }


@router.get("/api/observability/spans")
def search_spans(
    operation: Optional[str] = Query(None),
    min_duration_ms: Optional[float] = Query(None),
    limit: int = Query(50),
):
    """Search spans by criteria."""
    from src.observability.distributed_tracer import get_tracer
    tracer = get_tracer()
    spans = tracer.search_spans(
        operation_name=operation,
        min_duration_ms=min_duration_ms,
        limit=limit,
    )
    return {"spans": [s.to_dict() for s in spans], "total": len(spans)}


# =========================================
# METRICS ENDPOINTS
# =========================================

@router.get("/api/observability/metrics")
def list_metrics(metric_type: Optional[str] = Query(None)):
    """List all metrics."""
    from src.observability.metrics_pipeline import get_metrics, MetricType
    pipeline = get_metrics()
    mt = MetricType(metric_type) if metric_type else None
    metrics = pipeline.list_metrics(metric_type=mt)
    return {"metrics": [m.to_dict() for m in metrics], "total": len(metrics)}


@router.post("/api/observability/metrics/record")
def record_metric(req: RecordMetricRequest):
    """Record a metric value."""
    from src.observability.metrics_pipeline import get_metrics
    pipeline = get_metrics()
    pipeline.record(req.metric_name, req.value, req.labels or None)
    return {"recorded": True, "metric": req.metric_name, "value": req.value}


@router.get("/api/observability/metrics/export")
def export_metrics(fmt: str = Query("json")):
    """Export metrics in Prometheus or JSON format."""
    from src.observability.metrics_pipeline import get_metrics
    pipeline = get_metrics()
    if fmt == "prometheus":
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(pipeline.export_prometheus(), media_type="text/plain")
    return pipeline.export_json()


# =========================================
# ALERTS ENDPOINTS
# =========================================

@router.post("/api/observability/alerts/rules")
def create_alert_rule(req: AlertRuleRequest):
    """Create an alert rule."""
    from src.observability.metrics_pipeline import get_metrics
    pipeline = get_metrics()
    rule = pipeline.add_alert_rule(
        metric_name=req.metric_name,
        condition=req.condition,
        threshold=req.threshold,
        severity=req.severity,
    )
    return rule.to_dict()


@router.get("/api/observability/alerts")
def list_alerts(resolved: Optional[bool] = Query(None)):
    """List triggered alerts."""
    from src.observability.metrics_pipeline import get_metrics
    pipeline = get_metrics()
    alerts = pipeline.get_alerts(resolved=resolved)
    return {"alerts": [a.to_dict() for a in alerts], "total": len(alerts)}


# =========================================
# SLO ENDPOINTS
# =========================================

@router.get("/api/observability/slos")
def list_slos():
    """List all SLO definitions and current status."""
    from src.observability.slo_engine import get_slo_engine
    engine = get_slo_engine()
    return engine.get_dashboard()


@router.get("/api/observability/slos/{slo_id}")
def get_slo_report(slo_id: str):
    """Get detailed SLO report with error budget."""
    from src.observability.slo_engine import get_slo_engine
    engine = get_slo_engine()
    report = engine.get_report(slo_id)
    if not report:
        raise HTTPException(status_code=404, detail="SLO not found")
    return report.to_dict()


@router.post("/api/observability/slos/record")
def record_slo_event(req: RecordSLOEventRequest):
    """Record a good/bad event for an SLO."""
    from src.observability.slo_engine import get_slo_engine
    engine = get_slo_engine()
    slo = engine.get_slo(req.slo_id)
    if not slo:
        raise HTTPException(status_code=404, detail="SLO not found")
    engine.record_event(req.slo_id, req.good, req.value)
    return {"recorded": True, "slo_id": req.slo_id, "good": req.good}


# =========================================
# HEALTH
# =========================================

@router.get("/api/observability/health")
def observability_health():
    """Observability subsystem health check."""
    from src.observability.distributed_tracer import get_tracer
    from src.observability.metrics_pipeline import get_metrics
    from src.observability.slo_engine import get_slo_engine

    return {
        "status": "healthy",
        "tracing": get_tracer().get_stats(),
        "metrics": get_metrics().get_stats(),
        "slos": get_slo_engine().get_stats(),
    }


# =========================================
# ROUTER REGISTRATION
# =========================================

def include_observability_router(app: FastAPI) -> None:
    app.include_router(router)
