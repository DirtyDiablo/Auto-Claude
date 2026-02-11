"""Tests for Phase 48A — Geocoding Engine."""

import pytest

from src.geographic.geocoding_engine import (
    GeocodingEngine,
    GeoPoint,
    GeocodedEntity,
    BatchResult,
    get_geocoding_engine,
)


@pytest.fixture
def geocoder():
    return GeocodingEngine()


# =========================================
# EXACT CACHE HITS
# =========================================

def test_geocode_exact_name(geocoder):
    geo = geocoder.geocode("Pentagon")
    assert geo is not None
    assert abs(geo.lat - 38.8719) < 0.01
    assert geo.state == "VA"


def test_geocode_exact_alias(geocoder):
    geo = geocoder.geocode("Langley AFB, VA")
    assert geo is not None
    assert abs(geo.lat - 37.083) < 0.01


def test_geocode_dgs1(geocoder):
    geo = geocoder.geocode("DGS-1")
    assert geo is not None
    assert "Langley" in geo.name


def test_geocode_case_insensitive(geocoder):
    geo = geocoder.geocode("pentagon")
    assert geo is not None
    assert geo.name == "Pentagon"


def test_geocode_fort_meade(geocoder):
    geo = geocoder.geocode("Fort Meade, MD")
    assert geo is not None
    assert geo.state == "MD"


def test_geocode_nsa_hq(geocoder):
    geo = geocoder.geocode("NSA HQ")
    assert geo is not None
    assert "Meade" in geo.name


def test_geocode_wright_patt(geocoder):
    geo = geocoder.geocode("Wright-Patt")
    assert geo is not None
    assert geo.state == "OH"


def test_geocode_hill_afb(geocoder):
    geo = geocoder.geocode("Hill AFB, UT")
    assert geo is not None
    assert geo.state == "UT"


# =========================================
# FUZZY MATCHING
# =========================================

def test_geocode_fuzzy_substring(geocoder):
    geo = geocoder.geocode("Pax River")
    assert geo is not None
    assert "Patuxent" in geo.name


def test_geocode_aberdeen(geocoder):
    geo = geocoder.geocode("Aberdeen, MD")
    assert geo is not None
    assert abs(geo.lat - 39.46) < 0.1


def test_geocode_st_inigoes(geocoder):
    geo = geocoder.geocode("St. Inigoes, MD")
    assert geo is not None


# =========================================
# STATE FALLBACK
# =========================================

def test_geocode_unknown_va_location(geocoder):
    """Unknown location in VA should fallback to a VA facility."""
    geo = geocoder.geocode("Some Office, VA")
    assert geo is not None
    assert geo.state == "VA"
    assert geo.source == "fallback"


def test_geocode_unknown_no_state(geocoder):
    geo = geocoder.geocode("Unknown Location Nowhere")
    assert geo is None


def test_geocode_empty(geocoder):
    assert geocoder.geocode("") is None
    assert geocoder.geocode("  ") is None


# =========================================
# ENTITY GEOCODING
# =========================================

def test_geocode_entity(geocoder):
    ge = geocoder.geocode_entity("c001", "contact", "Craig Lindahl", "Langley AFB, VA")
    assert isinstance(ge, GeocodedEntity)
    assert ge.resolved is True
    assert ge.geo is not None


def test_geocode_entity_unresolved(geocoder):
    ge = geocoder.geocode_entity("c999", "contact", "Unknown Person", "Mars Colony")
    assert ge.resolved is False
    assert ge.geo is None


# =========================================
# BATCH GEOCODING
# =========================================

def test_batch_contacts(geocoder):
    result = geocoder.batch_geocode_contacts()
    assert isinstance(result, BatchResult)
    assert result.total == 10
    assert result.resolved >= 8  # most should resolve
    assert result.failed <= 2


def test_batch_programs(geocoder):
    result = geocoder.batch_geocode_programs()
    assert result.total >= 15  # 8 programs × ~2-3 locations each
    assert result.resolved >= 12


def test_batch_jobs(geocoder):
    result = geocoder.batch_geocode_jobs()
    assert result.total == 10
    assert result.resolved >= 8


def test_batch_all(geocoder):
    results = geocoder.batch_geocode_all()
    assert "contacts" in results
    assert "programs" in results
    assert "jobs" in results
    assert results["contacts"].total > 0


def test_batch_duration(geocoder):
    result = geocoder.batch_geocode_contacts()
    assert result.duration_sec >= 0


def test_batch_id(geocoder):
    result = geocoder.batch_geocode_contacts()
    assert result.id.startswith("gbatch_")


# =========================================
# FACILITIES
# =========================================

def test_get_all_facilities(geocoder):
    facilities = geocoder.get_facilities()
    assert len(facilities) >= 50


def test_filter_by_region(geocoder):
    ncr = geocoder.get_facilities(region="NCR")
    assert len(ncr) >= 10
    assert all(f.region == "NCR" for f in ncr)


def test_filter_by_type(geocoder):
    bases = geocoder.get_facilities(facility_type="base")
    assert len(bases) >= 20
    assert all(f.facility_type == "base" for f in bases)


def test_filter_by_state(geocoder):
    va = geocoder.get_facilities(state="VA")
    assert len(va) >= 5
    assert all(f.state == "VA" for f in va)


def test_get_regions(geocoder):
    regions = geocoder.get_regions()
    assert "NCR" in regions
    assert "southeast" in regions
    assert "west" in regions
    assert "midwest" in regions


# =========================================
# GEOPOINT
# =========================================

def test_geopoint_to_dict(geocoder):
    geo = geocoder.geocode("Pentagon")
    d = geo.to_dict()
    assert "lat" in d
    assert "lng" in d
    assert "name" in d
    assert "region" in d


# =========================================
# STATS
# =========================================

def test_stats(geocoder):
    geocoder.geocode("Pentagon")
    stats = geocoder.get_stats()
    assert stats["total_facilities"] >= 50
    assert stats["total_geocodes"] >= 1
    assert stats["cache_size"] > 0


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    g1 = get_geocoding_engine()
    g2 = get_geocoding_engine()
    assert g1 is g2
