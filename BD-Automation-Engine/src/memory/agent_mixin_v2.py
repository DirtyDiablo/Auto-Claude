"""Phase 42A — Memory-Aware Agent Mixin v2

Gives any agent automatic access to the unified memory cortex.
Handles memory recall before tasks, storage after tasks,
discovery of new facts, and strategy outcome recording.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.memory.cortex import (
    MemoryCortex,
    Memory,
    MemoryType,
    MemoryResult,
    ContextMemory,
    AgentContext,
    ProceduralInsight,
    get_memory_cortex,
)

logger = logging.getLogger(__name__)


class MemoryAwareAgentV2:
    """Mixin that gives any agent access to the full memory cortex.

    Automatically:
      - Recalls relevant context before executing a task
      - Stores new observations as episodic memories
      - Records task outcomes for procedural learning
      - Updates semantic memory when new facts are discovered
    """

    def __init__(
        self,
        agent_type: str = "generic",
        cortex: Optional[MemoryCortex] = None,
    ):
        self.agent_type = agent_type
        self._cortex = cortex or get_memory_cortex()
        self._session_id = uuid.uuid4().hex[:10]
        self._task_memories: List[str] = []  # IDs of memories stored this session

    @property
    def cortex(self) -> MemoryCortex:
        return self._cortex

    # -----------------------------------------
    # BEFORE TASK
    # -----------------------------------------

    async def before_task(
        self,
        task_description: str,
        entities: Optional[List[str]] = None,
        programs: Optional[List[str]] = None,
        contacts: Optional[List[str]] = None,
    ) -> ContextMemory:
        """Recall all relevant memories and prepare agent context.

        Called automatically before a task begins. Returns structured
        memory context that the agent can use in its prompt/reasoning.
        """
        context = AgentContext(
            task_type=self.agent_type,
            task_description=task_description,
            entities=entities or [],
            programs=programs or [],
            contacts=contacts or [],
            agent_type=self.agent_type,
            session_id=self._session_id,
        )

        memory_context = await self._cortex.recall_for_context(context)

        logger.debug(
            "Agent %s recalled %d memories for task: %s",
            self.agent_type, memory_context.total_memories,
            task_description[:60],
        )

        return memory_context

    # -----------------------------------------
    # AFTER TASK
    # -----------------------------------------

    async def after_task(
        self,
        task_description: str,
        result: Dict[str, Any],
        success: bool = True,
        notes: str = "",
    ) -> str:
        """Store task execution as an episodic memory and record outcome.

        Called automatically after a task completes. Creates an episodic
        memory of what happened and optionally records the outcome for
        procedural learning.
        """
        # Build episodic content
        status = "succeeded" if success else "failed"
        content_parts = [
            f"Task: {task_description}",
            f"Agent: {self.agent_type}",
            f"Status: {status}",
        ]
        if notes:
            content_parts.append(f"Notes: {notes}")

        # Summarize result
        result_summary = self._summarize_result(result)
        if result_summary:
            content_parts.append(f"Result: {result_summary}")

        episode = Memory(
            content=" | ".join(content_parts),
            memory_type=MemoryType.EPISODIC.value,
            importance=0.6 if success else 0.7,  # failures are slightly more important to remember
            source=f"agent:{self.agent_type}",
            tags=["task_execution", self.agent_type, status],
            metadata={
                "session_id": self._session_id,
                "success": success,
                "result_keys": list(result.keys()) if isinstance(result, dict) else [],
            },
        )

        mem_id = await self._cortex.store(episode)
        self._task_memories.append(mem_id)

        logger.debug("Stored episodic memory %s for task: %s", mem_id, task_description[:60])
        return mem_id

    # -----------------------------------------
    # ON DISCOVERY
    # -----------------------------------------

    async def on_discovery(
        self,
        fact: str,
        entities: Optional[List[str]] = None,
        confidence: float = 0.7,
        source: str = "",
    ) -> str:
        """When agent discovers a new fact, store in semantic memory.

        Called when an agent discovers a new fact during execution, e.g.:
        - "Kingsley Ero is the Acting Site Lead at PACAF"
        - "DCGS-A contract was awarded to Raytheon in Q2 2025"
        """
        semantic = Memory(
            content=fact,
            memory_type=MemoryType.SEMANTIC.value,
            importance=0.65,
            entities=entities or [],
            source=source or f"agent:{self.agent_type}",
            confidence=confidence,
            tags=["discovered_fact", self.agent_type],
            metadata={
                "session_id": self._session_id,
                "discovered_by": self.agent_type,
            },
        )

        mem_id = await self._cortex.store(semantic)
        self._task_memories.append(mem_id)

        logger.debug("Stored semantic discovery %s: %s", mem_id, fact[:60])
        return mem_id

    # -----------------------------------------
    # ON STRATEGY OUTCOME
    # -----------------------------------------

    async def on_strategy_outcome(
        self,
        strategy: str,
        outcome: str,
        success: bool = True,
        effectiveness: float = 0.5,
        applicable_to: Optional[List[str]] = None,
    ) -> str:
        """Record whether a strategy worked or failed for procedural learning.

        Called when an agent tries a specific approach and observes the result:
        - "LinkedIn outreach to Tier 4 managers" → "Got 3 responses out of 5 sent"
        - "Email follow-up within 48 hours" → "2x higher response rate"
        """
        status = "effective" if success else "ineffective"
        content = (
            f"Strategy: {strategy} | Outcome: {outcome} | "
            f"Effectiveness: {effectiveness:.0%} | Status: {status}"
        )

        procedural = Memory(
            content=content,
            memory_type=MemoryType.PROCEDURAL.value,
            importance=0.7 + (effectiveness * 0.2) if success else 0.6,
            source=f"agent:{self.agent_type}",
            tags=["strategy_outcome", self.agent_type, status],
            confidence=0.6 + (0.3 if success else 0.0),
            metadata={
                "session_id": self._session_id,
                "strategy": strategy,
                "outcome": outcome,
                "success": success,
                "effectiveness": effectiveness,
                "applicable_to": applicable_to or [],
            },
        )

        mem_id = await self._cortex.store(procedural)
        self._task_memories.append(mem_id)

        logger.debug("Stored procedural memory %s: %s → %s", mem_id, strategy[:40], outcome[:40])
        return mem_id

    # -----------------------------------------
    # HELPERS
    # -----------------------------------------

    def _summarize_result(self, result: Dict[str, Any]) -> str:
        """Create a brief summary of a task result."""
        if not isinstance(result, dict):
            return str(result)[:100]

        parts = []
        for key in ["status", "contacts_found", "jobs_found", "documents_generated",
                     "insights", "matches_found", "messages_crafted"]:
            if key in result:
                val = result[key]
                if isinstance(val, list):
                    parts.append(f"{key}={len(val)}")
                else:
                    parts.append(f"{key}={val}")

        return ", ".join(parts) if parts else f"keys={list(result.keys())[:5]}"

    def get_session_memories(self) -> List[str]:
        """Get IDs of all memories stored in this session."""
        return list(self._task_memories)
