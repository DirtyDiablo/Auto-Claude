"""Tests for Phase 49A — NL-to-Workflow Engine."""

import pytest

from src.workflows.nl_to_workflow import (
    NLToWorkflowEngine,
    IntentType,
    ValidationStatus,
    NLExecutionResult,
    get_nl_engine,
)


@pytest.fixture
def nl():
    return NLToWorkflowEngine()


# =========================================
# INTENT PARSING — CAMPAIGNS
# =========================================


def test_parse_campaign_intent(nl):
    intent = nl.parse_intent("Run full BD campaign for DCGS-A")
    assert intent.intent == IntentType.CREATE_CAMPAIGN
    assert intent.confidence >= 0.85
    assert intent.matched_workflow_id == "wf_full_bd_campaign"


def test_parse_campaign_launch(nl):
    intent = nl.parse_intent("Start BD campaign for JADC2")
    assert intent.intent == IntentType.CREATE_CAMPAIGN


def test_parse_campaign_create(nl):
    intent = nl.parse_intent("Create a campaign for NCR region")
    assert intent.intent == IntentType.CREATE_CAMPAIGN


# =========================================
# INTENT PARSING — ENRICHMENT
# =========================================


def test_parse_enrich_contact(nl):
    intent = nl.parse_intent("Enrich contact John Smith")
    assert intent.intent == IntentType.ENRICH_CONTACT
    assert intent.confidence >= 0.90
    assert intent.extracted_params.get("contact_name") == "John Smith"


def test_parse_update_contact(nl):
    intent = nl.parse_intent("Update contact data for our Leidos connections")
    assert intent.intent == IntentType.ENRICH_CONTACT


# =========================================
# INTENT PARSING — SCRAPING
# =========================================


def test_parse_scrape_jobs(nl):
    intent = nl.parse_intent("Scrape jobs from defense boards")
    assert intent.intent == IntentType.SCRAPE_JOBS
    assert intent.confidence >= 0.90


def test_parse_run_scraper(nl):
    intent = nl.parse_intent("Run scraper for new postings")
    assert intent.intent == IntentType.SCRAPE_JOBS


# =========================================
# INTENT PARSING — SCORING
# =========================================


def test_parse_score_pipeline(nl):
    intent = nl.parse_intent("Rescore pipeline opportunities")
    assert intent.intent == IntentType.SCORE_PIPELINE
    assert intent.confidence >= 0.85


def test_parse_update_scores(nl):
    intent = nl.parse_intent("Update scores for all BD opportunities")
    assert intent.intent == IntentType.SCORE_PIPELINE


# =========================================
# INTENT PARSING — REPORTS
# =========================================


def test_parse_generate_report(nl):
    intent = nl.parse_intent("Generate weekly report for leadership")
    assert intent.intent == IntentType.GENERATE_REPORT
    assert intent.confidence >= 0.85


def test_parse_weekly_intel(nl):
    intent = nl.parse_intent("Create weekly intel summary")
    assert intent.intent == IntentType.GENERATE_REPORT


# =========================================
# INTENT PARSING — COMPETITION
# =========================================


def test_parse_analyze_competition(nl):
    intent = nl.parse_intent("Analyze competition in the NCR region")
    assert intent.intent == IntentType.ANALYZE_COMPETITION


def test_parse_competitive_density(nl):
    intent = nl.parse_intent("Check competitive density for southeast")
    assert intent.intent == IntentType.ANALYZE_COMPETITION


# =========================================
# INTENT PARSING — FIND CONTACTS
# =========================================


def test_parse_find_contacts(nl):
    intent = nl.parse_intent("Find contacts at Northrop Grumman")
    assert intent.intent == IntentType.FIND_CONTACTS
    assert "Northrop Grumman" in str(intent.entities)


# =========================================
# INTENT PARSING — SCHEDULE
# =========================================


def test_parse_schedule_cycle(nl):
    intent = nl.parse_intent("Run weekly intel cycle now")
    assert intent.intent == IntentType.SCHEDULE_CYCLE


# =========================================
# INTENT PARSING — UNKNOWN
# =========================================


def test_parse_unknown_intent(nl):
    intent = nl.parse_intent("What is the meaning of life?")
    assert intent.intent == IntentType.UNKNOWN
    assert intent.confidence < 0.5


def test_parse_empty_text(nl):
    intent = nl.parse_intent("")
    assert intent.intent == IntentType.UNKNOWN
    assert intent.confidence == 0.0


def test_parse_whitespace_text(nl):
    intent = nl.parse_intent("   ")
    assert intent.intent == IntentType.UNKNOWN


# =========================================
# ENTITY EXTRACTION
# =========================================


def test_extract_program_entity(nl):
    intent = nl.parse_intent("Run campaign for DCGS-A")
    programs = [e for e in intent.entities if "program:" in e]
    assert len(programs) >= 1


def test_extract_company_entity(nl):
    intent = nl.parse_intent("Find contacts at Leidos")
    companies = [e for e in intent.entities if "company:" in e]
    assert len(companies) >= 1


def test_extract_region_entity(nl):
    intent = nl.parse_intent("Competitive analysis for NCR")
    regions = [e for e in intent.entities if "region:" in e]
    assert len(regions) >= 1


def test_extract_params_programs(nl):
    intent = nl.parse_intent("Run BD campaign for JADC2 and GBSD programs")
    assert "JADC2" in intent.extracted_params.get("programs", [])
    assert "GBSD" in intent.extracted_params.get("programs", [])


# =========================================
# VALIDATION
# =========================================


def test_validate_valid_intent(nl):
    intent = nl.parse_intent("Run full BD campaign for DCGS-A")
    result = nl.validate(intent)
    assert result.status == ValidationStatus.VALID
    assert result.workflow_id == "wf_full_bd_campaign"


def test_validate_unknown_intent(nl):
    intent = nl.parse_intent("Do something random")
    result = nl.validate(intent)
    assert result.status in (ValidationStatus.INVALID, ValidationStatus.AMBIGUOUS)


def test_validate_missing_params(nl):
    intent = nl.parse_intent("Enrich contact")
    result = nl.validate(intent)
    assert result.status == ValidationStatus.NEEDS_PARAMS
    assert "contact_name" in result.missing_params


# =========================================
# EXECUTION
# =========================================


def test_execute_valid(nl):
    result = nl.execute("Run full BD campaign for DCGS-A")
    assert isinstance(result, NLExecutionResult)
    assert result.status == "ready"
    assert result.intent.intent == IntentType.CREATE_CAMPAIGN


def test_execute_invalid(nl):
    result = nl.execute("What is the meaning of life?")
    assert result.status in ("invalid", "ambiguous")


def test_execute_returns_unique_id(nl):
    r1 = nl.execute("Run full BD campaign")
    r2 = nl.execute("Run full BD campaign")
    assert r1.execution_id != r2.execution_id


def test_get_execution(nl):
    result = nl.execute("Run full BD campaign")
    fetched = nl.get_execution(result.execution_id)
    assert fetched is not None
    assert fetched.execution_id == result.execution_id


def test_get_execution_not_found(nl):
    assert nl.get_execution("nlexec_nonexistent") is None


def test_list_executions(nl):
    nl.execute("Run full BD campaign")
    nl.execute("Enrich contact John Smith")
    execs = nl.list_executions()
    assert len(execs) == 2


# =========================================
# AUTOCOMPLETE
# =========================================


def test_autocomplete(nl):
    suggestions = nl.autocomplete("Run")
    assert len(suggestions) >= 1
    assert all("template" in s for s in suggestions)


def test_autocomplete_campaign(nl):
    suggestions = nl.autocomplete("campaign")
    assert len(suggestions) >= 1


def test_autocomplete_empty(nl):
    suggestions = nl.autocomplete("")
    assert suggestions == []


# =========================================
# TO DICT
# =========================================


def test_parsed_intent_to_dict(nl):
    intent = nl.parse_intent("Run full BD campaign")
    d = intent.to_dict()
    assert "intent" in d
    assert "confidence" in d
    assert "extracted_params" in d


def test_execution_to_dict(nl):
    result = nl.execute("Run full BD campaign")
    d = result.to_dict()
    assert "execution_id" in d
    assert "intent" in d
    assert "validation" in d


# =========================================
# STATS
# =========================================


def test_stats(nl):
    nl.execute("Run full BD campaign")
    stats = nl.get_stats()
    assert stats["total_executions"] >= 1
    assert len(stats["available_workflows"]) == 4


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    import src.workflows.nl_to_workflow as mod

    mod._instance = None
    s1 = get_nl_engine()
    s2 = get_nl_engine()
    assert s1 is s2
    mod._instance = None
