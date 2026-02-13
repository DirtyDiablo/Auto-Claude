"""Phase 57A — Read Replica Manager.

Manages read replicas with health monitoring, query routing,
lag tracking, and promotion for the BD pipeline data stores.
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

class ReplicaStatus(Enum):
    ACTIVE = "active"
    STANDBY = "standby"
    SYNCING = "syncing"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class ReadPreference(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    NEAREST = "nearest"
    ROUND_ROBIN = "round_robin"


@dataclass
class ReadReplica:
    replica_id: str
    name: str
    host: str = "localhost"
    port: int = 6333
    status: ReplicaStatus = ReplicaStatus.ACTIVE
    lag_ms: float = 0.0
    queries_served: int = 0
    last_health_check: str = ""
    weight: float = 1.0

    def __post_init__(self):
        if not self.last_health_check:
            self.last_health_check = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "replica_id": self.replica_id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "status": self.status.value,
            "lag_ms": self.lag_ms,
            "queries_served": self.queries_served,
            "last_health_check": self.last_health_check,
            "weight": self.weight,
        }


@dataclass
class ReplicaSetConfig:
    primary_host: str = "localhost"
    primary_port: int = 6333
    read_preference: ReadPreference = ReadPreference.ROUND_ROBIN
    max_lag_ms: float = 100.0


# =========================================
# READ REPLICA MANAGER
# =========================================

class ReadReplicaManager:
    """Manages read replicas with query routing, lag tracking,
    and promotion capabilities.
    """

    def __init__(self):
        self._replicas: Dict[str, ReadReplica] = {}
        self._config = ReplicaSetConfig()
        self._round_robin_idx = 0
        self._register_defaults()
        logger.info("ReadReplicaManager initialized with %d replicas", len(self._replicas))

    def _register_defaults(self) -> None:
        defaults = [
            ReadReplica(replica_id="qdrant_primary", name="Qdrant Primary", host="localhost", port=6333, weight=1.0, lag_ms=0.0),
            ReadReplica(replica_id="qdrant_replica_1", name="Qdrant Replica 1", host="localhost", port=6334, weight=1.0, lag_ms=5.0),
            ReadReplica(replica_id="qdrant_replica_2", name="Qdrant Replica 2", host="localhost", port=6335, status=ReplicaStatus.STANDBY, weight=0.5, lag_ms=15.0),
            ReadReplica(replica_id="analytics_replica", name="Analytics Replica", host="localhost", port=6336, weight=0.8, lag_ms=10.0),
        ]
        for r in defaults:
            self._replicas[r.replica_id] = r

    # ----- routing -----

    def route_query(self, query_type: str = "read") -> str:
        """Route a query to the best replica. Writes always go to primary."""
        if query_type == "write":
            primary = self._replicas.get("qdrant_primary")
            if primary:
                primary.queries_served += 1
            return "qdrant_primary"

        # Get active replicas within acceptable lag
        active = [r for r in self._replicas.values()
                   if r.status == ReplicaStatus.ACTIVE and r.lag_ms <= self._config.max_lag_ms]

        if not active:
            # Fall back to primary
            primary = self._replicas.get("qdrant_primary")
            if primary:
                primary.queries_served += 1
            return "qdrant_primary"

        # Round-robin among active replicas (weighted)
        self._round_robin_idx = (self._round_robin_idx + 1) % len(active)
        chosen = active[self._round_robin_idx]
        chosen.queries_served += 1
        return chosen.replica_id

    # ----- queries -----

    def get_replica(self, replica_id: str) -> Optional[ReadReplica]:
        return self._replicas.get(replica_id)

    def list_replicas(self, status_filter: Optional[ReplicaStatus] = None) -> List[ReadReplica]:
        replicas = list(self._replicas.values())
        if status_filter is not None:
            replicas = [r for r in replicas if r.status == status_filter]
        return replicas

    # ----- status management -----

    def update_replica_status(self, replica_id: str, new_status: ReplicaStatus) -> bool:
        replica = self._replicas.get(replica_id)
        if not replica:
            return False
        replica.status = new_status
        replica.last_health_check = datetime.utcnow().isoformat()
        logger.info("Replica %s status changed to %s", replica_id, new_status.value)
        return True

    def promote_replica(self, replica_id: str) -> bool:
        """Promote a replica to ACTIVE status."""
        replica = self._replicas.get(replica_id)
        if not replica:
            return False
        replica.status = ReplicaStatus.ACTIVE
        replica.last_health_check = datetime.utcnow().isoformat()
        logger.info("Replica %s promoted to ACTIVE", replica_id)
        return True

    # ----- lag report -----

    def get_lag_report(self) -> Dict[str, float]:
        return {rid: r.lag_ms for rid, r in self._replicas.items()}

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        by_status: Dict[str, int] = {}
        for r in self._replicas.values():
            by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
        return {
            "total_replicas": len(self._replicas),
            "by_status": by_status,
            "total_queries_served": sum(r.queries_served for r in self._replicas.values()),
            "avg_lag_ms": round(sum(r.lag_ms for r in self._replicas.values()) / max(len(self._replicas), 1), 1),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[ReadReplicaManager] = None


def get_replica_manager() -> ReadReplicaManager:
    global _instance
    if _instance is None:
        _instance = ReadReplicaManager()
    return _instance
