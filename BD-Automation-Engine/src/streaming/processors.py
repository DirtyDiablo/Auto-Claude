"""
Real-time event processors that react to intelligence signals.

Six processors handle different intelligence domains:
1. JobIntelProcessor    — React to new/enriched jobs
2. ContractIntelProcessor — React to contract awards and opportunities
3. ContactChangeProcessor — React to contact updates
4. CampaignEventProcessor — React to campaign events for closed-loop optimization
5. AnomalyProcessor     — React to anomaly detections
6. SystemHealthProcessor — Monitor system health events
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.streaming.event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class BaseProcessor:
    """Base class for all event processors."""

    name: str = "base"
    listen_streams: List[str] = []

    def __init__(self, event_bus: EventBus, hub_services: Optional[Dict[str, Any]] = None):
        self.event_bus = event_bus
        self.services = hub_services or {}
        self._running = False
        self._processed_count = 0
        self._error_count = 0
        self._started_at: Optional[datetime] = None

    async def start(self) -> None:
        """Start processing events from configured streams."""
        self._running = True
        self._started_at = datetime.now(timezone.utc)
        logger.info(f"{self.name} processor started", extra={"streams": self.listen_streams})
        await self.event_bus.subscribe(
            streams=self.listen_streams,
            handler=self._handle_wrapper,
            consumer=f"{self.name}-processor",
        )

    async def stop(self) -> None:
        """Stop processing events."""
        self._running = False
        logger.info(
            f"{self.name} processor stopped",
            extra={"processed": self._processed_count, "errors": self._error_count},
        )

    async def _handle_wrapper(self, event: Event) -> None:
        """Wrap handler with error tracking."""
        try:
            await self.handle(event)
            self._processed_count += 1
        except Exception as e:
            self._error_count += 1
            logger.error(
                f"{self.name} processing error",
                extra={"event_type": event.event_type, "error": str(e)},
            )
            raise

    async def handle(self, event: Event) -> None:
        """Process a single event. Override in subclasses."""
        raise NotImplementedError

    def get_status(self) -> dict:
        """Return processor status."""
        return {
            "name": self.name,
            "running": self._running,
            "streams": self.listen_streams,
            "processed": self._processed_count,
            "errors": self._error_count,
            "started_at": self._started_at.isoformat() if self._started_at else None,
        }


class JobIntelProcessor(BaseProcessor):
    """
    React to new/enriched jobs in real-time.

    Listens: jobs:scraped, jobs:enriched
    Actions:
      1. Dedup against existing jobs (content hash + cosine similarity)
      2. Run program mapping (location + keyword + clearance scoring)
      3. Match to contacts in Neo4j (same program + location)
      4. Update contact BD priority if their program has new openings
      5. Publish intel:signals if job matches priority program
      6. Update BERTopic clusters with new job data
      7. Publish to jobs:enriched stream (if from jobs:scraped)
    """

    name = "job_intel"
    listen_streams = ["jobs:scraped", "jobs:enriched"]

    async def handle(self, event: Event) -> None:
        payload = event.payload
        job_title = payload.get("title", "unknown")
        company = payload.get("company", "unknown")
        location = payload.get("location", "")
        clearance = payload.get("clearance", "")

        logger.info(
            "Processing job event",
            extra={"title": job_title, "company": company, "event_type": event.event_type},
        )

        # Step 1: Dedup check
        content_hash = payload.get("content_hash")
        if content_hash and "search" in self.services:
            try:
                existing = await self._check_duplicate(content_hash)
                if existing:
                    logger.info("Duplicate job detected, skipping", extra={"hash": content_hash})
                    return
            except Exception as e:
                logger.warning("Dedup check failed", extra={"error": str(e)})

        # Step 2: Program mapping
        mapped_program = payload.get("mapped_program")
        if not mapped_program and "mapper" in self.services:
            try:
                mapped_program = await self._map_program(payload)
            except Exception as e:
                logger.warning("Program mapping failed", extra={"error": str(e)})

        # Step 3-4: Contact matching and priority update
        matched_contacts = []
        if mapped_program and "graph" in self.services:
            try:
                matched_contacts = await self._match_contacts(mapped_program, location)
            except Exception as e:
                logger.warning("Contact matching failed", extra={"error": str(e)})

        # Step 5: Signal detection — priority program match
        priority_programs = {"AF DCGS", "PACAF", "Langley", "GBSD", "F-35"}
        if mapped_program and any(p in mapped_program for p in priority_programs):
            signal_event = Event(
                event_type="job.priority_match",
                source=self.name,
                payload={
                    "job_title": job_title,
                    "company": company,
                    "program": mapped_program,
                    "location": location,
                    "clearance": clearance,
                    "matched_contacts": len(matched_contacts),
                },
                metadata={
                    "correlation_id": event.metadata.get("correlation_id", event.event_id),
                    "causation_id": event.event_id,
                },
                priority="high",
            )
            await self.event_bus.publish("intel:signals", signal_event)

        # Step 7: If from scraped stream, publish enriched
        if event.event_type == "job.scraped" or "scraped" in event.source:
            enriched = Event(
                event_type="job.enriched",
                source=self.name,
                payload={
                    **payload,
                    "mapped_program": mapped_program,
                    "matched_contacts_count": len(matched_contacts),
                    "enriched_at": datetime.now(timezone.utc).isoformat(),
                },
                metadata={
                    "correlation_id": event.metadata.get("correlation_id", event.event_id),
                    "causation_id": event.event_id,
                },
            )
            await self.event_bus.publish("jobs:enriched", enriched)

    async def _check_duplicate(self, content_hash: str) -> bool:
        search = self.services.get("search")
        if search and hasattr(search, "find_by_hash"):
            return await search.find_by_hash(content_hash)
        return False

    async def _map_program(self, payload: dict) -> Optional[str]:
        mapper = self.services.get("mapper")
        if mapper and hasattr(mapper, "map_job"):
            result = await mapper.map_job(payload)
            return result.get("program") if result else None
        return None

    async def _match_contacts(self, program: str, location: str) -> List[dict]:
        graph = self.services.get("graph")
        if graph and hasattr(graph, "find_contacts_by_program"):
            return await graph.find_contacts_by_program(program, location)
        return []


class ContractIntelProcessor(BaseProcessor):
    """
    React to contract awards and opportunities.

    Listens: contracts:awards, contracts:opps
    Actions:
      1. Match award to Federal Programs database
      2. Create/update Contract node in Neo4j
      3. Link to Company and Program nodes
      4. If competitor won → flag as competitive intelligence
      5. If opportunity matches PTS capabilities → Critical alert
      6. Update memory with contract context
      7. Re-score all contacts at affected programs
    """

    name = "contract_intel"
    listen_streams = ["contracts:awards", "contracts:opps"]

    PTS_CAPABILITIES = {
        "ISR", "SIGINT", "GEOINT", "C4ISR", "intelligence", "reconnaissance",
        "surveillance", "data fusion", "analytics", "cyber", "mission systems",
    }

    async def handle(self, event: Event) -> None:
        payload = event.payload
        contract_title = payload.get("title", "unknown")
        agency = payload.get("agency", "")
        award_amount = payload.get("amount", 0)
        awardee = payload.get("awardee", "")

        logger.info(
            "Processing contract event",
            extra={"title": contract_title, "agency": agency, "type": event.event_type},
        )

        # Step 1: Program matching
        matched_program = payload.get("matched_program")
        if not matched_program:
            matched_program = self._fuzzy_match_program(contract_title, agency)

        # Step 2-3: Neo4j graph update
        if "graph" in self.services:
            try:
                await self._update_graph(payload, matched_program)
            except Exception as e:
                logger.warning("Graph update failed", extra={"error": str(e)})

        # Step 4: Competitive intelligence
        competitors = {"Leidos", "Raytheon", "Northrop Grumman", "L3Harris", "BAE Systems", "Booz Allen"}
        if awardee and any(comp.lower() in awardee.lower() for comp in competitors):
            alert_event = Event(
                event_type="contract.competitor_win",
                source=self.name,
                payload={
                    "title": contract_title,
                    "awardee": awardee,
                    "amount": award_amount,
                    "agency": agency,
                    "program": matched_program,
                },
                metadata={
                    "correlation_id": event.metadata.get("correlation_id", event.event_id),
                    "causation_id": event.event_id,
                },
                priority="high",
            )
            await self.event_bus.publish("intel:alerts", alert_event)

        # Step 5: PTS capability match → critical alert
        description = payload.get("description", "").lower()
        title_lower = contract_title.lower()
        if any(cap.lower() in description or cap.lower() in title_lower for cap in self.PTS_CAPABILITIES):
            if award_amount and award_amount > 10_000_000:
                signal = Event(
                    event_type="contract.pts_opportunity",
                    source=self.name,
                    payload={
                        "title": contract_title,
                        "agency": agency,
                        "amount": award_amount,
                        "capabilities_matched": [
                            c for c in self.PTS_CAPABILITIES
                            if c.lower() in description or c.lower() in title_lower
                        ],
                        "program": matched_program,
                    },
                    metadata={
                        "correlation_id": event.metadata.get("correlation_id", event.event_id),
                        "causation_id": event.event_id,
                    },
                    priority="critical",
                )
                await self.event_bus.publish("intel:signals", signal)

        # Step 6: Memory update
        if "memory" in self.services:
            try:
                memory = self.services["memory"]
                if hasattr(memory, "add"):
                    await memory.add(
                        f"Contract: {contract_title} awarded to {awardee} for ${award_amount:,.0f} by {agency}",
                        metadata={"type": "contract", "program": matched_program},
                    )
            except Exception as e:
                logger.warning("Memory update failed", extra={"error": str(e)})

    def _fuzzy_match_program(self, title: str, agency: str) -> Optional[str]:
        """Simple keyword-based program matching."""
        program_keywords = {
            "DCGS": "AF DCGS",
            "GBSD": "GBSD",
            "F-35": "F-35 JSF",
            "PACAF": "AF DCGS - PACAF",
            "Sentinel": "GBSD Sentinel",
        }
        combined = f"{title} {agency}".upper()
        for keyword, program in program_keywords.items():
            if keyword.upper() in combined:
                return program
        return None

    async def _update_graph(self, payload: dict, program: Optional[str]) -> None:
        graph = self.services.get("graph")
        if graph and hasattr(graph, "create_contract_node"):
            await graph.create_contract_node(payload, program)


class ContactChangeProcessor(BaseProcessor):
    """
    React to contact updates.

    Listens: contacts:discovered, contacts:updated
    Actions:
      1. Classify tier using hierarchy logic
      2. Assign program by location
      3. Score BD priority
      4. Create/update Neo4j node + relationships
      5. Index in Qdrant
      6. If Tier 1-2 discovered → immediate alert
      7. If contact changed companies → update graph, flag for outreach
      8. Update memory with new contact context
    """

    name = "contact_change"
    listen_streams = ["contacts:discovered", "contacts:updated"]

    TIER_KEYWORDS = {
        1: {"vp", "president", "director", "chief", "cxo", "general manager"},
        2: {"manager", "lead", "head", "principal", "senior director"},
        3: {"senior", "staff", "architect", "fellow"},
        4: {"engineer", "analyst", "developer", "specialist"},
        5: {"associate", "coordinator", "assistant"},
        6: {"intern", "trainee", "entry"},
    }

    async def handle(self, event: Event) -> None:
        payload = event.payload
        contact_name = payload.get("name", "unknown")
        title = payload.get("title", "")
        company = payload.get("company", "")
        location = payload.get("location", "")

        logger.info(
            "Processing contact event",
            extra={"name": contact_name, "company": company, "type": event.event_type},
        )

        # Step 1: Tier classification
        tier = self._classify_tier(title)

        # Step 2: Program assignment by location
        program = payload.get("program") or self._assign_program_by_location(location)

        # Step 3: BD priority scoring
        bd_priority = self._score_priority(tier, program, payload)

        # Step 4: Neo4j update
        if "graph" in self.services:
            try:
                graph = self.services["graph"]
                if hasattr(graph, "upsert_contact"):
                    await graph.upsert_contact({
                        **payload,
                        "tier": tier,
                        "program": program,
                        "bd_priority": bd_priority,
                    })
            except Exception as e:
                logger.warning("Graph update failed", extra={"error": str(e)})

        # Step 5: Qdrant index
        if "search" in self.services:
            try:
                search = self.services["search"]
                if hasattr(search, "index_contact"):
                    await search.index_contact({
                        **payload,
                        "tier": tier,
                        "program": program,
                        "bd_priority": bd_priority,
                    })
            except Exception as e:
                logger.warning("Qdrant indexing failed", extra={"error": str(e)})

        # Step 6: High-tier discovery alert
        if tier <= 2 and event.event_type in ("contact.discovered", "contact_discovered"):
            alert = Event(
                event_type="contact.high_tier_discovered",
                source=self.name,
                payload={
                    "name": contact_name,
                    "title": title,
                    "company": company,
                    "tier": tier,
                    "program": program,
                    "bd_priority": bd_priority,
                },
                metadata={
                    "correlation_id": event.metadata.get("correlation_id", event.event_id),
                    "causation_id": event.event_id,
                },
                priority="critical",
            )
            await self.event_bus.publish("intel:alerts", alert)

        # Step 7: Company change detection
        previous_company = payload.get("previous_company")
        if previous_company and previous_company != company:
            change_event = Event(
                event_type="contact.company_changed",
                source=self.name,
                payload={
                    "name": contact_name,
                    "previous_company": previous_company,
                    "new_company": company,
                    "title": title,
                    "tier": tier,
                },
                metadata={
                    "correlation_id": event.metadata.get("correlation_id", event.event_id),
                    "causation_id": event.event_id,
                },
                priority="high",
            )
            await self.event_bus.publish("intel:signals", change_event)

        # Step 8: Memory update
        if "memory" in self.services:
            try:
                memory = self.services["memory"]
                if hasattr(memory, "add"):
                    await memory.add(
                        f"Contact: {contact_name} ({title}) at {company}, Tier {tier}, Program: {program}",
                        metadata={"type": "contact", "tier": tier},
                    )
            except Exception as e:
                logger.warning("Memory update failed", extra={"error": str(e)})

    def _classify_tier(self, title: str) -> int:
        """Classify contact tier based on job title keywords."""
        title_lower = title.lower()
        for tier, keywords in self.TIER_KEYWORDS.items():
            if any(kw in title_lower for kw in keywords):
                return tier
        return 4  # Default to tier 4

    def _assign_program_by_location(self, location: str) -> Optional[str]:
        """Assign probable program based on location."""
        location_programs = {
            "langley": "AF DCGS - Langley",
            "hickam": "AF DCGS - PACAF",
            "pearl harbor": "AF DCGS - PACAF",
            "beale": "AF DCGS - Beale",
            "ramstein": "AF DCGS - USAFE",
            "offutt": "AF DCGS - USSTRATCOM",
            "san diego": "Navy ISR",
            "fort meade": "NSA Programs",
            "colorado springs": "Space Programs",
        }
        loc_lower = location.lower()
        for keyword, program in location_programs.items():
            if keyword in loc_lower:
                return program
        return None

    def _score_priority(self, tier: int, program: Optional[str], payload: dict) -> str:
        """Score BD priority based on tier, program, and signals."""
        score = 0
        if tier <= 2:
            score += 40
        elif tier <= 3:
            score += 25
        elif tier <= 4:
            score += 10

        priority_programs = {"AF DCGS", "PACAF", "GBSD", "F-35"}
        if program and any(p in program for p in priority_programs):
            score += 30

        clearance = payload.get("clearance", "")
        if "TS/SCI" in clearance.upper():
            score += 20
        elif "SECRET" in clearance.upper():
            score += 10

        if score >= 70:
            return "Critical"
        elif score >= 50:
            return "High"
        elif score >= 30:
            return "Medium"
        return "Standard"


class CampaignEventProcessor(BaseProcessor):
    """
    React to campaign events for closed-loop optimization.

    Listens: campaigns:events, campaigns:responses
    Actions:
      1. Update LinUCB bandit with response outcomes
      2. Update outreach memory per contact
      3. If positive response → escalate contact priority
      4. If meeting booked → generate meeting prep automatically
      5. If rejection → adjust cadence, try different channel
      6. Update campaign analytics in real-time
      7. Publish intel:signals for significant campaign wins
    """

    name = "campaign_event"
    listen_streams = ["campaigns:events", "campaigns:responses"]

    POSITIVE_OUTCOMES = {"replied", "meeting_booked", "interested", "accepted", "engaged"}
    NEGATIVE_OUTCOMES = {"rejected", "unsubscribed", "bounced", "no_response"}

    async def handle(self, event: Event) -> None:
        payload = event.payload
        campaign_id = payload.get("campaign_id", "unknown")
        contact_id = payload.get("contact_id")
        outcome = payload.get("outcome", "")
        channel = payload.get("channel", "email")

        logger.info(
            "Processing campaign event",
            extra={"campaign": campaign_id, "outcome": outcome, "type": event.event_type},
        )

        # Step 1: Bandit update
        if "ml_models" in self.services and outcome:
            try:
                models = self.services["ml_models"]
                if hasattr(models, "update_bandit"):
                    reward = 1.0 if outcome in self.POSITIVE_OUTCOMES else 0.0
                    await models.update_bandit(channel, reward)
            except Exception as e:
                logger.warning("Bandit update failed", extra={"error": str(e)})

        # Step 2: Outreach memory
        if "memory" in self.services and contact_id:
            try:
                memory = self.services["memory"]
                if hasattr(memory, "add"):
                    await memory.add(
                        f"Campaign {campaign_id}: {outcome} via {channel} for contact {contact_id}",
                        metadata={"type": "campaign_outcome", "contact_id": contact_id},
                    )
            except Exception as e:
                logger.warning("Memory update failed", extra={"error": str(e)})

        # Step 3: Positive response → escalate
        if outcome in self.POSITIVE_OUTCOMES:
            signal = Event(
                event_type="campaign.positive_response",
                source=self.name,
                payload={
                    "campaign_id": campaign_id,
                    "contact_id": contact_id,
                    "outcome": outcome,
                    "channel": channel,
                },
                metadata={
                    "correlation_id": event.metadata.get("correlation_id", event.event_id),
                    "causation_id": event.event_id,
                },
                priority="high",
            )
            await self.event_bus.publish("intel:signals", signal)

        # Step 4: Meeting booked → prep
        if outcome == "meeting_booked":
            meeting_event = Event(
                event_type="campaign.meeting_prep_needed",
                source=self.name,
                payload={
                    "contact_id": contact_id,
                    "campaign_id": campaign_id,
                    "meeting_date": payload.get("meeting_date"),
                },
                metadata={
                    "correlation_id": event.metadata.get("correlation_id", event.event_id),
                    "causation_id": event.event_id,
                },
                priority="high",
            )
            await self.event_bus.publish("campaigns:events", meeting_event)

        # Step 5: Rejection → adjust
        if outcome in self.NEGATIVE_OUTCOMES:
            adjust_event = Event(
                event_type="campaign.cadence_adjust",
                source=self.name,
                payload={
                    "contact_id": contact_id,
                    "campaign_id": campaign_id,
                    "failed_channel": channel,
                    "outcome": outcome,
                    "recommendation": "try_alternate_channel",
                },
                metadata={
                    "correlation_id": event.metadata.get("correlation_id", event.event_id),
                    "causation_id": event.event_id,
                },
                priority="medium",
            )
            await self.event_bus.publish("campaigns:events", adjust_event)


class AnomalyProcessor(BaseProcessor):
    """
    React to anomaly detections.

    Listens: intel:anomalies
    Actions:
      1. Evaluate against alert rules
      2. Fire alerts for matching rules
      3. Auto-adjust scrape frequency for surging sources
      4. Update memory with anomaly context
      5. If PACAF-related → immediate notification
    """

    name = "anomaly"
    listen_streams = ["intel:anomalies"]

    PRIORITY_KEYWORDS = {"PACAF", "DCGS", "Langley", "GBSD", "F-35", "Sentinel"}

    async def handle(self, event: Event) -> None:
        payload = event.payload
        anomaly_type = payload.get("anomaly_type", "unknown")
        severity = payload.get("severity", "medium")
        source_program = payload.get("program", "")
        description = payload.get("description", "")

        logger.info(
            "Processing anomaly",
            extra={"type": anomaly_type, "severity": severity},
        )

        # Step 1-2: Alert rule evaluation
        should_alert = severity in ("high", "critical")
        if anomaly_type == "VOLUME_SPIKE" and payload.get("multiplier", 1) >= 2.0:
            should_alert = True

        if should_alert:
            alert = Event(
                event_type=f"anomaly.alert.{anomaly_type.lower()}",
                source=self.name,
                payload={
                    "anomaly_type": anomaly_type,
                    "severity": severity,
                    "program": source_program,
                    "description": description,
                    "details": payload,
                },
                metadata={
                    "correlation_id": event.metadata.get("correlation_id", event.event_id),
                    "causation_id": event.event_id,
                },
                priority="high" if severity != "critical" else "critical",
            )
            await self.event_bus.publish("intel:alerts", alert)

        # Step 3: Auto-adjust scrape frequency
        if anomaly_type == "VOLUME_SPIKE":
            adjust_event = Event(
                event_type="system.scrape_frequency_adjust",
                source=self.name,
                payload={
                    "source": payload.get("scrape_source", ""),
                    "multiplier": payload.get("multiplier", 1),
                    "recommendation": "increase_frequency",
                },
                metadata={
                    "correlation_id": event.metadata.get("correlation_id", event.event_id),
                    "causation_id": event.event_id,
                },
            )
            await self.event_bus.publish("system:health", adjust_event)

        # Step 4: Memory update
        if "memory" in self.services:
            try:
                memory = self.services["memory"]
                if hasattr(memory, "add"):
                    await memory.add(
                        f"Anomaly detected: {anomaly_type} - {description} (severity: {severity})",
                        metadata={"type": "anomaly", "program": source_program},
                    )
            except Exception as e:
                logger.warning("Memory update failed", extra={"error": str(e)})

        # Step 5: PACAF priority check
        combined = f"{source_program} {description}".upper()
        if any(kw in combined for kw in self.PRIORITY_KEYWORDS):
            priority_alert = Event(
                event_type="anomaly.priority_program",
                source=self.name,
                payload={
                    "anomaly_type": anomaly_type,
                    "program": source_program,
                    "description": description,
                    "matched_keywords": [
                        kw for kw in self.PRIORITY_KEYWORDS if kw in combined
                    ],
                },
                metadata={
                    "correlation_id": event.metadata.get("correlation_id", event.event_id),
                    "causation_id": event.event_id,
                },
                priority="critical",
            )
            await self.event_bus.publish("intel:alerts", priority_alert)


class SystemHealthProcessor(BaseProcessor):
    """
    Monitor system health events.

    Listens: system:health
    Actions:
      1. Track service uptime/downtime
      2. Alert on consecutive failures
      3. Auto-pause failing scrape sources
      4. Log to Prometheus metrics
    """

    name = "system_health"
    listen_streams = ["system:health"]

    def __init__(self, event_bus: EventBus, hub_services: Optional[Dict[str, Any]] = None):
        super().__init__(event_bus, hub_services)
        self._failure_counts: Dict[str, int] = {}
        self._service_status: Dict[str, str] = {}
        self.consecutive_failure_threshold = 3

    async def handle(self, event: Event) -> None:
        payload = event.payload
        service_name = payload.get("service", "unknown")
        status = payload.get("status", "unknown")
        error_msg = payload.get("error", "")

        logger.info(
            "Processing health event",
            extra={"service": service_name, "status": status},
        )

        # Step 1: Track status
        self._service_status[service_name] = status

        # Step 2: Consecutive failure tracking
        if status in ("error", "failed", "down"):
            self._failure_counts[service_name] = self._failure_counts.get(service_name, 0) + 1

            if self._failure_counts[service_name] >= self.consecutive_failure_threshold:
                alert = Event(
                    event_type="system.consecutive_failures",
                    source=self.name,
                    payload={
                        "service": service_name,
                        "failure_count": self._failure_counts[service_name],
                        "last_error": error_msg,
                    },
                    metadata={
                        "correlation_id": event.metadata.get("correlation_id", event.event_id),
                        "causation_id": event.event_id,
                    },
                    priority="critical",
                )
                await self.event_bus.publish("intel:alerts", alert)
        else:
            # Reset on success
            self._failure_counts[service_name] = 0

        # Step 3: Auto-pause failing scrapers
        if (
            "scrape" in service_name.lower()
            and self._failure_counts.get(service_name, 0) >= self.consecutive_failure_threshold
        ):
            pause_event = Event(
                event_type="system.scraper_paused",
                source=self.name,
                payload={
                    "scraper": service_name,
                    "reason": f"Consecutive failures: {self._failure_counts[service_name]}",
                    "action": "auto_paused",
                },
                metadata={
                    "correlation_id": event.metadata.get("correlation_id", event.event_id),
                    "causation_id": event.event_id,
                },
                priority="high",
            )
            await self.event_bus.publish("intel:alerts", pause_event)

    def get_service_statuses(self) -> Dict[str, str]:
        """Get current status of all tracked services."""
        return dict(self._service_status)


class EventProcessorRegistry:
    """Manages all real-time event processors."""

    def __init__(self, event_bus: EventBus, hub_services: Optional[Dict[str, Any]] = None):
        self.event_bus = event_bus
        self.hub_services = hub_services or {}
        self.processors: Dict[str, BaseProcessor] = {}
        self._tasks: List[asyncio.Task] = []
        self._register_default_processors()

    def _register_default_processors(self) -> None:
        """Register the 6 built-in processors."""
        self.register(JobIntelProcessor(self.event_bus, self.hub_services))
        self.register(ContractIntelProcessor(self.event_bus, self.hub_services))
        self.register(ContactChangeProcessor(self.event_bus, self.hub_services))
        self.register(CampaignEventProcessor(self.event_bus, self.hub_services))
        self.register(AnomalyProcessor(self.event_bus, self.hub_services))
        self.register(SystemHealthProcessor(self.event_bus, self.hub_services))

    def register(self, processor: BaseProcessor) -> None:
        """Register a processor."""
        self.processors[processor.name] = processor

    async def start_all(self) -> None:
        """Start all registered processors as concurrent tasks."""
        for name, processor in self.processors.items():
            task = asyncio.create_task(processor.start())
            self._tasks.append(task)
            logger.info(f"Started processor: {name}")

    async def stop_all(self) -> None:
        """Graceful shutdown with in-flight event completion."""
        for name, processor in self.processors.items():
            await processor.stop()
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("All processors stopped")

    def get_all_status(self) -> List[dict]:
        """Get status of all processors."""
        return [p.get_status() for p in self.processors.values()]

    def get_processor(self, name: str) -> Optional[BaseProcessor]:
        """Get a processor by name."""
        return self.processors.get(name)

    async def restart_processor(self, name: str) -> bool:
        """Restart a specific processor."""
        processor = self.processors.get(name)
        if not processor:
            return False
        await processor.stop()
        task = asyncio.create_task(processor.start())
        self._tasks.append(task)
        return True
