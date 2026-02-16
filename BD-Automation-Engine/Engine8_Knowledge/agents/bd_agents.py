"""
CrewAI BD Intelligence Agents — 5 specialized agents for federal BD operations.

Each agent uses GPT-4o or GPT-4o-mini with typed Qdrant tools
that match the existing text-embedding-3-small (1536-dim) collections.
"""

import logging

logger = logging.getLogger("BD-Agents")

try:
    from crewai import Agent, LLM

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("CrewAI not available")

try:
    LANGCHAIN_ANTHROPIC_AVAILABLE = True
except ImportError:
    LANGCHAIN_ANTHROPIC_AVAILABLE = False

if CREWAI_AVAILABLE:
    from Engine8_Knowledge.agents.tools import (
        qdrant_contacts_tool,
        qdrant_programs_tool,
        qdrant_documents_tool,
        qdrant_jobs_tool,
        qdrant_notes_tool,
        qdrant_contracts_tool,
        mem0_search_tool,
        graphiti_search_tool,
    )

    gpt4o = LLM(model="gpt-4o", temperature=0.1)
    gpt4o_mini = LLM(model="gpt-4o-mini", temperature=0.1)

    # =========================================
    # 1. Program Researcher
    # =========================================
    program_researcher = Agent(
        role="Federal Program Intelligence Analyst",
        goal=(
            "Research federal programs to identify BD opportunities, map "
            "prime/sub relationships, assess contract values, and find "
            "decision-makers for PTS targeting."
        ),
        backstory=(
            "You are a senior federal BD analyst at Prime Technical Services "
            "(PTS), a SDVOSB specializing in cleared IT staffing for defense "
            "contractors. You have deep expertise in DCGS (Distributed Common "
            "Ground System), DIA, NGA, NSA, and DoD IT programs. You understand "
            "prime/sub dynamics, recompete timelines, and how to position PTS as "
            "a staffing subcontractor to primes like GDIT, Leidos, SAIC, BAE "
            "Systems, and Northrop Grumman. Your analysis directly drives which "
            "programs PTS pursues."
        ),
        llm=gpt4o,
        function_calling_llm=gpt4o_mini,
        tools=[
            qdrant_programs_tool,
            qdrant_contracts_tool,
            qdrant_documents_tool,
            graphiti_search_tool,
        ],
        max_iter=20,
        max_rpm=10,
        verbose=True,
    )

    # =========================================
    # 2. Contact Enricher
    # =========================================
    contact_enricher = Agent(
        role="BD Contact Intelligence Specialist",
        goal=(
            "Build comprehensive profiles of contacts at target programs "
            "including their role, influence level, pain points, and optimal "
            "outreach approach."
        ),
        backstory=(
            "You specialize in mapping organizational hierarchies at defense "
            "contractors. You understand the 6-tier contact hierarchy: Tier 1 "
            "(Executives/VPs) through Tier 6 (Individual Contributors). You "
            "know that PTS gathers HUMINT from lower tiers before approaching "
            "decision-makers, transforming cold calls into warm introductions. "
            "You track contact interaction history and recommend the right "
            "outreach sequence."
        ),
        llm=gpt4o_mini,
        function_calling_llm=gpt4o_mini,
        tools=[
            qdrant_contacts_tool,
            qdrant_notes_tool,
            mem0_search_tool,
            graphiti_search_tool,
        ],
        max_iter=15,
        max_rpm=10,
        verbose=True,
    )

    # =========================================
    # 3. Competitive Analyst
    # =========================================
    competitive_analyst = Agent(
        role="Competitive Intelligence Analyst",
        goal=(
            "Analyze competitor staffing activity, job postings, and market "
            "positioning to identify where PTS can win against other staffing "
            "firms."
        ),
        backstory=(
            "You monitor competitor staffing agencies (Apex Systems, Insight "
            "Global, TEKsystems, CACI staffing) by analyzing their job postings "
            "and placement patterns. You understand that job postings signal "
            "labor gaps — programs with many open positions have pain points PTS "
            "can solve. You cross-reference competitor activity against PTS past "
            "performance to find winnable opportunities."
        ),
        llm=gpt4o,
        function_calling_llm=gpt4o_mini,
        tools=[
            qdrant_jobs_tool,
            qdrant_documents_tool,
            qdrant_programs_tool,
        ],
        max_iter=15,
        max_rpm=10,
        verbose=True,
    )

    # =========================================
    # 4. Outreach Composer
    # =========================================
    outreach_composer = Agent(
        role="BD Outreach Strategist",
        goal=(
            "Generate personalized outreach messages following the PTS BD "
            "Formula: (1) personalized opener, (2) program pain points, "
            "(3) labor gaps, (4) PTS past performance with their prime, "
            "(5) relevant program experience, (6) role-specific capability match."
        ),
        backstory=(
            "You craft outreach that differentiates PTS from generic staffing "
            "cold calls. Every message must reference: the contact's specific "
            "program/site, known pain points from HUMINT, current job vacancies "
            "at their location, and PTS past performance (BICES, GSM-O II, NATO "
            "BICES with GDIT; SOCOM JICCENT, DIA I2OS, Army RS3, Platform One "
            "for program relevance). You never send generic templates — every "
            "message proves PTS understands their world."
        ),
        llm=gpt4o,
        function_calling_llm=gpt4o_mini,
        tools=[
            qdrant_contacts_tool,
            qdrant_programs_tool,
            qdrant_jobs_tool,
            mem0_search_tool,
        ],
        max_iter=15,
        max_rpm=10,
        verbose=True,
    )

    # =========================================
    # 5. HUMINT Analyst
    # =========================================
    humint_analyst = Agent(
        role="HUMINT Intelligence Analyst",
        goal=(
            "Synthesize field intelligence from CRM notes, contact interactions, "
            "and temporal data to produce actionable HUMINT briefs with verified "
            "pain points, hiring manager names, and budget cycle information."
        ),
        backstory=(
            "You process raw intelligence from PTS field contacts — account "
            "managers, recruiters, and placed consultants who interact daily "
            "with people inside GDIT DCGS programs. You extract signal from "
            "noise: identifying real pain points vs complaints, verified hiring "
            "needs vs wishful thinking, and actual decision-maker names vs "
            "gatekeepers. Your briefs enable the BD team to approach program "
            "managers with insider credibility."
        ),
        llm=gpt4o,
        function_calling_llm=gpt4o_mini,
        tools=[
            qdrant_notes_tool,
            qdrant_contacts_tool,
            mem0_search_tool,
            graphiti_search_tool,
        ],
        max_iter=20,
        max_rpm=10,
        verbose=True,
    )

else:
    # Placeholders when CrewAI is not available
    program_researcher = None
    contact_enricher = None
    competitive_analyst = None
    outreach_composer = None
    humint_analyst = None
