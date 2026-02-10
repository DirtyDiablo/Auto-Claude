"""Tests for Phase 37A — Tenant Manager."""

import pytest

from src.tenants.tenant_manager import (
    TenantManager,
    Tenant,
    TenantConfig,
    TenantHealth,
    TenantStatus,
    TenantBranding,
    FeatureFlags,
    DataRetention,
    qdrant_collection_name,
    neo4j_label,
    redis_prefix,
    sqlite_path,
    TENANT_COLLECTIONS,
    get_tenant_manager,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def mgr():
    return TenantManager()


@pytest.fixture
def tenant(mgr):
    return mgr.create_tenant(
        name="Acme Corp",
        owner_email="admin@acme.com",
        plan="enterprise",
    )


# =========================================
# ISOLATION HELPERS
# =========================================

class TestIsolationHelpers:
    def test_qdrant_collection_name(self):
        result = qdrant_collection_name("t1", "contacts")
        assert result == "tenant_t1_contacts"

    def test_neo4j_label(self):
        assert neo4j_label("t1") == "Tenant_t1"

    def test_redis_prefix(self):
        assert redis_prefix("t1") == "tenant:t1:"

    def test_sqlite_path(self):
        assert sqlite_path("t1") == "data/tenants/t1/tenant.db"


# =========================================
# TENANT CRUD
# =========================================

class TestTenantCRUD:
    def test_create_tenant(self, mgr):
        t = mgr.create_tenant(name="Test Corp", owner_email="a@b.com")
        assert isinstance(t, Tenant)
        assert t.name == "Test Corp"
        assert t.status == TenantStatus.ACTIVE
        assert t.slug == "test-corp"

    def test_create_sets_plan(self, mgr):
        t = mgr.create_tenant(name="X", owner_email="x@x.com", plan="starter")
        assert t.plan == "starter"

    def test_create_sets_timestamps(self, mgr):
        t = mgr.create_tenant(name="T", owner_email="t@t.com")
        assert t.created_at != ""
        assert t.updated_at != ""

    def test_create_unique_slug(self, mgr):
        t1 = mgr.create_tenant(name="Same Name", owner_email="a@b.com")
        t2 = mgr.create_tenant(name="Same Name", owner_email="c@d.com")
        assert t1.slug != t2.slug

    def test_get_tenant(self, mgr, tenant):
        found = mgr.get_tenant(tenant.id)
        assert found is not None
        assert found.name == "Acme Corp"

    def test_get_tenant_not_found(self, mgr):
        assert mgr.get_tenant("nonexistent") is None

    def test_get_tenant_by_slug(self, mgr, tenant):
        found = mgr.get_tenant_by_slug(tenant.slug)
        assert found is not None
        assert found.id == tenant.id

    def test_list_tenants(self, mgr):
        mgr.create_tenant(name="A", owner_email="a@a.com")
        mgr.create_tenant(name="B", owner_email="b@b.com")
        tenants = mgr.list_tenants()
        assert len(tenants) == 2

    def test_list_tenants_filter_status(self, mgr):
        t1 = mgr.create_tenant(name="A", owner_email="a@a.com")
        mgr.create_tenant(name="B", owner_email="b@b.com")
        mgr.deactivate_tenant(t1.id)
        active = mgr.list_tenants(status=TenantStatus.ACTIVE)
        assert len(active) == 1

    def test_update_tenant(self, mgr, tenant):
        updated = mgr.update_tenant(tenant.id, name="New Name", plan="starter")
        assert updated.name == "New Name"
        assert updated.plan == "starter"

    def test_update_tenant_not_found(self, mgr):
        assert mgr.update_tenant("x", name="Y") is None

    def test_update_tenant_config(self, mgr, tenant):
        config = TenantConfig(max_users=100)
        updated = mgr.update_tenant_config(tenant.id, config)
        assert updated.config.max_users == 100

    def test_deactivate_tenant(self, mgr, tenant):
        success = mgr.deactivate_tenant(tenant.id)
        assert success is True
        assert mgr.get_tenant(tenant.id).status == TenantStatus.DEACTIVATED

    def test_deactivate_sets_timestamp(self, mgr, tenant):
        mgr.deactivate_tenant(tenant.id)
        assert mgr.get_tenant(tenant.id).deactivated_at != ""

    def test_delete_tenant(self, mgr, tenant):
        success = mgr.delete_tenant(tenant.id)
        assert success is True
        assert mgr.get_tenant(tenant.id) is None

    def test_delete_nonexistent(self, mgr):
        assert mgr.delete_tenant("x") is False


# =========================================
# HEALTH & USAGE
# =========================================

class TestTenantHealth:
    def test_get_health(self, mgr, tenant):
        health = mgr.get_tenant_health(tenant.id)
        assert isinstance(health, TenantHealth)
        assert health.tenant_id == tenant.id
        assert health.status == TenantStatus.ACTIVE

    def test_health_not_found(self, mgr):
        assert mgr.get_tenant_health("x") is None

    def test_get_usage_metrics(self, mgr, tenant):
        metrics = mgr.get_usage_metrics(tenant.id)
        assert metrics["tenant_id"] == tenant.id
        assert metrics["plan"] == "enterprise"
        assert "storage_limit_gb" in metrics

    def test_usage_not_found(self, mgr):
        assert mgr.get_usage_metrics("x") == {}


# =========================================
# COLLECTIONS
# =========================================

class TestTenantCollections:
    def test_get_collections(self, mgr, tenant):
        collections = mgr.get_tenant_collections(tenant.id)
        assert len(collections) == len(TENANT_COLLECTIONS)
        assert all(f"tenant_{tenant.id}_" in c for c in collections)

    def test_redis_prefix(self, mgr, tenant):
        prefix = mgr.get_tenant_redis_prefix(tenant.id)
        assert prefix == f"tenant:{tenant.id}:"

    def test_neo4j_label(self, mgr, tenant):
        label = mgr.get_tenant_neo4j_label(tenant.id)
        assert label == f"Tenant_{tenant.id}"


# =========================================
# DATA CLASSES
# =========================================

class TestDataClasses:
    def test_branding_defaults(self):
        b = TenantBranding()
        assert b.primary_color == "#1a73e8"

    def test_feature_flags_defaults(self):
        f = FeatureFlags()
        assert f.engine_scraper is True
        assert f.nlq_enabled is True

    def test_data_retention_defaults(self):
        r = DataRetention()
        assert r.contacts_days == 365
        assert r.documents_days == 730

    def test_config_defaults(self):
        c = TenantConfig()
        assert c.max_users == 50
        assert c.max_api_calls_per_day == 10000


# =========================================
# SINGLETON
# =========================================

class TestSingleton:
    def test_get_manager(self):
        m = get_tenant_manager()
        assert isinstance(m, TenantManager)

    def test_singleton(self):
        m1 = get_tenant_manager()
        m2 = get_tenant_manager()
        assert m1 is m2
