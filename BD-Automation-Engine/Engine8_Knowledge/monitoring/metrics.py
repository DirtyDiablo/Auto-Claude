"""Phase 30A — Prometheus Metrics"""
import time
import structlog
from typing import Dict
from dataclasses import dataclass
logger = structlog.get_logger(__name__)

@dataclass
class MetricValue:
    name: str
    value: float
    labels: Dict[str, str]
    metric_type: str  # counter, gauge, histogram

class PlatformMetrics:
    """Prometheus metrics for all API services."""
    def __init__(self):
        self._counters: Dict[str, Dict[str, float]] = {}
        self._gauges: Dict[str, Dict[str, float]] = {}
        self._histograms: Dict[str, list] = {}
        self._prom_available = False
        self._request_counter = None
        self._request_duration = None
        self._request_in_progress = None
        self._initialize()

    def _initialize(self):
        try:
            from prometheus_client import Counter, Histogram, Gauge
            self._request_counter = Counter(
                "pts_api_requests_total", "Total API requests",
                ["method", "endpoint", "status_code"]
            )
            self._request_duration = Histogram(
                "pts_api_request_duration_seconds", "Request duration",
                ["method", "endpoint"],
                buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
            )
            self._request_in_progress = Gauge(
                "pts_api_requests_in_progress", "Requests in progress",
                ["endpoint"]
            )
            # Business metrics
            self._contacts_total = Gauge("pts_contacts_total", "Total contacts")
            self._active_campaigns = Gauge("pts_active_campaigns", "Active campaigns")
            self._scrape_jobs = Counter("pts_scrape_jobs_total", "Scrape jobs", ["source"])
            self._search_queries = Counter("pts_search_queries_total", "Search queries", ["type"])
            self._ml_predictions = Counter("pts_ml_predictions_total", "ML predictions", ["model"])
            self._memory_ops = Counter("pts_memory_operations_total", "Memory ops", ["layer", "operation"])
            self._workflow_execs = Counter("pts_workflow_executions_total", "Workflow executions", ["workflow", "status"])
            # Infra metrics
            self._qdrant_vectors = Gauge("pts_qdrant_vectors_total", "Qdrant vectors")
            self._neo4j_nodes = Gauge("pts_neo4j_nodes_total", "Neo4j nodes")
            self._db_query_duration = Histogram("pts_db_query_duration_seconds", "DB query duration", ["db_type"])
            self._prom_available = True
            logger.info("prometheus_metrics_initialized")
        except ImportError:
            logger.warning("prometheus_client_not_installed")

    def inc_counter(self, name: str, labels: Dict[str, str] = None, value: float = 1.0):
        key = f"{name}:{labels}"
        self._counters.setdefault(key, {"name": name, "value": 0.0})
        self._counters[key]["value"] += value

        if self._prom_available and name == "requests":
            self._request_counter.labels(**labels).inc(value)

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        key = f"{name}:{labels}"
        self._gauges[key] = {"name": name, "value": value}

        if self._prom_available:
            if name == "contacts_total":
                self._contacts_total.set(value)
            elif name == "qdrant_vectors":
                self._qdrant_vectors.set(value)
            elif name == "neo4j_nodes":
                self._neo4j_nodes.set(value)

    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        key = f"{name}:{labels}"
        self._histograms.setdefault(key, []).append(value)

        if self._prom_available and name == "request_duration":
            self._request_duration.labels(**labels).observe(value)

    def instrument_fastapi(self, app):
        """Add middleware for auto-recording request metrics."""
        metrics = self

        try:
            from starlette.middleware.base import BaseHTTPMiddleware
            from starlette.requests import Request

            class MetricsMiddleware(BaseHTTPMiddleware):
                async def dispatch(self, request: Request, call_next):
                    endpoint = request.url.path
                    method = request.method
                    start = time.time()

                    try:
                        response = await call_next(request)
                        status = str(response.status_code)
                    except Exception:
                        status = "500"
                        raise
                    finally:
                        duration = time.time() - start
                        metrics.inc_counter("requests", {"method": method, "endpoint": endpoint, "status_code": status})
                        metrics.observe_histogram("request_duration", duration, {"method": method, "endpoint": endpoint})

                    return response

            app.add_middleware(MetricsMiddleware)
            logger.info("fastapi_metrics_middleware_added")
        except Exception as e:
            logger.warning("middleware_setup_failed", error=str(e))

    def expose_endpoint(self, app, path: str = "/metrics"):
        """Expose Prometheus scrape endpoint."""
        if self._prom_available:
            try:
                from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
                from starlette.responses import Response

                @app.get(path)
                async def metrics_endpoint():
                    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

                logger.info("prometheus_endpoint_exposed", path=path)
            except Exception as e:
                logger.warning("expose_endpoint_failed", error=str(e))
        else:
            @app.get(path)
            async def metrics_fallback():
                return {"error": "prometheus_client not installed", "counters": len(self._counters),
                        "gauges": len(self._gauges)}

    def get_stats(self) -> Dict:
        return {
            "prometheus_available": self._prom_available,
            "counters": len(self._counters),
            "gauges": len(self._gauges),
            "histograms": len(self._histograms),
        }

_metrics = None
def get_platform_metrics():
    global _metrics
    if _metrics is None:
        _metrics = PlatformMetrics()
    return _metrics
