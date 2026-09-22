"""
Cost Record & Summary Models
All monetary values use Numeric(18, 4) to ensure exact financial fidelity.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    String,
    Date,
    DateTime,
    Numeric,
    JSON,
    Index,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class CostRecord(Base):
    __tablename__ = "cost_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), default="aws", index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    account_name: Mapped[str] = mapped_column(String(128), default="Default Account")
    region: Mapped[str] = mapped_column(String(32), default="global", index=True)
    service: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    service_category: Mapped[str] = mapped_column(String(64), default="Other", index=True)
    resource_id: Mapped[str] = mapped_column(String(256), nullable=True, index=True)
    usage_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"))
    usage_unit: Mapped[str] = mapped_column(String(64), default="Units")
    cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    tags: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_cost_org_date_account_service", "organization_id", "date", "account_id", "service"),
        Index("idx_cost_service_region", "service", "region"),
    )


class DailyCostSummary(Base):
    __tablename__ = "daily_cost_summary"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(32), nullable=False, default="all", index=True)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    previous_day_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"))
    cost_difference: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"))
    percentage_change: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "date", "account_id", name="uq_daily_summary_org_date_acc"),
    )


class ServiceCostSummary(Base):
    __tablename__ = "service_cost_summary"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(32), default="all", index=True)
    service: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    service_category: Mapped[str] = mapped_column(String(64), default="Other")
    cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    percentage_of_total: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(8), default="USD")

    __table_args__ = (
        UniqueConstraint("organization_id", "date", "account_id", "service", name="uq_service_summary_org_date_acc_svc"),
    )


class AccountCostSummary(Base):
    __tablename__ = "account_cost_summary"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    account_name: Mapped[str] = mapped_column(String(128), nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    percentage_of_total: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(8), default="USD")

    __table_args__ = (
        UniqueConstraint("organization_id", "date", "account_id", name="uq_account_summary_org_date_acc"),
    )


class RegionCostSummary(Base):
    __tablename__ = "region_cost_summary"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(32), default="all", index=True)
    region: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    percentage_of_total: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(8), default="USD")

    __table_args__ = (
        UniqueConstraint("organization_id", "date", "account_id", "region", name="uq_region_summary_org_date_acc_reg"),
    )

