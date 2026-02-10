"""
Phase 21A — Neo4j Graph Schema

Defines 7 node types, 20+ relationship types, constraints, and indexes
for the BD Intelligence Knowledge Graph.

Usage:
    from Engine8_Knowledge.graph.schema import apply_schema
    from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager
    mgr = get_neo4j_manager()
    apply_schema(mgr)
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Node type definitions
# ---------------------------------------------------------------------------

NODE_TYPES = {
    "Person": {
        "description": "Contact / person in the BD network",
        "properties": [
            "name", "title", "tier", "bd_priority", "email", "phone",
            "linkedin", "location_hub", "functional_area", "program",
            "company", "source_db", "first_name", "last_name",
        ],
    },
    "Company": {
        "description": "Contractor, agency, or staffing firm",
        "properties": [
            "name", "type", "revenue", "employee_count", "headquarters",
            "is_defense_prime", "website",
        ],
    },
    "Program": {
        "description": "Federal defense program or contract",
        "properties": [
            "name", "acronym", "value", "agency_owner", "prime_contractor",
            "pop_start", "pop_end", "clearance_req", "program_type",
            "confidence_level", "contract_vehicle", "hiring_velocity",
            "recompete_date", "naics",
        ],
    },
    "Job": {
        "description": "Job posting / opening",
        "properties": [
            "title", "status", "pay_rate", "bill_rate", "clearance",
            "date_added", "employment_type", "location", "source_url",
            "bd_priority", "functional_area",
        ],
    },
    "Contract": {
        "description": "Government contract vehicle",
        "properties": [
            "vehicle", "value", "naics", "set_aside", "pop_start",
            "pop_end", "award_date", "contract_number",
        ],
    },
    "Location": {
        "description": "Physical location / military installation",
        "properties": [
            "city", "state", "coordinates_lat", "coordinates_lon",
            "hub_name", "military_installation", "region",
        ],
    },
    "Interaction": {
        "description": "Call, email, meeting, or LinkedIn interaction",
        "properties": [
            "date", "type", "summary", "sentiment", "author",
            "action", "status", "note_body",
        ],
    },
}


# ---------------------------------------------------------------------------
# Relationship type definitions
# ---------------------------------------------------------------------------

RELATIONSHIP_TYPES = {
    "WORKS_AT": {"from": "Person", "to": "Company", "props": ["since", "title"]},
    "MANAGES": {"from": "Person", "to": "Program", "props": ["role"]},
    "REPORTS_TO": {"from": "Person", "to": "Person", "props": ["inferred"]},
    "LOCATED_IN": {"from": "Person", "to": "Location", "props": []},
    "CONTACTED_BY": {"from": "Person", "to": "Interaction", "props": []},
    "PRIMES_ON": {"from": "Company", "to": "Program", "props": ["contract_value", "vehicle"]},
    "SUBS_TO": {"from": "Company", "to": "Company", "props": ["on_program"]},
    "COMPETES_WITH": {"from": "Company", "to": "Company", "props": []},
    "COMPANY_LOCATED_IN": {"from": "Company", "to": "Location", "props": []},
    "OWNED_BY": {"from": "Program", "to": "Company", "props": []},
    "LOCATED_AT": {"from": "Program", "to": "Location", "props": []},
    "HAS_CONTRACT": {"from": "Program", "to": "Contract", "props": []},
    "REQUIRES_CLEARANCE": {"from": "Program", "to": "Program", "props": ["level"]},
    "POSTED_BY": {"from": "Job", "to": "Company", "props": []},
    "MAPPED_TO": {"from": "Job", "to": "Program", "props": ["confidence_score"]},
    "JOB_AT": {"from": "Job", "to": "Location", "props": []},
    "REQUIRES_SKILL": {"from": "Job", "to": "Job", "props": ["skill_name"]},
    "AWARDED_TO": {"from": "Contract", "to": "Company", "props": []},
    "COVERS": {"from": "Contract", "to": "Program", "props": []},
    "BETWEEN": {"from": "Interaction", "to": "Person", "props": []},
    "ABOUT": {"from": "Interaction", "to": "Program", "props": []},
    "BY_USER": {"from": "Interaction", "to": "Person", "props": []},
}


# ---------------------------------------------------------------------------
# Constraints and indexes
# ---------------------------------------------------------------------------

CONSTRAINTS = [
    # Unique constraints
    "CREATE CONSTRAINT person_email IF NOT EXISTS FOR (p:Person) REQUIRE p.email IS UNIQUE",
    "CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT program_acronym IF NOT EXISTS FOR (pr:Program) REQUIRE pr.acronym IS UNIQUE",
    "CREATE CONSTRAINT contract_number IF NOT EXISTS FOR (ct:Contract) REQUIRE ct.contract_number IS UNIQUE",
]

INDEXES = [
    # Standard indexes
    "CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name)",
    "CREATE INDEX person_tier IF NOT EXISTS FOR (p:Person) ON (p.tier)",
    "CREATE INDEX person_company IF NOT EXISTS FOR (p:Person) ON (p.company)",
    "CREATE INDEX job_status IF NOT EXISTS FOR (j:Job) ON (j.status)",
    "CREATE INDEX program_name IF NOT EXISTS FOR (pr:Program) ON (pr.name)",
    "CREATE INDEX program_agency IF NOT EXISTS FOR (pr:Program) ON (pr.agency_owner)",
    "CREATE INDEX location_city IF NOT EXISTS FOR (l:Location) ON (l.city)",
    "CREATE INDEX location_state IF NOT EXISTS FOR (l:Location) ON (l.state)",
    "CREATE INDEX interaction_date IF NOT EXISTS FOR (i:Interaction) ON (i.date)",
    "CREATE INDEX interaction_type IF NOT EXISTS FOR (i:Interaction) ON (i.type)",
    "CREATE INDEX company_type IF NOT EXISTS FOR (c:Company) ON (c.type)",
]

FULLTEXT_INDEXES = [
    # Full-text indexes for fuzzy search
    """CREATE FULLTEXT INDEX person_fulltext IF NOT EXISTS
       FOR (p:Person) ON EACH [p.name, p.title, p.company]""",
    """CREATE FULLTEXT INDEX company_fulltext IF NOT EXISTS
       FOR (c:Company) ON EACH [c.name]""",
    """CREATE FULLTEXT INDEX program_fulltext IF NOT EXISTS
       FOR (pr:Program) ON EACH [pr.name, pr.acronym]""",
]


# ---------------------------------------------------------------------------
# Schema application
# ---------------------------------------------------------------------------

def apply_schema(manager: "Neo4jManager") -> dict:
    """Apply all constraints and indexes to Neo4j. Idempotent — safe to run multiple times.

    Args:
        manager: Neo4jManager instance (from neo4j_manager.py)

    Returns:
        Summary of applied constraints and indexes.
    """
    results = {"constraints": [], "indexes": [], "fulltext": [], "errors": []}

    # Apply constraints
    for stmt in CONSTRAINTS:
        try:
            manager.write_query(stmt)
            name = stmt.split("CONSTRAINT")[1].split("IF")[0].strip()
            results["constraints"].append(name)
            logger.info("schema_constraint_applied", constraint=name)
        except Exception as e:
            err = str(e)[:100]
            # "already exists" is fine for idempotency
            if "already exists" in err.lower() or "equivalent" in err.lower():
                results["constraints"].append(f"{stmt[:40]}... (already exists)")
            else:
                results["errors"].append(err)
                logger.warning("schema_constraint_error", error=err)

    # Apply standard indexes
    for stmt in INDEXES:
        try:
            manager.write_query(stmt)
            name = stmt.split("INDEX")[1].split("IF")[0].strip()
            results["indexes"].append(name)
            logger.info("schema_index_applied", index=name)
        except Exception as e:
            err = str(e)[:100]
            if "already exists" in err.lower() or "equivalent" in err.lower():
                results["indexes"].append(f"{stmt[:40]}... (already exists)")
            else:
                results["errors"].append(err)

    # Apply full-text indexes
    for stmt in FULLTEXT_INDEXES:
        try:
            manager.write_query(stmt)
            name = stmt.split("INDEX")[1].split("IF")[0].strip()
            results["fulltext"].append(name)
            logger.info("schema_fulltext_applied", index=name)
        except Exception as e:
            err = str(e)[:100]
            if "already exists" in err.lower() or "equivalent" in err.lower():
                results["fulltext"].append("already exists")
            else:
                results["errors"].append(err)

    logger.info(
        "schema_applied",
        constraints=len(results["constraints"]),
        indexes=len(results["indexes"]),
        fulltext=len(results["fulltext"]),
        errors=len(results["errors"]),
    )
    return results


def get_schema_info(manager: "Neo4jManager") -> dict:
    """Get current schema information from Neo4j."""
    try:
        constraints = manager.run_query("SHOW CONSTRAINTS")
        indexes = manager.run_query("SHOW INDEXES")
        return {
            "constraints": [dict(c) for c in constraints],
            "indexes": [dict(i) for i in indexes],
            "node_types": list(NODE_TYPES.keys()),
            "relationship_types": list(RELATIONSHIP_TYPES.keys()),
        }
    except Exception as e:
        return {"error": str(e)[:200]}
