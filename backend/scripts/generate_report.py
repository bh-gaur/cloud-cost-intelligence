#!/usr/bin/env python3
"""
generate_report.py
CLI tool to compile and render executive cost reports in CSV, JSON, or HTML.

Usage:
    python generate_report.py --format html --start-date 2026-09-01 --end-date 2026-09-12
    python generate_report.py --cleanup --retention-days 90
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.reports.service import ReportService


def main():
    parser = argparse.ArgumentParser(description="Generate FinOps Cost Reports or purge old archives.")
    parser.add_argument("--format", choices=["csv", "json", "html", "pdf"], default="html")

    parser.add_argument("--start-date", type=date.fromisoformat, default=date.today() - timedelta(days=30))
    parser.add_argument("--end-date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--account", default="all", help="Target AWS Account ID or 'all'")
    parser.add_argument("--name", default=None, help="Custom report name")
    parser.add_argument("--cleanup", action="store_true", help="Execute 90-day retention cleanup")
    parser.add_argument("--retention-days", type=int, default=90)

    args = parser.parse_args()
    report_service = ReportService()
    db = SessionLocal()

    try:
        if args.cleanup:
            purged = report_service.cleanup_old_reports(db, retention_days=args.retention_days)
            print(f"[✓] Cleanup complete. Removed {purged} reports older than {args.retention_days} days.")
            return

        print(f"[*] Generating {args.format.upper()} report for {args.start_date} to {args.end_date}...")
        report = report_service.generate_report(
            db=db,
            fmt=args.format,
            start_date=args.start_date,
            end_date=args.end_date,
            account_id=args.account,
            custom_name=args.name,
        )

        print("[✓] Report successfully created:")
        print(f"    ID:       {report.id}")
        print(f"    Name:     {report.name}")
        print(f"    Format:   {report.format.upper()}")
        print(f"    Path:     {report.file_path}")
        print(f"    Size:     {report.file_size_bytes:,} bytes")
    finally:
        db.close()


if __name__ == "__main__":
    main()

