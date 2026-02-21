"""
SQLAlchemy 2.0 ORM models for the BD Automation Engine.

All tables use the ``bd`` schema prefix when running on PostgreSQL.
On SQLite the schema is ignored (flat namespace).

Models are derived from the existing SQLite schemas in:
  - Engine7_BullhornETL/scripts/database_schema.py  (Bullhorn master)
  - scripts/master_db/schema.py                      (master federal contracts)
  - services/database.py                             (pipeline persistence)
  - Engine8_Knowledge/scripts/memory_system.py       (memory layer)
  - Engine8_Knowledge/api_routers/phase7_endpoints.py (notifications)
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Shared declarative base for all BD models."""

    pass


BD_SCHEMA = "bd"


# ---------------------------------------------------------------------------
# Helper: a ``created_at`` / ``updated_at`` mixin
# ---------------------------------------------------------------------------

class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


# =========================================================================
# BULLHORN CORE ENTITIES  (from Engine7_BullhornETL/scripts/database_schema.py)
# =========================================================================


class Job(TimestampMixin, Base):
    """Bullhorn job orders."""

    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_bd_jobs_bullhorn_id", "bullhorn_job_id"),
        Index("ix_bd_jobs_client", "client_corporation"),
        Index("ix_bd_jobs_prime", "prime_contractor"),
        Index("ix_bd_jobs_status", "status"),
        Index("ix_bd_jobs_date_added", "date_added"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bullhorn_job_id: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    job_number: Mapped[Optional[str]] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    client_corporation: Mapped[Optional[str]] = mapped_column(String(200))
    prime_contractor: Mapped[Optional[str]] = mapped_column(String(200))
    employment_type: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[Optional[str]] = mapped_column(String(50))
    pay_rate: Mapped[Optional[float]] = mapped_column(Float)
    bill_rate: Mapped[Optional[float]] = mapped_column(Float)
    salary: Mapped[Optional[float]] = mapped_column(Float)
    perm_fee_percent: Mapped[Optional[int]] = mapped_column(Integer)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    clearance_required: Mapped[Optional[str]] = mapped_column(String(100))
    skills: Mapped[Optional[str]] = mapped_column(Text)
    owner: Mapped[Optional[str]] = mapped_column(String(200))
    contact: Mapped[Optional[str]] = mapped_column(String(200))
    date_added: Mapped[Optional[datetime]] = mapped_column(DateTime)
    date_modified: Mapped[Optional[datetime]] = mapped_column(DateTime)
    date_closed: Mapped[Optional[datetime]] = mapped_column(DateTime)
    custom_text1: Mapped[Optional[str]] = mapped_column(Text)
    custom_text2: Mapped[Optional[str]] = mapped_column(Text)
    custom_text3: Mapped[Optional[str]] = mapped_column(Text)
    source_file: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    placements: Mapped[list["Placement"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    activities: Mapped[list["Activity"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class Candidate(TimestampMixin, Base):
    """Bullhorn candidates / contacts."""

    __tablename__ = "candidates"
    __table_args__ = (
        Index("ix_bd_candidates_bullhorn_id", "bullhorn_candidate_id"),
        Index("ix_bd_candidates_name", "full_name"),
        Index("ix_bd_candidates_email", "email"),
        Index("ix_bd_candidates_company", "company_name"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bullhorn_candidate_id: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True
    )
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    mobile: Mapped[Optional[str]] = mapped_column(String(50))
    occupation: Mapped[Optional[str]] = mapped_column(String(200))
    job_title: Mapped[Optional[str]] = mapped_column(String(200))
    company_name: Mapped[Optional[str]] = mapped_column(String(200))
    current_employer: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[Optional[str]] = mapped_column(String(50))
    address: Mapped[Optional[str]] = mapped_column(String(500))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    zip_code: Mapped[Optional[str]] = mapped_column(String(20))
    clearance_level: Mapped[Optional[str]] = mapped_column(String(100))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    owner: Mapped[Optional[str]] = mapped_column(String(200))
    date_added: Mapped[Optional[datetime]] = mapped_column(DateTime)
    date_modified: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_activity_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    custom_text1: Mapped[Optional[str]] = mapped_column(Text)
    custom_text2: Mapped[Optional[str]] = mapped_column(Text)
    custom_text3: Mapped[Optional[str]] = mapped_column(Text)
    source_file: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    placements: Mapped[list["Placement"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    activities: Mapped[list["Activity"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )


class Placement(Base):
    """Bullhorn placements linking jobs to candidates."""

    __tablename__ = "placements"
    __table_args__ = (
        Index("ix_bd_placements_job_id", "job_id"),
        Index("ix_bd_placements_candidate_id", "candidate_id"),
        Index("ix_bd_placements_date", "placement_date"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bullhorn_placement_id: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True
    )
    job_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey(f"{BD_SCHEMA}.jobs.id")
    )
    candidate_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey(f"{BD_SCHEMA}.candidates.id")
    )
    bullhorn_job_id: Mapped[Optional[str]] = mapped_column(String(20))
    bullhorn_candidate_id: Mapped[Optional[str]] = mapped_column(String(50))
    placement_date: Mapped[Optional[date]] = mapped_column(Date)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    outcome: Mapped[Optional[str]] = mapped_column(String(100))
    pay_rate: Mapped[Optional[float]] = mapped_column(Float)
    bill_rate: Mapped[Optional[float]] = mapped_column(Float)
    salary: Mapped[Optional[float]] = mapped_column(Float)
    commission: Mapped[Optional[float]] = mapped_column(Float)
    duration_days: Mapped[Optional[int]] = mapped_column(Integer)
    client_name: Mapped[Optional[str]] = mapped_column(String(200))
    job_title: Mapped[Optional[str]] = mapped_column(String(500))
    candidate_name: Mapped[Optional[str]] = mapped_column(String(200))
    owner: Mapped[Optional[str]] = mapped_column(String(200))
    source_file: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    job: Mapped[Optional["Job"]] = relationship(back_populates="placements")
    candidate: Mapped[Optional["Candidate"]] = relationship(
        back_populates="placements"
    )


class Activity(Base):
    """Bullhorn activities / notes."""

    __tablename__ = "activities"
    __table_args__ = (
        Index("ix_bd_activities_job_id", "related_job_id"),
        Index("ix_bd_activities_candidate_id", "related_candidate_id"),
        Index("ix_bd_activities_date", "activity_date"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bullhorn_activity_id: Mapped[Optional[str]] = mapped_column(String(50))
    activity_type: Mapped[Optional[str]] = mapped_column(String(100))
    action: Mapped[Optional[str]] = mapped_column(String(200))
    related_job_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey(f"{BD_SCHEMA}.jobs.id")
    )
    related_candidate_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey(f"{BD_SCHEMA}.candidates.id")
    )
    bullhorn_job_id: Mapped[Optional[str]] = mapped_column(String(20))
    bullhorn_candidate_id: Mapped[Optional[str]] = mapped_column(String(50))
    activity_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actor: Mapped[Optional[str]] = mapped_column(String(200))
    note_text: Mapped[Optional[str]] = mapped_column(Text)
    comments: Mapped[Optional[str]] = mapped_column(Text)
    follow_up_required: Mapped[Optional[bool]] = mapped_column(Boolean)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    source_file: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    job: Mapped[Optional["Job"]] = relationship(back_populates="activities")
    candidate: Mapped[Optional["Candidate"]] = relationship(
        back_populates="activities"
    )


class PrimeContractor(TimestampMixin, Base):
    """Prime contractors we work with."""

    __tablename__ = "prime_contractors"
    __table_args__ = (
        Index("ix_bd_primes_name", "name"),
        Index("ix_bd_primes_normalized", "normalized_name"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    normalized_name: Mapped[Optional[str]] = mapped_column(String(200))
    aliases: Mapped[Optional[str]] = mapped_column(Text)
    cage_code: Mapped[Optional[str]] = mapped_column(String(20))
    duns_number: Mapped[Optional[str]] = mapped_column(String(20))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    headquarters: Mapped[Optional[str]] = mapped_column(String(200))
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)
    annual_revenue: Mapped[Optional[float]] = mapped_column(Float)
    naics_codes: Mapped[Optional[str]] = mapped_column(Text)
    contract_vehicles: Mapped[Optional[str]] = mapped_column(Text)
    total_jobs: Mapped[int] = mapped_column(Integer, default=0)
    total_placements: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[Optional[float]] = mapped_column(Float, default=0)
    first_engagement_date: Mapped[Optional[date]] = mapped_column(Date)
    last_engagement_date: Mapped[Optional[date]] = mapped_column(Date)
    relationship_status: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    programs: Mapped[list["Program"]] = relationship(back_populates="prime_contractor")
    past_performances: Mapped[list["PastPerformance"]] = relationship(
        back_populates="prime_contractor"
    )


class Program(TimestampMixin, Base):
    """Federal programs we support."""

    __tablename__ = "programs"
    __table_args__ = (
        Index("ix_bd_programs_name", "name"),
        Index("ix_bd_programs_prime_id", "prime_contractor_id"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_name: Mapped[Optional[str]] = mapped_column(String(500))
    acronym: Mapped[Optional[str]] = mapped_column(String(50))
    prime_contractor_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey(f"{BD_SCHEMA}.prime_contractors.id")
    )
    prime_contractor_name: Mapped[Optional[str]] = mapped_column(String(200))
    agency: Mapped[Optional[str]] = mapped_column(String(200))
    sub_agency: Mapped[Optional[str]] = mapped_column(String(200))
    contract_number: Mapped[Optional[str]] = mapped_column(String(100))
    contract_value: Mapped[Optional[float]] = mapped_column(Float)
    period_of_performance: Mapped[Optional[str]] = mapped_column(String(100))
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    location: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    total_jobs: Mapped[int] = mapped_column(Integer, default=0)
    total_placements: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[Optional[float]] = mapped_column(Float, default=0)
    source_file: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    prime_contractor: Mapped[Optional["PrimeContractor"]] = relationship(
        back_populates="programs"
    )
    past_performances: Mapped[list["PastPerformance"]] = relationship(
        back_populates="program"
    )


class PastPerformance(TimestampMixin, Base):
    """Aggregated past performance data."""

    __tablename__ = "past_performance"
    __table_args__ = {"schema": BD_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prime_contractor_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey(f"{BD_SCHEMA}.prime_contractors.id")
    )
    prime_contractor_name: Mapped[Optional[str]] = mapped_column(String(200))
    program_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey(f"{BD_SCHEMA}.programs.id")
    )
    program_name: Mapped[Optional[str]] = mapped_column(String(500))
    total_jobs: Mapped[int] = mapped_column(Integer, default=0)
    open_jobs: Mapped[int] = mapped_column(Integer, default=0)
    closed_jobs: Mapped[int] = mapped_column(Integer, default=0)
    filled_jobs: Mapped[int] = mapped_column(Integer, default=0)
    lost_jobs: Mapped[int] = mapped_column(Integer, default=0)
    total_placements: Mapped[int] = mapped_column(Integer, default=0)
    active_placements: Mapped[int] = mapped_column(Integer, default=0)
    completed_placements: Mapped[int] = mapped_column(Integer, default=0)
    total_candidates_submitted: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[Optional[float]] = mapped_column(Float, default=0)
    avg_bill_rate: Mapped[Optional[float]] = mapped_column(Float)
    avg_pay_rate: Mapped[Optional[float]] = mapped_column(Float)
    avg_margin: Mapped[Optional[float]] = mapped_column(Float)
    avg_placement_duration_days: Mapped[Optional[int]] = mapped_column(Integer)
    fill_rate: Mapped[Optional[float]] = mapped_column(Float)
    first_job_date: Mapped[Optional[date]] = mapped_column(Date)
    last_job_date: Mapped[Optional[date]] = mapped_column(Date)
    first_placement_date: Mapped[Optional[date]] = mapped_column(Date)
    last_placement_date: Mapped[Optional[date]] = mapped_column(Date)
    performance_score: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    prime_contractor: Mapped[Optional["PrimeContractor"]] = relationship(
        back_populates="past_performances"
    )
    program: Mapped[Optional["Program"]] = relationship(
        back_populates="past_performances"
    )


# =========================================================================
# LINKING / MAPPING TABLES  (from Engine7 database_schema.py)
# =========================================================================


class JobProgramMapping(Base):
    """Job-to-program mapping."""

    __tablename__ = "job_program_mapping"
    __table_args__ = (
        UniqueConstraint("job_id", "program_id", name="uq_job_program"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{BD_SCHEMA}.jobs.id"), nullable=False
    )
    program_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{BD_SCHEMA}.programs.id"), nullable=False
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    mapping_method: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class JobPrimeMapping(Base):
    """Job-to-prime-contractor mapping."""

    __tablename__ = "job_prime_mapping"
    __table_args__ = (
        UniqueConstraint("job_id", "prime_contractor_id", name="uq_job_prime"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{BD_SCHEMA}.jobs.id"), nullable=False
    )
    prime_contractor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{BD_SCHEMA}.prime_contractors.id"), nullable=False
    )
    relationship_type: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


# =========================================================================
# MASTER FEDERAL CONTRACTS  (from scripts/master_db/schema.py)
# =========================================================================


class Contact(TimestampMixin, Base):
    """Contacts from the master federal contracts database."""

    __tablename__ = "contacts"
    __table_args__ = (
        Index("ix_bd_contacts_name", "full_name"),
        Index("ix_bd_contacts_email", "email"),
        Index("ix_bd_contacts_company", "company"),
        Index("ix_bd_contacts_tier", "tier"),
        Index("ix_bd_contacts_program", "program"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    company: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    linkedin: Mapped[Optional[str]] = mapped_column(String(500))
    program: Mapped[Optional[str]] = mapped_column(String(255))
    tier: Mapped[Optional[int]] = mapped_column(Integer)
    contact_type: Mapped[Optional[str]] = mapped_column(String(50))
    bd_priority: Mapped[Optional[str]] = mapped_column(String(50))
    relationship_status: Mapped[Optional[str]] = mapped_column(String(50))
    relationship_score: Mapped[Optional[float]] = mapped_column(Float)
    is_hiring_manager: Mapped[Optional[bool]] = mapped_column(Boolean)
    has_open_reqs: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_decision_maker: Mapped[Optional[bool]] = mapped_column(Boolean)
    clearances: Mapped[Optional[str]] = mapped_column(Text)
    locations: Mapped[Optional[str]] = mapped_column(Text)
    note_count: Mapped[Optional[int]] = mapped_column(Integer)
    last_activity: Mapped[Optional[str]] = mapped_column(String(255))
    source_db: Mapped[Optional[str]] = mapped_column(String(100))
    source_files: Mapped[Optional[str]] = mapped_column(Text)
    data_quality_score: Mapped[Optional[float]] = mapped_column(Float)


class Company(TimestampMixin, Base):
    """Companies from the master federal contracts database."""

    __tablename__ = "companies"
    __table_args__ = (
        Index("ix_bd_companies_name", "name"),
        Index("ix_bd_companies_normalized", "normalized_name"),
        Index("ix_bd_companies_uei", "uei"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_name: Mapped[Optional[str]] = mapped_column(String(200))
    aliases: Mapped[Optional[str]] = mapped_column(Text)
    company_type: Mapped[Optional[str]] = mapped_column(String(50))
    cage_code: Mapped[Optional[str]] = mapped_column(String(20))
    duns_number: Mapped[Optional[str]] = mapped_column(String(20))
    uei: Mapped[Optional[str]] = mapped_column(String(20))
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)
    annual_revenue: Mapped[Optional[float]] = mapped_column(Float)
    website: Mapped[Optional[str]] = mapped_column(String(500))
    headquarters: Mapped[Optional[str]] = mapped_column(String(200))
    contract_vehicles: Mapped[Optional[str]] = mapped_column(Text)
    naics_codes: Mapped[Optional[str]] = mapped_column(Text)
    relationship_tier: Mapped[Optional[str]] = mapped_column(String(50))
    contract_count: Mapped[Optional[int]] = mapped_column(Integer)
    total_award_amount: Mapped[Optional[float]] = mapped_column(Float)
    source_files: Mapped[Optional[str]] = mapped_column(Text)
    data_quality_score: Mapped[Optional[float]] = mapped_column(Float)


class Contract(Base):
    """Federal contracts."""

    __tablename__ = "contracts"
    __table_args__ = (
        Index("ix_bd_contracts_piid", "piid"),
        Index("ix_bd_contracts_program_id", "program_id"),
        Index("ix_bd_contracts_recipient", "recipient_name"),
        Index("ix_bd_contracts_agency", "awarding_agency"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    piid: Mapped[Optional[str]] = mapped_column(String(100))
    award_id: Mapped[Optional[str]] = mapped_column(String(100))
    source: Mapped[Optional[str]] = mapped_column(String(50))
    program_id: Mapped[Optional[str]] = mapped_column(String(64))
    program_name: Mapped[Optional[str]] = mapped_column(String(500))
    recipient_name: Mapped[Optional[str]] = mapped_column(String(200))
    recipient_uei: Mapped[Optional[str]] = mapped_column(String(20))
    company_id: Mapped[Optional[str]] = mapped_column(String(64))
    award_amount: Mapped[Optional[float]] = mapped_column(Float)
    obligated: Mapped[Optional[float]] = mapped_column(Float)
    total_contract_value: Mapped[Optional[float]] = mapped_column(Float)
    description: Mapped[Optional[str]] = mapped_column(Text)
    awarding_agency: Mapped[Optional[str]] = mapped_column(String(200))
    naics_code: Mapped[Optional[str]] = mapped_column(String(20))
    psc_code: Mapped[Optional[str]] = mapped_column(String(20))
    start_date: Mapped[Optional[str]] = mapped_column(String(50))
    end_date: Mapped[Optional[str]] = mapped_column(String(50))
    set_aside: Mapped[Optional[str]] = mapped_column(String(100))
    award_date: Mapped[Optional[str]] = mapped_column(String(50))
    source_file: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class FederalContract(Base):
    """Simplified federal contract record for the bd.federal_contracts table
    specified in the migration scope."""

    __tablename__ = "federal_contracts"
    __table_args__ = (
        Index("ix_bd_fc_notice_id", "notice_id"),
        Index("ix_bd_fc_agency", "agency"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notice_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    title: Mapped[Optional[str]] = mapped_column(String(500))
    agency: Mapped[Optional[str]] = mapped_column(String(200))
    naics: Mapped[Optional[str]] = mapped_column(String(20))
    set_aside: Mapped[Optional[str]] = mapped_column(String(100))
    value: Mapped[Optional[float]] = mapped_column(Float)
    award_date: Mapped[Optional[str]] = mapped_column(String(50))
    awardee: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Intelligence(Base):
    """BD intelligence records."""

    __tablename__ = "intelligence"
    __table_args__ = (
        Index("ix_bd_intel_program_id", "program_id"),
        Index("ix_bd_intel_type", "intel_type"),
        Index("ix_bd_intel_score", "bd_score"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    intel_type: Mapped[Optional[str]] = mapped_column(String(50))
    program_name: Mapped[Optional[str]] = mapped_column(String(500))
    program_id: Mapped[Optional[str]] = mapped_column(String(64))
    company_name: Mapped[Optional[str]] = mapped_column(String(200))
    company_id: Mapped[Optional[str]] = mapped_column(String(64))
    bd_score: Mapped[Optional[float]] = mapped_column(Float)
    priority_tier: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    awarding_agency: Mapped[Optional[str]] = mapped_column(String(200))
    naics_code: Mapped[Optional[str]] = mapped_column(String(20))
    start_date: Mapped[Optional[str]] = mapped_column(String(50))
    end_date: Mapped[Optional[str]] = mapped_column(String(50))
    source: Mapped[Optional[str]] = mapped_column(String(100))
    source_file: Mapped[Optional[str]] = mapped_column(String(255))
    data_quality_score: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Document(Base):
    """Documents (past performance, briefings, etc.)."""

    __tablename__ = "documents"
    __table_args__ = {"schema": BD_SCHEMA}

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    doc_type: Mapped[Optional[str]] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[Optional[str]] = mapped_column(Text)
    program_name: Mapped[Optional[str]] = mapped_column(String(500))
    program_id: Mapped[Optional[str]] = mapped_column(String(64))
    company_name: Mapped[Optional[str]] = mapped_column(String(200))
    source: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Timeline(Base):
    """Derived timeline events."""

    __tablename__ = "timelines"
    __table_args__ = (
        Index("ix_bd_timelines_date", "event_date"),
        Index("ix_bd_timelines_program_id", "program_id"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_date: Mapped[Optional[str]] = mapped_column(String(50))
    program_id: Mapped[Optional[str]] = mapped_column(String(64))
    program_name: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    days_until_event: Mapped[Optional[int]] = mapped_column(Integer)
    urgency: Mapped[Optional[str]] = mapped_column(String(50))
    source: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Scoring(Base):
    """BD scoring records."""

    __tablename__ = "scoring"
    __table_args__ = (
        Index("ix_bd_scoring_entity_id", "entity_id"),
        Index("ix_bd_scoring_entity_type", "entity_type"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(64))
    entity_name: Mapped[Optional[str]] = mapped_column(String(500))
    bd_score: Mapped[Optional[float]] = mapped_column(Float)
    priority_tier: Mapped[Optional[str]] = mapped_column(String(50))
    composite_score: Mapped[Optional[float]] = mapped_column(Float)
    scoring_details: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class ProgramContact(Base):
    """Many-to-many junction: programs <-> contacts."""

    __tablename__ = "program_contacts"
    __table_args__ = (
        UniqueConstraint("program_id", "contact_id", name="uq_program_contact"),
        Index("ix_bd_pc_program", "program_id"),
        Index("ix_bd_pc_contact", "contact_id"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    program_id: Mapped[str] = mapped_column(String(64), nullable=False)
    contact_id: Mapped[str] = mapped_column(String(64), nullable=False)
    relationship_type: Mapped[Optional[str]] = mapped_column(String(50))
    source: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class ProgramCompany(Base):
    """Many-to-many junction: programs <-> companies."""

    __tablename__ = "program_companies"
    __table_args__ = (
        UniqueConstraint(
            "program_id", "company_id", "role", name="uq_program_company_role"
        ),
        Index("ix_bd_pco_program", "program_id"),
        Index("ix_bd_pco_company", "company_id"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    program_id: Mapped[str] = mapped_column(String(64), nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(50))
    source: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class EtlRun(Base):
    """ETL run metadata."""

    __tablename__ = "etl_runs"
    __table_args__ = {"schema": BD_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(100), nullable=False)
    run_type: Mapped[Optional[str]] = mapped_column(String(50))
    started_at: Mapped[Optional[str]] = mapped_column(String(50))
    completed_at: Mapped[Optional[str]] = mapped_column(String(50))
    tables_loaded: Mapped[Optional[str]] = mapped_column(Text)
    total_records: Mapped[Optional[int]] = mapped_column(Integer)
    errors: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    details: Mapped[Optional[str]] = mapped_column(Text)


class SourceTracking(Base):
    """Source file tracking metadata."""

    __tablename__ = "source_tracking"
    __table_args__ = (
        UniqueConstraint(
            "table_name", "record_id", "source_file", name="uq_source_tracking"
        ),
        Index("ix_bd_st_table", "table_name"),
        Index("ix_bd_st_record", "record_id"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_file: Mapped[Optional[str]] = mapped_column(String(255))
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    record_hash: Mapped[Optional[str]] = mapped_column(String(64))
    first_loaded: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    last_updated: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


# =========================================================================
# QA & SYNC TABLES  (specified in migration scope)
# =========================================================================


class QaReviewQueue(Base):
    """QA review queue for pipeline outputs."""

    __tablename__ = "qa_review_queue"
    __table_args__ = (
        Index("ix_bd_qa_status", "status"),
        {"schema": BD_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    review_reasons: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    reviewer: Mapped[Optional[str]] = mapped_column(String(255))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    root_cause: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    audit_log: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class SyncState(TimestampMixin, Base):
    """Tracks sync state for external data sources."""

    __tablename__ = "sync_state"
    __table_args__ = {"schema": BD_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cursor_data: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
