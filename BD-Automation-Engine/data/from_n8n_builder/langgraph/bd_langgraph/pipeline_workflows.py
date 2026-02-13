"""
WEEKLY PIPELINE WORKFLOW
========================
Workflow graph for weekly opportunity discovery and reporting.

Pipeline: Scrape → Enrich → Score → Report
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from langgraph.graph import StateGraph, END

from .states import WorkflowStatus
from .checkpointer import get_checkpointer, CheckpointManager
from .nodes import (
    scrape_opportunities_node,
    enrich_opportunities,
    score_and_rank,
    generate_report,
)
from .edges import should_continue_enrichment, should_generate_pipeline_report

# Try to import logger
try:
    from src.utils import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def create_weekly_pipeline_graph(checkpointer=None):
    """
    Create the Weekly Pipeline workflow graph.

    Args:
        checkpointer: Optional LangGraph checkpointer for persistence.

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create graph with state schema
    workflow = StateGraph(dict)

    # Add nodes
    workflow.add_node("scrape", scrape_opportunities_node)
    workflow.add_node("enrich", enrich_opportunities)
    workflow.add_node("score", score_and_rank)
    workflow.add_node("report", generate_report)
    workflow.add_node("complete", lambda state: {
        **state,
        'status': WorkflowStatus.COMPLETED.value,
        'completed_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    })

    # Define the flow
    # Conditional: check if enrichment needed
    workflow.add_conditional_edges(
        "scrape",
        should_continue_enrichment,
        {
            "enrich": "enrich",
            "score": "score"
        }
    )

    workflow.add_edge("enrich", "score")

    # Conditional: generate report if opportunities found
    workflow.add_conditional_edges(
        "score",
        should_generate_pipeline_report,
        {
            "report": "report",
            "complete": "complete"
        }
    )

    # End states
    workflow.add_edge("report", END)
    workflow.add_edge("complete", END)

    # Set entry point
    workflow.set_entry_point("scrape")

    # Compile with checkpointer
    if checkpointer is None:
        checkpointer = get_checkpointer()

    return workflow.compile(checkpointer=checkpointer)


def run_weekly_pipeline_workflow(
    target_agencies: Optional[List[str]] = None,
    target_naics: Optional[List[str]] = None,
    target_psc: Optional[List[str]] = None,
    min_value: float = 0.0,
    max_value: float = 0.0,
    date_range_days: int = 7,
    skip_enrichment: bool = False,
    skip_report: bool = False,
    score_criteria: Optional[Dict[str, float]] = None,
    checkpointer=None,
    thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the Weekly Pipeline workflow.

    Args:
        target_agencies: List of agency names/codes to filter
        target_naics: List of NAICS codes to filter
        target_psc: List of PSC codes to filter
        min_value: Minimum opportunity value
        max_value: Maximum opportunity value (0 = no limit)
        date_range_days: Number of days to look back
        skip_enrichment: If True, skip enrichment phase
        skip_report: If True, skip report generation
        score_criteria: Custom scoring weights
        checkpointer: Optional checkpointer
        thread_id: Optional thread ID

    Returns:
        Dictionary with workflow result and status
    """
    logger.info(f"Starting Weekly Pipeline workflow")

    # Generate workflow ID
    workflow_id = f"pipeline_{uuid.uuid4().hex[:8]}"
    thread_id = thread_id or f"thread_{workflow_id}"

    # Calculate date range
    to_date = datetime.now()
    from_date = to_date - timedelta(days=date_range_days)

    # Initialize state
    initial_state = {
        'workflow_id': workflow_id,
        'workflow_type': 'weekly_pipeline',
        'thread_id': thread_id,
        'status': WorkflowStatus.IN_PROGRESS.value,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'completed_nodes': [],

        # Input parameters
        'target_agencies': target_agencies or [],
        'target_naics': target_naics or [],
        'target_psc': target_psc or [],
        'min_value': min_value,
        'max_value': max_value,
        'date_range_days': date_range_days,

        # Date range for scraping
        'scrape_from_date': from_date.strftime('%Y-%m-%d'),
        'scrape_to_date': to_date.strftime('%Y-%m-%d'),

        # Processing options
        'skip_enrichment': skip_enrichment,
        'skip_report': skip_report,
        'score_criteria': score_criteria or {},

        # Initialize empty collections
        'raw_opportunities': [],
        'enriched_opportunities': [],
        'scored_opportunities': [],
        'top_opportunities': [],
        'weekly_report': {},
        'stats': {}
    }

    # Create graph
    graph = create_weekly_pipeline_graph(checkpointer)

    # Register workflow
    manager = CheckpointManager()
    manager.register_workflow(thread_id, 'weekly_pipeline', workflow_id)

    # Run workflow
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = graph.invoke(initial_state, config)

        manager.update_workflow_status(thread_id, WorkflowStatus.COMPLETED.value)
        return {
            'workflow_id': workflow_id,
            'thread_id': thread_id,
            'status': 'completed',
            'opportunities_found': result.get('opportunities_count', 0),
            'total_value': result.get('total_value', 0),
            'top_opportunities_count': len(result.get('top_opportunities', [])),
            'report_path': result.get('report_path'),
            'report_summary': result.get('report_summary'),
            'state': result
        }

    except Exception as e:
        manager.update_workflow_status(thread_id, WorkflowStatus.FAILED.value, str(e))
        logger.error(f"Workflow {workflow_id} failed: {e}")
        return {
            'workflow_id': workflow_id,
            'thread_id': thread_id,
            'status': 'failed',
            'error': str(e)
        }


def run_scheduled_weekly_pipeline(
    checkpointer=None
) -> Dict[str, Any]:
    """
    Run the weekly pipeline with default/configured settings.

    For use with scheduled execution (cron, N8N, etc.)

    Args:
        checkpointer: Optional checkpointer

    Returns:
        Dictionary with workflow results
    """
    # Load configuration from file if exists
    config = {}
    try:
        from pathlib import Path
        import json

        config_path = Path(__file__).parent.parent / "data" / "pipeline_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
    except Exception as e:
        logger.warning(f"Could not load pipeline config: {e}")

    # Use defaults from settings if available
    try:
        from src.config import settings
        target_naics = list(settings.TARGET_NAICS_CODES)
    except ImportError:
        target_naics = config.get('target_naics', [])

    return run_weekly_pipeline_workflow(
        target_agencies=config.get('target_agencies'),
        target_naics=target_naics,
        target_psc=config.get('target_psc'),
        min_value=config.get('min_value', 1_000_000),  # $1M default minimum
        date_range_days=config.get('date_range_days', 7),
        checkpointer=checkpointer
    )


def configure_weekly_pipeline(
    target_agencies: Optional[List[str]] = None,
    target_naics: Optional[List[str]] = None,
    target_psc: Optional[List[str]] = None,
    min_value: float = 1_000_000,
    date_range_days: int = 7
) -> bool:
    """
    Configure the weekly pipeline for scheduled runs.

    Args:
        target_agencies: List of agency names/codes
        target_naics: List of NAICS codes
        target_psc: List of PSC codes
        min_value: Minimum opportunity value
        date_range_days: Days to look back

    Returns:
        True if configuration saved successfully
    """
    try:
        from pathlib import Path
        import json

        config_path = Path(__file__).parent.parent / "data" / "pipeline_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config = {
            'target_agencies': target_agencies or [],
            'target_naics': target_naics or [],
            'target_psc': target_psc or [],
            'min_value': min_value,
            'date_range_days': date_range_days,
            'updated_at': datetime.now().isoformat()
        }

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved pipeline configuration to {config_path}")
        return True

    except Exception as e:
        logger.error(f"Error saving pipeline config: {e}")
        return False


def get_recent_pipeline_reports(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent pipeline workflow results.

    Args:
        limit: Maximum number of results

    Returns:
        List of recent pipeline run summaries
    """
    manager = CheckpointManager()
    workflows = manager.list_workflows(
        workflow_type='weekly_pipeline',
        limit=limit
    )

    return [
        {
            'workflow_id': w.get('workflow_id'),
            'thread_id': w.get('thread_id'),
            'status': w.get('status'),
            'created_at': w.get('created_at'),
            'completed_at': w.get('completed_at')
        }
        for w in workflows
    ]


# Export
__all__ = [
    'create_weekly_pipeline_graph',
    'run_weekly_pipeline_workflow',
    'run_scheduled_weekly_pipeline',
    'configure_weekly_pipeline',
    'get_recent_pipeline_reports',
]
