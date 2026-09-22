"""
Notification Integration Model
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class NotificationIntegration(Base):
    __tablename__ = "notification_integrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # email, slack, teams, gchat
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict)  # Webhook URL or SMTP settings (secrets encrypted/masked)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_tested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    test_status: Mapped[str] = mapped_column(String(32), default="UNTESTED")  # SUCCESS, FAILED, UNTESTED
    last_error: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

