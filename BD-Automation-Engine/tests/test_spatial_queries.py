"""Tests for Phase 48A — Spatial Query Processor."""

import pytest

from src.geographic.geocoding_engine import GeocodingEngine
from src.geographic.spatial_queries import (
    SpatialQueryProcessor,
    RadiusResult,
    GeoCluster,
    OverlapResult,
    CommuteResult,
    CompetitiveDensity,
    get_spatial_processor,
)


@pytest.fixture
def spatial():
    geocoder = GeocodingEngine()
    return SpatialQueryProcessor(geocoder)


# =========================================
# HAVERSINE
# =========================================

def test_haversine_zero_distance():
    dist = SpatialQueryProcessor.haversine(38.87, -77.05, 38.87, -77.05)
    assert dist == 0.0


def test_haversine_pentagon_to_langley():
    # Pentagon (38.87, -77.05) to Langley AFB (37.08, -76.36)
    dist = SpatialQueryProcessor.haversine(38.8719, -77.0563, 37.0833, -76.3605)
    assert 100 < dist < 200  # ~130 miles


def test_haversine_short_distance():
    # Pentagon to Fort Belvoir (~10 miles)
    dist = SpatialQueryProcessor.haversine(38.8719, -77.0563, 38.7118, -77.1452)
    assert 5 < dist < 20


# =========================================
# RADIUS SEARCH
# =========================================

def test_radius_around_pentagon(spatial):
    # Pentagon: 38.8719, -77.0563
    result = spatial.find_within_radius(38.8719, -77.0563, radius_miles=15.0)
    assert isinstance(result, RadiusResult)
    assert result.total >= 3  # Pentagon area has many facilities
    assert result.radius_miles == 15.0


def test_radius_sorted_by_distance(spatial):
    result = spatial.find_within_radius(38.8719, -77.0563, radius_miles=30.0)
    distances = [e["distance_miles"] for e in result.entities]
    assert distances == sorted(distances)


def test_radius_entity_type_filter(spatial):
    result = spatial.find_within_radius(
        38.8719, -77.0563, radius_miles=30.0, entity_types=["facility"],
    )
    assert all(e["entity_type"] == "facility" for e in result.entities)


def test_radius_contacts_only(spatial):
    result = spatial.find_within_radius(
        38.8719, -77.0563, radius_miles=50.0, entity_types=["contact"],
    )
    assert all(e["entity_type"] == "contact" for e in result.entities)


def test_radius_no_results(spatial):
    # Middle of Pacific Ocean
    result = spatial.find_within_radius(0.0, -170.0, radius_miles=10.0)
    assert result.total == 0


def test_radius_includes_distance(spatial):
    result = spatial.find_within_radius(38.8719, -77.0563, radius_miles=20.0)
    for e in result.entities:
        assert "distance_miles" in e
        assert e["distance_miles"] <= 20.0


# =========================================
# CLUSTER ANALYSIS
# =========================================

def test_cluster_contacts(spatial):
    clusters = spatial.cluster_analysis("contact")
    assert isinstance(clusters, list)
    assert len(clusters) >= 2  # at least NCR and some other regions
    assert all(isinstance(c, GeoCluster) for c in clusters)


def test_cluster_has_region(spatial):
    clusters = spatial.cluster_analysis("contact")
    regions = [c.region for c in clusters]
    assert "NCR" in regions or "southeast" in regions  # most contacts are in these areas


def test_cluster_has_center(spatial):
    clusters = spatial.cluster_analysis("contact")
    for c in clusters:
        assert c.center_lat != 0.0
        assert c.center_lng != 0.0


def test_cluster_facilities(spatial):
    clusters = spatial.cluster_analysis("facility")
    assert len(clusters) >= 4  # NCR, southeast, west, midwest, etc.
    total_entities = sum(c.total for c in clusters)
    assert total_entities >= 50


def test_cluster_jobs(spatial):
    clusters = spatial.cluster_analysis("job")
    assert len(clusters) >= 2


def test_cluster_programs(spatial):
    clusters = spatial.cluster_analysis("program")
    assert len(clusters) >= 2


def test_cluster_dominant_programs(spatial):
    clusters = spatial.cluster_analysis("contact")
    ncr = next((c for c in clusters if c.region == "NCR"), None)
    if ncr:
        assert len(ncr.dominant_programs) >= 1


# =========================================
# OVERLAP ANALYSIS
# =========================================

def test_overlap_dcgs_a_jadc2(spatial):
    """DCGS-A and JADC2 share Fort Meade."""
    result = spatial.overlap_analysis("DCGS-A", "JADC2")
    assert isinstance(result, OverlapResult)
    assert result.program_a == "DCGS-A"
    assert result.program_b == "JADC2"


def test_overlap_shared_locations(spatial):
    result = spatial.overlap_analysis("DCGS-A", "JADC2")
    # Both have Fort Meade, MD
    assert len(result.shared_locations) >= 1 or len(result.proximity_pairs) >= 1


def test_overlap_score(spatial):
    result = spatial.overlap_analysis("DCGS-A", "JADC2")
    assert 0 <= result.overlap_score <= 1.0


def test_overlap_no_overlap(spatial):
    result = spatial.overlap_analysis("GBSD", "MQ-25")
    # These should have minimal geographic overlap
    assert result.overlap_score < 0.5


def test_overlap_unknown_program(spatial):
    result = spatial.overlap_analysis("DCGS-A", "NONEXISTENT")
    assert result.overlap_score == 0


# =========================================
# COMMUTE ANALYSIS
# =========================================

def test_commute_from_langley(spatial):
    # Langley AFB area: 37.0833, -76.3605
    result = spatial.commute_analysis(37.0833, -76.3605, max_commute_miles=15.0)
    assert isinstance(result, CommuteResult)
    assert result.total >= 1  # DCGS-A jobs at Langley


def test_commute_sorted(spatial):
    result = spatial.commute_analysis(38.8719, -77.0563, max_commute_miles=50.0)
    distances = [j["distance_miles"] for j in result.jobs_in_range]
    assert distances == sorted(distances)


def test_commute_has_estimate(spatial):
    result = spatial.commute_analysis(37.0833, -76.3605, max_commute_miles=20.0)
    for j in result.jobs_in_range:
        assert "estimated_commute_min" in j
        assert j["estimated_commute_min"] >= 0


def test_commute_no_results(spatial):
    # Middle of nowhere
    result = spatial.commute_analysis(0.0, 0.0, max_commute_miles=10.0)
    assert result.total == 0


# =========================================
# COMPETITIVE DENSITY
# =========================================

def test_competitive_density_ncr(spatial):
    result = spatial.competitive_density("NCR")
    assert isinstance(result, CompetitiveDensity)
    assert result.region == "NCR"
    assert len(result.competitors) >= 1
    assert result.total_facilities >= 5


def test_competitive_density_score(spatial):
    result = spatial.competitive_density("NCR")
    assert 0 <= result.density_score <= 1.0


def test_competitive_density_empty_region(spatial):
    result = spatial.competitive_density("antarctica")
    assert result.total_facilities == 0
    assert result.density_score == 0


# =========================================
# HEATMAP
# =========================================

def test_heatmap_contacts(spatial):
    points = spatial.generate_heatmap("contact")
    assert len(points) >= 8
    for p in points:
        assert "lat" in p
        assert "lng" in p
        assert "weight" in p


def test_heatmap_facilities(spatial):
    points = spatial.generate_heatmap("facility")
    assert len(points) >= 50


def test_heatmap_jobs(spatial):
    points = spatial.generate_heatmap("job")
    assert len(points) >= 8


def test_heatmap_programs(spatial):
    points = spatial.generate_heatmap("program")
    assert len(points) >= 10


# =========================================
# STATS
# =========================================

def test_stats(spatial):
    stats = spatial.get_stats()
    assert stats["total_contacts"] >= 10
    assert stats["total_programs"] >= 8
    assert stats["total_jobs"] >= 10
    assert stats["total_facilities"] >= 50


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    s1 = get_spatial_processor()
    s2 = get_spatial_processor()
    assert s1 is s2
