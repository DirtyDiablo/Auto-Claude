"""Phase 37A — Tenant-Aware API Middleware

Middleware stack:
  - Tenant resolution from headers / JWT / API key
  - Authentication enforcement
  - Permission checking decorators
  - Rate limiting per tenant
  - Request context injection
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.auth.rbac import Action, Resource, Role, Scope, get_rbac_manager
from src.auth.auth_service import get_auth_service
from src.tenants.tenant_manager import TenantStatus, get_tenant_manager

logger = logging.getLogger(__name__)


# =========================================
# TENANT CONTEXT
# =========================================

@dataclass
class TenantContext:
    """Per-request tenant context injected by middleware."""
    tenant_id: str
    tenant_name: str = ""
    user_id: str = ""
    user_email: str = ""
    role: Role = Role.VIEWER
    session_id: str = ""
    auth_method: str = "none"   # token, api_key, sso
    request_id: str = ""
    timestamp: str = ""


# =========================================
# RATE LIMITER
# =========================================

class TenantRateLimiter:
    """Simple in-memory per-tenant rate limiter."""

    def __init__(self):
        self._counters: Dict[str, List[float]] = {}  # tenant_id -> [timestamps]

    def check_rate(self, tenant_id: str, max_per_minute: int = 60) -> bool:
        """Check if tenant is within rate limit. Returns True if allowed."""
        now = time.time()
        window = 60.0

        if tenant_id not in self._counters:
            self._counters[tenant_id] = []

        # Purge old entries
        self._counters[tenant_id] = [
            t for t in self._counters[tenant_id] if now - t < window
        ]

        if len(self._counters[tenant_id]) >= max_per_minute:
            return False

        self._counters[tenant_id].append(now)
        return True

    def get_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get current rate limit usage."""
        now = time.time()
        timestamps = self._counters.get(tenant_id, [])
        recent = [t for t in timestamps if now - t < 60.0]
        return {
            "tenant_id": tenant_id,
            "requests_last_minute": len(recent),
        }


# =========================================
# MIDDLEWARE
# =========================================

class TenantMiddleware:
    """Resolve tenant context from request headers.

    Supported header patterns:
      - Authorization: Bearer <access_token>  → JWT session lookup
      - X-API-Key: <key>                      → API key lookup
      - X-Tenant-ID: <id>                     → Explicit tenant (dev/testing)
    """

    def __init__(self):
        self._rate_limiter = TenantRateLimiter()

    def resolve_context(
        self,
        headers: Dict[str, str],
        ip_address: str = "",
        user_agent: str = "",
    ) -> Optional[TenantContext]:
        """Resolve tenant context from request headers."""
        import uuid
        request_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc).isoformat()

        auth_service = get_auth_service()
        rbac = get_rbac_manager()
        tenant_mgr = get_tenant_manager()

        # 1. Try Bearer token
        auth_header = headers.get("authorization", headers.get("Authorization", ""))
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            session = auth_service.validate_token(token)
            if session:
                user = auth_service.get_user(session.user_id)
                if user:
                    return TenantContext(
                        tenant_id=session.tenant_id,
                        tenant_name=self._get_tenant_name(tenant_mgr, session.tenant_id),
                        user_id=user.id,
                        user_email=user.email,
                        role=user.role,
                        session_id=session.id,
                        auth_method="token",
                        request_id=request_id,
                        timestamp=now,
                    )

        # 2. Try API key
        api_key_header = headers.get("x-api-key", headers.get("X-API-Key", ""))
        if api_key_header:
            api_key = rbac.validate_api_key(api_key_header)
            if api_key:
                return TenantContext(
                    tenant_id=api_key.tenant_id,
                    tenant_name=self._get_tenant_name(tenant_mgr, api_key.tenant_id),
                    role=api_key.role,
                    auth_method="api_key",
                    request_id=request_id,
                    timestamp=now,
                )

        # 3. Try explicit tenant header (dev/testing mode)
        tenant_header = headers.get("x-tenant-id", headers.get("X-Tenant-ID", ""))
        if tenant_header:
            tenant = tenant_mgr.get_tenant(tenant_header)
            if tenant and tenant.status == TenantStatus.ACTIVE:
                return TenantContext(
                    tenant_id=tenant.id,
                    tenant_name=tenant.name,
                    auth_method="header",
                    request_id=request_id,
                    timestamp=now,
                )

        return None

    def check_rate_limit(self, tenant_id: str, max_per_minute: int = 60) -> bool:
        """Check tenant rate limit."""
        return self._rate_limiter.check_rate(tenant_id, max_per_minute)

    def get_rate_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get rate limit usage for tenant."""
        return self._rate_limiter.get_usage(tenant_id)

    @staticmethod
    def _get_tenant_name(tenant_mgr, tenant_id: str) -> str:
        tenant = tenant_mgr.get_tenant(tenant_id)
        return tenant.name if tenant else ""


# =========================================
# PERMISSION DECORATORS (functional style)
# =========================================

def get_current_tenant(headers: Dict[str, str]) -> Optional[TenantContext]:
    """Quick helper to resolve tenant context from headers."""
    mw = TenantMiddleware()
    return mw.resolve_context(headers)


def require_permission(
    ctx: TenantContext,
    resource: Resource,
    action: Action,
    scope: Scope = Scope.TENANT,
) -> bool:
    """Check if context has required permission. Returns True/False."""
    rbac = get_rbac_manager()
    return rbac.check_permission(ctx.role, resource, action, scope)


def require_role(ctx: TenantContext, minimum_role: Role) -> bool:
    """Check if context has at least the minimum role."""
    rbac = get_rbac_manager()
    return rbac.is_role_at_least(ctx.role, minimum_role)


# =========================================
# SINGLETON
# =========================================

_middleware: Optional[TenantMiddleware] = None


def get_tenant_middleware() -> TenantMiddleware:
    global _middleware
    if _middleware is None:
        _middleware = TenantMiddleware()
    return _middleware
