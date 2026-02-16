"""
Recompete Predictor
====================

Flags contracts expiring within configurable horizons (6/12/18 months),
cross-references with PTS past performance, and generates prioritized
recompete alerts that feed into the daily action engine.

Usage:
    from scripts.recompete_predictor import RecompetePredictor
    predictor = RecompetePredictor(store)
    alerts = predictor.get_recompete_predictions(months=12)
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Paths to external databases
PROJECT_ROOT = Path(__file__).parent.parent.parent
BULLHORN_DB = PROJECT_ROOT / "Engine7_BullhornETL" / "data" / "bullhorn.db"
N8N_PROGRAMS_DB = Path("C:/Auto-Claud/N8N-Builder/data/federal_programs.db")

# PTS past performance keywords (contracts PTS has delivered on)
PTS_PAST_PERFORMANCE_KEYWORDS = [
    "dcgs",
    "distributed common ground",
    "geoint",
    "sigint",
    "isr",
    "intelligence surveillance",
    "c4isr",
    "elint",
    "masint",
    "humint",
    "osint",
    "fusion",
    "targeting",
    "air force",
    "usaf",
    "navy",
    "army",
    "raytheon",
    "northrop grumman",
    "leidos",
    "gdit",
    "saic",
    "bae systems",
    "l3harris",
    "peraton",
]


class RecompetePredictor:
    """Predicts upcoming recompete opportunities from program expiry data."""

    def __init__(self, store, memory=None):
        """
        Args:
            store: BDKnowledgeStore instance (Qdrant)
            memory: Optional MemoryLayer instance
        """
        self.store = store
        self.memory = memory

    def get_recompete_predictions(
        self,
        months: int = 12,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get contracts/programs expiring within the specified horizon.

        Combines data from:
        1. Qdrant programs collection (indexed program data)
        2. N8N-Builder federal_programs.db (30,800 rows of federal programs)
        3. Bullhorn program records

        Args:
            months: Look-ahead window in months
            limit: Max results

        Returns:
            Dict with recompetes list, total count, and total value
        """
        horizon = datetime.now() + timedelta(days=months * 30)
        today = datetime.now()

        recompetes = []

        # Source 1: Qdrant programs collection
        qdrant_recompetes = self._search_qdrant_programs(today, horizon)
        recompetes.extend(qdrant_recompetes)

        # Source 2: N8N-Builder federal_programs.db
        fed_recompetes = self._search_federal_programs_db(today, horizon)
        recompetes.extend(fed_recompetes)

        # Source 3: Bullhorn program data
        bullhorn_recompetes = self._search_bullhorn_programs(today, horizon)
        recompetes.extend(bullhorn_recompetes)

        # Deduplicate by program name (case-insensitive)
        seen = set()
        unique = []
        for r in recompetes:
            key = r["program"].lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(r)

        # Cross-reference with PTS past performance
        for r in unique:
            r["pts_past_performance"] = self._check_pts_past_performance(r)

        # Assign priority based on months remaining + value + PTS PP
        for r in unique:
            r["priority"] = self._calculate_priority(r)

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        unique.sort(
            key=lambda x: (
                priority_order.get(x["priority"], 9),
                x.get("months_remaining", 999),
            )
        )

        unique = unique[:limit]

        total_value = sum(
            r.get("value", 0)
            for r in unique
            if isinstance(r.get("value"), (int, float))
        )

        return {
            "recompetes": unique,
            "total": len(unique),
            "total_value": total_value,
            "horizon_months": months,
            "generated_at": datetime.now().isoformat(),
        }

    def get_recompete_alerts_for_playbook(
        self,
        months: int = 12,
        max_alerts: int = 5,
    ) -> List[Dict]:
        """
        Generate daily playbook tasks from upcoming recompetes.

        Returns tasks formatted for the DailyActionEngine.
        """
        predictions = self.get_recompete_predictions(
            months=months, limit=max_alerts * 2
        )
        tasks = []

        for r in predictions["recompetes"][:max_alerts]:
            months_left = r.get("months_remaining", 99)
            program = r.get("program", "Unknown")
            incumbent = r.get("incumbent", "")

            if months_left <= 6:
                priority = "critical"
                task_type = "call"
                desc = f"URGENT recompete in {months_left}mo — research incumbent {incumbent}, prepare capability brief"
            elif months_left <= 12:
                priority = "high"
                task_type = "research"
                desc = f"Recompete in {months_left}mo — identify contacts, gather intel on {program}"
            else:
                priority = "medium"
                task_type = "research"
                desc = (
                    f"Upcoming recompete in {months_left}mo — add to tracking pipeline"
                )

            tasks.append(
                {
                    "id": f"recompete-{hash(program) % 100000}",
                    "type": task_type,
                    "priority": priority,
                    "priority_score": max(100 - months_left * 4, 20),
                    "title": f"Recompete: {program}",
                    "description": desc,
                    "program": program,
                    "months_remaining": months_left,
                    "incumbent": incumbent,
                    "value": r.get("value", 0),
                    "pts_past_performance": r.get("pts_past_performance", False),
                    "source_type": "recompete",
                    "completed": False,
                }
            )

        return tasks

    # ── Data sources ──────────────────────────────────────────────────────

    def _search_qdrant_programs(self, today: datetime, horizon: datetime) -> List[Dict]:
        """Search Qdrant programs collection for expiring contracts."""
        results = []
        queries = [
            "contract expiration recompete renewal",
            "period of performance end date",
            "option year final",
        ]

        for query in queries:
            try:
                hits = self.store.search(
                    query=query,
                    collection="programs",
                    limit=50,
                    score_threshold=0.2,
                )
                for hit in hits:
                    payload = (
                        hit.payload
                        if hasattr(hit, "payload")
                        else hit.get("payload", {})
                    )
                    expiry = self._parse_expiry(payload)
                    if expiry and today <= expiry <= horizon:
                        months_remaining = max(1, (expiry - today).days // 30)
                        results.append(
                            {
                                "program": payload.get(
                                    "name", payload.get("program_name", "Unknown")
                                ),
                                "expiry_date": expiry.strftime("%Y-%m-%d"),
                                "months_remaining": months_remaining,
                                "value": self._parse_value(
                                    payload.get(
                                        "value", payload.get("contract_value", 0)
                                    )
                                ),
                                "incumbent": payload.get(
                                    "prime_contractor", payload.get("incumbent", "")
                                ),
                                "agency": payload.get("agency", ""),
                                "source": "qdrant",
                            }
                        )
            except Exception as e:
                logger.warning(f"Qdrant recompete search failed for '{query}': {e}")

        return results

    def _search_federal_programs_db(
        self, today: datetime, horizon: datetime
    ) -> List[Dict]:
        """Search N8N-Builder's federal_programs.db for expiring contracts."""
        results = []
        if not N8N_PROGRAMS_DB.exists():
            logger.debug("federal_programs.db not found at %s", N8N_PROGRAMS_DB)
            return results

        try:
            conn = sqlite3.connect(str(N8N_PROGRAMS_DB))
            conn.row_factory = sqlite3.Row

            # Try common column names for expiry dates
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t["name"] for t in tables]

            for table in table_names:
                cols = [
                    row["name"]
                    for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
                ]

                date_cols = [
                    c
                    for c in cols
                    if any(
                        kw in c.lower()
                        for kw in [
                            "end_date",
                            "expir",
                            "pop_end",
                            "period_end",
                            "completion",
                            "ultimate_completion",
                        ]
                    )
                ]

                if not date_cols:
                    continue

                name_col = next(
                    (
                        c
                        for c in cols
                        if any(
                            kw in c.lower()
                            for kw in ["name", "program", "title", "description"]
                        )
                    ),
                    None,
                )
                value_col = next(
                    (
                        c
                        for c in cols
                        if any(
                            kw in c.lower()
                            for kw in ["value", "amount", "dollars", "obligated"]
                        )
                    ),
                    None,
                )
                company_col = next(
                    (
                        c
                        for c in cols
                        if any(
                            kw in c.lower()
                            for kw in ["vendor", "contractor", "recipient", "company"]
                        )
                    ),
                    None,
                )
                agency_col = next(
                    (
                        c
                        for c in cols
                        if any(
                            kw in c.lower()
                            for kw in ["agency", "department", "awarding"]
                        )
                    ),
                    None,
                )

                for date_col in date_cols:
                    try:
                        rows = conn.execute(
                            f"SELECT * FROM {table} WHERE {date_col} IS NOT NULL "
                            f"AND {date_col} != '' LIMIT 500"
                        ).fetchall()

                        for row in rows:
                            d = dict(row)
                            expiry = self._parse_date_string(str(d.get(date_col, "")))
                            if expiry and today <= expiry <= horizon:
                                months_remaining = max(1, (expiry - today).days // 30)
                                results.append(
                                    {
                                        "program": str(d.get(name_col, ""))
                                        if name_col
                                        else f"Contract in {table}",
                                        "expiry_date": expiry.strftime("%Y-%m-%d"),
                                        "months_remaining": months_remaining,
                                        "value": self._parse_value(d.get(value_col, 0))
                                        if value_col
                                        else 0,
                                        "incumbent": str(d.get(company_col, ""))
                                        if company_col
                                        else "",
                                        "agency": str(d.get(agency_col, ""))
                                        if agency_col
                                        else "",
                                        "source": f"federal_programs/{table}",
                                    }
                                )
                    except Exception as e:
                        logger.debug(
                            "Table %s col %s scan failed: %s", table, date_col, e
                        )

            conn.close()
        except Exception as e:
            logger.warning("federal_programs.db scan failed: %s", e)

        return results

    def _search_bullhorn_programs(
        self, today: datetime, horizon: datetime
    ) -> List[Dict]:
        """Search Bullhorn DB for program/contract expiry dates."""
        results = []
        if not BULLHORN_DB.exists():
            logger.debug("bullhorn.db not found at %s", BULLHORN_DB)
            return results

        try:
            conn = sqlite3.connect(str(BULLHORN_DB))
            conn.row_factory = sqlite3.Row

            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()

            for table_row in tables:
                table = table_row["name"]
                cols = [
                    row["name"]
                    for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
                ]

                date_cols = [
                    c
                    for c in cols
                    if any(
                        kw in c.lower()
                        for kw in ["enddate", "end_date", "expirationdate"]
                    )
                ]

                if not date_cols:
                    continue

                name_col = next(
                    (
                        c
                        for c in cols
                        if any(
                            kw in c.lower() for kw in ["name", "title", "description"]
                        )
                    ),
                    None,
                )

                for date_col in date_cols:
                    try:
                        rows = conn.execute(
                            f"SELECT * FROM {table} WHERE {date_col} IS NOT NULL "
                            f"AND {date_col} != '' LIMIT 200"
                        ).fetchall()

                        for row in rows:
                            d = dict(row)
                            expiry = self._parse_date_string(str(d.get(date_col, "")))
                            if expiry and today <= expiry <= horizon:
                                months_remaining = max(1, (expiry - today).days // 30)
                                results.append(
                                    {
                                        "program": str(d.get(name_col, ""))
                                        if name_col
                                        else f"Bullhorn/{table}",
                                        "expiry_date": expiry.strftime("%Y-%m-%d"),
                                        "months_remaining": months_remaining,
                                        "value": 0,
                                        "incumbent": "",
                                        "agency": "",
                                        "source": f"bullhorn/{table}",
                                    }
                                )
                    except Exception:
                        pass

            conn.close()
        except Exception as e:
            logger.warning("Bullhorn DB recompete scan failed: %s", e)

        return results

    # ── Helpers ────────────────────────────────────────────────────────────

    def _parse_expiry(self, payload: Dict) -> Optional[datetime]:
        """Extract expiry/end date from a Qdrant program payload."""
        for key in [
            "end_date",
            "expiry_date",
            "pop_end",
            "period_of_performance_end",
            "completion_date",
            "contract_end",
            "expiration",
        ]:
            val = payload.get(key)
            if val:
                parsed = self._parse_date_string(str(val))
                if parsed:
                    return parsed
        return None

    @staticmethod
    def _parse_date_string(date_str: str) -> Optional[datetime]:
        """Parse various date formats."""
        if not date_str or date_str.lower() in ("none", "null", ""):
            return None

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%SZ",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%d-%b-%Y",
            "%B %d, %Y",
            "%Y%m%d",
        ]

        # Handle epoch timestamps
        try:
            ts = float(date_str)
            if ts > 1e12:
                ts /= 1000
            if 1e9 < ts < 2e9:
                return datetime.fromtimestamp(ts)
        except (ValueError, TypeError, OSError):
            pass

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip()[:20], fmt)
            except (ValueError, TypeError):
                continue

        return None

    @staticmethod
    def _parse_value(value) -> float:
        """Parse contract value from various formats."""
        if isinstance(value, (int, float)):
            return float(value)
        if not value:
            return 0.0
        try:
            cleaned = str(value).replace("$", "").replace(",", "").strip()
            if cleaned.upper().endswith("M"):
                return float(cleaned[:-1]) * 1_000_000
            elif cleaned.upper().endswith("B"):
                return float(cleaned[:-1]) * 1_000_000_000
            elif cleaned.upper().endswith("K"):
                return float(cleaned[:-1]) * 1_000
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _check_pts_past_performance(recompete: Dict) -> bool:
        """Check if PTS has past performance relevant to this program."""
        searchable = " ".join(
            [
                str(recompete.get("program", "")),
                str(recompete.get("incumbent", "")),
                str(recompete.get("agency", "")),
            ]
        ).lower()

        return any(kw in searchable for kw in PTS_PAST_PERFORMANCE_KEYWORDS)

    @staticmethod
    def _calculate_priority(recompete: Dict) -> str:
        """Calculate recompete priority level."""
        months = recompete.get("months_remaining", 99)
        has_pp = recompete.get("pts_past_performance", False)
        value = recompete.get("value", 0)

        # Critical: expiring within 6 months with PTS PP or high value
        if months <= 6:
            return "critical"

        # High: 6-12 months, or under 6 months without PP
        if months <= 12 and (has_pp or value > 50_000_000):
            return "high"

        if months <= 12:
            return "medium"

        # Beyond 12 months
        if has_pp and value > 100_000_000:
            return "high"

        return "low"

    def get_best_channels(self) -> Dict[str, Any]:
        """Analyze outreach outcomes to determine best channels.

        Queries Qdrant activities collection for outreach records and
        computes per-channel success rates.

        Returns:
            Dict with channels list and AI recommendation.
        """
        channel_stats: Dict[str, Dict] = {}

        try:
            results = self.store.search(
                query="outreach email call linkedin meeting response",
                collection="activities",
                limit=200,
                score_threshold=0.15,
            )

            for r in results:
                payload = r.payload if hasattr(r, "payload") else r.get("payload", {})
                content = str(payload.get("content", payload.get("notes", ""))).lower()
                action = str(payload.get("action", payload.get("type", ""))).lower()

                # Determine channel
                if any(kw in action or kw in content for kw in ["email", "e-mail"]):
                    ch = "email"
                elif any(
                    kw in action or kw in content
                    for kw in ["call", "phone", "voicemail"]
                ):
                    ch = "phone"
                elif any(
                    kw in action or kw in content for kw in ["linkedin", "inmail"]
                ):
                    ch = "linkedin"
                else:
                    ch = "email"

                if ch not in channel_stats:
                    channel_stats[ch] = {
                        "total": 0,
                        "success": 0,
                        "response_days_sum": 0,
                    }

                channel_stats[ch]["total"] += 1

                # Check for success signals
                if any(
                    kw in content
                    for kw in [
                        "replied",
                        "responded",
                        "meeting",
                        "scheduled",
                        "booked",
                        "interested",
                    ]
                ):
                    channel_stats[ch]["success"] += 1

        except Exception as e:
            logger.warning("Best channels analysis failed: %s", e)

        # Build results
        channels = []
        for ch, stats in channel_stats.items():
            total = stats["total"]
            success = stats["success"]
            channels.append(
                {
                    "channel": ch,
                    "total": total,
                    "success_rate": round(success / max(total, 1), 3),
                    "avg_response_days": round(
                        stats["response_days_sum"] / max(success, 1), 1
                    ),
                }
            )

        channels.sort(key=lambda x: -x["success_rate"])

        # Generate recommendation
        if channels:
            best = channels[0]
            recommendation = (
                f"Best performing channel is {best['channel']} "
                f"with {best['success_rate']:.0%} success rate across "
                f"{best['total']} interactions. "
            )
            if len(channels) > 1:
                recommendation += (
                    f"Consider multi-channel approach combining "
                    f"{channels[0]['channel']} and {channels[1]['channel']}."
                )
        else:
            recommendation = "Insufficient data for channel recommendation. Continue building interaction history."

        return {
            "channels": channels,
            "recommendation": recommendation,
            "data_points": sum(s["total"] for s in channel_stats.values()),
        }
