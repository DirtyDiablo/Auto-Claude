"""
BD Intelligence Hub Agents

Includes:
- Base agent infrastructure (BDAgent, AgentResponse)
- Specialized agents (ProgramIntel, CompanyResearch, ContactFinder, BDStrategy)
- CrewAI-based multi-agent workflows
- Orchestration for complex BD operations
"""

from .base_agent import BDAgent, AgentResponse
from .program_intel_agent import ProgramIntelAgent
from .company_research_agent import CompanyResearchAgent
from .contact_finder_agent import ContactFinderAgent
from .bd_strategy_agent import BDStrategyAgent

# CrewAI agents and workflows
try:
    from .bd_agents import (
        get_bd_agent_team,
        create_research_agent,
        create_analyst_agent,
        create_strategy_agent,
        create_writer_agent,
        BDAgentTeam,
        CREWAI_AVAILABLE
    )
    from .workflows import (
        get_workflows,
        BDWorkflows,
        analyze_program,
        prepare_outreach,
        generate_weekly_intel,
        WorkflowResult,
        ProgramAnalysisResult,
        OutreachPrepResult,
        WeeklyIntelResult
    )
    CREWAI_AGENTS_AVAILABLE = True
except ImportError:
    CREWAI_AGENTS_AVAILABLE = False
    CREWAI_AVAILABLE = False

__all__ = [
    # Base
    'BDAgent',
    'AgentResponse',

    # Specialized agents
    'ProgramIntelAgent',
    'CompanyResearchAgent',
    'ContactFinderAgent',
    'BDStrategyAgent',

    # CrewAI agents
    'get_bd_agent_team',
    'create_research_agent',
    'create_analyst_agent',
    'create_strategy_agent',
    'create_writer_agent',
    'BDAgentTeam',
    'CREWAI_AVAILABLE',

    # Workflows
    'get_workflows',
    'BDWorkflows',
    'analyze_program',
    'prepare_outreach',
    'generate_weekly_intel',
    'WorkflowResult',
    'ProgramAnalysisResult',
    'OutreachPrepResult',
    'WeeklyIntelResult',

    # Flags
    'CREWAI_AGENTS_AVAILABLE',
]
