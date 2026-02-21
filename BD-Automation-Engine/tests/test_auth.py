"""Tests for the auth module (Engine8_Knowledge/auth.py)."""

import os
import time
from unittest.mock import patch

import pytest

# Import after conftest sets up env vars
from Engine8_Knowledge.auth import (
    AuthUser,
    Role,
    ROLE_PERMISSIONS,
    DEV_USER,
    _hash_key,
    create_api_key,
    validate_api_key,
    create_jwt,
    validate_jwt,
    _check_rate_limit,
    _rate_limits,
)


class TestRoles:
    def test_role_values(self):
        assert Role.ADMIN.value == "admin"
        assert Role.BD_MANAGER.value == "bd_manager"
        assert Role.BD_TEAM.value == "bd_team"

    def test_admin_has_all_permissions(self):
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
        assert "read" in admin_perms
        assert "write" in admin_perms
        assert "delete" in admin_perms
        assert "admin" in admin_perms
        assert "keys:manage" in admin_perms

    def test_bd_team_is_read_only(self):
        team_perms = ROLE_PERMISSIONS[Role.BD_TEAM]
        assert team_perms == {"read"}
        assert "write" not in team_perms

    def test_bd_manager_can_write(self):
        mgr_perms = ROLE_PERMISSIONS[Role.BD_MANAGER]
        assert "read" in mgr_perms
        assert "write" in mgr_perms
        assert "pipeline:run" in mgr_perms
        assert "admin" not in mgr_perms


class TestAuthUser:
    def test_has_permission(self):
        user = AuthUser(
            user_id="test",
            role=Role.BD_TEAM,
            auth_method="api_key",
            permissions={"read"},
        )
        assert user.has_permission("read")
        assert not user.has_permission("write")

    def test_dev_user_is_admin(self):
        assert DEV_USER.role == Role.ADMIN
        assert DEV_USER.auth_method == "dev"
        assert DEV_USER.has_permission("admin")


class TestApiKeys:
    def test_create_and_validate(self, tmp_path):
        key_store = tmp_path / "keys.json"
        with patch("Engine8_Knowledge.auth._KEY_STORE_PATH", key_store):
            result = create_api_key("test-key", "bd_team")
            assert result["key"].startswith("bd_")
            assert result["role"] == "bd_team"

            user = validate_api_key(result["key"])
            assert user is not None
            assert user.role == Role.BD_TEAM
            assert user.has_permission("read")
            assert not user.has_permission("write")

    def test_invalid_key_returns_none(self, tmp_path):
        key_store = tmp_path / "keys.json"
        with patch("Engine8_Knowledge.auth._KEY_STORE_PATH", key_store):
            assert validate_api_key("bd_invalid_key_here") is None

    def test_legacy_key_mode(self):
        with patch.dict(os.environ, {"BD_API_KEY": "my-legacy-key"}):
            user = validate_api_key("my-legacy-key")
            assert user is not None
            assert user.user_id == "legacy_key"
            assert user.role == Role.ADMIN

    def test_hash_key_deterministic(self):
        h1 = _hash_key("test-key")
        h2 = _hash_key("test-key")
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex


class TestJWT:
    @pytest.fixture(autouse=True)
    def _set_jwt_secret(self):
        with patch("Engine8_Knowledge.auth._JWT_SECRET", "test-secret-key"):
            yield

    def test_create_and_validate(self):
        token = create_jwt("user@example.com", "bd_manager")
        assert token.count(".") == 2

        user = validate_jwt(token)
        assert user is not None
        assert user.user_id == "user@example.com"
        assert user.role == Role.BD_MANAGER
        assert user.has_permission("write")

    def test_expired_token_rejected(self):
        with patch("Engine8_Knowledge.auth._JWT_EXPIRY_HOURS", 0):
            token = create_jwt("user@example.com", "bd_team")
        # Token created with 0 hours expiry is already expired
        time.sleep(1)
        user = validate_jwt(token)
        assert user is None

    def test_tampered_token_rejected(self):
        token = create_jwt("user@example.com", "admin")
        # Tamper with payload
        parts = token.split(".")
        parts[1] = parts[1][::-1]  # Reverse payload
        tampered = ".".join(parts)
        assert validate_jwt(tampered) is None

    def test_no_secret_raises(self):
        with patch("Engine8_Knowledge.auth._JWT_SECRET", ""):
            with pytest.raises(ValueError, match="BD_JWT_SECRET"):
                create_jwt("user", "admin")

    def test_no_secret_validate_returns_none(self):
        with patch("Engine8_Knowledge.auth._JWT_SECRET", ""):
            assert validate_jwt("some.fake.token") is None


class TestRateLimit:
    def setup_method(self):
        _rate_limits.clear()

    def test_allows_under_limit(self):
        for _ in range(5):
            assert _check_rate_limit("test-user", 10)

    def test_blocks_over_limit(self):
        for _ in range(10):
            _check_rate_limit("test-user", 10)
        assert not _check_rate_limit("test-user", 10)

    def test_separate_users(self):
        for _ in range(10):
            _check_rate_limit("user-a", 10)
        # user-a is at limit, but user-b should still be fine
        assert _check_rate_limit("user-b", 10)
