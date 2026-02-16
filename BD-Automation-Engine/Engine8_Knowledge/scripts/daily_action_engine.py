"""
Daily Action Engine
===================

Generates prioritized daily call sheets with full contact context.
Queries Qdrant for Tier 1-3 contacts, cross-references Bullhorn activity,
applies BD scoring, and produces ranked daily actions.

Usage:
    from scripts.daily_action_engine import DailyActionEngine
    engine = DailyActionEngine(store)
    playbook = engine.generate_daily_playbook()
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DailyActionEngine:
    """Generates prioritized daily BD actions from indexed data."""

    def __init__(self, store, memory=None):
        """
        Args:
            store: BDKnowledgeStore instance (Qdrant)
            memory: Optional MemoryLayer instance
        """
        self.store = store
        self.memory = memory
        self.max_daily_actions = 30

    def generate_daily_playbook(
        self,
        target_date: Optional[str] = None,
        max_actions: int = None,
    ) -> Dict[str, Any]:
        """
        Generate a prioritized daily playbook.

        Args:
            target_date: ISO date string (default: today)
            max_actions: Override max actions per day

        Returns:
            Complete daily playbook with tasks, stats, and metadata
        """
        max_actions = max_actions or self.max_daily_actions
        target = target_date or datetime.now().strftime("%Y-%m-%d")

        tasks = []
        errors = []

        # Stage 1: Get high-priority contacts needing outreach
        try:
            contact_tasks = self._generate_contact_tasks(max_actions)
            tasks.extend(contact_tasks)
        except Exception as e:
            logger.error(f"Contact task generation failed: {e}")
            errors.append(f"contacts: {e}")

        # Stage 2: Get program-driven tasks (recompetes, new opportunities)
        try:
            program_tasks = self._generate_program_tasks(
                max(5, max_actions - len(tasks))
            )
            tasks.extend(program_tasks)
        except Exception as e:
            logger.error(f"Program task generation failed: {e}")
            errors.append(f"programs: {e}")

        # Stage 3: Get job-driven tasks (new positions to investigate)
        try:
            job_tasks = self._generate_job_tasks(max(5, max_actions - len(tasks)))
            tasks.extend(job_tasks)
        except Exception as e:
            logger.error(f"Job task generation failed: {e}")
            errors.append(f"jobs: {e}")

        # Sort by priority score (highest first)
        tasks.sort(key=lambda t: t.get("priority_score", 0), reverse=True)

        # Trim to max
        tasks = tasks[:max_actions]

        # Assign time slots
        tasks = self._assign_time_slots(tasks)

        # Build stats
        stats = self._compute_stats(tasks)

        return {
            "date": target,
            "generated_at": datetime.now().isoformat(),
            "tasks": tasks,
            "stats": stats,
            "errors": errors,
            "total": len(tasks),
        }

    def _generate_contact_tasks(self, limit: int = 20) -> List[Dict]:
        """Generate outreach tasks from high-priority contacts."""
        tasks = []

        # Search for Tier 1-3 contacts
        for tier_query in [
            "Tier 1 executive decision maker",
            "Tier 2 director program leader",
            "Tier 3 manager technical lead",
        ]:
            try:
                results = self.store.search(
                    query=tier_query,
                    collection="contacts",
                    limit=limit,
                    score_threshold=0.3,
                )

                for result in results:
                    payload = (
                        result.payload
                        if hasattr(result, "payload")
                        else result.get("payload", {})
                    )
                    name = payload.get("name", "Unknown")
                    company = payload.get("company", "")
                    title = payload.get("title", "")
                    tier = payload.get("tier", 5)
                    bd_priority = payload.get("bd_priority", "")
                    program = payload.get("program", payload.get("program_name", ""))

                    # Calculate priority score
                    priority_score = self._calculate_contact_priority(payload)

                    # Determine task type based on tier
                    if isinstance(tier, (int, float)) and tier <= 2:
                        task_type = "call"
                        priority = "critical" if priority_score >= 80 else "high"
                    elif isinstance(tier, (int, float)) and tier <= 3:
                        task_type = "call"
                        priority = "high" if priority_score >= 60 else "medium"
                    else:
                        task_type = "email"
                        priority = "medium" if priority_score >= 50 else "low"

                    task = {
                        "id": f"contact-{hash(name) % 100000}",
                        "type": task_type,
                        "priority": priority,
                        "priority_score": priority_score,
                        "title": f"{'Call' if task_type == 'call' else 'Email'} {name} — {title}",
                        "description": f"{'Executive outreach' if tier <= 2 else 'Follow-up'} with {name} at {company}"
                        + (f" re: {program}" if program else ""),
                        "contact": name,
                        "contact_id": str(result.id)
                        if hasattr(result, "id")
                        else payload.get("id", ""),
                        "company": company,
                        "program": program,
                        "tier": tier,
                        "bd_priority": bd_priority,
                        "source_type": "contact",
                        "completed": False,
                    }
                    tasks.append(task)

            except Exception as e:
                logger.warning(f"Contact search failed for '{tier_query}': {e}")

        # Deduplicate by contact name
        seen = set()
        unique_tasks = []
        for task in tasks:
            key = task["contact"]
            if key not in seen:
                seen.add(key)
                unique_tasks.append(task)

        return unique_tasks[:limit]

    def _generate_program_tasks(self, limit: int = 10) -> List[Dict]:
        """Generate tasks from program opportunities."""
        tasks = []

        queries = [
            "DCGS recompete opportunity",
            "new contract award ISR intelligence",
            "program expansion defense",
        ]

        for query in queries:
            try:
                results = self.store.search(
                    query=query,
                    collection="programs",
                    limit=5,
                    score_threshold=0.3,
                )

                for result in results:
                    payload = (
                        result.payload
                        if hasattr(result, "payload")
                        else result.get("payload", {})
                    )
                    name = payload.get("name", payload.get("program_name", "Unknown"))
                    agency = payload.get("agency", "")
                    prime = payload.get("prime_contractor", "")

                    task = {
                        "id": f"program-{hash(name) % 100000}",
                        "type": "research",
                        "priority": "high",
                        "priority_score": 65,
                        "title": f"Research {name} opportunity",
                        "description": f"Investigate {name}"
                        + (f" ({agency})" if agency else "")
                        + (f" — Prime: {prime}" if prime else ""),
                        "program": name,
                        "program_id": str(result.id) if hasattr(result, "id") else "",
                        "source_type": "program",
                        "completed": False,
                    }
                    tasks.append(task)

            except Exception as e:
                logger.warning(f"Program search failed for '{query}': {e}")

        # Deduplicate
        seen = set()
        unique = []
        for t in tasks:
            if t["program"] not in seen:
                seen.add(t["program"])
                unique.append(t)

        return unique[:limit]

    def _generate_job_tasks(self, limit: int = 10) -> List[Dict]:
        """Generate tasks from recent job intelligence."""
        tasks = []

        try:
            results = self.store.search(
                query="new job posting defense intelligence clearance",
                collection="jobs",
                limit=limit,
                score_threshold=0.3,
            )

            for result in results:
                payload = (
                    result.payload
                    if hasattr(result, "payload")
                    else result.get("payload", {})
                )
                title = payload.get("title", "Unknown Position")
                company = payload.get("company", "")
                program = payload.get("program_name", payload.get("mapped_program", ""))
                bd_score = payload.get("bd_priority_score", payload.get("bd_score", 50))

                if isinstance(bd_score, str):
                    try:
                        bd_score = float(bd_score)
                    except ValueError:
                        bd_score = 50

                priority = (
                    "high" if bd_score >= 70 else "medium" if bd_score >= 40 else "low"
                )

                task = {
                    "id": f"job-{hash(title) % 100000}",
                    "type": "research",
                    "priority": priority,
                    "priority_score": bd_score,
                    "title": f"Investigate: {title} at {company}",
                    "description": f"New opening indicates staffing need"
                    + (f" on {program}" if program else ""),
                    "company": company,
                    "program": program,
                    "job_id": str(result.id) if hasattr(result, "id") else "",
                    "source_type": "job",
                    "completed": False,
                }
                tasks.append(task)

        except Exception as e:
            logger.warning(f"Job search failed: {e}")

        return tasks[:limit]

    def _calculate_contact_priority(self, payload: Dict) -> float:
        """Calculate priority score for a contact (0-100)."""
        score = 50.0

        # Tier boost
        tier = payload.get("tier", 5)
        if isinstance(tier, (int, float)):
            tier_boosts = {1: 30, 2: 25, 3: 20, 4: 10, 5: 5, 6: 0}
            score += tier_boosts.get(int(tier), 0)

        # Clearance boost
        clearance = str(payload.get("clearance", "")).lower()
        if "ts/sci" in clearance and "poly" in clearance:
            score += 15
        elif "ts/sci" in clearance:
            score += 10
        elif "top secret" in clearance:
            score += 5

        # Program boost
        program = str(payload.get("program", payload.get("program_name", ""))).lower()
        if "dcgs" in program:
            score += 10
        elif any(kw in program for kw in ["isr", "sigint", "geoint"]):
            score += 5

        # BD priority
        bd = str(payload.get("bd_priority", "")).lower()
        if bd == "hot":
            score += 10
        elif bd == "warm":
            score += 5

        return min(score, 100.0)

    def _assign_time_slots(self, tasks: List[Dict]) -> List[Dict]:
        """Assign suggested time slots to tasks."""
        time_map = {
            "call": [
                "09:00",
                "09:30",
                "10:00",
                "10:30",
                "11:00",
                "14:00",
                "14:30",
                "15:00",
            ],
            "email": ["08:00", "08:15", "08:30", "12:00", "16:00", "16:30"],
            "meeting": ["11:00", "13:00", "14:00", "15:00"],
            "research": ["13:00", "15:00", "16:00"],
            "follow-up": ["11:30", "15:30", "16:30"],
        }

        type_counters = {}
        for task in tasks:
            task_type = task.get("type", "research")
            idx = type_counters.get(task_type, 0)
            slots = time_map.get(task_type, ["09:00"])
            task["time"] = slots[idx % len(slots)]
            type_counters[task_type] = idx + 1

        return tasks

    def _compute_stats(self, tasks: List[Dict]) -> Dict:
        """Compute playbook statistics."""
        by_priority = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_type = {"call": 0, "email": 0, "meeting": 0, "research": 0, "follow-up": 0}

        for task in tasks:
            p = task.get("priority", "low")
            t = task.get("type", "research")
            by_priority[p] = by_priority.get(p, 0) + 1
            by_type[t] = by_type.get(t, 0) + 1

        return {
            "total": len(tasks),
            "completed": sum(1 for t in tasks if t.get("completed")),
            "byPriority": by_priority,
            "byType": by_type,
        }
