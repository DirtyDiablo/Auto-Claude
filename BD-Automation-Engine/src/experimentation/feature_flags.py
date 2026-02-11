"""Phase 55A — Feature Flag Engine.

Manages boolean, percentage-based, user-list, and gradual-rollout feature
flags for controlled feature releases across the BD pipeline.
"""

from __future__ import annotations

import hashlib
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

class FlagType(Enum):
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    GRADUAL_ROLLOUT = "gradual_rollout"


class FlagStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


@dataclass
class RolloutStage:
    """A single stage in a gradual rollout."""
    stage_id: str
    percentage: float  # 0-100
    duration_hours: float
    started_at: str = ""
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "percentage": self.percentage,
            "duration_hours": self.duration_hours,
            "started_at": self.started_at,
            "completed": self.completed,
        }


@dataclass
class FeatureFlag:
    """A feature flag with multiple evaluation strategies."""
    flag_id: str
    name: str
    description: str = ""
    flag_type: FlagType = FlagType.BOOLEAN
    status: FlagStatus = FlagStatus.ACTIVE
    enabled: bool = False
    percentage: float = 0.0  # 0-100, used for PERCENTAGE type
    allowed_users: List[str] = field(default_factory=list)
    rollout_stages: List[RolloutStage] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        now = datetime.utcnow().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flag_id": self.flag_id,
            "name": self.name,
            "description": self.description,
            "flag_type": self.flag_type.value,
            "status": self.status.value,
            "enabled": self.enabled,
            "percentage": self.percentage,
            "allowed_users": self.allowed_users,
            "rollout_stages": [s.to_dict() for s in self.rollout_stages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": self.tags,
        }


# =========================================
# FEATURE FLAG ENGINE
# =========================================

class FeatureFlagEngine:
    """Manages feature flags with boolean, percentage, user-list, and
    gradual-rollout evaluation strategies.

    Flags are evaluated differently depending on their type:
    - BOOLEAN: checks the ``enabled`` field directly.
    - PERCENTAGE: hashes the user_id to produce a deterministic 0-100
      bucket and compares against the flag's ``percentage`` threshold.
    - USER_LIST: checks whether user_id is in ``allowed_users``.
    - GRADUAL_ROLLOUT: determines the current rollout stage percentage
      and evaluates as a percentage flag at that level.
    """

    def __init__(self):
        self._flags: Dict[str, FeatureFlag] = {}
        self._flag_counter = 0
        self._create_default_flags()
        logger.info("FeatureFlagEngine initialized with %d default flags", len(self._flags))

    # ----- flag CRUD -----

    def create_flag(
        self,
        name: str,
        flag_type: FlagType = FlagType.BOOLEAN,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> FeatureFlag:
        """Create a new feature flag."""
        self._flag_counter += 1
        flag_id = f"flag_{hashlib.md5(f'flag:{name}:{self._flag_counter}:{time.time()}'.encode()).hexdigest()[:12]}"

        flag = FeatureFlag(
            flag_id=flag_id,
            name=name,
            description=description,
            flag_type=flag_type,
            tags=tags or [],
        )
        self._flags[flag_id] = flag
        logger.info("Created flag %s (%s) type=%s", flag_id, name, flag_type.value)
        return flag

    def get_flag(self, flag_id: str) -> Optional[FeatureFlag]:
        """Return a flag by ID."""
        return self._flags.get(flag_id)

    def list_flags(
        self,
        status: Optional[FlagStatus] = None,
        tag: Optional[str] = None,
    ) -> List[FeatureFlag]:
        """List flags with optional status and tag filters."""
        flags = list(self._flags.values())
        if status is not None:
            flags = [f for f in flags if f.status == status]
        if tag is not None:
            flags = [f for f in flags if tag in f.tags]
        return flags

    def update_flag(self, flag_id: str, **kwargs: Any) -> Optional[FeatureFlag]:
        """Update flag attributes. Accepts any FeatureFlag field."""
        flag = self._flags.get(flag_id)
        if not flag:
            return None

        for key, value in kwargs.items():
            if hasattr(flag, key):
                setattr(flag, key, value)
        flag.updated_at = datetime.utcnow().isoformat()
        logger.info("Updated flag %s: %s", flag_id, list(kwargs.keys()))
        return flag

    def delete_flag(self, flag_id: str) -> FeatureFlag:
        """Archive a flag (soft-delete)."""
        flag = self._flags.get(flag_id)
        if not flag:
            raise ValueError(f"Flag not found: {flag_id}")

        flag.status = FlagStatus.ARCHIVED
        flag.updated_at = datetime.utcnow().isoformat()
        logger.info("Archived flag %s (%s)", flag_id, flag.name)
        return flag

    # ----- evaluation -----

    def is_enabled(self, flag_id: str, user_id: Optional[str] = None) -> bool:
        """Evaluate whether a flag is enabled for the given user.

        Evaluation logic per flag type:
        - BOOLEAN: returns ``flag.enabled``
        - PERCENTAGE: hashes user_id into a 0-99 bucket; enabled if
          bucket < flag.percentage.  Without a user_id returns False.
        - USER_LIST: returns True if user_id is in ``allowed_users``.
        - GRADUAL_ROLLOUT: finds the current active stage and evaluates
          as a percentage flag at that stage's percentage.
        """
        flag = self._flags.get(flag_id)
        if not flag:
            logger.warning("Flag not found: %s", flag_id)
            return False

        if flag.status != FlagStatus.ACTIVE:
            return False

        if flag.flag_type == FlagType.BOOLEAN:
            return flag.enabled

        if flag.flag_type == FlagType.PERCENTAGE:
            if user_id is None:
                return False
            bucket = self._user_bucket(flag_id, user_id)
            return bucket < flag.percentage

        if flag.flag_type == FlagType.USER_LIST:
            if user_id is None:
                return False
            return user_id in flag.allowed_users

        if flag.flag_type == FlagType.GRADUAL_ROLLOUT:
            current_pct = self._current_rollout_percentage(flag)
            if user_id is None:
                return False
            bucket = self._user_bucket(flag_id, user_id)
            return bucket < current_pct

        return False

    # ----- gradual rollout -----

    def set_rollout_stages(
        self,
        flag_id: str,
        stages: List[Dict[str, Any]],
    ) -> FeatureFlag:
        """Configure gradual rollout stages for a flag.

        Each entry in *stages* should be a dict with ``percentage`` and
        ``duration_hours`` keys.
        """
        flag = self._flags.get(flag_id)
        if not flag:
            raise ValueError(f"Flag not found: {flag_id}")

        rollout_stages: List[RolloutStage] = []
        for idx, stage_def in enumerate(stages):
            stage_id = f"rs_{hashlib.md5(f'{flag_id}:stage:{idx}'.encode()).hexdigest()[:8]}"
            rollout_stages.append(RolloutStage(
                stage_id=stage_id,
                percentage=stage_def.get("percentage", 0.0),
                duration_hours=stage_def.get("duration_hours", 24.0),
            ))

        flag.rollout_stages = rollout_stages
        flag.flag_type = FlagType.GRADUAL_ROLLOUT
        flag.updated_at = datetime.utcnow().isoformat()
        logger.info("Set %d rollout stages for flag %s", len(rollout_stages), flag_id)
        return flag

    def advance_rollout(self, flag_id: str) -> FeatureFlag:
        """Advance the gradual rollout to the next stage.

        Marks the current active stage as completed and starts the next
        one.  If all stages are already completed, this is a no-op.
        """
        flag = self._flags.get(flag_id)
        if not flag:
            raise ValueError(f"Flag not found: {flag_id}")
        if not flag.rollout_stages:
            raise ValueError(f"Flag {flag_id} has no rollout stages")

        now = datetime.utcnow().isoformat()

        # Find the first incomplete stage and mark it completed
        for idx, stage in enumerate(flag.rollout_stages):
            if not stage.completed:
                stage.completed = True
                if not stage.started_at:
                    stage.started_at = now
                logger.info("Completed rollout stage %s at %s%% for flag %s",
                            stage.stage_id, stage.percentage, flag_id)
                # Start the next incomplete stage
                for next_stage in flag.rollout_stages[idx + 1:]:
                    if not next_stage.completed:
                        next_stage.started_at = now
                        logger.info("Advanced to stage %s at %s%% for flag %s",
                                    next_stage.stage_id, next_stage.percentage, flag_id)
                        break
                break

        flag.updated_at = now
        return flag

    # ----- helpers -----

    @staticmethod
    def _user_bucket(flag_id: str, user_id: str) -> float:
        """Deterministic 0-99 bucket for a user/flag pair."""
        h = hashlib.md5(f"{flag_id}:{user_id}".encode()).hexdigest()
        return int(h[:8], 16) % 100

    @staticmethod
    def _current_rollout_percentage(flag: FeatureFlag) -> float:
        """Return the percentage for the current active rollout stage."""
        if not flag.rollout_stages:
            return 0.0
        # The current percentage is from the last started-but-not-completed
        # stage, or the last completed stage if all are done.
        current_pct = 0.0
        for stage in flag.rollout_stages:
            if stage.started_at:
                current_pct = stage.percentage
            if not stage.completed and stage.started_at:
                return current_pct
        return current_pct

    # ----- default flags -----

    def _create_default_flags(self) -> None:
        """Pre-create a set of default feature flags for the BD pipeline."""
        defaults = [
            {
                "name": "dark_mode",
                "flag_type": FlagType.BOOLEAN,
                "description": "Enable dark mode UI theme across the dashboard",
                "tags": ["ui", "theme"],
            },
            {
                "name": "new_search_ui",
                "flag_type": FlagType.PERCENTAGE,
                "description": "Redesigned search interface with faceted filters",
                "tags": ["ui", "search"],
            },
            {
                "name": "ai_call_prep",
                "flag_type": FlagType.GRADUAL_ROLLOUT,
                "description": "AI-powered call preparation briefs for BD meetings",
                "tags": ["ai", "bd"],
            },
            {
                "name": "pipeline_v2",
                "flag_type": FlagType.GRADUAL_ROLLOUT,
                "description": "Next-generation BD pipeline processing engine",
                "tags": ["pipeline", "core"],
            },
            {
                "name": "real_time_collab",
                "flag_type": FlagType.USER_LIST,
                "description": "Real-time collaboration features for BD team",
                "tags": ["collaboration", "beta"],
            },
            {
                "name": "advanced_analytics",
                "flag_type": FlagType.PERCENTAGE,
                "description": "Advanced analytics dashboard with predictive models",
                "tags": ["analytics", "ai"],
            },
            {
                "name": "mobile_pwa",
                "flag_type": FlagType.GRADUAL_ROLLOUT,
                "description": "Progressive web app for mobile access",
                "tags": ["mobile", "pwa"],
            },
            {
                "name": "chaos_testing",
                "flag_type": FlagType.USER_LIST,
                "description": "Chaos engineering testing mode for resilience validation",
                "tags": ["testing", "resilience"],
            },
        ]

        for defn in defaults:
            self.create_flag(**defn)

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        """Return summary statistics about registered flags."""
        flags = list(self._flags.values())
        return {
            "total_flags": len(flags),
            "active_flags": sum(1 for f in flags if f.status == FlagStatus.ACTIVE),
            "inactive_flags": sum(1 for f in flags if f.status == FlagStatus.INACTIVE),
            "archived_flags": sum(1 for f in flags if f.status == FlagStatus.ARCHIVED),
            "by_type": {
                ft.value: sum(1 for f in flags if f.flag_type == ft)
                for ft in FlagType
            },
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[FeatureFlagEngine] = None


def get_flag_engine() -> FeatureFlagEngine:
    global _instance
    if _instance is None:
        _instance = FeatureFlagEngine()
    return _instance
