"""Phase 54A — Bulkhead Isolation & Graceful Degradation.

Implements the bulkhead pattern (thread-pool, semaphore, rate-limiter)
to prevent one failing service from consuming all resources.  Includes
a GracefulDegradation controller with three severity levels and
pre-built fallback mappings for core BD-engine services.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================


class BulkheadType(str, Enum):
    THREAD_POOL = "thread_pool"
    SEMAPHORE = "semaphore"
    RATE_LIMITER = "rate_limiter"


@dataclass
class Bulkhead:
    """A single bulkhead partition protecting a resource pool."""

    name: str
    bulkhead_type: BulkheadType = BulkheadType.SEMAPHORE
    max_concurrent: int = 10
    active_count: int = 0
    queue_size: int = 0
    max_queue: int = 20
    rejected_count: int = 0
    total_acquired: int = 0
    total_released: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "bulkhead_type": self.bulkhead_type.value,
            "max_concurrent": self.max_concurrent,
            "active_count": self.active_count,
            "queue_size": self.queue_size,
            "max_queue": self.max_queue,
            "rejected_count": self.rejected_count,
            "total_acquired": self.total_acquired,
            "total_released": self.total_released,
        }


# =========================================
# PRE-REGISTERED BULKHEADS
# =========================================

_DEFAULT_BULKHEADS = [
    {
        "name": "search_pool",
        "bulkhead_type": BulkheadType.THREAD_POOL,
        "max_concurrent": 10,
        "max_queue": 20,
    },
    {
        "name": "agent_pool",
        "bulkhead_type": BulkheadType.THREAD_POOL,
        "max_concurrent": 5,
        "max_queue": 10,
    },
    {
        "name": "api_requests",
        "bulkhead_type": BulkheadType.SEMAPHORE,
        "max_concurrent": 100,
        "max_queue": 50,
    },
    {
        "name": "export_queue",
        "bulkhead_type": BulkheadType.SEMAPHORE,
        "max_concurrent": 3,
        "max_queue": 10,
    },
    {
        "name": "webhook_rate",
        "bulkhead_type": BulkheadType.RATE_LIMITER,
        "max_concurrent": 50,
        "max_queue": 100,
    },
]


# =========================================
# BULKHEAD MANAGER
# =========================================


class BulkheadManager:
    """Manages named bulkhead partitions to isolate resource pools.

    Each bulkhead tracks concurrent usage and rejects or queues
    requests that exceed its capacity, preventing cascade failures.
    """

    def __init__(self):
        self._bulkheads: Dict[str, Bulkhead] = {}

        for cfg in _DEFAULT_BULKHEADS:
            self.register(
                name=cfg["name"],
                bulkhead_type=cfg["bulkhead_type"],
                max_concurrent=cfg["max_concurrent"],
                max_queue=cfg["max_queue"],
            )

        logger.info(
            "BulkheadManager initialized with %d bulkheads",
            len(self._bulkheads),
        )

    # ----- registration -----

    def register(
        self,
        name: str,
        bulkhead_type: BulkheadType = BulkheadType.SEMAPHORE,
        max_concurrent: int = 10,
        max_queue: int = 20,
    ) -> Bulkhead:
        """Register a new bulkhead (or return existing)."""
        if name in self._bulkheads:
            return self._bulkheads[name]
        bulkhead = Bulkhead(
            name=name,
            bulkhead_type=bulkhead_type,
            max_concurrent=max_concurrent,
            max_queue=max_queue,
        )
        self._bulkheads[name] = bulkhead
        logger.info(
            "Registered bulkhead '%s' (%s, max=%d, queue=%d)",
            name,
            bulkhead_type.value,
            max_concurrent,
            max_queue,
        )
        return bulkhead

    # ----- acquire / release -----

    def acquire(self, name: str) -> bool:
        """Try to acquire a slot in the bulkhead.

        Returns True if the slot was acquired.  Returns False if the
        bulkhead is at capacity and the queue is full (request rejected).
        """
        bulkhead = self._bulkheads.get(name)
        if not bulkhead:
            return True  # unknown bulkhead -> allow

        if bulkhead.active_count < bulkhead.max_concurrent:
            bulkhead.active_count += 1
            bulkhead.total_acquired += 1
            return True

        # At capacity — try queuing
        if bulkhead.queue_size < bulkhead.max_queue:
            bulkhead.queue_size += 1
            bulkhead.total_acquired += 1
            logger.debug(
                "Bulkhead '%s' at capacity, request queued (%d/%d)",
                name,
                bulkhead.queue_size,
                bulkhead.max_queue,
            )
            return True

        # Both full — reject
        bulkhead.rejected_count += 1
        logger.warning(
            "Bulkhead '%s' REJECTED request (active=%d, queue=%d)",
            name,
            bulkhead.active_count,
            bulkhead.queue_size,
        )
        return False

    def release(self, name: str) -> None:
        """Release a slot back to the bulkhead."""
        bulkhead = self._bulkheads.get(name)
        if not bulkhead:
            return

        # Promote queued request first
        if bulkhead.queue_size > 0:
            bulkhead.queue_size -= 1
            bulkhead.total_released += 1
        elif bulkhead.active_count > 0:
            bulkhead.active_count -= 1
            bulkhead.total_released += 1

    # ----- query -----

    def get_bulkhead(self, name: str) -> Optional[Bulkhead]:
        return self._bulkheads.get(name)

    def list_bulkheads(self) -> List[Bulkhead]:
        return list(self._bulkheads.values())

    def get_utilization(self, name: str) -> float:
        """Return utilization as a float 0.0-1.0."""
        bulkhead = self._bulkheads.get(name)
        if not bulkhead or bulkhead.max_concurrent == 0:
            return 0.0
        return min(1.0, bulkhead.active_count / bulkhead.max_concurrent)

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        total_rejected = sum(b.rejected_count for b in self._bulkheads.values())
        total_acquired = sum(b.total_acquired for b in self._bulkheads.values())
        return {
            "total_bulkheads": len(self._bulkheads),
            "total_acquired": total_acquired,
            "total_rejected": total_rejected,
            "bulkheads": [b.to_dict() for b in self._bulkheads.values()],
        }


# =========================================
# GRACEFUL DEGRADATION
# =========================================


class DegradationLevel(str, Enum):
    NORMAL = "normal"
    DEGRADED = "degraded"
    EMERGENCY = "emergency"


_DEFAULT_FALLBACKS: Dict[str, str] = {
    "search": "cached_results",
    "agent": "queued_response",
    "notification": "batch_later",
    "export": "limited_export",
}


class GracefulDegradation:
    """Controls system-wide degradation levels and service fallbacks.

    When the system enters DEGRADED or EMERGENCY mode, callers can
    query fallback function names for each service to switch to a
    reduced-capability path.
    """

    def __init__(self):
        self._level: DegradationLevel = DegradationLevel.NORMAL
        self._fallbacks: Dict[str, str] = dict(_DEFAULT_FALLBACKS)
        self._level_changed_at: str = datetime.utcnow().isoformat()
        logger.info(
            "GracefulDegradation initialized at level=%s with %d fallback mappings",
            self._level.value,
            len(self._fallbacks),
        )

    # ----- level management -----

    @property
    def current_level(self) -> DegradationLevel:
        return self._level

    def set_level(self, level: DegradationLevel) -> None:
        """Transition to a new degradation level."""
        old = self._level
        self._level = level
        self._level_changed_at = datetime.utcnow().isoformat()
        logger.info(
            "Degradation level changed: %s -> %s",
            old.value,
            level.value,
        )

    # ----- fallbacks -----

    def register_fallback(self, service: str, fallback_fn_name: str) -> None:
        """Register or update a fallback for a service."""
        self._fallbacks[service] = fallback_fn_name

    def get_fallback(self, service: str) -> Optional[str]:
        """Get the fallback function name for a service."""
        return self._fallbacks.get(service)

    def get_degradation_plan(self) -> Dict[str, Any]:
        """Return the current degradation plan summary."""
        return {
            "level": self._level.value,
            "level_changed_at": self._level_changed_at,
            "fallbacks": dict(self._fallbacks),
            "active_fallbacks": (
                list(self._fallbacks.keys())
                if self._level != DegradationLevel.NORMAL
                else []
            ),
            "description": self._level_description(),
        }

    # ----- internal -----

    def _level_description(self) -> str:
        if self._level == DegradationLevel.NORMAL:
            return "All systems operating normally."
        if self._level == DegradationLevel.DEGRADED:
            return (
                "Non-critical features disabled. Services falling back "
                "to cached or reduced-capability paths."
            )
        if self._level == DegradationLevel.EMERGENCY:
            return (
                "Emergency mode. Only core read paths active. All "
                "background processing paused. Fallbacks engaged for "
                "every registered service."
            )
        return "Unknown level."

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        return {
            "level": self._level.value,
            "level_changed_at": self._level_changed_at,
            "registered_fallbacks": len(self._fallbacks),
        }


# =========================================
# SINGLETONS
# =========================================

_bulkhead_instance: Optional[BulkheadManager] = None
_degradation_instance: Optional[GracefulDegradation] = None


def get_bulkhead_manager() -> BulkheadManager:
    global _bulkhead_instance
    if _bulkhead_instance is None:
        _bulkhead_instance = BulkheadManager()
    return _bulkhead_instance


def get_degradation() -> GracefulDegradation:
    global _degradation_instance
    if _degradation_instance is None:
        _degradation_instance = GracefulDegradation()
    return _degradation_instance
