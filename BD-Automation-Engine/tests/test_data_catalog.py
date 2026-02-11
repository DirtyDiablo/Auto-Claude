"""Tests for Phase 43A — Data Catalog."""

import pytest

from src.governance.catalog import (
    DataCatalog,
    DataAsset,
    AssetType,
    AssetStatus,
    DataLineage,
    QualityMetrics,
    get_data_catalog,
)


@pytest.fixture
def catalog():
    return DataCatalog()


# =========================================
# SEEDED ASSETS
# =========================================

def test_seeded_assets(catalog):
    assets = catalog.list_assets()
    assert len(assets) >= 5
    ids = {a.id for a in assets}
    assert "contacts" in ids
    assert "programs" in ids
    assert "jobs" in ids


def test_get_seeded(catalog):
    asset = catalog.get("contacts")
    assert asset is not None
    assert asset.name == "Contacts"
    assert asset.record_count == 7337


# =========================================
# REGISTER & CRUD
# =========================================

def test_register(catalog):
    asset_id = catalog.register(DataAsset(
        name="Test Asset", domain="test", asset_type="file",
    ))
    assert asset_id != ""
    assert catalog.get(asset_id) is not None


def test_update(catalog):
    result = catalog.update("contacts", {"record_count": 8000})
    assert result is not None
    assert result.record_count == 8000


def test_update_nonexistent(catalog):
    assert catalog.update("nonexistent", {"name": "x"}) is None


def test_delete(catalog):
    catalog.register(DataAsset(id="temp", name="Temp"))
    assert catalog.delete("temp") is True
    assert catalog.get("temp") is None


def test_delete_nonexistent(catalog):
    assert catalog.delete("nonexistent") is False


# =========================================
# LIST & FILTER
# =========================================

def test_list_by_domain(catalog):
    results = catalog.list_assets(domain="contacts")
    assert all(a.domain == "contacts" for a in results)


def test_list_by_type(catalog):
    results = catalog.list_assets(asset_type="collection")
    assert all(a.asset_type == "collection" for a in results)


def test_list_with_limit(catalog):
    results = catalog.list_assets(limit=2)
    assert len(results) <= 2


# =========================================
# SEARCH
# =========================================

def test_search_by_name(catalog):
    results = catalog.search("Contacts")
    assert len(results) >= 1
    assert results[0].id == "contacts"


def test_search_by_tag(catalog):
    results = catalog.search("crm")
    assert len(results) >= 1


def test_search_by_domain(catalog):
    results = catalog.search("jobs")
    assert len(results) >= 1


def test_search_no_match(catalog):
    results = catalog.search("xyznonexistent")
    assert len(results) == 0


# =========================================
# LINEAGE
# =========================================

def test_lineage(catalog):
    lineage = catalog.get_lineage("contacts")
    assert lineage is not None
    assert lineage["asset_id"] == "contacts"
    assert len(lineage["upstream"]) >= 1


def test_lineage_nonexistent(catalog):
    assert catalog.get_lineage("nonexistent") is None


# =========================================
# USAGE TRACKING
# =========================================

def test_record_read(catalog):
    catalog.record_read("contacts")
    asset = catalog.get("contacts")
    assert asset.usage.total_reads >= 1
    assert asset.usage.last_read_at != ""


def test_record_write(catalog):
    catalog.record_write("contacts")
    asset = catalog.get("contacts")
    assert asset.usage.total_writes >= 1


def test_popularity(catalog):
    for _ in range(10):
        catalog.record_read("contacts")
    asset = catalog.get("contacts")
    assert asset.usage.popularity_score > 0


# =========================================
# QUALITY
# =========================================

def test_update_quality(catalog):
    q = catalog.update_quality("contacts", {
        "completeness": 0.92, "accuracy": 0.95,
        "freshness_hours": 24.0, "consistency": 0.88,
    })
    assert q is not None
    assert q.overall_score > 0


def test_update_quality_nonexistent(catalog):
    assert catalog.update_quality("nonexistent", {}) is None


# =========================================
# STATS
# =========================================

def test_stats(catalog):
    stats = catalog.get_stats()
    assert stats["total_assets"] >= 5
    assert len(stats["domains"]) >= 1
    assert stats["total_records"] > 0


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    c1 = get_data_catalog()
    c2 = get_data_catalog()
    assert c1 is c2
