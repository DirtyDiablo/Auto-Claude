"""KPI Dashboard router — executive BD intelligence metrics."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from Engine8_Knowledge.services.kpi_service import KPIService

try:
    import structlog

    logger = structlog.get_logger("KPIRouter")
except ImportError:
    logger = logging.getLogger("KPIRouter")

router = APIRouter(prefix="/kpi", tags=["Executive KPIs"])

# Singleton service instance
_kpi_service: Optional[KPIService] = None


def _get_service() -> KPIService:
    """Lazy-init KPI service singleton."""
    global _kpi_service
    if _kpi_service is None:
        _kpi_service = KPIService()
    return _kpi_service


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------


class DatePeriod(BaseModel):
    start_date: str = Field(..., description="Period start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Period end date (YYYY-MM-DD)")


class PipelineVelocityResponse(BaseModel):
    period: DatePeriod
    stages: Dict[str, int] = Field(..., description="Count per pipeline stage")
    total_processed: int
    velocity_per_day: float
    data_source: str


class WinRateDetail(BaseModel):
    submitted: int
    won: int
    rate: float


class OverallWinRate(BaseModel):
    total_submitted: int
    won: int
    rate: float


class WinRateResponse(BaseModel):
    period: DatePeriod
    overall: OverallWinRate
    by_program: Dict[str, WinRateDetail]
    by_company: Dict[str, WinRateDetail]
    by_clearance: Dict[str, WinRateDetail]
    data_source: str


class FunnelStage(BaseModel):
    stage: str
    count: int
    conversion_rate: float
    drop_off: int


class ConversionFunnelResponse(BaseModel):
    period: DatePeriod
    funnel: List[FunnelStage]
    overall_conversion: float
    total_scraped: int
    total_won: int
    data_source: str


class CompetitorEntry(BaseModel):
    company: str
    job_count: int
    market_share: float
    trend: str


class CompetitiveLandscapeResponse(BaseModel):
    competitors: List[CompetitorEntry]
    total_market_positions: int
    top_competitor: Optional[str]
    data_source: str
    program_filter: Optional[str] = None


class ContactEngagementResponse(BaseModel):
    period: DatePeriod
    total_contacts: int
    tier_distribution: Dict[str, int]
    engagement_rates: Dict[str, float]
    response_rates: Dict[str, float]
    highest_engagement_tier: str
    data_source: str


class ScoreTierInfo(BaseModel):
    count: int
    min_score: int
    label: str


class ProgramScoreInfo(BaseModel):
    avg_score: float
    count: int
    tier: str


class ScoringThresholds(BaseModel):
    hot: int
    warm: int


class ScoringDistributionResponse(BaseModel):
    distribution: Dict[str, ScoreTierInfo]
    total_scored: int
    hot_percentage: float
    warm_percentage: float
    cold_percentage: float
    by_program: Dict[str, ProgramScoreInfo]
    thresholds: ScoringThresholds


class PipelineSummary(BaseModel):
    total_processed: int
    velocity_per_day: float


class WinRateSummary(BaseModel):
    overall_rate: float
    total_submitted: int
    total_won: int


class FunnelSummary(BaseModel):
    overall_conversion: float
    total_scraped: int
    total_won: int


class CompetitiveSummary(BaseModel):
    top_competitor: Optional[str]
    total_market_positions: int


class ContactsSummary(BaseModel):
    total: int
    highest_engagement_tier: str


class ScoringSummary(BaseModel):
    total_scored: int
    hot_count: int
    warm_count: int
    cold_count: int
    hot_percentage: float


class ExecutiveSummaryResponse(BaseModel):
    period: DatePeriod
    generated_at: str
    pipeline: PipelineSummary
    win_rates: WinRateSummary
    funnel: FunnelSummary
    competitive: CompetitiveSummary
    contacts: ContactsSummary
    scoring: ScoringSummary
    data_sources: List[str]


class ExportStubResponse(BaseModel):
    pdf_generation: str = "not_implemented"
    message: str = "PDF export is planned for a future release."


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/pipeline-velocity", response_model=PipelineVelocityResponse)
async def pipeline_velocity(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Pipeline velocity metrics: jobs scraped, mapped, scored, submitted per period."""
    svc = _get_service()
    return svc.pipeline_velocity(start_date, end_date)


@router.get("/win-rates", response_model=WinRateResponse)
async def win_rates(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Win rate analysis by program, company, and clearance level."""
    svc = _get_service()
    return svc.win_rate_analysis(start_date, end_date)


@router.get("/conversion-funnel", response_model=ConversionFunnelResponse)
async def conversion_funnel(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Stage-by-stage conversion funnel from scraped to won."""
    svc = _get_service()
    return svc.conversion_funnel(start_date, end_date)


@router.get("/competitive-landscape", response_model=CompetitiveLandscapeResponse)
async def competitive_landscape(
    program: Optional[str] = Query(None, description="Filter by program name"),
):
    """Competitor positioning: market share, hiring velocity, program presence."""
    svc = _get_service()
    return svc.competitive_landscape(program)


@router.get("/contact-engagement", response_model=ContactEngagementResponse)
async def contact_engagement(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Contact engagement metrics: tier distribution, engagement and response rates."""
    svc = _get_service()
    return svc.contact_engagement(start_date, end_date)


@router.get("/scoring-distribution", response_model=ScoringDistributionResponse)
async def scoring_distribution():
    """BD score distribution: hot/warm/cold counts and averages by program."""
    svc = _get_service()
    return svc.scoring_distribution()


@router.get("/executive-summary", response_model=ExecutiveSummaryResponse)
async def executive_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Roll-up of all KPIs into a single executive summary."""
    svc = _get_service()
    return svc.executive_summary(start_date, end_date)


@router.get("/export/pdf", response_model=ExportStubResponse)
async def export_pdf():
    """PDF export stub — returns JSON indicating not yet implemented."""
    return ExportStubResponse()
