"""Tests for Feature 22 — Mobile-Responsive Dashboard API Layer.

50+ tests covering all 7 mobile endpoints, response models, pagination,
cache headers, empty-state handling, and payload compactness.
"""

import json
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from Engine8_Knowledge.models.mobile_models import (
    MobileAlertItem,
    MobileAlertListResponse,
    MobileContactDetailResponse,
    MobileContactItem,
    MobileContactListResponse,
    MobileDashboardResponse,
    MobileProgramItem,
    MobileProgramListResponse,
    MobileSearchResponse,
    MobileSearchResult,
    PWAIcon,
    PWAManifest,
)
from Engine8_Knowledge.routers.mobile import router, _get_service
import Engine8_Knowledge.routers.mobile as mobile_mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Sample data for the mock service
_SAMPLE_CONTACTS = [
    {
        "id": str(i),
        "name": f"Contact {i}",
        "company": f"Company {i}",
        "tier": (i % 6) + 1,
        "tier_label": "Decision Maker" if i % 6 == 0 else "Staff",
        "phone": f"555-000{i}",
        "email": f"c{i}@example.com",
        "title": f"Director {i}",
        "program": f"Program-{i}",
        "last_contacted": "2026-01-15",
        "notes": f"Notes for contact {i}",
        "bd_score": 50 + i * 5,
    }
    for i in range(30)
]

_SAMPLE_PROGRAMS = [
    {
        "id": str(i),
        "name": f"Program {i}",
        "agency": f"Agency {i % 5}",
        "value": f"${i * 10}M",
        "score": 60.0 + i,
    }
    for i in range(15)
]


class FakeMobileService:
    """In-memory fake that mirrors MobileService's public interface."""

    def get_dashboard(self):
        hot = sum(1 for c in _SAMPLE_CONTACTS if c["bd_score"] >= 80)
        warm = sum(1 for c in _SAMPLE_CONTACTS if 50 <= c["bd_score"] < 80)
        scores = [c["bd_score"] for c in _SAMPLE_CONTACTS]
        return {
            "pipeline_total": len(_SAMPLE_CONTACTS),
            "hot_leads": hot,
            "warm_leads": warm,
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
            "contacts_total": len(_SAMPLE_CONTACTS),
            "programs_total": len(_SAMPLE_PROGRAMS),
            "recent_alerts": 3,
            "last_updated": datetime.now(UTC).isoformat(),
        }

    def get_contacts(self, query="", limit=20, page=1):
        filtered = _SAMPLE_CONTACTS
        if query:
            q = query.lower()
            filtered = [
                c for c in _SAMPLE_CONTACTS
                if q in c["name"].lower() or q in c["company"].lower()
            ]
        total = len(filtered)
        offset = (page - 1) * limit
        page_items = filtered[offset: offset + limit]
        items = [
            {
                "id": c["id"],
                "name": c["name"],
                "company": c["company"],
                "tier": c["tier"],
                "tier_label": c["tier_label"],
                "phone": c["phone"],
                "email": c["email"],
            }
            for c in page_items
        ]
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": (offset + limit) < total,
        }

    def get_contact_detail(self, contact_id):
        for c in _SAMPLE_CONTACTS:
            if c["id"] == contact_id:
                return {
                    "id": c["id"],
                    "name": c["name"],
                    "company": c["company"],
                    "title": c["title"],
                    "tier": c["tier"],
                    "tier_label": c["tier_label"],
                    "phone": c["phone"],
                    "email": c["email"],
                    "program": c["program"],
                    "last_contacted": c["last_contacted"],
                    "notes": c["notes"],
                }
        return None

    def get_programs(self, limit=20, page=1):
        total = len(_SAMPLE_PROGRAMS)
        offset = (page - 1) * limit
        page_items = _SAMPLE_PROGRAMS[offset: offset + limit]
        items = [
            {
                "id": p["id"],
                "name": p["name"],
                "agency": p["agency"],
                "value": p["value"],
                "score": p["score"],
            }
            for p in page_items
        ]
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": (offset + limit) < total,
        }

    def get_alerts(self, limit=10):
        alerts = [
            {
                "id": str(uuid.uuid4()),
                "type": "new_opportunity",
                "title": f"Hot lead: Contact {i}",
                "summary": f"BD score {80 + i}",
                "created_at": datetime.now(UTC).isoformat(),
                "priority": "high",
            }
            for i in range(min(limit, 5))
        ]
        return {"items": alerts, "total": len(alerts)}

    def search(self, q, limit=10):
        q_lower = q.lower()
        results = []
        for c in _SAMPLE_CONTACTS:
            if q_lower in c["name"].lower() or q_lower in c["company"].lower():
                results.append(
                    {
                        "id": c["id"],
                        "type": "contact",
                        "title": c["name"],
                        "subtitle": c["company"],
                        "score": c["bd_score"],
                    }
                )
            if len(results) >= limit:
                break
        for p in _SAMPLE_PROGRAMS:
            if len(results) >= limit:
                break
            if q_lower in p["name"].lower() or q_lower in p["agency"].lower():
                results.append(
                    {
                        "id": p["id"],
                        "type": "program",
                        "title": p["name"],
                        "subtitle": p["agency"],
                        "score": p["score"],
                    }
                )
        return {"items": results[:limit], "total": len(results), "query": q}


@pytest.fixture(autouse=True)
def _patch_service():
    """Replace the singleton service with a fake for all tests."""
    fake = FakeMobileService()
    mobile_mod._mobile_service = fake
    yield
    mobile_mod._mobile_service = None


@pytest.fixture
def client():
    """FastAPI TestClient with mobile router mounted."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# =========================================================================
# 1. DASHBOARD ENDPOINT (/mobile/dashboard)
# =========================================================================


class TestMobileDashboard:
    def test_dashboard_200(self, client):
        resp = client.get("/mobile/dashboard")
        assert resp.status_code == 200

    def test_dashboard_has_all_fields(self, client):
        data = client.get("/mobile/dashboard").json()
        for field in MobileDashboardResponse.model_fields:
            assert field in data, f"Missing field: {field}"

    def test_dashboard_pipeline_total(self, client):
        data = client.get("/mobile/dashboard").json()
        assert data["pipeline_total"] == len(_SAMPLE_CONTACTS)

    def test_dashboard_hot_leads(self, client):
        data = client.get("/mobile/dashboard").json()
        expected = sum(1 for c in _SAMPLE_CONTACTS if c["bd_score"] >= 80)
        assert data["hot_leads"] == expected

    def test_dashboard_warm_leads(self, client):
        data = client.get("/mobile/dashboard").json()
        expected = sum(1 for c in _SAMPLE_CONTACTS if 50 <= c["bd_score"] < 80)
        assert data["warm_leads"] == expected

    def test_dashboard_avg_score(self, client):
        data = client.get("/mobile/dashboard").json()
        assert isinstance(data["avg_score"], float)
        assert data["avg_score"] > 0

    def test_dashboard_contacts_total(self, client):
        data = client.get("/mobile/dashboard").json()
        assert data["contacts_total"] == len(_SAMPLE_CONTACTS)

    def test_dashboard_programs_total(self, client):
        data = client.get("/mobile/dashboard").json()
        assert data["programs_total"] == len(_SAMPLE_PROGRAMS)

    def test_dashboard_last_updated_is_iso(self, client):
        data = client.get("/mobile/dashboard").json()
        # Should parse as ISO-8601
        assert "T" in data["last_updated"]

    def test_dashboard_cache_control_header(self, client):
        resp = client.get("/mobile/dashboard")
        assert "Cache-Control" in resp.headers
        assert "max-age=" in resp.headers["Cache-Control"]

    def test_dashboard_mobile_optimized_header(self, client):
        resp = client.get("/mobile/dashboard")
        assert resp.headers.get("X-Mobile-Optimized") == "true"

    def test_dashboard_payload_compact(self, client):
        resp = client.get("/mobile/dashboard")
        # Dashboard payload should be well under 5 KB
        assert len(resp.content) < 5120


# =========================================================================
# 2. CONTACTS ENDPOINT (/mobile/contacts)
# =========================================================================


class TestMobileContacts:
    def test_contacts_200(self, client):
        resp = client.get("/mobile/contacts")
        assert resp.status_code == 200

    def test_contacts_default_pagination(self, client):
        data = client.get("/mobile/contacts").json()
        assert data["page"] == 1
        assert data["limit"] == 20
        assert len(data["items"]) <= 20

    def test_contacts_custom_limit(self, client):
        data = client.get("/mobile/contacts", params={"limit": 5}).json()
        assert len(data["items"]) == 5
        assert data["limit"] == 5

    def test_contacts_page_2(self, client):
        data = client.get("/mobile/contacts", params={"limit": 10, "page": 2}).json()
        assert data["page"] == 2
        # Should have items from offset 10
        assert len(data["items"]) <= 10

    def test_contacts_has_more_true(self, client):
        data = client.get("/mobile/contacts", params={"limit": 5, "page": 1}).json()
        assert data["has_more"] is True

    def test_contacts_has_more_false_last_page(self, client):
        data = client.get("/mobile/contacts", params={"limit": 100, "page": 1}).json()
        assert data["has_more"] is False

    def test_contacts_search_filter(self, client):
        data = client.get("/mobile/contacts", params={"query": "Contact 1"}).json()
        assert data["total"] > 0
        for item in data["items"]:
            assert "1" in item["name"]

    def test_contacts_search_no_results(self, client):
        data = client.get("/mobile/contacts", params={"query": "ZZZZNOTFOUND"}).json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_contacts_item_has_required_fields(self, client):
        data = client.get("/mobile/contacts", params={"limit": 1}).json()
        assert len(data["items"]) == 1
        item = data["items"][0]
        for field in ["id", "name", "company", "tier", "tier_label"]:
            assert field in item, f"Missing field: {field}"

    def test_contacts_item_no_heavy_fields(self, client):
        data = client.get("/mobile/contacts", params={"limit": 1}).json()
        item = data["items"][0]
        # Mobile contact list should not include notes, program, etc.
        assert "notes" not in item
        assert "program" not in item

    def test_contacts_cache_header(self, client):
        resp = client.get("/mobile/contacts")
        assert "Cache-Control" in resp.headers

    def test_contacts_total_count(self, client):
        data = client.get("/mobile/contacts").json()
        assert data["total"] == len(_SAMPLE_CONTACTS)


# =========================================================================
# 3. PROGRAMS ENDPOINT (/mobile/programs)
# =========================================================================


class TestMobilePrograms:
    def test_programs_200(self, client):
        resp = client.get("/mobile/programs")
        assert resp.status_code == 200

    def test_programs_default_pagination(self, client):
        data = client.get("/mobile/programs").json()
        assert data["page"] == 1
        assert data["limit"] == 20

    def test_programs_custom_limit(self, client):
        data = client.get("/mobile/programs", params={"limit": 5}).json()
        assert len(data["items"]) == 5

    def test_programs_page_2(self, client):
        data = client.get("/mobile/programs", params={"limit": 5, "page": 2}).json()
        assert data["page"] == 2

    def test_programs_item_fields(self, client):
        data = client.get("/mobile/programs", params={"limit": 1}).json()
        item = data["items"][0]
        for field in ["id", "name", "agency", "value"]:
            assert field in item

    def test_programs_total(self, client):
        data = client.get("/mobile/programs").json()
        assert data["total"] == len(_SAMPLE_PROGRAMS)

    def test_programs_cache_header(self, client):
        resp = client.get("/mobile/programs")
        assert "Cache-Control" in resp.headers


# =========================================================================
# 4. ALERTS ENDPOINT (/mobile/alerts)
# =========================================================================


class TestMobileAlerts:
    def test_alerts_200(self, client):
        resp = client.get("/mobile/alerts")
        assert resp.status_code == 200

    def test_alerts_default_limit(self, client):
        data = client.get("/mobile/alerts").json()
        assert len(data["items"]) <= 10

    def test_alerts_custom_limit(self, client):
        data = client.get("/mobile/alerts", params={"limit": 3}).json()
        assert len(data["items"]) <= 3

    def test_alerts_item_fields(self, client):
        data = client.get("/mobile/alerts").json()
        if data["items"]:
            item = data["items"][0]
            for field in ["id", "type", "title", "summary", "created_at", "priority"]:
                assert field in item

    def test_alerts_priority_values(self, client):
        data = client.get("/mobile/alerts").json()
        for item in data["items"]:
            assert item["priority"] in ("high", "medium", "low")

    def test_alerts_type_values(self, client):
        data = client.get("/mobile/alerts").json()
        valid_types = {"new_opportunity", "score_change", "contact_update", "info"}
        for item in data["items"]:
            assert item["type"] in valid_types

    def test_alerts_cache_header(self, client):
        resp = client.get("/mobile/alerts")
        assert "Cache-Control" in resp.headers


# =========================================================================
# 5. SEARCH ENDPOINT (/mobile/search)
# =========================================================================


class TestMobileSearch:
    def test_search_200(self, client):
        resp = client.get("/mobile/search", params={"q": "Contact"})
        assert resp.status_code == 200

    def test_search_returns_results(self, client):
        data = client.get("/mobile/search", params={"q": "Contact"}).json()
        assert data["total"] > 0
        assert len(data["items"]) > 0

    def test_search_query_echoed(self, client):
        data = client.get("/mobile/search", params={"q": "Program"}).json()
        assert data["query"] == "Program"

    def test_search_limit(self, client):
        data = client.get("/mobile/search", params={"q": "Contact", "limit": 3}).json()
        assert len(data["items"]) <= 3

    def test_search_result_fields(self, client):
        data = client.get("/mobile/search", params={"q": "Contact"}).json()
        item = data["items"][0]
        for field in ["id", "type", "title", "subtitle"]:
            assert field in item

    def test_search_result_type_values(self, client):
        data = client.get("/mobile/search", params={"q": "Contact"}).json()
        for item in data["items"]:
            assert item["type"] in ("contact", "program", "job")

    def test_search_no_results(self, client):
        data = client.get("/mobile/search", params={"q": "ZZZZNOTFOUND"}).json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_search_requires_query(self, client):
        resp = client.get("/mobile/search")
        assert resp.status_code == 422  # Missing required param

    def test_search_cache_header(self, client):
        resp = client.get("/mobile/search", params={"q": "test"})
        assert "Cache-Control" in resp.headers


# =========================================================================
# 6. CONTACT DETAIL ENDPOINT (/mobile/contact/{id})
# =========================================================================


class TestMobileContactDetail:
    def test_contact_detail_200(self, client):
        resp = client.get("/mobile/contact/0")
        assert resp.status_code == 200

    def test_contact_detail_fields(self, client):
        data = client.get("/mobile/contact/0").json()
        for field in MobileContactDetailResponse.model_fields:
            assert field in data, f"Missing field: {field}"

    def test_contact_detail_has_program(self, client):
        data = client.get("/mobile/contact/0").json()
        assert "program" in data

    def test_contact_detail_has_notes(self, client):
        data = client.get("/mobile/contact/0").json()
        assert "notes" in data

    def test_contact_detail_404(self, client):
        resp = client.get("/mobile/contact/nonexistent-id")
        assert resp.status_code == 404

    def test_contact_detail_cache_header(self, client):
        resp = client.get("/mobile/contact/0")
        assert "Cache-Control" in resp.headers


# =========================================================================
# 7. PWA MANIFEST ENDPOINT (/mobile/pwa-manifest)
# =========================================================================


class TestPWAManifest:
    def test_pwa_manifest_200(self, client):
        resp = client.get("/mobile/pwa-manifest")
        assert resp.status_code == 200

    def test_pwa_manifest_name(self, client):
        data = client.get("/mobile/pwa-manifest").json()
        assert data["name"] == "PTS BD Intelligence"

    def test_pwa_manifest_short_name(self, client):
        data = client.get("/mobile/pwa-manifest").json()
        assert data["short_name"] == "PTS BD"

    def test_pwa_manifest_display(self, client):
        data = client.get("/mobile/pwa-manifest").json()
        assert data["display"] == "standalone"

    def test_pwa_manifest_colors(self, client):
        data = client.get("/mobile/pwa-manifest").json()
        assert data["background_color"] == "#1a1a2e"
        assert data["theme_color"] == "#0f3460"

    def test_pwa_manifest_icons(self, client):
        data = client.get("/mobile/pwa-manifest").json()
        assert isinstance(data["icons"], list)
        assert len(data["icons"]) == 2

    def test_pwa_manifest_icon_sizes(self, client):
        data = client.get("/mobile/pwa-manifest").json()
        sizes = {icon["sizes"] for icon in data["icons"]}
        assert "192x192" in sizes
        assert "512x512" in sizes

    def test_pwa_manifest_start_url(self, client):
        data = client.get("/mobile/pwa-manifest").json()
        assert data["start_url"] == "/"

    def test_pwa_manifest_cache_header_long(self, client):
        resp = client.get("/mobile/pwa-manifest")
        assert "Cache-Control" in resp.headers
        # PWA manifest should have long cache (24h)
        assert "86400" in resp.headers["Cache-Control"]

    def test_pwa_manifest_all_fields(self, client):
        data = client.get("/mobile/pwa-manifest").json()
        for field in PWAManifest.model_fields:
            assert field in data


# =========================================================================
# 8. PYDANTIC MODEL VALIDATION
# =========================================================================


class TestMobileModels:
    def test_dashboard_model_defaults(self):
        m = MobileDashboardResponse()
        assert m.pipeline_total == 0
        assert m.hot_leads == 0
        assert m.avg_score == 0.0

    def test_contact_item_model(self):
        m = MobileContactItem(id="1", name="Test", company="Co")
        assert m.tier == 0
        assert m.phone is None

    def test_program_item_model(self):
        m = MobileProgramItem(id="1", name="DCGS", agency="Army")
        assert m.score is None
        assert m.value == ""

    def test_alert_item_model(self):
        m = MobileAlertItem(id="1", type="info", title="Test", summary="s", created_at="2026-01-01", priority="low")
        assert m.priority == "low"

    def test_search_result_model(self):
        m = MobileSearchResult(id="1", type="contact", title="Name")
        assert m.subtitle == ""
        assert m.score is None

    def test_pwa_icon_model(self):
        m = PWAIcon(src="/icon.png", sizes="192x192")
        assert m.type == "image/png"

    def test_pwa_manifest_model_defaults(self):
        m = PWAManifest()
        assert m.display == "standalone"
        assert m.orientation == "any"
        assert m.icons == []

    def test_contact_list_response_model(self):
        m = MobileContactListResponse()
        assert m.items == []
        assert m.total == 0
        assert m.has_more is False

    def test_program_list_response_model(self):
        m = MobileProgramListResponse(
            items=[MobileProgramItem(id="1", name="P", agency="A")],
            total=1,
        )
        assert len(m.items) == 1

    def test_alert_list_response_model(self):
        m = MobileAlertListResponse()
        assert m.items == []
        assert m.total == 0

    def test_search_response_model(self):
        m = MobileSearchResponse(query="test")
        assert m.query == "test"
        assert m.items == []


# =========================================================================
# 9. CROSS-CUTTING: CACHE HEADERS ON ALL ENDPOINTS
# =========================================================================


class TestCacheHeaders:
    """Verify every endpoint returns proper cache-control headers."""

    ENDPOINTS = [
        "/mobile/dashboard",
        "/mobile/contacts",
        "/mobile/programs",
        "/mobile/alerts",
        "/mobile/search?q=test",
        "/mobile/contact/0",
        "/mobile/pwa-manifest",
    ]

    @pytest.mark.parametrize("url", ENDPOINTS)
    def test_cache_control_present(self, client, url):
        resp = client.get(url)
        assert "Cache-Control" in resp.headers

    @pytest.mark.parametrize("url", ENDPOINTS)
    def test_mobile_optimized_header(self, client, url):
        resp = client.get(url)
        assert resp.headers.get("X-Mobile-Optimized") == "true"
