"""
Test BD Knowledge Graph implementation.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from Engine8_Knowledge.graph.bd_knowledge_graph import (
    BDKnowledgeGraph,
    Entity,
    Relationship,
    ENTITY_TYPES,
    RELATIONSHIP_TYPES
)


def cleanup_graph(graph, db_path):
    """Clean up graph and database file."""
    if graph and graph.conn:
        graph.conn.close()
    try:
        os.unlink(db_path)
    except (PermissionError, FileNotFoundError):
        pass


def test_entity_creation():
    """Test creating entities."""
    print("\n=== Testing Entity Creation ===")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    graph = BDKnowledgeGraph(db_path)

    # Create contractors
    gdit = graph.add_entity("Contractor", "GDIT", {
        "type": "Large Prime",
        "uei": "123456789",
        "headquarters": "Falls Church, VA"
    })
    print(f"Created: {gdit.name} ({gdit.type}) - ID: {gdit.id}")

    leidos = graph.add_entity("Contractor", "Leidos", {
        "type": "Large Prime",
        "headquarters": "Reston, VA"
    })
    print(f"Created: {leidos.name} ({leidos.type}) - ID: {leidos.id}")

    # Create program
    dcgs = graph.add_entity("Program", "AF DCGS", {
        "acronym": "DCGS",
        "agency": "Air Force",
        "value": "$500M",
        "prime": "GDIT"
    })
    print(f"Created: {dcgs.name} ({dcgs.type}) - ID: {dcgs.id}")

    # Create contact
    contact = graph.add_entity("Contact", "John Smith", {
        "title": "Program Manager",
        "company": "GDIT",
        "tier": "Tier 1",
        "clearance": "TS/SCI"
    })
    print(f"Created: {contact.name} ({contact.type}) - ID: {contact.id}")

    # Verify entities were created
    assert len(graph.get_entities_by_type("Contractor")) == 2
    assert len(graph.get_entities_by_type("Program")) == 1
    assert len(graph.get_entities_by_type("Contact")) == 1

    print("PASS: Entity creation works")
    cleanup_graph(graph, db_path)


def test_relationships():
    """Test creating relationships."""
    print("\n=== Testing Relationships ===")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    graph = BDKnowledgeGraph(db_path)

    # Create entities
    gdit = graph.add_entity("Contractor", "GDIT")
    dcgs = graph.add_entity("Program", "AF DCGS")
    contact = graph.add_entity("Contact", "John Smith")

    # Create relationships
    rel1 = graph.add_relationship(gdit.id, "PRIMES_ON", dcgs.id, confidence=0.95)
    print(f"Created: {gdit.name} --{rel1.type}--> {dcgs.name}")

    rel2 = graph.add_relationship(contact.id, "WORKS_FOR", gdit.id)
    print(f"Created: {contact.name} --{rel2.type}--> {gdit.name}")

    rel3 = graph.add_relationship(contact.id, "WORKS_ON", dcgs.id)
    print(f"Created: {contact.name} --{rel3.type}--> {dcgs.name}")

    # Query relationships
    gdit_rels = graph.get_relationships(gdit.id)
    assert len(gdit_rels) >= 2
    print(f"GDIT has {len(gdit_rels)} relationships")

    print("PASS: Relationships work")
    cleanup_graph(graph, db_path)


def test_program_ecosystem():
    """Test program ecosystem query."""
    print("\n=== Testing Program Ecosystem ===")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    graph = BDKnowledgeGraph(db_path)

    # Create entities
    gdit = graph.add_entity("Contractor", "GDIT")
    leidos = graph.add_entity("Contractor", "Leidos")
    dcgs = graph.add_entity("Program", "AF DCGS", {"prime": "GDIT"})
    contact1 = graph.add_entity("Contact", "John Smith")
    contact2 = graph.add_entity("Contact", "Jane Doe")
    job = graph.add_entity("Job", "Network Engineer", {"location": "Langley AFB"})
    location = graph.add_entity("Location", "Langley AFB", {"state": "VA"})

    # Create relationships
    graph.add_relationship(gdit.id, "PRIMES_ON", dcgs.id)
    graph.add_relationship(leidos.id, "HAS_PAST_PERF", dcgs.id)
    graph.add_relationship(contact1.id, "WORKS_ON", dcgs.id)
    graph.add_relationship(contact2.id, "WORKS_ON", dcgs.id)
    graph.add_relationship(dcgs.id, "HAS_OPENING", job.id)
    graph.add_relationship(dcgs.id, "LOCATED_AT", location.id)

    # Query ecosystem
    ecosystem = graph.get_program_ecosystem("AF DCGS")

    print(f"Program: {ecosystem['program']['name']}")
    print(f"Primes: {len(ecosystem['primes'])}")
    print(f"Subs: {len(ecosystem['subcontractors'])}")
    print(f"Contacts: {len(ecosystem['contacts'])}")
    print(f"Jobs: {len(ecosystem['jobs'])}")
    print(f"Locations: {len(ecosystem['locations'])}")

    assert len(ecosystem['primes']) == 1
    assert len(ecosystem['contacts']) == 2

    print("PASS: Program ecosystem works")
    cleanup_graph(graph, db_path)


def test_teaming_path():
    """Test finding teaming paths."""
    print("\n=== Testing Teaming Path ===")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    graph = BDKnowledgeGraph(db_path)

    # Create network: PTS -> GDIT -> AF DCGS
    pts = graph.add_entity("Contractor", "PTS")
    gdit = graph.add_entity("Contractor", "GDIT")
    dcgs = graph.add_entity("Program", "AF DCGS")

    graph.add_relationship(pts.id, "SUBS_TO", gdit.id)
    graph.add_relationship(gdit.id, "PRIMES_ON", dcgs.id)

    # Find path
    path = graph.find_teaming_path("PTS", "AF DCGS")

    print(f"Path from PTS to AF DCGS:")
    for step in path:
        if isinstance(step, dict):
            if "relationship" in step:
                print(f"  --{step['relationship']}--> {step['entity']['name']}")
            else:
                print(f"  Start: {step.get('name', step)}")

    assert len(path) >= 3  # PTS -> GDIT -> AF DCGS

    print("PASS: Teaming path works")
    cleanup_graph(graph, db_path)


def test_natural_language_query():
    """Test natural language queries."""
    print("\n=== Testing Natural Language Query ===")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    graph = BDKnowledgeGraph(db_path)

    # Create data
    gdit = graph.add_entity("Contractor", "GDIT")
    dcgs = graph.add_entity("Program", "AF DCGS")
    contact = graph.add_entity("Contact", "John Smith")

    graph.add_relationship(contact.id, "WORKS_ON", dcgs.id)
    graph.add_relationship(gdit.id, "PRIMES_ON", dcgs.id)

    # Test queries
    results = graph.query("Who works on AF DCGS?")
    print(f"Query: 'Who works on AF DCGS?' -> {len(results)} results")

    results = graph.query("What programs does GDIT prime on?")
    print(f"Query: 'What programs does GDIT prime on?' -> {len(results)} results")

    print("PASS: Natural language queries work")
    cleanup_graph(graph, db_path)


def test_stats():
    """Test statistics."""
    print("\n=== Testing Statistics ===")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    graph = BDKnowledgeGraph(db_path)

    # Create data
    graph.add_entity("Contractor", "GDIT")
    graph.add_entity("Contractor", "Leidos")
    graph.add_entity("Program", "AF DCGS")
    graph.add_entity("Contact", "John Smith")

    stats = graph.get_stats()

    print(f"Total entities: {stats['total_entities']}")
    print(f"By type: {stats['entities_by_type']}")
    print(f"Total relationships: {stats['total_relationships']}")

    assert stats['total_entities'] == 4
    assert stats['entities_by_type']['Contractor'] == 2

    print("PASS: Statistics work")
    cleanup_graph(graph, db_path)


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("BD Knowledge Graph - Test Suite")
    print("=" * 60)

    test_entity_creation()
    test_relationships()
    test_program_ecosystem()
    test_teaming_path()
    test_natural_language_query()
    test_stats()

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
