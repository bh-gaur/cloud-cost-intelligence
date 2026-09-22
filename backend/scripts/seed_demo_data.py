#!/usr/bin/env python3
"""
seed_demo_data.py
Populates database with initial roles, demo users, accounts, 90 days of mock cost records,
optimization recommendations, alerts, and sample reports.

Usage:
    python seed_demo_data.py
"""

import sys
import argparse
from datetime import date, timedelta
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.models.user import Role, User
from app.models.account import CloudAccount, AWSAccount
from app.models.alert import AlertRule, AlertEvent
from app.models.cost import CostRecord
from app.models.optimization import OptimizationRecommendation
from app.models.notification import NotificationIntegration
from app.auth.security import hash_password
from app.providers.mock.provider import MockAWSProvider
from app.services.cost_service import CostService
from app.optimization.engine import OptimizationEngine
from app.alerts.detector import AnomalyDetector
from app.reports.service import ReportService
from app.models.organization import Organization, OrganizationMember


def seed(reset_data: bool = False):
    print("[*] Initializing Database Schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if reset_data:
            print("[*] Performing clean demo reset: wiping existing demo data...")
            demo_org = db.query(Organization).filter(Organization.slug == "demo-finops-enterprise").first()
            if demo_org:
                db.query(CostRecord).filter(CostRecord.organization_id == demo_org.id).delete(synchronize_session=False)
                db.query(AlertEvent).filter(AlertEvent.organization_id == demo_org.id).delete(synchronize_session=False)
                db.query(OptimizationRecommendation).filter(OptimizationRecommendation.organization_id == demo_org.id).delete(synchronize_session=False)
                db.query(AlertRule).filter(AlertRule.organization_id == demo_org.id).delete(synchronize_session=False)
                db.query(NotificationIntegration).filter(NotificationIntegration.organization_id == demo_org.id).delete(synchronize_session=False)
                db.query(AWSAccount).filter(AWSAccount.organization_id == demo_org.id).delete(synchronize_session=False)
                db.query(CloudAccount).filter(CloudAccount.organization_id == demo_org.id).delete(synchronize_session=False)
                db.commit()
                print("[✓] Demo organization records reset successfully.")
        # 1. Seed Roles
        admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
        if not admin_role:
            admin_role = Role(name="ADMIN", description="Administrator with full platform access")
            db.add(admin_role)

        user_role = db.query(Role).filter(Role.name == "USER").first()
        if not user_role:
            user_role = Role(name="USER", description="Standard FinOps Analyst with read-only access")
            db.add(user_role)

        db.commit()
        db.refresh(admin_role)
        db.refresh(user_role)

        # 2. Seed Default Users & Demo Organization
        admin_user = db.query(User).filter(User.email == "admin@cloudcost.local").first()
        if not admin_user:
            admin_user = User(
                email="admin@cloudcost.local",
                hashed_password=hash_password("Admin123!@#"),
                full_name="FinOps Administrator",
                role_id=admin_role.id,
                is_active=True,
            )
            db.add(admin_user)

        finops_user = db.query(User).filter(User.email == "user@cloudcost.local").first()
        if not finops_user:
            finops_user = User(
                email="user@cloudcost.local",
                hashed_password=hash_password("User123!@#"),
                full_name="Sarah FinOps Analyst",
                role_id=user_role.id,
                is_active=True,
            )
            db.add(finops_user)

        db.commit()
        db.refresh(admin_user)
        db.refresh(finops_user)

        # Seed Demo Organization
        demo_org = db.query(Organization).filter(Organization.slug == "demo-finops-enterprise").first()
        if not demo_org:
            demo_org = Organization(
                name="Demo FinOps Enterprise",
                slug="demo-finops-enterprise",
                status="ACTIVE",
            )
            db.add(demo_org)
            db.commit()
            db.refresh(demo_org)

        # Ensure demo members exist
        m_admin = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == demo_org.id,
            OrganizationMember.user_id == admin_user.id
        ).first()
        if not m_admin:
            m_admin = OrganizationMember(
                organization_id=demo_org.id,
                user_id=admin_user.id,
                role="OWNER",
                status="ACTIVE",
            )
            db.add(m_admin)

        m_user = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == demo_org.id,
            OrganizationMember.user_id == finops_user.id
        ).first()
        if not m_user:
            m_user = OrganizationMember(
                organization_id=demo_org.id,
                user_id=finops_user.id,
                role="ANALYST",
                status="ACTIVE",
            )
            db.add(m_user)

        db.commit()
        print("[✓] Seeded default demo organization (Demo FinOps Enterprise) and users:")
        print("    - Admin: admin@cloudcost.local / Admin123!@#")
        print("    - User:  user@cloudcost.local / User123!@#")

        # 3. Seed Accounts
        mock_provider = MockAWSProvider()
        accounts_data = mock_provider.get_accounts()

        for acc in accounts_data:
            existing_cloud = db.query(CloudAccount).filter(CloudAccount.name == acc["account_name"]).first()
            if not existing_cloud:
                cloud_acc = CloudAccount(organization_id=demo_org.id, provider="aws", name=acc["account_name"], is_active=True)
                db.add(cloud_acc)
                db.commit()
                db.refresh(cloud_acc)

                aws_acc = AWSAccount(
                    organization_id=demo_org.id,
                    cloud_account_id=cloud_acc.id,
                    account_id=acc["account_id"],
                    account_name=acc["account_name"],
                    role_arn=f"arn:aws:iam::{acc['account_id']}:role/FinOpsCostExplorerReadOnlyRole",
                    external_id="finops-cost-intelligence-access-2026",
                    default_region="us-east-1",
                    is_payer_account=acc.get("is_master", False),
                    connection_status="CONNECTED",
                )
                db.add(aws_acc)
                db.commit()

        print(f"[✓] Seeded {len(accounts_data)} AWS cloud accounts.")

        # 4. Seed 90 Days of Cost Records
        cost_service = CostService(mock_provider)
        today = date.today()
        start_date = today - timedelta(days=90)

        print(f"[*] Ingesting 90 days of deterministic mock cost records ({start_date} to {today})...")
        synced_count = cost_service.sync_costs(db, start_date=start_date, end_date=today, organization_id=demo_org.id)
        print(f"[✓] Ingested {synced_count} granular cost line items.")

        # 5. Seed Optimization Recommendations
        print("[*] Generating FinOps optimization recommendations...")
        opt_engine = OptimizationEngine(mock_provider)
        recs = opt_engine.run_all(db, organization_id=demo_org.id)
        print(f"[✓] Generated {len(recs)} optimization recommendations.")

        # 6. Seed Anomaly Events & Budgets
        print("[*] Detecting anomalies & synchronizing AWS budgets...")
        detector = AnomalyDetector(mock_provider)
        detector.detect_daily_anomalies(db, organization_id=demo_org.id)
        detector.sync_budgets(db, organization_id=demo_org.id)
        print("[✓] Anomaly detector and Budgets initialized.")

        # 7. Seed Alert Rules
        rule1 = db.query(AlertRule).filter(AlertRule.name == "Daily Spend Surge Alert", AlertRule.organization_id == demo_org.id).first()
        if not rule1:
            rule1 = AlertRule(
                organization_id=demo_org.id,
                name="Daily Spend Surge Alert",
                alert_type="DAILY_THRESHOLD",
                threshold_value=1500.0,
                notification_channel="slack",
                is_enabled=True,
            )
            db.add(rule1)

        rule2 = db.query(AlertRule).filter(AlertRule.name == "EC2 Spike Alert", AlertRule.organization_id == demo_org.id).first()
        if not rule2:
            rule2 = AlertRule(
                organization_id=demo_org.id,
                name="EC2 Spike Alert",
                alert_type="SERVICE_SPIKE",
                service="Amazon Elastic Compute Cloud - Compute",
                threshold_value=25.0,
                notification_channel="email",
                is_enabled=True,
            )
            db.add(rule2)

        db.commit()
        print("[✓] Configured default alert rules.")

        # 8. Seed Initial Sample Report
        print("[*] Generating initial HTML and CSV sample reports...")
        report_service = ReportService()
        report_service.generate_report(
            db=db,
            fmt="html",
            start_date=today - timedelta(days=30),
            end_date=today,
            custom_name="monthly-finops-executive-summary",
            organization_id=demo_org.id,
        )
        report_service.generate_report(
            db=db,
            fmt="csv",
            start_date=today - timedelta(days=30),
            end_date=today,
            custom_name="monthly-finops-spend-export",
            organization_id=demo_org.id,
        )
        print("[✓] Sample reports generated in backend/reports/.")

        print("\n[SUCCESS] Seed process completed successfully! You can now start the backend.")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed or reset demo data for CloudCost Intelligence.")
    parser.add_argument("--reset", "-r", action="store_true", help="Wipe existing demo data before re-seeding.")
    args = parser.parse_args()
    seed(reset_data=args.reset)

