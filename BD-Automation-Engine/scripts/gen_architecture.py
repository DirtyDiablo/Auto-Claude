#!/usr/bin/env python3
"""
BD-Engine Data Architecture Generator
======================================

Programmatically generates data_architecture_bd_engine.json from the
existing V3 hand-built architecture, preserving all 40 entities,
65 relationships, 18 data flows, and full database/engine/dify sections.

Usage:
    py scripts/gen_architecture.py

Output:
    data_architecture_bd_engine.json (root of BD-Automation-Engine)
"""

import json
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_architecture() -> dict:
    arch = {
        "project_id": "BD_ENGINE",
        "scan_date": datetime.now().strftime("%Y-%m-%d"),
        "scan_version": "3.0",
        "project_info": {
            "path": "BD-Automation-Engine/",
            "description": "PTS BD Intelligence System - 8-engine pipeline for federal defense BD automation targeting DCGS portfolio (~$950M)",
            "files_scanned": 4221,
            "file_types_found": {
                "python": 1190,
                "typescript": 888,
                "csv": 814,
                "json": 460,
                "markdown": 523,
                "other": 346,
            },
        },
        "scan_stats": {},  # computed at end
        "entities": _build_entities(),
        "relationships": _build_relationships(),
        "data_flows": _build_data_flows(),
        "databases": _build_databases(),
        "engines": _build_engines(),
        "dify_tools": _build_dify_tools(),
        "cross_project_references": {
            "data_scraper": "Provides enrichment data (Tango SDK, SAM.gov, FPDS, USASpending) that feeds into qdrant:federal_contracts and neo4j:Contract",
            "n8n_builder": "Orchestrates workflows (job scraping, contact enrichment, notification delivery) that trigger Engine8 API endpoints",
        },
    }

    # Compute scan stats
    entities = arch["entities"]
    total_props = sum(len(e.get("properties", [])) for e in entities)
    total_aliases = sum(len(e.get("aliases", [])) for e in entities)

    arch["scan_stats"] = {
        "files_scanned": 4221,
        "entities_found": len(entities),
        "properties_found": total_props,
        "relationships_found": len(arch["relationships"]),
        "aliases_found": total_aliases,
        "data_flows_found": len(arch["data_flows"]),
        "qdrant_collections_documented": len(arch["databases"]["qdrant_collections"]),
        "sqlite_databases_documented": len(arch["databases"]["sqlite_databases"]),
        "sqlite_tables_documented": sum(
            len(db.get("tables", [])) for db in arch["databases"]["sqlite_databases"]
        ),
        "neo4j_node_types": len(arch["databases"]["neo4j_graph"]["node_types"]),
        "neo4j_relationship_types": len(
            arch["databases"]["neo4j_graph"]["relationship_types"]
        ),
        "notion_databases_documented": len(arch["databases"]["notion_databases"]),
        "dashboard_feeds_documented": 25,
        "api_endpoints_documented": 340,
        "api_models_documented": 120,
        "engines_documented": len(arch["engines"]),
        "ai_agents_documented": 13,
        "ai_crews_documented": 3,
        "mcp_tools_documented": 32,
        "dify_tools_documented": len(arch["dify_tools"]),
        "streaming_schemas_documented": len(arch["databases"]["streaming_schemas"]),
        "src_api_routers": 32,
        "engine8_sub_routers": 28,
    }

    return arch


# =============================================================================
# ENTITIES
# =============================================================================


def _build_entities() -> list:
    return [
        _entity_contact(),
        _entity_program(),
        _entity_job(),
        _entity_placement(),
        _entity_activity(),
        _entity_prime_contractor(),
        _entity_document(),
        _entity_past_performance(),
        _entity_federal_contract(),
        _entity_contract_opportunity(),
        _entity_intelligence_report(),
        _entity_bullhorn_note(),
        _entity_memory(),
        _entity_interaction(),
        _entity_insight(),
        _entity_graph_entity(),
        _entity_graph_relationship(),
        _entity_source_file(),
        _entity_data_quality_log(),
        _entity_processing_stats(),
        _entity_location(),
        _entity_notification(),
        _entity_alert(),
        _entity_contract_watch(),
        _entity_weekly_report(),
        _entity_call_briefing(),
        _entity_transcript_intel(),
        _entity_relationship_score(),
        _entity_win_probability(),
        _entity_hiring_forecast(),
        _entity_recompete_prediction(),
        _entity_revenue_placement(),
        _entity_swarm_task(),
        _entity_workflow_run(),
        _entity_contact_claim(),
        _entity_strategic_pattern(),
        _entity_proposal_artifact(),
        _entity_streaming_event(),
        _entity_file_node(),
        _entity_process_node(),
    ]


def _entity_contact():
    return {
        "name": "CONTACT",
        "pk": "id",
        "records": "7337",
        "category": "BD Intelligence",
        "description": "BD contacts with tier classification (1-6), program affiliation, and clearance data from Bullhorn CRM",
        "sources": ["Bullhorn CRM", "Engine3_OrgChart", "Engine5_Scoring", "Qdrant"],
        "storage": [
            "qdrant:contacts",
            "sqlite:bullhorn_master.db/candidates",
            "neo4j:Person",
        ],
        "properties": [
            {
                "name": "id",
                "type": "string",
                "source": "bullhorn",
                "note": "Bullhorn candidate ID",
            },
            {"name": "first_name", "type": "string", "source": "bullhorn"},
            {"name": "last_name", "type": "string", "source": "bullhorn"},
            {
                "name": "full_name",
                "type": "string",
                "source": "derived",
                "note": "COALESCE(full_name, first+last)",
            },
            {
                "name": "name",
                "type": "string",
                "source": "qdrant",
                "note": "Display name in vector store",
            },
            {
                "name": "title",
                "type": "string",
                "source": "bullhorn",
                "note": "Job/position title",
            },
            {
                "name": "company",
                "type": "string",
                "source": "bullhorn",
                "note": "COALESCE(company_name, current_employer)",
            },
            {
                "name": "program",
                "type": "string",
                "source": "engine3",
                "note": "Matched federal program",
            },
            {"name": "email", "type": "string", "source": "bullhorn"},
            {
                "name": "phone",
                "type": "string",
                "source": "bullhorn",
                "note": "COALESCE(phone, mobile)",
            },
            {"name": "mobile", "type": "string", "source": "bullhorn"},
            {"name": "linkedin_url", "type": "string", "source": "bullhorn"},
            {"name": "address", "type": "string", "source": "bullhorn"},
            {"name": "city", "type": "string", "source": "bullhorn"},
            {"name": "state", "type": "string", "source": "bullhorn"},
            {"name": "zip_code", "type": "string", "source": "bullhorn"},
            {
                "name": "tier",
                "type": "string",
                "source": "engine3",
                "example": "Tier 1",
                "note": "Computed by classify_tier()",
            },
            {
                "name": "hierarchy_tier",
                "type": "string",
                "source": "engine3",
                "values": [
                    "Tier 1 - Executive",
                    "Tier 2 - Director",
                    "Tier 3 - Program Leadership",
                    "Tier 4 - Management",
                    "Tier 5 - Senior IC",
                    "Tier 6 - Individual Contributor",
                ],
            },
            {
                "name": "bd_priority",
                "type": "string",
                "source": "engine5",
                "values": ["Critical", "High", "Medium", "Standard"],
            },
            {
                "name": "clearance_level",
                "type": "string",
                "source": "bullhorn",
                "values": [
                    "TS/SCI w/ Full Scope Poly",
                    "TS/SCI w/ CI Poly",
                    "TS/SCI w/ Poly",
                    "TS/SCI",
                    "Top Secret",
                    "Secret",
                    "Public Trust",
                    "None",
                ],
            },
            {
                "name": "location_hub",
                "type": "string",
                "source": "engine3",
                "values": [
                    "Hampton Roads",
                    "San Diego Metro",
                    "DC Metro",
                    "Dayton/Wright-Patt",
                    "OCONUS",
                    "Other CONUS",
                ],
            },
            {
                "name": "outreach_sequence",
                "type": "string",
                "source": "engine3",
                "note": "A-D outreach tier",
            },
            {"name": "functional_area", "type": "string", "source": "neo4j"},
            {"name": "status", "type": "string", "source": "bullhorn"},
            {"name": "occupation", "type": "string", "source": "bullhorn"},
            {"name": "current_employer", "type": "string", "source": "bullhorn"},
            {"name": "skills", "type": "string", "source": "bullhorn"},
            {"name": "owner", "type": "string", "source": "bullhorn"},
            {
                "name": "notes",
                "type": "text",
                "source": "bullhorn",
                "note": "custom_text1",
            },
            {
                "name": "source",
                "type": "string",
                "source": "bullhorn",
                "note": "source_file",
            },
            {
                "name": "source_db",
                "type": "string",
                "source": "etl",
                "example": "bullhorn_master",
            },
            {"name": "date_added", "type": "datetime", "source": "bullhorn"},
            {"name": "date_modified", "type": "datetime", "source": "bullhorn"},
            {"name": "last_activity_date", "type": "datetime", "source": "bullhorn"},
            {"name": "_indexed_at", "type": "string", "source": "qdrant_meta"},
            {
                "name": "_embedding_model",
                "type": "string",
                "source": "qdrant_meta",
                "example": "text-embedding-3-small",
            },
        ],
        "aliases": [
            {
                "canonical": "company",
                "alias": "current_employer",
                "source": "Bullhorn CSV",
            },
            {"canonical": "company", "alias": "company_name", "source": "Bullhorn DB"},
            {"canonical": "phone", "alias": "mobile", "source": "Bullhorn CSV"},
            {"canonical": "title", "alias": "job_title", "source": "Bullhorn DB"},
            {
                "canonical": "linkedin_url",
                "alias": "linkedin",
                "source": "Qdrant payload",
            },
            {
                "canonical": "id",
                "alias": "bullhorn_candidate_id",
                "source": "Bullhorn DB",
            },
            {"canonical": "id", "alias": "contact_id", "source": "API response"},
            {
                "canonical": "tier",
                "alias": "hierarchy_tier",
                "source": "Engine3 output",
            },
            {"canonical": "notes", "alias": "custom_text1", "source": "Bullhorn DB"},
            {"canonical": "program", "alias": "custom_text3", "source": "Bullhorn DB"},
        ],
    }


def _entity_program():
    return {
        "name": "PROGRAM",
        "pk": "id",
        "records": "401",
        "category": "Federal Awards",
        "description": "Federal programs and contracts (DCGS portfolio, DoD, IC) with prime/sub relationships",
        "sources": [
            "Bullhorn CRM",
            "Federal Programs CSV",
            "Engine2_ProgramMapping",
            "Qdrant",
        ],
        "storage": [
            "qdrant:programs",
            "sqlite:bullhorn_master.db/programs",
            "neo4j:Program",
            "csv:Federal_Programs_MASTER_V4.csv",
        ],
        "properties": [
            {"name": "id", "type": "integer", "source": "sqlite"},
            {"name": "name", "type": "string", "source": "multiple"},
            {"name": "normalized_name", "type": "string", "source": "etl"},
            {"name": "acronym", "type": "string", "source": "multiple"},
            {"name": "prime_contractor", "type": "string", "source": "multiple"},
            {"name": "prime_contractor_id", "type": "integer", "source": "sqlite_fk"},
            {
                "name": "agency",
                "type": "string",
                "source": "multiple",
                "note": "Agency Owner",
            },
            {"name": "sub_agency", "type": "string", "source": "sqlite"},
            {"name": "program_type", "type": "string", "source": "csv"},
            {"name": "location", "type": "string", "source": "multiple"},
            {
                "name": "key_locations",
                "type": "list[str]",
                "source": "csv",
                "note": "Semicolon-separated",
            },
            {"name": "mission_area", "type": "string", "source": "qdrant"},
            {"name": "contract_value", "type": "decimal", "source": "multiple"},
            {"name": "contract_number", "type": "string", "source": "sqlite"},
            {"name": "contract_vehicle", "type": "string", "source": "qdrant"},
            {"name": "period_of_performance", "type": "string", "source": "sqlite"},
            {"name": "pop_start", "type": "date", "source": "neo4j"},
            {"name": "pop_end", "type": "date", "source": "neo4j"},
            {"name": "clearance_req", "type": "string", "source": "neo4j"},
            {
                "name": "keywords",
                "type": "list[str]",
                "source": "csv",
                "note": "Keywords/Signals",
            },
            {"name": "typical_roles", "type": "list[str]", "source": "csv"},
            {"name": "priority_level", "type": "string", "source": "csv"},
            {"name": "pts_involvement", "type": "string", "source": "notion"},
            {
                "name": "bd_priority",
                "type": "string",
                "source": "engine5",
                "values": ["Critical", "High", "Medium", "Low"],
            },
            {
                "name": "hiring_velocity",
                "type": "string",
                "source": "neo4j",
                "values": ["High", "Medium", "Low", "None"],
            },
            {"name": "confidence_level", "type": "string", "source": "neo4j"},
            {"name": "recompete_date", "type": "date", "source": "neo4j"},
            {"name": "naics", "type": "string", "source": "neo4j"},
            {"name": "description", "type": "text", "source": "sqlite"},
            {"name": "total_jobs", "type": "integer", "source": "sqlite"},
            {"name": "total_placements", "type": "integer", "source": "sqlite"},
            {"name": "total_revenue", "type": "decimal", "source": "sqlite"},
            {"name": "status", "type": "string", "source": "multiple"},
            {"name": "_indexed_at", "type": "string", "source": "qdrant_meta"},
            {"name": "_embedding_model", "type": "string", "source": "qdrant_meta"},
        ],
        "aliases": [
            {"canonical": "name", "alias": "Program Name", "source": "Notion/CSV"},
            {"canonical": "agency", "alias": "Agency Owner", "source": "CSV"},
            {
                "canonical": "prime_contractor",
                "alias": "Prime Contractor",
                "source": "Notion",
            },
            {
                "canonical": "clearance_req",
                "alias": "Clearance Requirements",
                "source": "CSV",
            },
            {"canonical": "contract_value", "alias": "value", "source": "API"},
            {"canonical": "pop_start", "alias": "start_date", "source": "SQLite"},
            {"canonical": "pop_end", "alias": "end_date", "source": "SQLite"},
        ],
    }


def _entity_job():
    return {
        "name": "JOB",
        "pk": "id",
        "records": "968",
        "category": "BD Intelligence",
        "description": "Job postings from Apify scraper and Bullhorn CRM with BD scores and program mappings",
        "sources": [
            "Apify Scraper",
            "Bullhorn CRM",
            "Engine2_ProgramMapping",
            "Engine5_Scoring",
        ],
        "storage": ["qdrant:jobs", "sqlite:bullhorn_master.db/jobs", "neo4j:Job"],
        "properties": [
            {"name": "id", "type": "string", "source": "multiple"},
            {"name": "bullhorn_job_id", "type": "string", "source": "bullhorn"},
            {"name": "job_number", "type": "string", "source": "bullhorn"},
            {"name": "title", "type": "string", "source": "multiple"},
            {"name": "company", "type": "string", "source": "multiple"},
            {"name": "client_corporation", "type": "string", "source": "bullhorn"},
            {"name": "prime_contractor", "type": "string", "source": "bullhorn"},
            {"name": "location", "type": "string", "source": "multiple"},
            {"name": "city", "type": "string", "source": "bullhorn"},
            {"name": "state", "type": "string", "source": "bullhorn"},
            {"name": "clearance", "type": "string", "source": "scraper"},
            {"name": "clearance_required", "type": "string", "source": "bullhorn"},
            {"name": "mapped_program", "type": "string", "source": "engine2"},
            {
                "name": "match_confidence",
                "type": "float",
                "source": "engine2",
                "note": "0.0-1.0",
            },
            {
                "name": "match_type",
                "type": "string",
                "source": "engine2",
                "values": ["direct", "fuzzy", "inferred"],
            },
            {
                "name": "bd_priority_score",
                "type": "integer",
                "source": "engine5",
                "note": "0-100",
            },
            {
                "name": "priority_tier",
                "type": "string",
                "source": "engine5",
                "values": ["Hot", "Warm", "Cold"],
            },
            {"name": "match_signals", "type": "list[str]", "source": "engine2"},
            {
                "name": "pipeline_stage",
                "type": "string",
                "source": "api",
                "values": [
                    "scraped",
                    "mapped",
                    "contacts_found",
                    "outreach_active",
                    "meeting_set",
                    "req_obtained",
                ],
            },
            {"name": "description", "type": "text", "source": "multiple"},
            {"name": "skills", "type": "text", "source": "bullhorn"},
            {
                "name": "employment_type",
                "type": "string",
                "source": "bullhorn",
                "values": ["Full-Time", "Contract", "Contract-to-Hire", "Part-Time"],
            },
            {"name": "status", "type": "string", "source": "bullhorn"},
            {"name": "pay_rate", "type": "decimal", "source": "bullhorn"},
            {"name": "bill_rate", "type": "decimal", "source": "bullhorn"},
            {"name": "salary", "type": "decimal", "source": "bullhorn"},
            {"name": "source", "type": "string", "source": "scraper"},
            {"name": "source_url", "type": "string", "source": "scraper"},
            {"name": "owner", "type": "string", "source": "bullhorn"},
            {"name": "contact", "type": "string", "source": "bullhorn"},
            {"name": "date_added", "type": "datetime", "source": "bullhorn"},
            {"name": "date_posted", "type": "string", "source": "scraper"},
            {"name": "date_closed", "type": "datetime", "source": "bullhorn"},
            {"name": "scraped_at", "type": "string", "source": "scraper"},
            {"name": "_indexed_at", "type": "string", "source": "qdrant_meta"},
            {"name": "_embedding_model", "type": "string", "source": "qdrant_meta"},
        ],
        "aliases": [
            {
                "canonical": "company",
                "alias": "client_corporation",
                "source": "Bullhorn DB",
            },
            {
                "canonical": "clearance",
                "alias": "clearance_required",
                "source": "Bullhorn DB",
            },
            {
                "canonical": "clearance",
                "alias": "detected_clearance",
                "source": "API v2",
            },
            {"canonical": "clearance", "alias": "Security Clearance", "source": "CSV"},
            {
                "canonical": "mapped_program",
                "alias": "program_name",
                "source": "Engine2",
            },
            {
                "canonical": "mapped_program",
                "alias": "Matched Program",
                "source": "CSV",
            },
            {
                "canonical": "bd_priority_score",
                "alias": "bd_score",
                "source": "Engine5",
            },
            {
                "canonical": "bd_priority_score",
                "alias": "BD Priority Score",
                "source": "CSV/Notion",
            },
        ],
    }


def _entity_placement():
    return {
        "name": "PLACEMENT",
        "pk": "id",
        "records": "616",
        "category": "BD Intelligence",
        "description": "Placements linking jobs to candidates with financial data (bill/pay rates, revenue)",
        "sources": ["Bullhorn CRM"],
        "storage": ["sqlite:bullhorn_master.db/placements"],
        "properties": [
            {"name": "id", "type": "integer", "source": "sqlite"},
            {"name": "bullhorn_placement_id", "type": "string", "source": "bullhorn"},
            {"name": "job_id", "type": "integer", "source": "sqlite_fk"},
            {"name": "candidate_id", "type": "integer", "source": "sqlite_fk"},
            {"name": "placement_date", "type": "date", "source": "bullhorn"},
            {"name": "start_date", "type": "date", "source": "bullhorn"},
            {"name": "end_date", "type": "date", "source": "bullhorn"},
            {"name": "status", "type": "string", "source": "bullhorn"},
            {"name": "outcome", "type": "string", "source": "bullhorn"},
            {"name": "pay_rate", "type": "decimal", "source": "bullhorn"},
            {"name": "bill_rate", "type": "decimal", "source": "bullhorn"},
            {"name": "salary", "type": "decimal", "source": "bullhorn"},
            {"name": "commission", "type": "decimal", "source": "bullhorn"},
            {"name": "duration_days", "type": "integer", "source": "derived"},
            {"name": "client_name", "type": "string", "source": "bullhorn"},
            {"name": "job_title", "type": "string", "source": "bullhorn"},
            {"name": "candidate_name", "type": "string", "source": "bullhorn"},
            {"name": "owner", "type": "string", "source": "bullhorn"},
        ],
        "aliases": [
            {"canonical": "placement", "alias": "assignment", "source": "general"},
            {"canonical": "placement", "alias": "engagement", "source": "general"},
        ],
    }


def _entity_activity():
    return {
        "name": "ACTIVITY",
        "pk": "id",
        "records": "500",
        "category": "BD Intelligence",
        "description": "CRM activities, call notes, meeting records, and interaction logs",
        "sources": ["Bullhorn CRM"],
        "storage": ["qdrant:activities", "sqlite:bullhorn_master.db/activities"],
        "properties": [
            {
                "name": "id",
                "type": "string",
                "source": "qdrant",
                "note": "Format: activity_{row_id}",
            },
            {"name": "bullhorn_activity_id", "type": "string", "source": "bullhorn"},
            {"name": "activity_type", "type": "string", "source": "bullhorn"},
            {"name": "action", "type": "string", "source": "bullhorn"},
            {
                "name": "content",
                "type": "text",
                "source": "qdrant_embedding",
                "note": "From comments",
            },
            {
                "name": "subject",
                "type": "string",
                "source": "qdrant",
                "note": "From note_text",
            },
            {
                "name": "date",
                "type": "datetime",
                "source": "bullhorn",
                "note": "activity_date",
            },
            {"name": "contact_id", "type": "string", "source": "qdrant"},
            {"name": "job_id", "type": "string", "source": "qdrant"},
            {"name": "related_job_id", "type": "integer", "source": "sqlite_fk"},
            {"name": "related_candidate_id", "type": "integer", "source": "sqlite_fk"},
            {"name": "actor", "type": "string", "source": "bullhorn"},
            {"name": "note_text", "type": "text", "source": "bullhorn"},
            {"name": "comments", "type": "text", "source": "bullhorn"},
            {"name": "follow_up_required", "type": "boolean", "source": "bullhorn"},
            {"name": "follow_up_date", "type": "date", "source": "bullhorn"},
            {"name": "status", "type": "string", "source": "bullhorn"},
            {
                "name": "source_db",
                "type": "string",
                "source": "etl",
                "example": "bullhorn_master",
            },
            {"name": "_indexed_at", "type": "string", "source": "qdrant_meta"},
            {"name": "_embedding_model", "type": "string", "source": "qdrant_meta"},
        ],
        "aliases": [
            {"canonical": "content", "alias": "comments", "source": "Bullhorn DB"},
            {"canonical": "subject", "alias": "note_text", "source": "Bullhorn DB"},
        ],
    }


def _entity_prime_contractor():
    return {
        "name": "PRIME_CONTRACTOR",
        "pk": "id",
        "records": "41",
        "category": "Organizations",
        "description": "Defense prime contractors (GDIT, Leidos, SAIC, etc.) with relationship and revenue tracking",
        "sources": ["Bullhorn CRM", "Enrichment"],
        "storage": [
            "sqlite:bullhorn_master.db/prime_contractors",
            "qdrant:primes",
            "neo4j:Company",
        ],
        "properties": [
            {"name": "id", "type": "integer", "source": "sqlite"},
            {"name": "name", "type": "string", "source": "bullhorn"},
            {"name": "normalized_name", "type": "string", "source": "etl"},
            {"name": "aliases", "type": "text", "source": "etl"},
            {"name": "cage_code", "type": "string", "source": "enrichment"},
            {"name": "duns_number", "type": "string", "source": "enrichment"},
            {"name": "website", "type": "string", "source": "enrichment"},
            {"name": "headquarters", "type": "string", "source": "enrichment"},
            {"name": "employee_count", "type": "integer", "source": "enrichment"},
            {"name": "annual_revenue", "type": "decimal", "source": "enrichment"},
            {"name": "naics_codes", "type": "text", "source": "enrichment"},
            {"name": "contract_vehicles", "type": "text", "source": "enrichment"},
            {"name": "total_jobs", "type": "integer", "source": "derived"},
            {"name": "total_placements", "type": "integer", "source": "derived"},
            {"name": "total_revenue", "type": "decimal", "source": "derived"},
            {"name": "first_engagement_date", "type": "date", "source": "derived"},
            {"name": "last_engagement_date", "type": "date", "source": "derived"},
            {
                "name": "relationship_status",
                "type": "string",
                "source": "manual",
                "values": ["Active Partner", "Prospect", "Target", "Watch", "Inactive"],
            },
            {"name": "category", "type": "string", "source": "qdrant"},
            {"name": "type", "type": "string", "source": "neo4j"},
            {"name": "is_defense_prime", "type": "boolean", "source": "neo4j"},
        ],
        "aliases": [
            {"canonical": "name", "alias": "company_name", "source": "General"},
            {"canonical": "name", "alias": "prime", "source": "API shorthand"},
        ],
    }


def _entity_document():
    return {
        "name": "DOCUMENT",
        "pk": "doc_id",
        "records": "205",
        "category": "BD Intelligence",
        "description": "Processed documents: SOWs, RFPs, past performance records, briefings",
        "sources": ["Filesystem", "Docling processor"],
        "storage": ["qdrant:documents"],
        "properties": [
            {"name": "doc_id", "type": "string", "source": "indexer"},
            {"name": "filename", "type": "string", "source": "filesystem"},
            {"name": "filepath", "type": "string", "source": "filesystem"},
            {"name": "doc_type", "type": "string", "source": "classifier"},
            {"name": "title", "type": "string", "source": "extractor"},
            {"name": "summary", "type": "string", "source": "llm"},
            {"name": "content", "type": "text", "source": "qdrant_embedding"},
            {"name": "chunk_index", "type": "integer", "source": "chunker"},
            {"name": "total_chunks", "type": "integer", "source": "chunker"},
            {"name": "tags", "type": "list[str]", "source": "auto_tagger"},
            {
                "name": "type",
                "type": "string",
                "source": "classifier",
                "example": "past_performance",
            },
            {"name": "_indexed_at", "type": "string", "source": "qdrant_meta"},
            {"name": "_embedding_model", "type": "string", "source": "qdrant_meta"},
        ],
        "aliases": [],
    }


def _entity_past_performance():
    return {
        "name": "PAST_PERFORMANCE",
        "pk": "id",
        "records": "492",
        "category": "BD Intelligence",
        "description": "Aggregated past performance records linking primes to programs with financial metrics",
        "sources": ["Bullhorn CRM", "Derived"],
        "storage": ["sqlite:bullhorn_master.db/past_performance"],
        "properties": [
            {"name": "id", "type": "integer", "source": "sqlite"},
            {"name": "prime_contractor_id", "type": "integer", "source": "sqlite_fk"},
            {"name": "prime_contractor_name", "type": "string", "source": "derived"},
            {"name": "program_id", "type": "integer", "source": "sqlite_fk"},
            {"name": "program_name", "type": "string", "source": "derived"},
            {"name": "total_jobs", "type": "integer", "source": "derived"},
            {"name": "open_jobs", "type": "integer", "source": "derived"},
            {"name": "closed_jobs", "type": "integer", "source": "derived"},
            {"name": "filled_jobs", "type": "integer", "source": "derived"},
            {"name": "total_placements", "type": "integer", "source": "derived"},
            {"name": "active_placements", "type": "integer", "source": "derived"},
            {"name": "total_revenue", "type": "decimal", "source": "derived"},
            {"name": "avg_bill_rate", "type": "decimal", "source": "derived"},
            {"name": "avg_pay_rate", "type": "decimal", "source": "derived"},
            {"name": "avg_margin", "type": "decimal", "source": "derived"},
            {"name": "fill_rate", "type": "decimal", "source": "derived"},
            {"name": "performance_score", "type": "decimal", "source": "engine5"},
        ],
        "aliases": [],
    }


def _entity_federal_contract():
    return {
        "name": "FEDERAL_CONTRACT",
        "pk": "award_id",
        "records": "unknown",
        "category": "Federal Awards",
        "description": "USASpending/SAM.gov federal contract awards with agency, contractor, and vehicle data",
        "sources": ["USASpending API", "SAM.gov API"],
        "storage": ["qdrant:federal_contracts", "neo4j:Contract"],
        "properties": [
            {"name": "award_id", "type": "string", "source": "sam_gov"},
            {"name": "title", "type": "string", "source": "usaspending"},
            {"name": "description", "type": "text", "source": "usaspending"},
            {"name": "agency", "type": "string", "source": "usaspending"},
            {"name": "sub_agency", "type": "string", "source": "sam_gov"},
            {"name": "awardee", "type": "string", "source": "sam_gov"},
            {"name": "contractor", "type": "string", "source": "usaspending"},
            {"name": "contract_vehicle", "type": "string", "source": "usaspending"},
            {"name": "contract_number", "type": "string", "source": "neo4j"},
            {"name": "contract_type", "type": "string", "source": "sam_gov"},
            {"name": "value", "type": "decimal", "source": "sam_gov"},
            {"name": "naics", "type": "string", "source": "sam_gov"},
            {"name": "set_aside", "type": "string", "source": "sam_gov"},
            {"name": "award_date", "type": "date", "source": "sam_gov"},
            {"name": "pop_start", "type": "date", "source": "sam_gov"},
            {"name": "pop_end", "type": "date", "source": "sam_gov"},
            {"name": "place_of_performance", "type": "string", "source": "sam_gov"},
            {"name": "modifications", "type": "list", "source": "sam_gov"},
            {"name": "status", "type": "string", "source": "usaspending"},
        ],
        "aliases": [
            {"canonical": "contractor", "alias": "awardee", "source": "SAM.gov"},
            {"canonical": "award_id", "alias": "contract_id", "source": "FPDS"},
        ],
    }


def _entity_contract_opportunity():
    return {
        "name": "CONTRACT_OPPORTUNITY",
        "pk": "notice_id",
        "records": "unknown",
        "category": "Procurement",
        "description": "SAM.gov contract opportunities (RFIs, RFPs, Sources Sought)",
        "sources": ["SAM.gov API"],
        "storage": ["qdrant:opportunities"],
        "properties": [
            {"name": "notice_id", "type": "string", "source": "sam_gov"},
            {"name": "title", "type": "string", "source": "sam_gov"},
            {
                "name": "type",
                "type": "string",
                "source": "sam_gov",
                "values": ["RFI", "RFP", "Sources Sought"],
            },
            {"name": "agency", "type": "string", "source": "sam_gov"},
            {"name": "posted_date", "type": "date", "source": "sam_gov"},
            {"name": "response_deadline", "type": "date", "source": "sam_gov"},
            {"name": "naics", "type": "string", "source": "sam_gov"},
            {"name": "set_aside", "type": "string", "source": "sam_gov"},
            {"name": "description", "type": "text", "source": "sam_gov"},
            {"name": "point_of_contact", "type": "json", "source": "sam_gov"},
            {"name": "attachments", "type": "list", "source": "sam_gov"},
            {"name": "estimated_value", "type": "decimal", "source": "sam_gov"},
        ],
        "aliases": [
            {"canonical": "notice_id", "alias": "opportunity_id", "source": "API"},
        ],
    }


def _entity_intelligence_report():
    return {
        "name": "INTELLIGENCE_REPORT",
        "pk": "id",
        "records": "unknown",
        "category": "BD Intelligence",
        "description": "Generated intelligence reports from agents and analysis workflows",
        "sources": ["AI Agents"],
        "storage": ["qdrant:intelligence_reports"],
        "properties": [
            {"name": "id", "type": "string", "source": "uuid"},
            {"name": "content", "type": "text", "source": "agent"},
            {"name": "title", "type": "string", "source": "agent"},
            {"name": "summary", "type": "string", "source": "agent"},
            {"name": "source", "type": "string", "source": "agent"},
            {"name": "report_type", "type": "string", "source": "agent"},
            {"name": "classification", "type": "string", "source": "agent"},
            {"name": "date", "type": "string", "source": "agent"},
        ],
        "aliases": [],
    }


def _entity_bullhorn_note():
    return {
        "name": "BULLHORN_NOTE",
        "pk": "id",
        "records": "50000+",
        "category": "BD Intelligence",
        "description": "Raw CRM notes from Bullhorn with HUMINT intelligence from field contacts",
        "sources": ["Bullhorn CRM"],
        "storage": ["qdrant:bullhorn_notes"],
        "properties": [
            {"name": "note_body", "type": "text", "source": "bullhorn"},
            {"name": "comments", "type": "text", "source": "bullhorn"},
            {"name": "about", "type": "string", "source": "bullhorn"},
            {"name": "action", "type": "string", "source": "bullhorn"},
            {"name": "note_type", "type": "string", "source": "bullhorn"},
            {"name": "noteType", "type": "string", "source": "bullhorn"},
            {"name": "personReference", "type": "string", "source": "bullhorn"},
            {"name": "_source", "type": "string", "source": "qdrant_meta"},
        ],
        "aliases": [],
    }


def _entity_memory():
    return {
        "name": "MEMORY",
        "pk": "id",
        "records": "unknown",
        "category": "Meta/Ops",
        "description": "Long-term agent memories with 5-layer system (working, episodic, semantic, procedural, strategic)",
        "sources": ["AI Agents", "Mem0"],
        "storage": ["sqlite:memories.db/memories", "qdrant:memories"],
        "properties": [
            {"name": "id", "type": "string", "source": "uuid"},
            {"name": "content", "type": "text", "source": "agent"},
            {
                "name": "memory_type",
                "type": "string",
                "source": "agent",
                "values": ["episodic", "semantic", "procedural"],
            },
            {"name": "importance", "type": "float", "source": "agent"},
            {
                "name": "layer",
                "type": "string",
                "source": "agent",
                "values": [
                    "working",
                    "episodic",
                    "semantic",
                    "procedural",
                    "strategic",
                ],
            },
            {"name": "entities", "type": "list[str]", "source": "agent"},
            {"name": "programs", "type": "list[str]", "source": "agent"},
            {"name": "contacts", "type": "list[str]", "source": "agent"},
            {"name": "source", "type": "string", "source": "agent"},
            {"name": "tags", "type": "list[str]", "source": "agent"},
            {"name": "confidence", "type": "float", "source": "agent"},
            {"name": "access_count", "type": "integer", "source": "system"},
            {"name": "user_id", "type": "string", "source": "system"},
            {"name": "agent_id", "type": "string", "source": "system"},
            {"name": "metadata", "type": "json", "source": "agent"},
            {"name": "created_at", "type": "timestamp", "source": "system"},
            {"name": "last_accessed", "type": "timestamp", "source": "system"},
        ],
        "aliases": [],
    }


def _entity_interaction():
    return {
        "name": "INTERACTION",
        "pk": "id",
        "records": "unknown",
        "category": "Meta/Ops",
        "description": "Agent interaction logs tracking contact engagement history",
        "sources": ["AI Agents"],
        "storage": ["sqlite:memories.db/interactions"],
        "properties": [
            {"name": "id", "type": "integer", "source": "auto"},
            {"name": "contact_id", "type": "string", "source": "agent"},
            {"name": "contact_name", "type": "string", "source": "agent"},
            {"name": "interaction_type", "type": "string", "source": "agent"},
            {"name": "summary", "type": "text", "source": "agent"},
            {"name": "sentiment", "type": "string", "source": "agent"},
            {"name": "outcome", "type": "string", "source": "agent"},
            {"name": "timestamp", "type": "timestamp", "source": "system"},
        ],
        "aliases": [],
    }


def _entity_insight():
    return {
        "name": "INSIGHT",
        "pk": "id",
        "records": "unknown",
        "category": "BD Intelligence",
        "description": "BD insights (opportunities, risks, relationships) stored by agents",
        "sources": ["AI Agents"],
        "storage": ["sqlite:memories.db/insights"],
        "properties": [
            {"name": "id", "type": "integer", "source": "auto"},
            {
                "name": "entity_type",
                "type": "string",
                "source": "agent",
                "values": ["company", "program", "contact", "contract"],
            },
            {"name": "entity_name", "type": "string", "source": "agent"},
            {"name": "insight", "type": "text", "source": "agent"},
            {"name": "source", "type": "string", "source": "agent"},
            {
                "name": "confidence",
                "type": "float",
                "source": "agent",
                "note": "0.0-1.0",
            },
            {"name": "timestamp", "type": "timestamp", "source": "system"},
        ],
        "aliases": [],
    }


def _entity_graph_entity():
    return {
        "name": "GRAPH_ENTITY",
        "pk": "id",
        "records": "unknown",
        "category": "Meta/Ops",
        "description": "Knowledge graph entities from LightRAG bd_graph.db",
        "sources": ["LightRAG"],
        "storage": ["sqlite:bd_graph.db/entities"],
        "properties": [
            {"name": "id", "type": "integer", "source": "auto"},
            {"name": "entity_type", "type": "string", "source": "lightrag"},
            {"name": "entity_name", "type": "string", "source": "lightrag"},
            {"name": "attributes", "type": "json", "source": "lightrag"},
        ],
        "aliases": [],
    }


def _entity_graph_relationship():
    return {
        "name": "GRAPH_RELATIONSHIP",
        "pk": "id",
        "records": "unknown",
        "category": "Meta/Ops",
        "description": "Knowledge graph relationships from LightRAG bd_graph.db",
        "sources": ["LightRAG"],
        "storage": ["sqlite:bd_graph.db/relationships"],
        "properties": [
            {"name": "id", "type": "integer", "source": "auto"},
            {"name": "source_entity", "type": "string", "source": "lightrag"},
            {"name": "target_entity", "type": "string", "source": "lightrag"},
            {"name": "relationship_type", "type": "string", "source": "lightrag"},
            {"name": "weight", "type": "float", "source": "lightrag"},
            {"name": "attributes", "type": "json", "source": "lightrag"},
        ],
        "aliases": [],
    }


def _entity_source_file():
    return {
        "name": "SOURCE_FILE",
        "pk": "id",
        "records": "unknown",
        "category": "Meta/Ops",
        "description": "ETL source file tracking for audit trail and data lineage",
        "sources": ["ETL Pipeline"],
        "storage": ["sqlite:bullhorn_master.db/source_files"],
        "properties": [
            {"name": "id", "type": "integer", "source": "auto"},
            {"name": "filename", "type": "string", "source": "filesystem"},
            {"name": "file_path", "type": "string", "source": "filesystem"},
            {"name": "file_size_bytes", "type": "integer", "source": "filesystem"},
            {"name": "file_type", "type": "string", "source": "filesystem"},
            {"name": "entity_type", "type": "string", "source": "etl"},
            {"name": "record_count", "type": "integer", "source": "etl"},
            {"name": "processed_date", "type": "datetime", "source": "etl"},
            {"name": "processing_status", "type": "string", "source": "etl"},
            {"name": "error_message", "type": "text", "source": "etl"},
            {"name": "checksum", "type": "string", "source": "etl"},
        ],
        "aliases": [],
    }


def _entity_data_quality_log():
    return {
        "name": "DATA_QUALITY_LOG",
        "pk": "id",
        "records": "unknown",
        "category": "Meta/Ops",
        "description": "Data quality issue tracking for ETL pipeline validation",
        "sources": ["QA Agent"],
        "storage": ["sqlite:bullhorn_master.db/data_quality_log"],
        "properties": [
            {"name": "id", "type": "integer", "source": "auto"},
            {"name": "source_file", "type": "string", "source": "etl"},
            {"name": "table_name", "type": "string", "source": "etl"},
            {"name": "record_identifier", "type": "string", "source": "etl"},
            {
                "name": "issue_type",
                "type": "string",
                "source": "qa_agent",
                "values": [
                    "duplicate",
                    "missing_field",
                    "stale",
                    "invalid",
                    "low_confidence",
                ],
            },
            {"name": "issue_description", "type": "text", "source": "qa_agent"},
            {
                "name": "severity",
                "type": "string",
                "source": "qa_agent",
                "values": ["critical", "high", "medium", "low"],
            },
            {"name": "resolved", "type": "boolean", "source": "manual"},
        ],
        "aliases": [],
    }


def _entity_processing_stats():
    return {
        "name": "PROCESSING_STATS",
        "pk": "id",
        "records": "unknown",
        "category": "Meta/Ops",
        "description": "ETL pipeline processing statistics per run",
        "sources": ["ETL Pipeline"],
        "storage": ["sqlite:bullhorn_master.db/processing_stats"],
        "properties": [
            {"name": "id", "type": "integer", "source": "auto"},
            {"name": "run_id", "type": "string", "source": "etl"},
            {"name": "source_file", "type": "string", "source": "etl"},
            {"name": "table_name", "type": "string", "source": "etl"},
            {"name": "records_read", "type": "integer", "source": "etl"},
            {"name": "records_inserted", "type": "integer", "source": "etl"},
            {"name": "records_updated", "type": "integer", "source": "etl"},
            {"name": "records_skipped", "type": "integer", "source": "etl"},
            {"name": "records_error", "type": "integer", "source": "etl"},
            {"name": "duplicates_found", "type": "integer", "source": "etl"},
            {"name": "processing_time_seconds", "type": "decimal", "source": "etl"},
        ],
        "aliases": [],
    }


def _entity_location():
    return {
        "name": "LOCATION",
        "pk": "city",
        "records": "16+",
        "category": "Reference",
        "description": "Geographic locations for programs, jobs, and contacts with BD significance",
        "sources": ["Engine3_OrgChart", "Neo4j"],
        "storage": ["neo4j:Location"],
        "properties": [
            {"name": "city", "type": "string", "source": "neo4j"},
            {"name": "state", "type": "string", "source": "neo4j"},
            {"name": "coordinates_lat", "type": "float", "source": "neo4j"},
            {"name": "coordinates_lon", "type": "float", "source": "neo4j"},
            {"name": "hub_name", "type": "string", "source": "engine3"},
            {"name": "military_installation", "type": "string", "source": "neo4j"},
            {"name": "region", "type": "string", "source": "neo4j"},
        ],
        "aliases": [
            {"canonical": "hub_name", "alias": "location_hub", "source": "Engine3"},
        ],
    }


def _entity_notification():
    return {
        "name": "NOTIFICATION",
        "pk": "id",
        "records": "unknown",
        "category": "Meta/Ops",
        "description": "System notifications from webhooks, alerts, and pipeline events",
        "sources": ["Phase 7 API"],
        "storage": ["api:phase7_endpoints"],
        "properties": [
            {"name": "id", "type": "string", "source": "uuid"},
            {"name": "type", "type": "string", "source": "system"},
            {"name": "title", "type": "string", "source": "system"},
            {"name": "message", "type": "text", "source": "system"},
            {"name": "entity_type", "type": "string", "source": "system"},
            {"name": "entity_id", "type": "string", "source": "system"},
            {"name": "priority", "type": "string", "source": "system"},
            {"name": "read", "type": "boolean", "source": "user"},
            {"name": "created_at", "type": "timestamp", "source": "system"},
        ],
        "aliases": [],
    }


def _entity_alert():
    return {
        "name": "ALERT",
        "pk": "alert_id",
        "records": "unknown",
        "category": "Meta/Ops",
        "description": "QA and BD-significant event alerts with severity tracking",
        "sources": ["Engine6_QA", "Phase 7 API"],
        "storage": ["api:alerts"],
        "properties": [
            {"name": "alert_id", "type": "string", "source": "uuid"},
            {"name": "rule_id", "type": "string", "source": "qa"},
            {
                "name": "severity",
                "type": "string",
                "source": "qa",
                "values": ["info", "warning", "critical"],
            },
            {"name": "title", "type": "string", "source": "qa"},
            {"name": "message", "type": "text", "source": "qa"},
            {"name": "data", "type": "json", "source": "qa"},
            {"name": "timestamp", "type": "datetime", "source": "system"},
        ],
        "aliases": [],
    }


def _entity_contract_watch():
    return {
        "name": "CONTRACT_WATCH",
        "pk": "watch_id",
        "records": "unknown",
        "category": "Procurement",
        "description": "SAM.gov contract monitoring watches with keyword/NAICS filters",
        "sources": ["SAM.gov Sync"],
        "storage": ["api:sam_watches"],
        "properties": [
            {"name": "watch_id", "type": "string", "source": "uuid"},
            {"name": "name", "type": "string", "source": "user"},
            {"name": "keywords", "type": "list[str]", "source": "user"},
            {"name": "naics_codes", "type": "list[str]", "source": "user"},
            {"name": "companies", "type": "list[str]", "source": "user"},
            {"name": "agencies", "type": "list[str]", "source": "user"},
            {"name": "min_value", "type": "decimal", "source": "user"},
            {"name": "alert_on", "type": "list[str]", "source": "user"},
            {"name": "enabled", "type": "boolean", "source": "user"},
            {"name": "created_at", "type": "datetime", "source": "system"},
        ],
        "aliases": [],
    }


def _entity_weekly_report():
    return {
        "name": "WEEKLY_REPORT",
        "pk": "id",
        "records": "unknown",
        "category": "BD Intelligence",
        "description": "Weekly BD reports with pipeline, outreach, competitive, and action items",
        "sources": ["Phase 10A API"],
        "storage": ["api:reports"],
        "properties": [
            {"name": "period", "type": "string", "source": "generated"},
            {"name": "generated_at", "type": "datetime", "source": "system"},
            {"name": "pipeline_summary", "type": "json", "source": "generated"},
            {"name": "outreach_activity", "type": "json", "source": "generated"},
            {"name": "meetings", "type": "json", "source": "generated"},
            {"name": "competitive_changes", "type": "json", "source": "generated"},
            {"name": "top_opportunities", "type": "list", "source": "generated"},
            {"name": "action_items", "type": "list", "source": "generated"},
            {"name": "executive_summary", "type": "text", "source": "generated"},
        ],
        "aliases": [],
    }


def _entity_call_briefing():
    return {
        "name": "CALL_BRIEFING",
        "pk": "id",
        "records": "unknown",
        "category": "BD Intelligence",
        "description": "Pre-call briefings with talking points, pain points, and relationship context",
        "sources": ["Voice Intelligence API"],
        "storage": ["api:briefings"],
        "properties": [
            {"name": "id", "type": "string", "source": "uuid"},
            {"name": "contact_id", "type": "string", "source": "fk"},
            {"name": "contact_name", "type": "string", "source": "derived"},
            {"name": "pain_points", "type": "list", "source": "generated"},
            {"name": "recent_interactions", "type": "list", "source": "generated"},
            {"name": "open_jobs", "type": "list", "source": "generated"},
            {"name": "talking_points", "type": "list", "source": "generated"},
            {"name": "relationship_map", "type": "list", "source": "generated"},
            {"name": "priority", "type": "string", "source": "generated"},
            {"name": "summary", "type": "text", "source": "generated"},
            {"name": "created_at", "type": "datetime", "source": "system"},
        ],
        "aliases": [],
    }


def _entity_transcript_intel():
    return {
        "name": "TRANSCRIPT_INTEL",
        "pk": "id",
        "records": "unknown",
        "category": "BD Intelligence",
        "description": "Intelligence extracted from call transcripts via NLP",
        "sources": ["Voice Intelligence API"],
        "storage": ["api:transcripts"],
        "properties": [
            {"name": "id", "type": "string", "source": "uuid"},
            {"name": "call_id", "type": "string", "source": "vapi"},
            {"name": "contact_id", "type": "string", "source": "fk"},
            {"name": "sentiment", "type": "string", "source": "nlp"},
            {"name": "sentiment_score", "type": "float", "source": "nlp"},
            {"name": "pain_points", "type": "list", "source": "nlp"},
            {"name": "job_openings", "type": "list", "source": "nlp"},
            {"name": "budget_signals", "type": "list", "source": "nlp"},
            {"name": "competitor_mentions", "type": "list", "source": "nlp"},
            {"name": "action_items", "type": "list", "source": "nlp"},
            {"name": "key_topics", "type": "list", "source": "nlp"},
            {"name": "summary", "type": "text", "source": "nlp"},
            {"name": "duration_sec", "type": "integer", "source": "vapi"},
            {"name": "created_at", "type": "datetime", "source": "system"},
        ],
        "aliases": [],
    }


def _entity_relationship_score():
    return {
        "name": "RELATIONSHIP_SCORE",
        "pk": "contact_pair",
        "records": "unknown",
        "category": "BD Intelligence",
        "description": "Relationship strength scores between contacts with decay tracking",
        "sources": ["Relationship Intelligence API"],
        "storage": ["api:relationships"],
        "properties": [
            {"name": "contact_id", "type": "string", "source": "fk"},
            {"name": "total_score", "type": "float", "source": "computed"},
            {"name": "recency_score", "type": "float", "source": "computed"},
            {"name": "frequency_score", "type": "float", "source": "computed"},
            {"name": "quality_score", "type": "float", "source": "computed"},
            {"name": "reciprocity_score", "type": "float", "source": "computed"},
            {"name": "depth_score", "type": "float", "source": "computed"},
            {"name": "outcome_score", "type": "float", "source": "computed"},
            {"name": "days_since_contact", "type": "integer", "source": "computed"},
            {"name": "risk_level", "type": "string", "source": "computed"},
            {"name": "recommended_action", "type": "string", "source": "computed"},
        ],
        "aliases": [],
    }


def _entity_win_probability():
    return {
        "name": "WIN_PROBABILITY",
        "pk": "opportunity_id",
        "records": "unknown",
        "category": "BD Intelligence",
        "description": "ML-predicted win probability for BD opportunities",
        "sources": ["Predictive Intelligence API"],
        "storage": ["api:predictions"],
        "properties": [
            {"name": "opportunity_id", "type": "string", "source": "fk"},
            {"name": "win_probability", "type": "float", "source": "ml_model"},
            {"name": "confidence", "type": "float", "source": "ml_model"},
            {"name": "top_factors", "type": "list", "source": "ml_model"},
            {"name": "recommended_actions", "type": "list", "source": "ml_model"},
            {"name": "optimal_timing", "type": "json", "source": "ml_model"},
            {"name": "contact_tier", "type": "integer", "source": "input"},
            {"name": "relationship_depth", "type": "float", "source": "input"},
            {"name": "days_since_last_contact", "type": "integer", "source": "input"},
            {"name": "clearance_match", "type": "float", "source": "input"},
            {"name": "role_match_score", "type": "float", "source": "input"},
            {"name": "competitor_density", "type": "float", "source": "input"},
        ],
        "aliases": [],
    }


def _entity_hiring_forecast():
    return {
        "name": "HIRING_FORECAST",
        "pk": "entity_program",
        "records": "unknown",
        "category": "BD Intelligence",
        "description": "Hiring forecasts, ramp signals, and optimal timing recommendations",
        "sources": ["Predictive Intelligence API"],
        "storage": ["api:forecasts"],
        "properties": [
            {"name": "entity", "type": "string", "source": "input"},
            {"name": "horizon_days", "type": "integer", "source": "input"},
            {"name": "current_rate", "type": "float", "source": "computed"},
            {"name": "forecasted_rate", "type": "float", "source": "ml_model"},
            {"name": "trend", "type": "string", "source": "computed"},
            {"name": "trend_strength", "type": "float", "source": "computed"},
            {"name": "seasonal_pattern", "type": "json", "source": "computed"},
            {"name": "confidence", "type": "float", "source": "ml_model"},
        ],
        "aliases": [],
    }


def _entity_recompete_prediction():
    return {
        "name": "RECOMPETE_PREDICTION",
        "pk": "contract_id",
        "records": "unknown",
        "category": "Procurement",
        "description": "Predicted recompete timelines for expiring contracts",
        "sources": ["Predictive Intelligence API"],
        "storage": ["api:predictions"],
        "properties": [
            {"name": "contract_id", "type": "string", "source": "input"},
            {"name": "contract_name", "type": "string", "source": "input"},
            {"name": "current_pop_end", "type": "date", "source": "input"},
            {"name": "options_remaining", "type": "integer", "source": "input"},
            {"name": "predicted_rfi_date", "type": "date", "source": "ml_model"},
            {"name": "predicted_rfp_date", "type": "date", "source": "ml_model"},
            {"name": "predicted_award_date", "type": "date", "source": "ml_model"},
            {"name": "recompete_probability", "type": "float", "source": "ml_model"},
            {"name": "months_to_action", "type": "integer", "source": "computed"},
            {"name": "recommended_actions", "type": "list", "source": "ml_model"},
        ],
        "aliases": [],
    }


def _entity_revenue_placement():
    return {
        "name": "REVENUE_PLACEMENT",
        "pk": "id",
        "records": "unknown",
        "category": "BD Intelligence",
        "description": "Revenue-tracked placements with margin analysis and ROI metrics",
        "sources": ["Revenue Intelligence API"],
        "storage": ["api:revenue"],
        "properties": [
            {"name": "id", "type": "string", "source": "input"},
            {"name": "contractor_name", "type": "string", "source": "input"},
            {"name": "client", "type": "string", "source": "input"},
            {"name": "program", "type": "string", "source": "input"},
            {"name": "role_title", "type": "string", "source": "input"},
            {"name": "bill_rate", "type": "decimal", "source": "input"},
            {"name": "pay_rate", "type": "decimal", "source": "input"},
            {"name": "start_date", "type": "date", "source": "input"},
            {"name": "end_date", "type": "date", "source": "input"},
            {"name": "rep", "type": "string", "source": "input"},
            {"name": "contact_id", "type": "string", "source": "fk"},
            {"name": "location", "type": "string", "source": "input"},
            {"name": "clearance", "type": "string", "source": "input"},
            {"name": "hours_per_week", "type": "integer", "source": "input"},
        ],
        "aliases": [],
    }


def _entity_swarm_task():
    return {
        "name": "SWARM_TASK",
        "pk": "swarm_id",
        "records": "unknown",
        "category": "Meta/Ops",
        "description": "Multi-agent swarm task execution with DAG decomposition",
        "sources": ["Swarm API"],
        "storage": ["api:swarm"],
        "properties": [
            {"name": "swarm_id", "type": "string", "source": "uuid"},
            {"name": "description", "type": "text", "source": "input"},
            {"name": "task_type", "type": "string", "source": "input"},
            {"name": "coordination_mode", "type": "string", "source": "input"},
            {"name": "quality_threshold", "type": "float", "source": "input"},
            {
                "name": "status",
                "type": "string",
                "source": "system",
                "values": ["pending", "running", "completed", "failed"],
            },
            {"name": "workers_used", "type": "integer", "source": "system"},
            {"name": "total_tokens", "type": "integer", "source": "system"},
            {"name": "quality_score", "type": "float", "source": "system"},
            {"name": "output", "type": "json", "source": "system"},
        ],
        "aliases": [],
    }


def _entity_workflow_run():
    return {
        "name": "WORKFLOW_RUN",
        "pk": "run_id",
        "records": "unknown",
        "category": "Meta/Ops",
        "description": "LangGraph workflow executions with state persistence",
        "sources": ["Workflow API"],
        "storage": ["sqlite:langgraph_checkpoints.db", "sqlite:checkpoints_meta.db"],
        "properties": [
            {"name": "run_id", "type": "string", "source": "uuid"},
            {"name": "workflow_id", "type": "string", "source": "input"},
            {"name": "workflow_name", "type": "string", "source": "input"},
            {"name": "thread_id", "type": "string", "source": "system"},
            {
                "name": "status",
                "type": "string",
                "source": "system",
                "values": ["pending", "running", "completed", "failed", "paused"],
            },
            {"name": "input_state", "type": "json", "source": "input"},
            {"name": "output_data", "type": "json", "source": "system"},
            {"name": "started_at", "type": "timestamp", "source": "system"},
            {"name": "completed_at", "type": "timestamp", "source": "system"},
        ],
        "aliases": [],
    }


def _entity_contact_claim():
    return {
        "name": "CONTACT_CLAIM",
        "pk": "id",
        "records": "unknown",
        "category": "Meta/Ops",
        "description": "Contact ownership claims for BD team collaboration",
        "sources": ["Collaboration API"],
        "storage": ["api:collaboration"],
        "properties": [
            {"name": "id", "type": "string", "source": "uuid"},
            {"name": "contact_id", "type": "string", "source": "fk"},
            {"name": "contact_name", "type": "string", "source": "derived"},
            {"name": "owner_id", "type": "string", "source": "input"},
            {"name": "owner_name", "type": "string", "source": "input"},
            {
                "name": "status",
                "type": "string",
                "source": "system",
                "values": ["active", "contested", "transferred", "expired"],
            },
            {"name": "reason", "type": "string", "source": "input"},
            {"name": "program", "type": "string", "source": "input"},
            {"name": "created_at", "type": "datetime", "source": "system"},
            {"name": "expires_at", "type": "datetime", "source": "system"},
        ],
        "aliases": [],
    }


def _entity_strategic_pattern():
    return {
        "name": "STRATEGIC_PATTERN",
        "pk": "id",
        "records": "unknown",
        "category": "BD Intelligence",
        "description": "Strategic patterns detected by meta-learning engine",
        "sources": ["Intelligence API"],
        "storage": ["api:intelligence"],
        "properties": [
            {"name": "id", "type": "string", "source": "uuid"},
            {"name": "pattern_type", "type": "string", "source": "ml"},
            {"name": "title", "type": "string", "source": "ml"},
            {"name": "description", "type": "text", "source": "ml"},
            {"name": "program", "type": "string", "source": "ml"},
            {"name": "confidence", "type": "float", "source": "ml"},
            {"name": "detected_at", "type": "datetime", "source": "system"},
            {"name": "expires_at", "type": "datetime", "source": "system"},
            {"name": "tags", "type": "list[str]", "source": "ml"},
        ],
        "aliases": [],
    }


def _entity_proposal_artifact():
    return {
        "name": "PROPOSAL_ARTIFACT",
        "pk": "id",
        "records": "unknown",
        "category": "Procurement",
        "description": "Proposal artifacts: capability statements, compliance matrices, rate cards",
        "sources": ["Proposal API"],
        "storage": ["api:proposals"],
        "properties": [
            {"name": "id", "type": "string", "source": "uuid"},
            {
                "name": "artifact_type",
                "type": "string",
                "source": "input",
                "values": [
                    "capability_statement",
                    "compliance_matrix",
                    "rate_card",
                    "past_performance",
                    "labor_category",
                ],
            },
            {"name": "program", "type": "string", "source": "input"},
            {"name": "agency", "type": "string", "source": "input"},
            {"name": "solicitation", "type": "string", "source": "input"},
            {"name": "content", "type": "json", "source": "generated"},
            {"name": "generated_at", "type": "datetime", "source": "system"},
        ],
        "aliases": [],
    }


def _entity_streaming_event():
    return {
        "name": "STREAMING_EVENT",
        "pk": "event_id",
        "records": "unknown",
        "category": "Meta/Ops",
        "description": "Real-time streaming events from SAM.gov, FPDS, and Bullhorn",
        "sources": ["Streaming Pipeline", "Event Bus"],
        "storage": ["redis:event_streams"],
        "properties": [
            {"name": "event_id", "type": "string", "source": "system"},
            {"name": "event_type", "type": "string", "source": "system"},
            {"name": "source", "type": "string", "source": "system"},
            {"name": "timestamp", "type": "datetime", "source": "system"},
            {"name": "payload", "type": "json", "source": "system"},
            {"name": "priority", "type": "string", "source": "system"},
            {"name": "metadata", "type": "json", "source": "system"},
        ],
        "aliases": [],
    }


def _entity_file_node():
    return {
        "name": "FILE_NODE",
        "pk": "path",
        "records": "4221",
        "category": "Meta/Ops",
        "description": "Neo4j file lineage nodes tracking code files and data dependencies",
        "sources": ["Neo4j Graph"],
        "storage": ["neo4j:File"],
        "properties": [
            {"name": "path", "type": "string", "source": "filesystem"},
            {"name": "name", "type": "string", "source": "filesystem"},
            {"name": "type", "type": "string", "source": "classifier"},
            {"name": "extension", "type": "string", "source": "filesystem"},
            {"name": "size_bytes", "type": "integer", "source": "filesystem"},
            {"name": "hash", "type": "string", "source": "filesystem"},
            {"name": "modified", "type": "datetime", "source": "filesystem"},
            {"name": "engine", "type": "string", "source": "classifier"},
            {"name": "is_input", "type": "boolean", "source": "lineage"},
            {"name": "is_output", "type": "boolean", "source": "lineage"},
        ],
        "aliases": [],
    }


def _entity_process_node():
    return {
        "name": "PROCESS_NODE",
        "pk": "name",
        "records": "unknown",
        "category": "Meta/Ops",
        "description": "Neo4j process lineage nodes tracking script executions",
        "sources": ["Neo4j Graph"],
        "storage": ["neo4j:Process"],
        "properties": [
            {"name": "name", "type": "string", "source": "classifier"},
            {"name": "script_path", "type": "string", "source": "filesystem"},
            {"name": "engine", "type": "string", "source": "classifier"},
            {"name": "description", "type": "text", "source": "manual"},
            {"name": "last_run", "type": "datetime", "source": "system"},
            {"name": "run_count", "type": "integer", "source": "system"},
            {"name": "avg_duration_seconds", "type": "float", "source": "computed"},
        ],
        "aliases": [],
    }


# =============================================================================
# RELATIONSHIPS
# =============================================================================


def _build_relationships() -> list:
    return [
        # CONTACT relationships
        {
            "source": "CONTACT",
            "target": "PRIME_CONTRACTOR",
            "type": "WORKS_AT",
            "description": "Contact employed by prime",
            "cardinality": "many-to-one",
        },
        {
            "source": "CONTACT",
            "target": "PROGRAM",
            "type": "WORKS_ON",
            "description": "Contact works on federal program",
            "cardinality": "many-to-many",
        },
        {
            "source": "CONTACT",
            "target": "ACTIVITY",
            "type": "HAS_ACTIVITY",
            "description": "Contact has CRM activity records",
            "cardinality": "one-to-many",
        },
        {
            "source": "CONTACT",
            "target": "PLACEMENT",
            "type": "HAS_PLACEMENT",
            "description": "Contact placed in a role",
            "cardinality": "one-to-many",
        },
        {
            "source": "CONTACT",
            "target": "JOB",
            "type": "SUBMITTED_FOR",
            "description": "Contact submitted for job order",
            "cardinality": "many-to-many",
        },
        {
            "source": "CONTACT",
            "target": "MEMORY",
            "type": "HAS_MEMORY",
            "description": "Agent memories about contact",
            "cardinality": "one-to-many",
        },
        {
            "source": "CONTACT",
            "target": "INTERACTION",
            "type": "CONTACTED_BY",
            "description": "Agent interaction record",
            "cardinality": "one-to-many",
        },
        {
            "source": "CONTACT",
            "target": "BULLHORN_NOTE",
            "type": "REFERENCED_IN",
            "description": "Contact mentioned in CRM notes",
            "cardinality": "one-to-many",
        },
        {
            "source": "CONTACT",
            "target": "CONTACT",
            "type": "REFERRED_BY",
            "description": "Referral network relationship",
            "cardinality": "many-to-many",
        },
        {
            "source": "CONTACT",
            "target": "CONTACT",
            "type": "MANAGES",
            "description": "Neo4j manager-report relationship",
            "cardinality": "one-to-many",
        },
        {
            "source": "CONTACT",
            "target": "CONTACT",
            "type": "REPORTS_TO",
            "description": "Neo4j reporting chain",
            "cardinality": "many-to-one",
        },
        {
            "source": "CONTACT",
            "target": "PRIME_CONTRACTOR",
            "type": "PREVIOUSLY_AT",
            "description": "Historical employment via candidate_prime_history",
            "cardinality": "many-to-many",
        },
        {
            "source": "CONTACT",
            "target": "LOCATION",
            "type": "LOCATED_IN",
            "description": "Contact location hub",
            "cardinality": "many-to-one",
        },
        {
            "source": "CONTACT",
            "target": "CALL_BRIEFING",
            "type": "HAS_BRIEFING",
            "description": "Pre-call briefing generated",
            "cardinality": "one-to-many",
        },
        {
            "source": "CONTACT",
            "target": "TRANSCRIPT_INTEL",
            "type": "HAS_TRANSCRIPT",
            "description": "Call transcript intelligence",
            "cardinality": "one-to-many",
        },
        {
            "source": "CONTACT",
            "target": "RELATIONSHIP_SCORE",
            "type": "HAS_SCORE",
            "description": "Relationship strength score",
            "cardinality": "one-to-many",
        },
        {
            "source": "CONTACT",
            "target": "CONTACT_CLAIM",
            "type": "CLAIMED_BY",
            "description": "BD team ownership claim",
            "cardinality": "one-to-many",
        },
        # PRIME_CONTRACTOR relationships
        {
            "source": "PRIME_CONTRACTOR",
            "target": "PROGRAM",
            "type": "PRIMES_ON",
            "description": "Contractor is prime on program",
            "cardinality": "one-to-many",
        },
        {
            "source": "PRIME_CONTRACTOR",
            "target": "PROGRAM",
            "type": "SUBS_TO",
            "description": "Contractor is sub on program",
            "cardinality": "many-to-many",
        },
        {
            "source": "PRIME_CONTRACTOR",
            "target": "JOB",
            "type": "POSTED_JOB",
            "description": "Prime posted job order",
            "cardinality": "one-to-many",
        },
        {
            "source": "PRIME_CONTRACTOR",
            "target": "CONTACT",
            "type": "EMPLOYS",
            "description": "Prime employs contact",
            "cardinality": "one-to-many",
        },
        {
            "source": "PRIME_CONTRACTOR",
            "target": "PAST_PERFORMANCE",
            "type": "HAS_PERFORMANCE",
            "description": "Prime has past performance record",
            "cardinality": "one-to-many",
        },
        {
            "source": "PRIME_CONTRACTOR",
            "target": "PRIME_CONTRACTOR",
            "type": "COMPETES_WITH",
            "description": "Competitor relationship",
            "cardinality": "many-to-many",
        },
        {
            "source": "PRIME_CONTRACTOR",
            "target": "PRIME_CONTRACTOR",
            "type": "TEAMS_WITH",
            "description": "Teaming partner relationship",
            "cardinality": "many-to-many",
        },
        {
            "source": "PRIME_CONTRACTOR",
            "target": "LOCATION",
            "type": "COMPANY_LOCATED_IN",
            "description": "Company facility location",
            "cardinality": "many-to-many",
        },
        # PROGRAM relationships
        {
            "source": "PROGRAM",
            "target": "JOB",
            "type": "HAS_JOB",
            "description": "Program has associated job postings",
            "cardinality": "one-to-many",
        },
        {
            "source": "PROGRAM",
            "target": "CONTACT",
            "type": "HAS_CONTACT",
            "description": "Program has associated contacts",
            "cardinality": "one-to-many",
        },
        {
            "source": "PROGRAM",
            "target": "DOCUMENT",
            "type": "HAS_DOCUMENT",
            "description": "Program has associated documents",
            "cardinality": "one-to-many",
        },
        {
            "source": "PROGRAM",
            "target": "PAST_PERFORMANCE",
            "type": "HAS_PERFORMANCE",
            "description": "Program has past performance data",
            "cardinality": "one-to-many",
        },
        {
            "source": "PROGRAM",
            "target": "CONTRACT_OPPORTUNITY",
            "type": "HAS_OPPORTUNITY",
            "description": "Program generates procurement opportunity",
            "cardinality": "one-to-many",
        },
        {
            "source": "PROGRAM",
            "target": "FEDERAL_CONTRACT",
            "type": "HAS_CONTRACT",
            "description": "Program has federal contract(s)",
            "cardinality": "one-to-many",
        },
        {
            "source": "PROGRAM",
            "target": "LOCATION",
            "type": "LOCATED_AT",
            "description": "Program execution location",
            "cardinality": "many-to-many",
        },
        {
            "source": "PROGRAM",
            "target": "RECOMPETE_PREDICTION",
            "type": "HAS_PREDICTION",
            "description": "Recompete timeline prediction",
            "cardinality": "one-to-many",
        },
        # JOB relationships
        {
            "source": "JOB",
            "target": "PLACEMENT",
            "type": "FILLED_BY",
            "description": "Job filled by placement",
            "cardinality": "one-to-many",
        },
        {
            "source": "JOB",
            "target": "PROGRAM",
            "type": "MAPPED_TO",
            "description": "Job mapped to program by Engine2",
            "cardinality": "many-to-one",
        },
        {
            "source": "JOB",
            "target": "PRIME_CONTRACTOR",
            "type": "POSTED_BY",
            "description": "Job posted by prime",
            "cardinality": "many-to-one",
        },
        {
            "source": "JOB",
            "target": "ACTIVITY",
            "type": "HAS_ACTIVITY",
            "description": "Job has associated CRM activities",
            "cardinality": "one-to-many",
        },
        {
            "source": "JOB",
            "target": "WIN_PROBABILITY",
            "type": "HAS_WIN_PROB",
            "description": "ML win probability prediction",
            "cardinality": "one-to-one",
        },
        # PLACEMENT relationships
        {
            "source": "PLACEMENT",
            "target": "JOB",
            "type": "FOR_JOB",
            "description": "Placement for specific job",
            "cardinality": "many-to-one",
        },
        {
            "source": "PLACEMENT",
            "target": "CONTACT",
            "type": "OF_CANDIDATE",
            "description": "Placement of candidate",
            "cardinality": "many-to-one",
        },
        {
            "source": "PLACEMENT",
            "target": "PRIME_CONTRACTOR",
            "type": "AT_PRIME",
            "description": "Placement at prime site",
            "cardinality": "many-to-one",
        },
        # ACTIVITY relationships
        {
            "source": "ACTIVITY",
            "target": "JOB",
            "type": "REGARDING_JOB",
            "description": "Activity about job",
            "cardinality": "many-to-one",
        },
        {
            "source": "ACTIVITY",
            "target": "CONTACT",
            "type": "REGARDING_CONTACT",
            "description": "Activity about contact",
            "cardinality": "many-to-one",
        },
        # DOCUMENT relationships
        {
            "source": "DOCUMENT",
            "target": "PROGRAM",
            "type": "ABOUT_PROGRAM",
            "description": "Document references program",
            "cardinality": "many-to-many",
        },
        {
            "source": "DOCUMENT",
            "target": "PRIME_CONTRACTOR",
            "type": "ABOUT_CONTRACTOR",
            "description": "Document references contractor",
            "cardinality": "many-to-many",
        },
        # INTELLIGENCE_REPORT relationships
        {
            "source": "INTELLIGENCE_REPORT",
            "target": "PROGRAM",
            "type": "ANALYZES",
            "description": "Report analyzes program",
            "cardinality": "many-to-many",
        },
        {
            "source": "INTELLIGENCE_REPORT",
            "target": "PRIME_CONTRACTOR",
            "type": "COVERS",
            "description": "Report covers contractor",
            "cardinality": "many-to-many",
        },
        # FEDERAL_CONTRACT relationships
        {
            "source": "FEDERAL_CONTRACT",
            "target": "PRIME_CONTRACTOR",
            "type": "AWARDED_TO",
            "description": "Contract awarded to prime",
            "cardinality": "many-to-one",
        },
        {
            "source": "FEDERAL_CONTRACT",
            "target": "PROGRAM",
            "type": "COVERS",
            "description": "Contract covers program",
            "cardinality": "many-to-many",
        },
        # INSIGHT relationships
        {
            "source": "INSIGHT",
            "target": "GRAPH_ENTITY",
            "type": "ABOUT_ENTITY",
            "description": "Insight relates to graph entity",
            "cardinality": "many-to-one",
        },
        # SOURCE_FILE relationships
        {
            "source": "SOURCE_FILE",
            "target": "PROCESSING_STATS",
            "type": "HAS_STATS",
            "description": "Source file has processing stats",
            "cardinality": "one-to-many",
        },
        {
            "source": "SOURCE_FILE",
            "target": "DATA_QUALITY_LOG",
            "type": "HAS_ISSUES",
            "description": "Source file has quality issues",
            "cardinality": "one-to-many",
        },
        # GRAPH relationships
        {
            "source": "GRAPH_ENTITY",
            "target": "GRAPH_ENTITY",
            "type": "GRAPH_RELATIONSHIP",
            "description": "LightRAG knowledge graph edge",
            "cardinality": "many-to-many",
        },
        # FILE_NODE relationships
        {
            "source": "FILE_NODE",
            "target": "FILE_NODE",
            "type": "DERIVED_FROM",
            "description": "Data lineage: output derived from input",
            "cardinality": "many-to-many",
        },
        {
            "source": "FILE_NODE",
            "target": "FILE_NODE",
            "type": "DEPENDS_ON",
            "description": "Code dependency",
            "cardinality": "many-to-many",
        },
        {
            "source": "PROCESS_NODE",
            "target": "FILE_NODE",
            "type": "READS",
            "description": "Process reads file",
            "cardinality": "many-to-many",
        },
        {
            "source": "PROCESS_NODE",
            "target": "FILE_NODE",
            "type": "WRITES",
            "description": "Process writes file",
            "cardinality": "many-to-many",
        },
        # CONTRACT_WATCH relationships
        {
            "source": "CONTRACT_WATCH",
            "target": "FEDERAL_CONTRACT",
            "type": "MONITORS",
            "description": "Watch monitors contracts",
            "cardinality": "many-to-many",
        },
        {
            "source": "CONTRACT_WATCH",
            "target": "CONTRACT_OPPORTUNITY",
            "type": "MONITORS",
            "description": "Watch monitors opportunities",
            "cardinality": "many-to-many",
        },
        # SWARM/WORKFLOW relationships
        {
            "source": "SWARM_TASK",
            "target": "WORKFLOW_RUN",
            "type": "EXECUTES_VIA",
            "description": "Swarm uses workflow",
            "cardinality": "one-to-many",
        },
        # STRATEGIC relationships
        {
            "source": "STRATEGIC_PATTERN",
            "target": "PROGRAM",
            "type": "ABOUT_PROGRAM",
            "description": "Pattern detected for program",
            "cardinality": "many-to-one",
        },
        {
            "source": "PROPOSAL_ARTIFACT",
            "target": "PROGRAM",
            "type": "FOR_PROGRAM",
            "description": "Artifact for program bid",
            "cardinality": "many-to-one",
        },
        # REVENUE relationships
        {
            "source": "REVENUE_PLACEMENT",
            "target": "PROGRAM",
            "type": "ON_PROGRAM",
            "description": "Revenue placement on program",
            "cardinality": "many-to-one",
        },
        {
            "source": "REVENUE_PLACEMENT",
            "target": "CONTACT",
            "type": "OF_CONTRACTOR",
            "description": "Revenue placement of contractor",
            "cardinality": "many-to-one",
        },
        # FORECAST relationships
        {
            "source": "HIRING_FORECAST",
            "target": "PROGRAM",
            "type": "FORECASTS_FOR",
            "description": "Hiring forecast for program",
            "cardinality": "many-to-one",
        },
    ]


# =============================================================================
# DATA FLOWS
# =============================================================================


def _build_data_flows() -> list:
    return [
        {
            "name": "Apify Job Scraping",
            "source": "Career websites (Indeed, ClearanceJobs, etc.)",
            "target": "Engine1_Scraper/outputs/*.json",
            "transforms": ["web_scrape", "dedup", "normalize"],
            "trigger": "manual | cron",
            "entities_touched": ["JOB"],
        },
        {
            "name": "Program Mapping Pipeline",
            "source": "Engine1 scraped jobs + Federal_Programs CSV",
            "target": "Engine2 enriched jobs (JSON + CSV)",
            "transforms": [
                "parse",
                "standardize_18_fields",
                "match_programs",
                "score_bd_priority",
                "generate_playbooks",
                "export_notion_csv",
            ],
            "trigger": "manual",
            "entities_touched": ["JOB", "PROGRAM"],
        },
        {
            "name": "Contact Classification",
            "source": "Bullhorn candidates",
            "target": "Classified contacts with tier/priority",
            "transforms": [
                "regex_tier_match",
                "location_hub_map",
                "outreach_sequence_assign",
            ],
            "trigger": "manual",
            "entities_touched": ["CONTACT"],
        },
        {
            "name": "BD Scoring",
            "source": "Enriched jobs/contacts",
            "target": "Scored records (0-100 BD score)",
            "transforms": [
                "clearance_boost",
                "program_boost",
                "location_boost",
                "tier_multiplier",
                "confidence_weight",
            ],
            "trigger": "manual",
            "entities_touched": ["JOB", "CONTACT"],
        },
        {
            "name": "Bullhorn ETL",
            "source": "Bullhorn CRM CSV exports",
            "target": "bullhorn_master.db (293 MB, 13 tables)",
            "transforms": [
                "parse_csv",
                "normalize_names",
                "deduplicate",
                "link_fk",
                "compute_past_performance",
            ],
            "trigger": "manual",
            "entities_touched": [
                "CONTACT",
                "JOB",
                "PLACEMENT",
                "ACTIVITY",
                "PRIME_CONTRACTOR",
                "PROGRAM",
                "PAST_PERFORMANCE",
            ],
        },
        {
            "name": "Qdrant Indexing (Contacts)",
            "source": "bullhorn_master.db/candidates (426K rows)",
            "target": "qdrant:contacts (7,337 vectors)",
            "transforms": [
                "text_concat",
                "openai_embed_3_small",
                "uuid5_id",
                "classify_tier",
            ],
            "trigger": "manual (index_contacts_openai.py)",
            "entities_touched": ["CONTACT"],
        },
        {
            "name": "Qdrant Indexing (Small Collections)",
            "source": "bullhorn_master.db (jobs, programs, past_performance, prime_contractors)",
            "target": "qdrant:jobs, qdrant:programs, qdrant:documents, qdrant:primes",
            "transforms": ["text_concat", "openai_embed_3_small", "uuid5_id"],
            "trigger": "manual (index_small_collections.py)",
            "entities_touched": ["JOB", "PROGRAM", "DOCUMENT", "PRIME_CONTRACTOR"],
        },
        {
            "name": "Qdrant Indexing (Activities)",
            "source": "bullhorn_master.db/activities",
            "target": "qdrant:activities (500 vectors)",
            "transforms": ["text_concat", "openai_embed_3_small", "uuid5_id"],
            "trigger": "manual (index_parallel_worker.py)",
            "entities_touched": ["ACTIVITY"],
        },
        {
            "name": "Notion Sync",
            "source": "Notion databases (6 DBs)",
            "target": "Qdrant collections + dashboard JSON",
            "transforms": ["notion_query", "property_extract", "embed", "upsert"],
            "trigger": "manual | webhook",
            "entities_touched": ["CONTACT", "JOB", "PROGRAM"],
        },
        {
            "name": "SAM.gov Contract Monitoring",
            "source": "SAM.gov API",
            "target": "qdrant:federal_contracts + neo4j:Contract",
            "transforms": [
                "search_awards",
                "search_opportunities",
                "match_watches",
                "generate_alerts",
            ],
            "trigger": "manual | cron",
            "entities_touched": [
                "FEDERAL_CONTRACT",
                "CONTRACT_OPPORTUNITY",
                "CONTRACT_WATCH",
                "ALERT",
            ],
        },
        {
            "name": "LightRAG Graph Building",
            "source": "All Qdrant collections",
            "target": "bd_graph.db (entities + relationships)",
            "transforms": [
                "entity_extraction",
                "relationship_extraction",
                "graph_build",
            ],
            "trigger": "manual",
            "entities_touched": ["GRAPH_ENTITY", "GRAPH_RELATIONSHIP"],
        },
        {
            "name": "Neo4j Graph Ingestion",
            "source": "Qdrant contacts, programs, jobs",
            "target": "Neo4j (9 node types, 23 relationship types)",
            "transforms": [
                "extract_nodes",
                "extract_relationships",
                "merge_nodes",
                "create_edges",
            ],
            "trigger": "manual (POST /neo4j/ingest/*)",
            "entities_touched": [
                "CONTACT",
                "PROGRAM",
                "JOB",
                "PRIME_CONTRACTOR",
                "LOCATION",
            ],
        },
        {
            "name": "Dashboard JSON Export",
            "source": "bullhorn_master.db + Qdrant",
            "target": "dashboard/public/data/*.json (25 feeds)",
            "transforms": ["query", "aggregate", "format_json"],
            "trigger": "manual (dashboard_integration.py)",
            "entities_touched": [
                "CONTACT",
                "JOB",
                "PROGRAM",
                "PLACEMENT",
                "PAST_PERFORMANCE",
                "PRIME_CONTRACTOR",
            ],
        },
        {
            "name": "Dify Knowledge Bridge",
            "source": "Qdrant collections",
            "target": "Dify external knowledge API",
            "transforms": ["search", "format_dify_result"],
            "trigger": "on_request (Dify app call)",
            "entities_touched": ["CONTACT", "JOB", "PROGRAM"],
        },
        {
            "name": "Real-time Streaming Pipeline",
            "source": "SAM.gov + FPDS + Bullhorn streams",
            "target": "PostgreSQL + Kafka + webhooks",
            "transforms": [
                "ingest",
                "filter_relevance",
                "detect_recompete",
                "detect_competitor",
                "alert",
            ],
            "trigger": "continuous (Pathway)",
            "entities_touched": [
                "CONTRACT_OPPORTUNITY",
                "FEDERAL_CONTRACT",
                "ACTIVITY",
                "ALERT",
                "STREAMING_EVENT",
            ],
        },
        {
            "name": "Memory Consolidation",
            "source": "Episodic memories",
            "target": "Semantic facts + procedural insights",
            "transforms": [
                "scan_episodes",
                "extract_facts",
                "update_semantic",
                "generate_insights",
            ],
            "trigger": "manual | scheduled",
            "entities_touched": ["MEMORY", "INSIGHT"],
        },
        {
            "name": "ML Model Training Pipeline",
            "source": "Qdrant contacts + activities + outcomes",
            "target": "ML models (placement prediction, NER, topic clustering)",
            "transforms": ["feature_extract", "train_model", "evaluate", "deploy"],
            "trigger": "manual (POST /ml/predict/train)",
            "entities_touched": ["CONTACT", "JOB", "PLACEMENT", "WIN_PROBABILITY"],
        },
        {
            "name": "Weekly BD Intelligence Report",
            "source": "All collections + agent analysis",
            "target": "Weekly report JSON + email",
            "transforms": [
                "aggregate_pipeline",
                "analyze_outreach",
                "scan_competitive",
                "generate_summary",
            ],
            "trigger": "scheduled | manual (POST /reports/weekly)",
            "entities_touched": [
                "WEEKLY_REPORT",
                "CONTACT",
                "JOB",
                "PROGRAM",
                "ACTIVITY",
            ],
        },
    ]


# =============================================================================
# DATABASES
# =============================================================================


def _build_databases() -> dict:
    return {
        "qdrant_collections": [
            {
                "name": "contacts",
                "vector_size": 1536,
                "distance": "Cosine",
                "embedding_model": "text-embedding-3-small",
                "record_count": 7337,
                "search_type": "dense",
                "payload_fields": [
                    "name",
                    "first_name",
                    "last_name",
                    "title",
                    "company",
                    "program",
                    "email",
                    "phone",
                    "tier",
                    "bd_priority",
                    "clearance",
                    "city",
                    "state",
                    "location_hub",
                    "status",
                    "skills",
                    "notes",
                    "source_db",
                    "_indexed_at",
                    "_embedding_model",
                ],
            },
            {
                "name": "programs",
                "vector_size": 1536,
                "distance": "Cosine",
                "embedding_model": "text-embedding-3-small",
                "record_count": 401,
                "search_type": "dense",
                "payload_fields": [
                    "name",
                    "acronym",
                    "agency",
                    "sub_agency",
                    "prime_contractor",
                    "location",
                    "contract_value",
                    "description",
                    "mission_area",
                    "contract_vehicle",
                    "bd_priority",
                    "status",
                    "_indexed_at",
                    "_embedding_model",
                ],
            },
            {
                "name": "jobs",
                "vector_size": 1536,
                "distance": "Cosine",
                "embedding_model": "text-embedding-3-small",
                "record_count": 4,
                "search_type": "dense",
                "payload_fields": [
                    "title",
                    "company",
                    "location",
                    "clearance",
                    "description",
                    "mapped_program",
                    "bd_priority_score",
                    "pipeline_stage",
                    "status",
                    "skills",
                    "_indexed_at",
                    "_embedding_model",
                ],
            },
            {
                "name": "documents",
                "vector_size": 1536,
                "distance": "Cosine",
                "embedding_model": "text-embedding-3-small",
                "record_count": 205,
                "search_type": "dense",
                "payload_fields": [
                    "filename",
                    "filepath",
                    "doc_type",
                    "title",
                    "summary",
                    "tags",
                    "type",
                    "chunk_index",
                    "total_chunks",
                    "_indexed_at",
                    "_embedding_model",
                ],
            },
            {
                "name": "activities",
                "vector_size": 1536,
                "distance": "Cosine",
                "embedding_model": "text-embedding-3-small",
                "record_count": 500,
                "search_type": "dense",
                "payload_fields": [
                    "activity_type",
                    "content",
                    "subject",
                    "date",
                    "contact_id",
                    "job_id",
                    "action",
                    "source_db",
                    "_indexed_at",
                    "_embedding_model",
                ],
            },
            {
                "name": "primes",
                "vector_size": 1536,
                "distance": "Cosine",
                "embedding_model": "text-embedding-3-small",
                "record_count": 41,
                "search_type": "dense",
                "payload_fields": [
                    "name",
                    "aliases",
                    "headquarters",
                    "naics_codes",
                    "contract_vehicles",
                    "total_jobs",
                    "total_placements",
                    "total_revenue",
                    "category",
                    "_indexed_at",
                    "_embedding_model",
                ],
            },
            {
                "name": "bullhorn_notes",
                "vector_size": 1536,
                "distance": "Cosine",
                "embedding_model": "text-embedding-3-small",
                "record_count": "50000+",
                "search_type": "hybrid",
                "payload_fields": [
                    "note_body",
                    "comments",
                    "about",
                    "action",
                    "note_type",
                    "personReference",
                    "_source",
                ],
            },
            {
                "name": "federal_contracts",
                "vector_size": 1536,
                "distance": "Cosine",
                "embedding_model": "text-embedding-3-small",
                "record_count": "unknown",
                "search_type": "hybrid",
                "payload_fields": [
                    "title",
                    "description",
                    "agency",
                    "contractor",
                    "contract_vehicle",
                    "status",
                ],
            },
            {
                "name": "intelligence_reports",
                "vector_size": 1536,
                "distance": "Cosine",
                "embedding_model": "text-embedding-3-small",
                "record_count": "unknown",
                "search_type": "hybrid",
                "payload_fields": [
                    "content",
                    "title",
                    "summary",
                    "source",
                    "report_type",
                    "classification",
                    "date",
                ],
            },
        ],
        "neo4j_graph": {
            "node_types": [
                {
                    "type": "Person",
                    "properties": [
                        "name",
                        "title",
                        "tier",
                        "bd_priority",
                        "email",
                        "phone",
                        "linkedin",
                        "location_hub",
                        "functional_area",
                        "program",
                        "company",
                        "source_db",
                        "first_name",
                        "last_name",
                    ],
                },
                {
                    "type": "Company",
                    "properties": [
                        "name",
                        "type",
                        "revenue",
                        "employee_count",
                        "headquarters",
                        "is_defense_prime",
                        "website",
                    ],
                },
                {
                    "type": "Program",
                    "properties": [
                        "name",
                        "acronym",
                        "value",
                        "agency_owner",
                        "prime_contractor",
                        "pop_start",
                        "pop_end",
                        "clearance_req",
                        "program_type",
                        "confidence_level",
                        "contract_vehicle",
                        "hiring_velocity",
                        "recompete_date",
                        "naics",
                    ],
                },
                {
                    "type": "Job",
                    "properties": [
                        "title",
                        "status",
                        "pay_rate",
                        "bill_rate",
                        "clearance",
                        "date_added",
                        "employment_type",
                        "location",
                        "source_url",
                        "bd_priority",
                        "functional_area",
                    ],
                },
                {
                    "type": "Contract",
                    "properties": [
                        "vehicle",
                        "value",
                        "naics",
                        "set_aside",
                        "pop_start",
                        "pop_end",
                        "award_date",
                        "contract_number",
                    ],
                },
                {
                    "type": "Location",
                    "properties": [
                        "city",
                        "state",
                        "coordinates_lat",
                        "coordinates_lon",
                        "hub_name",
                        "military_installation",
                        "region",
                    ],
                },
                {
                    "type": "Interaction",
                    "properties": [
                        "date",
                        "type",
                        "summary",
                        "sentiment",
                        "author",
                        "action",
                        "status",
                        "note_body",
                    ],
                },
                {
                    "type": "File",
                    "properties": [
                        "path",
                        "name",
                        "type",
                        "extension",
                        "size_bytes",
                        "hash",
                        "modified",
                        "engine",
                        "is_input",
                        "is_output",
                    ],
                },
                {
                    "type": "Process",
                    "properties": [
                        "name",
                        "script_path",
                        "engine",
                        "description",
                        "last_run",
                        "run_count",
                        "avg_duration_seconds",
                    ],
                },
            ],
            "relationship_types": [
                "WORKS_AT",
                "MANAGES",
                "REPORTS_TO",
                "LOCATED_IN",
                "CONTACTED_BY",
                "PRIMES_ON",
                "SUBS_TO",
                "COMPETES_WITH",
                "COMPANY_LOCATED_IN",
                "OWNED_BY",
                "LOCATED_AT",
                "HAS_CONTRACT",
                "REQUIRES_CLEARANCE",
                "POSTED_BY",
                "MAPPED_TO",
                "JOB_AT",
                "REQUIRES_SKILL",
                "AWARDED_TO",
                "COVERS",
                "BETWEEN",
                "ABOUT",
                "BY_USER",
                "DERIVED_FROM",
                "DEPENDS_ON",
                "READS",
                "WRITES",
            ],
        },
        "sqlite_databases": [
            {
                "name": "bullhorn_master.db",
                "path": "Engine7_BullhornETL/data/bullhorn_master.db",
                "size_mb": 293,
                "tables": [
                    "jobs",
                    "candidates",
                    "placements",
                    "activities",
                    "prime_contractors",
                    "programs",
                    "past_performance",
                    "job_program_mapping",
                    "job_prime_mapping",
                    "candidate_prime_history",
                    "source_files",
                    "data_quality_log",
                    "processing_stats",
                ],
            },
            {
                "name": "bd_graph.db",
                "path": "Engine8_Knowledge/data/bd_graph.db",
                "size_mb": 0.8,
                "tables": ["entities", "relationships"],
            },
            {
                "name": "memories.db",
                "path": "Engine8_Knowledge/data/memories.db",
                "size_mb": 0.04,
                "tables": ["memories", "interactions", "insights"],
            },
            {
                "name": "page_index.db",
                "path": "Engine8_Knowledge/data/page_index.db",
                "size_mb": 0.01,
                "tables": ["pages"],
            },
            {
                "name": "checkpoints_meta.db",
                "path": "Engine8_Knowledge/data/checkpoints_meta.db",
                "size_mb": 0.01,
                "tables": ["threads", "checkpoint_snapshots"],
            },
            {
                "name": "langgraph_checkpoints.db",
                "path": "Engine8_Knowledge/data/langgraph_checkpoints.db",
                "size_mb": 0.01,
                "tables": ["workflow_metadata"],
            },
        ],
        "notion_databases": [
            {
                "name": "Program Mapping Intelligence Hub",
                "id": "0a0d7e46-3d88-40b6-853a-3c9680347644",
                "properties": [
                    "Job Title",
                    "Company",
                    "Location",
                    "Clearance",
                    "Matched Program",
                    "BD Score",
                    "Priority Tier",
                    "Employment Type",
                    "Outreach Status",
                    "Duration",
                    "BD Formula Message",
                    "PTS Available Contractors",
                ],
            },
            {
                "name": "Federal Programs",
                "id": "9db40fce-0781-42b9-902c-d4b0263b1e23",
                "properties": [
                    "Program Name",
                    "Acronym",
                    "Agency",
                    "Prime Contractor",
                    "Contract Value",
                    "BD Priority",
                    "Hiring Velocity",
                    "Mission Area",
                    "BD Approach Notes",
                    "Next Actions",
                ],
            },
            {
                "name": "Contractors Database",
                "id": "ca67175b-df3d-442d-a2e7-cc24e9a1bf78",
                "properties": [
                    "Name",
                    "Relationship Status",
                    "PTS Placements Made",
                    "Active Placements",
                    "Portfolio Value",
                    "Last Engagement Date",
                ],
            },
            {
                "name": "DCGS Contacts Full",
                "id": "2ccdef65-baa5-80d0-9b66-c67d66e7a54d",
                "properties": [
                    "Name",
                    "Title",
                    "Company",
                    "Program",
                    "Clearance",
                    "Hierarchy Tier",
                    "BD Priority",
                    "Location Hub",
                    "Last Contact Date",
                    "Outreach History",
                    "Relationship Strength",
                ],
            },
            {
                "name": "Contract Vehicles Master",
                "id": "e1166305-1b1f-4812-b665-bcfa6a87a2ab",
                "properties": [
                    "Vehicle Name",
                    "Contract Number",
                    "Agency",
                    "Prime Contractor",
                    "Value",
                    "Period",
                ],
            },
            {
                "name": "GDIT Other Contacts",
                "id": "c1b1d358-9d82-4f03-b77c-db43d9795c6f",
                "properties": ["Name", "Title", "Company", "Program", "Contact Info"],
            },
        ],
        "api_endpoints": {
            "total_estimated": 340,
            "core_api": {
                "file": "Engine8_Knowledge/api.py",
                "prefix": "/",
                "endpoints": 67,
            },
            "unified_v2": {
                "file": "api/unified_endpoints.py",
                "prefix": "/api/v2",
                "endpoints": 13,
            },
            "engine8_sub_routers": [
                {"file": "api_routers/hybrid_endpoints.py", "endpoints": 7},
                {"file": "api_routers/phase7_endpoints.py", "endpoints": 13},
                {"file": "api_routers/phase8a_pipeline.py", "endpoints": 3},
                {"file": "api_routers/phase9a_competitive.py", "endpoints": 3},
                {"file": "api_routers/phase10a_reports.py", "endpoints": 1},
                {"file": "api_routers/scrape_api_v2.py", "endpoints": 20},
                {"file": "api_routers/memory_api.py", "endpoints": 12},
                {"file": "api_routers/mcp_api.py", "endpoints": 6},
                {"file": "api_routers/org_chart_api.py", "endpoints": 10},
                {"file": "api_routers/ml_api.py", "endpoints": 12},
                {"file": "api_routers/optimizer_api.py", "endpoints": 10},
                {"file": "api_routers/monitoring_api.py", "endpoints": 8},
                {"file": "search/search_routes.py", "endpoints": 9},
                {"file": "graph/neo4j_routes.py", "endpoints": 13},
                {"file": "graph/analytics_routes.py", "endpoints": 8},
                {"file": "workflows/workflow_routes.py", "endpoints": 18},
                {"file": "automation/routes.py", "endpoints": 10},
                {"file": "agents/api_routes.py", "endpoints": 6},
                {"file": "agents/autonomous/routes.py", "endpoints": 7},
                {"file": "ml/routes.py", "endpoints": 3},
                {"file": "integrations/routes.py", "endpoints": 5},
                {"file": "realtime/routes.py", "endpoints": 4},
                {"file": "bd_lightrag/routes.py", "endpoints": 3},
                {"file": "processors/routes.py", "endpoints": 4},
                {"file": "embeddings/routes.py", "endpoints": 6},
                {"file": "retrieval/routes.py", "endpoints": 3},
                {"file": "retrieval/ultra_rag_routes.py", "endpoints": 3},
            ],
            "src_api_routers": [
                {
                    "file": "src/api/knowledge_api.py",
                    "phase": "39A",
                    "endpoints": 15,
                    "focus": "Temporal knowledge, entity resolution",
                },
                {
                    "file": "src/api/relationship_api.py",
                    "phase": "34A",
                    "endpoints": 14,
                    "focus": "Relationship strength, influence scoring",
                },
                {
                    "file": "src/api/proposal_api.py",
                    "phase": "35A",
                    "endpoints": 10,
                    "focus": "Proposal artifacts, compliance matrices",
                },
                {
                    "file": "src/api/revenue_api.py",
                    "phase": "36A",
                    "endpoints": 16,
                    "focus": "Revenue tracking, margin analysis, ROI",
                },
                {
                    "file": "src/api/tenant_api.py",
                    "phase": "37A",
                    "endpoints": 21,
                    "focus": "Multi-tenancy, auth, RBAC",
                },
                {
                    "file": "src/api/data_quality_api.py",
                    "phase": "38A",
                    "endpoints": 17,
                    "focus": "Quality scoring, self-healing, lineage",
                },
                {
                    "file": "src/api/rag_api.py",
                    "phase": "40A",
                    "endpoints": 10,
                    "focus": "Agentic RAG, query decomposition",
                },
                {
                    "file": "src/api/swarm_api.py",
                    "phase": "41A",
                    "endpoints": 10,
                    "focus": "Multi-agent swarms, DAG execution",
                },
                {
                    "file": "src/api/memory_api.py",
                    "phase": "42A",
                    "endpoints": 12,
                    "focus": "5-layer memory, consolidation",
                },
                {
                    "file": "src/api/governance_api.py",
                    "phase": "43A",
                    "endpoints": 12,
                    "focus": "Data catalog, schema registry, SLAs",
                },
                {
                    "file": "src/api/intelligence_api.py",
                    "phase": "44A",
                    "endpoints": 13,
                    "focus": "Meta-learning, strategic patterns",
                },
                {
                    "file": "src/api/mcp_api.py",
                    "phase": "45A",
                    "endpoints": 10,
                    "focus": "MCP ecosystem orchestration",
                },
                {
                    "file": "src/api/voice_api.py",
                    "phase": "46A",
                    "endpoints": 12,
                    "focus": "Call briefings, transcript intel",
                },
                {
                    "file": "src/api/embeddings_api.py",
                    "phase": "47A",
                    "endpoints": 12,
                    "focus": "Fine-tuning, benchmarking, A/B tests",
                },
                {
                    "file": "src/api/geo_api.py",
                    "phase": "48A",
                    "endpoints": 10,
                    "focus": "Geocoding, spatial queries, clusters",
                },
                {
                    "file": "src/api/workflows_api.py",
                    "phase": "49A",
                    "endpoints": 12,
                    "focus": "Temporal workflows, task queues",
                },
                {
                    "file": "src/api/collaboration_api.py",
                    "phase": "50A",
                    "endpoints": 12,
                    "focus": "CRDT rooms, contact claiming, intel feed",
                },
                {
                    "file": "src/api/simulation_api.py",
                    "phase": "51A",
                    "endpoints": 14,
                    "focus": "Causal inference, digital twins",
                },
                {
                    "file": "src/api/security_api.py",
                    "phase": "52A",
                    "endpoints": 14,
                    "focus": "ABAC, audit trail, field encryption",
                },
                {
                    "file": "src/api/observability_api.py",
                    "phase": "53A",
                    "endpoints": 12,
                    "focus": "Tracing, metrics, SLOs",
                },
                {
                    "file": "src/api/experimentation_api.py",
                    "phase": "55A",
                    "endpoints": 12,
                    "focus": "Feature flags, A/B testing",
                },
                {
                    "file": "src/api/resilience_api.py",
                    "phase": "54A",
                    "endpoints": 12,
                    "focus": "Circuit breakers, chaos engineering",
                },
                {
                    "file": "src/api/scaling_api.py",
                    "phase": "57A",
                    "endpoints": 12,
                    "focus": "Connection pools, replicas, auto-scaling",
                },
                {
                    "file": "src/api/pwa_api.py",
                    "phase": "58A",
                    "endpoints": 10,
                    "focus": "PWA, push notifications, offline sync",
                },
                {
                    "file": "src/api/streaming_api.py",
                    "phase": "31A",
                    "endpoints": 14,
                    "focus": "Event bus, WebSocket, workflows",
                },
                {
                    "file": "src/api/predictive_api.py",
                    "phase": "32A",
                    "endpoints": 14,
                    "focus": "Win probability, hiring forecasts",
                },
                {
                    "file": "src/api/nlq_api.py",
                    "phase": "33A",
                    "endpoints": 9,
                    "focus": "Natural language queries, autocomplete",
                },
            ],
        },
        "csv_sources": [
            {
                "path": "engine_data/Engine2_ProgramMapping/Federal Programs MASTER V4.csv",
                "columns": [
                    "Program Name",
                    "Acronym",
                    "Agency",
                    "Prime Contractor",
                    "Contract Number",
                    "Contract Value",
                    "Contract Description",
                    "Match Confidence",
                    "Match Score",
                ],
            },
            {
                "path": "engine_data/Engine3_OrgChart/Contact_Search_List_MASTER.csv",
                "columns": [
                    "Job Source",
                    "Job Number",
                    "Job Title",
                    "Job Location",
                    "Security Clearance",
                    "Matched Programs",
                    "Prime Contractors",
                    "Program Locations",
                    "Target Titles (Bullhorn)",
                    "Search Keywords (ZoomInfo)",
                    "LinkedIn Search",
                    "Match Score",
                    "Match Reasons",
                ],
            },
            {
                "path": "engine_data/Engine3_OrgChart/Contacts_TEMPLATE.csv",
                "columns": [
                    "Name",
                    "Job Title",
                    "Email Address",
                    "Phone",
                    "LinkedIn URL",
                    "Company",
                    "Program",
                    "Location",
                    "Clearance",
                    "Hierarchy Tier",
                    "BD Priority",
                    "Location Hub",
                    "Functional Area",
                    "Last Contact Date",
                    "Notes",
                    "Source",
                ],
            },
            {
                "path": "engine_data/Engine2_ProgramMapping/Programs_KB_TEMPLATE.csv",
                "columns": [
                    "Program Name",
                    "Acronym",
                    "Agency Owner",
                    "Prime Contractor",
                    "Known Subcontractors",
                    "Contract Value",
                    "Contract Vehicle",
                    "Key Locations",
                    "Clearance Requirements",
                    "Typical Roles",
                    "Keywords",
                    "PTS Involvement",
                    "Priority Level",
                    "Pain Points",
                    "Notes",
                ],
            },
            {
                "path": "engine_data/Engine1_Scraper/Jobs_Mapped_to_Programs_MASTER.csv",
                "columns": [
                    "Job Source",
                    "Job Number",
                    "Job Title",
                    "Job Location",
                    "Security Clearance",
                    "Employment Type",
                    "Date Posted",
                    "Matched Program",
                    "Program Acronym",
                    "Program Agency",
                    "Prime Contractor",
                    "Program Location",
                    "Contract Number",
                    "Match Score",
                    "Match Confidence",
                    "Match Reasons",
                    "Job URL",
                ],
            },
            {
                "path": "Engine7_BullhornETL/colton_scurry_analysis/master_notes.csv",
                "columns": [
                    "source_sheet",
                    "department",
                    "note_author",
                    "date_added",
                    "type",
                    "action",
                    "about",
                    "status",
                    "note_body_raw",
                    "note_body_clean",
                    "extracted_primes",
                    "extracted_programs",
                    "extracted_contracts",
                    "extracted_roles",
                    "extracted_locations",
                    "extracted_headcount",
                    "extracted_bill_rates",
                    "extracted_dates_mentioned",
                    "extracted_experience_levels",
                    "extracted_skills",
                    "extracted_acronyms",
                    "extracted_emails",
                    "extracted_phone_numbers",
                ],
            },
            {
                "path": "docs/N8N-Builder.Capture-MCP-server/bd_targets.csv",
                "columns": [
                    "Program Name",
                    "Acronym",
                    "Agency",
                    "BD Priority",
                    "Prime Contractor",
                    "Contract Value",
                    "Recompete Date",
                    "Period of Performance",
                    "Key Locations",
                    "Contract Number",
                ],
            },
            {
                "path": "docs/N8N-Builder.Capture-MCP-server/subaward_intelligence.csv",
                "columns": [
                    "Program Name",
                    "Acronym",
                    "Agency",
                    "Prime Contractor",
                    "Contract Number",
                    "Contract Value",
                    "Subaward Count",
                    "Subaward Total",
                    "Recipient UEI",
                    "Recipient Name",
                    "City",
                    "State",
                ],
            },
        ],
        "streaming_schemas": [
            {
                "name": "SAMOpportunitySchema",
                "source": "SAM.gov",
                "fields": [
                    "notice_id",
                    "title",
                    "agency",
                    "posted_date",
                    "response_deadline",
                    "set_aside",
                    "naics_code",
                    "description",
                    "estimated_value",
                    "place_of_performance",
                ],
            },
            {
                "name": "FPDSContractSchema",
                "source": "FPDS",
                "fields": [
                    "contract_id",
                    "vendor_name",
                    "agency",
                    "award_date",
                    "award_amount",
                    "pop_start_date",
                    "pop_end_date",
                    "naics_code",
                    "description",
                    "contract_type",
                ],
            },
            {
                "name": "BullhornActivitySchema",
                "source": "Bullhorn",
                "fields": [
                    "activity_id",
                    "contact_id",
                    "activity_type",
                    "timestamp",
                    "notes",
                    "outcome",
                ],
            },
            {
                "name": "AlertSchema",
                "source": "Generated",
                "fields": [
                    "alert_id",
                    "alert_type",
                    "title",
                    "description",
                    "priority",
                    "source_id",
                    "timestamp",
                    "metadata",
                ],
            },
        ],
    }


# =============================================================================
# ENGINES
# =============================================================================


def _build_engines() -> list:
    return [
        {
            "id": "engine1",
            "name": "Apify Job Scraper",
            "path": "Engine1_Scraper/",
            "status": "configured",
        },
        {
            "id": "engine2",
            "name": "Program Mapping",
            "path": "Engine2_ProgramMapping/",
            "status": "complete",
            "key_scripts": [
                "pipeline.py",
                "job_standardizer.py",
                "program_mapper.py",
                "exporters.py",
            ],
        },
        {
            "id": "engine3",
            "name": "OrgChart Contact Classification",
            "path": "Engine3_OrgChart/",
            "status": "complete",
            "key_scripts": ["contact_classifier.py"],
        },
        {
            "id": "engine4",
            "name": "BD Playbook Generator",
            "path": "Engine4_Playbook/",
            "status": "complete",
            "key_scripts": ["bd_playbook_generator.py"],
        },
        {
            "id": "engine5",
            "name": "BD Priority Scoring",
            "path": "Engine5_Scoring/",
            "status": "complete",
            "key_scripts": ["bd_scoring.py"],
        },
        {
            "id": "engine6",
            "name": "QA & Alerts",
            "path": "Engine6_QA/",
            "status": "in_progress",
        },
        {
            "id": "engine7",
            "name": "Bullhorn ETL",
            "path": "Engine7_BullhornETL/",
            "status": "complete",
            "database": "bullhorn_master.db (293 MB, 13 tables)",
        },
        {
            "id": "engine8",
            "name": "AI Knowledge System",
            "path": "Engine8_Knowledge/",
            "status": "complete",
            "server": "http://localhost:8100",
            "endpoints": 340,
            "collections": 9,
            "agents": 13,
        },
    ]


# =============================================================================
# DIFY TOOLS
# =============================================================================


def _build_dify_tools() -> list:
    return [
        {"name": "qdrant_search", "category": "Search & RAG"},
        {"name": "qdrant_smart_query", "category": "Search & RAG"},
        {"name": "qdrant_hybrid_search", "category": "Search & RAG"},
        {"name": "qdrant_rag", "category": "Search & RAG"},
        {"name": "qdrant_contacts", "category": "Contacts & Companies"},
        {"name": "qdrant_programs", "category": "Contacts & Companies"},
        {"name": "qdrant_jobs", "category": "Contacts & Companies"},
        {"name": "graph_query", "category": "Knowledge Graph"},
        {"name": "graph_program_ecosystem", "category": "Knowledge Graph"},
        {"name": "graph_contact_network", "category": "Knowledge Graph"},
        {"name": "graph_teaming_path", "category": "Knowledge Graph"},
        {"name": "memory_search", "category": "Memory"},
        {"name": "memory_contact_context", "category": "Memory"},
        {"name": "bd_strategy_agent", "category": "AI Agents"},
        {"name": "company_research_agent", "category": "AI Agents"},
        {"name": "contact_finder_agent", "category": "AI Agents"},
        {"name": "program_intel_agent", "category": "AI Agents"},
        {"name": "crewai_analyze_program", "category": "Multi-Agent Workflows"},
        {"name": "crewai_prepare_outreach", "category": "Multi-Agent Workflows"},
        {"name": "crewai_weekly_intel", "category": "Multi-Agent Workflows"},
        {"name": "n8n_job_scraper", "category": "Automation"},
        {"name": "n8n_hot_lead_alert", "category": "Automation"},
        {"name": "n8n_weekly_report", "category": "Automation"},
        {"name": "n8n_master_pipeline", "category": "Automation"},
        {"name": "notion_query", "category": "External"},
        {"name": "apify_scrape", "category": "External"},
    ]


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    arch = build_architecture()

    output_path = os.path.join(ROOT, "data_architecture_bd_engine.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(arch, f, indent=2, ensure_ascii=False)

    stats = arch["scan_stats"]
    print(f"Architecture extraction complete for {arch['project_id']}")
    print(f"Files scanned: {stats['files_scanned']}")
    print(f"Entities found: {stats['entities_found']}")
    print(f"Properties found: {stats['properties_found']}")
    print(f"Relationships found: {stats['relationships_found']}")
    print(f"Aliases found: {stats['aliases_found']}")
    print(f"Data flows found: {stats['data_flows_found']}")
    print(f"Output: {output_path}")
