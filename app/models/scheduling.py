"""
Vinta School OS — Scheduling Models
Schedule (recurring weekly slot), Session (specific instance on a date).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, ForeignKey, DateTime, Date, Time,
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class Schedule(db.Model):
    """Recurring weekly slot defining when a class meets."""

    __tablename__ = "schedules"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    class_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("classes.id"), nullable=False
    )
    classroom_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("classrooms.id"), nullable=True
    )
    day_of_week: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="0=Sun, 1=Mon, ..., 6=Sat"
    )
    start_time: Mapped[str] = mapped_column(Time, nullable=False)
    end_time: Mapped[str] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    class_ = relationship("Class", back_populates="schedules")
    classroom = relationship("Classroom", back_populates="schedules")
    sessions = relationship("Session", back_populates="schedule", lazy="dynamic")

    def __repr__(self):
        return f"<Schedule class={self.class_id} day={self.day_of_week} {self.start_time}-{self.end_time}>"


class Session(db.Model):
    """A concrete class session on a specific date. Generated from Schedule or created manually."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    academy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academies.id"), nullable=False
    )
    class_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("classes.id"), nullable=False
    )
    schedule_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("schedules.id"), nullable=True,
        comment="Link back to recurring slot — null for custom sessions"
    )
    teacher_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("teachers.id"), nullable=False,
        comment="Denormalized from Class at creation time"
    )
    classroom_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("classrooms.id"), nullable=True,
        comment="Denormalized from Schedule at creation time"
    )
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    start_time: Mapped[str] = mapped_column(Time, nullable=False)
    end_time: Mapped[str] = mapped_column(Time, nullable=False)
    subject: Mapped[str | None] = mapped_column(
        String(100), comment="Denormalized from Class"
    )
    status: Mapped[str] = mapped_column(
        SAEnum("scheduled", "in_progress", "completed", "cancelled", name="session_status_enum"),
        default="scheduled",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    academy = relationship("Academy", back_populates="sessions")
    class_ = relationship("Class", back_populates="sessions")
    schedule = relationship("Schedule", back_populates="sessions")
    teacher = relationship("Teacher", back_populates="sessions")
    classroom = relationship("Classroom")
    session_students = relationship(
        "SessionStudent", back_populates="session", lazy="dynamic",
        cascade="all, delete-orphan"
    )
    hours_logs = relationship("TeacherHoursLog", back_populates="session", lazy="dynamic")

    def __repr__(self):
        return f"<Session {self.class_id} on {self.date} {self.start_time}-{self.end_time}>"
