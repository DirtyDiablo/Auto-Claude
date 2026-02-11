"""Phase 54A — Circuit Breaker Registry.

Implements the circuit-breaker pattern for service calls.  Each breaker
tracks failures, trips to OPEN when a threshold is exceeded, and
transitions through HALF_OPEN to CLOSED upon recovery.  Pre-registers
breakers for the six core BD-engine services.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """A single circuit breaker protecting a service call."""
    name: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    failure_threshold: int = 5
    recovery_timeout_sec: float = 30.0
    half_open_max_calls: int = 3
    last_failure_time: float = 0.0
    last_state_change: str = ""
    total_trips: int = 0

    def __post_init__(self):
        if not self.last_state_change:
            self.last_state_change = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_sec": self.recovery_timeout_sec,
            "half_open_max_calls": self.half_open_max_calls,
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change,
            "total_trips": self.total_trips,
        }


# =========================================
# PRE-REGISTERED BREAKERS
# =========================================

_DEFAULT_BREAKERS = [
    {"name": "qdrant_search", "failure_threshold": 5, "recovery_timeout_sec": 30},
    {"name": "api_gateway", "failure_threshold": 5, "recovery_timeout_sec": 30},
    {"name": "notification_service", "failure_threshold": 5, "recovery_timeout_sec": 30},
    {"name": "n8n_workflow", "failure_threshold": 5, "recovery_timeout_sec": 30},
    {"name": "agent_executor", "failure_threshold": 5, "recovery_timeout_sec": 30},
    {"name": "bullhorn_etl", "failure_threshold": 5, "recovery_timeout_sec": 30},
]


# =========================================
# CIRCUIT BREAKER REGISTRY
# =========================================

class CircuitBreakerRegistry:
    """Central registry that manages named circuit breakers.

    Supports registering breakers, recording successes / failures,
    checking execution eligibility, and forced trip / reset.
    """

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}

        # Pre-register default breakers
        for cfg in _DEFAULT_BREAKERS:
            self.register(
                name=cfg["name"],
                failure_threshold=cfg["failure_threshold"],
                recovery_timeout_sec=cfg["recovery_timeout_sec"],
            )

        logger.info(
            "CircuitBreakerRegistry initialized with %d breakers",
            len(self._breakers),
        )

    # ----- registration -----

    def register(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_sec: float = 30.0,
    ) -> CircuitBreaker:
        """Register a new circuit breaker (or return existing)."""
        if name in self._breakers:
            return self._breakers[name]
        breaker = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout_sec=recovery_timeout_sec,
        )
        self._breakers[name] = breaker
        logger.info(
            "Registered circuit breaker '%s' (threshold=%d, timeout=%.1fs)",
            name, failure_threshold, recovery_timeout_sec,
        )
        return breaker

    # ----- success / failure recording -----

    def record_success(self, name: str) -> None:
        """Record a successful call.  Transitions HALF_OPEN -> CLOSED."""
        breaker = self._breakers.get(name)
        if not breaker:
            return

        breaker.success_count += 1

        if breaker.state == CircuitState.HALF_OPEN:
            breaker.failure_count = 0
            breaker.state = CircuitState.CLOSED
            breaker.last_state_change = datetime.utcnow().isoformat()
            logger.info("Circuit breaker '%s' recovered -> CLOSED", name)

    def record_failure(self, name: str) -> None:
        """Record a failed call.  Trips to OPEN if threshold exceeded."""
        breaker = self._breakers.get(name)
        if not breaker:
            return

        breaker.failure_count += 1
        breaker.last_failure_time = time.time()

        if breaker.state == CircuitState.HALF_OPEN:
            # Any failure in half-open immediately trips back to open
            self._trip_breaker(breaker)
        elif breaker.state == CircuitState.CLOSED:
            if breaker.failure_count >= breaker.failure_threshold:
                self._trip_breaker(breaker)

    # ----- execution check -----

    def can_execute(self, name: str) -> bool:
        """Check whether the circuit allows execution.

        CLOSED  -> True
        OPEN    -> True only if recovery timeout elapsed (transitions to HALF_OPEN)
        HALF_OPEN -> True if under max allowed probe calls
        """
        breaker = self._breakers.get(name)
        if not breaker:
            return True  # unknown breaker -> allow

        if breaker.state == CircuitState.CLOSED:
            return True

        if breaker.state == CircuitState.OPEN:
            elapsed = time.time() - breaker.last_failure_time
            if elapsed >= breaker.recovery_timeout_sec:
                # Transition to HALF_OPEN
                breaker.state = CircuitState.HALF_OPEN
                breaker.success_count = 0
                breaker.last_state_change = datetime.utcnow().isoformat()
                logger.info(
                    "Circuit breaker '%s' timeout elapsed -> HALF_OPEN", name,
                )
                return True
            return False

        if breaker.state == CircuitState.HALF_OPEN:
            return breaker.success_count < breaker.half_open_max_calls

        return False

    # ----- forced operations -----

    def trip(self, name: str) -> bool:
        """Force-trip a breaker to OPEN. Returns False if not found."""
        breaker = self._breakers.get(name)
        if not breaker:
            return False
        self._trip_breaker(breaker)
        return True

    def reset(self, name: str) -> bool:
        """Force-reset a breaker to CLOSED. Returns False if not found."""
        breaker = self._breakers.get(name)
        if not breaker:
            return False
        breaker.state = CircuitState.CLOSED
        breaker.failure_count = 0
        breaker.success_count = 0
        breaker.last_state_change = datetime.utcnow().isoformat()
        logger.info("Circuit breaker '%s' force-reset -> CLOSED", name)
        return True

    # ----- query -----

    def get_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Return breaker details or None."""
        return self._breakers.get(name)

    def list_breakers(self) -> List[CircuitBreaker]:
        """Return all registered breakers."""
        return list(self._breakers.values())

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        by_state: Dict[str, int] = {}
        for b in self._breakers.values():
            by_state[b.state.value] = by_state.get(b.state.value, 0) + 1
        total_trips = sum(b.total_trips for b in self._breakers.values())
        return {
            "total_breakers": len(self._breakers),
            "by_state": by_state,
            "total_trips": total_trips,
            "breakers": [b.to_dict() for b in self._breakers.values()],
        }

    # ----- internal -----

    def _trip_breaker(self, breaker: CircuitBreaker) -> None:
        breaker.state = CircuitState.OPEN
        breaker.total_trips += 1
        breaker.last_state_change = datetime.utcnow().isoformat()
        logger.warning(
            "Circuit breaker '%s' TRIPPED -> OPEN (total trips: %d)",
            breaker.name, breaker.total_trips,
        )


# =========================================
# SINGLETON
# =========================================

_instance: Optional[CircuitBreakerRegistry] = None


def get_circuit_registry() -> CircuitBreakerRegistry:
    global _instance
    if _instance is None:
        _instance = CircuitBreakerRegistry()
    return _instance
