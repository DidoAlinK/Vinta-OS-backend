"""
Vinta School OS — Notification Model
In-app toast notifications and alerts.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Boolean, Text, ForeignKey, DateTime, JSON,
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class Notification(db.Model):
    """In-app toast notification / alert."""

    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    academy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academies.id"), nullable=False
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True,
        comment="null = broadcast to all academy users"
    )
    type: Mapped[str] = mapped_column(
        SAEnum(
            "payment_reminder", "class_ending", "enrollment_request",
            "overdue_alert", "general",
            name="notification_type_enum",
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    actions: Mapped[dict | None] = mapped_column(
        JSON, comment="Array of {label, variant} for action buttons"
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    academy = relationship("Academy", back_populates="notifications")
    user = relationship("User")

    def __repr__(self):
        return f"<Notification {self.type}: {self.title}>"
