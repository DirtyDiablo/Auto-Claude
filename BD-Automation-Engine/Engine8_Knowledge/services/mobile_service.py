"""Mobile data service — lightweight data access for mobile API endpoints.

Queries Bullhorn SQLite for contacts, federal-programs CSV for programs,
and synthesises alerts/search from available data sources.  Falls back
to sensible empty defaults when data files are absent.
"""

import logging
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import structlog

    logger = structlog.get_logger("MobileService")
except ImportError:
    logger = logging.getLogger("MobileService")

# Project root for locating data files
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_BULLHORN_DB = _PROJECT_ROOT / "Engine7_BullhornETL" / "data" / "bullhorn.db"

# BD score thresholds (matches Engine5_Scoring)
HOT_THRESHOLD = 80
WARM_THRESHOLD = 50

# Tier label mapping
_TIER_LABELS = {
    1: "Decision Maker",
    2: "Budget Authority",
    3: "Technical Lead",
    4: "Program Staff",
    5: "Support",
    6: "Unknown",
}


class MobileService:
    """Lightweight data-access layer for mobile API endpoints."""

    def __init__(self, bullhorn_db_path: Optional[str] = None):
        self._db_path = Path(bullhorn_db_path) if bullhorn_db_path else _BULLHORN_DB
        logger.info(
            "mobile_service_init",
            bullhorn_db=str(self._db_path),
            db_exists=self._db_path.exists(),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_db(self) -> Optional[sqlite3.Connection]:
        if not self._db_path.exists():
            return None
        try:
            conn = sqlite3.connect(str(self._db_path))
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as exc:
            logger.error("db_connect_error", error=str(exc))
            return None

    def _query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = self._get_db()
        if conn is None:
            return []
        try:
            cur = conn.execute(sql, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        except sqlite3.Error as exc:
            logger.error("db_query_error", error=str(exc), sql=sql[:120])
            return []
        finally:
            conn.close()

    def _count(self, table: str) -> int:
        rows = self._query(f"SELECT COUNT(*) as cnt FROM {table}")  # noqa: S608
        return rows[0]["cnt"] if rows else 0

    @staticmethod
    def _tier_label(tier: int) -> str:
        return _TIER_LABELS.get(tier, "Unknown")

    # ------------------------------------------------------------------
    # Dashboard summary
    # ------------------------------------------------------------------

    def get_dashboard(self) -> Dict[str, Any]:
        """Return top-level metrics for the mobile dashboard."""
        contacts_total = self._count("contacts") if self._get_db() else 0

        # Attempt to count programs from a programs table or CSV
        programs_total = 0
        try:
            programs_total = self._count("programs")
        except Exception:
            programs_total = 0

        # Score-based lead counts
        hot = 0
        warm = 0
        avg_score = 0.0
        pipeline_total = 0

        score_rows = self._query(
            "SELECT bd_score FROM contacts WHERE bd_score IS NOT NULL"
        )
        if score_rows:
            scores = [r["bd_score"] for r in score_rows if r["bd_score"] is not None]
            if scores:
                hot = sum(1 for s in scores if s >= HOT_THRESHOLD)
                warm = sum(1 for s in scores if WARM_THRESHOLD <= s < HOT_THRESHOLD)
                avg_score = round(sum(scores) / len(scores), 1)
                pipeline_total = len(scores)

        return {
            "pipeline_total": pipeline_total,
            "hot_leads": hot,
            "warm_leads": warm,
            "avg_score": avg_score,
            "contacts_total": contacts_total,
            "programs_total": programs_total,
            "recent_alerts": 0,
            "last_updated": datetime.now(UTC).isoformat(),
        }

    # ------------------------------------------------------------------
    # Contacts
    # ------------------------------------------------------------------

    def get_contacts(
        self, query: str = "", limit: int = 20, page: int = 1
    ) -> Dict[str, Any]:
        """Return paginated contact list with optional search."""
        offset = (max(1, page) - 1) * limit

        if query:
            where = "WHERE name LIKE ? OR company LIKE ? OR email LIKE ?"
            param = f"%{query}%"
            params: tuple = (param, param, param)
            count_rows = self._query(
                f"SELECT COUNT(*) as cnt FROM contacts {where}", params
            )
            total = count_rows[0]["cnt"] if count_rows else 0
            rows = self._query(
                f"SELECT * FROM contacts {where} ORDER BY name LIMIT ? OFFSET ?",
                (*params, limit, offset),
            )
        else:
            total = self._count("contacts") if self._get_db() else 0
            rows = self._query(
                "SELECT * FROM contacts ORDER BY name LIMIT ? OFFSET ?",
                (limit, offset),
            )

        items = []
        for r in rows:
            tier = r.get("tier") or r.get("contact_tier") or 6
            try:
                tier = int(tier)
            except (ValueError, TypeError):
                tier = 6
            items.append(
                {
                    "id": str(r.get("id", r.get("contact_id", ""))),
                    "name": r.get("name", r.get("first_name", "")),
                    "company": r.get("company", r.get("company_name", "")),
                    "tier": tier,
                    "tier_label": self._tier_label(tier),
                    "phone": r.get("phone", None),
                    "email": r.get("email", None),
                }
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": (offset + limit) < total,
        }

    def get_contact_detail(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Return single contact detail."""
        rows = self._query(
            "SELECT * FROM contacts WHERE id = ? OR contact_id = ? LIMIT 1",
            (contact_id, contact_id),
        )
        if not rows:
            return None
        r = rows[0]
        tier = r.get("tier") or r.get("contact_tier") or 6
        try:
            tier = int(tier)
        except (ValueError, TypeError):
            tier = 6
        return {
            "id": str(r.get("id", r.get("contact_id", ""))),
            "name": r.get("name", r.get("first_name", "")),
            "company": r.get("company", r.get("company_name", "")),
            "title": r.get("title", r.get("job_title", "")),
            "tier": tier,
            "tier_label": self._tier_label(tier),
            "phone": r.get("phone", None),
            "email": r.get("email", None),
            "program": r.get("program", ""),
            "last_contacted": r.get("last_contacted", None),
            "notes": r.get("notes", None),
        }

    # ------------------------------------------------------------------
    # Programs
    # ------------------------------------------------------------------

    def get_programs(self, limit: int = 20, page: int = 1) -> Dict[str, Any]:
        """Return paginated program list."""
        offset = (max(1, page) - 1) * limit

        total = 0
        try:
            total = self._count("programs")
        except Exception:
            pass

        rows = self._query(
            "SELECT * FROM programs ORDER BY name LIMIT ? OFFSET ?",
            (limit, offset),
        )

        items = []
        for r in rows:
            items.append(
                {
                    "id": str(r.get("id", r.get("program_id", ""))),
                    "name": r.get("name", r.get("program_name", "")),
                    "agency": r.get("agency", ""),
                    "value": r.get("value", r.get("contract_value", "")),
                    "score": r.get("score", r.get("bd_score", None)),
                }
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": (offset + limit) < total,
        }

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------

    def get_alerts(self, limit: int = 10) -> Dict[str, Any]:
        """Return recent alerts.  Synthesised from score changes, new contacts, etc."""
        alerts: List[Dict[str, Any]] = []

        # Try to pull recent high-score contacts as "hot lead" alerts
        rows = self._query(
            "SELECT * FROM contacts WHERE bd_score >= ? ORDER BY bd_score DESC LIMIT ?",
            (HOT_THRESHOLD, limit),
        )
        for r in rows:
            alerts.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "new_opportunity",
                    "title": f"Hot lead: {r.get('name', 'Unknown')}",
                    "summary": f"BD score {r.get('bd_score', 0)} at {r.get('company', 'N/A')}",
                    "created_at": datetime.now(UTC).isoformat(),
                    "priority": "high",
                }
            )

        return {"items": alerts[:limit], "total": len(alerts)}

    # ------------------------------------------------------------------
    # Unified search
    # ------------------------------------------------------------------

    def search(self, q: str, limit: int = 10) -> Dict[str, Any]:
        """Unified search across contacts and programs."""
        results: List[Dict[str, Any]] = []
        param = f"%{q}%"

        # Search contacts
        contact_rows = self._query(
            "SELECT * FROM contacts WHERE name LIKE ? OR company LIKE ? LIMIT ?",
            (param, param, limit),
        )
        for r in contact_rows:
            results.append(
                {
                    "id": str(r.get("id", r.get("contact_id", ""))),
                    "type": "contact",
                    "title": r.get("name", ""),
                    "subtitle": r.get("company", ""),
                    "score": r.get("bd_score", None),
                }
            )

        # Search programs
        remaining = max(0, limit - len(results))
        if remaining > 0:
            try:
                prog_rows = self._query(
                    "SELECT * FROM programs WHERE name LIKE ? OR agency LIKE ? LIMIT ?",
                    (param, param, remaining),
                )
                for r in prog_rows:
                    results.append(
                        {
                            "id": str(r.get("id", r.get("program_id", ""))),
                            "type": "program",
                            "title": r.get("name", r.get("program_name", "")),
                            "subtitle": r.get("agency", ""),
                            "score": r.get("bd_score", None),
                        }
                    )
            except Exception:
                pass

        return {"items": results[:limit], "total": len(results), "query": q}
