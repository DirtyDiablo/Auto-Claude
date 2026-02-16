"""Tests for Phase 44A — Meta-Learning Engine."""

import pytest

from src.intelligence.meta_learner import (
    MetaLearningEngine,
    MetaInsight,
    OutreachInsight,
    ProgramInsight,
    TransferReport,
    InsightDomain,
    get_meta_learner,
)


@pytest.fixture
def engine():
    return MetaLearningEngine()


# =========================================
# LEARN ALL
# =========================================


def test_learn_returns_insights(engine):
    insights = engine.learn()
    assert len(insights) >= 5


def test_learn_covers_all_domains(engine):
    insights = engine.learn()
    domains = {i.domain for i in insights}
    assert InsightDomain.OUTREACH.value in domains
    assert InsightDomain.PROGRAM.value in domains
    assert InsightDomain.CONTACT.value in domains
    assert InsightDomain.DATA_QUALITY.value in domains
    assert InsightDomain.COMPETITIVE.value in domains


def test_learn_stores_insights(engine):
    engine.learn()
    assert len(engine.get_insights()) >= 5


# =========================================
# OUTREACH
# =========================================


def test_learn_outreach(engine):
    insights = engine.learn_outreach()
    assert len(insights) >= 2  # channel effectiveness + best time
    assert all(isinstance(i, OutreachInsight) for i in insights)


def test_outreach_channel_effectiveness(engine):
    insights = engine.learn_outreach()
    channel_insights = [i for i in insights if i.channel]
    assert len(channel_insights) >= 1
    for ci in channel_insights:
        assert 0 <= ci.response_rate <= 1.0
        assert len(ci.tier_effectiveness) >= 1


def test_outreach_best_time(engine):
    insights = engine.learn_outreach()
    timing = [i for i in insights if i.best_time]
    assert len(timing) >= 1
    assert timing[0].best_time  # e.g. "Tuesday 14:00"


# =========================================
# PROGRAMS
# =========================================


def test_learn_programs(engine):
    insights = engine.learn_programs()
    assert len(insights) >= 3  # DCGS-A, DCGS-N, GBSD
    assert all(isinstance(i, ProgramInsight) for i in insights)


def test_program_trends(engine):
    insights = engine.learn_programs()
    trends = {i.trend for i in insights}
    assert "growing" in trends or "shrinking" in trends or "stable" in trends


def test_program_cycle_phase(engine):
    insights = engine.learn_programs()
    phases = {i.cycle_phase for i in insights}
    assert len(phases) >= 1


# =========================================
# CONTACTS
# =========================================


def test_learn_contacts(engine):
    insights = engine.learn_contacts()
    assert len(insights) >= 2


def test_super_connectors(engine):
    insights = engine.learn_contacts()
    connectors = [i for i in insights if i.contact_pattern == "super_connector"]
    assert len(connectors) >= 1
    assert len(connectors[0].affected_contacts) >= 1


def test_role_churn(engine):
    insights = engine.learn_contacts()
    churn = [i for i in insights if i.contact_pattern == "role_churn"]
    assert len(churn) >= 1


def test_career_progression(engine):
    insights = engine.learn_contacts()
    progression = [i for i in insights if i.contact_pattern == "career_progression"]
    assert len(progression) >= 1


# =========================================
# DATA QUALITY
# =========================================


def test_learn_data_quality(engine):
    insights = engine.learn_data_quality()
    assert len(insights) >= 2  # decay + source quality


def test_data_decay_insight(engine):
    insights = engine.learn_data_quality()
    decay = [i for i in insights if "decay" in i.tags]
    assert len(decay) >= 1


def test_source_quality_insight(engine):
    insights = engine.learn_data_quality()
    source = [i for i in insights if "source" in i.tags]
    assert len(source) >= 1


# =========================================
# COMPETITIVE
# =========================================


def test_learn_competitive(engine):
    insights = engine.learn_competitive()
    assert len(insights) >= 1


def test_competitive_exit_detected(engine):
    insights = engine.learn_competitive()
    exits = [i for i in insights if "exit" in i.tags]
    assert len(exits) >= 1


# =========================================
# TRANSFER LEARNING
# =========================================


def test_transfer_learning(engine):
    engine.learn()
    report = engine.transfer_learning("DCGS-A", "DCGS-N")
    assert isinstance(report, TransferReport)
    assert report.source_program == "DCGS-A"
    assert report.target_program == "DCGS-N"
    assert report.created_at != ""


def test_transfer_generates_insights(engine):
    engine.learn()
    report = engine.transfer_learning("DCGS-A", "DCGS-N")
    assert len(report.transferable_insights) >= 1
    # Transferred insights have reduced confidence
    for ti in report.transferable_insights:
        assert ti.confidence <= 0.95 * 0.7 + 0.01  # original max * 0.7


def test_transfer_empty_source(engine):
    report = engine.transfer_learning("nonexistent", "DCGS-N")
    assert report.similarity_score == 0.0
    assert len(report.transferable_insights) == 0


# =========================================
# QUERIES
# =========================================


def test_get_insights_by_domain(engine):
    engine.learn()
    outreach = engine.get_insights(domain="outreach")
    assert all(i.domain == "outreach" for i in outreach)


def test_get_insights_by_severity(engine):
    engine.learn()
    high = engine.get_insights(severity="high")
    assert all(i.severity == "high" for i in high)


def test_outreach_effectiveness(engine):
    data = engine.get_outreach_effectiveness()
    assert "channels" in data
    assert data["total_attempts"] >= 1
    assert 0 <= data["overall_rate"] <= 1.0


def test_campaign_effectiveness(engine):
    data = engine.get_campaign_effectiveness()
    assert "campaigns" in data
    assert data["total_campaigns"] >= 1


def test_competitive_trends(engine):
    data = engine.get_competitive_trends()
    assert "competitors" in data
    assert data["total_competitors"] >= 1


# =========================================
# STATS
# =========================================


def test_stats(engine):
    engine.learn()
    stats = engine.get_stats()
    assert stats["total_insights"] >= 5
    assert "by_domain" in stats
    assert "data_points" in stats


# =========================================
# INSIGHT ID & FIELDS
# =========================================


def test_insight_auto_id():
    i = MetaInsight(domain="test", title="Test Insight")
    assert i.id.startswith("insight_")
    assert i.created_at != ""
    assert i.expires_at != ""


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    e1 = get_meta_learner()
    e2 = get_meta_learner()
    assert e1 is e2
