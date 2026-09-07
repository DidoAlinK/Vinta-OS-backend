"""
Vinta School OS — Academy & Tenant Models
Academy (tenant root), AcademySettings (singleton), Subscription (tier gating).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, Boolean, Enum as SAEnum, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class Academy(db.Model):
    """Top-level tenant entity. One academy = one private school/academy."""

    __tablename__ = "academies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(500))
    weekend_day: Mapped[int] = mapped_column(
        Integer, default=5, comment="Day-of-week considered weekend (5=Friday for Algeria)"
    )
    current_term: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    users = relationship("User", back_populates="academy", lazy="dynamic")
    students = relationship("Student", back_populates="academy", lazy="dynamic")
    teachers = relationship("Teacher", back_populates="academy", lazy="dynamic")
    classrooms = relationship("Classroom", back_populates="academy", lazy="dynamic")
    classes = relationship("Class", back_populates="academy", lazy="dynamic")
    sessions = relationship("Session", back_populates="academy", lazy="dynamic")
    payment_plans = relationship("PaymentPlan", back_populates="academy", lazy="dynamic")
    activity_logs = relationship("ActivityLog", back_populates="academy", lazy="dynamic")
    notifications = relationship("Notification", back_populates="academy", lazy="dynamic")
    subjects = relationship("Subject", back_populates="academy", lazy="dynamic")

    settings = relationship("AcademySettings", back_populates="academy", uselist=False)
    subscription = relationship("Subscription", back_populates="academy", uselist=False)

    def __repr__(self):
        return f"<Academy {self.name}>"


class AcademySettings(db.Model):
    """Per-academy configuration singleton."""

    __tablename__ = "academy_settings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    academy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academies.id"), unique=True, nullable=False
    )
    currency: Mapped[str] = mapped_column(String(10), default="DZD")
    default_plan_duration: Mapped[int] = mapped_column(Integer, default=30)
    billing_reminder_days_before: Mapped[int] = mapped_column(Integer, default=3)
    due_date_reminder_timing: Mapped[str] = mapped_column(
        SAEnum("same_day", "custom", name="reminder_timing_enum"), default="same_day"
    )
    whatsapp_template: Mapped[str | None] = mapped_column(Text)
    auto_checkout_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    end_class_popup_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    default_theme: Mapped[str] = mapped_column(
        SAEnum("light", "dark", name="theme_enum"), default="light"
    )
    default_font_size: Mapped[str] = mapped_column(
        SAEnum("normal", "large", name="font_size_enum"), default="normal"
    )
    default_language: Mapped[str] = mapped_column(
        SAEnum("fr", "ar", name="language_enum"), default="fr"
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
    academy = relationship("Academy", back_populates="settings")

    def __repr__(self):
        return f"<AcademySettings for {self.academy_id}>"


class Subscription(db.Model):
    """Academy SaaS subscription tier."""

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    academy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academies.id"), unique=True, nullable=False
    )
    tier: Mapped[str] = mapped_column(
        SAEnum("starter", "pro", "scaler", name="subscription_tier_enum"),
        default="starter",
    )
    status: Mapped[str] = mapped_column(
        SAEnum("active", "inactive", "trialing", name="subscription_status_enum"),
        default="active",
    )
    invoicing_method: Mapped[str] = mapped_column(String(50), default="Manual")
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    academy = relationship("Academy", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription {self.tier} for {self.academy_id}>"
