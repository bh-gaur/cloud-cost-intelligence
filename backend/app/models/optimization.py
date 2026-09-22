"""
Optimization Recommendation Model
Matches FinOps Framework standards for confidence and validation tracking.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, Text, Index, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class OptimizationRecommendation(Base):
    __tablename__ = "optimization_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    rule_name: Mapped[str] = mapped_column(String(128), nullable=False)
    account_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(32), default="global", index=True)
    service: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    resource_name: Mapped[str] = mapped_column(String(256), nullable=True)

    current_monthly_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("0.0000")
    )
    estimated_monthly_savings: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("0.0000")
    )
    estimated_annual_savings: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("0.0000")
    )
    savings_percentage: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("0.00")
    )

    priority: Mapped[str] = mapped_column(String(16), default="MEDIUM", index=True)  # HIGH, MEDIUM, LOW
    confidence: Mapped[str] = mapped_column(String(16), default="Potential", index=True)  # Observed, Estimated, Potential
    validation_status: Mapped[str] = mapped_column(
        String(32), default="Requires validation", index=True
    )  # Requires validation, Insufficient data, Validated, Dismissed

    reason: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    action_required: Mapped[str] = mapped_column(Text, nullable=False)
    remediation_code: Mapped[str] = mapped_column(Text, nullable=True)
    implementation_effort: Mapped[str] = mapped_column(String(32), default="medium")  # low, medium, high
    operational_risk: Mapped[str] = mapped_column(String(32), default="low")  # low, medium, high
    production_safety_score: Mapped[int] = mapped_column(Integer, default=80)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_opt_rule_resource", "rule_id", "resource_id"),
        Index("idx_opt_priority_confidence", "priority", "confidence"),
    )

