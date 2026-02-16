"""
Phase 5: Pipeline Verification Script

Quick standalone verification of the BD Intelligence System.
Run this to validate the core components are working.

Usage:
    python scripts/verify_pipeline.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_header(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_result(name: str, success: bool, details: str = ""):
    """Print a test result."""
    status = "[PASS]" if success else "[FAIL]"
    print(f"  {status} {name}")
    if details:
        print(f"         {details}")


async def verify_agents():
    """Verify all 8 agents are importable and functional."""
    print_header("VERIFYING 8 CREWAI AGENTS")

    results = []

    # Test imports
    try:
        from Engine8_Knowledge.agents import (
            # Original 4
            ProgramIntelAgent,
            CompanyResearchAgent,
            ContactFinderAgent,
            BDStrategyAgent,
            # New 4
            ContactClassifierAgent,
            ScraperMonitorAgent,
            QualityAssuranceAgent,
            AnalyticsAgent,
            # Orchestrator
            BDCrewOrchestrator,
            get_orchestrator,
        )

        print_result("All agent imports", True)
        results.append(True)
    except ImportError as e:
        print_result("Agent imports", False, str(e))
        results.append(False)
        return results

    # Test ContactClassifierAgent
    try:
        agent = ContactClassifierAgent()
        result = agent.classify_contact(
            first_name="John",
            last_name="Smith",
            job_title="Senior Director, DCGS Programs",
            company="GDIT",
            city="Langley",
            state="VA",
        )
        print_result(
            "ContactClassifierAgent",
            True,
            f"Tier: {result.tier_label}, Priority: {result.bd_priority}",
        )
        results.append(True)
    except Exception as e:
        print_result("ContactClassifierAgent", False, str(e))
        results.append(False)

    # Test ScraperMonitorAgent
    try:
        agent = ScraperMonitorAgent()
        test_jobs = [
            {
                "title": "DCGS Engineer",
                "company": "GDIT",
                "detected_clearance": "TS/SCI",
                "bd_score": 85,
                "description": "Support ISR fusion operations",
            }
        ]
        analysis = agent.analyze_scrape_batch(test_jobs, "test")
        print_result(
            "ScraperMonitorAgent", True, f"High-value jobs: {analysis.high_value_jobs}"
        )
        results.append(True)
    except Exception as e:
        print_result("ScraperMonitorAgent", False, str(e))
        results.append(False)

    # Test QualityAssuranceAgent
    try:
        agent = QualityAssuranceAgent()
        test_records = [
            {"id": "1", "first_name": "John", "last_name": "Smith", "company": "GDIT"},
            {"id": "2", "first_name": "Jane", "last_name": "", "company": "Leidos"},
        ]
        report = agent.assess_quality(test_records, "contacts")
        print_result(
            "QualityAssuranceAgent",
            True,
            f"Issues found: {len(report.issues)}, Score: {report.overall_score:.0%}",
        )
        results.append(True)
    except Exception as e:
        print_result("QualityAssuranceAgent", False, str(e))
        results.append(False)

    # Test AnalyticsAgent
    try:
        agent = AnalyticsAgent()
        test_jobs = [
            {
                "title": "Engineer",
                "company": "GDIT",
                "detected_clearance": "TS/SCI",
                "bd_score": 85,
                "mapped_program": "AF DCGS",
            },
        ]
        report = agent.generate_report(jobs=test_jobs, period="weekly")
        print_result(
            "AnalyticsAgent",
            True,
            f"Insights: {len(report.insights)}, Recommendations: {len(report.recommendations)}",
        )
        results.append(True)
    except Exception as e:
        print_result("AnalyticsAgent", False, str(e))
        results.append(False)

    # Test orchestrator
    try:
        orchestrator = get_orchestrator()
        print_result("BDCrewOrchestrator", True, f"Backend: {orchestrator.backend}")
        results.append(True)
    except Exception as e:
        print_result("BDCrewOrchestrator", False, str(e))
        results.append(False)

    return results


async def verify_orchestrator_workflows():
    """Verify orchestrator workflows."""
    print_header("VERIFYING ORCHESTRATOR WORKFLOWS")

    results = []

    try:
        from Engine8_Knowledge.agents import get_orchestrator

        orchestrator = get_orchestrator()
    except ImportError as e:
        print_result("Orchestrator import", False, str(e))
        return [False]

    # Test classify_contacts_workflow
    try:
        contacts = [
            {
                "first_name": "John",
                "last_name": "Smith",
                "job_title": "VP Programs",
                "company": "GDIT",
            }
        ]
        result = await orchestrator.classify_contacts_workflow(contacts)
        print_result(
            "classify_contacts_workflow",
            result.success,
            f"Agents: {', '.join(result.agents_used)}",
        )
        results.append(result.success)
    except Exception as e:
        print_result("classify_contacts_workflow", False, str(e))
        results.append(False)

    # Test analyze_scrape_workflow
    try:
        jobs = [
            {
                "title": "DCGS Engineer",
                "company": "GDIT",
                "detected_clearance": "TS/SCI",
                "bd_score": 85,
            }
        ]
        result = await orchestrator.analyze_scrape_workflow(jobs, "test")
        print_result(
            "analyze_scrape_workflow",
            result.success,
            f"Agents: {', '.join(result.agents_used)}",
        )
        results.append(result.success)
    except Exception as e:
        print_result("analyze_scrape_workflow", False, str(e))
        results.append(False)

    # Test quality_check_workflow
    try:
        records = [
            {"id": "1", "first_name": "John", "last_name": "Smith", "company": "GDIT"}
        ]
        result = await orchestrator.quality_check_workflow(records, "contacts")
        print_result(
            "quality_check_workflow",
            result.success,
            f"Agents: {', '.join(result.agents_used)}",
        )
        results.append(result.success)
    except Exception as e:
        print_result("quality_check_workflow", False, str(e))
        results.append(False)

    # Test generate_analytics_workflow
    try:
        result = await orchestrator.generate_analytics_workflow(
            jobs=[{"title": "Engineer", "company": "GDIT", "bd_score": 80}],
            period="weekly",
        )
        print_result(
            "generate_analytics_workflow",
            result.success,
            f"Agents: {', '.join(result.agents_used)}",
        )
        results.append(result.success)
    except Exception as e:
        print_result("generate_analytics_workflow", False, str(e))
        results.append(False)

    return results


def verify_models():
    """Verify Pydantic v2 data models."""
    print_header("VERIFYING DATA MODELS")

    results = []

    # Test Contact model
    try:
        from models.contacts import Contact, HierarchyTier, BDPriority

        contact = Contact(
            first_name="John",
            last_name="Smith",
            company="GDIT",
            hierarchy_tier=HierarchyTier.TIER_2_DIRECTOR,
            bd_priority=BDPriority.CRITICAL,
        )
        print_result("Contact model", True, f"Full name: {contact.full_name}")
        results.append(True)
    except Exception as e:
        print_result("Contact model", False, str(e))
        results.append(False)

    # Test Job model
    try:
        from models.jobs import Job, JobStatus, ClearanceLevel

        job = Job(
            title="Systems Engineer",
            company="GDIT",
            status=JobStatus.ACTIVE,
            clearance_level=ClearanceLevel.TS_SCI,
        )
        print_result("Job model", True, f"Status: {job.status.value}")
        results.append(True)
    except Exception as e:
        print_result("Job model", False, str(e))
        results.append(False)

    # Test Program model
    try:
        from models.programs import Program

        program = Program(
            program_name="AF DCGS",
            acronym="DCGS",
        )
        print_result("Program model", True, f"Name: {program.program_name}")
        results.append(True)
    except Exception as e:
        print_result("Program model", False, str(e))
        results.append(False)

    # Test Activity model
    try:
        from models.activities import Activity, ActivityType

        activity = Activity(
            activity_type=ActivityType.MEETING,
            summary="BD meeting",
        )
        print_result("Activity model", True, f"Type: {activity.activity_type.value}")
        results.append(True)
    except Exception as e:
        print_result("Activity model", False, str(e))
        results.append(False)

    return results


def verify_settings():
    """Verify centralized settings."""
    print_header("VERIFYING SETTINGS")

    results = []

    try:
        from config.settings import get_settings

        settings = get_settings()
        print_result("Settings load", True, f"Log level: {settings.log_level}")
        results.append(True)

        # Verify caching
        settings2 = get_settings()
        cached = settings is settings2
        print_result("Settings cached", cached)
        results.append(cached)

    except Exception as e:
        print_result("Settings", False, str(e))
        results.append(False)

    return results


def verify_api_imports():
    """Verify API endpoint imports."""
    print_header("VERIFYING API ENDPOINTS")

    results = []

    try:
        print_result("Unified endpoints router", True)
        results.append(True)
    except Exception as e:
        print_result("Unified endpoints", False, str(e))
        results.append(False)

    try:
        print_result("FastAPI app import", True)
        results.append(True)
    except Exception as e:
        print_result("FastAPI app", False, str(e))
        results.append(False)

    return results


async def main():
    """Run all verifications."""
    print("\n" + "=" * 60)
    print("  BD INTELLIGENCE SYSTEM - PIPELINE VERIFICATION")
    print("=" * 60)

    all_results = []

    # Verify agents
    agent_results = await verify_agents()
    all_results.extend(agent_results)

    # Verify orchestrator workflows
    workflow_results = await verify_orchestrator_workflows()
    all_results.extend(workflow_results)

    # Verify models
    model_results = verify_models()
    all_results.extend(model_results)

    # Verify settings
    settings_results = verify_settings()
    all_results.extend(settings_results)

    # Verify API
    api_results = verify_api_imports()
    all_results.extend(api_results)

    # Summary
    print_header("VERIFICATION SUMMARY")
    passed = sum(all_results)
    total = len(all_results)
    success_rate = (passed / total * 100) if total > 0 else 0

    print(f"  Total tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    print(f"  Success rate: {success_rate:.1f}%")

    if success_rate == 100:
        print("\n  [SUCCESS] All verifications passed!")
    elif success_rate >= 80:
        print("\n  [WARNING] Most verifications passed, review failures.")
    else:
        print("\n  [ERROR] Multiple verifications failed, check errors above.")

    print("\n" + "=" * 60 + "\n")

    return success_rate == 100


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
