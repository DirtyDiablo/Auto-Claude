"""Tests for Phase 50A — Contact Claiming System."""

import pytest
from datetime import datetime, timedelta

from src.collaboration.contact_claiming import (
    ContactClaimingSystem,
    ContactClaim,
    ClaimStatus,
    ClaimContest,
    get_claiming_system,
)


@pytest.fixture
def cs():
    return ContactClaimingSystem()


# =========================================
# CLAIM CONTACT
# =========================================

def test_claim_contact(cs):
    claim = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    assert isinstance(claim, ContactClaim)
    assert claim.status == ClaimStatus.ACTIVE
    assert claim.contact_id == "c001"
    assert claim.owner_id == "rep_01"


def test_claim_with_reason_and_program(cs):
    claim = cs.claim_contact(
        "c001", "Craig Lindahl", "rep_01", "Sarah Mitchell",
        reason="Key decision maker for DCGS-A",
        program="DCGS-A",
    )
    assert claim.reason == "Key decision maker for DCGS-A"
    assert claim.program == "DCGS-A"


def test_claim_id_unique(cs):
    c1 = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    c1.status = ClaimStatus.RELEASED  # release so c002 can also be claimed
    c2 = cs.claim_contact("c002", "Mike Thompson", "rep_01", "Sarah Mitchell")
    assert c1.claim_id != c2.claim_id


def test_claim_expires_in_7_days(cs):
    claim = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    exp = datetime.fromisoformat(claim.expires_at)
    now = datetime.utcnow()
    # Should expire ~7 days from now (allow some tolerance)
    assert 6 < (exp - now).days <= 7


def test_duplicate_claim_raises(cs):
    cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    with pytest.raises(ValueError, match="already claimed"):
        cs.claim_contact("c001", "Craig Lindahl", "rep_02", "James Chen")


# =========================================
# GET CLAIMS
# =========================================

def test_get_claim(cs):
    claim = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    fetched = cs.get_claim(claim.claim_id)
    assert fetched is not None
    assert fetched.claim_id == claim.claim_id


def test_get_claim_not_found(cs):
    assert cs.get_claim("claim_nonexistent") is None


def test_get_claim_for_contact(cs):
    cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    claim = cs.get_claim_for_contact("c001")
    assert claim is not None
    assert claim.contact_id == "c001"


def test_get_claim_for_unclaimed_contact(cs):
    assert cs.get_claim_for_contact("c001") is None


# =========================================
# RELEASE
# =========================================

def test_release_claim(cs):
    claim = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    assert cs.release_claim(claim.claim_id) is True
    fetched = cs.get_claim(claim.claim_id)
    assert fetched.status == ClaimStatus.RELEASED


def test_release_allows_reclaim(cs):
    claim = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    cs.release_claim(claim.claim_id)
    new_claim = cs.claim_contact("c001", "Craig Lindahl", "rep_02", "James Chen")
    assert new_claim.owner_id == "rep_02"


# =========================================
# EXTEND
# =========================================

def test_extend_claim(cs):
    claim = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    orig_exp = claim.expires_at
    assert cs.extend_claim(claim.claim_id) is True
    assert claim.expires_at != orig_exp
    assert claim.extend_count == 1


def test_extend_limit(cs):
    claim = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    for _ in range(3):
        cs.extend_claim(claim.claim_id)
    assert cs.extend_claim(claim.claim_id) is False  # max_extends=3


# =========================================
# TRANSFER
# =========================================

def test_transfer_claim(cs):
    claim = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    assert cs.transfer_claim(claim.claim_id, "rep_02", "James Chen") is True
    assert claim.status == ClaimStatus.TRANSFERRED
    assert claim.transferred_to == "rep_02"
    new_claim = cs.get_claim_for_contact("c001")
    assert new_claim is not None
    assert new_claim.owner_id == "rep_02"


# =========================================
# CONTESTS
# =========================================

def test_contest_claim(cs):
    claim = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    contest = cs.contest_claim(
        claim.claim_id, "rep_02", "James Chen",
        reason="I have an existing relationship",
    )
    assert isinstance(contest, ClaimContest)
    assert claim.status == ClaimStatus.CONTESTED


def test_contest_not_found(cs):
    with pytest.raises(ValueError, match="Claim not found"):
        cs.contest_claim("claim_nonexistent", "rep_02", "James Chen")


def test_resolve_contest_approved(cs):
    claim = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    contest = cs.contest_claim(claim.claim_id, "rep_02", "James Chen")
    resolved = cs.resolve_contest(contest.contest_id, "approved")
    assert resolved.resolution == "approved"
    assert claim.status == ClaimStatus.TRANSFERRED


def test_resolve_contest_denied(cs):
    claim = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    contest = cs.contest_claim(claim.claim_id, "rep_02", "James Chen")
    resolved = cs.resolve_contest(contest.contest_id, "denied")
    assert resolved.resolution == "denied"
    assert claim.status == ClaimStatus.ACTIVE


def test_list_contests(cs):
    claim = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    cs.contest_claim(claim.claim_id, "rep_02", "James Chen")
    contests = cs.list_contests()
    assert len(contests) == 1


def test_list_pending_contests(cs):
    claim = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    contest = cs.contest_claim(claim.claim_id, "rep_02", "James Chen")
    cs.resolve_contest(contest.contest_id, "denied")
    pending = cs.list_contests(pending_only=True)
    assert len(pending) == 0


# =========================================
# QUERIES
# =========================================

def test_list_claims(cs):
    cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    cs.claim_contact("c002", "Mike Thompson", "rep_02", "James Chen")
    claims = cs.list_claims()
    assert len(claims) == 2


def test_list_claims_by_owner(cs):
    cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    cs.claim_contact("c002", "Mike Thompson", "rep_02", "James Chen")
    claims = cs.list_claims(owner_id="rep_01")
    assert len(claims) == 1


def test_list_active_claims(cs):
    c1 = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    cs.claim_contact("c002", "Mike Thompson", "rep_02", "James Chen")
    cs.release_claim(c1.claim_id)
    active = cs.list_claims(active_only=True)
    assert len(active) == 1


def test_available_contacts(cs):
    available_before = cs.get_available_contacts()
    cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    available_after = cs.get_available_contacts()
    assert len(available_after) == len(available_before) - 1


def test_get_bd_reps(cs):
    reps = cs.get_bd_reps()
    assert len(reps) == 5
    assert reps[0]["name"] == "Sarah Mitchell"


# =========================================
# TO DICT
# =========================================

def test_claim_to_dict(cs):
    claim = cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    d = claim.to_dict()
    assert d["contact_id"] == "c001"
    assert d["status"] == "active"
    assert "is_expired" in d


# =========================================
# STATS
# =========================================

def test_stats(cs):
    cs.claim_contact("c001", "Craig Lindahl", "rep_01", "Sarah Mitchell")
    stats = cs.get_stats()
    assert stats["total_claims"] >= 1
    assert stats["total_contacts"] == 10
    assert stats["total_reps"] == 5


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    import src.collaboration.contact_claiming as mod
    mod._instance = None
    s1 = get_claiming_system()
    s2 = get_claiming_system()
    assert s1 is s2
    mod._instance = None
