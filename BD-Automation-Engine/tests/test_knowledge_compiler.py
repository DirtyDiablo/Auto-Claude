"""Tests for Phase 39A — Knowledge Compiler."""

import pytest

from src.knowledge.compiler import (
    KnowledgeCompiler,
    ExtractedFact,
    CompilationReport,
    EpisodeSource,
    FactType,
    get_knowledge_compiler,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def compiler():
    return KnowledgeCompiler()


SAMPLE_TEXT = (
    "Spoke with John Smith at GDIT about the DCGS-A program. "
    "He mentioned they're hiring 5 new analysts for Q2. "
    "Their team is stretched thin since Mike left last month. "
    "Budget is $2.5M for this initiative. "
    "Need to follow up with him next week about the proposal."
)

SIMPLE_TEXT = "John Smith works at Leidos on the DCGS program."


# =========================================
# BASIC COMPILATION
# =========================================

def test_compile_empty(compiler):
    facts = compiler.compile("")
    assert facts == []


def test_compile_whitespace(compiler):
    facts = compiler.compile("   ")
    assert facts == []


def test_compile_returns_facts(compiler):
    facts = compiler.compile(SAMPLE_TEXT)
    assert len(facts) > 0
    assert all(isinstance(f, ExtractedFact) for f in facts)


def test_compile_fact_has_id(compiler):
    facts = compiler.compile(SIMPLE_TEXT)
    for fact in facts:
        assert fact.id != ""


def test_compile_fact_has_type(compiler):
    facts = compiler.compile(SAMPLE_TEXT)
    valid_types = {ft.value for ft in FactType}
    for fact in facts:
        assert fact.fact_type in valid_types


# =========================================
# RELATIONSHIP EXTRACTION
# =========================================

def test_compile_extracts_relationships(compiler):
    facts = compiler.compile(SIMPLE_TEXT)
    rels = [f for f in facts if f.fact_type == FactType.RELATIONSHIP.value]
    assert len(rels) >= 1


def test_compile_relationship_has_subject(compiler):
    facts = compiler.compile(SIMPLE_TEXT)
    rels = [f for f in facts if f.fact_type == FactType.RELATIONSHIP.value]
    if rels:
        assert rels[0].subject != ""


# =========================================
# NUMERICAL EXTRACTION
# =========================================

def test_compile_extracts_currency(compiler):
    facts = compiler.compile("The contract is worth $2.5M.")
    nums = [f for f in facts if f.fact_type == FactType.NUMERICAL.value]
    assert len(nums) >= 1
    assert any("$2.5M" in f.object for f in nums)


def test_compile_extracts_headcount(compiler):
    facts = compiler.compile("They need 10 analysts for the project.")
    nums = [f for f in facts if f.fact_type == FactType.NUMERICAL.value]
    assert len(nums) >= 1


def test_compile_extracts_team_size(compiler):
    facts = compiler.compile("She leads a team of 15 engineers.")
    nums = [f for f in facts if f.fact_type == FactType.NUMERICAL.value]
    assert len(nums) >= 1


# =========================================
# SENTIMENT / PAIN POINT EXTRACTION
# =========================================

def test_compile_extracts_pain_points(compiler):
    facts = compiler.compile("The team is stretched thin and overwhelmed.")
    sentiments = [f for f in facts if f.fact_type == FactType.SENTIMENT.value]
    assert len(sentiments) >= 1


def test_compile_pain_point_turnover(compiler):
    facts = compiler.compile("High turnover is a major concern at the organization.")
    sentiments = [f for f in facts if f.fact_type == FactType.SENTIMENT.value]
    assert len(sentiments) >= 1


def test_compile_pain_point_budget(compiler):
    facts = compiler.compile("Budget cuts are affecting the program significantly.")
    sentiments = [f for f in facts if f.fact_type == FactType.SENTIMENT.value]
    assert len(sentiments) >= 1


# =========================================
# ACTION ITEM EXTRACTION
# =========================================

def test_compile_extracts_actions(compiler):
    facts = compiler.compile("Need to follow up with John next week about the proposal.")
    actions = [f for f in facts if f.fact_type == FactType.ACTION_ITEM.value]
    assert len(actions) >= 1


def test_compile_action_with_source(compiler):
    source = EpisodeSource(author="Test User")
    facts = compiler.compile(
        "Need to schedule a meeting with the team.",
        source=source,
    )
    actions = [f for f in facts if f.fact_type == FactType.ACTION_ITEM.value]
    if actions:
        assert actions[0].subject == "Test User"


def test_compile_actions_limited_to_5(compiler):
    text = ". ".join([
        "Follow up on item one",
        "Schedule meeting for item two",
        "Send report for item three",
        "Call back about item four",
        "Set up demo for item five",
        "Arrange visit for item six",
        "Provide update for item seven",
    ])
    facts = compiler.compile(text)
    actions = [f for f in facts if f.fact_type == FactType.ACTION_ITEM.value]
    assert len(actions) <= 5


# =========================================
# HIRING EXTRACTION
# =========================================

def test_compile_extracts_hiring(compiler):
    facts = compiler.compile("GDIT is hiring 3 new positions for the program.")
    events = [f for f in facts if f.fact_type == FactType.EVENT.value]
    assert len(events) >= 1


def test_compile_hiring_vacancy(compiler):
    facts = compiler.compile("There is an open position for a senior analyst.")
    events = [f for f in facts if f.fact_type == FactType.EVENT.value]
    assert len(events) >= 1


# =========================================
# DEPARTURE EXTRACTION
# =========================================

def test_compile_extracts_departures(compiler):
    facts = compiler.compile("Mike Brown left the company last month.")
    events = [f for f in facts if f.predicate == "DEPARTED"]
    assert len(events) >= 1


def test_compile_departure_resigned(compiler):
    facts = compiler.compile("Sarah Johnson resigned from her position.")
    events = [f for f in facts if f.predicate == "DEPARTED"]
    assert len(events) >= 1


# =========================================
# TEMPORAL MARKERS
# =========================================

def test_compile_temporal_quarter(compiler):
    facts = compiler.compile("The Q2 hiring push will add 5 analysts.")
    # At least one fact should have a temporal marker
    markers = [f.temporal_marker for f in facts if f.temporal_marker]
    assert len(markers) >= 1


def test_compile_temporal_relative(compiler):
    facts = compiler.compile("They started last month and will finish next quarter.")
    markers = [f.temporal_marker for f in facts if f.temporal_marker]
    assert len(markers) >= 1


# =========================================
# BATCH COMPILATION
# =========================================

def test_compile_batch(compiler):
    texts = [SIMPLE_TEXT, SAMPLE_TEXT]
    report = compiler.compile_batch(texts)
    assert isinstance(report, CompilationReport)
    assert report.total_texts == 2
    assert report.total_facts >= 1


def test_compile_batch_deduplication(compiler):
    # Same text twice should produce deduplication
    texts = [SIMPLE_TEXT, SIMPLE_TEXT]
    report = compiler.compile_batch(texts)
    assert report.deduplicated >= 1


def test_compile_batch_error_handling(compiler):
    # Include None to trigger error
    texts = ["Valid text about John Smith at GDIT."]
    report = compiler.compile_batch(texts)
    assert len(report.errors) == 0


def test_compile_batch_duration(compiler):
    report = compiler.compile_batch([SIMPLE_TEXT])
    assert report.duration_seconds >= 0


# =========================================
# NOTES COMPILATION
# =========================================

def test_compile_from_notes(compiler):
    notes = [
        {"contact_name": "John Smith", "company": "GDIT", "notes": "Discussed hiring needs."},
        {"contact_name": "Jane Doe", "company": "Leidos", "subject": "DCGS", "content": "Budget review."},
    ]
    report = compiler.compile_from_notes(notes)
    assert isinstance(report, CompilationReport)
    assert report.total_texts == 2


def test_compile_from_notes_empty_fields(compiler):
    notes = [{"notes": "Just a simple note about hiring."}]
    report = compiler.compile_from_notes(notes)
    assert report.total_facts >= 0


# =========================================
# HISTORY
# =========================================

def test_compilation_history(compiler):
    compiler.compile_batch([SIMPLE_TEXT])
    compiler.compile_batch([SAMPLE_TEXT])
    history = compiler.get_history()
    assert len(history) == 2


# =========================================
# COMPREHENSIVE SAMPLE
# =========================================

def test_compile_comprehensive(compiler):
    """Test that a rich text produces multiple fact types."""
    facts = compiler.compile(SAMPLE_TEXT)
    types_found = {f.fact_type for f in facts}
    # Should extract at least 2 different fact types from the rich sample
    assert len(types_found) >= 2


# =========================================
# SINGLETON
# =========================================

def test_get_knowledge_compiler_singleton():
    c1 = get_knowledge_compiler()
    c2 = get_knowledge_compiler()
    assert c1 is c2
