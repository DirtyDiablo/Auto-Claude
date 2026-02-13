"""
LANGGRAPH WORKFLOW TEST SUITE
==============================
Comprehensive tests for all LangGraph workflow components.

Run with: pytest langgraph/test_langgraph.py -v
"""

import os
import tempfile
import pytest
from pathlib import Path

# Import all components to test
from .states import (
    WorkflowStatus,
    HumanReviewType,
    BaseWorkflowState,
    BDProposalState,
    ContactOutreachState,
    RecompeteState,
    WeeklyPipelineState,
)
from .checkpointer import (
    get_checkpointer,
    get_memory_checkpointer,
    CheckpointManager,
)
from .human_in_loop import (
    HumanReviewRequest,
    create_review_request,
    submit_review,
    get_pending_reviews,
    get_review_for_workflow,
    get_feedback_for_resume,
)
from .edges import (
    should_continue_after_review,
    has_contacts_for_review,
    should_generate_alert,
)
from .nodes import (
    research_opportunity,
    gather_contacts,
    analyze_competition,
)


# ============================================================================
# STATE CLASS TESTS
# ============================================================================

class TestWorkflowStates:
    """Tests for state dataclass definitions."""

    def test_base_workflow_state_creation(self):
        """Test BaseWorkflowState can be created with defaults."""
        state = BaseWorkflowState()

        assert state.workflow_id == ""
        assert state.status == WorkflowStatus.PENDING.value
        assert state.completed_nodes == []
        assert state.awaiting_human_review is False
        assert state.created_at is not None

    def test_base_workflow_state_to_dict(self):
        """Test BaseWorkflowState serializes correctly."""
        state = BaseWorkflowState(
            workflow_id="test_123",
            status=WorkflowStatus.IN_PROGRESS.value,
            completed_nodes=["node1", "node2"]
        )

        data = state.to_dict()

        assert data['workflow_id'] == "test_123"
        assert data['status'] == "in_progress"
        assert data['completed_nodes'] == ["node1", "node2"]

    def test_base_workflow_state_mark_node_complete(self):
        """Test marking nodes as complete."""
        state = BaseWorkflowState(workflow_id="test")
        state.mark_node_complete("node1")
        state.mark_node_complete("node2")
        state.mark_node_complete("node1")  # Duplicate should not add

        assert state.completed_nodes == ["node1", "node2"]

    def test_base_workflow_state_request_human_review(self):
        """Test requesting human review."""
        state = BaseWorkflowState(workflow_id="test")
        state.request_human_review(HumanReviewType.STRATEGY_APPROVAL, "req_123")

        assert state.awaiting_human_review is True
        assert state.human_review_type == HumanReviewType.STRATEGY_APPROVAL.value
        assert state.human_review_request_id == "req_123"
        assert state.status == WorkflowStatus.AWAITING_HUMAN_REVIEW.value

    def test_bd_proposal_state_creation(self):
        """Test BDProposalState with all fields."""
        state = BDProposalState(
            workflow_id="bd_test",
            target_opportunity_id="OPP_001",
            opportunity_title="Test Opportunity",
            agency="DoD",
            naics_codes=["541512", "541519"],
            target_value=5_000_000
        )

        assert state.workflow_type == "bd_proposal"
        assert state.target_opportunity_id == "OPP_001"
        assert state.naics_codes == ["541512", "541519"]
        assert state.similar_contracts == []
        assert state.prioritized_contacts == []

    def test_bd_proposal_state_to_dict(self):
        """Test BDProposalState serialization."""
        state = BDProposalState(
            workflow_id="bd_test",
            target_opportunity_id="OPP_001",
            similar_contracts=[{"id": "1"}, {"id": "2"}]
        )

        data = state.to_dict()

        assert data['workflow_id'] == "bd_test"
        assert data['workflow_type'] == "bd_proposal"
        assert len(data['similar_contracts']) == 2

    def test_contact_outreach_state_creation(self):
        """Test ContactOutreachState."""
        state = ContactOutreachState(
            workflow_id="contact_test",
            target_company="Acme Corp",
            target_program="Program X",
            outreach_goal="meeting"
        )

        assert state.workflow_type == "contact_outreach"
        assert state.target_company == "Acme Corp"
        assert state.max_contacts == 20

    def test_recompete_state_creation(self):
        """Test RecompeteState."""
        state = RecompeteState(
            workflow_id="recompete_test",
            monitored_contracts=["CONT_001", "CONT_002"],
            alert_threshold_days=180
        )

        assert state.workflow_type == "recompete_intelligence"
        assert len(state.monitored_contracts) == 2
        assert state.alert_threshold_days == 180

    def test_weekly_pipeline_state_creation(self):
        """Test WeeklyPipelineState."""
        state = WeeklyPipelineState(
            workflow_id="pipeline_test",
            target_naics=["541512"],
            min_value=1_000_000,
            date_range_days=7
        )

        assert state.workflow_type == "weekly_pipeline"
        assert state.target_naics == ["541512"]
        assert state.date_range_days == 7

    def test_workflow_status_enum(self):
        """Test WorkflowStatus enum values."""
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.IN_PROGRESS.value == "in_progress"
        assert WorkflowStatus.AWAITING_HUMAN_REVIEW.value == "awaiting_human_review"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"

    def test_human_review_type_enum(self):
        """Test HumanReviewType enum values."""
        assert HumanReviewType.STRATEGY_APPROVAL.value == "strategy_approval"
        assert HumanReviewType.CONTACT_APPROVAL.value == "contact_approval"


# ============================================================================
# CHECKPOINTER TESTS
# ============================================================================

class TestCheckpointer:
    """Tests for checkpointer and checkpoint manager."""

    def test_memory_checkpointer_creation(self):
        """Test in-memory checkpointer creation."""
        checkpointer = get_memory_checkpointer()
        assert checkpointer is not None

    def test_sqlite_checkpointer_creation(self):
        """Test SQLite checkpointer creation."""
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(tmpdir, "test_checkpoints.db")
            checkpointer = get_checkpointer(db_path)
            assert checkpointer is not None
            assert os.path.exists(db_path)
        finally:
            # On Windows, SQLite may hold file locks - ignore cleanup errors
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_checkpoint_manager_creation(self):
        """Test CheckpointManager creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_checkpoints.db")
            manager = CheckpointManager(db_path)
            assert manager is not None

    def test_checkpoint_manager_register_workflow(self):
        """Test registering a workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_checkpoints.db")
            manager = CheckpointManager(db_path)

            manager.register_workflow(
                thread_id="thread_123",
                workflow_type="bd_proposal",
                workflow_id="bd_001"
            )

            workflow = manager.get_workflow("thread_123")
            assert workflow is not None
            assert workflow['workflow_type'] == "bd_proposal"
            assert workflow['status'] == "pending"

    def test_checkpoint_manager_update_status(self):
        """Test updating workflow status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_checkpoints.db")
            manager = CheckpointManager(db_path)

            manager.register_workflow("thread_123", "bd_proposal", "bd_001")
            manager.update_workflow_status("thread_123", "completed")

            workflow = manager.get_workflow("thread_123")
            assert workflow['status'] == "completed"
            assert workflow['completed_at'] is not None

    def test_checkpoint_manager_list_workflows(self):
        """Test listing workflows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_checkpoints.db")
            manager = CheckpointManager(db_path)

            manager.register_workflow("thread_1", "bd_proposal", "bd_001")
            manager.register_workflow("thread_2", "contact_outreach", "contact_001")
            manager.register_workflow("thread_3", "bd_proposal", "bd_002")

            all_workflows = manager.list_workflows()
            assert len(all_workflows) == 3

            bd_workflows = manager.list_workflows(workflow_type="bd_proposal")
            assert len(bd_workflows) == 2

    def test_checkpoint_manager_get_stats(self):
        """Test getting workflow statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_checkpoints.db")
            manager = CheckpointManager(db_path)

            manager.register_workflow("thread_1", "bd_proposal", "bd_001")
            manager.update_workflow_status("thread_1", "completed")
            manager.register_workflow("thread_2", "bd_proposal", "bd_002")

            stats = manager.get_stats()
            assert stats['total'] == 2
            assert 'by_status' in stats
            assert 'by_type' in stats


# ============================================================================
# HUMAN-IN-THE-LOOP TESTS
# ============================================================================

class TestHumanInLoop:
    """Tests for human review system."""

    def test_review_request_creation(self):
        """Test creating a review request."""
        request = HumanReviewRequest(
            workflow_id="test_workflow",
            review_type="strategy_approval",
            review_data={"key": "value"},
            instructions="Please review"
        )

        assert request.request_id is not None
        assert request.workflow_id == "test_workflow"
        assert request.status == "pending"

    def test_review_request_to_dict(self):
        """Test review request serialization."""
        request = HumanReviewRequest(
            workflow_id="test_workflow",
            review_type="strategy_approval",
            review_data={"win_themes": ["theme1", "theme2"]}
        )

        data = request.to_dict()

        assert data['workflow_id'] == "test_workflow"
        assert data['review_data']['win_themes'] == ["theme1", "theme2"]

    def test_review_request_from_dict(self):
        """Test review request deserialization."""
        data = {
            'request_id': 'req_123',
            'workflow_id': 'wf_456',
            'review_type': 'strategy_approval',
            'review_data': {},
            'instructions': 'Review this',
            'created_at': '2024-01-01T00:00:00',
            'status': 'pending'
        }

        request = HumanReviewRequest.from_dict(data)

        assert request.request_id == 'req_123'
        assert request.workflow_id == 'wf_456'

    def test_create_review_request_file(self):
        """Test creating review request saves to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            review_dir = Path(tmpdir)

            request = create_review_request(
                workflow_id="test_wf",
                review_type=HumanReviewType.STRATEGY_APPROVAL,
                review_data={"test": "data"},
                instructions="Test instructions",
                review_dir=review_dir
            )

            # Check JSON file exists
            json_file = review_dir / f"review_{request.request_id}.json"
            assert json_file.exists()

            # Check markdown file exists
            md_file = review_dir / f"review_{request.request_id}_PENDING.md"
            assert md_file.exists()

    def test_submit_review(self):
        """Test submitting a review."""
        with tempfile.TemporaryDirectory() as tmpdir:
            review_dir = Path(tmpdir)

            # Create request
            request = create_review_request(
                workflow_id="test_wf",
                review_type=HumanReviewType.STRATEGY_APPROVAL,
                review_data={},
                review_dir=review_dir
            )

            # Submit review
            updated = submit_review(
                request_id=request.request_id,
                decision="approve",
                notes="Looks good",
                reviewer="Test User",
                review_dir=review_dir
            )

            assert updated.status == "approved"
            assert updated.decision == "approve"
            assert updated.feedback_notes == "Looks good"

            # Check pending md removed
            pending_md = review_dir / f"review_{request.request_id}_PENDING.md"
            assert not pending_md.exists()

            # Check completed md exists
            completed_md = review_dir / f"review_{request.request_id}_COMPLETED.md"
            assert completed_md.exists()

    def test_submit_review_invalid_decision(self):
        """Test submitting review with invalid decision raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            review_dir = Path(tmpdir)

            request = create_review_request(
                workflow_id="test_wf",
                review_type=HumanReviewType.STRATEGY_APPROVAL,
                review_data={},
                review_dir=review_dir
            )

            with pytest.raises(ValueError):
                submit_review(
                    request_id=request.request_id,
                    decision="invalid_decision",
                    review_dir=review_dir
                )

    def test_get_pending_reviews(self):
        """Test getting pending reviews."""
        with tempfile.TemporaryDirectory() as tmpdir:
            review_dir = Path(tmpdir)

            # Create multiple requests
            create_review_request("wf_1", HumanReviewType.STRATEGY_APPROVAL, {}, review_dir=review_dir)
            create_review_request("wf_2", HumanReviewType.CONTACT_APPROVAL, {}, review_dir=review_dir)
            req3 = create_review_request("wf_3", HumanReviewType.STRATEGY_APPROVAL, {}, review_dir=review_dir)

            # Submit one
            submit_review(req3.request_id, "approve", review_dir=review_dir)

            # Get pending
            pending = get_pending_reviews(review_dir=review_dir)
            assert len(pending) == 2

    def test_get_review_for_workflow(self):
        """Test getting review by workflow ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            review_dir = Path(tmpdir)

            create_review_request("wf_target", HumanReviewType.STRATEGY_APPROVAL, {}, review_dir=review_dir)
            create_review_request("wf_other", HumanReviewType.CONTACT_APPROVAL, {}, review_dir=review_dir)

            review = get_review_for_workflow("wf_target", review_dir=review_dir)

            assert review is not None
            assert review.workflow_id == "wf_target"

    def test_get_feedback_for_resume(self):
        """Test getting feedback in resume format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            review_dir = Path(tmpdir)

            request = create_review_request("wf_1", HumanReviewType.STRATEGY_APPROVAL, {}, review_dir=review_dir)

            # Pending review should return None
            feedback = get_feedback_for_resume(request.request_id, review_dir=review_dir)
            assert feedback is None

            # Submit review
            submit_review(request.request_id, "approve", notes="Good", review_dir=review_dir)

            # Now should return feedback
            feedback = get_feedback_for_resume(request.request_id, review_dir=review_dir)
            assert feedback is not None
            assert feedback['decision'] == "approve"
            assert feedback['notes'] == "Good"


# ============================================================================
# EDGE FUNCTION TESTS
# ============================================================================

class TestEdgeFunctions:
    """Tests for conditional edge functions."""

    def test_should_continue_after_review_approve(self):
        """Test routing to finalize on approval."""
        state = {
            'human_feedback': {'decision': 'approve'}
        }
        result = should_continue_after_review(state)
        assert result == "finalize"

    def test_should_continue_after_review_revise(self):
        """Test routing to revise on revision request."""
        state = {
            'human_feedback': {'decision': 'revise'}
        }
        result = should_continue_after_review(state)
        assert result == "revise"

    def test_should_continue_after_review_abort(self):
        """Test routing to abort on abort decision."""
        state = {
            'human_feedback': {'decision': 'abort'}
        }
        result = should_continue_after_review(state)
        assert result == "abort"

    def test_should_continue_after_review_no_feedback(self):
        """Test default to abort with no feedback."""
        state = {}
        result = should_continue_after_review(state)
        assert result == "abort"

    def test_has_contacts_for_review_with_contacts(self):
        """Test routing to approval with contacts."""
        state = {
            'scored_contacts': [{'name': 'John'}]
        }
        result = has_contacts_for_review(state)
        assert result == "request_approval"

    def test_has_contacts_for_review_no_contacts(self):
        """Test routing to generate with no contacts."""
        state = {
            'scored_contacts': []
        }
        result = has_contacts_for_review(state)
        assert result == "generate"

    def test_has_contacts_for_review_auto_approve(self):
        """Test routing to generate with auto approve."""
        state = {
            'scored_contacts': [{'name': 'John'}],
            'auto_approve_contacts': True
        }
        result = has_contacts_for_review(state)
        assert result == "generate"

    def test_should_generate_alert_with_signals(self):
        """Test routing to alert with signals."""
        state = {
            'recompete_signals': [{'contract_id': 'CONT_001'}]
        }
        result = should_generate_alert(state)
        assert result == "generate_alert"

    def test_should_generate_alert_no_signals(self):
        """Test routing to complete with no signals."""
        state = {
            'recompete_signals': []
        }
        result = should_generate_alert(state)
        assert result == "complete"


# ============================================================================
# NODE FUNCTION TESTS
# ============================================================================

class TestNodeFunctions:
    """Tests for workflow node functions."""

    def test_research_opportunity_node(self):
        """Test research opportunity node execution."""
        state = {
            'opportunity_title': 'Test Opportunity',
            'naics_codes': ['541512'],
            'agency': 'DoD',
            'target_value': 5_000_000,
            'completed_nodes': [],
            'stats': {}
        }

        result = research_opportunity(state)

        assert 'similar_contracts' in result
        assert 'market_intelligence' in result
        assert 'opportunity_analysis' in result
        assert 'research_opportunity' in result['completed_nodes']

    def test_gather_contacts_node(self):
        """Test gather contacts node execution."""
        state = {
            'agency': 'DoD',
            'opportunity_title': 'Test',
            'similar_contracts': [{'incumbent': 'Acme Corp'}],
            'incumbent_info': {'company_name': 'Acme Corp'},
            'completed_nodes': [],
            'stats': {}
        }

        result = gather_contacts(state)

        assert 'contacts_gathered' in result
        assert 'prioritized_contacts' in result
        assert 'gather_contacts' in result['completed_nodes']

    def test_analyze_competition_node(self):
        """Test analyze competition node execution."""
        state = {
            'naics_codes': ['541512'],
            'agency': 'DoD',
            'target_opportunity_id': 'OPP_001',
            'target_value': 5_000_000,
            'similar_contracts': [],
            'incumbent_info': {},
            'completed_nodes': [],
            'stats': {}
        }

        result = analyze_competition(state)

        assert 'competitor_analysis' in result
        assert 'competitive_landscape' in result
        assert 'win_probability' in result
        assert 'analyze_competition' in result['completed_nodes']


# ============================================================================
# WORKFLOW GRAPH TESTS
# ============================================================================

class TestWorkflowGraphs:
    """Tests for workflow graph compilation and execution."""

    def test_bd_proposal_graph_compilation(self):
        """Test BD proposal graph compiles without errors."""
        from .bd_workflows import create_bd_proposal_graph

        checkpointer = get_memory_checkpointer()
        graph = create_bd_proposal_graph(checkpointer)

        assert graph is not None

    def test_contact_outreach_graph_compilation(self):
        """Test contact outreach graph compiles without errors."""
        from .contact_workflows import create_contact_outreach_graph

        checkpointer = get_memory_checkpointer()
        graph = create_contact_outreach_graph(checkpointer)

        assert graph is not None

    def test_recompete_graph_compilation(self):
        """Test recompete graph compiles without errors."""
        from .recompete_workflows import create_recompete_graph

        checkpointer = get_memory_checkpointer()
        graph = create_recompete_graph(checkpointer)

        assert graph is not None

    def test_weekly_pipeline_graph_compilation(self):
        """Test weekly pipeline graph compiles without errors."""
        from .pipeline_workflows import create_weekly_pipeline_graph

        checkpointer = get_memory_checkpointer()
        graph = create_weekly_pipeline_graph(checkpointer)

        assert graph is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for end-to-end workflows."""

    def test_bd_workflow_to_human_review(self):
        """Test BD workflow runs to human review interrupt."""
        from .bd_workflows import run_bd_proposal_workflow

        result = run_bd_proposal_workflow(
            opportunity_id="TEST_OPP_001",
            opportunity_title="Test Opportunity",
            agency="Department of Defense",
            naics_codes=["541512"],
            target_value=5_000_000,
            checkpointer=get_memory_checkpointer()
        )

        assert result['status'] == 'awaiting_human_review'
        assert 'review_request_id' in result
        assert 'thread_id' in result

    def test_contact_workflow_with_auto_approve(self):
        """Test contact workflow with auto approve completes."""
        from .contact_workflows import run_contact_outreach_workflow

        result = run_contact_outreach_workflow(
            target_company="Test Corp",
            outreach_goal="meeting",
            auto_approve=True,
            checkpointer=get_memory_checkpointer()
        )

        assert result['status'] == 'completed'

    def test_recompete_workflow_completes(self):
        """Test recompete workflow completes."""
        from .recompete_workflows import run_recompete_workflow

        result = run_recompete_workflow(
            contract_ids=["CONT_001", "CONT_002"],
            alert_threshold_days=365,
            checkpointer=get_memory_checkpointer()
        )

        assert result['status'] == 'completed'
        assert 'contracts_monitored' in result

    def test_weekly_pipeline_workflow_completes(self):
        """Test weekly pipeline workflow completes."""
        from .pipeline_workflows import run_weekly_pipeline_workflow

        result = run_weekly_pipeline_workflow(
            target_naics=["541512"],
            date_range_days=7,
            checkpointer=get_memory_checkpointer()
        )

        assert result['status'] == 'completed'


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
