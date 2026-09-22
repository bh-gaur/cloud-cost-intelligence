"""
Google Chat Notification Provider
Formats and posts Cards v2 payloads to Google Chat space incoming webhook.
"""

import json
import logging
import urllib.request
from typing import Any, Dict, Optional
from app.config.settings import settings
from app.notifications.base import NotificationProvider

logger = logging.getLogger(__name__)


class GoogleChatNotificationProvider(NotificationProvider):
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.GCHAT_WEBHOOK_URL

    def get_channel_name(self) -> str:
        return "google_chat"

    def validate_configuration(self) -> bool:
        return bool(self.webhook_url and "chat.googleapis.com" in self.webhook_url)

    def health_check(self) -> Dict[str, Any]:
        if not self.validate_configuration():
            return {"healthy": False, "message": "Google Chat webhook URL not configured."}
        return {"healthy": True, "message": "Google Chat webhook configured and ready."}

    def send(self, payload: Dict[str, Any], attachment_path: Optional[str] = None) -> bool:
        if not self.validate_configuration():
            logger.warning("Google Chat skipped: webhook URL not configured.")
            return False

        today_cost = payload.get("today_cost", "0.00")
        diff = payload.get("difference", "0.00")
        pct = payload.get("percentage_change", "0.00")
        savings = payload.get("potential_monthly_savings", "0.00")

        card_payload = {
            "cardsV2": [
                {
                    "cardId": "finops-daily-summary",
                    "card": {
                        "header": {
                            "title": "AWS Cost Intelligence",
                            "subtitle": "Daily Spend & Optimization Summary",
                        },
                        "sections": [
                            {
                                "header": "Spend Metrics",
                                "widgets": [
                                    {"decoratedText": {"topLabel": "Today's Cost", "text": f"${today_cost}"}},
                                    {"decoratedText": {"topLabel": "Variance", "text": f"${diff} ({pct}%)"}},
                                    {"decoratedText": {"topLabel": "Potential Savings", "text": f"${savings}/month"}},
                                ],
                            }
                        ],
                    },
                }
            ]
        }

        body = json.dumps(card_payload).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    logger.info("Google Chat notification dispatched.")
                    return True
                return False
        except Exception as e:
            logger.error("Error sending Google Chat notification: %s", e)
            return False

