"""Phase 43A — Quality SLA Engine

Define and enforce quality SLAs (Service Level Agreements) for data assets.
Monitor compliance, track history, and generate alerts on violations.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# ENUMS
# =========================================

class SLAStatus(str, Enum):
    MEETING = "meeting"
    AT_RISK = "at_risk"
    VIOLATED = "violated"
    SUSPENDED = "suspended"


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class SLATarget:
    """A single target within an SLA."""
    metric: str = ""          # freshness_hours, completeness, accuracy, uptime, latency_ms
    target_value: float = 0.0
    operator: str = ">="      # direction: >= means "at least", <= means "at most"
    window: str = "7d"        # measurement window: 1d, 7d, 30d
    description: str = ""


@dataclass
class QualitySLA:
    """A quality SLA for a data asset or service."""
    id: str = ""
    name: str = ""
    asset_id: str = ""
    owner: str = ""
    description: str = ""
    targets: List[SLATarget] = field(default_factory=list)
    status: str = SLAStatus.MEETING.value
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SLAAlert:
    """An alert generated when an SLA is at risk or violated."""
    id: str = ""
    sla_id: str = ""
    sla_name: str = ""
    level: str = AlertLevel.WARNING.value
    target_metric: str = ""
    expected: str = ""
    actual: str = ""
    message: str = ""
    created_at: str = ""
    acknowledged: bool = False
    acknowledged_at: str = ""


@dataclass
class SLACheckResult:
    """Result of checking an SLA against current metrics."""
    sla_id: str = ""
    sla_name: str = ""
    status: str = SLAStatus.MEETING.value
    targets_checked: int = 0
    targets_met: int = 0
    targets_at_risk: int = 0
    targets_violated: int = 0
    alerts: List[SLAAlert] = field(default_factory=list)
    checked_at: str = ""


@dataclass
class SLAHistoryEntry:
    """Historical record of SLA compliance."""
    sla_id: str = ""
    status: str = ""
    compliance_pct: float = 0.0
    period: str = ""
    checked_at: str = ""


# =========================================
# SLA ENGINE
# =========================================

class SLAEngine:
    """Quality SLA management and enforcement."""

    def __init__(self):
        self._slas: Dict[str, QualitySLA] = {}
        self._alerts: List[SLAAlert] = []
        self._history: List[SLAHistoryEntry] = []
        self._check_results: List[SLACheckResult] = []
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        """Seed with platform-level SLAs."""
        now = datetime.now(timezone.utc).isoformat()

        defaults = [
            QualitySLA(
                id="sla_contacts_freshness",
                name="Contacts Data Freshness",
                asset_id="contacts",
                owner="Engine7_BullhornETL",
                description="Contact data must be refreshed weekly with 95% accuracy",
                targets=[
                    SLATarget(metric="freshness_hours", target_value=168.0, operator="<=",
                              window="7d", description="Max 168 hours (1 week) staleness"),
                    SLATarget(metric="accuracy", target_value=0.95, operator=">=",
                              window="30d", description="At least 95% accuracy"),
                    SLATarget(metric="completeness", target_value=0.90, operator=">=",
                              window="30d", description="At least 90% field completeness"),
                ],
            ),
            QualitySLA(
                id="sla_jobs_freshness",
                name="Job Data Freshness",
                asset_id="jobs",
                owner="Engine1_Scraper",
                description="Job data scraped daily with 4-hour max staleness",
                targets=[
                    SLATarget(metric="freshness_hours", target_value=4.0, operator="<=",
                              window="1d", description="Max 4 hours staleness"),
                    SLATarget(metric="completeness", target_value=0.85, operator=">=",
                              window="7d", description="At least 85% completeness"),
                ],
            ),
            QualitySLA(
                id="sla_programs_quality",
                name="Programs Data Quality",
                asset_id="programs",
                owner="Engine2_ProgramMapping",
                description="Program data maintained with high accuracy and completeness",
                targets=[
                    SLATarget(metric="accuracy", target_value=0.90, operator=">=",
                              window="30d", description="At least 90% accuracy"),
                    SLATarget(metric="completeness", target_value=0.80, operator=">=",
                              window="30d", description="At least 80% completeness"),
                    SLATarget(metric="freshness_hours", target_value=168.0, operator="<=",
                              window="7d", description="Updated at least weekly"),
                ],
            ),
        ]

        for sla in defaults:
            sla.created_at = now
            sla.updated_at = now
            self._slas[sla.id] = sla

    # -----------------------------------------
    # CRUD
    # -----------------------------------------

    def create(self, sla: QualitySLA) -> str:
        """Create a new SLA."""
        if not sla.id:
            sla.id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc).isoformat()
        if not sla.created_at:
            sla.created_at = now
        sla.updated_at = now
        self._slas[sla.id] = sla
        return sla.id

    def get(self, sla_id: str) -> Optional[QualitySLA]:
        """Get an SLA by ID."""
        return self._slas.get(sla_id)

    def list_slas(self, asset_id: str = "", status: str = "") -> List[QualitySLA]:
        """List SLAs with optional filtering."""
        results = list(self._slas.values())
        if asset_id:
            results = [s for s in results if s.asset_id == asset_id]
        if status:
            results = [s for s in results if s.status == status]
        return results

    def update(self, sla_id: str, updates: Dict[str, Any]) -> Optional[QualitySLA]:
        """Update an SLA."""
        sla = self._slas.get(sla_id)
        if not sla:
            return None
        for key, val in updates.items():
            if hasattr(sla, key) and key not in {"id", "created_at"}:
                setattr(sla, key, val)
        sla.updated_at = datetime.now(timezone.utc).isoformat()
        return sla

    def delete(self, sla_id: str) -> bool:
        """Delete an SLA."""
        return self._slas.pop(sla_id, None) is not None

    # -----------------------------------------
    # CHECK / ENFORCE
    # -----------------------------------------

    def check_sla(self, sla_id: str, current_metrics: Dict[str, float]) -> SLACheckResult:
        """Check an SLA against current metrics."""
        sla = self._slas.get(sla_id)
        if not sla:
            return SLACheckResult(sla_id=sla_id, status="error")

        now_iso = datetime.now(timezone.utc).isoformat()
        alerts: List[SLAAlert] = []
        targets_met = 0
        targets_at_risk = 0
        targets_violated = 0

        for target in sla.targets:
            actual = current_metrics.get(target.metric, 0.0)
            met = self._evaluate_target(target.operator, actual, target.target_value)

            if met:
                targets_met += 1
                # Check at-risk: within 10% of threshold
                margin = self._compute_margin(target.operator, actual, target.target_value)
                if margin < 0.1:
                    targets_at_risk += 1
                    alerts.append(SLAAlert(
                        id=uuid.uuid4().hex[:10],
                        sla_id=sla_id,
                        sla_name=sla.name,
                        level=AlertLevel.INFO.value,
                        target_metric=target.metric,
                        expected=f"{target.operator} {target.target_value}",
                        actual=str(actual),
                        message=f"{target.metric} at risk: {actual} (threshold: {target.target_value})",
                        created_at=now_iso,
                    ))
            else:
                targets_violated += 1
                alerts.append(SLAAlert(
                    id=uuid.uuid4().hex[:10],
                    sla_id=sla_id,
                    sla_name=sla.name,
                    level=AlertLevel.CRITICAL.value,
                    target_metric=target.metric,
                    expected=f"{target.operator} {target.target_value}",
                    actual=str(actual),
                    message=f"{target.metric} violated: {actual} (expected {target.operator} {target.target_value})",
                    created_at=now_iso,
                ))

        # Determine overall status
        if targets_violated > 0:
            status = SLAStatus.VIOLATED.value
        elif targets_at_risk > 0:
            status = SLAStatus.AT_RISK.value
        else:
            status = SLAStatus.MEETING.value

        sla.status = status
        sla.updated_at = now_iso
        self._alerts.extend(alerts)

        # Record history
        total_targets = len(sla.targets)
        compliance = targets_met / total_targets if total_targets > 0 else 1.0
        self._history.append(SLAHistoryEntry(
            sla_id=sla_id,
            status=status,
            compliance_pct=round(compliance * 100, 1),
            period=now_iso[:10],
            checked_at=now_iso,
        ))

        result = SLACheckResult(
            sla_id=sla_id,
            sla_name=sla.name,
            status=status,
            targets_checked=total_targets,
            targets_met=targets_met,
            targets_at_risk=targets_at_risk,
            targets_violated=targets_violated,
            alerts=alerts,
            checked_at=now_iso,
        )
        self._check_results.append(result)
        return result

    def check_all(self, metrics_by_asset: Dict[str, Dict[str, float]]) -> List[SLACheckResult]:
        """Check all active SLAs against provided metrics."""
        results = []
        for sla in self._slas.values():
            if sla.status == SLAStatus.SUSPENDED.value:
                continue
            metrics = metrics_by_asset.get(sla.asset_id, {})
            result = self.check_sla(sla.id, metrics)
            results.append(result)
        return results

    @staticmethod
    def _evaluate_target(operator: str, actual: float, target: float) -> bool:
        """Evaluate whether a target is met."""
        if operator == ">=":
            return actual >= target
        elif operator == "<=":
            return actual <= target
        elif operator == ">":
            return actual > target
        elif operator == "<":
            return actual < target
        elif operator == "==":
            return abs(actual - target) < 1e-6
        return False

    @staticmethod
    def _compute_margin(operator: str, actual: float, target: float) -> float:
        """Compute how much margin exists (0 = at threshold, 1 = far from threshold)."""
        if target == 0:
            return 1.0 if actual == 0 else 0.5
        if operator in (">=", ">"):
            return max(0, (actual - target) / target)
        elif operator in ("<=", "<"):
            return max(0, (target - actual) / target) if target > 0 else 1.0
        return 0.5

    # -----------------------------------------
    # ALERTS
    # -----------------------------------------

    def get_alerts(
        self,
        sla_id: str = "",
        level: str = "",
        unacknowledged_only: bool = False,
    ) -> List[SLAAlert]:
        """Get SLA alerts."""
        results = list(self._alerts)
        if sla_id:
            results = [a for a in results if a.sla_id == sla_id]
        if level:
            results = [a for a in results if a.level == level]
        if unacknowledged_only:
            results = [a for a in results if not a.acknowledged]
        return results

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    # -----------------------------------------
    # HISTORY & STATS
    # -----------------------------------------

    def get_history(self, sla_id: str = "", limit: int = 50) -> List[SLAHistoryEntry]:
        """Get compliance history."""
        results = list(self._history)
        if sla_id:
            results = [h for h in results if h.sla_id == sla_id]
        return results[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get SLA engine statistics."""
        slas = list(self._slas.values())
        return {
            "total_slas": len(slas),
            "by_status": {
                s.value: sum(1 for sla in slas if sla.status == s.value)
                for s in SLAStatus
            },
            "total_alerts": len(self._alerts),
            "unacknowledged_alerts": sum(1 for a in self._alerts if not a.acknowledged),
            "total_checks": len(self._check_results),
            "compliance_summary": self._compute_compliance_summary(),
        }

    def _compute_compliance_summary(self) -> Dict[str, float]:
        """Compute compliance percentages per SLA."""
        summary = {}
        for sla in self._slas.values():
            history = [h for h in self._history if h.sla_id == sla.id]
            if history:
                avg = sum(h.compliance_pct for h in history) / len(history)
                summary[sla.id] = round(avg, 1)
            else:
                summary[sla.id] = 100.0
        return summary


# =========================================
# SINGLETON
# =========================================

_engine: Optional[SLAEngine] = None


def get_sla_engine() -> SLAEngine:
    global _engine
    if _engine is None:
        _engine = SLAEngine()
    return _engine
