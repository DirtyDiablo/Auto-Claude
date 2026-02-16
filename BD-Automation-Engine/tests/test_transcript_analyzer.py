"""Tests for Phase 46A — Transcript Intelligence Extractor."""

import pytest

from src.voice.transcript_analyzer import (
    TranscriptIntelligenceExtractor,
    TranscriptIntel,
    Sentiment,
    get_transcript_analyzer,
)


@pytest.fixture
def analyzer():
    return TranscriptIntelligenceExtractor()


# Sample transcripts for testing
SAMPLE_TRANSCRIPT_FULL = """
Hi Craig, thanks for taking the time to speak with me today. I appreciate you being available.

We've been struggling to fill senior cloud architect positions at Langley. The SIGINT processing
pipeline has serious latency issues and it's a bottleneck for the whole program.

We're looking for cleared talent, ideally TS/SCI, for about five open positions. The hiring
process has been difficult with the current market.

I spoke with Mr. Johnson last week about this. He mentioned that Leidos is also having trouble
finding qualified people. BAE submitted a proposal last month but we weren't impressed.

Our budget for FY26 has been approved with a ceiling increase of about $20M. The funding
allocation should be available by Q2.

The contract recompete is scheduled for September. We need to have the transition plan
ready by then. The option year 3 exercise is due in June.

I'll send you the requirements document by Friday. Can you schedule a follow-up meeting
with our tech lead by next week? Let me check on the exact headcount numbers and
get back to you by end of month.

This has been a great conversation. I'm looking forward to working together on this.
Thank you for your time.
"""

SAMPLE_TRANSCRIPT_NEGATIVE = """
I'm disappointed with the progress so far. The integration is behind schedule and
we're frustrated with the lack of communication. The team seems understaffed and
I'm concerned about meeting the deadline. Unfortunately the budget situation is
getting worse and I'm worried about further cuts.
"""

SAMPLE_TRANSCRIPT_MINIMAL = """
Quick check-in call. Everything is going well. No major updates.
"""


# =========================================
# FULL TRANSCRIPT ANALYSIS
# =========================================


def test_analyze_full_transcript(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    assert isinstance(intel, TranscriptIntel)
    assert intel.contact_id == "c001"
    assert intel.id.startswith("tintel_")


def test_pain_points_extracted(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    assert len(intel.pain_points) >= 1
    contents = " ".join(pp.content.lower() for pp in intel.pain_points)
    assert "struggling" in contents or "bottleneck" in contents or "latency" in contents


def test_job_openings_extracted(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    assert len(intel.job_openings) >= 1
    contents = " ".join(j.content.lower() for j in intel.job_openings)
    assert (
        "hiring" in contents or "open position" in contents or "looking for" in contents
    )


def test_competitor_mentions_extracted(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    assert len(intel.competitor_mentions) >= 1
    contexts = [cm.context for cm in intel.competitor_mentions]
    assert any("Leidos" in c or "BAE" in c for c in contexts)


def test_budget_signals_extracted(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    assert len(intel.budget_signals) >= 1
    contents = " ".join(bs.content.lower() for bs in intel.budget_signals)
    assert "budget" in contents or "funding" in contents or "ceiling" in contents


def test_contract_signals_extracted(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    assert len(intel.contract_signals) >= 1
    contents = " ".join(cs.content.lower() for cs in intel.contract_signals)
    assert (
        "recompete" in contents or "option year" in contents or "transition" in contents
    )


def test_contact_mentions_extracted(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    assert len(intel.contact_mentions) >= 1
    assert any("Johnson" in cm.content for cm in intel.contact_mentions)


def test_action_items_extracted(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    assert len(intel.action_items) >= 2
    descriptions = " ".join(ai.description.lower() for ai in intel.action_items)
    assert (
        "send" in descriptions or "schedule" in descriptions or "follow" in descriptions
    )


def test_action_item_owner(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    owners = {ai.owner for ai in intel.action_items}
    assert "us" in owners or "them" in owners


def test_action_item_due_date(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    with_dates = [ai for ai in intel.action_items if ai.due_date]
    assert len(with_dates) >= 1


def test_sentiment_positive(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    assert intel.sentiment == Sentiment.POSITIVE.value
    assert intel.sentiment_score > 0.5


def test_sentiment_negative(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_NEGATIVE, contact_id="c001")
    assert intel.sentiment == Sentiment.NEGATIVE.value
    assert intel.sentiment_score < 0.5


def test_sentiment_neutral(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_MINIMAL, contact_id="c001")
    assert intel.sentiment == Sentiment.NEUTRAL.value


def test_key_topics(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    assert len(intel.key_topics) >= 2
    assert any(
        t in intel.key_topics
        for t in ["staffing", "budget", "contract", "cloud_migration"]
    )


def test_summary(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    assert "c001" in intel.summary
    assert "positive" in intel.summary.lower()


def test_total_intel_items(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    assert intel.total_intel_items >= 5


def test_transcript_length(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    assert intel.transcript_length == len(SAMPLE_TRANSCRIPT_FULL)


# =========================================
# VAPI WEBHOOK
# =========================================


def test_vapi_webhook(analyzer):
    webhook_data = {
        "call_id": "vapi_call_123",
        "transcript": SAMPLE_TRANSCRIPT_FULL,
        "contact_id": "c001",
        "duration_seconds": 300,
        "metadata": {},
    }
    intel = analyzer.process_vapi_webhook(webhook_data)
    assert intel.call_id == "vapi_call_123"
    assert intel.contact_id == "c001"
    assert intel.duration_sec == 300


def test_vapi_webhook_metadata_contact(analyzer):
    webhook_data = {
        "id": "vapi_456",
        "transcript": "Quick call about hiring needs.",
        "duration": 60,
        "metadata": {"contact_id": "c002"},
    }
    intel = analyzer.process_vapi_webhook(webhook_data)
    assert intel.contact_id == "c002"


def test_vapi_sets_source(analyzer):
    webhook_data = {
        "call_id": "vapi_789",
        "transcript": "Test call.",
        "contact_id": "c001",
        "duration_seconds": 30,
    }
    analyzer.process_vapi_webhook(webhook_data)
    call = analyzer.get_call("vapi_789")
    assert call is not None
    assert call.source == "vapi"


# =========================================
# COACHING
# =========================================


def test_coaching_competitor(analyzer):
    suggestions = analyzer.get_coaching_suggestions(
        "We're also talking to Leidos about this."
    )
    assert len(suggestions) >= 1
    assert any("competitor" in s.get("trigger", "") for s in suggestions)


def test_coaching_budget(analyzer):
    suggestions = analyzer.get_coaching_suggestions(
        "Our budget for this fiscal year is tight."
    )
    assert len(suggestions) >= 1


def test_coaching_pain_point(analyzer):
    suggestions = analyzer.get_coaching_suggestions("We're struggling with staffing.")
    assert len(suggestions) >= 1


def test_coaching_empty(analyzer):
    suggestions = analyzer.get_coaching_suggestions("The weather is nice today.")
    assert len(suggestions) == 0


# =========================================
# QUERIES
# =========================================


def test_call_history(analyzer):
    analyzer.analyze_transcript("Call 1 about hiring needs.", contact_id="c001")
    analyzer.analyze_transcript("Call 2 about budget.", contact_id="c001")
    history = analyzer.get_call_history("c001")
    assert len(history) == 2


def test_recent_intel(analyzer):
    analyzer.analyze_transcript("Call about challenges.", contact_id="c001")
    recent = analyzer.get_recent_intel(limit=10)
    assert len(recent) >= 1


def test_all_pain_points(analyzer):
    analyzer.analyze_transcript(
        "We're struggling with latency issues.", contact_id="c001"
    )
    pps = analyzer.get_all_pain_points()
    assert len(pps) >= 1


def test_all_action_items(analyzer):
    analyzer.analyze_transcript(
        "I'll send you the document by Friday.", contact_id="c001"
    )
    items = analyzer.get_all_action_items()
    assert len(items) >= 1


def test_all_action_items_by_status(analyzer):
    analyzer.analyze_transcript("I'll send the report by next week.", contact_id="c001")
    items = analyzer.get_all_action_items(status="open")
    assert all(i["status"] == "open" for i in items)


# =========================================
# ANALYTICS
# =========================================


def test_analytics(analyzer):
    analyzer.analyze_transcript(
        SAMPLE_TRANSCRIPT_FULL, contact_id="c001", duration_sec=300
    )
    analytics = analyzer.get_analytics()
    assert analytics["total_calls"] == 1
    assert analytics["total_duration_sec"] == 300
    assert "sentiment_distribution" in analytics
    assert analytics["total_intel_extracted"] >= 1


def test_analytics_sources(analyzer):
    analyzer.analyze_transcript("Call 1.", contact_id="c001")
    analyzer.process_vapi_webhook(
        {
            "call_id": "v1",
            "transcript": "Call 2.",
            "contact_id": "c002",
            "duration_seconds": 60,
        }
    )
    analytics = analyzer.get_analytics()
    assert "manual" in analytics["sources"]
    assert "vapi" in analytics["sources"]


# =========================================
# EXTRACTION CONFIDENCE
# =========================================


def test_extraction_confidence(analyzer):
    intel = analyzer.analyze_transcript(SAMPLE_TRANSCRIPT_FULL, contact_id="c001")
    for pp in intel.pain_points:
        assert 0 < pp.confidence <= 1.0
    for cm in intel.competitor_mentions:
        assert cm.confidence == 0.90


# =========================================
# STATS
# =========================================


def test_stats(analyzer):
    analyzer.analyze_transcript("Test.", contact_id="c001")
    stats = analyzer.get_stats()
    assert stats["total_analyses"] == 1
    assert stats["total_calls"] == 1


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    a1 = get_transcript_analyzer()
    a2 = get_transcript_analyzer()
    assert a1 is a2
