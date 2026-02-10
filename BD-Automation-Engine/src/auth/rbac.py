"""Phase 37A — Role-Based Access Control

Enterprise RBAC:
  - Role hierarchy: TENANT_ADMIN → BD_DIRECTOR → BD_MANAGER → BD_ANALYST → VIEWER
  - Permission model: Resource × Action × Scope
  - API key management per user/service
  - Permission checking utilities
"""

import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set

logger = logging.getLogger(__name__)


# =========================================
# ENUMS
# =========================================

class Role(str, Enum):
    SUPER_ADMIN = "super_admin"         # Cross-tenant admin (platform operator)
    TENANT_ADMIN = "tenant_admin"       # Full tenant access
    BD_DIRECTOR = "bd_director"         # All BD features, reporting
    BD_MANAGER = "bd_manager"           # Contact/campaign management
    BD_ANALYST = "bd_analyst"           # Read-only intelligence
    VIEWER = "viewer"                   # Dashboard-only
    API_SERVICE = "api_service"         # Machine-to-machine


class Resource(str, Enum):
    CONTACTS = "contacts"
    JOBS = "jobs"
    PROGRAMS = "programs"
    CAMPAIGNS = "campaigns"
    PROPOSALS = "proposals"
    REVENUE = "revenue"
    RELATIONSHIPS = "relationships"
    ANALYTICS = "analytics"
    USERS = "users"
    TENANTS = "tenants"
    API_KEYS = "api_keys"
    SETTINGS = "settings"
    AUDIT_LOG = "audit_log"


class Action(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    ADMIN = "admin"


class Scope(str, Enum):
    OWN = "own"                     # Only own records
    TEAM = "team"                   # Team records
    TENANT = "tenant"               # All tenant records


# =========================================
# PERMISSION
# =========================================

@dataclass(frozen=True)
class Permission:
    """A single permission grant."""
    resource: Resource
    action: Action
    scope: Scope = Scope.TENANT


# =========================================
# ROLE DEFINITIONS
# =========================================

# Define permissions per role
_ALL_RESOURCES = list(Resource)
_BD_RESOURCES = [
    Resource.CONTACTS, Resource.JOBS, Resource.PROGRAMS,
    Resource.CAMPAIGNS, Resource.PROPOSALS, Resource.RELATIONSHIPS,
    Resource.ANALYTICS,
]
_READ_ACTIONS = [Action.READ]
_CRUD_ACTIONS = [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE]
_FULL_ACTIONS = [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT, Action.ADMIN]


def _build_permissions(resources: List[Resource], actions: List[Action], scope: Scope) -> FrozenSet[Permission]:
    return frozenset(
        Permission(resource=r, action=a, scope=scope)
        for r in resources for a in actions
    )


ROLE_PERMISSIONS: Dict[Role, FrozenSet[Permission]] = {
    Role.SUPER_ADMIN: _build_permissions(_ALL_RESOURCES, _FULL_ACTIONS, Scope.TENANT),

    Role.TENANT_ADMIN: _build_permissions(_ALL_RESOURCES, _FULL_ACTIONS, Scope.TENANT),

    Role.BD_DIRECTOR: (
        _build_permissions(_BD_RESOURCES, _FULL_ACTIONS, Scope.TENANT)
        | _build_permissions([Resource.REVENUE], [Action.READ, Action.EXPORT], Scope.TENANT)
        | _build_permissions([Resource.USERS], _READ_ACTIONS, Scope.TENANT)
    ),

    Role.BD_MANAGER: (
        _build_permissions(
            [Resource.CONTACTS, Resource.CAMPAIGNS, Resource.PROPOSALS],
            _CRUD_ACTIONS, Scope.TENANT,
        )
        | _build_permissions(
            [Resource.JOBS, Resource.PROGRAMS, Resource.RELATIONSHIPS, Resource.ANALYTICS],
            _READ_ACTIONS + [Action.EXPORT], Scope.TENANT,
        )
    ),

    Role.BD_ANALYST: _build_permissions(
        _BD_RESOURCES, [Action.READ], Scope.TENANT,
    ),

    Role.VIEWER: _build_permissions(
        [Resource.ANALYTICS, Resource.PROGRAMS], [Action.READ], Scope.TENANT,
    ),

    Role.API_SERVICE: _build_permissions(
        _BD_RESOURCES + [Resource.REVENUE], [Action.READ, Action.CREATE], Scope.TENANT,
    ),
}

# Role hierarchy (higher index = more privilege)
ROLE_HIERARCHY = [
    Role.VIEWER,
    Role.BD_ANALYST,
    Role.BD_MANAGER,
    Role.BD_DIRECTOR,
    Role.TENANT_ADMIN,
    Role.SUPER_ADMIN,
]


# =========================================
# API KEY
# =========================================

@dataclass
class APIKey:
    """API key for service or user authentication."""
    id: str
    tenant_id: str
    name: str
    key_hash: str               # Hashed version of the key
    key_prefix: str             # First 8 chars for identification
    role: Role = Role.API_SERVICE
    created_by: str = ""
    created_at: str = ""
    last_used: str = ""
    active: bool = True


# =========================================
# RBAC MANAGER
# =========================================

class RBACManager:
    """Manage roles, permissions, and API keys."""

    def __init__(self):
        self._api_keys: Dict[str, APIKey] = {}
        self._user_roles: Dict[str, Dict[str, Role]] = {}  # tenant_id -> {user_id -> role}

    # -----------------------------------------
    # Permission checking
    # -----------------------------------------

    def check_permission(
        self, role: Role, resource: Resource, action: Action, scope: Scope = Scope.TENANT,
    ) -> bool:
        """Check if a role has a specific permission."""
        required = Permission(resource=resource, action=action, scope=scope)
        role_perms = ROLE_PERMISSIONS.get(role, frozenset())

        # Direct match
        if required in role_perms:
            return True

        # Check if role has broader scope
        if scope == Scope.OWN:
            team_perm = Permission(resource=resource, action=action, scope=Scope.TEAM)
            tenant_perm = Permission(resource=resource, action=action, scope=Scope.TENANT)
            if team_perm in role_perms or tenant_perm in role_perms:
                return True
        elif scope == Scope.TEAM:
            tenant_perm = Permission(resource=resource, action=action, scope=Scope.TENANT)
            if tenant_perm in role_perms:
                return True

        return False

    def get_role_permissions(self, role: Role) -> List[Dict[str, str]]:
        """Get all permissions for a role."""
        perms = ROLE_PERMISSIONS.get(role, frozenset())
        return [
            {"resource": p.resource.value, "action": p.action.value, "scope": p.scope.value}
            for p in sorted(perms, key=lambda p: (p.resource.value, p.action.value))
        ]

    def is_role_at_least(self, user_role: Role, minimum_role: Role) -> bool:
        """Check if user_role is at least as privileged as minimum_role."""
        try:
            user_idx = ROLE_HIERARCHY.index(user_role)
            min_idx = ROLE_HIERARCHY.index(minimum_role)
            return user_idx >= min_idx
        except ValueError:
            return False

    # -----------------------------------------
    # User role management
    # -----------------------------------------

    def assign_role(self, tenant_id: str, user_id: str, role: Role) -> None:
        """Assign a role to a user within a tenant."""
        if tenant_id not in self._user_roles:
            self._user_roles[tenant_id] = {}
        self._user_roles[tenant_id][user_id] = role

    def get_user_role(self, tenant_id: str, user_id: str) -> Optional[Role]:
        """Get user's role in a tenant."""
        return self._user_roles.get(tenant_id, {}).get(user_id)

    def remove_user_role(self, tenant_id: str, user_id: str) -> bool:
        """Remove a user's role assignment."""
        if tenant_id in self._user_roles and user_id in self._user_roles[tenant_id]:
            del self._user_roles[tenant_id][user_id]
            return True
        return False

    def list_tenant_users(self, tenant_id: str) -> List[Dict[str, str]]:
        """List all user-role assignments for a tenant."""
        users = self._user_roles.get(tenant_id, {})
        return [
            {"user_id": uid, "role": role.value}
            for uid, role in users.items()
        ]

    # -----------------------------------------
    # API key management
    # -----------------------------------------

    def create_api_key(
        self, tenant_id: str, name: str, role: Role = Role.API_SERVICE, created_by: str = "",
    ) -> tuple:
        """Create a new API key. Returns (APIKey, raw_key)."""
        raw_key = f"bdapi_{secrets.token_hex(24)}"
        key_prefix = raw_key[:12]
        key_id = uuid.uuid4().hex[:12] if hasattr(uuid, 'uuid4') else secrets.token_hex(6)

        # In production, hash the key with bcrypt
        import hashlib
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = APIKey(
            id=key_id,
            tenant_id=tenant_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            role=role,
            created_by=created_by,
            created_at=datetime.now(timezone.utc).isoformat(),
            active=True,
        )
        self._api_keys[key_id] = api_key
        return api_key, raw_key

    def validate_api_key(self, raw_key: str) -> Optional[APIKey]:
        """Validate an API key and return the key record."""
        import hashlib
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        for api_key in self._api_keys.values():
            if api_key.key_hash == key_hash and api_key.active:
                api_key.last_used = datetime.now(timezone.utc).isoformat()
                return api_key
        return None

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        key = self._api_keys.get(key_id)
        if key:
            key.active = False
            return True
        return False

    def list_api_keys(self, tenant_id: str) -> List[APIKey]:
        """List all API keys for a tenant."""
        return [k for k in self._api_keys.values() if k.tenant_id == tenant_id]


# =========================================
# CONVENIENCE
# =========================================

import uuid


def has_permission(role: Role, resource: Resource, action: Action) -> bool:
    """Quick permission check."""
    mgr = get_rbac_manager()
    return mgr.check_permission(role, resource, action)


# =========================================
# SINGLETON
# =========================================

_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    global _manager
    if _manager is None:
        _manager = RBACManager()
    return _manager
