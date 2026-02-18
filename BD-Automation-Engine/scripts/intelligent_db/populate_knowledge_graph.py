"""
Populate knowledge graph from unified database.
Creates entities (Companies, Programs, Contacts) and relationships (WORKS_ON, PRIMES_ON, etc.)
Reuses BDKnowledgeGraph from Engine8_Knowledge/graph/bd_knowledge_graph.py.
"""
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.master_db.utils import normalize_company_name, generate_id

DB_PATH = PROJECT_ROOT / "data" / "unified_federal_contracts.db"
GRAPH_DB_PATH = PROJECT_ROOT / "Engine8_Knowledge" / "data" / "bd_graph.db"


def run(db_path=None, graph_path=None):
    """Run knowledge graph population."""
    db_path = db_path or DB_PATH
    graph_path = graph_path or GRAPH_DB_PATH

    print("Knowledge Graph Population")
    print(f"  Source DB: {db_path}")
    print(f"  Graph DB: {graph_path}")

    try:
        from Engine8_Knowledge.graph.bd_knowledge_graph import BDKnowledgeGraph
    except ImportError:
        print("  ERROR: Could not import BDKnowledgeGraph.")
        return

    graph = BDKnowledgeGraph(db_path=str(graph_path))
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    entities = 0
    relationships = 0

    # 1. Companies -> Contractor entities
    print("  Ingesting companies...")
    cursor.execute("""
        SELECT id, name, normalized_name, company_type, cage_code, uei,
               employee_count, headquarters, key_capabilities
        FROM companies WHERE name IS NOT NULL
    """)
    for row in cursor.fetchall():
        r = dict(row)
        graph.add_entity(
            "Contractor", r["normalized_name"] or r["name"],
            properties={
                "type": r.get("company_type"), "uei": r.get("uei"),
                "cage_code": r.get("cage_code"), "size": r.get("employee_count"),
                "headquarters": r.get("headquarters"),
                "capabilities": r.get("key_capabilities"),
            },
            entity_id=r["id"],
        )
        entities += 1

    # 2. Programs -> Program entities
    print("  Ingesting programs...")
    cursor.execute("""
        SELECT id, program_name, acronym, agency_owner, prime_contractor,
               total_contract_value, clearance_requirements, priority_level, domain_tags
        FROM programs WHERE program_name IS NOT NULL
    """)
    for row in cursor.fetchall():
        r = dict(row)
        graph.add_entity(
            "Program", r["program_name"],
            properties={
                "acronym": r.get("acronym"), "agency": r.get("agency_owner"),
                "prime": r.get("prime_contractor"), "value": r.get("total_contract_value"),
                "clearance": r.get("clearance_requirements"),
                "status": r.get("priority_level"),
                "domain_tags": r.get("domain_tags"),
            },
            entity_id=r["id"],
        )
        entities += 1

    # 3. Contacts -> Contact entities
    print("  Ingesting contacts...")
    cursor.execute("""
        SELECT id, full_name, title, company, tier, bd_priority, email, clearances
        FROM contacts WHERE full_name IS NOT NULL
    """)
    for row in cursor.fetchall():
        r = dict(row)
        graph.add_entity(
            "Contact", r["full_name"],
            properties={
                "title": r.get("title"), "company": r.get("company"),
                "tier": r.get("tier"), "priority": r.get("bd_priority"),
                "email": r.get("email"), "clearance": r.get("clearances"),
            },
            entity_id=r["id"],
        )
        entities += 1

    # 4. Jobs -> Job entities
    print("  Ingesting jobs...")
    cursor.execute("""
        SELECT id, title, company, location, clearance, matched_program
        FROM jobs WHERE title IS NOT NULL
    """)
    for row in cursor.fetchall():
        r = dict(row)
        graph.add_entity(
            "Job", r["title"],
            properties={
                "location": r.get("location"), "clearance": r.get("clearance"),
                "program": r.get("matched_program"), "company": r.get("company"),
            },
            entity_id=r["id"],
        )
        entities += 1

    print(f"  Entities created: {entities}")

    # 5. Relationships from program_contacts (WORKS_ON)
    print("  Creating WORKS_ON relationships...")
    cursor.execute("SELECT program_id, contact_id, relationship_type FROM program_contacts")
    for row in cursor.fetchall():
        try:
            graph.add_relationship(
                row[1], "WORKS_ON", row[0],
                properties={"relationship_type": row[2]},
                source="unified_db",
            )
            relationships += 1
        except (ValueError, Exception):
            pass

    # 6. Relationships from program_companies (PRIMES_ON / SUBS_TO)
    print("  Creating PRIMES_ON/SUBS_TO relationships...")
    cursor.execute("SELECT program_id, company_id, role FROM program_companies")
    for row in cursor.fetchall():
        try:
            rel_type = "PRIMES_ON" if row[2] == "prime" else "SUBS_TO"
            if rel_type == "SUBS_TO":
                # Company subs to program's prime - need to find the prime company
                graph.add_relationship(
                    row[1], "PRIMES_ON", row[0],
                    properties={"role": row[2]},
                    source="unified_db",
                )
            else:
                graph.add_relationship(
                    row[1], "PRIMES_ON", row[0],
                    properties={"role": "prime"},
                    source="unified_db",
                )
            relationships += 1
        except (ValueError, Exception):
            pass

    # 7. WORKS_FOR relationships (contact -> company)
    print("  Creating WORKS_FOR relationships...")
    cursor.execute("""
        SELECT c.id AS contact_id, co.id AS company_id
        FROM contacts c
        JOIN companies co ON co.normalized_name = c.company OR co.name = c.company
        WHERE c.company IS NOT NULL
    """)
    for row in cursor.fetchall():
        try:
            graph.add_relationship(
                row[0], "WORKS_FOR", row[1],
                source="unified_db",
            )
            relationships += 1
        except (ValueError, Exception):
            pass

    # 8. HAS_OPENING relationships (program -> job)
    print("  Creating HAS_OPENING relationships...")
    cursor.execute("""
        SELECT matched_program_id, id FROM jobs
        WHERE matched_program_id IS NOT NULL
    """)
    for row in cursor.fetchall():
        try:
            graph.add_relationship(
                row[0], "HAS_OPENING", row[1],
                source="unified_db",
            )
            relationships += 1
        except (ValueError, Exception):
            pass

    # 9. Infer COMPETES_WITH from co-bidding patterns
    print("  Inferring COMPETES_WITH relationships...")
    cursor.execute("""
        SELECT program_id, company_id FROM program_companies
    """)
    program_companies = defaultdict(set)
    for row in cursor.fetchall():
        program_companies[row[0]].add(row[1])

    compete_pairs = set()
    for prog_id, company_ids in program_companies.items():
        companies = list(company_ids)
        for i in range(len(companies)):
            for j in range(i + 1, len(companies)):
                pair = tuple(sorted([companies[i], companies[j]]))
                compete_pairs.add(pair)

    for c1, c2 in compete_pairs:
        try:
            graph.add_relationship(
                c1, "COMPETES_WITH", c2,
                confidence=0.7,
                source="co_bidding_inference",
            )
            relationships += 1
        except (ValueError, Exception):
            pass

    conn.close()

    print(f"  Relationships created: {relationships}")
    print(f"  Total: {entities} entities + {relationships} relationships")


if __name__ == "__main__":
    run()
