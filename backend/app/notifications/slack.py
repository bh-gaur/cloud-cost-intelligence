"""
Slack Notification Provider
Formats and posts rich Block Kit messages to Slack webhook URL.
"""

import json
import logging
import urllib.request
from typing import Any, Dict, Optional
from app.config.settings import settings
from app.notifications.base import NotificationProvider

logger = logging.getLogger(__name__)


class SlackNotificationProvider(NotificationProvider):
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.SLACK_WEBHOOK_URL

    def get_channel_name(self) -> str:
        return "slack"

    def validate_configuration(self) -> bool:
        return bool(self.webhook_url and self.webhook_url.startswith("https://hooks.slack.com/"))

    def health_check(self) -> Dict[str, Any]:
        if not self.validate_configuration():
            return {"healthy": False, "message": "Slack webhook URL not configured or invalid."}
        masked = self.webhook_url[:30] + "..." if self.webhook_url else "None"
        return {"healthy": True, "message": f"Slack webhook ready ({masked})"}

    @staticmethod
    def build_anomaly_blocks(payload: Dict[str, Any]) -> list:
        """Builds Block Kit layout for spend anomalies and cost spikes."""
        anomalies = payload.get("anomalies", [])
        total_count = payload.get("anomalies_count", len(anomalies))
        critical_count = payload.get("critical_count", 0)
        org_name = payload.get("org_name", "Your Organization")
        header_text = "🚨 Critical Cloud Cost Spike Detected" if critical_count > 0 else "⚠️ Cloud Cost Anomaly Detected"

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{header_text}", "emoji": True},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Organization:* `{org_name}`\n"
                        f"*Incidents Flagged:* *{total_count}* ({critical_count} Critical)\n"
                        f"*Detection Mode:* Rolling 7-day Statistical Z-score & Cost Baseline"
                    ),
                },
            },
            {"type": "divider"},
        ]

        # Add top incidents
        for a in anomalies[:4]:
            sev_emoji = "🔴" if a.get("severity") == "CRITICAL" else "🟡"
            detected_cost = a.get("detected_value", 0.0)
            expected_cost = a.get("expected_value", 0.0)
            dev_pct = a.get("difference_percentage", 0.0)
            dev_str = f"+{dev_pct:.1f}%" if dev_pct else "Surge"

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"{sev_emoji} *[{a.get('severity', 'WARNING')}] {a.get('title', 'Cost Spike')}*\n"
                        f"• *Service:* `{a.get('service', 'AWS Service')}` | *Account:* `{a.get('account_id', 'AWS Account')}`\n"
                        f"• *Detected Spend:* `${detected_cost:,.2f}` (Baseline: `${expected_cost:,.2f}` | *{dev_str}*)\n"
                        f"• *Cause:* _{a.get('message', 'Unusual consumption pattern')}_"
                    ),
                },
            })

        if total_count > 4:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_...plus {total_count - 4} additional spend deviations recorded in the dashboard._",
                    }
                ],
            })

        blocks.append({"type": "divider"})
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "📊 Review in FinOps Dashboard", "emoji": True},
                    "style": "primary",
                    "url": "http://localhost:5173/alerts",
                }
            ],
        })

        return blocks

    @staticmethod
    def build_test_blocks(payload: Dict[str, Any]) -> list:
        """Builds Block Kit layout for testing the integration."""
        org_name = payload.get("org_name", "Cloud Cost Intelligence")
        timestamp = payload.get("timestamp", "")
        return [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🟢 FinOps Alert Channel Connected", "emoji": True},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"This is a test notification confirming your *Slack Webhook Channel* is active and verified for *{org_name}*.\n\n"
                        f"• *Status:* `ACTIVE & HEALTHY`\n"
                        f"• *Event Subscriptions:* Spend Anomalies, Budget Breaches, Daily FinOps Rollups\n"
                        f"• *Timestamp:* `{timestamp}`"
                    ),
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "AWS Cost Intelligence Platform • Real-time Automated Anomaly Detection",
                    }
                ],
            },
        ]

    def send(self, payload: Dict[str, Any], attachment_path: Optional[str] = None) -> bool:
        if not self.validate_configuration():
            logger.warning("Slack notification skipped: invalid or missing webhook URL.")
            return False

        # If payload already has custom blocks, use them
        if "blocks" in payload and isinstance(payload["blocks"], list):
            blocks = payload["blocks"]
        elif payload.get("event") == "ANOMALY_DETECTED":
            blocks = self.build_anomaly_blocks(payload)
        elif payload.get("event") == "TEST_ALERT":
            blocks = self.build_test_blocks(payload)
        elif "today_cost" in payload:
            today_cost = payload.get("today_cost", "0.00")
            yesterday_cost = payload.get("yesterday_cost", "0.00")
            diff = payload.get("difference", "0.00")
            pct = payload.get("percentage_change", "0.00")
            top_service = payload.get("top_service", "N/A")
            savings = payload.get("potential_monthly_savings", "0.00")

            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "☁️ AWS Cost Intelligence Daily Update", "emoji": True},
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Today's Spend:*\n${today_cost}"},
                        {"type": "mrkdwn", "text": f"*Yesterday's Spend:*\n${yesterday_cost}"},
                        {"type": "mrkdwn", "text": f"*Variance:*\n${diff} ({pct}%)"},
                        {"type": "mrkdwn", "text": f"*Top Cost Driver:*\n{top_service}"},
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"💡 *FinOps Optimization:* Potential monthly savings of *${savings}* detected across idle/oversized resources.",
                    },
                },
            ]
        else:
            # Fallback simple text block
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": payload.get("text", "AWS Cost Intelligence Notification"),
                    },
                }
            ]

        body = json.dumps({
            "text": payload.get("text", "AWS Cost Intelligence Notification"),
            "blocks": blocks,
        }).encode("utf-8")

        req = urllib.request.Request(
            self.webhook_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201, 204):
                    logger.info("Slack notification dispatched successfully.")
                    return True
                logger.error("Slack webhook returned unexpected status %s", resp.status)
                return False
        except Exception as e:
            logger.error("Error posting to Slack webhook: %s", e)
            return False
