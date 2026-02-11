"""Phase 44A — Strategic Pattern Recognition Engine.

Discovers strategic patterns across all intelligence data that surface
BD opportunities: hiring surges, leadership changes, contract milestones,
competitive shifts, budget signals, geographic shifts, and skill demands.
"""

from __future__ import annotations

import hashlib
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


# =========================================
# ENUMS & DATA CLASSES
# =========================================

class PatternType(str, Enum):
    HIRING_SURGE = "hiring_surge"
    LEADERSHIP_CHANGE = "leadership_change"
    CONTRACT_MILESTONE = "contract_milestone"
    COMPETITIVE_SHIFT = "competitive_shift"
    BUDGET_SIGNAL = "budget_signal"
    GEOGRAPHIC_SHIFT = "geographic_shift"
    SKILL_DEMAND = "skill_demand"


class AlertPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class StrategicPattern:
    id: str = ""
    pattern_type: str = ""
    title: str = ""
    description: str = ""
    program: str = ""
    confidence: float = 0.0
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    detected_at: str = ""
    expires_at: str = ""
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            raw = f"{self.pattern_type}:{self.title}:{datetime.utcnow().isoformat()}"
            self.id = f"pat_{hashlib.md5(raw.encode()).hexdigest()[:12]}"
        if not self.detected_at:
            self.detected_at = datetime.utcnow().isoformat()
        if not self.expires_at:
            self.expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()


@dataclass
class OpportunityScore:
    pattern_id: str = ""
    score: int = 0  # 0-100
    urgency: str = "medium"
    impact: str = "medium"
    win_probability: float = 0.0
    recommended_actions: List[str] = field(default_factory=list)
    scoring_factors: Dict[str, float] = field(default_factory=dict)
    scored_at: str = ""

    def __post_init__(self):
        if not self.scored_at:
            self.scored_at = datetime.utcnow().isoformat()


@dataclass
class StrategicAlert:
    id: str = ""
    pattern_id: str = ""
    priority: str = "medium"
    title: str = ""
    message: str = ""
    actions: List[str] = field(default_factory=list)
    created_at: str = ""
    acknowledged: bool = False

    def __post_init__(self):
        if not self.id:
            raw = f"alert:{self.pattern_id}:{datetime.utcnow().isoformat()}"
            self.id = f"alert_{hashlib.md5(raw.encode()).hexdigest()[:12]}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


# =========================================
# SIMULATED DATA
# =========================================

_HIRING_DATA: List[Dict[str, Any]] = [
    {"program": "DCGS-A", "month": "2025-01", "postings": 12, "location": "Langley"},
    {"program": "DCGS-A", "month": "2025-02", "postings": 15, "location": "Langley"},
    {"program": "DCGS-A", "month": "2025-03", "postings": 25, "location": "Langley"},
    {"program": "DCGS-N", "month": "2025-01", "postings": 8, "location": "San Diego"},
    {"program": "DCGS-N", "month": "2025-02", "postings": 6, "location": "San Diego"},
    {"program": "DCGS-N", "month": "2025-03", "postings": 4, "location": "San Diego"},
    {"program": "GBSD", "month": "2025-01", "postings": 10, "location": "Hill AFB"},
    {"program": "GBSD", "month": "2025-02", "postings": 10, "location": "Hill AFB"},
    {"program": "GBSD", "month": "2025-03", "postings": 11, "location": "Hill AFB"},
]

_LEADERSHIP_EVENTS: List[Dict[str, Any]] = [
    {"program": "DCGS-N", "event": "departure", "role": "Site Lead",
     "person": "John Smith", "date": "2025-03-01", "replacement": None},
    {"program": "DCGS-A", "event": "promotion", "role": "PM",
     "person": "Jane Doe", "date": "2025-02-15", "replacement": "Mike Johnson"},
]

_CONTRACT_MILESTONES: List[Dict[str, Any]] = [
    {"program": "DCGS-A", "milestone": "Option Year 3", "date": "2026-06-01",
     "action": "option_exercise", "prime": "Leidos"},
    {"program": "DCGS-N", "milestone": "Re-compete", "date": "2026-09-01",
     "action": "recompete", "prime": "Raytheon"},
    {"program": "GBSD", "milestone": "CDR", "date": "2027-01-01",
     "action": "design_review", "prime": "Northrop"},
]

_BUDGET_SIGNALS: List[Dict[str, Any]] = [
    {"program": "DCGS-A", "signal": "FY26 budget increase 12%",
     "source": "congressional_markup", "amount_delta_m": 45.0},
    {"program": "DCGS-N", "signal": "FY26 budget flat",
     "source": "pbd", "amount_delta_m": 0.0},
]

_GEO_ACTIVITY: List[Dict[str, Any]] = [
    {"program": "DCGS-A", "location": "Langley", "new_postings": 8, "is_new_site": False},
    {"program": "DCGS-A", "location": "Fort Meade", "new_postings": 5, "is_new_site": True},
]

_SKILL_DEMANDS: List[Dict[str, Any]] = [
    {"program": "DCGS-A", "skill": "AI/ML", "postings_prev": 2, "postings_curr": 8},
    {"program": "DCGS-A", "skill": "Cloud Migration", "postings_prev": 1, "postings_curr": 6},
    {"program": "GBSD", "skill": "Cybersecurity", "postings_prev": 3, "postings_curr": 4},
    {"program": "DCGS-N", "skill": "Data Engineering", "postings_prev": 4, "postings_curr": 3},
]

_COMPETITOR_SHIFTS: List[Dict[str, Any]] = [
    {"competitor": "BAE", "program": "DCGS-N", "prev_postings": 6, "curr_postings": 0,
     "direction": "exit"},
    {"competitor": "Leidos", "program": "DCGS-A", "prev_postings": 5, "curr_postings": 8,
     "direction": "ramp_up"},
    {"competitor": "Northrop", "program": "GBSD", "prev_postings": 12, "curr_postings": 15,
     "direction": "ramp_up"},
]


# =========================================
# STRATEGIC PATTERN ENGINE
# =========================================

class StrategicPatternEngine:
    """Advanced pattern recognition that surfaces BD opportunities."""

    def __init__(self) -> None:
        self._patterns: List[StrategicPattern] = []
        self._alerts: List[StrategicAlert] = []
        self._scores: Dict[str, OpportunityScore] = {}

    # --------------------------------------------------
    # SCAN
    # --------------------------------------------------

    def scan_patterns(self) -> List[StrategicPattern]:
        """Scan all data for active patterns."""
        patterns: List[StrategicPattern] = []
        patterns.extend(self._scan_hiring_surges())
        patterns.extend(self._scan_leadership_changes())
        patterns.extend(self._scan_contract_milestones())
        patterns.extend(self._scan_competitive_shifts())
        patterns.extend(self._scan_budget_signals())
        patterns.extend(self._scan_geographic_shifts())
        patterns.extend(self._scan_skill_demands())
        self._patterns.extend(patterns)
        return patterns

    def _scan_hiring_surges(self) -> List[StrategicPattern]:
        patterns: List[StrategicPattern] = []
        prog_data: Dict[str, List[Dict]] = {}
        for entry in _HIRING_DATA:
            prog_data.setdefault(entry["program"], []).append(entry)

        for program, months in prog_data.items():
            months_sorted = sorted(months, key=lambda m: m["month"])
            if len(months_sorted) >= 2:
                prev = months_sorted[-2]["postings"]
                curr = months_sorted[-1]["postings"]
                pct_change = (curr - prev) / max(prev, 1)
                if pct_change > 0.3:  # 30% increase
                    patterns.append(StrategicPattern(
                        pattern_type=PatternType.HIRING_SURGE.value,
                        title=f"Hiring surge: {program}",
                        description=(
                            f"{program} postings jumped {pct_change:.0%} "
                            f"({prev}→{curr}) at {months_sorted[-1]['location']}"
                        ),
                        program=program,
                        confidence=min(0.6 + pct_change * 0.3, 0.95),
                        evidence=[{"prev": prev, "curr": curr, "pct_change": round(pct_change, 2)}],
                        tags=["hiring_surge", program.lower()],
                    ))
        return patterns

    def _scan_leadership_changes(self) -> List[StrategicPattern]:
        patterns: List[StrategicPattern] = []
        for event in _LEADERSHIP_EVENTS:
            if event["event"] == "departure" and event.get("replacement") is None:
                patterns.append(StrategicPattern(
                    pattern_type=PatternType.LEADERSHIP_CHANGE.value,
                    title=f"Leadership gap: {event['program']} {event['role']}",
                    description=(
                        f"{event['person']} departed as {event['role']} on {event['program']} "
                        f"with no replacement — 4-6 month engagement window"
                    ),
                    program=event["program"],
                    confidence=0.90,
                    evidence=[event],
                    tags=["leadership_change", event["program"].lower()],
                ))
        return patterns

    def _scan_contract_milestones(self) -> List[StrategicPattern]:
        patterns: List[StrategicPattern] = []
        now = datetime.utcnow()
        for ms in _CONTRACT_MILESTONES:
            ms_date = datetime.strptime(ms["date"], "%Y-%m-%d")
            months_away = (ms_date - now).days / 30.0
            if 0 < months_away <= 12:
                urgency = "high" if months_away <= 3 else ("medium" if months_away <= 6 else "low")
                patterns.append(StrategicPattern(
                    pattern_type=PatternType.CONTRACT_MILESTONE.value,
                    title=f"{ms['milestone']}: {ms['program']}",
                    description=(
                        f"{ms['program']} {ms['milestone']} ({ms['action']}) in "
                        f"{months_away:.0f} months — prime: {ms['prime']}"
                    ),
                    program=ms["program"],
                    confidence=0.95,
                    evidence=[{**ms, "months_away": round(months_away, 1)}],
                    tags=["contract_milestone", ms["program"].lower(), ms["action"]],
                ))
        return patterns

    def _scan_competitive_shifts(self) -> List[StrategicPattern]:
        patterns: List[StrategicPattern] = []
        for shift in _COMPETITOR_SHIFTS:
            if shift["direction"] == "exit":
                patterns.append(StrategicPattern(
                    pattern_type=PatternType.COMPETITIVE_SHIFT.value,
                    title=f"{shift['competitor']} exiting {shift['program']}",
                    description=(
                        f"{shift['competitor']} dropped from {shift['prev_postings']} to "
                        f"{shift['curr_postings']} postings — market gap opportunity"
                    ),
                    program=shift["program"],
                    confidence=0.80,
                    evidence=[shift],
                    tags=["competitive_shift", "exit", shift["competitor"].lower()],
                ))
            elif shift["direction"] == "ramp_up" and shift["curr_postings"] > shift["prev_postings"] * 1.3:
                patterns.append(StrategicPattern(
                    pattern_type=PatternType.COMPETITIVE_SHIFT.value,
                    title=f"{shift['competitor']} ramping on {shift['program']}",
                    description=(
                        f"{shift['competitor']} increased from {shift['prev_postings']} to "
                        f"{shift['curr_postings']} postings on {shift['program']}"
                    ),
                    program=shift["program"],
                    confidence=0.70,
                    evidence=[shift],
                    tags=["competitive_shift", "ramp_up", shift["competitor"].lower()],
                ))
        return patterns

    def _scan_budget_signals(self) -> List[StrategicPattern]:
        patterns: List[StrategicPattern] = []
        for sig in _BUDGET_SIGNALS:
            if sig["amount_delta_m"] > 10.0:
                patterns.append(StrategicPattern(
                    pattern_type=PatternType.BUDGET_SIGNAL.value,
                    title=f"Budget increase: {sig['program']}",
                    description=(
                        f"{sig['program']}: {sig['signal']} (+${sig['amount_delta_m']:.0f}M) "
                        f"from {sig['source']}"
                    ),
                    program=sig["program"],
                    confidence=0.85,
                    evidence=[sig],
                    tags=["budget_signal", sig["program"].lower()],
                ))
        return patterns

    def _scan_geographic_shifts(self) -> List[StrategicPattern]:
        patterns: List[StrategicPattern] = []
        for geo in _GEO_ACTIVITY:
            if geo["is_new_site"]:
                patterns.append(StrategicPattern(
                    pattern_type=PatternType.GEOGRAPHIC_SHIFT.value,
                    title=f"New site: {geo['program']} at {geo['location']}",
                    description=(
                        f"{geo['program']} expanding to {geo['location']} "
                        f"({geo['new_postings']} new postings)"
                    ),
                    program=geo["program"],
                    confidence=0.80,
                    evidence=[geo],
                    tags=["geographic_shift", geo["location"].lower().replace(" ", "_")],
                ))
        return patterns

    def _scan_skill_demands(self) -> List[StrategicPattern]:
        patterns: List[StrategicPattern] = []
        for sk in _SKILL_DEMANDS:
            if sk["postings_curr"] > sk["postings_prev"] * 2:  # 2x increase
                patterns.append(StrategicPattern(
                    pattern_type=PatternType.SKILL_DEMAND.value,
                    title=f"Skill demand surge: {sk['skill']} on {sk['program']}",
                    description=(
                        f"{sk['program']} demand for {sk['skill']} jumped "
                        f"{sk['postings_prev']}→{sk['postings_curr']} — "
                        f"capability gap = BD angle"
                    ),
                    program=sk["program"],
                    confidence=0.75,
                    evidence=[sk],
                    tags=["skill_demand", sk["skill"].lower().replace("/", "_")],
                ))
        return patterns

    # --------------------------------------------------
    # SCORE
    # --------------------------------------------------

    def score_opportunity(self, pattern: StrategicPattern) -> OpportunityScore:
        """Score a detected pattern as a BD opportunity (0-100)."""
        factors: Dict[str, float] = {}

        # Confidence factor (0-25)
        factors["confidence"] = pattern.confidence * 25

        # Pattern type factor (0-25)
        type_weights = {
            PatternType.HIRING_SURGE.value: 20,
            PatternType.LEADERSHIP_CHANGE.value: 22,
            PatternType.CONTRACT_MILESTONE.value: 25,
            PatternType.COMPETITIVE_SHIFT.value: 23,
            PatternType.BUDGET_SIGNAL.value: 20,
            PatternType.GEOGRAPHIC_SHIFT.value: 15,
            PatternType.SKILL_DEMAND.value: 18,
        }
        factors["type_weight"] = type_weights.get(pattern.pattern_type, 15)

        # Evidence strength (0-25)
        evidence_count = len(pattern.evidence)
        factors["evidence"] = min(evidence_count * 8, 25)

        # Recency factor (0-25)
        try:
            detected = datetime.fromisoformat(pattern.detected_at)
            age_hours = (datetime.utcnow() - detected).total_seconds() / 3600
            factors["recency"] = max(25 - age_hours * 0.5, 0)
        except (ValueError, TypeError):
            factors["recency"] = 15

        score = int(min(sum(factors.values()), 100))

        # Urgency
        if score >= 80:
            urgency = "urgent"
        elif score >= 60:
            urgency = "high"
        elif score >= 40:
            urgency = "medium"
        else:
            urgency = "low"

        # Win probability (heuristic)
        win_prob = round(min(score * 0.008 + 0.10, 0.85), 2)

        # Actions
        actions = self._recommend_actions(pattern)

        opp = OpportunityScore(
            pattern_id=pattern.id,
            score=score,
            urgency=urgency,
            impact=urgency,
            win_probability=win_prob,
            recommended_actions=actions,
            scoring_factors={k: round(v, 1) for k, v in factors.items()},
        )
        self._scores[pattern.id] = opp
        return opp

    def _recommend_actions(self, pattern: StrategicPattern) -> List[str]:
        actions: List[str] = []
        pt = pattern.pattern_type
        prog = pattern.program

        if pt == PatternType.HIRING_SURGE.value:
            actions.append(f"Identify key hires needed for {prog} and position GDIT candidates")
            actions.append(f"Prepare staffing proposal for {prog} expansion")
        elif pt == PatternType.LEADERSHIP_CHANGE.value:
            actions.append(f"Engage {prog} during leadership transition window")
            actions.append(f"Offer interim staffing support for {prog}")
        elif pt == PatternType.CONTRACT_MILESTONE.value:
            actions.append(f"Begin teaming discussions for {prog}")
            actions.append(f"Prepare capability brief for {prog} re-compete")
        elif pt == PatternType.COMPETITIVE_SHIFT.value:
            if "exit" in pattern.tags:
                actions.append(f"Immediately pursue gap left in {prog}")
            else:
                actions.append(f"Monitor and differentiate positioning for {prog}")
        elif pt == PatternType.BUDGET_SIGNAL.value:
            actions.append(f"Align BD pipeline with {prog} budget increase")
        elif pt == PatternType.GEOGRAPHIC_SHIFT.value:
            actions.append(f"Assess local talent pool for new {prog} site")
        elif pt == PatternType.SKILL_DEMAND.value:
            actions.append(f"Highlight GDIT {pattern.tags[-1] if pattern.tags else ''} capability for {prog}")

        return actions

    # --------------------------------------------------
    # ALERTS
    # --------------------------------------------------

    def generate_alerts(self, patterns: List[StrategicPattern]) -> List[StrategicAlert]:
        """Generate actionable alerts for high-scoring patterns."""
        alerts: List[StrategicAlert] = []
        for pattern in patterns:
            score = self._scores.get(pattern.id)
            if score is None:
                score = self.score_opportunity(pattern)

            if score.score >= 50:
                priority = (
                    AlertPriority.URGENT.value if score.score >= 80
                    else AlertPriority.HIGH.value if score.score >= 65
                    else AlertPriority.MEDIUM.value
                )
                alert = StrategicAlert(
                    pattern_id=pattern.id,
                    priority=priority,
                    title=pattern.title,
                    message=pattern.description,
                    actions=score.recommended_actions,
                )
                alerts.append(alert)
                self._alerts.append(alert)

        return alerts

    # --------------------------------------------------
    # QUERIES
    # --------------------------------------------------

    def get_active_patterns(self, pattern_type: str = "") -> List[StrategicPattern]:
        """Get currently active patterns, optionally filtered by type."""
        now = datetime.utcnow().isoformat()
        results = [p for p in self._patterns if p.expires_at > now]
        if pattern_type:
            results = [p for p in results if p.pattern_type == pattern_type]
        return results

    def get_opportunities(self, min_score: int = 0) -> List[Dict[str, Any]]:
        """Get scored BD opportunities."""
        opps: List[Dict[str, Any]] = []
        for pattern in self._patterns:
            score = self._scores.get(pattern.id)
            if score and score.score >= min_score:
                opps.append({
                    "pattern_id": pattern.id,
                    "title": pattern.title,
                    "program": pattern.program,
                    "pattern_type": pattern.pattern_type,
                    "score": score.score,
                    "urgency": score.urgency,
                    "win_probability": score.win_probability,
                    "actions": score.recommended_actions,
                })
        opps.sort(key=lambda o: o["score"], reverse=True)
        return opps

    def get_alerts(self, unacknowledged_only: bool = False) -> List[StrategicAlert]:
        """Get all strategic alerts."""
        results = list(self._alerts)
        if unacknowledged_only:
            results = [a for a in results if not a.acknowledged]
        return results

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge a strategic alert."""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get pattern engine statistics."""
        type_counts: Dict[str, int] = {}
        for p in self._patterns:
            type_counts[p.pattern_type] = type_counts.get(p.pattern_type, 0) + 1

        return {
            "total_patterns": len(self._patterns),
            "by_type": type_counts,
            "total_scores": len(self._scores),
            "total_alerts": len(self._alerts),
            "avg_score": round(
                statistics.mean(s.score for s in self._scores.values()), 1
            ) if self._scores else 0,
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[StrategicPatternEngine] = None


def get_pattern_engine() -> StrategicPatternEngine:
    global _instance
    if _instance is None:
        _instance = StrategicPatternEngine()
    return _instance
