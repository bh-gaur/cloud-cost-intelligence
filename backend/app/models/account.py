"""
Cloud & AWS Account Models
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class CloudAccount(Base):
    __tablename__ = "cloud_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), default="aws", index=True)  # aws, azure, gcp
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    aws_details: Mapped["AWSAccount"] = relationship(
        "AWSAccount", back_populates="cloud_account", uselist=False, cascade="all, delete-orphan"
    )


class AWSAccount(Base):
    __tablename__ = "aws_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cloud_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cloud_accounts.id"), nullable=False, unique=True
    )
    account_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    account_name: Mapped[str] = mapped_column(String(128), nullable=False)
    role_arn: Mapped[str] = mapped_column(String(255), nullable=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=True)
    default_region: Mapped[str] = mapped_column(String(32), default="us-east-1")
    is_payer_account: Mapped[bool] = mapped_column(Boolean, default=False)
    connection_status: Mapped[str] = mapped_column(String(32), default="PENDING")  # PENDING, CONNECTED, FAILED
    last_connection_test: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    cloud_account: Mapped["CloudAccount"] = relationship("CloudAccount", back_populates="aws_details")

