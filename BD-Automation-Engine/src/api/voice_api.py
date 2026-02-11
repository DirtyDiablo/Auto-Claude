"""Phase 46A — Voice Intelligence API (12 endpoints).

REST endpoints for call briefings, transcript analysis, intelligence
extraction, coaching, and call analytics.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from src.voice.briefing_generator import (
    CallBriefingGenerator, CallBriefing, AudioBriefing,
    get_briefing_generator,
)
from src.voice.transcript_analyzer import (
    TranscriptIntelligenceExtractor, TranscriptIntel, CallRecord,
    get_transcript_analyzer,
)

logger = logging.getLogger(__name__)


# =========================================
# REQUEST MODELS
# =========================================

class BatchBriefingRequest(BaseModel):
    contact_ids: List[str]


class TranscriptRequest(BaseModel):
    transcript: str
    contact_id: str = ""
    call_id: str = ""
    duration_sec: int = 0


class VapiWebhookRequest(BaseModel):
    call_id: str = ""
    id: str = ""
    transcript: str = ""
    contact_id: str = ""
    duration_seconds: int = 0
    duration: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CoachingRequest(BaseModel):
    transcript: str


# =========================================
# ROUTE SETUP
# =========================================

def include_voice_router(app: FastAPI) -> None:
    """Register all voice intelligence endpoints on the FastAPI app."""

    briefings = get_briefing_generator()
    analyzer = get_transcript_analyzer()

    # --------------------------------------------------
    # 1. POST /api/voice/briefing/batch — Batch briefings (before {contact_id})
    # --------------------------------------------------
    @app.post("/api/voice/briefing/batch")
    async def voice_briefing_batch(req: BatchBriefingRequest):
        """Generate briefings for a call sheet of contacts."""
        results = briefings.generate_batch(req.contact_ids)
        return {
            "briefings": [
                {
                    "contact_id": b.contact_id,
                    "briefing_id": b.id,
                    "priority": b.priority,
                    "summary": b.summary,
                }
                for b in results
            ],
            "total": len(results),
        }

    # --------------------------------------------------
    # 2. POST /api/voice/briefing/{contact_id} — Generate briefing
    # --------------------------------------------------
    @app.post("/api/voice/briefing/{contact_id}")
    async def voice_briefing(contact_id: str):
        """Generate a pre-call intelligence briefing."""
        briefing = briefings.generate_briefing(contact_id)
        audio = briefings.generate_audio_briefing(briefing)
        return _serialize_briefing(briefing, audio)

    # --------------------------------------------------
    # 3. GET /api/voice/briefing/{contact_id}/audio — Audio briefing
    # --------------------------------------------------
    @app.get("/api/voice/briefing/{contact_id}/audio")
    async def voice_briefing_audio(contact_id: str):
        """Get audio briefing for a contact."""
        recent = briefings.get_briefings_for_contact(contact_id)
        if not recent:
            raise HTTPException(404, "No briefing found for contact")
        audio = briefings.get_audio_for_briefing(recent[-1].id)
        if not audio:
            raise HTTPException(404, "No audio briefing available")
        return {
            "briefing_id": recent[-1].id,
            "audio_id": audio.id,
            "format": audio.format,
            "duration_sec": audio.duration_sec,
            "size_bytes": audio.size_bytes,
            "text_script": audio.text_script,
            "audio_url": audio.audio_url,
        }

    # --------------------------------------------------
    # 4. POST /api/voice/transcript/analyze — Analyze transcript
    # --------------------------------------------------
    @app.post("/api/voice/transcript/analyze")
    async def voice_transcript_analyze(req: TranscriptRequest):
        """Analyze an uploaded call transcript."""
        if not req.transcript.strip():
            raise HTTPException(400, "Transcript cannot be empty")
        intel = analyzer.analyze_transcript(
            transcript=req.transcript,
            contact_id=req.contact_id,
            call_id=req.call_id,
            duration_sec=req.duration_sec,
        )
        return _serialize_intel(intel)

    # --------------------------------------------------
    # 5. POST /api/voice/transcript/vapi-webhook — Vapi webhook
    # --------------------------------------------------
    @app.post("/api/voice/transcript/vapi-webhook")
    async def voice_vapi_webhook(req: VapiWebhookRequest):
        """Handle Vapi post-call webhook with transcript."""
        webhook_data = {
            "call_id": req.call_id or req.id,
            "transcript": req.transcript,
            "contact_id": req.contact_id or req.metadata.get("contact_id", ""),
            "duration_seconds": req.duration_seconds or req.duration,
            "metadata": req.metadata,
        }
        intel = analyzer.process_vapi_webhook(webhook_data)
        return _serialize_intel(intel)

    # --------------------------------------------------
    # 6. GET /api/voice/transcript/{call_id} — Get analysis
    # --------------------------------------------------
    @app.get("/api/voice/transcript/{call_id}")
    async def voice_transcript_get(call_id: str):
        """Get transcript analysis results for a call."""
        call = analyzer.get_call(call_id)
        if not call or not call.intel:
            raise HTTPException(404, "Call not found")
        return _serialize_intel(call.intel)

    # --------------------------------------------------
    # 7. GET /api/voice/history/{contact_id} — Call history
    # --------------------------------------------------
    @app.get("/api/voice/history/{contact_id}")
    async def voice_history(contact_id: str):
        """All call history for a contact."""
        calls = analyzer.get_call_history(contact_id)
        return {
            "contact_id": contact_id,
            "calls": [
                {
                    "call_id": c.call_id,
                    "duration_sec": c.duration_sec,
                    "source": c.source,
                    "has_intel": c.intel is not None,
                    "sentiment": c.intel.sentiment if c.intel else "",
                    "created_at": c.created_at,
                }
                for c in calls
            ],
            "total": len(calls),
        }

    # --------------------------------------------------
    # 8. GET /api/voice/intel/recent — Recent intel
    # --------------------------------------------------
    @app.get("/api/voice/intel/recent")
    async def voice_recent_intel(
        limit: int = Query(20, ge=1, le=100),
    ):
        """Recent intelligence extracted from calls."""
        intels = analyzer.get_recent_intel(limit=limit)
        return {
            "intel": [_serialize_intel_summary(i) for i in intels],
            "total": len(intels),
        }

    # --------------------------------------------------
    # 9. GET /api/voice/intel/pain-points — All pain points
    # --------------------------------------------------
    @app.get("/api/voice/intel/pain-points")
    async def voice_pain_points():
        """Aggregated pain points across all calls."""
        pps = analyzer.get_all_pain_points()
        return {
            "pain_points": [
                {"content": pp.content, "confidence": pp.confidence, "context": pp.context}
                for pp in pps
            ],
            "total": len(pps),
        }

    # --------------------------------------------------
    # 10. GET /api/voice/intel/action-items — Action items
    # --------------------------------------------------
    @app.get("/api/voice/intel/action-items")
    async def voice_action_items(
        status: str = "",
    ):
        """Outstanding action items from calls."""
        items = analyzer.get_all_action_items(status=status)
        return {
            "action_items": items,
            "total": len(items),
        }

    # --------------------------------------------------
    # 11. POST /api/voice/coaching/suggestions — Coaching
    # --------------------------------------------------
    @app.post("/api/voice/coaching/suggestions")
    async def voice_coaching(req: CoachingRequest):
        """Real-time coaching suggestions based on transcript content."""
        suggestions = analyzer.get_coaching_suggestions(req.transcript)
        return {
            "suggestions": suggestions,
            "total": len(suggestions),
        }

    # --------------------------------------------------
    # 12. GET /api/voice/analytics — Call analytics
    # --------------------------------------------------
    @app.get("/api/voice/analytics")
    async def voice_analytics():
        """Call analytics: volume, duration, sentiment trends."""
        return analyzer.get_analytics()

    logger.info("Voice Intelligence API: 12 endpoints registered under /api/voice/*")


# =========================================
# SERIALIZATION HELPERS
# =========================================

def _serialize_briefing(b: CallBriefing, audio: Optional[AudioBriefing] = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "id": b.id,
        "contact_id": b.contact_id,
        "contact": {
            "name": b.contact.name, "title": b.contact.title,
            "company": b.contact.company, "program": b.contact.program,
            "tier": b.contact.tier, "priority_score": b.contact.priority_score,
            "location": b.contact.location, "clearance": b.contact.clearance,
        },
        "pain_points": [
            {"description": pp.description, "source": pp.source, "severity": pp.severity}
            for pp in b.pain_points
        ],
        "recent_interactions": [
            {"type": ix.interaction_type, "date": ix.date,
             "outcome": ix.outcome, "follow_up": ix.follow_up}
            for ix in b.recent_interactions
        ],
        "open_jobs": b.open_jobs,
        "past_performance": b.past_performance,
        "recent_news": b.recent_news,
        "talking_points": [
            {"topic": tp.topic, "context": tp.context,
             "suggested_opener": tp.suggested_opener, "priority": tp.priority}
            for tp in b.talking_points
        ],
        "relationship_map": [
            {"contact_name": rl.contact_name, "relationship": rl.relationship,
             "program": rl.program, "contacted": rl.contacted}
            for rl in b.relationship_map
        ],
        "priority": b.priority,
        "summary": b.summary,
        "duration_estimate_sec": b.duration_estimate_sec,
        "created_at": b.created_at,
    }
    if audio:
        result["audio"] = {
            "id": audio.id, "format": audio.format,
            "duration_sec": audio.duration_sec,
            "text_script": audio.text_script,
            "audio_url": audio.audio_url,
        }
    return result


def _serialize_intel(i: TranscriptIntel) -> Dict[str, Any]:
    return {
        "id": i.id,
        "call_id": i.call_id,
        "contact_id": i.contact_id,
        "transcript_length": i.transcript_length,
        "duration_sec": i.duration_sec,
        "sentiment": i.sentiment,
        "sentiment_score": i.sentiment_score,
        "pain_points": [{"content": p.content, "confidence": p.confidence} for p in i.pain_points],
        "job_openings": [{"content": p.content, "confidence": p.confidence} for p in i.job_openings],
        "contact_mentions": [{"content": p.content, "confidence": p.confidence} for p in i.contact_mentions],
        "budget_signals": [{"content": p.content, "confidence": p.confidence} for p in i.budget_signals],
        "competitor_mentions": [{"content": p.content, "confidence": p.confidence, "context": p.context} for p in i.competitor_mentions],
        "contract_signals": [{"content": p.content, "confidence": p.confidence} for p in i.contract_signals],
        "action_items": [
            {"description": a.description, "owner": a.owner, "due_date": a.due_date, "priority": a.priority}
            for a in i.action_items
        ],
        "key_topics": i.key_topics,
        "summary": i.summary,
        "total_intel_items": i.total_intel_items,
        "created_at": i.created_at,
    }


def _serialize_intel_summary(i: TranscriptIntel) -> Dict[str, Any]:
    return {
        "id": i.id,
        "call_id": i.call_id,
        "contact_id": i.contact_id,
        "sentiment": i.sentiment,
        "total_intel_items": i.total_intel_items,
        "key_topics": i.key_topics,
        "summary": i.summary,
        "created_at": i.created_at,
    }
