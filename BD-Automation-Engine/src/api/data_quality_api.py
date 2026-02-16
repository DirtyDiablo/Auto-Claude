"""Phase 38A — Data Quality API

17 endpoints for quality monitoring, self-healing, lineage tracking, and rules management.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

from src.data_quality.engine import (
    get_quality_engine,
)
from src.data_quality.self_healer import (
    get_self_healer,
)
from src.data_quality.lineage import (
    get_lineage_tracker,
)
from src.data_quality.rules_dsl import (
    get_rules_dsl,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-quality", tags=["data-quality"])


# =========================================
# REQUEST MODELS
# =========================================


class RunAuditRequest(BaseModel):
    domains: Optional[List[str]] = None  # If None, audit all domains


class HealRequest(BaseModel):
    domain: Optional[str] = None
    severity: Optional[str] = None
    auto_fixable_only: bool = True


class ReloadRulesRequest(BaseModel):
    rules: Dict[str, List[Dict[str, Any]]]


class BatchValidateRequest(BaseModel):
    domain: str
    records: List[Dict[str, Any]]


# =========================================
# HEALTH & OVERVIEW (3 endpoints)
# =========================================


@router.get("/health")
async def get_health():
    """Overall health score + trends."""
    engine = get_quality_engine()
    return engine.get_health_summary()


@router.get("/report")
async def get_report():
    """Full audit report."""
    engine = get_quality_engine()
    history = engine.get_history()
    if not history:
        return {
            "status": "no_audit_run",
            "message": "Run an audit first via POST /data-quality/audit/run",
        }
    latest = history[-1]
    return {
        "id": latest.id,
        "overall_score": latest.overall_score,
        "domain_scores": latest.domain_scores,
        "dimension_scores": latest.dimension_scores,
        "critical_issues": len(latest.critical_issues),
        "total_issues": len(latest.all_issues),
        "auto_fixable_count": latest.auto_fixable_count,
        "trend": latest.trend.value,
        "recommendations": latest.recommendations,
        "records_audited": latest.records_audited,
        "created_at": latest.created_at,
        "duration_seconds": latest.duration_seconds,
    }


@router.get("/report/{domain}")
async def get_domain_report(domain: str):
    """Domain-specific report."""
    engine = get_quality_engine()
    history = engine.get_history()
    if not history:
        raise HTTPException(status_code=404, detail="No audit has been run")
    latest = history[-1]
    if domain not in latest.domain_scores:
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")
    domain_issues = [i for i in latest.all_issues if i.domain == domain]
    return {
        "domain": domain,
        "score": latest.domain_scores.get(domain, 100.0),
        "total_issues": len(domain_issues),
        "critical": len([i for i in domain_issues if i.severity == "critical"]),
        "auto_fixable": len([i for i in domain_issues if i.auto_fixable]),
        "issues": [
            {
                "id": i.id,
                "dimension": i.dimension,
                "field": i.field_name,
                "severity": i.severity,
                "description": i.description,
                "auto_fixable": i.auto_fixable,
                "record_id": i.record_id,
            }
            for i in domain_issues[:50]  # Limit to 50 per response
        ],
    }


# =========================================
# RECORD SCORING (1 endpoint)
# =========================================


@router.get("/score/{record_type}/{record_id}")
async def score_record(record_type: str, record_id: str):
    """Single record quality score."""
    engine = get_quality_engine()
    data = engine._data.get(record_type, [])
    record = None
    for r in data:
        if r.get("id") == record_id:
            record = r
            break
    if not record:
        raise HTTPException(
            status_code=404, detail=f"Record {record_id} not found in {record_type}"
        )
    score = engine.score_single_record(record_type, record)
    return {
        "record_id": score.record_id,
        "record_type": score.record_type,
        "overall_score": score.overall_score,
        "dimension_scores": score.dimension_scores,
        "issues": [
            {
                "dimension": i.dimension,
                "field": i.field_name,
                "severity": i.severity,
                "description": i.description,
            }
            for i in score.issues
        ],
        "checked_at": score.checked_at,
    }


# =========================================
# AUDIT TRIGGER (1 endpoint)
# =========================================


@router.post("/audit/run")
async def run_audit(req: Optional[RunAuditRequest] = None):
    """Trigger immediate full audit."""
    engine = get_quality_engine()
    report = engine.run_full_audit()
    return {
        "id": report.id,
        "overall_score": report.overall_score,
        "domain_scores": report.domain_scores,
        "total_issues": len(report.all_issues),
        "critical_issues": len(report.critical_issues),
        "auto_fixable": report.auto_fixable_count,
        "trend": report.trend.value,
        "records_audited": report.records_audited,
        "duration_seconds": report.duration_seconds,
    }


# =========================================
# ISSUES (2 endpoints)
# =========================================


@router.get("/issues")
async def list_issues(
    domain: Optional[str] = None,
    severity: Optional[str] = None,
    auto_fixable: bool = False,
    limit: int = 100,
):
    """List all open issues."""
    engine = get_quality_engine()
    issues = engine.get_issues(
        domain=domain, severity=severity, auto_fixable_only=auto_fixable
    )
    return {
        "issues": [
            {
                "id": i.id,
                "domain": i.domain,
                "dimension": i.dimension,
                "record_id": i.record_id,
                "field": i.field_name,
                "current_value": str(i.current_value)[:100],
                "severity": i.severity,
                "description": i.description,
                "auto_fixable": i.auto_fixable,
                "impact_score": i.impact_score,
            }
            for i in issues[:limit]
        ],
        "total": len(issues),
    }


@router.get("/issues/{issue_id}")
async def get_issue(issue_id: str):
    """Issue detail with lineage."""
    engine = get_quality_engine()
    all_issues = engine.get_issues()
    issue = None
    for i in all_issues:
        if i.id == issue_id:
            issue = i
            break
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Try lineage trace
    tracker = get_lineage_tracker()
    lineage = tracker.trace_lineage(issue.record_id)

    return {
        "id": issue.id,
        "domain": issue.domain,
        "dimension": issue.dimension,
        "record_id": issue.record_id,
        "field": issue.field_name,
        "current_value": str(issue.current_value),
        "expected_pattern": issue.expected_pattern,
        "severity": issue.severity,
        "description": issue.description,
        "auto_fixable": issue.auto_fixable,
        "suggested_fix": str(issue.suggested_fix) if issue.suggested_fix else None,
        "lineage": {
            "depth": lineage.depth if lineage else 0,
            "transformations": lineage.total_transformations if lineage else 0,
            "sources": len(lineage.sources) if lineage else 0,
        }
        if lineage
        else None,
    }


# =========================================
# SELF-HEALING (2 endpoints)
# =========================================


@router.post("/heal")
async def trigger_healing(req: Optional[HealRequest] = None):
    """Trigger self-healing for pending issues."""
    engine = get_quality_engine()
    healer = get_self_healer()

    domain = req.domain if req else None
    severity = req.severity if req else None

    issues = engine.get_issues(
        domain=domain,
        severity=severity,
        auto_fixable_only=True,
    )

    if not issues:
        return {"status": "no_issues", "fixed": 0, "skipped": 0}

    results = healer.heal(issues)

    fixed = [r for r in results if r.status == "fixed"]
    skipped = [r for r in results if r.status == "skipped"]
    failed = [r for r in results if r.status == "failed"]
    needs_human = [r for r in results if r.status == "needs_human"]

    return {
        "total_processed": len(results),
        "fixed": len(fixed),
        "skipped": len(skipped),
        "failed": len(failed),
        "needs_human": len(needs_human),
        "cascading_fixes": sum(len(r.cascading_fixes) for r in fixed),
        "fixes": [
            {
                "record_id": r.issue.record_id,
                "field": r.issue.field_name,
                "old_value": str(r.old_value)[:100],
                "new_value": str(r.new_value)[:100],
                "confidence": r.confidence,
                "healer": r.healer_used,
            }
            for r in fixed[:20]
        ],
    }


@router.get("/heal/log")
async def get_heal_log(limit: int = 100):
    """Audit log of all auto-fixes."""
    healer = get_self_healer()
    log = healer.get_audit_log()
    return {
        "entries": [
            {
                "status": r.status,
                "record_id": r.issue.record_id,
                "field": r.issue.field_name,
                "healer": r.healer_used,
                "confidence": r.confidence,
                "old_value": str(r.old_value)[:100] if r.old_value else None,
                "new_value": str(r.new_value)[:100] if r.new_value else None,
                "reason": r.reason,
                "timestamp": r.timestamp,
            }
            for r in log[-limit:]
        ],
        "total": len(log),
    }


# =========================================
# LINEAGE (2 endpoints)
# =========================================


@router.get("/lineage/{record_id}")
async def get_lineage(record_id: str, depth: int = 10):
    """Full lineage trace for a record."""
    tracker = get_lineage_tracker()
    graph = tracker.trace_lineage(record_id, depth=depth)
    if not graph:
        raise HTTPException(status_code=404, detail="No lineage found for this record")
    return {
        "record_id": record_id,
        "root": {
            "id": graph.root.id,
            "type": graph.root.node_type,
            "confidence": graph.root.confidence,
        },
        "depth": graph.depth,
        "total_transformations": graph.total_transformations,
        "confidence_chain": graph.confidence_chain,
        "sources": [
            {"id": s.id, "type": s.source_type, "url": s.url} for s in graph.sources
        ],
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
    }


@router.get("/lineage/{record_id}/impact")
async def get_impact(record_id: str):
    """Forward impact analysis."""
    tracker = get_lineage_tracker()
    impact = tracker.get_impact_analysis(record_id)
    return {
        "record_id": impact.record_id,
        "total_downstream": impact.total_downstream,
        "risk_level": impact.risk_level,
        "downstream_records": [
            {"id": n.id, "type": n.node_type, "record_id": n.record_id}
            for n in impact.downstream_records[:20]
        ],
    }


# =========================================
# FRESHNESS (1 endpoint)
# =========================================


@router.get("/freshness")
async def get_freshness():
    """Data freshness report."""
    tracker = get_lineage_tracker()
    report = tracker.get_freshness_report()
    return {
        "overall_freshness_score": report.overall_freshness_score,
        "generated_at": report.generated_at,
        "domains": [
            {
                "domain": e.domain,
                "total_records": e.total_records,
                "avg_age_days": e.avg_age_days,
                "updated_last_30": e.updated_last_30,
                "updated_last_60": e.updated_last_60,
                "updated_last_90": e.updated_last_90,
                "stale_count": e.stale_count,
            }
            for e in report.entries
        ],
    }


# =========================================
# RULES (2 endpoints)
# =========================================


@router.get("/rules")
async def list_rules():
    """List all quality rules."""
    engine = get_quality_engine()
    rules = engine.get_rules()
    return {
        "rules": [
            {
                "name": r.name,
                "dimension": r.dimension,
                "domain": r.domain,
                "severity": r.severity,
                "description": r.description,
                "impact_score": r.impact_score,
                "enabled": r.enabled,
            }
            for r in rules
        ],
        "total": len(rules),
    }


@router.post("/rules/reload")
async def reload_rules(req: ReloadRulesRequest):
    """Hot-reload rules from dictionary."""
    dsl = get_rules_dsl()
    result = dsl.hot_reload(req.rules)
    if not result.success:
        raise HTTPException(status_code=400, detail={"errors": result.errors})
    return {
        "success": result.success,
        "added": result.added,
        "removed": result.removed,
        "modified": result.modified,
        "unchanged": result.unchanged,
        "timestamp": result.timestamp,
    }


# =========================================
# TRENDS (1 endpoint)
# =========================================


@router.get("/trends")
async def get_trends(periods: int = 10):
    """Quality score trends over time."""
    engine = get_quality_engine()
    return {"trends": engine.get_trends(periods)}


# =========================================
# BATCH VALIDATION (1 endpoint)
# =========================================


@router.post("/validate/batch")
async def validate_batch(req: BatchValidateRequest):
    """Validate a batch of records before import."""
    healer = get_self_healer()
    results = healer.validate_batch(req.records, req.domain)
    total_fixes = sum(r["fix_count"] for r in results)
    return {
        "domain": req.domain,
        "records_validated": len(results),
        "total_fixes_applied": total_fixes,
        "results": results[:50],  # Limit response size
    }


# =========================================
# ROUTER INCLUSION
# =========================================


def include_data_quality_router(app: FastAPI) -> None:
    """Include data quality router in the app."""
    app.include_router(router)
