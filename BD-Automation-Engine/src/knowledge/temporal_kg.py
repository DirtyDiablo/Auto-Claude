"""Phase 39A — Temporal Knowledge Graph Engine

Graphiti-inspired temporal knowledge graph where every fact has a time dimension.
Supports episode ingestion, temporal queries, entity timelines, change detection,
and contradiction detection.
"""

import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# ENUMS
# =========================================


class EpisodeType(str, Enum):
    CONVERSATION_NOTE = "conversation_note"
    SCRAPE_RESULT = "scrape_result"
    FEDERAL_DOCUMENT = "federal_document"
    CONTACT_IMPORT = "contact_import"
    HUMINT_REPORT = "humint_report"
    EMAIL_THREAD = "email_thread"


class EntityType(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    PROGRAM = "program"
    LOCATION = "location"
    ROLE = "role"
    SKILL = "skill"
    CONTRACT = "contract"


class EdgeType(str, Enum):
    WORKS_AT = "WORKS_AT"
    MANAGES = "MANAGES"
    ACTS_AS = "ACTS_AS"
    PRIME_ON = "PRIME_ON"
    SUB_ON = "SUB_ON"
    LOCATED_AT = "LOCATED_AT"
    REPORTS_TO = "REPORTS_TO"
    HIRING = "HIRING"
    HAS_VACANCY = "HAS_VACANCY"
    KNOWS = "KNOWS"
    PAIN_POINT = "PAIN_POINT"
    BUDGET_APPROVED = "BUDGET_APPROVED"
    AWARDED_TO = "AWARDED_TO"
    TEAMING_WITH = "TEAMING_WITH"
    COMPETES_WITH = "COMPETES_WITH"


class ChangeType(str, Enum):
    ADDED = "added"
    EXPIRED = "expired"
    MODIFIED = "modified"


class ContradictionType(str, Enum):
    DUAL_EMPLOYMENT = "dual_employment"
    CONFLICTING_TITLE = "conflicting_title"
    EXPIRED_CONTRACT_ACTIVE = "expired_contract_active"
    LOCATION_CONFLICT = "location_conflict"


# =========================================
# DATA CLASSES
# =========================================


@dataclass
class Episode:
    """A unit of information ingested into the knowledge graph."""

    id: str = ""
    episode_type: str = EpisodeType.CONVERSATION_NOTE.value
    content: str = ""
    source: str = ""
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    actor: str = ""  # Who created this (user, system, scraper)


@dataclass
class Entity:
    """A resolved real-world entity in the graph."""

    id: str
    entity_type: str
    name: str
    aliases: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    first_seen: str = ""
    last_seen: str = ""
    confidence: float = 1.0
    source_episodes: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None


@dataclass
class TemporalFact:
    """A timestamped relationship between two entities."""

    id: str
    subject_id: str
    predicate: str  # EdgeType value
    object_id: str
    valid_from: str = ""
    valid_to: str = ""  # Empty = still active
    confidence: float = 1.0
    source_episode_id: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


@dataclass
class EpisodeResult:
    """Result of processing an episode."""

    episode_id: str
    entities_discovered: int = 0
    entities_resolved: int = 0
    facts_added: int = 0
    facts_expired: int = 0
    contradictions_found: int = 0
    entities: List[Entity] = field(default_factory=list)
    facts: List[TemporalFact] = field(default_factory=list)
    processing_time_ms: float = 0.0


@dataclass
class TimelineEntry:
    """A single entry in an entity's timeline."""

    timestamp: str
    event_type: str  # added, expired, modified
    fact: TemporalFact
    description: str = ""


@dataclass
class EntityTimeline:
    """Full history of an entity."""

    entity_id: str
    entity_name: str
    entity_type: str
    first_seen: str = ""
    last_seen: str = ""
    entries: List[TimelineEntry] = field(default_factory=list)
    total_facts: int = 0
    active_facts: int = 0


@dataclass
class ChangeEvent:
    """A change detected for an entity."""

    entity_id: str
    change_type: str  # added, expired, modified
    fact: TemporalFact
    detected_at: str = ""
    description: str = ""


@dataclass
class Contradiction:
    """A logical contradiction in the graph."""

    id: str
    contradiction_type: str
    entity_id: str
    entity_name: str
    fact_a: TemporalFact
    fact_b: TemporalFact
    description: str = ""
    severity: str = "medium"
    detected_at: str = ""


# =========================================
# NER HELPERS (lightweight, no external deps)
# =========================================

# Simple patterns for entity extraction
PERSON_PATTERNS = [
    re.compile(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b"),  # "John Smith"
    re.compile(r"\b([A-Z]\. [A-Z][a-z]+)\b"),  # "J. Smith"
    re.compile(r"\b(Dr\.|Mr\.|Mrs\.|Ms\.) ([A-Z][a-z]+ [A-Z][a-z]+)\b"),
]

ORG_KEYWORDS = {
    "gdit",
    "general dynamics",
    "leidos",
    "booz allen",
    "saic",
    "northrop",
    "raytheon",
    "lockheed",
    "bae systems",
    "caci",
    "mantech",
    "peraton",
    "l3harris",
    "parsons",
    "jacobs",
    "kbr",
    "amentum",
}

PROGRAM_KEYWORDS = {
    "dcgs",
    "dcgs-a",
    "gbsd",
    "ngen",
    "deos",
    "ces",
    "jadc2",
    "abms",
    "odin",
    "titan",
    "maven",
    "jedi",
    "jwcc",
}

TITLE_KEYWORDS = {
    "ceo",
    "cto",
    "cfo",
    "vp",
    "vice president",
    "director",
    "manager",
    "lead",
    "engineer",
    "analyst",
    "architect",
    "pm",
    "program manager",
    "site lead",
    "team lead",
}


def extract_entities_simple(text: str) -> List[Dict[str, Any]]:
    """Lightweight entity extraction without external NER models."""
    entities = []
    text_lower = text.lower()

    # Extract person names
    for pattern in PERSON_PATTERNS:
        for match in pattern.finditer(text):
            name = match.group(0).strip()
            if len(name) > 3 and name.lower() not in ORG_KEYWORDS:
                entities.append(
                    {
                        "name": name,
                        "type": EntityType.PERSON.value,
                        "span": (match.start(), match.end()),
                    }
                )

    # Extract organizations
    for org in ORG_KEYWORDS:
        idx = text_lower.find(org)
        if idx >= 0:
            entities.append(
                {
                    "name": org.upper() if len(org) <= 4 else org.title(),
                    "type": EntityType.ORGANIZATION.value,
                    "span": (idx, idx + len(org)),
                }
            )

    # Extract programs
    for prog in PROGRAM_KEYWORDS:
        idx = text_lower.find(prog)
        if idx >= 0:
            entities.append(
                {
                    "name": prog.upper(),
                    "type": EntityType.PROGRAM.value,
                    "span": (idx, idx + len(prog)),
                }
            )

    # Deduplicate by name
    seen = set()
    unique = []
    for e in entities:
        key = e["name"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(e)

    return unique


def extract_relationships_simple(
    text: str,
    entities: List[Dict],
) -> List[Dict[str, Any]]:
    """Extract relationships between entities from text."""
    relationships = []
    text_lower = text.lower()

    entity_names = {e["name"].lower(): e for e in entities}

    # Pattern: "X [works/joined/is] at Y" → WORKS_AT
    works_at_verbs = ["at", "works at", "joined", "works for", "is at", "from"]
    for person in [e for e in entities if e["type"] == EntityType.PERSON.value]:
        for org in [e for e in entities if e["type"] == EntityType.ORGANIZATION.value]:
            pname = person["name"].lower()
            oname = org["name"].lower()
            if any(f"{pname} {v} {oname}" in text_lower for v in works_at_verbs):
                relationships.append(
                    {
                        "subject": person["name"],
                        "predicate": EdgeType.WORKS_AT.value,
                        "object": org["name"],
                    }
                )

    # Pattern: "X manages Y" or "X leads Y"
    manage_patterns = ["manages", "leads", "runs", "heads", "oversees"]
    for pattern in manage_patterns:
        if pattern in text_lower:
            for person in [e for e in entities if e["type"] == EntityType.PERSON.value]:
                if person["name"].lower() in text_lower.split(pattern)[0][-50:]:
                    for target in entities:
                        if target["name"] != person["name"]:
                            after = (
                                text_lower.split(pattern)[1][:50]
                                if pattern in text_lower
                                else ""
                            )
                            if target["name"].lower() in after:
                                relationships.append(
                                    {
                                        "subject": person["name"],
                                        "predicate": EdgeType.MANAGES.value,
                                        "object": target["name"],
                                    }
                                )

    # Pattern: "hiring X" → HIRING
    if "hiring" in text_lower or "looking for" in text_lower:
        for org in [e for e in entities if e["type"] == EntityType.ORGANIZATION.value]:
            relationships.append(
                {
                    "subject": org["name"],
                    "predicate": EdgeType.HIRING.value,
                    "object": "open_position",
                }
            )

    return relationships


# =========================================
# TEMPORAL KNOWLEDGE GRAPH
# =========================================


class TemporalKnowledgeGraph:
    """Knowledge graph where every fact has a time dimension."""

    def __init__(self):
        self._entities: Dict[str, Entity] = {}
        self._facts: Dict[str, TemporalFact] = {}
        self._episodes: Dict[str, Episode] = {}
        self._entity_name_index: Dict[str, str] = {}  # lowercase name → entity_id
        self._entity_facts: Dict[str, List[str]] = {}  # entity_id → [fact_ids]

    # -----------------------------------------
    # Data loading
    # -----------------------------------------

    def add_entity(self, entity: Entity) -> None:
        """Add an entity directly."""
        self._entities[entity.id] = entity
        self._entity_name_index[entity.name.lower()] = entity.id
        for alias in entity.aliases:
            self._entity_name_index[alias.lower()] = entity.id

    def add_fact(self, fact: TemporalFact) -> None:
        """Add a fact directly."""
        self._facts[fact.id] = fact
        for eid in (fact.subject_id, fact.object_id):
            if eid not in self._entity_facts:
                self._entity_facts[eid] = []
            self._entity_facts[eid].append(fact.id)

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self._entities.get(entity_id)

    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Get entity by name (case-insensitive)."""
        eid = self._entity_name_index.get(name.lower())
        if eid:
            return self._entities.get(eid)
        return None

    def get_fact(self, fact_id: str) -> Optional[TemporalFact]:
        """Get fact by ID."""
        return self._facts.get(fact_id)

    def get_all_entities(self) -> List[Entity]:
        """Get all entities."""
        return list(self._entities.values())

    def get_all_facts(self) -> List[TemporalFact]:
        """Get all facts."""
        return list(self._facts.values())

    # -----------------------------------------
    # Episode ingestion
    # -----------------------------------------

    def ingest_episode(self, episode: Episode) -> EpisodeResult:
        """Process a new piece of intelligence."""
        import time

        start = time.time()
        now = datetime.now(timezone.utc).isoformat()

        if not episode.id:
            episode.id = uuid.uuid4().hex[:12]
        if not episode.timestamp:
            episode.timestamp = now

        self._episodes[episode.id] = episode

        # 1. Extract entities
        raw_entities = extract_entities_simple(episode.content)

        # 2. Resolve against existing graph
        resolved_entities = []
        new_entity_count = 0
        resolved_count = 0

        for raw in raw_entities:
            existing = self.get_entity_by_name(raw["name"])
            if existing:
                # Update existing entity
                existing.last_seen = now
                if episode.id not in existing.source_episodes:
                    existing.source_episodes.append(episode.id)
                resolved_entities.append(existing)
                resolved_count += 1
            else:
                # Create new entity
                entity = Entity(
                    id=uuid.uuid4().hex[:10],
                    entity_type=raw["type"],
                    name=raw["name"],
                    first_seen=now,
                    last_seen=now,
                    source_episodes=[episode.id],
                )
                self.add_entity(entity)
                resolved_entities.append(entity)
                new_entity_count += 1

        # 3. Extract relationships
        raw_rels = extract_relationships_simple(episode.content, raw_entities)

        # 4. Create temporal facts
        new_facts = []
        for rel in raw_rels:
            subject = self.get_entity_by_name(rel["subject"])
            obj_entity = self.get_entity_by_name(rel["object"])

            if not subject:
                continue

            object_id = obj_entity.id if obj_entity else rel["object"]

            fact = TemporalFact(
                id=uuid.uuid4().hex[:10],
                subject_id=subject.id,
                predicate=rel["predicate"],
                object_id=object_id,
                valid_from=episode.timestamp,
                confidence=0.85,
                source_episode_id=episode.id,
                created_at=now,
            )
            self.add_fact(fact)
            new_facts.append(fact)

        elapsed = (time.time() - start) * 1000

        return EpisodeResult(
            episode_id=episode.id,
            entities_discovered=new_entity_count,
            entities_resolved=resolved_count,
            facts_added=len(new_facts),
            facts_expired=0,
            contradictions_found=0,
            entities=resolved_entities,
            facts=new_facts,
            processing_time_ms=round(elapsed, 2),
        )

    # -----------------------------------------
    # Temporal queries
    # -----------------------------------------

    def query_facts_at_time(
        self,
        timestamp: str,
        entity_id: Optional[str] = None,
        predicate: Optional[str] = None,
    ) -> List[TemporalFact]:
        """Get all facts valid at a specific point in time."""
        try:
            query_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return []

        results = []
        for fact in self._facts.values():
            # Filter by entity if specified
            if (
                entity_id
                and fact.subject_id != entity_id
                and fact.object_id != entity_id
            ):
                continue
            # Filter by predicate if specified
            if predicate and fact.predicate != predicate:
                continue

            # Check temporal validity
            if fact.valid_from:
                try:
                    valid_from = datetime.fromisoformat(
                        fact.valid_from.replace("Z", "+00:00")
                    )
                    if query_time < valid_from:
                        continue
                except (ValueError, TypeError):
                    pass

            if fact.valid_to:
                try:
                    valid_to = datetime.fromisoformat(
                        fact.valid_to.replace("Z", "+00:00")
                    )
                    if query_time > valid_to:
                        continue
                except (ValueError, TypeError):
                    pass

            results.append(fact)

        return results

    def get_active_facts(self, entity_id: Optional[str] = None) -> List[TemporalFact]:
        """Get all currently active facts (no valid_to set)."""
        results = []
        for fact in self._facts.values():
            if fact.valid_to:
                continue
            if (
                entity_id
                and fact.subject_id != entity_id
                and fact.object_id != entity_id
            ):
                continue
            results.append(fact)
        return results

    # -----------------------------------------
    # Entity timeline
    # -----------------------------------------

    def get_entity_timeline(self, entity_id: str) -> Optional[EntityTimeline]:
        """Get the full history of an entity."""
        entity = self._entities.get(entity_id)
        if not entity:
            return None

        fact_ids = self._entity_facts.get(entity_id, [])
        facts = [self._facts[fid] for fid in fact_ids if fid in self._facts]

        entries = []
        for fact in sorted(facts, key=lambda f: f.valid_from or f.created_at):
            # Added entry
            entries.append(
                TimelineEntry(
                    timestamp=fact.valid_from or fact.created_at,
                    event_type=ChangeType.ADDED.value,
                    fact=fact,
                    description=self._describe_fact(fact),
                )
            )
            # Expired entry
            if fact.valid_to:
                entries.append(
                    TimelineEntry(
                        timestamp=fact.valid_to,
                        event_type=ChangeType.EXPIRED.value,
                        fact=fact,
                        description=f"Expired: {self._describe_fact(fact)}",
                    )
                )

        entries.sort(key=lambda e: e.timestamp)
        active = [f for f in facts if not f.valid_to]

        return EntityTimeline(
            entity_id=entity_id,
            entity_name=entity.name,
            entity_type=entity.entity_type,
            first_seen=entity.first_seen,
            last_seen=entity.last_seen,
            entries=entries,
            total_facts=len(facts),
            active_facts=len(active),
        )

    # -----------------------------------------
    # Change detection
    # -----------------------------------------

    def detect_changes(self, entity_id: str, since: str) -> List[ChangeEvent]:
        """What changed for this entity since a given date."""
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return []

        changes = []
        fact_ids = self._entity_facts.get(entity_id, [])

        for fid in fact_ids:
            fact = self._facts.get(fid)
            if not fact:
                continue

            # New facts added since
            if fact.created_at:
                try:
                    created = datetime.fromisoformat(
                        fact.created_at.replace("Z", "+00:00")
                    )
                    if created > since_dt:
                        changes.append(
                            ChangeEvent(
                                entity_id=entity_id,
                                change_type=ChangeType.ADDED.value,
                                fact=fact,
                                detected_at=fact.created_at,
                                description=f"New: {self._describe_fact(fact)}",
                            )
                        )
                except (ValueError, TypeError):
                    pass

            # Facts expired since
            if fact.valid_to:
                try:
                    expired = datetime.fromisoformat(
                        fact.valid_to.replace("Z", "+00:00")
                    )
                    if expired > since_dt:
                        changes.append(
                            ChangeEvent(
                                entity_id=entity_id,
                                change_type=ChangeType.EXPIRED.value,
                                fact=fact,
                                detected_at=fact.valid_to,
                                description=f"Expired: {self._describe_fact(fact)}",
                            )
                        )
                except (ValueError, TypeError):
                    pass

        return sorted(changes, key=lambda c: c.detected_at)

    # -----------------------------------------
    # Expire a fact
    # -----------------------------------------

    def expire_fact(self, fact_id: str, valid_to: Optional[str] = None) -> bool:
        """Mark a fact as expired."""
        fact = self._facts.get(fact_id)
        if not fact:
            return False
        fact.valid_to = valid_to or datetime.now(timezone.utc).isoformat()
        return True

    # -----------------------------------------
    # Contradiction detection
    # -----------------------------------------

    def find_contradictions(self) -> List[Contradiction]:
        """Scan for logical contradictions in the graph."""
        contradictions = []
        now = datetime.now(timezone.utc).isoformat()

        # Check for dual employment (person WORKS_AT two orgs simultaneously)
        for entity in self._entities.values():
            if entity.entity_type != EntityType.PERSON.value:
                continue

            active_work = [
                f
                for f in self.get_active_facts(entity.id)
                if f.predicate == EdgeType.WORKS_AT.value and f.subject_id == entity.id
            ]
            if len(active_work) > 1:
                for i in range(len(active_work)):
                    for j in range(i + 1, len(active_work)):
                        if active_work[i].object_id != active_work[j].object_id:
                            contradictions.append(
                                Contradiction(
                                    id=uuid.uuid4().hex[:8],
                                    contradiction_type=ContradictionType.DUAL_EMPLOYMENT.value,
                                    entity_id=entity.id,
                                    entity_name=entity.name,
                                    fact_a=active_work[i],
                                    fact_b=active_work[j],
                                    description=f"{entity.name} works at two orgs simultaneously",
                                    severity="high",
                                    detected_at=now,
                                )
                            )

            # Check conflicting titles at same company
            active_roles = [
                f
                for f in self.get_active_facts(entity.id)
                if f.predicate == EdgeType.ACTS_AS.value and f.subject_id == entity.id
            ]
            if len(active_roles) > 1:
                for i in range(len(active_roles)):
                    for j in range(i + 1, len(active_roles)):
                        contradictions.append(
                            Contradiction(
                                id=uuid.uuid4().hex[:8],
                                contradiction_type=ContradictionType.CONFLICTING_TITLE.value,
                                entity_id=entity.id,
                                entity_name=entity.name,
                                fact_a=active_roles[i],
                                fact_b=active_roles[j],
                                description=f"{entity.name} has conflicting active roles",
                                severity="medium",
                                detected_at=now,
                            )
                        )

        return contradictions

    # -----------------------------------------
    # Search
    # -----------------------------------------

    def search_entities(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[Entity]:
        """Search entities by name (substring match)."""
        query_lower = query.lower()
        results = []
        for entity in self._entities.values():
            if entity_type and entity.entity_type != entity_type:
                continue
            if query_lower in entity.name.lower():
                results.append(entity)
            elif any(query_lower in a.lower() for a in entity.aliases):
                results.append(entity)
        return results[:limit]

    def search_facts(
        self,
        predicate: Optional[str] = None,
        subject_id: Optional[str] = None,
        object_id: Optional[str] = None,
        active_only: bool = False,
    ) -> List[TemporalFact]:
        """Search facts with filters."""
        results = []
        for fact in self._facts.values():
            if predicate and fact.predicate != predicate:
                continue
            if subject_id and fact.subject_id != subject_id:
                continue
            if object_id and fact.object_id != object_id:
                continue
            if active_only and fact.valid_to:
                continue
            results.append(fact)
        return results

    # -----------------------------------------
    # Stats
    # -----------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        type_counts: Dict[str, int] = {}
        for e in self._entities.values():
            type_counts[e.entity_type] = type_counts.get(e.entity_type, 0) + 1

        predicate_counts: Dict[str, int] = {}
        for f in self._facts.values():
            predicate_counts[f.predicate] = predicate_counts.get(f.predicate, 0) + 1

        active_facts = len([f for f in self._facts.values() if not f.valid_to])
        expired_facts = len([f for f in self._facts.values() if f.valid_to])

        return {
            "total_entities": len(self._entities),
            "total_facts": len(self._facts),
            "total_episodes": len(self._episodes),
            "active_facts": active_facts,
            "expired_facts": expired_facts,
            "entity_types": type_counts,
            "predicate_counts": predicate_counts,
        }

    # -----------------------------------------
    # Internal helpers
    # -----------------------------------------

    def _describe_fact(self, fact: TemporalFact) -> str:
        """Create human-readable description of a fact."""
        subject = self._entities.get(fact.subject_id)
        obj = self._entities.get(fact.object_id)
        s_name = subject.name if subject else fact.subject_id
        o_name = obj.name if obj else fact.object_id
        return f"{s_name} {fact.predicate} {o_name}"


# =========================================
# SINGLETON
# =========================================

_kg: Optional[TemporalKnowledgeGraph] = None


def get_temporal_kg() -> TemporalKnowledgeGraph:
    global _kg
    if _kg is None:
        _kg = TemporalKnowledgeGraph()
    return _kg
