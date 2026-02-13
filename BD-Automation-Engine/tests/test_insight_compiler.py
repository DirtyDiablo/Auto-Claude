"""Tests for Phase 44A — Insight Compiler."""

import pytest

from src.intelligence.meta_learner import MetaLearningEngine
from src.intelligence.pattern_engine import (
    StrategicPatternEngine,
)
from src.intelligence.insight_compiler import (
    InsightCompiler,
    WeeklyBrief,
    MonthlyAssessment,
    FlashReport,
    CampaignReview,
    BriefSection,
    get_insight_compiler,
)


@pytest.fixture
def learner():
    engine = MetaLearningEngine()
    engine.learn()
    return engine


@pytest.fixture
def pattern_engine():
    engine = StrategicPatternEngine()
    patterns = engine.scan_patterns()
    for p in patterns:
        engine.score_opportunity(p)
    engine.generate_alerts(patterns)
    return engine


@pytest.fixture
def compiler(learner, pattern_engine):
    return InsightCompiler(meta_learner=learner, pattern_engine=pattern_engine)


# =========================================
# WEEKLY BRIEF
# =========================================

def test_weekly_brief(compiler):
    brief = compiler.compile_weekly_brief()
    assert isinstance(brief, WeeklyBrief)
    assert brief.id.startswith("weekly_")
    assert brief.title != ""
    assert brief.executive_summary != ""
    assert brief.period_start != ""
    assert brief.period_end != ""


def test_weekly_brief_has_sections(compiler):
    brief = compiler.compile_weekly_brief()
    assert len(brief.sections) >= 2


def test_weekly_brief_has_metrics(compiler):
    brief = compiler.compile_weekly_brief()
    assert "patterns_detected" in brief.key_metrics
    assert "opportunities" in brief.key_metrics
    assert "outreach_response_rate" in brief.key_metrics


def test_weekly_brief_has_opportunities(compiler):
    brief = compiler.compile_weekly_brief()
    assert len(brief.top_opportunities) >= 1


def test_weekly_brief_has_action_items(compiler):
    brief = compiler.compile_weekly_brief()
    assert len(brief.action_items) >= 1


def test_weekly_brief_stored(compiler):
    compiler.compile_weekly_brief()
    assert len(compiler.get_briefs()) == 1


# =========================================
# MONTHLY ASSESSMENT
# =========================================

def test_monthly_assessment(compiler):
    assessment = compiler.compile_monthly_assessment()
    assert isinstance(assessment, MonthlyAssessment)
    assert assessment.id.startswith("monthly_")
    assert assessment.title != ""
    assert assessment.executive_summary != ""
    assert assessment.period != ""


def test_monthly_has_sections(compiler):
    assessment = compiler.compile_monthly_assessment()
    assert len(assessment.sections) >= 2


def test_monthly_has_trends(compiler):
    assessment = compiler.compile_monthly_assessment()
    assert "total_insights" in assessment.trend_analysis
    assert "total_patterns" in assessment.trend_analysis


def test_monthly_has_recommendations(compiler):
    assessment = compiler.compile_monthly_assessment()
    assert len(assessment.strategic_recommendations) >= 1


def test_monthly_stored(compiler):
    compiler.compile_monthly_assessment()
    assert len(compiler.get_assessments()) == 1


# =========================================
# FLASH REPORT
# =========================================

def test_flash_report(compiler, pattern_engine):
    patterns = pattern_engine.get_active_patterns()
    assert len(patterns) >= 1
    report = compiler.compile_flash_report(patterns[0])
    assert isinstance(report, FlashReport)
    assert report.id.startswith("flash_")
    assert report.title.startswith("FLASH:")
    assert report.pattern_id == patterns[0].id


def test_flash_report_urgency(compiler, pattern_engine):
    patterns = pattern_engine.get_active_patterns()
    report = compiler.compile_flash_report(patterns[0])
    assert report.urgency in ("low", "medium", "high", "urgent")


def test_flash_report_has_response(compiler, pattern_engine):
    patterns = pattern_engine.get_active_patterns()
    report = compiler.compile_flash_report(patterns[0])
    assert len(report.recommended_response) >= 1


def test_flash_report_has_impact(compiler, pattern_engine):
    patterns = pattern_engine.get_active_patterns()
    report = compiler.compile_flash_report(patterns[0])
    assert report.impact_assessment != ""


def test_flash_report_time_sensitivity(compiler, pattern_engine):
    patterns = pattern_engine.get_active_patterns()
    report = compiler.compile_flash_report(patterns[0])
    assert report.time_sensitivity != ""


def test_flash_report_stored(compiler, pattern_engine):
    patterns = pattern_engine.get_active_patterns()
    compiler.compile_flash_report(patterns[0])
    assert len(compiler.get_flash_reports()) == 1


# =========================================
# CAMPAIGN REVIEW
# =========================================

def test_campaign_review_all(compiler):
    review = compiler.compile_campaign_review()
    assert isinstance(review, CampaignReview)
    assert review.id.startswith("review_")
    assert review.campaign_id == "all"
    assert review.summary != ""


def test_campaign_review_specific(compiler):
    review = compiler.compile_campaign_review(campaign_id="campaign_email")
    assert review.campaign_id == "campaign_email"


def test_campaign_review_effectiveness(compiler):
    review = compiler.compile_campaign_review()
    assert 0 <= review.effectiveness_score <= 100


def test_campaign_review_what_worked(compiler):
    review = compiler.compile_campaign_review()
    # Should have at least one item in worked or didn't
    assert len(review.what_worked) + len(review.what_didnt) >= 1


def test_campaign_review_recommendations(compiler):
    review = compiler.compile_campaign_review()
    assert len(review.recommendations) >= 1


def test_campaign_review_stored(compiler):
    compiler.compile_campaign_review()
    assert len(compiler.get_campaign_reviews()) == 1


# =========================================
# STATS
# =========================================

def test_stats(compiler):
    compiler.compile_weekly_brief()
    compiler.compile_monthly_assessment()
    stats = compiler.get_stats()
    assert stats["weekly_briefs"] == 1
    assert stats["monthly_assessments"] == 1


# =========================================
# BRIEF SECTION
# =========================================

def test_brief_section():
    s = BriefSection(heading="Test", content="Content", priority="high")
    assert s.heading == "Test"
    assert s.priority == "high"


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    c1 = get_insight_compiler()
    c2 = get_insight_compiler()
    assert c1 is c2
