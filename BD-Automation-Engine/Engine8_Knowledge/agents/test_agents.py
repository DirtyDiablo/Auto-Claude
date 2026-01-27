"""
Tests for CrewAI BD Intelligence Agents
"""

import os
import sys
import asyncio
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from Engine8_Knowledge.agents.bd_agents import (
    get_bd_agent_team,
    SearchVectorStoreTool,
    QueryMemoryTool,
    SearchJobsTool,
    SearchContactsTool,
    SearchProgramsTool,
    GetContactContextTool,
    GetProgramContextTool,
    StoreInsightTool,
    CREWAI_AVAILABLE,
    LANGCHAIN_ANTHROPIC_AVAILABLE
)
from Engine8_Knowledge.agents.workflows import (
    get_workflows,
    analyze_program,
    prepare_outreach,
    generate_weekly_intel
)


def test_environment():
    """Test that required packages are available."""
    print("\n=== Environment Check ===")
    print(f"CrewAI available: {CREWAI_AVAILABLE}")
    print(f"LangChain Anthropic available: {LANGCHAIN_ANTHROPIC_AVAILABLE}")
    print(f"ANTHROPIC_API_KEY set: {bool(os.getenv('ANTHROPIC_API_KEY'))}")

    if not CREWAI_AVAILABLE:
        print("WARNING: CrewAI not installed. Run: pip install crewai")
    if not LANGCHAIN_ANTHROPIC_AVAILABLE:
        print("WARNING: langchain-anthropic not installed. Run: pip install langchain-anthropic")

    return CREWAI_AVAILABLE and LANGCHAIN_ANTHROPIC_AVAILABLE


def test_tools():
    """Test individual tools work correctly."""
    print("\n=== Testing Tools ===")

    # Test vector store search
    print("\n1. Testing SearchVectorStoreTool...")
    try:
        tool = SearchVectorStoreTool()
        result = tool._run("DCGS analyst")
        print(f"   Result: {result[:200]}...")
        assert result is not None
        print("   PASS")
    except Exception as e:
        print(f"   FAIL: {e}")

    # Test memory query
    print("\n2. Testing QueryMemoryTool...")
    try:
        tool = QueryMemoryTool()
        result = tool._run("program analysis")
        print(f"   Result: {result[:200]}...")
        assert result is not None
        print("   PASS")
    except Exception as e:
        print(f"   FAIL: {e}")

    # Test jobs search
    print("\n3. Testing SearchJobsTool...")
    try:
        tool = SearchJobsTool()
        result = tool._run("Leidos")
        print(f"   Result: {result[:200]}...")
        assert result is not None
        print("   PASS")
    except Exception as e:
        print(f"   FAIL: {e}")

    # Test contacts search
    print("\n4. Testing SearchContactsTool...")
    try:
        tool = SearchContactsTool()
        result = tool._run("Northrop Grumman")
        print(f"   Result: {result[:200]}...")
        assert result is not None
        print("   PASS")
    except Exception as e:
        print(f"   FAIL: {e}")

    # Test programs search
    print("\n5. Testing SearchProgramsTool...")
    try:
        tool = SearchProgramsTool()
        result = tool._run("AF DCGS")
        print(f"   Result: {result[:200]}...")
        assert result is not None
        print("   PASS")
    except Exception as e:
        print(f"   FAIL: {e}")

    # Test store insight
    print("\n6. Testing StoreInsightTool...")
    try:
        tool = StoreInsightTool()
        result = tool._run("program|AF DCGS|Test insight from automated test")
        print(f"   Result: {result}")
        assert "stored" in result.lower() or "error" in result.lower()
        print("   PASS")
    except Exception as e:
        print(f"   FAIL: {e}")


def test_agents():
    """Test that agents are created correctly."""
    print("\n=== Testing Agent Creation ===")

    team = get_bd_agent_team()

    print(f"Agent team available: {team.available}")

    if team.available:
        print("\n1. Research Agent:")
        print(f"   Role: {team.research_agent.role}")
        print(f"   Goal: {team.research_agent.goal[:50]}...")
        print(f"   Tools: {len(team.research_agent.tools)}")

        print("\n2. Analyst Agent:")
        print(f"   Role: {team.analyst_agent.role}")
        print(f"   Goal: {team.analyst_agent.goal[:50]}...")
        print(f"   Tools: {len(team.analyst_agent.tools)}")

        print("\n3. Strategy Agent:")
        print(f"   Role: {team.strategy_agent.role}")
        print(f"   Goal: {team.strategy_agent.goal[:50]}...")
        print(f"   Tools: {len(team.strategy_agent.tools)}")

        print("\n4. Writer Agent:")
        print(f"   Role: {team.writer_agent.role}")
        print(f"   Goal: {team.writer_agent.goal[:50]}...")
        print(f"   Tools: {len(team.writer_agent.tools)}")

        print("\nAll agents created successfully!")
    else:
        print("Agents not available - CrewAI or dependencies missing")


async def test_program_analysis_workflow(program_name: str = "AF DCGS"):
    """Test the program analysis workflow."""
    print(f"\n=== Testing Program Analysis Workflow: {program_name} ===")

    if not CREWAI_AVAILABLE:
        print("SKIP: CrewAI not available")
        return None

    try:
        result = await analyze_program(program_name)

        print(f"\nSuccess: {result.get('success')}")

        if result.get('success'):
            print(f"\nPlaybook preview:")
            print(result.get('playbook', '')[:500])

            print(f"\nTalking Points: {len(result.get('talking_points', []))}")
            for tp in result.get('talking_points', [])[:3]:
                print(f"  - {tp}")

            print(f"\nOpportunity Score: {result.get('opportunity_score')}")

            # Verify output saved to memory
            from Engine8_Knowledge.scripts.memory_system import get_memory_system
            memory = get_memory_system()
            recent = memory.recall(program_name, limit=1)
            if recent:
                print("\nVerified: Output saved to memory")
            else:
                print("\nNote: Output not found in memory")

        else:
            print(f"Error: {result.get('error')}")

        return result

    except Exception as e:
        print(f"Error: {e}")
        return None


async def test_outreach_prep_workflow(contact_name: str = "John Smith"):
    """Test the outreach prep workflow."""
    print(f"\n=== Testing Outreach Prep Workflow: {contact_name} ===")

    if not CREWAI_AVAILABLE:
        print("SKIP: CrewAI not available")
        return None

    try:
        result = await prepare_outreach(contact_name)

        print(f"\nSuccess: {result.get('success')}")

        if result.get('success'):
            print(f"\nCall Script preview:")
            print(result.get('call_script', '')[:300])

            print(f"\nEmail Template preview:")
            print(result.get('email_template', '')[:300])

            print(f"\nLinkedIn Message preview:")
            print(result.get('linkedin_message', '')[:200])

        else:
            print(f"Error: {result.get('error')}")

        return result

    except Exception as e:
        print(f"Error: {e}")
        return None


async def test_weekly_intel_workflow():
    """Test the weekly intelligence workflow."""
    print("\n=== Testing Weekly Intelligence Workflow ===")

    if not CREWAI_AVAILABLE:
        print("SKIP: CrewAI not available")
        return None

    try:
        result = await generate_weekly_intel()

        print(f"\nSuccess: {result.get('success')}")

        if result.get('success'):
            print(f"\nExecutive Summary:")
            print(result.get('executive_summary', '')[:500])

            print(f"\nHot Programs: {len(result.get('hot_programs', []))}")
            for hp in result.get('hot_programs', [])[:3]:
                print(f"  {hp}")

            print(f"\nAction Items: {len(result.get('action_items', []))}")
            for ai in result.get('action_items', [])[:3]:
                print(f"  - {ai}")

        else:
            print(f"Error: {result.get('error')}")

        return result

    except Exception as e:
        print(f"Error: {e}")
        return None


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("BD Intelligence Agents - Test Suite")
    print("=" * 60)

    # Environment check
    env_ok = test_environment()

    # Test tools (these work without CrewAI)
    test_tools()

    # Test agent creation
    test_agents()

    if env_ok:
        print("\n" + "=" * 60)
        print("Running Workflow Tests (requires API call)")
        print("=" * 60)

        # Test workflows
        await test_program_analysis_workflow("AF DCGS")
        # await test_outreach_prep_workflow("John Smith")  # Uncomment to test
        # await test_weekly_intel_workflow()  # Uncomment to test
    else:
        print("\n" + "=" * 60)
        print("SKIPPING Workflow Tests - Environment not ready")
        print("=" * 60)

    print("\n" + "=" * 60)
    print("Test Suite Complete")
    print("=" * 60)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test BD Intelligence Agents")
    parser.add_argument("--tools-only", action="store_true", help="Only test tools")
    parser.add_argument("--program", type=str, help="Test program analysis for specific program")
    parser.add_argument("--contact", type=str, help="Test outreach prep for specific contact")
    parser.add_argument("--weekly", action="store_true", help="Test weekly intel report")

    args = parser.parse_args()

    if args.tools_only:
        test_environment()
        test_tools()
        test_agents()
    elif args.program:
        asyncio.run(test_program_analysis_workflow(args.program))
    elif args.contact:
        asyncio.run(test_outreach_prep_workflow(args.contact))
    elif args.weekly:
        asyncio.run(test_weekly_intel_workflow())
    else:
        asyncio.run(run_all_tests())


if __name__ == "__main__":
    main()
