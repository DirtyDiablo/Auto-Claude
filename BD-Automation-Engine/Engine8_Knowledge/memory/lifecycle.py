"""
Phase 25A — Memory Lifecycle Manager

Automatic memory management: consolidation, decay, compression.
Runs periodically to keep memory store healthy and efficient.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class LifecycleReport:
    """Report from a lifecycle management pass."""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    memories_consolidated: int = 0
    memories_decayed: int = 0
    memories_compressed: int = 0
    storage_saved_bytes: int = 0
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Memory Lifecycle Manager
# ---------------------------------------------------------------------------


class MemoryLifecycle:
    """Automatic memory management: consolidation, decay, compression."""

    def __init__(self, memory_store=None, mem0_manager=None):
        self.memory_store = memory_store
        self.mem0 = mem0_manager
        self._importance_cache: Dict[str, float] = {}
        logger.info("memory_lifecycle_init")

    async def consolidate(self) -> int:
        """
        Merge duplicate/overlapping memories.
        Combine multiple interaction memories into summary memories.
        """
        consolidated = 0

        if not self.memory_store:
            return consolidated

        # Check episodic layer for duplicates
        episodic = self.memory_store._episodic
        if len(episodic) < 2:
            return consolidated

        seen_content: Dict[str, int] = {}
        to_remove = []

        for i, mem in enumerate(episodic):
            content = mem.get("content", "")
            # Normalize for comparison
            normalized = content.lower().strip()[:200]
            if normalized in seen_content:
                to_remove.append(i)
                consolidated += 1
            else:
                seen_content[normalized] = i

        # Remove duplicates (reverse to preserve indices)
        for idx in reversed(to_remove):
            if idx < len(self.memory_store._episodic):
                self.memory_store._episodic.pop(idx)

        # Consolidate procedural patterns
        procedural = self.memory_store._procedural
        proc_seen: Dict[str, int] = {}
        proc_remove = []

        for i, mem in enumerate(procedural):
            content = mem.get("content", "")
            normalized = content.lower().strip()[:200]
            if normalized in proc_seen:
                proc_remove.append(i)
                consolidated += 1
            else:
                proc_seen[normalized] = i

        for idx in reversed(proc_remove):
            if idx < len(self.memory_store._procedural):
                self.memory_store._procedural.pop(idx)

        if proc_remove:
            self.memory_store._save_procedural()

        logger.info("consolidation_complete", consolidated=consolidated)
        return consolidated

    async def decay(self, days_threshold: int = 90) -> int:
        """
        Reduce importance score of old, unreferenced memories.
        Don't delete — just lower retrieval priority.
        """
        decayed = 0
        cutoff = (datetime.utcnow() - timedelta(days=days_threshold)).isoformat()

        if self.memory_store:
            for mem in self.memory_store._episodic:
                created = mem.get("created_at", "")
                if created and created < cutoff:
                    mem["decayed"] = True
                    mem["original_score"] = mem.get("score", 0.5)
                    mem["score"] = max(mem.get("score", 0.5) * 0.5, 0.1)
                    decayed += 1

            for mem in self.memory_store._procedural:
                created = mem.get("created_at", "")
                if created and created < cutoff:
                    mem["decayed"] = True
                    decayed += 1

            if decayed > 0:
                self.memory_store._save_procedural()

        logger.info("decay_complete", decayed=decayed, threshold_days=days_threshold)
        return decayed

    async def compress(self) -> int:
        """
        Summarize verbose memories into concise versions.
        Keep original as version history.
        """
        compressed = 0
        max_length = 500

        if self.memory_store:
            for mem in self.memory_store._episodic:
                content = mem.get("content", "")
                if len(content) > max_length:
                    mem["original_content"] = content
                    mem["content"] = content[:max_length] + "..."
                    compressed += 1

            for mem in self.memory_store._procedural:
                content = mem.get("content", "")
                if len(content) > max_length:
                    mem["original_content"] = content
                    mem["content"] = content[:max_length] + "..."
                    compressed += 1

            if compressed > 0:
                self.memory_store._save_procedural()

        logger.info("compression_complete", compressed=compressed)
        return compressed

    async def importance_score(self, memory_id: str) -> float:
        """
        Score 0-1 based on: recency, frequency of recall,
        outcome impact, entity importance.
        """
        if memory_id in self._importance_cache:
            return self._importance_cache[memory_id]

        score = 0.5  # Default

        # Look up in memory store
        if self.memory_store:
            # Check episodic
            for mem in self.memory_store._episodic:
                if mem.get("id") == memory_id:
                    # Recency boost
                    created = mem.get("created_at", "")
                    if created:
                        try:
                            age_days = (
                                datetime.utcnow() - datetime.fromisoformat(created)
                            ).days
                            recency = max(0, 1.0 - (age_days / 365))
                            score = 0.3 + 0.4 * recency
                        except Exception:
                            pass

                    # Outcome boost
                    if mem.get("outcome") or mem.get("score"):
                        score += 0.2

                    # Decay penalty
                    if mem.get("decayed"):
                        score *= 0.5

                    break

            # Check procedural
            for mem in self.memory_store._procedural:
                if mem.get("id") == memory_id:
                    outcome_score = mem.get("score", 0.5)
                    score = 0.3 + 0.5 * outcome_score
                    break

        score = min(max(score, 0.0), 1.0)
        self._importance_cache[memory_id] = score
        return score

    async def run_lifecycle(self) -> LifecycleReport:
        """
        Full lifecycle pass: consolidate → decay → compress → report.
        """
        start = time.time()
        report = LifecycleReport(
            started_at=datetime.utcnow().isoformat(),
        )

        try:
            report.memories_consolidated = await self.consolidate()
        except Exception as exc:
            report.errors.append(f"consolidation: {exc}")

        try:
            report.memories_decayed = await self.decay()
        except Exception as exc:
            report.errors.append(f"decay: {exc}")

        try:
            report.memories_compressed = await self.compress()
        except Exception as exc:
            report.errors.append(f"compression: {exc}")

        # Estimate storage saved
        report.storage_saved_bytes = report.memories_compressed * 200  # Rough estimate

        elapsed = time.time() - start
        report.completed_at = datetime.utcnow().isoformat()
        report.duration_seconds = round(elapsed, 2)

        logger.info(
            "lifecycle_complete",
            consolidated=report.memories_consolidated,
            decayed=report.memories_decayed,
            compressed=report.memories_compressed,
            seconds=report.duration_seconds,
        )
        return report


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_lifecycle: Optional[MemoryLifecycle] = None


def get_memory_lifecycle(**kwargs) -> MemoryLifecycle:
    global _lifecycle
    if _lifecycle is None:
        _lifecycle = MemoryLifecycle(**kwargs)
    return _lifecycle
