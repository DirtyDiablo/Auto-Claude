"""Phase 36A — Revenue Intelligence API

16 endpoints for revenue tracking, deal lifecycle, ROI analysis, and executive dashboards.
"""

import logging
from typing import Optional

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

from src.revenue.revenue_tracker import (
    RevenueTracker,
    Placement,
    get_revenue_tracker,
)
from src.revenue.deal_lifecycle import (
    DealLifecycleEngine,
    get_deal_engine,
)
from src.revenue.roi_calculator import (
    ROICalculator,
    get_roi_calculator,
)
from src.revenue.executive_analytics import (
    ExecutiveAnalytics,
    get_executive_analytics,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/revenue", tags=["revenue"])


# =========================================
# REQUEST MODELS
# =========================================


class PlacementRequest(BaseModel):
    id: str
    contractor_name: str
    client: str
    program: str
    role_title: str
    bill_rate: float = 0.0
    pay_rate: float = 0.0
    start_date: str = ""
    end_date: str = ""
    rep: str = ""
    contact_id: str = ""
    location: str = ""
    clearance: str = ""
    hours_per_week: float = 40.0


# =========================================
# SINGLETONS
# =========================================

_tracker: Optional[RevenueTracker] = None
_deal_engine: Optional[DealLifecycleEngine] = None
_roi_calc: Optional[ROICalculator] = None
_exec_analytics: Optional[ExecutiveAnalytics] = None


def _get_tracker() -> RevenueTracker:
    global _tracker
    if _tracker is None:
        _tracker = get_revenue_tracker()
    return _tracker


def _get_deal_engine() -> DealLifecycleEngine:
    global _deal_engine
    if _deal_engine is None:
        _deal_engine = get_deal_engine()
    return _deal_engine


def _get_roi() -> ROICalculator:
    global _roi_calc
    if _roi_calc is None:
        _roi_calc = get_roi_calculator()
    return _roi_calc


def _get_exec() -> ExecutiveAnalytics:
    global _exec_analytics
    if _exec_analytics is None:
        _exec_analytics = get_executive_analytics()
    return _exec_analytics


# =========================================
# REVENUE ENDPOINTS (1-7)
# =========================================


@router.get("/summary")
async def revenue_summary(period: Optional[str] = None):
    """Revenue overview with period comparison."""
    tracker = _get_tracker()
    summary = tracker.get_revenue_summary(period)
    return {
        "period": summary.period,
        "total_revenue": summary.total_revenue,
        "total_cost": summary.total_cost,
        "total_margin": summary.total_margin,
        "avg_margin_pct": summary.avg_margin_pct,
        "placement_count": summary.placement_count,
        "active_placements": summary.active_placements,
    }


@router.get("/by-program")
async def revenue_by_program():
    """Revenue breakdown by program."""
    tracker = _get_tracker()
    by_program = tracker.get_revenue_by_program()
    total = sum(by_program.values())
    return {
        "programs": [
            {
                "program": prog,
                "revenue": round(rev, 2),
                "share_pct": round(rev / total * 100, 1) if total > 0 else 0,
            }
            for prog, rev in by_program.items()
        ],
        "total_revenue": round(total, 2),
        "total_programs": len(by_program),
    }


@router.get("/by-rep")
async def revenue_by_rep():
    """Revenue by sales rep."""
    tracker = _get_tracker()
    by_rep = tracker.get_revenue_by_rep()
    return {
        "reps": [{"rep": rep, "revenue": round(rev, 2)} for rep, rev in by_rep.items()],
        "total": len(by_rep),
    }


@router.get("/by-contact")
async def revenue_by_contact():
    """Revenue attributed to contacts."""
    tracker = _get_tracker()
    by_contact = tracker.get_revenue_by_contact()
    return {
        "contacts": [
            {"contact_id": cid, "revenue": round(rev, 2)}
            for cid, rev in by_contact.items()
        ],
        "total": len(by_contact),
    }


@router.get("/forecast")
async def revenue_forecast(months: int = 12):
    """Revenue waterfall forecast."""
    tracker = _get_tracker()
    forecast = tracker.forecast_revenue(months_ahead=months)
    total_projected = sum(f["projected_revenue"] for f in forecast)
    return {
        "forecast": forecast,
        "total_projected": round(total_projected, 2),
        "months": months,
    }


@router.get("/margins")
async def margin_analysis():
    """Margin analysis and trends."""
    tracker = _get_tracker()
    analysis = tracker.get_margin_analysis()
    return {
        "avg_margin_pct": analysis.avg_margin_pct,
        "margin_by_program": analysis.margin_by_program,
        "margin_trend": analysis.margin_trend,
        "highest_margin_program": analysis.highest_margin_program,
        "lowest_margin_program": analysis.lowest_margin_program,
    }


@router.get("/concentration")
async def concentration_risk():
    """Revenue concentration risk."""
    tracker = _get_tracker()
    risk = tracker.get_concentration_risk()
    return {
        "top_programs": risk.top_programs,
        "top_3_pct": risk.top_3_pct,
        "herfindahl_index": risk.herfindahl_index,
        "risk_level": risk.risk_level,
        "diversification_score": risk.diversification_score,
    }


# =========================================
# DEAL LIFECYCLE ENDPOINTS (8-10)
# =========================================


@router.get("/deals/lifecycle")
async def deal_lifecycle():
    """Deal stage analytics."""
    engine = _get_deal_engine()
    summary = engine.get_lifecycle_summary()
    return summary


@router.get("/deals/velocity")
async def deal_velocity():
    """Stage velocity metrics."""
    engine = _get_deal_engine()
    velocity = engine.get_stage_velocity()
    return {
        "stages": [
            {
                "stage": v.stage,
                "avg_days": v.avg_days,
                "median_days": v.median_days,
                "deal_count": v.deal_count,
            }
            for v in velocity
        ],
        "total_stages": len(velocity),
    }


@router.get("/deals/stale")
async def stale_deals():
    """Stale deals needing attention."""
    engine = _get_deal_engine()
    stale = engine.detect_stale_deals()
    return {
        "stale_deals": [
            {
                "deal_id": s.deal_id,
                "title": s.title,
                "stage": s.stage,
                "days_in_stage": s.days_in_stage,
                "overdue_by": s.overdue_by,
                "recommended_action": s.recommended_action,
            }
            for s in stale
        ],
        "total": len(stale),
    }


# =========================================
# ROI ENDPOINTS (11-14)
# =========================================


@router.get("/roi/campaigns")
async def campaign_roi():
    """Campaign ROI analysis."""
    calc = _get_roi()
    campaigns = calc.calculate_campaign_roi()
    return {
        "campaigns": [
            {
                "campaign_id": c.campaign_id,
                "campaign_name": c.campaign_name,
                "investment": c.total_investment,
                "revenue": c.total_revenue,
                "roi_pct": c.roi_pct,
                "revenue_per_dollar": c.revenue_per_dollar,
            }
            for c in campaigns
        ],
        "total": len(campaigns),
    }


@router.get("/roi/contacts")
async def contact_roi():
    """Contact ROI analysis."""
    calc = _get_roi()
    contacts = calc.calculate_contact_roi()
    return {
        "contacts": [
            {
                "contact_id": c.contact_id,
                "contact_name": c.contact_name,
                "touchpoints": c.total_touchpoints,
                "effort_cost": c.estimated_effort_cost,
                "revenue": c.total_revenue,
                "roi_pct": c.roi_pct,
                "placements": c.placements,
            }
            for c in contacts
        ],
        "total": len(contacts),
    }


@router.get("/roi/programs")
async def program_roi():
    """Program ROI analysis."""
    calc = _get_roi()
    programs = calc.calculate_program_roi()
    return {
        "programs": [
            {
                "program": p.program,
                "investment": p.total_investment,
                "revenue": p.total_revenue,
                "roi_pct": p.roi_pct,
                "placements": p.placements,
                "avg_margin_pct": p.avg_margin_pct,
            }
            for p in programs
        ],
        "total": len(programs),
    }


@router.get("/roi/channels")
async def channel_roi():
    """Channel ROI analysis."""
    calc = _get_roi()
    channels = calc.calculate_channel_roi()
    return {
        "channels": [
            {
                "channel": c.channel,
                "deals_sourced": c.deals_sourced,
                "deals_won": c.deals_won,
                "revenue": c.total_revenue,
                "cost": c.total_cost,
                "roi_pct": c.roi_pct,
                "conversion_rate": c.conversion_rate,
            }
            for c in channels
        ],
        "total": len(channels),
    }


# =========================================
# EXECUTIVE SUMMARY (15)
# =========================================


@router.get("/executive-summary")
async def executive_summary(
    period: Optional[str] = None, prior_period: Optional[str] = None
):
    """Auto-generated executive summary."""
    exec_analytics = _get_exec()
    summary = exec_analytics.generate_executive_summary(
        period=period or "",
        prior_period=prior_period or "",
    )
    return {
        "period": summary.period,
        "total_revenue": summary.total_revenue,
        "target_revenue": summary.target_revenue,
        "attainment_pct": summary.attainment_pct,
        "weighted_pipeline": summary.weighted_pipeline,
        "active_placements": summary.active_placements,
        "new_placements": summary.new_placements,
        "avg_margin_pct": summary.avg_margin_pct,
        "top_accounts": summary.top_accounts,
        "diversification": {
            "score": summary.diversification.score,
            "assessment": summary.diversification.assessment,
        }
        if summary.diversification
        else None,
        "narrative": summary.narrative,
        "generated_at": summary.generated_at,
    }


# =========================================
# PLACEMENT RECORDING (16)
# =========================================


@router.post("/placements")
async def record_placement(req: PlacementRequest):
    """Record new placement + revenue data."""
    tracker = _get_tracker()
    placement = Placement(
        id=req.id,
        contractor_name=req.contractor_name,
        client=req.client,
        program=req.program,
        role_title=req.role_title,
        bill_rate=req.bill_rate,
        pay_rate=req.pay_rate,
        start_date=req.start_date,
        end_date=req.end_date,
        rep=req.rep,
        contact_id=req.contact_id,
        location=req.location,
        clearance=req.clearance,
        hours_per_week=req.hours_per_week,
    )
    tracker.add_placement(placement)
    return {
        "status": "recorded",
        "placement_id": placement.id,
        "projected_annual_revenue": round(
            placement.bill_rate * placement.hours_per_week * 52, 2
        ),
    }


# =========================================
# INTEGRATION
# =========================================


def configure_revenue(app_instance: FastAPI) -> None:
    """Configure revenue routes on an existing FastAPI app."""
    app_instance.include_router(router)


def include_revenue_router(app_instance: FastAPI) -> None:
    """Include revenue router in FastAPI app."""
    app_instance.include_router(router)
