"""Comprehensive auth tests for Engine8_Knowledge/auth.py.

Expands on the existing test_auth.py with additional coverage for:
- Full RBAC permission matrix
- Rate limiting edge cases
- API key rotation/revocation
- JWT custom claims and edge cases
- get_current_user dependency behavior
- require_permission / require_role decorators
- Legacy BD_API_KEY fallback
"""

import os
import time
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from Engine8_Knowledge.auth import (
    AuthUser,
    Role,
    ROLE_PERMISSIONS,
    DEV_USER,
    _hash_key,
    create_api_key,
    validate_api_key,
    revoke_api_key,
    create_jwt,
    validate_jwt,
    _check_rate_limit,
    _rate_limits,
    get_current_user,
    require_permission,
    require_role,
    AUTH_EXEMPT_PATHS,
)


# ===================================================================
# Full RBAC Permission Matrix
# ===================================================================


class TestRBACPermissionMatrix:
    """Test every role against every permission scope."""

    ALL_PERMISSIONS = {
        "read", "write", "delete", "admin",
        "pipeline:run", "pipeline:config",
        "contacts:write", "contacts:delete",
        "keys:manage", "users:manage",
    }

    def test_admin_has_all_permissions(self):
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
        assert admin_perms == self.ALL_PERMISSIONS

    def test_bd_manager_permissions(self):
        perms = ROLE_PERMISSIONS[Role.BD_MANAGER]
        assert "read" in perms
        assert "write" in perms
        assert "pipeline:run" in perms
        assert "contacts:write" in perms
        # Should NOT have these
        assert "delete" not in perms
        assert "admin" not in perms
        assert "keys:manage" not in perms
        assert "users:manage" not in perms
        assert "pipeline:config" not in perms
        assert "contacts:delete" not in perms

    def test_bd_team_read_only(self):
        perms = ROLE_PERMISSIONS[Role.BD_TEAM]
        assert perms == {"read"}
        for p in self.ALL_PERMISSIONS - {"read"}:
            assert p not in perms

    @pytest.mark.parametrize("role", [Role.ADMIN, Role.BD_MANAGER, Role.BD_TEAM])
    def test_all_roles_have_read(self, role):
        assert "read" in ROLE_PERMISSIONS[role]

    def test_authuser_has_permission_checks_set(self):
        user = AuthUser(
            user_id="test",
            role=Role.BD_MANAGER,
            auth_method="api_key",
            permissions=ROLE_PERMISSIONS[Role.BD_MANAGER],
        )
        assert user.has_permission("read")
        assert user.has_permission("write")
        assert not user.has_permission("admin")
        assert not user.has_permission("delete")

    def test_admin_user_all_permissions(self):
        user = AuthUser(
            user_id="admin",
            role=Role.ADMIN,
            auth_method="jwt",
            permissions=ROLE_PERMISSIONS[Role.ADMIN],
        )
        for perm in self.ALL_PERMISSIONS:
            assert user.has_permission(perm), f"Admin missing permission: {perm}"


# ===================================================================
# Rate Limiting Edge Cases
# ===================================================================


class TestRateLimitingEdgeCases:
    def setup_method(self):
        _rate_limits.clear()

    def test_burst_at_exact_limit(self):
        limit = 5
        for _ in range(limit):
            assert _check_rate_limit("burst-user", limit) is True
        # The next request should be blocked
        assert _check_rate_limit("burst-user", limit) is False

    def test_window_expiry_allows_new_requests(self):
        limit = 3
        for _ in range(limit):
            _check_rate_limit("window-user", limit)
        assert _check_rate_limit("window-user", limit) is False

        # Simulate time passing beyond the window
        now = time.time()
        _rate_limits["window-user"] = [now - 120]  # older than 60s window
        assert _check_rate_limit("window-user", limit) is True

    def test_different_users_independent(self):
        for _ in range(10):
            _check_rate_limit("user-A", 10)
        assert _check_rate_limit("user-A", 10) is False
        assert _check_rate_limit("user-B", 10) is True

    def test_limit_of_one(self):
        assert _check_rate_limit("single-user", 1) is True
        assert _check_rate_limit("single-user", 1) is False

    def test_new_user_starts_fresh(self):
        assert "new-user" not in _rate_limits
        assert _check_rate_limit("new-user", 100) is True
        assert "new-user" in _rate_limits

    def test_old_entries_pruned(self):
        """Entries older than the window are pruned on each check."""
        _rate_limits["prune-user"] = [time.time() - 120, time.time() - 90]
        _check_rate_limit("prune-user", 10)
        # Old entries should be gone, only the new one remains
        assert len(_rate_limits["prune-user"]) == 1


# ===================================================================
# API Key Rotation / Revocation
# ===================================================================


class TestAPIKeyRotation:
    def test_create_multiple_keys(self, tmp_path):
        key_store = tmp_path / "keys.json"
        with patch("Engine8_Knowledge.auth._KEY_STORE_PATH", key_store):
            k1 = create_api_key("key-one", "bd_team")
            k2 = create_api_key("key-two", "bd_manager")

            assert validate_api_key(k1["key"]) is not None
            assert validate_api_key(k2["key"]) is not None

            u1 = validate_api_key(k1["key"])
            u2 = validate_api_key(k2["key"])
            assert u1.role == Role.BD_TEAM
            assert u2.role == Role.BD_MANAGER

    def test_revoke_key(self, tmp_path):
        key_store = tmp_path / "keys.json"
        with patch("Engine8_Knowledge.auth._KEY_STORE_PATH", key_store):
            result = create_api_key("revoke-me", "bd_team")
            key_hash = _hash_key(result["key"])

            # Key works before revocation
            assert validate_api_key(result["key"]) is not None

            # Revoke
            assert revoke_api_key(key_hash) is True

            # Key no longer works
            assert validate_api_key(result["key"]) is None

    def test_revoke_nonexistent_key(self, tmp_path):
        key_store = tmp_path / "keys.json"
        with patch("Engine8_Knowledge.auth._KEY_STORE_PATH", key_store):
            assert revoke_api_key("nonexistent_hash") is False

    def test_old_key_still_works_after_new_key_created(self, tmp_path):
        key_store = tmp_path / "keys.json"
        with patch("Engine8_Knowledge.auth._KEY_STORE_PATH", key_store):
            old = create_api_key("old-key", "admin")
            new = create_api_key("new-key", "admin")

            assert validate_api_key(old["key"]) is not None
            assert validate_api_key(new["key"]) is not None

    def test_key_prefix(self, tmp_path):
        key_store = tmp_path / "keys.json"
        with patch("Engine8_Knowledge.auth._KEY_STORE_PATH", key_store):
            result = create_api_key("prefixed", "bd_team")
            assert result["key"].startswith("bd_")

    def test_validate_updates_last_used(self, tmp_path):
        key_store = tmp_path / "keys.json"
        with patch("Engine8_Knowledge.auth._KEY_STORE_PATH", key_store):
            result = create_api_key("timestamp-key", "bd_team")
            validate_api_key(result["key"])

            import json
            store_data = json.loads(key_store.read_text())
            key_hash = _hash_key(result["key"])
            assert store_data["keys"][key_hash]["last_used"] is not None


# ===================================================================
# JWT Edge Cases
# ===================================================================


class TestJWTEdgeCases:
    @pytest.fixture(autouse=True)
    def _set_jwt_secret(self):
        with patch("Engine8_Knowledge.auth._JWT_SECRET", "test-secret-key-123"):
            yield

    def test_jwt_contains_three_parts(self):
        token = create_jwt("user", "admin")
        assert token.count(".") == 2

    def test_jwt_all_roles(self):
        for role in [Role.ADMIN, Role.BD_MANAGER, Role.BD_TEAM]:
            token = create_jwt("user", role.value)
            user = validate_jwt(token)
            assert user is not None
            assert user.role == role

    def test_jwt_permissions_match_role(self):
        token = create_jwt("user", "bd_manager")
        user = validate_jwt(token)
        assert user.permissions == ROLE_PERMISSIONS[Role.BD_MANAGER]

    def test_jwt_invalid_format(self):
        assert validate_jwt("not-a-jwt") is None
        assert validate_jwt("a.b") is None
        assert validate_jwt("a.b.c.d") is None
        assert validate_jwt("") is None

    def test_jwt_tampered_header(self):
        token = create_jwt("user", "admin")
        parts = token.split(".")
        parts[0] = "tampered"
        assert validate_jwt(".".join(parts)) is None

    def test_jwt_tampered_signature(self):
        token = create_jwt("user", "admin")
        parts = token.split(".")
        parts[2] = "badsig"
        assert validate_jwt(".".join(parts)) is None


# ===================================================================
# get_current_user dependency
# ===================================================================


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_dev_mode_returns_dev_user(self):
        """When neither BD_API_KEY nor JWT_SECRET is set, returns DEV_USER."""
        request = MagicMock()
        request.url.path = "/search"

        with patch.dict(os.environ, {"BD_API_KEY": ""}, clear=False), \
             patch("Engine8_Knowledge.auth._JWT_SECRET", ""):
            user = await get_current_user(request, api_key=None, bearer=None)
            assert user.user_id == "dev"
            assert user.role == Role.ADMIN

    @pytest.mark.asyncio
    async def test_exempt_paths_return_dev_user(self):
        """Auth-exempt paths always return DEV_USER."""
        for path in AUTH_EXEMPT_PATHS:
            request = MagicMock()
            request.url.path = path

            with patch.dict(os.environ, {"BD_API_KEY": "real-key"}, clear=False):
                user = await get_current_user(request, api_key=None, bearer=None)
                assert user.user_id == "dev"

    @pytest.mark.asyncio
    async def test_valid_api_key(self, tmp_path):
        key_store = tmp_path / "keys.json"
        with patch("Engine8_Knowledge.auth._KEY_STORE_PATH", key_store), \
             patch.dict(os.environ, {"BD_API_KEY": "trigger-auth"}, clear=False):
            result = create_api_key("test-key", "bd_team")
            request = MagicMock()
            request.url.path = "/search"

            # Clear rate limits
            _rate_limits.clear()

            user = await get_current_user(request, api_key=result["key"], bearer=None)
            assert user is not None
            assert user.role == Role.BD_TEAM

    @pytest.mark.asyncio
    async def test_invalid_api_key_raises_401(self):
        from fastapi import HTTPException

        request = MagicMock()
        request.url.path = "/search"

        with patch.dict(os.environ, {"BD_API_KEY": "real-key"}, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(request, api_key="bad-key", bearer=None)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_no_credentials_raises_401(self):
        from fastapi import HTTPException

        request = MagicMock()
        request.url.path = "/search"

        with patch.dict(os.environ, {"BD_API_KEY": "real-key"}, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(request, api_key=None, bearer=None)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_jwt_bearer(self):
        from fastapi import HTTPException

        request = MagicMock()
        request.url.path = "/search"

        with patch("Engine8_Knowledge.auth._JWT_SECRET", "test-secret"), \
             patch.dict(os.environ, {"BD_API_KEY": ""}, clear=False):
            # Need JWT_SECRET to be set for auth to be required
            # But also need BD_API_KEY empty so only JWT path is tried
            # Actually, with JWT_SECRET set and BD_API_KEY empty, dev mode is off
            pass

        # Test with both BD_API_KEY and JWT_SECRET set
        with patch("Engine8_Knowledge.auth._JWT_SECRET", "test-secret"), \
             patch.dict(os.environ, {"BD_API_KEY": "some-key"}, clear=False):
            token = create_jwt("jwt-user", "bd_manager")
            bearer = MagicMock()
            bearer.credentials = token

            _rate_limits.clear()

            user = await get_current_user(request, api_key=None, bearer=bearer)
            assert user.user_id == "jwt-user"
            assert user.role == Role.BD_MANAGER

    @pytest.mark.asyncio
    async def test_expired_jwt_raises_401(self):
        from fastapi import HTTPException

        request = MagicMock()
        request.url.path = "/search"

        with patch("Engine8_Knowledge.auth._JWT_SECRET", "test-secret"), \
             patch("Engine8_Knowledge.auth._JWT_EXPIRY_HOURS", 0), \
             patch.dict(os.environ, {"BD_API_KEY": "some-key"}, clear=False):
            token = create_jwt("user", "admin")

        time.sleep(1)

        with patch("Engine8_Knowledge.auth._JWT_SECRET", "test-secret"), \
             patch.dict(os.environ, {"BD_API_KEY": "some-key"}, clear=False):
            bearer = MagicMock()
            bearer.credentials = token
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(request, api_key=None, bearer=bearer)
            assert exc_info.value.status_code == 401


# ===================================================================
# require_permission / require_role
# ===================================================================


class TestRequirePermission:
    @pytest.mark.asyncio
    async def test_permission_granted(self):
        checker = require_permission("read")
        user = AuthUser(
            user_id="test", role=Role.BD_TEAM,
            auth_method="api_key", permissions={"read"},
        )
        result = await checker(user=user)
        assert result == user

    @pytest.mark.asyncio
    async def test_permission_denied(self):
        from fastapi import HTTPException

        checker = require_permission("admin")
        user = AuthUser(
            user_id="test", role=Role.BD_TEAM,
            auth_method="api_key", permissions={"read"},
        )
        with pytest.raises(HTTPException) as exc_info:
            await checker(user=user)
        assert exc_info.value.status_code == 403
        assert "admin" in str(exc_info.value.detail)


class TestRequireRole:
    @pytest.mark.asyncio
    async def test_sufficient_role(self):
        checker = require_role(Role.BD_TEAM)
        user = AuthUser(
            user_id="mgr", role=Role.BD_MANAGER,
            auth_method="jwt", permissions=ROLE_PERMISSIONS[Role.BD_MANAGER],
        )
        result = await checker(user=user)
        assert result == user

    @pytest.mark.asyncio
    async def test_admin_passes_any_role_check(self):
        for min_role in [Role.BD_TEAM, Role.BD_MANAGER, Role.ADMIN]:
            checker = require_role(min_role)
            user = AuthUser(
                user_id="admin", role=Role.ADMIN,
                auth_method="jwt", permissions=ROLE_PERMISSIONS[Role.ADMIN],
            )
            result = await checker(user=user)
            assert result == user

    @pytest.mark.asyncio
    async def test_insufficient_role(self):
        from fastapi import HTTPException

        checker = require_role(Role.ADMIN)
        user = AuthUser(
            user_id="team", role=Role.BD_TEAM,
            auth_method="api_key", permissions=ROLE_PERMISSIONS[Role.BD_TEAM],
        )
        with pytest.raises(HTTPException) as exc_info:
            await checker(user=user)
        assert exc_info.value.status_code == 403


# ===================================================================
# Legacy BD_API_KEY Fallback
# ===================================================================


class TestLegacyKeyFallback:
    def test_legacy_key_returns_admin(self):
        with patch.dict(os.environ, {"BD_API_KEY": "legacy-secret-123"}):
            user = validate_api_key("legacy-secret-123")
            assert user is not None
            assert user.user_id == "legacy_key"
            assert user.role == Role.ADMIN
            assert user.auth_method == "api_key"

    def test_wrong_legacy_key(self):
        with patch.dict(os.environ, {"BD_API_KEY": "correct-key"}):
            user = validate_api_key("wrong-key")
            # Falls through to key store lookup, which has no keys
            assert user is None

    def test_legacy_key_empty(self, tmp_path):
        key_store = tmp_path / "keys.json"
        with patch("Engine8_Knowledge.auth._KEY_STORE_PATH", key_store), \
             patch.dict(os.environ, {"BD_API_KEY": ""}):
            user = validate_api_key("any-key")
            assert user is None
