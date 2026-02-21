"""Initial BD schema with all tables.

Revision ID: 001
Revises: None
Create Date: 2026-02-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "bd"


def _schema_arg(name: str) -> str:
    """Return schema-qualified table name for PostgreSQL, plain for SQLite."""
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        return name
    return name


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    schema = SCHEMA if dialect == "postgresql" else None

    if dialect == "postgresql":
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")

    # -----------------------------------------------------------------
    # jobs
    # -----------------------------------------------------------------
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("bullhorn_job_id", sa.String(20), unique=True),
        sa.Column("job_number", sa.String(10)),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("client_corporation", sa.String(200)),
        sa.Column("prime_contractor", sa.String(200)),
        sa.Column("employment_type", sa.String(50)),
        sa.Column("status", sa.String(50)),
        sa.Column("pay_rate", sa.Float),
        sa.Column("bill_rate", sa.Float),
        sa.Column("salary", sa.Float),
        sa.Column("perm_fee_percent", sa.Integer),
        sa.Column("location", sa.String(255)),
        sa.Column("city", sa.String(100)),
        sa.Column("state", sa.String(50)),
        sa.Column("clearance_required", sa.String(100)),
        sa.Column("skills", sa.Text),
        sa.Column("owner", sa.String(200)),
        sa.Column("contact", sa.String(200)),
        sa.Column("date_added", sa.DateTime),
        sa.Column("date_modified", sa.DateTime),
        sa.Column("date_closed", sa.DateTime),
        sa.Column("custom_text1", sa.Text),
        sa.Column("custom_text2", sa.Text),
        sa.Column("custom_text3", sa.Text),
        sa.Column("source_file", sa.String(255)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_bd_jobs_bullhorn_id", "jobs", ["bullhorn_job_id"], schema=schema)
    op.create_index("ix_bd_jobs_client", "jobs", ["client_corporation"], schema=schema)
    op.create_index("ix_bd_jobs_prime", "jobs", ["prime_contractor"], schema=schema)
    op.create_index("ix_bd_jobs_status", "jobs", ["status"], schema=schema)
    op.create_index("ix_bd_jobs_date_added", "jobs", ["date_added"], schema=schema)

    # -----------------------------------------------------------------
    # candidates
    # -----------------------------------------------------------------
    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("bullhorn_candidate_id", sa.String(50), unique=True),
        sa.Column("first_name", sa.String(100)),
        sa.Column("last_name", sa.String(100)),
        sa.Column("full_name", sa.String(200)),
        sa.Column("email", sa.String(200)),
        sa.Column("phone", sa.String(50)),
        sa.Column("mobile", sa.String(50)),
        sa.Column("occupation", sa.String(200)),
        sa.Column("job_title", sa.String(200)),
        sa.Column("company_name", sa.String(200)),
        sa.Column("current_employer", sa.String(200)),
        sa.Column("status", sa.String(50)),
        sa.Column("address", sa.String(500)),
        sa.Column("city", sa.String(100)),
        sa.Column("state", sa.String(50)),
        sa.Column("zip_code", sa.String(20)),
        sa.Column("clearance_level", sa.String(100)),
        sa.Column("linkedin_url", sa.String(500)),
        sa.Column("owner", sa.String(200)),
        sa.Column("date_added", sa.DateTime),
        sa.Column("date_modified", sa.DateTime),
        sa.Column("last_activity_date", sa.DateTime),
        sa.Column("custom_text1", sa.Text),
        sa.Column("custom_text2", sa.Text),
        sa.Column("custom_text3", sa.Text),
        sa.Column("source_file", sa.String(255)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_bd_candidates_bullhorn_id", "candidates", ["bullhorn_candidate_id"], schema=schema)
    op.create_index("ix_bd_candidates_name", "candidates", ["full_name"], schema=schema)
    op.create_index("ix_bd_candidates_email", "candidates", ["email"], schema=schema)
    op.create_index("ix_bd_candidates_company", "candidates", ["company_name"], schema=schema)

    # -----------------------------------------------------------------
    # prime_contractors
    # -----------------------------------------------------------------
    op.create_table(
        "prime_contractors",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), unique=True, nullable=False),
        sa.Column("normalized_name", sa.String(200)),
        sa.Column("aliases", sa.Text),
        sa.Column("cage_code", sa.String(20)),
        sa.Column("duns_number", sa.String(20)),
        sa.Column("website", sa.String(500)),
        sa.Column("headquarters", sa.String(200)),
        sa.Column("employee_count", sa.Integer),
        sa.Column("annual_revenue", sa.Float),
        sa.Column("naics_codes", sa.Text),
        sa.Column("contract_vehicles", sa.Text),
        sa.Column("total_jobs", sa.Integer, default=0),
        sa.Column("total_placements", sa.Integer, default=0),
        sa.Column("total_revenue", sa.Float, default=0),
        sa.Column("first_engagement_date", sa.Date),
        sa.Column("last_engagement_date", sa.Date),
        sa.Column("relationship_status", sa.String(50)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_bd_primes_name", "prime_contractors", ["name"], schema=schema)
    op.create_index("ix_bd_primes_normalized", "prime_contractors", ["normalized_name"], schema=schema)

    # -----------------------------------------------------------------
    # programs
    # -----------------------------------------------------------------
    op.create_table(
        "programs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("normalized_name", sa.String(500)),
        sa.Column("acronym", sa.String(50)),
        sa.Column("prime_contractor_id", sa.Integer, sa.ForeignKey(f"{schema + '.' if schema else ''}prime_contractors.id")),
        sa.Column("prime_contractor_name", sa.String(200)),
        sa.Column("agency", sa.String(200)),
        sa.Column("sub_agency", sa.String(200)),
        sa.Column("contract_number", sa.String(100)),
        sa.Column("contract_value", sa.Float),
        sa.Column("period_of_performance", sa.String(100)),
        sa.Column("start_date", sa.Date),
        sa.Column("end_date", sa.Date),
        sa.Column("location", sa.String(200)),
        sa.Column("description", sa.Text),
        sa.Column("total_jobs", sa.Integer, default=0),
        sa.Column("total_placements", sa.Integer, default=0),
        sa.Column("total_revenue", sa.Float, default=0),
        sa.Column("source_file", sa.String(255)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_bd_programs_name", "programs", ["name"], schema=schema)
    op.create_index("ix_bd_programs_prime_id", "programs", ["prime_contractor_id"], schema=schema)

    # -----------------------------------------------------------------
    # placements
    # -----------------------------------------------------------------
    op.create_table(
        "placements",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("bullhorn_placement_id", sa.String(50), unique=True),
        sa.Column("job_id", sa.Integer, sa.ForeignKey(f"{schema + '.' if schema else ''}jobs.id")),
        sa.Column("candidate_id", sa.Integer, sa.ForeignKey(f"{schema + '.' if schema else ''}candidates.id")),
        sa.Column("bullhorn_job_id", sa.String(20)),
        sa.Column("bullhorn_candidate_id", sa.String(50)),
        sa.Column("placement_date", sa.Date),
        sa.Column("start_date", sa.Date),
        sa.Column("end_date", sa.Date),
        sa.Column("status", sa.String(50)),
        sa.Column("outcome", sa.String(100)),
        sa.Column("pay_rate", sa.Float),
        sa.Column("bill_rate", sa.Float),
        sa.Column("salary", sa.Float),
        sa.Column("commission", sa.Float),
        sa.Column("duration_days", sa.Integer),
        sa.Column("client_name", sa.String(200)),
        sa.Column("job_title", sa.String(500)),
        sa.Column("candidate_name", sa.String(200)),
        sa.Column("owner", sa.String(200)),
        sa.Column("source_file", sa.String(255)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        schema=schema,
    )
    op.create_index("ix_bd_placements_job_id", "placements", ["job_id"], schema=schema)
    op.create_index("ix_bd_placements_candidate_id", "placements", ["candidate_id"], schema=schema)
    op.create_index("ix_bd_placements_date", "placements", ["placement_date"], schema=schema)

    # -----------------------------------------------------------------
    # activities
    # -----------------------------------------------------------------
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("bullhorn_activity_id", sa.String(50)),
        sa.Column("activity_type", sa.String(100)),
        sa.Column("action", sa.String(200)),
        sa.Column("related_job_id", sa.Integer, sa.ForeignKey(f"{schema + '.' if schema else ''}jobs.id")),
        sa.Column("related_candidate_id", sa.Integer, sa.ForeignKey(f"{schema + '.' if schema else ''}candidates.id")),
        sa.Column("bullhorn_job_id", sa.String(20)),
        sa.Column("bullhorn_candidate_id", sa.String(50)),
        sa.Column("activity_date", sa.DateTime),
        sa.Column("actor", sa.String(200)),
        sa.Column("note_text", sa.Text),
        sa.Column("comments", sa.Text),
        sa.Column("follow_up_required", sa.Boolean),
        sa.Column("follow_up_date", sa.Date),
        sa.Column("status", sa.String(50)),
        sa.Column("source_file", sa.String(255)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        schema=schema,
    )
    op.create_index("ix_bd_activities_job_id", "activities", ["related_job_id"], schema=schema)
    op.create_index("ix_bd_activities_candidate_id", "activities", ["related_candidate_id"], schema=schema)
    op.create_index("ix_bd_activities_date", "activities", ["activity_date"], schema=schema)

    # -----------------------------------------------------------------
    # past_performance
    # -----------------------------------------------------------------
    op.create_table(
        "past_performance",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("prime_contractor_id", sa.Integer, sa.ForeignKey(f"{schema + '.' if schema else ''}prime_contractors.id")),
        sa.Column("prime_contractor_name", sa.String(200)),
        sa.Column("program_id", sa.Integer, sa.ForeignKey(f"{schema + '.' if schema else ''}programs.id")),
        sa.Column("program_name", sa.String(500)),
        sa.Column("total_jobs", sa.Integer, default=0),
        sa.Column("open_jobs", sa.Integer, default=0),
        sa.Column("closed_jobs", sa.Integer, default=0),
        sa.Column("filled_jobs", sa.Integer, default=0),
        sa.Column("lost_jobs", sa.Integer, default=0),
        sa.Column("total_placements", sa.Integer, default=0),
        sa.Column("active_placements", sa.Integer, default=0),
        sa.Column("completed_placements", sa.Integer, default=0),
        sa.Column("total_candidates_submitted", sa.Integer, default=0),
        sa.Column("total_revenue", sa.Float, default=0),
        sa.Column("avg_bill_rate", sa.Float),
        sa.Column("avg_pay_rate", sa.Float),
        sa.Column("avg_margin", sa.Float),
        sa.Column("avg_placement_duration_days", sa.Integer),
        sa.Column("fill_rate", sa.Float),
        sa.Column("first_job_date", sa.Date),
        sa.Column("last_job_date", sa.Date),
        sa.Column("first_placement_date", sa.Date),
        sa.Column("last_placement_date", sa.Date),
        sa.Column("performance_score", sa.Float),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        schema=schema,
    )

    # -----------------------------------------------------------------
    # job_program_mapping
    # -----------------------------------------------------------------
    op.create_table(
        "job_program_mapping",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.Integer, sa.ForeignKey(f"{schema + '.' if schema else ''}jobs.id"), nullable=False),
        sa.Column("program_id", sa.Integer, sa.ForeignKey(f"{schema + '.' if schema else ''}programs.id"), nullable=False),
        sa.Column("confidence_score", sa.Float),
        sa.Column("mapping_method", sa.String(50)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("job_id", "program_id", name="uq_job_program"),
        schema=schema,
    )

    # -----------------------------------------------------------------
    # job_prime_mapping
    # -----------------------------------------------------------------
    op.create_table(
        "job_prime_mapping",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.Integer, sa.ForeignKey(f"{schema + '.' if schema else ''}jobs.id"), nullable=False),
        sa.Column("prime_contractor_id", sa.Integer, sa.ForeignKey(f"{schema + '.' if schema else ''}prime_contractors.id"), nullable=False),
        sa.Column("relationship_type", sa.String(50)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("job_id", "prime_contractor_id", name="uq_job_prime"),
        schema=schema,
    )

    # -----------------------------------------------------------------
    # contacts
    # -----------------------------------------------------------------
    op.create_table(
        "contacts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("first_name", sa.String(100)),
        sa.Column("last_name", sa.String(100)),
        sa.Column("title", sa.String(255)),
        sa.Column("company", sa.String(255)),
        sa.Column("email", sa.String(200)),
        sa.Column("phone", sa.String(50)),
        sa.Column("linkedin", sa.String(500)),
        sa.Column("program", sa.String(255)),
        sa.Column("tier", sa.Integer),
        sa.Column("contact_type", sa.String(50)),
        sa.Column("bd_priority", sa.String(50)),
        sa.Column("relationship_status", sa.String(50)),
        sa.Column("relationship_score", sa.Float),
        sa.Column("is_hiring_manager", sa.Boolean),
        sa.Column("has_open_reqs", sa.Boolean),
        sa.Column("is_decision_maker", sa.Boolean),
        sa.Column("clearances", sa.Text),
        sa.Column("locations", sa.Text),
        sa.Column("note_count", sa.Integer),
        sa.Column("last_activity", sa.String(255)),
        sa.Column("source_db", sa.String(100)),
        sa.Column("source_files", sa.Text),
        sa.Column("data_quality_score", sa.Float),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_bd_contacts_name", "contacts", ["full_name"], schema=schema)
    op.create_index("ix_bd_contacts_email", "contacts", ["email"], schema=schema)
    op.create_index("ix_bd_contacts_company", "contacts", ["company"], schema=schema)
    op.create_index("ix_bd_contacts_tier", "contacts", ["tier"], schema=schema)
    op.create_index("ix_bd_contacts_program", "contacts", ["program"], schema=schema)

    # -----------------------------------------------------------------
    # companies
    # -----------------------------------------------------------------
    op.create_table(
        "companies",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("normalized_name", sa.String(200)),
        sa.Column("aliases", sa.Text),
        sa.Column("company_type", sa.String(50)),
        sa.Column("cage_code", sa.String(20)),
        sa.Column("duns_number", sa.String(20)),
        sa.Column("uei", sa.String(20)),
        sa.Column("employee_count", sa.Integer),
        sa.Column("annual_revenue", sa.Float),
        sa.Column("website", sa.String(500)),
        sa.Column("headquarters", sa.String(200)),
        sa.Column("contract_vehicles", sa.Text),
        sa.Column("naics_codes", sa.Text),
        sa.Column("relationship_tier", sa.String(50)),
        sa.Column("contract_count", sa.Integer),
        sa.Column("total_award_amount", sa.Float),
        sa.Column("source_files", sa.Text),
        sa.Column("data_quality_score", sa.Float),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_bd_companies_name", "companies", ["name"], schema=schema)
    op.create_index("ix_bd_companies_normalized", "companies", ["normalized_name"], schema=schema)
    op.create_index("ix_bd_companies_uei", "companies", ["uei"], schema=schema)

    # -----------------------------------------------------------------
    # contracts
    # -----------------------------------------------------------------
    op.create_table(
        "contracts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("piid", sa.String(100)),
        sa.Column("award_id", sa.String(100)),
        sa.Column("source", sa.String(50)),
        sa.Column("program_id", sa.String(64)),
        sa.Column("program_name", sa.String(500)),
        sa.Column("recipient_name", sa.String(200)),
        sa.Column("recipient_uei", sa.String(20)),
        sa.Column("company_id", sa.String(64)),
        sa.Column("award_amount", sa.Float),
        sa.Column("obligated", sa.Float),
        sa.Column("total_contract_value", sa.Float),
        sa.Column("description", sa.Text),
        sa.Column("awarding_agency", sa.String(200)),
        sa.Column("naics_code", sa.String(20)),
        sa.Column("psc_code", sa.String(20)),
        sa.Column("start_date", sa.String(50)),
        sa.Column("end_date", sa.String(50)),
        sa.Column("set_aside", sa.String(100)),
        sa.Column("award_date", sa.String(50)),
        sa.Column("source_file", sa.String(255)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_bd_contracts_piid", "contracts", ["piid"], schema=schema)
    op.create_index("ix_bd_contracts_program_id", "contracts", ["program_id"], schema=schema)
    op.create_index("ix_bd_contracts_recipient", "contracts", ["recipient_name"], schema=schema)
    op.create_index("ix_bd_contracts_agency", "contracts", ["awarding_agency"], schema=schema)

    # -----------------------------------------------------------------
    # federal_contracts
    # -----------------------------------------------------------------
    op.create_table(
        "federal_contracts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("notice_id", sa.String(100), unique=True),
        sa.Column("title", sa.String(500)),
        sa.Column("agency", sa.String(200)),
        sa.Column("naics", sa.String(20)),
        sa.Column("set_aside", sa.String(100)),
        sa.Column("value", sa.Float),
        sa.Column("award_date", sa.String(50)),
        sa.Column("awardee", sa.String(200)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        schema=schema,
    )
    op.create_index("ix_bd_fc_notice_id", "federal_contracts", ["notice_id"], schema=schema)
    op.create_index("ix_bd_fc_agency", "federal_contracts", ["agency"], schema=schema)

    # -----------------------------------------------------------------
    # intelligence
    # -----------------------------------------------------------------
    op.create_table(
        "intelligence",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("intel_type", sa.String(50)),
        sa.Column("program_name", sa.String(500)),
        sa.Column("program_id", sa.String(64)),
        sa.Column("company_name", sa.String(200)),
        sa.Column("company_id", sa.String(64)),
        sa.Column("bd_score", sa.Float),
        sa.Column("priority_tier", sa.String(50)),
        sa.Column("description", sa.Text),
        sa.Column("awarding_agency", sa.String(200)),
        sa.Column("naics_code", sa.String(20)),
        sa.Column("start_date", sa.String(50)),
        sa.Column("end_date", sa.String(50)),
        sa.Column("source", sa.String(100)),
        sa.Column("source_file", sa.String(255)),
        sa.Column("data_quality_score", sa.Float),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        schema=schema,
    )
    op.create_index("ix_bd_intel_program_id", "intelligence", ["program_id"], schema=schema)
    op.create_index("ix_bd_intel_type", "intelligence", ["intel_type"], schema=schema)
    op.create_index("ix_bd_intel_score", "intelligence", ["bd_score"], schema=schema)

    # -----------------------------------------------------------------
    # documents
    # -----------------------------------------------------------------
    op.create_table(
        "documents",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("doc_type", sa.String(50)),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("file_path", sa.Text),
        sa.Column("content", sa.Text),
        sa.Column("program_name", sa.String(500)),
        sa.Column("program_id", sa.String(64)),
        sa.Column("company_name", sa.String(200)),
        sa.Column("source", sa.String(100)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        schema=schema,
    )

    # -----------------------------------------------------------------
    # timelines
    # -----------------------------------------------------------------
    op.create_table(
        "timelines",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("event_date", sa.String(50)),
        sa.Column("program_id", sa.String(64)),
        sa.Column("program_name", sa.String(500)),
        sa.Column("description", sa.Text),
        sa.Column("days_until_event", sa.Integer),
        sa.Column("urgency", sa.String(50)),
        sa.Column("source", sa.String(100)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        schema=schema,
    )
    op.create_index("ix_bd_timelines_date", "timelines", ["event_date"], schema=schema)
    op.create_index("ix_bd_timelines_program_id", "timelines", ["program_id"], schema=schema)

    # -----------------------------------------------------------------
    # scoring
    # -----------------------------------------------------------------
    op.create_table(
        "scoring",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(64)),
        sa.Column("entity_name", sa.String(500)),
        sa.Column("bd_score", sa.Float),
        sa.Column("priority_tier", sa.String(50)),
        sa.Column("composite_score", sa.Float),
        sa.Column("scoring_details", sa.Text),
        sa.Column("source", sa.String(100)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        schema=schema,
    )
    op.create_index("ix_bd_scoring_entity_id", "scoring", ["entity_id"], schema=schema)
    op.create_index("ix_bd_scoring_entity_type", "scoring", ["entity_type"], schema=schema)

    # -----------------------------------------------------------------
    # program_contacts (junction)
    # -----------------------------------------------------------------
    op.create_table(
        "program_contacts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("program_id", sa.String(64), nullable=False),
        sa.Column("contact_id", sa.String(64), nullable=False),
        sa.Column("relationship_type", sa.String(50)),
        sa.Column("source", sa.String(100)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("program_id", "contact_id", name="uq_program_contact"),
        schema=schema,
    )
    op.create_index("ix_bd_pc_program", "program_contacts", ["program_id"], schema=schema)
    op.create_index("ix_bd_pc_contact", "program_contacts", ["contact_id"], schema=schema)

    # -----------------------------------------------------------------
    # program_companies (junction)
    # -----------------------------------------------------------------
    op.create_table(
        "program_companies",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("program_id", sa.String(64), nullable=False),
        sa.Column("company_id", sa.String(64), nullable=False),
        sa.Column("role", sa.String(50)),
        sa.Column("source", sa.String(100)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("program_id", "company_id", "role", name="uq_program_company_role"),
        schema=schema,
    )
    op.create_index("ix_bd_pco_program", "program_companies", ["program_id"], schema=schema)
    op.create_index("ix_bd_pco_company", "program_companies", ["company_id"], schema=schema)

    # -----------------------------------------------------------------
    # etl_runs
    # -----------------------------------------------------------------
    op.create_table(
        "etl_runs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(100), nullable=False),
        sa.Column("run_type", sa.String(50)),
        sa.Column("started_at", sa.String(50)),
        sa.Column("completed_at", sa.String(50)),
        sa.Column("tables_loaded", sa.Text),
        sa.Column("total_records", sa.Integer),
        sa.Column("errors", sa.Integer),
        sa.Column("status", sa.String(50)),
        sa.Column("details", sa.Text),
        schema=schema,
    )

    # -----------------------------------------------------------------
    # source_tracking
    # -----------------------------------------------------------------
    op.create_table(
        "source_tracking",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("table_name", sa.String(100), nullable=False),
        sa.Column("record_id", sa.String(64), nullable=False),
        sa.Column("source_file", sa.String(255)),
        sa.Column("source_type", sa.String(50)),
        sa.Column("record_hash", sa.String(64)),
        sa.Column("first_loaded", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("last_updated", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("table_name", "record_id", "source_file", name="uq_source_tracking"),
        schema=schema,
    )
    op.create_index("ix_bd_st_table", "source_tracking", ["table_name"], schema=schema)
    op.create_index("ix_bd_st_record", "source_tracking", ["record_id"], schema=schema)

    # -----------------------------------------------------------------
    # qa_review_queue
    # -----------------------------------------------------------------
    op.create_table(
        "qa_review_queue",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.Integer),
        sa.Column("status", sa.String(50)),
        sa.Column("confidence", sa.Float),
        sa.Column("review_reasons", sa.Text),
        sa.Column("reviewer", sa.String(255)),
        sa.Column("reviewed_at", sa.DateTime),
        sa.Column("root_cause", sa.Text),
        sa.Column("audit_log", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        schema=schema,
    )
    op.create_index("ix_bd_qa_status", "qa_review_queue", ["status"], schema=schema)

    # -----------------------------------------------------------------
    # sync_state
    # -----------------------------------------------------------------
    op.create_table(
        "sync_state",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(100), unique=True, nullable=False),
        sa.Column("last_sync", sa.DateTime),
        sa.Column("cursor_data", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        schema=schema,
    )


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    schema = SCHEMA if dialect == "postgresql" else None

    tables = [
        "sync_state",
        "qa_review_queue",
        "source_tracking",
        "etl_runs",
        "program_companies",
        "program_contacts",
        "scoring",
        "timelines",
        "documents",
        "intelligence",
        "federal_contracts",
        "contracts",
        "companies",
        "contacts",
        "job_prime_mapping",
        "job_program_mapping",
        "past_performance",
        "activities",
        "placements",
        "programs",
        "prime_contractors",
        "candidates",
        "jobs",
    ]

    for table in tables:
        op.drop_table(table, schema=schema)

    if dialect == "postgresql":
        op.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
