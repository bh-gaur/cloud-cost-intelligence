"""
Microsoft Teams Notification Provider
Formats and posts Adaptive Cards v1.4 to Microsoft Teams incoming webhook.
"""

import json
import logging
import urllib.request
from typing import Any, Dict, Optional
from app.config.settings import settings
from app.notifications.base import NotificationProvider

logger = logging.getLogger(__name__)


class TeamsNotificationProvider(NotificationProvider):
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.TEAMS_WEBHOOK_URL

    def get_channel_name(self) -> str:
        return "teams"

    def validate_configuration(self) -> bool:
        return bool(self.webhook_url and ("office.com" in self.webhook_url or "webhook.office" in self.webhook_url))

    def health_check(self) -> Dict[str, Any]:
        if not self.validate_configuration():
            return {"healthy": False, "message": "Microsoft Teams webhook URL not configured."}
        return {"healthy": True, "message": "Microsoft Teams webhook configured and ready."}

    def send(self, payload: Dict[str, Any], attachment_path: Optional[str] = None) -> bool:
        if not self.validate_configuration():
            logger.warning("Teams notification skipped: webhook URL not configured.")
            return False

        today_cost = payload.get("today_cost", "0.00")
        diff = payload.get("difference", "0.00")
        pct = payload.get("percentage_change", "0.00")
        savings = payload.get("potential_monthly_savings", "0.00")

        teams_payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "size": "Medium",
                                "weight": "Bolder",
                                "text": "☁️ AWS Cost Intelligence Summary",
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": "Today's Cost:", "value": f"${today_cost}"},
                                    {"title": "Cost Change:", "value": f"${diff} ({pct}%)"},
                                    {"title": "Potential Savings:", "value": f"${savings}/mo"},
                                ],
                            },
                        ],
                    },
                }
            ],
        }

        body = json.dumps(teams_payload).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 202):
                    logger.info("Teams notification dispatched successfully.")
                    return True
                return False
        except Exception as e:
            logger.error("Error sending Teams notification: %s", e)
            return False

