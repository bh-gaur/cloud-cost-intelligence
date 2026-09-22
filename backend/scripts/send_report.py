#!/usr/bin/env python3
"""
send_report.py
CLI tool to dispatch generated cost reports and KPI summaries to Slack, Teams, GChat, or Email.

Usage:
    python send_report.py --channel slack --dry-run
    python send_report.py --channel email --report-file backend/reports/html/aws-cost-report.html
"""

import argparse
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.notifications.service import NotificationService
from app.services.cost_service import CostService
from app.providers.factory import get_cloud_provider


def main():
    parser = argparse.ArgumentParser(description="Dispatch cost reports to notification channels.")
    parser.add_argument(
        "--channel",
        choices=["email", "slack", "teams", "google_chat", "all"],
        default="slack",
    )
    parser.add_argument("--report-file", default=None, help="Optional path to report attachment")
    parser.add_argument("--dry-run", action="store_true", help="Simulate send without actual network call")

    args = parser.parse_args()
    db = SessionLocal()

    try:
        provider = get_cloud_provider()
        cost_service = CostService(provider)
        summary = cost_service.get_dashboard_summary(db)
        kpis = cost_service.get_finops_kpis(db)

        payload = {
            "today_cost": f"{summary.today_cost:,.2f}",
            "yesterday_cost": f"{summary.yesterday_cost:,.2f}",
            "difference": f"{summary.today_vs_yesterday.difference:,.2f}",
            "percentage_change": f"{summary.today_vs_yesterday.percentage_change:.1f}",
            "top_service": kpis.top_service,
            "potential_monthly_savings": f"{kpis.potential_monthly_savings:,.2f}",
            "subject": f"AWS Cost Intelligence Daily Summary - ${summary.today_cost:,.2f}",
            "html_body": f"<h2>AWS Cost Intelligence Daily Report</h2><p>Today's Spend: <strong>${summary.today_cost:,.2f}</strong> ({summary.today_vs_yesterday.percentage_change:+.1f}%)</p><p>Top Cost Driver: <strong>{kpis.top_service}</strong></p><p>Potential Monthly Savings: <strong>${kpis.potential_monthly_savings:,.2f}</strong></p>",
        }

        notif_service = NotificationService()

        if args.dry_run:
            print("[*] DRY RUN MODE: Validating channel readiness...")
            health = notif_service.test_connection(args.channel if args.channel != "all" else "slack")
            print(f"    Channel '{args.channel}' status:", health)
            print("    Payload prepared:", payload)
            return

        print(f"[*] Dispatching report payload to channel: {args.channel}...")
        results = notif_service.dispatch(args.channel, payload, attachment_path=args.report_file)
        for ch, success in results.items():
            status_icon = "✓" if success else "✗"
            print(f"    [{status_icon}] {ch.upper()}: {'Sent successfully' if success else 'Failed / Not configured'}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

