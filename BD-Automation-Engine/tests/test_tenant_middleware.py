"""Tests for Phase 37A — Tenant-Aware Middleware."""

import pytest

from src.middleware.tenant_middleware import (
    TenantContext,
    TenantMiddleware,
    TenantRateLimiter,
    get_current_tenant,
    require_permission,
    require_role,
    get_tenant_middleware,
)
from src.auth.rbac import Action, Resource, Role, Scope, get_rbac_manager
from src.auth.auth_service import AuthService, get_auth_service
from src.tenants.tenant_manager import TenantManager, get_tenant_manager


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def setup():
    """Set up tenant, user, and session for middleware tests."""
    tenant_mgr = TenantManager()
    tenant = tenant_mgr.create_tenant(name="TestCorp", owner_email="admin@test.com")

    auth_svc = AuthService()
    user = auth_svc.create_user(
        email="user@test.com",
        tenant_id=tenant.id,
        password="TestPass123!",
        role=Role.BD_MANAGER,
    )
    session = auth_svc.login(
        email="user@test.com",
        password="TestPass123!",
        tenant_id=tenant.id,
    )

    # We need to patch singletons for middleware to find them
    import src.auth.auth_service as auth_mod
    import src.tenants.tenant_manager as tenant_mod
    old_auth = auth_mod._service
    old_tenant = tenant_mod._manager
    auth_mod._service = auth_svc
    tenant_mod._manager = tenant_mgr

    yield {
        "tenant": tenant,
        "user": user,
        "session": session,
        "auth_svc": auth_svc,
        "tenant_mgr": tenant_mgr,
    }

    # Restore
    auth_mod._service = old_auth
    tenant_mod._manager = old_tenant


# =========================================
# TENANT CONTEXT
# =========================================

class TestTenantContext:
    def test_context_dataclass(self):
        ctx = TenantContext(tenant_id="t1", user_id="u1", role=Role.BD_MANAGER)
        assert ctx.tenant_id == "t1"
        assert ctx.role == Role.BD_MANAGER

    def test_default_auth_method(self):
        ctx = TenantContext(tenant_id="t1")
        assert ctx.auth_method == "none"


# =========================================
# MIDDLEWARE RESOLUTION
# =========================================

class TestMiddlewareResolution:
    def test_resolve_bearer_token(self, setup):
        mw = TenantMiddleware()
        headers = {"Authorization": f"Bearer {setup['session'].access_token}"}
        ctx = mw.resolve_context(headers)
        assert ctx is not None
        assert ctx.tenant_id == setup["tenant"].id
        assert ctx.auth_method == "token"
        assert ctx.user_id == setup["user"].id

    def test_resolve_api_key(self, setup):
        rbac_mgr = get_rbac_manager()
        key, raw = rbac_mgr.create_api_key(setup["tenant"].id, "Test")
        mw = TenantMiddleware()
        headers = {"X-API-Key": raw}
        ctx = mw.resolve_context(headers)
        assert ctx is not None
        assert ctx.auth_method == "api_key"
        assert ctx.tenant_id == setup["tenant"].id

    def test_resolve_tenant_header(self, setup):
        mw = TenantMiddleware()
        headers = {"X-Tenant-ID": setup["tenant"].id}
        ctx = mw.resolve_context(headers)
        assert ctx is not None
        assert ctx.auth_method == "header"

    def test_resolve_no_auth(self, setup):
        mw = TenantMiddleware()
        ctx = mw.resolve_context({})
        assert ctx is None

    def test_resolve_invalid_token(self, setup):
        mw = TenantMiddleware()
        headers = {"Authorization": "Bearer bad_token_here"}
        ctx = mw.resolve_context(headers)
        assert ctx is None

    def test_resolve_lowercase_headers(self, setup):
        mw = TenantMiddleware()
        headers = {"authorization": f"Bearer {setup['session'].access_token}"}
        ctx = mw.resolve_context(headers)
        assert ctx is not None


# =========================================
# RATE LIMITER
# =========================================

class TestRateLimiter:
    def test_allows_under_limit(self):
        rl = TenantRateLimiter()
        assert rl.check_rate("t1", max_per_minute=10) is True

    def test_blocks_over_limit(self):
        rl = TenantRateLimiter()
        for _ in range(10):
            rl.check_rate("t1", max_per_minute=10)
        assert rl.check_rate("t1", max_per_minute=10) is False

    def test_different_tenants_independent(self):
        rl = TenantRateLimiter()
        for _ in range(10):
            rl.check_rate("t1", max_per_minute=10)
        # t2 should still be allowed
        assert rl.check_rate("t2", max_per_minute=10) is True

    def test_get_usage(self):
        rl = TenantRateLimiter()
        rl.check_rate("t1")
        rl.check_rate("t1")
        usage = rl.get_usage("t1")
        assert usage["requests_last_minute"] == 2

    def test_middleware_rate_check(self, setup):
        mw = TenantMiddleware()
        assert mw.check_rate_limit(setup["tenant"].id) is True


# =========================================
# PERMISSION HELPERS
# =========================================

class TestPermissionHelpers:
    def test_require_permission_granted(self, setup):
        ctx = TenantContext(
            tenant_id=setup["tenant"].id,
            user_id=setup["user"].id,
            role=Role.BD_MANAGER,
        )
        assert require_permission(ctx, Resource.CONTACTS, Action.CREATE) is True

    def test_require_permission_denied(self, setup):
        ctx = TenantContext(
            tenant_id=setup["tenant"].id,
            role=Role.VIEWER,
        )
        assert require_permission(ctx, Resource.CONTACTS, Action.CREATE) is False

    def test_require_role_sufficient(self, setup):
        ctx = TenantContext(tenant_id="t1", role=Role.BD_DIRECTOR)
        assert require_role(ctx, Role.BD_ANALYST) is True

    def test_require_role_insufficient(self, setup):
        ctx = TenantContext(tenant_id="t1", role=Role.VIEWER)
        assert require_role(ctx, Role.BD_MANAGER) is False

    def test_get_current_tenant_helper(self, setup):
        headers = {"Authorization": f"Bearer {setup['session'].access_token}"}
        ctx = get_current_tenant(headers)
        assert ctx is not None


# =========================================
# SINGLETON
# =========================================

class TestSingleton:
    def test_get_middleware(self):
        mw = get_tenant_middleware()
        assert isinstance(mw, TenantMiddleware)

    def test_singleton(self):
        m1 = get_tenant_middleware()
        m2 = get_tenant_middleware()
        assert m1 is m2
