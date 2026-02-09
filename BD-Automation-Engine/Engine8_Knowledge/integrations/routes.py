"""
Integration API Routes — FastAPI router for Slack and CRM sync endpoints.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["Integrations"])


# ─── Request Models ─────────────────────────────────────────────────────────

class SlackNotifyRequest(BaseModel):
    channel: str = "#bd-alerts"
    message: str
    blocks: Optional[List[Dict[str, Any]]] = None


class SlackCommandRequest(BaseModel):
    command: str
    text: str = ""
    user_id: Optional[str] = None
    channel_id: Optional[str] = None


class ContactUpdateRequest(BaseModel):
    contacts: List[Dict[str, Any]]


# ─── Slack Endpoints ────────────────────────────────────────────────────────

@router.post("/slack/notify")
async def slack_notify(request: SlackNotifyRequest):
    """Send a notification to a Slack channel."""
    from Engine8_Knowledge.integrations.slack_integration import get_slack_bot

    bot = get_slack_bot()
    result = bot.send_notification(
        channel=request.channel,
        message=request.message,
        blocks=request.blocks,
    )
    return result


@router.post("/slack/digest")
async def slack_digest(channel: str = Query("#bd-daily", description="Target channel")):
    """Trigger daily digest to a Slack channel."""
    from Engine8_Knowledge.integrations.slack_integration import get_slack_bot

    bot = get_slack_bot()
    result = bot.send_daily_digest(channel)
    return result


@router.post("/slack/hot-lead")
async def slack_hot_lead(
    channel: str = Query("#bd-alerts", description="Target channel"),
    contact_name: str = Query(..., description="Contact name"),
    reason: str = Query(..., description="Reason for alert"),
):
    """Send a hot lead alert to Slack."""
    from Engine8_Knowledge.integrations.slack_integration import get_slack_bot

    bot = get_slack_bot()
    contact = {"name": contact_name}  # Minimal; caller can provide more
    result = bot.send_hot_lead_alert(channel, contact, reason)
    return result


@router.get("/slack/status")
async def slack_status():
    """Get Slack bot connection status and message count."""
    from Engine8_Knowledge.integrations.slack_integration import get_slack_bot

    bot = get_slack_bot()
    return bot.get_status()


@router.post("/slack/command")
async def slack_command(request: SlackCommandRequest):
    """
    Slash command webhook receiver.

    Handles /bd-search, /bd-pipeline, /bd-signals commands.
    """
    from Engine8_Knowledge.integrations.slack_integration import get_slack_bot

    bot = get_slack_bot()
    result = bot.handle_command(request.command, request.text)
    return result


@router.get("/slack/notifications")
async def slack_notifications(limit: int = Query(50, description="Max entries to return")):
    """Get recent notifications from the JSONL fallback log."""
    from Engine8_Knowledge.integrations.slack_integration import get_slack_bot

    bot = get_slack_bot()
    return {"notifications": bot.get_recent_notifications(limit)}


# ─── CRM Sync Endpoints ─────────────────────────────────────────────────────

@router.post("/crm/sync")
async def crm_sync():
    """Trigger a full bidirectional CRM sync cycle."""
    from Engine8_Knowledge.integrations.crm_sync import get_crm_sync_manager

    manager = get_crm_sync_manager()
    result = manager.run_sync_cycle()
    return result


@router.get("/crm/status")
async def crm_status():
    """Get CRM sync health dashboard."""
    from Engine8_Knowledge.integrations.crm_sync import get_crm_sync_manager

    manager = get_crm_sync_manager()
    return manager.sync_status()


@router.get("/crm/queue")
async def crm_queue(limit: int = Query(50, description="Max items to return")):
    """Get pending CRM sync queue items."""
    from Engine8_Knowledge.integrations.crm_sync import get_crm_sync_manager

    manager = get_crm_sync_manager()
    items = manager.get_queue(limit)
    return {"queue": items, "count": len(items)}


@router.get("/crm/log")
async def crm_log(limit: int = Query(50, description="Max entries to return")):
    """Get recent CRM sync log entries."""
    from Engine8_Knowledge.integrations.crm_sync import get_crm_sync_manager

    manager = get_crm_sync_manager()
    entries = manager.get_sync_log(limit)
    return {"log": entries, "count": len(entries)}


@router.post("/crm/push-contacts")
async def crm_push_contacts(request: ContactUpdateRequest):
    """Queue contact classification updates for CRM push."""
    from Engine8_Knowledge.integrations.crm_sync import get_crm_sync_manager

    manager = get_crm_sync_manager()
    result = manager.push_contact_updates(request.contacts)
    return result


@router.post("/crm/pull-placements")
async def crm_pull_placements():
    """Pull new placements from Bullhorn."""
    from Engine8_Knowledge.integrations.crm_sync import get_crm_sync_manager

    manager = get_crm_sync_manager()
    result = manager.pull_new_placements()
    # Don't send full placement data, just count
    return {"success": result["success"], "count": result["count"], "error": result.get("error")}


@router.post("/crm/pull-activities")
async def crm_pull_activities():
    """Pull new activities from Bullhorn."""
    from Engine8_Knowledge.integrations.crm_sync import get_crm_sync_manager

    manager = get_crm_sync_manager()
    result = manager.pull_activity_updates()
    return {"success": result["success"], "count": result["count"], "error": result.get("error")}
