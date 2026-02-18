"""
Master Federal Contracts Database Schema
16 tables + 6 views for 360-degree program intelligence.
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "master_federal_contracts.db"


def create_database(db_path: Path = None) -> Path:
    """Create the master database with all tables, views, and indexes."""
    db_path = db_path or DATABASE_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    cursor = conn.cursor()

    # =========================================
    # TABLE 1: PROGRAMS (central hub)
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS programs (
            id TEXT PRIMARY KEY,
            program_name TEXT NOT NULL,
            acronym TEXT,
            agency_owner TEXT,
            program_type TEXT,
            priority_level TEXT,
            confidence_level TEXT,
            pts_involvement TEXT,
            contract_number TEXT,
            tango_piid TEXT,
            parent_piid TEXT,
            contract_value TEXT,
            contract_value_consolidated REAL,
            total_contract_value REAL,
            base_contract_value_fpds REAL,
            base_options_value_fpds REAL,
            obligated REAL,
            subawards_total REAL,
            subawards_count INTEGER,
            prime_contractor TEXT,
            prime_contractor_1 TEXT,
            prime_contractor_consolidated TEXT,
            recipient_name TEXT,
            recipient_uei TEXT,
            key_subcontractors TEXT,
            known_subcontractors TEXT,
            period_of_performance TEXT,
            pop_start TEXT,
            pop_end TEXT,
            pop_start_consolidated TEXT,
            pop_end_consolidated TEXT,
            ultimate_completion TEXT,
            ultimate_completion_consolidated TEXT,
            recompete_date TEXT,
            contract_signed_date_fpds TEXT,
            contract_effective_date_fpds TEXT,
            current_completion_date_fpds TEXT,
            ultimate_completion_date_fpds TEXT,
            key_locations TEXT,
            performance_location_tango TEXT,
            performance_location_fpds TEXT,
            pop_city TEXT,
            pop_state TEXT,
            pop_zip TEXT,
            pop_country TEXT,
            naics_code_consolidated TEXT,
            naics_code TEXT,
            fpds_naics_code TEXT,
            naics_description TEXT,
            psc_code_consolidated TEXT,
            psc_code TEXT,
            fpds_psc_code TEXT,
            psc_description TEXT,
            set_aside TEXT,
            technical_stack TEXT,
            tech_stack_basic TEXT,
            keywords_signals TEXT,
            functional_areas TEXT,
            typical_roles TEXT,
            job_titles TEXT,
            labor_rate_min REAL,
            labor_rate_max REAL,
            labor_rate_average REAL,
            education_requirement TEXT,
            experience_requirement TEXT,
            annual_salary_range TEXT,
            calc_api_status TEXT,
            contract_vehicle_used TEXT,
            contract_vehicle_type TEXT,
            awarding_office TEXT,
            awarding_agency TEXT,
            funding_office TEXT,
            cor_cotr TEXT,
            program_manager TEXT,
            clearance_requirements TEXT,
            security_requirements TEXT,
            match_confidence TEXT,
            match_score REAL,
            incumbent_score REAL,
            source_evidence TEXT,
            notes TEXT,
            pain_points TEXT,
            related_jobs TEXT,
            tango_description TEXT,
            parent_description TEXT,
            budget TEXT,
            description TEXT,
            mention_count INTEGER,
            piid_count INTEGER,
            total_award_amount REAL,
            top_recipients TEXT,
            technology_areas TEXT,
            roles_needed TEXT,
            parent_organization TEXT,
            source_files TEXT,
            domain_tags TEXT,
            data_quality_score REAL,
            community_id INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # =========================================
    # TABLE 2: COMPANIES
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            normalized_name TEXT,
            aliases TEXT,
            company_type TEXT,
            cage_code TEXT,
            duns_number TEXT,
            uei TEXT,
            sam_registration TEXT,
            clearance_facility TEXT,
            employee_count INTEGER,
            annual_revenue REAL,
            website TEXT,
            headquarters TEXT,
            linkedin_url TEXT,
            github_org TEXT,
            key_capabilities TEXT,
            recent_wins TEXT,
            contract_vehicles TEXT,
            naics_codes TEXT,
            federal_programs_prime TEXT,
            federal_programs_sub TEXT,
            past_performance TEXT,
            subcontractor_to TEXT,
            note_count INTEGER,
            programs TEXT,
            tech_stack TEXT,
            contract_count INTEGER,
            total_award_amount REAL,
            recent_contract_count INTEGER,
            recent_contract_value REAL,
            usaspending_contract_count INTEGER,
            usaspending_total_obligated REAL,
            usaspending_agencies TEXT,
            relationship_tier TEXT,
            bullhorn_mentions INTEGER,
            bullhorn_contacts INTEGER,
            bullhorn_programs TEXT,
            first_seen TEXT,
            last_seen TEXT,
            source_files TEXT,
            data_quality_score REAL,
            community_id INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # =========================================
    # TABLE 3: CONTRACTS
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id TEXT PRIMARY KEY,
            piid TEXT,
            award_id TEXT,
            contract_id TEXT,
            source TEXT,
            program_id TEXT,
            program_name TEXT,
            recipient_name TEXT,
            recipient_uei TEXT,
            company_id TEXT,
            award_amount REAL,
            obligated REAL,
            base_and_exercised_options_value REAL,
            total_contract_value REAL,
            description TEXT,
            awarding_agency TEXT,
            awarding_sub_agency TEXT,
            funding_agency TEXT,
            naics_code TEXT,
            naics_description TEXT,
            psc_code TEXT,
            psc_description TEXT,
            start_date TEXT,
            end_date TEXT,
            pop_start TEXT,
            pop_end TEXT,
            pop_ultimate TEXT,
            pop_city TEXT,
            pop_state TEXT,
            pop_zip TEXT,
            pop_country TEXT,
            fiscal_year TEXT,
            idv_type TEXT,
            set_aside TEXT,
            award_type TEXT,
            award_date TEXT,
            is_dod INTEGER,
            is_it_services INTEGER,
            prime_search TEXT,
            awarding_office TEXT,
            funding_office TEXT,
            source_file TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # =========================================
    # TABLE 4: TASK ORDERS / SUBAWARDS
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_orders (
            id TEXT PRIMARY KEY,
            subaward_id TEXT,
            prime_award_id TEXT,
            contract_id TEXT,
            prime_name TEXT,
            prime_uei TEXT,
            sub_recipient_name TEXT,
            sub_recipient_uei TEXT,
            subaward_amount REAL,
            subaward_date TEXT,
            subaward_description TEXT,
            awarding_agency TEXT,
            fiscal_year TEXT,
            is_competitor INTEGER,
            competitor_match TEXT,
            extraction_date TEXT,
            source_file TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # =========================================
    # TABLE 5: CONTACTS
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            title TEXT,
            company TEXT,
            email TEXT,
            phone TEXT,
            linkedin TEXT,
            program TEXT,
            tier INTEGER,
            contact_type TEXT,
            bd_priority TEXT,
            relationship_status TEXT,
            relationship_score REAL,
            is_hiring_manager INTEGER,
            has_open_reqs INTEGER,
            is_decision_maker INTEGER,
            clearances TEXT,
            locations TEXT,
            note_count INTEGER,
            last_activity TEXT,
            first_activity TEXT,
            last_contact_date TEXT,
            next_outreach_date TEXT,
            hiring_signals TEXT,
            pain_points TEXT,
            recent_note TEXT,
            notes TEXT,
            associated_primes TEXT,
            associated_programs TEXT,
            inferred_role_level TEXT,
            aggregated_summary TEXT,
            source_db TEXT,
            matched_program_id TEXT,
            matched_jobs TEXT,
            source_files TEXT,
            data_quality_score REAL,
            community_id INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # =========================================
    # TABLE 6: JOBS
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            job_number TEXT,
            title TEXT NOT NULL,
            company TEXT,
            prime TEXT,
            location TEXT,
            date_posted TEXT,
            duration TEXT,
            employment_type TEXT,
            status TEXT,
            clearance TEXT,
            description TEXT,
            experience_years TEXT,
            skills TEXT,
            technologies TEXT,
            certifications_required TEXT,
            certifications_extra TEXT,
            subcontractors TEXT,
            task_order TEXT,
            hiring_leader TEXT,
            program_manager TEXT,
            pts_past_programs TEXT,
            pts_past_jobs TEXT,
            pts_past_contractors TEXT,
            pts_past_contacts TEXT,
            pay_rate REAL,
            bill_rate REAL,
            salary REAL,
            url TEXT,
            scraped_at TEXT,
            matched_program TEXT,
            matched_program_id TEXT,
            linked_prime TEXT,
            owner TEXT,
            contact TEXT,
            source_file TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # =========================================
    # TABLE 7: PLACEMENTS
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS placements (
            id TEXT PRIMARY KEY,
            bullhorn_placement_id TEXT,
            job_id TEXT,
            candidate_id TEXT,
            bullhorn_job_id TEXT,
            bullhorn_candidate_id TEXT,
            placement_date TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT,
            outcome TEXT,
            pay_rate REAL,
            bill_rate REAL,
            salary REAL,
            spread REAL,
            flat_fee REAL,
            estimated_revenue REAL,
            commission REAL,
            duration_days INTEGER,
            client_name TEXT,
            job_title TEXT,
            candidate_name TEXT,
            owner TEXT,
            program_name TEXT,
            source_file TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # =========================================
    # TABLE 8: ACTIVITIES (call notes)
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id TEXT PRIMARY KEY,
            bullhorn_activity_id TEXT,
            activity_type TEXT,
            action TEXT,
            about TEXT,
            about_contact_id TEXT,
            activity_date TEXT,
            actor TEXT,
            note_text TEXT,
            comments TEXT,
            hiring_signal INTEGER,
            positive_response INTEGER,
            traction INTEGER,
            programs_mentioned TEXT,
            primes_mentioned TEXT,
            locations TEXT,
            source_file TEXT,
            sentiment_score REAL,
            has_hiring_signal INTEGER DEFAULT 0,
            priority TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # =========================================
    # TABLE 9: INTELLIGENCE
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS intelligence (
            id TEXT PRIMARY KEY,
            intel_type TEXT,
            program_name TEXT,
            program_id TEXT,
            company_name TEXT,
            company_id TEXT,
            piid TEXT,
            bd_score REAL,
            bd_reasons TEXT,
            priority_tier TEXT,
            lifecycle_phase TEXT,
            is_base_year INTEGER,
            runway_years REAL,
            award_amount REAL,
            description TEXT,
            awarding_agency TEXT,
            sub_agency TEXT,
            naics_code TEXT,
            psc_code TEXT,
            pop_city TEXT,
            pop_state TEXT,
            start_date TEXT,
            end_date TEXT,
            days_until_end INTEGER,
            competitors TEXT,
            competitor_present INTEGER,
            hiring_activity TEXT,
            matched_jobs TEXT,
            gap_analysis_notes TEXT,
            relationship_tier TEXT,
            narrative TEXT,
            entity_type TEXT,
            entity_properties TEXT,
            source TEXT,
            source_file TEXT,
            data_quality_score REAL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # =========================================
    # TABLE 10: DOCUMENTS
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            doc_type TEXT,
            title TEXT NOT NULL,
            file_path TEXT,
            content TEXT,
            program_name TEXT,
            program_id TEXT,
            company_name TEXT,
            entity_type TEXT,
            entity_properties TEXT,
            source TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # =========================================
    # TABLE 11: TIMELINES (derived)
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timelines (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            event_date TEXT,
            program_id TEXT,
            program_name TEXT,
            contract_id TEXT,
            piid TEXT,
            description TEXT,
            days_until_event INTEGER,
            urgency TEXT,
            source TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # =========================================
    # TABLE 12: SCORING (derived)
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scoring (
            id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id TEXT,
            entity_name TEXT,
            bd_score REAL,
            priority_tier TEXT,
            match_confidence REAL,
            engagement_score REAL,
            job_activity_score REAL,
            contract_score REAL,
            contact_access_score REAL,
            recompete_proximity_score REAL,
            composite_score REAL,
            scoring_details TEXT,
            source TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # =========================================
    # TABLE 13: PROGRAM_CONTACTS (junction M:M)
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS program_contacts (
            id TEXT PRIMARY KEY,
            program_id TEXT NOT NULL,
            contact_id TEXT NOT NULL,
            relationship_type TEXT,
            source TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(program_id, contact_id)
        )
    """)

    # =========================================
    # TABLE 14: PROGRAM_COMPANIES (junction M:M)
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS program_companies (
            id TEXT PRIMARY KEY,
            program_id TEXT NOT NULL,
            company_id TEXT NOT NULL,
            role TEXT,
            source TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(program_id, company_id, role)
        )
    """)

    # =========================================
    # TABLE 15: ETL_RUNS (metadata)
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etl_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            run_type TEXT,
            started_at TEXT,
            completed_at TEXT,
            tables_loaded TEXT,
            total_records INTEGER,
            errors INTEGER,
            status TEXT,
            details TEXT
        )
    """)

    # =========================================
    # TABLE 16: SOURCE_TRACKING (metadata)
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            record_id TEXT NOT NULL,
            source_file TEXT,
            source_type TEXT,
            record_hash TEXT,
            first_loaded TEXT DEFAULT (datetime('now')),
            last_updated TEXT DEFAULT (datetime('now')),
            UNIQUE(table_name, record_id, source_file)
        )
    """)

    # =========================================
    # INDEXES
    # =========================================
    indexes = [
        ("idx_programs_name", "programs", "program_name"),
        ("idx_programs_acronym", "programs", "acronym"),
        ("idx_programs_agency", "programs", "agency_owner"),
        ("idx_programs_prime", "programs", "prime_contractor"),
        ("idx_companies_name", "companies", "name"),
        ("idx_companies_normalized", "companies", "normalized_name"),
        ("idx_companies_uei", "companies", "uei"),
        ("idx_companies_cage", "companies", "cage_code"),
        ("idx_contracts_piid", "contracts", "piid"),
        ("idx_contracts_program", "contracts", "program_id"),
        ("idx_contracts_recipient", "contracts", "recipient_name"),
        ("idx_contracts_agency", "contracts", "awarding_agency"),
        ("idx_task_orders_prime_award", "task_orders", "prime_award_id"),
        ("idx_task_orders_sub_recipient", "task_orders", "sub_recipient_name"),
        ("idx_contacts_name", "contacts", "full_name"),
        ("idx_contacts_email", "contacts", "email"),
        ("idx_contacts_company", "contacts", "company"),
        ("idx_contacts_tier", "contacts", "tier"),
        ("idx_contacts_program", "contacts", "program"),
        ("idx_jobs_number", "jobs", "job_number"),
        ("idx_jobs_company", "jobs", "company"),
        ("idx_jobs_program", "jobs", "matched_program"),
        ("idx_placements_job", "placements", "job_id"),
        ("idx_placements_candidate", "placements", "candidate_id"),
        ("idx_activities_date", "activities", "activity_date"),
        ("idx_activities_about", "activities", "about"),
        ("idx_intelligence_program", "intelligence", "program_id"),
        ("idx_intelligence_type", "intelligence", "intel_type"),
        ("idx_intelligence_score", "intelligence", "bd_score"),
        ("idx_timelines_date", "timelines", "event_date"),
        ("idx_timelines_program", "timelines", "program_id"),
        ("idx_timelines_urgency", "timelines", "urgency"),
        ("idx_scoring_entity", "scoring", "entity_id"),
        ("idx_scoring_type", "scoring", "entity_type"),
        ("idx_pc_program", "program_contacts", "program_id"),
        ("idx_pc_contact", "program_contacts", "contact_id"),
        ("idx_pco_program", "program_companies", "program_id"),
        ("idx_pco_company", "program_companies", "company_id"),
        ("idx_source_tracking_table", "source_tracking", "table_name"),
        ("idx_source_tracking_record", "source_tracking", "record_id"),
    ]

    for idx_name, table, column in indexes:
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})"
        )

    # =========================================
    # VIEWS
    # =========================================
    _create_views(cursor)

    conn.commit()
    conn.close()
    print(f"Database created at: {db_path}")
    return db_path


def _create_views(cursor):
    """Create aggregation views."""

    # VIEW 1: program_360_view
    cursor.execute("DROP VIEW IF EXISTS program_360_view")
    cursor.execute("""
        CREATE VIEW program_360_view AS
        SELECT
            p.id AS program_id,
            p.program_name,
            p.acronym,
            p.agency_owner,
            p.prime_contractor,
            p.contract_value_consolidated,
            p.total_contract_value,
            p.pop_start_consolidated,
            p.pop_end_consolidated,
            p.recompete_date,
            p.clearance_requirements,
            p.technical_stack,
            p.priority_level,
            (SELECT COUNT(*) FROM program_contacts pc WHERE pc.program_id = p.id) AS contact_count,
            (SELECT COUNT(*) FROM program_companies pco WHERE pco.program_id = p.id) AS company_count,
            (SELECT COUNT(*) FROM jobs j WHERE j.matched_program_id = p.id) AS job_count,
            (SELECT COUNT(*) FROM placements pl
             JOIN program_contacts pc2 ON pc2.contact_id = pl.candidate_id
             WHERE pc2.program_id = p.id) AS placement_count,
            (SELECT COUNT(*) FROM contracts c WHERE c.program_id = p.id) AS contract_count,
            (SELECT COUNT(*) FROM intelligence i WHERE i.program_id = p.id) AS intel_count,
            (SELECT MIN(t.event_date) FROM timelines t
             WHERE t.program_id = p.id AND t.event_date > date('now')) AS next_event_date,
            (SELECT t.event_type FROM timelines t
             WHERE t.program_id = p.id AND t.event_date > date('now')
             ORDER BY t.event_date LIMIT 1) AS next_event_type,
            (SELECT s.composite_score FROM scoring s
             WHERE s.entity_id = p.id AND s.entity_type = 'program') AS bd_score
        FROM programs p
    """)

    # VIEW 2: bd_pipeline_view
    cursor.execute("DROP VIEW IF EXISTS bd_pipeline_view")
    cursor.execute("""
        CREATE VIEW bd_pipeline_view AS
        SELECT
            p.id AS program_id,
            p.program_name,
            p.acronym,
            p.agency_owner,
            p.prime_contractor,
            p.total_contract_value,
            p.recompete_date,
            CASE
                WHEN s.composite_score >= 70 THEN 'Hot'
                WHEN s.composite_score >= 40 THEN 'Warm'
                ELSE 'Cold'
            END AS pipeline_tier,
            s.composite_score AS bd_score,
            s.contact_access_score,
            s.recompete_proximity_score,
            (SELECT COUNT(*) FROM program_contacts pc WHERE pc.program_id = p.id) AS contact_access,
            (SELECT SUM(pl.estimated_revenue) FROM placements pl
             JOIN program_contacts pc2 ON pc2.contact_id = pl.candidate_id
             WHERE pc2.program_id = p.id) AS revenue,
            (SELECT julianday(MIN(t.event_date)) - julianday('now')
             FROM timelines t WHERE t.program_id = p.id
             AND t.event_type IN ('recompete', 'pop_end')
             AND t.event_date > date('now')) AS days_to_recompete
        FROM programs p
        LEFT JOIN scoring s ON s.entity_id = p.id AND s.entity_type = 'program'
    """)

    # VIEW 3: revenue_by_program
    cursor.execute("DROP VIEW IF EXISTS revenue_by_program")
    cursor.execute("""
        CREATE VIEW revenue_by_program AS
        SELECT
            p.id AS program_id,
            p.program_name,
            p.acronym,
            COUNT(DISTINCT pl.id) AS placement_count,
            AVG(pl.bill_rate) AS avg_bill_rate,
            AVG(pl.pay_rate) AS avg_pay_rate,
            AVG(pl.spread) AS avg_spread,
            SUM(pl.estimated_revenue) AS estimated_gross_revenue
        FROM programs p
        JOIN placement_program_links ppl ON ppl.program_id = p.id
        JOIN placements pl ON pl.id = ppl.placement_id
        GROUP BY p.id, p.program_name, p.acronym
    """)

    # For revenue_by_program, we need the placement_program_links helper
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS placement_program_links (
            placement_id TEXT,
            program_id TEXT,
            program_name TEXT,
            source TEXT,
            PRIMARY KEY (placement_id, program_id)
        )
    """)

    # VIEW 4: contact_network_view
    cursor.execute("DROP VIEW IF EXISTS contact_network_view")
    cursor.execute("""
        CREATE VIEW contact_network_view AS
        SELECT
            p.id AS program_id,
            p.program_name,
            c.id AS contact_id,
            c.full_name,
            c.title,
            c.company,
            c.tier,
            c.email,
            c.relationship_status,
            c.bd_priority,
            c.last_activity,
            CAST(julianday('now') - julianday(c.last_activity) AS INTEGER) AS days_since_activity,
            c.note_count,
            c.is_decision_maker,
            c.is_hiring_manager
        FROM program_contacts pc
        JOIN programs p ON p.id = pc.program_id
        JOIN contacts c ON c.id = pc.contact_id
    """)

    # VIEW 5: recompete_calendar
    cursor.execute("DROP VIEW IF EXISTS recompete_calendar")
    cursor.execute("""
        CREATE VIEW recompete_calendar AS
        SELECT
            t.id AS timeline_id,
            t.event_type,
            t.event_date,
            t.days_until_event,
            t.urgency,
            p.id AS program_id,
            p.program_name,
            p.acronym,
            p.prime_contractor,
            p.total_contract_value,
            (SELECT s.composite_score FROM scoring s
             WHERE s.entity_id = p.id AND s.entity_type = 'program') AS readiness_score,
            (SELECT COUNT(*) FROM program_contacts pc WHERE pc.program_id = p.id) AS contact_count
        FROM timelines t
        JOIN programs p ON p.id = t.program_id
        WHERE t.event_type IN ('recompete', 'pop_end', 'option_year', 'ultimate_completion')
        AND t.event_date > date('now')
    """)

    # VIEW 6: competitive_landscape
    cursor.execute("DROP VIEW IF EXISTS competitive_landscape")
    cursor.execute("""
        CREATE VIEW competitive_landscape AS
        SELECT
            co.id AS company_id,
            co.name AS company_name,
            co.normalized_name,
            co.relationship_tier,
            (SELECT COUNT(*) FROM program_companies pco
             WHERE pco.company_id = co.id AND pco.role = 'prime') AS programs_primed,
            (SELECT COUNT(*) FROM program_companies pco
             WHERE pco.company_id = co.id AND pco.role = 'sub') AS programs_subbed,
            (SELECT COUNT(*) FROM program_companies pco
             WHERE pco.company_id = co.id) AS total_program_roles,
            co.contract_count,
            co.total_award_amount,
            co.usaspending_total_obligated,
            (SELECT COUNT(*) FROM task_orders t
             WHERE t.sub_recipient_name = co.name
             OR t.sub_recipient_name = co.normalized_name) AS subaward_count,
            (SELECT SUM(t.subaward_amount) FROM task_orders t
             WHERE t.sub_recipient_name = co.name
             OR t.sub_recipient_name = co.normalized_name) AS subaward_total
        FROM companies co
    """)


def get_connection(db_path: Path = None) -> sqlite3.Connection:
    """Get database connection with row factory."""
    db_path = db_path or DATABASE_PATH
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_table_counts(db_path: Path = None) -> dict:
    """Get record counts for all tables."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    tables = [
        "programs", "companies", "contracts", "task_orders",
        "contacts", "jobs", "placements", "activities",
        "intelligence", "documents", "timelines", "scoring",
        "program_contacts", "program_companies", "etl_runs", "source_tracking",
        "placement_program_links",
    ]
    counts = {}
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            counts[table] = -1
    conn.close()
    return counts


if __name__ == "__main__":
    create_database()
    print("\nTable counts:")
    for table, count in get_table_counts().items():
        print(f"  {table}: {count}")
