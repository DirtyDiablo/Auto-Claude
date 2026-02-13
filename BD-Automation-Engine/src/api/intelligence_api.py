"""Phase 44A — Intelligence API (13 endpoints).

REST endpoints for meta-learning, strategic pattern recognition,
and insight compilation.
"""

import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from src.intelligence.meta_learner import (
    MetaInsight, OutreachInsight, ProgramInsight, ContactInsight,
    get_meta_learner,
)
from src.intelligence.pattern_engine import (
    StrategicPattern, get_pattern_engine,
)
from src.intelligence.insight_compiler import (
    WeeklyBrief, MonthlyAssessment, FlashReport, get_insight_compiler,
)

logger = logging.getLogger(__name__)


# =========================================
# REQUEST MODELS
# =========================================

class FlashReportRequest(BaseModel):
    pattern_id: str


class CampaignReviewRequest(BaseModel):
    campaign_id: str = ""


# =========================================
# ROUTE SETUP
# =========================================

def include_intelligence_router(app: FastAPI) -> None:
    """Register all intelligence endpoints on the FastAPI app."""

    learner = get_meta_learner()
    patterns = get_pattern_engine()
    compiler = get_insight_compiler()

    # --------------------------------------------------
    # 1. POST /api/intelligence/learn — Run meta-learning cycle
    # --------------------------------------------------
    @app.post("/api/intelligence/learn")
    async def intelligence_learn():
        """Run all meta-learning algorithms and generate insights."""
        insights = learner.learn()
        return {
            "insights_generated": len(insights),
            "insights": [_serialize_insight(i) for i in insights],
        }

    # --------------------------------------------------
    # 2. GET /api/intelligence/insights — All current insights
    # --------------------------------------------------
    @app.get("/api/intelligence/insights")
    async def intelligence_insights(
        domain: str = "",
        severity: str = "",
        limit: int = Query(100, ge=1, le=500),
    ):
        """Get all current insights with optional filtering."""
        results = learner.get_insights(domain=domain, severity=severity)
        return {
            "insights": [_serialize_insight(i) for i in results[:limit]],
            "total": len(results),
        }

    # --------------------------------------------------
    # 3. GET /api/intelligence/insights/{insight_type} — Insights by type
    # --------------------------------------------------
    @app.get("/api/intelligence/insights/{insight_type}")
    async def intelligence_insights_by_type(insight_type: str):
        """Get insights filtered by domain type."""
        valid_types = ["outreach", "program", "contact", "data_quality", "competitive"]
        if insight_type not in valid_types:
            raise HTTPException(400, f"Invalid type. Valid: {valid_types}")
        results = learner.get_insights(domain=insight_type)
        return {
            "type": insight_type,
            "insights": [_serialize_insight(i) for i in results],
            "total": len(results),
        }

    # --------------------------------------------------
    # 4. POST /api/intelligence/patterns/scan — Run pattern recognition
    # --------------------------------------------------
    @app.post("/api/intelligence/patterns/scan")
    async def intelligence_scan():
        """Scan all data for strategic patterns."""
        detected = patterns.scan_patterns()
        # Auto-score all detected patterns
        for p in detected:
            patterns.score_opportunity(p)
        alerts = patterns.generate_alerts(detected)
        return {
            "patterns_detected": len(detected),
            "patterns": [_serialize_pattern(p) for p in detected],
            "alerts_generated": len(alerts),
        }

    # --------------------------------------------------
    # 5. GET /api/intelligence/patterns/active — Active patterns
    # --------------------------------------------------
    @app.get("/api/intelligence/patterns/active")
    async def intelligence_active_patterns(
        pattern_type: str = "",
    ):
        """Get currently active strategic patterns."""
        results = patterns.get_active_patterns(pattern_type=pattern_type)
        return {
            "patterns": [_serialize_pattern(p) for p in results],
            "total": len(results),
        }

    # --------------------------------------------------
    # 6. GET /api/intelligence/opportunities — Scored BD opportunities
    # --------------------------------------------------
    @app.get("/api/intelligence/opportunities")
    async def intelligence_opportunities(
        min_score: int = Query(0, ge=0, le=100),
    ):
        """Get scored BD opportunities."""
        opps = patterns.get_opportunities(min_score=min_score)
        return {
            "opportunities": opps,
            "total": len(opps),
        }

    # --------------------------------------------------
    # 7. POST /api/intelligence/transfer/{source}/{target}
    # --------------------------------------------------
    @app.post("/api/intelligence/transfer/{source}/{target}")
    async def intelligence_transfer(source: str, target: str):
        """Transfer learning from one program to another."""
        report = learner.transfer_learning(source, target)
        return {
            "source_program": report.source_program,
            "target_program": report.target_program,
            "similarity_score": report.similarity_score,
            "transferable_insights": len(report.transferable_insights),
            "recommended_approaches": report.recommended_approaches,
            "caveats": report.caveats,
            "created_at": report.created_at,
        }

    # --------------------------------------------------
    # 8. POST /api/intelligence/brief/weekly — Generate weekly brief
    # --------------------------------------------------
    @app.post("/api/intelligence/brief/weekly")
    async def intelligence_weekly_brief():
        """Generate a weekly executive intelligence brief."""
        brief = compiler.compile_weekly_brief()
        return _serialize_weekly_brief(brief)

    # --------------------------------------------------
    # 9. POST /api/intelligence/brief/monthly — Generate monthly assessment
    # --------------------------------------------------
    @app.post("/api/intelligence/brief/monthly")
    async def intelligence_monthly_assessment():
        """Generate a monthly strategic assessment."""
        assessment = compiler.compile_monthly_assessment()
        return _serialize_monthly_assessment(assessment)

    # --------------------------------------------------
    # 10. POST /api/intelligence/brief/flash — Generate flash report
    # --------------------------------------------------
    @app.post("/api/intelligence/brief/flash")
    async def intelligence_flash_report(req: FlashReportRequest):
        """Generate a flash report for a critical pattern."""
        active = patterns.get_active_patterns()
        target = None
        for p in active:
            if p.id == req.pattern_id:
                target = p
                break
        if target is None:
            raise HTTPException(404, "Pattern not found")
        report = compiler.compile_flash_report(target)
        return _serialize_flash_report(report)

    # --------------------------------------------------
    # 11. GET /api/intelligence/effectiveness/outreach
    # --------------------------------------------------
    @app.get("/api/intelligence/effectiveness/outreach")
    async def intelligence_outreach_effectiveness():
        """Get outreach effectiveness data."""
        return learner.get_outreach_effectiveness()

    # --------------------------------------------------
    # 12. GET /api/intelligence/effectiveness/campaigns
    # --------------------------------------------------
    @app.get("/api/intelligence/effectiveness/campaigns")
    async def intelligence_campaign_effectiveness():
        """Get campaign effectiveness data."""
        return learner.get_campaign_effectiveness()

    # --------------------------------------------------
    # 13. GET /api/intelligence/trends/competitive
    # --------------------------------------------------
    @app.get("/api/intelligence/trends/competitive")
    async def intelligence_competitive_trends():
        """Get competitive intelligence trends."""
        return learner.get_competitive_trends()

    logger.info("Intelligence API: 13 endpoints registered under /api/intelligence/*")


# =========================================
# SERIALIZATION HELPERS
# =========================================

def _serialize_insight(i: MetaInsight) -> Dict[str, Any]:
    base = {
        "id": i.id, "domain": i.domain, "title": i.title,
        "description": i.description, "severity": i.severity,
        "confidence": i.confidence, "recommendations": i.recommendations,
        "created_at": i.created_at, "tags": i.tags,
    }
    if isinstance(i, OutreachInsight):
        base["channel"] = i.channel
        base["best_time"] = i.best_time
        base["response_rate"] = i.response_rate
        base["tier_effectiveness"] = i.tier_effectiveness
    elif isinstance(i, ProgramInsight):
        base["program_id"] = i.program_id
        base["program_name"] = i.program_name
        base["trend"] = i.trend
        base["cycle_phase"] = i.cycle_phase
    elif isinstance(i, ContactInsight):
        base["contact_pattern"] = i.contact_pattern
        base["affected_contacts"] = i.affected_contacts
    return base


def _serialize_pattern(p: StrategicPattern) -> Dict[str, Any]:
    return {
        "id": p.id, "pattern_type": p.pattern_type, "title": p.title,
        "description": p.description, "program": p.program,
        "confidence": p.confidence, "detected_at": p.detected_at,
        "expires_at": p.expires_at, "tags": p.tags,
    }


def _serialize_weekly_brief(b: WeeklyBrief) -> Dict[str, Any]:
    return {
        "id": b.id, "title": b.title,
        "period_start": b.period_start, "period_end": b.period_end,
        "executive_summary": b.executive_summary,
        "sections": [
            {"heading": s.heading, "content": s.content, "priority": s.priority}
            for s in b.sections
        ],
        "key_metrics": b.key_metrics,
        "top_opportunities": b.top_opportunities,
        "action_items": b.action_items,
        "created_at": b.created_at,
    }


def _serialize_monthly_assessment(a: MonthlyAssessment) -> Dict[str, Any]:
    return {
        "id": a.id, "title": a.title, "period": a.period,
        "executive_summary": a.executive_summary,
        "sections": [
            {"heading": s.heading, "content": s.content, "priority": s.priority}
            for s in a.sections
        ],
        "trend_analysis": a.trend_analysis,
        "strategic_recommendations": a.strategic_recommendations,
        "risk_factors": a.risk_factors,
        "created_at": a.created_at,
    }


def _serialize_flash_report(r: FlashReport) -> Dict[str, Any]:
    return {
        "id": r.id, "title": r.title, "pattern_id": r.pattern_id,
        "urgency": r.urgency, "summary": r.summary,
        "impact_assessment": r.impact_assessment,
        "recommended_response": r.recommended_response,
        "time_sensitivity": r.time_sensitivity,
        "created_at": r.created_at,
    }
