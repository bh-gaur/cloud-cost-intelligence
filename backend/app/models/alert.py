"""
Alert, Anomaly Event, and Budget Models
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, Numeric, Boolean, JSON, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(32), nullable=False)  # DAILY_THRESHOLD, PERCENT_INCREASE, SERVICE_SPIKE, BUDGET_THRESHOLD
    account_id: Mapped[str] = mapped_column(String(32), default="all")
    service: Mapped[str] = mapped_column(String(128), default="all")
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    time_window_days: Mapped[int] = mapped_column(default=1)
    notification_channel: Mapped[str] = mapped_column(String(32), default="all")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alert_rule_id: Mapped[str] = mapped_column(String(36), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="WARNING")  # INFO, WARNING, CRITICAL
    account_id: Mapped[str] = mapped_column(String(32), default="all")
    service: Mapped[str] = mapped_column(String(128), nullable=True)
    detected_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    expected_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=True)
    difference_percentage: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")  # OPEN, ACKNOWLEDGED, RESOLVED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )


class BudgetRecord(Base):
    __tablename__ = "budgets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    budget_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    budget_limit: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    current_spend: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"))
    forecasted_spend: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"))
    remaining_budget: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"))
    percentage_consumed: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0.00"))
    status: Mapped[str] = mapped_column(String(32), default="Healthy")  # Healthy, Warning, Critical, Exceeded
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

