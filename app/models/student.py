"""
Vinta School OS — Student Models
Student, Guardian (1:N), Enrollment (M:N with Class).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class Student(db.Model):
    """A child enrolled in the academy."""

    __tablename__ = "students"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    academy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academies.id"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    parent_phone: Mapped[str | None] = mapped_column(
        String(30), comment="Primary parent/guardian emergency number"
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    academy = relationship("Academy", back_populates="students")
    guardians = relationship(
        "Guardian", back_populates="student", lazy="dynamic", cascade="all, delete-orphan"
    )
    enrollments = relationship(
        "Enrollment", back_populates="student", lazy="dynamic", cascade="all, delete-orphan"
    )
    session_students = relationship(
        "SessionStudent", back_populates="student", lazy="dynamic"
    )
    billings = relationship(
        "StudentBilling", back_populates="student", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Student {self.full_name}>"


class Guardian(db.Model):
    """Student guardian / emergency contact. One student can have multiple guardians."""

    __tablename__ = "guardians"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    relationship_type: Mapped[str | None] = mapped_column(
        String(100), comment="Free-form relationship label (Mother, Father, Uncle...)"
    )
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    student = relationship("Student", back_populates="guardians")

    def __repr__(self):
        return f"<Guardian {self.name} ({self.relationship_type})>"


class Enrollment(db.Model):
    """Many-to-many: Student ↔ Class through Enrollment."""

    __tablename__ = "enrollments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id"), nullable=False
    )
    class_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("classes.id"), nullable=False
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    status: Mapped[str] = mapped_column(
        SAEnum("active", "withdrawn", name="enrollment_status_enum"),
        default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    student = relationship("Student", back_populates="enrollments")
    class_ = relationship("Class", back_populates="enrollments")

    def __repr__(self):
        return f"<Enrollment student={self.student_id} class={self.class_id}>"
