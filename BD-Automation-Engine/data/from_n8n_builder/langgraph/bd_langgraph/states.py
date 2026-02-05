"""
WORKFLOW STATE DEFINITIONS
==========================
State dataclasses for LangGraph workflows following existing patterns from src/models/federal_program.py.

Each state class:
- Uses @dataclass decorator with field() for defaults
- Implements to_dict() for serialization
- Contains workflow-specific fields for tracking progress
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_HUMAN_REVIEW = "awaiting_human_review"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class HumanReviewType(Enum):
    """Types of human review gates."""
    STRATEGY_APPROVAL = "strategy_approval"
    CONTACT_APPROVAL = "contact_approval"
    PLAYBOOK_APPROVAL = "playbook_approval"
    CAPTURE_DECISION = "capture_decision"
    ALERT_ACKNOWLEDGEMENT = "alert_acknowledgement"
    REPORT_APPROVAL = "report_approval"


@dataclass
class BaseWorkflowState:
    """
    Base state class for all LangGraph workflows.

    Contains common fields for workflow tracking, human review gates,
    and execution statistics.
    """

    # === WORKFLOW IDENTITY ===
    workflow_id: str = ""
    workflow_type: str = ""
    thread_id: Optional[str] = None

    # === STATUS TRACKING ===
    status: str = field(default_factory=lambda: WorkflowStatus.PENDING.value)
    current_node: str = ""
    completed_nodes: List[str] = field(default_factory=list)

    # === TIMESTAMPS ===
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    # === HUMAN REVIEW ===
    awaiting_human_review: bool = False
    human_review_type: Optional[str] = None
    human_review_request_id: Optional[str] = None
    human_feedback: Optional[Dict[str, Any]] = None

    # === ERROR TRACKING ===
    error_message: Optional[str] = None
    error_node: Optional[str] = None
    retry_count: int = 0

    # === STATISTICS ===
    stats: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        return data

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def mark_node_complete(self, node_name: str) -> None:
        """Mark a node as completed."""
        if node_name not in self.completed_nodes:
            self.completed_nodes.append(node_name)
        self.updated_at = datetime.now().isoformat()

    def set_status(self, status: WorkflowStatus) -> None:
        """Update workflow status."""
        self.status = status.value
        self.updated_at = datetime.now().isoformat()
        if status == WorkflowStatus.COMPLETED:
            self.completed_at = datetime.now().isoformat()

    def request_human_review(self, review_type: HumanReviewType, request_id: str) -> None:
        """Set workflow to await human review."""
        self.awaiting_human_review = True
        self.human_review_type = review_type.value
        self.human_review_request_id = request_id
        self.set_status(WorkflowStatus.AWAITING_HUMAN_REVIEW)

    def process_human_feedback(self, feedback: Dict[str, Any]) -> None:
        """Process human review feedback."""
        self.human_feedback = feedback
        self.awaiting_human_review = False
        self.human_review_type = None
        self.human_review_request_id = None
        self.set_status(WorkflowStatus.IN_PROGRESS)


@dataclass
class BDProposalState(BaseWorkflowState):
    """
    State for BD Proposal Pipeline workflow.

    Tracks progress through: Research → Contacts → Competition → Strategy → Playbook
    """

    # === INPUT ===
    target_opportunity_id: str = ""
    opportunity_title: str = ""
    agency: str = ""
    naics_codes: List[str] = field(default_factory=list)
    target_value: float = 0.0
    solicitation_number: Optional[str] = None

    # === RESEARCH PHASE ===
    similar_contracts: List[Dict[str, Any]] = field(default_factory=list)
    market_intelligence: Dict[str, Any] = field(default_factory=dict)
    incumbent_info: Dict[str, Any] = field(default_factory=dict)
    opportunity_analysis: Dict[str, Any] = field(default_factory=dict)

    # === CONTACTS PHASE ===
    contacts_gathered: List[Dict[str, Any]] = field(default_factory=list)
    contacts_from_crm: List[Dict[str, Any]] = field(default_factory=list)
    contacts_from_sam: List[Dict[str, Any]] = field(default_factory=list)
    contacts_from_jobs: List[Dict[str, Any]] = field(default_factory=list)
    prioritized_contacts: List[Dict[str, Any]] = field(default_factory=list)

    # === COMPETITION PHASE ===
    competitor_analysis: Dict[str, Any] = field(default_factory=dict)
    incumbent_data: Dict[str, Any] = field(default_factory=dict)
    competitive_landscape: List[Dict[str, Any]] = field(default_factory=list)
    win_probability: float = 0.0

    # === STRATEGY PHASE ===
    bd_strategy: Dict[str, Any] = field(default_factory=dict)
    win_themes: List[str] = field(default_factory=list)
    differentiators: List[str] = field(default_factory=list)
    teaming_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    strategy_approved: bool = False
    strategy_revision_notes: Optional[str] = None

    # === OUTPUT ===
    final_playbook: Dict[str, Any] = field(default_factory=dict)
    playbook_path: str = ""
    playbook_summary: str = ""

    def __post_init__(self):
        """Initialize workflow type."""
        self.workflow_type = "bd_proposal"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        return data


@dataclass
class ContactOutreachState(BaseWorkflowState):
    """
    State for Contact Outreach Sequence workflow.

    Tracks progress through: Discover → Score → Approve → Generate
    """

    # === INPUT ===
    target_program: str = ""
    target_company: str = ""
    outreach_goal: str = ""  # meeting, partnership, intelligence
    max_contacts: int = 20

    # === DISCOVERY PHASE ===
    discovered_contacts: List[Dict[str, Any]] = field(default_factory=list)
    linkedin_profiles: List[Dict[str, Any]] = field(default_factory=list)
    sam_executives: List[Dict[str, Any]] = field(default_factory=list)
    job_posting_contacts: List[Dict[str, Any]] = field(default_factory=list)

    # === SCORING PHASE ===
    scored_contacts: List[Dict[str, Any]] = field(default_factory=list)
    contact_rankings: List[Dict[str, Any]] = field(default_factory=list)

    # === APPROVAL PHASE ===
    approved_contacts: List[Dict[str, Any]] = field(default_factory=list)
    rejected_contacts: List[Dict[str, Any]] = field(default_factory=list)
    approval_notes: Optional[str] = None

    # === OUTPUT ===
    outreach_materials: List[Dict[str, Any]] = field(default_factory=list)
    email_templates: List[Dict[str, Any]] = field(default_factory=list)
    linkedin_messages: List[Dict[str, Any]] = field(default_factory=list)
    call_scripts: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Initialize workflow type."""
        self.workflow_type = "contact_outreach"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class RecompeteState(BaseWorkflowState):
    """
    State for Recompete Intelligence workflow.

    Tracks progress through: Monitor → Detect → Alert → Capture
    """

    # === INPUT ===
    monitored_contracts: List[str] = field(default_factory=list)
    monitoring_criteria: Dict[str, Any] = field(default_factory=dict)
    alert_threshold_days: int = 365  # Days until recompete to trigger alert

    # === MONITORING PHASE ===
    contract_statuses: List[Dict[str, Any]] = field(default_factory=list)
    last_check_date: Optional[str] = None

    # === DETECTION PHASE ===
    recompete_signals: List[Dict[str, Any]] = field(default_factory=list)
    detected_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    signal_types: List[str] = field(default_factory=list)  # expiring, RFI, sources_sought, etc.

    # === ALERT PHASE ===
    alerts_generated: List[Dict[str, Any]] = field(default_factory=list)
    alert_priorities: Dict[str, str] = field(default_factory=dict)  # contract_id -> priority
    alert_acknowledged: bool = False

    # === CAPTURE PHASE ===
    capture_decisions: Dict[str, bool] = field(default_factory=dict)  # contract_id -> pursue
    capture_plans: List[Dict[str, Any]] = field(default_factory=list)
    capture_team_assigned: bool = False

    def __post_init__(self):
        """Initialize workflow type."""
        self.workflow_type = "recompete_intelligence"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class WeeklyPipelineState(BaseWorkflowState):
    """
    State for Weekly Pipeline Generation workflow.

    Tracks progress through: Scrape → Enrich → Score → Report
    """

    # === INPUT ===
    target_agencies: List[str] = field(default_factory=list)
    target_naics: List[str] = field(default_factory=list)
    target_psc: List[str] = field(default_factory=list)
    min_value: float = 0.0
    max_value: float = 0.0
    date_range_days: int = 7

    # === SCRAPING PHASE ===
    raw_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    scrape_sources: List[str] = field(default_factory=list)  # sam.gov, usaspending, etc.
    scrape_timestamp: Optional[str] = None

    # === ENRICHMENT PHASE ===
    enriched_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    incumbent_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    market_data: Dict[str, Any] = field(default_factory=dict)

    # === SCORING PHASE ===
    scored_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    score_criteria: Dict[str, float] = field(default_factory=dict)  # criteria -> weight
    top_opportunities: List[Dict[str, Any]] = field(default_factory=list)

    # === OUTPUT ===
    weekly_report: Dict[str, Any] = field(default_factory=dict)
    report_path: str = ""
    report_summary: str = ""
    opportunities_count: int = 0
    total_value: float = 0.0

    def __post_init__(self):
        """Initialize workflow type."""
        self.workflow_type = "weekly_pipeline"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


# Export all classes
__all__ = [
    'WorkflowStatus',
    'HumanReviewType',
    'BaseWorkflowState',
    'BDProposalState',
    'ContactOutreachState',
    'RecompeteState',
    'WeeklyPipelineState',
]
