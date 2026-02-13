"""
Phase 23A — Morning Briefing v2 Tests

Tests production morning briefing: parallel gathers, merging, prioritization,
quality check, fallback, and delivery.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.workflows.production.morning_briefing import (
    MORNING_BRIEFING_STATE,
    gather_pipeline_updates, gather_new_jobs, gather_competitive_intel,
    gather_contact_changes, gather_graph_insights, merge_all_sections,
    prioritize_items, format_briefing, quality_check, quality_router,
    deliver, get_morning_briefing_definition,
)


def test_state_schema_keys():
    expected = {"briefing_date", "pipeline_updates", "new_jobs", "competitive_intel",
                "contact_changes", "graph_insights", "merged_items", "briefing",
                "quality_score", "delivery_results", "errors", "step_timings"}
    assert set(MORNING_BRIEFING_STATE.keys()) == expected


@pytest.mark.asyncio
async def test_gather_pipeline_updates():
    state = {}
    result = await gather_pipeline_updates(state)
    assert "pipeline_updates" in result
    assert isinstance(result["pipeline_updates"], list)


@pytest.mark.asyncio
async def test_gather_new_jobs():
    state = {}
    result = await gather_new_jobs(state)
    assert "new_jobs" in result


@pytest.mark.asyncio
async def test_gather_competitive_intel():
    state = {}
    result = await gather_competitive_intel(state)
    assert "competitive_intel" in result


@pytest.mark.asyncio
async def test_gather_contact_changes():
    state = {}
    result = await gather_contact_changes(state)
    assert "contact_changes" in result


@pytest.mark.asyncio
async def test_gather_graph_insights():
    state = {}
    result = await gather_graph_insights(state)
    assert "graph_insights" in result


@pytest.mark.asyncio
async def test_merge_all_sections():
    state = {
        "pipeline_updates": [{"type": "update", "priority": "high"}],
        "new_jobs": [{"type": "job", "priority": "medium"}],
        "competitive_intel": [],
        "contact_changes": [{"type": "contact", "priority": "critical"}],
        "graph_insights": [],
    }
    result = await merge_all_sections(state)
    assert len(result["merged_items"]) == 3


@pytest.mark.asyncio
async def test_prioritize_items_order():
    state = {"merged_items": [
        {"priority": "low", "type": "a"},
        {"priority": "critical", "type": "b"},
        {"priority": "medium", "type": "c"},
    ]}
    result = await prioritize_items(state)
    assert result["merged_items"][0]["priority"] == "critical"
    assert result["merged_items"][-1]["priority"] == "low"


@pytest.mark.asyncio
async def test_quality_check_high():
    state = {
        "briefing": {
            "sections": {
                "pipeline_updates": [1], "new_jobs": [1], "competitive_intel": [1],
                "contact_changes": [1], "graph_insights": [1],
            },
            "total_items": 20,
            "executive_summary": "This is a substantial executive summary for the morning briefing."
        }
    }
    result = await quality_check(state)
    assert result["quality_score"] >= 0.6


@pytest.mark.asyncio
async def test_quality_check_low():
    state = {"briefing": {"sections": {}, "total_items": 0, "executive_summary": ""}}
    result = await quality_check(state)
    assert result["quality_score"] < 0.6


def test_quality_router_pass():
    assert quality_router({"quality_score": 0.8}) == "deliver"


def test_quality_router_fail():
    assert quality_router({"quality_score": 0.3}) == "fallback_briefing"


@pytest.mark.asyncio
async def test_format_briefing():
    state = {
        "merged_items": [{"type": "job", "priority": "high"}, {"type": "contact", "priority": "critical"}],
        "briefing_date": "2024-01-15",
        "pipeline_updates": [], "new_jobs": [], "competitive_intel": [],
        "contact_changes": [], "graph_insights": [],
    }
    result = await format_briefing(state)
    assert "briefing" in result
    assert result["briefing"]["total_items"] == 2


@pytest.mark.asyncio
async def test_deliver():
    state = {"briefing": {"date": "2024-01-15"}}
    result = await deliver(state)
    assert result["delivery_results"]["dashboard"] is True


def test_get_definition_no_interrupts():
    defn = get_morning_briefing_definition()
    assert defn.name == "morning_briefing"
    assert defn.interrupt_nodes == []
    assert len(defn.parallel_groups) == 1
    assert len(defn.parallel_groups[0]) == 5
