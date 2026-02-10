"""Phase 36A — Revenue Tracker

Track revenue from placement to billing:
  Placement → Start Date → Billing Start → Invoice → Payment → Revenue Recognized
  - Per-placement metrics: bill rate, pay rate, margin, projected revenue
  - Revenue waterfall: monthly/quarterly/annual projections
  - Revenue by: program, contact, rep, location, role type
  - Margin analysis: avg margin by program, trend over time
  - Revenue concentration risk: % from top 3 programs
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class Placement:
    """Single placement record."""
    id: str
    contractor_name: str
    client: str
    program: str
    role_title: str
    bill_rate: float = 0.0          # $/hr billed to client
    pay_rate: float = 0.0           # $/hr paid to contractor
    start_date: str = ""
    end_date: str = ""
    status: str = "active"          # active, completed, terminated
    rep: str = ""                   # BD rep who sourced
    contact_id: str = ""            # Client contact who approved
    location: str = ""
    clearance: str = ""
    hours_per_week: float = 40.0
    billing_started: bool = True


@dataclass
class RevenueRecord:
    """Revenue recognized from a placement."""
    placement_id: str
    period: str                     # YYYY-MM
    billed_hours: float = 0.0
    bill_amount: float = 0.0
    pay_amount: float = 0.0
    margin: float = 0.0
    margin_pct: float = 0.0


@dataclass
class RevenueSummary:
    """Revenue summary for a period."""
    period: str
    total_revenue: float = 0.0
    total_cost: float = 0.0
    total_margin: float = 0.0
    avg_margin_pct: float = 0.0
    placement_count: int = 0
    active_placements: int = 0


@dataclass
class MarginAnalysis:
    """Margin analysis results."""
    avg_margin_pct: float = 0.0
    margin_by_program: Dict[str, float] = field(default_factory=dict)
    margin_trend: List[Dict[str, Any]] = field(default_factory=list)
    highest_margin_program: str = ""
    lowest_margin_program: str = ""


@dataclass
class ConcentrationRisk:
    """Revenue concentration risk assessment."""
    top_programs: List[Dict[str, Any]] = field(default_factory=list)
    top_3_pct: float = 0.0
    herfindahl_index: float = 0.0   # 0-1, higher = more concentrated
    risk_level: str = "low"         # low, moderate, high, critical
    diversification_score: float = 0.0  # 0-100


# =========================================
# TRACKER
# =========================================

class RevenueTracker:
    """Track revenue from placement to billing."""

    def __init__(self):
        self._placements: Dict[str, Placement] = {}
        self._revenue_records: List[RevenueRecord] = []

    def add_placement(self, placement: Placement) -> None:
        """Record a new placement."""
        self._placements[placement.id] = placement

    def set_placements(self, placements: List[Placement]) -> None:
        """Set all placements."""
        self._placements = {p.id: p for p in placements}

    def add_revenue_record(self, record: RevenueRecord) -> None:
        """Add a revenue record for a period."""
        self._revenue_records.append(record)

    def get_placement(self, placement_id: str) -> Optional[Placement]:
        return self._placements.get(placement_id)

    def get_active_placements(self) -> List[Placement]:
        return [p for p in self._placements.values() if p.status == "active"]

    # -----------------------------------------
    # Revenue summary
    # -----------------------------------------

    def get_revenue_summary(self, period: Optional[str] = None) -> RevenueSummary:
        """Get revenue summary, optionally filtered by period (YYYY-MM or YYYY-QN or YYYY)."""
        records = self._revenue_records
        if period:
            records = [r for r in records if r.period.startswith(period)]

        if not records:
            return RevenueSummary(
                period=period or "all",
                placement_count=len(self._placements),
                active_placements=len(self.get_active_placements()),
            )

        total_rev = sum(r.bill_amount for r in records)
        total_cost = sum(r.pay_amount for r in records)
        total_margin = total_rev - total_cost
        avg_margin = (total_margin / total_rev * 100) if total_rev > 0 else 0

        return RevenueSummary(
            period=period or "all",
            total_revenue=round(total_rev, 2),
            total_cost=round(total_cost, 2),
            total_margin=round(total_margin, 2),
            avg_margin_pct=round(avg_margin, 2),
            placement_count=len(self._placements),
            active_placements=len(self.get_active_placements()),
        )

    # -----------------------------------------
    # Revenue by dimension
    # -----------------------------------------

    def get_revenue_by_program(self) -> Dict[str, float]:
        """Revenue breakdown by program."""
        by_prog: Dict[str, float] = defaultdict(float)
        for record in self._revenue_records:
            placement = self._placements.get(record.placement_id)
            if placement:
                by_prog[placement.program] += record.bill_amount
        return dict(sorted(by_prog.items(), key=lambda x: x[1], reverse=True))

    def get_revenue_by_rep(self) -> Dict[str, float]:
        """Revenue breakdown by BD rep."""
        by_rep: Dict[str, float] = defaultdict(float)
        for record in self._revenue_records:
            placement = self._placements.get(record.placement_id)
            if placement and placement.rep:
                by_rep[placement.rep] += record.bill_amount
        return dict(sorted(by_rep.items(), key=lambda x: x[1], reverse=True))

    def get_revenue_by_contact(self) -> Dict[str, float]:
        """Revenue attributed to client contacts."""
        by_contact: Dict[str, float] = defaultdict(float)
        for record in self._revenue_records:
            placement = self._placements.get(record.placement_id)
            if placement and placement.contact_id:
                by_contact[placement.contact_id] += record.bill_amount
        return dict(sorted(by_contact.items(), key=lambda x: x[1], reverse=True))

    # -----------------------------------------
    # Revenue forecast / waterfall
    # -----------------------------------------

    def forecast_revenue(self, months_ahead: int = 12) -> List[Dict[str, Any]]:
        """Project revenue waterfall for active placements."""
        active = self.get_active_placements()
        now = datetime.now(timezone.utc)

        forecast = []
        for month_offset in range(months_ahead):
            year = now.year + (now.month + month_offset - 1) // 12
            month = (now.month + month_offset - 1) % 12 + 1
            period = f"{year}-{month:02d}"

            monthly_rev = 0.0
            monthly_cost = 0.0
            active_count = 0

            for p in active:
                # Check if placement is within period
                if p.end_date:
                    try:
                        end = datetime.fromisoformat(p.end_date.replace("Z", "+00:00"))
                        if end.tzinfo is None:
                            end = end.replace(tzinfo=timezone.utc)
                        end_period = f"{end.year}-{end.month:02d}"
                        if end_period < period:
                            continue
                    except (ValueError, TypeError):
                        pass

                weekly_hours = p.hours_per_week
                monthly_hours = weekly_hours * 4.33  # avg weeks per month
                monthly_rev += p.bill_rate * monthly_hours
                monthly_cost += p.pay_rate * monthly_hours
                active_count += 1

            margin = monthly_rev - monthly_cost
            margin_pct = (margin / monthly_rev * 100) if monthly_rev > 0 else 0

            forecast.append({
                "period": period,
                "projected_revenue": round(monthly_rev, 2),
                "projected_cost": round(monthly_cost, 2),
                "projected_margin": round(margin, 2),
                "margin_pct": round(margin_pct, 2),
                "active_placements": active_count,
            })

        return forecast

    # -----------------------------------------
    # Margin analysis
    # -----------------------------------------

    def get_margin_analysis(self) -> MarginAnalysis:
        """Analyze margins across programs."""
        if not self._revenue_records:
            return MarginAnalysis()

        # Overall avg margin
        total_rev = sum(r.bill_amount for r in self._revenue_records)
        total_cost = sum(r.pay_amount for r in self._revenue_records)
        avg_margin = ((total_rev - total_cost) / total_rev * 100) if total_rev > 0 else 0

        # By program
        prog_rev: Dict[str, float] = defaultdict(float)
        prog_cost: Dict[str, float] = defaultdict(float)
        for r in self._revenue_records:
            p = self._placements.get(r.placement_id)
            if p:
                prog_rev[p.program] += r.bill_amount
                prog_cost[p.program] += r.pay_amount

        margin_by_prog = {}
        for prog in prog_rev:
            rev = prog_rev[prog]
            cost = prog_cost[prog]
            margin_by_prog[prog] = round(((rev - cost) / rev * 100) if rev > 0 else 0, 2)

        # Margin trend by period
        period_rev: Dict[str, float] = defaultdict(float)
        period_cost: Dict[str, float] = defaultdict(float)
        for r in self._revenue_records:
            period_rev[r.period] += r.bill_amount
            period_cost[r.period] += r.pay_amount

        trend = []
        for period in sorted(period_rev.keys()):
            rev = period_rev[period]
            cost = period_cost[period]
            pct = ((rev - cost) / rev * 100) if rev > 0 else 0
            trend.append({"period": period, "margin_pct": round(pct, 2)})

        highest = max(margin_by_prog, key=margin_by_prog.get) if margin_by_prog else ""
        lowest = min(margin_by_prog, key=margin_by_prog.get) if margin_by_prog else ""

        return MarginAnalysis(
            avg_margin_pct=round(avg_margin, 2),
            margin_by_program=margin_by_prog,
            margin_trend=trend,
            highest_margin_program=highest,
            lowest_margin_program=lowest,
        )

    # -----------------------------------------
    # Concentration risk
    # -----------------------------------------

    def get_concentration_risk(self) -> ConcentrationRisk:
        """Assess revenue concentration risk."""
        by_program = self.get_revenue_by_program()
        if not by_program:
            return ConcentrationRisk(risk_level="low", diversification_score=100.0)

        total_rev = sum(by_program.values())
        if total_rev == 0:
            return ConcentrationRisk(risk_level="low", diversification_score=100.0)

        # Top programs with share
        top_programs = []
        for prog, rev in list(by_program.items())[:10]:
            share = rev / total_rev * 100
            top_programs.append({
                "program": prog,
                "revenue": round(rev, 2),
                "share_pct": round(share, 2),
            })

        # Top 3 concentration
        top_3_rev = sum(item["revenue"] for item in top_programs[:3])
        top_3_pct = (top_3_rev / total_rev * 100) if total_rev > 0 else 0

        # Herfindahl-Hirschman Index (normalized 0-1)
        shares = [(v / total_rev) for v in by_program.values()]
        hhi = sum(s * s for s in shares)

        # Risk level
        if top_3_pct > 90:
            risk = "critical"
        elif top_3_pct > 75:
            risk = "high"
        elif top_3_pct > 50:
            risk = "moderate"
        else:
            risk = "low"

        # Diversification score (inverse of concentration)
        n = len(by_program)
        min_hhi = 1.0 / n if n > 0 else 1.0
        diversification = ((1 - hhi) / (1 - min_hhi) * 100) if min_hhi < 1 else 0

        return ConcentrationRisk(
            top_programs=top_programs,
            top_3_pct=round(top_3_pct, 2),
            herfindahl_index=round(hhi, 4),
            risk_level=risk,
            diversification_score=round(max(0, min(100, diversification)), 2),
        )


# =========================================
# SINGLETON
# =========================================

_tracker: Optional[RevenueTracker] = None


def get_revenue_tracker() -> RevenueTracker:
    global _tracker
    if _tracker is None:
        _tracker = RevenueTracker()
    return _tracker
