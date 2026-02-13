"""
CONTACT OUTREACH WORKFLOW
=========================
Workflow graph for contact discovery, scoring, and outreach material generation.

Pipeline: Discover → Score → Approve → Generate Materials
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from langgraph.graph import StateGraph, END

from .states import WorkflowStatus
from .checkpointer import get_checkpointer, CheckpointManager
from .nodes import (
    discover_contacts,
    score_and_prioritize_contacts,
    request_contact_approval,
    generate_outreach_materials,
)
from .edges import has_contacts_for_review, should_continue_contact_outreach
from .human_in_loop import get_feedback_for_resume

# Try to import logger
try:
    from src.utils import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def create_contact_outreach_graph(checkpointer=None):
    """
    Create the Contact Outreach workflow graph.

    Args:
        checkpointer: Optional LangGraph checkpointer for persistence.

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create graph with state schema
    workflow = StateGraph(dict)

    # Add nodes
    workflow.add_node("discover", discover_contacts)
    workflow.add_node("score", score_and_prioritize_contacts)
    workflow.add_node("request_approval", request_contact_approval)
    workflow.add_node("process_approval", lambda state: {
        **state,
        'approved_contacts': state.get('human_feedback', {}).get('approved_items', state.get('scored_contacts', [])[:10]),
        'rejected_contacts': state.get('human_feedback', {}).get('rejected_items', []),
        'approval_notes': state.get('human_feedback', {}).get('notes'),
        'awaiting_human_review': False,
        'status': WorkflowStatus.IN_PROGRESS.value,
        'updated_at': datetime.now().isoformat()
    })
    workflow.add_node("generate", generate_outreach_materials)

    # Define the flow
    workflow.add_edge("discover", "score")

    # Conditional: check if contacts need approval
    workflow.add_conditional_edges(
        "score",
        has_contacts_for_review,
        {
            "request_approval": "request_approval",
            "generate": "generate"
        }
    )

    # Conditional after approval
    workflow.add_conditional_edges(
        "process_approval",
        should_continue_contact_outreach,
        {
            "generate": "generate",
            "abort": END
        }
    )

    # End after generation
    workflow.add_edge("generate", END)

    # Set entry point
    workflow.set_entry_point("discover")

    # Compile with checkpointer and interrupt
    if checkpointer is None:
        checkpointer = get_checkpointer()

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["process_approval"]
    )


def run_contact_outreach_workflow(
    target_company: str,
    target_program: Optional[str] = None,
    outreach_goal: str = "meeting",
    max_contacts: int = 20,
    auto_approve: bool = False,
    checkpointer=None,
    thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the Contact Outreach workflow.

    Args:
        target_company: Company to find contacts for
        target_program: Optional program/contract to focus on
        outreach_goal: Goal of outreach (meeting, partnership, intelligence)
        max_contacts: Maximum contacts to find
        auto_approve: If True, skip human approval
        checkpointer: Optional checkpointer
        thread_id: Optional thread ID

    Returns:
        Dictionary with workflow result and status
    """
    logger.info(f"Starting Contact Outreach workflow for: {target_company}")

    # Generate workflow ID
    workflow_id = f"contact_{uuid.uuid4().hex[:8]}"
    thread_id = thread_id or f"thread_{workflow_id}"

    # Initialize state
    initial_state = {
        'workflow_id': workflow_id,
        'workflow_type': 'contact_outreach',
        'thread_id': thread_id,
        'status': WorkflowStatus.IN_PROGRESS.value,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'completed_nodes': [],

        # Input parameters
        'target_company': target_company,
        'target_program': target_program,
        'outreach_goal': outreach_goal,
        'max_contacts': max_contacts,
        'auto_approve_contacts': auto_approve,

        # Initialize empty collections
        'discovered_contacts': [],
        'scored_contacts': [],
        'approved_contacts': [],
        'outreach_materials': [],
        'stats': {}
    }

    # Create graph
    graph = create_contact_outreach_graph(checkpointer)

    # Register workflow
    manager = CheckpointManager()
    manager.register_workflow(thread_id, 'contact_outreach', workflow_id)

    # Run workflow
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = graph.invoke(initial_state, config)

        if result.get('awaiting_human_review'):
            manager.update_workflow_status(thread_id, WorkflowStatus.AWAITING_HUMAN_REVIEW.value)
            return {
                'workflow_id': workflow_id,
                'thread_id': thread_id,
                'status': 'awaiting_human_review',
                'review_request_id': result.get('human_review_request_id'),
                'contacts_to_review': result.get('contact_rankings', []),
                'message': 'Workflow paused for contact approval.',
                'state': result
            }

        manager.update_workflow_status(thread_id, WorkflowStatus.COMPLETED.value)
        return {
            'workflow_id': workflow_id,
            'thread_id': thread_id,
            'status': 'completed',
            'contacts_found': len(result.get('discovered_contacts', [])),
            'materials_generated': len(result.get('outreach_materials', [])),
            'state': result
        }

    except Exception as e:
        manager.update_workflow_status(thread_id, WorkflowStatus.FAILED.value, str(e))
        logger.error(f"Workflow {workflow_id} failed: {e}")
        return {
            'workflow_id': workflow_id,
            'thread_id': thread_id,
            'status': 'failed',
            'error': str(e)
        }


def resume_contact_outreach_workflow(
    thread_id: str,
    human_feedback: Optional[Dict[str, Any]] = None,
    review_request_id: Optional[str] = None,
    checkpointer=None
) -> Dict[str, Any]:
    """
    Resume a Contact Outreach workflow after human approval.

    Args:
        thread_id: Thread ID of the paused workflow
        human_feedback: Human review feedback dictionary
        review_request_id: If provided, loads feedback from review file
        checkpointer: Optional checkpointer

    Returns:
        Dictionary with workflow result and status
    """
    logger.info(f"Resuming Contact Outreach workflow: {thread_id}")

    if review_request_id and not human_feedback:
        human_feedback = get_feedback_for_resume(review_request_id)
        if not human_feedback:
            return {
                'status': 'error',
                'error': f'Review {review_request_id} not found or not yet completed'
            }

    if not human_feedback:
        return {
            'status': 'error',
            'error': 'No human feedback provided.'
        }

    graph = create_contact_outreach_graph(checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    try:
        state_update = {
            'human_feedback': human_feedback,
            'updated_at': datetime.now().isoformat()
        }

        graph.update_state(config, state_update)

        for chunk in graph.stream(None, config):
            pass

        final_state = graph.get_state(config)
        final_values = final_state.values if final_state else {}

        manager = CheckpointManager()

        if final_values.get('status') == WorkflowStatus.COMPLETED.value:
            manager.update_workflow_status(thread_id, WorkflowStatus.COMPLETED.value)
            return {
                'thread_id': thread_id,
                'status': 'completed',
                'materials_generated': len(final_values.get('outreach_materials', [])),
                'state': final_values
            }
        else:
            return {
                'thread_id': thread_id,
                'status': final_values.get('status', 'unknown'),
                'state': final_values
            }

    except Exception as e:
        manager = CheckpointManager()
        manager.update_workflow_status(thread_id, WorkflowStatus.FAILED.value, str(e))
        return {
            'thread_id': thread_id,
            'status': 'failed',
            'error': str(e)
        }


# Export
__all__ = [
    'create_contact_outreach_graph',
    'run_contact_outreach_workflow',
    'resume_contact_outreach_workflow',
]
