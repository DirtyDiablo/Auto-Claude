"""Program Intelligence Agent"""

from typing import Dict, Optional
from .base_agent import BDAgent, AgentResponse


class ProgramIntelAgent(BDAgent):
    """Analyzes federal programs and contract opportunities."""

    def __init__(self):
        super().__init__(
            name="Program Intelligence Agent",
            description="Analyze federal programs, contracts, and opportunities. "
                       "Expert in DCGS portfolio, IC programs, DoD contracts."
        )

    async def process(self, query: str, context: Optional[Dict] = None) -> AgentResponse:
        ctx = await self._get_context(query, ["programs", "contracts"])

        # Get graph insights
        try:
            graph_result = await self.graph.query(
                f"Program relationships: {query}", mode="hybrid"
            )
            ctx += f"\n\n## Graph Insights\n{graph_result}"
        except Exception as e:
            pass

        prompt = f"""Analyze this program intelligence request:

Query: {query}

Provide:
1. Program Overview
2. Contract Structure (prime/sub, vehicles, values)
3. Opportunity Assessment
4. Incumbent Analysis
5. Recommended Actions"""

        response_text = await self._call_claude(prompt, ctx)

        response = AgentResponse(
            success=True, content=response_text,
            sources=[{"context": ctx[:500]}],
            confidence=0.85, agent_name=self.name,
            metadata={"query": query}
        )
        self._store_interaction(query, response)
        return response

    async def analyze_program(self, program_name: str) -> AgentResponse:
        return await self.process(f"Comprehensive analysis of {program_name}")

    async def find_recompetes(self, months: int = 12) -> AgentResponse:
        return await self.process(f"Find recompetes in next {months} months for DCGS/IC")

    async def get_program_value(self, program_name: str) -> AgentResponse:
        return await self.process(f"What is the contract value and structure of {program_name}?")

    async def find_incumbents(self, program_name: str) -> AgentResponse:
        return await self.process(f"Who are the current incumbents on {program_name}?")
