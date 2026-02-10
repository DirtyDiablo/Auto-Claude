"""Phase 35A — Proposal & Capture Automation API

10 endpoints for automated proposal generation:
  - Capability statements
  - Past performance matrices
  - Compliance matrices
  - Labor categories & pricing
  - Full proposal packages
  - Templates & history
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.proposals.capability_generator import (
    CapabilityStatementGenerator,
    TemplateVariant,
    get_capability_generator,
)
from src.proposals.past_performance import (
    PastPerformanceBuilder,
    PastPerformanceEntry,
    CPARSMetrics,
    get_past_performance_builder,
)
from src.proposals.compliance_matrix import (
    ComplianceMatrixGenerator,
    get_compliance_generator,
)
from src.proposals.pricing_engine import (
    PricingEngine,
    PricingModel,
    get_pricing_engine,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proposals", tags=["proposals"])


# =========================================
# REQUEST / RESPONSE MODELS
# =========================================

class CapabilityRequest(BaseModel):
    program: str
    agency: str = ""
    variant: str = "two_page"  # one_page, two_page, full_brief


class PastPerformanceRequest(BaseModel):
    solicitation: str
    requirements: Dict[str, Any] = Field(default_factory=dict)
    top_n: int = 5


class ComplianceRequest(BaseModel):
    rfp_title: str
    document_text: str = ""
    requirements: List[Dict[str, str]] = Field(default_factory=list)


class LaborCategoryRequest(BaseModel):
    titles: List[str]
    clearance: str = "Secret"
    experience_years: int = 5


class RateCardRequest(BaseModel):
    title: str
    categories: List[Dict[str, Any]]
    pricing_model: str = "T&M"
    option_years: int = 4
    escalation_rate: float = 3.0


class PricingAnalysisRequest(BaseModel):
    program: str
    categories: List[Dict[str, Any]] = Field(default_factory=list)


class FullPackageRequest(BaseModel):
    program: str
    agency: str = ""
    solicitation: str = ""
    rfp_text: str = ""
    labor_titles: List[str] = Field(default_factory=list)
    clearance: str = "Secret"


class ExportRequest(BaseModel):
    format: str = "docx"  # docx or xlsx


# =========================================
# SINGLETONS
# =========================================

_cap_gen: Optional[CapabilityStatementGenerator] = None
_pp_builder: Optional[PastPerformanceBuilder] = None
_comp_gen: Optional[ComplianceMatrixGenerator] = None
_pricing: Optional[PricingEngine] = None


def _get_cap_gen() -> CapabilityStatementGenerator:
    global _cap_gen
    if _cap_gen is None:
        _cap_gen = get_capability_generator()
    return _cap_gen


def _get_pp_builder() -> PastPerformanceBuilder:
    global _pp_builder
    if _pp_builder is None:
        _pp_builder = get_past_performance_builder()
    return _pp_builder


def _get_comp_gen() -> ComplianceMatrixGenerator:
    global _comp_gen
    if _comp_gen is None:
        _comp_gen = get_compliance_generator()
    return _comp_gen


def _get_pricing() -> PricingEngine:
    global _pricing
    if _pricing is None:
        _pricing = get_pricing_engine()
    return _pricing


# =========================================
# ENDPOINTS
# =========================================

@router.post("/capability-statement")
async def generate_capability_statement(req: CapabilityRequest):
    """Generate a PTS capability statement for a program."""
    gen = _get_cap_gen()
    variant_map = {
        "one_page": TemplateVariant.ONE_PAGE,
        "two_page": TemplateVariant.TWO_PAGE,
        "full_brief": TemplateVariant.FULL_BRIEF,
    }
    variant = variant_map.get(req.variant, TemplateVariant.TWO_PAGE)

    statement = await gen.generate(
        program=req.program,
        agency=req.agency,
        variant=variant,
    )
    return gen.export_to_dict(statement)


@router.post("/past-performance")
async def build_past_performance(req: PastPerformanceRequest):
    """Build a past performance matrix for a solicitation."""
    builder = _get_pp_builder()
    matrix = await builder.build_matrix(
        solicitation=req.solicitation,
        requirements=req.requirements,
        top_n=req.top_n,
    )
    return builder.export_to_dict(matrix)


@router.post("/compliance-matrix")
async def generate_compliance_matrix(req: ComplianceRequest):
    """Generate a compliance matrix from RFP text or requirements."""
    gen = _get_comp_gen()

    if req.document_text:
        matrix = await gen.generate_from_text(req.rfp_title, req.document_text)
    elif req.requirements:
        matrix = await gen.generate_from_requirements(req.rfp_title, req.requirements)
    else:
        raise HTTPException(
            status_code=400,
            detail="Either document_text or requirements must be provided.",
        )

    return gen.export_to_dict(matrix)


@router.post("/pricing/labor-categories")
async def generate_labor_categories(req: LaborCategoryRequest):
    """Generate labor categories with GSA/market rates."""
    engine = _get_pricing()
    categories = [
        engine.build_labor_category(
            title=title,
            clearance=req.clearance,
            experience_years=req.experience_years,
        )
        for title in req.titles
    ]

    return {
        "categories": [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "clearance": c.clearance_required,
                "gsa_rate": c.gsa_rate,
                "market_rate": c.market_rate,
                "proposed_rate": c.proposed_rate,
                "salary_range": f"${c.salary_range_low:,.0f} - ${c.salary_range_high:,.0f}",
                "functional_area": c.functional_area,
            }
            for c in categories
        ],
        "total": len(categories),
    }


@router.post("/pricing/rate-card")
async def generate_rate_card(req: RateCardRequest):
    """Generate a complete rate card."""
    engine = _get_pricing()

    categories = [
        engine.build_labor_category(
            title=c.get("title", ""),
            clearance=c.get("clearance", "Secret"),
            experience_years=c.get("experience_years", 5),
        )
        for c in req.categories
    ]

    model_map = {
        "T&M": PricingModel.TIME_AND_MATERIALS,
        "FFP": PricingModel.FIRM_FIXED_PRICE,
        "CPFF": PricingModel.COST_PLUS_FIXED_FEE,
        "CPAF": PricingModel.COST_PLUS_AWARD_FEE,
    }
    pricing_model = model_map.get(req.pricing_model, PricingModel.TIME_AND_MATERIALS)

    card = engine.generate_rate_card(
        title=req.title,
        categories=categories,
        pricing_model=pricing_model,
        option_years=req.option_years,
        escalation_rate=req.escalation_rate,
    )
    return engine.export_rate_card_to_dict(card)


@router.post("/pricing/analysis")
async def competitive_pricing_analysis(req: PricingAnalysisRequest):
    """Run competitive pricing analysis."""
    engine = _get_pricing()

    categories = [
        engine.build_labor_category(
            title=c.get("title", ""),
            clearance=c.get("clearance", "Secret"),
        )
        for c in req.categories
    ] if req.categories else []

    analysis = await engine.analyze_competitive_pricing(
        program=req.program,
        categories=categories,
    )

    return {
        "id": analysis.id,
        "program": analysis.program,
        "avg_market_rate": analysis.avg_market_rate,
        "our_rate": analysis.our_rate,
        "competitive_position": analysis.competitive_position,
        "rate_comparison": analysis.rate_comparison,
        "recommendations": analysis.recommendations,
        "generated_at": analysis.generated_at,
    }


@router.post("/full-package")
async def generate_full_package(req: FullPackageRequest):
    """Generate a complete proposal package."""
    results = {}

    # 1. Capability statement
    cap_gen = _get_cap_gen()
    statement = await cap_gen.generate(
        program=req.program,
        agency=req.agency,
        variant=TemplateVariant.TWO_PAGE,
    )
    results["capability_statement"] = cap_gen.export_to_dict(statement)

    # 2. Past performance
    pp_builder = _get_pp_builder()
    matrix = await pp_builder.build_matrix(solicitation=req.solicitation or req.program)
    results["past_performance"] = pp_builder.export_to_dict(matrix)

    # 3. Compliance matrix (if RFP text provided)
    if req.rfp_text:
        comp_gen = _get_comp_gen()
        compliance = await comp_gen.generate_from_text(f"{req.program} RFP", req.rfp_text)
        results["compliance_matrix"] = comp_gen.export_to_dict(compliance)

    # 4. Labor categories & rate card
    if req.labor_titles:
        engine = _get_pricing()
        categories = [
            engine.build_labor_category(title=t, clearance=req.clearance)
            for t in req.labor_titles
        ]
        card = engine.generate_rate_card(
            title=f"{req.program} Rate Card",
            categories=categories,
        )
        results["rate_card"] = engine.export_rate_card_to_dict(card)

    results["program"] = req.program
    results["generated_at"] = statement.generated_at
    return results


@router.get("/templates")
async def list_templates():
    """List available proposal templates."""
    gen = _get_cap_gen()
    return {
        "templates": gen.get_templates(),
        "pricing_models": [
            {"id": "T&M", "name": "Time & Materials"},
            {"id": "FFP", "name": "Firm Fixed Price"},
            {"id": "CPFF", "name": "Cost Plus Fixed Fee"},
            {"id": "CPAF", "name": "Cost Plus Award Fee"},
        ],
        "total": 7,
    }


@router.get("/history")
async def get_history():
    """Get proposal generation history."""
    cap_gen = _get_cap_gen()
    pp_builder = _get_pp_builder()
    comp_gen = _get_comp_gen()
    pricing = _get_pricing()

    return {
        "capability_statements": [
            {"id": s.id, "program": s.program, "generated_at": s.generated_at}
            for s in cap_gen.get_history()
        ],
        "past_performance": [
            {"id": m.id, "solicitation": m.solicitation, "generated_at": m.generated_at}
            for m in pp_builder.get_history()
        ],
        "compliance_matrices": [
            {"id": m.id, "rfp_title": m.rfp_title, "generated_at": m.generated_at}
            for m in comp_gen.get_history()
        ],
        "rate_cards": [
            {"id": c.id, "title": c.title, "generated_at": c.generated_at}
            for c in pricing.get_rate_card_history()
        ],
    }


@router.post("/export/{proposal_id}")
async def export_proposal(proposal_id: str, req: ExportRequest):
    """Export a proposal to DOCX/XLSX format."""
    # Find proposal in history
    cap_gen = _get_cap_gen()
    for s in cap_gen.get_history():
        if s.id == proposal_id:
            return {
                "id": proposal_id,
                "format": req.format,
                "status": "ready",
                "data": cap_gen.export_to_dict(s),
            }

    pp_builder = _get_pp_builder()
    for m in pp_builder.get_history():
        if m.id == proposal_id:
            return {
                "id": proposal_id,
                "format": req.format,
                "status": "ready",
                "data": pp_builder.export_to_dict(m),
            }

    comp_gen = _get_comp_gen()
    for m in comp_gen.get_history():
        if m.id == proposal_id:
            return {
                "id": proposal_id,
                "format": req.format,
                "status": "ready",
                "data": comp_gen.export_to_dict(m),
            }

    raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")


# =========================================
# INTEGRATION
# =========================================

def configure_proposals(app_instance: FastAPI) -> None:
    """Configure proposal routes on an existing FastAPI app."""
    app_instance.include_router(router)


def include_proposal_router(app_instance: FastAPI) -> None:
    """Include proposal router in FastAPI app."""
    app_instance.include_router(router)
