"""Phase 53A — Metrics Pipeline with Prometheus-Compatible Export.

Collects counters, gauges, histograms, and summaries.  Pre-built
BD-specific metrics for API latency, search performance, pipeline
throughput, and agent utilization.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================

class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Metric:
    """A named metric with type and data points."""
    name: str
    metric_type: MetricType
    description: str = ""
    unit: str = ""
    points: List[MetricPoint] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    # Histogram-specific
    bucket_boundaries: List[float] = field(default_factory=list)
    bucket_counts: Dict[str, int] = field(default_factory=dict)
    _sum: float = 0.0
    _count: int = 0
    _min: float = float("inf")
    _max: float = float("-inf")
    # Gauge current value
    _current: float = 0.0

    def record(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a metric value."""
        now = time.time()
        self.points.append(MetricPoint(timestamp=now, value=value, labels=labels or {}))
        self._sum += value
        self._count += 1
        self._min = min(self._min, value)
        self._max = max(self._max, value)

        if self.metric_type == MetricType.GAUGE:
            self._current = value
        elif self.metric_type == MetricType.HISTOGRAM:
            for boundary in self.bucket_boundaries:
                key = str(boundary)
                if value <= boundary:
                    self.bucket_counts[key] = self.bucket_counts.get(key, 0) + 1

    def get_current(self) -> float:
        if self.metric_type == MetricType.GAUGE:
            return self._current
        if self.metric_type == MetricType.COUNTER:
            return self._sum
        return self._sum

    def get_average(self) -> float:
        if self._count == 0:
            return 0.0
        return self._sum / self._count

    def get_percentile(self, p: float) -> float:
        """Get the p-th percentile (0-100)."""
        if not self.points:
            return 0.0
        values = sorted(pt.value for pt in self.points)
        k = (len(values) - 1) * (p / 100.0)
        f = int(k)
        c = f + 1
        if c >= len(values):
            return values[-1]
        d0 = values[f] * (c - k)
        d1 = values[c] * (k - f)
        return d0 + d1

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "type": self.metric_type.value,
            "description": self.description,
            "unit": self.unit,
            "count": self._count,
            "sum": round(self._sum, 4),
            "current": round(self._current, 4),
        }
        if self._count > 0:
            result["avg"] = round(self.get_average(), 4)
            result["min"] = round(self._min, 4)
            result["max"] = round(self._max, 4)
            result["p50"] = round(self.get_percentile(50), 4)
            result["p95"] = round(self.get_percentile(95), 4)
            result["p99"] = round(self.get_percentile(99), 4)
        if self.bucket_counts:
            result["buckets"] = self.bucket_counts
        return result


@dataclass
class Alert:
    """A metric alert when a threshold is breached."""
    alert_id: str
    metric_name: str
    condition: str  # gt | lt | gte | lte
    threshold: float
    current_value: float
    severity: str = "warning"  # info | warning | critical
    triggered_at: str = ""
    resolved: bool = False

    def __post_init__(self):
        if not self.triggered_at:
            self.triggered_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "metric_name": self.metric_name,
            "condition": self.condition,
            "threshold": self.threshold,
            "current_value": round(self.current_value, 4),
            "severity": self.severity,
            "triggered_at": self.triggered_at,
            "resolved": self.resolved,
        }


@dataclass
class AlertRule:
    """Rule for triggering metric alerts."""
    rule_id: str
    metric_name: str
    condition: str  # gt | lt | gte | lte
    threshold: float
    severity: str = "warning"
    enabled: bool = True
    cooldown_sec: float = 300.0
    last_triggered: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "metric_name": self.metric_name,
            "condition": self.condition,
            "threshold": self.threshold,
            "severity": self.severity,
            "enabled": self.enabled,
        }


# =========================================
# BUILT-IN BD METRICS
# =========================================

_BUILTIN_METRICS = [
    ("api_request_duration_ms", MetricType.HISTOGRAM, "API request latency", "ms",
     [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000]),
    ("api_requests_total", MetricType.COUNTER, "Total API requests", "requests", []),
    ("api_errors_total", MetricType.COUNTER, "Total API errors", "errors", []),
    ("search_latency_ms", MetricType.HISTOGRAM, "Search query latency", "ms",
     [10, 25, 50, 100, 250, 500, 1000]),
    ("search_results_count", MetricType.HISTOGRAM, "Search result count", "results",
     [0, 1, 5, 10, 25, 50, 100]),
    ("pipeline_jobs_active", MetricType.GAUGE, "Active pipeline jobs", "jobs", []),
    ("pipeline_throughput", MetricType.COUNTER, "Pipeline records processed", "records", []),
    ("agent_invocations_total", MetricType.COUNTER, "Total agent invocations", "invocations", []),
    ("agent_duration_ms", MetricType.HISTOGRAM, "Agent execution time", "ms",
     [100, 500, 1000, 5000, 10000, 30000]),
    ("contacts_indexed", MetricType.GAUGE, "Contacts in vector store", "contacts", []),
    ("qdrant_query_ms", MetricType.HISTOGRAM, "Qdrant query latency", "ms",
     [1, 5, 10, 25, 50, 100, 250]),
    ("cache_hit_ratio", MetricType.GAUGE, "Cache hit ratio", "ratio", []),
    ("encryption_operations_total", MetricType.COUNTER, "Encryption operations", "ops", []),
    ("audit_events_total", MetricType.COUNTER, "Audit events logged", "events", []),
]


# =========================================
# METRICS PIPELINE
# =========================================

class MetricsPipeline:
    """Prometheus-compatible metrics collection and alerting.

    Pre-registers BD-specific metrics and supports custom metric
    creation, alert rules, and Prometheus/OTLP export.
    """

    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._alert_rules: Dict[str, AlertRule] = {}
        self._alerts: List[Alert] = []
        self._registered_exporters: List[str] = []

        # Register built-in metrics
        for name, mtype, desc, unit, buckets in _BUILTIN_METRICS:
            self._metrics[name] = Metric(
                name=name,
                metric_type=mtype,
                description=desc,
                unit=unit,
                bucket_boundaries=buckets,
            )
        logger.info("MetricsPipeline initialized with %d built-in metrics",
                     len(self._metrics))

    # ----- metric operations -----

    def record(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a value for a metric."""
        metric = self._metrics.get(metric_name)
        if not metric:
            # Auto-create gauge for unknown metrics
            metric = Metric(
                name=metric_name,
                metric_type=MetricType.GAUGE,
                description=f"Auto-created metric: {metric_name}",
            )
            self._metrics[metric_name] = metric
        metric.record(value, labels)
        self._check_alerts(metric_name)

    def increment(self, metric_name: str, amount: float = 1.0) -> None:
        """Increment a counter metric."""
        self.record(metric_name, amount)

    def set_gauge(self, metric_name: str, value: float) -> None:
        """Set a gauge to a specific value."""
        self.record(metric_name, value)

    def observe(self, metric_name: str, value: float) -> None:
        """Observe a value for a histogram/summary."""
        self.record(metric_name, value)

    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str = "",
        unit: str = "",
        bucket_boundaries: Optional[List[float]] = None,
    ) -> Metric:
        """Register a custom metric."""
        metric = Metric(
            name=name,
            metric_type=metric_type,
            description=description,
            unit=unit,
            bucket_boundaries=bucket_boundaries or [],
        )
        self._metrics[name] = metric
        return metric

    # ----- queries -----

    def get_metric(self, name: str) -> Optional[Metric]:
        return self._metrics.get(name)

    def list_metrics(self, metric_type: Optional[MetricType] = None) -> List[Metric]:
        metrics = list(self._metrics.values())
        if metric_type:
            metrics = [m for m in metrics if m.metric_type == metric_type]
        return metrics

    def get_metric_value(self, name: str) -> Optional[float]:
        metric = self._metrics.get(name)
        if metric:
            return metric.get_current()
        return None

    # ----- alert rules -----

    def add_alert_rule(
        self,
        metric_name: str,
        condition: str,
        threshold: float,
        severity: str = "warning",
    ) -> AlertRule:
        """Add an alert rule."""
        rule_id = f"rule_{uuid.uuid4().hex[:10]}"
        rule = AlertRule(
            rule_id=rule_id,
            metric_name=metric_name,
            condition=condition,
            threshold=threshold,
            severity=severity,
        )
        self._alert_rules[rule_id] = rule
        return rule

    def list_alert_rules(self) -> List[AlertRule]:
        return list(self._alert_rules.values())

    def get_alerts(self, resolved: Optional[bool] = None) -> List[Alert]:
        alerts = self._alerts
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        return list(reversed(alerts))

    def _check_alerts(self, metric_name: str) -> None:
        """Check if any alert rules are triggered."""
        metric = self._metrics.get(metric_name)
        if not metric:
            return

        now = time.time()
        current = metric.get_current()

        for rule in self._alert_rules.values():
            if rule.metric_name != metric_name or not rule.enabled:
                continue
            if now - rule.last_triggered < rule.cooldown_sec:
                continue

            triggered = False
            if rule.condition == "gt" and current > rule.threshold:
                triggered = True
            elif rule.condition == "lt" and current < rule.threshold:
                triggered = True
            elif rule.condition == "gte" and current >= rule.threshold:
                triggered = True
            elif rule.condition == "lte" and current <= rule.threshold:
                triggered = True

            if triggered:
                alert = Alert(
                    alert_id=f"alert_{uuid.uuid4().hex[:10]}",
                    metric_name=metric_name,
                    condition=rule.condition,
                    threshold=rule.threshold,
                    current_value=current,
                    severity=rule.severity,
                )
                self._alerts.append(alert)
                rule.last_triggered = now

    # ----- export -----

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        lines: List[str] = []
        for metric in self._metrics.values():
            if metric._count == 0:
                continue
            lines.append(f"# HELP {metric.name} {metric.description}")
            lines.append(f"# TYPE {metric.name} {metric.metric_type.value}")
            if metric.metric_type == MetricType.COUNTER:
                lines.append(f"{metric.name}_total {metric._sum}")
            elif metric.metric_type == MetricType.GAUGE:
                lines.append(f"{metric.name} {metric._current}")
            elif metric.metric_type == MetricType.HISTOGRAM:
                for boundary in metric.bucket_boundaries:
                    count = metric.bucket_counts.get(str(boundary), 0)
                    lines.append(f'{metric.name}_bucket{{le="{boundary}"}} {count}')
                lines.append(f"{metric.name}_sum {metric._sum}")
                lines.append(f"{metric.name}_count {metric._count}")
        return "\n".join(lines)

    def export_json(self) -> List[Dict[str, Any]]:
        """Export all metrics as JSON."""
        return [m.to_dict() for m in self._metrics.values() if m._count > 0]

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        active = sum(1 for m in self._metrics.values() if m._count > 0)
        return {
            "total_metrics": len(self._metrics),
            "active_metrics": active,
            "total_alert_rules": len(self._alert_rules),
            "total_alerts": len(self._alerts),
            "unresolved_alerts": sum(1 for a in self._alerts if not a.resolved),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[MetricsPipeline] = None


def get_metrics() -> MetricsPipeline:
    global _instance
    if _instance is None:
        _instance = MetricsPipeline()
    return _instance
