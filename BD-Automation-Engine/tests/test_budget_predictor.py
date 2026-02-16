"""Tests for Phase 32A — Federal Budget Cycle Predictor."""

import pytest
from datetime import datetime, timezone

from src.ml.budget_predictor import (
    BudgetCyclePredictor,
    SpendingWindow,
    RecompetePrediction,
    BDCalendar,
    AGENCY_PATTERNS,
    DEFAULT_PATTERN,
    FEDERAL_CONFERENCES,
    get_budget_predictor,
)


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def predictor():
    return BudgetCyclePredictor()


@pytest.fixture
def predictor_with_contracts():
    contracts = [
        {
            "id": "contract-1",
            "name": "DCGS Sustainment",
            "pop_end": "2027-03-31",
            "options_remaining": 2,
            "program": "AF DCGS",
        },
        {
            "id": "contract-2",
            "name": "NGEN Operations",
            "pop_end": "2026-09-30",
            "options_remaining": 0,
            "program": "NGEN",
        },
    ]
    return BudgetCyclePredictor(contracts_data=contracts)


# =========================================
# FISCAL CALENDAR
# =========================================


class TestFiscalCalendar:
    def test_q1_oct(self, predictor):
        dt = datetime(2025, 10, 15, tzinfo=timezone.utc)
        assert predictor._get_fiscal_quarter(dt) == 1

    def test_q2_jan(self, predictor):
        dt = datetime(2025, 1, 15, tzinfo=timezone.utc)
        assert predictor._get_fiscal_quarter(dt) == 2

    def test_q3_apr(self, predictor):
        dt = datetime(2025, 4, 15, tzinfo=timezone.utc)
        assert predictor._get_fiscal_quarter(dt) == 3

    def test_q4_jul(self, predictor):
        dt = datetime(2025, 7, 15, tzinfo=timezone.utc)
        assert predictor._get_fiscal_quarter(dt) == 4

    def test_fiscal_year_oct(self, predictor):
        dt = datetime(2025, 10, 1, tzinfo=timezone.utc)
        assert predictor._get_fiscal_year(dt) == 2026

    def test_fiscal_year_jan(self, predictor):
        dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
        assert predictor._get_fiscal_year(dt) == 2025


# =========================================
# SPENDING WINDOW
# =========================================


@pytest.mark.asyncio
class TestSpendingWindow:
    async def test_returns_spending_window(self, predictor):
        result = await predictor.predict_spending_window("USAF")
        assert isinstance(result, SpendingWindow)

    async def test_agency_field(self, predictor):
        result = await predictor.predict_spending_window("Navy")
        assert result.agency == "Navy"

    async def test_intensity_range(self, predictor):
        result = await predictor.predict_spending_window("USAF")
        assert 0.0 <= result.spending_intensity <= 1.0

    async def test_phase_values(self, predictor):
        result = await predictor.predict_spending_window("USAF")
        assert result.current_phase in ("new_fy", "ramp_up", "peak", "surge")

    async def test_recommended_actions(self, predictor):
        result = await predictor.predict_spending_window("DIA")
        assert isinstance(result.recommended_actions, list)
        assert len(result.recommended_actions) > 0

    async def test_unknown_agency_uses_default(self, predictor):
        result = await predictor.predict_spending_window("UnknownAgency")
        assert isinstance(result, SpendingWindow)
        assert result.agency == "UnknownAgency"


# =========================================
# RECOMPETE PREDICTION
# =========================================


@pytest.mark.asyncio
class TestRecompetePrediction:
    async def test_returns_prediction(self, predictor_with_contracts):
        result = await predictor_with_contracts.predict_recompete_timing("contract-1")
        assert isinstance(result, RecompetePrediction)

    async def test_contract_name(self, predictor_with_contracts):
        result = await predictor_with_contracts.predict_recompete_timing("contract-1")
        assert result.contract_name == "DCGS Sustainment"

    async def test_options_remaining(self, predictor_with_contracts):
        result = await predictor_with_contracts.predict_recompete_timing("contract-1")
        assert result.options_remaining == 2

    async def test_no_options_high_recompete_prob(self, predictor_with_contracts):
        result = await predictor_with_contracts.predict_recompete_timing("contract-2")
        assert result.recompete_probability >= 0.8

    async def test_with_options_lower_recompete_prob(self, predictor_with_contracts):
        result = await predictor_with_contracts.predict_recompete_timing("contract-1")
        assert result.recompete_probability < 0.85

    async def test_recommended_actions(self, predictor_with_contracts):
        result = await predictor_with_contracts.predict_recompete_timing("contract-2")
        assert isinstance(result.recommended_actions, list)
        assert len(result.recommended_actions) > 0

    async def test_unknown_contract(self, predictor):
        result = await predictor.predict_recompete_timing("nonexistent")
        assert result.confidence <= 0.2

    async def test_dates_are_strings(self, predictor_with_contracts):
        result = await predictor_with_contracts.predict_recompete_timing("contract-1")
        assert isinstance(result.predicted_rfi_date, str)
        assert isinstance(result.predicted_rfp_date, str)
        assert isinstance(result.predicted_award_date, str)


# =========================================
# BD CALENDAR
# =========================================


@pytest.mark.asyncio
class TestBDCalendar:
    async def test_returns_calendar(self, predictor):
        cal = await predictor.get_calendar(12)
        assert isinstance(cal, BDCalendar)

    async def test_events_list(self, predictor):
        cal = await predictor.get_calendar(12)
        assert isinstance(cal.events, list)

    async def test_events_sorted_by_date(self, predictor):
        cal = await predictor.get_calendar(12)
        dates = [e.date for e in cal.events]
        assert dates == sorted(dates)

    async def test_total_events_matches(self, predictor):
        cal = await predictor.get_calendar(12)
        assert cal.total_events == len(cal.events)

    async def test_event_types(self, predictor):
        cal = await predictor.get_calendar(12)
        valid_types = {"budget", "recompete", "option", "hiring_surge", "conference"}
        for e in cal.events:
            assert e.event_type in valid_types

    async def test_includes_conferences(self, predictor):
        cal = await predictor.get_calendar(12)
        conf_events = [e for e in cal.events if e.event_type == "conference"]
        assert len(conf_events) > 0

    async def test_with_contracts(self, predictor_with_contracts):
        cal = await predictor_with_contracts.get_calendar(24)
        assert isinstance(cal, BDCalendar)


# =========================================
# AGENCY PATTERNS
# =========================================


class TestAgencyPatterns:
    def test_all_agencies_have_required_keys(self):
        required = {
            "peak_months",
            "surge_months",
            "slow_months",
            "budget_cycle_offset_days",
            "typical_procurement_lead_time_months",
        }
        for agency, pattern in AGENCY_PATTERNS.items():
            assert required.issubset(pattern.keys()), f"{agency} missing keys"

    def test_default_pattern_has_keys(self):
        required = {"peak_months", "surge_months", "slow_months"}
        assert required.issubset(DEFAULT_PATTERN.keys())

    def test_conferences_list(self):
        assert len(FEDERAL_CONFERENCES) >= 9
        for conf in FEDERAL_CONFERENCES:
            assert "month" in conf
            assert "name" in conf
            assert 1 <= conf["month"] <= 12


# =========================================
# SINGLETON
# =========================================


class TestSingleton:
    def test_get_predictor_returns_instance(self):
        p = get_budget_predictor()
        assert isinstance(p, BudgetCyclePredictor)

    def test_get_predictor_is_singleton(self):
        p1 = get_budget_predictor()
        p2 = get_budget_predictor()
        assert p1 is p2
