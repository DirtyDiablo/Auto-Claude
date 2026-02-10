"""Phase 32A — Composite Opportunity Scorer

Ranks all BD opportunities by a composite score (0-100) combining 6 dimensions:
  1. WIN_PROBABILITY (30%) — ML model prediction
  2. REVENUE_POTENTIAL (20%) — Estimated contract value × bill rate
  3. STRATEGIC_FIT (15%) — Alignment with PTS growth priorities
  4. RELATIONSHIP_STRENGTH (15%) — Existing contacts + graph proximity
  5. TIMING_URGENCY (10%) — Fiscal cycle + job age + POP deadlines
  6. COMPETITIVE_POSITION (10%) — PTS advantages vs known competitors
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.ml.win_probability import WinProbabilityModel, get_win_model

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class DimensionScore:
    name: str
    score: float  # 0-100
    weight: float
    weighted_score: float
    details: str = ""


@dataclass
class ScoredOpportunity:
    opportunity_id: str
    title: str
    company: str
    program: str
    composite_score: float  # 0-100
    rank: int = 0
    dimensions: List[DimensionScore] = field(default_factory=list)
    recommended_approach: str = ""
    win_probability: float = 0.0
    scored_at: str = ""


@dataclass
class PipelineReview:
    review_date: str
    top_opportunities: List[ScoredOpportunity]
    new_this_week: List[dict]
    at_risk: List[dict]
    stale: List[dict]
    win_loss_summary: dict
    focus_areas: List[str]
    total_pipeline_value: float = 0.0
    average_score: float = 0.0


# =========================================
# DIMENSION WEIGHTS
# =========================================

DIMENSION_WEIGHTS = {
    "win_probability": 0.30,
    "revenue_potential": 0.20,
    "strategic_fit": 0.15,
    "relationship_strength": 0.15,
    "timing_urgency": 0.10,
    "competitive_position": 0.10,
}

# PTS strategic growth priorities
PTS_PRIORITY_PROGRAMS = {
    "AF DCGS", "PACAF", "GBSD", "F-35", "Sentinel",
    "Navy ISR", "NGEN", "JADC2", "ABMS",
}
PTS_PRIORITY_CAPABILITIES = {
    "ISR", "SIGINT", "GEOINT", "C4ISR", "cyber", "data fusion",
    "mission systems", "DevSecOps", "cloud", "AI/ML",
}
PTS_PRIORITY_LOCATIONS = {
    "Langley", "San Diego", "Colorado Springs", "Fort Meade",
    "Hickam", "Beale", "Ramstein",
}


class OpportunityScorer:
    """Ranks all BD opportunities by composite score."""

    def __init__(
        self,
        win_model: Optional[WinProbabilityModel] = None,
        graph_client: Any = None,
        search_client: Any = None,
        memory_client: Any = None,
    ):
        self.win_model = win_model or get_win_model()
        self.graph = graph_client
        self.search = search_client
        self.memory = memory_client

    async def score_opportunity(self, opp: dict) -> ScoredOpportunity:
        """Score a single opportunity across 6 dimensions (0-100)."""
        dimensions = []

        # 1. Win Probability (30%)
        win_pred = await self.win_model.predict(opp)
        win_score = win_pred.win_probability * 100
        dimensions.append(DimensionScore(
            name="win_probability",
            score=round(win_score, 1),
            weight=DIMENSION_WEIGHTS["win_probability"],
            weighted_score=round(win_score * DIMENSION_WEIGHTS["win_probability"], 1),
            details=f"ML model: {win_pred.confidence} confidence",
        ))

        # 2. Revenue Potential (20%)
        rev_score = self._score_revenue(opp)
        dimensions.append(DimensionScore(
            name="revenue_potential",
            score=round(rev_score, 1),
            weight=DIMENSION_WEIGHTS["revenue_potential"],
            weighted_score=round(rev_score * DIMENSION_WEIGHTS["revenue_potential"], 1),
            details=self._revenue_details(opp),
        ))

        # 3. Strategic Fit (15%)
        strat_score = self._score_strategic_fit(opp)
        dimensions.append(DimensionScore(
            name="strategic_fit",
            score=round(strat_score, 1),
            weight=DIMENSION_WEIGHTS["strategic_fit"],
            weighted_score=round(strat_score * DIMENSION_WEIGHTS["strategic_fit"], 1),
            details=self._strategic_details(opp),
        ))

        # 4. Relationship Strength (15%)
        rel_score = self._score_relationship(opp)
        dimensions.append(DimensionScore(
            name="relationship_strength",
            score=round(rel_score, 1),
            weight=DIMENSION_WEIGHTS["relationship_strength"],
            weighted_score=round(rel_score * DIMENSION_WEIGHTS["relationship_strength"], 1),
            details=self._relationship_details(opp),
        ))

        # 5. Timing Urgency (10%)
        time_score = self._score_timing(opp)
        dimensions.append(DimensionScore(
            name="timing_urgency",
            score=round(time_score, 1),
            weight=DIMENSION_WEIGHTS["timing_urgency"],
            weighted_score=round(time_score * DIMENSION_WEIGHTS["timing_urgency"], 1),
            details=self._timing_details(opp),
        ))

        # 6. Competitive Position (10%)
        comp_score = self._score_competitive(opp)
        dimensions.append(DimensionScore(
            name="competitive_position",
            score=round(comp_score, 1),
            weight=DIMENSION_WEIGHTS["competitive_position"],
            weighted_score=round(comp_score * DIMENSION_WEIGHTS["competitive_position"], 1),
            details=self._competitive_details(opp),
        ))

        composite = sum(d.weighted_score for d in dimensions)
        approach = self._recommend_approach(composite, dimensions, opp)

        return ScoredOpportunity(
            opportunity_id=opp.get("id", "unknown"),
            title=opp.get("title", "Unknown"),
            company=opp.get("company", "Unknown"),
            program=opp.get("program", opp.get("mapped_program", "")),
            composite_score=round(composite, 1),
            dimensions=dimensions,
            recommended_approach=approach,
            win_probability=win_pred.win_probability,
            scored_at=datetime.now(timezone.utc).isoformat(),
        )

    async def rank_pipeline(self, opportunities: Optional[List[dict]] = None,
                            limit: int = 50) -> List[ScoredOpportunity]:
        """Rank all active opportunities."""
        if opportunities is None:
            opportunities = await self._fetch_active_opportunities()

        scored = []
        for opp in opportunities[:limit]:
            scored_opp = await self.score_opportunity(opp)
            scored.append(scored_opp)

        scored.sort(key=lambda x: x.composite_score, reverse=True)
        for i, opp in enumerate(scored):
            opp.rank = i + 1

        return scored

    async def weekly_pipeline_review(self,
                                     opportunities: Optional[List[dict]] = None) -> PipelineReview:
        """Automated weekly pipeline analysis."""
        if opportunities is None:
            opportunities = await self._fetch_active_opportunities()

        ranked = await self.rank_pipeline(opportunities)

        top_10 = ranked[:10]

        # Identify new opportunities (last 7 days)
        new_this_week = [
            {"id": opp.get("id"), "title": opp.get("title"),
             "days_open": opp.get("days_job_open", 0)}
            for opp in opportunities
            if opp.get("days_job_open", 999) <= 7
        ]

        # At-risk: high score but declining activity
        at_risk = [
            {"id": s.opportunity_id, "title": s.title, "score": s.composite_score,
             "reason": "No recent activity"}
            for s in ranked
            if s.composite_score > 50 and any(
                opp.get("id") == s.opportunity_id and opp.get("days_since_last_contact", 0) > 14
                for opp in opportunities
            )
        ]

        # Stale: no activity in 14+ days
        stale = [
            {"id": opp.get("id"), "title": opp.get("title"),
             "days_inactive": opp.get("days_since_last_contact", 0)}
            for opp in opportunities
            if opp.get("days_since_last_contact", 0) > 14
        ]

        # Focus areas
        focus = []
        if top_10:
            focus.append(f"Prioritize top {len(top_10)} opportunities (avg score: {sum(s.composite_score for s in top_10)/len(top_10):.0f})")
        if new_this_week:
            focus.append(f"Evaluate {len(new_this_week)} new opportunities this week")
        if stale:
            focus.append(f"Re-engage {len(stale)} stale opportunities or close them out")
        if at_risk:
            focus.append(f"Attention needed: {len(at_risk)} high-value opportunities at risk")

        total_value = sum(opp.get("estimated_value", 0) for opp in opportunities)
        avg_score = sum(s.composite_score for s in ranked) / len(ranked) if ranked else 0

        return PipelineReview(
            review_date=datetime.now(timezone.utc).isoformat(),
            top_opportunities=top_10,
            new_this_week=new_this_week,
            at_risk=at_risk,
            stale=stale,
            win_loss_summary={"total": len(opportunities), "scored": len(ranked)},
            focus_areas=focus,
            total_pipeline_value=total_value,
            average_score=round(avg_score, 1),
        )

    async def what_if_analysis(self, opportunity: dict, changes: dict) -> dict:
        """What-if scenario analysis: how does score change with hypothetical changes."""
        # Score original
        original = await self.score_opportunity(opportunity)

        # Apply changes
        modified = dict(opportunity)
        modified.update(changes)

        # Score modified
        modified_scored = await self.score_opportunity(modified)

        delta = modified_scored.composite_score - original.composite_score

        dimension_changes = []
        for orig_dim, mod_dim in zip(original.dimensions, modified_scored.dimensions):
            dimension_changes.append({
                "dimension": orig_dim.name,
                "original": orig_dim.score,
                "modified": mod_dim.score,
                "delta": round(mod_dim.score - orig_dim.score, 1),
            })

        return {
            "original_score": original.composite_score,
            "modified_score": modified_scored.composite_score,
            "score_delta": round(delta, 1),
            "changes_applied": changes,
            "dimension_changes": dimension_changes,
            "impact": "positive" if delta > 0 else "negative" if delta < 0 else "neutral",
            "recommendation": modified_scored.recommended_approach,
        }

    # =========================================
    # DIMENSION SCORING
    # =========================================

    def _score_revenue(self, opp: dict) -> float:
        """Score revenue potential (0-100)."""
        value = opp.get("estimated_value", opp.get("program_value", 0))
        try:
            value = float(value)
        except (ValueError, TypeError):
            return 20.0

        if value <= 0:
            return 20.0
        # Log-scale: $100K = ~30, $1M = ~50, $10M = ~70, $100M = ~90
        log_val = math.log10(max(value, 1))
        score = min(100, max(0, (log_val - 4) * 25 + 30))
        return score

    def _score_strategic_fit(self, opp: dict) -> float:
        """Score alignment with PTS strategic priorities (0-100)."""
        score = 30.0  # baseline

        program = str(opp.get("program", opp.get("mapped_program", "")))
        if any(p in program for p in PTS_PRIORITY_PROGRAMS):
            score += 30

        desc = str(opp.get("description", opp.get("title", "")))
        cap_matches = sum(1 for c in PTS_PRIORITY_CAPABILITIES if c.lower() in desc.lower())
        score += min(cap_matches * 8, 24)

        location = str(opp.get("location", ""))
        if any(loc.lower() in location.lower() for loc in PTS_PRIORITY_LOCATIONS):
            score += 16

        return min(100, score)

    def _score_relationship(self, opp: dict) -> float:
        """Score existing relationship strength (0-100)."""
        score = 10.0

        tier = opp.get("contact_tier", 6)
        score += max(0, (7 - tier) * 10)  # Tier 1 = +60, Tier 6 = +10

        depth = opp.get("relationship_depth", 0)
        score += min(depth * 3, 15)

        mutual = opp.get("mutual_connections", 0)
        score += min(mutual * 3, 15)

        return min(100, score)

    def _score_timing(self, opp: dict) -> float:
        """Score timing urgency (0-100)."""
        score = 30.0

        fq = opp.get("fiscal_quarter", 1)
        score += {4: 25, 3: 15, 2: 5, 1: 0}.get(fq, 0)

        days_open = opp.get("days_job_open", 0)
        if days_open > 60:
            score += 20  # urgent
        elif days_open > 30:
            score += 10

        days_pop = opp.get("days_to_pop_end", 999)
        if days_pop < 90:
            score += 15
        elif days_pop < 180:
            score += 8

        if opp.get("is_option_year"):
            score += 10

        return min(100, score)

    def _score_competitive(self, opp: dict) -> float:
        """Score competitive position (0-100)."""
        score = 50.0  # neutral baseline

        involvement = opp.get("pts_involvement", 0)
        score += {3: 25, 2: 15, 1: 5}.get(involvement, 0)

        competitors = opp.get("competitor_density", 0)
        score -= min(competitors * 5, 25)

        if opp.get("past_placements_on_program", 0) > 0:
            score += 15

        if opp.get("clearance_match"):
            score += 10

        return max(0, min(100, score))

    # =========================================
    # DETAIL GENERATORS
    # =========================================

    def _revenue_details(self, opp: dict) -> str:
        value = opp.get("estimated_value", 0)
        if value >= 1_000_000:
            return f"${value/1_000_000:.1f}M estimated value"
        if value > 0:
            return f"${value:,.0f} estimated value"
        return "Value unknown"

    def _strategic_details(self, opp: dict) -> str:
        program = opp.get("program", opp.get("mapped_program", ""))
        if any(p in program for p in PTS_PRIORITY_PROGRAMS):
            return f"Priority program: {program}"
        return "Standard alignment"

    def _relationship_details(self, opp: dict) -> str:
        tier = opp.get("contact_tier", 0)
        depth = opp.get("relationship_depth", 0)
        if tier <= 2:
            return f"Tier {tier} contact, {depth} interactions"
        return f"Tier {tier}, limited relationship ({depth} interactions)"

    def _timing_details(self, opp: dict) -> str:
        fq = opp.get("fiscal_quarter", 0)
        days_open = opp.get("days_job_open", 0)
        parts = []
        if fq:
            parts.append(f"Q{fq}")
        if days_open > 0:
            parts.append(f"open {days_open} days")
        return ", ".join(parts) if parts else "No timing data"

    def _competitive_details(self, opp: dict) -> str:
        inv = opp.get("pts_involvement", 0)
        comp = opp.get("competitor_density", 0)
        labels = {3: "Current incumbent", 2: "Past performer", 1: "Target", 0: "No history"}
        return f"{labels.get(inv, 'Unknown')}, {comp} competitors"

    def _recommend_approach(self, score: float,
                            dimensions: List[DimensionScore], opp: dict) -> str:
        """Generate recommended approach based on overall score profile."""
        if score >= 75:
            return "Full pursuit: assign BD lead, submit candidates immediately, executive outreach"
        if score >= 55:
            return "Active pursuit: multi-channel outreach, prepare candidate shortlist"
        if score >= 35:
            return "Develop: build relationship, gather intelligence, monitor for trigger events"
        return "Monitor: low priority, track passively for changes"

    async def _fetch_active_opportunities(self) -> List[dict]:
        """Fetch active opportunities from search/graph services."""
        if self.search and hasattr(self.search, "get_active_opportunities"):
            return await self.search.get_active_opportunities()
        return []


# =========================================
# SINGLETON
# =========================================

_scorer: Optional[OpportunityScorer] = None


def get_opportunity_scorer() -> OpportunityScorer:
    global _scorer
    if _scorer is None:
        _scorer = OpportunityScorer()
    return _scorer
