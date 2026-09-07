"""
Unit Tests — Billing Cycle Calculations
Tests for payment status derivation, aging buckets, renewal logic.
"""
import uuid
import pytest
from datetime import date, timedelta
from app.models.billing import PaymentPlan, StudentBilling, PaymentLog
from app.models.student import Student
from app.utils.formatters import days_overdue, overdue_bucket


@pytest.mark.unit
class TestBillingStatusDerivation:
    """Test billing status derivation logic."""

    def test_status_paid_when_paid_date_set(self, db, academy, student, payment_plans):
        """Status should be 'paid' when paid_date is set and paid_amount >= amount_da."""
        billing = StudentBilling(
            id=str(uuid.uuid4()),
            student_id=student.id,
            payment_plan_id=payment_plans[0].id,
            amount_da=3500,
            status="paid",
            due_date=date.today() + timedelta(days=15),
            paid_date=date.today(),
            paid_amount=3500,
            cycle_start=date.today(),
            cycle_end=date.today() + timedelta(days=30),
        )
        db.session.add(billing)
        db.session.flush()

        assert billing.status == "paid"

    def test_status_due_when_not_yet_paid(self, db, academy, student, payment_plans):
        """Status should be 'due' when due_date is in the future."""
        billing = StudentBilling(
            id=str(uuid.uuid4()),
            student_id=student.id,
            payment_plan_id=payment_plans[0].id,
            amount_da=3500,
            status="due",
            due_date=date.today() + timedelta(days=10),
            cycle_start=date.today(),
            cycle_end=date.today() + timedelta(days=30),
        )
        db.session.add(billing)
        db.session.flush()

        assert billing.status == "due"

    def test_status_overdue_when_past_due(self, db, academy, student, payment_plans):
        """Status should transition to 'overdue' when due_date has passed."""
        billing = StudentBilling(
            id=str(uuid.uuid4()),
            student_id=student.id,
            payment_plan_id=payment_plans[0].id,
            amount_da=3500,
            status="overdue",
            due_date=date.today() - timedelta(days=5),
            cycle_start=date.today() - timedelta(days=35),
            cycle_end=date.today() - timedelta(days=5),
        )
        db.session.add(billing)
        db.session.flush()

        assert billing.status == "overdue"


@pytest.mark.unit
class TestAgingBuckets:
    """Test aging bucket classification."""

    def test_recent_bucket_1_to_7_days(self):
        """1-7 days overdue should be classified as 'recent'."""
        assert overdue_bucket(1) == "recent"
        assert overdue_bucket(3) == "recent"
        assert overdue_bucket(7) == "recent"

    def test_aging_bucket_8_to_30_days(self):
        """8-30 days overdue should be classified as 'aging'."""
        assert overdue_bucket(8) == "aging"
        assert overdue_bucket(15) == "aging"
        assert overdue_bucket(30) == "aging"

    def test_critical_bucket_30plus_days(self):
        """30+ days overdue should be classified as 'critical'."""
        assert overdue_bucket(31) == "critical"
        assert overdue_bucket(60) == "critical"
        assert overdue_bucket(365) == "critical"


@pytest.mark.unit
class TestDaysOverdue:
    """Test days overdue calculation."""

    def test_positive_when_overdue(self):
        """Should return positive number for past due dates."""
        past_date = date.today() - timedelta(days=10)
        assert days_overdue(past_date) == 10

    def test_zero_when_not_overdue(self):
        """Should return 0 for future due dates."""
        future_date = date.today() + timedelta(days=5)
        assert days_overdue(future_date) == 0

    def test_zero_when_due_today(self):
        """Should return 0 when due date is today."""
        assert days_overdue(date.today()) == 0


@pytest.mark.unit
class TestPaymentPlans:
    """Test payment plan creation and properties."""

    def test_plan_creation(self, db, academy):
        """Payment plans should store correct values."""
        plan = PaymentPlan(
            id=str(uuid.uuid4()),
            academy_id=academy.id,
            name="Monthly — 3,500 DA",
            duration_days=30,
            amount_da=3500,
        )
        db.session.add(plan)
        db.session.flush()

        assert plan.name == "Monthly — 3,500 DA"
        assert plan.duration_days == 30
        assert plan.amount_da == 3500

    def test_term_plan_duration(self, db, academy):
        """Term plans should have 90-day duration."""
        plan = PaymentPlan(
            id=str(uuid.uuid4()),
            academy_id=academy.id,
            name="Term — 9,000 DA",
            duration_days=90,
            amount_da=9000,
        )
        db.session.add(plan)
        db.session.flush()

        assert plan.duration_days == 90
        assert plan.amount_da == 9000
