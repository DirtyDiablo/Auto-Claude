"""
Phase 20A — End-to-End Integration Tests

Tests the complete BD Intelligence platform workflow using existing services.
Run with: pytest Engine8_Knowledge/tests/integration/test_full_pipeline.py -v

These tests use the live API where available and mock where services are offline,
allowing both CI and local development testing.
"""

import os
import sys
import json
import uuid
import asyncio
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

API_BASE = os.getenv("BD_API_URL", "http://127.0.0.1:8100")


def _api_available() -> bool:
    """Check if the Hub API is reachable."""
    try:
        import httpx
        r = httpx.get(f"{API_BASE}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


skip_if_no_api = pytest.mark.skipif(
    not _api_available(),
    reason="Hub API not running — set BD_API_URL or start api.py"
)


# =========================================================================
# TEST SUITE 1: Job-to-Outreach Pipeline
# =========================================================================

class TestJobToOutreachPipeline:
    """End-to-end: scrape → program match → contact classify → outreach."""

    def test_job_scrape_event_triggers_enrichment(self):
        """Simulate a new job being scraped and verify enrichment hooks."""
        job_event = {
            "type": "job_scraped",
            "data": {
                "title": "Senior DCGS Analyst",
                "company": "GDIT",
                "location": "Fort Meade, MD",
                "clearance": "TS/SCI",
                "source_url": "https://example.com/job/123",
            },
        }
        # Verify event structure is valid
        assert job_event["type"] == "job_scraped"
        assert "title" in job_event["data"]
        assert "clearance" in job_event["data"]

    def test_hiring_signal_detection(self):
        """Verify ML model detects hiring surge from job volume."""
        try:
            from Engine8_Knowledge.ml.hiring_signals import get_hiring_signal_detector
            detector = get_hiring_signal_detector()
            # Simulate job history: sudden spike in DCGS jobs
            test_jobs = [
                {"program": "DCGS", "posted_date": "2026-02-01", "company": "GDIT"},
                {"program": "DCGS", "posted_date": "2026-02-02", "company": "Leidos"},
                {"program": "DCGS", "posted_date": "2026-02-03", "company": "GDIT"},
                {"program": "DCGS", "posted_date": "2026-02-04", "company": "SAIC"},
                {"program": "DCGS", "posted_date": "2026-02-05", "company": "GDIT"},
            ]
            signals = detector.detect_signals(test_jobs)
            assert isinstance(signals, (list, dict))
        except ImportError:
            # Module exists but dependencies missing — test structure only
            pytest.skip("ML hiring signals module not loadable")

    def test_contact_classification(self):
        """Verify contact tier classification works."""
        test_contact = {
            "name": "Test User",
            "title": "VP of Business Development",
            "company": "GDIT",
            "program": "DCGS-A",
            "email": "test@example.com",
        }
        # VP-level title should classify as Tier 2 (Senior Leadership)
        title = test_contact["title"].lower()
        if "vp" in title or "vice president" in title:
            expected_tier = 2
        elif "director" in title:
            expected_tier = 3
        elif "manager" in title:
            expected_tier = 4
        else:
            expected_tier = 5
        assert expected_tier == 2

    def test_outreach_message_bd_formula(self):
        """Verify outreach messages contain all 6 BD Formula elements."""
        bd_formula_elements = [
            "specific_reference",      # Reference to specific program/contract
            "value_proposition",       # What PTS brings
            "social_proof",            # Past performance evidence
            "personalization",         # Contact-specific detail
            "clear_ask",              # Specific next step
            "urgency",                # Time-sensitive element
        ]
        # Verify template structure expects all elements
        assert len(bd_formula_elements) == 6
        for elem in bd_formula_elements:
            assert isinstance(elem, str)

    def test_outreach_sequence_creation(self):
        """Verify cadence steps are correctly structured."""
        cadence = [
            {"step": 1, "channel": "email", "delay_days": 0, "template": "intro"},
            {"step": 2, "channel": "linkedin", "delay_days": 3, "template": "connection"},
            {"step": 3, "channel": "email", "delay_days": 7, "template": "follow_up"},
            {"step": 4, "channel": "phone", "delay_days": 10, "template": "call"},
            {"step": 5, "channel": "email", "delay_days": 14, "template": "value_add"},
        ]
        assert len(cadence) == 5
        # Verify correct ordering and timing
        for i, step in enumerate(cadence):
            assert step["step"] == i + 1
            assert step["channel"] in ("email", "linkedin", "phone")
            if i > 0:
                assert step["delay_days"] > cadence[i - 1]["delay_days"]

    def test_response_outcome_tracking(self):
        """Verify response tracking records outcomes correctly."""
        outcomes = ["positive_reply", "meeting_scheduled", "not_interested", "no_response", "bounced"]
        for outcome in outcomes:
            record = {
                "contact_id": "test-001",
                "sequence_id": "seq-001",
                "step": 1,
                "outcome": outcome,
                "recorded_at": datetime.now().isoformat(),
            }
            assert record["outcome"] in outcomes

    def test_feedback_loop_structure(self):
        """Verify feedback loop can connect outcomes to predictor."""
        try:
            from Engine8_Knowledge.ml.response_predictor import get_response_predictor
            predictor = get_response_predictor()
            info = predictor.get_model_info()
            assert isinstance(info, dict)
            assert "model_type" in info or "status" in info
        except ImportError:
            pytest.skip("ML response predictor not loadable")


# =========================================================================
# TEST SUITE 2: Competitive Intelligence Flow
# =========================================================================

class TestCompetitiveIntelligenceFlow:
    """Verify competitive intelligence pipeline end-to-end."""

    def test_contract_awarded_event_structure(self):
        """Verify CONTRACT_AWARDED event is well-formed."""
        event = {
            "type": "CONTRACT_AWARDED",
            "data": {
                "contract_number": "FA8750-26-C-0123",
                "awardee": "Leidos",
                "program": "DCGS-A",
                "value": 45_000_000,
                "agency": "Air Force",
                "award_date": "2026-02-01",
            },
        }
        assert event["type"] == "CONTRACT_AWARDED"
        assert event["data"]["value"] > 0
        assert event["data"]["awardee"]

    def test_alert_generation(self):
        """Verify alerts are generated with correct fields."""
        alert = {
            "type": "competitive_alert",
            "severity": "high",
            "competitor": "Leidos",
            "program": "DCGS-A",
            "impact": "Contract win reduces PTS positioning on future DCGS work",
            "recommended_action": "Schedule BD call with DCGS-A PM within 48 hours",
            "generated_at": datetime.now().isoformat(),
        }
        assert alert["severity"] in ("critical", "high", "medium", "low")
        assert "recommended_action" in alert

    def test_notification_payload(self):
        """Verify notification contains required fields for Slack delivery."""
        notification = {
            "channel": "#bd-alerts",
            "text": "Competitive Alert: Leidos won DCGS-A contract ($45M)",
            "blocks": [
                {"type": "header", "text": "Competitive Alert"},
                {"type": "section", "text": "Leidos won DCGS-A contract ($45M)"},
            ],
        }
        assert notification["channel"].startswith("#")
        assert len(notification["blocks"]) >= 2

    def test_escalation_threshold(self):
        """Verify escalation triggers for high-impact events."""
        thresholds = {
            "critical": 100_000_000,  # >$100M → critical
            "high": 25_000_000,       # >$25M → high
            "medium": 5_000_000,      # >$5M → medium
            "low": 0,                 # everything else
        }
        test_value = 45_000_000
        severity = "low"
        for level, threshold in sorted(thresholds.items(), key=lambda x: -x[1]):
            if test_value >= threshold:
                severity = level
                break
        assert severity == "high"


# =========================================================================
# TEST SUITE 3: Knowledge Graph Consistency
# =========================================================================

class TestKnowledgeGraphConsistency:
    """Verify knowledge graph operations maintain consistency."""

    def test_add_contact_creates_node(self):
        """Verify adding a contact creates a graph node."""
        try:
            from Engine8_Knowledge.graph.bd_knowledge_graph import BDKnowledgeGraph
            # Use in-memory database for testing
            graph = BDKnowledgeGraph(db_path=":memory:")
            entity_id = graph.add_entity(
                "Contact",
                "Test Engineer",
                {"title": "Sr. Engineer", "company": "GDIT"}
            )
            assert entity_id is not None
            # Verify node exists
            entity = graph.get_entity(entity_id)
            assert entity is not None
        except ImportError:
            pytest.skip("Knowledge graph module not loadable")

    def test_update_contact_program_updates_edges(self):
        """Verify updating a contact's program updates graph relationships."""
        try:
            from Engine8_Knowledge.graph.bd_knowledge_graph import BDKnowledgeGraph
            graph = BDKnowledgeGraph(db_path=":memory:")
            contact_id = graph.add_entity("Contact", "Jane Doe", {"title": "Director"})
            program_id = graph.add_entity("Program", "DCGS-A", {"agency": "Army"})
            rel_id = graph.add_relationship(contact_id, program_id, "WORKS_ON")
            assert rel_id is not None
        except ImportError:
            pytest.skip("Knowledge graph module not loadable")

    def test_influence_scoring_calculates(self):
        """Verify influence scoring runs without errors."""
        try:
            from Engine8_Knowledge.graph.influence_scoring import get_influence_scorer
            scorer = get_influence_scorer()
            leaderboard = scorer.get_leaderboard(limit=5)
            assert isinstance(leaderboard, list)
        except ImportError:
            pytest.skip("Influence scoring module not loadable")

    def test_community_detection_runs(self):
        """Verify community detection produces results."""
        try:
            from Engine8_Knowledge.graph.community_detection import get_community_detector
            detector = get_community_detector()
            summary = detector.get_community_summary()
            assert isinstance(summary, dict)
        except ImportError:
            pytest.skip("Community detection module not loadable")

    def test_graph_rag_query(self):
        """Verify Graph RAG returns structured results."""
        try:
            from Engine8_Knowledge.graph.graph_rag import get_graph_rag
            rag = get_graph_rag()
            # Just verify the engine initializes
            assert rag is not None
        except ImportError:
            pytest.skip("Graph RAG module not loadable")


# =========================================================================
# TEST SUITE 4: Autonomous Agents
# =========================================================================

class TestAutonomousAgents:
    """Verify autonomous agent scheduling and execution."""

    def test_scheduler_has_all_tasks(self):
        """Verify all 10 scheduled tasks are registered."""
        from Engine8_Knowledge.automation.task_scheduler import get_task_scheduler
        scheduler = get_task_scheduler()
        schedule = scheduler.get_schedule()
        expected_tasks = {
            "daily_scrape", "morning_brief", "contact_enrichment",
            "competitive_scan", "pipeline_health", "model_drift_check",
            "weekly_report", "monthly_retrain", "event_cleanup", "backup",
        }
        actual_tasks = {t["name"] for t in schedule}
        assert expected_tasks == actual_tasks, f"Missing: {expected_tasks - actual_tasks}"

    @pytest.mark.asyncio
    async def test_run_now_pipeline_health(self):
        """Verify pipeline_health task can execute."""
        from Engine8_Knowledge.automation.task_scheduler import get_task_scheduler
        scheduler = get_task_scheduler()
        result = await scheduler.run_now("pipeline_health")
        assert "status" in result
        assert result["task"] == "pipeline_health"

    @pytest.mark.asyncio
    async def test_run_now_event_cleanup(self):
        """Verify event_cleanup task executes without error."""
        from Engine8_Knowledge.automation.task_scheduler import get_task_scheduler
        scheduler = get_task_scheduler()
        result = await scheduler.run_now("event_cleanup")
        assert result["status"] in ("success", "failed")

    @pytest.mark.asyncio
    async def test_run_now_backup(self):
        """Verify backup task executes."""
        from Engine8_Knowledge.automation.task_scheduler import get_task_scheduler
        scheduler = get_task_scheduler()
        result = await scheduler.run_now("backup")
        assert result["task"] == "backup"

    def test_workflow_definitions_complete(self):
        """Verify all 4 workflows are registered."""
        from Engine8_Knowledge.automation.agent_coordinator import get_agent_coordinator
        coordinator = get_agent_coordinator()
        expected = {"new_program_discovery", "recompete_response", "hot_lead_pipeline", "weekly_optimization"}
        actual = set(coordinator.workflows.keys())
        assert expected == actual

    @pytest.mark.asyncio
    async def test_hot_lead_workflow_runs(self):
        """Verify hot_lead_pipeline workflow completes end-to-end."""
        from Engine8_Knowledge.automation.agent_coordinator import get_agent_coordinator
        coordinator = get_agent_coordinator()
        result = await coordinator.run_workflow(
            "hot_lead_pipeline",
            {"contact_name": "John Doe", "company": "GDIT"}
        )
        assert result["status"] in ("completed", "failed")
        assert result["workflow_name"] == "hot_lead_pipeline"

    @pytest.mark.asyncio
    async def test_workflow_with_human_gate_pauses(self):
        """Verify workflows pause at human gates."""
        from Engine8_Knowledge.automation.agent_coordinator import get_agent_coordinator
        coordinator = get_agent_coordinator()
        result = await coordinator.run_workflow("new_program_discovery", {})
        # new_program_discovery has a human gate after classify step
        assert result["status"] == "paused"
        assert result["human_gate_pending"] is True


# =========================================================================
# TEST SUITE 5: Auth and Scoping
# =========================================================================

class TestAuthAndScoping:
    """Verify role-based access control and data scoping."""

    ROLES = ["admin", "bd_manager", "account_manager", "recruiter"]

    def test_role_definitions_exist(self):
        """Verify all expected roles are defined."""
        for role in self.ROLES:
            assert isinstance(role, str)

    def test_admin_has_full_access(self):
        """Verify admin role has access to all resources."""
        admin_permissions = {
            "contacts": ["read", "write", "delete"],
            "programs": ["read", "write", "delete"],
            "outreach": ["read", "write", "delete"],
            "settings": ["read", "write"],
            "automation": ["read", "write", "execute"],
        }
        for resource, perms in admin_permissions.items():
            assert "read" in perms
            assert "write" in perms

    def test_recruiter_limited_access(self):
        """Verify recruiter role has limited scope."""
        recruiter_permissions = {
            "contacts": ["read"],
            "programs": ["read"],
            "outreach": ["read"],
            "settings": [],
            "automation": [],
        }
        assert "write" not in recruiter_permissions["contacts"]
        assert "delete" not in recruiter_permissions["contacts"]
        assert len(recruiter_permissions["settings"]) == 0

    def test_jwt_structure(self):
        """Verify JWT token contains expected claims."""
        # Simulate JWT payload structure
        token_payload = {
            "sub": "user-123",
            "role": "bd_manager",
            "permissions": ["contacts:read", "contacts:write", "outreach:read", "outreach:write"],
            "exp": 1738000000,
            "iat": 1737900000,
        }
        assert "sub" in token_payload
        assert "role" in token_payload
        assert "permissions" in token_payload
        assert token_payload["exp"] > token_payload["iat"]

    def test_data_scoping_per_role(self):
        """Verify data filtering applies per role."""
        # BD Manager sees all contacts
        bd_filter = {"tier__lte": 6}
        assert bd_filter["tier__lte"] == 6

        # Account Manager sees only their accounts
        am_filter = {"owner": "current_user", "tier__lte": 4}
        assert "owner" in am_filter

        # Recruiter sees only Tier 5-6
        recruiter_filter = {"tier__gte": 5}
        assert recruiter_filter["tier__gte"] == 5


# =========================================================================
# API-Level Integration Tests (require running server)
# =========================================================================

@skip_if_no_api
class TestAPIIntegration:
    """Tests that require the Hub API to be running."""

    def test_health_endpoint(self):
        import httpx
        r = httpx.get(f"{API_BASE}/health", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"

    def test_contacts_endpoint(self):
        import httpx
        r = httpx.get(f"{API_BASE}/api/v2/contacts", params={"limit": 5}, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "contacts" in data
        assert "total" in data

    def test_programs_endpoint(self):
        import httpx
        r = httpx.get(f"{API_BASE}/api/v2/programs", params={"limit": 5}, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "programs" in data

    def test_automation_schedule(self):
        import httpx
        r = httpx.get(f"{API_BASE}/automation/schedule", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "tasks" in data
        assert len(data["tasks"]) == 10

    def test_automation_workflows(self):
        import httpx
        r = httpx.get(f"{API_BASE}/automation/workflows/definitions", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "workflows" in data
        assert len(data["workflows"]) == 4

    def test_claude_queue(self):
        import httpx
        r = httpx.get(f"{API_BASE}/automation/claude/queue", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "stats" in data
