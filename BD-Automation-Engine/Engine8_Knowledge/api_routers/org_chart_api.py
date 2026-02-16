"""
Phase 27A — Org Chart API

10 endpoints for org chart generation, team queries, export, and caching.
"""

from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["org-chart"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    root: Optional[str] = None
    program: Optional[str] = None
    mode: str = "tree"
    depth: int = 5


class InferRequest(BaseModel):
    program: Optional[str] = None


class CompareRequest(BaseModel):
    date1: str
    date2: str
    program: str


class ExportRequest(BaseModel):
    chart_id: Optional[str] = None
    root: Optional[str] = None
    program: Optional[str] = None
    mode: str = "tree"
    depth: int = 5


# ---------------------------------------------------------------------------
# Lazy getters
# ---------------------------------------------------------------------------


def _get_engine():
    try:
        from Engine8_Knowledge.visualization.org_chart_engine import (
            get_org_chart_engine,
        )

        return get_org_chart_engine()
    except Exception:
        return None


def _get_renderer(mode: str):
    try:
        from Engine8_Knowledge.visualization.renderers import (
            TreeRenderer,
            NetworkRenderer,
            MatrixRenderer,
        )

        if mode == "network":
            return NetworkRenderer()
        elif mode == "matrix":
            return MatrixRenderer()
        return TreeRenderer()
    except Exception:
        return None


def _get_exporter():
    try:
        from Engine8_Knowledge.visualization.export_engine import ExportEngine

        return ExportEngine()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/org-chart/generate")
async def generate_org_chart(req: GenerateRequest):
    """Generate org chart (mode, program, root, depth)."""
    engine = _get_engine()
    if not engine:
        raise HTTPException(503, "Org chart engine not available")
    from dataclasses import asdict

    chart = await engine.generate(
        root=req.root, program=req.program, mode=req.mode, depth=req.depth
    )
    return asdict(chart)


@router.get("/org-chart/programs")
async def list_programs_with_org_data():
    """List programs with org data available."""
    engine = _get_engine()
    if not engine:
        return {"programs": []}
    people = await engine._fetch_people()
    programs = sorted(set(p.program for p in people if p.program))
    return {"programs": programs, "total": len(programs)}


@router.post("/org-chart/infer-reports-to")
async def infer_reports_to(req: InferRequest):
    """Auto-infer REPORTS_TO relationships."""
    engine = _get_engine()
    if not engine:
        raise HTTPException(503, "Org chart engine not available")
    from dataclasses import asdict

    report = await engine.infer_reports_to(program=req.program)
    return asdict(report)


@router.get("/org-chart/team/{person}")
async def get_team(person: str):
    """Get a person's team (direct + skip-level)."""
    engine = _get_engine()
    if not engine:
        raise HTTPException(503, "Org chart engine not available")
    from dataclasses import asdict

    team = await engine.get_team(person)
    return asdict(team)


@router.get("/org-chart/chain/{person}")
async def get_chain(person: str):
    """Chain of command from person to top."""
    engine = _get_engine()
    if not engine:
        raise HTTPException(503, "Org chart engine not available")
    from dataclasses import asdict

    chain = await engine.get_chain_of_command(person)
    return {"person": person, "chain": [asdict(p) for p in chain], "hops": len(chain)}


@router.post("/org-chart/compare")
async def compare_org_charts(req: CompareRequest):
    """Compare org charts between dates."""
    engine = _get_engine()
    if not engine:
        raise HTTPException(503, "Org chart engine not available")
    from dataclasses import asdict

    diff = await engine.compare_org_charts(req.date1, req.date2, req.program)
    return asdict(diff)


@router.post("/org-chart/export/{format}")
async def export_org_chart(format: str, req: ExportRequest):
    """Export org chart (svg, png, pdf, docx, json, mermaid)."""
    engine = _get_engine()
    exporter = _get_exporter()
    if not engine or not exporter:
        raise HTTPException(503, "Org chart or export engine not available")

    # Get or generate chart
    chart = None
    if req.chart_id:
        chart = engine.get_cached(req.chart_id)
    if not chart:
        chart = await engine.generate(
            root=req.root, program=req.program, mode=req.mode, depth=req.depth
        )

    if format == "json":
        return await exporter.to_json(chart)
    elif format == "mermaid":
        mermaid = await exporter.to_mermaid(chart)
        return {"mermaid": mermaid}

    # Need renderer for HTML-based exports
    renderer = _get_renderer(chart.mode)
    if not renderer:
        raise HTTPException(503, "Renderer not available")
    html = await renderer.render(chart)

    if format == "svg":
        data = await exporter.to_svg(html)
        return Response(content=data, media_type="image/svg+xml")
    elif format == "png":
        data = await exporter.to_png(html)
        if not data:
            raise HTTPException(503, "PNG export requires Playwright")
        return Response(content=data, media_type="image/png")
    elif format == "pdf":
        data = await exporter.to_pdf(html)
        if not data:
            raise HTTPException(503, "PDF export requires Playwright")
        return Response(content=data, media_type="application/pdf")
    elif format == "docx":
        data = await exporter.to_docx(chart)
        if not data:
            raise HTTPException(503, "DOCX export requires python-docx")
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    else:
        raise HTTPException(400, f"Unsupported format: {format}")


@router.get("/org-chart/cache")
async def list_cached():
    """List cached org charts."""
    engine = _get_engine()
    if not engine:
        return {"charts": [], "total": 0}
    charts = engine.list_cached()
    return {"charts": charts, "total": len(charts)}


@router.delete("/org-chart/cache/{chart_id}")
async def clear_cached(chart_id: str):
    """Clear a cached chart."""
    engine = _get_engine()
    if not engine:
        raise HTTPException(503, "Org chart engine not available")
    ok = engine.clear_cache(chart_id)
    if not ok:
        raise HTTPException(404, f"Chart not found: {chart_id}")
    return {"deleted": True, "chart_id": chart_id}


@router.get("/org-chart/stats")
async def org_chart_stats():
    """Org chart generation stats."""
    engine = _get_engine()
    if not engine:
        return {"cached_charts": 0}
    cached = engine.list_cached()
    return {
        "cached_charts": len(cached),
        "renderer_modes": ["tree", "network", "matrix"],
        "export_formats": ["svg", "png", "pdf", "docx", "json", "mermaid"],
    }
