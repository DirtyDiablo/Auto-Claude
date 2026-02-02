"""
Phase 5: Integration Testing for BD Intelligence System

End-to-end tests for:
- All 8 CrewAI agents
- Orchestrator workflows
- Unified data models
- API endpoints
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, List

# Test data
SAMPLE_CONTACTS = [
    {
        "id": "c1",
        "first_name": "John",
        "last_name": "Smith",
        "job_title": "Senior Director, DCGS Programs",
        "company": "GDIT",
        "city": "Langley",
        "state": "VA",
        "email": "john.smith@gdit.com",
    },
    {
        "id": "c2",
        "first_name": "Jane",
        "last_name": "Doe",
        "job_title": "VP, Federal Programs",
        "company": "Leidos",
        "city": "Reston",
        "state": "VA",
        "email": "jane.doe@leidos.com",
    },
    {
        "id": "c3",
        "first_name": "Bob",
        "last_name": "Jones",
        "job_title": "Systems Engineer",
        "company": "SAIC",
        "city": "San Diego",
        "state": "CA",
        "confidence_score": 0.3,
    },
    {
        "id": "c4",
        "first_name": "John",
        "last_name": "Smith",
        "job_title": "Senior Director",
        "company": "GDIT",
        "city": "Langley",
        "state": "VA",
    },  # Duplicate
]

SAMPLE_JOBS = [
    {
        "id": "j1",
        "title": "Senior Network Engineer - DCGS",
        "company": "GDIT",
        "detected_clearance": "TS/SCI",
        "bd_score": 85,
        "mapped_program": "AF DCGS",
        "location": "Langley, VA",
        "description": "Support DCGS-A fusion operations and ISR data processing",
    },
    {
        "id": "j2",
        "title": "Systems Administrator",
        "company": "Leidos",
        "detected_clearance": "Secret",
        "bd_score": 60,
        "mapped_program": "Army DCGS-A",
        "location": "Fort Huachuca, AZ",
        "description": "IT support role for Army intelligence systems",
    },
    {
        "id": "j3",
        "title": "Cyber Security Analyst",
        "company": "Northrop Grumman",
        "detected_clearance": "TS/SCI Poly",
        "bd_score": 90,
        "mapped_program": "AF DCGS",
        "location": "Wright-Patterson AFB, OH",
        "description": "SIGINT analyst supporting distributed ground systems",
    },
]

SAMPLE_PROGRAMS = [
    {
        "program_name": "AF DCGS",
        "acronym": "DCGS",
        "keywords": ["recompete", "follow-on", "Block 5"],
    },
    {
        "program_name": "Army DCGS-A",
        "acronym": "DCGS-A",
        "keywords": ["transition", "modernization"],
    },
]


# ============================================
# Phase 4 Agent Tests
# ============================================

class TestContactClassifierAgent:
    """Test ContactClassifierAgent."""

    @pytest.fixture
    def agent(self):
        from Engine8_Knowledge.agents import ContactClassifierAgent
        return ContactClassifierAgent()

    def test_classify_tier_executive(self, agent):
        """Test tier classification for executives."""
        tier, label, signals = agent.classify_tier("VP, Federal Programs")
        assert tier == 1
        assert "Tier 1" in label
        assert len(signals) > 0

    def test_classify_tier_director(self, agent):
        """Test tier classification for directors."""
        tier, label, signals = agent.classify_tier("Senior Director, DCGS Programs")
        assert tier == 2
        assert "Tier 2" in label

    def test_classify_tier_manager(self, agent):
        """Test tier classification for managers."""
        tier, label, signals = agent.classify_tier("Program Manager")
        assert tier == 3
        assert "Tier 3" in label

    def test_classify_tier_default(self, agent):
        """Test default tier classification."""
        tier, label, signals = agent.classify_tier("Consultant")
        assert tier in [5, 6]

    def test_classify_program(self, agent):
        """Test program classification."""
        program, signals = agent.classify_program(
            "DCGS Program Lead", "GDIT", "Langley, VA"
        )
        assert program == "AF DCGS - Langley"
        assert len(signals) > 0

    def test_classify_location_hub_dc_metro(self, agent):
        """Test DC Metro location hub."""
        hub, signals = agent.classify_location_hub("Reston", "VA")
        assert hub == "DC Metro"

    def test_classify_location_hub_san_diego(self, agent):
        """Test San Diego location hub."""
        hub, signals = agent.classify_location_hub("San Diego", "CA")
        assert hub == "San Diego Metro"

    def test_calculate_bd_priority_critical(self, agent):
        """Test Critical BD priority calculation."""
        priority = agent.calculate_bd_priority(tier=1, program="AF DCGS - Langley")
        assert priority == "Critical"

    def test_calculate_bd_priority_high(self, agent):
        """Test High BD priority calculation."""
        priority = agent.calculate_bd_priority(tier=3, program="AF DCGS - Langley")
        assert priority == "High"

    def test_calculate_bd_priority_standard(self, agent):
        """Test Standard BD priority calculation."""
        priority = agent.calculate_bd_priority(tier=6, program="Unassigned")
        assert priority == "Standard"

    def test_classify_contact_full(self, agent):
        """Test full contact classification."""
        result = agent.classify_contact(
            first_name="John",
            last_name="Smith",
            job_title="Senior Director, DCGS Programs",
            company="GDIT",
            city="Langley",
            state="VA",
        )
        assert result.hierarchy_tier == 2
        assert result.program == "AF DCGS - Langley"
        assert result.bd_priority in ["Critical", "High"]
        assert result.confidence > 0.3

    @pytest.mark.asyncio
    async def test_classify_batch(self, agent):
        """Test batch contact classification."""
        classified = await agent.classify_batch(SAMPLE_CONTACTS[:2])
        assert len(classified) == 2
        assert "hierarchy_tier" in classified[0]
        assert "bd_priority" in classified[0]


class TestScraperMonitorAgent:
    """Test ScraperMonitorAgent."""

    @pytest.fixture
    def agent(self):
        from Engine8_Knowledge.agents import ScraperMonitorAgent
        return ScraperMonitorAgent()

    def test_detect_competitors(self, agent):
        """Test competitor detection."""
        job = {
            "title": "Systems Engineer",
            "company": "GDIT",
            "description": "Work with Leidos team on ISR systems"
        }
        competitors = agent.detect_competitors(job)
        assert "leidos" in competitors

    def test_is_high_value_true(self, agent):
        """Test high-value job detection."""
        job = {
            "title": "DCGS Network Engineer",
            "detected_clearance": "TS/SCI",
            "bd_score": 85,
            "description": "Support ISR fusion operations"
        }
        is_high, signals = agent.is_high_value(job)
        assert is_high is True
        assert len(signals) >= 2

    def test_is_high_value_false(self, agent):
        """Test non-high-value job detection."""
        job = {
            "title": "Administrative Assistant",
            "detected_clearance": "Public Trust",
            "bd_score": 30,
            "description": "Office support"
        }
        is_high, signals = agent.is_high_value(job)
        assert is_high is False

    def test_analyze_scrape_batch(self, agent):
        """Test scrape batch analysis."""
        analysis = agent.analyze_scrape_batch(
            jobs=SAMPLE_JOBS,
            scraper_name="test_scraper",
            previous_job_ids={"j1"}
        )
        assert analysis.total_jobs == 3
        assert analysis.new_jobs == 2
        assert analysis.high_value_jobs >= 1
        assert analysis.ts_sci_jobs >= 2

    @pytest.mark.asyncio
    async def test_process(self, agent):
        """Test agent process method."""
        result = await agent.process(
            "Analyze scrape",
            context={"jobs": SAMPLE_JOBS, "scraper_name": "test"}
        )
        assert result.success is True
        assert "analysis" in result.metadata


class TestQualityAssuranceAgent:
    """Test QualityAssuranceAgent."""

    @pytest.fixture
    def agent(self):
        from Engine8_Knowledge.agents import QualityAssuranceAgent
        return QualityAssuranceAgent()

    def test_check_completeness(self, agent):
        """Test completeness check."""
        records = [
            {"id": "1", "first_name": "John", "last_name": "", "company": "GDIT"},
        ]
        issues = agent.check_completeness(records, "contacts")
        assert len(issues) > 0
        assert any(i.issue_type == "missing_field" for i in issues)

    def test_check_duplicates(self, agent):
        """Test duplicate detection."""
        issues = agent.check_duplicates(SAMPLE_CONTACTS, "contacts")
        assert len(issues) > 0
        assert any(i.issue_type == "duplicate" for i in issues)

    def test_check_confidence(self, agent):
        """Test low confidence detection."""
        records = [
            {"id": "1", "confidence_score": 0.2},
            {"id": "2", "confidence_score": 0.9},
        ]
        issues = agent.check_confidence(records, "contacts")
        assert len(issues) == 1
        assert issues[0].issue_type == "low_confidence"

    def test_assess_quality(self, agent):
        """Test full quality assessment."""
        report = agent.assess_quality(SAMPLE_CONTACTS, "contacts")
        assert report.total_records == 4
        assert len(report.issues) > 0
        assert 0 <= report.completeness_score <= 1
        assert 0 <= report.overall_score <= 1

    @pytest.mark.asyncio
    async def test_process(self, agent):
        """Test agent process method."""
        result = await agent.process(
            "Check quality",
            context={"records": SAMPLE_CONTACTS, "collection_type": "contacts"}
        )
        assert result.success is True
        assert "report" in result.metadata


class TestAnalyticsAgent:
    """Test AnalyticsAgent."""

    @pytest.fixture
    def agent(self):
        from Engine8_Knowledge.agents import AnalyticsAgent
        return AnalyticsAgent()

    def test_analyze_hiring_trends(self, agent):
        """Test hiring trend analysis."""
        insights = agent.analyze_hiring_trends(SAMPLE_JOBS)
        assert len(insights) > 0
        assert any(i.category == "hiring" for i in insights)

    def test_analyze_program_activity(self, agent):
        """Test program activity analysis."""
        insights = agent.analyze_program_activity(SAMPLE_PROGRAMS, SAMPLE_JOBS)
        assert len(insights) > 0
        assert any(i.category == "programs" for i in insights)

    def test_analyze_contacts_by_tier(self, agent):
        """Test contact tier analysis."""
        contacts_with_tiers = [
            {"hierarchy_tier": "Tier 1 - Executive", "bd_priority": "Critical"},
            {"hierarchy_tier": "Tier 3 - Program Leadership", "bd_priority": "High"},
        ]
        insights = agent.analyze_contacts_by_tier(contacts_with_tiers)
        assert len(insights) > 0

    def test_generate_report(self, agent):
        """Test report generation."""
        report = agent.generate_report(
            jobs=SAMPLE_JOBS,
            programs=SAMPLE_PROGRAMS,
            contacts=SAMPLE_CONTACTS,
            period="weekly"
        )
        assert report.period == "weekly"
        assert report.key_metrics["total_jobs"] == 3
        assert len(report.insights) > 0

    @pytest.mark.asyncio
    async def test_process(self, agent):
        """Test agent process method."""
        result = await agent.process(
            "Generate report",
            context={
                "jobs": SAMPLE_JOBS,
                "programs": SAMPLE_PROGRAMS,
                "period": "weekly"
            }
        )
        assert result.success is True
        assert "report" in result.metadata


# ============================================
# Orchestrator Tests
# ============================================

class TestBDCrewOrchestrator:
    """Test BDCrewOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        from Engine8_Knowledge.agents import get_orchestrator
        return get_orchestrator()

    @pytest.mark.asyncio
    async def test_classify_contacts_workflow(self, orchestrator):
        """Test contact classification workflow."""
        result = await orchestrator.classify_contacts_workflow(SAMPLE_CONTACTS[:2])
        assert result.success is True
        assert result.workflow == "classify_contacts"
        assert "contact_classifier" in result.agents_used

    @pytest.mark.asyncio
    async def test_analyze_scrape_workflow(self, orchestrator):
        """Test scrape analysis workflow."""
        result = await orchestrator.analyze_scrape_workflow(
            jobs=SAMPLE_JOBS,
            scraper_name="test_scraper"
        )
        assert result.success is True
        assert result.workflow == "analyze_scrape"
        assert "scraper_monitor" in result.agents_used

    @pytest.mark.asyncio
    async def test_quality_check_workflow(self, orchestrator):
        """Test quality check workflow."""
        result = await orchestrator.quality_check_workflow(
            records=SAMPLE_CONTACTS,
            collection_type="contacts"
        )
        assert result.success is True
        assert result.workflow == "quality_check"
        assert "quality_assurance" in result.agents_used

    @pytest.mark.asyncio
    async def test_generate_analytics_workflow(self, orchestrator):
        """Test analytics workflow."""
        result = await orchestrator.generate_analytics_workflow(
            jobs=SAMPLE_JOBS,
            contacts=SAMPLE_CONTACTS,
            period="weekly"
        )
        assert result.success is True
        assert result.workflow == "analytics"
        assert "analytics" in result.agents_used

    @pytest.mark.asyncio
    async def test_quick_intel_workflow(self, orchestrator):
        """Test quick intel workflow."""
        result = await orchestrator.quick_intel_workflow(
            "Tell me about DCGS programs"
        )
        assert result.success is True
        assert result.workflow == "quick_intel"


# ============================================
# Data Model Tests
# ============================================

class TestUnifiedModels:
    """Test Pydantic v2 unified data models."""

    def test_contact_model(self):
        """Test Contact model."""
        from models.contacts import Contact, HierarchyTier, BDPriority

        contact = Contact(
            first_name="John",
            last_name="Smith",
            company="GDIT",
            hierarchy_tier=HierarchyTier.TIER_2_DIRECTOR,
            bd_priority=BDPriority.CRITICAL,
        )
        assert contact.full_name == "John Smith"
        assert contact.hierarchy_tier == HierarchyTier.TIER_2_DIRECTOR

    def test_job_model(self):
        """Test Job model."""
        from models.jobs import Job, JobStatus, ClearanceLevel

        job = Job(
            title="Systems Engineer",
            company="GDIT",
            status=JobStatus.ACTIVE,
            clearance_level=ClearanceLevel.TS_SCI,
            bd_score=85,
        )
        assert job.status == JobStatus.ACTIVE
        assert job.clearance_level == ClearanceLevel.TS_SCI

    def test_program_model(self):
        """Test Program model."""
        from models.programs import Program

        program = Program(
            program_name="AF DCGS",
            acronym="DCGS",
            status="active",
        )
        assert program.program_name == "AF DCGS"

    def test_activity_model(self):
        """Test Activity model."""
        from models.activities import Activity, ActivityType

        activity = Activity(
            activity_type=ActivityType.MEETING,
            summary="BD strategy meeting",
            contact_ids=["c1", "c2"],
        )
        assert activity.activity_type == ActivityType.MEETING


# ============================================
# Settings Tests
# ============================================

class TestSettings:
    """Test centralized settings."""

    def test_settings_load(self):
        """Test settings load from environment."""
        from config.settings import get_settings

        settings = get_settings()
        assert settings is not None
        assert hasattr(settings, "qdrant_url")
        assert hasattr(settings, "log_level")

    def test_settings_cached(self):
        """Test settings are cached."""
        from config.settings import get_settings

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


# ============================================
# API Endpoint Tests
# ============================================

class TestAPIEndpoints:
    """Test unified API endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from Engine8_Knowledge.api import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_search_endpoint(self, client):
        """Test search endpoint."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "DCGS engineer",
                "collections": ["contacts"],
                "limit": 5
            }
        )
        # May return 200 or 503 if Qdrant not running
        assert response.status_code in [200, 503]

    def test_analytics_overview_endpoint(self, client):
        """Test analytics overview endpoint."""
        response = client.get("/api/v1/analytics/overview")
        assert response.status_code in [200, 503]

    def test_collections_stats_endpoint(self, client):
        """Test collections stats endpoint."""
        response = client.get("/api/v1/collections/stats")
        assert response.status_code in [200, 503]


# ============================================
# Run Tests
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
