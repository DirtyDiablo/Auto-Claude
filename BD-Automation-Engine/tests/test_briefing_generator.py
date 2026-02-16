"""Tests for Phase 46A — Call Briefing Generator."""

import pytest

from src.voice.briefing_generator import (
    CallBriefingGenerator,
    CallBriefing,
    AudioBriefing,
    PainPoint,
    TalkingPoint,
    BriefingPriority,
    get_briefing_generator,
)


@pytest.fixture
def generator():
    return CallBriefingGenerator()


# =========================================
# BRIEFING GENERATION
# =========================================


def test_generate_briefing(generator):
    briefing = generator.generate_briefing("c001")
    assert isinstance(briefing, CallBriefing)
    assert briefing.contact_id == "c001"
    assert briefing.id.startswith("brief_")
    assert briefing.created_at != ""


def test_briefing_contact_profile(generator):
    briefing = generator.generate_briefing("c001")
    assert briefing.contact.name == "Craig Lindahl"
    assert briefing.contact.company == "Leidos"
    assert briefing.contact.program == "DCGS-A"
    assert briefing.contact.tier == 1


def test_briefing_pain_points(generator):
    briefing = generator.generate_briefing("c001")
    assert len(briefing.pain_points) >= 2
    assert all(isinstance(pp, PainPoint) for pp in briefing.pain_points)
    assert any(
        "cloud architect" in pp.description.lower() for pp in briefing.pain_points
    )


def test_briefing_recent_interactions(generator):
    briefing = generator.generate_briefing("c001")
    assert len(briefing.recent_interactions) >= 1
    assert briefing.recent_interactions[0].interaction_type == "call"


def test_briefing_open_jobs(generator):
    briefing = generator.generate_briefing("c001")
    assert len(briefing.open_jobs) >= 2  # DCGS-A has 3 open jobs


def test_briefing_past_performance(generator):
    briefing = generator.generate_briefing("c001")
    assert len(briefing.past_performance) >= 1


def test_briefing_recent_news(generator):
    briefing = generator.generate_briefing("c001")
    assert len(briefing.recent_news) >= 1


def test_briefing_talking_points(generator):
    briefing = generator.generate_briefing("c001")
    assert len(briefing.talking_points) >= 2
    assert all(isinstance(tp, TalkingPoint) for tp in briefing.talking_points)
    # Should have relationship continuity point since c001 has interactions
    topics = [tp.topic for tp in briefing.talking_points]
    assert any(
        "Relationship" in t or "Pain Point" in t or "Staffing" in t for t in topics
    )


def test_briefing_relationship_map(generator):
    briefing = generator.generate_briefing("c001")
    assert len(briefing.relationship_map) >= 1
    assert briefing.relationship_map[0].contact_name == "Amanda Chen"


def test_briefing_priority_critical(generator):
    briefing = generator.generate_briefing("c001")
    # Tier 1 with critical pain point
    assert briefing.priority == BriefingPriority.CRITICAL.value


def test_briefing_priority_high(generator):
    briefing = generator.generate_briefing("c002")
    # Tier 2 with pain points
    assert briefing.priority == BriefingPriority.HIGH.value


def test_briefing_priority_standard(generator):
    briefing = generator.generate_briefing("c004")
    # Tier 3 without critical pain points
    assert briefing.priority == BriefingPriority.STANDARD.value


def test_briefing_summary(generator):
    briefing = generator.generate_briefing("c001")
    assert "Craig Lindahl" in briefing.summary
    assert "Leidos" in briefing.summary or "DCGS-A" in briefing.summary


def test_briefing_duration_estimate(generator):
    briefing = generator.generate_briefing("c001")
    assert briefing.duration_estimate_sec > 0


def test_briefing_not_found(generator):
    briefing = generator.generate_briefing("nonexistent")
    assert "not found" in briefing.summary.lower()
    assert briefing.priority == "low"


def test_briefing_stored(generator):
    briefing = generator.generate_briefing("c001")
    assert generator.get_briefing(briefing.id) is not None


# =========================================
# BATCH BRIEFINGS
# =========================================


def test_batch_briefings(generator):
    results = generator.generate_batch(["c001", "c002", "c003"])
    assert len(results) == 3
    assert all(isinstance(b, CallBriefing) for b in results)


def test_batch_with_invalid(generator):
    results = generator.generate_batch(["c001", "nonexistent"])
    assert len(results) == 2


# =========================================
# AUDIO BRIEFING
# =========================================


def test_audio_briefing(generator):
    briefing = generator.generate_briefing("c001")
    audio = generator.generate_audio_briefing(briefing)
    assert isinstance(audio, AudioBriefing)
    assert audio.id.startswith("audio_")
    assert audio.briefing_id == briefing.id


def test_audio_format(generator):
    briefing = generator.generate_briefing("c001")
    audio = generator.generate_audio_briefing(briefing)
    assert audio.format == "mp3"


def test_audio_duration(generator):
    briefing = generator.generate_briefing("c001")
    audio = generator.generate_audio_briefing(briefing)
    assert 30 <= audio.duration_sec <= 180


def test_audio_script(generator):
    briefing = generator.generate_briefing("c001")
    audio = generator.generate_audio_briefing(briefing)
    assert "Craig Lindahl" in audio.text_script
    assert len(audio.text_script) > 50


def test_audio_url(generator):
    briefing = generator.generate_briefing("c001")
    audio = generator.generate_audio_briefing(briefing)
    assert audio.audio_url.startswith("/api/voice/audio/")


def test_audio_size(generator):
    briefing = generator.generate_briefing("c001")
    audio = generator.generate_audio_briefing(briefing)
    assert audio.size_bytes > 0


def test_audio_stored(generator):
    briefing = generator.generate_briefing("c001")
    audio = generator.generate_audio_briefing(briefing)
    assert generator.get_audio(audio.id) is not None
    assert generator.get_audio_for_briefing(briefing.id) is not None


# =========================================
# DIFFERENT CONTACTS
# =========================================


def test_contact_c003(generator):
    briefing = generator.generate_briefing("c003")
    assert briefing.contact.name == "James Patel"
    assert briefing.contact.program == "DCGS-N"
    assert len(briefing.pain_points) >= 2


def test_contact_c002(generator):
    briefing = generator.generate_briefing("c002")
    assert briefing.contact.name == "Sarah Mitchell"
    assert briefing.contact.program == "GBSD"


# =========================================
# STATS
# =========================================


def test_stats(generator):
    generator.generate_briefing("c001")
    generator.generate_briefing("c002")
    stats = generator.get_stats()
    assert stats["total_briefings"] == 2
    assert stats["contacts_available"] >= 4


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    g1 = get_briefing_generator()
    g2 = get_briefing_generator()
    assert g1 is g2
