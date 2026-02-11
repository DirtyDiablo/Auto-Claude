"""Phase 42A — Unified Memory Cortex

Three-tier memory architecture inspired by human cognition:

EPISODIC MEMORY (What happened):
  - Interactions, conversations, scrapes, campaign events
  - Timestamped, context-rich, decays over time
  - Example: "On Jan 13, we called Kingsley Ero. He mentioned being stretched thin."

SEMANTIC MEMORY (What we know):
  - Extracted facts, relationships, classifications
  - Confidence-scored, multi-sourced, temporal
  - Example: "Kingsley Ero is the Acting Site Lead at PACAF San Diego"

PROCEDURAL MEMORY (What works):
  - Patterns, strategies, outcomes from past campaigns
  - Success/failure attribution, approach effectiveness scores
  - Example: "LinkedIn outreach to Tier 4 managers has 3x response rate vs email"
"""

import logging
import math
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# =========================================
# ENUMS
# =========================================

class MemoryType(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class ImportanceLevel(str, Enum):
    CRITICAL = "critical"    # 0.9-1.0: never forget
    HIGH = "high"            # 0.7-0.9: long-term retention
    MEDIUM = "medium"        # 0.4-0.7: normal decay
    LOW = "low"              # 0.1-0.4: fast decay
    TRIVIAL = "trivial"      # 0.0-0.1: forget quickly


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class Memory:
    """A single memory entry in any tier."""
    id: str = ""
    content: str = ""
    memory_type: str = MemoryType.EPISODIC.value
    importance: float = 0.5
    context: Dict[str, Any] = field(default_factory=dict)
    entities: List[str] = field(default_factory=list)
    programs: List[str] = field(default_factory=list)
    contacts: List[str] = field(default_factory=list)
    source: str = ""
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.8
    access_count: int = 0
    created_at: str = ""
    last_accessed: str = ""
    expires_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryResult:
    """A memory retrieval result with scoring."""
    memory: Memory
    relevance_score: float = 0.0
    recency_score: float = 0.0
    importance_score: float = 0.0
    combined_score: float = 0.0


@dataclass
class AgentContext:
    """Context describing what an agent is currently working on."""
    task_type: str = ""
    task_description: str = ""
    entities: List[str] = field(default_factory=list)
    programs: List[str] = field(default_factory=list)
    contacts: List[str] = field(default_factory=list)
    agent_type: str = ""
    session_id: str = ""


@dataclass
class ContextMemory:
    """Structured memory context for agent consumption."""
    episodic: List[MemoryResult] = field(default_factory=list)
    semantic: List[MemoryResult] = field(default_factory=list)
    procedural: List[MemoryResult] = field(default_factory=list)
    summary: str = ""
    total_memories: int = 0


@dataclass
class ProceduralInsight:
    """An insight extracted from episodic patterns."""
    id: str = ""
    pattern: str = ""
    insight: str = ""
    confidence: float = 0.0
    evidence_count: int = 0
    effectiveness_score: float = 0.0
    category: str = ""  # outreach, enrichment, research, timing
    applicable_to: List[str] = field(default_factory=list)
    created_at: str = ""


@dataclass
class ConsolidationReport:
    """Report from a memory consolidation run."""
    episodes_scanned: int = 0
    facts_extracted: int = 0
    facts_updated: int = 0
    facts_new: int = 0
    episodes_compressed: int = 0
    insights_generated: int = 0
    duration_seconds: float = 0.0
    timestamp: str = ""


@dataclass
class ForgetReport:
    """Report from a memory decay/forget run."""
    memories_scanned: int = 0
    memories_decayed: int = 0
    memories_removed: int = 0
    memories_preserved: int = 0
    timestamp: str = ""


# =========================================
# ENTITY EXTRACTION
# =========================================

# Programs
_PROGRAM_RE = re.compile(
    r'\b(DCGS|DCGS-[A-Z]|GBSD|NGEN|DEOS|CES|JADC2|ABMS|ODIN|TITAN)\b',
    re.IGNORECASE,
)

# Organizations
_ORG_RE = re.compile(
    r'\b(GDIT|Leidos|SAIC|Northrop|Raytheon|Lockheed|BAE|CACI|ManTech|Peraton'
    r'|Navy|Army|Air Force|PACAF)\b',
    re.IGNORECASE,
)

# Locations
_LOC_RE = re.compile(
    r'\b(Norfolk|Langley|Wright-Patterson|San Diego|Fort Meade|Huntsville)\b',
    re.IGNORECASE,
)

# People (Capitalized First Last)
_PERSON_RE = re.compile(r'\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,})\b')


def _extract_entities(text: str) -> Dict[str, List[str]]:
    """Extract entities from text across all categories."""
    entities: Dict[str, List[str]] = {
        "programs": [],
        "organizations": [],
        "locations": [],
        "people": [],
    }

    for m in _PROGRAM_RE.finditer(text):
        name = m.group(0).upper()
        if name not in entities["programs"]:
            entities["programs"].append(name)

    for m in _ORG_RE.finditer(text):
        name = m.group(0)
        if name not in entities["organizations"]:
            entities["organizations"].append(name)

    for m in _LOC_RE.finditer(text):
        name = m.group(0)
        if name not in entities["locations"]:
            entities["locations"].append(name)

    for m in _PERSON_RE.finditer(text):
        name = m.group(0)
        # Filter out common false positives
        if name.split()[0].lower() not in {
            "the", "this", "that", "what", "when", "where", "which",
            "monday", "tuesday", "wednesday", "thursday", "friday",
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
        }:
            if name not in entities["people"]:
                entities["people"].append(name)

    return entities


def _compute_importance(content: str, memory_type: str, metadata: Dict[str, Any]) -> float:
    """Compute importance score for a memory."""
    score = 0.3  # base

    # Content length factor
    words = len(content.split())
    score += min(words / 100, 0.1)

    # Entity density
    entities = _extract_entities(content)
    entity_count = sum(len(v) for v in entities.values())
    score += min(entity_count * 0.05, 0.15)

    # Memory type factor
    if memory_type == MemoryType.PROCEDURAL.value:
        score += 0.15  # procedural insights are inherently valuable
    elif memory_type == MemoryType.SEMANTIC.value:
        score += 0.1

    # Explicit importance from metadata
    if "importance" in metadata:
        score = metadata["importance"]

    # Human-verified boost
    if metadata.get("human_verified"):
        score = max(score, 0.9)

    return min(round(score, 4), 1.0)


# =========================================
# SIMILARITY SCORING
# =========================================

def _token_overlap(text_a: str, text_b: str) -> float:
    """Simple token overlap similarity."""
    tokens_a = set(text_a.lower().split())
    tokens_b = set(text_b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union) if union else 0.0


def _entity_overlap(query_entities: Dict[str, List[str]], memory: Memory) -> float:
    """Score based on entity overlap between query and memory."""
    query_set: Set[str] = set()
    for vals in query_entities.values():
        query_set.update(v.lower() for v in vals)

    memory_set: Set[str] = set()
    for e in memory.entities:
        memory_set.add(e.lower())
    for p in memory.programs:
        memory_set.add(p.lower())
    for c in memory.contacts:
        memory_set.add(c.lower())

    if not query_set or not memory_set:
        return 0.0

    overlap = query_set & memory_set
    return len(overlap) / max(len(query_set), 1)


def _recency_score(memory: Memory) -> float:
    """Score based on how recent a memory is. Exponential decay."""
    if not memory.created_at:
        return 0.5

    try:
        created = datetime.fromisoformat(memory.created_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_days = (now - created).total_seconds() / 86400
        # Half-life of 30 days
        return math.exp(-0.693 * age_days / 30)
    except (ValueError, TypeError):
        return 0.5


# =========================================
# MEMORY CORTEX
# =========================================

class MemoryCortex:
    """Unified memory system with episodic, semantic, and procedural tiers."""

    def __init__(self):
        # In-memory stores (production would use Redis + Qdrant + Neo4j)
        self._episodic: Dict[str, Memory] = {}
        self._semantic: Dict[str, Memory] = {}
        self._procedural: Dict[str, Memory] = {}
        self._insights: List[ProceduralInsight] = []
        self._consolidation_history: List[ConsolidationReport] = []
        self._forget_history: List[ForgetReport] = []

    def _store_for(self, memory_type: str) -> Dict[str, Memory]:
        """Get the store dict for a given memory type."""
        if memory_type == MemoryType.SEMANTIC.value:
            return self._semantic
        elif memory_type == MemoryType.PROCEDURAL.value:
            return self._procedural
        return self._episodic

    # -----------------------------------------
    # STORE
    # -----------------------------------------

    async def store(self, memory: Memory) -> str:
        """Store a new memory in the appropriate tier."""
        if not memory.id:
            memory.id = uuid.uuid4().hex[:12]

        now_iso = datetime.now(timezone.utc).isoformat()
        if not memory.created_at:
            memory.created_at = now_iso
        if not memory.last_accessed:
            memory.last_accessed = now_iso

        # Auto-extract entities from content
        if not memory.entities and not memory.programs and not memory.contacts:
            extracted = _extract_entities(memory.content)
            memory.entities = (
                extracted["people"] + extracted["organizations"] + extracted["locations"]
            )
            memory.programs = extracted["programs"]
            memory.contacts = extracted["people"]

        # Auto-compute importance if not set
        if memory.importance == 0.5 and "importance" not in memory.metadata:
            memory.importance = _compute_importance(
                memory.content, memory.memory_type, memory.metadata,
            )

        store = self._store_for(memory.memory_type)
        store[memory.id] = memory

        logger.debug("Stored %s memory %s (importance=%.2f)",
                      memory.memory_type, memory.id, memory.importance)
        return memory.id

    # -----------------------------------------
    # RECALL
    # -----------------------------------------

    async def recall(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        time_range: Optional[Tuple[str, str]] = None,
        limit: int = 10,
        min_score: float = 0.01,
    ) -> List[MemoryResult]:
        """Retrieve memories relevant to a query.

        Rank by: relevance × recency × importance.
        """
        if memory_types is None:
            memory_types = [mt.value for mt in MemoryType]

        query_entities = _extract_entities(query)
        candidates: List[MemoryResult] = []

        for mt in memory_types:
            store = self._store_for(mt)
            for mem in store.values():
                # Time range filter
                if time_range and mem.created_at:
                    if mem.created_at < time_range[0] or mem.created_at > time_range[1]:
                        continue

                # Compute scores
                text_sim = _token_overlap(query, mem.content)
                entity_sim = _entity_overlap(query_entities, mem)
                relevance = (text_sim * 0.5) + (entity_sim * 0.5)
                recency = _recency_score(mem)

                combined = (relevance * 0.5) + (recency * 0.25) + (mem.importance * 0.25)

                if combined >= min_score:
                    # Update access tracking
                    mem.access_count += 1
                    mem.last_accessed = datetime.now(timezone.utc).isoformat()

                    candidates.append(MemoryResult(
                        memory=mem,
                        relevance_score=round(relevance, 4),
                        recency_score=round(recency, 4),
                        importance_score=round(mem.importance, 4),
                        combined_score=round(combined, 4),
                    ))

        # Sort by combined score descending
        candidates.sort(key=lambda r: r.combined_score, reverse=True)
        return candidates[:limit]

    async def recall_for_context(self, context: AgentContext) -> ContextMemory:
        """Recall all relevant memories for an agent's current task context."""
        # Build query from context
        query_parts = [context.task_description]
        query_parts.extend(context.entities)
        query_parts.extend(context.programs)
        query_parts.extend(context.contacts)
        query = " ".join(query_parts)

        # Recall from each tier
        episodic = await self.recall(
            query, memory_types=[MemoryType.EPISODIC.value], limit=5,
        )
        semantic = await self.recall(
            query, memory_types=[MemoryType.SEMANTIC.value], limit=5,
        )
        procedural = await self.recall(
            query, memory_types=[MemoryType.PROCEDURAL.value], limit=3,
        )

        total = len(episodic) + len(semantic) + len(procedural)

        # Generate summary
        summary_parts = []
        if episodic:
            summary_parts.append(
                f"Found {len(episodic)} past interactions related to this task."
            )
        if semantic:
            summary_parts.append(
                f"Found {len(semantic)} relevant facts."
            )
        if procedural:
            summary_parts.append(
                f"Found {len(procedural)} strategy insights."
            )

        summary = " ".join(summary_parts) if summary_parts else "No relevant memories found."

        return ContextMemory(
            episodic=episodic,
            semantic=semantic,
            procedural=procedural,
            summary=summary,
            total_memories=total,
        )

    # -----------------------------------------
    # CONSOLIDATE
    # -----------------------------------------

    async def consolidate(self, age_threshold_days: int = 7) -> ConsolidationReport:
        """Memory consolidation: compress old episodes into semantic facts."""
        import time as _time
        start = _time.time()

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=age_threshold_days)
        cutoff_iso = cutoff.isoformat()

        episodes_scanned = 0
        facts_extracted = 0
        facts_updated = 0
        facts_new = 0
        episodes_compressed = 0
        insights_generated = 0

        # Scan old episodic memories
        old_episodes: List[Memory] = []
        for mem in self._episodic.values():
            if mem.created_at and mem.created_at < cutoff_iso:
                old_episodes.append(mem)
            episodes_scanned += 1

        for episode in old_episodes:
            # Extract entities as semantic facts
            extracted = _extract_entities(episode.content)
            all_entities = (
                extracted["programs"] + extracted["organizations"]
                + extracted["people"] + extracted["locations"]
            )

            for entity in all_entities:
                fact_key = f"entity:{entity.lower()}"
                existing = self._find_semantic_by_entity(entity)

                if existing:
                    # Update confidence
                    existing.confidence = min(existing.confidence + 0.05, 1.0)
                    existing.access_count += 1
                    existing.metadata.setdefault("sources", [])
                    if episode.id not in existing.metadata["sources"]:
                        existing.metadata["sources"].append(episode.id)
                    facts_updated += 1
                else:
                    # Create new semantic fact
                    fact = Memory(
                        content=f"Entity: {entity} — referenced in episode: {episode.content[:100]}",
                        memory_type=MemoryType.SEMANTIC.value,
                        importance=0.6,
                        entities=[entity],
                        programs=extracted["programs"],
                        contacts=extracted["people"],
                        source=f"consolidated_from:{episode.id}",
                        confidence=0.6,
                        metadata={"sources": [episode.id]},
                    )
                    await self.store(fact)
                    facts_new += 1

                facts_extracted += 1

            # Compress episode: keep summary, mark as consolidated
            if len(episode.content) > 200:
                episode.content = episode.content[:200] + "... [consolidated]"
                episode.metadata["consolidated"] = True
                episode.metadata["consolidated_at"] = now.isoformat()
                episodes_compressed += 1

        # Generate procedural insights from patterns
        new_insights = await self._extract_patterns(old_episodes)
        insights_generated = len(new_insights)

        elapsed = round(_time.time() - start, 2)
        report = ConsolidationReport(
            episodes_scanned=episodes_scanned,
            facts_extracted=facts_extracted,
            facts_updated=facts_updated,
            facts_new=facts_new,
            episodes_compressed=episodes_compressed,
            insights_generated=insights_generated,
            duration_seconds=elapsed,
            timestamp=now.isoformat(),
        )
        self._consolidation_history.append(report)
        return report

    # -----------------------------------------
    # REFLECT
    # -----------------------------------------

    async def reflect(self) -> List[ProceduralInsight]:
        """Generate procedural insights from episodic patterns."""
        episodes = list(self._episodic.values())
        return await self._extract_patterns(episodes)

    async def _extract_patterns(self, episodes: List[Memory]) -> List[ProceduralInsight]:
        """Extract procedural insights from a set of episodes."""
        insights: List[ProceduralInsight] = []

        if not episodes:
            return insights

        # Pattern 1: Outreach channel effectiveness
        channel_outcomes = self._analyze_channel_patterns(episodes)
        for channel, data in channel_outcomes.items():
            if data["count"] >= 2:
                effectiveness = data["success"] / data["count"] if data["count"] else 0
                insight = ProceduralInsight(
                    id=uuid.uuid4().hex[:10],
                    pattern=f"outreach_channel:{channel}",
                    insight=f"{channel} outreach has {effectiveness:.0%} effectiveness "
                            f"based on {data['count']} interactions.",
                    confidence=min(data["count"] / 10, 1.0),
                    evidence_count=data["count"],
                    effectiveness_score=round(effectiveness, 4),
                    category="outreach",
                    applicable_to=data.get("programs", []),
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
                insights.append(insight)

                # Store as procedural memory
                mem = Memory(
                    content=insight.insight,
                    memory_type=MemoryType.PROCEDURAL.value,
                    importance=0.7 + (effectiveness * 0.2),
                    source="reflection_engine",
                    tags=["insight", "outreach", channel],
                    confidence=insight.confidence,
                    programs=data.get("programs", []),
                )
                await self.store(mem)

        # Pattern 2: Entity activity frequency
        entity_freq = self._analyze_entity_frequency(episodes)
        for entity, count in entity_freq.items():
            if count >= 3:
                insight = ProceduralInsight(
                    id=uuid.uuid4().hex[:10],
                    pattern=f"entity_activity:{entity}",
                    insight=f"{entity} appears in {count} episodes — high activity entity.",
                    confidence=min(count / 10, 1.0),
                    evidence_count=count,
                    effectiveness_score=0.0,
                    category="research",
                    applicable_to=[entity],
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
                insights.append(insight)

        # Pattern 3: Program hiring surge detection
        program_mentions = self._analyze_program_mentions(episodes)
        for program, data in program_mentions.items():
            if data["hiring_mentions"] >= 2:
                insight = ProceduralInsight(
                    id=uuid.uuid4().hex[:10],
                    pattern=f"hiring_surge:{program}",
                    insight=f"{program} has {data['hiring_mentions']} hiring-related episodes "
                            f"— potential BD opportunity.",
                    confidence=min(data["hiring_mentions"] / 5, 1.0),
                    evidence_count=data["hiring_mentions"],
                    effectiveness_score=0.0,
                    category="timing",
                    applicable_to=[program],
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
                insights.append(insight)

        self._insights.extend(insights)
        return insights

    def _analyze_channel_patterns(self, episodes: List[Memory]) -> Dict[str, Dict[str, Any]]:
        """Analyze outreach channel patterns from episodes."""
        channels: Dict[str, Dict[str, Any]] = {}
        channel_keywords = {
            "email": ["email", "e-mail", "emailed", "sent email"],
            "phone": ["called", "phone", "call", "rang"],
            "linkedin": ["linkedin", "linked in", "connection request"],
            "meeting": ["meeting", "met with", "conference", "briefing"],
        }

        for ep in episodes:
            content_lower = ep.content.lower()
            for channel, keywords in channel_keywords.items():
                if any(kw in content_lower for kw in keywords):
                    if channel not in channels:
                        channels[channel] = {"count": 0, "success": 0, "programs": []}
                    channels[channel]["count"] += 1

                    # Check for positive outcome signals
                    if any(w in content_lower for w in [
                        "responded", "replied", "accepted", "agreed",
                        "interested", "positive", "scheduled",
                    ]):
                        channels[channel]["success"] += 1

                    for p in ep.programs:
                        if p not in channels[channel]["programs"]:
                            channels[channel]["programs"].append(p)

        return channels

    def _analyze_entity_frequency(self, episodes: List[Memory]) -> Dict[str, int]:
        """Count entity mentions across episodes."""
        freq: Dict[str, int] = {}
        for ep in episodes:
            seen = set()
            for entity in ep.entities + ep.programs + ep.contacts:
                key = entity.lower()
                if key not in seen:
                    freq[key] = freq.get(key, 0) + 1
                    seen.add(key)
        return freq

    def _analyze_program_mentions(self, episodes: List[Memory]) -> Dict[str, Dict[str, int]]:
        """Analyze program mentions and hiring signals."""
        programs: Dict[str, Dict[str, int]] = {}
        hiring_keywords = [
            "hiring", "position", "vacancy", "staffing", "recruiting",
            "headcount", "opening", "job posting",
        ]

        for ep in episodes:
            for prog in ep.programs:
                if prog not in programs:
                    programs[prog] = {"total_mentions": 0, "hiring_mentions": 0}
                programs[prog]["total_mentions"] += 1

                if any(kw in ep.content.lower() for kw in hiring_keywords):
                    programs[prog]["hiring_mentions"] += 1

        return programs

    def _find_semantic_by_entity(self, entity: str) -> Optional[Memory]:
        """Find existing semantic memory for an entity."""
        entity_lower = entity.lower()
        for mem in self._semantic.values():
            for e in mem.entities:
                if e.lower() == entity_lower:
                    return mem
        return None

    # -----------------------------------------
    # FORGET
    # -----------------------------------------

    async def forget(self, decay_factor: float = 0.95, removal_threshold: float = 0.05) -> ForgetReport:
        """Intelligent forgetting with importance decay."""
        now = datetime.now(timezone.utc)
        scanned = 0
        decayed = 0
        removed = 0
        preserved = 0

        remove_ids: List[str] = []

        for store_type in [MemoryType.EPISODIC.value, MemoryType.SEMANTIC.value, MemoryType.PROCEDURAL.value]:
            store = self._store_for(store_type)
            for mem_id, mem in store.items():
                scanned += 1

                # Never forget critical or human-verified memories
                if mem.importance >= 0.9 or mem.metadata.get("human_verified"):
                    preserved += 1
                    continue

                # Never forget procedural insights
                if store_type == MemoryType.PROCEDURAL.value:
                    preserved += 1
                    continue

                # Never forget high-confidence semantic facts
                if store_type == MemoryType.SEMANTIC.value and mem.confidence >= 0.9:
                    preserved += 1
                    continue

                # Apply decay
                mem.importance = round(mem.importance * decay_factor, 4)
                decayed += 1

                # Remove if below threshold
                if mem.importance < removal_threshold:
                    remove_ids.append((store_type, mem_id))
                    removed += 1
                    decayed -= 1  # don't double count

        # Remove marked memories
        for store_type, mem_id in remove_ids:
            store = self._store_for(store_type)
            store.pop(mem_id, None)

        report = ForgetReport(
            memories_scanned=scanned,
            memories_decayed=decayed,
            memories_removed=removed,
            memories_preserved=preserved,
            timestamp=now.isoformat(),
        )
        self._forget_history.append(report)
        return report

    # -----------------------------------------
    # SEARCH & QUERY
    # -----------------------------------------

    async def search(self, query: str, limit: int = 20) -> List[MemoryResult]:
        """Full-text search across all memory tiers."""
        return await self.recall(query, limit=limit, min_score=0.0)

    async def get_entity_memories(self, entity_id: str) -> List[MemoryResult]:
        """Get all memories related to a specific entity."""
        entity_lower = entity_id.lower()
        results: List[MemoryResult] = []

        for store_type in [MemoryType.EPISODIC.value, MemoryType.SEMANTIC.value, MemoryType.PROCEDURAL.value]:
            store = self._store_for(store_type)
            for mem in store.values():
                all_entities = [e.lower() for e in mem.entities + mem.programs + mem.contacts]
                if entity_lower in all_entities:
                    results.append(MemoryResult(
                        memory=mem,
                        relevance_score=1.0,
                        recency_score=_recency_score(mem),
                        importance_score=mem.importance,
                        combined_score=round((1.0 + _recency_score(mem) + mem.importance) / 3, 4),
                    ))

        results.sort(key=lambda r: r.combined_score, reverse=True)
        return results

    # -----------------------------------------
    # STATISTICS
    # -----------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics by tier."""
        def tier_stats(store: Dict[str, Memory]) -> Dict[str, Any]:
            if not store:
                return {"count": 0, "avg_importance": 0, "avg_confidence": 0}
            memories = list(store.values())
            return {
                "count": len(memories),
                "avg_importance": round(
                    sum(m.importance for m in memories) / len(memories), 4,
                ),
                "avg_confidence": round(
                    sum(m.confidence for m in memories) / len(memories), 4,
                ),
            }

        return {
            "episodic": tier_stats(self._episodic),
            "semantic": tier_stats(self._semantic),
            "procedural": tier_stats(self._procedural),
            "total_memories": (
                len(self._episodic) + len(self._semantic) + len(self._procedural)
            ),
            "procedural_insights": len(self._insights),
            "consolidation_runs": len(self._consolidation_history),
            "forget_runs": len(self._forget_history),
        }

    def get_recent_episodic(self, limit: int = 20) -> List[Memory]:
        """Get most recent episodic memories."""
        episodes = sorted(
            self._episodic.values(),
            key=lambda m: m.created_at or "",
            reverse=True,
        )
        return episodes[:limit]

    def get_semantic_facts(self, limit: int = 50) -> List[Memory]:
        """Get highest-confidence semantic facts."""
        facts = sorted(
            self._semantic.values(),
            key=lambda m: m.confidence,
            reverse=True,
        )
        return facts[:limit]

    def get_procedural_insights(self) -> List[ProceduralInsight]:
        """Get all procedural insights."""
        return list(self._insights)


# =========================================
# SINGLETON
# =========================================

_cortex: Optional[MemoryCortex] = None


def get_memory_cortex() -> MemoryCortex:
    global _cortex
    if _cortex is None:
        _cortex = MemoryCortex()
    return _cortex
