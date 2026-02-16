"""Phase 58A — Push Notification Service.

Web Push notification management with subscription handling,
topic-based routing, delivery tracking, and notification templates.
"""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================


class NotificationPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    CLICKED = "clicked"
    DISMISSED = "dismissed"
    FAILED = "failed"


class NotificationTopic(Enum):
    PIPELINE_COMPLETE = "pipeline_complete"
    NEW_CONTACT = "new_contact"
    SCORE_ALERT = "score_alert"
    PROGRAM_UPDATE = "program_update"
    SYSTEM_ALERT = "system_alert"
    TASK_ASSIGNED = "task_assigned"


@dataclass
class PushSubscription:
    """A browser push subscription endpoint."""

    subscription_id: str
    user_id: str
    endpoint: str = ""
    topics: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subscription_id": self.subscription_id,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "topics": self.topics,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "enabled": self.enabled,
        }


@dataclass
class Notification:
    """A push notification with delivery tracking."""

    notification_id: str
    title: str
    body: str = ""
    topic: NotificationTopic = NotificationTopic.SYSTEM_ALERT
    priority: NotificationPriority = NotificationPriority.NORMAL
    status: NotificationStatus = NotificationStatus.PENDING
    target_user_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    delivered_at: float = 0.0
    clicked_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "title": self.title,
            "body": self.body,
            "topic": self.topic.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "target_user_id": self.target_user_id,
            "data": self.data,
            "created_at": self.created_at,
            "delivered_at": self.delivered_at,
            "clicked_at": self.clicked_at,
        }


# =========================================
# PRE-BUILT TEMPLATES
# =========================================

_NOTIFICATION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "pipeline_complete": {
        "title": "Pipeline Complete",
        "body": "BD pipeline processing finished successfully",
        "topic": NotificationTopic.PIPELINE_COMPLETE,
        "priority": NotificationPriority.NORMAL,
    },
    "high_score_alert": {
        "title": "High BD Score Detected",
        "body": "A new opportunity scored above 80/100",
        "topic": NotificationTopic.SCORE_ALERT,
        "priority": NotificationPriority.HIGH,
    },
    "new_tier1_contact": {
        "title": "New Tier 1 Contact",
        "body": "A new Tier 1 decision maker has been identified",
        "topic": NotificationTopic.NEW_CONTACT,
        "priority": NotificationPriority.HIGH,
    },
    "program_status_change": {
        "title": "Program Status Change",
        "body": "A tracked program has changed status",
        "topic": NotificationTopic.PROGRAM_UPDATE,
        "priority": NotificationPriority.NORMAL,
    },
    "system_maintenance": {
        "title": "System Maintenance",
        "body": "Scheduled maintenance window approaching",
        "topic": NotificationTopic.SYSTEM_ALERT,
        "priority": NotificationPriority.LOW,
    },
}


# =========================================
# PUSH NOTIFICATION SERVICE
# =========================================


class PushNotificationService:
    """Manages push notification subscriptions, delivery,
    and template-based notifications.
    """

    def __init__(self):
        self._subscriptions: Dict[str, PushSubscription] = {}
        self._notifications: List[Notification] = []
        self._templates = dict(_NOTIFICATION_TEMPLATES)
        logger.info(
            "PushNotificationService initialized with %d templates",
            len(self._templates),
        )

    # ----- subscriptions -----

    def subscribe(
        self, user_id: str, endpoint: str = "", topics: Optional[List[str]] = None
    ) -> PushSubscription:
        sub_id = (
            f"sub_{hashlib.md5(f'{user_id}:{time.time()}'.encode()).hexdigest()[:12]}"
        )
        sub = PushSubscription(
            subscription_id=sub_id,
            user_id=user_id,
            endpoint=endpoint or f"https://push.example.com/{sub_id}",
            topics=topics or [t.value for t in NotificationTopic],
        )
        self._subscriptions[sub_id] = sub
        logger.info("User %s subscribed: %s", user_id, sub_id)
        return sub

    def unsubscribe(self, subscription_id: str) -> bool:
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
            return True
        return False

    def get_subscription(self, subscription_id: str) -> Optional[PushSubscription]:
        return self._subscriptions.get(subscription_id)

    def list_subscriptions(
        self, user_id: Optional[str] = None
    ) -> List[PushSubscription]:
        subs = list(self._subscriptions.values())
        if user_id:
            subs = [s for s in subs if s.user_id == user_id]
        return subs

    # ----- send notifications -----

    def send(
        self,
        title: str,
        body: str = "",
        topic: NotificationTopic = NotificationTopic.SYSTEM_ALERT,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        target_user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Send a push notification."""
        notif = Notification(
            notification_id=f"notif_{uuid.uuid4().hex[:12]}",
            title=title,
            body=body,
            topic=topic,
            priority=priority,
            target_user_id=target_user_id,
            data=data or {},
        )

        # Simulate delivery
        matching_subs = self._get_matching_subscriptions(topic, target_user_id)
        if matching_subs:
            notif.status = NotificationStatus.DELIVERED
            notif.delivered_at = time.time()
        else:
            notif.status = NotificationStatus.FAILED

        self._notifications.append(notif)
        logger.info(
            "Sent notification %s to %d subscribers",
            notif.notification_id,
            len(matching_subs),
        )
        return notif

    def send_from_template(
        self,
        template_key: str,
        target_user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Notification]:
        """Send a notification from a pre-built template."""
        tpl = self._templates.get(template_key)
        if not tpl:
            return None
        return self.send(
            title=tpl["title"],
            body=tpl["body"],
            topic=tpl["topic"],
            priority=tpl["priority"],
            target_user_id=target_user_id,
            data=data,
        )

    def _get_matching_subscriptions(
        self, topic: NotificationTopic, target_user_id: Optional[str]
    ) -> List[PushSubscription]:
        subs = []
        for sub in self._subscriptions.values():
            if not sub.enabled:
                continue
            if target_user_id and sub.user_id != target_user_id:
                continue
            if topic.value in sub.topics:
                subs.append(sub)
        return subs

    # ----- queries -----

    def get_notification(self, notification_id: str) -> Optional[Notification]:
        for n in self._notifications:
            if n.notification_id == notification_id:
                return n
        return None

    def list_notifications(
        self, user_id: Optional[str] = None, limit: int = 50
    ) -> List[Notification]:
        notifs = self._notifications
        if user_id:
            notifs = [n for n in notifs if n.target_user_id == user_id]
        return notifs[-limit:]

    def list_templates(self) -> Dict[str, Dict[str, Any]]:
        return {
            key: {
                "title": t["title"],
                "body": t["body"],
                "topic": t["topic"].value,
                "priority": t["priority"].value,
            }
            for key, t in self._templates.items()
        }

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        delivered = sum(
            1 for n in self._notifications if n.status == NotificationStatus.DELIVERED
        )
        failed = sum(
            1 for n in self._notifications if n.status == NotificationStatus.FAILED
        )
        return {
            "total_subscriptions": len(self._subscriptions),
            "total_notifications": len(self._notifications),
            "delivered": delivered,
            "failed": failed,
            "templates_available": len(self._templates),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[PushNotificationService] = None


def get_push_service() -> PushNotificationService:
    global _instance
    if _instance is None:
        _instance = PushNotificationService()
    return _instance
