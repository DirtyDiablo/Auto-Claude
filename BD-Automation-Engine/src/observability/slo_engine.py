"""Phase 53A — SLO (Service Level Objective) Engine.

Defines and monitors SLOs for API availability, latency, error rates,
and data freshness.  Computes error budgets, burn rates, and SLO
compliance over rolling windows.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================

class SLOType(str, Enum):
    AVAILABILITY = "availability"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    FRESHNESS = "freshness"


class SLOStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"  # >50% budget consumed
    CRITICAL = "critical"  # >80% budget consumed
    BREACHED = "breached"  # 100% budget consumed


@dataclass
class SLODefinition:
    """A Service Level Objective definition."""
    slo_id: str
    name: str
    slo_type: SLOType
    target: float  # e.g., 99.9 for 99.9% availability
    window_hours: int = 720  # 30 days default
    description: str = ""
    metric_name: str = ""
    enabled: bool = True
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slo_id": self.slo_id,
            "name": self.name,
            "slo_type": self.slo_type.value,
            "target": self.target,
            "window_hours": self.window_hours,
            "description": self.description,
            "metric_name": self.metric_name,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }


@dataclass
class SLOMeasurement:
    """A single SLO measurement."""
    timestamp: float
    good_events: int
    total_events: int
    value: float  # computed SLI value


@dataclass
class SLOReport:
    """Current state of an SLO."""
    slo_id: str
    name: str
    slo_type: str
    target: float
    current_value: float
    error_budget_total: float
    error_budget_remaining: float
    error_budget_pct: float  # % remaining
    burn_rate: float  # how fast budget is being consumed
    status: SLOStatus
    window_hours: int
    total_events: int
    good_events: int
    bad_events: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slo_id": self.slo_id,
            "name": self.name,
            "slo_type": self.slo_type,
            "target": self.target,
            "current_value": round(self.current_value, 4),
            "error_budget_total": round(self.error_budget_total, 4),
            "error_budget_remaining": round(self.error_budget_remaining, 4),
            "error_budget_pct": round(self.error_budget_pct, 2),
            "burn_rate": round(self.burn_rate, 4),
            "status": self.status.value,
            "window_hours": self.window_hours,
            "total_events": self.total_events,
            "good_events": self.good_events,
            "bad_events": self.bad_events,
        }


# =========================================
# BUILT-IN SLO DEFINITIONS
# =========================================

_BUILTIN_SLOS = [
    SLODefinition(
        slo_id="slo_api_availability",
        name="API Availability",
        slo_type=SLOType.AVAILABILITY,
        target=99.9,
        description="API uptime target 99.9% over 30-day window",
        metric_name="api_requests_total",
    ),
    SLODefinition(
        slo_id="slo_api_latency_p99",
        name="API Latency P99",
        slo_type=SLOType.LATENCY,
        target=500.0,  # 500ms p99
        description="99th percentile API latency under 500ms",
        metric_name="api_request_duration_ms",
    ),
    SLODefinition(
        slo_id="slo_search_latency",
        name="Search Latency P95",
        slo_type=SLOType.LATENCY,
        target=250.0,  # 250ms p95
        description="95th percentile search latency under 250ms",
        metric_name="search_latency_ms",
    ),
    SLODefinition(
        slo_id="slo_error_rate",
        name="API Error Rate",
        slo_type=SLOType.ERROR_RATE,
        target=0.1,  # 0.1% errors
        description="Error rate below 0.1% over 30-day window",
        metric_name="api_errors_total",
    ),
    SLODefinition(
        slo_id="slo_data_freshness",
        name="Data Freshness",
        slo_type=SLOType.FRESHNESS,
        target=24.0,  # data no older than 24 hours
        description="All indexed data refreshed within 24 hours",
        metric_name="data_age_hours",
    ),
    SLODefinition(
        slo_id="slo_pipeline_throughput",
        name="Pipeline Throughput",
        slo_type=SLOType.THROUGHPUT,
        target=1000.0,  # 1000 records/hour
        description="Pipeline processes at least 1000 records per hour",
        metric_name="pipeline_throughput",
    ),
]


# =========================================
# SLO ENGINE
# =========================================

class SLOEngine:
    """Service Level Objective monitoring and error budget tracking.

    Defines SLOs, records measurements (good/bad events), computes
    error budgets, burn rates, and compliance status.
    """

    def __init__(self):
        self._slos: Dict[str, SLODefinition] = {}
        self._measurements: Dict[str, List[SLOMeasurement]] = {}  # slo_id → measurements

        for slo in _BUILTIN_SLOS:
            self._slos[slo.slo_id] = slo
            self._measurements[slo.slo_id] = []

        logger.info("SLOEngine initialized with %d built-in SLOs", len(self._slos))

    # ----- SLO management -----

    def add_slo(self, slo: SLODefinition) -> None:
        self._slos[slo.slo_id] = slo
        self._measurements.setdefault(slo.slo_id, [])

    def get_slo(self, slo_id: str) -> Optional[SLODefinition]:
        return self._slos.get(slo_id)

    def list_slos(self, enabled_only: bool = False) -> List[SLODefinition]:
        slos = list(self._slos.values())
        if enabled_only:
            slos = [s for s in slos if s.enabled]
        return slos

    def update_slo(self, slo_id: str, **kwargs) -> Optional[SLODefinition]:
        slo = self._slos.get(slo_id)
        if not slo:
            return None
        for key, val in kwargs.items():
            if hasattr(slo, key):
                setattr(slo, key, val)
        return slo

    # ----- recording -----

    def record_event(
        self,
        slo_id: str,
        good: bool,
        value: float = 0.0,
    ) -> None:
        """Record a single good or bad event for an SLO."""
        if slo_id not in self._slos:
            return
        measurements = self._measurements[slo_id]
        now = time.time()

        # Add to current measurement bucket or create new
        if measurements and (now - measurements[-1].timestamp) < 60:
            # Aggregate into current bucket (1-minute buckets)
            m = measurements[-1]
            m.total_events += 1
            if good:
                m.good_events += 1
            m.value = value
        else:
            measurements.append(SLOMeasurement(
                timestamp=now,
                good_events=1 if good else 0,
                total_events=1,
                value=value,
            ))

    def record_batch(
        self,
        slo_id: str,
        good_events: int,
        total_events: int,
        value: float = 0.0,
    ) -> None:
        """Record a batch of events."""
        if slo_id not in self._slos:
            return
        self._measurements[slo_id].append(SLOMeasurement(
            timestamp=time.time(),
            good_events=good_events,
            total_events=total_events,
            value=value,
        ))

    # ----- reporting -----

    def get_report(self, slo_id: str) -> Optional[SLOReport]:
        """Generate current SLO report with error budget."""
        slo = self._slos.get(slo_id)
        if not slo:
            return None

        measurements = self._measurements.get(slo_id, [])
        # Filter to window
        window_start = time.time() - (slo.window_hours * 3600)
        window_measurements = [m for m in measurements if m.timestamp >= window_start]

        total_events = sum(m.total_events for m in window_measurements)
        good_events = sum(m.good_events for m in window_measurements)
        bad_events = total_events - good_events

        # Compute SLI
        if total_events == 0:
            current_value = 100.0 if slo.slo_type in (SLOType.AVAILABILITY,) else 0.0
        elif slo.slo_type == SLOType.AVAILABILITY:
            current_value = (good_events / total_events) * 100
        elif slo.slo_type == SLOType.ERROR_RATE:
            current_value = (bad_events / total_events) * 100
        elif slo.slo_type in (SLOType.LATENCY, SLOType.FRESHNESS, SLOType.THROUGHPUT):
            if window_measurements:
                current_value = window_measurements[-1].value
            else:
                current_value = 0.0
        else:
            current_value = 0.0

        # Error budget
        if slo.slo_type == SLOType.AVAILABILITY:
            error_budget_total = (100.0 - slo.target) / 100.0 * max(total_events, 1)
            error_budget_remaining = max(0, error_budget_total - bad_events)
        elif slo.slo_type == SLOType.ERROR_RATE:
            error_budget_total = slo.target / 100.0 * max(total_events, 1)
            error_budget_remaining = max(0, error_budget_total - bad_events)
        else:
            error_budget_total = slo.target
            error_budget_remaining = max(0, slo.target - current_value) if slo.slo_type == SLOType.LATENCY else slo.target

        budget_pct = (error_budget_remaining / max(error_budget_total, 0.001)) * 100

        # Burn rate (how fast budget is being consumed relative to expected)
        if error_budget_total > 0 and total_events > 0:
            expected_bad_per_event = (100.0 - slo.target) / 100.0 if slo.slo_type == SLOType.AVAILABILITY else slo.target / 100.0
            actual_bad_rate = bad_events / total_events if total_events > 0 else 0
            burn_rate = actual_bad_rate / max(expected_bad_per_event, 0.0001)
        else:
            burn_rate = 0.0

        # Status
        if budget_pct <= 0:
            status = SLOStatus.BREACHED
        elif budget_pct < 20:
            status = SLOStatus.CRITICAL
        elif budget_pct < 50:
            status = SLOStatus.WARNING
        else:
            status = SLOStatus.HEALTHY

        return SLOReport(
            slo_id=slo.slo_id,
            name=slo.name,
            slo_type=slo.slo_type.value,
            target=slo.target,
            current_value=current_value,
            error_budget_total=error_budget_total,
            error_budget_remaining=error_budget_remaining,
            error_budget_pct=budget_pct,
            burn_rate=burn_rate,
            status=status,
            window_hours=slo.window_hours,
            total_events=total_events,
            good_events=good_events,
            bad_events=bad_events,
        )

    def get_all_reports(self) -> List[SLOReport]:
        """Get reports for all enabled SLOs."""
        reports = []
        for slo in self._slos.values():
            if slo.enabled:
                report = self.get_report(slo.slo_id)
                if report:
                    reports.append(report)
        return reports

    def get_dashboard(self) -> Dict[str, Any]:
        """Get SLO dashboard summary."""
        reports = self.get_all_reports()
        by_status = {}
        for r in reports:
            by_status[r.status.value] = by_status.get(r.status.value, 0) + 1

        return {
            "total_slos": len(reports),
            "by_status": by_status,
            "overall_health": "healthy" if not by_status.get("breached", 0) and not by_status.get("critical", 0) else "degraded",
            "slos": [r.to_dict() for r in reports],
        }

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        total_measurements = sum(len(m) for m in self._measurements.values())
        return {
            "total_slos": len(self._slos),
            "enabled_slos": sum(1 for s in self._slos.values() if s.enabled),
            "total_measurements": total_measurements,
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[SLOEngine] = None


def get_slo_engine() -> SLOEngine:
    global _instance
    if _instance is None:
        _instance = SLOEngine()
    return _instance
