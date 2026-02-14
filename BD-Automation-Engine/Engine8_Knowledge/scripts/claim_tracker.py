"""
Contract Claim Tracker
======================

Tracks "claimed" vs "unclaimed" contracts/programs.

A contract is "claimed" when:
- At least 1 contact in Bullhorn is associated with it
- AND at least 1 outreach action has been logged

Provides:
- Claimed/unclaimed counts per program
- Velocity metrics (claims per week)
- Highest-value unclaimed contracts prioritization

Usage:
    from scripts.claim_tracker import ClaimTracker
    tracker = ClaimTracker(store)
    status = tracker.get_claim_status()
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class ClaimTracker:
    """Tracks contract claim status across the BD pipeline."""

    def __init__(self, store, memory=None):
        """
        Args:
            store: BDKnowledgeStore instance
            memory: Optional MemoryLayer instance
        """
        self.store = store
        self.memory = memory

    def get_claim_status(self) -> Dict[str, Any]:
        """
        Get overall claim status across all programs.

        Returns:
            Claim status summary with counts, programs, velocity
        """
        programs = self._get_all_programs()
        contacts_by_program = self._get_contacts_by_program()
        activities_by_program = self._get_activities_by_program()

        claimed = []
        unclaimed = []

        for program in programs:
            name = program.get("name", "")
            has_contacts = name in contacts_by_program and contacts_by_program[name] > 0
            has_outreach = name in activities_by_program and activities_by_program[name] > 0

            status = {
                "program": name,
                "agency": program.get("agency", ""),
                "prime": program.get("prime_contractor", ""),
                "value": program.get("value", program.get("contract_value", "")),
                "contacts_count": contacts_by_program.get(name, 0),
                "outreach_count": activities_by_program.get(name, 0),
                "is_claimed": has_contacts and has_outreach,
            }

            if status["is_claimed"]:
                claimed.append(status)
            else:
                unclaimed.append(status)

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_programs": len(programs),
                "claimed": len(claimed),
                "unclaimed": len(unclaimed),
                "claim_rate": round(len(claimed) / max(len(programs), 1), 3),
            },
            "claimed": sorted(claimed, key=lambda x: x["outreach_count"], reverse=True),
            "unclaimed": sorted(unclaimed, key=lambda x: x["contacts_count"], reverse=True),
        }

    def get_unclaimed_priority(self, limit: int = 20) -> List[Dict]:
        """
        Get highest-priority unclaimed contracts.

        Prioritized by:
        1. Has contacts but no outreach (warm leads)
        2. High-value programs
        3. Programs with many contacts (more entry points)

        Returns:
            Prioritized list of unclaimed opportunities
        """
        status = self.get_claim_status()
        unclaimed = status["unclaimed"]

        # Score unclaimed items
        for item in unclaimed:
            score = 0

            # Contacts exist but no outreach = warm lead
            if item["contacts_count"] > 0:
                score += 50 + min(item["contacts_count"] * 5, 30)

            # Value parsing
            value_str = str(item.get("value", ""))
            try:
                value = float(value_str.replace("$", "").replace(",", "").replace("M", "000000").replace("B", "000000000"))
                if value > 100_000_000:
                    score += 20
                elif value > 10_000_000:
                    score += 10
            except (ValueError, TypeError):
                pass

            # DCGS/priority programs
            name = item.get("program", "").lower()
            if "dcgs" in name:
                score += 15
            elif any(kw in name for kw in ["isr", "sigint", "geoint"]):
                score += 10

            item["priority_score"] = score

        unclaimed.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        return unclaimed[:limit]

    def get_velocity(self, days: int = 30) -> Dict:
        """
        Get claim velocity metrics.

        Returns claims per week over the specified period.
        """
        # Search for recent outreach activities
        claims_by_week = defaultdict(int)

        try:
            results = self.store.search(
                query="outreach call email meeting contact",
                collection="activities",
                limit=100,
                score_threshold=0.2,
            )

            for r in results:
                payload = r.payload if hasattr(r, "payload") else r.get("payload", {})
                date_str = payload.get("date", payload.get("activity_date", ""))
                if date_str:
                    try:
                        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        week_key = dt.strftime("%Y-W%W")
                        claims_by_week[week_key] += 1
                    except (ValueError, TypeError):
                        pass

        except Exception as e:
            logger.warning(f"Velocity calculation failed: {e}")

        weeks_sorted = sorted(claims_by_week.items())
        total_activities = sum(claims_by_week.values())
        num_weeks = max(len(claims_by_week), 1)

        return {
            "period_days": days,
            "total_outreach_activities": total_activities,
            "avg_per_week": round(total_activities / num_weeks, 1),
            "by_week": dict(weeks_sorted[-8:]),  # Last 8 weeks
        }

    def _get_all_programs(self) -> List[Dict]:
        """Get all programs from Qdrant."""
        programs = []
        try:
            # Scroll through programs collection
            results = self.store.search(
                query="federal program contract defense intelligence",
                collection="programs",
                limit=100,
                score_threshold=0.1,
            )
            for r in results:
                payload = r.payload if hasattr(r, "payload") else r.get("payload", {})
                programs.append({
                    "name": payload.get("name", payload.get("program_name", "")),
                    "agency": payload.get("agency", ""),
                    "prime_contractor": payload.get("prime_contractor", ""),
                    "value": payload.get("value", payload.get("contract_value", "")),
                })
        except Exception as e:
            logger.warning(f"Program fetch failed: {e}")

        return programs

    def _get_contacts_by_program(self) -> Dict[str, int]:
        """Count contacts per program."""
        counts = defaultdict(int)
        try:
            results = self.store.search(
                query="contact program defense",
                collection="contacts",
                limit=200,
                score_threshold=0.1,
            )
            for r in results:
                payload = r.payload if hasattr(r, "payload") else r.get("payload", {})
                program = payload.get("program", payload.get("program_name", ""))
                if program:
                    counts[program] += 1
        except Exception as e:
            logger.warning(f"Contact count failed: {e}")

        return dict(counts)

    def _get_activities_by_program(self) -> Dict[str, int]:
        """Count outreach activities per program."""
        counts = defaultdict(int)
        try:
            results = self.store.search(
                query="outreach call meeting email note",
                collection="activities",
                limit=200,
                score_threshold=0.1,
            )
            for r in results:
                payload = r.payload if hasattr(r, "payload") else r.get("payload", {})
                # Try to match to program
                content = str(payload.get("content", ""))
                company = payload.get("company", payload.get("company_name", ""))

                # Count by company as proxy for program
                if company:
                    counts[company] += 1
        except Exception as e:
            logger.warning(f"Activity count failed: {e}")

        return dict(counts)
