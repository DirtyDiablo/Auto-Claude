"""Tests for Phase 42A — Memory-Aware Agent Mixin v2."""

import pytest
import pytest_asyncio

from src.memory.cortex import MemoryCortex, Memory
from src.memory.agent_mixin_v2 import MemoryAwareAgentV2


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def cortex():
    return MemoryCortex()


@pytest.fixture
def agent(cortex):
    return MemoryAwareAgentV2(agent_type="research", cortex=cortex)


@pytest_asyncio.fixture
async def agent_with_context(cortex):
    """Agent with pre-loaded memory context."""
    # Pre-load some memories
    await cortex.store(
        Memory(
            content="Called John Smith at Leidos about DCGS program status",
            memory_type="episodic",
            programs=["DCGS"],
            contacts=["John Smith"],
        )
    )
    await cortex.store(
        Memory(
            content="DCGS-A is a $450M intelligence program",
            memory_type="semantic",
            programs=["DCGS"],
            confidence=0.9,
        )
    )
    await cortex.store(
        Memory(
            content="Phone outreach to Tier 3+ contacts has high response rate",
            memory_type="procedural",
            importance=0.8,
        )
    )
    return MemoryAwareAgentV2(agent_type="outreach", cortex=cortex)


# =========================================
# BEFORE TASK
# =========================================


@pytest.mark.asyncio
async def test_before_task_returns_context(agent_with_context):
    ctx = await agent_with_context.before_task(
        task_description="Build outreach campaign for DCGS contacts",
        programs=["DCGS"],
    )
    assert ctx.total_memories >= 0
    assert ctx.summary != ""


@pytest.mark.asyncio
async def test_before_task_empty_context(agent):
    ctx = await agent.before_task(task_description="Research something new")
    assert ctx.total_memories == 0
    assert "No relevant memories" in ctx.summary


# =========================================
# AFTER TASK
# =========================================


@pytest.mark.asyncio
async def test_after_task_stores_episode(agent, cortex):
    mem_id = await agent.after_task(
        task_description="Researched DCGS program contacts",
        result={"contacts_found": 5, "status": "completed"},
        success=True,
    )
    assert mem_id != ""
    stats = cortex.get_stats()
    assert stats["episodic"]["count"] == 1


@pytest.mark.asyncio
async def test_after_task_failure(agent, cortex):
    mem_id = await agent.after_task(
        task_description="Failed to reach API",
        result={"error": "timeout"},
        success=False,
        notes="API was down",
    )
    assert mem_id != ""
    # Failures have slightly higher importance
    episodes = cortex.get_recent_episodic()
    assert episodes[0].importance >= 0.6


@pytest.mark.asyncio
async def test_after_task_with_notes(agent, cortex):
    await agent.after_task(
        task_description="Contacted John Smith",
        result={"status": "completed"},
        notes="He seemed interested in DCGS opportunity",
    )
    episodes = cortex.get_recent_episodic()
    assert "interested" in episodes[0].content


# =========================================
# ON DISCOVERY
# =========================================


@pytest.mark.asyncio
async def test_on_discovery(agent, cortex):
    mem_id = await agent.on_discovery(
        fact="Kingsley Ero is the Acting Site Lead at PACAF San Diego",
        entities=["Kingsley Ero", "PACAF"],
        confidence=0.85,
    )
    assert mem_id != ""
    stats = cortex.get_stats()
    assert stats["semantic"]["count"] == 1


@pytest.mark.asyncio
async def test_on_discovery_low_confidence(agent, cortex):
    await agent.on_discovery(
        fact="DCGS contract might be recompeted in 2026",
        confidence=0.3,
    )
    facts = cortex.get_semantic_facts()
    assert len(facts) == 1
    assert facts[0].confidence == 0.3


# =========================================
# ON STRATEGY OUTCOME
# =========================================


@pytest.mark.asyncio
async def test_on_strategy_success(agent, cortex):
    mem_id = await agent.on_strategy_outcome(
        strategy="LinkedIn outreach to Tier 4 managers",
        outcome="3 out of 5 responded within 48 hours",
        success=True,
        effectiveness=0.6,
        applicable_to=["DCGS", "Langley"],
    )
    assert mem_id != ""
    stats = cortex.get_stats()
    assert stats["procedural"]["count"] == 1


@pytest.mark.asyncio
async def test_on_strategy_failure(agent, cortex):
    await agent.on_strategy_outcome(
        strategy="Cold email to government contacts",
        outcome="0 responses out of 10 sent",
        success=False,
        effectiveness=0.0,
    )
    stats = cortex.get_stats()
    assert stats["procedural"]["count"] == 1


# =========================================
# SESSION TRACKING
# =========================================


@pytest.mark.asyncio
async def test_session_memories(agent):
    await agent.after_task("Task 1", {"status": "ok"})
    await agent.on_discovery("Fact 1")
    await agent.on_strategy_outcome("Strategy 1", "Outcome 1")
    assert len(agent.get_session_memories()) == 3


def test_session_id(agent):
    assert agent._session_id != ""
    assert len(agent._session_id) == 10


# =========================================
# AGENT TYPE
# =========================================


def test_agent_type():
    agent = MemoryAwareAgentV2(agent_type="outreach_crafter")
    assert agent.agent_type == "outreach_crafter"


def test_cortex_access(agent, cortex):
    assert agent.cortex is cortex
