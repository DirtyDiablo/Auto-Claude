"""
Comprehensive tests for Feature 23 — Automated Weekly Intelligence Briefs.

Tests BriefSection, IntelligenceBrief, BriefTemplateEngine, BriefDeliveryService,
and the /briefs/* API router endpoints.
"""

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

import pytest

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine8_Knowledge.briefs.template_engine import (
    BriefSection,
    BriefTemplateEngine,
    IntelligenceBrief,
)
from Engine8_Knowledge.briefs.delivery import BriefDeliveryService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_section() -> BriefSection:
    return BriefSection(
        title="Test Section",
        content="Some test content here.",
        data={"key": "value", "count": 42},
        priority="high",
    )


@pytest.fixture
def sample_sections() -> list:
    return [
        BriefSection(
            title="New Opportunities",
            content="5 new postings found.",
            data={"scraped": 5, "mapped": 3},
            priority="high",
        ),
        BriefSection(
            title="Scoring Changes",
            content="2 hot opportunities.",
            data={"hot_count": 2, "warm_count": 5, "total_scored": 20, "hot_percentage": 10.0},
            priority="medium",
        ),
        BriefSection(
            title="Pipeline Status",
            content="Pipeline healthy.",
            data={"stages": {}, "total": 100, "velocity": 14.3},
            priority="medium",
        ),
        BriefSection(
            title="Contact Activity",
            content="7000 contacts tracked.",
            data={"total_contacts": 7000, "tier_distribution": {}},
            priority="low",
        ),
        BriefSection(
            title="Competitive Intelligence",
            content="Leidos leading.",
            data={"top_competitor": "Leidos", "competitor_count": 4},
            priority="high",
        ),
    ]


@pytest.fixture
def sample_brief(sample_sections) -> IntelligenceBrief:
    return IntelligenceBrief(
        id="test-brief-001",
        title="Weekly Intelligence Brief - DCGS Portfolio",
        period_start="2026-02-14",
        period_end="2026-02-21",
        generated_at="2026-02-21T08:00:00+00:00",
        sections=sample_sections,
        executive_summary="5 new opportunities discovered. 2 hot-scored opportunities.",
        portfolio="dcgs",
    )


@pytest.fixture
def engine() -> BriefTemplateEngine:
    return BriefTemplateEngine()


@pytest.fixture
def tmp_storage(tmp_path) -> Path:
    storage = tmp_path / "briefs"
    storage.mkdir()
    return storage


@pytest.fixture
def delivery(tmp_storage) -> BriefDeliveryService:
    return BriefDeliveryService(storage_dir=tmp_storage)


@pytest.fixture
def stored_brief(delivery, sample_brief) -> IntelligenceBrief:
    """A brief that has been stored via the delivery service."""
    delivery.store_brief(sample_brief)
    return sample_brief


# ---------------------------------------------------------------------------
# BriefSection Tests
# ---------------------------------------------------------------------------


class TestBriefSection:
    """Tests for BriefSection dataclass."""

    def test_creation_with_all_fields(self, sample_section):
        assert sample_section.title == "Test Section"
        assert sample_section.content == "Some test content here."
        assert sample_section.data == {"key": "value", "count": 42}
        assert sample_section.priority == "high"

    def test_default_priority(self):
        section = BriefSection(title="T", content="C", data={})
        assert section.priority == "medium"

    def test_to_dict(self, sample_section):
        d = sample_section.to_dict()
        assert isinstance(d, dict)
        assert d["title"] == "Test Section"
        assert d["priority"] == "high"
        assert d["data"]["count"] == 42

    def test_to_dict_contains_all_keys(self, sample_section):
        d = sample_section.to_dict()
        assert set(d.keys()) == {"title", "content", "data", "priority"}

    def test_priority_values(self):
        for prio in ("high", "medium", "low"):
            s = BriefSection(title="T", content="C", data={}, priority=prio)
            assert s.priority == prio

    def test_empty_data_dict(self):
        s = BriefSection(title="T", content="C", data={})
        assert s.data == {}
        assert s.to_dict()["data"] == {}

    def test_nested_data(self):
        s = BriefSection(title="T", content="C", data={"nested": {"a": 1}})
        assert s.data["nested"]["a"] == 1


# ---------------------------------------------------------------------------
# IntelligenceBrief Tests
# ---------------------------------------------------------------------------


class TestIntelligenceBrief:
    """Tests for IntelligenceBrief dataclass."""

    def test_creation_with_all_fields(self, sample_brief):
        assert sample_brief.id == "test-brief-001"
        assert sample_brief.title == "Weekly Intelligence Brief - DCGS Portfolio"
        assert sample_brief.period_start == "2026-02-14"
        assert sample_brief.period_end == "2026-02-21"
        assert sample_brief.generated_at == "2026-02-21T08:00:00+00:00"
        assert sample_brief.portfolio == "dcgs"
        assert len(sample_brief.sections) == 5

    def test_executive_summary_populated(self, sample_brief):
        assert sample_brief.executive_summary
        assert len(sample_brief.executive_summary) > 10

    def test_to_dict_returns_dict(self, sample_brief):
        d = sample_brief.to_dict()
        assert isinstance(d, dict)

    def test_to_dict_has_required_keys(self, sample_brief):
        d = sample_brief.to_dict()
        required = {
            "id", "title", "period_start", "period_end",
            "generated_at", "sections", "executive_summary", "portfolio",
        }
        assert required <= set(d.keys())

    def test_to_dict_sections_are_dicts(self, sample_brief):
        d = sample_brief.to_dict()
        assert isinstance(d["sections"], list)
        for s in d["sections"]:
            assert isinstance(s, dict)
            assert "title" in s

    def test_to_dict_roundtrip(self, sample_brief):
        d = sample_brief.to_dict()
        restored = IntelligenceBrief.from_dict(d)
        assert restored.id == sample_brief.id
        assert restored.title == sample_brief.title
        assert restored.portfolio == sample_brief.portfolio
        assert len(restored.sections) == len(sample_brief.sections)
        assert restored.executive_summary == sample_brief.executive_summary

    def test_from_dict_sections_restored(self, sample_brief):
        d = sample_brief.to_dict()
        restored = IntelligenceBrief.from_dict(d)
        for orig, rest in zip(sample_brief.sections, restored.sections):
            assert orig.title == rest.title
            assert orig.priority == rest.priority

    def test_to_dict_json_serializable(self, sample_brief):
        d = sample_brief.to_dict()
        serialized = json.dumps(d)
        assert isinstance(serialized, str)
        assert json.loads(serialized) == d

    # ---- HTML output ----

    def test_to_html_returns_string(self, sample_brief):
        html = sample_brief.to_html()
        assert isinstance(html, str)

    def test_to_html_contains_doctype(self, sample_brief):
        html = sample_brief.to_html()
        assert html.startswith("<!DOCTYPE html>")

    def test_to_html_contains_title(self, sample_brief):
        html = sample_brief.to_html()
        assert "Weekly Intelligence Brief" in html

    def test_to_html_contains_all_section_titles(self, sample_brief):
        html = sample_brief.to_html()
        for section in sample_brief.sections:
            assert section.title in html

    def test_to_html_contains_executive_summary(self, sample_brief):
        html = sample_brief.to_html()
        assert "Executive Summary" in html
        assert "new opportunities" in html

    def test_to_html_contains_period(self, sample_brief):
        html = sample_brief.to_html()
        assert "2026-02-14" in html
        assert "2026-02-21" in html

    def test_to_html_contains_portfolio(self, sample_brief):
        html = sample_brief.to_html()
        assert "dcgs" in html

    def test_to_html_priority_labels(self, sample_brief):
        html = sample_brief.to_html()
        assert "[HIGH]" in html
        assert "[MEDIUM]" in html
        assert "[LOW]" in html

    def test_to_html_escapes_special_chars(self):
        brief = IntelligenceBrief(
            id="esc-test",
            title='Brief with <script> & "quotes"',
            period_start="2026-01-01",
            period_end="2026-01-07",
            generated_at="2026-01-07T00:00:00",
            sections=[],
            executive_summary="Test <b>bold</b> & more",
            portfolio="test",
        )
        html = brief.to_html()
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
        assert "&amp;" in html

    # ---- Markdown output ----

    def test_to_markdown_returns_string(self, sample_brief):
        md = sample_brief.to_markdown()
        assert isinstance(md, str)

    def test_to_markdown_starts_with_heading(self, sample_brief):
        md = sample_brief.to_markdown()
        assert md.startswith("# Weekly Intelligence Brief")

    def test_to_markdown_contains_portfolio(self, sample_brief):
        md = sample_brief.to_markdown()
        assert "dcgs" in md

    def test_to_markdown_contains_section_headings(self, sample_brief):
        md = sample_brief.to_markdown()
        for section in sample_brief.sections:
            assert f"## {section.title}" in md

    def test_to_markdown_contains_priority_tags(self, sample_brief):
        md = sample_brief.to_markdown()
        assert "[HIGH]" in md
        assert "[MEDIUM]" in md
        assert "[LOW]" in md

    def test_to_markdown_contains_dates(self, sample_brief):
        md = sample_brief.to_markdown()
        assert "2026-02-14" in md
        assert "2026-02-21" in md

    def test_to_markdown_contains_executive_summary(self, sample_brief):
        md = sample_brief.to_markdown()
        assert "## Executive Summary" in md


# ---------------------------------------------------------------------------
# BriefTemplateEngine Tests
# ---------------------------------------------------------------------------


class TestBriefTemplateEngine:
    """Tests for the template engine that generates briefs."""

    def test_generate_brief_returns_intelligence_brief(self, engine):
        brief = engine.generate_brief()
        assert isinstance(brief, IntelligenceBrief)

    def test_generate_brief_has_id(self, engine):
        brief = engine.generate_brief()
        assert brief.id
        assert len(brief.id) > 10  # UUID

    def test_generate_brief_has_title(self, engine):
        brief = engine.generate_brief()
        assert "Intelligence Brief" in brief.title

    def test_generate_brief_default_portfolio(self, engine):
        brief = engine.generate_brief()
        assert brief.portfolio == "dcgs"

    def test_generate_brief_custom_portfolio(self, engine):
        brief = engine.generate_brief(portfolio_id="cyber")
        assert brief.portfolio == "cyber"

    def test_generate_brief_has_5_sections(self, engine):
        brief = engine.generate_brief()
        assert len(brief.sections) == 5

    def test_generate_brief_section_titles(self, engine):
        brief = engine.generate_brief()
        titles = [s.title for s in brief.sections]
        assert "New Opportunities" in titles
        assert "Scoring Changes" in titles
        assert "Pipeline Status" in titles
        assert "Contact Activity" in titles
        assert "Competitive Intelligence" in titles

    def test_generate_brief_executive_summary_populated(self, engine):
        brief = engine.generate_brief()
        assert brief.executive_summary
        assert len(brief.executive_summary) > 20

    def test_generate_brief_period_dates_correct(self, engine):
        brief = engine.generate_brief(period_days=7)
        start = datetime.strptime(brief.period_start, "%Y-%m-%d")
        end = datetime.strptime(brief.period_end, "%Y-%m-%d")
        delta = (end - start).days
        assert delta == 7

    def test_generate_brief_custom_period(self, engine):
        brief = engine.generate_brief(period_days=30)
        start = datetime.strptime(brief.period_start, "%Y-%m-%d")
        end = datetime.strptime(brief.period_end, "%Y-%m-%d")
        assert (end - start).days == 30

    def test_generate_brief_generated_at_is_iso(self, engine):
        brief = engine.generate_brief()
        # Should parse without error
        dt = datetime.fromisoformat(brief.generated_at)
        assert dt.year >= 2026

    def test_generate_brief_sections_have_content(self, engine):
        brief = engine.generate_brief()
        for section in brief.sections:
            assert section.content
            assert len(section.content) > 10

    def test_generate_brief_sections_have_data(self, engine):
        brief = engine.generate_brief()
        for section in brief.sections:
            assert isinstance(section.data, dict)

    def test_generate_brief_sections_have_valid_priority(self, engine):
        brief = engine.generate_brief()
        for section in brief.sections:
            assert section.priority in ("high", "medium", "low")

    def test_generate_brief_unique_ids(self, engine):
        b1 = engine.generate_brief()
        b2 = engine.generate_brief()
        assert b1.id != b2.id

    def test_executive_summary_mentions_high_priority(self, engine):
        brief = engine.generate_brief()
        # The synthetic data should produce at least one high-priority section
        high_sections = [s for s in brief.sections if s.priority == "high"]
        if high_sections:
            assert "high priority" in brief.executive_summary


# ---------------------------------------------------------------------------
# BriefDeliveryService Tests
# ---------------------------------------------------------------------------


class TestBriefDeliveryService:
    """Tests for brief storage and delivery."""

    def test_store_brief_returns_path(self, delivery, sample_brief):
        path = delivery.store_brief(sample_brief)
        assert path
        assert Path(path).exists()

    def test_store_brief_creates_json_file(self, delivery, sample_brief):
        path = delivery.store_brief(sample_brief)
        assert path.endswith(".json")
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data["id"] == sample_brief.id

    def test_store_brief_file_content(self, delivery, sample_brief):
        path = delivery.store_brief(sample_brief)
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data["title"] == sample_brief.title
        assert data["portfolio"] == "dcgs"
        assert len(data["sections"]) == 5

    def test_get_brief_existing(self, delivery, stored_brief):
        result = delivery.get_brief(stored_brief.id)
        assert result is not None
        assert result.id == stored_brief.id
        assert result.title == stored_brief.title

    def test_get_brief_nonexistent(self, delivery):
        result = delivery.get_brief("nonexistent-id")
        assert result is None

    def test_list_briefs_empty(self, delivery):
        result = delivery.list_briefs()
        assert result == []

    def test_list_briefs_after_store(self, delivery, stored_brief):
        result = delivery.list_briefs()
        assert len(result) == 1
        assert result[0]["id"] == stored_brief.id

    def test_list_briefs_summary_keys(self, delivery, stored_brief):
        result = delivery.list_briefs()
        entry = result[0]
        assert "id" in entry
        assert "title" in entry
        assert "portfolio" in entry
        assert "period_start" in entry
        assert "period_end" in entry
        assert "generated_at" in entry
        assert "section_count" in entry

    def test_list_briefs_portfolio_filter(self, delivery, sample_sections):
        b1 = IntelligenceBrief(
            id="dcgs-1", title="DCGS Brief", period_start="2026-02-01",
            period_end="2026-02-07", generated_at="2026-02-07T00:00:00",
            sections=sample_sections, executive_summary="Summary", portfolio="dcgs",
        )
        b2 = IntelligenceBrief(
            id="cyber-1", title="Cyber Brief", period_start="2026-02-01",
            period_end="2026-02-07", generated_at="2026-02-07T00:00:00",
            sections=sample_sections, executive_summary="Summary", portfolio="cyber",
        )
        delivery.store_brief(b1)
        delivery.store_brief(b2)

        dcgs_only = delivery.list_briefs(portfolio_id="dcgs")
        assert len(dcgs_only) == 1
        assert dcgs_only[0]["portfolio"] == "dcgs"

        cyber_only = delivery.list_briefs(portfolio_id="cyber")
        assert len(cyber_only) == 1
        assert cyber_only[0]["portfolio"] == "cyber"

    def test_list_briefs_limit(self, delivery, sample_sections):
        for i in range(5):
            b = IntelligenceBrief(
                id=f"brief-{i}", title=f"Brief {i}", period_start="2026-02-01",
                period_end="2026-02-07", generated_at=f"2026-02-07T0{i}:00:00",
                sections=sample_sections, executive_summary="S", portfolio="dcgs",
            )
            delivery.store_brief(b)

        result = delivery.list_briefs(limit=3)
        assert len(result) == 3

    def test_list_briefs_all(self, delivery, sample_sections):
        for i in range(5):
            b = IntelligenceBrief(
                id=f"brief-{i}", title=f"Brief {i}", period_start="2026-02-01",
                period_end="2026-02-07", generated_at=f"2026-02-07T0{i}:00:00",
                sections=sample_sections, executive_summary="S", portfolio="dcgs",
            )
            delivery.store_brief(b)

        result = delivery.list_briefs(limit=100)
        assert len(result) == 5

    def test_deliver_email_returns_status(self, delivery, sample_brief):
        result = delivery.deliver_email(sample_brief, ["test@example.com"])
        assert result["status"] == "stub"
        assert "brief_id" in result
        assert result["brief_id"] == sample_brief.id

    def test_deliver_email_includes_recipients(self, delivery, sample_brief):
        recipients = ["a@test.com", "b@test.com"]
        result = delivery.deliver_email(sample_brief, recipients)
        assert result["recipients"] == recipients

    def test_deliver_email_includes_subject(self, delivery, sample_brief):
        result = delivery.deliver_email(sample_brief, ["x@test.com"])
        assert result["would_send_subject"] == sample_brief.title

    def test_deliver_email_has_timestamp(self, delivery, sample_brief):
        result = delivery.deliver_email(sample_brief, ["x@test.com"])
        assert "timestamp" in result
        # Should be parseable ISO datetime
        datetime.fromisoformat(result["timestamp"])

    # ---- Schedule ----

    def test_get_schedule_default_disabled(self, delivery):
        sched = delivery.get_schedule()
        assert sched["enabled"] is False
        assert "disabled" in sched["description"].lower()

    def test_toggle_schedule_enables(self, delivery):
        result = delivery.toggle_schedule(enabled=True)
        assert result["enabled"] is True

    def test_toggle_schedule_disables(self, delivery):
        delivery.toggle_schedule(enabled=True)
        result = delivery.toggle_schedule(enabled=False)
        assert result["enabled"] is False

    def test_toggle_schedule_flip(self, delivery):
        assert delivery.get_schedule()["enabled"] is False
        delivery.toggle_schedule()  # flip to True
        assert delivery.get_schedule()["enabled"] is True
        delivery.toggle_schedule()  # flip back to False
        assert delivery.get_schedule()["enabled"] is False

    def test_schedule_has_day_and_hour(self, delivery):
        sched = delivery.get_schedule()
        assert "day" in sched
        assert "hour" in sched
        assert isinstance(sched["hour"], int)


# ---------------------------------------------------------------------------
# API Router Tests (using FastAPI TestClient)
# ---------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path):
    """FastAPI TestClient with Briefs router mounted, using temp storage."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import Engine8_Knowledge.routers.briefs as briefs_mod

    # Reset singletons so each test gets fresh state
    briefs_mod._engine = None
    briefs_mod._delivery = None

    app = FastAPI()

    from Engine8_Knowledge.routers.briefs import router
    app.include_router(router)

    c = TestClient(app)

    # Patch delivery to use temp storage
    delivery = briefs_mod._get_delivery()
    delivery._storage_dir = tmp_path / "briefs"
    delivery._storage_dir.mkdir(parents=True, exist_ok=True)

    return c


class TestBriefsEndpoints:
    """Tests for /briefs/* API endpoints."""

    def test_generate_brief_200(self, client):
        resp = client.post("/briefs/generate", json={"portfolio_id": "dcgs", "period_days": 7})
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "sections" in data
        assert len(data["sections"]) == 5

    def test_generate_brief_stores_it(self, client):
        resp = client.post("/briefs/generate", json={})
        assert resp.status_code == 200
        brief_id = resp.json()["id"]

        # Should be retrievable
        get_resp = client.get(f"/briefs/{brief_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == brief_id

    def test_generate_brief_default_params(self, client):
        resp = client.post("/briefs/generate", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["portfolio"] == "dcgs"

    def test_generate_brief_custom_portfolio(self, client):
        resp = client.post("/briefs/generate", json={"portfolio_id": "cyber"})
        assert resp.status_code == 200
        assert resp.json()["portfolio"] == "cyber"

    def test_list_briefs_empty(self, client):
        resp = client.get("/briefs")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_briefs_after_generate(self, client):
        client.post("/briefs/generate", json={})
        resp = client.get("/briefs")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_briefs_with_portfolio_filter(self, client):
        client.post("/briefs/generate", json={"portfolio_id": "dcgs"})
        client.post("/briefs/generate", json={"portfolio_id": "cyber"})

        resp = client.get("/briefs", params={"portfolio_id": "dcgs"})
        assert resp.status_code == 200
        briefs = resp.json()
        assert all(b["portfolio"] == "dcgs" for b in briefs)

    def test_get_brief_200(self, client):
        gen = client.post("/briefs/generate", json={})
        brief_id = gen.json()["id"]

        resp = client.get(f"/briefs/{brief_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == brief_id

    def test_get_brief_404(self, client):
        resp = client.get("/briefs/nonexistent-id")
        assert resp.status_code == 404

    def test_get_brief_html_200(self, client):
        gen = client.post("/briefs/generate", json={})
        brief_id = gen.json()["id"]

        resp = client.get(f"/briefs/{brief_id}/html")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "<!DOCTYPE html>" in resp.text

    def test_get_brief_html_contains_sections(self, client):
        gen = client.post("/briefs/generate", json={})
        brief_id = gen.json()["id"]

        resp = client.get(f"/briefs/{brief_id}/html")
        assert "New Opportunities" in resp.text
        assert "Scoring Changes" in resp.text

    def test_get_brief_html_404(self, client):
        resp = client.get("/briefs/nonexistent/html")
        assert resp.status_code == 404

    def test_get_brief_markdown_200(self, client):
        gen = client.post("/briefs/generate", json={})
        brief_id = gen.json()["id"]

        resp = client.get(f"/briefs/{brief_id}/markdown")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        assert resp.text.startswith("# Weekly Intelligence Brief")

    def test_get_brief_markdown_contains_sections(self, client):
        gen = client.post("/briefs/generate", json={})
        brief_id = gen.json()["id"]

        resp = client.get(f"/briefs/{brief_id}/markdown")
        assert "## New Opportunities" in resp.text
        assert "## Pipeline Status" in resp.text

    def test_get_brief_markdown_404(self, client):
        resp = client.get("/briefs/nonexistent/markdown")
        assert resp.status_code == 404

    def test_deliver_brief_200(self, client):
        gen = client.post("/briefs/generate", json={})
        brief_id = gen.json()["id"]

        resp = client.post(
            f"/briefs/{brief_id}/deliver",
            json={"recipients": ["user@example.com"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "stub"
        assert data["brief_id"] == brief_id

    def test_deliver_brief_404(self, client):
        resp = client.post(
            "/briefs/nonexistent/deliver",
            json={"recipients": ["x@test.com"]},
        )
        assert resp.status_code == 404

    def test_deliver_brief_multiple_recipients(self, client):
        gen = client.post("/briefs/generate", json={})
        brief_id = gen.json()["id"]

        recipients = ["a@test.com", "b@test.com", "c@test.com"]
        resp = client.post(
            f"/briefs/{brief_id}/deliver",
            json={"recipients": recipients},
        )
        assert resp.status_code == 200
        assert resp.json()["recipients"] == recipients

    def test_schedule_get_200(self, client):
        resp = client.get("/briefs/schedule")
        assert resp.status_code == 200
        data = resp.json()
        assert "enabled" in data
        assert "day" in data
        assert "hour" in data
        assert "description" in data

    def test_schedule_default_disabled(self, client):
        resp = client.get("/briefs/schedule")
        assert resp.json()["enabled"] is False

    def test_schedule_toggle_200(self, client):
        resp = client.post("/briefs/schedule/toggle", json={"enabled": True})
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

    def test_schedule_toggle_flip(self, client):
        client.post("/briefs/schedule/toggle", json={"enabled": True})
        resp = client.post("/briefs/schedule/toggle", json={})
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

    def test_generate_response_json_serializable(self, client):
        resp = client.post("/briefs/generate", json={})
        assert resp.headers["content-type"] == "application/json"
        data = resp.json()
        assert isinstance(data, dict)

    def test_list_response_json(self, client):
        resp = client.get("/briefs")
        assert resp.headers["content-type"] == "application/json"

    def test_generate_unknown_portfolio(self, client):
        resp = client.post("/briefs/generate", json={"portfolio_id": "nonexistent_xyz"})
        assert resp.status_code == 200  # Should still work with fallback name
        assert resp.json()["portfolio"] == "nonexistent_xyz"

    def test_generate_period_1_day(self, client):
        resp = client.post("/briefs/generate", json={"period_days": 1})
        assert resp.status_code == 200
        data = resp.json()
        start = datetime.strptime(data["period_start"], "%Y-%m-%d")
        end = datetime.strptime(data["period_end"], "%Y-%m-%d")
        assert (end - start).days == 1
