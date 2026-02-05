"""
Engine 6 Alert Engine - Monitors BD system health and sends notifications.

Alert rules:
1. High-priority contacts added (Tier 1)
2. Job count anomalies (>20% deviation)
3. Pipeline stage failures
4. Search quality degradation

Delivery channels: Slack webhook, n8n webhook, log file.
"""
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv

# Load environment
load_dotenv(Path(__file__).parent.parent.parent / "BD-Automation-Engine.env")
load_dotenv(override=True)

PROJECT_ROOT = Path(__file__).parent.parent.parent
LOG_DIR = PROJECT_ROOT / "outputs" / "Logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("BD-Alerts")


# ============================================
# DATA STRUCTURES
# ============================================

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    alert_id: str
    rule_id: str
    severity: AlertSeverity
    title: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================
# ALERT ENGINE
# ============================================

class AlertEngine:
    """Runs alert rules and delivers notifications."""

    COOLDOWN_MINUTES = 60

    def __init__(self):
        self.state_file = PROJECT_ROOT / "outputs" / "alert_state.json"
        self.pipeline_state_file = PROJECT_ROOT / "outputs" / "pipeline_state.json"
        self.slack_url = os.getenv("SLACK_WEBHOOK_URL", "")
        self.n8n_url = os.getenv("N8N_ALERT_WEBHOOK", "")
        self._state = self._load_state()

    # -- State persistence --

    def _load_state(self) -> Dict:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {"last_fired": {}, "history": []}

    def _save_state(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self._state, f, indent=2, default=str)

    def _is_cooled_down(self, rule_id: str) -> bool:
        last = self._state.get("last_fired", {}).get(rule_id)
        if not last:
            return True
        try:
            last_dt = datetime.fromisoformat(last)
            return datetime.now() - last_dt > timedelta(minutes=self.COOLDOWN_MINUTES)
        except (ValueError, TypeError):
            return True

    def _record_fired(self, rule_id: str):
        self._state.setdefault("last_fired", {})[rule_id] = datetime.now().isoformat()

    # -- Rule checks --

    def check_all_rules(self) -> List[Alert]:
        """Run all alert rules, respecting cooldowns."""
        alerts: List[Alert] = []

        rules = [
            ("high_priority_contacts", self._check_high_priority_contacts),
            ("job_count_anomaly", self._check_job_count_anomalies),
            ("pipeline_failures", self._check_pipeline_failures),
            ("search_quality", self._check_search_quality),
        ]

        for rule_id, check_fn in rules:
            if not self._is_cooled_down(rule_id):
                continue
            try:
                alert = check_fn(rule_id)
                if alert:
                    alerts.append(alert)
                    self._record_fired(rule_id)
            except Exception as e:
                logger.warning(f"Alert rule '{rule_id}' failed: {e}")

        self._save_state()
        return alerts

    def _check_high_priority_contacts(self, rule_id: str) -> Optional[Alert]:
        """Alert when new Tier 1 contacts are detected in Qdrant."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

            client = QdrantClient(url="http://localhost:6333", timeout=10)
            # Count Tier 1 contacts
            result = client.count(
                collection_name="contacts",
                count_filter=Filter(must=[
                    FieldCondition(key="tier", match=MatchValue(value="1"))
                ]),
                exact=False,
            )
            tier1_count = result.count

            # Compare to baseline (stored in state)
            baseline = self._state.get("baselines", {}).get("tier1_contacts", 0)
            new_count = tier1_count - baseline

            # Update baseline
            self._state.setdefault("baselines", {})["tier1_contacts"] = tier1_count

            if new_count > 0 and baseline > 0:
                return Alert(
                    alert_id=str(uuid.uuid4())[:8],
                    rule_id=rule_id,
                    severity=AlertSeverity.WARNING,
                    title=f"{new_count} new Tier 1 contacts detected",
                    message=f"Total Tier 1 contacts: {tier1_count} (was {baseline}). Review new high-priority contacts.",
                    data={"tier1_total": tier1_count, "new": new_count, "baseline": baseline},
                )
        except Exception as e:
            logger.debug(f"Tier 1 check skipped: {e}")
        return None

    def _check_job_count_anomalies(self, rule_id: str) -> Optional[Alert]:
        """Alert when job count deviates >20% from baseline."""
        try:
            from qdrant_client import QdrantClient

            client = QdrantClient(url="http://localhost:6333", timeout=10)
            info = client.get_collection("jobs")
            current = info.points_count

            baseline = self._state.get("baselines", {}).get("jobs_count", 0)
            self._state.setdefault("baselines", {})["jobs_count"] = current

            if baseline > 0:
                deviation = abs(current - baseline) / baseline
                if deviation > 0.20:
                    direction = "increased" if current > baseline else "decreased"
                    return Alert(
                        alert_id=str(uuid.uuid4())[:8],
                        rule_id=rule_id,
                        severity=AlertSeverity.WARNING,
                        title=f"Job count {direction} {deviation:.0%}",
                        message=f"Jobs collection: {current} vectors (baseline: {baseline}). Deviation: {deviation:.1%}.",
                        data={"current": current, "baseline": baseline, "deviation": round(deviation, 3)},
                    )
        except Exception as e:
            logger.debug(f"Job count check skipped: {e}")
        return None

    def _check_pipeline_failures(self, rule_id: str) -> Optional[Alert]:
        """Alert on pipeline stage errors from last run."""
        if not self.pipeline_state_file.exists():
            return None
        try:
            with open(self.pipeline_state_file, "r") as f:
                state = json.load(f)
            last_run = state.get("last_completed_run", {})
            errors = last_run.get("errors", [])
            if errors:
                return Alert(
                    alert_id=str(uuid.uuid4())[:8],
                    rule_id=rule_id,
                    severity=AlertSeverity.CRITICAL,
                    title=f"Pipeline failed with {len(errors)} error(s)",
                    message=f"Last run errors: {'; '.join(errors[:3])}",
                    data={"errors": errors, "run_id": last_run.get("run_id", "unknown")},
                )
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(f"Pipeline state check skipped: {e}")
        return None

    def _check_search_quality(self, rule_id: str) -> Optional[Alert]:
        """Alert when search quality benchmark scores drop."""
        try:
            from qdrant_client import QdrantClient
            from openai import OpenAI

            client = QdrantClient(url="http://localhost:6333", timeout=10)
            oai = OpenAI()

            # Quick benchmark: one representative query
            query = "network engineer TS/SCI Langley"
            resp = oai.embeddings.create(model="text-embedding-3-small", input=[query])
            vector = resp.data[0].embedding

            results = client.query_points(
                collection_name="jobs",
                query=vector,
                limit=1,
            )
            top_score = results.points[0].score if results.points else 0.0

            if top_score < 0.60:
                return Alert(
                    alert_id=str(uuid.uuid4())[:8],
                    rule_id=rule_id,
                    severity=AlertSeverity.WARNING,
                    title="Search quality below threshold",
                    message=f"Benchmark query scored {top_score:.3f} (threshold: 0.60). Embeddings may need refresh.",
                    data={"query": query, "score": round(top_score, 4), "threshold": 0.60},
                )
        except Exception as e:
            logger.debug(f"Search quality check skipped: {e}")
        return None

    # -- Delivery --

    def deliver_alert(self, alert: Alert):
        """Deliver alert to all configured channels."""
        # Always log
        level = logging.CRITICAL if alert.severity == AlertSeverity.CRITICAL else logging.WARNING
        logger.log(level, f"[{alert.severity.value.upper()}] {alert.title}: {alert.message}")

        # Record in history
        self._state.setdefault("history", []).append(asdict(alert))
        if len(self._state["history"]) > 200:
            self._state["history"] = self._state["history"][-200:]
        self._save_state()

        # Slack webhook
        if self.slack_url:
            self._send_slack(alert)

        # n8n webhook
        if self.n8n_url:
            self._send_webhook(alert)

    def _send_slack(self, alert: Alert):
        colors = {"info": "#36a64f", "warning": "#ff9900", "critical": "#ff0000"}
        payload = {
            "attachments": [{
                "color": colors.get(alert.severity.value, "#cccccc"),
                "title": f"BD Alert: {alert.title}",
                "text": alert.message,
                "fields": [
                    {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                    {"title": "Rule", "value": alert.rule_id, "short": True},
                ],
                "ts": int(datetime.now().timestamp()),
            }]
        }
        try:
            resp = requests.post(self.slack_url, json=payload, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"Slack delivery failed: {resp.status_code}")
        except requests.RequestException as e:
            logger.warning(f"Slack delivery error: {e}")

    def _send_webhook(self, alert: Alert):
        payload = {
            "source": "BD-Automation-Engine",
            "alert": asdict(alert),
            "timestamp": datetime.now().isoformat(),
        }
        try:
            resp = requests.post(self.n8n_url, json=payload, timeout=10)
            if resp.status_code not in (200, 201):
                logger.warning(f"Webhook delivery failed: {resp.status_code}")
        except requests.RequestException as e:
            logger.warning(f"Webhook delivery error: {e}")

    def deliver_all(self, alerts: List[Alert]):
        """Deliver a list of alerts."""
        for alert in alerts:
            self.deliver_alert(alert)

    def get_recent_alerts(self, limit: int = 20) -> List[Dict]:
        """Return recent alert history."""
        return list(reversed(self._state.get("history", [])[-limit:]))


# ============================================
# CLI
# ============================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    engine = AlertEngine()
    alerts = engine.check_all_rules()

    if alerts:
        print(f"\n{len(alerts)} alert(s) triggered:")
        for a in alerts:
            print(f"  [{a.severity.value.upper()}] {a.title}")
            print(f"    {a.message}")
        engine.deliver_all(alerts)
    else:
        print("No alerts triggered.")
    print(f"\nRecent history: {len(engine.get_recent_alerts())} alerts")
