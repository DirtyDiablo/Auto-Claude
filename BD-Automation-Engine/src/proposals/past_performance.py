"""Phase 35A — Past Performance Matrix Builder

Auto-build past performance matrices from Federal Programs DB + placement history:
  - Match past work to solicitation requirements (NAICS, labor categories, clearance)
  - Relevance scoring: how well each past performance aligns
  - CPARS-style metrics: quality, schedule, cost, management
  - Auto-generate performance narratives
  - Export to DOCX table format
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================


@dataclass
class RelevanceScore:
    """How well a past performance entry matches solicitation requirements."""

    overall: float = 0.0  # 0-100
    naics_match: float = 0.0
    labor_match: float = 0.0
    clearance_match: float = 0.0
    agency_match: float = 0.0
    scope_match: float = 0.0


@dataclass
class CPARSMetrics:
    """CPARS-style performance ratings."""

    quality: str = (
        "Satisfactory"  # Exceptional, Very Good, Satisfactory, Marginal, Unsatisfactory
    )
    schedule: str = "Satisfactory"
    cost: str = "Satisfactory"
    management: str = "Satisfactory"
    overall: str = "Satisfactory"


CPARS_RATINGS = [
    "Exceptional",
    "Very Good",
    "Satisfactory",
    "Marginal",
    "Unsatisfactory",
]
CPARS_SCORES = {
    "Exceptional": 5,
    "Very Good": 4,
    "Satisfactory": 3,
    "Marginal": 2,
    "Unsatisfactory": 1,
}


@dataclass
class PastPerformanceEntry:
    """Single past performance record."""

    id: str
    contract_name: str
    contract_number: str = ""
    agency: str = ""
    program: str = ""
    value: float = 0.0
    period_start: str = ""
    period_end: str = ""
    naics: str = ""
    labor_categories: List[str] = field(default_factory=list)
    clearance_level: str = ""
    description: str = ""
    relevance_narrative: str = ""
    relevance: RelevanceScore = field(default_factory=RelevanceScore)
    cpars: CPARSMetrics = field(default_factory=CPARSMetrics)
    placements: int = 0


@dataclass
class PerformanceMatrix:
    """Complete past performance matrix for a solicitation."""

    id: str
    solicitation: str
    entries: List[PastPerformanceEntry] = field(default_factory=list)
    total_entries: int = 0
    avg_relevance: float = 0.0
    generated_at: str = ""
    requirements: Dict[str, Any] = field(default_factory=dict)


# =========================================
# RELEVANCE SCORING
# =========================================

RELEVANCE_WEIGHTS = {
    "naics_match": 0.20,
    "labor_match": 0.25,
    "clearance_match": 0.20,
    "agency_match": 0.15,
    "scope_match": 0.20,
}


def _score_naics_match(entry_naics: str, required_naics: List[str]) -> float:
    """Score NAICS code match (0-100)."""
    if not required_naics or not entry_naics:
        return 50.0  # Neutral if no data
    entry_clean = entry_naics.strip()
    for req in required_naics:
        if entry_clean == req.strip():
            return 100.0
        if entry_clean[:4] == req.strip()[:4]:
            return 75.0
        if entry_clean[:2] == req.strip()[:2]:
            return 40.0
    return 10.0


def _score_labor_match(entry_labcats: List[str], required_labcats: List[str]) -> float:
    """Score labor category overlap (0-100)."""
    if not required_labcats or not entry_labcats:
        return 50.0
    entry_lower = {lc.lower() for lc in entry_labcats}
    req_lower = {lc.lower() for lc in required_labcats}
    overlap = len(entry_lower & req_lower)
    if overlap == 0:
        # Fuzzy: check partial matches
        partial = sum(1 for e in entry_lower for r in req_lower if e in r or r in e)
        return min(60.0, partial * 20.0)
    return min(100.0, (overlap / max(len(req_lower), 1)) * 100)


def _score_clearance_match(entry_clearance: str, required_clearance: str) -> float:
    """Score clearance level match (0-100)."""
    if not required_clearance:
        return 80.0
    clearance_hierarchy = {
        "ts/sci with ci polygraph": 6,
        "ts/sci ci poly": 6,
        "ts/sci": 5,
        "top secret": 4,
        "secret": 3,
        "public trust": 2,
        "none": 1,
    }
    entry_level = clearance_hierarchy.get(entry_clearance.lower().strip(), 0)
    req_level = clearance_hierarchy.get(required_clearance.lower().strip(), 0)

    if entry_level == 0 or req_level == 0:
        return 50.0
    if entry_level >= req_level:
        return 100.0
    if entry_level == req_level - 1:
        return 60.0
    return 20.0


def _score_agency_match(entry_agency: str, required_agency: str) -> float:
    """Score agency match (0-100)."""
    if not required_agency or not entry_agency:
        return 50.0
    if entry_agency.lower().strip() == required_agency.lower().strip():
        return 100.0
    # Same parent organization heuristic
    dod_agencies = {
        "army",
        "navy",
        "air force",
        "usaf",
        "marines",
        "disa",
        "dla",
        "nsa",
        "nga",
        "dia",
    }
    entry_low = entry_agency.lower()
    req_low = required_agency.lower()
    if any(a in entry_low for a in dod_agencies) and any(
        a in req_low for a in dod_agencies
    ):
        return 65.0
    return 25.0


def _score_scope_match(entry_value: float, required_value: float) -> float:
    """Score contract value/scope similarity (0-100)."""
    if required_value <= 0 or entry_value <= 0:
        return 50.0
    ratio = min(entry_value, required_value) / max(entry_value, required_value)
    return ratio * 100


def compute_relevance(
    entry: PastPerformanceEntry,
    requirements: Dict[str, Any],
) -> RelevanceScore:
    """Compute relevance score for a past performance entry against requirements."""
    naics_score = _score_naics_match(entry.naics, requirements.get("naics_codes", []))
    labor_score = _score_labor_match(
        entry.labor_categories, requirements.get("labor_categories", [])
    )
    clearance_score = _score_clearance_match(
        entry.clearance_level, requirements.get("clearance", "")
    )
    agency_score = _score_agency_match(entry.agency, requirements.get("agency", ""))
    scope_score = _score_scope_match(entry.value, requirements.get("contract_value", 0))

    overall = (
        naics_score * RELEVANCE_WEIGHTS["naics_match"]
        + labor_score * RELEVANCE_WEIGHTS["labor_match"]
        + clearance_score * RELEVANCE_WEIGHTS["clearance_match"]
        + agency_score * RELEVANCE_WEIGHTS["agency_match"]
        + scope_score * RELEVANCE_WEIGHTS["scope_match"]
    )

    return RelevanceScore(
        overall=round(overall, 2),
        naics_match=round(naics_score, 2),
        labor_match=round(labor_score, 2),
        clearance_match=round(clearance_score, 2),
        agency_match=round(agency_score, 2),
        scope_match=round(scope_score, 2),
    )


# =========================================
# NARRATIVE GENERATOR
# =========================================


def generate_narrative(entry: PastPerformanceEntry) -> str:
    """Auto-generate a relevance narrative for a past performance entry."""
    parts = [f"Under the {entry.contract_name} contract"]
    if entry.agency:
        parts.append(f"for {entry.agency}")
    parts.append(
        f", PTS provided {entry.placements or 'multiple'} cleared professionals"
    )
    if entry.labor_categories:
        cats = ", ".join(entry.labor_categories[:3])
        parts.append(f" in roles including {cats}")
    if entry.clearance_level:
        parts.append(f" at the {entry.clearance_level} clearance level")
    parts.append(".")

    if entry.value > 0:
        parts.append(f" Contract value: ${entry.value:,.0f}.")
    if entry.period_start and entry.period_end:
        parts.append(
            f" Period of performance: {entry.period_start} to {entry.period_end}."
        )

    cpars_score = CPARS_SCORES.get(entry.cpars.overall, 3)
    if cpars_score >= 4:
        parts.append(f" Performance was rated {entry.cpars.overall}.")

    return "".join(parts)


# =========================================
# BUILDER
# =========================================


class PastPerformanceBuilder:
    """Build past performance matrices for solicitations."""

    def __init__(self, knowledge_client: Any = None):
        self._knowledge = knowledge_client
        self._entries: List[PastPerformanceEntry] = []
        self._history: List[PerformanceMatrix] = []

    def set_knowledge_client(self, client: Any) -> None:
        self._knowledge = client

    def add_entry(self, entry: PastPerformanceEntry) -> None:
        """Add a past performance entry."""
        self._entries.append(entry)

    def set_entries(self, entries: List[PastPerformanceEntry]) -> None:
        """Set all entries."""
        self._entries = list(entries)

    async def build_matrix(
        self,
        solicitation: str,
        requirements: Optional[Dict[str, Any]] = None,
        top_n: int = 5,
    ) -> PerformanceMatrix:
        """Build a past performance matrix scored against solicitation requirements."""
        requirements = requirements or {}

        # Fetch entries from knowledge base if empty
        if not self._entries and self._knowledge:
            self._entries = await self._fetch_entries(solicitation)

        if not self._entries:
            matrix = PerformanceMatrix(
                id=f"pp-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                solicitation=solicitation,
                entries=[],
                total_entries=0,
                avg_relevance=0.0,
                generated_at=datetime.now(timezone.utc).isoformat(),
                requirements=requirements,
            )
            self._history.append(matrix)
            return matrix

        # Score relevance for each entry
        for entry in self._entries:
            entry.relevance = compute_relevance(entry, requirements)
            if not entry.relevance_narrative:
                entry.relevance_narrative = generate_narrative(entry)

        # Sort by relevance and take top N
        scored = sorted(self._entries, key=lambda e: e.relevance.overall, reverse=True)
        top_entries = scored[:top_n]

        avg_rel = (
            sum(e.relevance.overall for e in top_entries) / len(top_entries)
            if top_entries
            else 0
        )

        matrix = PerformanceMatrix(
            id=f"pp-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            solicitation=solicitation,
            entries=top_entries,
            total_entries=len(top_entries),
            avg_relevance=round(avg_rel, 2),
            generated_at=datetime.now(timezone.utc).isoformat(),
            requirements=requirements,
        )

        self._history.append(matrix)
        logger.info(
            f"Built past performance matrix for {solicitation}: "
            f"{len(top_entries)} entries, avg relevance {avg_rel:.1f}"
        )
        return matrix

    def get_history(self) -> List[PerformanceMatrix]:
        """Return build history."""
        return list(self._history)

    def export_to_dict(self, matrix: PerformanceMatrix) -> Dict[str, Any]:
        """Export matrix to serializable dictionary."""
        return {
            "id": matrix.id,
            "solicitation": matrix.solicitation,
            "total_entries": matrix.total_entries,
            "avg_relevance": matrix.avg_relevance,
            "generated_at": matrix.generated_at,
            "entries": [
                {
                    "contract_name": e.contract_name,
                    "contract_number": e.contract_number,
                    "agency": e.agency,
                    "program": e.program,
                    "value": e.value,
                    "period": f"{e.period_start} - {e.period_end}",
                    "naics": e.naics,
                    "clearance": e.clearance_level,
                    "relevance_score": e.relevance.overall,
                    "relevance_narrative": e.relevance_narrative,
                    "cpars": {
                        "quality": e.cpars.quality,
                        "schedule": e.cpars.schedule,
                        "cost": e.cpars.cost,
                        "management": e.cpars.management,
                        "overall": e.cpars.overall,
                    },
                }
                for e in matrix.entries
            ],
        }

    async def _fetch_entries(self, solicitation: str) -> List[PastPerformanceEntry]:
        """Fetch past performance entries from knowledge base."""
        if self._knowledge and hasattr(self._knowledge, "search"):
            try:
                results = await self._knowledge.search(
                    solicitation, collection="programs", limit=10
                )
                entries = []
                for r in results if isinstance(results, list) else []:
                    entries.append(
                        PastPerformanceEntry(
                            id=r.get("id", ""),
                            contract_name=r.get("name", r.get("contract_name", "")),
                            agency=r.get("agency", ""),
                            program=r.get("program", ""),
                            value=r.get("value", 0),
                        )
                    )
                return entries
            except Exception as e:
                logger.warning(f"Could not fetch entries for {solicitation}: {e}")
        return []


# =========================================
# SINGLETON
# =========================================

_builder: Optional[PastPerformanceBuilder] = None


def get_past_performance_builder() -> PastPerformanceBuilder:
    global _builder
    if _builder is None:
        _builder = PastPerformanceBuilder()
    return _builder
