#!/usr/bin/env python3
"""
clear_mock_data.py
Clears mock cost data, recommendations, accounts, reports, and alerts from the database,
while preserving system roles and default user accounts for login authentication.

Usage:
    python backend/scripts/clear_mock_data.py
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models.cost import (
    CostRecord,
    DailyCostSummary,
    ServiceCostSummary,
    AccountCostSummary,
    RegionCostSummary,
)
from app.models.optimization import OptimizationRecommendation
from app.models.alert import AlertEvent, BudgetRecord
from app.models.report import Report
from app.models.account import AWSAccount, CloudAccount
from app.models.audit import AuditLog
from app.models.user import Role, User
from app.auth.security import hash_password


def clear_mock_data():
    print("[*] Connecting to database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Delete mock records
        deleted_costs = db.query(CostRecord).delete()
        db.query(DailyCostSummary).delete()
        db.query(ServiceCostSummary).delete()
        db.query(AccountCostSummary).delete()
        db.query(RegionCostSummary).delete()

        deleted_recs = db.query(OptimizationRecommendation).delete()
        deleted_alerts = db.query(AlertEvent).delete()
        deleted_budgets = db.query(BudgetRecord).delete()
        deleted_reports = db.query(Report).delete()
        deleted_aws_acc = db.query(AWSAccount).delete()
        deleted_cloud_acc = db.query(CloudAccount).delete()
        deleted_audit = db.query(AuditLog).delete()


        db.commit()

        print(f"[✓] Deleted {deleted_costs} cost records.")
        print(f"[✓] Deleted {deleted_recs} optimization recommendations.")
        print(f"[✓] Deleted {deleted_alerts} alert events.")
        print(f"[✓] Deleted {deleted_budgets} budget entries.")
        print(f"[✓] Deleted {deleted_reports} report entries.")
        print(f"[✓] Deleted {deleted_aws_acc} AWS accounts and {deleted_cloud_acc} Cloud accounts.")
        print(f"[✓] Deleted {deleted_audit} audit log entries.")

        # Ensure baseline Roles exist
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

        # Ensure default baseline users exist for login access
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

        # Clean generated report files in backend/reports/
        reports_dir = backend_dir / "reports"
        if reports_dir.exists():
            for f in reports_dir.glob("*"):
                if f.is_file() and f.name != ".gitkeep":
                    try:
                        f.unlink()
                    except Exception:
                        pass
        print("[✓] Cleared report files from backend/reports/.")

        print("\n[SUCCESS] Mock data completely removed! Database is ready for live AWS data.")

    finally:
        db.close()


if __name__ == "__main__":
    clear_mock_data()
