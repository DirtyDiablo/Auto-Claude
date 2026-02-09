"""
Slack BD Bot — Rich notifications and slash commands for BD intelligence.

Sends daily digests, hot lead alerts, pipeline updates, and hiring signals
to Slack channels using Block Kit formatting. Falls back to JSONL logging
when SLACK_BOT_TOKEN is not configured.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "data"
FALLBACK_LOG = DATA_DIR / "slack_notifications.jsonl"


class SlackBDBot:
    """
    Slack integration for BD intelligence notifications.

    If SLACK_BOT_TOKEN is set, sends real Slack messages via slack-sdk.
    Otherwise, logs messages to data/slack_notifications.jsonl for review.
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("SLACK_BOT_TOKEN")
        self._client = None
        self._message_count = 0
        self._last_sent: Optional[str] = None
        self._connected = False

        if self.token:
            try:
                from slack_sdk import WebClient
                self._client = WebClient(token=self.token)
                # Test connection
                auth = self._client.auth_test()
                self._connected = True
                logger.info(f"Slack connected as {auth.get('user', 'unknown')}")
            except Exception as e:
                logger.warning(f"Slack connection failed: {e}. Using JSONL fallback.")
                self._client = None
                self._connected = False
        else:
            logger.info("No SLACK_BOT_TOKEN set. Using JSONL fallback for notifications.")

    @property
    def is_connected(self) -> bool:
        return self._connected and self._client is not None

    def get_status(self) -> Dict[str, Any]:
        """Get bot connection status."""
        return {
            "connected": self.is_connected,
            "mode": "slack" if self.is_connected else "jsonl_fallback",
            "message_count": self._message_count,
            "last_sent": self._last_sent,
            "fallback_log": str(FALLBACK_LOG),
        }

    # ─── Core Messaging ─────────────────────────────────────────────────

    def send_notification(
        self,
        channel: str,
        message: str,
        blocks: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Send a notification to a Slack channel.

        Args:
            channel: Channel name or ID (e.g. "#bd-alerts")
            message: Fallback text (shown in notifications)
            blocks: Slack Block Kit blocks for rich formatting

        Returns:
            Result dict with success status
        """
        payload = {
            "channel": channel,
            "text": message,
            "blocks": blocks,
            "timestamp": datetime.now().isoformat(),
        }

        if self.is_connected:
            try:
                result = self._client.chat_postMessage(
                    channel=channel,
                    text=message,
                    blocks=blocks,
                )
                self._message_count += 1
                self._last_sent = datetime.now().isoformat()
                return {"success": True, "ts": result.get("ts"), "channel": channel}
            except Exception as e:
                logger.error(f"Slack send error: {e}")
                self._log_to_file(payload)
                return {"success": False, "error": str(e), "fallback": True}
        else:
            self._log_to_file(payload)
            return {"success": True, "mode": "jsonl_fallback", "channel": channel}

    def _log_to_file(self, payload: Dict):
        """Log notification to JSONL fallback file."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(FALLBACK_LOG, "a") as f:
            f.write(json.dumps(payload) + "\n")
        self._message_count += 1
        self._last_sent = datetime.now().isoformat()

    # ─── Daily Digest ────────────────────────────────────────────────────

    def send_daily_digest(self, channel: str) -> Dict[str, Any]:
        """
        Send morning briefing with overnight alerts, pipeline changes,
        due sequences, and active hiring signals.
        """
        now = datetime.now()
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"BD Daily Digest — {now.strftime('%A, %B %d')}",
                },
            },
            {"type": "divider"},
        ]

        # Pipeline summary section
        pipeline_data = self._get_pipeline_summary()
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Pipeline Overview*\n"
                    f"Active Deals: *{pipeline_data.get('active_deals', 0)}*\n"
                    f"Contacts in Sequence: *{pipeline_data.get('active_sequences', 0)}*\n"
                    f"Open Jobs Tracked: *{pipeline_data.get('open_jobs', 0)}*"
                ),
            },
        })

        # Hiring signals section
        signals = self._get_hiring_signals()
        if signals:
            signal_text = "\n".join(
                f"• *{s['signal_type'].replace('_', ' ').title()}* — {s['program']} ({s['confidence']:.0%})"
                for s in signals[:5]
            )
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Active Hiring Signals ({len(signals)})*\n{signal_text}",
                },
            })

        # Footer
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Generated by BD Intelligence System at {now.strftime('%H:%M')}",
                }
            ],
        })

        return self.send_notification(
            channel=channel,
            message=f"BD Daily Digest — {now.strftime('%B %d')}",
            blocks=blocks,
        )

    # ─── Hot Lead Alert ──────────────────────────────────────────────────

    def send_hot_lead_alert(
        self,
        channel: str,
        contact: Dict[str, Any],
        reason: str,
    ) -> Dict[str, Any]:
        """
        Send immediate alert for a high-priority lead (score >= 80).

        Args:
            channel: Target channel
            contact: Contact dict with name, title, company, tier, program
            reason: Why this is a hot lead
        """
        name = contact.get("name", "Unknown")
        title = contact.get("title", "")
        company = contact.get("company", "")
        tier = contact.get("tier", "")
        program = contact.get("program", "")

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Hot Lead Alert"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Contact:*\n{name}"},
                    {"type": "mrkdwn", "text": f"*Title:*\n{title}"},
                    {"type": "mrkdwn", "text": f"*Company:*\n{company}"},
                    {"type": "mrkdwn", "text": f"*Tier:*\n{tier}"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Program:* {program}\n*Reason:* {reason}",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Contact"},
                        "value": name,
                        "action_id": "view_contact",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Draft Outreach"},
                        "value": name,
                        "action_id": "draft_outreach",
                    },
                ],
            },
        ]

        return self.send_notification(
            channel=channel,
            message=f"Hot Lead: {name} at {company} — {reason}",
            blocks=blocks,
        )

    # ─── Pipeline Update ─────────────────────────────────────────────────

    def send_pipeline_update(
        self,
        channel: str,
        deal: Dict[str, Any],
        old_stage: str,
        new_stage: str,
    ) -> Dict[str, Any]:
        """Send notification when a deal moves pipeline stages."""
        deal_name = deal.get("name", "Unknown Deal")
        value = deal.get("value", "")

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Pipeline Update*\n"
                        f"*{deal_name}*\n"
                        f"{old_stage} → *{new_stage}*"
                        + (f"\nValue: {value}" if value else "")
                    ),
                },
            },
        ]

        return self.send_notification(
            channel=channel,
            message=f"Pipeline: {deal_name} moved to {new_stage}",
            blocks=blocks,
        )

    # ─── Slash Command Handlers ──────────────────────────────────────────

    def handle_command(self, command: str, text: str) -> Dict[str, Any]:
        """
        Handle slash commands from Slack.

        Commands:
            /bd-search [query]  — Search contacts, programs, jobs
            /bd-pipeline        — Current pipeline summary
            /bd-signals         — Active hiring signals
        """
        cmd = command.strip("/").lower()

        if cmd == "bd-search":
            return self._handle_search(text)
        elif cmd == "bd-pipeline":
            return self._handle_pipeline()
        elif cmd == "bd-signals":
            return self._handle_signals()
        else:
            return {
                "response_type": "ephemeral",
                "text": f"Unknown command: {command}. Try /bd-search, /bd-pipeline, or /bd-signals",
            }

    def _handle_search(self, query: str) -> Dict[str, Any]:
        """Handle /bd-search command."""
        if not query.strip():
            return {
                "response_type": "ephemeral",
                "text": "Usage: /bd-search [query]\nExample: /bd-search DCGS analyst",
            }

        # Search via knowledge API
        results = self._search_knowledge(query)
        if not results:
            return {
                "response_type": "ephemeral",
                "text": f"No results found for: {query}",
            }

        text_lines = [f"*Search results for:* _{query}_\n"]
        for r in results[:10]:
            name = r.get("name", r.get("text", "Unknown"))
            collection = r.get("collection", "")
            score = r.get("score", 0)
            text_lines.append(f"• [{collection}] *{name}* (score: {score:.2f})")

        return {
            "response_type": "in_channel",
            "text": "\n".join(text_lines),
        }

    def _handle_pipeline(self) -> Dict[str, Any]:
        """Handle /bd-pipeline command."""
        data = self._get_pipeline_summary()
        return {
            "response_type": "in_channel",
            "text": (
                "*BD Pipeline Summary*\n"
                f"• Active Deals: *{data.get('active_deals', 0)}*\n"
                f"• Active Sequences: *{data.get('active_sequences', 0)}*\n"
                f"• Open Jobs: *{data.get('open_jobs', 0)}*\n"
                f"• Top Programs: {', '.join(data.get('top_programs', []))}"
            ),
        }

    def _handle_signals(self) -> Dict[str, Any]:
        """Handle /bd-signals command."""
        signals = self._get_hiring_signals()
        if not signals:
            return {
                "response_type": "ephemeral",
                "text": "No active hiring signals detected.",
            }

        lines = ["*Active Hiring Signals*\n"]
        for s in signals[:10]:
            emoji = {"hiring_surge": "📈", "new_capability": "⚡", "clearance_escalation": "🔒"}.get(
                s["signal_type"], "📊"
            )
            lines.append(
                f"{emoji} *{s['signal_type'].replace('_', ' ').title()}* — "
                f"{s['program']} @ {s['location']} ({s['confidence']:.0%})"
            )

        return {"response_type": "in_channel", "text": "\n".join(lines)}

    # ─── Data Fetchers (best-effort) ─────────────────────────────────────

    def _get_pipeline_summary(self) -> Dict[str, Any]:
        """Fetch pipeline summary from API (best-effort)."""
        try:
            import httpx
            resp = httpx.get("http://localhost:8100/stats", timeout=5.0)
            if resp.status_code == 200:
                stats = resp.json()
                collections = stats.get("collections", {})
                return {
                    "active_deals": collections.get("programs", {}).get("count", 0),
                    "active_sequences": 0,
                    "open_jobs": collections.get("jobs", {}).get("count", 0),
                    "top_programs": [],
                }
        except Exception:
            pass
        return {"active_deals": 0, "active_sequences": 0, "open_jobs": 0, "top_programs": []}

    def _get_hiring_signals(self) -> List[Dict]:
        """Fetch hiring signals from ML API (best-effort)."""
        try:
            import httpx
            resp = httpx.get("http://localhost:8100/ml/hiring-signals", timeout=5.0)
            if resp.status_code == 200:
                return resp.json().get("signals", [])
        except Exception:
            pass
        return []

    def _search_knowledge(self, query: str) -> List[Dict]:
        """Search knowledge base (best-effort)."""
        try:
            import httpx
            resp = httpx.get("http://localhost:8100/search", params={"q": query, "limit": 10}, timeout=5.0)
            if resp.status_code == 200:
                return resp.json().get("results", [])
        except Exception:
            pass
        return []

    def get_recent_notifications(self, limit: int = 50) -> List[Dict]:
        """Read recent notifications from JSONL fallback log."""
        if not FALLBACK_LOG.exists():
            return []

        lines = []
        try:
            with open(FALLBACK_LOG) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        lines.append(json.loads(line))
        except Exception as e:
            logger.warning(f"Error reading notification log: {e}")

        return lines[-limit:]


# ─── Singleton ──────────────────────────────────────────────────────────────

_bot: Optional[SlackBDBot] = None


def get_slack_bot() -> SlackBDBot:
    """Get or create the singleton SlackBDBot."""
    global _bot
    if _bot is None:
        _bot = SlackBDBot()
    return _bot
