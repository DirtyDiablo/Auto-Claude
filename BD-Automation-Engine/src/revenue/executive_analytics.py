"""Phase 36A — Executive Revenue Dashboard Data

Board-ready metrics and automated executive summary:
  - Revenue this month/quarter/year vs target
  - Pipeline weighted value with confidence intervals
  - Revenue per rep with quota attainment
  - Customer concentration and diversification
  - Margin trends with forecast
  - Top accounts by revenue and growth potential
  - MoM, QoQ, YoY comparison
  - Automated executive summary generation
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class QuotaAttainment:
    """Rep quota attainment."""
    rep: str
    revenue: float = 0.0
    quota: float = 0.0
    attainment_pct: float = 0.0
    placements: int = 0
    rank: int = 0


@dataclass
class DiversificationScore:
    """Customer/program diversification score."""
    score: float = 0.0              # 0-100
    program_count: int = 0
    top_program_pct: float = 0.0
    assessment: str = "balanced"    # concentrated, moderate, balanced, diversified


@dataclass
class PeriodComparison:
    """Period-over-period comparison."""
    current_period: str
    prior_period: str
    current_revenue: float = 0.0
    prior_revenue: float = 0.0
    change_pct: float = 0.0
    change_absolute: float = 0.0
    trend: str = "stable"           # growing, stable, declining


@dataclass
class ExecutiveSummary:
    """Auto-generated executive summary."""
    period: str
    total_revenue: float = 0.0
    target_revenue: float = 0.0
    attainment_pct: float = 0.0
    weighted_pipeline: float = 0.0
    active_placements: int = 0
    new_placements: int = 0
    avg_margin_pct: float = 0.0
    top_accounts: List[Dict[str, Any]] = field(default_factory=list)
    period_comparison: Optional[PeriodComparison] = None
    diversification: Optional[DiversificationScore] = None
    rep_attainment: List[QuotaAttainment] = field(default_factory=list)
    narrative: str = ""
    generated_at: str = ""


# =========================================
# EXECUTIVE ANALYTICS ENGINE
# =========================================

class ExecutiveAnalytics:
    """Generate board-ready executive revenue analytics."""

    def __init__(self):
        self._revenue_data: Dict[str, float] = {}      # period -> revenue
        self._target_data: Dict[str, float] = {}        # period -> target
        self._rep_data: List[Dict[str, Any]] = []
        self._program_revenue: Dict[str, float] = {}
        self._account_data: List[Dict[str, Any]] = []
        self._pipeline_data: List[Dict[str, Any]] = []
        self._placement_count: int = 0
        self._new_placements: int = 0
        self._avg_margin: float = 0.0

    def set_revenue_data(self, data: Dict[str, float]) -> None:
        """Set revenue by period (YYYY-MM -> amount)."""
        self._revenue_data = data

    def set_targets(self, targets: Dict[str, float]) -> None:
        """Set revenue targets by period."""
        self._target_data = targets

    def set_rep_data(self, reps: List[Dict[str, Any]]) -> None:
        """Set rep-level data: [{rep, revenue, quota, placements}]."""
        self._rep_data = reps

    def set_program_revenue(self, data: Dict[str, float]) -> None:
        self._program_revenue = data

    def set_account_data(self, accounts: List[Dict[str, Any]]) -> None:
        self._account_data = accounts

    def set_pipeline_data(self, deals: List[Dict[str, Any]]) -> None:
        self._pipeline_data = deals

    def set_placement_metrics(self, active: int, new: int, avg_margin: float) -> None:
        self._placement_count = active
        self._new_placements = new
        self._avg_margin = avg_margin

    # -----------------------------------------
    # Quota attainment
    # -----------------------------------------

    def get_quota_attainment(self) -> List[QuotaAttainment]:
        """Calculate quota attainment per rep."""
        results = []
        for r in self._rep_data:
            revenue = r.get("revenue", 0)
            quota = r.get("quota", 0)
            pct = (revenue / quota * 100) if quota > 0 else 0
            results.append(QuotaAttainment(
                rep=r.get("rep", ""),
                revenue=revenue,
                quota=quota,
                attainment_pct=round(pct, 1),
                placements=r.get("placements", 0),
            ))
        results.sort(key=lambda r: r.attainment_pct, reverse=True)
        for i, r in enumerate(results):
            r.rank = i + 1
        return results

    # -----------------------------------------
    # Diversification score
    # -----------------------------------------

    def get_diversification_score(self) -> DiversificationScore:
        """Calculate customer/program diversification."""
        if not self._program_revenue:
            return DiversificationScore(score=100.0, assessment="balanced")

        total = sum(self._program_revenue.values())
        if total == 0:
            return DiversificationScore(score=100.0, assessment="balanced")

        n = len(self._program_revenue)
        shares = [v / total for v in self._program_revenue.values()]
        hhi = sum(s * s for s in shares)
        top_pct = max(shares) * 100

        # Score: 0 = fully concentrated, 100 = perfectly distributed
        min_hhi = 1.0 / n if n > 0 else 1.0
        score = ((1 - hhi) / (1 - min_hhi) * 100) if min_hhi < 1 else 0
        score = max(0, min(100, score))

        if score >= 75:
            assessment = "diversified"
        elif score >= 50:
            assessment = "balanced"
        elif score >= 25:
            assessment = "moderate"
        else:
            assessment = "concentrated"

        return DiversificationScore(
            score=round(score, 1),
            program_count=n,
            top_program_pct=round(top_pct, 1),
            assessment=assessment,
        )

    # -----------------------------------------
    # Period comparison
    # -----------------------------------------

    def get_period_comparison(
        self, current_period: str, prior_period: str,
    ) -> PeriodComparison:
        """Compare revenue between two periods."""
        current_rev = self._revenue_data.get(current_period, 0)
        prior_rev = self._revenue_data.get(prior_period, 0)

        change_abs = current_rev - prior_rev
        change_pct = (change_abs / prior_rev * 100) if prior_rev > 0 else 0

        if change_pct > 5:
            trend = "growing"
        elif change_pct < -5:
            trend = "declining"
        else:
            trend = "stable"

        return PeriodComparison(
            current_period=current_period,
            prior_period=prior_period,
            current_revenue=round(current_rev, 2),
            prior_revenue=round(prior_rev, 2),
            change_pct=round(change_pct, 2),
            change_absolute=round(change_abs, 2),
            trend=trend,
        )

    # -----------------------------------------
    # Weighted pipeline
    # -----------------------------------------

    def get_weighted_pipeline(self) -> Dict[str, Any]:
        """Calculate weighted pipeline value with confidence intervals."""
        if not self._pipeline_data:
            return {"weighted_value": 0, "deal_count": 0, "confidence_low": 0, "confidence_high": 0}

        stage_probs = {
            "discovery": 0.10, "qualification": 0.20, "requirements": 0.35,
            "submission": 0.50, "interview": 0.65, "offer": 0.80,
            "start": 0.95, "revenue": 1.0,
        }

        weighted = 0.0
        low = 0.0
        high = 0.0

        for deal in self._pipeline_data:
            value = deal.get("value", 0)
            stage = deal.get("stage", "discovery").lower()
            prob = stage_probs.get(stage, 0.1)

            weighted += value * prob
            low += value * max(0, prob - 0.15)
            high += value * min(1.0, prob + 0.15)

        return {
            "weighted_value": round(weighted, 2),
            "confidence_low": round(low, 2),
            "confidence_high": round(high, 2),
            "deal_count": len(self._pipeline_data),
        }

    # -----------------------------------------
    # Top accounts
    # -----------------------------------------

    def get_top_accounts(self, n: int = 10) -> List[Dict[str, Any]]:
        """Top accounts by revenue and growth potential."""
        if self._account_data:
            sorted_accounts = sorted(
                self._account_data, key=lambda a: a.get("revenue", 0), reverse=True
            )
            return sorted_accounts[:n]

        # Fall back to program revenue
        accounts = []
        for prog, rev in sorted(self._program_revenue.items(), key=lambda x: x[1], reverse=True)[:n]:
            accounts.append({
                "account": prog,
                "revenue": round(rev, 2),
                "growth_potential": "medium",
            })
        return accounts

    # -----------------------------------------
    # Executive summary
    # -----------------------------------------

    def generate_executive_summary(
        self,
        period: str = "",
        prior_period: str = "",
    ) -> ExecutiveSummary:
        """Generate automated executive summary."""
        if not period:
            now = datetime.now(timezone.utc)
            period = f"{now.year}-{now.month:02d}"

        # Revenue vs target
        total_rev = self._revenue_data.get(period, 0)
        target = self._target_data.get(period, 0)
        attainment = (total_rev / target * 100) if target > 0 else 0

        # Pipeline
        pipeline = self.get_weighted_pipeline()

        # Diversification
        diversification = self.get_diversification_score()

        # Rep attainment
        rep_attainment = self.get_quota_attainment()

        # Period comparison
        comparison = None
        if prior_period:
            comparison = self.get_period_comparison(period, prior_period)

        # Top accounts
        top_accounts = self.get_top_accounts(10)

        # Generate narrative
        narrative = _generate_narrative(
            period, total_rev, target, attainment,
            pipeline["weighted_value"],
            self._placement_count, self._new_placements,
            self._avg_margin, diversification, comparison,
        )

        summary = ExecutiveSummary(
            period=period,
            total_revenue=round(total_rev, 2),
            target_revenue=round(target, 2),
            attainment_pct=round(attainment, 1),
            weighted_pipeline=pipeline["weighted_value"],
            active_placements=self._placement_count,
            new_placements=self._new_placements,
            avg_margin_pct=round(self._avg_margin, 1),
            top_accounts=top_accounts,
            period_comparison=comparison,
            diversification=diversification,
            rep_attainment=rep_attainment,
            narrative=narrative,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(f"Generated executive summary for {period}: ${total_rev:,.0f} revenue ({attainment:.0f}% of target)")
        return summary


# =========================================
# NARRATIVE GENERATOR
# =========================================

def _generate_narrative(
    period: str,
    revenue: float,
    target: float,
    attainment: float,
    pipeline: float,
    active: int,
    new: int,
    margin: float,
    diversification: DiversificationScore,
    comparison: Optional[PeriodComparison],
) -> str:
    """Generate executive summary narrative."""
    parts = [f"Revenue for {period}: ${revenue:,.0f}"]

    if target > 0:
        if attainment >= 100:
            parts.append(f" ({attainment:.0f}% of ${target:,.0f} target — on track).")
        elif attainment >= 80:
            parts.append(f" ({attainment:.0f}% of ${target:,.0f} target — close to plan).")
        else:
            parts.append(f" ({attainment:.0f}% of ${target:,.0f} target — below plan).")
    else:
        parts.append(".")

    parts.append(f" Active placements: {active}")
    if new > 0:
        parts.append(f" ({new} new this period)")
    parts.append(f". Average margin: {margin:.1f}%.")

    if pipeline > 0:
        parts.append(f" Weighted pipeline: ${pipeline:,.0f}.")

    if comparison:
        if comparison.trend == "growing":
            parts.append(f" Revenue is up {comparison.change_pct:.1f}% vs prior period.")
        elif comparison.trend == "declining":
            parts.append(f" Revenue is down {abs(comparison.change_pct):.1f}% vs prior period.")

    if diversification.assessment == "concentrated":
        parts.append(f" Warning: revenue is concentrated (top program = {diversification.top_program_pct:.0f}%).")

    return "".join(parts)


# =========================================
# SINGLETON
# =========================================

_analytics: Optional[ExecutiveAnalytics] = None


def get_executive_analytics() -> ExecutiveAnalytics:
    global _analytics
    if _analytics is None:
        _analytics = ExecutiveAnalytics()
    return _analytics
