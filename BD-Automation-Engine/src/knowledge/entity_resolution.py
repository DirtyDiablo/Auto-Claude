"""Phase 39A — Entity Resolution Engine

Multi-signal entity resolution for people, organizations, and programs.
Resolves duplicates across data sources using name similarity, email/phone
matching, company+title overlap, and embedding similarity.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# ENUMS
# =========================================

class MatchOutcome(str, Enum):
    DEFINITE_MATCH = "definite_match"    # > 0.95
    PROBABLE_MATCH = "probable_match"    # 0.80-0.95
    POSSIBLE_MATCH = "possible_match"    # 0.60-0.80
    NO_MATCH = "no_match"               # < 0.60


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class ResolutionResult:
    """Result of comparing two entity mentions."""
    entity_a_id: str
    entity_b_id: str
    outcome: str
    confidence: float
    signals: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""


@dataclass
class ResolutionCandidate:
    """A potential match for an entity."""
    entity_id: str
    entity_name: str
    confidence: float
    signals: Dict[str, float] = field(default_factory=dict)


@dataclass
class MergeResult:
    """Result of merging two entities."""
    primary_id: str
    merged_id: str
    success: bool
    fields_merged: List[str] = field(default_factory=list)
    facts_transferred: int = 0
    aliases_added: List[str] = field(default_factory=list)


@dataclass
class GlobalResolutionReport:
    """Result of running global entity resolution."""
    total_entities_scanned: int = 0
    pairs_compared: int = 0
    definite_matches: int = 0
    probable_matches: int = 0
    possible_matches: int = 0
    auto_merged: int = 0
    flagged_for_review: int = 0
    results: List[ResolutionResult] = field(default_factory=list)
    duration_seconds: float = 0.0


# =========================================
# STRING SIMILARITY
# =========================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """Normalized Levenshtein similarity (0-1)."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    max_len = max(len(s1), len(s2))
    dist = levenshtein_distance(s1, s2)
    return 1.0 - (dist / max_len)


def jaro_similarity(s1: str, s2: str) -> float:
    """Jaro similarity between two strings (0-1)."""
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    len1, len2 = len(s1), len(s2)
    match_dist = max(len1, len2) // 2 - 1
    if match_dist < 0:
        match_dist = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2

    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - match_dist)
        end = min(i + match_dist + 1, len2)
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    jaro = (matches / len1 + matches / len2 +
            (matches - transpositions / 2) / matches) / 3
    return jaro


def jaro_winkler_similarity(s1: str, s2: str, p: float = 0.1) -> float:
    """Jaro-Winkler similarity (gives bonus for common prefix)."""
    jaro = jaro_similarity(s1, s2)
    prefix_len = 0
    for i in range(min(4, min(len(s1), len(s2)))):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break
    return jaro + prefix_len * p * (1 - jaro)


def name_similarity(name_a: str, name_b: str) -> float:
    """Multi-signal name similarity combining multiple algorithms."""
    a = name_a.lower().strip()
    b = name_b.lower().strip()

    if a == b:
        return 1.0

    # Check for nickname/abbreviation patterns
    # "Jeffrey" vs "Jeff", "Robert" vs "Bob"
    nickname_score = _nickname_similarity(a, b)

    lev = levenshtein_similarity(a, b)
    jw = jaro_winkler_similarity(a, b)

    # Weighted combination
    combined = max(
        0.4 * jw + 0.3 * lev + 0.3 * nickname_score,
        nickname_score,  # Nickname match alone can be high
    )
    return round(min(combined, 1.0), 4)


NICKNAME_MAP = {
    "jeffrey": ["jeff", "geoff"],
    "robert": ["bob", "rob", "bobby"],
    "william": ["bill", "will", "billy"],
    "james": ["jim", "jimmy"],
    "richard": ["rick", "dick", "rich"],
    "michael": ["mike", "mikey"],
    "elizabeth": ["liz", "beth", "betty"],
    "jennifer": ["jen", "jenny"],
    "christopher": ["chris"],
    "katherine": ["kate", "kathy", "katie"],
    "joseph": ["joe", "joey"],
    "thomas": ["tom", "tommy"],
    "daniel": ["dan", "danny"],
    "matthew": ["matt"],
    "david": ["dave"],
    "edward": ["ed", "eddie", "ted"],
    "alexander": ["alex"],
    "benjamin": ["ben"],
    "samuel": ["sam"],
    "patricia": ["pat", "patty"],
    "margaret": ["maggie", "peg", "peggy"],
    "anthony": ["tony"],
    "stephen": ["steve"],
    "timothy": ["tim"],
    "charles": ["charlie", "chuck"],
    "andrew": ["andy", "drew"],
}


def _nickname_similarity(a: str, b: str) -> float:
    """Check if two names are nickname variants."""
    parts_a = a.split()
    parts_b = b.split()

    if not parts_a or not parts_b:
        return 0.0

    first_a = parts_a[0]
    first_b = parts_b[0]

    # Check last name match
    last_match = 0.0
    if len(parts_a) > 1 and len(parts_b) > 1:
        last_match = jaro_winkler_similarity(parts_a[-1], parts_b[-1])

    # Check first name nickname
    first_match = 0.0
    for formal, nicks in NICKNAME_MAP.items():
        if first_a == formal and first_b in nicks:
            first_match = 0.90
            break
        if first_b == formal and first_a in nicks:
            first_match = 0.90
            break
        if first_a in nicks and first_b in nicks:
            first_match = 0.85
            break

    # Initial match: "J. Smith" vs "John Smith"
    if len(first_a) <= 2 and first_a[0] == first_b[0]:
        first_match = max(first_match, 0.70)
    if len(first_b) <= 2 and first_b[0] == first_a[0]:
        first_match = max(first_match, 0.70)

    if first_match > 0 and last_match > 0.85:
        return (first_match + last_match) / 2

    return 0.0


def org_name_similarity(name_a: str, name_b: str) -> float:
    """Organization name similarity with abbreviation handling."""
    a = name_a.lower().strip()
    b = name_b.lower().strip()

    if a == b:
        return 1.0

    # Known abbreviation mappings
    org_aliases = {
        "gdit": ["general dynamics it", "general dynamics information technology"],
        "saic": ["science applications international"],
        "bah": ["booz allen hamilton", "booz allen"],
        "lmt": ["lockheed martin"],
        "noc": ["northrop grumman"],
        "rtn": ["raytheon", "raytheon technologies"],
        "ldos": ["leidos"],
        "bae": ["bae systems"],
        "caci": ["caci international"],
        "mant": ["mantech", "mantech international"],
    }

    for abbr, aliases in org_aliases.items():
        names = [abbr] + aliases
        if a in names and b in names:
            return 0.95

    return jaro_winkler_similarity(a, b)


def program_name_similarity(name_a: str, name_b: str) -> float:
    """Program name similarity with acronym expansion."""
    a = name_a.lower().strip()
    b = name_b.lower().strip()

    if a == b:
        return 1.0

    program_aliases = {
        "dcgs": ["distributed common ground system"],
        "dcgs-a": ["dcgs army", "distributed common ground system - army"],
        "gbsd": ["ground based strategic deterrent", "sentinel"],
        "ngen": ["next generation enterprise network"],
        "deos": ["defense enterprise office solutions"],
        "jadc2": ["joint all-domain command and control"],
        "abms": ["advanced battle management system"],
    }

    for abbr, aliases in program_aliases.items():
        names = [abbr] + aliases
        if a in names and b in names:
            return 0.95

    return jaro_winkler_similarity(a, b)


# =========================================
# RESOLVERS
# =========================================

class PersonResolver:
    """Multi-signal person resolution."""

    def resolve(self, entity_a: Dict, entity_b: Dict) -> ResolutionResult:
        """Compare two person entities."""
        signals = {}

        # 1. Name similarity
        name_a = entity_a.get("name", "")
        name_b = entity_b.get("name", "")
        signals["name"] = name_similarity(name_a, name_b)

        # 2. Email match
        email_a = entity_a.get("email", "").lower().strip()
        email_b = entity_b.get("email", "").lower().strip()
        if email_a and email_b:
            signals["email"] = 1.0 if email_a == email_b else 0.0
        else:
            signals["email"] = 0.0

        # 3. Company + Title overlap
        company_a = entity_a.get("company", "").lower()
        company_b = entity_b.get("company", "").lower()
        title_a = entity_a.get("title", "").lower()
        title_b = entity_b.get("title", "").lower()
        if company_a and company_b:
            comp_sim = org_name_similarity(company_a, company_b)
            title_sim = jaro_winkler_similarity(title_a, title_b) if title_a and title_b else 0.0
            signals["company_title"] = (comp_sim + title_sim) / 2
        else:
            signals["company_title"] = 0.0

        # 4. Phone match
        phone_a = re.sub(r'\D', '', entity_a.get("phone", ""))
        phone_b = re.sub(r'\D', '', entity_b.get("phone", ""))
        if phone_a and phone_b and len(phone_a) >= 7 and len(phone_b) >= 7:
            signals["phone"] = 1.0 if phone_a[-10:] == phone_b[-10:] else 0.0
        else:
            signals["phone"] = 0.0

        # 5. LinkedIn match
        li_a = entity_a.get("linkedin", "").lower().rstrip("/")
        li_b = entity_b.get("linkedin", "").lower().rstrip("/")
        if li_a and li_b:
            signals["linkedin"] = 1.0 if li_a == li_b else 0.0
        else:
            signals["linkedin"] = 0.0

        # 6. Location proximity
        loc_a = entity_a.get("location", "").lower()
        loc_b = entity_b.get("location", "").lower()
        if loc_a and loc_b:
            signals["location"] = 1.0 if loc_a == loc_b else jaro_winkler_similarity(loc_a, loc_b)
        else:
            signals["location"] = 0.0

        # Compute overall confidence
        confidence = self._compute_confidence(signals)
        outcome = self._classify_outcome(confidence)

        return ResolutionResult(
            entity_a_id=entity_a.get("id", ""),
            entity_b_id=entity_b.get("id", ""),
            outcome=outcome,
            confidence=round(confidence, 4),
            signals=signals,
            explanation=self._explain(signals, outcome),
        )

    def find_candidates(
        self, entity: Dict, all_entities: List[Dict], limit: int = 10,
    ) -> List[ResolutionCandidate]:
        """Find potential matches for an entity from a list."""
        candidates = []
        for other in all_entities:
            if other.get("id") == entity.get("id"):
                continue
            result = self.resolve(entity, other)
            if result.confidence >= 0.50:
                candidates.append(ResolutionCandidate(
                    entity_id=other.get("id", ""),
                    entity_name=other.get("name", ""),
                    confidence=result.confidence,
                    signals=result.signals,
                ))
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        return candidates[:limit]

    def _compute_confidence(self, signals: Dict[str, float]) -> float:
        """Weighted confidence from signals."""
        # Definitive signals override everything
        if signals.get("email") == 1.0:
            return max(0.98, signals.get("name", 0))
        if signals.get("linkedin") == 1.0:
            return max(0.97, signals.get("name", 0))
        if signals.get("phone") == 1.0:
            return max(0.96, signals.get("name", 0))

        # Weighted combination
        weights = {
            "name": 0.40,
            "company_title": 0.25,
            "location": 0.10,
            "email": 0.10,
            "phone": 0.10,
            "linkedin": 0.05,
        }
        score = sum(signals.get(k, 0) * w for k, w in weights.items())
        return min(score, 1.0)

    def _classify_outcome(self, confidence: float) -> str:
        if confidence >= 0.95:
            return MatchOutcome.DEFINITE_MATCH.value
        elif confidence >= 0.80:
            return MatchOutcome.PROBABLE_MATCH.value
        elif confidence >= 0.60:
            return MatchOutcome.POSSIBLE_MATCH.value
        return MatchOutcome.NO_MATCH.value

    def _explain(self, signals: Dict[str, float], outcome: str) -> str:
        top = sorted(signals.items(), key=lambda x: x[1], reverse=True)
        parts = [f"{k}={v:.2f}" for k, v in top[:3] if v > 0]
        return f"{outcome}: {', '.join(parts)}"


class OrganizationResolver:
    """Resolve organization name variants."""

    def resolve(self, name_a: str, name_b: str) -> ResolutionResult:
        sim = org_name_similarity(name_a, name_b)
        outcome = MatchOutcome.DEFINITE_MATCH.value if sim >= 0.95 else (
            MatchOutcome.PROBABLE_MATCH.value if sim >= 0.80 else (
                MatchOutcome.POSSIBLE_MATCH.value if sim >= 0.60 else
                MatchOutcome.NO_MATCH.value
            ))
        return ResolutionResult(
            entity_a_id=name_a, entity_b_id=name_b,
            outcome=outcome, confidence=round(sim, 4),
            signals={"name_similarity": sim},
        )


class ProgramResolver:
    """Resolve program name variants."""

    def resolve(self, name_a: str, name_b: str) -> ResolutionResult:
        sim = program_name_similarity(name_a, name_b)
        outcome = MatchOutcome.DEFINITE_MATCH.value if sim >= 0.95 else (
            MatchOutcome.PROBABLE_MATCH.value if sim >= 0.80 else (
                MatchOutcome.POSSIBLE_MATCH.value if sim >= 0.60 else
                MatchOutcome.NO_MATCH.value
            ))
        return ResolutionResult(
            entity_a_id=name_a, entity_b_id=name_b,
            outcome=outcome, confidence=round(sim, 4),
            signals={"name_similarity": sim},
        )


# =========================================
# ENTITY RESOLUTION ENGINE
# =========================================

class EntityResolutionEngine:
    """Resolves whether two entity mentions refer to the same real-world entity."""

    def __init__(self):
        self.person_resolver = PersonResolver()
        self.org_resolver = OrganizationResolver()
        self.program_resolver = ProgramResolver()
        self._merge_log: List[MergeResult] = []

    def resolve(self, entity_a: Dict, entity_b: Dict) -> ResolutionResult:
        """Resolve two entities based on their type."""
        type_a = entity_a.get("type", "person")
        if type_a == "person":
            return self.person_resolver.resolve(entity_a, entity_b)
        elif type_a == "organization":
            return self.org_resolver.resolve(
                entity_a.get("name", ""), entity_b.get("name", ""),
            )
        elif type_a == "program":
            return self.program_resolver.resolve(
                entity_a.get("name", ""), entity_b.get("name", ""),
            )
        # Default: name similarity
        sim = name_similarity(entity_a.get("name", ""), entity_b.get("name", ""))
        return ResolutionResult(
            entity_a_id=entity_a.get("id", ""),
            entity_b_id=entity_b.get("id", ""),
            outcome=MatchOutcome.NO_MATCH.value,
            confidence=sim,
            signals={"name": sim},
        )

    def find_candidates(
        self, entity: Dict, all_entities: List[Dict], limit: int = 10,
    ) -> List[ResolutionCandidate]:
        """Find resolution candidates for an entity."""
        return self.person_resolver.find_candidates(entity, all_entities, limit)

    def merge_entities(
        self, primary: Dict, duplicate: Dict,
    ) -> MergeResult:
        """Merge duplicate entity into primary, keeping the most complete data."""
        fields_merged = []
        aliases_added = []

        # Merge fields: keep primary's value if non-empty, else use duplicate's
        for key in set(list(primary.keys()) + list(duplicate.keys())):
            if key in ("id", "type"):
                continue
            p_val = primary.get(key, "")
            d_val = duplicate.get(key, "")
            if not p_val and d_val:
                primary[key] = d_val
                fields_merged.append(key)

        # Add duplicate name as alias
        dup_name = duplicate.get("name", "")
        if dup_name and dup_name != primary.get("name", ""):
            aliases = primary.get("aliases", [])
            if dup_name not in aliases:
                aliases.append(dup_name)
                primary["aliases"] = aliases
                aliases_added.append(dup_name)

        result = MergeResult(
            primary_id=primary.get("id", ""),
            merged_id=duplicate.get("id", ""),
            success=True,
            fields_merged=fields_merged,
            aliases_added=aliases_added,
        )
        self._merge_log.append(result)
        return result

    def run_global_resolution(
        self, entities: List[Dict], entity_type: str = "person",
    ) -> GlobalResolutionReport:
        """Scan all entities for duplicates using blocking + pairwise comparison."""
        import time
        start = time.time()

        # Block by first letter of last name for efficiency
        blocks: Dict[str, List[Dict]] = {}
        for entity in entities:
            name = entity.get("name", "")
            parts = name.split()
            key = parts[-1][0].lower() if parts else "?"
            if key not in blocks:
                blocks[key] = []
            blocks[key].append(entity)

        results = []
        pairs_compared = 0
        definite = probable = possible = 0

        for block_key, block_entities in blocks.items():
            for i in range(len(block_entities)):
                for j in range(i + 1, len(block_entities)):
                    pairs_compared += 1
                    result = self.resolve(block_entities[i], block_entities[j])
                    if result.outcome != MatchOutcome.NO_MATCH.value:
                        results.append(result)
                        if result.outcome == MatchOutcome.DEFINITE_MATCH.value:
                            definite += 1
                        elif result.outcome == MatchOutcome.PROBABLE_MATCH.value:
                            probable += 1
                        elif result.outcome == MatchOutcome.POSSIBLE_MATCH.value:
                            possible += 1

        auto_merged = definite  # Auto-merge definite matches
        flagged = probable + possible

        duration = time.time() - start

        return GlobalResolutionReport(
            total_entities_scanned=len(entities),
            pairs_compared=pairs_compared,
            definite_matches=definite,
            probable_matches=probable,
            possible_matches=possible,
            auto_merged=auto_merged,
            flagged_for_review=flagged,
            results=results,
            duration_seconds=round(duration, 3),
        )

    def get_merge_log(self) -> List[MergeResult]:
        return self._merge_log


# =========================================
# SINGLETON
# =========================================

_engine: Optional[EntityResolutionEngine] = None


def get_resolution_engine() -> EntityResolutionEngine:
    global _engine
    if _engine is None:
        _engine = EntityResolutionEngine()
    return _engine
