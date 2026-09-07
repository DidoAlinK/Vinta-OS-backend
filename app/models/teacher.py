"""
Vinta School OS — Teacher Models
Teacher, TeacherPayroll, TeacherHoursLog.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Text, ForeignKey, DateTime,
    Enum as SAEnum, Numeric, Date,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class Teacher(db.Model):
    """An instructor employed by the academy."""

    __tablename__ = "teachers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    academy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academies.id"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    subject: Mapped[str | None] = mapped_column(
        String(100), comment="Primary subject (Math, French, English, Science)"
    )
    notes: Mapped[str | None] = mapped_column(Text)
    contract_type: Mapped[str] = mapped_column(
        SAEnum("hourly", "per_student", name="contract_type_enum"),
        default="hourly",
    )
    hourly_rate: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="DA per hour — for hourly contracts"
    )
    per_student_rate: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="DA per student — for per-student contracts"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    academy = relationship("Academy", back_populates="teachers")
    classes = relationship("Class", back_populates="teacher", lazy="dynamic")
    sessions = relationship("Session", back_populates="teacher", lazy="dynamic")
    payrolls = relationship(
        "TeacherPayroll", back_populates="teacher", lazy="dynamic"
    )
    hours_logs = relationship(
        "TeacherHoursLog", back_populates="teacher", lazy="dynamic"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Teacher {self.full_name}>"


class TeacherPayroll(db.Model):
    """Monthly payroll record for each teacher."""

    __tablename__ = "teacher_payrolls"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    teacher_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("teachers.id"), nullable=False
    )
    period_start: Mapped[datetime] = mapped_column(Date, nullable=False)
    period_end: Mapped[datetime] = mapped_column(Date, nullable=False)
    total_hours: Mapped[float] = mapped_column(
        Numeric(8, 2), default=0, comment="Sum of logged hours (hourly contracts)"
    )
    total_students: Mapped[int] = mapped_column(
        Integer, default=0, comment="Active student count (per-student contracts)"
    )
    rate_applied: Mapped[int] = mapped_column(
        Integer, default=0, comment="Rate used for calculation"
    )
    calculated_amount: Mapped[int] = mapped_column(
        Integer, default=0, comment="total_hours × rate OR total_students × rate"
    )
    status: Mapped[str] = mapped_column(
        SAEnum("pending", "settled", "overdue", name="payroll_status_enum"),
        default="pending",
    )
    paid_date: Mapped[datetime | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    teacher = relationship("Teacher", back_populates="payrolls")

    def __repr__(self):
        return f"<TeacherPayroll {self.teacher_id} {self.period_start}>"


class TeacherHoursLog(db.Model):
    """Records when a teacher's hours are logged (per session)."""

    __tablename__ = "teacher_hours_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    teacher_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("teachers.id"), nullable=False
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=False
    )
    hours: Mapped[float] = mapped_column(
        Numeric(6, 2), nullable=False, comment="Duration of the session in hours"
    )
    logged_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    teacher = relationship("Teacher", back_populates="hours_logs")
    session = relationship("Session", back_populates="hours_logs")
    logged_by_user = relationship("User")

    def __repr__(self):
        return f"<TeacherHoursLog {self.teacher_id} {self.hours}h>"
