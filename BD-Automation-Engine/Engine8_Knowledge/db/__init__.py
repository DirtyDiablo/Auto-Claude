"""
Database package for BD Automation Engine.

Provides SQLAlchemy ORM models, session management, and repository pattern
for dual SQLite/PostgreSQL support during migration.
"""

from Engine8_Knowledge.db.models import (
    Base,
    Activity,
    Candidate,
    Company,
    Contact,
    Contract,
    Document,
    EtlRun,
    FederalContract,
    Intelligence,
    Job,
    JobPrimeMapping,
    JobProgramMapping,
    PastPerformance,
    Placement,
    PrimeContractor,
    Program,
    ProgramCompany,
    ProgramContact,
    QaReviewQueue,
    Scoring,
    SourceTracking,
    SyncState,
    Timeline,
)
from Engine8_Knowledge.db.session import get_db, get_engine, SessionLocal

__all__ = [
    "Base",
    "Activity",
    "Candidate",
    "Company",
    "Contact",
    "Contract",
    "Document",
    "EtlRun",
    "FederalContract",
    "Intelligence",
    "Job",
    "JobPrimeMapping",
    "JobProgramMapping",
    "PastPerformance",
    "Placement",
    "PrimeContractor",
    "Program",
    "ProgramCompany",
    "ProgramContact",
    "QaReviewQueue",
    "Scoring",
    "SourceTracking",
    "SyncState",
    "Timeline",
    "get_db",
    "get_engine",
    "SessionLocal",
]
