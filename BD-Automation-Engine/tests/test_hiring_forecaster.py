"""Tests for Phase 32A — Hiring Trend Forecaster."""

import pytest

from src.ml.hiring_forecaster import (
    HiringForecaster,
    HiringForecast,
    RampSignal,
    TimingRec,
    RoleForecast,
    ForecastPoint,
    get_hiring_forecaster,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def forecaster():
    return HiringForecaster()


@pytest.fixture
def forecaster_with_data():
    """Forecaster seeded with sample job history."""
    f = HiringForecaster()
    sample_jobs = [
        {"program": "AF DCGS", "location": "Hickam AFB", "role": "analyst",
         "posted_date": "2025-01-15", "company": "Leidos"},
        {"program": "AF DCGS", "location": "Hickam AFB", "role": "analyst",
         "posted_date": "2025-02-10", "company": "Leidos"},
        {"program": "AF DCGS", "location": "Langley", "role": "engineer",
         "posted_date": "2025-03-05", "company": "Leidos"},
        {"program": "NGEN", "location": "San Diego", "role": "cyber",
         "posted_date": "2025-01-20", "company": "GDIT"},
        {"program": "NGEN", "location": "San Diego", "role": "analyst",
         "posted_date": "2025-04-01", "company": "GDIT"},
        {"program": "GBSD", "location": "Colorado Springs", "role": "engineer",
         "posted_date": "2025-05-15", "company": "NGC"},
    ]
    f.set_historical_data(sample_jobs)
    return f


# =========================================
# PROGRAM FORECAST
# =========================================

@pytest.mark.asyncio
class TestProgramForecast:
    async def test_returns_hiring_forecast(self, forecaster_with_data):
        result = await forecaster_with_data.forecast_program_hiring("AF DCGS", 90)
        assert isinstance(result, HiringForecast)

    async def test_entity_matches_program(self, forecaster_with_data):
        result = await forecaster_with_data.forecast_program_hiring("AF DCGS", 90)
        assert result.entity == "AF DCGS"

    async def test_horizon_days(self, forecaster_with_data):
        result = await forecaster_with_data.forecast_program_hiring("AF DCGS", 180)
        assert result.horizon_days == 180

    async def test_trend_values(self, forecaster_with_data):
        result = await forecaster_with_data.forecast_program_hiring("AF DCGS", 90)
        assert result.trend in ("increasing", "decreasing", "stable")

    async def test_forecast_points(self, forecaster_with_data):
        result = await forecaster_with_data.forecast_program_hiring("AF DCGS", 90)
        assert isinstance(result.forecast_points, list)
        for p in result.forecast_points:
            assert isinstance(p, ForecastPoint)
            assert p.lower_bound <= p.predicted <= p.upper_bound

    async def test_unknown_program(self, forecaster):
        result = await forecaster.forecast_program_hiring("NONEXISTENT", 90)
        assert isinstance(result, HiringForecast)
        assert result.confidence <= 0.3

    async def test_confidence_range(self, forecaster_with_data):
        result = await forecaster_with_data.forecast_program_hiring("AF DCGS", 90)
        assert 0.0 <= result.confidence <= 1.0


# =========================================
# LOCATION FORECAST
# =========================================

@pytest.mark.asyncio
class TestLocationForecast:
    async def test_returns_forecast(self, forecaster_with_data):
        result = await forecaster_with_data.forecast_location_demand("Hickam AFB", 90)
        assert isinstance(result, HiringForecast)

    async def test_entity_matches_location(self, forecaster_with_data):
        result = await forecaster_with_data.forecast_location_demand("San Diego", 90)
        assert result.entity == "San Diego"

    async def test_unknown_location(self, forecaster):
        result = await forecaster.forecast_location_demand("Atlantis", 90)
        assert result.confidence <= 0.3


# =========================================
# ROLE FORECAST
# =========================================

@pytest.mark.asyncio
class TestRoleForecast:
    async def test_returns_role_forecast(self, forecaster_with_data):
        result = await forecaster_with_data.forecast_role_demand("analyst")
        assert isinstance(result, RoleForecast)

    async def test_role_category(self, forecaster_with_data):
        result = await forecaster_with_data.forecast_role_demand("analyst")
        assert result.role_category == "analyst"

    async def test_top_programs_list(self, forecaster_with_data):
        result = await forecaster_with_data.forecast_role_demand("analyst")
        assert isinstance(result.top_programs, list)

    async def test_top_locations_list(self, forecaster_with_data):
        result = await forecaster_with_data.forecast_role_demand("analyst")
        assert isinstance(result.top_locations, list)


# =========================================
# RAMP SIGNALS
# =========================================

@pytest.mark.asyncio
class TestRampSignals:
    async def test_returns_list(self, forecaster_with_data):
        signals = await forecaster_with_data.detect_ramp_signals()
        assert isinstance(signals, list)

    async def test_signal_structure(self, forecaster_with_data):
        signals = await forecaster_with_data.detect_ramp_signals()
        for s in signals:
            assert isinstance(s, RampSignal)
            assert s.signal_type in ("ramp_up", "wind_down", "recompete")
            assert 0.0 <= s.confidence <= 1.0
            assert isinstance(s.evidence, list)

    async def test_empty_forecaster(self, forecaster):
        signals = await forecaster.detect_ramp_signals()
        assert isinstance(signals, list)


# =========================================
# TIMING RECOMMENDATION
# =========================================

@pytest.mark.asyncio
class TestTimingRecommendation:
    async def test_returns_timing_rec(self, forecaster_with_data):
        rec = await forecaster_with_data.optimal_timing_recommendation("AF DCGS")
        assert isinstance(rec, TimingRec)

    async def test_program_field(self, forecaster_with_data):
        rec = await forecaster_with_data.optimal_timing_recommendation("AF DCGS")
        assert rec.program == "AF DCGS"

    async def test_best_window_present(self, forecaster_with_data):
        rec = await forecaster_with_data.optimal_timing_recommendation("AF DCGS")
        assert isinstance(rec.best_window, str)
        assert len(rec.best_window) > 0

    async def test_confidence_range(self, forecaster_with_data):
        rec = await forecaster_with_data.optimal_timing_recommendation("AF DCGS")
        assert 0.0 <= rec.confidence <= 1.0


# =========================================
# SINGLETON
# =========================================

class TestSingleton:
    def test_get_forecaster_returns_instance(self):
        f = get_hiring_forecaster()
        assert isinstance(f, HiringForecaster)

    def test_get_forecaster_is_singleton(self):
        f1 = get_hiring_forecaster()
        f2 = get_hiring_forecaster()
        assert f1 is f2
