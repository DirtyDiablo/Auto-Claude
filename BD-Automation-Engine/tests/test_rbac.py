"""Tests for Phase 37A — Role-Based Access Control."""

import pytest

from src.auth.rbac import (
    Role,
    Resource,
    Action,
    Scope,
    RBACManager,
    ROLE_HIERARCHY,
    has_permission,
    get_rbac_manager,
)


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def rbac():
    return RBACManager()


# =========================================
# ROLE ENUM
# =========================================


class TestRoleEnum:
    def test_all_roles_defined(self):
        assert len(Role) == 7

    def test_role_values(self):
        assert Role.SUPER_ADMIN.value == "super_admin"
        assert Role.VIEWER.value == "viewer"
        assert Role.API_SERVICE.value == "api_service"


# =========================================
# PERMISSION CHECKING
# =========================================


class TestPermissionChecking:
    def test_super_admin_has_all(self, rbac):
        for resource in Resource:
            for action in Action:
                assert rbac.check_permission(Role.SUPER_ADMIN, resource, action)

    def test_tenant_admin_has_all(self, rbac):
        for resource in Resource:
            for action in Action:
                assert rbac.check_permission(Role.TENANT_ADMIN, resource, action)

    def test_viewer_read_analytics(self, rbac):
        assert rbac.check_permission(Role.VIEWER, Resource.ANALYTICS, Action.READ)

    def test_viewer_read_programs(self, rbac):
        assert rbac.check_permission(Role.VIEWER, Resource.PROGRAMS, Action.READ)

    def test_viewer_cannot_create_contacts(self, rbac):
        assert not rbac.check_permission(Role.VIEWER, Resource.CONTACTS, Action.CREATE)

    def test_viewer_cannot_delete(self, rbac):
        assert not rbac.check_permission(Role.VIEWER, Resource.CONTACTS, Action.DELETE)

    def test_bd_analyst_read_only(self, rbac):
        assert rbac.check_permission(Role.BD_ANALYST, Resource.CONTACTS, Action.READ)
        assert not rbac.check_permission(
            Role.BD_ANALYST, Resource.CONTACTS, Action.CREATE
        )

    def test_bd_manager_crud_contacts(self, rbac):
        assert rbac.check_permission(Role.BD_MANAGER, Resource.CONTACTS, Action.CREATE)
        assert rbac.check_permission(Role.BD_MANAGER, Resource.CONTACTS, Action.READ)
        assert rbac.check_permission(Role.BD_MANAGER, Resource.CONTACTS, Action.UPDATE)
        assert rbac.check_permission(Role.BD_MANAGER, Resource.CONTACTS, Action.DELETE)

    def test_bd_manager_read_jobs(self, rbac):
        assert rbac.check_permission(Role.BD_MANAGER, Resource.JOBS, Action.READ)
        assert not rbac.check_permission(Role.BD_MANAGER, Resource.JOBS, Action.DELETE)

    def test_bd_director_full_bd(self, rbac):
        assert rbac.check_permission(Role.BD_DIRECTOR, Resource.CONTACTS, Action.ADMIN)
        assert rbac.check_permission(
            Role.BD_DIRECTOR, Resource.CAMPAIGNS, Action.EXPORT
        )

    def test_bd_director_revenue_read(self, rbac):
        assert rbac.check_permission(Role.BD_DIRECTOR, Resource.REVENUE, Action.READ)
        assert rbac.check_permission(Role.BD_DIRECTOR, Resource.REVENUE, Action.EXPORT)

    def test_api_service_permissions(self, rbac):
        assert rbac.check_permission(Role.API_SERVICE, Resource.CONTACTS, Action.READ)
        assert rbac.check_permission(Role.API_SERVICE, Resource.CONTACTS, Action.CREATE)
        assert not rbac.check_permission(
            Role.API_SERVICE, Resource.CONTACTS, Action.DELETE
        )

    def test_scope_escalation_own_to_tenant(self, rbac):
        # If role has tenant scope, requesting own scope should also pass
        assert rbac.check_permission(
            Role.TENANT_ADMIN, Resource.CONTACTS, Action.READ, Scope.OWN
        )

    def test_scope_escalation_team_to_tenant(self, rbac):
        assert rbac.check_permission(
            Role.TENANT_ADMIN, Resource.CONTACTS, Action.READ, Scope.TEAM
        )


# =========================================
# ROLE HIERARCHY
# =========================================


class TestRoleHierarchy:
    def test_hierarchy_order(self):
        assert ROLE_HIERARCHY.index(Role.VIEWER) < ROLE_HIERARCHY.index(
            Role.SUPER_ADMIN
        )

    def test_is_role_at_least(self, rbac):
        assert rbac.is_role_at_least(Role.TENANT_ADMIN, Role.VIEWER)
        assert rbac.is_role_at_least(Role.BD_DIRECTOR, Role.BD_ANALYST)

    def test_is_not_at_least(self, rbac):
        assert not rbac.is_role_at_least(Role.VIEWER, Role.BD_MANAGER)

    def test_same_role_at_least(self, rbac):
        assert rbac.is_role_at_least(Role.BD_MANAGER, Role.BD_MANAGER)

    def test_api_service_not_in_hierarchy(self, rbac):
        # API_SERVICE is not in hierarchy, should return False
        assert not rbac.is_role_at_least(Role.API_SERVICE, Role.VIEWER)


# =========================================
# USER ROLE MANAGEMENT
# =========================================


class TestUserRoles:
    def test_assign_role(self, rbac):
        rbac.assign_role("t1", "u1", Role.BD_ANALYST)
        assert rbac.get_user_role("t1", "u1") == Role.BD_ANALYST

    def test_get_unassigned_role(self, rbac):
        assert rbac.get_user_role("t1", "u999") is None

    def test_remove_role(self, rbac):
        rbac.assign_role("t1", "u1", Role.BD_ANALYST)
        assert rbac.remove_user_role("t1", "u1") is True
        assert rbac.get_user_role("t1", "u1") is None

    def test_remove_nonexistent(self, rbac):
        assert rbac.remove_user_role("t1", "u999") is False

    def test_list_tenant_users(self, rbac):
        rbac.assign_role("t1", "u1", Role.VIEWER)
        rbac.assign_role("t1", "u2", Role.BD_MANAGER)
        users = rbac.list_tenant_users("t1")
        assert len(users) == 2


# =========================================
# API KEY MANAGEMENT
# =========================================


class TestAPIKeys:
    def test_create_api_key(self, rbac):
        key, raw = rbac.create_api_key("t1", "Test Key")
        assert key.tenant_id == "t1"
        assert key.name == "Test Key"
        assert raw.startswith("bdapi_")

    def test_validate_api_key(self, rbac):
        key, raw = rbac.create_api_key("t1", "Key")
        validated = rbac.validate_api_key(raw)
        assert validated is not None
        assert validated.id == key.id

    def test_invalid_api_key(self, rbac):
        assert rbac.validate_api_key("bad_key") is None

    def test_revoke_api_key(self, rbac):
        key, raw = rbac.create_api_key("t1", "Key")
        assert rbac.revoke_api_key(key.id) is True
        assert rbac.validate_api_key(raw) is None

    def test_list_api_keys(self, rbac):
        rbac.create_api_key("t1", "A")
        rbac.create_api_key("t1", "B")
        rbac.create_api_key("t2", "C")
        assert len(rbac.list_api_keys("t1")) == 2
        assert len(rbac.list_api_keys("t2")) == 1


# =========================================
# CONVENIENCE + SINGLETON
# =========================================


class TestConvenience:
    def test_has_permission(self):
        assert has_permission(Role.SUPER_ADMIN, Resource.CONTACTS, Action.READ)
        assert not has_permission(Role.VIEWER, Resource.CONTACTS, Action.CREATE)

    def test_get_role_permissions(self, rbac):
        perms = rbac.get_role_permissions(Role.VIEWER)
        assert len(perms) > 0
        assert all("resource" in p for p in perms)

    def test_singleton(self):
        r1 = get_rbac_manager()
        r2 = get_rbac_manager()
        assert r1 is r2
