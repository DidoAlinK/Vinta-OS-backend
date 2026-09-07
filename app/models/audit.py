"""
Vinta School OS — Activity Log & Audit Trail Model
Every significant action is logged with the user who performed it.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class ActivityLog(db.Model):
    """
    Audit trail. Every significant action in the system is logged
    with user_id — the staff member who performed the action.
    """

    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    academy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academies.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False,
        comment="Who performed the action"
    )
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="student | teacher | class | session | billing | payment"
    )
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="created | updated | deleted | checked_in | checked_out | "
                "payment_received | payment_overdue | enrolled | withdrawn"
    )
    description: Mapped[str | None] = mapped_column(
        Text, comment="Human-readable: 'Payment received — Karim M.'"
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSON, comment="Contextual data: amount, session info, etc."
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    academy = relationship("Academy", back_populates="activity_logs")
    user = relationship("User", back_populates="activity_logs")

    def __repr__(self):
        return f"<ActivityLog {self.action} {self.entity_type} by {self.user_id}>"
