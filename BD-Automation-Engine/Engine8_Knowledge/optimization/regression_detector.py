"""Phase 29A — Regression Detector"""

import structlog
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime
import json

logger = structlog.get_logger(__name__)


@dataclass
class Regression:
    regression_id: str
    metric: str
    severity: str  # warning, critical
    current_value: float
    baseline_value: float
    change_pct: float
    detected_at: str = ""
    caused_by: str = ""  # opt_id or "unknown"
    status: str = "active"  # active, resolved, rolled_back


@dataclass
class RollbackResult:
    regression_id: str
    success: bool
    message: str
    rolled_back_optimization: str = ""


@dataclass
class ThresholdConfig:
    metric: str
    warning_threshold: float = 0.10  # 10% degradation
    critical_threshold: float = 0.25  # 25% degradation


class RegressionDetector:
    def __init__(self, storage_path: str = None):
        self._regressions: List[Regression] = []
        self._thresholds: Dict[str, ThresholdConfig] = {}
        self._storage_path = storage_path
        self._baselines: Dict[str, float] = {}
        self._load()

    def _load(self):
        if self._storage_path:
            try:
                import os

                path = os.path.join(self._storage_path, "regressions.json")
                if os.path.exists(path):
                    with open(path) as f:
                        data = json.load(f)
                    self._regressions = [
                        Regression(**r) for r in data.get("regressions", [])
                    ]
                    self._baselines = data.get("baselines", {})
            except Exception:
                pass

    def _save(self):
        if self._storage_path:
            try:
                import os

                os.makedirs(self._storage_path, exist_ok=True)
                from dataclasses import asdict

                path = os.path.join(self._storage_path, "regressions.json")
                with open(path, "w") as f:
                    json.dump(
                        {
                            "regressions": [asdict(r) for r in self._regressions],
                            "baselines": self._baselines,
                        },
                        f,
                    )
            except Exception:
                pass

    def set_baseline(self, metric: str, value: float):
        self._baselines[metric] = value
        self._save()

    async def check_regressions(
        self, current_metrics: Dict[str, float] = None
    ) -> List[Regression]:
        if not current_metrics:
            current_metrics = {}

        new_regressions = []
        counter = len(self._regressions)

        for metric, current in current_metrics.items():
            baseline = self._baselines.get(metric)
            if baseline is None or baseline == 0:
                continue

            change_pct = (current - baseline) / abs(baseline)
            threshold = self._thresholds.get(metric, ThresholdConfig(metric=metric))

            severity = None
            if change_pct <= -threshold.critical_threshold:
                severity = "critical"
            elif change_pct <= -threshold.warning_threshold:
                severity = "warning"

            if severity:
                counter += 1
                reg = Regression(
                    regression_id=f"reg_{counter:04d}",
                    metric=metric,
                    severity=severity,
                    current_value=current,
                    baseline_value=baseline,
                    change_pct=change_pct,
                    detected_at=datetime.utcnow().isoformat(),
                )
                new_regressions.append(reg)
                self._regressions.append(reg)

        if new_regressions:
            self._save()
        return new_regressions

    async def auto_rollback(
        self, regression: Regression, optimizer=None
    ) -> RollbackResult:
        if regression.caused_by and regression.caused_by != "unknown" and optimizer:
            success = await optimizer.rollback(regression.caused_by)
            if success:
                regression.status = "rolled_back"
                self._save()
                return RollbackResult(
                    regression_id=regression.regression_id,
                    success=True,
                    message=f"Rolled back optimization {regression.caused_by}",
                    rolled_back_optimization=regression.caused_by,
                )

        return RollbackResult(
            regression_id=regression.regression_id,
            success=False,
            message="No associated optimization to rollback or rollback failed",
        )

    async def get_regression_history(self) -> List[Regression]:
        return list(self._regressions)

    async def get_active_regressions(self) -> List[Regression]:
        return [r for r in self._regressions if r.status == "active"]

    async def configure_thresholds(
        self, metric: str, warning: float = 0.10, critical: float = 0.25
    ):
        self._thresholds[metric] = ThresholdConfig(
            metric=metric, warning_threshold=warning, critical_threshold=critical
        )

    async def resolve(self, regression_id: str) -> bool:
        for r in self._regressions:
            if r.regression_id == regression_id:
                r.status = "resolved"
                self._save()
                return True
        return False


_detector = None


def get_regression_detector():
    global _detector
    if _detector is None:
        _detector = RegressionDetector()
    return _detector
