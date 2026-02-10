"""Phase 32A — Federal Budget Cycle Predictor

Predicts budget availability windows, recompete timing, and optimal
BD outreach windows aligned with the federal procurement calendar.

Federal Fiscal Year (FY):
  Q1: Oct-Dec — New FY, fresh budgets, slow procurement
  Q2: Jan-Mar — Ramp-up, requirements solidifying
  Q3: Apr-Jun — Peak procurement activity
  Q4: Jul-Sep — Use-or-lose spending surge, quick-turn awards
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class SpendingWindow:
    agency: str
    current_quarter: int
    current_phase: str  # "new_fy", "ramp_up", "peak", "surge"
    spending_intensity: float  # 0-1
    recommended_actions: List[str]
    next_window: str
    days_to_next_window: int
    fiscal_year: int = 0
    details: str = ""


@dataclass
class RecompetePrediction:
    contract_id: str
    contract_name: str
    current_pop_end: str
    options_remaining: int
    predicted_rfi_date: str
    predicted_rfp_date: str
    predicted_award_date: str
    recompete_probability: float  # 0-1
    months_to_action: int
    recommended_actions: List[str]
    confidence: float = 0.5


@dataclass
class CalendarEvent:
    date: str
    event_type: str  # "budget", "recompete", "option", "hiring_surge", "conference"
    title: str
    agency: str = ""
    program: str = ""
    priority: str = "medium"  # critical, high, medium, low
    details: str = ""


@dataclass
class BDCalendar:
    start_date: str
    end_date: str
    events: List[CalendarEvent]
    total_events: int = 0
    fiscal_year: int = 0


# =========================================
# AGENCY-SPECIFIC PATTERNS
# =========================================

AGENCY_PATTERNS = {
    "USAF": {
        "peak_months": [3, 4, 5, 6],
        "surge_months": [7, 8, 9],
        "slow_months": [10, 11, 12],
        "budget_cycle_offset_days": 0,
        "typical_procurement_lead_time_months": 12,
    },
    "Army": {
        "peak_months": [2, 3, 4, 5],
        "surge_months": [7, 8, 9],
        "slow_months": [10, 11],
        "budget_cycle_offset_days": 15,
        "typical_procurement_lead_time_months": 14,
    },
    "Navy": {
        "peak_months": [3, 4, 5],
        "surge_months": [7, 8, 9],
        "slow_months": [10, 11, 12],
        "budget_cycle_offset_days": 0,
        "typical_procurement_lead_time_months": 13,
    },
    "DIA": {
        "peak_months": [1, 2, 3, 4],
        "surge_months": [7, 8, 9],
        "slow_months": [10, 11],
        "budget_cycle_offset_days": 30,
        "typical_procurement_lead_time_months": 18,
    },
    "NGA": {
        "peak_months": [2, 3, 4],
        "surge_months": [8, 9],
        "slow_months": [10, 11, 12],
        "budget_cycle_offset_days": 15,
        "typical_procurement_lead_time_months": 15,
    },
    "NSA": {
        "peak_months": [1, 2, 3, 4, 5],
        "surge_months": [7, 8, 9],
        "slow_months": [10, 11],
        "budget_cycle_offset_days": 0,
        "typical_procurement_lead_time_months": 18,
    },
}

# Default pattern for unknown agencies
DEFAULT_PATTERN = {
    "peak_months": [3, 4, 5, 6],
    "surge_months": [7, 8, 9],
    "slow_months": [10, 11, 12],
    "budget_cycle_offset_days": 0,
    "typical_procurement_lead_time_months": 12,
}

# Federal conferences (month -> events)
FEDERAL_CONFERENCES = [
    {"month": 1, "name": "AFCEA West", "focus": "Navy/Marine IT"},
    {"month": 2, "name": "AUSA Global Force Symposium", "focus": "Army modernization"},
    {"month": 3, "name": "Satellite Conference", "focus": "Space/satellite"},
    {"month": 5, "name": "GEOINT Symposium", "focus": "GEOINT/ISR"},
    {"month": 6, "name": "DoDIIS Worldwide", "focus": "Defense intelligence"},
    {"month": 8, "name": "AFCEA TechNet Augusta", "focus": "Army cyber"},
    {"month": 9, "name": "Air & Space Forces Association", "focus": "USAF modernization"},
    {"month": 10, "name": "AUSA Annual Meeting", "focus": "Army programs"},
    {"month": 11, "name": "AFCEA MILCOM", "focus": "Military communications"},
]


class BudgetCyclePredictor:
    """Predict budget availability windows for BD timing."""

    def __init__(self, contracts_data: Optional[List[dict]] = None):
        self._contracts = contracts_data or []

    def set_contracts_data(self, data: List[dict]) -> None:
        self._contracts = data

    def _get_fiscal_quarter(self, dt: Optional[datetime] = None) -> int:
        """Get federal fiscal quarter (Q1=Oct-Dec, Q4=Jul-Sep)."""
        dt = dt or datetime.now(timezone.utc)
        month = dt.month
        if month >= 10:
            return 1
        elif month >= 7:
            return 4
        elif month >= 4:
            return 3
        else:
            return 2

    def _get_fiscal_year(self, dt: Optional[datetime] = None) -> int:
        """Get federal fiscal year."""
        dt = dt or datetime.now(timezone.utc)
        return dt.year + 1 if dt.month >= 10 else dt.year

    async def predict_spending_window(self, agency: str) -> SpendingWindow:
        """Predict current spending window and next opportunity."""
        now = datetime.now(timezone.utc)
        fq = self._get_fiscal_quarter(now)
        fy = self._get_fiscal_year(now)
        month = now.month

        pattern = AGENCY_PATTERNS.get(agency, DEFAULT_PATTERN)

        # Determine current phase
        if month in pattern.get("surge_months", []):
            phase = "surge"
            intensity = 0.9
        elif month in pattern.get("peak_months", []):
            phase = "peak"
            intensity = 0.7
        elif month in pattern.get("slow_months", []):
            phase = "new_fy"
            intensity = 0.3
        else:
            phase = "ramp_up"
            intensity = 0.5

        # Determine next significant window
        next_window, days_to_next = self._next_window(now, pattern)

        # Recommended actions by phase
        actions_by_phase = {
            "new_fy": [
                "Build relationships: budget owners setting priorities",
                "Submit white papers for upcoming requirements",
                "Schedule capability briefings with program offices",
            ],
            "ramp_up": [
                "Respond to RFIs and Sources Sought notices",
                "Position for upcoming solicitations",
                "Strengthen teaming arrangements",
            ],
            "peak": [
                "Submit proposals for active solicitations",
                "Accelerate candidate pipeline for anticipated awards",
                "Follow up on pending evaluations",
            ],
            "surge": [
                "Pursue quick-turn task orders and BPAs",
                "Use-or-lose: agencies spending remaining budget fast",
                "Position for contract modifications and ceiling increases",
            ],
        }

        return SpendingWindow(
            agency=agency,
            current_quarter=fq,
            current_phase=phase,
            spending_intensity=intensity,
            recommended_actions=actions_by_phase.get(phase, []),
            next_window=next_window,
            days_to_next_window=days_to_next,
            fiscal_year=fy,
            details=f"FY{fy} Q{fq}: {phase.replace('_', ' ').title()} phase for {agency}",
        )

    async def predict_recompete_timing(
        self, contract_id: str,
        contract_data: Optional[dict] = None,
    ) -> RecompetePrediction:
        """Predict when a contract will recompete."""
        # Find contract data
        contract = contract_data
        if not contract:
            contract = next(
                (c for c in self._contracts if c.get("id") == contract_id),
                None,
            )

        if not contract:
            return RecompetePrediction(
                contract_id=contract_id,
                contract_name="Unknown",
                current_pop_end="Unknown",
                options_remaining=0,
                predicted_rfi_date="Unknown",
                predicted_rfp_date="Unknown",
                predicted_award_date="Unknown",
                recompete_probability=0.5,
                months_to_action=0,
                recommended_actions=["Gather contract details first"],
                confidence=0.1,
            )

        contract_name = contract.get("name", contract.get("title", "Unknown"))
        pop_end_str = contract.get("pop_end", contract.get("period_of_performance_end", ""))
        options_remaining = contract.get("options_remaining", contract.get("option_years", 0))

        # Parse POP end date
        now = datetime.now(timezone.utc)
        try:
            if isinstance(pop_end_str, str) and pop_end_str:
                pop_end = datetime.fromisoformat(pop_end_str.replace("Z", "+00:00"))
                if pop_end.tzinfo is None:
                    pop_end = pop_end.replace(tzinfo=timezone.utc)
            elif isinstance(pop_end_str, datetime):
                pop_end = pop_end_str if pop_end_str.tzinfo else pop_end_str.replace(tzinfo=timezone.utc)
            else:
                pop_end = now + timedelta(days=365)
        except Exception:
            pop_end = now + timedelta(days=365)

        # Standard federal recompete timeline
        # RFI: ~18 months before POP end
        # RFP: ~12 months before POP end
        # Award: ~3 months before POP end
        rfi_date = pop_end - timedelta(days=18 * 30)
        rfp_date = pop_end - timedelta(days=12 * 30)
        award_date = pop_end - timedelta(days=3 * 30)

        # If options remain, adjust
        if options_remaining > 0:
            # Option exercise likely extends POP
            extended_end = pop_end + timedelta(days=options_remaining * 365)
            rfi_date = extended_end - timedelta(days=18 * 30)
            rfp_date = extended_end - timedelta(days=12 * 30)
            award_date = extended_end - timedelta(days=3 * 30)
            recompete_prob = max(0.2, 0.8 - options_remaining * 0.15)
        else:
            recompete_prob = 0.85

        months_to_rfi = max(0, int((rfi_date - now).days / 30))

        actions = []
        if months_to_rfi <= 6:
            actions.append("Immediate: RFI window approaching, prepare response")
        if months_to_rfi <= 12:
            actions.append("Build relationship with incumbent PM and COR")
        if months_to_rfi <= 18:
            actions.append("Start teaming discussions and past performance collection")
        if options_remaining > 0:
            actions.append(f"Monitor: {options_remaining} option year(s) may be exercised first")
        actions.append("Track SAM.gov for pre-solicitation notices")

        return RecompetePrediction(
            contract_id=contract_id,
            contract_name=contract_name,
            current_pop_end=pop_end.strftime("%Y-%m-%d"),
            options_remaining=options_remaining,
            predicted_rfi_date=rfi_date.strftime("%Y-%m-%d"),
            predicted_rfp_date=rfp_date.strftime("%Y-%m-%d"),
            predicted_award_date=award_date.strftime("%Y-%m-%d"),
            recompete_probability=round(recompete_prob, 2),
            months_to_action=months_to_rfi,
            recommended_actions=actions[:5],
            confidence=0.6 if pop_end_str else 0.3,
        )

    async def get_calendar(self, months: int = 12) -> BDCalendar:
        """Forward-looking BD calendar with budget, recompete, and events."""
        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=months * 30)
        events = []

        # Budget milestones
        fy = self._get_fiscal_year(now)
        budget_events = [
            (datetime(fy - 1, 10, 1, tzinfo=timezone.utc), f"FY{fy} Start", "New fiscal year begins"),
            (datetime(fy, 2, 1, tzinfo=timezone.utc), f"FY{fy} President's Budget", "Budget request submitted to Congress"),
            (datetime(fy, 7, 1, tzinfo=timezone.utc), f"FY{fy} Q4 Begins", "Use-or-lose spending surge starts"),
            (datetime(fy, 9, 30, tzinfo=timezone.utc), f"FY{fy} Ends", "Fiscal year ends, final obligations"),
            (datetime(fy, 10, 1, tzinfo=timezone.utc), f"FY{fy+1} Start", "New fiscal year begins"),
        ]

        for dt, title, details in budget_events:
            if now <= dt <= end_date:
                events.append(CalendarEvent(
                    date=dt.strftime("%Y-%m-%d"),
                    event_type="budget",
                    title=title,
                    priority="high",
                    details=details,
                ))

        # Conference events
        for conf in FEDERAL_CONFERENCES:
            conf_date = datetime(now.year, conf["month"], 15, tzinfo=timezone.utc)
            if conf_date < now:
                conf_date = conf_date.replace(year=now.year + 1)
            if conf_date <= end_date:
                events.append(CalendarEvent(
                    date=conf_date.strftime("%Y-%m-%d"),
                    event_type="conference",
                    title=conf["name"],
                    details=conf["focus"],
                    priority="medium",
                ))

        # Recompete predictions from stored contracts
        for contract in self._contracts[:20]:  # Limit to 20
            try:
                pred = await self.predict_recompete_timing(
                    contract.get("id", ""), contract_data=contract
                )
                rfi_date = datetime.fromisoformat(pred.predicted_rfi_date)
                if isinstance(rfi_date, datetime) and now <= rfi_date <= end_date:
                    events.append(CalendarEvent(
                        date=pred.predicted_rfi_date,
                        event_type="recompete",
                        title=f"Predicted RFI: {pred.contract_name}",
                        program=contract.get("program", ""),
                        priority="high" if pred.recompete_probability > 0.7 else "medium",
                        details=f"Recompete prob: {pred.recompete_probability:.0%}",
                    ))
            except Exception:
                pass

        # Quarterly hiring surge windows
        for q in range(1, 5):
            q_start_month = {1: 10, 2: 1, 3: 4, 4: 7}[q]
            q_year = fy - 1 if q == 1 else fy
            try:
                q_start = datetime(q_year, q_start_month, 1, tzinfo=timezone.utc)
                if now <= q_start <= end_date:
                    priority = "high" if q == 4 else "medium"
                    events.append(CalendarEvent(
                        date=q_start.strftime("%Y-%m-%d"),
                        event_type="hiring_surge" if q == 4 else "budget",
                        title=f"FY{fy} Q{q} Begins",
                        priority=priority,
                        details=f"Federal Q{q} hiring and procurement window",
                    ))
            except Exception:
                pass

        events.sort(key=lambda e: e.date)

        return BDCalendar(
            start_date=now.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            events=events,
            total_events=len(events),
            fiscal_year=fy,
        )

    def _next_window(self, now: datetime, pattern: dict) -> tuple:
        """Find the next significant procurement window."""
        month = now.month
        peak_months = pattern.get("peak_months", [4, 5, 6])
        surge_months = pattern.get("surge_months", [7, 8, 9])

        # Find next peak or surge month
        for check_months, label in [(peak_months, "Peak procurement"), (surge_months, "Q4 surge")]:
            for m in sorted(check_months):
                target_year = now.year
                if m <= month:
                    target_year += 1
                target_date = datetime(target_year, m, 1, tzinfo=timezone.utc)
                days = (target_date - now).days
                if days > 0:
                    return label, days

        # Default: next fiscal year start
        fy_start = datetime(now.year + 1, 10, 1, tzinfo=timezone.utc) if now.month >= 10 else datetime(now.year, 10, 1, tzinfo=timezone.utc)
        return "New fiscal year", max(1, (fy_start - now).days)


# =========================================
# SINGLETON
# =========================================

_predictor: Optional[BudgetCyclePredictor] = None


def get_budget_predictor() -> BudgetCyclePredictor:
    global _predictor
    if _predictor is None:
        _predictor = BudgetCyclePredictor()
    return _predictor
