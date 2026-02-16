"""Phase 46A — Transcript Intelligence Extractor.

Processes call transcripts to extract pain points, job openings,
contact mentions, budget signals, competitor mentions, sentiment,
and action items. Handles Vapi webhook payloads.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# =========================================
# ENUMS & DATA CLASSES
# =========================================


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class IntelType(str, Enum):
    PAIN_POINT = "pain_point"
    JOB_OPENING = "job_opening"
    CONTACT_MENTION = "contact_mention"
    BUDGET_SIGNAL = "budget_signal"
    COMPETITOR_MENTION = "competitor_mention"
    CONTRACT_SIGNAL = "contract_signal"
    ACTION_ITEM = "action_item"


@dataclass
class ExtractedIntel:
    intel_type: str = ""
    content: str = ""
    confidence: float = 0.0
    context: str = ""
    source_segment: str = ""


@dataclass
class ActionItem:
    description: str = ""
    owner: str = ""  # "us" or "them"
    due_date: str = ""
    priority: str = "medium"
    status: str = "open"


@dataclass
class TranscriptIntel:
    id: str = ""
    call_id: str = ""
    contact_id: str = ""
    transcript_length: int = 0
    duration_sec: int = 0
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    pain_points: List[ExtractedIntel] = field(default_factory=list)
    job_openings: List[ExtractedIntel] = field(default_factory=list)
    contact_mentions: List[ExtractedIntel] = field(default_factory=list)
    budget_signals: List[ExtractedIntel] = field(default_factory=list)
    competitor_mentions: List[ExtractedIntel] = field(default_factory=list)
    contract_signals: List[ExtractedIntel] = field(default_factory=list)
    action_items: List[ActionItem] = field(default_factory=list)
    key_topics: List[str] = field(default_factory=list)
    summary: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            raw = f"intel:{self.call_id}:{datetime.utcnow().isoformat()}"
            self.id = f"tintel_{hashlib.md5(raw.encode()).hexdigest()[:10]}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    @property
    def total_intel_items(self) -> int:
        return (
            len(self.pain_points)
            + len(self.job_openings)
            + len(self.contact_mentions)
            + len(self.budget_signals)
            + len(self.competitor_mentions)
            + len(self.contract_signals)
            + len(self.action_items)
        )


@dataclass
class CallRecord:
    call_id: str = ""
    contact_id: str = ""
    transcript: str = ""
    duration_sec: int = 0
    intel: Optional[TranscriptIntel] = None
    source: str = "manual"  # manual | vapi | zoom
    created_at: str = ""

    def __post_init__(self):
        if not self.call_id:
            raw = f"call:{self.contact_id}:{datetime.utcnow().isoformat()}"
            self.call_id = f"call_{hashlib.md5(raw.encode()).hexdigest()[:10]}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


# =========================================
# KEYWORD PATTERNS FOR EXTRACTION
# =========================================

_PAIN_KEYWORDS = [
    "struggling",
    "challenge",
    "problem",
    "issue",
    "difficult",
    "behind schedule",
    "understaffed",
    "can't find",
    "need help",
    "short-staffed",
    "overworked",
    "frustrated",
    "bottleneck",
    "latency",
    "outage",
    "downtime",
]

_JOB_KEYWORDS = [
    "hiring",
    "open position",
    "looking for",
    "staffing",
    "need to fill",
    "vacancy",
    "recruiting",
    "new role",
    "headcount",
    "req open",
    "posting",
]

_BUDGET_KEYWORDS = [
    "budget",
    "funding",
    "fiscal year",
    "appropriation",
    "spend authority",
    "allocation",
    "cost ceiling",
    "contract value",
    "ceiling increase",
    "obligated",
]

_COMPETITOR_NAMES = [
    "Leidos",
    "Northrop",
    "Raytheon",
    "BAE",
    "Booz Allen",
    "Peraton",
    "SAIC",
    "ManTech",
    "L3Harris",
    "Lockheed",
    "General Dynamics",
    "CACI",
    "Accenture Federal",
]

_CONTRACT_KEYWORDS = [
    "recompete",
    "option year",
    "re-compete",
    "task order",
    "IDIQ",
    "BPA",
    "contract award",
    "period of performance",
    "transition",
    "incumbent",
    "protest",
]

_ACTION_KEYWORDS = [
    "send me",
    "follow up",
    "schedule",
    "set up a meeting",
    "get back to",
    "will provide",
    "action item",
    "next steps",
    "let me check",
    "i'll send",
    "due by",
    "by friday",
    "by next week",
    "by end of month",
]

_POSITIVE_WORDS = [
    "great",
    "excellent",
    "appreciate",
    "thank",
    "excited",
    "impressed",
    "looking forward",
    "absolutely",
    "perfect",
    "wonderful",
    "fantastic",
    "glad",
]

_NEGATIVE_WORDS = [
    "disappointed",
    "frustrated",
    "concerned",
    "worried",
    "unacceptable",
    "unfortunately",
    "regret",
    "unhappy",
    "angry",
    "terrible",
    "awful",
    "failing",
]


# =========================================
# TRANSCRIPT INTELLIGENCE EXTRACTOR
# =========================================


class TranscriptIntelligenceExtractor:
    """Extracts actionable intelligence from call transcripts."""

    def __init__(self) -> None:
        self._analyses: Dict[str, TranscriptIntel] = {}
        self._calls: Dict[str, CallRecord] = {}
        self._call_counter: int = 0
        self._coaching_rules: List[Dict[str, Any]] = [
            {
                "trigger": "competitor",
                "suggestion": "Acknowledge competitor strengths, then differentiate on PTS-specific capabilities",
            },
            {
                "trigger": "budget",
                "suggestion": "Ask about timeline for funding decisions and key decision-makers",
            },
            {
                "trigger": "pain_point",
                "suggestion": "Quantify the impact — ask about downstream effects and current workarounds",
            },
            {
                "trigger": "staffing",
                "suggestion": "Mention GDIT's cleared talent pipeline and rapid staffing capability",
            },
            {
                "trigger": "recompete",
                "suggestion": "Ask about teaming strategy and whether they're open to new partners",
            },
        ]

    # --------------------------------------------------
    # ANALYSIS
    # --------------------------------------------------

    def analyze_transcript(
        self,
        transcript: str,
        contact_id: str = "",
        call_id: str = "",
        duration_sec: int = 0,
    ) -> TranscriptIntel:
        """Extract all intelligence from a transcript."""
        text_lower = transcript.lower()
        sentences = self._split_sentences(transcript)

        # Create call record with unique call_id
        self._call_counter += 1
        effective_call_id = call_id or ""
        if not effective_call_id:
            raw = f"call:{contact_id}:{self._call_counter}:{transcript[:50]}"
            effective_call_id = f"call_{hashlib.md5(raw.encode()).hexdigest()[:10]}"
        record = CallRecord(
            call_id=effective_call_id,
            contact_id=contact_id,
            transcript=transcript,
            duration_sec=duration_sec,
            source="manual",
        )

        # Extract all intelligence types
        pain_points = self._extract_by_keywords(
            sentences, _PAIN_KEYWORDS, IntelType.PAIN_POINT.value
        )
        job_openings = self._extract_by_keywords(
            sentences, _JOB_KEYWORDS, IntelType.JOB_OPENING.value
        )
        budget_signals = self._extract_by_keywords(
            sentences, _BUDGET_KEYWORDS, IntelType.BUDGET_SIGNAL.value
        )
        competitor_mentions = self._extract_competitors(sentences)
        contract_signals = self._extract_by_keywords(
            sentences, _CONTRACT_KEYWORDS, IntelType.CONTRACT_SIGNAL.value
        )
        contact_mentions = self._extract_contact_mentions(sentences)
        action_items = self._extract_action_items(sentences)

        # Sentiment analysis
        sentiment, sentiment_score = self._analyze_sentiment(text_lower)

        # Key topics
        key_topics = self._extract_topics(text_lower)

        # Summary
        summary = self._build_summary(
            contact_id,
            pain_points,
            job_openings,
            competitor_mentions,
            action_items,
            sentiment,
        )

        intel = TranscriptIntel(
            call_id=record.call_id,
            contact_id=contact_id,
            transcript_length=len(transcript),
            duration_sec=duration_sec,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            pain_points=pain_points,
            job_openings=job_openings,
            contact_mentions=contact_mentions,
            budget_signals=budget_signals,
            competitor_mentions=competitor_mentions,
            contract_signals=contract_signals,
            action_items=action_items,
            key_topics=key_topics,
            summary=summary,
        )

        record.intel = intel
        self._analyses[intel.id] = intel
        self._calls[record.call_id] = record
        return intel

    def process_vapi_webhook(self, webhook_data: Dict[str, Any]) -> TranscriptIntel:
        """Handle Vapi post-call webhook with transcript."""
        transcript = webhook_data.get("transcript", "")
        contact_id = webhook_data.get(
            "contact_id", webhook_data.get("metadata", {}).get("contact_id", "")
        )
        call_id = webhook_data.get("call_id", webhook_data.get("id", ""))
        duration = webhook_data.get("duration_seconds", webhook_data.get("duration", 0))

        intel = self.analyze_transcript(
            transcript=transcript,
            contact_id=contact_id,
            call_id=call_id,
            duration_sec=int(duration),
        )

        # Mark source as vapi
        if call_id in self._calls:
            self._calls[call_id].source = "vapi"

        return intel

    # --------------------------------------------------
    # EXTRACTION HELPERS
    # --------------------------------------------------

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences, preserving honorifics like Mr./Dr."""
        # Protect honorifics from sentence splitting
        protected = re.sub(r"\b(Mr|Ms|Mrs|Dr)\.\s", r"\1_DOT_ ", text)
        parts = re.split(r"[.!?]+", protected)
        # Restore honorifics
        return [s.strip().replace("_DOT_", ".") for s in parts if s.strip()]

    def _extract_by_keywords(
        self, sentences: List[str], keywords: List[str], intel_type: str
    ) -> List[ExtractedIntel]:
        """Extract intelligence items by keyword matching."""
        results: List[ExtractedIntel] = []
        for sentence in sentences:
            s_lower = sentence.lower()
            matched = [kw for kw in keywords if kw in s_lower]
            if matched:
                results.append(
                    ExtractedIntel(
                        intel_type=intel_type,
                        content=sentence,
                        confidence=min(0.5 + len(matched) * 0.15, 0.95),
                        context=f"Matched keywords: {', '.join(matched[:3])}",
                        source_segment=sentence,
                    )
                )
        return results

    def _extract_competitors(self, sentences: List[str]) -> List[ExtractedIntel]:
        """Extract competitor mentions."""
        results: List[ExtractedIntel] = []
        for sentence in sentences:
            for comp in _COMPETITOR_NAMES:
                if comp.lower() in sentence.lower():
                    results.append(
                        ExtractedIntel(
                            intel_type=IntelType.COMPETITOR_MENTION.value,
                            content=sentence,
                            confidence=0.90,
                            context=f"Competitor: {comp}",
                            source_segment=sentence,
                        )
                    )
                    break  # one per sentence
        return results

    def _extract_contact_mentions(self, sentences: List[str]) -> List[ExtractedIntel]:
        """Extract mentions of other people (names)."""
        results: List[ExtractedIntel] = []
        # Simple heuristic: look for "Mr./Ms./Dr." or "Name Last" patterns
        name_pattern = re.compile(r"\b(?:Mr|Ms|Mrs|Dr)\.?\s+[A-Z][a-z]+\b")
        for sentence in sentences:
            matches = name_pattern.findall(sentence)
            for match in matches:
                results.append(
                    ExtractedIntel(
                        intel_type=IntelType.CONTACT_MENTION.value,
                        content=match,
                        confidence=0.70,
                        context=sentence,
                        source_segment=sentence,
                    )
                )
        return results

    def _extract_action_items(self, sentences: List[str]) -> List[ActionItem]:
        """Extract action items from transcript."""
        items: List[ActionItem] = []
        for sentence in sentences:
            s_lower = sentence.lower()
            matched = [kw for kw in _ACTION_KEYWORDS if kw in s_lower]
            if matched:
                # Determine owner
                owner = (
                    "us"
                    if any(
                        w in s_lower
                        for w in ["i'll", "we'll", "let me", "i will", "we will"]
                    )
                    else "them"
                )

                # Try to find due date
                due = ""
                if "by friday" in s_lower:
                    due = "Friday"
                elif "next week" in s_lower:
                    due = "Next week"
                elif "end of month" in s_lower:
                    due = "End of month"

                items.append(
                    ActionItem(
                        description=sentence,
                        owner=owner,
                        due_date=due,
                        priority="high"
                        if "asap" in s_lower or "urgent" in s_lower
                        else "medium",
                    )
                )
        return items

    def _analyze_sentiment(self, text_lower: str) -> tuple:
        """Simple keyword-based sentiment analysis."""
        pos_count = sum(1 for w in _POSITIVE_WORDS if w in text_lower)
        neg_count = sum(1 for w in _NEGATIVE_WORDS if w in text_lower)

        total = pos_count + neg_count
        if total == 0:
            return Sentiment.NEUTRAL.value, 0.5

        score = pos_count / total
        if score > 0.6:
            return Sentiment.POSITIVE.value, round(score, 2)
        elif score < 0.4:
            return Sentiment.NEGATIVE.value, round(score, 2)
        else:
            return Sentiment.NEUTRAL.value, round(score, 2)

    def _extract_topics(self, text_lower: str) -> List[str]:
        """Extract key topics from the conversation."""
        topic_keywords = {
            "staffing": ["hiring", "staffing", "headcount", "position", "vacancy"],
            "cloud_migration": ["cloud", "aws", "azure", "migration", "govcloud"],
            "cybersecurity": ["cyber", "security", "compliance", "ato", "stig"],
            "data_fusion": ["data fusion", "analytics", "machine learning", "ai", "ml"],
            "contract": ["contract", "recompete", "option year", "task order", "idiq"],
            "budget": ["budget", "funding", "fiscal", "appropriation"],
            "timeline": ["timeline", "schedule", "milestone", "deadline"],
            "integration": ["integration", "interface", "api", "interoperability"],
        }
        topics: List[str] = []
        for topic, kws in topic_keywords.items():
            if any(kw in text_lower for kw in kws):
                topics.append(topic)
        return topics

    def _build_summary(
        self,
        contact_id: str,
        pain_points: List[ExtractedIntel],
        job_openings: List[ExtractedIntel],
        competitors: List[ExtractedIntel],
        action_items: List[ActionItem],
        sentiment: str,
    ) -> str:
        parts = [f"Call with {contact_id}: sentiment {sentiment}."]
        if pain_points:
            parts.append(f"{len(pain_points)} pain point(s) identified.")
        if job_openings:
            parts.append(f"{len(job_openings)} staffing need(s) discussed.")
        if competitors:
            parts.append(f"{len(competitors)} competitor mention(s).")
        if action_items:
            parts.append(f"{len(action_items)} action item(s).")
        return " ".join(parts)

    # --------------------------------------------------
    # COACHING
    # --------------------------------------------------

    def get_coaching_suggestions(self, transcript: str) -> List[Dict[str, Any]]:
        """Generate real-time coaching suggestions based on transcript content."""
        text_lower = transcript.lower()
        suggestions: List[Dict[str, Any]] = []

        if any(comp.lower() in text_lower for comp in _COMPETITOR_NAMES):
            suggestions.append(self._coaching_rules[0])
        if any(kw in text_lower for kw in _BUDGET_KEYWORDS[:3]):
            suggestions.append(self._coaching_rules[1])
        if any(kw in text_lower for kw in _PAIN_KEYWORDS[:5]):
            suggestions.append(self._coaching_rules[2])
        if any(kw in text_lower for kw in _JOB_KEYWORDS[:4]):
            suggestions.append(self._coaching_rules[3])
        if any(kw in text_lower for kw in _CONTRACT_KEYWORDS[:3]):
            suggestions.append(self._coaching_rules[4])

        return suggestions

    # --------------------------------------------------
    # QUERIES
    # --------------------------------------------------

    def get_analysis(self, intel_id: str) -> Optional[TranscriptIntel]:
        return self._analyses.get(intel_id)

    def get_call(self, call_id: str) -> Optional[CallRecord]:
        return self._calls.get(call_id)

    def get_call_history(self, contact_id: str) -> List[CallRecord]:
        return [c for c in self._calls.values() if c.contact_id == contact_id]

    def get_recent_intel(self, limit: int = 20) -> List[TranscriptIntel]:
        intels = sorted(
            self._analyses.values(), key=lambda i: i.created_at, reverse=True
        )
        return intels[:limit]

    def get_all_pain_points(self) -> List[ExtractedIntel]:
        results: List[ExtractedIntel] = []
        for intel in self._analyses.values():
            results.extend(intel.pain_points)
        return results

    def get_all_action_items(self, status: str = "") -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for intel in self._analyses.values():
            for ai in intel.action_items:
                if not status or ai.status == status:
                    items.append(
                        {
                            "call_id": intel.call_id,
                            "contact_id": intel.contact_id,
                            "description": ai.description,
                            "owner": ai.owner,
                            "due_date": ai.due_date,
                            "priority": ai.priority,
                            "status": ai.status,
                        }
                    )
        return items

    def get_analytics(self) -> Dict[str, Any]:
        """Call analytics: volume, duration, sentiment trends."""
        total_calls = len(self._calls)
        total_duration = sum(c.duration_sec for c in self._calls.values())
        sentiments: Dict[str, int] = {}
        for intel in self._analyses.values():
            sentiments[intel.sentiment] = sentiments.get(intel.sentiment, 0) + 1

        total_intel = sum(intel.total_intel_items for intel in self._analyses.values())

        return {
            "total_calls": total_calls,
            "total_duration_sec": total_duration,
            "avg_duration_sec": round(total_duration / max(total_calls, 1), 1),
            "sentiment_distribution": sentiments,
            "total_intel_extracted": total_intel,
            "total_pain_points": sum(
                len(i.pain_points) for i in self._analyses.values()
            ),
            "total_action_items": sum(
                len(i.action_items) for i in self._analyses.values()
            ),
            "total_competitor_mentions": sum(
                len(i.competitor_mentions) for i in self._analyses.values()
            ),
            "sources": self._count_by_source(),
        }

    def _count_by_source(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for c in self._calls.values():
            counts[c.source] = counts.get(c.source, 0) + 1
        return counts

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_analyses": len(self._analyses),
            "total_calls": len(self._calls),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[TranscriptIntelligenceExtractor] = None


def get_transcript_analyzer() -> TranscriptIntelligenceExtractor:
    global _instance
    if _instance is None:
        _instance = TranscriptIntelligenceExtractor()
    return _instance
