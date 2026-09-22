"""
Database Migration & Multi-Tenancy Data Backfill Service
Creates default organization and backfills organization_id on pre-existing records safely.
"""

import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database.base import Base
from app.models.organization import Organization, OrganizationMember
from app.models.user import User

logger = logging.getLogger(__name__)

DEFAULT_ORG_SLUG = "default-org"
DEFAULT_ORG_NAME = "Default Organization"


def run_multi_tenancy_migration(db: Session, engine=None) -> Organization:
    """
    Ensures all database tables exist, creates default organization if missing,
    assigns all orphan users to default org, and backfills organization_id on orphan records.
    """
    if engine:
        Base.metadata.create_all(bind=engine)

    # 0. Migrate users table columns if missing
    try:
        db.execute(text("ALTER TABLE users ADD COLUMN status VARCHAR(32) DEFAULT 'ACTIVE'"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        db.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        db.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR(255)"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        db.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(512)"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        db.execute(text("ALTER TABLE audit_logs ADD COLUMN organization_id VARCHAR(36)"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        db.execute(text("ALTER TABLE organization_invitations ADD COLUMN updated_at DATETIME"))
        db.commit()
    except Exception:
        db.rollback()

    # Optimization recommendations scanner columns
    opt_columns = [
        ("remediation_code", "TEXT"),
        ("implementation_effort", "VARCHAR(32) DEFAULT 'medium'"),
        ("operational_risk", "VARCHAR(32) DEFAULT 'low'"),
        ("production_safety_score", "INTEGER DEFAULT 85"),
    ]
    for col_name, col_type in opt_columns:
        try:
            db.execute(text(f"ALTER TABLE optimization_recommendations ADD COLUMN {col_name} {col_type}"))
            db.commit()
        except Exception:
            db.rollback()

    # 1. Get or create Default Organization
    default_org = db.query(Organization).filter(Organization.slug == DEFAULT_ORG_SLUG).first()
    if not default_org:
        logger.info(f"Creating default organization: {DEFAULT_ORG_NAME}")
        default_org = Organization(
            name=DEFAULT_ORG_NAME,
            slug=DEFAULT_ORG_SLUG,
            status="ACTIVE",
        )
        db.add(default_org)
        db.flush()

    # 2. Assign orphan non-demo users to Default Organization as OWNER
    demo_emails = ["admin@cloudcost.local", "user@cloudcost.local"]
    users = db.query(User).filter(~User.email.in_(demo_emails)).all()
    for user in users:
        # Check if user already belongs to any organization
        existing_m = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
        if not existing_m:
            logger.info(f"Assigning orphan user {user.email} to default organization as OWNER")
            member = OrganizationMember(
                organization_id=default_org.id,
                user_id=user.id,
                role="OWNER",
                status="ACTIVE",
            )
            db.add(member)
    db.commit()

    # 3. Ensure organization_id column exists and backfill on all tenant tables
    tenant_tables = [
        "cloud_accounts",
        "aws_accounts",
        "cost_records",
        "daily_cost_summary",
        "service_cost_summary",
        "account_cost_summary",
        "region_cost_summary",
        "reports",
        "report_schedules",
        "alert_rules",
        "alert_events",
        "budgets",
        "notification_integrations",
        "optimization_recommendations",
        "audit_logs",
    ]

    for table in tenant_tables:
        try:
            db.execute(text(f"ALTER TABLE {table} ADD COLUMN organization_id VARCHAR(36)"))
            db.commit()
        except Exception:
            db.rollback()

    for table in tenant_tables:
        try:
            query = text(f"UPDATE {table} SET organization_id = :org_id WHERE organization_id IS NULL OR organization_id = ''")
            result = db.execute(query, {"org_id": default_org.id})
            if result.rowcount > 0:
                logger.info(f"Backfilled {result.rowcount} records in '{table}' with organization_id='{default_org.id}'")
        except Exception as e:
            logger.debug(f"Backfill notice for {table}: {e}")

    db.commit()
    logger.info("Multi-tenancy migration completed successfully.")
    return default_org
