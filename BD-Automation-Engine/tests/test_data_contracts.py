"""Tests for Phase 43A — Data Contracts Engine."""

import pytest

from src.governance.contracts import (
    DataContractsEngine,
    DataContract,
    BreachSeverity,
    get_contracts_engine,
)


@pytest.fixture
def engine():
    return DataContractsEngine()


# =========================================
# SEEDED CONTRACTS
# =========================================


def test_seeded_contracts(engine):
    contracts = engine.list_contracts()
    assert len(contracts) >= 3
    ids = {c.id for c in contracts}
    assert "contract_jobs_scraper" in ids
    assert "contract_contacts_etl" in ids


def test_get_seeded(engine):
    c = engine.get("contract_jobs_scraper")
    assert c is not None
    assert c.producer == "Engine1_Scraper"
    assert len(c.quality_terms) >= 2


# =========================================
# CRUD
# =========================================


def test_create(engine):
    cid = engine.create(
        DataContract(
            name="Test Contract",
            producer="test_producer",
            consumer="test_consumer",
            asset_id="test_asset",
        )
    )
    assert cid != ""
    assert engine.get(cid) is not None


def test_list_by_producer(engine):
    results = engine.list_contracts(producer="Engine1_Scraper")
    assert all(c.producer == "Engine1_Scraper" for c in results)


def test_list_by_consumer(engine):
    results = engine.list_contracts(consumer="Engine8_Knowledge")
    assert all(c.consumer == "Engine8_Knowledge" for c in results)


def test_update(engine):
    result = engine.update("contract_jobs_scraper", {"max_staleness_hours": 48.0})
    assert result is not None
    assert result.max_staleness_hours == 48.0


def test_delete(engine):
    engine.create(DataContract(id="temp", name="Temp"))
    assert engine.delete("temp") is True
    assert engine.get("temp") is None


# =========================================
# CHECK CONTRACT — PASSING
# =========================================


def test_check_passing(engine):
    result = engine.check_contract(
        "contract_jobs_scraper",
        current_metrics={"completeness": 0.95, "accuracy": 0.95},
        record_count=10,
        staleness_hours=4.0,
    )
    assert result.status == "passing"
    assert len(result.breaches) == 0
    assert result.terms_passing > 0


# =========================================
# CHECK CONTRACT — BREACHED
# =========================================


def test_check_quality_breach(engine):
    result = engine.check_contract(
        "contract_jobs_scraper",
        current_metrics={"completeness": 0.5, "accuracy": 0.7},
    )
    assert result.status == "breached"
    assert len(result.breaches) >= 1
    assert any(b.term_violated == "completeness" for b in result.breaches)


def test_check_staleness_breach(engine):
    result = engine.check_contract(
        "contract_jobs_scraper",
        current_metrics={"completeness": 0.95, "accuracy": 0.95},
        staleness_hours=100.0,
    )
    assert result.status == "breached"
    assert any(b.term_violated == "staleness" for b in result.breaches)
    assert any(b.severity == BreachSeverity.CRITICAL.value for b in result.breaches)


def test_check_record_count_breach(engine):
    result = engine.check_contract(
        "contract_contacts_etl",
        current_metrics={"completeness": 0.95, "accuracy": 0.97},
        record_count=5,
    )
    assert any(b.term_violated == "record_count" for b in result.breaches)


def test_check_nonexistent(engine):
    result = engine.check_contract("nonexistent", {})
    assert result.status == "error"


# =========================================
# CHECK ALL
# =========================================


def test_check_all(engine):
    metrics = {
        "jobs": {"completeness": 0.9, "accuracy": 0.95},
        "contacts": {"completeness": 0.95, "accuracy": 0.97},
        "programs": {"completeness": 0.85},
    }
    results = engine.check_all(metrics)
    assert len(results) >= 3


# =========================================
# BREACHES
# =========================================


def test_get_breaches(engine):
    engine.check_contract(
        "contract_jobs_scraper",
        current_metrics={"completeness": 0.5, "accuracy": 0.5},
    )
    breaches = engine.get_breaches()
    assert len(breaches) >= 1


def test_get_breaches_by_contract(engine):
    engine.check_contract(
        "contract_jobs_scraper",
        current_metrics={"completeness": 0.5, "accuracy": 0.5},
    )
    breaches = engine.get_breaches(contract_id="contract_jobs_scraper")
    assert all(b.contract_id == "contract_jobs_scraper" for b in breaches)


def test_resolve_breach(engine):
    engine.check_contract(
        "contract_jobs_scraper",
        current_metrics={"completeness": 0.5, "accuracy": 0.5},
    )
    breaches = engine.get_breaches(unresolved_only=True)
    assert len(breaches) >= 1
    resolved = engine.resolve_breach(breaches[0].id)
    assert resolved is True


def test_resolve_nonexistent(engine):
    assert engine.resolve_breach("nonexistent") is False


# =========================================
# EVALUATE TERM
# =========================================


def test_evaluate_gte():
    assert DataContractsEngine._evaluate_term(">=", 0.9, 0.85) is True
    assert DataContractsEngine._evaluate_term(">=", 0.8, 0.85) is False


def test_evaluate_lte():
    assert DataContractsEngine._evaluate_term("<=", 4.0, 28.0) is True
    assert DataContractsEngine._evaluate_term("<=", 30.0, 28.0) is False


def test_evaluate_eq():
    assert DataContractsEngine._evaluate_term("==", 1.0, 1.0) is True


# =========================================
# STATS
# =========================================


def test_stats(engine):
    stats = engine.get_stats()
    assert stats["total_contracts"] >= 3
    assert "by_status" in stats


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    e1 = get_contracts_engine()
    e2 = get_contracts_engine()
    assert e1 is e2
