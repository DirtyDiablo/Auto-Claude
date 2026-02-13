"""Phase 39A — Knowledge Compiler

Compile scattered intelligence (notes, emails, call transcripts) into
structured facts for the temporal knowledge graph.
"""

import logging
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.knowledge.temporal_kg import (
    EdgeType,
    extract_entities_simple,
    extract_relationships_simple,
)

logger = logging.getLogger(__name__)


# =========================================
# ENUMS & DATA CLASSES
# =========================================

class FactType(str, Enum):
    RELATIONSHIP = "relationship"
    ATTRIBUTE = "attribute"
    EVENT = "event"
    SENTIMENT = "sentiment"
    NUMERICAL = "numerical"
    ACTION_ITEM = "action_item"


@dataclass
class EpisodeSource:
    """Source metadata for an episode."""
    source_type: str = "conversation_note"
    author: str = ""
    date: str = ""
    subject: str = ""
    contact_name: str = ""
    company: str = ""


@dataclass
class ExtractedFact:
    """A structured fact extracted from unstructured text."""
    id: str = ""
    fact_type: str = FactType.RELATIONSHIP.value
    subject: str = ""
    predicate: str = ""
    object: str = ""
    confidence: float = 0.85
    temporal_marker: str = ""  # "Q2", "last month", "since March"
    source_text: str = ""  # The original text snippet
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompilationReport:
    """Result of compiling one or more texts."""
    total_texts: int = 0
    total_facts: int = 0
    fact_types: Dict[str, int] = field(default_factory=dict)
    entities_found: int = 0
    relationships_found: int = 0
    sentiments_found: int = 0
    numerical_data: int = 0
    action_items: int = 0
    deduplicated: int = 0
    facts: List[ExtractedFact] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


# =========================================
# EXTRACTION PATTERNS
# =========================================

# Temporal markers
TEMPORAL_PATTERNS = [
    (re.compile(r'\b(Q[1-4])\b', re.IGNORECASE), "quarter"),
    (re.compile(r'\b(next|last|this)\s+(week|month|quarter|year)\b', re.IGNORECASE), "relative"),
    (re.compile(r'\b(since|from|starting|beginning)\s+(\w+)\b', re.IGNORECASE), "start"),
    (re.compile(r'\b(until|through|ending|by)\s+(\w+)\b', re.IGNORECASE), "end"),
    (re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s*\d{0,4}\b', re.IGNORECASE), "month"),
    (re.compile(r'\b(20\d{2})\b'), "year"),
]

# Numerical data patterns
NUMBER_PATTERNS = [
    (re.compile(r'\$[\d,]+(?:\.\d+)?(?:\s*[MBKmbk](?:illion)?)?'), "currency"),
    (re.compile(r'\b(\d+)\s+(engineer|analyst|developer|people|staff|employee|contractor|position|role|vacancy|opening)s?\b', re.IGNORECASE), "headcount"),
    (re.compile(r'\b(team|group|department)\s+of\s+(\d+)\b', re.IGNORECASE), "team_size"),
]

# Sentiment/pain point patterns
PAIN_PATTERNS = [
    re.compile(r'\b(stretched thin|overwhelmed|understaffed|behind schedule|overworked)\b', re.IGNORECASE),
    re.compile(r'\b(frustrated|concerned|worried|struggling|difficulty)\b', re.IGNORECASE),
    re.compile(r'\b(turnover|attrition|losing people|people leaving|resignations)\b', re.IGNORECASE),
    re.compile(r'\b(budget cuts?|funding issues?|resource constraints?)\b', re.IGNORECASE),
]

# Action item patterns
ACTION_PATTERNS = [
    re.compile(r'\b(follow up|schedule|send|provide|share|call back|set up|arrange)\b', re.IGNORECASE),
    re.compile(r'\b(action item|todo|next step|need to|should|must|will)\b', re.IGNORECASE),
]

# Hiring/vacancy patterns
HIRING_PATTERNS = [
    re.compile(r'\b(hiring|looking for|need|seeking|recruiting|open position|vacancy|backfill)\b', re.IGNORECASE),
    re.compile(r'\b(\d+)\s+(?:new\s+)?(?:open\s+)?(?:position|role|opening|req|requisition)s?\b', re.IGNORECASE),
]

# Departure patterns
DEPARTURE_PATTERNS = [
    re.compile(r'\b(\w+)\s+(?:left|departed|resigned|retired|moved to|transferred)\b', re.IGNORECASE),
    re.compile(r'\bsince\s+(\w+)\s+left\b', re.IGNORECASE),
]


# =========================================
# KNOWLEDGE COMPILER
# =========================================

class KnowledgeCompiler:
    """Extract structured facts from unstructured intelligence text."""

    def __init__(self):
        self._compilation_history: List[CompilationReport] = []

    def compile(
        self, text: str, source: Optional[EpisodeSource] = None,
    ) -> List[ExtractedFact]:
        """Extract structured facts from unstructured text."""
        if not text or not text.strip():
            return []

        facts: List[ExtractedFact] = []

        # 1. Extract entities
        entities = extract_entities_simple(text)

        # 2. Extract relationships
        relationships = extract_relationships_simple(text, entities)
        for rel in relationships:
            facts.append(ExtractedFact(
                id=uuid.uuid4().hex[:8],
                fact_type=FactType.RELATIONSHIP.value,
                subject=rel["subject"],
                predicate=rel["predicate"],
                object=rel["object"],
                confidence=0.85,
                source_text=text[:200],
            ))

        # 3. Extract temporal markers
        temporal_markers = self._extract_temporal(text)

        # 4. Extract numerical data
        numerical = self._extract_numerical(text)
        for num in numerical:
            facts.append(ExtractedFact(
                id=uuid.uuid4().hex[:8],
                fact_type=FactType.NUMERICAL.value,
                subject=num.get("context", ""),
                predicate=num["type"],
                object=num["value"],
                confidence=0.90,
                source_text=num.get("snippet", ""),
                metadata=num,
            ))

        # 5. Extract sentiments/pain points
        sentiments = self._extract_sentiments(text, entities)
        for sent in sentiments:
            facts.append(ExtractedFact(
                id=uuid.uuid4().hex[:8],
                fact_type=FactType.SENTIMENT.value,
                subject=sent.get("entity", ""),
                predicate=EdgeType.PAIN_POINT.value,
                object=sent["pain_point"],
                confidence=0.80,
                source_text=sent.get("snippet", ""),
            ))

        # 6. Extract hiring/vacancy info
        hiring = self._extract_hiring(text, entities)
        for h in hiring:
            facts.append(ExtractedFact(
                id=uuid.uuid4().hex[:8],
                fact_type=FactType.EVENT.value,
                subject=h.get("org", ""),
                predicate=EdgeType.HIRING.value,
                object=h.get("role", "open position"),
                confidence=0.85,
                source_text=h.get("snippet", ""),
                temporal_marker=h.get("temporal", ""),
                metadata=h,
            ))

        # 7. Extract action items
        action_items = self._extract_actions(text)
        for ai in action_items:
            facts.append(ExtractedFact(
                id=uuid.uuid4().hex[:8],
                fact_type=FactType.ACTION_ITEM.value,
                subject=source.author if source else "",
                predicate="ACTION",
                object=ai,
                confidence=0.75,
                source_text=ai,
            ))

        # 8. Extract departures
        departures = self._extract_departures(text)
        for dep in departures:
            facts.append(ExtractedFact(
                id=uuid.uuid4().hex[:8],
                fact_type=FactType.EVENT.value,
                subject=dep.get("person", ""),
                predicate="DEPARTED",
                object=dep.get("context", ""),
                confidence=0.80,
                source_text=dep.get("snippet", ""),
            ))

        # Apply temporal markers to facts
        if temporal_markers:
            for fact in facts:
                if not fact.temporal_marker:
                    fact.temporal_marker = temporal_markers[0] if temporal_markers else ""

        return facts

    def compile_batch(self, texts: List[str]) -> CompilationReport:
        """Batch compile multiple texts with deduplication."""
        import time
        start = time.time()

        all_facts: List[ExtractedFact] = []
        errors = []

        for i, text in enumerate(texts):
            try:
                facts = self.compile(text)
                all_facts.extend(facts)
            except Exception as e:
                errors.append(f"Text {i}: {e}")

        # Deduplicate facts
        unique_facts, dedup_count = self._deduplicate_facts(all_facts)

        # Count by type
        type_counts: Dict[str, int] = {}
        for f in unique_facts:
            type_counts[f.fact_type] = type_counts.get(f.fact_type, 0) + 1

        duration = time.time() - start

        report = CompilationReport(
            total_texts=len(texts),
            total_facts=len(unique_facts),
            fact_types=type_counts,
            entities_found=sum(1 for f in unique_facts if f.fact_type == FactType.RELATIONSHIP.value),
            relationships_found=type_counts.get(FactType.RELATIONSHIP.value, 0),
            sentiments_found=type_counts.get(FactType.SENTIMENT.value, 0),
            numerical_data=type_counts.get(FactType.NUMERICAL.value, 0),
            action_items=type_counts.get(FactType.ACTION_ITEM.value, 0),
            deduplicated=dedup_count,
            facts=unique_facts,
            errors=errors,
            duration_seconds=round(duration, 3),
        )
        self._compilation_history.append(report)
        return report

    def compile_from_notes(self, notes: List[Dict[str, Any]]) -> CompilationReport:
        """Process structured notes (e.g., from master_notes.csv rows)."""
        texts = []
        for note in notes:
            # Combine relevant fields into text
            parts = []
            if note.get("contact_name"):
                parts.append(f"Contact: {note['contact_name']}")
            if note.get("company"):
                parts.append(f"at {note['company']}")
            if note.get("subject"):
                parts.append(f"Subject: {note['subject']}")
            if note.get("notes") or note.get("content"):
                parts.append(note.get("notes", note.get("content", "")))
            texts.append(" ".join(parts))

        return self.compile_batch(texts)

    def get_history(self) -> List[CompilationReport]:
        return self._compilation_history

    # -----------------------------------------
    # Extraction helpers
    # -----------------------------------------

    def _extract_temporal(self, text: str) -> List[str]:
        """Extract temporal markers from text."""
        markers = []
        for pattern, marker_type in TEMPORAL_PATTERNS:
            for match in pattern.finditer(text):
                markers.append(match.group(0))
        return markers

    def _extract_numerical(self, text: str) -> List[Dict[str, Any]]:
        """Extract numerical data from text."""
        results = []
        for pattern, num_type in NUMBER_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30]
                results.append({
                    "type": num_type,
                    "value": match.group(0),
                    "snippet": snippet.strip(),
                    "context": snippet.strip(),
                })
        return results

    def _extract_sentiments(
        self, text: str, entities: List[Dict],
    ) -> List[Dict[str, Any]]:
        """Extract pain points and sentiments."""
        results = []
        for pattern in PAIN_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 50):match.end() + 50]
                # Associate with nearest person entity
                entity_name = ""
                for e in entities:
                    if e["type"] == "person" and e["name"].lower() in snippet.lower():
                        entity_name = e["name"]
                        break
                results.append({
                    "pain_point": match.group(0),
                    "entity": entity_name,
                    "snippet": snippet.strip(),
                })
        return results

    def _extract_hiring(
        self, text: str, entities: List[Dict],
    ) -> List[Dict[str, Any]]:
        """Extract hiring and vacancy information."""
        results = []
        for pattern in HIRING_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 40):match.end() + 40]
                org = ""
                for e in entities:
                    if e["type"] == "organization":
                        org = e["name"]
                        break
                results.append({
                    "org": org,
                    "role": match.group(0),
                    "snippet": snippet.strip(),
                })
        return results

    def _extract_actions(self, text: str) -> List[str]:
        """Extract action items from text."""
        actions = []
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            for pattern in ACTION_PATTERNS:
                if pattern.search(sentence):
                    clean = sentence.strip()
                    if len(clean) > 10:
                        actions.append(clean)
                    break
        return actions[:5]  # Limit to 5 action items

    def _extract_departures(self, text: str) -> List[Dict[str, Any]]:
        """Extract departure/resignation information."""
        results = []
        for pattern in DEPARTURE_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30]
                results.append({
                    "person": match.group(1) if match.lastindex else "",
                    "context": match.group(0),
                    "snippet": snippet.strip(),
                })
        return results

    def _deduplicate_facts(
        self, facts: List[ExtractedFact],
    ) -> Tuple[List[ExtractedFact], int]:
        """Remove duplicate facts based on subject+predicate+object."""
        seen = set()
        unique = []
        dups = 0
        for fact in facts:
            key = f"{fact.subject.lower()}|{fact.predicate}|{fact.object.lower()}"
            if key not in seen:
                seen.add(key)
                unique.append(fact)
            else:
                dups += 1
        return unique, dups


# =========================================
# SINGLETON
# =========================================

_compiler: Optional[KnowledgeCompiler] = None


def get_knowledge_compiler() -> KnowledgeCompiler:
    global _compiler
    if _compiler is None:
        _compiler = KnowledgeCompiler()
    return _compiler
