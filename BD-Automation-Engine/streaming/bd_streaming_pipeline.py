"""
BD Streaming Pipeline using Pathway.

Real-time streaming capabilities for BD intelligence:
- Live opportunity monitoring from SAM.gov
- Contract alerts from FPDS
- Streaming RAG for knowledge base
- Recompete signal detection
- Competitor activity tracking
"""

import pathway as pw
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm.embedders import OpenAIEmbedder
from datetime import datetime
from typing import List, Optional, Dict
import json
import requests
import logging

from .pathway_config import PathwayConfig, load_config_from_env

logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMA DEFINITIONS
# =============================================================================

class SAMOpportunitySchema(pw.Schema):
    """Schema for SAM.gov opportunity data."""
    notice_id: str
    title: str
    agency: str
    posted_date: str
    response_deadline: str
    set_aside: str
    naics_code: str
    description: str
    estimated_value: float
    place_of_performance: str


class FPDSContractSchema(pw.Schema):
    """Schema for FPDS contract data."""
    contract_id: str
    vendor_name: str
    agency: str
    award_date: str
    award_amount: float
    pop_start_date: str
    pop_end_date: str
    naics_code: str
    description: str
    contract_type: str


class BullhornActivitySchema(pw.Schema):
    """Schema for Bullhorn CRM activity data."""
    activity_id: str
    contact_id: str
    activity_type: str
    timestamp: str
    notes: str
    outcome: str


class AlertSchema(pw.Schema):
    """Schema for unified alerts."""
    alert_id: str
    alert_type: str
    title: str
    description: str
    priority: str
    source_id: str
    timestamp: str
    metadata: str


# =============================================================================
# BD STREAMING PIPELINE
# =============================================================================

class BDStreamingPipeline:
    """
    Real-time streaming pipeline for BD intelligence.

    Provides:
    - SAM.gov opportunity monitoring
    - FPDS contract tracking
    - Bullhorn CRM activity streaming
    - Recompete detection
    - Competitor analysis
    - Unified alerting
    """

    def __init__(self, config: Optional[PathwayConfig] = None):
        """Initialize the pipeline with configuration."""
        self.config = config or load_config_from_env()
        self._pipeline_running = False
        self._vector_store = None

    # =========================================================================
    # DATA INGESTION
    # =========================================================================

    def create_sam_opportunity_stream(
        self,
        source_path: str = "data/streaming/sam_opportunities/",
    ) -> pw.Table:
        """
        Create a streaming data source for SAM.gov opportunities.

        Uses CSV files with streaming mode for demo. In production,
        would connect to Kafka topic with SAM.gov API data.

        Args:
            source_path: Path to CSV files for streaming input

        Returns:
            Pathway Table with opportunity data
        """
        return pw.io.csv.read(
            source_path,
            schema=SAMOpportunitySchema,
            mode="streaming",
            autocommit_duration_ms=self.config.checkpoint_interval_ms,
        )

    def create_fpds_contract_stream(
        self,
        source_path: str = "data/streaming/fpds_contracts/",
    ) -> pw.Table:
        """
        Create a streaming data source for FPDS contract awards.

        Args:
            source_path: Path to CSV files for streaming input

        Returns:
            Pathway Table with contract data
        """
        return pw.io.csv.read(
            source_path,
            schema=FPDSContractSchema,
            mode="streaming",
            autocommit_duration_ms=self.config.checkpoint_interval_ms,
        )

    def create_bullhorn_activity_stream(
        self,
        source_path: str = "data/streaming/bullhorn_activities/",
    ) -> pw.Table:
        """
        Create a streaming data source for Bullhorn CRM activities.

        Args:
            source_path: Path to CSV files for streaming input

        Returns:
            Pathway Table with activity data
        """
        return pw.io.csv.read(
            source_path,
            schema=BullhornActivitySchema,
            mode="streaming",
            autocommit_duration_ms=self.config.checkpoint_interval_ms,
        )

    # =========================================================================
    # REAL-TIME ANALYTICS
    # =========================================================================

    def detect_relevant_opportunities(
        self,
        opportunities: pw.Table,
        target_naics: List[str],
        target_agencies: List[str],
        keywords: List[str],
    ) -> pw.Table:
        """
        Filter opportunities that match target criteria.

        Uses multi-signal matching:
        1. NAICS code match
        2. Agency match
        3. Keyword match in title/description

        Args:
            opportunities: Streaming opportunity table
            target_naics: List of target NAICS codes
            target_agencies: List of target agencies
            keywords: List of keywords to match

        Returns:
            Filtered table of relevant opportunities
        """
        naics_set = set(target_naics)
        agency_set = set(a.lower() for a in target_agencies)
        keyword_set = set(k.lower() for k in keywords)

        @pw.udf
        def is_relevant(naics: str, agency: str, title: str, description: str) -> bool:
            # NAICS match (check prefix for broader matching)
            naics_match = any(naics.startswith(n[:4]) for n in naics_set) if naics else False

            # Agency match
            agency_match = agency.lower() in agency_set if agency else False

            # Keyword match
            text = f"{title} {description}".lower()
            keyword_match = any(kw in text for kw in keyword_set)

            # Relevant if at least 2 signals match
            signals = sum([naics_match, agency_match, keyword_match])
            return signals >= 2

        @pw.udf
        def calculate_relevance_score(naics: str, agency: str, title: str, description: str, estimated_value: float) -> float:
            score = 0.0

            # NAICS match bonus
            if naics and any(naics.startswith(n[:4]) for n in naics_set):
                score += 30.0

            # Agency match bonus
            if agency and agency.lower() in agency_set:
                score += 25.0

            # Keyword match bonus
            text = f"{title} {description}".lower()
            keyword_matches = sum(1 for kw in keyword_set if kw in text)
            score += min(keyword_matches * 10.0, 30.0)

            # Value bonus (higher value = higher priority)
            if estimated_value:
                if estimated_value >= 100_000_000:
                    score += 15.0
                elif estimated_value >= 50_000_000:
                    score += 10.0
                elif estimated_value >= 10_000_000:
                    score += 5.0

            return score

        # Filter and score
        return opportunities.filter(
            is_relevant(
                pw.this.naics_code,
                pw.this.agency,
                pw.this.title,
                pw.this.description,
            )
        ).select(
            *opportunities.columns(),
            relevance_score=calculate_relevance_score(
                pw.this.naics_code,
                pw.this.agency,
                pw.this.title,
                pw.this.description,
                pw.this.estimated_value,
            ),
        )

    def detect_recompete_signals(
        self,
        contracts: pw.Table,
        days_threshold: int = 365,
    ) -> pw.Table:
        """
        Detect contracts approaching end of period of performance.

        These represent recompete opportunities.

        Args:
            contracts: Streaming contract table
            days_threshold: Days before POP end to flag as recompete

        Returns:
            Table of contracts flagged for recompete
        """
        @pw.udf
        def calculate_days_to_pop_end(pop_end_date: str) -> int:
            try:
                end_date = datetime.strptime(pop_end_date, "%Y-%m-%d")
                days_remaining = (end_date - datetime.now()).days
                return max(0, days_remaining)
            except (ValueError, TypeError):
                return -1

        @pw.udf
        def is_recompete_candidate(pop_end_date: str, award_amount: float) -> bool:
            try:
                end_date = datetime.strptime(pop_end_date, "%Y-%m-%d")
                days_remaining = (end_date - datetime.now()).days
                # Flag if within threshold and significant value
                return 0 < days_remaining <= days_threshold and award_amount >= 1_000_000
            except (ValueError, TypeError):
                return False

        @pw.udf
        def calculate_recompete_urgency(pop_end_date: str) -> str:
            try:
                end_date = datetime.strptime(pop_end_date, "%Y-%m-%d")
                days_remaining = (end_date - datetime.now()).days
                if days_remaining <= 90:
                    return "CRITICAL"
                elif days_remaining <= 180:
                    return "HIGH"
                elif days_remaining <= 270:
                    return "MEDIUM"
                else:
                    return "LOW"
            except (ValueError, TypeError):
                return "UNKNOWN"

        return contracts.filter(
            is_recompete_candidate(pw.this.pop_end_date, pw.this.award_amount)
        ).select(
            *contracts.columns(),
            days_to_pop_end=calculate_days_to_pop_end(pw.this.pop_end_date),
            recompete_urgency=calculate_recompete_urgency(pw.this.pop_end_date),
        )

    def track_competitor_activity(
        self,
        contracts: pw.Table,
        competitors: List[str],
    ) -> pw.Table:
        """
        Track contract awards to competitor companies.

        Args:
            contracts: Streaming contract table
            competitors: List of competitor company names

        Returns:
            Table of competitor contract wins
        """
        competitor_set = set(c.lower() for c in competitors)

        @pw.udf
        def is_competitor_win(vendor_name: str) -> bool:
            if not vendor_name:
                return False
            vendor_lower = vendor_name.lower()
            return any(comp in vendor_lower for comp in competitor_set)

        @pw.udf
        def get_matched_competitor(vendor_name: str) -> str:
            if not vendor_name:
                return ""
            vendor_lower = vendor_name.lower()
            for comp in competitor_set:
                if comp in vendor_lower:
                    return comp.title()
            return ""

        return contracts.filter(
            is_competitor_win(pw.this.vendor_name)
        ).select(
            *contracts.columns(),
            matched_competitor=get_matched_competitor(pw.this.vendor_name),
        )

    def calculate_pipeline_metrics(
        self,
        opportunities: pw.Table,
        activities: pw.Table,
    ) -> pw.Table:
        """
        Calculate real-time pipeline metrics.

        Args:
            opportunities: Relevant opportunities table
            activities: CRM activities table

        Returns:
            Table with aggregated metrics
        """
        # Opportunity metrics
        opp_metrics = opportunities.reduce(
            total_opportunities=pw.reducers.count(),
            total_value=pw.reducers.sum(pw.this.estimated_value),
            avg_value=pw.reducers.avg(pw.this.estimated_value),
        )

        # Activity metrics
        activity_metrics = activities.reduce(
            total_activities=pw.reducers.count(),
        )

        return opp_metrics.join(activity_metrics).select(
            total_opportunities=pw.left.total_opportunities,
            total_value=pw.left.total_value,
            avg_value=pw.left.avg_value,
            total_activities=pw.right.total_activities,
            timestamp=pw.apply(lambda: datetime.now().isoformat()),
        )

    # =========================================================================
    # RAG INTEGRATION
    # =========================================================================

    def create_streaming_rag(
        self,
        documents: pw.Table,
        embedding_model: Optional[str] = None,
    ) -> VectorStoreServer:
        """
        Create a streaming RAG vector store.

        Incrementally indexes documents as they arrive.

        Args:
            documents: Streaming document table with 'text' column
            embedding_model: Override embedding model

        Returns:
            VectorStoreServer for similarity search
        """
        model = embedding_model or self.config.embedding_model

        embedder = OpenAIEmbedder(
            api_key=self.config.openai_api_key,
            model=model,
        )

        self._vector_store = VectorStoreServer(
            documents,
            embedder=embedder,
        )

        return self._vector_store

    # =========================================================================
    # ALERTING
    # =========================================================================

    def create_alert_stream(
        self,
        relevant_opps: pw.Table,
        recompete_signals: pw.Table,
        competitor_wins: pw.Table,
    ) -> pw.Table:
        """
        Create unified alert stream from multiple sources.

        Combines:
        - Relevant opportunity alerts
        - Recompete signal alerts
        - Competitor win alerts

        Args:
            relevant_opps: Filtered relevant opportunities
            recompete_signals: Detected recompete candidates
            competitor_wins: Competitor contract wins

        Returns:
            Unified alert stream
        """
        @pw.udf
        def create_opp_alert(
            notice_id: str,
            title: str,
            agency: str,
            estimated_value: float,
            relevance_score: float,
        ) -> Dict[str, str]:
            priority = "HIGH" if relevance_score >= 70 else "MEDIUM" if relevance_score >= 50 else "LOW"
            return {
                "alert_id": f"OPP-{notice_id}",
                "alert_type": "NEW_OPPORTUNITY",
                "title": f"New Opportunity: {title[:100]}",
                "description": f"Agency: {agency}, Est. Value: ${estimated_value:,.0f}",
                "priority": priority,
                "source_id": notice_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": json.dumps({"relevance_score": relevance_score}),
            }

        @pw.udf
        def create_recompete_alert(
            contract_id: str,
            vendor_name: str,
            agency: str,
            award_amount: float,
            days_to_pop_end: int,
            recompete_urgency: str,
        ) -> Dict[str, str]:
            return {
                "alert_id": f"REC-{contract_id}",
                "alert_type": "RECOMPETE_SIGNAL",
                "title": f"Recompete: {vendor_name[:50]} contract ending",
                "description": f"Agency: {agency}, Value: ${award_amount:,.0f}, Days remaining: {days_to_pop_end}",
                "priority": recompete_urgency,
                "source_id": contract_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": json.dumps({"days_remaining": days_to_pop_end}),
            }

        @pw.udf
        def create_competitor_alert(
            contract_id: str,
            vendor_name: str,
            agency: str,
            award_amount: float,
            matched_competitor: str,
        ) -> Dict[str, str]:
            priority = "HIGH" if award_amount >= 50_000_000 else "MEDIUM" if award_amount >= 10_000_000 else "LOW"
            return {
                "alert_id": f"COMP-{contract_id}",
                "alert_type": "COMPETITOR_WIN",
                "title": f"Competitor Win: {matched_competitor}",
                "description": f"Agency: {agency}, Award: ${award_amount:,.0f}",
                "priority": priority,
                "source_id": contract_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": json.dumps({"competitor": matched_competitor}),
            }

        # Transform each source to alert format
        opp_alerts = relevant_opps.select(
            alert_data=create_opp_alert(
                pw.this.notice_id,
                pw.this.title,
                pw.this.agency,
                pw.this.estimated_value,
                pw.this.relevance_score,
            )
        ).select(
            alert_id=pw.this.alert_data["alert_id"],
            alert_type=pw.this.alert_data["alert_type"],
            title=pw.this.alert_data["title"],
            description=pw.this.alert_data["description"],
            priority=pw.this.alert_data["priority"],
            source_id=pw.this.alert_data["source_id"],
            timestamp=pw.this.alert_data["timestamp"],
            metadata=pw.this.alert_data["metadata"],
        )

        recompete_alerts = recompete_signals.select(
            alert_data=create_recompete_alert(
                pw.this.contract_id,
                pw.this.vendor_name,
                pw.this.agency,
                pw.this.award_amount,
                pw.this.days_to_pop_end,
                pw.this.recompete_urgency,
            )
        ).select(
            alert_id=pw.this.alert_data["alert_id"],
            alert_type=pw.this.alert_data["alert_type"],
            title=pw.this.alert_data["title"],
            description=pw.this.alert_data["description"],
            priority=pw.this.alert_data["priority"],
            source_id=pw.this.alert_data["source_id"],
            timestamp=pw.this.alert_data["timestamp"],
            metadata=pw.this.alert_data["metadata"],
        )

        competitor_alerts = competitor_wins.select(
            alert_data=create_competitor_alert(
                pw.this.contract_id,
                pw.this.vendor_name,
                pw.this.agency,
                pw.this.award_amount,
                pw.this.matched_competitor,
            )
        ).select(
            alert_id=pw.this.alert_data["alert_id"],
            alert_type=pw.this.alert_data["alert_type"],
            title=pw.this.alert_data["title"],
            description=pw.this.alert_data["description"],
            priority=pw.this.alert_data["priority"],
            source_id=pw.this.alert_data["source_id"],
            timestamp=pw.this.alert_data["timestamp"],
            metadata=pw.this.alert_data["metadata"],
        )

        # Combine all alert streams
        return pw.Table.concat(opp_alerts, recompete_alerts, competitor_alerts)

    # =========================================================================
    # OUTPUT SINKS
    # =========================================================================

    def output_to_postgres(
        self,
        table: pw.Table,
        table_name: str,
    ) -> None:
        """
        Output streaming table to PostgreSQL.

        Args:
            table: Pathway table to output
            table_name: Target PostgreSQL table name
        """
        pg_settings = self.config.get_postgres_settings()

        pw.io.postgres.write(
            table,
            postgres_settings={
                "host": pg_settings["host"],
                "port": pg_settings["port"],
                "dbname": pg_settings["database"],
                "user": pg_settings["user"],
                "password": pg_settings["password"],
            },
            table_name=table_name,
        )

    def output_to_kafka(
        self,
        table: pw.Table,
        topic: str,
    ) -> None:
        """
        Output streaming table to Kafka topic.

        Args:
            table: Pathway table to output
            topic: Kafka topic name
        """
        kafka_settings = self.config.get_kafka_settings()

        pw.io.kafka.write(
            table,
            rdkafka_settings=kafka_settings,
            topic_name=topic,
        )

    def output_alerts_to_webhook(
        self,
        alerts: pw.Table,
        webhook_url: Optional[str] = None,
    ) -> None:
        """
        Send alerts to a webhook endpoint.

        Args:
            alerts: Alert table to output
            webhook_url: Override webhook URL
        """
        url = webhook_url or self.config.webhook_url

        if not url:
            logger.warning("No webhook URL configured, skipping webhook output")
            return

        @pw.io.python_connector.output_connectors.OutputConnector
        class WebhookOutput:
            def __init__(self, webhook_url: str):
                self.webhook_url = webhook_url

            def on_change(self, key, row, time, is_addition):
                if is_addition:
                    try:
                        requests.post(
                            self.webhook_url,
                            json=row,
                            headers={"Content-Type": "application/json"},
                            timeout=10,
                        )
                    except Exception as e:
                        logger.error(f"Failed to send webhook: {e}")

        pw.io.python_connector.write(alerts, WebhookOutput(url))

    # =========================================================================
    # ORCHESTRATION
    # =========================================================================

    def run_bd_intelligence_pipeline(
        self,
        sam_source: str = "data/streaming/sam_opportunities/",
        fpds_source: str = "data/streaming/fpds_contracts/",
        bullhorn_source: str = "data/streaming/bullhorn_activities/",
        output_postgres: bool = True,
        output_kafka: bool = False,
        output_webhook: bool = True,
    ) -> None:
        """
        Run the complete BD intelligence pipeline.

        Hardcoded targets for DCGS portfolio:
        - NAICS: 541512 (Computer Systems Design), 541519 (Other CS Services)
        - Agencies: Air Force, Army, DoD
        - Keywords: DCGS, ISR, intelligence, surveillance, reconnaissance
        - Competitors: Leidos, Northrop Grumman, Raytheon, L3Harris, SAIC

        Args:
            sam_source: Path to SAM opportunity data
            fpds_source: Path to FPDS contract data
            bullhorn_source: Path to Bullhorn activity data
            output_postgres: Enable PostgreSQL output
            output_kafka: Enable Kafka output
            output_webhook: Enable webhook alerting
        """
        logger.info("Starting BD Intelligence Pipeline...")

        # DCGS portfolio targets
        target_naics = ["541512", "541519", "541511", "541330", "541715"]
        target_agencies = [
            "Department of the Air Force",
            "Department of the Army",
            "Department of Defense",
            "National Geospatial-Intelligence Agency",
            "Defense Intelligence Agency",
        ]
        keywords = [
            "dcgs", "distributed common ground system",
            "isr", "intelligence surveillance reconnaissance",
            "sigint", "geoint", "elint",
            "sensor data", "mission systems",
            "ground station", "exploitation",
        ]
        competitors = [
            "leidos", "northrop grumman", "raytheon",
            "l3harris", "saic", "general dynamics",
            "bae systems", "lockheed martin", "boeing",
        ]

        # Create data streams
        opportunities = self.create_sam_opportunity_stream(sam_source)
        contracts = self.create_fpds_contract_stream(fpds_source)
        self.create_bullhorn_activity_stream(bullhorn_source)

        # Apply analytics
        relevant_opps = self.detect_relevant_opportunities(
            opportunities, target_naics, target_agencies, keywords
        )
        recompete_signals = self.detect_recompete_signals(contracts)
        competitor_wins = self.track_competitor_activity(contracts, competitors)

        # Create unified alert stream
        alerts = self.create_alert_stream(relevant_opps, recompete_signals, competitor_wins)

        # Configure outputs
        if output_postgres:
            self.output_to_postgres(relevant_opps, "bd_relevant_opportunities")
            self.output_to_postgres(recompete_signals, "bd_recompete_signals")
            self.output_to_postgres(competitor_wins, "bd_competitor_wins")
            self.output_to_postgres(alerts, "bd_alerts")

        if output_kafka:
            self.output_to_kafka(alerts, "bd-alerts")

        if output_webhook:
            self.output_alerts_to_webhook(alerts)

        # Run the pipeline
        self._pipeline_running = True
        logger.info("Pipeline configured. Starting Pathway runtime...")
        pw.run()

    def stop_pipeline(self) -> None:
        """Stop the running pipeline."""
        self._pipeline_running = False
        logger.info("Pipeline stop requested")


def run_pipeline(config: Optional[PathwayConfig] = None) -> None:
    """Convenience function to run the BD intelligence pipeline."""
    pipeline = BDStreamingPipeline(config)
    pipeline.run_bd_intelligence_pipeline()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_pipeline()
