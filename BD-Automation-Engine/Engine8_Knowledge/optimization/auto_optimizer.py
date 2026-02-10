"""Phase 29A — Auto-Optimizer"""
import structlog
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
logger = structlog.get_logger(__name__)

@dataclass
class Optimization:
    opt_id: str
    category: str  # create_index, adjust_cache_ttl, rewrite_query, etc.
    description: str
    expected_impact: str
    risk_level: str  # safe, approval_required
    parameters: Dict = field(default_factory=dict)
    status: str = "pending"  # pending, approved, applied, rolled_back, rejected

@dataclass
class ApplyResult:
    opt_id: str
    success: bool
    message: str
    applied_at: str = ""
    rollback_data: Dict = field(default_factory=dict)

SAFE_CATEGORIES = [
    "create_index", "adjust_cache_ttl", "rewrite_query",
    "adjust_threshold", "cleanup_expired", "rebalance_vectors",
]

APPROVAL_REQUIRED = [
    "retrain_model", "modify_schema", "change_workflow", "update_scoring",
]

class AutoOptimizer:
    def __init__(self, storage_path: str = None):
        self._optimizations: List[Optimization] = []
        self._applied: List[ApplyResult] = []
        self._storage_path = storage_path
        self._load()

    def _load(self):
        if self._storage_path:
            try:
                import os
                path = os.path.join(self._storage_path, "optimizations.json")
                if os.path.exists(path):
                    with open(path) as f:
                        data = json.load(f)
                    self._optimizations = [Optimization(**o) for o in data.get("optimizations", [])]
                    self._applied = [ApplyResult(**a) for a in data.get("applied", [])]
            except Exception:
                pass

    def _save(self):
        if self._storage_path:
            try:
                import os
                os.makedirs(self._storage_path, exist_ok=True)
                from dataclasses import asdict
                path = os.path.join(self._storage_path, "optimizations.json")
                with open(path, "w") as f:
                    json.dump({
                        "optimizations": [asdict(o) for o in self._optimizations],
                        "applied": [asdict(a) for a in self._applied],
                    }, f)
            except Exception:
                pass

    async def generate_recommendations(self, assessment) -> List[Optimization]:
        recommendations = []
        opt_counter = len(self._optimizations)

        for sub in assessment.subsystems:
            if sub.status == "red":
                if sub.name == "api_latency":
                    opt_counter += 1
                    recommendations.append(Optimization(
                        opt_id=f"opt_{opt_counter:04d}", category="create_index",
                        description=f"Add database index to reduce {sub.name} latency",
                        expected_impact="Reduce p95 latency by ~30%",
                        risk_level="safe",
                        parameters={"subsystem": sub.name, "target": "p95_ms"},
                    ))
                elif sub.name == "data_freshness":
                    opt_counter += 1
                    recommendations.append(Optimization(
                        opt_id=f"opt_{opt_counter:04d}", category="adjust_threshold",
                        description="Increase scrape frequency for stale sources",
                        expected_impact="Reduce staleness from >48h to <24h",
                        risk_level="safe",
                        parameters={"subsystem": sub.name},
                    ))
                elif sub.name == "model_accuracy":
                    opt_counter += 1
                    recommendations.append(Optimization(
                        opt_id=f"opt_{opt_counter:04d}", category="retrain_model",
                        description="Retrain models with fresh data",
                        expected_impact="Improve model accuracy by ~5-10%",
                        risk_level="approval_required",
                        parameters={"subsystem": sub.name},
                    ))

            if sub.status == "yellow":
                if sub.name == "memory_health":
                    opt_counter += 1
                    recommendations.append(Optimization(
                        opt_id=f"opt_{opt_counter:04d}", category="cleanup_expired",
                        description="Clean up expired short-term memories",
                        expected_impact="Improve memory hit rate by ~10%",
                        risk_level="safe",
                        parameters={"subsystem": sub.name},
                    ))
                elif sub.name == "search_quality":
                    opt_counter += 1
                    recommendations.append(Optimization(
                        opt_id=f"opt_{opt_counter:04d}", category="rebalance_vectors",
                        description="Rebalance Qdrant collection shards",
                        expected_impact="Improve search relevance by ~5%",
                        risk_level="safe",
                        parameters={"subsystem": sub.name},
                    ))

        self._optimizations.extend(recommendations)
        self._save()
        return recommendations

    async def auto_apply(self, optimization: Optimization) -> ApplyResult:
        if optimization.risk_level != "safe":
            return ApplyResult(opt_id=optimization.opt_id, success=False,
                             message="Requires approval for non-safe optimizations")

        if optimization.category not in SAFE_CATEGORIES:
            return ApplyResult(opt_id=optimization.opt_id, success=False,
                             message=f"Unknown safe category: {optimization.category}")

        logger.info("applying_optimization", opt_id=optimization.opt_id,
                    category=optimization.category)

        # Simulated application
        optimization.status = "applied"
        result = ApplyResult(
            opt_id=optimization.opt_id, success=True,
            message=f"Applied {optimization.category}: {optimization.description}",
            applied_at=datetime.utcnow().isoformat(),
            rollback_data={"category": optimization.category, "params": optimization.parameters},
        )
        self._applied.append(result)
        self._save()
        return result

    async def request_approval(self, optimization: Optimization) -> str:
        optimization.status = "pending_approval"
        self._save()
        return optimization.opt_id

    async def approve(self, opt_id: str) -> ApplyResult:
        for opt in self._optimizations:
            if opt.opt_id == opt_id:
                opt.status = "approved"
                return await self.auto_apply(opt)
        return ApplyResult(opt_id=opt_id, success=False, message="Optimization not found")

    async def get_applied_history(self) -> List[ApplyResult]:
        return list(self._applied)

    async def rollback(self, opt_id: str) -> bool:
        for opt in self._optimizations:
            if opt.opt_id == opt_id and opt.status == "applied":
                opt.status = "rolled_back"
                logger.info("optimization_rolled_back", opt_id=opt_id)
                self._save()
                return True
        return False

    def get_optimization(self, opt_id: str) -> Optional[Optimization]:
        for opt in self._optimizations:
            if opt.opt_id == opt_id:
                return opt
        return None

_optimizer = None
def get_auto_optimizer():
    global _optimizer
    if _optimizer is None:
        _optimizer = AutoOptimizer()
    return _optimizer
