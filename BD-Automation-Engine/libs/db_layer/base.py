"""
Base declarative model, session factory, and reusable mixins.

Extracted from Engine8_Knowledge/db/models.py and session.py so that
any engine (or future microservice) can reuse the same patterns
without coupling to Engine8's concrete schema.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator, Optional

import structlog
from sqlalchemy import DateTime, Boolean, create_engine, event, func, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Shared declarative base for all BD models."""

    pass


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    """Adds ``is_deleted`` and ``deleted_at`` columns for soft-delete support."""

    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None
    )

    def soft_delete(self) -> None:
        """Mark the record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Undo a soft-delete."""
        self.is_deleted = False
        self.deleted_at = None


# ---------------------------------------------------------------------------
# Session manager
# ---------------------------------------------------------------------------


class SessionManager:
    """Manages a SQLAlchemy engine and session factory.

    Supports both SQLite (dev/default) and PostgreSQL (production).

    Parameters
    ----------
    database_url:
        SQLAlchemy connection string. Falls back to ``DATABASE_URL`` env var,
        then to an in-memory SQLite database.
    schema:
        Optional PostgreSQL schema name.  When using SQLite the schema is
        automatically mapped to ``None`` via ``schema_translate_map``.
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> None:
        self._url = database_url or os.getenv("DATABASE_URL", "sqlite:///:memory:")
        self._schema = schema
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    @property
    def is_sqlite(self) -> bool:
        return self._url.startswith("sqlite")

    def get_engine(self) -> Engine:
        """Return the singleton engine, creating it on first call."""
        if self._engine is not None:
            return self._engine

        if self.is_sqlite:
            self._engine = create_engine(
                self._url,
                connect_args={"check_same_thread": False},
                echo=False,
            )

            if self._schema:
                self._engine = self._engine.execution_options(
                    schema_translate_map={self._schema: None}
                )

            @event.listens_for(self._engine, "connect")
            def _set_sqlite_pragmas(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.close()

            logger.info("database.engine_created", backend="sqlite", url=self._url)
        else:
            self._engine = create_engine(
                self._url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False,
            )
            logger.info("database.engine_created", backend="postgresql")

        return self._engine

    def session_factory(self) -> sessionmaker:
        """Return the singleton session factory."""
        if self._session_factory is not None:
            return self._session_factory

        engine = self.get_engine()
        self._session_factory = sessionmaker(
            bind=engine, autoflush=False, expire_on_commit=False
        )
        return self._session_factory

    def create_session(self) -> Session:
        """Create a new database session."""
        factory = self.session_factory()
        return factory()

    @contextmanager
    def get_db(self) -> Generator[Session, None, None]:
        """Context manager that yields a session with commit/rollback handling."""
        session = self.create_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_all_tables(self, base: type = None) -> None:
        """Create all ORM tables.

        Parameters
        ----------
        base:
            The declarative base whose metadata to create. Defaults to
            this module's ``Base``.
        """
        target_base = base or Base
        engine = self.get_engine()

        if not self.is_sqlite and self._schema:
            with engine.connect() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self._schema}"))
                conn.commit()

        target_base.metadata.create_all(bind=engine)
        logger.info("database.tables_created")

    def reset(self) -> None:
        """Dispose the engine and clear singletons (for tests)."""
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None
        self._session_factory = None
