"""
CrewAI Orchestration for BD Intelligence Hub
Repository: https://github.com/crewAIInc/crewAI (43,100+ stars)
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("CrewAI not available, using fallback orchestration")

from .program_intel_agent import ProgramIntelAgent
from .company_research_agent import CompanyResearchAgent
from .contact_finder_agent import ContactFinderAgent
from .bd_strategy_agent import BDStrategyAgent


@dataclass
class OrchestrationResult:
    success: bool
    workflow: str
    results: List[Dict]
    final_output: str
    agents_used: List[str]


class FallbackOrchestrator:
    """Fallback orchestration when CrewAI unavailable."""

    def __init__(self):
        self.program_agent = ProgramIntelAgent()
        self.company_agent = CompanyResearchAgent()
        self.contact_agent = ContactFinderAgent()
        self.strategy_agent = BDStrategyAgent()

    async def run_workflow(self, workflow: str, query: str) -> OrchestrationResult:
        results = []
        agents_used = []

        if workflow == "capture_strategy":
            # Run agents in sequence
            program_result = await self.program_agent.process(query)
            results.append({"agent": "program_intel", "output": program_result.content})
            agents_used.append("program_intel")

            company_result = await self.company_agent.process(query)
            results.append({"agent": "company_research", "output": company_result.content})
            agents_used.append("company_research")

            contact_result = await self.contact_agent.process(query)
            results.append({"agent": "contact_finder", "output": contact_result.content})
            agents_used.append("contact_finder")

            # Final strategy synthesis
            strategy_result = await self.strategy_agent.process(
                f"Synthesize capture strategy for {query} using:\n"
                f"Program Intel: {program_result.content[:500]}\n"
                f"Company Intel: {company_result.content[:500]}\n"
                f"Contacts: {contact_result.content[:500]}"
            )
            results.append({"agent": "bd_strategy", "output": strategy_result.content})
            agents_used.append("bd_strategy")

            return OrchestrationResult(
                success=True,
                workflow=workflow,
                results=results,
                final_output=strategy_result.content,
                agents_used=agents_used
            )

        elif workflow == "competitor_analysis":
            company_result = await self.company_agent.process(f"Competitor analysis: {query}")
            results.append({"agent": "company_research", "output": company_result.content})

            return OrchestrationResult(
                success=True,
                workflow=workflow,
                results=results,
                final_output=company_result.content,
                agents_used=["company_research"]
            )

        else:
            # Default: use strategy agent
            strategy_result = await self.strategy_agent.process(query)
            return OrchestrationResult(
                success=True,
                workflow="default",
                results=[{"agent": "bd_strategy", "output": strategy_result.content}],
                final_output=strategy_result.content,
                agents_used=["bd_strategy"]
            )


class BDCrewOrchestrator:
    """
    Multi-agent orchestration using CrewAI.
    Coordinates specialized BD agents for complex workflows.
    """

    def __init__(self):
        if CREWAI_AVAILABLE:
            self._init_crewai()
        else:
            self._init_fallback()

    def _init_crewai(self):
        """Initialize CrewAI agents and crews."""
        self.backend = "crewai"

        # Create CrewAI agents
        self.program_agent = Agent(
            role="Program Intelligence Analyst",
            goal="Analyze federal programs and identify opportunities",
            backstory="Expert in DCGS portfolio, DoD contracts, and federal procurement",
            verbose=True
        )

        self.company_agent = Agent(
            role="Company Research Analyst",
            goal="Research competitors and identify teaming partners",
            backstory="Expert in federal contractor intelligence and competitive analysis",
            verbose=True
        )

        self.contact_agent = Agent(
            role="Contact Intelligence Analyst",
            goal="Identify key decision makers and stakeholders",
            backstory="Expert in federal organization structures and personnel",
            verbose=True
        )

        self.strategy_agent = Agent(
            role="BD Strategy Lead",
            goal="Develop winning capture strategies",
            backstory="Senior BD executive with proven win record",
            verbose=True
        )

        # Store our custom agents for processing
        self._program_agent = ProgramIntelAgent()
        self._company_agent = CompanyResearchAgent()
        self._contact_agent = ContactFinderAgent()
        self._strategy_agent = BDStrategyAgent()

    def _init_fallback(self):
        """Initialize fallback orchestration."""
        self.backend = "fallback"
        self._orchestrator = FallbackOrchestrator()

    async def capture_strategy_workflow(self, opportunity: str) -> OrchestrationResult:
        """Run capture strategy workflow."""
        if self.backend == "fallback":
            return await self._orchestrator.run_workflow("capture_strategy", opportunity)

        results = []
        agents_used = []

        # Task 1: Program Analysis
        program_result = await self._program_agent.process(
            f"Analyze program opportunity: {opportunity}"
        )
        results.append({"agent": "program_intel", "output": program_result.content})
        agents_used.append("program_intel")

        # Task 2: Competitor Analysis
        company_result = await self._company_agent.process(
            f"Identify competitors for: {opportunity}"
        )
        results.append({"agent": "company_research", "output": company_result.content})
        agents_used.append("company_research")

        # Task 3: Key Contacts
        contact_result = await self._contact_agent.process(
            f"Find key decision makers for: {opportunity}"
        )
        results.append({"agent": "contact_finder", "output": contact_result.content})
        agents_used.append("contact_finder")

        # Task 4: Strategy Synthesis
        context = f"""
        Program Analysis: {program_result.content[:800]}
        Competitor Analysis: {company_result.content[:800]}
        Key Contacts: {contact_result.content[:800]}
        """
        strategy_result = await self._strategy_agent.process(
            f"Create capture strategy for {opportunity} based on the research",
            context={"research": context}
        )
        results.append({"agent": "bd_strategy", "output": strategy_result.content})
        agents_used.append("bd_strategy")

        return OrchestrationResult(
            success=True,
            workflow="capture_strategy",
            results=results,
            final_output=strategy_result.content,
            agents_used=agents_used
        )

    async def competitor_analysis_workflow(self, company: str) -> OrchestrationResult:
        """Run competitor analysis workflow."""
        if self.backend == "fallback":
            return await self._orchestrator.run_workflow("competitor_analysis", company)

        results = []
        agents_used = []

        # Company profile
        company_result = await self._company_agent.process(
            f"Comprehensive competitor analysis of {company}"
        )
        results.append({"agent": "company_research", "output": company_result.content})
        agents_used.append("company_research")

        # Key personnel
        contact_result = await self._contact_agent.process(
            f"Find key personnel at {company}"
        )
        results.append({"agent": "contact_finder", "output": contact_result.content})
        agents_used.append("contact_finder")

        return OrchestrationResult(
            success=True,
            workflow="competitor_analysis",
            results=results,
            final_output=company_result.content,
            agents_used=agents_used
        )

    async def teaming_partner_workflow(self, capability_gaps: List[str]) -> OrchestrationResult:
        """Run teaming partner identification workflow."""
        if self.backend == "fallback":
            return await self._orchestrator.run_workflow(
                "teaming_partner", f"Find partners for: {', '.join(capability_gaps)}"
            )

        results = []

        partner_result = await self._company_agent.find_teaming_partners(capability_gaps)
        results.append({"agent": "company_research", "output": partner_result.content})

        return OrchestrationResult(
            success=True,
            workflow="teaming_partner",
            results=results,
            final_output=partner_result.content,
            agents_used=["company_research"]
        )

    async def quick_intel_workflow(self, query: str) -> OrchestrationResult:
        """Run quick intelligence query."""
        if self.backend == "fallback":
            return await self._orchestrator.run_workflow("quick_intel", query)

        # Determine best agent for query
        query_lower = query.lower()

        if any(word in query_lower for word in ["program", "contract", "dcgs", "recompete"]):
            result = await self._program_agent.process(query)
            agent = "program_intel"
        elif any(word in query_lower for word in ["company", "competitor", "partner", "leidos", "gdit"]):
            result = await self._company_agent.process(query)
            agent = "company_research"
        elif any(word in query_lower for word in ["contact", "person", "decision maker", "clearance"]):
            result = await self._contact_agent.process(query)
            agent = "contact_finder"
        else:
            result = await self._strategy_agent.process(query)
            agent = "bd_strategy"

        return OrchestrationResult(
            success=True,
            workflow="quick_intel",
            results=[{"agent": agent, "output": result.content}],
            final_output=result.content,
            agents_used=[agent]
        )


_orchestrator_instance = None

def get_orchestrator() -> BDCrewOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = BDCrewOrchestrator()
    return _orchestrator_instance
