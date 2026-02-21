"""Brief delivery service — stores and delivers intelligence briefs.

Briefs are persisted as JSON files under Engine8_Knowledge/data/briefs/.
Email delivery is stubbed (logs but does not send).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from Engine8_Knowledge.briefs.template_engine import IntelligenceBrief

try:
    import structlog

    logger = structlog.get_logger("BriefDeliveryService")
except ImportError:
    logger = logging.getLogger("BriefDeliveryService")

# Default storage directory
_DEFAULT_STORAGE = Path(__file__).parent.parent / "data" / "briefs"


class BriefDeliveryService:
    """Delivers briefs via email (stub) and stores them for dashboard access."""

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self._storage_dir = storage_dir or _DEFAULT_STORAGE
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info("delivery_service_init", storage_dir=str(self._storage_dir))

        # Schedule state
        self._schedule_enabled: bool = False
        self._schedule_day: str = "Monday"
        self._schedule_hour: int = 8

    # ------------------------------------------------------------------
    # Email delivery (stub)
    # ------------------------------------------------------------------

    def deliver_email(
        self,
        brief: IntelligenceBrief,
        recipients: List[str],
    ) -> Dict[str, Any]:
        """Send brief via SMTP — currently a stub that logs the intent.

        Returns a status dict indicating the delivery was logged but not sent.
        """
        logger.info(
            "email_delivery_stub",
            brief_id=brief.id,
            recipients=recipients,
            subject=brief.title,
        )
        return {
            "status": "stub",
            "message": "Email delivery is not yet implemented. Brief logged for future sending.",
            "brief_id": brief.id,
            "recipients": recipients,
            "would_send_subject": brief.title,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    def store_brief(self, brief: IntelligenceBrief) -> str:
        """Persist a brief to a JSON file. Returns the file path."""
        file_path = self._storage_dir / f"{brief.id}.json"
        file_path.write_text(json.dumps(brief.to_dict(), indent=2), encoding="utf-8")
        logger.info("brief_stored", brief_id=brief.id, path=str(file_path))
        return str(file_path)

    def list_briefs(
        self,
        portfolio_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """List stored briefs, optionally filtered by portfolio.

        Returns lightweight summaries (no full section content).
        """
        briefs: List[Dict[str, Any]] = []

        json_files = sorted(
            self._storage_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for fp in json_files:
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("brief_read_error", path=str(fp), error=str(exc))
                continue

            if portfolio_id and data.get("portfolio") != portfolio_id:
                continue

            briefs.append(
                {
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "portfolio": data.get("portfolio"),
                    "period_start": data.get("period_start"),
                    "period_end": data.get("period_end"),
                    "generated_at": data.get("generated_at"),
                    "section_count": len(data.get("sections", [])),
                }
            )

            if len(briefs) >= limit:
                break

        return briefs

    def get_brief(self, brief_id: str) -> Optional[IntelligenceBrief]:
        """Retrieve a stored brief by ID. Returns None if not found."""
        file_path = self._storage_dir / f"{brief_id}.json"
        if not file_path.exists():
            logger.info("brief_not_found", brief_id=brief_id)
            return None

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return IntelligenceBrief.from_dict(data)
        except (json.JSONDecodeError, KeyError, OSError) as exc:
            logger.error("brief_load_error", brief_id=brief_id, error=str(exc))
            return None

    # ------------------------------------------------------------------
    # Schedule management
    # ------------------------------------------------------------------

    def get_schedule(self) -> Dict[str, Any]:
        """Return the current brief generation schedule."""
        return {
            "enabled": self._schedule_enabled,
            "day": self._schedule_day,
            "hour": self._schedule_hour,
            "description": (
                f"Briefs generated every {self._schedule_day} at {self._schedule_hour:02d}:00 UTC"
                if self._schedule_enabled
                else "Automatic brief generation is disabled"
            ),
        }

    def toggle_schedule(self, enabled: Optional[bool] = None) -> Dict[str, Any]:
        """Toggle automatic brief generation on/off.

        If *enabled* is None, flips the current state.
        """
        if enabled is None:
            self._schedule_enabled = not self._schedule_enabled
        else:
            self._schedule_enabled = enabled

        logger.info("schedule_toggled", enabled=self._schedule_enabled)
        return self.get_schedule()
