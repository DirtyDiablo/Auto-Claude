"""
Analytics Agent - Generates insights, trends, and forecasts from BD data.

Part of the 8-agent CrewAI system for BD Intelligence.
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import structlog

logger = structlog.get_logger(__name__)

# Import base agent
try:
    from .base_agent import BDAgent, AgentResponse
except ImportError:
    from base_agent import BDAgent, AgentResponse


@dataclass
class TrendInsight:
    """A trend or pattern identified in the data."""
    insight_type: str  # "trend", "anomaly", "pattern", "forecast"
    category: str  # "hiring", "programs", "locations", "clearances"
    title: str
    description: str
    confidence: float
    data_points: List[Dict]
    actionable: bool = True


@dataclass
class AnalyticsReport:
    """Comprehensive analytics report."""
    generated_at: datetime
    period: str  # "daily", "weekly", "monthly"
    insights: List[TrendInsight]
    key_metrics: Dict[str, Any]
    recommendations: List[str]
    summary: str


class AnalyticsAgent(BDAgent):
    """
    Agent that generates insights, trends, and forecasts from BD data.

    Responsibilities:
    - Analyze hiring trends
    - Identify program activity patterns
    - Track competitor movements
    - Generate weekly intelligence briefs
    - Surface actionable opportunities
    """

    def __init__(self):
        super().__init__(
            name="Analytics Agent",
            description="Surface actionable insights and trends from BD data. "
                       "Expert in hiring trends, program activity, and competitive intelligence."
        )

    def analyze_hiring_trends(self, jobs: List[Dict]) -> List[TrendInsight]:
        """Analyze job posting trends."""
        insights = []

        if not jobs:
            return insights

        # Count by company
        company_counts = Counter(j.get("company", "Unknown") for j in jobs)
        top_companies = company_counts.most_common(5)

        if top_companies:
            insights.append(TrendInsight(
                insight_type="trend",
                category="hiring",
                title="Top Hiring Companies",
                description=f"Top 5 hiring companies: {', '.join(f'{c[0]} ({c[1]})' for c in top_companies)}",
                confidence=0.9,
                data_points=[{"company": c[0], "count": c[1]} for c in top_companies],
                actionable=True,
            ))

        # Count by clearance
        clearance_counts = Counter(j.get("detected_clearance", "Unknown") for j in jobs)
        ts_sci_count = sum(c for cl, c in clearance_counts.items() if cl and "ts/sci" in cl.lower())

        if ts_sci_count > len(jobs) * 0.3:  # More than 30% TS/SCI
            insights.append(TrendInsight(
                insight_type="pattern",
                category="clearances",
                title="High TS/SCI Demand",
                description=f"{ts_sci_count} jobs ({ts_sci_count/len(jobs)*100:.0f}%) require TS/SCI clearance",
                confidence=0.95,
                data_points=[{"clearance": "TS/SCI", "count": ts_sci_count, "percentage": ts_sci_count/len(jobs)}],
                actionable=True,
            ))

        # Count by location
        location_counts = Counter(j.get("location", "Unknown") for j in jobs)
        top_locations = location_counts.most_common(5)

        if top_locations:
            insights.append(TrendInsight(
                insight_type="pattern",
                category="locations",
                title="Hot Job Locations",
                description=f"Most active locations: {', '.join(f'{l[0]} ({l[1]})' for l in top_locations if l[0] != 'Unknown')}",
                confidence=0.85,
                data_points=[{"location": l[0], "count": l[1]} for l in top_locations],
                actionable=True,
            ))

        return insights

    def analyze_program_activity(self, programs: List[Dict], jobs: List[Dict]) -> List[TrendInsight]:
        """Analyze program activity and job mappings."""
        insights = []

        if not jobs:
            return insights

        # Count jobs by mapped program
        program_counts = Counter(j.get("mapped_program", "Unmapped") for j in jobs)
        top_programs = [p for p in program_counts.most_common(10) if p[0] != "Unmapped"]

        if top_programs:
            insights.append(TrendInsight(
                insight_type="trend",
                category="programs",
                title="Active Programs by Job Volume",
                description=f"Programs with most job activity: {', '.join(f'{p[0]} ({p[1]})' for p in top_programs[:5])}",
                confidence=0.85,
                data_points=[{"program": p[0], "job_count": p[1]} for p in top_programs],
                actionable=True,
            ))

        # Identify programs with recompete indicators
        recompete_keywords = ["recompete", "follow-on", "successor", "transition"]
        recompete_programs = []

        for program in programs:
            program_name = program.get("program_name", "")
            keywords = program.get("keywords", [])
            if any(kw in str(keywords).lower() for kw in recompete_keywords):
                recompete_programs.append(program_name)

        if recompete_programs:
            insights.append(TrendInsight(
                insight_type="forecast",
                category="programs",
                title="Potential Recompete Opportunities",
                description=f"{len(recompete_programs)} programs show recompete indicators",
                confidence=0.7,
                data_points=[{"program": p} for p in recompete_programs[:10]],
                actionable=True,
            ))

        return insights

    def analyze_contacts_by_tier(self, contacts: List[Dict]) -> List[TrendInsight]:
        """Analyze contact distribution by tier."""
        insights = []

        if not contacts:
            return insights

        # Count by tier
        tier_counts = Counter(c.get("hierarchy_tier", "Unknown") for c in contacts)

        # High-value contacts (Tier 1-2)
        high_value = sum(c for t, c in tier_counts.items() if "Tier 1" in t or "Tier 2" in t)

        if high_value > 0:
            insights.append(TrendInsight(
                insight_type="pattern",
                category="contacts",
                title="Executive Contact Coverage",
                description=f"{high_value} executive-level contacts (Tier 1-2) in database",
                confidence=0.9,
                data_points=[{"tier": t, "count": c} for t, c in tier_counts.items()],
                actionable=True,
            ))

        # BD Priority distribution
        priority_counts = Counter(c.get("bd_priority", "Standard") for c in contacts)
        critical = priority_counts.get("Critical", 0)

        if critical > 0:
            insights.append(TrendInsight(
                insight_type="pattern",
                category="contacts",
                title="Critical BD Targets",
                description=f"{critical} contacts marked as Critical priority for BD outreach",
                confidence=0.95,
                data_points=[{"priority": p, "count": c} for p, c in priority_counts.items()],
                actionable=True,
            ))

        return insights

    def generate_report(
        self,
        jobs: List[Dict] = None,
        programs: List[Dict] = None,
        contacts: List[Dict] = None,
        period: str = "weekly",
    ) -> AnalyticsReport:
        """
        Generate comprehensive analytics report.

        Args:
            jobs: Job postings data
            programs: Federal programs data
            contacts: Contact data
            period: Report period

        Returns:
            AnalyticsReport with insights and recommendations
        """
        jobs = jobs or []
        programs = programs or []
        contacts = contacts or []

        all_insights = []

        # Run analyses
        all_insights.extend(self.analyze_hiring_trends(jobs))
        all_insights.extend(self.analyze_program_activity(programs, jobs))
        all_insights.extend(self.analyze_contacts_by_tier(contacts))

        # Key metrics
        key_metrics = {
            "total_jobs": len(jobs),
            "total_programs": len(programs),
            "total_contacts": len(contacts),
            "high_value_jobs": sum(1 for j in jobs if j.get("bd_score", 0) >= 80),
            "ts_sci_jobs": sum(1 for j in jobs if "ts/sci" in str(j.get("detected_clearance", "")).lower()),
            "critical_contacts": sum(1 for c in contacts if c.get("bd_priority") == "Critical"),
        }

        # Generate recommendations
        recommendations = []
        for insight in all_insights:
            if insight.actionable and insight.confidence >= 0.8:
                if insight.category == "hiring" and "Top Hiring" in insight.title:
                    recommendations.append(f"Focus on top-hiring companies for teaming opportunities")
                elif insight.category == "clearances":
                    recommendations.append(f"Build TS/SCI-cleared talent pipeline")
                elif insight.category == "programs" and "Recompete" in insight.title:
                    recommendations.append(f"Initiate capture planning for recompete programs")
                elif insight.category == "contacts" and "Critical" in insight.title:
                    recommendations.append(f"Schedule outreach to Critical priority contacts")

        # Summary
        summary = (
            f"{period.title()} BD Intelligence Summary: "
            f"{len(jobs)} jobs analyzed, {len(all_insights)} insights generated, "
            f"{len(recommendations)} actionable recommendations."
        )

        return AnalyticsReport(
            generated_at=datetime.utcnow(),
            period=period,
            insights=all_insights,
            key_metrics=key_metrics,
            recommendations=recommendations,
            summary=summary,
        )

    async def process(self, query: str, context: Optional[Dict] = None) -> AgentResponse:
        """Process an analytics request."""
        context = context or {}

        report = self.generate_report(
            jobs=context.get("jobs", []),
            programs=context.get("programs", []),
            contacts=context.get("contacts", []),
            period=context.get("period", "weekly"),
        )

        return AgentResponse(
            success=True,
            content=(
                f"{report.summary}\n\n"
                f"Key Metrics:\n"
                f"- Total Jobs: {report.key_metrics['total_jobs']}\n"
                f"- High-Value Jobs: {report.key_metrics['high_value_jobs']}\n"
                f"- TS/SCI Jobs: {report.key_metrics['ts_sci_jobs']}\n"
                f"- Total Contacts: {report.key_metrics['total_contacts']}\n"
                f"- Critical Contacts: {report.key_metrics['critical_contacts']}\n\n"
                f"Top Insights ({len(report.insights)}):\n" +
                "\n".join(f"- {i.title}: {i.description}" for i in report.insights[:5]) +
                f"\n\nRecommendations:\n" +
                "\n".join(f"- {r}" for r in report.recommendations)
            ),
            sources=[],
            confidence=0.85,
            agent_name=self.name,
            metadata={
                "report": {
                    "period": report.period,
                    "generated_at": report.generated_at.isoformat(),
                    "key_metrics": report.key_metrics,
                    "insights_count": len(report.insights),
                    "recommendations": report.recommendations,
                },
                "insights": [
                    {
                        "type": i.insight_type,
                        "category": i.category,
                        "title": i.title,
                        "confidence": i.confidence,
                    }
                    for i in report.insights
                ],
            },
        )


# CLI test
if __name__ == "__main__":
    import asyncio

    agent = AnalyticsAgent()

    # Test with sample data
    test_jobs = [
        {"title": "Network Engineer", "company": "GDIT", "detected_clearance": "TS/SCI", "bd_score": 85, "mapped_program": "AF DCGS"},
        {"title": "Systems Admin", "company": "GDIT", "detected_clearance": "Secret", "bd_score": 60, "mapped_program": "Army DCGS-A"},
        {"title": "Cyber Analyst", "company": "Leidos", "detected_clearance": "TS/SCI Poly", "bd_score": 90, "mapped_program": "AF DCGS"},
    ]

    test_contacts = [
        {"first_name": "John", "last_name": "Smith", "hierarchy_tier": "Tier 1 - Executive", "bd_priority": "Critical"},
        {"first_name": "Jane", "last_name": "Doe", "hierarchy_tier": "Tier 3 - Program Leadership", "bd_priority": "High"},
    ]

    async def test():
        result = await agent.process(
            "Generate analytics report",
            context={"jobs": test_jobs, "contacts": test_contacts, "period": "weekly"}
        )
        logger.info("analytics_report_generated", content=result.content)

    asyncio.run(test())
