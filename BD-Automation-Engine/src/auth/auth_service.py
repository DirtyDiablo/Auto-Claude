"""Phase 37A — Authentication & Session Service

Enterprise authentication:
  - JWT token-based authentication
  - Local auth: email + password with bcrypt-style hashing
  - SSO integration: SAML 2.0, OAuth 2.0 / OIDC stubs
  - Session management: token refresh, revocation, concurrent session limits
  - MFA: TOTP-based two-factor authentication
  - Audit logging: all auth events with IP, user agent, action
"""

import hashlib
import hmac
import logging
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from src.auth.rbac import Role, get_rbac_manager

logger = logging.getLogger(__name__)


# =========================================
# CONSTANTS
# =========================================

TOKEN_EXPIRY_HOURS = 24
REFRESH_TOKEN_EXPIRY_DAYS = 30
MAX_CONCURRENT_SESSIONS = 5
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 30
TOTP_WINDOW = 1  # Allow +/- 1 period


# =========================================
# ENUMS
# =========================================


class AuthProvider(str, Enum):
    LOCAL = "local"
    SAML = "saml"
    OAUTH2 = "oauth2"
    OIDC = "oidc"


class AuthEventType(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REVOKED = "token_revoked"
    PASSWORD_CHANGED = "password_changed"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_VERIFIED = "mfa_verified"
    MFA_FAILED = "mfa_failed"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SESSION_EXPIRED = "session_expired"
    USER_CREATED = "user_created"
    USER_DEACTIVATED = "user_deactivated"


# =========================================
# DATA CLASSES
# =========================================


@dataclass
class User:
    """User account."""

    id: str
    email: str
    tenant_id: str
    role: Role = Role.VIEWER
    display_name: str = ""
    password_hash: str = ""
    auth_provider: AuthProvider = AuthProvider.LOCAL
    mfa_enabled: bool = False
    mfa_secret: str = ""
    active: bool = True
    created_at: str = ""
    last_login: str = ""
    failed_login_attempts: int = 0
    locked_until: str = ""
    sso_subject_id: str = ""  # External IdP subject ID


@dataclass
class Session:
    """Active session / token record."""

    id: str
    user_id: str
    tenant_id: str
    access_token: str
    refresh_token: str
    created_at: str
    expires_at: str
    refresh_expires_at: str
    ip_address: str = ""
    user_agent: str = ""
    active: bool = True


@dataclass
class AuditEntry:
    """Authentication audit log entry."""

    id: str
    timestamp: str
    tenant_id: str
    user_id: str
    event_type: AuthEventType
    ip_address: str = ""
    user_agent: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    success: bool = True


@dataclass
class SSOConfig:
    """SSO provider configuration for a tenant."""

    tenant_id: str
    provider: AuthProvider
    entity_id: str = ""  # SAML entity ID
    sso_url: str = ""  # SAML SSO URL / OAuth authorize URL
    certificate: str = ""  # SAML IdP certificate
    client_id: str = ""  # OAuth/OIDC client ID
    client_secret: str = ""  # OAuth/OIDC client secret
    token_url: str = ""  # OAuth/OIDC token URL
    userinfo_url: str = ""  # OIDC userinfo URL
    redirect_uri: str = ""
    enabled: bool = True


# =========================================
# AUTH SERVICE
# =========================================


class AuthService:
    """Authentication, session management, and audit logging."""

    def __init__(self):
        self._users: Dict[str, User] = {}  # user_id -> User
        self._sessions: Dict[str, Session] = {}  # session_id -> Session
        self._audit_log: List[AuditEntry] = []
        self._sso_configs: Dict[str, SSOConfig] = {}  # tenant_id -> SSOConfig
        self._token_index: Dict[str, str] = {}  # access_token -> session_id

    # -----------------------------------------
    # Password hashing
    # -----------------------------------------

    @staticmethod
    def _hash_password(password: str, salt: Optional[str] = None) -> str:
        """Hash password with SHA-256 + salt (production would use bcrypt)."""
        if salt is None:
            salt = secrets.token_hex(16)
        hash_val = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
        return f"{salt}${hash_val}"

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        """Verify password against stored hash."""
        if "$" not in password_hash:
            return False
        salt, stored_hash = password_hash.split("$", 1)
        computed = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
        return hmac.compare_digest(computed, stored_hash)

    # -----------------------------------------
    # User management
    # -----------------------------------------

    def create_user(
        self,
        email: str,
        tenant_id: str,
        password: str = "",
        role: Role = Role.VIEWER,
        display_name: str = "",
        auth_provider: AuthProvider = AuthProvider.LOCAL,
        sso_subject_id: str = "",
    ) -> User:
        """Create a new user account."""
        # Check for duplicate email in tenant
        for u in self._users.values():
            if u.email == email and u.tenant_id == tenant_id:
                raise ValueError(
                    f"User with email {email} already exists in tenant {tenant_id}"
                )

        user_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc).isoformat()

        password_hash = ""
        if auth_provider == AuthProvider.LOCAL and password:
            password_hash = self._hash_password(password)

        user = User(
            id=user_id,
            email=email,
            tenant_id=tenant_id,
            role=role,
            display_name=display_name or email.split("@")[0],
            password_hash=password_hash,
            auth_provider=auth_provider,
            created_at=now,
            sso_subject_id=sso_subject_id,
        )
        self._users[user_id] = user

        # Assign role in RBAC manager
        rbac = get_rbac_manager()
        rbac.assign_role(tenant_id, user_id, role)

        self._log_event(tenant_id, user_id, AuthEventType.USER_CREATED)
        logger.info(f"Created user {email} (id={user_id}) in tenant {tenant_id}")
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self._users.get(user_id)

    def get_user_by_email(self, email: str, tenant_id: str) -> Optional[User]:
        """Get user by email within a tenant."""
        for u in self._users.values():
            if u.email == email and u.tenant_id == tenant_id:
                return u
        return None

    def list_users(self, tenant_id: str) -> List[User]:
        """List all users in a tenant."""
        return [u for u in self._users.values() if u.tenant_id == tenant_id]

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account."""
        user = self._users.get(user_id)
        if not user:
            return False
        user.active = False
        # Revoke all sessions
        self._revoke_user_sessions(user_id)
        self._log_event(user.tenant_id, user_id, AuthEventType.USER_DEACTIVATED)
        return True

    def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> bool:
        """Change user password."""
        user = self._users.get(user_id)
        if not user or user.auth_provider != AuthProvider.LOCAL:
            return False
        if not self._verify_password(old_password, user.password_hash):
            return False
        user.password_hash = self._hash_password(new_password)
        self._log_event(user.tenant_id, user_id, AuthEventType.PASSWORD_CHANGED)
        return True

    # -----------------------------------------
    # Authentication
    # -----------------------------------------

    def login(
        self,
        email: str,
        password: str,
        tenant_id: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> Optional[Session]:
        """Authenticate user and create session."""
        user = self.get_user_by_email(email, tenant_id)
        if not user:
            self._log_event(
                tenant_id,
                "",
                AuthEventType.LOGIN_FAILED,
                ip=ip_address,
                ua=user_agent,
                details={"reason": "user_not_found", "email": email},
            )
            return None

        # Check lockout
        if user.locked_until:
            lock_time = datetime.fromisoformat(user.locked_until)
            if datetime.now(timezone.utc) < lock_time:
                self._log_event(
                    tenant_id,
                    user.id,
                    AuthEventType.LOGIN_FAILED,
                    ip=ip_address,
                    ua=user_agent,
                    details={"reason": "account_locked"},
                )
                return None
            # Lockout expired — reset
            user.locked_until = ""
            user.failed_login_attempts = 0

        if not user.active:
            self._log_event(
                tenant_id,
                user.id,
                AuthEventType.LOGIN_FAILED,
                ip=ip_address,
                ua=user_agent,
                details={"reason": "account_deactivated"},
            )
            return None

        # Verify password
        if not self._verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                user.locked_until = (
                    datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
                ).isoformat()
                self._log_event(
                    tenant_id,
                    user.id,
                    AuthEventType.ACCOUNT_LOCKED,
                    ip=ip_address,
                    ua=user_agent,
                )
            self._log_event(
                tenant_id,
                user.id,
                AuthEventType.LOGIN_FAILED,
                ip=ip_address,
                ua=user_agent,
                details={
                    "reason": "bad_password",
                    "attempts": user.failed_login_attempts,
                },
            )
            return None

        # Reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = ""

        # Enforce concurrent session limit
        self._enforce_session_limit(user.id)

        # Create session
        session = self._create_session(user, ip_address, user_agent)
        user.last_login = datetime.now(timezone.utc).isoformat()

        self._log_event(
            tenant_id, user.id, AuthEventType.LOGIN, ip=ip_address, ua=user_agent
        )
        return session

    def login_sso(
        self,
        tenant_id: str,
        sso_subject_id: str,
        email: str,
        display_name: str = "",
        ip_address: str = "",
        user_agent: str = "",
    ) -> Optional[Session]:
        """Authenticate via SSO (SAML/OAuth/OIDC) and create session."""
        sso_config = self._sso_configs.get(tenant_id)
        if not sso_config or not sso_config.enabled:
            return None

        # Find or create user
        user = None
        for u in self._users.values():
            if u.sso_subject_id == sso_subject_id and u.tenant_id == tenant_id:
                user = u
                break

        if not user:
            # Auto-provision SSO user
            user = self.create_user(
                email=email,
                tenant_id=tenant_id,
                role=Role.VIEWER,
                display_name=display_name,
                auth_provider=sso_config.provider,
                sso_subject_id=sso_subject_id,
            )

        if not user.active:
            return None

        self._enforce_session_limit(user.id)
        session = self._create_session(user, ip_address, user_agent)
        user.last_login = datetime.now(timezone.utc).isoformat()

        self._log_event(
            tenant_id,
            user.id,
            AuthEventType.LOGIN,
            ip=ip_address,
            ua=user_agent,
            details={"provider": sso_config.provider.value},
        )
        return session

    # -----------------------------------------
    # Token / Session management
    # -----------------------------------------

    def validate_token(self, access_token: str) -> Optional[Session]:
        """Validate an access token and return session if valid."""
        session_id = self._token_index.get(access_token)
        if not session_id:
            return None
        session = self._sessions.get(session_id)
        if not session or not session.active:
            return None

        # Check expiry
        expires = datetime.fromisoformat(session.expires_at)
        if datetime.now(timezone.utc) > expires:
            session.active = False
            self._log_event(
                session.tenant_id, session.user_id, AuthEventType.SESSION_EXPIRED
            )
            return None

        return session

    def refresh_token(self, refresh_token: str) -> Optional[Session]:
        """Refresh an access token using refresh token."""
        # Find session by refresh token
        session = None
        for s in self._sessions.values():
            if s.refresh_token == refresh_token and s.active:
                session = s
                break

        if not session:
            return None

        # Check refresh token expiry
        refresh_expires = datetime.fromisoformat(session.refresh_expires_at)
        if datetime.now(timezone.utc) > refresh_expires:
            session.active = False
            return None

        # Issue new tokens
        now = datetime.now(timezone.utc)
        new_access = f"bd_at_{secrets.token_hex(32)}"
        new_refresh = f"bd_rt_{secrets.token_hex(32)}"

        # Remove old token index
        if session.access_token in self._token_index:
            del self._token_index[session.access_token]

        session.access_token = new_access
        session.refresh_token = new_refresh
        session.expires_at = (now + timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat()
        session.refresh_expires_at = (
            now + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)
        ).isoformat()

        self._token_index[new_access] = session.id

        self._log_event(session.tenant_id, session.user_id, AuthEventType.TOKEN_REFRESH)
        return session

    def revoke_session(self, session_id: str) -> bool:
        """Revoke a specific session."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        session.active = False
        if session.access_token in self._token_index:
            del self._token_index[session.access_token]
        self._log_event(session.tenant_id, session.user_id, AuthEventType.TOKEN_REVOKED)
        return True

    def logout(self, access_token: str) -> bool:
        """Log out by revoking the session for the given token."""
        session_id = self._token_index.get(access_token)
        if not session_id:
            return False
        session = self._sessions.get(session_id)
        if session:
            session.active = False
            del self._token_index[access_token]
            self._log_event(session.tenant_id, session.user_id, AuthEventType.LOGOUT)
            return True
        return False

    def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all active sessions for a user."""
        return [s for s in self._sessions.values() if s.user_id == user_id and s.active]

    # -----------------------------------------
    # MFA (TOTP)
    # -----------------------------------------

    def enable_mfa(self, user_id: str) -> Optional[str]:
        """Enable MFA for user. Returns the TOTP secret."""
        user = self._users.get(user_id)
        if not user:
            return None
        secret = secrets.token_hex(20)
        user.mfa_secret = secret
        user.mfa_enabled = True
        self._log_event(user.tenant_id, user_id, AuthEventType.MFA_ENABLED)
        return secret

    def disable_mfa(self, user_id: str) -> bool:
        """Disable MFA for user."""
        user = self._users.get(user_id)
        if not user:
            return False
        user.mfa_enabled = False
        user.mfa_secret = ""
        self._log_event(user.tenant_id, user_id, AuthEventType.MFA_DISABLED)
        return True

    def verify_mfa(self, user_id: str, code: str) -> bool:
        """Verify a TOTP code for the user."""
        user = self._users.get(user_id)
        if not user or not user.mfa_enabled or not user.mfa_secret:
            return False

        # Simplified TOTP: hash(secret + time_period) truncated to 6 digits
        import time

        period = int(time.time()) // 30
        for offset in range(-TOTP_WINDOW, TOTP_WINDOW + 1):
            expected = self._generate_totp(user.mfa_secret, period + offset)
            if hmac.compare_digest(code, expected):
                self._log_event(user.tenant_id, user_id, AuthEventType.MFA_VERIFIED)
                return True

        self._log_event(user.tenant_id, user_id, AuthEventType.MFA_FAILED)
        return False

    @staticmethod
    def _generate_totp(secret: str, period: int) -> str:
        """Generate a 6-digit TOTP code."""
        h = hashlib.sha256(f"{secret}:{period}".encode()).hexdigest()
        return str(int(h[:8], 16) % 1000000).zfill(6)

    # -----------------------------------------
    # SSO Configuration
    # -----------------------------------------

    def configure_sso(self, config: SSOConfig) -> SSOConfig:
        """Configure SSO for a tenant."""
        self._sso_configs[config.tenant_id] = config
        return config

    def get_sso_config(self, tenant_id: str) -> Optional[SSOConfig]:
        """Get SSO configuration for a tenant."""
        return self._sso_configs.get(tenant_id)

    def remove_sso_config(self, tenant_id: str) -> bool:
        """Remove SSO configuration for a tenant."""
        if tenant_id in self._sso_configs:
            del self._sso_configs[tenant_id]
            return True
        return False

    # -----------------------------------------
    # Audit log
    # -----------------------------------------

    def get_audit_log(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        event_type: Optional[AuthEventType] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Query audit log entries."""
        entries = [e for e in self._audit_log if e.tenant_id == tenant_id]
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        return sorted(entries, key=lambda e: e.timestamp, reverse=True)[:limit]

    def get_audit_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get aggregate audit statistics for a tenant."""
        entries = [e for e in self._audit_log if e.tenant_id == tenant_id]
        event_counts: Dict[str, int] = {}
        for e in entries:
            event_counts[e.event_type.value] = (
                event_counts.get(e.event_type.value, 0) + 1
            )

        failed = sum(1 for e in entries if not e.success)
        return {
            "total_events": len(entries),
            "event_counts": event_counts,
            "failed_events": failed,
            "unique_users": len(set(e.user_id for e in entries if e.user_id)),
        }

    # -----------------------------------------
    # Internal helpers
    # -----------------------------------------

    def _create_session(self, user: User, ip_address: str, user_agent: str) -> Session:
        """Create a new session with tokens."""
        now = datetime.now(timezone.utc)
        session_id = uuid.uuid4().hex[:16]
        access_token = f"bd_at_{secrets.token_hex(32)}"
        refresh_token = f"bd_rt_{secrets.token_hex(32)}"

        session = Session(
            id=session_id,
            user_id=user.id,
            tenant_id=user.tenant_id,
            access_token=access_token,
            refresh_token=refresh_token,
            created_at=now.isoformat(),
            expires_at=(now + timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat(),
            refresh_expires_at=(
                now + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)
            ).isoformat(),
            ip_address=ip_address,
            user_agent=user_agent,
            active=True,
        )
        self._sessions[session_id] = session
        self._token_index[access_token] = session_id
        return session

    def _enforce_session_limit(self, user_id: str) -> None:
        """Enforce max concurrent sessions by revoking oldest."""
        active = sorted(
            [s for s in self._sessions.values() if s.user_id == user_id and s.active],
            key=lambda s: s.created_at,
        )
        while len(active) >= MAX_CONCURRENT_SESSIONS:
            oldest = active.pop(0)
            oldest.active = False
            if oldest.access_token in self._token_index:
                del self._token_index[oldest.access_token]

    def _revoke_user_sessions(self, user_id: str) -> None:
        """Revoke all sessions for a user."""
        for s in self._sessions.values():
            if s.user_id == user_id and s.active:
                s.active = False
                if s.access_token in self._token_index:
                    del self._token_index[s.access_token]

    def _log_event(
        self,
        tenant_id: str,
        user_id: str,
        event_type: AuthEventType,
        ip: str = "",
        ua: str = "",
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
    ) -> None:
        """Record an audit log entry."""
        entry = AuditEntry(
            id=uuid.uuid4().hex[:12],
            timestamp=datetime.now(timezone.utc).isoformat(),
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            ip_address=ip,
            user_agent=ua,
            details=details or {},
            success=success,
        )
        self._audit_log.append(entry)


# =========================================
# SINGLETON
# =========================================

_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    global _service
    if _service is None:
        _service = AuthService()
    return _service
