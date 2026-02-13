"""
Phase 23A — Pipeline Manager v2 Tests

Tests production pipeline manager: scanning, stale detection, deadline checking,
budget cycles, risk analysis, recommendations, and human approval gate.
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.workflows.production.pipeline_manager import (
    PIPELINE_MANAGER_STATE,
    scan_pipeline, check_stale_items, check_upcoming_deadlines,
    check_budget_cycles, merge_pipeline_state, analyze_risks,
    recommend_actions, review_recommendations, execute_approved_actions,
    generate_pipeline_report, get_pipeline_manager_definition,
)


def test_state_schema_keys():
    expected = {"scan_date", "active_opportunities", "stale_items",
                "upcoming_deadlines", "budget_cycles", "pipeline_state",
                "risks", "recommendations", "human_approved_actions",
                "execution_results", "report", "errors", "step_timings"}
    assert set(PIPELINE_MANAGER_STATE.keys()) == expected


@pytest.mark.asyncio
async def test_scan_pipeline():
    state = {}
    result = await scan_pipeline(state)
    assert "scan_date" in result
    assert "active_opportunities" in result


@pytest.mark.asyncio
async def test_check_stale_items_none():
    now = datetime.utcnow().isoformat()
    state = {"active_opportunities": [
        {"title": "Fresh", "last_activity": now, "bd_priority": "medium"},
    ]}
    result = await check_stale_items(state)
    assert len(result["stale_items"]) == 0


@pytest.mark.asyncio
async def test_check_stale_items_found():
    old = (datetime.utcnow() - timedelta(days=30)).isoformat()
    state = {"active_opportunities": [
        {"title": "Stale Job", "last_activity": old, "bd_priority": "high"},
    ]}
    result = await check_stale_items(state)
    assert len(result["stale_items"]) >= 1


@pytest.mark.asyncio
async def test_check_upcoming_deadlines():
    state = {"active_opportunities": [
        {"title": "RFP Response", "program": "DCGS", "status": "proposal_due"},
    ]}
    result = await check_upcoming_deadlines(state)
    assert len(result["upcoming_deadlines"]) >= 1


@pytest.mark.asyncio
async def test_check_budget_cycles():
    state = {}
    result = await check_budget_cycles(state)
    assert len(result["budget_cycles"]) >= 1
    assert "days_to_fy_end" in result["budget_cycles"][0]


@pytest.mark.asyncio
async def test_merge_pipeline_state():
    state = {
        "active_opportunities": [{"title": "A"}, {"title": "B"}],
        "stale_items": [{"title": "A"}],
        "upcoming_deadlines": [],
        "budget_cycles": [],
    }
    result = await merge_pipeline_state(state)
    assert result["pipeline_state"]["total_opportunities"] == 2
    assert result["pipeline_state"]["health_score"] <= 1.0


@pytest.mark.asyncio
async def test_analyze_risks_critical():
    state = {
        "stale_items": [{"title": "Critical Deal", "bd_priority": "critical",
                          "company": "GDIT", "stale_days": 21}],
        "upcoming_deadlines": [],
    }
    result = await analyze_risks(state)
    assert len(result["risks"]) >= 1
    assert result["risks"][0]["severity"] == "critical"


@pytest.mark.asyncio
async def test_recommend_actions():
    state = {
        "risks": [{"opportunity": "Deal A", "recommendation": "Follow up",
                    "severity": "critical"}],
        "stale_items": [{"title": "Deal B", "bd_priority": "medium", "stale_days": 20}],
    }
    result = await recommend_actions(state)
    assert len(result["recommendations"]) >= 2


@pytest.mark.asyncio
async def test_review_recommendations():
    auto = [{"opportunity": "Deal A", "auto_execute": True}]
    state = {"recommendations": auto, "human_approved_actions": []}
    result = await review_recommendations(state)
    assert "human_approved_actions" in result


@pytest.mark.asyncio
async def test_execute_approved_actions():
    state = {"human_approved_actions": [
        {"opportunity": "Deal A", "action": "Send follow-up"},
    ]}
    result = await execute_approved_actions(state)
    assert len(result["execution_results"]) == 1


@pytest.mark.asyncio
async def test_generate_pipeline_report():
    state = {
        "scan_date": "2024-01-15",
        "pipeline_state": {"health_score": 0.75, "total_opportunities": 10,
                           "stale_count": 2, "upcoming_deadlines_count": 1},
        "risks": [{"severity": "critical"}],
        "recommendations": [{"action": "test"}],
        "execution_results": [{"status": "executed"}],
        "budget_cycles": [],
        "step_timings": {},
    }
    result = await generate_pipeline_report(state)
    assert result["report"]["pipeline_health"] == 0.75
    assert result["report"]["risks_identified"] == 1


def test_get_definition():
    defn = get_pipeline_manager_definition()
    assert defn.name == "pipeline_manager"
    assert "review_recommendations" in defn.interrupt_nodes
    assert len(defn.parallel_groups) == 1
    assert "check_stale_items" in defn.parallel_groups[0]
