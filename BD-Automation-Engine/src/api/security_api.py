"""Phase 52A — Zero-Trust Security API.

14 endpoints for ABAC policy evaluation, audit trail, encryption,
and compliance reporting.
"""

from __future__ import annotations

from fastapi import FastAPI, APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional

router = APIRouter()


# =========================================
# REQUEST / RESPONSE MODELS
# =========================================


class EvaluateRequest(BaseModel):
    user_id: str
    role: str = "analyst"
    action: str = "read"
    resource_type: str = "contact"
    resource_id: str = ""
    program: str = ""
    programs_assigned: List[str] = []
    classification: str = "unclassified"
    clearance_level: str = "unclassified"
    nda_signed: bool = False
    geo_country: str = "US"
    record_count: int = 1
    has_competitor_data: bool = False
    owner_id: str = ""
    owner_manager_id: str = ""


class PolicyUpdateRequest(BaseModel):
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    description: Optional[str] = None


class AuditQueryRequest(BaseModel):
    actor_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    program: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = 100
    offset: int = 0


class EncryptFieldRequest(BaseModel):
    resource_type: str
    resource_id: str
    field_name: str
    plaintext: str
    searchable: bool = False


class EncryptResourceRequest(BaseModel):
    resource_type: str
    resource_id: str
    fields: Dict[str, str]
    searchable_fields: List[str] = []


class DecryptRequest(BaseModel):
    field_id: str


class SearchEncryptedRequest(BaseModel):
    query: str


# =========================================
# ABAC POLICY ENDPOINTS
# =========================================


@router.post("/api/security/evaluate")
def evaluate_access(req: EvaluateRequest):
    """Evaluate an ABAC policy decision."""
    from src.security.abac_engine import (
        get_abac_engine,
        Subject,
        Resource,
        Environment,
        ClearanceLevel,
    )
    from src.security.audit_trail import (
        get_audit_trail,
        AuditActor,
        AuditAction,
        AuditResource,
    )

    engine = get_abac_engine()

    # Map clearance strings to enum
    cl_map = {c.value: c for c in ClearanceLevel}
    subject = Subject(
        user_id=req.user_id,
        role=req.role,
        clearance_level=cl_map.get(req.clearance_level, ClearanceLevel.UNCLASSIFIED),
        nda_signed=req.nda_signed,
        programs_assigned=req.programs_assigned,
    )
    resource = Resource(
        resource_type=req.resource_type,
        resource_id=req.resource_id,
        program=req.program,
        classification=cl_map.get(req.classification, ClearanceLevel.UNCLASSIFIED),
        owner_id=req.owner_id,
        owner_manager_id=req.owner_manager_id,
        has_competitor_data=req.has_competitor_data,
        record_count=req.record_count,
    )
    environment = Environment(geo_country=req.geo_country)

    decision = engine.evaluate(subject, req.action, resource, environment)

    # Log to audit trail
    trail = get_audit_trail()
    trail.log_event(
        actor=AuditActor(user_id=req.user_id, role=req.role),
        action=AuditAction.POLICY_EVAL,
        resource=AuditResource(
            resource_type=req.resource_type,
            resource_id=req.resource_id,
            program=req.program,
        ),
        details={"requested_action": req.action},
        policy_decision=decision.decision.value,
        policy_id=decision.policy_id,
    )

    return {
        **decision.to_dict(),
        "explanation": engine.explain_decision(decision),
    }


@router.get("/api/security/policies")
def list_policies(enabled_only: bool = Query(False)):
    """List all ABAC policies."""
    from src.security.abac_engine import get_abac_engine

    engine = get_abac_engine()
    policies = engine.list_policies(enabled_only=enabled_only)
    return {
        "policies": [p.to_dict() for p in policies],
        "total": len(policies),
    }


@router.get("/api/security/policies/{policy_id}")
def get_policy(policy_id: str):
    """Get a specific policy."""
    from src.security.abac_engine import get_abac_engine

    engine = get_abac_engine()
    policy = engine.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy.to_dict()


@router.patch("/api/security/policies/{policy_id}")
def update_policy(policy_id: str, req: PolicyUpdateRequest):
    """Update a policy."""
    from src.security.abac_engine import get_abac_engine

    engine = get_abac_engine()
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    policy = engine.update_policy(policy_id, **updates)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy.to_dict()


# =========================================
# AUDIT TRAIL ENDPOINTS
# =========================================


@router.get("/api/security/audit")
def query_audit_trail(
    actor_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
):
    """Query the immutable audit trail."""
    from src.security.audit_trail import get_audit_trail, AuditFilters, AuditAction

    trail = get_audit_trail()
    filters = AuditFilters(
        actor_id=actor_id,
        action=AuditAction(action) if action else None,
        resource_type=resource_type,
    )
    events = trail.query_trail(filters=filters, limit=limit, offset=offset)
    return {
        "events": [e.to_dict() for e in events],
        "total": len(events),
    }


@router.post("/api/security/audit/verify")
def verify_audit_chain():
    """Verify hash chain integrity of the audit trail."""
    from src.security.audit_trail import get_audit_trail

    trail = get_audit_trail()
    result = trail.verify_chain()
    return result.to_dict()


@router.get("/api/security/audit/stats")
def audit_stats():
    """Get audit trail statistics."""
    from src.security.audit_trail import get_audit_trail

    trail = get_audit_trail()
    return trail.get_stats()


# =========================================
# ENCRYPTION ENDPOINTS
# =========================================


@router.get("/api/security/encryption/status")
def encryption_status():
    """Get encryption system status."""
    from src.security.encryption import get_encryption_manager

    mgr = get_encryption_manager()
    return mgr.get_status().to_dict()


@router.post("/api/security/encryption/rotate")
def rotate_encryption_keys():
    """Rotate encryption keys and re-encrypt all fields."""
    from src.security.encryption import get_encryption_manager

    mgr = get_encryption_manager()
    result = mgr.rotate_keys()
    return result.to_dict()


@router.get("/api/security/encryption/keys")
def list_encryption_keys(key_type: str = Query("all")):
    """List encryption keys (metadata only, no key material)."""
    from src.security.encryption import get_encryption_manager

    mgr = get_encryption_manager()
    keys = mgr.list_keys(key_type=key_type)
    return {"keys": keys, "total": len(keys)}


@router.get("/api/security/encryption/registry")
def get_sensitive_field_registry():
    """Get the registry of fields that require encryption."""
    from src.security.encryption import get_encryption_manager

    mgr = get_encryption_manager()
    return mgr.get_sensitive_field_registry()


# =========================================
# COMPLIANCE ENDPOINTS
# =========================================


@router.get("/api/security/compliance/soc2")
def soc2_readiness():
    """SOC 2 Type II readiness assessment."""
    from src.security.audit_trail import get_audit_trail

    trail = get_audit_trail()
    return trail.soc2_readiness()


@router.get("/api/security/compliance/fedramp")
def fedramp_readiness():
    """FedRAMP Moderate readiness assessment."""
    from src.security.audit_trail import get_audit_trail

    trail = get_audit_trail()
    return trail.fedramp_readiness()


@router.get("/api/security/compliance/report")
def compliance_report(
    report_type: str = Query("soc2"),
    period_days: int = Query(30),
):
    """Generate a compliance report."""
    from src.security.audit_trail import get_audit_trail

    trail = get_audit_trail()
    report = trail.generate_compliance_report(
        report_type=report_type,
        period_days=period_days,
    )
    return report.to_dict()


# =========================================
# HEALTH
# =========================================


@router.get("/api/security/health")
def security_health():
    """Security subsystem health check."""
    from src.security.abac_engine import get_abac_engine
    from src.security.audit_trail import get_audit_trail
    from src.security.encryption import get_encryption_manager

    abac = get_abac_engine()
    trail = get_audit_trail()
    enc = get_encryption_manager()

    return {
        "status": "healthy",
        "abac": abac.get_stats(),
        "audit": trail.get_stats(),
        "encryption": enc.get_stats(),
    }


# =========================================
# ROUTER REGISTRATION
# =========================================


def include_security_router(app: FastAPI) -> None:
    app.include_router(router)
