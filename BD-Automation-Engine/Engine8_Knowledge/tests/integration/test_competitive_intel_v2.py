"""
Phase 23A — Competitive Intelligence v2 Tests

Tests production competitive intel workflow: planning, parallel scraping,
merging, LLM analysis, human validation, and briefing generation.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.workflows.production.competitive_intel import (
    COMPETITIVE_INTEL_STATE,
    plan_collection, scrape_job_boards, scrape_sam_gov, scrape_linkedin,
    scrape_news, merge_raw_intel, analyze_with_llm, validate_findings,
    generate_briefing, get_competitive_intel_definition,
)


def test_state_schema_keys():
    expected = {"collection_plan", "raw_intel", "raw_job_boards", "raw_sam_gov",
                "raw_linkedin", "raw_news", "merged_intel", "analysis",
                "human_validated", "graph_links", "briefing",
                "distribution_results", "errors", "step_timings"}
    assert set(COMPETITIVE_INTEL_STATE.keys()) == expected


@pytest.mark.asyncio
async def test_plan_collection_default():
    state = {"collection_plan": {}}
    result = await plan_collection(state)
    assert len(result["collection_plan"]["sources"]) == 4
    assert "DCGS" in result["collection_plan"]["focus_areas"]


@pytest.mark.asyncio
async def test_plan_collection_existing():
    plan = {"sources": ["news"], "focus_areas": ["GBSD"], "competitors": []}
    state = {"collection_plan": plan}
    result = await plan_collection(state)
    assert result["collection_plan"]["sources"] == ["news"]


@pytest.mark.asyncio
async def test_scrape_job_boards():
    state = {"collection_plan": {"competitors": ["GDIT", "Leidos"], "focus_areas": []}}
    result = await scrape_job_boards(state)
    assert "raw_job_boards" in result
    assert isinstance(result["raw_job_boards"], list)


@pytest.mark.asyncio
async def test_scrape_sam_gov():
    state = {"collection_plan": {"focus_areas": ["DCGS"]}}
    result = await scrape_sam_gov(state)
    assert "raw_sam_gov" in result


@pytest.mark.asyncio
async def test_scrape_linkedin():
    state = {"collection_plan": {"competitors": ["Raytheon"]}}
    result = await scrape_linkedin(state)
    assert "raw_linkedin" in result
    assert len(result["raw_linkedin"]) >= 1


@pytest.mark.asyncio
async def test_scrape_news():
    state = {"collection_plan": {"focus_areas": ["DCGS"], "competitors": []}}
    result = await scrape_news(state)
    assert "raw_news" in result


@pytest.mark.asyncio
async def test_merge_raw_intel_dedup():
    state = {
        "raw_job_boards": [{"source": "job_board", "title": "Analyst", "company": "GDIT"}],
        "raw_sam_gov": [{"source": "sam_gov", "title": "Contract", "company": ""}],
        "raw_linkedin": [{"source": "linkedin", "title": "Analyst", "company": "GDIT"}],
        "raw_news": [],
    }
    result = await merge_raw_intel(state)
    assert len(result["merged_intel"]) == 3  # deduped by source:title:company


@pytest.mark.asyncio
async def test_analyze_with_llm_alerts():
    state = {"merged_intel": [
        {"source": "job_board", "company": "GDIT"} for _ in range(6)
    ]}
    result = await analyze_with_llm(state)
    assert len(result["analysis"]["high_confidence_alerts"]) >= 1


@pytest.mark.asyncio
async def test_analyze_no_alerts():
    state = {"merged_intel": [{"source": "news", "company": "Unknown"}]}
    result = await analyze_with_llm(state)
    assert result["analysis"]["high_confidence_alerts"] == []


@pytest.mark.asyncio
async def test_validate_findings():
    state = {"human_validated": False}
    result = await validate_findings(state)
    assert "human_validated" in result


@pytest.mark.asyncio
async def test_generate_briefing():
    state = {
        "analysis": {"high_confidence_alerts": [{"description": "Test alert"}],
                      "hiring_trends": {"GDIT": [1, 2]}, "contract_signals": [],
                      "total_signals": 5, "risk_factors": []},
        "graph_links": [],
    }
    result = await generate_briefing(state)
    assert "briefing" in result
    assert result["briefing"]["total_signals"] == 5


def test_get_definition():
    defn = get_competitive_intel_definition()
    assert defn.name == "competitive_intel"
    assert "validate_findings" in defn.interrupt_nodes
    assert len(defn.parallel_groups) == 1
    assert "scrape_job_boards" in defn.parallel_groups[0]
