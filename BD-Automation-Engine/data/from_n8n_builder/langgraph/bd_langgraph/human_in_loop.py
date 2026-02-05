"""
HUMAN-IN-THE-LOOP REVIEW SYSTEM
================================
File-based human review gates for async workflow approval.

Reviews are stored as JSON files in data/human_reviews/ and can be:
- Viewed in any text editor
- Processed by external systems (N8N, email, etc.)
- Submitted programmatically via submit_review()
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .states import HumanReviewType

# Default directory for review files
DEFAULT_REVIEW_DIR = Path(__file__).parent.parent / "data" / "human_reviews"

# Try to import logger
try:
    from src.utils import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class HumanReviewRequest:
    """
    Human review request data structure.

    Represents a pending review that requires human input before
    the workflow can continue.
    """

    # === IDENTIFIERS ===
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    workflow_id: str = ""
    thread_id: Optional[str] = None

    # === REVIEW TYPE ===
    review_type: str = ""  # HumanReviewType value

    # === REQUEST DATA ===
    review_data: Dict[str, Any] = field(default_factory=dict)
    instructions: str = ""

    # === TIMESTAMPS ===
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = None

    # === STATUS ===
    status: str = "pending"  # pending, approved, rejected, expired
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None

    # === RESPONSE ===
    decision: Optional[str] = None  # approve, reject, revise, abort
    feedback_notes: Optional[str] = None
    approved_items: List[str] = field(default_factory=list)
    rejected_items: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HumanReviewRequest':
        """Create instance from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'HumanReviewRequest':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))


def _ensure_review_dir(review_dir: Optional[Path] = None) -> Path:
    """Ensure review directory exists."""
    dir_path = review_dir or DEFAULT_REVIEW_DIR
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def create_review_request(
    workflow_id: str,
    review_type: HumanReviewType,
    review_data: Dict[str, Any],
    instructions: str = "",
    thread_id: Optional[str] = None,
    expires_hours: Optional[int] = None,
    review_dir: Optional[Path] = None
) -> HumanReviewRequest:
    """
    Create a human review request and save to file.

    Args:
        workflow_id: ID of the workflow requesting review
        review_type: Type of review (from HumanReviewType enum)
        review_data: Data to be reviewed
        instructions: Instructions for the reviewer
        thread_id: LangGraph thread ID
        expires_hours: Hours until review expires (optional)
        review_dir: Directory to save review files

    Returns:
        HumanReviewRequest object
    """
    review_dir = _ensure_review_dir(review_dir)

    # Create request
    request = HumanReviewRequest(
        workflow_id=workflow_id,
        thread_id=thread_id,
        review_type=review_type.value,
        review_data=review_data,
        instructions=instructions
    )

    # Set expiration if provided
    if expires_hours:
        from datetime import timedelta
        expires = datetime.now() + timedelta(hours=expires_hours)
        request.expires_at = expires.isoformat()

    # Save to file
    file_name = f"review_{request.request_id}.json"
    file_path = review_dir / file_name

    with open(file_path, 'w') as f:
        f.write(request.to_json())

    # Also save a human-readable version
    readable_path = review_dir / f"review_{request.request_id}_PENDING.md"
    _save_readable_review(request, readable_path)

    logger.info(f"Created review request: {request.request_id} at {file_path}")

    return request


def _save_readable_review(request: HumanReviewRequest, file_path: Path) -> None:
    """Save a human-readable markdown version of the review request."""
    md_content = f"""# Human Review Request

**Request ID:** {request.request_id}
**Workflow ID:** {request.workflow_id}
**Review Type:** {request.review_type}
**Created:** {request.created_at}
**Status:** {request.status.upper()}

---

## Instructions

{request.instructions or "No specific instructions provided."}

---

## Data for Review

```json
{json.dumps(request.review_data, indent=2, default=str)}
```

---

## How to Submit Your Review

1. Open the JSON file: `review_{request.request_id}.json`
2. Set the `decision` field to one of: `approve`, `reject`, `revise`, `abort`
3. Add any notes in the `feedback_notes` field
4. Set `status` to `approved` or `rejected`
5. Save the file

Or use the Python API:
```python
from langgraph.human_in_loop import submit_review

submit_review(
    request_id="{request.request_id}",
    decision="approve",  # or "reject", "revise", "abort"
    notes="Your feedback here"
)
```

---

## Decision Options

| Decision | Description |
|----------|-------------|
| `approve` | Approve and continue workflow |
| `reject` | Reject and abort workflow |
| `revise` | Request revisions, then re-review |
| `abort` | Abort workflow without completing |

"""

    with open(file_path, 'w') as f:
        f.write(md_content)


def submit_review(
    request_id: str,
    decision: str,
    notes: Optional[str] = None,
    reviewer: Optional[str] = None,
    approved_items: Optional[List[str]] = None,
    rejected_items: Optional[List[str]] = None,
    review_dir: Optional[Path] = None
) -> HumanReviewRequest:
    """
    Submit a human review decision.

    Args:
        request_id: ID of the review request
        decision: Decision (approve, reject, revise, abort)
        notes: Optional feedback notes
        reviewer: Name of reviewer
        approved_items: List of approved item IDs (for partial approvals)
        rejected_items: List of rejected item IDs
        review_dir: Directory containing review files

    Returns:
        Updated HumanReviewRequest

    Raises:
        FileNotFoundError: If review request not found
        ValueError: If invalid decision
    """
    valid_decisions = {'approve', 'reject', 'revise', 'abort'}
    if decision not in valid_decisions:
        raise ValueError(f"Invalid decision: {decision}. Must be one of {valid_decisions}")

    review_dir = _ensure_review_dir(review_dir)
    file_path = review_dir / f"review_{request_id}.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Review request not found: {request_id}")

    # Load request
    with open(file_path, 'r') as f:
        request = HumanReviewRequest.from_json(f.read())

    # Check if already reviewed
    if request.status != 'pending':
        logger.warning(f"Review {request_id} already has status: {request.status}")

    # Update request
    request.decision = decision
    request.feedback_notes = notes
    request.reviewed_at = datetime.now().isoformat()
    request.reviewed_by = reviewer
    request.approved_items = approved_items or []
    request.rejected_items = rejected_items or []

    # Set status based on decision
    if decision == 'approve':
        request.status = 'approved'
    elif decision in ('reject', 'abort'):
        request.status = 'rejected'
    else:
        request.status = 'revision_requested'

    # Save updated request
    with open(file_path, 'w') as f:
        f.write(request.to_json())

    # Remove pending markdown file
    pending_md = review_dir / f"review_{request_id}_PENDING.md"
    if pending_md.exists():
        pending_md.unlink()

    # Create completed markdown file
    completed_md = review_dir / f"review_{request_id}_COMPLETED.md"
    _save_completed_review(request, completed_md)

    logger.info(f"Submitted review {request_id}: decision={decision}")

    return request


def _save_completed_review(request: HumanReviewRequest, file_path: Path) -> None:
    """Save a human-readable markdown version of the completed review."""
    md_content = f"""# Completed Review

**Request ID:** {request.request_id}
**Workflow ID:** {request.workflow_id}
**Review Type:** {request.review_type}
**Decision:** {request.decision.upper() if request.decision else "N/A"}
**Status:** {request.status.upper()}

---

## Timeline

- **Created:** {request.created_at}
- **Reviewed:** {request.reviewed_at}
- **Reviewed By:** {request.reviewed_by or "Unknown"}

---

## Feedback

{request.feedback_notes or "No feedback provided."}

---

## Approved Items

{chr(10).join(f"- {item}" for item in request.approved_items) or "All items" if request.decision == "approve" else "None"}

## Rejected Items

{chr(10).join(f"- {item}" for item in request.rejected_items) or "None"}

"""

    with open(file_path, 'w') as f:
        f.write(md_content)


def get_pending_reviews(
    workflow_type: Optional[str] = None,
    review_dir: Optional[Path] = None
) -> List[HumanReviewRequest]:
    """
    Get all pending review requests.

    Args:
        workflow_type: Filter by review type
        review_dir: Directory containing review files

    Returns:
        List of pending HumanReviewRequest objects
    """
    review_dir = _ensure_review_dir(review_dir)
    pending = []

    for file_path in review_dir.glob("review_*.json"):
        if "_PENDING" in file_path.name or "_COMPLETED" in file_path.name:
            continue  # Skip markdown files

        try:
            with open(file_path, 'r') as f:
                request = HumanReviewRequest.from_json(f.read())

            if request.status == 'pending':
                if workflow_type is None or request.review_type == workflow_type:
                    pending.append(request)
        except Exception as e:
            logger.error(f"Error loading review file {file_path}: {e}")

    # Sort by created date
    pending.sort(key=lambda r: r.created_at)

    return pending


def get_review_for_workflow(
    workflow_id: str,
    review_dir: Optional[Path] = None
) -> Optional[HumanReviewRequest]:
    """
    Get the most recent review request for a workflow.

    Args:
        workflow_id: Workflow ID to search for
        review_dir: Directory containing review files

    Returns:
        HumanReviewRequest or None if not found
    """
    review_dir = _ensure_review_dir(review_dir)
    reviews = []

    for file_path in review_dir.glob("review_*.json"):
        if "_PENDING" in file_path.name or "_COMPLETED" in file_path.name:
            continue

        try:
            with open(file_path, 'r') as f:
                request = HumanReviewRequest.from_json(f.read())

            if request.workflow_id == workflow_id:
                reviews.append(request)
        except Exception as e:
            logger.error(f"Error loading review file {file_path}: {e}")

    if not reviews:
        return None

    # Return most recent
    reviews.sort(key=lambda r: r.created_at, reverse=True)
    return reviews[0]


def get_review_by_id(
    request_id: str,
    review_dir: Optional[Path] = None
) -> Optional[HumanReviewRequest]:
    """
    Get a specific review request by ID.

    Args:
        request_id: Review request ID
        review_dir: Directory containing review files

    Returns:
        HumanReviewRequest or None if not found
    """
    review_dir = _ensure_review_dir(review_dir)
    file_path = review_dir / f"review_{request_id}.json"

    if not file_path.exists():
        return None

    try:
        with open(file_path, 'r') as f:
            return HumanReviewRequest.from_json(f.read())
    except Exception as e:
        logger.error(f"Error loading review file {file_path}: {e}")
        return None


def check_review_status(
    request_id: str,
    review_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Check the status of a review request.

    Args:
        request_id: Review request ID
        review_dir: Directory containing review files

    Returns:
        Dictionary with status information
    """
    request = get_review_by_id(request_id, review_dir)

    if not request:
        return {
            'found': False,
            'request_id': request_id,
            'error': 'Review request not found'
        }

    return {
        'found': True,
        'request_id': request.request_id,
        'workflow_id': request.workflow_id,
        'review_type': request.review_type,
        'status': request.status,
        'decision': request.decision,
        'is_pending': request.status == 'pending',
        'is_approved': request.status == 'approved',
        'is_rejected': request.status == 'rejected',
        'created_at': request.created_at,
        'reviewed_at': request.reviewed_at
    }


def get_feedback_for_resume(
    request_id: str,
    review_dir: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """
    Get feedback in format suitable for workflow resume.

    Args:
        request_id: Review request ID
        review_dir: Directory containing review files

    Returns:
        Feedback dictionary for workflow state, or None if not ready
    """
    request = get_review_by_id(request_id, review_dir)

    if not request or request.status == 'pending':
        return None

    return {
        'request_id': request.request_id,
        'decision': request.decision,
        'notes': request.feedback_notes,
        'approved_items': request.approved_items,
        'rejected_items': request.rejected_items,
        'reviewed_by': request.reviewed_by,
        'reviewed_at': request.reviewed_at
    }


def cleanup_old_reviews(
    days_old: int = 30,
    review_dir: Optional[Path] = None
) -> int:
    """
    Delete completed review files older than specified days.

    Args:
        days_old: Delete reviews older than this many days
        review_dir: Directory containing review files

    Returns:
        Number of files deleted
    """
    from datetime import timedelta

    review_dir = _ensure_review_dir(review_dir)
    cutoff = datetime.now() - timedelta(days=days_old)
    deleted = 0

    for file_path in review_dir.glob("review_*.json"):
        if "_PENDING" in file_path.name or "_COMPLETED" in file_path.name:
            continue

        try:
            with open(file_path, 'r') as f:
                request = HumanReviewRequest.from_json(f.read())

            # Only delete completed reviews
            if request.status != 'pending':
                created = datetime.fromisoformat(request.created_at.replace('Z', '+00:00').replace('+00:00', ''))
                if created < cutoff:
                    file_path.unlink()
                    deleted += 1

                    # Also delete related markdown files
                    for md_file in review_dir.glob(f"review_{request.request_id}_*.md"):
                        md_file.unlink()
                        deleted += 1

        except Exception as e:
            logger.error(f"Error processing review file {file_path}: {e}")

    logger.info(f"Cleaned up {deleted} old review files")
    return deleted


# Export all functions
__all__ = [
    'HumanReviewRequest',
    'create_review_request',
    'submit_review',
    'get_pending_reviews',
    'get_review_for_workflow',
    'get_review_by_id',
    'check_review_status',
    'get_feedback_for_resume',
    'cleanup_old_reviews',
]
