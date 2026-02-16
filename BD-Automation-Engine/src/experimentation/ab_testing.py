"""Phase 55A — A/B Testing Framework.

Manages multi-variant experiments with weighted assignment, conversion
tracking, and statistical significance analysis using z-tests.
"""

from __future__ import annotations

import hashlib
import logging
import math
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================


class ExperimentStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    GRADUATED = "graduated"


@dataclass
class Variant:
    """A single variant (arm) in an A/B experiment."""

    variant_id: str
    name: str
    description: str = ""
    is_control: bool = False
    weight: float = 50.0  # 0-100
    assignments: int = 0
    conversions: int = 0
    revenue: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        conv_rate = self.conversions / max(self.assignments, 1)
        return {
            "variant_id": self.variant_id,
            "name": self.name,
            "description": self.description,
            "is_control": self.is_control,
            "weight": self.weight,
            "assignments": self.assignments,
            "conversions": self.conversions,
            "revenue": round(self.revenue, 2),
            "conversion_rate": round(conv_rate, 4),
        }


@dataclass
class Experiment:
    """An A/B experiment with multiple variants."""

    experiment_id: str
    name: str
    description: str = ""
    hypothesis: str = ""
    status: ExperimentStatus = ExperimentStatus.DRAFT
    variants: List[Variant] = field(default_factory=list)
    metric_name: str = "conversion_rate"
    min_sample_size: int = 100
    confidence_level: float = 0.95
    created_at: str = ""
    started_at: str = ""
    ended_at: str = ""
    # Internal: maps user_id → variant_id for sticky assignment
    _user_assignments: Dict[str, str] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "description": self.description,
            "hypothesis": self.hypothesis,
            "status": self.status.value,
            "variants": [v.to_dict() for v in self.variants],
            "metric_name": self.metric_name,
            "min_sample_size": self.min_sample_size,
            "confidence_level": self.confidence_level,
            "total_assignments": sum(v.assignments for v in self.variants),
            "total_conversions": sum(v.conversions for v in self.variants),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }


# =========================================
# A/B TESTING FRAMEWORK
# =========================================


class ABTestingFramework:
    """Manages A/B experiments with weighted random assignment,
    conversion tracking, and z-test statistical significance.

    Workflow:
    1. ``create_experiment`` with named variants and weights.
    2. ``start_experiment`` to begin accepting traffic.
    3. ``assign_user`` to deterministically bucket users into variants.
    4. ``record_conversion`` when a user converts.
    5. ``get_results`` to compute uplift and statistical significance.
    6. ``graduate_experiment`` to promote the winning variant.
    """

    def __init__(self):
        self._experiments: Dict[str, Experiment] = {}
        self._experiment_counter = 0
        logger.info("ABTestingFramework initialized")

    # ----- experiment CRUD -----

    def create_experiment(
        self,
        name: str,
        hypothesis: str = "",
        metric_name: str = "conversion_rate",
        variants: Optional[List[Dict[str, Any]]] = None,
        min_sample_size: int = 100,
        confidence_level: float = 0.95,
    ) -> Experiment:
        """Create a new A/B experiment.

        *variants* is a list of dicts, each with ``name`` and optional
        ``weight`` (default 50).  The first variant is marked as the
        control.
        """
        self._experiment_counter += 1
        exp_id = f"exp_{hashlib.md5(f'exp:{name}:{self._experiment_counter}:{time.time()}'.encode()).hexdigest()[:12]}"

        variant_objects: List[Variant] = []
        variant_defs = variants or [
            {"name": "control", "weight": 50},
            {"name": "treatment", "weight": 50},
        ]

        for idx, vdef in enumerate(variant_defs):
            vid = f"var_{hashlib.md5(f'{exp_id}:v:{idx}'.encode()).hexdigest()[:8]}"
            variant_objects.append(
                Variant(
                    variant_id=vid,
                    name=vdef.get("name", f"variant_{idx}"),
                    description=vdef.get("description", ""),
                    is_control=(idx == 0),
                    weight=vdef.get("weight", 50.0),
                )
            )

        experiment = Experiment(
            experiment_id=exp_id,
            name=name,
            hypothesis=hypothesis,
            metric_name=metric_name,
            variants=variant_objects,
            min_sample_size=min_sample_size,
            confidence_level=confidence_level,
        )
        self._experiments[exp_id] = experiment
        logger.info(
            "Created experiment %s (%s) with %d variants",
            exp_id,
            name,
            len(variant_objects),
        )
        return experiment

    def start_experiment(self, experiment_id: str) -> Experiment:
        """Transition experiment to RUNNING status."""
        exp = self._experiments.get(experiment_id)
        if not exp:
            raise ValueError(f"Experiment not found: {experiment_id}")
        exp.status = ExperimentStatus.RUNNING
        exp.started_at = datetime.utcnow().isoformat()
        logger.info("Started experiment %s", experiment_id)
        return exp

    def pause_experiment(self, experiment_id: str) -> Experiment:
        """Pause a running experiment."""
        exp = self._experiments.get(experiment_id)
        if not exp:
            raise ValueError(f"Experiment not found: {experiment_id}")
        exp.status = ExperimentStatus.PAUSED
        logger.info("Paused experiment %s", experiment_id)
        return exp

    def complete_experiment(self, experiment_id: str) -> Experiment:
        """Mark experiment as completed (no more assignments)."""
        exp = self._experiments.get(experiment_id)
        if not exp:
            raise ValueError(f"Experiment not found: {experiment_id}")
        exp.status = ExperimentStatus.COMPLETED
        exp.ended_at = datetime.utcnow().isoformat()
        logger.info("Completed experiment %s", experiment_id)
        return exp

    def graduate_experiment(self, experiment_id: str) -> Experiment:
        """Graduate the experiment — promote the winning variant.

        Marks the experiment as GRADUATED.  The winner is the variant
        with the highest conversion rate (excluding control).
        """
        exp = self._experiments.get(experiment_id)
        if not exp:
            raise ValueError(f"Experiment not found: {experiment_id}")

        exp.status = ExperimentStatus.GRADUATED
        exp.ended_at = exp.ended_at or datetime.utcnow().isoformat()

        # Identify winner
        best = None
        best_rate = -1.0
        for v in exp.variants:
            rate = v.conversions / max(v.assignments, 1)
            if rate > best_rate:
                best_rate = rate
                best = v

        if best:
            logger.info(
                "Graduated experiment %s — winner: %s (%.2f%% conversion)",
                experiment_id,
                best.name,
                best_rate * 100,
            )
        return exp

    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Return an experiment by ID or None."""
        return self._experiments.get(experiment_id)

    def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None,
    ) -> List[Experiment]:
        """List experiments with optional status filter."""
        experiments = list(self._experiments.values())
        if status is not None:
            experiments = [e for e in experiments if e.status == status]
        return experiments

    # ----- assignment and conversion -----

    def assign_user(self, experiment_id: str, user_id: str) -> str:
        """Assign a user to a variant using weighted random selection.

        Assignment is sticky: once a user is assigned, subsequent calls
        return the same variant.  Only assigns when experiment is RUNNING.

        Returns the variant_id the user was assigned to.
        """
        exp = self._experiments.get(experiment_id)
        if not exp:
            raise ValueError(f"Experiment not found: {experiment_id}")

        if exp.status != ExperimentStatus.RUNNING:
            raise ValueError(
                f"Experiment {experiment_id} is not running (status={exp.status.value})"
            )

        # Sticky assignment
        if user_id in exp._user_assignments:
            return exp._user_assignments[user_id]

        # Weighted random selection
        total_weight = sum(v.weight for v in exp.variants)
        if total_weight <= 0:
            raise ValueError("Total variant weight must be positive")

        # Deterministic: seed from experiment + user for reproducibility
        seed = int(
            hashlib.md5(f"{experiment_id}:{user_id}".encode()).hexdigest()[:8], 16
        )
        rng = random.Random(seed)
        roll = rng.uniform(0, total_weight)

        cumulative = 0.0
        chosen = exp.variants[-1]  # fallback
        for v in exp.variants:
            cumulative += v.weight
            if roll <= cumulative:
                chosen = v
                break

        chosen.assignments += 1
        exp._user_assignments[user_id] = chosen.variant_id
        logger.debug(
            "Assigned user %s to variant %s in experiment %s",
            user_id,
            chosen.name,
            experiment_id,
        )
        return chosen.variant_id

    def record_conversion(
        self,
        experiment_id: str,
        variant_id: str,
        value: float = 1.0,
    ) -> None:
        """Record a conversion event for a variant.

        *value* is an optional monetary or metric value associated with
        the conversion (defaults to 1.0).
        """
        exp = self._experiments.get(experiment_id)
        if not exp:
            raise ValueError(f"Experiment not found: {experiment_id}")

        for v in exp.variants:
            if v.variant_id == variant_id:
                v.conversions += 1
                v.revenue += value
                logger.debug(
                    "Recorded conversion for variant %s in experiment %s (value=%.2f)",
                    variant_id,
                    experiment_id,
                    value,
                )
                return

        raise ValueError(
            f"Variant {variant_id} not found in experiment {experiment_id}"
        )

    # ----- results and statistics -----

    def get_results(self, experiment_id: str) -> Dict[str, Any]:
        """Compute experiment results including conversion rates, uplift,
        and statistical significance using a two-proportion z-test.

        Returns a dict with per-variant metrics, pairwise comparisons
        against the control, and an overall recommendation.
        """
        exp = self._experiments.get(experiment_id)
        if not exp:
            raise ValueError(f"Experiment not found: {experiment_id}")

        # Find control variant
        control = None
        for v in exp.variants:
            if v.is_control:
                control = v
                break
        if not control:
            control = exp.variants[0] if exp.variants else None

        variant_results = []
        comparisons = []

        control_rate = (
            control.conversions / max(control.assignments, 1) if control else 0.0
        )

        for v in exp.variants:
            rate = v.conversions / max(v.assignments, 1)
            variant_results.append(
                {
                    "variant_id": v.variant_id,
                    "name": v.name,
                    "is_control": v.is_control,
                    "assignments": v.assignments,
                    "conversions": v.conversions,
                    "conversion_rate": round(rate, 4),
                    "revenue": round(v.revenue, 2),
                    "revenue_per_user": round(v.revenue / max(v.assignments, 1), 2),
                }
            )

            # Compare non-control variants against control
            if not v.is_control and control:
                uplift = (rate - control_rate) / max(control_rate, 0.0001)
                z_score, p_value = self._z_test(
                    control.conversions,
                    control.assignments,
                    v.conversions,
                    v.assignments,
                )
                significant = p_value < (1.0 - exp.confidence_level)

                comparisons.append(
                    {
                        "variant": v.name,
                        "variant_id": v.variant_id,
                        "control_rate": round(control_rate, 4),
                        "variant_rate": round(rate, 4),
                        "uplift": round(uplift, 4),
                        "uplift_pct": round(uplift * 100, 2),
                        "z_score": round(z_score, 4),
                        "p_value": round(p_value, 4),
                        "significant": significant,
                        "confidence_level": exp.confidence_level,
                    }
                )

        # Overall recommendation
        has_enough_data = all(
            v.assignments >= exp.min_sample_size for v in exp.variants
        )
        significant_winners = [
            c for c in comparisons if c["significant"] and c["uplift"] > 0
        ]

        if not has_enough_data:
            recommendation = "Insufficient sample size — continue collecting data"
        elif significant_winners:
            best = max(significant_winners, key=lambda c: c["uplift"])
            recommendation = f"Variant '{best['variant']}' shows {best['uplift_pct']}% uplift with p={best['p_value']} — consider graduating"
        else:
            recommendation = "No statistically significant winner — consider extending the experiment"

        return {
            "experiment_id": exp.experiment_id,
            "name": exp.name,
            "status": exp.status.value,
            "metric_name": exp.metric_name,
            "variants": variant_results,
            "comparisons": comparisons,
            "has_enough_data": has_enough_data,
            "recommendation": recommendation,
        }

    @staticmethod
    def _z_test(
        c_conversions: int,
        c_trials: int,
        t_conversions: int,
        t_trials: int,
    ) -> tuple:
        """Two-proportion z-test.

        Returns (z_score, p_value).
        """
        if c_trials == 0 or t_trials == 0:
            return (0.0, 1.0)

        p_c = c_conversions / c_trials
        p_t = t_conversions / t_trials
        p_pool = (c_conversions + t_conversions) / (c_trials + t_trials)

        se = math.sqrt(p_pool * (1 - p_pool) * (1.0 / c_trials + 1.0 / t_trials))
        if se == 0:
            return (0.0, 1.0)

        z = (p_t - p_c) / se
        # Two-tailed p-value from z-score
        p_value = 2.0 * (1.0 - ABTestingFramework._normal_cdf(abs(z)))
        return (z, p_value)

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Approximate CDF of the standard normal distribution."""
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        """Return summary statistics about all experiments."""
        experiments = list(self._experiments.values())
        return {
            "total_experiments": len(experiments),
            "by_status": {
                s.value: sum(1 for e in experiments if e.status == s)
                for s in ExperimentStatus
            },
            "total_assignments": sum(
                sum(v.assignments for v in e.variants) for e in experiments
            ),
            "total_conversions": sum(
                sum(v.conversions for v in e.variants) for e in experiments
            ),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[ABTestingFramework] = None


def get_ab_framework() -> ABTestingFramework:
    global _instance
    if _instance is None:
        _instance = ABTestingFramework()
    return _instance
