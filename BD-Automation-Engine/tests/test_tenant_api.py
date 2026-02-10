"""Tests for Phase 37A — Tenant & Auth API (21 endpoints)."""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.tenant_api import include_tenant_router
from src.auth.rbac import Role


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def app():
    """Create a test FastAPI app with tenant routes."""
    # Reset singletons for clean state
    import src.tenants.tenant_manager as tm
    import src.auth.auth_service as auth
    import src.auth.rbac as rbac_mod
    old_tm = tm._manager
    old_auth = auth._service
    old_rbac = rbac_mod._manager
    tm._manager = None
    auth._service = None
    rbac_mod._manager = None

    test_app = FastAPI()
    include_tenant_router(test_app)
    yield test_app

    tm._manager = old_tm
    auth._service = old_auth
    rbac_mod._manager = old_rbac


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def tenant_id(client):
    """Create a tenant and return its ID."""
    resp = client.post("/tenants/", json={
        "name": "Test Corp",
        "owner_email": "admin@test.com",
        "plan": "enterprise",
    })
    return resp.json()["id"]


@pytest.fixture
def user_and_tokens(client, tenant_id):
    """Create a user and login, return user_id + tokens."""
    # Create user
    resp = client.post("/auth/users", json={
        "email": "alice@test.com",
        "tenant_id": tenant_id,
        "password": "Pass123!",
        "role": "bd_manager",
        "display_name": "Alice",
    })
    user_id = resp.json()["id"]

    # Login
    resp = client.post("/auth/login", json={
        "email": "alice@test.com",
        "password": "Pass123!",
        "tenant_id": tenant_id,
    })
    data = resp.json()
    return {
        "user_id": user_id,
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


# =========================================
# TENANT ENDPOINTS
# =========================================

class TestTenantEndpoints:
    def test_create_tenant(self, client):
        resp = client.post("/tenants/", json={
            "name": "Acme",
            "owner_email": "a@a.com",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Acme"
        assert data["status"] == "active"

    def test_list_tenants(self, client, tenant_id):
        resp = client.get("/tenants/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_get_tenant(self, client, tenant_id):
        resp = client.get(f"/tenants/{tenant_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == tenant_id

    def test_get_tenant_not_found(self, client):
        resp = client.get("/tenants/nonexistent")
        assert resp.status_code == 404

    def test_update_tenant(self, client, tenant_id):
        resp = client.put(f"/tenants/{tenant_id}", json={"name": "New Name"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_deactivate_tenant(self, client, tenant_id):
        resp = client.delete(f"/tenants/{tenant_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deactivated"

    def test_tenant_health(self, client, tenant_id):
        resp = client.get(f"/tenants/{tenant_id}/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    def test_tenant_usage(self, client, tenant_id):
        resp = client.get(f"/tenants/{tenant_id}/usage")
        assert resp.status_code == 200
        assert "storage_limit_gb" in resp.json()


# =========================================
# AUTH ENDPOINTS
# =========================================

class TestAuthEndpoints:
    def test_create_user(self, client, tenant_id):
        resp = client.post("/auth/users", json={
            "email": "bob@test.com",
            "tenant_id": tenant_id,
            "password": "Pass!",
            "role": "viewer",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "bob@test.com"
        assert data["role"] == "viewer"

    def test_create_user_invalid_role(self, client, tenant_id):
        resp = client.post("/auth/users", json={
            "email": "c@c.com",
            "tenant_id": tenant_id,
            "role": "invalid_role",
        })
        assert resp.status_code == 400

    def test_create_duplicate_user(self, client, tenant_id):
        client.post("/auth/users", json={"email": "d@d.com", "tenant_id": tenant_id, "password": "p"})
        resp = client.post("/auth/users", json={"email": "d@d.com", "tenant_id": tenant_id, "password": "p"})
        assert resp.status_code == 409

    def test_login(self, client, tenant_id):
        client.post("/auth/users", json={
            "email": "login@test.com",
            "tenant_id": tenant_id,
            "password": "Pass!",
        })
        resp = client.post("/auth/login", json={
            "email": "login@test.com",
            "password": "Pass!",
            "tenant_id": tenant_id,
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_bad_credentials(self, client, tenant_id):
        resp = client.post("/auth/login", json={
            "email": "nobody@x.com",
            "password": "bad",
            "tenant_id": tenant_id,
        })
        assert resp.status_code == 401

    def test_logout(self, client, user_and_tokens):
        resp = client.post(f"/auth/logout?access_token={user_and_tokens['access_token']}")
        assert resp.status_code == 200

    def test_refresh_token(self, client, user_and_tokens):
        resp = client.post("/auth/refresh", json={
            "refresh_token": user_and_tokens["refresh_token"],
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_list_users(self, client, tenant_id):
        client.post("/auth/users", json={"email": "u1@t.com", "tenant_id": tenant_id, "password": "p"})
        resp = client.get(f"/auth/users/{tenant_id}")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_change_password(self, client, user_and_tokens):
        resp = client.post("/auth/change-password", json={
            "user_id": user_and_tokens["user_id"],
            "old_password": "Pass123!",
            "new_password": "NewPass456!",
        })
        assert resp.status_code == 200

    def test_enable_mfa(self, client, user_and_tokens):
        resp = client.post(f"/auth/mfa/enable/{user_and_tokens['user_id']}")
        assert resp.status_code == 200
        assert "mfa_secret" in resp.json()


# =========================================
# RBAC ENDPOINTS
# =========================================

class TestRBACEndpoints:
    def test_assign_role(self, client, tenant_id, user_and_tokens):
        resp = client.post("/auth/roles/assign", json={
            "tenant_id": tenant_id,
            "user_id": user_and_tokens["user_id"],
            "role": "bd_director",
        })
        assert resp.status_code == 200
        assert resp.json()["role"] == "bd_director"

    def test_get_role_permissions(self, client):
        resp = client.get("/auth/roles/viewer")
        assert resp.status_code == 200
        assert resp.json()["count"] > 0

    def test_get_invalid_role(self, client):
        resp = client.get("/auth/roles/fake_role")
        assert resp.status_code == 400

    def test_check_permission(self, client):
        resp = client.post("/auth/permissions/check", json={
            "role": "tenant_admin",
            "resource": "contacts",
            "action": "create",
        })
        assert resp.status_code == 200
        assert resp.json()["allowed"] is True

    def test_create_api_key(self, client, tenant_id):
        resp = client.post("/auth/api-keys", json={
            "tenant_id": tenant_id,
            "name": "CI Bot",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["key"].startswith("bdapi_")
        assert data["name"] == "CI Bot"


# =========================================
# AUDIT ENDPOINTS
# =========================================

class TestAuditEndpoints:
    def test_get_audit_log(self, client, tenant_id, user_and_tokens):
        resp = client.get(f"/auth/audit/{tenant_id}")
        assert resp.status_code == 200
        assert resp.json()["total"] > 0

    def test_get_audit_stats(self, client, tenant_id, user_and_tokens):
        resp = client.get(f"/auth/audit/{tenant_id}/stats")
        assert resp.status_code == 200
        assert "total_events" in resp.json()


# =========================================
# SSO ENDPOINT
# =========================================

class TestSSOEndpoint:
    def test_sso_login_no_config(self, client, tenant_id):
        resp = client.post("/auth/sso/login", json={
            "tenant_id": tenant_id,
            "sso_subject_id": "ext-1",
            "email": "sso@test.com",
        })
        assert resp.status_code == 401
