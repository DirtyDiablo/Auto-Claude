"""Tests for Phase 44A — Strategic Pattern Recognition Engine."""

import pytest

from src.intelligence.pattern_engine import (
    StrategicPatternEngine,
    StrategicPattern,
    OpportunityScore,
    StrategicAlert,
    PatternType,
    AlertPriority,
    get_pattern_engine,
)


@pytest.fixture
def engine():
    return StrategicPatternEngine()


# =========================================
# SCAN ALL PATTERNS
# =========================================

def test_scan_returns_patterns(engine):
    patterns = engine.scan_patterns()
    assert len(patterns) >= 3


def test_scan_covers_multiple_types(engine):
    patterns = engine.scan_patterns()
    types = {p.pattern_type for p in patterns}
    assert len(types) >= 3


def test_scan_stores_patterns(engine):
    engine.scan_patterns()
    assert len(engine.get_active_patterns()) >= 3


# =========================================
# HIRING SURGE
# =========================================

def test_hiring_surge_detected(engine):
    patterns = engine.scan_patterns()
    surges = [p for p in patterns if p.pattern_type == PatternType.HIRING_SURGE.value]
    assert len(surges) >= 1
    assert surges[0].program != ""


# =========================================
# LEADERSHIP CHANGE
# =========================================

def test_leadership_change_detected(engine):
    patterns = engine.scan_patterns()
    changes = [p for p in patterns if p.pattern_type == PatternType.LEADERSHIP_CHANGE.value]
    assert len(changes) >= 1
    assert "departure" in changes[0].description.lower() or "gap" in changes[0].title.lower()


# =========================================
# CONTRACT MILESTONE
# =========================================

def test_contract_milestone_detected(engine):
    patterns = engine.scan_patterns()
    milestones = [p for p in patterns if p.pattern_type == PatternType.CONTRACT_MILESTONE.value]
    assert len(milestones) >= 1


# =========================================
# COMPETITIVE SHIFT
# =========================================

def test_competitive_shift_detected(engine):
    patterns = engine.scan_patterns()
    shifts = [p for p in patterns if p.pattern_type == PatternType.COMPETITIVE_SHIFT.value]
    assert len(shifts) >= 1


def test_competitive_exit_flagged(engine):
    patterns = engine.scan_patterns()
    exits = [p for p in patterns if "exit" in p.tags]
    assert len(exits) >= 1


# =========================================
# BUDGET SIGNAL
# =========================================

def test_budget_signal_detected(engine):
    patterns = engine.scan_patterns()
    signals = [p for p in patterns if p.pattern_type == PatternType.BUDGET_SIGNAL.value]
    assert len(signals) >= 1


# =========================================
# GEOGRAPHIC SHIFT
# =========================================

def test_geographic_shift_detected(engine):
    patterns = engine.scan_patterns()
    shifts = [p for p in patterns if p.pattern_type == PatternType.GEOGRAPHIC_SHIFT.value]
    assert len(shifts) >= 1
    assert "new site" in shifts[0].title.lower() or "Fort Meade" in shifts[0].description


# =========================================
# SKILL DEMAND
# =========================================

def test_skill_demand_detected(engine):
    patterns = engine.scan_patterns()
    demands = [p for p in patterns if p.pattern_type == PatternType.SKILL_DEMAND.value]
    assert len(demands) >= 1


# =========================================
# SCORE OPPORTUNITY
# =========================================

def test_score_opportunity(engine):
    patterns = engine.scan_patterns()
    score = engine.score_opportunity(patterns[0])
    assert isinstance(score, OpportunityScore)
    assert 0 <= score.score <= 100
    assert score.urgency in ("low", "medium", "high", "urgent")
    assert 0 < score.win_probability <= 1.0
    assert len(score.recommended_actions) >= 1


def test_score_factors(engine):
    patterns = engine.scan_patterns()
    score = engine.score_opportunity(patterns[0])
    assert "confidence" in score.scoring_factors
    assert "type_weight" in score.scoring_factors
    assert "evidence" in score.scoring_factors
    assert "recency" in score.scoring_factors


def test_score_all_patterns(engine):
    patterns = engine.scan_patterns()
    scores = [engine.score_opportunity(p) for p in patterns]
    assert all(0 <= s.score <= 100 for s in scores)


# =========================================
# GENERATE ALERTS
# =========================================

def test_generate_alerts(engine):
    patterns = engine.scan_patterns()
    for p in patterns:
        engine.score_opportunity(p)
    alerts = engine.generate_alerts(patterns)
    assert len(alerts) >= 1
    assert all(isinstance(a, StrategicAlert) for a in alerts)


def test_alert_priority(engine):
    patterns = engine.scan_patterns()
    for p in patterns:
        engine.score_opportunity(p)
    alerts = engine.generate_alerts(patterns)
    priorities = {a.priority for a in alerts}
    assert len(priorities) >= 1


def test_alert_has_actions(engine):
    patterns = engine.scan_patterns()
    for p in patterns:
        engine.score_opportunity(p)
    alerts = engine.generate_alerts(patterns)
    for alert in alerts:
        assert len(alert.actions) >= 1


# =========================================
# QUERIES
# =========================================

def test_get_active_by_type(engine):
    engine.scan_patterns()
    surges = engine.get_active_patterns(pattern_type=PatternType.HIRING_SURGE.value)
    assert all(p.pattern_type == PatternType.HIRING_SURGE.value for p in surges)


def test_get_opportunities(engine):
    patterns = engine.scan_patterns()
    for p in patterns:
        engine.score_opportunity(p)
    opps = engine.get_opportunities(min_score=0)
    assert len(opps) >= 1
    # Sorted by score descending
    if len(opps) >= 2:
        assert opps[0]["score"] >= opps[1]["score"]


def test_get_opportunities_with_filter(engine):
    patterns = engine.scan_patterns()
    for p in patterns:
        engine.score_opportunity(p)
    high = engine.get_opportunities(min_score=60)
    assert all(o["score"] >= 60 for o in high)


def test_get_alerts(engine):
    patterns = engine.scan_patterns()
    for p in patterns:
        engine.score_opportunity(p)
    engine.generate_alerts(patterns)
    alerts = engine.get_alerts()
    assert len(alerts) >= 1


def test_acknowledge_alert(engine):
    patterns = engine.scan_patterns()
    for p in patterns:
        engine.score_opportunity(p)
    engine.generate_alerts(patterns)
    alerts = engine.get_alerts(unacknowledged_only=True)
    assert len(alerts) >= 1
    assert engine.acknowledge_alert(alerts[0].id) is True


def test_acknowledge_nonexistent(engine):
    assert engine.acknowledge_alert("nonexistent") is False


# =========================================
# STATS
# =========================================

def test_stats(engine):
    patterns = engine.scan_patterns()
    for p in patterns:
        engine.score_opportunity(p)
    stats = engine.get_stats()
    assert stats["total_patterns"] >= 3
    assert "by_type" in stats
    assert stats["total_scores"] >= 3
    assert stats["avg_score"] > 0


# =========================================
# PATTERN ID & FIELDS
# =========================================

def test_pattern_auto_id():
    p = StrategicPattern(pattern_type="test", title="Test")
    assert p.id.startswith("pat_")
    assert p.detected_at != ""
    assert p.expires_at != ""


def test_alert_auto_id():
    a = StrategicAlert(pattern_id="pat_123", title="Test Alert")
    assert a.id.startswith("alert_")
    assert a.created_at != ""


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    e1 = get_pattern_engine()
    e2 = get_pattern_engine()
    assert e1 is e2
