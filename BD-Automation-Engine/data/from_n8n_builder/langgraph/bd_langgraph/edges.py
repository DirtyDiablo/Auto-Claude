"""
CONDITIONAL EDGE FUNCTIONS
==========================
Routing logic for LangGraph conditional edges.

Each function evaluates state and returns the name of the next node to execute.
"""

from typing import Any, Dict, Literal


# ============================================================================
# BD PROPOSAL PIPELINE EDGES
# ============================================================================

def should_continue_after_review(
    state: Dict[str, Any]
) -> Literal["finalize", "revise", "abort"]:
    """
    Route after human review based on feedback decision.

    Args:
        state: Current workflow state

    Returns:
        Next node name: "finalize", "revise", or "abort"
    """
    feedback = state.get('human_feedback', {})
    decision = feedback.get('decision', 'abort')

    if decision == 'approve':
        return "finalize"
    elif decision == 'revise':
        return "revise"
    else:
        return "abort"


def should_request_strategy_review(
    state: Dict[str, Any]
) -> Literal["request_review", "finalize"]:
    """
    Determine if strategy needs human review or can proceed.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    # Check if auto-approve is enabled
    if state.get('auto_approve_strategy', False):
        return "finalize"

    # Check win probability threshold
    win_prob = state.get('win_probability', 0)
    if win_prob >= 0.7:  # High confidence
        return "finalize"

    return "request_review"


# ============================================================================
# CONTACT OUTREACH EDGES
# ============================================================================

def has_contacts_for_review(
    state: Dict[str, Any]
) -> Literal["request_approval", "generate"]:
    """
    Check if there are contacts to review before generating materials.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    scored_contacts = state.get('scored_contacts', [])

    if not scored_contacts:
        # No contacts to review, skip to output
        return "generate"

    # Check if auto-approve is enabled
    if state.get('auto_approve_contacts', False):
        return "generate"

    return "request_approval"


def should_continue_contact_outreach(
    state: Dict[str, Any]
) -> Literal["generate", "abort"]:
    """
    Route after contact approval based on feedback.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    feedback = state.get('human_feedback', {})
    decision = feedback.get('decision', 'abort')

    if decision in ('approve', 'partial'):
        return "generate"
    else:
        return "abort"


# ============================================================================
# RECOMPETE INTELLIGENCE EDGES
# ============================================================================

def should_generate_alert(
    state: Dict[str, Any]
) -> Literal["generate_alert", "complete"]:
    """
    Determine if alerts should be generated based on signals.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    signals = state.get('recompete_signals', [])

    if signals:
        return "generate_alert"
    else:
        return "complete"


def should_prepare_capture(
    state: Dict[str, Any]
) -> Literal["prepare", "skip"]:
    """
    Determine if capture preparation should occur.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    alerts = state.get('alerts_generated', [])
    high_priority = [a for a in alerts if a.get('priority') == 'high']

    if high_priority:
        return "prepare"
    else:
        return "skip"


def should_request_capture_decision(
    state: Dict[str, Any]
) -> Literal["request_decision", "auto_prepare", "complete"]:
    """
    Determine if human decision needed for capture.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    alerts = state.get('alerts_generated', [])

    if not alerts:
        return "complete"

    # Check for high priority alerts requiring decision
    high_priority = [a for a in alerts if a.get('priority') == 'high']
    if high_priority:
        return "request_decision"

    # Auto-prepare for medium priority if configured
    if state.get('auto_prepare_medium', False):
        return "auto_prepare"

    return "complete"


# ============================================================================
# WEEKLY PIPELINE EDGES
# ============================================================================

def should_continue_enrichment(
    state: Dict[str, Any]
) -> Literal["enrich", "score"]:
    """
    Determine if enrichment should continue or move to scoring.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    raw = state.get('raw_opportunities', [])

    if not raw:
        # No opportunities, skip to scoring (will be empty)
        return "score"

    # Check if enrichment is enabled
    if state.get('skip_enrichment', False):
        return "score"

    return "enrich"


def should_generate_pipeline_report(
    state: Dict[str, Any]
) -> Literal["report", "complete"]:
    """
    Determine if report should be generated.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    scored = state.get('scored_opportunities', [])

    if not scored:
        return "complete"

    # Check if report generation is enabled
    if state.get('skip_report', False):
        return "complete"

    return "report"


# ============================================================================
# GENERIC EDGES
# ============================================================================

def check_workflow_abort(
    state: Dict[str, Any]
) -> Literal["continue", "abort"]:
    """
    Check if workflow should be aborted.

    Args:
        state: Current workflow state

    Returns:
        "continue" or "abort"
    """
    if state.get('status') == 'aborted':
        return "abort"

    if state.get('error_message'):
        return "abort"

    return "continue"


def check_retry_limit(
    state: Dict[str, Any],
    max_retries: int = 3
) -> Literal["retry", "fail"]:
    """
    Check if retry limit has been reached.

    Args:
        state: Current workflow state
        max_retries: Maximum retry attempts

    Returns:
        "retry" or "fail"
    """
    retry_count = state.get('retry_count', 0)

    if retry_count < max_retries:
        return "retry"
    else:
        return "fail"


# Export all edge functions
__all__ = [
    # BD Proposal edges
    'should_continue_after_review',
    'should_request_strategy_review',
    # Contact Outreach edges
    'has_contacts_for_review',
    'should_continue_contact_outreach',
    # Recompete edges
    'should_generate_alert',
    'should_prepare_capture',
    'should_request_capture_decision',
    # Weekly Pipeline edges
    'should_continue_enrichment',
    'should_generate_pipeline_report',
    # Generic edges
    'check_workflow_abort',
    'check_retry_limit',
]
