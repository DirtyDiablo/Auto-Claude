"""Tests for Phase 36A — ROI Calculator."""

import pytest

from src.revenue.roi_calculator import (
    ROICalculator,
    get_roi_calculator,
)


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def calculator():
    calc = ROICalculator()
    calc.set_campaign_data(
        [
            {
                "id": "camp-1",
                "name": "DCGS Outreach",
                "investment": 10000,
                "revenue": 50000,
                "placements": 3,
                "time_to_revenue_days": 45,
            },
            {
                "id": "camp-2",
                "name": "NGEN Push",
                "investment": 8000,
                "revenue": 12000,
                "placements": 1,
                "time_to_revenue_days": 90,
            },
            {
                "id": "camp-3",
                "name": "GBSD Prospect",
                "investment": 5000,
                "revenue": 0,
                "placements": 0,
            },
        ]
    )
    calc.set_contact_data(
        [
            {
                "id": "c1",
                "name": "VP Smith",
                "touchpoints": 20,
                "revenue": 100000,
                "placements": 5,
                "first_contact_date": "2024-06-01",
                "first_revenue_date": "2024-09-15",
            },
            {
                "id": "c2",
                "name": "Dir Jones",
                "touchpoints": 8,
                "revenue": 25000,
                "placements": 1,
                "first_contact_date": "2024-08-01",
                "first_revenue_date": "2025-01-01",
            },
            {
                "id": "c3",
                "name": "PM Brown",
                "touchpoints": 15,
                "revenue": 0,
                "placements": 0,
            },
        ]
    )
    calc.set_program_data(
        [
            {
                "program": "DCGS",
                "investment": 25000,
                "revenue": 150000,
                "placements": 8,
                "active_placements": 5,
                "avg_margin_pct": 35,
                "time_to_revenue_days": 60,
            },
            {
                "program": "NGEN",
                "investment": 15000,
                "revenue": 40000,
                "placements": 3,
                "active_placements": 2,
                "avg_margin_pct": 30,
                "time_to_revenue_days": 90,
            },
        ]
    )
    calc.set_channel_data(
        [
            {
                "channel": "referral",
                "deals_sourced": 20,
                "deals_won": 12,
                "revenue": 120000,
                "cost": 5000,
            },
            {
                "channel": "cold_outreach",
                "deals_sourced": 50,
                "deals_won": 5,
                "revenue": 30000,
                "cost": 15000,
            },
            {
                "channel": "inbound",
                "deals_sourced": 10,
                "deals_won": 4,
                "revenue": 45000,
                "cost": 2000,
            },
        ]
    )
    calc.set_tool_data(
        [
            {
                "name": "Apify",
                "monthly_cost": 150,
                "attributed_revenue": 20000,
                "placements": 2,
            },
            {
                "name": "OpenAI",
                "monthly_cost": 200,
                "attributed_revenue": 35000,
                "placements": 3,
            },
        ]
    )
    return calc


# =========================================
# CAMPAIGN ROI
# =========================================


class TestCampaignROI:
    def test_returns_list(self, calculator):
        results = calculator.calculate_campaign_roi()
        assert isinstance(results, list)
        assert len(results) == 3

    def test_roi_calculated(self, calculator):
        results = calculator.calculate_campaign_roi()
        dcgs = [r for r in results if r.campaign_name == "DCGS Outreach"][0]
        assert dcgs.roi_pct == 400.0  # (50000 - 10000) / 10000 * 100

    def test_zero_investment_handled(self, calculator):
        calculator.set_campaign_data(
            [{"id": "x", "name": "Free", "investment": 0, "revenue": 1000}]
        )
        results = calculator.calculate_campaign_roi()
        assert results[0].roi_pct == 0  # No division by zero

    def test_sorted_by_roi(self, calculator):
        results = calculator.calculate_campaign_roi()
        rois = [r.roi_pct for r in results]
        assert rois == sorted(rois, reverse=True)


# =========================================
# CONTACT ROI
# =========================================


class TestContactROI:
    def test_returns_list(self, calculator):
        results = calculator.calculate_contact_roi()
        assert isinstance(results, list)
        assert len(results) == 3

    def test_positive_roi_contact(self, calculator):
        results = calculator.calculate_contact_roi()
        vp = [r for r in results if r.contact_name == "VP Smith"][0]
        assert vp.roi_pct > 0
        assert vp.placements == 5

    def test_zero_revenue_negative_roi(self, calculator):
        results = calculator.calculate_contact_roi()
        brown = [r for r in results if r.contact_name == "PM Brown"][0]
        assert brown.roi_pct < 0  # Investment but no revenue

    def test_time_to_revenue(self, calculator):
        results = calculator.calculate_contact_roi()
        vp = [r for r in results if r.contact_name == "VP Smith"][0]
        assert vp.time_to_revenue_days > 0


# =========================================
# PROGRAM ROI
# =========================================


class TestProgramROI:
    def test_returns_list(self, calculator):
        results = calculator.calculate_program_roi()
        assert isinstance(results, list)
        assert len(results) == 2

    def test_dcgs_highest_roi(self, calculator):
        results = calculator.calculate_program_roi()
        assert results[0].program == "DCGS"
        assert results[0].roi_pct == 500.0  # (150000 - 25000) / 25000 * 100


# =========================================
# CHANNEL ROI
# =========================================


class TestChannelROI:
    def test_returns_list(self, calculator):
        results = calculator.calculate_channel_roi()
        assert isinstance(results, list)
        assert len(results) == 3

    def test_conversion_rate(self, calculator):
        results = calculator.calculate_channel_roi()
        referral = [r for r in results if r.channel == "referral"][0]
        assert referral.conversion_rate == 60.0  # 12/20 * 100

    def test_referral_best_roi(self, calculator):
        results = calculator.calculate_channel_roi()
        # referral: (120000-5000)/5000*100 = 2300% — highest
        assert results[0].channel == "referral"


# =========================================
# TOOL ROI
# =========================================


class TestToolROI:
    def test_returns_list(self, calculator):
        results = calculator.calculate_tool_roi()
        assert isinstance(results, list)
        assert len(results) == 2

    def test_annual_cost_calculated(self, calculator):
        results = calculator.calculate_tool_roi()
        apify = [r for r in results if r.tool_name == "Apify"][0]
        assert apify.annual_cost == 1800  # 150 * 12


# =========================================
# ROI SUMMARY
# =========================================


class TestROISummary:
    def test_summary(self, calculator):
        summary = calculator.get_roi_summary()
        assert "total_investment" in summary
        assert "total_revenue" in summary
        assert "overall_roi_pct" in summary
        assert summary["total_revenue"] > 0


# =========================================
# SINGLETON
# =========================================


class TestSingleton:
    def test_get_calculator_returns_instance(self):
        c = get_roi_calculator()
        assert isinstance(c, ROICalculator)

    def test_get_calculator_is_singleton(self):
        c1 = get_roi_calculator()
        c2 = get_roi_calculator()
        assert c1 is c2
