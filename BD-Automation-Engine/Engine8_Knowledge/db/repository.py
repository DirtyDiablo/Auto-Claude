"""
Repository pattern for BD Automation Engine database access.

Provides ``BaseRepository`` with CRUD operations and specialised repositories
for the core domain entities.  When ``DUAL_READ_ENABLED=true`` is set in the
environment, read operations query **both** SQLite and PostgreSQL, compare
results, and log discrepancies for migration verification.
"""

import os
import sqlite3
from pathlib import Path
from typing import Generic, List, Optional, Type, TypeVar

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from Engine8_Knowledge.db.models import (
    Base,
    Contact,
    Job,
    Placement,
    Program,
)

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=Base)

DUAL_READ_ENABLED = os.getenv("DUAL_READ_ENABLED", "false").lower() == "true"

# Path to the legacy Bullhorn SQLite database
_BULLHORN_DB = (
    Path(__file__).resolve().parent.parent.parent
    / "Engine7_BullhornETL"
    / "data"
    / "bullhorn_master.db"
)


# ---------------------------------------------------------------------------
# Base repository
# ---------------------------------------------------------------------------


class BaseRepository(Generic[T]):
    """Generic CRUD repository backed by a SQLAlchemy session."""

    model: Type[T]

    def __init__(self, session: Session) -> None:
        self.session = session

    # -- Create --------------------------------------------------------

    def create(self, entity: T) -> T:
        """Add a new entity and flush to obtain its id."""
        self.session.add(entity)
        self.session.flush()
        return entity

    def create_many(self, entities: List[T]) -> List[T]:
        """Bulk-add entities and flush."""
        self.session.add_all(entities)
        self.session.flush()
        return entities

    # -- Read ----------------------------------------------------------

    def get_by_id(self, entity_id) -> Optional[T]:
        """Fetch a single entity by primary key."""
        return self.session.get(self.model, entity_id)

    def list_all(self, *, offset: int = 0, limit: int = 100) -> List[T]:
        """Return a paginated list of entities."""
        stmt = select(self.model).offset(offset).limit(limit)
        return list(self.session.scalars(stmt).all())

    def count(self) -> int:
        """Return the total number of entities."""
        from sqlalchemy import func as sa_func

        stmt = select(sa_func.count()).select_from(self.model)
        return self.session.scalar(stmt) or 0

    # -- Update --------------------------------------------------------

    def update(self, entity: T, **kwargs) -> T:
        """Update an entity with keyword arguments."""
        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        self.session.flush()
        return entity

    # -- Delete --------------------------------------------------------

    def delete(self, entity: T) -> None:
        """Remove an entity from the session."""
        self.session.delete(entity)
        self.session.flush()


# ---------------------------------------------------------------------------
# Dual-read helper
# ---------------------------------------------------------------------------


def _dual_read_compare(
    table_name: str,
    pg_count: int,
    sqlite_db_path: Path,
    sqlite_table: str,
) -> None:
    """Compare record counts between PostgreSQL (via ORM) and SQLite.

    Only runs when ``DUAL_READ_ENABLED`` is true.
    """
    if not DUAL_READ_ENABLED:
        return
    if not sqlite_db_path.exists():
        logger.warning(
            "dual_read.sqlite_missing",
            table=table_name,
            path=str(sqlite_db_path),
        )
        return

    try:
        conn = sqlite3.connect(str(sqlite_db_path))
        cursor = conn.execute(f"SELECT COUNT(*) FROM {sqlite_table}")
        sqlite_count = cursor.fetchone()[0]
        conn.close()
    except sqlite3.OperationalError as exc:
        logger.warning("dual_read.sqlite_error", table=table_name, error=str(exc))
        return

    if pg_count != sqlite_count:
        logger.warning(
            "dual_read.count_mismatch",
            table=table_name,
            pg_count=pg_count,
            sqlite_count=sqlite_count,
            delta=pg_count - sqlite_count,
        )
    else:
        logger.info(
            "dual_read.counts_match",
            table=table_name,
            count=pg_count,
        )


# ---------------------------------------------------------------------------
# Specialised repositories
# ---------------------------------------------------------------------------


class ContactRepository(BaseRepository[Contact]):
    """Repository for Contact entities."""

    model = Contact

    def find_by_email(self, email: str) -> Optional[Contact]:
        """Look up a contact by email address."""
        stmt = select(Contact).where(Contact.email == email)
        return self.session.scalar(stmt)

    def find_by_company(
        self, company: str, *, limit: int = 100
    ) -> List[Contact]:
        """Return contacts at a given company."""
        stmt = (
            select(Contact)
            .where(Contact.company == company)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def find_by_tier(self, tier: int, *, limit: int = 100) -> List[Contact]:
        """Return contacts at a given tier."""
        stmt = (
            select(Contact)
            .where(Contact.tier == tier)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def count_with_dual_read(self) -> int:
        """Count contacts and optionally compare with SQLite."""
        pg_count = self.count()
        master_db = (
            Path(__file__).resolve().parent.parent.parent
            / "data"
            / "master_federal_contracts.db"
        )
        _dual_read_compare("contacts", pg_count, master_db, "contacts")
        return pg_count


class ProgramRepository(BaseRepository[Program]):
    """Repository for Program entities."""

    model = Program

    def find_by_name(self, name: str) -> Optional[Program]:
        """Look up a program by exact name."""
        stmt = select(Program).where(Program.name == name)
        return self.session.scalar(stmt)

    def find_by_agency(
        self, agency: str, *, limit: int = 100
    ) -> List[Program]:
        """Return programs for a given agency."""
        stmt = (
            select(Program)
            .where(Program.agency == agency)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def count_with_dual_read(self) -> int:
        """Count programs and optionally compare with SQLite."""
        pg_count = self.count()
        _dual_read_compare("programs", pg_count, _BULLHORN_DB, "programs")
        return pg_count


class PlacementRepository(BaseRepository[Placement]):
    """Repository for Placement entities."""

    model = Placement

    def find_by_job_id(self, job_id: int) -> List[Placement]:
        """Return all placements for a given job."""
        stmt = select(Placement).where(Placement.job_id == job_id)
        return list(self.session.scalars(stmt).all())

    def find_by_candidate_id(self, candidate_id: int) -> List[Placement]:
        """Return all placements for a given candidate."""
        stmt = select(Placement).where(Placement.candidate_id == candidate_id)
        return list(self.session.scalars(stmt).all())

    def count_with_dual_read(self) -> int:
        """Count placements and optionally compare with SQLite."""
        pg_count = self.count()
        _dual_read_compare("placements", pg_count, _BULLHORN_DB, "placements")
        return pg_count


class JobRepository(BaseRepository[Job]):
    """Repository for Job entities."""

    model = Job

    def find_by_bullhorn_id(self, bullhorn_job_id: str) -> Optional[Job]:
        """Look up a job by its Bullhorn ID."""
        stmt = select(Job).where(Job.bullhorn_job_id == bullhorn_job_id)
        return self.session.scalar(stmt)

    def find_by_status(
        self, status: str, *, limit: int = 100
    ) -> List[Job]:
        """Return jobs filtered by status."""
        stmt = (
            select(Job)
            .where(Job.status == status)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def find_by_client(
        self, client: str, *, limit: int = 100
    ) -> List[Job]:
        """Return jobs for a given client corporation."""
        stmt = (
            select(Job)
            .where(Job.client_corporation == client)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def count_with_dual_read(self) -> int:
        """Count jobs and optionally compare with SQLite."""
        pg_count = self.count()
        _dual_read_compare("jobs", pg_count, _BULLHORN_DB, "jobs")
        return pg_count
