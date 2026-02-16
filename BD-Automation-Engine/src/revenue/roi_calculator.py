"""Phase 36A — ROI Calculator

Measure return on investment across dimensions:
  - Campaign ROI: effort invested vs revenue generated
  - Contact ROI: effort on contact vs revenue from their placements
  - Program ROI: BD investment vs revenue from program
  - Channel ROI: which outreach channel drives most revenue per dollar
  - Tool ROI: cost of tools vs attributed revenue
  - Time-to-ROI: how long from first outreach to first revenue
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================


@dataclass
class CampaignROI:
    """ROI for a BD campaign."""

    campaign_id: str
    campaign_name: str
    total_investment: float = 0.0  # Time + money invested
    total_revenue: float = 0.0
    roi_pct: float = 0.0  # (revenue - investment) / investment * 100
    placements: int = 0
    revenue_per_dollar: float = 0.0
    time_to_first_revenue_days: int = 0


@dataclass
class ContactROI:
    """ROI for a client contact."""

    contact_id: str
    contact_name: str
    total_touchpoints: int = 0
    estimated_effort_hours: float = 0.0
    estimated_effort_cost: float = 0.0
    total_revenue: float = 0.0
    roi_pct: float = 0.0
    placements: int = 0
    first_contact_date: str = ""
    first_revenue_date: str = ""
    time_to_revenue_days: int = 0


@dataclass
class ProgramROI:
    """ROI for a program."""

    program: str
    total_investment: float = 0.0
    total_revenue: float = 0.0
    roi_pct: float = 0.0
    placements: int = 0
    active_placements: int = 0
    avg_margin_pct: float = 0.0
    time_to_first_revenue_days: int = 0


@dataclass
class ChannelROI:
    """ROI for an outreach channel."""

    channel: str
    deals_sourced: int = 0
    deals_won: int = 0
    total_revenue: float = 0.0
    total_cost: float = 0.0
    roi_pct: float = 0.0
    conversion_rate: float = 0.0
    avg_deal_value: float = 0.0


@dataclass
class ToolROI:
    """ROI for a tool/platform."""

    tool_name: str
    monthly_cost: float = 0.0
    annual_cost: float = 0.0
    attributed_revenue: float = 0.0
    roi_pct: float = 0.0
    placements_attributed: int = 0


# =========================================
# ROI CALCULATOR
# =========================================


class ROICalculator:
    """Calculate ROI across multiple dimensions."""

    def __init__(self):
        self._campaigns: List[Dict[str, Any]] = []
        self._contacts: List[Dict[str, Any]] = []
        self._programs: List[Dict[str, Any]] = []
        self._channels: List[Dict[str, Any]] = []
        self._tools: List[Dict[str, Any]] = []

    # -----------------------------------------
    # Data loading
    # -----------------------------------------

    def set_campaign_data(self, campaigns: List[Dict[str, Any]]) -> None:
        self._campaigns = campaigns

    def set_contact_data(self, contacts: List[Dict[str, Any]]) -> None:
        self._contacts = contacts

    def set_program_data(self, programs: List[Dict[str, Any]]) -> None:
        self._programs = programs

    def set_channel_data(self, channels: List[Dict[str, Any]]) -> None:
        self._channels = channels

    def set_tool_data(self, tools: List[Dict[str, Any]]) -> None:
        self._tools = tools

    # -----------------------------------------
    # Campaign ROI
    # -----------------------------------------

    def calculate_campaign_roi(self) -> List[CampaignROI]:
        """Calculate ROI for each campaign."""
        results = []
        for c in self._campaigns:
            investment = c.get("investment", 0)
            revenue = c.get("revenue", 0)
            roi = ((revenue - investment) / investment * 100) if investment > 0 else 0
            rpd = revenue / investment if investment > 0 else 0

            results.append(
                CampaignROI(
                    campaign_id=c.get("id", ""),
                    campaign_name=c.get("name", ""),
                    total_investment=investment,
                    total_revenue=revenue,
                    roi_pct=round(roi, 2),
                    placements=c.get("placements", 0),
                    revenue_per_dollar=round(rpd, 2),
                    time_to_first_revenue_days=c.get("time_to_revenue_days", 0),
                )
            )

        results.sort(key=lambda r: r.roi_pct, reverse=True)
        return results

    # -----------------------------------------
    # Contact ROI
    # -----------------------------------------

    def calculate_contact_roi(self, hourly_cost: float = 75.0) -> List[ContactROI]:
        """Calculate ROI for each contact relationship."""
        results = []
        for c in self._contacts:
            touchpoints = c.get("touchpoints", 0)
            effort_hours = c.get(
                "effort_hours", touchpoints * 0.5
            )  # ~30 min per touchpoint
            effort_cost = effort_hours * hourly_cost
            revenue = c.get("revenue", 0)
            roi = (
                ((revenue - effort_cost) / effort_cost * 100) if effort_cost > 0 else 0
            )

            # Time to revenue
            first_contact = c.get("first_contact_date", "")
            first_revenue = c.get("first_revenue_date", "")
            days = 0
            if first_contact and first_revenue:
                try:
                    fc = datetime.fromisoformat(first_contact.replace("Z", "+00:00"))
                    fr = datetime.fromisoformat(first_revenue.replace("Z", "+00:00"))
                    if fc.tzinfo is None:
                        fc = fc.replace(tzinfo=timezone.utc)
                    if fr.tzinfo is None:
                        fr = fr.replace(tzinfo=timezone.utc)
                    days = (fr - fc).days
                except (ValueError, TypeError):
                    pass

            results.append(
                ContactROI(
                    contact_id=c.get("id", ""),
                    contact_name=c.get("name", ""),
                    total_touchpoints=touchpoints,
                    estimated_effort_hours=round(effort_hours, 1),
                    estimated_effort_cost=round(effort_cost, 2),
                    total_revenue=revenue,
                    roi_pct=round(roi, 2),
                    placements=c.get("placements", 0),
                    first_contact_date=first_contact,
                    first_revenue_date=first_revenue,
                    time_to_revenue_days=days,
                )
            )

        results.sort(key=lambda r: r.roi_pct, reverse=True)
        return results

    # -----------------------------------------
    # Program ROI
    # -----------------------------------------

    def calculate_program_roi(self) -> List[ProgramROI]:
        """Calculate ROI for each program."""
        results = []
        for p in self._programs:
            investment = p.get("investment", 0)
            revenue = p.get("revenue", 0)
            roi = ((revenue - investment) / investment * 100) if investment > 0 else 0

            results.append(
                ProgramROI(
                    program=p.get("program", ""),
                    total_investment=investment,
                    total_revenue=revenue,
                    roi_pct=round(roi, 2),
                    placements=p.get("placements", 0),
                    active_placements=p.get("active_placements", 0),
                    avg_margin_pct=p.get("avg_margin_pct", 0),
                    time_to_first_revenue_days=p.get("time_to_revenue_days", 0),
                )
            )

        results.sort(key=lambda r: r.roi_pct, reverse=True)
        return results

    # -----------------------------------------
    # Channel ROI
    # -----------------------------------------

    def calculate_channel_roi(self) -> List[ChannelROI]:
        """Calculate ROI per outreach channel."""
        results = []
        for ch in self._channels:
            sourced = ch.get("deals_sourced", 0)
            won = ch.get("deals_won", 0)
            revenue = ch.get("revenue", 0)
            cost = ch.get("cost", 0)
            roi = ((revenue - cost) / cost * 100) if cost > 0 else 0
            conv = (won / sourced * 100) if sourced > 0 else 0
            avg_val = revenue / won if won > 0 else 0

            results.append(
                ChannelROI(
                    channel=ch.get("channel", ""),
                    deals_sourced=sourced,
                    deals_won=won,
                    total_revenue=revenue,
                    total_cost=cost,
                    roi_pct=round(roi, 2),
                    conversion_rate=round(conv, 1),
                    avg_deal_value=round(avg_val, 2),
                )
            )

        results.sort(key=lambda r: r.roi_pct, reverse=True)
        return results

    # -----------------------------------------
    # Tool ROI
    # -----------------------------------------

    def calculate_tool_roi(self) -> List[ToolROI]:
        """Calculate ROI for each tool/platform."""
        results = []
        for t in self._tools:
            monthly = t.get("monthly_cost", 0)
            annual = monthly * 12
            revenue = t.get("attributed_revenue", 0)
            roi = ((revenue - annual) / annual * 100) if annual > 0 else 0

            results.append(
                ToolROI(
                    tool_name=t.get("name", ""),
                    monthly_cost=monthly,
                    annual_cost=annual,
                    attributed_revenue=revenue,
                    roi_pct=round(roi, 2),
                    placements_attributed=t.get("placements", 0),
                )
            )

        results.sort(key=lambda r: r.roi_pct, reverse=True)
        return results

    # -----------------------------------------
    # Summary
    # -----------------------------------------

    def get_roi_summary(self) -> Dict[str, Any]:
        """Overall ROI summary."""
        campaigns = self.calculate_campaign_roi()
        programs = self.calculate_program_roi()
        channels = self.calculate_channel_roi()

        total_investment = sum(c.total_investment for c in campaigns) + sum(
            p.total_investment for p in programs
        )
        total_revenue = sum(c.total_revenue for c in campaigns) + sum(
            p.total_revenue for p in programs
        )
        overall_roi = (
            ((total_revenue - total_investment) / total_investment * 100)
            if total_investment > 0
            else 0
        )

        best_channel = channels[0].channel if channels else "N/A"

        return {
            "total_investment": round(total_investment, 2),
            "total_revenue": round(total_revenue, 2),
            "overall_roi_pct": round(overall_roi, 2),
            "campaign_count": len(campaigns),
            "program_count": len(programs),
            "best_channel": best_channel,
        }


# =========================================
# SINGLETON
# =========================================

_calculator: Optional[ROICalculator] = None


def get_roi_calculator() -> ROICalculator:
    global _calculator
    if _calculator is None:
        _calculator = ROICalculator()
    return _calculator
