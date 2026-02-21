"""
BD Knowledge API — Authentication & Authorization

Supports three auth modes:
1. **Dev mode** (BD_API_KEY unset) — no auth, all access
2. **API key** (X-API-Key header) — service-to-service, role embedded in key config
3. **JWT** (Authorization: Bearer) — dashboard users, role in token payload

Roles (RBAC):
- admin: full access (manage keys, users, all endpoints)
- bd_manager: read/write BD data, run pipelines, view dashboards
- bd_team: read-only access to search, contacts, programs

Rate limiting: 100 req/min per API key, 200 req/min per JWT user.
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger("bd-auth")


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------


class Role(str, Enum):
    ADMIN = "admin"
    BD_MANAGER = "bd_manager"
    BD_TEAM = "bd_team"


# Permission matrix: role -> set of allowed permission scopes
ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {
        "read", "write", "delete", "admin",
        "pipeline:run", "pipeline:config",
        "contacts:write", "contacts:delete",
        "keys:manage", "users:manage",
    },
    Role.BD_MANAGER: {
        "read", "write",
        "pipeline:run",
        "contacts:write",
    },
    Role.BD_TEAM: {
        "read",
    },
}


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------


@dataclass
class AuthUser:
    """Authenticated user context attached to each request."""
    user_id: str
    role: Role
    auth_method: str  # "api_key", "jwt", or "dev"
    permissions: set[str]

    def has_permission(self, scope: str) -> bool:
        return scope in self.permissions


# Dev-mode user (no auth configured)
DEV_USER = AuthUser(
    user_id="dev",
    role=Role.ADMIN,
    auth_method="dev",
    permissions=ROLE_PERMISSIONS[Role.ADMIN],
)


# ---------------------------------------------------------------------------
# API Key Store (file-based, production would use a database)
# ---------------------------------------------------------------------------

_KEY_STORE_PATH = Path(os.getenv(
    "BD_KEY_STORE_PATH",
    str(Path(__file__).parent.parent / ".auto-claude" / "api_keys.json"),
))


def _hash_key(key: str) -> str:
    """SHA-256 hash of an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def _load_keys() -> dict:
    """Load API key store from disk."""
    if _KEY_STORE_PATH.exists():
        return json.loads(_KEY_STORE_PATH.read_text())
    return {"keys": {}}


def _save_keys(store: dict) -> None:
    """Save API key store to disk."""
    _KEY_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _KEY_STORE_PATH.write_text(json.dumps(store, indent=2))


def create_api_key(name: str, role: str = "bd_team") -> dict:
    """Create a new API key. Returns the key (shown once) and metadata."""
    role_enum = Role(role)
    raw_key = f"bd_{secrets.token_urlsafe(32)}"
    key_hash = _hash_key(raw_key)

    store = _load_keys()
    store["keys"][key_hash] = {
        "name": name,
        "role": role,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used": None,
        "active": True,
    }
    _save_keys(store)

    return {"key": raw_key, "name": name, "role": role}


def revoke_api_key(key_hash: str) -> bool:
    """Revoke an API key by its hash."""
    store = _load_keys()
    if key_hash in store["keys"]:
        store["keys"][key_hash]["active"] = False
        _save_keys(store)
        return True
    return False


def validate_api_key(raw_key: str) -> Optional[AuthUser]:
    """Validate an API key and return an AuthUser if valid."""
    # Check legacy single-key mode first
    legacy_key = os.getenv("BD_API_KEY", "")
    if legacy_key and raw_key == legacy_key:
        return AuthUser(
            user_id="legacy_key",
            role=Role.ADMIN,
            auth_method="api_key",
            permissions=ROLE_PERMISSIONS[Role.ADMIN],
        )

    key_hash = _hash_key(raw_key)
    store = _load_keys()
    entry = store["keys"].get(key_hash)
    if not entry or not entry.get("active", True):
        return None

    role = Role(entry["role"])

    # Update last_used
    entry["last_used"] = datetime.now(timezone.utc).isoformat()
    _save_keys(store)

    return AuthUser(
        user_id=f"key:{entry['name']}",
        role=role,
        auth_method="api_key",
        permissions=ROLE_PERMISSIONS[role],
    )


# ---------------------------------------------------------------------------
# JWT (lightweight HMAC-based, no external dependency)
# ---------------------------------------------------------------------------

_JWT_SECRET = os.getenv("BD_JWT_SECRET", "")
_JWT_EXPIRY_HOURS = int(os.getenv("BD_JWT_EXPIRY_HOURS", "24"))


def _b64url_encode(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    import base64
    padding = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * padding)


def create_jwt(user_id: str, role: str) -> str:
    """Create a JWT token. Requires BD_JWT_SECRET to be set."""
    if not _JWT_SECRET:
        raise ValueError("BD_JWT_SECRET must be set to issue JWTs")

    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    now = int(time.time())
    payload_data = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + (_JWT_EXPIRY_HOURS * 3600),
    }
    payload = _b64url_encode(json.dumps(payload_data).encode())
    signature = _b64url_encode(
        hmac.new(_JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    )
    return f"{header}.{payload}.{signature}"


def validate_jwt(token: str) -> Optional[AuthUser]:
    """Validate a JWT and return an AuthUser if valid."""
    if not _JWT_SECRET:
        return None

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts

        # Verify signature
        expected_sig = _b64url_encode(
            hmac.new(
                _JWT_SECRET.encode(),
                f"{header_b64}.{payload_b64}".encode(),
                hashlib.sha256,
            ).digest()
        )
        if not hmac.compare_digest(sig_b64, expected_sig):
            return None

        # Decode payload
        payload = json.loads(_b64url_decode(payload_b64))

        # Check expiry
        if payload.get("exp", 0) < int(time.time()):
            return None

        role = Role(payload["role"])
        return AuthUser(
            user_id=payload["sub"],
            role=role,
            auth_method="jwt",
            permissions=ROLE_PERMISSIONS[role],
        )
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Rate Limiting (in-memory, per-key/user)
# ---------------------------------------------------------------------------

_rate_limits: dict[str, list[float]] = {}
_RATE_LIMIT_WINDOW = 60  # seconds
_RATE_LIMIT_API_KEY = 100  # requests per window
_RATE_LIMIT_JWT = 200


def _check_rate_limit(user_id: str, limit: int) -> bool:
    """Return True if request is allowed, False if rate-limited."""
    now = time.time()
    window_start = now - _RATE_LIMIT_WINDOW

    if user_id not in _rate_limits:
        _rate_limits[user_id] = []

    # Prune old entries
    _rate_limits[user_id] = [t for t in _rate_limits[user_id] if t > window_start]

    if len(_rate_limits[user_id]) >= limit:
        return False

    _rate_limits[user_id].append(now)
    return True


# ---------------------------------------------------------------------------
# FastAPI Dependencies
# ---------------------------------------------------------------------------

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_bearer_scheme = HTTPBearer(auto_error=False)

# Paths that never require authentication
AUTH_EXEMPT_PATHS = {"/health", "/ready", "/live", "/docs", "/openapi.json", "/redoc"}
AUTH_EXEMPT_PREFIXES = ("/docs", "/redoc")


async def get_current_user(
    request: Request,
    api_key: Optional[str] = Depends(_api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> AuthUser:
    """
    Unified auth dependency. Resolves user from API key or JWT.
    Returns DEV_USER when no auth is configured (BD_API_KEY unset and no JWT secret).
    """
    path = request.url.path

    # Exempt paths
    if path in AUTH_EXEMPT_PATHS or any(path.startswith(p) for p in AUTH_EXEMPT_PREFIXES):
        return DEV_USER

    # Dev mode — no auth configured at all
    if not os.getenv("BD_API_KEY", "") and not _JWT_SECRET:
        return DEV_USER

    # Try API key first
    if api_key:
        user = validate_api_key(api_key)
        if user:
            limit = _RATE_LIMIT_API_KEY
            if not _check_rate_limit(user.user_id, limit):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            return user
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Try JWT bearer token
    if bearer:
        user = validate_jwt(bearer.credentials)
        if user:
            limit = _RATE_LIMIT_JWT
            if not _check_rate_limit(user.user_id, limit):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            return user
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    raise HTTPException(status_code=401, detail="Authentication required")


def require_permission(scope: str):
    """Dependency factory: raises 403 if user lacks the required permission scope."""
    async def _check(user: AuthUser = Depends(get_current_user)):
        if not user.has_permission(scope):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions: requires '{scope}'",
            )
        return user
    return _check


def require_role(min_role: Role):
    """Dependency factory: raises 403 if user's role is below the minimum."""
    role_hierarchy = {Role.ADMIN: 3, Role.BD_MANAGER: 2, Role.BD_TEAM: 1}

    async def _check(user: AuthUser = Depends(get_current_user)):
        if role_hierarchy.get(user.role, 0) < role_hierarchy[min_role]:
            raise HTTPException(
                status_code=403,
                detail=f"Requires role '{min_role.value}' or higher",
            )
        return user
    return _check
