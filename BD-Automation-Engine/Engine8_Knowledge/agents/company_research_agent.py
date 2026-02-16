"""Company Research Agent"""

from typing import Dict, List, Optional
from .base_agent import BDAgent, AgentResponse


class CompanyResearchAgent(BDAgent):
    """Researches competitors and teaming partners."""

    def __init__(self):
        super().__init__(
            name="Company Research Agent",
            description="Research federal contractors. Expert in prime/sub relationships, "
            "capabilities, teaming history, competitive positioning.",
        )

    async def process(
        self, query: str, context: Optional[Dict] = None
    ) -> AgentResponse:
        ctx = await self._get_context(query, ["companies", "contracts"])

        try:
            network = await self.graph.query(f"Company network: {query}", mode="global")
            ctx += f"\n\n## Network Analysis\n{network}"
        except Exception:
            pass

        prompt = f"""Company research request:

Query: {query}

Provide:
1. Company Profile
2. Contract Portfolio
3. Competitive Position
4. Teaming History
5. BD Implications"""

        response_text = await self._call_claude(prompt, ctx)

        response = AgentResponse(
            success=True,
            content=response_text,
            sources=[{"context": ctx[:500]}],
            confidence=0.82,
            agent_name=self.name,
            metadata={"query": query},
        )
        self._store_interaction(query, response)
        return response

    async def analyze_competitor(self, company: str) -> AgentResponse:
        return await self.process(f"Competitor analysis of {company}")

    async def find_teaming_partners(self, gaps: List[str]) -> AgentResponse:
        return await self.process(f"Find partners for capabilities: {', '.join(gaps)}")

    async def get_contract_history(self, company: str) -> AgentResponse:
        return await self.process(
            f"What contracts has {company} won in the last 3 years?"
        )

    async def compare_companies(self, companies: List[str]) -> AgentResponse:
        return await self.process(f"Compare these companies: {', '.join(companies)}")
