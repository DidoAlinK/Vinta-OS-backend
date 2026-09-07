"""
Vinta School OS — Billing Models
PaymentPlan, StudentBilling, PaymentLog.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Text, ForeignKey, DateTime, Date,
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class PaymentPlan(db.Model):
    """Reusable billing plans that can be assigned to students."""

    __tablename__ = "payment_plans"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    academy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academies.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, comment="30 for monthly, 90 for term")
    amount_da: Mapped[int] = mapped_column(Integer, nullable=False, comment="Price in Algerian Dinars")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    academy = relationship("Academy", back_populates="payment_plans")
    billings = relationship("StudentBilling", back_populates="payment_plan", lazy="dynamic")

    def __repr__(self):
        return f"<PaymentPlan {self.name} {self.amount_da} DA>"


class StudentBilling(db.Model):
    """One record per billing cycle per student. Core billing entity."""

    __tablename__ = "student_billings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id"), nullable=False
    )
    payment_plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("payment_plans.id"), nullable=False
    )
    amount_da: Mapped[int] = mapped_column(Integer, nullable=False, comment="Amount due for this cycle")
    status: Mapped[str] = mapped_column(
        SAEnum("paid", "due", "overdue", name="billing_status_enum"),
        default="due",
    )
    due_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    paid_date: Mapped[datetime | None] = mapped_column(Date)
    paid_amount: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Actual amount paid (may differ if partial)"
    )
    cycle_start: Mapped[datetime] = mapped_column(Date, nullable=False)
    cycle_end: Mapped[datetime] = mapped_column(Date, nullable=False)
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
    student = relationship("Student", back_populates="billings")
    payment_plan = relationship("PaymentPlan", back_populates="billings")
    payment_logs = relationship(
        "PaymentLog", back_populates="student_billing", lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<StudentBilling {self.student_id} {self.amount_da} DA ({self.status})>"


class PaymentLog(db.Model):
    """Individual payment transactions against a billing record."""

    __tablename__ = "payment_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_billing_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_billings.id"), nullable=False
    )
    amount_da: Mapped[int] = mapped_column(Integer, nullable=False, comment="Amount paid in this transaction")
    payment_method: Mapped[str | None] = mapped_column(
        String(50), comment="Cash, bank transfer, etc."
    )
    recorded_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False,
        comment="Which staff member logged the payment"
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    student_billing = relationship("StudentBilling", back_populates="payment_logs")
    recorded_by_user = relationship("User")

    def __repr__(self):
        return f"<PaymentLog {self.amount_da} DA>"
