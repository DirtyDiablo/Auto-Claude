"""
CRM Bidirectional Sync — Synchronize BD intelligence with Bullhorn CRM data.

Pushes contact classification updates (tier, program, priority) to a sync queue,
pulls new placements and activity updates from Bullhorn SQLite DB.

Conflict resolution:
- Bullhorn = source of truth for candidate/placement data
- Qdrant = source of truth for BD intelligence (scores, tiers, programs)
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "data"
SYNC_QUEUE_PATH = DATA_DIR / "crm_sync_queue.jsonl"
SYNC_LOG_PATH = DATA_DIR / "crm_sync_log.jsonl"

# Bullhorn DB path
BULLHORN_DB = (
    Path(os.path.dirname(os.path.dirname(__file__)))
    / ".."
    / "Engine7_BullhornETL"
    / "data"
    / "bullhorn_master.db"
)


class CRMSyncManager:
    """
    Bidirectional sync manager for Bullhorn CRM ↔ BD Intelligence.

    Push direction (BD → CRM):
    - Contact tier/priority/program updates queued to JSONL
    - Ready for external sync tool to apply to Bullhorn API

    Pull direction (CRM → BD):
    - New placements since last sync
    - New call notes / activities since last sync
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(BULLHORN_DB.resolve())
        self._last_sync: Optional[str] = None
        self._records_pushed = 0
        self._records_pulled = 0
        self._errors: List[str] = []
        self._last_placement_id = 0
        self._last_activity_id = 0

        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Load last sync state
        self._load_sync_state()

    def _get_db(self) -> sqlite3.Connection:
        """Get SQLite connection to Bullhorn DB."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Bullhorn DB not found at {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_sync_state(self):
        """Load last sync state from log file."""
        if not SYNC_LOG_PATH.exists():
            return

        try:
            last_entry = None
            with open(SYNC_LOG_PATH) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        last_entry = json.loads(line)

            if last_entry:
                self._last_sync = last_entry.get("timestamp")
                self._last_placement_id = last_entry.get("last_placement_id", 0)
                self._last_activity_id = last_entry.get("last_activity_id", 0)
                logger.info(f"Loaded sync state: last sync {self._last_sync}")
        except Exception as e:
            logger.warning(f"Error loading sync state: {e}")

    def _save_sync_log(self, action: str, details: Dict):
        """Append sync event to log."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "last_placement_id": self._last_placement_id,
            "last_activity_id": self._last_activity_id,
            **details,
        }
        with open(SYNC_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
        self._last_sync = entry["timestamp"]

    # ─── Push: BD → CRM ─────────────────────────────────────────────────

    def push_contact_updates(self, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Queue contact classification changes for CRM push.

        Args:
            contacts: List of dicts with at least 'name' and fields to update
                     (tier, program, priority, bd_score, notes)

        Returns:
            Result with queued count
        """
        queued = 0
        for contact in contacts:
            name = contact.get("name")
            if not name:
                continue

            entry = {
                "type": "contact_update",
                "timestamp": datetime.now().isoformat(),
                "status": "pending",
                "contact_name": name,
                "updates": {
                    k: v
                    for k, v in contact.items()
                    if k
                    in (
                        "tier",
                        "program",
                        "priority",
                        "bd_score",
                        "notes",
                        "matched_programs",
                    )
                    and v is not None
                },
            }

            with open(SYNC_QUEUE_PATH, "a") as f:
                f.write(json.dumps(entry) + "\n")
            queued += 1

        self._records_pushed += queued
        self._save_sync_log("push_contacts", {"queued": queued})

        logger.info(f"Queued {queued} contact updates for CRM sync")
        return {"success": True, "queued": queued}

    # ─── Pull: CRM → BD ─────────────────────────────────────────────────

    def pull_new_placements(self) -> Dict[str, Any]:
        """
        Pull new placements from Bullhorn since last sync.

        Returns:
            Dict with new placements and count
        """
        try:
            conn = self._get_db()
            cursor = conn.execute(
                """
                SELECT p.id, p.bullhorn_placement_id, p.placement_date, p.start_date,
                       p.end_date, p.salary, p.pay_rate, p.bill_rate, p.status,
                       c.full_name as candidate_name, c.email as candidate_email,
                       j.title as job_title, j.prime_contractor, j.client_corporation
                FROM placements p
                LEFT JOIN candidates c ON p.candidate_id = c.id
                LEFT JOIN jobs j ON p.job_id = j.id
                WHERE p.id > ?
                ORDER BY p.id ASC
                LIMIT 500
                """,
                (self._last_placement_id,),
            )

            placements = []
            max_id = self._last_placement_id
            for row in cursor:
                placement = dict(row)
                placements.append(placement)
                max_id = max(max_id, placement["id"])

            conn.close()

            if placements:
                self._last_placement_id = max_id
                self._records_pulled += len(placements)
                self._save_sync_log(
                    "pull_placements", {"count": len(placements), "max_id": max_id}
                )

            logger.info(f"Pulled {len(placements)} new placements")
            return {"success": True, "placements": placements, "count": len(placements)}

        except FileNotFoundError:
            return {
                "success": False,
                "error": "Bullhorn DB not found",
                "placements": [],
                "count": 0,
            }
        except Exception as e:
            error_msg = f"Pull placements error: {e}"
            logger.error(error_msg)
            self._errors.append(error_msg)
            return {"success": False, "error": str(e), "placements": [], "count": 0}

    def pull_activity_updates(self) -> Dict[str, Any]:
        """
        Pull new activities (call notes, interactions) since last sync.

        Returns:
            Dict with new activities and count
        """
        try:
            conn = self._get_db()
            cursor = conn.execute(
                """
                SELECT a.id, a.activity_type, a.action, a.date_added,
                       a.comments, a.status,
                       c.full_name as contact_name,
                       j.title as job_title, j.prime_contractor
                FROM activities a
                LEFT JOIN candidates c ON a.related_candidate_id = c.id
                LEFT JOIN jobs j ON a.related_job_id = j.id
                WHERE a.id > ?
                ORDER BY a.id ASC
                LIMIT 1000
                """,
                (self._last_activity_id,),
            )

            activities = []
            max_id = self._last_activity_id
            for row in cursor:
                activity = dict(row)
                activities.append(activity)
                max_id = max(max_id, activity["id"])

            conn.close()

            if activities:
                self._last_activity_id = max_id
                self._records_pulled += len(activities)
                self._save_sync_log(
                    "pull_activities", {"count": len(activities), "max_id": max_id}
                )

            logger.info(f"Pulled {len(activities)} new activities")
            return {"success": True, "activities": activities, "count": len(activities)}

        except FileNotFoundError:
            return {
                "success": False,
                "error": "Bullhorn DB not found",
                "activities": [],
                "count": 0,
            }
        except Exception as e:
            error_msg = f"Pull activities error: {e}"
            logger.error(error_msg)
            self._errors.append(error_msg)
            return {"success": False, "error": str(e), "activities": [], "count": 0}

    # ─── Full Sync Cycle ─────────────────────────────────────────────────

    def run_sync_cycle(self) -> Dict[str, Any]:
        """
        Run a full bidirectional sync cycle.

        1. Pull new placements
        2. Pull new activities
        3. Report status

        Push operations happen via push_contact_updates() calls.
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "placements": self.pull_new_placements(),
            "activities": self.pull_activity_updates(),
        }

        self._save_sync_log(
            "full_sync",
            {
                "placements_pulled": results["placements"]["count"],
                "activities_pulled": results["activities"]["count"],
            },
        )

        return results

    # ─── Status & Queue ──────────────────────────────────────────────────

    def sync_status(self) -> Dict[str, Any]:
        """Get comprehensive sync status."""
        queue_count = 0
        pending_count = 0
        if SYNC_QUEUE_PATH.exists():
            with open(SYNC_QUEUE_PATH) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        queue_count += 1
                        entry = json.loads(line)
                        if entry.get("status") == "pending":
                            pending_count += 1

        db_exists = os.path.exists(self.db_path)
        db_size = os.path.getsize(self.db_path) if db_exists else 0

        return {
            "connected": db_exists,
            "db_path": self.db_path,
            "db_size_mb": round(db_size / (1024 * 1024), 1),
            "last_sync": self._last_sync,
            "records_pushed": self._records_pushed,
            "records_pulled": self._records_pulled,
            "queue_total": queue_count,
            "queue_pending": pending_count,
            "last_placement_id": self._last_placement_id,
            "last_activity_id": self._last_activity_id,
            "errors": self._errors[-5:],
        }

    def get_queue(self, limit: int = 50) -> List[Dict]:
        """Get pending items from the sync queue."""
        if not SYNC_QUEUE_PATH.exists():
            return []

        items = []
        with open(SYNC_QUEUE_PATH) as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    if entry.get("status") == "pending":
                        items.append(entry)
                        if len(items) >= limit:
                            break

        return items

    def get_sync_log(self, limit: int = 50) -> List[Dict]:
        """Get recent sync log entries."""
        if not SYNC_LOG_PATH.exists():
            return []

        entries = []
        with open(SYNC_LOG_PATH) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))

        return entries[-limit:]


# ─── Singleton ──────────────────────────────────────────────────────────────

_sync_manager: Optional[CRMSyncManager] = None


def get_crm_sync_manager() -> CRMSyncManager:
    """Get or create the singleton CRMSyncManager."""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = CRMSyncManager()
    return _sync_manager
