"""Phase 33A — Smart Autocomplete

Typeahead suggestions powered by platform knowledge. Sources suggestions
from entity names, common query patterns, recent searches, and platform
concepts. Supports fuzzy prefix matching.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class Suggestion:
    text: str
    category: str  # "entity", "query", "concept", "recent"
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# =========================================
# STATIC SUGGESTION SOURCES
# =========================================

# Common query starters → completions
_QUERY_TEMPLATES: Dict[str, List[str]] = {
    "show me": [
        "jobs in San Diego",
        "PACAF contacts",
        "pipeline forecast",
        "top opportunities",
        "Tier 1 contacts at Leidos",
        "TS/SCI positions this week",
    ],
    "who is": [
        "the Langley site lead",
        "our best contact at GDIT",
        "the PACAF program manager",
        "hiring at Leidos",
    ],
    "who are": [
        "the decision makers for DCGS",
        "our Tier 1 contacts",
        "the GDIT program managers",
        "key contacts at Northrop Grumman",
    ],
    "find": [
        "Tier 1 contacts at Leidos",
        "TS/SCI jobs at Langley",
        "DCGS analyst positions",
        "San Diego job openings",
        "GDIT program managers",
    ],
    "what": [
        "programs does GDIT run?",
        "is our pipeline worth?",
        "happened today?",
        "jobs are open in San Diego?",
        "is the win probability?",
    ],
    "compare": [
        "GDIT vs Leidos hiring",
        "San Diego vs Langley job volumes",
        "Q3 vs Q4 pipeline",
        "DCGS vs NGEN opportunities",
    ],
    "forecast": [
        "hiring for DCGS",
        "demand for analysts",
        "budget cycle next quarter",
        "program ramp signals",
    ],
    "generate": [
        "outreach email for the PM",
        "call script for DCGS contact",
        "meeting prep for Leidos visit",
        "campaign for Wright-Patt",
    ],
    "explain": [
        "the win probability score",
        "why PACAF is scored critical",
        "the composite scoring model",
        "the pipeline conversion rate",
    ],
}

# Known entities for direct matching
_KNOWN_COMPANIES = [
    "Leidos", "GDIT", "Booz Allen", "Northrop Grumman", "Raytheon",
    "Lockheed Martin", "BAE Systems", "SAIC", "CACI", "ManTech",
    "L3Harris", "General Dynamics", "Parsons",
]

_KNOWN_PROGRAMS = [
    "AF DCGS", "PACAF", "GBSD", "NGEN", "F-35", "Sentinel",
    "JADC2", "ABMS", "Navy ISR", "DCGS-N",
]

_KNOWN_LOCATIONS = [
    "San Diego", "Langley", "Fort Meade", "Colorado Springs",
    "Hickam AFB", "Beale AFB", "Ramstein", "Wright-Patterson",
    "San Antonio", "Huntsville", "Tampa", "Norfolk",
]

_PLATFORM_CONCEPTS = [
    "pipeline", "win probability", "forecast", "campaign",
    "outreach", "recompete", "budget cycle", "ramp signal",
    "composite score", "hiring trend", "daily digest",
]


class SmartAutocomplete:
    """Typeahead suggestions powered by platform knowledge."""

    def __init__(self):
        self._index: List[Suggestion] = []
        self._recent_queries: List[str] = []
        self._custom_entities: Dict[str, List[str]] = {}
        self._index_built = False

    async def suggest(
        self,
        partial_query: str,
        context: Optional[Dict[str, Any]] = None,
        limit: int = 8,
    ) -> List[Suggestion]:
        """Suggest completions as user types."""
        if not self._index_built:
            await self.build_suggestion_index()

        partial = partial_query.strip().lower()
        if not partial:
            return self._default_suggestions(limit)

        suggestions: List[Suggestion] = []

        # 1. Template matching (highest priority)
        template_suggestions = self._match_templates(partial)
        suggestions.extend(template_suggestions)

        # 2. Entity matching
        entity_suggestions = self._match_entities(partial)
        suggestions.extend(entity_suggestions)

        # 3. Recent queries matching
        recent_suggestions = self._match_recent(partial)
        suggestions.extend(recent_suggestions)

        # 4. Index matching
        index_suggestions = self._match_index(partial)
        suggestions.extend(index_suggestions)

        # De-duplicate by text
        seen = set()
        unique = []
        for s in suggestions:
            key = s.text.lower()
            if key not in seen:
                seen.add(key)
                unique.append(s)

        # Sort by score descending
        unique.sort(key=lambda x: x.score, reverse=True)

        return unique[:limit]

    async def build_suggestion_index(self) -> int:
        """Build/refresh autocomplete index from all platform entities."""
        self._index.clear()

        # Add companies
        for company in _KNOWN_COMPANIES:
            self._index.append(Suggestion(
                text=company,
                category="entity",
                score=0.8,
                metadata={"type": "company"},
            ))

        # Add programs
        for program in _KNOWN_PROGRAMS:
            self._index.append(Suggestion(
                text=program,
                category="entity",
                score=0.8,
                metadata={"type": "program"},
            ))

        # Add locations
        for loc in _KNOWN_LOCATIONS:
            self._index.append(Suggestion(
                text=loc,
                category="entity",
                score=0.7,
                metadata={"type": "location"},
            ))

        # Add concepts
        for concept in _PLATFORM_CONCEPTS:
            self._index.append(Suggestion(
                text=concept,
                category="concept",
                score=0.6,
                metadata={"type": "concept"},
            ))

        # Add custom entities
        for category, entities in self._custom_entities.items():
            for entity in entities:
                self._index.append(Suggestion(
                    text=entity,
                    category="entity",
                    score=0.7,
                    metadata={"type": category},
                ))

        self._index_built = True
        logger.info(f"Autocomplete index built with {len(self._index)} entries")
        return len(self._index)

    def add_recent_query(self, query: str) -> None:
        """Track recent queries for suggestion improvement."""
        self._recent_queries.insert(0, query)
        self._recent_queries = self._recent_queries[:100]  # Keep last 100

    def add_custom_entities(self, category: str, entities: List[str]) -> None:
        """Add custom entities to the suggestion index."""
        self._custom_entities[category] = entities
        self._index_built = False  # Force rebuild

    # =========================================
    # MATCHING HELPERS
    # =========================================

    def _match_templates(self, partial: str) -> List[Suggestion]:
        """Match against query templates."""
        suggestions = []
        for starter, completions in _QUERY_TEMPLATES.items():
            if partial.startswith(starter) or starter.startswith(partial):
                remainder = partial[len(starter):].strip() if partial.startswith(starter) else ""
                for completion in completions:
                    if not remainder or remainder in completion.lower():
                        full = f"{starter} {completion}" if partial.startswith(starter) else f"{starter} {completion}"
                        suggestions.append(Suggestion(
                            text=full,
                            category="query",
                            score=0.9,
                            metadata={"template": starter},
                        ))
        return suggestions

    def _match_entities(self, partial: str) -> List[Suggestion]:
        """Match against known entities."""
        suggestions = []
        words = partial.split()
        last_word = words[-1] if words else partial

        all_entities = _KNOWN_COMPANIES + _KNOWN_PROGRAMS + _KNOWN_LOCATIONS
        for entity in all_entities:
            if last_word and entity.lower().startswith(last_word.lower()):
                # Complete the current entity
                prefix = " ".join(words[:-1])
                full = f"{prefix} {entity}".strip() if prefix else entity
                suggestions.append(Suggestion(
                    text=full,
                    category="entity",
                    score=0.85,
                    metadata={"entity": entity},
                ))
        return suggestions

    def _match_recent(self, partial: str) -> List[Suggestion]:
        """Match against recent queries."""
        suggestions = []
        for query in self._recent_queries[:20]:
            if query.lower().startswith(partial) and query.lower() != partial:
                suggestions.append(Suggestion(
                    text=query,
                    category="recent",
                    score=0.7,
                    metadata={"source": "recent"},
                ))
        return suggestions

    def _match_index(self, partial: str) -> List[Suggestion]:
        """Match against the full index."""
        suggestions = []
        for item in self._index:
            if partial in item.text.lower():
                suggestions.append(Suggestion(
                    text=item.text,
                    category=item.category,
                    score=item.score * 0.8,  # Slightly lower for index matches
                    metadata=item.metadata,
                ))
        return suggestions

    def _default_suggestions(self, limit: int) -> List[Suggestion]:
        """Default suggestions when no input."""
        defaults = [
            Suggestion(text="Show me today's digest", category="query", score=0.9),
            Suggestion(text="Find Tier 1 contacts at Leidos", category="query", score=0.85),
            Suggestion(text="What's our pipeline worth?", category="query", score=0.85),
            Suggestion(text="Show TS/SCI jobs in San Diego", category="query", score=0.8),
            Suggestion(text="Forecast hiring for DCGS", category="query", score=0.8),
            Suggestion(text="Compare GDIT vs Leidos", category="query", score=0.75),
            Suggestion(text="Who are the PACAF decision makers?", category="query", score=0.75),
            Suggestion(text="Generate outreach email", category="query", score=0.7),
        ]
        # Mix in recent queries
        for q in self._recent_queries[:3]:
            defaults.append(Suggestion(text=q, category="recent", score=0.8))

        defaults.sort(key=lambda x: x.score, reverse=True)
        return defaults[:limit]
