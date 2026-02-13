"""
Pre-configured Dify applications that leverage your existing BD infrastructure.

These app templates can be imported into Dify to quickly set up:
1. BD Research Chat - Uses Qdrant for RAG
2. Call Prep Generator - Uses CrewAI agents
3. Pipeline Controller - Uses n8n workflows
4. Outreach Drafter - Uses HUMINT collection

Each app connects to your existing tools without duplicating data or logic.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .dify_qdrant_bridge import DifyQdrantBridge
from .dify_crewai_bridge import DifyCrewAIBridge
from .dify_n8n_bridge import DifyN8NBridge

logger = logging.getLogger(__name__)


@dataclass
class DifyAppConfig:
    """Configuration for a Dify application."""
    name: str
    mode: str  # chat, workflow, agent-chat, completion
    icon: str
    description: str
    system_prompt: str
    tools: List[str]
    knowledge_sources: List[str]
    model_config: Dict[str, Any]


class BDDifyApps:
    """
    BD applications built on Dify, using your existing infrastructure.

    Apps:
    1. BD Research Chat - Research assistant using your 8,447+ indexed documents
    2. Call Prep Workflow - Generate call briefs using your existing agents
    3. Pipeline Controller - Natural language control of your n8n pipelines
    4. Outreach Drafter - Draft personalized BD messages

    These are TEMPLATES - import them into Dify and customize as needed.
    """

    def __init__(self):
        """Initialize app manager with bridges to your existing tools."""
        self.qdrant_bridge = DifyQdrantBridge()
        self.crewai_bridge = DifyCrewAIBridge()
        self.n8n_bridge = DifyN8NBridge()

    def get_app_configs(self) -> Dict[str, DifyAppConfig]:
        """
        Get all pre-configured app templates.

        Returns:
            Dict mapping app names to their configurations
        """
        return {
            'bd_research_chat': self._get_research_chat_config(),
            'call_prep_workflow': self._get_call_prep_config(),
            'pipeline_controller': self._get_pipeline_controller_config(),
            'outreach_drafter': self._get_outreach_drafter_config(),
            'program_analyzer': self._get_program_analyzer_config(),
            'competitor_intel': self._get_competitor_intel_config(),
        }

    def _get_research_chat_config(self) -> DifyAppConfig:
        """BD Research Chat app configuration."""
        return DifyAppConfig(
            name="BD Research Chat",
            mode="chat",
            icon="magnifying-glass",
            description="Research assistant using your 8,447+ indexed documents. Search contacts, programs, jobs, and documents with natural language.",
            system_prompt="""You are the BD Research Assistant for PTS (Prime Tech Solutions). You help the BD team research federal defense programs, contacts, and business opportunities.

You have access to a knowledge base with:
- 7,337 contacts with tier classification (Tier 1-6)
- 401 federal programs and contracts
- 205 documents (past performance, briefings, RFPs)
- 500 activity records (call notes, meeting records)
- Job postings with BD priority scores

Target Market: DCGS portfolio (~$950M) across Air Force, Army, and Navy

When answering questions:
1. Search the knowledge base first
2. Cite your sources with contact names, program names, or document titles
3. Highlight Tier 1 and Tier 2 contacts as priority
4. Note clearance requirements when relevant
5. Suggest follow-up actions when appropriate

Be direct and actionable. The BD team needs intelligence they can act on today.""",
            tools=[
                "qdrant_search",
                "qdrant_contacts",
                "qdrant_programs",
                "qdrant_smart_query"
            ],
            knowledge_sources=[
                "qdrant_external"  # Your existing Qdrant, not duplicated
            ],
            model_config={
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.3,
                "max_tokens": 4096
            }
        )

    def _get_call_prep_config(self) -> DifyAppConfig:
        """Call Prep Workflow app configuration."""
        return DifyAppConfig(
            name="Call Prep Generator",
            mode="workflow",
            icon="phone",
            description="Generate comprehensive call preparation briefs using AI agents. Pulls contact history, program intel, and suggests talking points.",
            system_prompt="""Generate a call preparation brief for the BD team.

Include:
1. Contact Background
   - Name, title, company
   - Tier classification and influence level
   - Previous interactions (from HUMINT)

2. Program Context
   - Programs they work on
   - Current contract status
   - Upcoming opportunities

3. Talking Points
   - Relevant capabilities to mention
   - Questions to ask
   - Pain points to address

4. Meeting Objectives
   - Primary goal
   - Secondary objectives
   - Next steps to propose

Use the PTS BD formula: Problem → Capability → Proof → Ask""",
            tools=[
                "contact_finder_agent",
                "program_intel_agent",
                "qdrant_contacts",
                "memory_search"
            ],
            knowledge_sources=["qdrant_humint"],
            model_config={
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.4,
                "max_tokens": 4096
            }
        )

    def _get_pipeline_controller_config(self) -> DifyAppConfig:
        """Pipeline Controller app configuration."""
        return DifyAppConfig(
            name="Pipeline Controller",
            mode="agent-chat",
            icon="gear",
            description="Natural language control of your n8n BD automation pipelines. Trigger scraping, enrichment, alerts, and reports.",
            system_prompt="""You are the Pipeline Controller for the BD Automation Engine. You help the team manage and trigger automation workflows using natural language.

Available workflows:
1. job_scraper - Scrape jobs from ClearanceJobs, LinkedIn, competitor sites
2. job_enrichment - AI enrichment: program mapping, BD scoring
3. contact_classification - Assign contacts to OrgChart tiers
4. hot_lead_alert - Send alerts for high-priority leads
5. weekly_report - Generate weekly BD intelligence report
6. clearance_rag - Search clearance job postings
7. firecrawl_search - Web search for competitor intel
8. master_pipeline - Full automation pipeline

When the user asks to run a workflow:
1. Confirm the workflow and parameters
2. Trigger the workflow via the n8n bridge
3. Report the result

Example interactions:
- "Run the job scraper for DCGS positions" → trigger job_scraper with keywords=["DCGS"]
- "Send a hot lead alert for John Smith" → trigger hot_lead_alert
- "Generate this week's report" → trigger weekly_report""",
            tools=[
                "n8n_trigger",
                "n8n_job_scraper",
                "n8n_hot_lead",
                "n8n_weekly_report",
                "n8n_master_pipeline"
            ],
            knowledge_sources=[],
            model_config={
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.2,
                "max_tokens": 2048
            }
        )

    def _get_outreach_drafter_config(self) -> DifyAppConfig:
        """Outreach Drafter app configuration."""
        return DifyAppConfig(
            name="Outreach Message Drafter",
            mode="workflow",
            icon="envelope",
            description="Draft personalized BD outreach messages using the PTS formula and your contact intelligence.",
            system_prompt="""Draft personalized BD outreach messages for federal defense contacts.

Use the PTS BD Formula:
P - Problem: Identify their challenge or pain point
T - Technology: Present our relevant capability
S - Success: Cite proof points and past performance

Message Types:
1. LinkedIn Connection Request (300 char limit)
2. Email Introduction (2-3 paragraphs)
3. Call Script (3-5 minute conversation)
4. Follow-up Email (after meeting)

Personalization Requirements:
- Reference their program by name
- Mention mutual connections if any
- Cite relevant past performance
- Include specific value proposition

Tone: Professional but conversational. We're building relationships, not selling.""",
            tools=[
                "contact_finder_agent",
                "bd_strategy_agent",
                "qdrant_contacts",
                "qdrant_humint"
            ],
            knowledge_sources=["qdrant_humint", "qdrant_documents"],
            model_config={
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.6,
                "max_tokens": 2048
            }
        )

    def _get_program_analyzer_config(self) -> DifyAppConfig:
        """Program Analyzer app configuration."""
        return DifyAppConfig(
            name="Program Analyzer",
            mode="agent-chat",
            icon="target",
            description="Deep analysis of federal programs using multi-agent workflow. Generates capture strategies and BD playbooks.",
            system_prompt="""You are the Program Analysis Agent for PTS BD operations.

When asked to analyze a program, you orchestrate multiple agents:
1. Program Intel Agent - Gather contract details, incumbents, timeline
2. Company Research Agent - Competitive landscape
3. Contact Finder Agent - Key stakeholders and decision makers
4. BD Strategy Agent - Win themes and capture approach

Your output should include:
1. Program Overview
   - Contract details (value, period, vehicle)
   - Current incumbent and performance
   - Recompete timeline

2. Competitive Assessment
   - Key competitors and their positioning
   - Our strengths vs competition
   - Differentiators

3. Relationship Map
   - Tier 1-2 contacts to engage
   - Decision makers
   - Influencers

4. Capture Strategy
   - Win themes
   - Teaming opportunities
   - 90-day action plan

5. BD Priority Score (0-100)
   - Score breakdown
   - Recommendation (pursue/monitor/pass)""",
            tools=[
                "program_intel_agent",
                "company_research_agent",
                "contact_finder_agent",
                "bd_strategy_agent",
                "crewai_analyze_program"
            ],
            knowledge_sources=["qdrant_programs", "qdrant_contacts"],
            model_config={
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.3,
                "max_tokens": 8192
            }
        )

    def _get_competitor_intel_config(self) -> DifyAppConfig:
        """Competitor Intelligence app configuration."""
        return DifyAppConfig(
            name="Competitor Intelligence",
            mode="chat",
            icon="users",
            description="Research competitors, their programs, key personnel, and win/loss patterns.",
            system_prompt="""You are the Competitive Intelligence Analyst for PTS.

Help the BD team understand competitors:
1. Company profiles (size, capabilities, clearances)
2. Programs they prime or sub on
3. Key personnel (especially former government)
4. Win/loss history
5. Teaming patterns

Major competitors in DCGS portfolio:
- Northrop Grumman (DCGS-A incumbent)
- General Dynamics (GDIT)
- Leidos
- Raytheon
- L3Harris

When researching a competitor:
1. Search your knowledge base first
2. Note their program involvement
3. Identify key contacts we should know
4. Assess their positioning vs ours
5. Recommend counter-positioning strategies

Be factual and cite your sources. Avoid speculation without data.""",
            tools=[
                "company_research_agent",
                "qdrant_search",
                "qdrant_contacts",
                "firecrawl_search"
            ],
            knowledge_sources=["qdrant_programs", "qdrant_contacts", "qdrant_documents"],
            model_config={
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.3,
                "max_tokens": 4096
            }
        )

    def export_app_config(self, app_name: str, format: str = "yaml") -> str:
        """
        Export an app configuration for import into Dify.

        Args:
            app_name: Name of app to export
            format: Output format (yaml or json)

        Returns:
            Configuration string ready for Dify import
        """
        configs = self.get_app_configs()
        if app_name not in configs:
            raise ValueError(f"Unknown app: {app_name}. Available: {list(configs.keys())}")

        config = configs[app_name]

        if format == "json":
            import json
            return json.dumps({
                "name": config.name,
                "mode": config.mode,
                "icon": config.icon,
                "description": config.description,
                "model_config": config.model_config,
                "opening_statement": f"Welcome to {config.name}! How can I help you today?",
                "suggested_questions": self._get_suggested_questions(app_name),
                "prompt_config": {
                    "prompt_template": config.system_prompt
                },
                "external_knowledge_id": None,  # Set after creating external knowledge
                "tools": config.tools
            }, indent=2)

        else:  # yaml
            import yaml
            return yaml.dump({
                "name": config.name,
                "mode": config.mode,
                "icon": config.icon,
                "description": config.description,
                "model_config": config.model_config,
                "prompt_config": {
                    "prompt_template": config.system_prompt
                },
                "tools": config.tools
            }, default_flow_style=False)

    def _get_suggested_questions(self, app_name: str) -> List[str]:
        """Get suggested opening questions for an app."""
        suggestions = {
            'bd_research_chat': [
                "Who are the Tier 1 contacts for AF DCGS?",
                "What programs does Northrop Grumman prime on?",
                "Find TS/SCI jobs related to ISR",
                "What's our past performance on DCGS programs?"
            ],
            'call_prep_workflow': [
                "Prepare me for a call with John Smith at GDIT",
                "Generate a brief for my meeting about DCGS-A",
                "What should I know before calling the DCGS program manager?"
            ],
            'pipeline_controller': [
                "Run the job scraper for DCGS positions",
                "Generate this week's BD report",
                "Trigger enrichment for pending jobs",
                "Send a hot lead alert"
            ],
            'outreach_drafter': [
                "Draft a LinkedIn message for a DCGS program manager",
                "Write an introduction email for Northrop contact",
                "Create a follow-up email after yesterday's meeting"
            ],
            'program_analyzer': [
                "Analyze the AF DCGS program for capture",
                "What's our win probability for DCGS-A recompete?",
                "Generate a capture strategy for GBSD"
            ],
            'competitor_intel': [
                "Research Northrop Grumman's DCGS capabilities",
                "What programs does GDIT compete with us on?",
                "Who are the key Leidos contacts in ISR?"
            ]
        }
        return suggestions.get(app_name, [])

    async def initialize_in_dify(self, _dify_api_url: str, _dify_api_key: str) -> Dict[str, str]:
        """
        Initialize all apps in a Dify instance.

        Note: This is a placeholder. Actual Dify API integration would require
        their specific API endpoints which vary by version.

        Args:
            dify_api_url: Dify API URL
            dify_api_key: Dify API key

        Returns:
            Dict mapping app names to their Dify IDs
        """
        logger.info("Dify app initialization is manual - use export_app_config() to get configs")
        return {
            app_name: f"export:{app_name}"
            for app_name in self.get_app_configs().keys()
        }


# Convenience function to print all app configs
def print_app_configs():
    """Print all app configurations for review."""
    apps = BDDifyApps()
    configs = apps.get_app_configs()

    print("\n" + "=" * 60)
    print("BD Dify Application Templates")
    print("=" * 60)

    for name, config in configs.items():
        print(f"\n{config.icon} {config.name}")
        print(f"   Mode: {config.mode}")
        print(f"   Description: {config.description}")
        print(f"   Tools: {', '.join(config.tools)}")
        print(f"   Knowledge: {', '.join(config.knowledge_sources) or 'None'}")

    print("\n" + "=" * 60)
    print("Export with: BDDifyApps().export_app_config('app_name', 'json')")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print_app_configs()
