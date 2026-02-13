"""Tests for Phase 42A — Memory Cortex."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone

from src.memory.cortex import (
    MemoryCortex,
    Memory,
    MemoryResult,
    ContextMemory,
    AgentContext,
    ConsolidationReport,
    ForgetReport,
    get_memory_cortex,
    _extract_entities,
    _compute_importance,
    _token_overlap,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def cortex():
    return MemoryCortex()


@pytest_asyncio.fixture
async def populated_cortex():
    c = MemoryCortex()
    # Store episodic memories
    await c.store(Memory(
        content="Called Kingsley Ero at PACAF San Diego. He mentioned being stretched thin on staffing.",
        memory_type="episodic",
        importance=0.7,
        source="call_log",
    ))
    await c.store(Memory(
        content="Emailed John Smith at Leidos about DCGS contract opportunity. No response yet.",
        memory_type="episodic",
        importance=0.5,
        source="outreach_tracker",
    ))
    await c.store(Memory(
        content="LinkedIn outreach to Sarah Jones at GDIT about DCGS. She responded positively.",
        memory_type="episodic",
        importance=0.7,
        source="outreach_tracker",
    ))
    # Store semantic memories
    await c.store(Memory(
        content="Kingsley Ero is the Acting Site Lead at PACAF San Diego",
        memory_type="semantic",
        importance=0.8,
        entities=["Kingsley Ero", "PACAF"],
        confidence=0.9,
    ))
    await c.store(Memory(
        content="DCGS-A contract worth $450M awarded to Raytheon",
        memory_type="semantic",
        importance=0.9,
        programs=["DCGS"],
        confidence=0.85,
    ))
    # Store procedural memories
    await c.store(Memory(
        content="LinkedIn outreach to Tier 4 managers has 3x response rate vs email",
        memory_type="procedural",
        importance=0.85,
        tags=["insight", "outreach"],
    ))
    return c


# =========================================
# ENTITY EXTRACTION
# =========================================

def test_extract_programs():
    entities = _extract_entities("Research the DCGS and GBSD programs")
    assert "DCGS" in entities["programs"]
    assert "GBSD" in entities["programs"]


def test_extract_organizations():
    entities = _extract_entities("Find contacts at Leidos and GDIT")
    assert "Leidos" in entities["organizations"]
    assert "GDIT" in entities["organizations"]


def test_extract_locations():
    entities = _extract_entities("Jobs in Norfolk and Langley area")
    assert "Norfolk" in entities["locations"]
    assert "Langley" in entities["locations"]


def test_extract_people():
    entities = _extract_entities("Kingsley Ero is the site lead")
    assert "Kingsley Ero" in entities["people"]


def test_extract_empty():
    entities = _extract_entities("hello world")
    assert all(len(v) == 0 for v in entities.values())


# =========================================
# IMPORTANCE SCORING
# =========================================

def test_importance_procedural_boost():
    score = _compute_importance("Strategy insight about outreach", "procedural", {})
    assert score > 0.4


def test_importance_human_verified():
    score = _compute_importance("Some fact", "semantic", {"human_verified": True})
    assert score >= 0.9


def test_importance_explicit():
    score = _compute_importance("Something", "episodic", {"importance": 0.95})
    assert score == 0.95


# =========================================
# SIMILARITY
# =========================================

def test_token_overlap_identical():
    assert _token_overlap("hello world", "hello world") == 1.0


def test_token_overlap_none():
    assert _token_overlap("hello world", "foo bar") == 0.0


def test_token_overlap_partial():
    score = _token_overlap("find contacts at DCGS", "contacts DCGS program")
    assert 0 < score < 1


def test_token_overlap_empty():
    assert _token_overlap("", "hello") == 0.0


# =========================================
# STORE
# =========================================

@pytest.mark.asyncio
async def test_store_episodic(cortex):
    mem_id = await cortex.store(Memory(
        content="Called John Smith about DCGS",
        memory_type="episodic",
    ))
    assert mem_id != ""
    stats = cortex.get_stats()
    assert stats["episodic"]["count"] == 1


@pytest.mark.asyncio
async def test_store_semantic(cortex):
    mem_id = await cortex.store(Memory(
        content="John Smith is the PM for DCGS-A",
        memory_type="semantic",
        confidence=0.9,
    ))
    assert mem_id != ""
    assert cortex.get_stats()["semantic"]["count"] == 1


@pytest.mark.asyncio
async def test_store_procedural(cortex):
    mem_id = await cortex.store(Memory(
        content="Phone calls before 10am have higher answer rates",
        memory_type="procedural",
    ))
    assert mem_id != ""
    assert cortex.get_stats()["procedural"]["count"] == 1


@pytest.mark.asyncio
async def test_store_auto_extracts_entities(cortex):
    await cortex.store(Memory(
        content="Kingsley Ero at PACAF is interested in DCGS",
        memory_type="episodic",
    ))
    episodes = cortex.get_recent_episodic()
    assert len(episodes) == 1
    assert "DCGS" in episodes[0].programs


# =========================================
# RECALL
# =========================================

@pytest.mark.asyncio
async def test_recall_basic(populated_cortex):
    results = await populated_cortex.recall("DCGS contract")
    assert len(results) > 0
    assert all(isinstance(r, MemoryResult) for r in results)


@pytest.mark.asyncio
async def test_recall_by_type(populated_cortex):
    results = await populated_cortex.recall(
        "DCGS", memory_types=["semantic"],
    )
    for r in results:
        assert r.memory.memory_type == "semantic"


@pytest.mark.asyncio
async def test_recall_has_scores(populated_cortex):
    results = await populated_cortex.recall("PACAF staffing")
    for r in results:
        assert r.combined_score >= 0
        assert r.relevance_score >= 0
        assert r.recency_score >= 0


@pytest.mark.asyncio
async def test_recall_ordered_by_score(populated_cortex):
    results = await populated_cortex.recall("DCGS")
    if len(results) >= 2:
        assert results[0].combined_score >= results[1].combined_score


@pytest.mark.asyncio
async def test_recall_with_limit(populated_cortex):
    results = await populated_cortex.recall("DCGS", limit=2)
    assert len(results) <= 2


# =========================================
# RECALL FOR CONTEXT
# =========================================

@pytest.mark.asyncio
async def test_recall_for_context(populated_cortex):
    context = AgentContext(
        task_description="Build outreach campaign for DCGS contacts",
        programs=["DCGS"],
        agent_type="outreach_crafter",
    )
    ctx_mem = await populated_cortex.recall_for_context(context)
    assert isinstance(ctx_mem, ContextMemory)
    assert ctx_mem.total_memories >= 0
    assert ctx_mem.summary != ""


@pytest.mark.asyncio
async def test_recall_for_context_has_tiers(populated_cortex):
    context = AgentContext(
        task_description="Research PACAF program contacts",
        programs=["DCGS"],
        entities=["PACAF"],
    )
    ctx_mem = await populated_cortex.recall_for_context(context)
    assert isinstance(ctx_mem.episodic, list)
    assert isinstance(ctx_mem.semantic, list)
    assert isinstance(ctx_mem.procedural, list)


# =========================================
# CONSOLIDATE
# =========================================

@pytest.mark.asyncio
async def test_consolidate_empty(cortex):
    report = await cortex.consolidate()
    assert isinstance(report, ConsolidationReport)
    assert report.episodes_scanned == 0


@pytest.mark.asyncio
async def test_consolidate_with_old_episodes(cortex):
    # Store an episode with old timestamp
    old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    await cortex.store(Memory(
        content="Called Kingsley Ero at PACAF about DCGS staffing issues",
        memory_type="episodic",
        created_at=old_time,
    ))
    report = await cortex.consolidate(age_threshold_days=7)
    assert report.episodes_scanned >= 1
    assert report.facts_extracted >= 0


@pytest.mark.asyncio
async def test_consolidate_creates_semantic_facts(cortex):
    old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    await cortex.store(Memory(
        content="Discussed DCGS program status with Leidos team at Langley",
        memory_type="episodic",
        created_at=old_time,
    ))
    initial_semantic = cortex.get_stats()["semantic"]["count"]
    await cortex.consolidate(age_threshold_days=7)
    assert cortex.get_stats()["semantic"]["count"] >= initial_semantic


# =========================================
# REFLECT
# =========================================

@pytest.mark.asyncio
async def test_reflect_empty(cortex):
    insights = await cortex.reflect()
    assert isinstance(insights, list)


@pytest.mark.asyncio
async def test_reflect_with_patterns(cortex):
    # Store multiple episodes with channel patterns
    for i in range(3):
        await cortex.store(Memory(
            content=f"Emailed contact {i} at DCGS. They responded positively.",
            memory_type="episodic",
        ))
    insights = await cortex.reflect()
    # Should detect email channel pattern with 3 mentions (>= 2 threshold)
    assert len(insights) >= 1


@pytest.mark.asyncio
async def test_reflect_hiring_surge(cortex):
    for i in range(3):
        await cortex.store(Memory(
            content=f"DCGS has new hiring position posted for analyst role #{i}",
            memory_type="episodic",
            programs=["DCGS"],
        ))
    insights = await cortex.reflect()
    hiring_insights = [i for i in insights if "hiring" in i.pattern]
    assert len(hiring_insights) >= 1


# =========================================
# FORGET
# =========================================

@pytest.mark.asyncio
async def test_forget_empty(cortex):
    report = await cortex.forget()
    assert isinstance(report, ForgetReport)
    assert report.memories_scanned == 0


@pytest.mark.asyncio
async def test_forget_preserves_critical(cortex):
    await cortex.store(Memory(
        content="Critical contact information",
        memory_type="episodic",
        importance=0.95,
    ))
    report = await cortex.forget()
    assert report.memories_preserved >= 1
    assert report.memories_removed == 0


@pytest.mark.asyncio
async def test_forget_preserves_procedural(cortex):
    await cortex.store(Memory(
        content="Best outreach approach for Langley",
        memory_type="procedural",
        importance=0.3,
    ))
    report = await cortex.forget()
    assert report.memories_preserved >= 1


@pytest.mark.asyncio
async def test_forget_removes_low_importance(cortex):
    await cortex.store(Memory(
        content="Minor note about something",
        memory_type="episodic",
        importance=0.03,
    ))
    report = await cortex.forget(decay_factor=0.5, removal_threshold=0.05)
    assert report.memories_removed >= 1


# =========================================
# SEARCH & ENTITY
# =========================================

@pytest.mark.asyncio
async def test_search(populated_cortex):
    results = await populated_cortex.search("DCGS")
    assert len(results) > 0


@pytest.mark.asyncio
async def test_entity_memories(populated_cortex):
    results = await populated_cortex.get_entity_memories("DCGS")
    assert len(results) > 0


@pytest.mark.asyncio
async def test_entity_memories_empty(cortex):
    results = await cortex.get_entity_memories("nonexistent")
    assert len(results) == 0


# =========================================
# STATISTICS
# =========================================

@pytest.mark.asyncio
async def test_stats(populated_cortex):
    stats = populated_cortex.get_stats()
    assert stats["total_memories"] > 0
    assert "episodic" in stats
    assert "semantic" in stats
    assert "procedural" in stats


def test_recent_episodic_empty(cortex):
    episodes = cortex.get_recent_episodic()
    assert episodes == []


def test_semantic_facts_empty(cortex):
    facts = cortex.get_semantic_facts()
    assert facts == []


def test_procedural_insights_empty(cortex):
    insights = cortex.get_procedural_insights()
    assert insights == []


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    c1 = get_memory_cortex()
    c2 = get_memory_cortex()
    assert c1 is c2
