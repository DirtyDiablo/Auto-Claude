"""Phase 37A — Authentication & RBAC."""

from src.auth.rbac import (
    Role,
    Permission,
    Action,
    Resource,
    Scope,
    RBACManager,
    has_permission,
    get_rbac_manager,
)
from src.auth.auth_service import (
    AuthService,
    User,
    Session,
    AuditEntry,
    get_auth_service,
)

__all__ = [
    "Role", "Permission", "Action", "Resource", "Scope",
    "RBACManager", "has_permission", "get_rbac_manager",
    "AuthService", "User", "Session", "AuditEntry", "get_auth_service",
]
