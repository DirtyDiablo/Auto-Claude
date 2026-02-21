"""
Comprehensive tests for the shared library packages:
  - libs/shared_core  (config, logging, models, exceptions, constants)
  - libs/db_layer     (base, repository, mixins)
  - libs/bullhorn_client (client, models)

Run with:
    python -m pytest tests/test_shared_libs.py -v --tb=short
"""

import os
import sys
from pathlib import Path
from datetime import datetime

import pytest

# Ensure the project root is on sys.path so that ``libs.*`` is importable.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =========================================================================
# 1. SHARED CORE — EXCEPTIONS
# =========================================================================


class TestExceptions:
    """Exception hierarchy: isinstance and message propagation."""

    def test_bd_error_is_exception(self):
        from libs.shared_core.exceptions import BDError
        assert issubclass(BDError, Exception)

    def test_config_error_is_bd_error(self):
        from libs.shared_core.exceptions import BDError, ConfigError
        assert issubclass(ConfigError, BDError)

    def test_auth_error_is_bd_error(self):
        from libs.shared_core.exceptions import AuthError, BDError
        assert issubclass(AuthError, BDError)

    def test_data_error_is_bd_error(self):
        from libs.shared_core.exceptions import BDError, DataError
        assert issubclass(DataError, BDError)

    def test_external_service_error_is_bd_error(self):
        from libs.shared_core.exceptions import BDError, ExternalServiceError
        assert issubclass(ExternalServiceError, BDError)

    def test_not_found_error_is_bd_error(self):
        from libs.shared_core.exceptions import BDError, NotFoundError
        assert issubclass(NotFoundError, BDError)

    def test_exception_message_propagation(self):
        from libs.shared_core.exceptions import ConfigError
        err = ConfigError("missing key")
        assert str(err) == "missing key"

    def test_catch_bd_error_catches_subclasses(self):
        from libs.shared_core.exceptions import BDError, AuthError, DataError

        for exc_cls in (AuthError, DataError):
            with pytest.raises(BDError):
                raise exc_cls("test")


# =========================================================================
# 2. SHARED CORE — CONSTANTS
# =========================================================================


class TestConstants:
    """Validate constant values and structure."""

    def test_clearance_levels_is_list(self):
        from libs.shared_core.constants import CLEARANCE_LEVELS
        assert isinstance(CLEARANCE_LEVELS, list)
        assert len(CLEARANCE_LEVELS) == 7

    def test_clearance_levels_ts_sci_first(self):
        from libs.shared_core.constants import CLEARANCE_LEVELS
        assert CLEARANCE_LEVELS[0] == "TS/SCI CI Poly"

    def test_contact_tiers_dict(self):
        from libs.shared_core.constants import CONTACT_TIERS
        assert isinstance(CONTACT_TIERS, dict)
        assert CONTACT_TIERS[1] == "Executive"
        assert CONTACT_TIERS[6] == "Unknown"

    def test_score_tiers(self):
        from libs.shared_core.constants import SCORE_TIERS
        assert SCORE_TIERS["hot"] == 80
        assert SCORE_TIERS["warm"] == 50
        assert SCORE_TIERS["cold"] == 0

    def test_qdrant_collections(self):
        from libs.shared_core.constants import QDRANT_COLLECTIONS
        assert "contacts" in QDRANT_COLLECTIONS
        assert "programs" in QDRANT_COLLECTIONS
        assert len(QDRANT_COLLECTIONS) == 5

    def test_confidence_thresholds(self):
        from libs.shared_core.constants import CONFIDENCE_THRESHOLDS
        assert CONFIDENCE_THRESHOLDS["high"] == 0.70

    def test_engine_names(self):
        from libs.shared_core.constants import ENGINE_NAMES
        assert ENGINE_NAMES[1] == "Scraper"
        assert ENGINE_NAMES[8] == "Knowledge"

    def test_default_candidate_fields(self):
        from libs.shared_core.constants import DEFAULT_CANDIDATE_FIELDS
        assert "id" in DEFAULT_CANDIDATE_FIELDS
        assert "firstName" in DEFAULT_CANDIDATE_FIELDS


# =========================================================================
# 3. SHARED CORE — CONFIG
# =========================================================================


class TestBDConfig:
    """BDConfig loading, get, require, property accessors.

    We pass ``env_file="/dev/null"`` (a no-op path) to prevent BDConfig
    from re-loading the real ``.env`` file, which would overwrite the
    values set by ``monkeypatch``.
    """

    _NO_ENV = "/dev/null"  # empty file; won't add any env vars

    def test_get_returns_env_value(self, monkeypatch):
        monkeypatch.setenv("TEST_KEY_123", "hello")
        from libs.shared_core.config import BDConfig
        cfg = BDConfig(env_file=self._NO_ENV)
        assert cfg.get("TEST_KEY_123") == "hello"

    def test_get_returns_default_when_unset(self):
        from libs.shared_core.config import BDConfig
        cfg = BDConfig(env_file=self._NO_ENV)
        # Use a key that is guaranteed not to exist
        assert cfg.get("UNLIKELY_KEY_XYZZY_42", "fallback") == "fallback"

    def test_get_returns_none_when_unset_no_default(self):
        from libs.shared_core.config import BDConfig
        cfg = BDConfig(env_file=self._NO_ENV)
        assert cfg.get("UNLIKELY_KEY_XYZZY_42") is None

    def test_require_raises_on_missing(self):
        from libs.shared_core.config import BDConfig
        from libs.shared_core.exceptions import ConfigError
        cfg = BDConfig(env_file=self._NO_ENV)
        with pytest.raises(ConfigError, match="MISSING_KEY_999"):
            cfg.require("MISSING_KEY_999")

    def test_require_returns_value(self, monkeypatch):
        monkeypatch.setenv("REQUIRE_TEST", "present")
        from libs.shared_core.config import BDConfig
        cfg = BDConfig(env_file=self._NO_ENV)
        assert cfg.require("REQUIRE_TEST") == "present"

    def test_anthropic_api_key_property(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        from libs.shared_core.config import BDConfig
        cfg = BDConfig(env_file=self._NO_ENV)
        assert cfg.anthropic_api_key == "sk-test"

    def test_openai_api_key_property(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
        from libs.shared_core.config import BDConfig
        cfg = BDConfig(env_file=self._NO_ENV)
        assert cfg.openai_api_key == "sk-openai-test"

    def test_qdrant_url_default(self, monkeypatch):
        monkeypatch.delenv("QDRANT_URL", raising=False)
        from libs.shared_core.config import BDConfig
        cfg = BDConfig(env_file=self._NO_ENV)
        assert cfg.qdrant_url == "http://localhost:6333"

    def test_hot_threshold_default(self, monkeypatch):
        monkeypatch.delenv("BD_TIER_HOT_MIN", raising=False)
        from libs.shared_core.config import BDConfig
        cfg = BDConfig(env_file=self._NO_ENV)
        assert cfg.hot_threshold == 80

    def test_warm_threshold_custom(self, monkeypatch):
        monkeypatch.setenv("BD_TIER_WARM_MIN", "60")
        from libs.shared_core.config import BDConfig
        cfg = BDConfig(env_file=self._NO_ENV)
        assert cfg.warm_threshold == 60

    def test_database_url_none_when_unset(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        from libs.shared_core.config import BDConfig
        cfg = BDConfig(env_file=self._NO_ENV)
        assert cfg.database_url is None

    def test_log_level_default(self, monkeypatch):
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        from libs.shared_core.config import BDConfig
        cfg = BDConfig(env_file=self._NO_ENV)
        assert cfg.log_level == "INFO"

    def test_bullhorn_api_url_default(self, monkeypatch):
        monkeypatch.delenv("BULLHORN_API_URL", raising=False)
        from libs.shared_core.config import BDConfig
        cfg = BDConfig(env_file=self._NO_ENV)
        assert cfg.bullhorn_api_url == "https://rest.bullhornstaffing.com"

    def test_notion_token_property(self, monkeypatch):
        monkeypatch.setenv("NOTION_TOKEN", "secret_abc")
        from libs.shared_core.config import BDConfig
        cfg = BDConfig(env_file=self._NO_ENV)
        assert cfg.notion_token == "secret_abc"

    def test_default_env_file_loading(self):
        """BDConfig() with no args should not raise."""
        from libs.shared_core.config import BDConfig
        cfg = BDConfig()
        # Just verify it instantiates without error
        assert cfg is not None


# =========================================================================
# 4. SHARED CORE — LOGGING
# =========================================================================


class TestLogging:
    """configure_logging and get_logger."""

    def test_configure_logging_does_not_raise(self):
        from libs.shared_core.logging import configure_logging
        configure_logging(level="WARNING")

    def test_configure_logging_json(self):
        from libs.shared_core.logging import configure_logging
        configure_logging(level="INFO", json_output=True)

    def test_get_logger_returns_bound_logger(self):
        from libs.shared_core.logging import get_logger
        logger = get_logger("test_module")
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")

    def test_logger_can_log(self):
        from libs.shared_core.logging import get_logger
        logger = get_logger("test_log_call")
        # Should not raise
        logger.info("test.event", key="value")


# =========================================================================
# 5. SHARED CORE — MODELS
# =========================================================================


class TestSearchResult:
    """SearchResult Pydantic model."""

    def test_valid_construction(self):
        from libs.shared_core.models import SearchResult
        sr = SearchResult(
            id="abc", content="hello", score=0.95, collection="contacts"
        )
        assert sr.id == "abc"
        assert sr.score == 0.95

    def test_metadata_defaults_to_empty(self):
        from libs.shared_core.models import SearchResult
        sr = SearchResult(id="1", content="x", score=0.5, collection="c")
        assert sr.metadata == {}

    def test_metadata_custom(self):
        from libs.shared_core.models import SearchResult
        sr = SearchResult(
            id="1", content="x", score=0.5, collection="c",
            metadata={"tier": 1},
        )
        assert sr.metadata["tier"] == 1

    def test_serialization_roundtrip(self):
        from libs.shared_core.models import SearchResult
        sr = SearchResult(id="1", content="x", score=0.5, collection="c")
        data = sr.model_dump()
        sr2 = SearchResult(**data)
        assert sr == sr2


class TestPaginatedResponse:
    """PaginatedResponse Pydantic model."""

    def test_direct_construction(self):
        from libs.shared_core.models import PaginatedResponse
        pr = PaginatedResponse(
            items=["a", "b"], total=10, page=1, page_size=2, has_more=True
        )
        assert pr.total == 10
        assert pr.has_more is True

    def test_build_factory_computes_has_more_true(self):
        from libs.shared_core.models import PaginatedResponse
        pr = PaginatedResponse.build(items=["a"], total=5, page=1, page_size=2)
        assert pr.has_more is True

    def test_build_factory_computes_has_more_false(self):
        from libs.shared_core.models import PaginatedResponse
        pr = PaginatedResponse.build(items=["a"], total=2, page=1, page_size=2)
        assert pr.has_more is False

    def test_empty_items(self):
        from libs.shared_core.models import PaginatedResponse
        pr = PaginatedResponse.build(items=[], total=0, page=1, page_size=10)
        assert pr.has_more is False
        assert pr.items == []


class TestStatusResponse:
    """StatusResponse Pydantic model."""

    def test_auto_timestamp(self):
        from libs.shared_core.models import StatusResponse
        sr = StatusResponse(status="ok", message="all good")
        assert sr.timestamp  # should be a non-empty ISO string

    def test_details_default_empty(self):
        from libs.shared_core.models import StatusResponse
        sr = StatusResponse(status="ok", message="m")
        assert sr.details == {}

    def test_details_custom(self):
        from libs.shared_core.models import StatusResponse
        sr = StatusResponse(status="ok", message="m", details={"count": 42})
        assert sr.details["count"] == 42


class TestErrorResponse:
    """ErrorResponse Pydantic model."""

    def test_construction(self):
        from libs.shared_core.models import ErrorResponse
        er = ErrorResponse(error="NotFound", detail="No such item", status_code=404)
        assert er.status_code == 404
        assert er.error == "NotFound"

    def test_serialization(self):
        from libs.shared_core.models import ErrorResponse
        er = ErrorResponse(error="E", detail="D", status_code=500)
        data = er.model_dump()
        assert data["status_code"] == 500


# =========================================================================
# 6. SHARED CORE — PACKAGE IMPORTS
# =========================================================================


class TestSharedCorePackage:
    """Verify top-level re-exports from libs.shared_core."""

    def test_import_bdconfig(self):
        from libs.shared_core import BDConfig
        assert BDConfig is not None

    def test_import_exceptions(self):
        from libs.shared_core import (
            BDError, ConfigError, AuthError,
            DataError, ExternalServiceError, NotFoundError,
        )
        assert all(issubclass(e, BDError) for e in [
            ConfigError, AuthError, DataError, ExternalServiceError, NotFoundError
        ])

    def test_import_models(self):
        from libs.shared_core import (
            SearchResult, PaginatedResponse, StatusResponse, ErrorResponse,
        )
        assert SearchResult is not None

    def test_version(self):
        from libs.shared_core import __version__
        assert __version__ == "0.1.0"


# =========================================================================
# 7. DB LAYER — BASE & MIXINS
# =========================================================================


class TestDBBase:
    """Base model and mixins."""

    def test_base_is_declarative(self):
        from libs.db_layer.base import Base
        assert hasattr(Base, "metadata")

    def test_timestamp_mixin_has_columns(self):
        from libs.db_layer.base import TimestampMixin
        assert hasattr(TimestampMixin, "created_at")
        assert hasattr(TimestampMixin, "updated_at")

    def test_soft_delete_mixin_has_columns(self):
        from libs.db_layer.base import SoftDeleteMixin
        assert hasattr(SoftDeleteMixin, "is_deleted")
        assert hasattr(SoftDeleteMixin, "deleted_at")

    def test_soft_delete_mixin_methods(self):
        from libs.db_layer.base import SoftDeleteMixin
        assert callable(getattr(SoftDeleteMixin, "soft_delete", None))
        assert callable(getattr(SoftDeleteMixin, "restore", None))

    def test_mixins_reexport_from_mixins_module(self):
        from libs.db_layer.mixins import TimestampMixin, SoftDeleteMixin
        assert TimestampMixin is not None
        assert SoftDeleteMixin is not None


# =========================================================================
# 8. DB LAYER — SESSION MANAGER
# =========================================================================


class TestSessionManager:
    """SessionManager with in-memory SQLite."""

    def test_default_is_sqlite(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        from libs.db_layer.base import SessionManager
        mgr = SessionManager()
        assert mgr.is_sqlite is True

    def test_custom_url(self):
        from libs.db_layer.base import SessionManager
        mgr = SessionManager(database_url="sqlite:///test.db")
        assert mgr.is_sqlite is True

    def test_postgres_url_not_sqlite(self):
        from libs.db_layer.base import SessionManager
        mgr = SessionManager(
            database_url="postgresql://user:pw@localhost/db"
        )
        assert mgr.is_sqlite is False

    def test_get_engine_returns_engine(self):
        from libs.db_layer.base import SessionManager
        mgr = SessionManager(database_url="sqlite:///:memory:")
        engine = mgr.get_engine()
        assert engine is not None
        mgr.reset()

    def test_create_session(self):
        from libs.db_layer.base import SessionManager
        mgr = SessionManager(database_url="sqlite:///:memory:")
        session = mgr.create_session()
        assert session is not None
        session.close()
        mgr.reset()

    def test_get_db_context_manager(self):
        from libs.db_layer.base import SessionManager
        mgr = SessionManager(database_url="sqlite:///:memory:")
        with mgr.get_db() as session:
            assert session is not None
        mgr.reset()

    def test_reset_clears_engine(self):
        from libs.db_layer.base import SessionManager
        mgr = SessionManager(database_url="sqlite:///:memory:")
        mgr.get_engine()
        mgr.reset()
        assert mgr._engine is None
        assert mgr._session_factory is None


# =========================================================================
# 9. DB LAYER — REPOSITORY CRUD (in-memory SQLite)
# =========================================================================


# We need a concrete model for repository tests
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column


def _make_test_model():
    """Create a test model class bound to the db_layer Base."""
    from libs.db_layer.base import Base, TimestampMixin, SoftDeleteMixin

    class Item(TimestampMixin, SoftDeleteMixin, Base):
        __tablename__ = "test_items"
        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        name: Mapped[str] = mapped_column(String(100), nullable=False)

    return Item


# Build the model once at module level (but after imports)
_Item = _make_test_model()


@pytest.fixture
def db_session():
    """Yield a session with test_items table created in memory."""
    from libs.db_layer.base import SessionManager

    mgr = SessionManager(database_url="sqlite:///:memory:")
    _Item.metadata.create_all(bind=mgr.get_engine())
    session = mgr.create_session()
    yield session
    session.close()
    mgr.reset()


@pytest.fixture
def item_repo(db_session):
    """Repository for the test Item model."""
    from libs.db_layer.repository import BaseRepository

    class ItemRepository(BaseRepository):
        model = _Item

    return ItemRepository(db_session)


class TestBaseRepository:
    """CRUD operations on an in-memory SQLite database."""

    def test_create(self, item_repo):
        entity = _Item(name="Widget")
        result = item_repo.create(entity)
        assert result.id is not None
        assert result.name == "Widget"

    def test_get_by_id(self, item_repo):
        entity = _Item(name="Gadget")
        item_repo.create(entity)
        fetched = item_repo.get_by_id(entity.id)
        assert fetched is not None
        assert fetched.name == "Gadget"

    def test_get_by_id_not_found(self, item_repo):
        assert item_repo.get_by_id(9999) is None

    def test_list_all(self, item_repo):
        item_repo.create(_Item(name="A"))
        item_repo.create(_Item(name="B"))
        items = item_repo.list_all()
        assert len(items) == 2

    def test_list_all_pagination(self, item_repo):
        for i in range(5):
            item_repo.create(_Item(name=f"Item-{i}"))
        page = item_repo.list_all(offset=2, limit=2)
        assert len(page) == 2

    def test_count(self, item_repo):
        assert item_repo.count() == 0
        item_repo.create(_Item(name="X"))
        assert item_repo.count() == 1

    def test_update(self, item_repo):
        entity = _Item(name="Old")
        item_repo.create(entity)
        item_repo.update(entity, name="New")
        assert entity.name == "New"

    def test_update_ignores_nonexistent_attr(self, item_repo):
        entity = _Item(name="A")
        item_repo.create(entity)
        item_repo.update(entity, nonexistent="val")
        assert entity.name == "A"

    def test_delete(self, item_repo):
        entity = _Item(name="ToDelete")
        item_repo.create(entity)
        assert item_repo.count() == 1
        item_repo.delete(entity)
        assert item_repo.count() == 0

    def test_create_many(self, item_repo):
        entities = [_Item(name=f"Bulk-{i}") for i in range(3)]
        results = item_repo.create_many(entities)
        assert len(results) == 3
        assert item_repo.count() == 3

    def test_soft_delete(self, item_repo):
        entity = _Item(name="SoftDel")
        item_repo.create(entity)
        item_repo.soft_delete(entity)
        assert entity.is_deleted is True
        assert entity.deleted_at is not None

    def test_restore(self, item_repo):
        entity = _Item(name="Restore")
        item_repo.create(entity)
        item_repo.soft_delete(entity)
        item_repo.restore(entity)
        assert entity.is_deleted is False
        assert entity.deleted_at is None

    def test_soft_delete_raises_on_model_without_mixin(self, db_session):
        """Soft-delete should fail on a model without SoftDeleteMixin."""
        from libs.db_layer.base import Base as DBBase
        from libs.db_layer.repository import BaseRepository

        class PlainItem(DBBase):
            __tablename__ = "plain_items"
            id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
            name: Mapped[str] = mapped_column(String(50), nullable=False)

        PlainItem.metadata.create_all(bind=db_session.get_bind())

        class PlainRepo(BaseRepository):
            model = PlainItem

        repo = PlainRepo(db_session)
        entity = PlainItem(name="NoMixin")
        repo.create(entity)
        with pytest.raises(TypeError, match="does not support soft-delete"):
            repo.soft_delete(entity)


# =========================================================================
# 10. DB LAYER — PACKAGE IMPORTS
# =========================================================================


class TestDBLayerPackage:
    """Verify top-level re-exports from libs.db_layer."""

    def test_import_base(self):
        from libs.db_layer import Base
        assert Base is not None

    def test_import_session_manager(self):
        from libs.db_layer import SessionManager
        assert SessionManager is not None

    def test_import_base_repository(self):
        from libs.db_layer import BaseRepository
        assert BaseRepository is not None

    def test_version(self):
        from libs.db_layer import __version__
        assert __version__ == "0.1.0"


# =========================================================================
# 11. BULLHORN CLIENT — CONFIG
# =========================================================================


class TestBullhornConfig:
    """BullhornConfig dataclass and env loading."""

    def test_defaults_from_env(self, monkeypatch):
        monkeypatch.setenv("BULLHORN_CLIENT_ID", "test-id")
        monkeypatch.setenv("BULLHORN_CLIENT_SECRET", "test-secret")
        from libs.bullhorn_client.client import BullhornConfig
        cfg = BullhornConfig()
        assert cfg.client_id == "test-id"
        assert cfg.client_secret == "test-secret"

    def test_explicit_values_override_env(self, monkeypatch):
        monkeypatch.setenv("BULLHORN_CLIENT_ID", "env-id")
        from libs.bullhorn_client.client import BullhornConfig
        cfg = BullhornConfig(client_id="explicit-id")
        assert cfg.client_id == "explicit-id"

    def test_default_api_url(self, monkeypatch):
        monkeypatch.delenv("BULLHORN_API_URL", raising=False)
        from libs.bullhorn_client.client import BullhornConfig
        cfg = BullhornConfig()
        assert "bullhornstaffing.com" in cfg.api_url


# =========================================================================
# 12. BULLHORN CLIENT — MOCK CLIENT
# =========================================================================


class TestMockBullhornClient:
    """MockBullhornClient in-memory operations."""

    def test_authenticate(self):
        from libs.bullhorn_client.client import MockBullhornClient
        client = MockBullhornClient()
        assert client.authenticate() is True

    def test_create_candidate(self):
        from libs.bullhorn_client.client import MockBullhornClient
        client = MockBullhornClient()
        cid = client.create_candidate({"firstName": "John", "lastName": "Doe"})
        assert cid == 1

    def test_search_candidates_returns_created(self):
        from libs.bullhorn_client.client import MockBullhornClient
        client = MockBullhornClient()
        client.create_candidate({"firstName": "Jane"})
        results = client.search_candidates("Jane")
        assert len(results) == 1

    def test_get_candidate(self):
        from libs.bullhorn_client.client import MockBullhornClient
        client = MockBullhornClient()
        c = client.get_candidate(42)
        assert c["id"] == 42

    def test_enrich_contact(self):
        from libs.bullhorn_client.client import MockBullhornClient
        client = MockBullhornClient()
        enriched = client.enrich_contact_from_bullhorn({"name": "Test"})
        assert enriched["_mock_enrichment"] is True

    def test_sync_contact(self):
        from libs.bullhorn_client.client import MockBullhornClient
        client = MockBullhornClient()
        cid = client.sync_contact_to_bullhorn({"name": "Test User"})
        assert cid == 1

    def test_search_job_orders_empty(self):
        from libs.bullhorn_client.client import MockBullhornClient
        client = MockBullhornClient()
        assert client.search_job_orders("query") == []

    def test_create_job_order(self):
        from libs.bullhorn_client.client import MockBullhornClient
        client = MockBullhornClient()
        assert client.create_job_order({"title": "Analyst"}) == 1

    def test_update_candidate(self):
        from libs.bullhorn_client.client import MockBullhornClient
        client = MockBullhornClient()
        assert client.update_candidate(1, {"status": "Inactive"}) is True


# =========================================================================
# 13. BULLHORN CLIENT — FACTORY
# =========================================================================


class TestGetBullhornClient:
    """get_bullhorn_client factory function."""

    def test_returns_mock_when_use_mock(self):
        from libs.bullhorn_client.client import MockBullhornClient, get_bullhorn_client
        client = get_bullhorn_client(use_mock=True)
        assert isinstance(client, MockBullhornClient)

    def test_returns_mock_when_no_credentials(self, monkeypatch):
        monkeypatch.delenv("BULLHORN_CLIENT_ID", raising=False)
        monkeypatch.delenv("BULLHORN_CLIENT_SECRET", raising=False)
        from libs.bullhorn_client.client import MockBullhornClient, get_bullhorn_client
        client = get_bullhorn_client()
        assert isinstance(client, MockBullhornClient)


# =========================================================================
# 14. BULLHORN CLIENT — MODELS
# =========================================================================


class TestBullhornModels:
    """Pydantic models for Bullhorn entities."""

    def test_candidate_defaults(self):
        from libs.bullhorn_client.models import BullhornCandidate
        c = BullhornCandidate()
        assert c.status == "Active"
        assert c.firstName == ""

    def test_candidate_custom(self):
        from libs.bullhorn_client.models import BullhornCandidate
        c = BullhornCandidate(firstName="John", lastName="Doe", email="j@d.com")
        assert c.email == "j@d.com"

    def test_contact_to_bullhorn_format(self):
        from libs.bullhorn_client.models import BullhornContact
        contact = BullhornContact(
            name="John Doe", email="j@d.com", company="GDIT", program="DCGS"
        )
        fmt = contact.to_bullhorn_format()
        assert fmt["firstName"] == "John"
        assert fmt["lastName"] == "Doe"
        assert fmt["customText1"] == "DCGS"
        assert fmt["customText3"] == "BD-Automation"

    def test_contact_to_bullhorn_format_uses_first_last(self):
        from libs.bullhorn_client.models import BullhornContact
        contact = BullhornContact(first_name="Jane", last_name="Smith")
        fmt = contact.to_bullhorn_format()
        assert fmt["firstName"] == "Jane"

    def test_job_order_defaults(self):
        from libs.bullhorn_client.models import BullhornJobOrder
        jo = BullhornJobOrder()
        assert jo.status == "Open"
        assert jo.employmentType == "Contract"

    def test_job_order_custom(self):
        from libs.bullhorn_client.models import BullhornJobOrder
        jo = BullhornJobOrder(title="DCGS Analyst", status="Closed")
        assert jo.title == "DCGS Analyst"
        assert jo.status == "Closed"


# =========================================================================
# 15. BULLHORN CLIENT — PACKAGE IMPORTS
# =========================================================================


class TestBullhornClientPackage:
    """Verify top-level re-exports from libs.bullhorn_client."""

    def test_import_client(self):
        from libs.bullhorn_client import BullhornClient
        assert BullhornClient is not None

    def test_import_config(self):
        from libs.bullhorn_client import BullhornConfig
        assert BullhornConfig is not None

    def test_import_mock(self):
        from libs.bullhorn_client import MockBullhornClient
        assert MockBullhornClient is not None

    def test_import_factory(self):
        from libs.bullhorn_client import get_bullhorn_client
        assert callable(get_bullhorn_client)

    def test_import_models(self):
        from libs.bullhorn_client import (
            BullhornCandidate, BullhornContact, BullhornJobOrder,
        )
        assert BullhornCandidate is not None

    def test_version(self):
        from libs.bullhorn_client import __version__
        assert __version__ == "0.1.0"


# =========================================================================
# 16. BULLHORN CLIENT — LIVE CLIENT INIT (no network calls)
# =========================================================================


class TestBullhornClientInit:
    """BullhornClient initialisation (no actual API calls)."""

    def test_init_default_config(self):
        from libs.bullhorn_client.client import BullhornClient
        client = BullhornClient()
        assert client._authenticated is False
        assert client._token_expiry is None

    def test_init_custom_config(self):
        from libs.bullhorn_client.client import BullhornClient, BullhornConfig
        cfg = BullhornConfig(client_id="abc", client_secret="xyz")
        client = BullhornClient(config=cfg)
        assert client.config.client_id == "abc"

    def test_authenticate_fails_without_credentials(self):
        from libs.bullhorn_client.client import BullhornClient, BullhornConfig
        cfg = BullhornConfig(client_id="", client_secret="")
        client = BullhornClient(config=cfg)
        assert client.authenticate() is False

    def test_contact_to_bullhorn_format_static(self):
        from libs.bullhorn_client.client import BullhornClient
        fmt = BullhornClient._contact_to_bullhorn_format(
            {"name": "Alice Wonderland", "email": "a@w.com"}
        )
        assert fmt["firstName"] == "Alice"
        assert fmt["lastName"] == "Wonderland"
        assert fmt["email"] == "a@w.com"
