"""
Bullhorn Activity Logger (Write-Back)
======================================

POSTs activity/note entries back to Bullhorn REST API when outreach
actions are completed. Closes the loop between BD intelligence and CRM.

Bullhorn REST API endpoints used:
- POST /entity/Note  — Create a note
- POST /entity/NoteEntity  — Link note to candidate/contact/job

Usage:
    from scripts.bullhorn_activity_logger import BullhornActivityLogger
    logger = BullhornActivityLogger()
    result = logger.log_outreach(
        contact_name="John Smith",
        activity_type="call",
        notes="Discussed DCGS opportunity",
        program="AF DCGS - PACAF",
    )
"""

import os
import json
import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Bullhorn REST API configuration
BULLHORN_REST_URL = os.environ.get("BULLHORN_REST_URL", "")
BULLHORN_API_KEY = os.environ.get("BULLHORN_API_KEY", "")
BULLHORN_BH_REST_TOKEN = os.environ.get("BULLHORN_BH_REST_TOKEN", "")

# Local activity log (always writes locally, optionally to Bullhorn API)
ACTIVITY_LOG_DB = Path(__file__).parent.parent / "data" / "activity_log.db"
BULLHORN_DB = Path(__file__).parent.parent / "data" / "bullhorn.db"


class BullhornActivityLogger:
    """Logs outreach activities to local DB and optionally to Bullhorn REST API."""

    def __init__(self, bullhorn_url: str = None, api_token: str = None):
        self.bullhorn_url = (bullhorn_url or BULLHORN_REST_URL).rstrip("/")
        self.api_token = api_token or BULLHORN_BH_REST_TOKEN
        self._init_local_db()

    def _init_local_db(self):
        """Initialize local activity log database."""
        ACTIVITY_LOG_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(ACTIVITY_LOG_DB))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS outreach_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_name TEXT NOT NULL,
                contact_email TEXT,
                company TEXT,
                activity_type TEXT NOT NULL,
                channel TEXT,
                program TEXT,
                notes TEXT,
                outcome TEXT,
                bullhorn_note_id INTEGER,
                bullhorn_synced INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                synced_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def log_outreach(
        self,
        contact_name: str,
        activity_type: str,
        notes: str = "",
        contact_email: str = "",
        company: str = "",
        channel: str = "",
        program: str = "",
        outcome: str = "",
        sync_to_bullhorn: bool = True,
    ) -> Dict[str, Any]:
        """
        Log an outreach activity.

        Args:
            contact_name: Contact's full name
            activity_type: call, email, linkedin, meeting, note
            notes: Activity description/notes
            contact_email: Contact's email
            company: Contact's company
            channel: Communication channel used
            program: Related program name
            outcome: Outcome of the interaction
            sync_to_bullhorn: Whether to push to Bullhorn REST API

        Returns:
            Activity log result with local ID and optional Bullhorn ID
        """
        result = {
            "success": True,
            "contact_name": contact_name,
            "activity_type": activity_type,
            "local_id": None,
            "bullhorn_note_id": None,
            "bullhorn_synced": False,
        }

        # Build activity note text
        note_body = self._build_note_body(
            contact_name, activity_type, notes, channel, program, outcome
        )

        # Save to local DB
        local_id = self._save_local(
            contact_name=contact_name,
            contact_email=contact_email,
            company=company,
            activity_type=activity_type,
            channel=channel,
            program=program,
            notes=note_body,
            outcome=outcome,
        )
        result["local_id"] = local_id

        # Optionally sync to Bullhorn
        if sync_to_bullhorn and self.bullhorn_url and self.api_token:
            try:
                bh_result = self._push_to_bullhorn(
                    contact_name=contact_name,
                    note_body=note_body,
                    activity_type=activity_type,
                )
                if bh_result.get("success"):
                    result["bullhorn_note_id"] = bh_result.get("note_id")
                    result["bullhorn_synced"] = True
                    self._mark_synced(local_id, bh_result.get("note_id"))
            except Exception as e:
                logger.warning(f"Bullhorn sync failed (saved locally): {e}")
                result["bullhorn_error"] = str(e)

        logger.info(
            f"Logged outreach: {activity_type} with {contact_name}"
            f" (local_id={local_id}, bh_synced={result['bullhorn_synced']})"
        )

        return result

    def get_unsynced(self, limit: int = 100) -> List[Dict]:
        """Get activities that haven't been synced to Bullhorn yet."""
        conn = sqlite3.connect(str(ACTIVITY_LOG_DB))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM outreach_log WHERE bullhorn_synced = 0 ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def retry_sync(self) -> Dict:
        """Retry syncing all unsynced activities to Bullhorn."""
        unsynced = self.get_unsynced()
        synced = 0
        failed = 0

        for activity in unsynced:
            try:
                bh_result = self._push_to_bullhorn(
                    contact_name=activity["contact_name"],
                    note_body=activity["notes"],
                    activity_type=activity["activity_type"],
                )
                if bh_result.get("success"):
                    self._mark_synced(activity["id"], bh_result.get("note_id"))
                    synced += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

        return {"synced": synced, "failed": failed, "total": len(unsynced)}

    def get_activity_log(self, contact_name: str = None, limit: int = 50) -> List[Dict]:
        """Get activity log, optionally filtered by contact."""
        conn = sqlite3.connect(str(ACTIVITY_LOG_DB))
        conn.row_factory = sqlite3.Row

        if contact_name:
            cursor = conn.execute(
                "SELECT * FROM outreach_log WHERE contact_name LIKE ? ORDER BY created_at DESC LIMIT ?",
                (f"%{contact_name}%", limit),
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM outreach_log ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )

        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_stats(self) -> Dict:
        """Get activity logging statistics."""
        conn = sqlite3.connect(str(ACTIVITY_LOG_DB))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM outreach_log")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM outreach_log WHERE bullhorn_synced = 1")
        synced = cursor.fetchone()[0]

        cursor.execute("SELECT activity_type, COUNT(*) FROM outreach_log GROUP BY activity_type")
        by_type = dict(cursor.fetchall())

        cursor.execute(
            "SELECT COUNT(*) FROM outreach_log WHERE created_at > datetime('now', '-7 days')"
        )
        last_week = cursor.fetchone()[0]

        conn.close()

        return {
            "total_logged": total,
            "bullhorn_synced": synced,
            "unsynced": total - synced,
            "by_type": by_type,
            "last_7_days": last_week,
        }

    def _build_note_body(
        self,
        contact_name: str,
        activity_type: str,
        notes: str,
        channel: str,
        program: str,
        outcome: str,
    ) -> str:
        """Build formatted note body for Bullhorn."""
        parts = [
            f"BD Outreach — {activity_type.upper()}",
            f"Contact: {contact_name}",
        ]
        if channel:
            parts.append(f"Channel: {channel}")
        if program:
            parts.append(f"Program: {program}")
        if outcome:
            parts.append(f"Outcome: {outcome}")
        if notes:
            parts.append(f"\n{notes}")
        parts.append(f"\n[Auto-logged by BD Intelligence System — {datetime.now().strftime('%Y-%m-%d %H:%M')}]")
        return "\n".join(parts)

    def _save_local(self, **kwargs) -> int:
        """Save activity to local SQLite database."""
        conn = sqlite3.connect(str(ACTIVITY_LOG_DB))
        cursor = conn.execute(
            """INSERT INTO outreach_log
            (contact_name, contact_email, company, activity_type, channel, program, notes, outcome)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                kwargs.get("contact_name", ""),
                kwargs.get("contact_email", ""),
                kwargs.get("company", ""),
                kwargs.get("activity_type", ""),
                kwargs.get("channel", ""),
                kwargs.get("program", ""),
                kwargs.get("notes", ""),
                kwargs.get("outcome", ""),
            ),
        )
        conn.commit()
        local_id = cursor.lastrowid
        conn.close()
        return local_id

    def _mark_synced(self, local_id: int, bullhorn_note_id: int = None):
        """Mark a local activity as synced to Bullhorn."""
        conn = sqlite3.connect(str(ACTIVITY_LOG_DB))
        conn.execute(
            "UPDATE outreach_log SET bullhorn_synced = 1, bullhorn_note_id = ?, synced_at = ? WHERE id = ?",
            (bullhorn_note_id, datetime.now().isoformat(), local_id),
        )
        conn.commit()
        conn.close()

    def _push_to_bullhorn(
        self,
        contact_name: str,
        note_body: str,
        activity_type: str,
    ) -> Dict:
        """Push a note to Bullhorn REST API."""
        import requests

        if not self.bullhorn_url or not self.api_token:
            return {"success": False, "error": "Bullhorn API not configured"}

        # Look up candidate/contact ID by name
        candidate_id = self._find_bullhorn_entity(contact_name)

        # Create note via Bullhorn REST API
        note_data = {
            "action": activity_type.capitalize(),
            "comments": note_body,
            "dateAdded": int(datetime.now().timestamp() * 1000),
            "personReference": {"id": candidate_id} if candidate_id else None,
        }

        try:
            response = requests.put(
                f"{self.bullhorn_url}/entity/Note",
                params={"BhRestToken": self.api_token},
                json=note_data,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            return {
                "success": True,
                "note_id": result.get("changedEntityId"),
                "response": result,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _find_bullhorn_entity(self, contact_name: str) -> Optional[int]:
        """Look up Bullhorn entity ID by contact name from local DB."""
        if not BULLHORN_DB.exists():
            return None

        try:
            conn = sqlite3.connect(str(BULLHORN_DB))
            cursor = conn.execute(
                "SELECT id FROM contacts WHERE name LIKE ? LIMIT 1",
                (f"%{contact_name}%",),
            )
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception:
            return None
