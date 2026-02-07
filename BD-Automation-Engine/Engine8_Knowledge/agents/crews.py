"""
CrewAI Crew Factories for BD Intelligence Operations.

3 pre-built crews that combine agents + tasks for common BD workflows.
"""

import logging
from typing import Optional

logger = logging.getLogger("BD-Crews")

try:
    from crewai import Crew, Task, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("CrewAI not available — crews disabled")


def create_bd_research_crew(
    program_name: str,
    agency: str = "",
    prime: str = "",
) -> Optional["Crew"]:
    """
    Full-stack BD research crew: program intel → contacts → competitive → outreach.

    Returns a Crew ready to .kickoff().
    """
    if not CREWAI_AVAILABLE:
        return None

    from Engine8_Knowledge.agents.bd_agents import (
        program_researcher,
        contact_enricher,
        competitive_analyst,
        outreach_composer,
    )
    from Engine8_Knowledge.agents.models import (
        ProgramIntelligence,
        ContactProfile,
        CompetitiveReport,
        OutreachPlan,
    )

    context_str = f"Program: {program_name}"
    if agency:
        context_str += f", Agency: {agency}"
    if prime:
        context_str += f", Prime: {prime}"

    t1 = Task(
        description=(
            f"Research the federal program '{program_name}' to identify BD opportunities. "
            f"Context: {context_str}. "
            "Find contract values, prime/sub relationships, recompete timelines, "
            "and key decision-makers. Assess PTS positioning."
        ),
        expected_output="Structured program intelligence report with contacts, competitors, and recommendation.",
        output_pydantic=ProgramIntelligence,
        agent=program_researcher,
    )

    t2 = Task(
        description=(
            f"Build contact profiles for key people at '{program_name}'. "
            "Classify each contact by tier (1-6), identify their pain points, "
            "interaction history, and recommend outreach approach."
        ),
        expected_output="List of enriched contact profiles with tier classification and outreach recommendations.",
        agent=contact_enricher,
    )

    t3 = Task(
        description=(
            f"Analyze competitive landscape for '{program_name}'. "
            "Identify incumbent staffing firms, their strengths/weaknesses, "
            "and where PTS can differentiate. Check job postings for labor gaps."
        ),
        expected_output="Competitive report with win probability, risks, and recommended strategy.",
        output_pydantic=CompetitiveReport,
        agent=competitive_analyst,
    )

    t4 = Task(
        description=(
            f"Generate personalized outreach plan for top contacts at '{program_name}'. "
            "Use the PTS BD Formula: personalized opener, program pain points, "
            "labor gaps, PTS past performance, program experience, capability match."
        ),
        expected_output="Outreach plan with personalized messages for each key contact.",
        output_pydantic=OutreachPlan,
        agent=outreach_composer,
    )

    return Crew(
        agents=[program_researcher, contact_enricher, competitive_analyst, outreach_composer],
        tasks=[t1, t2, t3, t4],
        process=Process.sequential,
        verbose=True,
    )


def create_weekly_intel_crew(focus_programs: Optional[list[str]] = None) -> Optional["Crew"]:
    """
    Weekly intelligence digest crew: HUMINT analysis → competitive scan → summary.

    Produces a weekly brief for the BD team.
    """
    if not CREWAI_AVAILABLE:
        return None

    from Engine8_Knowledge.agents.bd_agents import (
        humint_analyst,
        competitive_analyst,
        program_researcher,
    )
    from Engine8_Knowledge.agents.models import HUMINTBrief

    programs_str = ", ".join(focus_programs) if focus_programs else "all active DCGS programs"

    t1 = Task(
        description=(
            f"Synthesize this week's HUMINT from CRM notes and contact interactions "
            f"for {programs_str}. Extract verified pain points, hiring manager names, "
            "budget cycle info, and vendor preferences. Flag any time-sensitive intel."
        ),
        expected_output="HUMINT brief with key findings, pain points, hiring managers, and action items.",
        output_pydantic=HUMINTBrief,
        agent=humint_analyst,
    )

    t2 = Task(
        description=(
            f"Scan competitor activity for {programs_str}. "
            "Check new job postings, placement changes, and market moves. "
            "Identify any shifts in competitive positioning."
        ),
        expected_output="Competitive activity summary with notable changes and opportunities.",
        agent=competitive_analyst,
    )

    t3 = Task(
        description=(
            f"Compile weekly intelligence summary for {programs_str}. "
            "Combine HUMINT findings with competitive intelligence. "
            "Prioritize actionable items and recommend next steps for BD team."
        ),
        expected_output="Weekly intelligence digest with prioritized action items.",
        agent=program_researcher,
    )

    return Crew(
        agents=[humint_analyst, competitive_analyst, program_researcher],
        tasks=[t1, t2, t3],
        process=Process.sequential,
        verbose=True,
    )


def create_contact_outreach_crew(
    contact_name: str,
    company: str = "",
    program: str = "",
) -> Optional["Crew"]:
    """
    Contact-focused outreach crew: enrich contact → research program → compose outreach.
    """
    if not CREWAI_AVAILABLE:
        return None

    from Engine8_Knowledge.agents.bd_agents import (
        contact_enricher,
        program_researcher,
        outreach_composer,
    )
    from Engine8_Knowledge.agents.models import ContactProfile, OutreachPlan

    context_str = f"Contact: {contact_name}"
    if company:
        context_str += f", Company: {company}"
    if program:
        context_str += f", Program: {program}"

    t1 = Task(
        description=(
            f"Build a comprehensive profile for '{contact_name}' at '{company}'. "
            "Find their role, tier classification, programs they work on, "
            "pain points, and interaction history with PTS."
        ),
        expected_output="Enriched contact profile with tier, pain points, and outreach recommendation.",
        output_pydantic=ContactProfile,
        agent=contact_enricher,
    )

    t2 = Task(
        description=(
            f"Research the program context for '{contact_name}'. "
            f"Context: {context_str}. "
            "Find current contract status, labor gaps, and PTS past performance "
            "relevant to this contact's program."
        ),
        expected_output="Program context relevant to the contact's role and responsibilities.",
        agent=program_researcher,
    )

    t3 = Task(
        description=(
            f"Compose personalized outreach for '{contact_name}' using PTS BD Formula. "
            "Reference their specific program, known pain points, current vacancies, "
            "and relevant PTS past performance. Make it specific, not generic."
        ),
        expected_output="Personalized outreach plan with talking points and follow-up strategy.",
        output_pydantic=OutreachPlan,
        agent=outreach_composer,
    )

    return Crew(
        agents=[contact_enricher, program_researcher, outreach_composer],
        tasks=[t1, t2, t3],
        process=Process.sequential,
        verbose=True,
    )
