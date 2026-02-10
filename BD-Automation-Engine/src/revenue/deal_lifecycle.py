"""Phase 36A — Deal Lifecycle Engine

Track deals from first contact to first dollar:
  Discovery → Qualification → Requirements → Submission → Interview → Offer → Start → Revenue
  - Stage velocity: avg days per stage
  - Drop-off analysis: where do deals die?
  - Win rate by: program, tier, channel, rep, role type
  - Stale deal detector: flag deals stuck too long
  - Close date predictor
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import IntEnum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DEAL STAGES
# =========================================

class DealStage(IntEnum):
    DISCOVERY = 1
    QUALIFICATION = 2
    REQUIREMENTS = 3
    SUBMISSION = 4
    INTERVIEW = 5
    OFFER = 6
    START = 7
    REVENUE = 8

    @classmethod
    def from_string(cls, s: str) -> "DealStage":
        mapping = {v.name.lower(): v for v in cls}
        return mapping.get(s.lower(), cls.DISCOVERY)


STAGE_NAMES = {s: s.name.lower() for s in DealStage}

# Max expected days per stage before considered stale
STALE_THRESHOLDS = {
    DealStage.DISCOVERY: 14,
    DealStage.QUALIFICATION: 10,
    DealStage.REQUIREMENTS: 14,
    DealStage.SUBMISSION: 7,
    DealStage.INTERVIEW: 21,
    DealStage.OFFER: 10,
    DealStage.START: 30,
    DealStage.REVENUE: 60,
}


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class Deal:
    """Single deal in the pipeline."""
    id: str
    title: str
    program: str = ""
    contact_tier: int = 0
    channel: str = ""               # referral, cold_outreach, inbound, event
    rep: str = ""
    role_type: str = ""
    estimated_value: float = 0.0    # Projected annual revenue
    current_stage: DealStage = DealStage.DISCOVERY
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    outcome: str = "open"           # open, won, lost, stale
    created_at: str = ""
    closed_at: str = ""
    lost_reason: str = ""


@dataclass
class StageVelocity:
    """Average time spent in each stage."""
    stage: str
    avg_days: float = 0.0
    median_days: float = 0.0
    min_days: float = 0.0
    max_days: float = 0.0
    deal_count: int = 0


@dataclass
class DropOffAnalysis:
    """Where deals drop out of the pipeline."""
    stage: str
    lost_count: int = 0
    total_entered: int = 0
    drop_rate: float = 0.0
    top_reasons: List[str] = field(default_factory=list)


@dataclass
class WinRateAnalysis:
    """Win rate analysis."""
    dimension: str                  # program, tier, channel, rep, role_type
    breakdown: List[Dict[str, Any]] = field(default_factory=list)
    overall_win_rate: float = 0.0


@dataclass
class StaleDeal:
    """A deal that's stuck in a stage too long."""
    deal_id: str
    title: str
    stage: str
    days_in_stage: int = 0
    threshold_days: int = 0
    overdue_by: int = 0
    recommended_action: str = ""


# =========================================
# ENGINE
# =========================================

class DealLifecycleEngine:
    """Track and analyze deal lifecycle."""

    def __init__(self):
        self._deals: Dict[str, Deal] = {}

    def add_deal(self, deal: Deal) -> None:
        """Add a deal to the pipeline."""
        if not deal.created_at:
            deal.created_at = datetime.now(timezone.utc).isoformat()
        if not deal.stage_history:
            deal.stage_history = [{
                "stage": STAGE_NAMES[deal.current_stage],
                "entered_at": deal.created_at,
            }]
        self._deals[deal.id] = deal

    def set_deals(self, deals: List[Deal]) -> None:
        self._deals = {d.id: d for d in deals}

    def advance_stage(self, deal_id: str, new_stage: DealStage) -> bool:
        """Move a deal to the next stage."""
        deal = self._deals.get(deal_id)
        if not deal:
            return False
        now = datetime.now(timezone.utc).isoformat()
        deal.stage_history.append({
            "stage": STAGE_NAMES[new_stage],
            "entered_at": now,
        })
        deal.current_stage = new_stage
        if new_stage == DealStage.REVENUE:
            deal.outcome = "won"
            deal.closed_at = now
        return True

    def mark_lost(self, deal_id: str, reason: str = "") -> bool:
        """Mark a deal as lost."""
        deal = self._deals.get(deal_id)
        if not deal:
            return False
        deal.outcome = "lost"
        deal.lost_reason = reason
        deal.closed_at = datetime.now(timezone.utc).isoformat()
        return True

    def get_deal(self, deal_id: str) -> Optional[Deal]:
        return self._deals.get(deal_id)

    def get_open_deals(self) -> List[Deal]:
        return [d for d in self._deals.values() if d.outcome == "open"]

    def get_won_deals(self) -> List[Deal]:
        return [d for d in self._deals.values() if d.outcome == "won"]

    def get_lost_deals(self) -> List[Deal]:
        return [d for d in self._deals.values() if d.outcome == "lost"]

    # -----------------------------------------
    # Stage velocity
    # -----------------------------------------

    def get_stage_velocity(self) -> List[StageVelocity]:
        """Calculate average time in each stage."""
        stage_durations: Dict[str, List[float]] = defaultdict(list)

        for deal in self._deals.values():
            history = deal.stage_history
            for i in range(len(history) - 1):
                stage_name = history[i]["stage"]
                try:
                    entered = datetime.fromisoformat(
                        history[i]["entered_at"].replace("Z", "+00:00")
                    )
                    exited = datetime.fromisoformat(
                        history[i + 1]["entered_at"].replace("Z", "+00:00")
                    )
                    if entered.tzinfo is None:
                        entered = entered.replace(tzinfo=timezone.utc)
                    if exited.tzinfo is None:
                        exited = exited.replace(tzinfo=timezone.utc)
                    days = (exited - entered).total_seconds() / 86400
                    stage_durations[stage_name].append(days)
                except (ValueError, KeyError):
                    continue

        results = []
        for stage in DealStage:
            name = STAGE_NAMES[stage]
            durations = stage_durations.get(name, [])
            if durations:
                durations_sorted = sorted(durations)
                mid = len(durations_sorted) // 2
                median = (
                    durations_sorted[mid]
                    if len(durations_sorted) % 2 == 1
                    else (durations_sorted[mid - 1] + durations_sorted[mid]) / 2
                )
                results.append(StageVelocity(
                    stage=name,
                    avg_days=round(sum(durations) / len(durations), 1),
                    median_days=round(median, 1),
                    min_days=round(min(durations), 1),
                    max_days=round(max(durations), 1),
                    deal_count=len(durations),
                ))
            else:
                results.append(StageVelocity(stage=name, deal_count=0))

        return results

    # -----------------------------------------
    # Drop-off analysis
    # -----------------------------------------

    def get_drop_off_analysis(self) -> List[DropOffAnalysis]:
        """Analyze where deals drop out."""
        lost = self.get_lost_deals()
        lost_at_stage: Dict[str, List[str]] = defaultdict(list)

        for deal in lost:
            stage_name = STAGE_NAMES[deal.current_stage]
            lost_at_stage[stage_name].append(deal.lost_reason or "unknown")

        # Count deals that entered each stage
        entered: Dict[str, int] = defaultdict(int)
        for deal in self._deals.values():
            for entry in deal.stage_history:
                entered[entry["stage"]] += 1

        results = []
        for stage in DealStage:
            name = STAGE_NAMES[stage]
            lost_count = len(lost_at_stage.get(name, []))
            total = entered.get(name, 0)
            rate = (lost_count / total * 100) if total > 0 else 0

            # Top reasons
            reasons = lost_at_stage.get(name, [])
            reason_counts: Dict[str, int] = defaultdict(int)
            for r in reasons:
                reason_counts[r] += 1
            top_reasons = sorted(reason_counts, key=reason_counts.get, reverse=True)[:3]

            results.append(DropOffAnalysis(
                stage=name,
                lost_count=lost_count,
                total_entered=total,
                drop_rate=round(rate, 1),
                top_reasons=top_reasons,
            ))

        return results

    # -----------------------------------------
    # Win rates
    # -----------------------------------------

    def get_win_rates(self, dimension: str = "program") -> WinRateAnalysis:
        """Win rate analysis by dimension."""
        closed = [d for d in self._deals.values() if d.outcome in ("won", "lost")]
        if not closed:
            return WinRateAnalysis(dimension=dimension, overall_win_rate=0.0)

        won_total = sum(1 for d in closed if d.outcome == "won")
        overall = (won_total / len(closed) * 100) if closed else 0

        # Group by dimension
        groups: Dict[str, Dict[str, int]] = defaultdict(lambda: {"won": 0, "total": 0})
        for deal in closed:
            key = getattr(deal, dimension, "") or "unknown"
            if dimension == "contact_tier":
                key = str(key)
            groups[key]["total"] += 1
            if deal.outcome == "won":
                groups[key]["won"] += 1

        breakdown = []
        for key, counts in sorted(groups.items(), key=lambda x: x[1]["won"], reverse=True):
            rate = (counts["won"] / counts["total"] * 100) if counts["total"] > 0 else 0
            breakdown.append({
                "value": key,
                "won": counts["won"],
                "total": counts["total"],
                "win_rate": round(rate, 1),
            })

        return WinRateAnalysis(
            dimension=dimension,
            breakdown=breakdown,
            overall_win_rate=round(overall, 1),
        )

    # -----------------------------------------
    # Stale deal detection
    # -----------------------------------------

    def detect_stale_deals(self) -> List[StaleDeal]:
        """Flag deals stuck in a stage too long."""
        now = datetime.now(timezone.utc)
        stale = []

        for deal in self.get_open_deals():
            if not deal.stage_history:
                continue

            last_entry = deal.stage_history[-1]
            try:
                entered = datetime.fromisoformat(
                    last_entry["entered_at"].replace("Z", "+00:00")
                )
                if entered.tzinfo is None:
                    entered = entered.replace(tzinfo=timezone.utc)
            except (ValueError, KeyError):
                continue

            days_in = (now - entered).days
            threshold = STALE_THRESHOLDS.get(deal.current_stage, 14)

            if days_in > threshold:
                overdue = days_in - threshold
                action = _recommend_action(deal.current_stage, overdue)
                stale.append(StaleDeal(
                    deal_id=deal.id,
                    title=deal.title,
                    stage=STAGE_NAMES[deal.current_stage],
                    days_in_stage=days_in,
                    threshold_days=threshold,
                    overdue_by=overdue,
                    recommended_action=action,
                ))

        stale.sort(key=lambda s: s.overdue_by, reverse=True)
        return stale

    # -----------------------------------------
    # Deal value prediction
    # -----------------------------------------

    def predict_deal_value(self, deal_id: str) -> Dict[str, Any]:
        """Estimate deal revenue based on stage and similar deals."""
        deal = self._deals.get(deal_id)
        if not deal:
            return {"error": "Deal not found"}

        # Stage-based probability
        stage_probabilities = {
            DealStage.DISCOVERY: 0.10,
            DealStage.QUALIFICATION: 0.20,
            DealStage.REQUIREMENTS: 0.35,
            DealStage.SUBMISSION: 0.50,
            DealStage.INTERVIEW: 0.65,
            DealStage.OFFER: 0.80,
            DealStage.START: 0.95,
            DealStage.REVENUE: 1.0,
        }

        prob = stage_probabilities.get(deal.current_stage, 0.1)
        weighted_value = deal.estimated_value * prob

        # Adjust based on historical win rate for this program
        won_deals = [d for d in self._deals.values()
                     if d.outcome == "won" and d.program == deal.program]
        closed_deals = [d for d in self._deals.values()
                        if d.outcome in ("won", "lost") and d.program == deal.program]

        historical_rate = (len(won_deals) / len(closed_deals)) if closed_deals else prob
        blended_prob = (prob + historical_rate) / 2

        return {
            "deal_id": deal.id,
            "estimated_value": deal.estimated_value,
            "stage_probability": round(prob, 2),
            "historical_win_rate": round(historical_rate, 2),
            "blended_probability": round(blended_prob, 2),
            "weighted_value": round(weighted_value, 2),
            "confidence_adjusted_value": round(deal.estimated_value * blended_prob, 2),
        }

    # -----------------------------------------
    # Lifecycle summary
    # -----------------------------------------

    def get_lifecycle_summary(self) -> Dict[str, Any]:
        """Full lifecycle analytics summary."""
        total = len(self._deals)
        open_deals = len(self.get_open_deals())
        won = len(self.get_won_deals())
        lost = len(self.get_lost_deals())
        win_rate = (won / (won + lost) * 100) if (won + lost) > 0 else 0

        # Pipeline value
        pipeline_value = sum(d.estimated_value for d in self.get_open_deals())
        won_value = sum(d.estimated_value for d in self.get_won_deals())

        # Weighted pipeline
        weighted = 0.0
        stage_probs = {1: 0.1, 2: 0.2, 3: 0.35, 4: 0.5, 5: 0.65, 6: 0.8, 7: 0.95, 8: 1.0}
        for d in self.get_open_deals():
            p = stage_probs.get(int(d.current_stage), 0.1)
            weighted += d.estimated_value * p

        return {
            "total_deals": total,
            "open_deals": open_deals,
            "won_deals": won,
            "lost_deals": lost,
            "win_rate": round(win_rate, 1),
            "pipeline_value": round(pipeline_value, 2),
            "won_value": round(won_value, 2),
            "weighted_pipeline": round(weighted, 2),
        }


# =========================================
# HELPERS
# =========================================

def _recommend_action(stage: DealStage, overdue_days: int) -> str:
    actions = {
        DealStage.DISCOVERY: "Schedule qualification call or mark as dead lead",
        DealStage.QUALIFICATION: "Complete requirements gathering or disqualify",
        DealStage.REQUIREMENTS: "Finalize JD and submit candidate",
        DealStage.SUBMISSION: "Follow up with hiring manager on submission status",
        DealStage.INTERVIEW: "Check interview scheduling and candidate availability",
        DealStage.OFFER: "Push for offer acceptance or negotiate terms",
        DealStage.START: "Confirm start date and onboarding logistics",
        DealStage.REVENUE: "Verify billing has started and first invoice sent",
    }
    base = actions.get(stage, "Review deal status")
    if overdue_days > 30:
        base += " — CRITICAL: consider closing as stale"
    return base


# =========================================
# SINGLETON
# =========================================

_engine: Optional[DealLifecycleEngine] = None


def get_deal_engine() -> DealLifecycleEngine:
    global _engine
    if _engine is None:
        _engine = DealLifecycleEngine()
    return _engine
