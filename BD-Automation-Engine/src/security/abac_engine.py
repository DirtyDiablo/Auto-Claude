"""Phase 52A — Attribute-Based Access Control (ABAC) Policy Engine.

Evaluates every API request against fine-grained policies using subject,
resource, action, and environment attributes. Supports program isolation,
HUMINT access controls, export approvals, geo-restrictions, and NDA
requirements. OPA-compatible policy evaluation.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================

class Decision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class ClearanceLevel(str, Enum):
    UNCLASSIFIED = "unclassified"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"
    TS_SCI = "ts_sci"


_CLEARANCE_RANK = {
    ClearanceLevel.UNCLASSIFIED: 0,
    ClearanceLevel.CONFIDENTIAL: 1,
    ClearanceLevel.SECRET: 2,
    ClearanceLevel.TOP_SECRET: 3,
    ClearanceLevel.TS_SCI: 4,
}


@dataclass
class Subject:
    """Who is making the request."""
    user_id: str
    role: str  # admin | bd_director | manager | account_manager | analyst | viewer
    team: str = ""
    programs_assigned: List[str] = field(default_factory=list)
    clearance_level: ClearanceLevel = ClearanceLevel.UNCLASSIFIED
    nda_signed: bool = False
    manager_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "role": self.role,
            "team": self.team,
            "programs_assigned": self.programs_assigned,
            "clearance_level": self.clearance_level.value,
            "nda_signed": self.nda_signed,
            "manager_id": self.manager_id,
        }


@dataclass
class Resource:
    """What is being accessed."""
    resource_type: str  # contact | program | job | humint_note | simulation | report | export
    resource_id: str = ""
    program: str = ""
    classification: ClearanceLevel = ClearanceLevel.UNCLASSIFIED
    owner_id: str = ""
    owner_manager_id: str = ""
    has_competitor_data: bool = False
    record_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "program": self.program,
            "classification": self.classification.value,
            "owner_id": self.owner_id,
            "owner_manager_id": self.owner_manager_id,
            "has_competitor_data": self.has_competitor_data,
            "record_count": self.record_count,
        }


@dataclass
class Environment:
    """Context of the request."""
    ip_address: str = "127.0.0.1"
    geo_country: str = "US"
    device_type: str = "desktop"
    time_of_day: str = ""  # HH:MM
    is_vpn: bool = False

    def __post_init__(self):
        if not self.time_of_day:
            self.time_of_day = datetime.utcnow().strftime("%H:%M")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ip_address": self.ip_address,
            "geo_country": self.geo_country,
            "device_type": self.device_type,
            "time_of_day": self.time_of_day,
            "is_vpn": self.is_vpn,
        }


@dataclass
class PolicyDecision:
    """Result of an ABAC policy evaluation."""
    decision: Decision
    policy_id: str
    policy_name: str
    reason: str
    evaluation_time_ms: float = 0.0
    matched_policies: List[str] = field(default_factory=list)
    subject_id: str = ""
    resource_type: str = ""
    action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "policy_id": self.policy_id,
            "policy_name": self.policy_name,
            "reason": self.reason,
            "evaluation_time_ms": round(self.evaluation_time_ms, 3),
            "matched_policies": self.matched_policies,
            "subject_id": self.subject_id,
            "resource_type": self.resource_type,
            "action": self.action,
        }


@dataclass
class Policy:
    """A single ABAC policy rule."""
    policy_id: str
    name: str
    description: str
    priority: int = 0  # lower = higher priority
    enabled: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)
    decision: Decision = Decision.DENY
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.utcnow().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "enabled": self.enabled,
            "conditions": self.conditions,
            "decision": self.decision.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# =========================================
# BUILT-IN POLICIES
# =========================================

_BUILTIN_POLICIES = [
    Policy(
        policy_id="pol_admin_bypass",
        name="admin_full_access",
        description="Admins have full access to all resources",
        priority=0,
        conditions={"subject_role": "admin"},
        decision=Decision.ALLOW,
    ),
    Policy(
        policy_id="pol_program_isolation",
        name="program_isolation",
        description="Users can only access contacts/resources in their assigned programs",
        priority=10,
        conditions={"check": "program_assignment"},
        decision=Decision.DENY,
    ),
    Policy(
        policy_id="pol_humint_access",
        name="humint_restricted",
        description="HUMINT notes visible only to author, their manager, and BD director",
        priority=5,
        conditions={"resource_type": "humint_note", "check": "humint_ownership"},
        decision=Decision.DENY,
    ),
    Policy(
        policy_id="pol_export_approval",
        name="export_approval_required",
        description="Exports of >50 records require manager approval",
        priority=15,
        conditions={"action": "export", "check": "export_threshold"},
        decision=Decision.REQUIRE_APPROVAL,
    ),
    Policy(
        policy_id="pol_geo_restriction",
        name="dcgs_us_only",
        description="DCGS contacts only accessible from US IP addresses",
        priority=5,
        conditions={"check": "geo_dcgs"},
        decision=Decision.DENY,
    ),
    Policy(
        policy_id="pol_nda_required",
        name="nda_competitor_data",
        description="Competitor data in simulations requires signed NDA",
        priority=10,
        conditions={"check": "nda_competitor"},
        decision=Decision.DENY,
    ),
    Policy(
        policy_id="pol_clearance_check",
        name="clearance_required",
        description="Resource classification must not exceed user clearance level",
        priority=3,
        conditions={"check": "clearance_level"},
        decision=Decision.DENY,
    ),
    Policy(
        policy_id="pol_viewer_read_only",
        name="viewer_read_only",
        description="Viewers can only read, not write/delete/export",
        priority=8,
        conditions={"subject_role": "viewer", "check": "read_only"},
        decision=Decision.DENY,
    ),
]


# =========================================
# ABAC POLICY ENGINE
# =========================================

class ABACPolicyEngine:
    """Attribute-Based Access Control engine.

    Evaluates every request against fine-grained policies using subject,
    resource, action, and environment attributes. Policies are evaluated
    in priority order; first matching deny/require_approval wins.
    """

    def __init__(self):
        self._policies: Dict[str, Policy] = {}
        self._evaluation_count = 0
        for p in _BUILTIN_POLICIES:
            self._policies[p.policy_id] = p
        logger.info("ABACPolicyEngine initialized with %d built-in policies",
                     len(self._policies))

    # ----- policy management -----

    def add_policy(self, policy: Policy) -> None:
        self._policies[policy.policy_id] = policy

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        return self._policies.get(policy_id)

    def list_policies(self, enabled_only: bool = False) -> List[Policy]:
        policies = list(self._policies.values())
        if enabled_only:
            policies = [p for p in policies if p.enabled]
        return sorted(policies, key=lambda p: p.priority)

    def update_policy(self, policy_id: str, **kwargs) -> Optional[Policy]:
        policy = self._policies.get(policy_id)
        if not policy:
            return None
        for key, val in kwargs.items():
            if hasattr(policy, key):
                setattr(policy, key, val)
        policy.updated_at = datetime.utcnow().isoformat()
        return policy

    def disable_policy(self, policy_id: str) -> bool:
        policy = self._policies.get(policy_id)
        if policy:
            policy.enabled = False
            return True
        return False

    # ----- evaluation -----

    def evaluate(
        self,
        subject: Subject,
        action: str,
        resource: Resource,
        environment: Optional[Environment] = None,
    ) -> PolicyDecision:
        """Evaluate a request against all applicable policies."""
        start = time.time()
        self._evaluation_count += 1
        env = environment or Environment()

        matched: List[str] = []
        # Evaluate policies in priority order
        sorted_policies = sorted(
            [p for p in self._policies.values() if p.enabled],
            key=lambda p: p.priority,
        )

        for policy in sorted_policies:
            result = self._evaluate_policy(policy, subject, action, resource, env)
            if result is not None:
                matched.append(policy.policy_id)
                if result.decision != Decision.ALLOW:
                    result.evaluation_time_ms = (time.time() - start) * 1000
                    result.matched_policies = matched
                    result.subject_id = subject.user_id
                    result.resource_type = resource.resource_type
                    result.action = action
                    return result

        # Default: allow if no deny/require_approval matched
        elapsed = (time.time() - start) * 1000
        return PolicyDecision(
            decision=Decision.ALLOW,
            policy_id="default",
            policy_name="default_allow",
            reason="No deny policy matched; access allowed by default",
            evaluation_time_ms=elapsed,
            matched_policies=matched,
            subject_id=subject.user_id,
            resource_type=resource.resource_type,
            action=action,
        )

    def _evaluate_policy(
        self,
        policy: Policy,
        subject: Subject,
        action: str,
        resource: Resource,
        env: Environment,
    ) -> Optional[PolicyDecision]:
        """Evaluate a single policy. Returns decision or None if not applicable."""
        check = policy.conditions.get("check", "")
        cond_role = policy.conditions.get("subject_role", "")
        cond_action = policy.conditions.get("action", "")
        cond_rt = policy.conditions.get("resource_type", "")

        # Role-specific conditions
        if cond_role and subject.role != cond_role:
            return None

        # Action-specific conditions
        if cond_action and action != cond_action:
            return None

        # Resource type conditions
        if cond_rt and resource.resource_type != cond_rt:
            return None

        # Admin bypass
        if check == "" and cond_role == "admin" and subject.role == "admin":
            return PolicyDecision(
                decision=Decision.ALLOW,
                policy_id=policy.policy_id,
                policy_name=policy.name,
                reason="Admin role has full access",
            )

        # Program isolation check
        if check == "program_assignment":
            if subject.role == "admin":
                return None  # admins skip this
            if resource.program and resource.program not in subject.programs_assigned:
                return PolicyDecision(
                    decision=Decision.DENY,
                    policy_id=policy.policy_id,
                    policy_name=policy.name,
                    reason=f"User not assigned to program '{resource.program}'",
                )
            return None  # passes check, continue to next policy

        # HUMINT ownership check
        if check == "humint_ownership":
            if (subject.user_id == resource.owner_id or
                    subject.role == "bd_director" or
                    subject.user_id == resource.owner_manager_id):
                return None  # allowed
            return PolicyDecision(
                decision=Decision.DENY,
                policy_id=policy.policy_id,
                policy_name=policy.name,
                reason="HUMINT notes restricted to author, their manager, and BD director",
            )

        # Export threshold check
        if check == "export_threshold":
            if resource.record_count > 50:
                return PolicyDecision(
                    decision=Decision.REQUIRE_APPROVAL,
                    policy_id=policy.policy_id,
                    policy_name=policy.name,
                    reason=f"Export of {resource.record_count} records requires manager approval",
                )
            return None

        # Geo restriction for DCGS
        if check == "geo_dcgs":
            if "DCGS" in resource.program.upper() and env.geo_country != "US":
                return PolicyDecision(
                    decision=Decision.DENY,
                    policy_id=policy.policy_id,
                    policy_name=policy.name,
                    reason=f"DCGS data restricted to US access; request from {env.geo_country}",
                )
            return None

        # NDA + competitor data check
        if check == "nda_competitor":
            if resource.has_competitor_data and not subject.nda_signed:
                return PolicyDecision(
                    decision=Decision.DENY,
                    policy_id=policy.policy_id,
                    policy_name=policy.name,
                    reason="Competitor data requires signed NDA",
                )
            return None

        # Clearance level check
        if check == "clearance_level":
            subj_rank = _CLEARANCE_RANK.get(subject.clearance_level, 0)
            res_rank = _CLEARANCE_RANK.get(resource.classification, 0)
            if res_rank > subj_rank:
                return PolicyDecision(
                    decision=Decision.DENY,
                    policy_id=policy.policy_id,
                    policy_name=policy.name,
                    reason=(
                        f"Clearance level '{subject.clearance_level.value}' insufficient "
                        f"for '{resource.classification.value}' resource"
                    ),
                )
            return None

        # Viewer read-only check
        if check == "read_only":
            if action not in ("read", "search", "list"):
                return PolicyDecision(
                    decision=Decision.DENY,
                    policy_id=policy.policy_id,
                    policy_name=policy.name,
                    reason="Viewer role is read-only; write/delete/export denied",
                )
            return None

        return None

    # ----- explanation -----

    def explain_decision(self, decision: PolicyDecision) -> str:
        """Generate human-readable explanation of a policy decision."""
        if decision.decision == Decision.ALLOW:
            return (
                f"ACCESS GRANTED: {decision.reason}. "
                f"Evaluated {len(decision.matched_policies)} policies in "
                f"{decision.evaluation_time_ms:.1f}ms."
            )
        elif decision.decision == Decision.DENY:
            return (
                f"ACCESS DENIED by policy '{decision.policy_name}': {decision.reason}. "
                f"User '{decision.subject_id}' attempted '{decision.action}' on "
                f"'{decision.resource_type}'."
            )
        else:
            return (
                f"APPROVAL REQUIRED by policy '{decision.policy_name}': {decision.reason}. "
                f"User '{decision.subject_id}' must obtain manager approval."
            )

    # ----- data classification -----

    def classify_resource(self, resource_type: str, attributes: Dict[str, Any]) -> str:
        """Determine the sensitivity level of a resource."""
        if resource_type == "humint_note":
            return "restricted"
        if resource_type == "simulation" and attributes.get("has_competitor_data"):
            return "confidential"
        if resource_type == "contact":
            program = attributes.get("program", "")
            if "DCGS" in program.upper():
                return "sensitive"
            return "internal"
        if resource_type == "export":
            return "confidential"
        return "internal"

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_policies": len(self._policies),
            "enabled_policies": sum(1 for p in self._policies.values() if p.enabled),
            "total_evaluations": self._evaluation_count,
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[ABACPolicyEngine] = None


def get_abac_engine() -> ABACPolicyEngine:
    global _instance
    if _instance is None:
        _instance = ABACPolicyEngine()
    return _instance
