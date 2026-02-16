"""Phase 57A — Connection Pool Manager.

Manages connection pools for database, HTTP, Redis, gRPC, and custom
backends with health monitoring, stats tracking, and dynamic resizing.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================


class PoolType(Enum):
    DATABASE = "database"
    HTTP = "http"
    REDIS = "redis"
    GRPC = "grpc"
    CUSTOM = "custom"


@dataclass
class PoolStats:
    total_acquired: int = 0
    total_released: int = 0
    total_timeouts: int = 0
    avg_wait_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_acquired": self.total_acquired,
            "total_released": self.total_released,
            "total_timeouts": self.total_timeouts,
            "avg_wait_ms": round(self.avg_wait_ms, 2),
        }


@dataclass
class ConnectionPool:
    name: str
    pool_type: PoolType
    min_size: int
    max_size: int
    current_size: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    wait_queue_size: int = 0
    created_at: float = field(default_factory=time.time)
    stats: PoolStats = field(default_factory=PoolStats)

    def __post_init__(self) -> None:
        if self.current_size == 0:
            self.current_size = self.min_size
        if self.idle_connections == 0 and self.active_connections == 0:
            self.idle_connections = self.current_size

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "pool_type": self.pool_type.value,
            "min_size": self.min_size,
            "max_size": self.max_size,
            "current_size": self.current_size,
            "active_connections": self.active_connections,
            "idle_connections": self.idle_connections,
            "wait_queue_size": self.wait_queue_size,
            "created_at": self.created_at,
            "stats": self.stats.to_dict(),
        }


# =========================================
# CONNECTION POOL MANAGER
# =========================================


class ConnectionPoolManager:
    """Manages named connection pools with acquire/release,
    dynamic resizing, health monitoring, and aggregate stats.
    """

    def __init__(self):
        self._pools: Dict[str, ConnectionPool] = {}
        self._created_at = time.time()
        self._register_defaults()
        logger.info("ConnectionPoolManager initialized with %d pools", len(self._pools))

    def _register_defaults(self) -> None:
        defaults = [
            ConnectionPool(
                name="qdrant_pool", pool_type=PoolType.DATABASE, min_size=2, max_size=20
            ),
            ConnectionPool(
                name="api_pool", pool_type=PoolType.HTTP, min_size=5, max_size=50
            ),
            ConnectionPool(
                name="redis_cache", pool_type=PoolType.REDIS, min_size=3, max_size=30
            ),
            ConnectionPool(
                name="grpc_agents", pool_type=PoolType.GRPC, min_size=2, max_size=15
            ),
            ConnectionPool(
                name="webhook_pool", pool_type=PoolType.HTTP, min_size=1, max_size=10
            ),
        ]
        for pool in defaults:
            self._pools[pool.name] = pool

    # ----- core operations -----

    def acquire(self, pool_name: str) -> bool:
        """Acquire a connection. Returns False if pool not found or at capacity."""
        pool = self._pools.get(pool_name)
        if pool is None:
            return False

        if pool.idle_connections > 0:
            pool.idle_connections -= 1
            pool.active_connections += 1
            pool.stats.total_acquired += 1
            self._update_avg_wait(pool, 0.5)
            return True

        if pool.current_size < pool.max_size:
            pool.current_size += 1
            pool.active_connections += 1
            pool.stats.total_acquired += 1
            self._update_avg_wait(pool, 2.0)
            return True

        pool.wait_queue_size += 1
        pool.stats.total_timeouts += 1
        return False

    def release(self, pool_name: str) -> bool:
        """Release a connection back to the pool."""
        pool = self._pools.get(pool_name)
        if pool is None:
            return False
        if pool.active_connections <= 0:
            return False
        pool.active_connections -= 1
        pool.idle_connections += 1
        pool.stats.total_released += 1
        if pool.wait_queue_size > 0:
            pool.wait_queue_size -= 1
        return True

    def resize(self, pool_name: str, new_max: int) -> bool:
        """Update the maximum size of a pool."""
        pool = self._pools.get(pool_name)
        if pool is None:
            return False
        if new_max < pool.min_size:
            return False
        pool.max_size = new_max
        return True

    # ----- queries -----

    def get_pool(self, name: str) -> Optional[ConnectionPool]:
        return self._pools.get(name)

    def list_pools(self) -> List[ConnectionPool]:
        return list(self._pools.values())

    def get_health(self, pool_name: str) -> Optional[Dict[str, Any]]:
        """Health report. Thresholds: <70% healthy, 70-90% warning, >90% critical."""
        pool = self._pools.get(pool_name)
        if pool is None:
            return None
        utilization = (
            (pool.active_connections / pool.max_size * 100)
            if pool.max_size > 0
            else 0.0
        )
        if utilization > 90:
            status = "critical"
        elif utilization > 70:
            status = "warning"
        else:
            status = "healthy"
        return {
            "pool_name": pool_name,
            "utilization_pct": round(utilization, 1),
            "status": status,
            "active": pool.active_connections,
            "idle": pool.idle_connections,
            "max_size": pool.max_size,
            "wait_queue": pool.wait_queue_size,
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_pools": len(self._pools),
            "total_active": sum(p.active_connections for p in self._pools.values()),
            "total_idle": sum(p.idle_connections for p in self._pools.values()),
            "total_acquired": sum(p.stats.total_acquired for p in self._pools.values()),
            "total_timeouts": sum(p.stats.total_timeouts for p in self._pools.values()),
        }

    @staticmethod
    def _update_avg_wait(pool: ConnectionPool, wait_ms: float) -> None:
        n = pool.stats.total_acquired
        if n <= 1:
            pool.stats.avg_wait_ms = wait_ms
        else:
            pool.stats.avg_wait_ms = (pool.stats.avg_wait_ms * (n - 1) + wait_ms) / n


# =========================================
# SINGLETON
# =========================================

_instance: Optional[ConnectionPoolManager] = None


def get_pool_manager() -> ConnectionPoolManager:
    global _instance
    if _instance is None:
        _instance = ConnectionPoolManager()
    return _instance
