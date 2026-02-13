"""
RECOMPETE INTELLIGENCE WORKFLOW
================================
Workflow graph for monitoring contracts and detecting recompete opportunities.

Pipeline: Monitor → Detect → Alert → Capture
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from langgraph.graph import StateGraph, END

from .states import WorkflowStatus
from .checkpointer import get_checkpointer, CheckpointManager
from .nodes import (
    monitor_contracts,
    detect_recompete_signals_node,
    generate_alert,
    prepare_capture,
)
from .edges import should_generate_alert, should_prepare_capture

# Try to import logger
try:
    from src.utils import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def create_recompete_graph(checkpointer=None):
    """
    Create the Recompete Intelligence workflow graph.

    Args:
        checkpointer: Optional LangGraph checkpointer for persistence.

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create graph with state schema
    workflow = StateGraph(dict)

    # Add nodes
    workflow.add_node("monitor", monitor_contracts)
    workflow.add_node("detect", detect_recompete_signals_node)
    workflow.add_node("alert", generate_alert)
    workflow.add_node("capture", prepare_capture)
    workflow.add_node("complete", lambda state: {
        **state,
        'status': WorkflowStatus.COMPLETED.value,
        'completed_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    })

    # Define the flow
    workflow.add_edge("monitor", "detect")

    # Conditional: generate alerts if signals detected
    workflow.add_conditional_edges(
        "detect",
        should_generate_alert,
        {
            "generate_alert": "alert",
            "complete": "complete"
        }
    )

    # Conditional: prepare capture for high priority
    workflow.add_conditional_edges(
        "alert",
        should_prepare_capture,
        {
            "prepare": "capture",
            "skip": "complete"
        }
    )

    # End after capture or complete
    workflow.add_edge("capture", END)
    workflow.add_edge("complete", END)

    # Set entry point
    workflow.set_entry_point("monitor")

    # Compile with checkpointer
    if checkpointer is None:
        checkpointer = get_checkpointer()

    return workflow.compile(checkpointer=checkpointer)


def run_recompete_workflow(
    contract_ids: List[str],
    alert_threshold_days: int = 365,
    monitoring_criteria: Optional[Dict[str, Any]] = None,
    auto_prepare: bool = False,
    checkpointer=None,
    thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the Recompete Intelligence workflow.

    Args:
        contract_ids: List of contract IDs to monitor
        alert_threshold_days: Days until recompete to trigger alert
        monitoring_criteria: Additional monitoring filters
        auto_prepare: If True, auto-prepare capture for high priority
        checkpointer: Optional checkpointer
        thread_id: Optional thread ID

    Returns:
        Dictionary with workflow result and status
    """
    logger.info(f"Starting Recompete workflow for {len(contract_ids)} contracts")

    # Generate workflow ID
    workflow_id = f"recompete_{uuid.uuid4().hex[:8]}"
    thread_id = thread_id or f"thread_{workflow_id}"

    # Initialize state
    initial_state = {
        'workflow_id': workflow_id,
        'workflow_type': 'recompete_intelligence',
        'thread_id': thread_id,
        'status': WorkflowStatus.IN_PROGRESS.value,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'completed_nodes': [],

        # Input parameters
        'monitored_contracts': contract_ids,
        'alert_threshold_days': alert_threshold_days,
        'monitoring_criteria': monitoring_criteria or {},

        # Capture settings
        'capture_decisions': {cid: auto_prepare for cid in contract_ids},

        # Initialize empty collections
        'contract_statuses': [],
        'recompete_signals': [],
        'alerts_generated': [],
        'capture_plans': [],
        'stats': {}
    }

    # Create graph
    graph = create_recompete_graph(checkpointer)

    # Register workflow
    manager = CheckpointManager()
    manager.register_workflow(thread_id, 'recompete_intelligence', workflow_id)

    # Run workflow
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = graph.invoke(initial_state, config)

        manager.update_workflow_status(thread_id, WorkflowStatus.COMPLETED.value)
        return {
            'workflow_id': workflow_id,
            'thread_id': thread_id,
            'status': 'completed',
            'contracts_monitored': len(contract_ids),
            'signals_detected': len(result.get('recompete_signals', [])),
            'alerts_generated': len(result.get('alerts_generated', [])),
            'capture_plans_created': len(result.get('capture_plans', [])),
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


def run_scheduled_recompete_check(
    checkpointer=None
) -> Dict[str, Any]:
    """
    Run a scheduled recompete check (for cron/scheduled execution).

    Loads monitored contracts from configuration and runs the workflow.

    Args:
        checkpointer: Optional checkpointer

    Returns:
        Dictionary with workflow results
    """
    # Load monitored contracts from config/database
    # This is a placeholder - would load from actual configuration
    monitored_contracts = []

    try:
        # Load from data file if exists
        from pathlib import Path
        import json
        config_path = Path(__file__).parent.parent / "data" / "recompete_monitoring.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                monitored_contracts = config.get('contract_ids', [])
    except Exception as e:
        logger.error(f"Error loading recompete config: {e}")

    if not monitored_contracts:
        return {
            'status': 'skipped',
            'message': 'No contracts configured for monitoring'
        }

    return run_recompete_workflow(
        contract_ids=monitored_contracts,
        checkpointer=checkpointer
    )


def add_contract_to_monitoring(
    contract_id: str,
    alert_threshold_days: int = 365
) -> bool:
    """
    Add a contract to the monitoring list.

    Args:
        contract_id: Contract ID to monitor
        alert_threshold_days: Days threshold for alerts

    Returns:
        True if added successfully
    """
    try:
        from pathlib import Path
        import json

        config_path = Path(__file__).parent.parent / "data" / "recompete_monitoring.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing config
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {'contract_ids': [], 'thresholds': {}}

        # Add contract if not already monitored
        if contract_id not in config['contract_ids']:
            config['contract_ids'].append(contract_id)
            config['thresholds'][contract_id] = alert_threshold_days

            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info(f"Added contract {contract_id} to monitoring")
            return True

        return False

    except Exception as e:
        logger.error(f"Error adding contract to monitoring: {e}")
        return False


def remove_contract_from_monitoring(contract_id: str) -> bool:
    """
    Remove a contract from the monitoring list.

    Args:
        contract_id: Contract ID to remove

    Returns:
        True if removed successfully
    """
    try:
        from pathlib import Path
        import json

        config_path = Path(__file__).parent.parent / "data" / "recompete_monitoring.json"

        if not config_path.exists():
            return False

        with open(config_path, 'r') as f:
            config = json.load(f)

        if contract_id in config['contract_ids']:
            config['contract_ids'].remove(contract_id)
            config['thresholds'].pop(contract_id, None)

            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info(f"Removed contract {contract_id} from monitoring")
            return True

        return False

    except Exception as e:
        logger.error(f"Error removing contract from monitoring: {e}")
        return False


# Export
__all__ = [
    'create_recompete_graph',
    'run_recompete_workflow',
    'run_scheduled_recompete_check',
    'add_contract_to_monitoring',
    'remove_contract_from_monitoring',
]
