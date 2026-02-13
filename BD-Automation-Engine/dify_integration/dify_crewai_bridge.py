"""
Bridge Dify to your existing CrewAI agents and BD agents.

Your Existing Agents (Engine8_Knowledge/agents/):
- BDStrategyAgent - Synthesizes intelligence into BD strategy
- CompanyResearchAgent - Gathers intelligence about companies
- ContactFinderAgent - Discovers and matches contacts
- ProgramIntelAgent - Analyzes federal programs
- CrewAI Orchestrator - Multi-agent coordination

This bridge allows Dify apps to:
1. Invoke your agents via visual workflow
2. Chain agents in drag-drop sequences
3. A/B test different agent configurations
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

logger = logging.getLogger(__name__)


@dataclass
class AgentInvocationResult:
    """Result from invoking a BD agent."""
    success: bool
    agent_name: str
    content: str
    confidence: float
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class DifyCrewAIBridge:
    """
    Bridge Dify to your existing CrewAI/BD agents.

    This allows Dify to:
    1. Invoke individual agents as tools
    2. Run multi-agent workflows
    3. Access agent capabilities via visual builder

    Agents are accessed via your Knowledge API (:8100) which already
    exposes them at /agent/* endpoints.
    """

    # Map agent names to API endpoints
    AGENT_ENDPOINTS = {
        'bd_strategy': '/agent/strategy',
        'company_research': '/agent/company',
        'contact_finder': '/agent/contact',
        'program_intel': '/agent/program',
    }

    # Workflow endpoints
    WORKFLOW_ENDPOINTS = {
        'capture_strategy': '/workflow/capture',
        'competitor_analysis': '/workflow/competitor',
        'quick_intel': '/workflow/quick',
        'analyze_program': '/agents/analyze-program',
        'prepare_outreach': '/agents/prepare-outreach',
        'weekly_intel': '/agents/weekly-intel',
    }

    def __init__(self, knowledge_api_url: str = None):
        """
        Initialize the Dify-CrewAI bridge.

        Args:
            knowledge_api_url: URL of your BD Knowledge API (default: http://127.0.0.1:8100)
        """
        self.knowledge_api_url = knowledge_api_url or os.getenv(
            'KNOWLEDGE_API_URL', 'http://127.0.0.1:8100'
        )
        self.client = httpx.AsyncClient(timeout=120.0)  # Longer timeout for agents

        logger.info(f"DifyCrewAIBridge initialized: API={self.knowledge_api_url}")

    async def invoke_agent(
        self,
        agent_name: str,
        query: str,
        context: Dict[str, Any] = None
    ) -> AgentInvocationResult:
        """
        Invoke a BD agent from Dify.

        This is the main function Dify will use as a tool.

        Args:
            agent_name: Name of agent (bd_strategy, company_research, contact_finder, program_intel)
            query: Query/task for the agent
            context: Optional additional context

        Returns:
            AgentInvocationResult with agent response
        """
        endpoint = self.AGENT_ENDPOINTS.get(agent_name)
        if not endpoint:
            return AgentInvocationResult(
                success=False,
                agent_name=agent_name,
                content=f"Unknown agent: {agent_name}. Available: {list(self.AGENT_ENDPOINTS.keys())}",
                confidence=0.0,
                sources=[],
                metadata={'error': 'unknown_agent'}
            )

        try:
            response = await self.client.get(
                f"{self.knowledge_api_url}{endpoint}",
                params={"q": query}
            )
            response.raise_for_status()
            data = response.json()

            return AgentInvocationResult(
                success=True,
                agent_name=data.get('agent', agent_name),
                content=data.get('response', ''),
                confidence=data.get('confidence', 0.0),
                sources=data.get('sources', []),
                metadata={'query': query, 'context': context}
            )

        except Exception as e:
            logger.error(f"Agent invocation error: {e}")
            return AgentInvocationResult(
                success=False,
                agent_name=agent_name,
                content=f"Error invoking agent: {e}",
                confidence=0.0,
                sources=[],
                metadata={'error': str(e)}
            )

    async def bd_strategy(self, query: str) -> AgentInvocationResult:
        """
        Get BD strategy recommendations.

        Expert at synthesizing intelligence into actionable capture plans.

        Examples:
        - "Develop capture plan for DCGS-A recompete"
        - "Assess win probability for AF DCGS"
        - "Develop teaming strategy for GBSD"
        """
        return await self.invoke_agent('bd_strategy', query)

    async def company_research(self, company_name: str) -> AgentInvocationResult:
        """
        Research a company for competitive intelligence.

        Gathers intelligence about companies and competitors.

        Examples:
        - "Research Northrop Grumman's ISR capabilities"
        - "What programs does GDIT prime on?"
        - "Leidos competitive positioning"
        """
        return await self.invoke_agent('company_research', company_name)

    async def contact_finder(self, query: str) -> AgentInvocationResult:
        """
        Find and match contacts for BD outreach.

        Discovers contacts based on program, company, or role criteria.

        Examples:
        - "Find Tier 1 contacts at Leidos for DCGS"
        - "Who are the decision makers for GBSD?"
        - "ISR program managers at Northrop"
        """
        return await self.invoke_agent('contact_finder', query)

    async def program_intel(self, program_name: str) -> AgentInvocationResult:
        """
        Get intelligence about a federal program.

        Analyzes programs for BD opportunities.

        Examples:
        - "AF DCGS program analysis"
        - "DCGS-A contract details"
        - "GBSD opportunity assessment"
        """
        return await self.invoke_agent('program_intel', program_name)

    # Multi-Agent Workflows

    async def run_capture_strategy_workflow(
        self,
        opportunity: str
    ) -> Dict[str, Any]:
        """
        Run the full capture strategy workflow.

        Uses multiple agents in sequence:
        1. Program Intel - Gather program details
        2. Company Research - Competitive landscape
        3. Contact Finder - Key stakeholders
        4. BD Strategy - Synthesis and recommendations

        Args:
            opportunity: Name of the opportunity/program

        Returns:
            Comprehensive capture strategy
        """
        try:
            response = await self.client.get(
                f"{self.knowledge_api_url}/workflow/capture",
                params={"opportunity": opportunity}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Capture workflow error: {e}")
            return {'success': False, 'error': str(e)}

    async def run_competitor_analysis_workflow(
        self,
        company: str
    ) -> Dict[str, Any]:
        """
        Run competitor analysis workflow.

        Args:
            company: Company name to analyze

        Returns:
            Competitive intelligence report
        """
        try:
            response = await self.client.get(
                f"{self.knowledge_api_url}/workflow/competitor",
                params={"company": company}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Competitor workflow error: {e}")
            return {'success': False, 'error': str(e)}

    async def run_program_analysis(
        self,
        program_name: str
    ) -> Dict[str, Any]:
        """
        Run full program analysis with CrewAI agents.

        Uses 4 agents in sequence:
        1. Research Agent - Gathers program intelligence
        2. Analyst Agent - Scores the opportunity
        3. Strategy Agent - Develops approach
        4. Writer Agent - Generates playbook

        Returns a complete BD playbook.
        """
        try:
            response = await self.client.post(
                f"{self.knowledge_api_url}/agents/analyze-program",
                params={"program_name": program_name}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Program analysis error: {e}")
            return {'success': False, 'error': str(e)}

    async def run_outreach_prep(
        self,
        contact_name: str
    ) -> Dict[str, Any]:
        """
        Prepare outreach materials for a contact.

        Uses 4 agents to generate:
        - Call script
        - Email template
        - LinkedIn message

        Args:
            contact_name: Name of the contact
        """
        try:
            response = await self.client.post(
                f"{self.knowledge_api_url}/agents/prepare-outreach",
                params={"contact_name": contact_name}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Outreach prep error: {e}")
            return {'success': False, 'error': str(e)}

    async def run_weekly_intel(self) -> Dict[str, Any]:
        """
        Generate weekly BD intelligence report.

        Returns:
        - Hot programs
        - New opportunities
        - Action items
        - Executive summary
        """
        try:
            response = await self.client.post(
                f"{self.knowledge_api_url}/agents/weekly-intel"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Weekly intel error: {e}")
            return {'success': False, 'error': str(e)}

    async def get_agent_status(self) -> Dict[str, Any]:
        """Check status of CrewAI agents."""
        try:
            response = await self.client.get(
                f"{self.knowledge_api_url}/agents/status"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Agent status error: {e}")
            return {'available': False, 'error': str(e)}

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """
        Get list of available agents for Dify tool registration.

        Returns agent metadata in format suitable for Dify.
        """
        return [
            {
                "name": "bd_strategy_agent",
                "description": "Develop winning BD strategies. Expert at synthesizing intelligence into actionable capture plans, win themes, and 90-day action plans.",
                "parameters": {
                    "query": {
                        "type": "string",
                        "required": True,
                        "description": "Strategy request (e.g., 'Develop capture plan for DCGS-A')"
                    }
                },
                "examples": [
                    "Develop capture plan for AF DCGS recompete",
                    "Assess win probability for GBSD",
                    "Teaming strategy for ISR modernization"
                ]
            },
            {
                "name": "company_research_agent",
                "description": "Gathers competitive intelligence about companies and contractors. Analyzes capabilities, programs, partnerships, and market position.",
                "parameters": {
                    "company_name": {
                        "type": "string",
                        "required": True,
                        "description": "Company to research"
                    }
                },
                "examples": [
                    "Research Northrop Grumman's ISR capabilities",
                    "What programs does GDIT prime on?",
                    "Leidos competitive positioning in DCGS"
                ]
            },
            {
                "name": "contact_finder_agent",
                "description": "Discovers and matches contacts for BD outreach. Finds decision makers, program managers, and key stakeholders.",
                "parameters": {
                    "query": {
                        "type": "string",
                        "required": True,
                        "description": "Contact search criteria"
                    }
                },
                "examples": [
                    "Find Tier 1 contacts at Leidos for DCGS",
                    "Who are the decision makers for GBSD?",
                    "ISR program managers at Northrop"
                ]
            },
            {
                "name": "program_intel_agent",
                "description": "Analyzes federal programs for BD opportunities. Provides contract details, incumbents, recompete timelines, and win strategies.",
                "parameters": {
                    "program_name": {
                        "type": "string",
                        "required": True,
                        "description": "Program to analyze"
                    }
                },
                "examples": [
                    "AF DCGS program analysis",
                    "DCGS-A contract vehicle details",
                    "GBSD opportunity timeline"
                ]
            }
        ]

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# FastAPI router for exposing agents to Dify
def create_dify_agents_router():
    """
    Create a FastAPI router for Dify agent integration.

    Add this to your api.py:
        from dify_integration.dify_crewai_bridge import create_dify_agents_router
        app.include_router(create_dify_agents_router(), prefix="/dify")
    """
    from fastapi import APIRouter, Query

    router = APIRouter(tags=["Dify Agents"])
    bridge = DifyCrewAIBridge()

    @router.get("/agents/list")
    async def list_agents():
        """List available agents for Dify."""
        return bridge.get_available_agents()

    @router.get("/agents/invoke")
    async def invoke_agent(
        agent: str = Query(..., description="Agent name"),
        query: str = Query(..., description="Query for agent")
    ):
        """Invoke an agent from Dify."""
        result = await bridge.invoke_agent(agent, query)
        return asdict(result)

    @router.get("/agents/strategy")
    async def bd_strategy(query: str = Query(...)):
        """BD Strategy agent endpoint for Dify."""
        result = await bridge.bd_strategy(query)
        return asdict(result)

    @router.get("/agents/company")
    async def company_research(company: str = Query(...)):
        """Company Research agent endpoint for Dify."""
        result = await bridge.company_research(company)
        return asdict(result)

    @router.get("/agents/contact")
    async def contact_finder(query: str = Query(...)):
        """Contact Finder agent endpoint for Dify."""
        result = await bridge.contact_finder(query)
        return asdict(result)

    @router.get("/agents/program")
    async def program_intel(program: str = Query(...)):
        """Program Intel agent endpoint for Dify."""
        result = await bridge.program_intel(program)
        return asdict(result)

    return router
