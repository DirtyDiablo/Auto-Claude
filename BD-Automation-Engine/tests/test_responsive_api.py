"""Tests for Phase 58A — Responsive API Layer."""

import pytest

from src.pwa.responsive_api import (
    ResponsiveAPILayer,
    DeviceType,
    NetworkQuality,
    ResponseFormat,
    ClientProfile,
    get_responsive_api,
)


@pytest.fixture
def api():
    return ResponsiveAPILayer()


# Sample data for testing adaptation
SAMPLE_DATA = [
    {"id": i, "name": f"Record {i}", "title": f"Title {i}",
     "description": f"Description for record {i}",
     "status": "active", "score": 75 + i, "company": f"Company {i}",
     "email": f"user{i}@example.com", "phone": "555-0100",
     "program": f"Program {i}", "tier": "Tier 1",
     "created_at": "2025-01-01", "updated_at": "2025-06-01",
     "metadata": {}, "tags": ["bd"], "notes": "Some notes"}
    for i in range(100)
]


# =========================================
# CLIENT DETECTION
# =========================================

def test_detect_desktop(api):
    profile = api.detect_client(user_agent="Mozilla/5.0 Desktop", screen_width=1920)
    assert profile.device_type == DeviceType.DESKTOP


def test_detect_mobile(api):
    profile = api.detect_client(user_agent="Mobile Safari", screen_width=375)
    assert profile.device_type == DeviceType.MOBILE


def test_detect_tablet(api):
    profile = api.detect_client(user_agent="iPad Safari", screen_width=1024)
    assert profile.device_type == DeviceType.TABLET


def test_detect_watch(api):
    profile = api.detect_client(user_agent="Watch", screen_width=200)
    assert profile.device_type == DeviceType.WATCH


def test_detect_api_client(api):
    profile = api.detect_client(user_agent="curl/7.68")
    assert profile.device_type == DeviceType.API_CLIENT


def test_detect_network_wifi(api):
    profile = api.detect_client(network_hint="wifi")
    assert profile.network_quality == NetworkQuality.EXCELLENT


def test_detect_network_3g(api):
    profile = api.detect_client(network_hint="3g")
    assert profile.network_quality == NetworkQuality.FAIR


def test_detect_network_poor(api):
    profile = api.detect_client(network_hint="2g")
    assert profile.network_quality == NetworkQuality.POOR


# =========================================
# RESPONSE ADAPTATION
# =========================================

def test_adapt_full(api):
    profile = ClientProfile(profile_id="test", device_type=DeviceType.DESKTOP,
                            preferred_format=ResponseFormat.FULL)
    result = api.adapt_response(SAMPLE_DATA, profile)
    assert len(result["data"]) == 50  # desktop page size
    assert result["total"] == 100


def test_adapt_mobile(api):
    profile = ClientProfile(profile_id="test", device_type=DeviceType.MOBILE,
                            preferred_format=ResponseFormat.COMPACT)
    result = api.adapt_response(SAMPLE_DATA, profile)
    assert len(result["data"]) == 15  # mobile page size


def test_adapt_watch(api):
    profile = ClientProfile(profile_id="test", device_type=DeviceType.WATCH,
                            preferred_format=ResponseFormat.MINIMAL)
    result = api.adapt_response(SAMPLE_DATA, profile)
    assert len(result["data"]) == 5  # watch page size


def test_adapt_minimal_has_fewer_fields(api):
    profile = ClientProfile(profile_id="test", preferred_format=ResponseFormat.MINIMAL)
    result = api.adapt_response(SAMPLE_DATA, profile)
    record = result["data"][0]
    assert "id" in record
    assert "name" in record
    assert "description" not in record
    assert "email" not in record


def test_adapt_compact_has_more_than_minimal(api):
    profile = ClientProfile(profile_id="test", preferred_format=ResponseFormat.COMPACT)
    result = api.adapt_response(SAMPLE_DATA, profile)
    record = result["data"][0]
    assert "company" in record
    assert "tier" in record


def test_adaptation_metadata(api):
    result = api.adapt_response(SAMPLE_DATA)
    assert "adaptation" in result
    assert "format_used" in result["adaptation"]


def test_adapt_empty_data(api):
    result = api.adapt_response([])
    assert len(result["data"]) == 0
    assert result["total"] == 0


# =========================================
# PAGE SIZES
# =========================================

def test_page_size_desktop(api):
    assert api.get_recommended_page_size(DeviceType.DESKTOP) == 50


def test_page_size_mobile(api):
    assert api.get_recommended_page_size(DeviceType.MOBILE) == 15


def test_page_size_api(api):
    assert api.get_recommended_page_size(DeviceType.API_CLIENT) == 100


# =========================================
# FIELDS FOR FORMAT
# =========================================

def test_full_fields(api):
    fields = api.get_fields_for_format(ResponseFormat.FULL)
    assert len(fields) > 10


def test_minimal_fields(api):
    fields = api.get_fields_for_format(ResponseFormat.MINIMAL)
    assert len(fields) <= 5


# =========================================
# PROFILE & STATS
# =========================================

def test_profile_to_dict(api):
    profile = api.detect_client(user_agent="Test")
    d = profile.to_dict()
    assert "device_type" in d
    assert "network_quality" in d


def test_get_profile(api):
    profile = api.detect_client(user_agent="Test")
    found = api.get_profile(profile.profile_id)
    assert found is not None


def test_stats(api):
    api.adapt_response(SAMPLE_DATA)
    stats = api.get_stats()
    assert stats["total_requests"] == 1


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    import src.pwa.responsive_api as mod
    mod._instance = None
    a1 = get_responsive_api()
    a2 = get_responsive_api()
    assert a1 is a2
    mod._instance = None
