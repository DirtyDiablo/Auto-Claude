"""
Comprehensive tests for Feature 18 — Executive BD Intelligence Dashboard.

Tests KPIService methods and KPI API router endpoints.
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine8_Knowledge.services.kpi_service import (
    HOT_THRESHOLD,
    WARM_THRESHOLD,
    KPIService,
    _default_date_range,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def kpi_service():
    """KPIService with a non-existent DB path (forces synthetic data)."""
    return KPIService(bullhorn_db_path="/tmp/nonexistent_test.db")


@pytest.fixture
def today_str():
    return datetime.utcnow().strftime("%Y-%m-%d")


@pytest.fixture
def thirty_days_ago_str():
    return (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# _default_date_range
# ---------------------------------------------------------------------------


class TestDefaultDateRange:
    """Tests for the date range default helper."""

    def test_both_none_defaults_to_last_30_days(self):
        start, end = _default_date_range(None, None)
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        assert (end_dt - start_dt).days == 30

    def test_end_none_defaults_to_today(self):
        _, end = _default_date_range("2026-01-01", None)
        assert end == datetime.now(UTC).strftime("%Y-%m-%d")

    def test_start_none_defaults_to_30_before_end(self):
        start, end = _default_date_range(None, "2026-02-20")
        assert end == "2026-02-20"
        assert start == "2026-01-21"

    def test_explicit_dates_pass_through(self):
        start, end = _default_date_range("2025-06-01", "2025-06-30")
        assert start == "2025-06-01"
        assert end == "2025-06-30"


# ---------------------------------------------------------------------------
# KPIService Instantiation
# ---------------------------------------------------------------------------


class TestKPIServiceInit:
    """Tests for KPIService initialization."""

    def test_init_with_custom_path(self):
        svc = KPIService(bullhorn_db_path="/some/path.db")
        assert svc._db_path == Path("/some/path.db")

    def test_init_default_path(self):
        svc = KPIService()
        assert "bullhorn.db" in str(svc._db_path)

    def test_db_connection_returns_none_for_missing_db(self, kpi_service):
        conn = kpi_service._get_db_connection()
        assert conn is None

    def test_query_db_returns_empty_for_missing_db(self, kpi_service):
        result = kpi_service._query_db("SELECT 1")
        assert result == []


# ---------------------------------------------------------------------------
# Safe Division
# ---------------------------------------------------------------------------


class TestSafeDivision:
    """Tests for division-by-zero handling."""

    def test_normal_division(self, kpi_service):
        assert kpi_service._safe_division(10, 4) == 2.5

    def test_zero_denominator_returns_zero(self, kpi_service):
        assert kpi_service._safe_division(10, 0) == 0.0

    def test_zero_numerator(self, kpi_service):
        assert kpi_service._safe_division(0, 5) == 0.0

    def test_both_zero(self, kpi_service):
        assert kpi_service._safe_division(0, 0) == 0.0

    def test_result_rounded_to_4_decimals(self, kpi_service):
        result = kpi_service._safe_division(1, 3)
        assert result == round(1 / 3, 4)


# ---------------------------------------------------------------------------
# Pipeline Velocity
# ---------------------------------------------------------------------------


class TestPipelineVelocity:
    """Tests for pipeline velocity metrics."""

    def test_returns_required_keys(self, kpi_service):
        result = kpi_service.pipeline_velocity()
        assert "period" in result
        assert "stages" in result
        assert "total_processed" in result
        assert "velocity_per_day" in result
        assert "data_source" in result

    def test_period_has_start_and_end(self, kpi_service):
        result = kpi_service.pipeline_velocity()
        assert "start_date" in result["period"]
        assert "end_date" in result["period"]

    def test_synthetic_data_when_no_db(self, kpi_service):
        result = kpi_service.pipeline_velocity()
        assert result["data_source"] == "synthetic"
        assert result["total_processed"] > 0

    def test_stages_contain_expected_keys(self, kpi_service):
        result = kpi_service.pipeline_velocity()
        stages = result["stages"]
        assert "Scraped" in stages
        assert "Mapped" in stages
        assert "Scored" in stages
        assert "Submitted" in stages
        assert "Won" in stages

    def test_total_matches_stage_sum(self, kpi_service):
        result = kpi_service.pipeline_velocity()
        assert result["total_processed"] == sum(result["stages"].values())

    def test_explicit_date_range(self, kpi_service):
        result = kpi_service.pipeline_velocity("2026-01-01", "2026-01-31")
        assert result["period"]["start_date"] == "2026-01-01"
        assert result["period"]["end_date"] == "2026-01-31"

    def test_velocity_per_day_positive(self, kpi_service):
        result = kpi_service.pipeline_velocity()
        assert result["velocity_per_day"] > 0

    def test_velocity_calculation_correctness(self, kpi_service):
        result = kpi_service.pipeline_velocity("2026-01-01", "2026-01-31")
        expected = kpi_service._safe_division(result["total_processed"], 30)
        assert result["velocity_per_day"] == expected


# ---------------------------------------------------------------------------
# Win Rate Analysis
# ---------------------------------------------------------------------------


class TestWinRateAnalysis:
    """Tests for win rate calculations."""

    def test_returns_required_keys(self, kpi_service):
        result = kpi_service.win_rate_analysis()
        assert "period" in result
        assert "overall" in result
        assert "by_program" in result
        assert "by_company" in result
        assert "by_clearance" in result
        assert "data_source" in result

    def test_overall_has_rate(self, kpi_service):
        result = kpi_service.win_rate_analysis()
        overall = result["overall"]
        assert "total_submitted" in overall
        assert "won" in overall
        assert "rate" in overall

    def test_rate_between_0_and_1(self, kpi_service):
        result = kpi_service.win_rate_analysis()
        assert 0.0 <= result["overall"]["rate"] <= 1.0

    def test_by_program_contains_dcgs(self, kpi_service):
        result = kpi_service.win_rate_analysis()
        programs = result["by_program"]
        assert any("DCGS" in p for p in programs)

    def test_by_company_has_entries(self, kpi_service):
        result = kpi_service.win_rate_analysis()
        assert len(result["by_company"]) > 0

    def test_by_clearance_has_entries(self, kpi_service):
        result = kpi_service.win_rate_analysis()
        assert len(result["by_clearance"]) > 0

    def test_each_breakdown_has_rate(self, kpi_service):
        result = kpi_service.win_rate_analysis()
        for detail in result["by_program"].values():
            assert "rate" in detail
            assert "submitted" in detail
            assert "won" in detail


# ---------------------------------------------------------------------------
# Conversion Funnel
# ---------------------------------------------------------------------------


class TestConversionFunnel:
    """Tests for the stage-by-stage conversion funnel."""

    def test_returns_required_keys(self, kpi_service):
        result = kpi_service.conversion_funnel()
        assert "period" in result
        assert "funnel" in result
        assert "overall_conversion" in result
        assert "total_scraped" in result
        assert "total_won" in result

    def test_funnel_has_five_stages(self, kpi_service):
        result = kpi_service.conversion_funnel()
        assert len(result["funnel"]) == 5

    def test_funnel_stage_names_ordered(self, kpi_service):
        result = kpi_service.conversion_funnel()
        names = [s["stage"] for s in result["funnel"]]
        assert names == ["Scraped", "Mapped", "Scored", "Submitted", "Won"]

    def test_first_stage_conversion_is_one(self, kpi_service):
        result = kpi_service.conversion_funnel()
        assert result["funnel"][0]["conversion_rate"] == 1.0

    def test_subsequent_stages_have_valid_rates(self, kpi_service):
        result = kpi_service.conversion_funnel()
        for stage in result["funnel"][1:]:
            assert 0.0 <= stage["conversion_rate"] <= 1.0

    def test_drop_off_non_negative(self, kpi_service):
        result = kpi_service.conversion_funnel()
        for stage in result["funnel"]:
            assert stage["drop_off"] >= 0

    def test_overall_conversion_matches(self, kpi_service):
        result = kpi_service.conversion_funnel()
        expected = kpi_service._safe_division(
            result["total_won"], result["total_scraped"]
        )
        assert result["overall_conversion"] == expected

    def test_total_scraped_equals_first_stage(self, kpi_service):
        result = kpi_service.conversion_funnel()
        assert result["total_scraped"] == result["funnel"][0]["count"]

    def test_total_won_equals_last_stage(self, kpi_service):
        result = kpi_service.conversion_funnel()
        assert result["total_won"] == result["funnel"][-1]["count"]


# ---------------------------------------------------------------------------
# Competitive Landscape
# ---------------------------------------------------------------------------


class TestCompetitiveLandscape:
    """Tests for competitor positioning metrics."""

    def test_returns_required_keys(self, kpi_service):
        result = kpi_service.competitive_landscape()
        assert "competitors" in result
        assert "total_market_positions" in result
        assert "top_competitor" in result
        assert "data_source" in result

    def test_competitors_list_not_empty(self, kpi_service):
        result = kpi_service.competitive_landscape()
        assert len(result["competitors"]) > 0

    def test_competitor_entry_structure(self, kpi_service):
        result = kpi_service.competitive_landscape()
        entry = result["competitors"][0]
        assert "company" in entry
        assert "job_count" in entry
        assert "market_share" in entry
        assert "trend" in entry

    def test_top_competitor_is_first(self, kpi_service):
        result = kpi_service.competitive_landscape()
        assert result["top_competitor"] == result["competitors"][0]["company"]

    def test_total_market_positions_matches_sum(self, kpi_service):
        result = kpi_service.competitive_landscape()
        total = sum(c["job_count"] for c in result["competitors"])
        assert result["total_market_positions"] == total

    def test_program_filter_included_when_specified(self, kpi_service):
        result = kpi_service.competitive_landscape(program="DCGS")
        assert result.get("program_filter") == "DCGS"

    def test_no_program_filter_when_none(self, kpi_service):
        result = kpi_service.competitive_landscape()
        assert "program_filter" not in result

    def test_market_share_between_0_and_1(self, kpi_service):
        result = kpi_service.competitive_landscape()
        for c in result["competitors"]:
            assert 0.0 <= c["market_share"] <= 1.0


# ---------------------------------------------------------------------------
# Contact Engagement
# ---------------------------------------------------------------------------


class TestContactEngagement:
    """Tests for contact engagement metrics."""

    def test_returns_required_keys(self, kpi_service):
        result = kpi_service.contact_engagement()
        assert "period" in result
        assert "total_contacts" in result
        assert "tier_distribution" in result
        assert "engagement_rates" in result
        assert "response_rates" in result
        assert "highest_engagement_tier" in result

    def test_total_contacts_positive(self, kpi_service):
        result = kpi_service.contact_engagement()
        assert result["total_contacts"] > 0

    def test_six_tiers_in_distribution(self, kpi_service):
        result = kpi_service.contact_engagement()
        assert len(result["tier_distribution"]) == 6

    def test_tier_names_follow_convention(self, kpi_service):
        result = kpi_service.contact_engagement()
        expected_tiers = [
            "tier_1_executive",
            "tier_2_director",
            "tier_3_program_lead",
            "tier_4_management",
            "tier_5_senior_ic",
            "tier_6_ic",
        ]
        for tier in expected_tiers:
            assert tier in result["tier_distribution"]

    def test_engagement_rates_between_0_and_1(self, kpi_service):
        result = kpi_service.contact_engagement()
        for rate in result["engagement_rates"].values():
            assert 0.0 <= rate <= 1.0

    def test_response_rates_have_channels(self, kpi_service):
        result = kpi_service.contact_engagement()
        channels = result["response_rates"]
        assert "email" in channels
        assert "phone" in channels

    def test_highest_engagement_tier_is_tier_1(self, kpi_service):
        result = kpi_service.contact_engagement()
        assert result["highest_engagement_tier"] == "tier_1_executive"


# ---------------------------------------------------------------------------
# Scoring Distribution
# ---------------------------------------------------------------------------


class TestScoringDistribution:
    """Tests for BD score distribution."""

    def test_returns_required_keys(self, kpi_service):
        result = kpi_service.scoring_distribution()
        assert "distribution" in result
        assert "total_scored" in result
        assert "hot_percentage" in result
        assert "warm_percentage" in result
        assert "cold_percentage" in result
        assert "by_program" in result
        assert "thresholds" in result

    def test_three_tiers_in_distribution(self, kpi_service):
        result = kpi_service.scoring_distribution()
        assert "hot" in result["distribution"]
        assert "warm" in result["distribution"]
        assert "cold" in result["distribution"]

    def test_total_scored_matches_tier_counts(self, kpi_service):
        result = kpi_service.scoring_distribution()
        total = sum(t["count"] for t in result["distribution"].values())
        assert result["total_scored"] == total

    def test_percentages_sum_to_roughly_one(self, kpi_service):
        result = kpi_service.scoring_distribution()
        total_pct = (
            result["hot_percentage"]
            + result["warm_percentage"]
            + result["cold_percentage"]
        )
        assert abs(total_pct - 1.0) < 0.01

    def test_thresholds_match_constants(self, kpi_service):
        result = kpi_service.scoring_distribution()
        assert result["thresholds"]["hot"] == HOT_THRESHOLD
        assert result["thresholds"]["warm"] == WARM_THRESHOLD

    def test_hot_threshold_is_80(self):
        assert HOT_THRESHOLD == 80

    def test_warm_threshold_is_50(self):
        assert WARM_THRESHOLD == 50

    def test_by_program_has_entries(self, kpi_service):
        result = kpi_service.scoring_distribution()
        assert len(result["by_program"]) > 0

    def test_program_entry_structure(self, kpi_service):
        result = kpi_service.scoring_distribution()
        for entry in result["by_program"].values():
            assert "avg_score" in entry
            assert "count" in entry
            assert "tier" in entry

    def test_program_tier_matches_score(self, kpi_service):
        result = kpi_service.scoring_distribution()
        for entry in result["by_program"].values():
            if entry["avg_score"] >= HOT_THRESHOLD:
                assert entry["tier"] == "hot"
            elif entry["avg_score"] >= WARM_THRESHOLD:
                assert entry["tier"] == "warm"
            else:
                assert entry["tier"] == "cold"


# ---------------------------------------------------------------------------
# Executive Summary
# ---------------------------------------------------------------------------


class TestExecutiveSummary:
    """Tests for the roll-up executive summary."""

    def test_returns_required_keys(self, kpi_service):
        result = kpi_service.executive_summary()
        assert "period" in result
        assert "generated_at" in result
        assert "pipeline" in result
        assert "win_rates" in result
        assert "funnel" in result
        assert "competitive" in result
        assert "contacts" in result
        assert "scoring" in result
        assert "data_sources" in result

    def test_generated_at_is_iso_format(self, kpi_service):
        result = kpi_service.executive_summary()
        # Should parse without error
        datetime.fromisoformat(result["generated_at"])

    def test_pipeline_section(self, kpi_service):
        result = kpi_service.executive_summary()
        assert "total_processed" in result["pipeline"]
        assert "velocity_per_day" in result["pipeline"]

    def test_win_rates_section(self, kpi_service):
        result = kpi_service.executive_summary()
        assert "overall_rate" in result["win_rates"]
        assert "total_submitted" in result["win_rates"]
        assert "total_won" in result["win_rates"]

    def test_funnel_section(self, kpi_service):
        result = kpi_service.executive_summary()
        assert "overall_conversion" in result["funnel"]
        assert "total_scraped" in result["funnel"]
        assert "total_won" in result["funnel"]

    def test_competitive_section(self, kpi_service):
        result = kpi_service.executive_summary()
        assert "top_competitor" in result["competitive"]
        assert "total_market_positions" in result["competitive"]

    def test_contacts_section(self, kpi_service):
        result = kpi_service.executive_summary()
        assert "total" in result["contacts"]
        assert "highest_engagement_tier" in result["contacts"]

    def test_scoring_section(self, kpi_service):
        result = kpi_service.executive_summary()
        scoring = result["scoring"]
        assert "total_scored" in scoring
        assert "hot_count" in scoring
        assert "warm_count" in scoring
        assert "cold_count" in scoring
        assert "hot_percentage" in scoring

    def test_data_sources_is_list(self, kpi_service):
        result = kpi_service.executive_summary()
        assert isinstance(result["data_sources"], list)
        assert len(result["data_sources"]) > 0

    def test_explicit_date_range_in_summary(self, kpi_service):
        result = kpi_service.executive_summary("2026-01-01", "2026-01-31")
        assert result["period"]["start_date"] == "2026-01-01"
        assert result["period"]["end_date"] == "2026-01-31"


# ---------------------------------------------------------------------------
# API Router Tests (using FastAPI TestClient)
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """FastAPI TestClient with KPI router mounted."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from Engine8_Knowledge.routers.kpi import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestKPIEndpoints:
    """Tests for KPI API endpoints."""

    def test_pipeline_velocity_200(self, client):
        resp = client.get("/kpi/pipeline-velocity")
        assert resp.status_code == 200
        data = resp.json()
        assert "stages" in data

    def test_pipeline_velocity_with_dates(self, client):
        resp = client.get(
            "/kpi/pipeline-velocity",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        )
        assert resp.status_code == 200
        assert resp.json()["period"]["start_date"] == "2026-01-01"

    def test_win_rates_200(self, client):
        resp = client.get("/kpi/win-rates")
        assert resp.status_code == 200
        data = resp.json()
        assert "overall" in data
        assert "by_program" in data

    def test_conversion_funnel_200(self, client):
        resp = client.get("/kpi/conversion-funnel")
        assert resp.status_code == 200
        data = resp.json()
        assert "funnel" in data
        assert len(data["funnel"]) == 5

    def test_competitive_landscape_200(self, client):
        resp = client.get("/kpi/competitive-landscape")
        assert resp.status_code == 200
        data = resp.json()
        assert "competitors" in data

    def test_competitive_landscape_with_program(self, client):
        resp = client.get(
            "/kpi/competitive-landscape", params={"program": "DCGS"}
        )
        assert resp.status_code == 200
        assert resp.json()["program_filter"] == "DCGS"

    def test_contact_engagement_200(self, client):
        resp = client.get("/kpi/contact-engagement")
        assert resp.status_code == 200
        data = resp.json()
        assert "tier_distribution" in data

    def test_scoring_distribution_200(self, client):
        resp = client.get("/kpi/scoring-distribution")
        assert resp.status_code == 200
        data = resp.json()
        assert "distribution" in data
        assert "thresholds" in data

    def test_executive_summary_200(self, client):
        resp = client.get("/kpi/executive-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "pipeline" in data
        assert "scoring" in data

    def test_export_pdf_stub(self, client):
        resp = client.get("/kpi/export/pdf")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pdf_generation"] == "not_implemented"

    def test_export_pdf_has_message(self, client):
        resp = client.get("/kpi/export/pdf")
        data = resp.json()
        assert "message" in data

    def test_all_date_endpoints_accept_no_params(self, client):
        """All date-scoped endpoints should work without query params."""
        endpoints = [
            "/kpi/pipeline-velocity",
            "/kpi/win-rates",
            "/kpi/conversion-funnel",
            "/kpi/contact-engagement",
            "/kpi/executive-summary",
        ]
        for ep in endpoints:
            resp = client.get(ep)
            assert resp.status_code == 200, f"Failed: {ep}"

    def test_response_json_serializable(self, client):
        """Ensure all endpoints return valid JSON."""
        endpoints = [
            "/kpi/pipeline-velocity",
            "/kpi/win-rates",
            "/kpi/conversion-funnel",
            "/kpi/competitive-landscape",
            "/kpi/contact-engagement",
            "/kpi/scoring-distribution",
            "/kpi/executive-summary",
            "/kpi/export/pdf",
        ]
        for ep in endpoints:
            resp = client.get(ep)
            assert resp.headers["content-type"] == "application/json"
            data = resp.json()  # Should not raise
            assert isinstance(data, dict)
