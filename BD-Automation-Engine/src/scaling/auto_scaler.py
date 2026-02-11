"""Phase 57A — Auto Scaler.

Policy-based auto-scaling with cooldown, scaling history,
and optimization recommendations.
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

class ScalingDirection(Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NO_CHANGE = "no_change"


@dataclass
class ScalingPolicy:
    policy_id: str
    name: str
    metric_name: str
    scale_up_threshold: float
    scale_down_threshold: float
    min_replicas: int = 1
    max_replicas: int = 10
    current_replicas: int = 2
    cooldown_seconds: float = 300.0
    last_scaled_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "metric_name": self.metric_name,
            "scale_up_threshold": self.scale_up_threshold,
            "scale_down_threshold": self.scale_down_threshold,
            "min_replicas": self.min_replicas,
            "max_replicas": self.max_replicas,
            "current_replicas": self.current_replicas,
            "cooldown_seconds": self.cooldown_seconds,
            "last_scaled_at": self.last_scaled_at,
        }


@dataclass
class ScalingEvent:
    event_id: str
    policy_id: str
    direction: ScalingDirection
    from_replicas: int
    to_replicas: int
    reason: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "policy_id": self.policy_id,
            "direction": self.direction.value,
            "from_replicas": self.from_replicas,
            "to_replicas": self.to_replicas,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


# =========================================
# AUTO SCALER
# =========================================

class AutoScaler:
    """Policy-based auto-scaler with cooldown periods,
    scaling history, and optimization recommendations.
    """

    def __init__(self):
        self._policies: Dict[str, ScalingPolicy] = {}
        self._history: List[ScalingEvent] = []
        self._register_defaults()
        logger.info("AutoScaler initialized with %d policies", len(self._policies))

    def _register_defaults(self) -> None:
        defaults = [
            ScalingPolicy(
                policy_id="api_cpu", name="API CPU Utilization",
                metric_name="cpu_utilization",
                scale_up_threshold=80, scale_down_threshold=30,
                min_replicas=2, max_replicas=10, current_replicas=3,
                cooldown_seconds=300,
            ),
            ScalingPolicy(
                policy_id="search_latency", name="Search P99 Latency",
                metric_name="search_p99_ms",
                scale_up_threshold=500, scale_down_threshold=100,
                min_replicas=1, max_replicas=8, current_replicas=2,
                cooldown_seconds=300,
            ),
            ScalingPolicy(
                policy_id="agent_queue", name="Agent Queue Depth",
                metric_name="queue_depth",
                scale_up_threshold=100, scale_down_threshold=10,
                min_replicas=1, max_replicas=12, current_replicas=2,
                cooldown_seconds=300,
            ),
            ScalingPolicy(
                policy_id="pipeline_throughput", name="Pipeline Throughput",
                metric_name="messages_per_sec",
                scale_up_threshold=1000, scale_down_threshold=200,
                min_replicas=1, max_replicas=6, current_replicas=2,
                cooldown_seconds=300,
            ),
        ]
        for p in defaults:
            self._policies[p.policy_id] = p

    # ----- evaluate -----

    def evaluate(self, policy_id: str, current_value: float) -> Optional[ScalingEvent]:
        """Evaluate a metric against a scaling policy."""
        policy = self._policies.get(policy_id)
        if not policy:
            return None

        now = time.time()
        from_replicas = policy.current_replicas

        # Check cooldown
        if policy.last_scaled_at > 0 and (now - policy.last_scaled_at) < policy.cooldown_seconds:
            event = ScalingEvent(
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                policy_id=policy_id,
                direction=ScalingDirection.NO_CHANGE,
                from_replicas=from_replicas,
                to_replicas=from_replicas,
                reason="Cooldown period active",
            )
            self._history.append(event)
            return event

        direction = ScalingDirection.NO_CHANGE
        to_replicas = from_replicas
        reason = ""

        if current_value >= policy.scale_up_threshold:
            if from_replicas < policy.max_replicas:
                to_replicas = from_replicas + 1
                direction = ScalingDirection.SCALE_UP
                reason = f"{policy.metric_name}={current_value} >= {policy.scale_up_threshold}"
            else:
                reason = f"Already at max replicas ({policy.max_replicas})"
        elif current_value <= policy.scale_down_threshold:
            if from_replicas > policy.min_replicas:
                to_replicas = from_replicas - 1
                direction = ScalingDirection.SCALE_DOWN
                reason = f"{policy.metric_name}={current_value} <= {policy.scale_down_threshold}"
            else:
                reason = f"Already at min replicas ({policy.min_replicas})"
        else:
            reason = f"{policy.metric_name}={current_value} within normal range"

        if direction != ScalingDirection.NO_CHANGE:
            policy.current_replicas = to_replicas
            policy.last_scaled_at = now
            logger.info("Scaling %s: %d -> %d (%s)", policy_id, from_replicas, to_replicas, reason)

        event = ScalingEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            policy_id=policy_id,
            direction=direction,
            from_replicas=from_replicas,
            to_replicas=to_replicas,
            reason=reason,
        )
        self._history.append(event)
        return event

    # ----- queries -----

    def get_policy(self, policy_id: str) -> Optional[ScalingPolicy]:
        return self._policies.get(policy_id)

    def list_policies(self) -> List[ScalingPolicy]:
        return list(self._policies.values())

    def update_policy(self, policy_id: str, **kwargs: Any) -> Optional[ScalingPolicy]:
        policy = self._policies.get(policy_id)
        if not policy:
            return None
        for key, value in kwargs.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        return policy

    def get_scaling_history(self, policy_id: Optional[str] = None, limit: int = 50) -> List[ScalingEvent]:
        events = self._history
        if policy_id:
            events = [e for e in events if e.policy_id == policy_id]
        return events[-limit:]

    # ----- recommendations -----

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Analyze current state and suggest optimizations."""
        recs = []
        for policy in self._policies.values():
            utilization = policy.current_replicas / policy.max_replicas
            if utilization > 0.8:
                recs.append({
                    "policy_id": policy.policy_id,
                    "type": "increase_max",
                    "message": f"{policy.name}: running at {utilization:.0%} of max capacity, consider increasing max_replicas",
                })
            if policy.current_replicas == policy.min_replicas:
                recs.append({
                    "policy_id": policy.policy_id,
                    "type": "at_minimum",
                    "message": f"{policy.name}: running at minimum replicas ({policy.min_replicas})",
                })
        return recs

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        total_replicas = sum(p.current_replicas for p in self._policies.values())
        scale_ups = sum(1 for e in self._history if e.direction == ScalingDirection.SCALE_UP)
        scale_downs = sum(1 for e in self._history if e.direction == ScalingDirection.SCALE_DOWN)
        return {
            "total_policies": len(self._policies),
            "total_replicas": total_replicas,
            "total_events": len(self._history),
            "scale_ups": scale_ups,
            "scale_downs": scale_downs,
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[AutoScaler] = None


def get_auto_scaler() -> AutoScaler:
    global _instance
    if _instance is None:
        _instance = AutoScaler()
    return _instance
