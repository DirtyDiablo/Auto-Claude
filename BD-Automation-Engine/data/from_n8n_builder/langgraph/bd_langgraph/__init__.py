"""
BD LANGGRAPH STATEFUL WORKFLOWS
================================
Durable, stateful multi-step BD automation workflows with human-in-the-loop capabilities.

This package provides LangGraph-based workflows for:
- BD Proposal Pipeline: Research → Contacts → Competition → Strategy → Playbook
- Contact Outreach: Discover → Score → Approve → Generate
- Recompete Intelligence: Monitor → Detect → Alert → Capture
- Weekly Pipeline: Scrape → Enrich → Score → Report

Usage:
    from bd_langgraph import create_bd_proposal_graph, run_bd_proposal_workflow
    from bd_langgraph.states import BDProposalState
    from bd_langgraph.checkpointer import get_checkpointer
"""

__version__ = "1.0.0"

# State classes
from .states import (
    WorkflowStatus,
    HumanReviewType,
    BaseWorkflowState,
    BDProposalState,
    ContactOutreachState,
    RecompeteState,
    WeeklyPipelineState,
)

# Checkpointer utilities
from .checkpointer import (
    get_checkpointer,
    get_memory_checkpointer,
    CheckpointManager,
)

# Workflow graphs
from .bd_workflows import (
    create_bd_proposal_graph,
    run_bd_proposal_workflow,
    resume_bd_proposal_workflow,
)

from .contact_workflows import (
    create_contact_outreach_graph,
    run_contact_outreach_workflow,
    resume_contact_outreach_workflow,
)

from .recompete_workflows import (
    create_recompete_graph,
    run_recompete_workflow,
)

from .pipeline_workflows import (
    create_weekly_pipeline_graph,
    run_weekly_pipeline_workflow,
)

# Human-in-the-loop
from .human_in_loop import (
    HumanReviewRequest,
    create_review_request,
    submit_review,
    get_pending_reviews,
    get_review_for_workflow,
)

__all__ = [
    # Version
    '__version__',
    # States
    'WorkflowStatus',
    'HumanReviewType',
    'BaseWorkflowState',
    'BDProposalState',
    'ContactOutreachState',
    'RecompeteState',
    'WeeklyPipelineState',
    # Checkpointer
    'get_checkpointer',
    'get_memory_checkpointer',
    'CheckpointManager',
    # BD Workflows
    'create_bd_proposal_graph',
    'run_bd_proposal_workflow',
    'resume_bd_proposal_workflow',
    # Contact Workflows
    'create_contact_outreach_graph',
    'run_contact_outreach_workflow',
    'resume_contact_outreach_workflow',
    # Recompete Workflows
    'create_recompete_graph',
    'run_recompete_workflow',
    # Pipeline Workflows
    'create_weekly_pipeline_graph',
    'run_weekly_pipeline_workflow',
    # Human-in-the-loop
    'HumanReviewRequest',
    'create_review_request',
    'submit_review',
    'get_pending_reviews',
    'get_review_for_workflow',
]
