"""
BD PROPOSAL PIPELINE WORKFLOW
=============================
Main workflow graph for BD proposal generation with human-in-the-loop approval.

Pipeline: Research → Contacts → Competition → Strategy → Human Review → Playbook
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from langgraph.graph import StateGraph, END

from .states import BDProposalState, WorkflowStatus
from .checkpointer import get_checkpointer, get_memory_checkpointer, CheckpointManager
from .nodes import (
    research_opportunity,
    gather_contacts,
    analyze_competition,
    generate_strategy,
    request_human_review,
    process_human_feedback,
    finalize_playbook,
)
from .edges import should_continue_after_review
from .human_in_loop import get_feedback_for_resume

# Try to import logger
try:
    from src.utils import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def create_bd_proposal_graph(checkpointer=None):
    """
    Create the BD Proposal Pipeline graph.

    Args:
        checkpointer: Optional LangGraph checkpointer for persistence.
                     If None, creates a new SQLite checkpointer.

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create graph with state schema
    workflow = StateGraph(dict)

    # Add nodes
    workflow.add_node("research", research_opportunity)
    workflow.add_node("gather_contacts", gather_contacts)
    workflow.add_node("analyze_competition", analyze_competition)
    workflow.add_node("generate_strategy", generate_strategy)
    workflow.add_node("request_review", request_human_review)
    workflow.add_node("process_feedback", process_human_feedback)
    workflow.add_node("finalize", finalize_playbook)

    # Define the flow
    # Linear flow through research phases
    workflow.add_edge("research", "gather_contacts")
    workflow.add_edge("gather_contacts", "analyze_competition")
    workflow.add_edge("analyze_competition", "generate_strategy")
    workflow.add_edge("generate_strategy", "request_review")

    # Conditional after human review
    workflow.add_conditional_edges(
        "process_feedback",
        should_continue_after_review,
        {
            "finalize": "finalize",
            "revise": "generate_strategy",  # Loop back to revise strategy
            "abort": END
        }
    )

    # End after finalization
    workflow.add_edge("finalize", END)

    # Set entry point
    workflow.set_entry_point("research")

    # Compile with checkpointer and interrupt
    if checkpointer is None:
        checkpointer = get_checkpointer()

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["process_feedback"]  # Interrupt before processing feedback
    )


def run_bd_proposal_workflow(
    opportunity_id: str,
    opportunity_title: str,
    agency: str,
    naics_codes: List[str],
    target_value: float = 0.0,
    solicitation_number: Optional[str] = None,
    incumbent_name: Optional[str] = None,
    incumbent_uei: Optional[str] = None,
    auto_approve: bool = False,
    checkpointer=None,
    thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the BD Proposal Pipeline workflow.

    Args:
        opportunity_id: Target opportunity ID
        opportunity_title: Opportunity title/description
        agency: Awarding agency
        naics_codes: Relevant NAICS codes
        target_value: Estimated opportunity value
        solicitation_number: Optional solicitation number
        incumbent_name: Optional incumbent contractor name
        incumbent_uei: Optional incumbent UEI
        auto_approve: If True, skip human review
        checkpointer: Optional checkpointer (uses SQLite if None)
        thread_id: Optional thread ID for tracking

    Returns:
        Dictionary with workflow result and status
    """
    logger.info(f"Starting BD Proposal workflow for: {opportunity_title}")

    # Generate workflow ID
    workflow_id = f"bd_{uuid.uuid4().hex[:8]}"
    thread_id = thread_id or f"thread_{workflow_id}"

    # Initialize state
    initial_state = {
        # Workflow tracking
        'workflow_id': workflow_id,
        'workflow_type': 'bd_proposal',
        'thread_id': thread_id,
        'status': WorkflowStatus.IN_PROGRESS.value,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'completed_nodes': [],

        # Input parameters
        'target_opportunity_id': opportunity_id,
        'opportunity_title': opportunity_title,
        'agency': agency,
        'naics_codes': naics_codes,
        'target_value': target_value,
        'solicitation_number': solicitation_number,
        'incumbent_name': incumbent_name,
        'incumbent_uei': incumbent_uei,

        # Auto-approve flag
        'auto_approve_strategy': auto_approve,

        # Initialize empty collections
        'similar_contracts': [],
        'market_intelligence': {},
        'contacts_gathered': [],
        'prioritized_contacts': [],
        'competitor_analysis': {},
        'bd_strategy': {},
        'stats': {}
    }

    # Create graph
    graph = create_bd_proposal_graph(checkpointer)

    # Register workflow with checkpoint manager
    manager = CheckpointManager()
    manager.register_workflow(thread_id, 'bd_proposal', workflow_id)

    # Run workflow
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Execute until interrupt or completion
        result = graph.invoke(initial_state, config)

        # Check if interrupted for human review
        if result.get('awaiting_human_review'):
            manager.update_workflow_status(thread_id, WorkflowStatus.AWAITING_HUMAN_REVIEW.value)
            logger.info(f"Workflow {workflow_id} awaiting human review")
            return {
                'workflow_id': workflow_id,
                'thread_id': thread_id,
                'status': 'awaiting_human_review',
                'review_request_id': result.get('human_review_request_id'),
                'review_type': result.get('human_review_type'),
                'message': 'Workflow paused for human review. Call resume_bd_proposal_workflow() after review.',
                'state': result
            }

        # Workflow completed
        manager.update_workflow_status(thread_id, WorkflowStatus.COMPLETED.value)
        logger.info(f"Workflow {workflow_id} completed successfully")
        return {
            'workflow_id': workflow_id,
            'thread_id': thread_id,
            'status': 'completed',
            'playbook_path': result.get('playbook_path'),
            'playbook_summary': result.get('playbook_summary'),
            'stats': result.get('stats', {}),
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


def resume_bd_proposal_workflow(
    thread_id: str,
    human_feedback: Optional[Dict[str, Any]] = None,
    review_request_id: Optional[str] = None,
    checkpointer=None
) -> Dict[str, Any]:
    """
    Resume a BD Proposal workflow after human review.

    Args:
        thread_id: Thread ID of the paused workflow
        human_feedback: Human review feedback dictionary
                       {'decision': 'approve'|'revise'|'abort', 'notes': '...'}
        review_request_id: If provided, loads feedback from review file
        checkpointer: Optional checkpointer (uses SQLite if None)

    Returns:
        Dictionary with workflow result and status
    """
    logger.info(f"Resuming BD Proposal workflow: {thread_id}")

    # Load feedback from review file if request_id provided
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
            'error': 'No human feedback provided. Provide human_feedback dict or review_request_id.'
        }

    # Create graph
    graph = create_bd_proposal_graph(checkpointer)

    # Update state with feedback
    config = {"configurable": {"thread_id": thread_id}}

    # Get current state
    current_state = graph.get_state(config)
    if not current_state or not current_state.values:
        return {
            'status': 'error',
            'error': f'No workflow state found for thread: {thread_id}'
        }

    # Prepare update with feedback
    state_update = {
        'human_feedback': human_feedback,
        'updated_at': datetime.now().isoformat()
    }

    try:
        # Update state
        graph.update_state(config, state_update)

        # Continue execution
        result = None
        for chunk in graph.stream(None, config):
            result = chunk

        # Get final state
        final_state = graph.get_state(config)
        final_values = final_state.values if final_state else {}

        # Update manager
        manager = CheckpointManager()

        if final_values.get('status') == WorkflowStatus.COMPLETED.value:
            manager.update_workflow_status(thread_id, WorkflowStatus.COMPLETED.value)
            logger.info(f"Workflow {thread_id} completed after resume")
            return {
                'thread_id': thread_id,
                'status': 'completed',
                'playbook_path': final_values.get('playbook_path'),
                'playbook_summary': final_values.get('playbook_summary'),
                'stats': final_values.get('stats', {}),
                'state': final_values
            }
        elif final_values.get('status') == WorkflowStatus.ABORTED.value:
            manager.update_workflow_status(thread_id, WorkflowStatus.ABORTED.value)
            logger.info(f"Workflow {thread_id} aborted by user")
            return {
                'thread_id': thread_id,
                'status': 'aborted',
                'message': 'Workflow aborted based on human review decision'
            }
        elif final_values.get('awaiting_human_review'):
            # Needs another review (revision requested)
            manager.update_workflow_status(thread_id, WorkflowStatus.AWAITING_HUMAN_REVIEW.value)
            return {
                'thread_id': thread_id,
                'status': 'awaiting_human_review',
                'review_request_id': final_values.get('human_review_request_id'),
                'message': 'Workflow paused for another review cycle',
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
        logger.error(f"Workflow {thread_id} failed on resume: {e}")
        return {
            'thread_id': thread_id,
            'status': 'failed',
            'error': str(e)
        }


def get_bd_workflow_status(thread_id: str) -> Dict[str, Any]:
    """
    Get the current status of a BD Proposal workflow.

    Args:
        thread_id: Thread ID of the workflow

    Returns:
        Status dictionary
    """
    manager = CheckpointManager()
    metadata = manager.get_workflow(thread_id)

    if not metadata:
        return {
            'found': False,
            'error': f'Workflow not found: {thread_id}'
        }

    return {
        'found': True,
        **metadata
    }


# Export
__all__ = [
    'create_bd_proposal_graph',
    'run_bd_proposal_workflow',
    'resume_bd_proposal_workflow',
    'get_bd_workflow_status',
]
