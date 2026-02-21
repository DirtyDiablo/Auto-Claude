"""Intelligence Briefs router — generate, store, and deliver weekly briefs."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from Engine8_Knowledge.briefs.template_engine import BriefTemplateEngine
from Engine8_Knowledge.briefs.delivery import BriefDeliveryService

try:
    import structlog

    logger = structlog.get_logger("BriefsRouter")
except ImportError:
    logger = logging.getLogger("BriefsRouter")

router = APIRouter(prefix="/briefs", tags=["Intelligence Briefs"])

# ---------------------------------------------------------------------------
# Singleton services
# ---------------------------------------------------------------------------

_engine: Optional[BriefTemplateEngine] = None
_delivery: Optional[BriefDeliveryService] = None


def _get_engine() -> BriefTemplateEngine:
    global _engine
    if _engine is None:
        _engine = BriefTemplateEngine()
    return _engine


def _get_delivery() -> BriefDeliveryService:
    global _delivery
    if _delivery is None:
        _delivery = BriefDeliveryService()
    return _delivery


# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------


class GenerateBriefRequest(BaseModel):
    portfolio_id: str = Field("dcgs", description="Portfolio to generate brief for")
    period_days: int = Field(7, ge=1, le=90, description="Number of days to cover")


class BriefSectionResponse(BaseModel):
    title: str
    content: str
    data: Dict
    priority: str


class BriefResponse(BaseModel):
    id: str
    title: str
    period_start: str
    period_end: str
    generated_at: str
    sections: List[BriefSectionResponse]
    executive_summary: str
    portfolio: str


class BriefSummary(BaseModel):
    id: str
    title: str
    portfolio: str
    period_start: str
    period_end: str
    generated_at: str
    section_count: int


class DeliverRequest(BaseModel):
    recipients: List[str] = Field(..., description="Email addresses to deliver to")


class DeliveryResponse(BaseModel):
    status: str
    message: str
    brief_id: str
    recipients: List[str]
    would_send_subject: str
    timestamp: str


class ScheduleResponse(BaseModel):
    enabled: bool
    day: str
    hour: int
    description: str


class ScheduleToggleRequest(BaseModel):
    enabled: Optional[bool] = Field(None, description="Set schedule state; omit to toggle")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/generate", response_model=BriefResponse)
async def generate_brief(body: GenerateBriefRequest):
    """Generate a new intelligence brief and store it."""
    engine = _get_engine()
    delivery = _get_delivery()

    brief = engine.generate_brief(
        portfolio_id=body.portfolio_id,
        period_days=body.period_days,
    )
    delivery.store_brief(brief)

    logger.info("brief_generated_via_api", brief_id=brief.id)
    return brief.to_dict()


@router.get("", response_model=List[BriefSummary])
async def list_briefs(
    portfolio_id: Optional[str] = None,
    limit: int = 10,
):
    """List stored intelligence briefs."""
    delivery = _get_delivery()
    return delivery.list_briefs(portfolio_id=portfolio_id, limit=limit)


@router.get("/schedule", response_model=ScheduleResponse)
async def get_schedule():
    """Get the current automatic brief generation schedule."""
    delivery = _get_delivery()
    return delivery.get_schedule()


@router.post("/schedule/toggle", response_model=ScheduleResponse)
async def toggle_schedule(body: ScheduleToggleRequest = ScheduleToggleRequest()):
    """Enable or disable automatic brief generation."""
    delivery = _get_delivery()
    return delivery.toggle_schedule(enabled=body.enabled)


@router.get("/{brief_id}", response_model=BriefResponse)
async def get_brief(brief_id: str):
    """Retrieve a specific intelligence brief by ID."""
    delivery = _get_delivery()
    brief = delivery.get_brief(brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail=f"Brief {brief_id} not found")
    return brief.to_dict()


@router.get("/{brief_id}/html", response_class=HTMLResponse)
async def get_brief_html(brief_id: str):
    """Retrieve a brief rendered as HTML."""
    delivery = _get_delivery()
    brief = delivery.get_brief(brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail=f"Brief {brief_id} not found")
    return HTMLResponse(content=brief.to_html())


@router.get("/{brief_id}/markdown", response_class=PlainTextResponse)
async def get_brief_markdown(brief_id: str):
    """Retrieve a brief rendered as Markdown."""
    delivery = _get_delivery()
    brief = delivery.get_brief(brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail=f"Brief {brief_id} not found")
    return PlainTextResponse(content=brief.to_markdown())


@router.post("/{brief_id}/deliver", response_model=DeliveryResponse)
async def deliver_brief(brief_id: str, body: DeliverRequest):
    """Deliver a brief via email (stub)."""
    delivery = _get_delivery()
    brief = delivery.get_brief(brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail=f"Brief {brief_id} not found")
    result = delivery.deliver_email(brief, body.recipients)
    return result
