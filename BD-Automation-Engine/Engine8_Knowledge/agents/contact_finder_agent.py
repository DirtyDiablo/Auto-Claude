"""Contact Finder Agent"""

from typing import Dict, Optional
from .base_agent import BDAgent, AgentResponse


class ContactFinderAgent(BDAgent):
    """Identifies key personnel and decision makers."""

    def __init__(self):
        super().__init__(
            name="Contact Finder Agent",
            description="Identify key personnel for BD opportunities. "
                       "Expert in org structures, clearance levels, decision makers."
        )

    async def process(self, query: str, context: Optional[Dict] = None) -> AgentResponse:
        ctx = await self._get_context(query, ["contacts", "companies", "programs"])

        prompt = f"""Contact finder request:

Query: {query}

Provide:
1. Relevant Contacts
2. Their Roles/Titles
3. Program Affiliations
4. Clearance Levels (if known)
5. Outreach Recommendations"""

        response_text = await self._call_claude(prompt, ctx)

        response = AgentResponse(
            success=True, content=response_text,
            sources=[{"context": ctx[:500]}],
            confidence=0.80, agent_name=self.name,
            metadata={"query": query}
        )
        self._store_interaction(query, response)
        return response

    async def find_decision_makers(self, program: str) -> AgentResponse:
        return await self.process(f"Decision makers for {program}")

    async def find_by_clearance(self, clearance: str, location: str = None) -> AgentResponse:
        q = f"Contacts with {clearance} clearance"
        if location:
            q += f" in {location}"
        return await self.process(q)

    async def find_at_company(self, company: str, role: str = None) -> AgentResponse:
        q = f"Find contacts at {company}"
        if role:
            q += f" in {role} roles"
        return await self.process(q)

    async def find_tier1_contacts(self, program: str = None) -> AgentResponse:
        q = "Find Tier 1 decision maker contacts"
        if program:
            q += f" for {program}"
        return await self.process(q)
