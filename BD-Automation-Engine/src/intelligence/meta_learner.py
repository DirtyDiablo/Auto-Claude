"""Phase 44A — Meta-Learning Engine.

Continuously analyzes platform activity to discover actionable patterns
across outreach effectiveness, program intelligence, contact behaviour,
data quality, and competitive intelligence.
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

class InsightDomain(str, Enum):
    OUTREACH = "outreach"
    PROGRAM = "program"
    CONTACT = "contact"
    DATA_QUALITY = "data_quality"
    COMPETITIVE = "competitive"


class InsightSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MetaInsight:
    id: str = ""
    domain: str = ""
    title: str = ""
    description: str = ""
    severity: str = "medium"
    confidence: float = 0.0
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    created_at: str = ""
    expires_at: str = ""
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            raw = f"{self.domain}:{self.title}:{datetime.utcnow().isoformat()}"
            self.id = f"insight_{hashlib.md5(raw.encode()).hexdigest()[:12]}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.expires_at:
            self.expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()


@dataclass
class OutreachInsight(MetaInsight):
    channel: str = ""
    best_time: str = ""
    response_rate: float = 0.0
    tier_effectiveness: Dict[str, float] = field(default_factory=dict)


@dataclass
class ProgramInsight(MetaInsight):
    program_id: str = ""
    program_name: str = ""
    trend: str = ""  # growing | shrinking | stable
    cycle_phase: str = ""  # hiring | stabilizing | winding_down


@dataclass
class ContactInsight(MetaInsight):
    contact_pattern: str = ""  # role_churn | super_connector | career_progression
    affected_contacts: List[str] = field(default_factory=list)


@dataclass
class TransferReport:
    source_program: str = ""
    target_program: str = ""
    transferable_insights: List[MetaInsight] = field(default_factory=list)
    similarity_score: float = 0.0
    recommended_approaches: List[str] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


# =========================================
# SIMULATED DATA STORES
# =========================================

_OUTREACH_LOG: List[Dict[str, Any]] = [
    {"channel": "email", "tier": 1, "day": "Tuesday", "hour": 14, "responded": True, "contact": "c001"},
    {"channel": "email", "tier": 1, "day": "Tuesday", "hour": 15, "responded": True, "contact": "c002"},
    {"channel": "email", "tier": 1, "day": "Monday", "hour": 9, "responded": False, "contact": "c003"},
    {"channel": "linkedin", "tier": 2, "day": "Wednesday", "hour": 10, "responded": True, "contact": "c004"},
    {"channel": "linkedin", "tier": 2, "day": "Friday", "hour": 16, "responded": False, "contact": "c005"},
    {"channel": "linkedin", "tier": 3, "day": "Tuesday", "hour": 14, "responded": True, "contact": "c006"},
    {"channel": "phone", "tier": 1, "day": "Thursday", "hour": 11, "responded": False, "contact": "c007"},
    {"channel": "phone", "tier": 2, "day": "Monday", "hour": 10, "responded": True, "contact": "c008"},
    {"channel": "email", "tier": 3, "day": "Tuesday", "hour": 14, "responded": True, "contact": "c009"},
    {"channel": "email", "tier": 2, "day": "Wednesday", "hour": 13, "responded": True, "contact": "c010"},
]

_PROGRAM_ACTIVITY: List[Dict[str, Any]] = [
    {"program": "DCGS-A", "month": "2025-01", "job_postings": 12, "hires": 8, "departures": 2},
    {"program": "DCGS-A", "month": "2025-02", "job_postings": 15, "hires": 10, "departures": 3},
    {"program": "DCGS-A", "month": "2025-03", "job_postings": 20, "hires": 12, "departures": 2},
    {"program": "DCGS-N", "month": "2025-01", "job_postings": 5, "hires": 3, "departures": 4},
    {"program": "DCGS-N", "month": "2025-02", "job_postings": 4, "hires": 2, "departures": 5},
    {"program": "DCGS-N", "month": "2025-03", "job_postings": 3, "hires": 1, "departures": 3},
    {"program": "GBSD", "month": "2025-01", "job_postings": 8, "hires": 6, "departures": 1},
    {"program": "GBSD", "month": "2025-02", "job_postings": 9, "hires": 7, "departures": 1},
    {"program": "GBSD", "month": "2025-03", "job_postings": 10, "hires": 8, "departures": 2},
]

_CONTACT_EVENTS: List[Dict[str, Any]] = [
    {"contact": "c001", "event": "role_change", "from_role": "Site Lead", "to_role": "PM", "program": "DCGS-A"},
    {"contact": "c002", "event": "departure", "from_role": "Site Lead", "program": "DCGS-N"},
    {"contact": "c003", "event": "role_change", "from_role": "Engineer", "to_role": "Tech Lead", "program": "DCGS-A"},
    {"contact": "c004", "event": "multi_program", "programs": ["DCGS-A", "DCGS-N", "GBSD"], "role": "BD Lead"},
    {"contact": "c005", "event": "multi_program", "programs": ["DCGS-A", "GBSD"], "role": "VP Engineering"},
    {"contact": "c006", "event": "departure", "from_role": "Analyst", "program": "DCGS-N"},
]

_COMPETITOR_ACTIVITY: List[Dict[str, Any]] = [
    {"competitor": "Leidos", "program": "DCGS-A", "postings": 8, "month": "2025-03", "roles": ["Systems Engineer", "Analyst"]},
    {"competitor": "Northrop", "program": "GBSD", "postings": 15, "month": "2025-03", "roles": ["Software Dev", "PM"]},
    {"competitor": "Raytheon", "program": "DCGS-N", "postings": 3, "month": "2025-03", "roles": ["Analyst"]},
    {"competitor": "Leidos", "program": "DCGS-A", "postings": 5, "month": "2025-02", "roles": ["Systems Engineer"]},
    {"competitor": "Northrop", "program": "GBSD", "postings": 12, "month": "2025-02", "roles": ["Software Dev"]},
    {"competitor": "BAE", "program": "DCGS-N", "postings": 0, "month": "2025-03", "roles": []},
    {"competitor": "BAE", "program": "DCGS-N", "postings": 6, "month": "2025-02", "roles": ["Engineer", "Analyst"]},
]

_DATA_QUALITY_LOG: List[Dict[str, Any]] = [
    {"source": "bullhorn", "field": "email", "decay_days": 30, "accuracy": 0.85},
    {"source": "bullhorn", "field": "title", "decay_days": 90, "accuracy": 0.92},
    {"source": "bullhorn", "field": "company", "decay_days": 180, "accuracy": 0.96},
    {"source": "bullhorn", "field": "location", "decay_days": 120, "accuracy": 0.94},
    {"source": "scraper", "field": "email", "decay_days": 45, "accuracy": 0.78},
    {"source": "scraper", "field": "title", "decay_days": 60, "accuracy": 0.88},
    {"source": "linkedin", "field": "title", "decay_days": 30, "accuracy": 0.95},
    {"source": "linkedin", "field": "company", "decay_days": 60, "accuracy": 0.97},
]


# =========================================
# META-LEARNING ENGINE
# =========================================

class MetaLearningEngine:
    """Continuously analyzes platform activity to discover actionable patterns."""

    def __init__(self) -> None:
        self._insights: List[MetaInsight] = []
        self._transfer_reports: List[TransferReport] = []

    # --------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------

    def learn(self) -> List[MetaInsight]:
        """Run all learning algorithms and generate insights."""
        insights: List[MetaInsight] = []
        insights.extend(self.learn_outreach())
        insights.extend(self.learn_programs())
        insights.extend(self.learn_contacts())
        insights.extend(self.learn_data_quality())
        insights.extend(self.learn_competitive())
        self._insights.extend(insights)
        return insights

    def learn_outreach(self) -> List[OutreachInsight]:
        """Analyze outreach effectiveness patterns."""
        insights: List[OutreachInsight] = []

        # --- Channel effectiveness by tier ---
        channel_tier: Dict[str, Dict[int, List[bool]]] = {}
        for entry in _OUTREACH_LOG:
            ch = entry["channel"]
            tier = entry["tier"]
            channel_tier.setdefault(ch, {}).setdefault(tier, []).append(entry["responded"])

        for channel, tiers in channel_tier.items():
            tier_eff: Dict[str, float] = {}
            for tier, responses in tiers.items():
                rate = sum(responses) / len(responses) if responses else 0.0
                tier_eff[f"tier_{tier}"] = round(rate, 2)

            avg_rate = statistics.mean(tier_eff.values()) if tier_eff else 0.0
            insights.append(OutreachInsight(
                domain=InsightDomain.OUTREACH.value,
                title=f"{channel.title()} channel effectiveness",
                description=f"{channel.title()} has {avg_rate:.0%} avg response rate across tiers",
                severity=InsightSeverity.MEDIUM.value if avg_rate < 0.6 else InsightSeverity.LOW.value,
                confidence=min(0.5 + len(_OUTREACH_LOG) * 0.02, 0.95),
                channel=channel,
                response_rate=round(avg_rate, 2),
                tier_effectiveness=tier_eff,
                recommendations=[f"Focus {channel} on highest-responding tiers"],
                tags=["outreach", channel],
            ))

        # --- Best day/time ---
        day_hour: Dict[str, List[bool]] = {}
        for entry in _OUTREACH_LOG:
            key = f"{entry['day']}_{entry['hour']}"
            day_hour.setdefault(key, []).append(entry["responded"])

        best_slot = max(day_hour.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))
        day, hour = best_slot[0].split("_")
        rate = sum(best_slot[1]) / len(best_slot[1])
        insights.append(OutreachInsight(
            domain=InsightDomain.OUTREACH.value,
            title=f"Best outreach window: {day} {hour}:00",
            description=f"{day} at {hour}:00 has {rate:.0%} response rate",
            severity=InsightSeverity.HIGH.value,
            confidence=0.75,
            best_time=f"{day} {hour}:00",
            response_rate=round(rate, 2),
            recommendations=[f"Schedule high-priority outreach on {day} around {hour}:00"],
            tags=["outreach", "timing"],
        ))

        return insights

    def learn_programs(self) -> List[ProgramInsight]:
        """Analyze program intelligence patterns."""
        insights: List[ProgramInsight] = []

        # Group by program
        prog_data: Dict[str, List[Dict]] = {}
        for entry in _PROGRAM_ACTIVITY:
            prog_data.setdefault(entry["program"], []).append(entry)

        for program, months in prog_data.items():
            months_sorted = sorted(months, key=lambda m: m["month"])
            postings = [m["job_postings"] for m in months_sorted]

            # Determine trend
            if len(postings) >= 2:
                delta = postings[-1] - postings[0]
                if delta > 2:
                    trend = "growing"
                elif delta < -2:
                    trend = "shrinking"
                else:
                    trend = "stable"
            else:
                trend = "stable"

            # Determine cycle phase
            latest = months_sorted[-1]
            net = latest["hires"] - latest["departures"]
            if latest["job_postings"] > 10 and net > 0:
                phase = "hiring"
            elif net < 0:
                phase = "winding_down"
            else:
                phase = "stabilizing"

            severity = InsightSeverity.HIGH.value if trend == "growing" else (
                InsightSeverity.CRITICAL.value if trend == "shrinking" else InsightSeverity.LOW.value
            )

            insights.append(ProgramInsight(
                domain=InsightDomain.PROGRAM.value,
                title=f"{program} is {trend}",
                description=(
                    f"{program}: {postings[-1]} postings last month, "
                    f"trend={trend}, phase={phase}"
                ),
                severity=severity,
                confidence=0.80,
                program_id=program.lower().replace("-", "_"),
                program_name=program,
                trend=trend,
                cycle_phase=phase,
                recommendations=[
                    f"{'Accelerate' if trend == 'growing' else 'Monitor'} BD efforts for {program}"
                ],
                tags=["program", trend, program.lower()],
            ))

        return insights

    def learn_contacts(self) -> List[ContactInsight]:
        """Analyze contact behaviour patterns."""
        insights: List[ContactInsight] = []

        # --- Super connectors (linked to 2+ programs) ---
        multi_program = [e for e in _CONTACT_EVENTS if e["event"] == "multi_program"]
        for entry in multi_program:
            n_programs = len(entry["programs"])
            if n_programs >= 2:
                insights.append(ContactInsight(
                    domain=InsightDomain.CONTACT.value,
                    title=f"Super connector: {entry['contact']}",
                    description=(
                        f"{entry['contact']} ({entry['role']}) spans "
                        f"{n_programs} programs: {', '.join(entry['programs'])}"
                    ),
                    severity=InsightSeverity.HIGH.value,
                    confidence=0.90,
                    contact_pattern="super_connector",
                    affected_contacts=[entry["contact"]],
                    recommendations=[f"Prioritize relationship with {entry['contact']}"],
                    tags=["contact", "super_connector"],
                ))

        # --- Role churn (departures leaving gaps) ---
        departures = [e for e in _CONTACT_EVENTS if e["event"] == "departure"]
        if departures:
            affected = [d["contact"] for d in departures]
            programs_affected = list({d["program"] for d in departures})
            insights.append(ContactInsight(
                domain=InsightDomain.CONTACT.value,
                title=f"Role churn detected: {len(departures)} departures",
                description=(
                    f"{len(departures)} departures across {', '.join(programs_affected)} — "
                    f"potential BD engagement windows during transition"
                ),
                severity=InsightSeverity.HIGH.value,
                confidence=0.85,
                contact_pattern="role_churn",
                affected_contacts=affected,
                recommendations=["Engage during transition period (4-6 month fill window)"],
                tags=["contact", "role_churn"],
            ))

        # --- Career progression ---
        progressions = [e for e in _CONTACT_EVENTS if e["event"] == "role_change"]
        if progressions:
            insights.append(ContactInsight(
                domain=InsightDomain.CONTACT.value,
                title=f"Career progressions: {len(progressions)} role changes",
                description=(
                    f"{len(progressions)} contacts changed roles — "
                    f"update relationship strategy for new positions"
                ),
                severity=InsightSeverity.MEDIUM.value,
                confidence=0.88,
                contact_pattern="career_progression",
                affected_contacts=[p["contact"] for p in progressions],
                recommendations=["Re-engage contacts with congratulatory outreach"],
                tags=["contact", "career_progression"],
            ))

        return insights

    def learn_data_quality(self) -> List[MetaInsight]:
        """Analyze data quality patterns."""
        insights: List[MetaInsight] = []

        # --- Decay rates by field ---
        field_decay: Dict[str, List[int]] = {}
        for entry in _DATA_QUALITY_LOG:
            field_decay.setdefault(entry["field"], []).append(entry["decay_days"])

        fastest = min(field_decay.items(), key=lambda kv: statistics.mean(kv[1]))
        slowest = max(field_decay.items(), key=lambda kv: statistics.mean(kv[1]))

        insights.append(MetaInsight(
            domain=InsightDomain.DATA_QUALITY.value,
            title=f"Fastest decaying field: {fastest[0]}",
            description=(
                f"'{fastest[0]}' data decays in avg {statistics.mean(fastest[1]):.0f} days vs "
                f"'{slowest[0]}' at {statistics.mean(slowest[1]):.0f} days"
            ),
            severity=InsightSeverity.HIGH.value,
            confidence=0.82,
            recommendations=[f"Increase refresh frequency for '{fastest[0]}' data"],
            tags=["data_quality", "decay", fastest[0]],
        ))

        # --- Source quality comparison ---
        source_acc: Dict[str, List[float]] = {}
        for entry in _DATA_QUALITY_LOG:
            source_acc.setdefault(entry["source"], []).append(entry["accuracy"])

        best_source = max(source_acc.items(), key=lambda kv: statistics.mean(kv[1]))
        worst_source = min(source_acc.items(), key=lambda kv: statistics.mean(kv[1]))

        insights.append(MetaInsight(
            domain=InsightDomain.DATA_QUALITY.value,
            title=f"Best data source: {best_source[0]}",
            description=(
                f"'{best_source[0]}' avg accuracy {statistics.mean(best_source[1]):.0%} vs "
                f"'{worst_source[0]}' at {statistics.mean(worst_source[1]):.0%}"
            ),
            severity=InsightSeverity.MEDIUM.value,
            confidence=0.78,
            recommendations=[f"Prioritize '{best_source[0]}' for critical enrichment"],
            tags=["data_quality", "source"],
        ))

        return insights

    def learn_competitive(self) -> List[MetaInsight]:
        """Analyze competitive intelligence patterns."""
        insights: List[MetaInsight] = []

        # --- Competitor activity by program (sorted by month) ---
        comp_prog_raw: Dict[str, Dict[str, List[Dict]]] = {}
        for entry in _COMPETITOR_ACTIVITY:
            comp = entry["competitor"]
            prog = entry["program"]
            comp_prog_raw.setdefault(comp, {}).setdefault(prog, []).append(entry)

        comp_prog: Dict[str, Dict[str, List[int]]] = {}
        for comp, programs in comp_prog_raw.items():
            comp_prog[comp] = {}
            for prog, entries in programs.items():
                sorted_entries = sorted(entries, key=lambda e: e["month"])
                comp_prog[comp][prog] = [e["postings"] for e in sorted_entries]

        for competitor, programs in comp_prog.items():
            for program, postings in programs.items():
                if len(postings) >= 2:
                    trend_delta = postings[-1] - postings[0]
                    if trend_delta > 3:
                        insights.append(MetaInsight(
                            domain=InsightDomain.COMPETITIVE.value,
                            title=f"{competitor} ramping up on {program}",
                            description=(
                                f"{competitor} increased postings from {postings[0]} to "
                                f"{postings[-1]} for {program}"
                            ),
                            severity=InsightSeverity.HIGH.value,
                            confidence=0.75,
                            recommendations=[
                                f"Monitor {competitor}'s {program} strategy",
                                f"Consider competitive positioning response",
                            ],
                            tags=["competitive", competitor.lower(), program.lower()],
                        ))
                    elif postings[-1] == 0 and postings[0] > 0:
                        insights.append(MetaInsight(
                            domain=InsightDomain.COMPETITIVE.value,
                            title=f"{competitor} exiting {program}",
                            description=(
                                f"{competitor} dropped from {postings[0]} to 0 postings on {program}"
                            ),
                            severity=InsightSeverity.CRITICAL.value,
                            confidence=0.70,
                            recommendations=[
                                f"Immediate BD opportunity — fill gap left by {competitor}",
                            ],
                            tags=["competitive", "exit", competitor.lower(), program.lower()],
                        ))

        return insights

    # --------------------------------------------------
    # TRANSFER LEARNING
    # --------------------------------------------------

    def transfer_learning(self, source_program: str, target_program: str) -> TransferReport:
        """Transfer knowledge from one program to another."""
        # Gather insights about source
        source_insights = [
            i for i in self._insights
            if (isinstance(i, ProgramInsight) and i.program_name.lower() == source_program.lower())
            or source_program.lower() in [t.lower() for t in i.tags]
        ]

        # Compute similarity (simple heuristic: shared tags / total tags)
        source_tags = set()
        for i in source_insights:
            source_tags.update(t.lower() for t in i.tags)

        target_tags = {target_program.lower(), "program"}
        overlap = source_tags & target_tags
        similarity = len(overlap) / max(len(source_tags | target_tags), 1)

        # Generate transferable insights
        transferable: List[MetaInsight] = []
        approaches: List[str] = []
        for insight in source_insights:
            adapted = MetaInsight(
                domain=insight.domain,
                title=f"[Transfer] {insight.title}",
                description=f"Adapted from {source_program}: {insight.description}",
                severity=insight.severity,
                confidence=insight.confidence * 0.7,  # reduce confidence for transfer
                recommendations=[
                    f"Apply to {target_program}: {r}" for r in insight.recommendations
                ],
                tags=insight.tags + ["transfer", target_program.lower()],
            )
            transferable.append(adapted)
            approaches.extend(adapted.recommendations)

        report = TransferReport(
            source_program=source_program,
            target_program=target_program,
            transferable_insights=transferable,
            similarity_score=round(similarity, 2),
            recommended_approaches=approaches[:5],
            caveats=[
                f"Similarity score {similarity:.0%} — insights may need adaptation",
                f"Confidence reduced by 30% for transferred insights",
            ],
        )
        self._transfer_reports.append(report)
        return report

    # --------------------------------------------------
    # QUERIES
    # --------------------------------------------------

    def get_insights(self, domain: str = "", severity: str = "") -> List[MetaInsight]:
        """Get insights with optional filtering."""
        results = list(self._insights)
        if domain:
            results = [i for i in results if i.domain == domain]
        if severity:
            results = [i for i in results if i.severity == severity]
        return results

    def get_outreach_effectiveness(self) -> Dict[str, Any]:
        """Get outreach effectiveness summary."""
        channel_stats: Dict[str, Dict[str, Any]] = {}
        for entry in _OUTREACH_LOG:
            ch = entry["channel"]
            if ch not in channel_stats:
                channel_stats[ch] = {"attempts": 0, "responses": 0, "tiers": {}}
            channel_stats[ch]["attempts"] += 1
            if entry["responded"]:
                channel_stats[ch]["responses"] += 1
            tier = str(entry["tier"])
            channel_stats[ch]["tiers"].setdefault(tier, {"attempts": 0, "responses": 0})
            channel_stats[ch]["tiers"][tier]["attempts"] += 1
            if entry["responded"]:
                channel_stats[ch]["tiers"][tier]["responses"] += 1

        for ch_data in channel_stats.values():
            ch_data["response_rate"] = round(
                ch_data["responses"] / max(ch_data["attempts"], 1), 2
            )
            for tier_data in ch_data["tiers"].values():
                tier_data["response_rate"] = round(
                    tier_data["responses"] / max(tier_data["attempts"], 1), 2
                )

        return {
            "channels": channel_stats,
            "total_attempts": len(_OUTREACH_LOG),
            "total_responses": sum(1 for e in _OUTREACH_LOG if e["responded"]),
            "overall_rate": round(
                sum(1 for e in _OUTREACH_LOG if e["responded"]) / max(len(_OUTREACH_LOG), 1), 2
            ),
        }

    def get_campaign_effectiveness(self) -> Dict[str, Any]:
        """Get campaign-level effectiveness summary."""
        # Group outreach by channel as proxy campaigns
        campaigns: Dict[str, Dict[str, Any]] = {}
        for entry in _OUTREACH_LOG:
            campaign_id = f"campaign_{entry['channel']}"
            if campaign_id not in campaigns:
                campaigns[campaign_id] = {
                    "id": campaign_id,
                    "channel": entry["channel"],
                    "total_sent": 0,
                    "total_responded": 0,
                    "by_tier": {},
                }
            campaigns[campaign_id]["total_sent"] += 1
            if entry["responded"]:
                campaigns[campaign_id]["total_responded"] += 1

        for c in campaigns.values():
            c["response_rate"] = round(
                c["total_responded"] / max(c["total_sent"], 1), 2
            )

        return {
            "campaigns": list(campaigns.values()),
            "total_campaigns": len(campaigns),
        }

    def get_competitive_trends(self) -> Dict[str, Any]:
        """Get competitive intelligence trends."""
        by_competitor: Dict[str, Dict[str, Any]] = {}
        for entry in _COMPETITOR_ACTIVITY:
            comp = entry["competitor"]
            if comp not in by_competitor:
                by_competitor[comp] = {"programs": {}, "total_postings": 0}
            prog = entry["program"]
            by_competitor[comp]["programs"].setdefault(prog, []).append({
                "month": entry["month"],
                "postings": entry["postings"],
                "roles": entry["roles"],
            })
            by_competitor[comp]["total_postings"] += entry["postings"]

        return {
            "competitors": by_competitor,
            "total_competitors": len(by_competitor),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get meta-learner statistics."""
        domain_counts: Dict[str, int] = {}
        for i in self._insights:
            domain_counts[i.domain] = domain_counts.get(i.domain, 0) + 1

        return {
            "total_insights": len(self._insights),
            "by_domain": domain_counts,
            "transfer_reports": len(self._transfer_reports),
            "data_points": {
                "outreach_log": len(_OUTREACH_LOG),
                "program_activity": len(_PROGRAM_ACTIVITY),
                "contact_events": len(_CONTACT_EVENTS),
                "competitor_activity": len(_COMPETITOR_ACTIVITY),
                "data_quality_log": len(_DATA_QUALITY_LOG),
            },
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[MetaLearningEngine] = None


def get_meta_learner() -> MetaLearningEngine:
    global _instance
    if _instance is None:
        _instance = MetaLearningEngine()
    return _instance
