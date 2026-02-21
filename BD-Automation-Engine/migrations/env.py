"""
Alembic environment configuration for BD Automation Engine migrations.

Reads ``DATABASE_URL`` from the environment (or ``.env`` file) and targets
the ``bd`` schema on PostgreSQL.  Falls back to SQLite for local development.
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool, text

# Ensure project root is on sys.path so we can import our models
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from Engine8_Knowledge.db.models import BD_SCHEMA, Base  # noqa: E402

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env")

# Alembic Config object (provides access to alembic.ini values)
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLAlchemy MetaData for autogenerate support
target_metadata = Base.metadata


def _get_url() -> str:
    """Resolve the database URL."""
    url = os.getenv("DATABASE_URL", "")
    if url:
        return url
    sqlite_path = PROJECT_ROOT / "Engine8_Knowledge" / "data" / "bd_engine.db"
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{sqlite_path}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without connecting)."""
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema=BD_SCHEMA if "postgresql" in url else None,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to the database)."""
    url = _get_url()
    is_pg = "postgresql" in url

    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        # Create the bd schema on PostgreSQL if it does not exist
        if is_pg:
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {BD_SCHEMA}"))
            connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=BD_SCHEMA if is_pg else None,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
