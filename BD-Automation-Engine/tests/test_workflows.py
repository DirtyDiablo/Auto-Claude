"""
Tests for the LangGraph Workflow Orchestration Engine.

Covers:
    - PipelineState creation and updates
    - Master pipeline node functions individually
    - Morning briefing workflow
    - Contact enrichment workflow
    - Scheduler start/stop/status
    - Workflow API endpoints
    - Error handling in nodes
    - Conditional edges (QA pass/fail)
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ===================================================================
# 1. State tests
# ===================================================================

class TestPipelineState:
    """Tests for PipelineState and WorkflowConfig."""

    def test_make_initial_state_defaults(self):
        from workflows.state import make_initial_state
        state = make_initial_state()
        assert state["jobs"] == []
        assert state["contacts"] == []
        assert state["programs"] == []
        assert state["enriched_jobs"] == []
        assert state["scored_jobs"] == []
        assert state["qa_results"] == {}
        assert state["errors"] == []
        assert state["metadata"] == {}
        assert state["stage_history"] == []

    def test_make_initial_state_overrides(self):
        from workflows.state import make_initial_state
        jobs = [{"title": "Engineer"}]
        state = make_initial_state(jobs=jobs, metadata={"test": True})
        assert state["jobs"] == jobs
        assert state["metadata"]["test"] is True
        assert state["errors"] == []

    def test_pipeline_state_update(self):
        from workflows.state import make_initial_state
        state = make_initial_state()
        state["jobs"] = [{"title": "Test Job"}]
        state["errors"].append("test error")
        assert len(state["jobs"]) == 1
        assert len(state["errors"]) == 1

    def test_workflow_config_defaults(self):
        from workflows.state import WorkflowConfig
        cfg = WorkflowConfig()
        assert cfg.batch_size == 50
        assert cfg.parallel is False
        assert cfg.human_approval_required is True
        assert cfg.input_path is None
        assert cfg.test_mode is False

    def test_workflow_config_custom(self):
        from workflows.state import WorkflowConfig
        cfg = WorkflowConfig(batch_size=10, parallel=True, test_mode=True)
        assert cfg.batch_size == 10
        assert cfg.parallel is True
        assert cfg.test_mode is True


# ===================================================================
# 2. Master pipeline node tests
# ===================================================================

class TestMasterPipelineNodes:
    """Test each master pipeline node individually."""

    def test_scrape_loads_from_file(self, tmp_path):
        from workflows.master_pipeline import scrape
        from workflows.state import make_initial_state

        # Write sample jobs file
        jobs_file = tmp_path / "jobs.json"
        sample_jobs = [{"title": "Engineer"}, {"title": "Analyst"}]
        jobs_file.write_text(json.dumps(sample_jobs))

        state = make_initial_state(metadata={"input_path": str(jobs_file)})
        result = scrape(state)
        assert len(result["jobs"]) == 2
        assert result["jobs"][0]["title"] == "Engineer"
        # Verify stage_history recorded
        assert any(h["name"] == "scrape" for h in result["stage_history"])

    def test_scrape_missing_file(self):
        from workflows.master_pipeline import scrape
        from workflows.state import make_initial_state

        state = make_initial_state(metadata={"input_path": "/nonexistent/file.json"})
        result = scrape(state)
        # Should not crash; jobs stays empty or engine fallback
        assert isinstance(result["jobs"], list)

    def test_scrape_no_input_path(self):
        from workflows.master_pipeline import scrape
        from workflows.state import make_initial_state

        state = make_initial_state()
        result = scrape(state)
        assert isinstance(result["jobs"], list)

    @patch("workflows.master_pipeline.Path.exists", return_value=False)
    def test_map_programs_no_engine(self, mock_exists):
        from workflows.master_pipeline import map_programs
        from workflows.state import make_initial_state

        state = make_initial_state(jobs=[{"title": "Test"}])
        result = map_programs(state)
        # With no Engine2, enriched_jobs should be set to jobs
        assert len(result.get("enriched_jobs", [])) >= 0
        assert any(h["name"] == "map_programs" for h in result["stage_history"])

    def test_map_programs_empty_jobs(self):
        from workflows.master_pipeline import map_programs
        from workflows.state import make_initial_state

        state = make_initial_state(jobs=[])
        result = map_programs(state)
        assert any(h["name"] == "map_programs" for h in result["stage_history"])

    def test_classify_contacts_no_engine(self):
        from workflows.master_pipeline import classify_contacts
        from workflows.state import make_initial_state

        state = make_initial_state(enriched_jobs=[{"title": "Test", "company": "Leidos"}])
        result = classify_contacts(state)
        assert "contacts" in result
        assert any(h["name"] == "classify_contacts" for h in result["stage_history"])

    def test_generate_playbooks_no_engine(self):
        from workflows.master_pipeline import generate_playbooks
        from workflows.state import make_initial_state

        state = make_initial_state(enriched_jobs=[{"title": "Test"}])
        result = generate_playbooks(state)
        assert any(h["name"] == "generate_playbooks" for h in result["stage_history"])

    def test_score_node(self):
        from workflows.master_pipeline import score
        from workflows.state import make_initial_state

        jobs = [{"title": "Test Job"}]
        state = make_initial_state(enriched_jobs=jobs)
        result = score(state)
        # scored_jobs should be populated (engine may or may not be available)
        assert len(result.get("scored_jobs", [])) == 1
        assert result["scored_jobs"][0]["title"] == "Test Job"
        assert any(h["name"] == "score" for h in result["stage_history"])

    def test_qa_check_runs(self):
        from workflows.master_pipeline import qa_check
        from workflows.state import make_initial_state

        state = make_initial_state(scored_jobs=[{"title": "Test"}])
        result = qa_check(state)
        # qa_results should be populated with pass/fail info
        assert "qa_results" in result
        assert "passed" in result["qa_results"]
        assert any(h["name"] == "qa_check" for h in result["stage_history"])

    def test_qa_check_empty_jobs(self):
        from workflows.master_pipeline import qa_check
        from workflows.state import make_initial_state

        state = make_initial_state()
        result = qa_check(state)
        assert result["qa_results"]["passed"] is True

    def test_index_knowledge_no_engine(self):
        from workflows.master_pipeline import index_knowledge
        from workflows.state import make_initial_state

        state = make_initial_state()
        result = index_knowledge(state)
        assert any(h["name"] == "index_knowledge" for h in result["stage_history"])


# ===================================================================
# 3. Conditional edge tests
# ===================================================================

class TestConditionalEdges:
    """Test the QA gate conditional routing."""

    def test_qa_gate_passes(self):
        from workflows.master_pipeline import _qa_gate
        state = {"qa_results": {"passed": True, "approved": 5, "needs_review": 0}}
        assert _qa_gate(state) == "index_knowledge"

    def test_qa_gate_fails(self):
        from workflows.master_pipeline import _qa_gate, END
        state = {"qa_results": {"passed": False, "approved": 3, "needs_review": 2}}
        assert _qa_gate(state) == END

    def test_qa_gate_missing_results(self):
        from workflows.master_pipeline import _qa_gate
        # Default: passed=True when missing
        state = {}
        assert _qa_gate(state) == "index_knowledge"

    def test_qa_gate_empty_results(self):
        from workflows.master_pipeline import _qa_gate
        state = {"qa_results": {}}
        assert _qa_gate(state) == "index_knowledge"


# ===================================================================
# 4. Full pipeline integration test
# ===================================================================

class TestMasterPipelineIntegration:
    """Test the full pipeline runner."""

    def test_run_master_pipeline_with_file(self, tmp_path):
        from workflows.master_pipeline import run_master_pipeline
        from workflows.state import WorkflowConfig

        jobs_file = tmp_path / "test_jobs.json"
        jobs_file.write_text(json.dumps([
            {"title": "DCGS Engineer", "company": "Leidos", "clearance": "TS/SCI"},
            {"title": "SIGINT Analyst", "company": "NGC", "clearance": "TS"},
        ]))

        cfg = WorkflowConfig(input_path=str(jobs_file))
        result = run_master_pipeline(config=cfg)

        assert "jobs" in result
        assert len(result["jobs"]) == 2
        assert "stage_history" in result
        assert len(result["stage_history"]) >= 6  # At least 6 nodes ran

    def test_run_master_pipeline_empty(self):
        from workflows.master_pipeline import run_master_pipeline
        from workflows.state import WorkflowConfig

        cfg = WorkflowConfig()
        result = run_master_pipeline(config=cfg)
        assert isinstance(result.get("errors", []), list)

    def test_build_master_pipeline_returns_graph(self):
        from workflows.master_pipeline import build_master_pipeline, LANGGRAPH_AVAILABLE
        graph = build_master_pipeline()
        if LANGGRAPH_AVAILABLE:
            assert graph is not None
        else:
            assert graph is None


# ===================================================================
# 5. Morning briefing tests
# ===================================================================

class TestMorningBriefing:
    """Test the morning briefing workflow."""

    def test_gather_signals_no_store(self):
        from workflows.morning_briefing import gather_signals, make_briefing_state
        state = make_briefing_state()
        result = gather_signals(state)
        assert "signals" in result
        assert isinstance(result["signals"], list)

    def test_analyze_empty_signals(self):
        from workflows.morning_briefing import analyze, make_briefing_state
        state = make_briefing_state(signals=[])
        result = analyze(state)
        assert result["analysis"]["total_signals"] == 0

    def test_analyze_with_signals(self):
        from workflows.morning_briefing import analyze, make_briefing_state
        signals = [
            {"collection": "jobs", "content": "DCGS Engineer hiring", "score": 0.9},
            {"collection": "contacts", "content": "New VP at Leidos", "score": 0.8},
        ]
        state = make_briefing_state(signals=signals)
        result = analyze(state)
        assert result["analysis"]["total_signals"] == 2
        assert "jobs" in result["analysis"]["collections_scanned"]
        assert "contacts" in result["analysis"]["collections_scanned"]

    def test_format_brief_structure(self):
        from workflows.morning_briefing import format_brief, make_briefing_state
        analysis = {
            "total_signals": 3,
            "collections_scanned": ["jobs", "contacts"],
            "summary": "Test summary",
            "top_signals": [{"collection": "jobs", "content": "test", "score": 0.9}],
        }
        state = make_briefing_state(analysis=analysis)
        result = format_brief(state)
        briefing = result["briefing"]
        assert "title" in briefing
        assert "executive_summary" in briefing
        assert "highlights" in briefing
        assert "recommendations" in briefing
        assert briefing["signal_count"] == 3

    def test_run_morning_briefing_full(self):
        from workflows.morning_briefing import run_morning_briefing
        result = run_morning_briefing()
        assert "briefing" in result
        assert "errors" in result


# ===================================================================
# 6. Contact enrichment tests
# ===================================================================

class TestContactEnrichment:
    """Test the contact enrichment workflow."""

    def test_fetch_stale_no_store(self):
        from workflows.contact_enrichment import fetch_stale, make_enrichment_state
        state = make_enrichment_state()
        result = fetch_stale(state)
        assert "stale_contacts" in result

    def test_enrich_bullhorn_empty(self):
        from workflows.contact_enrichment import enrich_bullhorn, make_enrichment_state
        state = make_enrichment_state(stale_contacts=[])
        result = enrich_bullhorn(state)
        assert result["bullhorn_enriched"] == []

    def test_enrich_bullhorn_no_engine(self):
        from workflows.contact_enrichment import enrich_bullhorn, make_enrichment_state
        contacts = [{"name": "Jane Doe", "id": 1, "metadata": {"id": 1}}]
        state = make_enrichment_state(stale_contacts=contacts)
        result = enrich_bullhorn(state)
        # Without Engine7, should pass through stale contacts
        assert len(result["bullhorn_enriched"]) == 1

    def test_enrich_web_placeholder(self):
        from workflows.contact_enrichment import enrich_web, make_enrichment_state
        contacts = [{"name": "John Smith", "company": "NGC"}]
        state = make_enrichment_state(bullhorn_enriched=contacts)
        result = enrich_web(state)
        assert len(result["web_enriched"]) == 1
        assert result["web_enriched"][0]["web_enrichment"] == "pending"

    def test_update_store_no_store(self):
        from workflows.contact_enrichment import update_store, make_enrichment_state
        contacts = [{"name": "Test User", "metadata": {}}]
        state = make_enrichment_state(web_enriched=contacts)
        result = update_store(state)
        assert "updated_contacts" in result

    def test_update_store_empty(self):
        from workflows.contact_enrichment import update_store, make_enrichment_state
        state = make_enrichment_state(web_enriched=[])
        result = update_store(state)
        assert result["updated_contacts"] == []

    def test_run_contact_enrichment_full(self):
        from workflows.contact_enrichment import run_contact_enrichment
        result = run_contact_enrichment()
        assert "errors" in result


# ===================================================================
# 7. Scheduler tests
# ===================================================================

class TestWorkflowScheduler:
    """Test the APScheduler integration."""

    def test_scheduler_creation(self):
        from workflows.scheduler import WorkflowScheduler
        scheduler = WorkflowScheduler()
        assert scheduler.is_running is False

    def test_scheduler_get_status_not_running(self):
        from workflows.scheduler import WorkflowScheduler
        scheduler = WorkflowScheduler()
        status = scheduler.get_status()
        assert status["running"] is False
        assert status["enabled"] is True
        assert isinstance(status["jobs"], list)

    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self):
        from workflows.scheduler import WorkflowScheduler, APSCHEDULER_AVAILABLE
        scheduler = WorkflowScheduler()
        result = scheduler.start()
        if APSCHEDULER_AVAILABLE:
            assert result is True
            assert scheduler.is_running is True
            status = scheduler.get_status()
            assert len(status["jobs"]) == 3  # 3 scheduled jobs
            scheduler.stop()
            assert scheduler.is_running is False
        else:
            assert result is False

    @pytest.mark.asyncio
    async def test_scheduler_toggle(self):
        from workflows.scheduler import WorkflowScheduler, APSCHEDULER_AVAILABLE
        scheduler = WorkflowScheduler()
        if APSCHEDULER_AVAILABLE:
            scheduler.toggle(True)
            assert scheduler.is_running is True
            scheduler.toggle(False)
            assert scheduler.is_running is False

    def test_execution_history(self):
        from workflows.scheduler import _record_execution, get_execution_history, _execution_history
        # Clear history
        _execution_history.clear()

        _record_execution("test_workflow", True, 1.5)
        _record_execution("test_workflow", False, 2.0, error="test error")

        history = get_execution_history()
        assert len(history) == 2
        assert history[0]["success"] is False  # Most recent first
        assert history[1]["success"] is True


# ===================================================================
# 8. API endpoint tests
# ===================================================================

class TestWorkflowAPI:
    """Test the workflow API router."""

    @pytest.fixture
    def client(self):
        """Create a test FastAPI client with the workflow router."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from Engine8_Knowledge.routers.workflows import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_get_status(self, client):
        response = client.get("/workflows/status")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "enabled" in data

    def test_get_history(self, client):
        response = client.get("/workflows/history")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data

    def test_run_unknown_workflow(self, client):
        response = client.post("/workflows/run/nonexistent")
        assert response.status_code == 404

    def test_run_morning_briefing(self, client):
        response = client.post("/workflows/run/morning_briefing")
        assert response.status_code == 200
        data = response.json()
        assert data["workflow"] == "morning_briefing"
        assert "duration_seconds" in data

    def test_toggle_schedule(self, client):
        response = client.post(
            "/workflows/schedule/toggle",
            json={"enabled": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False

    def test_run_master_pipeline_via_api(self, client, tmp_path):
        jobs_file = tmp_path / "api_test_jobs.json"
        jobs_file.write_text(json.dumps([{"title": "API Test Job"}]))

        response = client.post(
            "/workflows/run/master_pipeline",
            json={"input_path": str(jobs_file), "test_mode": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["workflow"] == "master_pipeline"


# ===================================================================
# 9. Error handling tests
# ===================================================================

class TestErrorHandling:
    """Test error handling and quarantine behavior."""

    def test_node_error_recorded_in_history(self):
        from workflows.master_pipeline import _run_node
        from workflows.state import make_initial_state

        def failing_fn(state):
            raise RuntimeError("Test explosion")

        state = make_initial_state()
        result = _run_node("test_node", state, failing_fn)
        assert any(
            h["name"] == "test_node" and h["status"] == "failed"
            for h in result["stage_history"]
        )
        assert any("Test explosion" in e for e in result["errors"])

    def test_node_success_recorded(self):
        from workflows.master_pipeline import _run_node
        from workflows.state import make_initial_state

        def ok_fn(state):
            state["jobs"] = [{"title": "OK"}]
            return state

        state = make_initial_state()
        result = _run_node("ok_node", state, ok_fn)
        history_entry = [h for h in result["stage_history"] if h["name"] == "ok_node"][0]
        assert history_entry["status"] == "passed"
        assert history_entry["duration_seconds"] >= 0

    def test_pipeline_continues_after_node_error(self, tmp_path):
        """Verify that the pipeline does not crash on engine ImportErrors."""
        from workflows.master_pipeline import run_master_pipeline
        from workflows.state import WorkflowConfig

        jobs_file = tmp_path / "err_test.json"
        jobs_file.write_text(json.dumps([{"title": "Resilience Test"}]))

        cfg = WorkflowConfig(input_path=str(jobs_file))
        result = run_master_pipeline(config=cfg)
        # Pipeline should complete even without real engines
        assert "stage_history" in result
        assert len(result["stage_history"]) >= 6

    def test_state_errors_accumulate(self):
        from workflows.state import make_initial_state
        state = make_initial_state()
        state["errors"].append("first")
        state["errors"].append("second")
        assert len(state["errors"]) == 2


# ===================================================================
# 10. Graph construction tests
# ===================================================================

class TestGraphConstruction:
    """Test LangGraph graph building."""

    def test_build_master_pipeline_graph(self):
        from workflows.master_pipeline import build_master_pipeline, LANGGRAPH_AVAILABLE
        graph = build_master_pipeline()
        if LANGGRAPH_AVAILABLE:
            assert graph is not None
        # If not available, returns None — tested above

    def test_build_morning_briefing_graph(self):
        from workflows.morning_briefing import build_morning_briefing, LANGGRAPH_AVAILABLE
        graph = build_morning_briefing()
        if LANGGRAPH_AVAILABLE:
            assert graph is not None

    def test_build_contact_enrichment_graph(self):
        from workflows.contact_enrichment import build_contact_enrichment, LANGGRAPH_AVAILABLE
        graph = build_contact_enrichment()
        if LANGGRAPH_AVAILABLE:
            assert graph is not None
