"""Phase 44A — Insight Compiler.

Compiles raw patterns and meta-learning insights into executive-ready
briefings: weekly briefs, monthly assessments, flash reports, and
campaign effectiveness reviews.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.intelligence.meta_learner import MetaLearningEngine, get_meta_learner
from src.intelligence.pattern_engine import (
    StrategicPatternEngine,
    StrategicPattern,
    get_pattern_engine,
)


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class BriefSection:
    heading: str = ""
    content: str = ""
    priority: str = "medium"  # low | medium | high | critical
    data_points: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WeeklyBrief:
    id: str = ""
    title: str = ""
    period_start: str = ""
    period_end: str = ""
    executive_summary: str = ""
    sections: List[BriefSection] = field(default_factory=list)
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    top_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"weekly_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class MonthlyAssessment:
    id: str = ""
    title: str = ""
    period: str = ""
    executive_summary: str = ""
    sections: List[BriefSection] = field(default_factory=list)
    trend_analysis: Dict[str, Any] = field(default_factory=dict)
    strategic_recommendations: List[str] = field(default_factory=list)
    risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"monthly_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class FlashReport:
    id: str = ""
    title: str = ""
    pattern_id: str = ""
    urgency: str = "high"
    summary: str = ""
    impact_assessment: str = ""
    recommended_response: List[str] = field(default_factory=list)
    time_sensitivity: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"flash_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class CampaignReview:
    id: str = ""
    campaign_id: str = ""
    title: str = ""
    period: str = ""
    summary: str = ""
    effectiveness_score: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    what_worked: List[str] = field(default_factory=list)
    what_didnt: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"review_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


# =========================================
# INSIGHT COMPILER
# =========================================

class InsightCompiler:
    """Compiles raw patterns and insights into executive-ready briefings."""

    def __init__(
        self,
        meta_learner: Optional[MetaLearningEngine] = None,
        pattern_engine: Optional[StrategicPatternEngine] = None,
    ) -> None:
        self._learner = meta_learner or get_meta_learner()
        self._patterns = pattern_engine or get_pattern_engine()
        self._briefs: List[WeeklyBrief] = []
        self._assessments: List[MonthlyAssessment] = []
        self._flash_reports: List[FlashReport] = []
        self._campaign_reviews: List[CampaignReview] = []

    # --------------------------------------------------
    # WEEKLY BRIEF
    # --------------------------------------------------

    def compile_weekly_brief(self) -> WeeklyBrief:
        """Generate a weekly executive intelligence brief."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        # Gather data
        insights = self._learner.get_insights()
        active_patterns = self._patterns.get_active_patterns()
        opportunities = self._patterns.get_opportunities(min_score=40)
        outreach = self._learner.get_outreach_effectiveness()

        # Build sections
        sections: List[BriefSection] = []

        # --- Top Opportunities ---
        if opportunities:
            opp_lines = []
            for opp in opportunities[:5]:
                opp_lines.append(
                    f"- [{opp['urgency'].upper()}] {opp['title']} "
                    f"(Score: {opp['score']}, Win Prob: {opp['win_probability']:.0%})"
                )
            sections.append(BriefSection(
                heading="Top BD Opportunities",
                content="\n".join(opp_lines),
                priority="high",
                data_points=opportunities[:5],
            ))

        # --- Pattern Alerts ---
        if active_patterns:
            pat_lines = []
            for p in active_patterns[:5]:
                pat_lines.append(f"- [{p.pattern_type}] {p.title}: {p.description}")
            sections.append(BriefSection(
                heading="Strategic Patterns Detected",
                content="\n".join(pat_lines),
                priority="high",
                data_points=[{"id": p.id, "type": p.pattern_type, "title": p.title}
                             for p in active_patterns[:5]],
            ))

        # --- Outreach Performance ---
        sections.append(BriefSection(
            heading="Outreach Performance",
            content=(
                f"Overall response rate: {outreach['overall_rate']:.0%} "
                f"({outreach['total_responses']}/{outreach['total_attempts']} responses)"
            ),
            priority="medium",
            data_points=[outreach],
        ))

        # --- Competitive Landscape ---
        comp_insights = [i for i in insights if i.domain == "competitive"]
        if comp_insights:
            comp_lines = [f"- {i.title}: {i.description}" for i in comp_insights[:3]]
            sections.append(BriefSection(
                heading="Competitive Intelligence",
                content="\n".join(comp_lines),
                priority="medium",
            ))

        # Executive summary
        n_opp = len(opportunities)
        n_pat = len(active_patterns)
        high_opps = [o for o in opportunities if o.get("urgency") in ("high", "urgent")]
        exec_summary = (
            f"This week: {n_pat} strategic patterns detected, "
            f"{n_opp} BD opportunities identified "
            f"({len(high_opps)} high/urgent priority). "
            f"Outreach response rate: {outreach['overall_rate']:.0%}."
        )

        # Action items
        action_items: List[str] = []
        for opp in opportunities[:3]:
            for action in opp.get("actions", [])[:1]:
                action_items.append(action)

        brief = WeeklyBrief(
            title=f"Weekly Intelligence Brief — {now.strftime('%B %d, %Y')}",
            period_start=week_ago.strftime("%Y-%m-%d"),
            period_end=now.strftime("%Y-%m-%d"),
            executive_summary=exec_summary,
            sections=sections,
            key_metrics={
                "patterns_detected": n_pat,
                "opportunities": n_opp,
                "high_priority_opportunities": len(high_opps),
                "outreach_response_rate": outreach["overall_rate"],
            },
            top_opportunities=opportunities[:5],
            action_items=action_items,
        )
        self._briefs.append(brief)
        return brief

    # --------------------------------------------------
    # MONTHLY ASSESSMENT
    # --------------------------------------------------

    def compile_monthly_assessment(self) -> MonthlyAssessment:
        """Generate a monthly strategic assessment."""
        now = datetime.utcnow()

        insights = self._learner.get_insights()
        patterns = self._patterns.get_active_patterns()
        opportunities = self._patterns.get_opportunities()
        competitive = self._learner.get_competitive_trends()
        stats = self._learner.get_stats()

        sections: List[BriefSection] = []

        # --- Program Trends ---
        prog_insights = [i for i in insights if i.domain == "program"]
        if prog_insights:
            prog_lines = [f"- {i.title}: {i.description}" for i in prog_insights]
            sections.append(BriefSection(
                heading="Program Trends",
                content="\n".join(prog_lines),
                priority="high",
            ))

        # --- Contact Intelligence ---
        contact_insights = [i for i in insights if i.domain == "contact"]
        if contact_insights:
            contact_lines = [f"- {i.title}: {i.description}" for i in contact_insights]
            sections.append(BriefSection(
                heading="Contact Intelligence",
                content="\n".join(contact_lines),
                priority="medium",
            ))

        # --- Data Quality Health ---
        dq_insights = [i for i in insights if i.domain == "data_quality"]
        if dq_insights:
            dq_lines = [f"- {i.title}: {i.description}" for i in dq_insights]
            sections.append(BriefSection(
                heading="Data Quality Health",
                content="\n".join(dq_lines),
                priority="medium",
            ))

        # --- Competitive Landscape ---
        comp_data = competitive.get("competitors", {})
        if comp_data:
            comp_lines = []
            for comp, data in comp_data.items():
                comp_lines.append(f"- {comp}: {data['total_postings']} total postings")
            sections.append(BriefSection(
                heading="Competitive Landscape",
                content="\n".join(comp_lines),
                priority="high",
            ))

        # Trend analysis
        trend_analysis = {
            "growing_programs": [
                i.title for i in prog_insights
                if hasattr(i, "trend") and getattr(i, "trend", "") == "growing"
            ],
            "shrinking_programs": [
                i.title for i in prog_insights
                if hasattr(i, "trend") and getattr(i, "trend", "") == "shrinking"
            ],
            "total_insights": stats["total_insights"],
            "total_patterns": len(patterns),
        }

        # Strategic recommendations
        recommendations: List[str] = []
        for opp in opportunities[:3]:
            for action in opp.get("actions", [])[:1]:
                recommendations.append(action)
        if not recommendations:
            recommendations.append("Continue monitoring all intelligence streams")

        # Risk factors
        risk_factors: List[Dict[str, Any]] = []
        critical_insights = [i for i in insights if i.severity == "critical"]
        for ci in critical_insights:
            risk_factors.append({
                "risk": ci.title,
                "description": ci.description,
                "severity": ci.severity,
            })

        exec_summary = (
            f"Monthly assessment: {stats['total_insights']} insights generated, "
            f"{len(patterns)} active patterns, "
            f"{len(opportunities)} BD opportunities in pipeline. "
            f"{len(risk_factors)} critical risks identified."
        )

        assessment = MonthlyAssessment(
            title=f"Monthly Strategic Assessment — {now.strftime('%B %Y')}",
            period=now.strftime("%Y-%m"),
            executive_summary=exec_summary,
            sections=sections,
            trend_analysis=trend_analysis,
            strategic_recommendations=recommendations,
            risk_factors=risk_factors,
        )
        self._assessments.append(assessment)
        return assessment

    # --------------------------------------------------
    # FLASH REPORT
    # --------------------------------------------------

    def compile_flash_report(self, pattern: StrategicPattern) -> FlashReport:
        """Generate a flash report for a critical pattern."""
        # Score the pattern
        score = self._patterns.score_opportunity(pattern)

        # Determine time sensitivity
        if score.urgency == "urgent":
            time_sensitivity = "Immediate action required (24-48 hours)"
        elif score.urgency == "high":
            time_sensitivity = "Action needed within 1 week"
        else:
            time_sensitivity = "Monitor and respond within 2 weeks"

        # Impact assessment
        impact_lines = [
            f"Pattern: {pattern.pattern_type} affecting {pattern.program}",
            f"Opportunity Score: {score.score}/100",
            f"Win Probability: {score.win_probability:.0%}",
            f"Confidence: {pattern.confidence:.0%}",
        ]

        report = FlashReport(
            title=f"FLASH: {pattern.title}",
            pattern_id=pattern.id,
            urgency=score.urgency,
            summary=pattern.description,
            impact_assessment="\n".join(impact_lines),
            recommended_response=score.recommended_actions,
            time_sensitivity=time_sensitivity,
        )
        self._flash_reports.append(report)
        return report

    # --------------------------------------------------
    # CAMPAIGN REVIEW
    # --------------------------------------------------

    def compile_campaign_review(self, campaign_id: str = "") -> CampaignReview:
        """Generate a campaign effectiveness review."""
        campaigns = self._learner.get_campaign_effectiveness()
        outreach = self._learner.get_outreach_effectiveness()

        # Find specific campaign or summarize all
        campaign_data = None
        if campaign_id:
            for c in campaigns.get("campaigns", []):
                if c["id"] == campaign_id:
                    campaign_data = c
                    break

        if campaign_data:
            rate = campaign_data["response_rate"]
            title = f"Campaign Review: {campaign_data['channel'].title()}"
        else:
            rate = outreach["overall_rate"]
            title = "Overall Campaign Effectiveness Review"
            campaign_data = {
                "channel": "all",
                "total_sent": outreach["total_attempts"],
                "total_responded": outreach["total_responses"],
                "response_rate": rate,
            }

        # Determine what worked / didn't
        what_worked: List[str] = []
        what_didnt: List[str] = []

        channels = outreach.get("channels", {})
        for ch, data in channels.items():
            ch_rate = data.get("response_rate", 0)
            if ch_rate >= 0.5:
                what_worked.append(f"{ch.title()} channel: {ch_rate:.0%} response rate")
            elif ch_rate < 0.3:
                what_didnt.append(f"{ch.title()} channel: only {ch_rate:.0%} response rate")

        # Effectiveness score (normalize response rate to 0-100)
        effectiveness = round(rate * 100, 1)

        # Recommendations
        recommendations: List[str] = []
        if rate < 0.5:
            recommendations.append("Increase personalization in outreach messages")
            recommendations.append("Test different timing windows")
        if rate >= 0.5:
            recommendations.append("Scale up current approach")
            recommendations.append("Document and replicate successful patterns")

        review = CampaignReview(
            campaign_id=campaign_id or "all",
            title=title,
            period=f"{datetime.utcnow().strftime('%Y-%m')}",
            summary=(
                f"Campaign achieved {rate:.0%} response rate across "
                f"{campaign_data['total_sent']} outreach attempts"
            ),
            effectiveness_score=effectiveness,
            metrics=campaign_data,
            what_worked=what_worked,
            what_didnt=what_didnt,
            recommendations=recommendations,
        )
        self._campaign_reviews.append(review)
        return review

    # --------------------------------------------------
    # QUERIES
    # --------------------------------------------------

    def get_briefs(self) -> List[WeeklyBrief]:
        return list(self._briefs)

    def get_assessments(self) -> List[MonthlyAssessment]:
        return list(self._assessments)

    def get_flash_reports(self) -> List[FlashReport]:
        return list(self._flash_reports)

    def get_campaign_reviews(self) -> List[CampaignReview]:
        return list(self._campaign_reviews)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "weekly_briefs": len(self._briefs),
            "monthly_assessments": len(self._assessments),
            "flash_reports": len(self._flash_reports),
            "campaign_reviews": len(self._campaign_reviews),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[InsightCompiler] = None


def get_insight_compiler() -> InsightCompiler:
    global _instance
    if _instance is None:
        _instance = InsightCompiler()
    return _instance
