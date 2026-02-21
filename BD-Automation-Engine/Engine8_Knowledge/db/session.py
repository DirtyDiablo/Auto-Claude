"""
Database session factory for BD Automation Engine.

Supports both SQLite (dev/default) and PostgreSQL (production) via the
``DATABASE_URL`` environment variable.

Usage::

    from Engine8_Knowledge.db.session import get_db

    # FastAPI dependency injection
    @router.get("/items")
    def list_items(db: Session = Depends(get_db)):
        ...

    # Standalone script
    with get_db() as db:
        ...
"""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import structlog
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from Engine8_Knowledge.db.models import BD_SCHEMA, Base

logger = structlog.get_logger(__name__)

_DEFAULT_SQLITE_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "bd_engine.db"
)

_engine: Engine | None = None
_session_factory: sessionmaker | None = None


def _build_database_url() -> str:
    """Resolve the database URL from environment or fall back to SQLite."""
    url = os.getenv("DATABASE_URL", "")
    if url:
        return url
    sqlite_path = _DEFAULT_SQLITE_PATH
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{sqlite_path}"


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def get_engine() -> Engine:
    """Return the singleton engine, creating it on first call."""
    global _engine
    if _engine is not None:
        return _engine

    url = _build_database_url()
    is_sqlite = _is_sqlite(url)

    if is_sqlite:
        _engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False,
        ).execution_options(schema_translate_map={BD_SCHEMA: None})

        # Enable WAL mode and foreign keys for SQLite
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragmas(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

        logger.info("database.engine_created", backend="sqlite", path=url)
    else:
        _engine = create_engine(
            url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False,
        )
        logger.info("database.engine_created", backend="postgresql")

    return _engine


def _get_session_factory() -> sessionmaker:
    """Return the singleton session factory."""
    global _session_factory
    if _session_factory is not None:
        return _session_factory

    engine = get_engine()
    _session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return _session_factory


def SessionLocal() -> Session:
    """Create a new database session."""
    factory = _get_session_factory()
    return factory()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager that yields a session and handles commit/rollback.

    Can also be used as a FastAPI ``Depends`` callable via::

        def get_db_dep():
            with get_db() as session:
                yield session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all_tables() -> None:
    """Create all ORM tables. Used by migration scripts and tests.

    On PostgreSQL this creates the ``bd`` schema first.
    On SQLite the schema prefix is ignored.
    """
    engine = get_engine()
    url = str(engine.url)

    if not _is_sqlite(url):
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {BD_SCHEMA}"))
            conn.commit()

    Base.metadata.create_all(bind=engine)
    logger.info("database.tables_created")


def reset_engine() -> None:
    """Dispose the current engine and clear singletons.

    Primarily used in tests to switch between in-memory databases.
    """
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
