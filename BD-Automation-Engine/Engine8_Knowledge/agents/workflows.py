"""
CrewAI BD Workflows
Multi-agent workflows for BD intelligence operations.
"""

import os
import sys
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("CrewAI not available")

from .bd_agents import (
    get_bd_agent_team,
    create_research_agent,
    create_analyst_agent,
    create_strategy_agent,
    create_writer_agent,
    BDAgentTeam
)
from Engine8_Knowledge.scripts.memory_system import get_memory_system
from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore


# =========================================
# WORKFLOW RESULT CLASSES
# =========================================

@dataclass
class WorkflowResult:
    """Result from a workflow execution."""
    workflow_name: str
    success: bool
    output: Dict[str, Any]
    agents_used: List[str]
    execution_time: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None


@dataclass
class ProgramAnalysisResult(WorkflowResult):
    """Result from program analysis workflow."""
    playbook: str = ""
    priority_contacts: List[Dict] = field(default_factory=list)
    talking_points: List[str] = field(default_factory=list)
    opportunity_score: float = 0.0


@dataclass
class OutreachPrepResult(WorkflowResult):
    """Result from contact outreach prep workflow."""
    call_script: str = ""
    email_template: str = ""
    linkedin_message: str = ""
    contact_context: Dict = field(default_factory=dict)


@dataclass
class WeeklyIntelResult(WorkflowResult):
    """Result from weekly intelligence report workflow."""
    hot_programs: List[Dict] = field(default_factory=list)
    new_opportunities: List[Dict] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    executive_summary: str = ""


# =========================================
# WORKFLOW IMPLEMENTATIONS
# =========================================

class BDWorkflows:
    """
    BD Intelligence Workflows using CrewAI.
    Coordinates multiple agents for complex BD tasks.
    """

    def __init__(self):
        self.agent_team = get_bd_agent_team()
        self.memory = get_memory_system()
        self.store = BDKnowledgeStore()

    def _create_fallback_result(
        self,
        workflow_name: str,
        error_msg: str,
        start_time: float
    ) -> WorkflowResult:
        """Create a fallback result when CrewAI is unavailable."""
        import time
        return WorkflowResult(
            workflow_name=workflow_name,
            success=False,
            output={"error": error_msg},
            agents_used=[],
            execution_time=time.time() - start_time,
            error=error_msg
        )

    async def analyze_program(self, program_name: str) -> ProgramAnalysisResult:
        """
        Program Analysis Pipeline
        Sequential: Research -> Analyze -> Strategize -> Write

        Returns a complete BD playbook for the specified program.
        """
        import time
        start_time = time.time()

        if not self.agent_team.available:
            return ProgramAnalysisResult(
                workflow_name="program_analysis",
                success=False,
                output={"error": "CrewAI not available"},
                agents_used=[],
                execution_time=time.time() - start_time,
                error="CrewAI not available"
            )

        agents_used = []

        try:
            # Task 1: Research Agent gathers program intel
            research_task = Task(
                description=f"""Research the federal program: {program_name}

                Gather:
                1. Program overview and mission
                2. Contract structure (prime contractors, vehicles, values)
                3. Recent news and developments
                4. Key agencies and stakeholders
                5. Related programs and dependencies

                Be thorough and cite all sources.""",
                expected_output="Comprehensive program intelligence report with sources",
                agent=self.agent_team.research_agent
            )
            agents_used.append("research")

            # Task 2: Analyst scores the opportunity
            analyst_task = Task(
                description=f"""Analyze the BD opportunity for {program_name}

                Based on the research, analyze:
                1. Current hiring patterns (search jobs)
                2. Contract lifecycle stage
                3. Competitive landscape
                4. Win probability assessment (0-100)
                5. Key risk factors

                Store any significant insights found.""",
                expected_output="Opportunity analysis with scoring and risk assessment",
                agent=self.agent_team.analyst_agent,
                context=[research_task]
            )
            agents_used.append("analyst")

            # Task 3: Strategy agent develops approach
            strategy_task = Task(
                description=f"""Develop BD strategy for {program_name}

                Based on the research and analysis:
                1. Identify top 5 priority contacts to engage
                2. Determine optimal teaming strategy
                3. Identify key win themes
                4. Outline 90-day engagement plan
                5. List competitive differentiators

                Check contact context for any prior relationships.""",
                expected_output="Strategic approach plan with priority contacts and action items",
                agent=self.agent_team.strategy_agent,
                context=[research_task, analyst_task]
            )
            agents_used.append("strategy")

            # Task 4: Writer generates playbook
            writer_task = Task(
                description=f"""Create a BD playbook for {program_name}

                Synthesize all research, analysis, and strategy into:
                1. Executive Summary (2-3 paragraphs)
                2. Program Overview section
                3. Opportunity Assessment section
                4. Recommended Approach section
                5. Key Talking Points (5-7 bullets)
                6. Next Steps (actionable items)

                Format as a professional BD playbook.""",
                expected_output="Complete BD playbook document",
                agent=self.agent_team.writer_agent,
                context=[research_task, analyst_task, strategy_task]
            )
            agents_used.append("writer")

            # Execute the crew
            crew = Crew(
                agents=[
                    self.agent_team.research_agent,
                    self.agent_team.analyst_agent,
                    self.agent_team.strategy_agent,
                    self.agent_team.writer_agent
                ],
                tasks=[research_task, analyst_task, strategy_task, writer_task],
                process=Process.sequential,
                verbose=True
            )

            # Run the crew (CrewAI is sync, wrap in asyncio)
            result = await asyncio.get_event_loop().run_in_executor(
                None, crew.kickoff
            )

            # Parse the output
            playbook = str(result)

            # Extract talking points (simple parsing)
            talking_points = []
            if "Talking Points" in playbook:
                tp_section = playbook.split("Talking Points")[1].split("\n\n")[0]
                for line in tp_section.split("\n"):
                    if line.strip().startswith("-") or line.strip().startswith("*"):
                        talking_points.append(line.strip()[1:].strip())

            # Store the result in memory
            self.memory.remember(
                f"Program Analysis for {program_name}: {playbook[:500]}",
                memory_type="analysis",
                metadata={"program": program_name, "workflow": "program_analysis"}
            )

            return ProgramAnalysisResult(
                workflow_name="program_analysis",
                success=True,
                output={
                    "program": program_name,
                    "playbook": playbook,
                    "talking_points": talking_points
                },
                agents_used=agents_used,
                execution_time=time.time() - start_time,
                playbook=playbook,
                talking_points=talking_points,
                opportunity_score=75.0  # Would be extracted from analyst output
            )

        except Exception as e:
            logger.error(f"Program analysis workflow error: {e}")
            return ProgramAnalysisResult(
                workflow_name="program_analysis",
                success=False,
                output={"error": str(e)},
                agents_used=agents_used,
                execution_time=time.time() - start_time,
                error=str(e)
            )

    async def prepare_outreach(self, contact_name: str) -> OutreachPrepResult:
        """
        Contact Outreach Prep Workflow
        Sequential: Research -> Analyze -> Strategize -> Write

        Returns personalized outreach materials for the contact.
        """
        import time
        start_time = time.time()

        if not self.agent_team.available:
            return OutreachPrepResult(
                workflow_name="outreach_prep",
                success=False,
                output={"error": "CrewAI not available"},
                agents_used=[],
                execution_time=time.time() - start_time,
                error="CrewAI not available"
            )

        agents_used = []

        try:
            # Task 1: Research agent gets contact context
            research_task = Task(
                description=f"""Research contact: {contact_name}

                Find:
                1. Current company and role
                2. Career history and background
                3. Programs they work on or influence
                4. Any prior interactions with PTS
                5. LinkedIn presence and activity
                6. Clearance level if known

                Search contacts and check memory for any context.""",
                expected_output="Comprehensive contact profile with background",
                agent=self.agent_team.research_agent
            )
            agents_used.append("research")

            # Task 2: Analyst finds relevant jobs/programs
            analyst_task = Task(
                description=f"""Analyze opportunities related to {contact_name}

                Based on the contact research:
                1. Find relevant job postings at their company
                2. Identify programs they may influence
                3. Determine their buying authority
                4. Assess relationship value (1-10)
                5. Identify shared connections or touchpoints

                This helps determine what to discuss with them.""",
                expected_output="Analysis of opportunities and talking points for this contact",
                agent=self.agent_team.analyst_agent,
                context=[research_task]
            )
            agents_used.append("analyst")

            # Task 3: Strategy agent determines approach
            strategy_task = Task(
                description=f"""Develop outreach strategy for {contact_name}

                Based on research and analysis:
                1. Determine best outreach channel (phone, email, LinkedIn)
                2. Identify the right "ask" for initial contact
                3. Find mutual connections or warm intro paths
                4. Determine optimal timing
                5. Plan follow-up sequence (3-touch campaign)

                Consider any past relationship context.""",
                expected_output="Detailed outreach strategy with approach recommendations",
                agent=self.agent_team.strategy_agent,
                context=[research_task, analyst_task]
            )
            agents_used.append("strategy")

            # Task 4: Writer generates outreach materials
            writer_task = Task(
                description=f"""Create outreach materials for {contact_name}

                Generate THREE personalized pieces:

                1. CALL SCRIPT (2-3 minutes):
                   - Opening hook referencing their work
                   - Value proposition for PTS
                   - Specific ask (meeting, intro, etc.)
                   - Objection handling

                2. EMAIL TEMPLATE:
                   - Compelling subject line
                   - Personal opening
                   - Clear value proposition
                   - Specific CTA
                   - Keep under 150 words

                3. LINKEDIN MESSAGE:
                   - Brief, casual tone
                   - Reference mutual interest/connection
                   - Soft ask (conversation, not meeting)
                   - Under 300 characters

                Make all materials feel personal, not templated.""",
                expected_output="Three personalized outreach pieces: call script, email, LinkedIn",
                agent=self.agent_team.writer_agent,
                context=[research_task, analyst_task, strategy_task]
            )
            agents_used.append("writer")

            # Execute the crew
            crew = Crew(
                agents=[
                    self.agent_team.research_agent,
                    self.agent_team.analyst_agent,
                    self.agent_team.strategy_agent,
                    self.agent_team.writer_agent
                ],
                tasks=[research_task, analyst_task, strategy_task, writer_task],
                process=Process.sequential,
                verbose=True
            )

            result = await asyncio.get_event_loop().run_in_executor(
                None, crew.kickoff
            )

            # Parse the output (simple parsing)
            output_str = str(result)

            call_script = ""
            email_template = ""
            linkedin_message = ""

            # Extract sections (basic parsing)
            if "CALL SCRIPT" in output_str:
                parts = output_str.split("CALL SCRIPT")
                if len(parts) > 1:
                    call_script = parts[1].split("EMAIL")[0].strip()

            if "EMAIL" in output_str:
                parts = output_str.split("EMAIL")
                if len(parts) > 1:
                    email_template = parts[1].split("LINKEDIN")[0].strip()

            if "LINKEDIN" in output_str:
                parts = output_str.split("LINKEDIN")
                if len(parts) > 1:
                    linkedin_message = parts[1].strip()

            # Store in memory
            self.memory.remember(
                f"Outreach prep for {contact_name}: Created call script, email, LinkedIn",
                memory_type="outreach",
                metadata={"contact": contact_name, "workflow": "outreach_prep"}
            )

            return OutreachPrepResult(
                workflow_name="outreach_prep",
                success=True,
                output={
                    "contact": contact_name,
                    "materials_generated": True
                },
                agents_used=agents_used,
                execution_time=time.time() - start_time,
                call_script=call_script or output_str,
                email_template=email_template,
                linkedin_message=linkedin_message
            )

        except Exception as e:
            logger.error(f"Outreach prep workflow error: {e}")
            return OutreachPrepResult(
                workflow_name="outreach_prep",
                success=False,
                output={"error": str(e)},
                agents_used=agents_used,
                execution_time=time.time() - start_time,
                error=str(e)
            )

    async def generate_weekly_intel(self) -> WeeklyIntelResult:
        """
        Weekly Intelligence Report Workflow
        Sequential: Research -> Analyze -> Strategize -> Write

        Returns a weekly BD intelligence briefing.
        """
        import time
        start_time = time.time()

        if not self.agent_team.available:
            return WeeklyIntelResult(
                workflow_name="weekly_intel",
                success=False,
                output={"error": "CrewAI not available"},
                agents_used=[],
                execution_time=time.time() - start_time,
                error="CrewAI not available"
            )

        agents_used = []

        try:
            # Task 1: Research agent scans for new opportunities
            research_task = Task(
                description="""Scan for new BD intelligence this week.

                Research:
                1. New job postings from major contractors (last 7 days)
                2. Contract awards and announcements
                3. RFI/RFP releases in DCGS/IC space
                4. News about key programs (AF DCGS, DIA DCGS, Army DCGS)
                5. Leadership changes at customer organizations

                Focus on actionable intelligence, not noise.""",
                expected_output="Summary of new intelligence with sources",
                agent=self.agent_team.research_agent
            )
            agents_used.append("research")

            # Task 2: Analyst identifies hot programs
            analyst_task = Task(
                description="""Analyze hiring patterns and opportunity signals.

                Based on research, analyze:
                1. Which programs show hiring surges (>5 jobs/week)?
                2. Calculate BD priority scores for top opportunities
                3. Identify any contract lifecycle signals (recompete indicators)
                4. Compare week-over-week changes
                5. Flag any urgent items requiring immediate action

                Store significant insights for tracking.""",
                expected_output="Ranked list of hot programs with scores and signals",
                agent=self.agent_team.analyst_agent,
                context=[research_task]
            )
            agents_used.append("analyst")

            # Task 3: Strategy agent prioritizes
            strategy_task = Task(
                description="""Prioritize BD activities for the week.

                Based on analysis:
                1. Rank top 5 opportunities by priority
                2. Identify key contacts to engage this week
                3. Recommend specific actions per opportunity
                4. Flag any competitive threats
                5. Suggest teaming conversations to initiate

                Be specific and actionable.""",
                expected_output="Prioritized action plan for the week",
                agent=self.agent_team.strategy_agent,
                context=[research_task, analyst_task]
            )
            agents_used.append("strategy")

            # Task 4: Writer generates executive briefing
            writer_task = Task(
                description="""Create the Weekly BD Intelligence Briefing.

                Format as executive briefing:

                ## EXECUTIVE SUMMARY
                (2-3 paragraph overview of key findings)

                ## HOT PROGRAMS
                (Ranked list with scores and recommended actions)

                ## NEW OPPORTUNITIES
                (Recently identified, worth investigating)

                ## COMPETITIVE INTELLIGENCE
                (What competitors are doing)

                ## ACTION ITEMS
                (Specific tasks with owners, due this week)

                ## WATCH LIST
                (Things to monitor for next week)

                Keep it concise but comprehensive.""",
                expected_output="Complete weekly intelligence briefing document",
                agent=self.agent_team.writer_agent,
                context=[research_task, analyst_task, strategy_task]
            )
            agents_used.append("writer")

            # Execute the crew
            crew = Crew(
                agents=[
                    self.agent_team.research_agent,
                    self.agent_team.analyst_agent,
                    self.agent_team.strategy_agent,
                    self.agent_team.writer_agent
                ],
                tasks=[research_task, analyst_task, strategy_task, writer_task],
                process=Process.sequential,
                verbose=True
            )

            result = await asyncio.get_event_loop().run_in_executor(
                None, crew.kickoff
            )

            output_str = str(result)

            # Parse hot programs (simple extraction)
            hot_programs = []
            if "HOT PROGRAMS" in output_str:
                hp_section = output_str.split("HOT PROGRAMS")[1].split("##")[0]
                for i, line in enumerate(hp_section.split("\n")):
                    if line.strip() and line.strip()[0].isdigit():
                        hot_programs.append({
                            "rank": i + 1,
                            "description": line.strip()
                        })

            # Parse action items
            action_items = []
            if "ACTION ITEMS" in output_str:
                ai_section = output_str.split("ACTION ITEMS")[1].split("##")[0]
                for line in ai_section.split("\n"):
                    if line.strip().startswith("-") or line.strip().startswith("*"):
                        action_items.append(line.strip()[1:].strip())

            # Extract executive summary
            executive_summary = ""
            if "EXECUTIVE SUMMARY" in output_str:
                es_section = output_str.split("EXECUTIVE SUMMARY")[1].split("##")[0]
                executive_summary = es_section.strip()

            # Store in memory
            self.memory.remember(
                f"Weekly Intel Report generated: {len(hot_programs)} hot programs, {len(action_items)} action items",
                memory_type="report",
                metadata={"workflow": "weekly_intel", "date": datetime.now().isoformat()}
            )

            return WeeklyIntelResult(
                workflow_name="weekly_intel",
                success=True,
                output={
                    "report": output_str,
                    "hot_programs_count": len(hot_programs),
                    "action_items_count": len(action_items)
                },
                agents_used=agents_used,
                execution_time=time.time() - start_time,
                hot_programs=hot_programs,
                action_items=action_items,
                executive_summary=executive_summary
            )

        except Exception as e:
            logger.error(f"Weekly intel workflow error: {e}")
            return WeeklyIntelResult(
                workflow_name="weekly_intel",
                success=False,
                output={"error": str(e)},
                agents_used=agents_used,
                execution_time=time.time() - start_time,
                error=str(e)
            )


# =========================================
# SINGLETON & CONVENIENCE FUNCTIONS
# =========================================

_workflows: Optional[BDWorkflows] = None


def get_workflows() -> BDWorkflows:
    """Get workflows singleton."""
    global _workflows
    if _workflows is None:
        _workflows = BDWorkflows()
    return _workflows


async def analyze_program(program_name: str) -> Dict:
    """Convenience function for program analysis."""
    workflows = get_workflows()
    result = await workflows.analyze_program(program_name)
    return {
        "playbook": result.playbook,
        "priority_contacts": result.priority_contacts,
        "talking_points": result.talking_points,
        "opportunity_score": result.opportunity_score,
        "success": result.success,
        "error": result.error
    }


async def prepare_outreach(contact_name: str) -> Dict:
    """Convenience function for outreach prep."""
    workflows = get_workflows()
    result = await workflows.prepare_outreach(contact_name)
    return {
        "call_script": result.call_script,
        "email_template": result.email_template,
        "linkedin_message": result.linkedin_message,
        "success": result.success,
        "error": result.error
    }


async def generate_weekly_intel() -> Dict:
    """Convenience function for weekly intel."""
    workflows = get_workflows()
    result = await workflows.generate_weekly_intel()
    return {
        "hot_programs": result.hot_programs,
        "new_opportunities": result.new_opportunities,
        "action_items": result.action_items,
        "executive_summary": result.executive_summary,
        "success": result.success,
        "error": result.error
    }
