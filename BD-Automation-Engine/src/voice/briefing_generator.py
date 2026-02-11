"""Phase 46A — Call Briefing Generator.

Generates pre-call intelligence briefings by synthesizing contact profile,
program pain points, recent interactions, open jobs, past performance,
recent news, suggested talking points, and relationship map.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


# =========================================
# DATA CLASSES
# =========================================

class BriefingPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    STANDARD = "standard"
    LOW = "low"


@dataclass
class ContactProfile:
    contact_id: str = ""
    name: str = ""
    title: str = ""
    company: str = ""
    program: str = ""
    tier: int = 0
    priority_score: float = 0.0
    email: str = ""
    phone: str = ""
    location: str = ""
    clearance: str = ""


@dataclass
class PainPoint:
    description: str = ""
    source: str = ""  # humint | transcript | report
    severity: str = "medium"
    first_reported: str = ""


@dataclass
class Interaction:
    interaction_type: str = ""  # call | email | meeting
    date: str = ""
    outcome: str = ""
    follow_up: str = ""
    notes: str = ""


@dataclass
class TalkingPoint:
    topic: str = ""
    context: str = ""
    suggested_opener: str = ""
    priority: str = "medium"


@dataclass
class RelationshipLink:
    contact_name: str = ""
    relationship: str = ""  # colleague | reports_to | knows
    program: str = ""
    contacted: bool = False


@dataclass
class CallBriefing:
    id: str = ""
    contact_id: str = ""
    contact: ContactProfile = field(default_factory=ContactProfile)
    pain_points: List[PainPoint] = field(default_factory=list)
    recent_interactions: List[Interaction] = field(default_factory=list)
    open_jobs: List[Dict[str, Any]] = field(default_factory=list)
    past_performance: List[Dict[str, Any]] = field(default_factory=list)
    recent_news: List[Dict[str, Any]] = field(default_factory=list)
    talking_points: List[TalkingPoint] = field(default_factory=list)
    relationship_map: List[RelationshipLink] = field(default_factory=list)
    priority: str = "standard"
    summary: str = ""
    created_at: str = ""
    duration_estimate_sec: int = 0

    def __post_init__(self):
        if not self.id:
            raw = f"briefing:{self.contact_id}:{datetime.utcnow().isoformat()}"
            self.id = f"brief_{hashlib.md5(raw.encode()).hexdigest()[:10]}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class AudioBriefing:
    id: str = ""
    briefing_id: str = ""
    format: str = "mp3"
    duration_sec: int = 0
    size_bytes: int = 0
    text_script: str = ""
    audio_url: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            raw = f"audio:{self.briefing_id}:{datetime.utcnow().isoformat()}"
            self.id = f"audio_{hashlib.md5(raw.encode()).hexdigest()[:10]}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


# =========================================
# SIMULATED DATA
# =========================================

_CONTACTS: Dict[str, Dict[str, Any]] = {
    "c001": {
        "name": "Craig Lindahl", "title": "VP Engineering", "company": "Leidos",
        "program": "DCGS-A", "tier": 1, "priority_score": 92.5,
        "email": "c.lindahl@leidos.com", "phone": "703-555-0101",
        "location": "Langley AFB, VA", "clearance": "TS/SCI",
    },
    "c002": {
        "name": "Sarah Mitchell", "title": "Site Lead", "company": "Northrop Grumman",
        "program": "GBSD", "tier": 2, "priority_score": 78.0,
        "email": "s.mitchell@ngc.com", "phone": "801-555-0202",
        "location": "Hill AFB, UT", "clearance": "Secret",
    },
    "c003": {
        "name": "James Patel", "title": "Program Manager", "company": "Raytheon",
        "program": "DCGS-N", "tier": 1, "priority_score": 88.0,
        "email": "j.patel@rtx.com", "phone": "619-555-0303",
        "location": "San Diego, CA", "clearance": "TS/SCI",
    },
    "c004": {
        "name": "Amanda Chen", "title": "Systems Architect", "company": "BAE Systems",
        "program": "DCGS-A", "tier": 3, "priority_score": 65.0,
        "email": "a.chen@baesystems.com", "phone": "703-555-0404",
        "location": "Langley AFB, VA", "clearance": "TS",
    },
}

_PAIN_POINTS: Dict[str, List[Dict[str, Any]]] = {
    "c001": [
        {"description": "Struggling to fill senior cloud architect positions", "source": "humint", "severity": "high"},
        {"description": "Current SIGINT processing pipeline has latency issues", "source": "transcript", "severity": "critical"},
    ],
    "c002": [
        {"description": "Need cleared cybersecurity talent in Utah", "source": "humint", "severity": "high"},
    ],
    "c003": [
        {"description": "Navy DCGS modernization behind schedule", "source": "report", "severity": "critical"},
        {"description": "Integration challenges with legacy GCCS-J", "source": "transcript", "severity": "high"},
    ],
}

_INTERACTIONS: Dict[str, List[Dict[str, Any]]] = {
    "c001": [
        {"type": "call", "date": "2025-12-15", "outcome": "positive", "follow_up": "Send staffing proposal by Jan 5", "notes": "Discussed cloud migration timeline"},
        {"type": "email", "date": "2025-12-20", "outcome": "neutral", "follow_up": "", "notes": "Sent holiday greeting"},
    ],
    "c003": [
        {"type": "meeting", "date": "2025-11-10", "outcome": "positive", "follow_up": "Schedule follow-up demo in Q1 2026", "notes": "Demo'd data fusion capabilities"},
    ],
}

_OPEN_JOBS: Dict[str, List[Dict[str, Any]]] = {
    "DCGS-A": [
        {"title": "Senior Cloud Architect", "location": "Langley AFB", "clearance": "TS/SCI", "posted": "2025-12-01"},
        {"title": "SIGINT Analyst", "location": "Langley AFB", "clearance": "TS/SCI", "posted": "2025-12-10"},
        {"title": "Systems Engineer", "location": "Langley AFB", "clearance": "TS", "posted": "2026-01-05"},
    ],
    "GBSD": [
        {"title": "Cybersecurity Engineer", "location": "Hill AFB", "clearance": "Secret", "posted": "2026-01-15"},
    ],
    "DCGS-N": [
        {"title": "Software Developer", "location": "San Diego", "clearance": "TS/SCI", "posted": "2025-12-20"},
        {"title": "Integration Engineer", "location": "San Diego", "clearance": "TS", "posted": "2026-01-10"},
    ],
}

_PAST_PERFORMANCE: Dict[str, List[Dict[str, Any]]] = {
    "DCGS-A": [
        {"project": "DCGS Cloud Migration Phase 1", "role": "Prime", "value_m": 12.5, "period": "2023-2024", "rating": "Exceptional"},
        {"project": "ISR Data Fusion Prototype", "role": "Sub", "value_m": 3.2, "period": "2024", "rating": "Very Good"},
    ],
    "GBSD": [
        {"project": "ICBM Test Infrastructure Support", "role": "Sub", "value_m": 5.8, "period": "2023-2025", "rating": "Satisfactory"},
    ],
    "DCGS-N": [
        {"project": "Navy Maritime ISR Analysis", "role": "Sub", "value_m": 8.1, "period": "2024-2025", "rating": "Very Good"},
    ],
}

_RECENT_NEWS: Dict[str, List[Dict[str, Any]]] = {
    "DCGS-A": [
        {"headline": "Leidos wins $200M DCGS-A sustainment extension", "date": "2026-01-15", "source": "Defense News"},
        {"headline": "AF DCGS migrating to AWS GovCloud in FY26", "date": "2025-12-20", "source": "C4ISRNET"},
    ],
    "DCGS-N": [
        {"headline": "Navy DCGS-N re-compete RFI expected Q2 2026", "date": "2026-01-10", "source": "FedBizOpps"},
    ],
}

_RELATIONSHIPS: Dict[str, List[Dict[str, Any]]] = {
    "c001": [
        {"contact_name": "Amanda Chen", "relationship": "colleague", "program": "DCGS-A", "contacted": True},
        {"contact_name": "Bob Franklin", "relationship": "reports_to", "program": "DCGS-A", "contacted": False},
    ],
    "c003": [
        {"contact_name": "Lisa Wong", "relationship": "colleague", "program": "DCGS-N", "contacted": True},
    ],
}


# =========================================
# CALL BRIEFING GENERATOR
# =========================================

class CallBriefingGenerator:
    """Generates pre-call intelligence briefings."""

    def __init__(self) -> None:
        self._briefings: Dict[str, CallBriefing] = {}
        self._audio_briefings: Dict[str, AudioBriefing] = {}

    # --------------------------------------------------
    # BRIEFING GENERATION
    # --------------------------------------------------

    def generate_briefing(self, contact_id: str) -> CallBriefing:
        """Generate a comprehensive pre-call briefing."""
        contact_data = _CONTACTS.get(contact_id)
        if not contact_data:
            return CallBriefing(
                contact_id=contact_id,
                summary=f"Contact {contact_id} not found",
                priority="low",
            )

        # Build contact profile
        contact = ContactProfile(
            contact_id=contact_id,
            **contact_data,
        )

        # Gather pain points
        pain_points = [
            PainPoint(
                description=pp["description"],
                source=pp["source"],
                severity=pp["severity"],
            )
            for pp in _PAIN_POINTS.get(contact_id, [])
        ]

        # Gather recent interactions
        interactions = [
            Interaction(
                interaction_type=ix["type"],
                date=ix["date"],
                outcome=ix["outcome"],
                follow_up=ix.get("follow_up", ""),
                notes=ix.get("notes", ""),
            )
            for ix in _INTERACTIONS.get(contact_id, [])
        ]

        # Gather open jobs for their program
        program = contact_data["program"]
        open_jobs = _OPEN_JOBS.get(program, [])

        # Past performance
        past_perf = _PAST_PERFORMANCE.get(program, [])

        # Recent news
        news = _RECENT_NEWS.get(program, [])

        # Relationships
        relationships = [
            RelationshipLink(**rel)
            for rel in _RELATIONSHIPS.get(contact_id, [])
        ]

        # Generate talking points
        talking_points = self._generate_talking_points(contact, pain_points, interactions, open_jobs)

        # Determine priority
        priority = self._determine_priority(contact, pain_points, interactions)

        # Build summary
        summary = self._build_summary(contact, pain_points, interactions, open_jobs)

        # Estimate duration (roughly 15 sec per section with content)
        sections_with_data = sum([
            1,  # contact profile always
            1 if pain_points else 0,
            1 if interactions else 0,
            1 if open_jobs else 0,
            1 if past_perf else 0,
            1 if news else 0,
            1 if talking_points else 0,
        ])
        duration_estimate = sections_with_data * 12

        briefing = CallBriefing(
            contact_id=contact_id,
            contact=contact,
            pain_points=pain_points,
            recent_interactions=interactions,
            open_jobs=open_jobs,
            past_performance=past_perf,
            recent_news=news,
            talking_points=talking_points,
            relationship_map=relationships,
            priority=priority,
            summary=summary,
            duration_estimate_sec=duration_estimate,
        )
        self._briefings[briefing.id] = briefing
        return briefing

    def generate_batch(self, contact_ids: List[str]) -> List[CallBriefing]:
        """Generate briefings for a batch of contacts (call sheet)."""
        return [self.generate_briefing(cid) for cid in contact_ids]

    def _generate_talking_points(
        self,
        contact: ContactProfile,
        pain_points: List[PainPoint],
        interactions: List[Interaction],
        open_jobs: List[Dict],
    ) -> List[TalkingPoint]:
        """Generate BD-formula talking points."""
        points: List[TalkingPoint] = []

        # Opening — reference last interaction
        if interactions:
            last = interactions[0]
            points.append(TalkingPoint(
                topic="Relationship Continuity",
                context=f"Last {last.interaction_type} on {last.date}: {last.notes}",
                suggested_opener=f"Following up on our {last.interaction_type} — {last.notes}",
                priority="high",
            ))

        # Pain point discussion
        for pp in pain_points[:2]:
            points.append(TalkingPoint(
                topic=f"Pain Point: {pp.description[:50]}",
                context=f"Source: {pp.source}, Severity: {pp.severity}",
                suggested_opener=f"I understand {contact.program} is dealing with {pp.description.lower()}",
                priority="high" if pp.severity == "critical" else "medium",
            ))

        # Staffing opportunity
        if open_jobs:
            points.append(TalkingPoint(
                topic="Staffing Support",
                context=f"{len(open_jobs)} open positions for {contact.program}",
                suggested_opener=f"I noticed {contact.program} has {len(open_jobs)} open positions — GDIT has strong cleared talent pipeline",
                priority="high",
            ))

        # Follow-up items
        pending = [ix for ix in interactions if ix.follow_up]
        for ix in pending[:1]:
            points.append(TalkingPoint(
                topic="Follow-up Item",
                context=ix.follow_up,
                suggested_opener=f"I wanted to close the loop on {ix.follow_up.lower()}",
                priority="high",
            ))

        return points

    def _determine_priority(
        self,
        contact: ContactProfile,
        pain_points: List[PainPoint],
        interactions: List[Interaction],
    ) -> str:
        """Determine briefing priority based on contact importance and signals."""
        if contact.tier == 1 and any(pp.severity == "critical" for pp in pain_points):
            return BriefingPriority.CRITICAL.value
        if contact.tier <= 2 and pain_points:
            return BriefingPriority.HIGH.value
        if contact.tier <= 3:
            return BriefingPriority.STANDARD.value
        return BriefingPriority.LOW.value

    def _build_summary(
        self,
        contact: ContactProfile,
        pain_points: List[PainPoint],
        interactions: List[Interaction],
        open_jobs: List[Dict],
    ) -> str:
        """Build a one-paragraph executive summary."""
        parts = [
            f"{contact.name} ({contact.title}, {contact.company}) — "
            f"Tier {contact.tier}, {contact.program}."
        ]
        if pain_points:
            parts.append(f"{len(pain_points)} known pain point(s).")
        if interactions:
            parts.append(f"Last contact: {interactions[0].date} ({interactions[0].outcome}).")
        if open_jobs:
            parts.append(f"{len(open_jobs)} open positions for {contact.program}.")

        return " ".join(parts)

    # --------------------------------------------------
    # AUDIO BRIEFING
    # --------------------------------------------------

    def generate_audio_briefing(self, briefing: CallBriefing) -> AudioBriefing:
        """Generate a 60-90 second audio briefing script and simulated audio."""
        script_parts: List[str] = []

        # Intro
        script_parts.append(
            f"Pre-call briefing for {briefing.contact.name}, "
            f"{briefing.contact.title} at {briefing.contact.company}, "
            f"{briefing.contact.program} program."
        )

        # Pain points
        if briefing.pain_points:
            pps = "; ".join(pp.description for pp in briefing.pain_points[:2])
            script_parts.append(f"Key pain points: {pps}.")

        # Last interaction
        if briefing.recent_interactions:
            last = briefing.recent_interactions[0]
            script_parts.append(
                f"Last contact was a {last.interaction_type} on {last.date}, "
                f"outcome was {last.outcome}."
            )
            if last.follow_up:
                script_parts.append(f"Outstanding follow-up: {last.follow_up}.")

        # Open jobs
        if briefing.open_jobs:
            script_parts.append(
                f"There are {len(briefing.open_jobs)} open positions on {briefing.contact.program}."
            )

        # Talking points
        if briefing.talking_points:
            script_parts.append("Recommended talking points:")
            for tp in briefing.talking_points[:3]:
                script_parts.append(f"  {tp.topic}: {tp.suggested_opener}")

        script = " ".join(script_parts)

        # Estimate duration (avg 150 words per minute for TTS)
        word_count = len(script.split())
        duration_sec = max(int(word_count / 2.5), 30)  # ~2.5 words/sec

        # Simulate audio generation
        audio = AudioBriefing(
            briefing_id=briefing.id,
            format="mp3",
            duration_sec=duration_sec,
            size_bytes=duration_sec * 16000,  # ~16KB/sec for mp3
            text_script=script,
            audio_url=f"/api/voice/audio/{briefing.id}.mp3",
        )
        self._audio_briefings[audio.id] = audio
        return audio

    # --------------------------------------------------
    # QUERIES
    # --------------------------------------------------

    def get_briefing(self, briefing_id: str) -> Optional[CallBriefing]:
        return self._briefings.get(briefing_id)

    def get_briefings_for_contact(self, contact_id: str) -> List[CallBriefing]:
        return [b for b in self._briefings.values() if b.contact_id == contact_id]

    def get_audio(self, audio_id: str) -> Optional[AudioBriefing]:
        return self._audio_briefings.get(audio_id)

    def get_audio_for_briefing(self, briefing_id: str) -> Optional[AudioBriefing]:
        for audio in self._audio_briefings.values():
            if audio.briefing_id == briefing_id:
                return audio
        return None

    def get_stats(self) -> Dict[str, Any]:
        priorities: Dict[str, int] = {}
        for b in self._briefings.values():
            priorities[b.priority] = priorities.get(b.priority, 0) + 1

        return {
            "total_briefings": len(self._briefings),
            "total_audio": len(self._audio_briefings),
            "by_priority": priorities,
            "contacts_available": len(_CONTACTS),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[CallBriefingGenerator] = None


def get_briefing_generator() -> CallBriefingGenerator:
    global _instance
    if _instance is None:
        _instance = CallBriefingGenerator()
    return _instance
