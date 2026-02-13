"""Tests for Phase 47A — Synthetic Training Data Generator."""

import pytest

from src.embeddings.synthetic_data_generator import (
    SyntheticDataGenerator,
    GenerationJob,
    get_synthetic_generator,
)


@pytest.fixture
def gen():
    return SyntheticDataGenerator()


# =========================================
# FULL GENERATION
# =========================================

def test_generate_all_strategies(gen):
    job = gen.generate()
    assert isinstance(job, GenerationJob)
    assert job.total_triplets > 0
    assert job.status == "completed"


def test_generate_returns_all_strategies(gen):
    job = gen.generate()
    assert len(job.triplets_by_strategy) == 7  # all 7 strategies


def test_generate_records_sources(gen):
    job = gen.generate()
    assert len(job.triplets_by_source) >= 1


def test_generate_records_difficulty(gen):
    job = gen.generate()
    assert len(job.triplets_by_difficulty) >= 1


def test_generate_measures_duration(gen):
    job = gen.generate()
    assert job.duration_sec >= 0


def test_generate_single_strategy(gen):
    job = gen.generate(strategies=["acronym"])
    assert "acronym" in job.triplets_by_strategy
    assert job.total_triplets > 0


def test_generate_multiple_strategies(gen):
    job = gen.generate(strategies=["acronym", "entity_centric"])
    assert len(job.triplets_by_strategy) == 2


def test_generate_max_per_strategy(gen):
    job = gen.generate(strategies=["entity_centric"], max_per_strategy=3)
    assert job.triplets_by_strategy.get("entity_centric", 0) <= 10  # 2 triplets per program * up to 3


# =========================================
# ENTITY-CENTRIC
# =========================================

def test_entity_centric_programs(gen):
    job = gen.generate(strategies=["entity_centric"])
    triplets = gen.get_triplets(strategy="entity_centric")
    assert len(triplets) >= 2
    # Should ask about program acronyms and full names
    queries = [t.query for t in triplets]
    assert any("DCGS-A" in q for q in queries)


def test_entity_centric_positive_negative(gen):
    job = gen.generate(strategies=["entity_centric"])
    triplets = gen.get_triplets(strategy="entity_centric")
    for t in triplets:
        assert t.positive != ""
        assert t.negative != ""
        assert t.positive != t.negative


# =========================================
# ROLE-CENTRIC
# =========================================

def test_role_centric_contacts(gen):
    job = gen.generate(strategies=["role_centric"])
    triplets = gen.get_triplets(strategy="role_centric")
    assert len(triplets) >= 2
    queries = [t.query for t in triplets]
    assert any("Craig Lindahl" in q or "Program Manager" in q for q in queries)


# =========================================
# PAIN POINT
# =========================================

def test_pain_point_queries(gen):
    job = gen.generate(strategies=["pain_point"])
    triplets = gen.get_triplets(strategy="pain_point")
    assert len(triplets) >= 1
    assert any("struggling" in t.positive.lower() or "challenge" in t.positive.lower()
               for t in triplets)


# =========================================
# RELATIONSHIP
# =========================================

def test_relationship_queries(gen):
    job = gen.generate(strategies=["relationship"])
    triplets = gen.get_triplets(strategy="relationship")
    assert len(triplets) >= 2
    queries = [t.query.lower() for t in triplets]
    assert any("prime" in q or "works on" in q for q in queries)


# =========================================
# JOB MAPPING
# =========================================

def test_job_mapping_queries(gen):
    job = gen.generate(strategies=["job_mapping"])
    triplets = gen.get_triplets(strategy="job_mapping")
    assert len(triplets) >= 2
    assert any("Kubernetes" in t.query or "Cloud" in t.query or "Autonomy" in t.query
               for t in triplets)


# =========================================
# ACRONYM
# =========================================

def test_acronym_queries(gen):
    job = gen.generate(strategies=["acronym"])
    triplets = gen.get_triplets(strategy="acronym")
    assert len(triplets) >= 2
    # Should have both "What does X stand for?" and reverse
    queries = [t.query for t in triplets]
    assert any("stand for" in q for q in queries)
    assert any("abbreviation" in q for q in queries)


def test_acronym_positive_contains_expansion(gen):
    job = gen.generate(strategies=["acronym"])
    triplets = gen.get_triplets(strategy="acronym")
    for t in triplets:
        if "stand for" in t.query:
            assert "stands for" in t.positive


# =========================================
# TEMPORAL
# =========================================

def test_temporal_queries(gen):
    job = gen.generate(strategies=["temporal"])
    triplets = gen.get_triplets(strategy="temporal")
    assert len(triplets) >= 1
    assert any("recompete" in t.positive.lower() or "fy26" in t.positive.lower()
               or "2026" in t.positive for t in triplets)


# =========================================
# COLLECTION-SPECIFIC
# =========================================

def test_from_notes(gen):
    triplets = gen.generate_from_notes()
    assert len(triplets) >= 1
    assert all(t.source_collection == "notes" for t in triplets)


def test_from_programs(gen):
    triplets = gen.generate_from_programs()
    assert len(triplets) >= 1
    assert all(t.source_collection == "programs" for t in triplets)


def test_from_acronyms(gen):
    triplets = gen.generate_from_acronyms()
    assert len(triplets) >= 2
    assert all(t.source_collection == "acronyms" for t in triplets)


def test_from_jobs(gen):
    triplets = gen.generate_from_jobs()
    assert len(triplets) >= 1
    assert all(t.source_collection == "jobs" for t in triplets)


def test_from_contacts(gen):
    triplets = gen.generate_from_contacts()
    assert len(triplets) >= 1
    assert all(t.source_collection == "contacts" for t in triplets)


# =========================================
# HARD NEGATIVE MINING
# =========================================

def test_hard_negative_mining(gen):
    base_triplets = gen.generate_from_programs(max_count=5)
    upgraded = gen.mine_hard_negatives(base_triplets)
    assert len(upgraded) == len(base_triplets)
    hard_count = sum(1 for t in upgraded if t.difficulty == "hard")
    assert hard_count >= 1  # at least some should be upgraded


# =========================================
# FILTERING & STATS
# =========================================

def test_filter_by_strategy(gen):
    gen.generate()
    acronym_trips = gen.get_triplets(strategy="acronym")
    entity_trips = gen.get_triplets(strategy="entity_centric")
    assert len(acronym_trips) > 0
    assert len(entity_trips) > 0
    assert all(t.strategy == "acronym" for t in acronym_trips)


def test_filter_by_source(gen):
    gen.generate()
    program_trips = gen.get_triplets(source="programs")
    assert all(t.source_collection == "programs" for t in program_trips)


def test_filter_by_difficulty(gen):
    gen.generate()
    hard_trips = gen.get_triplets(difficulty="hard")
    assert all(t.difficulty == "hard" for t in hard_trips)


def test_stats(gen):
    gen.generate()
    stats = gen.get_stats()
    assert stats["total_triplets"] > 0
    assert stats["programs_available"] >= 1
    assert stats["contacts_available"] >= 1
    assert stats["acronyms_available"] >= 1


def test_generation_history(gen):
    gen.generate(strategies=["acronym"])
    gen.generate(strategies=["entity_centric"])
    history = gen.get_generation_history()
    assert len(history) == 2


# =========================================
# TRIPLET STRUCTURE
# =========================================

def test_triplet_has_id(gen):
    gen.generate(strategies=["acronym"])
    triplets = gen.get_triplets()
    for t in triplets:
        assert t.id.startswith("trip_")


def test_triplet_query_positive_different(gen):
    gen.generate()
    for t in gen.get_triplets():
        assert t.query != t.positive
        assert t.query != t.negative


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    g1 = get_synthetic_generator()
    g2 = get_synthetic_generator()
    assert g1 is g2
