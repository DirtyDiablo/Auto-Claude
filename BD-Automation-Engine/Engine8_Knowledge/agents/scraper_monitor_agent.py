"""
Scraper Monitor Agent - Monitors and analyzes job scrape results.

Part of the 8-agent CrewAI system for BD Intelligence.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import base agent
try:
    from .base_agent import BDAgent, AgentResponse
except ImportError:
    from base_agent import BDAgent, AgentResponse


@dataclass
class ScraperAlert:
    """Alert from scraper monitoring."""
    alert_type: str  # "new_jobs", "competitor_activity", "high_value", "anomaly"
    severity: str  # "critical", "high", "medium", "low"
    message: str
    data: Dict[str, Any]
    timestamp: datetime


@dataclass
class ScrapeAnalysis:
    """Analysis of a scrape run."""
    scraper_name: str
    total_jobs: int
    new_jobs: int
    high_value_jobs: int
    ts_sci_jobs: int
    competitor_signals: List[str]
    alerts: List[ScraperAlert]
    recommendations: List[str]


class ScraperMonitorAgent(BDAgent):
    """
    Agent that monitors job scraper results and identifies BD opportunities.

    Responsibilities:
    - Analyze new job postings for BD signals
    - Detect competitor hiring activity
    - Identify high-value opportunities
    - Generate alerts for significant events
    """

    # Competitor keywords to monitor
    COMPETITORS = [
        "leidos", "northrop", "booz allen", "peraton", "caci",
        "saic", "mantech", "raytheon", "l3harris", "parsons"
    ]

    # High-value clearance levels
    HIGH_CLEARANCES = ["ts/sci", "ts/sci poly", "top secret/sci", "polygraph"]

    # DCGS-related keywords
    DCGS_KEYWORDS = [
        "dcgs", "distributed ground", "dgs", "sensor data",
        "isr", "sigint", "geoint", "humint", "masint",
        "fusion", "exploitation", "dissemination"
    ]

    def __init__(self):
        super().__init__(
            name="Scraper Monitor Agent",
            description="Monitor job scraper results and identify high-value BD opportunities. "
                       "Expert in competitor analysis and opportunity detection."
        )
        self.recent_alerts: List[ScraperAlert] = []

    def detect_competitors(self, job: Dict) -> List[str]:
        """Detect competitor mentions in job posting."""
        competitors_found = []
        text = f"{job.get('title', '')} {job.get('company', '')} {job.get('description', '')}".lower()

        for competitor in self.COMPETITORS:
            if competitor in text:
                competitors_found.append(competitor)

        return competitors_found

    def is_high_value(self, job: Dict) -> tuple[bool, List[str]]:
        """Determine if job is high-value for BD."""
        signals = []

        # Check clearance
        clearance = str(job.get("detected_clearance", "")).lower()
        for high_clearance in self.HIGH_CLEARANCES:
            if high_clearance in clearance:
                signals.append(f"High clearance: {clearance}")
                break

        # Check for DCGS keywords
        text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        for keyword in self.DCGS_KEYWORDS:
            if keyword in text:
                signals.append(f"DCGS keyword: {keyword}")

        # Check BD score if available
        bd_score = job.get("bd_score", 0)
        if bd_score >= 80:
            signals.append(f"High BD score: {bd_score}")

        return len(signals) >= 2, signals

    def analyze_scrape_batch(
        self,
        jobs: List[Dict],
        scraper_name: str = "unknown",
        previous_job_ids: Optional[set] = None,
    ) -> ScrapeAnalysis:
        """
        Analyze a batch of scraped jobs.

        Args:
            jobs: List of scraped job dictionaries
            scraper_name: Name of the scraper
            previous_job_ids: Set of previously seen job IDs for new job detection

        Returns:
            ScrapeAnalysis with insights and alerts
        """
        previous_job_ids = previous_job_ids or set()
        alerts = []
        recommendations = []
        all_competitor_signals = []

        new_jobs = 0
        high_value_count = 0
        ts_sci_count = 0

        for job in jobs:
            job_id = job.get("id") or job.get("url", "")

            # Check if new
            if job_id not in previous_job_ids:
                new_jobs += 1

            # Check clearance level
            clearance = str(job.get("detected_clearance", "")).lower()
            if any(hc in clearance for hc in self.HIGH_CLEARANCES):
                ts_sci_count += 1

            # Check high value
            is_high, signals = self.is_high_value(job)
            if is_high:
                high_value_count += 1
                alerts.append(ScraperAlert(
                    alert_type="high_value",
                    severity="high",
                    message=f"High-value job detected: {job.get('title', 'Unknown')}",
                    data={"job": job, "signals": signals},
                    timestamp=datetime.utcnow(),
                ))

            # Check competitors
            competitors = self.detect_competitors(job)
            if competitors:
                all_competitor_signals.extend(competitors)
                alerts.append(ScraperAlert(
                    alert_type="competitor_activity",
                    severity="medium",
                    message=f"Competitor activity: {', '.join(competitors)}",
                    data={"job": job, "competitors": competitors},
                    timestamp=datetime.utcnow(),
                ))

        # Generate recommendations
        if high_value_count > 5:
            recommendations.append(f"Review {high_value_count} high-value opportunities immediately")
        if ts_sci_count > 10:
            recommendations.append(f"Heavy TS/SCI hiring ({ts_sci_count} jobs) - program expansion likely")
        if all_competitor_signals:
            from collections import Counter
            top_competitors = Counter(all_competitor_signals).most_common(3)
            recommendations.append(f"Top competitor activity: {', '.join(c[0] for c in top_competitors)}")

        # Create analysis result
        analysis = ScrapeAnalysis(
            scraper_name=scraper_name,
            total_jobs=len(jobs),
            new_jobs=new_jobs,
            high_value_jobs=high_value_count,
            ts_sci_jobs=ts_sci_count,
            competitor_signals=list(set(all_competitor_signals)),
            alerts=alerts,
            recommendations=recommendations,
        )

        logger.info(
            f"Scrape analysis complete: {len(jobs)} jobs, "
            f"{new_jobs} new, {high_value_count} high-value"
        )

        return analysis

    def get_recent_alerts(self, hours: int = 24) -> List[ScraperAlert]:
        """Get alerts from the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [a for a in self.recent_alerts if a.timestamp > cutoff]

    async def process(self, query: str, context: Optional[Dict] = None) -> AgentResponse:
        """Process a scraper monitoring request."""
        if context and "jobs" in context:
            scraper_name = context.get("scraper_name", "unknown")
            previous_ids = set(context.get("previous_job_ids", []))

            analysis = self.analyze_scrape_batch(
                jobs=context["jobs"],
                scraper_name=scraper_name,
                previous_job_ids=previous_ids,
            )

            # Store alerts
            self.recent_alerts.extend(analysis.alerts)

            return AgentResponse(
                success=True,
                content=(
                    f"Scrape Analysis for {scraper_name}:\n"
                    f"- Total jobs: {analysis.total_jobs}\n"
                    f"- New jobs: {analysis.new_jobs}\n"
                    f"- High-value: {analysis.high_value_jobs}\n"
                    f"- TS/SCI: {analysis.ts_sci_jobs}\n"
                    f"- Alerts: {len(analysis.alerts)}\n"
                    f"- Recommendations: {', '.join(analysis.recommendations)}"
                ),
                sources=[],
                confidence=0.9,
                agent_name=self.name,
                metadata={
                    "analysis": {
                        "total_jobs": analysis.total_jobs,
                        "new_jobs": analysis.new_jobs,
                        "high_value_jobs": analysis.high_value_jobs,
                        "ts_sci_jobs": analysis.ts_sci_jobs,
                        "competitor_signals": analysis.competitor_signals,
                        "recommendations": analysis.recommendations,
                    },
                    "alerts": [
                        {
                            "type": a.alert_type,
                            "severity": a.severity,
                            "message": a.message,
                        }
                        for a in analysis.alerts
                    ],
                },
            )

        return AgentResponse(
            success=True,
            content=f"Scraper monitor ready. Provide jobs to analyze: {query}",
            sources=[],
            confidence=1.0,
            agent_name=self.name,
            metadata={"status": "ready"},
        )


# CLI test
if __name__ == "__main__":
    import asyncio

    agent = ScraperMonitorAgent()

    # Test with sample jobs
    test_jobs = [
        {
            "title": "Senior Network Engineer - DCGS",
            "company": "GDIT",
            "detected_clearance": "TS/SCI",
            "bd_score": 85,
            "description": "Support DCGS-A fusion operations...",
        },
        {
            "title": "Systems Administrator",
            "company": "Leidos",
            "detected_clearance": "Secret",
            "bd_score": 60,
            "description": "IT support role...",
        },
    ]

    async def test():
        result = await agent.process(
            "Analyze recent scrape",
            context={"jobs": test_jobs, "scraper_name": "insight_global"}
        )
        print(result.content)

    asyncio.run(test())
