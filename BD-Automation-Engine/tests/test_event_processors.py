"""Tests for Phase 31A - Event Processors (job intel, contract, contact, campaign, anomaly, health)."""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.streaming.event_bus import Event, EventBus
from src.streaming.processors import (
    AnomalyProcessor,
    CampaignEventProcessor,
    ContactChangeProcessor,
    ContractIntelProcessor,
    EventProcessorRegistry,
    JobIntelProcessor,
    SystemHealthProcessor,
)


def _make_mock_bus():
    """Create a mock EventBus with publish tracked."""
    bus = MagicMock(spec=EventBus)
    bus.publish = AsyncMock(return_value=b"1-0")
    bus.subscribe = AsyncMock()
    bus.STREAM_DEFINITIONS = EventBus.STREAM_DEFINITIONS
    bus._running = True
    return bus


# =========================================
# JOB INTEL PROCESSOR
# =========================================


@pytest.mark.asyncio
class TestJobIntelProcessor:
    """Tests for JobIntelProcessor."""

    async def test_process_scraped_job_publishes_enriched(self):
        """Processing a scraped job should publish to jobs:enriched."""
        bus = _make_mock_bus()
        proc = JobIntelProcessor(bus)

        event = Event(
            event_type="job.scraped",
            source="scraper",
            payload={"title": "Systems Analyst", "company": "GDIT", "location": "Langley, VA"},
        )
        await proc.handle(event)

        # Should publish to jobs:enriched
        publish_calls = bus.publish.call_args_list
        enriched_calls = [c for c in publish_calls if c[0][0] == "jobs:enriched"]
        assert len(enriched_calls) >= 1

    async def test_priority_program_publishes_signal(self):
        """Job matching priority program should publish intel:signals."""
        bus = _make_mock_bus()
        proc = JobIntelProcessor(bus)

        event = Event(
            event_type="job.enriched",
            source="processor",
            payload={
                "title": "DCGS Analyst",
                "company": "Leidos",
                "location": "Langley",
                "mapped_program": "AF DCGS - PACAF",
                "clearance": "TS/SCI",
            },
        )
        await proc.handle(event)

        signal_calls = [c for c in bus.publish.call_args_list if c[0][0] == "intel:signals"]
        assert len(signal_calls) >= 1

    async def test_duplicate_job_skipped(self):
        """Duplicate jobs should be skipped and not published."""
        bus = _make_mock_bus()
        mock_search = AsyncMock()
        mock_search.find_by_hash = AsyncMock(return_value=True)
        proc = JobIntelProcessor(bus, hub_services={"search": mock_search})

        event = Event(
            event_type="job.scraped",
            source="scraper",
            payload={"title": "Test", "content_hash": "abc123"},
        )
        await proc.handle(event)

        # Should NOT publish enriched (was a duplicate)
        enriched_calls = [c for c in bus.publish.call_args_list if c[0][0] == "jobs:enriched"]
        assert len(enriched_calls) == 0

    async def test_processor_tracks_count(self):
        """Processor should track processed count."""
        bus = _make_mock_bus()
        proc = JobIntelProcessor(bus)

        event = Event(event_type="job.scraped", source="test", payload={"title": "Eng"})
        await proc._handle_wrapper(event)

        assert proc._processed_count == 1
        assert proc._error_count == 0


# =========================================
# CONTRACT INTEL PROCESSOR
# =========================================


@pytest.mark.asyncio
class TestContractIntelProcessor:
    """Tests for ContractIntelProcessor."""

    async def test_competitor_win_publishes_alert(self):
        """Competitor win should publish to intel:alerts."""
        bus = _make_mock_bus()
        proc = ContractIntelProcessor(bus)

        event = Event(
            event_type="contract.awarded",
            source="sam_gov",
            payload={
                "title": "DCGS Modernization",
                "agency": "USAF",
                "amount": 100000000,
                "awardee": "Leidos Inc",
            },
        )
        await proc.handle(event)

        alert_calls = [c for c in bus.publish.call_args_list if c[0][0] == "intel:alerts"]
        assert len(alert_calls) >= 1

    async def test_pts_capability_match_critical_signal(self):
        """Large contract matching PTS capabilities should publish critical signal."""
        bus = _make_mock_bus()
        proc = ContractIntelProcessor(bus)

        event = Event(
            event_type="contract.awarded",
            source="sam_gov",
            payload={
                "title": "ISR Data Fusion Platform",
                "agency": "USAF",
                "amount": 50000000,
                "awardee": "Acme Corp",
                "description": "Intelligence surveillance reconnaissance data fusion analytics platform",
            },
        )
        await proc.handle(event)

        signal_calls = [c for c in bus.publish.call_args_list if c[0][0] == "intel:signals"]
        assert len(signal_calls) >= 1
        signal_event = signal_calls[0][0][1]
        assert signal_event.priority == "critical"

    async def test_fuzzy_match_program(self):
        """_fuzzy_match_program should match known keywords."""
        proc = ContractIntelProcessor(_make_mock_bus())
        assert proc._fuzzy_match_program("DCGS Modernization", "USAF") == "AF DCGS"
        assert proc._fuzzy_match_program("F-35 Sustainment", "DoD") == "F-35 JSF"
        assert proc._fuzzy_match_program("Random Contract", "Unknown") is None

    async def test_small_contract_no_critical_signal(self):
        """Contracts under $10M should not produce critical signal even with capability match."""
        bus = _make_mock_bus()
        proc = ContractIntelProcessor(bus)

        event = Event(
            event_type="contract.awarded",
            source="sam_gov",
            payload={
                "title": "ISR Analytics Tool",
                "amount": 500000,
                "description": "Intelligence analytics tool",
                "awardee": "SmallCo",
                "agency": "USAF",
            },
        )
        await proc.handle(event)

        signal_calls = [c for c in bus.publish.call_args_list if c[0][0] == "intel:signals"]
        assert len(signal_calls) == 0


# =========================================
# CONTACT CHANGE PROCESSOR
# =========================================


@pytest.mark.asyncio
class TestContactChangeProcessor:
    """Tests for ContactChangeProcessor."""

    async def test_tier_classification(self):
        """Should classify contacts by title keywords."""
        proc = ContactChangeProcessor(_make_mock_bus())
        assert proc._classify_tier("Vice President of Engineering") == 1
        assert proc._classify_tier("Senior Manager") == 2
        assert proc._classify_tier("Senior Software Engineer") == 3
        assert proc._classify_tier("Software Engineer") == 4
        assert proc._classify_tier("Associate Coordinator") == 5
        assert proc._classify_tier("Intern") == 6
        assert proc._classify_tier("Unknown Title") == 4  # default

    async def test_high_tier_discovery_publishes_alert(self):
        """Discovering a Tier 1-2 contact should publish critical alert."""
        bus = _make_mock_bus()
        proc = ContactChangeProcessor(bus)

        event = Event(
            event_type="contact.discovered",
            source="zoominfo",
            payload={
                "name": "Jane Smith",
                "title": "Vice President",
                "company": "Leidos",
                "location": "Langley, VA",
            },
        )
        await proc.handle(event)

        alert_calls = [c for c in bus.publish.call_args_list if c[0][0] == "intel:alerts"]
        assert len(alert_calls) >= 1

    async def test_company_change_publishes_signal(self):
        """Contact changing companies should publish intel:signals."""
        bus = _make_mock_bus()
        proc = ContactChangeProcessor(bus)

        event = Event(
            event_type="contact.updated",
            source="crm",
            payload={
                "name": "John Doe",
                "title": "Engineer",
                "company": "Northrop Grumman",
                "previous_company": "Raytheon",
            },
        )
        await proc.handle(event)

        signal_calls = [c for c in bus.publish.call_args_list if c[0][0] == "intel:signals"]
        assert len(signal_calls) >= 1

    async def test_location_program_assignment(self):
        """Should assign program based on location."""
        proc = ContactChangeProcessor(_make_mock_bus())
        assert proc._assign_program_by_location("Langley, VA") == "AF DCGS - Langley"
        assert proc._assign_program_by_location("Hickam AFB") == "AF DCGS - PACAF"
        assert proc._assign_program_by_location("Unknown City") is None

    async def test_priority_scoring(self):
        """Should score BD priority based on tier and program."""
        proc = ContactChangeProcessor(_make_mock_bus())
        assert proc._score_priority(1, "AF DCGS - PACAF", {"clearance": "TS/SCI"}) == "Critical"
        assert proc._score_priority(4, None, {}) == "Standard"


# =========================================
# CAMPAIGN EVENT PROCESSOR
# =========================================


@pytest.mark.asyncio
class TestCampaignEventProcessor:
    """Tests for CampaignEventProcessor."""

    async def test_positive_response_publishes_signal(self):
        """Positive campaign response should publish intel:signals."""
        bus = _make_mock_bus()
        proc = CampaignEventProcessor(bus)

        event = Event(
            event_type="campaign.response",
            source="outreach",
            payload={"campaign_id": "c-1", "contact_id": "ct-1", "outcome": "interested", "channel": "email"},
        )
        await proc.handle(event)

        signal_calls = [c for c in bus.publish.call_args_list if c[0][0] == "intel:signals"]
        assert len(signal_calls) >= 1

    async def test_meeting_booked_publishes_prep(self):
        """Meeting booked should publish meeting prep event."""
        bus = _make_mock_bus()
        proc = CampaignEventProcessor(bus)

        event = Event(
            event_type="campaign.response",
            source="outreach",
            payload={"campaign_id": "c-1", "contact_id": "ct-1", "outcome": "meeting_booked", "channel": "linkedin"},
        )
        await proc.handle(event)

        campaign_calls = [c for c in bus.publish.call_args_list if c[0][0] == "campaigns:events"]
        assert len(campaign_calls) >= 1

    async def test_rejection_publishes_cadence_adjust(self):
        """Rejection should publish cadence adjustment event."""
        bus = _make_mock_bus()
        proc = CampaignEventProcessor(bus)

        event = Event(
            event_type="campaign.response",
            source="outreach",
            payload={"campaign_id": "c-1", "contact_id": "ct-1", "outcome": "rejected", "channel": "email"},
        )
        await proc.handle(event)

        campaign_calls = [c for c in bus.publish.call_args_list if c[0][0] == "campaigns:events"]
        assert len(campaign_calls) >= 1


# =========================================
# ANOMALY PROCESSOR
# =========================================


@pytest.mark.asyncio
class TestAnomalyProcessor:
    """Tests for AnomalyProcessor."""

    async def test_high_severity_publishes_alert(self):
        """High-severity anomaly should publish to intel:alerts."""
        bus = _make_mock_bus()
        proc = AnomalyProcessor(bus)

        event = Event(
            event_type="anomaly.detected",
            source="detector",
            payload={"anomaly_type": "PATTERN_SHIFT", "severity": "high", "description": "Pattern shift detected"},
        )
        await proc.handle(event)

        alert_calls = [c for c in bus.publish.call_args_list if c[0][0] == "intel:alerts"]
        assert len(alert_calls) >= 1

    async def test_volume_spike_adjusts_frequency(self):
        """Volume spike should publish scrape frequency adjustment."""
        bus = _make_mock_bus()
        proc = AnomalyProcessor(bus)

        event = Event(
            event_type="anomaly.detected",
            source="detector",
            payload={"anomaly_type": "VOLUME_SPIKE", "severity": "medium", "multiplier": 3.0},
        )
        await proc.handle(event)

        health_calls = [c for c in bus.publish.call_args_list if c[0][0] == "system:health"]
        assert len(health_calls) >= 1

    async def test_pacaf_priority_keyword_critical_alert(self):
        """PACAF-related anomaly should publish critical alert."""
        bus = _make_mock_bus()
        proc = AnomalyProcessor(bus)

        event = Event(
            event_type="anomaly.detected",
            source="detector",
            payload={"anomaly_type": "VOLUME_SPIKE", "severity": "low", "program": "PACAF Operations", "description": "Surge at PACAF"},
        )
        await proc.handle(event)

        alert_calls = [c for c in bus.publish.call_args_list if c[0][0] == "intel:alerts"]
        # Should have at least one for priority keyword
        priority_calls = [
            c for c in alert_calls
            if c[0][1].event_type == "anomaly.priority_program"
        ]
        assert len(priority_calls) >= 1


# =========================================
# SYSTEM HEALTH PROCESSOR
# =========================================


@pytest.mark.asyncio
class TestSystemHealthProcessor:
    """Tests for SystemHealthProcessor."""

    async def test_tracks_service_status(self):
        """Should track service status."""
        bus = _make_mock_bus()
        proc = SystemHealthProcessor(bus)

        event = Event(
            event_type="health.check",
            source="monitor",
            payload={"service": "qdrant", "status": "healthy"},
        )
        await proc.handle(event)

        statuses = proc.get_service_statuses()
        assert statuses["qdrant"] == "healthy"

    async def test_consecutive_failures_alert(self):
        """3 consecutive failures should trigger critical alert."""
        bus = _make_mock_bus()
        proc = SystemHealthProcessor(bus)

        for i in range(3):
            event = Event(
                event_type="health.check",
                source="monitor",
                payload={"service": "scraper_v2", "status": "error", "error": f"Timeout #{i+1}"},
            )
            await proc.handle(event)

        alert_calls = [c for c in bus.publish.call_args_list if c[0][0] == "intel:alerts"]
        assert len(alert_calls) >= 1

    async def test_success_resets_failure_count(self):
        """Success should reset failure count."""
        bus = _make_mock_bus()
        proc = SystemHealthProcessor(bus)

        # Two failures
        for i in range(2):
            event = Event(
                event_type="health.check", source="monitor",
                payload={"service": "api", "status": "error"},
            )
            await proc.handle(event)

        # Success
        event = Event(
            event_type="health.check", source="monitor",
            payload={"service": "api", "status": "healthy"},
        )
        await proc.handle(event)

        assert proc._failure_counts.get("api", 0) == 0


# =========================================
# PROCESSOR REGISTRY
# =========================================


class TestEventProcessorRegistry:
    """Tests for EventProcessorRegistry."""

    def test_registers_6_default_processors(self):
        """Registry should register 6 default processors."""
        bus = _make_mock_bus()
        registry = EventProcessorRegistry(bus)
        assert len(registry.processors) == 6

    def test_get_processor_by_name(self):
        """Should retrieve processor by name."""
        bus = _make_mock_bus()
        registry = EventProcessorRegistry(bus)
        job_proc = registry.get_processor("job_intel")
        assert job_proc is not None
        assert isinstance(job_proc, JobIntelProcessor)

    def test_get_all_status(self):
        """get_all_status should return list of status dicts."""
        bus = _make_mock_bus()
        registry = EventProcessorRegistry(bus)
        statuses = registry.get_all_status()
        assert len(statuses) == 6
        for s in statuses:
            assert "name" in s
            assert "running" in s
            assert "processed" in s
