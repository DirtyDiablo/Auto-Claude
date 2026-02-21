"""Brief template engine — builds structured intelligence briefs from pipeline data.

Sections:
1. New Opportunities — new jobs/contracts discovered this period
2. Scoring Changes — significant BD score movements
3. Pipeline Status — funnel metrics and velocity
4. Contact Activity — new contacts, engagement updates
5. Competitive Intelligence — competitor activity detected
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

try:
    import structlog

    logger = structlog.get_logger("BriefTemplateEngine")
except ImportError:
    logger = logging.getLogger("BriefTemplateEngine")


# ---------------------------------------------------------------------------
# Dataclass models (internal — not Pydantic)
# ---------------------------------------------------------------------------


@dataclass
class BriefSection:
    """A section of an intelligence brief."""

    title: str
    content: str
    data: Dict[str, Any]
    priority: str = "medium"  # "high", "medium", "low"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class IntelligenceBrief:
    """Complete weekly intelligence brief."""

    id: str
    title: str
    period_start: str  # ISO date YYYY-MM-DD
    period_end: str
    generated_at: str
    sections: List[BriefSection]
    executive_summary: str
    portfolio: str  # which portfolio this brief covers

    # ---- serialization helpers ----

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "generated_at": self.generated_at,
            "sections": [s.to_dict() for s in self.sections],
            "executive_summary": self.executive_summary,
            "portfolio": self.portfolio,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IntelligenceBrief":
        sections = [BriefSection(**s) for s in data.get("sections", [])]
        return cls(
            id=data["id"],
            title=data["title"],
            period_start=data["period_start"],
            period_end=data["period_end"],
            generated_at=data["generated_at"],
            sections=sections,
            executive_summary=data["executive_summary"],
            portfolio=data["portfolio"],
        )

    def to_html(self) -> str:
        """Render the brief as an HTML document."""
        section_html_parts = []
        for section in self.sections:
            priority_color = {
                "high": "#dc2626",
                "medium": "#d97706",
                "low": "#16a34a",
            }.get(section.priority, "#6b7280")

            section_html_parts.append(
                f'<div class="section">'
                f'<h2>{_esc(section.title)}'
                f' <span class="priority" style="color:{priority_color}">'
                f"[{section.priority.upper()}]</span></h2>"
                f"<p>{_esc(section.content)}</p>"
                f"</div>"
            )

        sections_block = "\n".join(section_html_parts)

        return (
            "<!DOCTYPE html>\n"
            "<html><head>"
            f"<title>{_esc(self.title)}</title>"
            '<meta charset="utf-8">'
            "<style>"
            "body{font-family:Arial,sans-serif;max-width:900px;margin:0 auto;padding:20px}"
            "h1{color:#1e3a5f;border-bottom:2px solid #1e3a5f;padding-bottom:10px}"
            ".meta{color:#6b7280;font-size:0.9em;margin-bottom:20px}"
            ".executive-summary{background:#f0f9ff;border-left:4px solid #1e3a5f;"
            "padding:15px;margin:20px 0}"
            ".section{margin:20px 0;padding:15px;border:1px solid #e5e7eb;border-radius:8px}"
            ".section h2{color:#1e3a5f;margin-top:0}"
            ".priority{font-size:0.75em;font-weight:normal}"
            "</style>"
            "</head><body>"
            f"<h1>{_esc(self.title)}</h1>"
            f'<div class="meta">'
            f"<strong>Portfolio:</strong> {_esc(self.portfolio)} | "
            f"<strong>Period:</strong> {self.period_start} to {self.period_end} | "
            f"<strong>Generated:</strong> {self.generated_at}"
            f"</div>"
            f'<div class="executive-summary">'
            f"<h2>Executive Summary</h2>"
            f"<p>{_esc(self.executive_summary)}</p>"
            f"</div>"
            f"{sections_block}"
            f"</body></html>"
        )

    def to_markdown(self) -> str:
        """Render the brief as Markdown."""
        lines = [
            f"# {self.title}",
            "",
            f"**Portfolio:** {self.portfolio}  ",
            f"**Period:** {self.period_start} to {self.period_end}  ",
            f"**Generated:** {self.generated_at}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            self.executive_summary,
            "",
            "---",
            "",
        ]

        for section in self.sections:
            lines.append(f"## {section.title} [{section.priority.upper()}]")
            lines.append("")
            lines.append(section.content)
            lines.append("")

        return "\n".join(lines)


def _esc(text: str) -> str:
    """Minimal HTML escaping."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ---------------------------------------------------------------------------
# Template Engine
# ---------------------------------------------------------------------------


class BriefTemplateEngine:
    """Generates intelligence briefs from pipeline data.

    Uses KPIService and portfolio data when available, falling back to
    synthetic/placeholder data for graceful degradation.
    """

    def __init__(self) -> None:
        self._kpi_service = None
        self._portfolio_registry = None
        self._init_services()

    def _init_services(self) -> None:
        """Best-effort initialization of dependent services."""
        try:
            from Engine8_Knowledge.services.kpi_service import KPIService

            self._kpi_service = KPIService()
            logger.info("brief_engine_kpi_available")
        except Exception as exc:
            logger.warning("brief_engine_kpi_unavailable", error=str(exc))

        try:
            from Engine8_Knowledge.portfolios.registry import get_portfolio_registry

            self._portfolio_registry = get_portfolio_registry()
            logger.info("brief_engine_portfolio_available")
        except Exception as exc:
            logger.warning("brief_engine_portfolio_unavailable", error=str(exc))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_brief(
        self,
        portfolio_id: str = "dcgs",
        period_days: int = 7,
    ) -> IntelligenceBrief:
        """Generate a complete intelligence brief for the given portfolio and period."""
        now = datetime.now(timezone.utc)
        period_end = now.strftime("%Y-%m-%d")
        period_start = (now - timedelta(days=period_days)).strftime("%Y-%m-%d")

        logger.info(
            "generating_brief",
            portfolio=portfolio_id,
            period_start=period_start,
            period_end=period_end,
        )

        # Gather KPI data for sections
        kpi_data = self._gather_kpi_data(period_start, period_end)

        sections: List[BriefSection] = [
            self._build_new_opportunities_section(kpi_data),
            self._build_scoring_changes_section(kpi_data),
            self._build_pipeline_status_section(kpi_data),
            self._build_contact_activity_section(kpi_data),
            self._build_competitive_intel_section(kpi_data),
        ]

        executive_summary = self._build_executive_summary(sections)

        portfolio_name = self._resolve_portfolio_name(portfolio_id)
        brief = IntelligenceBrief(
            id=str(uuid.uuid4()),
            title=f"Weekly Intelligence Brief - {portfolio_name}",
            period_start=period_start,
            period_end=period_end,
            generated_at=now.isoformat(),
            sections=sections,
            executive_summary=executive_summary,
            portfolio=portfolio_id,
        )

        logger.info(
            "brief_generated",
            brief_id=brief.id,
            section_count=len(brief.sections),
        )
        return brief

    # ------------------------------------------------------------------
    # KPI data gathering
    # ------------------------------------------------------------------

    def _gather_kpi_data(self, start: str, end: str) -> Dict[str, Any]:
        """Pull KPI metrics; returns synthetic data if service unavailable."""
        data: Dict[str, Any] = {}

        if self._kpi_service:
            try:
                data["pipeline"] = self._kpi_service.pipeline_velocity(start, end)
            except Exception:
                data["pipeline"] = None
            try:
                data["competitive"] = self._kpi_service.competitive_landscape()
            except Exception:
                data["competitive"] = None
            try:
                data["contacts"] = self._kpi_service.contact_engagement(start, end)
            except Exception:
                data["contacts"] = None
            try:
                data["scoring"] = self._kpi_service.scoring_distribution()
            except Exception:
                data["scoring"] = None
        else:
            data = self._synthetic_kpi_data()

        return data

    def _synthetic_kpi_data(self) -> Dict[str, Any]:
        """Fallback synthetic KPI data for when services are unavailable."""
        return {
            "pipeline": {
                "stages": {
                    "Scraped": 142,
                    "Mapped": 118,
                    "Scored": 97,
                    "Submitted": 43,
                    "Won": 12,
                },
                "total_processed": 412,
                "velocity_per_day": 58.86,
            },
            "competitive": {
                "competitors": [
                    {"company": "Leidos", "job_count": 45, "market_share": 0.28},
                    {"company": "Northrop Grumman", "job_count": 38, "market_share": 0.24},
                    {"company": "GDIT", "job_count": 32, "market_share": 0.20},
                    {"company": "Raytheon", "job_count": 22, "market_share": 0.14},
                ],
                "top_competitor": "Leidos",
            },
            "contacts": {
                "total_contacts": 7337,
                "tier_distribution": {
                    "Tier 1": 42,
                    "Tier 2": 156,
                    "Tier 3": 489,
                    "Tier 4": 1205,
                    "Tier 5": 2890,
                    "Tier 6": 2555,
                },
                "highest_engagement_tier": "Tier 1",
            },
            "scoring": {
                "distribution": {
                    "hot": {"count": 23, "min_score": 80},
                    "warm": {"count": 67, "min_score": 50},
                    "cold": {"count": 125, "min_score": 0},
                },
                "total_scored": 215,
                "hot_percentage": 10.7,
            },
        }

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_new_opportunities_section(self, data: Dict[str, Any]) -> BriefSection:
        pipeline = data.get("pipeline") or {}
        stages = pipeline.get("stages", {})
        scraped = stages.get("Scraped", 0)
        mapped = stages.get("Mapped", 0)

        content = (
            f"{scraped} new job postings were discovered this period. "
            f"Of these, {mapped} were successfully mapped to federal programs. "
            f"The discovery rate indicates {'strong' if scraped > 100 else 'moderate'} "
            f"market activity in the target portfolio."
        )

        return BriefSection(
            title="New Opportunities",
            content=content,
            data={"scraped": scraped, "mapped": mapped},
            priority="high" if scraped > 100 else "medium",
        )

    def _build_scoring_changes_section(self, data: Dict[str, Any]) -> BriefSection:
        scoring = data.get("scoring") or {}
        distribution = scoring.get("distribution", {})
        hot_count = distribution.get("hot", {}).get("count", 0)
        warm_count = distribution.get("warm", {}).get("count", 0)
        total = scoring.get("total_scored", 0)
        hot_pct = scoring.get("hot_percentage", 0)

        content = (
            f"{total} opportunities have been scored. "
            f"{hot_count} are rated HOT (score >= 80), "
            f"{warm_count} are WARM (score >= 50). "
            f"Hot opportunities represent {hot_pct:.1f}% of the pipeline."
        )

        return BriefSection(
            title="Scoring Changes",
            content=content,
            data={
                "hot_count": hot_count,
                "warm_count": warm_count,
                "total_scored": total,
                "hot_percentage": hot_pct,
            },
            priority="high" if hot_count > 20 else "medium",
        )

    def _build_pipeline_status_section(self, data: Dict[str, Any]) -> BriefSection:
        pipeline = data.get("pipeline") or {}
        stages = pipeline.get("stages", {})
        total = pipeline.get("total_processed", 0)
        velocity = pipeline.get("velocity_per_day", 0)

        stage_lines = ", ".join(f"{k}: {v}" for k, v in stages.items())
        content = (
            f"Pipeline processed {total} items this period at "
            f"{velocity:.1f} items/day. "
            f"Stage breakdown: {stage_lines}."
        )

        return BriefSection(
            title="Pipeline Status",
            content=content,
            data={"stages": stages, "total": total, "velocity": velocity},
            priority="medium",
        )

    def _build_contact_activity_section(self, data: Dict[str, Any]) -> BriefSection:
        contacts = data.get("contacts") or {}
        total = contacts.get("total_contacts", 0)
        tiers = contacts.get("tier_distribution", {})
        top_tier = contacts.get("highest_engagement_tier", "N/A")

        tier_summary = ", ".join(f"{k}: {v}" for k, v in tiers.items())
        content = (
            f"{total} contacts in the database. "
            f"Tier distribution: {tier_summary}. "
            f"Highest engagement tier: {top_tier}."
        )

        return BriefSection(
            title="Contact Activity",
            content=content,
            data={"total_contacts": total, "tier_distribution": tiers},
            priority="low",
        )

    def _build_competitive_intel_section(self, data: Dict[str, Any]) -> BriefSection:
        competitive = data.get("competitive") or {}
        competitors = competitive.get("competitors", [])
        top = competitive.get("top_competitor", "Unknown")

        if competitors:
            comp_lines = "; ".join(
                f"{c.get('company', '?')} ({c.get('job_count', 0)} postings, "
                f"{c.get('market_share', 0) * 100:.0f}% share)"
                for c in competitors[:5]
            )
            content = (
                f"Top competitor: {top}. "
                f"Competitor activity: {comp_lines}."
            )
        else:
            content = "No competitor activity data available this period."

        return BriefSection(
            title="Competitive Intelligence",
            content=content,
            data={"top_competitor": top, "competitor_count": len(competitors)},
            priority="high" if len(competitors) > 3 else "medium",
        )

    def _build_executive_summary(self, sections: List[BriefSection]) -> str:
        """Synthesize an executive summary from section data."""
        high_priority = [s for s in sections if s.priority == "high"]
        summaries = []

        for section in sections:
            # Pull key stat from each section's data
            d = section.data
            if section.title == "New Opportunities":
                summaries.append(f"{d.get('scraped', 0)} new opportunities discovered")
            elif section.title == "Scoring Changes":
                summaries.append(f"{d.get('hot_count', 0)} hot-scored opportunities")
            elif section.title == "Pipeline Status":
                summaries.append(f"{d.get('total', 0)} items processed in pipeline")
            elif section.title == "Contact Activity":
                summaries.append(f"{d.get('total_contacts', 0)} contacts tracked")
            elif section.title == "Competitive Intelligence":
                summaries.append(
                    f"{d.get('competitor_count', 0)} competitors monitored"
                )

        summary = ". ".join(summaries) + "."
        if high_priority:
            summary += (
                f" {len(high_priority)} section(s) flagged as high priority: "
                + ", ".join(s.title for s in high_priority)
                + "."
            )

        return summary

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_portfolio_name(self, portfolio_id: str) -> str:
        """Resolve a portfolio ID to its display name."""
        if self._portfolio_registry:
            try:
                portfolio = self._portfolio_registry.get_portfolio(portfolio_id)
                if portfolio:
                    return portfolio.get("name", portfolio_id.upper())
            except Exception:
                pass
        # Fallback names for known portfolios
        names = {
            "dcgs": "DCGS Portfolio",
            "cyber": "Cyber Operations",
            "c4isr": "C4ISR Programs",
            "space": "Space Systems",
        }
        return names.get(portfolio_id, portfolio_id.upper())
