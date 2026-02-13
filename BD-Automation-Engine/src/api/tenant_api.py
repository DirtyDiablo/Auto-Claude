"""Phase 37A — Tenant & Auth API

21 endpoints for multi-tenant management, authentication, and RBAC.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

from src.tenants.tenant_manager import (
    Tenant,
    TenantStatus,
    get_tenant_manager,
)
from src.auth.rbac import (
    Action,
    Resource,
    Role,
    get_rbac_manager,
)
from src.auth.auth_service import (
    get_auth_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenants", tags=["tenants"])
auth_router = APIRouter(prefix="/auth", tags=["auth"])


# =========================================
# REQUEST MODELS
# =========================================

class CreateTenantRequest(BaseModel):
    name: str
    owner_email: str
    plan: str = "professional"

class UpdateTenantRequest(BaseModel):
    name: Optional[str] = None
    plan: Optional[str] = None
    owner_email: Optional[str] = None

class CreateUserRequest(BaseModel):
    email: str
    tenant_id: str
    password: str = ""
    role: str = "viewer"
    display_name: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str
    tenant_id: str

class ChangePasswordRequest(BaseModel):
    user_id: str
    old_password: str
    new_password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class SSOLoginRequest(BaseModel):
    tenant_id: str
    sso_subject_id: str
    email: str
    display_name: str = ""

class SSOConfigRequest(BaseModel):
    tenant_id: str
    provider: str = "saml"
    entity_id: str = ""
    sso_url: str = ""
    certificate: str = ""
    client_id: str = ""
    client_secret: str = ""
    token_url: str = ""
    userinfo_url: str = ""
    redirect_uri: str = ""

class AssignRoleRequest(BaseModel):
    tenant_id: str
    user_id: str
    role: str

class CreateApiKeyRequest(BaseModel):
    tenant_id: str
    name: str
    role: str = "api_service"

class PermissionCheckRequest(BaseModel):
    role: str
    resource: str
    action: str


# =========================================
# TENANT ENDPOINTS (7)
# =========================================

@router.post("/")
async def create_tenant(req: CreateTenantRequest):
    """Create a new tenant."""
    mgr = get_tenant_manager()
    tenant = mgr.create_tenant(
        name=req.name,
        owner_email=req.owner_email,
        plan=req.plan,
    )
    return _tenant_to_dict(tenant)


@router.get("/")
async def list_tenants(status: Optional[str] = None):
    """List all tenants."""
    mgr = get_tenant_manager()
    filter_status = TenantStatus(status) if status else None
    tenants = mgr.list_tenants(status=filter_status)
    return {"tenants": [_tenant_to_dict(t) for t in tenants], "total": len(tenants)}


@router.get("/{tenant_id}")
async def get_tenant(tenant_id: str):
    """Get tenant by ID."""
    mgr = get_tenant_manager()
    tenant = mgr.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return _tenant_to_dict(tenant)


@router.put("/{tenant_id}")
async def update_tenant(tenant_id: str, req: UpdateTenantRequest):
    """Update tenant properties."""
    mgr = get_tenant_manager()
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    tenant = mgr.update_tenant(tenant_id, **kwargs)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return _tenant_to_dict(tenant)


@router.delete("/{tenant_id}")
async def deactivate_tenant(tenant_id: str):
    """Deactivate a tenant (soft delete)."""
    mgr = get_tenant_manager()
    success = mgr.deactivate_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"status": "deactivated", "tenant_id": tenant_id}


@router.get("/{tenant_id}/health")
async def get_tenant_health(tenant_id: str):
    """Get tenant health metrics."""
    mgr = get_tenant_manager()
    health = mgr.get_tenant_health(tenant_id)
    if not health:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {
        "tenant_id": health.tenant_id,
        "status": health.status.value,
        "user_count": health.user_count,
        "api_calls_today": health.api_calls_today,
        "storage_used_gb": health.storage_used_gb,
        "collections_count": health.collections_count,
        "uptime_pct": health.uptime_pct,
    }


@router.get("/{tenant_id}/usage")
async def get_tenant_usage(tenant_id: str):
    """Get tenant usage metrics for billing."""
    mgr = get_tenant_manager()
    metrics = mgr.get_usage_metrics(tenant_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return metrics


# =========================================
# AUTH ENDPOINTS (8)
# =========================================

@auth_router.post("/login")
async def login(req: LoginRequest):
    """Authenticate user and return tokens."""
    svc = get_auth_service()
    session = svc.login(
        email=req.email,
        password=req.password,
        tenant_id=req.tenant_id,
    )
    if not session:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_at": session.expires_at,
        "user_id": session.user_id,
        "tenant_id": session.tenant_id,
    }


@auth_router.post("/logout")
async def logout(access_token: str):
    """Log out by revoking session."""
    svc = get_auth_service()
    success = svc.logout(access_token)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "logged_out"}


@auth_router.post("/refresh")
async def refresh(req: RefreshTokenRequest):
    """Refresh access token."""
    svc = get_auth_service()
    session = svc.refresh_token(req.refresh_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_at": session.expires_at,
    }


@auth_router.post("/sso/login")
async def sso_login(req: SSOLoginRequest):
    """Authenticate via SSO."""
    svc = get_auth_service()
    session = svc.login_sso(
        tenant_id=req.tenant_id,
        sso_subject_id=req.sso_subject_id,
        email=req.email,
        display_name=req.display_name,
    )
    if not session:
        raise HTTPException(status_code=401, detail="SSO authentication failed")
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_at": session.expires_at,
        "user_id": session.user_id,
    }


@auth_router.post("/users")
async def create_user(req: CreateUserRequest):
    """Create a new user."""
    svc = get_auth_service()
    try:
        role = Role(req.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {req.role}")
    try:
        user = svc.create_user(
            email=req.email,
            tenant_id=req.tenant_id,
            password=req.password,
            role=role,
            display_name=req.display_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {
        "id": user.id,
        "email": user.email,
        "tenant_id": user.tenant_id,
        "role": user.role.value,
        "display_name": user.display_name,
    }


@auth_router.get("/users/{tenant_id}")
async def list_users(tenant_id: str):
    """List all users in a tenant."""
    svc = get_auth_service()
    users = svc.list_users(tenant_id)
    return {
        "users": [
            {"id": u.id, "email": u.email, "role": u.role.value,
             "display_name": u.display_name, "active": u.active}
            for u in users
        ],
        "total": len(users),
    }


@auth_router.post("/change-password")
async def change_password(req: ChangePasswordRequest):
    """Change user password."""
    svc = get_auth_service()
    success = svc.change_password(req.user_id, req.old_password, req.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Password change failed")
    return {"status": "password_changed"}


@auth_router.post("/mfa/enable/{user_id}")
async def enable_mfa(user_id: str):
    """Enable MFA for user."""
    svc = get_auth_service()
    secret = svc.enable_mfa(user_id)
    if not secret:
        raise HTTPException(status_code=404, detail="User not found")
    return {"mfa_secret": secret, "status": "enabled"}


# =========================================
# RBAC ENDPOINTS (4)
# =========================================

@auth_router.post("/roles/assign")
async def assign_role(req: AssignRoleRequest):
    """Assign a role to a user."""
    rbac = get_rbac_manager()
    try:
        role = Role(req.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {req.role}")
    rbac.assign_role(req.tenant_id, req.user_id, role)
    return {"status": "role_assigned", "user_id": req.user_id, "role": req.role}


@auth_router.get("/roles/{role}")
async def get_role_permissions(role: str):
    """Get all permissions for a role."""
    rbac = get_rbac_manager()
    try:
        role_enum = Role(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    perms = rbac.get_role_permissions(role_enum)
    return {"role": role, "permissions": perms, "count": len(perms)}


@auth_router.post("/permissions/check")
async def check_permission(req: PermissionCheckRequest):
    """Check if a role has a specific permission."""
    rbac = get_rbac_manager()
    try:
        role = Role(req.role)
        resource = Resource(req.resource)
        action = Action(req.action)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    allowed = rbac.check_permission(role, resource, action)
    return {"allowed": allowed, "role": req.role, "resource": req.resource, "action": req.action}


@auth_router.post("/api-keys")
async def create_api_key(req: CreateApiKeyRequest):
    """Create a new API key."""
    rbac = get_rbac_manager()
    try:
        role = Role(req.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {req.role}")
    api_key, raw_key = rbac.create_api_key(
        tenant_id=req.tenant_id,
        name=req.name,
        role=role,
    )
    return {
        "id": api_key.id,
        "name": api_key.name,
        "key": raw_key,
        "key_prefix": api_key.key_prefix,
        "role": api_key.role.value,
    }


# =========================================
# AUDIT ENDPOINTS (2)
# =========================================

@auth_router.get("/audit/{tenant_id}")
async def get_audit_log(tenant_id: str, user_id: Optional[str] = None, limit: int = 100):
    """Get audit log for a tenant."""
    svc = get_auth_service()
    entries = svc.get_audit_log(tenant_id, user_id=user_id, limit=limit)
    return {
        "entries": [
            {
                "id": e.id,
                "timestamp": e.timestamp,
                "user_id": e.user_id,
                "event_type": e.event_type.value,
                "ip_address": e.ip_address,
                "success": e.success,
                "details": e.details,
            }
            for e in entries
        ],
        "total": len(entries),
    }


@auth_router.get("/audit/{tenant_id}/stats")
async def get_audit_stats(tenant_id: str):
    """Get audit statistics for a tenant."""
    svc = get_auth_service()
    return svc.get_audit_stats(tenant_id)


# =========================================
# HELPERS
# =========================================

def _tenant_to_dict(t: Tenant) -> Dict[str, Any]:
    return {
        "id": t.id,
        "name": t.name,
        "slug": t.slug,
        "status": t.status.value,
        "plan": t.plan,
        "owner_email": t.owner_email,
        "created_at": t.created_at,
        "updated_at": t.updated_at,
        "config": {
            "max_users": t.config.max_users,
            "max_api_calls_per_day": t.config.max_api_calls_per_day,
            "max_storage_gb": t.config.max_storage_gb,
        },
    }


# =========================================
# ROUTER INCLUSION
# =========================================

def include_tenant_router(app: FastAPI) -> None:
    """Include tenant and auth routers in the app."""
    app.include_router(router)
    app.include_router(auth_router)
