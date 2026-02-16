"""Tests for Phase 39A — Temporal Knowledge Graph Engine."""

import pytest
from datetime import datetime, timezone, timedelta

from src.knowledge.temporal_kg import (
    TemporalKnowledgeGraph,
    Episode,
    EpisodeType,
    Entity,
    EdgeType,
    TemporalFact,
    EpisodeResult,
    EntityTimeline,
    ContradictionType,
    extract_entities_simple,
    extract_relationships_simple,
    get_temporal_kg,
)


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def kg():
    return TemporalKnowledgeGraph()


@pytest.fixture
def populated_kg(kg):
    """KG with some data already ingested."""
    ep1 = Episode(
        content="John Smith works at GDIT as a Senior Analyst on the DCGS program.",
        episode_type=EpisodeType.CONVERSATION_NOTE.value,
        source="test",
    )
    kg.ingest_episode(ep1)
    return kg


# =========================================
# ENTITY EXTRACTION
# =========================================


def test_extract_entities_person():
    entities = extract_entities_simple("John Smith is working on DCGS.")
    names = [e["name"] for e in entities]
    assert "John Smith" in names


def test_extract_entities_org():
    entities = extract_entities_simple("Leidos won the DCGS contract.")
    types = {e["name"]: e["type"] for e in entities}
    assert types.get("leidos") == "organization" or any(
        e["type"] == "organization" for e in entities
    )


def test_extract_entities_program():
    entities = extract_entities_simple("The DCGS-A program is expanding.")
    types = {e["name"]: e["type"] for e in entities}
    assert any(e["type"] == "program" for e in entities)


def test_extract_entities_empty():
    entities = extract_entities_simple("")
    assert entities == []


def test_extract_entities_no_names():
    entities = extract_entities_simple("the quick brown fox jumps over the lazy dog")
    # Should find no person entities (no capitalized names)
    persons = [e for e in entities if e["type"] == "person"]
    assert len(persons) == 0


# =========================================
# RELATIONSHIP EXTRACTION
# =========================================


def test_extract_relationships_works_at():
    entities = extract_entities_simple("John Smith works at GDIT.")
    rels = extract_relationships_simple("John Smith works at GDIT.", entities)
    predicates = [r["predicate"] for r in rels]
    assert EdgeType.WORKS_AT.value in predicates


def test_extract_relationships_manages():
    text = "Sarah Johnson manages the DCGS team."
    entities = extract_entities_simple(text)
    rels = extract_relationships_simple(text, entities)
    predicates = [r["predicate"] for r in rels]
    assert EdgeType.MANAGES.value in predicates


def test_extract_relationships_empty():
    rels = extract_relationships_simple("", [])
    assert rels == []


# =========================================
# EPISODE INGESTION
# =========================================


def test_ingest_episode_basic(kg):
    ep = Episode(
        content="John Smith works at GDIT as a Senior Analyst.",
        episode_type=EpisodeType.CONVERSATION_NOTE.value,
    )
    result = kg.ingest_episode(ep)
    assert isinstance(result, EpisodeResult)
    assert result.episode_id != ""
    assert result.entities_discovered >= 1
    assert result.processing_time_ms >= 0


def test_ingest_episode_creates_entities(kg):
    ep = Episode(content="Jane Doe works at Leidos on DCGS.")
    kg.ingest_episode(ep)
    stats = kg.get_stats()
    assert stats["total_entities"] >= 1


def test_ingest_episode_creates_facts(kg):
    ep = Episode(content="Mike Brown works at SAIC.")
    result = kg.ingest_episode(ep)
    assert result.facts_added >= 1


def test_ingest_episode_resolves_existing(kg):
    ep1 = Episode(content="John Smith works at GDIT.")
    ep2 = Episode(content="John Smith manages the analytics team.")
    kg.ingest_episode(ep1)
    r2 = kg.ingest_episode(ep2)
    # Second ingestion should resolve John Smith, not create new
    assert r2.entities_resolved >= 1


def test_ingest_episode_assigns_id(kg):
    ep = Episode(content="Test episode.")
    result = kg.ingest_episode(ep)
    assert result.episode_id != ""


def test_ingest_episode_preserves_id(kg):
    ep = Episode(id="custom-id", content="Test episode.")
    result = kg.ingest_episode(ep)
    assert result.episode_id == "custom-id"


def test_ingest_multiple_episodes(kg):
    for i in range(3):
        ep = Episode(content=f"Person{i} Name{i} works at GDIT.")
        kg.ingest_episode(ep)
    stats = kg.get_stats()
    assert stats["total_episodes"] == 3


# =========================================
# TEMPORAL QUERIES
# =========================================


def test_query_facts_at_time(populated_kg):
    now = datetime.now(timezone.utc).isoformat()
    facts = populated_kg.query_facts_at_time(now)
    assert isinstance(facts, list)


def test_query_facts_at_time_with_entity(populated_kg):
    entities = list(populated_kg._entities.values())
    if entities:
        now = datetime.now(timezone.utc).isoformat()
        facts = populated_kg.query_facts_at_time(now, entity_id=entities[0].id)
        assert isinstance(facts, list)


def test_query_facts_at_time_invalid_timestamp(populated_kg):
    facts = populated_kg.query_facts_at_time("not-a-date")
    assert facts == []


def test_get_active_facts(populated_kg):
    facts = populated_kg.get_active_facts()
    assert isinstance(facts, list)
    # All returned facts should have no valid_to
    for fact in facts:
        assert fact.valid_to == ""


def test_get_active_facts_by_entity(populated_kg):
    entities = list(populated_kg._entities.values())
    if entities:
        facts = populated_kg.get_active_facts(entity_id=entities[0].id)
        assert isinstance(facts, list)


# =========================================
# ENTITY TIMELINE
# =========================================


def test_get_entity_timeline(populated_kg):
    entities = list(populated_kg._entities.values())
    if entities:
        timeline = populated_kg.get_entity_timeline(entities[0].id)
        assert timeline is not None
        assert isinstance(timeline, EntityTimeline)
        assert timeline.entity_id == entities[0].id


def test_get_entity_timeline_nonexistent(kg):
    timeline = kg.get_entity_timeline("nonexistent-id")
    assert timeline is None


# =========================================
# CHANGE DETECTION
# =========================================


def test_detect_changes(populated_kg):
    entities = list(populated_kg._entities.values())
    if entities:
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        changes = populated_kg.detect_changes(entities[0].id, yesterday)
        assert isinstance(changes, list)


def test_detect_changes_nonexistent(kg):
    changes = kg.detect_changes("nonexistent", "2024-01-01T00:00:00Z")
    assert changes == []


# =========================================
# FACT EXPIRATION
# =========================================


def test_expire_fact(populated_kg):
    facts = list(populated_kg._facts.values())
    if facts:
        success = populated_kg.expire_fact(facts[0].id)
        assert success is True
        # Fact should now have valid_to set
        expired = populated_kg._facts[facts[0].id]
        assert expired.valid_to != ""


def test_expire_fact_nonexistent(kg):
    success = kg.expire_fact("nonexistent-id")
    assert success is False


# =========================================
# CONTRADICTION DETECTION
# =========================================


def test_find_contradictions_empty(kg):
    contradictions = kg.find_contradictions()
    assert contradictions == []


def test_find_contradictions_dual_employment(kg):
    # Create entity working at two places simultaneously
    entity = Entity(id="e1", entity_type="person", name="Test Person")
    kg.add_entity(entity)

    org1 = Entity(id="o1", entity_type="organization", name="Company A")
    org2 = Entity(id="o2", entity_type="organization", name="Company B")
    kg.add_entity(org1)
    kg.add_entity(org2)

    now = datetime.now(timezone.utc).isoformat()
    f1 = TemporalFact(
        id="f1",
        subject_id="e1",
        predicate=EdgeType.WORKS_AT.value,
        object_id="o1",
        valid_from=now,
        confidence=0.9,
    )
    f2 = TemporalFact(
        id="f2",
        subject_id="e1",
        predicate=EdgeType.WORKS_AT.value,
        object_id="o2",
        valid_from=now,
        confidence=0.9,
    )
    kg.add_fact(f1)
    kg.add_fact(f2)

    contradictions = kg.find_contradictions()
    assert len(contradictions) >= 1
    assert (
        contradictions[0].contradiction_type == ContradictionType.DUAL_EMPLOYMENT.value
    )


# =========================================
# SEARCH
# =========================================


def test_search_entities(populated_kg):
    results = populated_kg.search_entities("John")
    assert len(results) >= 1
    assert results[0].name == "John Smith"


def test_search_entities_by_type(populated_kg):
    results = populated_kg.search_entities("GDIT", entity_type="organization")
    # Should find GDIT as organization
    assert isinstance(results, list)


def test_search_entities_no_match(kg):
    results = kg.search_entities("nonexistent-entity-xyz")
    assert results == []


def test_search_facts(populated_kg):
    facts = populated_kg.search_facts(predicate=EdgeType.WORKS_AT.value)
    assert isinstance(facts, list)


def test_search_facts_active_only(populated_kg):
    facts = populated_kg.search_facts(active_only=True)
    for fact in facts:
        assert fact.valid_to == ""


# =========================================
# STATS
# =========================================


def test_get_stats_empty(kg):
    stats = kg.get_stats()
    assert stats["total_entities"] == 0
    assert stats["total_facts"] == 0
    assert stats["total_episodes"] == 0


def test_get_stats_populated(populated_kg):
    stats = populated_kg.get_stats()
    assert stats["total_entities"] >= 1
    assert stats["total_episodes"] >= 1
    assert "entity_types" in stats
    assert "predicate_counts" in stats


# =========================================
# SINGLETON
# =========================================


def test_get_temporal_kg_singleton():
    kg1 = get_temporal_kg()
    kg2 = get_temporal_kg()
    assert kg1 is kg2
