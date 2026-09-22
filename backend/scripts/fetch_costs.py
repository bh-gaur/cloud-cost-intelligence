#!/usr/bin/env python3
"""
fetch_costs.py
Standalone CLI to ingest and synchronize AWS cost data into PostgreSQL.

Usage:
    python fetch_costs.py --provider mock --start-date 2026-09-01 --end-date 2026-09-12
    python fetch_costs.py --provider aws --account 123456789012 --dry-run
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.providers.factory import get_cloud_provider
from app.services.cost_service import CostService
from app.models.organization import Organization


def main():
    parser = argparse.ArgumentParser(description="Fetch and synchronize cloud cost data.")
    parser.add_argument("--provider", choices=["aws", "mock"], default="mock", help="Cloud provider to query")
    parser.add_argument("--start-date", type=date.fromisoformat, default=date.today() - timedelta(days=30))
    parser.add_argument("--end-date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--account", default=None, help="Optional AWS Account ID")
    parser.add_argument("--region", default=None, help="Optional AWS Region")
    parser.add_argument("--organization-id", default=None, help="Optional Organization ID (defaults to default-org)")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and display without database write")

    args = parser.parse_args()

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    org_id = args.organization_id
    if not org_id:
        default_org = db.query(Organization).filter(Organization.slug == "default-org").first()
        if default_org:
            org_id = default_org.id

    print(f"[*] Initializing {args.provider.upper()} cost fetcher...")
    print(f"    Organization ID: {org_id or 'All Organizations'}")
    print(f"    Date Range: {args.start_date} to {args.end_date}")
    print(f"    Account: {args.account or 'All Accounts'}")
    print(f"    Region: {args.region or 'All Regions'}")

    provider = get_cloud_provider(force_provider=args.provider)

    if args.dry_run:
        records = provider.fetch_cost_and_usage(
            start_date=args.start_date,
            end_date=args.end_date,
            account_id=args.account,
            region=args.region,
        )
        print(f"[+] Dry run complete. Retrieved {len(records)} line-item records.")
        if records:
            print("    Sample record:", records[0])
        db.close()
        return

    try:
        service = CostService(provider)
        count = service.sync_costs(
            db,
            start_date=args.start_date,
            end_date=args.end_date,
            account_id=args.account,
            region=args.region,
            organization_id=org_id,
        )
        print(f"[✓] Synchronization successful. Inserted/updated {count} cost records in database.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

