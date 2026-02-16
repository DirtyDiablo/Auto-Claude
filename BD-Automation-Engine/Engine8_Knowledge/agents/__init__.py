"""
BD Intelligence Hub Agents

8-Agent CrewAI System for BD Intelligence:

Core Agents (Original 4):
- ProgramIntelAgent: Federal program analysis and opportunity identification
- CompanyResearchAgent: Competitor analysis and teaming partner identification
- ContactFinderAgent: Key contact identification and stakeholder mapping
- BDStrategyAgent: Capture strategy development and win theme generation

Phase 4 Enhancement Agents (New 4):
- ContactClassifierAgent: Automatic contact classification by tier, program, priority
- ScraperMonitorAgent: Job scraper monitoring and opportunity detection
- QualityAssuranceAgent: Data quality validation across all collections
- AnalyticsAgent: Trend analysis, insights, and intelligence reporting

Orchestration:
- BDCrewOrchestrator: Multi-agent workflow coordination
- FallbackOrchestrator: Fallback when CrewAI unavailable
"""

from .base_agent import BDAgent, AgentResponse

# Original 4 Core Agents
from .program_intel_agent import ProgramIntelAgent
from .company_research_agent import CompanyResearchAgent
from .contact_finder_agent import ContactFinderAgent
from .bd_strategy_agent import BDStrategyAgent

# Phase 4 Enhancement Agents (New 4)
from .contact_classifier_agent import ContactClassifierAgent
from .scraper_monitor_agent import ScraperMonitorAgent
from .quality_assurance_agent import QualityAssuranceAgent
from .analytics_agent import AnalyticsAgent

# Orchestrator
from .crewai_orchestrator import (
    BDCrewOrchestrator,
    FallbackOrchestrator,
    OrchestrationResult,
    get_orchestrator,
)

# CrewAI agents and workflows
try:
    from .bd_agents import (
        get_bd_agent_team,
        create_research_agent,
        create_analyst_agent,
        create_strategy_agent,
        create_writer_agent,
        BDAgentTeam,
        CREWAI_AVAILABLE,
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
        WeeklyIntelResult,
    )

    CREWAI_AGENTS_AVAILABLE = True
except ImportError:
    CREWAI_AGENTS_AVAILABLE = False
    CREWAI_AVAILABLE = False

__all__ = [
    # Base
    "BDAgent",
    "AgentResponse",
    # Core Agents (Original 4)
    "ProgramIntelAgent",
    "CompanyResearchAgent",
    "ContactFinderAgent",
    "BDStrategyAgent",
    # Phase 4 Enhancement Agents (New 4)
    "ContactClassifierAgent",
    "ScraperMonitorAgent",
    "QualityAssuranceAgent",
    "AnalyticsAgent",
    # Orchestrator
    "BDCrewOrchestrator",
    "FallbackOrchestrator",
    "OrchestrationResult",
    "get_orchestrator",
    # CrewAI agents (legacy)
    "get_bd_agent_team",
    "create_research_agent",
    "create_analyst_agent",
    "create_strategy_agent",
    "create_writer_agent",
    "BDAgentTeam",
    "CREWAI_AVAILABLE",
    # Workflows
    "get_workflows",
    "BDWorkflows",
    "analyze_program",
    "prepare_outreach",
    "generate_weekly_intel",
    "WorkflowResult",
    "ProgramAnalysisResult",
    "OutreachPrepResult",
    "WeeklyIntelResult",
    # Flags
    "CREWAI_AGENTS_AVAILABLE",
]
