"""Phase 58A — PWA API.

10 endpoints for PWA management, push notifications,
offline sync, and responsive API adaptation.
"""

from __future__ import annotations

from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter()


# =========================================
# REQUEST MODELS
# =========================================

class SubscribeRequest(BaseModel):
    user_id: str
    endpoint: str = ""
    topics: List[str] = []


class SendNotificationRequest(BaseModel):
    title: str
    body: str = ""
    topic: str = "system_alert"
    priority: str = "normal"
    target_user_id: Optional[str] = None


class QueueSyncRequest(BaseModel):
    action: str
    payload: Dict[str, Any] = {}


class DetectClientRequest(BaseModel):
    user_agent: str = ""
    screen_width: int = 0
    network_hint: str = ""


# =========================================
# PWA ENDPOINTS
# =========================================

@router.get("/api/pwa/manifest")
def get_manifest():
    """Get the PWA web app manifest."""
    from src.pwa.pwa_manager import get_pwa_manager
    mgr = get_pwa_manager()
    return mgr.get_manifest().to_dict()


@router.get("/api/pwa/resources")
def list_resources():
    """List offline-cached resources."""
    from src.pwa.pwa_manager import get_pwa_manager
    mgr = get_pwa_manager()
    resources = mgr.list_resources()
    return {"resources": [r.to_dict() for r in resources], "total": len(resources)}


@router.post("/api/pwa/sync")
def queue_sync(req: QueueSyncRequest):
    """Queue an offline action for sync."""
    from src.pwa.pwa_manager import get_pwa_manager
    mgr = get_pwa_manager()
    item = mgr.queue_sync(req.action, req.payload)
    return item.to_dict()


@router.post("/api/pwa/sync/process")
def process_sync():
    """Process all pending sync items."""
    from src.pwa.pwa_manager import get_pwa_manager
    mgr = get_pwa_manager()
    return mgr.process_sync_queue()


# =========================================
# PUSH NOTIFICATION ENDPOINTS
# =========================================

@router.post("/api/pwa/notifications/subscribe")
def subscribe(req: SubscribeRequest):
    """Subscribe to push notifications."""
    from src.pwa.push_notifications import get_push_service
    svc = get_push_service()
    sub = svc.subscribe(user_id=req.user_id, endpoint=req.endpoint, topics=req.topics or None)
    return sub.to_dict()


@router.post("/api/pwa/notifications/send")
def send_notification(req: SendNotificationRequest):
    """Send a push notification."""
    from src.pwa.push_notifications import get_push_service, NotificationTopic, NotificationPriority
    svc = get_push_service()
    topic_map = {t.value: t for t in NotificationTopic}
    priority_map = {p.value: p for p in NotificationPriority}
    notif = svc.send(
        title=req.title,
        body=req.body,
        topic=topic_map.get(req.topic, NotificationTopic.SYSTEM_ALERT),
        priority=priority_map.get(req.priority, NotificationPriority.NORMAL),
        target_user_id=req.target_user_id,
    )
    return notif.to_dict()


@router.get("/api/pwa/notifications/templates")
def list_templates():
    """List notification templates."""
    from src.pwa.push_notifications import get_push_service
    svc = get_push_service()
    templates = svc.list_templates()
    return {"templates": templates, "total": len(templates)}


# =========================================
# RESPONSIVE API ENDPOINTS
# =========================================

@router.post("/api/pwa/detect-client")
def detect_client(req: DetectClientRequest):
    """Detect client capabilities."""
    from src.pwa.responsive_api import get_responsive_api
    api = get_responsive_api()
    profile = api.detect_client(
        user_agent=req.user_agent,
        screen_width=req.screen_width,
        network_hint=req.network_hint,
    )
    return profile.to_dict()


# =========================================
# HEALTH
# =========================================

@router.get("/api/pwa/health")
def pwa_health():
    """PWA subsystem health check."""
    from src.pwa.pwa_manager import get_pwa_manager
    from src.pwa.push_notifications import get_push_service
    from src.pwa.responsive_api import get_responsive_api

    return {
        "status": "healthy",
        "pwa": get_pwa_manager().get_stats(),
        "notifications": get_push_service().get_stats(),
        "responsive_api": get_responsive_api().get_stats(),
    }


# =========================================
# ROUTER REGISTRATION
# =========================================

def include_pwa_router(app: FastAPI) -> None:
    app.include_router(router)
