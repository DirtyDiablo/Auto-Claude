"""
Phase 23A — Human-in-the-Loop Manager

Manages human approval gates in LangGraph workflows.
When a workflow hits an interrupt_before node, this manager:
1. Persists the pending approval request
2. Notifies the human (dashboard widget + optional email)
3. Waits for human response (approve/reject/modify)
4. Resumes the workflow with the human's decision
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from Engine8_Knowledge.workflows.checkpoint_store import CheckpointStore, get_checkpoint_store

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ApprovalRequest:
    request_id: str
    thread_id: str
    workflow_name: str
    node_name: str
    description: str
    state_snapshot: Dict[str, Any]
    options: List[str]
    urgency: str  # normal, high, critical
    created_at: str
    expires_at: str
    status: str  # pending, approved, rejected, modified, expired


@dataclass
class ApprovalDecision:
    request_id: str
    decision: str
    modified_state: Optional[Dict[str, Any]]
    notes: str
    decided_by: str
    decided_at: str


# ---------------------------------------------------------------------------
# HumanInTheLoopManager
# ---------------------------------------------------------------------------

class HumanInTheLoopManager:
    """Manages human approval gates in production workflows."""

    def __init__(self, checkpoint_store: Optional[CheckpointStore] = None,
                 storage_path: str = "data/approvals"):
        self.checkpoint_store = checkpoint_store or get_checkpoint_store()
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._requests: Dict[str, ApprovalRequest] = {}
        self._decisions: Dict[str, ApprovalDecision] = {}

        # Load existing requests
        self._load_requests()
        logger.info("human_loop.init", pending=len(self._get_pending()))

    def _load_requests(self):
        """Load persisted approval requests from disk."""
        requests_file = self.storage_path / "requests.json"
        if requests_file.exists():
            try:
                data = json.loads(requests_file.read_text())
                for req_data in data.get("requests", []):
                    req = ApprovalRequest(**req_data)
                    self._requests[req.request_id] = req
                for dec_data in data.get("decisions", []):
                    dec = ApprovalDecision(**dec_data)
                    self._decisions[dec.request_id] = dec
            except Exception as e:
                logger.warning("human_loop.load_error", error=str(e))

    def _save_requests(self):
        """Persist approval requests to disk."""
        requests_file = self.storage_path / "requests.json"
        data = {
            "requests": [asdict(r) for r in self._requests.values()],
            "decisions": [asdict(d) for d in self._decisions.values()],
            "saved_at": datetime.utcnow().isoformat(),
        }
        requests_file.write_text(json.dumps(data, indent=2, default=str))

    def _get_pending(self) -> List[ApprovalRequest]:
        """Get all pending requests."""
        return [r for r in self._requests.values() if r.status == "pending"]

    # ------------------------------------------------------------------
    # Create and manage approval requests
    # ------------------------------------------------------------------

    async def create_approval_request(
        self,
        thread_id: str,
        workflow_name: str,
        node_name: str,
        state_snapshot: dict,
        description: str,
        options: Optional[List[str]] = None,
        urgency: str = "normal",
        expires_in_hours: int = 24,
    ) -> ApprovalRequest:
        """Create a new approval request for a workflow interrupt."""
        request_id = f"approval_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()
        expires = now + timedelta(hours=expires_in_hours)

        # Extract relevant state fields (not full state)
        relevant_state = {}
        for key in ("classifications", "recommendations", "risks",
                     "analysis", "briefing", "report"):
            if key in state_snapshot:
                val = state_snapshot[key]
                # Truncate large lists
                if isinstance(val, list) and len(val) > 10:
                    relevant_state[key] = val[:10]
                    relevant_state[f"{key}_total"] = len(val)
                else:
                    relevant_state[key] = val

        request = ApprovalRequest(
            request_id=request_id,
            thread_id=thread_id,
            workflow_name=workflow_name,
            node_name=node_name,
            description=description,
            state_snapshot=relevant_state,
            options=options or ["approve", "reject", "modify"],
            urgency=urgency,
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
            status="pending",
        )

        self._requests[request_id] = request
        self._save_requests()

        logger.info("human_loop.request_created",
                     request_id=request_id, workflow=workflow_name,
                     node=node_name, urgency=urgency,
                     expires_in=expires_in_hours)
        return request

    async def list_pending_approvals(
        self,
        workflow_name: Optional[str] = None,
        urgency: Optional[str] = None,
        limit: int = 20,
    ) -> List[ApprovalRequest]:
        """List pending approval requests with optional filtering."""
        # Check for expired requests
        now = datetime.utcnow().isoformat()
        for req in self._get_pending():
            if req.expires_at < now:
                req.status = "expired"

        results = self._get_pending()

        if workflow_name:
            results = [r for r in results if r.workflow_name == workflow_name]
        if urgency:
            results = [r for r in results if r.urgency == urgency]

        # Sort by urgency (critical first), then by creation time
        urgency_order = {"critical": 0, "high": 1, "normal": 2}
        results.sort(key=lambda r: (urgency_order.get(r.urgency, 3), r.created_at))

        return results[:limit]

    async def get_approval_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific approval request."""
        return self._requests.get(request_id)

    async def submit_decision(
        self,
        request_id: str,
        decision: str,
        modified_state: Optional[dict] = None,
        notes: str = "",
        decided_by: str = "user",
    ) -> ApprovalDecision:
        """Submit a human decision for an approval request."""
        request = self._requests.get(request_id)
        if not request:
            raise ValueError(f"Approval request {request_id} not found")

        if request.status != "pending":
            raise ValueError(f"Request {request_id} is already {request.status}")

        if decision not in request.options:
            raise ValueError(f"Invalid decision '{decision}'. Options: {request.options}")

        # Update request status
        request.status = decision

        # Create decision record
        decision_rec = ApprovalDecision(
            request_id=request_id,
            decision=decision,
            modified_state=modified_state,
            notes=notes,
            decided_by=decided_by,
            decided_at=datetime.utcnow().isoformat(),
        )

        self._decisions[request_id] = decision_rec
        self._save_requests()

        logger.info("human_loop.decision_submitted",
                     request_id=request_id, decision=decision,
                     workflow=request.workflow_name, decided_by=decided_by)
        return decision_rec

    async def resume_workflow(self, request_id: str) -> str:
        """Resume the interrupted workflow with the human's decision.
        Returns the thread_id of the resumed execution."""
        request = self._requests.get(request_id)
        if not request:
            raise ValueError(f"Approval request {request_id} not found")

        decision = self._decisions.get(request_id)
        if not decision:
            raise ValueError(f"No decision found for request {request_id}")

        # Build updated state
        updated_state = {}
        if decision.decision == "approve":
            updated_state["human_approved"] = True
            updated_state["human_validated"] = True
        elif decision.decision == "reject":
            updated_state["human_approved"] = False
            updated_state["human_validated"] = False
        elif decision.decision == "modify" and decision.modified_state:
            updated_state = decision.modified_state
            updated_state["human_approved"] = True

        updated_state["_approval_decision"] = decision.decision
        updated_state["_approval_notes"] = decision.notes
        updated_state["_decided_by"] = decision.decided_by

        # Update checkpoint store
        await self.checkpoint_store.update_thread_status(
            request.thread_id, "running"
        )

        logger.info("human_loop.workflow_resumed",
                     request_id=request_id, thread_id=request.thread_id,
                     decision=decision.decision)
        return request.thread_id

    # ------------------------------------------------------------------
    # Auto-approve and maintenance
    # ------------------------------------------------------------------

    async def auto_approve_expired(self, default_action: str = "approve") -> List[str]:
        """Auto-approve requests past their expiration."""
        now = datetime.utcnow().isoformat()
        auto_approved = []

        for req in list(self._requests.values()):
            if req.status == "pending" and req.expires_at < now:
                decision = ApprovalDecision(
                    request_id=req.request_id,
                    decision=default_action,
                    modified_state=None,
                    notes="Auto-approved: request expired",
                    decided_by="system_auto",
                    decided_at=datetime.utcnow().isoformat(),
                )
                req.status = default_action
                self._decisions[req.request_id] = decision
                auto_approved.append(req.request_id)

                logger.info("human_loop.auto_approved",
                             request_id=req.request_id,
                             workflow=req.workflow_name)

        if auto_approved:
            self._save_requests()

        return auto_approved

    async def get_approval_stats(self) -> dict:
        """Stats: avg response time, approval rate, by workflow, by urgency."""
        total = len(self._requests)
        pending = sum(1 for r in self._requests.values() if r.status == "pending")
        approved = sum(1 for r in self._requests.values() if r.status == "approve")
        rejected = sum(1 for r in self._requests.values() if r.status == "reject")
        expired = sum(1 for r in self._requests.values() if r.status == "expired")

        # By workflow
        by_workflow: Dict[str, int] = {}
        for r in self._requests.values():
            by_workflow[r.workflow_name] = by_workflow.get(r.workflow_name, 0) + 1

        # By urgency
        by_urgency: Dict[str, int] = {}
        for r in self._requests.values():
            by_urgency[r.urgency] = by_urgency.get(r.urgency, 0) + 1

        # Average response time
        response_times = []
        for dec in self._decisions.values():
            req = self._requests.get(dec.request_id)
            if req:
                try:
                    created = datetime.fromisoformat(req.created_at)
                    decided = datetime.fromisoformat(dec.decided_at)
                    response_times.append((decided - created).total_seconds())
                except (ValueError, TypeError):
                    pass

        avg_response = sum(response_times) / len(response_times) if response_times else 0

        return {
            "total_requests": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "expired": expired,
            "approval_rate": round(approved / max(1, approved + rejected), 2),
            "avg_response_seconds": round(avg_response, 1),
            "by_workflow": by_workflow,
            "by_urgency": by_urgency,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_manager: Optional[HumanInTheLoopManager] = None


def get_hitl_manager() -> HumanInTheLoopManager:
    """Get or create the singleton HumanInTheLoopManager."""
    global _manager
    if _manager is None:
        _manager = HumanInTheLoopManager()
    return _manager
