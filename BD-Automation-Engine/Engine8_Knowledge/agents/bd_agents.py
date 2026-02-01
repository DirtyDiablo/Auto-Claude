"""
CrewAI BD Intelligence Agents
4 specialized agents for federal BD operations using CrewAI framework.
"""

import os
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import BaseTool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("CrewAI not available")

try:
    from langchain_anthropic import ChatAnthropic
    LANGCHAIN_ANTHROPIC_AVAILABLE = True
except ImportError:
    LANGCHAIN_ANTHROPIC_AVAILABLE = False
    logger.warning("langchain-anthropic not available")

# Import existing infrastructure
from Engine8_Knowledge.scripts.memory_system import get_memory_system
from Engine8_Knowledge.scripts.rag_router import get_rag_router, RetrievalStrategy
from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore


# =========================================
# TOOL DEFINITIONS
# =========================================

class SearchVectorStoreTool(BaseTool):
    """Tool to search the vector store."""
    name: str = "search_vector_store"
    description: str = (
        "Search the BD knowledge base for relevant information. "
        "Input should be a search query string. "
        "Collections: programs, contacts, jobs, documents, activities"
    )

    def _run(self, query: str, collection: str = None) -> str:
        try:
            store = BDKnowledgeStore()
            if collection:
                results = store.search(query, collection, limit=5)
            else:
                all_results = store.search_all(query, limit_per_collection=3)
                results = []
                for col, items in all_results.items():
                    for item in items:
                        item.collection = col
                        results.append(item)

            if not results:
                return f"No results found for: {query}"

            output = []
            for r in results[:5]:
                output.append(f"[{getattr(r, 'collection', 'unknown')}] Score: {r.score:.2f}")
                output.append(f"  {str(r.payload)[:300]}")
            return "\n".join(output)
        except Exception as e:
            logger.error(f"Vector store search error: {e}")
            return f"Search error: {str(e)}"


class QueryMemoryTool(BaseTool):
    """Tool to query the memory system."""
    name: str = "query_memory"
    description: str = (
        "Query the memory system for past interactions, insights, and context. "
        "Use this to recall previous BD activities and learnings."
    )

    def _run(self, query: str) -> str:
        try:
            memory = get_memory_system()
            memories = memory.recall(query, limit=5)

            if not memories:
                return f"No memories found for: {query}"

            output = ["## Past Context:"]
            for m in memories:
                content = m.get("content", m.get("memory", ""))
                output.append(f"- {content[:200]}")
            return "\n".join(output)
        except Exception as e:
            logger.error(f"Memory query error: {e}")
            return f"Memory error: {str(e)}"


class SearchJobsTool(BaseTool):
    """Tool to search job postings."""
    name: str = "search_jobs"
    description: str = (
        "Search job postings to identify hiring patterns and BD opportunities. "
        "Input should be a program name, company, or skill set."
    )

    def _run(self, query: str) -> str:
        try:
            store = BDKnowledgeStore()
            results = store.search(query, "jobs", limit=10)

            if not results:
                return f"No jobs found for: {query}"

            output = [f"Found {len(results)} relevant job postings:"]
            for r in results:
                payload = r.payload
                output.append(
                    f"- {payload.get('title', 'Unknown')} at {payload.get('company', 'Unknown')}"
                )
                output.append(f"  Clearance: {payload.get('clearance', 'N/A')}")
                if payload.get('mapped_program'):
                    output.append(f"  Program: {payload.get('mapped_program')}")
            return "\n".join(output)
        except Exception as e:
            logger.error(f"Job search error: {e}")
            return f"Job search error: {str(e)}"


class SearchContactsTool(BaseTool):
    """Tool to search contacts."""
    name: str = "search_contacts"
    description: str = (
        "Search for contacts at companies or in programs. "
        "Input should be a company name, program, or role description."
    )

    def _run(self, query: str) -> str:
        try:
            store = BDKnowledgeStore()
            results = store.search(query, "contacts", limit=10)

            if not results:
                return f"No contacts found for: {query}"

            output = [f"Found {len(results)} relevant contacts:"]
            for r in results:
                payload = r.payload
                name = payload.get("name", payload.get("full_name", "Unknown"))
                company = payload.get("company", payload.get("employer", "Unknown"))
                title = payload.get("title", payload.get("job_title", "Unknown"))
                tier = payload.get("tier", "")
                output.append(f"- {name} ({tier})")
                output.append(f"  {title} at {company}")
            return "\n".join(output)
        except Exception as e:
            logger.error(f"Contact search error: {e}")
            return f"Contact search error: {str(e)}"


class SearchProgramsTool(BaseTool):
    """Tool to search programs."""
    name: str = "search_programs"
    description: str = (
        "Search federal programs and contracts. "
        "Input should be a program name, agency, or capability area."
    )

    def _run(self, query: str) -> str:
        try:
            store = BDKnowledgeStore()
            results = store.search(query, "programs", limit=10)

            if not results:
                return f"No programs found for: {query}"

            output = [f"Found {len(results)} relevant programs:"]
            for r in results:
                payload = r.payload
                name = payload.get("name", payload.get("program_name", "Unknown"))
                agency = payload.get("agency", "")
                value = payload.get("value", payload.get("contract_value", ""))
                output.append(f"- {name}")
                if agency:
                    output.append(f"  Agency: {agency}")
                if value:
                    output.append(f"  Value: {value}")
            return "\n".join(output)
        except Exception as e:
            logger.error(f"Program search error: {e}")
            return f"Program search error: {str(e)}"


class GetContactContextTool(BaseTool):
    """Tool to get full context for a contact."""
    name: str = "get_contact_context"
    description: str = (
        "Get full context for a contact including past interactions and insights. "
        "Input should be the contact's name."
    )

    def _run(self, contact_name: str) -> str:
        try:
            memory = get_memory_system()
            context = memory.get_contact_context(contact_name)

            output = [f"## Context for {contact_name}:"]

            interactions = context.get("interactions", [])
            if interactions:
                output.append("\n### Past Interactions:")
                for i in interactions[:5]:
                    output.append(f"- {i.get('interaction_type', 'Unknown')}: {i.get('notes', '')[:100]}")

            memories = context.get("memories", [])
            if memories:
                output.append("\n### Memories:")
                for m in memories[:5]:
                    content = m.get("content", m.get("memory", ""))
                    output.append(f"- {content[:150]}")

            if not interactions and not memories:
                output.append("No prior context found for this contact.")

            return "\n".join(output)
        except Exception as e:
            logger.error(f"Contact context error: {e}")
            return f"Contact context error: {str(e)}"


class GetProgramContextTool(BaseTool):
    """Tool to get full context for a program."""
    name: str = "get_program_context"
    description: str = (
        "Get full context for a program including insights and past analysis. "
        "Input should be the program name."
    )

    def _run(self, program_name: str) -> str:
        try:
            memory = get_memory_system()
            context = memory.get_program_context(program_name)

            output = [f"## Context for {program_name}:"]

            insights = context.get("insights", [])
            if insights:
                output.append("\n### Insights:")
                for i in insights[:5]:
                    output.append(f"- {i.get('insight', '')[:150]}")

            memories = context.get("memories", [])
            if memories:
                output.append("\n### Memories:")
                for m in memories[:5]:
                    content = m.get("content", m.get("memory", ""))
                    output.append(f"- {content[:150]}")

            if not insights and not memories:
                output.append("No prior context found for this program.")

            return "\n".join(output)
        except Exception as e:
            logger.error(f"Program context error: {e}")
            return f"Program context error: {str(e)}"


class StoreInsightTool(BaseTool):
    """Tool to store insights in memory."""
    name: str = "store_insight"
    description: str = (
        "Store an insight or finding in the memory system for future reference. "
        "Input format: 'entity_type|entity_name|insight' "
        "Example: 'program|AF DCGS|Strong hiring indicates upcoming recompete'"
    )

    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split("|")
            if len(parts) < 3:
                return "Invalid format. Use: entity_type|entity_name|insight"

            entity_type = parts[0].strip()
            entity_name = parts[1].strip()
            insight = parts[2].strip()

            memory = get_memory_system()
            memory.db.add_insight(entity_type, entity_name, insight, source="bd_agent")

            return f"Insight stored for {entity_type} '{entity_name}'"
        except Exception as e:
            logger.error(f"Store insight error: {e}")
            return f"Store insight error: {str(e)}"


# =========================================
# AGENT DEFINITIONS
# =========================================

def get_llm():
    """Get the LLM instance for CrewAI agents."""
    if not LANGCHAIN_ANTHROPIC_AVAILABLE:
        logger.warning("langchain-anthropic not available, agents may not work")
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set")
        return None

    return ChatAnthropic(
        model="claude-sonnet-4-20250514",
        anthropic_api_key=api_key,
        temperature=0.7,
        max_tokens=4096
    )


def create_research_agent() -> Optional[Agent]:
    """Create the Federal Contract Researcher agent."""
    if not CREWAI_AVAILABLE:
        return None

    return Agent(
        role="Federal Contract Researcher",
        goal="Gather intelligence on federal programs, contracts, and competitors",
        backstory="""You are an expert federal contract researcher with deep knowledge
of DoD and IC programs, particularly the DCGS portfolio (~$950M). You have
15+ years of experience tracking contract awards, recompetes, and teaming
arrangements. You excel at finding publicly available information and
synthesizing it into actionable intelligence.""",
        tools=[
            SearchVectorStoreTool(),
            SearchProgramsTool(),
            QueryMemoryTool(),
            GetProgramContextTool(),
        ],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )


def create_analyst_agent() -> Optional[Agent]:
    """Create the BD Intelligence Analyst agent."""
    if not CREWAI_AVAILABLE:
        return None

    return Agent(
        role="BD Intelligence Analyst",
        goal="Analyze hiring patterns, identify opportunities, and score BD leads",
        backstory="""You are a data analyst specializing in defense contractor
staffing patterns. You can identify when companies are ramping up for new
contracts based on their job postings. You understand clearance requirements,
skill alignments, and program lifecycles. Your analysis has consistently
predicted contract wins 6+ months in advance.""",
        tools=[
            SearchJobsTool(),
            SearchProgramsTool(),
            QueryMemoryTool(),
            StoreInsightTool(),
        ],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )


def create_strategy_agent() -> Optional[Agent]:
    """Create the BD Strategy Architect agent."""
    if not CREWAI_AVAILABLE:
        return None

    return Agent(
        role="BD Strategy Architect",
        goal="Develop approach strategies, prioritize contacts, and plan outreach sequences",
        backstory="""You are a senior BD strategist with a proven track record of
winning federal contracts. You specialize in building teaming relationships,
identifying gate-keepers, and developing multi-touch outreach campaigns.
You understand the federal acquisition process and how to position for wins.
Your strategies have resulted in $500M+ in contract wins.""",
        tools=[
            SearchContactsTool(),
            GetContactContextTool(),
            QueryMemoryTool(),
            StoreInsightTool(),
        ],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )


def create_writer_agent() -> Optional[Agent]:
    """Create the BD Content Specialist agent."""
    if not CREWAI_AVAILABLE:
        return None

    return Agent(
        role="BD Content Specialist",
        goal="Generate personalized playbooks, call scripts, and email templates",
        backstory="""You are a BD content specialist who crafts compelling,
personalized outreach materials. You understand federal contractor culture
and know how to speak their language. You create materials that resonate
with technical decision-makers and program managers. Your call scripts
and emails have a 40%+ response rate.""",
        tools=[
            GetProgramContextTool(),
            GetContactContextTool(),
            QueryMemoryTool(),
        ],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )


# =========================================
# AGENT FACTORY
# =========================================

@dataclass
class BDAgentTeam:
    """Container for the BD agent team."""
    research_agent: Optional[Agent]
    analyst_agent: Optional[Agent]
    strategy_agent: Optional[Agent]
    writer_agent: Optional[Agent]
    available: bool


def create_bd_agent_team() -> BDAgentTeam:
    """Create the full BD agent team."""
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available - agents will be None")
        return BDAgentTeam(
            research_agent=None,
            analyst_agent=None,
            strategy_agent=None,
            writer_agent=None,
            available=False
        )

    return BDAgentTeam(
        research_agent=create_research_agent(),
        analyst_agent=create_analyst_agent(),
        strategy_agent=create_strategy_agent(),
        writer_agent=create_writer_agent(),
        available=True
    )


# Singleton instance
_agent_team: Optional[BDAgentTeam] = None


def get_bd_agent_team() -> BDAgentTeam:
    """Get the BD agent team singleton."""
    global _agent_team
    if _agent_team is None:
        _agent_team = create_bd_agent_team()
    return _agent_team
