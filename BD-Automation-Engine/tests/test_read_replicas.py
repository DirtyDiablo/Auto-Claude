"""Tests for Phase 57A — Read Replica Manager."""

import pytest

from src.scaling.read_replicas import (
    ReadReplicaManager,
    ReplicaStatus,
    get_replica_manager,
)


@pytest.fixture
def mgr():
    return ReadReplicaManager()


# =========================================
# PRE-REGISTERED REPLICAS
# =========================================

def test_default_replicas(mgr):
    replicas = mgr.list_replicas()
    assert len(replicas) == 4


def test_primary_replica(mgr):
    r = mgr.get_replica("qdrant_primary")
    assert r is not None
    assert r.status == ReplicaStatus.ACTIVE


def test_standby_replica(mgr):
    r = mgr.get_replica("qdrant_replica_2")
    assert r is not None
    assert r.status == ReplicaStatus.STANDBY


# =========================================
# ROUTING
# =========================================

def test_route_write_to_primary(mgr):
    result = mgr.route_query("write")
    assert result == "qdrant_primary"


def test_route_read(mgr):
    result = mgr.route_query("read")
    assert result is not None
    # Should be one of the active replicas
    active = [r.replica_id for r in mgr.list_replicas(ReplicaStatus.ACTIVE)]
    assert result in active


def test_route_read_increments_queries(mgr):
    name = mgr.route_query("read")
    r = mgr.get_replica(name)
    assert r.queries_served >= 1


# =========================================
# STATUS UPDATES
# =========================================

def test_update_status(mgr):
    mgr.update_replica_status("qdrant_replica_2", ReplicaStatus.ACTIVE)
    r = mgr.get_replica("qdrant_replica_2")
    assert r.status == ReplicaStatus.ACTIVE


def test_update_status_not_found(mgr):
    result = mgr.update_replica_status("fake_replica", ReplicaStatus.ACTIVE)
    assert result is False


def test_promote_replica(mgr):
    mgr.promote_replica("qdrant_replica_2")
    r = mgr.get_replica("qdrant_replica_2")
    assert r.status == ReplicaStatus.ACTIVE


def test_promote_not_found(mgr):
    result = mgr.promote_replica("fake")
    assert result is False


# =========================================
# LAG REPORT
# =========================================

def test_lag_report(mgr):
    report = mgr.get_lag_report()
    assert "qdrant_primary" in report
    assert "qdrant_replica_1" in report


def test_lag_values(mgr):
    report = mgr.get_lag_report()
    for rid, lag in report.items():
        assert isinstance(lag, (int, float))
        assert lag >= 0


# =========================================
# FILTER BY STATUS
# =========================================

def test_list_active(mgr):
    active = mgr.list_replicas(status_filter=ReplicaStatus.ACTIVE)
    assert len(active) >= 2


def test_list_standby(mgr):
    standby = mgr.list_replicas(status_filter=ReplicaStatus.STANDBY)
    assert len(standby) >= 1


# =========================================
# TO_DICT & STATS
# =========================================

def test_replica_to_dict(mgr):
    r = mgr.get_replica("qdrant_primary")
    d = r.to_dict()
    assert "replica_id" in d
    assert "status" in d
    assert "lag_ms" in d


def test_stats(mgr):
    stats = mgr.get_stats()
    assert stats["total_replicas"] == 4


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    import src.scaling.read_replicas as mod
    mod._instance = None
    a1 = get_replica_manager()
    a2 = get_replica_manager()
    assert a1 is a2
    mod._instance = None
