"""Phase 55A — Experiment Analytics.

Tracks granular events across experiments and provides funnel analysis,
time-series breakdowns, segment analysis, and sample-size calculators.
"""

from __future__ import annotations

import hashlib
import logging
import math
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================

@dataclass
class AnalyticsEvent:
    """A single analytics event tied to an experiment."""
    event_id: str
    experiment_id: str
    variant_id: str
    user_id: str
    event_type: str  # e.g. "view", "click", "conversion", "purchase"
    value: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "experiment_id": self.experiment_id,
            "variant_id": self.variant_id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "value": self.value,
            "timestamp": self.timestamp,
        }


@dataclass
class FunnelStep:
    """A single step in a conversion funnel."""
    step_name: str
    count: int = 0
    conversion_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "count": self.count,
            "conversion_rate": round(self.conversion_rate, 4),
        }


# =========================================
# EXPERIMENT ANALYTICS
# =========================================

class ExperimentAnalytics:
    """Tracks events and provides analytical views over experiment data.

    Capabilities:
    - Event tracking for every user interaction within an experiment.
    - Conversion funnel construction across predefined step sequences.
    - Time-series aggregation of metrics per experiment.
    - Segment-based analysis to compare conversion rates across user
      segments.
    - Sample-size calculator for experiment planning.
    """

    # Default funnel step ordering
    FUNNEL_STEPS = ["view", "click", "engage", "convert", "purchase"]

    def __init__(self):
        self._events: List[AnalyticsEvent] = []
        self._event_counter = 0
        logger.info("ExperimentAnalytics initialized")

    # ----- event tracking -----

    def track_event(
        self,
        experiment_id: str,
        variant_id: str,
        user_id: str,
        event_type: str,
        value: float = 0.0,
    ) -> AnalyticsEvent:
        """Record a single analytics event.

        Parameters
        ----------
        experiment_id : str
            The experiment this event belongs to.
        variant_id : str
            The variant the user was assigned to.
        user_id : str
            The user who triggered the event.
        event_type : str
            The type of event (e.g. ``"view"``, ``"click"``, ``"conversion"``).
        value : float
            Optional numeric value (e.g. revenue).

        Returns
        -------
        AnalyticsEvent
            The recorded event.
        """
        self._event_counter += 1
        event_id = f"evt_{hashlib.md5(f'evt:{self._event_counter}:{time.time()}'.encode()).hexdigest()[:12]}"

        event = AnalyticsEvent(
            event_id=event_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
            user_id=user_id,
            event_type=event_type,
            value=value,
        )
        self._events.append(event)
        logger.debug("Tracked event %s: %s for experiment %s, variant %s",
                      event_id, event_type, experiment_id, variant_id)
        return event

    # ----- funnel analysis -----

    def get_funnel(self, experiment_id: str) -> List[FunnelStep]:
        """Build a conversion funnel for the given experiment.

        Uses the predefined ``FUNNEL_STEPS`` ordering.  For each step,
        counts the number of unique users who reached that step.
        Conversion rate is calculated relative to the first step.

        Returns
        -------
        List[FunnelStep]
            Ordered funnel steps with counts and conversion rates.
        """
        exp_events = [e for e in self._events if e.experiment_id == experiment_id]

        # Unique users per event type
        users_per_type: Dict[str, set] = defaultdict(set)
        for evt in exp_events:
            users_per_type[evt.event_type].add(evt.user_id)

        funnel: List[FunnelStep] = []
        top_count = 0

        for step_name in self.FUNNEL_STEPS:
            count = len(users_per_type.get(step_name, set()))
            if not funnel:
                top_count = max(count, 1)  # avoid division by zero
            conversion_rate = count / top_count
            funnel.append(FunnelStep(
                step_name=step_name,
                count=count,
                conversion_rate=conversion_rate,
            ))

        return funnel

    # ----- time series -----

    def get_time_series(
        self,
        experiment_id: str,
        metric_name: str = "conversion",
    ) -> List[Dict[str, Any]]:
        """Aggregate events into a daily time series.

        Groups events for *experiment_id* by date and returns one data
        point per day with the count of events matching *metric_name*
        and the sum of their values.

        Returns
        -------
        List[Dict[str, Any]]
            Sorted list of ``{"date", "count", "value"}`` dicts.
        """
        exp_events = [
            e for e in self._events
            if e.experiment_id == experiment_id and e.event_type == metric_name
        ]

        daily: Dict[str, Dict[str, Any]] = {}
        for evt in exp_events:
            # Extract date portion (YYYY-MM-DD)
            date_key = evt.timestamp[:10] if len(evt.timestamp) >= 10 else evt.timestamp
            if date_key not in daily:
                daily[date_key] = {"date": date_key, "count": 0, "value": 0.0}
            daily[date_key]["count"] += 1
            daily[date_key]["value"] += evt.value

        # Sort by date
        result = sorted(daily.values(), key=lambda d: d["date"])
        for point in result:
            point["value"] = round(point["value"], 2)
        return result

    # ----- segment analysis -----

    def get_segment_analysis(
        self,
        experiment_id: str,
        segment_by: str = "variant_id",
    ) -> Dict[str, float]:
        """Compute conversion rates segmented by a given field.

        Groups events for the experiment by the *segment_by* attribute
        (e.g. ``"variant_id"`` or ``"user_id"``).  For each segment,
        computes the ratio of ``"convert"`` events to total events.

        Parameters
        ----------
        experiment_id : str
            Target experiment.
        segment_by : str
            Event attribute to segment on.  Must be one of
            ``"variant_id"``, ``"user_id"``, or ``"event_type"``.

        Returns
        -------
        Dict[str, float]
            Mapping of segment value to conversion rate.
        """
        exp_events = [e for e in self._events if e.experiment_id == experiment_id]

        segment_totals: Dict[str, int] = defaultdict(int)
        segment_conversions: Dict[str, int] = defaultdict(int)

        for evt in exp_events:
            key = getattr(evt, segment_by, "unknown")
            segment_totals[key] += 1
            if evt.event_type in ("convert", "conversion", "purchase"):
                segment_conversions[key] += 1

        result: Dict[str, float] = {}
        for seg_key, total in segment_totals.items():
            conversions = segment_conversions.get(seg_key, 0)
            result[seg_key] = round(conversions / max(total, 1), 4)

        return result

    # ----- sample size calculator -----

    def compute_sample_size_needed(
        self,
        baseline_rate: float,
        min_detectable_effect: float,
        significance: float = 0.05,
        power: float = 0.8,
    ) -> int:
        """Compute the per-variant sample size needed for an experiment.

        Uses the standard formula for a two-proportion z-test:

        .. math::

            n = \\frac{(Z_{\\alpha/2} + Z_{\\beta})^2
                       (p_1 (1 - p_1) + p_2 (1 - p_2))}
                      {(p_2 - p_1)^2}

        Parameters
        ----------
        baseline_rate : float
            Expected conversion rate of the control (e.g. 0.10 for 10%).
        min_detectable_effect : float
            Minimum relative improvement to detect (e.g. 0.05 for 5%
            absolute lift).
        significance : float
            Type I error rate (default 0.05).
        power : float
            Desired statistical power (default 0.80).

        Returns
        -------
        int
            Required sample size per variant.
        """
        p1 = baseline_rate
        p2 = baseline_rate + min_detectable_effect

        if p1 <= 0 or p1 >= 1 or p2 <= 0 or p2 >= 1:
            logger.warning("Invalid rates for sample size calculation: p1=%s p2=%s", p1, p2)
            return 0

        z_alpha = self._z_score(1.0 - significance / 2.0)
        z_beta = self._z_score(power)

        numerator = (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
        denominator = (p2 - p1) ** 2

        if denominator == 0:
            return 0

        n = math.ceil(numerator / denominator)
        logger.info(
            "Sample size needed: %d per variant (baseline=%.2f%%, MDE=%.2f%%, "
            "alpha=%.2f, power=%.2f)",
            n, p1 * 100, min_detectable_effect * 100, significance, power,
        )
        return n

    @staticmethod
    def _z_score(quantile: float) -> float:
        """Approximate the z-score for a given quantile using the inverse
        of the normal CDF (Beasley-Springer-Moro approximation).

        Good enough for quantiles in [0.01, 0.99].
        """
        # Rational approximation (Abramowitz and Stegun 26.2.23)
        if quantile <= 0.0 or quantile >= 1.0:
            return 0.0
        if quantile == 0.5:
            return 0.0

        if quantile > 0.5:
            sign = 1.0
            q = 1.0 - quantile
        else:
            sign = -1.0
            q = quantile

        t = math.sqrt(-2.0 * math.log(q))
        # Coefficients for rational approximation
        c0 = 2.515517
        c1 = 0.802853
        c2 = 0.010328
        d1 = 1.432788
        d2 = 0.189269
        d3 = 0.001308

        z = t - (c0 + c1 * t + c2 * t * t) / (1.0 + d1 * t + d2 * t * t + d3 * t * t * t)
        return sign * z

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        """Return summary statistics about tracked events."""
        exp_ids = set(e.experiment_id for e in self._events)
        event_types: Dict[str, int] = defaultdict(int)
        for evt in self._events:
            event_types[evt.event_type] += 1

        return {
            "total_events": len(self._events),
            "unique_experiments": len(exp_ids),
            "event_types": dict(event_types),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[ExperimentAnalytics] = None


def get_experiment_analytics() -> ExperimentAnalytics:
    global _instance
    if _instance is None:
        _instance = ExperimentAnalytics()
    return _instance
