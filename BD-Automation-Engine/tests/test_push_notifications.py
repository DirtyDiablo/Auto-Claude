"""Tests for Phase 58A — Push Notification Service."""

import pytest

from src.pwa.push_notifications import (
    PushNotificationService,
    NotificationTopic,
    NotificationPriority,
    NotificationStatus,
    get_push_service,
)


@pytest.fixture
def svc():
    return PushNotificationService()


# =========================================
# SUBSCRIPTIONS
# =========================================

def test_subscribe(svc):
    sub = svc.subscribe("user1")
    assert sub.subscription_id.startswith("sub_")
    assert sub.user_id == "user1"


def test_subscribe_with_topics(svc):
    sub = svc.subscribe("user1", topics=["score_alert", "new_contact"])
    assert len(sub.topics) == 2


def test_unsubscribe(svc):
    sub = svc.subscribe("user1")
    result = svc.unsubscribe(sub.subscription_id)
    assert result is True


def test_unsubscribe_not_found(svc):
    assert svc.unsubscribe("sub_fake") is False


def test_list_subscriptions(svc):
    svc.subscribe("user1")
    svc.subscribe("user2")
    subs = svc.list_subscriptions()
    assert len(subs) == 2


def test_list_by_user(svc):
    svc.subscribe("user1")
    svc.subscribe("user2")
    subs = svc.list_subscriptions(user_id="user1")
    assert len(subs) == 1


# =========================================
# SEND NOTIFICATIONS
# =========================================

def test_send_with_subscriber(svc):
    svc.subscribe("user1")
    notif = svc.send("Test Title", "Test Body", target_user_id="user1")
    assert notif.status == NotificationStatus.DELIVERED


def test_send_no_subscriber(svc):
    notif = svc.send("Test", "No one listening")
    assert notif.status == NotificationStatus.FAILED


def test_send_with_topic(svc):
    svc.subscribe("user1", topics=["score_alert"])
    notif = svc.send("Score!", topic=NotificationTopic.SCORE_ALERT)
    assert notif.status == NotificationStatus.DELIVERED


def test_send_wrong_topic(svc):
    svc.subscribe("user1", topics=["score_alert"])
    notif = svc.send("Pipeline Done", topic=NotificationTopic.PIPELINE_COMPLETE)
    assert notif.status == NotificationStatus.FAILED


def test_notification_to_dict(svc):
    svc.subscribe("user1")
    notif = svc.send("Test", target_user_id="user1")
    d = notif.to_dict()
    assert "notification_id" in d
    assert "title" in d
    assert "status" in d


# =========================================
# TEMPLATES
# =========================================

def test_send_from_template(svc):
    svc.subscribe("user1")
    notif = svc.send_from_template("high_score_alert", target_user_id="user1")
    assert notif is not None
    assert notif.title == "High BD Score Detected"


def test_send_from_unknown_template(svc):
    notif = svc.send_from_template("nonexistent")
    assert notif is None


def test_list_templates(svc):
    templates = svc.list_templates()
    assert len(templates) == 5
    assert "pipeline_complete" in templates


# =========================================
# QUERIES
# =========================================

def test_list_notifications(svc):
    svc.subscribe("user1")
    svc.send("N1", target_user_id="user1")
    svc.send("N2", target_user_id="user1")
    notifs = svc.list_notifications()
    assert len(notifs) == 2


def test_get_notification(svc):
    svc.subscribe("user1")
    notif = svc.send("Test", target_user_id="user1")
    found = svc.get_notification(notif.notification_id)
    assert found is not None


def test_get_notification_not_found(svc):
    assert svc.get_notification("notif_fake") is None


# =========================================
# STATS & SINGLETON
# =========================================

def test_stats(svc):
    svc.subscribe("user1")
    svc.send("Test", target_user_id="user1")
    stats = svc.get_stats()
    assert stats["total_subscriptions"] == 1
    assert stats["total_notifications"] == 1


def test_subscription_to_dict(svc):
    sub = svc.subscribe("user1")
    d = sub.to_dict()
    assert "subscription_id" in d
    assert "user_id" in d


def test_singleton():
    import src.pwa.push_notifications as mod
    mod._instance = None
    a1 = get_push_service()
    a2 = get_push_service()
    assert a1 is a2
    mod._instance = None
