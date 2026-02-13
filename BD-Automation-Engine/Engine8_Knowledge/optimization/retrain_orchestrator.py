"""Phase 29A — Auto-Retrain Orchestrator"""
import structlog
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime
import json
logger = structlog.get_logger(__name__)

@dataclass
class ModelDriftReport:
    model_name: str
    current_metric: float
    baseline_metric: float
    drift_pct: float
    needs_retrain: bool
    last_trained: str = ""
    last_checked: str = ""

@dataclass
class RetrainResult:
    model_name: str
    success: bool
    old_metric: float = 0.0
    new_metric: float = 0.0
    improvement: float = 0.0
    duration_seconds: float = 0.0
    status: str = "completed"  # completed, failed, pending_approval, rejected

REGISTERED_MODELS = {
    "defense_ner": {"metric": "f1", "baseline": 0.78, "threshold": 0.05},
    "placement_predictor": {"metric": "auc", "baseline": 0.82, "threshold": 0.05},
    "topic_modeler": {"metric": "coherence", "baseline": 0.65, "threshold": 0.10},
    "domain_adapter": {"metric": "mrr", "baseline": 0.75, "threshold": 0.05},
    "response_predictor": {"metric": "accuracy", "baseline": 0.70, "threshold": 0.05},
}

class RetrainOrchestrator:
    def __init__(self, storage_path: str = None):
        self._models = dict(REGISTERED_MODELS)
        self._retrain_history: List[RetrainResult] = []
        self._storage_path = storage_path
        self._load()

    def _load(self):
        if self._storage_path:
            try:
                import os
                path = os.path.join(self._storage_path, "retrain_history.json")
                if os.path.exists(path):
                    with open(path) as f:
                        data = json.load(f)
                    self._retrain_history = [RetrainResult(**r) for r in data]
            except Exception:
                pass

    def _save(self):
        if self._storage_path:
            try:
                import os
                os.makedirs(self._storage_path, exist_ok=True)
                from dataclasses import asdict
                path = os.path.join(self._storage_path, "retrain_history.json")
                with open(path, "w") as f:
                    json.dump([asdict(r) for r in self._retrain_history], f)
            except Exception:
                pass

    async def check_all_models(self) -> List[ModelDriftReport]:
        reports = []
        for name, config in self._models.items():
            baseline = config["baseline"]
            # Simulated current metric (in production: query actual model)
            current = baseline * 0.97  # Simulate slight degradation
            drift = (baseline - current) / baseline if baseline > 0 else 0.0
            reports.append(ModelDriftReport(
                model_name=name,
                current_metric=current,
                baseline_metric=baseline,
                drift_pct=drift,
                needs_retrain=drift > config["threshold"],
                last_checked=datetime.utcnow().isoformat(),
            ))
        return reports

    async def orchestrate_retrain(self, model_name: str) -> RetrainResult:
        if model_name not in self._models:
            return RetrainResult(model_name=model_name, success=False, status="failed")

        config = self._models[model_name]
        logger.info("retrain_start", model=model_name)

        # Simulated retraining
        old_metric = config["baseline"] * 0.95
        new_metric = config["baseline"] * 1.02  # Simulate improvement
        improvement = (new_metric - old_metric) / old_metric if old_metric > 0 else 0.0

        result = RetrainResult(
            model_name=model_name,
            success=True,
            old_metric=old_metric,
            new_metric=new_metric,
            improvement=improvement,
            duration_seconds=5.0,
            status="completed",
        )

        self._retrain_history.append(result)
        self._save()
        return result

    async def schedule_retrains(self) -> List[str]:
        drift_reports = await self.check_all_models()
        scheduled = []
        for report in drift_reports:
            if report.needs_retrain:
                scheduled.append(report.model_name)
        return scheduled

    async def get_retrain_history(self, model_name: str = None) -> List[RetrainResult]:
        if model_name:
            return [r for r in self._retrain_history if r.model_name == model_name]
        return list(self._retrain_history)

    def get_registered_models(self) -> Dict:
        return dict(self._models)

_orchestrator = None
def get_retrain_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = RetrainOrchestrator()
    return _orchestrator
