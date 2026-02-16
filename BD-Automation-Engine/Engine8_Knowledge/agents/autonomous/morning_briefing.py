"""
Morning Briefing Agent — Generates daily BD intelligence reports.

Pulls from hiring signals, pipeline status, due sequences, new jobs,
contract changes, and priority contacts to produce an executive morning brief.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "data"
BRIEFINGS_DIR = DATA_DIR / "briefings"


# ─── Data Models ─────────────────────────────────────────────────────────────


@dataclass
class DailyBrief:
    """Complete daily intelligence briefing."""

    date: str
    generated_at: str
    executive_summary: str = ""
    hiring_signals: List[Dict[str, Any]] = field(default_factory=list)
    pipeline_snapshot: Dict[str, Any] = field(default_factory=dict)
    due_actions: List[Dict[str, Any]] = field(default_factory=list)
    new_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    contract_updates: List[Dict[str, Any]] = field(default_factory=list)
    priority_contacts: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── Morning Briefing Agent ─────────────────────────────────────────────────


class MorningBriefingAgent:
    """
    Autonomous agent that generates daily BD intelligence reports.

    Gathers data from multiple internal APIs and services, then synthesizes
    an executive-ready morning briefing with actionable insights.
    """

    def __init__(self, api_base: str = "http://localhost:8100"):
        self.api_base = api_base
        BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)

    def generate_brief(self) -> DailyBrief:
        """
        Generate a complete daily intelligence briefing.

        Pulls from all available data sources and compiles the report.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"Generating morning briefing for {today}...")

        brief = DailyBrief(
            date=today,
            generated_at=datetime.now().isoformat(),
        )

        # Gather data from all sources
        brief.hiring_signals = self._fetch_hiring_signals()
        brief.pipeline_snapshot = self._fetch_pipeline_snapshot()
        brief.due_actions = self._fetch_due_actions()
        brief.new_opportunities = self._fetch_new_opportunities()
        brief.contract_updates = self._fetch_contract_updates()
        brief.priority_contacts = self._fetch_priority_contacts()

        # Generate executive summary
        brief.executive_summary = self._generate_executive_summary(brief)

        # Persist
        self._save_brief(brief)

        # Send to Slack if configured
        self._send_to_slack(brief)

        logger.info(
            f"Morning briefing generated: {len(brief.hiring_signals)} signals, "
            f"{len(brief.new_opportunities)} opportunities, "
            f"{len(brief.priority_contacts)} priority contacts"
        )

        return brief

    # ─── Data Source Fetchers ────────────────────────────────────────────

    def _fetch_hiring_signals(self) -> List[Dict]:
        """Fetch active hiring signals from ML model (Phase 13A)."""
        try:
            import httpx

            resp = httpx.get(
                f"{self.api_base}/ml/hiring-signals?refresh=true", timeout=10.0
            )
            if resp.status_code == 200:
                return resp.json().get("signals", [])
        except Exception as e:
            logger.warning(f"Could not fetch hiring signals: {e}")
        return []

    def _fetch_pipeline_snapshot(self) -> Dict:
        """Aggregate pipeline status from graph stats and collections."""
        snapshot = {
            "total_programs": 0,
            "total_contacts": 0,
            "total_jobs": 0,
            "graph_entities": 0,
            "graph_relationships": 0,
        }
        try:
            import httpx

            # Get collection stats
            resp = httpx.get(f"{self.api_base}/stats", timeout=10.0)
            if resp.status_code == 200:
                stats = resp.json()
                collections = stats.get("collections", {})
                snapshot["total_programs"] = collections.get("programs", {}).get(
                    "count", 0
                )
                snapshot["total_contacts"] = collections.get("contacts", {}).get(
                    "count", 0
                )
                snapshot["total_jobs"] = collections.get("jobs", {}).get("count", 0)

            # Get graph stats
            resp = httpx.get(f"{self.api_base}/bdgraph/stats", timeout=10.0)
            if resp.status_code == 200:
                graph = resp.json()
                snapshot["graph_entities"] = graph.get("total_entities", 0)
                snapshot["graph_relationships"] = graph.get("total_relationships", 0)
        except Exception as e:
            logger.warning(f"Could not fetch pipeline snapshot: {e}")

        return snapshot

    def _fetch_due_actions(self) -> List[Dict]:
        """Check for outreach sequences needing advancement today."""
        actions = []
        try:
            import httpx

            resp = httpx.get(
                f"{self.api_base}/integrations/crm/log?limit=20", timeout=10.0
            )
            if resp.status_code == 200:
                log = resp.json().get("log", [])
                today = datetime.now().strftime("%Y-%m-%d")
                for entry in log:
                    if entry.get("timestamp", "").startswith(today):
                        actions.append(
                            {
                                "action": entry.get("action", ""),
                                "timestamp": entry.get("timestamp", ""),
                                "details": {
                                    k: v
                                    for k, v in entry.items()
                                    if k not in ("timestamp", "action")
                                },
                            }
                        )
        except Exception as e:
            logger.warning(f"Could not fetch due actions: {e}")
        return actions

    def _fetch_new_opportunities(self) -> List[Dict]:
        """Check Qdrant jobs collection for documents indexed in last 24h."""
        opportunities = []
        try:
            import httpx

            resp = httpx.get(
                f"{self.api_base}/api/v2/jobs",
                params={"limit": 50},
                timeout=10.0,
            )
            if resp.status_code == 200:
                jobs = resp.json().get("jobs", [])
                cutoff = (datetime.now() - timedelta(days=1)).isoformat()
                for job in jobs:
                    scraped = job.get("scraped_at") or job.get("created_at", "")
                    if scraped >= cutoff:
                        opportunities.append(
                            {
                                "title": job.get("title", ""),
                                "program": job.get("program", ""),
                                "company": job.get("company", ""),
                                "location": job.get("location", ""),
                                "clearance": job.get("clearance", ""),
                                "bd_priority": job.get("bd_priority"),
                                "scraped_at": scraped,
                            }
                        )
        except Exception as e:
            logger.warning(f"Could not fetch new opportunities: {e}")
        return opportunities

    def _fetch_contract_updates(self) -> List[Dict]:
        """Check for contract modifications, expirations, awards."""
        updates = []
        try:
            import httpx

            # Try competitive intel endpoint
            resp = httpx.get(f"{self.api_base}/competitive/summary", timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                if "recent_awards" in data:
                    for award in data["recent_awards"][:5]:
                        updates.append({"type": "award", **award})
        except Exception:
            pass

        try:
            import httpx

            resp = httpx.get(f"{self.api_base}/contracts/expiring", timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                for contract in data.get("contracts", [])[:5]:
                    updates.append({"type": "expiring", **contract})
        except Exception:
            pass

        return updates

    def _fetch_priority_contacts(self) -> List[Dict]:
        """Get contacts with highest response probability not recently reached."""
        contacts = []
        try:
            import httpx

            resp = httpx.get(
                f"{self.api_base}/api/v2/contacts",
                params={"limit": 100},
                timeout=10.0,
            )
            if resp.status_code == 200:
                all_contacts = resp.json().get("contacts", [])
                # Filter to tier 1-3 contacts
                priority = [c for c in all_contacts if c.get("tier") in (1, 2, 3)]
                # Sort by BD priority
                priority.sort(key=lambda c: c.get("bd_priority", "z"))
                contacts = priority[:10]
        except Exception as e:
            logger.warning(f"Could not fetch priority contacts: {e}")
        return contacts

    # ─── Summary Generation ──────────────────────────────────────────────

    def _generate_executive_summary(self, brief: DailyBrief) -> str:
        """Generate executive summary from gathered data."""
        parts = []

        signals_count = len(brief.hiring_signals)
        if signals_count > 0:
            surge_count = sum(
                1
                for s in brief.hiring_signals
                if s.get("signal_type") == "hiring_surge"
            )
            parts.append(
                f"{signals_count} hiring signals detected ({surge_count} surges)"
            )

        opps = len(brief.new_opportunities)
        if opps > 0:
            parts.append(f"{opps} new job opportunities in the last 24 hours")

        contacts = len(brief.priority_contacts)
        if contacts > 0:
            parts.append(f"{contacts} priority contacts flagged for outreach")

        updates = len(brief.contract_updates)
        if updates > 0:
            parts.append(f"{updates} contract updates requiring attention")

        snap = brief.pipeline_snapshot
        if snap.get("total_programs"):
            parts.append(
                f"Pipeline tracking {snap['total_programs']} programs, "
                f"{snap['total_contacts']} contacts, {snap['total_jobs']} jobs"
            )

        if not parts:
            return "All clear — no significant overnight changes detected."

        return "Today's intelligence brief: " + ". ".join(parts) + "."

    # ─── Formatting ──────────────────────────────────────────────────────

    def format_slack_blocks(self, brief: DailyBrief) -> List[Dict]:
        """Format briefing as Slack Block Kit blocks."""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"Morning Brief — {brief.date}"},
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Executive Summary*\n{brief.executive_summary}",
                },
            },
        ]

        if brief.hiring_signals:
            signal_text = "\n".join(
                f"• *{s.get('signal_type', '').replace('_', ' ').title()}* — "
                f"{s.get('program', 'Unknown')} ({s.get('confidence', 0):.0%})"
                for s in brief.hiring_signals[:5]
            )
            blocks.append({"type": "divider"})
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Hiring Signals ({len(brief.hiring_signals)})*\n{signal_text}",
                    },
                }
            )

        if brief.new_opportunities:
            opp_text = "\n".join(
                f"• {o.get('title', '')} — {o.get('company', '')} ({o.get('location', '')})"
                for o in brief.new_opportunities[:5]
            )
            blocks.append({"type": "divider"})
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*New Opportunities ({len(brief.new_opportunities)})*\n{opp_text}",
                    },
                }
            )

        if brief.priority_contacts:
            contact_text = "\n".join(
                f"• *{c.get('name', '')}* — {c.get('title', '')} at {c.get('company', '')} (Tier {c.get('tier', '?')})"
                for c in brief.priority_contacts[:5]
            )
            blocks.append({"type": "divider"})
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Priority Contacts*\n{contact_text}",
                    },
                }
            )

        blocks.append(
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Generated at {brief.generated_at}"}
                ],
            }
        )

        return blocks

    def format_markdown(self, brief: DailyBrief) -> str:
        """Format briefing as markdown string."""
        lines = [
            f"# Morning Brief — {brief.date}",
            f"\n## Executive Summary\n{brief.executive_summary}",
        ]

        if brief.hiring_signals:
            lines.append(f"\n## Hiring Signals ({len(brief.hiring_signals)})")
            for s in brief.hiring_signals:
                lines.append(
                    f"- **{s.get('signal_type', '').replace('_', ' ').title()}** — "
                    f"{s.get('program', '')} at {s.get('location', '')} "
                    f"(confidence: {s.get('confidence', 0):.0%})"
                )

        snap = brief.pipeline_snapshot
        if snap:
            lines.append("\n## Pipeline Snapshot")
            lines.append(f"- Programs: {snap.get('total_programs', 0)}")
            lines.append(f"- Contacts: {snap.get('total_contacts', 0)}")
            lines.append(f"- Jobs: {snap.get('total_jobs', 0)}")
            lines.append(f"- Graph Entities: {snap.get('graph_entities', 0)}")

        if brief.new_opportunities:
            lines.append(f"\n## New Opportunities ({len(brief.new_opportunities)})")
            for o in brief.new_opportunities:
                lines.append(
                    f"- {o.get('title', '')} — {o.get('company', '')} ({o.get('location', '')})"
                )

        if brief.priority_contacts:
            lines.append(f"\n## Priority Contacts ({len(brief.priority_contacts)})")
            for c in brief.priority_contacts:
                lines.append(
                    f"- **{c.get('name', '')}** — {c.get('title', '')} at {c.get('company', '')} (Tier {c.get('tier', '?')})"
                )

        if brief.contract_updates:
            lines.append(f"\n## Contract Updates ({len(brief.contract_updates)})")
            for u in brief.contract_updates:
                lines.append(
                    f"- [{u.get('type', '')}] {u.get('name', u.get('program', ''))}"
                )

        lines.append(f"\n---\n*Generated at {brief.generated_at}*")
        return "\n".join(lines)

    # ─── Persistence ─────────────────────────────────────────────────────

    def _save_brief(self, brief: DailyBrief):
        """Save briefing to data/briefings/YYYY-MM-DD.json."""
        path = BRIEFINGS_DIR / f"{brief.date}.json"
        with open(path, "w") as f:
            json.dump(brief.to_dict(), f, indent=2)
        logger.info(f"Briefing saved to {path}")

    def get_brief(self, date: Optional[str] = None) -> Optional[DailyBrief]:
        """Load a saved briefing by date (defaults to today)."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        path = BRIEFINGS_DIR / f"{date}.json"
        if not path.exists():
            return None

        with open(path) as f:
            data = json.load(f)

        return DailyBrief(**data)

    def get_latest_brief(self) -> Optional[DailyBrief]:
        """Get the most recent briefing."""
        if not BRIEFINGS_DIR.exists():
            return None

        files = sorted(BRIEFINGS_DIR.glob("*.json"), reverse=True)
        if not files:
            return None

        with open(files[0]) as f:
            data = json.load(f)

        return DailyBrief(**data)

    def _send_to_slack(self, brief: DailyBrief):
        """Send briefing to Slack if configured."""
        try:
            from Engine8_Knowledge.integrations.slack_integration import get_slack_bot

            bot = get_slack_bot()
            blocks = self.format_slack_blocks(brief)
            bot.send_notification(
                channel="#bd-daily",
                message=f"Morning Brief — {brief.date}: {brief.executive_summary}",
                blocks=blocks,
            )
        except Exception as e:
            logger.debug(f"Slack notification skipped: {e}")
