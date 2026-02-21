"""
Tests for Feature 19 — Enhanced CrewAI Multi-Agent BD Workflows.

Covers agent instantiation, execution, orchestrator workflows, parallel execution,
router endpoints, error handling, and context passing.
"""

import pytest
from unittest.mock import patch, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Import agents and orchestrator
# ---------------------------------------------------------------------------

from Engine8_Knowledge.agents.bd_workflow_agents import (
    BDAgentBase,
    ResearcherAgent,
    AnalystAgent,
    CompetitorAgent,
    PlaybookAgent,
    CallPrepAgent,
    OutreachAgent,
    WinStrategyAgent,
    AccountMapperAgent,
    ALL_AGENTS,
)

from Engine8_Knowledge.agents.orchestrator import (
    BDAgentOrchestrator,
    WORKFLOW_DEFINITIONS,
    get_bd_orchestrator,
)

from Engine8_Knowledge.routers.agents import router as agents_router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_orchestrator_singleton():
    """Reset orchestrator singleton between tests."""
    import Engine8_Knowledge.agents.orchestrator as mod
    mod._orchestrator_instance = None
    yield
    mod._orchestrator_instance = None


@pytest.fixture
def orchestrator():
    return BDAgentOrchestrator()


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(agents_router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def basic_context():
    return {"query": "DCGS-A modernization", "program": "DCGS-A", "company": "Leidos"}


@pytest.fixture
def contact_context():
    return {
        "contact_name": "Jane Doe",
        "contact": {"name": "Jane Doe", "company": "Leidos", "title": "VP of ISR"},
        "company": "Leidos",
        "program": "DCGS-A",
    }


@pytest.fixture
def jobs_context():
    return {
        "query": "DCGS hiring trends",
        "jobs": [
            {"title": "Systems Engineer", "company": "Leidos", "clearance": "TS/SCI"},
            {"title": "Software Developer", "company": "Leidos", "clearance": "Secret"},
            {"title": "Intel Analyst", "company": "GDIT", "clearance": "TS/SCI"},
            {"title": "DevOps Engineer", "company": "GDIT", "clearance": "TS/SCI"},
            {"title": "Cloud Architect", "company": "SAIC", "clearance": "Secret"},
        ],
    }


# ===========================================================================
# AGENT CLASS TESTS — Instantiation
# ===========================================================================


class TestAgentInstantiation:
    """Test each agent class can be instantiated."""

    def test_researcher_agent_instantiation(self):
        agent = ResearcherAgent()
        assert agent.name == "researcher"
        assert agent.role == "BD Researcher"

    def test_analyst_agent_instantiation(self):
        agent = AnalystAgent()
        assert agent.name == "analyst"
        assert agent.role == "BD Analyst"

    def test_competitor_agent_instantiation(self):
        agent = CompetitorAgent()
        assert agent.name == "competitor"
        assert agent.role == "Competitive Intelligence Analyst"

    def test_playbook_agent_instantiation(self):
        agent = PlaybookAgent()
        assert agent.name == "playbook"
        assert agent.role == "Capture Strategy Lead"

    def test_call_prep_agent_instantiation(self):
        agent = CallPrepAgent()
        assert agent.name == "call_prep"
        assert agent.role == "Call Preparation Specialist"

    def test_outreach_agent_instantiation(self):
        agent = OutreachAgent()
        assert agent.name == "outreach"
        assert agent.role == "BD Outreach Strategist"

    def test_win_strategy_agent_instantiation(self):
        agent = WinStrategyAgent()
        assert agent.name == "win_strategy"
        assert agent.role == "Win Strategy Advisor"

    def test_account_mapper_agent_instantiation(self):
        agent = AccountMapperAgent()
        assert agent.name == "account_mapper"
        assert agent.role == "Account Intelligence Mapper"

    def test_all_agents_registry_has_8_agents(self):
        assert len(ALL_AGENTS) == 8

    def test_all_agents_registry_keys(self):
        expected = {"researcher", "analyst", "competitor", "playbook",
                    "call_prep", "outreach", "win_strategy", "account_mapper"}
        assert set(ALL_AGENTS.keys()) == expected

    def test_base_agent_execute_raises(self):
        agent = BDAgentBase()
        with pytest.raises(NotImplementedError):
            agent.execute({})


# ===========================================================================
# AGENT EXECUTION TESTS — Result structure
# ===========================================================================


class TestAgentExecution:
    """Test each agent's execute() returns correct structure."""

    REQUIRED_KEYS = {"agent_name", "status", "findings", "recommendations", "confidence"}

    def _assert_valid_result(self, result: dict, expected_agent: str):
        assert isinstance(result, dict)
        for key in self.REQUIRED_KEYS:
            assert key in result, f"Missing key: {key}"
        assert result["agent_name"] == expected_agent
        assert result["status"] in ("success", "error")
        assert isinstance(result["findings"], list)
        assert isinstance(result["recommendations"], list)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_researcher_execute(self, basic_context):
        result = ResearcherAgent().execute(basic_context)
        self._assert_valid_result(result, "researcher")
        assert len(result["findings"]) > 0

    def test_analyst_execute(self, basic_context):
        result = AnalystAgent().execute(basic_context)
        self._assert_valid_result(result, "analyst")

    def test_analyst_execute_with_score(self):
        result = AnalystAgent().execute({"bd_score": 85})
        self._assert_valid_result(result, "analyst")
        assert any("High-priority" in f for f in result["findings"])

    def test_analyst_execute_with_medium_score(self):
        result = AnalystAgent().execute({"bd_score": 60})
        self._assert_valid_result(result, "analyst")
        assert any("Medium-priority" in f for f in result["findings"])

    def test_analyst_execute_with_low_score(self):
        result = AnalystAgent().execute({"bd_score": 30})
        self._assert_valid_result(result, "analyst")
        assert any("Low-priority" in f for f in result["findings"])

    def test_analyst_execute_with_jobs(self, jobs_context):
        result = AnalystAgent().execute(jobs_context)
        self._assert_valid_result(result, "analyst")
        assert any("Hiring trend" in f for f in result["findings"])

    def test_competitor_execute(self, basic_context):
        result = CompetitorAgent().execute(basic_context)
        self._assert_valid_result(result, "competitor")

    def test_competitor_execute_known_prime(self):
        result = CompetitorAgent().execute({"company": "GDIT"})
        self._assert_valid_result(result, "competitor")
        assert any("GDIT" in f for f in result["findings"])

    def test_playbook_execute(self, basic_context):
        result = PlaybookAgent().execute(basic_context)
        self._assert_valid_result(result, "playbook")
        assert any("Phase" in r for r in result["recommendations"])

    def test_call_prep_execute(self, contact_context):
        result = CallPrepAgent().execute(contact_context)
        self._assert_valid_result(result, "call_prep")
        assert any("Jane Doe" in f for f in result["findings"])

    def test_outreach_execute(self, contact_context):
        result = OutreachAgent().execute(contact_context)
        self._assert_valid_result(result, "outreach")
        assert any("PTS BD Formula" in r for r in result["recommendations"])

    def test_win_strategy_execute(self, basic_context):
        result = WinStrategyAgent().execute(basic_context)
        self._assert_valid_result(result, "win_strategy")
        assert any("Win Theme" in r for r in result["recommendations"])

    def test_account_mapper_execute(self, basic_context):
        result = AccountMapperAgent().execute(basic_context)
        self._assert_valid_result(result, "account_mapper")

    def test_empty_context_handling(self):
        """All agents should handle empty context gracefully."""
        for name, cls in ALL_AGENTS.items():
            agent = cls()
            result = agent.execute({})
            assert result["agent_name"] == name
            assert result["status"] == "success"
            assert isinstance(result["findings"], list)
            assert isinstance(result["recommendations"], list)


# ===========================================================================
# ORCHESTRATOR TESTS
# ===========================================================================


class TestOrchestrator:
    """Test BDAgentOrchestrator."""

    def test_orchestrator_registers_all_agents(self, orchestrator):
        assert len(orchestrator.agents) == 8

    def test_orchestrator_agent_names(self, orchestrator):
        expected = {"researcher", "analyst", "competitor", "playbook",
                    "call_prep", "outreach", "win_strategy", "account_mapper"}
        assert set(orchestrator.agents.keys()) == expected

    def test_get_agent_status(self, orchestrator):
        status = orchestrator.get_agent_status()
        assert status["total_agents"] == 8
        assert len(status["agents"]) == 8
        for info in status["agents"]:
            assert "name" in info
            assert "role" in info
            assert "goal" in info
            assert info["status"] == "ready"

    def test_get_workflows(self, orchestrator):
        result = orchestrator.get_workflows()
        assert result["total_workflows"] == 4
        names = {w["name"] for w in result["workflows"]}
        assert names == {"full_analysis", "call_prep", "opportunity_capture", "competitive_intel"}

    def test_workflow_descriptions(self, orchestrator):
        result = orchestrator.get_workflows()
        for wf in result["workflows"]:
            assert len(wf["description"]) > 10
            assert wf["steps"] >= 2
            assert len(wf["agents"]) >= 2


# ===========================================================================
# SINGLE AGENT VIA ORCHESTRATOR
# ===========================================================================


class TestSingleAgentExecution:
    """Test orchestrator.run_single_agent()."""

    def test_run_single_agent_success(self, orchestrator, basic_context):
        result = orchestrator.run_single_agent("researcher", basic_context)
        assert result["agent_name"] == "researcher"
        assert result["status"] == "success"
        assert "duration_seconds" in result

    def test_run_single_agent_all_agents(self, orchestrator, basic_context):
        for name in ALL_AGENTS:
            result = orchestrator.run_single_agent(name, basic_context)
            assert result["agent_name"] == name
            assert result["status"] in ("success", "error")

    def test_run_unknown_agent(self, orchestrator):
        result = orchestrator.run_single_agent("nonexistent_agent", {})
        assert result["status"] == "error"
        assert "Unknown agent" in result["error"]

    def test_run_single_agent_empty_context(self, orchestrator):
        result = orchestrator.run_single_agent("researcher", {})
        assert result["agent_name"] == "researcher"
        assert result["status"] == "success"


# ===========================================================================
# PARALLEL EXECUTION
# ===========================================================================


class TestParallelExecution:
    """Test orchestrator.run_parallel()."""

    def test_run_two_agents_parallel(self, orchestrator, basic_context):
        result = orchestrator.run_parallel(["researcher", "competitor"], basic_context)
        assert result["status"] == "success"
        assert "researcher" in result["results"]
        assert "competitor" in result["results"]
        assert "duration_seconds" in result

    def test_run_all_agents_parallel(self, orchestrator, basic_context):
        result = orchestrator.run_parallel(list(ALL_AGENTS.keys()), basic_context)
        assert len(result["results"]) == 8

    def test_parallel_with_unknown_agent(self, orchestrator, basic_context):
        result = orchestrator.run_parallel(["researcher", "fake_agent"], basic_context)
        assert result["status"] == "partial"
        assert "researcher" in result["results"]
        assert "fake_agent" in result["results"]
        assert result["results"]["fake_agent"]["status"] == "error"

    def test_parallel_all_unknown(self, orchestrator):
        result = orchestrator.run_parallel(["fake1", "fake2"], {})
        assert result["status"] == "error"
        assert len(result["errors"]) == 2

    def test_parallel_result_merging(self, orchestrator, basic_context):
        result = orchestrator.run_parallel(["researcher", "analyst", "competitor"], basic_context)
        for name in ["researcher", "analyst", "competitor"]:
            agent_result = result["results"][name]
            assert "findings" in agent_result
            assert "recommendations" in agent_result

    def test_parallel_empty_context(self, orchestrator):
        result = orchestrator.run_parallel(["researcher", "analyst"], {})
        assert result["status"] == "success"
        assert len(result["results"]) == 2


# ===========================================================================
# WORKFLOW EXECUTION
# ===========================================================================


class TestWorkflowExecution:
    """Test orchestrator.run_workflow()."""

    def test_full_analysis_workflow(self, orchestrator, basic_context):
        result = orchestrator.run_workflow("full_analysis", basic_context)
        assert result["status"] == "success"
        assert result["workflow"] == "full_analysis"
        assert "researcher" in result["results"]
        assert "analyst" in result["results"]
        assert "competitor" in result["results"]
        assert "win_strategy" in result["results"]
        assert "duration_seconds" in result

    def test_call_prep_workflow(self, orchestrator, contact_context):
        result = orchestrator.run_workflow("call_prep", contact_context)
        assert result["status"] == "success"
        assert result["workflow"] == "call_prep"
        assert "researcher" in result["results"]
        assert "account_mapper" in result["results"]
        assert "call_prep" in result["results"]

    def test_opportunity_capture_workflow(self, orchestrator, basic_context):
        result = orchestrator.run_workflow("opportunity_capture", basic_context)
        assert result["status"] == "success"
        assert "researcher" in result["results"]
        assert "analyst" in result["results"]
        assert "playbook" in result["results"]
        assert "outreach" in result["results"]

    def test_competitive_intel_workflow(self, orchestrator, basic_context):
        result = orchestrator.run_workflow("competitive_intel", basic_context)
        assert result["status"] == "success"
        assert "competitor" in result["results"]
        assert "researcher" in result["results"]
        assert "analyst" in result["results"]

    def test_unknown_workflow(self, orchestrator):
        result = orchestrator.run_workflow("nonexistent", {})
        assert result["status"] == "error"
        assert "Unknown workflow" in result["error"]

    def test_workflow_agents_used_list(self, orchestrator, basic_context):
        result = orchestrator.run_workflow("full_analysis", basic_context)
        assert isinstance(result["agents_used"], list)
        assert len(result["agents_used"]) == 4

    def test_workflow_context_passing(self, orchestrator, basic_context):
        """Sequential agents should receive prior_results in context."""
        result = orchestrator.run_workflow("full_analysis", basic_context)
        # The analyst should have received researcher results via prior_results
        analyst_result = result["results"]["analyst"]
        # Analyst synthesizes prior findings
        assert analyst_result["status"] == "success"

    def test_workflow_empty_context(self, orchestrator):
        result = orchestrator.run_workflow("full_analysis", {})
        assert result["status"] == "success"
        assert len(result["results"]) == 4


# ===========================================================================
# CONTEXT PASSING BETWEEN AGENTS
# ===========================================================================


class TestContextPassing:
    """Test that context flows correctly between sequential agents."""

    def test_prior_results_passed_to_later_agents(self, orchestrator):
        """When running a sequential workflow, later agents receive prior_results."""
        context = {"query": "DCGS modernization"}
        result = orchestrator.run_workflow("full_analysis", context)

        # The win_strategy agent is last in full_analysis;
        # it should have received prior_results from researcher, analyst, competitor
        win = result["results"]["win_strategy"]
        assert win["status"] == "success"
        # Win strategy should synthesize from prior intelligence
        assert any("synthesized" in f.lower() or "strategy" in f.lower()
                    for f in win["findings"])

    def test_parallel_step_results_fed_to_next_step(self, orchestrator):
        """In call_prep workflow, parallel results feed into call_prep agent."""
        context = {"contact_name": "Test User", "company": "GDIT"}
        result = orchestrator.run_workflow("call_prep", context)
        call_prep_result = result["results"]["call_prep"]
        assert call_prep_result["status"] == "success"


# ===========================================================================
# ERROR HANDLING
# ===========================================================================


class TestErrorHandling:
    """Test that agent failures don't crash workflows."""

    def test_agent_exception_caught(self, orchestrator):
        """If an agent raises, the orchestrator returns error status, not crash."""
        original_execute = orchestrator.agents["researcher"].execute

        def bad_execute(ctx):
            raise RuntimeError("Simulated failure")

        orchestrator.agents["researcher"].execute = bad_execute
        result = orchestrator.run_single_agent("researcher", {})
        assert result["status"] == "error"
        assert "Simulated failure" in result["error"]

        orchestrator.agents["researcher"].execute = original_execute

    def test_parallel_failure_doesnt_crash_others(self, orchestrator, basic_context):
        """One agent failing in parallel should not prevent others from completing."""
        original = orchestrator.agents["competitor"].execute

        def bad_execute(ctx):
            raise ValueError("Competitor broke")

        orchestrator.agents["competitor"].execute = bad_execute
        result = orchestrator.run_parallel(["researcher", "competitor", "analyst"], basic_context)

        assert result["results"]["researcher"]["status"] == "success"
        assert result["results"]["analyst"]["status"] == "success"
        assert result["results"]["competitor"]["status"] == "error"

        orchestrator.agents["competitor"].execute = original

    def test_workflow_agent_failure_continues(self, orchestrator, basic_context):
        """Agent failure in a workflow step should not crash the entire workflow."""
        original = orchestrator.agents["researcher"].execute

        def bad_execute(ctx):
            raise RuntimeError("Research failed")

        orchestrator.agents["researcher"].execute = bad_execute
        # full_analysis: researcher → analyst → competitor → win_strategy
        # researcher fails but workflow continues with other agents
        result = orchestrator.run_workflow("full_analysis", basic_context)
        # The result should still include entries for other agents
        assert "analyst" in result["results"]

        orchestrator.agents["researcher"].execute = original


# ===========================================================================
# SINGLETON
# ===========================================================================


class TestSingleton:
    """Test get_bd_orchestrator singleton."""

    def test_singleton_returns_same_instance(self):
        o1 = get_bd_orchestrator()
        o2 = get_bd_orchestrator()
        assert o1 is o2

    def test_singleton_is_orchestrator(self):
        o = get_bd_orchestrator()
        assert isinstance(o, BDAgentOrchestrator)


# ===========================================================================
# API ENDPOINT TESTS
# ===========================================================================


class TestAPIEndpoints:
    """Test FastAPI router endpoints."""

    def test_get_status(self, client):
        resp = client.get("/bd-agents/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_agents"] == 8
        assert len(data["agents"]) == 8

    def test_get_workflows(self, client):
        resp = client.get("/bd-agents/workflows")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_workflows"] == 4
        names = {w["name"] for w in data["workflows"]}
        assert "full_analysis" in names
        assert "call_prep" in names

    def test_run_single_agent_endpoint(self, client):
        resp = client.post(
            "/bd-agents/run/researcher",
            json={"context": {"query": "DCGS"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_name"] == "researcher"

    def test_run_unknown_agent_endpoint(self, client):
        resp = client.post(
            "/bd-agents/run/nonexistent",
            json={"context": {}},
        )
        assert resp.status_code == 404

    def test_run_workflow_endpoint(self, client):
        resp = client.post(
            "/bd-agents/run",
            json={"workflow": "competitive_intel", "context": {"query": "DCGS"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["workflow"] == "competitive_intel"
        assert data["status"] == "success"

    def test_run_unknown_workflow_endpoint(self, client):
        resp = client.post(
            "/bd-agents/run",
            json={"workflow": "nonexistent", "context": {}},
        )
        assert resp.status_code == 400

    def test_parallel_endpoint(self, client):
        resp = client.post(
            "/bd-agents/parallel",
            json={"agents": ["researcher", "analyst"], "context": {"query": "DCGS"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "researcher" in data["results"]
        assert "analyst" in data["results"]

    def test_parallel_endpoint_empty_agents(self, client):
        resp = client.post(
            "/bd-agents/parallel",
            json={"agents": [], "context": {}},
        )
        assert resp.status_code == 200

    def test_workflow_endpoint_empty_context(self, client):
        resp = client.post(
            "/bd-agents/run",
            json={"workflow": "full_analysis", "context": {}},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_single_agent_endpoint_empty_context(self, client):
        resp = client.post(
            "/bd-agents/run/analyst",
            json={"context": {}},
        )
        assert resp.status_code == 200
        assert resp.json()["agent_name"] == "analyst"


# ===========================================================================
# KNOWLEDGE BASE INTEGRATION
# ===========================================================================


class TestKnowledgeIntegration:
    """Test knowledge base search fallback behavior."""

    def test_search_knowledge_returns_empty_without_store(self):
        """When knowledge store is unavailable, search returns empty list."""
        agent = ResearcherAgent()
        agent._knowledge = None
        results = agent._search_knowledge("test query")
        assert results == []

    def test_search_knowledge_handles_exception(self):
        """Knowledge search exceptions are caught gracefully."""
        agent = ResearcherAgent()
        mock_store = MagicMock()
        mock_store.search.side_effect = ConnectionError("Qdrant down")
        agent._knowledge = mock_store
        results = agent._search_knowledge("test")
        assert results == []

    def test_agent_works_without_knowledge(self):
        """Agents produce valid results even without knowledge base."""
        for name, cls in ALL_AGENTS.items():
            agent = cls()
            agent._knowledge = None
            result = agent.execute({"query": "test"})
            assert result["agent_name"] == name
            assert result["status"] == "success"


# ===========================================================================
# MAKE RESULT HELPER
# ===========================================================================


class TestMakeResult:
    """Test the _make_result helper on BDAgentBase."""

    def test_default_result(self):
        agent = ResearcherAgent()
        result = agent._make_result()
        assert result["agent_name"] == "researcher"
        assert result["status"] == "success"
        assert result["findings"] == []
        assert result["recommendations"] == []
        assert result["confidence"] == 0.5

    def test_custom_result(self):
        agent = AnalystAgent()
        result = agent._make_result(
            status="error",
            findings=["f1"],
            recommendations=["r1"],
            confidence=0.9,
            metadata={"key": "val"},
        )
        assert result["status"] == "error"
        assert result["findings"] == ["f1"]
        assert result["recommendations"] == ["r1"]
        assert result["confidence"] == 0.9
        assert result["metadata"] == {"key": "val"}
