"""
Feature 20 — Multi-Portfolio Management Router.

Provides REST endpoints for listing, inspecting, and scoring jobs
against multiple defense portfolio configurations.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from Engine8_Knowledge.portfolios.registry import get_portfolio_registry
from Engine8_Knowledge.portfolios.portfolio_scorer import PortfolioScorer

try:
    import structlog

    logger = structlog.get_logger("PortfolioRouter")
except ImportError:
    logger = logging.getLogger("PortfolioRouter")

router = APIRouter(prefix="/portfolios", tags=["Portfolio Management"])


# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------


class PortfolioSummary(BaseModel):
    id: str
    name: str
    description: str
    estimated_value: str
    keyword_count: int
    program_count: int
    competitor_count: int


class PortfolioDetail(BaseModel):
    id: str
    name: str
    description: str
    estimated_value: str
    keywords: List[str]
    secondary_keywords: List[str]
    programs: List[str]
    agencies: List[str]
    competitors: List[str]
    location_keywords: List[str]
    keyword_boost: int
    location_boost: int
    clearance_boost: Dict[str, int]
    scoring_weights: Dict[str, float]


class ScoreRequest(BaseModel):
    job: Dict = Field(..., description="Job/opportunity data to score")


class ScoreResponse(BaseModel):
    score: int
    tier: str
    breakdown: Dict
    portfolio_id: str


class CrossScoreRequest(BaseModel):
    job: Dict = Field(..., description="Job/opportunity data to score across portfolios")


class CrossScoreResponse(BaseModel):
    job: Dict
    rankings: List[Dict]
    best_match: Optional[Dict]


class PortfolioComparison(BaseModel):
    portfolios: List[Dict]
    total_estimated_value: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=List[PortfolioSummary])
async def list_portfolios():
    """List all available portfolios."""
    registry = get_portfolio_registry()
    results = []
    for p in registry.list_all():
        results.append(
            PortfolioSummary(
                id=p.id,
                name=p.name,
                description=p.description,
                estimated_value=p.estimated_value,
                keyword_count=len(p.keywords),
                program_count=len(p.programs),
                competitor_count=len(p.competitors),
            )
        )
    return results


@router.get("/comparison", response_model=PortfolioComparison)
async def compare_portfolios():
    """Compare all portfolios side by side (value, keywords, competitors)."""
    registry = get_portfolio_registry()
    items = []
    for p in registry.list_all():
        items.append(
            {
                "id": p.id,
                "name": p.name,
                "estimated_value": p.estimated_value,
                "keywords": p.keywords,
                "competitors": p.competitors,
                "agencies": p.agencies,
                "program_count": len(p.programs),
            }
        )
    return PortfolioComparison(
        portfolios=items,
        total_estimated_value=_sum_values(registry.list_all()),
    )


@router.get("/{portfolio_id}", response_model=PortfolioDetail)
async def get_portfolio(portfolio_id: str):
    """Get detailed configuration for a portfolio."""
    registry = get_portfolio_registry()
    p = registry.get(portfolio_id)
    if p is None:
        raise HTTPException(status_code=404, detail=f"Portfolio '{portfolio_id}' not found")
    return PortfolioDetail(
        id=p.id,
        name=p.name,
        description=p.description,
        estimated_value=p.estimated_value,
        keywords=p.keywords,
        secondary_keywords=p.secondary_keywords,
        programs=p.programs,
        agencies=p.agencies,
        competitors=p.competitors,
        location_keywords=p.location_keywords,
        keyword_boost=p.keyword_boost,
        location_boost=p.location_boost,
        clearance_boost=p.clearance_boost,
        scoring_weights=p.scoring_weights,
    )


@router.post("/{portfolio_id}/score", response_model=ScoreResponse)
async def score_job(portfolio_id: str, req: ScoreRequest):
    """Score a job against a specific portfolio."""
    registry = get_portfolio_registry()
    scorer = registry.get_scorer(portfolio_id)
    if scorer is None:
        raise HTTPException(status_code=404, detail=f"Portfolio '{portfolio_id}' not found")
    result = scorer.score(req.job)
    return ScoreResponse(**result)


@router.post("/cross-score", response_model=CrossScoreResponse)
async def cross_score(req: CrossScoreRequest):
    """Score a job against all portfolios and rank the results."""
    registry = get_portfolio_registry()
    all_portfolios = registry.list_all()
    scorer = PortfolioScorer(all_portfolios[0])
    result = scorer.cross_portfolio_analysis(req.job, all_portfolios)
    return CrossScoreResponse(**result)


@router.get("/{portfolio_id}/programs", response_model=List[str])
async def list_programs(portfolio_id: str):
    """List programs associated with a portfolio."""
    registry = get_portfolio_registry()
    p = registry.get(portfolio_id)
    if p is None:
        raise HTTPException(status_code=404, detail=f"Portfolio '{portfolio_id}' not found")
    return p.programs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sum_values(portfolios) -> str:
    """Best-effort summation of estimated_value strings for display."""
    total = 0.0
    suffix = "B"
    for p in portfolios:
        val = p.estimated_value.replace("$", "").replace("+", "").strip()
        if val.endswith("B"):
            total += float(val[:-1])
        elif val.endswith("M"):
            total += float(val[:-1]) / 1000.0
    return f"${total:.1f}B+"
