"""
Vinta School OS — Attendance Model
SessionStudent: tracks check-in/out, payment snapshot per session per student.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Boolean, ForeignKey, DateTime,
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class SessionStudent(db.Model):
    """
    Many-to-many: Session ↔ Student.
    Tracks attendance (is_present, check-in/out times) and per-session payment status.
    """

    __tablename__ = "session_students"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=False
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id"), nullable=False
    )
    is_present: Mapped[bool] = mapped_column(Boolean, default=False)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime)
    checked_out_at: Mapped[datetime | None] = mapped_column(DateTime)
    checked_in_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True,
        comment="Which staff member logged the check-in"
    )
    payment_status: Mapped[str] = mapped_column(
        SAEnum("paid", "due", "overdue", name="session_payment_status_enum"),
        default="paid",
        comment="Denormalized snapshot for this session",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    session = relationship("Session", back_populates="session_students")
    student = relationship("Student", back_populates="session_students")
    checked_in_by_user = relationship("User")

    def __repr__(self):
        return f"<SessionStudent session={self.session_id} student={self.student_id}>"
