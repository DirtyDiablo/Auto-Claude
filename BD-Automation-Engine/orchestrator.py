#!/usr/bin/env python3
"""
BD Automation Engine - Master Orchestrator
Unified pipeline integrating all 6 engines for end-to-end BD automation.

Engines:
1. Engine1_Scraper - Job data collection (Apify integration)
2. Engine2_ProgramMapping - Core pipeline (standardize, match, score, export)
3. Engine3_OrgChart - Contact lookup and classification
4. Engine4_Playbook - BD playbook generation
5. Engine5_Scoring - BD priority scoring
6. Engine6_QA - Quality assurance and feedback loop
7. Engine7_BullhornETL - Bullhorn CRM ETL and dashboard data export

Usage:
    python orchestrator.py --input data/jobs.json --full-pipeline
    python orchestrator.py --input data/jobs.json --hot-leads-only --email
    python orchestrator.py --schedule --interval 6h
"""

import asyncio
import json
import os
import sys
import argparse
import logging
import smtplib
import time as time_module
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure log directory exists
LOG_DIR = PROJECT_ROOT / "outputs" / "Logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "orchestrator.log", mode="a"),
    ],
)
logger = logging.getLogger("BD-Orchestrator")


# ============================================
# CONFIGURATION
# ============================================


@dataclass
class OrchestratorConfig:
    """Configuration for the BD Automation Orchestrator."""

    # Input/Output
    input_path: Optional[str] = None
    output_dir: str = str(PROJECT_ROOT / "outputs")

    # Pipeline Stages
    run_scraper: bool = False
    run_mapping: bool = True
    run_contacts: bool = True
    run_briefings: bool = True
    run_scoring: bool = True
    run_qa: bool = True
    run_bullhorn: bool = True
    export_dashboard: bool = True
    run_knowledge: bool = True  # Engine 8: Knowledge indexing
    run_sam_sync: bool = False  # SAM.gov opportunity sync (requires SAM_API_KEY or TANGO_API_KEY)
    run_ner: bool = True  # NER entity enrichment (pattern-based, no external deps)

    # Filters
    hot_leads_only: bool = False
    min_bd_score: int = 0
    min_confidence: float = 0.0

    # Notifications
    send_email: bool = False
    send_webhook: bool = True

    # API Keys (from env)
    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    n8n_webhook_url: str = field(
        default_factory=lambda: os.getenv("N8N_WEBHOOK_URL", "")
    )
    smtp_host: str = field(
        default_factory=lambda: os.getenv("SMTP_HOST", "smtp.gmail.com")
    )
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    smtp_user: str = field(default_factory=lambda: os.getenv("SMTP_USER", ""))
    smtp_password: str = field(default_factory=lambda: os.getenv("SMTP_PASSWORD", ""))
    notification_email: str = field(
        default_factory=lambda: os.getenv("NOTIFICATION_EMAIL", "")
    )

    # Processing
    test_mode: bool = False
    batch_size: int = 50
    fail_on_stage_error: bool = False  # Quarantine failures by default; --strict enables fail-fast
    resume: bool = False  # Resume from last checkpoint

    # Scheduling
    schedule_enabled: bool = False
    schedule_interval_hours: int = 6


@dataclass
class PipelineResult:
    """Result of a complete pipeline run."""

    success: bool
    jobs_processed: int
    hot_leads: int
    warm_leads: int
    cold_leads: int
    briefings_generated: int
    qa_approved: int
    qa_needs_review: int
    export_files: Dict[str, str]
    errors: List[str]
    duration_seconds: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class StageResult:
    """Result of a single pipeline stage execution."""

    name: str
    status: str  # "passed", "failed", "skipped"
    duration_seconds: float = 0.0
    record_count: int = 0
    error: Optional[str] = None


class PipelineCheckpoint:
    """JSON-based checkpoint system for pipeline resume support."""

    def __init__(self, output_dir: str):
        self.checkpoint_path = Path(output_dir) / "pipeline_checkpoint.json"
        self.data: Dict = {}

    def load(self) -> Dict:
        """Load existing checkpoint from disk."""
        if self.checkpoint_path.exists():
            try:
                with open(self.checkpoint_path, "r") as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.data = {}
        return self.data

    def create(self, run_id: str) -> None:
        """Initialize a new checkpoint for a fresh run."""
        self.data = {
            "run_id": run_id,
            "stages_completed": [],
            "stages_failed": {},
            "started_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }
        self._save()

    def mark_completed(self, stage_name: str) -> None:
        """Record a stage as successfully completed."""
        if stage_name not in self.data.get("stages_completed", []):
            self.data.setdefault("stages_completed", []).append(stage_name)
        self.data["last_updated"] = datetime.now().isoformat()
        self._save()

    def mark_failed(self, stage_name: str, error_msg: str) -> None:
        """Record a stage as failed with its error message."""
        self.data.setdefault("stages_failed", {})[stage_name] = error_msg
        self.data["last_updated"] = datetime.now().isoformat()
        self._save()

    def is_completed(self, stage_name: str) -> bool:
        """Check whether a stage was already completed in a previous run."""
        return stage_name in self.data.get("stages_completed", [])

    def _save(self) -> None:
        """Write checkpoint data to disk."""
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.checkpoint_path, "w") as f:
            json.dump(self.data, f, indent=2, default=str)


# ============================================
# ENGINE IMPORTS
# ============================================


def import_engines():
    """Import all engine modules with graceful fallbacks."""
    engines = {}

    # Engine 2: Program Mapping Pipeline
    try:
        from Engine2_ProgramMapping.scripts.pipeline import (
            PipelineConfig,
            load_config,
            run_pipeline as run_mapping_pipeline,
        )
        from Engine2_ProgramMapping.scripts.job_standardizer import (
            preprocess_job_data,
            standardize_job_with_llm,
        )
        from Engine2_ProgramMapping.scripts.program_mapper import (
            map_job_to_program,
            process_jobs_batch,
        )
        from Engine2_ProgramMapping.scripts.exporters import (
            NotionCSVExporter,
            N8nWebhookExporter,
            export_batch,
        )

        engines["mapping"] = {
            "PipelineConfig": PipelineConfig,
            "load_config": load_config,
            "run_pipeline": run_mapping_pipeline,
            "preprocess_job_data": preprocess_job_data,
            "standardize_job_with_llm": standardize_job_with_llm,
            "map_job_to_program": map_job_to_program,
            "process_jobs_batch": process_jobs_batch,
            "NotionCSVExporter": NotionCSVExporter,
            "N8nWebhookExporter": N8nWebhookExporter,
            "export_batch": export_batch,
        }
        logger.info("Engine2_ProgramMapping loaded successfully")
    except ImportError as e:
        logger.warning(f"Engine2_ProgramMapping not available: {e}")

    # Engine 3: Contact Lookup
    try:
        from Engine3_OrgChart.scripts.contact_lookup import (
            lookup_contacts,
            format_contacts_for_briefing,
            ContactDatabase,
        )

        engines["contacts"] = {
            "lookup_contacts": lookup_contacts,
            "format_contacts_for_briefing": format_contacts_for_briefing,
            "ContactDatabase": ContactDatabase,
        }
        logger.info("Engine3_OrgChart loaded successfully")
    except ImportError as e:
        logger.warning(f"Engine3_OrgChart not available: {e}")

    # Engine 4: Playbook Generator (Full BD Playbooks with Email/Call/TalkingPoints)
    try:
        from Engine4_Playbook.scripts.bd_playbook_generator import (
            generate_playbook,
            generate_playbooks_batch,
            PlaybookData,
            PlaybookOutput,
        )

        engines["briefings"] = {
            "generate_briefing": generate_playbook,
            "generate_briefings_batch": generate_playbooks_batch,
            "BriefingData": PlaybookData,
            "PlaybookOutput": PlaybookOutput,
        }
        logger.info("Engine4_Playbook loaded successfully")
    except ImportError as e:
        logger.warning(f"Engine4_Playbook not available: {e}")

    # Engine 5: BD Scoring
    try:
        from Engine5_Scoring.scripts.bd_scoring import (
            calculate_bd_score,
            score_batch,
            generate_scoring_report,
        )

        engines["scoring"] = {
            "calculate_bd_score": calculate_bd_score,
            "score_batch": score_batch,
            "generate_scoring_report": generate_scoring_report,
        }
        logger.info("Engine5_Scoring loaded successfully")
    except ImportError as e:
        logger.warning(f"Engine5_Scoring not available: {e}")

    # Engine 6: QA Feedback
    try:
        from Engine6_QA.scripts.qa_feedback import (
            run_qa_workflow,
            evaluate_batch,
            ReviewQueue,
            QAConfig,
        )

        engines["qa"] = {
            "run_qa_workflow": run_qa_workflow,
            "evaluate_batch": evaluate_batch,
            "ReviewQueue": ReviewQueue,
            "QAConfig": QAConfig,
        }
        logger.info("Engine6_QA loaded successfully")
    except ImportError as e:
        logger.warning(f"Engine6_QA not available: {e}")

    # Engine 7: Bullhorn ETL & Dashboard Integration
    try:
        from Engine7_BullhornETL.run_pipeline import (
            run_full_pipeline as run_bullhorn_pipeline,
        )
        from Engine7_BullhornETL.scripts.dashboard_integration import (
            run_integration as run_dashboard_export,
        )

        engines["bullhorn"] = {
            "run_pipeline": run_bullhorn_pipeline,
            "run_dashboard_export": run_dashboard_export,
        }
        logger.info("Engine7_BullhornETL loaded successfully")
    except ImportError as e:
        logger.warning(f"Engine7_BullhornETL not available: {e}")

    # Engine 8: Knowledge Management (Vector DB + Semantic Search)
    try:
        from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
        from Engine8_Knowledge.scripts.indexer import BDIndexer

        engines["knowledge"] = {
            "BDKnowledgeStore": BDKnowledgeStore,
            "BDIndexer": BDIndexer,
        }
        logger.info("Engine8_Knowledge loaded successfully")
    except ImportError as e:
        logger.warning(f"Engine8_Knowledge not available: {e}")

    return engines


# ============================================
# EMAIL NOTIFICATION
# ============================================


class EmailNotifier:
    """Send email notifications for hot leads and alerts."""

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.enabled = bool(config.smtp_user and config.smtp_password)

    def send_hot_lead_alert(self, jobs: List[Dict], briefings: List[Dict]) -> bool:
        """Send email alert for hot leads."""
        if not self.enabled:
            logger.warning("Email notifications not configured")
            return False

        if not jobs:
            logger.info("No hot leads to notify")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = (
                f"[BD Alert] {len(jobs)} Hot Lead(s) Detected - {datetime.now().strftime('%Y-%m-%d')}"
            )
            msg["From"] = self.config.smtp_user
            msg["To"] = self.config.notification_email

            # Build HTML content
            html_content = self._build_hot_lead_html(jobs, briefings)
            text_content = self._build_hot_lead_text(jobs)

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Send email
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg)

            logger.info(f"Hot lead alert sent to {self.config.notification_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _build_hot_lead_html(self, jobs: List[Dict], briefings: List[Dict]) -> str:
        """Build HTML email content for hot leads."""
        job_rows = ""
        for job in jobs:
            mapping = job.get("_mapping", {})
            scoring = job.get("_scoring", {})
            job_rows += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">
                    <strong>{job.get("Job Title/Position", job.get("title", "Unknown"))}</strong><br>
                    <small>{job.get("Location", job.get("location", "N/A"))}</small>
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{mapping.get("program_name", "N/A")}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">
                    <span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px;">
                        {scoring.get("BD Priority Score", 0)}
                    </span>
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{job.get("Security Clearance", "N/A")}</td>
            </tr>
            """

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <h2 style="color: #dc3545;">Hot Lead Alert</h2>
            <p>The BD Automation Engine has identified <strong>{len(jobs)}</strong> high-priority opportunities requiring immediate attention.</p>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <thead>
                    <tr style="background: #f8f9fa;">
                        <th style="padding: 10px; text-align: left;">Position</th>
                        <th style="padding: 10px; text-align: left;">Program</th>
                        <th style="padding: 10px; text-align: center;">BD Score</th>
                        <th style="padding: 10px; text-align: left;">Clearance</th>
                    </tr>
                </thead>
                <tbody>
                    {job_rows}
                </tbody>
            </table>

            <h3>Recommended Actions:</h3>
            <ul>
                <li>Review attached briefings for detailed opportunity analysis</li>
                <li>Escalate to BD leadership for capture decision</li>
                <li>Initiate outreach to program contacts</li>
            </ul>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                Generated by BD Automation Engine | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </p>
        </body>
        </html>
        """

    def _build_hot_lead_text(self, jobs: List[Dict]) -> str:
        """Build plain text email content for hot leads."""
        lines = [
            f"HOT LEAD ALERT - {len(jobs)} Opportunities Detected",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "=" * 60,
        ]

        for job in jobs:
            mapping = job.get("_mapping", {})
            scoring = job.get("_scoring", {})
            lines.extend(
                [
                    f"\nPosition: {job.get('Job Title/Position', job.get('title', 'Unknown'))}",
                    f"Location: {job.get('Location', job.get('location', 'N/A'))}",
                    f"Program: {mapping.get('program_name', 'N/A')}",
                    f"BD Score: {scoring.get('BD Priority Score', 0)}",
                    f"Clearance: {job.get('Security Clearance', 'N/A')}",
                    "-" * 40,
                ]
            )

        return "\n".join(lines)

    def send_daily_summary(self, result: PipelineResult) -> bool:
        """Send daily summary email."""
        if not self.enabled:
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = (
                f"[BD Summary] Daily Pipeline Report - {datetime.now().strftime('%Y-%m-%d')}"
            )
            msg["From"] = self.config.smtp_user
            msg["To"] = self.config.notification_email

            text_content = f"""
BD Automation Daily Summary
===========================
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Pipeline Results:
- Jobs Processed: {result.jobs_processed}
- Hot Leads: {result.hot_leads}
- Warm Leads: {result.warm_leads}
- Cold Leads: {result.cold_leads}
- Briefings Generated: {result.briefings_generated}
- QA Approved: {result.qa_approved}
- QA Needs Review: {result.qa_needs_review}

Duration: {result.duration_seconds:.1f} seconds
Status: {"SUCCESS" if result.success else "FAILED"}

Errors: {len(result.errors)}
"""
            msg.attach(MIMEText(text_content, "plain"))

            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg)

            logger.info(f"Daily summary sent to {self.config.notification_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False


# ============================================
# WEBHOOK DELIVERY
# ============================================


class WebhookDelivery:
    """Deliver pipeline results to n8n webhooks."""

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.webhook_url = config.n8n_webhook_url
        self.enrichment_url = os.getenv("N8N_ENRICHMENT_WEBHOOK", "")
        self.scoring_url = os.getenv("N8N_SCORING_WEBHOOK", "")

    def deliver_jobs(self, jobs: List[Dict], batch_id: str = None) -> bool:
        """Deliver processed jobs to n8n webhook."""
        if not self.webhook_url:
            logger.warning("n8n webhook URL not configured")
            return False

        if not jobs:
            logger.info("No jobs to deliver")
            return True

        try:
            payload = {
                "batch_id": batch_id or datetime.now().strftime("BATCH_%Y%m%d_%H%M%S"),
                "timestamp": datetime.now().isoformat(),
                "job_count": len(jobs),
                "jobs": jobs,
                "metadata": {
                    "source": "BD-Automation-Engine",
                    "version": "2.0",
                },
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 200:
                logger.info(f"Delivered {len(jobs)} jobs to n8n webhook")
                return True
            else:
                logger.error(
                    f"Webhook delivery failed: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Webhook delivery error: {e}")
            return False

    def deliver_hot_leads(self, hot_leads: List[Dict]) -> bool:
        """Deliver hot leads specifically for urgent processing."""
        if not hot_leads:
            return True

        # Use scoring webhook for hot leads (higher priority)
        url = self.scoring_url or self.webhook_url
        if not url:
            return False

        try:
            payload = {
                "alert_type": "HOT_LEADS",
                "timestamp": datetime.now().isoformat(),
                "lead_count": len(hot_leads),
                "leads": hot_leads,
                "priority": "URGENT",
            }

            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Hot lead webhook error: {e}")
            return False


# ============================================
# MAIN ORCHESTRATOR
# ============================================


class BDOrchestrator:
    """Main orchestrator coordinating all BD automation engines."""

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.engines = import_engines()
        self.email_notifier = EmailNotifier(config)
        self.webhook_delivery = WebhookDelivery(config)

        # Ensure output directories exist
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        (Path(config.output_dir) / "Logs").mkdir(exist_ok=True)
        (Path(config.output_dir) / "BD_Briefings").mkdir(exist_ok=True)
        (Path(config.output_dir) / "notion").mkdir(exist_ok=True)
        (Path(config.output_dir) / "n8n").mkdir(exist_ok=True)

    def _validate_stage_output(self, stage_name: str, data: list, min_count: int = 0) -> bool:
        """Validate that a stage produced usable output before proceeding."""
        if data is None:
            logger.error(f"Stage '{stage_name}' returned None — downstream stages will skip")
            return False
        if not isinstance(data, list):
            logger.error(f"Stage '{stage_name}' returned {type(data).__name__}, expected list")
            return False
        if len(data) < min_count:
            logger.warning(f"Stage '{stage_name}' produced only {len(data)} results (expected >= {min_count})")
            return len(data) > 0
        return True

    def _run_stage(self, stage_name: str, stage_fn, checkpoint: PipelineCheckpoint,
                   stage_results: List[StageResult], errors: List[str]) -> Optional[any]:
        """Execute a single pipeline stage with checkpoint and quarantine support.

        Returns the stage function's return value, or None if skipped/failed.
        """
        if self.config.resume and checkpoint.is_completed(stage_name):
            stage_results.append(StageResult(
                name=stage_name, status="skipped", record_count=0,
            ))
            print(f"  Skipped (completed in previous run)")
            return None

        stage_start = datetime.now()
        try:
            result = stage_fn()
            duration = (datetime.now() - stage_start).total_seconds()
            record_count = len(result) if isinstance(result, list) else 0
            stage_results.append(StageResult(
                name=stage_name, status="passed",
                duration_seconds=duration, record_count=record_count,
            ))
            checkpoint.mark_completed(stage_name)
            return result
        except Exception as e:
            duration = (datetime.now() - stage_start).total_seconds()
            error_msg = f"{stage_name} error: {e}"
            errors.append(error_msg)
            logger.error(f"{stage_name} CRASHED: {e}", exc_info=True)
            stage_results.append(StageResult(
                name=stage_name, status="failed",
                duration_seconds=duration, error=str(e),
            ))
            checkpoint.mark_failed(stage_name, str(e))

            if self.config.fail_on_stage_error:
                raise
            return None

    def _print_run_summary(self, stage_results: List[StageResult],
                           total_duration: float, errors: List[str]) -> None:
        """Print a formatted summary table of all stage results."""
        print(f"\n{'=' * 75}")
        print("RUN SUMMARY")
        print(f"{'=' * 75}")
        print(f"{'Stage':<25} {'Status':<10} {'Duration':>10} {'Records':>10}")
        print(f"{'-' * 25} {'-' * 10} {'-' * 10} {'-' * 10}")

        for sr in stage_results:
            duration_str = f"{sr.duration_seconds:.1f}s" if sr.duration_seconds > 0 else "-"
            records_str = str(sr.record_count) if sr.record_count > 0 else "-"
            print(f"{sr.name:<25} {sr.status:<10} {duration_str:>10} {records_str:>10}")

        print(f"{'-' * 25} {'-' * 10} {'-' * 10} {'-' * 10}")
        print(f"{'TOTAL':<25} {'':10} {total_duration:.1f}s")
        print()

        failed_stages = [sr for sr in stage_results if sr.status == "failed"]
        if failed_stages:
            print(f"QUARANTINED ERRORS ({len(failed_stages)}):")
            for sr in failed_stages:
                print(f"  [{sr.name}] {sr.error}")
            print()

        if errors:
            print(f"Total errors: {len(errors)}")
        else:
            print("No errors.")
        print(f"{'=' * 75}")

    def run_full_pipeline(self, input_path: str = None) -> PipelineResult:
        """
        Run the complete BD automation pipeline.

        Stages:
        1. Ingest raw jobs from JSON
        2. Standardize with LLM extraction
        3. Map to federal programs
        4. Calculate BD scores
        5. Run QA evaluation
        6. Generate briefings for hot leads
        7. Export to Notion/n8n
        8. Send notifications
        """
        start_time = datetime.now()
        run_id = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        errors = []
        stage_results: List[StageResult] = []

        # Initialize checkpoint
        checkpoint = PipelineCheckpoint(self.config.output_dir)
        if self.config.resume:
            existing = checkpoint.load()
            if existing.get("stages_completed"):
                logger.info(f"Resuming run {existing.get('run_id')} — "
                            f"{len(existing['stages_completed'])} stages already completed")
                print(f"Resuming from checkpoint: {len(existing['stages_completed'])} stages done")
            else:
                checkpoint.create(run_id)
        else:
            checkpoint.create(run_id)

        input_file = input_path or self.config.input_path
        if not input_file:
            return PipelineResult(
                success=False,
                jobs_processed=0,
                hot_leads=0,
                warm_leads=0,
                cold_leads=0,
                briefings_generated=0,
                qa_approved=0,
                qa_needs_review=0,
                export_files={},
                errors=["No input file specified"],
                duration_seconds=0,
            )

        logger.info(f"Starting full pipeline: {input_file}")
        print(f"\n{'=' * 60}")
        print("BD AUTOMATION ENGINE - Full Pipeline")
        print(f"{'=' * 60}")
        print(f"Input: {input_file}")
        print(f"Test Mode: {self.config.test_mode}")
        print(f"Batch Size: {self.config.batch_size}")
        if self.config.resume:
            print(f"Mode: RESUME")
        if not self.config.fail_on_stage_error:
            print(f"Mode: QUARANTINE (non-strict)")

        # Stage 1: Ingest
        print(f"\n[1/11] INGESTING JOBS...")
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                all_jobs = json.load(f)

            if self.config.test_mode:
                all_jobs = all_jobs[:3]
                print(f"  Test mode: limited to {len(all_jobs)} jobs")

            print(f"  Loaded {len(all_jobs)} jobs")
        except Exception as e:
            errors.append(f"Ingest error: {e}")
            logger.error(f"Ingest error: {e}")
            stage_results.append(StageResult(name="ingest", status="failed", error=str(e)))
            return self._error_result(errors, start_time)

        if not self._validate_stage_output("ingest", all_jobs, min_count=1):
            errors.append("Ingest produced no jobs — aborting pipeline")
            stage_results.append(StageResult(name="ingest", status="failed", error="No jobs loaded"))
            return self._error_result(errors, start_time)

        stage_results.append(StageResult(
            name="ingest", status="passed", record_count=len(all_jobs),
        ))
        checkpoint.mark_completed("ingest")

        # Batch processing: chunk jobs and process each batch
        batch_size = self.config.batch_size
        total_batches = max(1, (len(all_jobs) + batch_size - 1) // batch_size)
        if total_batches > 1:
            print(f"\n  Processing in {total_batches} batches of up to {batch_size} jobs")

        all_processed_jobs = []
        all_hot_leads = []
        all_warm_leads = []
        all_cold_leads = []
        all_briefings = []
        total_qa_approved = 0
        total_qa_needs_review = 0
        export_files = {}
        pipeline_degraded = False  # Set True when critical stages (mapping/scoring) fail

        for batch_idx in range(total_batches):
            batch_start = batch_idx * batch_size
            batch_end = min(batch_start + batch_size, len(all_jobs))
            jobs = all_jobs[batch_start:batch_end]

            if total_batches > 1:
                print(f"\n{'~' * 40}")
                print(f"  Batch {batch_idx + 1}/{total_batches} ({len(jobs)} jobs)")
                print(f"{'~' * 40}")

            # Stage 2-4: Program Mapping Pipeline
            print(f"\n[2/11] RUNNING PROGRAM MAPPING PIPELINE...")
            if "mapping" in self.engines and self.config.run_mapping:
                def _run_mapping():
                    self.engines["mapping"]["PipelineConfig"](
                        input_path=input_file,
                        output_dir=self.config.output_dir,
                        test_mode=self.config.test_mode,
                        anthropic_api_key=self.config.anthropic_api_key,
                    )
                    return self.engines["mapping"]["process_jobs_batch"](jobs)

                try:
                    result = self._run_stage(
                        "mapping", _run_mapping, checkpoint, stage_results, errors,
                    )
                    if result is not None and self._validate_stage_output("mapping", result, min_count=1):
                        print(f"  Mapped {len(result)} jobs to programs")
                        jobs = result
                    elif result is not None:
                        errors.append("Mapping produced no results — using raw jobs")
                        logger.warning("Mapping stage returned no results; falling back to raw jobs")
                        pipeline_degraded = True
                    else:
                        # _run_stage returned None = crash in quarantine mode
                        pipeline_degraded = True
                        errors.append("CRITICAL: Mapping engine crashed — downstream data is unreliable")
                        logger.error("Mapping crash in quarantine mode — pipeline_degraded=True")
                except Exception:
                    if self.config.fail_on_stage_error:
                        errors.append("ABORTING: Mapping engine crashed — cannot produce valid results")
                        duration = (datetime.now() - start_time).total_seconds()
                        self._print_run_summary(stage_results, duration, errors)
                        return self._error_result(errors, start_time)
            else:
                print("  Skipped (engine not available)")
                stage_results.append(StageResult(name="mapping", status="skipped"))

            # Stage 2b: SAM.gov Opportunity Sync (optional)
            sam_results = []
            if self.config.run_sam_sync:
                print(f"\n[2b/11] SYNCING SAM.gov OPPORTUNITIES...")

                def _run_sam_sync():
                    from Engine8_Knowledge.scrapers.sam_gov_sync import SAMGovSync, OpportunityQuery
                    client = SAMGovSync()

                    async def _fetch():
                        results = []
                        # Extract program keywords from mapped jobs
                        seen_keywords = set()
                        for job in jobs[:20]:
                            mapping = job.get("_mapping", {})
                            program_name = mapping.get("program_name", "")
                            if program_name and program_name not in seen_keywords:
                                seen_keywords.add(program_name)
                                query = OpportunityQuery(keywords=[program_name], limit=10)
                                opps = await client.search_opportunities(query)
                                results.extend(opps)
                        return results

                    return asyncio.run(_fetch())

                try:
                    result = self._run_stage(
                        "sam_sync", _run_sam_sync, checkpoint, stage_results, errors,
                    )
                    if result is not None:
                        sam_results = result
                        print(f"  Found {len(sam_results)} SAM.gov opportunities")
                except Exception:
                    pass  # Error already recorded by _run_stage
            else:
                stage_results.append(StageResult(name="sam_sync", status="skipped"))

            # Stage 2c: NER Entity Enrichment
            if self.config.run_ner and jobs:
                print(f"\n[2c/11] RUNNING NER ENTITY ENRICHMENT...")

                def _run_ner():
                    from Engine8_Knowledge.ml.defense_ner import run_ner_pipeline_stage
                    return run_ner_pipeline_stage(jobs)

                try:
                    result = self._run_stage(
                        "ner_enrichment", _run_ner, checkpoint, stage_results, errors,
                    )
                    if result is not None:
                        jobs = result
                        entity_count = sum(
                            len(v) for j in jobs for v in j.get("entities", {}).values()
                        )
                        print(f"  Extracted {entity_count} entities from {len(jobs)} records")
                except Exception:
                    pass  # Error already recorded by _run_stage
            else:
                stage_results.append(StageResult(name="ner_enrichment", status="skipped"))

            # Stage 5: BD Scoring
            print(f"\n[3/11] CALCULATING BD SCORES...")
            if "scoring" in self.engines and self.config.run_scoring:
                def _run_scoring():
                    return self.engines["scoring"]["score_batch"](jobs)

                try:
                    result = self._run_stage(
                        "scoring", _run_scoring, checkpoint, stage_results, errors,
                    )
                    if result is not None and self._validate_stage_output("scoring", result, min_count=1):
                        print(f"  Scored {len(result)} jobs")
                        jobs = result
                    elif result is not None:
                        errors.append("Scoring produced no results — using unscored jobs")
                        logger.warning("Scoring stage returned no results; falling back to unscored jobs")
                        pipeline_degraded = True
                    else:
                        # _run_stage returned None = crash in quarantine mode
                        pipeline_degraded = True
                        errors.append("CRITICAL: Scoring engine crashed — tier data is unreliable")
                        logger.error("Scoring crash in quarantine mode — pipeline_degraded=True")
                except Exception:
                    if self.config.fail_on_stage_error:
                        errors.append("ABORTING: Scoring engine crashed — cannot tier jobs correctly")
                        duration = (datetime.now() - start_time).total_seconds()
                        self._print_run_summary(stage_results, duration, errors)
                        return self._error_result(errors, start_time)
            else:
                print("  Skipped (engine not available)")
                stage_results.append(StageResult(name="scoring", status="skipped"))

            # Categorize by tier
            hot_leads = [
                j
                for j in jobs
                if "Hot" in str(j.get("_scoring", {}).get("Priority Tier", ""))
            ]
            warm_leads = [
                j
                for j in jobs
                if "Warm" in str(j.get("_scoring", {}).get("Priority Tier", ""))
            ]
            cold_leads = [
                j
                for j in jobs
                if "Cold" in str(j.get("_scoring", {}).get("Priority Tier", ""))
            ]

            print(
                f"  Tiers: Hot={len(hot_leads)}, Warm={len(warm_leads)}, Cold={len(cold_leads)}"
            )

            # Data quality gate: if scoring ran but produced zero categorized leads, flag it
            categorized = len(hot_leads) + len(warm_leads) + len(cold_leads)
            if self.config.run_scoring and "scoring" in self.engines and categorized == 0 and len(jobs) > 0:
                gate_msg = (
                    f"DATA QUALITY WARNING: {len(jobs)} jobs processed but 0 categorized into tiers. "
                    "Scoring may have failed silently — review _scoring fields in output."
                )
                errors.append(gate_msg)
                logger.warning(gate_msg)
                pipeline_degraded = True
                if self.config.fail_on_stage_error:
                    errors.append("ABORTING: Zero leads categorized after scoring — pipeline output would be empty")
                    duration = (datetime.now() - start_time).total_seconds()
                    self._print_run_summary(stage_results, duration, errors)
                    return self._error_result(errors, start_time)

            # Stage 6: QA Evaluation
            print(f"\n[4/11] RUNNING QA EVALUATION...")
            qa_approved = 0
            qa_needs_review = 0
            if "qa" in self.engines and self.config.run_qa:
                def _run_qa():
                    return self.engines["qa"]["run_qa_workflow"](jobs)

                try:
                    qa_result = self._run_stage(
                        "qa", _run_qa, checkpoint, stage_results, errors,
                    )
                    if qa_result is not None:
                        qa_report, approved_jobs, review_jobs = qa_result
                        qa_approved = len(approved_jobs)
                        qa_needs_review = len(review_jobs)
                        print(f"  QA: {qa_approved} approved, {qa_needs_review} need review")
                except Exception:
                    pass  # Error already recorded by _run_stage
            else:
                print("  Skipped (engine not available)")
                stage_results.append(StageResult(name="qa", status="skipped"))

            # Stage 7: Generate Briefings
            print(f"\n[5/11] GENERATING BRIEFINGS...")
            briefings = []
            briefings_to_process = hot_leads if self.config.hot_leads_only else jobs
            if (
                "briefings" in self.engines
                and self.config.run_briefings
                and briefings_to_process
            ):
                def _run_briefings():
                    return self.engines["briefings"]["generate_briefings_batch"](
                        briefings_to_process,
                        output_dir=str(Path(self.config.output_dir) / "BD_Briefings"),
                        min_score=self.config.min_bd_score,
                        include_contacts=self.config.run_contacts,
                    )

                try:
                    result = self._run_stage(
                        "briefings", _run_briefings, checkpoint, stage_results, errors,
                    )
                    if result is not None:
                        briefings = result
                        print(f"  Generated {len(briefings)} briefings")
                except Exception:
                    pass
            else:
                print("  Skipped (no hot leads or engine not available)")
                stage_results.append(StageResult(name="briefings", status="skipped"))

            # Stage 8: Export
            print(f"\n[6/11] EXPORTING RESULTS...")
            if pipeline_degraded:
                degrade_msg = (
                    "EXPORT BLOCKED: Pipeline is degraded (mapping or scoring failed). "
                    "Exporting corrupt data would produce misleading BD intelligence. "
                    "Fix the failed stages and re-run, or use --fail-on-stage-error to abort early."
                )
                print(f"  {degrade_msg}")
                errors.append(degrade_msg)
                logger.error(degrade_msg)
                stage_results.append(StageResult(name="export", status="blocked", error="pipeline_degraded"))
            elif "mapping" in self.engines:
                def _run_export():
                    return self.engines["mapping"]["export_batch"](
                        jobs, output_dir=self.config.output_dir, formats=["notion", "n8n"]
                    )

                try:
                    export_result = self._run_stage(
                        "export", _run_export, checkpoint, stage_results, errors,
                    )
                    if export_result is not None:
                        for fmt, res in export_result.items():
                            if res.success:
                                export_files[fmt] = res.file_path
                                print(f"  {fmt.upper()}: {res.file_path}")
                except Exception:
                    pass
            else:
                stage_results.append(StageResult(name="export", status="skipped"))

            # Stage 7: Webhook Delivery
            print(f"\n[7/11] DELIVERING TO WEBHOOKS...")
            if pipeline_degraded:
                print("  Skipped (pipeline degraded — corrupt data not delivered)")
                stage_results.append(StageResult(name="webhooks", status="blocked", error="pipeline_degraded"))
            elif self.config.send_webhook:
                def _run_webhooks():
                    delivered = []
                    job_result = self.webhook_delivery.deliver_jobs(jobs)
                    if job_result:
                        print(f"  Delivered {len(jobs)} jobs to webhook")
                        delivered.extend(jobs)
                    else:
                        raise RuntimeError("Webhook delivery failed for jobs batch")
                    if hot_leads:
                        lead_result = self.webhook_delivery.deliver_hot_leads(hot_leads)
                        if lead_result:
                            print(f"  Delivered {len(hot_leads)} hot leads to webhook")
                        else:
                            raise RuntimeError("Webhook delivery failed for hot leads")
                    return delivered

                try:
                    self._run_stage(
                        "webhooks", _run_webhooks, checkpoint, stage_results, errors,
                    )
                except Exception:
                    pass
            else:
                print("  Skipped (webhooks disabled)")
                stage_results.append(StageResult(name="webhooks", status="skipped"))

            # Stage 8: Email Notifications
            print(f"\n[8/11] SENDING NOTIFICATIONS...")
            if pipeline_degraded:
                print("  Skipped (pipeline degraded — corrupt data not sent)")
                stage_results.append(StageResult(name="notifications", status="blocked", error="pipeline_degraded"))
            elif self.config.send_email and hot_leads:
                self.email_notifier.send_hot_lead_alert(hot_leads, briefings)
                stage_results.append(StageResult(name="notifications", status="passed"))
                checkpoint.mark_completed("notifications")
            else:
                print("  Skipped (email disabled or no hot leads)")
                stage_results.append(StageResult(name="notifications", status="skipped"))

            # Accumulate batch results
            all_processed_jobs.extend(jobs)
            all_hot_leads.extend(hot_leads)
            all_warm_leads.extend(warm_leads)
            all_cold_leads.extend(cold_leads)
            all_briefings.extend(briefings)
            total_qa_approved += qa_approved
            total_qa_needs_review += qa_needs_review

            if total_batches > 1:
                print(f"\n  Batch {batch_idx + 1}/{total_batches} complete")

        # Stages 9-11: Run Bullhorn+Dashboard and Knowledge indexing in parallel
        # Stage 10 (dashboard) depends on Stage 9 (Bullhorn ETL), but Stage 11 is independent
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _run_bullhorn_and_dashboard():
            """Stages 9-10: Bullhorn ETL then Dashboard Export (sequential)."""
            stage_errors = []
            # Stage 9: Bullhorn ETL
            print(f"\n[9/11] RUNNING BULLHORN ETL...")
            if "bullhorn" in self.engines and self.config.run_bullhorn:
                bullhorn_start = datetime.now()
                try:
                    self.engines["bullhorn"]["run_pipeline"]()
                    print(f"  Bullhorn ETL completed")
                    stage_results.append(StageResult(
                        name="bullhorn_etl", status="passed",
                        duration_seconds=(datetime.now() - bullhorn_start).total_seconds(),
                    ))
                    checkpoint.mark_completed("bullhorn_etl")
                except Exception as e:
                    stage_errors.append(f"Bullhorn ETL error: {e}")
                    logger.error(f"Bullhorn ETL error: {e}")
                    stage_results.append(StageResult(
                        name="bullhorn_etl", status="failed",
                        duration_seconds=(datetime.now() - bullhorn_start).total_seconds(),
                        error=str(e),
                    ))
                    checkpoint.mark_failed("bullhorn_etl", str(e))
            else:
                print("  Skipped (engine not available or disabled)")
                stage_results.append(StageResult(name="bullhorn_etl", status="skipped"))

            # Stage 10: Dashboard Export with Verification
            print(f"\n[10/11] EXPORTING DASHBOARD DATA...")
            if "bullhorn" in self.engines and self.config.export_dashboard:
                dashboard_start = datetime.now()
                try:
                    self.engines["bullhorn"]["run_dashboard_export"]()
                    print(f"  Dashboard export completed")

                    # VERIFICATION: Check all required files were created
                    dashboard_dir = PROJECT_ROOT / "dashboard" / "public" / "data"
                    required_files = [
                        "past_performance.json",
                        "prime_org_chart.json",
                        "contact_org_chart.json",
                        "program_org_chart.json",
                        "placements.json",
                        "correlation_summary_enriched.json",
                    ]
                    missing_files = [
                        f for f in required_files if not (dashboard_dir / f).exists()
                    ]
                    if missing_files:
                        error_msg = f"Dashboard export incomplete: missing {missing_files}"
                        stage_errors.append(error_msg)
                        logger.warning(error_msg)
                    else:
                        logger.info("Dashboard data verified: all 6 files present")
                        print(
                            f"  Verified: all {len(required_files)} dashboard files present"
                        )
                    stage_results.append(StageResult(
                        name="dashboard_export", status="passed",
                        duration_seconds=(datetime.now() - dashboard_start).total_seconds(),
                    ))
                    checkpoint.mark_completed("dashboard_export")
                except Exception as e:
                    stage_errors.append(f"Dashboard export error: {e}")
                    logger.error(f"Dashboard export error: {e}")
                    stage_results.append(StageResult(
                        name="dashboard_export", status="failed",
                        duration_seconds=(datetime.now() - dashboard_start).total_seconds(),
                        error=str(e),
                    ))
                    checkpoint.mark_failed("dashboard_export", str(e))
            else:
                print("  Skipped (engine not available or disabled)")
                stage_results.append(StageResult(name="dashboard_export", status="skipped"))
            return stage_errors

        def _run_knowledge_indexing():
            """Stage 11: Knowledge Indexing (independent of Bullhorn)."""
            stage_errors = []
            print(f"\n[11/11] INDEXING KNOWLEDGE BASE...")
            if "knowledge" in self.engines and self.config.run_knowledge:
                knowledge_start = datetime.now()
                try:
                    indexer = self.engines["knowledge"]["BDIndexer"]()
                    indexer.index_all()
                    print(f"  Knowledge base indexed successfully")
                    logger.info("Engine8_Knowledge indexing completed")
                    stage_results.append(StageResult(
                        name="knowledge_indexing", status="passed",
                        duration_seconds=(datetime.now() - knowledge_start).total_seconds(),
                    ))
                    checkpoint.mark_completed("knowledge_indexing")
                except Exception as e:
                    stage_errors.append(f"Knowledge indexing error: {e}")
                    logger.error(f"Knowledge indexing error: {e}")
                    stage_results.append(StageResult(
                        name="knowledge_indexing", status="failed",
                        duration_seconds=(datetime.now() - knowledge_start).total_seconds(),
                        error=str(e),
                    ))
                    checkpoint.mark_failed("knowledge_indexing", str(e))
            else:
                print("  Skipped (engine not available or disabled)")
                stage_results.append(StageResult(name="knowledge_indexing", status="skipped"))
            return stage_errors

        # Execute stages 9+10 and 11 in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(_run_bullhorn_and_dashboard): "bullhorn+dashboard",
                executor.submit(_run_knowledge_indexing): "knowledge",
            }
            for future in as_completed(futures):
                stage_name = futures[future]
                try:
                    stage_errors = future.result()
                    errors.extend(stage_errors)
                except Exception as e:
                    errors.append(f"Parallel stage '{stage_name}' crashed: {e}")
                    logger.error(f"Parallel stage '{stage_name}' crashed: {e}")

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()

        # Build result
        result = PipelineResult(
            success=len(errors) == 0,
            jobs_processed=len(all_processed_jobs),
            hot_leads=len(all_hot_leads),
            warm_leads=len(all_warm_leads),
            cold_leads=len(all_cold_leads),
            briefings_generated=len(all_briefings),
            qa_approved=total_qa_approved,
            qa_needs_review=total_qa_needs_review,
            export_files=export_files,
            errors=errors,
            duration_seconds=duration,
        )

        # Print run summary table
        self._print_run_summary(stage_results, duration, errors)

        # Print legacy summary for backward compatibility
        print(f"\n{'=' * 60}")
        print("PIPELINE COMPLETE")
        print(f"{'=' * 60}")
        print(f"Duration: {duration:.1f} seconds")
        print(f"Jobs Processed: {result.jobs_processed}")
        print(f"Hot Leads: {result.hot_leads}")
        print(f"Warm Leads: {result.warm_leads}")
        print(f"Cold Leads: {result.cold_leads}")
        print(f"Briefings: {result.briefings_generated}")
        print(f"QA Approved: {result.qa_approved}")
        print(f"QA Review: {result.qa_needs_review}")
        print(f"Errors: {len(errors)}")
        print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")

        # Log result
        logger.info(
            f"Pipeline complete: {result.jobs_processed} jobs, {result.hot_leads} hot leads"
        )

        # Persist state and check alerts
        self._save_pipeline_state(result)
        self._check_and_send_alerts(result)

        return result

    def _save_pipeline_state(self, result: PipelineResult, run_id: str = None):
        """Persist pipeline run result to outputs/pipeline_state.json."""
        state_file = Path(self.config.output_dir) / "pipeline_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = {}
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Pipeline state file corrupted ({e}), resetting run history")
                state = {}

        run_record = {
            "run_id": run_id or datetime.now().strftime("RUN_%Y%m%d_%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "success": result.success,
            "duration_seconds": result.duration_seconds,
            "stats": {
                "jobs_processed": result.jobs_processed,
                "hot_leads": result.hot_leads,
                "warm_leads": result.warm_leads,
                "cold_leads": result.cold_leads,
                "briefings_generated": result.briefings_generated,
                "qa_approved": result.qa_approved,
                "qa_needs_review": result.qa_needs_review,
            },
            "errors": result.errors,
        }

        state["last_completed_run"] = run_record
        state.setdefault("history", []).append(run_record)
        state["current_run"] = None

        # Keep last 100 runs
        if len(state["history"]) > 100:
            state["history"] = state["history"][-100:]

        with open(state_file, "w") as f:
            json.dump(state, f, indent=2, default=str)
        logger.info(f"Pipeline state saved: {state_file}")

    def _check_and_send_alerts(self, result: PipelineResult):
        """Trigger alert engine after pipeline run."""
        try:
            from Engine6_QA.scripts.alerts import AlertEngine

            engine = AlertEngine()
            alerts = engine.check_all_rules()
            if alerts:
                engine.deliver_all(alerts)
                logger.info(f"Delivered {len(alerts)} alert(s)")
        except ImportError:
            logger.warning("Alert engine not available (Engine6_QA.scripts.alerts not installed)")
        except Exception as e:
            logger.error(f"Alert check failed: {e}")

    def _error_result(self, errors: List[str], start_time: datetime) -> PipelineResult:
        """Create an error result."""
        duration = (datetime.now() - start_time).total_seconds()
        return PipelineResult(
            success=False,
            jobs_processed=0,
            hot_leads=0,
            warm_leads=0,
            cold_leads=0,
            briefings_generated=0,
            qa_approved=0,
            qa_needs_review=0,
            export_files={},
            errors=errors,
            duration_seconds=duration,
        )

    def run_scheduled(self, interval_hours: int = 6):
        """Run the pipeline on a schedule."""
        logger.info(f"Starting scheduled runs every {interval_hours} hours")
        print(f"\nScheduled mode: running every {interval_hours} hours")
        print("Press Ctrl+C to stop\n")

        while True:
            try:
                # Find latest input file
                input_dir = PROJECT_ROOT / "Engine1_Scraper" / "data"
                json_files = list(input_dir.glob("*.json"))
                if json_files:
                    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                    result = self.run_full_pipeline(str(latest_file))

                    # Send daily summary
                    if self.config.send_email:
                        self.email_notifier.send_daily_summary(result)
                else:
                    logger.warning("No input files found")

                # Sleep until next run
                next_run = datetime.now() + timedelta(hours=interval_hours)
                logger.info(f"Next run scheduled for: {next_run}")
                time_module.sleep(interval_hours * 3600)

            except KeyboardInterrupt:
                logger.info("Scheduled runs stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduled run error: {e}")
                time_module.sleep(300)  # Wait 5 minutes on error


# ============================================
# CLI INTERFACE
# ============================================


def main():
    parser = argparse.ArgumentParser(
        description="BD Automation Engine - Master Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline on input file
  python orchestrator.py --input Engine1_Scraper/data/Sample_Jobs.json

  # Run with email notifications for hot leads
  python orchestrator.py --input data/jobs.json --email --hot-leads-only

  # Run in test mode (first 3 jobs)
  python orchestrator.py --input data/jobs.json --test

  # Run on schedule (every 6 hours)
  python orchestrator.py --schedule --interval 6

  # Skip specific stages
  python orchestrator.py --input data/jobs.json --no-briefings --no-qa

  # Resume a failed run from last checkpoint
  python orchestrator.py --input data/jobs.json --resume

  # Continue on stage failures (quarantine mode)
  python orchestrator.py --input data/jobs.json

  # Fail fast on any stage error (strict mode)
  python orchestrator.py --input data/jobs.json --strict

  # Process in batches of 25
  python orchestrator.py --input data/jobs.json --batch-size 25
        """,
    )

    # Input/Output
    parser.add_argument("--input", "-i", help="Input JSON file with jobs")
    parser.add_argument("--output", "-o", default="outputs", help="Output directory")

    # Pipeline Control
    parser.add_argument("--test", action="store_true", help="Test mode (first 3 jobs)")
    parser.add_argument(
        "--hot-leads-only", action="store_true", help="Only process hot leads"
    )
    parser.add_argument(
        "--min-score", type=int, default=0, help="Minimum BD score to process"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from last checkpoint, skipping completed stages"
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Fail fast on any stage error (default: quarantine and continue)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=50,
        help="Number of jobs per batch (default: 50)"
    )

    # Stage Control
    parser.add_argument(
        "--no-mapping", action="store_true", help="Skip program mapping"
    )
    parser.add_argument(
        "--no-contacts", action="store_true", help="Skip contact lookup"
    )
    parser.add_argument(
        "--no-briefings", action="store_true", help="Skip briefing generation"
    )
    parser.add_argument("--no-scoring", action="store_true", help="Skip BD scoring")
    parser.add_argument("--no-qa", action="store_true", help="Skip QA evaluation")
    parser.add_argument("--no-bullhorn", action="store_true", help="Skip Bullhorn ETL")
    parser.add_argument(
        "--no-dashboard-export", action="store_true", help="Skip dashboard data export"
    )
    parser.add_argument(
        "--no-knowledge", action="store_true", help="Skip knowledge base indexing"
    )
    parser.add_argument(
        "--sam-sync", action="store_true",
        help="Enable SAM.gov opportunity sync (requires SAM_API_KEY or TANGO_API_KEY)"
    )

    # Notifications
    parser.add_argument("--email", action="store_true", help="Send email notifications")
    parser.add_argument(
        "--no-webhook", action="store_true", help="Disable webhook delivery"
    )

    # Validation
    parser.add_argument(
        "--validate-scores", action="store_true",
        help="Run BD score validation against Bullhorn placement outcomes (XGBoost)"
    )

    # Scheduling
    parser.add_argument("--schedule", action="store_true", help="Run on schedule")
    parser.add_argument(
        "--interval", type=int, default=6, help="Schedule interval in hours"
    )

    args = parser.parse_args()

    # Build configuration
    config = OrchestratorConfig(
        input_path=args.input,
        output_dir=args.output,
        test_mode=args.test,
        hot_leads_only=args.hot_leads_only,
        min_bd_score=args.min_score,
        run_mapping=not args.no_mapping,
        run_contacts=not args.no_contacts,
        run_briefings=not args.no_briefings,
        run_scoring=not args.no_scoring,
        run_qa=not args.no_qa,
        run_bullhorn=not args.no_bullhorn,
        export_dashboard=not args.no_dashboard_export,
        run_knowledge=not args.no_knowledge,
        run_sam_sync=args.sam_sync,
        send_email=args.email,
        send_webhook=not args.no_webhook,
        schedule_enabled=args.schedule,
        schedule_interval_hours=args.interval,
        batch_size=args.batch_size,
        fail_on_stage_error=args.strict,
        resume=args.resume,
    )

    # Create and run orchestrator
    orchestrator = BDOrchestrator(config)

    if args.validate_scores:
        _run_score_validation()
    elif args.schedule:
        orchestrator.run_scheduled(args.interval)
    elif args.input:
        result = orchestrator.run_full_pipeline(args.input)
        sys.exit(0 if result.success else 1)
    else:
        parser.print_help()
        print("\nError: --input required unless using --schedule or --validate-scores")
        sys.exit(1)


def _run_score_validation():
    """Run BD score validation and print results."""
    from Engine5_Scoring.scripts.score_validator import BDScoreValidator

    print(f"\n{'=' * 60}")
    print("BD SCORE VALIDATION (XGBoost vs Rule-Based)")
    print(f"{'=' * 60}")

    validator = BDScoreValidator()
    result = validator.validate()

    if result.sample_size == 0:
        print("\nNo training data available.")
        for rec in result.recommendations:
            print(f"  - {rec}")
        sys.exit(0)

    print(f"\nSample Size: {result.sample_size} placements")
    print(f"\n{'Rule-Based Scoring':>25}  {'XGBoost ML':>15}")
    print(f"{'-' * 25}  {'-' * 15}")
    print(f"{'Accuracy:':<25}  {result.manual_accuracy:>6.1%}         {result.ml_accuracy:>6.1%}")
    print(f"{'MAE:':<25}  {result.manual_mae:>6.4f}         {result.ml_mae:>6.4f}")

    print(f"\nFeature Importance (XGBoost):")
    for feature, importance in sorted(
        result.feature_importance.items(), key=lambda x: x[1], reverse=True
    ):
        bar = "#" * int(importance * 40)
        print(f"  {feature:<20} {importance:.4f}  {bar}")

    print(f"\nRecommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")

    report_path = validator.save_report(result)
    print(f"\nFull report saved: {report_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
