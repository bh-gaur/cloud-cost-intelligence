"""
Tests for Notification Providers & Masking
"""

import pytest
from app.notifications.slack import SlackNotificationProvider
from app.notifications.teams import TeamsNotificationProvider
from app.notifications.google_chat import GoogleChatNotificationProvider
from app.notifications.email import EmailNotificationProvider
from app.notifications.service import NotificationService


def test_slack_provider_validation():
    invalid_p = SlackNotificationProvider(webhook_url="http://invalid.com")
    assert invalid_p.validate_configuration() is False

    valid_p = SlackNotificationProvider(webhook_url="https://hooks.slack.com/services/T00/B00/X00")
    assert valid_p.validate_configuration() is True


def test_notification_service_health_check():
    svc = NotificationService()
    slack_health = svc.test_connection("slack")
    assert "healthy" in slack_health
    assert "message" in slack_health

