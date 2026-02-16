"""Tests for Phase 39A — Entity Resolution Engine."""

import pytest

from src.knowledge.entity_resolution import (
    EntityResolutionEngine,
    GlobalResolutionReport,
    MatchOutcome,
    PersonResolver,
    OrganizationResolver,
    ProgramResolver,
    levenshtein_distance,
    levenshtein_similarity,
    jaro_similarity,
    jaro_winkler_similarity,
    name_similarity,
    org_name_similarity,
    program_name_similarity,
    get_resolution_engine,
)


# =========================================
# STRING SIMILARITY
# =========================================


def test_levenshtein_distance_identical():
    assert levenshtein_distance("hello", "hello") == 0


def test_levenshtein_distance_different():
    assert levenshtein_distance("kitten", "sitting") == 3


def test_levenshtein_distance_empty():
    assert levenshtein_distance("", "hello") == 5
    assert levenshtein_distance("hello", "") == 5


def test_levenshtein_similarity_identical():
    assert levenshtein_similarity("test", "test") == 1.0


def test_levenshtein_similarity_different():
    sim = levenshtein_similarity("John", "Jane")
    assert 0 < sim < 1


def test_levenshtein_similarity_empty():
    assert levenshtein_similarity("", "") == 1.0


def test_jaro_similarity_identical():
    sim = jaro_similarity("hello", "hello")
    assert sim == 1.0


def test_jaro_similarity_different():
    sim = jaro_similarity("MARTHA", "MARHTA")
    assert sim > 0.9


def test_jaro_similarity_empty():
    assert jaro_similarity("", "") == 1.0
    assert jaro_similarity("a", "") == 0.0


def test_jaro_winkler_identical():
    sim = jaro_winkler_similarity("hello", "hello")
    assert sim == 1.0


def test_jaro_winkler_prefix_boost():
    jaro = jaro_similarity("MARTHA", "MARHTA")
    jw = jaro_winkler_similarity("MARTHA", "MARHTA")
    assert jw >= jaro  # JW should boost shared prefix


def test_name_similarity_identical():
    sim = name_similarity("John Smith", "John Smith")
    assert sim == 1.0


def test_name_similarity_nicknames():
    sim = name_similarity("Robert Smith", "Bob Smith")
    assert sim > 0.6


def test_name_similarity_initials():
    sim = name_similarity("J. Smith", "John Smith")
    assert sim > 0.4


def test_name_similarity_completely_different():
    sim = name_similarity("John Smith", "Alice Williams")
    assert sim < 0.5


# =========================================
# ORG & PROGRAM SIMILARITY
# =========================================


def test_org_similarity_alias():
    sim = org_name_similarity("GDIT", "General Dynamics IT")
    assert sim >= 0.9


def test_org_similarity_same():
    sim = org_name_similarity("Leidos", "Leidos")
    assert sim == 1.0


def test_org_similarity_different():
    sim = org_name_similarity("Leidos", "SAIC")
    assert sim < 0.5


def test_program_similarity_alias():
    sim = program_name_similarity("DCGS", "DCGS-A")
    assert sim >= 0.9


def test_program_similarity_same():
    sim = program_name_similarity("GBSD", "GBSD")
    assert sim == 1.0


# =========================================
# PERSON RESOLVER
# =========================================


@pytest.fixture
def resolver():
    return PersonResolver()


def test_person_resolve_same_person(resolver):
    a = {"id": "a", "name": "John Smith", "type": "person", "email": "jsmith@gdit.com"}
    b = {"id": "b", "name": "John Smith", "type": "person", "email": "jsmith@gdit.com"}
    result = resolver.resolve(a, b)
    assert result.outcome == MatchOutcome.DEFINITE_MATCH.value
    assert result.confidence >= 0.95


def test_person_resolve_similar_names(resolver):
    a = {"id": "a", "name": "John Smith", "type": "person"}
    b = {"id": "b", "name": "Jon Smith", "type": "person"}
    result = resolver.resolve(a, b)
    # Name-only match gives low overall confidence due to weighting (name=0.4)
    assert result.confidence > 0.2
    assert result.signals["name"] > 0.6


def test_person_resolve_different_people(resolver):
    a = {"id": "a", "name": "John Smith", "type": "person"}
    b = {"id": "b", "name": "Alice Williams", "type": "person"}
    result = resolver.resolve(a, b)
    assert result.outcome == MatchOutcome.NO_MATCH.value


def test_person_resolve_email_definitive(resolver):
    a = {
        "id": "a",
        "name": "J. Smith",
        "type": "person",
        "email": "john.smith@leidos.com",
    }
    b = {
        "id": "b",
        "name": "John Smith",
        "type": "person",
        "email": "john.smith@leidos.com",
    }
    result = resolver.resolve(a, b)
    assert result.confidence >= 0.95


def test_person_resolve_company_title(resolver):
    a = {
        "id": "a",
        "name": "John Smith",
        "type": "person",
        "company": "GDIT",
        "title": "Analyst",
    }
    b = {
        "id": "b",
        "name": "John Smith",
        "type": "person",
        "company": "GDIT",
        "title": "Sr Analyst",
    }
    result = resolver.resolve(a, b)
    # name(1.0)*0.4 + company_title(~0.95)*0.25 ≈ 0.64
    assert result.confidence > 0.6
    assert result.signals["company_title"] > 0.9


def test_person_find_candidates(resolver):
    entity = {
        "id": "a",
        "name": "John Smith",
        "type": "person",
        "email": "jsmith@gdit.com",
    }
    pool = [
        {"id": "b", "name": "Jon Smith", "type": "person"},
        {"id": "c", "name": "John Smith", "type": "person", "email": "jsmith@gdit.com"},
        {"id": "d", "name": "Alice Williams", "type": "person"},
    ]
    candidates = resolver.find_candidates(entity, pool, limit=5)
    assert len(candidates) >= 1
    # Best match should be the exact name + email match
    assert candidates[0].entity_name == "John Smith"


# =========================================
# ORGANIZATION RESOLVER
# =========================================


def test_org_resolver():
    resolver = OrganizationResolver()
    result = resolver.resolve("GDIT", "General Dynamics IT")
    assert result.confidence >= 0.9


# =========================================
# PROGRAM RESOLVER
# =========================================


def test_program_resolver():
    resolver = ProgramResolver()
    result = resolver.resolve("DCGS", "DCGS-A")
    assert result.confidence >= 0.9


# =========================================
# ENGINE
# =========================================


@pytest.fixture
def engine():
    return EntityResolutionEngine()


def test_engine_resolve_person(engine):
    a = {"id": "a", "name": "John Smith", "type": "person", "email": "js@test.com"}
    b = {"id": "b", "name": "John Smith", "type": "person", "email": "js@test.com"}
    result = engine.resolve(a, b)
    assert result.confidence >= 0.95


def test_engine_resolve_org(engine):
    a = {"id": "a", "name": "GDIT", "type": "organization"}
    b = {"id": "b", "name": "General Dynamics IT", "type": "organization"}
    result = engine.resolve(a, b)
    assert result.confidence >= 0.9


def test_engine_resolve_program(engine):
    a = {"id": "a", "name": "DCGS", "type": "program"}
    b = {"id": "b", "name": "DCGS-A", "type": "program"}
    result = engine.resolve(a, b)
    assert result.confidence >= 0.9


def test_engine_find_candidates(engine):
    entity = {"id": "a", "name": "John Smith", "type": "person"}
    pool = [
        {"id": "b", "name": "Jon Smith", "type": "person"},
        {"id": "c", "name": "Jane Doe", "type": "person"},
    ]
    candidates = engine.find_candidates(entity, pool)
    assert isinstance(candidates, list)


def test_engine_merge_entities(engine):
    primary = {"id": "p1", "name": "John Smith", "email": "jsmith@test.com"}
    duplicate = {"id": "d1", "name": "Jon Smith", "phone": "555-0123"}
    result = engine.merge_entities(primary, duplicate)
    assert result.success is True
    assert "phone" in result.fields_merged
    assert "Jon Smith" in result.aliases_added


def test_engine_merge_keeps_primary_values(engine):
    primary = {
        "id": "p1",
        "name": "John Smith",
        "email": "jsmith@test.com",
        "company": "GDIT",
    }
    duplicate = {
        "id": "d1",
        "name": "Jon Smith",
        "email": "old@test.com",
        "company": "Old Corp",
    }
    engine.merge_entities(primary, duplicate)
    # Primary's values should be preserved
    assert primary["email"] == "jsmith@test.com"
    assert primary["company"] == "GDIT"


def test_engine_merge_log(engine):
    primary = {"id": "p1", "name": "John"}
    duplicate = {"id": "d1", "name": "Jon"}
    engine.merge_entities(primary, duplicate)
    log = engine.get_merge_log()
    assert len(log) == 1
    assert log[0].primary_id == "p1"


# =========================================
# GLOBAL RESOLUTION
# =========================================


def test_global_resolution_basic(engine):
    entities = [
        {"id": "1", "name": "John Smith", "type": "person"},
        {"id": "2", "name": "Jon Smith", "type": "person"},
        {"id": "3", "name": "Alice Williams", "type": "person"},
    ]
    report = engine.run_global_resolution(entities)
    assert isinstance(report, GlobalResolutionReport)
    assert report.total_entities_scanned == 3
    assert report.pairs_compared >= 1


def test_global_resolution_empty(engine):
    report = engine.run_global_resolution([])
    assert report.total_entities_scanned == 0
    assert report.pairs_compared == 0


def test_global_resolution_finds_duplicates(engine):
    entities = [
        {"id": "1", "name": "John Smith", "type": "person", "email": "jsmith@test.com"},
        {"id": "2", "name": "John Smith", "type": "person", "email": "jsmith@test.com"},
    ]
    report = engine.run_global_resolution(entities)
    assert report.definite_matches >= 1


# =========================================
# SINGLETON
# =========================================


def test_get_resolution_engine_singleton():
    e1 = get_resolution_engine()
    e2 = get_resolution_engine()
    assert e1 is e2
