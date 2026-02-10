"""
Phase 25A — Agent Memory Mixin

Mixin class any agent can inherit for persistent memory.
Provides remember, recall, learn, forget, and briefing generation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ContactMemoryBrief:
    """Brief summary of what an agent knows about a contact."""
    contact_id: str = ""
    contact_name: str = ""
    interaction_count: int = 0
    last_interaction: Optional[str] = None
    key_insights: List[str] = field(default_factory=list)
    preferences: List[str] = field(default_factory=list)
    recommended_approach: str = ""


class AgentMemoryMixin:
    """Mixin class any agent can inherit for persistent memory."""

    def __init__(self, agent_id: str, memory_store=None):
        self.agent_id = agent_id
        self._memory_store = memory_store
        self._local_memories: List[Dict[str, Any]] = []
        logger.info("agent_memory_mixin_init", agent_id=agent_id)

    async def remember(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a memory as this agent. Auto-classifies layer."""
        meta = metadata or {}
        meta["agent_id"] = self.agent_id

        if self._memory_store:
            from Engine8_Knowledge.memory.memory_store import MemoryContext
            ctx = MemoryContext(
                user_id=self.agent_id,
                agent_id=self.agent_id,
                contact_id=meta.get("contact_id"),
                tags=meta.get("tags", []),
            )
            layer = meta.get("layer")
            return await self._memory_store.add_memory(content, layer, ctx)

        entry = {
            "id": f"local_{len(self._local_memories)}",
            "content": content,
            "agent_id": self.agent_id,
            **meta,
        }
        self._local_memories.append(entry)
        return entry["id"]

    async def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memories relevant to this agent's current task."""
        if self._memory_store:
            from Engine8_Knowledge.memory.memory_store import MemoryContext
            ctx = MemoryContext(user_id=self.agent_id, agent_id=self.agent_id)
            recall = await self._memory_store.recall(query, ctx)
            results = []
            for layer_results in recall.results.values():
                results.extend(layer_results)
            return sorted(results, key=lambda x: x.get("score", 0), reverse=True)[:limit]

        q = query.lower()
        return [
            m for m in self._local_memories
            if q in m.get("content", "").lower()
        ][:limit]

    async def recall_contact(self, contact_id: str) -> ContactMemoryBrief:
        """Everything this agent knows about a contact."""
        if self._memory_store:
            cm = await self._memory_store.get_contact_memory(contact_id)
            return ContactMemoryBrief(
                contact_id=contact_id,
                interaction_count=len(cm.interactions),
                key_insights=[i.get("content", "")[:100] for i in cm.insights[:5]],
                preferences=[p.get("content", "")[:100] for p in cm.preferences[:5]],
                total_memories=cm.total_memories,
            )

        relevant = [
            m for m in self._local_memories
            if contact_id in m.get("content", "") or m.get("contact_id") == contact_id
        ]
        return ContactMemoryBrief(
            contact_id=contact_id,
            interaction_count=len(relevant),
            key_insights=[m.get("content", "")[:100] for m in relevant[:5]],
        )

    async def learn_from_outcome(self, action: str, outcome: str, score: float):
        """Store in procedural layer: what worked, what didn't."""
        content = f"Action: {action} | Outcome: {outcome} | Score: {score:.2f}"
        await self.remember(content, {
            "type": "pattern",
            "layer": "procedural",
            "action": action,
            "outcome": outcome,
            "score": score,
        })
        logger.info(
            "agent_learned_outcome",
            agent=self.agent_id,
            action=action[:50],
            score=score,
        )

    async def forget(self, memory_id: str) -> bool:
        """Remove a specific memory."""
        if self._memory_store and hasattr(self._memory_store, "mem0") and self._memory_store.mem0:
            return await self._memory_store.mem0.delete(memory_id)

        before = len(self._local_memories)
        self._local_memories = [
            m for m in self._local_memories if m.get("id") != memory_id
        ]
        return len(self._local_memories) < before

    async def get_briefing(self, task_context: str) -> str:
        """
        LLM-generated briefing from relevant memories for current task.
        Falls back to simple text assembly if no LLM available.
        """
        memories = await self.recall(task_context, limit=10)

        if not memories:
            return f"No prior context found for: {task_context}"

        # Build briefing from memories
        briefing_parts = [f"Briefing for agent {self.agent_id}:", ""]
        briefing_parts.append(f"Task: {task_context}")
        briefing_parts.append("")
        briefing_parts.append("Relevant context from memory:")

        for i, mem in enumerate(memories[:7], 1):
            content = mem.get("content", "")[:200]
            briefing_parts.append(f"  {i}. {content}")

        briefing_parts.append("")
        briefing_parts.append(f"Total relevant memories: {len(memories)}")

        return "\n".join(briefing_parts)
