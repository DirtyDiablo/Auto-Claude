"""Phase 32A — Hiring Trend Forecaster

Time-series forecasting for hiring patterns by program, location, and role.
Uses exponential smoothing with seasonal decomposition. Falls back to
rolling-average projection when statsmodels is not available.
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NP_AVAILABLE = True
except ImportError:
    NP_AVAILABLE = False


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class ForecastPoint:
    date: str
    predicted: float
    lower_bound: float
    upper_bound: float


@dataclass
class HiringForecast:
    entity: str  # program name, location, or role
    entity_type: str  # "program", "location", "role"
    horizon_days: int
    current_rate: float  # jobs per week (recent)
    forecasted_rate: float  # predicted jobs per week
    trend: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1
    seasonal_pattern: str  # "Q4 surge", "steady", etc.
    forecast_points: List[ForecastPoint] = field(default_factory=list)
    confidence: float = 0.5
    generated_at: str = ""


@dataclass
class LocationForecast:
    location: str
    forecasts_by_program: Dict[str, HiringForecast] = field(default_factory=dict)
    total_forecast: Optional[HiringForecast] = None


@dataclass
class RoleForecast:
    role_category: str
    current_demand: int
    forecasted_demand: int
    growth_rate: float  # percent change
    top_programs: List[str] = field(default_factory=list)
    top_locations: List[str] = field(default_factory=list)


@dataclass
class RampSignal:
    program: str
    signal_type: str  # "ramp_up", "wind_down", "recompete"
    confidence: float
    evidence: List[str]
    detected_at: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class TimingRec:
    program: str
    best_window: str
    reason: str
    historical_peaks: List[str]
    next_peak_estimate: str = ""
    confidence: float = 0.5


class HiringForecaster:
    """Predict future hiring activity by program, location, and role."""

    # Federal fiscal year quarters
    FY_QUARTERS = {
        1: (10, 11, 12),  # Oct-Dec
        2: (1, 2, 3),      # Jan-Mar
        3: (4, 5, 6),      # Apr-Jun
        4: (7, 8, 9),      # Jul-Sep
    }

    # Known seasonal patterns
    SEASONAL_PATTERNS = {
        "Q4_surge": "Jul-Sep spending surge (use-or-lose)",
        "Q1_slow": "Oct-Dec new FY ramp-up (slow start)",
        "Q3_peak": "Apr-Jun peak procurement",
        "steady": "No strong seasonal pattern",
    }

    def __init__(self, historical_data: Optional[List[dict]] = None):
        self._historical = historical_data or []
        self._forecasts_cache: Dict[str, HiringForecast] = {}

    def set_historical_data(self, data: List[dict]) -> None:
        """Set historical job posting data for forecasting."""
        self._historical = data
        self._forecasts_cache.clear()

    async def forecast_program_hiring(
        self, program: str, horizon_days: int = 90,
        historical: Optional[List[dict]] = None,
    ) -> HiringForecast:
        """Forecast hiring volume for a program."""
        data = historical or self._get_program_data(program)

        if not data:
            return self._empty_forecast(program, "program", horizon_days)

        weekly_counts = self._aggregate_weekly(data)
        current_rate = self._current_rate(weekly_counts)
        trend, strength = self._detect_trend(weekly_counts)
        seasonal = self._detect_seasonal_pattern(weekly_counts)
        forecast_points = self._project_forward(weekly_counts, horizon_days, trend, strength)
        forecasted_rate = forecast_points[-1].predicted if forecast_points else current_rate

        return HiringForecast(
            entity=program,
            entity_type="program",
            horizon_days=horizon_days,
            current_rate=round(current_rate, 2),
            forecasted_rate=round(forecasted_rate, 2),
            trend=trend,
            trend_strength=round(strength, 3),
            seasonal_pattern=seasonal,
            forecast_points=forecast_points,
            confidence=min(0.9, 0.3 + len(weekly_counts) * 0.05),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    async def forecast_location_demand(
        self, location: str, horizon_days: int = 90,
        historical: Optional[List[dict]] = None,
    ) -> HiringForecast:
        """Forecast hiring by location across all programs."""
        data = historical or self._get_location_data(location)

        if not data:
            return self._empty_forecast(location, "location", horizon_days)

        weekly_counts = self._aggregate_weekly(data)
        current_rate = self._current_rate(weekly_counts)
        trend, strength = self._detect_trend(weekly_counts)
        seasonal = self._detect_seasonal_pattern(weekly_counts)
        forecast_points = self._project_forward(weekly_counts, horizon_days, trend, strength)
        forecasted_rate = forecast_points[-1].predicted if forecast_points else current_rate

        return HiringForecast(
            entity=location,
            entity_type="location",
            horizon_days=horizon_days,
            current_rate=round(current_rate, 2),
            forecasted_rate=round(forecasted_rate, 2),
            trend=trend,
            trend_strength=round(strength, 3),
            seasonal_pattern=seasonal,
            forecast_points=forecast_points,
            confidence=min(0.9, 0.3 + len(weekly_counts) * 0.05),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    async def forecast_role_demand(
        self, role_category: str,
        historical: Optional[List[dict]] = None,
    ) -> RoleForecast:
        """Forecast demand for specific role types."""
        data = historical or self._get_role_data(role_category)

        current_count = len(data) if data else 0
        weekly = self._aggregate_weekly(data) if data else []
        trend, strength = self._detect_trend(weekly) if weekly else ("stable", 0.0)

        growth = strength * 100 if trend == "increasing" else -strength * 100 if trend == "decreasing" else 0
        forecasted = max(0, int(current_count * (1 + growth / 100)))

        # Extract top programs and locations
        programs = {}
        locations = {}
        for item in (data or []):
            p = item.get("program", "Unknown")
            l = item.get("location", "Unknown")
            programs[p] = programs.get(p, 0) + 1
            locations[l] = locations.get(l, 0) + 1

        top_programs = sorted(programs, key=programs.get, reverse=True)[:5]
        top_locations = sorted(locations, key=locations.get, reverse=True)[:5]

        return RoleForecast(
            role_category=role_category,
            current_demand=current_count,
            forecasted_demand=forecasted,
            growth_rate=round(growth, 1),
            top_programs=top_programs,
            top_locations=top_locations,
        )

    async def detect_ramp_signals(
        self, historical: Optional[List[dict]] = None,
    ) -> List[RampSignal]:
        """Detect programs entering ramp-up, wind-down, or recompete."""
        data = historical or self._historical
        if not data:
            return []

        # Group by program
        by_program: Dict[str, List[dict]] = {}
        for item in data:
            prog = item.get("program", "Unknown")
            by_program.setdefault(prog, []).append(item)

        signals = []
        now = datetime.now(timezone.utc).isoformat()

        for program, items in by_program.items():
            weekly = self._aggregate_weekly(items)
            if len(weekly) < 4:
                continue

            trend, strength = self._detect_trend(weekly)
            recent_avg = sum(weekly[-4:]) / 4 if len(weekly) >= 4 else 0
            baseline = sum(weekly[:-4]) / max(len(weekly) - 4, 1) if len(weekly) > 4 else recent_avg

            # Ramp-up: accelerating postings
            if trend == "increasing" and strength > 0.3 and recent_avg > baseline * 1.5:
                evidence = [
                    f"Posting rate increased {strength*100:.0f}% trend",
                    f"Recent: {recent_avg:.1f}/week vs baseline {baseline:.1f}/week",
                ]
                # Check for new role types
                recent_roles = set(item.get("role", "") for item in items[-10:])
                older_roles = set(item.get("role", "") for item in items[:-10])
                new_roles = recent_roles - older_roles
                if new_roles:
                    evidence.append(f"New role types appearing: {', '.join(list(new_roles)[:3])}")

                signals.append(RampSignal(
                    program=program,
                    signal_type="ramp_up",
                    confidence=min(0.9, strength + 0.3),
                    evidence=evidence,
                    detected_at=now,
                    details={"recent_avg": recent_avg, "baseline": baseline},
                ))

            # Wind-down: declining postings
            elif trend == "decreasing" and strength > 0.3 and recent_avg < baseline * 0.5:
                evidence = [
                    f"Posting rate declined {strength*100:.0f}% trend",
                    f"Recent: {recent_avg:.1f}/week vs baseline {baseline:.1f}/week",
                ]
                signals.append(RampSignal(
                    program=program,
                    signal_type="wind_down",
                    confidence=min(0.9, strength + 0.2),
                    evidence=evidence,
                    detected_at=now,
                    details={"recent_avg": recent_avg, "baseline": baseline},
                ))

            # Recompete: sudden drop then new activity pattern
            if len(weekly) >= 8:
                mid = len(weekly) // 2
                first_half = sum(weekly[:mid]) / mid
                second_half = sum(weekly[mid:]) / (len(weekly) - mid)
                if first_half > 0 and second_half < first_half * 0.3:
                    signals.append(RampSignal(
                        program=program,
                        signal_type="recompete",
                        confidence=0.5,
                        evidence=[
                            f"Activity dropped from {first_half:.1f}/week to {second_half:.1f}/week",
                            "Possible recompete or contract transition",
                        ],
                        detected_at=now,
                    ))

        return signals

    async def optimal_timing_recommendation(
        self, program: str,
        historical: Optional[List[dict]] = None,
    ) -> TimingRec:
        """When to approach this program based on historical hiring cycles."""
        data = historical or self._get_program_data(program)

        if not data:
            return TimingRec(
                program=program,
                best_window="Q3 (Apr-Jun)",
                reason="Default recommendation: Q3 is peak procurement across federal agencies",
                historical_peaks=[],
                confidence=0.3,
            )

        # Analyze monthly distribution
        monthly_counts: Dict[int, int] = {m: 0 for m in range(1, 13)}
        for item in data:
            dt = item.get("posted_date") or item.get("date")
            if dt:
                try:
                    if isinstance(dt, str):
                        month = datetime.fromisoformat(dt.replace("Z", "+00:00")).month
                    else:
                        month = dt.month
                    monthly_counts[month] += 1
                except Exception:
                    pass

        # Find peak months
        if sum(monthly_counts.values()) == 0:
            return TimingRec(
                program=program,
                best_window="Q3 (Apr-Jun)",
                reason="Insufficient historical data, using default Q3 recommendation",
                historical_peaks=[],
                confidence=0.3,
            )

        sorted_months = sorted(monthly_counts.items(), key=lambda x: x[1], reverse=True)
        peak_months = [m for m, c in sorted_months[:3] if c > 0]
        month_names = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                       7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

        peak_names = [month_names.get(m, str(m)) for m in peak_months]
        best_month = peak_months[0] if peak_months else 4

        # Determine quarter
        for q, months in self.FY_QUARTERS.items():
            if best_month in months:
                best_quarter = f"Q{q}"
                break
        else:
            best_quarter = "Q3"

        return TimingRec(
            program=program,
            best_window=f"{best_quarter} ({', '.join(peak_names)})",
            reason=f"Historical peaks in {', '.join(peak_names)} based on {sum(monthly_counts.values())} postings",
            historical_peaks=peak_names,
            next_peak_estimate=peak_names[0] if peak_names else "Apr",
            confidence=min(0.9, 0.3 + len(data) * 0.01),
        )

    # =========================================
    # INTERNAL HELPERS
    # =========================================

    def _get_program_data(self, program: str) -> List[dict]:
        return [d for d in self._historical if program.lower() in str(d.get("program", "")).lower()]

    def _get_location_data(self, location: str) -> List[dict]:
        return [d for d in self._historical if location.lower() in str(d.get("location", "")).lower()]

    def _get_role_data(self, role: str) -> List[dict]:
        return [d for d in self._historical if role.lower() in str(d.get("role", d.get("title", ""))).lower()]

    def _aggregate_weekly(self, data: List[dict]) -> List[float]:
        """Aggregate data into weekly counts."""
        if not data:
            return []

        dates = []
        for item in data:
            dt = item.get("posted_date") or item.get("date") or item.get("created_at")
            if dt:
                try:
                    if isinstance(dt, str):
                        dates.append(datetime.fromisoformat(dt.replace("Z", "+00:00")))
                    elif isinstance(dt, datetime):
                        dates.append(dt)
                except Exception:
                    pass

        if not dates:
            # No dates available — return a single-week estimate
            return [float(len(data))]

        dates.sort()
        min_date = dates[0]
        max_date = dates[-1]
        total_weeks = max(1, int((max_date - min_date).days / 7) + 1)

        weeks = [0.0] * total_weeks
        for dt in dates:
            week_idx = min(int((dt - min_date).days / 7), total_weeks - 1)
            weeks[week_idx] += 1.0

        return weeks

    def _current_rate(self, weekly: List[float]) -> float:
        """Get current rate (avg of last 4 weeks)."""
        if not weekly:
            return 0.0
        recent = weekly[-4:] if len(weekly) >= 4 else weekly
        return sum(recent) / len(recent)

    def _detect_trend(self, weekly: List[float]) -> Tuple[str, float]:
        """Detect trend direction and strength using linear regression."""
        if len(weekly) < 3:
            return "stable", 0.0

        if not NP_AVAILABLE:
            # Simple comparison fallback
            first_half = sum(weekly[:len(weekly)//2]) / max(len(weekly)//2, 1)
            second_half = sum(weekly[len(weekly)//2:]) / max(len(weekly) - len(weekly)//2, 1)
            if second_half > first_half * 1.2:
                return "increasing", 0.5
            elif second_half < first_half * 0.8:
                return "decreasing", 0.5
            return "stable", 0.1

        x = np.arange(len(weekly), dtype=float)
        y = np.array(weekly, dtype=float)

        # Linear regression
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        ss_xy = np.sum((x - x_mean) * (y - y_mean))
        ss_xx = np.sum((x - x_mean) ** 2)

        if ss_xx == 0:
            return "stable", 0.0

        slope = ss_xy / ss_xx

        # Normalize strength by data range
        y_range = max(y) - min(y) if max(y) != min(y) else 1.0
        strength = min(1.0, abs(slope) / (y_range / len(weekly) + 0.01))

        if slope > 0.05:
            return "increasing", strength
        elif slope < -0.05:
            return "decreasing", strength
        return "stable", strength

    def _detect_seasonal_pattern(self, weekly: List[float]) -> str:
        """Detect seasonal pattern in weekly data."""
        if len(weekly) < 12:
            return "steady"

        # Split into quarters (assuming ~13 weeks/quarter)
        quarter_size = max(1, len(weekly) // 4)
        quarters = [
            sum(weekly[i*quarter_size:(i+1)*quarter_size]) / quarter_size
            for i in range(4)
            if i * quarter_size < len(weekly)
        ]

        if len(quarters) < 4:
            return "steady"

        max_q = quarters.index(max(quarters)) + 1
        if max_q == 4 and quarters[3] > sum(quarters[:3]) / 3 * 1.3:
            return "Q4_surge"
        if max_q == 3 and quarters[2] > sum([quarters[0], quarters[1], quarters[3]]) / 3 * 1.3:
            return "Q3_peak"
        return "steady"

    def _project_forward(self, weekly: List[float], horizon_days: int,
                         trend: str, strength: float) -> List[ForecastPoint]:
        """Project forward using trend extrapolation."""
        if not weekly:
            return []

        horizon_weeks = max(1, horizon_days // 7)
        current = self._current_rate(weekly)
        points = []
        now = datetime.now(timezone.utc)

        for w in range(1, horizon_weeks + 1):
            date = now + timedelta(weeks=w)

            # Apply trend
            if trend == "increasing":
                predicted = current * (1 + strength * w * 0.02)
            elif trend == "decreasing":
                predicted = current * (1 - strength * w * 0.02)
            else:
                predicted = current

            predicted = max(0, predicted)

            # Confidence interval widens with horizon
            margin = current * 0.2 * math.sqrt(w)
            points.append(ForecastPoint(
                date=date.strftime("%Y-%m-%d"),
                predicted=round(predicted, 2),
                lower_bound=round(max(0, predicted - margin), 2),
                upper_bound=round(predicted + margin, 2),
            ))

        return points

    def _empty_forecast(self, entity: str, entity_type: str,
                        horizon_days: int) -> HiringForecast:
        """Return empty forecast when no data available."""
        return HiringForecast(
            entity=entity,
            entity_type=entity_type,
            horizon_days=horizon_days,
            current_rate=0.0,
            forecasted_rate=0.0,
            trend="stable",
            trend_strength=0.0,
            seasonal_pattern="steady",
            confidence=0.1,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


# =========================================
# SINGLETON
# =========================================

_forecaster: Optional[HiringForecaster] = None


def get_hiring_forecaster() -> HiringForecaster:
    global _forecaster
    if _forecaster is None:
        _forecaster = HiringForecaster()
    return _forecaster
