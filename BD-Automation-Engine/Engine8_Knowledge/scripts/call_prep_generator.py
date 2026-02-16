"""
Call Preparation Brief Generator
=================================

Generates comprehensive call prep briefs for BD outreach:
- Contact 360 view (profile, history, network)
- Program intelligence summary
- PTS past performance
- Suggested talking points
- Competitive landscape context

Usage:
    from scripts.call_prep_generator import CallPrepGenerator
    gen = CallPrepGenerator(store)
    brief = gen.generate_brief(contact_id="abc123")
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class CallPrepGenerator:
    """Generates call preparation briefs from indexed BD intelligence."""

    def __init__(self, store, memory=None):
        """
        Args:
            store: BDKnowledgeStore instance
            memory: Optional MemoryLayer instance
        """
        self.store = store
        self.memory = memory

    def generate_brief(
        self,
        contact_id: Optional[str] = None,
        contact_name: Optional[str] = None,
        program_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a complete call preparation brief.

        Args:
            contact_id: Qdrant point ID for the contact
            contact_name: Contact name to search for
            program_name: Optional program context

        Returns:
            Complete call prep brief
        """
        brief = {
            "generated_at": datetime.now().isoformat(),
            "contact": {},
            "program_intel": {},
            "past_performance": [],
            "talking_points": [],
            "competitive_landscape": [],
            "related_contacts": [],
            "recent_activity": [],
        }

        # Resolve contact
        contact = self._resolve_contact(contact_id, contact_name)
        if not contact:
            brief["error"] = "Contact not found"
            return brief

        brief["contact"] = contact

        # Get program intelligence
        program = program_name or contact.get("program", "")
        if program:
            brief["program_intel"] = self._get_program_intel(program)

        # Get PTS past performance
        company = contact.get("company", "")
        if company:
            brief["past_performance"] = self._get_past_performance(company, program)

        # Get competitive landscape
        if program:
            brief["competitive_landscape"] = self._get_competitors(program)

        # Get related contacts at same company/program
        brief["related_contacts"] = self._get_related_contacts(
            contact.get("name", ""), company, program
        )

        # Get recent activity/notes
        brief["recent_activity"] = self._get_recent_activity(
            contact.get("name", ""), company
        )

        # Generate talking points
        brief["talking_points"] = self._generate_talking_points(brief)

        return brief

    def _resolve_contact(
        self,
        contact_id: Optional[str],
        contact_name: Optional[str],
    ) -> Optional[Dict]:
        """Resolve contact by ID or name search."""
        if contact_id:
            try:
                points = self.store.client.retrieve(
                    collection_name="contacts",
                    ids=[contact_id],
                    with_payload=True,
                )
                if points:
                    payload = points[0].payload
                    return {
                        "id": str(points[0].id),
                        "name": payload.get("name", ""),
                        "title": payload.get("title", ""),
                        "company": payload.get("company", ""),
                        "email": payload.get("email", ""),
                        "phone": payload.get("phone", ""),
                        "program": payload.get(
                            "program", payload.get("program_name", "")
                        ),
                        "tier": payload.get("tier", ""),
                        "clearance": payload.get("clearance", ""),
                        "bd_priority": payload.get("bd_priority", ""),
                        "linkedin_url": payload.get("linkedin_url", ""),
                        "notes": payload.get("notes", ""),
                    }
            except Exception as e:
                logger.warning(f"Contact retrieve failed: {e}")

        if contact_name:
            try:
                results = self.store.search(
                    query=contact_name,
                    collection="contacts",
                    limit=1,
                    score_threshold=0.5,
                )
                if results:
                    payload = (
                        results[0].payload
                        if hasattr(results[0], "payload")
                        else results[0].get("payload", {})
                    )
                    return {
                        "id": str(results[0].id) if hasattr(results[0], "id") else "",
                        "name": payload.get("name", contact_name),
                        "title": payload.get("title", ""),
                        "company": payload.get("company", ""),
                        "email": payload.get("email", ""),
                        "phone": payload.get("phone", ""),
                        "program": payload.get(
                            "program", payload.get("program_name", "")
                        ),
                        "tier": payload.get("tier", ""),
                        "clearance": payload.get("clearance", ""),
                        "bd_priority": payload.get("bd_priority", ""),
                    }
            except Exception as e:
                logger.warning(f"Contact search failed: {e}")

        return None

    def _get_program_intel(self, program_name: str) -> Dict:
        """Get program intelligence summary."""
        try:
            results = self.store.search(
                query=program_name,
                collection="programs",
                limit=3,
                score_threshold=0.4,
            )

            if not results:
                return {"name": program_name, "found": False}

            payload = (
                results[0].payload
                if hasattr(results[0], "payload")
                else results[0].get("payload", {})
            )
            return {
                "name": payload.get("name", program_name),
                "agency": payload.get("agency", ""),
                "prime_contractor": payload.get("prime_contractor", ""),
                "value": payload.get("value", payload.get("contract_value", "")),
                "status": payload.get("status", ""),
                "locations": payload.get("locations", ""),
                "clearance": payload.get("clearance", payload.get("clearances", "")),
                "description": payload.get("description", payload.get("content", ""))[
                    :500
                ],
                "found": True,
            }
        except Exception as e:
            logger.warning(f"Program intel failed: {e}")
            return {"name": program_name, "found": False, "error": str(e)}

    def _get_past_performance(self, company: str, program: str = "") -> List[Dict]:
        """Get PTS past performance relevant to the contact's company/program."""
        results_list = []

        queries = [f"past performance {company}"]
        if program:
            queries.append(f"past performance {program}")

        for query in queries:
            try:
                results = self.store.search(
                    query=query,
                    collection="documents",
                    limit=3,
                    score_threshold=0.3,
                )
                for r in results:
                    payload = (
                        r.payload if hasattr(r, "payload") else r.get("payload", {})
                    )
                    results_list.append(
                        {
                            "title": payload.get("title", ""),
                            "summary": payload.get("content", "")[:300],
                            "type": payload.get("doc_type", payload.get("type", "")),
                            "score": round(
                                r.score if hasattr(r, "score") else r.get("score", 0), 3
                            ),
                        }
                    )
            except Exception:
                pass

        return results_list[:5]

    def _get_competitors(self, program_name: str) -> List[Dict]:
        """Get competitive landscape for a program."""
        competitors = []
        try:
            results = self.store.search(
                query=f"competitor {program_name} prime contractor",
                collection="programs",
                limit=5,
                score_threshold=0.3,
            )
            for r in results:
                payload = r.payload if hasattr(r, "payload") else r.get("payload", {})
                prime = payload.get("prime_contractor", payload.get("primes", ""))
                if prime:
                    competitors.append(
                        {
                            "company": prime,
                            "program": payload.get("name", ""),
                            "relationship": "prime",
                        }
                    )
        except Exception:
            pass

        return competitors[:5]

    def _get_related_contacts(
        self, contact_name: str, company: str, program: str
    ) -> List[Dict]:
        """Find related contacts at same company/program."""
        related = []

        if company:
            try:
                results = self.store.search(
                    query=f"{company} contact",
                    collection="contacts",
                    limit=5,
                    score_threshold=0.4,
                )
                for r in results:
                    payload = (
                        r.payload if hasattr(r, "payload") else r.get("payload", {})
                    )
                    name = payload.get("name", "")
                    if name and name != contact_name:
                        related.append(
                            {
                                "name": name,
                                "title": payload.get("title", ""),
                                "company": payload.get("company", ""),
                                "tier": payload.get("tier", ""),
                                "relationship": "same_company",
                            }
                        )
            except Exception:
                pass

        return related[:5]

    def _get_recent_activity(self, contact_name: str, company: str) -> List[Dict]:
        """Get recent activity/notes related to the contact."""
        activities = []

        for query in [contact_name, company]:
            if not query:
                continue
            try:
                results = self.store.search(
                    query=query,
                    collection="activities",
                    limit=3,
                    score_threshold=0.3,
                )
                for r in results:
                    payload = (
                        r.payload if hasattr(r, "payload") else r.get("payload", {})
                    )
                    activities.append(
                        {
                            "subject": payload.get("subject", ""),
                            "type": payload.get("activity_type", ""),
                            "date": payload.get(
                                "date", payload.get("activity_date", "")
                            ),
                            "summary": payload.get("content", "")[:200],
                        }
                    )
            except Exception:
                pass

        return activities[:5]

    def _generate_talking_points(self, brief: Dict) -> List[str]:
        """Generate suggested talking points from brief data."""
        points = []

        contact = brief.get("contact", {})
        program = brief.get("program_intel", {})
        past_perf = brief.get("past_performance", [])

        # Company/program context
        if program.get("found"):
            points.append(
                f"Discuss PTS capabilities relevant to {program.get('name', 'their program')}"
            )

        # Past performance leverage
        if past_perf:
            points.append(
                f"Reference PTS past performance: {past_perf[0].get('title', 'related experience')}"
            )

        # Tier-specific approach
        tier = contact.get("tier", "")
        if isinstance(tier, (int, float)) and tier <= 2:
            points.append(
                "Focus on strategic partnership and executive-level value proposition"
            )
        elif isinstance(tier, (int, float)) and tier <= 3:
            points.append("Discuss technical capabilities and team qualifications")

        # Competitive awareness
        competitors = brief.get("competitive_landscape", [])
        if competitors:
            primes = [c["company"] for c in competitors[:3] if c.get("company")]
            if primes:
                points.append(
                    f"Competitive awareness: {', '.join(primes)} also active in this space"
                )

        # Network leverage
        related = brief.get("related_contacts", [])
        if related:
            points.append(
                f"Mention connection with {related[0].get('name', 'colleague')} ({related[0].get('title', '')})"
            )

        # Default point
        if not points:
            points.append(
                "Introduce PTS capabilities and explore potential collaboration"
            )

        return points
