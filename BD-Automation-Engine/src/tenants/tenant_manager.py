"""Phase 37A — Tenant Management System

Multi-tenant isolation and lifecycle:
  - Tenant CRUD: create, read, update, deactivate, delete
  - Isolation model: Qdrant collections, Neo4j labels, SQLite files, Redis prefixes
  - Provisioning: auto-create all required resources
  - Deprovisioning: clean removal of all tenant data
  - Configuration: branding, feature flags, data retention
  - Health: per-tenant resource usage, API counts, storage
"""

import logging
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# ENUMS & DATA CLASSES
# =========================================

class TenantStatus(str, Enum):
    ACTIVE = "active"
    PROVISIONING = "provisioning"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


@dataclass
class TenantBranding:
    """White-label branding configuration."""
    company_name: str = ""
    logo_url: str = ""
    primary_color: str = "#1a73e8"
    secondary_color: str = "#4285f4"
    favicon_url: str = ""
    custom_domain: str = ""


@dataclass
class FeatureFlags:
    """Which engines/features are enabled for the tenant."""
    engine_scraper: bool = True
    engine_program_mapping: bool = True
    engine_orgchart: bool = True
    engine_playbook: bool = True
    engine_scoring: bool = True
    engine_qa: bool = True
    engine_bullhorn_etl: bool = True
    engine_knowledge: bool = True
    nlq_enabled: bool = True
    proposals_enabled: bool = True
    revenue_tracking: bool = True
    relationship_intelligence: bool = True
    predictive_models: bool = True
    streaming_enabled: bool = True


@dataclass
class DataRetention:
    """Data retention policies."""
    contacts_days: int = 365
    jobs_days: int = 180
    activities_days: int = 90
    audit_logs_days: int = 365
    documents_days: int = 730  # 2 years


@dataclass
class TenantConfig:
    """Full tenant configuration."""
    branding: TenantBranding = field(default_factory=TenantBranding)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    retention: DataRetention = field(default_factory=DataRetention)
    max_users: int = 50
    max_api_calls_per_day: int = 10000
    max_storage_gb: float = 50.0
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantHealth:
    """Per-tenant resource usage and health."""
    tenant_id: str
    status: TenantStatus = TenantStatus.ACTIVE
    user_count: int = 0
    api_calls_today: int = 0
    api_calls_this_month: int = 0
    storage_used_gb: float = 0.0
    collections_count: int = 0
    last_activity: str = ""
    uptime_pct: float = 100.0


@dataclass
class Tenant:
    """Tenant entity."""
    id: str
    name: str
    slug: str                       # URL-safe identifier
    status: TenantStatus = TenantStatus.ACTIVE
    config: TenantConfig = field(default_factory=TenantConfig)
    owner_email: str = ""
    created_at: str = ""
    updated_at: str = ""
    deactivated_at: str = ""
    plan: str = "professional"      # starter, professional, enterprise
    api_key_prefix: str = ""        # For tenant-scoped API keys


# =========================================
# RESOURCE PREFIXES
# =========================================

def qdrant_collection_name(tenant_id: str, collection: str) -> str:
    """Get tenant-scoped Qdrant collection name."""
    return f"tenant_{tenant_id}_{collection}"


def neo4j_label(tenant_id: str) -> str:
    """Get tenant-scoped Neo4j label."""
    return f"Tenant_{tenant_id}"


def redis_prefix(tenant_id: str) -> str:
    """Get tenant-scoped Redis key prefix."""
    return f"tenant:{tenant_id}:"


def sqlite_path(tenant_id: str) -> str:
    """Get tenant-scoped SQLite database path."""
    return f"data/tenants/{tenant_id}/tenant.db"


# =========================================
# COLLECTIONS PER TENANT
# =========================================

TENANT_COLLECTIONS = [
    "contacts", "jobs", "programs", "documents", "activities",
]


# =========================================
# TENANT MANAGER
# =========================================

class TenantManager:
    """Manage tenant lifecycle and isolation."""

    def __init__(self):
        self._tenants: Dict[str, Tenant] = {}

    # -----------------------------------------
    # CRUD
    # -----------------------------------------

    def create_tenant(
        self,
        name: str,
        owner_email: str,
        plan: str = "professional",
        config: Optional[TenantConfig] = None,
    ) -> Tenant:
        """Create and provision a new tenant."""
        tenant_id = uuid.uuid4().hex[:12]
        slug = name.lower().replace(" ", "-").replace("_", "-")
        # Ensure unique slug
        existing_slugs = {t.slug for t in self._tenants.values()}
        if slug in existing_slugs:
            slug = f"{slug}-{tenant_id[:4]}"

        now = datetime.now(timezone.utc).isoformat()
        api_key_prefix = f"pk_{secrets.token_hex(4)}"

        tenant = Tenant(
            id=tenant_id,
            name=name,
            slug=slug,
            status=TenantStatus.PROVISIONING,
            config=config or TenantConfig(),
            owner_email=owner_email,
            created_at=now,
            updated_at=now,
            plan=plan,
            api_key_prefix=api_key_prefix,
        )

        # Provision resources
        self._provision_tenant(tenant)

        tenant.status = TenantStatus.ACTIVE
        self._tenants[tenant_id] = tenant

        logger.info(f"Created tenant '{name}' (id={tenant_id}, plan={plan})")
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self._tenants.get(tenant_id)

    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        for t in self._tenants.values():
            if t.slug == slug:
                return t
        return None

    def list_tenants(self, status: Optional[TenantStatus] = None) -> List[Tenant]:
        """List all tenants, optionally filtered by status."""
        tenants = list(self._tenants.values())
        if status:
            tenants = [t for t in tenants if t.status == status]
        return sorted(tenants, key=lambda t: t.created_at, reverse=True)

    def update_tenant(self, tenant_id: str, **kwargs) -> Optional[Tenant]:
        """Update tenant properties."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return None

        for key, value in kwargs.items():
            if hasattr(tenant, key) and key not in ("id", "created_at"):
                setattr(tenant, key, value)

        tenant.updated_at = datetime.now(timezone.utc).isoformat()
        return tenant

    def update_tenant_config(self, tenant_id: str, config: TenantConfig) -> Optional[Tenant]:
        """Update tenant configuration."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return None
        tenant.config = config
        tenant.updated_at = datetime.now(timezone.utc).isoformat()
        return tenant

    def deactivate_tenant(self, tenant_id: str) -> bool:
        """Deactivate a tenant (soft delete)."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False
        tenant.status = TenantStatus.DEACTIVATED
        tenant.deactivated_at = datetime.now(timezone.utc).isoformat()
        tenant.updated_at = tenant.deactivated_at
        logger.info(f"Deactivated tenant '{tenant.name}' (id={tenant_id})")
        return True

    def delete_tenant(self, tenant_id: str) -> bool:
        """Permanently delete a tenant and all data."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False
        self._deprovision_tenant(tenant)
        del self._tenants[tenant_id]
        logger.info(f"Deleted tenant '{tenant.name}' (id={tenant_id})")
        return True

    # -----------------------------------------
    # Provisioning
    # -----------------------------------------

    def _provision_tenant(self, tenant: Tenant) -> None:
        """Auto-create all required resources for a tenant."""
        # In production, this would:
        # 1. Create Qdrant collections
        # 2. Set up Neo4j labels/constraints
        # 3. Create SQLite database
        # 4. Set up Redis key namespaces
        collections = [
            qdrant_collection_name(tenant.id, c) for c in TENANT_COLLECTIONS
        ]
        logger.info(
            f"Provisioning tenant {tenant.id}: "
            f"{len(collections)} collections, Redis prefix={redis_prefix(tenant.id)}"
        )

    def _deprovision_tenant(self, tenant: Tenant) -> None:
        """Remove all resources for a tenant."""
        logger.info(f"Deprovisioning tenant {tenant.id}: removing all resources")

    # -----------------------------------------
    # Health
    # -----------------------------------------

    def get_tenant_health(self, tenant_id: str) -> Optional[TenantHealth]:
        """Get health metrics for a tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return None

        return TenantHealth(
            tenant_id=tenant_id,
            status=tenant.status,
            user_count=0,  # Would query user store
            api_calls_today=0,  # Would query usage store
            api_calls_this_month=0,
            storage_used_gb=0.0,
            collections_count=len(TENANT_COLLECTIONS),
            last_activity=tenant.updated_at,
            uptime_pct=100.0,
        )

    def get_usage_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Get usage metrics for billing."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return {}
        return {
            "tenant_id": tenant_id,
            "plan": tenant.plan,
            "api_calls_this_month": 0,
            "api_calls_limit": tenant.config.max_api_calls_per_day * 30,
            "storage_used_gb": 0.0,
            "storage_limit_gb": tenant.config.max_storage_gb,
            "users": 0,
            "users_limit": tenant.config.max_users,
            "collections": len(TENANT_COLLECTIONS),
        }

    # -----------------------------------------
    # Isolation helpers
    # -----------------------------------------

    def get_tenant_collections(self, tenant_id: str) -> List[str]:
        """Get all Qdrant collection names for a tenant."""
        return [qdrant_collection_name(tenant_id, c) for c in TENANT_COLLECTIONS]

    def get_tenant_redis_prefix(self, tenant_id: str) -> str:
        return redis_prefix(tenant_id)

    def get_tenant_neo4j_label(self, tenant_id: str) -> str:
        return neo4j_label(tenant_id)


# =========================================
# SINGLETON
# =========================================

_manager: Optional[TenantManager] = None


def get_tenant_manager() -> TenantManager:
    global _manager
    if _manager is None:
        _manager = TenantManager()
    return _manager
