"""BD Strategy Agent"""

from typing import Dict, Optional
from .base_agent import BDAgent, AgentResponse


class BDStrategyAgent(BDAgent):
    """Synthesizes intelligence into BD strategy."""

    def __init__(self):
        super().__init__(
            name="BD Strategy Agent",
            description="Develop winning BD strategies. Expert at synthesizing "
                       "intelligence into actionable capture plans."
        )

    async def process(self, query: str, context: Optional[Dict] = None) -> AgentResponse:
        ctx = await self._get_context(query, ["programs", "companies", "contacts"])

        # Get comprehensive graph analysis
        try:
            analysis = await self.graph.query(
                f"Strategic analysis: {query}", mode="hybrid"
            )
            ctx += f"\n\n## Strategic Analysis\n{analysis}"
        except Exception as e:
            pass

        prompt = f"""BD strategy request:

Query: {query}

Develop strategy with:
1. Opportunity Assessment (win probability)
2. Key Win Themes
3. Teaming Strategy
4. Competitive Differentiation
5. 90-Day Action Plan
6. Risk Mitigation"""

        response_text = await self._call_claude(prompt, ctx)

        response = AgentResponse(
            success=True, content=response_text,
            sources=[{"context": ctx[:500]}],
            confidence=0.85, agent_name=self.name,
            metadata={"query": query}
        )
        self._store_interaction(query, response)
        return response

    async def create_capture_plan(self, opportunity: str) -> AgentResponse:
        return await self.process(f"Create capture plan for {opportunity}")

    async def assess_win_probability(self, opportunity: str) -> AgentResponse:
        return await self.process(f"Assess win probability for {opportunity}")

    async def develop_teaming_strategy(self, opportunity: str, gaps: list = None) -> AgentResponse:
        q = f"Develop teaming strategy for {opportunity}"
        if gaps:
            q += f". We need to fill these capability gaps: {', '.join(gaps)}"
        return await self.process(q)

    async def competitive_analysis(self, opportunity: str, competitors: list = None) -> AgentResponse:
        q = f"Competitive analysis for {opportunity}"
        if competitors:
            q += f". Known competitors: {', '.join(competitors)}"
        return await self.process(q)
