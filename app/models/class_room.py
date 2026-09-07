"""
Vinta School OS — Classroom, Class & Subject Models
Classroom (physical room), Class (subject offering), Subject (extensible palette).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Text, ForeignKey, DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class Classroom(db.Model):
    """A physical room in the academy."""

    __tablename__ = "classrooms"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    academy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academies.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    academy = relationship("Academy", back_populates="classrooms")
    schedules = relationship("Schedule", back_populates="classroom", lazy="dynamic")

    def __repr__(self):
        return f"<Classroom {self.name}>"


class Class(db.Model):
    """A subject offering (e.g., 'Math — CM2'). Enrollment target for students."""

    __tablename__ = "classes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    academy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academies.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(
        String(100), comment="Math, French, English, Science (extensible)"
    )
    color: Mapped[str | None] = mapped_column(
        String(7), comment="Hex color for calendar palette styling, e.g. #b3872a"
    )
    teacher_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("teachers.id"), nullable=True
    )
    capacity: Mapped[int] = mapped_column(Integer, default=0)
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
    academy = relationship("Academy", back_populates="classes")
    teacher = relationship("Teacher", back_populates="classes")
    schedules = relationship(
        "Schedule", back_populates="class_", lazy="dynamic", cascade="all, delete-orphan"
    )
    enrollments = relationship(
        "Enrollment", back_populates="class_", lazy="dynamic", cascade="all, delete-orphan"
    )
    sessions = relationship(
        "Session", back_populates="class_", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Class {self.name}>"


class Subject(db.Model):
    """Extensible palette entity for calendar subject colors."""

    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    academy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academies.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(
        String(7), default="#b3872a", comment="Hex color for calendar display"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    academy = relationship("Academy", back_populates="subjects")

    def __repr__(self):
        return f"<Subject {self.name} ({self.color})>"
