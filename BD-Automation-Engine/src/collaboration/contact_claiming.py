"""Phase 50A — Contact Claiming System.

Manages exclusive ownership of contacts during BD outreach to prevent
duplicate calls and wasted effort. Claims expire after 7 days and can
be extended, transferred, or released.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================

class ClaimStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    RELEASED = "released"
    TRANSFERRED = "transferred"
    CONTESTED = "contested"


@dataclass
class ContactClaim:
    """An exclusive claim on a contact by a BD rep."""
    claim_id: str
    contact_id: str
    contact_name: str
    owner_id: str
    owner_name: str
    status: ClaimStatus = ClaimStatus.ACTIVE
    reason: str = ""
    program: str = ""
    created_at: str = ""
    expires_at: str = ""
    released_at: Optional[str] = None
    transferred_to: Optional[str] = None
    extend_count: int = 0
    max_extends: int = 3
    notes: str = ""

    def __post_init__(self):
        now = datetime.utcnow()
        if not self.created_at:
            self.created_at = now.isoformat()
        if not self.expires_at:
            self.expires_at = (now + timedelta(days=7)).isoformat()

    @property
    def is_expired(self) -> bool:
        try:
            exp = datetime.fromisoformat(self.expires_at)
            return datetime.utcnow() > exp
        except (ValueError, TypeError):
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "contact_id": self.contact_id,
            "contact_name": self.contact_name,
            "owner_id": self.owner_id,
            "owner_name": self.owner_name,
            "status": self.status.value,
            "reason": self.reason,
            "program": self.program,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "released_at": self.released_at,
            "transferred_to": self.transferred_to,
            "extend_count": self.extend_count,
            "max_extends": self.max_extends,
            "is_expired": self.is_expired,
            "notes": self.notes,
        }


@dataclass
class ClaimContest:
    """A dispute when two reps want the same contact."""
    contest_id: str
    claim_id: str
    contact_id: str
    requester_id: str
    requester_name: str
    current_owner_id: str
    reason: str = ""
    resolution: Optional[str] = None  # "approved" | "denied" | "split"
    created_at: str = ""
    resolved_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contest_id": self.contest_id,
            "claim_id": self.claim_id,
            "contact_id": self.contact_id,
            "requester_id": self.requester_id,
            "requester_name": self.requester_name,
            "current_owner_id": self.current_owner_id,
            "reason": self.reason,
            "resolution": self.resolution,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }


# =========================================
# CONTACT CLAIMING SYSTEM
# =========================================

# Pre-built BD reps for simulation
_BD_REPS = [
    {"id": "rep_01", "name": "Sarah Mitchell"},
    {"id": "rep_02", "name": "James Chen"},
    {"id": "rep_03", "name": "Patricia Okafor"},
    {"id": "rep_04", "name": "David Reyes"},
    {"id": "rep_05", "name": "Laura Kim"},
]

# Pre-built contacts for claiming
_CLAIMABLE_CONTACTS = [
    {"id": "c001", "name": "Craig Lindahl"},
    {"id": "c002", "name": "Mike Thompson"},
    {"id": "c003", "name": "Jennifer Walsh"},
    {"id": "c004", "name": "Robert Martinez"},
    {"id": "c005", "name": "Emily Chang"},
    {"id": "c006", "name": "Thomas Brooks"},
    {"id": "c007", "name": "Amanda Foster"},
    {"id": "c008", "name": "Kevin Park"},
    {"id": "c009", "name": "Diana Morales"},
    {"id": "c010", "name": "Brian O'Neill"},
]


class ContactClaimingSystem:
    """Manages exclusive contact ownership for BD reps.

    Rules:
    - One active claim per contact at a time
    - Claims expire after 7 days
    - Up to 3 extensions allowed (7 days each)
    - Contests can be raised for claimed contacts
    - Released contacts are immediately available
    """

    def __init__(self):
        self._claims: Dict[str, ContactClaim] = {}
        self._contests: Dict[str, ClaimContest] = {}
        self._contact_to_claim: Dict[str, str] = {}  # contact_id → claim_id
        self._claim_counter = 0
        self._contest_counter = 0
        logger.info("ContactClaimingSystem initialized")

    # ----- claim management -----

    def claim_contact(
        self,
        contact_id: str,
        contact_name: str,
        owner_id: str,
        owner_name: str,
        reason: str = "",
        program: str = "",
    ) -> ContactClaim:
        """Claim exclusive ownership of a contact."""
        # Check for existing active claim
        existing_id = self._contact_to_claim.get(contact_id)
        if existing_id:
            existing = self._claims[existing_id]
            self._expire_if_needed(existing)
            if existing.status == ClaimStatus.ACTIVE:
                raise ValueError(
                    f"Contact {contact_id} already claimed by {existing.owner_name} "
                    f"(claim {existing.claim_id})"
                )

        self._claim_counter += 1
        claim_id = f"claim_{hashlib.md5(f'{contact_id}:{owner_id}:{self._claim_counter}'.encode()).hexdigest()[:10]}"

        claim = ContactClaim(
            claim_id=claim_id,
            contact_id=contact_id,
            contact_name=contact_name,
            owner_id=owner_id,
            owner_name=owner_name,
            reason=reason,
            program=program,
        )
        self._claims[claim_id] = claim
        self._contact_to_claim[contact_id] = claim_id
        logger.info("Contact %s claimed by %s (%s)", contact_id, owner_name, claim_id)
        return claim

    def get_claim(self, claim_id: str) -> Optional[ContactClaim]:
        claim = self._claims.get(claim_id)
        if claim:
            self._expire_if_needed(claim)
        return claim

    def get_claim_for_contact(self, contact_id: str) -> Optional[ContactClaim]:
        claim_id = self._contact_to_claim.get(contact_id)
        if not claim_id:
            return None
        claim = self._claims.get(claim_id)
        if claim:
            self._expire_if_needed(claim)
            if claim.status == ClaimStatus.ACTIVE:
                return claim
        return None

    def release_claim(self, claim_id: str) -> bool:
        claim = self._claims.get(claim_id)
        if claim and claim.status == ClaimStatus.ACTIVE:
            claim.status = ClaimStatus.RELEASED
            claim.released_at = datetime.utcnow().isoformat()
            return True
        return False

    def extend_claim(self, claim_id: str, days: int = 7) -> bool:
        """Extend a claim by additional days."""
        claim = self._claims.get(claim_id)
        if not claim or claim.status != ClaimStatus.ACTIVE:
            return False
        if claim.extend_count >= claim.max_extends:
            return False

        try:
            current_exp = datetime.fromisoformat(claim.expires_at)
        except (ValueError, TypeError):
            current_exp = datetime.utcnow()

        claim.expires_at = (current_exp + timedelta(days=days)).isoformat()
        claim.extend_count += 1
        return True

    def transfer_claim(
        self, claim_id: str, new_owner_id: str, new_owner_name: str,
    ) -> bool:
        """Transfer a claim to another BD rep."""
        claim = self._claims.get(claim_id)
        if not claim or claim.status != ClaimStatus.ACTIVE:
            return False

        claim.transferred_to = new_owner_id
        claim.status = ClaimStatus.TRANSFERRED
        claim.released_at = datetime.utcnow().isoformat()

        # Create new claim for the new owner
        self.claim_contact(
            contact_id=claim.contact_id,
            contact_name=claim.contact_name,
            owner_id=new_owner_id,
            owner_name=new_owner_name,
            reason=f"Transferred from {claim.owner_name}",
            program=claim.program,
        )
        return True

    # ----- contests -----

    def contest_claim(
        self,
        claim_id: str,
        requester_id: str,
        requester_name: str,
        reason: str = "",
    ) -> ClaimContest:
        """Raise a dispute for a claimed contact."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Claim not found: {claim_id}")

        self._contest_counter += 1
        contest_id = f"contest_{hashlib.md5(f'{claim_id}:{requester_id}:{self._contest_counter}'.encode()).hexdigest()[:10]}"

        contest = ClaimContest(
            contest_id=contest_id,
            claim_id=claim_id,
            contact_id=claim.contact_id,
            requester_id=requester_id,
            requester_name=requester_name,
            current_owner_id=claim.owner_id,
            reason=reason,
        )
        claim.status = ClaimStatus.CONTESTED
        self._contests[contest_id] = contest
        return contest

    def resolve_contest(
        self, contest_id: str, resolution: str,
    ) -> Optional[ClaimContest]:
        """Resolve a claim contest: 'approved', 'denied', or 'split'."""
        contest = self._contests.get(contest_id)
        if not contest:
            return None

        contest.resolution = resolution
        contest.resolved_at = datetime.utcnow().isoformat()

        claim = self._claims.get(contest.claim_id)
        if claim:
            if resolution == "approved":
                # Transfer to requester
                claim.status = ClaimStatus.TRANSFERRED
                claim.transferred_to = contest.requester_id
            elif resolution == "denied":
                claim.status = ClaimStatus.ACTIVE
            elif resolution == "split":
                claim.status = ClaimStatus.ACTIVE
                # Both can work the contact

        return contest

    def list_contests(self, pending_only: bool = False) -> List[ClaimContest]:
        contests = list(self._contests.values())
        if pending_only:
            contests = [c for c in contests if c.resolution is None]
        return sorted(contests, key=lambda c: c.created_at, reverse=True)

    # ----- queries -----

    def list_claims(
        self,
        owner_id: Optional[str] = None,
        status: Optional[ClaimStatus] = None,
        active_only: bool = False,
    ) -> List[ContactClaim]:
        """List claims with optional filters."""
        # Check expirations first
        for claim in self._claims.values():
            self._expire_if_needed(claim)

        claims = list(self._claims.values())
        if owner_id:
            claims = [c for c in claims if c.owner_id == owner_id]
        if status:
            claims = [c for c in claims if c.status == status]
        if active_only:
            claims = [c for c in claims if c.status == ClaimStatus.ACTIVE]
        return sorted(claims, key=lambda c: c.created_at, reverse=True)

    def get_available_contacts(self) -> List[Dict[str, Any]]:
        """Get contacts not currently claimed."""
        claimed_ids = set()
        for claim in self._claims.values():
            self._expire_if_needed(claim)
            if claim.status == ClaimStatus.ACTIVE:
                claimed_ids.add(claim.contact_id)

        return [c for c in _CLAIMABLE_CONTACTS if c["id"] not in claimed_ids]

    def get_bd_reps(self) -> List[Dict[str, Any]]:
        """Get available BD reps."""
        return list(_BD_REPS)

    # ----- expiration -----

    def _expire_if_needed(self, claim: ContactClaim) -> None:
        """Mark expired claims."""
        if claim.status == ClaimStatus.ACTIVE and claim.is_expired:
            claim.status = ClaimStatus.EXPIRED

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        # Refresh expirations
        for c in self._claims.values():
            self._expire_if_needed(c)

        by_status: Dict[str, int] = {}
        for c in self._claims.values():
            by_status[c.status.value] = by_status.get(c.status.value, 0) + 1

        return {
            "total_claims": len(self._claims),
            "claims_by_status": by_status,
            "total_contests": len(self._contests),
            "pending_contests": sum(1 for c in self._contests.values() if c.resolution is None),
            "available_contacts": len(self.get_available_contacts()),
            "total_contacts": len(_CLAIMABLE_CONTACTS),
            "total_reps": len(_BD_REPS),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[ContactClaimingSystem] = None


def get_claiming_system() -> ContactClaimingSystem:
    global _instance
    if _instance is None:
        _instance = ContactClaimingSystem()
    return _instance
