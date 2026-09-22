"""
Central Notification Dispatcher Service
Orchestrates outbound alerts to configured channels with zero secret leakage.
"""

import logging
from typing import Any, Dict, List, Optional
from app.notifications.base import NotificationProvider
from app.notifications.email import EmailNotificationProvider
from app.notifications.slack import SlackNotificationProvider
from app.notifications.google_chat import GoogleChatNotificationProvider
from app.notifications.teams import TeamsNotificationProvider

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.providers: Dict[str, NotificationProvider] = {
            "email": EmailNotificationProvider(),
            "slack": SlackNotificationProvider(),
            "google_chat": GoogleChatNotificationProvider(),
            "teams": TeamsNotificationProvider(),
        }

    def dispatch(
        self,
        channel: str,
        payload: Dict[str, Any],
        attachment_path: Optional[str] = None,
    ) -> Dict[str, bool]:
        """Dispatches payload to a specific channel or all configured channels."""
        results: Dict[str, bool] = {}

        if channel == "all":
            for name, prov in self.providers.items():
                if prov.validate_configuration():
                    results[name] = prov.send(payload, attachment_path)
                else:
                    results[name] = False
        elif channel in self.providers:
            prov = self.providers[channel]
            results[channel] = prov.send(payload, attachment_path)
        else:
            logger.warning("Unknown notification channel requested: %s", channel)
            results[channel] = False

        return results

    def test_connection(
        self, channel: str, custom_webhook: Optional[str] = None, recipient_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs a diagnostic test without sending external spam."""
        if channel == "slack":
            p = SlackNotificationProvider(webhook_url=custom_webhook)
            return p.health_check()
        elif channel == "teams":
            p = TeamsNotificationProvider(webhook_url=custom_webhook)
            return p.health_check()
        elif channel == "google_chat":
            p = GoogleChatNotificationProvider(webhook_url=custom_webhook)
            return p.health_check()
        elif channel == "email":
            p = EmailNotificationProvider()
            return p.health_check()

        return {"healthy": False, "message": f"Unsupported channel: {channel}"}

