"""Tests for Phase 37A — Authentication Service."""

import time
import pytest

from src.auth.auth_service import (
    AuthService,
    AuthProvider,
    AuthEventType,
    User,
    SSOConfig,
    get_auth_service,
    MAX_LOGIN_ATTEMPTS,
    MAX_CONCURRENT_SESSIONS,
)
from src.auth.rbac import Role


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def svc():
    return AuthService()


@pytest.fixture
def user(svc):
    return svc.create_user(
        email="alice@acme.com",
        tenant_id="t1",
        password="SecurePass123!",
        role=Role.BD_MANAGER,
        display_name="Alice Smith",
    )


@pytest.fixture
def session(svc, user):
    return svc.login(
        email="alice@acme.com",
        password="SecurePass123!",
        tenant_id="t1",
        ip_address="10.0.0.1",
        user_agent="TestAgent/1.0",
    )


# =========================================
# PASSWORD HASHING
# =========================================


class TestPasswordHashing:
    def test_hash_contains_salt(self, svc):
        h = svc._hash_password("test")
        assert "$" in h

    def test_verify_correct(self, svc):
        h = svc._hash_password("password")
        assert svc._verify_password("password", h)

    def test_verify_incorrect(self, svc):
        h = svc._hash_password("password")
        assert not svc._verify_password("wrong", h)

    def test_verify_bad_format(self, svc):
        assert not svc._verify_password("x", "nohash")


# =========================================
# USER MANAGEMENT
# =========================================


class TestUserManagement:
    def test_create_user(self, svc):
        u = svc.create_user(email="a@b.com", tenant_id="t1", password="pass")
        assert isinstance(u, User)
        assert u.email == "a@b.com"
        assert u.tenant_id == "t1"
        assert u.active is True

    def test_create_user_default_role(self, svc):
        u = svc.create_user(email="b@b.com", tenant_id="t1")
        assert u.role == Role.VIEWER

    def test_create_user_display_name_from_email(self, svc):
        u = svc.create_user(email="john.doe@acme.com", tenant_id="t1")
        assert u.display_name == "john.doe"

    def test_duplicate_email_raises(self, svc):
        svc.create_user(email="x@x.com", tenant_id="t1", password="p")
        with pytest.raises(ValueError):
            svc.create_user(email="x@x.com", tenant_id="t1", password="p")

    def test_same_email_different_tenant(self, svc):
        u1 = svc.create_user(email="x@x.com", tenant_id="t1", password="p")
        u2 = svc.create_user(email="x@x.com", tenant_id="t2", password="p")
        assert u1.id != u2.id

    def test_get_user(self, svc, user):
        found = svc.get_user(user.id)
        assert found is not None
        assert found.email == "alice@acme.com"

    def test_get_user_by_email(self, svc, user):
        found = svc.get_user_by_email("alice@acme.com", "t1")
        assert found is not None
        assert found.id == user.id

    def test_list_users(self, svc, user):
        svc.create_user(email="b@b.com", tenant_id="t1", password="p")
        users = svc.list_users("t1")
        assert len(users) == 2

    def test_deactivate_user(self, svc, user):
        assert svc.deactivate_user(user.id) is True
        assert svc.get_user(user.id).active is False

    def test_change_password(self, svc, user):
        assert svc.change_password(user.id, "SecurePass123!", "NewPass456!")
        # Old password no longer works
        assert not svc._verify_password(
            "SecurePass123!", svc.get_user(user.id).password_hash
        )
        # New password works
        assert svc._verify_password("NewPass456!", svc.get_user(user.id).password_hash)

    def test_change_password_wrong_old(self, svc, user):
        assert not svc.change_password(user.id, "WrongOld!", "NewPass!")


# =========================================
# LOGIN
# =========================================


class TestLogin:
    def test_login_success(self, svc, user):
        sess = svc.login(
            email="alice@acme.com", password="SecurePass123!", tenant_id="t1"
        )
        assert sess is not None
        assert sess.user_id == user.id
        assert sess.access_token.startswith("bd_at_")

    def test_login_bad_password(self, svc, user):
        sess = svc.login(email="alice@acme.com", password="wrong", tenant_id="t1")
        assert sess is None

    def test_login_unknown_user(self, svc):
        sess = svc.login(email="nobody@x.com", password="pass", tenant_id="t1")
        assert sess is None

    def test_login_deactivated(self, svc, user):
        svc.deactivate_user(user.id)
        sess = svc.login(
            email="alice@acme.com", password="SecurePass123!", tenant_id="t1"
        )
        assert sess is None

    def test_login_sets_last_login(self, svc, user):
        svc.login(email="alice@acme.com", password="SecurePass123!", tenant_id="t1")
        assert svc.get_user(user.id).last_login != ""

    def test_account_lockout(self, svc, user):
        for _ in range(MAX_LOGIN_ATTEMPTS):
            svc.login(email="alice@acme.com", password="wrong", tenant_id="t1")
        # Next attempt should fail even with correct password (locked)
        sess = svc.login(
            email="alice@acme.com", password="SecurePass123!", tenant_id="t1"
        )
        assert sess is None


# =========================================
# TOKEN / SESSION
# =========================================


class TestSession:
    def test_validate_token(self, svc, session):
        validated = svc.validate_token(session.access_token)
        assert validated is not None
        assert validated.id == session.id

    def test_validate_invalid_token(self, svc):
        assert svc.validate_token("bad_token") is None

    def test_refresh_token(self, svc, session):
        old_token = session.access_token
        new_session = svc.refresh_token(session.refresh_token)
        assert new_session is not None
        assert new_session.access_token != old_token

    def test_refresh_invalid_token(self, svc):
        assert svc.refresh_token("bad_refresh") is None

    def test_revoke_session(self, svc, session):
        assert svc.revoke_session(session.id) is True
        assert svc.validate_token(session.access_token) is None

    def test_logout(self, svc, session):
        assert svc.logout(session.access_token) is True
        assert svc.validate_token(session.access_token) is None

    def test_logout_invalid(self, svc):
        assert svc.logout("bad_token") is False

    def test_get_user_sessions(self, svc, session):
        sessions = svc.get_user_sessions(session.user_id)
        assert len(sessions) == 1
        assert sessions[0].id == session.id

    def test_concurrent_session_limit(self, svc, user):
        sessions = []
        for _ in range(MAX_CONCURRENT_SESSIONS + 1):
            s = svc.login(
                email="alice@acme.com", password="SecurePass123!", tenant_id="t1"
            )
            if s:
                sessions.append(s)
        # Should have at most MAX active
        active = svc.get_user_sessions(user.id)
        assert len(active) <= MAX_CONCURRENT_SESSIONS


# =========================================
# MFA
# =========================================


class TestMFA:
    def test_enable_mfa(self, svc, user):
        secret = svc.enable_mfa(user.id)
        assert secret is not None
        assert svc.get_user(user.id).mfa_enabled is True

    def test_disable_mfa(self, svc, user):
        svc.enable_mfa(user.id)
        assert svc.disable_mfa(user.id) is True
        assert svc.get_user(user.id).mfa_enabled is False

    def test_verify_mfa(self, svc, user):
        secret = svc.enable_mfa(user.id)
        # Generate expected code for current period
        period = int(time.time()) // 30
        code = svc._generate_totp(secret, period)
        assert svc.verify_mfa(user.id, code) is True

    def test_verify_mfa_wrong_code(self, svc, user):
        svc.enable_mfa(user.id)
        assert svc.verify_mfa(user.id, "000000") is False

    def test_verify_mfa_not_enabled(self, svc, user):
        assert svc.verify_mfa(user.id, "123456") is False


# =========================================
# SSO
# =========================================


class TestSSO:
    def test_configure_sso(self, svc):
        config = SSOConfig(
            tenant_id="t1",
            provider=AuthProvider.SAML,
            entity_id="https://idp.example.com",
            sso_url="https://idp.example.com/sso",
        )
        result = svc.configure_sso(config)
        assert result.tenant_id == "t1"

    def test_get_sso_config(self, svc):
        config = SSOConfig(tenant_id="t1", provider=AuthProvider.SAML)
        svc.configure_sso(config)
        found = svc.get_sso_config("t1")
        assert found is not None
        assert found.provider == AuthProvider.SAML

    def test_remove_sso_config(self, svc):
        svc.configure_sso(SSOConfig(tenant_id="t1", provider=AuthProvider.SAML))
        assert svc.remove_sso_config("t1") is True
        assert svc.get_sso_config("t1") is None

    def test_sso_login(self, svc):
        svc.configure_sso(
            SSOConfig(
                tenant_id="t1",
                provider=AuthProvider.SAML,
                enabled=True,
            )
        )
        sess = svc.login_sso(
            tenant_id="t1",
            sso_subject_id="ext-123",
            email="sso_user@acme.com",
            display_name="SSO User",
        )
        assert sess is not None
        assert sess.tenant_id == "t1"

    def test_sso_login_no_config(self, svc):
        sess = svc.login_sso(tenant_id="t1", sso_subject_id="x", email="x@x.com")
        assert sess is None

    def test_sso_auto_provisions_user(self, svc):
        svc.configure_sso(
            SSOConfig(tenant_id="t1", provider=AuthProvider.OIDC, enabled=True)
        )
        svc.login_sso(tenant_id="t1", sso_subject_id="new-user", email="new@acme.com")
        users = svc.list_users("t1")
        assert len(users) == 1
        assert users[0].email == "new@acme.com"


# =========================================
# AUDIT LOG
# =========================================


class TestAuditLog:
    def test_login_creates_audit(self, svc, user):
        svc.login(email="alice@acme.com", password="SecurePass123!", tenant_id="t1")
        entries = svc.get_audit_log("t1")
        # Should have user_created + login events
        event_types = [e.event_type for e in entries]
        assert AuthEventType.LOGIN in event_types

    def test_audit_log_filter_user(self, svc, user):
        svc.login(email="alice@acme.com", password="SecurePass123!", tenant_id="t1")
        entries = svc.get_audit_log("t1", user_id=user.id)
        assert all(e.user_id == user.id for e in entries)

    def test_audit_log_filter_event(self, svc, user):
        svc.login(email="alice@acme.com", password="SecurePass123!", tenant_id="t1")
        entries = svc.get_audit_log("t1", event_type=AuthEventType.LOGIN)
        assert all(e.event_type == AuthEventType.LOGIN for e in entries)

    def test_audit_stats(self, svc, user):
        svc.login(email="alice@acme.com", password="SecurePass123!", tenant_id="t1")
        stats = svc.get_audit_stats("t1")
        assert stats["total_events"] > 0
        assert "event_counts" in stats


# =========================================
# SINGLETON
# =========================================


class TestSingleton:
    def test_get_service(self):
        s = get_auth_service()
        assert isinstance(s, AuthService)

    def test_singleton(self):
        s1 = get_auth_service()
        s2 = get_auth_service()
        assert s1 is s2
