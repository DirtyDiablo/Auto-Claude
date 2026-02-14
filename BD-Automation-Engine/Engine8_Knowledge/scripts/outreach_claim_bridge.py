"""
Outreach-to-Claim Bridge
=========================

Automatically updates claim tracker when outreach reaches key milestones:
- "meeting_booked" → marks program as partially claimed
- "placement" → marks program as fully claimed
- Any outreach activity → increments program outreach count

Connects the outreach activity log to the claim tracking system.

Usage:
    from scripts.outreach_claim_bridge import OutreachClaimBridge
    bridge = OutreachClaimBridge(store)
    bridge.process_outreach_event(event)
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class OutreachClaimBridge:
    """Bridges outreach activities to claim status updates."""

    # Outcomes that mark a program as claimed
    CLAIM_OUTCOMES = {"meeting_booked", "meeting_scheduled", "placement", "hired", "won"}

    # Outcomes that indicate partial progress
    PROGRESS_OUTCOMES = {"replied", "interested", "callback_scheduled", "referral"}

    def __init__(self, store, memory=None):
        """
        Args:
            store: BDKnowledgeStore instance
            memory: Optional MemoryLayer for logging events
        """
        self.store = store
        self.memory = memory

    def process_outreach_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an outreach event and update claim status.

        Args:
            event: Dict with keys:
                - contact_name: str
                - program: str (optional)
                - company: str (optional)
                - outcome: str (e.g., "meeting_booked", "replied", "no_response")
                - activity_type: str (e.g., "call", "email")
                - channel: str (optional)

        Returns:
            Processing result with claim status update info
        """
        result = {
            "processed": True,
            "event_type": event.get("outcome", "unknown"),
            "claim_updated": False,
            "claim_status": None,
        }

        outcome = event.get("outcome", "").lower().replace(" ", "_")
        program = event.get("program", "")
        company = event.get("company", "")
        contact_name = event.get("contact_name", "")

        # Resolve program from company if not provided
        if not program and company:
            program = self._resolve_program_from_company(company)

        if not program:
            result["note"] = "No program resolved, claim not updated"
            return result

        # Determine claim action
        if outcome in self.CLAIM_OUTCOMES:
            claim_status = "claimed"
            result["claim_updated"] = True
            result["claim_status"] = "claimed"
            logger.info(f"Program '{program}' marked as CLAIMED via {outcome} with {contact_name}")
        elif outcome in self.PROGRESS_OUTCOMES:
            claim_status = "in_progress"
            result["claim_updated"] = True
            result["claim_status"] = "in_progress"
            logger.info(f"Program '{program}' marked as IN_PROGRESS via {outcome}")
        else:
            claim_status = "outreach_logged"
            result["claim_status"] = "outreach_logged"

        # Index the claim event to Qdrant for tracking
        try:
            self._index_claim_event(
                program=program,
                contact_name=contact_name,
                company=company,
                outcome=outcome,
                claim_status=claim_status,
            )
        except Exception as e:
            logger.warning(f"Failed to index claim event: {e}")
            result["index_error"] = str(e)

        # Log to memory if available
        if self.memory and claim_status in ("claimed", "in_progress"):
            try:
                self.memory.add(
                    content=f"Program {program} claim status: {claim_status} "
                    f"(via {outcome} with {contact_name})",
                    metadata={
                        "type": "claim_update",
                        "program": program,
                        "status": claim_status,
                        "contact": contact_name,
                    },
                )
            except Exception:
                pass

        return result

    def process_activity_log(self, activities: list) -> Dict[str, Any]:
        """
        Process a batch of activity log entries.

        Args:
            activities: List of activity dicts from BullhornActivityLogger

        Returns:
            Batch processing results
        """
        results = {
            "total": len(activities),
            "processed": 0,
            "claims_updated": 0,
            "errors": 0,
        }

        for activity in activities:
            try:
                event = {
                    "contact_name": activity.get("contact_name", ""),
                    "program": activity.get("program", ""),
                    "company": activity.get("company", ""),
                    "outcome": activity.get("outcome", ""),
                    "activity_type": activity.get("activity_type", ""),
                    "channel": activity.get("channel", ""),
                }
                result = self.process_outreach_event(event)
                results["processed"] += 1
                if result.get("claim_updated"):
                    results["claims_updated"] += 1
            except Exception as e:
                logger.warning(f"Failed to process activity: {e}")
                results["errors"] += 1

        return results

    def _resolve_program_from_company(self, company: str) -> Optional[str]:
        """Try to find a program associated with a company."""
        try:
            results = self.store.search(
                query=f"{company} program contract",
                collection="programs",
                limit=1,
                score_threshold=0.4,
            )
            if results:
                payload = results[0].payload if hasattr(results[0], "payload") else results[0].get("payload", {})
                return payload.get("name", payload.get("program_name", ""))
        except Exception:
            pass
        return None

    def _index_claim_event(
        self,
        program: str,
        contact_name: str,
        company: str,
        outcome: str,
        claim_status: str,
    ):
        """Index a claim event to Qdrant activities collection."""
        activity = {
            "content": f"Claim event: {program} — {claim_status} via {outcome} with {contact_name} at {company}",
            "subject": f"Claim: {program} — {claim_status}",
            "activity_type": "claim_update",
            "contact_name": contact_name,
            "company": company or "",
            "program": program,
            "outcome": outcome,
            "claim_status": claim_status,
            "date": datetime.now().isoformat(),
        }
        self.store.index_activities([activity])
