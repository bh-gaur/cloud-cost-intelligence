"""
Tests for Notification Providers & Masking
"""

import pytest
from app.notifications.slack import SlackNotificationProvider
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

    email_health = svc.test_connection("email")
    assert "healthy" in email_health
    assert "message" in email_health

    # Unsupported channels should be rejected
    teams_health = svc.test_connection("teams")
    assert teams_health["healthy"] is False
    assert "Unsupported" in teams_health["message"]

