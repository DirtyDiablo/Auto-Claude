"""
Bridge Dify to your existing n8n workflows.

Your 18 n8n Workflows:
- BD_Master_Orchestration_Workflow - Main pipeline coordinator
- PTS_BD_WF1_Apify_Job_Scraper_Intake - Job scraping ingestion
- PTS_BD_WF2_AI_Enrichment_Processor - AI enrichment pipeline
- PTS_BD_WF3_Hub_to_BD_Opportunities - Opportunity classification
- PTS_BD_WF4_Contact_Classification - OrgChart tier assignment
- PTS_BD_WF5_Hot_Lead_Alerts - Priority notification system
- PTS_BD_WF6_Weekly_Summary_Report - Automated reporting
- Clearance_Job_RAG_Agent - Security clearance RAG queries
- Firecrawl_Search_Agent - Web search agent
- And more...

This bridge allows Dify to:
1. Trigger n8n workflows from visual AI apps
2. Get workflow status and results
3. Schedule workflows
4. Chain n8n automations with AI operations
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

logger = logging.getLogger(__name__)


@dataclass
class WorkflowTriggerResult:
    """Result from triggering an n8n workflow."""

    success: bool
    workflow_name: str
    execution_id: Optional[str]
    status: str
    data: Dict[str, Any]
    triggered_at: str


class DifyN8NBridge:
    """
    Connect Dify apps to your 18 existing n8n workflows.

    This allows Dify to:
    1. Trigger workflows via webhooks
    2. Check execution status
    3. Get workflow results
    4. Schedule recurring executions

    Workflows are triggered via webhooks you've configured in n8n.
    """

    # Map workflow names to their webhook paths
    # Update these paths to match your actual n8n webhook configuration
    WORKFLOW_WEBHOOKS = {
        # Job Processing Pipeline
        "job_scraper": "/webhook/job-scraper-trigger",
        "job_enrichment": "/webhook/ai-enrichment",
        "job_scoring": "/webhook/score-job",
        # BD Opportunity Pipeline
        "hub_to_opportunities": "/webhook/hub-to-bd",
        "contact_classification": "/webhook/contact-classify",
        # Alerts & Notifications
        "hot_lead_alert": "/webhook/hot-lead",
        "weekly_report": "/webhook/weekly-report",
        # RAG & Search
        "clearance_rag": "/webhook/clearance-rag",
        "firecrawl_search": "/webhook/firecrawl-search",
        # Master Orchestration
        "master_pipeline": "/webhook/master-pipeline",
    }

    # Map to workflow file names (for reference)
    WORKFLOW_FILES = {
        "job_scraper": "PTS_BD_WF1_Apify_Job_Scraper_Intake.json",
        "job_enrichment": "PTS_BD_WF2_AI_Enrichment_Processor.json",
        "hub_to_opportunities": "PTS_BD_WF3_Hub_to_BD_Opportunities.json",
        "contact_classification": "PTS_BD_WF4_Contact_Classification.json",
        "hot_lead_alert": "PTS_BD_WF5_Hot_Lead_Alerts.json",
        "weekly_report": "PTS_BD_WF6_Weekly_Summary_Report.json",
        "clearance_rag": "Clearance_Job_RAG_Agent.json",
        "firecrawl_search": "Firecrawl_Search_Agent.json",
        "master_pipeline": "BD_Master_Orchestration_Workflow.json",
    }

    def __init__(self, n8n_url: str = None, n8n_api_key: str = None):
        """
        Initialize the Dify-n8n bridge.

        Args:
            n8n_url: Base URL of your n8n instance
            n8n_api_key: API key for n8n API operations
        """
        self.n8n_url = n8n_url or os.getenv(
            "N8N_API_URL", "https://primetech.app.n8n.cloud"
        )
        self.n8n_api_key = n8n_api_key or os.getenv("N8N_API_KEY", "")

        headers = {"Content-Type": "application/json"}
        if self.n8n_api_key:
            headers["X-N8N-API-KEY"] = self.n8n_api_key

        self.client = httpx.AsyncClient(timeout=120.0, headers=headers)

        logger.info(f"DifyN8NBridge initialized: n8n={self.n8n_url}")

    async def trigger_workflow(
        self, workflow_key: str, payload: Dict[str, Any] = None
    ) -> WorkflowTriggerResult:
        """
        Trigger an n8n workflow by key.

        This is the main function Dify will use as a tool.

        Args:
            workflow_key: Key of workflow to trigger (see WORKFLOW_WEBHOOKS)
            payload: Data to send to the workflow

        Returns:
            WorkflowTriggerResult with execution details
        """
        webhook_path = self.WORKFLOW_WEBHOOKS.get(workflow_key)
        if not webhook_path:
            return WorkflowTriggerResult(
                success=False,
                workflow_name=workflow_key,
                execution_id=None,
                status="error",
                data={
                    "error": f"Unknown workflow: {workflow_key}. Available: {list(self.WORKFLOW_WEBHOOKS.keys())}"
                },
                triggered_at=datetime.now().isoformat(),
            )

        try:
            response = await self.client.post(
                f"{self.n8n_url}{webhook_path}", json=payload or {}
            )

            # n8n webhooks may return various status codes
            data = {}
            try:
                data = response.json()
            except Exception:
                data = {"raw_response": response.text}

            return WorkflowTriggerResult(
                success=response.status_code < 400,
                workflow_name=workflow_key,
                execution_id=data.get("executionId"),
                status="triggered" if response.status_code < 400 else "error",
                data=data,
                triggered_at=datetime.now().isoformat(),
            )

        except Exception as e:
            logger.error(f"Workflow trigger error: {e}")
            return WorkflowTriggerResult(
                success=False,
                workflow_name=workflow_key,
                execution_id=None,
                status="error",
                data={"error": str(e)},
                triggered_at=datetime.now().isoformat(),
            )

    # Convenience methods for common workflows

    async def trigger_job_scraper(
        self,
        keywords: List[str] = None,
        sources: List[str] = None,
        max_results: int = 100,
    ) -> WorkflowTriggerResult:
        """
        Trigger job scraping via n8n.

        Uses: PTS_BD_WF1_Apify_Job_Scraper_Intake

        Args:
            keywords: Search keywords (default: DCGS, ISR, TS/SCI)
            sources: Job sources to scrape (default: insight_global, teksystems, apex)
            max_results: Maximum jobs to scrape

        Returns:
            Trigger result with execution details
        """
        payload = {
            "keywords": keywords or ["DCGS", "ISR", "TS/SCI", "intelligence analyst"],
            "sources": sources
            or ["insight_global", "teksystems", "apex", "clearancejobs"],
            "max_results": max_results,
            "triggered_by": "dify",
        }
        return await self.trigger_workflow("job_scraper", payload)

    async def trigger_job_enrichment(
        self, job_ids: List[str] = None, enrich_all_pending: bool = False
    ) -> WorkflowTriggerResult:
        """
        Trigger AI enrichment for jobs.

        Uses: PTS_BD_WF2_AI_Enrichment_Processor

        Args:
            job_ids: Specific job IDs to enrich
            enrich_all_pending: Process all pending jobs

        Returns:
            Trigger result
        """
        payload = {
            "job_ids": job_ids,
            "enrich_all_pending": enrich_all_pending,
            "triggered_by": "dify",
        }
        return await self.trigger_workflow("job_enrichment", payload)

    async def trigger_contact_classification(
        self, contact_ids: List[str] = None, company_filter: str = None
    ) -> WorkflowTriggerResult:
        """
        Trigger contact classification (OrgChart tier assignment).

        Uses: PTS_BD_WF4_Contact_Classification

        Args:
            contact_ids: Specific contact IDs to classify
            company_filter: Filter contacts by company

        Returns:
            Trigger result
        """
        payload = {
            "contact_ids": contact_ids,
            "company_filter": company_filter,
            "triggered_by": "dify",
        }
        return await self.trigger_workflow("contact_classification", payload)

    async def trigger_hot_lead_alert(
        self, lead_data: Dict[str, Any]
    ) -> WorkflowTriggerResult:
        """
        Send hot lead alert notification.

        Uses: PTS_BD_WF5_Hot_Lead_Alerts

        Args:
            lead_data: Lead information including:
                - contact_name
                - company
                - program
                - score
                - reason

        Returns:
            Trigger result
        """
        payload = {
            **lead_data,
            "triggered_by": "dify",
            "triggered_at": datetime.now().isoformat(),
        }
        return await self.trigger_workflow("hot_lead_alert", payload)

    async def trigger_weekly_report(
        self, recipients: List[str] = None, include_sections: List[str] = None
    ) -> WorkflowTriggerResult:
        """
        Generate and send weekly BD intelligence report.

        Uses: PTS_BD_WF6_Weekly_Summary_Report

        Args:
            recipients: Email addresses for report delivery
            include_sections: Sections to include (hot_leads, new_jobs, opportunities)

        Returns:
            Trigger result
        """
        payload = {
            "recipients": recipients,
            "include_sections": include_sections
            or ["hot_leads", "new_jobs", "opportunities", "actions"],
            "triggered_by": "dify",
        }
        return await self.trigger_workflow("weekly_report", payload)

    async def trigger_clearance_rag(
        self, query: str, clearance_level: str = None
    ) -> WorkflowTriggerResult:
        """
        Query clearance jobs via RAG agent.

        Uses: Clearance_Job_RAG_Agent

        Args:
            query: Natural language query about clearance jobs
            clearance_level: Filter by clearance (TS/SCI, Secret, etc.)

        Returns:
            Trigger result with RAG response
        """
        payload = {
            "query": query,
            "clearance_level": clearance_level,
            "triggered_by": "dify",
        }
        return await self.trigger_workflow("clearance_rag", payload)

    async def trigger_firecrawl_search(
        self, search_query: str, target_sites: List[str] = None
    ) -> WorkflowTriggerResult:
        """
        Run Firecrawl web search agent.

        Uses: Firecrawl_Search_Agent

        Args:
            search_query: Search query
            target_sites: Sites to search (competitor sites, news, etc.)

        Returns:
            Trigger result with search results
        """
        payload = {
            "query": search_query,
            "target_sites": target_sites,
            "triggered_by": "dify",
        }
        return await self.trigger_workflow("firecrawl_search", payload)

    async def trigger_master_pipeline(
        self, pipeline_stage: str = "full", options: Dict[str, Any] = None
    ) -> WorkflowTriggerResult:
        """
        Trigger master BD orchestration pipeline.

        Uses: BD_Master_Orchestration_Workflow

        Args:
            pipeline_stage: Which stage to run (scrape, enrich, score, full)
            options: Additional pipeline options

        Returns:
            Trigger result
        """
        payload = {
            "stage": pipeline_stage,
            "options": options or {},
            "triggered_by": "dify",
        }
        return await self.trigger_workflow("master_pipeline", payload)

    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """
        Get list of available workflows for Dify tool registration.

        Returns workflow metadata in format suitable for Dify.
        """
        return [
            {
                "name": "job_scraper",
                "description": "Scrape jobs from ClearanceJobs, LinkedIn, and competitor sites using Apify",
                "file": self.WORKFLOW_FILES.get("job_scraper"),
                "parameters": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Search keywords",
                    },
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Job sources to scrape",
                    },
                    "max_results": {"type": "integer", "default": 100},
                },
            },
            {
                "name": "job_enrichment",
                "description": "AI-powered job enrichment: program mapping, BD scoring, contact matching",
                "file": self.WORKFLOW_FILES.get("job_enrichment"),
                "parameters": {
                    "job_ids": {"type": "array", "items": {"type": "string"}},
                    "enrich_all_pending": {"type": "boolean", "default": False},
                },
            },
            {
                "name": "contact_classification",
                "description": "Classify contacts into OrgChart tiers (Tier 1-6) based on role and influence",
                "file": self.WORKFLOW_FILES.get("contact_classification"),
                "parameters": {
                    "contact_ids": {"type": "array", "items": {"type": "string"}},
                    "company_filter": {"type": "string"},
                },
            },
            {
                "name": "hot_lead_alert",
                "description": "Send real-time alerts for hot BD leads (score >= 80)",
                "file": self.WORKFLOW_FILES.get("hot_lead_alert"),
                "parameters": {
                    "contact_name": {"type": "string", "required": True},
                    "company": {"type": "string"},
                    "program": {"type": "string"},
                    "score": {"type": "integer"},
                    "reason": {"type": "string"},
                },
            },
            {
                "name": "weekly_report",
                "description": "Generate and distribute weekly BD intelligence report",
                "file": self.WORKFLOW_FILES.get("weekly_report"),
                "parameters": {
                    "recipients": {"type": "array", "items": {"type": "string"}},
                    "include_sections": {"type": "array", "items": {"type": "string"}},
                },
            },
            {
                "name": "clearance_rag",
                "description": "RAG-powered search across clearance job postings",
                "file": self.WORKFLOW_FILES.get("clearance_rag"),
                "parameters": {
                    "query": {"type": "string", "required": True},
                    "clearance_level": {"type": "string"},
                },
            },
            {
                "name": "firecrawl_search",
                "description": "Web search using Firecrawl for competitor intelligence",
                "file": self.WORKFLOW_FILES.get("firecrawl_search"),
                "parameters": {
                    "query": {"type": "string", "required": True},
                    "target_sites": {"type": "array", "items": {"type": "string"}},
                },
            },
            {
                "name": "master_pipeline",
                "description": "Master BD orchestration - runs full scrape->enrich->score->notify pipeline",
                "file": self.WORKFLOW_FILES.get("master_pipeline"),
                "parameters": {
                    "stage": {
                        "type": "string",
                        "enum": ["scrape", "enrich", "score", "full"],
                    },
                    "options": {"type": "object"},
                },
            },
        ]

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# FastAPI router for exposing n8n triggers to Dify
def create_dify_n8n_router():
    """
    Create a FastAPI router for Dify n8n integration.

    Add this to your api.py:
        from dify_integration.dify_n8n_bridge import create_dify_n8n_router
        app.include_router(create_dify_n8n_router(), prefix="/dify")
    """
    from fastapi import APIRouter, Query
    from dataclasses import asdict

    router = APIRouter(tags=["Dify n8n"])
    bridge = DifyN8NBridge()

    @router.get("/n8n/workflows")
    async def list_workflows():
        """List available n8n workflows for Dify."""
        return bridge.get_available_workflows()

    @router.post("/n8n/trigger/{workflow_key}")
    async def trigger_workflow(workflow_key: str, payload: Dict[str, Any] = None):
        """Trigger an n8n workflow from Dify."""
        result = await bridge.trigger_workflow(workflow_key, payload or {})
        return asdict(result)

    @router.post("/n8n/scrape-jobs")
    async def scrape_jobs(
        keywords: List[str] = Query(None), max_results: int = Query(100)
    ):
        """Trigger job scraping from Dify."""
        result = await bridge.trigger_job_scraper(
            keywords=keywords, max_results=max_results
        )
        return asdict(result)

    @router.post("/n8n/hot-lead")
    async def hot_lead_alert(lead_data: Dict[str, Any]):
        """Send hot lead alert from Dify."""
        result = await bridge.trigger_hot_lead_alert(lead_data)
        return asdict(result)

    @router.post("/n8n/weekly-report")
    async def weekly_report(recipients: List[str] = Query(None)):
        """Trigger weekly report from Dify."""
        result = await bridge.trigger_weekly_report(recipients=recipients)
        return asdict(result)

    return router
